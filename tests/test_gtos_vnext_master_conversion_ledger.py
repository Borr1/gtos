from __future__ import annotations

import csv
from collections import Counter
from functools import lru_cache
import json
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts import build_gtos_vnext_master_conversion_ledger as ledger
from src.components import gtos_vnext_runtime


@lru_cache(maxsize=1)
def _ledger_rows() -> list[dict]:
    return ledger.build_rows()


@lru_cache(maxsize=1)
def _batch_waves() -> list[dict]:
    return ledger.build_batch_runtime_waves(_ledger_rows())


READY8_CONTEXT_RISK_RULES = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_READY8_CONTEXT_RISK_RULES_2026-05-18.json"
)
READY8_DISCRIMINATIVE_CONTEXT_RULES = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_READY8_DISCRIMINATIVE_CONTEXT_RULES_2026-05-18.json"
)
READY8_DISCRIMINATIVE_CONTEXT_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_READY8_DISCRIMINATIVE_CONTEXT_SUMMARY_2026-05-18.json"
)
READY8_FAILURE_CONTEXT_ADJUSTMENT_RULES = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_READY8_FAILURE_CONTEXT_ADJUSTMENT_RULES_2026-05-18.json"
)
READY8_FAILURE_CONTEXT_ADJUSTMENT_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_READY8_FAILURE_CONTEXT_ADJUSTMENT_SUMMARY_2026-05-18.json"
)
READY8_FAILURE_CONTROL_RESIDUE_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_READY8_FAILURE_CONTROL_RESIDUE_RUNTIME_ROWS_2026-05-18.jsonl"
)
READY8_FAILURE_CONTROL_RESIDUE_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_READY8_FAILURE_CONTROL_RESIDUE_RUNTIME_SUMMARY_2026-05-18.json"
)
REJECTED_CANDIDATE_L2_VALUE_MINING_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_REJECTED_CANDIDATE_L2_VALUE_MINING_RUNTIME_ROWS_2026-05-18.jsonl"
)
REJECTED_CANDIDATE_L2_VALUE_MINING_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_REJECTED_CANDIDATE_L2_VALUE_MINING_RUNTIME_SUMMARY_2026-05-18.json"
)
ACCEPTED_CANDIDATE_M1_FILL_SOURCE_REPAIR_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_ACCEPTED_CANDIDATE_M1_FILL_SOURCE_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
)
ACCEPTED_CANDIDATE_M1_FILL_SOURCE_REPAIR_RUNTIME_SUMMARY = Path(
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
Q62_PARTIAL_CLOSE_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_Q62_PARTIAL_CLOSE_RUNTIME_ROWS_2026-05-18.jsonl"
)
Q62_PARTIAL_CLOSE_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_Q62_PARTIAL_CLOSE_RUNTIME_SUMMARY_2026-05-18.json"
)
MAIN_ORCH24_TICK_STRUCTURAL_ENTRY_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_TICK_STRUCTURAL_ENTRY_RUNTIME_ROWS_2026-05-18.jsonl"
)
MAIN_ORCH24_TICK_STRUCTURAL_ENTRY_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_TICK_STRUCTURAL_ENTRY_RUNTIME_SUMMARY_2026-05-18.json"
)
MAIN_ORCH24_STRUCTURAL_REPAIR_ACTION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_STRUCTURAL_REPAIR_ACTION_RUNTIME_ROWS_2026-05-18.jsonl"
)
MAIN_ORCH24_STRUCTURAL_REPAIR_ACTION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_STRUCTURAL_REPAIR_ACTION_RUNTIME_SUMMARY_2026-05-18.json"
)
MAIN_ORCH24_ACTION_COMPLETENESS_RESIDUAL_R_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_ACTION_COMPLETENESS_RESIDUAL_R_RUNTIME_ROWS_2026-05-18.jsonl"
)
MAIN_ORCH24_ACTION_COMPLETENESS_RESIDUAL_R_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_ACTION_COMPLETENESS_RESIDUAL_R_RUNTIME_SUMMARY_2026-05-18.json"
)
MAIN_ORCH24_IMPLEMENTATION_SELECTION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_IMPLEMENTATION_SELECTION_RUNTIME_ROWS_2026-05-18.jsonl"
)
MAIN_ORCH24_IMPLEMENTATION_SELECTION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_IMPLEMENTATION_SELECTION_RUNTIME_SUMMARY_2026-05-18.json"
)
MAIN_ORCH24_SNAPSHOT_DEPENDENCY_REPAIR_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_SNAPSHOT_DEPENDENCY_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
)
MAIN_ORCH24_SNAPSHOT_DEPENDENCY_REPAIR_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_SNAPSHOT_DEPENDENCY_REPAIR_RUNTIME_SUMMARY_2026-05-18.json"
)
MAIN_ORCH24_UNIFIED_CANDIDATE_PATH_PROXY_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_UNIFIED_CANDIDATE_PATH_PROXY_RUNTIME_ROWS_2026-05-18.jsonl"
)
MAIN_ORCH24_UNIFIED_CANDIDATE_PATH_PROXY_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_UNIFIED_CANDIDATE_PATH_PROXY_RUNTIME_SUMMARY_2026-05-18.json"
)
MAIN_ORCH48_FINAL_REVIEW_SELECTOR_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH48_FINAL_REVIEW_SELECTOR_RUNTIME_ROWS_2026-05-18.jsonl"
)
MAIN_ORCH48_FINAL_REVIEW_SELECTOR_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH48_FINAL_REVIEW_SELECTOR_RUNTIME_SUMMARY_2026-05-18.json"
)
LTF_PATH_GEOMETRY_SOURCE_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LTF_PATH_GEOMETRY_SOURCE_RUNTIME_ROWS_2026-05-18.jsonl"
)
LTF_PATH_GEOMETRY_SOURCE_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LTF_PATH_GEOMETRY_SOURCE_RUNTIME_SUMMARY_2026-05-18.json"
)
INSTRUMENT_EXPANSION_MARKET_SESSION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_INSTRUMENT_EXPANSION_MARKET_SESSION_RUNTIME_ROWS_2026-05-18.jsonl"
)
INSTRUMENT_EXPANSION_MARKET_SESSION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_INSTRUMENT_EXPANSION_MARKET_SESSION_RUNTIME_SUMMARY_2026-05-18.json"
)
SCID_COMBINED_SOURCE_CAPTURE_POI_BOUNDS_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SCID_COMBINED_SOURCE_CAPTURE_POI_BOUNDS_RUNTIME_ROWS_2026-05-18.jsonl"
)
SCID_COMBINED_SOURCE_CAPTURE_POI_BOUNDS_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SCID_COMBINED_SOURCE_CAPTURE_POI_BOUNDS_RUNTIME_SUMMARY_2026-05-18.json"
)
SCID_NOAPI_SOURCE_REPAIR_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SCID_NOAPI_SOURCE_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
)
SCID_NOAPI_SOURCE_REPAIR_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SCID_NOAPI_SOURCE_REPAIR_RUNTIME_SUMMARY_2026-05-18.json"
)
LIFECYCLE_EXECUTION_SOURCE_GUARD_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LIFECYCLE_EXECUTION_SOURCE_GUARD_RUNTIME_ROWS_2026-05-18.jsonl"
)
LIFECYCLE_EXECUTION_SOURCE_GUARD_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LIFECYCLE_EXECUTION_SOURCE_GUARD_RUNTIME_SUMMARY_2026-05-18.json"
)
MAIN_ORCH24_SOURCE_ACCEPTED_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_SOURCE_ACCEPTED_RUNTIME_ROWS_2026-05-18.jsonl"
)
MAIN_ORCH24_SOURCE_ACCEPTED_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_SOURCE_ACCEPTED_RUNTIME_SUMMARY_2026-05-18.json"
)
MAIN_ORCH24_SWING_PROTECTED_SOURCE_REPAIR_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_SWING_PROTECTED_SOURCE_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
)
MAIN_ORCH24_SWING_PROTECTED_SOURCE_REPAIR_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_SWING_PROTECTED_SOURCE_REPAIR_RUNTIME_SUMMARY_2026-05-18.json"
)
MAIN_ORCH24_SOURCE_M15_BRANCH_REPAIR_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_SOURCE_M15_BRANCH_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
)
MAIN_ORCH24_SOURCE_M15_BRANCH_REPAIR_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_SOURCE_M15_BRANCH_REPAIR_RUNTIME_SUMMARY_2026-05-18.json"
)
MAIN_ORCH24_LIVE_MECHANICAL_GEOMETRY_OUTCOME_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_LIVE_MECHANICAL_GEOMETRY_OUTCOME_RUNTIME_ROWS_2026-05-18.jsonl"
)
MAIN_ORCH24_LIVE_MECHANICAL_GEOMETRY_OUTCOME_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_MAIN_ORCH24_LIVE_MECHANICAL_GEOMETRY_OUTCOME_RUNTIME_SUMMARY_2026-05-18.json"
)
TICK_SOURCE_RECOVERY_QUOTE_CONTRACT_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_TICK_SOURCE_RECOVERY_QUOTE_CONTRACT_RUNTIME_ROWS_2026-05-18.jsonl"
)
TICK_SOURCE_RECOVERY_QUOTE_CONTRACT_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_TICK_SOURCE_RECOVERY_QUOTE_CONTRACT_RUNTIME_SUMMARY_2026-05-18.json"
)
LEGACY_LIVE_SHADOW_DECISION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LEGACY_LIVE_SHADOW_DECISION_RUNTIME_ROWS_2026-05-18.jsonl"
)
LEGACY_LIVE_SHADOW_DECISION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LEGACY_LIVE_SHADOW_DECISION_RUNTIME_SUMMARY_2026-05-18.json"
)
ENTRY_OFFSET_050R_CLUSTER_GUARD_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_ENTRY_OFFSET_050R_CLUSTER_GUARD_RUNTIME_ROWS_2026-05-18.jsonl"
)
ENTRY_OFFSET_050R_CLUSTER_GUARD_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_ENTRY_OFFSET_050R_CLUSTER_GUARD_RUNTIME_SUMMARY_2026-05-18.json"
)
OPENING_DRIVE_SOURCE_CONTRACT_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_OPENING_DRIVE_SOURCE_CONTRACT_RUNTIME_ROWS_2026-05-18.jsonl"
)
OPENING_DRIVE_SOURCE_CONTRACT_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_OPENING_DRIVE_SOURCE_CONTRACT_RUNTIME_SUMMARY_2026-05-18.json"
)
NUMERIC_ROUTER_CATALOG_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_NUMERIC_ROUTER_CATALOG_RUNTIME_ROWS_2026-05-18.jsonl"
)
NUMERIC_ROUTER_CATALOG_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_NUMERIC_ROUTER_CATALOG_RUNTIME_SUMMARY_2026-05-18.json"
)
SURVIVOR_FAILURE_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SURVIVOR_FAILURE_RUNTIME_ROWS_2026-05-18.jsonl"
)
SURVIVOR_FAILURE_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SURVIVOR_FAILURE_RUNTIME_SUMMARY_2026-05-18.json"
)
NR_SOURCE_REPAIR_EXECUTION_IDENTITY_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_NR_SOURCE_REPAIR_EXECUTION_IDENTITY_RUNTIME_ROWS_2026-05-18.jsonl"
)
NR_SOURCE_REPAIR_EXECUTION_IDENTITY_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_NR_SOURCE_REPAIR_EXECUTION_IDENTITY_RUNTIME_SUMMARY_2026-05-18.json"
)
AI_NARROWING_DEFAULT_OFF_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_AI_NARROWING_DEFAULT_OFF_RUNTIME_ROWS_2026-05-18.jsonl"
)
AI_NARROWING_DEFAULT_OFF_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_AI_NARROWING_DEFAULT_OFF_RUNTIME_SUMMARY_2026-05-18.json"
)
AI_DECISION_TRACE_ROUTING_GUARD_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_AI_DECISION_TRACE_ROUTING_GUARD_RUNTIME_ROWS_2026-05-18.jsonl"
)
AI_DECISION_TRACE_ROUTING_GUARD_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_AI_DECISION_TRACE_ROUTING_GUARD_RUNTIME_SUMMARY_2026-05-18.json"
)
PRE_AI_POST_L2_ROUTING_POLICY_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_PRE_AI_POST_L2_ROUTING_POLICY_RUNTIME_ROWS_2026-05-18.jsonl"
)
PRE_AI_POST_L2_ROUTING_POLICY_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_PRE_AI_POST_L2_ROUTING_POLICY_RUNTIME_SUMMARY_2026-05-18.json"
)
LEGACY_AI_CASCADE_MODEL_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LEGACY_AI_CASCADE_MODEL_RUNTIME_ROWS_2026-05-18.jsonl"
)
LEGACY_AI_CASCADE_MODEL_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LEGACY_AI_CASCADE_MODEL_RUNTIME_SUMMARY_2026-05-18.json"
)
EXIT_MANAGEMENT_TRAILING_J46_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_EXIT_MANAGEMENT_TRAILING_J46_RUNTIME_ROWS_2026-05-18.jsonl"
)
EXIT_MANAGEMENT_TRAILING_J46_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_EXIT_MANAGEMENT_TRAILING_J46_RUNTIME_SUMMARY_2026-05-18.json"
)
EXIT_MANAGEMENT_RESIDUE_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_EXIT_MANAGEMENT_RESIDUE_RUNTIME_ROWS_2026-05-18.jsonl"
)
EXIT_MANAGEMENT_RESIDUE_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_EXIT_MANAGEMENT_RESIDUE_RUNTIME_SUMMARY_2026-05-18.json"
)
LEGACY_T7_SIMULATION_FRICTION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LEGACY_T7_SIMULATION_FRICTION_RUNTIME_ROWS_2026-05-18.jsonl"
)
LEGACY_T7_SIMULATION_FRICTION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LEGACY_T7_SIMULATION_FRICTION_RUNTIME_SUMMARY_2026-05-18.json"
)
LEGACY_V2_V3_PAPER_LIVE_FRICTION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LEGACY_V2_V3_PAPER_LIVE_FRICTION_RUNTIME_ROWS_2026-05-18.jsonl"
)
LEGACY_V2_V3_PAPER_LIVE_FRICTION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_LEGACY_V2_V3_PAPER_LIVE_FRICTION_RUNTIME_SUMMARY_2026-05-18.json"
)
SL_BEYOND_OB_OUTCOME_JOIN_SOURCE_REPAIR_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SL_BEYOND_OB_OUTCOME_JOIN_SOURCE_REPAIR_RUNTIME_ROWS_2026-05-18.jsonl"
)
SL_BEYOND_OB_OUTCOME_JOIN_SOURCE_REPAIR_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SL_BEYOND_OB_OUTCOME_JOIN_SOURCE_REPAIR_RUNTIME_SUMMARY_2026-05-18.json"
)
FVG_TRADE_RECORD_BOUNDS_EXECUTION_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_FVG_TRADE_RECORD_BOUNDS_EXECUTION_RUNTIME_ROWS_2026-05-18.jsonl"
)
FVG_TRADE_RECORD_BOUNDS_EXECUTION_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_FVG_TRADE_RECORD_BOUNDS_EXECUTION_RUNTIME_SUMMARY_2026-05-18.json"
)
SCID_TARGET_HORIZON_CONTROL_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SCID_TARGET_HORIZON_CONTROL_RUNTIME_ROWS_2026-05-18.jsonl"
)
SCID_TARGET_HORIZON_CONTROL_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_SCID_TARGET_HORIZON_CONTROL_RUNTIME_SUMMARY_2026-05-18.json"
)
EXECUTION_ADJACENT_FRICTION_RESIDUE_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_EXECUTION_ADJACENT_FRICTION_RESIDUE_RUNTIME_ROWS_2026-05-18.jsonl"
)
EXECUTION_ADJACENT_FRICTION_RESIDUE_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_EXECUTION_ADJACENT_FRICTION_RESIDUE_RUNTIME_SUMMARY_2026-05-18.json"
)
TRADE_RECORD_EXECUTION_LIFECYCLE_RUNTIME_ROWS = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_TRADE_RECORD_EXECUTION_LIFECYCLE_RUNTIME_ROWS_2026-05-18.jsonl"
)
TRADE_RECORD_EXECUTION_LIFECYCLE_RUNTIME_SUMMARY = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "gtos_vnext_research_to_runtime_builder/"
    "GTOS_VNEXT_TRADE_RECORD_EXECUTION_LIFECYCLE_RUNTIME_SUMMARY_2026-05-18.json"
)


