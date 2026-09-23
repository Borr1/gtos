#!/usr/bin/env python3
"""Build vNext runtime rows for Main Orch24 action completeness and residual-R evidence."""

from __future__ import annotations

import os
import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
SOURCE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "main_orchestrator_24h_full_stack_research_integration_materialization"
)
DATE = "2026-05-18"
WAVE_ID = "WAVE_MAIN_ORCH24_ACTION_COMPLETENESS_RESIDUAL_R_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_main_orch24_action_completeness_residual_r_runtime"
SOURCE_NAME = "gtos_vnext_main_orch24_action_completeness_residual_r_runtime_wave"
RUNTIME_SURFACE = "main_orch24_action_completeness_residual_r_runtime"

OUTPUT_ROWS = (
    ROUTE_DIR
    / f"GTOS_VNEXT_MAIN_ORCH24_ACTION_COMPLETENESS_RESIDUAL_R_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / f"GTOS_VNEXT_MAIN_ORCH24_ACTION_COMPLETENESS_RESIDUAL_R_RUNTIME_SUMMARY_{DATE}.json"
)

LEDGER_SOURCES = (
    (
        "action_decision_completeness",
        "MAIN_ORCH24_ACTION_DECISION_COMPLETENESS_LEDGER_2026-05-17.jsonl",
    ),
    (
        "full_opportunity_preservation_repair",
        "MAIN_ORCH24_ACTION_AFTER_FULL_OPPORTUNITY_PRESERVATION_REPAIR_LEDGER_2026-05-17.jsonl",
    ),
    (
        "source_provenance_reference_repair",
        "MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_REFERENCE_REPAIR_LEDGER_2026-05-17.jsonl",
    ),
    (
        "source_provenance_context_decision",
        "MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_CONTEXT_DECISION_LEDGER_2026-05-17.jsonl",
    ),
    (
        "action_after_residual_numeric_r_resolution",
        "MAIN_ORCH24_ACTION_AFTER_RESIDUAL_NUMERIC_R_RESOLUTION_LEDGER_2026-05-17.jsonl",
    ),
    (
        "residual_numeric_r_field_resolution",
        "MAIN_ORCH24_RESIDUAL_NUMERIC_R_FIELD_RESOLUTION_LEDGER_2026-05-17.jsonl",
    ),
)

