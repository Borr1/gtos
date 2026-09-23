#!/usr/bin/env python3
"""Build vNext runtime rows for SL-beyond-OB outcome-join source repair."""

from __future__ import annotations

import os
import argparse
import hashlib
import json
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


DATE = "2026-05-18"
WAVE_ID = "WAVE_SL_BEYOND_OB_OUTCOME_JOIN_SOURCE_REPAIR_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_sl_beyond_ob_outcome_join_source_repair"
SOURCE_NAME = "gtos_vnext_sl_beyond_ob_outcome_join_source_repair_wave"
RUNTIME_SURFACE = "sl_beyond_ob_outcome_join_source_repair_runtime"

BUILDER_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
MAIN_ORCH48_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "main_orchestrator_24h_full_stack_research_integration_materialization"
)
T3_SL_BEYOND_DIR = REPO_ROOT / "research" / "t3_2_sl_beyond_ob_cross_instrument_audit"

OUTPUT_ROWS = BUILDER_DIR / f"GTOS_VNEXT_SL_BEYOND_OB_OUTCOME_JOIN_SOURCE_REPAIR_RUNTIME_ROWS_{DATE}.jsonl"
OUTPUT_SUMMARY = BUILDER_DIR / f"GTOS_VNEXT_SL_BEYOND_OB_OUTCOME_JOIN_SOURCE_REPAIR_RUNTIME_SUMMARY_{DATE}.json"

SOURCE_PATHS = (
    MAIN_ORCH48_DIR / "build_main_orch48_sl_beyond_ob_logger_activation_2026_05_18.py",
    MAIN_ORCH48_DIR / "build_main_orch48_sl_beyond_ob_outcome_join_2026_05_18.py",
    MAIN_ORCH48_DIR / "MAIN_ORCH48_SL_BEYOND_OB_LOGGER_ACTIVATION_LEDGER_2026-05-18.jsonl",
    MAIN_ORCH48_DIR / "MAIN_ORCH48_SL_BEYOND_OB_LOGGER_ACTIVATION_MANIFEST_2026-05-18.json",
    MAIN_ORCH48_DIR / "MAIN_ORCH48_SL_BEYOND_OB_LOGGER_ACTIVATION_SUMMARY_2026-05-18.json",
    MAIN_ORCH48_DIR / "MAIN_ORCH48_SL_BEYOND_OB_LOGGER_ACTIVATION_VERIFY_RESULT_2026-05-18.json",
    MAIN_ORCH48_DIR / "MAIN_ORCH48_SL_BEYOND_OB_OUTCOME_JOIN_LEDGER_2026-05-18.jsonl",
    MAIN_ORCH48_DIR / "MAIN_ORCH48_SL_BEYOND_OB_OUTCOME_JOIN_MANIFEST_2026-05-18.json",
    MAIN_ORCH48_DIR / "MAIN_ORCH48_SL_BEYOND_OB_OUTCOME_JOIN_SUMMARY_2026-05-18.json",
    MAIN_ORCH48_DIR / "MAIN_ORCH48_SL_BEYOND_OB_OUTCOME_JOIN_VERIFY_RESULT_2026-05-18.json",
    MAIN_ORCH48_DIR / "verify_main_orch48_sl_beyond_ob_logger_activation_2026_05_18.py",
    MAIN_ORCH48_DIR / "verify_main_orch48_sl_beyond_ob_outcome_join_2026_05_18.py",
    T3_SL_BEYOND_DIR / "counterfactual_tables.json",
    T3_SL_BEYOND_DIR / "extract.py",
    T3_SL_BEYOND_DIR / "sl_buffer_universality.json",
)

OUTCOME_JOIN_LEDGER = MAIN_ORCH48_DIR / "MAIN_ORCH48_SL_BEYOND_OB_OUTCOME_JOIN_LEDGER_2026-05-18.jsonl"
LOGGER_ACTIVATION_LEDGER = MAIN_ORCH48_DIR / "MAIN_ORCH48_SL_BEYOND_OB_LOGGER_ACTIVATION_LEDGER_2026-05-18.jsonl"
COUNTERFACTUAL_TABLES = T3_SL_BEYOND_DIR / "counterfactual_tables.json"
SL_BUFFER_UNIVERSALITY = T3_SL_BEYOND_DIR / "sl_buffer_universality.json"
MASTER_LEDGER = BUILDER_DIR / "GTOS_VNEXT_MASTER_INTELLIGENCE_TO_RUNTIME_CONVERSION_LEDGER_2026-05-18.jsonl"

ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "timeframe",
    "market_timeframe",
    "route_session",
    "side",
    "primitive",
    "entry_variant",
    "target_stop_order_class",
    "source_component",
)


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _long_path(path: Path) -> str:
    text = str(path.resolve())
    if os.name == "nt" and len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