def _row(position: int, state: str, **overrides) -> dict:
    row = {
        "schema_version": "gtos_vnext_master_intelligence_to_runtime_conversion_ledger_v1",
        "intelligence_unit_id": f"UNIT_{position:06d}",
        "execution_position": position,
        "source_artifact_path": f"research/unit_{position}.jsonl",
        "source_artifact_hash": "abc123",
        "source_artifact_hash_algorithm": "git_blob",
        "source_artifact_paths": [f"research/unit_{position}.jsonl"],
        "evidence_family": "fixture",
        "affected_runtime_surface": "fixture_runtime_surface",
        "conversion_state": state,
        "implemented_commit": "",
        "tests_verifier": "",
        "remaining_action": "consume this fixture unit",
        "not_directly_convertible_reason": (
            "" if state != "NOT_STARTED" else "ordered fixture unit not started"
        ),
        "missing_field_source": "",
        "next_code_config_test_action": "",
    }
    row.update(overrides)
    return row


def test_master_ledger_summary_reports_required_checkpoint_counts(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "SUMMARY_PATH", tmp_path / "missing_summary.json")
    rows = [
        _row(
            1,
            "IMPLEMENTED_RUNTIME_CODE_CONFIG_TESTS",
            intelligence_unit_id=ledger.CURRENT_UNIT_ID,
        ),
        _row(2, "CONVERTED_AI_NARROWING_OR_AI_REMOVAL_RULE"),
        _row(
            3,
            "REPAIR_NEEDED_WITH_EXACT_FIELD_SOURCE_CODE_ACTION",
            missing_field_source="broker_execution_geometry_fields",
            next_code_config_test_action="add offline geometry repair adapter and tests",
            not_directly_convertible_reason="exact broker geometry field missing",
        ),
        _row(4, "NOT_STARTED"),
    ]

    ledger.validate_rows(rows)
    summary = ledger.build_summary(rows)

    assert summary["total_intelligence_units"] == 4
    assert summary["implemented_units"] == 1
    assert summary["converted_units"] == 1
    assert summary["repair_action_defined_units"] == 1
    assert summary["not_started_units"] == 1
    assert summary["current_unit_being_consumed"]["intelligence_unit_id"] == ledger.CURRENT_UNIT_ID
    assert summary["next_unit_being_consumed"]["intelligence_unit_id"] == "UNIT_000004"
    assert summary["delta_since_previous_checkpoint"]["previous_summary_found"] is False


