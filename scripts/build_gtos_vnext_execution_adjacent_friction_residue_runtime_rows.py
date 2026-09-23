#!/usr/bin/env python3
"""Build runtime rows for the execution-adjacent friction residue wave."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DATE = "2026-05-18"
WAVE_ID = "WAVE_EXECUTION_ADJACENT_FRICTION_RESIDUE_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_execution_adjacent_friction_residue"
SOURCE_NAME = "gtos_vnext_execution_adjacent_friction_residue_wave"

ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
OUTPUT_ROWS = (
    ROUTE_DIR
    / f"GTOS_VNEXT_EXECUTION_ADJACENT_FRICTION_RESIDUE_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / f"GTOS_VNEXT_EXECUTION_ADJACENT_FRICTION_RESIDUE_RUNTIME_SUMMARY_{DATE}.json"
)

SOURCE_UNITS: tuple[tuple[str, str, int | None], ...] = (
    ("UNIT_003260", "research/a3_trade_record_instrumentation/PHASE_A_RECON.md", 100),
    ("UNIT_003581", "research/audit_2026_04_26/16_mt5_broker.md", 21),
    ("UNIT_003598", "research/b_deep_audit_2026-04-19/phase1/_alpha_scratch/slippage_analysis.py", None),
    ("UNIT_004363", "research/kap_outputs/TARGETED_BOOK_ACQUISITION_LIST.md", 140),
    ("UNIT_004629", "research/ml_program/experiments/l7_slippage_logger.py", None),
    ("UNIT_004966", "research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.json", 1),
    ("UNIT_004967", "research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.md", 15),
    ("UNIT_004974", "research/operations/BROKER_R_RECONCILIATION_COVERAGE_2026-05-04.json", 1),
    ("UNIT_004975", "research/operations/BROKER_R_RECONCILIATION_COVERAGE_2026-05-04.md", 23),
    ("UNIT_004976", "research/operations/BROKER_R_RECONCILIATION_COVERAGE_2026-05-05.json", 1),
    ("UNIT_004977", "research/operations/BROKER_R_RECONCILIATION_COVERAGE_2026-05-05.md", 26),
    ("UNIT_005002", "research/operations/LANE3_EXECUTION_TELEMETRY_VERIFIERS_2026-05-03.json", 1),
    ("UNIT_005003", "research/operations/LANE3_EXECUTION_TELEMETRY_VERIFIERS_2026-05-03.md", 55),
    ("UNIT_005130", "research/operations/STATIC_LIMIT_ADAPTIVE_EXECUTION_GAP_LIVE_INTELLIGENCE_2026-05-13.md", 123),
    ("UNIT_005295", "research/phase_3_external_feed_validation/PHASE3_EXECUTION_UPDATE_2026-05-02.json", 1),
    ("UNIT_005296", "research/phase_3_external_feed_validation/PHASE3_EXECUTION_UPDATE_2026-05-02.md", 192),
    ("UNIT_005549", "research/program_control/LTO015_BROKER_ACTUAL_R_AUDIT_2026-05-05.json", 1),
    ("UNIT_005550", "research/program_control/LTO015_BROKER_ACTUAL_R_AUDIT_2026-05-05.md", 28),
    ("UNIT_005897", "research/science_program_2026_05/01_domain_syntheses/G10_EXECUTION_RISK_DOMAIN_SYNTHESIS_2026-05-06.md", 44),
    ("UNIT_005934", "research/science_program_2026_05/01_domain_syntheses/raw/G10_execution_risk_sources_2026-05-06/SOURCE_INDEX_G10_EXECUTION_RISK_2026-05-06.md", 11),
    ("UNIT_005978", "research/science_program_2026_05/03_experiment_specs/G8_CD2_02_SHORT_VOL_EXECUTION_LIFECYCLE_PREREG_2026-05-06.json", 1),
    ("UNIT_005979", "research/science_program_2026_05/03_experiment_specs/G8_CD2_02_SHORT_VOL_EXECUTION_LIFECYCLE_PREREG_2026-05-06.md", 78),
    ("UNIT_006029", "research/science_program_2026_05/04_goal_prompts/G10_G10_EXECUTION_RISK_GOAL_PROMPT_2026-05-06.md", 51),
    ("UNIT_006816", "research/science_program_2026_05/06_outcome_testing/g0_scid_asof_packet_source_control_synthesis_and_validation_design/G0_SCID_ASOF_FALSIFICATION_STOP_CONDITIONS_2026-05-11.json", 1),
    ("UNIT_007500", "research/science_program_2026_05/06_outcome_testing/g12_gtos_local_research_data_catalog_source_control_audit/G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_TARGET_VERIFIER_NONWRITING_AUDIT_2026-05-10.json", 1),
    ("UNIT_007501", "research/science_program_2026_05/06_outcome_testing/g12_gtos_local_research_data_catalog_source_control_audit/G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT_TARGET_VERIFIER_NONWRITING_AUDIT_2026-05-10.md", 38),
    ("UNIT_007517", "research/science_program_2026_05/06_outcome_testing/g12_live_forward_evidence_capture_hardening_audit/TARGETED_TEST_RESULT_2026-05-12.json", 1),
    ("UNIT_007518", "research/science_program_2026_05/06_outcome_testing/g12_live_forward_evidence_capture_hardening_audit/TARGETED_TEST_RESULT_2026-05-12.md", 12),
    ("UNIT_007551", "research/science_program_2026_05/06_outcome_testing/g12_no_api_mechanical_replay_engine_source_control_audit/G12_NO_API_MECHANICAL_REPLAY_TARGET_ARTIFACT_PARSE_AUDIT_2026-05-10.json", 1),
    ("UNIT_007552", "research/science_program_2026_05/06_outcome_testing/g12_no_api_mechanical_replay_engine_source_control_audit/G12_NO_API_MECHANICAL_REPLAY_TARGET_ARTIFACT_PARSE_AUDIT_2026-05-10.md", 257),
    ("UNIT_007553", "research/science_program_2026_05/06_outcome_testing/g12_no_api_mechanical_replay_engine_source_control_audit/G12_NO_API_MECHANICAL_REPLAY_TARGET_CODE_SOURCE_AUDIT_2026-05-10.json", 1),
    ("UNIT_007554", "research/science_program_2026_05/06_outcome_testing/g12_no_api_mechanical_replay_engine_source_control_audit/G12_NO_API_MECHANICAL_REPLAY_TARGET_CODE_SOURCE_AUDIT_2026-05-10.md", 218),
    ("UNIT_007555", "research/science_program_2026_05/06_outcome_testing/g12_no_api_mechanical_replay_engine_source_control_audit/G12_NO_API_MECHANICAL_REPLAY_TARGET_VERIFIER_TEST_REPORT_2026-05-10.json", 1),
    ("UNIT_007556", "research/science_program_2026_05/06_outcome_testing/g12_no_api_mechanical_replay_engine_source_control_audit/G12_NO_API_MECHANICAL_REPLAY_TARGET_VERIFIER_TEST_REPORT_2026-05-10.md", 77),
    ("UNIT_008357", "research/science_program_2026_05/06_outcome_testing/g12_scid_anti_boxing_r11_adv_002_source_control_audit/G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT_TARGET_ARTIFACT_AUDIT_2026-05-13.json", 1),
    ("UNIT_008358", "research/science_program_2026_05/06_outcome_testing/g12_scid_anti_boxing_r11_adv_002_source_control_audit/G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT_TARGET_ARTIFACT_AUDIT_2026-05-13.md", 279),
    ("UNIT_008570", "research/science_program_2026_05/06_outcome_testing/g12_scid_expansion_candidate_acceptance_design_audit/G12_SCID_EXPANSION_AUDIT_CONTEXT_AND_TARGET_INPUT_INVENTORY_2026-05-12.json", 1),
    ("UNIT_008571", "research/science_program_2026_05/06_outcome_testing/g12_scid_expansion_candidate_acceptance_design_audit/G12_SCID_EXPANSION_AUDIT_CONTEXT_AND_TARGET_INPUT_INVENTORY_2026-05-12.md", 195),
    ("UNIT_008630", "research/science_program_2026_05/06_outcome_testing/g12_scid_forward_capture_implementation_design_package_audit/G12_SCID_FC_IMPL_DESIGN_AUDIT_TARGET_VERIFIER_AND_FOCUSED_TESTS_2026-05-12.json", 1),
    ("UNIT_008631", "research/science_program_2026_05/06_outcome_testing/g12_scid_forward_capture_implementation_design_package_audit/G12_SCID_FC_IMPL_DESIGN_AUDIT_TARGET_VERIFIER_AND_FOCUSED_TESTS_2026-05-12.md", 98),
    ("UNIT_008632", "research/science_program_2026_05/06_outcome_testing/g12_scid_forward_capture_implementation_design_package_audit/G12_SCID_FC_IMPL_DESIGN_AUDIT_TARGET_VERIFIER_STDOUT_2026-05-12.json", 1),
    ("UNIT_008790", "research/science_program_2026_05/06_outcome_testing/g12_scid_noapi_40card_prereg_replay_input_design_audit/G12_SCID_NOAPI_PREREG_AUDIT_CONTEXT_AND_TARGET_INPUT_INVENTORY_2026-05-12.json", 1),
    ("UNIT_008791", "research/science_program_2026_05/06_outcome_testing/g12_scid_noapi_40card_prereg_replay_input_design_audit/G12_SCID_NOAPI_PREREG_AUDIT_CONTEXT_AND_TARGET_INPUT_INVENTORY_2026-05-12.md", 461),
    ("UNIT_012516", "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_additive_implementation_from_parallel_g12_wave/SCID_FC_ADDITIVE_IMPL_BROKER_READ_LEDGER_2026-05-12.json", 1),
    ("UNIT_012517", "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_additive_implementation_from_parallel_g12_wave/SCID_FC_ADDITIVE_IMPL_BROKER_READ_LEDGER_2026-05-12.md", 3),
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
    "action_class",
    "entry_variant",
    "target_stop_order_class",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _repo_path(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def _metric(value: float | int | None, *, source_field: str) -> dict[str, Any]:
    if isinstance(value, (int, float)):
        return {
            "sum": float(value),
            "count": 1,
            "mean": float(value),
            "min": float(value),
            "max": float(value),
            "positive_rows": 1 if value > 0 else 0,
            "negative_rows": 1 if value < 0 else 0,
            "zero_rows": 1 if value == 0 else 0,
            "match_rows_with_metric": 1,
            "source_field": source_field,
            "source_shape": "execution_adjacent_friction_residue",
        }
    return {
        "sum": None,
        "count": 0,
        "mean": None,
        "min": None,
        "max": None,
        "positive_rows": 0,
        "negative_rows": 0,
        "zero_rows": 0,
        "match_rows_with_metric": 0,
        "source_field": source_field,
        "source_shape": "missing",
    }


def _family(path_text: str) -> str:
    path = path_text.casefold()
    if "static_limit_adaptive" in path or "execution_lifecycle_prereg" in path or "g10_execution_risk" in path:
        return "static_limit_adaptive_entry_pending_lifecycle"
    if "broker_r" in path or "lto015" in path or "slippage" in path or "mt5_broker" in path:
        return "broker_actual_r_slippage_execution_identity"
    if "trade_record_instrumentation" in path or "lane3_execution_telemetry" in path:
        return "trade_record_execution_lifecycle_source_repair"
    if "target_feature_registry" in path or "targeted_book" in path or "external_feed" in path:
        return "target_feature_orderflow_external_feed_context"
    if "noapi" in path or "anti_boxing" in path or "expansion_candidate" in path:
        return "replay_audit_support_execution_source_contract"
    return "source_capture_materialization_and_audit_support"


def _scope(
    *,
    source_component: str,
    symbol: str = "",
    source_symbol: str = "",
    market: str = "",
    route_session: str = "",
    side: str = "",
    action_class: str = "",
    target_stop_order_class: str = "",
    source_path_sha256: str = "",
) -> dict[str, str]:
    return {
        key: value
        for key, value in {
            "symbol": symbol,
            "source_symbol": source_symbol or symbol,
            "market": market or symbol,
            "timeframe": "M15" if symbol else "",
            "market_timeframe": "M15" if symbol else "",
            "route_family": "nofill_mechanical" if source_component.startswith("static_limit_") else "numeric_router",
            "route_session": route_session,
            "side": side,
            "source_component": source_component,
            "action_class": action_class,
            "target_stop_order_class": target_stop_order_class,
            "source_path_sha256": source_path_sha256 if not symbol else "",
        }.items()
        if value
    }


def _base_row(
    *,
    unit_id: str,
    path_text: str,
    path_sha: str,
    row_count: int | None,
    row_suffix: str,
    source_component: str,
    decision: str,
    action_class: str,
    source_role: str,
    r_evidence_class: str,
    runtime_effect_now: str,
    event_scope: dict[str, str],
    proxy_r_class: str = "",
    source_repair_required: bool = False,
    source_acquisition_required: bool = False,
    source_bound: bool = False,
    source_complete: bool = False,
    metric_value: float | None = None,
    metric_field: str = "source_row",
) -> dict[str, Any]:
    row_id = f"execution_adjacent_friction_residue:{_hash_text(f'{unit_id}|{row_suffix}|{path_text}')}"
    row = {
        "execution_adjacent_friction_residue_runtime_row_id": row_id,
        "row_key": row_id,
        "source_row_id": f"{unit_id}:{row_suffix}",
        "schema_version": "gtos_vnext_execution_adjacent_friction_residue_runtime_v1",
        "wave_id": WAVE_ID,
        "source_unit_id": unit_id,
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "source_group": action_class,
        "source_role": source_role,
        "system_surface": "execution_adjacent_friction_residue_runtime",
        "source_component": source_component,
        "source_artifact_path": path_text,
        "source_path": path_text,
        "source_artifact": path_text,
        "source_artifact_sha256": path_sha,
        "source_declared_row_count": row_count,
        "source_row_count_known": row_count is not None,
        "behavior_family": _family(path_text),
        "event_scope": event_scope,
        "route_family": event_scope.get("route_family", ""),
        "symbol": event_scope.get("symbol", ""),
        "source_symbol": event_scope.get("source_symbol", ""),
        "market": event_scope.get("market", ""),
        "timeframe": event_scope.get("timeframe", ""),
        "market_timeframe": event_scope.get("market_timeframe", ""),
        "route_session": event_scope.get("route_session", ""),
        "side": event_scope.get("side", ""),
        "action_class": action_class,
        "target_stop_order_class": event_scope.get("target_stop_order_class", ""),
        "decision": decision,
        "review_action": decision,
        "runtime_effect_now": runtime_effect_now,
        "r_evidence_class": r_evidence_class,
        "proxy_r_class": proxy_r_class,
        "source_repair_required": source_repair_required,
        "source_acquisition_required": source_acquisition_required,
        "source_bound": source_bound,
        "source_complete": source_complete,
        "runtime_score_allowed": decision in {"FOLLOW", "AVOID"} and source_complete,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
        "validation_safe": False,
        "implementation_action": (
            "STATIC_LIMIT_ADAPTIVE_ENTRY_SOURCE_REQUIREMENT"
            if source_component == "static_limit_adaptive_entry_source_requirement"
            else "STATIC_LIMIT_ADAPTIVE_ENTRY_SHADOW_CHALLENGER"
            if source_component == "static_limit_adaptive_entry_challenger"
            else "SOURCE_JOIN_REPAIR_REQUIRED"
            if source_repair_required
            else "MERGE_AS_CONTEXT_STRESS_GUARD_INPUT"
        ),
        "r_metrics": {
            "proxy_score": _metric(metric_value, source_field=metric_field),
            "effective_n": _metric(1, source_field="runtime_residue_row"),
        },
    }
    return row


def _static_limit_rows(unit_id: str, path_text: str, path_sha: str, row_count: int | None) -> list[dict[str, Any]]:
    if "STATIC_LIMIT_ADAPTIVE_EXECUTION_GAP" not in path_text:
        scope_hash = _scope(
            source_component="static_limit_adaptive_entry_source_requirement",
            action_class="static_limit_adaptive_entry_source_requirement",
            source_path_sha256=path_sha,
        )
        return [
            _base_row(
                unit_id=unit_id,
                path_text=path_text,
                path_sha=path_sha,
                row_count=row_count,
                row_suffix="source_requirement_context",
                source_component="static_limit_adaptive_entry_source_requirement",
                decision="MIXED",
                action_class="static_limit_adaptive_entry_source_requirement",
                source_role="static_limit_adaptive_entry_source_requirement",
                r_evidence_class="STATIC_LIMIT_ADAPTIVE_ENTRY_SOURCE_REQUIREMENT",
                runtime_effect_now="static_limit_adaptive_entry_source_requirement_guard",
                event_scope=scope_hash,
                source_acquisition_required=True,
            )
        ]

    incident_scopes = [
        ("xagusd_near_miss_challenger", "XAGUSD", "LONG", "ALL_SESSIONS", "static_limit_adaptive_entry_challenger", "FOLLOW", "static_limit_adaptive_entry_follow_pressure", "STATIC_LIMIT_ADAPTIVE_ENTRY_TARGET_FIRST_PROXY", "POSITIVE_PROXY_R", "TARGET_FIRST_PROXY_DOMINANT", 0.291667),
        ("xagusd_source_requirement", "XAGUSD", "LONG", "ALL_SESSIONS", "static_limit_adaptive_entry_source_requirement", "MIXED", "static_limit_adaptive_entry_source_requirement", "STATIC_LIMIT_ADAPTIVE_ENTRY_SOURCE_REQUIREMENT", "", "TARGET_FIRST_PROXY_DOMINANT", None),
        ("gbpjpy_prior_source_requirement", "GBPJPY", "LONG", "london_core", "static_limit_adaptive_entry_source_requirement", "MIXED", "static_limit_adaptive_entry_source_requirement", "STATIC_LIMIT_ADAPTIVE_ENTRY_SOURCE_REQUIREMENT", "", "", None),
        ("us30_prior_source_requirement", "US30", "LONG", "london_core", "static_limit_adaptive_entry_source_requirement", "MIXED", "static_limit_adaptive_entry_source_requirement", "STATIC_LIMIT_ADAPTIVE_ENTRY_SOURCE_REQUIREMENT", "", "", None),
        ("nas100_prior_source_requirement", "NAS100", "LONG", "london_core", "static_limit_adaptive_entry_source_requirement", "MIXED", "static_limit_adaptive_entry_source_requirement", "STATIC_LIMIT_ADAPTIVE_ENTRY_SOURCE_REQUIREMENT", "", "", None),
        ("xagusd_post_cancel_reentry_source_requirement", "XAGUSD", "LONG", "ALL_SESSIONS", "static_limit_adaptive_entry_source_requirement", "MIXED", "static_limit_adaptive_entry_source_requirement", "STATIC_LIMIT_ADAPTIVE_ENTRY_SOURCE_REQUIREMENT", "", "TARGET_STOP_AMBIGUOUS_OR_MIXED", None),
    ]
    rows: list[dict[str, Any]] = []
    for suffix, symbol, side, session, component, decision, action_class, r_class, proxy_class, target_class, metric_value in incident_scopes:
        rows.append(
            _base_row(
                unit_id=unit_id,
                path_text=path_text,
                path_sha=path_sha,
                row_count=row_count,
                row_suffix=suffix,
                source_component=component,
                decision=decision,
                action_class=action_class,
                source_role=(
                    "static_limit_adaptive_entry_shadow_challenger"
                    if component == "static_limit_adaptive_entry_challenger"
                    else "static_limit_adaptive_entry_source_requirement"
                ),
                r_evidence_class=r_class,
                runtime_effect_now=(
                    "static_limit_adaptive_pending_market_entry_candidate"
                    if component == "static_limit_adaptive_entry_challenger"
                    else "static_limit_adaptive_entry_source_requirement_guard"
                ),
                event_scope=_scope(
                    source_component=component,
                    symbol=symbol,
                    route_session=session,
                    side=side,
                    action_class=action_class,
                    target_stop_order_class=target_class,
                ),
                proxy_r_class=proxy_class,
                source_acquisition_required=component.endswith("_source_requirement"),
                source_bound=True,
                source_complete=component == "static_limit_adaptive_entry_challenger",
                metric_value=metric_value,
                metric_field="missed_fill_rate_or_live_near_miss_proxy",
            )
        )
    return rows


def _generic_rows(unit_id: str, path_text: str, path_sha: str, row_count: int | None) -> list[dict[str, Any]]:
    family = _family(path_text)
    if family == "static_limit_adaptive_entry_pending_lifecycle":
        return _static_limit_rows(unit_id, path_text, path_sha, row_count)
    if family == "broker_actual_r_slippage_execution_identity":
        component = "broker_actual_r_slippage_source_repair"
        role = "broker_actual_r_slippage_source_repair"
        source_repair = True
        r_class = "SOURCE_REPAIR_FOR_EXACT_R"
    elif family == "trade_record_execution_lifecycle_source_repair":
        component = "trade_record_execution_source_repair"
        role = "trade_record_execution_source_repair"
        source_repair = True
        r_class = "SOURCE_REPAIR_FOR_EXACT_R"
    elif family == "target_feature_orderflow_external_feed_context":
        component = "orderflow_pending_lifecycle_source_gap"
        role = "orderflow_pending_lifecycle_source_gap"
        source_repair = False
        r_class = "ORDERFLOW_PENDING_LIFECYCLE_SOURCE_CONTEXT"
    elif family == "replay_audit_support_execution_source_contract":
        component = "execution_replay_source_contract_context"
        role = "execution_replay_source_contract_context"
        source_repair = False
        r_class = "EXECUTION_REPLAY_SOURCE_CONTRACT_CONTEXT"
    else:
        component = "execution_source_capture_contract_context"
        role = "execution_source_capture_contract_context"
        source_repair = False
        r_class = "EXECUTION_SOURCE_CAPTURE_CONTRACT_CONTEXT"
    return [
        _base_row(
            unit_id=unit_id,
            path_text=path_text,
            path_sha=path_sha,
            row_count=row_count,
            row_suffix=family,
            source_component=component,
            decision="MIXED",
            action_class=component,
            source_role=role,
            r_evidence_class=r_class,
            runtime_effect_now=f"{component}_guard",
            event_scope=_scope(
                source_component=component,
                action_class=component,
                source_path_sha256=path_sha,
            ),
            source_repair_required=source_repair,
            source_acquisition_required=not source_repair,
        )
    ]


def build_runtime_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for unit_id, path_text, row_count in SOURCE_UNITS:
        path = REPO_ROOT / path_text
        path_sha = _sha256(path)
        rows.extend(_generic_rows(unit_id, path_text, path_sha, row_count))
    return rows


def _coverage(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    specs = {
        "symbols": "symbol",
        "source_symbols": "source_symbol",
        "markets": "market",
        "timeframes": "timeframe",
        "sessions": "route_session",
        "sides": "side",
        "source_components": "source_component",
        "action_classes": "action_class",
        "target_stop_order_classes": "target_stop_order_class",
        "r_evidence_classes": "r_evidence_class",
        "proxy_r_classes": "proxy_r_class",
        "behavior_families": "behavior_family",
    }
    output: dict[str, dict[str, int]] = {}
    for name, field in specs.items():
        counts = Counter(str(row.get(field) or "") for row in rows if row.get(field))
        output[name] = dict(sorted(counts.items()))
    return output


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_path[str(row["source_artifact_path"])].append(row)
    source_artifacts = []
    source_lookup = {path: (unit_id, row_count) for unit_id, path, row_count in SOURCE_UNITS}
    for path_text in sorted(source_lookup):
        path = REPO_ROOT / path_text
        unit_id, row_count = source_lookup[path_text]
        path_rows = by_path.get(path_text, [])
        source_artifacts.append(
            {
                "unit_id": unit_id,
                "path": path_text,
                "sha256_or_git_blob": _sha256(path),
                "rows": row_count,
                "row_count_known": row_count is not None,
                "runtime_rows_read": len(path_rows),
                "source_components": sorted({row["source_component"] for row in path_rows}),
                "decision_counts": dict(Counter(row["decision"] for row in path_rows)),
                "behavior_family": _family(path_text),
            }
        )
    blank_anchor_counts = {
        field: sum(1 for row in rows if not row.get(field))
        for field in ANCHOR_FIELDS
        if sum(1 for row in rows if not row.get(field))
    }
    decision_counts = Counter(row["decision"] for row in rows)
    source_component_counts = Counter(row["source_component"] for row in rows)
    r_class_counts = Counter(row["r_evidence_class"] for row in rows)
    return {
        "schema_version": "gtos_vnext_execution_adjacent_friction_residue_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": sum(row_count or 0 for _, _, row_count in SOURCE_UNITS),
        "selected_source_unit_count": len(SOURCE_UNITS),
        "wave_source_artifact_count": len(SOURCE_UNITS),
        "wave_source_rows_counted": sum(row_count or 0 for _, _, row_count in SOURCE_UNITS),
        "row_count_unknown_unit_count": sum(1 for _, _, row_count in SOURCE_UNITS if row_count is None),
        "decision_counts": dict(sorted(decision_counts.items())),
        "source_component_counts": dict(sorted(source_component_counts.items())),
        "source_group_counts": dict(sorted(Counter(row["source_group"] for row in rows).items())),
        "source_role_counts": dict(sorted(Counter(row["source_role"] for row in rows).items())),
        "action_class_counts": dict(sorted(Counter(row["action_class"] for row in rows).items())),
        "r_evidence_class_counts": dict(sorted(r_class_counts.items())),
        "proxy_r_class_counts": dict(sorted(Counter(row["proxy_r_class"] for row in rows if row.get("proxy_r_class")).items())),
        "source_repair_required_rows": sum(1 for row in rows if row.get("source_repair_required")),
        "source_acquisition_required_rows": sum(1 for row in rows if row.get("source_acquisition_required")),
        "static_limit_adaptive_entry_rows": source_component_counts["static_limit_adaptive_entry_challenger"],
        "static_limit_source_requirement_rows": source_component_counts["static_limit_adaptive_entry_source_requirement"],
        "broker_actual_r_slippage_source_repair_rows": source_component_counts["broker_actual_r_slippage_source_repair"],
        "trade_record_execution_source_repair_rows": source_component_counts["trade_record_execution_source_repair"],
        "context_rows": int(decision_counts.get("MIXED", 0)),
        "follow_pressure_rows": int(decision_counts.get("FOLLOW", 0)),
        "avoid_veto_rows": int(decision_counts.get("AVOID", 0)),
        "runtime_candidate_use_permitted_rows": sum(1 for row in rows if row.get("runtime_candidate_use_permitted")),
        "candidate_use_allowed_now_rows": sum(1 for row in rows if row.get("candidate_use_allowed_now")),
        "live_effect_rows": sum(1 for row in rows if row.get("live_effect")),
        "broker_operation_rows": sum(1 for row in rows if row.get("broker_operation")),
        "paid_api_or_vendor_call_rows": sum(1 for row in rows if row.get("paid_api_or_vendor_call")),
        "runtime_trading_or_live_broker_effect_rows": sum(1 for row in rows if row.get("runtime_trading_or_live_broker_effect")),
        "blank_anchor_counts": blank_anchor_counts,
        "coverage_counts": _coverage(rows),
        "source_artifacts": source_artifacts,
    }


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_ROWS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rows = build_runtime_rows()
    summary = _summary(rows)
    if not args.check:
        write_outputs(rows, summary)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
