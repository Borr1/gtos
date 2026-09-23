#!/usr/bin/env python3
"""Verify the initial Wave2 causal-microscope spine artifacts."""

from __future__ import annotations

from collections import Counter
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]
READINESS_STATUS = "semantic_repaired_ready_for_central_orchestrator_review_not_launched_not_accepted"
PROMPT_STATUS = "semantic_hardened_ready_for_central_orchestrator_review_not_accepted"
EXPECTED_LANE_COUNT = 19

REQUIRED_JSON = [
    "WAVE2_CONTEXT_ANCHOR.json",
    "WAVE2_SYSTEM_INTERACTION_GRAPH.json",
    "WAVE2_CANDIDATE_FUNNEL_QUALITY_METRICS.json",
    "WAVE2_FULL_SYSTEM_CAUSAL_MODEL.json",
    "WAVE2_FULL_LEDGER_COVERAGE_AUDIT.json",
    "WAVE2_STATIC_R_GEOMETRY_AUDIT_SUMMARY.json",
    "WAVE2_COST_BROKER_NET_SUMMARY.json",
    "WAVE2_AI_RELIABILITY_AND_COST_CONTROL_CONTRACT.json",
    "WAVE2_LIVE_DECISION_PACKET_V4_CAPTURE_CONTRACT.json",
    "WAVE2_VALIDATION_ANTI_OVERFIT_CONTRACT.json",
    "WAVE2_REPLAY_COMPRESSION_AND_PARTITION_PLAN.json",
    "WAVE2_TICK_REPAIR_SOURCE_COVERAGE_AUDIT.json",
    "WAVE2_MARKET_DATA_GAP_PROXY_REPAIR_SUMMARY.json",
    "WAVE2_PENDING_NOFILL_SOURCE_COVERAGE_SUMMARY.json",
    "WAVE2_V3_VALIDATION_AI_DUAL_BROKER_DISPOSITION_SUMMARY.json",
    "WAVE2_PROMPT_REQUIRED_OUTPUT_GAP_SUMMARY.json",
    "WAVE2_PROMPT_PACK_MANIFEST.json",
    "WAVE2_PROMPT_HARDENING_VERIFICATION_RESULT.json",
    "WAVE2_SEMANTIC_PROMPT_HARDENING_VERIFICATION_RESULT.json",
    "WAVE2_FINAL_MASTER_STATE_TABLE.json",
    "WAVE2_WAVE3_LAUNCH_ORDER.json",
    "WAVE2_INSTRUCTION_COVERAGE_CHECKLIST.json",
    "WAVE3_LANE_DEPENDENCY_GRAPH.json",
    "WAVE2_SAME_SYMBOL_LIFECYCLE_OWNERSHIP_CONTRACT.json",
    "WAVE2_PROBABILITY_DEBATE_ENGINE_CONTRACT.json",
    "WAVE2_FOLLOW_AVOID_MIXED_NUMERIC_CONFLUENCE_CONTRACT.json",
    "WAVE2_WAVE4_WAVE5_ML_OWNERSHIP_CONTRACT.json",
    "WAVE2_FEATURE_LABEL_STORE_CONTRACT.json",
    "WAVE2_MODEL_REGISTRY_AND_CHALLENGER_CONTRACT.json",
    "WAVE2_LONG_RUNNING_LOCAL_TRAINING_CONTRACT.json",
    "WAVE2_DOWNSTREAM_OWNERSHIP_MAP.json",
    "WAVE2_SEMANTIC_LAUNCH_ARCHITECTURE_REPAIR_SUMMARY.json",
    "WAVE2_ROUTE_AUDIT.json",
    "WAVE2_OUTPUT_MANIFEST.json",
]

REQUIRED_JSONL = [
    "WAVE2_SEARCHED_ROOT_LEDGER.jsonl",
    "WAVE2_SOURCE_INVENTORY.jsonl",
    "WAVE2_WAVE1_INPUT_INSPECTION_LEDGER.jsonl",
    "WAVE2_DEEP_REVIEW_SUBAGENT_LEDGER.jsonl",
    "WAVE2_SUBAGENT_ROSTER_AND_FINDINGS_LEDGER.jsonl",
    "WAVE2_CONTRADICTION_REPAIR_LEDGER.jsonl",
    "WAVE2_SEMANTIC_INDEPENDENT_REVIEW_LEDGER.jsonl",
    "WAVE2_ACTIVE_CAUSAL_QUESTION_STACK.jsonl",
    "WAVE2_QUESTION_COVERAGE_SATURATION_LEDGER.jsonl",
    "WAVE2_DISCOVERED_HYPOTHESIS_LEDGER.jsonl",
    "WAVE2_NEWLY_DISCOVERED_INTELLIGENCE_LEDGER.jsonl",
    "WAVE2_STATIC_R_GEOMETRY_SOURCE_INVENTORY.jsonl",
    "WAVE2_STATIC_R_GEOMETRY_AUDIT_LEDGER.jsonl",
    "WAVE2_TARGET_STOP_GEOMETRY_AND_PATH_ORDER_LEDGER.jsonl",
    "WAVE2_SLTP_MODIFY_LIFECYCLE_SOURCE_COVERAGE_LEDGER.jsonl",
    "WAVE2_STATIC_R_GEOMETRY_JOIN_GAP_LEDGER.jsonl",
    "WAVE2_COST_BROKER_NET_CAUSAL_LEDGER.jsonl",
    "WAVE2_COST_SPREAD_SLIPPAGE_BROKER_NET_LEDGER.jsonl",
    "WAVE2_COST_SOURCE_COVERAGE_AUDIT.jsonl",
    "WAVE2_SELECTOR_SCHEDULER_OPPORTUNITY_COST_LEDGER.jsonl",
    "WAVE2_SELECTED_VS_ALTERNATIVE_OPPORTUNITY_COST_LEDGER.jsonl",
    "WAVE2_BEST_TRADE_ALLOCATOR_OPPORTUNITY_COST_LEDGER.jsonl",
    "WAVE2_MARKET_VS_SYSTEM_WHITEBOARD_LEDGER.jsonl",
    "WAVE2_PROFIT_HARVEST_FILLED_TRADE_LEDGER.jsonl",
    "WAVE2_FIRST_PASSAGE_TIME_TO_DESTINATION_LEDGER.jsonl",
    "WAVE2_EXECUTION_ENTRY_PATH_MAE_MFE_TIME_LEDGER.jsonl",
    "WAVE2_ENTRY_PATH_MAE_MFE_TTD_CAUSAL_LEDGER.jsonl",
    "WAVE2_POOR_ENTRY_ADVERSE_EXCURSION_LEDGER.jsonl",
    "WAVE2_TIME_TO_DESTINATION_AND_STALE_THESIS_LEDGER.jsonl",
    "WAVE2_OVERNIGHT_NEXT_DAY_STALE_THESIS_LEDGER.jsonl",
    "WAVE2_LOSER_MFE_REPAIR_LEDGER.jsonl",
    "WAVE2_MAX_PROFITABILITY_AND_REVERSAL_LEDGER.jsonl",
    "WAVE2_MFE_HARVEST_FAILURE_LEDGER.jsonl",
    "WAVE2_PROFIT_PATH_CONSOLIDATION_REVERSAL_LEDGER.jsonl",
    "WAVE2_SHADOW_PATH_SOURCE_COVERAGE_LEDGER.jsonl",
    "WAVE2_ROW_LEVEL_CAUSAL_EXEMPLAR_LEDGER.jsonl",
    "WAVE2_PROMPT_REQUIRED_OUTPUT_GAP_LEDGER.jsonl",
    "WAVE2_ALLOCATOR_DECISION_WINDOW_REPAIR_SOURCE_LEDGER.jsonl",
    "WAVE2_ALLOCATOR_WINDOW_SOURCE_COVERAGE_AUDIT.jsonl",
    "WAVE2_INFERRED_ALLOCATOR_DECISION_WINDOW_REPAIR_LEDGER.jsonl",
    "WAVE2_PATH_REPAIR_SOURCE_COVERAGE_AUDIT.jsonl",
    "WAVE2_TICK_REPAIRED_FIRST_PASSAGE_MFE_MAE_REVERSAL_LEDGER.jsonl",
    "WAVE2_MARKET_SYSTEM_ROW_CLASSIFICATION_LEDGER.jsonl",
    "WAVE2_SELECTOR_SELECTED_CELL_QUALITY_REPAIR_LEDGER.jsonl",
    "WAVE2_ALLOCATOR_DECISION_WINDOW_REPLAY_LEDGER.jsonl",
    "WAVE2_ZERO_TRADE_COUNTERFACTUAL_PATH_RANK_LEDGER.jsonl",
    "WAVE2_FINAL_SAY_SELECTOR_SCHEDULER_JOIN_LEDGER.jsonl",
    "WAVE2_MT5_READONLY_MARKET_DATA_RECOVERY_LEDGER.jsonl",
    "WAVE2_MARKET_DATA_GAP_PROXY_REPAIR_LEDGER.jsonl",
    "WAVE2_PENDING_NOFILL_LIFECYCLE_RECONCILIATION.jsonl",
    "WAVE2_DUAL_BROKER_AUTHORITY_DISPOSITION_LEDGER.jsonl",
    "WAVE2_V3_TO_V4_DISPOSITION_LEDGER.jsonl",
    "WAVE2_WAVE3_LANE_CONTRACTS.jsonl",
    "WAVE3_PER_LANE_CONTROLLING_PROMPTS.jsonl",
    "WAVE3_PER_LANE_ONE_LINE_STARTERS.jsonl",
    "WAVE2_CAPTURE_REPLAY_AI_PRODUCTION_DISPOSITION_LEDGER.jsonl",
    "WAVE2_PRODUCTION_CODE_COMPONENT_DISPOSITION_LEDGER.jsonl",
    "WAVE2_DEPLOYABLE_SCOPE_LFS_AND_ROLLBACK_LEDGER.jsonl",
    "WAVE2_ACCEPT_REJECT_MANAGE_EXIT_INTERACTION_LEDGER.jsonl",
    "WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl",
    "WAVE2_EVERY_CANDIDATE_CAUSAL_MICROSCOPE.jsonl",
    "WAVE2_SELECTOR_LOOSENESS_AND_TRADE_QUALITY_LEDGER.jsonl",
    "WAVE2_LIVE_AUTHORITY_FINAL_SAY_MATRIX.jsonl",
    "WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl",
]

REQUIRED_TEXT = [
    "WAVE2_SATURATION_SELF_RED_TEAM.md",
    "WAVE2_COMPLETION_AUDIT.md",
    "WAVE2_STATIC_R_GEOMETRY_AUDIT_SUMMARY.md",
]


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} is not a JSON object")
    return payload


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_no} is not a JSON object")
            rows.append(payload)
    return rows


def resolve_manifest_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else REPO_ROOT / path