def test_master_ledger_next_unit_prefers_current_cp281_moonshot_over_old_handoff(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "SUMMARY_PATH", tmp_path / "missing_summary.json")
    rows = [
        _row(
            1,
            "CONVERTED_AVOID_FILTER",
            intelligence_unit_id=ledger.CURRENT_UNIT_ID,
        ),
        _row(
            2,
            "NOT_STARTED",
            source_artifact_path=".context/02_session_handoffs/RESEARCH_PROGRAM_KICKOFF.md",
            evidence_family="historical_handoff",
        ),
        _row(
            3,
            "NOT_STARTED",
            source_artifact_path=(
                "research/science_program_2026_05/06_outcome_testing/"
                "main_orchestrator_24h_full_stack_research_integration_materialization/"
                "MAIN_ORCH48_CP281_READY_RUNTIME_MAPPING_SUMMARY_2026-05-18.json"
            ),
            evidence_family="cp280_cp281_cp282_moonshot",
        ),
    ]

    ledger.validate_rows(rows)
    summary = ledger.build_summary(rows)

    assert summary["next_unit_being_consumed"]["intelligence_unit_id"] == "UNIT_000003"
    assert "CP281" in summary["next_unit_being_consumed"]["source_artifact_path"]


def _json(path_text: str) -> dict:
    return json.loads((ledger.REPO_ROOT / path_text).read_text(encoding="utf-8"))


