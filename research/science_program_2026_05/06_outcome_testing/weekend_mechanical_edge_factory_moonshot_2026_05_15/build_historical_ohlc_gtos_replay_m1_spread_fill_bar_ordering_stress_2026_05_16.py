#!/usr/bin/env python3
"""Stress fill-bar target/stop ordering for M1 spread-adjusted replay rows."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
DATE = "2026-05-16"

CONTROL_PROMPT_PATH = (
    REPO
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H_GOAL_PROMPT_2026-05-15.md"
)
STARTER_PATH = ROUTE_DIR / "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H_STARTER_2026-05-15.txt"
INPUT_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_RESULT_2026-05-16.json"
INPUT_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_SIGNATURE_LEDGER_2026-05-16.jsonl"
INPUT_COST_MODEL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_COST_MODEL_LEDGER_2026-05-16.jsonl"

OUTPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_FILL_BAR_ORDERING_STRESS"
RESULT_PATH = ROUTE_DIR / f"{OUTPUT_PREFIX}_RESULT_{DATE}.json"
SIGNATURE_LEDGER_PATH = ROUTE_DIR / f"{OUTPUT_PREFIX}_SIGNATURE_LEDGER_{DATE}.jsonl"
FAMILY_LEDGER_PATH = ROUTE_DIR / f"{OUTPUT_PREFIX}_FAMILY_LEDGER_{DATE}.jsonl"
BUCKET_LEDGER_PATH = ROUTE_DIR / f"{OUTPUT_PREFIX}_BUCKET_LEDGER_{DATE}.jsonl"
QUESTION_LEDGER_PATH = ROUTE_DIR / f"{OUTPUT_PREFIX}_QUESTION_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{OUTPUT_PREFIX}_SUMMARY_{DATE}.md"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS replay M1 spread fill-bar ordering stress only. This packet "
    "preserves the full upstream M1 spread-adjusted signature denominator, splits rows "
    "whose original m1_first_touch_status has fill-bar order-unresolved target/stop "
    "touches into optimistic and conservative M1 interval statuses, and uses MT5 M1 "
    "bars read-only where row fields alone cannot evaluate the conservative next-bar "
    "path. It makes no validation, R/PnL, win-rate, expectancy, live-readiness, "
    "promotion, or live behavior-change claim."
)

NOT_COMPLETION = (
    "This branch-local fill-bar ordering stress packet does not complete the weekend "
    "moonshot objective and does not close tick-level ordering uncertainty."
)

EVIDENCE_CLASS = "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_FILL_BAR_ORDERING_STRESS_ONLY"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
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


def rel(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def source_manifest() -> tuple[list[dict[str, Any]], str]:
    paths = [
        CONTROL_PROMPT_PATH,
        STARTER_PATH,
        INPUT_RESULT_PATH,
        INPUT_SIGNATURE_PATH,
        INPUT_COST_MODEL_PATH,
    ]
    rows = []
    for path in paths:
        rows.append(
            {
                "path": rel(path),
                "sha256": sha256_file(path) if path.exists() else "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
                "status": "HASHED" if path.exists() else "MISSING_FAIL_CLOSED",
            }
        )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def is_fill_bar_order_unresolved(status: str) -> bool:
    return "FILL_BAR_" in status and "ORDER_UNRESOLVED" in status


def target_touch(side: str, high: float, low: float, price: float) -> bool:
    return low <= price if side.upper() == "SHORT" else high >= price


def stop_touch(side: str, high: float, low: float, price: float) -> bool:
    return high >= price if side.upper() == "SHORT" else low <= price


def optimistic_status(row: dict[str, Any]) -> str:
    target = bool(row.get("fill_bar_target_touch"))
    stop = bool(row.get("fill_bar_stop_touch"))
    if target and stop:
        return "OPTIMISTIC_TARGET_AND_STOP_TOUCH_ON_FILL_BAR_ORDER_UNRESOLVED"
    if target:
        return "OPTIMISTIC_TARGET_TOUCH_FIRST_OR_ONLY_ON_FILL_BAR"
    if stop:
        return "OPTIMISTIC_STOP_TOUCH_FIRST_OR_ONLY_ON_FILL_BAR"
    return "OPTIMISTIC_FILL_BAR_STATUS_PRESENT_BUT_NO_FILL_BAR_TARGET_STOP_FLAG"


def carried_status(prefix: str, original_status: str) -> str:
    return f"{prefix}_{original_status}"


def classify_conservative_path(
    row: dict[str, Any],
    bars: list[dict[str, Any]],
    source_status: str,
    source_error: str | None,
) -> dict[str, Any]:
    if source_status != "MT5_M1_NEXT_BARS_AVAILABLE":
        return {
            "conservative_first_touch_status": source_status,
            "conservative_source_status": source_status,
            "conservative_source_error": source_error,
            "conservative_m1_bars_evaluated": len(bars),
            "conservative_first_target_touch_m1_utc": None,
            "conservative_first_stop_touch_m1_utc": None,
            "conservative_first_target_touch_m1_offset_from_fill": None,
            "conservative_first_stop_touch_m1_offset_from_fill": None,
            "conservative_first_target_touch_m1_offset_from_start": None,
            "conservative_first_stop_touch_m1_offset_from_start": None,
        }

    side = str(row["side"])
    target = float(row["target_price_m1_proxy"])
    stop = float(row["stop_price_m1_proxy"])
    first_target_index: int | None = None
    first_stop_index: int | None = None
    for index, bar in enumerate(bars):
        high = float(bar["high"])
        low = float(bar["low"])
        if first_target_index is None and target_touch(side, high, low, target):
            first_target_index = index
        if first_stop_index is None and stop_touch(side, high, low, stop):
            first_stop_index = index
        if first_target_index is not None and first_stop_index is not None:
            break

    if first_target_index is None and first_stop_index is None:
        status = "CONSERVATIVE_NO_TARGET_OR_STOP_TOUCH_AFTER_FILL_BAR"
    elif first_target_index is not None and first_stop_index is not None and first_target_index == first_stop_index:
        status = "CONSERVATIVE_TARGET_AND_STOP_TOUCH_SAME_M1_BAR_AMBIGUOUS_AFTER_FILL_BAR"
    elif first_target_index is not None and (first_stop_index is None or first_target_index < first_stop_index):
        status = "CONSERVATIVE_TARGET_TOUCH_FIRST_OR_ONLY_AFTER_FILL_BAR"
    else:
        status = "CONSERVATIVE_STOP_TOUCH_FIRST_OR_ONLY_AFTER_FILL_BAR"

    return {
        "conservative_first_touch_status": status,
        "conservative_source_status": source_status,
        "conservative_source_error": source_error,
        "conservative_m1_bars_evaluated": len(bars),
        "conservative_first_target_touch_m1_utc": iso_utc(bars[first_target_index]["time"]) if first_target_index is not None else None,
        "conservative_first_stop_touch_m1_utc": iso_utc(bars[first_stop_index]["time"]) if first_stop_index is not None else None,
        "conservative_first_target_touch_m1_offset_from_fill": first_target_index + 1 if first_target_index is not None else None,
        "conservative_first_stop_touch_m1_offset_from_fill": first_stop_index + 1 if first_stop_index is not None else None,
        "conservative_first_target_touch_m1_offset_from_start": first_target_index if first_target_index is not None else None,
        "conservative_first_stop_touch_m1_offset_from_start": first_stop_index if first_stop_index is not None else None,
    }


def interval_status(optimistic: str, conservative: str) -> str:
    if optimistic.startswith("OPTIMISTIC_TARGET_AND_STOP"):
        optimistic_side = "BOTH"
    elif "TARGET" in optimistic:
        optimistic_side = "TARGET"
    elif "STOP" in optimistic:
        optimistic_side = "STOP"
    else:
        optimistic_side = "UNKNOWN"

    if "NO_TARGET_OR_STOP" in conservative:
        conservative_side = "NONE"
    elif "TARGET_AND_STOP" in conservative:
        conservative_side = "BOTH"
    elif "TARGET_TOUCH" in conservative:
        conservative_side = "TARGET"
    elif "STOP_TOUCH" in conservative:
        conservative_side = "STOP"
    elif "FAIL_CLOSED" in conservative or "UNAVAILABLE" in conservative or "FAILED" in conservative:
        conservative_side = "SOURCE_FAIL_CLOSED"
    else:
        conservative_side = "UNKNOWN"
    return f"INTERVAL_OPTIMISTIC_{optimistic_side}_TO_CONSERVATIVE_{conservative_side}"


def mt5_next_bar_windows(
    rows: list[dict[str, Any]],
    cost_by_fill_id: dict[str, dict[str, Any]],
) -> tuple[dict[tuple[str, str, int], dict[str, Any]], dict[str, Any]]:
    unresolved = [row for row in rows if is_fill_bar_order_unresolved(str(row.get("m1_first_touch_status", "")))]
    query_specs: dict[tuple[str, str, int], tuple[str, datetime, datetime]] = {}
    failed_specs: dict[tuple[str, str, int], dict[str, Any]] = {}
    for row in unresolved:
        cost = cost_by_fill_id.get(str(row.get("cost_fill_id")))
        fill_time = parse_utc(str(row.get("m1_fill_utc")) if row.get("m1_fill_utc") else None)
        fill_offset = row.get("m1_fill_bar_offset")
        bars_returned = cost.get("m1_bars_returned") if cost else None
        key = (
            str(row.get("symbol")),
            str(row.get("m1_fill_utc")),
            int(row.get("m1_fill_bar_offset") or -1),
        )
        if cost is None:
            failed_specs[key] = {
                "bars": [],
                "source_status": "MT5_M1_COST_MODEL_ROW_MISSING_FAIL_CLOSED",
                "source_error": f"cost_fill_id={row.get('cost_fill_id')}",
            }
            continue
        if fill_time is None or fill_offset is None or bars_returned is None:
            failed_specs[key] = {
                "bars": [],
                "source_status": "MT5_M1_NEXT_BAR_WINDOW_FIELDS_MISSING_FAIL_CLOSED",
                "source_error": "m1_fill_utc/m1_fill_bar_offset/m1_bars_returned missing",
            }
            continue
        remaining_after_fill = int(bars_returned) - int(fill_offset) - 1
        if remaining_after_fill <= 0:
            failed_specs[key] = {
                "bars": [],
                "source_status": "MT5_M1_NO_NEXT_BAR_IN_ORIGINAL_REPLAY_WINDOW_FAIL_CLOSED",
                "source_error": None,
            }
            continue
        start = fill_time + timedelta(minutes=1)
        end = fill_time + timedelta(minutes=remaining_after_fill)
        query_specs[key] = (str(row.get("symbol")), start, end)

    terminal_summary: dict[str, Any]
    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on local terminal
        mt5 = None
        mt5_init_ok = False
        terminal_summary = {
            "mt5_module_available": False,
            "mt5_initialize": False,
            "mt5_error": f"{type(exc).__name__}: {exc}",
            "read_only_market_data_probe": True,
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

    result: dict[tuple[str, str, int], dict[str, Any]] = dict(failed_specs)
    symbol_select_cache: dict[str, tuple[bool, Any]] = {}
    try:
        for key, spec in query_specs.items():
            symbol, start, end = spec
            bars: list[dict[str, Any]] = []
            source_status = "MT5_NOT_INITIALIZED_FAIL_CLOSED"
            source_error: str | None = None
            if mt5 is not None and mt5_init_ok:
                if symbol not in symbol_select_cache:
                    symbol_select_cache[symbol] = (bool(mt5.symbol_select(symbol, True)), mt5.last_error())
                selected, select_error = symbol_select_cache[symbol]
                if not selected:
                    source_status = "MT5_SYMBOL_SELECT_FAILED_FAIL_CLOSED"
                    source_error = str(select_error)
                else:
                    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, start, end)
                    if rates is None:
                        source_status = "MT5_COPY_RATES_M1_RETURNED_NONE_FAIL_CLOSED"
                        source_error = str(mt5.last_error())
                    elif len(rates) == 0:
                        source_status = "MT5_NO_M1_NEXT_BARS_IN_CONSERVATIVE_WINDOW_FAIL_CLOSED"
                    else:
                        source_status = "MT5_M1_NEXT_BARS_AVAILABLE"
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
            result[key] = {
                "bars": bars,
                "source_status": source_status,
                "source_error": source_error,
                "window_start_utc": iso_utc(start),
                "window_end_utc": iso_utc(end),
            }
    finally:
        if mt5 is not None and mt5_init_ok:
            mt5.shutdown()

    terminal_summary["unique_conservative_m1_query_windows"] = len(query_specs)
    terminal_summary["prequery_fail_closed_windows"] = len(failed_specs)
    return result, terminal_summary


def add_bucket(rows: list[dict[str, Any]], axis: str, counter: Counter[Any]) -> None:
    for bucket, count in sorted(counter.items(), key=lambda item: str(item[0])):
        rows.append(
            {
                "bucket_axis": axis,
                "bucket": "|".join(str(part) for part in bucket) if isinstance(bucket, tuple) else str(bucket),
                "count": count,
                "evidence_class": f"{EVIDENCE_CLASS}_BUCKET",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )


def main() -> int:
    generated_at = now_utc()
    source_rows, source_manifest_hash = source_manifest()
    input_result = read_json(INPUT_RESULT_PATH)
    signature_input = [row for row in read_jsonl(INPUT_SIGNATURE_PATH) if not row.get("_parse_error")]
    cost_model_input = [row for row in read_jsonl(INPUT_COST_MODEL_PATH) if not row.get("_parse_error")]
    cost_by_fill_id = {str(row.get("cost_fill_id")): row for row in cost_model_input}
    mt5_windows, terminal_summary = mt5_next_bar_windows(signature_input, cost_by_fill_id)

    signature_rows: list[dict[str, Any]] = []
    for seq, row in enumerate(signature_input, 1):
        original_status = str(row.get("m1_first_touch_status", ""))
        stress_scope_status = (
            "FILL_BAR_ORDER_UNRESOLVED_STRESSED"
            if is_fill_bar_order_unresolved(original_status)
            else "NON_FILL_BAR_ORDER_STATUS_CARRIED_FORWARD"
        )
        if stress_scope_status == "FILL_BAR_ORDER_UNRESOLVED_STRESSED":
            key = (
                str(row.get("symbol")),
                str(row.get("m1_fill_utc")),
                int(row.get("m1_fill_bar_offset") or -1),
            )
            window = mt5_windows.get(
                key,
                {
                    "bars": [],
                    "source_status": "MT5_M1_NEXT_BAR_WINDOW_NOT_BUILT_FAIL_CLOSED",
                    "source_error": None,
                    "window_start_utc": None,
                    "window_end_utc": None,
                },
            )
            optimistic = optimistic_status(row)
            conservative = classify_conservative_path(
                row,
                list(window.get("bars") or []),
                str(window.get("source_status")),
                window.get("source_error"),
            )
            interval = interval_status(optimistic, str(conservative["conservative_first_touch_status"]))
            window_start = window.get("window_start_utc")
            window_end = window.get("window_end_utc")
        else:
            optimistic = carried_status("OPTIMISTIC_CARRIED", original_status)
            conservative = {
                "conservative_first_touch_status": carried_status("CONSERVATIVE_CARRIED", original_status),
                "conservative_source_status": "ROW_FIELDS_SUFFICIENT_NO_FILL_BAR_STRESS_NEEDED",
                "conservative_source_error": None,
                "conservative_m1_bars_evaluated": 0,
                "conservative_first_target_touch_m1_utc": row.get("first_target_touch_m1_utc"),
                "conservative_first_stop_touch_m1_utc": row.get("first_stop_touch_m1_utc"),
                "conservative_first_target_touch_m1_offset_from_fill": row.get("first_target_touch_m1_offset"),
                "conservative_first_stop_touch_m1_offset_from_fill": row.get("first_stop_touch_m1_offset"),
                "conservative_first_target_touch_m1_offset_from_start": None,
                "conservative_first_stop_touch_m1_offset_from_start": None,
            }
            interval = "INTERVAL_NOT_APPLICABLE_NON_FILL_BAR_ORDER_STATUS_CARRIED"
            window_start = None
            window_end = None

        signature_rows.append(
            {
                **row,
                "fill_bar_ordering_stress_signature_id": f"OHLC-GTOS-M1-SPREAD-FILL-BAR-ORDER-SIG-{seq:05d}",
                "stress_scope_status": stress_scope_status,
                "optimistic_first_touch_status": optimistic,
                **conservative,
                "interval_status": interval,
                "conservative_window_start_utc": window_start,
                "conservative_window_end_utc": window_end,
                "source_manifest_hash": source_manifest_hash,
                "evidence_class": f"{EVIDENCE_CLASS}_SIGNATURE",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    family_counter: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    family_stress_counter: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    family_conservative_counter: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    family_examples: dict[tuple[str, str], dict[str, Any]] = {}
    for row in signature_rows:
        key = (str(row["family_key"]), str(row["cost_model"]))
        family_counter[key][str(row["interval_status"])] += 1
        family_stress_counter[key][str(row["stress_scope_status"])] += 1
        family_conservative_counter[key][str(row["conservative_first_touch_status"])] += 1
        family_examples.setdefault(key, row)

    family_rows: list[dict[str, Any]] = []
    for seq, (key, counter) in enumerate(sorted(family_counter.items()), 1):
        example = family_examples[key]
        family_rows.append(
            {
                "fill_bar_ordering_stress_family_id": f"OHLC-GTOS-M1-SPREAD-FILL-BAR-ORDER-FAMILY-{seq:05d}",
                "family_key": key[0],
                "cost_model": key[1],
                "route_candidate_id": example.get("route_candidate_id"),
                "route_session": example.get("route_session"),
                "symbol": example.get("symbol"),
                "side": example.get("side"),
                "entry_variant": example.get("entry_variant"),
                "target_stop_contract_id": example.get("target_stop_contract_id"),
                "target_multiple": example.get("target_multiple"),
                "stop_multiple": example.get("stop_multiple"),
                "signature_rows": sum(counter.values()),
                "stress_scope_status_counts": dict(sorted(family_stress_counter[key].items())),
                "interval_status_counts": dict(sorted(counter.items())),
                "conservative_first_touch_status_counts": dict(sorted(family_conservative_counter[key].items())),
                "same_m15_ambiguity_rows_for_family": example.get("same_m15_ambiguity_rows_for_family"),
                "cross_control_family_status": example.get("cross_control_family_status"),
                "source_manifest_hash": source_manifest_hash,
                "evidence_class": f"{EVIDENCE_CLASS}_FAMILY",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    bucket_rows: list[dict[str, Any]] = []
    add_bucket(bucket_rows, "stress_scope_status", Counter(row["stress_scope_status"] for row in signature_rows))
    add_bucket(bucket_rows, "original_m1_first_touch_status", Counter(row["m1_first_touch_status"] for row in signature_rows))
    add_bucket(bucket_rows, "optimistic_first_touch_status", Counter(row["optimistic_first_touch_status"] for row in signature_rows))
    add_bucket(bucket_rows, "conservative_first_touch_status", Counter(row["conservative_first_touch_status"] for row in signature_rows))
    add_bucket(bucket_rows, "interval_status", Counter(row["interval_status"] for row in signature_rows))
    add_bucket(bucket_rows, "cost_model__interval_status", Counter((row["cost_model"], row["interval_status"]) for row in signature_rows))
    add_bucket(bucket_rows, "symbol__interval_status", Counter((row["symbol"], row["interval_status"]) for row in signature_rows))
    add_bucket(bucket_rows, "session__interval_status", Counter((row["route_session"], row["interval_status"]) for row in signature_rows))
    add_bucket(bucket_rows, "side__interval_status", Counter((row["side"], row["interval_status"]) for row in signature_rows))
    add_bucket(bucket_rows, "conservative_source_status", Counter(row["conservative_source_status"] for row in signature_rows))
    add_bucket(
        bucket_rows,
        "fill_bar_original__conservative",
        Counter(
            (row["m1_first_touch_status"], row["conservative_first_touch_status"])
            for row in signature_rows
            if row["stress_scope_status"] == "FILL_BAR_ORDER_UNRESOLVED_STRESSED"
        ),
    )

    fill_bar_rows = [row for row in signature_rows if row["stress_scope_status"] == "FILL_BAR_ORDER_UNRESOLVED_STRESSED"]
    conservative_stop_rows = [
        row for row in fill_bar_rows if row["conservative_first_touch_status"] == "CONSERVATIVE_STOP_TOUCH_FIRST_OR_ONLY_AFTER_FILL_BAR"
    ]
    conservative_none_rows = [
        row for row in fill_bar_rows if row["conservative_first_touch_status"] == "CONSERVATIVE_NO_TARGET_OR_STOP_TOUCH_AFTER_FILL_BAR"
    ]
    conservative_target_rows = [
        row for row in fill_bar_rows if row["conservative_first_touch_status"] == "CONSERVATIVE_TARGET_TOUCH_FIRST_OR_ONLY_AFTER_FILL_BAR"
    ]
    conservative_ambiguous_rows = [
        row
        for row in fill_bar_rows
        if row["conservative_first_touch_status"] == "CONSERVATIVE_TARGET_AND_STOP_TOUCH_SAME_M1_BAR_AMBIGUOUS_AFTER_FILL_BAR"
    ]
    source_fail_rows = [
        row
        for row in fill_bar_rows
        if row["conservative_source_status"] != "MT5_M1_NEXT_BARS_AVAILABLE"
    ]

    question_seed = [
        (
            "OHLC-GTOS-M1-SPREAD-FILL-BAR-ORDER-QUESTION-001",
            "How many upstream signatures required fill-bar ordering stress?",
            len(fill_bar_rows),
            "Use the stressed full-denominator signature ledger rather than the original fill-bar order-unresolved bucket for downstream family synthesis.",
        ),
        (
            "OHLC-GTOS-M1-SPREAD-FILL-BAR-ORDER-QUESTION-002",
            "How many optimistic fill-bar target touches remain target-first after excluding the fill bar?",
            len(conservative_target_rows),
            "These rows are interval-stable at M1 resolution but still not tick-order exact inside the fill bar.",
        ),
        (
            "OHLC-GTOS-M1-SPREAD-FILL-BAR-ORDER-QUESTION-003",
            "How many optimistic fill-bar target touches become no-touch under the conservative next-bar path?",
            len(conservative_none_rows),
            "Carry as target-to-none interval uncertainty until exact tick ordering or an approved stronger proxy is available.",
        ),
        (
            "OHLC-GTOS-M1-SPREAD-FILL-BAR-ORDER-QUESTION-004",
            "How many optimistic fill-bar target touches become stop-first under the conservative next-bar path?",
            len(conservative_stop_rows),
            "Treat as the sharpest interval divergence family for downstream risk/fill synthesis and tick-source pursuit.",
        ),
        (
            "OHLC-GTOS-M1-SPREAD-FILL-BAR-ORDER-QUESTION-005",
            "How many conservative next-bar paths remain same-M1-bar target/stop ambiguous?",
            len(conservative_ambiguous_rows),
            "Route to tick-level or sub-M1 ordering pursuit before any descriptor is used beyond stress bounds.",
        ),
        (
            "OHLC-GTOS-M1-SPREAD-FILL-BAR-ORDER-QUESTION-006",
            "How many fill-bar stress rows failed closed due missing next-bar M1 source?",
            len(source_fail_rows),
            "Use the conservative source-status buckets to separate recoverable MT5/source issues from true interval evidence.",
        ),
    ]
    question_rows = [
        {
            "question_id": question_id,
            "question": question,
            "row_count": row_count,
            "next_same_resource_action": action,
            "evidence_class": f"{EVIDENCE_CLASS}_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for question_id, question, row_count, action in question_seed
    ]

    verifier_checks = {
        "signature_rows_preserve_full_denominator": len(signature_rows) == len(signature_input),
        "fill_bar_unresolved_rows_preserved": len(fill_bar_rows)
        == sum(is_fill_bar_order_unresolved(str(row.get("m1_first_touch_status", ""))) for row in signature_input),
        "all_signature_rows_have_safe_flags": all(row.get("safe_flags") == SAFE_FLAGS for row in signature_rows),
        "all_family_rows_have_safe_flags": all(row.get("safe_flags") == SAFE_FLAGS for row in family_rows),
        "source_manifest_all_files_hashed": all(row["status"] == "HASHED" for row in source_rows),
        "no_output_manifest_or_sprint_ledger_write": True,
    }
    verifier = {
        "ok": all(verifier_checks.values()),
        "checks": verifier_checks,
        "py_compile_required": True,
        "script_generated_outputs_only": [
            rel(RESULT_PATH),
            rel(SIGNATURE_LEDGER_PATH),
            rel(FAMILY_LEDGER_PATH),
            rel(BUCKET_LEDGER_PATH),
            rel(QUESTION_LEDGER_PATH),
            rel(SUMMARY_PATH),
        ],
    }

    counts = {
        "input_signature_rows": len(signature_input),
        "input_cost_model_rows": len(cost_model_input),
        "output_signature_rows": len(signature_rows),
        "family_rows": len(family_rows),
        "bucket_rows": len(bucket_rows),
        "question_rows": len(question_rows),
        "fill_bar_order_unresolved_rows": len(fill_bar_rows),
        "conservative_target_after_fill_bar_rows": len(conservative_target_rows),
        "conservative_no_touch_after_fill_bar_rows": len(conservative_none_rows),
        "conservative_stop_after_fill_bar_rows": len(conservative_stop_rows),
        "conservative_same_m1_ambiguous_after_fill_bar_rows": len(conservative_ambiguous_rows),
        "conservative_source_fail_closed_rows": len(source_fail_rows),
        "source_manifest_rows": len(source_rows),
    }
    output = {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "historical_ohlc_gtos_replay_m1_spread_fill_bar_ordering_stress_v1",
        "generated_utc": generated_at,
        "evidence_class": EVIDENCE_CLASS,
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": NOT_COMPLETION,
        "counts": counts,
        "original_m1_first_touch_status_counts": dict(sorted(Counter(row["m1_first_touch_status"] for row in signature_rows).items())),
        "stress_scope_status_counts": dict(sorted(Counter(row["stress_scope_status"] for row in signature_rows).items())),
        "optimistic_first_touch_status_counts": dict(sorted(Counter(row["optimistic_first_touch_status"] for row in signature_rows).items())),
        "conservative_first_touch_status_counts": dict(sorted(Counter(row["conservative_first_touch_status"] for row in signature_rows).items())),
        "interval_status_counts": dict(sorted(Counter(row["interval_status"] for row in signature_rows).items())),
        "terminal_summary": terminal_summary,
        "upstream_counts": input_result.get("counts", {}),
        "source_manifest": source_rows,
        "source_manifest_hash": source_manifest_hash,
        "verifier": verifier,
        "next_unresolved_questions": question_rows,
    }

    write_jsonl(SIGNATURE_LEDGER_PATH, signature_rows)
    write_jsonl(FAMILY_LEDGER_PATH, family_rows)
    write_jsonl(BUCKET_LEDGER_PATH, bucket_rows)
    write_jsonl(QUESTION_LEDGER_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay M1 Spread Fill-Bar Ordering Stress",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                CLAIM_BOUNDARY,
                "",
                "## Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in counts.items()),
                "",
                "## Conservative First-Touch Status",
                "",
                *(f"- `{key}`: `{value}`" for key, value in output["conservative_first_touch_status_counts"].items()),
                "",
                "## Interval Status",
                "",
                *(f"- `{key}`: `{value}`" for key, value in output["interval_status_counts"].items()),
                "",
                "## Verifier",
                "",
                f"- `ok`: `{verifier['ok']}`",
                *(f"- `{key}`: `{value}`" for key, value in verifier_checks.items()),
                "",
                "## Next Unresolved Questions",
                "",
                *(f"- `{row['question_id']}`: {row['question']} (`row_count={row['row_count']}`)" for row in question_rows),
                "",
                NOT_COMPLETION,
                "",
                "No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": verifier["ok"], "counts": counts}, sort_keys=True))
    return 0 if verifier["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
