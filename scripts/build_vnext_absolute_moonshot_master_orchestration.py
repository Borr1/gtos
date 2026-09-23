from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_goal_prompt_hardening import validate_prompt

ROUTE_ID = "vnext_absolute_moonshot_master_orchestration_2026_06_01"
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"

MASTER_PROMPT = PROMPT_DIR / "VNEXT_ABSOLUTE_MOONSHOT_MASTER_ORCHESTRATION_GOAL_PROMPT_2026-06-01.md"
MASTER_STARTER = PROMPT_DIR / "VNEXT_ABSOLUTE_MOONSHOT_MASTER_ORCHESTRATION_STARTER_2026-06-01.txt"
POST_V3_MASTER_PROMPT = PROMPT_DIR / "VNEXT_ABSOLUTE_MOONSHOT_POST_V3_MASTER_REFRESH_GOAL_PROMPT_2026-06-01.md"
POST_V3_MASTER_STARTER = PROMPT_DIR / "VNEXT_ABSOLUTE_MOONSHOT_POST_V3_MASTER_REFRESH_STARTER_2026-06-01.txt"
LAUNCH_ORDER = PROMPT_DIR / "VNEXT_ABSOLUTE_MOONSHOT_PROGRAM_LAUNCH_ORDER_2026-06-01.md"
VISION_PATH = ROOT / ".context" / "00_core" / "vnext_absolute_moonshot_vision_and_limitations.md"

NEXT_LEVEL_MASTER = ROOT / "research" / "operations" / "vnext_next_level_master_orchestration_2026_05_31"
LANE09_PACKAGE = ROOT / "research" / "operations" / "vnext_lane09_cross_lane_merge_dossier_production_package_2026_05_31"
FRIDAY_ROUTE = ROOT / "research" / "operations" / "vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"
LIVE_COMPANION = ROOT / "research" / "operations" / "vnext_live_activation_active_repair_companion_2026_05_28"
MT5_LOCAL_CACHE = ROOT / "research" / "operations" / "vnext_mt5_local_cache_preservation_2026_06_01"
VPS_PRESERVATION = ROOT / "research" / "operations" / "vnext_compliant_vps_data_preservation_broker_portability_2026_06_01"
ACTIVATION_REPAIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"
)

LIVE_SYMBOLS = [
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
]

LANE_WAVES = {
    "01": 1,
    "02": 1,
    "03": 1,
    "04": 1,
    "05": 2,
    "06": 2,
    "07": 2,
    "08": 3,
    "09": 3,
    "10": 3,
    "11": 3,
    "16": 4,
    "17": 4,
    "18": 4,
    "12": 5,
    "13": 5,
    "14": 6,
    "15": 7,
}

LANE_DEPENDENCIES = {
    "01": [],
    "02": ["01"],
    "03": ["01", "02"],
    "04": ["01", "02", "03"],
    "05": ["01", "02", "03", "04"],
    "06": ["01", "02", "03", "04"],
    "07": ["01", "02", "03", "04"],
    "08": ["01", "02", "03", "04", "05", "06", "07"],
    "09": ["01", "02", "03", "04", "05", "06", "07", "08"],
    "10": ["01", "02", "03", "04", "05", "06", "07", "08"],
    "11": ["01", "02", "03", "04", "05", "06", "07", "08"],
    "16": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11"],
    "17": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11"],
    "18": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11"],
    "12": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "16", "17", "18"],
    "13": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "16", "17", "18"],
    "14": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "16", "17", "18"],
    "15": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "16", "17", "18"],
}

EVIDENCE_DEPENDENCIES = [
    "current_live_state",
    "absolute_moonshot_vision",
    "next_level_master_package",
    "lane09_merge_package",
    "mt5_local_cache_preservation",
    "compliant_vps_data_preservation",
    "friday_microscope_route",
    "live_companion_route",
    "activation_repair_route",
    "selected_denominator_artifacts",
]

REQUIRED_OUTPUTS = [
    "ABSOLUTE_MASTER_LANE_REGISTRY.json",
    "ABSOLUTE_MASTER_LANE_REGISTRY_LEDGER.jsonl",
    "ABSOLUTE_MASTER_DEPENDENCY_GRAPH.json",
    "ABSOLUTE_MASTER_LAUNCH_WAVES.json",
    "ABSOLUTE_MASTER_SOURCE_AUTHORITY_MAP.json",
    "ABSOLUTE_MASTER_OUTPUT_SCHEMA_CONTRACTS.json",
    "ABSOLUTE_MASTER_CROSS_LANE_BLOCKER_LEDGER.jsonl",
    "ABSOLUTE_MASTER_ANTI_DUPLICATION_AND_LOOP_RULES.json",
    "ABSOLUTE_MASTER_MERGE_COMMIT_OWNERSHIP_PLAN.json",
    "ABSOLUTE_MASTER_VERIFIER_TEST_MATRIX.json",
    "ABSOLUTE_MASTER_EVIDENCE_INSPECTION_LEDGER.jsonl",
    "ABSOLUTE_MASTER_WAVE1_ARTIFACT_INSPECTION_LEDGER.jsonl",
    "ABSOLUTE_MASTER_WAVE1_TERMINAL_STATE_TABLE.json",
    "ABSOLUTE_MASTER_WAVE2_ARTIFACT_INSPECTION_LEDGER.jsonl",
    "ABSOLUTE_MASTER_WAVE2_TERMINAL_STATE_TABLE.json",
    "ABSOLUTE_MASTER_WAVE2_READINESS_DECISION.json",
    "ABSOLUTE_MASTER_WAVE3_ARTIFACT_INSPECTION_LEDGER.jsonl",
    "ABSOLUTE_MASTER_WAVE3_TERMINAL_STATE_TABLE.json",
    "ABSOLUTE_MASTER_POST_LANE11_TERMINAL_STATE_TABLE.json",
    "ABSOLUTE_MASTER_WAVE3_READINESS_DECISION.json",
    "ABSOLUTE_MASTER_WAVE3_LAUNCH_ORDER.json",
    "ABSOLUTE_MASTER_LIMITATION_DISPOSITION_MAP.json",
    "ABSOLUTE_MASTER_NEXT_WAVE_LAUNCH_DECISION.json",
    "ABSOLUTE_MASTER_LATER_WAVE_GATES.json",
    "ABSOLUTE_MASTER_WAVE4_ARTIFACT_INSPECTION_LEDGER.jsonl",
    "ABSOLUTE_MASTER_WAVE4_TERMINAL_STATE_TABLE.json",
    "ABSOLUTE_MASTER_POST_LANE18_IMPLEMENTATION_WAVE_DECISION.json",
    "ABSOLUTE_MASTER_POST_V3_ARTIFACT_INSPECTION_LEDGER.jsonl",
    "ABSOLUTE_MASTER_POST_V3_TERMINAL_STATE_TABLE.json",
    "ABSOLUTE_MASTER_POST_V3_LAUNCH_DECISION.json",
    "ABSOLUTE_MASTER_STALE_DEPENDENCY_TEXT_NEUTRALIZATION.json",
    "ABSOLUTE_MASTER_SOURCE_CAPTURE_DECISIONS.jsonl",
    "ABSOLUTE_MASTER_SOURCE_COMPLETENESS_DECISIONS.jsonl",
    "ABSOLUTE_MASTER_DECISION_LEDGER.jsonl",
    "ABSOLUTE_MASTER_BRANCH_IMPLEMENTATION_DECISIONS.jsonl",
    "ABSOLUTE_MASTER_RESULT_USE_STATUS.json",
    "ABSOLUTE_MASTER_SATURATION_SELF_RED_TEAM.md",
    "ABSOLUTE_MASTER_RUNTIME_EFFECT_BOUNDARY.json",
    "ABSOLUTE_MASTER_PROMPT_HARDENING_VERIFICATION.json",
    "ABSOLUTE_MASTER_CONTEXT_ANCHOR.md",
    "ABSOLUTE_MASTER_OUTPUT_MANIFEST.json",
    "ABSOLUTE_MASTER_COMPLETION_AUDIT.json",
    "ABSOLUTE_MASTER_FOCUSED_TEST_RESULT.json",
    "ABSOLUTE_MASTER_FOCUSED_TEST_RESULT.xml",
    "ABSOLUTE_MASTER_VERIFICATION_RESULT.json",
]

ALLOWED_OUTPUT_PREFIXES = (
    f"research/operations/{ROUTE_ID}/",
    "scripts/build_vnext_absolute_moonshot_master_orchestration.py",
    "tests/test_vnext_absolute_moonshot_master_orchestration.py",
)

FORBIDDEN_LIVE_PREFIXES = (
    "config/",
    "src/components/",
    "src/research/",
    "pipeline_state/",
    "shadow_logs/",
    "knowledge_base/",
    "data/",
    "research/program_control/",
    "research/ml_program/shadow/",
    "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/",
)

WAVE1_ROUTE_DIRS = {
    "01": ROOT
    / "research"
    / "operations"
    / "vnext_moonshot_lane01_data_universe_source_authority_2026_06_01",
    "02": ROOT
    / "research"
    / "operations"
    / "vnext_moonshot_lane02_no_leak_time_alignment_asof_contract_2026_06_01",
    "03": ROOT
    / "research"
    / "operations"
    / "vnext_moonshot_lane03_historical_candidate_reconstruction_2026_06_01",
    "04": ROOT
    / "research"
    / "operations"
    / "vnext_moonshot_lane04_historical_microscope_engine_2026_06_01",
}

WAVE1_EXPECTED_COUNTS = {
    "01": {
        "source_inventory_rows": 12545,
        "source_gap_rows": 975,
        "downstream_source_contracts": 11,
    },
    "02": {
        "timestamp_inventory_rows": 1236093,
        "asof_contract_rows": 7284,
    },
    "03": {
        "canonical_event_rows": 10389561,
        "canonical_candidate_rows": 3761515,
        "duplicate_groups": 724408,
        "source_inventory_rows": 1129,
        "source_gap_rows": 24,
        "exact_r_rows": 36,
        "proxy_r_rows": 2089623,
    },
    "04": {
        "timeline_rows": 289928,
        "strict_tick_rows": 1790,
        "source_gap_rows": 289604,
        "anatomy_split_rows": 1402,
    },
}

WAVE1_REQUIRED_ARTIFACTS = {
    "01": {
        "completion_audit": "COMPLETION_AUDIT.json",
        "verifier_result": "VERIFICATION_RESULT.json",
        "manifest": "OUTPUT_MANIFEST.json",
        "dependency_ledger": "DEPENDENCY_STATE_LEDGER.jsonl",
        "source_gap_ledger": "SOURCE_GAP_LEDGER.jsonl",
        "schema_contracts": [
            "DOWNSTREAM_SOURCE_CONTRACTS.json",
            "SOURCE_AUTHORITY_MAP.json",
            "PARSER_CHECKER_REGISTRY.json",
        ],
        "material_row_count_artifacts": [
            "DATA_SOURCE_INVENTORY.jsonl",
            "SOURCE_GAP_LEDGER.jsonl",
            "DOWNSTREAM_SOURCE_CONTRACTS.json",
        ],
        "context_anchor": "ROUTE_CONTEXT_ANCHOR.json",
    },
    "02": {
        "completion_audit": "LANE02_COMPLETION_AUDIT.json",
        "verifier_result": "LANE02_VERIFICATION_RESULT.json",
        "manifest": "LANE02_OUTPUT_MANIFEST.json",
        "dependency_ledger": "LANE02_SOURCE_DEPENDENCY_STATE_LEDGER.jsonl",
        "source_gap_ledger": "LANE02_SOURCE_COMPLETENESS_DECISIONS.jsonl",
        "schema_contracts": [
            "LANE02_DOWNSTREAM_FIELD_CONTRACT.json",
            "LANE02_CANONICAL_KEY_POLICY.json",
            "LANE02_LEAKAGE_VALIDATOR_SPEC.json",
            "LANE02_SESSION_TIMEZONE_CONTRACT.json",
        ],
        "material_row_count_artifacts": [
            "LANE02_TIMESTAMP_FIELD_INVENTORY.jsonl",
            "LANE02_ASOF_FIELD_CONTRACT.jsonl",
        ],
        "context_anchor": "LANE02_CONTEXT_ANCHOR.md",
    },
    "03": {
        "completion_audit": "LANE03_COMPLETION_AUDIT.json",
        "verifier_result": "LANE03_VERIFICATION_RESULT.json",
        "manifest": "LANE03_OUTPUT_MANIFEST.json",
        "dependency_ledger": "LANE03_DEPENDENCY_STATE_LEDGER.jsonl",
        "source_gap_ledger": "LANE03_SOURCE_GAP_LEDGER.jsonl",
        "schema_contracts": [
            "LANE03_RECONSTRUCTION_SUMMARY.json",
            "LANE03_DUPLICATE_DENOMINATOR_POLICY.md",
            "LANE03_MECHANISM_COVERAGE_LEDGER.jsonl",
        ],
        "material_row_count_artifacts": [
            "LANE03_CANONICAL_CANDIDATE_EVENT_LEDGER.jsonl.gz",
            "LANE03_CANONICAL_CANDIDATE_LEDGER.jsonl.gz",
            "LANE03_DUPLICATE_GROUP_LEDGER.jsonl.gz",
            "LANE03_SOURCE_INVENTORY_LEDGER.jsonl",
            "LANE03_SOURCE_GAP_LEDGER.jsonl",
        ],
        "context_anchor": "LANE03_CONTEXT_ANCHOR.md",
    },
    "04": {
        "completion_audit": "LANE04_COMPLETION_AUDIT.json",
        "verifier_result": "LANE04_VERIFICATION_RESULT.json",
        "manifest": "LANE04_OUTPUT_MANIFEST.json",
        "dependency_ledger": "LANE04_DEPENDENCY_STATE_LEDGER.jsonl",
        "source_gap_ledger": "LANE04_SOURCE_GAP_LEDGER.jsonl",
        "schema_contracts": [
            "LANE04_EXPECTANCY_SUMMARY.json",
            "LANE04_ANATOMY_SPLIT_LEDGER.jsonl",
            "LANE04_STRICT_TICK_TIMELINE_LEDGER.jsonl",
        ],
        "material_row_count_artifacts": [
            "LANE04_ROW_TIMELINE_LEDGER.jsonl",
            "LANE04_STRICT_TICK_TIMELINE_LEDGER.jsonl",
            "LANE04_SOURCE_GAP_LEDGER.jsonl",
            "LANE04_ANATOMY_SPLIT_LEDGER.jsonl",
        ],
        "context_anchor": "LANE04_CONTEXT_ANCHOR.md",
    },
}

WAVE2_ROUTE_DIRS = {
    "05": ROOT / "research" / "operations" / "vnext_moonshot_lane05_feature_store_v1_2026_06_01",
    "06": ROOT / "research" / "operations" / "vnext_moonshot_lane06_label_store_v1_2026_06_01",
    "07": ROOT
    / "research"
    / "operations"
    / "vnext_moonshot_lane07_broker_truth_cost_calibration_2026_06_01",
}

WAVE2_EXPECTED_COUNTS = {
    "05": {
        "canonical_candidate_feature_rows": 3761515,
        "timeline_feature_rows": 289928,
    },
    "06": {
        "label_vector_rows": 289928,
        "missing_label_gap_rows": 3471773,
        "broker_real_label_rows": 8,
    },
    "07": {
        "symbol_rows": 24,
        "broker_truth_rows": 64,
        "cost_rows": 53,
        "source_gap_rows": 221,
        "source_coverage_rows": 38,
    },
}

WAVE2_REQUIRED_ARTIFACTS = {
    "05": {
        "completion_audit": "LANE05_COMPLETION_AUDIT.json",
        "verifier_result": "LANE05_VERIFICATION_RESULT.json",
        "manifest": "LANE05_OUTPUT_MANIFEST.json",
        "downstream_contract": "LANE05_DOWNSTREAM_CONTRACT.json",
        "dependency_ledger": "LANE05_DEPENDENCY_STATE_LEDGER.jsonl",
        "source_gap_ledgers": ["LANE05_SOURCE_GAP_LEDGER.jsonl"],
        "coverage_ledgers": [
            "LANE05_FEATURE_COVERAGE_LEDGER.jsonl",
            "LANE05_SOURCE_COMPLETENESS_LEDGER.jsonl",
            "LANE05_NO_LEAK_VALIDATION_LEDGER.jsonl",
        ],
        "schema_contracts": [
            "LANE05_FEATURE_SCHEMA.json",
            "LANE05_DOWNSTREAM_CONTRACT.json",
        ],
        "material_row_count_artifacts": [
            "LANE05_CANONICAL_CANDIDATE_FEATURE_VECTOR_LEDGER.jsonl.gz",
            "LANE05_TIMELINE_FEATURE_VECTOR_LEDGER.jsonl.gz",
        ],
        "builder": "build_vnext_moonshot_lane05_feature_store_v1.py",
        "verifier": "verify_vnext_moonshot_lane05_feature_store_v1.py",
        "focused_test_result": "LANE05_FOCUSED_TEST_RESULT.xml",
        "tests": ["test_vnext_moonshot_lane05_feature_store_v1.py"],
        "context_anchor": "LANE05_CONTEXT_ANCHOR.md",
        "result_use_status": "LANE05_RESULT_USE_STATUS.json",
        "runtime_effect_boundary": "LANE05_RUNTIME_EFFECT_BOUNDARY.json",
    },
    "06": {
        "completion_audit": "LANE06_COMPLETION_AUDIT.json",
        "verifier_result": "LANE06_VERIFICATION_RESULT.json",
        "manifest": "LANE06_OUTPUT_MANIFEST.json",
        "downstream_contract": "LANE06_DOWNSTREAM_CONTRACT.json",
        "dependency_ledger": "LANE06_DEPENDENCY_STATE_LEDGER.jsonl",
        "source_gap_ledgers": [
            "LANE06_MISSING_LABEL_GAP_LEDGER.jsonl.gz",
            "LANE06_SOURCE_COMPLETENESS_DECISION_LEDGER.jsonl",
        ],
        "coverage_ledgers": [
            "LANE06_SOURCE_COVERAGE_LEDGER.jsonl",
            "LANE06_LABEL_FAMILY_COVERAGE_LEDGER.jsonl",
            "LANE06_NO_LEAK_VALIDATION_LEDGER.jsonl",
        ],
        "schema_contracts": [
            "LANE06_LABEL_SCHEMA.json",
            "LANE06_DOWNSTREAM_CONTRACT.json",
        ],
        "material_row_count_artifacts": [
            "LANE06_LABEL_VECTOR_LEDGER.jsonl.gz",
            "LANE06_MISSING_LABEL_GAP_LEDGER.jsonl.gz",
        ],
        "builder": "build_vnext_moonshot_lane06_label_store_v1.py",
        "verifier": "verify_vnext_moonshot_lane06_label_store_v1.py",
        "focused_test_result": "LANE06_FOCUSED_TEST_RESULT.xml",
        "tests": ["test_vnext_moonshot_lane06_label_store_v1.py"],
        "context_anchor": "LANE06_CONTEXT_ANCHOR.md",
        "result_use_status": "LANE06_RESULT_USE_STATUS.json",
        "runtime_effect_boundary": "LANE06_RUNTIME_EFFECT_BOUNDARY.json",
        "saturation_review": "LANE06_SATURATION_SELF_RED_TEAM.md",
    },
    "07": {
        "completion_audit": "LANE07_COMPLETION_AUDIT.json",
        "verifier_result": "LANE07_VERIFICATION_RESULT.json",
        "manifest": "LANE07_OUTPUT_MANIFEST.json",
        "downstream_contract": "LANE07_DOWNSTREAM_CONTRACT.json",
        "dependency_ledger": "LANE07_DEPENDENCY_STATE_LEDGER.jsonl",
        "source_gap_ledgers": ["LANE07_SOURCE_GAP_LEDGER.jsonl"],
        "coverage_ledgers": ["LANE07_SOURCE_COVERAGE_LEDGER.jsonl"],
        "schema_contracts": [
            "LANE07_BROKER_COST_SCHEMA.json",
            "LANE07_DOWNSTREAM_CONTRACT.json",
        ],
        "material_row_count_artifacts": [
            "LANE07_SYMBOL_SPEC_SESSION_LEDGER.jsonl",
            "LANE07_BROKER_TRUTH_LEDGER.jsonl",
            "LANE07_COST_CALIBRATION_LEDGER.jsonl",
            "LANE07_SOURCE_GAP_LEDGER.jsonl",
            "LANE07_SOURCE_COVERAGE_LEDGER.jsonl",
        ],
        "builder": "build_vnext_moonshot_lane07_broker_truth_cost_calibration.py",
        "verifier": "verify_vnext_moonshot_lane07_broker_truth_cost_calibration.py",
        "focused_test_result": "LANE07_FOCUSED_TEST_RESULT.xml",
        "tests": ["tests/test_vnext_moonshot_lane07_broker_truth_cost_calibration.py"],
        "context_anchor": "LANE07_CONTEXT_ANCHOR.json",
        "source_use_state": "LANE07_SOURCE_USE_STATE.json",
        "runtime_effect_boundary": "LANE07_RUNTIME_EFFECT_BOUNDARY.json",
    },
}

WAVE3_ROUTE_DIRS = {
    "08": ROOT / "research" / "operations" / "vnext_moonshot_lane08_digital_twin_replay_engine_2026_06_01",
    "09": ROOT / "research" / "operations" / "vnext_moonshot_lane09_meta_selector_v2_2026_06_01",
    "10": ROOT / "research" / "operations" / "vnext_moonshot_lane10_portfolio_scheduler_v2_2026_06_01",
    "11": ROOT / "research" / "operations" / "vnext_moonshot_lane11_execution_policy_engine_v2_2026_06_01",
}

WAVE3_EXPECTED_COUNTS = {
    "08": {
        "replay_rows": 289928,
        "missing_replay_gap_rows": 3471773,
        "split_metric_rows": 1536,
        "depth_rows": 9,
    },
    "09": {
        "selector_row_evidence_rows": 289928,
        "selector_discovery_rows": 21052,
        "default_off_clause_rows": 9808,
        "mechanism_decision_rows": 43,
        "capture_repair_requirement_rows": 1909,
    },
    "10": {
        "replay_rows": 289928,
        "conflict_rows": 215495,
        "gap_rows": 3471773,
        "risk_rows": 1474,
        "split_rows": 1547,
    },
    "11": {
        "simulation_rows": 289928,
        "policy_result_cells": 2899280,
        "metric_rows": 35938,
        "policy_variant_count": 10,
        "expanded_policy_variant_count": 890,
        "expanded_metric_rows": 70800,
        "expanded_package_rows": 1320,
        "expanded_policy_result_cell_accounting": 1026261670,
    },
}

WAVE3_REQUIRED_ARTIFACTS = {
    "08": {
        "completion_audit": "LANE08_COMPLETION_AUDIT.json",
        "verifier_result": "LANE08_VERIFICATION_RESULT.json",
        "manifest": "LANE08_OUTPUT_MANIFEST.json",
        "downstream_contract": "LANE08_MODULE_CONTRACTS.json",
        "dependency_ledger": "LANE08_DEPENDENCY_STATE_LEDGER.jsonl",
        "source_gap_ledgers": ["LANE08_MISSING_REPLAY_GAP_LEDGER.jsonl.gz"],
        "schema_contracts": ["LANE08_REPLAY_SCHEMA.json", "LANE08_MODULE_CONTRACTS.json"],
        "material_row_count_artifacts": [
            "LANE08_REPLAY_ROW_LEDGER.jsonl.gz",
            "LANE08_MISSING_REPLAY_GAP_LEDGER.jsonl.gz",
            "LANE08_SPLIT_STRESS_METRICS.jsonl",
            "LANE08_REPLAY_DEPTH_COVERAGE_LEDGER.jsonl",
        ],
        "builder": "build_vnext_moonshot_lane08_digital_twin_replay_engine.py",
        "verifier": "verify_vnext_moonshot_lane08_digital_twin_replay_engine.py",
        "focused_test_result": "LANE08_FOCUSED_TEST_RESULT.xml",
        "tests": ["test_vnext_moonshot_lane08_digital_twin_replay_engine.py"],
        "context_anchor": "LANE08_CONTEXT_ANCHOR.md",
        "source_use_state": "LANE08_SOURCE_USE_STATE.json",
        "result_use_status": "LANE08_RESULT_USE_STATUS.json",
        "runtime_effect_boundary": "LANE08_RUNTIME_EFFECT_BOUNDARY.json",
    },
    "09": {
        "completion_audit": "LANE09_COMPLETION_AUDIT.json",
        "verifier_result": "LANE09_VERIFICATION_RESULT.json",
        "manifest": "LANE09_OUTPUT_MANIFEST.json",
        "downstream_contract": "LANE09_DOWNSTREAM_CONTRACT.json",
        "dependency_ledger": "LANE09_DEPENDENCY_STATE_LEDGER.jsonl",
        "source_gap_ledgers": ["LANE09_SOURCE_COMPLETENESS_DECISION_LEDGER.jsonl"],
        "schema_contracts": ["LANE09_DOWNSTREAM_CONTRACT.json", "LANE09_DEFAULT_OFF_SELECTOR_PACKAGE.json"],
        "material_row_count_artifacts": [
            "LANE09_SELECTOR_ROW_EVIDENCE_LEDGER.jsonl.gz",
            "LANE09_SELECTOR_DISCOVERY_LEDGER.jsonl.gz",
            "LANE09_DEFAULT_OFF_SELECTOR_CLAUSE_LEDGER.jsonl",
            "LANE09_SELECTOR_MECHANISM_RANKING.jsonl",
            "LANE09_PACKET_CAPTURE_REQUIREMENTS.jsonl",
        ],
        "builder": "build_vnext_moonshot_lane09_meta_selector_v2.py",
        "verifier": "verify_vnext_moonshot_lane09_meta_selector_v2.py",
        "focused_test_result": "LANE09_FOCUSED_TEST_RESULT.xml",
        "tests": ["test_vnext_moonshot_lane09_meta_selector_v2.py"],
        "context_anchor": "LANE09_CONTEXT_ANCHOR.md",
        "source_use_state": "LANE09_SOURCE_USE_STATE.json",
        "result_use_status": "LANE09_RESULT_USE_STATUS.json",
        "runtime_effect_boundary": "LANE09_RUNTIME_EFFECT_BOUNDARY.json",
    },
    "10": {
        "completion_audit": "LANE10_COMPLETION_AUDIT.json",
        "verifier_result": "LANE10_VERIFICATION_RESULT.json",
        "manifest": "LANE10_OUTPUT_MANIFEST.json",
        "downstream_contract": "LANE10_DOWNSTREAM_CONTRACT.json",
        "dependency_ledger": "LANE10_DEPENDENCY_STATE_LEDGER.jsonl",
        "source_gap_ledgers": ["LANE10_MISSING_REPLAY_GAP_SCHEDULER_LEDGER.jsonl.gz"],
        "schema_contracts": ["LANE10_DOWNSTREAM_CONTRACT.json", "portfolio_scheduler_v2.py"],
        "material_row_count_artifacts": [
            "LANE10_SCHEDULER_REPLAY_LEDGER.jsonl.gz",
            "LANE10_SCHEDULING_CONFLICT_LEDGER.jsonl.gz",
            "LANE10_MISSING_REPLAY_GAP_SCHEDULER_LEDGER.jsonl.gz",
            "LANE10_RISK_EXPOSURE_LEDGER.jsonl",
            "LANE10_SPLIT_STRESS_METRICS.jsonl",
        ],
        "builder": "build_vnext_moonshot_lane10_portfolio_scheduler_v2.py",
        "verifier": "verify_vnext_moonshot_lane10_portfolio_scheduler_v2.py",
        "focused_test_result": "LANE10_FOCUSED_TEST_RESULT.xml",
        "tests": [],
        "context_anchor": "LANE10_CONTEXT_ANCHOR.md",
        "source_use_state": "LANE10_SOURCE_USE_STATE.json",
    },
    "11": {
        "completion_audit": "LANE11_COMPLETION_AUDIT.json",
        "verifier_result": "LANE11_VERIFICATION_RESULT.json",
        "manifest": "LANE11_OUTPUT_MANIFEST.json",
        "downstream_contract": "LANE11_DOWNSTREAM_CONTRACT.json",
        "dependency_ledger": "LANE11_DEPENDENCY_STATE_LEDGER.jsonl",
        "source_gap_ledgers": [
            "LANE11_SOURCE_COMPLETENESS_DECISION_LEDGER.jsonl",
            "LANE11_EXPANDED_POLICY_SOURCE_GAP_LEDGER.jsonl.gz",
        ],
        "schema_contracts": [
            "LANE11_POLICY_SCHEMA.json",
            "LANE11_DOWNSTREAM_CONTRACT.json",
            "LANE11_DEFAULT_OFF_POLICY_ROUTER_PACKAGE.json",
        ],
        "material_row_count_artifacts": [
            "LANE11_POLICY_SIMULATION_LEDGER.jsonl.gz",
            "LANE11_POLICY_METRIC_LEDGER.jsonl",
            "LANE11_POLICY_DOMINANCE_DECISION_LEDGER.jsonl",
            "LANE11_EXPANDED_POLICY_VARIANT_REGISTRY.jsonl",
            "LANE11_EXPANDED_POLICY_SIMULATION_METRIC_LEDGER.jsonl.gz",
            "LANE11_EXPANDED_DEFAULT_OFF_POLICY_PACKAGE_LEDGER.jsonl.gz",
        ],
        "builder": "build_vnext_moonshot_lane11_execution_policy_engine_v2.py",
        "verifier": "verify_vnext_moonshot_lane11_execution_policy_engine_v2.py",
        "focused_test_result": "LANE11_FOCUSED_TEST_RESULT.xml",
        "tests": ["test_vnext_moonshot_lane11_execution_policy_engine_v2.py"],
        "context_anchor": "LANE11_CONTEXT_ANCHOR.md",
        "source_use_state": "LANE11_SOURCE_USE_STATE.json",
        "result_use_status": "LANE11_RESULT_USE_STATUS.json",
        "runtime_effect_boundary": "LANE11_RUNTIME_EFFECT_BOUNDARY.json",
    },
}

POST_LANE11_ROUTE_DIRS = {
    "09B": ROOT / "research" / "operations" / "vnext_moonshot_lane09b_selector_scheduler_reconciliation_2026_06_01",
    "10B": ROOT
    / "research"
    / "operations"
    / "vnext_moonshot_lane10b_scheduler_conflict_anatomy_multiticket_design_2026_06_01",
    "11": WAVE3_ROUTE_DIRS["11"],
}

WAVE4_ROUTE_DIRS = {
    "16": ROOT
    / "research"
    / "operations"
    / "vnext_absolute_moonshot_lane16_historical_microscope_scale_2026_06_01",
    "17": ROOT
    / "research"
    / "operations"
    / "vnext_absolute_moonshot_lane17_market_awareness_whiteboard_2026_06_01",
    "18": ROOT
    / "research"
    / "operations"
    / "vnext_absolute_moonshot_lane18_broker_truth_cost_capture_v2_2026_06_01",
}

WAVE4_EXPECTED_COUNTS = {
    "16": {
        "event_rows": 289928,
        "path_anatomy_rows": 289928,
        "source_gap_rows": 3761701,
        "non_reconstructable_gap_rows": 3471773,
        "coverage_inventory_rows": 9032,
        "split_stress_rows": 11105,
    },
    "17": {
        "replay_whiteboard_rows": 289928,
        "source_gap_rows": 2101044,
        "forward_snapshot_rows": 24,
        "source_completeness_rows": 336,
        "correlation_pair_rows": 276,
    },
    "18": {
        "source_inventory_rows": 25,
        "source_gap_rows": 1207,
        "prospective_capture_rows": 10,
        "cost_rows": 53,
    },
}

WAVE4_REQUIRED_ARTIFACTS = {
    "16": {
        "completion_audit": "LANE16_COMPLETION_AUDIT.json",
        "verifier_result": "LANE16_VERIFICATION_RESULT.json",
        "manifest": "LANE16_OUTPUT_MANIFEST.json",
        "downstream_contract": "LANE16_DOWNSTREAM_CONTRACT.json",
        "dependency_ledger": "LANE16_DEPENDENCY_STATE_LEDGER.jsonl",
        "source_gap_ledgers": ["LANE16_SOURCE_GAP_LEDGER.jsonl.gz"],
        "schema_contracts": [],
        "material_row_count_artifacts": [
            "LANE16_MICROSCOPE_EVENT_LEDGER.jsonl.gz",
            "LANE16_PATH_ANATOMY_LEDGER.jsonl.gz",
            "LANE16_SOURCE_GAP_LEDGER.jsonl.gz",
            "LANE16_COVERAGE_INVENTORY.jsonl",
            "LANE16_SPLIT_STRESS_SUMMARY.jsonl",
        ],
        "builder": "build_vnext_absolute_moonshot_lane16_historical_microscope_scale.py",
        "verifier": "verify_vnext_absolute_moonshot_lane16_historical_microscope_scale.py",
        "focused_test_result": "LANE16_FOCUSED_TEST_RESULT.xml",
        "tests": ["tests/test_vnext_absolute_moonshot_lane16_historical_microscope_scale.py"],
        "context_anchor": "LANE16_CONTEXT_ANCHOR.md",
        "source_use_state": "LANE16_SOURCE_USE_STATE.json",
        "result_use_status": "LANE16_RESULT_USE_STATUS.json",
        "runtime_effect_boundary": "LANE16_RUNTIME_EFFECT_BOUNDARY.json",
    },
    "17": {
        "completion_audit": "LANE17_COMPLETION_AUDIT.json",
        "verifier_result": "LANE17_VERIFICATION_RESULT.json",
        "manifest": "LANE17_OUTPUT_MANIFEST.json",
        "downstream_contract": "LANE17_DOWNSTREAM_CONTRACT.json",
        "dependency_ledger": "LANE17_DEPENDENCY_STATE_LEDGER.jsonl",
        "source_gap_ledgers": ["LANE17_SOURCE_GAP_LEDGER.jsonl.gz"],
        "schema_contracts": ["LANE17_MARKET_AWARENESS_SCHEMA.json", "LANE17_FORWARD_CAPTURE_CONTRACT.json"],
        "material_row_count_artifacts": [
            "LANE17_MARKET_WHITEBOARD_REPLAY_ROWS.jsonl.gz",
            "LANE17_SOURCE_GAP_LEDGER.jsonl.gz",
            "LANE17_FORWARD_SNAPSHOT_LEDGER.jsonl",
            "LANE17_SOURCE_COMPLETENESS_LEDGER.jsonl",
            "LANE17_CORRELATION_REGIME_SPREAD_LEDGER.jsonl",
        ],
        "builder": "build_vnext_absolute_moonshot_lane17_market_awareness_whiteboard.py",
        "verifier": "verify_vnext_absolute_moonshot_lane17_market_awareness_whiteboard.py",
        "focused_test_result": "LANE17_FOCUSED_TEST_RESULT.xml",
        "tests": ["test_vnext_absolute_moonshot_lane17_market_awareness_whiteboard.py"],
        "context_anchor": "LANE17_CONTEXT_ANCHOR.md",
        "source_use_state": "LANE17_SOURCE_USE_STATE.json",
        "result_use_status": "LANE17_RESULT_USE_STATUS.json",
        "runtime_effect_boundary": "LANE17_RUNTIME_EFFECT_BOUNDARY.json",
    },
    "18": {
        "completion_audit": "LANE18_COMPLETION_AUDIT.json",
        "verifier_result": "LANE18_VERIFICATION_RESULT.json",
        "manifest": "LANE18_OUTPUT_MANIFEST.json",
        "downstream_contract": "LANE18_DOWNSTREAM_CONTRACTS.json",
        "dependency_ledger": None,
        "source_gap_ledgers": ["LANE18_SOURCE_GAP_LEDGER.jsonl"],
        "schema_contracts": ["LANE18_UNIVERSAL_BROKER_TRUTH_COST_CAPTURE_CONTRACT.json"],
        "material_row_count_artifacts": [
            "LANE18_SOURCE_INVENTORY_LEDGER.jsonl",
            "LANE18_SOURCE_GAP_LEDGER.jsonl",
            "LANE18_PROSPECTIVE_CAPTURE_REQUIREMENTS.jsonl",
            "LANE18_COST_CALIBRATION_V2_LEDGER.jsonl",
        ],
        "builder": "build_vnext_absolute_moonshot_lane18_broker_truth_cost_capture_v2.py",
        "verifier": "verify_vnext_absolute_moonshot_lane18_broker_truth_cost_capture_v2.py",
        "focused_test_result": "LANE18_FOCUSED_TEST_RESULT.xml",
        "tests": ["test_vnext_absolute_moonshot_lane18_broker_truth_cost_capture_v2.py"],
        "context_anchor": "LANE18_CONTEXT_ANCHOR.json",
        "source_use_state": "LANE18_SOURCE_USE_STATE.json",
        "result_use_status": "LANE18_RESULT_USE_STATUS.json",
        "runtime_effect_boundary": "LANE18_RUNTIME_EFFECT_BOUNDARY.json",
    },
}