def _jsonl(path_text: str) -> list[dict]:
    return [
        json.loads(line)
        for line in (ledger.REPO_ROOT / path_text).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _yaml(path_text: str) -> dict:
    return yaml.safe_load((ledger.REPO_ROOT / path_text).read_text(encoding="utf-8"))


def test_cp281_event_field_availability_source_repair_stays_consumed():
    repair_unit = next(
        unit
        for unit in ledger.MANUAL_UNITS
        if unit["intelligence_unit_id"] == "MANUAL_RUNTIME_CP281_EVENT_FIELD_AVAILABILITY_SOURCE_REPAIR"
    )

    assert repair_unit["conversion_state"] == "IMPLEMENTED_RUNTIME_CODE_CONFIG_TESTS"
    assert "MAIN_ORCH48_CP281_EVENT_FIELD_AVAILABILITY_LEDGER_2026-05-18.jsonl" in repair_unit["source_artifact_path"]
    assert "src/components/gtos_vnext_event_fields.py" in repair_unit["source_artifact_paths"]
    assert "source_path_sha256" in repair_unit["next_code_config_test_action"]


def test_cp281_event_field_availability_wrappers_stay_consumed():
    wrapper_ids = {
        "MANUAL_KILL_CP281_EVENT_FIELD_AVAILABILITY_MANIFEST_WRAPPER",
        "MANUAL_KILL_CP281_EVENT_FIELD_AVAILABILITY_SUMMARY_WRAPPER",
        "MANUAL_KILL_CP281_EVENT_FIELD_AVAILABILITY_VERIFY_WRAPPER",
    }
    current_units = [
        unit
        for unit in ledger.MANUAL_UNITS
        if unit["intelligence_unit_id"] in wrapper_ids
    ]

    assert len(current_units) == 3
    assert {unit["conversion_state"] for unit in current_units} == {
        "KILLED_BY_COMPUTED_EVIDENCE_WITH_TESTED_REASON",
    }


def test_cp281_ready_runtime_aggregate_provenance_stays_consumed():
    aggregate_unit = next(
        unit
        for unit in ledger.MANUAL_UNITS
        if unit["intelligence_unit_id"] == "MANUAL_RUNTIME_CP281_READY_RUNTIME_MAPPING_AGGREGATE_PROVENANCE"
    )

    assert aggregate_unit["conversion_state"] == "IMPLEMENTED_RUNTIME_CODE_CONFIG_TESTS"
    assert "MAIN_ORCH48_CP281_READY_RUNTIME_MAPPING_AGGREGATE_LEDGER_2026-05-18.jsonl" in aggregate_unit["source_artifact_path"]
    assert "MAIN_ORCH48_CP281_BRANCH_DECISIONS_LEDGER_2026-05-18.jsonl" in " ".join(
        aggregate_unit["source_artifact_paths"]
    )


def test_cp281_source_contract_matching_stays_consumed():
    source_contract = next(
        unit
        for unit in ledger.MANUAL_UNITS
        if unit["intelligence_unit_id"]
        == "MANUAL_RUNTIME_CP281_READY_RUNTIME_MAPPING_SOURCE_CONTRACT_MATCHING"
    )

    assert source_contract["conversion_state"] == "IMPLEMENTED_RUNTIME_CODE_CONFIG_TESTS"
    assert "MAIN_ORCH48_CP281_READY_RUNTIME_MAPPING_SOURCE_CONTRACT_LEDGER_2026-05-18.jsonl" in source_contract[
        "source_artifact_path"
    ]
    assert "src/components/gtos_vnext_event_fields.py" in source_contract["source_artifact_paths"]
    assert "source_file_sha256" in " ".join(
        source_contract["source_artifact_paths"]
    ) or "source_file_sha256" in source_contract["next_code_config_test_action"]


def test_cp281_self_check_runtime_regression_stays_consumed():
    self_check = next(
        unit
        for unit in ledger.MANUAL_UNITS
        if unit["intelligence_unit_id"]
        == "MANUAL_RUNTIME_CP281_READY_RUNTIME_MAPPING_SELF_CHECK_REGRESSION"
    )

    assert self_check["conversion_state"] == "IMPLEMENTED_RUNTIME_CODE_CONFIG_TESTS"
    assert "MAIN_ORCH48_CP281_READY_RUNTIME_MAPPING_SELF_CHECK_LEDGER_2026-05-18.jsonl" in self_check[
        "source_artifact_path"
    ]


def test_long_path_source_discovery_skips_index_entries_absent_from_the_worktree(
    tmp_path, monkeypatch,
):
    """``iter_current_wave_long_path_source_files`` must not yield phantom sources.

    ``_git_ls_files_with_blob_hash`` reports *index* entries. Under a sparse
    checkout a tracked path can be in the index and absent from disk, and this
    repo is exactly that case (2,171 of 4,133 tracked ``*.py`` are not
    materialized here). Both other consumers of that helper filter with
    ``path.exists()``; this one did not, so 24 non-existent long-path ledgers
    entered ``build_rows()`` as real source artifacts carrying a git-blob hash.

    Fixture: a throwaway git repo with two committed ledgers, one of which is
    then removed from the worktree while staying in the index. The materialized
    one must come through and the phantom must not — so the test is non-vacuous
    in either direction and fails against the unguarded implementation.
    """
    repo = tmp_path / "wave_repo"
    route = repo / "route"
    route.mkdir(parents=True)
    materialized = route / "MATERIALIZED_LEDGER_2026-05-17.jsonl"
    phantom = route / "PHANTOM_LEDGER_2026-05-17.jsonl"
    materialized.write_text('{"row": 1}\n', encoding="utf-8")
    phantom.write_text('{"row": 2}\n', encoding="utf-8")

    def git(*args: str) -> None:
        done = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, timeout=120,
        )
        assert done.returncode == 0, f"git {args}: {done.stderr}"

    git("init", "-q")
    git("config", "user.email", "redacted@example.com")
    git("config", "user.name", "test")
    git("add", "route")
    git("commit", "-q", "-m", "seed")

    # In the index, gone from the worktree — what a sparse checkout looks like.
    phantom.unlink()
    tracked = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "--", "route"],
        capture_output=True, text=True, timeout=120,
    ).stdout.split()
    assert "route/PHANTOM_LEDGER_2026-05-17.jsonl" in tracked, (
        "fixture is broken: the phantom must still be a tracked index entry"
    )

    monkeypatch.setattr(ledger, "MOONSHOT_REPO", repo)
    monkeypatch.setattr(ledger, "MOONSHOT_ROUTE", route)
    monkeypatch.setattr(
        ledger,
        "UNIFIED_SHADOW_SOURCE_MATERIALIZATION_LONG_PATH_SOURCE_NAMES",
        (materialized.name, phantom.name),
    )

    yielded = list(ledger.iter_current_wave_long_path_source_files(set()))
    names = [path.name for path, _, _ in yielded]

    assert materialized.name in names, (
        "the materialized long-path ledger must still be discovered"
    )
    assert phantom.name not in names, (
        "a tracked-but-absent index entry was emitted as a source artifact; "
        f"got {names}"
    )
    assert all(path.exists() for path, _, _ in yielded)


