#!/usr/bin/env python3
"""Replay M1 spread-adjusted fills for no-fill source-alignment rows."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

SOURCE_ALIGNMENT_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_RESULT_2026-05-16.json"
SOURCE_ALIGNMENT_ENTRY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_ENTRY_LEDGER_2026-05-16.jsonl"
SOURCE_ALIGNMENT_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_SIGNATURE_LEDGER_2026-05-16.jsonl"
SOURCE_ALIGNMENT_COST_MODEL_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_NOFILL_COST_THRESHOLD_SOURCE_ALIGNMENT_COST_MODEL_LEDGER_2026-05-16.jsonl"
TARGET_STOP_CONTRACT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_TARGET_STOP_CONTRACT_LEDGER_2026-05-16.jsonl"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_RESULT_2026-05-16.json"
ENTRY_REPLAY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_ENTRY_LEDGER_2026-05-16.jsonl"
COST_MODEL_REPLAY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_COST_MODEL_LEDGER_2026-05-16.jsonl"
SIGNATURE_REPLAY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_SIGNATURE_LEDGER_2026-05-16.jsonl"
FAMILY_REPLAY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_FAMILY_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

ALL_THRESHOLD_STATUS = "M1_TOUCHES_ALL_SPREAD_ADJUSTED_THRESHOLDS_ZERO_UNTOUCHED"
MODEL_CONFLICT_STATUS = "M1_TOUCHES_MODEL_THRESHOLD_BUT_M15_COST_PATH_NOT_FILLED"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS M1 spread-adjusted fill replay packet only. Rows replay "
    "source-alignment entries where M1 touches spread-adjusted effective thresholds "
    "while zero entry remains untouched; target/stop ordering is M1-proxy only and "
    "same-bar ordering remains explicit; no validation, R/PnL, expectancy, win-rate, "
    "live-readiness, promotion, or live behavior change is claimed."
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
        SOURCE_ALIGNMENT_RESULT_PATH,
        SOURCE_ALIGNMENT_ENTRY_PATH,
        SOURCE_ALIGNMENT_SIGNATURE_PATH,
        SOURCE_ALIGNMENT_COST_MODEL_PATH,
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
            "m1_replay_path_status": "M1_SPREAD_ADJUSTED_FILL_NOT_FOUND_FAIL_CLOSED",
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
        status = "NO_TARGET_OR_STOP_TOUCH_WITHIN_M1_REPLAY_HORIZON"
    elif first_target_index is not None and first_stop_index is not None and first_target_index == first_stop_index:
        if first_target_index == fill_index:
            status = "FILL_BAR_TARGET_AND_STOP_TOUCH_M1_PROXY_ORDER_UNRESOLVED"
        else:
            status = "TARGET_AND_STOP_TOUCH_SAME_M1_BAR_AMBIGUOUS"
    elif first_target_index is not None and (first_stop_index is None or first_target_index < first_stop_index):
        if first_target_index == fill_index:
            status = "FILL_BAR_TARGET_TOUCH_FIRST_OR_ONLY_M1_PROXY_ORDER_UNRESOLVED"
        else:
            status = "TARGET_TOUCH_FIRST_OR_ONLY_M1_PROXY"
    else:
        if first_stop_index == fill_index:
            status = "FILL_BAR_STOP_TOUCH_FIRST_OR_ONLY_M1_PROXY_ORDER_UNRESOLVED"
        else:
            status = "STOP_TOUCH_FIRST_OR_ONLY_M1_PROXY"
    first_target_utc = iso_utc(bars[first_target_index]["time"]) if first_target_index is not None else None
    first_stop_utc = iso_utc(bars[first_stop_index]["time"]) if first_stop_index is not None else None
    return {
        "m1_replay_path_status": "M1_SPREAD_ADJUSTED_FILL_PATH_REPLAYED",
        "m1_first_touch_status": status,
        "target_price_m1_proxy": round_price(target),
        "stop_price_m1_proxy": round_price(stop),
        "first_target_touch_m1_utc": first_target_utc,
        "first_stop_touch_m1_utc": first_stop_utc,
        "first_target_touch_m1_offset": first_target_index - fill_index if first_target_index is not None else None,
        "first_stop_touch_m1_offset": first_stop_index - fill_index if first_stop_index is not None else None,
        "fill_bar_target_touch": fill_bar_target_touch,
        "fill_bar_stop_touch": fill_bar_stop_touch,
    }


def update_manifest(outputs: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    existing = [row for row in manifest.get("outputs", []) if row.get("artifact") != RESULT_PATH.name]
    existing.append(
        {
            "artifact": RESULT_PATH.name,
            "category": "historical_ohlc_gtos_replay_m1_spread_adjusted_fill_replay",
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
        "route": "historical_ohlc_gtos_replay_m1_spread_adjusted_fill_replay",
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
    source_alignment_result = read_json(SOURCE_ALIGNMENT_RESULT_PATH)
    source_entries = [row for row in read_jsonl(SOURCE_ALIGNMENT_ENTRY_PATH) if not row.get("_parse_error")]
    source_signatures = [row for row in read_jsonl(SOURCE_ALIGNMENT_SIGNATURE_PATH) if not row.get("_parse_error")]
    source_cost_models = [row for row in read_jsonl(SOURCE_ALIGNMENT_COST_MODEL_PATH) if not row.get("_parse_error")]
    target_stop_contracts = [row for row in read_jsonl(TARGET_STOP_CONTRACT_PATH) if not row.get("_parse_error")]
    target_stop_by_id = {row["target_stop_contract_id"]: row for row in target_stop_contracts}
    signatures_by_entry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_signatures:
        signatures_by_entry[row["entry_variant_id"]].append(row)
    cost_models_by_entry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in source_cost_models:
        cost_models_by_entry[row["entry_variant_id"]].append(row)

    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:  # pragma: no cover - local terminal dependency
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
    bars_by_entry: dict[str, list[dict[str, Any]]] = {}
    m1_source_status_by_entry: dict[str, str] = {}
    m1_error_by_entry: dict[str, str | None] = {}
    try:
        for entry in source_entries:
            entry_id = entry["entry_variant_id"]
            if entry["entry_alignment_status"] != ALL_THRESHOLD_STATUS:
                continue
            symbol = str(entry["symbol"])
            start = parse_utc(str(entry["probe_window_start_utc"]))
            end = parse_utc(str(entry["probe_window_end_utc"]))
            bars: list[dict[str, Any]] = []
            status = "MT5_NOT_INITIALIZED_FAIL_CLOSED"
            error = None
            if mt5 is not None and mt5_init_ok:
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
                        status = "MT5_NO_M1_BARS_IN_REPLAY_WINDOW_FAIL_CLOSED" if len(rates) == 0 else "MT5_M1_BARS_AVAILABLE"
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
            bars_by_entry[entry_id] = bars
            m1_source_status_by_entry[entry_id] = status
            m1_error_by_entry[entry_id] = error
    finally:
        if mt5 is not None and mt5_init_ok:
            mt5.shutdown()

    cost_model_replay_rows: list[dict[str, Any]] = []
    replayable_cost_models_by_entry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    entry_rows: list[dict[str, Any]] = []
    for seq, entry in enumerate(source_entries, 1):
        entry_id = entry["entry_variant_id"]
        replay_scope_status = "NONREPLAY_SOURCE_ALIGNMENT_ROUTE_SPLIT"
        if entry["entry_alignment_status"] == ALL_THRESHOLD_STATUS:
            replay_scope_status = "REPLAYED_ALL_SPREAD_ADJUSTED_THRESHOLD_TOUCH_ENTRY"
        elif entry["entry_alignment_status"] == "M1_TOUCHES_PARTIAL_SPREAD_ADJUSTED_THRESHOLDS_ZERO_UNTOUCHED":
            replay_scope_status = "PARTIAL_THRESHOLD_TOUCH_ROUTE_SPLIT_ONLY"
        elif entry["entry_alignment_status"] == "CONFLICT_NOT_M1_PROXY_SOURCE_RECHECK":
            replay_scope_status = "SOURCE_RECHECK_ROUTE_SPLIT_ONLY"
        bars = bars_by_entry.get(entry_id, [])
        touched_models = [
            row
            for row in cost_models_by_entry.get(entry_id, [])
            if row.get("cost_model_alignment_status") == MODEL_CONFLICT_STATUS
            and row.get("cost_model") != "ZERO_COST_CONTROL"
            and entry["entry_alignment_status"] == ALL_THRESHOLD_STATUS
        ]
        fill_offsets: list[int] = []
        for cost in touched_models:
            fill_index = None
            threshold = float(cost["effective_entry_price"])
            for index, bar in enumerate(bars):
                if side_fill_touch(str(entry["side"]), float(bar["high"]), float(bar["low"]), threshold):
                    fill_index = index
                    break
            fill_offsets.append(fill_index if fill_index is not None else -1)
            fill_status = (
                "M1_SPREAD_ADJUSTED_THRESHOLD_FILL_FOUND"
                if fill_index is not None
                else "M1_SPREAD_ADJUSTED_THRESHOLD_FILL_NOT_FOUND_FAIL_CLOSED"
            )
            row = {
                "m1_spread_adjusted_cost_model_replay_id": f"OHLC-GTOS-M1-SPREAD-FILL-COST-{len(cost_model_replay_rows) + 1:05d}",
                "entry_variant_id": entry_id,
                "event_id": entry["event_id"],
                "route_candidate_id": entry["route_candidate_id"],
                "route_session": entry["route_session"],
                "symbol": entry["symbol"],
                "side": entry["side"],
                "entry_variant": entry["entry_variant"],
                "cost_model": cost["cost_model"],
                "cost_fill_id": cost["cost_fill_id"],
                "effective_entry_price": cost["effective_entry_price"],
                "entry_price_input_only": cost["entry_price_input_only"],
                "spread_proxy_price_distance": cost["spread_proxy_price_distance"],
                "m1_source_status": m1_source_status_by_entry.get(entry_id),
                "m1_source_error": m1_error_by_entry.get(entry_id),
                "m1_bars_returned": len(bars),
                "m1_fill_status": fill_status,
                "m1_fill_utc": iso_utc(bars[fill_index]["time"]) if fill_index is not None else None,
                "m1_fill_bar_offset": fill_index,
                "m1_fill_bar_high": bars[fill_index]["high"] if fill_index is not None else None,
                "m1_fill_bar_low": bars[fill_index]["low"] if fill_index is not None else None,
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_COST_MODEL",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
            cost_model_replay_rows.append(row)
            replayable_cost_models_by_entry[entry_id].append(row)
        entry_rows.append(
            {
                "m1_spread_adjusted_entry_replay_id": f"OHLC-GTOS-M1-SPREAD-FILL-ENTRY-{seq:05d}",
                "entry_variant_id": entry_id,
                "event_id": entry["event_id"],
                "route_candidate_id": entry["route_candidate_id"],
                "route_session": entry["route_session"],
                "symbol": entry["symbol"],
                "side": entry["side"],
                "entry_variant": entry["entry_variant"],
                "entry_alignment_status": entry["entry_alignment_status"],
                "replay_scope_status": replay_scope_status,
                "m1_source_status": m1_source_status_by_entry.get(entry_id),
                "m1_source_error": m1_error_by_entry.get(entry_id),
                "m1_bars_returned": len(bars),
                "touched_spread_cost_models_replayed": sorted({row["cost_model"] for row in touched_models}),
                "cost_model_replay_rows": len(touched_models),
                "signature_rows": len(signatures_by_entry.get(entry_id, [])),
                "min_m1_fill_bar_offset": min([offset for offset in fill_offsets if offset >= 0], default=None),
                "max_m1_fill_bar_offset": max([offset for offset in fill_offsets if offset >= 0], default=None),
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_ENTRY",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    signature_rows: list[dict[str, Any]] = []
    for signature in source_signatures:
        if signature["entry_alignment_status"] != ALL_THRESHOLD_STATUS:
            continue
        contract = target_stop_by_id.get(signature["target_stop_contract_id"], {})
        for cost in replayable_cost_models_by_entry.get(signature["entry_variant_id"], []):
            fill_index = cost.get("m1_fill_bar_offset")
            entry_match = next(row for row in source_entries if row["entry_variant_id"] == signature["entry_variant_id"])
            replay = replay_target_stop(
                str(signature["side"]),
                bars_by_entry.get(signature["entry_variant_id"], []),
                int(fill_index) if fill_index is not None else None,
                float(cost["effective_entry_price"]),
                float(entry_match.get("rolling_median_range") or 0.0),
                float(contract.get("target_multiple_of_rolling_median_range") or signature.get("target_multiple") or 0.0),
                float(contract.get("stop_multiple_of_rolling_median_range") or signature.get("stop_multiple") or 0.0),
            )
            signature_rows.append(
                {
                    "m1_spread_adjusted_signature_replay_id": f"OHLC-GTOS-M1-SPREAD-FILL-SIG-{len(signature_rows) + 1:05d}",
                    "source_alignment_signature_id": signature["source_alignment_signature_id"],
                    "cost_sensitivity_signature_id": signature["cost_sensitivity_signature_id"],
                    "entry_variant_id": signature["entry_variant_id"],
                    "event_id": signature["event_id"],
                    "route_candidate_id": signature["route_candidate_id"],
                    "route_session": signature["route_session"],
                    "symbol": signature["symbol"],
                    "side": signature["side"],
                    "entry_variant": signature["entry_variant"],
                    "target_stop_contract_id": signature["target_stop_contract_id"],
                    "target_multiple": signature["target_multiple"],
                    "stop_multiple": signature["stop_multiple"],
                    "family_key": signature["family_key"],
                    "cost_model": cost["cost_model"],
                    "cost_fill_id": cost["cost_fill_id"],
                    "effective_entry_price": cost["effective_entry_price"],
                    "m1_fill_status": cost["m1_fill_status"],
                    "m1_fill_utc": cost["m1_fill_utc"],
                    "m1_fill_bar_offset": cost["m1_fill_bar_offset"],
                    "same_m15_ambiguity_rows_for_family": signature.get("same_m15_ambiguity_rows_for_family"),
                    "cross_control_family_status": signature.get("cross_control_family_status"),
                    "family_exact_descriptor_delta_rows": signature.get("family_exact_descriptor_delta_rows"),
                    "family_exact_unavailable_stress_rows": signature.get("family_exact_unavailable_stress_rows"),
                    **replay,
                    "source_manifest_hash": manifest_hash,
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_SIGNATURE",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )

    family_counter: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    family_examples: dict[tuple[str, str], dict[str, Any]] = {}
    for row in signature_rows:
        key = (row["family_key"], row["cost_model"])
        family_counter[key][row["m1_first_touch_status"]] += 1
        family_examples.setdefault(key, row)
    family_rows: list[dict[str, Any]] = []
    for seq, (key, counter) in enumerate(sorted(family_counter.items()), 1):
        example = family_examples[key]
        family_rows.append(
            {
                "m1_spread_adjusted_family_replay_id": f"OHLC-GTOS-M1-SPREAD-FILL-FAMILY-{seq:05d}",
                "family_key": key[0],
                "cost_model": key[1],
                "route_candidate_id": example["route_candidate_id"],
                "route_session": example["route_session"],
                "symbol": example["symbol"],
                "side": example["side"],
                "entry_variant": example["entry_variant"],
                "target_stop_contract_id": example["target_stop_contract_id"],
                "target_multiple": example["target_multiple"],
                "stop_multiple": example["stop_multiple"],
                "signature_rows": sum(counter.values()),
                "m1_first_touch_status_counts": dict(sorted(counter.items())),
                "same_m15_ambiguity_rows_for_family": example.get("same_m15_ambiguity_rows_for_family"),
                "cross_control_family_status": example.get("cross_control_family_status"),
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_FAMILY",
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
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_BUCKET",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )

    add_bucket("entry_replay_scope_status", Counter(row["replay_scope_status"] for row in entry_rows))
    add_bucket("cost_model_fill_status", Counter(row["m1_fill_status"] for row in cost_model_replay_rows))
    add_bucket("cost_model__fill_status", Counter((row["cost_model"], row["m1_fill_status"]) for row in cost_model_replay_rows))
    add_bucket("signature_first_touch_status", Counter(row["m1_first_touch_status"] for row in signature_rows))
    add_bucket("cost_model__signature_first_touch_status", Counter((row["cost_model"], row["m1_first_touch_status"]) for row in signature_rows))
    add_bucket("same_m15_ambiguity__first_touch_status", Counter((bool(row["same_m15_ambiguity_rows_for_family"]), row["m1_first_touch_status"]) for row in signature_rows))
    add_bucket("cross_family_status__first_touch_status", Counter((row.get("cross_control_family_status"), row["m1_first_touch_status"]) for row in signature_rows))
    add_bucket("symbol__first_touch_status", Counter((row["symbol"], row["m1_first_touch_status"]) for row in signature_rows))
    add_bucket("session__first_touch_status", Counter((row["route_session"], row["m1_first_touch_status"]) for row in signature_rows))

    fill_bar_ambiguous = [row for row in signature_rows if "FILL_BAR" in row["m1_first_touch_status"]]
    same_m15_overlap = [row for row in signature_rows if row.get("same_m15_ambiguity_rows_for_family")]
    exact_overlap = [
        row for row in signature_rows
        if row.get("family_exact_descriptor_delta_rows", 0) or row.get("family_exact_unavailable_stress_rows", 0)
    ]
    question_rows = [
        {
            "question_id": "OHLC-GTOS-M1-SPREAD-FILL-QUESTION-001",
            "question": "How many all-threshold source-alignment entries replay as M1 spread-adjusted fills?",
            "row_count": sum(1 for row in entry_rows if row["replay_scope_status"] == "REPLAYED_ALL_SPREAD_ADJUSTED_THRESHOLD_TOUCH_ENTRY"),
            "next_same_resource_action": "use cost-model replay rows as source-safe spread-adjusted fill denominator",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-M1-SPREAD-FILL-QUESTION-002",
            "question": "How many spread-adjusted signature replays have fill-bar target/stop order ambiguity?",
            "row_count": len(fill_bar_ambiguous),
            "next_same_resource_action": "split fill-bar ambiguous rows into conservative target/stop interval bounds or seek tick source",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-M1-SPREAD-FILL-QUESTION-003",
            "question": "How many spread-adjusted signature replays overlap same-M15 ambiguity from the original path-control ledger?",
            "row_count": len(same_m15_overlap),
            "next_same_resource_action": "carry same-M15 ambiguity into family synthesis and target/stop descriptor labels",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-M1-SPREAD-FILL-QUESTION-004",
            "question": "How many spread-adjusted signature replays overlap exact-spread or exact-unavailable families?",
            "row_count": len(exact_overlap),
            "next_same_resource_action": "join spread-adjusted replay to exact-spread context before cost/fill/path synthesis",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]

    counts = {
        "bucket_rows": len(bucket_rows),
        "cost_model_replay_rows": len(cost_model_replay_rows),
        "entry_replay_rows": len(entry_rows),
        "family_replay_rows": len(family_rows),
        "question_rows": len(question_rows),
        "signature_replay_rows": len(signature_rows),
        "source_alignment_cost_model_input_rows": len(source_cost_models),
        "source_alignment_entry_input_rows": len(source_entries),
        "source_alignment_signature_input_rows": len(source_signatures),
        "source_manifest_rows": len(manifest_rows),
        "target_stop_contract_input_rows": len(target_stop_contracts),
    }
    output = {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "historical_ohlc_gtos_replay_m1_spread_adjusted_fill_replay_v1",
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_M1_SPREAD_ADJUSTED_FILL_REPLAY_ONLY",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": "This M1 spread-adjusted fill replay packet does not complete the 60-hour moonshot objective.",
        "counts": counts,
        "entry_replay_scope_status_counts": dict(sorted(Counter(row["replay_scope_status"] for row in entry_rows).items())),
        "cost_model_fill_status_counts": dict(sorted(Counter(row["m1_fill_status"] for row in cost_model_replay_rows).items())),
        "signature_first_touch_status_counts": dict(sorted(Counter(row["m1_first_touch_status"] for row in signature_rows).items())),
        "terminal_summary": terminal_summary,
        "upstream_source_alignment_counts": source_alignment_result.get("counts", {}),
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "next_same_resource_work": [
            "split fill-bar order-unresolved M1 replay rows with conservative target/stop interval bounds",
            "join M1 spread-adjusted replay families into cost/fill/path synthesis",
            "compare spread-adjusted replay descriptors against near-miss market-entry branches",
            "route partial/source-recheck source-alignment rows into separate repair packets",
        ],
    }

    write_jsonl(ENTRY_REPLAY_PATH, entry_rows)
    write_jsonl(COST_MODEL_REPLAY_PATH, cost_model_replay_rows)
    write_jsonl(SIGNATURE_REPLAY_PATH, signature_rows)
    write_jsonl(FAMILY_REPLAY_PATH, family_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay M1 Spread-Adjusted Fill Replay",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                "This packet replays all source-alignment entries where M1 touches every nonzero spread-adjusted threshold while zero entry remains untouched.",
                "",
                "## Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in counts.items()),
                "",
                "## M1 First-Touch Status",
                "",
                *(f"- `{key}`: `{value}`" for key, value in sorted(Counter(row["m1_first_touch_status"] for row in signature_rows).items())),
                "",
                "## Immediate Work",
                "",
                "- Split fill-bar order-unresolved M1 replay rows with conservative target/stop interval bounds.",
                "- Join M1 spread-adjusted replay families into cost/fill/path synthesis.",
                "- Compare spread-adjusted replay descriptors against near-miss market-entry branches.",
                "- Route partial/source-recheck source-alignment rows into separate repair packets.",
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
