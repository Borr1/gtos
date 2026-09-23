#!/usr/bin/env python3
"""Build vNext runtime rows for legacy live-shadow decision evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
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
SOURCE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "main_orchestrator_24h_full_stack_research_integration_materialization"
)
DATE = "2026-05-18"
WAVE_ID = "WAVE_LEGACY_LIVE_SHADOW_DECISION_RUNTIME"
SOURCE_NAME = "gtos_vnext_legacy_live_shadow_decision_runtime_wave"
EVIDENCE_FAMILY = "gtos_vnext_legacy_live_shadow_decision_runtime"
RUNTIME_SURFACE = "legacy_live_shadow_decision_runtime"

MASTER_LEDGER_PATH = (
    ROUTE_DIR / f"GTOS_VNEXT_MASTER_INTELLIGENCE_TO_RUNTIME_CONVERSION_LEDGER_{DATE}.jsonl"
)
BATCH_LEDGER_PATH = ROUTE_DIR / f"GTOS_VNEXT_BATCH_RUNTIME_CONVERSION_LEDGER_{DATE}.jsonl"
DECISION_LEDGER_PATH = SOURCE_DIR / "MAIN_ORCH24_LEGACY_IMPLEMENTATION_DECISION_LEDGER_2026-05-16.jsonl"
REPAIR_LEDGER_PATH = SOURCE_DIR / "MAIN_ORCH24_XAGUSD_ACCOUNT_HISTORY_JOIN_REPAIR_LEDGER_2026-05-16.jsonl"
OUTPUT_ROWS = (
    ROUTE_DIR / f"GTOS_VNEXT_LEGACY_LIVE_SHADOW_DECISION_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR / f"GTOS_VNEXT_LEGACY_LIVE_SHADOW_DECISION_RUNTIME_SUMMARY_{DATE}.json"
)

SOURCE_ARTIFACT_PATHS = (
    "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/build_main_orchestrator_live_shadow_legacy_integration_2026_05_16.py",
    "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/build_main_orchestrator_xagusd_account_history_join_repair_2026_05_16.py",
    "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_LEGACY_IMPLEMENTATION_DECISION_LEDGER_2026-05-16.jsonl",
    "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_LIVE_SHADOW_LEGACY_INPUT_SNAPSHOT_2026-05-16.json",
    "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_LIVE_SHADOW_LEGACY_INTEGRATION_SUMMARY_2026-05-16.md",
    "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_LIVE_SHADOW_LEGACY_OUTPUT_MANIFEST_2026-05-16.json",
    "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_LIVE_SHADOW_LEGACY_VERIFICATION_RESULT_2026-05-16.json",
    "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_XAGUSD_ACCOUNT_HISTORY_JOIN_REPAIR_LEDGER_2026-05-16.jsonl",
    "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_XAGUSD_ACCOUNT_HISTORY_JOIN_REPAIR_OUTPUT_MANIFEST_2026-05-16.json",
    "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_XAGUSD_ACCOUNT_HISTORY_JOIN_REPAIR_SUMMARY_2026-05-16.json",
    "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_XAGUSD_ACCOUNT_HISTORY_JOIN_REPAIR_SUMMARY_2026-05-16.md",
    "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/MAIN_ORCH24_XAGUSD_ACCOUNT_HISTORY_JOIN_REPAIR_VERIFICATION_RESULT_2026-05-16.json",
    "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/verify_main_orchestrator_live_shadow_legacy_integration_2026_05_16.py",
    "research/science_program_2026_05/06_outcome_testing/main_orchestrator_24h_full_stack_research_integration_materialization/verify_main_orchestrator_xagusd_account_history_join_repair_2026_05_16.py",
)

ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "timeframe",
    "market_timeframe",
    "route_session",
    "side",
    "source_component",
    "entry_variant",
    "target_stop_order_class",
)

FAMILY_RUNTIME_MAP: dict[str, dict[str, Any]] = {
    "V2_OB_BOUNDARY_PATH_SCALING": {
        "decision": "MIXED",
        "source_component": "legacy_live_shadow_v2_replay_context",
        "source_role": "legacy_live_shadow_v2_replay_context",
        "action_class": "legacy_live_shadow_v2_duplicate_aware_replay_context",
        "r_evidence_class": "LEGACY_LIVE_SHADOW_V2_REPLAY_CONTEXT",
        "proxy_r": 0.0,
        "runtime_effect_now": "duplicate_aware_replay_context_only",
    },
    "V2B_FORWARD": {
        "decision": "MIXED",
        "source_component": "legacy_live_shadow_v2b_forward_source_acquisition",
        "source_role": "legacy_live_shadow_v2b_forward_source_acquisition_guard",
        "action_class": "legacy_live_shadow_v2b_forward_source_acquisition_guard",
        "r_evidence_class": "LEGACY_LIVE_SHADOW_V2B_FORWARD_SOURCE_ACQUISITION_REQUIRED",
        "proxy_r": 0.0,
        "source_acquisition_required": True,
        "source_acquisition_kind": "duplicate_aware_forward_actual_r_recompute_required",
        "runtime_effect_now": "zero_risk_until_duplicate_aware_forward_actual_r_exists",
    },
    "FVG_OB_CONFLUENCE": {
        "decision": "MIXED",
        "source_component": "legacy_live_shadow_fvg_ob_source_acquisition",
        "source_role": "legacy_live_shadow_fvg_ob_source_acquisition_guard",
        "action_class": "legacy_live_shadow_fvg_ob_source_acquisition_guard",
        "r_evidence_class": "LEGACY_LIVE_SHADOW_FVG_OB_SOURCE_ACQUISITION_REQUIRED",
        "proxy_r": 0.0,
        "source_acquisition_required": True,
        "source_acquisition_kind": "fvg_entry_lock_metadata_required",
        "runtime_effect_now": "zero_risk_until_exact_countable_fvg_ob_subset_exists",
    },
    "J46_J49_POLICY": {
        "decision": "FOLLOW",
        "source_component": "legacy_live_shadow_j46_j49_policy_follow",
        "source_role": "legacy_live_shadow_j46_j49_policy_context",
        "action_class": "legacy_live_shadow_j46_j49_policy_follow_pressure",
        "r_evidence_class": "LEGACY_LIVE_SHADOW_J46_J49_POLICY_FOLLOW",
        "proxy_r": 0.25,
        "runtime_effect_now": "policy_context_follow_pressure_existing_runtime_only",
    },
    "S79_SIDE_AWARE": {
        "decision": "FOLLOW",
        "source_component": "legacy_live_shadow_s79_side_aware_context",
        "source_role": "legacy_live_shadow_s79_side_aware_context",
        "action_class": "legacy_live_shadow_s79_side_aware_context",
        "r_evidence_class": "LEGACY_LIVE_SHADOW_S79_SIDE_AWARE_CONTEXT",
        "proxy_r": 0.2,
        "runtime_effect_now": "side_aware_context_follow_pressure_without_new_gate",
    },
    "K54_K55": {
        "decision": "AVOID",
        "source_component": "legacy_live_shadow_k54_k55_same_cohort_kill",
        "source_role": "legacy_live_shadow_k54_k55_same_cohort_kill_guard",
        "action_class": "legacy_live_shadow_k54_k55_same_cohort_avoid_filter",
        "r_evidence_class": "LEGACY_LIVE_SHADOW_K54_K55_MODEL_AVOID_FILTER",
        "proxy_r": -1.0,
        "runtime_effect_now": "block_same_cohort_k54_iteration_as_runtime_input",
    },
    "NOFILL_FORWARD_SOURCE_CAPTURE": {
        "decision": "MIXED",
        "source_component": "legacy_live_shadow_nofill_capture_source_acquisition",
        "source_role": "legacy_live_shadow_nofill_capture_source_acquisition_guard",
        "action_class": "legacy_live_shadow_nofill_capture_source_acquisition_guard",
        "r_evidence_class": "LEGACY_LIVE_SHADOW_NOFILL_CAPTURE_SOURCE_ACQUISITION_REQUIRED",
        "proxy_r": 0.0,
        "source_acquisition_required": True,
        "source_acquisition_kind": "entry_touch_pending_cancel_expiry_event_order_required",
        "runtime_effect_now": "zero_risk_until_no_fill_capture_contract_fields_exist",
    },
    "SIERRA_ORDERFLOW": {
        "decision": "MIXED",
        "source_component": "legacy_live_shadow_sierra_orderflow_diagnostic_context",
        "source_role": "legacy_live_shadow_sierra_orderflow_context",
        "action_class": "legacy_live_shadow_sierra_orderflow_diagnostic_context",
        "r_evidence_class": "LEGACY_LIVE_SHADOW_SIERRA_ORDERFLOW_CONTEXT",
        "proxy_r": 0.0,
        "runtime_effect_now": "diagnostic_context_no_live_filter",
    },
    "LIVE_SHADOW_STRATEGY_FOLLOW": {
        "decision": "MIXED",
        "source_component": "legacy_live_shadow_strategy_replay_context",
        "source_role": "legacy_live_shadow_strategy_replay_context",
        "action_class": "legacy_live_shadow_strategy_failure_intelligence_context",
        "r_evidence_class": "LEGACY_LIVE_SHADOW_STRATEGY_REPLAY_CONTEXT",
        "proxy_r": 0.0,
        "runtime_effect_now": "duplicate_aware_replay_and_failure_intelligence_only",
    },
    "TRAILING_STOP_EXIT_VARIANT": {
        "decision": "FOLLOW",
        "source_component": "legacy_live_shadow_trailing_stop_shadow_context",
        "source_role": "legacy_live_shadow_trailing_stop_shadow_context",
        "action_class": "legacy_live_shadow_trailing_stop_shadow_context",
        "r_evidence_class": "LEGACY_LIVE_SHADOW_TRAILING_STOP_SHADOW_CONTEXT",
        "proxy_r": 0.1,
        "runtime_effect_now": "default_off_shadow_logger_queue_context",
    },
    "PARTIAL_CLOSE_EXPANSION": {
        "decision": "AVOID",
        "source_component": "legacy_live_shadow_partial_close_expansion_avoid",
        "source_role": "legacy_live_shadow_partial_close_expansion_avoid_guard",
        "action_class": "legacy_live_shadow_partial_close_expansion_avoid_filter",
        "r_evidence_class": "LEGACY_LIVE_SHADOW_PARTIAL_CLOSE_EXPANSION_AVOID_FILTER",
        "proxy_r": -0.5,
        "runtime_effect_now": "block_new_partial_close_variant_queue",
    },
    "PORTFOLIO_VOL_MANAGED_SIZING": {
        "decision": "AVOID",
        "source_component": "legacy_live_shadow_portfolio_vol_sizing_avoid",
        "source_role": "legacy_live_shadow_portfolio_vol_sizing_avoid_guard",
        "action_class": "legacy_live_shadow_portfolio_vol_sizing_avoid_filter",
        "r_evidence_class": "LEGACY_LIVE_SHADOW_PORTFOLIO_VOL_SIZING_AVOID_FILTER",
        "proxy_r": -0.5,
        "runtime_effect_now": "block_portfolio_wide_vol_managed_sizing_runtime_input",
    },
}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _repo_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else REPO_ROOT / path


def _path_text(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return ""
    return digest.hexdigest()


def _hash_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _row_count_from_source(path: Path) -> int | None:
    suffix = path.suffix.casefold()
    if suffix == ".jsonl":
        try:
            return sum(1 for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip())
        except OSError:
            return None
    if suffix == ".json":
        return 1
    if suffix == ".md":
        try:
            return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        except OSError:
            return None
    if suffix == ".py":
        try:
            return sum(1 for line in path.read_text(encoding="utf-8").splitlines())
        except OSError:
            return None
    return None


def _ledger_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return _read_jsonl(path)


def _batch_meta() -> dict[str, dict[str, Any]]:
    meta: dict[str, dict[str, Any]] = {}
    for wave in _ledger_rows(BATCH_LEDGER_PATH):
        wave_id = _norm(wave.get("wave_id"))
        for unit in wave.get("unit_dispositions") or []:
            if not isinstance(unit, dict):
                continue
            unit_id = _norm(unit.get("unit_id"))
            if unit_id:
                payload = dict(unit)
                payload["source_batch_wave_id"] = wave_id
                meta[unit_id] = payload
    return meta


def _selected_source_units() -> list[dict[str, Any]]:
    selected_paths = {path.replace("\\", "/") for path in SOURCE_ARTIFACT_PATHS}
    batch_meta = _batch_meta()
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in _ledger_rows(MASTER_LEDGER_PATH):
        path_text = _norm(row.get("source_artifact_path")).replace("\\", "/")
        if path_text not in selected_paths or path_text in seen:
            continue
        seen.add(path_text)
        unit_id = _norm(row.get("intelligence_unit_id"))
        meta = batch_meta.get(unit_id, {})
        source_path = _repo_path(path_text)
        row_count = meta.get("row_count", row.get("row_count"))
        if row_count in ("", None):
            row_count = _row_count_from_source(source_path)
        selected.append(
            {
                "unit_id": unit_id,
                "path": path_text,
                "name": source_path.name,
                "hash": _norm(meta.get("source_artifact_hash"))
                or _norm(row.get("source_artifact_hash"))
                or _sha256_file(source_path),
                "hash_algorithm": _norm(meta.get("source_artifact_hash_algorithm"))
                or _norm(row.get("source_artifact_hash_algorithm"))
                or "git_blob_or_sha256",
                "row_count": row_count,
                "source_batch_wave_id": _norm(meta.get("source_batch_wave_id")),
            }
        )
    selected.sort(key=lambda item: (item["path"], item["unit_id"]))
    return selected


def _proxy_class(proxy_r: float) -> str:
    if proxy_r >= 1.0:
        return "STRONG_POSITIVE_PROXY_R"
    if proxy_r > 0:
        return "POSITIVE_PROXY_R"
    if proxy_r <= -1.0:
        return "STRONG_NEGATIVE_PROXY_R"
    if proxy_r < 0:
        return "NEGATIVE_PROXY_R"
    return "FLAT_PROXY_R"


def _metric(value: float | None, count: int) -> dict[str, Any]:
    if value is None:
        return {
            "sum": None,
            "mean": None,
            "match_rows_with_metric": 0,
            "positive_rows": 0,
            "negative_rows": 0,
            "zero_rows": 0,
        }
    return {
        "sum": round(value * count, 6),
        "mean": round(value, 6),
        "match_rows_with_metric": count,
        "positive_rows": count if value > 0 else 0,
        "negative_rows": count if value < 0 else 0,
        "zero_rows": count if value == 0 else 0,
    }


def _family_row_id(family: str, decision_id: str) -> str:
    suffix = decision_id.split(":", 1)[-1] if decision_id else _hash_payload({"family": family})
    return f"legacy_live_shadow_decision:{family.lower()}:{suffix}"


def _base_runtime_row(
    *,
    row_id: str,
    source_row: dict[str, Any],
    mapping: dict[str, Any],
    source_artifact: Path,
    scope: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    proxy_r = float(mapping.get("proxy_r", 0.0))
    effective_n = 3 if mapping["decision"] == "AVOID" else 1
    event_scope = {
        "route_family": "legacy_live_shadow_decision",
        "source_component": mapping["source_component"],
    }
    if scope:
        event_scope.update({key: value for key, value in scope.items() if _norm(value)})
    row = {
        "schema_version": "gtos_vnext_legacy_live_shadow_decision_runtime_row_v1",
        "row_type": "gtos_vnext_legacy_live_shadow_decision_runtime_row",
        "legacy_live_shadow_decision_runtime_row_id": row_id,
        "row_key": row_id,
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "batch_wave_id": WAVE_ID,
        "source_component": mapping["source_component"],
        "source_role": mapping["source_role"],
        "system_surface": RUNTIME_SURFACE,
        "decision": mapping["decision"],
        "review_action": mapping["decision"],
        "action_class": mapping["action_class"],
        "r_evidence_class": mapping["r_evidence_class"],
        "proxy_r": proxy_r,
        "proxy_r_class": _proxy_class(proxy_r),
        "r_metric_traces": {
            "effective_n": _metric(1.0, effective_n),
            "proxy_score": _metric(proxy_r, effective_n),
        },
        "event_scope": event_scope,
        "route_family": event_scope.get("route_family", ""),
        "route_session": event_scope.get("route_session", ""),
        "timeframe": event_scope.get("timeframe", ""),
        "market_timeframe": event_scope.get("market_timeframe", ""),
        "symbol": event_scope.get("symbol", ""),
        "source_symbol": event_scope.get("source_symbol", ""),
        "market": event_scope.get("market", ""),
        "side": event_scope.get("side", ""),
        "entry_variant": event_scope.get("entry_variant", ""),
        "target_stop_order_class": event_scope.get("target_stop_order_class", ""),
        "source_bound": bool(
            event_scope.get("symbol")
            or event_scope.get("source_symbol")
            or event_scope.get("source_component")
        ),
        "source_artifact": _path_text(source_artifact),
        "source_rows_represented": 1,
        "source_row_hash": _hash_payload(source_row),
        "source_decision_id": source_row.get("decision_id") or source_row.get("row_id", ""),
        "source_family": source_row.get("family", ""),
        "source_bucket": source_row.get("bucket", ""),
        "source_decision": source_row.get("decision") or mapping["decision"],
        "evidence_summary": source_row.get("evidence_summary") or source_row.get("current_disk_conclusion", ""),
        "candidate_use_allowed_now": False,
        "runtime_candidate_use_permitted": mapping["decision"] == "FOLLOW",
        "live_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
        "live_policy_change_allowed_now": False,
        "fresh_moonshot_cp_evidence_override_allowed": False,
        "legacy_cannot_override_fresher_cp280_cp281_cp282": True,
        "runtime_effect_now": mapping["runtime_effect_now"],
        "safe_flags": source_row.get("safe_flags", {}),
    }
    if mapping.get("source_acquisition_required"):
        row["source_acquisition_required"] = True
        row["source_acquisition_kind"] = mapping.get("source_acquisition_kind", "")
    if extra:
        row.update(extra)
    return row


def _runtime_rows_from_decisions() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_row in _read_jsonl(DECISION_LEDGER_PATH):
        family = _norm(source_row.get("family"))
        mapping = FAMILY_RUNTIME_MAP.get(family)
        if not mapping:
            continue
        rows.append(
            _base_runtime_row(
                row_id=_family_row_id(family, _norm(source_row.get("decision_id"))),
                source_row=source_row,
                mapping=mapping,
                source_artifact=DECISION_LEDGER_PATH,
                extra={
                    "artifact_paths_checked": [
                        str(path).replace("\\", "/")
                        for path in source_row.get("artifact_paths_checked") or []
                    ],
                    "input_hashes": source_row.get("input_hashes") or {},
                    "implementation_decision": source_row.get("decision"),
                    "implementation_bucket": source_row.get("bucket"),
                    "default_off_shadow_or_replay_only": True,
                },
            )
        )
    return rows


def _runtime_rows_from_repairs() -> list[dict[str, Any]]:
    mapping = {
        "decision": "MIXED",
        "source_component": "legacy_live_shadow_xagusd_account_history_source_acquisition",
        "source_role": "legacy_live_shadow_xagusd_account_history_source_acquisition_guard",
        "action_class": "legacy_live_shadow_xagusd_account_history_source_acquisition_guard",
        "r_evidence_class": "LEGACY_LIVE_SHADOW_XAGUSD_ACCOUNT_HISTORY_SOURCE_ACQUISITION_REQUIRED",
        "proxy_r": 0.0,
        "source_acquisition_required": True,
        "source_acquisition_kind": "xagusd_account_history_close_deal_export_required",
        "runtime_effect_now": "zero_risk_until_xagusd_account_history_join_repaired",
    }
    rows: list[dict[str, Any]] = []
    for source_row in _read_jsonl(REPAIR_LEDGER_PATH):
        fill_id = _norm(source_row.get("fill_id"))
        session_match = re.search(r"_(tokyo|london|ny)_(\d{4})", fill_id)
        route_session = {
            "tokyo": "tokyo_kz",
            "london": "london_core",
            "ny": "ny_core",
        }.get(session_match.group(1) if session_match else "", "ny_core")
        rows.append(
            _base_runtime_row(
                row_id=f"legacy_live_shadow_decision:xagusd_account_history:{fill_id or source_row.get('row_id')}",
                source_row=source_row,
                mapping=mapping,
                source_artifact=REPAIR_LEDGER_PATH,
                scope={
                    "symbol": "XAGUSD",
                    "source_symbol": "XAGUSD",
                    "market": "XAGUSD",
                    "timeframe": "M15",
                    "market_timeframe": "M15",
                    "route_session": route_session,
                    "entry_variant": "account_history_join_repair",
                    "target_stop_order_class": "ACCOUNT_HISTORY_REALIZED_R_MISSING",
                },
                extra={
                    "fill_id": fill_id,
                    "repair_status": source_row.get("repair_status"),
                    "missing_source": source_row.get("missing_source"),
                    "exact_next_unblocker": source_row.get("exact_next_unblocker"),
                    "next_unblocker_boundary": source_row.get("next_unblocker_boundary"),
                    "account_history_exports_searched": source_row.get(
                        "account_history_exports_searched"
                    ),
                    "account_history_xagusd_2026_05_14_deal_rows": source_row.get(
                        "account_history_xagusd_2026_05_14_deal_rows"
                    ),
                    "broker_actual_r_rows_for_fill": source_row.get(
                        "broker_actual_r_rows_for_fill"
                    ),
                    "j46_outcome_rows": source_row.get("j46_outcome_rows"),
                },
            )
        )
    return rows


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(1 for row in rows if not _norm(row.get(field)))
        for field in ANCHOR_FIELDS
    }


def _coverage_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    fields = {
        "symbols": "symbol",
        "source_symbols": "source_symbol",
        "markets": "market",
        "timeframes": "timeframe",
        "sessions": "route_session",
        "sides": "side",
        "entry_variants": "entry_variant",
        "target_stop_order_classes": "target_stop_order_class",
    }
    return {
        name: dict(
            sorted(Counter(_norm(row.get(field)) for row in rows if _norm(row.get(field))).items())
        )
        for name, field in fields.items()
    }


def build_runtime_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = _runtime_rows_from_decisions() + _runtime_rows_from_repairs()
    rows.sort(key=lambda row: row["legacy_live_shadow_decision_runtime_row_id"])
    source_artifacts = _selected_source_units()
    known_counts = [
        int(item["row_count"])
        for item in source_artifacts
        if isinstance(item.get("row_count"), int)
    ]
    source_component_counts = Counter(row["source_component"] for row in rows)
    summary = {
        "schema_version": "gtos_vnext_legacy_live_shadow_decision_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "runtime_surface": RUNTIME_SURFACE,
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": sum(
            int(row.get("source_rows_represented") or 0) for row in rows
        ),
        "wave_source_rows_counted": sum(known_counts),
        "selected_open_unit_count": len(source_artifacts),
        "row_count_unknown_unit_count": sum(
            1 for item in source_artifacts if item.get("row_count") is None
        ),
        "decision_counts": dict(sorted(Counter(row["decision"] for row in rows).items())),
        "source_component_counts": dict(sorted(source_component_counts.items())),
        "source_role_counts": dict(sorted(Counter(row["source_role"] for row in rows).items())),
        "r_evidence_class_counts": dict(
            sorted(Counter(row["r_evidence_class"] for row in rows).items())
        ),
        "action_class_counts": dict(sorted(Counter(row["action_class"] for row in rows).items())),
        "proxy_r_class_counts": dict(
            sorted(Counter(row["proxy_r_class"] for row in rows).items())
        ),
        "source_acquisition_required_rows": sum(
            1 for row in rows if row.get("source_acquisition_required") is True
        ),
        "positive_proxy_rows": sum(1 for row in rows if row["decision"] == "FOLLOW"),
        "avoid_or_redesign_rows": sum(1 for row in rows if row["decision"] == "AVOID"),
        "runtime_candidate_use_permitted_rows": sum(
            1 for row in rows if row["runtime_candidate_use_permitted"]
        ),
        "candidate_use_allowed_now_rows": sum(
            1 for row in rows if row["candidate_use_allowed_now"]
        ),
        "live_effect_rows": sum(1 for row in rows if row["live_effect"]),
        "broker_operation_rows": sum(1 for row in rows if row["broker_operation"]),
        "paid_api_or_vendor_call_rows": sum(
            1 for row in rows if row["paid_api_or_vendor_call"]
        ),
        "runtime_trading_or_live_broker_effect_rows": sum(
            1 for row in rows if row["runtime_trading_or_live_broker_effect"]
        ),
        "coverage_counts": _coverage_counts(rows),
        "blank_anchor_counts": _blank_anchor_counts(rows),
        "source_artifacts": source_artifacts,
    }
    return rows, summary


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_ROWS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _outputs_match(rows: list[dict[str, Any]], summary: dict[str, Any]) -> bool:
    if not OUTPUT_ROWS.exists() or not OUTPUT_SUMMARY.exists():
        return False
    expected_rows = [
        json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows
    ]
    if OUTPUT_ROWS.read_text(encoding="utf-8").splitlines() != expected_rows:
        return False
    try:
        actual_summary = json.loads(OUTPUT_SUMMARY.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return actual_summary == summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rows, summary = build_runtime_rows()
    if args.check:
        if not _outputs_match(rows, summary):
            print("Generated legacy live-shadow decision runtime outputs are stale.")
            return 1
        print(
            "Legacy live-shadow decision runtime outputs are current: "
            f"{summary['runtime_row_count']} rows"
        )
        return 0
    write_outputs(rows, summary)
    print(
        "Wrote legacy live-shadow decision runtime outputs: "
        f"{OUTPUT_ROWS} ({summary['runtime_row_count']} rows)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