def manifest_contradiction_scan_scope(
    manifest: dict[str, Any],
    issues: list[str],
) -> tuple[list[Path], list[dict[str, str]], int]:
    files = manifest.get("files")
    if not isinstance(files, list):
        issues.append("manifest_files_missing_for_active_contradiction_scan")
        return [], [], 0

    active_artifacts: list[Path] = []
    source_exclusions: list[dict[str, str]] = []
    for index, entry in enumerate(files, start=1):
        if not isinstance(entry, dict):
            issues.append(f"manifest_file_entry_not_object:{index}")
            continue
        manifest_path = entry.get("path")
        if not isinstance(manifest_path, str) or not manifest_path:
            issues.append(f"manifest_file_entry_missing_path:{index}")
            continue
        path = resolve_manifest_path(manifest_path)
        if not path.exists():
            issues.append(f"manifested_artifact_missing_for_contradiction_scan:{manifest_path}")
            continue
        if path.suffix == ".py":
            if path.name.startswith("build_wave2_"):
                classification = "generator_history_excluded_from_active_route_state"
            elif path.name == "verify_wave2_initial_causal_master.py":
                classification = "verifier_control_source_excluded_from_active_route_state"
            else:
                classification = "unclassified_python_source_not_excluded"
                issues.append(f"unclassified_python_source_in_manifest:{manifest_path}")
                active_artifacts.append(path)
                continue
            source_exclusions.append({"path": manifest_path, "classification": classification})
            continue
        active_artifacts.append(path)
    return active_artifacts, source_exclusions, len(files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-result", action="store_true")
    args = parser.parse_args()

    issues: list[str] = []
    json_payloads: dict[str, dict[str, Any]] = {}
    jsonl_rows: dict[str, list[dict[str, Any]]] = {}

    for name in REQUIRED_JSON:
        path = ROUTE_DIR / name
        if not path.exists():
            issues.append(f"missing_json:{name}")
            continue
        try:
            json_payloads[name] = read_json(path)
        except Exception as exc:  # noqa: BLE001 - verifier reports all parse failures.
            issues.append(f"json_parse_error:{name}:{exc}")

    for name in REQUIRED_JSONL:
        path = ROUTE_DIR / name
        if not path.exists():
            issues.append(f"missing_jsonl:{name}")
            continue
        try:
            jsonl_rows[name] = read_jsonl(path)
        except Exception as exc:  # noqa: BLE001 - verifier reports all parse failures.
            issues.append(f"jsonl_parse_error:{name}:{exc}")

    for name in REQUIRED_TEXT:
        if not (ROUTE_DIR / name).exists():
            issues.append(f"missing_text:{name}")

    coverage = json_payloads.get("WAVE2_FULL_LEDGER_COVERAGE_AUDIT.json", {})
    metrics = json_payloads.get("WAVE2_CANDIDATE_FUNNEL_QUALITY_METRICS.json", {})
    headline = metrics.get("headline", {}) if isinstance(metrics.get("headline"), dict) else {}

    expected_counts = {
        "WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl": 77,
        "WAVE2_EVERY_CANDIDATE_CAUSAL_MICROSCOPE.jsonl": 13246,
        "WAVE2_LIVE_AUTHORITY_FINAL_SAY_MATRIX.jsonl": 12775,
        "WAVE2_WAVE1_INPUT_INSPECTION_LEDGER.jsonl": 4,
        "WAVE2_STATIC_R_GEOMETRY_AUDIT_LEDGER.jsonl": 471,
        "WAVE2_TARGET_STOP_GEOMETRY_AND_PATH_ORDER_LEDGER.jsonl": 77,
        "WAVE2_SLTP_MODIFY_LIFECYCLE_SOURCE_COVERAGE_LEDGER.jsonl": 77,
        "WAVE2_COST_BROKER_NET_CAUSAL_LEDGER.jsonl": 77,
        "WAVE2_COST_SPREAD_SLIPPAGE_BROKER_NET_LEDGER.jsonl": 77,
        "WAVE2_COST_SOURCE_COVERAGE_AUDIT.jsonl": 77,
        "WAVE2_PROFIT_HARVEST_FILLED_TRADE_LEDGER.jsonl": 55,
        "WAVE2_FIRST_PASSAGE_TIME_TO_DESTINATION_LEDGER.jsonl": 55,
        "WAVE2_EXECUTION_ENTRY_PATH_MAE_MFE_TIME_LEDGER.jsonl": 55,
        "WAVE2_ENTRY_PATH_MAE_MFE_TTD_CAUSAL_LEDGER.jsonl": 55,
        "WAVE2_POOR_ENTRY_ADVERSE_EXCURSION_LEDGER.jsonl": 55,
        "WAVE2_TIME_TO_DESTINATION_AND_STALE_THESIS_LEDGER.jsonl": 55,
        "WAVE2_OVERNIGHT_NEXT_DAY_STALE_THESIS_LEDGER.jsonl": 55,
        "WAVE2_SHADOW_PATH_SOURCE_COVERAGE_LEDGER.jsonl": 8,
        "WAVE2_MAX_PROFITABILITY_AND_REVERSAL_LEDGER.jsonl": 29,
        "WAVE2_MFE_HARVEST_FAILURE_LEDGER.jsonl": 29,
        "WAVE2_PROFIT_PATH_CONSOLIDATION_REVERSAL_LEDGER.jsonl": 29,
        "WAVE2_ROW_LEVEL_CAUSAL_EXEMPLAR_LEDGER.jsonl": 8,
        "WAVE2_ALLOCATOR_DECISION_WINDOW_REPAIR_SOURCE_LEDGER.jsonl": 20,
        "WAVE2_ALLOCATOR_WINDOW_SOURCE_COVERAGE_AUDIT.jsonl": 6,
        "WAVE2_INFERRED_ALLOCATOR_DECISION_WINDOW_REPAIR_LEDGER.jsonl": 96,
        "WAVE2_SELECTOR_SCHEDULER_OPPORTUNITY_COST_LEDGER.jsonl": 96,
        "WAVE2_SELECTED_VS_ALTERNATIVE_OPPORTUNITY_COST_LEDGER.jsonl": 96,
        "WAVE2_BEST_TRADE_ALLOCATOR_OPPORTUNITY_COST_LEDGER.jsonl": 96,
        "WAVE2_PATH_REPAIR_SOURCE_COVERAGE_AUDIT.jsonl": 8,
        "WAVE2_TICK_REPAIRED_FIRST_PASSAGE_MFE_MAE_REVERSAL_LEDGER.jsonl": 55,
        "WAVE2_MARKET_SYSTEM_ROW_CLASSIFICATION_LEDGER.jsonl": 77,
        "WAVE2_SELECTOR_SELECTED_CELL_QUALITY_REPAIR_LEDGER.jsonl": 589,
        "WAVE2_ALLOCATOR_DECISION_WINDOW_REPLAY_LEDGER.jsonl": 96,
        "WAVE2_ZERO_TRADE_COUNTERFACTUAL_PATH_RANK_LEDGER.jsonl": 416,
        "WAVE2_FINAL_SAY_SELECTOR_SCHEDULER_JOIN_LEDGER.jsonl": 12775,
        "WAVE2_MT5_READONLY_MARKET_DATA_RECOVERY_LEDGER.jsonl": 6,
        "WAVE2_MARKET_DATA_GAP_PROXY_REPAIR_LEDGER.jsonl": 6,
        "WAVE2_PENDING_NOFILL_LIFECYCLE_RECONCILIATION.jsonl": 877,
        "WAVE2_DUAL_BROKER_AUTHORITY_DISPOSITION_LEDGER.jsonl": 7,
        "WAVE2_V3_TO_V4_DISPOSITION_LEDGER.jsonl": 13,
        "WAVE2_WAVE3_LANE_CONTRACTS.jsonl": EXPECTED_LANE_COUNT,
        "WAVE3_PER_LANE_CONTROLLING_PROMPTS.jsonl": EXPECTED_LANE_COUNT,
        "WAVE3_PER_LANE_ONE_LINE_STARTERS.jsonl": EXPECTED_LANE_COUNT,
        "WAVE2_QUESTION_COVERAGE_SATURATION_LEDGER.jsonl": 22,
        "WAVE2_CONTRADICTION_REPAIR_LEDGER.jsonl": 8,
        "WAVE2_SEMANTIC_INDEPENDENT_REVIEW_LEDGER.jsonl": 4,
    }
    for name, expected in expected_counts.items():
        actual = len(jsonl_rows.get(name, []))
        if actual != expected:
            issues.append(f"row_count_mismatch:{name}:expected={expected}:actual={actual}")

    if headline.get("wave1a_broker_trades") != 77:
        issues.append("headline_missing_77_broker_trades")
    if headline.get("wave1a_candidate_trade_records") != 471:
        issues.append("headline_missing_471_candidate_records")
    if headline.get("wave1b_live_authority_rows") != 12775:
        issues.append("headline_missing_12775_live_authority_rows")
    if round(float(headline.get("broker_real_net_pnl_cash", 999)), 2) != -859.69:
        issues.append("headline_broker_real_net_pnl_not_minus_859_69")
    if coverage.get("no_arbitrary_top_n_used") is not True:
        issues.append("coverage_audit_missing_no_top_n_true")
    if coverage.get("coverage_gap") in (None, ""):
        issues.append("coverage_audit_missing_incomplete_gap")

    contradiction_tokens = [
        "initial_causal_model_not_complete",
        '"wave3_allowed": false',
        "opened_not_saturated",
        "not_wave2_complete",
        "blocked_until_wave2_completion",
        "wave2_prompt_pack_verified_complete",
        "ready_for_owner_launch",
        "ready_for_wave3_owner_launch",
        "generated_hardened_ready_for_wave3_launch",
        "Status: Wave2 complete",
    ]
    scan_paths, source_exclusions, manifest_file_count = manifest_contradiction_scan_scope(
        json_payloads.get("WAVE2_OUTPUT_MANIFEST.json", {}),
        issues,
    )
    contradiction_hits: list[dict[str, str]] = []
    for path in scan_paths:
        rel_path = path.relative_to(REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        for token in contradiction_tokens:
            if token in text:
                contradiction_hits.append({"path": rel_path, "token": token})
                issues.append(f"unrepaired_contradiction_token:{rel_path}:{token}")

    context_anchor = json_payloads.get("WAVE2_CONTEXT_ANCHOR.json", {})
    if context_anchor.get("completion_status") == "incomplete_initial_spine_only":
        issues.append("context_anchor_active_completion_status_still_initial_spine_only")
    historical_anchor = context_anchor.get("historical_initial_anchor")
    if not isinstance(historical_anchor, dict) or historical_anchor.get("completion_status") != "incomplete_initial_spine_only":
        issues.append("context_anchor_missing_historical_initial_anchor_for_initial_spine_status")
    semantic_review_status = context_anchor.get("semantic_repair_review_status")
    if (
        not isinstance(semantic_review_status, dict)
        or semantic_review_status.get("active_status") != READINESS_STATUS
        or semantic_review_status.get("accepted_in_substance_by_central_orchestrator_review") is not True
    ):
        issues.append("context_anchor_missing_current_semantic_repair_review_status")
    contradiction_scan_summary = {
        "scope": "manifested_active_route_artifacts_from_WAVE2_OUTPUT_MANIFEST",
        "manifest_file_count": manifest_file_count,
        "active_route_artifacts_scanned": len(scan_paths),
        "excluded_source_file_count": len(source_exclusions),
        "excluded_source_files": source_exclusions,
        "stale_contradiction_hit_count": len(contradiction_hits),
        "token_count": len(contradiction_tokens),
        "self_verification_result_scanned": any(
            path.name == "WAVE2_INITIAL_CAUSAL_SPINE_VERIFICATION_RESULT.json" for path in scan_paths
        ),
        "exclusion_policy": "only Python generator/verifier source controls are excluded; builder source strings are classified as generator history, not active route state",
    }

    question_rows = jsonl_rows.get("WAVE2_ACTIVE_CAUSAL_QUESTION_STACK.jsonl", [])
    question_statuses = Counter(row.get("status") for row in question_rows)
    if len(question_rows) < 18:
        issues.append(f"question_stack_too_small:{len(question_rows)}")
    if not any(row.get("origin") == "row_anomaly" for row in question_rows):
        issues.append("question_stack_missing_row_anomaly")
    if not any(row.get("origin") == "source_gap" for row in question_rows):
        issues.append("question_stack_missing_source_gap")

    trade_rows = jsonl_rows.get("WAVE2_EVERY_TRADE_CAUSAL_MICROSCOPE.jsonl", [])
    if not all(row.get("broker_position_id") not in (None, "") for row in trade_rows):
        issues.append("trade_microscope_missing_broker_position_id")
    if not all(row.get("evidence_class") for row in trade_rows):
        issues.append("trade_microscope_missing_evidence_class")
    trade_missing_counts = Counter(field for row in trade_rows for field in row.get("missing_fields") or [])
    if trade_missing_counts.get("commission", 0) != 0:
        issues.append("trade_microscope_commission_still_marked_missing_after_cost_repair")
    if trade_missing_counts.get("swap", 0) != 0:
        issues.append("trade_microscope_swap_still_marked_missing_after_cost_repair")
    if trade_missing_counts.get("slippage_price", 0) != 7:
        issues.append(f"trade_microscope_slippage_missing_count_not_7:{trade_missing_counts.get('slippage_price', 0)}")
    if not all((row.get("metric_fields_used") or {}).get("commission_cash") is not None for row in trade_rows):
        issues.append("trade_microscope_missing_commission_cash_metric")
    if not all((row.get("metric_fields_used") or {}).get("swap_cash") is not None for row in trade_rows):
        issues.append("trade_microscope_missing_swap_cash_metric")
    if sum(1 for row in trade_rows if (row.get("metric_fields_used") or {}).get("slippage_source_status") == "shadow_slippage_joined_with_price") != 70:
        issues.append("trade_microscope_shadow_slippage_joined_count_not_70")
    candidate_microscope_rows = jsonl_rows.get("WAVE2_EVERY_CANDIDATE_CAUSAL_MICROSCOPE.jsonl", [])
    candidate_row_ids = [row.get("row_id") for row in candidate_microscope_rows]
    if len(candidate_row_ids) != len(set(candidate_row_ids)):
        issues.append("candidate_microscope_row_id_not_unique")
    if not any(row.get("duplicate_source_row_key") for row in candidate_microscope_rows):
        issues.append("candidate_microscope_missing_duplicate_source_row_key")

    input_rows = jsonl_rows.get("WAVE2_WAVE1_INPUT_INSPECTION_LEDGER.jsonl", [])
    if not all(row.get("route_verifier_ok") is True for row in input_rows):
        issues.append("not_all_input_verifiers_ok")
    if not all(row.get("artifact_audit_ok") is True for row in input_rows):
        issues.append("not_all_input_artifact_audits_ok")

    subagent_rows = jsonl_rows.get("WAVE2_DEEP_REVIEW_SUBAGENT_LEDGER.jsonl", [])
    if len(subagent_rows) < 9:
        issues.append("subagent_ledger_missing_expanded_review_roles")
    integrated_subagents = [
        row
        for row in subagent_rows
        if row.get("accepted_rejected_finding_disposition") not in {"spawned_pending_result_integration", "pending"}
    ]
    if len(integrated_subagents) < 9:
        issues.append("subagent_ledger_missing_all_completed_findings")

    intelligence_rows = jsonl_rows.get("WAVE2_NEWLY_DISCOVERED_INTELLIGENCE_LEDGER.jsonl", [])
    if len(intelligence_rows) < 12:
        issues.append("newly_discovered_intelligence_ledger_too_small")

    proxy_summary = json_payloads.get("WAVE2_MARKET_DATA_GAP_PROXY_REPAIR_SUMMARY.json", {})
    proxy_rows = jsonl_rows.get("WAVE2_MARKET_DATA_GAP_PROXY_REPAIR_LEDGER.jsonl", [])
    if proxy_summary.get("row_count") != 6:
        issues.append("market_data_gap_proxy_summary_missing_6_rows")
    if proxy_summary.get("exact_full_tick_claims_created") != 0:
        issues.append("market_data_gap_proxy_promoted_exact_tick_claim")
    if not all(
        row.get("result_use_status") == "market_data_recovery_proxy_audit_not_broker_real_path_not_runtime_intent"
        for row in proxy_rows
    ):
        issues.append("market_data_gap_proxy_rows_missing_proxy_result_boundary")

    static_inventory_rows = jsonl_rows.get("WAVE2_STATIC_R_GEOMETRY_SOURCE_INVENTORY.jsonl", [])
    if len(static_inventory_rows) < 8:
        issues.append("static_r_source_inventory_too_small")
    static_summary = json_payloads.get("WAVE2_STATIC_R_GEOMETRY_AUDIT_SUMMARY.json", {})
    if static_summary.get("candidate_trade_record_rows") != 471:
        issues.append("static_r_summary_missing_471_candidate_rows")
    if static_summary.get("broker_order_geometry_rows") != 77:
        issues.append("static_r_summary_missing_77_broker_order_rows")
    semantic_conclusion = str(static_summary.get("semantic_conclusion") or "")
    if "raw 1.5R" not in semantic_conclusion or "near 3R" not in semantic_conclusion:
        issues.append("static_r_summary_missing_semantic_split_conclusion")

    broker_order_rows = jsonl_rows.get("WAVE2_TARGET_STOP_GEOMETRY_AND_PATH_ORDER_LEDGER.jsonl", [])
    if not all(row.get("initial_broker_order_target_multiple_r") is not None for row in broker_order_rows):
        issues.append("broker_order_geometry_missing_initial_target_multiple")
    if not any(row.get("bucket_0_25") == "near_3r" for row in broker_order_rows):
        issues.append("broker_order_geometry_missing_near_3r_bucket")
    sltp_rows = jsonl_rows.get("WAVE2_SLTP_MODIFY_LIFECYCLE_SOURCE_COVERAGE_LEDGER.jsonl", [])
    if not all(row.get("sltp_order_count_for_position") == 1 for row in sltp_rows):
        issues.append("sltp_source_coverage_expected_single_initial_sltp_order_per_position")
    if any(row.get("has_multiple_sltp_states_in_broker_export") is True for row in sltp_rows):
        issues.append("sltp_source_coverage_unexpected_multiple_sltp_states_without_lifecycle_classifier")
    if not all(row.get("coverage_status") == "initial_sltp_present_full_modify_lifecycle_not_captured" for row in sltp_rows):
        issues.append("sltp_source_coverage_missing_initial_present_not_full_lifecycle_status")
    blocker_rows_for_static = jsonl_rows.get("WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl", [])
    static_blockers = [row for row in blocker_rows_for_static if row.get("blocker_id") == "wave2_static_r_geometry_join"]
    if not static_blockers or static_blockers[0].get("status") != "initial_sltp_geometry_repair_complete_full_modify_lifecycle_capture_required":
        issues.append("blocker_static_r_geometry_not_marked_initial_sltp_repaired_capture_required")

    cost_summary = json_payloads.get("WAVE2_COST_BROKER_NET_SUMMARY.json", {})
    if round(float(cost_summary.get("broker_net_cash_from_deals_sum", 999)), 2) != -859.69:
        issues.append("cost_summary_broker_net_not_minus_859_69")
    if float(cost_summary.get("gross_deal_profit_cash_sum", -1)) <= 0:
        issues.append("cost_summary_gross_profit_not_positive")
    if float(cost_summary.get("cost_drag_cash_sum", 1)) >= 0:
        issues.append("cost_summary_cost_drag_not_negative")
    cost_source_repair = cost_summary.get("source_coverage_repair", {})
    if not isinstance(cost_source_repair, dict) or cost_source_repair.get("cost_source_coverage_rows") != 77:
        issues.append("cost_summary_missing_source_coverage_repair_77_rows")
    if cost_source_repair.get("matched_shadow_slippage_positions") != 70:
        issues.append("cost_summary_matched_shadow_slippage_positions_not_70")
    if cost_source_repair.get("shadow_slippage_source_gap_positions") != 7:
        issues.append("cost_summary_shadow_slippage_source_gap_positions_not_7")

    cost_source_rows = jsonl_rows.get("WAVE2_COST_SOURCE_COVERAGE_AUDIT.jsonl", [])
    cost_spread_rows = jsonl_rows.get("WAVE2_COST_SPREAD_SLIPPAGE_BROKER_NET_LEDGER.jsonl", [])
    for name, rows in {
        "WAVE2_COST_SOURCE_COVERAGE_AUDIT.jsonl": cost_source_rows,
        "WAVE2_COST_SPREAD_SLIPPAGE_BROKER_NET_LEDGER.jsonl": cost_spread_rows,
    }.items():
        status_counts = Counter(row.get("slippage_source_status") for row in rows)
        if status_counts.get("shadow_slippage_joined_with_price") != 70:
            issues.append(f"cost_source_shadow_slippage_joined_count_not_70:{name}")
        if status_counts.get("shadow_slippage_not_joined_source_gap") != 7:
            issues.append(f"cost_source_shadow_slippage_gap_count_not_7:{name}")
        if not all(row.get("broker_deal_source_status") == "broker_truth_deal_cost_joined" for row in rows):
            issues.append(f"cost_source_rows_missing_broker_deal_truth:{name}")
        if not all(row.get("broker_order_source_status") == "broker_truth_orders_joined" for row in rows):
            issues.append(f"cost_source_rows_missing_broker_order_truth:{name}")
        if not all(row.get("commission_swap_source_status") == "broker_deal_truth_joined" for row in rows):
            issues.append(f"cost_source_rows_missing_commission_swap_deal_truth:{name}")
        if not all(row.get("result_use_status") == "cost_truth_joined_shadow_slippage_diagnostic_not_original_runtime_packet" for row in rows):
            issues.append(f"cost_source_rows_wrong_result_use_status:{name}")
        if not all(
            "LiveDecisionPacketV4_pretrade_cost_snapshot" in set(row.get("missing_runtime_truth") or [])
            for row in rows
        ):
            issues.append(f"cost_source_rows_missing_runtime_packet_gap:{name}")
        if any(
            row.get("slippage_source_status") == "shadow_slippage_joined_with_price"
            and not ((row.get("shadow_slippage_coverage") or {}).get("slippage_price_values"))
            for row in rows
        ):
            issues.append(f"cost_source_joined_rows_missing_slippage_price_values:{name}")
    if cost_source_rows and cost_spread_rows:
        if {row.get("broker_position_id") for row in cost_source_rows} != {row.get("broker_position_id") for row in cost_spread_rows}:
            issues.append("cost_source_and_spread_position_sets_differ")

    packet_contract = json_payloads.get("WAVE2_LIVE_DECISION_PACKET_V4_CAPTURE_CONTRACT.json", {})
    required_groups = packet_contract.get("required_field_groups") if isinstance(packet_contract.get("required_field_groups"), list) else []
    if len(required_groups) < 10:
        issues.append("packet_v4_contract_required_groups_too_small")

    validation_contract = json_payloads.get("WAVE2_VALIDATION_ANTI_OVERFIT_CONTRACT.json", {})
    if len(validation_contract.get("sealed_validation_requirements", [])) < 6:
        issues.append("validation_contract_missing_sealed_requirements")

    profit_rows = jsonl_rows.get("WAVE2_PROFIT_HARVEST_FILLED_TRADE_LEDGER.jsonl", [])
    if not any("loser_positive_mfe_before_loss" in set(row.get("harvest_tags") or []) for row in profit_rows):
        issues.append("profit_harvest_missing_positive_mfe_loser_tag")
    if not any("partial_be_runner_no_recorded_partial_close" in set(row.get("harvest_tags") or []) for row in profit_rows):
        issues.append("profit_harvest_missing_no_partial_close_tag")
    loser_rows = jsonl_rows.get("WAVE2_LOSER_MFE_REPAIR_LEDGER.jsonl", [])
    if len(loser_rows) < 29:
        issues.append(f"loser_mfe_repair_ledger_too_small:{len(loser_rows)}")
    if not any(row.get("repair_status") == "positive_mfe_loser_requires_harvest_rule_counterfactual" for row in loser_rows):
        issues.append("loser_mfe_repair_missing_positive_mfe_status")

    first_passage_rows = jsonl_rows.get("WAVE2_FIRST_PASSAGE_TIME_TO_DESTINATION_LEDGER.jsonl", [])
    first_passage_statuses = Counter(row.get("status") for row in first_passage_rows)
    if first_passage_statuses.get("source_bound_first_passage_computed") != 49:
        issues.append("first_passage_rows_source_bound_count_not_49")
    if first_passage_statuses.get("partial_or_missing_tick_window_source_gap") != 6:
        issues.append("first_passage_rows_source_gap_count_not_6")
    if not all(str(row.get("row_id", "")).startswith("first_passage_ttd:") for row in first_passage_rows):
        issues.append("first_passage_rows_still_look_like_placeholder_alias")
    if not all(row.get("source_tick_repair_row_id") for row in first_passage_rows):
        issues.append("first_passage_rows_missing_tick_repair_source_id")
    if not any(row.get("destination_efficiency") == "reached_1r_slow_or_stale" for row in first_passage_rows):
        issues.append("first_passage_rows_missing_slow_stale_1r_case")
    if not any(((row.get("first_passage") or {}).get("0.25") or {}).get("hit") is True for row in first_passage_rows):
        issues.append("first_passage_rows_missing_plus_0_25_hits")

    entry_path_rows = jsonl_rows.get("WAVE2_EXECUTION_ENTRY_PATH_MAE_MFE_TIME_LEDGER.jsonl", [])
    if not all("tick_mfe_r" in row and "tick_mae_r" in row for row in entry_path_rows):
        issues.append("execution_entry_path_rows_missing_tick_mfe_mae_fields")
    if not all(str(row.get("row_id", "")).startswith("entry_path_mae_mfe_ttd:") for row in entry_path_rows):
        issues.append("execution_entry_path_rows_still_look_like_placeholder_alias")
    if not any("mfe_delta_ge_1r" in set(row.get("ledger_basis_discrepancy_flags") or []) for row in entry_path_rows):
        issues.append("execution_entry_path_rows_missing_mfe_delta_discrepancy")

    poor_entry_rows = jsonl_rows.get("WAVE2_POOR_ENTRY_ADVERSE_EXCURSION_LEDGER.jsonl", [])
    poor_entry_statuses = Counter(row.get("entry_quality_status") for row in poor_entry_rows)
    if poor_entry_statuses.get("deep_adverse_before_first_useful_profit", 0) < 7:
        issues.append("poor_entry_rows_missing_deep_adverse_cases")
    if poor_entry_statuses.get("adverse_before_first_useful_profit", 0) < 12:
        issues.append("poor_entry_rows_missing_adverse_before_profit_cases")
    if poor_entry_statuses.get("source_gap_no_tick_mae", 0) != 1:
        issues.append("poor_entry_rows_source_gap_no_tick_mae_not_1")

    stale_rows = jsonl_rows.get("WAVE2_TIME_TO_DESTINATION_AND_STALE_THESIS_LEDGER.jsonl", [])
    stale_statuses = Counter(row.get("stale_thesis_status") for row in stale_rows)
    if stale_statuses.get("stale_hold_ge_24h", 0) < 2:
        issues.append("stale_thesis_rows_missing_24h_holds")
    if stale_statuses.get("stale_hold_ge_12h", 0) < 5:
        issues.append("stale_thesis_rows_missing_12h_holds")
    if stale_statuses.get("stale_hold_ge_6h", 0) < 6:
        issues.append("stale_thesis_rows_missing_6h_holds")
    if not all(row.get("destination_efficiency") for row in stale_rows):
        issues.append("stale_thesis_rows_missing_destination_efficiency")

    max_profit_rows = jsonl_rows.get("WAVE2_MAX_PROFITABILITY_AND_REVERSAL_LEDGER.jsonl", [])
    if not all(row.get("path_source_status") == "tick_full_window_source_bound" for row in max_profit_rows):
        issues.append("max_profitability_rows_not_all_full_tick_source_bound")
    if not all(str(row.get("row_id", "")).startswith("loser_mfe_harvest:") for row in max_profit_rows):
        issues.append("max_profitability_rows_still_look_like_placeholder_alias")
    harvest_statuses = Counter(row.get("harvest_failure_status") for row in max_profit_rows)
    if harvest_statuses.get("loser_reached_0_5r_before_loss", 0) < 10:
        issues.append("harvest_failure_rows_missing_loser_0_5r_before_loss_cases")
    if harvest_statuses.get("loser_reached_0_25r_before_loss", 0) < 8:
        issues.append("harvest_failure_rows_missing_loser_0_25r_before_loss_cases")
    if any(str(row.get("harvest_failure_status", "")).startswith("winner_or_breakeven") for row in max_profit_rows):
        issues.append("harvest_failure_loser_rows_have_winner_or_breakeven_status")
    if not all(row.get("near_mfe_within_0_10r_tick_count") is not None for row in max_profit_rows):
        issues.append("max_profitability_rows_missing_near_mfe_dwell_proxy")
    near_mfe_range_fields = [
        "near_mfe_within_0_10r_first_time_utc",
        "near_mfe_within_0_10r_last_time_utc",
        "near_mfe_within_0_10r_min_r",
        "near_mfe_within_0_10r_max_r",
        "near_mfe_within_0_10r_range_r",
    ]
    for field in near_mfe_range_fields:
        if not all(row.get(field) is not None for row in max_profit_rows):
            issues.append(f"max_profitability_rows_missing_{field}")
    blocker_rows = jsonl_rows.get("WAVE2_BLOCKER_AND_REPAIR_LEDGER.jsonl", [])
    loser_blockers = [row for row in blocker_rows if row.get("blocker_id") == "wave2_loser_mfe_consolidation_reversal"]
    if not loser_blockers or loser_blockers[0].get("status") != "tick_loser_mfe_consolidation_reversal_repair_complete_v4_policy_required":
        issues.append("blocker_loser_mfe_consolidation_reversal_not_marked_tick_repaired")

    shadow_rows = jsonl_rows.get("WAVE2_SHADOW_PATH_SOURCE_COVERAGE_LEDGER.jsonl", [])
    if not any(row.get("source_path") == "shadow_logs/candidate_ltf_path_order.jsonl" and row.get("row_count", 0) > 10000 for row in shadow_rows):
        issues.append("shadow_path_source_coverage_missing_ltf_path_order_rows")
    allocator_source_rows = jsonl_rows.get("WAVE2_ALLOCATOR_WINDOW_SOURCE_COVERAGE_AUDIT.jsonl", [])
    if not allocator_source_rows:
        issues.append("allocator_window_source_coverage_missing")
    if any((row.get("key_coverage") or {}).get("decision_window_id", 0) for row in allocator_source_rows):
        issues.append("allocator_window_source_coverage_unexpected_decision_window_id_present")
    if any((row.get("key_coverage") or {}).get("candidate_set_id", 0) for row in allocator_source_rows):
        issues.append("allocator_window_source_coverage_unexpected_candidate_set_id_present")
    if not any(row.get("source_id") == "live_opportunity_clusters" and (row.get("key_coverage") or {}).get("opportunity_id", 0) > 7000 for row in allocator_source_rows):
        issues.append("allocator_window_source_coverage_missing_opportunity_cluster_ids")
    inferred_allocator_rows = jsonl_rows.get("WAVE2_INFERRED_ALLOCATOR_DECISION_WINDOW_REPAIR_LEDGER.jsonl", [])
    if not any(row.get("has_same_timestamp_alternatives_for_filled") is True for row in inferred_allocator_rows):
        issues.append("inferred_allocator_missing_filled_windows_with_alternatives")
    if not all(row.get("evidence_class") == "source_bound_reconstruction_not_original_runtime_intent" for row in inferred_allocator_rows):
        issues.append("inferred_allocator_wrong_evidence_class")
    if not all(row.get("result_use_status") == "diagnostic_only_not_final_allocator_truth" for row in inferred_allocator_rows):
        issues.append("inferred_allocator_wrong_result_use_status")

    required_missing_allocator_truth = {
        "original_decision_window_id",
        "original_candidate_set_id",
        "runtime_selected_candidate_id",
        "open_position_snapshot",
        "pending_order_snapshot",
        "stale_exposure_opportunity_cost",
        "zero_trade_value",
        "broker_net_ev_per_unit_risk",
        "fill_probability_at_decision",
    }
    inferred_by_id = {row.get("inferred_window_id"): row for row in inferred_allocator_rows}
    inferred_window_ids = set(inferred_by_id)
    inferred_window_times = {row.get("window_time_utc") for row in inferred_allocator_rows}
    if sum(int(row.get("candidate_rows") or 0) for row in inferred_allocator_rows) != 471:
        issues.append("inferred_allocator_candidate_row_sum_not_471")
    if sum(int(row.get("filled_count") or 0) for row in inferred_allocator_rows) != 55:
        issues.append("inferred_allocator_filled_sum_not_55")
    if sum(int(row.get("alternative_count") or 0) for row in inferred_allocator_rows) != 416:
        issues.append("inferred_allocator_alternative_sum_not_416")
    if sum(1 for row in inferred_allocator_rows if int(row.get("filled_count") or 0) > 0) != 37:
        issues.append("inferred_allocator_filled_window_count_not_37")
    if sum(1 for row in inferred_allocator_rows if int(row.get("filled_count") or 0) == 0) != 59:
        issues.append("inferred_allocator_zero_fill_window_count_not_59")
    if sum(1 for row in inferred_allocator_rows if int(row.get("filled_count") or 0) > 0 and int(row.get("alternative_count") or 0) > 0) != 28:
        issues.append("inferred_allocator_filled_with_alternative_window_count_not_28")

    old_summary_keys = {"ledger_id", "surface", "finding", "metrics"}
    allocator_target_files = [
        "WAVE2_SELECTOR_SCHEDULER_OPPORTUNITY_COST_LEDGER.jsonl",
        "WAVE2_SELECTED_VS_ALTERNATIVE_OPPORTUNITY_COST_LEDGER.jsonl",
        "WAVE2_BEST_TRADE_ALLOCATOR_OPPORTUNITY_COST_LEDGER.jsonl",
    ]
    expected_artifact_families = {
        "WAVE2_SELECTOR_SCHEDULER_OPPORTUNITY_COST_LEDGER.jsonl": "selector_scheduler_per_window_opportunity_cost",
        "WAVE2_SELECTED_VS_ALTERNATIVE_OPPORTUNITY_COST_LEDGER.jsonl": "selected_vs_alternative_opportunity_cost",
        "WAVE2_BEST_TRADE_ALLOCATOR_OPPORTUNITY_COST_LEDGER.jsonl": "best_trade_allocator_opportunity_cost",
    }
    target_file_texts: dict[str, str] = {}
    for name in allocator_target_files:
        rows = jsonl_rows.get(name, [])
        if len(rows) == 4:
            issues.append(f"allocator_opportunity_ledger_still_four_row_summary:{name}")
        if rows and set(rows[0]).issubset(old_summary_keys | {"source_paths", "status", "v4_requirement"}):
            issues.append(f"allocator_opportunity_ledger_old_summary_schema:{name}")
        row_ids = [row.get("row_id") for row in rows]
        if len(row_ids) != len(set(row_ids)):
            issues.append(f"allocator_opportunity_row_id_not_unique:{name}")
        if {row.get("inferred_window_id") for row in rows} != inferred_window_ids:
            issues.append(f"allocator_opportunity_window_id_set_mismatch:{name}")
        if {row.get("window_time_utc") for row in rows} != inferred_window_times:
            issues.append(f"allocator_opportunity_window_time_set_mismatch:{name}")
        if sum(int(row.get("candidate_rows") or 0) for row in rows) != 471:
            issues.append(f"allocator_opportunity_candidate_row_sum_not_471:{name}")
        if sum(int(row.get("filled_count") or 0) for row in rows) != 55:
            issues.append(f"allocator_opportunity_filled_sum_not_55:{name}")
        if sum(int(row.get("alternative_count") or 0) for row in rows) != 416:
            issues.append(f"allocator_opportunity_alternative_sum_not_416:{name}")
        if not all(row.get("artifact_family") == expected_artifact_families[name] for row in rows):
            issues.append(f"allocator_opportunity_wrong_artifact_family:{name}")
        if not all(row.get("evidence_class") == "source_bound_reconstruction_not_original_runtime_intent" for row in rows):
            issues.append(f"allocator_opportunity_wrong_evidence_class:{name}")
        if not all(row.get("result_use_status") == "diagnostic_only_not_final_allocator_truth" for row in rows):
            issues.append(f"allocator_opportunity_wrong_result_use_status:{name}")
        if not all(row.get("allocator_intent_status") == "original_runtime_allocator_intent_not_generatable_from_current_sources" for row in rows):
            issues.append(f"allocator_opportunity_missing_runtime_intent_boundary:{name}")
        if not all(required_missing_allocator_truth.issubset(set(row.get("missing_runtime_truth") or [])) for row in rows):
            issues.append(f"allocator_opportunity_missing_runtime_truth_fields:{name}")
        if any("final_allocator_truth" in str(row.get("status") or "") or "live_authority" in str(row.get("status") or "") for row in rows):
            issues.append(f"allocator_opportunity_status_overclaims_truth:{name}")
        for row in rows:
            inferred = inferred_by_id.get(row.get("inferred_window_id"))
            if not inferred:
                continue
            if int(row.get("candidate_rows") or 0) != int(inferred.get("candidate_rows") or 0):
                issues.append(f"allocator_opportunity_candidate_count_mismatch:{name}:{row.get('inferred_window_id')}")
            if int(row.get("filled_count") or 0) != int(inferred.get("filled_count") or 0):
                issues.append(f"allocator_opportunity_filled_count_mismatch:{name}:{row.get('inferred_window_id')}")
            if int(row.get("alternative_count") or 0) != int(inferred.get("alternative_count") or 0):
                issues.append(f"allocator_opportunity_alternative_count_mismatch:{name}:{row.get('inferred_window_id')}")
            if row.get("selected_or_filled_candidate_ids") != inferred.get("selected_or_filled_candidate_ids"):
                issues.append(f"allocator_opportunity_selected_ids_mismatch:{name}:{row.get('inferred_window_id')}")
            if row.get("rejected_skipped_no_trade_candidate_ids") != inferred.get("rejected_skipped_no_trade_candidate_ids"):
                issues.append(f"allocator_opportunity_alternative_ids_mismatch:{name}:{row.get('inferred_window_id')}")
        if any(int(row.get("filled_count") or 0) > 0 and not row.get("selected_broker_real_result") for row in rows):
            issues.append(f"allocator_opportunity_filled_rows_missing_selected_detail:{name}")
        if any(int(row.get("alternative_count") or 0) > 0 and not row.get("best_rejected_or_skipped_by_source_expectancy") for row in rows):
            issues.append(f"allocator_opportunity_alternative_rows_missing_best_alt:{name}")
        filled_alt_deltas = [
            (((row.get("selected_vs_best_delta") or {}).get("best_filled_exact_r_minus_best_alt_expectancy_r")))
            for row in rows
            if int(row.get("filled_count") or 0) > 0 and int(row.get("alternative_count") or 0) > 0
        ]
        if sum(value is not None for value in filled_alt_deltas) != 28:
            issues.append(f"allocator_opportunity_filled_alt_delta_count_not_28:{name}")
        target_file_texts[name] = (ROUTE_DIR / name).read_text(encoding="utf-8") if (ROUTE_DIR / name).exists() else ""
    if len(set(target_file_texts.values())) != len(target_file_texts):
        issues.append("allocator_opportunity_ledgers_are_byte_identical_aliases")

    path_source_rows = jsonl_rows.get("WAVE2_PATH_REPAIR_SOURCE_COVERAGE_AUDIT.jsonl", [])
    if not any(row.get("source_id") == "candidate_ltf_path_order" and row.get("row_count", 0) > 10000 for row in path_source_rows):
        issues.append("path_repair_source_coverage_missing_ltf_path_order_rows")
    if not any(row.get("source_id") == "partial_close_shadow_log" and (row.get("key_coverage") or {}).get("trade_id", 0) == 10 for row in path_source_rows):
        issues.append("path_repair_source_coverage_missing_partial_close_trade_ids")

    tick_audit = json_payloads.get("WAVE2_TICK_REPAIR_SOURCE_COVERAGE_AUDIT.json", {})
    if tick_audit.get("filled_rows") != 55:
        issues.append("tick_repair_audit_missing_55_filled_rows")
    if tick_audit.get("tick_repaired_full_rows") != 49:
        issues.append("tick_repair_audit_full_repaired_not_49")
    if tick_audit.get("tick_partial_rows") != 5:
        issues.append("tick_repair_audit_partial_rows_not_5")
    if tick_audit.get("tick_no_window_rows") != 1:
        issues.append("tick_repair_audit_no_window_rows_not_1")
    if tick_audit.get("tick_blocked_rows") != 0:
        issues.append("tick_repair_audit_has_blocked_rows")
    if tick_audit.get("loser_rows") != 29 or tick_audit.get("loser_full_tick_repaired_rows") != 29:
        issues.append("tick_repair_audit_loser_full_repair_not_29_of_29")
    if tick_audit.get("broker_truth_minus_3h_close_time_repairs") != 12:
        issues.append("tick_repair_audit_broker_time_repairs_not_12")
    if tick_audit.get("parquet_parse_error_count") != 0:
        issues.append("tick_repair_audit_parse_errors_nonzero")
    if "ETHUSD/2026-06-01" not in (tick_audit.get("missing_tick_date_counts") or {}):
        issues.append("tick_repair_audit_missing_ethusd_2026_06_01_gap")

    tick_rows = jsonl_rows.get("WAVE2_TICK_REPAIRED_FIRST_PASSAGE_MFE_MAE_REVERSAL_LEDGER.jsonl", [])
    tick_status_counts = Counter(row.get("tick_repair_status") for row in tick_rows)
    if tick_status_counts.get("full_tick_window_recomputed") != 49:
        issues.append("tick_repair_rows_full_status_not_49")
    if tick_status_counts.get("partial_tick_window_missing_source_dates_or_parse_errors") != 5:
        issues.append("tick_repair_rows_partial_status_not_5")
    if tick_status_counts.get("tick_window_no_rows_in_entry_exit_interval") != 1:
        issues.append("tick_repair_rows_no_window_status_not_1")
    if not all(row.get("evidence_class") == "tick_parquet_recompute_with_trade_record_and_broker_truth_timestamp_repair" for row in tick_rows):
        issues.append("tick_repair_rows_wrong_evidence_class")
    if not all(row.get("result_use_status") == "source_bound_path_repair_not_runtime_intent" for row in tick_rows):
        issues.append("tick_repair_rows_wrong_result_use_status")
    full_tick_rows = [row for row in tick_rows if row.get("tick_repair_status") == "full_tick_window_recomputed"]
    if not all(row.get("usable_for_full_first_passage") is True and row.get("tick_count", 0) > 0 for row in full_tick_rows):
        issues.append("tick_repair_full_rows_not_all_usable_with_ticks")
    if not all(set((row.get("first_passage") or {}).keys()) == {"-1.0", "0.0", "0.25", "0.5", "1.0", "1.5", "2.0", "3.0"} for row in full_tick_rows):
        issues.append("tick_repair_full_rows_missing_first_passage_thresholds")
    if not any(row.get("broker_position_id") == 242383463 and row.get("tick_repair_status") == "tick_window_no_rows_in_entry_exit_interval" for row in tick_rows):
        issues.append("tick_repair_missing_eurjpy_no_window_gap_row")
    if not any(row.get("broker_position_id") == 242442562 and "mfe_delta_ge_1r" in set(row.get("ledger_basis_discrepancy_flags") or []) and abs(float(row.get("tick_mfe_r")) - 0.343998) < 0.001 for row in tick_rows):
        issues.append("tick_repair_missing_nas100_mfe_collapse_discrepancy")
    if not any(row.get("broker_position_id") == 242731196 and ((row.get("first_passage") or {}).get("0.25") or {}).get("hit") is True for row in tick_rows):
        issues.append("tick_repair_missing_audjpy_first_plus_0_25r")
    if not any(row.get("broker_position_id") == 242597416 and ((row.get("first_passage") or {}).get("1.0") or {}).get("hit") is True for row in tick_rows):
        issues.append("tick_repair_missing_uk100_first_plus_1r")
    if sum(1 for row in tick_rows if "tick_mfe_ge_1r_no_recorded_partial_close" in set(row.get("ledger_basis_discrepancy_flags") or [])) < 6:
        issues.append("tick_repair_missing_six_ge_1r_no_partial_flags")
    if sum(1 for row in full_tick_rows if row.get("loser_positive_mfe_before_loss_tick_repaired") is True) < 20:
        issues.append("tick_repair_positive_mfe_loser_count_too_low")

    market_system_rows = jsonl_rows.get("WAVE2_MARKET_SYSTEM_ROW_CLASSIFICATION_LEDGER.jsonl", [])
    market_statuses = Counter(row.get("primary_disposition") for row in market_system_rows)
    if sum(market_statuses.values()) != 77:
        issues.append("market_system_row_count_not_77")
    for required_disposition in {
        "bad_market_system_mismatch",
        "bad_system_logic",
        "bad_execution_cost_broker",
        "bad_data_capture",
        "unknown_with_source_gap",
    }:
        if market_statuses.get(required_disposition, 0) == 0:
            issues.append(f"market_system_missing_disposition:{required_disposition}")
    if not all(row.get("evidence_class") == "broker-real cash plus source-bound path/cost/health diagnostics" for row in market_system_rows):
        issues.append("market_system_wrong_evidence_class")
    if not all(row.get("status") == "row_level_market_system_classified_not_full_runtime_whiteboard" for row in market_system_rows):
        issues.append("market_system_wrong_status")
    if not any("dominant_damage_symbol" in set(row.get("supporting_evidence_tags") or []) for row in market_system_rows):
        issues.append("market_system_missing_dominant_damage_tag")

    selector_repair_rows = jsonl_rows.get("WAVE2_SELECTOR_SELECTED_CELL_QUALITY_REPAIR_LEDGER.jsonl", [])
    selector_repair_statuses = Counter(row.get("repair_status") for row in selector_repair_rows)
    if selector_repair_statuses.get("selected_cell_rows_present_win_pf_not_captured") != 562:
        issues.append("selector_repair_rows_present_win_pf_not_captured_not_562")
    if selector_repair_statuses.get("selected_cell_quality_fields_missing_fail_closed") != 27:
        issues.append("selector_repair_fail_closed_missing_count_not_27")
    if not all(row.get("result_use_status") == "selector_v4_admission_requirement_not_live_selector_proof" for row in selector_repair_rows):
        issues.append("selector_repair_wrong_result_use_status")

    allocator_replay_rows = jsonl_rows.get("WAVE2_ALLOCATOR_DECISION_WINDOW_REPLAY_LEDGER.jsonl", [])
    if sum(int(row.get("candidate_rows") or 0) for row in allocator_replay_rows) != 471:
        issues.append("allocator_replay_candidate_row_sum_not_471")
    if sum(int(row.get("filled_count") or 0) for row in allocator_replay_rows) != 55:
        issues.append("allocator_replay_filled_sum_not_55")
    if sum(int(row.get("alternative_count") or 0) for row in allocator_replay_rows) != 416:
        issues.append("allocator_replay_alternative_sum_not_416")
    if not all(row.get("replay_status") == "same_evidence_class_replay_materialized_original_runtime_intent_non_generatable" for row in allocator_replay_rows):
        issues.append("allocator_replay_wrong_status")
    if not all(row.get("result_use_status") == "diagnostic_allocator_replay_not_original_runtime_allocator_truth" for row in allocator_replay_rows):
        issues.append("allocator_replay_wrong_result_use_status")

    zero_rank_rows = jsonl_rows.get("WAVE2_ZERO_TRADE_COUNTERFACTUAL_PATH_RANK_LEDGER.jsonl", [])
    if len(zero_rank_rows) != 416:
        issues.append("zero_trade_rank_row_count_not_416")
    if not all(row.get("rank_status") == "counterfactual_path_rank_source_gap_exact_row_preserved" for row in zero_rank_rows):
        issues.append("zero_trade_rank_wrong_status")
    if not all(row.get("result_use_status") == "zero_trade_quality_evidence_not_realized_alternative_counterfactual" for row in zero_rank_rows):
        issues.append("zero_trade_rank_wrong_result_use_status")
    if not any(((row.get("source_bound_expectancy_context") or {}).get("selected_cell_rows") or 0) > 50000 for row in zero_rank_rows):
        issues.append("zero_trade_rank_missing_selected_cell_context")

    final_say_join_rows = jsonl_rows.get("WAVE2_FINAL_SAY_SELECTOR_SCHEDULER_JOIN_LEDGER.jsonl", [])
    final_say_join_statuses = Counter(row.get("join_status") for row in final_say_join_rows)
    if final_say_join_statuses.get("final_say_preserved_packet_incomplete", 0) < 12000:
        issues.append("final_say_join_packet_incomplete_count_too_low")
    if final_say_join_statuses.get("final_say_preserved_packet_fields_present", 0) < 400:
        issues.append("final_say_join_packet_present_count_too_low")
    if not any("cost_swap_slippage_state" in set(row.get("missing_packet_fields") or []) for row in final_say_join_rows):
        issues.append("final_say_join_missing_cost_packet_gap")
    if not any("scheduler_v3_runtime_authority" in set(row.get("missing_packet_fields") or []) for row in final_say_join_rows):
        issues.append("final_say_join_missing_scheduler_authority_gap")

    mt5_recovery_rows = jsonl_rows.get("WAVE2_MT5_READONLY_MARKET_DATA_RECOVERY_LEDGER.jsonl", [])
    mt5_statuses = Counter(row.get("recovery_status") for row in mt5_recovery_rows)
    if sum(mt5_statuses.values()) != 6:
        issues.append("mt5_recovery_row_count_not_6")
    if mt5_statuses.get("not_found_in_current_mt5_cache_requires_readonly_chart_export_or_source_pull", 0) < 4:
        issues.append("mt5_recovery_missing_not_found_boundaries")
    if mt5_statuses.get("mt5_ftmo_tick_cache_present_requires_parser_or_export", 0) < 2:
        issues.append("mt5_recovery_missing_ftmo_tick_cache_boundaries")
    if not all(row.get("result_use_status") == "market_data_recovery_audit_not_broker_mutation_not_runtime_intent" for row in mt5_recovery_rows):
        issues.append("mt5_recovery_wrong_result_use_status")
    if not all("FTMO-Server3" in {probe.get("server") for probe in row.get("mt5_probe_results", [])} for row in mt5_recovery_rows):
        issues.append("mt5_recovery_missing_ftmo_server_probe")

    pending_summary = json_payloads.get("WAVE2_PENDING_NOFILL_SOURCE_COVERAGE_SUMMARY.json", {})
    if pending_summary.get("lifecycle_rows") != 877 or pending_summary.get("reconciled_rows") != 877:
        issues.append("pending_nofill_summary_missing_877_reconciled_rows")
    if pending_summary.get("join_backfill_rows") != 874:
        issues.append("pending_nofill_summary_join_backfill_rows_not_874")
    if pending_summary.get("audit_rows") != 313:
        issues.append("pending_nofill_summary_audit_rows_not_313")
    if pending_summary.get("forward_capture_rows") != 446:
        issues.append("pending_nofill_summary_forward_capture_rows_not_446")
    if pending_summary.get("distinct_lifecycle_trade_ids") != 92:
        issues.append("pending_nofill_summary_distinct_trade_ids_not_92")
    pending_fill_counts = pending_summary.get("broker_fill_state_counts") or {}
    if pending_fill_counts.get("not_filled") != 807 or pending_fill_counts.get("filled") != 70:
        issues.append("pending_nofill_summary_fill_counts_not_807_70")
    pending_backfill_counts = pending_summary.get("manual_backfill_status_counts") or {}
    if pending_backfill_counts.get("RECOVERED_EXACT") != 469:
        issues.append("pending_nofill_summary_recovered_exact_not_469")
    if pending_backfill_counts.get("SOURCE_NOT_CAPTURED") != 405:
        issues.append("pending_nofill_summary_source_not_captured_not_405")
    pending_audit_counts = pending_summary.get("audit_status_counts") or {}
    if pending_audit_counts.get("PENDING_LIMIT_LIFECYCLE_COMPLETE_WITH_DOCUMENTED_LIMITATIONS") != 239:
        issues.append("pending_nofill_summary_complete_with_limitations_not_239")
    if pending_audit_counts.get("PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED") != 74:
        issues.append("pending_nofill_summary_action_required_not_74")
    pending_final_state_counts = pending_summary.get("audit_final_state_counts") or {}
    if pending_final_state_counts.get("LEGACY_PENDING_LIFECYCLE_TRUTH_UNRECOVERABLE") != 65:
        issues.append("pending_nofill_summary_legacy_unrecoverable_not_65")
    if pending_final_state_counts.get("PENDING_LIFECYCLE_GROUP_MISSING") != 52:
        issues.append("pending_nofill_summary_group_missing_not_52")
    if pending_final_state_counts.get("UNKNOWN_PENDING_LIFECYCLE_FINAL_STATE") != 3:
        issues.append("pending_nofill_summary_unknown_final_state_not_3")
    forward_touch_counts = pending_summary.get("forward_capture_touch_status_counts") or {}
    for field in [
        "side_aware_entry_touch_status",
        "terminal_area_touch_status",
        "protective_area_touch_status",
        "cancel_expiry_reason_status",
    ]:
        if (forward_touch_counts.get(field) or {}).get("LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED") != 446:
            issues.append(f"pending_nofill_forward_{field}_not_446_fail_closed")
    if (forward_touch_counts.get("decision_spread_status") or {}).get("QUOTE_SNAPSHOT_CAPTURED_SOURCE_SAFE") != 446:
        issues.append("pending_nofill_forward_decision_spread_not_446_captured")

    pending_rows = jsonl_rows.get("WAVE2_PENDING_NOFILL_LIFECYCLE_RECONCILIATION.jsonl", [])
    pending_decision_counts = Counter(row.get("decision_status") for row in pending_rows)
    if pending_decision_counts.get("not_filled") != 807 or pending_decision_counts.get("filled") != 70:
        issues.append("pending_nofill_rows_decision_counts_not_807_70")
    if not all(row.get("geometry_capture_status") == "raw_lifecycle_geometry_present" for row in pending_rows):
        issues.append("pending_nofill_rows_missing_raw_geometry")
    if not all(row.get("result_use_status") == "pending_nofill_lifecycle_source_reconciliation_not_broker_real_execution_truth" for row in pending_rows):
        issues.append("pending_nofill_rows_wrong_result_use_status")
    if not all(row.get("status") == "pending_lifecycle_material_row_reconciled_with_source_gap_boundaries" for row in pending_rows):
        issues.append("pending_nofill_rows_wrong_status")
    if not all(str(row.get("row_id", "")).startswith("pending_nofill:") for row in pending_rows):
        issues.append("pending_nofill_rows_missing_rebuilt_row_ids")
    required_pending_sources = {
        "shadow_logs/pending_limit_lifecycle.jsonl",
        "shadow_logs/pending_limit_lifecycle_join_backfill.jsonl",
        "shadow_logs/pending_limit_lifecycle_audit.jsonl",
        "shadow_logs/nofill_forward_source_capture.jsonl",
    }
    if not all(required_pending_sources.issubset(set(row.get("source_paths") or [])) for row in pending_rows):
        issues.append("pending_nofill_rows_missing_source_path_set")

    disposition_summary = json_payloads.get("WAVE2_V3_VALIDATION_AI_DUAL_BROKER_DISPOSITION_SUMMARY.json", {})
    v3_summary = disposition_summary.get("v3_summary") if isinstance(disposition_summary.get("v3_summary"), dict) else {}
    if v3_summary.get("v3_disposition_rows") != 13:
        issues.append("v3_disposition_summary_row_count_not_13")
    if v3_summary.get("live_authority_matrix_rows") != 12775:
        issues.append("v3_disposition_summary_live_authority_rows_not_12775")
    v3_disposition_counts = v3_summary.get("production_code_disposition_counts") or {}
    for label in {"active", "staged_default_off", "research_only", "rejected"}:
        if int(v3_disposition_counts.get(label, 0)) <= 0:
            issues.append(f"v3_disposition_summary_missing_label:{label}")
    dual_summary = disposition_summary.get("dual_broker_summary") if isinstance(disposition_summary.get("dual_broker_summary"), dict) else {}
    if dual_summary.get("dual_broker_rows") != 7 or dual_summary.get("ftmo_no_copy_rows") != 7:
        issues.append("dual_broker_summary_missing_7_no_copy_rows")
    ai_log_counts = disposition_summary.get("ai_log_counts") or {}
    expected_ai_counts = {
        "ai_call_policy_decisions": 0,
        "ai_decision_trace": 0,
        "ai_supervisor_decisions": 0,
        "ai_narrowing_policy_shadow_evaluations": 5671,
        "malformed_responses": 38,
    }
    for key, expected in expected_ai_counts.items():
        if ai_log_counts.get(key) != expected:
            issues.append(f"ai_log_count_mismatch:{key}:expected={expected}:actual={ai_log_counts.get(key)}")

    v3_rows = jsonl_rows.get("WAVE2_V3_TO_V4_DISPOSITION_LEDGER.jsonl", [])
    allowed_dispositions = {"active", "staged_default_off", "research_only", "rejected"}
    if not all(row.get("production_code_disposition") in allowed_dispositions for row in v3_rows):
        issues.append("v3_disposition_rows_invalid_label")
    if {row.get("production_code_disposition") for row in v3_rows} != allowed_dispositions:
        issues.append("v3_disposition_rows_missing_required_label_set")
    rejected_rows = [row for row in v3_rows if row.get("component_id") == "full_v3_live_authority_claim"]
    if not rejected_rows or rejected_rows[0].get("production_code_disposition") != "rejected":
        issues.append("v3_disposition_missing_rejected_full_authority_claim")
    for component_id in {"selector_v3", "scheduler_v3", "execution_policy_v3"}:
        component_rows = [row for row in v3_rows if row.get("component_id") == component_id]
        if not component_rows:
            issues.append(f"v3_disposition_missing_component:{component_id}")
            continue
        flags = component_rows[0].get("config_flag_state") or {}
        if any(flags.get(key) is not False for key in flags):
            issues.append(f"v3_disposition_core_flags_not_false:{component_id}")
        if component_rows[0].get("halt_time_authority_result") != "not_full_live_authority":
            issues.append(f"v3_disposition_core_component_overclaims_authority:{component_id}")
    if not all("not_live_activation" in str(row.get("result_use_status") or "") or row.get("production_code_disposition") in {"active", "rejected"} for row in v3_rows):
        issues.append("v3_disposition_rows_missing_non_activation_boundary")

    dual_rows = jsonl_rows.get("WAVE2_DUAL_BROKER_AUTHORITY_DISPOSITION_LEDGER.jsonl", [])
    if not all(row.get("ftmo_no_copy_rule") is True for row in dual_rows):
        issues.append("dual_broker_rows_missing_ftmo_no_copy_true")
    if not all("redacted_account_lot_size" in set(row.get("no_copy_forbidden_fields") or []) for row in dual_rows):
        issues.append("dual_broker_rows_missing_lot_copy_forbidden")
    if not all("FTMO_order_deal_position_account_history" in set(row.get("required_ftmo_local_truth") or []) for row in dual_rows):
        issues.append("dual_broker_rows_missing_ftmo_account_history_requirement")
    if not all(row.get("result_use_status") == "dual_broker_architecture_contract_not_target_broker_account_truth" for row in dual_rows):
        issues.append("dual_broker_rows_wrong_result_use_status")

    ai_contract = json_payloads.get("WAVE2_AI_RELIABILITY_AND_COST_CONTROL_CONTRACT.json", {})
    if ai_contract.get("status") != "contract_materialized_no_paid_replay_guard_required_for_v4":
        issues.append("ai_contract_status_not_materialized_guard")
    if ai_contract.get("runtime_log_counts") != expected_ai_counts:
        issues.append("ai_contract_runtime_counts_mismatch")
    if "no paid broad historical replay through AI" not in set(ai_contract.get("hard_rules") or []):
        issues.append("ai_contract_missing_no_paid_broad_replay_rule")

    validation_contract = json_payloads.get("WAVE2_VALIDATION_ANTI_OVERFIT_CONTRACT.json", {})
    if validation_contract.get("status") != "contract_materialized_execution_pending":
        issues.append("validation_contract_status_not_materialized_execution_pending")
    validation_counts = validation_contract.get("materialized_evidence_class_map") or {}
    expected_validation_counts = {
        "tick_repaired_first_passage_rows": 55,
        "full_tick_window_rows": 49,
        "partial_or_missing_tick_rows": 6,
        "allocator_replay_rows": 96,
        "zero_trade_rank_rows": 416,
        "final_say_authority_rows": 12775,
        "market_system_classification_rows": 77,
        "cost_source_coverage_rows": 77,
        "pending_nofill_lifecycle_rows": 877,
    }
    for key, expected in expected_validation_counts.items():
        if validation_counts.get(key) != expected:
            issues.append(f"validation_contract_count_mismatch:{key}:expected={expected}:actual={validation_counts.get(key)}")
    replay_plan = json_payloads.get("WAVE2_REPLAY_COMPRESSION_AND_PARTITION_PLAN.json", {})
    if replay_plan.get("status") != "plan_materialized_execution_pending_wave3":
        issues.append("replay_plan_status_not_execution_pending_wave3")
    if replay_plan.get("no_api_first") is not True:
        issues.append("replay_plan_no_api_first_not_true")

    causal_model = json_payloads.get("WAVE2_FULL_SYSTEM_CAUSAL_MODEL.json", {})
    if causal_model.get("status") != READINESS_STATUS:
        issues.append("full_system_causal_model_status_not_semantic_repaired")
    if causal_model.get("wave3_allowed") is not True:
        issues.append("full_system_causal_model_wave3_allowed_not_true")

    same_symbol_contract = json_payloads.get("WAVE2_SAME_SYMBOL_LIFECYCLE_OWNERSHIP_CONTRACT.json", {})
    if same_symbol_contract.get("owner_lane") != "same_symbol_same_instrument_lifecycle_v4":
        issues.append("same_symbol_contract_wrong_owner_lane")
    required_same_symbol_actions = {
        "same_direction_scale_in",
        "close_and_reverse",
        "no_trade_duplicate",
        "no_trade_hedge_conflict",
        "source_required_fail_closed",
    }
    if not required_same_symbol_actions.issubset(set(same_symbol_contract.get("owned_actions") or [])):
        issues.append("same_symbol_contract_missing_required_actions")
    for field in [
        "required_state",
        "open_position_snapshot",
        "pending_order_snapshot",
        "lifecycle_event_history",
        "broker_local_risk",
        "outputs",
        "dependencies",
        "verification",
    ]:
        if not same_symbol_contract.get(field):
            issues.append(f"same_symbol_contract_missing_{field}")

    probability_contract = json_payloads.get("WAVE2_PROBABILITY_DEBATE_ENGINE_CONTRACT.json", {})
    if probability_contract.get("owner_lane") != "probability_debate_team_engine_v4":
        issues.append("probability_contract_wrong_owner_lane")
    required_probability_actions = {"long", "short", "no-trade", "wait", "scale", "reduce", "close", "reverse"}
    if required_probability_actions != set(probability_contract.get("actions_requiring_numeric_theses") or []):
        issues.append("probability_contract_action_set_mismatch")
    for field in ["probability", "EV", "uncertainty", "vetoes", "missing_source_penalty", "confidence_calibration"]:
        if field not in set(probability_contract.get("per_thesis_fields") or []):
            issues.append(f"probability_contract_missing_per_thesis_field:{field}")

    confluence_contract = json_payloads.get("WAVE2_FOLLOW_AVOID_MIXED_NUMERIC_CONFLUENCE_CONTRACT.json", {})
    if confluence_contract.get("owner_lane") != "follow_avoid_mixed_numeric_confluence_v4":
        issues.append("confluence_contract_wrong_owner_lane")
    required_confluence_fields = {
        "direction",
        "strength",
        "confidence",
        "reliability history",
        "evidence class",
        "freshness",
        "cost sensitivity",
        "conflict reason",
        "source completeness",
    }
    if not required_confluence_fields.issubset(set(confluence_contract.get("required_source_fields") or [])):
        issues.append("confluence_contract_missing_required_fields")
    confluence_rules = set(confluence_contract.get("hard_rules") or [])
    for rule in [
        "FOLLOW is not automatic trade permission",
        "AVOID invalidation type must be explicit",
        "MIXED structured disagreement replaces vague middle state",
    ]:
        if rule not in confluence_rules:
            issues.append(f"confluence_contract_missing_rule:{rule}")

    ml_contract = json_payloads.get("WAVE2_WAVE4_WAVE5_ML_OWNERSHIP_CONTRACT.json", {})
    if ml_contract.get("status") != "downstream_wave4_wave5_contract_materialized_ml_not_ai_reliability":
        issues.append("ml_contract_status_not_separate_from_ai")
    required_ml_labels = {
        "broker-real PnL/cash",
        "exact-R",
        "proxy-R",
        "MFE",
        "MAE",
        "time-to-profit",
        "time-to-destination",
        "giveback",
        "stale thesis",
        "stop/target efficiency",
        "harvest failure",
        "opportunity cost",
    }
    if required_ml_labels != set(ml_contract.get("required_labels") or []):
        issues.append("ml_contract_required_labels_mismatch")
    for metric in ["Brier", "ECE", "reliability bins", "logloss"]:
        if metric not in set(ml_contract.get("required_metrics") or []):
            issues.append(f"ml_contract_missing_metric:{metric}")
    downstream_map = json_payloads.get("WAVE2_DOWNSTREAM_OWNERSHIP_MAP.json", {})
    if downstream_map.get("status") != READINESS_STATUS:
        issues.append("downstream_ownership_map_status_not_semantic_repaired")
    if downstream_map.get("wave3_lane_count") != EXPECTED_LANE_COUNT:
        issues.append(f"downstream_ownership_map_lane_count_not_{EXPECTED_LANE_COUNT}")

    capture_replay_rows = jsonl_rows.get("WAVE2_CAPTURE_REPLAY_AI_PRODUCTION_DISPOSITION_LEDGER.jsonl", [])
    required_capture_statuses = {
        "capture_schema_contract_materialized_implementation_pending",
        "validation_contract_materialized_execution_pending",
        "ai_reliability_contract_materialized_no_paid_replay_guard",
        "production_return_blocked_pending_v4_implementation_validation_broker_local_constraints_and_dossier",
    }
    if {row.get("status") for row in capture_replay_rows} != required_capture_statuses:
        issues.append("capture_replay_ai_disposition_status_set_mismatch")

    production_component_rows = jsonl_rows.get("WAVE2_PRODUCTION_CODE_COMPONENT_DISPOSITION_LEDGER.jsonl", [])
    if not all(row.get("production_code_disposition") in allowed_dispositions for row in production_component_rows):
        issues.append("production_component_rows_invalid_disposition_label")
    if not all(row.get("result_use_status") == "production_component_disposition_for_v4_design_not_live_activation" for row in production_component_rows):
        issues.append("production_component_rows_wrong_result_boundary")

    if question_statuses.get("opened_initial_pursuit_not_exhausted", 0) != 0:
        issues.append("question_stack_still_has_opened_initial_pursuit_rows")

    lane_contract_rows = jsonl_rows.get("WAVE2_WAVE3_LANE_CONTRACTS.jsonl", [])
    required_lane_fields = [
        "derived_from_question_ids",
        "derived_from_interaction_ids",
        "derived_from_broker_rows",
        "derived_from_candidate_rows",
        "derived_from_code_config_paths",
        "derived_from_source_gaps",
    ]
    for field in required_lane_fields:
        if not all(row.get(field) for row in lane_contract_rows):
            issues.append(f"lane_contract_missing_{field}")
    if len(lane_contract_rows) != EXPECTED_LANE_COUNT:
        issues.append(f"lane_contract_count_not_{EXPECTED_LANE_COUNT}:{len(lane_contract_rows)}")
    required_semantic_lanes = {
        "same_symbol_same_instrument_lifecycle_v4",
        "probability_debate_team_engine_v4",
        "follow_avoid_mixed_numeric_confluence_v4",
    }
    lane_names = {row.get("lane") for row in lane_contract_rows}
    missing_semantic_lanes = sorted(required_semantic_lanes - lane_names)
    if missing_semantic_lanes:
        issues.append(f"lane_contract_missing_semantic_lanes:{missing_semantic_lanes}")
    if not all(row.get("prompt_status") == PROMPT_STATUS for row in lane_contract_rows):
        issues.append("lane_contract_prompt_status_not_semantic_repaired")
    launch_order = json_payloads.get("WAVE2_WAVE3_LAUNCH_ORDER.json", {})
    launch_lanes = launch_order.get("lanes") if isinstance(launch_order.get("lanes"), list) else []
    for field in required_lane_fields:
        if not all(row.get(field) for row in launch_lanes):
            issues.append(f"launch_order_missing_{field}")
    if not all(row.get("prompt_status") == PROMPT_STATUS for row in launch_lanes):
        issues.append("launch_order_prompt_status_not_semantic_repaired")
    dependency_graph = json_payloads.get("WAVE3_LANE_DEPENDENCY_GRAPH.json", {})
    if dependency_graph.get("wave3_prompt_pack_allowed") is not True:
        issues.append("wave3_dependency_graph_should_allow_prompt_pack")
    if len(dependency_graph.get("nodes", [])) != EXPECTED_LANE_COUNT:
        issues.append(f"wave3_dependency_graph_node_count_not_{EXPECTED_LANE_COUNT}")
    if missing := sorted(required_semantic_lanes - set(dependency_graph.get("nodes", []))):
        issues.append(f"wave3_dependency_graph_missing_semantic_nodes:{missing}")
    if not dependency_graph.get("lane_provenance"):
        issues.append("wave3_dependency_graph_missing_lane_provenance")

    instruction_checklist = json_payloads.get("WAVE2_INSTRUCTION_COVERAGE_CHECKLIST.json", {})
    if instruction_checklist.get("goal_session_research_discipline_read_after_preflight") is not True:
        issues.append("instruction_checklist_missing_goal_session_discipline_read")
    if instruction_checklist.get("research_operating_doctrine_read_after_preflight") is not True:
        issues.append("instruction_checklist_missing_research_operating_doctrine_read")
    if instruction_checklist.get("lane_type") != "builder_integration_master_orchestration_not_g12_g0_audit":
        issues.append("instruction_checklist_wrong_lane_type")

    prompt_gap_summary = json_payloads.get("WAVE2_PROMPT_REQUIRED_OUTPUT_GAP_SUMMARY.json", {})
    if prompt_gap_summary.get("wave3_prompt_pack_allowed") is not True:
        issues.append("prompt_gap_summary_should_allow_wave3_prompt_pack")
    if int(prompt_gap_summary.get("required_output_count", 0)) < 90:
        issues.append("prompt_gap_summary_required_output_count_too_small")
    if int(prompt_gap_summary.get("missing_required_prompt_output_count", -1)) != 0:
        issues.append("prompt_gap_summary_missing_count_not_zero")
    prompt_gap_rows = jsonl_rows.get("WAVE2_PROMPT_REQUIRED_OUTPUT_GAP_LEDGER.jsonl", [])
    if any(row.get("status") == "missing_required_prompt_output" for row in prompt_gap_rows):
        issues.append("prompt_gap_ledger_still_has_missing_status")
    prompt_pack_required = {
        "WAVE2_PROMPT_PACK_MANIFEST",
        "WAVE2_PROMPT_HARDENING_VERIFICATION_RESULT",
        "WAVE3_PER_LANE_CONTROLLING_PROMPTS",
        "WAVE3_PER_LANE_ONE_LINE_STARTERS",
    }
    prompt_gap_by_name = {row.get("required_output"): row for row in prompt_gap_rows}
    for required_name in prompt_pack_required:
        if prompt_gap_by_name.get(required_name, {}).get("status") != "exact_present":
            issues.append(f"prompt_pack_required_output_not_exact_present:{required_name}")

    prompt_pack_manifest = json_payloads.get("WAVE2_PROMPT_PACK_MANIFEST.json", {})
    if prompt_pack_manifest.get("status") != READINESS_STATUS:
        issues.append("prompt_pack_manifest_status_not_semantic_repaired")
    if prompt_pack_manifest.get("lane_count") != EXPECTED_LANE_COUNT:
        issues.append(f"prompt_pack_manifest_lane_count_not_{EXPECTED_LANE_COUNT}")

    hardening_result = json_payloads.get("WAVE2_PROMPT_HARDENING_VERIFICATION_RESULT.json", {})
    if hardening_result.get("status") != "passed":
        issues.append("prompt_hardening_result_not_passed")
    if hardening_result.get("all_prompts_hardened") is not True:
        issues.append("prompt_hardening_prompts_not_all_hardened")
    if hardening_result.get("all_starters_hardened") is not True:
        issues.append("prompt_hardening_starters_not_all_hardened")
    if hardening_result.get("all_starters_one_physical_line") is not True:
        issues.append("prompt_hardening_starters_not_one_line")
    if hardening_result.get("all_starters_required_prefix") is not True:
        issues.append("prompt_hardening_starters_missing_prefix")
    semantic_hardening_result = json_payloads.get("WAVE2_SEMANTIC_PROMPT_HARDENING_VERIFICATION_RESULT.json", {})
    if semantic_hardening_result.get("status") != "passed":
        issues.append("semantic_prompt_hardening_result_not_passed")
    if semantic_hardening_result.get("lane_count") != EXPECTED_LANE_COUNT:
        issues.append(f"semantic_prompt_hardening_lane_count_not_{EXPECTED_LANE_COUNT}")

    prompt_rows = jsonl_rows.get("WAVE3_PER_LANE_CONTROLLING_PROMPTS.jsonl", [])
    starter_rows = jsonl_rows.get("WAVE3_PER_LANE_ONE_LINE_STARTERS.jsonl", [])
    contract_lanes = [row.get("lane") for row in sorted(lane_contract_rows, key=lambda row: int(row.get("launch_order") or 0))]
    prompt_lanes = [row.get("lane") for row in sorted(prompt_rows, key=lambda row: int(row.get("launch_order") or 0))]
    starter_lanes = [row.get("lane") for row in sorted(starter_rows, key=lambda row: int(row.get("launch_order") or 0))]
    if prompt_lanes != contract_lanes:
        issues.append("prompt_pack_lanes_do_not_match_contract_lanes")
    if starter_lanes != contract_lanes:
        issues.append("starter_pack_lanes_do_not_match_contract_lanes")
    for field in required_lane_fields:
        if not all(row.get(field) for row in prompt_rows):
            issues.append(f"prompt_rows_missing_{field}")
    required_prompt_texts = [
        "Mandatory Preflight",
        "goal_session_research_discipline.md",
        "research_operating_doctrine.md",
        "Do not rely on chat memory",
        "no arbitrary top-N",
        "same-evidence-class",
        "Forbidden without separate owner approval",
        "RESULT_MATERIALIZATION_REQUIRED",
        "broker_runtime_change_status=false",
        "Co-Authored-By: Codex GPT-5 <redacted@example.com>",
    ]
    for row in prompt_rows:
        body = str(row.get("controlling_prompt_body") or "")
        for needle in required_prompt_texts:
            if needle.lower() not in body.lower():
                issues.append(f"prompt_body_missing_required_text:{row.get('lane')}:{needle}")
        if row.get("prompt_status") != PROMPT_STATUS:
            issues.append(f"prompt_row_status_not_semantic_repaired:{row.get('lane')}")
        if row.get("result_boundary") != "local_production_code_integration_not_live_deployment":
            issues.append(f"prompt_row_result_boundary_wrong:{row.get('lane')}")
    for row in starter_rows:
        text = str(row.get("starter_text") or "")
        if row.get("one_physical_line") is not True or "\n" in text:
            issues.append(f"starter_not_one_physical_line:{row.get('lane')}")
        if row.get("starts_with_required_prefix") is not True:
            issues.append(f"starter_missing_required_prefix:{row.get('lane')}")
        for needle in ["no arbitrary top-N", "same-evidence-class", "RESULT_MATERIALIZATION_REQUIRED", "broker_runtime_change_status=false"]:
            if needle.lower() not in text.lower():
                issues.append(f"starter_missing_required_text:{row.get('lane')}:{needle}")

    final_master = json_payloads.get("WAVE2_FINAL_MASTER_STATE_TABLE.json", {})
    if final_master.get("wave3_prompt_pack_allowed") is not True:
        issues.append("final_master_state_should_allow_wave3_prompt_pack")
    if final_master.get("status") != READINESS_STATUS:
        issues.append("final_master_state_status_not_semantic_repaired")
    if final_master.get("central_orchestrator_acceptance_required") is not True:
        issues.append("final_master_missing_central_orchestrator_acceptance_required")
    launch_order = json_payloads.get("WAVE2_WAVE3_LAUNCH_ORDER.json", {})
    if launch_order.get("wave3_prompt_pack_allowed") is not True:
        issues.append("wave3_launch_order_should_be_allowed")
    if launch_order.get("status") != READINESS_STATUS:
        issues.append("wave3_launch_order_status_not_semantic_repaired")
    if len(launch_order.get("lanes", [])) < 10:
        issues.append("wave3_launch_order_too_few_candidate_lanes")

    result = {
        "ok": not issues,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "issue_count": len(issues),
        "issues": issues,
        "route_dir": str(ROUTE_DIR.relative_to(REPO_ROOT)),
        "json_files_checked": len(REQUIRED_JSON),
        "jsonl_files_checked": len(REQUIRED_JSONL),
        "jsonl_row_counts": {name: len(rows) for name, rows in sorted(jsonl_rows.items())},
        "headline": headline,
        "question_status_counts": dict(question_statuses),
        "contradiction_scan_summary": contradiction_scan_summary,
        "completion_status": (
            "wave2_semantic_launch_architecture_repair_verified_pending_central_orchestrator_acceptance"
            if not issues
            else "wave2_semantic_launch_architecture_repair_verification_failed"
        ),
    }

    if args.write_result:
        (ROUTE_DIR / "WAVE2_INITIAL_CAUSAL_SPINE_VERIFICATION_RESULT.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
