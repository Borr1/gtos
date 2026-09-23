"""Run executable May 28-31 vNext execution-policy tournament.

This builder consumes the current weekend price-action anatomy ledger, then
replays each candidate with an event-driven bid/ask simulator. Tick parquet is
used when available; M1 OHLC is a conservative fallback and every same-bar
ordering ambiguity is flagged. The output is route evidence only and performs no
broker actions.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import build_vnext_weekend_price_action_anatomy as anatomy


ROOT = anatomy.ROOT
ROUTE_DIR = anatomy.ROUTE_DIR
ANATOMY_LEDGER = anatomy.ANATOMY_LEDGER
FORENSIC_SUMMARY = anatomy.FORENSIC_SUMMARY

TOURNAMENT_LEDGER = ROUTE_DIR / "LIVE_WEEKEND_EXECUTION_POLICY_TOURNAMENT_LEDGER.jsonl"
TOURNAMENT_SUMMARY = ROUTE_DIR / "LIVE_WEEKEND_EXECUTION_POLICY_TOURNAMENT_SUMMARY.json"
TOURNAMENT_VERIFICATION = ROUTE_DIR / "LIVE_WEEKEND_EXECUTION_POLICY_TOURNAMENT_VERIFICATION.json"
QUALITY_LEDGER = ROUTE_DIR / "LIVE_WEEKEND_CANDIDATE_QUALITY_SELECTOR_LEDGER.jsonl"
POLICY_REPAIR_LEDGER = ROUTE_DIR / "LIVE_WEEKEND_EXECUTION_POLICY_REPAIR_LEDGER.jsonl"
PLACED_AUTOPSY_LEDGER = anatomy.PLACED_AUTOPSY_LEDGER
TOURNAMENT_FINDINGS = ROUTE_DIR / "LIVE_WEEKEND_EXECUTION_POLICY_TOURNAMENT_FINDINGS.md"

DEFAULT_HORIZON = timedelta(hours=48)


@dataclass(frozen=True)
class PolicySpec:
    name: str
    policy_type: str
    trigger_r: float | None = None
    target_r: float | None = None
    partial_fraction: float = 0.0
    be_after_trigger: bool = False
    trail_gap_r: float | None = None
    time_stop_hours: float | None = None
    evidence_role: str = "executable_policy_candidate"


POLICY_SPECS: tuple[PolicySpec, ...] = (
    PolicySpec("no_trade_baseline", "no_trade", evidence_role="baseline"),
    PolicySpec("current_selected_policy", "current_router"),
    PolicySpec("partial_be_runner", "partial_be", trigger_r=1.0, target_r=3.0, partial_fraction=0.5, be_after_trigger=True),
    PolicySpec("momentum_exhaustion", "momentum", trigger_r=1.0, target_r=2.0, trail_gap_r=0.4),
    PolicySpec("fixed_1_5r_comparator", "fixed_target", target_r=1.5, evidence_role="comparator"),
    PolicySpec("be_after_trigger_comparator", "be_target", trigger_r=1.0, target_r=1.5, be_after_trigger=True, evidence_role="comparator"),
    PolicySpec("trailing_1r_gap_0_5_cap_3r", "trailing", trigger_r=1.0, target_r=3.0, trail_gap_r=0.5),
    PolicySpec("trailing_1r_gap_0_75_cap_3r", "trailing", trigger_r=1.0, target_r=3.0, trail_gap_r=0.75),
    PolicySpec("trailing_1_5r_gap_0_5_cap_3r", "trailing", trigger_r=1.5, target_r=3.0, trail_gap_r=0.5),
    PolicySpec("trailing_1r_gap_0_5_no_cap", "trailing", trigger_r=1.0, target_r=None, trail_gap_r=0.5),
    PolicySpec("partial_then_trail_1r_gap_0_5_cap_3r", "partial_trailing", trigger_r=1.0, target_r=3.0, partial_fraction=0.5, be_after_trigger=True, trail_gap_r=0.5),
    PolicySpec("time_stop_2h", "time_stop", time_stop_hours=2.0, evidence_role="comparator"),
    PolicySpec("time_stop_4h", "time_stop", time_stop_hours=4.0, evidence_role="comparator"),
    PolicySpec("time_stop_8h", "time_stop", time_stop_hours=8.0, evidence_role="comparator"),
)

HYBRID_POLICY_SPECS: tuple[tuple[str, str], ...] = (
    ("quality_gate_current_selected_policy", "current_selected_policy"),
    ("quality_gate_partial_be_runner", "partial_be_runner"),
    ("quality_gate_momentum_exhaustion", "momentum_exhaustion"),
    ("quality_gate_trailing_1_5r_gap_0_5_cap_3r", "trailing_1_5r_gap_0_5_cap_3r"),
)

TRADEABLE_SESSION_ORIGIN_RULES: dict[tuple[str, str], dict[str, Any]] = {
    ("london", "liquidity_sweep_reclaim"): {
        "rule_id": "weekend_london_liquidity_sweep_reclaim_positive_current_selected",
        "weekend_rows": 20,
        "weekend_current_selected_gross_r": 7.0,
        "weekend_current_selected_avg_r": 0.35,
    },
    ("london", "displacement_continuation"): {
        "rule_id": "weekend_london_displacement_continuation_positive_current_selected",
        "weekend_rows": 25,
        "weekend_current_selected_gross_r": 3.5,
        "weekend_current_selected_avg_r": 0.14,
    },
}


def policy_variant_count() -> int:
    return len(POLICY_SPECS) + len(HYBRID_POLICY_SPECS)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


def route_artifact_only_descendant(artifact_head: str | None) -> dict[str, Any]:
    current = anatomy.git_head()
    if not artifact_head or artifact_head in {"UNKNOWN", current}:
        return {"allowed": artifact_head == current, "changed_files": [], "disallowed_files": []}
    try:
        diff = subprocess_check(["git", "diff", "--name-only", f"{artifact_head}..{current}"])
    except Exception as exc:
        return {"allowed": False, "error": repr(exc), "changed_files": [], "disallowed_files": []}
    changed = [line.strip().replace("\\", "/") for line in diff.splitlines() if line.strip()]
    route_prefix = "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/"
    disallowed = [path for path in changed if not path.startswith(route_prefix)]
    return {"allowed": bool(changed) and not disallowed, "changed_files": changed, "disallowed_files": disallowed}


def subprocess_check(args: list[str]) -> str:
    import subprocess

    return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            row = json.loads(text)
            row["_ledger_source_path"] = str(path)
            row["_ledger_source_line"] = line_no
            rows.append(row)
    return rows


def load_actual_fill_map() -> dict[str, dict[str, Any]]:
    fills: dict[str, dict[str, Any]] = {}
    for row in load_jsonl(PLACED_AUTOPSY_LEDGER):
        candidate_id = row.get("candidate_id")
        if not candidate_id:
            continue
        for event in row.get("lifecycle_events") or []:
            fill_time = event.get("fill_time_utc")
            entry_price = to_float(event.get("executed_entry_price"))
            if event.get("broker_fill_state") == "filled" and fill_time and entry_price is not None:
                fills[str(candidate_id)] = {
                    "actual_entry_time_utc": fill_time,
                    "actual_entry_price": entry_price,
                    "actual_entry_source": "pending_lifecycle_executed_entry_price",
                    "actual_mt5_position_ticket": event.get("mt5_position_ticket"),
                    "actual_mt5_entry_order_ticket": event.get("mt5_entry_order_ticket"),
                    "actual_mt5_entry_deal_ticket": event.get("mt5_entry_deal_ticket"),
                    "broker_truth_status": row.get("mt5_broker_truth_status") or row.get("broker_truth_status"),
                    "manual_contamination_status": row.get("manual_intervention_status"),
                }
                break
    return fills


def to_float(value: Any) -> float | None:
    return anatomy.as_float(value)


def parse_dt(value: Any) -> datetime | None:
    return anatomy.parse_dt(value)


def iso(dt: datetime | None) -> str | None:
    return anatomy.iso(dt)


def side_r(side: str, entry: float, stop: float, exit_price: float) -> float:
    risk = abs(entry - stop)
    if risk <= 0:
        return 0.0
    if side == "LONG":
        return (exit_price - entry) / risk
    return (entry - exit_price) / risk


def price_at_r(side: str, entry: float, risk: float, r_value: float) -> float:
    if side == "LONG":
        return entry + r_value * risk
    return entry - r_value * risk


def broker_min_distance(row: dict[str, Any]) -> float:
    spec = row.get("broker_spec_snapshot") or {}
    point = to_float(spec.get("point")) or 0.0
    stops_level = to_float(spec.get("trade_stops_level")) or 0.0
    freeze_level = to_float(spec.get("trade_freeze_level")) or 0.0
    explicit = to_float(spec.get("broker_min_stop_distance")) or 0.0
    return max(explicit, stops_level * point, freeze_level * point, 0.0)


def stop_modify_allowed(side: str, desired_stop: float, bid: float, ask: float, min_distance: float) -> bool:
    if min_distance <= 0:
        return True
    if side == "LONG":
        return desired_stop <= bid - min_distance
    return desired_stop >= ask + min_distance


def current_policy_spec(row: dict[str, Any]) -> PolicySpec:
    selected = row.get("selected_policy")
    if selected == "momentum_exhaustion":
        return policy_by_name("momentum_exhaustion")
    if selected == "partial_be_runner":
        return policy_by_name("partial_be_runner")
    if selected == "trailing_runner":
        return policy_by_name("trailing_1r_gap_0_5_cap_3r")
    return policy_by_name("partial_be_runner")


def policy_by_name(name: str) -> PolicySpec:
    for spec in POLICY_SPECS:
        if spec.name == name:
            return spec
    raise KeyError(name)


def effective_policy(row: dict[str, Any], spec: PolicySpec) -> PolicySpec:
    if spec.policy_type == "current_router":
        base = current_policy_spec(row)
        return PolicySpec(
            name=spec.name,
            policy_type=base.policy_type,
            trigger_r=base.trigger_r,
            target_r=base.target_r,
            partial_fraction=base.partial_fraction,
            be_after_trigger=base.be_after_trigger,
            trail_gap_r=base.trail_gap_r,
            time_stop_hours=base.time_stop_hours,
            evidence_role="current_router_projection",
        )
    return spec


def frame_window_ticks(row: dict[str, Any], tick_cache: dict[str, pd.DataFrame | None]) -> pd.DataFrame | None:
    symbol = str(row.get("symbol") or "")
    candle = parse_dt(row.get("candle_time_utc"))
    if not symbol or candle is None:
        return None
    if symbol not in tick_cache:
        tick_cache[symbol] = anatomy.load_ticks(symbol)
    ticks = tick_cache.get(symbol)
    if ticks is None or ticks.empty:
        return None
    start = pd.Timestamp(candle)
    end = pd.Timestamp(candle + DEFAULT_HORIZON)
    window = ticks[(ticks["ts_utc"] >= start) & (ticks["ts_utc"] <= end)]
    return window.reset_index(drop=True) if not window.empty else None


def frame_window_m1(row: dict[str, Any], m1_cache: dict[str, list[anatomy.Bar]]) -> list[anatomy.Bar]:
    symbol = str(row.get("symbol") or "")
    candle = parse_dt(row.get("candle_time_utc"))
    if not symbol or candle is None:
        return []
    if symbol not in m1_cache:
        m1_cache[symbol] = anatomy.load_m1(symbol)
    end = candle + DEFAULT_HORIZON
    return [bar for bar in m1_cache.get(symbol, []) if candle <= bar.time_utc <= end]


def geometry(row: dict[str, Any]) -> tuple[str | None, datetime | None, float | None, float | None, float | None]:
    side = row.get("side")
    candle = parse_dt(row.get("candle_time_utc"))
    entry = to_float(row.get("actual_entry_price")) if row.get("actual_entry_price") is not None else to_float(row.get("repaired_entry"))
    stop = to_float(row.get("repaired_stop_loss"))
    risk = abs(entry - stop) if entry is not None and stop is not None else None
    if side not in {"LONG", "SHORT"} or candle is None or entry is None or stop is None or not risk or risk <= 0:
        return None, candle, entry, stop, risk
    return str(side), candle, entry, stop, risk


def tick_entry_mask(frame: pd.DataFrame, side: str, entry: float) -> pd.Series:
    if side == "LONG":
        return frame["ask"] <= entry
    return frame["bid"] >= entry


def tick_exit_r(side: str, entry: float, stop: float, tick: pd.Series) -> float:
    exit_price = float(tick["bid"] if side == "LONG" else tick["ask"])
    return side_r(side, entry, stop, exit_price)


def tick_exit_price(side: str, tick: pd.Series) -> float:
    return float(tick["bid"] if side == "LONG" else tick["ask"])


def simulate_tick_policy(row: dict[str, Any], tick_frame: pd.DataFrame, spec: PolicySpec) -> dict[str, Any]:
    side, candle, entry, stop, risk = geometry(row)
    if spec.policy_type == "no_trade":
        return result_row(row, spec, "no_trade", 0.0, "tick_bid_ask", "no_trade_baseline", candle, None)
    if spec.policy_type == "current_router" and row.get("selected_policy") not in {"partial_be_runner", "momentum_exhaustion", "trailing_runner"}:
        return result_row(
            row,
            spec,
            "not_computed_missing_selected_policy",
            None,
            "tick_bid_ask",
            "current_selected_policy_absent_from_candidate_packet",
            candle,
            None,
            extra={"tick_coverage_status": "not_evaluated_missing_selected_policy"},
        )
    if side is None or candle is None or entry is None or stop is None or risk is None:
        return result_row(row, spec, "not_simulatable_missing_geometry", None, "tick_bid_ask", "missing_geometry", candle, None)
    if tick_frame is None or tick_frame.empty:
        return result_row(row, spec, "not_simulatable_no_tick_window", None, "tick_bid_ask", "no_tick_window", candle, None)

    actual_entry_time = parse_dt(row.get("actual_entry_time_utc"))
    if actual_entry_time is not None:
        after_actual = tick_frame[tick_frame["ts_utc"] >= pd.Timestamp(actual_entry_time)]
        if after_actual.empty:
            return result_row(
                row,
                spec,
                "not_simulatable_actual_fill_after_tick_window",
                None,
                "tick_bid_ask",
                "actual_broker_fill_time_has_no_following_tick",
                candle,
                actual_entry_time,
                extra={
                    "entry_source": "broker_actual_fill",
                    "tick_coverage_status": "actual_fill_after_tick_window",
                },
            )
        entry_idx = int(after_actual.index[0])
        entry_time = actual_entry_time
    else:
        entry_hits = tick_frame[tick_entry_mask(tick_frame, side, entry)]
        if entry_hits.empty:
            last = tick_frame.iloc[-1]
            return result_row(
                row,
                spec,
                "no_fill_no_entry_touch",
                0.0,
                "tick_bid_ask",
                "entry_not_touched_before_last_tick",
                candle,
                None,
                extra={
                    "price_source_first_utc": iso(tick_frame.iloc[0]["ts_utc"].to_pydatetime()),
                    "price_source_last_utc": iso(last["ts_utc"].to_pydatetime()),
                    "tick_first_utc": iso(tick_frame.iloc[0]["ts_utc"].to_pydatetime()),
                    "tick_last_utc": iso(last["ts_utc"].to_pydatetime()),
                    "tick_rows": int(len(tick_frame)),
                    "tick_coverage_status": "tick_window_present_entry_not_touched",
                    "entry_source": "counterfactual_tick_touch",
                    "entry_price_basis": "ask_touch_for_long_bid_touch_for_short",
                },
            )
        entry_idx = int(entry_hits.index[0])
        entry_time = tick_frame.loc[entry_idx]["ts_utc"].to_pydatetime()

    min_dist = broker_min_distance(row)
    if min_dist <= 0 or (risk and min_dist / risk <= 0.05):
        return simulate_tick_policy_fast(row, tick_frame, spec, entry_idx, entry_time)

    if False:
        last = tick_frame.iloc[-1]
        return result_row(
            row,
            spec,
            "no_fill_no_entry_touch",
            0.0,
            "tick_bid_ask",
            "entry_not_touched_before_last_tick",
            candle,
            None,
            extra={
                "price_source_first_utc": iso(tick_frame.iloc[0]["ts_utc"].to_pydatetime()),
                "price_source_last_utc": iso(last["ts_utc"].to_pydatetime()),
                "tick_rows": int(len(tick_frame)),
            },
        )

    eff = effective_policy(row, spec)
    after = tick_frame.loc[entry_idx:].reset_index(drop=True)
    entry_tick = after.iloc[0]
    current_stop_r = -1.0
    remaining = 1.0
    realized = 0.0
    max_r = -10**9
    min_r = 10**9
    stop_modify_attempts = 0
    stop_modify_rejections = 0
    stop_modify_last_reason = None
    activation_utc = None
    partial_utc = None
    final_utc = None
    stop_utc = None
    time_stop_utc = None
    last_r = 0.0
    open_reason = "open_at_last_tick"
    cost_status = "spread_in_bid_ask_path_commission_swap_not_row_convertible"
    spread_at_entry = float(entry_tick["ask"] - entry_tick["bid"])

    for _, tick in after.iterrows():
        tick_time = tick["ts_utc"].to_pydatetime()
        current_r = tick_exit_r(side, entry, stop, tick)
        last_r = current_r
        max_r = max(max_r, current_r)
        min_r = min(min_r, current_r)

        if current_r <= current_stop_r:
            stop_utc = tick_time
            realized += remaining * current_stop_r
            return result_row(
                row,
                spec,
                "stop_hit",
                realized,
                "tick_bid_ask",
                f"stop_r_{current_stop_r:.4f}_hit",
                candle,
                entry_time,
                exit_time=stop_utc,
                extra=execution_extra(after, max_r, min_r, spread_at_entry, risk, stop_modify_attempts, stop_modify_rejections, stop_modify_last_reason, current_stop_r, cost_status),
            )

        if eff.policy_type == "fixed_target":
            target = eff.target_r or 1.5
            if current_r >= target:
                final_utc = tick_time
                return result_row(row, spec, "fixed_target_hit", target, "tick_bid_ask", "target_hit", candle, entry_time, exit_time=final_utc, extra=execution_extra(after, max_r, min_r, spread_at_entry, risk, stop_modify_attempts, stop_modify_rejections, stop_modify_last_reason, current_stop_r, cost_status))

        elif eff.policy_type == "be_target":
            trigger = eff.trigger_r or 1.0
            target = eff.target_r or 1.5
            if current_r >= trigger and current_stop_r < 0:
                stop_modify_attempts += 1
                desired_stop = price_at_r(side, entry, risk, 0.0)
                if stop_modify_allowed(side, desired_stop, float(tick["bid"]), float(tick["ask"]), min_dist):
                    current_stop_r = 0.0
                    activation_utc = activation_utc or tick_time
                else:
                    stop_modify_rejections += 1
                    stop_modify_last_reason = "broker_stop_or_freeze_distance_rejected_be_modify"
            if current_r >= target:
                final_utc = tick_time
                return result_row(row, spec, "be_target_hit", target, "tick_bid_ask", "target_hit_after_be_trigger", candle, entry_time, exit_time=final_utc, extra=execution_extra(after, max_r, min_r, spread_at_entry, risk, stop_modify_attempts, stop_modify_rejections, stop_modify_last_reason, current_stop_r, cost_status, activation_utc=activation_utc))

        elif eff.policy_type == "partial_be":
            trigger = eff.trigger_r or 1.0
            target = eff.target_r or 3.0
            if partial_utc is None and current_r >= trigger:
                partial_utc = tick_time
                part = eff.partial_fraction
                realized += part * trigger
                remaining -= part
                stop_modify_attempts += 1
                desired_stop = price_at_r(side, entry, risk, 0.0)
                if stop_modify_allowed(side, desired_stop, float(tick["bid"]), float(tick["ask"]), min_dist):
                    current_stop_r = max(current_stop_r, 0.0)
                    activation_utc = activation_utc or tick_time
                else:
                    stop_modify_rejections += 1
                    stop_modify_last_reason = "broker_stop_or_freeze_distance_rejected_be_modify"
            if partial_utc is not None and current_r >= target:
                final_utc = tick_time
                realized += remaining * target
                return result_row(row, spec, "partial_then_final_target", realized, "tick_bid_ask", "partial_1r_final_target_hit", candle, entry_time, exit_time=final_utc, extra=execution_extra(after, max_r, min_r, spread_at_entry, risk, stop_modify_attempts, stop_modify_rejections, stop_modify_last_reason, current_stop_r, cost_status, activation_utc=activation_utc, partial_utc=partial_utc))

        elif eff.policy_type in {"momentum", "trailing", "partial_trailing"}:
            trigger = eff.trigger_r or 1.0
            target = eff.target_r
            gap = eff.trail_gap_r or 0.5
            if eff.policy_type == "partial_trailing" and partial_utc is None and current_r >= trigger:
                partial_utc = tick_time
                part = eff.partial_fraction
                realized += part * trigger
                remaining -= part
                stop_modify_attempts += 1
                desired_stop = price_at_r(side, entry, risk, 0.0)
                if stop_modify_allowed(side, desired_stop, float(tick["bid"]), float(tick["ask"]), min_dist):
                    current_stop_r = max(current_stop_r, 0.0)
                    activation_utc = activation_utc or tick_time
                else:
                    stop_modify_rejections += 1
                    stop_modify_last_reason = "broker_stop_or_freeze_distance_rejected_be_modify"
            if current_r >= trigger:
                activation_utc = activation_utc or tick_time
                desired_stop_r = max(current_stop_r, max_r - gap)
                if desired_stop_r > current_stop_r:
                    stop_modify_attempts += 1
                    desired_stop = price_at_r(side, entry, risk, desired_stop_r)
                    if stop_modify_allowed(side, desired_stop, float(tick["bid"]), float(tick["ask"]), min_dist):
                        current_stop_r = desired_stop_r
                    else:
                        stop_modify_rejections += 1
                        stop_modify_last_reason = "broker_stop_or_freeze_distance_rejected_trailing_modify"
            if target is not None and current_r >= target:
                final_utc = tick_time
                realized += remaining * target
                result_name = "dynamic_final_target_hit" if eff.policy_type == "momentum" else "trailing_cap_target_hit"
                return result_row(row, spec, result_name, realized, "tick_bid_ask", "target_hit_after_dynamic_management", candle, entry_time, exit_time=final_utc, extra=execution_extra(after, max_r, min_r, spread_at_entry, risk, stop_modify_attempts, stop_modify_rejections, stop_modify_last_reason, current_stop_r, cost_status, activation_utc=activation_utc, partial_utc=partial_utc))

        elif eff.policy_type == "time_stop":
            hours = eff.time_stop_hours or 4.0
            if tick_time >= entry_time + timedelta(hours=hours):
                time_stop_utc = tick_time
                realized += remaining * current_r
                return result_row(row, spec, "time_stop_exit", realized, "tick_bid_ask", f"time_stop_{hours:g}h", candle, entry_time, exit_time=time_stop_utc, extra=execution_extra(after, max_r, min_r, spread_at_entry, risk, stop_modify_attempts, stop_modify_rejections, stop_modify_last_reason, current_stop_r, cost_status))

    realized += remaining * last_r
    if eff.policy_type in {"trailing", "partial_trailing", "momentum"} and activation_utc is None:
        open_reason = "open_no_dynamic_activation_before_last_tick"
    return result_row(
        row,
        spec,
        "open_at_last_tick",
        realized,
        "tick_bid_ask",
        open_reason,
        candle,
        entry_time,
        exit_time=None,
        extra=execution_extra(after, max_r, min_r, spread_at_entry, risk, stop_modify_attempts, stop_modify_rejections, stop_modify_last_reason, current_stop_r, cost_status, activation_utc=activation_utc, partial_utc=partial_utc),
    )


def _first_true(mask: np.ndarray) -> int | None:
    hits = np.flatnonzero(mask)
    return int(hits[0]) if hits.size else None


def _ts_at(times: pd.Series, idx: int | None) -> datetime | None:
    if idx is None:
        return None
    value = times.iloc[idx]
    return value.to_pydatetime() if hasattr(value, "to_pydatetime") else parse_dt(value)


def simulate_tick_policy_fast(
    row: dict[str, Any],
    tick_frame: pd.DataFrame,
    spec: PolicySpec,
    entry_idx: int,
    entry_time: datetime,
) -> dict[str, Any]:
    side, candle, entry, stop, risk = geometry(row)
    if side is None or candle is None or entry is None or stop is None or risk is None:
        return result_row(row, spec, "not_simulatable_missing_geometry", None, "tick_bid_ask", "missing_geometry", candle, entry_time)
    eff = effective_policy(row, spec)
    cache = row.get("_tick_fast_cache")
    if not isinstance(cache, dict) or cache.get("entry_idx") != entry_idx or cache.get("entry_time") != iso(entry_time):
        after = tick_frame.loc[entry_idx:].reset_index(drop=True)
        if after.empty:
            return result_row(row, spec, "not_simulatable_empty_after_entry", None, "tick_bid_ask", "empty_after_entry", candle, entry_time)
        r = ((after["bid"].to_numpy(dtype=float) - entry) / risk) if side == "LONG" else ((entry - after["ask"].to_numpy(dtype=float)) / risk)
        max_r = float(np.max(r))
        min_r = float(np.min(r))
        spread_at_entry = float(after.iloc[0]["ask"] - after.iloc[0]["bid"])
        extra = execution_extra(after, max_r, min_r, spread_at_entry, risk, 0, 0, None, -1.0, "spread_in_bid_ask_path_commission_swap_not_row_convertible")
        extra.update(
            {
                "entry_source": "broker_actual_fill" if row.get("actual_entry_time_utc") else "counterfactual_tick_touch",
                "tick_coverage_status": "tick_window_present",
                "tick_first_utc": extra.get("price_source_first_utc"),
                "tick_last_utc": extra.get("price_source_last_utc"),
                "tick_rows": int(len(tick_frame)),
                "same_tick_multiple_event": False,
                "event_order_resolution": "ts_utc_ts_msc_stable_tick_order",
                "order_start_source": "actual_broker_fill_time" if row.get("actual_entry_time_utc") else "candidate_candle_time",
                "entry_price_basis": "actual_broker_fill_price" if row.get("actual_entry_price") is not None else "ask_touch_for_long_bid_touch_for_short",
            }
        )
        cache = {
            "entry_idx": entry_idx,
            "entry_time": iso(entry_time),
            "times": after["ts_utc"],
            "r": r,
            "max_r": max_r,
            "min_r": min_r,
            "last_r": float(r[-1]),
            "base_extra": extra,
        }
        row["_tick_fast_cache"] = cache
    times = cache["times"]
    r = cache["r"]
    max_r = cache["max_r"]
    min_r = cache["min_r"]
    last_r = cache["last_r"]
    extra = dict(cache["base_extra"])
    if len(r) == 0:
        return result_row(row, spec, "not_simulatable_empty_after_entry", None, "tick_bid_ask", "empty_after_entry", candle, entry_time)

    if eff.policy_type == "fixed_target":
        stop_idx = _first_true(r <= -1.0)
        target = eff.target_r or 1.5
        target_idx = _first_true(r >= target)
        if stop_idx is not None and (target_idx is None or stop_idx <= target_idx):
            return result_row(row, spec, "stop_hit", -1.0, "tick_bid_ask", "sl_before_fixed_target", candle, entry_time, exit_time=_ts_at(times, stop_idx), extra=extra)
        if target_idx is not None:
            return result_row(row, spec, "fixed_target_hit", target, "tick_bid_ask", "target_hit", candle, entry_time, exit_time=_ts_at(times, target_idx), extra=extra)
        return result_row(row, spec, "open_at_last_tick", last_r, "tick_bid_ask", "open_at_last_tick", candle, entry_time, extra=extra)

    if eff.policy_type == "time_stop":
        hours = eff.time_stop_hours or 4.0
        stop_idx = _first_true(r <= -1.0)
        cutoff = pd.Timestamp(entry_time + timedelta(hours=hours))
        time_idx = _first_true((times >= cutoff).to_numpy())
        if stop_idx is not None and (time_idx is None or stop_idx <= time_idx):
            return result_row(row, spec, "stop_hit", -1.0, "tick_bid_ask", "sl_before_time_stop", candle, entry_time, exit_time=_ts_at(times, stop_idx), extra=extra)
        if time_idx is not None:
            return result_row(row, spec, "time_stop_exit", float(r[time_idx]), "tick_bid_ask", f"time_stop_{hours:g}h", candle, entry_time, exit_time=_ts_at(times, time_idx), extra=extra)
        return result_row(row, spec, "open_at_last_tick", last_r, "tick_bid_ask", "open_before_time_stop", candle, entry_time, extra=extra)

    trigger = eff.trigger_r or 1.0
    trigger_idx = _first_true(r >= trigger)
    stop_scope = r if trigger_idx is None else r[: trigger_idx + 1]
    stop_before_trigger_idx = _first_true(stop_scope <= -1.0)
    if trigger_idx is None:
        if stop_before_trigger_idx is not None:
            return result_row(row, spec, "stop_hit", -1.0, "tick_bid_ask", "sl_before_dynamic_trigger", candle, entry_time, exit_time=_ts_at(times, stop_before_trigger_idx), extra=extra)
        return result_row(row, spec, "open_at_last_tick", last_r, "tick_bid_ask", "open_no_dynamic_activation_before_last_tick", candle, entry_time, extra=extra)
    if stop_before_trigger_idx is not None and stop_before_trigger_idx <= trigger_idx:
        return result_row(row, spec, "stop_hit", -1.0, "tick_bid_ask", "sl_before_dynamic_trigger", candle, entry_time, exit_time=_ts_at(times, stop_before_trigger_idx), extra=extra)

    after_trigger = r[trigger_idx:]
    times_after_trigger = times.iloc[trigger_idx:].reset_index(drop=True)
    activation_utc = _ts_at(times, trigger_idx)

    if eff.policy_type == "be_target":
        target = eff.target_r or 1.5
        target_idx = _first_true(after_trigger >= target)
        be_idx = _first_true(after_trigger <= 0.0)
        extra.update({"stop_modify_attempts": 1, "final_stop_r": 0.0, "dynamic_activation_utc": iso(activation_utc)})
        if target_idx is not None and (be_idx is None or target_idx <= be_idx):
            return result_row(row, spec, "be_target_hit", target, "tick_bid_ask", "target_hit_after_be_trigger", candle, entry_time, exit_time=_ts_at(times_after_trigger, target_idx), extra=extra)
        if be_idx is not None:
            return result_row(row, spec, "stop_hit", 0.0, "tick_bid_ask", "be_stop_after_trigger", candle, entry_time, exit_time=_ts_at(times_after_trigger, be_idx), extra=extra)
        return result_row(row, spec, "open_at_last_tick", last_r, "tick_bid_ask", "open_after_be_trigger", candle, entry_time, extra=extra)

    if eff.policy_type == "partial_be":
        target = eff.target_r or 3.0
        target_idx = _first_true(after_trigger >= target)
        be_idx = _first_true(after_trigger <= 0.0)
        extra.update({"stop_modify_attempts": 1, "final_stop_r": 0.0, "dynamic_activation_utc": iso(activation_utc), "partial_close_utc": iso(activation_utc)})
        if target_idx is not None and (be_idx is None or target_idx <= be_idx):
            return result_row(row, spec, "partial_then_final_target", 0.5 * trigger + 0.5 * target, "tick_bid_ask", "partial_1r_final_target_hit", candle, entry_time, exit_time=_ts_at(times_after_trigger, target_idx), extra=extra)
        if be_idx is not None:
            return result_row(row, spec, "stop_hit", 0.5 * trigger, "tick_bid_ask", "partial_1r_then_be_stop", candle, entry_time, exit_time=_ts_at(times_after_trigger, be_idx), extra=extra)
        return result_row(row, spec, "open_at_last_tick", 0.5 * trigger + 0.5 * last_r, "tick_bid_ask", "partial_1r_then_open_at_last_tick", candle, entry_time, extra=extra)

    if eff.policy_type in {"momentum", "trailing", "partial_trailing"}:
        target = eff.target_r
        gap = eff.trail_gap_r or 0.5
        cummax = np.maximum.accumulate(after_trigger)
        floor = 0.0 if eff.policy_type == "partial_trailing" else -1.0
        stop_line = np.maximum(floor, cummax - gap)
        target_idx = _first_true(after_trigger >= target) if target is not None else None
        stop_idx = _first_true(after_trigger <= stop_line)
        updates = int(np.count_nonzero(np.diff(stop_line) > 1e-12)) + 1
        extra.update({"stop_modify_attempts": updates, "final_stop_r": float(stop_line[-1]), "dynamic_activation_utc": iso(activation_utc)})
        realized_prefix = 0.0
        remaining = 1.0
        if eff.policy_type == "partial_trailing":
            realized_prefix = eff.partial_fraction * trigger
            remaining = 1.0 - eff.partial_fraction
            extra["partial_close_utc"] = iso(activation_utc)
        if target_idx is not None and (stop_idx is None or target_idx <= stop_idx):
            result = "dynamic_final_target_hit" if eff.policy_type == "momentum" else "trailing_cap_target_hit"
            return result_row(row, spec, result, realized_prefix + remaining * float(target), "tick_bid_ask", "target_hit_after_dynamic_management", candle, entry_time, exit_time=_ts_at(times_after_trigger, target_idx), extra=extra)
        if stop_idx is not None:
            stop_r = float(stop_line[stop_idx])
            return result_row(row, spec, "stop_hit", realized_prefix + remaining * stop_r, "tick_bid_ask", f"dynamic_stop_r_{stop_r:.4f}_hit", candle, entry_time, exit_time=_ts_at(times_after_trigger, stop_idx), extra=extra)
        return result_row(row, spec, "open_at_last_tick", realized_prefix + remaining * last_r, "tick_bid_ask", "open_after_dynamic_activation", candle, entry_time, extra=extra)

    return result_row(row, spec, "not_computed_unknown_policy", None, "tick_bid_ask", "unknown_effective_policy", candle, entry_time, extra=extra)


def execution_extra(
    after: pd.DataFrame,
    max_r: float,
    min_r: float,
    spread_at_entry: float,
    risk: float,
    stop_modify_attempts: int,
    stop_modify_rejections: int,
    stop_modify_last_reason: str | None,
    final_stop_r: float,
    cost_status: str,
    *,
    activation_utc: datetime | None = None,
    partial_utc: datetime | None = None,
) -> dict[str, Any]:
    return {
        "price_source_first_utc": iso(after.iloc[0]["ts_utc"].to_pydatetime()) if not after.empty else None,
        "price_source_last_utc": iso(after.iloc[-1]["ts_utc"].to_pydatetime()) if not after.empty else None,
        "tick_rows_after_entry": int(len(after)),
        "mfe_r": None if max_r <= -10**8 else max_r,
        "mae_r": None if min_r >= 10**8 else min_r,
        "spread_at_entry": spread_at_entry,
        "spread_r_at_entry": spread_at_entry / risk if risk else None,
        "stop_modify_attempts": stop_modify_attempts,
        "stop_modify_rejections": stop_modify_rejections,
        "stop_modify_last_rejection_reason": stop_modify_last_reason,
        "final_stop_r": final_stop_r,
        "dynamic_activation_utc": iso(activation_utc),
        "partial_close_utc": iso(partial_utc),
        "cost_model_status": cost_status,
    }


def bar_r_range(side: str, entry: float, stop: float, bar: anatomy.Bar) -> tuple[float, float, float]:
    if side == "LONG":
        max_r = side_r(side, entry, stop, bar.high)
        min_r = side_r(side, entry, stop, bar.low)
        close_r = side_r(side, entry, stop, bar.close)
    else:
        max_r = side_r(side, entry, stop, bar.low)
        min_r = side_r(side, entry, stop, bar.high)
        close_r = side_r(side, entry, stop, bar.close)
    return max_r, min_r, close_r


def bar_entry_hit(side: str, entry: float, bar: anatomy.Bar) -> bool:
    if side == "LONG":
        return bar.low <= entry
    return bar.high >= entry


def simulate_m1_policy(row: dict[str, Any], bars: list[anatomy.Bar], spec: PolicySpec) -> dict[str, Any]:
    side, candle, entry, stop, risk = geometry(row)
    if spec.policy_type == "no_trade":
        return result_row(row, spec, "no_trade", 0.0, "m1_ohlc", "no_trade_baseline", candle, None)
    if spec.policy_type == "current_router" and row.get("selected_policy") not in {"partial_be_runner", "momentum_exhaustion", "trailing_runner"}:
        return result_row(
            row,
            spec,
            "not_computed_missing_selected_policy",
            None,
            "m1_ohlc",
            "current_selected_policy_absent_from_candidate_packet",
            candle,
            None,
            extra={
                "m1_fallback_reason": "tick_unavailable_but_policy_not_evaluated_missing_selected_policy",
                "m1_same_bar_ambiguity": False,
                "tick_coverage_status": "not_evaluated_missing_selected_policy",
            },
        )
    if side is None or candle is None or entry is None or stop is None or risk is None:
        return result_row(row, spec, "not_simulatable_missing_geometry", None, "m1_ohlc", "missing_geometry", candle, None)
    if not bars:
        return result_row(row, spec, "not_simulatable_no_m1_window", None, "m1_ohlc", "no_m1_window", candle, None)
    entry_index = next((idx for idx, bar in enumerate(bars) if bar_entry_hit(side, entry, bar)), None)
    if entry_index is None:
        return result_row(row, spec, "no_fill_no_entry_touch", 0.0, "m1_ohlc", "entry_not_touched_before_last_m1", candle, None, extra={"m1_rows": len(bars), "m1_same_bar_ambiguity": False})

    eff = effective_policy(row, spec)
    current_stop_r = -1.0
    remaining = 1.0
    realized = 0.0
    max_seen = -10**9
    min_seen = 10**9
    ambiguity = False
    activation_utc = None
    partial_utc = None
    entry_time = bars[entry_index].time_utc
    last_close_r = 0.0

    for bar in bars[entry_index:]:
        high_r, low_r, close_r = bar_r_range(side, entry, stop, bar)
        last_close_r = close_r
        max_seen = max(max_seen, high_r)
        min_seen = min(min_seen, low_r)

        if low_r <= current_stop_r and high_r >= (eff.trigger_r or eff.target_r or 10**9):
            ambiguity = True
        if low_r <= current_stop_r:
            realized += remaining * current_stop_r
            return result_row(row, spec, "stop_hit_conservative_m1", realized, "m1_ohlc", "m1_stop_before_favorable_when_ambiguous", candle, entry_time, exit_time=bar.time_utc, extra=m1_extra(bars, max_seen, min_seen, ambiguity, current_stop_r))

        if eff.policy_type == "fixed_target":
            target = eff.target_r or 1.5
            if high_r >= target:
                return result_row(row, spec, "fixed_target_hit_m1", target, "m1_ohlc", "target_hit_m1", candle, entry_time, exit_time=bar.time_utc, extra=m1_extra(bars, max_seen, min_seen, ambiguity, current_stop_r))

        elif eff.policy_type == "be_target":
            trigger = eff.trigger_r or 1.0
            target = eff.target_r or 1.5
            if high_r >= trigger and current_stop_r < 0:
                current_stop_r = 0.0
                activation_utc = activation_utc or bar.time_utc
                if low_r <= current_stop_r:
                    ambiguity = True
            if high_r >= target:
                return result_row(row, spec, "be_target_hit_m1", target, "m1_ohlc", "target_hit_after_be_trigger_m1", candle, entry_time, exit_time=bar.time_utc, extra=m1_extra(bars, max_seen, min_seen, ambiguity, current_stop_r, activation_utc=activation_utc))

        elif eff.policy_type == "partial_be":
            trigger = eff.trigger_r or 1.0
            target = eff.target_r or 3.0
            if partial_utc is None and high_r >= trigger:
                partial_utc = bar.time_utc
                realized += eff.partial_fraction * trigger
                remaining -= eff.partial_fraction
                current_stop_r = max(current_stop_r, 0.0)
                activation_utc = activation_utc or bar.time_utc
                if low_r <= current_stop_r:
                    ambiguity = True
            if partial_utc is not None and high_r >= target:
                realized += remaining * target
                return result_row(row, spec, "partial_then_final_target_m1", realized, "m1_ohlc", "partial_1r_final_target_hit_m1", candle, entry_time, exit_time=bar.time_utc, extra=m1_extra(bars, max_seen, min_seen, ambiguity, current_stop_r, activation_utc=activation_utc, partial_utc=partial_utc))

        elif eff.policy_type in {"momentum", "trailing", "partial_trailing"}:
            trigger = eff.trigger_r or 1.0
            target = eff.target_r
            gap = eff.trail_gap_r or 0.5
            if eff.policy_type == "partial_trailing" and partial_utc is None and high_r >= trigger:
                partial_utc = bar.time_utc
                realized += eff.partial_fraction * trigger
                remaining -= eff.partial_fraction
                current_stop_r = max(current_stop_r, 0.0)
            if high_r >= trigger:
                activation_utc = activation_utc or bar.time_utc
                current_stop_r = max(current_stop_r, high_r - gap)
                if low_r <= current_stop_r:
                    ambiguity = True
            if target is not None and high_r >= target:
                realized += remaining * target
                result = "dynamic_final_target_hit_m1" if eff.policy_type == "momentum" else "trailing_cap_target_hit_m1"
                return result_row(row, spec, result, realized, "m1_ohlc", "target_hit_after_dynamic_management_m1", candle, entry_time, exit_time=bar.time_utc, extra=m1_extra(bars, max_seen, min_seen, ambiguity, current_stop_r, activation_utc=activation_utc, partial_utc=partial_utc))

        elif eff.policy_type == "time_stop":
            hours = eff.time_stop_hours or 4.0
            if bar.time_utc >= entry_time + timedelta(hours=hours):
                realized += remaining * close_r
                return result_row(row, spec, "time_stop_exit_m1", realized, "m1_ohlc", f"time_stop_{hours:g}h_m1", candle, entry_time, exit_time=bar.time_utc, extra=m1_extra(bars, max_seen, min_seen, ambiguity, current_stop_r))

    realized += remaining * last_close_r
    return result_row(row, spec, "open_at_last_m1", realized, "m1_ohlc", "open_at_last_m1_close", candle, entry_time, extra=m1_extra(bars, max_seen, min_seen, ambiguity, current_stop_r, activation_utc=activation_utc, partial_utc=partial_utc))


def m1_extra(
    bars: list[anatomy.Bar],
    max_seen: float,
    min_seen: float,
    ambiguity: bool,
    final_stop_r: float,
    *,
    activation_utc: datetime | None = None,
    partial_utc: datetime | None = None,
) -> dict[str, Any]:
    return {
        "m1_rows": len(bars),
        "price_source_first_utc": iso(bars[0].time_utc) if bars else None,
        "price_source_last_utc": iso(bars[-1].time_utc) if bars else None,
        "mfe_r": None if max_seen <= -10**8 else max_seen,
        "mae_r": None if min_seen >= 10**8 else min_seen,
        "m1_same_bar_ambiguity": ambiguity,
        "same_bar_or_tick_ambiguity": ambiguity,
        "final_stop_r": final_stop_r,
        "dynamic_activation_utc": iso(activation_utc),
        "partial_close_utc": iso(partial_utc),
        "cost_model_status": "m1_ohlc_fallback_spread_not_tick_exact_commission_swap_not_row_convertible",
    }


def result_row(
    row: dict[str, Any],
    spec: PolicySpec,
    result: str,
    gross_r: float | None,
    source: str,
    proof: str,
    candle: datetime | None,
    entry_time: datetime | None,
    *,
    exit_time: datetime | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = {
        "schema_version": "vnext_weekend_execution_policy_tournament_v1",
        "candidate_id": row.get("candidate_id"),
        "trade_id": row.get("trade_id"),
        "symbol": row.get("symbol"),
        "broker_symbol": row.get("broker_symbol"),
        "side": row.get("side"),
        "session": row.get("route_session") or row.get("session"),
        "origin_family": row.get("origin_family"),
        "framework": row.get("framework"),
        "source_mode": row.get("source_mode"),
        "candle_time_utc": row.get("candle_time_utc"),
        "final_outcome": row.get("final_outcome"),
        "current_selected_policy": row.get("selected_policy"),
        "current_execution_policy_id": row.get("execution_policy_id"),
        "comparison_policy": spec.name,
        "effective_policy_type": effective_policy(row, spec).policy_type if spec.policy_type != "no_trade" else "no_trade",
        "policy_evidence_role": spec.evidence_role,
        "execution_result": result,
        "execution_proof": proof,
        "gross_r": gross_r,
        "gross_r_bidask": gross_r,
        "entry_slippage_r": row.get("entry_slippage_r"),
        "exit_slippage_r": None,
        "net_r": gross_r,
        "net_r_status": "gross_bidask_only_commission_swap_not_converted" if gross_r is not None else "unknown",
        "price_source": source,
        "entry_touch_utc": iso(entry_time),
        "exit_utc": iso(exit_time),
        "time_to_entry_seconds": (entry_time - candle).total_seconds() if candle and entry_time else None,
        "time_in_trade_seconds": (exit_time - entry_time).total_seconds() if entry_time and exit_time else None,
        "entry": row.get("repaired_entry"),
        "stop_loss": row.get("repaired_stop_loss"),
        "risk_distance": row.get("risk_distance"),
        "dynamic_trigger_price": row.get("dynamic_trigger_price"),
        "dynamic_final_target_price": row.get("dynamic_final_target_price"),
        "dynamic_pullback_r": row.get("dynamic_pullback_r"),
        "selected_cell_risk_pct": row.get("selected_cell_risk_pct"),
        "selected_cell_risk_cell_id": row.get("selected_cell_risk_cell_id"),
        "actual_entry_time_utc": row.get("actual_entry_time_utc"),
        "actual_entry_price": row.get("actual_entry_price"),
        "entry_source": row.get("actual_entry_source"),
        "broker_truth_status": row.get("broker_truth_status"),
        "manual_contamination_status": row.get("manual_contamination_status"),
        "policy_source": "runtime_selected_policy" if spec.name == "current_selected_policy" else "tournament_variant",
        "config_snapshot": {
            "primary_policy": "momentum_exhaustion",
            "exception_policy": "partial_be_runner",
        },
        "source_path": row.get("source_path"),
        "source_row_reference": f"{row.get('_ledger_source_path')}:{row.get('_ledger_source_line')}",
        "evidence_class": "tick_sequenced_executable_replay" if source == "tick_bid_ask" else "m1_conservative_fallback_with_ambiguity_flag",
    }
    out.update(extra or {})
    return out


def simulate_candidate(
    row: dict[str, Any],
    tick_cache: dict[str, pd.DataFrame | None],
    m1_cache: dict[str, list[anatomy.Bar]],
) -> list[dict[str, Any]]:
    ticks = frame_window_ticks(row, tick_cache)
    bars = [] if ticks is not None and not ticks.empty else frame_window_m1(row, m1_cache)
    rows: list[dict[str, Any]] = []
    for spec in POLICY_SPECS:
        if ticks is not None and not ticks.empty:
            rows.append(simulate_tick_policy(row, ticks, spec))
        else:
            rows.append(simulate_m1_policy(row, bars, spec))
    return rows


def quality_bucket(row: dict[str, Any], policy_rows: list[dict[str, Any]]) -> dict[str, Any]:
    spread_r = to_float(row.get("spread_r_at_candidate"))
    gate1_reason = str(row.get("gate1_denial_reason") or "")
    gate3_reason = str(row.get("gate3_denial_reason") or "")
    session = str(row.get("route_session") or row.get("session") or "")
    origin = str(row.get("origin_family") or "")
    side = str(row.get("side") or "")
    selected_policy = row.get("selected_policy")
    execution_policy_id = row.get("execution_policy_id")
    final_outcome = row.get("final_outcome")
    current = next((r for r in policy_rows if r.get("comparison_policy") == "current_selected_policy"), {})
    trailing = next((r for r in policy_rows if r.get("comparison_policy") == "trailing_1r_gap_0_5_cap_3r"), {})
    current_result = str(current.get("execution_result") or "")
    current_gross_r = current.get("gross_r")
    mfe_r = to_float(row.get("mfe_r"))
    mae_r = to_float(row.get("mae_r"))
    time_to_entry_seconds = to_float(row.get("time_to_entry_seconds"))
    time_to_1r_seconds = to_float(row.get("time_to_1r_seconds"))
    time_to_sl_seconds = to_float(row.get("time_to_sl_seconds"))
    time_to_mfe_seconds = to_float(row.get("time_to_mfe_seconds"))
    time_to_mae_seconds = to_float(row.get("time_to_mae_seconds"))
    m1_same_bar_ambiguous = bool(current.get("m1_same_bar_ambiguity") or row.get("same_bar_or_tick_ambiguity"))
    tradeable_rule = TRADEABLE_SESSION_ORIGIN_RULES.get((session, origin))
    reasons: list[str] = []
    proof_fields: dict[str, Any] = {
        "mfe_r": mfe_r,
        "mae_r": mae_r,
        "mfe_before_mae": (
            time_to_mfe_seconds is not None
            and time_to_mae_seconds is not None
            and time_to_mfe_seconds <= time_to_mae_seconds
        ),
        "mae_before_mfe": (
            time_to_mfe_seconds is not None
            and time_to_mae_seconds is not None
            and time_to_mae_seconds < time_to_mfe_seconds
        ),
        "time_to_entry_seconds": time_to_entry_seconds,
        "time_to_1r_seconds": time_to_1r_seconds,
        "time_to_sl_seconds": time_to_sl_seconds,
        "time_to_mfe_seconds": time_to_mfe_seconds,
        "time_to_mae_seconds": time_to_mae_seconds,
        "path_status": row.get("path_status"),
        "price_source": row.get("price_source"),
        "m1_same_bar_ambiguity": m1_same_bar_ambiguous,
        "current_policy_result": current_result,
    }
    if spread_r is not None and spread_r >= 0.30:
        reasons.append("spread_r_at_candidate_ge_0_30")
    elif spread_r is not None and spread_r >= 0.20:
        reasons.append("spread_r_at_candidate_ge_0_20")
    if "sl_too_tight" in gate1_reason or "sl_below_minimum_floor" in gate1_reason:
        reasons.append("gate1_stop_geometry_failed_current_repair_required")
    if final_outcome == "REJECTED_GATE3_CIRCUIT_BREAKER" or "spread_too_wide" in gate3_reason:
        reasons.append("gate3_spread_rejected_no_trade_by_current_broker_cost")
    if final_outcome == "DEFERRED_GTOS_VNEXT_PROP_RESET":
        reasons.append("historical_prop_deferral_requires_current_account_risk_reconstruction")
    if final_outcome == "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC":
        refusal_reasons = row.get("dynamic_refusal_reasons") or []
        if refusal_reasons:
            reasons.append("dynamic_router_refusal_requires_exact_selector_risk_bridge")
        else:
            reasons.append("dynamic_router_skip_without_refusal_packet_requires_bridge_proof")
    if not selected_policy or not execution_policy_id:
        reasons.append("missing_selected_policy_or_execution_policy_id")
    if session == "ny" and origin in {"structural_distance_extreme", "liquidity_sweep_reclaim"} and side == "SHORT":
        reasons.append("weekend_negative_ny_short_origin_slice")
    if session == "off_configured_session" and origin == "liquidity_sweep_reclaim" and side == "LONG":
        reasons.append("off_session_crypto_liquidity_sweep_long_negative_slice")
    if session == "moonshot_h20_21" and origin == "liquidity_sweep_reclaim" and side == "LONG":
        reasons.append("h20_21_liquidity_sweep_long_negative_slice")
    if not reasons:
        reasons.append("no_current_quality_exclusion_from_weekend_asof_fields")
    if any(reason.startswith("gate1_") or "repair" in reason or "bridge" in reason for reason in reasons):
        classification = "repair_before_execution"
    elif any(reason.startswith("spread_r_at_candidate_ge_0_30") or reason.startswith("gate3_") for reason in reasons):
        classification = "no_trade_by_evidence"
    elif any(
        reason
        in {
            "weekend_negative_ny_short_origin_slice",
            "off_session_crypto_liquidity_sweep_long_negative_slice",
            "h20_21_liquidity_sweep_long_negative_slice",
        }
        for reason in reasons
    ):
        classification = "avoid_now"
    elif "missing_selected_policy_or_execution_policy_id" in reasons:
        classification = "insufficient_current_proof"
    elif tradeable_rule and spread_r is not None and spread_r < 0.20 and selected_policy and execution_policy_id:
        classification = "tradeable_now"
        reasons.append(str(tradeable_rule["rule_id"]))
    else:
        classification = "insufficient_current_proof"
    return {
        "schema_version": "vnext_weekend_candidate_quality_selector_v1",
        "candidate_id": row.get("candidate_id"),
        "symbol": row.get("symbol"),
        "side": row.get("side"),
        "session": row.get("route_session") or row.get("session"),
        "origin_family": row.get("origin_family"),
        "source_mode": row.get("source_mode"),
        "final_outcome": final_outcome,
        "selected_policy": selected_policy,
        "execution_policy_id": execution_policy_id,
        "selected_cell_risk_cell_id": row.get("selected_cell_risk_cell_id"),
        "selected_cell_risk_pct": row.get("selected_cell_risk_pct"),
        "spread_r_at_candidate": spread_r,
        "risk_distance": row.get("risk_distance"),
        "broker_spec_snapshot": row.get("broker_spec_snapshot"),
        "gate1_denial_reason": row.get("gate1_denial_reason"),
        "gate3_denial_reason": row.get("gate3_denial_reason"),
        "current_policy_gross_r": current.get("gross_r"),
        "current_policy_execution_result": current_result,
        "real_trailing_gross_r": trailing.get("gross_r"),
        "tradeable_rule": tradeable_rule,
        "quality_classification": classification,
        "quality_reasons": reasons,
        **proof_fields,
        "source_path": row.get("source_path"),
        "source_row_reference": f"{row.get('_ledger_source_path')}:{row.get('_ledger_source_line')}",
    }


def hybrid_policy_rows(candidate: dict[str, Any], quality: dict[str, Any], policy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name = {row.get("comparison_policy"): row for row in policy_rows}
    eligible = quality.get("quality_classification") == "tradeable_now"
    out: list[dict[str, Any]] = []
    for hybrid_name, source_policy in HYBRID_POLICY_SPECS:
        if eligible and source_policy in by_name:
            row = dict(by_name[source_policy])
            row["comparison_policy"] = hybrid_name
            row["policy_evidence_role"] = "hybrid_quality_gate_projection"
            row["quality_gate_action"] = "trade"
            row["quality_gate_source_policy"] = source_policy
            row["quality_gate_reasons"] = quality.get("quality_reasons")
            out.append(row)
        else:
            spec = PolicySpec(hybrid_name, "no_trade", evidence_role="hybrid_quality_gate_projection")
            row = result_row(
                candidate,
                spec,
                "quality_gate_no_trade",
                0.0,
                "quality_gate",
                "candidate_failed_weekend_asof_quality_filter",
                parse_dt(candidate.get("candle_time_utc")),
                None,
                extra={
                    "quality_gate_action": "no_trade",
                    "quality_gate_source_policy": source_policy,
                    "quality_gate_reasons": quality.get("quality_reasons"),
                    "tick_coverage_status": "not_applicable_quality_gate_no_trade",
                    "cost_model_status": "not_applicable_quality_gate_no_trade",
                },
            )
            out.append(row)
    return out


def summarize(tournament_rows: list[dict[str, Any]], quality_rows: list[dict[str, Any]], candidate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    policy_summary: dict[str, dict[str, Any]] = {}
    policy_names = [spec.name for spec in POLICY_SPECS] + [name for name, _ in HYBRID_POLICY_SPECS]
    for policy_name in policy_names:
        rows = [r for r in tournament_rows if r.get("comparison_policy") == policy_name]
        known = [r for r in rows if r.get("gross_r") is not None]
        gross_sum = sum(float(r.get("gross_r") or 0.0) for r in known)
        tick_rows = [r for r in rows if r.get("price_source") == "tick_bid_ask"]
        m1_rows = [r for r in rows if r.get("price_source") == "m1_ohlc"]
        by_symbol = Counter(r.get("symbol") for r in known)
        symbol_r: defaultdict[str, float] = defaultdict(float)
        for r in known:
            symbol_r[str(r.get("symbol"))] += float(r.get("gross_r") or 0.0)
        abs_symbol_sum = sum(abs(v) for v in symbol_r.values()) or 1.0
        max_symbol_share = max((abs(v) for v in symbol_r.values()), default=0.0) / abs_symbol_sum
        policy_summary[policy_name] = {
            "rows": len(rows),
            "known_r_rows": len(known),
            "gross_r_sum": gross_sum,
            "gross_r_avg": gross_sum / len(known) if known else None,
            "tick_rows": len(tick_rows),
            "m1_rows": len(m1_rows),
            "m1_ambiguous_rows": sum(1 for r in m1_rows if r.get("m1_same_bar_ambiguity")),
            "stop_modify_rejections": sum(int(r.get("stop_modify_rejections") or 0) for r in rows),
            "no_fill_rows": sum(1 for r in rows if str(r.get("execution_result", "")).startswith("no_fill")),
            "open_rows": sum(1 for r in rows if str(r.get("execution_result", "")).startswith("open_at_last")),
            "result_counts": dict(Counter(r.get("execution_result") for r in rows)),
            "symbol_counts": dict(by_symbol),
            "max_abs_symbol_r_share": max_symbol_share,
        }
    current_sum = policy_summary["current_selected_policy"]["gross_r_sum"]
    trailing_names = [s.name for s in POLICY_SPECS if s.name.startswith("trailing_") or s.name.startswith("partial_then_trail")]
    best_trailing = max(trailing_names, key=lambda name: policy_summary[name]["gross_r_sum"])
    best_policy = max(policy_summary, key=lambda name: policy_summary[name]["gross_r_sum"])
    quality_counts = Counter(r.get("quality_classification") for r in quality_rows)
    quality_reason_counts: Counter[str] = Counter()
    for row in quality_rows:
        quality_reason_counts.update(row.get("quality_reasons") or [])
    quality_subset_summary: dict[str, dict[str, Any]] = {}
    for classification in sorted(quality_counts):
        rows = [r for r in quality_rows if r.get("quality_classification") == classification]
        known = [r for r in rows if r.get("current_policy_gross_r") is not None]
        quality_subset_summary[classification] = {
            "rows": len(rows),
            "known_current_policy_r_rows": len(known),
            "current_selected_policy_gross_r_sum": sum(float(r.get("current_policy_gross_r") or 0.0) for r in known),
            "session_origin_counts": dict(
                Counter(f"{r.get('session')}|{r.get('origin_family')}" for r in rows)
            ),
        }
    tradeable_rule_summary: dict[str, dict[str, Any]] = {}
    for rule_key, rule in TRADEABLE_SESSION_ORIGIN_RULES.items():
        rows = [
            r
            for r in quality_rows
            if (r.get("session"), r.get("origin_family")) == rule_key
        ]
        known = [r for r in rows if r.get("current_policy_gross_r") is not None]
        tradeable_rule_summary[str(rule["rule_id"])] = {
            **rule,
            "session": rule_key[0],
            "origin_family": rule_key[1],
            "candidate_rows": len(rows),
            "classified_tradeable_now_rows": sum(
                1 for r in rows if r.get("quality_classification") == "tradeable_now"
            ),
            "current_selected_policy_gross_r_sum_from_rows": sum(
                float(r.get("current_policy_gross_r") or 0.0) for r in known
            ),
            "known_current_policy_r_rows": len(known),
        }
    repair_decision = "do_not_promote_trailing_primary_from_weekend_only"
    best_trailing_summary = policy_summary[best_trailing]
    if (
        best_trailing_summary["gross_r_sum"] > 0
        and best_policy == best_trailing
        and best_trailing_summary["gross_r_sum"] > current_sum
        and best_trailing_summary["max_abs_symbol_r_share"] <= 0.45
        and best_trailing_summary["m1_ambiguous_rows"] <= max(5, int(best_trailing_summary["rows"] * 0.15))
    ):
        repair_decision = "shadow_route_trailing_variant_candidate_requires_forward_confirmation"
    return {
        "schema_version": "vnext_weekend_execution_policy_tournament_summary_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": anatomy.git_head(),
        "candidate_rows": len(candidate_rows),
        "policy_variant_count": policy_variant_count(),
        "tournament_rows": len(tournament_rows),
        "policy_summaries": policy_summary,
        "best_policy_by_gross_r": best_policy,
        "best_trailing_policy_by_gross_r": best_trailing,
        "current_selected_policy_gross_r_sum": current_sum,
        "best_trailing_gross_r_sum": best_trailing_summary["gross_r_sum"],
        "trailing_repair_decision": repair_decision,
        "quality_classification_counts": dict(quality_counts),
        "quality_reason_counts": dict(quality_reason_counts),
        "quality_subset_summary": quality_subset_summary,
        "tradeable_rule_summary": tradeable_rule_summary,
        "quality_selector_runtime_recommendation": (
            "allow_configured_positive_session_origin_rules_after_current_bridge_risk_spread_proof"
            if tradeable_rule_summary
            else "no_trade_until_new_positive_subset_proof"
        ),
        "candidate_outcome_counts": dict(Counter(r.get("final_outcome") for r in candidate_rows)),
        "price_source_counts": dict(Counter(r.get("price_source") for r in tournament_rows)),
        "outputs": {
            "tournament_ledger": str(TOURNAMENT_LEDGER),
            "tournament_summary": str(TOURNAMENT_SUMMARY),
            "candidate_quality_selector": str(QUALITY_LEDGER),
            "policy_repair_ledger": str(POLICY_REPAIR_LEDGER),
            "findings_report": str(TOURNAMENT_FINDINGS),
            "verification": str(TOURNAMENT_VERIFICATION),
        },
    }


def repair_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    current = summary["policy_summaries"]["current_selected_policy"]
    best_trailing = summary["best_trailing_policy_by_gross_r"]
    best = summary["policy_summaries"][best_trailing]
    return [
        {
            "repair_item": "trailing_runner_proxy_replaced_by_executable_tournament",
            "status": "implemented",
            "proof": "real trailing variants are replayed tick-by-tick with bid/ask fills, stop movement, broker stop/freeze checks, M1 ambiguity flags, and no MFE-minus-gap proxy authority",
            "candidate_rows": summary["candidate_rows"],
            "policy_rows": summary["tournament_rows"],
        },
        {
            "repair_item": "production_policy_mismatch_partial_dominance",
            "status": "classified",
            "proof": "current_selected_policy is computed from row selected_policy; weekend partial dominance is expected when router selected partial_be_runner for most rows, not evidence that momentum primary executed globally",
            "current_selected_policy_gross_r_sum": current["gross_r_sum"],
        },
        {
            "repair_item": "trailing_policy_promotion",
            "status": summary["trailing_repair_decision"],
            "proof": f"best real trailing variant {best_trailing} gross_r={best['gross_r_sum']}, m1_ambiguous_rows={best['m1_ambiguous_rows']}, max_abs_symbol_r_share={best['max_abs_symbol_r_share']}",
        },
    ]


def build() -> dict[str, Any]:
    actual_fills = load_actual_fill_map()
    candidates = []
    for candidate in load_jsonl(ANATOMY_LEDGER):
        fill = actual_fills.get(str(candidate.get("candidate_id")))
        candidates.append({**candidate, **fill} if fill else candidate)
    tick_cache: dict[str, pd.DataFrame | None] = {}
    m1_cache: dict[str, list[anatomy.Bar]] = {}
    tournament_rows: list[dict[str, Any]] = []
    quality_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_policy_rows = simulate_candidate(candidate, tick_cache, m1_cache)
        quality = quality_bucket(candidate, candidate_policy_rows)
        candidate_policy_rows.extend(hybrid_policy_rows(candidate, quality, candidate_policy_rows))
        tournament_rows.extend(candidate_policy_rows)
        quality_rows.append(quality)
    summary = summarize(tournament_rows, quality_rows, candidates)
    repairs = repair_rows(summary)
    write_jsonl(TOURNAMENT_LEDGER, tournament_rows)
    write_jsonl(QUALITY_LEDGER, quality_rows)
    write_jsonl(POLICY_REPAIR_LEDGER, repairs)
    write_json(TOURNAMENT_SUMMARY, summary)
    TOURNAMENT_FINDINGS.write_text(render_findings(summary, repairs), encoding="utf-8")
    verification = verify(summary)
    write_json(TOURNAMENT_VERIFICATION, verification)
    return verification


def render_findings(summary: dict[str, Any], repairs: list[dict[str, Any]]) -> str:
    policy = summary["policy_summaries"]
    lines = [
        "# Weekend vNext Execution Policy Tournament Findings",
        "",
        f"Generated: {summary['generated_at_utc']}",
        f"HEAD: {summary['git_head']}",
        "",
        "## Denominator",
        "",
        f"- Candidate rows: {summary['candidate_rows']}",
        f"- Policy variants: {summary['policy_variant_count']}",
        f"- Tournament rows: {summary['tournament_rows']}",
        "",
        "## Policy Results",
        "",
        f"- Best policy by gross R: `{summary['best_policy_by_gross_r']}`.",
        f"- Current selected policy gross R: `{summary['current_selected_policy_gross_r_sum']}`.",
        f"- Best real trailing policy: `{summary['best_trailing_policy_by_gross_r']}` at `{summary['best_trailing_gross_r_sum']}`.",
        f"- Trailing decision: `{summary['trailing_repair_decision']}`.",
        f"- Quality-gated current selected gross R: `{policy['quality_gate_current_selected_policy']['gross_r_sum']}`.",
        f"- Quality-gated best trailing gross R: `{policy['quality_gate_trailing_1_5r_gap_0_5_cap_3r']['gross_r_sum']}`.",
        "",
        "## Quality Gate",
        "",
        f"- Quality classifications: `{json.dumps(summary['quality_classification_counts'], sort_keys=True)}`.",
        f"- Quality reasons: `{json.dumps(summary['quality_reason_counts'], sort_keys=True)}`.",
        f"- Tradeable rule summary: `{json.dumps(summary['tradeable_rule_summary'], sort_keys=True)}`.",
        f"- Runtime recommendation: `{summary['quality_selector_runtime_recommendation']}`.",
        "",
        "## Repair Decisions",
        "",
    ]
    for row in repairs:
        lines.append(f"- `{row['repair_item']}`: `{row['status']}` - {row['proof']}")
    lines.extend(
        [
            "",
            "## Production Boundary",
            "",
            "This tournament replaces the old trailing proxy as evidence. It does not perform broker actions and does not promote a live policy because every raw and quality-gated executable policy remains negative on the current weekend denominator.",
        ]
    )
    return "\n".join(lines) + "\n"


def verify(summary: dict[str, Any] | None = None) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    if summary is None:
        summary = json.loads(TOURNAMENT_SUMMARY.read_text(encoding="utf-8")) if TOURNAMENT_SUMMARY.exists() else {}
    forensic = json.loads(FORENSIC_SUMMARY.read_text(encoding="utf-8")) if FORENSIC_SUMMARY.exists() else {}
    expected_candidates = int(forensic.get("candidate_trade_record_count") or 0)
    route_descendant = route_artifact_only_descendant(summary.get("git_head"))
    if summary.get("git_head") != anatomy.git_head() and not route_descendant.get("allowed"):
        issues.append(
            {
                "code": "stale_tournament_git_head",
                "expected": anatomy.git_head(),
                "actual": summary.get("git_head"),
                "route_artifact_only_descendant": route_descendant,
            }
        )
    if summary.get("candidate_rows") != expected_candidates:
        issues.append({"code": "candidate_row_count_mismatch", "expected": expected_candidates, "actual": summary.get("candidate_rows")})
    expected_rows = (summary.get("candidate_rows") or 0) * policy_variant_count()
    if summary.get("tournament_rows") != expected_rows:
        issues.append({"code": "tournament_row_count_mismatch", "expected": expected_rows, "actual": summary.get("tournament_rows")})
    for path in (TOURNAMENT_LEDGER, TOURNAMENT_SUMMARY, QUALITY_LEDGER, POLICY_REPAIR_LEDGER, TOURNAMENT_FINDINGS):
        if not path.exists() or path.stat().st_size <= 0:
            issues.append({"code": "missing_or_empty_output", "path": str(path)})
    if not summary.get("policy_summaries", {}).get("trailing_1r_gap_0_5_cap_3r"):
        issues.append({"code": "missing_real_trailing_variant"})
    stale_proxy_hits = 0
    if TOURNAMENT_LEDGER.exists():
        with TOURNAMENT_LEDGER.open("r", encoding="utf-8") as handle:
            for line in handle:
                if "trailing_proxy" in line or "mfe_minus" in line:
                    stale_proxy_hits += 1
    if stale_proxy_hits:
        issues.append({"code": "stale_trailing_proxy_in_tournament", "rows": stale_proxy_hits})
    if summary.get("price_source_counts", {}).get("tick_bid_ask", 0) <= 0:
        issues.append({"code": "no_tick_bid_ask_rows"})
    required_quality_classes = {
        "tradeable_now",
        "avoid_now",
        "repair_before_execution",
        "insufficient_current_proof",
        "no_trade_by_evidence",
    }
    quality_classes = set((summary.get("quality_classification_counts") or {}).keys())
    if not quality_classes.issubset(required_quality_classes):
        issues.append(
            {
                "code": "unknown_quality_classification",
                "values": sorted(quality_classes - required_quality_classes),
            }
        )
    if summary.get("candidate_rows") and not (summary.get("tradeable_rule_summary") or {}):
        issues.append({"code": "missing_tradeable_rule_summary"})
    if QUALITY_LEDGER.exists():
        quality_rows_checked = 0
        missing_quality_fields = []
        required_quality_fields = {
            "candidate_id",
            "symbol",
            "side",
            "session",
            "origin_family",
            "quality_classification",
            "quality_reasons",
            "mfe_r",
            "mae_r",
            "time_to_entry_seconds",
            "spread_r_at_candidate",
            "price_source",
            "current_policy_execution_result",
        }
        with QUALITY_LEDGER.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                quality_rows_checked += 1
                row = json.loads(line)
                missing = sorted(field for field in required_quality_fields if field not in row)
                if missing:
                    missing_quality_fields.append({"line": line_no, "missing": missing})
                    if len(missing_quality_fields) >= 5:
                        break
        if quality_rows_checked != summary.get("candidate_rows"):
            issues.append(
                {
                    "code": "quality_row_count_mismatch",
                    "expected": summary.get("candidate_rows"),
                    "actual": quality_rows_checked,
                }
            )
        if missing_quality_fields:
            issues.append({"code": "quality_rows_missing_required_fields", "examples": missing_quality_fields})
    return {
        "schema_version": "vnext_weekend_execution_policy_tournament_verification_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": anatomy.git_head(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "route_artifact_only_descendant": route_descendant,
        "candidate_rows_checked": summary.get("candidate_rows"),
        "policy_variant_count": policy_variant_count(),
        "tournament_rows_checked": summary.get("tournament_rows"),
        "forensic_candidate_row_anchor": expected_candidates,
        "no_top_n_truncation_proof": "tournament_rows equals current candidate_rows times every executable policy variant",
    }


def check() -> int:
    verification = verify()
    print(json.dumps(verification, indent=2, sort_keys=True))
    return 0 if verification.get("ok") else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        return check()
    verification = build()
    print(json.dumps(verification, indent=2, sort_keys=True))
    return 0 if verification.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