def test_old_moonshot_wrapper_batch_remains_closed_as_superseded():
    batch_unit = next(
        unit
        for unit in ledger.MANUAL_UNITS
        if unit["intelligence_unit_id"] == "MANUAL_KILL_OLD_MOONSHOT_WRAPPER_BATCH_SUPERSEDED"
    )

    assert batch_unit["conversion_state"] == "KILLED_BY_COMPUTED_EVIDENCE_WITH_TESTED_REASON"
    assert Path(batch_unit["source_artifact_path"]).name == "OUTPUT_MANIFEST_2026-05-15.json"
    assert "do not spend one checkpoint per old wrapper" in batch_unit["next_code_config_test_action"]


def test_non_material_resume_handoff_is_not_added_to_execution_denominator():
    expected_non_material_handoffs = {
        f"SESSION_{number}_NON_MATERIAL_CONTEXT_HANDOFF_2026-05-{day}.md"
        for number, day in (
            (70, "19"),
            (71, "19"),
            (72, "19"),
            (73, "20"),
            (74, "20"),
            (75, "20"),
            (76, "20"),
            (77, "20"),
        )
    }
    assert all(
        ledger._is_non_material_handoff_source_name(name)
        for name in expected_non_material_handoffs
    )

    excluded_names = {
        Path(row["source_artifact_path"]).name
        for row in ledger.build_rows()
        if ledger._is_non_material_handoff_source_name(
            Path(row["source_artifact_path"]).name
        )
    }

    assert excluded_names == set()


