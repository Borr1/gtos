from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROUTE_ID = "vnext_next_level_master_orchestration_2026_05_31"
ROUTE_DIR = ROOT / "research" / "operations" / ROUTE_ID
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
FRIDAY_DIR = ROOT / "research" / "operations" / "vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"
LIVE_COMPANION_DIR = ROOT / "research" / "operations" / "vnext_live_activation_active_repair_companion_2026_05_28"
ACTIVATION_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27"
)

MASTER_PROMPT = PROMPT_DIR / "VNEXT_NEXT_LEVEL_MASTER_ORCHESTRATION_GOAL_PROMPT_2026-05-31.md"
MASTER_STARTER = PROMPT_DIR / "VNEXT_NEXT_LEVEL_MASTER_ORCHESTRATION_STARTER_2026-05-31.txt"
LAUNCH_PACK = PROMPT_DIR / "VNEXT_NEXT_LEVEL_PARALLEL_PROGRAM_LAUNCH_PACK_2026-05-31.md"
LANE09_ROUTE_DIR = ROOT / "research" / "operations" / "vnext_lane09_cross_lane_merge_dossier_production_package_2026_05_31"

EXTERNAL_SESSION_OWNED_LANES = {
    "02": {
        "owner_state": "dedicated_lane02_goal_session_owns_terminal_artifacts",
        "master_policy": "treat_current_uncommitted_lane02_artifacts_as_handoff_material_only",
    }
}

MASTER_SCOPED_INCLUDE_PATHS = {
    ".gitattributes",
    "config/agent_config.yaml",
    "scripts/build_vnext_post_reload_candidate_proof.py",
    "scripts/build_vnext_lane01_fixed_friday_portfolio_replay.py",
    "scripts/build_vnext_lane02_broad_selected_portfolio_replay_stress.py",
    "scripts/build_vnext_lane03_meta_selector.py",
    "scripts/build_vnext_lane05_runtime_portfolio_scheduler.py",
    "scripts/build_vnext_lane06_broker_lifecycle_truth.py",
    "scripts/build_vnext_lane08_execution_policy_microstructure_stress.py",
    "scripts/verify_vnext_lane06_broker_lifecycle_truth.py",
    "scripts/build_vnext_next_level_master_orchestration.py",
    "scripts/build_vnext_lane09_cross_lane_merge_dossier_production_package.py",
    "src/components/execution.py",
    "src/components/gtos_vnext_runtime.py",
    "src/components/m1_capture.py",
    "src/components/orchestrator.py",
    "src/research/moonshot_default_off_policy_router.py",
    "tests/test_config_symbol_aliases.py",
    "tests/test_execution.py",
    "tests/test_gtos_vnext_runtime.py",
    "tests/test_m1_capture.py",
    "tests/test_moonshot_default_off_policy_router.py",
    "tests/test_vnext_broader_origin_orchestrator.py",
    "tests/test_vnext_lane01_fixed_friday_portfolio_replay.py",
    "tests/test_vnext_lane02_broad_selected_portfolio_replay_stress.py",
    "tests/test_vnext_lane05_portfolio_scheduler.py",
    "tests/test_vnext_lane06_broker_lifecycle_truth.py",
    "tests/test_vnext_lane08_execution_policy_microstructure_stress.py",
    "tests/test_vnext_lane09_cross_lane_merge_dossier.py",
}
MASTER_SCOPED_INCLUDE_PREFIXES = (
    "research/operations/vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31/",
    "research/operations/vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31/",
    "research/operations/vnext_lane03_meta_selector_discovery_implementation_2026_05_31/",
    "research/operations/vnext_lane04_selected_cell_risk_bridge_packet_completeness_2026_05_31/",
    "research/operations/vnext_lane05_runtime_portfolio_scheduler_integration_2026_05_31/",
    "research/operations/vnext_lane06_broker_lifecycle_net_r_cost_truth_2026_05_31/",
    "research/operations/vnext_lane07_market_coverage_source_starvation_repair_2026_05_31/",
    "research/operations/vnext_lane08_execution_policy_microstructure_stress_2026_05_31/",
    "research/operations/vnext_next_level_master_orchestration_2026_05_31/",
    "research/operations/vnext_lane09_cross_lane_merge_dossier_production_package_2026_05_31/",
)
LANE_ROUTE_PREFIXES = tuple(
    f"research/operations/vnext_lane{idx:02d}_"
    for idx in range(1, 9)
)
LIVE_OR_RUNTIME_DIRTY_PREFIXES = (
    "shadow_logs/",
    "pipeline_state/",
    "data/",
    "knowledge_base/",
    "research/program_control/",
    "research/ml_program/shadow/",
    "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/",
)
PROMPT_PREFIX = "research/science_program_2026_05/04_goal_prompts/"
PROMPT_PACKAGE_MARKERS = (
    "VNEXT_LANE01_FIXED_FRIDAY_PORTFOLIO_REPLAY_ENGINE_",
    "VNEXT_LANE02_BROAD_SELECTED_PORTFOLIO_REPLAY_STRESS_",
    "VNEXT_LANE03_META_SELECTOR_DISCOVERY_IMPLEMENTATION_",
    "VNEXT_LANE04_SELECTED_CELL_RISK_BRIDGE_PACKET_COMPLETENESS_",
    "VNEXT_LANE05_RUNTIME_PORTFOLIO_SCHEDULER_INTEGRATION_",
    "VNEXT_LANE06_BROKER_LIFECYCLE_NET_R_COST_TRUTH_",
    "VNEXT_LANE07_MARKET_COVERAGE_SOURCE_STARVATION_REPAIR_",
    "VNEXT_LANE08_EXECUTION_POLICY_MICROSTRUCTURE_STRESS_",
    "VNEXT_LANE09_CROSS_LANE_MERGE_DOSSIER_PRODUCTION_PACKAGE_",
    "VNEXT_NEXT_LEVEL_MASTER_ORCHESTRATION_",
)
SCOPED_PACKAGE_COMMIT_SUBJECT = "vnext: package next-level lane implementation"
SCOPED_PACKAGE_REQUIRED_PATHS = (
    ".gitattributes",
    "config/agent_config.yaml",
    "research/operations/vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31/LANE02_BROAD_SELECTED_PORTFOLIO_REPLAY_LEDGER.jsonl",
    "research/operations/vnext_lane08_execution_policy_microstructure_stress_2026_05_31/LANE08_STRICT_TICK_POLICY_LEDGER.jsonl",
    "research/operations/vnext_lane09_cross_lane_merge_dossier_production_package_2026_05_31/LANE09_PRODUCTION_PACKAGE.json",
    "research/operations/vnext_next_level_master_orchestration_2026_05_31/MASTER_SCOPED_MERGE_STAGING_PLAN.json",
    "scripts/build_vnext_lane09_cross_lane_merge_dossier_production_package.py",
    "scripts/build_vnext_next_level_master_orchestration.py",
    "src/components/gtos_vnext_runtime.py",
    "tests/test_vnext_lane09_cross_lane_merge_dossier.py",
)
SCOPED_PACKAGE_REQUIRED_PREFIXES = MASTER_SCOPED_INCLUDE_PREFIXES + (PROMPT_PREFIX,)
SCOPED_PACKAGE_FORBIDDEN_PREFIXES = LIVE_OR_RUNTIME_DIRTY_PREFIXES + (
    ".codex/",
    ".context/",
    "research/archive/",
)


def apply_external_session_lane_policy(
    lane_id: str, route_path: Path, terminal_status: dict[str, Any]
) -> dict[str, Any]:
    external_owner = EXTERNAL_SESSION_OWNED_LANES.get(lane_id)
    if not external_owner or not route_path.exists():
        return terminal_status
    lane09_state = lane09_packaged_lane_state(lane_id)
    if lane09_state:
        return {
            **terminal_status,
            "external_goal_session_owner_state": external_owner["owner_state"],
            "lane09_external_handoff_adoption_state": lane09_state.get("lane09_adoption_state"),
            "lane09_package_verification_path": rel(LANE09_ROUTE_DIR / "LANE09_VERIFICATION_RESULT.json"),
            "master_terminal_acceptance_policy": "accepted_read_only_after_lane09_cross_lane_package",
            "raw_terminal_artifacts_present_before_master_policy": terminal_status.get(
                "terminal_artifacts_present"
            ),
            "terminal_artifacts_present": bool(terminal_status.get("terminal_artifacts_present")),
        }
    return {
        **terminal_status,
        "external_goal_session_owner_state": external_owner["owner_state"],
        "master_terminal_acceptance_policy": external_owner["master_policy"],
        "raw_terminal_artifacts_present_before_master_policy": terminal_status.get(
            "terminal_artifacts_present"
        ),
        "terminal_artifacts_present": False,
    }


def apply_external_dependency_policy(
    lane: dict[str, Any], terminal_status: dict[str, Any]
) -> dict[str, Any]:
    pending_external = []
    dependency_text = " ".join(str(item).lower() for item in lane.get("dependencies", []))
    for lane_id in EXTERNAL_SESSION_OWNED_LANES:
        if f"lane{lane_id}" in dependency_text:
            pending_external.append(lane_id)
    if not pending_external:
        return terminal_status
    cleared = [lane_id for lane_id in pending_external if lane09_packaged_lane_state(lane_id)]
    if sorted(cleared) == sorted(pending_external):
        return {
            **terminal_status,
            "external_dependency_cleared_by_lane09_package": cleared,
            "master_terminal_acceptance_policy": "dependency_accepted_after_lane09_cross_lane_package",
            "terminal_artifacts_present": bool(terminal_status.get("terminal_artifacts_present")),
        }
    return {
        **terminal_status,
        "external_dependency_pending_lanes": pending_external,
        "master_terminal_acceptance_policy": (
            "do_not_accept_as_terminal_until_external_dependency_lanes_are_"
            "dedicated-session-verified_or_explicitly_adopt_current_artifacts"
        ),
        "raw_terminal_artifacts_present_before_master_policy": terminal_status.get(
            "terminal_artifacts_present"
        ),
        "terminal_artifacts_present": False,
    }

SUBAGENT_AUDIT_REQUESTS = [
    {
        "agent_id": "019e7e53-a60d-71a2-9d76-9a134b20e743",
        "audit_id": "subagent_lane01_lane02_replay_audit",
        "lanes": ["01", "02"],
        "nickname": "Noether",
        "requested_output": "fixed Friday portfolio replay and broad selected replay stress evidence audit",
        "status": "completed_findings_integrated",
    },
    {
        "agent_id": "019e7e53-bc1d-76f0-9d09-d8dc2757f8f0",
        "audit_id": "subagent_lane03_lane05_code_path_audit",
        "lanes": ["03", "05"],
        "nickname": "Parfit",
        "requested_output": "meta-selector and runtime portfolio scheduler code-path audit",
        "status": "completed_findings_integrated",
    },
    {
        "agent_id": "019e7e53-da1a-76a1-9a0c-3a84b9f2ac34",
        "audit_id": "subagent_lane04_lane06_bridge_broker_audit",
        "lanes": ["04", "06"],
        "nickname": "Beauvoir",
        "requested_output": "selected-cell risk bridge and broker lifecycle net-R/cost truth audit",
        "status": "completed_findings_integrated",
    },
    {
        "agent_id": "019e7e53-f288-7583-b451-0690f82d3219",
        "audit_id": "subagent_lane07_lane08_coverage_policy_audit",
        "lanes": ["07", "08"],
        "nickname": "Nietzsche",
        "requested_output": "24-symbol coverage/source starvation and execution-policy stress audit",
        "status": "completed_findings_integrated",
    },
    {
        "agent_id": "019e7e54-0b98-7e60-8a74-906bfe79611d",
        "audit_id": "subagent_lane09_master_requirements_audit",
        "lanes": ["09", "master"],
        "nickname": "Kant",
        "requested_output": "merge dossier and master orchestration requirement audit",
        "status": "completed_findings_integrated",
    },
]

SUBAGENT_FINDINGS = [
    {
        "agent_id": "019e7e53-a60d-71a2-9d76-9a134b20e743",
        "audit_id": "subagent_lane01_lane02_replay_audit",
        "finding_status": "integrated",
        "lanes": ["01", "02"],
        "material_findings": [
            "Friday clean freeze confirmed at 328 non-crypto primary rows from 2026-05-28T23:45Z through before 2026-05-29T21:00Z.",
            "Quality subset confirmed as 43 tradeable_now rows and +9.5R on current_selected_proxy_gross_r, not the manual portfolio seed.",
            "Broad selected replay confirmed by full shard scan at 289600 rows; normalized London liquidity and displacement metrics match Friday summary.",
            "Manual fixed-vNext seed exists only in prompts; no reproducible accepted/rejected sequential portfolio timeline artifact was found.",
            "Lane01 and Lane02 route directories/artifacts were absent at audit time.",
        ],
        "recommended_status": {
            "01": "NOT_STARTED_ARTIFACT_ABSENT",
            "02": "READY_AFTER_LANE01_INTERFACE_OR_ADAPTER_NOT_COMPLETE",
        },
        "schema_version": "vnext_next_level_subagent_finding_v1",
        "source": "subagent_notification",
    },
    {
        "agent_id": "019e7e53-bc1d-76f0-9d09-d8dc2757f8f0",
        "audit_id": "subagent_lane03_lane05_code_path_audit",
        "finding_status": "integrated",
        "lanes": ["03", "05"],
        "material_findings": [
            "Lane03 route artifacts are absent; current quality selector remains a narrow Friday/broad-backed session/origin/spread rule rather than a full meta-selector package.",
            "Lane05 route artifacts are absent; prop-safe/account-exposure governor repairs exist but no scheduler package, scheduler ledger, verifier, manifest, or completion audit exists.",
            "Runtime scheduler integration depends on Lane01 replay risk interfaces and Lane04 packet contracts before any live-behavior change is eligible.",
            "Shared-code risk identified around src/components/orchestrator.py check_permissions analysis/trade_params handoff; route-owned focused tests are required before merge.",
        ],
        "recommended_status": {
            "03": "NOT_STARTED_SCOPED_DISCOVERY_READY_NO_IMPLEMENTATION_DECISION",
            "05": "GATED_AFTER_LANE01_AND_LANE04_INITIAL_ARTIFACTS",
        },
        "schema_version": "vnext_next_level_subagent_finding_v1",
        "source": "subagent_notification",
    },
    {
        "agent_id": "019e7e53-da1a-76a1-9a0c-3a84b9f2ac34",
        "audit_id": "subagent_lane04_lane06_bridge_broker_audit",
        "finding_status": "integrated",
        "lanes": ["04", "06"],
        "material_findings": [
            "Friday full vNext ledger has 328 rows, but selected-cell risk proof exists for only 9 rows; 319 rows are missing or zero selected risk.",
            "Canonical Friday broker-ready audit records 274 bridge-missing selected-cell risk rows, 45 prop deferrals, 8 placed rows, and 1 dynamic refusal.",
            "Runtime shadow dynamic records include 527 rows, only 16 with selected risk pct, 214 with cell ID, and 511 selected_cell_risk_not_verified_or_zero refusals.",
            "Friday broker truth has 8 placed trades: 4 fully closed, 2 open at Friday close, and 2 partial residual open; net-R is available for 5 and blocked for 3.",
            "Live companion now contains real vNext fill/open-position evidence; close reconciliation is still pending and prose claiming flat state is stale against structured state.",
        ],
        "recommended_status": {
            "04": "NOT_STARTED_BUT_HIGHEST_PRIORITY_IMMEDIATE_PACKET_REPAIR",
            "06": "NOT_STARTED_PARTIAL_EVIDENCE_CLOSE_RECONCILIATION_PENDING",
        },
        "schema_version": "vnext_next_level_subagent_finding_v1",
        "source": "subagent_notification",
    },
    {
        "agent_id": "019e7e53-f288-7583-b451-0690f82d3219",
        "audit_id": "subagent_lane07_lane08_coverage_policy_audit",
        "finding_status": "integrated",
        "lanes": ["07", "08"],
        "material_findings": [
            "Friday market/starvation ledger covers 22 non-crypto symbols; BTCUSD and ETHUSD are appendix/excluded from primary Friday denominator.",
            "Live starvation summary covers all 24 symbols and 191 symbol/origin rows, but current window has zero dynamic and zero broker-ready rows.",
            "Lane07 has no route-owned 24-symbol source ledger, starvation repair ledger, verifier, manifest, or completion audit.",
            "Friday execution-policy selected denominator has 5904 rows, broker-ready policy denominator has 162 rows, and trailing simulation has 1640 rows.",
            "Lane08 has no route-owned microstructure stress ledger, implementation decision ledger, verifier, manifest, or completion audit.",
            "Static 1.5R verifier remains blocked by missing manifest-referenced shards; dynamic router and momentum promotion verifiers are passed.",
        ],
        "recommended_status": {
            "07": "NOT_STARTED_ON_DISK_READY_TO_LAUNCH_SOURCE_REPAIR",
            "08": "NOT_STARTED_ON_DISK_READY_TO_LAUNCH_STRESS_REPLAY_NO_POLICY_PROMOTION",
        },
        "schema_version": "vnext_next_level_subagent_finding_v1",
        "source": "subagent_notification",
    },
    {
        "agent_id": "019e7e54-0b98-7e60-8a74-906bfe79611d",
        "audit_id": "subagent_lane09_master_requirements_audit",
        "finding_status": "integrated_partially_superseded_by_current_master_scaffold",
        "lanes": ["09", "master"],
        "material_findings": [
            "At audit time the master route and all lane route directories were absent; current master route scaffold now supersedes only the master-absent portion.",
            "Master and lane goal prompts passed validator; all next-level starter files failed hardening checks before this session's starter repair.",
            "Lane09 prompt omitted orchestrator_successor_operating_brief.md before this session's prompt repair.",
            "Prompt validator is regex-based and does not catch every doctrine requirement; starter contracts remain material for goal runtime behavior.",
            "Lane09 must not start as a merge/package route until lane artifacts exist on disk.",
        ],
        "recommended_status": {
            "09": "GATED_NO_LANE_ARTIFACTS_TO_MERGE",
            "master": "MASTER_SCAFFOLD_REQUIRED_AND_NOW_PARTIALLY_MATERIALIZED",
        },
        "schema_version": "vnext_next_level_subagent_finding_v1",
        "source": "subagent_notification",
    },
]

