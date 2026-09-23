from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

import src.components.gtos_vnext_runtime as vnext_runtime_mod
import src.components.orchestrator as orchestrator_mod
from src.components.gtos_vnext_runtime import (
    DEFAULT_CP281_BRANCH_DECISIONS_ARTIFACT_PATH,
    DEFAULT_CP281_READY_RUNTIME_AGGREGATE_ARTIFACT_PATH,
    DEFAULT_CP281_READY_RUNTIME_RULE_ARTIFACT_PATH,
    DEFAULT_CP281_RULE_REPLAY_EVENT_ARTIFACT_PATH,
    DEFAULT_CP281_RULE_REPLAY_RESULT_TABLE_ARTIFACT_PATH,
    DEFAULT_BRIDGE_DIAGNOSTIC_ARTIFACT_PATH,
    DEFAULT_EVIDENCE_MATRIX_ARTIFACT_PATH,
    DEFAULT_IMPLEMENTATION_ARTIFACT_PATH,
    DEFAULT_REVIEW_ARTIFACT_PATH,
    GTOSVNextEvidenceIndex,
    GTOSVNextAIPolicyDecision,
    GTOSVNextMoonshotDynamicExecutionDecision,
    GTOSVNextReplacementMonitoringSnapshot,
    GTOSVNextRuntimeDecision,
    GTOSVNextPreAIRoutingDecision,
    GTOSVNextRiskAdjustment,
    GTOSVNextLTFPathExecutionDecision,
    GTOSVNextPendingPolicy,
    GTOSVNextPropSafeSelectorDecision,
    attach_vnext_confidence_override_to_record,
    attach_vnext_ai_policy_to_record,
    attach_vnext_ltf_path_execution_to_record,
    attach_vnext_moonshot_dynamic_execution_to_record,
    attach_vnext_pre_ai_to_record,
    apply_vnext_risk_adjustment,
    attach_vnext_pending_policy_to_record,
    attach_vnext_prop_safe_selector_to_record,
    attach_vnext_replacement_monitoring_to_record,
    build_vnext_pre_ai_event,
    build_vnext_event_from_candidate,
    build_vnext_replacement_monitoring_snapshot,
    evaluate_vnext_confidence_override,
    evaluate_vnext_ai_policy,
    evaluate_vnext_exit_management_policy,
    evaluate_vnext_ready8_failure_control_policy,
    evaluate_vnext_ltf_path_execution,
    evaluate_vnext_moonshot_dynamic_execution,
    evaluate_vnext_pending_policy,
    evaluate_vnext_prop_safe_selector,
    evaluate_vnext_event,
    evaluate_vnext_route_event,
    evaluate_pre_ai_vnext,
    format_vnext_ai_policy_context_for_prompt,
    format_vnext_ai_role_context_for_prompt,
    load_vnext_bridge_diagnostics,
    load_vnext_evidence_index,
    normalize_event,
    normalize_vnext_symbol_key,
    record_vnext_replacement_monitoring_snapshot,
    record_vnext_runtime_decision,
    resolve_vnext_symbol_family,
    symbol_family_candidates_for_vnext,
    vnext_ai_policy_allows_no_paid_mechanical_follow,
    vnext_ai_policy_no_paid_call_replay_decision,
    vnext_ai_policy_requires_paid_call,
    vnext_blocks_execution,
    vnext_execution_block_reason,
)
from src.components.orchestrator import SessionOrchestrator


MOONSHOT_SOURCE_REPAIR_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_SOURCE_REPAIR_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_AMBIGUITY_COLLAPSE_ACTION_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_ACTION_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_ENTRY_ADVERSE_VARIANT_DETAIL_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_ADVERSE_REDESIGN_DETAIL_ADVERSE_VARIANT_DETAIL_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_BROKER_REPAIRED_PROXY_RESULT_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_BROKER_SOURCE_REPAIR_EXPECTANCY_REPAIR_RESULT_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_UNIFIED_NUMERIC_RESULT_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_NUMERIC_RESULT_TABLES_NUMERIC_RESULT_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_EXACT_R_OR_MISSING_PROOF_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_NUMERIC_RESULT_TABLES_EXACT_R_OR_MISSING_PROOF_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_SOURCE_COMPONENT_SUMMARY_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_NUMERIC_RESULT_TABLES_SOURCE_COMPONENT_SUMMARY_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_SOURCE_GEOMETRY_REPAIR_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_NUMERIC_RESULT_TABLES_SOURCE_GEOMETRY_REPAIR_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_RECOMMENDATION_MERGE_BUCKET_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_RECOMMENDATION_MERGE_BUNDLE_BUCKET_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_RECOMMENDATION_MERGE_FAMILY_ROLLUP_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_RECOMMENDATION_MERGE_BUNDLE_FAMILY_ROLLUP_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_RECOMMENDATION_MERGE_UNIFIED_CANDIDATE_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_RECOMMENDATION_MERGE_BUNDLE_UNIFIED_CANDIDATE_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_RECOMMENDATION_MERGE_SCOPE_ROLLUP_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_RECOMMENDATION_MERGE_BUNDLE_SCOPE_ROLLUP_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_CHALLENGER_FRONTIER_ACTION_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_CHALLENGER_FRONTIER_ACTION_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_CHALLENGER_FRONTIER_ROUTE_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_CHALLENGER_FRONTIER_ROUTE_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_CONTROL_SCREEN_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_CONTROL_SCREEN_LEDGER_2026-05-15.jsonl"
)
MOONSHOT_CONTROL_SCREEN_ROUTE_QUEUE = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_CONTROL_SCREEN_ROUTE_QUEUE_2026-05-15.jsonl"
)
MOONSHOT_GTOS_REPLAY_BLOCKER_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BLOCKER_LEDGER_2026-05-15.jsonl"
)
MOONSHOT_ACCEPTED_BUILDER_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_ACCEPTED_BUILDER_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_ACCEPTED_BUILDER_BINDING_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_BINDING_RESULT_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_ACCEPTED_BUILDER_BRANCH_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_BRANCH_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_ACCEPTED_BUILDER_ENTRY_ADVERSE_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_ENTRY_ADVERSE_RESULT_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_ACCEPTED_BUILDER_FAMILY_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_FAMILY_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_ACCEPTED_BUILDER_M15_RESULT_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_M15_RESULT_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_ACCEPTED_BUILDER_M1_RESULT_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_M1_RESULT_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_ACCEPTED_BUILDER_POSITIVE_RESULT_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_POSITIVE_RESULT_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_ACCEPTED_BUILDER_SOURCE_RESULT_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_SOURCE_RESULT_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_ACCEPTED_BUILDER_REJECTED_REPAIR_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_REJECTED_REPAIR_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_MARKET_GAP_PRIMITIVE_ACTION_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_MARKET_GAP_PRIMITIVE_EXPANSION_ACTION_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_MARKET_GAP_PRIMITIVE_TRANSFER_CONTEXT_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_MARKET_GAP_PRIMITIVE_EXPANSION_TRANSFER_CONTEXT_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_MARKET_GAP_PRIMITIVE_SCORE_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_SCORING_MARKET_GAP_SCORE_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_MARKET_GAP_CODE_CANDIDATE_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_REPLAY_CODE_CANDIDATE_MARKET_GAP_CODE_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_NEARMISS_BRANCH_SUMMARY_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NEARMISS_MARKET_ENTRY_JOIN_BRANCH_SUMMARY_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_NEARMISS_MARKET_ENTRY_JOIN_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NEARMISS_MARKET_ENTRY_JOIN_MARKET_ENTRY_JOIN_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_NEARMISS_OFFSET_JOIN_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NEARMISS_MARKET_ENTRY_JOIN_OFFSET_JOIN_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_NEARMISS_SOURCE_REQUIREMENT_JOIN_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NEARMISS_MARKET_ENTRY_JOIN_SOURCE_REQUIREMENT_JOIN_LEDGER_2026-05-16.jsonl"
)
MOONSHOT_EXPANDED_MARKET_CODE_CANDIDATES_ROW_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_CODE_CANDIDATES_ROW_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION_ROW_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION_ROW_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_EXPANDED_MARKET_REDUCED_CANDIDATES_ROW_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_IMPLEMENTATION_CANDIDATES_ROW_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_EXPANDED_MARKET_DECON_SCORER_SURFACE_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_DECONCENTRATED_SCORER_SURFACES_SURFACE_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_EXPANDED_MARKET_FINAL_DECISION_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_FINAL_IMPLEMENTATION_DECISIONS_DECISION_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_EXPANDED_MARKET_SOURCE_EXPANSION_CANDIDATE_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_EXPANDED_MARKET_UNIFIED_ACTION_DECISION_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_IMPLEMENTATION_ACTIONS_DECISION_ACTION_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_EXPANDED_MARKET_STRICT_READINESS_SURFACE_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_READINESS_SURFACE_READINESS_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_EXPANDED_MARKET_REPAIR_HANDOFF_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_HANDOFF_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_EXPANDED_MARKET_REPAIR_ACCEPTANCE_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPAIR_IMPLEMENTATION_ACCEPTANCE_ACCEPTANCE_LEDGER_2026-05-17.jsonl"
)
GTOS_VNEXT_EXPANDED_MARKET_SOURCE_GEOMETRY_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_EXPANDED_MARKET_SOURCE_GEOMETRY_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_EXPANDED_MARKET_SOURCE_GEOMETRY_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_EXPANDED_MARKET_SOURCE_GEOMETRY_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_NOFILL_PENDING_LIFECYCLE_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_NOFILL_PENDING_LIFECYCLE_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_NOFILL_PENDING_LIFECYCLE_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_NOFILL_PENDING_LIFECYCLE_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_ENTRY_OFFSET_050R_CLUSTER_GUARD_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_ENTRY_OFFSET_050R_CLUSTER_GUARD_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_ENTRY_OFFSET_050R_CLUSTER_GUARD_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_ENTRY_OFFSET_050R_CLUSTER_GUARD_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_OPENING_DRIVE_SOURCE_CONTRACT_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_OPENING_DRIVE_SOURCE_CONTRACT_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_OPENING_DRIVE_SOURCE_CONTRACT_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_OPENING_DRIVE_SOURCE_CONTRACT_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_NUMERIC_ROUTER_CATALOG_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_NUMERIC_ROUTER_CATALOG_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_NUMERIC_ROUTER_CATALOG_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_NUMERIC_ROUTER_CATALOG_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_SURVIVOR_FAILURE_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SURVIVOR_FAILURE_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_SURVIVOR_FAILURE_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SURVIVOR_FAILURE_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_SOURCE_REPAIR_MISSING_DENOMINATOR_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SOURCE_REPAIR_MISSING_DENOMINATOR_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_SOURCE_REPAIR_MISSING_DENOMINATOR_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SOURCE_REPAIR_MISSING_DENOMINATOR_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_NR_SOURCE_REPAIR_EXECUTION_IDENTITY_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_NR_SOURCE_REPAIR_EXECUTION_IDENTITY_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_NR_SOURCE_REPAIR_EXECUTION_IDENTITY_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_NR_SOURCE_REPAIR_EXECUTION_IDENTITY_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_AI_NARROWING_DEFAULT_OFF_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_AI_NARROWING_DEFAULT_OFF_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_AI_NARROWING_DEFAULT_OFF_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_AI_NARROWING_DEFAULT_OFF_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_AI_DECISION_TRACE_ROUTING_GUARD_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_AI_DECISION_TRACE_ROUTING_GUARD_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_AI_DECISION_TRACE_ROUTING_GUARD_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_AI_DECISION_TRACE_ROUTING_GUARD_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_PRE_AI_POST_L2_ROUTING_POLICY_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_PRE_AI_POST_L2_ROUTING_POLICY_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_PRE_AI_POST_L2_ROUTING_POLICY_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_PRE_AI_POST_L2_ROUTING_POLICY_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_LEGACY_AI_CASCADE_MODEL_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LEGACY_AI_CASCADE_MODEL_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_LEGACY_AI_CASCADE_MODEL_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LEGACY_AI_CASCADE_MODEL_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_EXIT_MANAGEMENT_TRAILING_J46_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_EXIT_MANAGEMENT_TRAILING_J46_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_EXIT_MANAGEMENT_TRAILING_J46_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_EXIT_MANAGEMENT_TRAILING_J46_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_EXIT_MANAGEMENT_RESIDUE_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_EXIT_MANAGEMENT_RESIDUE_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_EXIT_MANAGEMENT_RESIDUE_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_EXIT_MANAGEMENT_RESIDUE_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_Q62_PARTIAL_CLOSE_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_Q62_PARTIAL_CLOSE_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_Q62_PARTIAL_CLOSE_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_Q62_PARTIAL_CLOSE_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_MAIN_ORCH24_TICK_STRUCTURAL_ENTRY_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_TICK_STRUCTURAL_ENTRY_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_MAIN_ORCH24_TICK_STRUCTURAL_ENTRY_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_TICK_STRUCTURAL_ENTRY_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_MAIN_ORCH24_STRUCTURAL_REPAIR_ACTION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_STRUCTURAL_REPAIR_ACTION_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_MAIN_ORCH24_STRUCTURAL_REPAIR_ACTION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_STRUCTURAL_REPAIR_ACTION_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_MAIN_ORCH24_ACTION_COMPLETENESS_RESIDUAL_R_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_ACTION_COMPLETENESS_RESIDUAL_R_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_MAIN_ORCH24_ACTION_COMPLETENESS_RESIDUAL_R_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_ACTION_COMPLETENESS_RESIDUAL_R_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_MAIN_ORCH24_IMPLEMENTATION_SELECTION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_IMPLEMENTATION_SELECTION_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_MAIN_ORCH24_IMPLEMENTATION_SELECTION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_IMPLEMENTATION_SELECTION_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_MAIN_ORCH24_SNAPSHOT_DEPENDENCY_REPAIR_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_SNAPSHOT_DEPENDENCY_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_MAIN_ORCH24_SNAPSHOT_DEPENDENCY_REPAIR_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_SNAPSHOT_DEPENDENCY_REPAIR_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_MAIN_ORCH24_UNIFIED_CANDIDATE_PATH_PROXY_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_UNIFIED_CANDIDATE_PATH_PROXY_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_MAIN_ORCH24_UNIFIED_CANDIDATE_PATH_PROXY_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_UNIFIED_CANDIDATE_PATH_PROXY_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_MAIN_ORCH48_FINAL_REVIEW_SELECTOR_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH48_FINAL_REVIEW_SELECTOR_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_MAIN_ORCH48_FINAL_REVIEW_SELECTOR_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH48_FINAL_REVIEW_SELECTOR_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_LTF_PATH_GEOMETRY_SOURCE_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LTF_PATH_GEOMETRY_SOURCE_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_LTF_PATH_GEOMETRY_SOURCE_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LTF_PATH_GEOMETRY_SOURCE_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_INSTRUMENT_EXPANSION_MARKET_SESSION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_INSTRUMENT_EXPANSION_MARKET_SESSION_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_INSTRUMENT_EXPANSION_MARKET_SESSION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_INSTRUMENT_EXPANSION_MARKET_SESSION_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_MAIN_ORCH24_SOURCE_ACCEPTED_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_SOURCE_ACCEPTED_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_MAIN_ORCH24_SOURCE_ACCEPTED_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_SOURCE_ACCEPTED_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_MAIN_ORCH24_SWING_PROTECTED_SOURCE_REPAIR_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_SWING_PROTECTED_SOURCE_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_MAIN_ORCH24_SWING_PROTECTED_SOURCE_REPAIR_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_SWING_PROTECTED_SOURCE_REPAIR_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_MAIN_ORCH24_SOURCE_M15_BRANCH_REPAIR_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_SOURCE_M15_BRANCH_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_MAIN_ORCH24_SOURCE_M15_BRANCH_REPAIR_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_SOURCE_M15_BRANCH_REPAIR_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_MAIN_ORCH24_LIVE_MECHANICAL_GEOMETRY_OUTCOME_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_LIVE_MECHANICAL_GEOMETRY_OUTCOME_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_MAIN_ORCH24_LIVE_MECHANICAL_GEOMETRY_OUTCOME_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_LIVE_MECHANICAL_GEOMETRY_OUTCOME_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_TICK_SOURCE_RECOVERY_QUOTE_CONTRACT_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_TICK_SOURCE_RECOVERY_QUOTE_CONTRACT_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_TICK_SOURCE_RECOVERY_QUOTE_CONTRACT_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_TICK_SOURCE_RECOVERY_QUOTE_CONTRACT_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_LEGACY_LIVE_SHADOW_DECISION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LEGACY_LIVE_SHADOW_DECISION_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_LEGACY_LIVE_SHADOW_DECISION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LEGACY_LIVE_SHADOW_DECISION_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_READY8_FAILURE_CONTROL_RESIDUE_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_READY8_FAILURE_CONTROL_RESIDUE_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_READY8_FAILURE_CONTROL_RESIDUE_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_READY8_FAILURE_CONTROL_RESIDUE_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_REJECTED_CANDIDATE_L2_VALUE_MINING_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_REJECTED_CANDIDATE_L2_VALUE_MINING_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_REJECTED_CANDIDATE_L2_VALUE_MINING_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_REJECTED_CANDIDATE_L2_VALUE_MINING_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_ACCEPTED_CANDIDATE_M1_FILL_SOURCE_REPAIR_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_ACCEPTED_CANDIDATE_M1_FILL_SOURCE_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_ACCEPTED_CANDIDATE_M1_FILL_SOURCE_REPAIR_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_ACCEPTED_CANDIDATE_M1_FILL_SOURCE_REPAIR_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_BRIDGE_RESIDUE_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_BRIDGE_RESIDUE_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_BRIDGE_RESIDUE_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_BRIDGE_RESIDUE_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_LEGACY_T7_SIMULATION_FRICTION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LEGACY_T7_SIMULATION_FRICTION_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_LEGACY_T7_SIMULATION_FRICTION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LEGACY_T7_SIMULATION_FRICTION_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_LEGACY_V2_V3_PAPER_LIVE_FRICTION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LEGACY_V2_V3_PAPER_LIVE_FRICTION_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_LEGACY_V2_V3_PAPER_LIVE_FRICTION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LEGACY_V2_V3_PAPER_LIVE_FRICTION_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_SL_BEYOND_OB_OUTCOME_JOIN_SOURCE_REPAIR_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SL_BEYOND_OB_OUTCOME_JOIN_SOURCE_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_SL_BEYOND_OB_OUTCOME_JOIN_SOURCE_REPAIR_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SL_BEYOND_OB_OUTCOME_JOIN_SOURCE_REPAIR_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_FVG_TRADE_RECORD_BOUNDS_EXECUTION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_FVG_TRADE_RECORD_BOUNDS_EXECUTION_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_FVG_TRADE_RECORD_BOUNDS_EXECUTION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_FVG_TRADE_RECORD_BOUNDS_EXECUTION_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_SCID_TARGET_HORIZON_CONTROL_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SCID_TARGET_HORIZON_CONTROL_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_SCID_TARGET_HORIZON_CONTROL_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SCID_TARGET_HORIZON_CONTROL_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_EXECUTION_ADJACENT_FRICTION_RESIDUE_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_EXECUTION_ADJACENT_FRICTION_RESIDUE_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_EXECUTION_ADJACENT_FRICTION_RESIDUE_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_EXECUTION_ADJACENT_FRICTION_RESIDUE_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_TRADE_RECORD_EXECUTION_LIFECYCLE_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_TRADE_RECORD_EXECUTION_LIFECYCLE_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_TRADE_RECORD_EXECUTION_LIFECYCLE_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_TRADE_RECORD_EXECUTION_LIFECYCLE_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_SIERRA_DEPTH_SOURCE_ACQUISITION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SIERRA_DEPTH_SOURCE_ACQUISITION_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_SIERRA_DEPTH_SOURCE_ACQUISITION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SIERRA_DEPTH_SOURCE_ACQUISITION_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_RISK_PROXY_STRESS_COST_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_RISK_PROXY_STRESS_COST_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_RISK_PROXY_STRESS_COST_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_RISK_PROXY_STRESS_COST_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_GATE_SELECTOR_SESSION_TIMEFRAME_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_GATE_SELECTOR_SESSION_TIMEFRAME_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_GATE_SELECTOR_SESSION_TIMEFRAME_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_GATE_SELECTOR_SESSION_TIMEFRAME_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_ADVERSE_STOP_FIRST_EXECUTION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_ADVERSE_STOP_FIRST_EXECUTION_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_ADVERSE_STOP_FIRST_EXECUTION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_ADVERSE_STOP_FIRST_EXECUTION_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_BRANCH_FOLLOWUP_COMPUTATION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_BRANCH_FOLLOWUP_COMPUTATION_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_BRANCH_FOLLOWUP_COMPUTATION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_BRANCH_FOLLOWUP_COMPUTATION_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_BRANCH_AMBIGUITY_COLLAPSE_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_BRANCH_AMBIGUITY_COLLAPSE_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_BRANCH_AMBIGUITY_COLLAPSE_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_BRANCH_AMBIGUITY_COLLAPSE_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_BRANCH_IMPLEMENTATION_REPLAY_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_BRANCH_IMPLEMENTATION_REPLAY_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_BRANCH_IMPLEMENTATION_REPLAY_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_BRANCH_IMPLEMENTATION_REPLAY_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_CP280_SCORER_FILTER_ROUTER_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_CP280_SCORER_FILTER_ROUTER_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_CP280_SCORER_FILTER_ROUTER_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_CP280_SCORER_FILTER_ROUTER_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_OBSERVABLE_EXECUTION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_OBSERVABLE_EXECUTION_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_OBSERVABLE_EXECUTION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_OBSERVABLE_EXECUTION_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_UNIFIED_EXECUTION_ACTION_WORK_ORDER_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_UNIFIED_EXECUTION_ACTION_WORK_ORDER_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_UNIFIED_EXECUTION_ACTION_WORK_ORDER_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_UNIFIED_EXECUTION_ACTION_WORK_ORDER_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_TARGET_STOP_ORDERING_EXECUTION_SCORING_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_TARGET_STOP_ORDERING_EXECUTION_SCORING_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_TARGET_STOP_ORDERING_EXECUTION_SCORING_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_TARGET_STOP_ORDERING_EXECUTION_SCORING_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_BRANCH_REPLAY_EXECUTION_REPAIR_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_BRANCH_REPLAY_EXECUTION_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_BRANCH_REPLAY_EXECUTION_REPAIR_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_BRANCH_REPLAY_EXECUTION_REPAIR_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_UNIFIED_CANDIDATE_ACTION_EXECUTION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_UNIFIED_CANDIDATE_ACTION_EXECUTION_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_UNIFIED_CANDIDATE_ACTION_EXECUTION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_UNIFIED_CANDIDATE_ACTION_EXECUTION_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_UNIFIED_CANDIDATE_SCORING_EXECUTION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_UNIFIED_CANDIDATE_SCORING_EXECUTION_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_UNIFIED_CANDIDATE_SCORING_EXECUTION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_UNIFIED_CANDIDATE_SCORING_EXECUTION_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_UNIFIED_EXECUTION_DECISION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_UNIFIED_EXECUTION_DECISION_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_UNIFIED_EXECUTION_DECISION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_UNIFIED_EXECUTION_DECISION_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_UNIFIED_SHADOW_SOURCE_MATERIALIZATION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_UNIFIED_SHADOW_SOURCE_MATERIALIZATION_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_UNIFIED_SHADOW_SOURCE_MATERIALIZATION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_UNIFIED_SHADOW_SOURCE_MATERIALIZATION_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_TICK_M15_EXECUTION_FRICTION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_TICK_M15_EXECUTION_FRICTION_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_TICK_M15_EXECUTION_FRICTION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_TICK_M15_EXECUTION_FRICTION_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_TICK_M15_TARGET_CONTROL_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_TICK_M15_TARGET_CONTROL_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_TICK_M15_TARGET_CONTROL_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_TICK_M15_TARGET_CONTROL_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_SCID_FORWARD_SOURCE_CAPTURE_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SCID_FORWARD_SOURCE_CAPTURE_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_SCID_FORWARD_SOURCE_CAPTURE_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SCID_FORWARD_SOURCE_CAPTURE_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_SCID_FUTURE_CAPTURE_SOURCE_STATE_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SCID_FUTURE_CAPTURE_SOURCE_STATE_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_SCID_FUTURE_CAPTURE_SOURCE_STATE_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SCID_FUTURE_CAPTURE_SOURCE_STATE_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_SCID_COMBINED_SOURCE_CAPTURE_POI_BOUNDS_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SCID_COMBINED_SOURCE_CAPTURE_POI_BOUNDS_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_SCID_COMBINED_SOURCE_CAPTURE_POI_BOUNDS_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SCID_COMBINED_SOURCE_CAPTURE_POI_BOUNDS_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_SCID_NOAPI_SOURCE_REPAIR_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SCID_NOAPI_SOURCE_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_SCID_NOAPI_SOURCE_REPAIR_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SCID_NOAPI_SOURCE_REPAIR_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_LIFECYCLE_EXECUTION_SOURCE_GUARD_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LIFECYCLE_EXECUTION_SOURCE_GUARD_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_LIFECYCLE_EXECUTION_SOURCE_GUARD_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LIFECYCLE_EXECUTION_SOURCE_GUARD_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_PRE_AI_H1_POI_SOURCE_GAP_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_PRE_AI_H1_POI_SOURCE_GAP_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_PRE_AI_H1_POI_SOURCE_GAP_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_PRE_AI_H1_POI_SOURCE_GAP_RUNTIME_SUMMARY_2026-05-18.json"
)
GTOS_VNEXT_SHADOW_SOURCE_LOG_MATERIALIZATION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SHADOW_SOURCE_LOG_MATERIALIZATION_RUNTIME_ROWS_2026-05-18.jsonl"
)
GTOS_VNEXT_SHADOW_SOURCE_LOG_MATERIALIZATION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SHADOW_SOURCE_LOG_MATERIALIZATION_RUNTIME_SUMMARY_2026-05-18.json"
)
MOONSHOT_REPAIRED_PROXY_SCOPE_DEFAULT_OFF_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCOPE_SCORER_APPLICATION_DEFAULT_OFF_SCORE_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_SCOPE_AVOID_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCOPE_SCORER_APPLICATION_AVOID_REDESIGN_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_SCOPE_REPAIR_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCOPE_SCORER_APPLICATION_REPAIR_REQUIRED_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_SCOPE_REGISTRY_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCOPE_SCORER_APPLICATION_REGISTRY_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_SYMBOL_PROXY_SURFACE_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SYMBOL_ACTION_PACKET_SYMBOL_PROXY_SURFACE_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_SYMBOL_ACTION_PACKET_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SYMBOL_ACTION_PACKET_SYMBOL_ACTION_PACKET_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_COMPARATOR_REGISTRATION_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SYMBOL_ACTION_PACKET_COMPARATOR_REGISTRATION_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_RUNTIME_PERFORMANCE_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_PERFORMANCE_ROW_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_RUNTIME_CANDIDATE_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_CANDIDATE_BUNDLE_RUNTIME_CANDIDATE_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_RUNTIME_GUARD_CHECK_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_CANDIDATE_BUNDLE_GUARD_CHECK_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_REGISTRY_EVENT_PROBE_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_CANDIDATE_REGISTRY_EVENT_PROBE_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_REGISTRY_MODULE_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_CANDIDATE_REGISTRY_REGISTRY_MODULE_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_REGISTRATION_SPEC_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REGISTRATION_SPECS_REGISTRATION_SPEC_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_RUNTIME_GUARD_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REGISTRATION_SPECS_RUNTIME_GUARD_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_SYMBOL_REGISTRATION_SUMMARY_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REGISTRATION_SPECS_SYMBOL_REGISTRATION_SUMMARY_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_SCORE_ACTION_SCOPE_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCORE_BRIDGE_ACTION_PACKET_ACTION_SCOPE_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_SCORE_SCOPE_SUMMARY_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCORE_BRIDGE_REBUILD_SCORE_SCOPE_SUMMARY_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_REPAIR_CONTEXT_BRIDGE_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCORE_BRIDGE_REBUILD_REPAIR_CONTEXT_BRIDGE_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_SCORE_SYMBOL_SUMMARY_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCORE_BRIDGE_REBUILD_SYMBOL_SUMMARY_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_EXECUTION_SYMBOL_ACTION_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_EXECUTION_REGISTRY_SYMBOL_ACTION_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_REPAIRED_PROXY_COST_SYMBOL_LEDGER = Path(
    r"research\science_program_2026_05\06_outcome_testing"
    r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
    r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_EXECUTION_SPECS_COST_SYMBOL_LEDGER_2026-05-17.jsonl"
)
MOONSHOT_UNIFIED_CANDIDATE_MARKET_ROLLUP_ARTIFACTS = [
    Path(
        r"research\science_program_2026_05\06_outcome_testing"
        r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
        r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_DISPATCH_BUNDLE_GUARD_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl"
    ),
    Path(
        r"research\science_program_2026_05\06_outcome_testing"
        r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
        r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_DISPATCH_BUNDLE_MARKET_ROLLUP_LEDGER_2026-05-17.jsonl"
    ),
    Path(
        r"research\science_program_2026_05\06_outcome_testing"
        r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
        r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_DISPATCH_BUNDLE_NOFILL_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl"
    ),
    Path(
        r"research\science_program_2026_05\06_outcome_testing"
        r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
        r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_DISPATCH_BUNDLE_SCORER_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl"
    ),
    Path(
        r"research\science_program_2026_05\06_outcome_testing"
        r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
        r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_BUNDLE_MARKET_ROLLUP_LEDGER_2026-05-17.jsonl"
    ),
    Path(
        r"research\science_program_2026_05\06_outcome_testing"
        r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
        r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_MATERIALIZATION_BUNDLE_MARKET_ROLLUP_LEDGER_2026-05-17.jsonl"
    ),
    Path(
        r"research\science_program_2026_05\06_outcome_testing"
        r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
        r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_RUNTIME_BUNDLE_GUARD_RUNTIME_BINDING_LEDGER_2026-05-17.jsonl"
    ),
    Path(
        r"research\science_program_2026_05\06_outcome_testing"
        r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
        r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_RUNTIME_BUNDLE_MARKET_ROLLUP_LEDGER_2026-05-17.jsonl"
    ),
    Path(
        r"research\science_program_2026_05\06_outcome_testing"
        r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
        r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_BUNDLE_CANDIDATE_EXECUTION_LEDGER_2026-05-17.jsonl"
    ),
    Path(
        r"research\science_program_2026_05\06_outcome_testing"
        r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
        r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_BUNDLE_GUARD_COMPONENT_LEDGER_2026-05-17.jsonl"
    ),
    Path(
        r"research\science_program_2026_05\06_outcome_testing"
        r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
        r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_BUNDLE_MARKET_COMPONENT_LEDGER_2026-05-17.jsonl"
    ),
    Path(
        r"research\science_program_2026_05\06_outcome_testing"
        r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
        r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_BUNDLE_MARKET_ROLLUP_LEDGER_2026-05-17.jsonl"
    ),
    Path(
        r"research\science_program_2026_05\06_outcome_testing"
        r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
        r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_BUNDLE_NOFILL_COMPONENT_LEDGER_2026-05-17.jsonl"
    ),
    Path(
        r"research\science_program_2026_05\06_outcome_testing"
        r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
        r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_BUNDLE_RECHECK_COMPONENT_LEDGER_2026-05-17.jsonl"
    ),
    Path(
        r"research\science_program_2026_05\06_outcome_testing"
        r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
        r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_BUNDLE_SCORER_COMPONENT_LEDGER_2026-05-17.jsonl"
    ),
    Path(
        r"research\science_program_2026_05\06_outcome_testing"
        r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
        r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_BUNDLE_SOURCE_COMPONENT_LEDGER_2026-05-17.jsonl"
    ),
    Path(
        r"research\science_program_2026_05\06_outcome_testing"
        r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
        r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_EXECUTABLE_ARTIFACTS_BUNDLE_MARKET_ROLLUP_LEDGER_2026-05-17.jsonl"
    ),
    Path(
        r"research\science_program_2026_05\06_outcome_testing"
        r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
        r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_IMPLEMENTATION_EXECUTION_BUNDLE_MARKET_ROLLUP_LEDGER_2026-05-17.jsonl"
    ),
    Path(
        r"research\science_program_2026_05\06_outcome_testing"
        r"\weekend_mechanical_edge_factory_moonshot_2026_05_15"
        r"\HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_RUNTIME_SURFACES_BUNDLE_MARKET_ROLLUP_LEDGER_2026-05-17.jsonl"
    ),
]


def _metric(sum_value: float, count: float = 1.0) -> dict:
    return {
        "sum": sum_value,
        "mean": sum_value / count if count else None,
        "match_rows_with_metric": count,
        "positive_rows": 1 if sum_value > 0 else 0,
        "negative_rows": 1 if sum_value < 0 else 0,
        "zero_rows": 1 if sum_value == 0 else 0,
    }


def _review_row(row_id: str, scope: dict, review_action: str, *, r: float, stress: float, n: float, proxy=None, **extra):
    row = {
        "review_row_id": row_id,
        "row_type": "gtos_vnext_default_off_registry_review_row",
        "review_action": review_action,
        "event_scope": scope,
        "source_event_rows": 3,
        "source_weighted_registry_match_rows": 3,
        "unique_scope_registry_match_rows": 1,
        "review_pressure": 12.5,
        "source_path": "shadow_logs/strategy_follow_candidates.jsonl",
        "source_name": "cp281_rule_replay_result_table",
        "evidence_family": "cp281_native_rule_replay",
        "r_metric_traces": {
            "cost_adjusted_simulated_r": _metric(r),
            "stress_simulated_r": _metric(stress),
            "effective_n": _metric(n),
            "proxy_score": _metric(proxy) if proxy is not None else {
                "sum": None,
                "mean": None,
                "match_rows_with_metric": 0,
                "positive_rows": 0,
                "negative_rows": 0,
                "zero_rows": 0,
            },
        },
    }
    row.update(extra)
    return row


def _production_change_promotion_row(
    row_id: str,
    scope: dict,
    review_action: str,
    *,
    r: float,
    n: float,
    proxy: float | None = None,
    source_component: str = "nofill_near_miss_market_entry",
    action_class: str = "vnext_production_change_follow_scorer",
    route_family: str = "nofill_mechanical",
    framework: str = "breaker_re_entry",
    target_stop_order_class: str = "TARGET_FIRST_PROXY_DOMINANT",
    proxy_r_class: str = "STRONG_POSITIVE_PROXY_R",
) -> dict:
    return {
        "schema_version": "vnext_production_change_runtime_change_row_v1",
        "route_id": "vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25",
        "stage_id": "STAGE_02_PROMOTION_IMPLEMENTATION",
        "row_type": "gtos_vnext_production_change_promoted_runtime_row",
        "review_row_id": row_id,
        "row_key": row_id,
        "source_row_id": f"decision-map-{row_id}",
        "event_scope": scope,
        "review_action": review_action,
        "source_name": "vnext_production_change_promoted_stage06_final_map",
        "evidence_family": "gtos_vnext_production_change_promotions",
        "source_group": "ltf_path_nofill_pending_lifecycle_engine",
        "source_role": "production_change_promotion",
        "system_surface": "ltf_path_nofill_pending_lifecycle_engine",
        "source_component": source_component,
        "action_family": "production_change_follow_pressure",
        "action_class": action_class,
        "framework": framework,
        "route_family": route_family,
        "market_timeframe": scope.get("market_timeframe", "M15"),
        "timeframe": scope.get("timeframe", "M15"),
        "route_session": scope.get("route_session"),
        "side": scope.get("side"),
        "symbol": scope.get("symbol"),
        "source_symbol": scope.get("source_symbol"),
        "symbol_family": scope.get("symbol_family"),
        "market": scope.get("market"),
        "proxy_r_class": proxy_r_class,
        "target_stop_order_class": target_stop_order_class,
        "r_evidence_class": "STAGE06_REPLAY_PROMOTION_PROXY_R",
        "implementation_action": "PROMOTE_REPLAY_MEASURED_FOLLOW_PRESSURE_ACTIVATION_GATED",
        "r_metric_traces": {
            "cost_adjusted_simulated_r": _metric(r, n),
            "stress_simulated_r": _metric(r, n),
            "effective_n": _metric(n, 1),
            "proxy_score": _metric(proxy if proxy is not None else r, n),
        },
        "runtime_candidate_use_permitted": True,
        "activation_gated": True,
        "production_activation_gate": "gtos_vnext_runtime.apply_to_execution",
        "pre_ai_activation_gate": "gtos_vnext_runtime.pre_ai_apply_to_ai_call",
        "live_effect": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
        "runtime_trading_or_live_broker_effect": False,
        "requires_owner_review_before_runtime_effect": True,
    }


def _production_change_guard_row(
    row_id: str,
    scope: dict,
    review_action: str,
    *,
    r: float,
    n: float,
    source_component: str,
    action_class: str,
    route_family: str = "nofill_mechanical",
    framework: str = "breaker_re_entry",
    target_stop_order_class: str = "STOP_FIRST_PROXY_DOMINANT",
    proxy_r_class: str = "STRONG_NEGATIVE_PROXY_R",
    source_final_decision: str = "KILL_OR_REDESIGN_BEFORE_USE",
) -> dict:
    row = _production_change_promotion_row(
        row_id,
        scope,
        review_action,
        r=r,
        n=n,
        proxy=r,
        source_component=source_component,
        action_class=action_class,
        route_family=route_family,
        framework=framework,
        target_stop_order_class=target_stop_order_class,
        proxy_r_class=proxy_r_class,
    )
    row.update(
        {
            "schema_version": "vnext_production_change_kill_redesign_guard_row_v1",
            "row_type": "gtos_vnext_production_change_kill_redesign_guard_row",
            "source_name": "vnext_production_change_stage03_kill_redesign_guards",
            "evidence_family": "gtos_vnext_production_change_kill_redesign_guards",
            "source_role": "production_change_kill_redesign_guard",
            "action_family": (
                "production_change_kill_avoid_guard"
                if "AVOID" in review_action
                else "production_change_non_override_guard"
            ),
            "implementation_action": (
                "ENFORCE_KILL_REDESIGN_AVOID_OR_NOFILL_GUARD"
                if "AVOID" in review_action
                else "ENFORCE_GUARD_ONLY_NO_DIRECTIONAL_PRESSURE"
            ),
            "source_final_decision": source_final_decision,
            "guard_only_no_directional_pressure": "MIXED" in review_action,
            "kill_redesign_avoid_guard": "AVOID" in review_action,
        }
    )
    return row


def _production_change_mixed_resolution_row(
    row_id: str,
    scope: dict,
    review_action: str,
    *,
    r: float,
    n: float,
    resolution_class: str,
    source_component: str,
    action_class: str,
    route_family: str = "numeric_router",
    framework: str = "ob_retest",
    target_stop_order_class: str = "MIXED_RESOLUTION_AVOID_CONTEXT",
    proxy_r_class: str = "USEFUL_AVOID_CONTEXT_PROXY_R",
) -> dict:
    row = _production_change_promotion_row(
        row_id,
        scope,
        review_action,
        r=r,
        n=n,
        proxy=r,
        source_component=source_component,
        action_class=action_class,
        route_family=route_family,
        framework=framework,
        target_stop_order_class=target_stop_order_class,
        proxy_r_class=proxy_r_class,
    )
    decision = "FOLLOW" if "FOLLOW" in review_action else "AVOID" if "AVOID" in review_action else "MIXED"
    row.update(
        {
            "schema_version": "vnext_production_change_mixed_resolution_row_v1",
            "stage_id": "STAGE_04_MIXED_RESOLUTION",
            "row_type": "gtos_vnext_production_change_mixed_resolution_row",
            "source_name": "vnext_production_change_stage04_mixed_resolution",
            "evidence_family": "gtos_vnext_production_change_mixed_resolution",
            "source_role": "production_change_mixed_resolution",
            "source_group": "route_decision_scorer_filter_router",
            "system_surface": "route_decision_scorer_filter_router",
            "action_family": (
                "production_change_mixed_follow_pressure"
                if decision == "FOLLOW"
                else "production_change_mixed_avoid_pressure"
                if decision == "AVOID"
                else "production_change_mixed_non_override_guard"
            ),
            "computed_decision": decision,
            "implementation_action": (
                "RESOLVE_MIXED_REPLAY_FOLLOW_PRESSURE_ACTIVATION_GATED"
                if decision == "FOLLOW"
                else "RESOLVE_MIXED_REPLAY_AVOID_PRESSURE_ACTIVATION_GATED"
                if decision == "AVOID"
                else "KILL_OR_REDESIGN_HARMFUL_OVERBLOCK_AS_NON_OVERRIDE_GUARD"
            ),
            "mixed_resolution_class": resolution_class,
            "resolution_class": resolution_class,
            "r_evidence_class": "STAGE05_MIXED_RESOLUTION_REPLAY_PROXY_R",
            "runtime_candidate_use_permitted": decision in {"FOLLOW", "AVOID"},
            "mixed_resolution_follow_pressure": decision == "FOLLOW",
            "mixed_resolution_avoid_pressure": decision == "AVOID",
            "mixed_resolution_non_override_guard": decision == "MIXED",
            "harmful_overblock_killed_or_redesigned": (
                resolution_class == "harmful_overblock_context"
            ),
        }
    )
    return row


def _config(path, *, enabled=True, apply=False):
    return {
        "gtos_vnext_runtime": {
            "enabled": enabled,
            "apply_to_execution": apply,
            "review_artifact_path": str(path),
            "min_scope_fields": 1,
        },
        "model_a": {"entry_timeframe": "M15"},
    }


def _write_jsonl(path, rows):
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    vnext_runtime_mod._load_evidence_index_cached.cache_clear()


def _current_usdjpy_london_long_route_rows(cfg):
    runtime_cfg = cfg["gtos_vnext_runtime"]
    index = vnext_runtime_mod._runtime_index_for_evaluation(
        config=cfg,
        artifact_rows=None,
        artifact_index=None,
    )
    events = vnext_runtime_mod._artifact_scoped_route_events(
        {"symbol": "USDJPY", "source_symbol": "USDJPY", "kill_zone": "london", "direction": "LONG"},
        cfg=runtime_cfg,
        prefix="post_l2",
        artifact_index=index,
    )
    min_scope_fields = int(runtime_cfg.get("min_scope_fields", 1) or 1)
    excluded_families = vnext_runtime_mod._route_event_excluded_evidence_families(runtime_cfg)
    raw_rows = []
    selected_rows = []
    for event in events:
        normalized = vnext_runtime_mod.normalize_event(event)
        criteria_key = vnext_runtime_mod._event_criteria_key(normalized)
        candidate_indices = set()
        for size in range(1, len(criteria_key) + 1):
            for subset in combinations(criteria_key, size):
                candidate_indices.update(index._scope_key_index.get(tuple(subset), ()))
        matches = []
        for row_index in sorted(candidate_indices):
            scope = index.scopes[row_index]
            if len(scope) < min_scope_fields:
                continue
            row = index.rows[row_index]
            if vnext_runtime_mod._normalized(row.get("evidence_family")) in excluded_families:
                continue
            if vnext_runtime_mod._scope_matches(scope, normalized) and (
                vnext_runtime_mod._row_matches_event_filters(row, normalized)
            ):
                matches.append(dict(row))
        raw_rows.extend(matches)
        selected_rows.extend(
            vnext_runtime_mod._select_runtime_rows(
                matches,
                cfg=runtime_cfg,
                min_scope_fields=min_scope_fields,
                normalized_event=normalized,
            )
        )
    return (
        vnext_runtime_mod._dedupe_rows(raw_rows),
        vnext_runtime_mod._dedupe_rows(selected_rows),
    )


def test_runtime_returns_follow_with_r_proxy_stress_and_effective_n(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "follow-row",
                {"symbol": "GBPJPY", "source_symbol": "GBPJPY", "route_session": "tokyo", "side": "LONG"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=33.8,
                stress=33.7,
                n=325609,
                proxy=4.2,
            )
        ],
    )

    decision = evaluate_vnext_event(
        {"broker_symbol": "GBPJPY", "kill_zone": "tokyo", "direction": "LONG"},
        _config(artifact),
    )

    assert decision.decision == "FOLLOW"
    assert decision.matched is True
    assert decision.event == {
        "symbol": "GBPJPY",
        "source_symbol": "GBPJPY",
        "market": "GBPJPY",
        "route_session": "tokyo",
        "side": "LONG",
    }
    metrics = decision.evidence["metrics"]
    assert metrics["cost_adjusted_simulated_r"]["sum"] == 33.8
    assert metrics["proxy_score"]["sum"] == 4.2
    assert metrics["stress_simulated_r"]["sum"] == 33.7
    assert metrics["effective_n"]["sum"] == 325609


def test_runtime_caps_detailed_rows_without_erasing_dimension_counts(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    scope = {"symbol": "GBPJPY", "source_symbol": "GBPJPY", "route_session": "ny", "side": "LONG"}
    _write_jsonl(
        artifact,
        [
            _review_row(
                f"row-{idx}",
                scope,
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=1.0,
                stress=1.0,
                n=10,
                source_component="nofill_far_miss_retest",
                target_stop_order_class="TARGET_FIRST_PROXY_DOMINANT",
                source_row_id=f"SOURCE-{idx}",
            )
            for idx in range(3)
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"]["evidence_row_detail_limit"] = 1
    cfg["gtos_vnext_runtime"]["evidence_id_list_limit"] = 2

    decision = evaluate_vnext_event(
        {"broker_symbol": "GBPJPY", "kill_zone": "ny", "direction": "LONG"},
        cfg,
    )

    assert decision.evidence["matched_rows"] == 3
    assert decision.evidence["source_component_counts"] == {"nofill_far_miss_retest": 3}
    assert decision.evidence["target_stop_order_class_counts"] == {"TARGET_FIRST_PROXY_DOMINANT": 3}
    assert decision.evidence["matched_row_id_count"] == 3
    assert decision.evidence["matched_row_ids"] == ["row-0", "row-1"]
    assert decision.evidence["matched_row_ids_truncated"] is True
    assert decision.evidence["source_row_id_count"] == 3
    assert decision.evidence["source_row_ids"] == ["SOURCE-0", "SOURCE-1"]
    assert decision.evidence["source_row_ids_truncated"] is True
    assert decision.evidence["row_detail_count"] == 1
    assert decision.evidence["row_details_truncated"] is True
    assert decision.evidence["rows"][0]["row_id"] == "row-0"


def test_runtime_returns_avoid_from_real_event_field_aliases(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "avoid-row",
                {"symbol": "NAS100", "source_symbol": "NAS100", "route_session": "london", "side": "SHORT"},
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-81.2,
                stress=-625.6,
                n=11475,
            )
        ],
    )

    decision = evaluate_vnext_event(
        {"candidate_symbol": "NAS100", "session": "london", "selected_side": "SHORT"},
        _config(artifact),
    )

    assert decision.decision == "AVOID"
    assert decision.evidence["matched_rows"] == 1
    assert decision.evidence["metrics"]["cost_adjusted_simulated_r"]["sum"] == -81.2


def test_runtime_returns_mixed_when_same_specific_scope_conflicts(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    scope = {"symbol": "USDJPY", "route_session": "london", "side": "SHORT"}
    _write_jsonl(
        artifact,
        [
            _review_row("follow-row", scope, "DEFAULT_OFF_FOLLOW_SCORER_REVIEW", r=10, stress=8, n=50),
            _review_row("avoid-row", scope, "DEFAULT_OFF_AVOID_FILTER_REVIEW", r=-12, stress=-40, n=50),
        ],
    )

    decision = evaluate_vnext_event(
        {"symbol": "USDJPY", "route_session": "london", "side": "SHORT"},
        _config(artifact),
    )

    assert decision.decision == "MIXED"
    assert decision.evidence["matched_rows"] == 2
    assert decision.evidence["decision_counts"] == {"FOLLOW": 1, "AVOID": 1}


def test_runtime_scope_selection_can_preserve_all_matching_less_specific_rows(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "specific-follow",
                {
                    "symbol": "XAUUSD",
                    "route_session": "ny",
                    "side": "LONG",
                    "framework": "ob_retest",
                },
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=4,
                stress=3,
                n=20,
            ),
            _review_row(
                "broader-avoid",
                {"symbol": "XAUUSD", "route_session": "ny"},
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-5,
                stress=-7,
                n=25,
                source_component="market_gap_code",
            ),
        ],
    )
    event = {
        "symbol": "XAUUSD",
        "kill_zone": "ny",
        "side": "LONG",
        "framework": "ob_retest",
    }

    max_specificity = evaluate_vnext_event(event, _config(artifact))
    all_matching_cfg = _config(artifact)
    all_matching_cfg["gtos_vnext_runtime"]["scope_selection_policy"] = "all_matching"
    all_matching = evaluate_vnext_event(event, all_matching_cfg)

    assert max_specificity.decision == "FOLLOW"
    assert max_specificity.evidence["matched_rows"] == 1
    assert max_specificity.evidence["scope_selection_policy"] == "max_specificity"
    assert all_matching.decision == "MIXED"
    assert all_matching.evidence["matched_rows"] == 2
    assert all_matching.evidence["decision_counts"] == {"FOLLOW": 1, "AVOID": 1}
    assert all_matching.evidence["source_component_decision_counts"] == {
        "market_gap_code": {"AVOID": 1}
    }
    assert all_matching.evidence["scope_selection_policy"] == "all_matching"


def test_runtime_anchored_scope_selection_blocks_unanchored_generic_dominance(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "specific-follow",
                {
                    "symbol": "USDJPY",
                    "route_session": "london",
                    "side": "LONG",
                    "framework": "ob_retest",
                },
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=4,
                stress=3,
                n=20,
            ),
            _review_row(
                "route-family-only-avoid",
                {"route_family": "cp281_native_rule"},
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-100,
                stress=-100,
                n=10000,
            ),
            _review_row(
                "anchored-less-specific-avoid",
                {"symbol": "USDJPY", "route_session": "london", "side": "LONG"},
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-3,
                stress=-2,
                n=10,
                source_component="market_gap_code",
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update({
        "scope_selection_policy": "all_matching_anchored",
        "scope_required_anchor_groups": [
            ["symbol", "source_symbol", "symbol_family", "market"],
            ["route_session"],
            ["side"],
        ],
    })

    decision = evaluate_vnext_event(
        {"symbol": "USDJPY", "kill_zone": "london", "side": "LONG", "framework": "ob_retest"},
        cfg,
    )

    assert decision.decision == "MIXED"
    assert decision.evidence["matched_rows"] == 2
    assert decision.evidence["matched_row_ids"] == [
        "specific-follow",
        "anchored-less-specific-avoid",
    ]
    assert decision.evidence["source_component_decision_counts"] == {
        "market_gap_code": {"AVOID": 1}
    }
    assert decision.evidence["scope_selection_policy"] == "all_matching_anchored"
    assert decision.evidence["scope_required_anchor_groups"] == [
        ["symbol", "source_symbol", "symbol_family", "market"],
        ["route_session"],
        ["side"],
    ]


def test_production_change_promotion_row_drives_shadow_pending_market_entry():
    scope = {
        "symbol": "GBPJPY",
        "source_symbol": "GBPJPY",
        "market": "GBPJPY",
        "route_session": "ny_core",
        "side": "LONG",
        "framework": "breaker_re_entry",
        "route_family": "nofill_mechanical",
        "market_timeframe": "M15",
        "timeframe": "M15",
        "source_component": "static_limit_adaptive_entry_challenger",
        "target_stop_order_class": "TARGET_FIRST_PROXY_DOMINANT",
        "proxy_r_class": "STRONG_POSITIVE_PROXY_R",
    }
    row = _production_change_promotion_row(
        "prodchg-follow",
        scope,
        "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
        r=11.12,
        n=39,
        proxy=11.12,
        source_component="static_limit_adaptive_entry_challenger",
    )
    cfg = _config("unused.jsonl")
    cfg["gtos_vnext_runtime"].update(
        {
            "apply_to_execution": False,
            "scope_selection_policy": "all_matching_anchored",
            "scope_required_anchor_groups": [
                ["symbol", "source_symbol", "symbol_family", "market"],
                ["route_session"],
                ["side"],
            ],
            "post_l2_evaluate_route_variants": True,
            "post_l2_prune_route_variants_to_artifact_scopes": True,
            "post_l2_match_artifact_scopes_directly": True,
            "post_l2_route_use_candidate_framework_only": True,
            "post_l2_route_timeframes": ["M15"],
            "post_l2_route_horizons": [""],
            "post_l2_route_frameworks": [],
            "post_l2_route_families": ["nofill_mechanical"],
            "post_l2_route_source_components": [
                "static_limit_adaptive_entry_challenger",
            ],
            "pending_policy_enabled": True,
            "pending_policy_market_entry_enabled": True,
            "pending_policy_static_limit_adaptive_entry_enabled": True,
            "pending_policy_market_entry_requires_follow": True,
            "pending_policy_market_entry_requires_positive_proxy": True,
            "pending_policy_use_source_component_decisions": True,
            "pending_policy_market_entry_requires_component_follow": True,
        }
    )

    decision = evaluate_vnext_route_event(
        {
            "symbol": "GBPJPY",
            "source_symbol": "GBPJPY",
            "kill_zone": "ny",
            "side": "LONG",
            "framework": "breaker_re_entry",
            "effective_framework": "breaker_re_entry",
            "market_timeframe": "M15",
        },
        cfg,
        artifact_rows=[row],
    )
    pending = evaluate_vnext_pending_policy(decision=decision, config=cfg)

    assert decision.decision == "FOLLOW"
    assert decision.matched is True
    assert decision.evidence["source_component_counts"] == {
        "static_limit_adaptive_entry_challenger": 1
    }
    assert decision.evidence["proxy_r_class_counts"] == {"STRONG_POSITIVE_PROXY_R": 1}
    assert pending.action == "PLACE_LIMIT"
    assert pending.would_action == "MARKET_ENTRY_NOW"
    assert pending.applied is False
    assert pending.evidence_summary["static_limit_adaptive_entry_rows"] == 1

    active_cfg = _config("unused.jsonl", apply=True)
    active_cfg["gtos_vnext_runtime"].update(cfg["gtos_vnext_runtime"])
    active_cfg["gtos_vnext_runtime"]["apply_to_execution"] = True
    active_decision = evaluate_vnext_route_event(
        {
            "symbol": "GBPJPY",
            "source_symbol": "GBPJPY",
            "kill_zone": "ny",
            "side": "LONG",
            "framework": "breaker_re_entry",
            "effective_framework": "breaker_re_entry",
            "market_timeframe": "M15",
        },
        active_cfg,
        artifact_rows=[row],
    )
    active_pending = evaluate_vnext_pending_policy(decision=active_decision, config=active_cfg)

    assert active_pending.action == "MARKET_ENTRY_NOW"
    assert active_pending.applied is True


def test_production_change_unanchored_promotion_guard_cannot_dominate_runtime():
    row = _production_change_promotion_row(
        "prodchg-unanchored",
        {"route_family": "numeric_router"},
        "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
        r=500,
        n=500,
        source_component="vnext_production_change_unknown_component",
        route_family="numeric_router",
        framework="ob_retest",
    )
    cfg = _config("unused.jsonl")
    cfg["gtos_vnext_runtime"].update(
        {
            "scope_selection_policy": "all_matching_anchored",
            "scope_required_anchor_groups": [
                ["symbol", "source_symbol", "symbol_family", "market"],
                ["route_session"],
                ["side"],
            ],
        }
    )

    decision = evaluate_vnext_event(
        {"symbol": "XAUUSD", "route_session": "ny", "side": "LONG", "framework": "ob_retest"},
        cfg,
        artifact_rows=[row],
    )

    assert decision.decision == "LEGACY"
    assert decision.matched is False
    assert decision.reason == "no_matching_vnext_scope"


def test_production_change_kill_redesign_stop_first_guard_blocks_pending_entry():
    scope = {
        "symbol": "GBPJPY",
        "source_symbol": "GBPJPY",
        "market": "GBPJPY",
        "route_session": "tokyo_kz",
        "side": "SHORT",
        "framework": "breaker_re_entry",
        "route_family": "nofill_mechanical",
        "market_timeframe": "M15",
        "timeframe": "M15",
        "source_component": "nofill_far_miss_avoid",
        "target_stop_order_class": "STOP_FIRST_PROXY_DOMINANT",
        "proxy_r_class": "STRONG_NEGATIVE_PROXY_R",
    }
    row = _production_change_guard_row(
        "prodchg-kill-stop-first",
        scope,
        "DEFAULT_OFF_AVOID_FILTER_REVIEW",
        r=-9.4,
        n=40,
        source_component="nofill_far_miss_avoid",
        action_class="filled_then_stop_first",
    )
    cfg = _config("unused.jsonl")
    cfg["gtos_vnext_runtime"].update(
        {
            "apply_to_execution": False,
            "scope_selection_policy": "all_matching_anchored",
            "scope_required_anchor_groups": [
                ["symbol", "source_symbol", "symbol_family", "market"],
                ["route_session"],
                ["side"],
            ],
            "post_l2_evaluate_route_variants": True,
            "post_l2_prune_route_variants_to_artifact_scopes": True,
            "post_l2_match_artifact_scopes_directly": True,
            "post_l2_route_use_candidate_framework_only": True,
            "post_l2_route_timeframes": ["M15"],
            "post_l2_route_horizons": [""],
            "post_l2_route_frameworks": [],
            "post_l2_route_families": ["nofill_mechanical"],
            "post_l2_route_source_components": ["nofill_far_miss_avoid"],
            "pending_policy_enabled": True,
            "pending_policy_nofill_avoid_requires_component_avoid": True,
            "pending_policy_offset_avoid_requires_negative_proxy": True,
        }
    )

    decision = evaluate_vnext_route_event(
        {
            "symbol": "GBPJPY",
            "source_symbol": "GBPJPY",
            "kill_zone": "tokyo",
            "side": "SHORT",
            "framework": "breaker_re_entry",
            "effective_framework": "breaker_re_entry",
            "market_timeframe": "M15",
        },
        cfg,
        artifact_rows=[row],
    )
    pending = evaluate_vnext_pending_policy(decision=decision, config=cfg)

    assert decision.decision == "AVOID"
    assert decision.evidence["source_component_counts"] == {"nofill_far_miss_avoid": 1}
    assert decision.evidence["target_stop_order_class_counts"] == {
        "STOP_FIRST_PROXY_DOMINANT": 1
    }
    assert pending.action == "PLACE_LIMIT"
    assert pending.would_action == "SKIP_PENDING_NOFILL_AVOID"
    assert pending.applied is False

    active_cfg = _config("unused.jsonl", apply=True)
    active_cfg["gtos_vnext_runtime"].update(cfg["gtos_vnext_runtime"])
    active_cfg["gtos_vnext_runtime"]["apply_to_execution"] = True
    active_decision = evaluate_vnext_route_event(
        {
            "symbol": "GBPJPY",
            "source_symbol": "GBPJPY",
            "kill_zone": "tokyo",
            "side": "SHORT",
            "framework": "breaker_re_entry",
            "effective_framework": "breaker_re_entry",
            "market_timeframe": "M15",
        },
        active_cfg,
        artifact_rows=[row],
    )
    active_pending = evaluate_vnext_pending_policy(decision=active_decision, config=active_cfg)

    assert active_pending.action == "SKIP_PENDING_NOFILL_AVOID"
    assert active_pending.applied is True


def test_production_change_guard_only_row_remains_mixed_non_override_context():
    row = _production_change_guard_row(
        "prodchg-guard-only",
        {
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market": "XAUUSD",
            "route_session": "ny_core",
            "side": "LONG",
            "route_family": "numeric_router",
            "market_timeframe": "M15",
            "timeframe": "M15",
        },
        "DEFAULT_OFF_MIXED_SOURCE_REPAIR_GUARD",
        r=0.0,
        n=10,
        source_component="vnext_production_change_non_override_guard",
        action_class="unknown_action_class",
        route_family="numeric_router",
        framework="ob_retest",
        target_stop_order_class="GUARD_ONLY_TARGET_STOP_CONTEXT",
        proxy_r_class="GUARD_ONLY_PROXY_R",
        source_final_decision="KEEP_SHADOW_OR_GUARD_ONLY",
    )
    cfg = _config("unused.jsonl")
    cfg["gtos_vnext_runtime"].update(
        {
            "scope_selection_policy": "all_matching_anchored",
            "scope_required_anchor_groups": [
                ["symbol", "source_symbol", "symbol_family", "market"],
                ["route_session"],
                ["side"],
            ],
        }
    )

    decision = evaluate_vnext_event(
        {
            "symbol": "XAUUSD",
            "route_session": "ny",
            "side": "LONG",
            "route_family": "numeric_router",
            "market_timeframe": "M15",
            "timeframe": "M15",
        },
        cfg,
        artifact_rows=[row],
    )

    assert decision.decision == "MIXED"
    assert decision.matched is True
    assert decision.evidence["decision_counts"] == {"MIXED": 1}
    assert decision.evidence["source_name_decision_counts"] == {
        "vnext_production_change_stage03_kill_redesign_guards": {"MIXED": 1}
    }


def test_production_change_mixed_follow_candidate_casts_activation_gated_follow():
    scope = {
        "symbol": "USDJPY",
        "source_symbol": "USDJPY",
        "market": "USDJPY",
        "route_session": "ny_core",
        "side": "LONG",
        "framework": "ob_retest",
        "route_family": "numeric_router",
        "market_timeframe": "M15",
        "timeframe": "M15",
        "source_component": "l2_entry_in_ob_rejection_value",
        "target_stop_order_class": "MIXED_RESOLUTION_FOLLOW_CONTEXT",
        "proxy_r_class": "POSITIVE_PROXY_R",
    }
    row = _production_change_mixed_resolution_row(
        "prodchg-mixed-follow",
        scope,
        "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
        r=9.2,
        n=76,
        resolution_class="replay_resolvable_into_follow_candidate",
        source_component="l2_entry_in_ob_rejection_value",
        action_class="l2_entry_in_ob_rejection_value_context_guard",
        target_stop_order_class="MIXED_RESOLUTION_FOLLOW_CONTEXT",
        proxy_r_class="POSITIVE_PROXY_R",
    )
    cfg = _config("unused.jsonl")
    cfg["gtos_vnext_runtime"].update(
        {
            "scope_selection_policy": "all_matching_anchored",
            "scope_required_anchor_groups": [
                ["symbol", "source_symbol", "symbol_family", "market"],
                ["route_session"],
                ["side"],
            ],
        }
    )

    decision = evaluate_vnext_event(
        {
            "symbol": "USDJPY",
            "source_symbol": "USDJPY",
            "route_session": "ny",
            "side": "LONG",
            "framework": "ob_retest",
            "route_family": "numeric_router",
            "market_timeframe": "M15",
            "timeframe": "M15",
            "source_component": "l2_entry_in_ob_rejection_value",
        },
        cfg,
        artifact_rows=[row],
    )

    assert decision.matched is True
    assert decision.decision == "FOLLOW"
    assert decision.evidence["evidence_family_counts"] == {
        "gtos_vnext_production_change_mixed_resolution": 1
    }
    assert decision.evidence["source_name_decision_counts"] == {
        "vnext_production_change_stage04_mixed_resolution": {"FOLLOW": 1}
    }


def test_production_change_mixed_useful_avoid_context_blocks_only_when_activated():
    scope = {
        "symbol": "NAS100",
        "source_symbol": "NAS100",
        "market": "NAS100",
        "route_session": "ny_core",
        "side": "SHORT",
        "framework": "breaker_re_entry",
        "route_family": "numeric_router",
        "market_timeframe": "M15",
        "timeframe": "M15",
        "source_component": "rejected_candidate_ob_proximity_value",
        "target_stop_order_class": "MIXED_RESOLUTION_AVOID_CONTEXT",
        "proxy_r_class": "USEFUL_AVOID_CONTEXT_PROXY_R",
    }
    row = _production_change_mixed_resolution_row(
        "prodchg-mixed-avoid",
        scope,
        "DEFAULT_OFF_AVOID_FILTER_REVIEW",
        r=18.0,
        n=120,
        resolution_class="useful_avoid_context",
        source_component="rejected_candidate_ob_proximity_value",
        action_class="rejected_candidate_ob_proximity_value_avoid_filter",
    )
    cfg = _config("unused.jsonl")
    cfg["gtos_vnext_runtime"].update(
        {
            "scope_selection_policy": "all_matching_anchored",
            "scope_required_anchor_groups": [
                ["symbol", "source_symbol", "symbol_family", "market"],
                ["route_session"],
                ["side"],
            ],
        }
    )

    shadow_decision = evaluate_vnext_event(
        {
            "symbol": "NAS100",
            "source_symbol": "NAS100",
            "route_session": "ny",
            "side": "SHORT",
            "framework": "breaker_re_entry",
            "route_family": "numeric_router",
            "market_timeframe": "M15",
            "timeframe": "M15",
            "source_component": "rejected_candidate_ob_proximity_value",
        },
        cfg,
        artifact_rows=[row],
    )
    assert shadow_decision.decision == "AVOID"
    assert vnext_blocks_execution(shadow_decision, cfg) is False

    active_cfg = _config("unused.jsonl", apply=True)
    active_cfg["gtos_vnext_runtime"].update(cfg["gtos_vnext_runtime"])
    active_cfg["gtos_vnext_runtime"]["apply_to_execution"] = True
    active_decision = evaluate_vnext_event(
        {
            "symbol": "NAS100",
            "source_symbol": "NAS100",
            "route_session": "ny",
            "side": "SHORT",
            "framework": "breaker_re_entry",
            "route_family": "numeric_router",
            "market_timeframe": "M15",
            "timeframe": "M15",
            "source_component": "rejected_candidate_ob_proximity_value",
        },
        active_cfg,
        artifact_rows=[row],
    )

    assert active_decision.decision == "AVOID"
    assert vnext_blocks_execution(active_decision, active_cfg) is True


def test_production_change_mixed_harmful_overblock_context_is_not_hidden_avoid():
    row = _production_change_mixed_resolution_row(
        "prodchg-mixed-harmful-overblock",
        {
            "symbol": "EURUSD",
            "source_symbol": "EURUSD",
            "market": "EURUSD",
            "route_session": "ny_core",
            "side": "LONG",
            "framework": "ob_retest",
            "route_family": "numeric_router",
            "market_timeframe": "M15",
            "timeframe": "M15",
            "target_stop_order_class": "HARMFUL_OVERBLOCK_REDESIGN_GUARD",
            "proxy_r_class": "HARMFUL_OVERBLOCK_GUARD_PROXY_R",
        },
        "DEFAULT_OFF_MIXED_SOURCE_REPAIR_GUARD",
        r=30.5,
        n=102,
        resolution_class="harmful_overblock_context",
        source_component="l2_h1_poi_rejection_value",
        action_class="l2_h1_poi_rejection_value_avoid_filter",
        target_stop_order_class="HARMFUL_OVERBLOCK_REDESIGN_GUARD",
        proxy_r_class="HARMFUL_OVERBLOCK_GUARD_PROXY_R",
    )
    cfg = _config("unused.jsonl", apply=True)
    cfg["gtos_vnext_runtime"].update(
        {
            "apply_to_execution": True,
            "scope_selection_policy": "all_matching_anchored",
            "scope_required_anchor_groups": [
                ["symbol", "source_symbol", "symbol_family", "market"],
                ["route_session"],
                ["side"],
            ],
        }
    )

    decision = evaluate_vnext_event(
        {
            "symbol": "EURUSD",
            "source_symbol": "EURUSD",
            "route_session": "ny",
            "side": "LONG",
            "framework": "ob_retest",
            "route_family": "numeric_router",
            "market_timeframe": "M15",
            "timeframe": "M15",
        },
        cfg,
        artifact_rows=[row],
    )

    assert decision.matched is True
    assert decision.decision == "MIXED"
    assert decision.evidence["decision_counts"] == {"MIXED": 1}
    assert vnext_blocks_execution(decision, cfg) is False


def test_runtime_specific_event_fields_block_broad_adverse_dominance(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "specific-follow",
                {
                    "symbol": "USDJPY",
                    "source_symbol": "USDJPY",
                    "route_session": "london",
                    "side": "LONG",
                    "framework": "ob_retest",
                    "source_component": "shadow_source_guard",
                },
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=4,
                stress=3,
                n=20,
                source_component="shadow_source_guard",
            ),
            _review_row(
                "broad-adverse-avoid",
                {"symbol": "USDJPY", "source_symbol": "USDJPY", "route_session": "london", "side": "LONG"},
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-100,
                stress=-100,
                n=10000,
                source_component="market_gap_code",
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "scope_selection_policy": "all_matching_anchored",
            "scope_required_anchor_groups": [
                ["symbol", "source_symbol", "symbol_family", "market"],
                ["route_session"],
                ["side"],
            ],
            "scope_prefer_event_specific_fields_enabled": True,
            "scope_prefer_event_specific_fields": ["framework", "source_component"],
            "conflict_resolution": "evidence_weighted",
        }
    )

    decision = evaluate_vnext_event(
        {
            "symbol": "USDJPY",
            "source_symbol": "USDJPY",
            "kill_zone": "london",
            "side": "LONG",
            "framework": "ob_retest",
            "source_component": "shadow_source_guard",
        },
        cfg,
    )

    assert decision.decision == "FOLLOW"
    assert decision.evidence["matched_row_ids"] == ["specific-follow"]
    assert decision.evidence["decision_counts"] == {"FOLLOW": 1}
    assert decision.evidence["source_component_decision_counts"] == {
        "shadow_source_guard": {"FOLLOW": 1}
    }


def test_runtime_prefers_exact_session_over_all_sessions_when_available(tmp_path):
    artifact = tmp_path / "vnext_session_specificity.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "london-follow",
                {"symbol": "USDJPY", "route_session": "london", "side": "LONG"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=3,
                stress=2,
                n=20,
            ),
            _review_row(
                "all-sessions-avoid",
                {"symbol": "USDJPY", "route_session": "ALL_SESSIONS", "side": "LONG"},
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-100,
                stress=-100,
                n=5000,
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "scope_selection_policy": "all_matching_anchored",
            "scope_required_anchor_groups": [
                ["symbol", "source_symbol", "symbol_family", "market"],
                ["route_session"],
                ["side"],
            ],
            "scope_prefer_event_specific_fields_enabled": True,
            "scope_prefer_event_specific_fields": ["route_session"],
            "conflict_resolution": "evidence_weighted",
        }
    )

    london = evaluate_vnext_event(
        {"symbol": "USDJPY", "kill_zone": "london", "side": "LONG"},
        cfg,
    )
    tokyo = evaluate_vnext_event(
        {"symbol": "USDJPY", "kill_zone": "tokyo", "side": "LONG"},
        cfg,
    )

    assert london.decision == "FOLLOW"
    assert london.evidence["matched_row_ids"] == ["london-follow"]
    assert london.evidence["decision_counts"] == {"FOLLOW": 1}
    assert london.evidence["route_session_counts"] == {"london": 1}
    assert tokyo.decision == "AVOID"
    assert tokyo.evidence["matched_row_ids"] == ["all-sessions-avoid"]
    assert tokyo.evidence["decision_counts"] == {"AVOID": 1}
    assert tokyo.evidence["route_session_counts"] == {"ALL_SESSIONS": 1}


def test_runtime_resolves_conflict_to_follow_when_r_proxy_stress_pressure_dominates(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    scope = {"symbol": "USDJPY", "route_session": "london", "side": "LONG"}
    _write_jsonl(
        artifact,
        [
            _review_row("follow-row", scope, "DEFAULT_OFF_FOLLOW_SCORER_REVIEW", r=20, stress=8, n=200, proxy=3),
            _review_row("avoid-row", scope, "DEFAULT_OFF_AVOID_FILTER_REVIEW", r=-2, stress=-4, n=20, proxy=-1),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"]["conflict_resolution"] = "evidence_weighted"
    cfg["gtos_vnext_runtime"]["conflict_pressure_dominance_ratio"] = 1.25

    decision = evaluate_vnext_event(
        {"symbol": "USDJPY", "route_session": "london", "side": "LONG"},
        cfg,
    )

    resolution = decision.evidence["decision_resolution"]
    assert decision.decision == "FOLLOW"
    assert resolution["mode"] == "evidence_weighted"
    assert resolution["raw_decision_counts"] == {"FOLLOW": 1, "AVOID": 1}
    assert resolution["selected_decision"] == "FOLLOW"
    assert resolution["follow_pressure"] > resolution["avoid_pressure"] * 1.25
    assert resolution["effective_n_sum"] == 220


def test_runtime_resolves_conflict_to_avoid_when_negative_pressure_dominates(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    scope = {"symbol": "NAS100", "route_session": "london", "side": "SHORT"}
    _write_jsonl(
        artifact,
        [
            _review_row("follow-row", scope, "DEFAULT_OFF_FOLLOW_SCORER_REVIEW", r=2, stress=2, n=20),
            _review_row("avoid-row", scope, "DEFAULT_OFF_AVOID_FILTER_REVIEW", r=-20, stress=-10, n=200, proxy=-3),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"]["conflict_resolution"] = "evidence_weighted"

    decision = evaluate_vnext_event(
        {"symbol": "NAS100", "route_session": "london", "side": "SHORT"},
        cfg,
    )

    resolution = decision.evidence["decision_resolution"]
    assert decision.decision == "AVOID"
    assert resolution["selected_decision"] == "AVOID"
    assert resolution["avoid_pressure"] > resolution["follow_pressure"] * 1.25


def test_runtime_exposes_wave3_numeric_confluence_source_schema(tmp_path):
    artifact = tmp_path / "vnext_numeric_confluence.jsonl"
    scope = {"symbol": "USDJPY", "route_session": "london", "side": "LONG"}
    _write_jsonl(
        artifact,
        [
            _review_row(
                "follow-row",
                scope,
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=20,
                stress=8,
                n=200,
                proxy=3,
                timestamp_utc="2026-06-04T20:00:00+00:00",
                source_component="registry_scorer_module",
            ),
            _review_row(
                "avoid-row",
                scope,
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-2,
                stress=-4,
                n=20,
                proxy=-1,
                timestamp_utc="2026-06-04T19:45:00+00:00",
                source_component="nofill_far_miss_avoid",
                target_stop_order_class="STOP_FIRST_PROXY_DOMINANT",
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "conflict_resolution": "evidence_weighted",
            "conflict_pressure_dominance_ratio": 1.25,
            "numeric_confluence_now_utc": "2026-06-04T20:30:00+00:00",
        }
    )

    decision = evaluate_vnext_event(
        {"symbol": "USDJPY", "route_session": "london", "side": "LONG"},
        cfg,
    )

    confluence = decision.evidence["numeric_confluence"]
    assert decision.decision == "FOLLOW"
    assert confluence["schema_version"] == "wave3_follow_avoid_mixed_numeric_confluence_v4"
    assert confluence["source_count"] == 2
    assert confluence["label_counts"] == {"FOLLOW": 1, "AVOID": 1}
    assert confluence["source_completeness"]["complete_sources"] == 2
    assert confluence["freshness"]["timestamped_sources"] == 2
    assert confluence["follow_is_trade_permission"] is False
    assert confluence["runtime_candidate_use_permitted_by_confluence"] is False

    by_id = {source["source_id"]: source for source in confluence["sources"]}
    assert by_id["follow-row"]["direction"] == "LONG"
    assert by_id["follow-row"]["strength"] > by_id["avoid-row"]["strength"]
    assert by_id["follow-row"]["follow_is_trade_permission"] is False
    assert by_id["avoid-row"]["avoid_invalidation_type"] == "stop_first_or_adverse_path"
    assert confluence["final_mapping"]["selected_label"] == "FOLLOW"
    assert confluence["final_mapping"]["action_type"] == (
        "follow_candidate_for_downstream_probability_scheduler_audit"
    )
    assert confluence["final_mapping"]["candidate_use_allowed_now_by_confluence"] is False


def test_failure_intelligence_source_repair_avoid_cannot_dominate_specific_follow(tmp_path):
    artifact = tmp_path / "vnext_failure_guard.jsonl"
    scope = {
        "symbol": "USDJPY",
        "source_symbol": "USDJPY",
        "route_session": "london",
        "side": "LONG",
        "framework": "ob_retest",
        "source_component": "shadow_source_guard",
    }
    _write_jsonl(
        artifact,
        [
            _review_row(
                "specific-follow",
                scope,
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=5,
                stress=4,
                n=25,
                source_component="shadow_source_guard",
            ),
            _review_row(
                "source-repair-avoid",
                scope,
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-500,
                stress=-500,
                n=10000,
                source_component="shadow_source_guard",
                implementation_action="READY_DEFAULT_OFF_SOURCE_REPAIR",
                evidence_family="numeric_router_source_repair",
                source_name="numeric_router_source_repair_proof",
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "scope_selection_policy": "all_matching_anchored",
            "scope_required_anchor_groups": [
                ["symbol", "source_symbol", "symbol_family", "market"],
                ["route_session"],
                ["side"],
            ],
            "scope_prefer_event_specific_fields_enabled": True,
            "scope_prefer_event_specific_fields": ["framework", "source_component"],
            "conflict_resolution": "evidence_weighted",
        }
    )

    decision = evaluate_vnext_event(
        {
            "symbol": "USDJPY",
            "source_symbol": "USDJPY",
            "kill_zone": "london",
            "side": "LONG",
            "framework": "ob_retest",
            "source_component": "shadow_source_guard",
        },
        cfg,
    )

    assert decision.decision == "FOLLOW"
    assert decision.evidence["matched_row_ids"] == ["specific-follow", "source-repair-avoid"]
    assert decision.evidence["decision_counts"] == {"FOLLOW": 1, "MIXED": 1}
    assert decision.evidence["failure_intelligence_guard"]["non_executable_rows"] == 1
    assert decision.evidence["failure_intelligence_guard"]["runtime_executable_rows"] == 1
    repair_row = next(row for row in decision.evidence["rows"] if row["row_id"] == "source-repair-avoid")
    assert repair_row["decision"] == "MIXED"
    assert repair_row["runtime_evidence_executable"] is False
    assert repair_row["failure_intelligence_guard"]["reason"] == "non_executable_failure_intelligence"
    resolution = decision.evidence["decision_resolution"]
    assert resolution["selected_decision"] == "FOLLOW"
    assert resolution["avoid_pressure"] == 0.0


def test_failure_intelligence_explicit_avoid_filter_remains_executable(tmp_path):
    artifact = tmp_path / "vnext_failure_guard_explicit_avoid.jsonl"
    scope = {
        "symbol": "GBPJPY",
        "source_symbol": "GBPJPY",
        "route_session": "ny",
        "side": "LONG",
        "source_component": "market_gap_code",
    }
    _write_jsonl(
        artifact,
        [
            _review_row(
                "explicit-avoid",
                scope,
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-8,
                stress=-6,
                n=30,
                source_component="market_gap_code",
                action_class="avoid_filter",
                implementation_action="IMPLEMENT_AVOID_INVERSE_OR_FAILURE_FILTER_SCOPE",
                runtime_candidate_use_permitted=True,
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"]["conflict_resolution"] = "evidence_weighted"

    decision = evaluate_vnext_event(
        {
            "symbol": "GBPJPY",
            "source_symbol": "GBPJPY",
            "kill_zone": "ny",
            "side": "LONG",
            "source_component": "market_gap_code",
        },
        cfg,
    )

    assert decision.decision == "AVOID"
    assert decision.evidence["decision_counts"] == {"AVOID": 1}
    assert decision.evidence["failure_intelligence_guard"]["non_executable_rows"] == 0
    assert decision.evidence["failure_intelligence_guard"]["executable_avoid_token_counts"][
        "AVOID_FILTER"
    ] == 1
    row = decision.evidence["rows"][0]
    assert row["decision"] == "AVOID"
    assert row["runtime_evidence_executable"] is True


def test_failure_intelligence_source_incomplete_avoid_filter_is_not_executable(tmp_path):
    artifact = tmp_path / "vnext_failure_guard_incomplete_avoid.jsonl"
    scope = {
        "symbol": "GBPJPY",
        "source_symbol": "GBPJPY",
        "route_session": "ny",
        "side": "LONG",
        "source_component": "market_gap_code",
    }
    _write_jsonl(
        artifact,
        [
            _review_row(
                "incomplete-avoid",
                scope,
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-8,
                stress=-6,
                n=30,
                source_component="market_gap_code",
                action_class="avoid_filter",
                implementation_action="IMPLEMENT_AVOID_INVERSE_OR_FAILURE_FILTER_SCOPE",
                source_complete=False,
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"]["conflict_resolution"] = "evidence_weighted"

    decision = evaluate_vnext_event(
        {
            "symbol": "GBPJPY",
            "source_symbol": "GBPJPY",
            "kill_zone": "ny",
            "side": "LONG",
            "source_component": "market_gap_code",
        },
        cfg,
    )

    assert decision.decision == "MIXED"
    assert decision.evidence["decision_counts"] == {"MIXED": 1}
    assert decision.evidence["failure_intelligence_guard"]["non_executable_rows"] == 1
    assert decision.evidence["failure_intelligence_guard"]["source_incomplete_flag_rows"] == 1
    row = decision.evidence["rows"][0]
    assert row["decision"] == "MIXED"
    assert row["runtime_evidence_executable"] is False
    assert row["failure_intelligence_guard"]["source_complete_flag_false"] is True
    assert decision.evidence["decision_resolution"]["avoid_pressure"] == 0.0


def test_unvalidated_orderflow_proxy_rows_stay_diagnostic_not_follow_or_avoid(tmp_path):
    artifact = tmp_path / "vnext_orderflow_diagnostic.jsonl"
    scope = {
        "symbol_family": "USDJPY_6J_FAMILY",
        "route_session": "london",
        "side": "LONG",
    }
    _write_jsonl(
        artifact,
        [
            _review_row(
                "unvalidated-orderflow-follow",
                scope,
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=20,
                stress=10,
                n=200,
                source_name="databento_6j_depth_orderflow_proxy",
                evidence_family="futures_proxy_transfer_orderflow",
                source_component="orderflow_depth_proxy",
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"]["conflict_resolution"] = "evidence_weighted"

    decision = evaluate_vnext_event(
        {"symbol": "USDJPY", "source_symbol": "USDJPY", "kill_zone": "london", "side": "LONG"},
        cfg,
    )

    assert decision.decision == "MIXED"
    assert decision.evidence["decision_counts"] == {"MIXED": 1}
    assert decision.evidence["orderflow_diagnostic_guard"]["diagnostic_only_rows"] == 1
    assert decision.evidence["orderflow_diagnostic_guard"]["runtime_executable_rows"] == 0
    row = decision.evidence["rows"][0]
    assert row["decision"] == "MIXED"
    assert row["runtime_evidence_executable"] is False
    assert row["orderflow_diagnostic_guard"]["reason"] == (
        "orderflow_diagnostic_only_until_transfer_validated"
    )
    assert decision.evidence["decision_resolution"]["follow_pressure"] == 0.0


def test_validated_orderflow_proxy_rows_remain_executable_follow_evidence(tmp_path):
    artifact = tmp_path / "vnext_orderflow_validated.jsonl"
    scope = {
        "symbol_family": "USDJPY_6J_FAMILY",
        "route_session": "london",
        "side": "LONG",
    }
    _write_jsonl(
        artifact,
        [
            _review_row(
                "validated-orderflow-follow",
                scope,
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=20,
                stress=10,
                n=200,
                source_name="databento_6j_depth_orderflow_proxy",
                evidence_family="futures_proxy_transfer_orderflow",
                source_component="orderflow_depth_proxy",
                proxy_transfer_validated=True,
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"]["conflict_resolution"] = "evidence_weighted"

    decision = evaluate_vnext_event(
        {"symbol": "USDJPY", "source_symbol": "USDJPY", "kill_zone": "london", "side": "LONG"},
        cfg,
    )

    assert decision.decision == "FOLLOW"
    assert decision.evidence["decision_counts"] == {"FOLLOW": 1}
    assert decision.evidence["orderflow_diagnostic_guard"]["diagnostic_only_rows"] == 0
    assert decision.evidence["orderflow_diagnostic_guard"]["runtime_validated_rows"] == 1
    row = decision.evidence["rows"][0]
    assert row["decision"] == "FOLLOW"
    assert row["runtime_evidence_executable"] is True
    assert row["orderflow_diagnostic_guard"]["runtime_validated"] is True


def test_runtime_prefers_most_specific_scope_over_general_scope(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "general-avoid",
                {"symbol": "GBPJPY"},
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-5,
                stress=-9,
                n=20,
            ),
            _review_row(
                "specific-follow",
                {"symbol": "GBPJPY", "route_session": "tokyo", "side": "LONG"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=12,
                stress=11,
                n=80,
            ),
        ],
    )

    decision = evaluate_vnext_event(
        {"symbol": "GBPJPY", "kill_zone": "tokyo", "direction": "LONG"},
        _config(artifact),
    )

    assert decision.decision == "FOLLOW"
    assert decision.evidence["matched_row_ids"] == ["specific-follow"]


def test_runtime_match_is_framework_aware_when_artifact_carries_framework(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    base_scope = {"symbol": "XAUUSD", "route_session": "london", "side": "LONG"}
    _write_jsonl(
        artifact,
        [
            _review_row(
                "ob-follow",
                {**base_scope, "framework": "ob_retest"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=5,
                stress=4,
                n=25,
            ),
            _review_row(
                "fvg-avoid",
                {**base_scope, "framework": "fvg_fill"},
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-5,
                stress=-8,
                n=25,
            ),
        ],
    )

    ob = evaluate_vnext_event(
        {"symbol": "XAUUSD", "kill_zone": "london", "side": "LONG", "framework": "ob_retest"},
        _config(artifact),
    )
    fvg = evaluate_vnext_event(
        {"symbol": "XAUUSD", "kill_zone": "london", "side": "LONG", "framework": "fvg_fill"},
        _config(artifact),
    )

    assert ob.decision == "FOLLOW"
    assert ob.evidence["matched_row_ids"] == ["ob-follow"]
    assert fvg.decision == "AVOID"
    assert fvg.evidence["matched_row_ids"] == ["fvg-avoid"]


def test_runtime_match_consumes_source_name_and_evidence_family_when_present(tmp_path):
    artifact = tmp_path / "vnext_source_dimension.jsonl"
    base_scope = {"symbol": "USDJPY", "route_session": "london", "side": "LONG"}
    _write_jsonl(
        artifact,
        [
            _review_row(
                "moonshot-follow",
                base_scope,
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=5,
                stress=4,
                n=25,
                source_name="moonshot_reduced_surface_candidates",
                evidence_family="expanded_market_reduced_surface",
                source_role="branch_local_default_off_candidate",
            ),
            _review_row(
                "cp281-avoid",
                base_scope,
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-5,
                stress=-8,
                n=25,
                source_name="cp281_rule_replay_result_table",
                evidence_family="cp281_native_rule_replay",
                source_role="historical_replay_result_table",
            ),
        ],
    )

    moonshot = evaluate_vnext_event(
        {
            "symbol": "USDJPY",
            "kill_zone": "london",
            "side": "LONG",
            "source_name": "moonshot_reduced_surface_candidates",
        },
        _config(artifact),
    )
    cp281 = evaluate_vnext_event(
        {
            "symbol": "USDJPY",
            "kill_zone": "london",
            "side": "LONG",
            "evidence_family": "cp281_native_rule_replay",
        },
        _config(artifact),
    )

    assert moonshot.decision == "FOLLOW"
    assert moonshot.evidence["matched_row_ids"] == ["moonshot-follow"]
    assert moonshot.evidence["source_name_decision_counts"] == {
        "moonshot_reduced_surface_candidates": {"FOLLOW": 1}
    }
    assert cp281.decision == "AVOID"
    assert cp281.evidence["matched_row_ids"] == ["cp281-avoid"]
    assert cp281.evidence["evidence_family_decision_counts"] == {
        "cp281_native_rule_replay": {"AVOID": 1}
    }
    assert cp281.evidence["source_role_decision_counts"] == {
        "historical_replay_result_table": {"AVOID": 1}
    }


def test_runtime_match_is_route_family_market_and_timeframe_aware(tmp_path):
    artifact = tmp_path / "vnext_route_family.jsonl"
    base_scope = {
        "symbol": "XAUUSD",
        "market": "XAUUSD",
        "timeframe": "M5",
        "route_session": "london",
        "side": "LONG",
        "framework": "ob_retest",
    }
    _write_jsonl(
        artifact,
        [
            _review_row(
                "moonshot-follow",
                {**base_scope, "route_family": "moonshot_mechanical"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=7,
                stress=5,
                n=44,
            ),
            _review_row(
                "legacy-avoid",
                {**base_scope, "route_family": "legacy_mechanical"},
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-6,
                stress=-9,
                n=44,
            ),
        ],
    )

    decision = evaluate_vnext_event(
        {
            "symbol": "XAUUSD",
            "market": "XAUUSD",
            "timeframe": "M5",
            "kill_zone": "london",
            "side": "LONG",
            "framework": "ob_retest",
            "route_family": "moonshot_mechanical",
        },
        _config(artifact),
    )

    assert decision.decision == "FOLLOW"
    assert decision.evidence["matched_row_ids"] == ["moonshot-follow"]
    assert decision.evidence["market_counts"] == {"XAUUSD": 1}
    assert decision.evidence["timeframe_counts"] == {"M5": 1}
    assert decision.evidence["route_family_counts"] == {"moonshot_mechanical": 1}
    assert decision.evidence["rows"][0]["route_family"] == "moonshot_mechanical"


def test_runtime_infers_route_family_from_full_evidence_tokens(tmp_path):
    artifact = tmp_path / "vnext_inferred_route_family.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "vnext_matrix_row_id": "moonshot-row",
                "row_type": "gtos_vnext_evidence_to_system_matrix_row",
                "source_name": "moonshot_reduced_surface_candidates",
                "evidence_family": "expanded_market_reduced_surface",
                "source_component": "shadow_source_guard",
                "symbol": "XAUUSD",
                "side": "LONG",
                "implementation_action": (
                    "REGISTER_DEFAULT_OFF_BRANCH_LOCAL_LEAKAGE_REDUCED_SURFACE_CANDIDATE"
                ),
                "cost_adjusted_simulated_r": {"sum": 4.0, "count": 4},
                "effective_n": {"sum": 4.0, "count": 4},
            }
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "post_l2_route_families": ["moonshot_mechanical"],
            "post_l2_route_source_components": ["shadow_source_guard"],
            "post_l2_route_timeframes": ["M15"],
            "post_l2_route_horizons": [""],
        }
    )

    generic_ob = evaluate_vnext_event(
        {
            "symbol": "XAUUSD",
            "side": "LONG",
            "framework": "ob_retest",
            "source_component": "shadow_source_guard",
        },
        cfg,
    )
    routed = evaluate_vnext_route_event(
        {
            "symbol": "XAUUSD",
            "side": "LONG",
            "framework": "ob_retest",
            "source_component": "shadow_source_guard",
        },
        cfg,
    )

    assert generic_ob.decision == "LEGACY"
    assert routed.decision == "FOLLOW"
    assert routed.evidence["route_family_counts"] == {"moonshot_mechanical": 1}
    assert routed.evidence["route_family_inferred_from_counts"] == {"evidence_token": 1}
    assert routed.evidence["rows"][0]["route_family"] == "moonshot_mechanical"
    assert routed.evidence["rows"][0]["route_family_inferred_from"] == "evidence_token"


def test_route_family_avoid_veto_zeroes_follow_risk(tmp_path):
    artifact = tmp_path / "vnext_route_family_veto.jsonl"
    scope = {
        "symbol": "XAUUSD",
        "side": "LONG",
        "source_component": "shadow_source_guard",
    }
    _write_jsonl(
        artifact,
        [
            {
                "vnext_matrix_row_id": "moonshot-follow",
                "row_type": "gtos_vnext_evidence_to_system_matrix_row",
                "source_name": "moonshot_reduced_surface_candidates",
                "evidence_family": "expanded_market_reduced_surface",
                "implementation_action": (
                    "REGISTER_DEFAULT_OFF_BRANCH_LOCAL_LEAKAGE_REDUCED_SURFACE_CANDIDATE"
                ),
                "r_metrics": {
                    "cost_adjusted_simulated_r": _metric(12.0),
                    "stress_simulated_r": _metric(0.0),
                    "effective_n": _metric(30.0),
                    "proxy_score": _metric(0.0),
                },
                **scope,
            },
            {
                "vnext_matrix_row_id": "numeric-avoid",
                "row_type": "gtos_vnext_evidence_to_system_matrix_row",
                "source_name": "numeric_router_avoid_score",
                "evidence_family": "numeric_router_system_recommendations",
                "implementation_action": "IMPLEMENT_AVOID_INVERSE_OR_FAILURE_FILTER_SCOPE",
                **scope,
            },
        ],
    )
    cfg = _config(artifact, apply=True)
    cfg["gtos_vnext_runtime"].update(
        {
            "post_l2_route_families": ["moonshot_mechanical", "numeric_router"],
            "post_l2_route_source_components": ["shadow_source_guard"],
            "post_l2_route_timeframes": ["M15"],
            "post_l2_route_horizons": [""],
            "conflict_resolution": "evidence_weighted",
            "route_family_avoid_veto_enabled": True,
            "route_family_avoid_veto_families": ["numeric_router"],
            "route_family_avoid_veto_min_rows": 1,
            "risk_adjustment_enabled": True,
        }
    )

    decision = evaluate_vnext_route_event(
        {
            "symbol": "XAUUSD",
            "side": "LONG",
            "source_component": "shadow_source_guard",
            "framework": "ob_retest",
        },
        cfg,
    )
    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config=cfg,
    )

    assert decision.decision == "FOLLOW"
    assert decision.evidence["route_family_decision_counts"] == {
        "moonshot_mechanical": {"FOLLOW": 1},
        "numeric_router": {"AVOID": 1},
    }
    assert adjustment.applied is True
    assert adjustment.after_risk_pct == 0.0
    assert adjustment.reason == "vnext_risk_route_family_avoid_veto"
    assert adjustment.evidence_summary["route_family_avoid_veto_family"] == "numeric_router"
    cfg["gtos_vnext_runtime"]["block_min_effective_n"] = 999
    assert vnext_execution_block_reason(decision, cfg) == "vnext_risk_route_family_avoid_veto"


def test_source_component_avoid_veto_zeroes_follow_risk_before_effective_n_floor():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 3,
            "source_component_decision_counts": {
                "market_gap_code": {"FOLLOW": 1, "AVOID": 2},
            },
        },
    )
    cfg = {
        "gtos_vnext_runtime": {
            "risk_adjustment_enabled": True,
            "risk_zero_blocks_execution": True,
            "execution_block_min_risk_multiplier": 0.000001,
            "block_min_effective_n": 999,
            "source_component_avoid_veto_enabled": True,
            "source_component_avoid_veto_components": ["market_gap_code"],
            "source_component_avoid_veto_min_rows": 1,
            "source_component_avoid_veto_dominance_ratio": 1.0,
            "source_component_avoid_veto_risk_multiplier": 0.0,
        }
    }

    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config=cfg,
    )

    assert adjustment.applied is True
    assert adjustment.after_risk_pct == 0.0
    assert adjustment.reason == "vnext_risk_source_component_avoid_veto"
    assert adjustment.evidence_summary["source_component_avoid_veto_component"] == "market_gap_code"
    assert adjustment.evidence_summary["source_component_avoid_veto_avoid_rows"] == 2
    assert vnext_execution_block_reason(decision, cfg) == "vnext_risk_source_component_avoid_veto"


def test_action_class_avoid_veto_zeroes_follow_risk_before_effective_n_floor():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 3,
            "action_class_decision_counts": {
                "avoid_filter": {"FOLLOW": 1, "AVOID": 2},
            },
        },
    )
    cfg = {
        "gtos_vnext_runtime": {
            "risk_adjustment_enabled": True,
            "risk_zero_blocks_execution": True,
            "execution_block_min_risk_multiplier": 0.000001,
            "block_min_effective_n": 999,
            "action_class_avoid_veto_enabled": True,
            "action_class_avoid_veto_classes": ["avoid_filter"],
            "action_class_avoid_veto_min_rows": 1,
            "action_class_avoid_veto_dominance_ratio": 1.0,
            "action_class_avoid_veto_risk_multiplier": 0.0,
        }
    }

    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config=cfg,
    )

    assert adjustment.applied is True
    assert adjustment.after_risk_pct == 0.0
    assert adjustment.reason == "vnext_risk_action_class_avoid_veto"
    assert adjustment.evidence_summary["action_class_avoid_veto_class"] == "avoid_filter"
    assert adjustment.evidence_summary["action_class_avoid_veto_avoid_rows"] == 2
    assert vnext_execution_block_reason(decision, cfg) == "vnext_risk_action_class_avoid_veto"


def test_evidence_family_avoid_veto_zeroes_follow_risk_before_effective_n_floor():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 3,
            "evidence_family_decision_counts": {
                "numeric_router_system_recommendations": {"FOLLOW": 1, "AVOID": 2},
            },
        },
    )
    cfg = {
        "gtos_vnext_runtime": {
            "risk_adjustment_enabled": True,
            "risk_zero_blocks_execution": True,
            "execution_block_min_risk_multiplier": 0.000001,
            "block_min_effective_n": 999,
            "evidence_family_avoid_veto_enabled": True,
            "evidence_family_avoid_veto_families": ["numeric_router_system_recommendations"],
            "evidence_family_avoid_veto_min_rows": 1,
            "evidence_family_avoid_veto_dominance_ratio": 1.0,
            "evidence_family_avoid_veto_risk_multiplier": 0.0,
        }
    }

    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config=cfg,
    )

    assert adjustment.applied is True
    assert adjustment.after_risk_pct == 0.0
    assert adjustment.reason == "vnext_risk_evidence_family_avoid_veto"
    assert adjustment.evidence_summary["evidence_family_avoid_veto_family"] == (
        "numeric_router_system_recommendations"
    )
    assert adjustment.evidence_summary["evidence_family_avoid_veto_avoid_rows"] == 2
    assert vnext_execution_block_reason(decision, cfg) == "vnext_risk_evidence_family_avoid_veto"


def test_source_name_avoid_veto_zeroes_follow_risk_before_effective_n_floor():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 3,
            "source_name_decision_counts": {
                "cp281_rule_replay_result_table": {"FOLLOW": 1, "AVOID": 2},
            },
        },
    )
    cfg = {
        "gtos_vnext_runtime": {
            "risk_adjustment_enabled": True,
            "risk_zero_blocks_execution": True,
            "execution_block_min_risk_multiplier": 0.000001,
            "block_min_effective_n": 999,
            "source_name_avoid_veto_enabled": True,
            "source_name_avoid_veto_names": ["cp281_rule_replay_result_table"],
            "source_name_avoid_veto_min_rows": 1,
            "source_name_avoid_veto_dominance_ratio": 1.0,
            "source_name_avoid_veto_risk_multiplier": 0.0,
        }
    }

    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config=cfg,
    )

    assert adjustment.applied is True
    assert adjustment.after_risk_pct == 0.0
    assert adjustment.reason == "vnext_risk_source_name_avoid_veto"
    assert adjustment.evidence_summary["source_name_avoid_veto_name"] == (
        "cp281_rule_replay_result_table"
    )
    assert adjustment.evidence_summary["source_name_avoid_veto_avoid_rows"] == 2
    assert vnext_execution_block_reason(decision, cfg) == "vnext_risk_source_name_avoid_veto"


def test_source_role_avoid_veto_zeroes_follow_risk_before_effective_n_floor():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "USDJPY"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 3,
            "source_role_decision_counts": {
                "default_off_branch_decision": {"FOLLOW": 1, "AVOID": 2},
            },
        },
    )
    cfg = {
        "gtos_vnext_runtime": {
            "risk_adjustment_enabled": True,
            "risk_zero_blocks_execution": True,
            "execution_block_min_risk_multiplier": 0.000001,
            "block_min_effective_n": 999,
            "source_role_avoid_veto_enabled": True,
            "source_role_avoid_veto_roles": ["default_off_branch_decision"],
            "source_role_avoid_veto_min_rows": 1,
            "source_role_avoid_veto_dominance_ratio": 1.0,
            "source_role_avoid_veto_risk_multiplier": 0.0,
        }
    }

    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config=cfg,
    )

    assert adjustment.applied is True
    assert adjustment.after_risk_pct == 0.0
    assert adjustment.reason == "vnext_risk_source_role_avoid_veto"
    assert adjustment.evidence_summary["source_role_avoid_veto_role"] == (
        "default_off_branch_decision"
    )
    assert adjustment.evidence_summary["source_role_avoid_veto_avoid_rows"] == 2
    assert vnext_execution_block_reason(decision, cfg) == "vnext_risk_source_role_avoid_veto"


def test_pre_ai_router_vetoes_follow_side_on_route_family_avoid(tmp_path):
    artifact = tmp_path / "vnext_pre_ai_route_family_veto.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "vnext_matrix_row_id": "moonshot-follow",
                "row_type": "gtos_vnext_evidence_to_system_matrix_row",
                "source_name": "moonshot_reduced_surface_candidates",
                "evidence_family": "expanded_market_reduced_surface",
                "implementation_action": (
                    "REGISTER_DEFAULT_OFF_BRANCH_LOCAL_LEAKAGE_REDUCED_SURFACE_CANDIDATE"
                ),
                "symbol": "GBPJPY",
                "source_symbol": "GBPJPY",
                "route_session": "ny_core",
                "side": "LONG",
                "source_component": "shadow_source_guard",
                "r_metrics": {
                    "cost_adjusted_simulated_r": _metric(12.0),
                    "stress_simulated_r": _metric(0.0),
                    "effective_n": _metric(30.0),
                    "proxy_score": _metric(0.0),
                },
            },
            {
                "vnext_matrix_row_id": "numeric-avoid",
                "row_type": "gtos_vnext_evidence_to_system_matrix_row",
                "source_name": "numeric_router_avoid_score",
                "evidence_family": "numeric_router_system_recommendations",
                "implementation_action": "IMPLEMENT_AVOID_INVERSE_OR_FAILURE_FILTER_SCOPE",
                "symbol": "GBPJPY",
                "source_symbol": "GBPJPY",
                "route_session": "ny_core",
                "side": "LONG",
                "source_component": "shadow_source_guard",
            },
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": False,
            "pre_ai_route_families": ["moonshot_mechanical", "numeric_router"],
            "pre_ai_route_source_components": ["shadow_source_guard"],
            "pre_ai_route_timeframes": ["M15"],
            "pre_ai_route_horizons": [""],
            "conflict_resolution": "evidence_weighted",
            "route_family_avoid_veto_enabled": True,
            "route_family_avoid_veto_families": ["numeric_router"],
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="GBPJPY",
        source_symbol="GBPJPY",
        kill_zone="ny",
        config=cfg,
        bias="bullish",
    )

    assert decision.action == "SKIP_AI_AVOID_ONLY"
    assert decision.risk_vetoed_sides == ("LONG",)
    assert decision.side_risk_reasons["LONG"] == "vnext_risk_route_family_avoid_veto"


def test_pre_ai_router_keeps_strong_positive_side_and_blocks_only_bad_route_family(tmp_path):
    artifact = tmp_path / "vnext_pre_ai_positive_pressure_route.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "vnext_matrix_row_id": "moonshot-follow-source-bound",
                "row_type": "gtos_vnext_evidence_to_system_matrix_row",
                "source_name": "moonshot_reduced_surface_candidates",
                "evidence_family": "expanded_market_reduced_surface",
                "implementation_action": (
                    "REGISTER_DEFAULT_OFF_BRANCH_LOCAL_LEAKAGE_REDUCED_SURFACE_CANDIDATE"
                ),
                "symbol": "GBPJPY",
                "source_symbol": "GBPJPY",
                "route_session": "ny_core",
                "side": "LONG",
                "source_component": "shadow_source_guard",
                "r_metrics": {
                    "cost_adjusted_simulated_r": _metric(180.0, count=180),
                    "stress_simulated_r": _metric(40.0, count=180),
                    "effective_n": _metric(180.0, count=180),
                },
            },
            {
                "vnext_matrix_row_id": "numeric-proxy-avoid",
                "row_type": "gtos_vnext_evidence_to_system_matrix_row",
                "source_name": "numeric_router_avoid_score",
                "evidence_family": "numeric_router_system_recommendations",
                "implementation_action": "REGISTER_NEGATIVE_PROXY_FAILURE_FEATURE",
                "symbol": "GBPJPY",
                "source_symbol": "GBPJPY",
                "route_session": "ny_core",
                "side": "LONG",
                "source_component": "shadow_source_guard",
                "proxy_r_class": "STRONG_NEGATIVE_PROXY_R",
                "target_stop_order_class": "TARGET_STOP_ORDER_NOT_SOURCE_BOUND",
            },
            {
                "vnext_matrix_row_id": "numeric-weak-follow",
                "row_type": "gtos_vnext_evidence_to_system_matrix_row",
                "source_name": "numeric_router_scorer_surface",
                "evidence_family": "numeric_router_system_recommendations",
                "implementation_action": "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS",
                "symbol": "GBPJPY",
                "source_symbol": "GBPJPY",
                "route_session": "ny_core",
                "side": "LONG",
                "source_component": "shadow_source_guard",
            },
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": False,
            "pre_ai_route_families": ["moonshot_mechanical", "numeric_router"],
            "pre_ai_route_source_components": ["shadow_source_guard"],
            "pre_ai_route_timeframes": ["M15"],
            "pre_ai_route_horizons": [""],
            "conflict_resolution": "evidence_weighted",
            "risk_adjustment_enabled": True,
            "strong_negative_proxy_risk_min_rows": 1,
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="GBPJPY",
        source_symbol="GBPJPY",
        kill_zone="ny",
        config=cfg,
        bias="bullish",
    )

    assert decision.action == "NARROW_AI_TO_ROUTE"
    assert decision.recommended_side == "LONG"
    assert decision.recommended_route_families == ("moonshot_mechanical",)
    assert decision.blocked_route_families == ("numeric_router",)
    assert decision.risk_vetoed_sides == ()
    assert decision.side_risk_reasons["LONG"] == "vnext_risk_strong_follow"

    side_decision = decision.side_decisions[0]
    assert side_decision.decision == "FOLLOW"
    assert side_decision.evidence["decision_resolution"]["selected_decision"] == "FOLLOW"


def test_pre_ai_router_vetoes_follow_side_on_source_component_avoid(tmp_path):
    artifact = tmp_path / "vnext_pre_ai_component_veto.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "component-follow",
                {
                    "symbol": "GBPJPY",
                    "source_symbol": "GBPJPY",
                    "route_session": "ny_core",
                    "side": "LONG",
                    "source_component": "market_gap_code",
                },
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=10.0,
                stress=0.0,
                n=10,
                proxy=0.0,
                source_component="market_gap_code",
            ),
            _review_row(
                "component-avoid",
                {
                    "symbol": "GBPJPY",
                    "source_symbol": "GBPJPY",
                    "route_session": "ny_core",
                    "side": "LONG",
                    "source_component": "market_gap_code",
                },
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=0.0,
                stress=0.0,
                n=10,
                proxy=0.0,
                source_component="market_gap_code",
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": False,
            "pre_ai_route_timeframes": ["M15"],
            "pre_ai_route_horizons": [""],
            "pre_ai_route_source_components": ["market_gap_code"],
            "conflict_resolution": "evidence_weighted",
            "risk_adjustment_enabled": True,
            "source_component_avoid_veto_enabled": True,
            "source_component_avoid_veto_components": ["market_gap_code"],
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="GBPJPY",
        source_symbol="GBPJPY",
        kill_zone="ny",
        config=cfg,
        bias="bullish",
    )

    assert decision.action == "SKIP_AI_AVOID_ONLY"
    assert decision.risk_vetoed_sides == ("LONG",)
    assert decision.side_risk_reasons["LONG"] == "vnext_risk_source_component_avoid_veto"


def test_pre_ai_router_vetoes_follow_side_on_action_class_avoid(tmp_path):
    artifact = tmp_path / "vnext_pre_ai_action_class_veto.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "action-follow",
                {
                    "symbol": "GBPJPY",
                    "source_symbol": "GBPJPY",
                    "route_session": "ny_core",
                    "side": "LONG",
                    "action_class": "follow_rule",
                },
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=10.0,
                stress=0.0,
                n=10,
                proxy=0.0,
                action_class="follow_rule",
            ),
            _review_row(
                "action-avoid",
                {
                    "symbol": "GBPJPY",
                    "source_symbol": "GBPJPY",
                    "route_session": "ny_core",
                    "side": "LONG",
                    "action_class": "avoid_filter",
                },
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=0.0,
                stress=0.0,
                n=10,
                proxy=0.0,
                action_class="avoid_filter",
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": False,
            "pre_ai_route_timeframes": ["M15"],
            "pre_ai_route_horizons": [""],
            "conflict_resolution": "evidence_weighted",
            "risk_adjustment_enabled": True,
            "action_class_avoid_veto_enabled": True,
            "action_class_avoid_veto_classes": ["avoid_filter"],
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="GBPJPY",
        source_symbol="GBPJPY",
        kill_zone="ny",
        config=cfg,
        bias="bullish",
    )

    assert decision.action == "SKIP_AI_AVOID_ONLY"
    assert decision.risk_vetoed_sides == ("LONG",)
    assert decision.side_risk_reasons["LONG"] == "vnext_risk_action_class_avoid_veto"


def test_pre_ai_router_vetoes_follow_side_on_evidence_family_avoid(tmp_path):
    artifact = tmp_path / "vnext_pre_ai_evidence_family_veto.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "follow-family",
                {
                    "symbol": "USDJPY",
                    "source_symbol": "USDJPY",
                    "route_session": "london_core",
                    "side": "LONG",
                },
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=12.0,
                stress=0.0,
                n=10,
                proxy=0.0,
                source_name="moonshot_reduced_surface_candidates",
                evidence_family="expanded_market_reduced_surface",
            ),
            _review_row(
                "avoid-family",
                {
                    "symbol": "USDJPY",
                    "source_symbol": "USDJPY",
                    "route_session": "london_core",
                    "side": "LONG",
                },
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=0.0,
                stress=0.0,
                n=10,
                proxy=0.0,
                source_name="numeric_router_system_recommendations",
                evidence_family="numeric_router_system_recommendations",
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": False,
            "pre_ai_route_timeframes": ["M15"],
            "pre_ai_route_horizons": [""],
            "conflict_resolution": "evidence_weighted",
            "risk_adjustment_enabled": True,
            "evidence_family_avoid_veto_enabled": True,
            "evidence_family_avoid_veto_families": ["numeric_router_system_recommendations"],
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="USDJPY",
        source_symbol="USDJPY",
        kill_zone="london",
        config=cfg,
        bias="bullish",
    )

    assert decision.action == "SKIP_AI_AVOID_ONLY"
    assert decision.risk_vetoed_sides == ("LONG",)
    assert decision.side_risk_reasons["LONG"] == "vnext_risk_evidence_family_avoid_veto"
    long_side = decision.side_decisions[0]
    assert long_side.decision == "FOLLOW"
    assert long_side.evidence["evidence_family_decision_counts"][
        "numeric_router_system_recommendations"
    ] == {"AVOID": 1}


def test_pre_ai_router_vetoes_follow_side_on_source_name_avoid(tmp_path):
    artifact = tmp_path / "vnext_pre_ai_source_name_veto.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "follow-source-name",
                {
                    "symbol": "USDJPY",
                    "source_symbol": "USDJPY",
                    "route_session": "london_core",
                    "side": "LONG",
                },
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=12.0,
                stress=0.0,
                n=10,
                proxy=0.0,
                source_name="moonshot_reduced_surface_candidates",
                evidence_family="expanded_market_reduced_surface",
            ),
            _review_row(
                "avoid-source-name",
                {
                    "symbol": "USDJPY",
                    "source_symbol": "USDJPY",
                    "route_session": "london_core",
                    "side": "LONG",
                },
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=0.0,
                stress=0.0,
                n=10,
                proxy=0.0,
                source_name="cp281_rule_replay_result_table",
                evidence_family="cp281_native_rule_replay",
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": False,
            "pre_ai_route_timeframes": ["M15"],
            "pre_ai_route_horizons": [""],
            "conflict_resolution": "evidence_weighted",
            "risk_adjustment_enabled": True,
            "evidence_family_avoid_veto_enabled": False,
            "source_name_avoid_veto_enabled": True,
            "source_name_avoid_veto_names": ["cp281_rule_replay_result_table"],
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="USDJPY",
        source_symbol="USDJPY",
        kill_zone="london",
        config=cfg,
        bias="bullish",
    )

    assert decision.action == "SKIP_AI_AVOID_ONLY"
    assert decision.risk_vetoed_sides == ("LONG",)
    assert decision.side_risk_reasons["LONG"] == "vnext_risk_source_name_avoid_veto"
    long_side = decision.side_decisions[0]
    assert long_side.decision == "FOLLOW"
    assert long_side.evidence["source_name_decision_counts"][
        "cp281_rule_replay_result_table"
    ] == {"AVOID": 1}


def test_pre_ai_router_vetoes_follow_side_on_source_role_avoid(tmp_path):
    artifact = tmp_path / "vnext_pre_ai_source_role_veto.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "follow-source-role",
                {
                    "symbol": "USDJPY",
                    "source_symbol": "USDJPY",
                    "route_session": "london_core",
                    "side": "LONG",
                },
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=12.0,
                stress=0.0,
                n=10,
                proxy=0.0,
                source_role="scorer_registry_surface",
            ),
            _review_row(
                "avoid-source-role",
                {
                    "symbol": "USDJPY",
                    "source_symbol": "USDJPY",
                    "route_session": "london_core",
                    "side": "LONG",
                },
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=0.0,
                stress=0.0,
                n=10,
                proxy=0.0,
                source_role="default_off_branch_decision",
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": False,
            "pre_ai_route_timeframes": ["M15"],
            "pre_ai_route_horizons": [""],
            "conflict_resolution": "evidence_weighted",
            "risk_adjustment_enabled": True,
            "source_name_avoid_veto_enabled": False,
            "source_role_avoid_veto_enabled": True,
            "source_role_avoid_veto_roles": ["default_off_branch_decision"],
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="USDJPY",
        source_symbol="USDJPY",
        kill_zone="london",
        config=cfg,
        bias="bullish",
    )

    assert decision.action == "SKIP_AI_AVOID_ONLY"
    assert decision.risk_vetoed_sides == ("LONG",)
    assert decision.side_risk_reasons["LONG"] == "vnext_risk_source_role_avoid_veto"
    long_side = decision.side_decisions[0]
    assert long_side.decision == "FOLLOW"
    assert long_side.evidence["source_role_decision_counts"][
        "default_off_branch_decision"
    ] == {"AVOID": 1}


def test_pre_ai_router_can_skip_ai_from_nofill_avoid_source_component(tmp_path):
    artifact = tmp_path / "vnext_pre_ai_nofill_avoid.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                f"{side.lower()}-nofill-avoid",
                {
                    "symbol": "GBPJPY",
                    "source_symbol": "GBPJPY",
                    "route_session": "tokyo",
                    "side": side,
                    "source_component": "nofill_far_miss_avoid",
                    "route_family": "nofill_mechanical",
                    "market_timeframe": "M15",
                },
                "",
                r=0,
                stress=0,
                n=0,
                proxy=-5.0,
                implementation_action="REGISTER_NEGATIVE_PROXY_FAILURE_FEATURE",
                source_component="nofill_far_miss_avoid",
                proxy_r_class="STRONG_NEGATIVE_PROXY_R",
                target_stop_order_class="TARGET_FIRST_PROXY_DOMINANT",
                source_name="numeric_router_avoid_score",
                evidence_family="numeric_router_system_recommendations",
            )
            for side in ("LONG", "SHORT")
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": True,
            "pre_ai_evaluate_route_variants": True,
            "pre_ai_route_timeframes": ["M15"],
            "pre_ai_route_horizons": [""],
            "pre_ai_route_frameworks": [""],
            "pre_ai_route_families": ["nofill_mechanical"],
            "pre_ai_route_source_components": ["nofill_far_miss_avoid"],
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="GBPJPY",
        source_symbol="GBPJPY",
        kill_zone="tokyo",
        config=cfg,
        bias=None,
    )

    assert decision.action == "SKIP_AI_AVOID_ONLY"
    assert decision.reason == "pre_ai_vnext_avoid_only"
    assert decision.blocked_sides == ("LONG", "SHORT")
    assert decision.blocked_route_families == ("nofill_mechanical",)
    assert {side.decision for side in decision.side_decisions} == {"AVOID"}
    assert decision.side_decisions[0].evidence["source_component_counts"] == {
        "nofill_far_miss_avoid": 1
    }


def test_pre_ai_router_uses_source_guarded_positive_proxy_without_effective_n(tmp_path):
    artifact = tmp_path / "vnext_pre_ai_source_guarded_proxy.jsonl"
    scope = {
        "symbol": "USDJPY",
        "source_symbol": "USDJPY",
        "route_session": "london",
        "side": "LONG",
        "framework": "fvg_fill",
        "source_component": "shadow_source_guard",
        "market_timeframe": "M15",
    }
    _write_jsonl(
        artifact,
        [
            _review_row(
                f"long-positive-proxy-{idx}",
                scope,
                "",
                r=0,
                stress=0,
                n=0,
                proxy=1.0,
                implementation_action="DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS",
                source_name="numeric_router_scorer_surface",
                source_role="scorer_registry_surface",
                source_group="scorer_registry_surface",
                system_surface="default_off_research_scorer_registry_catalog",
                source_component="shadow_source_guard",
                proxy_r_class="STRONG_POSITIVE_PROXY_R",
                target_stop_order_class="TARGET_STOP_ORDER_NOT_SOURCE_BOUND",
            )
            for idx in range(20)
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": True,
            "pre_ai_evaluate_route_variants": True,
            "pre_ai_route_timeframes": ["M15"],
            "pre_ai_route_horizons": [""],
            "pre_ai_route_frameworks": ["fvg_fill"],
            "pre_ai_route_families": ["fvg_fill"],
            "pre_ai_route_source_components": ["shadow_source_guard"],
            "risk_adjustment_enabled": True,
            "source_guarded_positive_proxy_enabled": True,
            "source_guarded_positive_proxy_min_rows": 20,
            "strong_positive_proxy_risk_min_rows": 20,
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="USDJPY",
        source_symbol="USDJPY",
        kill_zone="london",
        config=cfg,
        bias=None,
    )

    assert decision.action == "NARROW_AI_TO_ROUTE"
    assert decision.recommended_side == "LONG"
    assert decision.recommended_frameworks == ("fvg_fill",)
    assert decision.risk_vetoed_sides == ()
    assert decision.side_risk_reasons["LONG"] == "vnext_risk_strong_positive_proxy_class"
    long_decision = next(side for side in decision.side_decisions if side.event.get("side") == "LONG")
    assert long_decision.evidence["proxy_r_class_counts"] == {"STRONG_POSITIVE_PROXY_R": 20}
    assert long_decision.evidence["target_stop_order_class_counts"] == {
        "TARGET_STOP_ORDER_NOT_SOURCE_BOUND": 20
    }


def test_runtime_session_aliases_and_symbol_family_match_full_style_rows(tmp_path):
    artifact = tmp_path / "vnext_impl.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "vnext_matrix_row_id": "family-row",
                "row_type": "gtos_vnext_evidence_system_row",
                "symbol_family": "USDJPY_6J_FAMILY",
                "route_session": "ALL_SESSIONS",
                "market_timeframe": "M15",
                "side": "LONG",
                "action_class": "follow_rule",
                "source_name": "cp281_branch_decisions",
                "evidence_family": "cp281_ready_runtime_mapping",
                "source_artifact": "research/source.jsonl",
                "source_line_no": 7,
                "source_row_id": "source-7",
                "r_metrics": {
                    "cost_adjusted_simulated_r": _metric(0.26, 4),
                    "stress_simulated_r": _metric(0.22, 4),
                    "effective_n": _metric(118186, 4),
                    "proxy_score": _metric(0, 0),
                },
            }
        ],
    )

    decision = evaluate_vnext_event(
        {"symbol": "USDJPY", "source_symbol": "USDJPY", "kill_zone": "london", "side": "LONG", "timeframe": "M15"},
        _config(artifact),
    )

    assert decision.decision == "FOLLOW"
    assert decision.evidence["rows"][0]["source_name"] == "cp281_branch_decisions"
    assert decision.evidence["rows"][0]["source_line_no"] == 7
    assert decision.evidence["rows"][0]["source_row_id"] == "source-7"


def test_runtime_symbol_family_aliases_normalize_broker_and_proxy_symbols():
    assert normalize_vnext_symbol_key("US30.cash") == "US30_CASH"
    assert normalize_vnext_symbol_key("US30_cash") == "US30_CASH"
    for symbol in ("US30.cash", "US30_cash", "US30", "YM"):
        assert resolve_vnext_symbol_family(symbol) == "US30_YM_FAMILY"
    for symbol in ("XAGUSD", "XAGUSD_SI", "SI"):
        assert resolve_vnext_symbol_family(symbol) == "XAGUSD_SILVER_FAMILY"
    assert resolve_vnext_symbol_family("NAS100.cash") == "NAS100_NQ_FAMILY"
    assert resolve_vnext_symbol_family("US500.cash") == "SPX500_ES_FAMILY"
    assert resolve_vnext_symbol_family("6J") == "USDJPY_6J_FAMILY"
    assert symbol_family_candidates_for_vnext("US30.cash", "US30_cash", "YM") == ("US30_YM_FAMILY",)


def test_runtime_futures_contract_aliases_resolve_to_current_artifact_families():
    assert resolve_vnext_symbol_family("ESM26-CME") == "SPX500_ES_FAMILY"
    assert resolve_vnext_symbol_family("MESM26-CME") == "SPX500_ES_FAMILY"
    assert resolve_vnext_symbol_family("NQM26-CME") == "NAS100_NQ_FAMILY"
    assert resolve_vnext_symbol_family("YMM26-CME") == "US30_YM_FAMILY"
    assert resolve_vnext_symbol_family("MYMM26-CME") == "US30_YM_FAMILY"
    assert resolve_vnext_symbol_family("6EM26-CME") == "EURUSD_6E_FAMILY"
    assert resolve_vnext_symbol_family("6BM26-CME") == "GBPUSD_6B_FAMILY"
    assert resolve_vnext_symbol_family("6JM26-CME") == "USDJPY_6J_FAMILY"
    assert resolve_vnext_symbol_family("GCM26-CME") == "XAUUSD_GC_FAMILY"
    assert resolve_vnext_symbol_family("GCM26-COMEX") == "XAUUSD_GC_FAMILY"
    assert resolve_vnext_symbol_family("SIM26-CME") == "XAGUSD_SILVER_FAMILY"


def test_runtime_normalizes_symbol_family_from_canonical_symbol_when_source_symbol_is_broker_dotted():
    event = normalize_event(
        {
            "symbol": "US30_cash",
            "source_symbol": "US30.cash",
            "kill_zone": "ny",
            "side": "LONG",
            "timeframe": "M15",
        }
    )

    assert event["symbol_family"] == "US30_YM_FAMILY"


def test_runtime_matches_family_only_evidence_for_broker_dotted_events(tmp_path):
    artifact = tmp_path / "vnext_impl.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "vnext_matrix_row_id": "us30-family-follow",
                "row_type": "gtos_vnext_evidence_system_row",
                "symbol_family": "US30_YM_FAMILY",
                "route_session": "ny_core",
                "market_timeframe": "M15",
                "side": "LONG",
                "action_class": "follow_rule",
                "source_name": "gtos_vnext_market_timeframe_expansion",
                "evidence_family": "expanded_market_reduced_surface",
                "source_artifact": "research/full_matrix.jsonl",
                "source_line_no": 101,
                "source_row_id": "mtf-101",
                "r_metrics": {
                    "cost_adjusted_simulated_r": _metric(0.32, 5),
                    "stress_simulated_r": _metric(0.18, 5),
                    "effective_n": _metric(170, 5),
                    "proxy_score": _metric(0, 0),
                },
            }
        ],
    )

    decision = evaluate_vnext_event(
        {
            "symbol": "US30_cash",
            "source_symbol": "US30.cash",
            "kill_zone": "ny",
            "side": "LONG",
            "timeframe": "M15",
        },
        _config(artifact),
    )

    assert decision.decision == "FOLLOW"
    assert decision.event["symbol_family"] == "US30_YM_FAMILY"
    assert decision.evidence["symbol_family_counts"] == {"US30_YM_FAMILY": 1}
    assert decision.evidence["rows"][0]["source_row_id"] == "mtf-101"


def test_runtime_matches_source_symbol_scoped_evidence_for_broker_dotted_events(tmp_path):
    artifact = tmp_path / "vnext_impl.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "vnext_matrix_row_id": "us30-source-symbol-follow",
                "row_type": "gtos_vnext_evidence_system_row",
                "symbol": "US30",
                "source_symbol": "US30_YM",
                "route_session": "ny_core",
                "market_timeframe": "M15",
                "side": "LONG",
                "action_class": "follow_rule",
                "source_name": "gtos_vnext_market_timeframe_expansion",
                "evidence_family": "expanded_market_reduced_surface",
                "source_artifact": "research/full_matrix.jsonl",
                "source_line_no": 103,
                "source_row_id": "mtf-103",
                "r_metrics": {
                    "cost_adjusted_simulated_r": _metric(0.28, 4),
                    "stress_simulated_r": _metric(0.16, 4),
                    "effective_n": _metric(170, 4),
                    "proxy_score": _metric(0, 0),
                },
            }
        ],
    )

    decision = evaluate_vnext_event(
        {
            "symbol": "US30_cash",
            "source_symbol": "US30.cash",
            "kill_zone": "ny",
            "side": "LONG",
            "timeframe": "M15",
        },
        _config(artifact),
    )

    assert decision.decision == "FOLLOW"
    assert decision.evidence["source_symbol_counts"] == {"US30_YM": 1}
    assert decision.evidence["symbol_counts"] == {"US30": 1}
    assert decision.evidence["rows"][0]["source_row_id"] == "mtf-103"


def test_runtime_matches_family_only_evidence_for_futures_contract_events(tmp_path):
    artifact = tmp_path / "vnext_impl.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "vnext_matrix_row_id": "silver-family-follow",
                "row_type": "gtos_vnext_evidence_system_row",
                "symbol_family": "XAGUSD_SILVER_FAMILY",
                "route_session": "ny_core",
                "market_timeframe": "M15",
                "side": "LONG",
                "action_class": "follow_rule",
                "source_name": "gtos_vnext_market_timeframe_expansion",
                "evidence_family": "expanded_market_reduced_surface",
                "source_artifact": "research/full_matrix.jsonl",
                "source_line_no": 102,
                "source_row_id": "mtf-102",
                "r_metrics": {
                    "cost_adjusted_simulated_r": _metric(0.41, 6),
                    "stress_simulated_r": _metric(0.23, 6),
                    "effective_n": _metric(95, 6),
                    "proxy_score": _metric(0, 0),
                },
            }
        ],
    )

    decision = evaluate_vnext_event(
        {
            "symbol": "XAGUSD",
            "source_symbol": "SIM26-CME",
            "kill_zone": "ny",
            "side": "LONG",
            "timeframe": "M15",
        },
        _config(artifact),
    )

    assert decision.decision == "FOLLOW"
    assert decision.event["symbol_family"] == "XAGUSD_SILVER_FAMILY"
    assert decision.evidence["symbol_family_counts"] == {"XAGUSD_SILVER_FAMILY": 1}
    assert decision.evidence["rows"][0]["source_row_id"] == "mtf-102"


def test_runtime_matches_source_symbol_scoped_evidence_for_futures_contract_events(tmp_path):
    artifact = tmp_path / "vnext_impl.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "vnext_matrix_row_id": "silver-source-symbol-follow",
                "row_type": "gtos_vnext_evidence_system_row",
                "symbol": "XAGUSD_SI",
                "source_symbol": "SI",
                "route_session": "ny_core",
                "market_timeframe": "M15",
                "side": "LONG",
                "action_class": "follow_rule",
                "source_name": "gtos_vnext_market_timeframe_expansion",
                "evidence_family": "expanded_market_reduced_surface",
                "source_artifact": "research/full_matrix.jsonl",
                "source_line_no": 104,
                "source_row_id": "mtf-104",
                "r_metrics": {
                    "cost_adjusted_simulated_r": _metric(0.37, 5),
                    "stress_simulated_r": _metric(0.21, 5),
                    "effective_n": _metric(95, 5),
                    "proxy_score": _metric(0, 0),
                },
            }
        ],
    )

    decision = evaluate_vnext_event(
        {
            "symbol": "XAGUSD",
            "source_symbol": "SIM26-CME",
            "kill_zone": "ny",
            "side": "LONG",
            "timeframe": "M15",
        },
        _config(artifact),
    )

    assert decision.decision == "FOLLOW"
    assert decision.evidence["source_symbol_counts"] == {"SI": 1}
    assert decision.evidence["symbol_counts"] == {"XAGUSD_SI": 1}
    assert decision.evidence["rows"][0]["source_row_id"] == "mtf-104"


def test_runtime_matches_source_symbol_scoped_evidence_for_fx_futures_contract_events(tmp_path):
    artifact = tmp_path / "vnext_impl.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "vnext_matrix_row_id": "eur-source-symbol-follow",
                "row_type": "gtos_vnext_evidence_system_row",
                "symbol": "EURUSD_6E",
                "source_symbol": "6E",
                "route_session": "london_core",
                "market_timeframe": "M15",
                "side": "LONG",
                "action_class": "follow_rule",
                "source_name": "gtos_vnext_market_timeframe_expansion",
                "evidence_family": "expanded_market_reduced_surface",
                "source_artifact": "research/full_matrix.jsonl",
                "source_line_no": 105,
                "source_row_id": "mtf-105",
                "r_metrics": {
                    "cost_adjusted_simulated_r": _metric(0.22, 4),
                    "stress_simulated_r": _metric(0.14, 4),
                    "effective_n": _metric(64, 4),
                    "proxy_score": _metric(0, 0),
                },
            }
        ],
    )

    decision = evaluate_vnext_event(
        {
            "symbol": "EURUSD",
            "source_symbol": "6EM26-CME",
            "kill_zone": "london",
            "side": "LONG",
            "timeframe": "M15",
        },
        _config(artifact),
    )

    assert decision.decision == "FOLLOW"
    assert decision.event["symbol_family"] == "EURUSD_6E_FAMILY"
    assert decision.evidence["source_symbol_counts"] == {"6E": 1}
    assert decision.evidence["symbol_counts"] == {"EURUSD_6E": 1}
    assert decision.evidence["rows"][0]["source_row_id"] == "mtf-105"


def test_runtime_matches_xauusd_evidence_for_gold_futures_contract_events(tmp_path):
    artifact = tmp_path / "vnext_impl.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "vnext_matrix_row_id": "gold-source-symbol-follow",
                "row_type": "gtos_vnext_evidence_system_row",
                "symbol": "XAUUSD",
                "source_symbol": "XAUUSD",
                "route_session": "ny_core",
                "market_timeframe": "M15",
                "side": "SHORT",
                "action_class": "follow_rule",
                "source_name": "gtos_vnext_market_timeframe_expansion",
                "evidence_family": "expanded_market_reduced_surface",
                "source_artifact": "research/full_matrix.jsonl",
                "source_line_no": 106,
                "source_row_id": "mtf-106",
                "r_metrics": {
                    "cost_adjusted_simulated_r": _metric(0.31, 5),
                    "stress_simulated_r": _metric(0.19, 5),
                    "effective_n": _metric(118, 5),
                    "proxy_score": _metric(0, 0),
                },
            }
        ],
    )

    decision = evaluate_vnext_event(
        {
            "symbol": "XAUUSD",
            "source_symbol": "GCM26-CME",
            "kill_zone": "ny",
            "side": "SHORT",
            "timeframe": "M15",
        },
        _config(artifact),
    )

    assert decision.decision == "FOLLOW"
    assert decision.event["symbol_family"] == "XAUUSD_GC_FAMILY"
    assert decision.evidence["source_symbol_counts"] == {"XAUUSD": 1}
    assert decision.evidence["symbol_counts"] == {"XAUUSD": 1}
    assert decision.evidence["rows"][0]["source_row_id"] == "mtf-106"


def test_route_variant_pruning_uses_artifact_scopes_instead_of_cartesian_product(tmp_path):
    artifact = tmp_path / "vnext_pruned_routes.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "vnext_matrix_row_id": "pruned-route-follow",
                "row_type": "gtos_vnext_evidence_system_row",
                "symbol": "USDJPY",
                "source_symbol": "USDJPY",
                "route_session": "london_core",
                "market_timeframe": "H4",
                "horizon_id": "h16",
                "side": "LONG",
                "route_family": "moonshot_mechanical",
                "source_component": "shadow_source_guard",
                "action_class": "follow_rule",
                "source_name": "moonshot_reduced_surface_candidates",
                "evidence_family": "expanded_market_reduced_surface",
                "r_metrics": {
                    "cost_adjusted_simulated_r": _metric(0.42, 2),
                    "stress_simulated_r": _metric(0.40, 2),
                    "effective_n": _metric(144, 2),
                    "proxy_score": _metric(0, 0),
                },
            }
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "post_l2_prune_route_variants_to_artifact_scopes": True,
            "post_l2_route_use_candidate_framework_only": False,
            "post_l2_route_timeframes": ["M1", "M5", "M15", "H1", "H4", "D1"],
            "post_l2_route_horizons": ["h4", "h16", "h32"],
            "post_l2_route_frameworks": ["ob_retest", "fvg_fill", "breaker_re_entry"],
            "post_l2_route_families": ["moonshot_mechanical", "numeric_router", "cp281_native_rule"],
            "post_l2_route_source_components": ["shadow_source_guard", "market_gap_code"],
        }
    )

    decision = evaluate_vnext_route_event(
        {
            "symbol": "USDJPY",
            "source_symbol": "USDJPY",
            "kill_zone": "london",
            "side": "LONG",
            "timeframe": "M15",
        },
        cfg,
    )

    assert decision.decision == "FOLLOW"
    assert decision.evidence["route_event_count"] == 2
    assert decision.evidence["matched_rows"] == 1


def test_direct_artifact_scope_matching_bypasses_generic_subset_matcher(tmp_path, monkeypatch):
    artifact = tmp_path / "vnext_direct_route_match.jsonl"
    rows = [
        {
            "vnext_matrix_row_id": "direct-route-follow",
            "row_type": "gtos_vnext_evidence_system_row",
            "symbol": "USDJPY",
            "source_symbol": "USDJPY",
            "route_session": "london_core",
            "market_timeframe": "H4",
            "horizon_id": "h16",
            "side": "LONG",
            "route_family": "moonshot_mechanical",
            "source_component": "shadow_source_guard",
            "action_class": "follow_rule",
            "source_name": "moonshot_reduced_surface_candidates",
            "evidence_family": "expanded_market_reduced_surface",
            "r_metrics": {
                "cost_adjusted_simulated_r": _metric(0.42, 2),
                "stress_simulated_r": _metric(0.40, 2),
                "effective_n": _metric(144, 2),
                "proxy_score": _metric(0, 0),
            },
        }
    ]
    _write_jsonl(artifact, rows)
    index = GTOSVNextEvidenceIndex.from_rows(
        rows,
        artifact_paths=(str(artifact),),
        rows_loaded_by_path={str(artifact): len(rows)},
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "post_l2_prune_route_variants_to_artifact_scopes": True,
            "post_l2_match_artifact_scopes_directly": True,
            "post_l2_route_use_candidate_framework_only": False,
            "post_l2_route_timeframes": ["M15", "H4"],
            "post_l2_route_horizons": ["h16"],
            "post_l2_route_families": ["moonshot_mechanical"],
            "post_l2_route_source_components": ["shadow_source_guard"],
        }
    )

    def fail_generic_match(*args, **kwargs):
        raise AssertionError("generic subset matcher should not run for direct route matching")

    monkeypatch.setattr(GTOSVNextEvidenceIndex, "match_event", fail_generic_match)

    decision = evaluate_vnext_route_event(
        {
            "symbol": "USDJPY",
            "source_symbol": "USDJPY",
            "kill_zone": "london",
            "side": "LONG",
            "timeframe": "M15",
        },
        cfg,
        artifact_index=index,
    )

    assert decision.decision == "FOLLOW"
    assert decision.evidence["route_event_count"] == 2
    assert decision.evidence["matched_rows"] == 1
    assert decision.evidence["rows"][0]["row_id"] == "direct-route-follow"


def test_direct_artifact_scope_matching_matches_generic_route_results(tmp_path):
    artifact = tmp_path / "vnext_direct_route_parity.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "vnext_matrix_row_id": "direct-route-follow",
                "row_type": "gtos_vnext_evidence_system_row",
                "symbol": "USDJPY",
                "source_symbol": "USDJPY",
                "route_session": "london_core",
                "market_timeframe": "H4",
                "horizon_id": "h16",
                "side": "LONG",
                "route_family": "moonshot_mechanical",
                "source_component": "shadow_source_guard",
                "action_class": "follow_rule",
                "source_name": "moonshot_reduced_surface_candidates",
                "evidence_family": "expanded_market_reduced_surface",
                "r_metrics": {
                    "cost_adjusted_simulated_r": _metric(0.42, 2),
                    "stress_simulated_r": _metric(0.40, 2),
                    "effective_n": _metric(144, 2),
                    "proxy_score": _metric(0, 0),
                },
            },
            {
                "vnext_matrix_row_id": "direct-route-avoid",
                "row_type": "gtos_vnext_evidence_system_row",
                "symbol": "USDJPY",
                "source_symbol": "USDJPY",
                "route_session": "london_core",
                "market_timeframe": "H1",
                "horizon_id": "h4",
                "side": "LONG",
                "route_family": "numeric_router",
                "source_component": "market_gap_code",
                "action_class": "avoid_filter",
                "source_name": "numeric_router_default_off_scope_decision_catalog",
                "evidence_family": "numeric_router_runtime_recommendation",
                "r_metrics": {
                    "cost_adjusted_simulated_r": _metric(-0.20, 1),
                    "stress_simulated_r": _metric(-0.25, 1),
                    "effective_n": _metric(20, 1),
                    "proxy_score": _metric(0, 0),
                },
            },
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "conflict_resolution": "strict",
            "post_l2_prune_route_variants_to_artifact_scopes": True,
            "post_l2_route_use_candidate_framework_only": False,
            "post_l2_route_timeframes": ["M15", "H1", "H4"],
            "post_l2_route_horizons": ["h4", "h16"],
            "post_l2_route_families": ["moonshot_mechanical", "numeric_router"],
            "post_l2_route_source_components": ["shadow_source_guard", "market_gap_code"],
        }
    )
    event = {
        "symbol": "USDJPY",
        "source_symbol": "USDJPY",
        "kill_zone": "london",
        "side": "LONG",
        "timeframe": "M15",
    }

    direct_cfg = {
        **cfg,
        "gtos_vnext_runtime": {
            **cfg["gtos_vnext_runtime"],
            "post_l2_match_artifact_scopes_directly": True,
        },
    }
    generic_cfg = {
        **cfg,
        "gtos_vnext_runtime": {
            **cfg["gtos_vnext_runtime"],
            "post_l2_match_artifact_scopes_directly": False,
        },
    }
    direct = evaluate_vnext_route_event(event, direct_cfg)
    generic = evaluate_vnext_route_event(event, generic_cfg)

    assert direct.decision == generic.decision == "MIXED"
    assert direct.evidence["route_event_count"] == generic.evidence["route_event_count"] == 3
    assert direct.evidence["matched_rows"] == generic.evidence["matched_rows"] == 2
    assert direct.evidence["matched_row_ids"] == generic.evidence["matched_row_ids"]


def test_post_l2_route_variant_evaluation_consumes_higher_timeframe_evidence(tmp_path):
    artifact = tmp_path / "vnext_impl.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "vnext_matrix_row_id": "h4-follow",
                "row_type": "gtos_vnext_evidence_system_row",
                "symbol": "XAUUSD",
                "source_symbol": "XAUUSD",
                "route_session": "london_core",
                "market_timeframe": "H4",
                "horizon_id": "h16",
                "side": "LONG",
                "action_class": "follow_rule",
                "source_name": "moonshot_reduced_surface_candidates",
                "evidence_family": "expanded_market_reduced_surface",
                "source_artifact": "research/h4_source.jsonl",
                "source_line_no": 9,
                "source_row_id": "source-h4",
                "r_metrics": {
                    "cost_adjusted_simulated_r": _metric(0.42, 2),
                    "stress_simulated_r": _metric(0.40, 2),
                    "effective_n": _metric(144, 2),
                    "proxy_score": _metric(0, 0),
                },
            }
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"]["post_l2_evaluate_route_variants"] = True
    cfg["gtos_vnext_runtime"]["post_l2_route_timeframes"] = ["M15", "H4"]
    cfg["gtos_vnext_runtime"]["post_l2_route_horizons"] = ["h16"]

    route_decision = evaluate_vnext_route_event(
        {"symbol": "XAUUSD", "source_symbol": "XAUUSD", "kill_zone": "london", "side": "LONG", "timeframe": "M15"},
        cfg,
    )
    exact_decision = evaluate_vnext_event(
        {"symbol": "XAUUSD", "source_symbol": "XAUUSD", "kill_zone": "london", "side": "LONG", "timeframe": "M15"},
        cfg,
    )

    assert exact_decision.decision == "LEGACY"
    assert route_decision.decision == "FOLLOW"
    assert route_decision.reason == "matched_vnext_route_scope"
    assert route_decision.evidence["route_event_count"] > 1
    assert route_decision.evidence["matched_row_ids"] == ["h4-follow"]


def test_post_l2_route_variant_evaluation_consumes_route_family_evidence(tmp_path):
    artifact = tmp_path / "vnext_route_family_impl.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "vnext_matrix_row_id": "moonshot-route-follow",
                "row_type": "gtos_vnext_evidence_system_row",
                "symbol": "XAUUSD",
                "source_symbol": "XAUUSD",
                "route_session": "london_core",
                "market_timeframe": "H4",
                "timeframe": "H4",
                "horizon_id": "h16",
                "side": "LONG",
                "framework": "ob_retest",
                "route_family": "moonshot_mechanical",
                "action_class": "follow_rule",
                "source_name": "moonshot_reduced_surface_candidates",
                "evidence_family": "expanded_market_reduced_surface",
                "source_artifact": "research/moonshot_source.jsonl",
                "source_line_no": 12,
                "source_row_id": "source-moonshot",
                "r_metrics": {
                    "cost_adjusted_simulated_r": _metric(0.58, 4),
                    "stress_simulated_r": _metric(0.44, 4),
                    "effective_n": _metric(188, 4),
                    "proxy_score": _metric(0, 0),
                },
            }
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "post_l2_evaluate_route_variants": True,
            "post_l2_route_timeframes": ["M15", "H4"],
            "post_l2_route_horizons": ["h16"],
            "post_l2_route_families": ["moonshot_mechanical"],
            "post_l2_route_use_candidate_framework_only": True,
        }
    )

    route_decision = evaluate_vnext_route_event(
        {
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "kill_zone": "london",
            "side": "LONG",
            "framework": "ob_retest",
            "timeframe": "M15",
        },
        cfg,
    )
    exact_decision = evaluate_vnext_event(
        {
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "kill_zone": "london",
            "side": "LONG",
            "framework": "ob_retest",
            "timeframe": "M15",
        },
        cfg,
    )

    assert exact_decision.decision == "LEGACY"
    assert route_decision.decision == "FOLLOW"
    assert route_decision.evidence["matched_row_ids"] == ["moonshot-route-follow"]
    assert route_decision.evidence["route_family_counts"] == {"moonshot_mechanical": 1}


def test_post_l2_route_variants_stay_on_candidate_effective_framework(tmp_path):
    artifact = tmp_path / "vnext_impl.jsonl"
    base_scope = {
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "route_session": "london_core",
        "market_timeframe": "H4",
        "horizon_id": "h16",
        "side": "LONG",
    }
    _write_jsonl(
        artifact,
        [
            _review_row(
                "ob-follow",
                {**base_scope, "framework": "ob_retest"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=5,
                stress=4,
                n=25,
            ),
            _review_row(
                "fvg-avoid",
                {**base_scope, "framework": "fvg_fill"},
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-9,
                stress=-12,
                n=25,
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "post_l2_evaluate_route_variants": True,
            "post_l2_route_use_candidate_framework_only": True,
            "post_l2_route_timeframes": ["H4"],
            "post_l2_route_horizons": ["h16"],
            "post_l2_route_frameworks": ["ob_retest", "fvg_fill"],
        }
    )

    decision = evaluate_vnext_route_event(
        {
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "kill_zone": "london",
            "side": "LONG",
            "timeframe": "M15",
            "effective_framework": "ob_retest",
        },
        cfg,
    )

    assert decision.decision == "FOLLOW"
    assert decision.reason == "matched_vnext_route_scope"
    assert decision.evidence["matched_row_ids"] == ["ob-follow"]
    assert decision.evidence["framework_counts"] == {"ob_retest": 1}


def test_runtime_returns_legacy_when_disabled_or_unmatched(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    _write_jsonl(
        artifact,
        [_review_row("follow-row", {"symbol": "GBPJPY"}, "DEFAULT_OFF_FOLLOW_SCORER_REVIEW", r=1, stress=1, n=10)],
    )

    disabled = evaluate_vnext_event({"symbol": "GBPJPY"}, _config(artifact, enabled=False))
    unmatched = evaluate_vnext_event({"symbol": "XAUUSD"}, _config(artifact))

    assert disabled.decision == "LEGACY"
    assert disabled.reason == "gtos_vnext_runtime_disabled"
    assert unmatched.decision == "LEGACY"
    assert unmatched.reason == "no_matching_vnext_scope"


def test_candidate_event_builder_uses_live_orchestrator_fields():
    analysis = SimpleNamespace(
        framework="ob_retest",
        trade_parameters=SimpleNamespace(direction="SHORT"),
    )

    event = build_vnext_event_from_candidate(
        analysis=analysis,
        raw_data={
            "candle_close_utc": "2026-05-18T07:15:00+00:00",
            "source_name": "cp281_rule_replay_result_table",
            "evidence_family": "cp281_native_rule_replay",
            "source_role": "historical_replay_result_table",
            "r_evidence_class": "SIMULATED_REPLAY_R",
        },
        kill_zone="london",
        config={"model_a": {"entry_timeframe": "M15"}},
        symbol="NAS100",
        source_symbol="NAS100",
    )

    assert event["symbol"] == "NAS100"
    assert event["source_symbol"] == "NAS100"
    assert event["route_session"] == "london"
    assert event["side"] == "SHORT"
    assert event["market_timeframe"] == "M15"
    assert event["timeframe"] == "M15"
    assert event["market"] == "NAS100"
    assert event["route_family"] == "ob_retest"
    assert event["source_name"] == "cp281_rule_replay_result_table"
    assert event["evidence_family"] == "cp281_native_rule_replay"
    assert event["source_role"] == "historical_replay_result_table"
    assert event["r_evidence_class"] == "SIMULATED_REPLAY_R"


def test_candidate_event_builder_uses_l2_effective_framework():
    analysis = SimpleNamespace(
        framework="ob_retest",
        trade_parameters=SimpleNamespace(direction="LONG"),
        frameworks_evaluated={
            "ob_retest": SimpleNamespace(qualified=False, reason="no OB"),
            "fvg_fill": SimpleNamespace(qualified=True, reason="FVG present"),
        },
        reasoning=SimpleNamespace(
            h1_setup=SimpleNamespace(poi_type="FVG"),
        ),
    )

    event = build_vnext_event_from_candidate(
        analysis=analysis,
        raw_data={"candle_close_utc": "2026-05-18T07:15:00+00:00"},
        kill_zone="london",
        config={"model_a": {"entry_timeframe": "M15"}},
        symbol="GBPJPY",
        source_symbol="GBPJPY",
    )

    assert event["framework"] == "fvg_fill"
    assert event["effective_framework"] == "fvg_fill"
    assert event["route_family"] == "fvg_fill"
    assert event["wrapper_framework"] == "ob_retest"
    assert event["framework_route_overridden"] is True
    assert event["framework_route_reason"] == "wrapper_disagrees_single_qualified"


def test_candidate_event_builder_uses_runtime_symbol_when_config_market_is_stale():
    analysis = SimpleNamespace(
        framework="ob_retest",
        trade_parameters=SimpleNamespace(direction="LONG"),
        frameworks_evaluated={},
        reasoning=SimpleNamespace(h1_setup=SimpleNamespace(poi_type="OB")),
    )

    event = build_vnext_event_from_candidate(
        analysis=analysis,
        raw_data={"candle_close_utc": "2026-05-18T07:15:00+00:00"},
        kill_zone="london",
        config={"market": {"symbol": "XAUUSD"}, "model_a": {"entry_timeframe": "M15"}},
        symbol="USDJPY",
        source_symbol="USDJPY",
    )

    assert event["market"] == "USDJPY"
    assert event["symbol_family"] == "USDJPY_6J_FAMILY"


def test_pre_ai_event_builder_uses_bias_without_ai_output():
    event = build_vnext_pre_ai_event(
        symbol="NAS100",
        source_symbol="NAS100",
        kill_zone="london",
        config={"model_a": {"entry_timeframe": "M15"}},
        bias="bearish",
        raw_data={
            "candle_close_utc": "2026-05-18T07:15:00+00:00",
            "source_name": "ai_narrowing_policy",
            "evidence_family": "ai_decision_architecture",
            "system_surface": "PRE_AI_MECHANICAL_SELECTOR_REVIEW_ONLY",
        },
    )

    assert event["symbol"] == "NAS100"
    assert event["route_session"] == "london"
    assert event["side"] == "SHORT"
    assert event["market_timeframe"] == "M15"
    assert event["timeframe"] == "M15"
    assert event["market"] == "NAS100"
    assert event["source_name"] == "ai_narrowing_policy"
    assert event["evidence_family"] == "ai_decision_architecture"
    assert event["system_surface"] == "PRE_AI_MECHANICAL_SELECTOR_REVIEW_ONLY"


def test_pre_ai_event_builder_uses_runtime_symbol_when_config_market_is_stale():
    event = build_vnext_pre_ai_event(
        symbol="USDJPY",
        source_symbol="USDJPY",
        kill_zone="london",
        config={"market": {"symbol": "XAUUSD"}, "model_a": {"entry_timeframe": "M15"}},
        bias="bullish",
    )

    assert event["market"] == "USDJPY"
    assert event["symbol_family"] == "USDJPY_6J_FAMILY"


def test_pre_ai_router_can_skip_ai_when_avoid_only_and_config_flipped(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "avoid-row",
                {"symbol": "NAS100", "source_symbol": "NAS100", "route_session": "london", "side": "SHORT"},
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-81.2,
                stress=-625.6,
                n=11475,
            )
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"]["pre_ai_apply_to_ai_call"] = True

    decision = evaluate_pre_ai_vnext(
        symbol="NAS100",
        source_symbol="NAS100",
        kill_zone="london",
        config=cfg,
        bias="bearish",
    )

    assert decision.action == "SKIP_AI_AVOID_ONLY"
    assert decision.decision == "AVOID"
    assert decision.side_decisions[0].evidence["metrics"]["stress_simulated_r"]["sum"] == -625.6


def test_pre_ai_router_runs_but_allows_ai_when_execution_effect_is_off(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "avoid-row",
                {"symbol": "NAS100", "route_session": "london", "side": "SHORT"},
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-81.2,
                stress=-625.6,
                n=11475,
            )
        ],
    )

    decision = evaluate_pre_ai_vnext(
        symbol="NAS100",
        source_symbol="NAS100",
        kill_zone="london",
        config=_config(artifact),
        bias="bearish",
    )

    assert decision.action == "ALLOW_AI"
    assert decision.decision == "AVOID"
    assert decision.apply_to_ai_call is False


def test_production_change_promotion_can_narrow_pre_ai_without_live_ai_effect():
    scope = {
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "symbol_family": "XAUUSD_GC_FAMILY",
        "market": "XAUUSD",
        "route_session": "ny_core",
        "side": "LONG",
        "framework": "ob_retest",
        "route_family": "numeric_router",
        "market_timeframe": "M15",
        "timeframe": "M15",
        "source_component": "rejected_candidate_blocked_limit_value",
    }
    row = _production_change_promotion_row(
        "prodchg-pre-ai-follow",
        scope,
        "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
        r=8.0,
        n=38,
        proxy=8.0,
        source_component="rejected_candidate_blocked_limit_value",
        action_class="rejected_candidate_blocked_limit_value_follow_scorer",
        route_family="numeric_router",
        framework="ob_retest",
    )
    cfg = _config("unused.jsonl")
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": False,
            "pre_ai_evaluate_all_sides": False,
            "pre_ai_evaluate_route_variants": True,
            "pre_ai_prune_route_variants_to_artifact_scopes": True,
            "pre_ai_match_artifact_scopes_directly": True,
            "pre_ai_route_timeframes": ["M15"],
            "pre_ai_route_horizons": [""],
            "pre_ai_route_frameworks": ["ob_retest"],
            "pre_ai_route_families": ["numeric_router"],
            "pre_ai_route_source_components": [
                "rejected_candidate_blocked_limit_value",
            ],
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="XAUUSD",
        source_symbol="XAUUSD",
        kill_zone="ny",
        config=cfg,
        bias="bullish",
        artifact_rows=[row],
    )

    assert decision.action == "ALLOW_AI"
    assert decision.would_action == "NARROW_AI_TO_ROUTE"
    assert decision.apply_to_ai_call is False
    assert decision.recommended_side == "LONG"
    assert decision.recommended_frameworks == ("ob_retest",)
    assert decision.recommended_route_families == ("numeric_router",)
    assert decision.reason == "matched_pre_ai_vnext_scope"
    assert decision.side_decisions[0].evidence["source_component_counts"] == {
        "rejected_candidate_blocked_limit_value": 1
    }


def test_pre_ai_router_returns_mixed_when_all_sides_conflict(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "long-follow",
                {"symbol": "USDJPY", "route_session": "london", "side": "LONG"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=10,
                stress=9,
                n=50,
            ),
            _review_row(
                "short-avoid",
                {"symbol": "USDJPY", "route_session": "london", "side": "SHORT"},
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-20,
                stress=-30,
                n=50,
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"]["pre_ai_evaluate_all_sides"] = True

    decision = evaluate_pre_ai_vnext(
        symbol="USDJPY",
        source_symbol="USDJPY",
        kill_zone="london",
        config=cfg,
        bias="bullish",
    )

    assert decision.action == "ALLOW_AI"
    assert decision.decision == "MIXED"
    assert [item.decision for item in decision.side_decisions] == ["FOLLOW", "AVOID"]


def test_pre_ai_router_can_narrow_ai_to_single_follow_side_when_config_flipped(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "long-follow",
                {"symbol": "USDJPY", "route_session": "london", "side": "LONG"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=10,
                stress=9,
                n=50,
            ),
            _review_row(
                "short-avoid",
                {"symbol": "USDJPY", "route_session": "london", "side": "SHORT"},
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-20,
                stress=-30,
                n=50,
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"]["pre_ai_evaluate_all_sides"] = True
    cfg["gtos_vnext_runtime"]["pre_ai_apply_to_ai_call"] = True

    decision = evaluate_pre_ai_vnext(
        symbol="USDJPY",
        source_symbol="USDJPY",
        kill_zone="london",
        config=cfg,
        bias="bearish",
    )

    assert decision.action == "NARROW_AI_TO_SIDE"
    assert decision.would_action == "NARROW_AI_TO_SIDE"
    assert decision.recommended_side == "LONG"
    assert decision.blocked_sides == ("SHORT",)
    assert decision.evaluated_sides == ("LONG", "SHORT")


def test_pre_ai_router_keeps_source_bound_positive_follow_despite_geometry_proxy(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "long-follow-unbound-geometry",
                {"symbol": "XAGUSD", "route_session": "london", "side": "LONG"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=12,
                stress=10,
                n=168,
                target_stop_order_class="TARGET_STOP_ORDER_NOT_SOURCE_BOUND",
            ),
            _review_row(
                "short-avoid",
                {"symbol": "XAGUSD", "route_session": "london", "side": "SHORT"},
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-20,
                stress=-30,
                n=50,
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"]["pre_ai_evaluate_all_sides"] = True
    cfg["gtos_vnext_runtime"]["pre_ai_apply_to_ai_call"] = True

    decision = evaluate_pre_ai_vnext(
        symbol="XAGUSD",
        source_symbol="XAGUSD",
        kill_zone="london",
        config=cfg,
        bias="bullish",
    )

    assert decision.action == "NARROW_AI_TO_SIDE"
    assert decision.would_action == "NARROW_AI_TO_SIDE"
    assert decision.recommended_side == "LONG"
    assert decision.blocked_sides == ("SHORT",)
    assert decision.risk_vetoed_sides == ()
    assert decision.side_risk_reasons["LONG"] == "vnext_risk_strong_follow"
    assert decision.side_risk_reasons["SHORT"] == "vnext_risk_avoid"


def test_pre_ai_router_vetoes_low_effective_n_follow_side(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "low-n-follow",
                {"symbol": "XAGUSD", "route_session": "london", "side": "LONG"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=5,
                stress=2,
                n=2,
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_min_follow_effective_n": 3,
            "pre_ai_evaluate_all_sides": False,
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="XAGUSD",
        source_symbol="XAGUSD",
        kill_zone="london",
        config=cfg,
        bias="bullish",
    )

    assert decision.action == "SKIP_AI_AVOID_ONLY"
    assert decision.would_action == "SKIP_AI_AVOID_ONLY"
    assert decision.risk_vetoed_sides == ("LONG",)
    assert decision.side_risk_reasons["LONG"] == "vnext_pre_ai_follow_effective_n_below_min"


def test_pre_ai_router_can_narrow_ai_to_framework_route_when_config_flipped(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    base_scope = {"symbol": "XAUUSD", "route_session": "london", "side": "LONG"}
    _write_jsonl(
        artifact,
        [
            _review_row(
                "ob-follow",
                {**base_scope, "framework": "ob_retest"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=20,
                stress=8,
                n=200,
                proxy=3,
                framework="ob_retest",
            ),
            _review_row(
                "fvg-avoid",
                {**base_scope, "framework": "fvg_fill"},
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-2,
                stress=-2,
                n=20,
                proxy=-1,
                framework="fvg_fill",
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"]["pre_ai_apply_to_ai_call"] = True
    cfg["gtos_vnext_runtime"]["pre_ai_evaluate_all_sides"] = True
    cfg["gtos_vnext_runtime"]["pre_ai_route_frameworks"] = ["ob_retest", "fvg_fill"]
    cfg["gtos_vnext_runtime"]["conflict_resolution"] = "evidence_weighted"

    decision = evaluate_pre_ai_vnext(
        symbol="XAUUSD",
        source_symbol="XAUUSD",
        kill_zone="london",
        config=cfg,
        bias="no_bias",
    )

    assert decision.action == "NARROW_AI_TO_ROUTE"
    assert decision.would_action == "NARROW_AI_TO_ROUTE"
    assert decision.recommended_side == "LONG"
    assert decision.recommended_frameworks == ("ob_retest",)
    assert decision.recommended_route_families == ("ob_retest",)
    assert decision.blocked_frameworks == ("fvg_fill",)
    assert decision.blocked_route_families == ("fvg_fill",)
    assert decision.reason == "pre_ai_vnext_route_to_LONG_ob_retest"
    assert decision.side_decisions[0].evidence["decision_resolution"]["selected_decision"] == "FOLLOW"


def test_pre_ai_router_prefers_core_ob_framework_when_follow_pressure_is_tied(tmp_path):
    artifact = tmp_path / "vnext_ob_core_preference.jsonl"
    base_scope = {"symbol": "XAUUSD", "route_session": "london", "side": "LONG"}
    _write_jsonl(
        artifact,
        [
            _review_row(
                "ob-follow-core",
                {**base_scope, "framework": "ob_retest"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=10.0,
                stress=0.0,
                n=120,
                proxy=0.0,
                framework="ob_retest",
            ),
            _review_row(
                "fvg-follow-weaker",
                {**base_scope, "framework": "fvg_fill"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=9.0,
                stress=0.0,
                n=120,
                proxy=0.0,
                framework="fvg_fill",
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": False,
            "pre_ai_route_frameworks": ["ob_retest", "fvg_fill"],
            "pre_ai_ob_core_framework_preference_enabled": True,
            "pre_ai_ob_core_min_abs_pressure": 1.0,
            "pre_ai_ob_core_competing_framework_dominance_ratio": 1.5,
            "conflict_resolution": "evidence_weighted",
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="XAUUSD",
        source_symbol="XAUUSD",
        kill_zone="london",
        config=cfg,
        bias="bullish",
    )

    assert decision.action == "NARROW_AI_TO_ROUTE"
    assert decision.recommended_side == "LONG"
    assert decision.recommended_frameworks == ("ob_retest",)
    assert decision.recommended_route_families == ("ob_retest",)
    assert decision.reason == "pre_ai_vnext_route_to_LONG_ob_retest"
    assert decision.side_decisions[0].evidence["framework_decision_metric_summaries"][
        "ob_retest"
    ]["FOLLOW"]["cost_adjusted_simulated_r"] == 10.0
    assert decision.side_decisions[0].evidence["framework_decision_metric_summaries"][
        "fvg_fill"
    ]["FOLLOW"]["cost_adjusted_simulated_r"] == 9.0


def test_pre_ai_router_allows_non_ob_framework_when_follow_pressure_dominates(tmp_path):
    artifact = tmp_path / "vnext_ob_core_override.jsonl"
    base_scope = {"symbol": "XAUUSD", "route_session": "london", "side": "LONG"}
    _write_jsonl(
        artifact,
        [
            _review_row(
                "ob-follow-weaker",
                {**base_scope, "framework": "ob_retest"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=4.0,
                stress=0.0,
                n=120,
                proxy=0.0,
                framework="ob_retest",
            ),
            _review_row(
                "fvg-follow-dominant",
                {**base_scope, "framework": "fvg_fill"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=8.0,
                stress=0.0,
                n=120,
                proxy=0.0,
                framework="fvg_fill",
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": False,
            "pre_ai_route_frameworks": ["ob_retest", "fvg_fill"],
            "pre_ai_ob_core_framework_preference_enabled": True,
            "pre_ai_ob_core_min_abs_pressure": 1.0,
            "pre_ai_ob_core_competing_framework_dominance_ratio": 1.5,
            "conflict_resolution": "evidence_weighted",
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="XAUUSD",
        source_symbol="XAUUSD",
        kill_zone="london",
        config=cfg,
        bias="bullish",
    )

    assert decision.action == "NARROW_AI_TO_ROUTE"
    assert decision.recommended_side == "LONG"
    assert decision.recommended_frameworks == ("fvg_fill",)
    assert decision.recommended_route_families == ("fvg_fill",)
    assert decision.reason == "pre_ai_vnext_route_to_LONG_fvg_fill"


def test_pre_ai_xau_asian_high_sweep_routes_long_ob_retest_from_current_fields(tmp_path):
    artifact = tmp_path / "empty_vnext.jsonl"
    _write_jsonl(artifact, [])
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": False,
            "pre_ai_xau_asian_sweep_continuation_enabled": True,
            "pre_ai_xau_asian_sweep_framework": "ob_retest",
        }
    )
    raw_data = {
        "session_levels": {"asian_high": 3030.0, "asian_low": 3000.0},
        "candles": {
            "M15": [
                {"time": "2026-05-19T07:15:00Z", "open": 3028.0, "high": 3034.0, "low": 3027.0, "close": 3032.0}
            ]
        },
    }

    decision = evaluate_pre_ai_vnext(
        symbol="XAUUSD",
        source_symbol="XAUUSD",
        kill_zone="london",
        config=cfg,
        bias="bearish",
        raw_data=raw_data,
    )

    assert decision.decision == "FOLLOW"
    assert decision.action == "NARROW_AI_TO_ROUTE"
    assert decision.recommended_side == "LONG"
    assert decision.recommended_frameworks == ("ob_retest",)
    assert decision.recommended_route_families == ("ob_retest",)
    assert decision.blocked_sides == ("SHORT",)
    assert decision.side_risk_reasons["SHORT"] == "xau_asian_sweep_continuation_against_side"
    assert decision.reason == "pre_ai_vnext_route_to_LONG_ob_retest"
    assert decision.ai_role_context["runtime_rules"]["xau_asian_sweep_continuation"][
        "pool_type"
    ] == "asian_high"
    assert decision.evaluated_sides == ("SHORT", "LONG")


def test_pre_ai_xau_asian_low_detected_sweep_routes_short_only_for_gold(tmp_path):
    artifact = tmp_path / "empty_vnext.jsonl"
    _write_jsonl(artifact, [])
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": False,
            "pre_ai_xau_asian_sweep_continuation_enabled": True,
        }
    )
    raw_data = {
        "detected_sweeps": [
            {
                "pool": {"type": "asian_low", "price": 3000.0, "side": "low"},
                "sweep_type": "sweep",
                "candle_index": 47,
                "time": "2026-05-19T08:00:00Z",
            }
        ]
    }

    gold_decision = evaluate_pre_ai_vnext(
        symbol="XAUUSD",
        source_symbol="XAUUSD",
        kill_zone="london",
        config=cfg,
        bias="bullish",
        raw_data=raw_data,
    )
    gbp_decision = evaluate_pre_ai_vnext(
        symbol="GBPUSD",
        source_symbol="GBPUSD",
        kill_zone="london",
        config=cfg,
        bias="bullish",
        raw_data=raw_data,
    )

    assert gold_decision.action == "NARROW_AI_TO_ROUTE"
    assert gold_decision.decision == "FOLLOW"
    assert gold_decision.recommended_side == "SHORT"
    assert gold_decision.recommended_frameworks == ("ob_retest",)
    assert gold_decision.blocked_sides == ("LONG",)
    assert gold_decision.ai_role_context["runtime_rules"]["xau_asian_sweep_continuation"][
        "pool_type"
    ] == "asian_low"
    assert gbp_decision.action == "ALLOW_AI"
    assert gbp_decision.decision == "LEGACY"
    assert gbp_decision.recommended_side is None


def test_pre_ai_xau_asian_sweep_does_not_override_vnext_avoid_on_continuation_side(tmp_path):
    artifact = tmp_path / "xau_asian_sweep_vnext_avoid.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "xau-long-avoid",
                {"symbol": "XAUUSD", "route_session": "london", "side": "LONG", "framework": "ob_retest"},
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-6.0,
                stress=-2.0,
                n=30,
                proxy=-1.0,
                framework="ob_retest",
            )
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": True,
            "pre_ai_route_frameworks": ["ob_retest"],
            "pre_ai_xau_asian_sweep_continuation_enabled": True,
        }
    )
    raw_data = {"asian_sweep_continuation_side": "LONG", "asian_sweep_type": "run"}

    decision = evaluate_pre_ai_vnext(
        symbol="XAUUSD",
        source_symbol="XAUUSD",
        kill_zone="london",
        config=cfg,
        bias="no_bias",
        raw_data=raw_data,
    )

    assert decision.action == "SKIP_AI_AVOID_ONLY"
    assert decision.decision == "AVOID"
    assert decision.recommended_side is None
    assert set(decision.blocked_sides) == {"LONG", "SHORT"}
    assert decision.blocked_frameworks == ("ob_retest",)
    assert decision.ai_role_context["runtime_rules"]["xau_asian_sweep_continuation"][
        "continuation_side"
    ] == "LONG"


def test_pre_ai_router_builds_specialized_ai_role_context_from_would_route(tmp_path):
    artifact = tmp_path / "vnext_ai_role_context.jsonl"
    base_scope = {"symbol": "XAUUSD", "route_session": "london", "side": "LONG"}
    _write_jsonl(
        artifact,
        [
            _review_row(
                "ob-follow-ai-role",
                {**base_scope, "framework": "ob_retest", "route_family": "ob_retest"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=20,
                stress=8,
                n=200,
                proxy=3,
                framework="ob_retest",
                route_family="ob_retest",
                source_component="registry_scorer_module",
                evidence_family="ai_decision_architecture",
                source_name="ai_narrowing_policy",
            ),
            _review_row(
                "fvg-avoid-ai-role",
                {**base_scope, "framework": "fvg_fill", "route_family": "fvg_fill"},
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-2,
                stress=-2,
                n=20,
                proxy=-1,
                framework="fvg_fill",
                route_family="fvg_fill",
                source_component="shadow_source_guard",
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": False,
            "pre_ai_ai_role_context_enabled": True,
            "pre_ai_ai_role_context_uses_would_action": True,
            "pre_ai_evaluate_all_sides": True,
            "pre_ai_route_frameworks": ["ob_retest", "fvg_fill"],
            "conflict_resolution": "evidence_weighted",
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="XAUUSD",
        source_symbol="XAUUSD",
        kill_zone="london",
        config=cfg,
        bias="no_bias",
    )

    role_context = decision.ai_role_context
    prompt_context = format_vnext_ai_role_context_for_prompt(role_context)

    assert decision.action == "ALLOW_AI"
    assert decision.would_action == "NARROW_AI_TO_ROUTE"
    assert role_context["ai_role"] == "vnext_route_validator"
    assert role_context["selection_action"] == "NARROW_AI_TO_ROUTE"
    assert role_context["active_action"] == "ALLOW_AI"
    assert role_context["recommended_side"] == "LONG"
    assert role_context["recommended_frameworks"] == ["ob_retest"]
    assert role_context["blocked_frameworks"] == ["fvg_fill"]
    assert role_context["matched_rows"] == 2
    assert role_context["metric_sums"]["effective_n"] == 220.0
    assert role_context["source_artifact_path"] == (
        ".context/00_core/llm_specialization_research_backlog.md"
    )
    assert role_context["scope_guard"]["per_instrument_required"] is True
    assert role_context["scope_guard"]["symbol"] == "XAUUSD"
    assert role_context["scope_guard"]["source_symbol"] == "XAUUSD"
    assert role_context["scope_guard"]["symbol_family"] == "XAUUSD_GC_FAMILY"
    assert role_context["scope_guard"]["null_result_is_valid"] is True
    assert role_context["pressure_test"]["steps"] == [
        "critic_mode",
        "list_issues",
        "fix_or_reject",
        "state_what_was_fixed",
    ]
    assert "Role: vnext_route_validator" in prompt_context
    assert "frameworks=ob_retest" in prompt_context
    assert "source_components=registry_scorer_module=1" in prompt_context
    assert "Scope guard: per-instrument evidence only; symbol=XAUUSD" in prompt_context
    assert "Pressure test: critic_mode -> list_issues -> fix_or_reject" in prompt_context


def test_pre_ai_router_can_narrow_ai_to_mechanical_route_family_when_config_flipped(tmp_path):
    artifact = tmp_path / "vnext_route_family_only.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "moonshot-follow",
                {
                    "symbol": "GBPJPY",
                    "source_symbol": "GBPJPY",
                    "route_session": "ny_core",
                    "side": "LONG",
                    "route_family": "moonshot_mechanical",
                },
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=14.0,
                stress=3.0,
                n=20,
                proxy=1.0,
                route_family="moonshot_mechanical",
                source_name="moonshot_reduced_surface_candidates",
                evidence_family="expanded_market_reduced_surface",
            )
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": False,
            "pre_ai_route_families": ["moonshot_mechanical"],
            "pre_ai_route_timeframes": [""],
            "pre_ai_route_horizons": [""],
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="GBPJPY",
        source_symbol="GBPJPY",
        kill_zone="ny",
        config=cfg,
        bias="bullish",
    )

    assert decision.action == "NARROW_AI_TO_ROUTE"
    assert decision.would_action == "NARROW_AI_TO_ROUTE"
    assert decision.recommended_side == "LONG"
    assert decision.recommended_frameworks == ()
    assert decision.recommended_route_families == ("moonshot_mechanical",)
    assert decision.reason == "pre_ai_vnext_route_to_LONG_moonshot_mechanical"


def test_pre_ai_router_infers_framework_from_framework_route_family(tmp_path):
    artifact = tmp_path / "vnext_framework_route_family_only.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "fvg-family-follow",
                {
                    "symbol": "XAUUSD",
                    "source_symbol": "XAUUSD",
                    "route_session": "london_core",
                    "side": "LONG",
                    "route_family": "fvg_fill",
                },
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=11.0,
                stress=2.0,
                n=30,
                proxy=1.0,
                route_family="fvg_fill",
            )
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": False,
            "pre_ai_route_families": ["fvg_fill"],
            "pre_ai_route_timeframes": [""],
            "pre_ai_route_horizons": [""],
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="XAUUSD",
        source_symbol="XAUUSD",
        kill_zone="london",
        config=cfg,
        bias="bullish",
    )

    assert decision.action == "NARROW_AI_TO_ROUTE"
    assert decision.recommended_side == "LONG"
    assert decision.recommended_frameworks == ("fvg_fill",)
    assert decision.recommended_route_families == ("fvg_fill",)
    assert decision.reason == "pre_ai_vnext_route_to_LONG_fvg_fill"


def test_pre_ai_router_can_exclude_blocked_frameworks_without_single_side_route(tmp_path):
    artifact = tmp_path / "vnext_framework_exclusion.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "long-ob-follow",
                {"symbol": "XAUUSD", "route_session": "london", "side": "LONG", "framework": "ob_retest"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=10.0,
                stress=0.0,
                n=10,
                proxy=0.0,
                framework="ob_retest",
            ),
            _review_row(
                "long-fvg-avoid",
                {"symbol": "XAUUSD", "route_session": "london", "side": "LONG", "framework": "fvg_fill"},
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=0.0,
                stress=0.0,
                n=10,
                proxy=0.0,
                framework="fvg_fill",
            ),
            _review_row(
                "short-breaker-follow",
                {
                    "symbol": "XAUUSD",
                    "route_session": "london",
                    "side": "SHORT",
                    "framework": "breaker_re_entry",
                },
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=10.0,
                stress=0.0,
                n=10,
                proxy=0.0,
                framework="breaker_re_entry",
            ),
        ],
    )
    cfg = _config(artifact, apply=True)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": True,
            "pre_ai_route_frameworks": ["ob_retest", "fvg_fill", "breaker_re_entry"],
            "pre_ai_framework_exclusion_candidates": [
                "ob_retest",
                "fvg_fill",
                "breaker_re_entry",
            ],
            "pre_ai_select_stronger_follow_side_enabled": True,
            "pre_ai_stronger_follow_dominance_ratio": 2.0,
            "conflict_resolution": "evidence_weighted",
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="XAUUSD",
        source_symbol="XAUUSD",
        kill_zone="london",
        config=cfg,
        bias="bullish",
    )

    assert decision.action == "NARROW_AI_EXCLUDE_FRAMEWORKS"
    assert decision.would_action == "NARROW_AI_EXCLUDE_FRAMEWORKS"
    assert decision.recommended_side is None
    assert decision.recommended_frameworks == ("ob_retest", "breaker_re_entry")
    assert decision.blocked_frameworks == ("fvg_fill",)
    assert decision.reason == "pre_ai_vnext_exclude_frameworks_fvg_fill"


def test_pre_ai_router_selects_dominant_follow_side_from_all_side_evidence(tmp_path):
    artifact = tmp_path / "vnext_review.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "long-follow",
                {"symbol": "XAUUSD", "route_session": "london", "side": "LONG", "framework": "ob_retest"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=30,
                stress=8,
                n=200,
                proxy=4,
                framework="ob_retest",
            ),
            _review_row(
                "short-follow",
                {"symbol": "XAUUSD", "route_session": "london", "side": "SHORT", "framework": "fvg_fill"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=2,
                stress=0.5,
                n=50,
                proxy=0.2,
                framework="fvg_fill",
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": True,
            "pre_ai_route_frameworks": ["ob_retest", "fvg_fill"],
            "pre_ai_select_stronger_follow_side_enabled": True,
            "pre_ai_stronger_follow_dominance_ratio": 2.0,
            "pre_ai_stronger_follow_min_abs_pressure": 1.0,
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="XAUUSD",
        source_symbol="XAUUSD",
        kill_zone="london",
        config=cfg,
        bias="no_bias",
    )

    assert decision.action == "NARROW_AI_TO_ROUTE"
    assert decision.would_action == "NARROW_AI_TO_ROUTE"
    assert decision.recommended_side == "LONG"
    assert decision.recommended_frameworks == ("ob_retest",)
    assert decision.blocked_sides == ()
    assert [side_decision.decision for side_decision in decision.side_decisions] == [
        "FOLLOW",
        "FOLLOW",
    ]


def test_pre_ai_router_converts_ai_narrowing_policy_rows_to_follow_route(tmp_path):
    artifact = tmp_path / "vnext_ai_policy.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "vnext_matrix_row_id": "ai-policy-ready",
                "source_name": "ai_narrowing_policy",
                "evidence_family": "ai_decision_architecture",
                "ai_narrowing_policy_status": (
                    "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY"
                ),
                "symbol": "USDJPY",
                "source_symbol": "USDJPY",
                "route_session": "london_core",
                "side": "LONG",
                "market_timeframe": "D1",
                "horizon_id": "h16",
                "source_component": "shadow_source_guard",
                "source_row_id": "MAIN-ORCH48-AI-NARROWING-POLICY-00000001",
            },
            _review_row(
                "more-specific-follow-row",
                {
                    "symbol": "USDJPY",
                    "source_symbol": "USDJPY",
                    "route_session": "london_core",
                    "side": "LONG",
                    "market_timeframe": "D1",
                    "horizon_id": "h16",
                    "source_component": "shadow_source_guard",
                    "framework": "ob_retest",
                },
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=4,
                stress=2,
                n=50,
                source_component="shadow_source_guard",
                framework="ob_retest",
            ),
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": True,
            "pre_ai_route_timeframes": ["D1"],
            "pre_ai_route_horizons": ["h16"],
            "pre_ai_route_frameworks": ["ob_retest"],
            "pre_ai_route_source_components": ["shadow_source_guard"],
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="USDJPY",
        source_symbol="USDJPY",
        kill_zone="london",
        config=cfg,
        bias="bearish",
    )

    assert decision.action == "NARROW_AI_TO_ROUTE"
    assert decision.recommended_side == "LONG"
    assert decision.recommended_frameworks == ("ob_retest",)
    assert decision.decision == "FOLLOW"
    assert decision.side_decisions[0].evidence["decision_counts"] == {"FOLLOW": 2}
    assert decision.side_decisions[0].evidence["source_name_counts"]["ai_narrowing_policy"] == 1
    assert decision.side_decisions[0].evidence["rows"][0]["decision"] == "FOLLOW"
    assert decision.side_decisions[0].evidence["row_detail_count"] == 2


def test_pre_ai_router_does_not_follow_ai_policy_capacity_blocklist_scope(tmp_path):
    artifact = tmp_path / "vnext_ai_policy.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "vnext_matrix_row_id": "ai-policy-blocklist",
                "source_name": "ai_narrowing_policy",
                "evidence_family": "ai_decision_architecture",
                "ai_narrowing_policy_status": (
                    "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY_WITH_CAPACITY_BLOCKLIST"
                ),
                "symbol": "XAUUSD",
                "source_symbol": "XAUUSD",
                "route_session": "ny_core",
                "side": "LONG",
                "market_timeframe": "H1",
                "horizon_id": "h16",
                "source_component": "shadow_source_guard",
                "source_row_id": "MAIN-ORCH48-AI-NARROWING-POLICY-00000020",
            }
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": True,
            "pre_ai_route_timeframes": ["H1"],
            "pre_ai_route_horizons": ["h16"],
            "pre_ai_route_source_components": ["shadow_source_guard"],
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="XAUUSD",
        source_symbol="XAUUSD",
        kill_zone="ny",
        config=cfg,
        bias="bearish",
    )

    assert decision.action == "ALLOW_AI"
    assert decision.recommended_side is None
    assert decision.decision == "MIXED"
    assert decision.side_decisions[0].evidence["decision_counts"] == {"MIXED": 1}
    assert decision.side_decisions[0].evidence["rows"][0]["decision"] == "MIXED"


def test_pre_ai_router_loads_capacity_blocklist_artifact_when_active(tmp_path):
    policy_artifact = tmp_path / "vnext_ai_policy.jsonl"
    blocklist_artifact = tmp_path / "vnext_ai_capacity_blocklist.jsonl"
    _write_jsonl(
        policy_artifact,
        [
            {
                "ai_narrowing_policy_row_id": "POLICY-BLOCKLIST-READY",
                "source_name": "ai_narrowing_policy",
                "evidence_family": "ai_decision_architecture",
                "ai_narrowing_policy_status": (
                    "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY_WITH_CAPACITY_BLOCKLIST"
                ),
                "symbol": "XAUUSD",
                "source_symbol": "XAUUSD",
                "route_session": "ny_core",
                "selected_side": "LONG",
                "market_timeframe": "H1",
                "horizon_id": "h16",
                "source_component": "shadow_source_guard",
            }
        ],
    )
    _write_jsonl(
        blocklist_artifact,
        [
            {
                "ai_narrowing_capacity_blocklist_row_id": "BLOCKLIST-READY",
                "ai_narrowing_capacity_blocklist_status": (
                    "AI_NARROWING_CAPACITY_BLOCKLIST_REQUIRED_FOR_PRE_AI_SELECTOR_REVIEW"
                ),
                "symbol": "XAUUSD",
                "source_symbol": "XAUUSD",
                "route_session": "ny_core",
                "selected_side": "LONG",
                "market_timeframe": "H1",
                "horizon_id": "h16",
                "source_component": "shadow_source_guard",
                "capacity_blocked_candidate_row_ids": ["CANDIDATE-BLOCKED"],
                "implementation_ready_candidate_row_ids": [
                    "CANDIDATE-READY-1",
                    "CANDIDATE-READY-2",
                    "CANDIDATE-READY-3",
                    "CANDIDATE-READY-4",
                ],
            }
        ],
    )
    cfg = _config(policy_artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_apply_to_ai_call": True,
            "pre_ai_evaluate_all_sides": True,
            "pre_ai_route_timeframes": ["H1"],
            "pre_ai_route_horizons": ["h16"],
            "pre_ai_route_families": ["mechanical_ai_selector"],
            "pre_ai_route_source_components": ["shadow_source_guard"],
            "pre_ai_ai_narrowing_load_capacity_blocklist_artifact": True,
            "pre_ai_ai_narrowing_capacity_blocklist_artifact_path": str(blocklist_artifact),
            "pre_ai_ai_narrowing_allow_blocklist_required_scopes": True,
            "pre_ai_ai_narrowing_capacity_blocklist_active": True,
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="XAUUSD",
        source_symbol="XAUUSD",
        kill_zone="ny",
        config=cfg,
        bias="bearish",
    )

    long_side = next(
        side_decision
        for side_decision in decision.side_decisions
        if side_decision.event.get("side") == "LONG"
    )
    assert decision.action == "NARROW_AI_TO_ROUTE"
    assert decision.recommended_side == "LONG"
    assert decision.recommended_route_families == ("mechanical_ai_selector",)
    assert long_side.evidence["decision_counts"] == {"FOLLOW": 2}
    assert long_side.evidence["metrics"]["effective_n"]["sum"] == 4.0
    assert long_side.evidence["source_name_counts"]["ai_narrowing_policy"] == 1
    assert long_side.evidence["source_name_counts"]["ai_narrowing_capacity_blocklist"] == 1
    assert str(blocklist_artifact) in long_side.artifact_paths
    assert {row["row_id"] for row in long_side.evidence["rows"]} == {
        "POLICY-BLOCKLIST-READY",
        "BLOCKLIST-READY",
    }


def test_runtime_uses_implementation_action_follow_and_avoid_semantics(tmp_path):
    artifact = tmp_path / "vnext_implementation_actions.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "vnext_matrix_row_id": "impl-follow",
                "source_name": "numeric_router_scorer_surface",
                "evidence_family": "numeric_router_system_recommendations",
                "implementation_action": "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS",
                "symbol": "XAUUSD",
                "source_symbol": "XAUUSD",
                "route_session": "ny_core",
                "side": "LONG",
                "source_component": "registry_scorer_module",
            },
            {
                "vnext_matrix_row_id": "impl-avoid",
                "source_name": "numeric_router_avoid_score",
                "evidence_family": "numeric_router_system_recommendations",
                "implementation_action": "IMPLEMENT_AVOID_INVERSE_OR_FAILURE_FILTER_SCOPE",
                "symbol": "XAUUSD",
                "source_symbol": "XAUUSD",
                "route_session": "ny_core",
                "side": "SHORT",
                "source_component": "nofill_far_miss_avoid",
            },
            {
                "vnext_matrix_row_id": "impl-source-repair",
                "source_name": "numeric_router_source_repair_proof",
                "evidence_family": "numeric_router_source_repair",
                "implementation_action": "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R",
                "symbol": "XAUUSD",
                "source_symbol": "XAUUSD",
                "route_session": "ny_core",
                "side": "LONG",
                "source_component": "shadow_source_guard",
            },
        ],
    )
    cfg = _config(artifact)

    follow = evaluate_vnext_event(
        {
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "kill_zone": "ny",
            "side": "LONG",
            "source_component": "registry_scorer_module",
        },
        cfg,
    )
    avoid = evaluate_vnext_event(
        {
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "kill_zone": "ny",
            "side": "SHORT",
            "source_component": "nofill_far_miss_avoid",
        },
        cfg,
    )
    repair = evaluate_vnext_event(
        {
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "kill_zone": "ny",
            "side": "LONG",
            "source_component": "shadow_source_guard",
        },
        cfg,
    )

    assert follow.decision == "FOLLOW"
    assert follow.evidence["rows"][0]["decision"] == "FOLLOW"
    assert follow.evidence["implementation_action_counts"] == {
        "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS": 1
    }
    assert avoid.decision == "AVOID"
    assert avoid.evidence["rows"][0]["decision"] == "AVOID"
    assert avoid.evidence["implementation_action_counts"] == {
        "IMPLEMENT_AVOID_INVERSE_OR_FAILURE_FILTER_SCOPE": 1
    }
    assert repair.decision == "MIXED"
    assert repair.evidence["rows"][0]["decision"] == "MIXED"
    assert repair.evidence["implementation_action_counts"] == {
        "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R": 1
    }


def test_runtime_artifact_loader_searches_configured_local_heavy_data_roots(tmp_path):
    external_root = tmp_path / "absolute_main_repo_copy"
    relative_artifact = "missing_artifacts/vnext_external_only.jsonl"
    external_artifact = external_root / relative_artifact
    external_artifact.parent.mkdir(parents=True)
    _write_jsonl(
        external_artifact,
        [
            _review_row(
                "external-follow-row",
                {"symbol": "GBPJPY", "route_session": "tokyo", "side": "LONG"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=4.5,
                stress=3.0,
                n=12,
                source_component="registry_scorer_module",
            )
        ],
    )
    cfg = {
        "gtos_vnext_runtime": {
            "enabled": True,
            "apply_to_execution": False,
            "artifact_paths": [relative_artifact],
            "local_heavy_data_search_enabled": True,
            "local_heavy_data_search_roots": [str(external_root)],
        },
        "model_a": {"entry_timeframe": "M15"},
    }

    decision = evaluate_vnext_event(
        {"symbol": "GBPJPY", "kill_zone": "tokyo", "direction": "LONG"},
        cfg,
    )

    assert decision.decision == "FOLLOW"
    assert decision.artifact_paths == (str(external_artifact),)
    assert decision.evidence["rows"][0]["loaded_from"] == str(external_artifact)
    assert decision.evidence["metrics"]["effective_n"]["sum"] == 12


def test_cp281_result_table_rows_are_runtime_matchable_without_new_artifact_layer(tmp_path):
    artifact = tmp_path / "cp281_result_table.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "row_key": "cp281-nas100-ny-h32-short",
                "row_type": "cp281_rule_replay_result_table",
                "result_table_group": "follow_vs_avoid_scope",
                "result_table_dimensions": {
                    "matched_action_class": "avoid_filter",
                    "symbol_family": "NAS100_NQ_FAMILY",
                    "market_timeframe": "M1",
                    "route_session": "ny_core",
                    "horizon_id": "h32",
                    "side": "SHORT",
                },
                "rule_replay_match_rows": 9,
                "unique_matched_rule_count": 3,
                "unique_replay_event_count": 3,
                "action_class_counts": {"avoid_filter": 9},
                "main_system_surface_counts": {"cp281_default_off_avoid_filter_registry": 9},
                "cost_adjusted_simulated_r": _metric(-2.865400713, 9),
                "stress_simulated_r": _metric(-30.085534719, 9),
                "effective_n": _metric(126.0, 9),
            }
        ],
    )
    cfg = _config(artifact, apply=True)
    cfg["gtos_vnext_runtime"].update(
        {
            "artifact_paths": [str(artifact)],
            "post_l2_evaluate_route_variants": True,
            "post_l2_prune_route_variants_to_artifact_scopes": True,
            "post_l2_match_artifact_scopes_directly": True,
            "post_l2_route_timeframes": ["M1"],
            "post_l2_route_horizons": ["h32"],
            "post_l2_route_families": ["cp281_native_rule"],
            "post_l2_route_source_components": [""],
            "risk_adjustment_enabled": True,
            "min_loaded_evidence_rows": 0,
        }
    )

    decision = evaluate_vnext_route_event(
        {
            "symbol": "NAS100",
            "source_symbol": "NAS100",
            "kill_zone": "ny",
            "direction": "SHORT",
            "timeframe": "M1",
        },
        cfg,
    )

    assert decision.decision == "AVOID"
    assert decision.reason == "matched_vnext_route_scope"
    assert decision.evidence["source_name_counts"] == {"cp281_rule_replay_result_table": 1}
    assert decision.evidence["evidence_family_counts"] == {"cp281_native_rule_replay": 1}
    assert decision.evidence["route_family_counts"] == {"cp281_native_rule": 1}
    assert decision.evidence["action_class_decision_counts"] == {
        "avoid_filter": {"AVOID": 1}
    }
    assert decision.evidence["matched_row_ids"] == ["cp281-nas100-ny-h32-short"]
    assert decision.evidence["metrics"]["cost_adjusted_simulated_r"]["sum"] == -2.865400713
    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config=cfg,
    )
    assert adjustment.would_multiplier == 0.0
    assert adjustment.reason == "vnext_risk_action_class_avoid_veto"


def test_cp281_branch_decision_rows_are_runtime_matchable_without_new_artifact_layer(tmp_path):
    artifact = tmp_path / "cp281_branch_decisions.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "row_key": "cp281-branch-us30-london-m5-short",
                "row_type": "cp281_ready_runtime_branch_decision",
                "action_class": "avoid_filter",
                "aggregate_scope": {
                    "action_class": "avoid_filter",
                    "symbol_family": "US30_YM_FAMILY",
                    "market_timeframe": "M5",
                    "route_session": "london_core",
                    "horizon_id": "h16",
                    "side": "SHORT",
                },
                "branch_decision_action": "DEFAULT_OFF_CP281_BRANCH_AVOID_FILTER_READY",
                "main_surface_action": "REGISTER_DEFAULT_OFF_CP281_AVOID_FILTER_RULE",
                "main_system_surface": "cp281_default_off_avoid_filter_registry",
                "member_rule_count": 6,
                "member_rule_ids": [
                    "FROZEN-MOONSHOT-READY-ACTION-RUNTIME-RULE-0000101",
                    "FROZEN-MOONSHOT-READY-ACTION-RUNTIME-RULE-0000102",
                ],
                "cost_adjusted_simulated_r": _metric(-2.715178569, 6),
                "stress_simulated_r": _metric(-2.715178569, 6),
                "effective_n": _metric(72.0, 6),
            }
        ],
    )
    cfg = _config(artifact, apply=True)
    cfg["gtos_vnext_runtime"].update(
        {
            "artifact_paths": [str(artifact)],
            "post_l2_evaluate_route_variants": True,
            "post_l2_prune_route_variants_to_artifact_scopes": True,
            "post_l2_match_artifact_scopes_directly": True,
            "post_l2_route_timeframes": ["M5"],
            "post_l2_route_horizons": ["h16"],
            "post_l2_route_families": ["cp281_native_rule"],
            "post_l2_route_source_components": [""],
            "risk_adjustment_enabled": True,
            "min_loaded_evidence_rows": 0,
        }
    )

    decision = evaluate_vnext_route_event(
        {
            "symbol": "US30.cash",
            "source_symbol": "US30.cash",
            "kill_zone": "london",
            "direction": "SHORT",
            "timeframe": "M5",
        },
        cfg,
    )

    assert decision.decision == "AVOID"
    assert decision.reason == "matched_vnext_route_scope"
    assert decision.evidence["source_name_counts"] == {"cp281_branch_decisions": 1}
    assert decision.evidence["evidence_family_counts"] == {
        "cp281_ready_runtime_branch_decision": 1
    }
    assert decision.evidence["route_family_counts"] == {"cp281_native_rule": 1}
    assert decision.evidence["action_class_decision_counts"] == {
        "avoid_filter": {"AVOID": 1}
    }
    assert decision.evidence["system_surface_counts"] == {
        "cp281_default_off_avoid_filter_registry": 1
    }
    assert decision.evidence["matched_row_ids"] == [
        "cp281-branch-us30-london-m5-short"
    ]
    assert decision.evidence["rows"][0]["source_row_id"] == (
        "cp281-branch-us30-london-m5-short"
    )
    assert decision.evidence["metrics"]["cost_adjusted_simulated_r"]["sum"] == -2.715178569
    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config=cfg,
    )
    assert adjustment.would_multiplier == 0.0
    assert adjustment.reason == "vnext_risk_action_class_avoid_veto"


def test_cp281_aggregate_rows_are_runtime_matchable_without_new_artifact_layer(tmp_path):
    artifact = tmp_path / "cp281_aggregate.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "row_key": "cp281-aggregate-gbpusd-london-m1-long",
                "row_type": "cp281_ready_runtime_aggregate_to_main_system_surface",
                "cp281_aggregate_row_id": "FROZEN-MOONSHOT-READY-ACTION-RUNTIME-AGG-900001",
                "action_class": "avoid_filter",
                "aggregate_scope": {
                    "action_class": "avoid_filter",
                    "symbol_family": "GBPUSD_6B_FAMILY",
                    "market_timeframe": "M1",
                    "route_session": "london_core",
                    "horizon_id": "h16",
                    "side": "LONG",
                },
                "main_surface_action": "REGISTER_DEFAULT_OFF_CP281_AVOID_FILTER_RULE",
                "main_system_surface": "cp281_default_off_avoid_filter_registry",
                "rule_count": 3,
                "source_row_count": 42,
                "average_cost_adjusted_simulated_r": -0.106067308,
                "average_stress_simulated_r": -0.106067308,
                "effective_n_sum": 42.0,
                "source_ownership": {
                    "source_aggregate_artifact": "moonshot/aggregate.jsonl",
                    "source_aggregate_artifact_sha256": "a" * 64,
                    "source_aggregate_line_no": 8,
                },
            }
        ],
    )
    cfg = _config(artifact, apply=True)
    cfg["gtos_vnext_runtime"].update(
        {
            "artifact_paths": [str(artifact)],
            "post_l2_evaluate_route_variants": True,
            "post_l2_prune_route_variants_to_artifact_scopes": True,
            "post_l2_match_artifact_scopes_directly": True,
            "post_l2_route_timeframes": ["M1"],
            "post_l2_route_horizons": ["h16"],
            "post_l2_route_families": ["cp281_native_rule"],
            "post_l2_route_source_components": [""],
            "risk_adjustment_enabled": True,
            "min_loaded_evidence_rows": 0,
        }
    )

    decision = evaluate_vnext_route_event(
        {
            "symbol": "GBPUSD",
            "source_symbol": "GBPUSD",
            "kill_zone": "london",
            "direction": "LONG",
            "timeframe": "M1",
        },
        cfg,
    )

    assert decision.decision == "AVOID"
    assert decision.evidence["source_name_counts"] == {"cp281_ready_runtime_aggregates": 1}
    assert decision.evidence["evidence_family_counts"] == {"cp281_ready_runtime_aggregate": 1}
    assert decision.evidence["route_family_counts"] == {"cp281_native_rule": 1}
    assert decision.evidence["matched_row_ids"] == ["cp281-aggregate-gbpusd-london-m1-long"]
    row = decision.evidence["rows"][0]
    assert row["cp281_aggregate_row_id"] == "FROZEN-MOONSHOT-READY-ACTION-RUNTIME-AGG-900001"
    assert row["cp281_aggregate_source_row_count"] == 42
    assert row["cp281_aggregate_provenance"]["source_row_count"] == 42
    assert row["declared_origin_artifact"] == "moonshot/aggregate.jsonl"
    assert row["declared_origin_line_no"] == 8
    assert decision.evidence["metrics"]["cost_adjusted_simulated_r"]["sum"] == -0.106067308
    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config=cfg,
    )
    assert adjustment.would_multiplier == 0.0
    assert adjustment.reason == "vnext_risk_action_class_avoid_veto"


def test_cp281_aggregate_provenance_enriches_branch_rows_without_duplicate_votes(tmp_path):
    aggregate_artifact = tmp_path / "cp281_aggregate.jsonl"
    branch_artifact = tmp_path / "cp281_branch_decisions.jsonl"
    aggregate_id = "FROZEN-MOONSHOT-READY-ACTION-RUNTIME-AGG-900002"
    scope = {
        "action_class": "avoid_filter",
        "symbol_family": "NAS100_NQ_FAMILY",
        "market_timeframe": "M1",
        "route_session": "london_core",
        "horizon_id": "h4",
        "side": "SHORT",
    }
    _write_jsonl(
        aggregate_artifact,
        [
            {
                "row_key": "cp281-aggregate-nas100-london-m1-short",
                "row_type": "cp281_ready_runtime_aggregate_to_main_system_surface",
                "cp281_aggregate_row_id": aggregate_id,
                "action_class": "avoid_filter",
                "aggregate_scope": scope,
                "main_surface_action": "REGISTER_DEFAULT_OFF_CP281_AVOID_FILTER_RULE",
                "main_system_surface": "cp281_default_off_avoid_filter_registry",
                "rule_count": 6,
                "source_row_count": 72,
                "average_cost_adjusted_simulated_r": -0.078946496,
                "average_stress_simulated_r": -3.103405831,
                "effective_n_sum": 72.0,
                "source_ownership": {
                    "source_aggregate_artifact": "moonshot/aggregate.jsonl",
                    "source_aggregate_artifact_sha256": "b" * 64,
                    "source_aggregate_line_no": 11,
                },
            }
        ],
    )
    _write_jsonl(
        branch_artifact,
        [
            {
                "row_key": "cp281-branch-nas100-london-m1-short",
                "row_type": "cp281_ready_runtime_branch_decision",
                "cp281_aggregate_row_id": aggregate_id,
                "action_class": "avoid_filter",
                "aggregate_scope": scope,
                "branch_decision_action": "DEFAULT_OFF_CP281_BRANCH_AVOID_FILTER_READY",
                "main_surface_action": "REGISTER_DEFAULT_OFF_CP281_AVOID_FILTER_RULE",
                "main_system_surface": "cp281_default_off_avoid_filter_registry",
                "member_rule_count": 6,
                "member_rule_ids": [
                    "FROZEN-MOONSHOT-READY-ACTION-RUNTIME-RULE-900101",
                    "FROZEN-MOONSHOT-READY-ACTION-RUNTIME-RULE-900102",
                ],
                "cost_adjusted_simulated_r": _metric(-0.473678976, 6),
                "stress_simulated_r": _metric(-18.620434986, 6),
                "effective_n": _metric(72.0, 6),
            }
        ],
    )
    cfg = _config(branch_artifact, apply=True)
    cfg["gtos_vnext_runtime"].update(
        {
            "artifact_paths": [str(branch_artifact), str(aggregate_artifact)],
            "post_l2_evaluate_route_variants": True,
            "post_l2_prune_route_variants_to_artifact_scopes": True,
            "post_l2_match_artifact_scopes_directly": True,
            "post_l2_route_timeframes": ["M1"],
            "post_l2_route_horizons": ["h4"],
            "post_l2_route_families": ["cp281_native_rule"],
            "post_l2_route_source_components": [""],
            "min_loaded_evidence_rows": 0,
        }
    )

    index = load_vnext_evidence_index([branch_artifact, aggregate_artifact])
    assert index.rows_loaded_by_path[str(aggregate_artifact)] == 1
    assert sum(1 for row in index.rows if row.get("cp281_aggregate_row_id") == aggregate_id) == 1

    decision = evaluate_vnext_route_event(
        {
            "symbol": "NQM26-CME",
            "source_symbol": "NQM26-CME",
            "kill_zone": "london",
            "direction": "SHORT",
            "timeframe": "M1",
        },
        cfg,
        artifact_index=index,
    )

    assert decision.decision == "AVOID"
    assert decision.evidence["source_name_counts"] == {"cp281_branch_decisions": 1}
    assert decision.evidence["evidence_family_counts"] == {
        "cp281_ready_runtime_branch_decision": 1
    }
    row = decision.evidence["rows"][0]
    assert row["source_row_id"] == "cp281-branch-nas100-london-m1-short"
    assert row["cp281_aggregate_source_row_count"] == 72
    assert row["cp281_aggregate_loaded_from"] == str(aggregate_artifact)
    assert row["cp281_aggregate_provenance"]["source_ownership"]["source_aggregate_line_no"] == 11


def test_cp281_ready_runtime_rule_rows_are_runtime_matchable_without_new_artifact_layer(tmp_path):
    artifact = tmp_path / "cp281_ready_runtime_rules.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "row_key": "cp281-rule-us30-london-m1-short",
                "row_type": "cp281_ready_runtime_rule_to_main_system_surface",
                "cp281_rule_row_id": "FROZEN-MOONSHOT-READY-ACTION-RUNTIME-RULE-900001",
                "action_class": "avoid_filter",
                "implementation_decision": "IMPLEMENT_DEFAULT_OFF_AVOID_FILTER_RULE",
                "main_surface_action": "REGISTER_DEFAULT_OFF_CP281_AVOID_FILTER_RULE",
                "main_system_surface": "cp281_default_off_avoid_filter_registry",
                "symbol": "US30_cash",
                "source_symbol": "US30_YM",
                "symbol_family": "US30_YM_FAMILY",
                "market_timeframe": "M1",
                "route_session": "london_core",
                "horizon_id": "h4",
                "side": "SHORT",
                "match_scope": {
                    "symbol": "US30_cash",
                    "source_symbol": "US30_YM",
                    "symbol_family": "US30_YM_FAMILY",
                    "market_timeframe": "M1",
                    "route_session": "london_core",
                    "horizon_id": "h4",
                    "side": "SHORT",
                    "source_path_sha256": "source-path-hash-us30-m1",
                    "source_file_sha256": "source-file-hash-us30-m1",
                },
                "source_ownership": {
                    "source_path": "data/historical/US30_M1.csv",
                    "source_rule_artifact": "research/frozen_ready_action_runtime_rule_ledger.jsonl",
                    "source_rule_line_no": 17,
                },
                "cost_adjusted_simulated_r": -0.079718205,
                "stress_simulated_r": -0.079718205,
                "effective_n": 12.0,
            }
        ],
    )
    cfg = _config(artifact, apply=True)
    cfg["gtos_vnext_runtime"].update(
        {
            "artifact_paths": [str(artifact)],
            "post_l2_evaluate_route_variants": True,
            "post_l2_prune_route_variants_to_artifact_scopes": True,
            "post_l2_match_artifact_scopes_directly": True,
            "post_l2_route_timeframes": ["M1"],
            "post_l2_route_horizons": ["h4"],
            "post_l2_route_families": ["cp281_native_rule"],
            "post_l2_route_source_components": [""],
            "risk_adjustment_enabled": True,
            "min_loaded_evidence_rows": 0,
        }
    )

    decision = evaluate_vnext_route_event(
        {
            "symbol": "US30.cash",
            "source_symbol": "US30.cash",
            "kill_zone": "london",
            "direction": "SHORT",
            "timeframe": "M1",
            "source_path_sha256": "source-path-hash-us30-m1",
            "source_file_sha256": "source-file-hash-us30-m1",
        },
        cfg,
    )

    assert decision.decision == "AVOID"
    assert decision.evidence["source_name_counts"] == {"cp281_ready_runtime_rules": 1}
    assert decision.evidence["evidence_family_counts"] == {"cp281_ready_runtime_rule": 1}
    assert decision.evidence["route_family_counts"] == {"cp281_native_rule": 1}
    assert decision.evidence["source_row_ids"] == [
        "FROZEN-MOONSHOT-READY-ACTION-RUNTIME-RULE-900001"
    ]
    assert decision.evidence["rows"][0]["source_path_sha256"] == "source-path-hash-us30-m1"
    assert decision.evidence["rows"][0]["source_file_sha256"] == "source-file-hash-us30-m1"
    assert decision.evidence["rows"][0]["declared_origin_line_no"] == 17
    assert decision.evidence["metrics"]["cost_adjusted_simulated_r"]["sum"] == -0.079718205
    assert decision.evidence["metrics"]["effective_n"]["sum"] == 12.0
    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config=cfg,
    )
    assert adjustment.would_multiplier == 0.0
    assert adjustment.reason == "vnext_risk_action_class_avoid_veto"

    direct_without_hashes = evaluate_vnext_event(
        {
            "symbol": "US30.cash",
            "source_symbol": "US30.cash",
            "kill_zone": "london",
            "direction": "SHORT",
            "timeframe": "M1",
            "route_family": "cp281_native_rule",
        },
        cfg,
    )
    assert direct_without_hashes.decision == "LEGACY"
    assert direct_without_hashes.evidence.get("matched_rows", 0) == 0


def test_cp281_rule_replay_events_attach_to_ready_rules_without_duplicate_votes(tmp_path):
    rule_artifact = tmp_path / "cp281_ready_runtime_rules.jsonl"
    event_artifact = tmp_path / "cp281_rule_replay_events.jsonl"
    rule_row = {
        "row_key": "cp281-rule-us30-london-m1-short",
        "row_type": "cp281_ready_runtime_rule_to_main_system_surface",
        "cp281_rule_row_id": "FROZEN-MOONSHOT-READY-ACTION-RUNTIME-RULE-900001",
        "action_class": "avoid_filter",
        "implementation_decision": "IMPLEMENT_DEFAULT_OFF_AVOID_FILTER_RULE",
        "main_surface_action": "REGISTER_DEFAULT_OFF_CP281_AVOID_FILTER_RULE",
        "main_system_surface": "cp281_default_off_avoid_filter_registry",
        "match_scope": {
            "symbol": "US30_cash",
            "source_symbol": "US30_YM",
            "symbol_family": "US30_YM_FAMILY",
            "market_timeframe": "M1",
            "route_session": "london_core",
            "horizon_id": "h4",
            "side": "SHORT",
            "source_path_sha256": "source-path-hash-us30-m1",
            "source_file_sha256": "source-file-hash-us30-m1",
        },
        "cost_adjusted_simulated_r": -0.079718205,
        "stress_simulated_r": -0.079718205,
        "effective_n": 12.0,
    }
    event_payload = {
        "symbol": "US30_cash",
        "source_symbol": "US30_YM",
        "symbol_family": "US30_YM_FAMILY",
        "market_timeframe": "M1",
        "timeframe": "M1",
        "route_session": "london_core",
        "session": "london_core",
        "horizon_id": "h4",
        "side": "SHORT",
        "selected_side": "SHORT",
        "source_path_sha256": "source-path-hash-us30-m1",
        "source_file_sha256": "source-file-hash-us30-m1",
    }
    event_row = {
        "row_key": "cp281-event-us30-london-m1-short",
        "row_type": "cp281_rule_replay_event",
        "cp281_rule_replay_event_id": "CP281-RULE-REPLAY-EVENT-900001",
        "source_cp281_rule_row_id": "FROZEN-MOONSHOT-READY-ACTION-RUNTIME-RULE-900001",
        "event_materialization_status": "CP281_RULE_REPLAY_EVENT_MATERIALIZED_FROM_READY_RUNTIME_MAPPING",
        "event_payload": event_payload,
        "event_required_fields": [
            "symbol_family",
            "symbol",
            "source_symbol",
            "market_timeframe",
            "route_session",
            "horizon_id",
            "side",
            "source_path_sha256",
            "source_file_sha256",
        ],
        "event_required_field_count": 9,
        "source_mapping_row_key": "mapping-row-key-900001",
        "source_operation": "SOURCE_ARTIFACT_RULE_REPLAY_EVENT_PRODUCTION",
        "gross_simulated_r": -0.079718205,
        "cost_adjusted_simulated_r": -0.079718205,
        "stress_simulated_r": -0.079718205,
        "effective_n": 12.0,
    }
    _write_jsonl(rule_artifact, [rule_row])
    _write_jsonl(event_artifact, [event_row])
    index = load_vnext_evidence_index([rule_artifact, event_artifact])
    cfg = _config(rule_artifact, apply=True)
    cfg["gtos_vnext_runtime"].update(
        {
            "artifact_paths": [str(rule_artifact), str(event_artifact)],
            "min_loaded_evidence_rows": 0,
        }
    )

    decision = evaluate_vnext_event(
        {**event_payload, "route_family": "cp281_native_rule"},
        cfg,
        artifact_index=index,
    )

    rows_loaded = {
        path.replace("\\", "/"): count
        for path, count in decision.evidence["runtime_index"]["rows_loaded_by_path"].items()
    }
    assert index.row_count == 1
    assert rows_loaded[str(rule_artifact).replace("\\", "/")] == 1
    assert rows_loaded[str(event_artifact).replace("\\", "/")] == 1
    assert decision.decision == "AVOID"
    assert decision.evidence["source_name_counts"] == {"cp281_ready_runtime_rules": 1}
    assert "cp281_rule_replay_event" not in decision.evidence["source_name_counts"]
    evidence_row = decision.evidence["rows"][0]
    assert evidence_row["cp281_rule_replay_event_id"] == "CP281-RULE-REPLAY-EVENT-900001"
    assert evidence_row["cp281_rule_replay_event_payload"] == event_payload
    assert evidence_row["cp281_rule_replay_event_required_field_count"] == 9
    assert evidence_row["cp281_rule_replay_event_count"] == 1
    assert evidence_row["cp281_rule_replay_event_provenance"][0]["source_mapping_row_key"] == (
        "mapping-row-key-900001"
    )


def test_runtime_fails_closed_when_full_evidence_denominator_is_missing(tmp_path):
    artifact = tmp_path / "partial_vnext_review.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "partial-follow",
                {"symbol": "USDJPY", "source_symbol": "USDJPY", "route_session": "london", "side": "LONG"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=10,
                stress=4,
                n=10,
            )
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "min_loaded_evidence_rows": 2,
            "post_l2_evaluate_route_variants": True,
        }
    )

    decision = evaluate_vnext_route_event(
        {"symbol": "USDJPY", "source_symbol": "USDJPY", "kill_zone": "london", "direction": "LONG"},
        cfg,
    )

    assert decision.decision == "LEGACY"
    assert decision.matched is False
    assert decision.reason == "vnext_evidence_index_below_min_loaded_rows"
    assert decision.evidence["runtime_index"]["row_count"] == 1
    assert decision.evidence["runtime_index"]["min_loaded_evidence_rows"] == 2


def test_pre_ai_fails_closed_when_full_evidence_denominator_is_missing(tmp_path):
    artifact = tmp_path / "partial_vnext_review.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "partial-follow",
                {"symbol": "USDJPY", "source_symbol": "USDJPY", "route_session": "london", "side": "LONG"},
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=10,
                stress=4,
                n=10,
            )
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "pre_ai_enabled": True,
            "pre_ai_evaluate_all_sides": True,
            "min_loaded_evidence_rows": 2,
        }
    )

    decision = evaluate_pre_ai_vnext(
        symbol="USDJPY",
        source_symbol="USDJPY",
        kill_zone="london",
        config=cfg,
        bias="bullish",
    )

    assert decision.decision == "LEGACY"
    assert decision.action == "ALLOW_AI"
    assert decision.reason == "vnext_evidence_index_below_min_loaded_rows"
    assert decision.side_decisions == ()


def test_orchestrator_runtime_hook_attaches_vnext_evidence_to_trade_record(monkeypatch, caplog):
    caplog.set_level("INFO", logger="src.components.orchestrator")
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch.config = _config("unused.jsonl")
    orch._symbol = "GBPJPY"
    orch._mt5_symbol = "GBPJPY"
    expected = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "GBPJPY", "route_session": "tokyo", "side": "LONG"},
        enabled=True,
        apply_to_execution=False,
        matched=True,
        reason="matched_vnext_scope",
        evidence={
            "matched_rows": 1,
            "metrics": {
                "cost_adjusted_simulated_r": {"sum": 33.8},
                "proxy_score": {"sum": 4.2},
                "stress_simulated_r": {"sum": 33.7},
                "effective_n": {"sum": 325609},
            },
        },
        artifact_paths=("unused.jsonl",),
    )

    def fake_evaluate_candidate_vnext(**kwargs):
        assert kwargs["symbol"] == "GBPJPY"
        assert kwargs["source_symbol"] == "GBPJPY"
        assert kwargs["kill_zone"] == "tokyo"
        return expected

    monkeypatch.setattr(orchestrator_mod, "evaluate_candidate_vnext", fake_evaluate_candidate_vnext)
    record = {"decision_pipeline": {}, "instrumentation": {}}

    result = orch._evaluate_gtos_vnext_runtime(
        analysis=SimpleNamespace(trade_parameters=SimpleNamespace(direction="LONG")),
        raw_data={},
        kill_zone="tokyo",
        record=record,
    )

    assert result is expected
    attached = record["decision_pipeline"]["gtos_vnext_runtime"]
    assert attached["decision"] == "FOLLOW"
    assert attached["evidence"]["metrics"]["effective_n"]["sum"] == 325609
    assert record["instrumentation"]["gtos_vnext_decision"] == "FOLLOW"
    assert "GTOS_VNEXT_RUNTIME decision=FOLLOW" in caplog.text


def test_orchestrator_pre_ai_hook_records_route_decision(monkeypatch, tmp_path, caplog):
    caplog.set_level("INFO", logger="src.components.orchestrator")
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch.config = {
        "ai_supervisor": {
            "decision_log_path": str(tmp_path / "ai_supervisor_decisions.jsonl"),
        },
        "gtos_vnext_runtime": {
            "enabled": True,
            "pre_ai_enabled": True,
            "pre_ai_apply_to_ai_call": False,
            "decision_log_path": str(tmp_path / "vnext_decisions.jsonl"),
        }
    }
    orch._symbol = "NAS100"
    orch._mt5_symbol = "NAS100"
    expected = GTOSVNextPreAIRoutingDecision(
        action="ALLOW_AI",
        decision="AVOID",
        enabled=True,
        apply_to_ai_call=False,
        reason="matched_pre_ai_vnext_scope",
        event={"symbol": "NAS100", "route_session": "london", "side": "SHORT"},
        side_decisions=(
            GTOSVNextRuntimeDecision(
                decision="AVOID",
                event={"symbol": "NAS100", "route_session": "london", "side": "SHORT"},
                enabled=True,
                apply_to_execution=False,
                matched=True,
                reason="matched_vnext_scope",
            ),
        ),
    )

    def fake_evaluate_pre_ai_vnext(**kwargs):
        assert kwargs["symbol"] == "NAS100"
        assert kwargs["bias"] == "bearish"
        return expected

    monkeypatch.setattr(orchestrator_mod, "evaluate_pre_ai_vnext", fake_evaluate_pre_ai_vnext)

    result = orch._evaluate_gtos_vnext_pre_ai(
        raw_data={"candle_close_utc": "2026-05-18T07:15:00+00:00"},
        kill_zone="london",
        bias_result={"bias": "bearish"},
    )

    assert result is expected
    rows = (tmp_path / "vnext_decisions.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1
    logged = json.loads(rows[0])
    assert logged["phase"] == "pre_ai"
    assert logged["decision"]["decision"] == "AVOID"
    assert "GTOS_VNEXT_PRE_AI action=ALLOW_AI decision=AVOID" in caplog.text


def test_orchestrator_injects_vnext_ai_role_context_into_ai_path():
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch.config = {"gtos_vnext_runtime": {"pre_ai_ai_role_context_apply_to_prompt": True}}
    orch._symbol = "XAUUSD"
    orch._mt5_symbol = "XAUUSD"
    decision = GTOSVNextPreAIRoutingDecision(
        action="ALLOW_AI",
        decision="FOLLOW",
        enabled=True,
        apply_to_ai_call=False,
        reason="matched_pre_ai_vnext_scope",
        event={"symbol": "XAUUSD", "route_session": "london"},
        recommended_side="LONG",
        recommended_frameworks=("ob_retest",),
        would_action="NARROW_AI_TO_ROUTE",
        ai_role_context={
            "enabled": True,
            "ai_role": "vnext_route_validator",
            "source_artifact_path": ".context/00_core/llm_specialization_research_backlog.md",
            "decision": "FOLLOW",
            "active_action": "ALLOW_AI",
            "selection_action": "NARROW_AI_TO_ROUTE",
            "would_action": "NARROW_AI_TO_ROUTE",
            "recommended_side": "LONG",
            "recommended_frameworks": ["ob_retest"],
            "recommended_route_families": ["ob_retest"],
            "blocked_sides": ["SHORT"],
            "blocked_frameworks": ["fvg_fill"],
            "blocked_route_families": ["fvg_fill"],
            "matched_rows": 12,
            "metric_sums": {"effective_n": 200.0, "cost_adjusted_simulated_r": 20.0},
            "decision_counts": {"FOLLOW": 12},
            "framework_counts": {"ob_retest": 12},
            "route_family_counts": {"ob_retest": 12},
            "source_component_counts": {"registry_scorer_module": 12},
            "role_instruction": "Validate the evidence-routed side/framework/route only.",
        },
    )

    prompt_context = orch._format_gtos_vnext_ai_role_context(vnext_pre_ai=decision)
    ai_policy = GTOSVNextAIPolicyDecision(
        action="CALL_AI_NARROWED_ROUTE",
        would_action="CALL_AI_NARROWED_ROUTE",
        allowed=True,
        would_allow_ai_call=True,
        enabled=True,
        apply_to_ai_call=False,
        reason="mechanical_route_narrows_ai_scope",
        ai_role="vnext_route_validator",
        prompt_scope={
            "recommended_side": "LONG",
            "recommended_frameworks": ["ob_retest"],
            "source_bound": True,
        },
        schema_contract={"schema_name": "PrimaryAnalysisOutput"},
        cache_contract={"prompt_packet_hash_required": True},
    )
    policy_prompt_context = orch._format_gtos_vnext_ai_role_context(
        vnext_pre_ai=decision,
        vnext_ai_policy=ai_policy,
    )
    policy_context = orch._ai_call_policy_context(
        raw_data={"candle_close_utc": "2026-05-18T07:15:00+00:00"},
        kill_zone="london",
        bias_result={"bias": "bullish"},
        vnext_pre_ai=decision,
        vnext_ai_policy=ai_policy,
    )

    assert "Role: vnext_route_validator" in prompt_context
    assert "Directive source: .context/00_core/llm_specialization_research_backlog.md" in (
        prompt_context
    )
    assert policy_context["vnext_ai_role"] == "vnext_route_validator"
    assert policy_context["vnext_pre_ai_would_action"] == "NARROW_AI_TO_ROUTE"
    assert policy_context["vnext_ai_role_matched_rows"] == 12
    assert policy_context["vnext_ai_role_recommended_frameworks"] == ["ob_retest"]
    assert policy_context["vnext_ai_policy_would_action"] == "CALL_AI_NARROWED_ROUTE"
    assert policy_context["vnext_ai_policy_role"] == "vnext_route_validator"
    assert "GTOS vNext AI Policy Contract" in policy_prompt_context


def test_attach_vnext_pre_ai_to_trade_record_preserves_route_evidence():
    decision = GTOSVNextPreAIRoutingDecision(
        action="NARROW_AI_TO_ROUTE",
        decision="FOLLOW",
        enabled=True,
        apply_to_ai_call=True,
        reason="pre_ai_vnext_route_to_LONG_ob_retest",
        event={"symbol": "XAUUSD", "route_session": "london"},
        recommended_side="LONG",
        recommended_frameworks=("ob_retest",),
        recommended_route_families=("ob_retest", "moonshot_mechanical"),
        blocked_sides=("SHORT",),
        blocked_frameworks=("fvg_fill",),
        blocked_route_families=("fvg_fill", "nofill_mechanical"),
        risk_vetoed_sides=("SHORT",),
        side_risk_reasons={"SHORT": "vnext_risk_source_repair_required"},
        evaluated_sides=("LONG", "SHORT"),
        would_action="NARROW_AI_TO_ROUTE",
        ai_role_context={
            "ai_role": "vnext_route_validator",
            "source_artifact_path": ".context/00_core/llm_specialization_research_backlog.md",
            "matched_rows": 3,
        },
    )
    record: dict = {"decision_pipeline": {}, "instrumentation": {}}

    attach_vnext_pre_ai_to_record(record, decision)

    attached = record["decision_pipeline"]["gtos_vnext_pre_ai"]
    assert attached["action"] == "NARROW_AI_TO_ROUTE"
    assert attached["recommended_frameworks"] == ["ob_retest"]
    assert attached["ai_role_context"]["ai_role"] == "vnext_route_validator"
    assert attached["recommended_route_families"] == ["ob_retest", "moonshot_mechanical"]
    assert attached["blocked_route_families"] == ["fvg_fill", "nofill_mechanical"]
    assert record["instrumentation"]["gtos_vnext_pre_ai_action"] == "NARROW_AI_TO_ROUTE"
    assert record["instrumentation"]["gtos_vnext_pre_ai_would_action"] == "NARROW_AI_TO_ROUTE"
    assert record["instrumentation"]["gtos_vnext_pre_ai_recommended_side"] == "LONG"
    assert record["instrumentation"]["gtos_vnext_pre_ai_recommended_frameworks"] == ["ob_retest"]
    assert record["instrumentation"]["gtos_vnext_pre_ai_recommended_route_families"] == [
        "ob_retest",
        "moonshot_mechanical",
    ]
    assert record["instrumentation"]["gtos_vnext_pre_ai_blocked_frameworks"] == ["fvg_fill"]
    assert record["instrumentation"]["gtos_vnext_pre_ai_blocked_route_families"] == [
        "fvg_fill",
        "nofill_mechanical",
    ]
    assert record["instrumentation"]["gtos_vnext_pre_ai_risk_vetoed_sides"] == ["SHORT"]
    assert record["instrumentation"]["gtos_vnext_pre_ai_side_risk_reasons"] == {
        "SHORT": "vnext_risk_source_repair_required"
    }
    assert record["instrumentation"]["gtos_vnext_pre_ai_ai_role"] == "vnext_route_validator"
    assert record["instrumentation"]["gtos_vnext_pre_ai_ai_role_matched_rows"] == 3


def test_vnext_ai_policy_shadows_mechanical_avoid_skip_until_activation():
    pre_ai = GTOSVNextPreAIRoutingDecision(
        action="ALLOW_AI",
        decision="AVOID",
        enabled=True,
        apply_to_ai_call=False,
        reason="matched_pre_ai_vnext_scope",
        event={"symbol": "XAUUSD", "route_session": "london"},
        blocked_sides=("LONG",),
        would_action="SKIP_AI_AVOID_ONLY",
        ai_role_context={
            "enabled": True,
            "ai_role": "vnext_avoid_blocker_classifier",
            "matched_rows": 12,
            "source_component_counts": {"rejected_candidate_c1_failed_value": 12},
            "decision_counts": {"AVOID": 12},
        },
    )

    shadow = evaluate_vnext_ai_policy(
        pre_ai_decision=pre_ai,
        config={"gtos_vnext_runtime": {"ai_policy_enabled": True}},
    )
    active = evaluate_vnext_ai_policy(
        pre_ai_decision=pre_ai,
        config={
            "gtos_vnext_runtime": {
                "ai_policy_enabled": True,
                "ai_policy_apply_to_ai_call": True,
            }
        },
    )

    assert shadow.action == "CALL_AI_CURRENT_PATH"
    assert shadow.would_action == "SKIP_AI_MECHANICAL_AVOID"
    assert shadow.allowed is True
    assert shadow.would_allow_ai_call is False
    assert active.action == "SKIP_AI_MECHANICAL_AVOID"
    assert active.allowed is False


def test_vnext_ai_policy_constrains_narrowed_route_and_prompt_contract():
    pre_ai = GTOSVNextPreAIRoutingDecision(
        action="NARROW_AI_TO_ROUTE",
        decision="FOLLOW",
        enabled=True,
        apply_to_ai_call=True,
        reason="pre_ai_vnext_route_to_LONG_ob_retest",
        event={"symbol": "XAUUSD", "route_session": "ny"},
        recommended_side="LONG",
        recommended_frameworks=("ob_retest",),
        recommended_route_families=("ob_retest",),
        blocked_frameworks=("fvg_fill",),
        would_action="NARROW_AI_TO_ROUTE",
        ai_role_context={
            "enabled": True,
            "ai_role": "vnext_route_validator",
            "matched_rows": 9,
            "source_component_counts": {"registry_scorer_module": 9},
            "decision_counts": {"FOLLOW": 9},
        },
    )

    decision = evaluate_vnext_ai_policy(
        pre_ai_decision=pre_ai,
        config={"gtos_vnext_runtime": {"ai_policy_enabled": True}},
        raw_data={"risk_tier": "funded_prop", "candidate_id": "cand-stage07"},
    )
    prompt_text = format_vnext_ai_policy_context_for_prompt(decision)

    assert decision.action == "CALL_AI_NARROWED_ROUTE"
    assert decision.would_action == "CALL_AI_NARROWED_ROUTE"
    assert decision.allowed is True
    assert decision.prompt_scope["source_bound"] is True
    assert decision.schema_contract["candidate_directions"] == ["LONG"]
    assert decision.schema_contract["candidate_frameworks"] == ["ob_retest"]
    assert decision.cache_contract["prompt_packet_hash_required"] is True
    assert "AI policy action: CALL_AI_NARROWED_ROUTE" in prompt_text
    assert "candidate_directions=LONG" in prompt_text


def test_vnext_ai_policy_allows_standard_follow_without_paid_ai_when_enabled():
    pre_ai = GTOSVNextPreAIRoutingDecision(
        action="ALLOW_AI",
        decision="FOLLOW",
        enabled=True,
        apply_to_ai_call=True,
        reason="matched_follow_scope",
        event={"symbol": "XAUUSD", "route_session": "london"},
        recommended_side="LONG",
        recommended_frameworks=("ob_retest",),
        would_action="ALLOW_AI",
        ai_role_context={"enabled": True, "ai_role": "vnext_route_validator"},
    )

    decision = evaluate_vnext_ai_policy(
        pre_ai_decision=pre_ai,
        config={
            "gtos_vnext_runtime": {
                "ai_policy_enabled": True,
                "ai_policy_apply_to_ai_call": True,
                "ai_policy_follow_no_ai_enabled": True,
                "ai_policy_follow_validator_risk_tiers": ["funded_prop"],
            }
        },
        risk_tier="standard",
    )
    no_paid = vnext_ai_policy_no_paid_call_replay_decision(
        decision,
        production_selected=True,
    )

    assert decision.action == "MECHANICAL_FOLLOW_NO_AI"
    assert decision.would_action == "MECHANICAL_FOLLOW_NO_AI"
    assert decision.would_allow_ai_call is False
    assert vnext_ai_policy_allows_no_paid_mechanical_follow(decision) is True
    assert vnext_ai_policy_requires_paid_call(decision) is False
    assert no_paid["selected"] is True
    assert no_paid["status"] == "mechanical_follow_no_paid_selected"


def test_vnext_ai_policy_no_paid_funded_prop_ai_required_is_diagnostic_only():
    pre_ai = GTOSVNextPreAIRoutingDecision(
        action="ALLOW_AI",
        decision="FOLLOW",
        enabled=True,
        apply_to_ai_call=True,
        reason="matched_follow_scope",
        event={"symbol": "XAUUSD", "route_session": "london"},
        recommended_side="LONG",
        recommended_frameworks=("ob_retest",),
        would_action="ALLOW_AI",
        ai_role_context={"enabled": True, "ai_role": "vnext_route_validator"},
    )

    decision = evaluate_vnext_ai_policy(
        pre_ai_decision=pre_ai,
        config={
            "gtos_vnext_runtime": {
                "ai_policy_enabled": True,
                "ai_policy_apply_to_ai_call": True,
                "ai_policy_follow_no_ai_enabled": True,
                "ai_policy_follow_validator_risk_tiers": ["standard", "funded_prop"],
            }
        },
        risk_tier="funded_prop",
    )
    no_paid = vnext_ai_policy_no_paid_call_replay_decision(
        decision,
        production_selected=True,
    )

    assert decision.action == "CALL_AI_CONSTRAINED_VALIDATOR"
    assert decision.would_allow_ai_call is True
    assert vnext_ai_policy_allows_no_paid_mechanical_follow(decision) is False
    assert vnext_ai_policy_requires_paid_call(decision) is True
    assert no_paid["selected"] is False
    assert no_paid["status"] == "diagnostic_ai_required_not_selected"
    assert no_paid["diagnostic_only"] is True


def test_vnext_ai_policy_blocks_unreplayed_legacy_broad_fallback_when_active():
    pre_ai = GTOSVNextPreAIRoutingDecision(
        action="ALLOW_AI",
        decision="LEGACY",
        enabled=True,
        apply_to_ai_call=True,
        reason="no_matching_pre_ai_vnext_scope",
        event={"symbol": "GBPJPY", "route_session": "tokyo"},
        would_action="ALLOW_AI",
        ai_role_context={"enabled": True, "ai_role": "general_trade_decision"},
    )

    decision = evaluate_vnext_ai_policy(
        pre_ai_decision=pre_ai,
        config={
            "gtos_vnext_runtime": {
                "ai_policy_enabled": True,
                "ai_policy_apply_to_ai_call": True,
                "ai_policy_allow_legacy_broad_fallback": False,
            }
        },
    )

    assert decision.action == "BLOCK_LEGACY_BROAD_FALLBACK"
    assert decision.allowed is False
    assert decision.reason == "legacy_broad_ai_fallback_not_replayed"
    assert decision.schema_contract["schema_version"] == "ai_reliability_contract_v1"
    assert decision.schema_contract["deterministic_baseline_contract"][
        "trade_permission"
    ] is False
    assert decision.schema_contract["semantic_ownership_handoff"][
        "no_copy_rule"
    ] == "do_not_copy_redacted_account_broker_truth_to_ftmo"
    assert decision.cache_contract["schema_version"] == "vnext_ai_policy_cache_contract_v2"


def test_attach_vnext_ai_policy_to_trade_record_preserves_hash_schema_contract():
    decision = GTOSVNextAIPolicyDecision(
        action="CALL_AI_NARROWED_ROUTE",
        would_action="CALL_AI_NARROWED_ROUTE",
        allowed=True,
        would_allow_ai_call=True,
        enabled=True,
        apply_to_ai_call=False,
        reason="mechanical_route_narrows_ai_scope",
        ai_role="vnext_route_validator",
        prompt_scope={"recommended_side": "SHORT", "source_bound": True},
        schema_contract={"schema_name": "PrimaryAnalysisOutput"},
        cache_contract={"prompt_packet_hash_required": True},
    )
    record: dict = {"decision_pipeline": {}, "instrumentation": {}}

    attach_vnext_ai_policy_to_record(record, decision)

    assert record["decision_pipeline"]["gtos_vnext_ai_policy"]["would_action"] == (
        "CALL_AI_NARROWED_ROUTE"
    )
    assert record["instrumentation"]["gtos_vnext_ai_policy_role"] == "vnext_route_validator"
    assert record["instrumentation"]["gtos_vnext_ai_policy_prompt_scope"][
        "recommended_side"
    ] == "SHORT"


def test_orchestrator_can_apply_active_pre_ai_route_to_bias_context():
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    decision = GTOSVNextPreAIRoutingDecision(
        action="NARROW_AI_TO_SIDE",
        decision="MIXED",
        enabled=True,
        apply_to_ai_call=True,
        reason="pre_ai_vnext_route_to_LONG",
        event={"symbol": "USDJPY", "route_session": "london"},
        recommended_side="LONG",
        recommended_frameworks=("ob_retest",),
        blocked_sides=("SHORT",),
        blocked_frameworks=("fvg_fill",),
        evaluated_sides=("LONG", "SHORT"),
        would_action="NARROW_AI_TO_SIDE",
    )

    routed = orch._apply_gtos_vnext_pre_ai_route(
        bias_result={"bias": "bearish", "source": "D1", "d1": "bearish", "h4": "bullish", "h1": "bullish", "m15": "bullish"},
        vnext_pre_ai=decision,
    )

    assert routed["bias"] == "bullish"
    assert routed["source"].startswith("gtos_vnext_pre_ai:LONG:ob_retest")
    assert routed["gtos_vnext_recommended_frameworks"] == ["ob_retest"]
    assert routed["gtos_vnext_blocked_frameworks"] == ["fvg_fill"]
    assert routed["gtos_vnext_original_bias"] == "bearish"
    assert routed["gtos_vnext_route_decision"]["recommended_side"] == "LONG"
    assert routed["gtos_vnext_route_decision"]["recommended_frameworks"] == ["ob_retest"]


def test_orchestrator_can_apply_active_route_family_to_bias_context():
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    decision = GTOSVNextPreAIRoutingDecision(
        action="NARROW_AI_TO_ROUTE",
        decision="FOLLOW",
        enabled=True,
        apply_to_ai_call=True,
        reason="pre_ai_vnext_route_to_LONG_moonshot_mechanical",
        event={"symbol": "GBPJPY", "route_session": "ny"},
        recommended_side="LONG",
        recommended_route_families=("moonshot_mechanical",),
        blocked_route_families=("numeric_router",),
        evaluated_sides=("LONG",),
        would_action="NARROW_AI_TO_ROUTE",
    )

    routed = orch._apply_gtos_vnext_pre_ai_route(
        bias_result={
            "bias": "no_bias",
            "source": "D1",
            "d1": "bullish",
            "h4": "bearish",
            "h1": "bullish",
            "m15": "bullish",
        },
        vnext_pre_ai=decision,
    )

    assert routed["bias"] == "bullish"
    assert routed["source"].startswith("gtos_vnext_pre_ai:LONG:moonshot_mechanical")
    assert routed["gtos_vnext_recommended_frameworks"] == []
    assert routed["gtos_vnext_recommended_route_families"] == ["moonshot_mechanical"]
    assert routed["gtos_vnext_blocked_route_families"] == ["numeric_router"]
    assert routed["gtos_vnext_route_decision"]["recommended_route_families"] == [
        "moonshot_mechanical"
    ]


def test_orchestrator_can_apply_active_framework_exclusion_to_bias_context():
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    decision = GTOSVNextPreAIRoutingDecision(
        action="NARROW_AI_EXCLUDE_FRAMEWORKS",
        decision="MIXED",
        enabled=True,
        apply_to_ai_call=True,
        reason="pre_ai_vnext_exclude_frameworks_fvg_fill",
        event={"symbol": "USDJPY", "route_session": "london"},
        recommended_frameworks=("ob_retest", "breaker_re_entry"),
        blocked_frameworks=("fvg_fill",),
        evaluated_sides=("LONG", "SHORT"),
        would_action="NARROW_AI_EXCLUDE_FRAMEWORKS",
    )

    routed = orch._apply_gtos_vnext_pre_ai_route(
        bias_result={
            "bias": "bearish",
            "source": "D1",
            "d1": "bearish",
            "h4": "bearish",
            "h1": "bearish",
            "m15": "bearish",
        },
        vnext_pre_ai=decision,
    )

    assert routed["bias"] == "bearish"
    assert routed["source"].startswith("gtos_vnext_pre_ai:frameworks:ob_retest+breaker_re_entry")
    assert routed["gtos_vnext_recommended_frameworks"] == ["ob_retest", "breaker_re_entry"]
    assert routed["gtos_vnext_blocked_frameworks"] == ["fvg_fill"]
    assert routed["gtos_vnext_original_source"] == "D1"


def test_orchestrator_pre_ai_gate_config_uses_active_vnext_framework_route():
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch.config = {
        "model_a": {"enabled_frameworks": ["ob_retest", "fvg_fill", "breaker_re_entry"]},
        "pre_ai_gates": {"h1_poi_availability_enabled": True},
    }
    routed_decision = GTOSVNextPreAIRoutingDecision(
        action="NARROW_AI_TO_ROUTE",
        decision="FOLLOW",
        enabled=True,
        apply_to_ai_call=True,
        reason="pre_ai_vnext_route_to_LONG_ob_retest",
        event={"symbol": "XAUUSD", "route_session": "london"},
        recommended_side="LONG",
        recommended_frameworks=("ob_retest",),
        blocked_frameworks=("fvg_fill",),
        would_action="NARROW_AI_TO_ROUTE",
    )
    shadow_decision = GTOSVNextPreAIRoutingDecision(
        action="ALLOW_AI",
        decision="FOLLOW",
        enabled=True,
        apply_to_ai_call=False,
        reason="matched_pre_ai_vnext_scope",
        event={"symbol": "XAUUSD", "route_session": "london"},
        recommended_side="LONG",
        recommended_frameworks=("ob_retest",),
        would_action="NARROW_AI_TO_ROUTE",
    )

    routed_cfg = orch._config_for_gtos_vnext_pre_ai_gate(vnext_pre_ai=routed_decision)
    shadow_cfg = orch._config_for_gtos_vnext_pre_ai_gate(vnext_pre_ai=shadow_decision)

    assert routed_cfg["model_a"]["enabled_frameworks"] == ["ob_retest"]
    assert orch.config["model_a"]["enabled_frameworks"] == ["ob_retest", "fvg_fill", "breaker_re_entry"]
    assert shadow_cfg is orch.config


def test_orchestrator_pre_ai_gate_config_can_exclude_blocked_frameworks():
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch.config = {
        "model_a": {"enabled_frameworks": ["ob_retest", "fvg_fill", "breaker_re_entry"]},
        "pre_ai_gates": {"h1_poi_availability_enabled": True},
    }
    decision = GTOSVNextPreAIRoutingDecision(
        action="NARROW_AI_EXCLUDE_FRAMEWORKS",
        decision="MIXED",
        enabled=True,
        apply_to_ai_call=True,
        reason="pre_ai_vnext_exclude_frameworks_fvg_fill",
        event={"symbol": "XAUUSD", "route_session": "london"},
        recommended_frameworks=("ob_retest", "breaker_re_entry"),
        blocked_frameworks=("fvg_fill",),
        would_action="NARROW_AI_EXCLUDE_FRAMEWORKS",
    )

    routed_cfg = orch._config_for_gtos_vnext_pre_ai_gate(vnext_pre_ai=decision)

    assert routed_cfg["model_a"]["enabled_frameworks"] == ["ob_retest", "breaker_re_entry"]
    assert orch.config["model_a"]["enabled_frameworks"] == ["ob_retest", "fvg_fill", "breaker_re_entry"]


def test_orchestrator_ai_framework_override_uses_active_vnext_route_only():
    routed_decision = GTOSVNextPreAIRoutingDecision(
        action="NARROW_AI_TO_ROUTE",
        decision="FOLLOW",
        enabled=True,
        apply_to_ai_call=True,
        reason="pre_ai_vnext_route_to_LONG_ob_retest",
        event={"symbol": "XAUUSD", "route_session": "london"},
        recommended_side="LONG",
        recommended_frameworks=("ob_retest",),
        would_action="NARROW_AI_TO_ROUTE",
    )
    shadow_decision = GTOSVNextPreAIRoutingDecision(
        action="ALLOW_AI",
        decision="FOLLOW",
        enabled=True,
        apply_to_ai_call=False,
        reason="matched_pre_ai_vnext_scope",
        event={"symbol": "XAUUSD", "route_session": "london"},
        recommended_side="LONG",
        recommended_frameworks=("ob_retest",),
        would_action="NARROW_AI_TO_ROUTE",
    )
    exclusion_decision = GTOSVNextPreAIRoutingDecision(
        action="NARROW_AI_EXCLUDE_FRAMEWORKS",
        decision="MIXED",
        enabled=True,
        apply_to_ai_call=True,
        reason="pre_ai_vnext_exclude_frameworks_fvg_fill",
        event={"symbol": "XAUUSD", "route_session": "london"},
        recommended_frameworks=("ob_retest", "breaker_re_entry"),
        blocked_frameworks=("fvg_fill",),
        would_action="NARROW_AI_EXCLUDE_FRAMEWORKS",
    )

    assert SessionOrchestrator._frameworks_override_for_gtos_vnext_ai(
        vnext_pre_ai=routed_decision
    ) == ["ob_retest"]
    assert SessionOrchestrator._frameworks_override_for_gtos_vnext_ai(
        vnext_pre_ai=exclusion_decision
    ) == ["ob_retest", "breaker_re_entry"]
    assert SessionOrchestrator._frameworks_override_for_gtos_vnext_ai(
        vnext_pre_ai=shadow_decision
    ) is None


def test_orchestrator_rejects_ai_candidate_that_violates_active_vnext_route():
    routed_decision = GTOSVNextPreAIRoutingDecision(
        action="NARROW_AI_TO_ROUTE",
        decision="FOLLOW",
        enabled=True,
        apply_to_ai_call=True,
        reason="pre_ai_vnext_route_to_LONG_ob_retest",
        event={"symbol": "XAUUSD", "route_session": "london"},
        recommended_side="LONG",
        recommended_frameworks=("ob_retest",),
        would_action="NARROW_AI_TO_ROUTE",
    )
    fvg_routed_decision = GTOSVNextPreAIRoutingDecision(
        action="NARROW_AI_TO_ROUTE",
        decision="FOLLOW",
        enabled=True,
        apply_to_ai_call=True,
        reason="pre_ai_vnext_route_to_LONG_fvg_fill",
        event={"symbol": "XAUUSD", "route_session": "london"},
        recommended_side="LONG",
        recommended_frameworks=("fvg_fill",),
        would_action="NARROW_AI_TO_ROUTE",
    )
    route_family_only_decision = GTOSVNextPreAIRoutingDecision(
        action="NARROW_AI_TO_ROUTE",
        decision="FOLLOW",
        enabled=True,
        apply_to_ai_call=True,
        reason="pre_ai_vnext_route_to_LONG_moonshot_mechanical",
        event={"symbol": "XAUUSD", "route_session": "london"},
        recommended_side="LONG",
        recommended_route_families=("moonshot_mechanical",),
        would_action="NARROW_AI_TO_ROUTE",
    )
    route_family_blocked_during_routing = GTOSVNextPreAIRoutingDecision(
        action="NARROW_AI_TO_ROUTE",
        decision="FOLLOW",
        enabled=True,
        apply_to_ai_call=True,
        reason="pre_ai_vnext_route_to_LONG_moonshot_mechanical",
        event={"symbol": "XAUUSD", "route_session": "london"},
        recommended_side="LONG",
        recommended_route_families=("moonshot_mechanical",),
        blocked_route_families=("fvg_fill",),
        would_action="NARROW_AI_TO_ROUTE",
    )
    route_family_exclusion_decision = GTOSVNextPreAIRoutingDecision(
        action="NARROW_AI_EXCLUDE_FRAMEWORKS",
        decision="MIXED",
        enabled=True,
        apply_to_ai_call=True,
        reason="pre_ai_vnext_exclude_frameworks_numeric_router",
        event={"symbol": "XAUUSD", "route_session": "london"},
        recommended_frameworks=("ob_retest", "breaker_re_entry"),
        blocked_route_families=("fvg_fill",),
        would_action="NARROW_AI_EXCLUDE_FRAMEWORKS",
    )
    exclusion_decision = GTOSVNextPreAIRoutingDecision(
        action="NARROW_AI_EXCLUDE_FRAMEWORKS",
        decision="MIXED",
        enabled=True,
        apply_to_ai_call=True,
        reason="pre_ai_vnext_exclude_frameworks_fvg_fill",
        event={"symbol": "XAUUSD", "route_session": "london"},
        recommended_frameworks=("ob_retest", "breaker_re_entry"),
        blocked_frameworks=("fvg_fill",),
        would_action="NARROW_AI_EXCLUDE_FRAMEWORKS",
    )
    framework_mismatch = SimpleNamespace(
        decision="CANDIDATE",
        framework="fvg_fill",
        trade_parameters=SimpleNamespace(direction="LONG"),
    )
    side_mismatch = SimpleNamespace(
        decision="CANDIDATE",
        framework="ob_retest",
        trade_parameters=SimpleNamespace(direction="SHORT"),
    )
    matched = SimpleNamespace(
        decision="CANDIDATE",
        framework="ob_retest",
        trade_parameters=SimpleNamespace(direction="LONG"),
    )
    matched_effective_framework = SimpleNamespace(
        decision="CANDIDATE",
        framework="ob_retest",
        trade_parameters=SimpleNamespace(direction="LONG"),
        frameworks_evaluated={
            "ob_retest": SimpleNamespace(qualified=False, reason="no OB"),
            "fvg_fill": SimpleNamespace(qualified=True, reason="FVG present"),
        },
        reasoning=SimpleNamespace(
            h1_setup=SimpleNamespace(poi_type="FVG"),
        ),
    )

    assert SessionOrchestrator._gtos_vnext_ai_route_mismatch(
        analysis=framework_mismatch,
        vnext_pre_ai=routed_decision,
    ) == "framework_mismatch_expected_ob_retest_got_fvg_fill"
    assert SessionOrchestrator._gtos_vnext_ai_route_mismatch(
        analysis=side_mismatch,
        vnext_pre_ai=routed_decision,
    ) == "side_mismatch_expected_LONG_got_SHORT"
    assert SessionOrchestrator._gtos_vnext_ai_route_mismatch(
        analysis=matched,
        vnext_pre_ai=routed_decision,
    ) is None
    assert SessionOrchestrator._gtos_vnext_ai_route_mismatch(
        analysis=matched_effective_framework,
        vnext_pre_ai=fvg_routed_decision,
    ) is None
    assert SessionOrchestrator._gtos_vnext_ai_route_mismatch(
        analysis=framework_mismatch,
        vnext_pre_ai=exclusion_decision,
    ) == "framework_blocked_fvg_fill"
    assert SessionOrchestrator._gtos_vnext_ai_route_mismatch(
        analysis=framework_mismatch,
        vnext_pre_ai=route_family_only_decision,
    ) is None
    assert SessionOrchestrator._gtos_vnext_ai_route_mismatch(
        analysis=framework_mismatch,
        vnext_pre_ai=route_family_blocked_during_routing,
    ) == "route_family_blocked_fvg_fill"
    assert SessionOrchestrator._gtos_vnext_ai_route_mismatch(
        analysis=framework_mismatch,
        vnext_pre_ai=route_family_exclusion_decision,
    ) == "route_family_blocked_fvg_fill"


def test_orchestrator_builds_vnext_pending_telemetry():
    pre_ai = GTOSVNextPreAIRoutingDecision(
        action="NARROW_AI_TO_ROUTE",
        decision="FOLLOW",
        enabled=True,
        apply_to_ai_call=True,
        reason="pre_ai_vnext_route_to_LONG_ob_retest",
        event={"symbol": "XAUUSD"},
        recommended_side="LONG",
        recommended_frameworks=("ob_retest",),
        blocked_sides=("SHORT",),
        risk_vetoed_sides=("LONG",),
        side_risk_reasons={"LONG": "vnext_risk_target_stop_not_source_bound"},
        would_action="NARROW_AI_TO_ROUTE",
    )
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD"},
        enabled=True,
        apply_to_execution=False,
        matched=True,
        reason="matched_vnext_route_scope",
        evidence={
            "matched_rows": 3,
            "metrics": {
                "cost_adjusted_simulated_r": {"sum": 12.5},
                "proxy_score": {"sum": 2.0},
                "stress_simulated_r": {"sum": 10.0},
                "effective_n": {"sum": 250},
            },
        },
    )
    adjustment = GTOSVNextRiskAdjustment(
        enabled=True,
        apply_to_execution=False,
        applied=False,
        decision="FOLLOW",
        before_risk_pct=1.0,
        after_risk_pct=1.0,
        multiplier=1.0,
        would_multiplier=1.25,
        reason="shadow_vnext_risk_strong_follow",
    )
    pending_policy = GTOSVNextPendingPolicy(
        action="PLACE_LIMIT",
        would_action="SKIP_PENDING_NOFILL_AVOID",
        enabled=True,
        apply_to_execution=False,
        applied=False,
        decision="MIXED",
        reason="shadow_vnext_pending_policy_nofill_avoid",
    )
    ltf_path_execution = GTOSVNextLTFPathExecutionDecision(
        action="PLACE_LIMIT",
        would_action="MONITOR_LTF_PATH",
        enabled=True,
        apply_to_execution=False,
        applied=False,
        decision="FOLLOW",
        reason="shadow_vnext_ltf_path_monitor_until_touch_or_invalidation",
        monitor_timeframe="M1",
        adjusted_entry_price=None,
    )
    prop_safe_selector = GTOSVNextPropSafeSelectorDecision(
        action="ALLOW",
        would_action="REDUCE_RISK",
        enabled=True,
        apply_to_execution=False,
        applied=False,
        decision="FOLLOW",
        before_risk_pct=2.0,
        after_risk_pct=2.0,
        max_allowed_new_trade_risk_pct=1.5,
        reason="shadow_prop_safe_selector_reduce_risk_to_redacted_account_external_daily_5pct_budget",
    )
    moonshot_dynamic = GTOSVNextMoonshotDynamicExecutionDecision(
        enabled=True,
        apply_to_execution=False,
        applied=False,
        decision_status="vnext_candidate_ready",
        candidate_action="TRADE_VNEXT_ACTIVATED_CANDIDATE",
        selected_branch="origin_current_fvg_fill",
        selected_policy="momentum_exhaustion",
        execution_policy_id="vnext_exec_momentum_1r_pullback_04r_cap_2r",
        replaced_policy="retired_static_baseline_comparator",
        fixed_target_role="baseline_comparator_only",
        prop_action="ALLOW_UNLESS_EXTERNAL_PROP_GOVERNOR_BLOCKS",
        ai_role="MECHANICAL_PRIMARY_AI_VALIDATES_ONLY_AMBIGUOUS_SOURCE_OR_CONFLICT",
        source_quality_action="SOURCE_OK_FOR_DEFAULT_OFF_REPLAY",
        exit_management_action="REPLACE_RETIRED_STATIC_BASELINE_WITH_MOMENTUM_EXHAUSTION_PRIMARY",
    )

    telemetry = SessionOrchestrator._gtos_vnext_pending_telemetry(
        vnext_pre_ai=pre_ai,
        vnext_decision=decision,
        vnext_risk_adjustment=adjustment,
        vnext_pending_policy=pending_policy,
        vnext_ltf_path_execution=ltf_path_execution,
        vnext_prop_safe_selector=prop_safe_selector,
        vnext_moonshot_dynamic_execution=moonshot_dynamic,
    )

    assert telemetry["gtos_vnext_pre_ai_action"] == "NARROW_AI_TO_ROUTE"
    assert telemetry["gtos_vnext_pre_ai_recommended_frameworks"] == ["ob_retest"]
    assert telemetry["gtos_vnext_pre_ai_recommended_route_families"] == []
    assert telemetry["gtos_vnext_pre_ai_blocked_sides"] == ["SHORT"]
    assert telemetry["gtos_vnext_pre_ai_blocked_frameworks"] == []
    assert telemetry["gtos_vnext_pre_ai_blocked_route_families"] == []
    assert telemetry["gtos_vnext_pre_ai_risk_vetoed_sides"] == ["LONG"]
    assert telemetry["gtos_vnext_pre_ai_side_risk_reasons"] == {
        "LONG": "vnext_risk_target_stop_not_source_bound"
    }
    assert telemetry["gtos_vnext_decision"] == "FOLLOW"
    assert telemetry["gtos_vnext_matched_rows"] == 3
    assert telemetry["gtos_vnext_cost_adjusted_r_sum"] == 12.5
    assert telemetry["gtos_vnext_effective_n_sum"] == 250
    assert telemetry["gtos_vnext_risk_would_multiplier"] == 1.25
    assert telemetry["gtos_vnext_pending_policy_action"] == "PLACE_LIMIT"
    assert telemetry["gtos_vnext_pending_policy_would_action"] == "SKIP_PENDING_NOFILL_AVOID"
    assert telemetry["gtos_vnext_pending_policy_applied"] is False
    assert telemetry["gtos_vnext_ltf_path_action"] == "PLACE_LIMIT"
    assert telemetry["gtos_vnext_ltf_path_would_action"] == "MONITOR_LTF_PATH"
    assert telemetry["gtos_vnext_ltf_path_monitor_timeframe"] == "M1"
    assert telemetry["gtos_vnext_prop_safe_selector_action"] == "ALLOW"
    assert telemetry["gtos_vnext_prop_safe_selector_would_action"] == "REDUCE_RISK"
    assert telemetry["gtos_vnext_prop_safe_selector_applied"] is False
    assert telemetry["gtos_vnext_prop_safe_selector_after_risk_pct"] == 2.0
    assert telemetry["gtos_vnext_dynamic_policy_selected"] == "momentum_exhaustion"
    assert telemetry["gtos_vnext_dynamic_policy_applied"] is False
    assert telemetry["gtos_vnext_dynamic_policy_replaced_policy"] == "retired_static_baseline_comparator"
    assert telemetry["gtos_vnext_dynamic_policy_candidate_action"] == (
        "TRADE_VNEXT_ACTIVATED_CANDIDATE"
    )


def test_moonshot_dynamic_execution_default_off_attaches_no_effect() -> None:
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD", "side": "LONG", "framework": "fvg_fill", "route_session": "london"},
        enabled=True,
        apply_to_execution=False,
        matched=True,
        reason="matched_vnext_route_scope",
        evidence={"matched_rows": 3},
    )

    routed = evaluate_vnext_moonshot_dynamic_execution(
        decision=decision,
        config={"gtos_vnext_runtime": {}},
    )
    record = {}
    attach_vnext_moonshot_dynamic_execution_to_record(record, routed)

    assert routed.decision_status == "disabled_vnext"
    assert routed.applied is False
    assert routed.selected_policy is None
    assert routed.target_stop_geometry_v4["status"] == "dynamic_policy_not_selected"
    assert routed.source_event["session_bucket"] == "london_broad"
    assert record["instrumentation"]["gtos_vnext_dynamic_policy_applied"] is False
    assert record["instrumentation"]["gtos_vnext_target_stop_geometry_v4_status"] == (
        "dynamic_policy_not_selected"
    )


def test_moonshot_dynamic_execution_overlay_replaces_j46_when_source_bound() -> None:
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD", "side": "LONG", "framework": "fvg_fill", "route_session": "ny"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched_vnext_route_scope",
        evidence={"matched_rows": 3},
    )
    cfg = {
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
            "moonshot_dynamic_execution_router_default_source_mode": "OHLC_M15_CSV",
            "moonshot_dynamic_execution_router_default_source_path_feature_status": (
                "computed_from_source_ohlc_asof"
            ),
            "moonshot_dynamic_execution_router_default_source_window_complete": True,
            "moonshot_dynamic_execution_router_default_ordered_path_status": (
                "ordered_path_not_ambiguous_in_m15_replay"
            ),
        },
    }

    routed = evaluate_vnext_moonshot_dynamic_execution(
        decision=decision,
        config=cfg,
        candidate_context={
            "current_bar_displacement_atr14": 0.4,
            "kill_zone_position": "in_ny_early",
            "trade_parameters": {
                "direction": "LONG",
                "entry_price": 100.0,
                "stop_loss": 98.0,
            },
        },
    )

    assert routed.decision_status == "vnext_candidate_ready"
    assert routed.selected_policy == "momentum_exhaustion"
    assert routed.execution_policy_id == "vnext_exec_momentum_1r_pullback_04r_cap_2r"
    assert routed.replaced_policy == "retired_static_baseline_comparator"
    assert routed.candidate_use_allowed_now is True
    assert routed.applied is True
    assert routed.target_stop_geometry_v4["status"] == (
        "source_bound_geometry_contract_ready"
    )
    assert routed.target_stop_geometry_v4["target_destination"]["final_target_r"] == 2.0
    assert routed.to_record()["target_stop_geometry_v4"]["thesis_horizon"][
        "horizon_m15_bars"
    ] == 32
    assert routed.source_event["session_bucket"] == "ny_broad"


def test_moonshot_dynamic_execution_repaired_branch_allowlist_promotes_non_follow(tmp_path) -> None:
    allowlist = tmp_path / "stage13_repaired_branch_allowlist.json"
    allowlist.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "symbol": "UK100",
                        "framework": "ob_retest",
                        "candidate_origin_family": "origin_current_ob_retest",
                        "session_bucket": "london_broad",
                        "kill_zone_bucket": "in_london_repo_schedule_repaired",
                        "allowed_prior_branch_labels": ["LEGACY"],
                        "repaired_branch_action": "MOONSHOT_REPAIRED_FOLLOW",
                        "proof_class": "positive_executable_repaired_branch_semantics",
                        "repaired_branch_metrics": {
                            "performance_rows": 255,
                            "expectancy_r": 0.36,
                            "profit_factor": 2.06,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    decision = GTOSVNextRuntimeDecision(
        decision="LEGACY",
        event={"symbol": "UK100", "side": "LONG", "framework": "ob_retest", "route_session": "london"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="no_matching_vnext_route_scope",
        evidence={"matched_rows": 0},
    )
    cfg = {
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
            "moonshot_dynamic_execution_router_activated_frameworks": [
                "breaker_re_entry",
                "fvg_fill",
                "ob_retest",
            ],
            "moonshot_dynamic_execution_router_broker_native_eligible_symbols": ["UK100"],
            "moonshot_dynamic_execution_router_required_branch_labels": ["FOLLOW"],
            "moonshot_dynamic_execution_router_repaired_branch_allowlist_path": str(allowlist),
        },
    }

    routed = evaluate_vnext_moonshot_dynamic_execution(
        decision=decision,
        config=cfg,
        candidate_context={
            "candidate_origin_family": "origin_current_ob_retest",
            "candle_time_utc": "2026-01-02T08:30:00+00:00",
            "kill_zone_position": "in_london_repo_schedule_repaired",
        },
    )

    assert routed.decision_status == "vnext_candidate_ready"
    assert routed.candidate_action == "TRADE_VNEXT_REPAIRED_BRANCH_CANDIDATE"
    assert routed.applied is True
    assert routed.source_event["repaired_branch_allowed"] is True
    assert routed.source_event["kill_zone_position"] == "in_london_repo_schedule_repaired"


def test_moonshot_dynamic_execution_broader_origin_allowlist_promotes_origin_family(tmp_path) -> None:
    allowlist = tmp_path / "stage13_broader_origin_allowlist.json"
    allowlist.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "origin_family": "liquidity_sweep_reclaim",
                        "candidate_origin_family": "origin_liquidity_sweep_reclaim",
                        "symbol": "XAUUSD",
                        "route_session": "london",
                        "side": "LONG",
                        "selected_policy": "partial_be_runner",
                        "proof_class": "positive_origin_native_dynamic_replay_row_level_proof",
                        "activation_action": "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE",
                        "metrics": {
                            "performance_rows": 144,
                            "expectancy_r": 0.27,
                            "profit_factor": 1.6,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    decision = GTOSVNextRuntimeDecision(
        decision="LEGACY",
        event={
            "symbol": "XAUUSD",
            "side": "LONG",
            "framework": "liquidity_sweep_reclaim",
            "candidate_origin_family": "origin_liquidity_sweep_reclaim",
            "route_session": "london",
        },
        enabled=True,
        apply_to_execution=True,
        matched=False,
        reason="broader_origin_candidate_contract",
        evidence={"matched_rows": 0},
    )
    cfg = {
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
            "moonshot_dynamic_execution_router_policy": "momentum_exhaustion",
            "moonshot_dynamic_execution_router_condition_challenger_enabled": True,
            "moonshot_dynamic_execution_router_condition_challenger_policy": (
                "condition_asof_displacement_v1"
            ),
            "moonshot_dynamic_execution_router_momentum_exception_policy": (
                "partial_be_runner"
            ),
            "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner": [
                "liquidity_sweep_reclaim"
            ],
            "moonshot_dynamic_execution_router_activated_origin_families": [
                "liquidity_sweep_reclaim",
            ],
            "moonshot_dynamic_execution_router_broker_native_eligible_symbols": ["XAUUSD"],
            "moonshot_dynamic_execution_router_required_branch_labels": ["FOLLOW"],
            "moonshot_dynamic_execution_router_broader_origin_allowlist_path": str(allowlist),
        },
    }

    routed = evaluate_vnext_moonshot_dynamic_execution(
        decision=decision,
        config=cfg,
        candidate_context={
            "kill_zone_position": "in_london_early",
            "live_generation_status": "generated_live_asof",
        },
    )

    assert routed.decision_status == "vnext_candidate_ready"
    assert routed.candidate_action == "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE"
    assert routed.selected_policy == "partial_be_runner"
    assert routed.execution_policy_id == "vnext_exec_partial_50_at_1r_be_runner_to_3r"
    assert routed.applied is True
    assert routed.source_event["broader_origin_allowed"] is True


def test_moonshot_dynamic_execution_requires_positive_selected_cell_risk_when_configured(tmp_path) -> None:
    allowlist = tmp_path / "stage13_broader_origin_allowlist.json"
    allowlist.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "origin_family": "liquidity_sweep_reclaim",
                        "candidate_origin_family": "origin_liquidity_sweep_reclaim",
                        "symbol": "XAUUSD",
                        "route_session": "london",
                        "side": "LONG",
                        "selected_policy": "partial_be_runner",
                        "proof_class": "positive_origin_native_dynamic_replay_row_level_proof",
                        "activation_action": "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE",
                        "metrics": {
                            "performance_rows": 144,
                            "expectancy_r": 0.27,
                            "profit_factor": 1.6,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    risk_ledger = tmp_path / "selected_cell_risk.jsonl"
    risk_ledger.write_text(
        json.dumps(
            {
                "record_type": "redacted_account_selected_cell_risk",
                "selector_component": "broader_origin",
                "risk_cell_id": "risk-positive-1",
                "symbol": "XAUUSD",
                "family": "liquidity_sweep_reclaim",
                "candidate_origin_family": "origin_liquidity_sweep_reclaim",
                "route_session": "london",
                "session_bucket": "london",
                "side": "LONG",
                "selected_policy": "be_after_trigger",
                "effective_risk_per_trade_pct": 0.25,
                "risk_decision_basis": "vnext_cell_evidence_tier:micro_positive_ev_floor;no_spread_cap;redacted_account_5pct_daily_10pct_static",
                "exact_unresolved_or_excluded_reasons": [],
                "source_effective_config_status": "broker_native_geometry_bound",
                "effective_price_rounding_increment": 0.01,
                "effective_lot_rounding_step": 0.01,
                "price_rounding_policy": {"status": "verified_from_broker_spec"},
                "volume_rounding_policy": {"status": "verified_from_broker_spec"},
                "uses_unverified_default": False,
                "stale_old_profile_risk_without_cell_evidence": False,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    decision = GTOSVNextRuntimeDecision(
        decision="LEGACY",
        event={
            "symbol": "XAUUSD",
            "side": "LONG",
            "framework": "liquidity_sweep_reclaim",
            "candidate_origin_family": "origin_liquidity_sweep_reclaim",
            "route_session": "london",
        },
        enabled=True,
        apply_to_execution=True,
        matched=False,
        reason="broader_origin_candidate_contract",
        evidence={"matched_rows": 0},
    )
    cfg = {
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
            "moonshot_dynamic_execution_router_policy": "momentum_exhaustion",
            "moonshot_dynamic_execution_router_condition_challenger_enabled": True,
            "moonshot_dynamic_execution_router_condition_challenger_policy": (
                "condition_asof_displacement_v1"
            ),
            "moonshot_dynamic_execution_router_momentum_exception_policy": (
                "partial_be_runner"
            ),
            "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner": [
                "liquidity_sweep_reclaim"
            ],
            "moonshot_dynamic_execution_router_allow_policy_invariant_selected_cell_risk_geometry": True,
            "moonshot_dynamic_execution_router_activated_origin_families": [
                "liquidity_sweep_reclaim",
            ],
            "moonshot_dynamic_execution_router_broker_native_eligible_symbols": ["XAUUSD"],
            "moonshot_dynamic_execution_router_required_branch_labels": ["FOLLOW"],
            "moonshot_dynamic_execution_router_broader_origin_allowlist_path": str(allowlist),
            "moonshot_dynamic_execution_router_require_selected_cell_risk_ledger": True,
            "moonshot_dynamic_execution_router_selected_cell_risk_ledger_path": str(risk_ledger),
        },
    }

    routed = evaluate_vnext_moonshot_dynamic_execution(
        decision=decision,
        config=cfg,
        candidate_context={
            "kill_zone_position": "in_london_early",
            "live_generation_status": "generated_live_asof",
        },
    )

    assert routed.applied is True
    assert routed.source_event["selected_cell_risk_allowed"] is True
    assert routed.source_event["selected_cell_risk_pct"] == 0.25
    assert routed.source_event["selected_cell_risk_cell_id"] == "risk-positive-1"
    assert routed.source_event["selected_cell_risk_selected_policy"] == "partial_be_runner"
    assert routed.source_event["selected_cell_risk_source_policy"] == "be_after_trigger"
    assert routed.source_event["selected_cell_risk_policy_identity_status"] == (
        "policy_invariant_broker_geometry_for_selected_execution_policy"
    )


def test_moonshot_dynamic_execution_reloads_selected_cell_risk_after_lfs_materialization(
    tmp_path,
) -> None:
    allowlist = tmp_path / "stage13_broader_origin_allowlist.json"
    allowlist.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "origin_family": "liquidity_sweep_reclaim",
                        "candidate_origin_family": "origin_liquidity_sweep_reclaim",
                        "symbol": "XAUUSD",
                        "route_session": "london",
                        "side": "LONG",
                        "selected_policy": "partial_be_runner",
                        "proof_class": "positive_origin_native_dynamic_replay_row_level_proof",
                        "activation_action": "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE",
                        "metrics": {
                            "performance_rows": 144,
                            "expectancy_r": 0.27,
                            "profit_factor": 1.6,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    risk_ledger = tmp_path / "selected_cell_risk.jsonl"
    risk_ledger.write_text(
        "\n".join(
            [
                "version https://git-lfs.github.com/spec/v1",
                "oid sha256:" + "0" * 64,
                "size 5818853",
                "",
            ]
        ),
        encoding="utf-8",
    )
    decision = GTOSVNextRuntimeDecision(
        decision="LEGACY",
        event={
            "symbol": "XAUUSD",
            "side": "LONG",
            "framework": "liquidity_sweep_reclaim",
            "candidate_origin_family": "origin_liquidity_sweep_reclaim",
            "route_session": "london",
        },
        enabled=True,
        apply_to_execution=True,
        matched=False,
        reason="broader_origin_candidate_contract",
        evidence={"matched_rows": 0},
    )
    cfg = {
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
            "moonshot_dynamic_execution_router_policy": "momentum_exhaustion",
            "moonshot_dynamic_execution_router_condition_challenger_enabled": True,
            "moonshot_dynamic_execution_router_condition_challenger_policy": (
                "condition_asof_displacement_v1"
            ),
            "moonshot_dynamic_execution_router_momentum_exception_policy": (
                "partial_be_runner"
            ),
            "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner": [
                "liquidity_sweep_reclaim"
            ],
            "moonshot_dynamic_execution_router_allow_policy_invariant_selected_cell_risk_geometry": True,
            "moonshot_dynamic_execution_router_activated_origin_families": [
                "liquidity_sweep_reclaim",
            ],
            "moonshot_dynamic_execution_router_broker_native_eligible_symbols": ["XAUUSD"],
            "moonshot_dynamic_execution_router_required_branch_labels": ["FOLLOW"],
            "moonshot_dynamic_execution_router_broader_origin_allowlist_path": str(allowlist),
            "moonshot_dynamic_execution_router_require_selected_cell_risk_ledger": True,
            "moonshot_dynamic_execution_router_selected_cell_risk_ledger_path": str(risk_ledger),
        },
    }

    pointed = evaluate_vnext_moonshot_dynamic_execution(
        decision=decision,
        config=cfg,
        candidate_context={
            "kill_zone_position": "in_london_early",
            "live_generation_status": "generated_live_asof",
        },
    )

    assert pointed.applied is False
    assert "selected_cell_risk_not_verified_or_zero" in pointed.refusal_reasons
    assert pointed.source_event["selected_cell_risk_match_reason"] == (
        "selected_cell_risk_ledger_raw_lfs_pointer"
    )
    assert pointed.source_event["selected_cell_risk_refusal_cause"] == (
        "selected_cell_risk_ledger_raw_lfs_pointer"
    )
    assert pointed.source_event["selected_cell_risk_ledger_load_status"]["status"] == (
        "raw_lfs_pointer"
    )

    risk_ledger.write_text(
        json.dumps(
            {
                "record_type": "redacted_account_selected_cell_risk",
                "selector_component": "broader_origin",
                "risk_cell_id": "risk-positive-after-lfs-materialization",
                "symbol": "XAUUSD",
                "family": "liquidity_sweep_reclaim",
                "candidate_origin_family": "origin_liquidity_sweep_reclaim",
                "route_session": "london",
                "session_bucket": "london",
                "side": "LONG",
                "selected_policy": "be_after_trigger",
                "effective_risk_per_trade_pct": 0.25,
                "risk_decision_basis": "vnext_cell_evidence_tier:micro_positive_ev_floor;no_spread_cap;redacted_account_5pct_daily_10pct_static",
                "exact_unresolved_or_excluded_reasons": [],
                "source_effective_config_status": "broker_native_geometry_bound",
                "effective_price_rounding_increment": 0.01,
                "effective_lot_rounding_step": 0.01,
                "price_rounding_policy": {"status": "verified_from_broker_spec"},
                "volume_rounding_policy": {"status": "verified_from_broker_spec"},
                "uses_unverified_default": False,
                "stale_old_profile_risk_without_cell_evidence": False,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    materialized = evaluate_vnext_moonshot_dynamic_execution(
        decision=decision,
        config=cfg,
        candidate_context={
            "kill_zone_position": "in_london_early",
            "live_generation_status": "generated_live_asof",
        },
    )

    assert materialized.applied is True
    assert materialized.source_event["selected_cell_risk_allowed"] is True
    assert materialized.source_event["selected_cell_risk_cell_id"] == (
        "risk-positive-after-lfs-materialization"
    )


def test_moonshot_dynamic_execution_allows_positive_selected_cell_with_nonblocking_commission_source_fact(tmp_path) -> None:
    allowlist = tmp_path / "stage13_broader_origin_allowlist.json"
    allowlist.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "origin_family": "liquidity_sweep_reclaim",
                        "candidate_origin_family": "origin_liquidity_sweep_reclaim",
                        "symbol": "XAUUSD",
                        "route_session": "london",
                        "side": "LONG",
                        "selected_policy": "partial_be_runner",
                        "proof_class": "positive_origin_native_dynamic_replay_row_level_proof",
                        "activation_action": "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE",
                        "metrics": {
                            "performance_rows": 144,
                            "expectancy_r": 0.27,
                            "profit_factor": 1.6,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    risk_ledger = tmp_path / "selected_cell_risk.jsonl"
    risk_ledger.write_text(
        json.dumps(
            {
                "record_type": "redacted_account_selected_cell_risk",
                "selector_component": "broader_origin",
                "risk_cell_id": "risk-unresolved-commission",
                "symbol": "XAUUSD",
                "family": "liquidity_sweep_reclaim",
                "candidate_origin_family": "origin_liquidity_sweep_reclaim",
                "route_session": "london",
                "session_bucket": "london",
                "side": "LONG",
                "selected_policy": "partial_be_runner",
                "effective_risk_per_trade_pct": 0.25,
                "risk_decision_basis": "vnext_cell_evidence_tier:micro_positive_ev_floor;no_spread_cap;redacted_account_5pct_daily_10pct_static",
                "exact_unresolved_or_excluded_reasons": [
                    "commission_fields_not_exposed_in_current_symbol_info_snapshot"
                ],
                "source_effective_config_status": "broker_native_geometry_bound",
                "effective_price_rounding_increment": 0.01,
                "effective_lot_rounding_step": 0.01,
                "price_rounding_policy": {"status": "verified_from_broker_spec"},
                "volume_rounding_policy": {"status": "verified_from_broker_spec"},
                "uses_unverified_default": False,
                "stale_old_profile_risk_without_cell_evidence": False,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    decision = GTOSVNextRuntimeDecision(
        decision="LEGACY",
        event={
            "symbol": "XAUUSD",
            "side": "LONG",
            "framework": "liquidity_sweep_reclaim",
            "candidate_origin_family": "origin_liquidity_sweep_reclaim",
            "route_session": "london",
        },
        enabled=True,
        apply_to_execution=True,
        matched=False,
        reason="broader_origin_candidate_contract",
        evidence={"matched_rows": 0},
    )
    cfg = {
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
            "moonshot_dynamic_execution_router_policy": "momentum_exhaustion",
            "moonshot_dynamic_execution_router_condition_challenger_enabled": True,
            "moonshot_dynamic_execution_router_condition_challenger_policy": (
                "condition_asof_displacement_v1"
            ),
            "moonshot_dynamic_execution_router_momentum_exception_policy": (
                "partial_be_runner"
            ),
            "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner": [
                "liquidity_sweep_reclaim"
            ],
            "moonshot_dynamic_execution_router_allow_policy_invariant_selected_cell_risk_geometry": True,
            "moonshot_dynamic_execution_router_activated_origin_families": [
                "liquidity_sweep_reclaim",
            ],
            "moonshot_dynamic_execution_router_broker_native_eligible_symbols": ["XAUUSD"],
            "moonshot_dynamic_execution_router_required_branch_labels": ["FOLLOW"],
            "moonshot_dynamic_execution_router_broader_origin_allowlist_path": str(allowlist),
            "moonshot_dynamic_execution_router_require_selected_cell_risk_ledger": True,
            "moonshot_dynamic_execution_router_selected_cell_risk_ledger_path": str(risk_ledger),
        },
    }

    routed = evaluate_vnext_moonshot_dynamic_execution(
        decision=decision,
        config=cfg,
        candidate_context={
            "kill_zone_position": "in_london_early",
            "live_generation_status": "generated_live_asof",
        },
    )

    assert routed.applied is True
    assert "selected_cell_risk_not_verified_or_zero" not in routed.refusal_reasons
    assert routed.source_event["selected_cell_risk_match_reason"] == (
        "exact_selected_cell_risk_positive_match"
    )
    assert routed.source_event["selected_cell_risk_allowed"] is True
    assert routed.source_event["selected_cell_risk_unresolved_reasons"] == []
    assert routed.source_event["selected_cell_risk_source_row_identity"][
        "exact_unresolved_or_excluded_reasons"
    ] == ["commission_fields_not_exposed_in_current_symbol_info_snapshot"]


def test_moonshot_dynamic_execution_rejects_zero_selected_cell_risk(tmp_path) -> None:
    allowlist = tmp_path / "stage13_broader_origin_allowlist.json"
    allowlist.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "origin_family": "liquidity_sweep_reclaim",
                        "candidate_origin_family": "origin_liquidity_sweep_reclaim",
                        "symbol": "XAUUSD",
                        "route_session": "london",
                        "side": "LONG",
                        "selected_policy": "be_after_trigger",
                        "proof_class": "positive_origin_native_dynamic_replay_row_level_proof",
                        "activation_action": "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE",
                        "metrics": {
                            "performance_rows": 144,
                            "expectancy_r": 0.27,
                            "profit_factor": 1.6,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    risk_ledger = tmp_path / "selected_cell_risk.jsonl"
    risk_ledger.write_text(
        json.dumps(
            {
                "record_type": "redacted_account_selected_cell_risk",
                "selector_component": "broader_origin",
                "risk_cell_id": "risk-zero-1",
                "symbol": "XAUUSD",
                "family": "liquidity_sweep_reclaim",
                "candidate_origin_family": "origin_liquidity_sweep_reclaim",
                "route_session": "london",
                "session_bucket": "london",
                "side": "LONG",
                "selected_policy": "be_after_trigger",
                "effective_risk_per_trade_pct": 0.0,
                "risk_decision_basis": "risk_zero_spread_cost_exceeds_20pct_of_median_sl",
                "exact_unresolved_or_excluded_reasons": [
                    "risk_zero_spread_cost_exceeds_20pct_of_median_sl"
                ],
                "source_effective_config_status": "broker_native_geometry_bound",
                "effective_price_rounding_increment": 0.01,
                "effective_lot_rounding_step": 0.01,
                "price_rounding_policy": {"status": "verified_from_broker_spec"},
                "volume_rounding_policy": {"status": "verified_from_broker_spec"},
                "uses_unverified_default": False,
                "stale_old_profile_risk_without_cell_evidence": False,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    decision = GTOSVNextRuntimeDecision(
        decision="LEGACY",
        event={
            "symbol": "XAUUSD",
            "side": "LONG",
            "framework": "liquidity_sweep_reclaim",
            "candidate_origin_family": "origin_liquidity_sweep_reclaim",
            "route_session": "london",
        },
        enabled=True,
        apply_to_execution=True,
        matched=False,
        reason="broader_origin_candidate_contract",
        evidence={"matched_rows": 0},
    )
    cfg = {
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
            "moonshot_dynamic_execution_router_policy": "momentum_exhaustion",
            "moonshot_dynamic_execution_router_condition_challenger_enabled": True,
            "moonshot_dynamic_execution_router_condition_challenger_policy": (
                "condition_asof_displacement_v1"
            ),
            "moonshot_dynamic_execution_router_momentum_exception_policy": (
                "partial_be_runner"
            ),
            "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner": [
                "liquidity_sweep_reclaim"
            ],
            "moonshot_dynamic_execution_router_allow_policy_invariant_selected_cell_risk_geometry": True,
            "moonshot_dynamic_execution_router_activated_origin_families": [
                "liquidity_sweep_reclaim",
            ],
            "moonshot_dynamic_execution_router_broker_native_eligible_symbols": ["XAUUSD"],
            "moonshot_dynamic_execution_router_required_branch_labels": ["FOLLOW"],
            "moonshot_dynamic_execution_router_broader_origin_allowlist_path": str(allowlist),
            "moonshot_dynamic_execution_router_require_selected_cell_risk_ledger": True,
            "moonshot_dynamic_execution_router_selected_cell_risk_ledger_path": str(risk_ledger),
        },
    }

    routed = evaluate_vnext_moonshot_dynamic_execution(
        decision=decision,
        config=cfg,
        candidate_context={
            "kill_zone_position": "in_london_early",
            "live_generation_status": "generated_live_asof",
        },
    )

    assert routed.applied is False
    assert "selected_cell_risk_not_verified_or_zero" in routed.refusal_reasons
    assert routed.source_event["selected_cell_risk_match_reason"] == (
        "matching_selected_cell_risk_zero_or_unresolved"
    )


def test_moonshot_dynamic_execution_no_selected_cell_symbol_match_does_not_borrow_other_symbol_nearest(
    tmp_path,
) -> None:
    allowlist = tmp_path / "stage13_broader_origin_allowlist.json"
    allowlist.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "origin_family": "structural_distance_extreme",
                        "candidate_origin_family": "origin_structural_distance_extreme",
                        "symbol": "UKOIL_cash",
                        "route_session": "london",
                        "side": "SHORT",
                        "selected_policy": "be_after_trigger",
                        "proof_class": "positive_origin_native_dynamic_replay_row_level_proof",
                        "activation_action": "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE",
                        "metrics": {
                            "performance_rows": 144,
                            "expectancy_r": 0.27,
                            "profit_factor": 1.6,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    risk_ledger = tmp_path / "selected_cell_risk.jsonl"
    risk_ledger.write_text(
        json.dumps(
            {
                "record_type": "redacted_account_selected_cell_risk",
                "selector_component": "broader_origin",
                "risk_cell_id": "risk-audjpy-same-dims",
                "symbol": "AUDJPY",
                "family": "structural_distance_extreme",
                "candidate_origin_family": "origin_structural_distance_extreme",
                "route_session": "london",
                "session_bucket": "london",
                "side": "SHORT",
                "selected_policy": "be_after_trigger",
                "effective_risk_per_trade_pct": 0.0,
                "risk_decision_basis": "risk_zero_execution_critical_evidence_unresolved",
                "exact_unresolved_or_excluded_reasons": [
                    "risk_zero_execution_critical_evidence_unresolved"
                ],
                "source_effective_config_status": "broker_native_geometry_bound",
                "effective_price_rounding_increment": 0.001,
                "effective_lot_rounding_step": 0.01,
                "price_rounding_policy": {"status": "verified_from_broker_spec"},
                "volume_rounding_policy": {"status": "verified_from_broker_spec"},
                "uses_unverified_default": False,
                "stale_old_profile_risk_without_cell_evidence": False,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    decision = GTOSVNextRuntimeDecision(
        decision="LEGACY",
        event={
            "symbol": "UKOIL_cash",
            "side": "SHORT",
            "framework": "origin_structural_distance_extreme",
            "candidate_origin_family": "origin_structural_distance_extreme",
            "route_session": "london",
            "utc_hour_bucket": "h08_09",
        },
        enabled=True,
        apply_to_execution=True,
        matched=False,
        reason="broader_origin_candidate_contract",
        evidence={"matched_rows": 0},
    )
    cfg = {
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
            "moonshot_dynamic_execution_router_policy": "momentum_exhaustion",
            "moonshot_dynamic_execution_router_condition_challenger_enabled": True,
            "moonshot_dynamic_execution_router_condition_challenger_policy": (
                "condition_asof_displacement_v1"
            ),
            "moonshot_dynamic_execution_router_momentum_exception_policy": (
                "partial_be_runner"
            ),
            "moonshot_dynamic_execution_router_allow_policy_invariant_selected_cell_risk_geometry": True,
            "moonshot_dynamic_execution_router_activated_origin_families": [
                "structural_distance_extreme",
            ],
            "moonshot_dynamic_execution_router_broker_native_eligible_symbols": ["UKOIL_cash"],
            "moonshot_dynamic_execution_router_required_branch_labels": ["FOLLOW"],
            "moonshot_dynamic_execution_router_broader_origin_allowlist_path": str(allowlist),
            "moonshot_dynamic_execution_router_require_selected_cell_risk_ledger": True,
            "moonshot_dynamic_execution_router_selected_cell_risk_ledger_path": str(risk_ledger),
        },
    }

    routed = evaluate_vnext_moonshot_dynamic_execution(
        decision=decision,
        config=cfg,
        candidate_context={
            "kill_zone_position": "in_london",
            "live_generation_status": "generated_live_asof",
        },
    )

    assert routed.applied is False
    assert "selected_cell_risk_not_verified_or_zero" in routed.refusal_reasons
    assert routed.source_event["selected_cell_risk_refusal_cause"] == (
        "selected_cell_risk_symbol_absent_from_ledger"
    )
    assert routed.source_event["selected_cell_risk_nearest_candidate"] == {
        "status": "not_available",
        "reason": "no_same_symbol_selected_cell_risk_rows",
        "symbol": "UKOIL_CASH",
    }
    assert routed.source_event["selected_cell_risk_failed_dimensions"] == [
        {
            "field": "symbol",
            "live": "UKOIL_CASH",
            "risk_row": None,
            "reason": "symbol_not_present_in_selected_cell_risk_ledger",
        }
    ]


def test_moonshot_dynamic_execution_rejects_weak_broader_origin_allowlist_rows(tmp_path) -> None:
    allowlist = tmp_path / "weak_broader_origin_allowlist.json"
    allowlist.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "origin_family": "liquidity_sweep_reclaim",
                        "candidate_origin_family": "origin_liquidity_sweep_reclaim",
                        "symbol": "XAUUSD",
                        "route_session": "london",
                        "side": "LONG",
                        "selected_policy": "trailing_runner",
                        "proof_class": "positive_origin_native_dynamic_replay_row_level_proof",
                        "activation_action": "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE",
                        "metrics": {
                            "performance_rows": 144,
                            "expectancy_r": 0.27,
                            "profit_factor": 1.6,
                        },
                    },
                    {
                        "origin_family": "liquidity_sweep_reclaim",
                        "candidate_origin_family": "origin_liquidity_sweep_reclaim",
                        "symbol": "XAUUSD",
                        "route_session": "london",
                        "side": "LONG",
                        "selected_policy": "be_after_trigger",
                        "proof_class": "broad_label_not_row_level_proof",
                        "activation_action": "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE",
                        "metrics": {
                            "performance_rows": 144,
                            "expectancy_r": 0.27,
                            "profit_factor": 1.6,
                        },
                    },
                    {
                        "origin_family": "liquidity_sweep_reclaim",
                        "candidate_origin_family": "origin_liquidity_sweep_reclaim",
                        "symbol": "XAUUSD",
                        "route_session": "london",
                        "side": "LONG",
                        "selected_policy": "be_after_trigger",
                        "proof_class": "positive_origin_native_dynamic_replay_row_level_proof",
                        "activation_action": "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE",
                        "metrics": {
                            "performance_rows": 19,
                            "expectancy_r": 0.27,
                            "profit_factor": 1.6,
                        },
                    },
                    {
                        "origin_family": "liquidity_sweep_reclaim",
                        "candidate_origin_family": "origin_liquidity_sweep_reclaim",
                        "symbol": "XAUUSD",
                        "route_session": "london",
                        "side": "LONG",
                        "selected_policy": "be_after_trigger",
                        "proof_class": "positive_origin_native_dynamic_replay_row_level_proof",
                        "activation_action": "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE",
                        "metrics": {
                            "performance_rows": 144,
                            "expectancy_r": 0.27,
                            "profit_factor": 1.0,
                        },
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    decision = GTOSVNextRuntimeDecision(
        decision="LEGACY",
        event={
            "symbol": "XAUUSD",
            "side": "LONG",
            "framework": "liquidity_sweep_reclaim",
            "candidate_origin_family": "origin_liquidity_sweep_reclaim",
            "route_session": "london",
        },
        enabled=True,
        apply_to_execution=True,
        matched=False,
        reason="broader_origin_candidate_contract",
        evidence={"matched_rows": 0},
    )
    cfg = {
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
            "moonshot_dynamic_execution_router_activated_origin_families": [
                "liquidity_sweep_reclaim",
            ],
            "moonshot_dynamic_execution_router_broker_native_eligible_symbols": ["XAUUSD"],
            "moonshot_dynamic_execution_router_required_branch_labels": ["FOLLOW"],
            "moonshot_dynamic_execution_router_broader_origin_allowlist_path": str(allowlist),
            "moonshot_dynamic_execution_router_broader_origin_min_group_rows": 20,
            "moonshot_dynamic_execution_router_policy": "be_after_trigger",
        },
    }

    routed = evaluate_vnext_moonshot_dynamic_execution(
        decision=decision,
        config=cfg,
        candidate_context={"kill_zone_position": "in_london_early"},
    )

    assert routed.applied is False
    assert routed.source_event["broader_origin_allowed"] is False
    assert "branch_semantics_not_follow_or_repaired" in routed.refusal_reasons


def test_moonshot_dynamic_execution_rejects_weak_repaired_branch_allowlist_rows(tmp_path) -> None:
    allowlist = tmp_path / "weak_repaired_branch_allowlist.json"
    allowlist.write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "symbol": "UK100",
                        "framework": "ob_retest",
                        "candidate_origin_family": "origin_current_ob_retest",
                        "session_bucket": "london_broad",
                        "kill_zone_bucket": "in_london_repo_schedule_repaired",
                        "allowed_prior_branch_labels": ["LEGACY"],
                        "repaired_branch_action": "MOONSHOT_REPAIRED_FOLLOW",
                        "proof_class": "positive_executable_repaired_branch_semantics",
                        "repaired_branch_metrics": {
                            "performance_rows": 18,
                            "expectancy_r": 0.36,
                            "profit_factor": 2.06,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    decision = GTOSVNextRuntimeDecision(
        decision="LEGACY",
        event={"symbol": "UK100", "side": "LONG", "framework": "ob_retest", "route_session": "london"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="no_matching_vnext_route_scope",
        evidence={"matched_rows": 0},
    )
    cfg = {
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
            "moonshot_dynamic_execution_router_activated_frameworks": [
                "breaker_re_entry",
                "fvg_fill",
                "ob_retest",
            ],
            "moonshot_dynamic_execution_router_broker_native_eligible_symbols": ["UK100"],
            "moonshot_dynamic_execution_router_required_branch_labels": ["FOLLOW"],
            "moonshot_dynamic_execution_router_repaired_branch_allowlist_path": str(allowlist),
            "moonshot_dynamic_execution_router_repaired_branch_min_rows": 20,
        },
    }

    routed = evaluate_vnext_moonshot_dynamic_execution(
        decision=decision,
        config=cfg,
        candidate_context={
            "candidate_origin_family": "origin_current_ob_retest",
            "candle_time_utc": "2026-01-02T08:30:00+00:00",
            "kill_zone_position": "in_london_repo_schedule_repaired",
        },
    )

    assert routed.applied is False
    assert routed.source_event["repaired_branch_allowed"] is False
    assert "branch_semantics_not_follow_or_repaired" in routed.refusal_reasons


def test_moonshot_dynamic_execution_ignores_condition_mode_when_config_disabled() -> None:
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={
            "symbol": "XAUUSD",
            "side": "LONG",
            "framework": "fvg_fill",
            "route_session": "ny",
            "policy_router_mode": "condition_asof_displacement_v1",
        },
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched_vnext_route_scope",
        evidence={"matched_rows": 3},
    )
    cfg = {
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
            "moonshot_dynamic_execution_router_condition_challenger_enabled": False,
        },
    }

    routed = evaluate_vnext_moonshot_dynamic_execution(
        decision=decision,
        config=cfg,
        candidate_context={
            "current_bar_displacement_atr14": 1.3,
            "kill_zone_position": "in_ny_early",
        },
    )

    assert routed.selected_policy == "momentum_exhaustion"
    assert routed.source_event["condition_challenger_enabled"] is False
    assert "policy_router_mode" not in routed.source_event


def test_moonshot_dynamic_execution_requires_real_kz_schedule_when_configured() -> None:
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD", "side": "LONG", "framework": "fvg_fill", "route_session": "ny"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched_vnext_route_scope",
        evidence={"matched_rows": 3},
    )
    cfg = {
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
            "moonshot_dynamic_execution_router_require_configured_kill_zone": True,
        },
    }

    routed = evaluate_vnext_moonshot_dynamic_execution(
        decision=decision,
        config=cfg,
        candidate_context={"kill_zone": "ny"},
    )

    assert routed.applied is False
    assert "kill_zone_position" not in routed.source_event
    assert "outside_configured_kill_zone_or_missing_schedule" in routed.refusal_reasons


def test_moonshot_dynamic_execution_same_bar_ambiguity_refuses_activation() -> None:
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD", "side": "LONG", "framework": "fvg_fill", "route_session": "london"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched_vnext_route_scope",
        evidence={"matched_rows": 3},
    )
    cfg = {
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
        },
    }

    routed = evaluate_vnext_moonshot_dynamic_execution(
        decision=decision,
        config=cfg,
        candidate_context={"same_bar_ambiguous": True},
    )

    assert routed.decision_status == "refuse_live_use_until_source_or_scope_repaired"
    assert routed.applied is False
    assert "selected_policy_ordered_ltf_or_tick_path_required" in routed.refusal_reasons


def test_vnext_replacement_monitoring_snapshot_records_stage10_surfaces(tmp_path) -> None:
    cfg = {
        "gtos_vnext_runtime": {
            "enabled": True,
            "mode": "shadow",
            "apply_to_execution": True,
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
            "replacement_monitoring_enabled": True,
            "replacement_monitoring_log_enabled": True,
            "replacement_ml_apply_to_execution": False,
            "replacement_ml_role_source_manifest": (
                "research/science_program_2026_05/06_outcome_testing/"
                "vnext_activation_edge_anatomy_ai_budget_ml_feasibility_2026_05_26/"
                "VNEXT_ACTIVATION_ML_CHALLENGER_RESULTS_2026-05-26.json"
            ),
            "replacement_ml_role_keys": [
                "ai_call_reducer",
                "source_confidence_scorer",
                "partition_robustness_scorer",
                "timeout_ambiguous_monitor",
                "drift_detector",
            ],
        }
    }
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={
            "symbol": "XAUUSD",
            "side": "LONG",
            "framework": "fvg_fill",
            "route_session": "ny",
        },
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched_vnext_route_scope",
        evidence={
            "matched_rows": 5,
            "decision_group_counts": {"FOLLOW": 4, "AVOID": 1},
            "source_component_decision_counts": {"gtos_vnext_cp280": {"FOLLOW": 4}},
            "metrics": {
                "cost_adjusted_simulated_r": {"sum": 9.0},
                "proxy_score": {"sum": 3.5},
                "stress_simulated_r": {"sum": 7.0},
                "effective_n": {"sum": 42},
            },
        },
    )
    pre_ai = GTOSVNextPreAIRoutingDecision(
        action="NARROW_AI_TO_ROUTE",
        would_action="NARROW_AI_TO_ROUTE",
        decision="FOLLOW",
        enabled=True,
        apply_to_ai_call=False,
        reason="matched_pre_ai_vnext_scope",
        event={"symbol": "XAUUSD"},
        recommended_side="LONG",
        recommended_frameworks=("fvg_fill",),
    )
    ai_policy = GTOSVNextAIPolicyDecision(
        action="CALL_AI_CURRENT_PATH",
        would_action="CALL_AI_CONSTRAINED_VALIDATOR",
        allowed=True,
        would_allow_ai_call=True,
        enabled=True,
        apply_to_ai_call=False,
        reason="shadow_ai_validator_only",
        ai_role="validator_only",
    )
    risk = GTOSVNextRiskAdjustment(
        enabled=True,
        apply_to_execution=True,
        applied=True,
        decision="FOLLOW",
        before_risk_pct=2.0,
        after_risk_pct=1.5,
        multiplier=0.75,
        would_multiplier=0.75,
        reason="vnext_risk_follow_conflicted",
    )
    pending = GTOSVNextPendingPolicy(
        action="PLACE_LIMIT",
        would_action="PLACE_LIMIT",
        enabled=True,
        apply_to_execution=True,
        applied=False,
        decision="FOLLOW",
        reason="vnext_pending_policy_default_limit",
    )
    ltf = GTOSVNextLTFPathExecutionDecision(
        action="MONITOR_LTF_PATH",
        would_action="MONITOR_LTF_PATH",
        enabled=True,
        apply_to_execution=True,
        applied=True,
        decision="FOLLOW",
        reason="vnext_ltf_path_monitor_until_touch_or_invalidation",
        monitor_timeframe="M1",
        path_state={"source_complete": True, "same_bar_ambiguous": False},
    )
    prop = GTOSVNextPropSafeSelectorDecision(
        action="ALLOW",
        would_action="REDUCE_RISK",
        enabled=True,
        apply_to_execution=False,
        applied=False,
        decision="FOLLOW",
        before_risk_pct=1.5,
        after_risk_pct=1.5,
        max_allowed_new_trade_risk_pct=1.0,
        reason="shadow_prop_safe_selector_reduce_risk",
        external_rule_projection={"remaining_daily_cushion": 3200.0},
    )
    dynamic = GTOSVNextMoonshotDynamicExecutionDecision(
        enabled=True,
        apply_to_execution=True,
        applied=True,
        decision_status="vnext_candidate_ready",
        candidate_action="TRADE_VNEXT_ACTIVATED_CANDIDATE",
        selected_branch="origin_current_fvg_fill",
        selected_policy="be_after_trigger",
        replaced_policy="retired_static_baseline_comparator",
        fixed_target_role="baseline_comparator_only",
        prop_action="ALLOW_UNLESS_EXTERNAL_PROP_GOVERNOR_BLOCKS",
        ai_role="MECHANICAL_PRIMARY_AI_VALIDATES_ONLY_AMBIGUOUS_SOURCE_OR_CONFLICT",
        source_quality_action="SOURCE_OK_FOR_DEFAULT_OFF_REPLAY",
        exit_management_action="REPLACE_RETIRED_STATIC_BASELINE_WITH_BE_AFTER_TRIGGER_DEFAULT_OFF",
        runtime_effect_now=True,
        candidate_use_allowed_now=True,
        source_event={
            "source_mode": "OHLC_M1_CSV",
            "source_window_complete": True,
            "ordered_path_status": "ordered_path_not_ambiguous_in_m15_replay",
            "selected_cell_risk_required": True,
            "selected_cell_risk_allowed": False,
            "selected_cell_risk_cell_id": "risk_cell_test",
            "selected_cell_risk_decision_basis": "risk_zero_test_basis",
            "selected_cell_risk_refusal_cause": "zero_risk_row",
            "selected_cell_risk_source_row_identity": {
                "risk_cell_id": "risk_cell_test",
                "effective_risk_per_trade_pct": 0.0,
            },
            "m15_source_fields": {"sweep_direction": "reclaim"},
            "tick_snapshot": {"available": True, "bid": 100.0, "ask": 100.1},
        },
    )

    snapshot = build_vnext_replacement_monitoring_snapshot(
        config=cfg,
        phase="post_l2_replacement_candidate",
        symbol="XAUUSD",
        kill_zone="ny",
        candle_time_utc="2026-05-26T13:15:00Z",
        vnext_decision=decision,
        vnext_pre_ai=pre_ai,
        vnext_ai_policy=ai_policy,
        vnext_risk_adjustment=risk,
        vnext_pending_policy=pending,
        vnext_ltf_path_execution=ltf,
        vnext_prop_safe_selector=prop,
        vnext_moonshot_dynamic_execution=dynamic,
        malformed_ai_summary={"row_count": 0},
    )

    assert isinstance(snapshot, GTOSVNextReplacementMonitoringSnapshot)
    assert snapshot.vnext_apply_status["global_apply_to_execution"] is True
    assert snapshot.vnext_apply_status["ml_apply_to_execution"] is False
    assert snapshot.router_decision["dynamic_selected_policy"] == "be_after_trigger"
    assert snapshot.execution_effects["risk_multiplier"] == 0.75
    assert snapshot.execution_effects["cost_adjusted_simulated_r_sum"] == 9.0
    assert snapshot.dynamic_exit_transition["replaces_retired_static_baseline"] is True
    assert snapshot.ltf_pending_monitor_health["source_complete"] is True
    assert snapshot.prop_budget_projection["external_rule_projection"][
        "remaining_daily_cushion"
    ] == 3200.0
    assert snapshot.source_capture_completeness["source_window_complete"] is True
    assert snapshot.source_capture_completeness["m15_source_fields"]["sweep_direction"] == (
        "reclaim"
    )
    assert snapshot.source_capture_completeness["tick_snapshot"]["available"] is True
    assert snapshot.source_capture_completeness["selected_cell_risk"] == {
        "selected_cell_risk_required": True,
        "selected_cell_risk_allowed": False,
        "selected_cell_risk_cell_id": "risk_cell_test",
        "selected_cell_risk_decision_basis": "risk_zero_test_basis",
        "selected_cell_risk_refusal_cause": "zero_risk_row",
        "selected_cell_risk_source_row_identity": {
            "risk_cell_id": "risk_cell_test",
            "effective_risk_per_trade_pct": 0.0,
        },
    }
    assert snapshot.old_live_fallback_leakage["leakage_detected"] is False
    assert set(snapshot.ml_assistant_roles["roles"]) == {
        "ai_call_reducer",
        "source_confidence_scorer",
        "partition_robustness_scorer",
        "timeout_ambiguous_monitor",
        "drift_detector",
    }

    record = {}
    attach_vnext_replacement_monitoring_to_record(record, snapshot)
    assert record["decision_pipeline"]["gtos_vnext_replacement_monitoring"][
        "schema_version"
    ] == "gtos_vnext_replacement_monitoring_v1"
    assert record["instrumentation"]["gtos_vnext_replacement_old_live_leakage"] is False

    log_path = tmp_path / "replacement_monitor.jsonl"
    record_vnext_replacement_monitoring_snapshot(
        snapshot=snapshot,
        config=cfg,
        log_path=log_path,
    )
    logged = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
    assert logged["schema_version"] == "gtos_vnext_replacement_monitoring_log_v1"
    assert logged["snapshot"]["dynamic_exit_transition"]["selected_policy"] == (
        "be_after_trigger"
    )


def test_vnext_replacement_monitoring_flags_old_live_fallback_leakage() -> None:
    cfg = {
        "gtos_vnext_runtime": {
            "enabled": True,
            "apply_to_execution": True,
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
        }
    }
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD", "side": "LONG"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched_vnext_route_scope",
        evidence={"matched_rows": 2},
    )

    snapshot = build_vnext_replacement_monitoring_snapshot(
        config=cfg,
        phase="post_l2_replacement_candidate",
        symbol="XAUUSD",
        kill_zone="ny",
        vnext_decision=decision,
        vnext_moonshot_dynamic_execution=None,
    )

    assert snapshot.old_live_fallback_leakage["leakage_detected"] is True
    assert "old_live_fallback_leakage_when_dynamic_overlay_requested" in snapshot.warnings


def test_vnext_replacement_monitoring_does_not_flag_dynamic_refusal_as_fallback() -> None:
    cfg = {
        "gtos_vnext_runtime": {
            "enabled": True,
            "apply_to_execution": True,
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
        }
    }
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD", "side": "LONG"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched_vnext_route_scope",
        evidence={"matched_rows": 2},
    )
    dynamic = GTOSVNextMoonshotDynamicExecutionDecision(
        enabled=True,
        apply_to_execution=True,
        applied=False,
        decision_status="vnext_candidate_refused_for_selected_cell_risk",
        candidate_action="SKIP_GTOS_VNEXT_DYNAMIC",
        selected_branch="origin_current_momentum_exhaustion",
        selected_policy="momentum_exhaustion",
        execution_policy_id="vnext_exec_momentum_1r_pullback_2r_dynamic_final",
        replaced_policy="retired_static_baseline_comparator",
        fixed_target_role="baseline_comparator_only",
        prop_action="BLOCK_SELECTED_CELL_RISK_UNVERIFIED",
        ai_role="MECHANICAL_PRIMARY_AI_VALIDATES_ONLY_AMBIGUOUS_SOURCE_OR_CONFLICT",
        source_quality_action="SOURCE_OK_FOR_DEFAULT_OFF_REPLAY",
        exit_management_action="DYNAMIC_ROUTER_REFUSED_BEFORE_ORDER_PLACEMENT",
        refusal_reasons=("selected_cell_risk_not_verified_or_zero",),
        runtime_effect_now=False,
        candidate_use_allowed_now=False,
    )

    snapshot = build_vnext_replacement_monitoring_snapshot(
        config=cfg,
        phase="broader_origin_pre_ai_candidate",
        symbol="XAUUSD",
        kill_zone="ny",
        vnext_decision=decision,
        vnext_moonshot_dynamic_execution=dynamic,
    )

    leakage = snapshot.old_live_fallback_leakage
    assert leakage["leakage_detected"] is False
    assert leakage["dynamic_decision_present"] is True
    assert leakage["dynamic_policy_applied"] is False
    assert leakage["dynamic_contains_old_live_fallback"] is True
    assert snapshot.dynamic_exit_transition["fixed_target_role"] == (
        "baseline_comparator_only"
    )
    assert "old_live_fallback_leakage_when_dynamic_overlay_requested" not in snapshot.warnings


def _prop_selector_cfg(**overrides):
    runtime = {
        "prop_safe_selector_enabled": True,
        "prop_safe_selector_apply_to_execution": True,
        "prop_safe_selector_initial_balance": 100000.0,
        "prop_safe_selector_external_daily_loss_limit_pct": 5.0,
        "prop_safe_selector_external_overall_max_loss_pct": 10.0,
        "prop_safe_selector_phase1_target_pct": 8.0,
        "prop_safe_selector_phase2_target_pct": 5.0,
        "prop_safe_selector_daily_reset_timezone_offset_hours": 3.0,
        "prop_safe_selector_malaysia_timezone_offset_hours": 8.0,
        "prop_safe_selector_spread_slippage_commission_buffer_pct": 0.0,
        "prop_safe_selector_min_reduced_risk_pct": 0.25,
        "prop_safe_selector_reserve_simultaneous_candidates": True,
        "prop_safe_selector_internal_daily_overlay_enabled": False,
        "prop_safe_selector_internal_overlay_applies_to_budget": True,
    }
    runtime.update(overrides)
    return {"risk": {"max_daily_loss_pct": 4.0}, "gtos_vnext_runtime": runtime}


def _prop_selector_decision(*, apply_to_execution=True):
    return GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD", "route_session": "ny_kz"},
        enabled=True,
        apply_to_execution=apply_to_execution,
        matched=True,
        reason="matched_vnext_prop_safe_selector_test",
        evidence={
            "matched_rows": 3,
            "metrics": {
                "cost_adjusted_simulated_r": {"sum": 3.0, "mean": 1.0},
                "stress_simulated_r": {"sum": 1.5, "mean": 0.5},
                "effective_n": {"sum": 30},
            },
        },
    )


def _prop_account(*, current_equity=100000.0, day_start=100000.0, **overrides):
    state = {
        "initial_balance": 100000.0,
        "current_balance": current_equity,
        "current_equity": current_equity,
        "risk_base_amount": 100000.0,
        "day_start_equity_or_balance_baseline": day_start,
        "open_position_risk_pct": 0.0,
        "pending_order_risk_pct": 0.0,
        "new_trade_sl_risk_pct": 1.0,
        "spread_slippage_commission_buffer_pct": 0.0,
        "correlated_exposure_buffer_pct": 0.0,
        "concentration_buffer_pct": 0.0,
        "day_trade_count": 0,
        "session_trade_count": 0,
        "symbol_day_trade_count": 0,
        "symbol_session_trade_count": 0,
        "simultaneous_candidate_count": 1,
        "symbol": "XAUUSD",
        "route_session": "ny_kz",
    }
    state.update(overrides)
    return state


def test_vnext_prop_safe_selector_reset_window_and_malaysia_conversion():
    decision = _prop_selector_decision()
    before_reset = evaluate_vnext_prop_safe_selector(
        decision=decision,
        config=_prop_selector_cfg(),
        current_risk_pct=1.0,
        account_state=_prop_account(),
        current_time_utc="2026-05-25T20:59:00+00:00",
    )
    after_reset = evaluate_vnext_prop_safe_selector(
        decision=decision,
        config=_prop_selector_cfg(),
        current_risk_pct=1.0,
        account_state=_prop_account(),
        current_time_utc="2026-05-25T21:01:00+00:00",
    )

    assert before_reset.reset_window["next_reset_utc"] == "2026-05-25T21:00:00+00:00"
    assert before_reset.reset_window["next_reset_malaysia_time"] == (
        "2026-05-26T05:00:00+08:00"
    )
    assert before_reset.reset_window["daily_loss_reset_model"] == "00:00_GMT_PLUS_3"
    assert after_reset.reset_window["reset_window_start_utc"] == (
        "2026-05-25T21:00:00+00:00"
    )
    assert after_reset.reset_window["next_reset_utc"] == "2026-05-26T21:00:00+00:00"


def test_vnext_prop_safe_selector_intraday_profit_increases_daily_cushion_to_7000():
    selector = evaluate_vnext_prop_safe_selector(
        decision=_prop_selector_decision(),
        config=_prop_selector_cfg(),
        current_risk_pct=1.0,
        account_state=_prop_account(current_equity=102000.0),
        current_time_utc="2026-05-25T12:00:00+00:00",
    )

    assert selector.action == "ALLOW"
    assert selector.would_action == "ALLOW"
    assert selector.external_rule_projection["daily_loss_amount"] == 5000.0
    assert selector.external_rule_projection["daily_floor"] == 95000.0
    assert selector.external_rule_projection["remaining_daily_cushion"] == 7000.0
    record = selector.to_record()
    assert len(record["risk_packet_hash_sha256"]) == 64
    assert record["risk_packet_source_status"] == "source_bound_risk_packet_complete"
    assert record["risk_packet_field_groups"]["daily_and_overall_budget"]["status"] == (
        "source_bound"
    )


def test_vnext_prop_safe_selector_losing_day_reduces_cushion():
    selector = evaluate_vnext_prop_safe_selector(
        decision=_prop_selector_decision(),
        config=_prop_selector_cfg(),
        current_risk_pct=1.0,
        account_state=_prop_account(current_equity=97000.0),
        current_time_utc="2026-05-25T12:00:00+00:00",
    )

    assert selector.external_rule_projection["remaining_daily_cushion"] == 2000.0
    assert selector.external_rule_projection["projected_daily_cushion_after_full_risk"] == 1000.0
    assert selector.action == "ALLOW"


def test_vnext_prop_safe_selector_missing_day_start_baseline_blocks() -> None:
    account_state = _prop_account()
    account_state.pop("day_start_equity_or_balance_baseline")
    account_state.pop("day_start_equity", None)
    account_state.pop("day_start_balance", None)

    selector = evaluate_vnext_prop_safe_selector(
        decision=_prop_selector_decision(),
        config=_prop_selector_cfg(),
        current_risk_pct=1.0,
        account_state=account_state,
        current_time_utc="2026-05-25T12:00:00+00:00",
    )

    assert selector.action == "BLOCK"
    assert selector.reason == "prop_safe_selector_missing_day_start_baseline"
    assert selector.external_rule_projection["day_start_baseline_source"] == "missing_fail_closed"
    record = selector.to_record()
    assert record["risk_packet_source_status"] == "source_gap_fail_closed"
    assert "day_start_balance" in record["risk_packet_missing_fields"]


def test_vnext_prop_safe_selector_static_overall_floor_reduces_risk():
    selector = evaluate_vnext_prop_safe_selector(
        decision=_prop_selector_decision(),
        config=_prop_selector_cfg(),
        current_risk_pct=2.0,
        account_state=_prop_account(
            current_equity=91000.0,
            day_start=91000.0,
            new_trade_sl_risk_pct=2.0,
        ),
        current_time_utc="2026-05-25T12:00:00+00:00",
    )

    assert selector.external_rule_projection["max_loss_floor"] == 90000.0
    assert selector.external_rule_projection["remaining_overall_cushion"] == 1000.0
    assert selector.action == "REDUCE_RISK"
    assert selector.after_risk_pct == 1.0


def test_vnext_prop_safe_selector_current_equity_includes_open_floating_loss():
    selector = evaluate_vnext_prop_safe_selector(
        decision=_prop_selector_decision(),
        config=_prop_selector_cfg(),
        current_risk_pct=1.0,
        account_state=_prop_account(
            current_equity=96000.0,
            open_position_risk_pct=0.5,
            new_trade_sl_risk_pct=1.0,
        ),
        current_time_utc="2026-05-25T12:00:00+00:00",
    )

    assert selector.external_rule_projection["remaining_daily_cushion"] == 1000.0
    assert selector.exposure_breakdown["open_position_risk_amount"] == 500.0
    assert selector.action == "REDUCE_RISK"
    assert selector.after_risk_pct == 0.5


def test_vnext_prop_safe_selector_pending_risk_is_included():
    selector = evaluate_vnext_prop_safe_selector(
        decision=_prop_selector_decision(),
        config=_prop_selector_cfg(),
        current_risk_pct=1.0,
        account_state=_prop_account(
            pending_order_risk_pct=4.5,
            new_trade_sl_risk_pct=1.0,
        ),
        current_time_utc="2026-05-25T12:00:00+00:00",
    )

    assert selector.exposure_breakdown["pending_order_risk_amount"] == 4500.0
    assert selector.action == "REDUCE_RISK"
    assert selector.after_risk_pct == 0.5


def test_vnext_prop_safe_selector_multiple_simultaneous_candidates_reserve_budget():
    selector = evaluate_vnext_prop_safe_selector(
        decision=_prop_selector_decision(),
        config=_prop_selector_cfg(),
        current_risk_pct=2.0,
        account_state=_prop_account(
            new_trade_sl_risk_pct=2.0,
            simultaneous_candidate_count=3,
        ),
        current_time_utc="2026-05-25T12:00:00+00:00",
    )

    assert selector.exposure_breakdown["simultaneous_candidate_reserved_risk_amount"] == 4000.0
    assert selector.action == "REDUCE_RISK"
    assert selector.after_risk_pct == 1.0


def test_vnext_prop_safe_selector_correlated_exposure_buffer_reduces_risk():
    selector = evaluate_vnext_prop_safe_selector(
        decision=_prop_selector_decision(),
        config=_prop_selector_cfg(),
        current_risk_pct=1.0,
        account_state=_prop_account(
            correlated_exposure_buffer_pct=4.5,
            new_trade_sl_risk_pct=1.0,
        ),
        current_time_utc="2026-05-25T12:00:00+00:00",
    )

    assert selector.exposure_breakdown["correlated_exposure_buffer_amount"] == 4500.0
    assert selector.action == "REDUCE_RISK"
    assert selector.after_risk_pct == 0.5


def test_vnext_prop_safe_selector_reduces_risk_instead_of_blocking_when_budget_exists():
    selector = evaluate_vnext_prop_safe_selector(
        decision=_prop_selector_decision(),
        config=_prop_selector_cfg(),
        current_risk_pct=2.0,
        account_state=_prop_account(
            current_equity=96500.0,
            new_trade_sl_risk_pct=2.0,
        ),
        current_time_utc="2026-05-25T12:00:00+00:00",
    )

    assert selector.external_rule_projection["remaining_daily_cushion"] == 1500.0
    assert selector.action == "REDUCE_RISK"
    assert selector.after_risk_pct == 1.5


def test_vnext_prop_safe_selector_defers_until_reset_when_daily_budget_too_small():
    selector = evaluate_vnext_prop_safe_selector(
        decision=_prop_selector_decision(),
        config=_prop_selector_cfg(),
        current_risk_pct=1.0,
        account_state=_prop_account(
            current_equity=95200.0,
            new_trade_sl_risk_pct=1.0,
        ),
        current_time_utc="2026-05-25T12:00:00+00:00",
    )

    assert selector.external_rule_projection["remaining_daily_cushion"] == 200.0
    assert selector.action == "DEFER_UNTIL_RESET"
    assert selector.after_risk_pct == 0.0


def test_vnext_prop_safe_selector_blocks_only_when_projected_breach_exists():
    allow = evaluate_vnext_prop_safe_selector(
        decision=_prop_selector_decision(),
        config=_prop_selector_cfg(),
        current_risk_pct=1.0,
        account_state=_prop_account(),
        current_time_utc="2026-05-25T12:00:00+00:00",
    )
    block = evaluate_vnext_prop_safe_selector(
        decision=_prop_selector_decision(),
        config=_prop_selector_cfg(),
        current_risk_pct=1.0,
        account_state=_prop_account(current_equity=89000.0),
        current_time_utc="2026-05-25T12:00:00+00:00",
    )

    assert allow.action == "ALLOW"
    assert block.external_rule_projection["remaining_overall_cushion"] == -1000.0
    assert block.action == "BLOCK"


def test_vnext_prop_safe_selector_blocks_unverified_open_position_cash_risk():
    selector = evaluate_vnext_prop_safe_selector(
        decision=_prop_selector_decision(),
        config=_prop_selector_cfg(),
        current_risk_pct=1.0,
        account_state=_prop_account(
            open_position_count=1,
            open_position_risk_valued_count=0,
            open_position_risk_missing_count=1,
            open_position_risk_missing_positions=[
                {
                    "symbol": "GER40",
                    "ticket": 242667071,
                    "risk_amount_missing_reason": (
                        "position_profit_at_stop_broker_order_calc_profit_required_unavailable"
                    ),
                }
            ],
            new_trade_sl_risk_pct=1.0,
        ),
        current_time_utc="2026-05-25T12:00:00+00:00",
    )

    assert selector.action == "BLOCK"
    assert selector.would_action == "BLOCK"
    assert selector.reason == "prop_safe_selector_unverified_open_position_risk"
    assert selector.exposure_breakdown["unverified_open_position_risk_block"][
        "requirement"
    ] == "broker_order_calc_profit_cash_risk_for_all_open_positions"


def test_vnext_prop_safe_selector_shadow_mode_exposes_would_action_without_applying():
    selector = evaluate_vnext_prop_safe_selector(
        decision=_prop_selector_decision(apply_to_execution=False),
        config=_prop_selector_cfg(),
        current_risk_pct=2.0,
        account_state=_prop_account(current_equity=96500.0, new_trade_sl_risk_pct=2.0),
        current_time_utc="2026-05-25T12:00:00+00:00",
    )
    record = {}
    attach_vnext_prop_safe_selector_to_record(record, selector)

    assert selector.action == "ALLOW"
    assert selector.would_action == "REDUCE_RISK"
    assert selector.applied is False
    assert selector.reason.startswith("shadow_prop_safe_selector_reduce_risk")
    assert record["instrumentation"]["gtos_vnext_prop_safe_selector_would_action"] == "REDUCE_RISK"


def test_agent_config_wires_redacted_account_prop_safe_selector_production_activation_gate():
    config = yaml.safe_load(Path("config/agent_config.yaml").read_text(encoding="utf-8"))
    runtime = config["gtos_vnext_runtime"]

    assert runtime["prop_safe_selector_enabled"] is True
    assert runtime["prop_safe_selector_apply_to_execution"] is True
    assert runtime["prop_safe_selector_external_daily_loss_limit_pct"] == 5.0
    assert runtime["prop_safe_selector_external_overall_max_loss_pct"] == 10.0
    assert runtime["prop_safe_selector_daily_reset_timezone_offset_hours"] == 3.0
    assert runtime["prop_safe_selector_malaysia_timezone_offset_hours"] == 8.0
    assert runtime["prop_safe_selector_internal_daily_overlay_enabled"] is True
    assert runtime["prop_safe_selector_internal_daily_overlay_pct"] == 4.0

    selector = evaluate_vnext_prop_safe_selector(
        decision=_prop_selector_decision(apply_to_execution=True),
        config=config,
        current_risk_pct=2.0,
        account_state=_prop_account(current_equity=96500.0, new_trade_sl_risk_pct=2.0),
        current_time_utc="2026-05-25T12:00:00+00:00",
    )
    assert selector.action in {"REDUCE_RISK", "DEFER_UNTIL_RESET"}
    assert selector.would_action == selector.action
    assert selector.applied is True
    assert selector.internal_overlay_projection[
        "distinct_from_redacted_account_external_daily_limit"
    ] is True


def _ltf_decision(
    *,
    decision: str = "FOLLOW",
    apply_to_execution: bool = True,
    source_component_counts: dict | None = None,
    component_decisions: dict | None = None,
    proxy_counts: dict | None = None,
    target_stop_counts: dict | None = None,
) -> GTOSVNextRuntimeDecision:
    return GTOSVNextRuntimeDecision(
        decision=decision,
        event={"symbol": "XAUUSD", "side": "LONG", "route_session": "ny_kz"},
        enabled=True,
        apply_to_execution=apply_to_execution,
        matched=True,
        reason="matched_vnext_ltf_path_test",
        evidence={
            "matched_rows": sum((source_component_counts or {}).values()) or 1,
            "source_component_counts": source_component_counts or {},
            "source_component_decision_counts": component_decisions or {},
            "proxy_r_class_counts": proxy_counts or {},
            "target_stop_order_class_counts": target_stop_counts or {},
        },
    )


def _ltf_config(*, apply: bool) -> dict:
    return {
        "gtos_vnext_runtime": {
            "enabled": True,
            "apply_to_execution": True,
            "ltf_path_execution_enabled": True,
            "ltf_path_execution_apply_to_execution": apply,
            "ltf_path_execution_min_component_rows": 1,
            "ltf_path_monitor_timeframe": "M1",
            "ltf_path_market_entry_requires_path_touch": True,
            "ltf_path_adjusted_entry_enabled": True,
            "ltf_path_adjusted_entry_offset_r": 0.5,
        }
    }


def test_vnext_ltf_path_execution_shadow_and_active_skip_nofill():
    decision = _ltf_decision(
        decision="AVOID",
        source_component_counts={"nofill_far_miss_avoid": 3},
        component_decisions={"nofill_far_miss_avoid": {"AVOID": 3}},
        proxy_counts={"STRONG_NEGATIVE_PROXY_R": 3},
        target_stop_counts={"STOP_FIRST_PROXY_DOMINANT": 3},
    )

    shadow = evaluate_vnext_ltf_path_execution(
        decision=decision,
        config=_ltf_config(apply=False),
        path_state={"source_complete": True, "source_timeframe": "M1"},
    )
    active = evaluate_vnext_ltf_path_execution(
        decision=decision,
        config=_ltf_config(apply=True),
        path_state={"source_complete": True, "source_timeframe": "M1"},
    )
    record = {}
    attach_vnext_ltf_path_execution_to_record(record, shadow)

    assert shadow.action == "PLACE_LIMIT"
    assert shadow.would_action == "SKIP_LTF_NOFILL_AVOID"
    assert shadow.applied is False
    assert shadow.reason.startswith("shadow_vnext_ltf_path_nofill_avoid")
    assert active.action == "SKIP_LTF_NOFILL_AVOID"
    assert active.applied is True
    assert record["instrumentation"]["gtos_vnext_ltf_path_would_action"] == (
        "SKIP_LTF_NOFILL_AVOID"
    )


def test_vnext_ltf_path_execution_market_entry_requires_asof_touch():
    decision = _ltf_decision(
        decision="FOLLOW",
        source_component_counts={"nofill_near_miss_market_entry": 2},
        component_decisions={"nofill_near_miss_market_entry": {"FOLLOW": 2}},
        proxy_counts={"STRONG_POSITIVE_PROXY_R": 2},
        target_stop_counts={"TARGET_FIRST_PROXY_DOMINANT": 2},
    )

    monitor = evaluate_vnext_ltf_path_execution(
        decision=decision,
        config=_ltf_config(apply=True),
        path_state={
            "source_complete": True,
            "source_timeframe": "M1",
            "entry_touched": False,
            "approach_state": "monitoring",
        },
    )
    market = evaluate_vnext_ltf_path_execution(
        decision=decision,
        config=_ltf_config(apply=True),
        path_state={
            "source_complete": True,
            "source_timeframe": "M1",
            "entry_touched": True,
            "approach_state": "entry_touched",
        },
    )

    assert monitor.action == "MONITOR_LTF_PATH"
    assert monitor.reason == "vnext_ltf_path_monitor_until_touch_or_invalidation"
    assert market.action == "MARKET_ENTRY_NOW"
    assert market.reason == "vnext_ltf_path_market_entry_now"


def test_vnext_ltf_path_pre_entry_touch_monitors_instead_of_hard_skip():
    decision = _ltf_decision(
        decision="FOLLOW",
        source_component_counts={"main_orch24_structural_ltf_positive_follow": 1},
        component_decisions={"main_orch24_structural_ltf_positive_follow": {"FOLLOW": 1}},
    )

    target_before_entry = evaluate_vnext_ltf_path_execution(
        decision=decision,
        config=_ltf_config(apply=True),
        path_state={
            "source_complete": True,
            "source_timeframe": "M1",
            "target_touched_without_entry": True,
        },
    )
    protective_before_entry = evaluate_vnext_ltf_path_execution(
        decision=decision,
        config=_ltf_config(apply=True),
        path_state={
            "source_complete": True,
            "source_timeframe": "M1",
            "protective_touched_before_entry": True,
        },
    )

    assert target_before_entry.action == "MONITOR_LTF_PATH"
    assert target_before_entry.reason == "vnext_ltf_path_target_reached_without_entry_monitor"
    assert protective_before_entry.action == "MONITOR_LTF_PATH"
    assert (
        protective_before_entry.reason
        == "vnext_ltf_path_protective_area_before_entry_monitor"
    )


def test_vnext_ltf_path_execution_adjusts_limit_from_offset_evidence():
    decision = _ltf_decision(
        decision="AVOID",
        source_component_counts={"nofill_near_miss_offset": 4},
        component_decisions={"nofill_near_miss_offset": {"AVOID": 4}},
        proxy_counts={"STRONG_NEGATIVE_PROXY_R": 4},
    )
    ltf = evaluate_vnext_ltf_path_execution(
        decision=decision,
        config=_ltf_config(apply=True),
        trade_params={
            "direction": "LONG",
            "entry_price": 100.0,
            "stop_loss": 98.0,
            "take_profit_1": 103.0,
        },
        path_state={"source_complete": True, "source_timeframe": "M1"},
    )

    assert ltf.action == "ADJUST_LIMIT_ENTRY"
    assert ltf.adjusted_entry_price == 101.0
    assert ltf.evidence_summary["adjusted_entry_offset_r"] == 0.5


def test_agent_config_wires_ltf_path_execution_production_activation_gate():
    config = yaml.safe_load(Path("config/agent_config.yaml").read_text(encoding="utf-8"))
    runtime = config["gtos_vnext_runtime"]

    assert runtime["ltf_path_execution_enabled"] is True
    assert runtime["ltf_path_execution_apply_to_execution"] is True
    assert runtime["ltf_path_monitor_timeframe"] == "M1"
    assert runtime["ltf_path_monitor_pending_intent_enabled"] is True
    assert runtime["ltf_path_market_entry_requires_path_touch"] is True
    decision = _ltf_decision(
        decision="FOLLOW",
        source_component_counts={"nofill_near_miss_market_entry": 1},
        component_decisions={"nofill_near_miss_market_entry": {"FOLLOW": 1}},
        proxy_counts={"POSITIVE_PROXY_R": 1},
        target_stop_counts={"TARGET_FIRST_PROXY_DOMINANT": 1},
    )
    ltf = evaluate_vnext_ltf_path_execution(
        decision=decision,
        config=config,
        path_state={"source_complete": True, "entry_touched": True},
    )
    assert ltf.action == "MARKET_ENTRY_NOW"
    assert ltf.would_action == "MARKET_ENTRY_NOW"
    assert ltf.applied is True


def test_structured_decision_logger_writes_pre_ai_and_post_l2_rows(tmp_path):
    cfg = {"gtos_vnext_runtime": {"decision_log_path": str(tmp_path / "decisions.jsonl")}}
    record_vnext_runtime_decision(
        decision=GTOSVNextPreAIRoutingDecision(
            action="ALLOW_AI",
            decision="FOLLOW",
            enabled=True,
            apply_to_ai_call=False,
            reason="matched",
            event={"symbol": "GBPJPY"},
        ),
        config=cfg,
        phase="pre_ai",
        symbol="GBPJPY",
        kill_zone="tokyo",
        candle_time_utc="2026-05-18T00:15:00+00:00",
    )
    record_vnext_runtime_decision(
        decision=GTOSVNextRuntimeDecision(
            decision="FOLLOW",
            event={"symbol": "GBPJPY"},
            enabled=True,
            apply_to_execution=False,
            matched=True,
            reason="matched",
        ),
        config=cfg,
        phase="post_l2_candidate",
        symbol="GBPJPY",
        kill_zone="tokyo",
    )
    record_vnext_runtime_decision(
        decision=GTOSVNextMoonshotDynamicExecutionDecision(
            enabled=True,
            apply_to_execution=True,
            applied=False,
            decision_status="vnext_candidate_refused_for_selected_cell_risk",
            candidate_action="SKIP_GTOS_VNEXT_DYNAMIC",
            selected_branch="origin_current_momentum_exhaustion",
            selected_policy="partial_be_runner",
            execution_policy_id="vnext_exec_partial_50_at_1r_be_runner_to_3r",
            replaced_policy="retired_static_baseline_comparator",
            fixed_target_role="baseline_comparator_only",
            prop_action="BLOCK_SELECTED_CELL_RISK_UNVERIFIED",
            ai_role="MECHANICAL_PRIMARY_AI_VALIDATES_ONLY_AMBIGUOUS_SOURCE_OR_CONFLICT",
            source_quality_action="SOURCE_OK_FOR_DEFAULT_OFF_REPLAY",
            exit_management_action="DYNAMIC_ROUTER_REFUSED_BEFORE_ORDER_PLACEMENT",
            refusal_reasons=("selected_cell_risk_not_verified_or_zero",),
            runtime_effect_now=False,
            candidate_use_allowed_now=False,
            source_event={
                "candidate_id": "broadorigin_test",
                "symbol": "GBPJPY",
                "broker_symbol": "GBPJPY",
                "side": "LONG",
                "session": "tokyo",
                "kill_zone": "tokyo",
                "route_session": "tokyo",
                "origin_family": "liquidity_sweep_reclaim",
                "candidate_origin_family": "origin_liquidity_sweep_reclaim",
                "framework": "origin_liquidity_sweep_reclaim",
                "route_family": "broader_origin_configured_session",
                "broader_origin_allowed": True,
                "broader_origin_match_reason": "exact_stage13_broader_origin_allowlist_match",
                "broader_origin_source_row_identity": {
                    "symbol": "GBPJPY",
                    "origin_family": "liquidity_sweep_reclaim",
                },
                "selected_cell_risk_allowed": False,
                "selected_cell_risk_pct": None,
                "selected_cell_risk_cell_id": None,
                "selected_cell_risk_match_reason": "no_exact_selected_cell_risk_match",
                "selected_cell_risk_refusal_cause": "session_or_hour_key_mismatch",
                "selected_cell_risk_capture_contract": {
                    "status": "exact_selected_cell_source_row_capture_required",
                    "source_ledger_path": "selected_cell_risk.jsonl",
                },
                "candidate_quality_selector": {
                    "classification": "tradeable_now",
                    "refusal_reason": None,
                    "matched_rule": {"rule_id": "test_quality_rule"},
                },
                "broker_snapshot": {
                    "broker_symbol": "GBPJPY",
                    "server_time_utc": datetime(2026, 5, 18, 0, 15, tzinfo=timezone.utc),
                },
                "spread_r_at_candidate": 0.04,
                "source_mode": "LIVE_RAW_M15",
                "source_path_feature_status": "raw_data_m15_asof_complete",
                "source_window_complete": True,
                "ordered_path_status": "ordered_path_not_ambiguous",
                "selected_policy_ordered_path_status": "ordered_path_not_ambiguous",
            },
        ),
        config=cfg,
        phase="moonshot_dynamic_execution",
        symbol="GBPJPY",
        kill_zone="tokyo",
    )

    rows = [json.loads(line) for line in (tmp_path / "decisions.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [row["phase"] for row in rows] == [
        "pre_ai",
        "post_l2_candidate",
        "moonshot_dynamic_execution",
    ]
    assert rows[0]["decision"]["action"] == "ALLOW_AI"
    assert rows[1]["decision"]["decision"] == "FOLLOW"
    bridge = rows[2]["bridge_packet_summary"]
    assert bridge["candidate_id"] == "broadorigin_test"
    assert bridge["symbol"] == "GBPJPY"
    assert bridge["broker_symbol"] == "GBPJPY"
    assert bridge["side"] == "LONG"
    assert bridge["route_session"] == "tokyo"
    assert bridge["origin_family"] == "liquidity_sweep_reclaim"
    assert bridge["candidate_origin_family"] == "origin_liquidity_sweep_reclaim"
    assert bridge["framework"] == "origin_liquidity_sweep_reclaim"
    assert bridge["route_family"] == "broader_origin_configured_session"
    assert bridge["selected_policy"] == "partial_be_runner"
    assert bridge["source_quality_action"] == "SOURCE_OK_FOR_DEFAULT_OFF_REPLAY"
    assert bridge["prop_action"] == "BLOCK_SELECTED_CELL_RISK_UNVERIFIED"
    assert (
        bridge["exit_management_action"]
        == "DYNAMIC_ROUTER_REFUSED_BEFORE_ORDER_PLACEMENT"
    )
    assert bridge["candidate_quality_classification"] == "tradeable_now"
    assert bridge["candidate_quality_matched_rule_id"] == "test_quality_rule"
    assert bridge["selected_cell_risk_capture_contract"]["status"] == (
        "exact_selected_cell_source_row_capture_required"
    )
    assert bridge["source_completeness_state"]["source_path_feature_status"] == (
        "raw_data_m15_asof_complete"
    )
    assert bridge["broker_snapshot"]["server_time_utc"] == "2026-05-18T00:15:00+00:00"


def test_vnext_locked_jsonl_append_handles_concurrent_writers(tmp_path):
    log_path = tmp_path / "vnext_shared_runtime.jsonl"

    def write_row(index: int) -> None:
        vnext_runtime_mod._append_jsonl_locked(
            log_path,
            {
                "index": index,
                "payload": "x" * 4096,
                "schema_version": "test_locked_jsonl_append_v1",
            },
        )

    with ThreadPoolExecutor(max_workers=12) as pool:
        list(pool.map(write_row, range(120)))

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 120
    rows = [json.loads(line) for line in lines]
    assert sorted(row["index"] for row in rows) == list(range(120))


def test_vnext_execution_effect_is_ready_but_controlled_by_config():
    shadow_decision = GTOSVNextRuntimeDecision(
        decision="AVOID",
        event={},
        enabled=True,
        apply_to_execution=False,
        matched=True,
        reason="matched",
    )
    active_decision = GTOSVNextRuntimeDecision(
        decision="AVOID",
        event={},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={"metrics": {"effective_n": {"sum": 10}}},
    )
    weak_active_decision = GTOSVNextRuntimeDecision(
        decision="AVOID",
        event={},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={"metrics": {"effective_n": {"sum": 2}}},
    )
    missing_n_avoid = GTOSVNextRuntimeDecision(
        decision="AVOID",
        event={},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
    )

    assert vnext_blocks_execution(shadow_decision, {"gtos_vnext_runtime": {"avoid_blocks_execution": True}}) is False
    assert vnext_blocks_execution(active_decision, {"gtos_vnext_runtime": {"avoid_blocks_execution": True}}) is True
    assert vnext_blocks_execution(
        weak_active_decision,
        {"gtos_vnext_runtime": {"avoid_blocks_execution": True, "block_min_effective_n": 3}},
    ) is False
    assert (
        vnext_execution_block_reason(
            missing_n_avoid,
            {
                "gtos_vnext_runtime": {
                    "avoid_blocks_execution": True,
                    "risk_adjustment_enabled": True,
                    "risk_zero_blocks_execution": True,
                    "block_min_effective_n": 3,
                }
            },
        )
        is None
    )


def test_vnext_blocks_zero_risk_follow_execution_when_active():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 120,
            "metrics": {"effective_n": {"sum": 120}},
            "proxy_r_class_counts": {
                "STRONG_NEGATIVE_PROXY_R": 96,
                "NEGATIVE_PROXY_R": 20,
                "POSITIVE_PROXY_R": 12,
            },
        },
    )
    cfg = {
        "gtos_vnext_runtime": {
            "risk_adjustment_enabled": True,
            "risk_zero_blocks_execution": True,
            "execution_block_min_risk_multiplier": 0.000001,
            "strong_negative_proxy_risk_adjustment_enabled": True,
            "strong_negative_proxy_risk_min_rows": 20,
            "strong_negative_proxy_risk_dominance_ratio": 2.0,
            "strong_negative_proxy_risk_multiplier": 0.0,
        }
    }

    assert vnext_blocks_execution(decision, cfg) is True
    assert vnext_execution_block_reason(decision, cfg) == "vnext_risk_strong_negative_proxy_class"


def test_vnext_confidence_override_keeps_low_confidence_shadow_until_activation():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "GBPJPY"},
        enabled=True,
        apply_to_execution=False,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 2,
            "metrics": {
                "cost_adjusted_simulated_r": {"sum": 12.0, "mean": 6.0},
                "stress_simulated_r": {"sum": 10.0, "mean": 5.0},
                "effective_n": {"sum": 150, "mean": 75},
            },
        },
    )

    override = evaluate_vnext_confidence_override(
        decision=decision,
        confidence_grade="LOW",
        config={"gtos_vnext_runtime": {"confidence_override_enabled": True}},
    )
    record: dict = {}
    attach_vnext_confidence_override_to_record(record, override)

    assert override.would_apply is True
    assert override.applied is False
    assert override.reason == "shadow_vnext_confidence_override_strong_follow"
    assert record["decision_pipeline"]["gtos_vnext_confidence_override"]["would_apply"] is True
    assert record["instrumentation"]["gtos_vnext_confidence_override_applied"] is False


def test_vnext_confidence_override_applies_only_to_strong_active_follow():
    strong_follow = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "GBPJPY"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 2,
            "metrics": {
                "cost_adjusted_simulated_r": {"sum": 12.0, "mean": 6.0},
                "stress_simulated_r": {"sum": 10.0, "mean": 5.0},
                "effective_n": {"sum": 150, "mean": 75},
            },
        },
    )
    weak_follow = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "GBPJPY"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 1,
            "metrics": {
                "cost_adjusted_simulated_r": {"sum": 12.0, "mean": 12.0},
                "effective_n": {"sum": 2, "mean": 2},
            },
        },
    )

    active = evaluate_vnext_confidence_override(
        decision=strong_follow,
        confidence_grade="LOW",
        config={"gtos_vnext_runtime": {"confidence_override_enabled": True}},
    )
    not_low = evaluate_vnext_confidence_override(
        decision=strong_follow,
        confidence_grade="MEDIUM",
        config={"gtos_vnext_runtime": {"confidence_override_enabled": True}},
    )
    weak = evaluate_vnext_confidence_override(
        decision=weak_follow,
        confidence_grade="LOW",
        config={"gtos_vnext_runtime": {"confidence_override_enabled": True}},
    )

    assert active.applied is True
    assert active.reason == "vnext_confidence_override_strong_follow"
    assert active.evidence_summary["effective_n_sum"] == 150
    assert not_low.applied is False
    assert not_low.reason == "vnext_confidence_override_not_low_confidence"
    assert weak.applied is False
    assert weak.reason == "vnext_confidence_override_requires_strong_follow"


def test_vnext_confidence_override_accepts_strong_positive_proxy_class():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "USDJPY"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 25,
            "proxy_r_class_counts": {"STRONG_POSITIVE_PROXY_R": 25},
        },
    )

    override = evaluate_vnext_confidence_override(
        decision=decision,
        confidence_grade="LOW",
        config={"gtos_vnext_runtime": {"confidence_override_enabled": True}},
    )

    assert override.applied is True
    assert override.would_apply is True
    assert override.reason == "vnext_confidence_override_strong_positive_proxy"
    assert override.evidence_summary["strong_positive_proxy_r_rows"] == 25


def test_vnext_pending_policy_skips_nofill_avoid_only_when_active():
    decision = GTOSVNextRuntimeDecision(
        decision="MIXED",
        event={"symbol": "XAUUSD"},
        enabled=True,
        apply_to_execution=False,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 3,
            "source_component_counts": {
                "nofill_far_miss_avoid": 2,
                "nofill_far_miss_retest": 1,
            },
            "target_stop_order_class_counts": {"TARGET_FIRST_PROXY_DOMINANT": 2},
        },
    )
    shadow = evaluate_vnext_pending_policy(
        decision=decision,
        config={"gtos_vnext_runtime": {"pending_policy_enabled": True}},
    )
    active = evaluate_vnext_pending_policy(
        decision=GTOSVNextRuntimeDecision(
            decision=decision.decision,
            event=decision.event,
            enabled=True,
            apply_to_execution=True,
            matched=True,
            reason=decision.reason,
            evidence=decision.evidence,
        ),
        config={"gtos_vnext_runtime": {"pending_policy_enabled": True}},
    )
    record: dict = {}
    attach_vnext_pending_policy_to_record(record, shadow)

    assert shadow.action == "PLACE_LIMIT"
    assert shadow.would_action == "SKIP_PENDING_NOFILL_AVOID"
    assert shadow.applied is False
    assert shadow.reason == "shadow_vnext_pending_policy_nofill_avoid"
    assert active.action == "SKIP_PENDING_NOFILL_AVOID"
    assert active.applied is True
    assert active.reason == "vnext_pending_policy_nofill_avoid"
    assert record["instrumentation"]["gtos_vnext_pending_policy_would_action"] == (
        "SKIP_PENDING_NOFILL_AVOID"
    )


def test_vnext_pending_policy_apply_flag_blocks_execution_effect():
    decision = GTOSVNextRuntimeDecision(
        decision="MIXED",
        event={"symbol": "XAUUSD"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 3,
            "source_component_counts": {
                "nofill_far_miss_avoid": 2,
                "nofill_far_miss_retest": 1,
            },
            "target_stop_order_class_counts": {"TARGET_FIRST_PROXY_DOMINANT": 2},
        },
    )

    policy = evaluate_vnext_pending_policy(
        decision=decision,
        config={
            "gtos_vnext_runtime": {
                "pending_policy_enabled": True,
                "pending_policy_apply_to_execution": False,
            }
        },
    )

    assert policy.action == "PLACE_LIMIT"
    assert policy.would_action == "SKIP_PENDING_NOFILL_AVOID"
    assert policy.applied is False
    assert policy.reason == "shadow_vnext_pending_policy_nofill_avoid"


def test_vnext_pending_policy_keeps_limit_for_retest_dominant_evidence():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 4,
            "source_component_counts": {
                "nofill_far_miss_avoid": 1,
                "nofill_far_miss_retest": 3,
            },
        },
    )

    policy = evaluate_vnext_pending_policy(
        decision=decision,
        config={"gtos_vnext_runtime": {"pending_policy_enabled": True}},
    )

    assert policy.action == "PLACE_LIMIT"
    assert policy.would_action == "PLACE_LIMIT"
    assert policy.applied is False
    assert policy.reason == "vnext_pending_policy_place_limit"


def test_vnext_pending_policy_keeps_limit_when_nofill_avoid_component_not_avoid():
    decision = GTOSVNextRuntimeDecision(
        decision="MIXED",
        event={"symbol": "XAUUSD"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 3,
            "source_component_counts": {
                "nofill_far_miss_avoid": 3,
            },
            "source_component_decision_counts": {
                "nofill_far_miss_avoid": {"FOLLOW": 3},
            },
            "target_stop_order_class_counts": {"TARGET_FIRST_PROXY_DOMINANT": 3},
        },
    )

    policy = evaluate_vnext_pending_policy(
        decision=decision,
        config={"gtos_vnext_runtime": {"pending_policy_enabled": True}},
    )

    assert policy.action == "PLACE_LIMIT"
    assert policy.would_action == "PLACE_LIMIT"
    assert policy.reason == "vnext_pending_policy_nofill_avoid_component_conflict"
    assert policy.evidence_summary["nofill_avoid_rows"] == 3
    assert policy.evidence_summary["nofill_avoid_component_follow_rows"] == 3
    assert policy.evidence_summary["nofill_avoid_component_avoid_rows"] == 0


def test_vnext_pending_policy_can_route_near_miss_market_entry_when_active():
    evidence = {
        "matched_rows": 2,
        "source_component_counts": {
            "nofill_near_miss_market_entry": 2,
        },
        "target_stop_order_class_counts": {
            "TARGET_FIRST_PROXY_DOMINANT": 2,
        },
    }
    shadow = evaluate_vnext_pending_policy(
        decision=GTOSVNextRuntimeDecision(
            decision="FOLLOW",
            event={"symbol": "GBPJPY"},
            enabled=True,
            apply_to_execution=False,
            matched=True,
            reason="matched",
            evidence=evidence,
        ),
        config={"gtos_vnext_runtime": {"pending_policy_enabled": True}},
    )
    active = evaluate_vnext_pending_policy(
        decision=GTOSVNextRuntimeDecision(
            decision="FOLLOW",
            event={"symbol": "GBPJPY"},
            enabled=True,
            apply_to_execution=True,
            matched=True,
            reason="matched",
            evidence=evidence,
        ),
        config={"gtos_vnext_runtime": {"pending_policy_enabled": True}},
    )

    assert shadow.action == "PLACE_LIMIT"
    assert shadow.would_action == "MARKET_ENTRY_NOW"
    assert shadow.reason == "shadow_vnext_pending_policy_market_entry_now"
    assert shadow.evidence_summary["nofill_market_entry_rows"] == 2
    assert active.action == "MARKET_ENTRY_NOW"
    assert active.applied is True
    assert active.reason == "vnext_pending_policy_market_entry_now"


def test_vnext_pending_policy_blocks_market_entry_on_source_requirement_evidence():
    evidence = {
        "matched_rows": 4,
        "source_component_counts": {
            "nofill_near_miss_market_entry": 3,
            "nofill_near_miss_source_requirement": 1,
        },
        "source_component_decision_counts": {
            "nofill_near_miss_market_entry": {"FOLLOW": 3},
            "nofill_near_miss_source_requirement": {"MIXED": 1},
        },
        "target_stop_order_class_counts": {
            "TARGET_FIRST_PROXY_DOMINANT": 4,
        },
        "proxy_r_class_counts": {
            "STRONG_POSITIVE_PROXY_R": 4,
        },
    }
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "GBPJPY"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence=evidence,
    )

    policy = evaluate_vnext_pending_policy(
        decision=decision,
        config={"gtos_vnext_runtime": {"pending_policy_enabled": True}},
    )

    assert policy.action == "PLACE_LIMIT"
    assert policy.would_action == "PLACE_LIMIT"
    assert policy.applied is False
    assert policy.reason == "vnext_pending_policy_market_entry_source_requirement"
    assert policy.evidence_summary["nofill_market_entry_rows"] == 3
    assert policy.evidence_summary["nofill_source_requirement_rows"] == 1
    assert policy.evidence_summary["nofill_source_requirement_component_mixed_rows"] == 1


def test_vnext_pending_policy_can_allow_market_entry_when_source_requirement_block_disabled():
    evidence = {
        "matched_rows": 4,
        "source_component_counts": {
            "nofill_near_miss_market_entry": 3,
            "nofill_near_miss_source_requirement": 1,
        },
        "source_component_decision_counts": {
            "nofill_near_miss_market_entry": {"FOLLOW": 3},
            "nofill_near_miss_source_requirement": {"MIXED": 1},
        },
        "target_stop_order_class_counts": {
            "TARGET_FIRST_PROXY_DOMINANT": 4,
        },
        "proxy_r_class_counts": {
            "STRONG_POSITIVE_PROXY_R": 4,
        },
    }
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "GBPJPY"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence=evidence,
    )

    policy = evaluate_vnext_pending_policy(
        decision=decision,
        config={
            "gtos_vnext_runtime": {
                "pending_policy_enabled": True,
                "pending_policy_market_entry_blocks_on_source_requirement": False,
            }
        },
    )

    assert policy.action == "MARKET_ENTRY_NOW"
    assert policy.would_action == "MARKET_ENTRY_NOW"
    assert policy.applied is True
    assert policy.reason == "vnext_pending_policy_market_entry_now"


def test_vnext_pending_policy_keeps_limit_when_market_entry_component_avoid_dominates():
    evidence = {
        "matched_rows": 3,
        "source_component_counts": {
            "nofill_near_miss_market_entry": 3,
        },
        "source_component_decision_counts": {
            "nofill_near_miss_market_entry": {"FOLLOW": 1, "AVOID": 2},
        },
        "target_stop_order_class_counts": {
            "TARGET_FIRST_PROXY_DOMINANT": 3,
        },
        "proxy_r_class_counts": {
            "STRONG_POSITIVE_PROXY_R": 3,
        },
    }
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "GBPJPY"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence=evidence,
    )

    policy = evaluate_vnext_pending_policy(
        decision=decision,
        config={"gtos_vnext_runtime": {"pending_policy_enabled": True}},
    )

    assert policy.action == "PLACE_LIMIT"
    assert policy.would_action == "PLACE_LIMIT"
    assert policy.reason == "vnext_pending_policy_market_entry_component_conflict"
    assert policy.evidence_summary["nofill_market_entry_rows"] == 3
    assert policy.evidence_summary["nofill_market_entry_component_follow_rows"] == 1
    assert policy.evidence_summary["nofill_market_entry_component_avoid_rows"] == 2


def test_vnext_pending_policy_keeps_limit_when_near_miss_market_entry_is_not_follow():
    evidence = {
        "matched_rows": 2,
        "source_component_counts": {
            "nofill_near_miss_market_entry": 2,
        },
        "target_stop_order_class_counts": {
            "TARGET_FIRST_PROXY_DOMINANT": 2,
        },
        "proxy_r_class_counts": {
            "STRONG_POSITIVE_PROXY_R": 2,
        },
    }
    decision = GTOSVNextRuntimeDecision(
        decision="AVOID",
        event={"symbol": "GBPJPY"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence=evidence,
    )

    policy = evaluate_vnext_pending_policy(
        decision=decision,
        config={"gtos_vnext_runtime": {"pending_policy_enabled": True}},
    )

    assert policy.action == "PLACE_LIMIT"
    assert policy.would_action == "PLACE_LIMIT"
    assert policy.reason == "vnext_pending_policy_market_entry_requires_follow"
    assert policy.evidence_summary["nofill_market_entry_rows"] == 2
    assert policy.evidence_summary["positive_proxy_rows"] == 2


def test_vnext_pending_policy_keeps_limit_when_market_entry_proxy_is_negative_dominant():
    evidence = {
        "matched_rows": 5,
        "source_component_counts": {
            "nofill_near_miss_market_entry": 5,
        },
        "target_stop_order_class_counts": {
            "TARGET_FIRST_PROXY_DOMINANT": 5,
        },
        "proxy_r_class_counts": {
            "STRONG_POSITIVE_PROXY_R": 2,
            "STRONG_NEGATIVE_PROXY_R": 3,
        },
    }
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "GBPJPY"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence=evidence,
    )

    policy = evaluate_vnext_pending_policy(
        decision=decision,
        config={"gtos_vnext_runtime": {"pending_policy_enabled": True}},
    )

    assert policy.action == "PLACE_LIMIT"
    assert policy.would_action == "PLACE_LIMIT"
    assert policy.reason == "vnext_pending_policy_market_entry_proxy_conflict"
    assert policy.evidence_summary["positive_proxy_rows"] == 2
    assert policy.evidence_summary["negative_proxy_rows"] == 3


def test_vnext_pending_policy_skips_nofill_offset_avoid_when_active():
    evidence = {
        "matched_rows": 4,
        "source_component_counts": {
            "nofill_near_miss_offset": 4,
        },
        "source_component_decision_counts": {
            "nofill_near_miss_offset": {"AVOID": 3, "FOLLOW": 1},
        },
        "proxy_r_class_counts": {
            "STRONG_NEGATIVE_PROXY_R": 3,
            "STRONG_POSITIVE_PROXY_R": 1,
        },
        "target_stop_order_class_counts": {
            "STOP_FIRST_PROXY_DOMINANT": 3,
            "TARGET_FIRST_PROXY_DOMINANT": 1,
        },
    }

    policy = evaluate_vnext_pending_policy(
        decision=GTOSVNextRuntimeDecision(
            decision="FOLLOW",
            event={"symbol": "GBPJPY"},
            enabled=True,
            apply_to_execution=True,
            matched=True,
            reason="matched",
            evidence=evidence,
        ),
        config={"gtos_vnext_runtime": {"pending_policy_enabled": True}},
    )

    assert policy.action == "SKIP_PENDING_NOFILL_AVOID"
    assert policy.would_action == "SKIP_PENDING_NOFILL_AVOID"
    assert policy.applied is True
    assert policy.reason == "vnext_pending_policy_nofill_offset_avoid"
    assert policy.evidence_summary["nofill_offset_rows"] == 4
    assert policy.evidence_summary["nofill_offset_component_avoid_rows"] == 3
    assert policy.evidence_summary["negative_proxy_rows"] == 3


def test_vnext_pending_policy_keeps_limit_when_nofill_offset_proxy_not_negative():
    evidence = {
        "matched_rows": 4,
        "source_component_counts": {
            "nofill_near_miss_offset": 4,
        },
        "source_component_decision_counts": {
            "nofill_near_miss_offset": {"AVOID": 3, "FOLLOW": 1},
        },
        "proxy_r_class_counts": {
            "STRONG_NEGATIVE_PROXY_R": 1,
            "STRONG_POSITIVE_PROXY_R": 3,
        },
    }

    policy = evaluate_vnext_pending_policy(
        decision=GTOSVNextRuntimeDecision(
            decision="FOLLOW",
            event={"symbol": "GBPJPY"},
            enabled=True,
            apply_to_execution=True,
            matched=True,
            reason="matched",
            evidence=evidence,
        ),
        config={"gtos_vnext_runtime": {"pending_policy_enabled": True}},
    )

    assert policy.action == "PLACE_LIMIT"
    assert policy.would_action == "PLACE_LIMIT"
    assert policy.reason == "vnext_pending_policy_nofill_offset_proxy_conflict"
    assert policy.evidence_summary["nofill_offset_rows"] == 4
    assert policy.evidence_summary["negative_proxy_rows"] == 1
    assert policy.evidence_summary["positive_proxy_rows"] == 3


def test_post_l2_source_component_variants_feed_pending_policy_from_full_rows(tmp_path):
    artifact = tmp_path / "vnext_impl.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "near-miss-market-row",
                {
                    "symbol": "GBPJPY",
                    "source_symbol": "GBPJPY",
                    "route_session": "ny_core",
                    "side": "LONG",
                    "market_timeframe": "H4",
                    "horizon_id": "h16",
                    "source_component": "nofill_near_miss_market_entry",
                },
                "DEFAULT_OFF_FOLLOW_SCORER_REVIEW",
                r=0.0,
                stress=0.0,
                n=8,
                proxy=0.15,
                source_component="nofill_near_miss_market_entry",
                target_stop_order_class="TARGET_FIRST_PROXY_DOMINANT",
                r_evidence_class="PROXY_R",
                source_artifact="research/full_matrix.jsonl",
                declared_origin_artifact="research/source_row_ledger.jsonl",
                source_row_id="FULL-EVIDENCE-0001",
                source_line_no=77,
            )
        ],
    )
    cfg = _config(artifact, apply=True)
    cfg["gtos_vnext_runtime"].update(
        {
            "post_l2_evaluate_route_variants": True,
            "post_l2_route_timeframes": ["H4"],
            "post_l2_route_horizons": ["h16"],
            "post_l2_route_source_components": ["nofill_near_miss_market_entry"],
            "pending_policy_enabled": True,
            "pending_policy_market_entry_enabled": True,
        }
    )

    decision = evaluate_vnext_route_event(
        {"symbol": "GBPJPY", "source_symbol": "GBPJPY", "kill_zone": "ny", "direction": "LONG"},
        cfg,
    )
    policy = evaluate_vnext_pending_policy(decision=decision, config=cfg)

    assert decision.matched is True
    assert decision.reason == "matched_vnext_route_scope"
    assert decision.evidence["source_component_counts"] == {"nofill_near_miss_market_entry": 1}
    assert decision.evidence["target_stop_order_class_counts"] == {"TARGET_FIRST_PROXY_DOMINANT": 1}
    assert decision.evidence["proxy_r_class_counts"] == {}
    assert decision.evidence["r_evidence_class_counts"] == {"PROXY_R": 1}
    assert decision.evidence["market_timeframe_counts"] == {"H4": 1}
    assert decision.evidence["horizon_id_counts"] == {"h16": 1}
    assert decision.evidence["source_row_ids"] == ["FULL-EVIDENCE-0001"]
    assert decision.evidence["drill_through_paths"] == ["research/source_row_ledger.jsonl"]
    assert decision.evidence["rows"][0]["drill_through_path"] == "research/source_row_ledger.jsonl"
    assert policy.action == "MARKET_ENTRY_NOW"
    assert policy.reason == "vnext_pending_policy_market_entry_now"
    assert policy.evidence_summary["nofill_market_entry_rows"] == 1


def test_post_l2_route_variants_include_source_components_from_loaded_artifacts(tmp_path):
    artifact = tmp_path / "vnext_impl.jsonl"
    _write_jsonl(
        artifact,
        [
            _review_row(
                "registry-system-row",
                {
                    "symbol": "USDJPY",
                    "source_symbol": "USDJPY",
                    "route_session": "london_core",
                    "side": "LONG",
                    "market_timeframe": "M15",
                    "source_component": "registry_scorer_module_system",
                },
                "DEFAULT_OFF_AVOID_FILTER_REVIEW",
                r=-0.18,
                stress=-0.12,
                n=8,
                source_component="registry_scorer_module_system",
                evidence_family="numeric_router_system_recommendations",
                source_artifact="research/full_matrix.jsonl",
                source_row_id="FULL-EVIDENCE-REGISTRY-SYSTEM",
            )
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "post_l2_evaluate_route_variants": True,
            "post_l2_route_timeframes": ["M15"],
            "post_l2_route_horizons": [""],
            "post_l2_route_frameworks": [""],
            "post_l2_route_families": [""],
            "post_l2_route_source_components": [""],
            "include_artifact_source_components": True,
        }
    )

    decision = evaluate_vnext_route_event(
        {"symbol": "USDJPY", "source_symbol": "USDJPY", "kill_zone": "london", "direction": "LONG"},
        cfg,
    )

    assert decision.decision == "AVOID"
    assert decision.reason == "matched_vnext_route_scope"
    assert decision.evidence["source_component_counts"] == {"registry_scorer_module_system": 1}
    assert decision.evidence["source_row_ids"] == ["FULL-EVIDENCE-REGISTRY-SYSTEM"]


def test_artifact_source_component_expansion_ignores_code_surface_components(tmp_path):
    artifact = tmp_path / "vnext_impl.jsonl"
    _write_jsonl(
        artifact,
        [
            {
                "vnext_matrix_row_id": "gate-code-surface-row",
                "row_type": "gtos_vnext_evidence_to_system_matrix_row",
                "symbol": "USDJPY",
                "source_symbol": "USDJPY",
                "route_session": "london_core",
                "side": "LONG",
                "market_timeframe": "M15",
                "source_component": "src/components/permissions.py::_reject_if_touch_count_too_high",
                "action_class": "avoid_filter",
                "source_name": "gate_filter_selector_runtime_mapping",
                "evidence_family": "gate_filter_selector_evidence",
                "source_artifact": "research/gate.jsonl",
                "source_row_id": "GATE-CODE-SURFACE",
                "r_metrics": {
                    "cost_adjusted_simulated_r": _metric(-1.0, 1),
                    "stress_simulated_r": _metric(-1.0, 1),
                    "effective_n": _metric(1, 1),
                    "proxy_score": _metric(0, 0),
                },
            }
        ],
    )
    cfg = _config(artifact)
    cfg["gtos_vnext_runtime"].update(
        {
            "post_l2_evaluate_route_variants": True,
            "post_l2_route_timeframes": ["M15"],
            "post_l2_route_horizons": [""],
            "post_l2_route_frameworks": [""],
            "post_l2_route_families": [""],
            "post_l2_route_source_components": [""],
            "include_artifact_source_components": True,
        }
    )

    decision = evaluate_vnext_route_event(
        {"symbol": "USDJPY", "source_symbol": "USDJPY", "kill_zone": "london", "direction": "LONG"},
        cfg,
    )

    assert decision.decision == "LEGACY"
    assert decision.reason == "no_matching_vnext_route_scope"


def test_vnext_risk_adjustment_computes_strong_follow_shadow_multiplier():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "GBPJPY"},
        enabled=True,
        apply_to_execution=False,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 1,
            "metrics": {
                "cost_adjusted_simulated_r": {"sum": 33.8, "mean": 0.1},
                "stress_simulated_r": {"sum": 33.7, "mean": 0.1},
                "effective_n": {"sum": 325609, "mean": 325609},
                "proxy_score": {"sum": 4.2, "mean": 4.2},
            },
        },
    )

    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config={
            "gtos_vnext_runtime": {
                "risk_adjustment_enabled": True,
                "positive_follow_pressure_guard_enabled": False,
            }
        },
    )

    assert adjustment.applied is False
    assert adjustment.after_risk_pct == 1.0
    assert adjustment.multiplier == 1.0
    assert adjustment.would_multiplier == 1.25
    assert adjustment.reason == "shadow_vnext_risk_strong_follow"
    assert adjustment.evidence_summary["effective_n_sum"] == 325609


def test_vnext_risk_adjustment_applies_when_execution_flag_flipped():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "GBPJPY"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 1,
            "metrics": {
                "cost_adjusted_simulated_r": {"sum": 12, "mean": 0.2},
                "stress_simulated_r": {"sum": 11, "mean": 0.18},
                "effective_n": {"sum": 200, "mean": 200},
            },
        },
    )

    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=0.5,
        decision=decision,
        config={"gtos_vnext_runtime": {"risk_adjustment_enabled": True}},
    )

    assert adjustment.applied is True
    assert adjustment.after_risk_pct == 0.625
    assert adjustment.multiplier == 1.25
    assert adjustment.reason == "vnext_risk_strong_follow"


def test_vnext_risk_adjustment_can_zero_avoid_when_blocking_disabled():
    decision = GTOSVNextRuntimeDecision(
        decision="AVOID",
        event={"symbol": "NAS100"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 1,
            "metrics": {
                "cost_adjusted_simulated_r": {"sum": -81.2, "mean": -0.2},
                "stress_simulated_r": {"sum": -625.6, "mean": -1.0},
                "effective_n": {"sum": 11475, "mean": 11475},
            },
        },
    )

    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config={
            "gtos_vnext_runtime": {
                "risk_adjustment_enabled": True,
                "positive_follow_pressure_guard_enabled": False,
            }
        },
    )

    assert adjustment.applied is True
    assert adjustment.after_risk_pct == 0.0
    assert adjustment.multiplier == 0.0
    assert adjustment.reason == "vnext_risk_avoid"


def test_vnext_risk_adjustment_can_zero_stop_first_proxy_path():
    decision = GTOSVNextRuntimeDecision(
        decision="MIXED",
        event={"symbol": "XAUUSD"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 4,
            "target_stop_order_class_counts": {
                "STOP_FIRST_PROXY_DOMINANT": 3,
                "TARGET_FIRST_PROXY_DOMINANT": 1,
            },
            "metrics": {"effective_n": {"sum": 4, "mean": 1}},
        },
    )

    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config={
            "gtos_vnext_runtime": {
                "risk_adjustment_enabled": True,
                "positive_follow_pressure_guard_enabled": False,
            }
        },
    )

    assert adjustment.applied is True
    assert adjustment.after_risk_pct == 0.0
    assert adjustment.multiplier == 0.0
    assert adjustment.reason == "vnext_risk_stop_first_proxy"
    assert adjustment.evidence_summary["stop_first_proxy_rows"] == 3
    assert adjustment.evidence_summary["target_first_proxy_rows"] == 1


def test_vnext_risk_adjustment_downweights_ambiguous_negative_target_stop_proxy():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 4,
            "target_stop_order_class_counts": {
                "TARGET_STOP_AMBIGUOUS_OR_MIXED": 4,
            },
            "proxy_r_class_counts": {
                "STRONG_NEGATIVE_PROXY_R": 3,
                "POSITIVE_PROXY_R": 1,
            },
            "metrics": {
                "cost_adjusted_simulated_r": {"sum": 2.0, "mean": 0.5},
                "effective_n": {"sum": 4, "mean": 1},
            },
        },
    )

    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config={
            "gtos_vnext_runtime": {
                "risk_adjustment_enabled": True,
                "strong_negative_proxy_risk_min_rows": 20,
            }
        },
    )

    assert adjustment.applied is True
    assert adjustment.after_risk_pct == 0.5
    assert adjustment.multiplier == 0.5
    assert adjustment.reason == "vnext_risk_target_stop_ambiguous_proxy"
    assert adjustment.evidence_summary["target_stop_ambiguous_rows"] == 4
    assert adjustment.evidence_summary["negative_proxy_r_rows"] == 3
    assert adjustment.evidence_summary["positive_proxy_r_rows"] == 1


def test_vnext_risk_adjustment_does_not_downweight_ambiguous_positive_target_stop_proxy():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 4,
            "target_stop_order_class_counts": {
                "TARGET_STOP_AMBIGUOUS_OR_MIXED": 4,
            },
            "proxy_r_class_counts": {
                "STRONG_POSITIVE_PROXY_R": 3,
                "NEGATIVE_PROXY_R": 1,
            },
        },
    )

    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config={
            "gtos_vnext_runtime": {
                "risk_adjustment_enabled": True,
                "strong_positive_proxy_risk_min_rows": 20,
            }
        },
    )

    assert adjustment.applied is False
    assert adjustment.after_risk_pct == 1.0
    assert adjustment.reason == "vnext_risk_follow"
    assert adjustment.evidence_summary["target_stop_ambiguous_rows"] == 4
    assert adjustment.evidence_summary["negative_proxy_r_rows"] == 1
    assert adjustment.evidence_summary["positive_proxy_r_rows"] == 3


def test_vnext_risk_adjustment_can_zero_not_source_bound_target_stop_geometry():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAGUSD"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 168,
            "target_stop_order_class_counts": {
                "TARGET_STOP_ORDER_NOT_SOURCE_BOUND": 168,
            },
            "metrics": {
                "cost_adjusted_simulated_r": {"sum": 12, "mean": 0.07},
                "stress_simulated_r": {"sum": 10, "mean": 0.06},
                "effective_n": {"sum": 168, "mean": 1},
            },
        },
    )

    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config={
            "gtos_vnext_runtime": {
                "risk_adjustment_enabled": True,
                "positive_follow_pressure_guard_enabled": False,
            }
        },
    )

    assert adjustment.applied is True
    assert adjustment.after_risk_pct == 0.0
    assert adjustment.multiplier == 0.0
    assert adjustment.reason == "vnext_risk_target_stop_not_source_bound"
    assert adjustment.evidence_summary["target_stop_not_source_bound_rows"] == 168


def test_vnext_risk_adjustment_can_zero_strong_negative_proxy_class_follow():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 116,
            "proxy_r_class_counts": {
                "STRONG_NEGATIVE_PROXY_R": 96,
                "NEGATIVE_PROXY_R": 20,
                "POSITIVE_PROXY_R": 12,
            },
            "metrics": {
                "cost_adjusted_simulated_r": {"sum": 20, "mean": 0.17},
                "stress_simulated_r": {"sum": 19, "mean": 0.16},
                "effective_n": {"sum": 116, "mean": 1},
            },
        },
    )

    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config={
            "gtos_vnext_runtime": {
                "risk_adjustment_enabled": True,
                "positive_follow_pressure_guard_enabled": False,
            }
        },
    )

    assert adjustment.applied is True
    assert adjustment.after_risk_pct == 0.0
    assert adjustment.multiplier == 0.0
    assert adjustment.reason == "vnext_risk_strong_negative_proxy_class"
    assert adjustment.evidence_summary["strong_negative_proxy_r_rows"] == 96
    assert adjustment.evidence_summary["negative_proxy_r_rows"] == 116
    assert adjustment.evidence_summary["positive_proxy_r_rows"] == 12


def test_vnext_risk_adjustment_source_bound_positive_pressure_bypasses_proxy_vetoes():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "XAUUSD", "side": "LONG"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 250,
            "route_family_decision_counts": {
                "numeric_router": {"AVOID": 60, "FOLLOW": 4},
            },
            "source_component_decision_counts": {
                "shadow_source_guard": {"AVOID": 60, "FOLLOW": 4},
            },
            "evidence_family_decision_counts": {
                "numeric_router_system_recommendations": {"AVOID": 60, "FOLLOW": 4},
            },
            "source_name_decision_counts": {
                "numeric_router_avoid_score": {"AVOID": 60},
            },
            "target_stop_order_class_counts": {
                "TARGET_STOP_ORDER_NOT_SOURCE_BOUND": 80,
            },
            "proxy_r_class_counts": {
                "STRONG_NEGATIVE_PROXY_R": 60,
            },
            "evidence_family_counts": {
                "numeric_router_source_repair": 20,
            },
            "metrics": {
                "cost_adjusted_simulated_r": {"sum": 220.0, "mean": 1.1},
                "stress_simulated_r": {"sum": 80.0, "mean": 0.4},
                "effective_n": {"sum": 250, "mean": 1},
            },
        },
    )

    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config={"gtos_vnext_runtime": {"risk_adjustment_enabled": True}},
    )

    assert adjustment.applied is True
    assert adjustment.after_risk_pct == 1.25
    assert adjustment.reason == "vnext_risk_strong_follow"
    assert adjustment.evidence_summary["positive_follow_pressure_guard_active"] is True
    assert adjustment.evidence_summary["route_family_avoid_veto_bypassed"] is True
    assert adjustment.evidence_summary["source_component_avoid_veto_bypassed"] is True
    assert adjustment.evidence_summary["evidence_family_avoid_veto_bypassed"] is True
    assert adjustment.evidence_summary["source_name_avoid_veto_bypassed"] is True
    assert adjustment.evidence_summary["target_stop_not_source_bound_bypassed"] is True
    assert adjustment.evidence_summary["strong_negative_proxy_risk_bypassed"] is True
    assert adjustment.evidence_summary["source_repair_required_bypassed"] is True


def test_vnext_risk_adjustment_can_boost_strong_positive_proxy_class_follow():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "USDJPY"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 32,
            "proxy_r_class_counts": {
                "STRONG_POSITIVE_PROXY_R": 30,
                "NEGATIVE_PROXY_R": 2,
            },
        },
    )
    cfg = {
        "gtos_vnext_runtime": {
            "risk_adjustment_enabled": True,
            "strong_positive_proxy_risk_adjustment_enabled": True,
            "strong_positive_proxy_risk_min_rows": 20,
            "strong_positive_proxy_risk_dominance_ratio": 2.0,
            "strong_positive_proxy_risk_multiplier": 1.25,
        }
    }

    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config=cfg,
    )

    assert adjustment.applied is True
    assert adjustment.after_risk_pct == 1.25
    assert adjustment.multiplier == 1.25
    assert adjustment.reason == "vnext_risk_strong_positive_proxy_class"
    assert adjustment.evidence_summary["strong_positive_proxy_r_rows"] == 30
    assert adjustment.evidence_summary["positive_proxy_r_rows"] == 30
    assert adjustment.evidence_summary["negative_proxy_r_rows"] == 2


def test_vnext_risk_adjustment_source_guarded_positive_proxy_bypasses_geometry_veto():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "USDJPY", "side": "LONG"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 25,
            "proxy_r_class_counts": {"STRONG_POSITIVE_PROXY_R": 25},
            "target_stop_order_class_counts": {"TARGET_STOP_ORDER_NOT_SOURCE_BOUND": 25},
            "source_role_counts": {"scorer_registry_surface": 25},
            "source_group_counts": {"scorer_registry_surface": 25},
            "system_surface_counts": {"default_off_research_scorer_registry_catalog": 25},
            "implementation_action_counts": {
                "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS": 25
            },
            "metrics": {
                "proxy_score": {"sum": 25.0, "mean": 1.0},
            },
        },
    )
    cfg = {
        "gtos_vnext_runtime": {
            "risk_adjustment_enabled": True,
            "strong_positive_proxy_risk_adjustment_enabled": True,
            "strong_positive_proxy_risk_min_rows": 20,
            "source_guarded_positive_proxy_enabled": True,
            "source_guarded_positive_proxy_min_rows": 20,
            "target_stop_not_source_bound_risk_adjustment_enabled": True,
        }
    }

    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config=cfg,
    )

    assert adjustment.applied is True
    assert adjustment.after_risk_pct == 1.25
    assert adjustment.reason == "vnext_risk_strong_positive_proxy_class"
    assert adjustment.evidence_summary["source_guarded_positive_proxy_guard_active"] is True
    assert adjustment.evidence_summary["source_guarded_positive_proxy_guard_rows"] == 25
    assert adjustment.evidence_summary["target_stop_not_source_bound_bypassed"] is True


def test_vnext_risk_adjustment_does_not_boost_conflicted_positive_proxy_class():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "USDJPY"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 45,
            "proxy_r_class_counts": {
                "STRONG_POSITIVE_PROXY_R": 25,
                "STRONG_NEGATIVE_PROXY_R": 20,
            },
        },
    )
    cfg = {
        "gtos_vnext_runtime": {
            "risk_adjustment_enabled": True,
            "strong_positive_proxy_risk_adjustment_enabled": True,
            "strong_positive_proxy_risk_min_rows": 20,
            "strong_positive_proxy_risk_dominance_ratio": 2.0,
            "strong_positive_proxy_risk_multiplier": 1.25,
            "strong_negative_proxy_risk_adjustment_enabled": True,
            "strong_negative_proxy_risk_min_rows": 20,
            "strong_negative_proxy_risk_dominance_ratio": 2.0,
            "strong_negative_proxy_risk_multiplier": 0.0,
        }
    }

    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config=cfg,
    )

    assert adjustment.applied is False
    assert adjustment.after_risk_pct == 1.0
    assert adjustment.multiplier == 1.0
    assert adjustment.would_multiplier == 1.0
    assert adjustment.reason == "vnext_risk_follow"
    assert adjustment.evidence_summary["strong_positive_proxy_r_rows"] == 25
    assert adjustment.evidence_summary["strong_negative_proxy_r_rows"] == 20


def test_vnext_risk_adjustment_can_zero_source_repair_dominant_follow():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "USDJPY"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 8,
            "evidence_family_counts": {"numeric_router_source_repair": 8},
            "r_evidence_class_counts": {"SOURCE_REPAIR_FOR_EXACT_R": 8},
            "source_group_counts": {"source_repair_proof": 8},
            "source_role_counts": {"exact_r_source_repair_proof": 8},
            "system_surface_counts": {"source_repair_proof": 8},
            "target_stop_order_class_counts": {"TARGET_FIRST_PROXY_DOMINANT": 2},
            "metrics": {
                "cost_adjusted_simulated_r": {"sum": 9, "mean": 1.125},
                "stress_simulated_r": {"sum": 8, "mean": 1.0},
                "effective_n": {"sum": 8, "mean": 1},
            },
        },
    )

    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config={"gtos_vnext_runtime": {"risk_adjustment_enabled": True}},
    )

    assert adjustment.applied is True
    assert adjustment.after_risk_pct == 0.0
    assert adjustment.multiplier == 0.0
    assert adjustment.reason == "vnext_risk_source_repair_required"
    assert adjustment.evidence_summary["source_repair_required_rows"] == 8


def test_vnext_blocks_source_repair_dominant_follow_execution_when_active():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "USDJPY"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 4,
            "evidence_family_counts": {"numeric_router_source_repair": 4},
            "r_evidence_class_counts": {"SOURCE_REPAIR_FOR_EXACT_R": 4},
            "metrics": {"effective_n": {"sum": 4, "mean": 1}},
        },
    )
    cfg = {
        "gtos_vnext_runtime": {
            "risk_adjustment_enabled": True,
            "risk_zero_blocks_execution": True,
            "source_repair_risk_adjustment_enabled": True,
            "source_repair_risk_min_rows": 1,
            "source_repair_risk_multiplier": 0.0,
            "execution_block_min_risk_multiplier": 0.000001,
            "block_min_effective_n": 3,
        }
    }

    assert vnext_execution_block_reason(decision, cfg) == "vnext_risk_source_repair_required"


def test_vnext_blocks_source_repair_before_effective_n_floor():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "USDJPY"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 1,
            "evidence_family_counts": {"numeric_router_source_repair": 1},
            "r_evidence_class_counts": {"SOURCE_REPAIR_FOR_EXACT_R": 1},
        },
    )
    cfg = {
        "gtos_vnext_runtime": {
            "risk_adjustment_enabled": True,
            "risk_zero_blocks_execution": True,
            "source_repair_risk_adjustment_enabled": True,
            "source_repair_risk_min_rows": 1,
            "source_repair_risk_multiplier": 0.0,
            "execution_block_min_risk_multiplier": 0.000001,
            "block_min_effective_n": 999,
        }
    }

    assert vnext_execution_block_reason(decision, cfg) == "vnext_risk_source_repair_required"


def test_vnext_risk_adjustment_downweights_context_guard_follow():
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "USDJPY"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 3,
            "source_group_counts": {"context_guard_input": 3},
            "metrics": {
                "cost_adjusted_simulated_r": {"sum": 12, "mean": 4},
                "stress_simulated_r": {"sum": 9, "mean": 3},
                "effective_n": {"sum": 300, "mean": 100},
            },
        },
    )

    adjustment = apply_vnext_risk_adjustment(
        current_risk_pct=1.0,
        decision=decision,
        config={"gtos_vnext_runtime": {"risk_adjustment_enabled": True}},
    )

    assert adjustment.applied is True
    assert adjustment.after_risk_pct == 0.5
    assert adjustment.multiplier == 0.5
    assert adjustment.reason == "vnext_risk_context_guard_input"
    assert adjustment.evidence_summary["context_guard_input_rows"] == 3


def test_orchestrator_vnext_risk_hook_attaches_adjustment_to_record():
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch.config = {"gtos_vnext_runtime": {"risk_adjustment_enabled": True}}
    record = {"decision_pipeline": {}, "instrumentation": {}}
    decision = GTOSVNextRuntimeDecision(
        decision="MIXED",
        event={"symbol": "USDJPY"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={"matched_rows": 2, "metrics": {"effective_n": {"sum": 50}}},
    )

    adjustment = orch._apply_gtos_vnext_risk_adjustment(
        current_risk_pct=1.0,
        vnext_decision=decision,
        record=record,
    )

    assert isinstance(adjustment, GTOSVNextRiskAdjustment)
    assert adjustment.applied is True
    assert adjustment.after_risk_pct == 0.5
    attached = record["decision_pipeline"]["gtos_vnext_risk_adjustment"]
    assert attached["decision"] == "MIXED"
    assert record["instrumentation"]["gtos_vnext_risk_multiplier"] == 0.5


def test_orchestrator_vnext_block_preview_attaches_risk_evidence_to_record():
    orch = SessionOrchestrator.__new__(SessionOrchestrator)
    orch.config = {
        "risk": {"risk_per_trade_pct": 2.0},
        "gtos_vnext_runtime": {
            "risk_adjustment_enabled": True,
            "route_family_avoid_veto_enabled": True,
            "route_family_avoid_veto_families": ["numeric_router"],
        },
    }
    record = {"decision_pipeline": {}, "instrumentation": {}}
    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={"symbol": "USDJPY"},
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched",
        evidence={
            "matched_rows": 4,
            "route_family_decision_counts": {
                "moonshot_mechanical": {"FOLLOW": 3},
                "numeric_router": {"AVOID": 1},
            },
            "metrics": {"effective_n": {"sum": 100}},
        },
    )

    adjustment = orch._attach_gtos_vnext_block_risk_preview(
        vnext_decision=decision,
        record=record,
    )

    assert adjustment.applied is True
    assert adjustment.before_risk_pct == 2.0
    assert adjustment.after_risk_pct == 0.0
    assert adjustment.reason == "vnext_risk_route_family_avoid_veto"
    attached = record["decision_pipeline"]["gtos_vnext_risk_adjustment"]
    assert attached["evidence_summary"]["route_family_avoid_veto_family"] == "numeric_router"
    assert record["instrumentation"]["gtos_vnext_risk_reason"] == (
        "vnext_risk_route_family_avoid_veto"
    )


def test_agent_config_wires_vnext_runtime_production_replacement_path():
    cfg = yaml.safe_load(open("config/agent_config.yaml", encoding="utf-8"))
    block = cfg["gtos_vnext_runtime"]

    assert block["enabled"] is True
    assert block["mode"] == "production_replacement_vnext_moonshot"
    assert block["apply_to_execution"] is True
    assert block["moonshot_dynamic_execution_router_enabled"] is True
    assert block["moonshot_dynamic_execution_router_apply_to_execution"] is True
    assert block["moonshot_broader_origin_live_generation_enabled"] is True
    assert block["moonshot_broader_origin_execute_pre_ai_pre_l2"] is True
    assert "moonshot_broader_origin_consume_no_candidate" not in block
    assert block["moonshot_broader_origin_cross_asset_fetch_enabled"] is True
    assert block["moonshot_broader_origin_cross_asset_fetch_bars"] == 80
    assert block["pending_policy_apply_to_execution"] is True
    assert block["moonshot_dynamic_execution_router_policy"] == "momentum_exhaustion"
    assert block["moonshot_dynamic_execution_router_momentum_exception_policy"] == (
        "partial_be_runner"
    )
    assert block[
        "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner"
    ] == []
    assert block[
        "moonshot_dynamic_execution_router_allow_policy_invariant_selected_cell_risk_geometry"
    ] is True
    assert block["moonshot_dynamic_execution_router_be_trigger_r"] == 1.0
    assert block["moonshot_dynamic_execution_router_be_final_target_r"] == 1.5
    assert block["moonshot_dynamic_execution_router_be_time_stop_bars"] is None
    assert block["moonshot_dynamic_execution_router_partial_trigger_r"] == 1.0
    assert block["moonshot_dynamic_execution_router_partial_final_target_r"] == 3.0
    assert block["moonshot_dynamic_execution_router_partial_close_ratio"] == 0.5
    assert block["moonshot_dynamic_execution_router_trailing_trigger_r"] == 1.0
    assert block["moonshot_dynamic_execution_router_trailing_final_target_r"] == 3.0
    assert block["moonshot_dynamic_execution_router_trailing_gap_r"] == 0.5
    assert block["moonshot_dynamic_execution_router_momentum_trigger_r"] == 1.0
    assert block["moonshot_dynamic_execution_router_momentum_final_target_r"] == 2.0
    assert block["moonshot_dynamic_execution_router_momentum_pullback_r"] == 0.4
    assert block["moonshot_dynamic_target_stop_geometry_v4_enabled"] is True
    assert block["moonshot_dynamic_target_stop_geometry_v4_policy_id"] == (
        "wave3_dynamic_target_stop_thesis_horizon_geometry_v4"
    )
    assert block[
        "moonshot_dynamic_target_stop_geometry_v4_default_thesis_horizon_m15_bars"
    ] == 32
    assert block["moonshot_dynamic_target_stop_geometry_v4_stale_review_m15_bars"] == 24
    assert block["moonshot_dynamic_target_stop_geometry_v4_capture_required"] is True
    assert block["moonshot_dynamic_execution_router_condition_challenger_enabled"] is True
    assert block["moonshot_dynamic_execution_router_replaces_policy"] == (
        "retired_static_baseline_comparator"
    )
    assert block["moonshot_dynamic_execution_router_default_source_mode"] == "OHLC_M15_CSV"
    assert block["moonshot_dynamic_execution_router_default_source_path_feature_status"] == (
        "computed_from_source_ohlc_asof"
    )
    assert block["moonshot_dynamic_execution_router_default_source_window_complete"] is True
    assert block["moonshot_dynamic_execution_router_default_ordered_path_status"] == (
        "ordered_path_not_ambiguous_in_m15_replay"
    )
    assert block["moonshot_dynamic_execution_router_ordered_path_scope"] == "selected_policy"
    assert block["moonshot_dynamic_execution_router_source_window_complete_blocks_activation"] is False
    assert block["moonshot_dynamic_execution_router_require_configured_kill_zone"] is True
    assert block["moonshot_dynamic_execution_router_repaired_overlay_selector"] == (
        "full_moonshot_old_three_plus_broader_origin_positive_native_be_after_trigger"
    )
    assert block["moonshot_dynamic_execution_router_stage13_repair_summary_path"].endswith(
        "VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_2026-05-26.json"
    )
    assert block["moonshot_dynamic_execution_router_repaired_branch_allowlist_path"].endswith(
        "VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_REPAIRED_BRANCH_ALLOWLIST_2026-05-26.json"
    )
    assert block["moonshot_dynamic_execution_router_broader_origin_allowlist_path"].endswith(
        "VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_ACTIVATION_ALLOWLIST_2026-05-26.json"
    )
    assert block["moonshot_dynamic_execution_router_repaired_branch_action"] == (
        "MOONSHOT_REPAIRED_FOLLOW"
    )
    assert block["moonshot_dynamic_execution_router_required_branch_labels"] == ["FOLLOW"]
    assert block["moonshot_dynamic_execution_router_activated_frameworks"] == [
        "breaker_re_entry",
        "fvg_fill",
        "ob_retest",
    ]
    assert block["moonshot_dynamic_execution_router_activated_origin_families"] == [
        "cross_asset_lead_lag",
        "displacement_continuation",
        "liquidity_sweep_reclaim",
        "regime_transition_break",
        "session_open_range_break",
        "structural_distance_extreme",
        "volatility_compression_expansion",
    ]
    assert block["moonshot_dynamic_execution_router_broader_origin_min_group_rows"] == 20
    assert block["moonshot_dynamic_execution_router_repaired_branch_min_rows"] == 20
    assert len(block["moonshot_dynamic_execution_router_broker_native_eligible_symbols"]) == 39
    assert block["moonshot_dynamic_execution_router_broker_native_exact_excluded_symbols"] == []
    assert block["replacement_monitoring_enabled"] is True
    assert block["replacement_monitoring_log_enabled"] is True
    assert block["replacement_monitoring_log_path"] == (
        "shadow_logs/gtos_vnext_replacement_monitoring.jsonl"
    )
    assert block["replacement_ml_apply_to_execution"] is False
    assert block["replacement_ml_role_source_manifest"].endswith(
        "VNEXT_ACTIVATION_ML_CHALLENGER_RESULTS_2026-05-26.json"
    )
    assert block["replacement_ml_role_keys"] == [
        "ai_call_reducer",
        "source_confidence_scorer",
        "partition_robustness_scorer",
        "timeout_ambiguous_monitor",
        "drift_detector",
    ]
    assert block["replacement_ml_ai_call_reducer_enabled"] is True
    assert block["replacement_ml_source_confidence_scorer_enabled"] is True
    assert block["replacement_ml_partition_robustness_scorer_enabled"] is True
    assert block["replacement_ml_timeout_ambiguous_monitor_enabled"] is True
    assert block["replacement_ml_drift_detector_enabled"] is True
    assert block["replacement_ml_drift_psi_warn_threshold"] == 0.25
    assert block["pre_ai_enabled"] is True
    assert block["pre_ai_apply_to_ai_call"] is True
    assert block["pre_ai_evaluate_all_sides"] is True
    assert block["pre_ai_evaluate_route_variants"] is True
    assert block["pre_ai_prune_route_variants_to_artifact_scopes"] is True
    assert block["pre_ai_match_artifact_scopes_directly"] is True
    assert block["pre_ai_exclude_zero_risk_routes"] is True
    assert block["pre_ai_min_route_risk_multiplier"] == 0.000001
    assert block["pre_ai_min_follow_effective_n"] == 3
    assert block["pre_ai_follow_effective_n_bypass_risk_reasons"] == [
        "vnext_risk_strong_positive_proxy_class"
    ]
    assert block["pre_ai_select_stronger_follow_side_enabled"] is True
    assert block["pre_ai_stronger_follow_dominance_ratio"] == 1.5
    assert block["pre_ai_stronger_follow_min_abs_pressure"] == 1.0
    assert block["pre_ai_ob_core_framework_preference_enabled"] is True
    assert block["pre_ai_ob_core_framework"] == "ob_retest"
    assert block["pre_ai_ob_core_min_abs_pressure"] == 1.0
    assert block["pre_ai_ob_core_competing_framework_dominance_ratio"] == 1.5
    assert block["pre_ai_xau_asian_sweep_continuation_enabled"] is True
    assert block["pre_ai_xau_asian_sweep_evaluate_continuation_side"] is True
    assert block["pre_ai_xau_asian_sweep_symbol_families"] == ["XAUUSD_GC_FAMILY"]
    assert block["pre_ai_xau_asian_sweep_framework"] == "ob_retest"
    assert block["pre_ai_exclude_blocked_frameworks_enabled"] is True
    assert block["pre_ai_framework_exclusion_candidates"] == [
        "ob_retest",
        "fvg_fill",
        "breaker_re_entry",
    ]
    assert block["pre_ai_ai_narrowing_policy_decision_enabled"] is True
    assert block["pre_ai_ai_narrowing_capacity_blocklist_decision_enabled"] is True
    assert block["pre_ai_ai_narrowing_load_capacity_blocklist_artifact"] is True
    assert block["pre_ai_ai_narrowing_capacity_blocklist_artifact_path"].endswith(
        "MAIN_ORCH48_AI_NARROWING_CAPACITY_BLOCKLIST_LEDGER_2026-05-18.jsonl"
    )
    assert block["pre_ai_ai_narrowing_allow_blocklist_required_scopes"] is False
    assert block["pre_ai_ai_narrowing_capacity_blocklist_active"] is False
    assert block["load_cp281_rule_replay_result_table_artifact"] is True
    assert block["cp281_rule_replay_result_table_artifact_path"].endswith(
        "MAIN_ORCH48_CP281_RULE_REPLAY_EXECUTION_MATERIALIZATION_RESULT_TABLE_LEDGER_2026-05-18.jsonl"
    )
    assert block["load_cp281_rule_replay_event_artifact"] is True
    assert block["cp281_rule_replay_event_artifact_path"].endswith(
        "MAIN_ORCH48_CP281_RULE_REPLAY_EXECUTION_MATERIALIZATION_EVENT_LEDGER_2026-05-18.jsonl"
    )
    assert block["pre_ai_ai_role_context_enabled"] is True
    assert block["pre_ai_ai_role_context_apply_to_prompt"] is True
    assert block["pre_ai_ai_role_context_uses_would_action"] is True
    assert block["pre_ai_ai_role_context_side_limit"] == 4
    assert block["pre_ai_ai_role_context_source_artifact_path"] == (
        ".context/00_core/llm_specialization_research_backlog.md"
    )
    assert block["pre_ai_ai_role_pressure_test_enabled"] is True
    assert block["pre_ai_ai_role_pressure_test_steps"] == [
        "critic_mode",
        "list_issues",
        "fix_or_reject",
        "state_what_was_fixed",
    ]
    assert block["pre_ai_ai_role_per_instrument_scope_guard_enabled"] is True
    assert block["pre_ai_ai_role_null_result_is_valid"] is True
    assert block["ai_policy_enabled"] is True
    assert block["ai_policy_apply_to_ai_call"] is False
    assert block["ai_policy_follow_no_ai_enabled"] is True
    assert block["ai_policy_follow_validator_risk_tiers"] == [
        "standard",
        "elevated",
        "high",
        "funded_prop",
    ]
    assert block["ai_policy_allow_mixed_ai_resolution"] is True
    assert block["ai_policy_mixed_resolution_requires_source_bound_fields"] is True
    assert block["ai_policy_allow_legacy_broad_fallback"] is False
    assert block["ai_policy_legacy_requires_replayed_scope"] is True
    assert block["ai_policy_prompt_hash_logging_required"] is True
    assert block["ai_policy_schema_validation_required"] is True
    assert block["ai_policy_content_addressed_cache_required"] is True
    assert block["local_heavy_data_search_enabled"] is True
    assert block["local_heavy_data_use_default_roots"] is False
    assert "C:/Users/MSI/Documents/ai-trading-agent" in block["local_heavy_data_search_roots"]
    assert "C:/tmp" in block["local_heavy_data_search_roots"]
    assert block["include_artifact_source_components"] is True
    assert block["artifact_source_component_evidence_families"] == [
        "numeric_router_system_recommendations",
        "numeric_router_source_repair",
        "moonshot_target_stop_ordering",
        "moonshot_entry_adverse_stop_first",
        "moonshot_broker_repaired_proxy",
        "moonshot_repaired_proxy_symbol_surface",
        "moonshot_unified_numeric_result",
        "moonshot_exact_r_missing_proof",
        "moonshot_source_geometry_repair",
        "moonshot_challenger_frontier_action",
        "moonshot_challenger_frontier_route",
        "moonshot_control_screen",
        "moonshot_control_screen_route_queue",
        "moonshot_gtos_replay_blocker",
        "moonshot_accepted_builder",
        "moonshot_accepted_builder_binding",
        "moonshot_accepted_builder_branch",
        "moonshot_accepted_builder_entry_adverse",
        "moonshot_accepted_builder_family",
        "moonshot_accepted_builder_m15",
        "moonshot_accepted_builder_m1",
        "moonshot_accepted_builder_positive",
        "moonshot_accepted_builder_source",
        "moonshot_accepted_builder_rejected_repair",
        "moonshot_market_gap_primitive_expansion",
        "moonshot_nearmiss_market_entry_join",
        "moonshot_recommendation_merge_bucket",
        "moonshot_recommendation_family_rollup",
        "moonshot_recommendation_unified_candidate",
        "moonshot_recommendation_scope_rollup",
        "moonshot_unified_candidate_market_rollup",
        "expanded_market_source_geometry",
        "gtos_vnext_nofill_pending_lifecycle",
        "gtos_vnext_production_change_promotions",
        "gtos_vnext_production_change_kill_redesign_guards",
        "gtos_vnext_production_change_mixed_resolution",
        "gtos_vnext_entry_offset_050r_cluster_guard",
        "gtos_vnext_opening_drive_source_contract",
        "gtos_vnext_numeric_router_catalog_runtime",
        "gtos_vnext_survivor_failure_runtime",
        "gtos_vnext_source_repair_missing_denominator",
        "gtos_vnext_nr_source_repair_execution_identity",
        "gtos_vnext_ai_narrowing_default_off_runtime",
        "gtos_vnext_ai_decision_trace_routing_guard",
        "gtos_vnext_pre_ai_post_l2_routing_policy",
        "gtos_vnext_rejected_candidate_l2_value_mining",
        "gtos_vnext_legacy_ai_cascade_model_runtime",
        "gtos_vnext_legacy_t7_simulation_friction",
        "gtos_vnext_legacy_v2_v3_paper_live_friction",
        "gtos_vnext_sl_beyond_ob_outcome_join_source_repair",
        "gtos_vnext_fvg_trade_record_bounds_execution_runtime",
        "gtos_vnext_exit_management_trailing_j46",
        "gtos_vnext_exit_management_residue",
        "gtos_vnext_q62_partial_close_exit_runtime",
        "gtos_vnext_ready8_failure_control_residue",
        "gtos_vnext_trade_record_execution_lifecycle",
        "gtos_vnext_lifecycle_execution_source_guard",
        "gtos_vnext_execution_adjacent_friction_residue",
        "gtos_vnext_accepted_candidate_m1_fill_source_repair",
        "gtos_vnext_sierra_depth_source_acquisition",
        "gtos_vnext_risk_proxy_stress_cost",
        "gtos_vnext_gate_selector_session_timeframe",
        "gtos_vnext_adverse_stop_first_execution",
        "gtos_vnext_branch_followup_computation",
        "gtos_vnext_branch_ambiguity_collapse",
        "gtos_vnext_branch_implementation_replay",
        "gtos_vnext_cp280_scorer_filter_router",
        "gtos_vnext_observable_execution",
        "gtos_vnext_unified_execution_action_work_order",
        "gtos_vnext_target_stop_ordering_execution_scoring",
        "gtos_vnext_branch_replay_execution_repair",
        "gtos_vnext_unified_candidate_action_execution",
        "gtos_vnext_unified_candidate_scoring_execution",
        "gtos_vnext_unified_execution_decision",
        "gtos_vnext_unified_shadow_source_materialization",
        "gtos_vnext_scid_forward_source_capture",
        "gtos_vnext_scid_future_capture_source_state",
        "gtos_vnext_scid_combined_source_capture_poi_bounds",
        "gtos_vnext_scid_noapi_source_repair",
        "gtos_vnext_pre_ai_h1_poi_source_gap",
        "gtos_vnext_shadow_source_log_materialization",
        "gtos_vnext_tick_m15_execution_friction",
        "gtos_vnext_tick_m15_target_control",
        "gtos_vnext_main_orch24_tick_structural_entry_runtime",
        "gtos_vnext_main_orch24_structural_repair_action_runtime",
        "gtos_vnext_main_orch24_action_completeness_residual_r_runtime",
        "gtos_vnext_main_orch24_implementation_selection_runtime",
        "gtos_vnext_main_orch24_snapshot_dependency_repair_runtime",
        "gtos_vnext_main_orch48_final_review_selector_runtime",
        "gtos_vnext_ltf_path_geometry_source_runtime",
        "gtos_vnext_instrument_expansion_market_session_runtime",
        "gtos_vnext_main_orch24_source_accepted_action_repair_runtime",
        "gtos_vnext_main_orch24_swing_protected_source_repair_runtime",
        "gtos_vnext_main_orch24_source_m15_branch_repair_runtime",
        "gtos_vnext_main_orch24_live_mechanical_geometry_outcome_runtime",
        "gtos_vnext_main_orch24_unified_candidate_path_proxy_runtime",
        "gtos_vnext_tick_source_recovery_quote_contract_runtime",
        "gtos_vnext_legacy_live_shadow_decision_runtime",
        "gtos_vnext_scid_target_horizon_control",
        "expanded_market_reduced_surface",
        "ai_decision_architecture",
    ]
    assert block["artifact_source_component_exclusions"] == []
    assert block["implementation_action_decision_enabled"] is True
    assert "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS" in block[
        "implementation_action_follow_tokens"
    ]
    assert "KEEP_SOURCE_REPAIRED_PROXY_AS_DEFAULT_OFF_SCORER_OR_GUARD_INPUT" in block[
        "implementation_action_follow_tokens"
    ]
    assert "REPAIRED_PROXY_DEFAULT_OFF_SCORER_WITH_GUARDS" in block[
        "implementation_action_follow_tokens"
    ]
    assert "UNIFIED_CANDIDATE_DEFAULT_OFF_SCORER_WITH_SOURCE_GUARDS" in block[
        "implementation_action_follow_tokens"
    ]
    assert "KEEP_NOFILL_CHALLENGER_COMPARATOR_STRONG_POSITIVE" in block[
        "implementation_action_follow_tokens"
    ]
    assert "IMPLEMENT_AVOID_INVERSE_OR_FAILURE_FILTER_SCOPE" in block[
        "implementation_action_avoid_tokens"
    ]
    assert "KEEP_SOURCE_REPAIRED_NEGATIVE_PROXY_AS_AVOID_OR_REDESIGN_INPUT" in block[
        "implementation_action_avoid_tokens"
    ]
    assert "UNIFIED_CANDIDATE_AVOID_OR_FAILURE_FILTER" in block[
        "implementation_action_avoid_tokens"
    ]
    assert "CONVERT_STRONG_NEGATIVE_TO_AVOID_INVERSE_OR_FAILURE_FILTER" in block[
        "implementation_action_avoid_tokens"
    ]
    assert "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R" in block[
        "implementation_action_mixed_tokens"
    ]
    assert "ORDERING_OR_INTERVAL_COLLAPSE_BEFORE_DIRECTIONAL_USE" in block[
        "implementation_action_mixed_tokens"
    ]
    assert "MERGE_SOURCE_REPAIRED_FLAT_PROXY_AS_CONTEXT" in block[
        "implementation_action_mixed_tokens"
    ]
    assert "SOURCE_GEOMETRY_REPAIR_OR_GUARD_BINDING_REQUIRED" in block[
        "implementation_action_mixed_tokens"
    ]
    assert "REDESIGN_NEGATIVE_PROXY_OR_MERGE_AS_CONTEXT_FEATURE" in block[
        "implementation_action_mixed_tokens"
    ]
    assert block["failure_intelligence_guard_enabled"] is True
    assert "SOURCE_REPAIR" in block["failure_intelligence_non_executable_tokens"]
    assert "AVOID_FILTER" in block["failure_intelligence_executable_avoid_tokens"]
    assert block["orderflow_diagnostic_guard_enabled"] is True
    assert "DATABENTO" in block["orderflow_diagnostic_tokens"]
    assert "SCID" in block["orderflow_diagnostic_tokens"]
    assert block["orderflow_runtime_validated_fields"] == [
        "orderflow_runtime_validated",
        "proxy_transfer_validated",
        "futures_to_cfd_transfer_validated",
        "source_transfer_validated",
    ]
    assert "VALIDATED_FUTURES_PROXY_TRANSFER" in block["orderflow_runtime_ready_tokens"]
    assert block["bridge_diagnostics_enabled"] is True
    assert block["bridge_diagnostic_artifact_paths"] == [
        DEFAULT_BRIDGE_DIAGNOSTIC_ARTIFACT_PATH.as_posix()
    ]
    assert block["pre_ai_route_timeframes"] == ["M1", "M5", "M15", "H1", "H4", "D1"]
    assert block["pre_ai_route_frameworks"] == ["ob_retest", "fvg_fill", "breaker_re_entry"]
    assert block["pre_ai_route_families"] == [
        "moonshot_mechanical",
        "moonshot_control_screen",
        "moonshot_control_screen_route_queue",
        "moonshot_gtos_replay_blocker",
        "moonshot_accepted_builder",
        "moonshot_accepted_builder_binding",
        "moonshot_accepted_builder_branch",
        "moonshot_accepted_builder_entry_adverse",
        "moonshot_accepted_builder_family",
        "moonshot_accepted_builder_m15",
        "moonshot_accepted_builder_m1",
        "moonshot_accepted_builder_positive",
        "moonshot_accepted_builder_source",
        "moonshot_accepted_builder_rejected_repair",
        "moonshot_branch_followup_binding",
        "moonshot_branch_followup_branch",
        "moonshot_branch_followup_bucket",
        "moonshot_branch_followup_family",
        "moonshot_branch_followup_m15",
        "moonshot_branch_followup_m1",
        "moonshot_branch_followup_positive",
        "moonshot_branch_followup_source",
        "moonshot_branch_ambiguity_collapse",
        "moonshot_branch_implementation_replay",
        "main_orch24_snapshot_dependency_repair",
        "numeric_router",
        "survivor_failure_proxy",
        "cp281_native_rule",
        "mechanical_ai_selector",
        "nofill_mechanical",
        "source_discovery",
    ]
    assert "shadow_source_guard" in block["pre_ai_route_source_components"]
    assert "market_gap_code" in block["pre_ai_route_source_components"]
    assert "nofill_far_miss_avoid" in block["pre_ai_route_source_components"]
    assert "nofill_far_miss_retest" in block["pre_ai_route_source_components"]
    assert "nofill_near_miss_market_entry" in block["pre_ai_route_source_components"]
    assert "nofill_near_miss_offset" in block["pre_ai_route_source_components"]
    assert "nofill_near_miss_source_requirement" in block["pre_ai_route_source_components"]
    assert "source_repair_proof" in block["pre_ai_route_source_components"]
    assert "target_stop_ordering" in block["pre_ai_route_source_components"]
    assert "entry_adverse_stop_first" in block["pre_ai_route_source_components"]
    assert "adverse_stop_first_execution" in block["pre_ai_route_source_components"]
    assert "entry_adverse_execution" in block["pre_ai_route_source_components"]
    assert "targetstop_na_binding_repair" in block["pre_ai_route_source_components"]
    assert "target_stop_path_control" in block["pre_ai_route_source_components"]
    assert "gbpjpy_long_adverse_avoid_reclass" in block["pre_ai_route_source_components"]
    assert "ohlc_challenger_frontier_action" in block["pre_ai_route_source_components"]
    assert "ohlc_challenger_frontier_route" in block["pre_ai_route_source_components"]
    assert "ohlc_control_screen" in block["pre_ai_route_source_components"]
    assert "ohlc_control_screen_route_queue" in block["pre_ai_route_source_components"]
    assert "gtos_replay_blocker" in block["pre_ai_route_source_components"]
    assert "gtos_accepted_builder" in block["pre_ai_route_source_components"]
    assert "gtos_accepted_builder_binding" in block["pre_ai_route_source_components"]
    assert "gtos_accepted_builder_branch" in block["pre_ai_route_source_components"]
    assert "gtos_accepted_builder_entry_adverse" in block["pre_ai_route_source_components"]
    assert "gtos_accepted_builder_family" in block["pre_ai_route_source_components"]
    assert "gtos_accepted_builder_m15" in block["pre_ai_route_source_components"]
    assert "gtos_accepted_builder_m1" in block["pre_ai_route_source_components"]
    assert "gtos_accepted_builder_positive" in block["pre_ai_route_source_components"]
    assert "gtos_accepted_builder_source" in block["pre_ai_route_source_components"]
    assert "gtos_accepted_builder_rejected_repair" in block["pre_ai_route_source_components"]
    for source_component in (
        "gtos_branch_followup_binding",
        "gtos_branch_followup_branch",
        "gtos_branch_followup_bucket",
        "gtos_branch_followup_family",
        "gtos_branch_followup_m15",
        "gtos_branch_followup_m1",
        "gtos_branch_followup_positive",
        "gtos_branch_followup_source",
        "gtos_branch_ambiguity_branch",
        "gtos_branch_ambiguity_bucket",
        "gtos_branch_ambiguity_cause_matrix",
        "gtos_branch_ambiguity_interval",
        "gtos_branch_ambiguity_m15_same_bar",
        "gtos_branch_ambiguity_ordering",
        "gtos_branch_ambiguity_source_repair",
        "gtos_branch_impl_action",
        "gtos_branch_impl_candidate",
        "gtos_branch_impl_cause_matrix",
        "gtos_branch_impl_code_replay",
        "gtos_branch_impl_control_source_split",
        "gtos_branch_impl_full_outcome",
        "gtos_branch_impl_guarded_scope_scorer",
        "gtos_branch_impl_m1_chronology",
        "gtos_branch_impl_m1_interval",
        "gtos_branch_impl_m1_support",
        "gtos_branch_impl_next_compute",
        "gtos_branch_impl_numeric_decision",
        "gtos_branch_impl_numeric_router",
        "gtos_branch_impl_ordering_collapse",
        "gtos_branch_impl_positive_challenger",
        "gtos_branch_impl_replay_builder",
        "gtos_branch_impl_replay_matrix",
        "gtos_branch_impl_router_scoring",
        "gtos_branch_impl_score_export",
        "gtos_branch_impl_source_spread_recompute",
    ):
        assert source_component in block["pre_ai_route_source_components"]
    for source_component in (
        "observable_execution_follow_scorer",
        "observable_execution_control_guard",
        "observable_execution_denominator_guard",
        "observable_execution_source_policy_guard",
        "observable_execution_source_repair",
        "observable_execution_horizon_repair",
        "observable_execution_avoid_filter",
    ):
        assert source_component in block["pre_ai_route_source_components"]
    assert "expanded_market_source_expansion" in block["pre_ai_route_source_components"]
    assert "expanded_market_source_geometry" in block["pre_ai_route_source_components"]
    assert "expanded_market_source_gap" in block["pre_ai_route_source_components"]
    for source_component in (
        "ltf_path_source_blocked_guard",
        "ltf_path_source_recovered_context",
        "ltf_path_contract_complete_context",
        "ltf_path_strategy_candidate_context",
        "ltf_path_source_context",
        "g3_geometry_source_repair_guard",
        "g3_geometry_stop_first_avoid",
        "g3_geometry_target_first_follow",
        "g3_geometry_entry_missed_nofill",
        "g3_geometry_same_m1_ambiguity_guard",
    ):
        assert source_component in block["pre_ai_route_source_components"]
    assert "data_inventory" in block["pre_ai_route_source_components"]
    assert "repaired_proxy_symbol_surface" in block["pre_ai_route_source_components"]
    assert "repaired_proxy_score_bridge" in block["pre_ai_route_source_components"]
    assert "repaired_proxy_symbol_action" in block["pre_ai_route_source_components"]
    assert "repaired_proxy_cost_symbol" in block["pre_ai_route_source_components"]
    assert "unified_candidate_market_rollup" in block["pre_ai_route_source_components"]
    assert "unified_candidate_default_off_scorer" in block[
        "pre_ai_route_source_components"
    ]
    assert "unified_candidate_guard" in block["pre_ai_route_source_components"]
    assert "unified_candidate_source_repair" in block[
        "pre_ai_route_source_components"
    ]
    assert "default_off_application" in block["pre_ai_route_source_components"]
    assert "default_off_scorer_application" in block[
        "pre_ai_route_source_components"
    ]
    assert "registry_scorer_module" in block["pre_ai_route_source_components"]
    for source_component in (
        "ai_hallucination_guard",
        "legacy_v4_lira_guard",
        "ai_v3_cascade_preferred",
        "no_ai_shadow_observer",
        "ai_source_lineage_materialization_guard",
        "ai_routing_architecture_context",
        "ai_narrowing_policy_residue",
        "ai_limit_order_prompt_context",
    ):
        assert source_component in block["pre_ai_route_source_components"]
    for source_component in (
        "unified_candidate_action_branch_avoid_filter",
        "unified_candidate_action_fillability_redesign",
        "unified_candidate_action_market_entry_comparator",
        "unified_candidate_action_provenance_guard",
        "unified_candidate_action_market_gap_avoid_inverse",
        "unified_candidate_action_market_gap_entry_geometry",
        "unified_candidate_action_source_expansion",
        "unified_candidate_action_concentration_restress",
        "unified_candidate_action_symbol_session",
        "unified_candidate_action_scorer_spec",
        "unified_candidate_scoring_avoid_inverse_execution",
        "unified_candidate_scoring_entry_geometry_execution",
        "unified_execution_decision_avoid_redirect",
        "unified_execution_decision_fillability_retest_redesign",
        "unified_execution_decision_market_entry_challenger",
        "unified_execution_decision_market_gap_avoid_inverse",
        "unified_execution_decision_market_gap_entry_geometry",
        "unified_execution_decision_provenance_guard",
        "unified_execution_decision_source_expansion_guard",
        "unified_candidate_variant_avoid_inverse",
        "unified_candidate_variant_entry_geometry",
        "unified_candidate_variant_source_expansion",
        "unified_shadow_scorer_branch_failure_avoid_filter",
        "unified_shadow_scorer_avoid_filter",
        "unified_shadow_scorer_market_gap_avoid_filter",
        "unified_shadow_scorer_entry_geometry",
        "unified_shadow_scorer_market_gap_entry_geometry",
        "unified_shadow_scorer_market_entry_comparator",
        "unified_shadow_scorer_branch_proxy_scorer",
        "unified_shadow_scorer_source_materialization",
        "unified_source_materialization_execution",
        "scid_future_capture_baseline_control",
        "scid_future_capture_framework_setup",
        "scid_future_capture_entry_reference",
        "scid_future_capture_side_direction",
        "scid_future_capture_stop_reference",
        "scid_future_capture_target_reference",
        "scid_future_capture_lifecycle_status",
        "scid_combined_framework_setup_source_gap",
        "scid_combined_orderflow_depth_source_gap",
        "scid_combined_entry_reference_source_gap",
        "scid_combined_side_direction_source_gap",
        "scid_combined_stop_reference_source_gap",
        "scid_combined_target_reference_source_gap",
        "scid_combined_lifecycle_source_gap",
        "scid_combined_ltf_path_source_gap",
        "scid_combined_poi_bounds_source_gap",
        "pre_ai_h1_poi_bullish_source_gap",
        "pre_ai_h1_poi_bearish_source_gap",
        "shadow_action_required_source_gap",
        "shadow_candidate_poi_source_gap",
        "shadow_external_source_blocker",
        "shadow_framework_qualification_source_gap",
        "shadow_generic_source_materialization_gap",
        "shadow_join_status_source_gap",
        "shadow_missing_exact_required_fields",
        "shadow_path_contract_source_gap",
        "tick_m15_execution_friction_spread_competes",
        "tick_m15_execution_friction_movement_dominates",
        "tick_m15_execution_friction_weak_denominator",
        "tick_m15_target_control_negative_alignment",
        "tick_m15_target_control_placebo_ready_positive",
        "tick_m15_target_control_flat_or_negative_abs",
        "tick_m15_target_control_small_n_context",
        "main_orch24_tick_structural_kill_guard",
        "main_orch24_tick_redesign_source_repair",
        "main_orch24_tick_preserve_source_acquisition",
        "main_orch24_tick_negative_proxy_guard",
        "main_orch24_tick_positive_proxy_follow",
        "main_orch24_nas100_tick_order_repair_follow",
        "main_orch24_entry_offset_025r_kill_guard",
        "main_orch24_entry_offset_050r_challenger",
        "main_orch24_entry_offset_tick_source_acquisition",
        "main_orch24_structural_metadata_default_off_follow",
        "main_orch24_structural_ltf_positive_follow",
        "main_orch24_structural_pending_lifecycle_context",
        "main_orch24_structural_fvg_ob_shared_path_context",
        "main_orch24_structural_context",
        "main_orch24_structural_source_repair_requirement",
        "main_orch24_snapshot_dependency_source_repair_requirement",
        "main_orch24_structural_fvg_ob_single_family_kill_guard",
        "main_orch24_structural_standalone_fvg_kill_guard",
        "main_orch24_structural_swing_unprotected_kill_guard",
        "main_orch24_structural_duplicate_redesign_guard",
        "main_orch24_structural_ltf_adverse_redesign_guard",
        "main_orch24_structural_prefill_redesign_guard",
        "main_orch24_structural_gbpjpy_long_adverse_redesign_guard",
        "main_orch24_structural_repair_redesign_guard",
        "main_orch24_structural_repair_kill_guard",
        "main_orch24_source_accepted_m15_ordering_follow",
        "main_orch24_source_accepted_source_cost_proxy_follow",
        "main_orch24_source_accepted_degraded_redesign_source_acquisition",
        "main_orch24_swing_protected_tick_repair_follow",
        "main_orch24_swing_protected_unprotected_stop_guard",
        "main_orch24_swing_protected_negative_proxy_guard",
        "main_orch24_swing_protected_source_acquisition",
        "main_orch24_swing_protected_neutral_context",
        "main_orch24_source_m15_ordering_positive_follow",
        "main_orch24_source_m15_kill_or_no_fill_guard",
        "main_orch24_source_m15_redesign_guard",
        "main_orch24_source_m15_source_acquisition",
        "main_orch24_source_m15_default_off_context",
        "main_orch24_source_m15_neutral_context",
        "main_orch24_live_mechanical_forward_follow",
        "main_orch24_live_mechanical_stop_or_nofill_avoid",
        "main_orch24_live_mechanical_source_acquisition",
        "main_orch24_live_mechanical_ambiguous_path_guard",
        "main_orch24_live_mechanical_pending_lifecycle_guard",
        "main_orch24_live_mechanical_kill_guard",
        "main_orch24_live_mechanical_redesign_guard",
        "main_orch24_live_mechanical_context",
        "main_orch24_live_mechanical_geometry_proxy_context",
        "main_orch24_unified_tick_m15_path_follow",
        "main_orch24_unified_tick_m15_path_inverse_avoid",
        "main_orch24_unified_m1_spread_fill_target_follow",
        "main_orch24_unified_m1_spread_fill_stop_or_nofill_avoid",
        "main_orch24_unified_m1_fill_ordering_source_repair",
        "main_orch24_unified_m1_entry_materialized_context",
        "main_orch24_unified_branch_proxy_follow",
        "main_orch24_unified_branch_proxy_avoid",
        "main_orch24_unified_branch_proxy_source_repair",
        "main_orch24_unified_ready8_source_capture_repair_replay",
        "main_orch24_unified_split_summary_replay_attribution",
        "tick_source_recovery_path_ready_context",
        "tick_source_recovery_ordered_path_source_acquisition",
        "tick_source_recovery_quote_tick_nofill_avoid",
        "tick_source_recovery_separate_fill_path_source_acquisition",
        "tick_source_recovery_opening_drive_source_acquisition",
        "tick_source_recovery_stop_first_avoid",
        "tick_source_recovery_target_first_follow",
        "tick_source_recovery_no_entry_touch_source_acquisition",
        "tick_source_recovery_no_terminal_pending_guard",
        "tick_source_recovery_geometry_join_context",
        "tick_source_recovery_source_hash_context",
        "tick_source_recovery_partial_coverage_source_acquisition",
        "legacy_live_shadow_v2_replay_context",
        "legacy_live_shadow_v2b_forward_source_acquisition",
        "legacy_live_shadow_fvg_ob_source_acquisition",
        "legacy_live_shadow_j46_j49_policy_follow",
        "legacy_live_shadow_s79_side_aware_context",
        "legacy_live_shadow_nofill_capture_source_acquisition",
        "legacy_live_shadow_sierra_orderflow_diagnostic_context",
        "legacy_live_shadow_strategy_replay_context",
        "legacy_live_shadow_trailing_stop_shadow_context",
        "legacy_live_shadow_xagusd_account_history_source_acquisition",
        "main_orch24_standalone_fvg_negative_guard",
        "scid_neutral_target_candidate_context",
        "scid_neutral_target_control_context",
        "scid_target_control_card_rank_non_discriminative",
        "scid_target_horizon_fail_closed_source_repair",
        "scid_target_horizon_neutral_only",
        "scid_target_horizon_source_field_requirement",
        "static_limit_adaptive_entry_challenger",
        "static_limit_adaptive_entry_source_requirement",
        "broker_actual_r_slippage_source_repair",
        "trade_record_execution_source_repair",
        "orderflow_pending_lifecycle_source_gap",
        "execution_source_capture_contract_context",
        "execution_replay_source_contract_context",
    ):
        assert source_component in block["pre_ai_route_source_components"]
    assert "sierra_depth_source_gap" in block["pre_ai_route_source_components"]
    assert "sierra_depth_window_sample_block" in block["pre_ai_route_source_components"]
    assert "sierra_depth_in_window_clear_repair" in block["pre_ai_route_source_components"]
    assert "sierra_depth_live_feature_status" in block["pre_ai_route_source_components"]
    assert "sierra_depth_source_acquisition" in block["pre_ai_route_source_components"]
    assert "risk_source_cost_cap" in block["pre_ai_route_source_components"]
    assert "risk_cost_fill_proxy" in block["pre_ai_route_source_components"]
    assert "risk_rstyle_proxy_outcome" in block["pre_ai_route_source_components"]
    assert "risk_source_stress_acquisition" in block["pre_ai_route_source_components"]
    assert "risk_stress_robustness" in block["pre_ai_route_source_components"]
    assert "risk_sizing_policy" in block["pre_ai_route_source_components"]
    assert "risk_ai_cost_control" in block["pre_ai_route_source_components"]
    assert "risk_proxy_gap_status" in block["pre_ai_route_source_components"]
    assert "risk_touch_count_proxy" in block["pre_ai_route_source_components"]
    assert "risk_proxy_stress_cost_context" in block["pre_ai_route_source_components"]
    for source_component in (
        "gate_touch_count",
        "gate_touch_count_gate",
        "gate_sl_beyond_ob",
        "gate_sl_beyond_ob_l2",
        "gate_pre_ai_poi_availability",
        "gate_pre_ai_h1_poi_availability",
        "gate_cross_instrument_correlation",
        "gate_cross_instrument_correlation_gate",
        "confidence_filter_quarantine",
        "fvg_ob_framework_repair",
        "l2_entry_in_ob_rejection_value",
        "l2_h1_poi_rejection_value",
        "l2_m15_choch_rejection_value",
        "l2_sl_beyond_ob_rejection_value",
        "rejected_candidate_blocked_limit_value",
        "rejected_candidate_c1_failed_value",
        "rejected_candidate_c2_m15_opposing_value",
        "rejected_candidate_c3_direction_mismatch_value",
        "rejected_candidate_no_qualifying_h1_poi_value",
        "rejected_candidate_no_reason_logged_value",
        "rejected_candidate_ob_proximity_value",
        "rejected_candidate_other_unknown_value",
        "rejected_candidate_parse_error_value",
        "rejected_candidate_prescreen_no_direction_value",
        "ltf_selector_repair",
        "kill_scope_preservation",
        "framework_gate_selector",
        "selector_shadow_source_guard",
        "session_timeframe_selector",
    ):
        assert source_component in block["pre_ai_route_source_components"]
    assert block["post_l2_evaluate_route_variants"] is True
    assert block["post_l2_prune_route_variants_to_artifact_scopes"] is True
    assert block["post_l2_match_artifact_scopes_directly"] is True
    assert block["post_l2_route_use_candidate_framework_only"] is True
    assert block["post_l2_route_timeframes"] == ["M1", "M5", "M15", "H1", "H4", "D1"]
    assert block["post_l2_route_families"] == [
        "moonshot_mechanical",
        "moonshot_control_screen",
        "moonshot_control_screen_route_queue",
        "moonshot_gtos_replay_blocker",
        "moonshot_accepted_builder",
        "moonshot_accepted_builder_binding",
        "moonshot_accepted_builder_branch",
        "moonshot_accepted_builder_entry_adverse",
        "moonshot_accepted_builder_family",
        "moonshot_accepted_builder_m15",
        "moonshot_accepted_builder_m1",
        "moonshot_accepted_builder_positive",
        "moonshot_accepted_builder_source",
        "moonshot_accepted_builder_rejected_repair",
        "moonshot_branch_followup_binding",
        "moonshot_branch_followup_branch",
        "moonshot_branch_followup_bucket",
        "moonshot_branch_followup_family",
        "moonshot_branch_followup_m15",
        "moonshot_branch_followup_m1",
        "moonshot_branch_followup_positive",
        "moonshot_branch_followup_source",
        "moonshot_branch_ambiguity_collapse",
        "moonshot_branch_implementation_replay",
        "main_orch24_snapshot_dependency_repair",
        "numeric_router",
        "cp281_native_rule",
        "mechanical_ai_selector",
        "nofill_mechanical",
        "source_discovery",
    ]
    assert "nofill_far_miss_avoid" in block["post_l2_route_source_components"]
    assert "nofill_near_miss_market_entry" in block["post_l2_route_source_components"]
    assert "nofill_near_miss_offset" in block["post_l2_route_source_components"]
    assert "nofill_near_miss_source_requirement" in block["post_l2_route_source_components"]
    assert "source_repair_proof" in block["post_l2_route_source_components"]
    for source_component in (
        "lifecycle_still_pending_no_fill_source_guard",
        "lifecycle_wrong_side_no_fill_source_guard",
        "trade_index_lifecycle_action_required_source_repair",
        "opportunity_lifecycle_reset_policy_source_guard",
    ):
        assert source_component in block["post_l2_route_source_components"]
    assert "target_stop_ordering" in block["post_l2_route_source_components"]
    assert "entry_adverse_stop_first" in block["post_l2_route_source_components"]
    assert "adverse_stop_first_execution" in block["post_l2_route_source_components"]
    assert "entry_adverse_execution" in block["post_l2_route_source_components"]
    assert "targetstop_na_binding_repair" in block["post_l2_route_source_components"]
    assert "target_stop_path_control" in block["post_l2_route_source_components"]
    assert "gbpjpy_long_adverse_avoid_reclass" in block["post_l2_route_source_components"]
    assert "ohlc_challenger_frontier_action" in block["post_l2_route_source_components"]
    assert "ohlc_challenger_frontier_route" in block["post_l2_route_source_components"]
    assert "ohlc_control_screen" in block["post_l2_route_source_components"]
    assert "ohlc_control_screen_route_queue" in block["post_l2_route_source_components"]
    assert "gtos_replay_blocker" in block["post_l2_route_source_components"]
    assert "gtos_accepted_builder" in block["post_l2_route_source_components"]
    assert "gtos_accepted_builder_binding" in block["post_l2_route_source_components"]
    assert "gtos_accepted_builder_branch" in block["post_l2_route_source_components"]
    assert "gtos_accepted_builder_entry_adverse" in block["post_l2_route_source_components"]
    assert "gtos_accepted_builder_family" in block["post_l2_route_source_components"]
    assert "gtos_accepted_builder_m15" in block["post_l2_route_source_components"]
    assert "gtos_accepted_builder_m1" in block["post_l2_route_source_components"]
    assert "gtos_accepted_builder_positive" in block["post_l2_route_source_components"]
    assert "gtos_accepted_builder_source" in block["post_l2_route_source_components"]
    assert "gtos_accepted_builder_rejected_repair" in block["post_l2_route_source_components"]
    for source_component in (
        "gtos_branch_followup_binding",
        "gtos_branch_followup_branch",
        "gtos_branch_followup_bucket",
        "gtos_branch_followup_family",
        "gtos_branch_followup_m15",
        "gtos_branch_followup_m1",
        "gtos_branch_followup_positive",
        "gtos_branch_followup_source",
        "gtos_branch_ambiguity_branch",
        "gtos_branch_ambiguity_bucket",
        "gtos_branch_ambiguity_cause_matrix",
        "gtos_branch_ambiguity_interval",
        "gtos_branch_ambiguity_m15_same_bar",
        "gtos_branch_ambiguity_ordering",
        "gtos_branch_ambiguity_source_repair",
        "gtos_branch_impl_action",
        "gtos_branch_impl_candidate",
        "gtos_branch_impl_cause_matrix",
        "gtos_branch_impl_code_replay",
        "gtos_branch_impl_control_source_split",
        "gtos_branch_impl_full_outcome",
        "gtos_branch_impl_guarded_scope_scorer",
        "gtos_branch_impl_m1_chronology",
        "gtos_branch_impl_m1_interval",
        "gtos_branch_impl_m1_support",
        "gtos_branch_impl_next_compute",
        "gtos_branch_impl_numeric_decision",
        "gtos_branch_impl_numeric_router",
        "gtos_branch_impl_ordering_collapse",
        "gtos_branch_impl_positive_challenger",
        "gtos_branch_impl_replay_builder",
        "gtos_branch_impl_replay_matrix",
        "gtos_branch_impl_router_scoring",
        "gtos_branch_impl_score_export",
        "gtos_branch_impl_source_spread_recompute",
    ):
        assert source_component in block["post_l2_route_source_components"]
    for source_component in (
        "observable_execution_follow_scorer",
        "observable_execution_control_guard",
        "observable_execution_denominator_guard",
        "observable_execution_source_policy_guard",
        "observable_execution_source_repair",
        "observable_execution_horizon_repair",
        "observable_execution_avoid_filter",
    ):
        assert source_component in block["post_l2_route_source_components"]
    assert "expanded_market_source_expansion" in block["post_l2_route_source_components"]
    assert "expanded_market_source_geometry" in block["post_l2_route_source_components"]
    assert "expanded_market_source_gap" in block["post_l2_route_source_components"]
    for source_component in (
        "ltf_path_source_blocked_guard",
        "ltf_path_source_recovered_context",
        "ltf_path_contract_complete_context",
        "ltf_path_strategy_candidate_context",
        "ltf_path_source_context",
        "g3_geometry_source_repair_guard",
        "g3_geometry_stop_first_avoid",
        "g3_geometry_target_first_follow",
        "g3_geometry_entry_missed_nofill",
        "g3_geometry_same_m1_ambiguity_guard",
    ):
        assert source_component in block["post_l2_route_source_components"]
    assert "data_inventory" in block["post_l2_route_source_components"]
    assert "repaired_proxy_symbol_surface" in block["post_l2_route_source_components"]
    assert "repaired_proxy_score_bridge" in block["post_l2_route_source_components"]
    assert "repaired_proxy_symbol_action" in block["post_l2_route_source_components"]
    assert "repaired_proxy_cost_symbol" in block["post_l2_route_source_components"]
    assert "unified_candidate_market_rollup" in block[
        "post_l2_route_source_components"
    ]
    assert "unified_candidate_default_off_scorer" in block[
        "post_l2_route_source_components"
    ]
    assert "unified_candidate_guard" in block["post_l2_route_source_components"]
    assert "unified_candidate_source_repair" in block[
        "post_l2_route_source_components"
    ]
    assert "default_off_application" in block["post_l2_route_source_components"]
    assert "default_off_scorer_application" in block[
        "post_l2_route_source_components"
    ]
    assert "registry_scorer_module" in block["post_l2_route_source_components"]
    for source_component in (
        "ai_hallucination_guard",
        "legacy_v4_lira_guard",
        "ai_v3_cascade_preferred",
        "no_ai_shadow_observer",
        "ai_source_lineage_materialization_guard",
        "ai_routing_architecture_context",
        "ai_narrowing_policy_residue",
        "ai_limit_order_prompt_context",
    ):
        assert source_component in block["post_l2_route_source_components"]
    for source_component in (
        "unified_candidate_action_branch_avoid_filter",
        "unified_candidate_action_fillability_redesign",
        "unified_candidate_action_market_entry_comparator",
        "unified_candidate_action_provenance_guard",
        "unified_candidate_action_market_gap_avoid_inverse",
        "unified_candidate_action_market_gap_entry_geometry",
        "unified_candidate_action_source_expansion",
        "unified_candidate_action_concentration_restress",
        "unified_candidate_action_symbol_session",
        "unified_candidate_action_scorer_spec",
        "unified_candidate_scoring_avoid_inverse_execution",
        "unified_candidate_scoring_entry_geometry_execution",
        "unified_execution_decision_avoid_redirect",
        "unified_execution_decision_fillability_retest_redesign",
        "unified_execution_decision_market_entry_challenger",
        "unified_execution_decision_market_gap_avoid_inverse",
        "unified_execution_decision_market_gap_entry_geometry",
        "unified_execution_decision_provenance_guard",
        "unified_execution_decision_source_expansion_guard",
        "unified_candidate_variant_avoid_inverse",
        "unified_candidate_variant_entry_geometry",
        "unified_candidate_variant_source_expansion",
        "unified_shadow_scorer_branch_failure_avoid_filter",
        "unified_shadow_scorer_avoid_filter",
        "unified_shadow_scorer_market_gap_avoid_filter",
        "unified_shadow_scorer_entry_geometry",
        "unified_shadow_scorer_market_gap_entry_geometry",
        "unified_shadow_scorer_market_entry_comparator",
        "unified_shadow_scorer_branch_proxy_scorer",
        "unified_shadow_scorer_source_materialization",
        "unified_source_materialization_execution",
        "scid_future_capture_baseline_control",
        "scid_future_capture_framework_setup",
        "scid_future_capture_entry_reference",
        "scid_future_capture_side_direction",
        "scid_future_capture_stop_reference",
        "scid_future_capture_target_reference",
        "scid_future_capture_lifecycle_status",
        "scid_combined_framework_setup_source_gap",
        "scid_combined_orderflow_depth_source_gap",
        "scid_combined_entry_reference_source_gap",
        "scid_combined_side_direction_source_gap",
        "scid_combined_stop_reference_source_gap",
        "scid_combined_target_reference_source_gap",
        "scid_combined_lifecycle_source_gap",
        "scid_combined_ltf_path_source_gap",
        "scid_combined_poi_bounds_source_gap",
        "pre_ai_h1_poi_bullish_source_gap",
        "pre_ai_h1_poi_bearish_source_gap",
        "shadow_action_required_source_gap",
        "shadow_candidate_poi_source_gap",
        "shadow_external_source_blocker",
        "shadow_framework_qualification_source_gap",
        "shadow_generic_source_materialization_gap",
        "shadow_join_status_source_gap",
        "shadow_missing_exact_required_fields",
        "shadow_path_contract_source_gap",
        "tick_m15_execution_friction_spread_competes",
        "tick_m15_execution_friction_movement_dominates",
        "tick_m15_execution_friction_weak_denominator",
        "tick_m15_target_control_negative_alignment",
        "tick_m15_target_control_placebo_ready_positive",
        "tick_m15_target_control_flat_or_negative_abs",
        "tick_m15_target_control_small_n_context",
        "main_orch24_tick_structural_kill_guard",
        "main_orch24_tick_redesign_source_repair",
        "main_orch24_tick_preserve_source_acquisition",
        "main_orch24_tick_negative_proxy_guard",
        "main_orch24_tick_positive_proxy_follow",
        "main_orch24_nas100_tick_order_repair_follow",
        "main_orch24_entry_offset_025r_kill_guard",
        "main_orch24_entry_offset_050r_challenger",
        "main_orch24_entry_offset_tick_source_acquisition",
        "main_orch24_structural_metadata_default_off_follow",
        "main_orch24_structural_ltf_positive_follow",
        "main_orch24_structural_pending_lifecycle_context",
        "main_orch24_structural_fvg_ob_shared_path_context",
        "main_orch24_structural_context",
        "main_orch24_structural_source_repair_requirement",
        "main_orch24_snapshot_dependency_source_repair_requirement",
        "main_orch24_structural_fvg_ob_single_family_kill_guard",
        "main_orch24_structural_standalone_fvg_kill_guard",
        "main_orch24_structural_swing_unprotected_kill_guard",
        "main_orch24_structural_duplicate_redesign_guard",
        "main_orch24_structural_ltf_adverse_redesign_guard",
        "main_orch24_structural_prefill_redesign_guard",
        "main_orch24_structural_gbpjpy_long_adverse_redesign_guard",
        "main_orch24_structural_repair_redesign_guard",
        "main_orch24_structural_repair_kill_guard",
        "main_orch24_source_accepted_m15_ordering_follow",
        "main_orch24_source_accepted_source_cost_proxy_follow",
        "main_orch24_source_accepted_degraded_redesign_source_acquisition",
        "main_orch24_swing_protected_tick_repair_follow",
        "main_orch24_swing_protected_unprotected_stop_guard",
        "main_orch24_swing_protected_negative_proxy_guard",
        "main_orch24_swing_protected_source_acquisition",
        "main_orch24_swing_protected_neutral_context",
        "main_orch24_source_m15_ordering_positive_follow",
        "main_orch24_source_m15_kill_or_no_fill_guard",
        "main_orch24_source_m15_redesign_guard",
        "main_orch24_source_m15_source_acquisition",
        "main_orch24_source_m15_default_off_context",
        "main_orch24_source_m15_neutral_context",
        "main_orch24_live_mechanical_forward_follow",
        "main_orch24_live_mechanical_stop_or_nofill_avoid",
        "main_orch24_live_mechanical_source_acquisition",
        "main_orch24_live_mechanical_ambiguous_path_guard",
        "main_orch24_live_mechanical_pending_lifecycle_guard",
        "main_orch24_live_mechanical_kill_guard",
        "main_orch24_live_mechanical_redesign_guard",
        "main_orch24_live_mechanical_context",
        "main_orch24_live_mechanical_geometry_proxy_context",
        "main_orch24_unified_tick_m15_path_follow",
        "main_orch24_unified_tick_m15_path_inverse_avoid",
        "main_orch24_unified_m1_spread_fill_target_follow",
        "main_orch24_unified_m1_spread_fill_stop_or_nofill_avoid",
        "main_orch24_unified_m1_fill_ordering_source_repair",
        "main_orch24_unified_m1_entry_materialized_context",
        "main_orch24_unified_branch_proxy_follow",
        "main_orch24_unified_branch_proxy_avoid",
        "main_orch24_unified_branch_proxy_source_repair",
        "main_orch24_unified_ready8_source_capture_repair_replay",
        "main_orch24_unified_split_summary_replay_attribution",
        "main_orch24_standalone_fvg_negative_guard",
        "scid_neutral_target_candidate_context",
        "scid_neutral_target_control_context",
        "scid_target_control_card_rank_non_discriminative",
        "scid_target_horizon_fail_closed_source_repair",
        "scid_target_horizon_neutral_only",
        "scid_target_horizon_source_field_requirement",
        "static_limit_adaptive_entry_challenger",
        "static_limit_adaptive_entry_source_requirement",
        "broker_actual_r_slippage_source_repair",
        "trade_record_execution_source_repair",
        "orderflow_pending_lifecycle_source_gap",
        "execution_source_capture_contract_context",
        "execution_replay_source_contract_context",
    ):
        assert source_component in block["post_l2_route_source_components"]
    assert "sierra_depth_source_gap" in block["post_l2_route_source_components"]
    assert "sierra_depth_window_sample_block" in block["post_l2_route_source_components"]
    assert "sierra_depth_in_window_clear_repair" in block["post_l2_route_source_components"]
    assert "sierra_depth_live_feature_status" in block["post_l2_route_source_components"]
    assert "sierra_depth_source_acquisition" in block["post_l2_route_source_components"]
    assert "risk_source_cost_cap" in block["post_l2_route_source_components"]
    assert "risk_cost_fill_proxy" in block["post_l2_route_source_components"]
    assert "risk_rstyle_proxy_outcome" in block["post_l2_route_source_components"]
    assert "risk_source_stress_acquisition" in block["post_l2_route_source_components"]
    assert "risk_stress_robustness" in block["post_l2_route_source_components"]
    assert "risk_sizing_policy" in block["post_l2_route_source_components"]
    assert "risk_ai_cost_control" in block["post_l2_route_source_components"]
    assert "risk_proxy_gap_status" in block["post_l2_route_source_components"]
    assert "risk_touch_count_proxy" in block["post_l2_route_source_components"]
    assert "risk_proxy_stress_cost_context" in block["post_l2_route_source_components"]
    for source_component in (
        "gate_touch_count",
        "gate_touch_count_gate",
        "gate_sl_beyond_ob",
        "gate_sl_beyond_ob_l2",
        "gate_pre_ai_poi_availability",
        "gate_pre_ai_h1_poi_availability",
        "gate_cross_instrument_correlation",
        "gate_cross_instrument_correlation_gate",
        "confidence_filter_quarantine",
        "fvg_ob_framework_repair",
        "l2_entry_in_ob_rejection_value",
        "l2_h1_poi_rejection_value",
        "l2_m15_choch_rejection_value",
        "l2_sl_beyond_ob_rejection_value",
        "rejected_candidate_blocked_limit_value",
        "rejected_candidate_c1_failed_value",
        "rejected_candidate_c2_m15_opposing_value",
        "rejected_candidate_c3_direction_mismatch_value",
        "rejected_candidate_no_qualifying_h1_poi_value",
        "rejected_candidate_no_reason_logged_value",
        "rejected_candidate_ob_proximity_value",
        "rejected_candidate_other_unknown_value",
        "rejected_candidate_parse_error_value",
        "rejected_candidate_prescreen_no_direction_value",
        "ltf_selector_repair",
        "kill_scope_preservation",
        "framework_gate_selector",
        "selector_shadow_source_guard",
        "session_timeframe_selector",
    ):
        assert source_component in block["post_l2_route_source_components"]
    assert block["conflict_resolution"] == "evidence_weighted"
    assert block["conflict_pressure_dominance_ratio"] == 1.25
    assert block["conflict_cost_adjusted_r_weight"] == 1.0
    assert block["conflict_stress_r_weight"] == 0.25
    assert block["conflict_proxy_score_weight"] == 1.0
    assert block["positive_follow_pressure_guard_enabled"] is True
    assert block["positive_follow_pressure_guard_min_effective_n"] == 100
    assert block["positive_follow_pressure_guard_min_abs_pressure"] == 1.0
    assert block["positive_follow_pressure_guard_dominance_ratio"] == 1.25
    assert block["positive_follow_pressure_bypasses_avoid_veto"] is True
    assert block["positive_follow_pressure_bypasses_target_stop_geometry"] is True
    assert block["positive_follow_pressure_bypasses_negative_proxy_class"] is True
    assert block["positive_follow_pressure_bypasses_source_repair"] is True
    assert block["source_guarded_positive_proxy_enabled"] is True
    assert block["source_guarded_positive_proxy_min_rows"] == 20
    assert block["source_guarded_positive_proxy_min_guard_rows"] == 1
    assert block["source_guarded_positive_proxy_dominance_ratio"] == 2.0
    assert block["source_guarded_positive_proxy_source_roles"] == [
        "scorer_registry_surface",
        "branch_local_default_off_candidate",
        "scope_system_decision",
    ]
    assert block["source_guarded_positive_proxy_source_groups"] == [
        "scorer_registry_surface"
    ]
    assert block["source_guarded_positive_proxy_system_surfaces"] == [
        "default_off_research_scorer_registry_catalog",
        "numeric_router_default_off_scope_decision_catalog",
        "scorer_registry_surface",
        "src/research_infra/moonshot_expanded_market_reduced_surface_execution.py",
    ]
    assert block["source_guarded_positive_proxy_bypasses_target_stop_geometry"] is True
    assert block["source_guarded_positive_proxy_bypasses_source_repair"] is True
    assert block["risk_adjustment_enabled"] is True
    assert block["risk_zero_blocks_execution"] is True
    assert block["risk_zero_bypass_effective_n_reasons"] == [
        "vnext_risk_route_family_avoid_veto",
        "vnext_risk_source_component_avoid_veto",
        "vnext_risk_source_component_summary_adverse_prior",
        "vnext_risk_action_class_avoid_veto",
        "vnext_risk_evidence_family_avoid_veto",
        "vnext_risk_source_name_avoid_veto",
        "vnext_risk_source_role_avoid_veto",
        "vnext_risk_recommendation_bucket_repair_prior",
        "vnext_risk_recommendation_family_rollup_adverse_prior",
        "vnext_risk_recommendation_unified_candidate_adverse_prior",
        "vnext_risk_recommendation_scope_rollup_adverse_prior",
        "vnext_risk_target_stop_not_source_bound",
        "vnext_risk_stop_first_proxy",
        "vnext_risk_proxy_stress_cost_repair",
        "vnext_risk_source_acquisition_required",
        "vnext_risk_source_repair_required",
        "vnext_risk_strong_negative_proxy_class",
    ]
    assert block["execution_block_min_risk_multiplier"] == 0.000001
    assert block["strong_follow_risk_multiplier"] == 1.25
    assert block["mixed_risk_multiplier"] == 0.5
    assert block["avoid_risk_multiplier"] == 0.0
    assert block["target_stop_not_source_bound_risk_adjustment_enabled"] is True
    assert block["target_stop_not_source_bound_risk_min_rows"] == 1
    assert block["target_stop_not_source_bound_risk_multiplier"] == 0.0
    assert block["stop_first_risk_adjustment_enabled"] is True
    assert block["stop_first_risk_min_rows"] == 1
    assert block["stop_first_risk_multiplier"] == 0.0
    assert block["target_stop_ambiguous_risk_adjustment_enabled"] is True
    assert block["target_stop_ambiguous_risk_min_rows"] == 1
    assert block["target_stop_ambiguous_negative_proxy_dominance_ratio"] == 1.0
    assert block["target_stop_ambiguous_risk_multiplier"] == 0.5
    assert block["source_repair_risk_adjustment_enabled"] is True
    assert block["source_repair_risk_min_rows"] == 1
    assert block["source_repair_risk_multiplier"] == 0.0
    assert block["source_acquisition_risk_adjustment_enabled"] is True
    assert block["source_acquisition_risk_min_rows"] == 1
    assert block["source_acquisition_risk_multiplier"] == 0.0
    assert block["risk_proxy_stress_cost_repair_adjustment_enabled"] is True
    assert block["risk_proxy_stress_cost_repair_min_rows"] == 1
    assert block["risk_proxy_stress_cost_repair_multiplier"] == 0.0
    assert block["recommendation_bucket_prior_enabled"] is True
    assert block["recommendation_bucket_prior_evidence_families"] == [
        "moonshot_recommendation_merge_bucket"
    ]
    assert block["recommendation_bucket_prior_bucket_families"] == [
        "source_component",
        "source_component_decision_group",
    ]
    assert block["recommendation_bucket_prior_min_bucket_rows"] == 20
    assert block["recommendation_bucket_prior_risk_enabled"] is True
    assert block["recommendation_bucket_prior_risk_min_rows"] == 20
    assert block["recommendation_bucket_prior_repair_groups"] == [
        "SOURCE_OR_CONTROL_REPAIR"
    ]
    assert block["recommendation_bucket_prior_supportive_groups"] == [
        "IMPLEMENT",
        "SCORE_WITH_CONTROL",
    ]
    assert block["recommendation_bucket_prior_repair_dominance_ratio"] == 1.0
    assert block["recommendation_bucket_prior_risk_multiplier"] == 0.0
    assert block["positive_follow_pressure_bypasses_recommendation_bucket_repair"] is False
    assert block["recommendation_family_rollup_prior_enabled"] is True
    assert block["recommendation_family_rollup_prior_evidence_families"] == [
        "moonshot_recommendation_family_rollup"
    ]
    assert block["recommendation_family_rollup_prior_rollup_types"] == [
        "source_component_decision_group"
    ]
    assert block["recommendation_family_rollup_prior_min_rows"] == 20
    assert block["recommendation_family_rollup_prior_risk_enabled"] is True
    assert block["recommendation_family_rollup_prior_risk_min_rows"] == 20
    assert block["recommendation_family_rollup_prior_adverse_groups"] == [
        "SOURCE_OR_CONTROL_REPAIR",
        "REDESIGN",
        "GUARD",
    ]
    assert block["recommendation_family_rollup_prior_supportive_groups"] == [
        "IMPLEMENT",
        "SCORE_WITH_CONTROL",
    ]
    assert block["recommendation_family_rollup_prior_adverse_dominance_ratio"] == 1.0
    assert block["recommendation_family_rollup_prior_risk_multiplier"] == 0.0
    assert block[
        "positive_follow_pressure_bypasses_recommendation_family_rollup_adverse"
    ] is False
    assert block["recommendation_unified_candidate_prior_enabled"] is True
    assert block["recommendation_unified_candidate_prior_evidence_families"] == [
        "moonshot_recommendation_unified_candidate"
    ]
    assert block["recommendation_unified_candidate_prior_match_fields"] == [
        "symbol",
        "route_session",
        "horizon_id",
        "primitive",
    ]
    assert block["recommendation_unified_candidate_prior_min_rows"] == 20
    assert block["recommendation_unified_candidate_prior_risk_enabled"] is True
    assert block["recommendation_unified_candidate_prior_risk_min_rows"] == 20
    assert block["recommendation_unified_candidate_prior_adverse_groups"] == [
        "SOURCE_OR_CONTROL_REPAIR",
        "REDESIGN",
        "GUARD",
    ]
    assert block["recommendation_unified_candidate_prior_supportive_groups"] == [
        "IMPLEMENT",
        "SCORE_WITH_CONTROL",
    ]
    assert block["recommendation_unified_candidate_prior_adverse_dominance_ratio"] == 1.0
    assert block["recommendation_unified_candidate_prior_risk_multiplier"] == 0.0
    assert block[
        "positive_follow_pressure_bypasses_recommendation_unified_candidate_adverse"
    ] is False
    assert block["recommendation_scope_rollup_prior_enabled"] is True
    assert block["recommendation_scope_rollup_prior_evidence_families"] == [
        "moonshot_recommendation_scope_rollup"
    ]
    assert block["recommendation_scope_rollup_prior_rollup_types"] == [
        "scope_component"
    ]
    assert block["recommendation_scope_rollup_prior_match_fields"] == [
        "symbol",
        "route_session",
        "horizon_id",
        "primitive",
    ]
    assert block["recommendation_scope_rollup_prior_min_rows"] == 20
    assert block["recommendation_scope_rollup_prior_risk_enabled"] is True
    assert block["recommendation_scope_rollup_prior_risk_min_rows"] == 20
    assert block["recommendation_scope_rollup_prior_adverse_groups"] == [
        "SOURCE_OR_CONTROL_REPAIR",
        "REDESIGN",
        "GUARD",
    ]
    assert block["recommendation_scope_rollup_prior_supportive_groups"] == [
        "IMPLEMENT",
        "SCORE_WITH_CONTROL",
    ]
    assert block["recommendation_scope_rollup_prior_adverse_dominance_ratio"] == 1.0
    assert block["recommendation_scope_rollup_prior_risk_multiplier"] == 0.0
    assert block[
        "positive_follow_pressure_bypasses_recommendation_scope_rollup_adverse"
    ] is False
    assert block["route_event_excluded_evidence_families"] == [
        "moonshot_source_component_summary",
        "moonshot_recommendation_merge_bucket",
        "moonshot_recommendation_family_rollup",
        "moonshot_recommendation_unified_candidate",
        "moonshot_recommendation_scope_rollup",
    ]
    assert block["context_guard_risk_adjustment_enabled"] is True
    assert block["context_guard_risk_min_rows"] == 1
    assert block["context_guard_risk_multiplier"] == 0.5
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_AMBIGUITY_COLLAPSE_ACTION_LEDGER_2026-05-16.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ENTRY_ADVERSE_REDESIGN_DETAIL_ADVERSE_VARIANT_DETAIL_LEDGER_2026-05-16.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_BROKER_SOURCE_REPAIR_EXPECTANCY_REPAIR_RESULT_LEDGER_2026-05-17.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_NUMERIC_RESULT_TABLES_SOURCE_COMPONENT_SUMMARY_LEDGER_2026-05-17.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_NUMERIC_RESULT_TABLES_SOURCE_GEOMETRY_REPAIR_LEDGER_2026-05-17.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_RECOMMENDATION_MERGE_BUNDLE_BUCKET_LEDGER_2026-05-17.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_RECOMMENDATION_MERGE_BUNDLE_FAMILY_ROLLUP_LEDGER_2026-05-17.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_RECOMMENDATION_MERGE_BUNDLE_UNIFIED_CANDIDATE_LEDGER_2026-05-17.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_RECOMMENDATION_MERGE_BUNDLE_SCOPE_ROLLUP_LEDGER_2026-05-17.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_CHALLENGER_FRONTIER_ACTION_LEDGER_2026-05-16.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_CHALLENGER_FRONTIER_ROUTE_LEDGER_2026-05-16.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_MAIN_ORCH24_TICK_STRUCTURAL_ENTRY_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_MAIN_ORCH24_STRUCTURAL_REPAIR_ACTION_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_MAIN_ORCH24_ACTION_COMPLETENESS_RESIDUAL_R_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_MAIN_ORCH24_IMPLEMENTATION_SELECTION_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_MAIN_ORCH24_SNAPSHOT_DEPENDENCY_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_MAIN_ORCH24_UNIFIED_CANDIDATE_PATH_PROXY_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_MAIN_ORCH48_FINAL_REVIEW_SELECTOR_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_LTF_PATH_GEOMETRY_SOURCE_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_INSTRUMENT_EXPANSION_MARKET_SESSION_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_MAIN_ORCH24_SOURCE_ACCEPTED_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_MAIN_ORCH24_SWING_PROTECTED_SOURCE_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_MAIN_ORCH24_SOURCE_M15_BRANCH_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_MAIN_ORCH24_LIVE_MECHANICAL_GEOMETRY_OUTCOME_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_MAIN_ORCH24_UNIFIED_CANDIDATE_PATH_PROXY_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_SCID_NOAPI_SOURCE_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_LIFECYCLE_EXECUTION_SOURCE_GUARD_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert block["route_family_avoid_veto_enabled"] is True
    assert block["route_family_avoid_veto_families"] == ["numeric_router", "nofill_mechanical"]
    assert block["route_family_avoid_veto_min_rows"] == 1
    assert block["route_family_avoid_veto_dominance_ratio"] == 1.0
    assert block["route_family_avoid_veto_risk_multiplier"] == 0.0
    assert block["source_component_avoid_veto_enabled"] is True
    assert block["source_component_avoid_veto_components"] == [
        "market_gap_code",
        "nofill_far_miss_avoid",
        "nofill_far_miss_source_confidence",
        "nofill_near_miss_offset",
        "entry_adverse_stop_first",
        "adverse_stop_first_execution",
        "entry_adverse_execution",
        "gbpjpy_long_adverse_avoid_reclass",
        "gtos_branch_followup_branch",
        "gtos_branch_followup_family",
        "gtos_branch_followup_m15",
        "gtos_branch_followup_source",
        "gtos_branch_ambiguity_branch",
        "gtos_branch_ambiguity_cause_matrix",
        "gtos_branch_ambiguity_m15_same_bar",
        "gtos_branch_ambiguity_ordering",
        "branch_replay_execution_negative_or_redesign",
        "unified_candidate_action_branch_avoid_filter",
        "unified_candidate_action_market_gap_avoid_inverse",
        "unified_candidate_scoring_avoid_inverse_execution",
        "unified_execution_decision_avoid_redirect",
        "unified_execution_decision_fillability_retest_redesign",
        "unified_execution_decision_market_gap_avoid_inverse",
        "unified_execution_decision_provenance_guard",
        "unified_execution_decision_source_expansion_guard",
        "unified_candidate_variant_avoid_inverse",
        "unified_shadow_scorer_branch_failure_avoid_filter",
        "unified_shadow_scorer_avoid_filter",
        "unified_shadow_scorer_market_gap_avoid_filter",
        "tick_m15_execution_friction_spread_competes",
        "main_orch24_tick_structural_kill_guard",
        "main_orch24_tick_negative_proxy_guard",
        "main_orch24_entry_offset_025r_kill_guard",
        "main_orch24_structural_fvg_ob_single_family_kill_guard",
        "main_orch24_structural_standalone_fvg_kill_guard",
        "main_orch24_structural_swing_unprotected_kill_guard",
        "main_orch24_structural_duplicate_redesign_guard",
        "main_orch24_structural_ltf_adverse_redesign_guard",
        "main_orch24_structural_prefill_redesign_guard",
        "main_orch24_structural_gbpjpy_long_adverse_redesign_guard",
        "main_orch24_structural_repair_redesign_guard",
        "main_orch24_structural_repair_kill_guard",
        "main_orch24_action_completeness_fvg_ob_kill_guard",
        "main_orch24_action_completeness_nofill_far_miss_kill_guard",
        "main_orch24_action_completeness_swing_unprotected_kill_guard",
        "main_orch24_action_completeness_kill_guard",
        "main_orch24_action_completeness_redesign_guard",
        "main_orch24_action_completeness_pending_redesign_guard",
        "main_orch24_action_completeness_entry_offset_redesign_guard",
        "main_orch24_action_completeness_source_provenance_redesign_guard",
        "main_orch24_residual_numeric_r_redesign_guard",
        "main_orch24_residual_numeric_r_adverse_avoid_guard",
        "main_orch24_residual_numeric_r_distance_context",
        "main_orch24_swing_protected_unprotected_stop_guard",
        "main_orch24_swing_protected_negative_proxy_guard",
        "main_orch24_source_m15_kill_or_no_fill_guard",
        "main_orch24_source_m15_redesign_guard",
        "main_orch24_live_mechanical_stop_or_nofill_avoid",
        "main_orch24_live_mechanical_kill_guard",
        "main_orch24_live_mechanical_redesign_guard",
        "main_orch24_unified_tick_m15_path_inverse_avoid",
        "main_orch24_unified_m1_spread_fill_stop_or_nofill_avoid",
        "main_orch24_unified_branch_proxy_avoid",
        "tick_source_recovery_quote_tick_nofill_avoid",
        "tick_source_recovery_stop_first_avoid",
        "legacy_live_shadow_k54_k55_same_cohort_kill",
        "legacy_live_shadow_partial_close_expansion_avoid",
        "legacy_live_shadow_portfolio_vol_sizing_avoid",
        "main_orch24_standalone_fvg_negative_guard",
        "ai_hallucination_guard",
        "legacy_v4_lira_guard",
        "legacy_t7_negative_simulation",
        "shadow_source_guard",
        "observable_execution_avoid_filter",
        "gate_touch_count",
        "gate_touch_count_gate",
        "gate_sl_beyond_ob",
        "gate_sl_beyond_ob_l2",
        "gate_pre_ai_poi_availability",
        "gate_pre_ai_h1_poi_availability",
        "gate_cross_instrument_correlation",
        "gate_cross_instrument_correlation_gate",
        "confidence_filter_quarantine",
        "fvg_ob_framework_repair",
        "l2_entry_in_ob_rejection_value",
        "l2_h1_poi_rejection_value",
        "l2_m15_choch_rejection_value",
        "l2_sl_beyond_ob_rejection_value",
        "rejected_candidate_blocked_limit_value",
        "rejected_candidate_c1_failed_value",
        "rejected_candidate_c2_m15_opposing_value",
        "rejected_candidate_c3_direction_mismatch_value",
        "rejected_candidate_no_qualifying_h1_poi_value",
        "rejected_candidate_no_reason_logged_value",
        "rejected_candidate_ob_proximity_value",
        "rejected_candidate_other_unknown_value",
        "rejected_candidate_parse_error_value",
        "rejected_candidate_prescreen_no_direction_value",
        "accepted_candidate_distribution_result_pressure",
        "accepted_candidate_feature_ranking_pressure",
        "accepted_candidate_feature_stratification_pressure",
        "ltf_selector_repair",
        "ltf_path_source_blocked_guard",
        "g3_geometry_source_repair_guard",
        "g3_geometry_stop_first_avoid",
        "instrument_expansion_route_avoid",
        "instrument_expansion_h1_h2_decay_guard",
        "instrument_expansion_microstructure_cost_guard",
        "instrument_expansion_tier2_slice_avoid",
        "instrument_expansion_tier2_source_repair_guard",
        "instrument_expansion_gbpusd_observer_avoid",
        "kill_scope_preservation",
    ]
    assert block["source_component_avoid_veto_min_rows"] == 1
    assert block["source_component_avoid_veto_dominance_ratio"] == 1.0
    assert block["source_component_avoid_veto_risk_multiplier"] == 0.0
    assert block["source_component_summary_prior_enabled"] is True
    assert block["source_component_summary_prior_evidence_families"] == [
        "moonshot_source_component_summary"
    ]
    assert block["source_component_summary_prior_min_rollup_rows"] == 20
    assert block["source_component_summary_prior_risk_enabled"] is True
    assert block["source_component_summary_prior_risk_min_rollup_rows"] == 20
    assert block["source_component_summary_prior_adverse_proxy_mean_max"] == -0.05
    assert block["source_component_summary_prior_risk_multiplier"] == 0.0
    assert block["action_class_avoid_veto_enabled"] is True
    assert block["action_class_avoid_veto_classes"] == [
        "avoid_filter",
        "inverse_filter",
        "failure_filter",
        "repaired_proxy_avoid_filter",
        "unified_candidate_avoid_filter",
        "expanded_market_source_geometry_avoid_filter",
        "nofill_lifecycle_avoid_filter",
        "gate_filter_selector_avoid_filter",
        "gate_selector_avoid_filter",
        "confidence_quarantine_filter",
        "framework_gate_repair_filter",
        "adverse_stop_first_avoid_filter",
        "entry_adverse_avoid_filter",
        "gbpjpy_long_adverse_avoid_filter",
        "branch_ambiguity_stop_first_avoid_filter",
        "branch_impl_replay_avoid_filter",
        "cp280_scorer_filter_router_avoid_filter",
        "numeric_router_default_off_avoid_filter",
        "survivor_failure_avoid_filter",
        "observable_execution_avoid_filter",
        "unified_execution_action_work_order_avoid_filter",
        "target_stop_ordering_stop_first_avoid_filter",
        "branch_replay_execution_negative_avoid_filter",
        "unified_candidate_action_execution_avoid_filter",
        "unified_candidate_scoring_avoid_inverse_filter",
        "unified_execution_decision_avoid_redirect_filter",
        "unified_execution_decision_fillability_retest_avoid_filter",
        "unified_execution_decision_market_gap_avoid_inverse_filter",
        "unified_execution_decision_provenance_avoid_filter",
        "unified_execution_decision_source_expansion_avoid_filter",
        "unified_candidate_variant_avoid_inverse_filter",
        "unified_shadow_scorer_branch_failure_avoid_filter",
        "unified_shadow_scorer_avoid_filter",
        "unified_shadow_scorer_market_gap_avoid_filter",
        "tick_m15_execution_friction_spread_avoid_filter",
        "tick_m15_target_control_negative_alignment_avoid_filter",
        "live_mechanical_stop_first_avoid_filter",
        "live_mechanical_nofill_avoid_filter",
        "live_mechanical_kill_avoid_filter",
        "live_mechanical_redesign_avoid_filter",
        "pre_ai_post_l2_ai_route_failure_filter",
        "legacy_v4_lira_avoid_filter",
        "legacy_t7_simulation_avoid_filter",
        "legacy_v2_v3_paper_live_avoid_filter",
        "sl_beyond_ob_gate_support_avoid_filter",
        "fvg_trade_record_bounds_avoid_filter",
        "scid_target_control_card_rank_avoid_filter",
    ]
    assert block["action_class_avoid_veto_min_rows"] == 1
    assert block["action_class_avoid_veto_dominance_ratio"] == 1.0
    assert block["action_class_avoid_veto_risk_multiplier"] == 0.0
    assert block["evidence_family_avoid_veto_enabled"] is True
    assert block["evidence_family_avoid_veto_families"] == [
        "numeric_router_system_recommendations",
        "gate_filter_selector_evidence",
        "gtos_vnext_gate_selector_session_timeframe",
        "gtos_vnext_adverse_stop_first_execution",
        "gtos_vnext_branch_followup_computation",
        "gtos_vnext_branch_ambiguity_collapse",
        "gtos_vnext_branch_implementation_replay",
        "gtos_vnext_cp280_scorer_filter_router",
        "gtos_vnext_numeric_router_catalog_runtime",
        "gtos_vnext_survivor_failure_runtime",
        "gtos_vnext_observable_execution",
        "gtos_vnext_unified_execution_action_work_order",
        "gtos_vnext_target_stop_ordering_execution_scoring",
        "gtos_vnext_branch_replay_execution_repair",
        "gtos_vnext_unified_candidate_action_execution",
        "gtos_vnext_unified_candidate_scoring_execution",
        "gtos_vnext_unified_execution_decision",
        "gtos_vnext_unified_shadow_source_materialization",
        "gtos_vnext_tick_m15_execution_friction",
        "gtos_vnext_tick_m15_target_control",
        "gtos_vnext_scid_target_horizon_control",
        "gtos_vnext_rejected_candidate_l2_value_mining",
        "gtos_vnext_accepted_candidate_m1_fill_source_repair",
        "gtos_vnext_legacy_t7_simulation_friction",
        "gtos_vnext_legacy_v2_v3_paper_live_friction",
    ]
    assert block["evidence_family_avoid_veto_min_rows"] == 1
    assert block["evidence_family_avoid_veto_dominance_ratio"] == 1.0
    assert block["evidence_family_avoid_veto_risk_multiplier"] == 0.0
    assert block["source_name_avoid_veto_enabled"] is True
    assert block["source_name_avoid_veto_names"] == [
        "numeric_router_avoid_score",
        "gate_filter_selector_runtime_mapping",
        "gtos_vnext_gate_selector_session_timeframe_wave",
        "gtos_vnext_adverse_stop_first_execution_wave",
        "gtos_vnext_branch_followup_computation_wave",
        "gtos_vnext_branch_ambiguity_collapse_wave",
        "gtos_vnext_branch_implementation_replay_wave",
        "gtos_vnext_cp280_scorer_filter_router_wave",
        "gtos_vnext_observable_execution_wave",
        "gtos_vnext_unified_execution_action_work_order_wave",
        "gtos_vnext_target_stop_ordering_execution_scoring_wave",
        "gtos_vnext_branch_replay_execution_repair_wave",
        "gtos_vnext_unified_candidate_action_execution_wave",
        "gtos_vnext_unified_candidate_scoring_execution_wave",
        "gtos_vnext_unified_execution_decision_wave",
        "gtos_vnext_unified_shadow_source_materialization_wave",
        "gtos_vnext_legacy_t7_simulation_friction_wave",
        "gtos_vnext_legacy_v2_v3_paper_live_friction_wave",
        "gtos_vnext_rejected_candidate_l2_value_mining_wave",
        "gtos_vnext_accepted_candidate_m1_fill_source_repair_wave",
    ]
    assert block["source_name_avoid_veto_min_rows"] == 1
    assert block["source_name_avoid_veto_dominance_ratio"] == 1.0
    assert block["source_name_avoid_veto_risk_multiplier"] == 0.0
    assert block["source_role_avoid_veto_enabled"] is True
    assert block["source_role_avoid_veto_roles"] == [
        "historical_replay_result_table",
        "default_off_branch_decision",
        "gate_selector_avoid_guard",
        "confidence_filter_shadow_guard",
        "legacy_ai_hallucination_avoid_guard",
        "legacy_v4_lira_avoid_guard",
        "adverse_stop_first_avoid_guard",
        "gbpjpy_long_adverse_avoid_guard",
        "branch_followup_avoid_guard",
        "branch_ambiguity_stop_first_avoid_guard",
        "branch_impl_replay_avoid_guard",
        "cp280_scorer_filter_router_avoid_guard",
        "observable_execution_avoid_guard",
        "unified_execution_avoid_guard",
        "target_stop_ordering_stop_first_avoid_guard",
        "branch_replay_execution_negative_proxy",
        "unified_candidate_action_avoid_guard",
        "unified_candidate_scoring_avoid_inverse_guard",
        "unified_execution_decision_avoid_redirect_guard",
        "unified_execution_decision_fillability_retest_avoid_guard",
        "unified_execution_decision_market_gap_avoid_inverse_guard",
        "unified_execution_decision_provenance_avoid_guard",
        "unified_execution_decision_source_expansion_avoid_guard",
        "unified_candidate_variant_avoid_inverse_guard",
        "unified_shadow_scorer_avoid_guard",
        "rejected_candidate_l2_value_avoid_filter",
        "exact_r_bridge_kill_branch_avoid_kill_avoid_filter",
        "fill_sim_stop_first_avoid_avoid_filter",
        "legacy_t7_simulation_avoid_guard",
        "legacy_v2_v3_paper_live_avoid_guard",
        "sl_beyond_ob_rejected_l2_gate_support_guard",
        "fvg_trade_record_bounds_kill_guard",
        "fvg_trade_record_bounds_negative_proxy_guard",
        "fvg_trade_record_bounds_redesign_negative_guard",
        "scid_target_control_card_rank_avoid_guard",
    ]
    assert block["source_role_avoid_veto_min_rows"] == 1
    assert block["source_role_avoid_veto_dominance_ratio"] == 1.0
    assert block["source_role_avoid_veto_risk_multiplier"] == 0.0
    assert block["strong_negative_proxy_risk_adjustment_enabled"] is True
    assert block["strong_negative_proxy_risk_min_rows"] == 20
    assert block["strong_negative_proxy_risk_dominance_ratio"] == 2.0
    assert block["strong_negative_proxy_risk_multiplier"] == 0.0
    assert block["strong_positive_proxy_risk_adjustment_enabled"] is True
    assert block["strong_positive_proxy_risk_min_rows"] == 20
    assert block["strong_positive_proxy_risk_dominance_ratio"] == 2.0
    assert block["strong_positive_proxy_risk_multiplier"] == 1.25
    assert block["confidence_override_enabled"] is True
    assert block["confidence_override_risk_reasons"] == [
        "vnext_risk_strong_follow",
        "vnext_risk_strong_positive_proxy_class",
    ]
    assert block["pending_policy_enabled"] is True
    assert block["pending_policy_min_component_rows"] == 1
    assert block["pending_policy_market_entry_enabled"] is True
    assert block["pending_policy_market_entry_min_component_rows"] == 1
    assert block["pending_policy_static_limit_adaptive_entry_enabled"] is True
    assert block["pending_policy_static_limit_adaptive_entry_min_component_rows"] == 1
    assert block["pending_policy_offset_avoid_enabled"] is True
    assert block["pending_policy_offset_min_component_rows"] == 1
    assert block["pending_policy_market_entry_blocks_on_source_requirement"] is True
    assert block["pending_policy_source_requirement_min_component_rows"] == 1
    assert block["pending_policy_market_entry_requires_follow"] is True
    assert block["pending_policy_market_entry_requires_positive_proxy"] is True
    assert block["pending_policy_market_entry_positive_proxy_dominance_ratio"] == 1.0
    assert block["pending_policy_offset_avoid_requires_component_avoid"] is True
    assert block["pending_policy_offset_avoid_requires_negative_proxy"] is True
    assert block["pending_policy_offset_avoid_negative_proxy_dominance_ratio"] == 1.0
    assert block["pending_policy_use_source_component_decisions"] is True
    assert block["pending_policy_nofill_avoid_requires_component_avoid"] is True
    assert block["pending_policy_market_entry_requires_component_follow"] is True
    assert block["pending_policy_source_requirement_requires_mixed"] is True
    assert block["pending_policy_component_decision_dominance_ratio"] == 1.0
    assert block["block_min_effective_n"] == 3
    assert block["avoid_blocks_execution"] is False
    assert block["decision_log_path"] == "shadow_logs/gtos_vnext_runtime_decisions.jsonl"
    assert block["evidence_row_detail_limit"] == 250
    assert block["evidence_id_list_limit"] == 2000
    assert block["min_loaded_evidence_rows"] == 50000
    assert block["scope_selection_policy"] == "all_matching_anchored"
    assert block["scope_required_anchor_groups"] == [
        ["symbol", "source_symbol", "symbol_family", "market"],
        ["route_session"],
        ["side"],
    ]
    assert block["scope_side_anchor_optional_evidence_families"] == [
        "moonshot_unified_numeric_result",
        "moonshot_exact_r_missing_proof",
        "moonshot_source_geometry_repair",
        "moonshot_control_screen",
        "moonshot_control_screen_route_queue",
        "moonshot_unified_candidate_market_rollup",
        "gtos_vnext_nofill_pending_lifecycle",
        "gtos_vnext_source_repair_missing_denominator",
        "gtos_vnext_numeric_router_catalog_runtime",
        "gtos_vnext_survivor_failure_runtime",
        "gtos_vnext_nr_source_repair_execution_identity",
        "gtos_vnext_ai_narrowing_default_off_runtime",
        "gtos_vnext_ai_decision_trace_routing_guard",
        "gtos_vnext_pre_ai_post_l2_routing_policy",
        "gtos_vnext_legacy_ai_cascade_model_runtime",
        "gtos_vnext_legacy_t7_simulation_friction",
        "gtos_vnext_legacy_v2_v3_paper_live_friction",
        "gtos_vnext_sl_beyond_ob_outcome_join_source_repair",
        "gtos_vnext_fvg_trade_record_bounds_execution_runtime",
        "gtos_vnext_exit_management_trailing_j46",
        "gtos_vnext_exit_management_residue",
        "gtos_vnext_q62_partial_close_exit_runtime",
        "gtos_vnext_ready8_failure_control_residue",
        "gtos_vnext_execution_adjacent_friction_residue",
        "gtos_vnext_lifecycle_execution_source_guard",
        "gtos_vnext_accepted_candidate_m1_fill_source_repair",
        "gtos_vnext_sierra_depth_source_acquisition",
        "gtos_vnext_risk_proxy_stress_cost",
        "gtos_vnext_gate_selector_session_timeframe",
        "gtos_vnext_adverse_stop_first_execution",
        "gtos_vnext_observable_execution",
        "gtos_vnext_unified_execution_action_work_order",
        "gtos_vnext_branch_replay_execution_repair",
        "gtos_vnext_unified_candidate_action_execution",
        "gtos_vnext_unified_candidate_scoring_execution",
        "gtos_vnext_unified_execution_decision",
        "gtos_vnext_unified_shadow_source_materialization",
        "gtos_vnext_scid_forward_source_capture",
        "gtos_vnext_scid_future_capture_source_state",
        "gtos_vnext_scid_combined_source_capture_poi_bounds",
        "gtos_vnext_scid_noapi_source_repair",
        "gtos_vnext_pre_ai_h1_poi_source_gap",
        "gtos_vnext_shadow_source_log_materialization",
        "gtos_vnext_tick_m15_execution_friction",
        "gtos_vnext_tick_m15_target_control",
        "gtos_vnext_main_orch24_tick_structural_entry_runtime",
        "gtos_vnext_main_orch24_structural_repair_action_runtime",
        "gtos_vnext_main_orch24_action_completeness_residual_r_runtime",
        "gtos_vnext_main_orch24_implementation_selection_runtime",
        "gtos_vnext_main_orch48_final_review_selector_runtime",
        "gtos_vnext_ltf_path_geometry_source_runtime",
        "gtos_vnext_instrument_expansion_market_session_runtime",
        "gtos_vnext_main_orch24_source_accepted_action_repair_runtime",
        "gtos_vnext_main_orch24_swing_protected_source_repair_runtime",
        "gtos_vnext_main_orch24_source_m15_branch_repair_runtime",
        "gtos_vnext_main_orch24_live_mechanical_geometry_outcome_runtime",
        "gtos_vnext_tick_source_recovery_quote_contract_runtime",
        "gtos_vnext_legacy_live_shadow_decision_runtime",
        "gtos_vnext_scid_target_horizon_control",
    ]
    assert block["scope_side_anchor_optional_source_components"] == [
        "nofill_far_miss_avoid",
        "nofill_far_miss_retest",
        "nofill_far_miss_family",
        "nofill_far_miss_source_confidence",
        "nofill_near_miss_market_entry",
        "nofill_near_miss_offset",
        "nofill_near_miss_source_requirement",
        "ohlc_control_screen",
        "ohlc_control_screen_route_queue",
        "unified_candidate_market_rollup",
        "unified_candidate_default_off_scorer",
        "unified_candidate_guard",
        "unified_candidate_source_repair",
        "source_repair_proof",
        "sl_beyond_ob_outcome_capture_gap",
        "sl_beyond_ob_pass_adverse_outcome_reference",
        "sl_beyond_ob_pass_nofill_outcome_reference",
        "sl_beyond_ob_pass_outcome_reference",
        "sl_beyond_ob_rejected_l2_counterfactual",
        "sl_beyond_ob_legacy_zero_buffer_source_repair",
        "entry_geometry_fillability_tick_path_ordering",
        "entry_geometry_fillability_tick_path_ordering_retest_control",
        "fvg_entry_geometry_and_lock_metadata",
        "fvg_ob_confluence_shared_path_scorer",
        "pending_lifecycle_fill_cancel_expiry_source_capture",
        "lifecycle_still_pending_no_fill_source_guard",
        "lifecycle_wrong_side_no_fill_source_guard",
        "trade_index_lifecycle_action_required_source_repair",
        "opportunity_lifecycle_reset_policy_source_guard",
        "prefill_delivery_adverse_reversal_path",
        "prefill_delivery_adverse_reversal_path_retest_control",
        "source_cost_spread_bar_proxy_implication",
        "structural_lock_reentry_cost_metadata",
        "structural_swing_protected_stop_geometry",
        "tick_derived_structural_source_repair",
        "market_gap_code",
        "shadow_source_guard",
        "default_off_application",
        "ai_architecture_audit",
        "ai_trace_integrity_guard",
        "ai_trace_provenance",
        "ai_trace_trade_record_backfill",
        "ai_shadow_readiness",
        "survivor_failure_proxy",
        "default_off_scorer_application",
        "registry_scorer_module",
        "registry_scorer_module_system",
        "sierra_scid_source_bound_m15_bar_replay",
        "sierra_depth_source_gap",
        "sierra_depth_window_sample_block",
        "sierra_depth_in_window_clear_repair",
        "sierra_depth_live_feature_status",
        "sierra_depth_source_acquisition",
        "risk_source_cost_cap",
        "risk_cost_fill_proxy",
        "risk_rstyle_proxy_outcome",
        "risk_source_stress_acquisition",
        "risk_stress_robustness",
        "risk_sizing_policy",
        "risk_ai_cost_control",
        "risk_proxy_gap_status",
        "risk_touch_count_proxy",
        "risk_proxy_stress_cost_context",
        "gate_touch_count",
        "gate_touch_count_gate",
        "gate_sl_beyond_ob",
        "gate_sl_beyond_ob_l2",
        "gate_pre_ai_poi_availability",
        "gate_pre_ai_h1_poi_availability",
        "gate_cross_instrument_correlation",
        "gate_cross_instrument_correlation_gate",
        "confidence_filter_quarantine",
        "fvg_ob_framework_repair",
        "ltf_selector_repair",
        "kill_scope_preservation",
        "ai_hallucination_guard",
        "legacy_v4_lira_guard",
        "ai_v3_cascade_preferred",
        "no_ai_shadow_observer",
        "ai_source_lineage_materialization_guard",
        "ai_routing_architecture_context",
        "ai_narrowing_policy_residue",
        "ai_limit_order_prompt_context",
        "legacy_ai_schema_parser_guard",
        "legacy_ai_model_context_guard",
        "legacy_ai_cascade_context_guard",
        "legacy_t7_positive_simulation",
        "legacy_t7_negative_simulation",
        "legacy_t7_context_simulation",
        "legacy_v2_v3_paper_live_follow_scorer",
        "legacy_v2_v3_paper_live_friction_guard",
        "legacy_v2_v3_paper_live_context_guard",
        "framework_gate_selector",
        "selector_shadow_source_guard",
        "session_timeframe_selector",
        "targetstop_na_binding_repair",
        "target_stop_path_control",
        "observable_execution_follow_scorer",
        "observable_execution_control_guard",
        "observable_execution_denominator_guard",
        "observable_execution_source_policy_guard",
        "observable_execution_source_repair",
        "observable_execution_horizon_repair",
        "observable_execution_avoid_filter",
        "trailing_stop_v1_shadow",
        "j46_j49_active_exit_policy",
        "j46_j49_actual_r_boundary",
        "exit_optimization_context",
        "exit_policy_legacy_batch_context",
        "exit_policy_h29_risk_context",
        "exit_partial_split_policy_guard",
        "exit_session_timestamp_source_requirement",
        "exit_no_event_status_observability",
        "q62_partial_close_scheme_result",
        "q62_variant_c_shadow_context",
        "q62_variant_d_shadow_queue_guard",
        "q62_common_trigger_runner_giveup_guard",
        "q62_partial_close_policy_guard",
        "ready8_control_only_quarantine",
        "ready8_card_rank_redundancy_kill",
        "ready8_source_control_repair_requirement",
        "ready8_denominator_overlap_requirement",
        "ready8_exact_geometry_source_requirement",
        "ready8_weak_overlap_shadow_only",
        "ready8_fail_closed_source_policy",
        "ready8_promotion_validation_block",
        "branch_replay_execution_blocker_repair_guard",
        "branch_replay_execution_source_ordering_guard",
        "branch_replay_execution_work_unit_context",
        "unified_candidate_action_market_gap_avoid_inverse",
        "unified_candidate_action_market_gap_entry_geometry",
        "unified_candidate_action_source_expansion",
        "unified_candidate_action_concentration_restress",
        "unified_candidate_action_symbol_session",
        "unified_candidate_scoring_avoid_inverse_execution",
        "unified_candidate_scoring_entry_geometry_execution",
        "unified_execution_decision_avoid_redirect",
        "unified_execution_decision_fillability_retest_redesign",
        "unified_execution_decision_market_entry_challenger",
        "unified_execution_decision_market_gap_avoid_inverse",
        "unified_execution_decision_market_gap_entry_geometry",
        "unified_execution_decision_provenance_guard",
        "unified_execution_decision_source_expansion_guard",
        "unified_candidate_variant_avoid_inverse",
        "unified_candidate_variant_entry_geometry",
        "unified_candidate_variant_source_expansion",
        "unified_shadow_scorer_branch_failure_avoid_filter",
        "unified_shadow_scorer_avoid_filter",
        "unified_shadow_scorer_market_gap_avoid_filter",
        "unified_shadow_scorer_entry_geometry",
        "unified_shadow_scorer_market_gap_entry_geometry",
        "unified_shadow_scorer_market_entry_comparator",
        "unified_shadow_scorer_branch_proxy_scorer",
        "unified_shadow_scorer_source_materialization",
        "unified_source_materialization_execution",
        "scid_forward_source_capture_lifecycle",
        "scid_future_capture_baseline_control",
        "scid_future_capture_framework_setup",
        "scid_future_capture_entry_reference",
        "scid_future_capture_side_direction",
        "scid_future_capture_stop_reference",
        "scid_future_capture_target_reference",
        "scid_future_capture_lifecycle_status",
        "scid_combined_framework_setup_source_gap",
        "scid_combined_orderflow_depth_source_gap",
        "scid_combined_entry_reference_source_gap",
        "scid_combined_side_direction_source_gap",
        "scid_combined_stop_reference_source_gap",
        "scid_combined_target_reference_source_gap",
        "scid_combined_lifecycle_source_gap",
        "scid_combined_ltf_path_source_gap",
        "scid_combined_poi_bounds_source_gap",
        "scid_noapi_forbidden_surface_guard",
        "scid_noapi_future_capture_source_acquisition",
        "scid_noapi_ltf_orderflow_source_acquisition",
        "scid_noapi_missing_source_acquisition",
        "scid_strategy_field_ltf_orderflow_source_acquisition",
        "scid_strategy_field_missing_source_acquisition",
        "scid_forward_readonly_alignment_source_acquisition",
        "pre_ai_h1_poi_bullish_source_gap",
        "pre_ai_h1_poi_bearish_source_gap",
        "shadow_action_required_source_gap",
        "shadow_candidate_poi_source_gap",
        "shadow_external_source_blocker",
        "shadow_framework_qualification_source_gap",
        "shadow_generic_source_materialization_gap",
        "shadow_join_status_source_gap",
        "shadow_missing_exact_required_fields",
        "shadow_path_contract_source_gap",
        "tick_m15_execution_friction_spread_competes",
        "tick_m15_execution_friction_movement_dominates",
        "tick_m15_execution_friction_weak_denominator",
        "tick_m15_target_control_negative_alignment",
        "tick_m15_target_control_placebo_ready_positive",
        "tick_m15_target_control_flat_or_negative_abs",
        "tick_m15_target_control_small_n_context",
        "main_orch24_tick_structural_kill_guard",
        "main_orch24_tick_redesign_source_repair",
        "main_orch24_tick_preserve_source_acquisition",
        "main_orch24_tick_negative_proxy_guard",
        "main_orch24_tick_positive_proxy_follow",
        "main_orch24_nas100_tick_order_repair_follow",
        "main_orch24_entry_offset_025r_kill_guard",
        "main_orch24_entry_offset_050r_challenger",
        "main_orch24_entry_offset_tick_source_acquisition",
        "main_orch24_structural_metadata_default_off_follow",
        "main_orch24_structural_ltf_positive_follow",
        "main_orch24_structural_pending_lifecycle_context",
        "main_orch24_structural_fvg_ob_shared_path_context",
        "main_orch24_structural_context",
        "main_orch24_structural_source_repair_requirement",
        "main_orch24_action_completeness_default_off_follow",
        "main_orch24_action_completeness_fvg_structural_follow",
        "main_orch24_action_completeness_entry_offset_follow",
        "main_orch24_action_completeness_source_provenance_follow",
        "main_orch24_action_completeness_keep_context",
        "main_orch24_action_completeness_context",
        "main_orch24_action_completeness_source_repair_requirement",
        "main_orch24_residual_numeric_r_materialized_context",
        "main_orch24_residual_numeric_r_context",
        "main_orch24_source_accepted_m15_ordering_follow",
        "main_orch24_source_accepted_source_cost_proxy_follow",
        "main_orch24_source_accepted_degraded_redesign_source_acquisition",
        "main_orch24_swing_protected_tick_repair_follow",
        "main_orch24_swing_protected_unprotected_stop_guard",
        "main_orch24_swing_protected_negative_proxy_guard",
        "main_orch24_swing_protected_source_acquisition",
        "main_orch24_swing_protected_neutral_context",
        "main_orch24_source_m15_ordering_positive_follow",
        "main_orch24_source_m15_kill_or_no_fill_guard",
        "main_orch24_source_m15_redesign_guard",
        "main_orch24_source_m15_source_acquisition",
        "main_orch24_source_m15_default_off_context",
        "main_orch24_source_m15_neutral_context",
        "main_orch24_live_mechanical_geometry_proxy_context",
        "main_orch24_live_mechanical_source_acquisition",
        "main_orch24_live_mechanical_ambiguous_path_guard",
        "main_orch24_live_mechanical_pending_lifecycle_guard",
        "main_orch24_live_mechanical_context",
        "main_orch24_unified_tick_m15_path_follow",
        "main_orch24_unified_tick_m15_path_inverse_avoid",
        "main_orch24_unified_m1_spread_fill_target_follow",
        "main_orch24_unified_m1_spread_fill_stop_or_nofill_avoid",
        "main_orch24_unified_m1_fill_ordering_source_repair",
        "main_orch24_unified_m1_entry_materialized_context",
        "main_orch24_unified_branch_proxy_follow",
        "main_orch24_unified_branch_proxy_avoid",
        "main_orch24_unified_branch_proxy_source_repair",
        "main_orch24_unified_ready8_source_capture_repair_replay",
        "main_orch24_unified_split_summary_replay_attribution",
        "tick_source_recovery_path_ready_context",
        "tick_source_recovery_ordered_path_source_acquisition",
        "tick_source_recovery_separate_fill_path_source_acquisition",
        "tick_source_recovery_opening_drive_source_acquisition",
        "tick_source_recovery_no_entry_touch_source_acquisition",
        "tick_source_recovery_no_terminal_pending_guard",
        "tick_source_recovery_geometry_join_context",
        "tick_source_recovery_source_hash_context",
        "tick_source_recovery_partial_coverage_source_acquisition",
        "legacy_live_shadow_v2_replay_context",
        "legacy_live_shadow_v2b_forward_source_acquisition",
        "legacy_live_shadow_fvg_ob_source_acquisition",
        "legacy_live_shadow_j46_j49_policy_follow",
        "legacy_live_shadow_s79_side_aware_context",
        "legacy_live_shadow_nofill_capture_source_acquisition",
        "legacy_live_shadow_sierra_orderflow_diagnostic_context",
        "legacy_live_shadow_strategy_replay_context",
        "legacy_live_shadow_trailing_stop_shadow_context",
        "legacy_live_shadow_xagusd_account_history_source_acquisition",
        "main_orch24_standalone_fvg_negative_guard",
        "scid_neutral_target_candidate_context",
        "scid_neutral_target_control_context",
        "scid_target_control_card_rank_non_discriminative",
        "scid_target_horizon_fail_closed_source_repair",
        "scid_target_horizon_neutral_only",
        "scid_target_horizon_source_field_requirement",
        "static_limit_adaptive_entry_challenger",
        "static_limit_adaptive_entry_source_requirement",
        "broker_actual_r_slippage_source_repair",
        "trade_record_execution_source_repair",
        "orderflow_pending_lifecycle_source_gap",
        "execution_source_capture_contract_context",
        "execution_replay_source_contract_context",
        "a4_fill_simulation_result_pressure",
        "accepted_candidate_classifier_validation_context",
        "accepted_candidate_distribution_result_pressure",
        "accepted_candidate_feature_ranking_pressure",
        "accepted_candidate_feature_stratification_pressure",
        "accepted_candidate_h1_h2_feature_stability_context",
        "accepted_candidate_m1_fill_support_code_context",
        "accepted_candidate_touch_bucket_result_pressure",
        "accepted_filled_candidate_result_pressure",
        "adv002_source_control_exact_requirement_guard",
        "exact_r_alias_search_context",
        "exact_r_alias_search_source_repair",
        "exact_r_bridge_kill_branch_avoid",
        "exact_r_bridge_materialized_context",
        "exact_r_bridge_missing_identifier_source_repair",
        "exact_r_bridge_redesign_source_repair",
        "exact_r_source_materialization_support_context",
        "exact_r_verification_missing_identifier_source_repair",
        "exact_r_verification_owner_reference_context",
        "m1_backfill_source_coverage_guard",
        "m1_fill_quality_result_pressure",
        "m1_micro_feature_no_signal_context",
        "missed_fill_entry_geometry_source_requirement",
        "missed_fill_to_tp_area_source_requirement",
        "non_xau_fillback_source_inventory_guard",
        "old_backfill_source_bias_guard",
        "old_backfill_source_context",
    ]
    assert block["scope_prefer_event_specific_fields_enabled"] is True
    assert block["scope_prefer_event_specific_fields"] == [
        "route_session",
        "framework",
        "route_family",
        "market_timeframe",
        "horizon_id",
        "primitive",
        "source_component",
        "action_family",
    ]
    assert block["preserve_source_names_when_less_specific"] == ["ai_narrowing_policy"]
    assert block["preserve_evidence_families_when_less_specific"] == ["ai_decision_architecture"]
    assert block["artifact_paths"][0].endswith("GTOS_VNEXT_SCORER_FILTER_ROUTER_IMPLEMENTATION_LEDGER_2026-05-18.jsonl")
    assert block["artifact_paths"][1].endswith("GTOS_VNEXT_EVIDENCE_TO_SYSTEM_BUILD_MATRIX_2026-05-18.jsonl")
    assert any(
        path.endswith("GTOS_VNEXT_ADVERSE_STOP_FIRST_EXECUTION_RUNTIME_ROWS_2026-05-18.jsonl")
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith("GTOS_VNEXT_BRANCH_FOLLOWUP_COMPUTATION_RUNTIME_ROWS_2026-05-18.jsonl")
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith("GTOS_VNEXT_BRANCH_AMBIGUITY_COLLAPSE_RUNTIME_ROWS_2026-05-18.jsonl")
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith("GTOS_VNEXT_BRANCH_IMPLEMENTATION_REPLAY_RUNTIME_ROWS_2026-05-18.jsonl")
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith("VNEXT_PRODUCTION_CHANGE_RUNTIME_CHANGE_LEDGER_2026-05-25.jsonl")
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith("VNEXT_PRODUCTION_CHANGE_KILL_REDESIGN_LEDGER_2026-05-25.jsonl")
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith("VNEXT_PRODUCTION_CHANGE_MIXED_RESOLUTION_LEDGER_2026-05-25.jsonl")
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith("GTOS_VNEXT_EXIT_MANAGEMENT_RESIDUE_RUNTIME_ROWS_2026-05-18.jsonl")
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith("GTOS_VNEXT_Q62_PARTIAL_CLOSE_RUNTIME_ROWS_2026-05-18.jsonl")
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_MAIN_ORCH24_TICK_STRUCTURAL_ENTRY_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_MAIN_ORCH24_ACTION_COMPLETENESS_RESIDUAL_R_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_MAIN_ORCH24_IMPLEMENTATION_SELECTION_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_MAIN_ORCH24_SNAPSHOT_DEPENDENCY_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_MAIN_ORCH48_FINAL_REVIEW_SELECTOR_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_MAIN_ORCH24_SOURCE_ACCEPTED_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_MAIN_ORCH24_SWING_PROTECTED_SOURCE_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_READY8_FAILURE_CONTROL_RESIDUE_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith("GTOS_VNEXT_CP280_SCORER_FILTER_ROUTER_RUNTIME_ROWS_2026-05-18.jsonl")
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith("GTOS_VNEXT_OBSERVABLE_EXECUTION_RUNTIME_ROWS_2026-05-18.jsonl")
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_UNIFIED_EXECUTION_ACTION_WORK_ORDER_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_TARGET_STOP_ORDERING_EXECUTION_SCORING_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_BRANCH_REPLAY_EXECUTION_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_UNIFIED_CANDIDATE_ACTION_EXECUTION_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_UNIFIED_CANDIDATE_SCORING_EXECUTION_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_UNIFIED_EXECUTION_DECISION_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_UNIFIED_SHADOW_SOURCE_MATERIALIZATION_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_SCID_FORWARD_SOURCE_CAPTURE_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_SCID_FUTURE_CAPTURE_SOURCE_STATE_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_SCID_COMBINED_SOURCE_CAPTURE_POI_BOUNDS_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_SCID_NOAPI_SOURCE_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_LIFECYCLE_EXECUTION_SOURCE_GUARD_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_PRE_AI_H1_POI_SOURCE_GAP_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_SHADOW_SOURCE_LOG_MATERIALIZATION_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_TICK_M15_EXECUTION_FRICTION_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_TICK_M15_TARGET_CONTROL_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_NUMERIC_ROUTER_CATALOG_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_SURVIVOR_FAILURE_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_NR_SOURCE_REPAIR_EXECUTION_IDENTITY_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_AI_NARROWING_DEFAULT_OFF_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_AI_DECISION_TRACE_ROUTING_GUARD_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_PRE_AI_POST_L2_ROUTING_POLICY_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_REJECTED_CANDIDATE_L2_VALUE_MINING_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_LEGACY_AI_CASCADE_MODEL_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_LEGACY_T7_SIMULATION_FRICTION_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_LEGACY_V2_V3_PAPER_LIVE_FRICTION_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_SL_BEYOND_OB_OUTCOME_JOIN_SOURCE_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_FVG_TRADE_RECORD_BOUNDS_EXECUTION_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_SCID_TARGET_HORIZON_CONTROL_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_TICK_SOURCE_RECOVERY_QUOTE_CONTRACT_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_LEGACY_LIVE_SHADOW_DECISION_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_EXECUTION_ADJACENT_FRICTION_RESIDUE_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "GTOS_VNEXT_EXIT_MANAGEMENT_TRAILING_J46_RUNTIME_ROWS_2026-05-18.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_CAUSE_IMPLEMENTATION_MATRIX_SOURCE_REPAIR_LEDGER_2026-05-16.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_NUMERIC_RESULT_TABLES_NUMERIC_RESULT_LEDGER_2026-05-17.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_NUMERIC_RESULT_TABLES_EXACT_R_OR_MISSING_PROOF_LEDGER_2026-05-17.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith("HISTORICAL_OHLC_CONTROL_SCREEN_LEDGER_2026-05-15.jsonl")
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith("HISTORICAL_OHLC_CONTROL_SCREEN_ROUTE_QUEUE_2026-05-15.jsonl")
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith("HISTORICAL_OHLC_GTOS_REPLAY_BLOCKER_LEDGER_2026-05-15.jsonl")
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_ACCEPTED_BUILDER_LEDGER_2026-05-16.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_BINDING_RESULT_LEDGER_2026-05-16.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_BRANCH_LEDGER_2026-05-16.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_ENTRY_ADVERSE_RESULT_LEDGER_2026-05-16.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_FAMILY_LEDGER_2026-05-16.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_M15_RESULT_LEDGER_2026-05-16.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_M1_RESULT_LEDGER_2026-05-16.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_POSITIVE_RESULT_LEDGER_2026-05-16.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_SOURCE_RESULT_LEDGER_2026-05-16.jsonl"
        )
        for path in block["artifact_paths"]
    )
    assert any(
        path.endswith(
            "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_ACCEPTED_BUILDER_RESULT_PACKET_REJECTED_REPAIR_LEDGER_2026-05-16.jsonl"
        )
        for path in block["artifact_paths"]
    )
    for artifact_name in (
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_MARKET_GAP_PRIMITIVE_EXPANSION_ACTION_LEDGER_2026-05-16.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_MARKET_GAP_PRIMITIVE_EXPANSION_TRANSFER_CONTEXT_LEDGER_2026-05-16.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_CANDIDATE_SCORING_MARKET_GAP_SCORE_LEDGER_2026-05-16.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_UNIFIED_REPLAY_CODE_CANDIDATE_MARKET_GAP_CODE_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NEARMISS_MARKET_ENTRY_JOIN_BRANCH_SUMMARY_LEDGER_2026-05-16.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NEARMISS_MARKET_ENTRY_JOIN_MARKET_ENTRY_JOIN_LEDGER_2026-05-16.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NEARMISS_MARKET_ENTRY_JOIN_OFFSET_JOIN_LEDGER_2026-05-16.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_SYSTEM_TRANSFER_NEARMISS_MARKET_ENTRY_JOIN_SOURCE_REQUIREMENT_JOIN_LEDGER_2026-05-16.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_CODE_CANDIDATES_ROW_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION_ROW_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_IMPLEMENTATION_CANDIDATES_ROW_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_DECONCENTRATED_SCORER_SURFACES_SURFACE_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_FINAL_IMPLEMENTATION_DECISIONS_DECISION_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_CANDIDATE_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_IMPLEMENTATION_ACTIONS_DECISION_ACTION_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_READINESS_SURFACE_READINESS_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPAIR_IMPLEMENTATION_HANDOFF_HANDOFF_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPAIR_IMPLEMENTATION_ACCEPTANCE_ACCEPTANCE_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCOPE_SCORER_APPLICATION_DEFAULT_OFF_SCORE_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCOPE_SCORER_APPLICATION_AVOID_REDESIGN_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCOPE_SCORER_APPLICATION_REPAIR_REQUIRED_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_PERFORMANCE_ROW_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_CANDIDATE_BUNDLE_RUNTIME_CANDIDATE_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SYMBOL_ACTION_PACKET_SYMBOL_PROXY_SURFACE_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SYMBOL_ACTION_PACKET_SYMBOL_ACTION_PACKET_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_DISPATCH_BUNDLE_GUARD_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_DISPATCH_BUNDLE_MARKET_ROLLUP_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_DISPATCH_BUNDLE_NOFILL_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_DISPATCH_BUNDLE_SCORER_DISPATCH_PLAN_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_IMPLEMENTATION_BUNDLE_MARKET_ROLLUP_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_MATERIALIZATION_BUNDLE_MARKET_ROLLUP_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_RUNTIME_BUNDLE_GUARD_RUNTIME_BINDING_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_RUNTIME_BUNDLE_MARKET_ROLLUP_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_BUNDLE_CANDIDATE_EXECUTION_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_BUNDLE_GUARD_COMPONENT_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_BUNDLE_MARKET_COMPONENT_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_BUNDLE_MARKET_ROLLUP_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_BUNDLE_NOFILL_COMPONENT_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_BUNDLE_RECHECK_COMPONENT_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_BUNDLE_SCORER_COMPONENT_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_BUNDLE_SOURCE_COMPONENT_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_EXECUTABLE_ARTIFACTS_BUNDLE_MARKET_ROLLUP_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_IMPLEMENTATION_EXECUTION_BUNDLE_MARKET_ROLLUP_LEDGER_2026-05-17.jsonl",
        "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_RUNTIME_SURFACES_BUNDLE_MARKET_ROLLUP_LEDGER_2026-05-17.jsonl",
        "GTOS_VNEXT_EXPANDED_MARKET_SOURCE_GEOMETRY_RUNTIME_ROWS_2026-05-18.jsonl",
        "GTOS_VNEXT_NOFILL_PENDING_LIFECYCLE_RUNTIME_ROWS_2026-05-18.jsonl",
        "GTOS_VNEXT_SOURCE_REPAIR_MISSING_DENOMINATOR_RUNTIME_ROWS_2026-05-18.jsonl",
        "GTOS_VNEXT_SIERRA_DEPTH_SOURCE_ACQUISITION_RUNTIME_ROWS_2026-05-18.jsonl",
        "GTOS_VNEXT_RISK_PROXY_STRESS_COST_RUNTIME_ROWS_2026-05-18.jsonl",
        "GTOS_VNEXT_GATE_SELECTOR_SESSION_TIMEFRAME_RUNTIME_ROWS_2026-05-18.jsonl",
        "GTOS_VNEXT_CP280_SCORER_FILTER_ROUTER_RUNTIME_ROWS_2026-05-18.jsonl",
    ):
        assert any(path.endswith(artifact_name) for path in block["artifact_paths"])
    assert block["review_artifact_path"].endswith("GTOS_VNEXT_SCORER_FILTER_ROUTER_REVIEW_LEDGER_2026-05-18.jsonl")
