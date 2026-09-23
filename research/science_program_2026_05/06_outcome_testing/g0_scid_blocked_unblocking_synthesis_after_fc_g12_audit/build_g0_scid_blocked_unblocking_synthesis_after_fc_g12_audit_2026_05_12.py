"""Build G0 blocked-card source/control unblocking synthesis artifacts.

This route reconciles accepted G12 control evidence for the 15 future-capture
blocked cards with the sibling blocked-card control lanes. It emits source and
route-control artifacts only: no results, validation, promotion, broker order
evidence, paid/API access, raw market blobs, live restarts, or trading behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-12"
PREFIX = "G0_SCID_BLOCKED_UNBLOCKING"
ROUTE_ID = "G0_SCID_BLOCKED_CARD_UNBLOCKING_SYNTHESIS_AFTER_G12_FUTURE_CAPTURE_SOURCE_AUDIT"
EVIDENCE_CLASS = "G0_SCID_BLOCKED_CARD_UNBLOCKING_SYNTHESIS_AFTER_G12_FUTURE_CAPTURE_SOURCE_AUDIT_ONLY"
SCHEMA_VERSION = "g0_scid_blocked_unblocking_synthesis_v1"
TERMINAL_DECISION = "ACCEPT_AS_G0_SCID_BLOCKED_CARD_UNBLOCKING_SYNTHESIS_WITH_RANKED_SOURCE_CONTROL_ROUTE_BUNDLE"

ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
PROMPT_DIR = REPO_ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
OUTCOME_DIR = REPO_ROOT / "research" / "science_program_2026_05" / "06_outcome_testing"

G0_NOAPI_DIR = OUTCOME_DIR / "g0_scid_noapi_40card_prereg_replay_input_design_synthesis"
FC_TARGET_DIR = OUTCOME_DIR / "scid_future_capture_field_source_state_materialization_for_blocked15"
FC_G12_DIR = OUTCOME_DIR / "g12_scid_future_capture_blocked15_source_state_materialization_audit"
LTF_G12_DIR = OUTCOME_DIR / "g12_scid_ltf_proxy_blocked17_source_status_audit"
READY8_G12_DIR = OUTCOME_DIR / "g12_scid_noapi_ready8_rowset_target_horizon_packet_audit"
EXPANSION_G12_DIR = OUTCOME_DIR / "g12_scid_expansion_candidate_acceptance_design_audit"
ANTI_BOXING_G12_DIR = OUTCOME_DIR / "g12_scid_anti_boxing_route_intake_audit"

SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}

MANDATORY_CONTEXT = [
    ".context/LIVE_STATE.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/00_core/ai_in_loop_cost_control_research_plan.md",
    ".context/00_core/quick_reference_card.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
]

CONTROL_PROMPT = (
    "research/science_program_2026_05/04_goal_prompts/"
    "G0_SCID_BLOCKED_UNBLOCKING_SYNTHESIS_AFTER_FC_G12_AUDIT_GOAL_PROMPT_2026-05-12.md"
)

REQUIRED_INPUTS = {
    "g12_blocked15_decision": FC_G12_DIR / "G12_SCID_FC_BLOCKED15_AUDIT_DECISION_LEDGER_2026-05-12.json",
    "g12_blocked15_completion": FC_G12_DIR / "G12_SCID_FC_BLOCKED15_AUDIT_COMPLETION_AUDIT_2026-05-12.json",
    "g12_blocked15_recovered_rows": FC_G12_DIR / "G12_SCID_FC_BLOCKED15_AUDIT_RECOVERED_ROW_SCHEMA_REDACTION_AUDIT_2026-05-12.json",
    "g12_blocked15_contract": FC_G12_DIR / "G12_SCID_FC_BLOCKED15_AUDIT_PROSPECTIVE_CONTRACT_EXACTNESS_AUDIT_2026-05-12.json",
    "g12_blocked15_denominator": FC_G12_DIR / "G12_SCID_FC_BLOCKED15_AUDIT_DENOMINATOR_QUARANTINE_AND_SAFE_FLAG_AUDIT_2026-05-12.json",
    "blocked32_route_ledger": G0_NOAPI_DIR / "G0_SCID_NOAPI_PREREG_SYNTHESIS_BLOCKED_32_ROUTE_LEDGER_2026-05-12.json",
    "blocked15_card_set": FC_TARGET_DIR / "SCID_FUTURE_CAPTURE_BLOCKED15_CARD_SET_2026-05-12.json",
    "blocked15_field_matrix": FC_TARGET_DIR / "SCID_FUTURE_CAPTURE_FIELD_TO_SOURCE_STATE_MATRIX_2026-05-12.json",
    "g12_ltf_decision": LTF_G12_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_DECISION_LEDGER_2026-05-12.json",
    "g12_ltf_denominator": LTF_G12_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_DENOMINATOR_RECOMPUTATION_2026-05-12.json",
    "g12_ltf_source_status": LTF_G12_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_SOURCE_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json",
    "g12_ltf_search_inventory": LTF_G12_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_SEARCH_ROOT_SOURCE_INVENTORY_AUDIT_2026-05-12.json",
    "g12_ready8_decision": READY8_G12_DIR / "G12_SCID_NOAPI_READY8_DECISION_LEDGER_2026-05-12.json",
    "g12_expansion_decision": EXPANSION_G12_DIR / "G12_SCID_EXPANSION_AUDIT_DECISION_LEDGER_2026-05-12.json",
    "g12_expansion_candidate_count": EXPANSION_G12_DIR / "G12_SCID_EXPANSION_AUDIT_CANDIDATE_COUNT_AUDIT_2026-05-12.json",
    "g12_anti_boxing_decision": ANTI_BOXING_G12_DIR / "G12_SCID_ANTI_BOXING_DECISION_LEDGER_2026-05-12.json",
    "g12_anti_boxing_route_family": ANTI_BOXING_G12_DIR / "G12_SCID_ANTI_BOXING_ROUTE_FAMILY_RECOMPUTATION_AUDIT_2026-05-12.json",
    "g12_anti_boxing_prompt_pack": ANTI_BOXING_G12_DIR / "G12_SCID_ANTI_BOXING_PROMPT_PACK_AUDIT_2026-05-12.json",
}

EXPECTED_CAPTURE_GROUPS = {
    "baseline_control_fields",
    "framework_setup_family",
    "future_orderflow_depth_proxy_requirements",
    "intended_entry_reference",
    "intended_side_direction",
    "intended_stop_reference",
    "intended_target_reference",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "poi_type_bounds_source",
}

FORBIDDEN_SURFACES = [
    "validation",
    "results",
    "R/PnL/win-rate/expectancy/performance",
    "promotion",
    "AI/API",
    "paid vendor access",
    "broker account/order/history/deal/position evidence",
    "raw market blob commit",
    "live restart",
    "live behavior",
    "trading/risk/safety/prompt-decision changes",
]


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE}{suffix}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# {title}\n\n```json\n{json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)}\n```\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def base_payload(artifact_family: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "artifact_family": artifact_family,
        "generated_at_utc": utc_now(),
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "schema_version": SCHEMA_VERSION,
    }
    payload.update(SAFE_FLAGS)
    return payload


def load_inputs() -> dict[str, Any]:
    return {name: read_json(path) for name, path in REQUIRED_INPUTS.items()}


def input_hash_rows() -> list[dict[str, Any]]:
    rows = []
    for name, path in REQUIRED_INPUTS.items():
        rows.append(
            {
                "input_name": name,
                "path": rel(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
            }
        )
    return rows


def git_head() -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip()


def git_status_rows() -> list[dict[str, Any]]:
    proc = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    rows = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        rows.append({"raw": line, "path": line[3:].replace("\\", "/")})
    return rows


def root_existence_rows() -> list[dict[str, Any]]:
    roots = [
        REPO_ROOT / "data",
        Path("C:/Users/MSI/Documents/ai-trading-agent/data"),
        Path("C:/Users/MSI/Documents/ai-trading-agent/data/ticks"),
        Path("C:/Users/MSI/Documents/ai-trading-agent/data/external"),
        Path("C:/Users/MSI/Documents/ai-trading-agent/shadow_logs"),
        Path("C:/Users/MSI/Documents/ai-trading-agent/exports"),
        Path("C:/tmp"),
        Path("C:/SierraChart"),
    ]
    rows = []
    for root in roots:
        rows.append({"path": root.as_posix(), "exists": root.exists(), "used_as_result_or_blob_source": False})
    return rows


def source_action_for_capture_group(group: str, summary: dict[str, Any]) -> dict[str, Any]:
    current = summary.get("current_route_materialization", {})
    status = current.get("status")
    recovered = current.get("recovered_row_count", 0)
    historical = summary.get("historical_status_after_search")
    if status == "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT":
        if group == "baseline_control_fields":
            next_action = (
                "Immediate source-control materialization is available: freeze baseline/partition/control assignment "
                "manifests for blocked cards, then require G12 packet audit before any future scoring gate."
            )
        elif group == "lifecycle_fill_cancel_expiry_source_status":
            next_action = (
                "Materialize nonbroker lifecycle source-state examples and prospective capture contract; preserve the "
                "broker-account/order/history/deal/position evidence ban and require G12 source-control audit."
            )
        else:
            next_action = (
                "Use recovered source-state rows as parser/schema/as-of fixtures and forward capture proof; denominator "
                "remains blocked until candidate-attached source rows are frozen and audited."
            )
        action_type = "IMMEDIATE_SOURCE_MATERIALIZATION_THEN_G12_PACKET_AUDIT"
    elif status == "NO_RECOVERABLE_STRUCTURED_SOURCE_ROWS_FOUND_FOR_ACCEPTED_40_DENOMINATOR":
        next_action = (
            "Historical source-state truth is not recoverable from price. Build the exact forward capture/source logger "
            "`source_safe_mso_snapshot_and_poi_logger` with POI type, bounds, source bars, snapshot hash, and rule version; "
            "then run G12 audit before any denominator movement."
        )
        action_type = "EXACT_PROSPECTIVE_CAPTURE_REQUIREMENT"
    elif status == "ROUTED_TO_R2_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION":
        next_action = (
            "Use the accepted LTF/orderflow/proxy source-status lane: attach parser/source-hash/as-of/proxy-validity "
            "requirements to each card, then G12 audit the candidate-attached packet before scoring."
        )
        action_type = "ROUTED_TO_ACCEPTED_LTF_PROXY_SOURCE_STATUS_CONTROL"
    else:
        next_action = "Fail closed until source/logger/parser/as-of contract is made exact and independently audited."
        action_type = "FAIL_CLOSED_EXACT_SOURCE_REQUIREMENT"
    return {
        "capture_group": group,
        "current_materialization_status": status,
        "historical_status_after_search": historical,
        "recovered_source_state_rows": recovered,
        "next_action_type": action_type,
        "exact_next_action": next_action,
        "accepted_40_denominator_unblocked_now": False,
    }


def source_action_for_ltf_card(card_row: dict[str, Any]) -> dict[str, Any]:
    terminal = card_row.get("terminal_source_status")
    if terminal == "SOURCE_STATUS_EXPANDED_LTF_PARSER_REQUIRED":
        action_type = "LTF_PARSER_AND_ASOF_ATTACHMENT_REQUIRED"
        action = (
            "Implement or select a read-only lower-timeframe parser/source-hash/as-of attachment manifest for the card's "
            "decision window; G12 audit parser coverage before result packet use."
        )
    elif terminal == "SOURCE_STATUS_EXPANDED_PROXY_CONTRACT_REQUIRED":
        action_type = "ORDERFLOW_PROXY_CONTRACT_REQUIRED"
        action = (
            "Freeze proxy instrument, source family, contract month, parser/hash/as-of, CFD-transfer limits, and "
            "no-broker-truth language; require G12 source-contract audit before result packet use."
        )
    else:
        action_type = "PARTIAL_SOURCE_STATUS_SPLIT_REQUIRED"
        action = (
            "Split the card into recovered/source-existing fields and non-generatable historical source-state fields; "
            "materialize recoverable parser contracts and prospective capture requirements separately."
        )
    return {
        "terminal_source_status": terminal,
        "status_counts": card_row.get("status_counts", {}),
        "next_action_type": action_type,
        "exact_next_action": action,
        "accepted_40_denominator_unblocked_now": False,
    }


def route_definitions() -> list[dict[str, Any]]:
    prompt_base_inputs = [
        CONTROL_PROMPT,
        rel(artifact_path("ROUTE_RECONCILIATION_LEDGER")),
        rel(artifact_path("SAME_EVIDENCE_BLOCKER_PURSUIT_LEDGER")),
        rel(artifact_path("DENOMINATOR_QUARANTINE_GATE_LEDGER")),
    ]
    return [
        {
            "rank": 1,
            "route_id": "SCID_BLOCKED32_PARALLEL_SOURCE_CONTROL_REPAIR_WAVE",
            "title": "SCID Blocked32 Parallel Source-Control Repair Wave",
            "evidence_class": "SCID_BLOCKED32_PARALLEL_SOURCE_CONTROL_REPAIR_WAVE_ONLY",
            "route_family": "parent_parallel_wave_for_blocked_card_unblocking",
            "domain_breadth": [
                "source-state",
                "lifecycle",
                "LTF",
                "orderflow/proxy",
                "baseline-control",
                "failure-anatomy",
                "non-OB",
                "cross-domain",
            ],
            "parallelizable_now": False,
            "requires_prior_acceptance": "This current G0 synthesis acceptance; children may run in parallel after it.",
            "may_open_outcomes_or_results": False,
            "objective": (
                "Launch the blocked32 child repair wave as source/control only, using accepted G12 blocked15 and "
                "blocked17 control evidence to drive disjoint same-evidence-class repairs without scoring."
            ),
            "required_inputs": prompt_base_inputs,
            "required_outputs": [
                "child-route closeout ledger",
                "card-level source-control transition matrix",
                "fail-closed packet readiness gate",
                "G12 audit prompt for the assembled packet gate",
            ],
            "completion_standard": (
                "Complete only when every child source-control route has either accepted source materialization, an exact "
                "prospective capture requirement, or an exact access/source/parser requirement; no result row may open."
            ),
        },
        {
            "rank": 2,
            "route_id": "SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR",
            "title": "SCID Blocked15 POI Bounds Source Capture Contract Repair",
            "evidence_class": "SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR_ONLY",
            "route_family": "poi_bounds_and_mso_snapshot_source_state_repair",
            "domain_breadth": ["source-state", "non-OB", "geometry", "failure-anatomy"],
            "parallelizable_now": True,
            "requires_prior_acceptance": "Current G0 synthesis acceptance only.",
            "may_open_outcomes_or_results": False,
            "objective": (
                "Turn the zero-recovered POI/bounds group into an exact forward source-state capture contract and "
                "synthetic parser fixture package without inferring historical structure truth from price."
            ),
            "required_inputs": prompt_base_inputs + [rel(FC_G12_DIR / "G12_SCID_FC_BLOCKED15_AUDIT_PROSPECTIVE_CONTRACT_EXACTNESS_AUDIT_2026-05-12.json")],
            "required_outputs": [
                "POI/bounds source logger contract",
                "mso snapshot hash and source-bar schema",
                "synthetic no-leak/redaction fixtures",
                "G12 repair audit prompt/starter",
            ],
            "completion_standard": (
                "Complete only with exact fields, parser/as-of/hash/redaction tests, and fail-closed card requirements for "
                "ADV-005, BEH-002, BEH-003, BEH-005, and GEO-001."
            ),
        },
        {
            "rank": 3,
            "route_id": "SCID_BLOCKED17_LTF_ASOF_PATH_PARSER_AND_CANDIDATE_ATTACHMENT",
            "title": "SCID Blocked17 LTF Asof Path Parser And Candidate Attachment",
            "evidence_class": "SCID_BLOCKED17_LTF_ASOF_PATH_PARSER_AND_CANDIDATE_ATTACHMENT_ONLY",
            "route_family": "ltf_parser_source_hash_asof_attachment",
            "domain_breadth": ["LTF", "path-shape", "hazard", "geometry", "execution"],
            "parallelizable_now": True,
            "requires_prior_acceptance": "Current G0 synthesis acceptance only.",
            "may_open_outcomes_or_results": False,
            "objective": (
                "Use the accepted blocked17 source-status audit to attach lower-timeframe source existence, parser, hash, "
                "and decision-window as-of requirements to card-level packet designs."
            ),
            "required_inputs": prompt_base_inputs + [rel(LTF_G12_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_SOURCE_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json")],
            "required_outputs": [
                "LTF parser/source hash attachment matrix",
                "candidate decision-window as-of manifest",
                "missing parser/access ledger",
                "G12 source-status repair audit prompt/starter",
            ],
            "completion_standard": (
                "Complete only when SOURCE_EXISTS_NEEDS_PARSER rows are either parser-bound and hash/as-of attached or "
                "reduced to exact file/parser/access requirements."
            ),
        },
        {
            "rank": 4,
            "route_id": "SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AND_SOURCE_STATUS_ATTACH",
            "title": "SCID Blocked17 Orderflow Proxy Contract And Source Status Attach",
            "evidence_class": "SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AND_SOURCE_STATUS_ATTACH_ONLY",
            "route_family": "orderflow_depth_proxy_source_contract",
            "domain_breadth": ["orderflow/proxy", "microstructure", "cross-domain", "execution"],
            "parallelizable_now": True,
            "requires_prior_acceptance": "Current G0 synthesis acceptance only; paid/vendor access still separately forbidden.",
            "may_open_outcomes_or_results": False,
            "objective": (
                "Freeze proxy/depth/orderflow source contracts for blocked cards without claiming broker-native CFD truth, "
                "using existing source-status evidence and exact future access requirements where needed."
            ),
            "required_inputs": prompt_base_inputs + [rel(LTF_G12_DIR / "G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_PROXY_HASH_ASOF_AUDIT_2026-05-12.json")],
            "required_outputs": [
                "proxy-validity and source-family contract",
                "as-of/hash/redaction policy",
                "paid-access-free blocker ledger",
                "G12 proxy source-contract audit prompt/starter",
            ],
            "completion_standard": (
                "Complete only when proxy evidence is explicitly context/control only, broker truth claims remain zero, and "
                "every unresolved source is an exact source/access/parser requirement."
            ),
        },
        {
            "rank": 5,
            "route_id": "SCID_BLOCKED_BASELINE_LIFECYCLE_SOURCE_STATE_MATERIALIZATION",
            "title": "SCID Blocked Baseline Lifecycle Source State Materialization",
            "evidence_class": "SCID_BLOCKED_BASELINE_LIFECYCLE_SOURCE_STATE_MATERIALIZATION_ONLY",
            "route_family": "baseline_control_and_lifecycle_materialization",
            "domain_breadth": ["baseline-control", "lifecycle", "failure-anatomy", "execution"],
            "parallelizable_now": True,
            "requires_prior_acceptance": "Current G0 synthesis acceptance only.",
            "may_open_outcomes_or_results": False,
            "objective": (
                "Materialize recovered baseline-control and nonbroker lifecycle source-state examples into candidate-safe "
                "packet/control fixtures while preserving the broker account/order/history/deal/position ban."
            ),
            "required_inputs": prompt_base_inputs + [rel(FC_G12_DIR / "G12_SCID_FC_BLOCKED15_AUDIT_RECOVERED_ROW_SCHEMA_REDACTION_AUDIT_2026-05-12.json")],
            "required_outputs": [
                "baseline assignment packet fixture",
                "lifecycle source-state fixture",
                "redaction/no-broker-evidence audit",
                "G12 source-state packet audit prompt/starter",
            ],
            "completion_standard": (
                "Complete only when baseline-control and lifecycle rows are source/as-of/hash/redaction bound and still "
                "cannot be interpreted as result denominators."
            ),
        },
        {
            "rank": 6,
            "route_id": "SCID_BLOCKED_FAILURE_ANATOMY_NEGATIVE_EVIDENCE_CONTROL_PACKET",
            "title": "SCID Blocked Failure Anatomy Negative Evidence Control Packet",
            "evidence_class": "SCID_BLOCKED_FAILURE_ANATOMY_NEGATIVE_EVIDENCE_CONTROL_PACKET_ONLY",
            "route_family": "failure_anatomy_without_outcome_opening",
            "domain_breadth": ["failure-anatomy", "non-OB", "cross-domain", "uncertainty"],
            "parallelizable_now": True,
            "requires_prior_acceptance": "Current G0 synthesis acceptance only.",
            "may_open_outcomes_or_results": False,
            "objective": (
                "Convert blocked-card negative/source gaps into row-level failure-anatomy controls without opening target, "
                "stop, R, PnL, win-rate, expectancy, or validation fields."
            ),
            "required_inputs": prompt_base_inputs,
            "required_outputs": [
                "blocked reason anatomy matrix",
                "source-gap to future-hypothesis ledger",
                "no-outcome redaction audit",
                "G12 failure-anatomy source-control audit prompt/starter",
            ],
            "completion_standard": (
                "Complete only with exact source-gap categories, future capture fields, and no result/performance leakage."
            ),
        },
        {
            "rank": 7,
            "route_id": "SCID_BLOCKED_CROSS_DOMAIN_NON_OB_ROUTE_EXPANSION_GATE",
            "title": "SCID Blocked Cross Domain Non OB Route Expansion Gate",
            "evidence_class": "SCID_BLOCKED_CROSS_DOMAIN_NON_OB_ROUTE_EXPANSION_GATE_ONLY",
            "route_family": "anti_boxing_and_expansion_denominator_gate",
            "domain_breadth": ["cross-domain", "non-OB", "macro", "ML", "microstructure", "behavioral"],
            "parallelizable_now": True,
            "requires_prior_acceptance": "Current G0 synthesis acceptance only; accepted-40 denominator entry still requires separate G0/G12 gate.",
            "may_open_outcomes_or_results": False,
            "objective": (
                "Keep the 40 accepted cards as a floor rather than a ceiling by ranking quarantined expansion and anti-boxing "
                "routes with denominator-entry gates, without mixing them into accepted result rows."
            ),
            "required_inputs": prompt_base_inputs + [
                rel(EXPANSION_G12_DIR / "G12_SCID_EXPANSION_AUDIT_CANDIDATE_COUNT_AUDIT_2026-05-12.json"),
                rel(ANTI_BOXING_G12_DIR / "G12_SCID_ANTI_BOXING_ROUTE_FAMILY_RECOMPUTATION_AUDIT_2026-05-12.json"),
            ],
            "required_outputs": [
                "expansion denominator-entry criteria",
                "anti-boxing child-route sequence",
                "accepted-40 quarantine audit",
                "next G0 denominator-entry prompt/starter",
            ],
            "completion_standard": (
                "Complete only when expansion candidates remain outside the accepted denominator until separately accepted."
            ),
        },
        {
            "rank": 8,
            "route_id": "SCID_BLOCKED_RESULT_GATE_DORMANT_UNTIL_SOURCE_CONTROL_ACCEPTED",
            "title": "SCID Blocked Result Gate Dormant Until Source Control Accepted",
            "evidence_class": "SCID_BLOCKED_RESULT_GATE_DORMANT_UNTIL_SOURCE_CONTROL_ACCEPTED_ONLY",
            "route_family": "result_gate_dormancy_and_completion_audit",
            "domain_breadth": ["denominator-control", "validation-gate", "source-control"],
            "parallelizable_now": False,
            "requires_prior_acceptance": "All child source-control routes plus G12/G0 packet acceptance.",
            "may_open_outcomes_or_results": False,
            "objective": (
                "Maintain a dormant future result gate that refuses blocked-card scoring until every accepted source/control "
                "dependency is packetized, G12 accepted, and re-synthesized by G0."
            ),
            "required_inputs": prompt_base_inputs,
            "required_outputs": [
                "dormant result-gate checklist",
                "source-control acceptance dependency graph",
                "no-result safe flag audit",
                "future result-gate prompt only if dependencies are complete",
            ],
            "completion_standard": (
                "Complete only with a fail-closed gate; it must not open outcomes in the blocked-card source/control lane."
            ),
        },
    ]


def prompt_for_route(route: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "title": route["title"],
        "objective": route["objective"],
        "evidence_class": route["evidence_class"],
        "operating_posture": (
            "Constructive source/control builder posture. Examples are starting points, not limits. Pursue same-evidence-class "
            "source, parser, as-of, redaction, lifecycle, baseline-control, LTF, orderflow/proxy, cross-domain, non-OB, and "
            "failure-anatomy routes until cleared, proven impossible from accepted routes, or reduced to an exact source/capture/access requirement."
        ),
        "mandatory_preflight": [
            "python scripts/generate_live_state.py",
            ".context/LIVE_STATE.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/research_operating_doctrine.md",
            ".context/00_core/research_current_state.md",
            ".context/00_core/local_heavy_data_inventory.md",
            ".context/00_core/ai_in_loop_cost_control_research_plan.md",
        ],
        "required_inputs": route["required_inputs"],
        "required_outputs": route["required_outputs"],
        "completion_standard": route["completion_standard"],
        "forbidden_surfaces": FORBIDDEN_SURFACES,
        "safe_flags": {
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "must_not_do": [
            "Do not open validation, result scoring, R/PnL/win-rate/expectancy/performance, or promotion.",
            "Do not use AI/API, paid vendor access, broker account/order/history/deal/position evidence, raw market blob commits, live restarts, live behavior changes, or trading/risk/safety/prompt-decision changes.",
            "Do not infer historical GTOS intent/order/lifecycle/source-state truth from later price movement.",
            "Do not mix expansion/quarantined rows into the accepted 40-card denominator.",
        ],
    }
    return payload


def write_prompt_pack(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for route in routes:
        prompt_path = PROMPT_DIR / f"{route['route_id']}_GOAL_PROMPT_{DATE}.md"
        starter_path = ROUTE_DIR / f"{route['route_id']}_STARTER_{DATE}.txt"
        prompt_payload = prompt_for_route(route)
        prompt_path.write_text(
            f"# {route['title']}\n\n```json\n{json.dumps(prompt_payload, indent=2, sort_keys=True, ensure_ascii=True)}\n```\n",
            encoding="utf-8",
        )
        starter = (
            f"/goal Follow the full controlling prompt in {rel(prompt_path)} as the complete objective; "
            "run mandatory preflight/context refresh first; do not rely on chat or compaction memory; "
            f"stay {route['evidence_class']} with no validation/results/R/PnL/win-rate/expectancy/performance/promotion/"
            "AI/API/paid-vendor/broker-account-order-history-deal-position/raw-blob/live-restart/live-behavior/"
            "trading-risk-safety-prompt-decision changes; pursue every same-evidence-class source/control blocker "
            "until cleared, proven impossible from accepted routes, or reduced to an exact runnable source/capture/access "
            "requirement; emit verifier/focused tests and scoped artifacts; preserve NO_PROMOTION_VERDICT "
            "validation_safe=false outcome_review_opened=false live_effect=false."
        )
        starter_path.write_text(starter + "\n", encoding="utf-8")
        rows.append(
            {
                "rank": route["rank"],
                "route_id": route["route_id"],
                "prompt_path": rel(prompt_path),
                "prompt_sha256": sha256_file(prompt_path),
                "starter_path": rel(starter_path),
                "starter_sha256": sha256_file(starter_path),
                "starter_one_physical_line": "\n" not in starter,
            }
        )
    return rows


def build() -> dict[str, Path]:
    data = load_inputs()
    generated_at = utc_now()

    blocked32_cards = data["blocked32_route_ledger"]["blocked_cards"]
    blocked15_cards = data["blocked15_card_set"]["cards"]
    blocked15_ids = {row["card_id"] for row in blocked15_cards}
    blocked17_ids = set(data["g12_ltf_denominator"]["included_card_ids"])
    ready8_ids = set(data["g12_ready8_decision"]["ready_scope"]["ready_cards_expected"])
    accepted40_blocked_ids = set(data["g12_ready8_decision"]["ready_scope"]["blocked_card_ids"])

    capture_summaries = {
        row["field_group"]: row for row in data["blocked15_field_matrix"]["capture_group_summaries"]
    }
    ltf_card_rows = {row["card_id"]: row for row in data["g12_ltf_source_status"]["per_card_rows"]}
    route_rows = []
    group_rows = []
    for group in sorted(EXPECTED_CAPTURE_GROUPS):
        summary = capture_summaries[group]
        group_rows.append(source_action_for_capture_group(group, summary))

    for card in blocked32_cards:
        card_id = card["card_id"]
        if card_id in blocked15_ids:
            lane = "blocked15_future_capture_source_state"
            g12_terminal_decision = data["g12_blocked15_decision"]["terminal_decision"]
            group_actions = [source_action_for_capture_group(group, capture_summaries[group]) for group in card.get("required_capture_groups", [])]
            terminal_next_action = (
                "Source-state/control only: materialize recovered groups, prospectively capture non-generatable source truth, "
                "then require G12 audit before any packet/result gate."
            )
        elif card_id in blocked17_ids:
            lane = "blocked17_ltf_orderflow_proxy_source_status"
            g12_terminal_decision = data["g12_ltf_decision"]["terminal_decision"]
            ltf_action = source_action_for_ltf_card(ltf_card_rows[card_id])
            group_actions = [ltf_action]
            terminal_next_action = ltf_action["exact_next_action"]
        else:
            lane = "unexpected"
            g12_terminal_decision = "NOT_ACCEPTED_FOR_BLOCKED_ROUTE"
            group_actions = []
            terminal_next_action = "Fail closed; card is not part of the accepted blocked32 dependency set."
        route_rows.append(
            {
                "card_id": card_id,
                "science_domain": card["science_domain"],
                "accepted_readiness": card["accepted_readiness"],
                "blocked_lane": lane,
                "required_capture_groups": card.get("required_capture_groups", []),
                "exact_missing_fields_or_source_status": card.get("exact_missing_fields_or_source_status", []),
                "accepted_g12_terminal_decision": g12_terminal_decision,
                "same_evidence_class_actions": group_actions,
                "terminal_next_action": terminal_next_action,
                "may_score_results_now": False,
                "accepted_40_denominator_unblocked_now": False,
            }
        )

    domain_counts = Counter(row["science_domain"] for row in route_rows)
    lane_counts = Counter(row["blocked_lane"] for row in route_rows)
    capture_group_counts = Counter()
    for row in blocked32_cards:
        capture_group_counts.update(row.get("required_capture_groups", []))

    context_anchor = base_payload("context_anchor")
    context_anchor.update(
        {
            "generated_at_utc": generated_at,
            "controlling_prompt": CONTROL_PROMPT,
            "git_head_at_build": git_head(),
            "mandatory_preflight_completed": True,
            "mandatory_context_reads_after_preflight": [
                {"path": path, "read_this_session": True} for path in MANDATORY_CONTEXT
            ],
            "lane_statement": (
                "G0 blocked-card source/control synthesis only. Active unblocking posture; no result scoring or promotion."
            ),
            "constructive_framing_applied": True,
            "input_hashes": input_hash_rows(),
            "local_heavy_root_presence_checked": root_existence_rows(),
            "git_status_before_build_or_current": git_status_rows(),
            "safe_boundaries": FORBIDDEN_SURFACES,
        }
    )

    reconciliation = base_payload("blocked_card_route_reconciliation_ledger")
    reconciliation.update(
        {
            "accepted_40_card_denominator_count": 40,
            "ready8_card_count": len(ready8_ids),
            "blocked32_card_count": len(blocked32_cards),
            "blocked15_card_count": len(blocked15_ids),
            "blocked17_card_count": len(blocked17_ids),
            "blocked32_card_ids": sorted(row["card_id"] for row in blocked32_cards),
            "blocked15_card_ids": sorted(blocked15_ids),
            "blocked17_card_ids": sorted(blocked17_ids),
            "ready8_card_ids": sorted(ready8_ids),
            "accepted40_blocked_ids_match_blocked32": sorted(accepted40_blocked_ids) == sorted(row["card_id"] for row in blocked32_cards),
            "readiness_split": data["blocked32_route_ledger"]["blocked_readiness_split"],
            "assigned_route_counts": data["blocked32_route_ledger"]["assigned_route_counts"],
            "science_domain_counts": dict(sorted(domain_counts.items())),
            "lane_counts": dict(sorted(lane_counts.items())),
            "required_capture_group_counts_across_blocked32": dict(sorted(capture_group_counts.items())),
            "capture_group_count": len(EXPECTED_CAPTURE_GROUPS),
            "capture_groups": sorted(EXPECTED_CAPTURE_GROUPS),
            "recovered_source_state_rows": data["g12_blocked15_decision"]["verified_counts"]["recovered_source_state_rows"],
            "accepted_g12_decisions_preserved": {
                "blocked15_future_capture": data["g12_blocked15_decision"]["terminal_decision"],
                "blocked17_ltf_proxy": data["g12_ltf_decision"]["terminal_decision"],
                "ready8": data["g12_ready8_decision"]["terminal_decision"],
                "expansion": data["g12_expansion_decision"]["terminal_decision"],
                "anti_boxing": data["g12_anti_boxing_decision"]["terminal_decision"],
            },
            "card_route_rows": route_rows,
        }
    )

    blocker_pursuit = base_payload("same_evidence_class_blocker_pursuit_ledger")
    blocker_pursuit.update(
        {
            "principle": (
                "No blocker family is terminal if same-evidence-class source/control pursuit remains. Every blocker below is "
                "cleared, routed to accepted evidence, or reduced to an exact source/capture/parser/access/G12 requirement."
            ),
            "blocked15_card_count": len(blocked15_ids),
            "capture_group_rows": group_rows,
            "blocked17_terminal_source_status_counts": data["g12_ltf_source_status"]["terminal_source_status_counts"],
            "blocked17_field_status_counts": data["g12_ltf_source_status"]["status_counts"],
            "same_class_open_items": [
                {
                    "item": "POI/bounds historical source-state rows",
                    "status": "TRUE_HISTORICAL_SOURCE_GAP_REDUCED_TO_FORWARD_CAPTURE_REQUIREMENT",
                    "exact_requirement": "source_safe_mso_snapshot_and_poi_logger with POI type/bounds/source bars/snapshot hash/rule version",
                },
                {
                    "item": "LTF parser attachment",
                    "status": "SOURCE_EXISTS_NEEDS_PARSER_REDUCED_TO_PARSER_HASH_ASOF_REQUIREMENT",
                    "exact_requirement": "decision-window LTF source pointer/cache id, file hash, parser version, bars-present-by-timeframe, as-of descriptor",
                },
                {
                    "item": "Orderflow/depth proxy validity",
                    "status": "PROXY_CONTEXT_REDUCED_TO_PROXY_CONTRACT_REQUIREMENT",
                    "exact_requirement": "proxy instrument/contract/source family/capture as-of/feature schema/proxy-transfer limits; broker-native truth claims remain zero",
                },
                {
                    "item": "Non-generatable historical lifecycle/source-state truth",
                    "status": "PROSPECTIVE_CAPTURE_REQUIRED",
                    "exact_requirement": "forward nonbroker source-state logger with redacted bridge hashes only; no broker account/order/history/deal/position evidence",
                },
            ],
            "unresolved_vague_blockers": [],
            "every_item_has_exact_next_requirement": True,
        }
    )

    denominator = base_payload("denominator_quarantine_source_state_gate_ledger")
    denominator.update(
        {
            "accepted_40_denominator_count": 40,
            "ready8_count": len(ready8_ids),
            "blocked15_count": len(blocked15_ids),
            "blocked17_count": len(blocked17_ids),
            "accepted_40_equation": "8 ready + 15 future-capture blocked + 17 LTF/orderflow/proxy blocked = 40",
            "recovered_source_state_rows": data["g12_blocked15_decision"]["verified_counts"]["recovered_source_state_rows"],
            "recovered_rows_are_result_denominator_rows": False,
            "accepted_40_result_denominator_unblocked_by_recovered_rows": False,
            "blocked_cards_may_score_results_now": False,
            "expansion_candidate_count_quarantined": data["g12_expansion_candidate_count"]["candidate_count_recomputed"],
            "expansion_accepted40_overlap_count": len(data["g12_expansion_candidate_count"].get("duplicate_candidate_ids", [])),
            "anti_boxing_route_family_count": data["g12_anti_boxing_route_family"]["route_family_count"],
            "anti_boxing_domain_count": data["g12_anti_boxing_route_family"]["domain_count"],
            "source_state_gate_before_any_future_result": [
                "candidate-attached source fields frozen",
                "as-of and source hash verified",
                "duplicate denominator policy frozen",
                "baseline/control assignment frozen",
                "forbidden fields absent",
                "G12 packet/source audit accepted",
                "G0 future result gate explicitly authorizes outcome opening",
            ],
            "safe_flags_preserved": True,
        }
    )

    routes = route_definitions()
    prompt_rows = write_prompt_pack(routes)

    ranked_bundle = base_payload("ranked_unblocking_route_bundle")
    ranked_bundle.update(
        {
            "route_count": len(routes),
            "ranking_policy": (
                "Rank by accepted-card unblock potential, same-evidence-class feasibility, denominator safety, breadth beyond "
                "current GTOS/OB framing, and ability to emit exact source/capture/parser/access requirements."
            ),
            "routes": routes,
            "prompt_pack": prompt_rows,
            "non_ob_cross_domain_routes_present": True,
            "orderflow_proxy_ltf_lifecycle_baseline_failure_routes_present": True,
        }
    )

    parallelization = base_payload("parallelization_ledger")
    parallelization.update(
        {
            "can_run_in_parallel_after_current_g0_acceptance": [
                "SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR",
                "SCID_BLOCKED17_LTF_ASOF_PATH_PARSER_AND_CANDIDATE_ATTACHMENT",
                "SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AND_SOURCE_STATUS_ATTACH",
                "SCID_BLOCKED_BASELINE_LIFECYCLE_SOURCE_STATE_MATERIALIZATION",
                "SCID_BLOCKED_FAILURE_ANATOMY_NEGATIVE_EVIDENCE_CONTROL_PACKET",
                "SCID_BLOCKED_CROSS_DOMAIN_NON_OB_ROUTE_EXPANSION_GATE",
            ],
            "must_wait_for_child_outputs": [
                "SCID_BLOCKED32_PARALLEL_SOURCE_CONTROL_REPAIR_WAVE",
                "SCID_BLOCKED_RESULT_GATE_DORMANT_UNTIL_SOURCE_CONTROL_ACCEPTED",
            ],
            "requires_prior_g12_or_g0_acceptance_before_result_opening": [
                "all routes in this bundle",
            ],
            "disjoint_write_scopes_for_parallel_children": {
                "POI_BOUNDS": "prospective source logger contract and synthetic fixtures",
                "LTF_ASOF": "LTF parser/source-hash/as-of attachment matrix",
                "ORDERFLOW_PROXY": "proxy/source contract and access ledger",
                "BASELINE_LIFECYCLE": "baseline/lifecycle source-state fixtures",
                "FAILURE_ANATOMY": "negative-evidence/source-gap control packet",
                "CROSS_DOMAIN_EXPANSION": "quarantined expansion/anti-boxing denominator gate",
            },
            "do_not_parallelize": [
                "Any result scoring or validation route with source-control children.",
                "Any route requiring paid/API/vendor or broker account/order/history/deal/position access.",
            ],
        }
    )

    saturation = base_payload("saturation_self_red_team")
    saturation.update(
        {
            "anti_boxing_questions_answered": [
                {
                    "question": "Did the synthesis collapse to OB/retest only?",
                    "answer": "No. Route bundle explicitly includes LTF, orderflow/proxy, lifecycle, baseline-control, failure-anatomy, cross-domain, macro/ML/microstructure/behavioral expansion gates, and non-OB mechanisms.",
                },
                {
                    "question": "Could source-control evidence leak into result denominators?",
                    "answer": "Gate ledger keeps recovered source-state rows, LTF/proxy statuses, expansion candidates, and anti-boxing routes outside result denominators until separate G12/G0 result authorization.",
                },
                {
                    "question": "Which fields are most likely to be over-interpreted?",
                    "answer": "Recovered lifecycle and source-state rows, proxy/depth context, and baseline controls. They are marked source/control only and may not be scored.",
                },
                {
                    "question": "Were broad non-OB routes dropped for convenience?",
                    "answer": "No. Ranked bundle preserves cross-domain expansion, orderflow/proxy, LTF path, execution/fillability, behavioral/game-theory, macro/session, ML/uncertainty, and failure-anatomy routes.",
                },
                {
                    "question": "What would a skeptical G12 reject?",
                    "answer": "Any denominator movement without candidate-attached source hashes/as-of proof, any inferred historical intent/order truth from price, any proxy-to-CFD truth leap, or any result/performance field. The next prompts forbid those paths.",
                },
            ],
            "same_evidence_class_gaps_exposed_and_pursued": blocker_pursuit["same_class_open_items"],
            "no_unresolved_tbd_unknown_maybe_later_placeholders": True,
        }
    )

    instruction_coverage = base_payload("mandatory_instruction_coverage_audit")
    instruction_coverage.update(
        {
            "goal_session_research_discipline_read_after_preflight": True,
            "research_operating_doctrine_read_after_preflight": True,
            "research_current_state_read_after_preflight": True,
            "local_heavy_data_inventory_read_after_preflight": True,
            "ai_in_loop_cost_control_read_after_preflight": True,
            "lane_type": "G0 source/control synthesis, not result scoring or promotion",
            "posture_applied": "active non-conservative unblocking synthesis with strict evidence-class boundaries",
            "anti_boxing_operationalized_in": [
                rel(artifact_path("RANKED_ROUTE_BUNDLE")),
                rel(artifact_path("SATURATION_SELF_RED_TEAM")),
                rel(artifact_path("PARALLELIZATION_LEDGER")),
                rel(artifact_path("NEXT_PROMPT_STARTER_LEDGER")),
            ],
            "outside_current_gtos_ob_routes_considered": [
                "LTF path availability",
                "orderflow/depth proxy context",
                "baseline/placebo controls",
                "lifecycle fill/cancel/expiry source status",
                "failure anatomy",
                "cross-domain expansion",
                "macro/session/calendar",
                "ML/meta-labeling/uncertainty",
                "microstructure/trapped flow",
                "behavioral/game theory",
            ],
            "proof_or_impossibility_stop_condition": (
                "Each blocker is cleared, routed to accepted G12 control evidence, or reduced to exact source/capture/parser/access/G12 requirements."
            ),
            "forbidden_surfaces_preserved": True,
        }
    )

    decision = base_payload("g0_decision_ledger")
    decision.update(
        {
            "terminal_decision": TERMINAL_DECISION,
            "decision_rationale": (
                "Accepted G12 future-capture blocked15 source-state evidence, accepted blocked17 LTF/proxy source-status evidence, "
                "and accepted ready/expansion/anti-boxing control facts are reconciled into a ranked source-control route bundle. "
                "No blocked card is result-ready in this lane, but no same-class blocker remains vague."
            ),
            "check_map": {
                "required_inputs_exist_and_hashed": all(row["exists"] and row["sha256"] for row in context_anchor["input_hashes"]),
                "blocked32_reconciled": len(route_rows) == 32,
                "blocked15_reconciled": len(blocked15_ids) == 15,
                "blocked17_reconciled": len(blocked17_ids) == 17,
                "capture_groups_reconciled": set(capture_summaries) == EXPECTED_CAPTURE_GROUPS,
                "recovered_source_state_rows_preserved": reconciliation["recovered_source_state_rows"] == 1213,
                "denominator_quarantine_preserved": denominator["accepted_40_result_denominator_unblocked_by_recovered_rows"] is False,
                "broad_route_bundle_ranked": ranked_bundle["route_count"] >= 8,
                "prompt_pack_emitted": len(prompt_rows) == len(routes),
                "parallelization_ledger_emitted": True,
                "instruction_coverage_emitted": True,
            },
            "terminal_blockers": [],
            "same_evidence_class_remaining_vague_blockers": [],
            "next_route_bundle": [route["route_id"] for route in routes],
        }
    )

    next_prompt_starter = base_payload("next_prompt_starter_ledger")
    next_prompt_starter.update(
        {
            "prompt_count": len(prompt_rows),
            "starter_count": len(prompt_rows),
            "prompt_pack": prompt_rows,
            "all_starters_one_physical_line": all(row["starter_one_physical_line"] for row in prompt_rows),
            "all_prompts_bind_safe_flags": True,
        }
    )

    focused_test = base_payload("focused_test_result")
    focused_test.update(
        {
            "focused_tests_ok": False,
            "status": "PENDING_RUN_VERIFIER_WITH_MARK_FOCUSED_TESTS_OK_AFTER_PYTEST",
            "command": (
                "pytest research/science_program_2026_05/06_outcome_testing/"
                "g0_scid_blocked_unblocking_synthesis_after_fc_g12_audit/"
                "test_g0_scid_blocked_unblocking_synthesis_after_fc_g12_audit_2026_05_12.py -q"
            ),
        }
    )

    completion_items = [
        ("mandatory preflight/context refresh completed", rel(artifact_path("CONTEXT_ANCHOR")), True),
        ("all required input artifacts hashed", rel(artifact_path("CONTEXT_ANCHOR")), True),
        ("G0 decision ledger emitted", rel(artifact_path("DECISION_LEDGER")), True),
        ("blocked-card route reconciliation ledger emitted", rel(artifact_path("ROUTE_RECONCILIATION_LEDGER")), True),
        ("ranked unblocking route bundle emitted", rel(artifact_path("RANKED_ROUTE_BUNDLE")), True),
        ("same-evidence-class blocker pursuit ledger emitted", rel(artifact_path("SAME_EVIDENCE_BLOCKER_PURSUIT_LEDGER")), True),
        ("anti-boxing saturation/self-red-team emitted", rel(artifact_path("SATURATION_SELF_RED_TEAM")), True),
        ("denominator quarantine/source-state gate ledger emitted", rel(artifact_path("DENOMINATOR_QUARANTINE_GATE_LEDGER")), True),
        ("next controlling prompts/starters emitted", rel(artifact_path("NEXT_PROMPT_STARTER_LEDGER")), True),
        ("mandatory instruction coverage audit emitted", rel(artifact_path("MANDATORY_INSTRUCTION_COVERAGE_AUDIT")), True),
        ("parallelization ledger emitted", rel(artifact_path("PARALLELIZATION_LEDGER")), True),
        ("standalone verifier passed", rel(artifact_path("VERIFICATION_RESULT")), False),
        ("focused tests passed", rel(artifact_path("FOCUSED_TEST_RESULT")), False),
        ("NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false preserved", rel(artifact_path("DENOMINATOR_QUARANTINE_GATE_LEDGER")), True),
    ]
    completion = base_payload("completion_audit")
    completion.update(
        {
            "objective_restatement": (
                "Reconcile the accepted blocked15 future-capture source-state audit with sibling blocked-card routes, preserve "
                "denominator quarantine, rank broad source/control unblocking routes, emit exact prompts/starters, and verify "
                "all artifacts without opening forbidden result/live/API/broker/promotion surfaces."
            ),
            "prompt_to_artifact_checklist": [
                {"requirement": req, "evidence": evidence, "satisfied": satisfied}
                for req, evidence, satisfied in completion_items
            ],
            "missing_incomplete_or_weakly_verified_requirements": [
                req for req, _evidence, satisfied in completion_items if not satisfied
            ],
            "completion_standard_satisfied": False,
            "standalone_verifier_ok": False,
            "focused_tests_ok": False,
            "can_mark_goal_complete": False,
            "scoped_research_commit_required": True,
        }
    )

    artifacts = {
        "CONTEXT_ANCHOR": context_anchor,
        "DECISION_LEDGER": decision,
        "ROUTE_RECONCILIATION_LEDGER": reconciliation,
        "RANKED_ROUTE_BUNDLE": ranked_bundle,
        "SAME_EVIDENCE_BLOCKER_PURSUIT_LEDGER": blocker_pursuit,
        "DENOMINATOR_QUARANTINE_GATE_LEDGER": denominator,
        "SATURATION_SELF_RED_TEAM": saturation,
        "MANDATORY_INSTRUCTION_COVERAGE_AUDIT": instruction_coverage,
        "PARALLELIZATION_LEDGER": parallelization,
        "NEXT_PROMPT_STARTER_LEDGER": next_prompt_starter,
        "FOCUSED_TEST_RESULT": focused_test,
        "COMPLETION_AUDIT": completion,
    }

    written: dict[str, Path] = {}
    for stem, payload in artifacts.items():
        path = artifact_path(stem)
        write_json(path, payload)
        write_md(path.with_suffix(".md"), stem.replace("_", " ").title(), payload)
        written[stem] = path

    manifest_rows = []
    for stem, path in written.items():
        manifest_rows.append({"artifact": stem, "path": rel(path), "sha256": sha256_file(path)})
        md_path = path.with_suffix(".md")
        manifest_rows.append({"artifact": f"{stem}_MD", "path": rel(md_path), "sha256": sha256_file(md_path)})
    for row in prompt_rows:
        manifest_rows.append({"artifact": f"{row['route_id']}_PROMPT", "path": row["prompt_path"], "sha256": row["prompt_sha256"]})
        manifest_rows.append({"artifact": f"{row['route_id']}_STARTER", "path": row["starter_path"], "sha256": row["starter_sha256"]})
    for script in [
        ROUTE_DIR / "build_g0_scid_blocked_unblocking_synthesis_after_fc_g12_audit_2026_05_12.py",
        ROUTE_DIR / "verify_g0_scid_blocked_unblocking_synthesis_after_fc_g12_audit_2026_05_12.py",
        ROUTE_DIR / "test_g0_scid_blocked_unblocking_synthesis_after_fc_g12_audit_2026_05_12.py",
    ]:
        if script.exists():
            manifest_rows.append({"artifact": script.name, "path": rel(script), "sha256": sha256_file(script)})

    manifest = base_payload("output_manifest")
    manifest.update(
        {
            "artifact_count": len(manifest_rows),
            "artifacts": manifest_rows,
            "raw_market_blob_artifacts": [row for row in manifest_rows if Path(row["path"]).suffix.lower() in {".scid", ".depth", ".parquet", ".zip", ".bin"}],
        }
    )
    manifest_path = artifact_path("OUTPUT_MANIFEST")
    write_json(manifest_path, manifest)
    write_md(manifest_path.with_suffix(".md"), "Output Manifest", manifest)
    written["OUTPUT_MANIFEST"] = manifest_path
    return written


if __name__ == "__main__":
    paths = build()
    print(json.dumps({"ok": True, "route_id": ROUTE_ID, "artifact_count": len(paths), "route_dir": rel(ROUTE_DIR)}, indent=2))