SELECTED_SOURCE_ARTIFACTS = (
    "build_main_orchestrator_action_after_full_opportunity_preservation_repair_2026_05_17.py",
    "build_main_orchestrator_action_after_source_provenance_context_decision_2026_05_17.py",
    "build_main_orchestrator_action_after_source_provenance_reference_repair_2026_05_17.py",
    "build_main_orchestrator_action_decision_completeness_materialization_2026_05_17.py",
    "build_main_orchestrator_residual_numeric_r_field_resolution_2026_05_17.py",
    "MAIN_ORCH24_ACTION_AFTER_FULL_OPPORTUNITY_PRESERVATION_REPAIR_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_ACTION_AFTER_FULL_OPPORTUNITY_PRESERVATION_REPAIR_OUTPUT_MANIFEST_2026-05-17.json",
    "MAIN_ORCH24_ACTION_AFTER_FULL_OPPORTUNITY_PRESERVATION_REPAIR_SUMMARY_2026-05-17.json",
    "MAIN_ORCH24_ACTION_AFTER_FULL_OPPORTUNITY_PRESERVATION_REPAIR_VERIFICATION_RESULT_2026-05-17.json",
    "MAIN_ORCH24_ACTION_AFTER_RESIDUAL_NUMERIC_R_RESOLUTION_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_CONTEXT_DECISION_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_CONTEXT_DECISION_OUTPUT_MANIFEST_2026-05-17.json",
    "MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_CONTEXT_DECISION_SUMMARY_2026-05-17.json",
    "MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_CONTEXT_DECISION_VERIFICATION_RESULT_2026-05-17.json",
    "MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_REFERENCE_REPAIR_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_REFERENCE_REPAIR_OUTPUT_MANIFEST_2026-05-17.json",
    "MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_REFERENCE_REPAIR_SUMMARY_2026-05-17.json",
    "MAIN_ORCH24_ACTION_AFTER_SOURCE_PROVENANCE_REFERENCE_REPAIR_VERIFICATION_RESULT_2026-05-17.json",
    "MAIN_ORCH24_ACTION_DECISION_COMPLETENESS_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_ACTION_DECISION_COMPLETENESS_OUTPUT_MANIFEST_2026-05-17.json",
    "MAIN_ORCH24_ACTION_DECISION_COMPLETENESS_SUMMARY_2026-05-17.json",
    "MAIN_ORCH24_ACTION_DECISION_COMPLETENESS_VERIFICATION_RESULT_2026-05-17.json",
    "MAIN_ORCH24_RESIDUAL_NUMERIC_R_FIELD_RESOLUTION_LEDGER_2026-05-17.jsonl",
    "MAIN_ORCH24_RESIDUAL_NUMERIC_R_FIELD_RESOLUTION_OUTPUT_MANIFEST_2026-05-17.json",
    "MAIN_ORCH24_RESIDUAL_NUMERIC_R_FIELD_RESOLUTION_SUMMARY_2026-05-17.json",
    "MAIN_ORCH24_RESIDUAL_NUMERIC_R_FIELD_RESOLUTION_VERIFY_RESULT_2026-05-17.json",
    "verify_main_orchestrator_action_after_full_opportunity_preservation_repair_2026_05_17.py",
    "verify_main_orchestrator_action_after_source_provenance_context_decision_2026_05_17.py",
    "verify_main_orchestrator_action_after_source_provenance_reference_repair_2026_05_17.py",
    "verify_main_orchestrator_action_decision_completeness_materialization_2026_05_17.py",
    "verify_main_orchestrator_residual_numeric_r_field_resolution_2026_05_17.py",
)

ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "timeframe",
    "market_timeframe",
    "route_session",
    "route_family",
    "primitive",
    "side",
    "entry_variant",
    "target_stop_order_class",
    "source_component",
)

SOURCE_REPAIR_ACTIONS = {
    "SOURCE_REPAIR",
    "PRESERVE_REQUIREMENT",
    "DOWNGRADE_OR_REPAIR",
    "KEEP_REPAIR_OR_AVOID",
}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _float(value: Any) -> float | None:
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


