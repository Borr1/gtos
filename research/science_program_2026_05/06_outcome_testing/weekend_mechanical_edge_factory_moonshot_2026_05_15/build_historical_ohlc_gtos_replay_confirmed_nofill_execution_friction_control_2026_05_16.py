#!/usr/bin/env python3
"""Convert confirmed no-fill replay signatures into execution-friction controls."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

UNFILLED_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_TICK_M1_PROBE_RESULT_2026-05-16.json"
UNFILLED_ENTRY_PROBE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_ENTRY_WINDOW_PROBE_LEDGER_2026-05-16.jsonl"
UNFILLED_SIGNATURE_PROBE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_UNFILLED_SIGNATURE_PROBE_LEDGER_2026-05-16.jsonl"
UNFILLED_SPLIT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_UNFILLED_LEDGER_2026-05-16.jsonl"
COST_STATUS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_COST_FILL_STATUS_LEDGER_2026-05-16.jsonl"
CROSS_SIGNATURE_JOIN_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_SIGNATURE_JOIN_LEDGER_2026-05-16.jsonl"
CROSS_FAMILY_JOIN_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_FAMILY_JOIN_LEDGER_2026-05-16.jsonl"
NOFILL_CONTEXT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_RECOVERED_UNFILLED_CROSS_CONTROL_NOFILL_GEOMETRY_CONTEXT_LEDGER_2026-05-16.jsonl"
PATH_AMBIGUITY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_AMBIGUITY_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_CONTROL_RESULT_2026-05-16.json"
ENTRY_FRICTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_ENTRY_LEDGER_2026-05-16.jsonl"
FULL_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_SIGNATURE_LEDGER_2026-05-16.jsonl"
CONFIRMED_BRANCH_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_BRANCH_LEDGER_2026-05-16.jsonl"
FAMILY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_FAMILY_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS confirmed no-fill execution-friction control packet only. "
    "Rows convert tick/M1-confirmed no-fill signatures into fillability, closest-approach, "
    "spread-threshold, same-M15 ambiguity, and branch-control descriptors; no validation, "
    "R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior change is claimed."
)

CONFIRMED_NOFILL_STATUSES = {
    "TICK_CONFIRMS_NO_FILL_SIDE_TOUCH",
    "M1_CONFIRMS_NO_BID_BAR_TOUCH",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {"_parse_error": True, "_line_no": line_no}


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_manifest() -> tuple[list[dict[str, Any]], str]:
    paths = [
        UNFILLED_RESULT_PATH,
        UNFILLED_ENTRY_PROBE_PATH,
        UNFILLED_SIGNATURE_PROBE_PATH,
        UNFILLED_SPLIT_PATH,
        COST_STATUS_PATH,
        CROSS_SIGNATURE_JOIN_PATH,
        CROSS_FAMILY_JOIN_PATH,
        NOFILL_CONTEXT_PATH,
        PATH_AMBIGUITY_PATH,
    ]
    rows = [
        {
            "path": str(path.relative_to(REPO)).replace("\\", "/"),
            "sha256": sha256_file(path) if path.exists() else "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
            "status": "HASHED" if path.exists() else "MISSING_FAIL_CLOSED",
        }
        for path in paths
    ]
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def family_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("route_candidate_id")),
            str(row.get("entry_variant")),
            str(row.get("target_stop_contract_id")),
        ]
    )


def symbol_side_key(row: dict[str, Any]) -> str:
    return f"{row.get('symbol')}|{row.get('side')}"


def round_or_none(value: float | None, digits: int = 9) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def ratio_or_none(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return round(numerator / denominator, 9)


def fill_thresholds(side: str, cost_rows: list[dict[str, Any]]) -> tuple[float | None, float | None]:
    values = [float(row["effective_entry_price"]) for row in cost_rows if row.get("effective_entry_price") is not None]
    if not values:
        return None, None
    if side.upper() == "SHORT":
        return min(values), max(values)
    return max(values), min(values)


def miss_distance(side: str, closest_price: float | None, threshold: float | None) -> float | None:
    if closest_price is None or threshold is None:
        return None
    if side.upper() == "SHORT":
        return max(0.0, threshold - closest_price)
    return max(0.0, closest_price - threshold)


def is_touch(side: str, source_price: float, threshold: float) -> bool:
    if side.upper() == "SHORT":
        return source_price >= threshold
    return source_price <= threshold


def closest_update(side: str, current: float | None, candidate: float) -> float:
    if current is None:
        return candidate
    if side.upper() == "SHORT":
        return max(current, candidate)
    return min(current, candidate)


def distance_bucket(
    confirmed: bool,
    probe_status: str,
    miss_to_zero: float | None,
    miss_to_easiest: float | None,
    first_spread_price_distance: float | None,
    max_spread_proxy_price_distance: float | None,
    rolling_median_range: float | None,
) -> str:
    if not confirmed:
        if "RECOVERED" in probe_status:
            return "NONCONFIRMED_RECOVERED_FILL_TOUCH"
        return "NONCONFIRMED_SOURCE_STATUS_NOT_CONFIRMING_NOFILL"
    if miss_to_zero is None:
        return "CONFIRMED_NOFILL_DISTANCE_UNAVAILABLE_FAIL_CLOSED"
    if miss_to_easiest is not None and miss_to_easiest <= 0:
        return "CONFIRMED_NOFILL_STATUS_CONFLICTS_WITH_EXISTING_COST_THRESHOLD"
    if first_spread_price_distance is not None and first_spread_price_distance > 0 and miss_to_zero <= first_spread_price_distance:
        return "CONFIRMED_NOFILL_NEAR_MISS_WITHIN_EXACT_FIRST_SPREAD"
    if (
        max_spread_proxy_price_distance is not None
        and max_spread_proxy_price_distance > 0
        and miss_to_zero <= max_spread_proxy_price_distance
    ):
        return "CONFIRMED_NOFILL_NEAR_MISS_WITHIN_EXISTING_SPREAD_PROXY_ENVELOPE"
    if rolling_median_range is not None and rolling_median_range > 0 and miss_to_zero <= rolling_median_range:
        return "CONFIRMED_NOFILL_MISS_WITHIN_ROLLING_MEDIAN_RANGE"
    return "CONFIRMED_NOFILL_MISS_BEYOND_ROLLING_MEDIAN_RANGE"


def branch_action(bucket: str, source_status: str) -> str:
    if bucket == "CONFIRMED_NOFILL_STATUS_CONFLICTS_WITH_EXISTING_COST_THRESHOLD":
        return "RECHECK_COST_THRESHOLD_AND_SOURCE_ALIGNMENT_NOW"
    if bucket == "CONFIRMED_NOFILL_NEAR_MISS_WITHIN_EXACT_FIRST_SPREAD":
        return "BUILD_ENTRY_OFFSET_AND_MARKET_PROXY_BRANCH_CONTROL_NOW"
    if bucket == "CONFIRMED_NOFILL_NEAR_MISS_WITHIN_EXISTING_SPREAD_PROXY_ENVELOPE":
        return "BUILD_SPREAD_ENVELOPE_FILLABILITY_BRANCH_CONTROL_NOW"
    if bucket == "CONFIRMED_NOFILL_MISS_WITHIN_ROLLING_MEDIAN_RANGE":
        return "BUILD_WIDER_RETEST_ZONE_OR_FILLABILITY_FILTER_BRANCH_NOW"
    if bucket == "CONFIRMED_NOFILL_MISS_BEYOND_ROLLING_MEDIAN_RANGE":
        return "BUILD_AVOID_OR_MARKET_ENTRY_REDESIGN_BRANCH_NOW"
    if bucket == "CONFIRMED_NOFILL_DISTANCE_UNAVAILABLE_FAIL_CLOSED":
        return "REPLAY_OR_PROXY_DISTANCE_SOURCE_NOW"
    if "RECOVERED" in bucket:
        return "KEEP_IN_RECOVERED_PATH_CONTROL_BRANCH"
    if source_status == "TICK_CONFIRMS_NO_FILL_SIDE_TOUCH":
        return "EXACT_TICK_CONFIRMED_NOFILL_DESCRIPTOR_ONLY"
    return "SOURCE_STATUS_NOT_CONFIRMED_NOFILL_DESCRIPTOR_ONLY"


def median_or_none(values: list[float]) -> float | None:
    return round(float(median(values)), 9) if values else None


def build_cost_summary(cost_rows: list[dict[str, Any]]) -> dict[str, Any]:
    exemplar = cost_rows[0]
    side = str(exemplar.get("side"))
    easiest, hardest = fill_thresholds(side, cost_rows)
    spread_distances = [
        float(row["spread_proxy_price_distance"])
        for row in cost_rows
        if row.get("spread_proxy_price_distance") is not None
    ]
    return {
        "entry_variant_id": exemplar.get("entry_variant_id"),
        "event_id": exemplar.get("event_id"),
        "route_candidate_id": exemplar.get("route_candidate_id"),
        "symbol": exemplar.get("symbol"),
        "side": side,
        "entry_variant": exemplar.get("entry_variant"),
        "source_time_utc": exemplar.get("source_time_utc"),
        "horizon_bars": exemplar.get("horizon_bars"),
        "entry_price_input_only": float(exemplar["entry_price_input_only"]),
        "rolling_median_range": float(exemplar["rolling_median_range"]) if exemplar.get("rolling_median_range") is not None else None,
        "cost_model_count": len(cost_rows),
        "cost_models": sorted({str(row.get("cost_model")) for row in cost_rows}),
        "cost_path_statuses": sorted({str(row.get("cost_path_status")) for row in cost_rows}),
        "fill_timing_statuses": sorted({str(row.get("fill_timing_status")) for row in cost_rows}),
        "easiest_existing_cost_fill_threshold": easiest,
        "hardest_existing_cost_fill_threshold": hardest,
        "max_spread_proxy_price_distance": max(spread_distances) if spread_distances else None,
        "median_spread_proxy_price_distance": median_or_none(spread_distances),
    }


def probe_entry_distances(
    cost: dict[str, Any],
    upstream_probe: dict[str, Any],
    mt5: Any | None,
    mt5_init_ok: bool,
    symbol_select_cache: dict[str, tuple[bool, Any]],
) -> dict[str, Any]:
    symbol = str(cost["symbol"])
    side = str(cost["side"])
    source_time = parse_utc(str(cost["source_time_utc"]))
    horizon_bars = int(cost.get("horizon_bars") or 0)
    window_start = source_time + timedelta(minutes=15)
    window_end = source_time + timedelta(minutes=15 * (horizon_bars + 1))
    zero_threshold = float(cost["entry_price_input_only"])
    easiest_threshold = cost.get("easiest_existing_cost_fill_threshold")
    closest_tick_price = None
    closest_m1_bid_bar_price = None
    first_tick_spread_price_distance = None
    tick_status = "MT5_NOT_INITIALIZED_FAIL_CLOSED"
    m1_status = "MT5_NOT_INITIALIZED_FAIL_CLOSED"
    tick_count = 0
    m1_count = 0
    tick_touches_zero = False
    tick_touches_easiest = False
    m1_touches_zero = False
    m1_touches_easiest = False
    first_tick_closest_utc = None
    first_m1_closest_utc = None
    errors: list[str] = []
    if mt5 is not None and mt5_init_ok:
        if symbol not in symbol_select_cache:
            symbol_select_cache[symbol] = (bool(mt5.symbol_select(symbol, True)), mt5.last_error())
        selected, select_error = symbol_select_cache[symbol]
        if not selected:
            tick_status = "MT5_SYMBOL_SELECT_FAILED_FAIL_CLOSED"
            m1_status = "MT5_SYMBOL_SELECT_FAILED_FAIL_CLOSED"
            errors.append(f"symbol_select:{select_error}")
        else:
            ticks = mt5.copy_ticks_range(symbol, window_start, window_end, mt5.COPY_TICKS_ALL)
            if ticks is None:
                tick_status = "MT5_COPY_TICKS_RETURNED_NONE_FAIL_CLOSED"
                errors.append(f"ticks:{mt5.last_error()}")
            else:
                tick_count = len(ticks)
                tick_status = "MT5_NO_TICKS_IN_PROBE_WINDOW_FAIL_CLOSED" if tick_count == 0 else "EXACT_MT5_TICKS_AVAILABLE"
                for tick in ticks:
                    bid = float(tick["bid"])
                    ask = float(tick["ask"])
                    if bid <= 0 or ask <= 0 or ask < bid:
                        continue
                    tick_dt = datetime.fromtimestamp(int(tick["time_msc"]) / 1000.0, tz=timezone.utc)
                    if first_tick_spread_price_distance is None:
                        first_tick_spread_price_distance = ask - bid
                    source_price = bid if side.upper() == "SHORT" else ask
                    before = closest_tick_price
                    closest_tick_price = closest_update(side, closest_tick_price, source_price)
                    if closest_tick_price != before:
                        first_tick_closest_utc = iso_utc(tick_dt)
                    tick_touches_zero = tick_touches_zero or is_touch(side, source_price, zero_threshold)
                    if easiest_threshold is not None:
                        tick_touches_easiest = tick_touches_easiest or is_touch(side, source_price, float(easiest_threshold))
            rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, window_start, window_end)
            if rates is None:
                m1_status = "MT5_COPY_RATES_M1_RETURNED_NONE_FAIL_CLOSED"
                errors.append(f"m1:{mt5.last_error()}")
            else:
                m1_count = len(rates)
                m1_status = "MT5_NO_M1_BARS_IN_PROBE_WINDOW_FAIL_CLOSED" if m1_count == 0 else "MT5_M1_BARS_AVAILABLE"
                for rate in rates:
                    source_price = float(rate["high"]) if side.upper() == "SHORT" else float(rate["low"])
                    rate_dt = datetime.fromtimestamp(int(rate["time"]), tz=timezone.utc)
                    before = closest_m1_bid_bar_price
                    closest_m1_bid_bar_price = closest_update(side, closest_m1_bid_bar_price, source_price)
                    if closest_m1_bid_bar_price != before:
                        first_m1_closest_utc = iso_utc(rate_dt)
                    m1_touches_zero = m1_touches_zero or is_touch(side, source_price, zero_threshold)
                    if easiest_threshold is not None:
                        m1_touches_easiest = m1_touches_easiest or is_touch(side, source_price, float(easiest_threshold))

    authoritative_source = "DISTANCE_SOURCE_UNAVAILABLE_FAIL_CLOSED"
    authoritative_price = None
    if tick_status == "EXACT_MT5_TICKS_AVAILABLE":
        authoritative_source = "EXACT_TICK_FILL_SIDE_PRICE"
        authoritative_price = closest_tick_price
    elif m1_status == "MT5_M1_BARS_AVAILABLE":
        authoritative_source = "M1_BID_BAR_PROXY_PRICE"
        authoritative_price = closest_m1_bid_bar_price

    miss_to_zero = miss_distance(side, authoritative_price, zero_threshold)
    miss_to_easiest = miss_distance(side, authoritative_price, float(easiest_threshold) if easiest_threshold is not None else None)
    rolling_range = cost.get("rolling_median_range")
    max_proxy_distance = cost.get("max_spread_proxy_price_distance")
    status_mismatch = (
        upstream_probe.get("tick_source_status") != tick_status
        or upstream_probe.get("m1_source_status") != m1_status
    )
    return {
        **cost,
        "probe_window_start_utc": iso_utc(window_start),
        "probe_window_end_utc": iso_utc(window_end),
        "recomputed_tick_source_status": tick_status,
        "recomputed_m1_source_status": m1_status,
        "upstream_tick_source_status": upstream_probe.get("tick_source_status"),
        "upstream_m1_source_status": upstream_probe.get("m1_source_status"),
        "upstream_unfilled_probe_status": upstream_probe.get("unfilled_probe_status"),
        "source_status_mismatch_vs_upstream": status_mismatch,
        "ticks_returned_recomputed": tick_count,
        "m1_bars_returned_recomputed": m1_count,
        "authoritative_distance_source": authoritative_source,
        "closest_tick_fill_side_price": round_or_none(closest_tick_price),
        "closest_m1_bid_bar_price": round_or_none(closest_m1_bid_bar_price),
        "authoritative_closest_fill_side_price": round_or_none(authoritative_price),
        "first_tick_closest_utc": first_tick_closest_utc,
        "first_m1_closest_utc": first_m1_closest_utc,
        "first_tick_spread_price_distance": round_or_none(first_tick_spread_price_distance),
        "tick_touches_zero_entry": tick_touches_zero,
        "tick_touches_easiest_cost_threshold": tick_touches_easiest,
        "m1_touches_zero_entry": m1_touches_zero,
        "m1_touches_easiest_cost_threshold": m1_touches_easiest,
        "miss_distance_to_zero_entry_price": round_or_none(miss_to_zero),
        "miss_distance_to_easiest_existing_cost_threshold": round_or_none(miss_to_easiest),
        "miss_distance_to_zero_over_rolling_median_range": ratio_or_none(miss_to_zero, rolling_range),
        "miss_distance_to_zero_over_first_tick_spread": ratio_or_none(miss_to_zero, first_tick_spread_price_distance),
        "miss_distance_to_zero_over_max_spread_proxy": ratio_or_none(miss_to_zero, max_proxy_distance),
        "probe_recompute_errors": errors,
    }


def update_manifest(outputs: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    existing = [row for row in manifest.get("outputs", []) if row.get("artifact") != RESULT_PATH.name]
    existing.append(
        {
            "artifact": RESULT_PATH.name,
            "category": "historical_ohlc_gtos_replay_confirmed_nofill_execution_friction_control",
            "generated_utc": generated_at,
            "counts": outputs["counts"],
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        }
    )
    manifest["outputs"] = existing
    manifest["last_updated_utc"] = generated_at
    OUTPUT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(outputs: dict[str, Any], generated_at: str) -> None:
    row = {
        "timestamp_utc": generated_at,
        "event_type": "route_artifact_built",
        "route": "historical_ohlc_gtos_replay_confirmed_nofill_execution_friction_control",
        "artifact": RESULT_PATH.name,
        "counts": outputs["counts"],
        "not_completion": True,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    manifest_rows, manifest_hash = source_manifest()
    upstream_result = read_json(UNFILLED_RESULT_PATH)
    entry_probe_rows = [row for row in read_jsonl(UNFILLED_ENTRY_PROBE_PATH) if not row.get("_parse_error")]
    signature_probe_rows = [row for row in read_jsonl(UNFILLED_SIGNATURE_PROBE_PATH) if not row.get("_parse_error")]
    split_rows = [row for row in read_jsonl(UNFILLED_SPLIT_PATH) if not row.get("_parse_error")]
    cost_rows = [row for row in read_jsonl(COST_STATUS_PATH) if not row.get("_parse_error")]
    cross_signature_rows = [row for row in read_jsonl(CROSS_SIGNATURE_JOIN_PATH) if not row.get("_parse_error")]
    cross_family_rows = [row for row in read_jsonl(CROSS_FAMILY_JOIN_PATH) if not row.get("_parse_error")]
    nofill_context_rows = [row for row in read_jsonl(NOFILL_CONTEXT_PATH) if not row.get("_parse_error")]
    ambiguity_rows = [row for row in read_jsonl(PATH_AMBIGUITY_PATH) if not row.get("_parse_error")]

    entry_probe_by_id = {row["entry_variant_id"]: row for row in entry_probe_rows}
    split_by_signature = {row["cost_sensitivity_signature_id"]: row for row in split_rows}
    cross_signature_by_id = {row["cost_sensitivity_signature_id"]: row for row in cross_signature_rows}
    cross_family_by_key = {row["family_key"]: row for row in cross_family_rows}

    costs_by_entry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in cost_rows:
        costs_by_entry[row["entry_variant_id"]].append(row)

    nofill_symbol_side_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in nofill_context_rows:
        nofill_symbol_side_counts[symbol_side_key(row)][str(row.get("cross_control_nofill_context_status"))] += 1

    ambiguity_by_family: dict[str, Counter[str]] = defaultdict(Counter)
    for row in ambiguity_rows:
        ambiguity_by_family[family_key(row)][str(row.get("ambiguity_status"))] += 1

    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on local terminal package
        mt5 = None
        mt5_init_ok = False
        terminal_summary = {"mt5_module_available": False, "mt5_initialize": False, "mt5_error": f"{type(exc).__name__}: {exc}"}
    else:
        mt5_init_ok = bool(mt5.initialize())
        terminal_info = mt5.terminal_info() if mt5_init_ok else None
        terminal_summary = {
            "mt5_module_available": True,
            "mt5_initialize": mt5_init_ok,
            "mt5_last_error": mt5.last_error(),
            "terminal_name": getattr(terminal_info, "name", None) if terminal_info is not None else None,
            "terminal_company": getattr(terminal_info, "company", None) if terminal_info is not None else None,
            "read_only_market_data_probe": True,
        }

    symbol_select_cache: dict[str, tuple[bool, Any]] = {}
    entry_friction_rows: list[dict[str, Any]] = []
    entry_friction_by_id: dict[str, dict[str, Any]] = {}
    unfilled_entry_ids = sorted({row["entry_variant_id"] for row in signature_probe_rows})
    try:
        for seq, entry_id in enumerate(unfilled_entry_ids, 1):
            if entry_id not in costs_by_entry:
                continue
            cost_summary = build_cost_summary(costs_by_entry[entry_id])
            upstream_probe = entry_probe_by_id.get(entry_id, {})
            friction = probe_entry_distances(cost_summary, upstream_probe, mt5, mt5_init_ok, symbol_select_cache)
            confirmed = friction["upstream_unfilled_probe_status"] in CONFIRMED_NOFILL_STATUSES
            bucket = distance_bucket(
                confirmed,
                str(friction["upstream_unfilled_probe_status"]),
                friction["miss_distance_to_zero_entry_price"],
                friction["miss_distance_to_easiest_existing_cost_threshold"],
                friction["first_tick_spread_price_distance"],
                friction["max_spread_proxy_price_distance"],
                friction["rolling_median_range"],
            )
            row = {
                "execution_friction_entry_id": f"OHLC-GTOS-CONFIRMED-NOFILL-FRICTION-ENTRY-{seq:05d}",
                **friction,
                "confirmed_nofill_entry": confirmed,
                "execution_friction_distance_bucket": bucket,
                "execution_friction_branch_action": branch_action(bucket, str(friction["upstream_unfilled_probe_status"])),
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_ENTRY",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
            entry_friction_rows.append(row)
            entry_friction_by_id[entry_id] = row
    finally:
        if mt5 is not None and mt5_init_ok:
            mt5.shutdown()

    full_signature_rows: list[dict[str, Any]] = []
    confirmed_branch_rows: list[dict[str, Any]] = []
    for seq, row in enumerate(signature_probe_rows, 1):
        entry = entry_friction_by_id.get(row["entry_variant_id"], {})
        split = split_by_signature.get(row["cost_sensitivity_signature_id"], {})
        cross_signature = cross_signature_by_id.get(row["cost_sensitivity_signature_id"], {})
        key = family_key(row)
        cross_family = cross_family_by_key.get(key, {})
        ss_key = symbol_side_key(row)
        confirmed = row["unfilled_probe_status"] in CONFIRMED_NOFILL_STATUSES
        bucket = distance_bucket(
            confirmed,
            str(row["unfilled_probe_status"]),
            entry.get("miss_distance_to_zero_entry_price"),
            entry.get("miss_distance_to_easiest_existing_cost_threshold"),
            entry.get("first_tick_spread_price_distance"),
            entry.get("max_spread_proxy_price_distance"),
            entry.get("rolling_median_range"),
        )
        action = branch_action(bucket, str(row["unfilled_probe_status"]))
        ambiguity_counter = ambiguity_by_family.get(key, Counter())
        base = {
            "execution_friction_signature_id": f"OHLC-GTOS-CONFIRMED-NOFILL-FRICTION-SIG-{seq:05d}",
            "cost_sensitivity_signature_id": row["cost_sensitivity_signature_id"],
            "entry_variant_id": row["entry_variant_id"],
            "event_id": row["event_id"],
            "route_candidate_id": row["route_candidate_id"],
            "symbol": row["symbol"],
            "side": row["side"],
            "entry_variant": row["entry_variant"],
            "target_stop_contract_id": row["target_stop_contract_id"],
            "target_multiple": row["target_multiple"],
            "stop_multiple": row["stop_multiple"],
            "family_key": key,
            "symbol_side_key": ss_key,
            "unfilled_probe_status": row["unfilled_probe_status"],
            "confirmed_nofill_signature": confirmed,
            "tick_source_status": row["tick_source_status"],
            "m1_source_status": row["m1_source_status"],
            "has_same_m15_ambiguity": bool(split.get("has_same_m15_ambiguity")),
            "same_m15_ambiguity_rows_for_family": sum(ambiguity_counter.values()),
            "same_m15_ambiguity_statuses_for_family": dict(sorted(ambiguity_counter.items())),
            "authoritative_distance_source": entry.get("authoritative_distance_source"),
            "miss_distance_to_zero_entry_price": entry.get("miss_distance_to_zero_entry_price"),
            "miss_distance_to_easiest_existing_cost_threshold": entry.get("miss_distance_to_easiest_existing_cost_threshold"),
            "miss_distance_to_zero_over_rolling_median_range": entry.get("miss_distance_to_zero_over_rolling_median_range"),
            "miss_distance_to_zero_over_first_tick_spread": entry.get("miss_distance_to_zero_over_first_tick_spread"),
            "miss_distance_to_zero_over_max_spread_proxy": entry.get("miss_distance_to_zero_over_max_spread_proxy"),
            "entry_distance_bucket": entry.get("execution_friction_distance_bucket"),
            "execution_friction_distance_bucket": bucket,
            "execution_friction_branch_action": action,
            "cost_path_statuses": entry.get("cost_path_statuses"),
            "fill_timing_statuses": entry.get("fill_timing_statuses"),
            "cross_control_join_status": cross_signature.get("cross_control_join_status"),
            "cross_control_family_status": cross_family.get("cross_control_family_status"),
            "family_exact_descriptor_delta_rows": cross_family.get("exact_descriptor_delta_rows", 0),
            "family_exact_unavailable_stress_rows": cross_family.get("exact_unavailable_stress_rows", 0),
            "symbol_side_nofill_context_status_counts": dict(sorted(nofill_symbol_side_counts.get(ss_key, Counter()).items())),
            "source_manifest_hash": manifest_hash,
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_SIGNATURE",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        full_signature_rows.append(base)
        if confirmed:
            confirmed_branch_rows.append(
                {
                    "execution_friction_branch_id": f"OHLC-GTOS-CONFIRMED-NOFILL-FRICTION-BRANCH-{len(confirmed_branch_rows) + 1:05d}",
                    **base,
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_BRANCH",
                }
            )

    family_counter: dict[str, Counter[str]] = defaultdict(Counter)
    family_examples: dict[str, dict[str, Any]] = {}
    family_distances: dict[str, list[float]] = defaultdict(list)
    for row in full_signature_rows:
        key = row["family_key"]
        family_examples.setdefault(key, row)
        family_counter[key][row["execution_friction_distance_bucket"]] += 1
        if row["confirmed_nofill_signature"] and row.get("miss_distance_to_zero_entry_price") is not None:
            family_distances[key].append(float(row["miss_distance_to_zero_entry_price"]))

    family_rows: list[dict[str, Any]] = []
    for seq, key in enumerate(sorted(family_counter), 1):
        example = family_examples[key]
        counter = family_counter[key]
        confirmed_count = sum(
            count for bucket, count in counter.items() if bucket.startswith("CONFIRMED_NOFILL_")
        )
        family_rows.append(
            {
                "execution_friction_family_id": f"OHLC-GTOS-CONFIRMED-NOFILL-FRICTION-FAMILY-{seq:05d}",
                "family_key": key,
                "route_candidate_id": example["route_candidate_id"],
                "symbol": example["symbol"],
                "side": example["side"],
                "entry_variant": example["entry_variant"],
                "target_stop_contract_id": example["target_stop_contract_id"],
                "target_multiple": example["target_multiple"],
                "stop_multiple": example["stop_multiple"],
                "signature_rows": sum(counter.values()),
                "confirmed_nofill_signature_rows": confirmed_count,
                "nonconfirmed_signature_rows": sum(counter.values()) - confirmed_count,
                "distance_bucket_counts": dict(sorted(counter.items())),
                "min_confirmed_miss_distance_to_zero_entry_price": min(family_distances[key]) if family_distances[key] else None,
                "median_confirmed_miss_distance_to_zero_entry_price": median_or_none(family_distances[key]),
                "max_confirmed_miss_distance_to_zero_entry_price": max(family_distances[key]) if family_distances[key] else None,
                "cross_control_family_status": example.get("cross_control_family_status"),
                "family_exact_descriptor_delta_rows": example.get("family_exact_descriptor_delta_rows"),
                "family_exact_unavailable_stress_rows": example.get("family_exact_unavailable_stress_rows"),
                "same_m15_ambiguity_rows_for_family": example.get("same_m15_ambiguity_rows_for_family"),
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_FAMILY",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    bucket_rows: list[dict[str, Any]] = []

    def add_bucket(axis: str, counter: Counter[Any]) -> None:
        for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
            bucket_rows.append(
                {
                    "bucket_axis": axis,
                    "bucket": "|".join(str(part) for part in bucket) if isinstance(bucket, tuple) else str(bucket),
                    "count": count,
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_BUCKET",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )

    add_bucket("entry_distance_bucket", Counter(row["execution_friction_distance_bucket"] for row in entry_friction_rows))
    add_bucket("signature_probe_status", Counter(row["unfilled_probe_status"] for row in full_signature_rows))
    add_bucket("signature_distance_bucket", Counter(row["execution_friction_distance_bucket"] for row in full_signature_rows))
    add_bucket("confirmed_branch_action", Counter(row["execution_friction_branch_action"] for row in confirmed_branch_rows))
    add_bucket("symbol__confirmed_distance_bucket", Counter((row["symbol"], row["execution_friction_distance_bucket"]) for row in confirmed_branch_rows))
    add_bucket("entry_variant__confirmed_distance_bucket", Counter((row["entry_variant"], row["execution_friction_distance_bucket"]) for row in confirmed_branch_rows))
    add_bucket("source__confirmed_distance_bucket", Counter((row["authoritative_distance_source"], row["execution_friction_distance_bucket"]) for row in confirmed_branch_rows))
    add_bucket("same_m15_ambiguity__confirmed_distance_bucket", Counter((row["has_same_m15_ambiguity"], row["execution_friction_distance_bucket"]) for row in confirmed_branch_rows))
    add_bucket("cross_family_status__confirmed_distance_bucket", Counter((row.get("cross_control_family_status"), row["execution_friction_distance_bucket"]) for row in confirmed_branch_rows))
    add_bucket("family_distance_bucket_mix", Counter(tuple(sorted(row["distance_bucket_counts"].items())) for row in family_rows))

    near_rows = [
        row for row in confirmed_branch_rows
        if row["execution_friction_distance_bucket"]
        in {
            "CONFIRMED_NOFILL_NEAR_MISS_WITHIN_EXACT_FIRST_SPREAD",
            "CONFIRMED_NOFILL_NEAR_MISS_WITHIN_EXISTING_SPREAD_PROXY_ENVELOPE",
        }
    ]
    far_rows = [
        row for row in confirmed_branch_rows
        if row["execution_friction_distance_bucket"] == "CONFIRMED_NOFILL_MISS_BEYOND_ROLLING_MEDIAN_RANGE"
    ]
    ambiguity_confirmed = [row for row in confirmed_branch_rows if row["has_same_m15_ambiguity"] or row["same_m15_ambiguity_rows_for_family"]]
    exact_overlap = [
        row for row in confirmed_branch_rows
        if row.get("family_exact_descriptor_delta_rows", 0) or row.get("family_exact_unavailable_stress_rows", 0)
    ]
    source_mismatch = [row for row in entry_friction_rows if row["source_status_mismatch_vs_upstream"]]
    question_rows = [
        {
            "question_id": "OHLC-GTOS-CONFIRMED-NOFILL-FRICTION-QUESTION-001",
            "question": "Which signatures are still confirmed no-fill after exact tick or M1 bid-bar reconstruction?",
            "row_count": len(confirmed_branch_rows),
            "next_same_resource_action": "use confirmed branch ledger as the full execution-friction denominator for avoid/fillability controls",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-CONFIRMED-NOFILL-FRICTION-QUESTION-002",
            "question": "Which confirmed no-fill signatures are near misses under source-derived spread envelopes?",
            "row_count": len(near_rows),
            "next_same_resource_action": "materialize entry-offset, market-entry, or spread-envelope branch controls on the near-miss ledger",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-CONFIRMED-NOFILL-FRICTION-QUESTION-003",
            "question": "Which confirmed no-fill signatures miss beyond the rolling median range and therefore behave like retest-limit non-opportunities?",
            "row_count": len(far_rows),
            "next_same_resource_action": "convert far-miss rows into avoid/retest-limit-redesign controls and compare against market-entry branches",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-CONFIRMED-NOFILL-FRICTION-QUESTION-004",
            "question": "Which confirmed no-fill signatures also carry same-M15 target/stop ambiguity context?",
            "row_count": len(ambiguity_confirmed),
            "next_same_resource_action": "join no-fill branch controls to same-M15 ambiguity controls before any target/stop interpretation",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-CONFIRMED-NOFILL-FRICTION-QUESTION-005",
            "question": "Which confirmed no-fill signatures overlap exact-spread delta or unavailable-stress families?",
            "row_count": len(exact_overlap),
            "next_same_resource_action": "split execution-friction branches by exact-spread family context and source availability",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-CONFIRMED-NOFILL-FRICTION-QUESTION-006",
            "question": "Did the fresh read-only MT5 recompute disagree with the upstream tick/M1 source-status ledger?",
            "row_count": len(source_mismatch),
            "next_same_resource_action": "if nonzero, inspect source-status mismatches before using distance descriptors downstream",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]

    counts = {
        "bucket_rows": len(bucket_rows),
        "confirmed_branch_rows": len(confirmed_branch_rows),
        "cost_status_input_rows": len(cost_rows),
        "cross_family_input_rows": len(cross_family_rows),
        "cross_signature_input_rows": len(cross_signature_rows),
        "entry_friction_rows": len(entry_friction_rows),
        "family_rows": len(family_rows),
        "full_signature_rows": len(full_signature_rows),
        "nofill_context_input_rows": len(nofill_context_rows),
        "path_ambiguity_input_rows": len(ambiguity_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(manifest_rows),
        "split_unfilled_input_rows": len(split_rows),
        "unfilled_entry_probe_input_rows": len(entry_probe_rows),
        "unique_unfilled_entry_input_rows": len(unfilled_entry_ids),
        "unfilled_signature_probe_input_rows": len(signature_probe_rows),
    }
    output = {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "historical_ohlc_gtos_replay_confirmed_nofill_execution_friction_control_v1",
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_CONFIRMED_NOFILL_EXECUTION_FRICTION_CONTROL_ONLY",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": "This confirmed no-fill execution-friction packet does not complete the 60-hour moonshot objective.",
        "counts": counts,
        "signature_probe_status_counts": dict(sorted(Counter(row["unfilled_probe_status"] for row in full_signature_rows).items())),
        "confirmed_distance_bucket_counts": dict(sorted(Counter(row["execution_friction_distance_bucket"] for row in confirmed_branch_rows).items())),
        "branch_action_counts": dict(sorted(Counter(row["execution_friction_branch_action"] for row in confirmed_branch_rows).items())),
        "entry_distance_bucket_counts": dict(sorted(Counter(row["execution_friction_distance_bucket"] for row in entry_friction_rows).items())),
        "authoritative_distance_source_counts": dict(sorted(Counter(row["authoritative_distance_source"] for row in entry_friction_rows).items())),
        "terminal_summary": terminal_summary,
        "upstream_unfilled_probe_counts": upstream_result.get("signature_probe_status_counts", {}),
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "next_same_resource_work": [
            "materialize near-miss entry-offset and market-entry branch controls from the full near-miss ledger",
            "convert far-miss retest-limit rows into avoid/retest-redesign controls and compare against market-proxy descriptors",
            "split confirmed no-fill branches by same-M15 ambiguity and exact-spread family context",
            "join execution-friction family rows into the cost/fill/path synthesis packet preserving all families",
        ],
    }

    write_jsonl(ENTRY_FRICTION_PATH, entry_friction_rows)
    write_jsonl(FULL_SIGNATURE_PATH, full_signature_rows)
    write_jsonl(CONFIRMED_BRANCH_PATH, confirmed_branch_rows)
    write_jsonl(FAMILY_PATH, family_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Confirmed No-Fill Execution-Friction Control",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                "This packet converts tick/M1-confirmed no-fill signatures into execution-friction and fillability branch-control descriptors while preserving the full unfilled signature denominator.",
                "",
                "## Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in counts.items()),
                "",
                "## Confirmed Distance Buckets",
                "",
                *(f"- `{key}`: `{value}`" for key, value in sorted(Counter(row["execution_friction_distance_bucket"] for row in confirmed_branch_rows).items())),
                "",
                "## Immediate Work",
                "",
                "- Materialize near-miss entry-offset and market-entry branch controls from the full near-miss ledger.",
                "- Convert far-miss retest-limit rows into avoid/retest-redesign controls and compare against market-proxy descriptors.",
                "- Split confirmed no-fill branches by same-M15 ambiguity and exact-spread family context.",
                "- Join execution-friction family rows into the cost/fill/path synthesis packet preserving all families.",
                "",
                "No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    update_manifest(output, generated_at)
    append_sprint_ledger(output, generated_at)
    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