def test_repair_needed_rows_must_have_exact_field_surface_and_code_action():
    rows = [
        _row(
            1,
            "REPAIR_NEEDED_WITH_EXACT_FIELD_SOURCE_CODE_ACTION",
            missing_field_source="",
            next_code_config_test_action="",
            not_directly_convertible_reason="missing field",
        )
    ]

    with pytest.raises(ValueError, match="repair row lacks missing_field_source"):
        ledger.validate_rows(rows)


def test_killed_rows_require_computed_tested_reason():
    rows = [
        _row(
            1,
            "KILLED_BY_COMPUTED_EVIDENCE_WITH_TESTED_REASON",
            tests_verifier="",
            not_directly_convertible_reason="",
        )
    ]

    with pytest.raises(ValueError, match="killed row lacks tested reason"):
        ledger.validate_rows(rows)


def test_source_repair_artifacts_are_actionable_repair_units():
    disposition = ledger.classify_artifact(
        "research/science_program_2026_05/06_outcome_testing/"
        "main_orchestrator_24h_full_stack_research_integration_materialization/"
        "MAIN_ORCH48_NUMERIC_ROUTER_SOURCE_REPAIR_EXECUTION_PLAN_2026-05-18.jsonl"
    )

    assert disposition.conversion_state == "REPAIR_NEEDED_WITH_EXACT_FIELD_SOURCE_CODE_ACTION"
    assert "source-bound geometry" in disposition.missing_field_source
    assert "adapter" in disposition.next_code_config_test_action


def test_apr17_prompt_wrapper_is_killed_only_because_handoff_unit_is_consumed():
    prompt_disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/21_apr17_FRESH_SESSION_PROMPT.md"
    )
    handoff_disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/21_apr17_test_isolation_exposed_bugs_handoff.md"
    )

    assert prompt_disposition.conversion_state == (
        "KILLED_BY_COMPUTED_EVIDENCE_WITH_TESTED_REASON"
    )
    assert "prompt wrapper" in prompt_disposition.not_directly_convertible_reason
    assert "UNIT_000047" in prompt_disposition.next_code_config_test_action
    assert handoff_disposition.conversion_state == "IMPLEMENTED_RUNTIME_CODE_CONFIG_TESTS"
    assert "production_path" in handoff_disposition.runtime_surface


def test_apr17_session23_prompt_wrapper_is_killed_only_because_canary_cache_handoff_is_consumed():
    prompt_disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/23_apr17_FRESH_SESSION_PROMPT.md"
    )
    handoff_disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/23_apr17_task_C_canary_cache_handoff.md"
    )

    assert prompt_disposition.conversion_state == (
        "KILLED_BY_COMPUTED_EVIDENCE_WITH_TESTED_REASON"
    )
    assert "prompt wrapper" in prompt_disposition.not_directly_convertible_reason
    assert "UNIT_000050" in prompt_disposition.next_code_config_test_action
    assert handoff_disposition.conversion_state == "IMPLEMENTED_RUNTIME_CODE_CONFIG_TESTS"
    assert "canary_schema_v2_pass_cache" in handoff_disposition.runtime_surface
    assert "test_current_fleet_prompt_hash_slots_all_validate" in (
        handoff_disposition.tests_verifier
    )


def test_apr18_session24_prompt_wrapper_is_killed_only_because_ob_monitor_handoff_is_consumed():
    prompt_disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/24_apr18_FRESH_SESSION_PROMPT.md"
    )
    handoff_disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/24_apr18_task_A_ob_continuation_monitor_handoff.md"
    )

    assert prompt_disposition.conversion_state == (
        "KILLED_BY_COMPUTED_EVIDENCE_WITH_TESTED_REASON"
    )
    assert "prompt wrapper" in prompt_disposition.not_directly_convertible_reason
    assert "UNIT_000052" in prompt_disposition.next_code_config_test_action
    assert handoff_disposition.conversion_state == "IMPLEMENTED_RUNTIME_CODE_CONFIG_TESTS"
    assert "ob_continuation_monitor" in handoff_disposition.runtime_surface
    assert "test_main_symbols_override" in handoff_disposition.tests_verifier


def test_apr18_session25_prompt_wrapper_is_killed_only_because_tier2_execution_handoff_is_consumed():
    prompt_disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/25_apr18_FRESH_SESSION_TIER2_VERIFICATION_PROMPT.md"
    )
    handoff_disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/25_apr18_retest_tier1_verified_tier2_dispatched_handoff.md"
    )

    assert prompt_disposition.conversion_state == (
        "KILLED_BY_COMPUTED_EVIDENCE_WITH_TESTED_REASON"
    )
    assert "prompt wrapper" in prompt_disposition.not_directly_convertible_reason
    assert "UNIT_000054" in prompt_disposition.next_code_config_test_action
    assert handoff_disposition.conversion_state == (
        "CONVERTED_NOFILL_PENDING_EXECUTION_BEHAVIOR"
    )
    assert "software_pending_limit_market_order" in handoff_disposition.runtime_surface
    assert "test_limit_fill_executes_market_order_at_current_tick_not_limit_price" in (
        handoff_disposition.tests_verifier
    )


def test_apr18_session26_prompt_wrapper_is_killed_only_because_prechallenge_handoff_is_consumed():
    prompt_disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/26_apr18_FRESH_SESSION_PRE_CHALLENGE_UNLOCK_PROMPT.md"
    )
    handoff_disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/26_apr18_pre_challenge_tier1_shipped_handoff.md"
    )

    assert prompt_disposition.conversion_state == (
        "KILLED_BY_COMPUTED_EVIDENCE_WITH_TESTED_REASON"
    )
    assert "prompt wrapper" in prompt_disposition.not_directly_convertible_reason
    assert "UNIT_000056" in prompt_disposition.next_code_config_test_action
    assert handoff_disposition.conversion_state == (
        "CONVERTED_GATE_SELECTOR_FRAMEWORK_BEHAVIOR"
    )
    assert "structural_sl_exception" in handoff_disposition.runtime_surface
    assert "test_apr16_sweep_zone_rejection_logs_sweep_margin_failure" in (
        handoff_disposition.tests_verifier
    )