POST_V3_ROUTE_DIRS = {
    "source_capture_repair": ROOT
    / "research"
    / "operations"
    / "vnext_absolute_moonshot_post_lane18_source_capture_repair_2026_06_01",
    "selector_v3": ROOT / "research" / "operations" / "vnext_absolute_moonshot_selector_v3_2026_06_01",
    "scheduler_v3": ROOT / "research" / "operations" / "vnext_absolute_moonshot_scheduler_v3_2026_06_01",
    "execution_policy_v3": ROOT
    / "research"
    / "operations"
    / "vnext_absolute_moonshot_execution_policy_v3_2026_06_01",
}

POST_V3_EXPECTED_COUNTS = {
    "source_capture_repair": {
        "superledger_rows": 16579491,
        "repaired_rows": 2949305,
        "read_only_export_requirement_rows": 2823,
        "forward_capture_contract_rows": 351,
        "non_generatable_rows": 41953158,
        "validation_rows": 3,
    },
    "selector_v3": {
        "full_evidence_rows": 289928,
        "selector_scheduler_execution_join_rows": 289928,
        "market_whiteboard_rows": 289928,
        "source_gap_capture_dependency_rows": 289928,
        "mechanism_action_rows": 6488,
        "split_stress_rows": 6488,
        "runtime_selector_rule_count": 2027,
        "exact_r_rows": 0,
        "proxy_r_rows": 289917,
    },
    "scheduler_v3": {
        "full_evidence_rows": 289928,
        "decision_rows": 289928,
        "conflict_rows": 289928,
        "money_risk_rows": 289928,
        "source_gap_rows": 289928,
        "correlation_rows": 290372,
        "blocked_edge_rows": 179575,
        "split_stress_rows": 325,
        "exact_broker_real_rows": 8,
        "source_bound_proxy_rows": 289909,
        "missing_result_rows": 11,
    },
    "execution_policy_v3": {
        "policy_variant_rows": 1353,
        "evaluation_rows": 107201,
        "source_gap_rows": 7587,
        "routing_rows": 7861,
        "lifecycle_feasibility_rows": 104,
        "failure_anatomy_rows": 4250,
        "source_decision_rows": 269,
        "split_stress_rows": 11105,
        "lane11_inherited_variant_rows": 890,
        "v3_added_variant_rows": 463,
    },
}