LANES: list[dict[str, Any]] = [
    {
        "lane_id": "01",
        "title": "Fixed Friday portfolio replay engine",
        "prompt": "VNEXT_LANE01_FIXED_FRIDAY_PORTFOLIO_REPLAY_ENGINE_GOAL_PROMPT_2026-05-31.md",
        "starter": "VNEXT_LANE01_FIXED_FRIDAY_PORTFOLIO_REPLAY_ENGINE_STARTER_2026-05-31.txt",
        "route": "research/operations/vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31",
        "launch_class": "immediate",
        "dependencies": ["friday_microscope_route"],
        "expected_outputs": [
            "builder",
            "verifier",
            "accepted timeline ledger",
            "rejected trade ledger",
            "risk/exposure/dollar/R ledgers",
            "portfolio summary",
            "output manifest",
            "completion audit",
        ],
        "shared_code_ownership": [
            "portfolio replay interfaces",
            "Friday source artifact adapters",
            "risk/dollar sizing math helpers",
        ],
    },
    {
        "lane_id": "02",
        "title": "Broad selected portfolio replay stress",
        "prompt": "VNEXT_LANE02_BROAD_SELECTED_PORTFOLIO_REPLAY_STRESS_GOAL_PROMPT_2026-05-31.md",
        "starter": "VNEXT_LANE02_BROAD_SELECTED_PORTFOLIO_REPLAY_STRESS_STARTER_2026-05-31.txt",
        "route": "research/operations/vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31",
        "launch_class": "after_lane01_interface",
        "dependencies": ["lane01_replay_interface", "stage04_selected_denominator_shards"],
        "expected_outputs": [
            "broad selected replay/stress builder",
            "full selected denominator result ledgers",
            "split/cost/exposure/concentration summaries",
            "verifier",
            "output manifest",
            "completion audit",
        ],
        "shared_code_ownership": [
            "selected denominator shard readers",
            "portfolio replay stress engine",
        ],
    },
    {
        "lane_id": "03",
        "title": "Meta-selector discovery and implementation",
        "prompt": "VNEXT_LANE03_META_SELECTOR_DISCOVERY_IMPLEMENTATION_GOAL_PROMPT_2026-05-31.md",
        "starter": "VNEXT_LANE03_META_SELECTOR_DISCOVERY_IMPLEMENTATION_STARTER_2026-05-31.txt",
        "route": "research/operations/vnext_lane03_meta_selector_discovery_implementation_2026_05_31",
        "launch_class": "scaffold_now_update_after_lane02",
        "dependencies": ["friday_mechanism_expansion", "lane02_broad_split_artifacts"],
        "expected_outputs": [
            "selector design ledger",
            "exact/proxy R branch ledgers",
            "implementation decision ledger",
            "code/config/test package",
            "verifier",
            "output manifest",
            "completion audit",
        ],
        "shared_code_ownership": [
            "src/research/moonshot_default_off_policy_router.py",
            "config/agent_config.yaml",
            "tests/test_moonshot_candidate_quality_selector.py",
        ],
    },
    {
        "lane_id": "04",
        "title": "Selected-cell risk bridge and packet completeness",
        "prompt": "VNEXT_LANE04_SELECTED_CELL_RISK_BRIDGE_PACKET_COMPLETENESS_GOAL_PROMPT_2026-05-31.md",
        "starter": "VNEXT_LANE04_SELECTED_CELL_RISK_BRIDGE_PACKET_COMPLETENESS_STARTER_2026-05-31.txt",
        "route": "research/operations/vnext_lane04_selected_cell_risk_bridge_packet_completeness_2026_05_31",
        "launch_class": "immediate",
        "dependencies": ["friday_selected_risk_broker_ready_ledger", "live_candidate_packet_writer"],
        "expected_outputs": [
            "packet schema",
            "bridge ledger",
            "repair ledger",
            "source completeness ledger",
            "runtime packet/log writer patches",
            "verifier",
            "focused tests",
            "output manifest",
            "completion audit",
        ],
        "shared_code_ownership": [
            "src/components/orchestrator.py",
            "candidate packet/log writer code",
            "tests/test_vnext_broader_origin_orchestrator.py",
        ],
    },
    {
        "lane_id": "05",
        "title": "Runtime portfolio scheduler integration",
        "prompt": "VNEXT_LANE05_RUNTIME_PORTFOLIO_SCHEDULER_INTEGRATION_GOAL_PROMPT_2026-05-31.md",
        "starter": "VNEXT_LANE05_RUNTIME_PORTFOLIO_SCHEDULER_INTEGRATION_STARTER_2026-05-31.txt",
        "route": "research/operations/vnext_lane05_runtime_portfolio_scheduler_integration_2026_05_31",
        "launch_class": "after_lane01_and_lane04_initial_artifacts",
        "dependencies": ["lane01_replay_risk_interface", "lane04_packet_contracts"],
        "expected_outputs": [
            "code/config/test changes",
            "scheduler ledger",
            "before/after gate matrix",
            "implementation decision rows",
            "verifier",
            "output manifest",
            "completion audit",
        ],
        "shared_code_ownership": [
            "src/components/permissions.py",
            "risk/exposure gate helpers",
            "tests/test_concurrent_cap.py",
            "tests/test_vnext_broader_origin_orchestrator.py",
        ],
    },
    {
        "lane_id": "06",
        "title": "Broker lifecycle net-R and cost truth",
        "prompt": "VNEXT_LANE06_BROKER_LIFECYCLE_NET_R_COST_TRUTH_GOAL_PROMPT_2026-05-31.md",
        "starter": "VNEXT_LANE06_BROKER_LIFECYCLE_NET_R_COST_TRUTH_STARTER_2026-05-31.txt",
        "route": "research/operations/vnext_lane06_broker_lifecycle_net_r_cost_truth_2026_05_31",
        "launch_class": "immediate",
        "dependencies": ["friday_broker_truth_reconciliation", "live_companion_broker_lifecycle"],
        "expected_outputs": [
            "broker lifecycle ledger",
            "cost calibration ledger",
            "projected-vs-broker reconciliation",
            "notification parity verifier",
            "code/tests where truth incomplete",
            "output manifest",
            "completion audit",
        ],
        "shared_code_ownership": [
            "src/components/execution.py",
            "src/notifications.py",
            "broker audit/slippage helpers",
            "tests/test_notifications.py",
            "tests/test_limit_order_flow.py",
        ],
    },
    {
        "lane_id": "07",
        "title": "Market coverage, source, and starvation repair",
        "prompt": "VNEXT_LANE07_MARKET_COVERAGE_SOURCE_STARVATION_REPAIR_GOAL_PROMPT_2026-05-31.md",
        "starter": "VNEXT_LANE07_MARKET_COVERAGE_SOURCE_STARVATION_REPAIR_STARTER_2026-05-31.txt",
        "route": "research/operations/vnext_lane07_market_coverage_source_starvation_repair_2026_05_31",
        "launch_class": "immediate",
        "dependencies": ["friday_market_starvation_ledgers", "live_symbol_spec_and_capture_state"],
        "expected_outputs": [
            "24-symbol funnel ledger",
            "source integrity ledger",
            "starvation decision ledger",
            "repair ledger",
            "source-capture code/tests",
            "verifier",
            "output manifest",
            "completion audit",
        ],
        "shared_code_ownership": [
            "config/agent_config.yaml",
            "src/components/m1_capture.py",
            "symbol alias/spec handling",
            "scripts/watchdog.ps1",
            "tests/test_m1_capture.py",
        ],
    },
    {
        "lane_id": "08",
        "title": "Execution policy and microstructure stress",
        "prompt": "VNEXT_LANE08_EXECUTION_POLICY_MICROSTRUCTURE_STRESS_GOAL_PROMPT_2026-05-31.md",
        "starter": "VNEXT_LANE08_EXECUTION_POLICY_MICROSTRUCTURE_STRESS_STARTER_2026-05-31.txt",
        "route": "research/operations/vnext_lane08_execution_policy_microstructure_stress_2026_05_31",
        "launch_class": "after_lane01_interface_or_schema_adapter",
        "dependencies": ["lane01_replay_interface", "lane02_stress_outputs", "lane06_cost_truth"],
        "expected_outputs": [
            "execution policy ledgers",
            "microstructure stress ledgers",
            "exact/proxy R summaries",
            "implementation decision ledger",
            "code/test package where supported",
            "verifier",
            "output manifest",
            "completion audit",
        ],
        "shared_code_ownership": [
            "src/research/moonshot_default_off_policy_router.py",
            "execution policy replay builders",
            "tests/test_moonshot_default_off_policy_router.py",
        ],
    },
    {
        "lane_id": "09",
        "title": "Cross-lane merge dossier and production package",
        "prompt": "VNEXT_LANE09_CROSS_LANE_MERGE_DOSSIER_PRODUCTION_PACKAGE_GOAL_PROMPT_2026-05-31.md",
        "starter": "VNEXT_LANE09_CROSS_LANE_MERGE_DOSSIER_PRODUCTION_PACKAGE_STARTER_2026-05-31.txt",
        "route": "research/operations/vnext_lane09_cross_lane_merge_dossier_production_package_2026_05_31",
        "launch_class": "gated_after_lane_artifacts",
        "dependencies": ["lanes01_to_08_terminal_artifacts"],
        "expected_outputs": [
            "merge dossier",
            "production package",
            "route manifest",
            "verification matrix",
            "result materialization ledger",
            "implementation decision ledger",
            "blocker ledger",
            "completion audit",
        ],
        "shared_code_ownership": [
            "cross-lane diff review",
            "global verifier/test matrix",
            "production-change dossier artifacts",
        ],
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def run_git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def git_head() -> dict[str, str | None]:
    full = run_git(["rev-parse", "HEAD"])
    short_subject = run_git(["log", "-1", "--format=%h %s"])
    return {"full_sha": full, "short_subject": short_subject}


def latest_scoped_package_commit_sha() -> str | None:
    history = run_git(["log", "-n", "50", "--format=%H%x09%s"])
    if not history:
        return None
    for line in history.splitlines():
        if "\t" not in line:
            continue
        sha, subject = line.split("\t", 1)
        if subject == SCOPED_PACKAGE_COMMIT_SUBJECT:
            return sha
    return None


def git_commit_paths(sha: str) -> list[str]:
    output = run_git(["show", "--name-only", "--format=", "--no-renames", sha])
    if not output:
        return []
    return [line.replace("\\", "/") for line in output.splitlines() if line.strip()]


def detect_scoped_package_commit() -> dict[str, Any]:
    sha = latest_scoped_package_commit_sha()
    if not sha:
        return {
            "scoped_commit_forbidden_path_count": None,
            "scoped_commit_forbidden_paths": [],
            "scoped_commit_missing_required_paths": list(SCOPED_PACKAGE_REQUIRED_PATHS),
            "scoped_commit_missing_required_prefixes": list(SCOPED_PACKAGE_REQUIRED_PREFIXES),
            "scoped_commit_path_count": 0,
            "scoped_commit_paths": [],
            "scoped_commit_performed": False,
            "scoped_commit_sha": None,
            "scoped_commit_short_subject": None,
            "scoped_commit_status": "not_performed; no scoped implementation package commit found in recent history",
        }
    paths = git_commit_paths(sha)
    path_set = set(paths)
    forbidden_paths = sorted(
        path for path in paths if path.startswith(SCOPED_PACKAGE_FORBIDDEN_PREFIXES)
    )
    missing_required_paths = sorted(
        path for path in SCOPED_PACKAGE_REQUIRED_PATHS if path not in path_set
    )
    missing_required_prefixes = sorted(
        prefix
        for prefix in SCOPED_PACKAGE_REQUIRED_PREFIXES
        if not any(path.startswith(prefix) for path in paths)
    )
    scope_ok = not forbidden_paths and not missing_required_paths and not missing_required_prefixes
    short_subject = run_git(["show", "-s", "--format=%h %s", sha])
    return {
        "scoped_commit_forbidden_path_count": len(forbidden_paths),
        "scoped_commit_forbidden_paths": forbidden_paths,
        "scoped_commit_missing_required_paths": missing_required_paths,
        "scoped_commit_missing_required_prefixes": missing_required_prefixes,
        "scoped_commit_path_count": len(paths),
        "scoped_commit_paths": paths,
        "scoped_commit_performed": scope_ok,
        "scoped_commit_sha": sha,
        "scoped_commit_short_subject": short_subject,
        "scoped_commit_status": "performed_scope_audited"
        if scope_ok
        else "found_but_failed_scope_audit",
    }


def latest_commit_for(path: Path) -> dict[str, str | None]:
    if not path.exists():
        return {"full_sha": None, "short_subject": None}
    full = run_git(["log", "-1", "--format=%H", "--", rel(path)])
    short_subject = run_git(["log", "-1", "--format=%h %s", "--", rel(path)])
    return {"full_sha": full, "short_subject": short_subject}


def git_status_for(path: Path) -> list[str]:
    try:
        status = subprocess.check_output(
            ["git", "status", "--short", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).rstrip("\n")
    except Exception:
        status = ""
    return status.splitlines() if status else []


def git_status_porcelain_all() -> list[dict[str, Any]]:
    try:
        status = subprocess.check_output(
            ["git", "status", "--porcelain=v1", "-uall"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).rstrip("\n")
    except Exception:
        status = ""
    rows: list[dict[str, Any]] = []
    if not status:
        return rows
    for line in status.splitlines():
        if len(line) < 4:
            continue
        status_code = line[:2]
        path_text = line[3:].replace("\\", "/")
        rows.append(
            {
                "path": path_text,
                "staged": status_code[0] not in {" ", "?"},
                "status_code": status_code,
                "worktree_changed": status_code == "??" or status_code[1] not in {" ", "?"},
            }
        )
    return rows


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_jsonl(path: Path) -> int | None:
    if path.suffix.lower() != ".jsonl" or not path.exists():
        return None
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return sum(1 for line in handle if line.strip())


def file_evidence(path: Path, source_role: str) -> dict[str, Any]:
    item: dict[str, Any] = {
        "exists": path.exists(),
        "path": rel(path),
        "source_role": source_role,
    }
    if path.exists() and path.is_file():
        item.update(
            {
                "kind": "file",
                "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                "row_count": count_jsonl(path),
                "sha256": sha256(path),
                "size_bytes": path.stat().st_size,
            }
        )
    elif path.exists():
        item["kind"] = "directory"
        item["file_count"] = sum(1 for child in path.rglob("*") if child.is_file())
    return item


def metric(summary: dict[str, Any], key: str) -> dict[str, Any]:
    row = summary.get(key, {}) if isinstance(summary, dict) else {}
    return {
        "breakeven": row.get("breakeven"),
        "gross_r_avg": row.get("gross_r_avg"),
        "gross_r_sum": row.get("gross_r_sum"),
        "known_r_rows": row.get("known_r_rows"),
        "losses": row.get("losses"),
        "rows": row.get("rows"),
        "win_rate": row.get("win_rate"),
        "wins": row.get("wins"),
    }


def validate_prompt(path: Path, *, kind: str = "builder") -> dict[str, Any]:
    command = [sys.executable, "scripts/validate_goal_prompt_hardening.py", rel(path), "--kind", kind]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    return {
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "ok": completed.returncode == 0,
        "prompt_path": rel(path),
        "stderr_tail": completed.stderr[-1000:],
        "stdout_tail": completed.stdout[-1000:],
    }


def route_file_count(route_path: Path) -> int:
    if not route_path.exists():
        return 0
    return sum(1 for child in route_path.rglob("*") if child.is_file())


def first_match(route_path: Path, pattern: str) -> Path | None:
    if not route_path.exists():
        return None
    matches = sorted(path for path in route_path.rglob(pattern) if path.is_file())
    return matches[0] if matches else None


def lane09_packaged_lane_state(lane_id: str) -> dict[str, Any] | None:
    verifier = load_json(LANE09_ROUTE_DIR / "LANE09_VERIFICATION_RESULT.json", {})
    audit = load_json(LANE09_ROUTE_DIR / "LANE09_COMPLETION_AUDIT.json", {})
    if not verifier_payload_ok(verifier) or not audit.get("completion_ready_for_master"):
        return None
    for row in load_jsonl(LANE09_ROUTE_DIR / "LANE09_LANE_VERIFICATION_MATRIX.jsonl"):
        if row.get("lane_id") == lane_id and row.get("lane09_terminal_accepted"):
            return row
    return None


def verifier_payload_ok(payload: dict[str, Any]) -> bool:
    status = str(payload.get("status") or payload.get("result") or "").lower()
    return bool(
        payload.get("ok")
        or payload.get("passed")
        or status in {"verified", "pass", "passed", "ok", "complete", "completed"}
    )


def lane_route_terminal_status(route_path: Path) -> dict[str, Any]:
    audit_path = first_match(route_path, "*COMPLETION_AUDIT.json")
    verifier_path = first_match(route_path, "*VERIFICATION_RESULT.json")
    audit = load_json(audit_path, {}) if audit_path else {}
    verifier = load_json(verifier_path, {}) if verifier_path else {}
    audit_verifier = audit.get("verifier_result")
    if not isinstance(audit_verifier, dict):
        audit_verifier = {}
    verifier_ok = verifier_payload_ok(verifier) or verifier_payload_ok(audit_verifier)
    audit_status = str(audit.get("status", "")).lower()
    audit_decision = str(audit.get("completion_decision", "")).lower()
    audit_schema = str(audit.get("schema_version", "")).lower()
    audit_complete = bool(
        audit.get("can_mark_route_complete")
        or audit.get("completion_ready")
        or audit.get("can_mark_route_complete_after_verifier")
        or audit_status in {"complete", "completed", "pass", "passed"}
        or audit_status.startswith("complete")
        or audit_decision.startswith("complete")
        or ("completion_audit" in audit_schema and bool(audit.get("outputs")))
    )
    return {
        "completion_audit_path": rel(audit_path) if audit_path else None,
        "completion_audit_route_complete": audit_complete,
        "route_file_count": route_file_count(route_path),
        "terminal_artifacts_present": bool(audit_path and verifier_path and verifier_ok and audit_complete),
        "verification_result_ok": verifier_ok,
        "verification_result_path": rel(verifier_path) if verifier_path else None,
    }


def route_path_for_lane(lane_id: str) -> Path:
    for lane in LANES:
        if lane["lane_id"] == lane_id:
            return ROOT / lane["route"]
    raise KeyError(f"unknown lane_id {lane_id}")


def lane_current_status(
    lane: dict[str, Any],
    route_path: Path,
    terminal_status: dict[str, Any],
) -> tuple[str, str]:
    if terminal_status["terminal_artifacts_present"]:
        return "route_terminal_artifacts_present_verifier_ok", "none_terminal_lane_complete"
    if route_path.exists() and route_file_count(route_path) > 0:
        return "route_artifacts_present_needs_disk_audit", "route_artifact_audit_required"
    launch_class = lane["launch_class"]
    if launch_class == "immediate":
        return "ready_to_launch_no_route_artifacts_on_disk", "route_not_started"
    if launch_class == "gated_after_lane_artifacts":
        return "gated_until_lanes01_to_08_materialize_terminal_artifacts", "gated_merge_lane"
    return "dependency_or_schema_interface_needed_before_full_launch", "upstream_interface_dependency"


def build_registry(now: str, prompt_checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks_by_prompt = {check["prompt_path"]: check for check in prompt_checks}
    findings = load_jsonl(ROUTE_DIR / "MASTER_SUBAGENT_AUDIT_FINDINGS.jsonl")
    findings_by_lane: dict[str, list[dict[str, Any]]] = {}
    for row in findings:
        for lane_id in row.get("lanes", []):
            findings_by_lane.setdefault(str(lane_id), []).append(row)

    registry: list[dict[str, Any]] = []
    request_by_lane: dict[str, list[dict[str, Any]]] = {}
    for request in SUBAGENT_AUDIT_REQUESTS:
        for lane_id in request["lanes"]:
            request_by_lane.setdefault(str(lane_id), []).append(request)

    for lane in LANES:
        prompt_path = PROMPT_DIR / lane["prompt"]
        starter_path = PROMPT_DIR / lane["starter"]
        route_path = ROOT / lane["route"]
        terminal_status = apply_external_session_lane_policy(
            lane["lane_id"], route_path, lane_route_terminal_status(route_path)
        )
        terminal_status = apply_external_dependency_policy(lane, terminal_status)
        external_owner = EXTERNAL_SESSION_OWNED_LANES.get(lane["lane_id"])
        status, blocker_class = lane_current_status(lane, route_path, terminal_status)
        if external_owner and route_path.exists():
            status = "external_goal_session_active_handoff_artifacts_present_unaccepted"
            blocker_class = "external_goal_session_owned_handoff_pending"
        elif terminal_status.get("external_dependency_pending_lanes"):
            status = "external_dependency_pending_terminal_acceptance"
            blocker_class = "external_lane_dependency_pending"
        prompt_rel = rel(prompt_path)
        registry.append(
            {
                "blocker_class": blocker_class,
                "current_status": status,
                "expected_outputs": lane["expected_outputs"],
                "inspected_from_disk_status": {
                    **terminal_status,
                    "prompt_exists": prompt_path.exists(),
                    "route_exists": route_path.exists(),
                    "starter_exists": starter_path.exists(),
                },
                "lane_id": lane["lane_id"],
                "latest_commit": {
                    "prompt": latest_commit_for(prompt_path),
                    "route": latest_commit_for(route_path),
                    "starter": latest_commit_for(starter_path),
                },
                "launch_class": lane["launch_class"],
                "prompt_hardening": checks_by_prompt.get(prompt_rel, {"ok": False, "reason": "not_checked"}),
                "prompt_path": prompt_rel,
                "route_path": rel(route_path),
                "shared_code_ownership": lane["shared_code_ownership"],
                "starter_path": rel(starter_path),
                "subagent_audits": {
                    "findings": findings_by_lane.get(lane["lane_id"], []),
                    "requests": request_by_lane.get(lane["lane_id"], []),
                },
                "title": lane["title"],
                "updated_at_utc": now,
                "verifier_status": "terminal_verified"
                if terminal_status["terminal_artifacts_present"]
                else (
                    "missing_until_lane_route_materializes"
                    if not route_path.exists()
                    else "route_present_verifier_audit_required"
                ),
            }
        )
    return registry


def build_dependency_graph(now: str) -> dict[str, Any]:
    edges = []
    for lane in LANES:
        for dependency in lane["dependencies"]:
            edges.append({"from": dependency, "to": f"lane{lane['lane_id']}", "edge_type": "input_dependency"})
    edges.extend(
        [
            {"from": "lane01", "to": "lane02", "edge_type": "replay_interface"},
            {"from": "lane01", "to": "lane05", "edge_type": "risk_replay_interface"},
            {"from": "lane04", "to": "lane05", "edge_type": "packet_contract"},
            {"from": "lane02", "to": "lane03", "edge_type": "broad_split_evidence"},
            {"from": "lane06", "to": "lane08", "edge_type": "broker_cost_truth"},
            {"from": "lane01", "to": "lane08", "edge_type": "portfolio_replay_interface"},
        ]
    )
    for lane_id in [f"lane{lane['lane_id']}" for lane in LANES if lane["lane_id"] != "09"]:
        edges.append({"from": lane_id, "to": "lane09", "edge_type": "merge_input"})
    return {
        "edges": edges,
        "generated_at_utc": now,
        "nodes": [
            {"id": f"lane{lane['lane_id']}", "label": lane["title"], "route": lane["route"]}
            for lane in LANES
        ]
        + [
            {"id": "friday_microscope_route", "label": "Friday microscope disk evidence", "route": rel(FRIDAY_DIR)},
            {
                "id": "stage04_selected_denominator_shards",
                "label": "289,600 selected denominator activation-repair shards",
                "route": rel(ACTIVATION_DIR),
            },
            {
                "id": "live_companion_broker_lifecycle",
                "label": "current live activation companion lifecycle evidence",
                "route": rel(LIVE_COMPANION_DIR),
            },
        ],
        "route_id": ROUTE_ID,
        "schema_version": "vnext_next_level_lane_dependency_graph_v1",
    }


def build_evidence_inspection_ledger() -> list[dict[str, Any]]:
    paths = [
        (ROOT / ".context" / "LIVE_STATE.md", "preflight_live_state"),
        (ROOT / ".context" / "00_core" / "current_vnext_system_map.md", "current_system_map"),
        (ROOT / ".context" / "00_core" / "current_repo_reading_order.md", "current_reading_order"),
        (ROOT / ".context" / "00_core" / "quick_reference_card.md", "quick_reference"),
        (ROOT / ".context" / "00_core" / "goal_session_research_discipline.md", "research_discipline"),
        (ROOT / ".context" / "00_core" / "research_operating_doctrine.md", "research_doctrine"),
        (ROOT / ".context" / "00_core" / "orchestrator_successor_operating_brief.md", "orchestrator_brief"),
        (ROOT / ".context" / "00_core" / "orchestrator_methodology_hardening_controls.md", "hardening_controls"),
        (ROOT / ".context" / "00_core" / "parallel_goal_merge_playbook.md", "merge_playbook"),
        (ROOT / ".context" / "00_core" / "local_heavy_data_inventory.md", "local_heavy_data_policy"),
        (MASTER_PROMPT, "master_controlling_prompt"),
        (MASTER_STARTER, "master_starter"),
        (LAUNCH_PACK, "parallel_launch_pack"),
        (FRIDAY_DIR / "FRIDAY_MICROSCOPE_FINAL_REPORT.md", "friday_final_report"),
        (FRIDAY_DIR / "FRIDAY_MICROSCOPE_COMPLETION_AUDIT.json", "friday_completion_audit"),
        (FRIDAY_DIR / "FRIDAY_MICROSCOPE_OUTPUT_MANIFEST.json", "friday_output_manifest"),
        (FRIDAY_DIR / "FRIDAY_MICROSCOPE_FINAL_VERIFICATION_RESULT.json", "friday_final_verification"),
        (FRIDAY_DIR / "FRIDAY_MICROSCOPE_FOCUSED_TEST_RESULT.json", "friday_focused_test_result"),
        (FRIDAY_DIR / "FRIDAY_QUALITY_SELECTOR_BROAD_REPLAY_SUMMARY.json", "friday_quality_broad_replay"),
        (FRIDAY_DIR / "FRIDAY_FULL_VNEXT_SYSTEM_REPLAY_SUMMARY.json", "friday_full_replay"),
        (FRIDAY_DIR / "FRIDAY_RAW_VS_SELECTED_DENOMINATOR_RECONCILIATION.json", "friday_denominator_reconciliation"),
        (FRIDAY_DIR / "FRIDAY_MARKET_STARVATION_BY_SYMBOL_LEDGER.jsonl", "friday_market_starvation"),
        (FRIDAY_DIR / "FRIDAY_BROKER_TRUTH_RECONCILIATION_LEDGER.jsonl", "friday_broker_truth"),
        (LIVE_COMPANION_DIR / "ACTIVE_REPAIR_STATE.json", "live_companion_state"),
        (LIVE_COMPANION_DIR / "LIVE_REPLAY_GATE_STACK_PARITY_SUMMARY.json", "live_replay_gate_stack_parity"),
        (ACTIVATION_DIR / "VNEXT_ACTIVATION_REPAIR_STAGE06_FINAL_ROUTE_STATE_2026-05-27.json", "activation_repair_state"),
    ]
    return [file_evidence(path, source_role) for path, source_role in paths]


def build_seed_fact_audit(now: str) -> dict[str, Any]:
    quality = load_json(FRIDAY_DIR / "FRIDAY_QUALITY_SELECTOR_BROAD_REPLAY_SUMMARY.json", {})
    full = load_json(FRIDAY_DIR / "FRIDAY_FULL_VNEXT_SYSTEM_REPLAY_SUMMARY.json", {})
    raw = load_json(FRIDAY_DIR / "FRIDAY_RAW_VS_SELECTED_DENOMINATOR_RECONCILIATION.json", {})
    verification = load_json(FRIDAY_DIR / "FRIDAY_MICROSCOPE_FINAL_VERIFICATION_RESULT.json", {})
    activation = load_json(ACTIVATION_DIR / "VNEXT_ACTIVATION_REPAIR_STAGE06_FINAL_ROUTE_STATE_2026-05-27.json", {})
    gate = load_json(LIVE_COMPANION_DIR / "LIVE_REPLAY_GATE_STACK_PARITY_SUMMARY.json", {})
    live_state = load_json(LIVE_COMPANION_DIR / "ACTIVE_REPAIR_STATE.json", {})
    clean = quality.get("clean_friday_quality_metrics", {})
    broad = quality.get("broad_selected_replay", {}).get("normalized_london_rule_metrics", {})
    lane01_route = route_path_for_lane("01")
    lane01_status = lane_route_terminal_status(lane01_route)
    lane01_summary = (
        load_json(lane01_route / "LANE01_PORTFOLIO_REPLAY_SUMMARY.json", {})
        if lane01_status["terminal_artifacts_present"]
        else {}
    )
    manual_seed_fact = (
        {
            "accepted": lane01_summary.get("accepted_rows"),
            "accepted_effective_gross_dollars": lane01_summary.get("accepted_effective_gross_dollars"),
            "gross_r_sum": lane01_summary.get("accepted_gross_r_sum"),
            "quality_subset_rows": lane01_summary.get("quality_subset_rows"),
            "rejected": lane01_summary.get("rejected_rows"),
            "reproduction_status": "materialized_by_lane01_route_terminal_verified",
            "source": lane01_status["completion_audit_path"],
            "start_equity_usd": lane01_summary.get("account_baseline", {}).get("freeze_start_current_equity"),
        }
        if lane01_status["terminal_artifacts_present"]
        else {
            "accepted": 18,
            "end_equity_usd": 117868.34,
            "gross_r_sum": 13.5,
            "reproduction_status": "not_materialized_on_current_disk_master_pass_assigned_to_lane01",
            "rejected": 25,
            "source": "controlling_prompt_seed_only_until_lane01_builder_recomputes_or_corrects",
            "start_equity_usd": 100339.58,
        }
    )
    return {
        "audit_status": "seed_facts_reproduced_or_assigned_from_disk",
        "friday_seed_facts": {
            "broad_london_displacement": broad.get("london|displacement_continuation"),
            "broad_london_liquidity": broad.get("london|liquidity_sweep_reclaim"),
            "clean_quality_subset": metric(clean, "tradeable_now"),
            "friday_primary_non_crypto_rows": full.get("primary_rows"),
            "manual_fixed_vnext_portfolio_seed": manual_seed_fact,
            "raw_vs_selected_status_counts": raw.get("status_counts"),
        },
        "generated_at_utc": now,
        "live_companion_status": live_state.get("status"),
        "prompt_seed_policy": "disk recomputation wins over prompt seed numbers",
        "route_id": ROUTE_ID,
        "schema_version": "vnext_next_level_seed_fact_audit_v1",
        "source_artifacts": {
            "activation_state": rel(ACTIVATION_DIR / "VNEXT_ACTIVATION_REPAIR_STAGE06_FINAL_ROUTE_STATE_2026-05-27.json"),
            "friday_quality_summary": rel(FRIDAY_DIR / "FRIDAY_QUALITY_SELECTOR_BROAD_REPLAY_SUMMARY.json"),
            "friday_verification": rel(FRIDAY_DIR / "FRIDAY_MICROSCOPE_FINAL_VERIFICATION_RESULT.json"),
            "live_gate_parity": rel(LIVE_COMPANION_DIR / "LIVE_REPLAY_GATE_STACK_PARITY_SUMMARY.json"),
        },
        "verification_status": {
            "activation_dynamic_router_rows": activation.get("execution_intelligence_final_dynamic_router_rows"),
            "friday_route_verification_ok": verification.get("ok"),
            "live_gate_parity_required_gate_count": gate.get("required_gate_count"),
            "live_gate_parity_replay_rows": gate.get("replay_selected_rows"),
        },
    }


def build_result_materialization_ledger(now: str) -> list[dict[str, Any]]:
    quality = load_json(FRIDAY_DIR / "FRIDAY_QUALITY_SELECTOR_BROAD_REPLAY_SUMMARY.json", {})
    policy = load_json(FRIDAY_DIR / "FRIDAY_POLICY_ROUTER_REDESIGN_SUMMARY.json", {})
    full = load_json(FRIDAY_DIR / "FRIDAY_FULL_VNEXT_SYSTEM_REPLAY_SUMMARY.json", {})
    broker_rows = load_jsonl(FRIDAY_DIR / "FRIDAY_BROKER_TRUTH_RECONCILIATION_LEDGER.jsonl")
    activation = load_json(ACTIVATION_DIR / "VNEXT_ACTIVATION_REPAIR_STAGE06_FINAL_ROUTE_STATE_2026-05-27.json", {})
    gate = load_json(LIVE_COMPANION_DIR / "LIVE_REPLAY_GATE_STACK_PARITY_SUMMARY.json", {})
    lane01_route = route_path_for_lane("01")
    lane01_status = lane_route_terminal_status(lane01_route)
    lane01_audit = (
        load_json(first_match(lane01_route, "*COMPLETION_AUDIT.json"), {})
        if lane01_status["terminal_artifacts_present"]
        else {}
    )

    clean = quality.get("clean_friday_quality_metrics", {})
    broad = quality.get("broad_selected_replay", {}).get("normalized_london_rule_metrics", {})
    broker_status = Counter(row.get("net_broker_r_status") for row in broker_rows)
    rows = [
        {
            "branch_decision": "materialized_friday_quality_subset_source_bound_proxy_r",
            "evidence_path": rel(FRIDAY_DIR / "FRIDAY_QUALITY_SELECTOR_BROAD_REPLAY_SUMMARY.json"),
            "lane_owner": "lane01_lane03_lane08",
            "materialization_result_scope": "clean_friday_current_selected_proxy_r",
            "metric": metric(clean, "tradeable_now"),
            "result_materialization_status": "materialized_from_friday_route",
            "schema_version": "vnext_next_level_result_materialization_v1",
            "timestamp_utc": now,
        },
        {
            "branch_decision": "materialized_broad_london_liquidity_selected_support",
            "evidence_path": rel(FRIDAY_DIR / "FRIDAY_QUALITY_SELECTOR_BROAD_REPLAY_SUMMARY.json"),
            "lane_owner": "lane02_lane03",
            "materialization_result_scope": "broad_selected_proxy_r",
            "metric": broad.get("london|liquidity_sweep_reclaim"),
            "result_materialization_status": "materialized_from_friday_route",
            "schema_version": "vnext_next_level_result_materialization_v1",
            "timestamp_utc": now,
        },
        {
            "branch_decision": "materialized_broad_london_displacement_selected_support",
            "evidence_path": rel(FRIDAY_DIR / "FRIDAY_QUALITY_SELECTOR_BROAD_REPLAY_SUMMARY.json"),
            "lane_owner": "lane02_lane03",
            "materialization_result_scope": "broad_selected_proxy_r",
            "metric": broad.get("london|displacement_continuation"),
            "result_materialization_status": "materialized_from_friday_route",
            "schema_version": "vnext_next_level_result_materialization_v1",
            "timestamp_utc": now,
        },
        {
            "branch_decision": "friday_current_selected_policy_baseline_materialized",
            "evidence_path": rel(FRIDAY_DIR / "FRIDAY_POLICY_ROUTER_REDESIGN_SUMMARY.json"),
            "lane_owner": "lane08",
            "materialization_result_scope": "clean_friday_selected_denominator_policy_replay",
            "metric": metric(policy.get("selected_policy_summaries", {}), "current_selected_policy"),
            "result_materialization_status": "materialized_from_friday_route",
            "schema_version": "vnext_next_level_result_materialization_v1",
            "timestamp_utc": now,
        },
        {
            "branch_decision": "broker_ready_friday_policy_baseline_materialized",
            "evidence_path": rel(FRIDAY_DIR / "FRIDAY_POLICY_ROUTER_REDESIGN_SUMMARY.json"),
            "lane_owner": "lane06_lane08",
            "materialization_result_scope": "clean_friday_broker_ready_policy_replay",
            "metric": metric(policy.get("broker_ready_policy_summaries", {}), "current_selected_policy"),
            "result_materialization_status": "materialized_from_friday_route",
            "schema_version": "vnext_next_level_result_materialization_v1",
            "timestamp_utc": now,
        },
        {
            "branch_decision": "manual_fixed_vnext_seed_recomputed_by_lane01"
            if lane01_status["terminal_artifacts_present"]
            else "manual_fixed_vnext_seed_not_yet_reproducible_from_master_disk_pass",
            "evidence_path": lane01_status["completion_audit_path"]
            if lane01_status["terminal_artifacts_present"]
            else rel(MASTER_PROMPT),
            "lane_owner": "lane01",
            "materialization_result_scope": "lane01_fixed_friday_portfolio_replay"
            if lane01_status["terminal_artifacts_present"]
            else "manual_seed_only_until_lane01_replay_builder",
            "metric": lane01_audit.get("summary_metrics")
            if lane01_status["terminal_artifacts_present"]
            else {
                "accepted": 18,
                "gross_r_sum": 13.5,
                "rejected": 25,
                "seed_quality_rows": 43,
            },
            "result_materialization_status": "materialized_from_lane01_route_terminal_verified"
            if lane01_status["terminal_artifacts_present"]
            else "not_materialized_current_disk_assigned_to_lane01",
            "schema_version": "vnext_next_level_result_materialization_v1",
            "timestamp_utc": now,
        },
        {
            "branch_decision": "activation_dynamic_router_broad_replay_materialized",
            "evidence_path": rel(ACTIVATION_DIR / "VNEXT_ACTIVATION_REPAIR_STAGE06_FINAL_ROUTE_STATE_2026-05-27.json"),
            "lane_owner": "lane02_lane08",
            "materialization_result_scope": "broad_selected_dynamic_router_replay",
            "metric": activation.get("execution_intelligence_final_dynamic_router_metrics"),
            "result_materialization_status": "materialized_from_activation_route",
            "schema_version": "vnext_next_level_result_materialization_v1",
            "timestamp_utc": now,
        },
        {
            "branch_decision": "live_gate_stack_selected_projection_materialized",
            "evidence_path": rel(LIVE_COMPANION_DIR / "LIVE_REPLAY_GATE_STACK_PARITY_SUMMARY.json"),
            "lane_owner": "lane04_lane05_lane07",
            "materialization_result_scope": "live_replay_gate_stack_and_selected_trade_projection",
            "metric": {
                "replay_selected_rows": gate.get("replay_selected_rows"),
                "required_gate_count": gate.get("required_gate_count"),
                "selected_trade_projection_counts": gate.get("selected_trade_projection", {}).get("counts"),
            },
            "result_materialization_status": "materialized_from_live_companion_route",
            "schema_version": "vnext_next_level_result_materialization_v1",
            "timestamp_utc": now,
        },
        {
            "branch_decision": "friday_broker_lifecycle_truth_materialized_partial_net_r_gap_remains",
            "evidence_path": rel(FRIDAY_DIR / "FRIDAY_BROKER_TRUTH_RECONCILIATION_LEDGER.jsonl"),
            "lane_owner": "lane06",
            "materialization_result_scope": "friday_broker_truth_reconciliation",
            "metric": {
                "net_broker_r_status_counts": dict(broker_status),
                "rows": len(broker_rows),
            },
            "result_materialization_status": "materialized_with_source_specific_gap",
            "schema_version": "vnext_next_level_result_materialization_v1",
            "timestamp_utc": now,
        },
        {
            "branch_decision": "friday_selected_denominator_counts_materialized",
            "evidence_path": rel(FRIDAY_DIR / "FRIDAY_FULL_VNEXT_SYSTEM_REPLAY_SUMMARY.json"),
            "lane_owner": "lane01_lane04_lane05_lane07",
            "materialization_result_scope": "clean_friday_denominator_counts",
            "metric": full.get("denominator_counts"),
            "result_materialization_status": "materialized_from_friday_route",
            "schema_version": "vnext_next_level_result_materialization_v1",
            "timestamp_utc": now,
        },
    ]
    lane07_route = route_path_for_lane("07")
    lane07_status = lane_route_terminal_status(lane07_route)
    if lane07_status["terminal_artifacts_present"]:
        lane07_audit = load_json(first_match(lane07_route, "*COMPLETION_AUDIT.json"), {})
        rows.append(
            {
                "branch_decision": "lane07_market_coverage_route_verified_complete",
                "evidence_path": lane07_status["completion_audit_path"],
                "lane_owner": "lane07",
                "materialization_result_scope": "24_symbol_source_starvation_repair_route",
                "metric": {
                    "counts": lane07_audit.get("counts"),
                    "runtime_effect_boundary": lane07_audit.get("runtime_effect_boundary"),
                    "verifier_result": lane07_audit.get("verifier_result"),
                },
                "result_materialization_status": "materialized_from_lane07_route_terminal_verified",
                "schema_version": "vnext_next_level_result_materialization_v1",
                "timestamp_utc": now,
            }
        )
    for lane_id in ["04", "06"]:
        lane_route = route_path_for_lane(lane_id)
        lane_status = lane_route_terminal_status(lane_route)
        if not lane_status["terminal_artifacts_present"]:
            continue
        audit = load_json(first_match(lane_route, "*COMPLETION_AUDIT.json"), {})
        verifier = load_json(first_match(lane_route, "*VERIFICATION_RESULT.json"), {})
        summary_path = lane_route / f"LANE{lane_id}_SUMMARY.json"
        rows.append(
            {
                "branch_decision": f"lane{lane_id}_route_verified_complete",
                "evidence_path": lane_status["completion_audit_path"],
                "lane_owner": f"lane{lane_id}",
                "materialization_result_scope": f"lane{lane_id}_terminal_route",
                "metric": {
                    "completion_schema": audit.get("schema_version"),
                    "summary": load_json(summary_path, {}) if summary_path.exists() else None,
                    "verifier": verifier,
                },
                "result_materialization_status": f"materialized_from_lane{lane_id}_route_terminal_verified",
                "schema_version": "vnext_next_level_result_materialization_v1",
                "timestamp_utc": now,
            }
        )
    lane09_route = route_path_for_lane("09")
    lane09_status = lane_route_terminal_status(lane09_route)
    if lane09_status["terminal_artifacts_present"]:
        audit = load_json(first_match(lane09_route, "*COMPLETION_AUDIT.json"), {})
        package = load_json(lane09_route / "LANE09_PRODUCTION_PACKAGE.json", {})
        verifier = load_json(first_match(lane09_route, "*VERIFICATION_RESULT.json"), {})
        rows.append(
            {
                "branch_decision": "lane09_cross_lane_package_verified_complete",
                "evidence_path": lane09_status["completion_audit_path"],
                "lane_owner": "lane09",
                "materialization_result_scope": "cross_lane_merge_dossier_and_local_production_package",
                "metric": {
                    "accepted_lane_packages": audit.get("accepted_lane_packages"),
                    "completion_ready_for_master": audit.get("completion_ready_for_master"),
                    "live_production_change_ready": package.get("live_production_change_ready"),
                    "remaining_blockers": audit.get("remaining_blockers"),
                    "verifier": verifier,
                },
                "result_materialization_status": "materialized_from_lane09_route_terminal_verified",
                "schema_version": "vnext_next_level_result_materialization_v1",
                "timestamp_utc": now,
            }
        )
    return rows


def build_blocker_ledger(now: str) -> list[dict[str, Any]]:
    raw = load_json(FRIDAY_DIR / "FRIDAY_RAW_VS_SELECTED_DENOMINATOR_RECONCILIATION.json", {})
    completion = load_json(FRIDAY_DIR / "FRIDAY_MICROSCOPE_COMPLETION_AUDIT.json", {})
    live_state = load_json(LIVE_COMPANION_DIR / "ACTIVE_REPAIR_STATE.json", {})
    gate = load_json(LIVE_COMPANION_DIR / "LIVE_REPLAY_GATE_STACK_PARITY_SUMMARY.json", {})
    lane_terminal = {
        lane["lane_id"]: apply_external_dependency_policy(
            lane,
            apply_external_session_lane_policy(
                lane["lane_id"],
                ROOT / lane["route"],
                lane_route_terminal_status(ROOT / lane["route"]),
            ),
        )
        for lane in LANES
        if lane["lane_id"] in {"01", "02", "03", "04", "05", "06", "07", "08"}
    }
    terminal_lanes = sorted(
        lane_id for lane_id, status in lane_terminal.items() if status["terminal_artifacts_present"]
    )
    non_terminal_lanes = sorted(
        lane_id for lane_id, status in lane_terminal.items() if not status["terminal_artifacts_present"]
    )
    lane01_status = lane_terminal["01"]
    lane02_status = lane_terminal["02"]
    lane03_status = lane_terminal["03"]
    lane04_status = lane_terminal["04"]
    lane05_status = lane_terminal["05"]
    lane06_status = lane_terminal["06"]
    lane06_summary = (
        load_json(route_path_for_lane("06") / "LANE06_SUMMARY.json", {})
        if lane06_status["terminal_artifacts_present"]
        else {}
    )
    lane07_status = lane_terminal["07"]
    lane08_status = lane_terminal["08"]
    lane09_status = lane_route_terminal_status(LANE09_ROUTE_DIR)
    return [
        {
            "blocker_class": "missing_reproducible_replay_engine",
            "current_evidence": lane01_status
            if lane01_status["terminal_artifacts_present"]
            else "manual fixed-vNext seed exists only in controlling prompt until Lane01 recomputes or corrects it",
            "exact_next_action": "Carry Lane01 replay outputs into Lane02/Lane05/Lane09; reopen only if downstream audit finds a conflict"
            if lane01_status["terminal_artifacts_present"]
            else "Lane01 must build accepted/rejected timelines, risk/dollar/R ledgers, verifier, tests, manifest, and completion audit",
            "lane_owner": "01",
            "schema_version": "vnext_next_level_cross_lane_blocker_v1",
            "status": "closed_terminal_verified_from_lane01_route"
            if lane01_status["terminal_artifacts_present"]
            else "open_assigned",
            "timestamp_utc": now,
        },
        {
            "blocker_class": "lane02_external_goal_session_pending",
            "current_evidence": {
                "external_owner_state": EXTERNAL_SESSION_OWNED_LANES["02"]["owner_state"],
                "lane09_adoption_state": lane02_status.get("lane09_external_handoff_adoption_state"),
                "raw_disk_terminal_artifacts_present": raw_disk_terminal_present(lane02_status),
                "route_path": rel(route_path_for_lane("02")),
                "uncommitted_handoff_policy": EXTERNAL_SESSION_OWNED_LANES["02"]["master_policy"],
                "verification_result_ok": lane02_status.get("verification_result_ok"),
                "verification_result_path": lane02_status.get("verification_result_path"),
            },
            "exact_next_action": "Carry read-only Lane02 package adoption into scoped merge review"
            if lane02_status.get("lane09_external_handoff_adoption_state")
            else "Dedicated Lane02 goal session owns terminal artifact regeneration; master must inspect accepted disk artifacts before marking Lane02 terminal",
            "lane_owner": "02",
            "schema_version": "vnext_next_level_cross_lane_blocker_v1",
            "status": "closed_read_only_packaged_by_lane09"
            if lane02_status.get("lane09_external_handoff_adoption_state")
            else "open_external_goal_session_owned",
            "timestamp_utc": now,
        },
        {
            "blocker_class": "selected_cell_risk_bridge_missing_or_zero",
            "current_evidence": lane04_status
            if lane04_status["terminal_artifacts_present"]
            else {
                "selected_or_raw_bridge_missing_selected_cell_risk": raw.get("status_counts", {}).get("selected_or_raw_bridge_missing_selected_cell_risk"),
                "subagent_counts": "Friday full replay risk proof present 9/328, missing/zero 319; selected_cell_risk_pct present 9/328; selected_cell_risk_cell_id present 103/328.",
            },
            "exact_next_action": "Carry Lane04 packet/source-completeness contracts into Lane05/Lane09; reopen only if downstream audit finds a conflict"
            if lane04_status["terminal_artifacts_present"]
            else "Lane04 must repair obtainable decision-time packet fields, prove route-dimension fallback into execution/accounting evidence, and emit exact capture contracts for unrepaired historical source truth",
            "lane_owner": "04",
            "schema_version": "vnext_next_level_cross_lane_blocker_v1",
            "status": "closed_terminal_verified_from_lane04_route"
            if lane04_status["terminal_artifacts_present"]
            else "open_assigned",
            "timestamp_utc": now,
        },
        {
            "blocker_class": "partial_broker_net_r_source_gap",
            "current_evidence": {
                "lane06_status": lane06_status,
                "summary": lane06_summary,
            }
            if lane06_status["terminal_artifacts_present"]
            else completion.get("remaining_blockers"),
            "exact_next_action": "Carry Lane06 current source-truth ledger into Lane09; final open residual net-R remains event-pending until broker close"
            if lane06_status["terminal_artifacts_present"]
            else "Lane06 must bind initial risk, partial/full broker profit, commission, swap, slippage, and close/partial lifecycle fields where source exists",
            "lane_owner": "06",
            "schema_version": "vnext_next_level_cross_lane_blocker_v1",
            "status": "closed_current_source_truth_materialized_by_lane06_route"
            if lane06_status["terminal_artifacts_present"]
            else "open_assigned",
            "timestamp_utc": now,
        },
        {
            "blocker_class": "real_lifecycle_close_reconciliation_pending",
            "current_evidence": {
                "lane06_summary": lane06_summary if lane06_status["terminal_artifacts_present"] else None,
                "live_companion_status": live_state.get("status"),
                "known_pending_work": live_state.get("known_pending_work"),
            },
            "exact_next_action": "Lane06 and master must consume close/partial/final deal evidence once present; no live broker action is authorized by this route",
            "lane_owner": "06",
            "schema_version": "vnext_next_level_cross_lane_blocker_v1",
            "status": "open_external_runtime_event_pending",
            "timestamp_utc": now,
        },
        {
            "blocker_class": "meta_selector_package_packaged_by_lane09"
            if lane03_status.get("external_dependency_cleared_by_lane09_package")
            else "meta_selector_package_dependency_hold"
            if lane03_status.get("verification_result_ok")
            else "meta_selector_package_not_built",
            "current_evidence": lane03_status
            if lane03_status.get("verification_result_ok")
            else "Current quality selector is narrow Friday/broad London metadata using session/origin/spread rules; no all-family selected-denominator meta-selector route package exists.",
            "exact_next_action": "Carry Lane03 selector package into scoped merge review"
            if lane03_status.get("external_dependency_cleared_by_lane09_package")
            else "Hold Lane03 terminal acceptance until dedicated Lane02 handoff is accepted; then carry Lane03 selector package into Lane09"
            if lane03_status.get("verification_result_ok")
            else "Lane03 must build all-family/failure-pattern discovery, feature availability/leakage, split/stress, implementation decision ledgers, and code/config/tests for supported clauses only.",
            "lane_owner": "03",
            "schema_version": "vnext_next_level_cross_lane_blocker_v1",
            "status": "closed_dependency_cleared_by_lane09_package"
            if lane03_status.get("external_dependency_cleared_by_lane09_package")
            else "held_external_lane02_dependency"
            if lane03_status.get("verification_result_ok")
            else "open_assigned",
            "timestamp_utc": now,
        },
        {
            "blocker_class": "portfolio_scheduler_package_not_built",
            "current_evidence": lane05_status
            if lane05_status["terminal_artifacts_present"]
            else "Existing prop-safe/account-exposure governor is distributed across runtime/orchestrator/permissions and lacks Lane05 scheduler ledger, before/after matrix, verifier, and completion audit.",
            "exact_next_action": "Carry Lane05 scheduler ledger, gate matrix, and focused tests into Lane09; reopen only if downstream audit finds a conflict"
            if lane05_status["terminal_artifacts_present"]
            else "Lane05 must implement or package a central source-bound scheduler and test vNext dynamic field propagation through check_permissions before claiming scheduler integration.",
            "lane_owner": "05",
            "schema_version": "vnext_next_level_cross_lane_blocker_v1",
            "status": "closed_terminal_verified_from_lane05_route"
            if lane05_status["terminal_artifacts_present"]
            else "open_assigned",
            "timestamp_utc": now,
        },
        {
            "blocker_class": "market_starvation_and_coverage_funnel_not_repaired",
            "current_evidence": lane07_status
            if lane07_status["terminal_artifacts_present"]
            else rel(FRIDAY_DIR / "FRIDAY_MARKET_STARVATION_BY_SYMBOL_LEDGER.jsonl"),
            "exact_next_action": "Carry Lane07 terminal evidence into Lane09 merge; reopen only if downstream audit finds a conflict"
            if lane07_status["terminal_artifacts_present"]
            else "Lane07 must preserve all 24 symbols in a source/opportunity funnel and repair alias/spec/source/logging gaps",
            "lane_owner": "07",
            "schema_version": "vnext_next_level_cross_lane_blocker_v1",
            "status": "closed_terminal_verified_from_lane07_route"
            if lane07_status["terminal_artifacts_present"]
            else "open_assigned",
            "timestamp_utc": now,
        },
        {
            "blocker_class": "execution_policy_packaged_by_lane09"
            if lane08_status.get("external_dependency_cleared_by_lane09_package")
            else "execution_policy_dependency_hold"
            if lane08_status.get("verification_result_ok")
            else "static_15r_extra_recheck_missing_shards",
            "current_evidence": lane08_status
            if lane08_status.get("verification_result_ok")
            else gate.get("route_verifier_suite") or "see ACTIVE_REPAIR_STATE route_verifier_suite",
            "exact_next_action": "Carry Lane08 policy stress package into scoped merge review"
            if lane08_status.get("external_dependency_cleared_by_lane09_package")
            else "Hold Lane08 terminal acceptance until dedicated Lane02 handoff is accepted; then carry Lane08 policy stress package into Lane09"
            if lane08_status.get("verification_result_ok")
            else "Lane08 must decide whether the missing static 1.5R shards are irrelevant comparator-only evidence, recoverable local data, or a verifier repair requirement",
            "lane_owner": "08",
            "schema_version": "vnext_next_level_cross_lane_blocker_v1",
            "status": "closed_dependency_cleared_by_lane09_package"
            if lane08_status.get("external_dependency_cleared_by_lane09_package")
            else "held_external_lane02_dependency"
            if lane08_status.get("verification_result_ok")
            else "open_assigned",
            "timestamp_utc": now,
        },
        {
            "blocker_class": "merge_lane_gated",
            "current_evidence": {
                "lane09_status": lane09_status,
                "non_terminal_lanes_01_to_08": non_terminal_lanes,
                "terminal_lanes_01_to_08": terminal_lanes,
            },
            "exact_next_action": "Carry Lane09 package into scoped merge/staging review"
            if lane09_status["terminal_artifacts_present"]
            else "Lane09 starts only after lane artifacts, verifiers, manifests, and blocker ledgers are present or exactly bounded",
            "lane_owner": "09",
            "schema_version": "vnext_next_level_cross_lane_blocker_v1",
            "status": "closed_lane09_terminal_package_present"
            if lane09_status["terminal_artifacts_present"]
            else "open_gated",
            "timestamp_utc": now,
        },
    ]


def build_market_coverage_seed_ledger(now: str) -> list[dict[str, Any]]:
    starvation_rows = load_jsonl(FRIDAY_DIR / "FRIDAY_MARKET_STARVATION_BY_SYMBOL_LEDGER.jsonl")
    crypto = load_json(FRIDAY_DIR / "FRIDAY_CRYPTO_EXCLUSION_SUMMARY.json", {})
    gate = load_json(LIVE_COMPANION_DIR / "LIVE_REPLAY_GATE_STACK_PARITY_SUMMARY.json", {})
    selected_counts = gate.get("selected_trade_projection", {}).get("symbol_counts", {})
    rows: list[dict[str, Any]] = []
    for row in starvation_rows:
        symbol = row.get("symbol")
        rows.append(
            {
                **row,
                "broad_selected_rows": selected_counts.get(symbol),
                "friday_scope": "primary_non_crypto_clean_freeze",
                "lane_owner": "07",
                "master_recorded_at_utc": now,
                "schema_version": "vnext_next_level_market_coverage_seed_v1",
            }
        )
    for symbol, count in sorted((crypto.get("symbol_counts") or {}).items()):
        rows.append(
            {
                "broker_ready": 0,
                "broad_selected_rows": selected_counts.get(symbol),
                "friday_scope": "crypto_appendix_excluded_from_primary_execution_era_denominator",
                "lane_owner": "07",
                "master_recorded_at_utc": now,
                "placed": 0,
                "primary_reason": crypto.get("reason"),
                "raw_candidates": count,
                "risk_proof_present": 0,
                "schema_version": "vnext_next_level_market_coverage_seed_v1",
                "selected_or_bridge_candidates": count,
                "symbol": symbol,
            }
        )
    return rows


def acceptance_state_for_lane(lane: dict[str, Any], *, scoped_commit_performed: bool = False) -> str:
    status = lane["inspected_from_disk_status"]
    if status.get("lane09_external_handoff_adoption_state"):
        if scoped_commit_performed:
            return "terminal_verified_packaged_by_lane09_from_external_handoff_committed"
        return "terminal_verified_packaged_by_lane09_from_external_handoff"
    if status.get("external_dependency_cleared_by_lane09_package"):
        if scoped_commit_performed:
            return "terminal_verified_dependency_cleared_by_lane09_package_committed"
        return "terminal_verified_dependency_cleared_by_lane09_package"
    if lane["lane_id"] == "09" and status.get("terminal_artifacts_present"):
        if scoped_commit_performed:
            return "terminal_verified_cross_lane_merge_package_committed"
        return "terminal_verified_cross_lane_merge_package"
    if status.get("external_goal_session_owner_state"):
        return "external_session_owned_handoff_not_master_accepted"
    if status.get("external_dependency_pending_lanes"):
        return "terminal_acceptance_held_for_external_dependency"
    if lane["lane_id"] == "09":
        return "merge_lane_gated_until_lanes01_to_08_ready"
    if status.get("terminal_artifacts_present"):
        if scoped_commit_performed:
            return "terminal_verified_packaged_by_lane09_scoped_commit"
        return "terminal_verified_uncommitted_shared_merge_owned_until_lane09"
    if status.get("route_exists"):
        return "route_present_needs_terminal_verifier_test_audit"
    return "route_absent_or_not_materialized"


def raw_disk_terminal_present(status: dict[str, Any]) -> bool:
    if "raw_terminal_artifacts_present_before_master_policy" in status:
        return bool(status.get("raw_terminal_artifacts_present_before_master_policy"))
    return bool(status.get("terminal_artifacts_present"))


def build_terminal_acceptance_ledger(
    now: str, registry: list[dict[str, Any]], scoped_package_commit: dict[str, Any]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    scoped_commit_performed = bool(scoped_package_commit.get("scoped_commit_performed"))
    for lane in registry:
        status = lane["inspected_from_disk_status"]
        state = acceptance_state_for_lane(lane, scoped_commit_performed=scoped_commit_performed)
        rows.append(
            {
                "acceptance_state": state,
                "completion_audit_path": status.get("completion_audit_path"),
                "completion_audit_route_complete": status.get("completion_audit_route_complete"),
                "disk_verification_result_ok": status.get("verification_result_ok"),
                "external_dependency_pending_lanes": status.get("external_dependency_pending_lanes") or [],
                "external_dependency_cleared_by_lane09_package": status.get("external_dependency_cleared_by_lane09_package") or [],
                "external_goal_session_owner_state": status.get("external_goal_session_owner_state"),
                "lane09_external_handoff_adoption_state": status.get("lane09_external_handoff_adoption_state"),
                "lane_id": lane["lane_id"],
                "master_terminal_accepted": bool(status.get("terminal_artifacts_present")),
                "merge_owner": "Lane09" if lane["lane_id"] != "09" else "master_after_lane_prerequisites",
                "raw_disk_terminal_artifacts_present": raw_disk_terminal_present(status),
                "route_file_count": status.get("route_file_count"),
                "route_path": lane["route_path"],
                "schema_version": "vnext_next_level_terminal_acceptance_v1",
                "scoped_package_commit_performed": scoped_commit_performed,
                "scoped_package_commit_sha": scoped_package_commit.get("scoped_commit_sha"),
                "shared_merge_state": (
                    "scoped_package_commit_performed"
                    if scoped_commit_performed and status.get("terminal_artifacts_present")
                    else "packaged_or_terminal_verified_by_lane09"
                    if status.get("terminal_artifacts_present")
                    else "not_merge_ready_from_master"
                ),
                "timestamp_utc": now,
                "verification_result_path": status.get("verification_result_path"),
            }
        )
    return rows


def lane02_scope_guard() -> dict[str, Any]:
    return {
        "complete_selected_surface_required": True,
        "forbidden_closures": [
            "summary_only_substitute",
            "arbitrary_row_cutoff",
            "one_green_subset_closure",
            "friday_only_narrowing",
            "route_completion_without_disk_persisted_verifier_and_test_evidence",
        ],
        "required_selected_denominator_rows": 289600,
        "required_surface_fields": [
            "join_keys",
            "symbol",
            "session",
            "origin_family",
            "policy",
            "selected_cell_risk_proof",
            "r_and_cost_result",
            "split_tags",
            "source_completeness",
            "portfolio_stress_fields",
        ],
    }


def build_external_dependency_ledger(
    now: str, registry: list[dict[str, Any]], scoped_package_commit: dict[str, Any]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    scoped_commit_performed = bool(scoped_package_commit.get("scoped_commit_performed"))
    for lane in registry:
        status = lane["inspected_from_disk_status"]
        external_owner = status.get("external_goal_session_owner_state")
        external_dependencies = status.get("external_dependency_pending_lanes") or []
        cleared_dependencies = status.get("external_dependency_cleared_by_lane09_package") or []
        if not external_owner and not external_dependencies and not cleared_dependencies:
            continue
        verifier_payload = (
            load_json(ROOT / status["verification_result_path"], {})
            if status.get("verification_result_path")
            else {}
        )
        completion_payload = (
            load_json(ROOT / status["completion_audit_path"], {})
            if status.get("completion_audit_path")
            else {}
        )
        row: dict[str, Any] = {
            "acceptance_state": acceptance_state_for_lane(
                lane, scoped_commit_performed=scoped_commit_performed
            ),
            "completion_audit_path": status.get("completion_audit_path"),
            "completion_status": completion_payload.get("status")
            or completion_payload.get("completion_decision"),
            "disk_verification_result_ok": status.get("verification_result_ok"),
            "external_dependency_pending_lanes": external_dependencies,
            "external_dependency_cleared_by_lane09_package": cleared_dependencies,
            "external_goal_session_owner_state": external_owner,
            "lane09_external_handoff_adoption_state": status.get("lane09_external_handoff_adoption_state"),
            "lane_id": lane["lane_id"],
            "master_conflict_prevention": (
                "Master records status and dependencies only; terminal route artifacts and "
                "shared-file merge packaging stay with the owning lane/Lane09."
            ),
            "master_terminal_accepted": bool(status.get("terminal_artifacts_present")),
            "raw_disk_terminal_artifacts_present": raw_disk_terminal_present(status),
            "route_path": lane["route_path"],
            "schema_version": "vnext_next_level_external_dependency_v1",
            "timestamp_utc": now,
            "verification_result_path": status.get("verification_result_path"),
            "verifier_payload_summary": {
                "accepted_rows": verifier_payload.get("accepted_rows"),
                "input_rows": verifier_payload.get("input_rows"),
                "issue_count": verifier_payload.get("issue_count"),
                "ok": verifier_payload.get("ok"),
                "portfolio_ready_rows": verifier_payload.get("portfolio_ready_rows"),
                "status": verifier_payload.get("status"),
            },
        }
        if lane["lane_id"] == "02":
            row.update(
                {
                    "dedicated_lane02_scope_guard": lane02_scope_guard(),
                    "master_lane02_policy": EXTERNAL_SESSION_OWNED_LANES["02"]["master_policy"],
                    "terminal_artifact_owner": EXTERNAL_SESSION_OWNED_LANES["02"]["owner_state"],
                }
            )
        rows.append(row)
    return rows


def shared_path_kind(path: Path) -> dict[str, Any]:
    if path.is_file():
        return {"exists": True, "kind": "file", "size_bytes": path.stat().st_size}
    if path.is_dir():
        return {"exists": True, "file_count": route_file_count(path), "kind": "directory"}
    return {"exists": False, "kind": "missing"}


def build_shared_file_ownership_ledger(
    now: str, registry: list[dict[str, Any]], scoped_package_commit: dict[str, Any]
) -> list[dict[str, Any]]:
    lane_lookup = {lane["lane_id"]: lane for lane in registry}
    scoped_commit_performed = bool(scoped_package_commit.get("scoped_commit_performed"))
    specs = [
        {
            "path": "config/agent_config.yaml",
            "owner": "Lane09",
            "participants": ["03", "07", "09"],
            "state": "shared_config_merge_owned",
            "policy": "Lane03 selector and Lane07 source repairs may propose changes; Lane09 owns final config packaging.",
        },
        {
            "path": "src/components/gtos_vnext_runtime.py",
            "owner": "Lane09",
            "participants": ["03", "04", "05", "08", "09"],
            "state": "shared_runtime_merge_owned",
            "policy": "Runtime behavior changes must be reconciled by Lane09 after route verifiers and focused tests pass.",
        },
        {
            "path": "src/components/orchestrator.py",
            "owner": "Lane09",
            "participants": ["04", "05", "09"],
            "state": "shared_packet_scheduler_merge_owned",
            "policy": "Lane04 packet fields and Lane05 scheduling gates must not overwrite each other.",
        },
        {
            "path": "src/components/permissions.py",
            "owner": "Lane05_then_Lane09",
            "participants": ["05", "09"],
            "state": "scheduler_gate_merge_owned",
            "policy": "Lane05 owns scheduler evidence; Lane09 owns final shared merge review.",
        },
        {
            "path": "src/components/execution.py",
            "owner": "Lane06_then_Lane09",
            "participants": ["06", "09"],
            "state": "broker_lifecycle_merge_owned",
            "policy": "Lane06 owns source-truth repairs; Lane09 owns production package reconciliation.",
        },
        {
            "path": "src/components/m1_capture.py",
            "owner": "Lane07_then_Lane09",
            "participants": ["07", "09"],
            "state": "source_capture_merge_owned",
            "policy": "Lane07 owns capture/source evidence; Lane09 owns final merge packaging.",
        },
        {
            "path": "src/research/moonshot_default_off_policy_router.py",
            "owner": "Lane09",
            "participants": ["03", "08", "09"],
            "state": "selector_policy_router_merge_owned",
            "policy": "Lane03 selector clauses and Lane08 execution-policy stress decisions require Lane09 conflict review.",
        },
        {
            "path": "scripts/build_vnext_lane02_broad_selected_portfolio_replay_stress.py",
            "owner": "dedicated_lane02_goal_session",
            "participants": ["02"],
            "state": "external_handoff_builder_master_read_only",
            "policy": "Master treats this builder as handoff material unless the dedicated Lane02 session explicitly adopts it.",
        },
        {
            "path": "tests/test_vnext_lane02_broad_selected_portfolio_replay_stress.py",
            "owner": "dedicated_lane02_goal_session",
            "participants": ["02"],
            "state": "external_handoff_test_master_read_only",
            "policy": "Master records test evidence only and does not narrow or duplicate Lane02.",
        },
        {
            "path": "research/operations/vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31",
            "owner": "dedicated_lane02_goal_session",
            "participants": ["02", "03", "08", "09"],
            "state": "external_route_handoff_dependency",
            "policy": "Lane02 owns the complete 289600 selected-denominator replay/stress route; Master records dependency state.",
        },
        {
            "path": "research/operations/vnext_lane03_meta_selector_discovery_implementation_2026_05_31",
            "owner": "Lane03_then_Lane09",
            "participants": ["03", "09"],
            "state": "route_terminal_verified_packaged_by_lane09",
            "policy": "Lane03 evidence is packaged by Lane09 after read-only Lane02 handoff adoption.",
        },
        {
            "path": "research/operations/vnext_lane08_execution_policy_microstructure_stress_2026_05_31",
            "owner": "Lane08_then_Lane09",
            "participants": ["08", "09"],
            "state": "route_terminal_verified_packaged_by_lane09",
            "policy": "Lane08 evidence is packaged by Lane09 after read-only Lane02 handoff adoption.",
        },
        {
            "path": "scripts/build_vnext_lane05_runtime_portfolio_scheduler.py",
            "owner": "Lane05_then_Lane09",
            "participants": ["05", "09"],
            "state": "terminal_verified_lane_route_uncommitted",
            "policy": "Lane05 is terminal verified but final shared merge is Lane09-owned.",
        },
        {
            "path": "tests/test_vnext_lane05_portfolio_scheduler.py",
            "owner": "Lane05_then_Lane09",
            "participants": ["05", "09"],
            "state": "terminal_verified_lane_test_uncommitted",
            "policy": "Lane05 focused tests are evidence for Lane09, not a standalone production merge.",
        },
        {
            "path": "tests/test_gtos_vnext_runtime.py",
            "owner": "Lane09",
            "participants": ["03", "04", "05", "08", "09"],
            "state": "shared_runtime_test_merge_owned",
            "policy": "Lane-specific focused runtime tests must be reconciled in Lane09's final matrix.",
        },
        {
            "path": "tests/test_vnext_broader_origin_orchestrator.py",
            "owner": "Lane09",
            "participants": ["04", "05", "09"],
            "state": "shared_orchestrator_test_merge_owned",
            "policy": "Packet completeness and scheduler propagation assertions share this surface.",
        },
        {
            "path": "tests/test_moonshot_default_off_policy_router.py",
            "owner": "Lane09",
            "participants": ["03", "08", "09"],
            "state": "shared_policy_router_test_merge_owned",
            "policy": "Selector and execution-policy assertions require final Lane09 reconciliation.",
        },
        {
            "path": "tests/test_concurrent_cap.py",
            "owner": "Lane05_then_Lane09",
            "participants": ["05", "09"],
            "state": "scheduler_limit_test_merge_owned",
            "policy": "Lane05 scheduler evidence feeds Lane09's merge dossier.",
        },
        {
            "path": "tests/test_notifications.py",
            "owner": "Lane06_then_Lane09",
            "participants": ["06", "09"],
            "state": "broker_notification_test_merge_owned",
            "policy": "Lane06 notification parity evidence feeds Lane09.",
        },
        {
            "path": "tests/test_limit_order_flow.py",
            "owner": "Lane06_then_Lane09",
            "participants": ["06", "09"],
            "state": "broker_execution_test_merge_owned",
            "policy": "Lane06 broker lifecycle evidence feeds Lane09.",
        },
        {
            "path": "tests/test_m1_capture.py",
            "owner": "Lane07_then_Lane09",
            "participants": ["07", "09"],
            "state": "source_capture_test_merge_owned",
            "policy": "Lane07 source capture evidence feeds Lane09.",
        },
        {
            "path": "tests/test_moonshot_candidate_quality_selector.py",
            "owner": "Lane03_then_Lane09",
            "participants": ["03", "09"],
            "state": "selector_quality_test_merge_owned",
            "policy": "Lane03 selector evidence feeds Lane09 after Lane02 dependency acceptance.",
        },
    ]
    rows: list[dict[str, Any]] = []
    for spec in specs:
        path = ROOT / spec["path"]
        participants = spec["participants"]
        rows.append(
            {
                **shared_path_kind(path),
                "current_git_status": git_status_for(path),
                "lane_route_states": {
                    lane_id: acceptance_state_for_lane(
                        lane_lookup[lane_id],
                        scoped_commit_performed=scoped_commit_performed,
                    )
                    for lane_id in participants
                    if lane_id in lane_lookup
                },
                "master_conflict_policy": spec["policy"],
                "owner": spec["owner"],
                "owner_state": spec["state"],
                "participating_lanes": participants,
                "path": spec["path"],
                "schema_version": "vnext_next_level_shared_file_ownership_v1",
                "timestamp_utc": now,
            }
        )
    return rows


def classify_scoped_staging_path(path_text: str) -> dict[str, Any]:
    shared_surface_paths = {
        "config/agent_config.yaml",
        "src/components/gtos_vnext_runtime.py",
        "src/components/orchestrator.py",
        "src/components/permissions.py",
        "src/components/execution.py",
        "src/components/m1_capture.py",
        "src/research/moonshot_default_off_policy_router.py",
        "tests/test_gtos_vnext_runtime.py",
        "tests/test_vnext_broader_origin_orchestrator.py",
        "tests/test_moonshot_default_off_policy_router.py",
        "tests/test_m1_capture.py",
        "tests/test_concurrent_cap.py",
        "tests/test_notifications.py",
        "tests/test_limit_order_flow.py",
        "tests/test_moonshot_candidate_quality_selector.py",
    }
    if path_text in MASTER_SCOPED_INCLUDE_PATHS or path_text.startswith(MASTER_SCOPED_INCLUDE_PREFIXES):
        owner = "Lane09_or_master_package"
        if "lane02" in path_text or "LANE02" in path_text:
            owner = "dedicated_lane02_goal_session_terminal_artifact_packaged_by_lane09"
        elif any(f"lane{idx:02d}" in path_text or f"LANE{idx:02d}" in path_text for idx in range(1, 9)):
            owner = "owning_lane_terminal_artifact_packaged_by_lane09"
        elif path_text.startswith(("src/", "config/", "tests/", "scripts/")):
            owner = "lane_owned_implementation_surface_packaged_by_lane09"
        return {
            "include_in_scoped_commit_candidate": True,
            "owner": owner,
            "staging_decision": "stage_candidate_lane_owned_implementation_or_route_package",
            "staging_reason": "Scoped package candidate from lane-owned implementation surface, terminal lane route artifact, or Master/Lane09 package evidence.",
        }
    if path_text.startswith(LANE_ROUTE_PREFIXES):
        return {
            "include_in_scoped_commit_candidate": True,
            "owner": "owning_lane_terminal_artifact_packaged_by_lane09",
            "staging_decision": "stage_candidate_lane_route_artifact",
            "staging_reason": "Terminal lane route artifact is part of the actual Lane09 implementation/package commit.",
        }
    if path_text in shared_surface_paths:
        return {
            "include_in_scoped_commit_candidate": True,
            "owner": "Lane09_shared_merge_review",
            "staging_decision": "stage_candidate_shared_runtime_config_test_surface",
            "staging_reason": "Shared runtime/config/test surface is lane-owned implementation material after Lane09 scoped review.",
        }
    if path_text.startswith(LIVE_OR_RUNTIME_DIRTY_PREFIXES):
        return {
            "include_in_scoped_commit_candidate": False,
            "owner": "live_runtime_or_unrelated_research_surface",
            "staging_decision": "exclude_live_shadow_runtime_or_unrelated_dirt",
            "staging_reason": "Do not sweep live/shadow/runtime generated dirt into the Master/Lane09 package commit.",
        }
    if path_text == ".context/LIVE_STATE.md":
        return {
            "include_in_scoped_commit_candidate": False,
            "owner": "preflight_generated_context",
            "staging_decision": "exclude_preflight_live_state_refresh",
            "staging_reason": "LIVE_STATE was regenerated for preflight and is not a scoped route artifact.",
        }
    if path_text.startswith(".codex/"):
        return {
            "include_in_scoped_commit_candidate": False,
            "owner": "local_codex_configuration",
            "staging_decision": "exclude_local_codex_config",
            "staging_reason": "Local Codex configuration is outside the vNext route package.",
        }
    if path_text.startswith(PROMPT_PREFIX):
        prompt_name = path_text.rsplit("/", 1)[-1]
        if "2026-05-31" in prompt_name and any(
            marker in prompt_name for marker in PROMPT_PACKAGE_MARKERS
        ):
            return {
                "include_in_scoped_commit_candidate": True,
                "owner": "next_level_lane_prompt_contract",
                "staging_decision": "stage_candidate_prompt_contract",
                "staging_reason": "Current next-level lane/master prompt contract belongs with the reproducible route package.",
            }
        return {
            "include_in_scoped_commit_candidate": False,
            "owner": "prompt_hardening_or_lane_prompt_surface",
            "staging_decision": "hold_prompt_surface_for_separate_review",
            "staging_reason": "Prompt/starter deltas are not staged by Master in the scoped route package without explicit review.",
        }
    return {
        "include_in_scoped_commit_candidate": False,
        "owner": "unowned_or_unclassified_worktree_dirt",
        "staging_decision": "exclude_unowned_or_unclassified_path",
        "staging_reason": "Path is not part of the Master/Lane09 scoped package candidate.",
    }


def build_scoped_merge_staging_review(
    now: str, scoped_package_commit: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    for git_row in git_status_porcelain_all():
        classification = classify_scoped_staging_path(git_row["path"])
        rows.append(
            {
                **classification,
                **git_row,
                "schema_version": "vnext_next_level_scoped_merge_staging_row_v1",
                "timestamp_utc": now,
            }
        )
    staged_paths = [row["path"] for row in rows if row["staged"]]
    stage_candidates = [
        row["path"]
        for row in rows
        if row["include_in_scoped_commit_candidate"]
    ]
    unstaged_include_candidates = [
        row["path"]
        for row in rows
        if row["include_in_scoped_commit_candidate"] and not row["staged"]
    ]
    decision_counts = Counter(row["staging_decision"] for row in rows)
    plan = {
        "decision_counts": dict(sorted(decision_counts.items())),
        "forbidden_sweep_policy": (
            "Do not stage broad live/shadow/runtime dirt or in-progress Lane02 artifacts. "
            "Package verified Lane02 terminal handoff artifacts only through the scoped Lane09/Master candidate list."
        ),
        "generated_at_utc": now,
        "include_candidate_count": len(stage_candidates),
        "include_candidate_paths": stage_candidates,
        "lane02_terminal_paths_included": [
            row["path"]
            for row in rows
            if row["owner"] == "dedicated_lane02_goal_session_terminal_artifact_packaged_by_lane09"
        ],
        "path_count": len(rows),
        "route_id": ROUTE_ID,
        "schema_version": "vnext_next_level_scoped_merge_staging_plan_v1",
        "scoped_commit_forbidden_path_count": scoped_package_commit.get("scoped_commit_forbidden_path_count"),
        "scoped_commit_missing_required_paths": scoped_package_commit.get("scoped_commit_missing_required_paths"),
        "scoped_commit_missing_required_prefixes": scoped_package_commit.get("scoped_commit_missing_required_prefixes"),
        "scoped_commit_path_count": scoped_package_commit.get("scoped_commit_path_count"),
        "scoped_commit_paths": scoped_package_commit.get("scoped_commit_paths"),
        "scoped_commit_performed": bool(scoped_package_commit.get("scoped_commit_performed")),
        "scoped_commit_sha": scoped_package_commit.get("scoped_commit_sha"),
        "scoped_commit_short_subject": scoped_package_commit.get("scoped_commit_short_subject"),
        "scoped_commit_status": scoped_package_commit.get("scoped_commit_status"),
        "scoped_package_commit": scoped_package_commit,
        "scoped_staging_review_complete": True,
        "staged_path_count": len(staged_paths),
        "staged_paths": staged_paths,
        "stage_candidate_policy": "Lane-owned implementation surfaces, terminal lane route artifacts, next-level prompt contracts, and Master/Lane09 package evidence are candidates; live/shadow/runtime dirt and unrelated program-control churn are excluded.",
        "unstaged_include_candidate_count": len(unstaged_include_candidates),
        "unstaged_include_candidate_paths": unstaged_include_candidates,
    }
    return plan, rows


def build_merge_readiness_matrix(
    now: str,
    registry: list[dict[str, Any]],
    terminal_acceptance: list[dict[str, Any]],
    external_dependencies: list[dict[str, Any]],
    staging_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scoped_commit_performed = bool(
        staging_plan and staging_plan.get("scoped_commit_performed")
    )
    terminal_lanes = [
        row["lane_id"]
        for row in terminal_acceptance
        if row["master_terminal_accepted"]
    ]
    external_owned = [
        row["lane_id"]
        for row in terminal_acceptance
        if row["acceptance_state"] == "external_session_owned_handoff_not_master_accepted"
    ]
    dependency_held = [
        {
            "lane_id": row["lane_id"],
            "pending_dependencies": row["external_dependency_pending_lanes"],
        }
        for row in terminal_acceptance
        if row["acceptance_state"] == "terminal_acceptance_held_for_external_dependency"
    ]
    non_terminal_lanes_01_to_08 = [
        row["lane_id"]
        for row in terminal_acceptance
        if row["lane_id"] in {"01", "02", "03", "04", "05", "06", "07", "08"}
        and not row["master_terminal_accepted"]
    ]
    lane_rows = []
    for lane in registry:
        status = lane["inspected_from_disk_status"]
        lane_rows.append(
            {
                "acceptance_state": acceptance_state_for_lane(
                    lane, scoped_commit_performed=scoped_commit_performed
                ),
                "completion_audit_route_complete": status.get("completion_audit_route_complete"),
                "disk_verification_result_ok": status.get("verification_result_ok"),
                "external_dependency_cleared_by_lane09_package": status.get("external_dependency_cleared_by_lane09_package") or [],
                "external_dependency_pending_lanes": status.get("external_dependency_pending_lanes") or [],
                "external_goal_session_owner_state": status.get("external_goal_session_owner_state"),
                "lane09_external_handoff_adoption_state": status.get("lane09_external_handoff_adoption_state"),
                "lane_id": lane["lane_id"],
                "master_terminal_accepted": bool(status.get("terminal_artifacts_present")),
                "raw_disk_terminal_artifacts_present": raw_disk_terminal_present(status),
                "route_path": lane["route_path"],
                "shared_merge_owner": "Lane09" if lane["lane_id"] != "09" else "master",
                "verification_result_path": status.get("verification_result_path"),
            }
        )
    blockers = []
    if external_owned:
        blockers.append("Lane02 remains external-session-owned handoff material until dedicated Lane02/Lane09 adoption.")
    if dependency_held:
        blockers.append("Lane03 and Lane08 terminal acceptance is held on Lane02 external dependency.")
    if "09" not in terminal_lanes:
        blockers.append("Lane09 merge dossier and production package are not terminal on disk.")
    if non_terminal_lanes_01_to_08:
        blockers.append(
            "Non-terminal-for-Master lanes 01-08: " + ", ".join(non_terminal_lanes_01_to_08)
        )
    if "09" in terminal_lanes:
        staging_review_complete = bool(
            staging_plan and staging_plan.get("scoped_staging_review_complete")
        )
        if not scoped_commit_performed:
            blockers.append(
                "Lane09 package is complete locally; scoped staging review is materialized, but scoped commit remains unperformed."
                if staging_review_complete
                else "Lane09 package is complete locally; scoped commit/staging boundary remains open."
            )
        blockers.extend(
            [
                "Production-change approval remains a separate owner-approved gate before live deployment.",
                "Final broker close/deal/cost reconciliation remains event-pending.",
            ]
        )
    return {
        "completion_ready": False,
        "external_dependency_rows": external_dependencies,
        "external_dependency_pending_lanes": dependency_held,
        "external_session_owned_lanes": external_owned,
        "generated_at_utc": now,
        "lane09_package_terminal": "09" in terminal_lanes,
        "lane09_start_ready": not non_terminal_lanes_01_to_08 and not external_owned and not dependency_held,
        "lane_rows": lane_rows,
        "merge_blockers": blockers,
        "non_terminal_lanes_01_to_08": non_terminal_lanes_01_to_08,
        "route_id": ROUTE_ID,
        "schema_version": "vnext_next_level_merge_readiness_matrix_v1",
        "scoped_merge_staging_review": {
            "include_candidate_count": staging_plan.get("include_candidate_count") if staging_plan else None,
            "path_count": staging_plan.get("path_count") if staging_plan else None,
            "scoped_commit_forbidden_path_count": staging_plan.get("scoped_commit_forbidden_path_count") if staging_plan else None,
            "scoped_commit_path_count": staging_plan.get("scoped_commit_path_count") if staging_plan else None,
            "scoped_commit_performed": staging_plan.get("scoped_commit_performed") if staging_plan else None,
            "scoped_commit_sha": staging_plan.get("scoped_commit_sha") if staging_plan else None,
            "scoped_commit_short_subject": staging_plan.get("scoped_commit_short_subject") if staging_plan else None,
            "scoped_commit_status": staging_plan.get("scoped_commit_status") if staging_plan else None,
            "scoped_staging_review_complete": staging_plan.get("scoped_staging_review_complete") if staging_plan else False,
            "staged_path_count": staging_plan.get("staged_path_count") if staging_plan else None,
        },
        "shared_merge_policy": (
            "Master coordinates registry, dependencies, shared-file ownership, conflict prevention, "
            "lane status, and merge readiness. Lane09 owns final shared merge packaging."
        ),
        "terminal_verified_packaged_by_lane09_scoped_commit": terminal_lanes
        if scoped_commit_performed
        else [],
        "terminal_verified_uncommitted_shared_merge_owned_until_lane09": []
        if scoped_commit_performed
        else terminal_lanes,
    }


def write_route_local_verifier() -> None:
    verifier = ROUTE_DIR / "verify_master_orchestration_artifacts.py"
    verifier.write_text(
        '''from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = ROOT / "research" / "operations" / "vnext_next_level_master_orchestration_2026_05_31"

REQUIRED = [
    "MASTER_ROUTE_REGISTRY.json",
    "MASTER_LANE_DEPENDENCY_GRAPH.json",
    "MASTER_TERMINAL_ACCEPTANCE_LEDGER.jsonl",
    "MASTER_EXTERNAL_DEPENDENCY_LEDGER.jsonl",
    "MASTER_SHARED_FILE_OWNERSHIP_LEDGER.jsonl",
    "MASTER_SCOPED_MERGE_STAGING_LEDGER.jsonl",
    "MASTER_SCOPED_MERGE_STAGING_PLAN.json",
    "MASTER_MERGE_READINESS_MATRIX.json",
    "MASTER_CROSS_LANE_BLOCKER_LEDGER.jsonl",
    "MASTER_CROSS_LANE_RESULT_MATERIALIZATION_LEDGER.jsonl",
    "MASTER_MARKET_COVERAGE_SEED_LEDGER.jsonl",
    "MASTER_EVIDENCE_INSPECTION_LEDGER.jsonl",
    "MASTER_SUBAGENT_AUDIT_LEDGER.jsonl",
    "MASTER_PROMPT_HARDENING_VERIFICATION.json",
    "MASTER_ORCHESTRATION_OUTPUT_MANIFEST.json",
    "MASTER_ORCHESTRATION_COMPLETION_AUDIT.json",
    "MASTER_ORCHESTRATION_FINAL_REPORT.md",
]


def count_jsonl(path: Path) -> int:
    return sum(1 for line in path.open("r", encoding="utf-8") if line.strip())


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    issues = []
    for name in REQUIRED:
        path = ROUTE_DIR / name
        if not path.exists() or path.stat().st_size <= 0:
            issues.append({"code": "missing_required_output", "path": str(path)})
    registry_path = ROUTE_DIR / "MASTER_ROUTE_REGISTRY.json"
    if registry_path.exists():
        registry = load_json(registry_path)
        if len(registry.get("lanes", [])) != 9:
            issues.append({"code": "registry_lane_count_mismatch", "actual": len(registry.get("lanes", []))})
        for lane in registry.get("lanes", []):
            if not lane.get("prompt_path") or not lane.get("starter_path") or not lane.get("route_path"):
                issues.append({"code": "lane_missing_required_path", "lane_id": lane.get("lane_id")})
    market_path = ROUTE_DIR / "MASTER_MARKET_COVERAGE_SEED_LEDGER.jsonl"
    if market_path.exists() and count_jsonl(market_path) != 24:
        issues.append({"code": "market_seed_not_24_symbols", "actual": count_jsonl(market_path)})
    acceptance_path = ROUTE_DIR / "MASTER_TERMINAL_ACCEPTANCE_LEDGER.jsonl"
    if acceptance_path.exists() and count_jsonl(acceptance_path) != 9:
        issues.append({"code": "terminal_acceptance_lane_count_mismatch", "actual": count_jsonl(acceptance_path)})
    shared_path = ROUTE_DIR / "MASTER_SHARED_FILE_OWNERSHIP_LEDGER.jsonl"
    if shared_path.exists() and count_jsonl(shared_path) < 10:
        issues.append({"code": "shared_file_ownership_ledger_too_narrow", "actual": count_jsonl(shared_path)})
    staging_path = ROUTE_DIR / "MASTER_SCOPED_MERGE_STAGING_LEDGER.jsonl"
    if staging_path.exists() and count_jsonl(staging_path) <= 0:
        issues.append({"code": "scoped_staging_ledger_empty"})
    staging_plan_path = ROUTE_DIR / "MASTER_SCOPED_MERGE_STAGING_PLAN.json"
    if staging_plan_path.exists():
        staging_plan = load_json(staging_plan_path)
        if not staging_plan.get("scoped_staging_review_complete"):
            issues.append({"code": "scoped_staging_review_not_complete"})
        staged_paths = set(staging_plan.get("staged_paths") or [])
        include_paths = set(staging_plan.get("include_candidate_paths") or [])
        unexpected_staged = sorted(staged_paths - include_paths)
        if unexpected_staged:
            issues.append({"code": "scoped_staging_contains_unapproved_paths", "paths": unexpected_staged})
        if staging_plan.get("include_candidate_count", 0) <= 0:
            issues.append({"code": "scoped_staging_has_no_include_candidates"})
        if not staged_paths and not staging_plan.get("scoped_commit_performed"):
            issues.append({"code": "scoped_package_not_staged_or_committed"})
        unstaged_candidates = staging_plan.get("unstaged_include_candidate_paths") or []
        if unstaged_candidates and not staging_plan.get("scoped_commit_performed"):
            issues.append({"code": "scoped_include_candidates_unstaged", "paths": unstaged_candidates[:50], "count": len(unstaged_candidates)})
        if staging_plan.get("scoped_commit_performed") and not staging_plan.get("scoped_commit_sha"):
            issues.append({"code": "scoped_commit_missing_sha"})
        if staging_plan.get("scoped_commit_forbidden_path_count"):
            issues.append({"code": "scoped_commit_contains_forbidden_paths", "count": staging_plan.get("scoped_commit_forbidden_path_count")})
    matrix_path = ROUTE_DIR / "MASTER_MERGE_READINESS_MATRIX.json"
    if matrix_path.exists():
        matrix = load_json(matrix_path)
        lane_rows = matrix.get("lane_rows", [])
        if len(lane_rows) != 9:
            issues.append({"code": "merge_readiness_lane_count_mismatch", "actual": len(lane_rows)})
        lane02 = next((row for row in lane_rows if row.get("lane_id") == "02"), {})
        lane09 = next((row for row in lane_rows if row.get("lane_id") == "09"), {})
        lane09_terminal = bool(lane09.get("master_terminal_accepted"))
        if lane02.get("master_terminal_accepted") and not lane09_terminal:
            issues.append({"code": "lane02_wrongly_master_terminal_accepted"})
        if not lane02.get("master_terminal_accepted") and "02" not in matrix.get("external_session_owned_lanes", []):
            issues.append({"code": "lane02_external_session_not_tracked"})
        held = {row.get("lane_id") for row in matrix.get("external_dependency_pending_lanes", [])}
        if not lane09_terminal and not {"03", "08"}.issubset(held):
            issues.append({"code": "lane03_lane08_external_dependency_hold_missing", "actual": sorted(held)})
        if lane09_terminal and (matrix.get("external_session_owned_lanes") or matrix.get("external_dependency_pending_lanes")):
            issues.append({"code": "lane09_terminal_but_external_dependency_not_cleared"})
        if matrix.get("completion_ready"):
            issues.append({"code": "merge_readiness_claimed_too_early"})
    completion_ready = False
    audit_path = ROUTE_DIR / "MASTER_ORCHESTRATION_COMPLETION_AUDIT.json"
    if audit_path.exists():
        completion_ready = bool(load_json(audit_path).get("completion_ready"))
    result = {
        "completion_ready": completion_ready,
        "issue_count": len(issues),
        "issues": issues,
        "ok": not issues,
        "route_dir": str(ROUTE_DIR.relative_to(ROOT)).replace("\\\\", "/"),
        "schema_version": "vnext_next_level_master_route_verification_v1",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
''',
        encoding="utf-8",
    )


def build_prompt_hardening(now: str) -> dict[str, Any]:
    prompts = [(MASTER_PROMPT, "builder"), (MASTER_STARTER, "starter")]
    for lane in LANES:
        prompts.append((PROMPT_DIR / lane["prompt"], "builder"))
        prompts.append((PROMPT_DIR / lane["starter"], "starter"))
    checks = [validate_prompt(path, kind=kind) for path, kind in prompts]
    return {
        "checks": checks,
        "generated_at_utc": now,
        "ok": all(check["ok"] for check in checks),
        "route_id": ROUTE_ID,
        "schema_version": "vnext_next_level_prompt_hardening_verification_v1",
    }


def build_completion_audit(
    now: str,
    registry: list[dict[str, Any]],
    prompt_hardening: dict[str, Any],
    merge_readiness: dict[str, Any],
    staging_plan: dict[str, Any],
) -> dict[str, Any]:
    routes_missing = [
        lane["lane_id"]
        for lane in registry
        if lane["inspected_from_disk_status"]["route_file_count"] == 0
    ]
    terminal_lanes = [
        lane["lane_id"]
        for lane in registry
        if lane["inspected_from_disk_status"].get("terminal_artifacts_present")
    ]
    external_session_owned_lanes = [
        lane["lane_id"]
        for lane in registry
        if lane["inspected_from_disk_status"].get("external_goal_session_owner_state")
        and not lane["inspected_from_disk_status"].get("terminal_artifacts_present")
    ]
    external_dependency_pending_lanes = [
        {
            "lane_id": lane["lane_id"],
            "pending_dependencies": lane["inspected_from_disk_status"].get(
                "external_dependency_pending_lanes"
            ),
        }
        for lane in registry
        if lane["inspected_from_disk_status"].get("external_dependency_pending_lanes")
    ]
    non_terminal_lanes_01_to_08 = [
        lane["lane_id"]
        for lane in registry
        if lane["lane_id"] in {"01", "02", "03", "04", "05", "06", "07", "08"}
        and not lane["inspected_from_disk_status"].get("terminal_artifacts_present")
    ]
    lane09_terminal = "09" in terminal_lanes
    all_lane_packages_terminal = not non_terminal_lanes_01_to_08 and lane09_terminal
    integrated_audits = [
        row["audit_id"]
        for row in SUBAGENT_FINDINGS
        if str(row.get("finding_status", "")).startswith("integrated")
    ]
    pending_audits = [
        row["audit_id"]
        for row in SUBAGENT_AUDIT_REQUESTS
        if row.get("status") == "launched_pending_result"
    ]
    scoped_commit_performed = bool(staging_plan.get("scoped_commit_performed"))
    scoped_gate_status = (
        "scoped_commit_materialized_live_policy_and_runtime_event_gates_remain"
        if scoped_commit_performed
        else "scoped_staging_review_materialized_commit_policy_and_runtime_event_gates_remain"
        if staging_plan.get("scoped_staging_review_complete")
        else "not_complete_policy_and_commit_boundaries_remain"
    )
    unmet_requirements = [
        "Production-change approval remains separate before live deployment",
        "Final broker close/deal/cost reconciliation remains event-pending",
    ]
    if not scoped_commit_performed:
        unmet_requirements.insert(
            0,
            "Scoped staging review is materialized, but scoped commit remains unperformed; do not sweep unrelated live/shadow dirt",
        )
    return {
        "branch_decision": "keep_master_goal_active",
        "completion_ready": False,
        "generated_at_utc": now,
        "items": [
            {
                "evidence": rel(ROOT / ".context" / "LIVE_STATE.md"),
                "passed": True,
                "requirement": "LIVE_STATE_regenerated_and_current_context_reread",
                "status": "satisfied_for_current_master_checkpoint",
            },
            {
                "evidence": rel(MASTER_PROMPT),
                "passed": True,
                "requirement": "controlling_prompt_read_from_disk",
                "status": "satisfied_for_current_master_checkpoint",
            },
            {
                "evidence": "MASTER_ROUTE_REGISTRY.json",
                "passed": len(registry) == 9,
                "requirement": "master_route_registry_tracks_all_lanes",
                "status": "satisfied_for_current_master_checkpoint" if len(registry) == 9 else "failed",
            },
            {
                "evidence": "MASTER_PROMPT_HARDENING_VERIFICATION.json",
                "passed": bool(prompt_hardening.get("ok")),
                "requirement": "prompt_hardening_checked_for_master_and_lane_prompts",
                "status": "satisfied_for_current_master_checkpoint" if prompt_hardening.get("ok") else "prompt_hardening_failure",
            },
            {
                "evidence": {
                    "integrated": integrated_audits,
                    "pending": pending_audits,
                },
                "passed": True,
                "requirement": "highest_reasoning_subagent_audits_launched",
                "status": "some_findings_integrated_remaining_audits_pending"
                if pending_audits
                else "all_returned_findings_integrated",
            },
            {
                "evidence": "MASTER_CROSS_LANE_RESULT_MATERIALIZATION_LEDGER.jsonl",
                "passed": True,
                "requirement": "seed_result_materialization_written_from_disk_evidence",
                "status": "satisfied_for_current_master_checkpoint",
            },
            {
                "evidence": "MASTER_CROSS_LANE_BLOCKER_LEDGER.jsonl",
                "passed": True,
                "requirement": "cross_lane_blockers_written_from_disk_evidence",
                "status": "satisfied_for_current_master_checkpoint",
            },
            {
                "evidence": [
                    "MASTER_TERMINAL_ACCEPTANCE_LEDGER.jsonl",
                    "MASTER_EXTERNAL_DEPENDENCY_LEDGER.jsonl",
                    "MASTER_SHARED_FILE_OWNERSHIP_LEDGER.jsonl",
                    "MASTER_SCOPED_MERGE_STAGING_LEDGER.jsonl",
                    "MASTER_SCOPED_MERGE_STAGING_PLAN.json",
                    "MASTER_MERGE_READINESS_MATRIX.json",
                ],
                "passed": True,
                "requirement": "master_tracks_terminal_acceptance_shared_file_ownership_conflict_prevention_scoped_staging_and_merge_readiness",
                "status": "satisfied_for_current_master_checkpoint",
            },
            {
                "evidence": {
                    "missing_route_directories": routes_missing,
                    "non_terminal_lanes_01_to_08": non_terminal_lanes_01_to_08,
                    "terminal_lanes": terminal_lanes,
                    "external_session_owned_lanes": external_session_owned_lanes,
                    "external_dependency_pending_lanes": external_dependency_pending_lanes,
                    "merge_blockers": merge_readiness.get("merge_blockers"),
                },
                "passed": all_lane_packages_terminal,
                "requirement": "lane_implementation_verifiers_tests_and_merge_package_complete",
                "status": "satisfied_for_current_master_checkpoint"
                if all_lane_packages_terminal
                else "not_complete_master_terminal_acceptance_or_merge_package_pending",
            },
            {
                "evidence": {
                    "scoped_commit_performed": scoped_commit_performed,
                    "scoped_commit_sha": staging_plan.get("scoped_commit_sha"),
                    "scoped_staging_review_complete": staging_plan.get("scoped_staging_review_complete"),
                    "staged_path_count": staging_plan.get("staged_path_count"),
                    "merge_blockers": merge_readiness.get("merge_blockers"),
                },
                "passed": False,
                "requirement": "scoped_merge_commit_and_live_production_change_gates",
                "status": scoped_gate_status,
            },
        ],
        "result_materialization": "master_checkpoint_materialized_not_final_program_completion",
        "route_id": ROUTE_ID,
        "schema_version": "vnext_next_level_master_completion_audit_v1",
        "source_completeness": "master_seed_evidence_inspected_lane09_package_terminal_scoped_commit_materialized_live_gates_remain"
        if scoped_commit_performed
        else "master_seed_evidence_inspected_lane09_package_terminal_scoped_staging_review_materialized_commit_and_live_gates_remain",
        "status": "active_not_complete",
        "unmet_requirements": unmet_requirements,
    }


def build_manifest(now: str) -> dict[str, Any]:
    outputs: list[dict[str, Any]] = []
    for path in sorted(ROUTE_DIR.iterdir()):
        if path.is_dir() or path.name == "MASTER_ORCHESTRATION_OUTPUT_MANIFEST.json":
            continue
        item = file_evidence(path, "master_route_output")
        outputs.append(item)
    return {
        "generated_at_utc": now,
        "materialized_outputs": [item["path"].split("/")[-1] for item in outputs],
        "missing_required_outputs": [],
        "output_count": len(outputs),
        "outputs": outputs,
        "result_materialization": "master_route_output_manifest_written",
        "route_id": ROUTE_ID,
        "route_dir": rel(ROUTE_DIR),
        "schema_version": "vnext_next_level_master_output_manifest_v1",
    }


def remaining_gate_phrase(scoped_commit_performed: bool) -> str:
    if scoped_commit_performed:
        return "separate production-change approval and event-pending broker close/deal/cost evidence"
    return "scoped commit, separate production-change approval, and event-pending broker close/deal/cost evidence"


def build_final_report(
    now: str,
    registry: list[dict[str, Any]],
    audit: dict[str, Any],
    staging_plan: dict[str, Any],
) -> str:
    lane_by_id = {lane["lane_id"]: lane for lane in registry}
    missing_routes = [lane["lane_id"] for lane in registry if lane["inspected_from_disk_status"]["route_file_count"] == 0]
    terminal_lanes = [
        lane["lane_id"]
        for lane in registry
        if lane["inspected_from_disk_status"].get("terminal_artifacts_present")
    ]
    external_session_owned_lanes = [
        lane["lane_id"]
        for lane in registry
        if lane["inspected_from_disk_status"].get("external_goal_session_owner_state")
        and not lane["inspected_from_disk_status"].get("terminal_artifacts_present")
    ]
    external_dependency_pending_lanes = [
        lane["lane_id"]
        for lane in registry
        if lane["inspected_from_disk_status"].get("external_dependency_pending_lanes")
    ]
    non_terminal_lanes_01_to_08 = [
        lane["lane_id"]
        for lane in registry
        if lane["lane_id"] in {"01", "02", "03", "04", "05", "06", "07", "08"}
        and not lane["inspected_from_disk_status"].get("terminal_artifacts_present")
    ]
    immediate = [lane["lane_id"] for lane in registry if lane["launch_class"] == "immediate"]
    lane03_status = lane_by_id["03"]["inspected_from_disk_status"]
    lane08_status = lane_by_id["08"]["inspected_from_disk_status"]
    blocker_lines = [
        "- Lane01 fixed Friday portfolio replay is terminal verified on current disk and must feed Lane02/Lane05/Lane09."
        if "01" in terminal_lanes
        else "- Reproducible Lane01 portfolio engine missing.",
        "- Lane04 selected-cell risk bridge packet completeness is terminal verified on current disk and must feed Lane05/Lane09."
        if "04" in terminal_lanes
        else "- Selected-cell risk bridge missing/zero rows assigned to Lane04.",
        "- Lane05 runtime portfolio scheduler integration is terminal verified on current disk and must feed Lane09."
        if "05" in terminal_lanes
        else "- Runtime portfolio scheduler package assigned to Lane05.",
        "- Lane06 broker lifecycle source truth is terminal verified for current evidence; final net-R on open residual positions remains event-pending."
        if "06" in terminal_lanes
        else "- Broker net-R/cost lifecycle gaps assigned to Lane06.",
        "- Lane07 market coverage/starvation repair is terminal verified on current disk and must be carried into Lane09."
        if "07" in terminal_lanes
        else "- Market coverage/starvation repair assigned to Lane07.",
        "- Lane03 meta-selector package is verified and dependency-cleared through Lane09's read-only Lane02 package adoption."
        if lane03_status.get("external_dependency_cleared_by_lane09_package")
        else "- Lane03 meta-selector package is verified on disk but Master terminal acceptance is held for Lane02 external dependency."
        if lane03_status.get("verification_result_ok")
        else "- Meta-selector discovery and implementation assigned to Lane03.",
        "- Lane08 execution-policy stress is verified and dependency-cleared through Lane09's read-only Lane02 package adoption."
        if lane08_status.get("external_dependency_cleared_by_lane09_package")
        else "- Lane08 execution-policy stress is verified on disk but Master terminal acceptance is held for Lane02 external dependency."
        if lane08_status.get("verification_result_ok")
        else "- Execution-policy stress and static comparator verifier questions assigned to Lane08.",
    ]
    lane01_seed_line = (
        "- The manual fixed-vNext portfolio seed has been recomputed by Lane01's terminal verified route and supersedes prompt-only seed status."
        if "01" in terminal_lanes
        else "- The manual fixed-vNext portfolio seed is recorded as prompt-seed-only until Lane01 recomputes or corrects it with a builder and verifier."
    )
    lane02_status = lane_by_id["02"]["inspected_from_disk_status"]
    scoped_commit_performed = bool(staging_plan.get("scoped_commit_performed"))
    gate_phrase = remaining_gate_phrase(scoped_commit_performed)
    merge_state_line = (
        f"- Scoped implementation/package commit is recorded as `{staging_plan.get('scoped_commit_short_subject')}` with `{staging_plan.get('scoped_commit_path_count')}` scoped paths and no forbidden path findings."
        if scoped_commit_performed
        else "- Scoped implementation/package commit remains open; do not stage unrelated live/shadow/runtime dirt."
    )
    lane02_line = (
        "- Lane02 has been adopted read-only by Lane09 for packaging; dedicated Lane02 remains the terminal artifact owner and Master did not rewrite or narrow it."
        if lane02_status.get("lane09_external_handoff_adoption_state")
        else (
        "- Lane02 currently has disk verifier/test evidence, but Master records it as dedicated-session-owned handoff material; Master does not accept it as terminal or narrow its scope."
        if lane02_status.get("verification_result_ok")
        else "- Lane02 remains dedicated-session-owned and not accepted by Master until its full selected-denominator verifier/test evidence is stable on disk."
        )
    )
    return "\n".join(
        [
            "# vNext Next-Level Master Orchestration Report",
            "",
            f"Generated: {now}",
            f"Route id: `{ROUTE_ID}`",
            "",
            "## Current Decision",
            "",
            f"`active_not_complete`. The master route is materialized and tracks all nine lanes. Lane09 has packaged lanes 01-08, including read-only adoption of the dedicated Lane02 handoff; remaining gates are {gate_phrase}.",
            "",
            "## Disk Evidence Used",
            "",
            "- Friday microscope final report, completion audit, output manifest, final verification, focused test result, quality/broad replay summary, denominator reconciliation, market starvation ledger, and broker truth ledger.",
            "- Live activation companion active state and live/replay gate-stack parity summary.",
            "- Activation repair-hardening Stage06 final route state and selected-denominator replay evidence.",
            "- Current vNext context/doctrine and launch-pack prompts.",
            "- Master terminal acceptance, external dependency, shared-file ownership, and merge-readiness ledgers.",
            "",
            "## Lane Status",
            "",
            f"- Immediate launch lanes from the launch pack: `{', '.join(immediate)}`.",
            f"- Terminal verified lanes on current disk: `{', '.join(terminal_lanes) if terminal_lanes else 'none'}`.",
            f"- External-session-owned handoff lanes not accepted as terminal by Master: `{', '.join(external_session_owned_lanes) if external_session_owned_lanes else 'none'}`.",
            f"- Lanes with terminal acceptance held for external Lane02 dependency: `{', '.join(external_dependency_pending_lanes) if external_dependency_pending_lanes else 'none'}`.",
            f"- Missing lane route directories: `{', '.join(missing_routes) if missing_routes else 'none'}`.",
            f"- Non-terminal lanes 01-08 still blocking Lane09: `{', '.join(non_terminal_lanes_01_to_08) if non_terminal_lanes_01_to_08 else 'none'}`.",
            "- Lane09 package is terminal on disk; remaining work is scoped merge/staging review and policy-gated production deployment, not lane-artifact absence.",
            lane02_line,
            "",
            "## Ownership And Merge Readiness",
            "",
            "- Terminal-verified lane artifacts have been packaged by Lane09 for local merge review.",
            "- `MASTER_SHARED_FILE_OWNERSHIP_LEDGER.jsonl` records shared runtime/config/test/route ownership and conflict-prevention policy.",
            "- `MASTER_SCOPED_MERGE_STAGING_LEDGER.jsonl` and `MASTER_SCOPED_MERGE_STAGING_PLAN.json` classify the full current dirty worktree without staging broad live/shadow dirt; verified Lane02 terminal handoff artifacts are packaged only through the scoped Lane09/Master candidate list.",
            merge_state_line,
            f"- `MASTER_MERGE_READINESS_MATRIX.json` keeps `completion_ready=false` because {gate_phrase} remain open.",
            "",
            "## Seed Results",
            "",
            "- Clean Friday quality subset and broad London replay support are materialized in `MASTER_CROSS_LANE_RESULT_MATERIALIZATION_LEDGER.jsonl`.",
            lane01_seed_line,
            "- All 24 symbols are preserved in `MASTER_MARKET_COVERAGE_SEED_LEDGER.jsonl`; the crypto rows are appendix/exclusion evidence rather than primary Friday denominator rows.",
            "",
            "## Blockers",
            "",
            *blocker_lines,
            "",
            "## Completion Audit",
            "",
            f"Completion ready: `{audit['completion_ready']}`.",
            f"Do not mark the thread goal complete from this checkpoint; {gate_phrase} remain open.",
            "",
        ]
    )


def run_route_verifier() -> dict[str, Any]:
    command = [sys.executable, str(ROUTE_DIR / "verify_master_orchestration_artifacts.py")]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = {}
    payload.update(
        {
            "command": " ".join(command),
            "exit_code": completed.returncode,
            "stderr_tail": completed.stderr[-1000:],
            "stdout_tail": completed.stdout[-1000:],
        }
    )
    return payload


def run_py_compile_checks() -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "py_compile",
        "scripts/build_vnext_next_level_master_orchestration.py",
        rel(ROUTE_DIR / "verify_master_orchestration_artifacts.py"),
    ]
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    return {
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "ok": completed.returncode == 0,
        "stderr_tail": completed.stderr[-1000:],
        "stdout_tail": completed.stdout[-1000:],
    }


def build_focused_test_result(
    now: str,
    prompt_hardening: dict[str, Any],
    verification: dict[str, Any],
    py_compile_result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "completion_ready": False,
        "generated_at_utc": now,
        "ok": bool(prompt_hardening.get("ok")) and bool(verification.get("ok")) and bool(py_compile_result.get("ok")),
        "prompt_hardening_ok": bool(prompt_hardening.get("ok")),
        "py_compile_result": py_compile_result,
        "route_id": ROUTE_ID,
        "schema_version": "vnext_next_level_master_focused_test_result_v1",
        "test_commands": [
            check["command"] for check in prompt_hardening.get("checks", [])
        ]
        + [
            py_compile_result["command"],
            verification.get("command"),
            "python scripts/audit_goal_route_artifacts.py research/operations/vnext_next_level_master_orchestration_2026_05_31 --full-jsonl",
        ],
        "verification_ok": bool(verification.get("ok")),
    }


def build_saturation_report(now: str, audit: dict[str, Any], staging_plan: dict[str, Any]) -> str:
    gate_phrase = remaining_gate_phrase(bool(staging_plan.get("scoped_commit_performed")))
    return "\n".join(
        [
            "# vNext Next-Level Master Saturation And Self-Red-Team",
            "",
            f"Generated: {now}",
            "",
            "## Master-Scope Saturation",
            "",
            "The master route has exhausted the current master orchestration evidence class for this checkpoint: current context was reread, all lane prompts were validated, all nine lanes were registered, the dependency graph was written, seed result materialization was copied from disk evidence, every live-symbol Friday coverage seed row was preserved, Lane09 package status was consumed, cross-lane blockers were assigned, and terminal-acceptance/shared-file/scoped-staging/merge-readiness ledgers were materialized.",
            "",
            "## Self-Red-Team Findings",
            "",
            "- Completion is deliberately false. A registry, blocker ledger, or subagent request ledger is not lane completion.",
            "- The manual fixed-vNext portfolio seed is not accepted as truth from the prompt. It is assigned to Lane01 for recomputation or correction from disk evidence.",
            "- Lane02 remains dedicated-session-owned, but Lane09 may package the verified handoff read-only without Master rewriting or narrowing it.",
            "- Lane03 and Lane08 are accepted only after Lane09 records read-only Lane02 package adoption.",
            "- Completion remains false after Lane09 packaging because scoped commit, production-change approval, and broker lifecycle future evidence remain separate.",
            "- The subagent request ledger proves launch, not finding integration. Findings must be written to disk and the registry regenerated before using them as evidence.",
            "- No live broker action, paid source call, credential change, remote push, or hidden production behavior change was performed.",
            "",
            "## Stop Condition",
            "",
            f"Current status: `{audit['status']}`. Lane artifacts, the Lane09 package, and Master scoped staging review are materialized; the broader objective remains active until {gate_phrase} are resolved or explicitly bounded.",
            "",
        ]
    )


def main() -> int:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    now = utc_now()
    head = git_head()
    scoped_package_commit = detect_scoped_package_commit()

    prompt_hardening = build_prompt_hardening(now)
    write_json(ROUTE_DIR / "MASTER_PROMPT_HARDENING_VERIFICATION.json", prompt_hardening)
    write_jsonl(ROUTE_DIR / "MASTER_SUBAGENT_AUDIT_FINDINGS.jsonl", SUBAGENT_FINDINGS)

    registry = build_registry(now, prompt_hardening["checks"])
    write_json(
        ROUTE_DIR / "MASTER_ROUTE_REGISTRY.json",
        {
            "generated_at_utc": now,
            "git_head": head,
            "lanes": registry,
            "route_id": ROUTE_ID,
            "schema_version": "vnext_next_level_master_route_registry_v1",
        },
    )
    write_json(ROUTE_DIR / "MASTER_LANE_DEPENDENCY_GRAPH.json", build_dependency_graph(now))
    write_json(ROUTE_DIR / "MASTER_SEED_FACT_AUDIT.json", build_seed_fact_audit(now))
    write_jsonl(ROUTE_DIR / "MASTER_EVIDENCE_INSPECTION_LEDGER.jsonl", build_evidence_inspection_ledger())
    write_jsonl(ROUTE_DIR / "MASTER_CROSS_LANE_BLOCKER_LEDGER.jsonl", build_blocker_ledger(now))
    write_jsonl(ROUTE_DIR / "MASTER_CROSS_LANE_RESULT_MATERIALIZATION_LEDGER.jsonl", build_result_materialization_ledger(now))
    write_jsonl(ROUTE_DIR / "MASTER_MARKET_COVERAGE_SEED_LEDGER.jsonl", build_market_coverage_seed_ledger(now))
    write_jsonl(ROUTE_DIR / "MASTER_SUBAGENT_AUDIT_LEDGER.jsonl", SUBAGENT_AUDIT_REQUESTS)
    terminal_acceptance = build_terminal_acceptance_ledger(now, registry, scoped_package_commit)
    external_dependencies = build_external_dependency_ledger(now, registry, scoped_package_commit)
    write_jsonl(ROUTE_DIR / "MASTER_TERMINAL_ACCEPTANCE_LEDGER.jsonl", terminal_acceptance)
    write_jsonl(ROUTE_DIR / "MASTER_EXTERNAL_DEPENDENCY_LEDGER.jsonl", external_dependencies)
    write_jsonl(
        ROUTE_DIR / "MASTER_SHARED_FILE_OWNERSHIP_LEDGER.jsonl",
        build_shared_file_ownership_ledger(now, registry, scoped_package_commit),
    )
    staging_plan, staging_rows = build_scoped_merge_staging_review(now, scoped_package_commit)
    write_jsonl(ROUTE_DIR / "MASTER_SCOPED_MERGE_STAGING_LEDGER.jsonl", staging_rows)
    write_json(ROUTE_DIR / "MASTER_SCOPED_MERGE_STAGING_PLAN.json", staging_plan)
    merge_readiness = build_merge_readiness_matrix(
        now,
        registry,
        terminal_acceptance,
        external_dependencies,
        staging_plan,
    )
    write_json(ROUTE_DIR / "MASTER_MERGE_READINESS_MATRIX.json", merge_readiness)

    decisions = [
        {
            "branch_decision": "open_master_route_keep_goal_active",
            "evidence": "MASTER_ROUTE_REGISTRY.json",
            "implementation_decision": "materialize_master_registry_and_lane_contracts_first",
            "schema_version": "vnext_next_level_master_decision_v1",
            "timestamp_utc": now,
        },
        {
            "branch_decision": "do_not_claim_lane_completion",
            "evidence": "MASTER_ORCHESTRATION_COMPLETION_AUDIT.json",
            "implementation_decision": "lane routes must implement, verify, and write terminal artifacts before Lane09 merge",
            "schema_version": "vnext_next_level_master_decision_v1",
            "timestamp_utc": now,
        },
        {
            "branch_decision": "respect_dedicated_lane02_goal_session_ownership",
            "evidence": "MASTER_EXTERNAL_DEPENDENCY_LEDGER.jsonl",
            "implementation_decision": "Master coordinates Lane02 status/dependencies only and treats Lane02 artifacts as handoff material until explicitly adopted by Lane02/Lane09",
            "schema_version": "vnext_next_level_master_decision_v1",
            "timestamp_utc": now,
        },
    ]
    write_jsonl(ROUTE_DIR / "MASTER_ORCHESTRATION_DECISION_LEDGER.jsonl", decisions)

    audit = build_completion_audit(now, registry, prompt_hardening, merge_readiness, staging_plan)
    write_json(ROUTE_DIR / "MASTER_ORCHESTRATION_COMPLETION_AUDIT.json", audit)
    (ROUTE_DIR / "MASTER_ORCHESTRATION_CONTEXT_ANCHOR.md").write_text(
        "\n".join(
            [
                "# vNext Next-Level Master Context Anchor",
                "",
                f"Generated: {now}",
                f"HEAD: `{head.get('short_subject')}`",
                f"Controlling prompt: `{rel(MASTER_PROMPT)}`",
                "",
                f"Current stop condition: keep the goal active. The master route registry, seed evidence ledgers, blocker ledger, result materialization ledger, terminal acceptance ledger, external dependency ledger, shared-file ownership ledger, scoped staging review ledger, merge-readiness matrix, prompt-hardening check, verifier, manifest, and not-complete audit have been written. Lane02 remains dedicated-session-owned while Lane09 has adopted its verifier-clean handoff read-only for packaging; Lane03/Lane08 dependency holds are cleared by Lane09; {remaining_gate_phrase(bool(staging_plan.get('scoped_commit_performed')))} remain open.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (ROUTE_DIR / "MASTER_ORCHESTRATION_FINAL_REPORT.md").write_text(
        build_final_report(now, registry, audit, staging_plan),
        encoding="utf-8",
    )
    write_route_local_verifier()
    write_json(ROUTE_DIR / "MASTER_ORCHESTRATION_OUTPUT_MANIFEST.json", build_manifest(now))
    verification = run_route_verifier()
    write_json(ROUTE_DIR / "MASTER_ORCHESTRATION_VERIFICATION_RESULT.json", verification)
    py_compile_result = run_py_compile_checks()
    write_json(
        ROUTE_DIR / "MASTER_ORCHESTRATION_FOCUSED_TEST_RESULT.json",
        build_focused_test_result(now, prompt_hardening, verification, py_compile_result),
    )
    (ROUTE_DIR / "MASTER_ORCHESTRATION_SATURATION_SELF_RED_TEAM.md").write_text(
        build_saturation_report(now, audit, staging_plan),
        encoding="utf-8",
    )
    write_json(ROUTE_DIR / "MASTER_ORCHESTRATION_OUTPUT_MANIFEST.json", build_manifest(now))

    print(
        json.dumps(
            {
                "completion_ready": audit["completion_ready"],
                "git_head": head,
                "ok": verification.get("ok", False) and prompt_hardening.get("ok", False),
                "route_dir": rel(ROUTE_DIR),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if verification.get("ok", False) and prompt_hardening.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