def test_apr18_session27_meta_handoff_is_killed_only_because_gate0_runtime_unit_is_consumed():
    meta_disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/27_apr18_session_close_handoff.md"
    )
    gate0_disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/28_apr19_session_close_handoff.md"
    )

    assert meta_disposition.conversion_state == (
        "KILLED_BY_COMPUTED_EVIDENCE_WITH_TESTED_REASON"
    )
    assert "no trading-logic changes" in meta_disposition.not_directly_convertible_reason
    assert "UNIT_000058" in meta_disposition.next_code_config_test_action
    assert gate0_disposition.conversion_state == (
        "CONVERTED_GATE_SELECTOR_FRAMEWORK_BEHAVIOR"
    )
    assert "deployment_phase_gate0" in gate0_disposition.runtime_surface
    assert "test_phase_2_permission_denial_routes_to_log_only_no_order" in (
        gate0_disposition.tests_verifier
    )
    assert "test_phase_2_permission_denial_attaches_log_only_evidence_to_record" in (
        gate0_disposition.tests_verifier
    )


def test_apr19_session29_canary_tiered_threshold_unit_is_implemented():
    disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/29_apr19_session_close_handoff.md"
    )

    assert disposition.conversion_state == "IMPLEMENTED_RUNTIME_CODE_CONFIG_TESTS"
    assert "canary_fixture_tiered" in disposition.runtime_surface
    assert "32 baseline / 51 borderline" in disposition.next_code_config_test_action
    assert "test_current_manifest_uses_tiered_thresholds" in disposition.tests_verifier


def test_apr19_session30_monitoring_unit_is_implemented():
    disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/30_apr19_session_close_handoff.md"
    )

    assert disposition.conversion_state == "IMPLEMENTED_RUNTIME_CODE_CONFIG_TESTS"
    assert "model_pin_candidate_rate_cusum_no_data_alert" in disposition.runtime_surface
    assert "XAGUSD and NAS100" in disposition.remaining_action
    assert "test_supervised_symbol_maps_cover_watchdog_fleet" in (
        disposition.tests_verifier
    )


def test_apr19_session31_runtime_guard_unit_is_implemented():
    disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/31_apr19_session_close_handoff.md"
    )

    assert disposition.conversion_state == "IMPLEMENTED_RUNTIME_CODE_CONFIG_TESTS"
    assert "canary_cache_pid_tid" in disposition.runtime_surface
    assert "pending_intent_utc_day_staleness" in disposition.runtime_surface
    assert "autostart_halt_weekend_profile_guards" in disposition.runtime_surface
    assert "test_cache_write_tmp_path_includes_pid_and_thread_id" in (
        disposition.tests_verifier
    )
    assert "test_same_utc_day_pending_intent_before_first_kz_survives_restart" in (
        disposition.tests_verifier
    )
    assert "tests/test_start_all_runtime_contract.py" in disposition.tests_verifier


def test_apr19_session32_correlation_shock_unit_is_converted():
    disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/32_apr19_session_close_handoff.md"
    )

    assert disposition.conversion_state == "CONVERTED_GATE_SELECTOR_FRAMEWORK_BEHAVIOR"
    assert "correlation_shock_monitor_watchdog" in disposition.runtime_surface
    assert "us_indices_nas100_risk_group" in disposition.runtime_surface
    assert "gbpusd_cross_instrument_context_strip" in disposition.runtime_surface
    assert "test_nas100_reduced_when_us30_open" in disposition.tests_verifier
    assert "test_us_indices_include_live_nas100_pairs" in disposition.tests_verifier
    assert "tests/test_watchdog_correlation_shock_contract.py" in (
        disposition.tests_verifier
    )


def test_apr19_session33_d1_lag_ai_route_unit_is_converted():
    disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/33_apr19_session_close_handoff.md"
    )

    assert disposition.conversion_state == "CONVERTED_AI_NARROWING_OR_AI_REMOVAL_RULE"
    assert "d1_bias_lag" in disposition.evidence_family
    assert "structural_c_gate_d1_lag_h4_h1_consensus" in disposition.runtime_surface
    assert "test_d1_lag_h4_h1_consensus_routes_against_stale_d1_bias" in (
        disposition.tests_verifier
    )
    assert "test_orchestrator_applies_d1_lag_route_to_runtime_bias" in (
        disposition.tests_verifier
    )


def test_apr19_session34_daily_loss_pending_cancel_unit_is_converted():
    disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/34_apr19_FRESH_SESSION_POST_NAS100_PROMPT.md"
    )

    assert disposition.conversion_state == "CONVERTED_NOFILL_PENDING_EXECUTION_BEHAVIOR"
    assert "daily_loss_stop" in disposition.evidence_family
    assert "cross_symbol_pending_intent_cancel" in disposition.runtime_surface
    assert "test_trigger_clears_all_persisted_pending_intent_files" in (
        disposition.tests_verifier
    )
    assert "test_dormant_gate_helper_cancels_local_in_memory_pending_intent" in (
        disposition.tests_verifier
    )


def test_apr19_session35_fill_epsilon_alias_unit_is_converted():
    disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/35_apr19_FRESH_SESSION_PRE_redacted_account_EDGE_INVESTIGATION.md"
    )

    assert disposition.conversion_state == "CONVERTED_NOFILL_PENDING_EXECUTION_BEHAVIOR"
    assert "fillability_epsilon_scaling" in disposition.evidence_family
    assert "vnext_alias_and_futures_family_epsilon" in disposition.runtime_surface
    assert "test_vnext_and_futures_aliases_use_family_epsilon" in (
        disposition.tests_verifier
    )
    assert "test_usdjpy_futures_alias_does_not_use_legacy_wide_epsilon" in (
        disposition.tests_verifier
    )