@lru_cache(maxsize=None)
def _sha256_file_cached(path_text: str) -> str:
    digest = hashlib.sha256()
    with open(_long_path(Path(path_text)), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_file_cached(str(path))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _path_text(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _read_json(path: Path) -> dict[str, Any]:
    with open(_long_path(path), "r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(_long_path(path), "r", encoding="utf-8-sig", newline="") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _count_nonempty_lines(path: Path) -> int | None:
    suffix = path.suffix.casefold()
    if not path.exists():
        return None
    if suffix == ".json":
        return 1
    if suffix == ".jsonl":
        return len(_read_jsonl(path))
    if suffix in {".md", ".txt"}:
        with open(_long_path(path), "rb") as handle:
            return sum(1 for line in handle if line.strip())
    return None


def _metric(value: float | int | None, *, source_field: str) -> dict[str, Any] | None:
    if value is None:
        return None
    numeric = float(value)
    return {
        "sum": round(numeric, 12),
        "count": 1,
        "mean": round(numeric, 12),
        "positive_rows": 1 if numeric > 0 else 0,
        "negative_rows": 1 if numeric < 0 else 0,
        "zero_rows": 1 if numeric == 0 else 0,
        "match_rows_with_metric": 1,
        "source_field": source_field,
        "source_shape": "scalar",
    }


def _target_stop_class(outcome_status: str, action: str) -> str:
    if "MISSING" in action:
        return "SOURCE_REPAIR_REQUIRED"
    if outcome_status == "ENTRY_TOUCHED_THEN_SL":
        return "STOP_FIRST_PROXY_DOMINANT"
    if outcome_status in {"NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH", "NO_ENTRY_TOUCH_BY_ASOF"}:
        return "NO_FILL_OR_NO_TOUCH"
    if outcome_status == "ENTRY_TOUCHED_UNRESOLVED":
        return "TARGET_STOP_AMBIGUOUS_OR_MIXED"
    return "TARGET_STOP_REFERENCE_CONTEXT"


def _outcome_behavior(row: dict[str, Any]) -> dict[str, str]:
    action = _norm(row.get("sl_beyond_ob_outcome_action"))
    outcome_status = _norm(row.get("outcome_status"))
    if "MISSING" in action:
        return {
            "decision": "MIXED",
            "source_component": "sl_beyond_ob_outcome_capture_gap",
            "source_group": "source_repair_proof",
            "source_role": "sl_beyond_ob_outcome_capture_repair_guard",
            "system_surface": RUNTIME_SURFACE,
            "action_class": "source_repair_guard",
            "r_evidence_class": "SOURCE_REPAIR_FOR_EXACT_R",
            "proxy_r_class": "SOURCE_REPAIR_REQUIRED",
            "runtime_effect_now": "sl_beyond_ob_outcome_capture_source_repair_risk_guard",
        }
    if outcome_status == "ENTRY_TOUCHED_THEN_SL":
        return {
            "decision": "MIXED",
            "source_component": "sl_beyond_ob_pass_adverse_outcome_reference",
            "source_group": "sl_beyond_ob_outcome_reference",
            "source_role": "sl_beyond_ob_pass_adverse_reference_guard",
            "system_surface": RUNTIME_SURFACE,
            "action_class": "sl_beyond_ob_outcome_reference_context",
            "r_evidence_class": "SL_BEYOND_OB_PASS_ADVERSE_OUTCOME_REFERENCE",
            "proxy_r_class": "NEGATIVE_PROXY_R",
            "runtime_effect_now": "sl_beyond_ob_pass_adverse_outcome_context",
        }
    if outcome_status in {"NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH", "NO_ENTRY_TOUCH_BY_ASOF"}:
        return {
            "decision": "MIXED",
            "source_component": "sl_beyond_ob_pass_nofill_outcome_reference",
            "source_group": "sl_beyond_ob_outcome_reference",
            "source_role": "sl_beyond_ob_pass_nofill_reference_guard",
            "system_surface": RUNTIME_SURFACE,
            "action_class": "sl_beyond_ob_outcome_reference_context",
            "r_evidence_class": "SL_BEYOND_OB_PASS_NOFILL_OUTCOME_REFERENCE",
            "proxy_r_class": "NO_FILL_OR_NO_TOUCH_PROXY",
            "runtime_effect_now": "sl_beyond_ob_pass_nofill_outcome_context",
        }
    return {
        "decision": "MIXED",
        "source_component": "sl_beyond_ob_pass_outcome_reference",
        "source_group": "sl_beyond_ob_outcome_reference",
        "source_role": "sl_beyond_ob_pass_reference_guard",
        "system_surface": RUNTIME_SURFACE,
        "action_class": "sl_beyond_ob_outcome_reference_context",
        "r_evidence_class": "SL_BEYOND_OB_PASS_OUTCOME_REFERENCE",
        "proxy_r_class": "MIXED_PROXY_R",
        "runtime_effect_now": "sl_beyond_ob_pass_outcome_reference_context",
    }


def _base_scope(symbol: str, side: str, framework: str, primitive: str) -> dict[str, str]:
    canonical = _norm(symbol)
    return {
        "symbol": canonical,
        "source_symbol": _norm(symbol),
        "market": canonical,
        "symbol_family": resolve_vnext_symbol_family(canonical),
        "timeframe": "M15",
        "market_timeframe": "M15",
        "route_session": "ALL_SESSIONS",
        "side": _norm(side),
        "route_family": _norm(framework),
        "framework": _norm(framework),
        "primitive": _norm(primitive).lower() or "sl_beyond_ob",
        "entry_variant": "sl_beyond_ob_l2",
    }


def _event_scope(row: dict[str, Any]) -> dict[str, str]:
    return {
        key: _norm(row.get(key))
        for key in (
            "symbol",
            "source_symbol",
            "market",
            "symbol_family",
            "timeframe",
            "market_timeframe",
            "route_session",
            "side",
            "route_family",
            "source_component",
            "primitive",
            "entry_variant",
            "target_stop_order_class",
        )
        if _norm(row.get(key))
    }


def _runtime_row_from_outcome(row: dict[str, Any], index: int) -> dict[str, Any]:
    behavior = _outcome_behavior(row)
    scope = _base_scope(
        _norm(row.get("canonical_symbol")) or _norm(row.get("symbol")),
        _norm(row.get("direction")),
        _norm(row.get("framework")),
        _norm(row.get("zone_label")),
    )
    target_stop_order_class = _target_stop_class(
        _norm(row.get("outcome_status")),
        _norm(row.get("sl_beyond_ob_outcome_action")),
    )
    row_id = (
        f"sl_beyond_ob_outcome_join_source_repair:"
        f"{_norm(row.get('sl_beyond_ob_outcome_join_row_id')) or index:0>8}"
    )
    runtime_row = {
        "sl_beyond_ob_outcome_join_source_repair_runtime_row_id": row_id,
        "schema_version": "gtos_vnext_sl_beyond_ob_outcome_join_source_repair_runtime_v1",
        "batch_wave_id": WAVE_ID,
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "decision": behavior["decision"],
        **scope,
        "source_component": behavior["source_component"],
        "source_group": behavior["source_group"],
        "source_role": behavior["source_role"],
        "system_surface": behavior["system_surface"],
        "action_class": behavior["action_class"],
        "r_evidence_class": behavior["r_evidence_class"],
        "proxy_r_class": behavior["proxy_r_class"],
        "runtime_effect_now": behavior["runtime_effect_now"],
        "target_stop_order_class": target_stop_order_class,
        "source_artifact_path": _path_text(OUTCOME_JOIN_LEDGER),
        "source_artifact_sha256": _sha256_file(OUTCOME_JOIN_LEDGER),
        "source_row_id": row.get("sl_beyond_ob_outcome_join_row_id"),
        "source_row_key": row.get("row_key"),
        "source_line_no": row.get("sl_beyond_source_line_no"),
        "join_status": row.get("join_status"),
        "l2_decision": row.get("l2_decision"),
        "l2_reason": row.get("l2_reason"),
        "outcome_status": row.get("outcome_status"),
        "sl_beyond_ob_outcome_action": row.get("sl_beyond_ob_outcome_action"),
        "outcome_candidate_id": row.get("outcome_candidate_id"),
        "candle_minute_utc": row.get("candle_minute_utc"),
        "proposed_entry": row.get("proposed_entry"),
        "proposed_sl": row.get("proposed_sl"),
        "proposed_tp1": row.get("proposed_tp1"),
        "max_favorable_r_from_entry": row.get("max_favorable_r_from_entry"),
        "max_adverse_r_from_entry": row.get("max_adverse_r_from_entry"),
        "strategy_proxy_r": row.get("strategy_proxy_r"),
        "runtime_decision_effect": False,
        "production_change_opened_now": False,
        "gate_config_change_now": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_candidate_use_permitted": False,
        "replay_r_reference_counted_as_new_main_result": False,
    }
    runtime_row["event_scope"] = _event_scope(runtime_row)
    proxy_r = _to_float(row.get("strategy_proxy_r"))
    if proxy_r is not None:
        runtime_row["proxy_score"] = _metric(proxy_r, source_field="strategy_proxy_r")
    runtime_row["effective_n"] = _metric(1, source_field="runtime_row")
    runtime_row["anchor_blank_fields"] = [
        field for field in ANCHOR_FIELDS if not _norm(runtime_row.get(field))
    ]
    return runtime_row


def _runtime_rows_from_activation() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(_read_jsonl(LOGGER_ACTIVATION_LEDGER), start=1):
        row_id = f"sl_beyond_ob_outcome_join_source_repair:logger_activation:{index:04d}"
        runtime_row = {
            "sl_beyond_ob_outcome_join_source_repair_runtime_row_id": row_id,
            "schema_version": "gtos_vnext_sl_beyond_ob_outcome_join_source_repair_runtime_v1",
            "batch_wave_id": WAVE_ID,
            "source_name": SOURCE_NAME,
            "evidence_family": EVIDENCE_FAMILY,
            "decision": "MIXED",
            "symbol": "ALL_MARKETS",
            "source_symbol": "ALL_MARKETS",
            "market": "ALL_MARKETS",
            "symbol_family": "ALL_MARKETS",
            "timeframe": "M15",
            "market_timeframe": "M15",
            "route_session": "ALL_SESSIONS",
            "side": "ALL_SIDES",
            "route_family": "mechanical_ai_selector",
            "primitive": "sl_beyond_ob",
            "entry_variant": "sl_beyond_ob_l2",
            "target_stop_order_class": "SOURCE_REPAIR_REQUIRED",
            "source_component": "sl_beyond_ob_logger_activation",
            "source_group": "sl_beyond_ob_capture_activation",
            "source_role": "sl_beyond_ob_capture_activation_guard",
            "system_surface": RUNTIME_SURFACE,
            "action_class": "sl_beyond_ob_capture_activation_context",
            "r_evidence_class": "SL_BEYOND_OB_CAPTURE_ACTIVATION",
            "proxy_r_class": "MIXED_PROXY_R",
            "runtime_effect_now": "sl_beyond_ob_capture_activation_context",
            "source_artifact_path": _path_text(LOGGER_ACTIVATION_LEDGER),
            "source_artifact_sha256": _sha256_file(LOGGER_ACTIVATION_LEDGER),
            "source_row_id": row.get("activation_row_id"),
            "activation_check": row.get("activation_check"),
            "runtime_halt_active": row.get("runtime_halt_active"),
            "runtime_decision_effect": False,
            "production_change_opened_now": False,
            "gate_config_change_now": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "runtime_candidate_use_permitted": False,
        }
        runtime_row["event_scope"] = _event_scope(runtime_row)
        runtime_row["effective_n"] = _metric(1, source_field="runtime_row")
        runtime_row["anchor_blank_fields"] = [
            field for field in ANCHOR_FIELDS if not _norm(runtime_row.get(field))
        ]
        rows.append(runtime_row)
    return rows


def _runtime_rows_from_counterfactual_tables() -> list[dict[str, Any]]:
    payload = _read_json(COUNTERFACTUAL_TABLES)
    tables = payload.get("tables")
    rows: list[dict[str, Any]] = []
    if not isinstance(tables, dict):
        return rows
    for table_name, table_rows in sorted(tables.items()):
        if not isinstance(table_rows, list):
            continue
        for row in table_rows:
            if not isinstance(row, dict):
                continue
            cat = _norm(row.get("cat"))
            if cat != "TOTAL":
                continue
            n = int(row.get("N") or 0)
            exp = _to_float(row.get("exp"))
            decision = "AVOID" if exp is not None and exp < 0 else "MIXED"
            runtime_row = {
                "sl_beyond_ob_outcome_join_source_repair_runtime_row_id": (
                    "sl_beyond_ob_outcome_join_source_repair:"
                    f"counterfactual:{table_name}"
                ),
                "schema_version": "gtos_vnext_sl_beyond_ob_outcome_join_source_repair_runtime_v1",
                "batch_wave_id": WAVE_ID,
                "source_name": SOURCE_NAME,
                "evidence_family": EVIDENCE_FAMILY,
                "decision": decision,
                "symbol": "XAUUSD",
                "source_symbol": "XAUUSD",
                "market": "XAUUSD",
                "symbol_family": resolve_vnext_symbol_family("XAUUSD"),
                "timeframe": "M15",
                "market_timeframe": "M15",
                "route_session": "ALL_SESSIONS",
                "side": "LONG",
                "route_family": "ob_retest",
                "framework": "ob_retest",
                "primitive": "sl_beyond_ob",
                "entry_variant": "sl_beyond_ob_l2",
                "target_stop_order_class": "STOP_FIRST_PROXY_DOMINANT",
                "source_component": "sl_beyond_ob_rejected_l2_counterfactual",
                "source_group": "sl_beyond_ob_gate_support",
                "source_role": "sl_beyond_ob_rejected_l2_gate_support_guard",
                "system_surface": RUNTIME_SURFACE,
                "action_class": "sl_beyond_ob_gate_support_avoid_filter",
                "r_evidence_class": "SL_BEYOND_OB_REJECTED_L2_NEGATIVE_COUNTERFACTUAL",
                "proxy_r_class": "NEGATIVE_PROXY_R" if decision == "AVOID" else "MIXED_PROXY_R",
                "runtime_effect_now": "sl_beyond_ob_rejected_l2_gate_support_context",
                "counterfactual_table": table_name,
                "counterfactual_category": cat,
                "counterfactual_n": n,
                "counterfactual_win_rate_pct": row.get("WR"),
                "counterfactual_sum_r": row.get("sumR"),
                "counterfactual_expectancy_r": exp,
                "source_bound": bool(n and exp is not None),
                "source_complete": bool(n and exp is not None),
                "source_artifact_path": _path_text(COUNTERFACTUAL_TABLES),
                "source_artifact_sha256": _sha256_file(COUNTERFACTUAL_TABLES),
                "runtime_decision_effect": False,
                "production_change_opened_now": False,
                "gate_config_change_now": False,
                "broker_operation": False,
                "paid_api_or_vendor_call": False,
                "runtime_candidate_use_permitted": False,
            }
            runtime_row["event_scope"] = _event_scope(runtime_row)
            runtime_row["effective_n"] = _metric(n, source_field="counterfactual_n")
            runtime_row["proxy_score"] = _metric(exp, source_field="counterfactual_expectancy_r")
            runtime_row["anchor_blank_fields"] = [
                field for field in ANCHOR_FIELDS if not _norm(runtime_row.get(field))
            ]
            rows.append(runtime_row)
    return rows


def _runtime_row_from_sl_buffer_universality() -> dict[str, Any]:
    payload = _read_json(SL_BUFFER_UNIVERSALITY)
    rows_with_params = int(payload.get("records_with_trade_parameters") or 0)
    zero_count = int(payload.get("sl_buffer_equals_zero") or 0)
    runtime_row = {
        "sl_beyond_ob_outcome_join_source_repair_runtime_row_id": (
            "sl_beyond_ob_outcome_join_source_repair:sl_buffer_universality"
        ),
        "schema_version": "gtos_vnext_sl_beyond_ob_outcome_join_source_repair_runtime_v1",
        "batch_wave_id": WAVE_ID,
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "decision": "MIXED",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market": "XAUUSD",
        "symbol_family": resolve_vnext_symbol_family("XAUUSD"),
        "timeframe": "M15",
        "market_timeframe": "M15",
        "route_session": "ALL_SESSIONS",
        "side": "LONG",
        "route_family": "ob_retest",
        "framework": "ob_retest",
        "primitive": "sl_beyond_ob",
        "entry_variant": "sl_beyond_ob_l2",
        "target_stop_order_class": "SOURCE_REPAIR_REQUIRED",
        "source_component": "sl_beyond_ob_legacy_zero_buffer_source_repair",
        "source_group": "source_repair_proof",
        "source_role": "sl_beyond_ob_zero_buffer_legacy_repair_guard",
        "system_surface": RUNTIME_SURFACE,
        "action_class": "source_repair_guard",
        "r_evidence_class": "SOURCE_REPAIR_FOR_EXACT_R",
        "proxy_r_class": "SOURCE_REPAIR_REQUIRED",
        "runtime_effect_now": "sl_beyond_ob_legacy_zero_buffer_source_repair_guard",
        "records_with_trade_parameters": rows_with_params,
        "sl_buffer_equals_zero": zero_count,
        "sl_buffer_zero_pct": payload.get("percent_zero"),
        "source_artifact_path": _path_text(SL_BUFFER_UNIVERSALITY),
        "source_artifact_sha256": _sha256_file(SL_BUFFER_UNIVERSALITY),
        "runtime_decision_effect": False,
        "production_change_opened_now": False,
        "gate_config_change_now": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_candidate_use_permitted": False,
    }
    runtime_row["event_scope"] = _event_scope(runtime_row)
    runtime_row["effective_n"] = _metric(rows_with_params, source_field="records_with_trade_parameters")
    runtime_row["anchor_blank_fields"] = [
        field for field in ANCHOR_FIELDS if not _norm(runtime_row.get(field))
    ]
    return runtime_row


def build_runtime_rows() -> list[dict[str, Any]]:
    rows = [
        _runtime_row_from_outcome(row, index)
        for index, row in enumerate(_read_jsonl(OUTCOME_JOIN_LEDGER), start=1)
    ]
    rows.extend(_runtime_rows_from_activation())
    rows.extend(_runtime_rows_from_counterfactual_tables())
    rows.append(_runtime_row_from_sl_buffer_universality())
    return rows


def _master_units_by_path() -> dict[str, dict[str, Any]]:
    units: dict[str, dict[str, Any]] = {}
    if not MASTER_LEDGER.exists():
        return units
    source_names = {_path_text(path) for path in SOURCE_PATHS}
    source_names.update(path.name for path in SOURCE_PATHS)
    with open(_long_path(MASTER_LEDGER), "r", encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            path_text = _norm(row.get("source_artifact_path")).replace("\\", "/")
            if path_text in source_names or Path(path_text).name in source_names:
                units[path_text] = row
                units[Path(path_text).name] = row
    return units


def _source_artifacts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_by_path = Counter(str(row.get("source_artifact_path") or "") for row in rows)
    decision_by_path: dict[str, Counter[str]] = {}
    component_by_path: dict[str, Counter[str]] = {}
    for row in rows:
        path = str(row.get("source_artifact_path") or "")
        decision_by_path.setdefault(path, Counter())[str(row.get("decision") or "")] += 1
        component_by_path.setdefault(path, Counter())[str(row.get("source_component") or "")] += 1
    units_by_path = _master_units_by_path()
    artifacts = []
    for source_path in SOURCE_PATHS:
        path_text = _path_text(source_path)
        unit = units_by_path.get(path_text) or units_by_path.get(source_path.name) or {}
        row_count = _count_nonempty_lines(source_path)
        artifacts.append(
            {
                "unit_id": unit.get("intelligence_unit_id", ""),
                "path": path_text,
                "sha256_or_git_blob": unit.get("source_artifact_hash") or _sha256_file(source_path),
                "rows": row_count,
                "row_count_known": row_count is not None,
                "rows_represented": row_count or 0,
                "runtime_rows_read": runtime_by_path.get(path_text, 0),
                "decision_counts": dict(sorted(decision_by_path.get(path_text, Counter()).items())),
                "source_components": sorted(component_by_path.get(path_text, Counter())),
            }
        )
    return artifacts


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_artifacts = _source_artifacts(rows)
    coverage: dict[str, Counter[str]] = {
        "symbols": Counter(),
        "source_symbols": Counter(),
        "markets": Counter(),
        "timeframes": Counter(),
        "sessions": Counter(),
        "sides": Counter(),
        "frameworks": Counter(),
        "target_stop_order_classes": Counter(),
    }
    blank = Counter()
    for row in rows:
        for key, counter_name in (
            ("symbol", "symbols"),
            ("source_symbol", "source_symbols"),
            ("market", "markets"),
            ("timeframe", "timeframes"),
            ("route_session", "sessions"),
            ("side", "sides"),
            ("framework", "frameworks"),
            ("target_stop_order_class", "target_stop_order_classes"),
        ):
            if value := _norm(row.get(key)):
                coverage[counter_name][value] += 1
        blank.update(row.get("anchor_blank_fields") or [])
    return {
        "schema_version": "gtos_vnext_sl_beyond_ob_outcome_join_source_repair_summary_v1",
        "generated_utc": "2026-05-18T00:00:00Z",
        "wave_id": WAVE_ID,
        "batch_wave_id": WAVE_ID,
        "runtime_surface": RUNTIME_SURFACE,
        "evidence_family": EVIDENCE_FAMILY,
        "source_name": SOURCE_NAME,
        "runtime_behavior_target": (
            "SL-beyond-OB outcome-join rows become vNext execution-adjacent "
            "source-repair and gate-support evidence: missing outcome joins "
            "zero risk through the existing source-repair guard, PASS outcome "
            "joins remain scoped context, and historical rejected-L2 "
            "counterfactuals reinforce the existing gate as avoid/support "
            "context with candidate, broker, live, and paid API effects off."
        ),
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": sum(item["rows_represented"] for item in source_artifacts),
        "selected_source_unit_count": len(source_artifacts),
        "wave_source_artifact_count": len(source_artifacts),
        "wave_source_rows_counted": sum(item["rows_represented"] for item in source_artifacts),
        "row_count_unknown_unit_count": sum(1 for item in source_artifacts if not item["row_count_known"]),
        "decision_counts": dict(sorted(Counter(str(row.get("decision") or "") for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(str(row.get("source_component") or "") for row in rows).items())),
        "source_role_counts": dict(sorted(Counter(str(row.get("source_role") or "") for row in rows).items())),
        "source_group_counts": dict(sorted(Counter(str(row.get("source_group") or "") for row in rows).items())),
        "action_class_counts": dict(sorted(Counter(str(row.get("action_class") or "") for row in rows).items())),
        "r_evidence_class_counts": dict(sorted(Counter(str(row.get("r_evidence_class") or "") for row in rows).items())),
        "proxy_r_class_counts": dict(sorted(Counter(str(row.get("proxy_r_class") or "") for row in rows).items())),
        "join_status_counts": dict(sorted(Counter(str(row.get("join_status") or "") for row in rows if row.get("join_status")).items())),
        "l2_decision_counts": dict(sorted(Counter(str(row.get("l2_decision") or "") for row in rows if row.get("l2_decision")).items())),
        "outcome_status_counts": dict(sorted(Counter(str(row.get("outcome_status") or "") for row in rows if row.get("outcome_status")).items())),
        "coverage_counts": {key: dict(sorted(value.items())) for key, value in coverage.items()},
        "blank_anchor_counts": dict(sorted(blank.items())),
        "source_repair_required_rows": sum(
            row.get("source_group") == "source_repair_proof"
            or row.get("action_class") == "source_repair_guard"
            for row in rows
        ),
        "candidate_use_allowed_now_rows": 0,
        "live_effect_rows": 0,
        "broker_operation_rows": 0,
        "paid_api_or_vendor_call_rows": 0,
        "runtime_trading_or_live_broker_effect_rows": 0,
        "runtime_candidate_use_permitted_rows": 0,
        "source_artifacts": source_artifacts,
        "output_rows": _path_text(OUTPUT_ROWS),
    }


def write_outputs() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = build_runtime_rows()
    summary = build_summary(rows)
    BUILDER_DIR.mkdir(parents=True, exist_ok=True)
    with open(_long_path(OUTPUT_ROWS), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    OUTPUT_SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rows, summary


def check_outputs() -> bool:
    expected_rows = build_runtime_rows()
    expected_summary = build_summary(expected_rows)
    if not OUTPUT_ROWS.exists() or not OUTPUT_SUMMARY.exists():
        print("missing generated output", file=sys.stderr)
        return False
    actual_rows = _read_jsonl(OUTPUT_ROWS)
    actual_summary = _read_json(OUTPUT_SUMMARY)
    if actual_rows != expected_rows:
        print("runtime rows differ from regenerated rows", file=sys.stderr)
        return False
    if actual_summary != expected_summary:
        print("runtime summary differs from regenerated summary", file=sys.stderr)
        return False
    print(json.dumps(expected_summary, sort_keys=True))
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        return 0 if check_outputs() else 1
    _, summary = write_outputs()
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
