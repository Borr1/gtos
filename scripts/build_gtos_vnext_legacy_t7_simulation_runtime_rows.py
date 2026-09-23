#!/usr/bin/env python3
"""Build vNext runtime rows from legacy T7 production simulation evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
DATE = "2026-05-18"
MASTER_LEDGER_PATH = (
    ROUTE_DIR
    / f"GTOS_VNEXT_MASTER_INTELLIGENCE_TO_RUNTIME_CONVERSION_LEDGER_{DATE}.jsonl"
)
BATCH_LEDGER_PATH = (
    ROUTE_DIR
    / f"GTOS_VNEXT_BATCH_RUNTIME_CONVERSION_LEDGER_{DATE}.jsonl"
)
ROWS_PATH = (
    ROUTE_DIR
    / f"GTOS_VNEXT_LEGACY_T7_SIMULATION_FRICTION_RUNTIME_ROWS_{DATE}.jsonl"
)
SUMMARY_PATH = (
    ROUTE_DIR
    / f"GTOS_VNEXT_LEGACY_T7_SIMULATION_FRICTION_RUNTIME_SUMMARY_{DATE}.json"
)

WAVE_ID = "WAVE_LEGACY_T7_PRODUCTION_SIMULATION_FRICTION_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_legacy_t7_simulation_friction"
SOURCE_NAME = "gtos_vnext_legacy_t7_simulation_friction_wave"
RUNTIME_SURFACE = "legacy_t7_simulation_friction_runtime"
OPEN_STATES = {"NOT_STARTED", "REPAIR_NEEDED_WITH_EXACT_FIELD_SOURCE_CODE_ACTION"}
OUTPUT_NAMES = {ROWS_PATH.name, SUMMARY_PATH.name}
SELECTED_SOURCE_WAVES = {
    WAVE_ID,
    "WAVE_LEGACY_V2_V3_PAPER_LIVE_FRICTION_RUNTIME_MERGE",
    "WAVE_GENERAL_ROW_BEARING_RUNTIME_TRANSLATION",
}
SOURCE_PATH_FAMILY_TOKENS = (
    "/a2_v2_active_backtest/",
    "/f3_backtest_2026-04-24/",
    "/instrument_expansion_2026-04-25/",
    "/lira_ab_backtest/",
    "/t3_1_eurusd_nas100_validation_2026-04-19/",
    "/t7_live_simulation/",
)
SESSION_CANONICAL = {
    "tokyo": "tokyo_kz",
    "tokyo_kz": "tokyo_kz",
    "london": "london_core",
    "london_core": "london_core",
    "ny": "ny_core",
    "new_york": "ny_core",
    "ny_core": "ny_core",
}
SYMBOL_FAMILY_BY_SYMBOL = {
    "EURUSD": "EURUSD_6E_FAMILY",
    "GBPUSD": "GBPUSD_6B_FAMILY",
    "GER40": "GER40_FDAX_FAMILY",
    "NAS100": "NAS100_NQ_FAMILY",
    "UK100": "UK100_FTSE_FAMILY",
    "USDJPY": "USDJPY_6J_FAMILY",
    "XAGUSD": "XAGUSD_SILVER_FAMILY",
    "XAUUSD": "XAUUSD_GC_FAMILY",
}


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8-sig") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    rows.append(payload)
    except OSError:
        return []
    return rows


def _source_category(path_text: str) -> str:
    name = Path(path_text).name.casefold()
    if name in {item.casefold() for item in OUTPUT_NAMES}:
        return ""
    if name == "t7_live_simulation_report.md":
        return "report"
    if name.endswith("_t7_simulation.json"):
        return "symbol_json"
    if name == "all_results.json":
        return "all_results"
    if name == "candidate_features_log.jsonl":
        return "candidate_features_log"
    return ""


def _is_target_source_path(path_text: str) -> bool:
    normalized_path = path_text.casefold().replace("\\", "/")
    normalized = f"/{normalized_path}"
    return bool(_source_category(path_text)) and any(
        token in normalized for token in SOURCE_PATH_FAMILY_TOKENS
    )


def _iter_batch_unit_dispositions() -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for wave in _read_jsonl(BATCH_LEDGER_PATH):
        wave_id = str(wave.get("wave_id") or "")
        dispositions = wave.get("unit_dispositions")
        if not isinstance(dispositions, list):
            continue
        for unit in dispositions:
            if not isinstance(unit, dict):
                continue
            payload = dict(unit)
            payload.setdefault("batch_wave_id", wave_id)
            units.append(payload)
    return units


def _selected_source_units() -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    units = _iter_batch_unit_dispositions()
    if not units:
        units = _read_jsonl(MASTER_LEDGER_PATH)
    for row in units:
        path_text = str(row.get("source_artifact_path") or "")
        if not _is_target_source_path(path_text):
            continue
        wave_id = str(row.get("batch_wave_id") or "")
        evidence_family = str(row.get("evidence_family") or "")
        conversion_state = str(row.get("conversion_state") or "")
        if (
            wave_id in SELECTED_SOURCE_WAVES
            or conversion_state in OPEN_STATES
            or evidence_family == EVIDENCE_FAMILY
        ):
            selected.append(row)
    return selected


def _sha256_file(path: Path) -> str:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return ""


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, str):
        value = value.strip().removesuffix("R").removesuffix("%")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int:
    numeric = _to_float(value)
    return int(numeric) if numeric is not None else 0


def _metric(sum_value: float | None, count: float | None, *, source_field: str) -> dict[str, Any]:
    if sum_value is None:
        return {
            "sum": None,
            "mean": None,
            "match_rows_with_metric": 0,
            "positive_rows": 0,
            "negative_rows": 0,
            "zero_rows": 0,
            "source_field": source_field,
        }
    metric_count = count if count and count > 0 else 1.0
    return {
        "sum": round(float(sum_value), 6),
        "mean": round(float(sum_value) / metric_count, 6),
        "match_rows_with_metric": metric_count,
        "positive_rows": 1 if sum_value > 0 else 0,
        "negative_rows": 1 if sum_value < 0 else 0,
        "zero_rows": 1 if sum_value == 0 else 0,
        "source_field": source_field,
    }


def _canonical_session(value: Any) -> str:
    text = str(value or "").strip().casefold().replace(" ", "_")
    return SESSION_CANONICAL.get(text, text)


def _infer_symbol(path: Path, payload: dict[str, Any] | None = None) -> str:
    if isinstance(payload, dict) and payload.get("symbol"):
        return str(payload["symbol"]).upper()
    for part in reversed(path.parts):
        upper = part.upper()
        for symbol in SYMBOL_FAMILY_BY_SYMBOL:
            if symbol in upper:
                return symbol
    return "UNKNOWN"


def _result_is_candidate(row: dict[str, Any]) -> bool:
    if str(row.get("decision") or "").upper() == "CANDIDATE":
        return True
    return bool(row.get("trade_parameters"))


def _result_is_l2_reject(row: dict[str, Any]) -> bool:
    if str(row.get("decision") or "").upper() == "REJECTED_L2":
        return True
    if row.get("l2_passed") is False:
        return True
    return bool(row.get("l2_reason"))


def _result_is_limit_block(row: dict[str, Any]) -> bool:
    if str(row.get("decision") or "").upper() in {"BLOCKED_LIMIT", "LIMIT_BLOCK"}:
        return True
    block_reason = str(row.get("block_reason") or "").casefold()
    return "max_" in block_reason or "limit" in block_reason or "blocked" in block_reason


def _result_is_final_trade(row: dict[str, Any]) -> bool:
    return _result_is_candidate(row) and not _result_is_l2_reject(row) and not _result_is_limit_block(row)


def _parse_json_results(path: Path) -> dict[str, Any]:
    payload = _read_json(path)
    if not isinstance(payload, dict):
        return {}
    results = payload.get("results")
    if not isinstance(results, list):
        return {}

    session_counts: Counter[str] = Counter()
    side_counts: Counter[str] = Counter()
    final_session_counts: Counter[str] = Counter()
    final_side_counts: Counter[str] = Counter()
    outcome_counts: Counter[str] = Counter()
    raw_candidates = 0
    l2_rejects = 0
    limit_blocks = 0
    final_trades = 0
    unfilled = 0
    total_r = 0.0
    r_rows = 0
    api_calls = 0
    total_cost = _to_float(payload.get("total_cost")) or 0.0

    for result in results:
        if not isinstance(result, dict):
            continue
        session = _canonical_session(result.get("kill_zone") or result.get("route_session"))
        if session:
            session_counts[session] += 1
        side = str(result.get("direction") or "").upper()
        if side in {"LONG", "SHORT"}:
            side_counts[side] += 1
        cost = _to_float(result.get("cost"))
        if cost and cost > 0:
            api_calls += 1
            if not payload.get("total_cost"):
                total_cost += cost
        if _result_is_candidate(result):
            raw_candidates += 1
        if _result_is_l2_reject(result):
            l2_rejects += 1
        if _result_is_limit_block(result):
            limit_blocks += 1
        if _result_is_final_trade(result):
            final_trades += 1
            if session:
                final_session_counts[session] += 1
            if side in {"LONG", "SHORT"}:
                final_side_counts[side] += 1
            outcome = str(result.get("outcome") or "").upper()
            if outcome:
                outcome_counts[outcome] += 1
            if outcome == "UNFILLED":
                unfilled += 1
            r_value = _to_float(result.get("r_multiple"))
            if r_value is not None:
                total_r += r_value
                r_rows += 1

    evaluated = _to_int(payload.get("n_evaluated")) or len(results)
    return {
        "parsed_status": "parsed_json_results",
        "symbol": _infer_symbol(path, payload),
        "start": payload.get("start", ""),
        "end": payload.get("end", ""),
        "evaluated_candles": evaluated,
        "api_call_count": api_calls,
        "api_cost_usd": round(total_cost, 4),
        "raw_candidate_count": raw_candidates,
        "l2_reject_count": l2_rejects,
        "limit_block_count": limit_blocks,
        "final_trade_count": final_trades,
        "resolved_trade_count": r_rows,
        "unfilled_count": unfilled,
        "win_count": int(outcome_counts.get("WIN") or 0),
        "loss_count": int(outcome_counts.get("LOSS") or 0),
        "total_r": round(total_r, 6),
        "expectancy_per_resolved_trade": round(total_r / r_rows, 6) if r_rows else None,
        "session_counts": dict(sorted(session_counts.items())),
        "side_counts": dict(sorted(side_counts.items())),
        "final_session_counts": dict(sorted(final_session_counts.items())),
        "final_side_counts": dict(sorted(final_side_counts.items())),
        "outcome_counts": dict(sorted(outcome_counts.items())),
    }


TABLE_ROW_RE = re.compile(
    r"^\|\s*(?P<symbol>[A-Z0-9_]+)\s*\|\s*(?P<kz>\d+)\s*\|\s*(?P<api>\d+)\s*\|"
    r"\s*(?P<cand>\d+)\s*\|\s*(?P<l2>\d+)\s*\|\s*(?P<limit>\d+)\s*\|"
    r"\s*(?P<trades>\d+)\s*\|.*?\|\s*(?P<wins>\d+)\s*\|\s*(?P<losses>\d+)\s*\|.*?\|"
    r"\s*(?P<total_r>[-+0-9.]+)R\s*\|\s*(?P<expectancy>[-+0-9.]+)R\s*\|"
)


def _parse_report(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError:
        return {}
    for line in text.splitlines():
        match = TABLE_ROW_RE.match(line.strip())
        if not match:
            continue
        data = match.groupdict()
        total_r = _to_float(data.get("total_r")) or 0.0
        trades = _to_int(data.get("trades"))
        return {
            "parsed_status": "parsed_report_table",
            "symbol": str(data.get("symbol") or _infer_symbol(path)).upper(),
            "start": "",
            "end": "",
            "evaluated_candles": _to_int(data.get("kz")),
            "api_call_count": _to_int(data.get("api")),
            "api_cost_usd": None,
            "raw_candidate_count": _to_int(data.get("cand")),
            "l2_reject_count": _to_int(data.get("l2")),
            "limit_block_count": _to_int(data.get("limit")),
            "final_trade_count": trades,
            "resolved_trade_count": _to_int(data.get("wins")) + _to_int(data.get("losses")),
            "unfilled_count": max(0, trades - _to_int(data.get("wins")) - _to_int(data.get("losses"))),
            "win_count": _to_int(data.get("wins")),
            "loss_count": _to_int(data.get("losses")),
            "total_r": round(total_r, 6),
            "expectancy_per_resolved_trade": round(total_r / trades, 6) if trades else None,
            "session_counts": {},
            "side_counts": {},
            "final_session_counts": {},
            "final_side_counts": {},
            "outcome_counts": {},
        }
    return {}


def _group_units(units: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for unit in units:
        path_text = str(unit.get("source_artifact_path") or "")
        grouped[Path(path_text).parent.as_posix()].append(unit)
    return dict(sorted(grouped.items()))


def _parse_group(group_path: str, units: list[dict[str, Any]]) -> dict[str, Any]:
    paths_by_category: dict[str, list[Path]] = defaultdict(list)
    for unit in units:
        path_text = str(unit.get("source_artifact_path") or "")
        category = _source_category(path_text)
        paths_by_category[category].append(REPO_ROOT / path_text)

    preferred_path = None
    for category in ("symbol_json", "all_results", "report"):
        if paths_by_category.get(category):
            preferred_path = sorted(paths_by_category[category])[0]
            break

    parsed: dict[str, Any] = {}
    if preferred_path:
        if _source_category(_rel(preferred_path)) in {"symbol_json", "all_results"}:
            parsed = _parse_json_results(preferred_path)
        if not parsed:
            report_paths = paths_by_category.get("report") or []
            if report_paths:
                parsed = _parse_report(sorted(report_paths)[0])

    if not parsed:
        parsed = {
            "parsed_status": "unparsed_zero_or_report_only",
            "symbol": _infer_symbol(Path(group_path)),
            "start": "",
            "end": "",
            "evaluated_candles": 0,
            "api_call_count": 0,
            "api_cost_usd": None,
            "raw_candidate_count": 0,
            "l2_reject_count": 0,
            "limit_block_count": 0,
            "final_trade_count": 0,
            "resolved_trade_count": 0,
            "unfilled_count": 0,
            "win_count": 0,
            "loss_count": 0,
            "total_r": 0.0,
            "expectancy_per_resolved_trade": None,
            "session_counts": {},
            "side_counts": {},
            "final_session_counts": {},
            "final_side_counts": {},
            "outcome_counts": {},
        }

    parsed["group_path"] = group_path
    parsed["source_unit_ids"] = [
        str(unit.get("unit_id") or unit.get("intelligence_unit_id") or "")
        for unit in units
    ]
    parsed["source_paths"] = [str(unit.get("source_artifact_path") or "") for unit in units]
    parsed["source_rows_represented"] = sum(
        int(unit.get("row_count") or 0) for unit in units if unit.get("row_count") is not None
    )
    parsed["source_unit_count"] = len(units)
    return parsed


def _decision_for_group(group: dict[str, Any]) -> tuple[str, str, str, str, str]:
    resolved = int(group.get("resolved_trade_count") or 0)
    expectancy = _to_float(group.get("expectancy_per_resolved_trade"))
    if resolved >= 3 and expectancy is not None and expectancy > 0:
        return (
            "FOLLOW",
            "legacy_t7_positive_simulation",
            "legacy_t7_simulation_follow_pressure",
            "legacy_t7_simulation_follow_context",
            "LEGACY_T7_PRODUCTION_FAITHFUL_POSITIVE_REPLAY",
        )
    if resolved >= 3 and expectancy is not None and expectancy <= 0:
        return (
            "AVOID",
            "legacy_t7_negative_simulation",
            "legacy_t7_simulation_avoid_filter",
            "legacy_t7_simulation_avoid_guard",
            "LEGACY_T7_PRODUCTION_FAITHFUL_NEGATIVE_REPLAY",
        )
    return (
        "MIXED",
        "legacy_t7_context_simulation",
        "legacy_t7_simulation_context_guard",
        "legacy_t7_simulation_context_guard",
        "LEGACY_T7_PRODUCTION_FAITHFUL_CONTEXT",
    )


def _runtime_row(index: int, group: dict[str, Any]) -> dict[str, Any]:
    decision, component, action_class, source_role, r_class = _decision_for_group(group)
    symbol = str(group.get("symbol") or "UNKNOWN").upper()
    expectancy = _to_float(group.get("expectancy_per_resolved_trade"))
    total_r = _to_float(group.get("total_r")) or 0.0
    resolved = int(group.get("resolved_trade_count") or 0)
    raw_candidates = int(group.get("raw_candidate_count") or 0)
    l2_rejects = int(group.get("l2_reject_count") or 0)
    limit_blocks = int(group.get("limit_block_count") or 0)
    api_calls = int(group.get("api_call_count") or 0)
    evaluated = int(group.get("evaluated_candles") or 0)
    friction_count = l2_rejects + limit_blocks
    friction_rate = friction_count / raw_candidates if raw_candidates else None
    r_metrics = {
        "cost_adjusted_simulated_r": _metric(total_r, resolved, source_field="t7_total_r"),
        "effective_n": _metric(float(resolved), 1.0, source_field="resolved_trade_count"),
        "proxy_score": _metric(expectancy, 1.0, source_field="expectancy_per_resolved_trade"),
        "fill_friction_count": _metric(float(friction_count), 1.0, source_field="l2_reject_plus_limit_block_count"),
        "api_call_count": _metric(float(api_calls), 1.0, source_field="api_call_count"),
    }
    row = {
        "schema_version": "gtos_vnext_legacy_t7_simulation_friction_runtime_v1",
        "legacy_t7_simulation_friction_runtime_row_id": f"LEGACY_T7_SIM_FRICTION_{index:04d}",
        "row_type": "gtos_vnext_legacy_t7_simulation_friction_runtime_row",
        "batch_wave_id": WAVE_ID,
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "source_component": component,
        "source_group": "legacy_t7_production_faithful_simulation",
        "source_role": source_role,
        "system_surface": RUNTIME_SURFACE,
        "review_action": f"DEFAULT_OFF_{decision}_SCORER_REVIEW",
        "action_class": action_class,
        "r_evidence_class": r_class,
        "runtime_effect_now": "shadow_legacy_t7_simulation_context",
        "candidate_use_allowed_now": False,
        "runtime_candidate_use_permitted": False,
        "live_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "symbol": symbol,
        "source_symbol": symbol,
        "market": symbol,
        "symbol_family": SYMBOL_FAMILY_BY_SYMBOL.get(symbol, ""),
        "timeframe": "M15",
        "market_timeframe": "M15",
        "route_session": "ALL_SESSIONS",
        "side": "",
        "event_scope": {
            "symbol": symbol,
            "source_symbol": symbol,
            "market": symbol,
            "timeframe": "M15",
            "market_timeframe": "M15",
            "route_session": "ALL_SESSIONS",
            "source_component": component,
            "action_class": action_class,
        },
        "source_rows_represented": group.get("source_rows_represented", 0),
        "source_unit_count": group.get("source_unit_count", 0),
        "source_unit_ids": group.get("source_unit_ids", []),
        "source_artifact": group.get("source_paths", [""])[0],
        "declared_origin_artifact": group.get("source_paths", [""])[0],
        "drill_through_path": group.get("source_paths", [""])[0],
        "source_artifact_paths": group.get("source_paths", []),
        "source_group_path": group.get("group_path", ""),
        "parsed_status": group.get("parsed_status", ""),
        "simulation_start": group.get("start", ""),
        "simulation_end": group.get("end", ""),
        "evaluated_candles": evaluated,
        "api_call_count": api_calls,
        "api_cost_usd": group.get("api_cost_usd"),
        "raw_candidate_count": raw_candidates,
        "l2_reject_count": l2_rejects,
        "limit_block_count": limit_blocks,
        "final_trade_count": int(group.get("final_trade_count") or 0),
        "resolved_trade_count": resolved,
        "unfilled_count": int(group.get("unfilled_count") or 0),
        "win_count": int(group.get("win_count") or 0),
        "loss_count": int(group.get("loss_count") or 0),
        "total_r": round(total_r, 6),
        "expectancy_per_resolved_trade": expectancy,
        "l2_reject_ratio": round(l2_rejects / raw_candidates, 6) if raw_candidates else None,
        "limit_block_ratio": round(limit_blocks / raw_candidates, 6) if raw_candidates else None,
        "fill_friction_ratio": round(friction_rate, 6) if friction_rate is not None else None,
        "api_call_ratio": round(api_calls / evaluated, 6) if evaluated else None,
        "source_session_counts": group.get("session_counts", {}),
        "source_side_counts": group.get("side_counts", {}),
        "source_final_session_counts": group.get("final_session_counts", {}),
        "source_final_side_counts": group.get("final_side_counts", {}),
        "source_outcome_counts": group.get("outcome_counts", {}),
        "r_metric_traces": r_metrics,
        "r_metrics": r_metrics,
    }
    if row["symbol_family"]:
        row["event_scope"]["symbol_family"] = row["symbol_family"]
    return row


def _counter_from_rows(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        value = row.get(field)
        if value not in (None, ""):
            counts[str(value)] += 1
    return dict(sorted(counts.items()))


def _nested_counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        payload = row.get(field)
        if isinstance(payload, dict):
            for key, value in payload.items():
                counts[str(key)] += int(value or 0)
    return dict(sorted(counts.items()))


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    fields = (
        "entry_variant",
        "framework",
        "horizon_id",
        "market",
        "market_timeframe",
        "primitive",
        "route_family",
        "route_session",
        "side",
        "source_symbol",
        "symbol",
        "target_stop_order_class",
        "timeframe",
    )
    return {
        field: sum(1 for row in rows if row.get(field) in (None, ""))
        for field in fields
        if any(row.get(field) in (None, "") for row in rows)
    }


def build_payloads() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    units = _selected_source_units()
    grouped = _group_units(units)
    groups = [_parse_group(group_path, group_units) for group_path, group_units in grouped.items()]
    runtime_rows = [_runtime_row(index, group) for index, group in enumerate(groups, start=1)]
    source_artifacts = []
    for unit in units:
        path_text = str(unit.get("source_artifact_path") or "")
        path = REPO_ROOT / path_text
        source_artifacts.append(
            {
                "unit_id": unit.get("unit_id") or unit.get("intelligence_unit_id", ""),
                "path": path_text,
                "hash": unit.get("source_artifact_hash") or _sha256_file(path),
                "hash_algorithm": unit.get("source_artifact_hash_algorithm", "git_blob"),
                "row_count": unit.get("row_count"),
                "category": _source_category(path_text),
                "source_group_path": Path(path_text).parent.as_posix(),
            }
        )

    decision_counts = Counter(str(row.get("review_action", "")).split("_")[2] for row in runtime_rows)
    source_rows_represented = sum(
        int(unit.get("row_count") or 0) for unit in units if unit.get("row_count") is not None
    )
    summary = {
        "schema_version": "gtos_vnext_legacy_t7_simulation_friction_summary_v1",
        "batch_wave_id": WAVE_ID,
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "runtime_surface": RUNTIME_SURFACE,
        "runtime_row_count": len(runtime_rows),
        "runtime_source_rows_represented": source_rows_represented,
        "wave_source_rows_counted": source_rows_represented,
        "selected_open_unit_count": len(units),
        "selected_source_unit_count": len(units),
        "wave_source_artifact_count": len(source_artifacts),
        "row_count_unknown_unit_count": sum(1 for unit in units if unit.get("row_count") is None),
        "run_group_count": len(groups),
        "parsed_run_group_count": sum(1 for group in groups if group.get("parsed_status") != "unparsed_zero_or_report_only"),
        "unparsed_run_group_count": sum(1 for group in groups if group.get("parsed_status") == "unparsed_zero_or_report_only"),
        "decision_counts": dict(sorted(decision_counts.items())),
        "source_component_counts": _counter_from_rows(runtime_rows, "source_component"),
        "action_class_counts": _counter_from_rows(runtime_rows, "action_class"),
        "r_evidence_class_counts": _counter_from_rows(runtime_rows, "r_evidence_class"),
        "blank_anchor_counts": _blank_anchor_counts(runtime_rows),
        "coverage_counts": {
            "symbols": _counter_from_rows(runtime_rows, "symbol"),
            "source_symbols": _counter_from_rows(runtime_rows, "source_symbol"),
            "markets": _counter_from_rows(runtime_rows, "market"),
            "timeframes": _counter_from_rows(runtime_rows, "timeframe"),
            "market_timeframes": _counter_from_rows(runtime_rows, "market_timeframe"),
            "runtime_sessions": _counter_from_rows(runtime_rows, "route_session"),
            "source_sessions": _nested_counter(runtime_rows, "source_session_counts"),
            "source_final_sessions": _nested_counter(runtime_rows, "source_final_session_counts"),
            "sides": _counter_from_rows(runtime_rows, "side"),
            "source_sides": _nested_counter(runtime_rows, "source_side_counts"),
            "source_final_sides": _nested_counter(runtime_rows, "source_final_side_counts"),
        },
        "aggregate_metrics_by_symbol": _aggregate_by_symbol(runtime_rows),
        "candidate_use_allowed_now_rows": sum(1 for row in runtime_rows if row.get("candidate_use_allowed_now")),
        "runtime_candidate_use_permitted_rows": sum(1 for row in runtime_rows if row.get("runtime_candidate_use_permitted")),
        "live_effect_rows": sum(1 for row in runtime_rows if row.get("live_effect")),
        "broker_operation_rows": sum(1 for row in runtime_rows if row.get("broker_operation")),
        "paid_api_or_vendor_call_rows": sum(1 for row in runtime_rows if row.get("paid_api_or_vendor_call")),
        "runtime_trading_or_live_broker_effect_rows": sum(
            1
            for row in runtime_rows
            if row.get("candidate_use_allowed_now")
            or row.get("runtime_candidate_use_permitted")
            or row.get("live_effect")
            or row.get("broker_operation")
            or row.get("paid_api_or_vendor_call")
        ),
        "source_artifacts": source_artifacts,
        "runtime_behavior_target": (
            "Legacy production-faithful T7 simulation rows become scoped "
            "symbol-level paper/live friction context: positive resolved "
            "expectancy adds FOLLOW pressure, negative resolved expectancy "
            "adds AVOID pressure, and underpowered/unparsed groups stay MIXED "
            "with candidate, broker, live, and paid API effects disabled."
        ),
    }
    return runtime_rows, summary


def _aggregate_by_symbol(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("symbol") or "UNKNOWN")].append(row)
    output: dict[str, dict[str, Any]] = {}
    for symbol, items in sorted(grouped.items()):
        resolved = sum(int(row.get("resolved_trade_count") or 0) for row in items)
        total_r = sum(float(row.get("total_r") or 0.0) for row in items)
        output[symbol] = {
            "run_groups": len(items),
            "evaluated_candles": sum(int(row.get("evaluated_candles") or 0) for row in items),
            "api_call_count": sum(int(row.get("api_call_count") or 0) for row in items),
            "raw_candidate_count": sum(int(row.get("raw_candidate_count") or 0) for row in items),
            "l2_reject_count": sum(int(row.get("l2_reject_count") or 0) for row in items),
            "limit_block_count": sum(int(row.get("limit_block_count") or 0) for row in items),
            "final_trade_count": sum(int(row.get("final_trade_count") or 0) for row in items),
            "resolved_trade_count": resolved,
            "win_count": sum(int(row.get("win_count") or 0) for row in items),
            "loss_count": sum(int(row.get("loss_count") or 0) for row in items),
            "total_r": round(total_r, 6),
            "expectancy_per_resolved_trade": round(total_r / resolved, 6) if resolved else None,
        }
    return output


def write_payloads(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    ROWS_PATH.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _existing_rows() -> list[dict[str, Any]]:
    return _read_jsonl(ROWS_PATH)


def _existing_summary() -> dict[str, Any]:
    payload = _read_json(SUMMARY_PATH)
    return payload if isinstance(payload, dict) else {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if generated artifacts are stale.")
    args = parser.parse_args(argv)
    rows, summary = build_payloads()
    if args.check:
        if rows != _existing_rows() or summary != _existing_summary():
            print("legacy T7 simulation runtime artifacts are stale", file=sys.stderr)
            return 1
        print(
            f"legacy T7 simulation runtime artifacts ok: rows={len(rows)} "
            f"source_units={summary['selected_open_unit_count']} "
            f"source_rows={summary['runtime_source_rows_represented']}"
        )
        return 0
    write_payloads(rows, summary)
    print(
        f"wrote {ROWS_PATH} ({len(rows)} rows) and {SUMMARY_PATH} "
        f"from {summary['selected_open_unit_count']} source units"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
