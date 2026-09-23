#!/usr/bin/env python3
"""Exploratory V3 reentry replay with risk-bank accounting.

Research/tooling only. This is a same-dataset, path-synthetic replay designed
to expose V3 mechanics, failure modes, and blockers. It never promotes live
logic and never overwrites actual broker R labels.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import analyze_raw_ohlc_path_scaling_v2_confluence as v2  # noqa: E402
from scripts.build_raw_ohlc_prefill_delivery_path import (  # noqa: E402
    DEFAULT_DATA_ROOTS,
    PathIndex,
    high_low_close,
    iso,
    load_path_indexes,
    parse_cohort,
    parse_utc,
)

DEFAULT_EVENT_LOG = v2.DEFAULT_EVENT_LOG
DEFAULT_VARIANT_SPEC = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V3_PRE_REGISTERED_VARIANTS_2026-05-03.json"
)
DEFAULT_OUTPUT_JSON = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V3_FULL_EXPLORATORY_REPLAY_2026-05-03.json"
)
DEFAULT_OUTPUT_MD = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V3_FULL_EXPLORATORY_REPLAY_2026-05-03.md"
)
DEFAULT_CASEBOOK_JSONL = (
    "research/phase_3_external_feed_validation/"
    "RAW_OHLC_PATH_SCALING_V3_CASEBOOK_2026-05-03.jsonl"
)

BASELINE = v2.BASELINE
FVG = v2.FVG
OB = v2.OB
SWING = v2.SWING
COMPOSITE = v2.COMPOSITE
V2_VARIANTS = (BASELINE, SWING, FVG, OB, COMPOSITE)
EPS = 1e-9
SETUP_FLOOR_R = -1.0


@dataclass(frozen=True)
class RiskBankPlan:
    status: str
    requested_size: float
    accepted_size: float
    aggregate_worst_case_before: float
    aggregate_worst_case_after: float | None
    max_size_allowed: float
    reason: str | None = None


def aggregate_worst_case_r(
    *,
    realized_closed_leg_r: float,
    open_leg_stop_if_hit_rs: Sequence[float],
    estimated_remaining_cost_r: float,
) -> float:
    return round(realized_closed_leg_r + sum(open_leg_stop_if_hit_rs) - estimated_remaining_cost_r, 10)


def max_new_leg_size(
    *,
    realized_closed_leg_r: float,
    existing_open_stop_rs: Sequence[float],
    new_leg_stop_if_hit_r_per_full_size: float,
    estimated_remaining_cost_r: float,
    floor_r: float = SETUP_FLOOR_R,
) -> float:
    if new_leg_stop_if_hit_r_per_full_size >= 0:
        return math.inf
    before_without_new = realized_closed_leg_r + sum(existing_open_stop_rs) - estimated_remaining_cost_r
    allowed_loss = before_without_new - floor_r
    if allowed_loss <= 0:
        return 0.0
    return max(0.0, allowed_loss / abs(new_leg_stop_if_hit_r_per_full_size))


def plan_new_leg(
    *,
    realized_closed_leg_r: float,
    existing_open_stop_rs: Sequence[float],
    new_leg_stop_if_hit_r_per_full_size: float,
    estimated_remaining_cost_r: float,
    requested_size: float = 1.0,
    min_size: float = 0.01,
) -> RiskBankPlan:
    before = aggregate_worst_case_r(
        realized_closed_leg_r=realized_closed_leg_r,
        open_leg_stop_if_hit_rs=existing_open_stop_rs,
        estimated_remaining_cost_r=estimated_remaining_cost_r,
    )
    max_size = max_new_leg_size(
        realized_closed_leg_r=realized_closed_leg_r,
        existing_open_stop_rs=existing_open_stop_rs,
        new_leg_stop_if_hit_r_per_full_size=new_leg_stop_if_hit_r_per_full_size,
        estimated_remaining_cost_r=estimated_remaining_cost_r,
    )
    if max_size <= 0 or max_size < min_size:
        return RiskBankPlan("BLOCKED_RISK_BANK", requested_size, 0.0, before, None, round(max_size, 10), "max_size_below_min")
    accepted = min(requested_size, max_size)
    status = "ACCEPTED_FULL_SIZE" if accepted >= requested_size - EPS else "ACCEPTED_RESIZED"
    after = aggregate_worst_case_r(
        realized_closed_leg_r=realized_closed_leg_r,
        open_leg_stop_if_hit_rs=[*existing_open_stop_rs, new_leg_stop_if_hit_r_per_full_size * accepted],
        estimated_remaining_cost_r=estimated_remaining_cost_r,
    )
    if after < SETUP_FLOOR_R - EPS:
        return RiskBankPlan("BLOCKED_RISK_BANK", requested_size, 0.0, before, after, round(max_size, 10), "invariant_violation")
    return RiskBankPlan(status, requested_size, round(accepted, 10), before, after, round(max_size, 10), None)


def finalized_unfilled_pending(realized_closed_leg_r: float) -> float:
    return realized_closed_leg_r


def completed_leg_cost(total_completed_legs: int, cost_r_per_completed_leg: float) -> float:
    return round(total_completed_legs * cost_r_per_completed_leg, 10)


def normal_approx_p_value(values: list[float]) -> dict[str, Any]:
    if len(values) < 2:
        return {"status": "not_computable", "reason": "n_lt_2"}
    sd = statistics.stdev(values)
    if sd <= 0:
        return {"status": "not_computable", "reason": "zero_variance"}
    mean_value = statistics.mean(values)
    z = mean_value / (sd / math.sqrt(len(values)))
    p = math.erfc(abs(z) / math.sqrt(2.0))
    return {
        "status": "raw_normal_approx_discovery_only",
        "n": len(values),
        "mean": round(mean_value, 6),
        "z": round(z, 6),
        "two_sided_p": p,
    }


def side_sign(side: str) -> int:
    return 1 if side.upper() == "LONG" else -1


def r_distance(entry: float, stop: float) -> float:
    return abs(entry - stop)


def price_from_r(entry: float, base_r: float, side: str, r_value: float) -> float:
    return entry + side_sign(side) * base_r * r_value


def r_from_price(entry: float, base_r: float, side: str, price: float) -> float:
    return side_sign(side) * (price - entry) / base_r


def hit_reentry(*, side: str, price: float, high: float, low: float) -> bool:
    return low <= price if side.upper() == "LONG" else high >= price


def hit_stop(*, side: str, stop_price: float, high: float, low: float) -> bool:
    return low <= stop_price if side.upper() == "LONG" else high >= stop_price


def hit_target(*, side: str, target_price: float, high: float, low: float) -> bool:
    return high >= target_price if side.upper() == "LONG" else low <= target_price


def classify_same_row_fill_exit(
    *,
    side: str,
    fill_price: float,
    stop_price: float,
    target_price: float,
    high: float,
    low: float,
) -> dict[str, Any]:
    filled = hit_reentry(side=side, price=fill_price, high=high, low=low)
    stop = hit_stop(side=side, stop_price=stop_price, high=high, low=low)
    target = hit_target(side=side, target_price=target_price, high=high, low=low)
    ambiguous = filled and (stop or target)
    return {
        "filled": filled,
        "stop_hit_same_row": stop,
        "target_hit_same_row": target,
        "ambiguous": ambiguous,
        "status": "AMBIGUOUS_FILL_EXIT_SAME_ROW" if ambiguous else "ORDERABLE_AFTER_FILL_ROW",
    }


def load_variant_spec(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
        raise ValueError("V3 variant spec must preserve NO_PROMOTION_VERDICT")
    if not data.get("pre_registered_before_outcome_run"):
        raise ValueError("V3 variant spec must declare pre-registration before outcome run")
    return data


def load_events(event_log_path: str | Path) -> dict[str, dict[str, dict[str, Any]]]:
    return v2.load_event_rows(event_log_path, variants=V2_VARIANTS)


def net_r(row: Mapping[str, Any], cost_key: str) -> float | None:
    value = (row.get("net_r_by_cost") or {}).get(cost_key)
    return None if value is None else float(value)


def first_lock(row: Mapping[str, Any]) -> dict[str, Any] | None:
    return v2.first_lock(dict(row))


def event_year(row: Mapping[str, Any]) -> int | None:
    dt = parse_utc(row.get("candle_close_utc"))
    return dt.year if dt else None


def event_quarter(row: Mapping[str, Any]) -> str | None:
    dt = parse_utc(row.get("candle_close_utc"))
    return f"{dt.year}Q{((dt.month - 1) // 3) + 1}" if dt else None


def sequence_bucket(fvg_lock: Mapping[str, Any] | None, ob_lock: Mapping[str, Any] | None) -> str | None:
    if not fvg_lock or not ob_lock:
        return None
    fvg_time = str(fvg_lock.get("confirmed_time") or "")
    ob_time = str(ob_lock.get("confirmed_time") or "")
    if fvg_time < ob_time:
        return "fvg_then_ob"
    if ob_time < fvg_time:
        return "ob_then_fvg"
    return "same_time"


def variant_lock_for_event(
    *,
    variant_id: str,
    rows: Mapping[str, Mapping[str, Any]],
    cost_key: str,
) -> tuple[dict[str, Any] | None, str | None]:
    fvg_lock = first_lock(rows.get(FVG, {}))
    ob_lock = first_lock(rows.get(OB, {}))
    fvg_r = net_r(rows.get(FVG, {}), cost_key)
    ob_r = net_r(rows.get(OB, {}), cost_key)
    j46_r = net_r(rows.get(BASELINE, {}), cost_key)
    if variant_id in ("V3_OB_LOCK_PULLBACK_RISK_BANK", "V3_OB_LOCK_COST_AWARE_MIN_R"):
        if not ob_lock or float(ob_lock.get("floor_r") or 0.0) <= 0:
            return None, "NO_POSITIVE_OB_LOCK"
        if variant_id == "V3_OB_LOCK_COST_AWARE_MIN_R":
            floor = float(ob_lock.get("floor_r") or 0.0)
            if 6.0 - floor < 1.0:
                return None, "LOW_INCREMENTAL_TARGET_POTENTIAL"
        return dict(ob_lock), None
    if variant_id == "V3_FVG_THEN_OB_TAIL_RISK_BANK":
        if not fvg_lock or not ob_lock:
            return None, "FVG_AND_OB_BOTH_REQUIRED"
        if sequence_bucket(fvg_lock, ob_lock) != "fvg_then_ob":
            return None, "SEQUENCE_NOT_FVG_THEN_OB"
        if ob_r is None or fvg_r is None or ob_r <= fvg_r:
            return None, "OB_NOT_BETTER_THAN_FVG_ON_SOURCE_EVENT"
        if float(ob_lock.get("floor_r") or 0.0) <= 0:
            return None, "NO_POSITIVE_OB_LOCK"
        return dict(ob_lock), None
    if variant_id == "V3_FVG_ONLY_RESCUE_RISK_BANK":
        if not fvg_lock:
            return None, "NO_FVG_LOCK"
        if ob_lock:
            return None, "OB_LOCK_PRESENT"
        if fvg_r is None or j46_r is None or ob_r is None or not (fvg_r > j46_r and fvg_r > ob_r):
            return None, "FVG_NOT_RESCUE_WINNER"
        if float(fvg_lock.get("floor_r") or 0.0) <= 0:
            return None, "NO_POSITIVE_FVG_LOCK"
        return dict(fvg_lock), None
    return None, f"UNKNOWN_VARIANT_{variant_id}"


def selected_rows_after_lock(
    *,
    symbol: str,
    timeframe: str,
    lock_time: datetime,
    hold_bars: int,
    indexes: Mapping[tuple[str, str], PathIndex],
) -> list[dict[str, Any]]:
    index = indexes.get((symbol, timeframe))
    if index is None:
        return []
    deadline = lock_time + timedelta(minutes=15 * hold_bars)
    return index.between(lock_time, deadline)


def simulate_reentry_leg(
    *,
    side: str,
    original_entry: float,
    original_sl: float,
    reentry_price: float,
    target_price: float,
    rows_after_lock: Sequence[Mapping[str, Any]],
    cost_r: float,
    size: float,
) -> dict[str, Any]:
    base_r = r_distance(original_entry, original_sl)
    if base_r <= 0:
        return {"fill_status": "INVALID_BASE_R", "path_synthetic_r": None, "ambiguity_flags": ["DEGENERATE_BASE_R"]}
    stop_price = original_entry
    fill_time: str | None = None
    rows_after_fill: list[Mapping[str, Any]] = []
    for index, row in enumerate(rows_after_lock):
        high, low, close = high_low_close(row)
        if high is None or low is None or close is None:
            continue
        if not hit_reentry(side=side, price=reentry_price, high=high, low=low):
            continue
        fill_time = iso(row.get("time"))
        ambiguity = classify_same_row_fill_exit(
            side=side,
            fill_price=reentry_price,
            stop_price=stop_price,
            target_price=target_price,
            high=high,
            low=low,
        )
        if ambiguity["ambiguous"]:
            stop_r = r_from_price(reentry_price, base_r, side, stop_price)
            target_r = r_from_price(reentry_price, base_r, side, target_price)
            return {
                "fill_status": "FILLED_AMBIGUOUS_SAME_ROW",
                "fill_time_utc": fill_time,
                "exit_time_utc": fill_time,
                "reentry_outcome": "AMBIGUOUS_FILL_EXIT_SAME_ROW",
                "path_synthetic_r": None,
                "bounded_pessimistic_reentry_r": round(stop_r - cost_r, 6),
                "bounded_optimistic_reentry_r": round(target_r - cost_r, 6),
                "ambiguity_flags": ["SAME_ROW_REENTRY_FILL_AND_EXIT_AMBIGUOUS"],
            }
        rows_after_fill = list(rows_after_lock[index + 1 :])
        break
    if fill_time is None:
        return {
            "fill_status": "UNFILLED_REENTRY_PENDING",
            "fill_time_utc": None,
            "exit_time_utc": None,
            "reentry_outcome": "UNFILLED",
            "path_synthetic_r": 0.0,
            "ambiguity_flags": [],
        }
    last_close = reentry_price
    last_time = fill_time
    for row in rows_after_fill:
        high, low, close = high_low_close(row)
        if high is None or low is None or close is None:
            continue
        last_close = close
        last_time = iso(row.get("time"))
        if hit_stop(side=side, stop_price=stop_price, high=high, low=low):
            gross = r_from_price(reentry_price, base_r, side, stop_price)
            return {
                "fill_status": "FILLED_RESOLVED",
                "fill_time_utc": fill_time,
                "exit_time_utc": last_time,
                "reentry_outcome": "STOP",
                "path_synthetic_r": round(size * (gross - cost_r), 6),
                "gross_reentry_r": round(gross, 6),
                "ambiguity_flags": [],
            }
        if hit_target(side=side, target_price=target_price, high=high, low=low):
            gross = r_from_price(reentry_price, base_r, side, target_price)
            return {
                "fill_status": "FILLED_RESOLVED",
                "fill_time_utc": fill_time,
                "exit_time_utc": last_time,
                "reentry_outcome": "TARGET",
                "path_synthetic_r": round(size * (gross - cost_r), 6),
                "gross_reentry_r": round(gross, 6),
                "ambiguity_flags": [],
            }
    gross = r_from_price(reentry_price, base_r, side, last_close)
    return {
        "fill_status": "FILLED_RESOLVED",
        "fill_time_utc": fill_time,
        "exit_time_utc": last_time,
        "reentry_outcome": "TIMEOUT",
        "path_synthetic_r": round(size * (gross - cost_r), 6),
        "gross_reentry_r": round(gross, 6),
        "ambiguity_flags": [],
    }


def replay_variant_event(
    *,
    variant: Mapping[str, Any],
    event_key: str,
    rows: Mapping[str, Mapping[str, Any]],
    indexes: Mapping[tuple[str, str], PathIndex],
    cost_key: str,
    cost_r: float,
    hold_bars: int,
) -> dict[str, Any]:
    j46 = rows[BASELINE]
    side = str(j46.get("mechanical_side") or "").upper()
    entry = float(j46["mechanical_entry"])
    sl = float(j46["mechanical_sl"])
    base_r = r_distance(entry, sl)
    lock, skip_reason = variant_lock_for_event(variant_id=str(variant["variant_id"]), rows=rows, cost_key=cost_key)
    common = {
        "setup_id": event_key,
        "variant_id": variant["variant_id"],
        "symbol": j46.get("symbol"),
        "session": j46.get("session"),
        "side": side,
        "role": j46.get("role"),
        "raw_cohort_key": j46.get("raw_cohort_key"),
        **parse_cohort(j46.get("raw_cohort_key")),
        "year": event_year(j46),
        "quarter": event_quarter(j46),
        "setup_decision_close_utc": j46.get("candle_close_utc"),
        "actual_broker_r": None,
        "actual_broker_r_source": "not_available_in_v2_event_log",
        "j46_path_synthetic_r": net_r(j46, cost_key),
        "v2_fvg_path_synthetic_r": net_r(rows[FVG], cost_key),
        "v2_ob_path_synthetic_r": net_r(rows[OB], cost_key),
        "v2_composite_path_synthetic_r": net_r(rows[COMPOSITE], cost_key),
        "label_policy": "actual broker R is never overwritten by V3 path_synthetic_r",
    }
    if base_r <= 0:
        return {**common, "eligibility": "SKIPPED", "skip_reason": "DEGENERATE_BASE_R", "path_synthetic_r": None}
    if lock is None:
        return {**common, "eligibility": "SKIPPED", "skip_reason": skip_reason, "path_synthetic_r": None}
    lock_time = parse_utc(lock.get("confirmed_time"))
    floor_r = float(lock.get("floor_r") or 0.0)
    if lock_time is None or floor_r <= 0:
        return {**common, "eligibility": "SKIPPED", "skip_reason": "INVALID_LOCK_TIME_OR_FLOOR", "path_synthetic_r": None}
    lock_price = float(lock.get("price") or price_from_r(entry, base_r, side, floor_r))
    target_price = price_from_r(entry, base_r, side, 6.0)
    initial_closed_net = floor_r - cost_r
    stop_if_hit_full_size = -abs(lock_price - entry) / base_r
    plan = plan_new_leg(
        realized_closed_leg_r=initial_closed_net,
        existing_open_stop_rs=[],
        new_leg_stop_if_hit_r_per_full_size=stop_if_hit_full_size,
        estimated_remaining_cost_r=cost_r,
        requested_size=1.0,
        min_size=0.01,
    )
    if plan.status == "BLOCKED_RISK_BANK":
        return {
            **common,
            "eligibility": "ELIGIBLE_LOCK",
            "reentry_status": "BLOCKED_RISK_BANK",
            "lock": lock,
            "initial_closed_net_r": round(initial_closed_net, 6),
            "risk_bank": plan.__dict__,
            "path_synthetic_r": round(initial_closed_net, 6),
            "fill_status": "NOT_ARMED",
            "ambiguity_flags": ["RISK_BANK_BLOCKED_REENTRY"],
        }
    timeframe_source = FVG if variant["variant_id"] == "V3_FVG_ONLY_RESCUE_RISK_BANK" else OB
    timeframe = str(rows[timeframe_source].get("selected_timeframe") or j46.get("selected_timeframe") or "M15")
    path_rows = selected_rows_after_lock(
        symbol=str(j46.get("symbol")),
        timeframe=timeframe,
        lock_time=lock_time,
        hold_bars=hold_bars,
        indexes=indexes,
    )
    if not path_rows:
        return {
            **common,
            "eligibility": "ELIGIBLE_LOCK",
            "reentry_status": plan.status,
            "lock": lock,
            "selected_timeframe": timeframe,
            "initial_closed_net_r": round(initial_closed_net, 6),
            "risk_bank": plan.__dict__,
            "path_synthetic_r": None,
            "fill_status": "UNRESOLVED_NO_POST_LOCK_PATH_ROWS",
            "ambiguity_flags": ["NO_POST_LOCK_PATH_ROWS"],
        }
    reentry = simulate_reentry_leg(
        side=side,
        original_entry=entry,
        original_sl=sl,
        reentry_price=lock_price,
        target_price=target_price,
        rows_after_lock=path_rows,
        cost_r=cost_r,
        size=plan.accepted_size,
    )
    total = None
    if reentry.get("path_synthetic_r") is not None:
        total = round(initial_closed_net + float(reentry["path_synthetic_r"]), 6)
    return {
        **common,
        "eligibility": "ELIGIBLE_LOCK",
        "reentry_status": plan.status,
        "selected_timeframe": timeframe,
        "lock": lock,
        "initial_closed_net_r": round(initial_closed_net, 6),
        "reentry_price": round(lock_price, 10),
        "reentry_stop_price": round(entry, 10),
        "reentry_target_price": round(target_price, 10),
        "risk_bank": plan.__dict__,
        "path_rows_after_lock": len(path_rows),
        "fill_status": reentry.get("fill_status"),
        "fill_time_utc": reentry.get("fill_time_utc"),
        "exit_time_utc": reentry.get("exit_time_utc"),
        "reentry_outcome": reentry.get("reentry_outcome"),
        "reentry_path_synthetic_r": reentry.get("path_synthetic_r"),
        "path_synthetic_r": total,
        "bounded_pessimistic_total_r": round(initial_closed_net + float(reentry.get("bounded_pessimistic_reentry_r", 0.0)), 6)
        if reentry.get("bounded_pessimistic_reentry_r") is not None
        else None,
        "bounded_optimistic_total_r": round(initial_closed_net + float(reentry.get("bounded_optimistic_reentry_r", 0.0)), 6)
        if reentry.get("bounded_optimistic_reentry_r") is not None
        else None,
        "ambiguity_flags": reentry.get("ambiguity_flags", []),
    }


def build_records(
    *,
    event_log_path: str | Path,
    variant_spec: Mapping[str, Any],
    data_roots: Sequence[str | Path],
    cost_key: str,
) -> list[dict[str, Any]]:
    by_event = load_events(event_log_path)
    complete = {
        key: rows
        for key, rows in by_event.items()
        if all(variant in rows for variant in V2_VARIANTS)
        and rows[BASELINE].get("mechanical_entry") is not None
        and net_r(rows[BASELINE], cost_key) is not None
    }
    indexes = load_path_indexes((rows[BASELINE]["symbol"] for rows in complete.values()), [Path(path) for path in data_roots])
    cost_r = float(variant_spec.get("cost_r_per_completed_leg", 0.05))
    hold_bars = int((variant_spec.get("common_replay_rules") or {}).get("reentry_hold_window_m15_bars") or 12)
    records = []
    for event_key, rows in complete.items():
        for variant in variant_spec["variants"]:
            records.append(
                replay_variant_event(
                    variant=variant,
                    event_key=event_key,
                    rows=rows,
                    indexes=indexes,
                    cost_key=cost_key,
                    cost_r=cost_r,
                    hold_bars=hold_bars,
                )
            )
    return records


def mean(values: Iterable[float]) -> float | None:
    vals = list(values)
    if not vals:
        return None
    return round(sum(vals) / len(vals), 6)


def median(values: Iterable[float]) -> float | None:
    vals = sorted(values)
    if not vals:
        return None
    return round(statistics.median(vals), 6)


def percentile(values: Iterable[float], q: float) -> float | None:
    vals = sorted(values)
    if not vals:
        return None
    idx = min(len(vals) - 1, max(0, int(round((len(vals) - 1) * q))))
    return round(vals[idx], 6)


def variant_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    out = {}
    for variant_id, rows in sorted(group_by(records, "variant_id").items()):
        eligible = [row for row in rows if row.get("eligibility") == "ELIGIBLE_LOCK"]
        headline = [float(row["path_synthetic_r"]) for row in eligible if row.get("path_synthetic_r") is not None]
        deltas_j46 = [
            float(row["path_synthetic_r"]) - float(row["j46_path_synthetic_r"])
            for row in eligible
            if row.get("path_synthetic_r") is not None and row.get("j46_path_synthetic_r") is not None
        ]
        out[variant_id] = {
            "rows_seen": len(rows),
            "eligible_n": len(eligible),
            "headline_resolved_n": len(headline),
            "skipped_n": len(rows) - len(eligible),
            "fill_status_counts": dict(Counter(row.get("fill_status") for row in eligible)),
            "reentry_status_counts": dict(Counter(row.get("reentry_status") for row in eligible)),
            "ambiguity_n": sum(bool(row.get("ambiguity_flags")) for row in eligible),
            "ambiguity_rate": round(sum(bool(row.get("ambiguity_flags")) for row in eligible) / len(eligible), 6)
            if eligible
            else None,
            "fill_rate": round(
                sum(str(row.get("fill_status", "")).startswith("FILLED") for row in eligible) / len(eligible), 6
            )
            if eligible
            else None,
            "mean_r": mean(headline),
            "median_r": median(headline),
            "sum_r": round(sum(headline), 6),
            "win_rate_gt_zero": round(sum(value > 0 for value in headline) / len(headline), 6) if headline else None,
            "loss_tail_p10": percentile(headline, 0.10),
            "min_r": min(headline) if headline else None,
            "mean_delta_vs_j46": mean(deltas_j46),
            "sum_delta_vs_j46": round(sum(deltas_j46), 6),
            "raw_p_delta_vs_j46": normal_approx_p_value(deltas_j46),
        }
    return out


def group_by(rows: Iterable[dict[str, Any]], key: str) -> dict[Any, list[dict[str, Any]]]:
    out: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        out[row.get(key)].append(row)
    return out


def dimension_summary(records: list[dict[str, Any]], dimensions: tuple[str, ...]) -> list[dict[str, Any]]:
    rows = [row for row in records if row.get("eligibility") == "ELIGIBLE_LOCK" and row.get("path_synthetic_r") is not None]
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(dim) for dim in dimensions)].append(row)
    out = []
    for key, members in grouped.items():
        values = [float(row["path_synthetic_r"]) for row in members]
        deltas = [float(row["path_synthetic_r"]) - float(row["j46_path_synthetic_r"]) for row in members]
        out.append(
            {
                "dimensions": dict(zip(dimensions, key)),
                "n": len(members),
                "mean_r": mean(values),
                "sum_r": round(sum(values), 6),
                "mean_delta_vs_j46": mean(deltas),
                "sum_delta_vs_j46": round(sum(deltas), 6),
            }
        )
    return sorted(out, key=lambda row: abs(float(row["sum_delta_vs_j46"])), reverse=True)


def contribution_concentration(records: list[dict[str, Any]], dimensions: tuple[str, ...]) -> dict[str, Any]:
    rows = [row for row in records if row.get("eligibility") == "ELIGIBLE_LOCK" and row.get("path_synthetic_r") is not None]
    grouped: dict[tuple[Any, ...], float] = defaultdict(float)
    for row in rows:
        delta = float(row["path_synthetic_r"]) - float(row["j46_path_synthetic_r"])
        grouped[tuple(row.get(dim) for dim in dimensions)] += max(0.0, delta)
    total = sum(grouped.values())
    ranked = [
        {
            "dimensions": dict(zip(dimensions, key)),
            "positive_delta_contribution": round(value, 6),
            "share": round(value / total, 6) if total > 0 else None,
        }
        for key, value in sorted(grouped.items(), key=lambda item: item[1], reverse=True)
    ]
    return {
        "dimensions": list(dimensions),
        "total_positive_delta": round(total, 6),
        "top_share": ranked[0]["share"] if ranked else None,
        "top_groups": ranked[:10],
    }


def taxonomy(row: Mapping[str, Any]) -> str:
    if row.get("path_synthetic_r") is None:
        if "SAME_ROW_REENTRY_FILL_AND_EXIT_AMBIGUOUS" in (row.get("ambiguity_flags") or []):
            return "ambiguous_same_row_fill_exit"
        return "unresolved_path"
    v3 = float(row["path_synthetic_r"])
    j46 = float(row["j46_path_synthetic_r"])
    if row.get("fill_status") == "UNFILLED_REENTRY_PENDING":
        return "unfilled_reentry_initial_lock_only_better" if v3 > j46 else "unfilled_reentry_closed_too_early"
    if row.get("reentry_outcome") == "TARGET":
        return "reentry_target_after_pullback"
    if row.get("reentry_outcome") == "STOP":
        return "reentry_stop_gave_back_locked_profit"
    if row.get("reentry_outcome") == "TIMEOUT":
        return "reentry_timeout_path_dependent"
    return "other_resolved"


def taxonomy_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [row for row in records if row.get("eligibility") == "ELIGIBLE_LOCK"]
    out = {}
    for variant_id, rows in sorted(group_by(eligible, "variant_id").items()):
        counts = Counter(taxonomy(row) for row in rows)
        out[variant_id] = dict(counts)
    return out


def casebook(records: list[dict[str, Any]], limit: int = 80) -> list[dict[str, Any]]:
    eligible = [row for row in records if row.get("eligibility") == "ELIGIBLE_LOCK"]
    resolved = [row for row in eligible if row.get("path_synthetic_r") is not None]
    winners = sorted(resolved, key=lambda row: float(row["path_synthetic_r"]) - float(row["j46_path_synthetic_r"]), reverse=True)[: limit // 4]
    losers = sorted(resolved, key=lambda row: float(row["path_synthetic_r"]) - float(row["j46_path_synthetic_r"]))[: limit // 4]
    ambiguous = [row for row in eligible if row.get("path_synthetic_r") is None][: limit // 4]
    unfilled = [row for row in eligible if row.get("fill_status") == "UNFILLED_REENTRY_PENDING"][: limit // 4]
    selected = winners + losers + ambiguous + unfilled
    keys = [
        "setup_id",
        "variant_id",
        "symbol",
        "session",
        "side",
        "regime",
        "year",
        "path_synthetic_r",
        "j46_path_synthetic_r",
        "v2_ob_path_synthetic_r",
        "v2_fvg_path_synthetic_r",
        "fill_status",
        "reentry_outcome",
        "selected_timeframe",
        "ambiguity_flags",
    ]
    return [{key: row.get(key) for key in keys} | {"taxonomy": taxonomy(row)} for row in selected]


def methodology_diagnostics(records: list[dict[str, Any]], variant_ids: list[str]) -> dict[str, Any]:
    return {
        "variant_count": len(variant_ids),
        "dsr": {
            "status": "not_computable",
            "reason": "same_dataset_discovery_variants_not_frozen_unseen_validation; DSR would be promotion-style misuse",
        },
        "pbo": {
            "status": "not_computable",
            "reason": "no CSCV matrix of pre-registered folds for V3; current run is exploratory full-corpus replay",
        },
        "effective_n_proxy": {
            "status": "proxy_only_not_promotion_effective_n",
            "by_variant_symbol_session_side_year_groups": {
                variant_id: len(
                    {
                        (row.get("symbol"), row.get("session"), row.get("side"), row.get("year"))
                        for row in records
                        if row.get("variant_id") == variant_id
                        and row.get("eligibility") == "ELIGIBLE_LOCK"
                        and row.get("path_synthetic_r") is not None
                    }
                )
                for variant_id in variant_ids
            },
        },
    }


def build_payload(
    *,
    event_log_path: str | Path = DEFAULT_EVENT_LOG,
    variant_spec_path: str | Path = DEFAULT_VARIANT_SPEC,
    data_roots: Sequence[str | Path] = DEFAULT_DATA_ROOTS,
    cost_key: str = "0.05",
) -> dict[str, Any]:
    spec = load_variant_spec(variant_spec_path)
    records = build_records(event_log_path=event_log_path, variant_spec=spec, data_roots=data_roots, cost_key=cost_key)
    variant_ids = [str(item["variant_id"]) for item in spec["variants"]]
    return {
        "schema_version": "raw_ohlc_path_scaling_v3_full_exploratory_replay_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "discovery_label": "DISCOVERY_ONLY_NOT_REGISTERED",
        "inputs": {
            "event_log_path": str(event_log_path),
            "variant_spec_path": str(variant_spec_path),
            "data_roots": [str(path) for path in data_roots],
            "cost_key": cost_key,
        },
        "pre_registered_variants": spec,
        "label_policy": {
            "actual_broker_r": "not available in V2 event log and never overwritten",
            "path_synthetic_r": "V3 replay output only",
            "fill_no_fill": "reported per reentry leg; unfilled pending contributes no reentry realized R",
        },
        "summary": variant_summary(records),
        "dimension_summaries": {
            "by_symbol": dimension_summary(records, ("variant_id", "symbol")),
            "by_session": dimension_summary(records, ("variant_id", "session")),
            "by_side": dimension_summary(records, ("variant_id", "side")),
            "by_regime": dimension_summary(records, ("variant_id", "regime")),
            "by_year": dimension_summary(records, ("variant_id", "year")),
            "by_symbol_session_side": dimension_summary(records, ("variant_id", "symbol", "session", "side")),
        },
        "concentration": {
            "symbol_session_side": {
                variant_id: contribution_concentration(
                    [row for row in records if row.get("variant_id") == variant_id],
                    ("symbol", "session", "side"),
                )
                for variant_id in variant_ids
            },
            "year": {
                variant_id: contribution_concentration(
                    [row for row in records if row.get("variant_id") == variant_id],
                    ("year",),
                )
                for variant_id in variant_ids
            },
        },
        "taxonomy": taxonomy_summary(records),
        "methodology_diagnostics": methodology_diagnostics(records, variant_ids),
        "casebook": casebook(records),
        "records": records,
        "interpretation": {
            "what_v3_is_trying_to_capture": (
                "A bounded way to recycle locked structural progress: close initial exposure at a "
                "confirmed FVG/OB floor, then test whether a pullback to that floor can be reentered "
                "without pushing aggregate setup worst-case below -1R."
            ),
            "likely_structural_signal": (
                "Rows with FVG-then-OB sequence and later successful pullback target are the most "
                "structurally interpretable. FVG-only rows are a separate rescue pocket but carry "
                "higher concentration risk from P1-A."
            ),
            "likely_artifacts": [
                "The replay uses selected OHLC rows, not broker lifecycle telemetry.",
                "The original POI bounds are missing, so reentry level quality is inferred from structural lock metadata.",
                "Same-row fill/exit ambiguity is bounded, not guessed.",
                "Same-dataset variant selection is not validation.",
            ],
            "next_hypotheses": [
                "Forward-log original POI bounds and pending lifecycle fields before any V3 promotion lane.",
                "Test FVG-then-OB tail preservation on post-cutoff V2b rows first.",
                "Add broker/tick costs and close-side slippage before reentry sizing research gets promoted beyond discovery.",
            ],
        },
    }


def write_json(payload: dict[str, Any], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    safe = dict(payload)
    safe.pop("records", None)
    out.write_text(json.dumps(safe, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_casebook(rows: list[dict[str, Any]], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value).replace("|", r"\|")


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(value) for value in row) + " |")
    return lines


def write_markdown(payload: dict[str, Any], path: str | Path) -> None:
    lines = [
        "# Raw OHLC Path Scaling V3 Full Exploratory Replay",
        "",
        "Date: 2026-05-03",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        f"Discovery label: `{payload['discovery_label']}`",
        "",
        "## Pre-Registration",
        "",
        f"Variant sidecar: `{payload['inputs']['variant_spec_path']}`",
        "",
        *table(
            ["variant", "family", "status", "mechanism"],
            [
                [
                    item["variant_id"],
                    item["family"],
                    item["status"],
                    item["mechanism"],
                ]
                for item in payload["pre_registered_variants"]["variants"]
            ],
        ),
        "",
        "## Label Separation",
        "",
        *[f"- `{key}`: {value}" for key, value in payload["label_policy"].items()],
        "",
        "## Variant Summary",
        "",
        *table(
            [
                "variant",
                "eligible",
                "resolved",
                "fill rate",
                "ambiguity rate",
                "mean R",
                "median R",
                "sum R",
                "WR > 0",
                "p10",
                "mean delta vs J46",
            ],
            [
                [
                    variant,
                    row["eligible_n"],
                    row["headline_resolved_n"],
                    row["fill_rate"],
                    row["ambiguity_rate"],
                    row["mean_r"],
                    row["median_r"],
                    row["sum_r"],
                    row["win_rate_gt_zero"],
                    row["loss_tail_p10"],
                    row["mean_delta_vs_j46"],
                ]
                for variant, row in payload["summary"].items()
            ],
        ),
        "",
        "## Fill And Risk Status",
        "",
        *table(
            ["variant", "fill status counts", "risk-bank status counts"],
            [
                [variant, row["fill_status_counts"], row["reentry_status_counts"]]
                for variant, row in payload["summary"].items()
            ],
        ),
        "",
        "## Taxonomy",
        "",
        *table(
            ["variant", "taxonomy counts"],
            [[variant, counts] for variant, counts in payload["taxonomy"].items()],
        ),
        "",
        "## Concentration",
        "",
        *table(
            ["variant", "top symbol/session/side share", "top group", "top year share", "top year"],
            [
                [
                    variant,
                    payload["concentration"]["symbol_session_side"][variant]["top_share"],
                    (payload["concentration"]["symbol_session_side"][variant]["top_groups"] or [{}])[0].get("dimensions"),
                    payload["concentration"]["year"][variant]["top_share"],
                    (payload["concentration"]["year"][variant]["top_groups"] or [{}])[0].get("dimensions"),
                ]
                for variant in payload["summary"]
            ],
        ),
        "",
        "## Methodology Diagnostics",
        "",
        f"- Variant count: `{payload['methodology_diagnostics']['variant_count']}`.",
        f"- DSR: `{payload['methodology_diagnostics']['dsr']['status']}` because {payload['methodology_diagnostics']['dsr']['reason']}.",
        f"- PBO: `{payload['methodology_diagnostics']['pbo']['status']}` because {payload['methodology_diagnostics']['pbo']['reason']}.",
        f"- Effective-N proxy: `{payload['methodology_diagnostics']['effective_n_proxy']['status']}`.",
        "",
        "## Interpretation",
        "",
        f"- What V3 appears to capture: {payload['interpretation']['what_v3_is_trying_to_capture']}",
        f"- Likely structural signal: {payload['interpretation']['likely_structural_signal']}",
        "",
        "Likely artifacts:",
        "",
        *[f"- {item}" for item in payload["interpretation"]["likely_artifacts"]],
        "",
        "Next hypotheses:",
        "",
        *[f"{idx}. {item}" for idx, item in enumerate(payload["interpretation"]["next_hypotheses"], start=1)],
        "",
        "## Casebook",
        "",
        f"Representative casebook rows are in `{DEFAULT_CASEBOOK_JSONL}`.",
        "",
    ]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-log", default=DEFAULT_EVENT_LOG)
    parser.add_argument("--variant-spec", default=DEFAULT_VARIANT_SPEC)
    parser.add_argument("--data-root", action="append", default=None)
    parser.add_argument("--cost-key", default="0.05")
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--casebook-jsonl", default=DEFAULT_CASEBOOK_JSONL)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(
        event_log_path=args.event_log,
        variant_spec_path=args.variant_spec,
        data_roots=args.data_root or DEFAULT_DATA_ROOTS,
        cost_key=args.cost_key,
    )
    write_json(payload, args.output_json)
    write_casebook(payload["casebook"], args.casebook_jsonl)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.casebook_jsonl}")
    print(f"wrote {args.output_md}")
    print(
        "variants="
        + ",".join(payload["summary"].keys())
        + f" promotion={payload['promotion_verdict']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