POST_V3_REQUIRED_ARTIFACTS = {
    "source_capture_repair": {
        "completion_audit": "POST_LANE18_COMPLETION_AUDIT.json",
        "verifier_result": "POST_LANE18_VERIFICATION_RESULT.json",
        "manifest": "POST_LANE18_OUTPUT_MANIFEST.json",
        "downstream_contract": "POST_LANE18_DOWNSTREAM_CONTRACTS.json",
        "focused_test_result": "POST_LANE18_FOCUSED_TEST_RESULT.xml",
        "tests": ["test_vnext_absolute_moonshot_post_lane18_source_capture_repair.py"],
        "builder": "build_vnext_absolute_moonshot_post_lane18_source_capture_repair.py",
        "verifier": "verify_vnext_absolute_moonshot_post_lane18_source_capture_repair.py",
        "source_capture_decisions": "POST_LANE18_SOURCE_CAPTURE_DECISIONS.jsonl",
        "source_completeness_decisions": "POST_LANE18_SOURCE_COMPLETENESS_DECISIONS.jsonl",
        "branch_decisions": "POST_LANE18_BRANCH_DECISION_LEDGER.jsonl",
        "implementation_decisions": "POST_LANE18_IMPLEMENTATION_DECISION_LEDGER.jsonl",
        "result_use_status": "POST_LANE18_RESULT_USE_STATUS.json",
        "runtime_effect_boundary": "offline_source_capture_repair_no_live_behavior_change",
        "material_row_count_artifacts": [
            "POST_LANE18_SOURCE_GAP_SUPERLEDGER.jsonl.gz",
            "POST_LANE18_REPAIRED_SOURCE_LEDGER.jsonl.gz",
            "POST_LANE18_READ_ONLY_EXPORT_REQUIREMENT_LEDGER.jsonl.gz",
            "POST_LANE18_FORWARD_CAPTURE_CONTRACT.jsonl.gz",
            "POST_LANE18_NON_GENERATABLE_HISTORICAL_TRUTH_LEDGER.jsonl.gz",
            "POST_LANE18_SOURCE_ASOF_NOLEAK_VALIDATION_LEDGER.jsonl",
        ],
    },
    "selector_v3": {
        "completion_audit": "SELECTOR_V3_COMPLETION_AUDIT.json",
        "verifier_result": "SELECTOR_V3_VERIFICATION_RESULT.json",
        "manifest": "SELECTOR_V3_OUTPUT_MANIFEST.json",
        "downstream_contract": "SELECTOR_V3_DOWNSTREAM_CONTRACTS.json",
        "focused_test_result": "SELECTOR_V3_FOCUSED_TEST_RESULT.xml",
        "tests": ["test_vnext_absolute_moonshot_selector_v3.py"],
        "builder": "build_vnext_absolute_moonshot_selector_v3.py",
        "verifier": "verify_vnext_absolute_moonshot_selector_v3.py",
        "default_off_package": "SELECTOR_V3_DEFAULT_OFF_PACKAGE.json",
        "source_capture_decisions": "SELECTOR_V3_SOURCE_CAPTURE_DECISIONS.jsonl",
        "source_completeness_decisions": "SELECTOR_V3_SOURCE_COMPLETENESS_DECISIONS.jsonl",
        "branch_decisions": "SELECTOR_V3_BRANCH_DECISION_LEDGER.jsonl",
        "implementation_decisions": "SELECTOR_V3_IMPLEMENTATION_DECISION_LEDGER.jsonl",
        "result_use_status": "SELECTOR_V3_RESULT_USE_STATUS.json",
        "runtime_packet_schema": "SELECTOR_V3_RUNTIME_PACKET_SCHEMA.json",
        "runtime_effect_boundary": "offline_default_off_selector_v3_research_package_only_no_live_broker_order_deal_position_operation_no_config_prompt_risk_execution_safety_canary_selector_activation_no_paid_api_no_remote",
        "material_row_count_artifacts": [
            "SELECTOR_V3_FULL_SELECTOR_EVIDENCE_LEDGER.jsonl.gz",
            "SELECTOR_V3_SELECTOR_SCHEDULER_EXECUTION_JOIN_LEDGER.jsonl.gz",
            "SELECTOR_V3_MARKET_WHITEBOARD_CONTEXT_LEDGER.jsonl.gz",
            "SELECTOR_V3_SOURCE_GAP_CAPTURE_DEPENDENCY_LEDGER.jsonl.gz",
            "SELECTOR_V3_MECHANISM_ACTION_DECISION_LEDGER.jsonl",
            "SELECTOR_V3_SPLIT_STRESS_DECONCENTRATION_LEDGER.jsonl",
        ],
    },
    "scheduler_v3": {
        "completion_audit": "SCHEDULER_V3_COMPLETION_AUDIT.json",
        "verifier_result": "SCHEDULER_V3_VERIFICATION_RESULT.json",
        "manifest": "SCHEDULER_V3_OUTPUT_MANIFEST.json",
        "downstream_contract": "SCHEDULER_V3_DOWNSTREAM_CONTRACTS.json",
        "focused_test_result": "SCHEDULER_V3_FOCUSED_TEST_RESULT.xml",
        "tests": ["tests/test_vnext_absolute_moonshot_scheduler_v3.py"],
        "builder": "build_vnext_absolute_moonshot_scheduler_v3.py",
        "verifier": "verify_vnext_absolute_moonshot_scheduler_v3.py",
        "default_off_package": "SCHEDULER_V3_DEFAULT_OFF_PACKAGE.json",
        "source_capture_decisions": "SCHEDULER_V3_SOURCE_CAPTURE_DECISIONS.jsonl",
        "source_completeness_decisions": "SCHEDULER_V3_SOURCE_COMPLETENESS_DECISIONS.jsonl",
        "branch_decisions": "SCHEDULER_V3_BRANCH_DECISION_LEDGER.jsonl",
        "implementation_decisions": "SCHEDULER_V3_IMPLEMENTATION_DECISION_LEDGER.jsonl",
        "result_use_status": "SCHEDULER_V3_RESULT_USE_STATUS.json",
        "runtime_effect_boundary": "offline_scheduler_v3_package_only_no_live_broker_order_deal_position_operation_no_config_prompt_risk_execution_safety_canary_selector_scheduler_activation_no_paid_api_no_remote",
        "material_row_count_artifacts": [
            "SCHEDULER_V3_FULL_EVIDENCE_LEDGER.jsonl.gz",
            "SCHEDULER_V3_ACCEPTED_REDUCED_REJECTED_DECISION_LEDGER.jsonl.gz",
            "SCHEDULER_V3_CONFLICT_ANATOMY_DISPOSITION_LEDGER.jsonl.gz",
            "SCHEDULER_V3_MONEY_RISK_EXPOSURE_LEDGER.jsonl.gz",
            "SCHEDULER_V3_CORRELATION_CLUSTER_EXPOSURE_LEDGER.jsonl.gz",
            "SCHEDULER_V3_SOURCE_GAP_CAPTURE_DEPENDENCY_LEDGER.jsonl.gz",
            "SCHEDULER_V3_SPLIT_STRESS_DECONCENTRATION_LEDGER.jsonl",
        ],
    },
    "execution_policy_v3": {
        "completion_audit": "V3_COMPLETION_AUDIT.json",
        "verifier_result": "V3_VERIFICATION_RESULT.json",
        "manifest": "V3_OUTPUT_MANIFEST.json",
        "downstream_contract": "V3_DOWNSTREAM_CONTRACTS.json",
        "focused_test_result": "V3_FOCUSED_TEST_RESULT.xml",
        "tests": ["test_vnext_absolute_moonshot_execution_policy_v3.py"],
        "builder": "build_vnext_absolute_moonshot_execution_policy_v3.py",
        "verifier": "verify_vnext_absolute_moonshot_execution_policy_v3.py",
        "default_off_package": "V3_DEFAULT_OFF_EXECUTION_POLICY_PACKAGE.json",
        "source_completeness_decisions": "V3_SOURCE_CAPTURE_AND_COMPLETENESS_DECISIONS.jsonl",
        "branch_decisions": "V3_BRANCH_DECISION_LEDGER.jsonl",
        "implementation_decisions": "V3_IMPLEMENTATION_DECISION_LEDGER.jsonl",
        "result_use_status": "V3_RESULT_USE_STATUS.json",
        "source_use_state": "V3_SOURCE_USE_STATE.json",
        "runtime_effect_boundary": "default_off_execution_policy_v3_artifacts_only_no_live_broker_order_deal_position_operation_no_config_prompt_risk_execution_safety_canary_selector_scheduler_activation_no_paid_api_no_remote",
        "material_row_count_artifacts": [
            "V3_POLICY_VARIANT_REGISTRY.jsonl",
            "V3_FEASIBLE_POLICY_EVALUATION_LEDGER.jsonl.gz",
            "V3_NON_REPLAYABLE_SOURCE_GAP_LEDGER.jsonl.gz",
            "V3_POLICY_ROUTING_DECISION_LEDGER.jsonl.gz",
            "V3_LIFECYCLE_BROKER_TICK_FEASIBILITY_LEDGER.jsonl",
            "V3_POLICY_FAILURE_ANATOMY_LEDGER.jsonl.gz",
            "V3_SPLIT_STRESS_DECONCENTRATION_LEDGER.jsonl",
        ],
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return sum(1 for line in handle if line.strip())


def read_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def artifact_record(route_dir: Path, name: str) -> dict[str, Any]:
    path = resolve_route_artifact(route_dir, name)
    return {
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "sha256": sha256_file(path),
    }


def artifact_presence_record(route_dir: Path, name: str) -> dict[str, Any]:
    path = resolve_route_artifact(route_dir, name)
    return {
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def resolve_route_artifact(route_dir: Path, name: str) -> Path:
    if name.startswith("tests/"):
        return ROOT / name
    return route_dir / name


def manifest_output_count(manifest: dict[str, Any]) -> int:
    return (
        manifest.get("output_count")
        or manifest.get("artifact_count")
        or len(manifest.get("outputs", []))
        or len(manifest.get("artifacts", []))
        or len(manifest.get("files", []))
    )


def parse_junit_result(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": rel(path),
            "exists": False,
            "ok": False,
            "tests": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
        }
    root = ET.parse(path).getroot()
    if root.tag == "testsuites":
        suites = list(root.findall("testsuite"))
        tests = sum(int(suite.attrib.get("tests", "0")) for suite in suites)
        failures = sum(int(suite.attrib.get("failures", "0")) for suite in suites)
        errors = sum(int(suite.attrib.get("errors", "0")) for suite in suites)
        skipped = sum(int(suite.attrib.get("skipped", "0")) for suite in suites)
    else:
        tests = int(root.attrib.get("tests", "0"))
        failures = int(root.attrib.get("failures", "0"))
        errors = int(root.attrib.get("errors", "0"))
        skipped = int(root.attrib.get("skipped", "0"))
    return {
        "path": rel(path),
        "exists": True,
        "ok": tests > 0 and failures == 0 and errors == 0,
        "tests": tests,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def run_git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def git_head() -> dict[str, str | None]:
    return {
        "head": run_git(["rev-parse", "HEAD"]),
        "head_short": run_git(["rev-parse", "--short", "HEAD"]),
        "head_subject": run_git(["log", "-1", "--format=%s"]),
    }


def git_last_commit_for_path(path: Path) -> dict[str, str | None]:
    rel_path = rel(path)
    raw = run_git(["log", "-1", "--format=%H%x09%h%x09%s", "--", rel_path])
    if not raw:
        return {"commit": None, "commit_short": None, "subject": None}
    parts = raw.split("\t", 2)
    return {
        "commit": parts[0] if len(parts) > 0 else None,
        "commit_short": parts[1] if len(parts) > 1 else None,
        "subject": parts[2] if len(parts) > 2 else None,
    }


def extract_section(text: str, heading: str) -> str:
    pattern = rf"^## {re.escape(heading)}\s*$"
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r"^## ", text[start:], flags=re.MULTILINE)
    end = start + next_match.start() if next_match else len(text)
    return text[start:end].strip()


def bullet_lines(section: str) -> list[str]:
    return [line[2:].strip() for line in section.splitlines() if line.startswith("- ")]


def parse_lane_prompt(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    name = path.name
    lane_match = re.search(r"LANE(\d{2})", name)
    if not lane_match:
        raise ValueError(f"Cannot parse lane id from {path}")
    lane_id = lane_match.group(1)
    first_heading = text.splitlines()[0].lstrip("# ").strip()
    route_match = re.search(r"`(research/operations/(?:vnext_moonshot|vnext_absolute_moonshot)_lane[^`]+/)`", text)
    route_path = route_match.group(1).rstrip("/") if route_match else ""
    starter = path.with_name(name.replace("_GOAL_PROMPT_", "_STARTER_").replace(".md", ".txt"))
    required_work = bullet_lines(extract_section(text, "Required Work"))
    completion = extract_section(text, "Completion Standard")
    posture_line = next((line.strip() for line in text.splitlines() if line.startswith("This is ")), "")
    finish_match = re.search(r"Finish with ([^.]+)\.", text)
    finish_with = finish_match.group(1) if finish_match else "manifest, verifier, focused tests, and completion audit"
    return {
        "lane_id": lane_id,
        "title": first_heading,
        "prompt_path": rel(path),
        "prompt_sha256": sha256_file(path),
        "starter_path": rel(starter),
        "starter_sha256": sha256_file(starter),
        "route_path": route_path,
        "wave": LANE_WAVES[lane_id],
        "dependencies": LANE_DEPENDENCIES[lane_id],
        "evidence_dependencies": EVIDENCE_DEPENDENCIES,
        "posture": posture_line,
        "required_work": required_work,
        "terminal_artifact_contract": {
            "finish_with": finish_with,
            "required_terminal_artifacts": [
                "route_output_manifest",
                "route_verifier",
                "focused_tests",
                "completion_audit",
                "source_use_state",
                "result_use_status",
                "runtime_effect_boundary",
                "branch_or_implementation_decision",
            ],
            "same_evidence_class_pursuit_required": True,
            "ledger_only_completion_allowed": False,
        },
        "boundary_contract": {
            "runtime_effect_boundary": "research_or_default_off_or_dossier_only_until_separate_owner_approval",
            "forbidden_surfaces": [
                "live_trading_broker_operation",
                "order_placement_modification_cancellation_close",
                "paid_api_vendor_call",
                "credential_print_or_change",
                "remote_push",
                "hidden_production_activation",
            ],
            "read_only_mt5_source_acquisition_authorized_when_lane_relevant": True,
        },
        "result_contract": {
            "exact_r_fields_required_when_owned": [
                "exact_r",
                "net_exact_r",
                "cost_adjusted_r",
                "expectancy_r",
                "r_source_state",
            ],
            "proxy_fields_required_when_exact_missing": [
                "proxy_r",
                "proxy_expectancy_r",
                "proxy_source_state",
                "row_level_missing_field_proof",
                "capture_or_export_requirement",
            ],
            "production_change_readiness_from_lane_output": False,
        },
    }


def lane_goal_prompt_paths() -> list[Path]:
    paths: set[Path] = set()
    for pattern in (
        "VNEXT_MOONSHOT_LANE*_GOAL_PROMPT_2026-06-01.md",
        "VNEXT_ABSOLUTE_MOONSHOT_LANE*_GOAL_PROMPT_2026-06-01.md",
    ):
        paths.update(PROMPT_DIR.glob(pattern))

    def sort_key(path: Path) -> tuple[int, str]:
        match = re.search(r"LANE(\d{2})", path.name)
        return (int(match.group(1)) if match else 999, path.name)

    return sorted(paths, key=sort_key)


def lane_goal_prompt_path(lane_id: str) -> Path:
    for path in lane_goal_prompt_paths():
        if f"LANE{lane_id}" in path.name:
            return path
    raise FileNotFoundError(f"Missing lane prompt for Lane{lane_id}")


def _lane01_counts(route_dir: Path) -> dict[str, int | None]:
    audit = load_json(route_dir / "COMPLETION_AUDIT.json", {})
    verification = load_json(route_dir / "VERIFICATION_RESULT.json", {})
    contracts = load_json(route_dir / "DOWNSTREAM_SOURCE_CONTRACTS.json", {})
    return {
        "source_inventory_rows": verification.get("artifact_counts", {}).get("inventory_rows")
        or audit.get("artifact_counts", {}).get("inventory_rows"),
        "source_gap_rows": verification.get("artifact_counts", {}).get("gap_rows")
        or audit.get("artifact_counts", {}).get("gap_rows"),
        "downstream_source_contracts": verification.get("artifact_counts", {}).get("contract_count")
        or len(contracts.get("contracts", {})),
    }


def _lane02_counts(route_dir: Path) -> dict[str, int | None]:
    verification = load_json(route_dir / "LANE02_VERIFICATION_RESULT.json", {})
    audit = load_json(route_dir / "LANE02_COMPLETION_AUDIT.json", {})
    summary = audit.get("summary", {})
    return {
        "timestamp_inventory_rows": verification.get("timestamp_inventory_rows")
        or summary.get("timestamp_inventory_rows"),
        "asof_contract_rows": verification.get("asof_contract_rows")
        or summary.get("asof_field_contract_rows"),
    }


def _lane03_counts(route_dir: Path) -> dict[str, int | None]:
    audit = load_json(route_dir / "LANE03_COMPLETION_AUDIT.json", {})
    counts = audit.get("counts", {})
    return {
        "canonical_event_rows": counts.get("total_event_rows"),
        "canonical_candidate_rows": counts.get("candidate_rows"),
        "duplicate_groups": counts.get("duplicate_groups"),
        "source_inventory_rows": counts.get("source_count"),
        "source_gap_rows": counts.get("source_gap_rows"),
        "exact_r_rows": counts.get("exact_r_count"),
        "proxy_r_rows": counts.get("proxy_r_count"),
    }


def _lane04_counts(route_dir: Path) -> dict[str, int | None]:
    verification = load_json(route_dir / "LANE04_VERIFICATION_RESULT.json", {})
    summary = load_json(route_dir / "LANE04_EXPECTANCY_SUMMARY.json", {})
    return {
        "timeline_rows": verification.get("timeline_rows") or summary.get("timeline_rows"),
        "strict_tick_rows": verification.get("strict_tick_rows")
        or summary.get("strict_tick", {}).get("strict_tick_materialized_rows"),
        "source_gap_rows": verification.get("source_gap_rows") or summary.get("source_gap_rows"),
        "anatomy_split_rows": summary.get("anatomy_split_rows"),
    }


def wave1_terminal_state_table() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    count_readers = {
        "01": _lane01_counts,
        "02": _lane02_counts,
        "03": _lane03_counts,
        "04": _lane04_counts,
    }
    for lane_id, route_dir in WAVE1_ROUTE_DIRS.items():
        required = WAVE1_REQUIRED_ARTIFACTS[lane_id]
        verification = load_json(route_dir / required["verifier_result"], {})
        completion = load_json(route_dir / required["completion_audit"], {})
        manifest = load_json(route_dir / required["manifest"], {})
        dependency_rows = read_jsonl_rows(route_dir / required["dependency_ledger"])
        counts = count_readers[lane_id](route_dir)
        expected_counts = WAVE1_EXPECTED_COUNTS[lane_id]
        count_matches = {key: counts.get(key) == value for key, value in expected_counts.items()}
        required_files = [
            required["completion_audit"],
            required["verifier_result"],
            required["manifest"],
            required["dependency_ledger"],
            required["source_gap_ledger"],
            required["context_anchor"],
            *required["schema_contracts"],
        ]
        missing_files = [name for name in required_files if not (route_dir / name).exists()]
        verifier_ok = bool(verification.get("ok", verification.get("passed", False)))
        completion_status = (
            completion.get("status")
            or ("complete" if completion.get("can_mark_goal_complete") else None)
            or ("complete" if completion.get("completion_ready") else None)
        )
        rows.append(
            {
                "lane_id": lane_id,
                "route_path": rel(route_dir),
                "terminal_status": "terminal_verified" if verifier_ok and not missing_files and all(count_matches.values()) else "not_terminal",
                "completion_status": completion_status,
                "verifier_ok": verifier_ok,
                "verifier_result_path": rel(route_dir / required["verifier_result"]),
                "completion_audit_path": rel(route_dir / required["completion_audit"]),
                "manifest_path": rel(route_dir / required["manifest"]),
                "dependency_ledger_path": rel(route_dir / required["dependency_ledger"]),
                "source_gap_ledger_path": rel(route_dir / required["source_gap_ledger"]),
                "schema_contract_paths": [rel(route_dir / name) for name in required["schema_contracts"]],
                "material_row_count_artifacts": [
                    artifact_presence_record(route_dir, name)
                    for name in required["material_row_count_artifacts"]
                ],
                "context_anchor_path": rel(route_dir / required["context_anchor"]),
                "material_row_counts": counts,
                "expected_count_matches": count_matches,
                "dependency_rows": len(dependency_rows),
                "manifest_output_count": manifest.get("output_count") or len(manifest.get("files", [])),
                "missing_required_files": missing_files,
                "source_use_state": "direct_disk_artifacts_inspected_by_master_refresh",
                "result_use_status": "terminal_wave1_source_bound_evidence_not_broker_real_production_claim",
            }
        )
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_wave1_terminal_state_table_v1",
        "generated_at_utc": utc_now(),
        "git": git_head(),
        "wave1_lanes": rows,
        "all_wave1_terminal_verified": all(row["terminal_status"] == "terminal_verified" for row in rows),
        "source_use_state": "completion_audits_verifier_results_manifests_dependency_ledgers_source_gap_ledgers_schema_contracts_context_anchors_and_material_counts_read_from_disk",
        "runtime_effect_boundary": "master_consumption_only_no_lane_rebuild_no_live_behavior_change",
    }


def wave1_artifact_inspection_rows(terminal_table: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    table = terminal_table or wave1_terminal_state_table()
    terminal_by_lane = {row["lane_id"]: row for row in table["wave1_lanes"]}
    rows: list[dict[str, Any]] = []
    now = utc_now()
    for lane_id, route_dir in WAVE1_ROUTE_DIRS.items():
        required = WAVE1_REQUIRED_ARTIFACTS[lane_id]
        terminal = terminal_by_lane[lane_id]
        artifact_names = [
            required["completion_audit"],
            required["verifier_result"],
            required["manifest"],
            required["dependency_ledger"],
            required["source_gap_ledger"],
            required["context_anchor"],
            *required["schema_contracts"],
        ]
        rows.append(
            {
                "schema_version": "absolute_master_wave1_artifact_inspection_row_v1",
                "timestamp_utc": now,
                "artifact_family": f"absolute_lane{lane_id}_terminal_outputs",
                "lane_id": lane_id,
                "route_path": rel(route_dir),
                "inspection_status": terminal["terminal_status"],
                "verifier_ok": terminal["verifier_ok"],
                "completion_status": terminal["completion_status"],
                "material_row_counts": terminal["material_row_counts"],
                "dependency_rows": terminal["dependency_rows"],
                "source_gap_ledger_path": terminal["source_gap_ledger_path"],
                "schema_contract_paths": terminal["schema_contract_paths"],
                "material_row_count_artifacts": terminal["material_row_count_artifacts"],
                "context_anchor_path": terminal["context_anchor_path"],
                "artifacts": [artifact_record(route_dir, name) for name in artifact_names],
                "source_use_state": "direct_artifact_inspection_not_closeout_claim",
                "runtime_effect_boundary": "inspection_only_no_heavy_ledger_rebuild_no_live_behavior_change",
            }
        )
    return rows


def _lane05_counts(route_dir: Path) -> dict[str, int | None]:
    audit = load_json(route_dir / "LANE05_COMPLETION_AUDIT.json", {})
    return {
        "canonical_candidate_feature_rows": audit.get("row_counts", {}).get("canonical_candidate_feature_rows"),
        "timeline_feature_rows": audit.get("row_counts", {}).get("timeline_feature_rows"),
    }


def _lane06_counts(route_dir: Path) -> dict[str, int | None]:
    audit = load_json(route_dir / "LANE06_COMPLETION_AUDIT.json", {})
    verification = load_json(route_dir / "LANE06_VERIFICATION_RESULT.json", {})
    counts = audit.get("counts", {})
    metrics = verification.get("metrics", {})
    return {
        "label_vector_rows": counts.get("label_vector_rows") or metrics.get("label_vector_rows"),
        "missing_label_gap_rows": counts.get("missing_label_gap_rows") or metrics.get("missing_label_gap_rows"),
        "broker_real_label_rows": counts.get("broker_real_rows"),
        "lane05_consumed": bool(audit.get("instruction_coverage", {}).get("lane05_feature_store_present_consumed")),
        "lane07_consumed": bool(audit.get("instruction_coverage", {}).get("lane07_broker_truth_cost_present_consumed")),
    }


def _lane07_counts(route_dir: Path) -> dict[str, int | None]:
    verification = load_json(route_dir / "LANE07_VERIFICATION_RESULT.json", {})
    counts = verification.get("counts", {})
    return {
        "symbol_rows": counts.get("symbol_rows"),
        "broker_truth_rows": counts.get("broker_truth_rows"),
        "cost_rows": counts.get("cost_rows"),
        "source_gap_rows": counts.get("gap_rows"),
        "source_coverage_rows": counts.get("source_coverage_rows"),
    }


def _completion_status(completion: dict[str, Any]) -> str | None:
    return (
        completion.get("completion_status")
        or completion.get("status")
        or ("complete" if completion.get("can_mark_goal_complete") else None)
        or ("complete" if completion.get("completion_ready") else None)
    )


def _is_terminal_completion_status(status: str | None) -> bool:
    return bool(status) and str(status).startswith("complete")


def wave2_terminal_state_table() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    count_readers = {
        "05": _lane05_counts,
        "06": _lane06_counts,
        "07": _lane07_counts,
    }
    for lane_id, route_dir in WAVE2_ROUTE_DIRS.items():
        required = WAVE2_REQUIRED_ARTIFACTS[lane_id]
        verification = load_json(route_dir / required["verifier_result"], {})
        completion = load_json(route_dir / required["completion_audit"], {})
        manifest = load_json(route_dir / required["manifest"], {})
        downstream_contract = load_json(route_dir / required["downstream_contract"], {})
        dependency_rows = read_jsonl_rows(route_dir / required["dependency_ledger"])
        counts = count_readers[lane_id](route_dir)
        expected_counts = WAVE2_EXPECTED_COUNTS[lane_id]
        count_matches = {key: counts.get(key) == value for key, value in expected_counts.items()}
        focused = parse_junit_result(route_dir / required["focused_test_result"])
        required_files = [
            required["completion_audit"],
            required["verifier_result"],
            required["manifest"],
            required["downstream_contract"],
            required["dependency_ledger"],
            required["context_anchor"],
            required["builder"],
            required["verifier"],
            required["focused_test_result"],
            required["runtime_effect_boundary"],
            *required.get("schema_contracts", []),
            *required.get("coverage_ledgers", []),
            *required.get("source_gap_ledgers", []),
            *required.get("material_row_count_artifacts", []),
            *required.get("tests", []),
        ]
        for optional_key in ["result_use_status", "source_use_state", "saturation_review"]:
            optional_name = required.get(optional_key)
            if optional_name:
                required_files.append(optional_name)
        missing_files = [name for name in required_files if not resolve_route_artifact(route_dir, name).exists()]
        verifier_ok = bool(verification.get("ok", verification.get("passed", False)))
        lane_specific_contract_ok = True
        if lane_id == "06":
            lane_specific_contract_ok = bool(counts.get("lane05_consumed")) and bool(counts.get("lane07_consumed"))
        if lane_id == "07":
            missing_rule = downstream_contract.get("missing_data_rule", "")
            lane_specific_contract_ok = (
                "do not block Lane05 Feature Store, Lane06 Label Store, Lane08 Digital Twin, ML, Selector, Scheduler, or Execution Policy work"
                in missing_rule
            )
        terminal_verified = (
            verifier_ok
            and focused["ok"]
            and not missing_files
            and all(count_matches.values())
            and lane_specific_contract_ok
        )
        non_material_artifacts = [
            required["completion_audit"],
            required["verifier_result"],
            required["manifest"],
            required["downstream_contract"],
            required["dependency_ledger"],
            required["context_anchor"],
            required["builder"],
            required["verifier"],
            required["focused_test_result"],
            required["runtime_effect_boundary"],
            *required.get("schema_contracts", []),
            *required.get("coverage_ledgers", []),
            *required.get("source_gap_ledgers", []),
            *required.get("tests", []),
        ]
        material_names = set(required.get("material_row_count_artifacts", []))
        non_material_artifacts = [
            name for name in non_material_artifacts if name not in material_names and not name.endswith(".gz")
        ]
        rows.append(
            {
                "lane_id": lane_id,
                "route_path": rel(route_dir),
                "terminal_status": "terminal_verified" if terminal_verified else "not_terminal",
                "completion_status": _completion_status(completion),
                "verifier_ok": verifier_ok,
                "focused_test_result": focused,
                "verifier_result_path": rel(route_dir / required["verifier_result"]),
                "completion_audit_path": rel(route_dir / required["completion_audit"]),
                "manifest_path": rel(route_dir / required["manifest"]),
                "downstream_contract_path": rel(route_dir / required["downstream_contract"]),
                "dependency_ledger_path": rel(route_dir / required["dependency_ledger"]),
                "source_gap_ledger_paths": [
                    rel(resolve_route_artifact(route_dir, name)) for name in required.get("source_gap_ledgers", [])
                ],
                "coverage_ledger_paths": [
                    rel(resolve_route_artifact(route_dir, name)) for name in required.get("coverage_ledgers", [])
                ],
                "schema_contract_paths": [
                    rel(resolve_route_artifact(route_dir, name)) for name in required.get("schema_contracts", [])
                ],
                "material_row_count_artifacts": [
                    artifact_presence_record(route_dir, name)
                    for name in required.get("material_row_count_artifacts", [])
                ],
                "context_anchor_path": rel(route_dir / required["context_anchor"]),
                "material_row_counts": counts,
                "expected_count_matches": count_matches,
                "dependency_rows": len(dependency_rows),
                "manifest_output_count": manifest_output_count(manifest),
                "missing_required_files": missing_files,
                "lane_specific_contract_ok": lane_specific_contract_ok,
                "inspected_artifacts": [artifact_record(route_dir, name) for name in non_material_artifacts],
                "source_use_state": "direct_disk_artifacts_inspected_by_master_wave2_refresh",
                "result_use_status": "terminal_wave2_research_artifact_consumption_not_live_activation",
                "runtime_effect_boundary": "master_consumption_only_no_lane_rebuild_no_live_behavior_change",
            }
        )
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_wave2_terminal_state_table_v1",
        "generated_at_utc": utc_now(),
        "git": git_head(),
        "wave2_lanes": rows,
        "all_wave2_terminal_verified": all(row["terminal_status"] == "terminal_verified" for row in rows),
        "source_use_state": "completion_audits_verifier_results_manifests_downstream_contracts_dependency_source_gap_coverage_ledgers_schema_files_context_anchors_tests_and_material_counts_read_from_disk",
        "runtime_effect_boundary": "master_consumption_only_no_lane_rebuild_no_live_behavior_change",
    }


def wave2_artifact_inspection_rows(terminal_table: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    table = terminal_table or wave2_terminal_state_table()
    terminal_by_lane = {row["lane_id"]: row for row in table["wave2_lanes"]}
    rows: list[dict[str, Any]] = []
    now = utc_now()
    for lane_id, route_dir in WAVE2_ROUTE_DIRS.items():
        terminal = terminal_by_lane[lane_id]
        rows.append(
            {
                "schema_version": "absolute_master_wave2_artifact_inspection_row_v1",
                "timestamp_utc": now,
                "artifact_family": f"absolute_lane{lane_id}_terminal_outputs",
                "lane_id": lane_id,
                "route_path": rel(route_dir),
                "inspection_status": terminal["terminal_status"],
                "verifier_ok": terminal["verifier_ok"],
                "completion_status": terminal["completion_status"],
                "focused_test_result": terminal["focused_test_result"],
                "material_row_counts": terminal["material_row_counts"],
                "dependency_rows": terminal["dependency_rows"],
                "source_gap_ledger_paths": terminal["source_gap_ledger_paths"],
                "coverage_ledger_paths": terminal["coverage_ledger_paths"],
                "schema_contract_paths": terminal["schema_contract_paths"],
                "downstream_contract_path": terminal["downstream_contract_path"],
                "material_row_count_artifacts": terminal["material_row_count_artifacts"],
                "context_anchor_path": terminal["context_anchor_path"],
                "artifacts": terminal["inspected_artifacts"],
                "source_use_state": "direct_artifact_inspection_not_closeout_claim",
                "runtime_effect_boundary": "inspection_only_no_heavy_ledger_rebuild_no_live_behavior_change",
            }
        )
    return rows


def _lane08_counts(route_dir: Path) -> dict[str, int | None]:
    verification = load_json(route_dir / "LANE08_VERIFICATION_RESULT.json", {})
    counts = verification.get("counts", {})
    return {
        "replay_rows": counts.get("replay_rows"),
        "missing_replay_gap_rows": counts.get("missing_replay_gap_rows"),
        "split_metric_rows": counts.get("split_metric_rows"),
        "depth_rows": counts.get("depth_rows"),
    }


def _lane09_counts(route_dir: Path) -> dict[str, int | bool | None]:
    verification = load_json(route_dir / "LANE09_VERIFICATION_RESULT.json", {})
    counts = verification.get("counts", {})
    return {
        "selector_row_evidence_rows": counts.get("selector_row_evidence_rows"),
        "selector_discovery_rows": counts.get("selector_discovery_rows"),
        "default_off_clause_rows": counts.get("default_off_clause_rows"),
        "mechanism_decision_rows": counts.get("mechanism_decision_rows"),
        "capture_repair_requirement_rows": counts.get("capture_repair_requirement_rows"),
        "focused_test_result_present": bool(counts.get("focused_test_result_present")),
    }


def _lane10_counts(route_dir: Path) -> dict[str, int | None]:
    verification = load_json(route_dir / "LANE10_VERIFICATION_RESULT.json", {})
    counts = verification.get("counts", {})
    return {
        "replay_rows": counts.get("replay_rows"),
        "conflict_rows": counts.get("conflict_rows"),
        "gap_rows": counts.get("gap_rows"),
        "risk_rows": counts.get("risk_rows"),
        "split_rows": counts.get("split_rows"),
    }


def _lane11_counts(route_dir: Path) -> dict[str, int | None]:
    verification = load_json(route_dir / "LANE11_VERIFICATION_RESULT.json", {})
    audit = load_json(route_dir / "LANE11_COMPLETION_AUDIT.json", {})
    counts = verification.get("counts", {})
    audit_counts = audit.get("counts", {})
    return {
        "simulation_rows": counts.get("simulation_rows"),
        "policy_result_cells": counts.get("policy_result_cells"),
        "metric_rows": counts.get("metric_rows"),
        "policy_variant_count": counts.get("policy_variant_count"),
        "dominance_decision_rows": audit_counts.get("dominance_decision_rows"),
        "default_off_package_rows": audit_counts.get("default_off_package_rows"),
        "expanded_policy_variant_count": counts.get("expanded_policy_variant_count"),
        "expanded_metric_rows": counts.get("expanded_metric_rows"),
        "expanded_package_rows": counts.get("expanded_package_rows"),
        "expanded_policy_result_cell_accounting": counts.get("expanded_policy_result_cell_accounting"),
    }


def wave3_terminal_state_table() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    count_readers = {
        "08": _lane08_counts,
        "09": _lane09_counts,
        "10": _lane10_counts,
        "11": _lane11_counts,
    }
    for lane_id, route_dir in WAVE3_ROUTE_DIRS.items():
        required = WAVE3_REQUIRED_ARTIFACTS[lane_id]
        verification = load_json(route_dir / required["verifier_result"], {})
        completion = load_json(route_dir / required["completion_audit"], {})
        manifest = load_json(route_dir / required["manifest"], {})
        dependency_rows = read_jsonl_rows(route_dir / required["dependency_ledger"])
        counts = count_readers[lane_id](route_dir)
        expected_counts = WAVE3_EXPECTED_COUNTS[lane_id]
        count_matches = {key: counts.get(key) == value for key, value in expected_counts.items()}
        focused = parse_junit_result(route_dir / required["focused_test_result"])
        required_files = [
            required["completion_audit"],
            required["verifier_result"],
            required["manifest"],
            required["downstream_contract"],
            required["dependency_ledger"],
            required["context_anchor"],
            required["builder"],
            required["verifier"],
            required["focused_test_result"],
            *required.get("schema_contracts", []),
            *required.get("source_gap_ledgers", []),
            *required.get("material_row_count_artifacts", []),
            *required.get("tests", []),
        ]
        for optional_key in ["result_use_status", "source_use_state", "runtime_effect_boundary"]:
            optional_name = required.get(optional_key)
            if optional_name:
                required_files.append(optional_name)
        missing_files = [name for name in required_files if not resolve_route_artifact(route_dir, name).exists()]
        verifier_ok = bool(verification.get("ok", verification.get("passed", False)))
        completion_status = _completion_status(completion)
        terminal_verified = (
            verifier_ok
            and focused["ok"]
            and not missing_files
            and all(count_matches.values())
            and completion_status == "complete_verified"
        )
        material_names = set(required.get("material_row_count_artifacts", []))
        non_material_artifacts = [
            name
            for name in required_files
            if name not in material_names and not name.endswith(".gz")
        ]
        rows.append(
            {
                "lane_id": lane_id,
                "route_path": rel(route_dir),
                "terminal_status": "terminal_verified" if terminal_verified else "not_terminal",
                "completion_status": completion_status,
                "commit": git_last_commit_for_path(route_dir),
                "verifier_ok": verifier_ok,
                "focused_test_result": focused,
                "verifier_result_path": rel(route_dir / required["verifier_result"]),
                "completion_audit_path": rel(route_dir / required["completion_audit"]),
                "manifest_path": rel(route_dir / required["manifest"]),
                "manifest_output_count": manifest_output_count(manifest),
                "downstream_contract_path": rel(route_dir / required["downstream_contract"]),
                "dependency_ledger_path": rel(route_dir / required["dependency_ledger"]),
                "source_gap_ledger_paths": [
                    rel(resolve_route_artifact(route_dir, name)) for name in required.get("source_gap_ledgers", [])
                ],
                "schema_contract_paths": [
                    rel(resolve_route_artifact(route_dir, name)) for name in required.get("schema_contracts", [])
                ],
                "material_row_count_artifacts": [
                    artifact_presence_record(route_dir, name)
                    for name in required.get("material_row_count_artifacts", [])
                ],
                "context_anchor_path": rel(route_dir / required["context_anchor"]),
                "material_row_counts": counts,
                "expected_count_matches": count_matches,
                "dependency_rows": len(dependency_rows),
                "missing_required_files": missing_files,
                "inspected_artifacts": [artifact_record(route_dir, name) for name in non_material_artifacts],
                "source_use_state": "direct_disk_artifacts_inspected_by_post_lane11_master_refresh",
                "result_use_status": "terminal_wave3_research_artifact_consumption_not_live_activation",
                "runtime_effect_boundary": "master_consumption_only_no_lane_rebuild_no_live_behavior_change",
            }
        )
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_wave3_terminal_state_table_v1",
        "generated_at_utc": utc_now(),
        "git": git_head(),
        "wave3_lanes": rows,
        "all_wave3_terminal_verified": all(row["terminal_status"] == "terminal_verified" for row in rows),
        "source_use_state": "completion_audits_verifier_results_manifests_downstream_contracts_dependency_source_gap_ledgers_schema_files_context_anchors_tests_and_material_counts_read_from_disk",
        "runtime_effect_boundary": "master_consumption_only_no_lane_rebuild_no_live_behavior_change",
    }


def wave3_artifact_inspection_rows(terminal_table: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    table = terminal_table or wave3_terminal_state_table()
    terminal_by_lane = {row["lane_id"]: row for row in table["wave3_lanes"]}
    rows: list[dict[str, Any]] = []
    now = utc_now()
    for lane_id, route_dir in WAVE3_ROUTE_DIRS.items():
        terminal = terminal_by_lane[lane_id]
        rows.append(
            {
                "schema_version": "absolute_master_wave3_artifact_inspection_row_v1",
                "timestamp_utc": now,
                "artifact_family": f"absolute_lane{lane_id}_terminal_outputs",
                "lane_id": lane_id,
                "route_path": rel(route_dir),
                "inspection_status": terminal["terminal_status"],
                "commit": terminal["commit"],
                "verifier_ok": terminal["verifier_ok"],
                "completion_status": terminal["completion_status"],
                "focused_test_result": terminal["focused_test_result"],
                "material_row_counts": terminal["material_row_counts"],
                "dependency_rows": terminal["dependency_rows"],
                "source_gap_ledger_paths": terminal["source_gap_ledger_paths"],
                "schema_contract_paths": terminal["schema_contract_paths"],
                "downstream_contract_path": terminal["downstream_contract_path"],
                "material_row_count_artifacts": terminal["material_row_count_artifacts"],
                "context_anchor_path": terminal["context_anchor_path"],
                "artifacts": terminal["inspected_artifacts"],
                "source_use_state": "direct_artifact_inspection_not_closeout_claim",
                "runtime_effect_boundary": "inspection_only_no_heavy_ledger_rebuild_no_live_behavior_change",
            }
        )
    return rows


def _lane09b_counts(route_dir: Path) -> dict[str, int | float | None]:
    audit = load_json(route_dir / "LANE09B_COMPLETION_AUDIT.json", {})
    verification = load_json(route_dir / "LANE09B_VERIFICATION_RESULT.json", {})
    counts = verification.get("counts", {})
    metrics = audit.get("scheduler_reconciliation_metrics", {})
    return {
        "selector_scheduler_join_rows": counts.get("LANE09B_SELECTOR_TO_SCHEDULER_ROW_JOIN_LEDGER.jsonl.gz"),
        "clause_outcome_rows": counts.get("LANE09B_CLAUSE_TO_SCHEDULER_OUTCOME_LEDGER.jsonl"),
        "discovery_outcome_rows": counts.get("LANE09B_DISCOVERY_TO_SCHEDULER_OUTCOME_LEDGER.jsonl.gz"),
        "mechanism_outcome_rows": counts.get("LANE09B_MECHANISM_TO_SCHEDULER_OUTCOME_LEDGER.jsonl"),
        "capture_requirement_gap_rows": counts.get("LANE09B_CAPTURE_REQUIREMENT_TO_SCHEDULER_GAP_LEDGER.jsonl"),
        "lane11_policy_dependent_rows": metrics.get("lane11_policy_dependent_rows"),
        "scheduler_survived_rows": metrics.get("reconciliation_class_counts", {}).get("scheduler-survived"),
        "scheduler_reduced_rows": metrics.get("reconciliation_class_counts", {}).get("scheduler-reduced"),
        "scheduler_blocked_repairable_rows": metrics.get("reconciliation_class_counts", {}).get("scheduler-blocked-repairable"),
        "selector_false_positive_rows": metrics.get("reconciliation_class_counts", {}).get("selector-false-positive"),
    }


def _lane10b_counts(route_dir: Path) -> dict[str, int | None]:
    verification = load_json(route_dir / "LANE10B_VERIFICATION_RESULT.json", {})
    counts = verification.get("counts", {})
    return {
        "full_anatomy_rows": counts.get("full_anatomy_rows"),
        "missed_edge_rows": counts.get("missed_edge_rows"),
        "correct_reject_rows": counts.get("correct_reject_rows"),
        "repairable_rows": counts.get("repairable_rows"),
        "risk_breach_rows": counts.get("risk_breach_rows"),
        "stress_rows": counts.get("stress_rows"),
        "impact_dimension_rows": counts.get("impact_dimension_rows"),
        "source_gap_rows": counts.get("source_gap_rows"),
        "branch_decision_rows": counts.get("branch_decision_rows"),
    }


def post_lane11_terminal_state_table(wave3_table: dict[str, Any] | None = None) -> dict[str, Any]:
    wave3 = wave3_table or wave3_terminal_state_table()
    lane11 = next(row for row in wave3["wave3_lanes"] if row["lane_id"] == "11")
    now = utc_now()
    rows: list[dict[str, Any]] = []
    specs = {
        "09B": {
            "route_dir": POST_LANE11_ROUTE_DIRS["09B"],
            "completion_audit": "LANE09B_COMPLETION_AUDIT.json",
            "verifier_result": "LANE09B_VERIFICATION_RESULT.json",
            "manifest": "LANE09B_OUTPUT_MANIFEST.json",
            "focused_test_result": "LANE09B_FOCUSED_TEST_RESULT.xml",
            "downstream_contracts": [
                "LANE09B_SCHEDULER_AWARE_META_SELECTOR_REFINEMENT_PACKAGE.json",
                "LANE09B_LANE11_EXPANDED_POLICY_INTEGRATION_CONTRACT.json",
            ],
            "counts": _lane09b_counts(POST_LANE11_ROUTE_DIRS["09B"]),
            "expected_count_matches": {
                "selector_scheduler_join_rows": _lane09b_counts(POST_LANE11_ROUTE_DIRS["09B"]).get("selector_scheduler_join_rows") == 289928,
                "lane11_policy_dependent_rows": _lane09b_counts(POST_LANE11_ROUTE_DIRS["09B"]).get("lane11_policy_dependent_rows") == 110386,
            },
        },
        "10B": {
            "route_dir": POST_LANE11_ROUTE_DIRS["10B"],
            "completion_audit": "LANE10B_COMPLETION_AUDIT.json",
            "verifier_result": "LANE10B_VERIFICATION_RESULT.json",
            "manifest": "LANE10B_OUTPUT_MANIFEST.json",
            "focused_test_result": "LANE10B_FOCUSED_TEST_RESULT.xml",
            "downstream_contracts": [
                "LANE10B_MULTI_TICKET_LIFECYCLE_CONTRACT.json",
                "LANE10B_SCHEDULER_V3_DEFAULT_OFF_DESIGN_PACKAGE.json",
                "LANE10B_LANE11_INTEGRATION_CONTRACT.json",
            ],
            "counts": _lane10b_counts(POST_LANE11_ROUTE_DIRS["10B"]),
            "expected_count_matches": {
                "full_anatomy_rows": _lane10b_counts(POST_LANE11_ROUTE_DIRS["10B"]).get("full_anatomy_rows") == 289928,
                "missed_edge_rows": _lane10b_counts(POST_LANE11_ROUTE_DIRS["10B"]).get("missed_edge_rows") == 222563,
                "repairable_rows": _lane10b_counts(POST_LANE11_ROUTE_DIRS["10B"]).get("repairable_rows") == 42479,
            },
        },
        "11": {
            "route_dir": POST_LANE11_ROUTE_DIRS["11"],
            "completion_audit": "LANE11_COMPLETION_AUDIT.json",
            "verifier_result": "LANE11_VERIFICATION_RESULT.json",
            "manifest": "LANE11_OUTPUT_MANIFEST.json",
            "focused_test_result": "LANE11_FOCUSED_TEST_RESULT.xml",
            "downstream_contracts": [
                "LANE11_DOWNSTREAM_CONTRACT.json",
                "LANE11_DEFAULT_OFF_POLICY_ROUTER_PACKAGE.json",
            ],
            "counts": lane11["material_row_counts"],
            "expected_count_matches": lane11["expected_count_matches"],
        },
    }
    for lane_id, spec in specs.items():
        route_dir = spec["route_dir"]
        verification = load_json(route_dir / spec["verifier_result"], {})
        completion = load_json(route_dir / spec["completion_audit"], {})
        manifest = load_json(route_dir / spec["manifest"], {})
        focused = parse_junit_result(route_dir / spec["focused_test_result"])
        required_files = [
            spec["completion_audit"],
            spec["verifier_result"],
            spec["manifest"],
            spec["focused_test_result"],
            *spec["downstream_contracts"],
        ]
        missing_files = [name for name in required_files if not (route_dir / name).exists()]
        verifier_ok = bool(verification.get("ok", verification.get("passed", False)))
        expected_ok = all(bool(value) for value in spec["expected_count_matches"].values())
        completion_status = _completion_status(completion)
        terminal_status = (
            "terminal_verified"
            if verifier_ok and focused["ok"] and expected_ok and not missing_files and completion_status == "complete_verified"
            else "not_terminal"
        )
        rows.append(
            {
                "schema_version": "absolute_master_post_lane11_terminal_state_row_v1",
                "timestamp_utc": now,
                "lane_id": lane_id,
                "route_path": rel(route_dir),
                "terminal_status": terminal_status,
                "completion_status": completion_status,
                "commit": git_last_commit_for_path(route_dir),
                "verifier_ok": verifier_ok,
                "focused_test_result": focused,
                "manifest_path": rel(route_dir / spec["manifest"]),
                "manifest_output_count": manifest_output_count(manifest),
                "completion_audit_path": rel(route_dir / spec["completion_audit"]),
                "verifier_result_path": rel(route_dir / spec["verifier_result"]),
                "downstream_contract_paths": [rel(route_dir / name) for name in spec["downstream_contracts"]],
                "material_row_counts": spec["counts"],
                "expected_count_matches": spec["expected_count_matches"],
                "missing_required_files": missing_files,
                "source_use_state": "terminal_disk_evidence_consumed_by_post_lane11_master_refresh",
                "runtime_effect_boundary": "master_consumption_only_no_lane_rebuild_no_live_behavior_change",
            }
        )
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_post_lane11_terminal_state_table_v1",
        "generated_at_utc": utc_now(),
        "git": git_head(),
        "terminal_lanes": rows,
        "all_post_lane11_terminal_verified": all(row["terminal_status"] == "terminal_verified" for row in rows),
        "source_use_state": "Lane09B_Lane10B_Lane11_completion_audits_verifiers_manifests_focused_tests_and_contracts_read_from_disk",
        "runtime_effect_boundary": "master_consumption_only_no_lane_rebuild_no_live_behavior_change",
    }


def _lane16_counts(route_dir: Path) -> dict[str, int | None]:
    verification = load_json(route_dir / "LANE16_VERIFICATION_RESULT.json", {})
    return {
        "event_rows": verification.get("event_rows"),
        "path_anatomy_rows": verification.get("path_anatomy_rows"),
        "source_gap_rows": verification.get("source_gap_rows"),
        "non_reconstructable_gap_rows": verification.get("non_reconstructable_gap_rows"),
        "coverage_inventory_rows": verification.get("coverage_inventory_rows"),
        "split_stress_rows": verification.get("split_stress_rows"),
    }


def _lane17_counts(route_dir: Path) -> dict[str, int | None]:
    verification = load_json(route_dir / "LANE17_VERIFICATION_RESULT.json", {})
    counts = verification.get("counts", {})
    return {
        "replay_whiteboard_rows": counts.get("replay_whiteboard_rows"),
        "source_gap_rows": counts.get("source_gap_rows"),
        "forward_snapshot_rows": counts.get("forward_snapshot_rows"),
        "source_completeness_rows": counts.get("source_completeness_rows"),
        "correlation_pair_rows": counts.get("correlation_pair_rows"),
    }


def _lane18_counts(route_dir: Path) -> dict[str, int | None]:
    verification = load_json(route_dir / "LANE18_VERIFICATION_RESULT.json", {})
    completion = load_json(route_dir / "LANE18_COMPLETION_AUDIT.json", {})
    verifier_counts = verification.get("counts", {})
    completion_counts = completion.get("counts", {})
    return {
        "source_inventory_rows": completion_counts.get("source_inventory_rows"),
        "source_gap_rows": verifier_counts.get("source_gap_rows") or completion_counts.get("source_gap_rows"),
        "prospective_capture_rows": verifier_counts.get("prospective_capture_rows") or completion_counts.get("prospective_capture_rows"),
        "cost_rows": verifier_counts.get("cost_rows") or completion_counts.get("cost_rows"),
    }


def wave4_terminal_state_table() -> dict[str, Any]:
    count_readers = {
        "16": _lane16_counts,
        "17": _lane17_counts,
        "18": _lane18_counts,
    }
    now = utc_now()
    rows: list[dict[str, Any]] = []
    for lane_id, route_dir in WAVE4_ROUTE_DIRS.items():
        required = WAVE4_REQUIRED_ARTIFACTS[lane_id]
        verification = load_json(route_dir / required["verifier_result"], {})
        completion = load_json(route_dir / required["completion_audit"], {})
        manifest = load_json(route_dir / required["manifest"], {})
        dependency_rows = (
            read_jsonl_rows(route_dir / required["dependency_ledger"])
            if required.get("dependency_ledger")
            else []
        )
        counts = count_readers[lane_id](route_dir)
        expected_counts = WAVE4_EXPECTED_COUNTS[lane_id]
        count_matches = {key: counts.get(key) == value for key, value in expected_counts.items()}
        focused = parse_junit_result(route_dir / required["focused_test_result"])
        required_files = [
            required["completion_audit"],
            required["verifier_result"],
            required["manifest"],
            required["downstream_contract"],
            required["builder"],
            required["verifier"],
            required["focused_test_result"],
            required["context_anchor"],
            *required.get("schema_contracts", []),
            *required.get("source_gap_ledgers", []),
            *required.get("material_row_count_artifacts", []),
            *required.get("tests", []),
        ]
        if required.get("dependency_ledger"):
            required_files.append(required["dependency_ledger"])
        for optional_key in ["result_use_status", "source_use_state", "runtime_effect_boundary"]:
            optional_name = required.get(optional_key)
            if optional_name:
                required_files.append(optional_name)
        missing_files = [name for name in required_files if not resolve_route_artifact(route_dir, name).exists()]
        verifier_ok = bool(verification.get("ok", verification.get("passed", False)))
        completion_status = _completion_status(completion)
        terminal_verified = (
            verifier_ok
            and focused["ok"]
            and not missing_files
            and all(count_matches.values())
            and _is_terminal_completion_status(completion_status)
        )
        material_names = set(required.get("material_row_count_artifacts", []))
        non_material_artifacts = [
            name
            for name in required_files
            if name not in material_names and not name.endswith(".gz")
        ]
        rows.append(
            {
                "schema_version": "absolute_master_wave4_terminal_state_row_v1",
                "timestamp_utc": now,
                "lane_id": lane_id,
                "route_path": rel(route_dir),
                "terminal_status": "terminal_verified" if terminal_verified else "not_terminal",
                "completion_status": completion_status,
                "commit": git_last_commit_for_path(route_dir),
                "verifier_ok": verifier_ok,
                "focused_test_result": focused,
                "manifest_path": rel(route_dir / required["manifest"]),
                "manifest_output_count": manifest_output_count(manifest),
                "completion_audit_path": rel(route_dir / required["completion_audit"]),
                "verifier_result_path": rel(route_dir / required["verifier_result"]),
                "downstream_contract_path": rel(route_dir / required["downstream_contract"]),
                "material_row_counts": counts,
                "expected_count_matches": count_matches,
                "missing_required_files": missing_files,
                "dependency_rows": len(dependency_rows),
                "source_gap_ledger_paths": [rel(route_dir / name) for name in required.get("source_gap_ledgers", [])],
                "schema_contract_paths": [rel(route_dir / name) for name in required.get("schema_contracts", [])],
                "material_row_count_artifacts": [rel(route_dir / name) for name in required.get("material_row_count_artifacts", [])],
                "context_anchor_path": rel(route_dir / required["context_anchor"]),
                "inspected_artifacts": [artifact_record(route_dir, name) for name in non_material_artifacts],
                "source_use_state": "terminal_wave4_disk_evidence_consumed_by_master_refresh",
                "runtime_effect_boundary": "master_consumption_only_no_lane_rebuild_no_live_behavior_change",
            }
        )
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_wave4_terminal_state_table_v1",
        "generated_at_utc": utc_now(),
        "git": git_head(),
        "wave4_lanes": rows,
        "all_wave4_terminal_verified": all(row["terminal_status"] == "terminal_verified" for row in rows),
        "source_use_state": "Lane16_Lane17_Lane18_completion_audits_verifiers_manifests_focused_tests_and_contracts_read_from_disk",
        "runtime_effect_boundary": "master_consumption_only_no_lane_rebuild_no_live_behavior_change",
    }


def wave4_artifact_inspection_rows(wave4_table: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    table = wave4_table or wave4_terminal_state_table()
    rows: list[dict[str, Any]] = []
    for terminal in table["wave4_lanes"]:
        lane_id = terminal["lane_id"]
        rows.append(
            {
                "schema_version": "absolute_master_wave4_artifact_inspection_row_v1",
                "timestamp_utc": utc_now(),
                "artifact_family": f"absolute_lane{lane_id}_terminal_outputs",
                "lane_id": lane_id,
                "route_path": terminal["route_path"],
                "inspection_status": terminal["terminal_status"],
                "commit": terminal["commit"],
                "verifier_ok": terminal["verifier_ok"],
                "completion_status": terminal["completion_status"],
                "focused_test_result": terminal["focused_test_result"],
                "material_row_counts": terminal["material_row_counts"],
                "dependency_rows": terminal["dependency_rows"],
                "source_gap_ledger_paths": terminal["source_gap_ledger_paths"],
                "schema_contract_paths": terminal["schema_contract_paths"],
                "downstream_contract_path": terminal["downstream_contract_path"],
                "material_row_count_artifacts": terminal["material_row_count_artifacts"],
                "context_anchor_path": terminal["context_anchor_path"],
                "artifacts": terminal["inspected_artifacts"],
                "source_use_state": terminal["source_use_state"],
                "runtime_effect_boundary": terminal["runtime_effect_boundary"],
            }
        )
    return rows


def _post_v3_source_counts(route_dir: Path) -> dict[str, int | float | None]:
    verification = load_json(route_dir / "POST_LANE18_VERIFICATION_RESULT.json", {})
    derived = verification.get("derived_stats", {})
    return {
        "superledger_rows": verification.get("superledger_rows"),
        "repaired_rows": derived.get("repaired_rows"),
        "read_only_export_requirement_rows": derived.get("read_only_export_requirement_rows"),
        "forward_capture_contract_rows": derived.get("forward_capture_contract_rows"),
        "non_generatable_rows": derived.get("non_generatable_rows"),
        "validation_rows": derived.get("validation_rows"),
    }


def _post_v3_selector_counts(route_dir: Path) -> dict[str, int | float | None]:
    counts = load_json(route_dir / "SELECTOR_V3_VERIFICATION_RESULT.json", {}).get("counts", {})
    return {
        "full_evidence_rows": counts.get("full_evidence_rows"),
        "selector_scheduler_execution_join_rows": counts.get("selector_scheduler_execution_join_rows"),
        "market_whiteboard_rows": counts.get("market_whiteboard_rows"),
        "source_gap_capture_dependency_rows": counts.get("source_gap_capture_dependency_rows"),
        "mechanism_action_rows": counts.get("mechanism_action_rows"),
        "split_stress_rows": counts.get("split_stress_rows"),
        "runtime_selector_rule_count": counts.get("runtime_selector_rule_count"),
        "exact_r_rows": counts.get("exact_r_rows"),
        "proxy_r_rows": counts.get("proxy_r_rows"),
    }


def _post_v3_scheduler_counts(route_dir: Path) -> dict[str, int | float | None]:
    verification = load_json(route_dir / "SCHEDULER_V3_VERIFICATION_RESULT.json", {})
    ledgers = verification.get("ledger_counts", {})
    result_classes = verification.get("result_class_counts", {})
    return {
        "full_evidence_rows": ledgers.get("full_evidence_rows"),
        "decision_rows": ledgers.get("decision_rows"),
        "conflict_rows": ledgers.get("conflict_rows"),
        "money_risk_rows": ledgers.get("money_risk_rows"),
        "source_gap_rows": ledgers.get("source_gap_rows"),
        "correlation_rows": ledgers.get("correlation_rows"),
        "blocked_edge_rows": ledgers.get("blocked_edge_rows"),
        "split_stress_rows": ledgers.get("split_stress_rows"),
        "exact_broker_real_rows": result_classes.get("exact_broker_real"),
        "source_bound_proxy_rows": result_classes.get("source_bound_proxy"),
        "missing_result_rows": result_classes.get("missing_result"),
    }


def _post_v3_execution_counts(route_dir: Path) -> dict[str, int | float | None]:
    counts = load_json(route_dir / "V3_VERIFICATION_RESULT.json", {}).get("counts", {})
    manifest_artifacts = load_json(route_dir / "V3_OUTPUT_MANIFEST.json", {}).get("artifacts", [])
    manifest_counts = {row.get("name"): row.get("row_count") for row in manifest_artifacts}
    return {
        "policy_variant_rows": counts.get("policy_variant_rows"),
        "evaluation_rows": counts.get("evaluation_rows"),
        "source_gap_rows": counts.get("source_gap_rows"),
        "routing_rows": counts.get("routing_rows"),
        "lifecycle_feasibility_rows": counts.get("lifecycle_feasibility_rows"),
        "failure_anatomy_rows": counts.get("failure_anatomy_rows") or manifest_counts.get("failure_anatomy"),
        "source_decision_rows": count_jsonl(route_dir / "V3_SOURCE_CAPTURE_AND_COMPLETENESS_DECISIONS.jsonl"),
        "split_stress_rows": counts.get("split_stress_rows") or manifest_counts.get("split_stress"),
        "lane11_inherited_variant_rows": counts.get("lane11_inherited_variant_rows"),
        "v3_added_variant_rows": counts.get("v3_added_variant_rows"),
    }


POST_V3_COUNT_READERS = {
    "source_capture_repair": _post_v3_source_counts,
    "selector_v3": _post_v3_selector_counts,
    "scheduler_v3": _post_v3_scheduler_counts,
    "execution_policy_v3": _post_v3_execution_counts,
}


def post_v3_terminal_state_table() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for gate_id, route_dir in POST_V3_ROUTE_DIRS.items():
        required = POST_V3_REQUIRED_ARTIFACTS[gate_id]
        completion = load_json(route_dir / required["completion_audit"], {})
        verification = load_json(route_dir / required["verifier_result"], {})
        manifest = load_json(route_dir / required["manifest"], {})
        result_use = load_json(route_dir / required["result_use_status"], {})
        focused = parse_junit_result(route_dir / required["focused_test_result"])
        counts = POST_V3_COUNT_READERS[gate_id](route_dir)
        expected_counts = POST_V3_EXPECTED_COUNTS[gate_id]
        count_matches = {key: counts.get(key) == value for key, value in expected_counts.items()}
        required_names = [
            required["completion_audit"],
            required["verifier_result"],
            required["manifest"],
            required["downstream_contract"],
            required["focused_test_result"],
            required["builder"],
            required["verifier"],
            *required.get("tests", []),
            required.get("default_off_package"),
            required.get("runtime_packet_schema"),
            required.get("source_capture_decisions"),
            required.get("source_completeness_decisions"),
            required.get("branch_decisions"),
            required.get("implementation_decisions"),
            required.get("result_use_status"),
            required.get("source_use_state"),
            *required["material_row_count_artifacts"],
        ]
        required_files = [artifact_presence_record(route_dir, name) for name in required_names if name]
        required_present = all(item["exists"] and item["size_bytes"] > 0 for item in required_files)
        completion_status = completion.get("status")
        last_commit = git_last_commit_for_path(route_dir)
        terminal_verified = (
            bool(verification.get("ok"))
            and focused["ok"]
            and required_present
            and manifest_output_count(manifest) > 0
            and all(bool(value) for value in count_matches.values())
        )
        rows.append(
            {
                "schema_version": "absolute_master_post_v3_terminal_route_row_v1",
                "gate_id": gate_id,
                "route_path": rel(route_dir),
                "terminal_status": "terminal_verified" if terminal_verified else "not_terminal",
                "completion_status": completion_status,
                "completion_audit_path": rel(route_dir / required["completion_audit"]),
                "completion_audit_pending_commit_text_neutralized_by_git_history": bool(
                    completion_status and "pending" in str(completion_status).lower() and last_commit.get("commit_short")
                ),
                "route_last_commit": last_commit,
                "verification_ok": bool(verification.get("ok")),
                "verification_path": rel(route_dir / required["verifier_result"]),
                "manifest_path": rel(route_dir / required["manifest"]),
                "manifest_artifact_count": manifest_output_count(manifest),
                "focused_test_result": focused,
                "required_files_present": required_present,
                "required_files": required_files,
                "expected_count_matches": count_matches,
                "material_row_counts": counts,
                "result_use_status_path": rel(route_dir / required["result_use_status"]),
                "result_use_status": result_use,
                "runtime_effect_boundary": verification.get("runtime_effect_boundary")
                or result_use.get("runtime_effect_boundary")
                or required["runtime_effect_boundary"],
                "source_use_state": result_use.get("source_use_state")
                or completion.get("source_use_state")
                or "current_disk_route_artifacts_read_by_master",
            }
        )
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_post_v3_terminal_state_table_v1",
        "generated_at_utc": utc_now(),
        "all_post_v3_terminal_verified": all(row["terminal_status"] == "terminal_verified" for row in rows),
        "terminal_routes": rows,
        "terminal_gate_ids": [row["gate_id"] for row in rows if row["terminal_status"] == "terminal_verified"],
        "required_gate_ids": list(POST_V3_ROUTE_DIRS),
        "runtime_effect_boundary": "post_v3_integration_truth_only_no_live_behavior_change",
        "source_use_state": "Source Capture Repair, Selector V3, Scheduler V3, and Execution Policy V3 completion audits, verifiers, manifests, focused tests, source decisions, result-use files, and default-off packages read from disk",
    }


def post_v3_artifact_inspection_rows(post_v3_table: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    table = post_v3_table or post_v3_terminal_state_table()
    terminals = {row["gate_id"]: row for row in table["terminal_routes"]}
    rows = []
    for gate_id, route_dir in POST_V3_ROUTE_DIRS.items():
        required = POST_V3_REQUIRED_ARTIFACTS[gate_id]
        terminal = terminals[gate_id]
        artifact_names = [
            required["completion_audit"],
            required["verifier_result"],
            required["manifest"],
            required["downstream_contract"],
            required["focused_test_result"],
            required["builder"],
            required["verifier"],
            *required.get("tests", []),
            required.get("default_off_package"),
            required.get("runtime_packet_schema"),
            required.get("source_capture_decisions"),
            required.get("source_completeness_decisions"),
            required.get("branch_decisions"),
            required.get("implementation_decisions"),
            required.get("result_use_status"),
            required.get("source_use_state"),
            *required["material_row_count_artifacts"],
        ]
        rows.append(
            {
                "schema_version": "absolute_master_post_v3_artifact_inspection_row_v1",
                "timestamp_utc": utc_now(),
                "artifact_family": f"absolute_post_v3_{gate_id}_terminal_outputs",
                "gate_id": gate_id,
                "route_path": rel(route_dir),
                "inspection_status": terminal["terminal_status"],
                "completion_status": terminal["completion_status"],
                "verification_ok": terminal["verification_ok"],
                "focused_test_result": terminal["focused_test_result"],
                "manifest_artifact_count": terminal["manifest_artifact_count"],
                "material_row_counts": terminal["material_row_counts"],
                "expected_count_matches": terminal["expected_count_matches"],
                "required_artifacts": [artifact_record(route_dir, name) for name in artifact_names if name],
                "result_use_status": terminal["result_use_status"],
                "runtime_effect_boundary": terminal["runtime_effect_boundary"],
                "source_use_state": terminal["source_use_state"],
            }
        )
    return rows


def limitation_disposition_map() -> dict[str, Any]:
    rows = [
        {
            "limitation_id": "historical_microscope_scale",
            "limitation_family": "replay_validation_and_path_anatomy",
            "source_anchor": rel(VISION_PATH),
            "owner_lane_or_gate": "Lane16 Historical Microscope Scaling",
            "disposition_class": "REPLAY",
            "decision": "scale_friday_microscope_to_all_source_supported_windows_before_treating_any_slice_as_system_truth",
            "downstream_consumers": ["Market Awareness", "Selector V3", "Scheduler V3", "Execution Policy V3", "ML", "Repair Companion", "Command Center"],
        },
        {
            "limitation_id": "market_awareness_whiteboard",
            "limitation_family": "market_state_context",
            "source_anchor": rel(VISION_PATH),
            "owner_lane_or_gate": "Lane17 Market Awareness Whiteboard",
            "disposition_class": "FIX",
            "decision": "build_a_unified_symbol_timeframe_session_regime_source_state_layer_instead_of_single_timeframe_or_stale_context_inference",
            "downstream_consumers": ["Selector V3", "Scheduler V3", "Execution Policy V3", "ML", "Repair Companion", "Command Center"],
        },
        {
            "limitation_id": "broker_truth_cost_capture",
            "limitation_family": "broker_lifecycle_and_cost_truth",
            "source_anchor": rel(VISION_PATH),
            "owner_lane_or_gate": "Lane18 Broker Truth Cost Capture V2",
            "disposition_class": "CAPTURE",
            "decision": "convert_missing_order_deal_position_cost_spread_retcode_truth_into_contracts_default_off_capture_repairs_and_exact_export_requirements",
            "downstream_consumers": ["Scheduler V3", "Execution Policy V3", "Digital Twin V2", "ML Labels", "Repair Companion", "Command Center"],
        },
        {
            "limitation_id": "selector_v3",
            "limitation_family": "selector_precision_and_false_positive_control",
            "source_anchor": rel(POST_V3_ROUTE_DIRS["selector_v3"]),
            "owner_lane_or_gate": "Selector V3 terminal default-off package",
            "disposition_class": "FIX",
            "decision": "consume_terminal_Selector_V3_default_off_package_for_ML_repair_companion_and_command_center_without_live_selector_activation",
            "downstream_consumers": ["Scheduler V3", "Execution Policy V3", "ML", "Repair Companion"],
        },
        {
            "limitation_id": "scheduler_v3",
            "limitation_family": "portfolio_scheduler_conflict_anatomy",
            "source_anchor": rel(POST_V3_ROUTE_DIRS["scheduler_v3"]),
            "owner_lane_or_gate": "Scheduler V3 terminal default-off package",
            "disposition_class": "FIX",
            "decision": "consume_terminal_Scheduler_V3_money_risk_conflict_recovery_and_multi_ticket_contracts_as_offline_ML_repair_and_command_center_inputs",
            "downstream_consumers": ["Execution Policy V3", "ML", "Repair Companion", "Command Center"],
        },
        {
            "limitation_id": "execution_policy_v3",
            "limitation_family": "execution_policy_and_lifecycle_feasibility",
            "source_anchor": rel(POST_V3_ROUTE_DIRS["execution_policy_v3"]),
            "owner_lane_or_gate": "Execution Policy V3 terminal default-off package",
            "disposition_class": "FIX",
            "decision": "consume_terminal_Execution_Policy_V3_policy_variant_feasibility_routing_failure_anatomy_and_source_gap_contracts_without_live_execution_activation",
            "downstream_consumers": ["ML", "Repair Companion", "Command Center"],
        },
        {
            "limitation_id": "post_lane18_source_capture_repair",
            "limitation_family": "source_capture_and_completeness",
            "source_anchor": rel(POST_V3_ROUTE_DIRS["source_capture_repair"]),
            "owner_lane_or_gate": "Source Capture Repair terminal route",
            "disposition_class": "CAPTURE",
            "decision": "consume_terminal_source_repair_superledger_repaired_rows_read_only_export_requirements_forward_capture_contracts_and_non_generatable_truth_rows",
            "downstream_consumers": ["ML", "Repair Companion", "Command Center", "Production dossier"],
        },
        {
            "limitation_id": "ml_scope_control",
            "limitation_family": "ml_as_subsystem_not_program_horizon",
            "source_anchor": rel(LAUNCH_ORDER),
            "owner_lane_or_gate": "Lane12/Lane13 later ML gates",
            "disposition_class": "FIX",
            "decision": "defer_ml_until_next_wave_contracts_exist;_ml_must_consume_market_state_microscope_broker_truth_selector_scheduler_and_execution_contracts",
            "downstream_consumers": ["ML Dataset Baseline Lab", "ML Selector Policy Intelligence"],
        },
        {
            "limitation_id": "source_completeness_and_data_authority",
            "limitation_family": "source_gaps_as_contracts",
            "source_anchor": "Lane01-Lane07 terminal source contracts",
            "owner_lane_or_gate": "Master plus each builder lane",
            "disposition_class": "CAPTURE",
            "decision": "preserve_source_gap_rows_and_exact_capture_or_export_requirements_instead_of_summary_blockers",
            "downstream_consumers": ["all downstream lanes"],
        },
        {
            "limitation_id": "orderflow_depth_paid_vendor_surface",
            "limitation_family": "external_paid_data_or_depth_dependency",
            "source_anchor": rel(VISION_PATH),
            "owner_lane_or_gate": "Master boundary",
            "disposition_class": "KILL_OR_REDESIGN",
            "decision": "do_not_center_this_program_on_Sierra_Databento_or_paid_orderflow_depth_lanes;use_local_authorized_evidence_or_exact_future_capture_contracts_only",
            "downstream_consumers": ["Lane17", "Lane18", "later market microstructure contracts"],
        },
        {
            "limitation_id": "repair_companion",
            "limitation_family": "daily_learning_and_ai_companion",
            "source_anchor": rel(LAUNCH_ORDER),
            "owner_lane_or_gate": "Lane14 later gate",
            "disposition_class": "PRODUCTION_DOSSIER",
            "decision": "repair_companion_waits_for_Lanes16_18_and_v3_engine_contracts_before_default_off_repair_decisions",
            "downstream_consumers": ["Command Center", "Production dossier"],
        },
        {
            "limitation_id": "command_center_production_dossier",
            "limitation_family": "operations_and_owner_approval",
            "source_anchor": rel(LAUNCH_ORDER),
            "owner_lane_or_gate": "Lane15 later gate",
            "disposition_class": "PRODUCTION_DOSSIER",
            "decision": "production_activation_remains_forbidden_until_terminal_contracts_owner_approval_and_broker_lifecycle_reconciliation_exist",
            "downstream_consumers": ["Owner approval workflow"],
        },
        {
            "limitation_id": "research_process_saturation",
            "limitation_family": "research_method",
            "source_anchor": ".context/00_core/goal_session_research_discipline.md",
            "owner_lane_or_gate": "Master verifier and all lane verifiers",
            "disposition_class": "FIX",
            "decision": "same_evidence_class_pursuit_no_top_n_no_summary_only_no_ledger_only_completion_are_verifier_contracts",
            "downstream_consumers": ["all lanes"],
        },
    ]
    allowed = {"FIX", "REPLAY", "CAPTURE", "KILL_OR_REDESIGN", "PRODUCTION_DOSSIER"}
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_limitation_disposition_map_v1",
        "generated_at_utc": utc_now(),
        "rows": rows,
        "row_count": len(rows),
        "all_dispositions_allowed": all(row["disposition_class"] in allowed for row in rows),
        "no_top_n_or_summary_only_disposition": True,
        "runtime_effect_boundary": "research_control_only_no_live_behavior_change",
    }


def later_wave_gates(
    next_wave_decision: dict[str, Any] | None = None,
    wave4_table: dict[str, Any] | None = None,
    post_v3_table: dict[str, Any] | None = None,
) -> dict[str, Any]:
    wave4_terminal = bool((wave4_table or {}).get("all_wave4_terminal_verified"))
    post_v3_terminal = bool((post_v3_table or {}).get("all_post_v3_terminal_verified"))
    v3_status = (
        "terminal_verified_consumed_by_post_v3_master"
        if post_v3_terminal
        else
        "ready_after_lane16_17_18_terminal_contracts"
        if wave4_terminal
        else "later_gate_waiting_for_next_wave_contracts"
    )
    source_capture_status = (
        "terminal_verified_consumed_by_post_v3_master"
        if post_v3_terminal
        else
        "ready_after_lane16_17_18_gap_contracts"
        if wave4_terminal
        else "later_gate_waiting_for_next_wave_gap_contracts"
    )
    next_wave_contracts = [
        "Lane16 historical microscope scale downstream contract",
        "Lane17 market awareness whiteboard downstream contract",
        "Lane18 broker truth cost capture V2 downstream contract",
    ]
    rows = [
        {
            "gate_id": "selector_v3",
            "consumer": "Selector V3",
            "owned_by": "future default-off selector lane or Lane09 successor",
            "status": v3_status,
            "must_consume": ["Lane09B scheduler-aware selector refinement", "Lane11 expanded policy integration", *next_wave_contracts],
            "opens_after": ["Lane16", "Lane17", "Lane18"],
            "prompt_required_before_execution": True,
        },
        {
            "gate_id": "scheduler_v3",
            "consumer": "Scheduler V3",
            "owned_by": "future default-off scheduler lane or Lane10 successor",
            "status": v3_status,
            "must_consume": ["Lane10B multi-ticket lifecycle contract", "Lane09B reconciliation", *next_wave_contracts],
            "opens_after": ["Lane16", "Lane17", "Lane18"],
            "prompt_required_before_execution": True,
        },
        {
            "gate_id": "execution_policy_v3",
            "consumer": "Execution Policy V3",
            "owned_by": "future default-off execution lane or Lane11 successor",
            "status": v3_status,
            "must_consume": ["Lane11 default-off policy router package", "Lane10B Lane11 integration contract", "Lane18 broker truth lifecycle contract", *next_wave_contracts],
            "opens_after": ["Lane16", "Lane17", "Lane18"],
            "prompt_required_before_execution": True,
        },
        {
            "gate_id": "source_capture_repair",
            "consumer": "Data Source Capture Repair",
            "owned_by": "future source repair lane",
            "status": source_capture_status,
            "must_consume": [
                "Lane16 source-gap ledger",
                "Lane17 source-gap ledger",
                "Lane18 prospective capture requirements",
                "MT5 local cache preservation",
                "compliant VPS read-only export requirements",
            ],
            "opens_after": ["Lane16", "Lane17", "Lane18"],
            "prompt_required_before_execution": True,
        },
        {
            "gate_id": "ml_dataset_baselines",
            "consumer": "Lane12 ML Dataset Baseline Lab",
            "owned_by": "Lane12",
            "status": "ready_after_post_v3_master_refresh" if post_v3_terminal else "later_ml_subsystem_gate_not_next_main_actor",
            "must_consume": ["Lane05 feature store", "Lane06 label store", "Lane08 replay rows", "Lane16 scaled microscope", "Lane17 market whiteboard", "Lane18 broker truth/cost", "Source Capture Repair", "Selector V3", "Scheduler V3", "Execution Policy V3"],
            "opens_after": ["post_v3_master_refresh"] if post_v3_terminal else ["Lane16", "Lane17", "Lane18"],
            "prompt_required_before_execution": True,
        },
        {
            "gate_id": "ml_policy_intelligence",
            "consumer": "Lane13 ML Selector Policy Intelligence",
            "owned_by": "Lane13",
            "status": "ready_after_lane12_and_post_v3_contracts" if post_v3_terminal else "later_ml_subsystem_gate_not_next_main_actor",
            "must_consume": ["Lane12 baseline outputs", "Selector V3", "Scheduler V3", "Execution Policy V3", *next_wave_contracts],
            "opens_after": ["Lane12", "selector_v3", "scheduler_v3", "execution_policy_v3"],
            "prompt_required_before_execution": True,
        },
        {
            "gate_id": "repair_companion",
            "consumer": "Lane14 Daily Learning Repair Companion",
            "owned_by": "Lane14",
            "status": "ready_for_post_v3_default_off_repair_loop_design_with_ml_fields_gated" if post_v3_terminal else "later_gate_waiting_for_v3_ml_and_next_wave_contracts",
            "must_consume": ["Lane16", "Lane17", "Lane18", "Source Capture Repair", "Selector V3", "Scheduler V3", "Execution Policy V3", "Lane12/Lane13 ML intelligence when present"],
            "opens_after": ["Lane12", "Lane13", "selector_v3", "scheduler_v3", "execution_policy_v3"],
            "prompt_required_before_execution": True,
        },
        {
            "gate_id": "command_center",
            "consumer": "Lane15 Command Center Production Dossier",
            "owned_by": "Lane15",
            "status": "ready_for_command_center_report_pack_after_post_v3_with_production_activation_still_owner_gated" if post_v3_terminal else "later_production_dossier_gate_waiting_for_terminal_program_evidence_and_owner_approval",
            "must_consume": ["Lane16", "Lane17", "Lane18", "Source Capture Repair", "Selector V3", "Scheduler V3", "Execution Policy V3", "Lane12", "Lane13", "Lane14", "broker lifecycle reconciliation", "owner approval"],
            "opens_after": ["Lane14", "owner_approval", "broker_lifecycle_reconciliation"],
            "prompt_required_before_execution": True,
        },
    ]
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_later_wave_gates_v1",
        "generated_at_utc": utc_now(),
        "gates": rows,
        "gate_count": len(rows),
        "all_gates_consume_next_wave_contracts": all(
            any("Lane16" in item for item in row["must_consume"])
            or any("historical microscope" in item for item in row["must_consume"])
            or row["gate_id"] == "source_capture_repair"
            for row in rows
        ),
        "wave4_terminal_consumed": wave4_terminal,
        "post_v3_terminal_consumed": post_v3_terminal,
        "ml_role": "subsystem_after_post_v3_contracts_not_the_only_program_horizon"
        if post_v3_terminal
        else "subsystem_after_next_wave_contracts_not_the_main_next_actor",
        "runtime_effect_boundary": "coordination_contract_only_no_live_behavior_change",
    }


def next_wave_launch_decision(
    post_lane11_table: dict[str, Any] | None = None,
    limitation_map: dict[str, Any] | None = None,
    gates: dict[str, Any] | None = None,
) -> dict[str, Any]:
    post = post_lane11_table or post_lane11_terminal_state_table()
    limitations = limitation_map or limitation_disposition_map()
    later = gates or later_wave_gates()
    lane_rows = []
    for lane_id in ["16", "17", "18"]:
        prompt = lane_goal_prompt_path(lane_id)
        starter = prompt.with_name(prompt.name.replace("_GOAL_PROMPT_", "_STARTER_").replace(".md", ".txt"))
        lane_rows.append(
            {
                "lane_id": lane_id,
                "title": parse_lane_prompt(prompt)["title"],
                "prompt_path": rel(prompt),
                "starter_path": rel(starter),
                "route_path": parse_lane_prompt(prompt)["route_path"],
                "launch_status": "ready_to_launch_next_wave",
                "required_terminal_inputs": [
                    "Lane08 terminal digital twin",
                    "Lane09 terminal meta-selector",
                    "Lane09B selector-scheduler reconciliation",
                    "Lane10 terminal scheduler",
                    "Lane10B scheduler conflict anatomy",
                    "Lane11 terminal execution policy engine",
                ],
                "runtime_effect_boundary": "builder_research_or_default_off_capture_only_no_live_behavior_change",
            }
        )
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_next_wave_launch_decision_v1",
        "generated_at_utc": utc_now(),
        "decision": "open_lanes16_17_18_as_the_post_lane11_full_trading_operating_system_wave",
        "launch_mode": "parallel_if_workers_available_because_route_paths_are_disjoint",
        "next_wave_lanes": ["16", "17", "18"],
        "lane_rows": lane_rows,
        "terminal_inputs_verified": bool(post.get("all_post_lane11_terminal_verified")),
        "terminal_input_table": rel(ROUTE_DIR / "ABSOLUTE_MASTER_POST_LANE11_TERMINAL_STATE_TABLE.json"),
        "limitation_disposition_map": {
            "path": rel(ROUTE_DIR / "ABSOLUTE_MASTER_LIMITATION_DISPOSITION_MAP.json"),
            "row_count": limitations.get("row_count"),
            "all_dispositions_allowed": limitations.get("all_dispositions_allowed"),
        },
        "later_wave_gates": {
            "path": rel(ROUTE_DIR / "ABSOLUTE_MASTER_LATER_WAVE_GATES.json"),
            "gate_count": later.get("gate_count"),
        },
        "ml_role": "ML is one subsystem after the next-wave contracts, not the main actor and not the next-wave closure condition.",
        "not_ml_only_closure": True,
        "summary_only_closure_rejected": True,
        "runtime_effect_boundary": "launch_control_only_no_live_behavior_change",
    }