def _path_text(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _source_path(name: str) -> Path:
    return SOURCE_DIR / name


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(_long_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


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


def _source_row_count(path: Path) -> int:
    suffix = path.suffix.casefold()
    if suffix == ".jsonl":
        return len(_read_jsonl(path))
    if suffix == ".json":
        return 1
    with open(_long_path(path), "r", encoding="utf-8", errors="ignore") as handle:
        return sum(1 for line in handle if line.strip())


def _candidate_session(symbol: str, candidate_id: Any, row: dict[str, Any]) -> str:
    session = _norm(row.get("session")).casefold()
    if session and session != "unknown":
        return {
            "ny": "ny_core",
            "london": "london_core",
            "tokyo": "tokyo_kz",
        }.get(session, session)
    text = _norm(candidate_id)
    match = re.search(r"T(\d{2}):(\d{2})", text)
    if not match:
        return "ALL_SESSIONS"
    minute = int(match.group(1)) * 60 + int(match.group(2))
    symbol = _norm(symbol).upper()
    if symbol in {"GBPJPY", "USDJPY"}:
        if 0 <= minute < 180:
            return "tokyo_kz"
        if 420 <= minute < 570:
            return "london_core"
        if 780 <= minute < 930:
            return "ny_core"
    if symbol == "GBPUSD":
        if 420 <= minute < 720:
            return "london_core"
        if 780 <= minute < 930:
            return "ny_core"
    if symbol in {"XAUUSD", "XAGUSD"}:
        if 420 <= minute < 630:
            return "london_core"
        if 780 <= minute < 1020:
            return "ny_core"
    if symbol in {"US30", "US30_CASH"}:
        if 480 <= minute < 630:
            return "london_core"
        if 810 <= minute < 960:
            return "ny_core"
    if symbol == "NAS100" and 780 <= minute < 1020:
        return "ny_core"
    return "off_core_session"


def _metric(value: float | int | None, *, source_field: str) -> dict[str, Any] | None:
    if value is None:
        return None
    value = float(value)
    return {
        "sum": round(value, 12),
        "count": 1,
        "mean": round(value, 12),
        "positive_rows": 1 if value > 0 else 0,
        "negative_rows": 1 if value < 0 else 0,
        "zero_rows": 1 if value == 0 else 0,
        "match_rows_with_metric": 1,
        "source_field": source_field,
        "source_shape": "scalar",
    }


def _proxy_value(row: dict[str, Any]) -> tuple[float | None, str]:
    for field in (
        "exact_r",
        "after_proxy_r",
        "selected_shift_proxy_r",
        "selected_shift_r",
        "proxy_r_delta",
        "materialized_proxy_r",
        "field_value",
        "before_proxy_r",
    ):
        value = _float(row.get(field))
        if value is not None:
            return value, field
    return None, ""


def _proxy_class(value: float | None, decision: str) -> str:
    if value is None:
        if decision == "AVOID":
            return "NEGATIVE_PROXY_R"
        if decision == "FOLLOW":
            return "POSITIVE_PROXY_R"
        return "MIXED_PROXY_R"
    if value > 0:
        return "POSITIVE_PROXY_R"
    if value < 0:
        return "NEGATIVE_PROXY_R"
    return "FLAT_PROXY_R"


def _residual_numeric_behavior(row: dict[str, Any]) -> dict[str, Any]:
    status = _norm(row.get("resolution_status")).upper()
    action = _norm(row.get("action_class")).upper()
    branch = _norm(row.get("branch_decision")).upper()
    if (
        "ADVERSE_AVOID" in status
        or "REDESIGN" in status
        or "FVG_BOUNDS" in status
        or "REDESIGN" in action
        or "REDESIGN" in branch
    ):
        component = "main_orch24_residual_numeric_r_redesign_guard"
        if "ADVERSE_AVOID" in status:
            component = "main_orch24_residual_numeric_r_adverse_avoid_guard"
        elif "DISTANCE" in status:
            component = "main_orch24_residual_numeric_r_distance_context"
        return {
            "decision": "AVOID",
            "source_component": component,
            "source_role": component,
            "source_group": "main_orch24_residual_numeric_r_redesign_filter",
            "system_surface": "main_orch24_residual_numeric_r_redesign_guard",
            "action_class": f"{component}_avoid_filter",
            "r_evidence_class": "MAIN_ORCH24_ACTION_COMPLETENESS_RESIDUAL_R_REDESIGN_AVOID_FILTER",
        }
    if "MATERIALIZED" in status or "MERGED" in status or action == "IMPLEMENT_DEFAULT_OFF":
        return {
            "decision": "FOLLOW",
            "source_component": "main_orch24_residual_numeric_r_materialized_context",
            "source_role": "main_orch24_residual_numeric_r_materialized_context",
            "source_group": "main_orch24_residual_numeric_r_materialized_context",
            "system_surface": "main_orch24_residual_numeric_r_materialized_follow",
            "action_class": "main_orch24_residual_numeric_r_materialized_follow_pressure",
            "r_evidence_class": "MAIN_ORCH24_ACTION_COMPLETENESS_RESIDUAL_R_DEFAULT_OFF_FOLLOW_PRESSURE",
        }
    return {
        "decision": "MIXED",
        "source_component": "main_orch24_residual_numeric_r_context",
        "source_role": "main_orch24_residual_numeric_r_context",
        "source_group": "main_orch24_residual_numeric_r_context",
        "system_surface": "main_orch24_residual_numeric_r_context",
        "action_class": "main_orch24_residual_numeric_r_context",
        "r_evidence_class": "MAIN_ORCH24_ACTION_COMPLETENESS_RESIDUAL_R_CONTEXT",
    }


def _action_behavior(row: dict[str, Any]) -> dict[str, Any]:
    action = _norm(row.get("action_class")).upper()
    implementation = _norm(row.get("implementation_decision")).upper()
    branch = _norm(row.get("branch_decision")).upper()
    coverage = _norm(row.get("coverage_status")).upper()
    data_state = _norm(row.get("data_requirement_state")).upper()
    surface = _norm(row.get("source_capture_surface")) or _norm(row.get("primitive_family"))
    surface_upper = surface.upper()

    if (
        action in SOURCE_REPAIR_ACTIONS
        or "SOURCE_REQUIREMENT" in implementation
        or "PRESERVE_SOURCE" in branch
        or "MISSING_REQUIRED" in data_state
        or "REQUIRES" in data_state
    ):
        return {
            "decision": "MIXED",
            "source_component": "main_orch24_action_completeness_source_repair_requirement",
            "source_role": "main_orch24_action_completeness_source_repair_requirement_guard",
            "source_group": "main_orch24_action_completeness_source_repair",
            "system_surface": "main_orch24_action_completeness_source_repair_guard",
            "action_class": "main_orch24_action_completeness_source_repair_requirement",
            "r_evidence_class": "MAIN_ORCH24_ACTION_COMPLETENESS_SOURCE_REPAIR_REQUIRED",
            "source_acquisition_required": True,
            "source_acquisition_kind": "main_orch24_action_completeness_source_or_exact_r_repair_required",
        }

    if action == "KILL" or implementation.startswith("KILL") or "KILLED" in coverage:
        component = "main_orch24_action_completeness_kill_guard"
        if "FVG_OB" in implementation or "FVG_OB" in branch:
            component = "main_orch24_action_completeness_fvg_ob_kill_guard"
        elif "FAR_MISS" in implementation or "NO_FILL" in implementation or "NO_FILL" in branch:
            component = "main_orch24_action_completeness_nofill_far_miss_kill_guard"
        elif "SWING" in implementation:
            component = "main_orch24_action_completeness_swing_unprotected_kill_guard"
        return {
            "decision": "AVOID",
            "source_component": component,
            "source_role": component,
            "source_group": "main_orch24_action_completeness_kill_filter",
            "system_surface": "main_orch24_action_completeness_kill_guard",
            "action_class": f"{component}_avoid_filter",
            "r_evidence_class": "MAIN_ORCH24_ACTION_COMPLETENESS_KILL_AVOID_FILTER",
        }

    if action == "REDESIGN" or "REDESIGN" in implementation or "REDESIGN" in branch:
        component = "main_orch24_action_completeness_redesign_guard"
        if "SOURCE_PROVENANCE" in implementation or "SOURCE_PROVENANCE" in branch:
            component = "main_orch24_action_completeness_source_provenance_redesign_guard"
        elif "OPPORTUNITY" in implementation or "OPPORTUNITY" in branch:
            component = "main_orch24_action_completeness_opportunity_preservation_redesign_guard"
        elif "PENDING" in implementation or "PENDING" in branch:
            component = "main_orch24_action_completeness_pending_redesign_guard"
        elif "ENTRY_OFFSET" in implementation or "050R" in implementation or "FAR_MISS" in implementation:
            component = "main_orch24_action_completeness_entry_offset_redesign_guard"
        return {
            "decision": "AVOID",
            "source_component": component,
            "source_role": component,
            "source_group": "main_orch24_action_completeness_redesign_filter",
            "system_surface": "main_orch24_action_completeness_redesign_guard",
            "action_class": f"{component}_avoid_filter",
            "r_evidence_class": "MAIN_ORCH24_ACTION_COMPLETENESS_REDESIGN_AVOID_FILTER",
        }

    if action in {"IMPLEMENT_DEFAULT_OFF", "KEEP_WITH_SOURCE_DERIVATION", "UPGRADE_CHALLENGER_REVIEW"}:
        component = "main_orch24_action_completeness_default_off_follow"
        if "SOURCE_PROVENANCE" in implementation or "SOURCE_PROVENANCE" in branch:
            component = "main_orch24_action_completeness_source_provenance_follow"
        elif "ENTRY_OFFSET" in implementation or "050R" in implementation or "FAR_MISS" in implementation:
            component = "main_orch24_action_completeness_entry_offset_follow"
        elif "FVG" in implementation or "FVG" in surface_upper:
            component = "main_orch24_action_completeness_fvg_structural_follow"
        return {
            "decision": "FOLLOW",
            "source_component": component,
            "source_role": component,
            "source_group": "main_orch24_action_completeness_default_off_follow",
            "system_surface": "main_orch24_action_completeness_default_off_follow",
            "action_class": f"{component}_pressure",
            "r_evidence_class": "MAIN_ORCH24_ACTION_COMPLETENESS_DEFAULT_OFF_FOLLOW_PRESSURE",
        }

    if action == "KEEP":
        return {
            "decision": "MIXED",
            "source_component": "main_orch24_action_completeness_keep_context",
            "source_role": "main_orch24_action_completeness_keep_context",
            "source_group": "main_orch24_action_completeness_keep_context",
            "system_surface": "main_orch24_action_completeness_context",
            "action_class": "main_orch24_action_completeness_keep_context",
            "r_evidence_class": "MAIN_ORCH24_ACTION_COMPLETENESS_CONTEXT",
        }

    return {
        "decision": "MIXED",
        "source_component": "main_orch24_action_completeness_context",
        "source_role": "main_orch24_action_completeness_context",
        "source_group": "main_orch24_action_completeness_context",
        "system_surface": "main_orch24_action_completeness_context",
        "action_class": "main_orch24_action_completeness_context",
        "r_evidence_class": "MAIN_ORCH24_ACTION_COMPLETENESS_CONTEXT",
    }


def _behavior(row: dict[str, Any], source_label: str) -> dict[str, Any]:
    if source_label == "residual_numeric_r_field_resolution":
        return _residual_numeric_behavior(row)
    return _action_behavior(row)


def _scope(row: dict[str, Any], behavior: dict[str, Any]) -> dict[str, str]:
    symbol = _norm(row.get("symbol"))
    primitive = _norm(row.get("primitive_family")) or _norm(row.get("field_name"))
    side = _norm(row.get("side")) or "ALL_SIDES"
    entry = (
        _norm(row.get("source_capture_surface"))
        or _norm(row.get("primitive_family"))
        or _norm(row.get("field_name"))
        or "unknown_entry"
    )
    target_stop = (
        _norm(row.get("data_requirement_state"))
        or _norm(row.get("selected_shift_status"))
        or _norm(row.get("resolution_status"))
        or _norm(row.get("coverage_status"))
        or "unknown_target_stop"
    )
    scope = {
        "timeframe": "M15",
        "market_timeframe": "M15",
        "route_session": _candidate_session(symbol, row.get("candidate_id"), row),
        "route_family": "main_orch24_action_completeness_residual_r",
        "primitive": primitive,
        "source_component": behavior["source_component"],
        "side": side,
        "entry_variant": entry,
        "target_stop_order_class": target_stop,
    }
    if symbol:
        scope.update(
            {
                "symbol": symbol,
                "source_symbol": symbol,
                "market": symbol,
                "symbol_family": resolve_vnext_symbol_family(symbol),
            }
        )
    return {key: value for key, value in scope.items() if value}


def _runtime_row(
    *,
    source_label: str,
    source_path: Path,
    source_sha: str,
    line_no: int,
    row: dict[str, Any],
) -> dict[str, Any]:
    behavior = _behavior(row, source_label)
    scope = _scope(row, behavior)
    proxy, proxy_field = _proxy_value(row)
    proxy_class = _proxy_class(proxy, behavior["decision"])
    metrics = {
        key: value
        for key, value in {
            "proxy_score": _metric(proxy, source_field=proxy_field) if proxy_field else None,
            "cost_adjusted_simulated_r": _metric(proxy, source_field=proxy_field) if proxy_field else None,
            "proxy_r_delta": _metric(_float(row.get("proxy_r_delta")), source_field="proxy_r_delta"),
        }.items()
        if value is not None
    }
    row_hash = _sha256_payload(row)
    runtime = {
        "schema_version": "gtos_vnext_main_orch24_action_completeness_residual_r_runtime_row_v1",
        "row_type": "gtos_vnext_main_orch24_action_completeness_residual_r_runtime_row",
        "main_orch24_action_completeness_residual_r_runtime_row_id": (
            f"main_orch24_action_completeness_residual_r:{source_label}:{line_no}:{row_hash[:16]}"
        ),
        "row_key": f"main_orch24_action_completeness_residual_r:{source_label}:{line_no}:{row_hash[:16]}",
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "batch_wave_id": WAVE_ID,
        "source_artifact": _path_text(source_path),
        "source_file_sha256": source_sha,
        "source_line_no": line_no,
        "source_row_id": row.get("row_id"),
        "candidate_id": row.get("candidate_id"),
        "source_payload_hash": row_hash,
        "source_label": source_label,
        "source_group": behavior["source_group"],
        "source_role": behavior["source_role"],
        "source_component": behavior["source_component"],
        "system_surface": behavior["system_surface"],
        "action_class": behavior["action_class"],
        "review_action": behavior["decision"],
        "decision": behavior["decision"],
        "r_evidence_class": behavior["r_evidence_class"],
        "proxy_r_class": proxy_class,
        "event_scope": scope,
        "source_bound": bool(scope.get("source_component")),
        "candidate_use_allowed_now": False,
        "runtime_candidate_use_permitted": behavior["decision"] == "FOLLOW",
        "fresh_moonshot_cp_evidence_override_allowed": False,
        "legacy_cannot_override_fresher_cp280_cp281_cp282": True,
        "live_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
        "runtime_effect_now": "main_orch24_action_completeness_residual_r_shadow_runtime",
        "source_acquisition_required": behavior.get("source_acquisition_required", False),
        "source_acquisition_kind": behavior.get("source_acquisition_kind"),
        "original_action_class": row.get("action_class"),
        "implementation_decision": row.get("implementation_decision"),
        "branch_decision": row.get("branch_decision"),
        "coverage_status": row.get("coverage_status"),
        "data_requirement_state": row.get("data_requirement_state"),
        "source_capture_surface": row.get("source_capture_surface"),
        "primitive_family": row.get("primitive_family"),
        "source_plate": row.get("source_plate"),
        "strategy_id": row.get("strategy_id"),
        "resolution_status": row.get("resolution_status"),
        "field_name": row.get("field_name"),
        "field_value": _float(row.get("field_value")),
        "materialized_proxy_r": _float(row.get("materialized_proxy_r")),
        "after_proxy_r": _float(row.get("after_proxy_r")),
        "before_proxy_r": _float(row.get("before_proxy_r")),
        "proxy_r_delta": _float(row.get("proxy_r_delta")),
        "exact_r": _float(row.get("exact_r")),
        "r_metrics": metrics,
    }
    runtime.update(scope)
    return {key: value for key, value in runtime.items() if value not in (None, "", {}, [])}


def build_rows() -> list[dict[str, Any]]:
    runtime_rows: list[dict[str, Any]] = []
    for source_label, filename in LEDGER_SOURCES:
        path = _source_path(filename)
        source_sha = _sha256_file(path)
        for line_no, row in enumerate(_read_jsonl(path), start=1):
            runtime_rows.append(
                _runtime_row(
                    source_label=source_label,
                    source_path=path,
                    source_sha=source_sha,
                    line_no=line_no,
                    row=row,
                )
            )
    return runtime_rows


def _coverage_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {
        "symbols": dict(Counter(row.get("symbol") for row in rows if row.get("symbol"))),
        "source_symbols": dict(Counter(row.get("source_symbol") for row in rows if row.get("source_symbol"))),
        "markets": dict(Counter(row.get("market") for row in rows if row.get("market"))),
        "timeframes": dict(Counter(row.get("timeframe") for row in rows if row.get("timeframe"))),
        "sessions": dict(Counter(row.get("route_session") for row in rows if row.get("route_session"))),
        "sides": dict(Counter(row.get("side") for row in rows if row.get("side"))),
        "entry_variants": dict(Counter(row.get("entry_variant") for row in rows if row.get("entry_variant"))),
        "target_stop_order_classes": dict(
            Counter(row.get("target_stop_order_class") for row in rows if row.get("target_stop_order_class"))
        ),
    }


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(1 for row in rows if not _norm(row.get(field)))
        for field in ANCHOR_FIELDS
    }


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected_paths = [_source_path(name) for name in SELECTED_SOURCE_ARTIFACTS]
    source_artifacts = [
        {
            "path": _path_text(path),
            "name": path.name,
            "hash": _git_blob_sha1(path),
            "hash_algorithm": "git_blob",
            "row_count": _source_row_count(path),
            "source_batch_wave_id": WAVE_ID,
        }
        for path in selected_paths
    ]
    return {
        "schema_version": "gtos_vnext_main_orch24_action_completeness_residual_r_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "runtime_surface": RUNTIME_SURFACE,
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": sum(int(row.get("source_rows_represented") or 1) for row in rows),
        "wave_source_rows_counted": sum(item["row_count"] for item in source_artifacts),
        "selected_open_unit_count": len(source_artifacts),
        "row_count_unknown_unit_count": 0,
        "source_artifacts": source_artifacts,
        "source_rows_by_label": dict(Counter(row["source_label"] for row in rows)),
        "decision_counts": dict(Counter(row["decision"] for row in rows)),
        "original_action_class_counts": dict(
            Counter(row["original_action_class"] for row in rows if row.get("original_action_class"))
        ),
        "source_component_counts": dict(Counter(row["source_component"] for row in rows)),
        "source_role_counts": dict(Counter(row["source_role"] for row in rows)),
        "r_evidence_class_counts": dict(Counter(row["r_evidence_class"] for row in rows)),
        "proxy_r_class_counts": dict(Counter(row["proxy_r_class"] for row in rows)),
        "source_acquisition_required_rows": sum(1 for row in rows if row.get("source_acquisition_required")),
        "positive_proxy_rows": sum(1 for row in rows if row.get("proxy_r_class") == "POSITIVE_PROXY_R"),
        "avoid_or_redesign_rows": sum(1 for row in rows if row["decision"] == "AVOID"),
        "runtime_candidate_use_permitted_rows": sum(1 for row in rows if row["runtime_candidate_use_permitted"]),
        "candidate_use_allowed_now_rows": sum(1 for row in rows if row["candidate_use_allowed_now"]),
        "runtime_trading_or_live_broker_effect_rows": 0,
        "broker_operation_rows": 0,
        "paid_api_or_vendor_call_rows": 0,
        "coverage_counts": _coverage_counts(rows),
        "blank_anchor_counts": _blank_anchor_counts(rows),
    }


def write_outputs() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = build_rows()
    summary = build_summary(rows)
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_ROWS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return rows, summary


def _current_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def check_outputs() -> tuple[bool, str]:
    rows = build_rows()
    summary = build_summary(rows)
    expected_rows = "".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    )
    expected_summary = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if _current_text(OUTPUT_ROWS) != expected_rows:
        return False, f"{OUTPUT_ROWS} is stale or missing"
    if _current_text(OUTPUT_SUMMARY) != expected_summary:
        return False, f"{OUTPUT_SUMMARY} is stale or missing"
    return True, f"Main Orch24 action completeness residual-R runtime outputs are current: {len(rows)} rows"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify generated outputs are current")
    args = parser.parse_args()
    if args.check:
        ok, message = check_outputs()
        print(message)
        return 0 if ok else 1
    rows, summary = write_outputs()
    print(
        json.dumps(
            {
                "rows": len(rows),
                "summary": str(OUTPUT_SUMMARY),
                "runtime_rows": str(OUTPUT_ROWS),
                "decision_counts": summary["decision_counts"],
                "source_acquisition_required_rows": summary[
                    "source_acquisition_required_rows"
                ],
                "blank_anchor_counts": summary["blank_anchor_counts"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
