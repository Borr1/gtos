#!/usr/bin/env python3
"""Repair partial/source-recheck rows from the M1 spread-adjusted replay packet."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

SOURCE_ALIGNMENT_ENTRY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_ENTRY_LEDGER_2026-05-16.jsonl"
SOURCE_ALIGNMENT_COST_MODEL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_COST_MODEL_LEDGER_2026-05-16.jsonl"
SOURCE_ALIGNMENT_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_SIGNATURE_LEDGER_2026-05-16.jsonl"
M1_REPLAY_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_RESULT_2026-05-16.json"
M1_REPLAY_ENTRY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_ENTRY_LEDGER_2026-05-16.jsonl"
M1_REPLAY_COST_MODEL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_COST_MODEL_LEDGER_2026-05-16.jsonl"
M1_REPLAY_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_SIGNATURE_LEDGER_2026-05-16.jsonl"
TARGET_STOP_CONTRACT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_TARGET_STOP_CONTRACT_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_RESULT_2026-05-16.json"
ENTRY_REPAIR_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_ENTRY_LEDGER_2026-05-16.jsonl"
COST_MODEL_REPAIR_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_COST_MODEL_LEDGER_2026-05-16.jsonl"
SIGNATURE_SCOPE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_SIGNATURE_SCOPE_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_SUMMARY_2026-05-16.md"

REPAIR_SCOPE_STATUSES = {
    "PARTIAL_THRESHOLD_TOUCH_ROUTE_SPLIT_ONLY",
    "SOURCE_RECHECK_ROUTE_SPLIT_ONLY",
}

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS M1 spread partial/source-recheck repair packet only. Rows repair "
    "the two M1 replay route-split entries by tracing source-alignment cost-model/status "
    "rows and recomputing same-resource M1 bar threshold/path branches; no validation, "
    "R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior change is claimed."
)


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
        return []
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
        SOURCE_ALIGNMENT_ENTRY_PATH,
        SOURCE_ALIGNMENT_COST_MODEL_PATH,
        SOURCE_ALIGNMENT_SIGNATURE_PATH,
        M1_REPLAY_RESULT_PATH,
        M1_REPLAY_ENTRY_PATH,
        M1_REPLAY_COST_MODEL_PATH,
        M1_REPLAY_SIGNATURE_PATH,
        TARGET_STOP_CONTRACT_PATH,
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


def side_fill_touch(side: str, high: float, low: float, threshold: float) -> bool:
    if side.upper() == "SHORT":
        return high >= threshold
    return low <= threshold


def target_price(side: str, entry: float, rolling_range: float, multiple: float) -> float:
    return entry - rolling_range * multiple if side.upper() == "SHORT" else entry + rolling_range * multiple


def stop_price(side: str, entry: float, rolling_range: float, multiple: float) -> float:
    return entry + rolling_range * multiple if side.upper() == "SHORT" else entry - rolling_range * multiple


def target_touch(side: str, high: float, low: float, price: float) -> bool:
    if side.upper() == "SHORT":
        return low <= price
    return high >= price


def stop_touch(side: str, high: float, low: float, price: float) -> bool:
    if side.upper() == "SHORT":
        return high >= price
    return low <= price


def round_price(value: float | None) -> float | None:
    return round(value, 9) if value is not None else None


def model_sort_key(row: dict[str, Any]) -> tuple[int, str]:
    order = {
        "ZERO_COST_CONTROL": 0,
        "SYMBOL_MEDIAN_SPREAD_PROXY": 1,
        "SYMBOL_MAX_SPREAD_PROXY": 2,
        "STATIC_CONSERVATIVE_FALLBACK_PROXY": 3,
    }
    return (order.get(str(row.get("cost_model")), 99), str(row.get("cost_model")))


def cost_model_repair_status(
    replay_scope_status: str,
    cost_model: str,
    touch_found: bool,
    source_alignment_status: str,
) -> str:
    if cost_model == "ZERO_COST_CONTROL" and not touch_found:
        return "ZERO_COST_CONTROL_UNTOUCHED_REMAINS_NOFILL"
    if replay_scope_status == "PARTIAL_THRESHOLD_TOUCH_ROUTE_SPLIT_ONLY":
        if touch_found:
            return "PARTIAL_THRESHOLD_TOUCHED_COST_MODEL_REPLAYABLE"
        return "PARTIAL_THRESHOLD_UNTOUCHED_COST_MODEL_REMAINS_NOFILL"
    if replay_scope_status == "SOURCE_RECHECK_ROUTE_SPLIT_ONLY":
        if touch_found:
            return "SOURCE_RECHECK_M1_CONFIRMS_THRESHOLD_TOUCH_REPLAYABLE"
        return "SOURCE_RECHECK_COST_MODEL_NOT_TOUCHED_BY_M1_BARS_FAIL_CLOSED"
    return f"UNEXPECTED_REPAIR_SCOPE_{source_alignment_status}"


def cost_model_branch_action(status: str) -> str:
    if status == "PARTIAL_THRESHOLD_TOUCHED_COST_MODEL_REPLAYABLE":
        return "REPLAY_PARTIAL_TOUCHED_COST_MODEL_WITH_M1_TARGET_STOP_BRANCH"
    if status == "PARTIAL_THRESHOLD_UNTOUCHED_COST_MODEL_REMAINS_NOFILL":
        return "PRESERVE_PARTIAL_UNTOUCHED_COST_MODEL_AS_NOFILL_CONTROL"
    if status == "SOURCE_RECHECK_M1_CONFIRMS_THRESHOLD_TOUCH_REPLAYABLE":
        return "REPLAY_SOURCE_RECHECK_M1_CONFIRMED_COST_MODEL_WITH_TARGET_STOP_BRANCH"
    if status == "ZERO_COST_CONTROL_UNTOUCHED_REMAINS_NOFILL":
        return "PRESERVE_ZERO_COST_CONTROL_AS_ORIGINAL_ENTRY_NOFILL_CONTROL"
    return "FAIL_CLOSED_REPAIR_COST_MODEL_REVIEW_REQUIRED"


def entry_repair_status(replay_scope_status: str, nonzero_total: int, nonzero_touched: int, zero_touched: bool) -> str:
    if replay_scope_status == "PARTIAL_THRESHOLD_TOUCH_ROUTE_SPLIT_ONLY":
        if nonzero_touched and nonzero_touched < nonzero_total and not zero_touched:
            return "PARTIAL_REPAIR_REPLAY_TOUCHED_COST_MODELS_KEEP_UNTOUCHED_NOFILL"
        return "PARTIAL_REPAIR_PATTERN_CHANGED_REVIEW_REQUIRED"
    if replay_scope_status == "SOURCE_RECHECK_ROUTE_SPLIT_ONLY":
        if nonzero_touched == nonzero_total and not zero_touched:
            return "SOURCE_RECHECK_REPAIR_M1_CONFIRMS_ALL_NONZERO_THRESHOLDS_ZERO_UNTOUCHED"
        return "SOURCE_RECHECK_REPAIR_M1_PATTERN_CHANGED_REVIEW_REQUIRED"
    return "UNEXPECTED_REPAIR_ENTRY_SCOPE"


def entry_source_pattern(replay_scope_status: str, authoritative_source: str, nonzero_total: int, nonzero_touched: int) -> str:
    if replay_scope_status == "PARTIAL_THRESHOLD_TOUCH_ROUTE_SPLIT_ONLY":
        return f"PARTIAL_THRESHOLD_PATTERN_{nonzero_touched}_OF_{nonzero_total}_NONZERO_M1_PROXY"
    if replay_scope_status == "SOURCE_RECHECK_ROUTE_SPLIT_ONLY" and authoritative_source == "EXACT_TICK_FILL_SIDE_PRICE":
        return "EXACT_TICK_SOURCE_RECHECK_M1_BARS_RECOMPUTED"
    return f"SOURCE_PATTERN_{authoritative_source or 'UNKNOWN'}"


def replay_target_stop(
    side: str,
    bars: list[dict[str, Any]],
    fill_index: int | None,
    entry_price: float,
    rolling_range: float,
    target_multiple: float,
    stop_multiple: float,
) -> dict[str, Any]:
    if fill_index is None:
        return {
            "m1_repair_path_status": "M1_REPAIR_THRESHOLD_FILL_NOT_FOUND_NO_TARGET_STOP_REPLAY",
            "m1_first_touch_status": "NO_FILL_NO_TARGET_STOP_REPLAY",
        }
    target = target_price(side, entry_price, rolling_range, target_multiple)
    stop = stop_price(side, entry_price, rolling_range, stop_multiple)
    first_target_index = None
    first_stop_index = None
    fill_bar_target_touch = False
    fill_bar_stop_touch = False
    for index in range(fill_index, len(bars)):
        bar = bars[index]
        high = float(bar["high"])
        low = float(bar["low"])
        t_touch = target_touch(side, high, low, target)
        s_touch = stop_touch(side, high, low, stop)
        if index == fill_index:
            fill_bar_target_touch = t_touch
            fill_bar_stop_touch = s_touch
        if t_touch and first_target_index is None:
            first_target_index = index
        if s_touch and first_stop_index is None:
            first_stop_index = index
        if first_target_index is not None and first_stop_index is not None:
            break
    if first_target_index is None and first_stop_index is None:
        status = "NO_TARGET_OR_STOP_TOUCH_WITHIN_M1_REPAIR_HORIZON"
    elif first_target_index is not None and first_stop_index is not None and first_target_index == first_stop_index:
        if first_target_index == fill_index:
            status = "FILL_BAR_TARGET_AND_STOP_TOUCH_M1_REPAIR_ORDER_UNRESOLVED"
        else:
            status = "TARGET_AND_STOP_TOUCH_SAME_M1_BAR_M1_REPAIR_AMBIGUOUS"
    elif first_target_index is not None and (first_stop_index is None or first_target_index < first_stop_index):
        if first_target_index == fill_index:
            status = "FILL_BAR_TARGET_TOUCH_FIRST_OR_ONLY_M1_REPAIR_ORDER_UNRESOLVED"
        else:
            status = "TARGET_TOUCH_FIRST_OR_ONLY_M1_REPAIR"
    else:
        if first_stop_index == fill_index:
            status = "FILL_BAR_STOP_TOUCH_FIRST_OR_ONLY_M1_REPAIR_ORDER_UNRESOLVED"
        else:
            status = "STOP_TOUCH_FIRST_OR_ONLY_M1_REPAIR"
    return {
        "m1_repair_path_status": "M1_REPAIR_THRESHOLD_FILL_PATH_REPLAYED",
        "m1_first_touch_status": status,
        "target_price_m1_repair_proxy": round_price(target),
        "stop_price_m1_repair_proxy": round_price(stop),
        "first_target_touch_m1_utc": iso_utc(bars[first_target_index]["time"]) if first_target_index is not None else None,
        "first_stop_touch_m1_utc": iso_utc(bars[first_stop_index]["time"]) if first_stop_index is not None else None,
        "first_target_touch_m1_offset": first_target_index - fill_index if first_target_index is not None else None,
        "first_stop_touch_m1_offset": first_stop_index - fill_index if first_stop_index is not None else None,
        "fill_bar_target_touch": fill_bar_target_touch,
        "fill_bar_stop_touch": fill_bar_stop_touch,
    }


def add_bucket_rows(bucket_rows: list[dict[str, Any]], axis: str, counter: Counter[Any]) -> None:
    for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
        bucket_rows.append(
            {
                "bucket_axis": axis,
                "bucket": "|".join(str(part) for part in bucket) if isinstance(bucket, tuple) else str(bucket),
                "count": count,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_BUCKET",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )


def main() -> int:
    generated_at = now_utc()
    manifest_rows, manifest_hash = source_manifest()
    m1_replay_result = read_json(M1_REPLAY_RESULT_PATH)
    source_entries = [row for row in read_jsonl(SOURCE_ALIGNMENT_ENTRY_PATH) if not row.get("_parse_error")]
    source_cost_models = [row for row in read_jsonl(SOURCE_ALIGNMENT_COST_MODEL_PATH) if not row.get("_parse_error")]
    source_signatures = [row for row in read_jsonl(SOURCE_ALIGNMENT_SIGNATURE_PATH) if not row.get("_parse_error")]
    m1_entry_rows = [row for row in read_jsonl(M1_REPLAY_ENTRY_PATH) if not row.get("_parse_error")]
    m1_cost_rows = [row for row in read_jsonl(M1_REPLAY_COST_MODEL_PATH) if not row.get("_parse_error")]
    m1_signature_rows = [row for row in read_jsonl(M1_REPLAY_SIGNATURE_PATH) if not row.get("_parse_error")]
    target_stop_contracts = [row for row in read_jsonl(TARGET_STOP_CONTRACT_PATH) if not row.get("_parse_error")]

    target_stop_by_id = {row["target_stop_contract_id"]: row for row in target_stop_contracts}
    source_entry_by_id = {row["entry_variant_id"]: row for row in source_entries}
    source_cost_by_entry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_cost_models:
        source_cost_by_entry[row["entry_variant_id"]].append(row)
    source_signatures_by_entry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_signatures:
        source_signatures_by_entry[row["entry_variant_id"]].append(row)
    m1_cost_by_entry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in m1_cost_rows:
        m1_cost_by_entry[row["entry_variant_id"]].append(row)
    m1_signature_by_entry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in m1_signature_rows:
        m1_signature_by_entry[row["entry_variant_id"]].append(row)

    repair_m1_entries = [row for row in m1_entry_rows if row.get("replay_scope_status") in REPAIR_SCOPE_STATUSES]

    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:  # pragma: no cover - local terminal dependency
        mt5 = None
        mt5_init_ok = False
        terminal_summary = {
            "mt5_module_available": False,
            "mt5_initialize": False,
            "mt5_error": f"{type(exc).__name__}: {exc}",
        }
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

    bars_by_entry: dict[str, list[dict[str, Any]]] = {}
    m1_source_status_by_entry: dict[str, str] = {}
    m1_error_by_entry: dict[str, str | None] = {}
    symbol_select_cache: dict[str, tuple[bool, Any]] = {}
    try:
        for m1_entry in repair_m1_entries:
            source_entry = source_entry_by_id.get(m1_entry["entry_variant_id"], {})
            symbol = str(m1_entry["symbol"])
            start_value = source_entry.get("probe_window_start_utc")
            end_value = source_entry.get("probe_window_end_utc")
            bars: list[dict[str, Any]] = []
            status = "MT5_NOT_INITIALIZED_FAIL_CLOSED"
            error = None
            if start_value and end_value and mt5 is not None and mt5_init_ok:
                start = parse_utc(str(start_value))
                end = parse_utc(str(end_value))
                if symbol not in symbol_select_cache:
                    symbol_select_cache[symbol] = (bool(mt5.symbol_select(symbol, True)), mt5.last_error())
                selected, select_error = symbol_select_cache[symbol]
                if not selected:
                    status = "MT5_SYMBOL_SELECT_FAILED_FAIL_CLOSED"
                    error = str(select_error)
                else:
                    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, start, end)
                    if rates is None:
                        status = "MT5_COPY_RATES_M1_RETURNED_NONE_FAIL_CLOSED"
                        error = str(mt5.last_error())
                    else:
                        status = "MT5_NO_M1_BARS_IN_REPAIR_WINDOW_FAIL_CLOSED" if len(rates) == 0 else "MT5_M1_BARS_AVAILABLE"
                        for rate in rates:
                            bars.append(
                                {
                                    "time": datetime.fromtimestamp(int(rate["time"]), tz=timezone.utc),
                                    "open": float(rate["open"]),
                                    "high": float(rate["high"]),
                                    "low": float(rate["low"]),
                                    "close": float(rate["close"]),
                                }
                            )
            bars_by_entry[m1_entry["entry_variant_id"]] = bars
            m1_source_status_by_entry[m1_entry["entry_variant_id"]] = status
            m1_error_by_entry[m1_entry["entry_variant_id"]] = error
    finally:
        if mt5 is not None and mt5_init_ok:
            mt5.shutdown()

    cost_model_repair_rows: list[dict[str, Any]] = []
    cost_repair_by_entry_model: dict[tuple[str, str], dict[str, Any]] = {}
    for m1_entry in repair_m1_entries:
        entry_id = m1_entry["entry_variant_id"]
        source_entry = source_entry_by_id.get(entry_id, {})
        bars = bars_by_entry.get(entry_id, [])
        for cost in sorted(source_cost_by_entry.get(entry_id, []), key=model_sort_key):
            threshold = float(cost["effective_entry_price"]) if cost.get("effective_entry_price") is not None else None
            fill_index = None
            if threshold is not None:
                for index, bar in enumerate(bars):
                    if side_fill_touch(str(m1_entry["side"]), float(bar["high"]), float(bar["low"]), threshold):
                        fill_index = index
                        break
            touch_found = fill_index is not None
            status = cost_model_repair_status(
                str(m1_entry["replay_scope_status"]),
                str(cost.get("cost_model")),
                touch_found,
                str(source_entry.get("entry_alignment_status")),
            )
            fill_bar = bars[fill_index] if fill_index is not None else {}
            row = {
                "partial_source_recheck_cost_model_repair_id": f"OHLC-GTOS-M1-PARTIAL-SOURCE-REPAIR-COST-{len(cost_model_repair_rows) + 1:05d}",
                "entry_variant_id": entry_id,
                "event_id": m1_entry["event_id"],
                "route_candidate_id": m1_entry["route_candidate_id"],
                "route_session": m1_entry["route_session"],
                "symbol": m1_entry["symbol"],
                "side": m1_entry["side"],
                "entry_variant": m1_entry["entry_variant"],
                "replay_scope_status": m1_entry["replay_scope_status"],
                "entry_alignment_status": source_entry.get("entry_alignment_status"),
                "source_alignment_cost_model_id": cost.get("source_alignment_cost_model_id"),
                "cost_fill_id": cost.get("cost_fill_id"),
                "cost_model": cost.get("cost_model"),
                "cost_path_status": cost.get("cost_path_status"),
                "fill_timing_status": cost.get("fill_timing_status"),
                "source_alignment_cost_model_status": cost.get("cost_model_alignment_status"),
                "source_alignment_m1_touches_model_threshold": cost.get("m1_touches_model_threshold"),
                "source_alignment_authoritative_distance_source": cost.get("authoritative_distance_source"),
                "entry_price_input_only": cost.get("entry_price_input_only"),
                "effective_entry_price": cost.get("effective_entry_price"),
                "signed_threshold_shift_from_zero": cost.get("signed_threshold_shift_from_zero"),
                "spread_proxy_price_distance": cost.get("spread_proxy_price_distance"),
                "authoritative_closest_fill_side_price": cost.get("authoritative_closest_fill_side_price"),
                "m1_repair_source_status": m1_source_status_by_entry.get(entry_id),
                "m1_repair_source_error": m1_error_by_entry.get(entry_id),
                "m1_bars_returned": len(bars),
                "m1_repair_threshold_touch": touch_found,
                "m1_repair_fill_status": "M1_REPAIR_THRESHOLD_FILL_FOUND" if touch_found else "M1_REPAIR_THRESHOLD_NOT_TOUCHED",
                "m1_repair_fill_utc": iso_utc(fill_bar["time"]) if fill_index is not None else None,
                "m1_repair_fill_bar_offset": fill_index,
                "m1_repair_fill_bar_high": fill_bar.get("high"),
                "m1_repair_fill_bar_low": fill_bar.get("low"),
                "cost_model_repair_status": status,
                "cost_model_repair_branch_action": cost_model_branch_action(status),
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_COST_MODEL",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
            cost_model_repair_rows.append(row)
            cost_repair_by_entry_model[(entry_id, str(cost.get("cost_model")))] = row

    entry_repair_rows: list[dict[str, Any]] = []
    for seq, m1_entry in enumerate(repair_m1_entries, 1):
        entry_id = m1_entry["entry_variant_id"]
        source_entry = source_entry_by_id.get(entry_id, {})
        costs = [row for row in cost_model_repair_rows if row["entry_variant_id"] == entry_id]
        nonzero_costs = [row for row in costs if row["cost_model"] != "ZERO_COST_CONTROL"]
        nonzero_touched = [row for row in nonzero_costs if row["m1_repair_threshold_touch"]]
        zero_touched = any(row["m1_repair_threshold_touch"] for row in costs if row["cost_model"] == "ZERO_COST_CONTROL")
        repair_status = entry_repair_status(
            str(m1_entry["replay_scope_status"]),
            len(nonzero_costs),
            len(nonzero_touched),
            zero_touched,
        )
        fill_offsets = [row["m1_repair_fill_bar_offset"] for row in nonzero_touched if row["m1_repair_fill_bar_offset"] is not None]
        entry_repair_rows.append(
            {
                "partial_source_recheck_entry_repair_id": f"OHLC-GTOS-M1-PARTIAL-SOURCE-REPAIR-ENTRY-{seq:05d}",
                "entry_variant_id": entry_id,
                "event_id": m1_entry["event_id"],
                "route_candidate_id": m1_entry["route_candidate_id"],
                "route_session": m1_entry["route_session"],
                "symbol": m1_entry["symbol"],
                "side": m1_entry["side"],
                "entry_variant": m1_entry["entry_variant"],
                "source_time_utc": source_entry.get("source_time_utc"),
                "probe_window_start_utc": source_entry.get("probe_window_start_utc"),
                "probe_window_end_utc": source_entry.get("probe_window_end_utc"),
                "replay_scope_status": m1_entry["replay_scope_status"],
                "entry_alignment_status": source_entry.get("entry_alignment_status"),
                "source_alignment_authoritative_distance_source": source_entry.get("authoritative_distance_source"),
                "source_alignment_authoritative_closest_fill_side_price": source_entry.get("authoritative_closest_fill_side_price"),
                "entry_price_input_only": source_entry.get("entry_price_input_only"),
                "rolling_median_range": source_entry.get("rolling_median_range"),
                "m1_replay_entry_source_status": m1_entry.get("m1_source_status"),
                "m1_replay_entry_bars_returned": m1_entry.get("m1_bars_returned"),
                "m1_repair_source_status": m1_source_status_by_entry.get(entry_id),
                "m1_repair_source_error": m1_error_by_entry.get(entry_id),
                "m1_repair_bars_returned": len(bars_by_entry.get(entry_id, [])),
                "m1_replay_skipped_source_status_absent": m1_entry.get("m1_source_status") is None,
                "authoritative_source_not_m1_proxy": source_entry.get("authoritative_distance_source") != "M1_BID_BAR_PROXY_PRICE",
                "source_repair_pattern": entry_source_pattern(
                    str(m1_entry["replay_scope_status"]),
                    str(source_entry.get("authoritative_distance_source")),
                    len(nonzero_costs),
                    len(nonzero_touched),
                ),
                "cost_model_rows": len(costs),
                "nonzero_cost_model_rows": len(nonzero_costs),
                "nonzero_cost_models_touched_by_m1_repair": sorted(row["cost_model"] for row in nonzero_touched),
                "nonzero_cost_models_untouched_by_m1_repair": sorted(
                    row["cost_model"] for row in nonzero_costs if not row["m1_repair_threshold_touch"]
                ),
                "zero_cost_control_touched_by_m1_repair": zero_touched,
                "source_signature_rows": len(source_signatures_by_entry.get(entry_id, [])),
                "m1_replay_cost_rows_for_entry": len(m1_cost_by_entry.get(entry_id, [])),
                "m1_replay_signature_rows_for_entry": len(m1_signature_by_entry.get(entry_id, [])),
                "signature_scope_rows": len(source_signatures_by_entry.get(entry_id, [])) * len(costs),
                "replayed_signature_scope_rows": len(source_signatures_by_entry.get(entry_id, [])) * len(nonzero_touched),
                "entry_repair_status": repair_status,
                "min_m1_repair_fill_bar_offset": min(fill_offsets) if fill_offsets else None,
                "max_m1_repair_fill_bar_offset": max(fill_offsets) if fill_offsets else None,
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_ENTRY",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    signature_scope_rows: list[dict[str, Any]] = []
    for m1_entry in repair_m1_entries:
        entry_id = m1_entry["entry_variant_id"]
        source_entry = source_entry_by_id.get(entry_id, {})
        bars = bars_by_entry.get(entry_id, [])
        for signature in sorted(source_signatures_by_entry.get(entry_id, []), key=lambda row: str(row.get("target_stop_contract_id"))):
            contract = target_stop_by_id.get(signature["target_stop_contract_id"], {})
            for cost in sorted(source_cost_by_entry.get(entry_id, []), key=model_sort_key):
                cost_repair = cost_repair_by_entry_model[(entry_id, str(cost.get("cost_model")))]
                fill_index = cost_repair.get("m1_repair_fill_bar_offset")
                replayable = cost_repair["m1_repair_threshold_touch"] and cost_repair["cost_model"] != "ZERO_COST_CONTROL"
                if replayable:
                    replay = replay_target_stop(
                        str(signature["side"]),
                        bars,
                        int(fill_index) if fill_index is not None else None,
                        float(cost_repair["effective_entry_price"]),
                        float(source_entry.get("rolling_median_range") or 0.0),
                        float(contract.get("target_multiple_of_rolling_median_range") or signature.get("target_multiple") or 0.0),
                        float(contract.get("stop_multiple_of_rolling_median_range") or signature.get("stop_multiple") or 0.0),
                    )
                    signature_scope_status = "REPAIR_REPLAYED_M1_TARGET_STOP_SCOPE"
                elif cost_repair["cost_model"] == "ZERO_COST_CONTROL":
                    replay = {
                        "m1_repair_path_status": "ZERO_COST_CONTROL_UNTOUCHED_NO_TARGET_STOP_REPLAY",
                        "m1_first_touch_status": "NOFILL_SCOPE_ZERO_COST_CONTROL_UNTOUCHED",
                    }
                    signature_scope_status = "REPAIR_ZERO_COST_CONTROL_NOFILL_SCOPE"
                else:
                    replay = {
                        "m1_repair_path_status": "UNTOUCHED_COST_MODEL_NO_TARGET_STOP_REPLAY",
                        "m1_first_touch_status": "NOFILL_SCOPE_COST_MODEL_THRESHOLD_UNTOUCHED",
                    }
                    signature_scope_status = "REPAIR_UNTOUCHED_COST_MODEL_NOFILL_SCOPE"
                signature_scope_rows.append(
                    {
                        "partial_source_recheck_signature_scope_id": f"OHLC-GTOS-M1-PARTIAL-SOURCE-REPAIR-SIG-{len(signature_scope_rows) + 1:05d}",
                        "source_alignment_signature_id": signature.get("source_alignment_signature_id"),
                        "cost_sensitivity_signature_id": signature.get("cost_sensitivity_signature_id"),
                        "entry_variant_id": entry_id,
                        "event_id": signature.get("event_id"),
                        "route_candidate_id": signature.get("route_candidate_id"),
                        "route_session": signature.get("route_session"),
                        "symbol": signature.get("symbol"),
                        "side": signature.get("side"),
                        "entry_variant": signature.get("entry_variant"),
                        "target_stop_contract_id": signature.get("target_stop_contract_id"),
                        "target_multiple": signature.get("target_multiple"),
                        "stop_multiple": signature.get("stop_multiple"),
                        "family_key": signature.get("family_key"),
                        "replay_scope_status": m1_entry["replay_scope_status"],
                        "entry_alignment_status": source_entry.get("entry_alignment_status"),
                        "cost_model": cost_repair["cost_model"],
                        "cost_fill_id": cost_repair.get("cost_fill_id"),
                        "effective_entry_price": cost_repair.get("effective_entry_price"),
                        "cost_model_repair_status": cost_repair["cost_model_repair_status"],
                        "cost_model_repair_branch_action": cost_repair["cost_model_repair_branch_action"],
                        "signature_scope_status": signature_scope_status,
                        "m1_repair_fill_status": cost_repair["m1_repair_fill_status"],
                        "m1_repair_fill_utc": cost_repair["m1_repair_fill_utc"],
                        "m1_repair_fill_bar_offset": cost_repair["m1_repair_fill_bar_offset"],
                        "same_m15_ambiguity_rows_for_family": signature.get("same_m15_ambiguity_rows_for_family"),
                        "cross_control_family_status": signature.get("cross_control_family_status"),
                        "family_exact_descriptor_delta_rows": signature.get("family_exact_descriptor_delta_rows"),
                        "family_exact_unavailable_stress_rows": signature.get("family_exact_unavailable_stress_rows"),
                        **replay,
                        "source_manifest_hash": manifest_hash,
                        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_SIGNATURE_SCOPE",
                        "safe_flags": SAFE_FLAGS,
                        "claim_boundary": CLAIM_BOUNDARY,
                    }
                )

    bucket_rows: list[dict[str, Any]] = []
    add_bucket_rows(bucket_rows, "entry_replay_scope_status", Counter(row["replay_scope_status"] for row in entry_repair_rows))
    add_bucket_rows(bucket_rows, "entry_repair_status", Counter(row["entry_repair_status"] for row in entry_repair_rows))
    add_bucket_rows(bucket_rows, "entry_source_repair_pattern", Counter(row["source_repair_pattern"] for row in entry_repair_rows))
    add_bucket_rows(bucket_rows, "cost_model_repair_status", Counter(row["cost_model_repair_status"] for row in cost_model_repair_rows))
    add_bucket_rows(bucket_rows, "cost_model__repair_status", Counter((row["cost_model"], row["cost_model_repair_status"]) for row in cost_model_repair_rows))
    add_bucket_rows(bucket_rows, "cost_model__m1_repair_fill_status", Counter((row["cost_model"], row["m1_repair_fill_status"]) for row in cost_model_repair_rows))
    add_bucket_rows(bucket_rows, "signature_scope_status", Counter(row["signature_scope_status"] for row in signature_scope_rows))
    add_bucket_rows(bucket_rows, "signature_first_touch_status", Counter(row["m1_first_touch_status"] for row in signature_scope_rows))
    add_bucket_rows(bucket_rows, "replay_scope__signature_scope_status", Counter((row["replay_scope_status"], row["signature_scope_status"]) for row in signature_scope_rows))
    add_bucket_rows(bucket_rows, "cost_model__signature_first_touch_status", Counter((row["cost_model"], row["m1_first_touch_status"]) for row in signature_scope_rows))
    add_bucket_rows(bucket_rows, "symbol__entry_repair_status", Counter((row["symbol"], row["entry_repair_status"]) for row in entry_repair_rows))

    replayed_signature_scopes = [row for row in signature_scope_rows if row["signature_scope_status"] == "REPAIR_REPLAYED_M1_TARGET_STOP_SCOPE"]
    nofill_signature_scopes = [row for row in signature_scope_rows if row["signature_scope_status"] != "REPAIR_REPLAYED_M1_TARGET_STOP_SCOPE"]
    fill_bar_ambiguous_scopes = [row for row in replayed_signature_scopes if "FILL_BAR" in row["m1_first_touch_status"]]
    source_recheck_repaired = [
        row for row in entry_repair_rows
        if row["replay_scope_status"] == "SOURCE_RECHECK_ROUTE_SPLIT_ONLY"
        and row["entry_repair_status"] == "SOURCE_RECHECK_REPAIR_M1_CONFIRMS_ALL_NONZERO_THRESHOLDS_ZERO_UNTOUCHED"
    ]
    partial_repaired = [
        row for row in entry_repair_rows
        if row["replay_scope_status"] == "PARTIAL_THRESHOLD_TOUCH_ROUTE_SPLIT_ONLY"
        and row["entry_repair_status"] == "PARTIAL_REPAIR_REPLAY_TOUCHED_COST_MODELS_KEEP_UNTOUCHED_NOFILL"
    ]

    question_rows = [
        {
            "question_id": "OHLC-GTOS-M1-PARTIAL-SOURCE-REPAIR-QUESTION-001",
            "question": "How many M1 replay route-split entries were repaired with same-resource M1 bars?",
            "row_count": len(entry_repair_rows),
            "next_same_resource_action": "carry repaired entry statuses into cost/fill/path synthesis with explicit partial/source-recheck branch tags",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-M1-PARTIAL-SOURCE-REPAIR-QUESTION-002",
            "question": "Does the partial-threshold row become a concrete replay branch or remain fully blocked?",
            "row_count": len(partial_repaired),
            "next_same_resource_action": "replay only touched static fallback branches and preserve untouched median/max/zero branches as no-fill controls",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-M1-PARTIAL-SOURCE-REPAIR-QUESTION-003",
            "question": "Does the exact-tick source-recheck row also satisfy M1 bar spread-adjusted threshold repair?",
            "row_count": len(source_recheck_repaired),
            "next_same_resource_action": "include the source-recheck row as M1-confirmed spread-adjusted replay branch while retaining exact-tick source-class tag",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-M1-PARTIAL-SOURCE-REPAIR-QUESTION-004",
            "question": "How many signature/cost-model scopes are replayable versus preserved as no-fill controls?",
            "row_count": len(signature_scope_rows),
            "replayable_scope_rows": len(replayed_signature_scopes),
            "nofill_scope_rows": len(nofill_signature_scopes),
            "next_same_resource_action": "use signature scope ledger as the full denominator; do not collapse to repaired-only rows",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-M1-PARTIAL-SOURCE-REPAIR-QUESTION-005",
            "question": "How many replayable repaired signature scopes still have fill-bar M1 order ambiguity?",
            "row_count": len(fill_bar_ambiguous_scopes),
            "next_same_resource_action": "route fill-bar ambiguous repaired scopes into interval-bound or tick-order stress before descriptor claims",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]

    counts = {
        "bucket_rows": len(bucket_rows),
        "cost_model_repair_rows": len(cost_model_repair_rows),
        "entry_repair_rows": len(entry_repair_rows),
        "m1_replay_cost_model_rows_for_repair_entries": sum(len(m1_cost_by_entry.get(row["entry_variant_id"], [])) for row in entry_repair_rows),
        "m1_replay_entry_input_rows": len(m1_entry_rows),
        "m1_replay_signature_rows_for_repair_entries": sum(len(m1_signature_by_entry.get(row["entry_variant_id"], [])) for row in entry_repair_rows),
        "question_rows": len(question_rows),
        "replayed_signature_scope_rows": len(replayed_signature_scopes),
        "signature_scope_rows": len(signature_scope_rows),
        "source_alignment_cost_model_input_rows": len(source_cost_models),
        "source_alignment_entry_input_rows": len(source_entries),
        "source_alignment_signature_input_rows": len(source_signatures),
        "source_manifest_rows": len(manifest_rows),
        "target_stop_contract_input_rows": len(target_stop_contracts),
    }
    output = {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "historical_ohlc_gtos_replay_m1_spread_partial_source_recheck_repair_v1",
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_PARTIAL_SOURCE_RECHECK_REPAIR_ONLY",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": "This partial/source-recheck repair packet does not complete the 60-hour moonshot objective.",
        "counts": counts,
        "entry_repair_status_counts": dict(sorted(Counter(row["entry_repair_status"] for row in entry_repair_rows).items())),
        "cost_model_repair_status_counts": dict(sorted(Counter(row["cost_model_repair_status"] for row in cost_model_repair_rows).items())),
        "signature_scope_status_counts": dict(sorted(Counter(row["signature_scope_status"] for row in signature_scope_rows).items())),
        "signature_first_touch_status_counts": dict(sorted(Counter(row["m1_first_touch_status"] for row in signature_scope_rows).items())),
        "upstream_m1_replay_counts": m1_replay_result.get("counts", {}),
        "terminal_summary": terminal_summary,
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "next_same_resource_work": [
            "feed repaired partial/static and source-recheck/M1-confirmed branches into cost/fill/path family synthesis",
            "keep untouched median/max/zero partial scopes as explicit no-fill controls instead of dropping them",
            "route fill-bar ambiguous repaired scopes into interval-bound or tick-order stress before descriptor claims",
            "compare repaired branches against near-miss market-entry and far-miss redesign packets on the full shared family denominator",
        ],
    }

    write_jsonl(ENTRY_REPAIR_PATH, entry_repair_rows)
    write_jsonl(COST_MODEL_REPAIR_PATH, cost_model_repair_rows)
    write_jsonl(SIGNATURE_SCOPE_PATH, signature_scope_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay M1 Spread Partial/Source-Recheck Repair",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                "This packet repairs the two M1 replay route-split rows from the spread-adjusted fill replay packet using the source-alignment cost-model/signature ledgers plus read-only MT5 M1 bars.",
                "",
                "## Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in counts.items()),
                "",
                "## Entry Repair Status",
                "",
                *(f"- `{key}`: `{value}`" for key, value in sorted(Counter(row["entry_repair_status"] for row in entry_repair_rows).items())),
                "",
                "## Cost-Model Repair Status",
                "",
                *(f"- `{key}`: `{value}`" for key, value in sorted(Counter(row["cost_model_repair_status"] for row in cost_model_repair_rows).items())),
                "",
                "## Immediate Work",
                "",
                "- Feed repaired partial/static and source-recheck/M1-confirmed branches into cost/fill/path family synthesis.",
                "- Preserve untouched partial median/max/zero scopes as no-fill controls.",
                "- Route fill-bar ambiguous repaired scopes into interval-bound or tick-order stress before descriptor claims.",
                "- Compare repaired branches against near-miss market-entry and far-miss redesign packets on the shared family denominator.",
                "",
                "No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps({"ok": True, "counts": counts}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