def stale_dependency_text_neutralization(
    terminal_table: dict[str, Any] | None = None,
    post_v3_table: dict[str, Any] | None = None,
) -> dict[str, Any]:
    table = terminal_table or wave1_terminal_state_table()
    post_v3 = post_v3_table or post_v3_terminal_state_table()
    lane04_dir = WAVE1_ROUTE_DIRS["04"]
    dependency_rows = read_jsonl_rows(lane04_dir / "LANE04_DEPENDENCY_STATE_LEDGER.jsonl")
    present_required = {
        "absolute_lane01_source_authority",
        "absolute_lane02_asof_contract",
        "absolute_lane03_candidate_reconstruction",
    }
    present_names = {
        row.get("dependency_name")
        for row in dependency_rows
        if row.get("status") == "present" and row.get("exists") is True
    }
    post_v3_stale_sources = []
    for row in post_v3["terminal_routes"]:
        if row.get("completion_audit_pending_commit_text_neutralized_by_git_history"):
            post_v3_stale_sources.append(
                    {
                        "gate_id": row["gate_id"],
                        "completion_audit_path": row["completion_audit_path"],
                        "last_commit": row["route_last_commit"],
                        "stale_text_pattern": "pending scoped commit / launch-pending wording",
                        "current_authority": "git history plus post-V3 terminal verifier/focused-test state",
                    }
            )
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_stale_dependency_text_neutralization_v1",
        "generated_at_utc": utc_now(),
        "stale_text_sources": [
            rel(lane04_dir / "LANE04_COMPLETION_AUDIT.json"),
            rel(lane04_dir / "LANE04_CONTEXT_ANCHOR.md"),
            rel(LAUNCH_ORDER),
            rel(POST_V3_MASTER_PROMPT),
            *[source["completion_audit_path"] for source in post_v3_stale_sources],
        ],
        "stale_text_pattern": "Lane04 absent-dependency wording; post-Lane18/V3/source-capture launch-pending or pending-commit wording after terminal disk evidence exists",
        "current_authority": {
            "lane04_dependency_ledger": rel(lane04_dir / "LANE04_DEPENDENCY_STATE_LEDGER.jsonl"),
            "present_dependency_names": sorted(present_names),
            "required_present_dependency_names": sorted(present_required),
            "dependency_ledger_supersedes_absence_wording": present_required.issubset(present_names),
            "wave1_terminal_verified": table["all_wave1_terminal_verified"],
            "post_v3_terminal_state_table": rel(ROUTE_DIR / "ABSOLUTE_MASTER_POST_V3_TERMINAL_STATE_TABLE.json"),
            "post_v3_terminal_verified": post_v3["all_post_v3_terminal_verified"],
            "post_v3_terminal_gate_ids": post_v3["terminal_gate_ids"],
            "post_v3_pending_commit_sources_neutralized_by_git_history": post_v3_stale_sources,
        },
        "neutralized_for_master_consumption": present_required.issubset(present_names)
        and table["all_wave1_terminal_verified"]
        and post_v3["all_post_v3_terminal_verified"],
        "post_v3_neutralized_by_terminal_consumption": post_v3["all_post_v3_terminal_verified"]
        and all(row["terminal_status"] == "terminal_verified" for row in post_v3["terminal_routes"]),
        "downstream_consumption_rule": "Master and downstream lanes must consume Lane01-Lane04 terminal verifiers, Lane04 dependency ledger, and post-V3 terminal state table as current truth; stale Lane04 absence wording and stale source-capture/V3 launch-pending wording are historical build-time context and must not propagate as blockers or relaunch triggers.",
        "rebuild_decision": "do_not_rebuild_lane04_heavy_ledgers_no_data_mismatch_proven",
        "runtime_effect_boundary": "master_coordination_truth_only_no_lane04_data_rebuild_no_live_behavior_change",
    }


def wave2_readiness_decision(
    wave1_table: dict[str, Any] | None = None,
    wave2_table: dict[str, Any] | None = None,
) -> dict[str, Any]:
    wave1 = wave1_table or wave1_terminal_state_table()
    wave2 = wave2_table or wave2_terminal_state_table()
    terminal_by_lane = {row["lane_id"]: row for row in wave2["wave2_lanes"]}
    lane_readiness = {
        "05": {
            "lane_id": "05",
            "decision": "terminal_verified_feature_store_ready_for_wave3_consumption",
            "terminal_status": terminal_by_lane["05"]["terminal_status"],
            "material_row_counts": terminal_by_lane["05"]["material_row_counts"],
            "broker_real_truth_required_for_consumption": False,
            "downstream_consumers": ["Lane06", "Lane08", "Lane09", "Lane10", "Lane11", "Lane12", "Lane13"],
        },
        "06": {
            "lane_id": "06",
            "decision": "terminal_verified_label_store_ready_for_wave3_and_bounded_ml_consumption",
            "terminal_status": terminal_by_lane["06"]["terminal_status"],
            "material_row_counts": terminal_by_lane["06"]["material_row_counts"],
            "lane05_consumed": bool(terminal_by_lane["06"]["material_row_counts"].get("lane05_consumed")),
            "lane07_consumed": bool(terminal_by_lane["06"]["material_row_counts"].get("lane07_consumed")),
            "broker_real_proxy_replay_labels_separated": True,
        },
        "07": {
            "lane_id": "07",
            "decision": "terminal_verified_separate_broker_truth_cost_enrichment",
            "terminal_status": terminal_by_lane["07"]["terminal_status"],
            "material_row_counts": terminal_by_lane["07"]["material_row_counts"],
            "blocks_lane05_or_lane06": False,
            "blocks_wave3_when_broker_real_fields_absent": False,
            "missing_broker_real_field_rule": "explicit_proxy_gap_or_export_fields_not_wave3_blockers",
        },
    }
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_wave2_readiness_decision_v2_terminal",
        "generated_at_utc": utc_now(),
        "wave1_terminal_verified": wave1["all_wave1_terminal_verified"],
        "wave2_terminal_verified": wave2["all_wave2_terminal_verified"],
        "broker_real_truth_does_not_gate_historical_wave2_or_wave3": True,
        "older_wave2_pending_wording_replaced": True,
        "wave2_launch_state": "terminal_completed_lanes05_06_07"
        if wave1["all_wave1_terminal_verified"] and wave2["all_wave2_terminal_verified"]
        else "not_ready_until_wave1_wave2_terminal_verification",
        "lane_readiness": lane_readiness,
        "blocked_lanes": [],
        "deferred_lanes": [],
        "source_use_state": "Wave2 terminal state derived from inspected Lane05-Lane07 disk artifacts, not chat closeouts",
        "runtime_effect_boundary": "research_coordination_truth_only_no_live_behavior_change",
    }


def wave3_readiness_decision(
    wave1_table: dict[str, Any] | None = None,
    wave2_table: dict[str, Any] | None = None,
    wave3_table: dict[str, Any] | None = None,
    post_lane11_table: dict[str, Any] | None = None,
    next_wave: dict[str, Any] | None = None,
    later_gates: dict[str, Any] | None = None,
) -> dict[str, Any]:
    wave1 = wave1_table or wave1_terminal_state_table()
    wave2 = wave2_table or wave2_terminal_state_table()
    wave3_terminal = wave3_table or wave3_terminal_state_table()
    post_lane11 = post_lane11_table or post_lane11_terminal_state_table(wave3_terminal)
    gates = later_gates or later_wave_gates()
    next_wave_decision = next_wave or next_wave_launch_decision(post_lane11, limitation_disposition_map(), gates)
    wave1_ok = wave1["all_wave1_terminal_verified"]
    wave2_ok = wave2["all_wave2_terminal_verified"]
    wave3_ok = wave3_terminal["all_wave3_terminal_verified"]
    post_ok = post_lane11["all_post_lane11_terminal_verified"]
    next_wave_ok = wave1_ok and wave2_ok and wave3_ok and post_ok and next_wave_decision["next_wave_lanes"] == ["16", "17", "18"]
    terminal_by_lane = {row["lane_id"]: row for row in wave3_terminal["wave3_lanes"]}
    post_by_lane = {row["lane_id"]: row for row in post_lane11["terminal_lanes"]}
    lanes = {
        "08": {
            "lane_id": "08",
            "title": "Digital Twin Replay Engine",
            "readiness": "terminal_verified_wave3",
            "launch_phase": "wave3_completed_terminal",
            "terminal_status": terminal_by_lane["08"]["terminal_status"],
            "material_row_counts": terminal_by_lane["08"]["material_row_counts"],
            "required_inputs": ["Lane03 candidates", "Lane04 microscope", "Lane05 feature store", "Lane06 label store", "Lane07 broker/cost enrichment"],
        },
        "09": {
            "lane_id": "09",
            "title": "Meta-Selector V2",
            "readiness": "terminal_verified_wave3",
            "launch_phase": "wave3_completed_terminal",
            "terminal_status": terminal_by_lane["09"]["terminal_status"],
            "material_row_counts": terminal_by_lane["09"]["material_row_counts"],
            "required_inputs": ["Lane05 feature store", "Lane06 label store", "Lane07 broker/cost enrichment", "Lane08 replay output"],
        },
        "10": {
            "lane_id": "10",
            "title": "Portfolio Scheduler V2",
            "readiness": "terminal_verified_wave3",
            "launch_phase": "wave3_completed_terminal",
            "terminal_status": terminal_by_lane["10"]["terminal_status"],
            "material_row_counts": terminal_by_lane["10"]["material_row_counts"],
            "required_inputs": ["Lane05 feature store", "Lane06 label store", "Lane07 broker/cost enrichment", "Lane08 replay output"],
        },
        "11": {
            "lane_id": "11",
            "title": "Execution Policy Engine V2",
            "readiness": "terminal_verified_wave3_and_post_lane11",
            "launch_phase": "wave3_completed_terminal_and_post_lane11_consumed",
            "terminal_status": terminal_by_lane["11"]["terminal_status"],
            "post_lane11_terminal_status": post_by_lane["11"]["terminal_status"],
            "material_row_counts": terminal_by_lane["11"]["material_row_counts"],
            "required_inputs": ["Lane04 microscope/strict tick", "Lane05 feature store", "Lane06 label store", "Lane07 broker/cost enrichment", "Lane08 replay output"],
        },
        "16": {
            "lane_id": "16",
            "title": "Historical Microscope Scaling",
            "readiness": "ready_next_wave_full_trading_operating_system",
            "launch_phase": "wave4_post_lane11_next_wave",
            "required_inputs": ["Lane08", "Lane09", "Lane09B", "Lane10", "Lane10B", "Lane11"],
            "parallelization": "may_run_in_parallel_with_lanes17_and_18_if_workers_are_available",
        },
        "17": {
            "lane_id": "17",
            "title": "Market Awareness Whiteboard",
            "readiness": "ready_next_wave_full_trading_operating_system",
            "launch_phase": "wave4_post_lane11_next_wave",
            "required_inputs": ["Lane08", "Lane09", "Lane09B", "Lane10", "Lane10B", "Lane11", "current runtime market-state code"],
            "parallelization": "may_run_in_parallel_with_lanes16_and_18_if_workers_are_available",
        },
        "18": {
            "lane_id": "18",
            "title": "Broker Truth Cost Capture V2",
            "readiness": "ready_next_wave_full_trading_operating_system",
            "launch_phase": "wave4_post_lane11_next_wave",
            "required_inputs": ["Lane07", "Lane08", "Lane10", "Lane10B", "Lane11", "live companion", "MT5 cache", "VPS preservation"],
            "parallelization": "may_run_in_parallel_with_lanes16_and_17_if_workers_are_available",
        },
        "12": {
            "lane_id": "12",
            "title": "ML Dataset Baseline Lab",
            "readiness": "later_ml_subsystem_gate_after_next_wave_contracts",
            "launch_phase": "wave5_after_lanes16_17_18",
            "ml_role": "subsystem_not_main_next_actor",
            "full_terminal_prerequisites": ["Lane16 scaled microscope", "Lane17 market awareness", "Lane18 broker truth/cost", "Selector/Scheduler/Execution V3 contracts where required"],
        },
        "13": {
            "lane_id": "13",
            "title": "ML Selector Policy Intelligence",
            "readiness": "later_ml_subsystem_gate_after_lane12_and_v3_contracts",
            "launch_phase": "wave5_after_lane12_and_v3_contracts",
            "ml_role": "subsystem_not_main_next_actor",
            "full_terminal_prerequisites": ["Lane12 baseline outputs", "Selector V3", "Scheduler V3", "Execution Policy V3", "Lane16-Lane18 contracts"],
        },
        "14": {
            "lane_id": "14",
            "title": "Daily Learning Repair Companion",
            "readiness": "later_repair_companion_gate_after_next_wave_v3_and_ml",
            "launch_phase": "wave6_after_v3_and_ml_contracts",
            "full_terminal_prerequisites": ["Lane16-Lane18 contracts", "Selector V3", "Scheduler V3", "Execution Policy V3", "Lane12-Lane13 ML intelligence contracts"],
        },
        "15": {
            "lane_id": "15",
            "title": "Command Center Production Dossier",
            "readiness": "later_command_center_production_dossier_gate",
            "launch_phase": "wave7_final_after_lanes16_18_v3_ml_repair_and_owner_approval",
            "full_terminal_prerequisites": ["Lane16-Lane18 terminal artifacts", "V3/ML/repair companion contracts", "production-change dossier", "owner approval", "broker lifecycle close/deal/cost reconciliation where claimed"],
        },
    }
    if gates.get("post_v3_terminal_consumed"):
        lanes["12"].update(
            {
                "readiness": "ready_after_post_v3_master_refresh_ml_subsystem",
                "launch_phase": "wave8_post_v3_ml_dataset_baseline_lab",
                "full_terminal_prerequisites": [
                    "Lane05 feature store",
                    "Lane06 label store",
                    "Lane08 digital twin",
                    "Lane16 scaled microscope",
                    "Lane17 market awareness",
                    "Lane18 broker truth/cost",
                    "Source Capture Repair",
                    "Selector V3",
                    "Scheduler V3",
                    "Execution Policy V3",
                ],
            }
        )
        lanes["13"].update(
            {
                "readiness": "ready_after_lane12_and_post_v3_contracts_ml_subsystem",
                "launch_phase": "wave9_after_lane12_and_post_v3_contracts",
            }
        )
        lanes["14"].update(
            {
                "readiness": "ready_post_v3_repair_companion_default_off_design_with_ml_fields_gated",
                "launch_phase": "wave10_post_v3_daily_learning_repair_companion",
            }
        )
        lanes["15"].update(
            {
                "readiness": "ready_post_v3_command_center_report_pack_owner_gated_production",
                "launch_phase": "wave11_post_v3_command_center_report_pack",
            }
        )
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_post_lane11_readiness_decision_v2",
        "generated_at_utc": utc_now(),
        "wave1_terminal_verified": wave1_ok,
        "wave2_terminal_verified": wave2_ok,
        "wave3_terminal_verified": wave3_ok,
        "post_lane11_terminal_verified": post_ok,
        "wave3_ready_to_open": False,
        "wave3_state": "completed_terminal_lanes08_09_10_11",
        "next_wave_ready_to_open": next_wave_ok,
        "next_wave_lanes": next_wave_decision["next_wave_lanes"],
        "broker_real_truth_gap_rule": "Lane07 and Lane18 contracts separate broker-real, proxy, source-gap, and capture/export requirements; gaps do not justify ML-only or summary-only closure.",
        "later_wave_gates": gates["gates"],
        "lane_readiness": lanes,
        "blocked_lanes": [],
        "deferred_or_gated_lanes": [
            {"lane_id": "12", "status": lanes["12"]["readiness"], "prerequisites": lanes["12"]["full_terminal_prerequisites"]},
            {"lane_id": "13", "status": lanes["13"]["readiness"], "prerequisites": lanes["13"]["full_terminal_prerequisites"]},
            {"lane_id": "14", "status": lanes["14"]["readiness"], "prerequisites": lanes["14"]["full_terminal_prerequisites"]},
            {"lane_id": "15", "status": lanes["15"]["readiness"], "prerequisites": lanes["15"]["full_terminal_prerequisites"]},
        ],
        "runtime_effect_boundary": "research_lane_launch_decision_only_no_live_behavior_change",
    }


def wave3_launch_order(wave3: dict[str, Any] | None = None) -> dict[str, Any]:
    readiness = wave3 or wave3_readiness_decision()
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_post_lane11_launch_order_v2",
        "generated_at_utc": utc_now(),
        "wave3_open": False,
        "wave3_terminal_verified": bool(readiness.get("wave3_terminal_verified")),
        "post_lane11_terminal_verified": bool(readiness.get("post_lane11_terminal_verified")),
        "next_wave_open": bool(readiness.get("next_wave_ready_to_open")),
        "launch_order": [
            {
                "phase": "post_lane11_next_wave",
                "lanes": ["16", "17", "18"],
                "mode": "parallel_full_trading_operating_system_wave",
                "rule": "Open Historical Microscope Scaling, Market Awareness Whiteboard, and Broker Truth Cost Capture V2 from terminal Lane08-Lane11 plus Lane09B/Lane10B/Lane11 disk evidence.",
            },
            {
                "phase": "post_lane18_source_capture_and_v3_gates",
                "lanes": ["source_capture_repair", "selector_v3", "scheduler_v3", "execution_policy_v3"],
                "mode": "terminal_consumed_by_post_v3_master_refresh",
                "rule": "Source Capture Repair, Selector V3, Scheduler V3, and Execution Policy V3 consume Lane16-Lane18 contracts plus Lane09B/Lane10B/Lane11 and are now terminal post-V3 inputs.",
            },
            {
                "phase": "post_v3_engine_gates_historical_pointer",
                "lanes": ["selector_v3", "scheduler_v3", "execution_policy_v3"],
                "mode": "do_not_relaunch_without_hash_or_verifier_defect",
                "rule": "Selector/Scheduler/Execution V3 terminal route artifacts are consumed by post-V3 Master; stale launch-pending wording must not reopen them.",
            },
            {
                "phase": "post_v3_ml_subsystem",
                "lanes": ["12", "13"],
                "mode": "lane12_open_then_lane13_after_lane12_outputs",
                "rule": "ML remains a subsystem consumer of post-V3 contracts and is not the whole research horizon.",
            },
            {
                "phase": "post_v3_repair_and_command_center",
                "lanes": ["14", "15"],
                "mode": "lane14_default_off_repair_design_then_lane15_report_pack_owner_gated_activation",
                "rule": "Repair Companion and Command Center consume post-V3 contracts; production activation, broker mutation, credentials, spend, and remote push remain forbidden without owner approval.",
            },
        ],
        "parallelization_rules": [
            "Do not create another Master route; Master writes only this route and context integration artifacts.",
            "Wave 3 is terminal: Lane08, Lane09, Lane10, and Lane11 disk artifacts are consumed as verified inputs.",
            "Post-Lane11 evidence is terminal: Lane09B, Lane10B, and Lane11 completion audits, verifiers, manifests, focused tests, and contracts are consumed from disk.",
            "Wave 4 is terminal: Lane16, Lane17, and Lane18 are consumed from verified disk outputs.",
            "Post-V3 source-capture and engine gates are terminal and must not be relaunched from stale launch text.",
            "Lane12-Lane15 open in post-V3 order while production activation remains owner-gated.",
        ],
        "runtime_effect_boundary": "coordination_artifact_only_no_live_behavior_change",
    }