def test_apr20_session36_sim_validator_parity_unit_is_converted():
    disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/36_apr20_FRESH_SESSION_redacted_account_READINESS_VERIFICATION_AND_FA4.md"
    )

    assert disposition.conversion_state == "CONVERTED_GATE_SELECTOR_FRAMEWORK_BEHAVIOR"
    assert "sim_validator_parity_gate" in disposition.evidence_family
    assert "candidate_output_guard_parity" in disposition.runtime_surface
    assert "test_degenerate_candidate_is_demoted_before_l2_and_outcome" in (
        disposition.tests_verifier
    )
    assert "test_parse_fail_counted_as_raw_candidate" in disposition.tests_verifier


def test_apr24_session37_structural_dead_zone_unit_is_converted():
    disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/37_apr24_FRESH_SESSION_POST_THURSDAY_BATCH_F2_F3.md"
    )

    assert disposition.conversion_state == "CONVERTED_GATE_SELECTOR_FRAMEWORK_BEHAVIOR"
    assert "structural_detector_v2_dead_zone" in disposition.evidence_family
    assert "v2_dead_zone_divisor" in disposition.runtime_surface
    assert "market_state.v2_dead_zone_divisor" in disposition.next_code_config_test_action
    assert "test_dead_zone_divisor_changes_borderline_runtime_label" in (
        disposition.tests_verifier
    )
    assert "test_compute_market_state_threads_configured_v2_dead_zone_divisor" in (
        disposition.tests_verifier
    )


def test_apr25_session38_monthly_decay_unit_is_converted():
    disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/38_apr25_session_39_close_PHASE1_A1_A2_A3_S1_handoff.md"
    )

    assert disposition.conversion_state == "CONVERTED_RISK_SIZING_RULE"
    assert "monthly_decay" in disposition.evidence_family
    assert "contextual_side_risk_monthly_decay" in disposition.runtime_surface
    assert "v1/v2_shadow detector" in disposition.remaining_action
    assert "_score_monthly_decay_rules" in disposition.next_code_config_test_action
    assert "test_monthly_decay_alert_reduces_only_matching_detector_regime" in (
        disposition.tests_verifier
    )


def test_apr25_session39_long_wr_halt_unit_is_converted():
    disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/39_apr25_session_40_KICKOFF_MONDAY_DEPLOY_AND_POWERFUL_MACHINE_VISION.md"
    )

    assert disposition.conversion_state == "CONVERTED_GATE_SELECTOR_FRAMEWORK_BEHAVIOR"
    assert disposition.evidence_family == "apr25_session40_long_wr_halt_gate"
    assert disposition.runtime_surface == "sprt_class_halt_runtime_orchestrator_gate"
    assert "live LONG exits update" in disposition.remaining_action
    assert "sprt_class_halt_runtime.py" in disposition.next_code_config_test_action
    assert "test_orchestrator_gate_cancels_pending_and_blocks_when_active" in (
        disposition.tests_verifier
    )


def test_apr26_deferred_xau_anchor_corr_gate_unit_is_converted():
    disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/40_apr26_DEFERRED_CHANGES_MASTER.md"
    )

    assert disposition.conversion_state == "CONVERTED_AI_NARROWING_OR_AI_REMOVAL_RULE"
    assert "xau_anchor_correlation_gate" in disposition.evidence_family
    assert disposition.runtime_surface == (
        "cross_instrument_context_xau_anchor_corr_scoped_ai_guidance"
    )
    assert "format_cross_instrument_context" in disposition.next_code_config_test_action
    assert "test_config_market_symbol_blocks_omitted_candidate_symbol" in (
        disposition.tests_verifier
    )
    assert "test_us30_blocked_by_gate" in disposition.tests_verifier


def test_apr26_session40_canary_timeout_scaling_unit_is_converted():
    disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/40_apr26_session_40_CLOSE_FRESH_SESSION_KICKOFF.md"
    )

    assert disposition.conversion_state == "CONVERTED_GATE_SELECTOR_FRAMEWORK_BEHAVIOR"
    assert "canary_timeout_scaling" in disposition.evidence_family
    assert disposition.runtime_surface == "canary_fixture_count_scaled_runtime_timeout"
    assert "_derive_canary_subprocess_timeout_s" in (
        disposition.next_code_config_test_action
    )
    assert "test_run_canary_counts_manifest_for_timeout_scaling" in (
        disposition.tests_verifier
    )


def test_apr26_session41_pending_no_fill_notification_unit_is_converted():
    disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/41_apr26_session_41_CLOSE_RESEARCH_PROGRAM_HANDOFF.md"
    )

    assert disposition.conversion_state == "CONVERTED_NOFILL_PENDING_EXECUTION_BEHAVIOR"
    assert "persistent_telegram_pending_no_fill" in disposition.evidence_family
    assert disposition.runtime_surface == (
        "pending_limit_expiry_persistent_notification_queue"
    )
    assert "notify_limit_expired" in disposition.next_code_config_test_action
    assert "test_limit_expired_routes_high_priority_through_queue" in (
        disposition.tests_verifier
    )


def test_apr27_session42_equity_zero_daily_loss_guard_unit_is_converted():
    disposition = ledger.classify_artifact(
        ".context/02_session_handoffs/42_apr27_session_42_CLOSE_FN_GO_LIVE_HANDOFF.md"
    )

    assert disposition.conversion_state == "CONVERTED_GATE_SELECTOR_FRAMEWORK_BEHAVIOR"
    assert "equity_zero_daily_loss_guard" in disposition.evidence_family
    assert disposition.runtime_surface == "daily_loss_stop_safe_equity_read_guard"
    assert "safe_read_equity" in disposition.next_code_config_test_action
    assert "test_equity_zero_transient_does_not_trigger_daily_loss_stop" in (
        disposition.tests_verifier
    )
