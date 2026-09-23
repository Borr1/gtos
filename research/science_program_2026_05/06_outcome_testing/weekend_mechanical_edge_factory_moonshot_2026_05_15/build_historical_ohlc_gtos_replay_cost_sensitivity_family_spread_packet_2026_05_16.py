#!/usr/bin/env python3
"""Aggregate cost-sensitive replay families and probe exact spread surfaces."""

from __future__ import annotations

import hashlib
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

SPLIT_RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_RESULT_2026-05-16.json"
CHANGED_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_CHANGED_SIGNATURE_LEDGER_2026-05-16.jsonl"
GRADIENT_REQUIREMENT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_GRADIENT_REQUIREMENT_LEDGER_2026-05-16.jsonl"
UNFILLED_SPLIT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_UNFILLED_LEDGER_2026-05-16.jsonl"
AMBIGUITY_SIGNATURE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPLIT_AMBIGUITY_SIGNATURE_LEDGER_2026-05-16.jsonl"
COST_STATUS_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_PATH_CONTROL_COST_FILL_STATUS_LEDGER_2026-05-16.jsonl"
SLIPPAGE_LOG_PATH = REPO / "shadow_logs/slippage.jsonl"
TICK_README_PATH = REPO / "data/ticks/README.md"

RESULT_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_FAMILY_SPREAD_RESULT_2026-05-16.json"
FAMILY_AGGREGATE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_FAMILY_AGGREGATE_LEDGER_2026-05-16.jsonl"
GRADIENT_EXACT_SPREAD_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_GRADIENT_EXACT_SPREAD_LEDGER_2026-05-16.jsonl"
EXACT_SOURCE_WINDOW_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_EXACT_SPREAD_SOURCE_WINDOW_LEDGER_2026-05-16.jsonl"
SPREAD_STRESS_BOUND_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_SPREAD_STRESS_BOUND_LEDGER_2026-05-16.jsonl"
UNFILLED_RECON_ROUTE_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_UNFILLED_RECON_ROUTE_LEDGER_2026-05-16.jsonl"
BUCKET_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_FAMILY_SPREAD_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_FAMILY_SPREAD_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_FAMILY_SPREAD_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "Historical OHLC GTOS replay cost-sensitivity family/spread packet only. "
    "Rows aggregate cost descriptor families, attempt read-only exact MT5 tick "
    "spread lookup for gradient-sensitive rows, and build stress-bound routes; "
    "no validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or "
    "live behavior change is claimed."
)


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
                yield {"_parse_error": True, "_line_no": line_no, "_source_path": str(path)}


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_manifest() -> tuple[list[dict[str, Any]], str]:
    paths = [
        SPLIT_RESULT_PATH,
        CHANGED_SIGNATURE_PATH,
        GRADIENT_REQUIREMENT_PATH,
        UNFILLED_SPLIT_PATH,
        AMBIGUITY_SIGNATURE_PATH,
        COST_STATUS_PATH,
        SLIPPAGE_LOG_PATH,
        TICK_README_PATH,
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


def seq_from_id(value: str) -> int:
    return int(str(value).rsplit("-", 1)[-1])


def transition_statuses(signature: str) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for part in signature.split("|"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        statuses[key] = value
    return statuses


def family_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["route_candidate_id"],
        row["symbol"],
        row["side"],
        row["entry_variant"],
        row["target_multiple"],
        row["stop_multiple"],
    )


def reference_time_for_cost_status(cost_row: dict[str, Any]) -> str:
    source_time = parse_utc(cost_row["source_time_utc"])
    fill_offset = cost_row.get("fill_offset_bars")
    if fill_offset is None:
        bars_after_source = 1
    else:
        bars_after_source = max(1, int(fill_offset))
    return iso_utc(source_time + timedelta(minutes=15 * bars_after_source))


def spread_value_from_bid_ask(bid: float, ask: float) -> float | None:
    if bid <= 0 or ask <= 0 or ask < bid:
        return None
    return round((ask - bid) * 100.0, 6)


def mt5_probe_windows(
    unique_windows: list[dict[str, Any]],
    generated_at: str,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on local terminal package
        rows = []
        by_key = {}
        for window in unique_windows:
            row = {
                **window,
                "exact_source_status": "MT5_MODULE_UNAVAILABLE_FAIL_CLOSED",
                "mt5_error": f"{type(exc).__name__}: {exc}",
                "ticks_returned": 0,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_SOURCE_WINDOW",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
            rows.append(row)
            by_key[window["source_window_key"]] = row
        return rows, by_key, {"mt5_module_available": False, "mt5_initialize": False, "mt5_error": str(exc)}

    init_ok = bool(mt5.initialize())
    init_error = mt5.last_error()
    terminal_info = mt5.terminal_info() if init_ok else None
    dynamic_source = {
        "mt5_module_available": True,
        "mt5_initialize": init_ok,
        "mt5_last_error": init_error,
        "terminal_name": getattr(terminal_info, "name", None) if terminal_info is not None else None,
        "terminal_company": getattr(terminal_info, "company", None) if terminal_info is not None else None,
        "terminal_data_path": getattr(terminal_info, "data_path", None) if terminal_info is not None else None,
        "read_only_market_data_probe": True,
    }
    rows: list[dict[str, Any]] = []
    by_key: dict[str, dict[str, Any]] = {}
    try:
        if not init_ok:
            for window in unique_windows:
                row = {
                    **window,
                    "exact_source_status": "MT5_INITIALIZE_FAILED_FAIL_CLOSED",
                    "mt5_error": str(init_error),
                    "ticks_returned": 0,
                    "generated_utc": generated_at,
                    "source_manifest_hash": manifest_hash,
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_SOURCE_WINDOW",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
                rows.append(row)
                by_key[window["source_window_key"]] = row
            return rows, by_key, dynamic_source

        symbol_select_cache: dict[str, tuple[bool, Any]] = {}
        for window in unique_windows:
            symbol = window["symbol"]
            if symbol not in symbol_select_cache:
                symbol_select_cache[symbol] = (bool(mt5.symbol_select(symbol, True)), mt5.last_error())
            selected, select_error = symbol_select_cache[symbol]
            base = {
                **window,
                "generated_utc": generated_at,
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_EXACT_SPREAD_SOURCE_WINDOW",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
            if not selected:
                row = {
                    **base,
                    "exact_source_status": "MT5_SYMBOL_SELECT_FAILED_FAIL_CLOSED",
                    "mt5_error": str(select_error),
                    "ticks_returned": 0,
                }
                rows.append(row)
                by_key[window["source_window_key"]] = row
                continue

            reference_time = parse_utc(window["reference_time_utc"])
            extract_start = reference_time - timedelta(seconds=5)
            extract_end = reference_time + timedelta(minutes=15)
            ticks = mt5.copy_ticks_range(symbol, extract_start, extract_end, mt5.COPY_TICKS_ALL)
            if ticks is None:
                row = {
                    **base,
                    "exact_source_status": "MT5_COPY_TICKS_RETURNED_NONE_FAIL_CLOSED",
                    "mt5_error": str(mt5.last_error()),
                    "extract_start_utc": iso_utc(extract_start),
                    "extract_end_utc": iso_utc(extract_end),
                    "ticks_returned": 0,
                }
                rows.append(row)
                by_key[window["source_window_key"]] = row
                continue

            ticks_returned = len(ticks)
            tick_records: list[dict[str, Any]] = []
            first_after: dict[str, Any] | None = None
            first_after_60s_spreads: list[float] = []
            full_window_spreads: list[float] = []
            for tick in ticks:
                tick_ms = int(tick["time_msc"])
                tick_dt = datetime.fromtimestamp(tick_ms / 1000.0, tz=timezone.utc)
                bid = float(tick["bid"])
                ask = float(tick["ask"])
                spread_value = spread_value_from_bid_ask(bid, ask)
                if spread_value is None:
                    continue
                if tick_dt >= reference_time:
                    if first_after is None:
                        first_after = {
                            "first_tick_utc": iso_utc(tick_dt),
                            "first_tick_delta_ms": int((tick_dt - reference_time).total_seconds() * 1000),
                            "first_bid": bid,
                            "first_ask": ask,
                            "first_spread_value": spread_value,
                        }
                    if tick_dt <= reference_time + timedelta(seconds=60):
                        first_after_60s_spreads.append(spread_value)
                    full_window_spreads.append(spread_value)
                tick_records.append({"spread_value": spread_value})

            if ticks_returned == 0:
                row = {
                    **base,
                    "exact_source_status": "MT5_NO_TICKS_IN_REFERENCE_WINDOW_FAIL_CLOSED",
                    "extract_start_utc": iso_utc(extract_start),
                    "extract_end_utc": iso_utc(extract_end),
                    "ticks_returned": 0,
                    "valid_spread_ticks": 0,
                }
            elif first_after is None:
                row = {
                    **base,
                    "exact_source_status": "MT5_TICKS_FOUND_BUT_NONE_AT_OR_AFTER_REFERENCE_FAIL_CLOSED",
                    "extract_start_utc": iso_utc(extract_start),
                    "extract_end_utc": iso_utc(extract_end),
                    "ticks_returned": ticks_returned,
                    "valid_spread_ticks": len(tick_records),
                }
            else:
                row = {
                    **base,
                    **first_after,
                    "exact_source_status": "EXACT_MT5_TICK_SPREAD_AT_REFERENCE_AVAILABLE",
                    "extract_start_utc": iso_utc(extract_start),
                    "extract_end_utc": iso_utc(extract_end),
                    "ticks_returned": ticks_returned,
                    "valid_spread_ticks": len(tick_records),
                    "spread_60s_count": len(first_after_60s_spreads),
                    "spread_60s_min": min(first_after_60s_spreads) if first_after_60s_spreads else None,
                    "spread_60s_median": statistics.median(first_after_60s_spreads) if first_after_60s_spreads else None,
                    "spread_60s_max": max(first_after_60s_spreads) if first_after_60s_spreads else None,
                    "spread_15m_count": len(full_window_spreads),
                    "spread_15m_min": min(full_window_spreads) if full_window_spreads else None,
                    "spread_15m_median": statistics.median(full_window_spreads) if full_window_spreads else None,
                    "spread_15m_max": max(full_window_spreads) if full_window_spreads else None,
                }
            rows.append(row)
            by_key[window["source_window_key"]] = row
    finally:
        if init_ok:
            mt5.shutdown()
    return rows, by_key, dynamic_source


def slippage_source_summary() -> dict[str, Any]:
    rows = [row for row in read_jsonl(SLIPPAGE_LOG_PATH) if not row.get("_parse_error")]
    spread_by_symbol: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        value = row.get("spread_at_request")
        if isinstance(value, (int, float)):
            spread_by_symbol[str(row.get("symbol", "UNKNOWN"))].append(float(value))
    summary = {}
    for symbol, values in sorted(spread_by_symbol.items()):
        summary[symbol] = {
            "rows": len(values),
            "min": min(values),
            "median": statistics.median(values),
            "max": max(values),
        }
    return {"slippage_rows": len(rows), "spread_by_symbol": summary}


def classify_exact_spread(
    exact_spread: float | None,
    median_proxy: float | None,
    static_proxy: float | None,
) -> str:
    if exact_spread is None or median_proxy is None or static_proxy is None:
        return "EXACT_SPREAD_UNAVAILABLE_STRESS_PAIR_ONLY"
    epsilon = 1e-9
    if exact_spread <= median_proxy + epsilon:
        return "EXACT_SPREAD_WITHIN_MEDIAN_PROXY_BOUND_NONSTATIC_DESCRIPTOR"
    if exact_spread <= static_proxy + epsilon:
        return "EXACT_SPREAD_BETWEEN_MEDIAN_AND_STATIC_PROXY_INTERVAL_BOUND"
    return "EXACT_SPREAD_ABOVE_STATIC_PROXY_SUPRA_STATIC_STRESS_REQUIRED"


def update_manifest(outputs: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    existing = [row for row in manifest.get("outputs", []) if row.get("artifact") != RESULT_PATH.name]
    existing.append(
        {
            "artifact": RESULT_PATH.name,
            "category": "historical_ohlc_gtos_replay_cost_sensitivity_family_spread_packet",
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
        "route": "historical_ohlc_gtos_replay_cost_sensitivity_family_spread_packet",
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
    split_result = read_json(SPLIT_RESULT_PATH)
    changed_rows = [row for row in read_jsonl(CHANGED_SIGNATURE_PATH) if not row.get("_parse_error")]
    gradient_rows = [row for row in read_jsonl(GRADIENT_REQUIREMENT_PATH) if not row.get("_parse_error")]
    unfilled_rows = [row for row in read_jsonl(UNFILLED_SPLIT_PATH) if not row.get("_parse_error")]
    ambiguity_rows = [row for row in read_jsonl(AMBIGUITY_SIGNATURE_PATH) if not row.get("_parse_error")]
    cost_status_rows = [row for row in read_jsonl(COST_STATUS_PATH) if not row.get("_parse_error")]

    cost_by_entry_model: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    cost_by_entry_zero: dict[str, dict[str, Any]] = {}
    for row in cost_status_rows:
        cost_by_entry_model[row["entry_variant_id"]][row["cost_model"]] = row
        if row["cost_model"] == "ZERO_COST_CONTROL":
            cost_by_entry_zero[row["entry_variant_id"]] = row

    family: dict[tuple[Any, ...], dict[str, Any]] = {}
    family_status_counters: dict[tuple[Any, ...], Counter[str]] = defaultdict(Counter)
    family_changed_model_counters: dict[tuple[Any, ...], Counter[str]] = defaultdict(Counter)
    for row in changed_rows + unfilled_rows + ambiguity_rows:
        key = family_key(row)
        family.setdefault(
            key,
            {
                "route_candidate_id": key[0],
                "symbol": key[1],
                "side": key[2],
                "entry_variant": key[3],
                "target_multiple": key[4],
                "stop_multiple": key[5],
                "changed_signature_rows": 0,
                "gradient_signature_rows": 0,
                "unfilled_signature_rows": 0,
                "ambiguity_signature_rows": 0,
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_FAMILY_AGGREGATE",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            },
        )
        status = row.get("cost_sensitivity_status", "UNKNOWN")
        family_status_counters[key][status] += 1
        if row in changed_rows:
            family[key]["changed_signature_rows"] += 1
        if status == "SPREAD_PROXY_GRADIENT_DESCRIPTOR_SENSITIVE":
            family[key]["gradient_signature_rows"] += 1
        if row in unfilled_rows:
            family[key]["unfilled_signature_rows"] += 1
        if row in ambiguity_rows:
            family[key]["ambiguity_signature_rows"] += 1
        for model in row.get("changed_models", []):
            family_changed_model_counters[key][model] += 1

    unique_window_by_key: dict[str, dict[str, Any]] = {}
    gradient_enriched_base: list[dict[str, Any]] = []
    for row in gradient_rows:
        models = cost_by_entry_model[row["entry_variant_id"]]
        zero = models.get("ZERO_COST_CONTROL") or cost_by_entry_zero[row["entry_variant_id"]]
        median_row = models.get("SYMBOL_MEDIAN_SPREAD_PROXY", {})
        static_row = models.get("STATIC_CONSERVATIVE_FALLBACK_PROXY", {})
        reference_time = reference_time_for_cost_status(zero)
        source_window_key = f"{row['symbol']}|{reference_time}"
        unique_window_by_key.setdefault(
            source_window_key,
            {
                "source_window_key": source_window_key,
                "symbol": row["symbol"],
                "reference_time_utc": reference_time,
                "source_time_utc": zero["source_time_utc"],
                "reference_time_rule": "source_time_plus_max_one_or_fill_offset_m15_bar",
            },
        )
        statuses = transition_statuses(row["transition_signature"])
        gradient_enriched_base.append(
            {
                **row,
                "source_window_key": source_window_key,
                "source_time_utc": zero["source_time_utc"],
                "reference_time_utc": reference_time,
                "zero_descriptor_status": statuses.get("ZERO_COST_CONTROL"),
                "median_descriptor_status": statuses.get("SYMBOL_MEDIAN_SPREAD_PROXY"),
                "max_descriptor_status": statuses.get("SYMBOL_MAX_SPREAD_PROXY"),
                "static_descriptor_status": statuses.get("STATIC_CONSERVATIVE_FALLBACK_PROXY"),
                "median_spread_proxy_value": median_row.get("spread_proxy_value"),
                "max_spread_proxy_value": models.get("SYMBOL_MAX_SPREAD_PROXY", {}).get("spread_proxy_value"),
                "static_spread_proxy_value": static_row.get("spread_proxy_value"),
                "rolling_median_range": zero.get("rolling_median_range"),
                "fill_timing_status": zero.get("fill_timing_status"),
                "fill_offset_bars": zero.get("fill_offset_bars"),
            }
        )

    source_window_rows, source_by_key, mt5_dynamic_source = mt5_probe_windows(
        sorted(unique_window_by_key.values(), key=lambda item: (item["symbol"], item["reference_time_utc"])),
        generated_at,
        manifest_hash,
    )

    gradient_exact_rows: list[dict[str, Any]] = []
    stress_rows: list[dict[str, Any]] = []
    exact_bucket_counter: Counter[str] = Counter()
    source_status_counter: Counter[str] = Counter()
    for base in gradient_enriched_base:
        source = source_by_key.get(base["source_window_key"], {})
        source_status = source.get("exact_source_status", "EXACT_SOURCE_ROW_MISSING_FAIL_CLOSED")
        source_status_counter[source_status] += 1
        exact_spread = source.get("first_spread_value")
        exact_bucket = classify_exact_spread(
            exact_spread if isinstance(exact_spread, (int, float)) else None,
            base.get("median_spread_proxy_value"),
            base.get("static_spread_proxy_value"),
        )
        exact_bucket_counter[exact_bucket] += 1
        exact_row = {
            **base,
            "exact_spread_source_status": source_status,
            "first_tick_utc": source.get("first_tick_utc"),
            "first_tick_delta_ms": source.get("first_tick_delta_ms"),
            "first_spread_value": exact_spread,
            "spread_60s_median": source.get("spread_60s_median"),
            "spread_15m_median": source.get("spread_15m_median"),
            "exact_spread_proxy_bucket": exact_bucket,
            "source_manifest_hash": manifest_hash,
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_GRADIENT_EXACT_SPREAD",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        gradient_exact_rows.append(exact_row)
        stress_rows.append(
            {
                "cost_sensitivity_signature_id": base["cost_sensitivity_signature_id"],
                "route_candidate_id": base["route_candidate_id"],
                "event_id": base["event_id"],
                "entry_variant_id": base["entry_variant_id"],
                "entry_variant": base["entry_variant"],
                "target_stop_contract_id": base["target_stop_contract_id"],
                "symbol": base["symbol"],
                "side": base["side"],
                "target_multiple": base["target_multiple"],
                "stop_multiple": base["stop_multiple"],
                "source_window_key": base["source_window_key"],
                "exact_spread_source_status": source_status,
                "exact_spread_proxy_bucket": exact_bucket,
                "observed_spread_value": exact_spread,
                "tested_low_spread_proxy_value": base.get("median_spread_proxy_value"),
                "tested_high_spread_proxy_value": base.get("static_spread_proxy_value"),
                "low_spread_descriptor_status": base.get("median_descriptor_status"),
                "high_spread_descriptor_status": base.get("static_descriptor_status"),
                "stress_bound_status": (
                    "EXACT_SPREAD_RESOLVES_TO_LOW_PROXY_DESCRIPTOR_BOUND"
                    if exact_bucket == "EXACT_SPREAD_WITHIN_MEDIAN_PROXY_BOUND_NONSTATIC_DESCRIPTOR"
                    else "EXACT_SPREAD_REQUIRES_LOW_HIGH_DESCRIPTOR_INTERVAL_OR_SUPRA_STATIC_STRESS"
                ),
                "next_same_resource_action": (
                    "use exact MT5 tick spread row as cost-input bracket and carry low/high descriptor pair"
                    if source_status == "EXACT_MT5_TICK_SPREAD_AT_REFERENCE_AVAILABLE"
                    else "run MT5/acquisition retry or use low/high proxy descriptor stress pair without waiting"
                ),
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_SPREAD_STRESS_BOUND",
                "safe_flags": SAFE_FLAGS,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )

    family_rows: list[dict[str, Any]] = []
    gradient_bucket_by_family: dict[tuple[Any, ...], Counter[str]] = defaultdict(Counter)
    for row in gradient_exact_rows:
        gradient_bucket_by_family[family_key(row)][row["exact_spread_proxy_bucket"]] += 1
    for key, row in sorted(family.items(), key=lambda item: tuple(str(part) for part in item[0])):
        status_counts = dict(sorted(family_status_counters[key].items()))
        changed_model_counts = dict(sorted(family_changed_model_counters[key].items()))
        exact_bucket_counts = dict(sorted(gradient_bucket_by_family[key].items()))
        family_rows.append(
            {
                **row,
                "cost_sensitivity_status_counts": status_counts,
                "changed_model_counts": changed_model_counts,
                "gradient_exact_spread_bucket_counts": exact_bucket_counts,
                "family_route_status": (
                    "HAS_GRADIENT_EXACT_SPREAD_PACKET"
                    if row["gradient_signature_rows"]
                    else "NO_GRADIENT_ROWS_IN_FAMILY"
                ),
            }
        )

    unfilled_group: dict[tuple[Any, ...], Counter[str]] = defaultdict(Counter)
    unfilled_example: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in unfilled_rows:
        key = (
            row["route_candidate_id"],
            row["symbol"],
            row["side"],
            row["entry_variant"],
            row["target_multiple"],
            row["stop_multiple"],
        )
        unfilled_group[key][row["unfilled_split_status"]] += 1
        unfilled_example.setdefault(key, row)
    unfilled_recon_rows: list[dict[str, Any]] = []
    for seq, (key, counter) in enumerate(sorted(unfilled_group.items(), key=lambda item: tuple(str(part) for part in item[0])), 1):
        example = unfilled_example[key]
        zero = cost_by_entry_zero.get(example["entry_variant_id"], {})
        unfilled_recon_rows.append(
            {
                "unfilled_recon_route_id": f"OHLC-GTOS-COST-SENS-UNFILLED-RECON-{seq:05d}",
                "route_candidate_id": key[0],
                "symbol": key[1],
                "side": key[2],
                "entry_variant": key[3],
                "target_multiple": key[4],
                "stop_multiple": key[5],
                "unfilled_signature_rows": sum(counter.values()),
                "unfilled_status_counts": dict(sorted(counter.items())),
                "source_time_utc": zero.get("source_time_utc"),
                "reference_time_utc": reference_time_for_cost_status(zero) if zero else None,
                "fill_timing_status": zero.get("fill_timing_status"),
                "tick_reconstruction_status": "MT5_TICK_OR_M1_TOUCH_PROBE_NEXT_SAME_RESOURCE_ROUTE",
                "next_same_resource_action": "probe unique unfilled entry windows with MT5 ticks/M1 bars and compare against M15 no-fill envelope",
                "source_manifest_hash": manifest_hash,
                "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_UNFILLED_RECON_ROUTE",
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
                    "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_FAMILY_SPREAD_BUCKET",
                    "safe_flags": SAFE_FLAGS,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )

    add_bucket("family_route_status", Counter(row["family_route_status"] for row in family_rows))
    add_bucket("gradient_exact_spread_proxy_bucket", exact_bucket_counter)
    add_bucket("exact_spread_source_status", source_status_counter)
    add_bucket("gradient_symbol", Counter(row["symbol"] for row in gradient_exact_rows))
    add_bucket("gradient_entry_variant", Counter(row["entry_variant"] for row in gradient_exact_rows))
    add_bucket(
        "gradient_route__exact_spread_proxy_bucket",
        Counter((row["route_candidate_id"], row["exact_spread_proxy_bucket"]) for row in gradient_exact_rows),
    )
    add_bucket("unfilled_recon_entry_variant", Counter(row["entry_variant"] for row in unfilled_recon_rows))
    add_bucket("unfilled_recon_symbol", Counter(row["symbol"] for row in unfilled_recon_rows))

    question_rows = [
        {
            "question_id": "OHLC-GTOS-COST-SENS-FAMILY-SPREAD-QUESTION-001",
            "question": "Which cost-sensitive families are isolated uniform proxy shifts versus gradient rows with exact tick spread evidence?",
            "row_count": len(family_rows),
            "next_same_resource_action": "use family aggregate rows to split uniform, gradient, ambiguity, and unfilled route families without top-N pruning",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_FAMILY_SPREAD_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-COST-SENS-FAMILY-SPREAD-QUESTION-002",
            "question": "Do exact MT5 tick spreads resolve gradient-sensitive rows below the static conservative proxy?",
            "row_count": len(gradient_exact_rows),
            "next_same_resource_action": "carry exact-spread buckets into descriptor stress/reconstruction and re-run path rows where exact spread crosses tested proxy brackets",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_FAMILY_SPREAD_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "question_id": "OHLC-GTOS-COST-SENS-FAMILY-SPREAD-QUESTION-003",
            "question": "Which cost-invariant unfilled retest-limit families should be probed with MT5 tick/M1 touch reconstruction next?",
            "row_count": len(unfilled_recon_rows),
            "next_same_resource_action": "probe every unique unfilled entry/time route with MT5 ticks or M1 bars, then join to no-fill geometry controls",
            "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_FAMILY_SPREAD_QUESTION",
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]

    counts = {
        "ambiguity_input_rows": len(ambiguity_rows),
        "bucket_rows": len(bucket_rows),
        "changed_input_rows": len(changed_rows),
        "exact_source_window_rows": len(source_window_rows),
        "family_aggregate_rows": len(family_rows),
        "gradient_exact_spread_rows": len(gradient_exact_rows),
        "gradient_input_rows": len(gradient_rows),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(manifest_rows),
        "spread_stress_bound_rows": len(stress_rows),
        "unfilled_input_rows": len(unfilled_rows),
        "unfilled_recon_route_rows": len(unfilled_recon_rows),
    }
    output = {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "historical_ohlc_gtos_replay_cost_sensitivity_family_spread_packet_v1",
        "generated_utc": generated_at,
        "evidence_class": "HISTORICAL_OHLC_GTOS_REPLAY_COST_SENSITIVITY_FAMILY_SPREAD_ONLY",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": "This family/spread packet does not complete the 60-hour moonshot objective.",
        "counts": counts,
        "family_route_status_counts": dict(Counter(row["family_route_status"] for row in family_rows)),
        "gradient_exact_spread_proxy_bucket_counts": dict(sorted(exact_bucket_counter.items())),
        "exact_spread_source_status_counts": dict(sorted(source_status_counter.items())),
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "dynamic_source_summary": mt5_dynamic_source,
        "slippage_source_summary": slippage_source_summary(),
        "upstream_split_counts": split_result.get("counts", {}),
        "next_same_resource_work": [
            "use exact-spread buckets to re-run exact-cost path controls for gradient-sensitive rows",
            "probe unfilled retest-limit families with MT5 tick/M1 touch reconstruction",
            "join exact spread and unfilled reconstruction to same-M15 ambiguity/no-fill geometry controls",
        ],
    }

    write_jsonl(FAMILY_AGGREGATE_PATH, family_rows)
    write_jsonl(GRADIENT_EXACT_SPREAD_PATH, gradient_exact_rows)
    write_jsonl(EXACT_SOURCE_WINDOW_PATH, source_window_rows)
    write_jsonl(SPREAD_STRESS_BOUND_PATH, stress_rows)
    write_jsonl(UNFILLED_RECON_ROUTE_PATH, unfilled_recon_rows)
    write_jsonl(BUCKET_PATH, bucket_rows)
    write_jsonl(QUESTION_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# Historical OHLC GTOS Replay Cost-Sensitivity Family Spread Packet",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                "This packet aggregates changed cost-sensitive signatures by route/entry/target-stop family, probes read-only MT5 ticks for every gradient-sensitive reference window, and emits stress-bound rows for every gradient row.",
                "",
                "## Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in counts.items()),
                "",
                "## Exact Spread Buckets",
                "",
                *(f"- `{key}`: `{value}`" for key, value in sorted(exact_bucket_counter.items())),
                "",
                "## Immediate Work",
                "",
                "- Re-run exact-cost path controls for gradient-sensitive rows using the extracted spread brackets.",
                "- Probe cost-invariant unfilled retest-limit families with MT5 tick/M1 touch reconstruction.",
                "- Join exact-spread and unfilled reconstruction to same-M15 ambiguity and no-fill geometry controls.",
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