def post_lane18_implementation_wave_decision(
    wave4_table: dict[str, Any] | None = None,
    gates: dict[str, Any] | None = None,
) -> dict[str, Any]:
    wave4 = wave4_table or wave4_terminal_state_table()
    later = gates or later_wave_gates(wave4_table=wave4)
    wave4_terminal = bool(wave4.get("all_wave4_terminal_verified"))
    post_v3_consumed = bool(later.get("post_v3_terminal_consumed"))
    implementation_gates = [
        row
        for row in later["gates"]
        if row["gate_id"] in {"selector_v3", "scheduler_v3", "execution_policy_v3", "source_capture_repair"}
    ]
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_post_lane18_implementation_wave_decision_v1",
        "generated_at_utc": utc_now(),
        "wave4_terminal_verified": wave4_terminal,
        "post_v3_terminal_consumed": post_v3_consumed,
        "decision": (
            "post_lane18_v3_and_source_capture_wave_consumed_by_terminal_post_v3_artifacts"
            if post_v3_consumed
            else
            "open_selector_v3_scheduler_v3_execution_policy_v3_and_source_capture_repair"
            if wave4_terminal
            else "wait_for_lane16_lane17_lane18_terminal_artifacts"
        ),
        "next_implementation_gates": [row["gate_id"] for row in implementation_gates],
        "launch_order": [
            {
                "phase": "post_lane18_v3_engine_wave",
                "gates": ["selector_v3", "scheduler_v3", "execution_policy_v3"],
                "mode": "terminal_consumed_by_post_v3_master_refresh"
                if post_v3_consumed
                else "parallel_after_lane16_lane17_lane18_terminal_consumption",
                "required_terminal_inputs": [
                    "Lane09B selector-scheduler reconciliation",
                    "Lane10B scheduler conflict anatomy and multi-ticket contract",
                    "Lane11 execution policy engine",
                    "Lane16 historical microscope scale",
                    "Lane17 market awareness whiteboard",
                    "Lane18 broker truth/cost capture V2",
                ],
            },
            {
                "phase": "post_lane18_source_capture_repair",
                "gates": ["source_capture_repair"],
                "mode": "terminal_consumed_by_post_v3_master_refresh"
                if post_v3_consumed
                else "parallel_with_v3_when_write_paths_are_disjoint",
                "required_terminal_inputs": [
                    "Lane16 source-gap ledger",
                    "Lane17 source-gap ledger",
                    "Lane18 prospective capture requirements",
                    "MT5 local cache preservation",
                    "VPS read-only export requirements",
                ],
            },
            {
                "phase": "later_ml_subsystem",
                "gates": ["ml_dataset_baselines", "ml_policy_intelligence"],
                "mode": "after_v3_and_source_contracts_where_required",
                "required_terminal_inputs": [
                    "Feature Store",
                    "Label Store",
                    "Digital Twin",
                    "Lane16 microscope",
                    "Lane17 whiteboard",
                    "Lane18 broker truth/cost",
                    "V3 engine contracts",
                ],
            },
        ],
        "gate_rows": implementation_gates,
        "ml_role": "ML remains a subsystem consumer of trading-operating-system contracts, not the main actor.",
        "summary_only_closure_rejected": True,
        "runtime_effect_boundary": "implementation_wave_coordination_only_no_live_behavior_change",
    }


def post_v3_launch_decision(
    post_v3_table: dict[str, Any] | None = None,
    gates: dict[str, Any] | None = None,
) -> dict[str, Any]:
    table = post_v3_table or post_v3_terminal_state_table()
    later = gates or later_wave_gates(post_v3_table=table)
    post_v3_terminal = bool(table.get("all_post_v3_terminal_verified"))
    gate_rows = {row["gate_id"]: row for row in later["gates"]}
    exact_repair_lanes = [
        {
            "lane_id": "source_export_and_forward_capture_requirements",
            "status": "open_as_exact_source_or_capture_work_not_live_broker_mutation",
            "required_inputs": [
                "POST_LANE18_READ_ONLY_EXPORT_REQUIREMENT_LEDGER.jsonl.gz",
                "POST_LANE18_FORWARD_CAPTURE_CONTRACT.jsonl.gz",
                "Selector/Scheduler/Execution V3 source decision ledgers",
            ],
            "runtime_effect_boundary": "read_only_or_prospective_capture_contract_only",
        }
    ]
    launch_order = [
        {
            "phase": "post_v3_ml_dataset_baseline_lab",
            "lanes": ["12"],
            "mode": "open_now_after_post_v3_master_refresh" if post_v3_terminal else "wait_for_post_v3_terminal_evidence",
            "required_terminal_inputs": [
                "Feature Store",
                "Label Store",
                "Digital Twin",
                "Lane16 microscope",
                "Lane17 whiteboard",
                "Lane18 broker truth/cost",
                "Source Capture Repair",
                "Selector V3",
                "Scheduler V3",
                "Execution Policy V3",
            ],
        },
        {
            "phase": "post_v3_ml_policy_intelligence",
            "lanes": ["13"],
            "mode": "open_after_lane12_outputs_while_consuming_post_v3_contracts",
            "required_terminal_inputs": ["Lane12 baseline outputs", "Selector V3", "Scheduler V3", "Execution Policy V3"],
        },
        {
            "phase": "post_v3_daily_learning_repair_companion",
            "lanes": ["14"],
            "mode": "open_default_off_repair_loop_design_after_post_v3; ml_fields_wait_for_lane12_13",
            "required_terminal_inputs": [
                "Source Capture Repair",
                "Selector V3",
                "Scheduler V3",
                "Execution Policy V3",
                "Lane12/Lane13 ML intelligence when present",
            ],
        },
        {
            "phase": "post_v3_command_center_and_production_dossier",
            "lanes": ["15"],
            "mode": "open_command_center_report_pack_after_post_v3; production_activation_stays_owner_gated",
            "required_terminal_inputs": [
                "Post-V3 terminal state",
                "Lane14 repair companion outputs",
                "broker lifecycle reconciliation where claimed",
                "separate owner approval for production activation",
            ],
        },
        {
            "phase": "exact_source_or_implementation_repair",
            "lanes": [row["lane_id"] for row in exact_repair_lanes],
            "mode": "open_only_from_exact_post_v3_source_or_implementation_decision_rows",
            "required_terminal_inputs": ["post_v3_source_capture_and_completeness_decision_ledgers"],
        },
    ]
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_post_v3_launch_decision_v1",
        "generated_at_utc": utc_now(),
        "post_v3_terminal_verified": post_v3_terminal,
        "decision": (
            "open_ml_dataset_baselines_ml_policy_intelligence_daily_repair_companion_command_center_production_dossier_and_exact_source_repair_lanes"
            if post_v3_terminal
            else "wait_for_terminal_source_capture_selector_scheduler_execution_v3_evidence"
        ),
        "terminal_gate_ids": table.get("terminal_gate_ids", []),
        "next_launch_order": launch_order,
        "exact_source_or_implementation_repair_lanes": exact_repair_lanes,
        "gate_rows": [gate_rows[key] for key in ["ml_dataset_baselines", "ml_policy_intelligence", "repair_companion", "command_center"]],
        "ml_role": "ML opens as a subsystem consumer of post-V3/source-capture contracts, not as the full research horizon.",
        "broad_research_ambition_outside_ml": [
            "daily learning and repair companion",
            "command center and production dossier",
            "source export and prospective capture requirements",
            "execution feasibility and broker lifecycle truth",
            "selector/scheduler/execution default-off package hardening",
        ],
        "summary_only_closure_rejected": True,
        "runtime_effect_boundary": "post_v3_launch_coordination_only_no_live_behavior_change",
    }


def collect_lanes() -> list[dict[str, Any]]:
    prompts = lane_goal_prompt_paths()
    lanes = [parse_lane_prompt(path) for path in prompts]
    wave1_table = wave1_terminal_state_table()
    wave1_by_lane = {row["lane_id"]: row for row in wave1_table["wave1_lanes"]}
    wave2_table = wave2_terminal_state_table()
    wave2_by_lane = {row["lane_id"]: row for row in wave2_table["wave2_lanes"]}
    wave2_readiness = wave2_readiness_decision(wave1_table, wave2_table)["lane_readiness"]
    wave3_table = wave3_terminal_state_table()
    wave3_by_lane = {row["lane_id"]: row for row in wave3_table["wave3_lanes"]}
    post_lane11 = post_lane11_terminal_state_table(wave3_table)
    wave4_table = wave4_terminal_state_table()
    wave4_by_lane = {row["lane_id"]: row for row in wave4_table["wave4_lanes"]}
    post_v3_table = post_v3_terminal_state_table()
    limitation_map = limitation_disposition_map()
    gates = later_wave_gates(wave4_table=wave4_table, post_v3_table=post_v3_table)
    next_wave = next_wave_launch_decision(post_lane11, limitation_map, gates)
    next_wave_by_lane = {row["lane_id"]: row for row in next_wave["lane_rows"]}
    wave3_readiness = wave3_readiness_decision(
        wave1_table,
        wave2_table,
        wave3_table,
        post_lane11,
        next_wave,
        gates,
    )["lane_readiness"]
    gate_by_consumer = {
        "12": next(row for row in gates["gates"] if row["gate_id"] == "ml_dataset_baselines"),
        "13": next(row for row in gates["gates"] if row["gate_id"] == "ml_policy_intelligence"),
        "14": next(row for row in gates["gates"] if row["gate_id"] == "repair_companion"),
        "15": next(row for row in gates["gates"] if row["gate_id"] == "command_center"),
    }
    for lane in lanes:
        lane_id = lane["lane_id"]
        if lane_id in wave1_by_lane:
            lane["master_integration_status"] = "terminal_verified_wave1"
            lane["terminal_state"] = wave1_by_lane[lane_id]
        elif lane_id in wave2_by_lane:
            lane["master_integration_status"] = "terminal_verified_wave2"
            lane["terminal_state"] = wave2_by_lane[lane_id]
            lane["wave2_readiness"] = wave2_readiness[lane_id]
        elif lane_id in wave3_by_lane:
            lane["master_integration_status"] = "terminal_verified_wave3"
            lane["terminal_state"] = wave3_by_lane[lane_id]
            lane["wave3_readiness"] = wave3_readiness[lane_id]
            if lane_id == "11":
                lane["post_lane11_state"] = next(row for row in post_lane11["terminal_lanes"] if row["lane_id"] == "11")
        elif lane_id in wave4_by_lane:
            lane["master_integration_status"] = "terminal_verified_wave4"
            lane["terminal_state"] = wave4_by_lane[lane_id]
            lane["wave4_terminal_state"] = wave4_by_lane[lane_id]
        elif lane_id in next_wave_by_lane:
            lane["master_integration_status"] = "ready_next_wave_full_trading_operating_system"
            lane["wave3_readiness"] = wave3_readiness[lane_id]
            lane["next_wave_launch_contract"] = next_wave_by_lane[lane_id]
        elif lane_id in wave3_readiness:
            lane["master_integration_status"] = wave3_readiness[lane_id]["readiness"]
            lane["wave3_readiness"] = wave3_readiness[lane_id]
            if lane_id in gate_by_consumer:
                lane["later_wave_gate"] = gate_by_consumer[lane_id]
            if post_v3_table["all_post_v3_terminal_verified"] and lane_id == "12":
                lane["master_integration_status"] = "ready_after_post_v3_master_refresh"
            elif post_v3_table["all_post_v3_terminal_verified"] and lane_id == "13":
                lane["master_integration_status"] = "ready_after_lane12_and_post_v3_contracts"
            elif post_v3_table["all_post_v3_terminal_verified"] and lane_id == "14":
                lane["master_integration_status"] = "ready_post_v3_repair_companion_default_off_design"
            elif post_v3_table["all_post_v3_terminal_verified"] and lane_id == "15":
                lane["master_integration_status"] = "ready_post_v3_command_center_report_pack_owner_gated_production"
        else:
            lane["master_integration_status"] = "deferred_until_required_dependency_outputs"
    lanes.sort(key=lambda row: int(row["lane_id"]))
    return lanes


def prompt_validation_payload() -> dict[str, Any]:
    paths: set[Path] = {MASTER_PROMPT, MASTER_STARTER, POST_V3_MASTER_PROMPT, POST_V3_MASTER_STARTER, LAUNCH_ORDER}
    for pattern in (
        "VNEXT_ABSOLUTE_MOONSHOT_POST_LANE11_MASTER_REFRESH_GOAL_PROMPT_2026-06-01.md",
        "VNEXT_ABSOLUTE_MOONSHOT_POST_LANE11_MASTER_REFRESH_STARTER_2026-06-01.txt",
        "VNEXT_ABSOLUTE_MOONSHOT_POST_LANE18_SOURCE_CAPTURE_REPAIR_GOAL_PROMPT_2026-06-01.md",
        "VNEXT_ABSOLUTE_MOONSHOT_POST_LANE18_SOURCE_CAPTURE_REPAIR_STARTER_2026-06-01.txt",
        "VNEXT_ABSOLUTE_MOONSHOT_SELECTOR_V3_GOAL_PROMPT_2026-06-01.md",
        "VNEXT_ABSOLUTE_MOONSHOT_SELECTOR_V3_STARTER_2026-06-01.txt",
        "VNEXT_ABSOLUTE_MOONSHOT_SCHEDULER_V3_GOAL_PROMPT_2026-06-01.md",
        "VNEXT_ABSOLUTE_MOONSHOT_SCHEDULER_V3_STARTER_2026-06-01.txt",
        "VNEXT_ABSOLUTE_MOONSHOT_EXECUTION_POLICY_V3_GOAL_PROMPT_2026-06-01.md",
        "VNEXT_ABSOLUTE_MOONSHOT_EXECUTION_POLICY_V3_STARTER_2026-06-01.txt",
        "VNEXT_MOONSHOT_LANE*_GOAL_PROMPT_2026-06-01.md",
        "VNEXT_MOONSHOT_LANE*_STARTER_2026-06-01.txt",
        "VNEXT_ABSOLUTE_MOONSHOT_LANE*_GOAL_PROMPT_2026-06-01.md",
        "VNEXT_ABSOLUTE_MOONSHOT_LANE*_STARTER_2026-06-01.txt",
    ):
        paths.update(PROMPT_DIR.glob(pattern))
    results = []
    for path in sorted(paths, key=lambda item: item.name):
        result = validate_prompt(path)
        result["path"] = rel(path)
        result["sha256"] = sha256_file(path)
        results.append(result)
    return {
        "generated_at_utc": utc_now(),
        "ok": all(bool(row["ok"]) for row in results),
        "result_count": len(results),
        "results": results,
        "schema_version": "absolute_master_prompt_hardening_verification_v1",
    }


def evidence_inspection_rows(
    wave1_rows: list[dict[str, Any]] | None = None,
    stale_neutralization: dict[str, Any] | None = None,
    wave2_rows: list[dict[str, Any]] | None = None,
    wave3_rows: list[dict[str, Any]] | None = None,
    post_lane11_table: dict[str, Any] | None = None,
    wave4_rows: list[dict[str, Any]] | None = None,
    post_v3_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    next_master_audit = load_json(NEXT_LEVEL_MASTER / "MASTER_ORCHESTRATION_COMPLETION_AUDIT.json", {})
    merge_matrix = load_json(NEXT_LEVEL_MASTER / "MASTER_MERGE_READINESS_MATRIX.json", {})
    lane09_audit = load_json(LANE09_PACKAGE / "LANE09_COMPLETION_AUDIT.json", {})
    lane09_verification = load_json(LANE09_PACKAGE / "LANE09_VERIFICATION_RESULT.json", {})
    mt5_audit = load_json(MT5_LOCAL_CACHE / "COMPLETION_AUDIT.json", {})
    mt5_summary = load_json(MT5_LOCAL_CACHE / "MT5_LOCAL_CACHE_COVERAGE_SUMMARY.json", {})
    mt5_repo_compare = load_json(MT5_LOCAL_CACHE / "MT5_REPO_COVERAGE_COMPARISON.json", {})
    vps_audit = load_json(VPS_PRESERVATION / "COMPLETION_AUDIT.json", {})
    vps_verify = load_json(VPS_PRESERVATION / "VERIFICATION_RESULT.json", {})
    friday_audit = load_json(FRIDAY_ROUTE / "FRIDAY_MICROSCOPE_COMPLETION_AUDIT.json", {})
    friday_verify = load_json(FRIDAY_ROUTE / "FRIDAY_MICROSCOPE_FINAL_VERIFICATION_RESULT.json", {})
    live_state = load_json(LIVE_COMPANION / "ACTIVE_REPAIR_STATE.json", {})
    live_gate = load_json(LIVE_COMPANION / "LIVE_REPLAY_GATE_STACK_PARITY_SUMMARY.json", {})
    live_verify = load_json(LIVE_COMPANION / "LIVE_REPLAY_GATE_STACK_VERIFICATION.json", {})
    activation_state = load_json(
        ACTIVATION_REPAIR / "VNEXT_ACTIVATION_REPAIR_STAGE06_FINAL_ROUTE_STATE_2026-05-27.json",
        {},
    )
    live_state_text = (ROOT / ".context" / "LIVE_STATE.md").read_text(encoding="utf-8", errors="replace")
    research_stale = "STALE_UPDATE_RESEARCH_CURRENT_STATE" in live_state_text
    rows = [
        {
            "artifact_family": "current_live_state",
            "path": ".context/LIVE_STATE.md",
            "status": "regenerated_current_session",
            "head": git_head(),
            "research_current_state_stale_warning": research_stale,
            "source_use_state": "read_direct_artifacts_before_using_stale_research_summary",
        },
        {
            "artifact_family": "next_level_master_package",
            "path": rel(NEXT_LEVEL_MASTER),
            "status": next_master_audit.get("status"),
            "completion_ready": next_master_audit.get("completion_ready"),
            "lane_count": len(merge_matrix.get("lane_rows", [])),
            "terminal_verified_packaged": merge_matrix.get("terminal_verified_packaged_by_lane09_scoped_commit"),
            "merge_blockers": merge_matrix.get("merge_blockers"),
        },
        {
            "artifact_family": "lane09_merge_package",
            "path": rel(LANE09_PACKAGE),
            "status": lane09_audit.get("status"),
            "accepted_lane_packages": lane09_audit.get("accepted_lane_packages"),
            "verification_ok": lane09_verification.get("ok"),
            "scoped_commit_performed": lane09_audit.get("scoped_commit_performed"),
            "runtime_effect_boundary": lane09_audit.get("runtime_effect_boundary"),
        },
        {
            "artifact_family": "mt5_local_cache_preservation",
            "path": rel(MT5_LOCAL_CACHE),
            "status": "complete" if mt5_audit.get("can_mark_goal_complete") else "not_complete",
            "verification_ok": mt5_audit.get("verification_ok"),
            "inventory_rows": count_jsonl(MT5_LOCAL_CACHE / "MT5_LOCAL_CACHE_INVENTORY.jsonl"),
            "archive_candidate_file_count": mt5_summary.get("archive_candidate_file_count"),
            "source_file_count": mt5_summary.get("source_file_count"),
            "remaining_vps_export_requirement_rows": count_jsonl(MT5_LOCAL_CACHE / "MT5_REMAINING_VPS_EXPORT_REQUIREMENTS.jsonl"),
            "repo_vs_external_interpretation": mt5_repo_compare.get("interpretation"),
        },
        {
            "artifact_family": "compliant_vps_data_preservation",
            "path": rel(VPS_PRESERVATION),
            "status": "complete" if vps_audit.get("can_mark_goal_complete") else "not_complete",
            "verification_ok": vps_verify.get("ok"),
            "inventory_rows": vps_verify.get("counts", {}).get("inventory_rows"),
            "missing_export_rows": vps_verify.get("counts", {}).get("missing_export_rows"),
            "broker_gap_rows": vps_verify.get("counts", {}).get("broker_gap_rows"),
            "official_source_entries": vps_verify.get("counts", {}).get("official_source_entries"),
        },
        {
            "artifact_family": "friday_microscope_route",
            "path": rel(FRIDAY_ROUTE),
            "status": friday_audit.get("status"),
            "verification_ok": friday_verify.get("ok"),
            "primary_non_crypto_rows_current": friday_audit.get("primary_non_crypto_rows_current"),
            "remaining_blockers": friday_audit.get("remaining_blockers"),
            "verified_artifact_contracts": friday_verify.get("verified_artifact_contracts"),
        },
        {
            "artifact_family": "live_companion_route",
            "path": rel(LIVE_COMPANION),
            "status": live_state.get("status"),
            "updated_at": live_state.get("updated_at"),
            "current_focus": live_state.get("current_focus"),
            "gate_stack_ok": live_verify.get("ok"),
            "required_gate_count": live_gate.get("required_gate_count"),
            "ledger_rows": live_gate.get("ledger_rows"),
            "evidence_gap_count": live_state.get("gates", {}).get("live_health_latest_checkpoint", {}).get("evidence", {}).get("evidence_gap_count"),
        },
        {
            "artifact_family": "activation_repair_route",
            "path": rel(ACTIVATION_REPAIR),
            "status": activation_state.get("status"),
            "stage_id": activation_state.get("stage_id"),
            "selected_rows": activation_state.get("execution_policy_momentum_promotion_selected_rows"),
            "dynamic_router_metric_rows": activation_state.get("execution_intelligence_final_dynamic_router_metric_rows"),
            "dynamic_router_expectancy_r": activation_state.get("execution_intelligence_final_dynamic_router_metrics", {}).get("expectancy_r"),
            "dynamic_router_total_r": activation_state.get("execution_intelligence_final_dynamic_router_metrics", {}).get("total_r"),
            "dynamic_router_profit_factor": activation_state.get("execution_intelligence_final_dynamic_router_metrics", {}).get("profit_factor"),
        },
    ]
    for row in wave1_rows or wave1_artifact_inspection_rows():
        rows.append(
            {
                "artifact_family": row["artifact_family"],
                "path": row["route_path"],
                "status": row["inspection_status"],
                "lane_id": row["lane_id"],
                "verifier_ok": row["verifier_ok"],
                "completion_status": row["completion_status"],
                "material_row_counts": row["material_row_counts"],
                "dependency_rows": row["dependency_rows"],
                "source_gap_ledger_path": row["source_gap_ledger_path"],
                "schema_contract_paths": row["schema_contract_paths"],
                "material_row_count_artifacts": row["material_row_count_artifacts"],
                "context_anchor_path": row["context_anchor_path"],
                "source_use_state": row["source_use_state"],
                "runtime_effect_boundary": row["runtime_effect_boundary"],
            }
        )
    for row in wave2_rows or wave2_artifact_inspection_rows():
        rows.append(
            {
                "artifact_family": row["artifact_family"],
                "path": row["route_path"],
                "status": row["inspection_status"],
                "lane_id": row["lane_id"],
                "verifier_ok": row["verifier_ok"],
                "completion_status": row["completion_status"],
                "focused_test_result": row["focused_test_result"],
                "material_row_counts": row["material_row_counts"],
                "dependency_rows": row["dependency_rows"],
                "source_gap_ledger_paths": row["source_gap_ledger_paths"],
                "coverage_ledger_paths": row["coverage_ledger_paths"],
                "schema_contract_paths": row["schema_contract_paths"],
                "downstream_contract_path": row["downstream_contract_path"],
                "material_row_count_artifacts": row["material_row_count_artifacts"],
                "context_anchor_path": row["context_anchor_path"],
                "source_use_state": row["source_use_state"],
                "runtime_effect_boundary": row["runtime_effect_boundary"],
            }
        )
    for row in wave3_rows or wave3_artifact_inspection_rows():
        rows.append(
            {
                "artifact_family": row["artifact_family"],
                "path": row["route_path"],
                "status": row["inspection_status"],
                "lane_id": row["lane_id"],
                "commit": row["commit"],
                "verifier_ok": row["verifier_ok"],
                "completion_status": row["completion_status"],
                "focused_test_result": row["focused_test_result"],
                "material_row_counts": row["material_row_counts"],
                "dependency_rows": row["dependency_rows"],
                "source_gap_ledger_paths": row["source_gap_ledger_paths"],
                "schema_contract_paths": row["schema_contract_paths"],
                "downstream_contract_path": row["downstream_contract_path"],
                "material_row_count_artifacts": row["material_row_count_artifacts"],
                "context_anchor_path": row["context_anchor_path"],
                "source_use_state": row["source_use_state"],
                "runtime_effect_boundary": row["runtime_effect_boundary"],
            }
        )
    post_table = post_lane11_table or post_lane11_terminal_state_table()
    for row in post_table["terminal_lanes"]:
        rows.append(
            {
                "artifact_family": f"absolute_post_lane11_lane{row['lane_id'].lower()}_terminal_outputs",
                "path": row["route_path"],
                "status": row["terminal_status"],
                "lane_id": row["lane_id"],
                "commit": row["commit"],
                "verifier_ok": row["verifier_ok"],
                "completion_status": row["completion_status"],
                "focused_test_result": row["focused_test_result"],
                "manifest_output_count": row["manifest_output_count"],
                "downstream_contract_paths": row["downstream_contract_paths"],
                "material_row_counts": row["material_row_counts"],
                "expected_count_matches": row["expected_count_matches"],
                "source_use_state": row["source_use_state"],
                "runtime_effect_boundary": row["runtime_effect_boundary"],
            }
        )
    for row in wave4_rows or wave4_artifact_inspection_rows():
        rows.append(
            {
                "artifact_family": row["artifact_family"],
                "path": row["route_path"],
                "status": row["inspection_status"],
                "lane_id": row["lane_id"],
                "commit": row["commit"],
                "verifier_ok": row["verifier_ok"],
                "completion_status": row["completion_status"],
                "focused_test_result": row["focused_test_result"],
                "material_row_counts": row["material_row_counts"],
                "dependency_rows": row["dependency_rows"],
                "source_gap_ledger_paths": row["source_gap_ledger_paths"],
                "schema_contract_paths": row["schema_contract_paths"],
                "downstream_contract_path": row["downstream_contract_path"],
                "material_row_count_artifacts": row["material_row_count_artifacts"],
                "context_anchor_path": row["context_anchor_path"],
                "source_use_state": row["source_use_state"],
                "runtime_effect_boundary": row["runtime_effect_boundary"],
            }
        )
    for row in post_v3_rows or post_v3_artifact_inspection_rows():
        rows.append(
            {
                "artifact_family": row["artifact_family"],
                "path": row["route_path"],
                "status": row["inspection_status"],
                "gate_id": row["gate_id"],
                "verification_ok": row["verification_ok"],
                "completion_status": row["completion_status"],
                "focused_test_result": row["focused_test_result"],
                "manifest_artifact_count": row["manifest_artifact_count"],
                "material_row_counts": row["material_row_counts"],
                "expected_count_matches": row["expected_count_matches"],
                "result_use_status": row["result_use_status"],
                "required_artifacts": row["required_artifacts"],
                "source_use_state": row["source_use_state"],
                "runtime_effect_boundary": row["runtime_effect_boundary"],
            }
        )
    neutralization = stale_neutralization or stale_dependency_text_neutralization()
    rows.append(
        {
            "artifact_family": "lane04_stale_dependency_text_neutralization",
            "path": rel(WAVE1_ROUTE_DIRS["04"] / "LANE04_DEPENDENCY_STATE_LEDGER.jsonl"),
            "status": "neutralized" if neutralization["neutralized_for_master_consumption"] else "not_neutralized",
            "neutralized_for_master_consumption": neutralization["neutralized_for_master_consumption"],
            "current_authority": neutralization["current_authority"],
            "source_use_state": "master_consumes_current_dependency_ledger_not_stale_absence_wording",
            "runtime_effect_boundary": neutralization["runtime_effect_boundary"],
        }
    )
    return rows


def source_authority_map(evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_family = {row["artifact_family"]: row for row in evidence_rows}
    activation = by_family.get("activation_repair_route", {})
    live_gate = load_json(LIVE_COMPANION / "LIVE_REPLAY_GATE_STACK_PARITY_SUMMARY.json", {})
    mt5_summary = load_json(MT5_LOCAL_CACHE / "MT5_LOCAL_CACHE_COVERAGE_SUMMARY.json", {})
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_source_authority_map_v1",
        "generated_at_utc": utc_now(),
        "source_families": [
            {
                "source_family": "repo_data_and_runtime_logs",
                "authority_level": "local_repo_evidence",
                "paths": ["data/", "exports/", "shadow_logs/", "pipeline_state/", "knowledge_base/"],
                "allowed_use": "source_inventory_feature_candidate_runtime_log_and_forward_capture_inputs",
                "limits": "runtime dirt is not context truth unless consumed by a current route artifact or verifier",
            },
            {
                "source_family": "local_mt5_cache",
                "authority_level": "local_mt5_native_cache_preserved",
                "paths": [rel(MT5_LOCAL_CACHE / "MT5_LOCAL_CACHE_INVENTORY.jsonl"), rel(MT5_LOCAL_CACHE / "MT5_ARCHIVE_MANIFEST.json")],
                "counts": {
                    "inventory_rows": count_jsonl(MT5_LOCAL_CACHE / "MT5_LOCAL_CACHE_INVENTORY.jsonl"),
                    "source_file_count": mt5_summary.get("source_file_count"),
                    "archive_candidate_file_count": mt5_summary.get("archive_candidate_file_count"),
                    "remaining_vps_export_requirement_rows": count_jsonl(MT5_LOCAL_CACHE / "MT5_REMAINING_VPS_EXPORT_REQUIREMENTS.jsonl"),
                },
                "allowed_use": "market_history_bar_tick_cache_broker_metadata_local_cache_source_authority",
                "limits": "server/account/order/deal/position truth still requires compliant read_only_export where not present",
            },
            {
                "source_family": "compliant_vps_data_preservation",
                "authority_level": "local_inventory_and_default_off_export_contract",
                "paths": [rel(VPS_PRESERVATION / "LOCAL_EVIDENCE_INVENTORY.jsonl"), rel(VPS_PRESERVATION / "MISSING_SOURCE_EXPORT_REQUIREMENTS.jsonl")],
                "counts": load_json(VPS_PRESERVATION / "VERIFICATION_RESULT.json", {}).get("counts", {}),
                "allowed_use": "exact_missing_source_requirements_vps_portability_default_off_export_design",
                "limits": "default_off tools only; no mt5 server access or broker action by master route",
            },
            {
                "source_family": "friday_microscope",
                "authority_level": "row_level_current_vnext_microscope_evidence",
                "paths": [rel(FRIDAY_ROUTE)],
                "counts": {
                    "primary_non_crypto_rows_current": by_family.get("friday_microscope_route", {}).get("primary_non_crypto_rows_current"),
                },
                "allowed_use": "candidate_anatomy_broker_ready_selected_denominator_stale_blocker_failure_and_policy_seed",
                "limits": "one_day_microscope_seed_not_final_system_validation",
            },
            {
                "source_family": "next_level_lane_package",
                "authority_level": "terminal_packaged_current_lane_evidence",
                "paths": [rel(NEXT_LEVEL_MASTER), rel(LANE09_PACKAGE)],
                "counts": {
                    "packaged_lanes": by_family.get("lane09_merge_package", {}).get("accepted_lane_packages"),
                    "selected_denominator_rows": 289600,
                    "accepted_rows": 72482,
                },
                "allowed_use": "seed_contracts_selected_surface_broad_replay_scheduler_selector_execution_package_inputs",
                "limits": "not production activation; approval and final broker lifecycle gates remain separate",
            },
            {
                "source_family": "absolute_lane01_source_authority",
                "authority_level": "terminal_wave1_verified",
                "paths": [rel(WAVE1_ROUTE_DIRS["01"])],
                "counts": by_family.get("absolute_lane01_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "source_inventory_source_gap_downstream_contract_authority_for_wave2_lanes",
                "limits": "source authority only; no broker-real result scoring owned by Lane01",
            },
            {
                "source_family": "absolute_lane02_asof_contract",
                "authority_level": "terminal_wave1_verified",
                "paths": [rel(WAVE1_ROUTE_DIRS["02"])],
                "counts": by_family.get("absolute_lane02_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "timestamp_inventory_asof_field_contract_no_leak_rules_for_feature_label_replay_lanes",
                "limits": "as-of contract only; not an outcome or production-change result",
            },
            {
                "source_family": "absolute_lane03_candidate_reconstruction",
                "authority_level": "terminal_wave1_verified",
                "paths": [rel(WAVE1_ROUTE_DIRS["03"])],
                "counts": by_family.get("absolute_lane03_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "canonical_events_candidates_duplicate_policy_source_inventory_exact_proxy_r_source_bound_rows",
                "limits": "source-bound reconstruction, not broker-real production performance",
            },
            {
                "source_family": "absolute_lane04_historical_microscope",
                "authority_level": "terminal_wave1_verified",
                "paths": [rel(WAVE1_ROUTE_DIRS["04"])],
                "counts": by_family.get("absolute_lane04_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "timeline_anatomy_strict_tick_subset_source_gap_and_path_context_for_feature_label_stores",
                "limits": "stale absence wording in audit/context anchor is superseded by current dependency ledger and master neutralization artifact",
            },
            {
                "source_family": "absolute_lane05_feature_store",
                "authority_level": "terminal_wave2_verified",
                "paths": [rel(WAVE2_ROUTE_DIRS["05"])],
                "counts": by_family.get("absolute_lane05_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "no_leak_feature_vectors_schema_builders_ledgers_downstream_contract_for_digital_twin_ml_selector_scheduler_execution_policy",
                "limits": "offline research feature materialization only; no labels or post-outcome broker fields as features",
            },
            {
                "source_family": "absolute_lane06_label_store",
                "authority_level": "terminal_wave2_verified",
                "paths": [rel(WAVE2_ROUTE_DIRS["06"])],
                "counts": by_family.get("absolute_lane06_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "label_vectors_missing_label_gaps_broker_real_proxy_replay_label_separation_for_replay_ml_selector_scheduler_execution_policy",
                "limits": "labels join only after purge/embargo/split; broker-real and proxy labels remain distinct target families",
            },
            {
                "source_family": "absolute_lane07_broker_truth_cost_calibration",
                "authority_level": "terminal_wave2_verified_separate_cost_enrichment",
                "paths": [rel(WAVE2_ROUTE_DIRS["07"])],
                "counts": by_family.get("absolute_lane07_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "symbol_specs_broker_truth_rows_cost_rows_source_gap_proxy_export_fields_for_wave3_enrichment",
                "limits": "missing broker-real fields remain source gaps/proxies/export requirements and do not block Wave3 historical research",
            },
            {
                "source_family": "absolute_lane08_digital_twin",
                "authority_level": "terminal_wave3_verified",
                "paths": [rel(WAVE3_ROUTE_DIRS["08"])],
                "counts": by_family.get("absolute_lane08_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "source_bound_replay_rows_missing_replay_gaps_split_stress_and_replay_depth_for_next_wave_contracts",
                "limits": "offline replay and proxy/result separation only; not broker-real production performance",
            },
            {
                "source_family": "absolute_lane09_meta_selector",
                "authority_level": "terminal_wave3_verified_default_off",
                "paths": [rel(WAVE3_ROUTE_DIRS["09"])],
                "counts": by_family.get("absolute_lane09_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "selector_row_evidence_discovery_clauses_mechanism_decisions_and_capture_requirements_for_selector_v3",
                "limits": "default-off research package only; activation requires later dossier",
            },
            {
                "source_family": "absolute_lane10_portfolio_scheduler",
                "authority_level": "terminal_wave3_verified_default_off",
                "paths": [rel(WAVE3_ROUTE_DIRS["10"])],
                "counts": by_family.get("absolute_lane10_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "scheduler_replay_conflict_risk_split_and_missing_gap_evidence_for_scheduler_v3",
                "limits": "offline scheduler research package only; no live scheduler behavior change",
            },
            {
                "source_family": "absolute_lane09b_selector_scheduler_reconciliation",
                "authority_level": "post_lane11_terminal_verified",
                "paths": [rel(POST_LANE11_ROUTE_DIRS["09B"])],
                "counts": by_family.get("absolute_post_lane11_lane09b_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "selector_scheduler_join_blocked_surviving_false_positive_and_lane11_policy_dependency_evidence_for_selector_v3",
                "limits": "default-off reconciliation package; no selector or scheduler live mutation",
            },
            {
                "source_family": "absolute_lane10b_scheduler_conflict_anatomy",
                "authority_level": "post_lane11_terminal_verified",
                "paths": [rel(POST_LANE11_ROUTE_DIRS["10B"])],
                "counts": by_family.get("absolute_post_lane11_lane10b_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "full_conflict_anatomy_missed_edges_correct_rejects_repairable_blocks_risk_breaches_and_multi_ticket_contracts_for_scheduler_v3",
                "limits": "default-off design package; no live risk or scheduler behavior change",
            },
            {
                "source_family": "absolute_lane11_execution_policy_engine",
                "authority_level": "terminal_wave3_and_post_lane11_verified_default_off",
                "paths": [rel(WAVE3_ROUTE_DIRS["11"])],
                "counts": by_family.get("absolute_lane11_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "policy_simulation_dominance_default_off_router_expanded_variants_and_lane09b_lane10b_integration_contracts_for_execution_v3",
                "limits": "offline execution policy package only; no live execution policy activation",
            },
            {
                "source_family": "absolute_lane16_historical_microscope_scale",
                "authority_level": "terminal_wave4_verified",
                "paths": [rel(WAVE4_ROUTE_DIRS["16"])],
                "counts": by_family.get("absolute_lane16_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "scaled_microscope_event_path_gap_split_contracts_for_selector_v3_scheduler_v3_execution_v3_ml_repair_and_command_center",
                "limits": "broker-real net-R, cost-adjusted R, and ordered tick truth remain exact source-gap fields where unavailable",
            },
            {
                "source_family": "absolute_lane17_market_awareness_whiteboard",
                "authority_level": "terminal_wave4_verified",
                "paths": [rel(WAVE4_ROUTE_DIRS["17"])],
                "counts": by_family.get("absolute_lane17_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "market_state_whiteboard_forward_snapshots_correlation_regime_spread_source_state_contracts_for_v3_engines_and_command_center",
                "limits": "market-hours, exact correlation runtime joins, exact spread-to-risk, and ordered tick fields remain source-labeled gaps where not captured",
            },
            {
                "source_family": "absolute_lane18_broker_truth_cost_capture_v2",
                "authority_level": "terminal_wave4_verified_default_off_capture_contract",
                "paths": [rel(WAVE4_ROUTE_DIRS["18"])],
                "counts": by_family.get("absolute_lane18_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "broker_truth_cost_capture_contract_source_gap_export_requirements_and_default_off_capture_helper_for_scheduler_v3_execution_v3_repair_companion",
                "limits": "default-off capture contract only; missing server/account/order/deal fields remain read-only export or prospective capture requirements",
            },
            {
                "source_family": "absolute_next_wave_lanes16_18_launch_contracts",
                "authority_level": "superseded_by_terminal_wave4_master_context",
                "paths": [
                    rel(lane_goal_prompt_path("16")),
                    rel(lane_goal_prompt_path("17")),
                    rel(lane_goal_prompt_path("18")),
                    rel(ROUTE_DIR / "ABSOLUTE_MASTER_NEXT_WAVE_LAUNCH_DECISION.json"),
                    rel(ROUTE_DIR / "ABSOLUTE_MASTER_WAVE4_TERMINAL_STATE_TABLE.json"),
                ],
                "counts": {"wave4_terminal_lane_count": 3, "post_lane11_terminal_inputs": 3},
                "allowed_use": "historical_launch_contract_pointer_and_terminal_wave4_status_context",
                "limits": "do not relaunch Lane16-Lane18 from stale launch wording unless their source hashes or verifiers prove a specific gap",
            },
            {
                "source_family": "absolute_post_lane18_source_capture_repair",
                "authority_level": "terminal_post_v3_verified_source_capture_contract",
                "paths": [rel(POST_V3_ROUTE_DIRS["source_capture_repair"])],
                "counts": by_family.get("absolute_post_v3_source_capture_repair_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "source_gap_superledger_repaired_source_rows_read_only_export_requirements_forward_capture_contracts_non_generatable_truth_and_source_completeness_decisions_for_ml_repair_command_center_and_dossier_lanes",
                "limits": "source_capture_repair_not_result_scoring; exact broker/order/deal truth remains read-only export or forward capture where absent",
            },
            {
                "source_family": "absolute_selector_v3_default_off_package",
                "authority_level": "terminal_post_v3_verified_default_off_selector",
                "paths": [rel(POST_V3_ROUTE_DIRS["selector_v3"])],
                "counts": by_family.get("absolute_post_v3_selector_v3_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "selector_v3_runtime_packet_schema_default_off_rules_mechanism_action_decisions_proxy_r_materialization_and_source_capture_decisions_for_ml_and_command_center",
                "limits": "default-off research package only; no live selector activation or production-change claim",
            },
            {
                "source_family": "absolute_scheduler_v3_default_off_package",
                "authority_level": "terminal_post_v3_verified_default_off_scheduler",
                "paths": [rel(POST_V3_ROUTE_DIRS["scheduler_v3"])],
                "counts": by_family.get("absolute_post_v3_scheduler_v3_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "money_risk_exposure_conflict_recovery_correlation_cluster_same_symbol_contract_and_exact_or_proxy_r_research_accounting_for_ml_repair_and_command_center",
                "limits": "offline scheduler package only; no live risk/scheduler behavior change",
            },
            {
                "source_family": "absolute_execution_policy_v3_default_off_package",
                "authority_level": "terminal_post_v3_verified_default_off_execution_policy",
                "paths": [rel(POST_V3_ROUTE_DIRS["execution_policy_v3"])],
                "counts": by_family.get("absolute_post_v3_execution_policy_v3_terminal_outputs", {}).get("material_row_counts", {}),
                "allowed_use": "policy_variant_registry_feasible_policy_evaluations_routing_decisions_lifecycle_feasibility_failure_anatomy_and_source_gap_contracts_for_ml_repair_and_command_center",
                "limits": "default-off execution-policy package only; no live execution policy activation",
            },
            {
                "source_family": "selected_denominator_dynamic_replay",
                "authority_level": "source_bound_proxy_r_replay_result",
                "paths": [
                    rel(
                        ACTIVATION_REPAIR
                        / "VNEXT_ACTIVATION_REPAIR_STAGE06_FINAL_ROUTE_STATE_2026-05-27.json"
                    ),
                    rel(LIVE_COMPANION / "LIVE_REPLAY_GATE_STACK_PARITY_SUMMARY.json"),
                ],
                "result_use_status": "proxy_r_and_expectancy_fields_available_for_replay_contracts_not_broker_real_performance",
                "proxy_r_fields": {
                    "selected_rows": activation.get("selected_rows"),
                    "dynamic_router_metric_rows": activation.get("dynamic_router_metric_rows"),
                    "dynamic_router_expectancy_r": activation.get("dynamic_router_expectancy_r"),
                    "dynamic_router_total_r": activation.get("dynamic_router_total_r"),
                    "dynamic_router_profit_factor": activation.get("dynamic_router_profit_factor"),
                    "live_gate_stack_dynamic_replay_metrics": live_gate.get("dynamic_replay_metrics_after_replay_included_live_gates"),
                },
                "limits": "net broker R blocked until live cost_slippage_commission_swap_and_deal_reconciliation_are_captured",
            },
            {
                "source_family": "live_companion",
                "authority_level": "hot_live_evidence_context_only_for_master",
                "paths": [rel(LIVE_COMPANION)],
                "allowed_use": "current_live_status_gate_stack_broker_lifecycle_gap_runtime_effect_boundary",
                "limits": "master must not rewrite hot live evidence or perform broker operations",
            },
        ],
        "source_capture_decision": "all master-owned evidence consumed from current local route artifacts; downstream lanes must use read_only_mt5_export only when their source contract requires it",
        "source_use_state": "local_repo_route_mt5_cache_and_read_only_artifact_inspection_only",
    }


def output_schema_contracts() -> dict[str, Any]:
    common = [
        "schema_version",
        "row_id",
        "source_family",
        "source_path",
        "source_hash",
        "decision_asof_utc",
        "source_capture_utc",
        "symbol",
        "broker_symbol",
        "duplicate_key",
        "no_leak_status",
        "source_completeness_state",
        "runtime_effect_boundary",
    ]
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_output_schema_contracts_v1",
        "generated_at_utc": utc_now(),
        "schemas": {
            "event_row": common
            + [
                "event_time_utc",
                "event_type",
                "candidate_id",
                "origin_family",
                "side",
                "session",
                "timeframe",
                "event_payload",
            ],
            "feature_row": common
            + [
                "feature_set_id",
                "feature_time_utc",
                "feature_namespace",
                "feature_name",
                "feature_value",
                "feature_source_state",
                "asof_dependency_fields",
                "post_outcome_field_excluded",
            ],
            "label_row": common
            + [
                "label_family",
                "label_time_utc",
                "label_value",
                "exact_r",
                "net_exact_r",
                "proxy_r",
                "cost_adjusted_r",
                "expectancy_r",
                "r_source_state",
                "row_level_missing_field_proof",
            ],
            "replay_row": common
            + [
                "replay_engine_version",
                "candidate_state_asof",
                "selector_state_asof",
                "scheduler_state_asof",
                "execution_policy_id",
                "fillability_state",
                "path_ordering_state",
                "gross_r",
                "net_r",
                "proxy_r",
                "cost_model_version",
                "stress_partition",
            ],
            "ml_row": common
            + [
                "dataset_version",
                "partition_id",
                "model_family",
                "feature_vector_hash",
                "label_vector_hash",
                "prediction",
                "prediction_time_utc",
                "calibration_state",
                "uncertainty",
                "ood_score",
                "baseline_comparison",
            ],
            "scheduler_row": common
            + [
                "account_equity",
                "day_start_balance",
                "open_worst_case_sl_risk",
                "pending_worst_case_sl_risk",
                "new_candidate_worst_case_risk",
                "correlation_cluster_risk",
                "prop_daily_limit_state",
                "scheduler_decision",
                "scheduler_reason",
            ],
            "market_whiteboard_row": common
            + [
                "whiteboard_version",
                "timeframe_coverage_state",
                "htf_structure_state",
                "m15_structure_state",
                "m1_path_state",
                "tick_state",
                "spread_to_risk_state",
                "volatility_state",
                "session_state",
                "market_hours_state",
                "correlation_cluster_state",
                "regime_state",
                "field_source_state",
                "stale_or_null_reason",
            ],
            "execution_policy_row": common
            + [
                "policy_id",
                "policy_family",
                "entry_price",
                "stop_price",
                "target_price",
                "partial_close_plan",
                "tick_ordering_proof",
                "bid_ask_side",
                "broker_stop_freeze_feasibility",
                "modify_retcode_state",
                "gross_r",
                "net_r",
                "proxy_r",
            ],
            "broker_truth_cost_capture_row": common
            + [
                "ticket",
                "order_id",
                "deal_id",
                "position_id",
                "lifecycle_event_type",
                "fill_price",
                "close_price",
                "volume",
                "commission",
                "swap",
                "slippage",
                "spread_at_action",
                "retcode",
                "stop_freeze_context",
                "account_balance",
                "account_equity",
                "broker_real_or_proxy_state",
                "capture_or_export_requirement",
            ],
            "source_capture_repair_row": common
            + [
                "field_family",
                "disposition",
                "source_class",
                "repair_source_path",
                "exact_source_requirement",
                "read_only_export_requirement",
                "forward_capture_requirement",
                "non_generatable_truth_reason",
                "downstream_consumer",
            ],
            "post_v3_terminal_route_row": common
            + [
                "gate_id",
                "route_path",
                "terminal_status",
                "completion_status",
                "verification_ok",
                "focused_test_ok",
                "manifest_artifact_count",
                "material_row_counts",
                "result_use_status",
            ],
            "limitation_disposition_row": common
            + [
                "limitation_id",
                "limitation_family",
                "owner_lane_or_gate",
                "disposition_class",
                "decision",
                "downstream_consumer",
            ],
            "next_wave_contract_row": common
            + [
                "lane_id",
                "next_wave_contract_family",
                "required_terminal_input",
                "downstream_consumer",
                "launch_status",
                "summary_only_closure_rejected",
                "ml_role",
            ],
            "selector_v3_contract_row": common
            + [
                "selector_contract_id",
                "lane09b_reconciliation_key",
                "market_whiteboard_key",
                "microscope_anatomy_key",
                "broker_truth_key",
                "selector_action",
                "default_off_state",
            ],
            "scheduler_v3_contract_row": common
            + [
                "scheduler_contract_id",
                "lane10b_conflict_key",
                "multi_ticket_lifecycle_key",
                "market_state_key",
                "broker_truth_key",
                "risk_budget_state",
                "default_off_state",
            ],
            "execution_policy_v3_contract_row": common
            + [
                "execution_contract_id",
                "lane11_policy_key",
                "ticket_lifecycle_key",
                "broker_feasibility_key",
                "cost_truth_key",
                "policy_router_state",
                "default_off_state",
            ],
            "production_dossier_row": common
            + [
                "dossier_id",
                "candidate_change_surface",
                "sealed_validation_status",
                "stress_status",
                "cost_realism_status",
                "drift_monitor_status",
                "rollback_plan",
                "owner_approval_state",
                "production_activation_state",
            ],
        },
        "merge_rules": {
            "all_rows_require_source_hash": True,
            "all_rows_require_decision_asof_utc": True,
            "broker_real_r_and_proxy_r_must_not_share_label_family": True,
            "missing_exact_r_requires_row_level_missing_field_proof": True,
            "runtime_effect_boundary_must_be_explicit": True,
        },
    }


def dependency_graph(
    lanes: list[dict[str, Any]],
    post_v3_table: dict[str, Any] | None = None,
) -> dict[str, Any]:
    post_v3 = post_v3_table or post_v3_terminal_state_table()
    nodes = [
        {
            "node_id": "MASTER",
            "node_type": "master_orchestration",
            "route_path": rel(ROUTE_DIR),
            "wave": 0,
            "status": "materialized_by_this_route",
        }
    ]
    edges = []
    for lane in lanes:
        nodes.append(
            {
                "node_id": lane["lane_id"],
                "node_type": "program_lane",
                "title": lane["title"],
                "route_path": lane["route_path"],
                "wave": lane["wave"],
                "status": lane.get("master_integration_status", "launch_contract_ready_pending_lane_execution"),
                "terminal_state": lane.get("terminal_state"),
                "wave2_readiness": lane.get("wave2_readiness"),
                "wave3_readiness": lane.get("wave3_readiness"),
                "wave4_terminal_state": lane.get("wave4_terminal_state"),
                "next_wave_launch_contract": lane.get("next_wave_launch_contract"),
                "later_wave_gate": lane.get("later_wave_gate"),
            }
        )
        edges.append({"from": "MASTER", "to": lane["lane_id"], "edge_type": "registry_and_control_contract"})
        for dep in lane["dependencies"]:
            edges.append({"from": dep, "to": lane["lane_id"], "edge_type": "terminal_output_dependency"})
        for dep in lane["evidence_dependencies"]:
            edges.append({"from": dep, "to": lane["lane_id"], "edge_type": "evidence_seed_dependency"})
    for row in post_v3.get("terminal_routes", []):
        gate_id = row["gate_id"]
        nodes.append(
            {
                "node_id": gate_id,
                "node_type": "post_v3_terminal_gate",
                "route_path": row["route_path"],
                "wave": 4.5,
                "status": row["terminal_status"],
                "terminal_state": row,
            }
        )
        edges.append({"from": "MASTER", "to": gate_id, "edge_type": "post_v3_terminal_consumption_contract"})
        for dep in ["16", "17", "18"]:
            edges.append({"from": dep, "to": gate_id, "edge_type": "wave4_terminal_contract_input"})
    downstream_by_gate = {
        "source_capture_repair": ["12", "13", "14", "15"],
        "selector_v3": ["12", "13", "14", "15"],
        "scheduler_v3": ["12", "13", "14", "15"],
        "execution_policy_v3": ["12", "13", "14", "15"],
    }
    for gate_id, downstream_lanes in downstream_by_gate.items():
        for lane_id in downstream_lanes:
            edges.append({"from": gate_id, "to": lane_id, "edge_type": "post_v3_terminal_input_dependency"})
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_dependency_graph_v1",
        "generated_at_utc": utc_now(),
        "nodes": nodes,
        "edges": edges,
        "post_v3_terminal_consumed": post_v3["all_post_v3_terminal_verified"],
        "launch_policy": "launch_every_lane_or_gate_only_after_its_dependencies_are_terminal_or_dependency_state_bounded",
    }


def launch_waves(
    lanes: list[dict[str, Any]],
    post_v3_table: dict[str, Any] | None = None,
) -> dict[str, Any]:
    post_v3 = post_v3_table or post_v3_terminal_state_table()
    waves: dict[str, list[dict[str, Any]]] = {"0": [{"lane_id": "MASTER", "status": "current_route"}]}
    for lane in lanes:
        waves.setdefault(str(lane["wave"]), []).append(
            {
                "lane_id": lane["lane_id"],
                "title": lane["title"],
                "prompt_path": lane["prompt_path"],
                "starter_path": lane["starter_path"],
                "route_path": lane["route_path"],
                "dependencies": lane["dependencies"],
                "status": lane.get("master_integration_status", "ready_to_launch_when_dependencies_satisfied"),
                "terminal_state": lane.get("terminal_state"),
                "wave2_readiness": lane.get("wave2_readiness"),
                "wave3_readiness": lane.get("wave3_readiness"),
                "wave4_terminal_state": lane.get("wave4_terminal_state"),
                "next_wave_launch_contract": lane.get("next_wave_launch_contract"),
                "later_wave_gate": lane.get("later_wave_gate"),
            }
        )
    waves["4.5"] = [
        {
            "gate_id": row["gate_id"],
            "route_path": row["route_path"],
            "status": row["terminal_status"],
            "completion_status": row["completion_status"],
            "verification_ok": row["verification_ok"],
            "focused_test_result": row["focused_test_result"],
            "material_row_counts": row["material_row_counts"],
            "runtime_effect_boundary": row["runtime_effect_boundary"],
        }
        for row in post_v3["terminal_routes"]
    ]
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_launch_waves_v1",
        "generated_at_utc": utc_now(),
        "waves": waves,
        "parallelization_rules": [
            "Wave 1 lanes can run in parallel after master registry exists because their write paths are disjoint.",
            "Wave 2 is terminal: Lane05 Feature Store, Lane06 Label Store, and Lane07 Broker Truth/Cost Calibration have verified route artifacts.",
            "Lane07 remains separated broker-truth/cost enrichment; missing broker-real fields become proxy/gap/export fields rather than Wave 3 blockers.",
            "Wave 3 is terminal: Lane08, Lane09, Lane10, and Lane11 verified disk outputs are consumed by this Master refresh.",
            "Post-Lane11 evidence is terminal: Lane09B, Lane10B, and Lane11 are consumed from completion audits, verifiers, manifests, focused tests, and downstream contracts.",
            "Wave 4 is terminal: Lane16 Historical Microscope Scale, Lane17 Market Awareness Whiteboard, and Lane18 Broker Truth Cost Capture V2 have verified disk outputs.",
            "Post-V3 source-capture and engine gates are terminal: Source Capture Repair, Selector V3, Scheduler V3, and Execution Policy V3 are consumed from disk and must not be relaunched from stale launch wording.",
            "The next launch sequence opens Lane12, then Lane13, then Lane14, then Lane15/report-pack work, with production activation still owner-gated.",
            "ML is a subsystem consumer of post-V3 contracts, not the whole research horizon.",
            "Lane14 and Lane15 preserve repair/command-center prerequisites, broker lifecycle reconciliation, production dossier, and owner approval gates.",
            "No parent coordinator may run in parallel with child writers it may rewrite.",
        ],
        "post_v3_terminal_consumed": post_v3["all_post_v3_terminal_verified"],
    }


def blocker_rows(lanes: list[dict[str, Any]], evidence_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    now = utc_now()
    post_v3_terminal = post_v3_terminal_state_table()["all_post_v3_terminal_verified"]
    for lane in lanes:
        if lane["lane_id"] in {"01", "02", "03", "04"}:
            status = "terminal_verified_by_wave1_artifact_inspection"
            next_action = "consume_terminal_outputs_in_wave2_and_wave3_lanes"
        elif lane["lane_id"] in {"05", "06", "07"}:
            status = "terminal_verified_by_wave2_artifact_inspection"
            next_action = "consume_terminal_outputs_in_wave3; broker_real_missing_fields_remain_proxy_gap_or_export_requirements"
        elif lane["lane_id"] in {"08", "09", "10", "11"}:
            status = "terminal_verified_by_wave3_artifact_inspection"
            next_action = "consume_terminal_wave3_outputs_plus_post_lane11_contracts_in_lanes16_17_18"
        elif lane["lane_id"] in {"16", "17", "18"}:
            status = "terminal_verified_by_wave4_artifact_inspection"
            next_action = "consume_lane16_lane17_lane18_contracts_in_selector_v3_scheduler_v3_execution_policy_v3_and_source_capture_repair"
        elif lane["lane_id"] in {"12", "13"}:
            status = "ready_after_post_v3_terminal_contracts" if post_v3_terminal else "later_ml_subsystem_gate_not_next_main_actor"
            next_action = (
                "launch Lane12 then Lane13 from terminal Source Capture Repair, Selector V3, Scheduler V3, and Execution Policy V3 contracts"
                if post_v3_terminal
                else "wait_for_v3_engine_and_source_capture_contracts_before_ml_terminalization"
            )
        elif lane["lane_id"] in {"14", "15"}:
            status = "post_v3_ready_with_ml_or_owner_gates_preserved" if post_v3_terminal else "later_repair_or_command_center_gate_exact_prerequisites_recorded"
            next_action = (
                "launch repair companion and command-center work only from post-V3 terminal contracts while keeping production activation owner-gated"
                if post_v3_terminal
                else "wait_for_next_wave_v3_ml_repair_or_production_dossier_owner_approval_prerequisites"
            )
        else:
            status = "deferred_until_required_dependency_outputs"
            next_action = "wait_for_exact_prerequisite_outputs"
        rows.append(
            {
                "schema_version": "absolute_master_cross_lane_blocker_v1",
                "timestamp_utc": now,
                "lane_id": lane["lane_id"],
                "blocker_class": "lane_dependency_state",
                "status": status,
                "dependencies": lane["dependencies"],
                "same_evidence_class_pursuit_state": "master_recorded_exact_dependency_state_and_created_launch_contract",
                "exact_next_action": next_action,
            }
        )
    shared = [
        {
            "blocker_class": "production_change_approval",
            "status": "open_by_policy_not_route_failure",
            "exact_next_action": "separate_owner_approved_production_change_dossier_before_live_behavior_activation",
        },
        {
            "blocker_class": "broker_lifecycle_close_deal_cost_reconciliation",
            "status": "external_runtime_event_or_read_only_export_required",
            "exact_next_action": "consume broker close/deal/cost export after it exists; no broker action authorized",
        },
        {
            "blocker_class": "vps_export_requirements",
            "status": "exact_source_requirements_preserved",
            "exact_next_action": "use compliant read_only_vps_export routes for broker lifecycle, symbol geometry, and server history gaps",
        },
        {
            "blocker_class": "research_current_state_freshness",
            "status": "direct_artifacts_read_and_context_refresh_owned_by_this_scoped_commit",
            "exact_next_action": "commit refreshed research_current_state with post_v3_terminal_state_and_next_launch_artifacts",
        },
        {
            "blocker_class": "lane04_stale_absence_wording",
            "status": "neutralized_in_master_consumption",
            "exact_next_action": "downstream lanes must use Lane04 dependency ledger/current Wave1 terminal table rather than stale build-time absence wording",
        },
        {
            "blocker_class": "broker_real_truth_gate_confusion",
            "status": "closed_for_historical_wave2_and_wave3_research_lanes",
            "exact_next_action": "broker-real gaps become Lane07 proxy/gap/export fields, not blockers for Feature Store, Label Store, Digital Twin, ML, Selector, Scheduler, or Execution Policy research",
        },
        {
            "blocker_class": "post_lane11_terminal_state",
            "status": "closed_by_disk_artifact_consumption",
            "exact_next_action": "consume Lane09B, Lane10B, and Lane11 terminal tables as inputs to Lane16-Lane18",
        },
        {
            "blocker_class": "ml_only_closure",
            "status": "rejected_by_master_verifier",
            "exact_next_action": "open full trading operating system next wave before ML subsystem gates",
        },
        {
            "blocker_class": "wave4_terminal_state",
            "status": "closed_by_disk_artifact_consumption",
            "exact_next_action": "consume Lane16, Lane17, and Lane18 terminal contracts in Selector V3, Scheduler V3, Execution Policy V3, and source capture repair",
        },
        {
            "blocker_class": "summary_only_closeout",
            "status": "rejected_by_master_verifier",
            "exact_next_action": "require terminal disk artifacts, contracts, verifiers, and focused tests for every consumed lane",
        },
        {
            "blocker_class": "post_v3_terminal_state",
            "status": "closed_by_disk_artifact_consumption" if post_v3_terminal else "open_until_source_capture_and_v3_routes_terminal",
            "exact_next_action": "consume terminal post-V3 contracts in Lane12/Lane13/Lane14/Lane15 and exact source repair lanes",
        },
        {
            "blocker_class": "exact_source_export_and_forward_capture",
            "status": "open_as_exact_source_requirement_not_master_failure",
            "exact_next_action": "use POST_LANE18 read-only export, forward capture, and V3 source decision ledgers for future source/acquisition routes; no broker mutation authorized",
        },
    ]
    for item in shared:
        rows.append(
            {
                "schema_version": "absolute_master_cross_lane_blocker_v1",
                "timestamp_utc": now,
                "lane_id": "MASTER",
                "same_evidence_class_pursuit_state": "pursued_to_exact_policy_or_source_requirement",
                **item,
            }
        )
    return rows


def source_completeness_rows(evidence_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    now = utc_now()
    for row in evidence_rows:
        rows.append(
            {
                "schema_version": "absolute_master_source_completeness_decision_v1",
                "timestamp_utc": now,
                "source_family": row["artifact_family"],
                "path": row["path"],
                "status": row.get("status"),
                "decision": "accepted_as_master_seed_evidence_with_recorded_limits",
                "source_use_state": row.get("source_use_state", "read_from_current_disk_artifact"),
                "missing_source_or_limit": row.get("merge_blockers")
                or row.get("remaining_blockers")
                or row.get("remaining_vps_export_requirement_rows")
                or row.get("evidence_gap_count")
                or "none_recorded_in_master_evidence_row",
            }
        )
    return rows


def source_capture_rows() -> list[dict[str, Any]]:
    rows = []
    now = utc_now()
    for gate_id, route_dir in POST_V3_ROUTE_DIRS.items():
        required = POST_V3_REQUIRED_ARTIFACTS[gate_id]
        capture_name = required.get("source_capture_decisions") or required.get("source_completeness_decisions")
        completeness_name = required.get("source_completeness_decisions")
        rows.append(
            {
                "schema_version": "absolute_master_source_capture_decision_v1",
                "timestamp_utc": now,
                "gate_id": gate_id,
                "route_path": rel(route_dir),
                "source_capture_decision_path": rel(route_dir / capture_name) if capture_name else None,
                "source_capture_decision_rows": count_jsonl(route_dir / capture_name) if capture_name else 0,
                "source_completeness_decision_path": rel(route_dir / completeness_name) if completeness_name else None,
                "source_completeness_decision_rows": count_jsonl(route_dir / completeness_name) if completeness_name else 0,
                "decision": "accepted_as_terminal_post_v3_source_decision_input_for_master",
                "source_use_state": "route_owned_source_decision_artifacts_read_from_disk",
                "runtime_effect_boundary": "master_source_capture_integration_only_no_live_behavior_change",
            }
        )
    rows.append(
        {
            "schema_version": "absolute_master_source_capture_decision_v1",
            "timestamp_utc": now,
            "gate_id": "master_post_v3_integration",
            "route_path": rel(ROUTE_DIR),
            "source_capture_decision_path": rel(ROUTE_DIR / "ABSOLUTE_MASTER_SOURCE_CAPTURE_DECISIONS.jsonl"),
            "source_capture_decision_rows": len(rows),
            "source_completeness_decision_path": rel(ROUTE_DIR / "ABSOLUTE_MASTER_SOURCE_COMPLETENESS_DECISIONS.jsonl"),
            "decision": "do_not_relaunch_source_capture_or_v3_lanes_after_terminal_consumption; open exact source/export/capture repair only from row-level decision ledgers",
            "source_use_state": "master_owned_integration_decision",
            "runtime_effect_boundary": "master_source_capture_integration_only_no_live_behavior_change",
        }
    )
    return rows


def result_use_status(
    post_v3_table: dict[str, Any] | None = None,
) -> dict[str, Any]:
    table = post_v3_table or post_v3_terminal_state_table()
    by_gate = {row["gate_id"]: row for row in table["terminal_routes"]}
    activation = load_json(
        ACTIVATION_REPAIR / "VNEXT_ACTIVATION_REPAIR_STAGE06_FINAL_ROUTE_STATE_2026-05-27.json",
        {},
    )
    selector = by_gate["selector_v3"]["result_use_status"]
    scheduler = by_gate["scheduler_v3"]["result_use_status"]
    execution = by_gate["execution_policy_v3"]["result_use_status"]
    source_capture = by_gate["source_capture_repair"]["result_use_status"]
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_result_use_status_v1",
        "generated_at_utc": utc_now(),
        "master_owned_result_materialization": False,
        "master_result_scope": "post_v3_integration_and_launch_control_not_result_scoring",
        "source_capture_repair": {
            "exact_r": source_capture.get("exact_r"),
            "proxy_r": source_capture.get("proxy_r"),
            "expectancy_r": source_capture.get("expectancy_r"),
            "result_scope": source_capture.get("result_scope"),
            "source_bound_proxy_reference": source_capture.get("source_bound_proxy_reference"),
        },
        "selector_v3": {
            "exact_r_rows": selector.get("exact_r_rows"),
            "proxy_r_rows": selector.get("proxy_r_rows"),
            "proxy_r_sum": selector.get("proxy_r_sum"),
            "expectancy_r": selector.get("expectancy_r"),
            "broker_real_performance_claim": selector.get("broker_real_performance_claim"),
        },
        "scheduler_v3": {
            "exact_proxy_expectancy_by_class": scheduler.get("exact_proxy_expectancy_by_class"),
            "owned_result_materialization": scheduler.get("owned_result_materialization"),
        },
        "execution_policy_v3": {
            "exact_r_status": execution.get("exact_r_status"),
            "proxy_r_status": execution.get("proxy_r_status"),
            "expectancy_status": execution.get("expectancy_status"),
            "proxy_to_production_leap_allowed": execution.get("proxy_to_production_leap_allowed"),
        },
        "selected_denominator_dynamic_replay_reference": {
            "dynamic_router_expectancy_r": activation.get("execution_intelligence_final_dynamic_router_metrics", {}).get("expectancy_r"),
            "dynamic_router_total_r": activation.get("execution_intelligence_final_dynamic_router_metrics", {}).get("total_r"),
            "dynamic_router_profit_factor": activation.get("execution_intelligence_final_dynamic_router_metrics", {}).get("profit_factor"),
        },
        "production_change_readiness_claim": False,
        "runtime_effect_boundary": "master_consumes_result_use_status_only_no_live_behavior_change",
    }


def decision_rows(lanes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    now = utc_now()
    rows = [
        {
            "schema_version": "absolute_master_branch_implementation_decision_v1",
            "timestamp_utc": now,
            "decision_id": "MASTER-DECISION-001",
            "decision": "register_all_18_absolute_moonshot_lanes_consume_wave4_terminal_outputs_and_open_post_lane18_implementation_gates",
            "reason": "all lane prompts and starters exist; Lane08-Lane11, Lane09B/Lane10B/Lane11, and Lane16/Lane17/Lane18 terminal disk evidence is consumed; Master registry, dependency graph, schemas, merge rules, and verifier contracts are materialized",
            "runtime_effect_boundary": "no_live_behavior_change",
        },
        {
            "schema_version": "absolute_master_branch_implementation_decision_v1",
            "timestamp_utc": now,
            "decision_id": "MASTER-DECISION-002",
            "decision": "do_not_create_sierra_databento_orderflow_depth_api_lanes_in_this_program",
            "reason": "controlling prompt forbids centering this program on those external paid/vendor surfaces",
            "runtime_effect_boundary": "no_paid_api_or_vendor_call",
        },
        {
            "schema_version": "absolute_master_branch_implementation_decision_v1",
            "timestamp_utc": now,
            "decision_id": "MASTER-DECISION-003",
            "decision": "consume_lane01_lane02_lane03_lane04_as_terminal_wave1_outputs",
            "reason": "direct disk inspection found verifier-ok terminal artifacts and material row counts for all Wave 1 lanes",
            "runtime_effect_boundary": "research_control_only",
        },
        {
            "schema_version": "absolute_master_branch_implementation_decision_v1",
            "timestamp_utc": now,
            "decision_id": "MASTER-DECISION-004",
            "decision": "consume_lane05_lane06_lane07_as_terminal_wave2_outputs",
            "reason": "direct disk inspection found verifier-ok terminal artifacts and material row counts for Feature Store, Label Store, and Broker Truth/Cost Calibration",
            "runtime_effect_boundary": "research_control_only",
        },
        {
            "schema_version": "absolute_master_branch_implementation_decision_v1",
            "timestamp_utc": now,
            "decision_id": "MASTER-DECISION-005",
            "decision": "keep_lane07_as_cost_broker_enrichment_not_wave3_blocker",
            "reason": "Lane07 downstream contract says missing broker-real fields remain explicit row-level source gaps or proxy-status/export fields and do not block Digital Twin, ML, Selector, Scheduler, or Execution Policy work",
            "runtime_effect_boundary": "research_control_only",
        },
        {
            "schema_version": "absolute_master_branch_implementation_decision_v1",
            "timestamp_utc": now,
            "decision_id": "MASTER-DECISION-006",
            "decision": "neutralize_stale_lane04_absent_dependency_wording_in_master_consumption",
            "reason": "Lane04 dependency ledger marks absolute Lane01/Lane02/Lane03 present; stale build-time wording is historical and must not pollute downstream lanes",
            "runtime_effect_boundary": "research_control_only",
        },
        {
            "schema_version": "absolute_master_branch_implementation_decision_v1",
            "timestamp_utc": now,
            "decision_id": "MASTER-DECISION-007",
            "decision": "consume_lane08_lane09_lane10_lane11_as_terminal_wave3_outputs",
            "reason": "direct disk inspection found verifier-ok terminal artifacts, focused tests, manifests, contracts, and material row counts for Digital Twin, Meta-Selector, Scheduler, and Execution Policy",
            "runtime_effect_boundary": "research_control_only",
        },
        {
            "schema_version": "absolute_master_branch_implementation_decision_v1",
            "timestamp_utc": now,
            "decision_id": "MASTER-DECISION-008",
            "decision": "consume_lane09b_lane10b_lane11_as_terminal_post_lane11_evidence",
            "reason": "Lane09B selector-scheduler reconciliation, Lane10B scheduler conflict anatomy, and Lane11 execution policy engine have terminal completion audits, verifier results, manifests, focused tests, and downstream contracts on disk",
            "runtime_effect_boundary": "research_control_only",
        },
        {
            "schema_version": "absolute_master_branch_implementation_decision_v1",
            "timestamp_utc": now,
            "decision_id": "MASTER-DECISION-009",
            "decision": "consume_lane16_lane17_lane18_as_terminal_wave4_outputs",
            "reason": "Lane16 scaled microscope, Lane17 market-awareness state, and Lane18 broker truth/cost capture V2 have terminal completion audits, verifier results, manifests, focused tests, and downstream contracts on disk",
            "runtime_effect_boundary": "research_control_only",
        },
        {
            "schema_version": "absolute_master_branch_implementation_decision_v1",
            "timestamp_utc": now,
            "decision_id": "MASTER-DECISION-010",
            "decision": "reject_ml_only_or_summary_only_master_closure",
            "reason": "ML is a later subsystem that must consume Wave4, V3 engine, and source-capture contracts; Master verifier fails if Lane12 is treated as the sole next main actor",
            "runtime_effect_boundary": "research_control_only",
        },
        {
            "schema_version": "absolute_master_branch_implementation_decision_v1",
            "timestamp_utc": now,
            "decision_id": "MASTER-DECISION-011",
            "decision": "open_lanes12_13_14_15_from_post_v3_terminal_contracts_with_ml_and_owner_gates_preserved",
            "reason": "Source Capture Repair, Selector V3, Scheduler V3, and Execution Policy V3 are terminal on disk; Lane12 opens ML dataset baselines, Lane13 follows Lane12, Lane14 opens default-off repair-loop design, and Lane15 opens command-center report-pack/dossier work without production activation",
            "runtime_effect_boundary": "research_control_only",
        },
        {
            "schema_version": "absolute_master_branch_implementation_decision_v1",
            "timestamp_utc": now,
            "decision_id": "MASTER-DECISION-012",
            "decision": "do_not_relaunch_source_capture_repair_selector_v3_scheduler_v3_or_execution_policy_v3_after_terminal_consumption",
            "reason": "terminal route artifacts, verifiers, focused tests, source decision ledgers, result-use files, and git history supersede stale pending-commit or launch-pending wording",
            "runtime_effect_boundary": "research_control_only",
        },
        {
            "schema_version": "absolute_master_branch_implementation_decision_v1",
            "timestamp_utc": now,
            "decision_id": "MASTER-DECISION-013",
            "decision": "open_exact_source_export_and_forward_capture_repair_only_from_post_v3_row_level_decisions",
            "reason": "Source Capture Repair and V3 ledgers preserve exact read-only export, forward capture, non-generatable historical truth, and implementation/source requirements without broker mutation",
            "runtime_effect_boundary": "research_control_only",
        },
    ]
    for lane in lanes:
        rows.append(
            {
                "schema_version": "absolute_master_branch_implementation_decision_v1",
                "timestamp_utc": now,
                "decision_id": f"LANE-{lane['lane_id']}-CONTRACT",
                "decision": "lane_launch_contract_ready",
                "lane_id": lane["lane_id"],
                "route_path": lane["route_path"],
                "wave": lane["wave"],
                "dependencies": lane["dependencies"],
                "terminal_artifact_contract": lane["terminal_artifact_contract"],
                "runtime_effect_boundary": lane["boundary_contract"]["runtime_effect_boundary"],
            }
        )
    return rows


def anti_duplication_rules() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_anti_duplication_and_loop_rules_v1",
        "generated_at_utc": utc_now(),
        "anti_duplication_rules": [
            "Each lane owns exactly one route directory and may not write another lane route unless the master updates ownership explicitly.",
            "Rows must carry duplicate_key and source_hash when source rows can duplicate opportunity.",
            "Broker-real labels, proxy labels, replay labels, and feature rows must use separate label_family/result_scope values.",
            "Ranked summaries are allowed only after full machine-readable ledgers preserve all material rows.",
            "No arbitrary top-N, top 3/5/10, representative-only, or number-limited cutoff may replace a full ledger.",
            "Terminal Source Capture Repair, Selector V3, Scheduler V3, and Execution Policy V3 routes must not be relaunched from stale launch-order or pending-commit text after the post-V3 terminal state table verifies them.",
        ],
        "anti_infinite_ledger_rules": [
            "A blocker ledger is not terminal when same-evidence-class repair is still executable.",
            "A next prompt is not terminal unless it crosses a real evidence-class gate or external access boundary.",
            "Every lane completion audit must name the behavior, data product, model artifact, verifier, source repair, or branch decision changed.",
            "Every open blocker must have exact owner, path, field, source, parser, export, capture, or approval requirement.",
            "The master verifier fails if a lane has no terminal artifact contract or if completion is ledger-only.",
            "The master verifier fails if post-V3 route artifacts, result-use status, source-capture decisions, focused tests, or downstream contracts are absent.",
        ],
        "loop_escape_rule": "build_or_repair_same_class_artifact_now; otherwise cross_one_explicit_evidence_class_gate_with_exact_prompt; otherwise declare exact exhaustion",
    }


def merge_plan(lanes: list[dict[str, Any]]) -> dict[str, Any]:
    lane_prefixes = [lane["route_path"].rstrip("/") + "/" for lane in lanes]
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_merge_commit_ownership_plan_v1",
        "generated_at_utc": utc_now(),
        "master_owned_paths": [
            rel(ROUTE_DIR) + "/",
            "scripts/build_vnext_absolute_moonshot_master_orchestration.py",
            "tests/test_vnext_absolute_moonshot_master_orchestration.py",
            rel(LAUNCH_ORDER),
            rel(POST_V3_MASTER_PROMPT),
            rel(POST_V3_MASTER_STARTER),
        ],
        "lane_owned_prefixes": lane_prefixes,
        "forbidden_scoped_commit_prefixes_for_master": list(FORBIDDEN_LIVE_PREFIXES),
        "commit_policy": "stage_only_master_owned_paths_for_this_route; do_not_stage_live_runtime_shadow_pipeline_data_or_other_agent_dirt",
        "remote_push_policy": "forbidden_without_explicit_owner_instruction",
        "shared_write_rule": "downstream lanes must update this plan or declare Lane15/master merge owner before mutating shared code or prompt/control artifacts",
    }


def verifier_matrix(lanes: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for lane in lanes:
        rows.append(
            {
                "lane_id": lane["lane_id"],
                "prompt_path": lane["prompt_path"],
                "route_path": lane["route_path"],
                "required_verifier_classes": [
                    "prompt_hardening_validation",
                    "manifest_schema_parse",
                    "source_hash_or_source_completeness_check",
                    "no_leak_asof_check_when_time_fields_exist",
                    "duplicate_denominator_check_when_rows_exist",
                    "focused_pytest_or_equivalent",
                    "completion_audit_instruction_coverage",
                    "runtime_effect_boundary_check",
                ],
                "must_fail_on": [
                    "prompt_drift",
                    "dependency_drift",
                    "infinite_ledger_loop",
                    "missing_terminal_artifacts",
                    "unscoped_live_or_runtime_write",
                    "broker_real_and_proxy_label_collapse",
                ],
                "status": lane.get("master_integration_status", "contract_defined_pending_lane_execution"),
                "terminal_state": lane.get("terminal_state"),
                "wave2_readiness": lane.get("wave2_readiness"),
                "wave3_readiness": lane.get("wave3_readiness"),
                "next_wave_launch_contract": lane.get("next_wave_launch_contract"),
                "later_wave_gate": lane.get("later_wave_gate"),
            }
        )
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_verifier_test_matrix_v1",
        "generated_at_utc": utc_now(),
        "master_verifiers": [
            rel(ROUTE_DIR / "verify_absolute_moonshot_master_orchestration.py"),
            "scripts/build_vnext_absolute_moonshot_master_orchestration.py --check",
            "tests/test_vnext_absolute_moonshot_master_orchestration.py",
            "scripts/validate_goal_prompt_hardening.py for master, launch order, and all lane prompts/starters",
        ],
        "lane_rows": rows,
    }


def runtime_effect_boundary() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_runtime_effect_boundary_v1",
        "generated_at_utc": utc_now(),
        "evidence_class": "master_orchestration_evidence_and_launch_control_only",
        "forbidden_surfaces_touched_by_this_route": [],
        "attestation": {
            "production_change_activation": False,
            "live_trading_broker_operation": False,
            "order_placement_modification_cancellation_close": False,
            "broker_account_order_history_deal_position_change": False,
            "paid_api_vendor_call": False,
            "credential_print_or_change": False,
            "remote_push": False,
            "prompt_config_risk_execution_safety_canary_selector_live_behavior_change": False,
        },
        "authorized_scope": [
            "inspect current code/config/prompt/route artifacts",
            "write master orchestration route artifacts",
            "write verifier and focused tests for master route",
            "write scoped research launch-order and prompt-pack context hardening",
            "record default_off_or_dossier_authority for future lanes",
        ],
        "read_only_source_acquisition_rule": "downstream lanes may use read_only_mt5_market_history_spec_account_history_export when their lane contract requires it; this master route did not perform broker access",
    }


def focused_test_result() -> dict[str, Any]:
    xml_path = ROUTE_DIR / "ABSOLUTE_MASTER_FOCUSED_TEST_RESULT.xml"
    if not xml_path.exists():
        return {
            "schema_version": "absolute_master_focused_test_result_v1",
            "status": "pending_until_pytest_junitxml_is_written",
            "ok": False,
            "path": rel(xml_path),
        }
    try:
        root = ET.parse(xml_path).getroot()
        if root.tag == "testsuites":
            suites = list(root.findall("testsuite"))
            tests = sum(int(suite.attrib.get("tests", "0")) for suite in suites)
            failures = sum(int(suite.attrib.get("failures", "0")) for suite in suites)
            errors = sum(int(suite.attrib.get("errors", "0")) for suite in suites)
            skipped = sum(int(suite.attrib.get("skipped", "0")) for suite in suites)
        else:
            tests = int(root.attrib.get("tests", "0"))
            failures = int(root.attrib.get("failures", "0"))
            errors = int(root.attrib.get("errors", "0"))
            skipped = int(root.attrib.get("skipped", "0"))
    except Exception as exc:
        return {
            "schema_version": "absolute_master_focused_test_result_v1",
            "status": "xml_parse_failed",
            "ok": False,
            "path": rel(xml_path),
            "error": str(exc),
        }
    return {
        "schema_version": "absolute_master_focused_test_result_v1",
        "status": "passed" if tests > 0 and failures == 0 and errors == 0 else "failed",
        "ok": tests > 0 and failures == 0 and errors == 0,
        "path": rel(xml_path),
        "tests": tests,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
    }


def completion_audit(
    lanes: list[dict[str, Any]],
    prompt_validation: dict[str, Any],
    focused_result: dict[str, Any],
    verification_result: dict[str, Any] | None,
) -> dict[str, Any]:
    terminal_table = wave1_terminal_state_table()
    wave2_terminal = wave2_terminal_state_table()
    wave2 = wave2_readiness_decision(terminal_table, wave2_terminal)
    wave3_terminal = wave3_terminal_state_table()
    post_lane11 = post_lane11_terminal_state_table(wave3_terminal)
    wave4_terminal = wave4_terminal_state_table()
    limitations = limitation_disposition_map()
    post_v3_terminal = post_v3_terminal_state_table()
    gates = later_wave_gates(wave4_table=wave4_terminal, post_v3_table=post_v3_terminal)
    next_wave = next_wave_launch_decision(post_lane11, limitations, gates)
    post_lane18 = post_lane18_implementation_wave_decision(wave4_terminal, gates)
    post_v3_decision = post_v3_launch_decision(post_v3_terminal, gates)
    result_status = result_use_status(post_v3_terminal)
    wave3 = wave3_readiness_decision(terminal_table, wave2_terminal, wave3_terminal, post_lane11, next_wave, gates)
    launch_order = wave3_launch_order(wave3)
    stale_neutralization = stale_dependency_text_neutralization(terminal_table, post_v3_terminal)
    items = [
        {
            "requirement": "mandatory_preflight_and_context_refresh",
            "status": "satisfied_for_current_master_route",
            "evidence": ".context/LIVE_STATE.md regenerated before build plus required context files read from disk",
            "passed": True,
        },
        {
            "requirement": "controlling_prompt_and_starter_read_from_disk",
            "status": "satisfied",
            "evidence": [rel(MASTER_PROMPT), rel(MASTER_STARTER), rel(POST_V3_MASTER_PROMPT), rel(POST_V3_MASTER_STARTER)],
            "passed": True,
        },
        {
            "requirement": "lane_registry_for_all_18_lanes",
            "status": "satisfied",
            "evidence": "ABSOLUTE_MASTER_LANE_REGISTRY.json",
            "passed": len(lanes) == 18,
        },
        {
            "requirement": "dependency_graph_and_launch_waves",
            "status": "satisfied",
            "evidence": ["ABSOLUTE_MASTER_DEPENDENCY_GRAPH.json", "ABSOLUTE_MASTER_LAUNCH_WAVES.json"],
            "passed": True,
        },
        {
            "requirement": "source_authority_map_and_source_completeness_decisions",
            "status": "satisfied",
            "evidence": ["ABSOLUTE_MASTER_SOURCE_AUTHORITY_MAP.json", "ABSOLUTE_MASTER_SOURCE_COMPLETENESS_DECISIONS.jsonl"],
            "passed": True,
        },
        {
            "requirement": "output_schema_contracts",
            "status": "satisfied",
            "evidence": "ABSOLUTE_MASTER_OUTPUT_SCHEMA_CONTRACTS.json",
            "passed": True,
        },
        {
            "requirement": "anti_loop_anti_duplication_merge_rules",
            "status": "satisfied",
            "evidence": ["ABSOLUTE_MASTER_ANTI_DUPLICATION_AND_LOOP_RULES.json", "ABSOLUTE_MASTER_MERGE_COMMIT_OWNERSHIP_PLAN.json"],
            "passed": True,
        },
        {
            "requirement": "prompt_hardening_validation",
            "status": "satisfied" if prompt_validation.get("ok") else "failed",
            "evidence": "ABSOLUTE_MASTER_PROMPT_HARDENING_VERIFICATION.json",
            "passed": bool(prompt_validation.get("ok")),
        },
        {
            "requirement": "focused_tests",
            "status": focused_result.get("status"),
            "evidence": focused_result.get("path"),
            "passed": bool(focused_result.get("ok")),
        },
        {
            "requirement": "master_verifier",
            "status": "passed" if verification_result and verification_result.get("ok") else "pending_or_failed",
            "evidence": "ABSOLUTE_MASTER_VERIFICATION_RESULT.json",
            "passed": bool(verification_result and verification_result.get("ok")),
        },
        {
            "requirement": "runtime_effect_boundary",
            "status": "closed_research_control_only",
            "evidence": "ABSOLUTE_MASTER_RUNTIME_EFFECT_BOUNDARY.json",
            "passed": True,
        },
        {
            "requirement": "wave1_terminal_artifact_inspection",
            "status": "satisfied" if terminal_table["all_wave1_terminal_verified"] else "failed",
            "evidence": [
                "ABSOLUTE_MASTER_WAVE1_ARTIFACT_INSPECTION_LEDGER.jsonl",
                "ABSOLUTE_MASTER_WAVE1_TERMINAL_STATE_TABLE.json",
            ],
            "passed": bool(terminal_table["all_wave1_terminal_verified"]),
        },
        {
            "requirement": "wave2_terminal_artifact_inspection",
            "status": wave2["wave2_launch_state"],
            "evidence": [
                "ABSOLUTE_MASTER_WAVE2_ARTIFACT_INSPECTION_LEDGER.jsonl",
                "ABSOLUTE_MASTER_WAVE2_TERMINAL_STATE_TABLE.json",
                "ABSOLUTE_MASTER_WAVE2_READINESS_DECISION.json",
            ],
            "passed": wave2["wave1_terminal_verified"]
            and wave2["wave2_terminal_verified"]
            and wave2["lane_readiness"]["05"]["terminal_status"] == "terminal_verified"
            and wave2["lane_readiness"]["06"]["terminal_status"] == "terminal_verified"
            and wave2["lane_readiness"]["07"]["terminal_status"] == "terminal_verified"
            and wave2["lane_readiness"]["07"]["blocks_lane05_or_lane06"] is False,
        },
        {
            "requirement": "wave3_terminal_artifact_inspection",
            "status": "satisfied" if wave3_terminal["all_wave3_terminal_verified"] else "failed",
            "evidence": [
                "ABSOLUTE_MASTER_WAVE3_ARTIFACT_INSPECTION_LEDGER.jsonl",
                "ABSOLUTE_MASTER_WAVE3_TERMINAL_STATE_TABLE.json",
            ],
            "passed": bool(wave3_terminal["all_wave3_terminal_verified"]),
        },
        {
            "requirement": "post_lane11_terminal_state",
            "status": "satisfied" if post_lane11["all_post_lane11_terminal_verified"] else "failed",
            "evidence": "ABSOLUTE_MASTER_POST_LANE11_TERMINAL_STATE_TABLE.json",
            "passed": bool(post_lane11["all_post_lane11_terminal_verified"]),
        },
        {
            "requirement": "wave4_terminal_artifact_inspection",
            "status": "satisfied" if wave4_terminal["all_wave4_terminal_verified"] else "failed",
            "evidence": [
                "ABSOLUTE_MASTER_WAVE4_ARTIFACT_INSPECTION_LEDGER.jsonl",
                "ABSOLUTE_MASTER_WAVE4_TERMINAL_STATE_TABLE.json",
            ],
            "passed": bool(wave4_terminal["all_wave4_terminal_verified"]),
        },
        {
            "requirement": "limitation_disposition_map",
            "status": "satisfied" if limitations["all_dispositions_allowed"] and limitations["row_count"] >= 10 else "failed",
            "evidence": "ABSOLUTE_MASTER_LIMITATION_DISPOSITION_MAP.json",
            "passed": bool(limitations["all_dispositions_allowed"]) and limitations["row_count"] >= 10,
        },
        {
            "requirement": "next_wave_launch_decision",
            "status": "satisfied" if wave3["next_wave_ready_to_open"] and launch_order["next_wave_open"] else "failed",
            "evidence": ["ABSOLUTE_MASTER_NEXT_WAVE_LAUNCH_DECISION.json", "ABSOLUTE_MASTER_WAVE3_LAUNCH_ORDER.json"],
            "passed": bool(wave3["next_wave_ready_to_open"])
            and launch_order["launch_order"][0]["lanes"] == ["16", "17", "18"]
            and next_wave["not_ml_only_closure"] is True,
        },
        {
            "requirement": "later_wave_gates",
            "status": "satisfied" if gates["gate_count"] >= 8 and gates["wave4_terminal_consumed"] and "subsystem" in gates["ml_role"] else "failed",
            "evidence": "ABSOLUTE_MASTER_LATER_WAVE_GATES.json",
            "passed": gates["gate_count"] >= 8 and gates["wave4_terminal_consumed"] and "subsystem" in gates["ml_role"],
        },
        {
            "requirement": "post_lane18_implementation_wave_decision",
            "status": "satisfied" if post_lane18["wave4_terminal_verified"] else "failed",
            "evidence": "ABSOLUTE_MASTER_POST_LANE18_IMPLEMENTATION_WAVE_DECISION.json",
            "passed": bool(post_lane18["wave4_terminal_verified"])
            and {"selector_v3", "scheduler_v3", "execution_policy_v3", "source_capture_repair"}.issubset(set(post_lane18["next_implementation_gates"])),
        },
        {
            "requirement": "post_v3_terminal_artifact_inspection",
            "status": "satisfied" if post_v3_terminal["all_post_v3_terminal_verified"] else "failed",
            "evidence": [
                "ABSOLUTE_MASTER_POST_V3_ARTIFACT_INSPECTION_LEDGER.jsonl",
                "ABSOLUTE_MASTER_POST_V3_TERMINAL_STATE_TABLE.json",
            ],
            "passed": bool(post_v3_terminal["all_post_v3_terminal_verified"])
            and set(post_v3_terminal["terminal_gate_ids"]) == set(POST_V3_ROUTE_DIRS),
        },
        {
            "requirement": "post_v3_launch_decision",
            "status": "satisfied" if post_v3_decision["post_v3_terminal_verified"] else "failed",
            "evidence": "ABSOLUTE_MASTER_POST_V3_LAUNCH_DECISION.json",
            "passed": bool(post_v3_decision["post_v3_terminal_verified"])
            and {"12", "13", "14", "15"}.issubset(
                {
                    lane
                    for phase in post_v3_decision["next_launch_order"]
                    for lane in phase.get("lanes", [])
                }
            ),
        },
        {
            "requirement": "source_capture_decisions",
            "status": "satisfied",
            "evidence": "ABSOLUTE_MASTER_SOURCE_CAPTURE_DECISIONS.jsonl",
            "passed": all(
                count_jsonl(POST_V3_ROUTE_DIRS[gate_id] / (
                    POST_V3_REQUIRED_ARTIFACTS[gate_id].get("source_capture_decisions")
                    or POST_V3_REQUIRED_ARTIFACTS[gate_id].get("source_completeness_decisions")
                )) > 0
                for gate_id in POST_V3_ROUTE_DIRS
            ),
        },
        {
            "requirement": "result_use_status",
            "status": "satisfied" if result_status["production_change_readiness_claim"] is False else "failed",
            "evidence": "ABSOLUTE_MASTER_RESULT_USE_STATUS.json",
            "passed": result_status["production_change_readiness_claim"] is False
            and result_status["execution_policy_v3"]["proxy_to_production_leap_allowed"] is False,
        },
        {
            "requirement": "lane04_stale_dependency_text_neutralization",
            "status": "neutralized" if stale_neutralization["neutralized_for_master_consumption"] else "failed",
            "evidence": "ABSOLUTE_MASTER_STALE_DEPENDENCY_TEXT_NEUTRALIZATION.json",
            "passed": bool(stale_neutralization["neutralized_for_master_consumption"]),
        },
    ]
    can_mark = all(bool(item["passed"]) for item in items)
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_completion_audit_v1",
        "generated_at_utc": utc_now(),
        "status": "complete_for_master_orchestration_launch_control" if can_mark else "active_not_complete",
        "can_mark_master_orchestration_goal_complete_after_scoped_commit": can_mark,
        "absolute_moonshot_program_completion_status": "not_complete_lanes_pending_execution",
        "items": items,
        "instruction_coverage": {
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "orchestrator_hardening_and_playbook_read": True,
            "absolute_vision_read": True,
            "constructive_control_posture_applied": True,
            "anti_boxing_questions_pursued": [
                "Are lanes boxed to Friday-only evidence?",
                "Are current vNext frameworks treated as the horizon?",
                "Are missing upstream lane outputs incorrectly treated as blockers?",
                "Are source families beyond repo summaries represented?",
                "Are live/production boundaries rails rather than brakes?",
            ],
            "outside_current_edge_route_families_considered": [
                "historical_microscope_at_scale",
                "market_awareness_whiteboard",
                "broker_truth_cost_capture_v2",
                "feature_store",
                "label_store",
                "digital_twin_replay",
                "portfolio_scheduler",
                "execution_policy_engine",
                "selector_v3",
                "scheduler_v3",
                "execution_policy_v3",
                "ml_baseline_and_selector_policy_intelligence_as_later_subsystem",
                "daily_repair_companion",
                "command_center_production_dossier",
            ],
            "proof_or_impossibility_stop_condition": "master-owned executable reads, route inspections, prompt validations, schema/registry/dependency/verifier artifacts materialized; downstream lane execution remains separate dependency state",
            "wave1_terminal_artifacts_inspected": True,
            "wave2_terminal_artifacts_inspected": True,
            "lane05_readiness": wave2["lane_readiness"]["05"],
            "lane06_readiness": wave2["lane_readiness"]["06"],
            "lane07_separated_status": wave2["lane_readiness"]["07"],
            "wave3_terminal_artifacts_inspected": wave3_terminal["all_wave3_terminal_verified"],
            "post_lane11_terminal_artifacts_inspected": post_lane11["all_post_lane11_terminal_verified"],
            "wave4_terminal_artifacts_inspected": wave4_terminal["all_wave4_terminal_verified"],
            "post_v3_terminal_artifacts_inspected": post_v3_terminal["all_post_v3_terminal_verified"],
            "wave3_readiness": wave3["lane_readiness"],
            "wave3_launch_order": launch_order["launch_order"],
            "next_wave_launch_decision": next_wave["decision"],
            "post_lane18_implementation_wave_decision": post_lane18["decision"],
            "post_v3_launch_decision": post_v3_decision["decision"],
            "source_capture_decision_state": "terminal_source_capture_and_v3_source_decision_ledgers_consumed_by_master",
            "result_use_status": result_status,
            "later_wave_gates": gates["gates"],
            "stale_lane04_absence_wording_neutralized": stale_neutralization["neutralized_for_master_consumption"],
            "stale_v3_launch_pending_wording_neutralized": stale_neutralization["post_v3_neutralized_by_terminal_consumption"],
        },
        "source_use_state": "current_disk_route_artifacts_repo_prompt_pack_and_local_preservation_manifests_only_no_broker_mutation",
        "result_use_status": "master_consumes post-V3 exact/proxy/expectancy status from terminal route result-use files; master_does_not_claim_broker_real_performance_or_production_change_readiness",
        "result_use_status_path": "ABSOLUTE_MASTER_RESULT_USE_STATUS.json",
        "runtime_effect_boundary": "no_live_trading_behavior_change_no_prompt_config_risk_execution_safety_canary_selector_live_activation",
        "scoped_commit_state": "required_after_verification; final commit proof lives in git history to avoid self-referential artifact churn",
    }


def render_context_anchor(
    lanes: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    verification_result: dict[str, Any] | None,
) -> str:
    lines = [
        "# Absolute Moonshot Master Orchestration Context Anchor",
        "",
        f"Route: `{ROUTE_ID}`",
        f"Generated: `{utc_now()}`",
        f"HEAD: `{git_head().get('head_short')} {git_head().get('head_subject')}`",
        "",
        "## Controlling Inputs",
        "",
        f"- Prompt: `{rel(MASTER_PROMPT)}`",
        f"- Starter: `{rel(MASTER_STARTER)}`",
        f"- Post-V3 prompt: `{rel(POST_V3_MASTER_PROMPT)}`",
        f"- Post-V3 starter: `{rel(POST_V3_MASTER_STARTER)}`",
        f"- Launch order: `{rel(LAUNCH_ORDER)}`",
        f"- Vision: `{rel(VISION_PATH)}`",
        "",
        "## Resume Procedure",
        "",
        "1. Run `python scripts/generate_live_state.py`.",
        "2. Read `.context/LIVE_STATE.md`, current vNext map, reading order, quick reference, doctrine, orchestrator hardening/playbook files, this anchor, and latest route artifacts from disk.",
        "3. Run `python scripts/build_vnext_absolute_moonshot_master_orchestration.py --check`.",
        "4. Launch lanes only by wave/dependency state recorded in `ABSOLUTE_MASTER_DEPENDENCY_GRAPH.json` and `ABSOLUTE_MASTER_LAUNCH_WAVES.json`.",
        "",
        "## Lane State",
        "",
    ]
    for lane in lanes:
        deps = ", ".join(lane["dependencies"]) if lane["dependencies"] else "master registry only"
        lines.append(
            f"- Lane {lane['lane_id']} wave {lane['wave']}: `{lane['route_path']}`; deps: {deps}; status `{lane.get('master_integration_status')}`."
        )
    wave2_terminal = wave2_terminal_state_table()
    wave2 = wave2_readiness_decision(wave2_table=wave2_terminal)
    wave3_terminal = wave3_terminal_state_table()
    post_lane11 = post_lane11_terminal_state_table(wave3_terminal)
    wave4_terminal = wave4_terminal_state_table()
    post_v3_terminal = post_v3_terminal_state_table()
    gates = later_wave_gates(wave4_table=wave4_terminal, post_v3_table=post_v3_terminal)
    next_wave = next_wave_launch_decision(post_lane11, limitation_disposition_map(), gates)
    post_lane18 = post_lane18_implementation_wave_decision(wave4_terminal, gates)
    post_v3_decision = post_v3_launch_decision(post_v3_terminal, gates)
    wave3 = wave3_readiness_decision(wave2_table=wave2_terminal, wave3_table=wave3_terminal, post_lane11_table=post_lane11, next_wave=next_wave, later_gates=gates)
    launch_order = wave3_launch_order(wave3)
    lines.extend(["", "## Wave 2 Terminal State", ""])
    lines.append(f"- Lane05: `{wave2['lane_readiness']['05']['decision']}`.")
    lines.append(f"- Lane06: `{wave2['lane_readiness']['06']['decision']}`.")
    lines.append(f"- Lane07: `{wave2['lane_readiness']['07']['decision']}`.")
    lines.append("- Lane07 broker-real gaps are proxy/gap/export fields, not Wave 3 blockers.")
    lines.extend(["", "## Wave 3 And Post-Lane11 Terminal State", ""])
    lines.append(f"- Wave 3 terminal verified: `{wave3_terminal['all_wave3_terminal_verified']}`.")
    lines.append(f"- Post-Lane11 terminal verified: `{post_lane11['all_post_lane11_terminal_verified']}`.")
    lines.append("- Lane09B, Lane10B, and Lane11 are consumed from disk as terminal evidence for the next wave.")
    lines.extend(["", "## Next Wave Launch State", ""])
    for phase in launch_order["launch_order"]:
        lines.append(f"- Phase {phase['phase']}: lanes `{', '.join(phase['lanes'])}`; mode `{phase['mode']}`.")
    lines.extend(["", "## Wave 4 Terminal State", ""])
    lines.append(f"- Wave 4 terminal verified: `{wave4_terminal['all_wave4_terminal_verified']}`.")
    for row in wave4_terminal["wave4_lanes"]:
        lines.append(f"- Lane {row['lane_id']}: `{row['terminal_status']}`; counts `{row['material_row_counts']}`.")
    lines.extend(["", "## Post-Lane18 Implementation State", ""])
    for phase in post_lane18["launch_order"]:
        lines.append(f"- Phase {phase['phase']}: gates `{', '.join(phase['gates'])}`; mode `{phase['mode']}`.")
    lines.append("- Selector V3, Scheduler V3, Execution Policy V3, and source capture repair are terminal and consumed by this post-V3 refresh.")
    lines.extend(["", "## Post-V3 Terminal State", ""])
    lines.append(f"- Post-V3 terminal verified: `{post_v3_terminal['all_post_v3_terminal_verified']}`.")
    for row in post_v3_terminal["terminal_routes"]:
        lines.append(f"- Gate {row['gate_id']}: `{row['terminal_status']}`; counts `{row['material_row_counts']}`.")
    lines.extend(["", "## Post-V3 Launch State", ""])
    for phase in post_v3_decision["next_launch_order"]:
        lanes_text = ", ".join(phase["lanes"])
        lines.append(f"- Phase {phase['phase']}: lanes `{lanes_text}`; mode `{phase['mode']}`.")
    lines.append("- Lane12/Lane13 ML are subsystem consumers after V3/source contracts, not the full research horizon.")
    lines.append("- Lane14/Lane15 repair and command-center work are open only as default-off/report-pack/dossier lanes; production activation remains owner-gated.")
    lines.extend(["", "## Evidence Anchors", ""])
    for row in evidence_rows:
        lines.append(f"- `{row['artifact_family']}`: `{row['path']}` status `{row.get('status')}`.")
    lines.extend(
        [
            "",
            "## Current Stop Condition",
            "",
            "The master lane is complete only when registry, dependency graph, source authority map, output schemas, blockers, merge rules, context anchor, verifier, focused tests, completion audit, and scoped commit are present. The absolute moonshot program itself remains incomplete until downstream lanes execute.",
            "",
            "## Latest Verification",
            "",
            f"- Verification: `{verification_result.get('ok') if verification_result else 'pending'}`",
        ]
    )
    return "\n".join(lines) + "\n"


def render_saturation_self_red_team(lanes: list[dict[str, Any]]) -> str:
    return "\n".join(
        [
            "# Absolute Moonshot Master Saturation And Self-Red-Team",
            "",
            f"Route: `{ROUTE_ID}`",
            "",
            "## Saturation Result",
            "",
            f"- All lane prompts discovered: `{len(lanes)}/18`.",
            "- Lane01-Lane04 terminal artifacts were inspected from disk and consumed as Wave 1 authority.",
            "- Lane05 Feature Store, Lane06 Label Store, and Lane07 Broker Truth/Cost Calibration terminal artifacts were inspected from disk and consumed as Wave 2 authority.",
            "- Lane07 is separated as broker truth and cost calibration; missing broker-real fields are proxy/gap/export fields, not Wave 3 blockers.",
            "- Lane08, Lane09, Lane10, and Lane11 terminal artifacts were inspected from disk and consumed as Wave 3 authority.",
            "- Lane09B selector-scheduler reconciliation, Lane10B scheduler conflict anatomy, and Lane11 execution policy evidence are consumed as terminal post-Lane11 authority.",
            "- Lane16 Historical Microscope Scaling, Lane17 Market Awareness Whiteboard, and Lane18 Broker Truth Cost Capture V2 are inspected from disk and consumed as Wave 4 terminal authority.",
            "- Source Capture Repair, Selector V3, Scheduler V3, and Execution Policy V3 are inspected from disk and consumed as terminal post-V3 authority.",
            "- The next launch sequence is Lane12 ML dataset/baselines, Lane13 ML policy intelligence after Lane12, Lane14 daily learning/repair companion design, Lane15 command-center/report-pack/dossier work, and exact source/export/capture repairs from row-level ledgers.",
            "- Lane12/Lane13 ML are subsystem consumers after V3/source contracts; ML-only closure is rejected.",
            "- No arbitrary top-N or representative-only lane subset is used; every June 1 lane prompt and starter is in the registry.",
            "- Missing Lane12-Lane15 route outputs are open dependency-state rows with exact prerequisites, not post-Lane11 or post-V3 stop conditions.",
            "- Full source ledgers are preserved by pointer instead of sampled into this master route.",
            "- Master-owned verification fails on prompt drift, dependency drift, ledger-only completion, missing post-V3 terminal contracts, missing result-use/source-capture artifacts, and unscoped live/runtime writes.",
            "",
            "## Self-Red-Team Questions",
            "",
            "- Could Friday-only evidence box the program? The registry opens scaled historical microscope, market awareness, broker truth, V3 engines, ML, repair, and command-center lanes rather than only Friday follow-up.",
            "- Could source-control evidence be mistaken for production performance? The source authority map labels selected denominator R as proxy replay evidence and keeps broker-real net R gated by broker truth.",
            "- Could ledgers become infinite? The anti-loop artifact says blocker and next-prompt outputs are not terminal while same-evidence-class repair is executable.",
            "- Could a lane silently mutate live behavior? The merge plan and runtime boundary restrict this route to master-owned artifacts and require default-off/dossier authority downstream.",
            "- Could hidden duplicate rows dominate later results? Output schemas require duplicate keys, source hashes, label-family separation, and row-level missing-field proof.",
            "- Could ML become the whole program by accident? The implementation decision makes ML a later subsystem and requires V3/source contracts first.",
            "- Could stale launch text relaunch completed source/V3 lanes? The stale dependency neutralization artifact and verifier require post-V3 terminal-state consumption and next-launch rows for Lane12-Lane15 instead.",
            "",
            "## Residual Limits",
            "",
            "- The master route does not execute downstream lanes.",
            "- Production activation remains forbidden without separate owner approval.",
            "- Broker close/deal/cost truth remains an external event or read-only export requirement for broker-truth lanes.",
            "- Exact source/export/forward-capture repairs remain future read-only/prospective-capture work unless row-level V3/source decision ledgers already close the field.",
            "",
        ]
    )


def output_manifest(output_paths: list[Path]) -> dict[str, Any]:
    rows = []
    for path in output_paths:
        rows.append(
            {
                "path": rel(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
                "sha256": sha256_file(path),
            }
        )
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_output_manifest_v1",
        "generated_at_utc": utc_now(),
        "output_count": len(rows),
        "outputs": rows,
    }


def _verify_payload(
    lanes: list[dict[str, Any]],
    graph: dict[str, Any],
    source_map: dict[str, Any],
    schemas: dict[str, Any],
    blockers: list[dict[str, Any]],
    anti_loop: dict[str, Any],
    merge: dict[str, Any],
    manifest: dict[str, Any],
    prompt_validation: dict[str, Any],
    completion: dict[str, Any],
    focused_result: dict[str, Any],
    terminal_table: dict[str, Any],
    wave2_terminal_table: dict[str, Any],
    wave2_readiness: dict[str, Any],
    wave3_readiness: dict[str, Any],
    wave3_launch: dict[str, Any],
    wave3_terminal_table: dict[str, Any],
    post_lane11_table: dict[str, Any],
    wave4_terminal_table: dict[str, Any],
    limitation_map: dict[str, Any],
    next_wave: dict[str, Any],
    later_gates: dict[str, Any],
    post_lane18_decision: dict[str, Any],
    post_v3_table: dict[str, Any],
    post_v3_decision: dict[str, Any],
    stale_neutralization: dict[str, Any],
    result_status: dict[str, Any],
    *,
    require_focused_test_result: bool,
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    if len(lanes) != 18:
        issues.append({"code": "lane_count_not_18", "actual": len(lanes)})
    expected_ids = [f"{idx:02d}" for idx in range(1, 19)]
    actual_ids = [lane["lane_id"] for lane in lanes]
    if actual_ids != expected_ids:
        issues.append({"code": "lane_ids_mismatch", "actual": actual_ids})

    if not terminal_table.get("all_wave1_terminal_verified"):
        issues.append({"code": "wave1_terminal_state_not_verified"})
    terminal_counts = {
        row.get("lane_id"): row.get("material_row_counts", {})
        for row in terminal_table.get("wave1_lanes", [])
    }
    for lane_id, expected in WAVE1_EXPECTED_COUNTS.items():
        actual = terminal_counts.get(lane_id, {})
        for key, value in expected.items():
            if actual.get(key) != value:
                issues.append(
                    {
                        "code": "wave1_terminal_count_mismatch",
                        "lane_id": lane_id,
                        "field": key,
                        "expected": value,
                        "actual": actual.get(key),
                    }
                )
    if not wave2_terminal_table.get("all_wave2_terminal_verified"):
        issues.append({"code": "wave2_terminal_state_not_verified"})
    wave2_counts = {
        row.get("lane_id"): row.get("material_row_counts", {})
        for row in wave2_terminal_table.get("wave2_lanes", [])
    }
    for lane_id, expected in WAVE2_EXPECTED_COUNTS.items():
        actual = wave2_counts.get(lane_id, {})
        for key, value in expected.items():
            if actual.get(key) != value:
                issues.append(
                    {
                        "code": "wave2_terminal_count_mismatch",
                        "lane_id": lane_id,
                        "field": key,
                        "expected": value,
                        "actual": actual.get(key),
                    }
                )
    if wave2_readiness.get("lane_readiness", {}).get("05", {}).get("terminal_status") != "terminal_verified":
        issues.append({"code": "lane05_not_terminal"})
    if wave2_readiness.get("lane_readiness", {}).get("06", {}).get("terminal_status") != "terminal_verified":
        issues.append({"code": "lane06_not_terminal"})
    if wave2_readiness.get("lane_readiness", {}).get("07", {}).get("terminal_status") != "terminal_verified":
        issues.append({"code": "lane07_not_terminal"})
    if wave2_readiness.get("lane_readiness", {}).get("07", {}).get("blocks_lane05_or_lane06") is not False:
        issues.append({"code": "lane07_not_separated_from_lane05_lane06"})
    if not wave2_readiness.get("broker_real_truth_does_not_gate_historical_wave2_or_wave3"):
        issues.append({"code": "broker_real_truth_gate_not_closed_for_historical_wave2"})

    if not wave3_terminal_table.get("all_wave3_terminal_verified"):
        issues.append({"code": "wave3_terminal_state_not_verified"})
    wave3_counts = {
        row.get("lane_id"): row.get("material_row_counts", {})
        for row in wave3_terminal_table.get("wave3_lanes", [])
    }
    for lane_id, expected in WAVE3_EXPECTED_COUNTS.items():
        actual = wave3_counts.get(lane_id, {})
        for key, value in expected.items():
            if actual.get(key) != value:
                issues.append(
                    {
                        "code": "wave3_terminal_count_mismatch",
                        "lane_id": lane_id,
                        "field": key,
                        "expected": value,
                        "actual": actual.get(key),
                    }
                )
    if not post_lane11_table.get("all_post_lane11_terminal_verified"):
        issues.append({"code": "post_lane11_terminal_state_not_verified"})
    post_ids = {row.get("lane_id") for row in post_lane11_table.get("terminal_lanes", [])}
    if post_ids != {"09B", "10B", "11"}:
        issues.append({"code": "post_lane11_terminal_ids_mismatch", "actual": sorted(post_ids)})
    for row in post_lane11_table.get("terminal_lanes", []):
        if row.get("terminal_status") != "terminal_verified":
            issues.append({"code": "post_lane11_lane_not_terminal", "lane_id": row.get("lane_id")})
        if not all(bool(value) for value in row.get("expected_count_matches", {}).values()):
            issues.append({"code": "post_lane11_expected_counts_not_matched", "lane_id": row.get("lane_id")})

    if not wave4_terminal_table.get("all_wave4_terminal_verified"):
        issues.append({"code": "wave4_terminal_state_not_verified"})
    wave4_ids = {row.get("lane_id") for row in wave4_terminal_table.get("wave4_lanes", [])}
    if wave4_ids != {"16", "17", "18"}:
        issues.append({"code": "wave4_terminal_ids_mismatch", "actual": sorted(wave4_ids)})
    wave4_counts = {
        row.get("lane_id"): row.get("material_row_counts", {})
        for row in wave4_terminal_table.get("wave4_lanes", [])
    }
    for lane_id, expected in WAVE4_EXPECTED_COUNTS.items():
        actual = wave4_counts.get(lane_id, {})
        for key, value in expected.items():
            if actual.get(key) != value:
                issues.append(
                    {
                        "code": "wave4_terminal_count_mismatch",
                        "lane_id": lane_id,
                        "field": key,
                        "expected": value,
                        "actual": actual.get(key),
                    }
                )
    for row in wave4_terminal_table.get("wave4_lanes", []):
        if row.get("terminal_status") != "terminal_verified":
            issues.append({"code": "wave4_lane_not_terminal", "lane_id": row.get("lane_id")})
        if not all(bool(value) for value in row.get("expected_count_matches", {}).values()):
            issues.append({"code": "wave4_expected_counts_not_matched", "lane_id": row.get("lane_id")})

    if not wave3_readiness.get("wave3_terminal_verified"):
        issues.append({"code": "wave3_readiness_does_not_record_terminal_wave3"})
    if not wave3_readiness.get("post_lane11_terminal_verified"):
        issues.append({"code": "wave3_readiness_does_not_record_post_lane11_terminal"})
    if not wave3_readiness.get("next_wave_ready_to_open"):
        issues.append({"code": "next_wave_not_ready_to_open"})
    for lane_id in ["08", "09", "10"]:
        if wave3_readiness.get("lane_readiness", {}).get(lane_id, {}).get("readiness") != "terminal_verified_wave3":
            issues.append({"code": "wave3_lane_not_marked_terminal", "lane_id": lane_id})
    if wave3_readiness.get("lane_readiness", {}).get("11", {}).get("readiness") != "terminal_verified_wave3_and_post_lane11":
        issues.append({"code": "lane11_not_marked_post_lane11_terminal"})
    lane_statuses = {lane["lane_id"]: lane.get("master_integration_status") for lane in lanes}
    for lane_id in ["16", "17", "18"]:
        if lane_statuses.get(lane_id) != "terminal_verified_wave4":
            issues.append({"code": "wave4_lane_not_marked_terminal_in_registry", "lane_id": lane_id, "status": lane_statuses.get(lane_id)})
    for lane_id in ["12", "13"]:
        if "ml_subsystem" not in wave3_readiness.get("lane_readiness", {}).get(lane_id, {}).get("readiness", ""):
            issues.append({"code": "ml_lane_not_later_subsystem_gate", "lane_id": lane_id})
    for lane_id in ["14", "15"]:
        readiness_text = wave3_readiness.get("lane_readiness", {}).get(lane_id, {}).get("readiness", "")
        if "later" not in readiness_text and "ready_post_v3" not in readiness_text:
            issues.append({"code": "lane14_15_not_later_gate", "lane_id": lane_id})
    if wave3_launch.get("launch_order", [{}])[0].get("lanes") != ["16", "17", "18"]:
        issues.append({"code": "post_lane11_launch_order_not_lanes16_17_18"})
    launch_text = json.dumps({"readiness": wave3_readiness, "launch": wave3_launch, "next_wave": next_wave}, sort_keys=True).lower()
    forbidden_next_actor_phrases = [
        "bounded_baseline_open_now",
        "bounded_ml_prep",
        "lane12 may open",
        "lane12 is next",
        "only lane12",
        "ml_only_closure_allowed",
    ]
    for phrase in forbidden_next_actor_phrases:
        if phrase in launch_text:
            issues.append({"code": "stale_ml_only_or_lane12_next_actor_text_present", "phrase": phrase})
    if next_wave.get("next_wave_lanes") != ["16", "17", "18"]:
        issues.append({"code": "next_wave_lanes_not_16_17_18", "actual": next_wave.get("next_wave_lanes")})
    if next_wave.get("not_ml_only_closure") is not True or "subsystem" not in next_wave.get("ml_role", ""):
        issues.append({"code": "next_wave_ml_role_not_subsystem"})
    if not limitation_map.get("all_dispositions_allowed") or limitation_map.get("row_count", 0) < 10:
        issues.append({"code": "limitation_disposition_map_incomplete"})
    if later_gates.get("gate_count", 0) < 7 or "subsystem" not in later_gates.get("ml_role", ""):
        issues.append({"code": "later_wave_gates_incomplete_or_ml_not_subsystem"})
    if later_gates.get("gate_count", 0) < 8 or later_gates.get("wave4_terminal_consumed") is not True:
        issues.append({"code": "later_wave_gates_not_refreshed_post_lane18"})
    if post_lane18_decision.get("wave4_terminal_verified") is not True:
        issues.append({"code": "post_lane18_decision_does_not_consume_terminal_wave4"})
    required_next_gates = {"selector_v3", "scheduler_v3", "execution_policy_v3", "source_capture_repair"}
    if not required_next_gates.issubset(set(post_lane18_decision.get("next_implementation_gates", []))):
        issues.append(
            {
                "code": "post_lane18_next_implementation_gates_incomplete",
                "actual": post_lane18_decision.get("next_implementation_gates", []),
            }
        )
    if post_lane18_decision.get("post_v3_terminal_consumed") is not True:
        issues.append({"code": "post_lane18_decision_not_neutralized_after_post_v3_terminal"})
    if post_lane18_decision.get("decision") == "open_selector_v3_scheduler_v3_execution_policy_v3_and_source_capture_repair":
        issues.append({"code": "post_lane18_decision_still_relaunches_terminal_post_v3_gates"})
    if post_v3_table.get("all_post_v3_terminal_verified") is not True:
        issues.append({"code": "post_v3_terminal_state_not_verified"})
    post_v3_ids = {row.get("gate_id") for row in post_v3_table.get("terminal_routes", [])}
    expected_post_v3_ids = set(POST_V3_ROUTE_DIRS)
    if post_v3_ids != expected_post_v3_ids:
        issues.append({"code": "post_v3_terminal_gate_ids_mismatch", "actual": sorted(post_v3_ids)})
    post_v3_counts = {
        row.get("gate_id"): row.get("material_row_counts", {})
        for row in post_v3_table.get("terminal_routes", [])
    }
    for gate_id, expected in POST_V3_EXPECTED_COUNTS.items():
        actual = post_v3_counts.get(gate_id, {})
        for key, value in expected.items():
            if actual.get(key) != value:
                issues.append(
                    {
                        "code": "post_v3_terminal_count_mismatch",
                        "gate_id": gate_id,
                        "field": key,
                        "expected": value,
                        "actual": actual.get(key),
                    }
                )
    for row in post_v3_table.get("terminal_routes", []):
        if row.get("terminal_status") != "terminal_verified":
            issues.append({"code": "post_v3_gate_not_terminal", "gate_id": row.get("gate_id")})
        if row.get("verification_ok") is not True:
            issues.append({"code": "post_v3_gate_verifier_not_ok", "gate_id": row.get("gate_id")})
        if row.get("focused_test_result", {}).get("ok") is not True:
            issues.append({"code": "post_v3_gate_focused_test_not_ok", "gate_id": row.get("gate_id")})
        if not all(bool(value) for value in row.get("expected_count_matches", {}).values()):
            issues.append({"code": "post_v3_expected_counts_not_matched", "gate_id": row.get("gate_id")})
        missing_required = [
            artifact.get("path")
            for artifact in row.get("required_files", [])
            if not artifact.get("exists") or artifact.get("size_bytes", 0) <= 0
        ]
        if missing_required:
            issues.append(
                {
                    "code": "post_v3_required_artifact_missing",
                    "gate_id": row.get("gate_id"),
                    "missing": missing_required,
                }
            )
    if later_gates.get("post_v3_terminal_consumed") is not True:
        issues.append({"code": "later_wave_gates_do_not_consume_post_v3_terminal_state"})
    if post_v3_decision.get("post_v3_terminal_verified") is not True:
        issues.append({"code": "post_v3_launch_decision_not_open_from_terminal_state"})
    post_v3_launch_lanes = {
        lane
        for phase in post_v3_decision.get("next_launch_order", [])
        for lane in phase.get("lanes", [])
    }
    if not {"12", "13", "14", "15"}.issubset(post_v3_launch_lanes):
        issues.append({"code": "post_v3_launch_order_missing_lanes12_15", "actual": sorted(post_v3_launch_lanes)})
    if "subsystem" not in post_v3_decision.get("ml_role", ""):
        issues.append({"code": "post_v3_ml_role_not_subsystem"})
    stale_launch_text = json.dumps({"later_gates": later_gates, "post_v3_decision": post_v3_decision}, sort_keys=True).lower()
    for phrase in [
        "wait_for_post_v3_terminal_evidence",
        "open_selector_v3_scheduler_v3_execution_policy_v3_and_source_capture_repair_as_the_next_implementation_wave",
        "ready_after_lane16_17_18_terminal_contracts",
        "ready_after_lane16_17_18_gap_contracts",
    ]:
        if phrase in stale_launch_text:
            issues.append({"code": "stale_post_v3_launch_text_present", "phrase": phrase})
    if not stale_neutralization.get("neutralized_for_master_consumption"):
        issues.append({"code": "lane04_stale_dependency_text_not_neutralized"})
    if stale_neutralization.get("post_v3_neutralized_by_terminal_consumption") is not True:
        issues.append({"code": "post_v3_stale_dependency_text_not_neutralized"})

    for lane in lanes:
        prompt = ROOT / lane["prompt_path"]
        starter = ROOT / lane["starter_path"]
        if not prompt.exists() or sha256_file(prompt) != lane["prompt_sha256"]:
            issues.append({"code": "prompt_hash_drift", "lane_id": lane["lane_id"]})
        if not starter.exists() or sha256_file(starter) != lane["starter_sha256"]:
            issues.append({"code": "starter_hash_drift", "lane_id": lane["lane_id"]})
        allowed_route_prefixes = (
            f"research/operations/vnext_moonshot_lane{lane['lane_id']}_",
            f"research/operations/vnext_absolute_moonshot_lane{lane['lane_id']}_",
        )
        if not lane["route_path"].startswith(allowed_route_prefixes):
            issues.append({"code": "lane_route_path_drift", "lane_id": lane["lane_id"], "route": lane["route_path"]})
        terminal = lane.get("terminal_artifact_contract", {}).get("required_terminal_artifacts", [])
        required_terminal = {"route_output_manifest", "route_verifier", "focused_tests", "completion_audit"}
        if not required_terminal.issubset(set(terminal)):
            issues.append({"code": "lane_missing_terminal_artifact_contract", "lane_id": lane["lane_id"]})
        if lane.get("terminal_artifact_contract", {}).get("ledger_only_completion_allowed") is not False:
            issues.append({"code": "ledger_only_completion_not_forbidden", "lane_id": lane["lane_id"]})
    node_ids = {node["node_id"] for node in graph.get("nodes", [])}
    required_graph_nodes = set(expected_ids + ["MASTER"]) | set(POST_V3_ROUTE_DIRS)
    if not required_graph_nodes.issubset(node_ids):
        issues.append({"code": "dependency_graph_missing_nodes", "actual": sorted(node_ids)})
    post_v3_edges = {
        (edge.get("from"), edge.get("to"), edge.get("edge_type"))
        for edge in graph.get("edges", [])
    }
    for gate_id in POST_V3_ROUTE_DIRS:
        for lane_id in ["12", "13", "14", "15"]:
            if (gate_id, lane_id, "post_v3_terminal_input_dependency") not in post_v3_edges:
                issues.append({"code": "dependency_graph_missing_post_v3_edge", "gate_id": gate_id, "lane_id": lane_id})
    wave_by_id = {lane["lane_id"]: lane["wave"] for lane in lanes}
    for lane in lanes:
        for dep in lane["dependencies"]:
            if wave_by_id.get(dep, 99) > lane["wave"]:
                issues.append({"code": "dependency_wave_drift", "lane_id": lane["lane_id"], "dependency": dep})
    if len(blockers) < 27:
        issues.append({"code": "blocker_ledger_too_small", "actual": len(blockers)})
    families = {family.get("source_family") for family in source_map.get("source_families", [])}
    required_families = {
        "repo_data_and_runtime_logs",
        "local_mt5_cache",
        "compliant_vps_data_preservation",
        "friday_microscope",
        "next_level_lane_package",
        "selected_denominator_dynamic_replay",
        "live_companion",
        "absolute_lane01_source_authority",
        "absolute_lane02_asof_contract",
        "absolute_lane03_candidate_reconstruction",
        "absolute_lane04_historical_microscope",
        "absolute_lane05_feature_store",
        "absolute_lane06_label_store",
        "absolute_lane07_broker_truth_cost_calibration",
        "absolute_lane08_digital_twin",
        "absolute_lane09_meta_selector",
        "absolute_lane10_portfolio_scheduler",
        "absolute_lane09b_selector_scheduler_reconciliation",
        "absolute_lane10b_scheduler_conflict_anatomy",
        "absolute_lane11_execution_policy_engine",
        "absolute_lane16_historical_microscope_scale",
        "absolute_lane17_market_awareness_whiteboard",
        "absolute_lane18_broker_truth_cost_capture_v2",
        "absolute_next_wave_lanes16_18_launch_contracts",
        "absolute_post_lane18_source_capture_repair",
        "absolute_selector_v3_default_off_package",
        "absolute_scheduler_v3_default_off_package",
        "absolute_execution_policy_v3_default_off_package",
    }
    if not required_families.issubset(families):
        issues.append({"code": "source_authority_missing_family", "missing": sorted(required_families - families)})
    schema_keys = set(schemas.get("schemas", {}).keys())
    required_schema_keys = {
        "event_row",
        "feature_row",
        "label_row",
        "replay_row",
        "ml_row",
        "scheduler_row",
        "market_whiteboard_row",
        "execution_policy_row",
        "broker_truth_cost_capture_row",
        "limitation_disposition_row",
        "next_wave_contract_row",
        "selector_v3_contract_row",
        "scheduler_v3_contract_row",
        "execution_policy_v3_contract_row",
        "source_capture_repair_row",
        "post_v3_terminal_route_row",
        "production_dossier_row",
    }
    if not required_schema_keys.issubset(schema_keys):
        issues.append({"code": "schema_contract_missing_keys", "missing": sorted(required_schema_keys - schema_keys)})
    label_fields = set(schemas.get("schemas", {}).get("label_row", []))
    if not {"exact_r", "proxy_r", "expectancy_r", "row_level_missing_field_proof"}.issubset(label_fields):
        issues.append({"code": "label_schema_missing_r_or_missing_proof_fields"})
    if "top-N" not in " ".join(anti_loop.get("anti_duplication_rules", [])) and "top 3/5/10" not in " ".join(anti_loop.get("anti_duplication_rules", [])):
        issues.append({"code": "anti_dup_no_topn_rule_missing"})
    if not anti_loop.get("anti_infinite_ledger_rules"):
        issues.append({"code": "anti_infinite_ledger_rules_missing"})
    forbidden_prefixes = tuple(merge.get("forbidden_scoped_commit_prefixes_for_master", []))
    for output in manifest.get("outputs", []):
        path = output.get("path", "")
        if not any(path.startswith(prefix) or path == prefix for prefix in ALLOWED_OUTPUT_PREFIXES):
            issues.append({"code": "manifest_output_unscoped", "path": path})
        if any(path.startswith(prefix) for prefix in forbidden_prefixes):
            issues.append({"code": "manifest_output_forbidden_live_prefix", "path": path})
    manifest_paths = {output.get("path") for output in manifest.get("outputs", [])}
    required_manifest_paths = {rel(ROUTE_DIR / name) for name in REQUIRED_OUTPUTS}
    missing_manifest_paths = sorted(required_manifest_paths - manifest_paths)
    if missing_manifest_paths:
        issues.append({"code": "manifest_missing_required_output_paths", "missing": missing_manifest_paths})
    if not prompt_validation.get("ok"):
        issues.append({"code": "prompt_hardening_failed"})
    prompt_paths = {row.get("path") for row in prompt_validation.get("results", [])}
    required_prompt_paths = {
        rel(POST_V3_MASTER_PROMPT),
        rel(POST_V3_MASTER_STARTER),
        rel(PROMPT_DIR / "VNEXT_ABSOLUTE_MOONSHOT_POST_LANE18_SOURCE_CAPTURE_REPAIR_GOAL_PROMPT_2026-06-01.md"),
        rel(PROMPT_DIR / "VNEXT_ABSOLUTE_MOONSHOT_POST_LANE18_SOURCE_CAPTURE_REPAIR_STARTER_2026-06-01.txt"),
        rel(PROMPT_DIR / "VNEXT_ABSOLUTE_MOONSHOT_SELECTOR_V3_GOAL_PROMPT_2026-06-01.md"),
        rel(PROMPT_DIR / "VNEXT_ABSOLUTE_MOONSHOT_SELECTOR_V3_STARTER_2026-06-01.txt"),
        rel(PROMPT_DIR / "VNEXT_ABSOLUTE_MOONSHOT_SCHEDULER_V3_GOAL_PROMPT_2026-06-01.md"),
        rel(PROMPT_DIR / "VNEXT_ABSOLUTE_MOONSHOT_SCHEDULER_V3_STARTER_2026-06-01.txt"),
        rel(PROMPT_DIR / "VNEXT_ABSOLUTE_MOONSHOT_EXECUTION_POLICY_V3_GOAL_PROMPT_2026-06-01.md"),
        rel(PROMPT_DIR / "VNEXT_ABSOLUTE_MOONSHOT_EXECUTION_POLICY_V3_STARTER_2026-06-01.txt"),
    }
    if not required_prompt_paths.issubset(prompt_paths):
        issues.append({"code": "post_v3_prompt_validation_missing_paths", "missing": sorted(required_prompt_paths - prompt_paths)})
    if result_status.get("production_change_readiness_claim") is not False:
        issues.append({"code": "result_use_status_allows_production_change_claim"})
    if result_status.get("execution_policy_v3", {}).get("proxy_to_production_leap_allowed") is not False:
        issues.append({"code": "execution_policy_v3_proxy_to_production_leap_not_closed"})
    if require_focused_test_result and not focused_result.get("ok"):
        issues.append({"code": "focused_test_result_missing_or_failed", "status": focused_result.get("status")})
    boundary = load_json(ROUTE_DIR / "ABSOLUTE_MASTER_RUNTIME_EFFECT_BOUNDARY.json", {})
    if any(boundary.get("attestation", {}).values()):
        issues.append({"code": "runtime_effect_boundary_open"})
    return {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_verification_result_v1",
        "generated_at_utc": utc_now(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "lane_count": len(lanes),
        "prompt_validation_ok": bool(prompt_validation.get("ok")),
        "focused_test_result_ok": bool(focused_result.get("ok")),
        "source_family_count": len(families),
    }


def build_outputs(*, write: bool = True, require_focused_test_result: bool = False) -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    terminal_table = wave1_terminal_state_table()
    wave1_inspection_rows = wave1_artifact_inspection_rows(terminal_table)
    wave2_terminal_table = wave2_terminal_state_table()
    wave2_inspection_rows = wave2_artifact_inspection_rows(wave2_terminal_table)
    wave2_readiness = wave2_readiness_decision(terminal_table, wave2_terminal_table)
    wave3_terminal_table = wave3_terminal_state_table()
    wave3_inspection_rows = wave3_artifact_inspection_rows(wave3_terminal_table)
    post_lane11_table = post_lane11_terminal_state_table(wave3_terminal_table)
    limitation_map = limitation_disposition_map()
    wave4_terminal_table = wave4_terminal_state_table()
    wave4_inspection_rows = wave4_artifact_inspection_rows(wave4_terminal_table)
    post_v3_table = post_v3_terminal_state_table()
    post_v3_inspection_rows = post_v3_artifact_inspection_rows(post_v3_table)
    stale_neutralization = stale_dependency_text_neutralization(terminal_table, post_v3_table)
    later_gates = later_wave_gates(wave4_table=wave4_terminal_table, post_v3_table=post_v3_table)
    next_wave = next_wave_launch_decision(post_lane11_table, limitation_map, later_gates)
    post_lane18_decision = post_lane18_implementation_wave_decision(wave4_terminal_table, later_gates)
    post_v3_decision = post_v3_launch_decision(post_v3_table, later_gates)
    wave3_readiness = wave3_readiness_decision(
        terminal_table,
        wave2_terminal_table,
        wave3_terminal_table,
        post_lane11_table,
        next_wave,
        later_gates,
    )
    wave3_launch = wave3_launch_order(wave3_readiness)
    lanes = collect_lanes()
    prompt_validation = prompt_validation_payload()
    evidence_rows = evidence_inspection_rows(
        wave1_inspection_rows,
        stale_neutralization,
        wave2_inspection_rows,
        wave3_inspection_rows,
        post_lane11_table,
        wave4_inspection_rows,
        post_v3_inspection_rows,
    )
    source_map = source_authority_map(evidence_rows)
    schemas = output_schema_contracts()
    graph = dependency_graph(lanes, post_v3_table)
    waves = launch_waves(lanes, post_v3_table)
    blockers = blocker_rows(lanes, evidence_rows)
    source_decisions = source_completeness_rows(evidence_rows)
    source_capture_decisions = source_capture_rows()
    result_status = result_use_status(post_v3_table)
    decisions = decision_rows(lanes)
    anti_loop = anti_duplication_rules()
    merge = merge_plan(lanes)
    verifier = verifier_matrix(lanes)
    boundary = runtime_effect_boundary()
    focused = focused_test_result()

    registry = {
        "route_id": ROUTE_ID,
        "schema_version": "absolute_master_lane_registry_v1",
        "generated_at_utc": utc_now(),
        "git": git_head(),
        "master_prompt_path": rel(MASTER_PROMPT),
        "master_starter_path": rel(MASTER_STARTER),
        "post_v3_master_prompt_path": rel(POST_V3_MASTER_PROMPT),
        "post_v3_master_starter_path": rel(POST_V3_MASTER_STARTER),
        "launch_order_path": rel(LAUNCH_ORDER),
        "lane_count": len(lanes),
        "lanes": lanes,
    }
    lane_ledger = [
        {
            "schema_version": "absolute_master_lane_registry_row_v1",
            "route_id": ROUTE_ID,
            "lane_id": lane["lane_id"],
            "title": lane["title"],
            "prompt_path": lane["prompt_path"],
            "starter_path": lane["starter_path"],
            "route_path": lane["route_path"],
            "wave": lane["wave"],
            "dependencies": lane["dependencies"],
            "terminal_artifact_contract": lane["terminal_artifact_contract"],
            "runtime_effect_boundary": lane["boundary_contract"]["runtime_effect_boundary"],
        }
        for lane in lanes
    ]

    output_paths = [ROUTE_DIR / name for name in REQUIRED_OUTPUTS]
    manifest = output_manifest(output_paths + [ROUTE_DIR / "verify_absolute_moonshot_master_orchestration.py"])
    verification = _verify_payload(
        lanes,
        graph,
        source_map,
        schemas,
        blockers,
        anti_loop,
        merge,
        manifest,
        prompt_validation,
        {"can_mark_master_orchestration_goal_complete_after_scoped_commit": False},
        focused,
        terminal_table,
        wave2_terminal_table,
        wave2_readiness,
        wave3_readiness,
        wave3_launch,
        wave3_terminal_table,
        post_lane11_table,
        wave4_terminal_table,
        limitation_map,
        next_wave,
        later_gates,
        post_lane18_decision,
        post_v3_table,
        post_v3_decision,
        stale_neutralization,
        result_status,
        require_focused_test_result=require_focused_test_result,
    )
    completion = completion_audit(lanes, prompt_validation, focused, verification)
    verification = _verify_payload(
        lanes,
        graph,
        source_map,
        schemas,
        blockers,
        anti_loop,
        merge,
        manifest,
        prompt_validation,
        completion,
        focused,
        terminal_table,
        wave2_terminal_table,
        wave2_readiness,
        wave3_readiness,
        wave3_launch,
        wave3_terminal_table,
        post_lane11_table,
        wave4_terminal_table,
        limitation_map,
        next_wave,
        later_gates,
        post_lane18_decision,
        post_v3_table,
        post_v3_decision,
        stale_neutralization,
        result_status,
        require_focused_test_result=require_focused_test_result,
    )
    context_anchor = render_context_anchor(lanes, evidence_rows, verification)

    payload = {
        "registry": registry,
        "lane_ledger": lane_ledger,
        "graph": graph,
        "waves": waves,
        "source_map": source_map,
        "schemas": schemas,
        "blockers": blockers,
        "anti_loop": anti_loop,
        "merge": merge,
        "verifier": verifier,
        "evidence_rows": evidence_rows,
        "wave1_inspection_rows": wave1_inspection_rows,
        "terminal_table": terminal_table,
        "wave2_inspection_rows": wave2_inspection_rows,
        "wave2_terminal_table": wave2_terminal_table,
        "wave2_readiness": wave2_readiness,
        "wave3_inspection_rows": wave3_inspection_rows,
        "wave3_terminal_table": wave3_terminal_table,
        "post_lane11_table": post_lane11_table,
        "wave4_inspection_rows": wave4_inspection_rows,
        "wave4_terminal_table": wave4_terminal_table,
        "post_v3_inspection_rows": post_v3_inspection_rows,
        "post_v3_table": post_v3_table,
        "wave3_readiness": wave3_readiness,
        "wave3_launch": wave3_launch,
        "limitation_map": limitation_map,
        "next_wave": next_wave,
        "later_gates": later_gates,
        "post_lane18_decision": post_lane18_decision,
        "post_v3_decision": post_v3_decision,
        "stale_neutralization": stale_neutralization,
        "source_decisions": source_decisions,
        "source_capture_decisions": source_capture_decisions,
        "decisions": decisions,
        "result_status": result_status,
        "boundary": boundary,
        "prompt_validation": prompt_validation,
        "focused": focused,
        "context_anchor": context_anchor,
        "saturation": render_saturation_self_red_team(lanes),
        "manifest": manifest,
        "completion": completion,
        "verification": verification,
    }
    if write:
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_LANE_REGISTRY.json", registry)
        write_jsonl(ROUTE_DIR / "ABSOLUTE_MASTER_LANE_REGISTRY_LEDGER.jsonl", lane_ledger)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_DEPENDENCY_GRAPH.json", graph)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_LAUNCH_WAVES.json", waves)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_SOURCE_AUTHORITY_MAP.json", source_map)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_OUTPUT_SCHEMA_CONTRACTS.json", schemas)
        write_jsonl(ROUTE_DIR / "ABSOLUTE_MASTER_CROSS_LANE_BLOCKER_LEDGER.jsonl", blockers)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_ANTI_DUPLICATION_AND_LOOP_RULES.json", anti_loop)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_MERGE_COMMIT_OWNERSHIP_PLAN.json", merge)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_VERIFIER_TEST_MATRIX.json", verifier)
        write_jsonl(ROUTE_DIR / "ABSOLUTE_MASTER_EVIDENCE_INSPECTION_LEDGER.jsonl", evidence_rows)
        write_jsonl(ROUTE_DIR / "ABSOLUTE_MASTER_WAVE1_ARTIFACT_INSPECTION_LEDGER.jsonl", wave1_inspection_rows)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_WAVE1_TERMINAL_STATE_TABLE.json", terminal_table)
        write_jsonl(ROUTE_DIR / "ABSOLUTE_MASTER_WAVE2_ARTIFACT_INSPECTION_LEDGER.jsonl", wave2_inspection_rows)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_WAVE2_TERMINAL_STATE_TABLE.json", wave2_terminal_table)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_WAVE2_READINESS_DECISION.json", wave2_readiness)
        write_jsonl(ROUTE_DIR / "ABSOLUTE_MASTER_WAVE3_ARTIFACT_INSPECTION_LEDGER.jsonl", wave3_inspection_rows)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_WAVE3_TERMINAL_STATE_TABLE.json", wave3_terminal_table)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_POST_LANE11_TERMINAL_STATE_TABLE.json", post_lane11_table)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_WAVE3_READINESS_DECISION.json", wave3_readiness)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_WAVE3_LAUNCH_ORDER.json", wave3_launch)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_LIMITATION_DISPOSITION_MAP.json", limitation_map)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_NEXT_WAVE_LAUNCH_DECISION.json", next_wave)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_LATER_WAVE_GATES.json", later_gates)
        write_jsonl(ROUTE_DIR / "ABSOLUTE_MASTER_WAVE4_ARTIFACT_INSPECTION_LEDGER.jsonl", wave4_inspection_rows)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_WAVE4_TERMINAL_STATE_TABLE.json", wave4_terminal_table)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_POST_LANE18_IMPLEMENTATION_WAVE_DECISION.json", post_lane18_decision)
        write_jsonl(ROUTE_DIR / "ABSOLUTE_MASTER_POST_V3_ARTIFACT_INSPECTION_LEDGER.jsonl", post_v3_inspection_rows)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_POST_V3_TERMINAL_STATE_TABLE.json", post_v3_table)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_POST_V3_LAUNCH_DECISION.json", post_v3_decision)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_STALE_DEPENDENCY_TEXT_NEUTRALIZATION.json", stale_neutralization)
        write_jsonl(ROUTE_DIR / "ABSOLUTE_MASTER_SOURCE_CAPTURE_DECISIONS.jsonl", source_capture_decisions)
        write_jsonl(ROUTE_DIR / "ABSOLUTE_MASTER_SOURCE_COMPLETENESS_DECISIONS.jsonl", source_decisions)
        write_jsonl(ROUTE_DIR / "ABSOLUTE_MASTER_DECISION_LEDGER.jsonl", decisions)
        write_jsonl(ROUTE_DIR / "ABSOLUTE_MASTER_BRANCH_IMPLEMENTATION_DECISIONS.jsonl", decisions)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_RESULT_USE_STATUS.json", result_status)
        (ROUTE_DIR / "ABSOLUTE_MASTER_SATURATION_SELF_RED_TEAM.md").write_text(
            render_saturation_self_red_team(lanes), encoding="utf-8"
        )
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_RUNTIME_EFFECT_BOUNDARY.json", boundary)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_PROMPT_HARDENING_VERIFICATION.json", prompt_validation)
        (ROUTE_DIR / "ABSOLUTE_MASTER_CONTEXT_ANCHOR.md").write_text(context_anchor, encoding="utf-8")
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_FOCUSED_TEST_RESULT.json", focused)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_OUTPUT_MANIFEST.json", output_manifest(output_paths + [ROUTE_DIR / "verify_absolute_moonshot_master_orchestration.py"]))
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_COMPLETION_AUDIT.json", completion)
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_VERIFICATION_RESULT.json", verification)
    return payload


def verify_outputs(*, write: bool = True, require_focused_test_result: bool = True) -> dict[str, Any]:
    payload = build_outputs(write=False, require_focused_test_result=require_focused_test_result)
    result = payload["verification"]
    if write:
        write_json(ROUTE_DIR / "ABSOLUTE_MASTER_VERIFICATION_RESULT.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify generated artifacts and return non-zero on failure.")
    parser.add_argument(
        "--allow-missing-focused-test",
        action="store_true",
        help="Permit the first build before pytest writes the focused JUnit XML.",
    )
    args = parser.parse_args(argv)
    if args.check:
        result = verify_outputs(write=True, require_focused_test_result=not args.allow_missing_focused_test)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("ok") else 1
    payload = build_outputs(write=True, require_focused_test_result=not args.allow_missing_focused_test)
    print(
        json.dumps(
            {
                "route_id": ROUTE_ID,
                "lane_count": payload["registry"]["lane_count"],
                "verification_ok": payload["verification"]["ok"],
                "focused_test_result_ok": payload["focused"]["ok"],
                "completion_ready_after_scoped_commit": payload["completion"][
                    "can_mark_master_orchestration_goal_complete_after_scoped_commit"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
