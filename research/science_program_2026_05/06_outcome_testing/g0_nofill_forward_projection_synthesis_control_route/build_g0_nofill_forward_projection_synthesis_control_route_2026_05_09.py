"""Build G0 NOFILL forward projection synthesis/control artifacts.

This lane is research/control design only. It consumes accepted source-control
projection evidence and emits implementation-design requirements without
opening result scoring, validation, promotion, live wiring, paid/API routes, or
live trading behavior.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


BASE = Path(__file__).resolve().parent
REPO_ROOT = BASE.parents[3]
DATE = "2026-05-09"
ROUTE_ID = "G0_NOFILL_FORWARD_PROJECTION_SYNTHESIS_CONTROL_ROUTE"
SCHEMA_VERSION = "g0_nofill_forward_projection_synthesis_control_route_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"


UPSTREAM = {
    "g12_repair_completion": "research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_projection_repair_reaudit/G12_NOFILL_FORWARD_PROJECTION_REPAIR_COMPLETION_AUDIT_2026-05-09.json",
    "g12_repair_no_leak": "research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_projection_repair_reaudit/G12_NOFILL_FORWARD_PROJECTION_REPAIR_NO_LEAK_AUDIT_2026-05-09.json",
    "g12_repair_source_hash": "research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_projection_repair_reaudit/G12_NOFILL_FORWARD_PROJECTION_REPAIR_SOURCE_HASH_AUDIT_2026-05-09.json",
    "projection_denom": "research/science_program_2026_05/06_outcome_testing/nofill_forward_source_safe_projection_builder/NOFILL_FORWARD_DENOMINATOR_AND_EXCLUSION_AUDIT_2026-05-09.json",
    "projection_missing": "research/science_program_2026_05/06_outcome_testing/nofill_forward_source_safe_projection_builder/NOFILL_FORWARD_MISSING_STATUS_LEDGER_2026-05-09.json",
    "projection_allowlist": "research/science_program_2026_05/06_outcome_testing/nofill_forward_source_safe_projection_builder/NOFILL_FORWARD_ALLOWLIST_PROJECTION_SPEC_2026-05-09.json",
    "addendum_schema": "research/science_program_2026_05/06_outcome_testing/nofill_forward_contract_addendum_projection_plan/NOFILL_FORWARD_PROJECTION_FIELD_SCHEMA_2026-05-09.json",
    "addendum_latency": "research/science_program_2026_05/06_outcome_testing/nofill_forward_contract_addendum_projection_plan/NOFILL_FORWARD_LATENCY_CLOCK_SKEW_CAPTURE_SPEC_2026-05-09.json",
    "addendum_spread": "research/science_program_2026_05/06_outcome_testing/nofill_forward_contract_addendum_projection_plan/NOFILL_FORWARD_SPREAD_SLIPPAGE_EXECUTION_QUALITY_STATUS_SPEC_2026-05-09.json",
    "g12_forward_schema_audit": "research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_lifecycle_capture_contract_audit/G12_NOFILL_FORWARD_SCHEMA_AUDIT_2026-05-09.json",
    "g12_forward_decision": "research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_lifecycle_capture_contract_audit/G12_NOFILL_FORWARD_DECISION_LEDGER_2026-05-09.json",
    "g0_cat_route_ranking": "research/science_program_2026_05/06_outcome_testing/g0_nofill_cat_v3_categorical_evidence_synthesis_control_review/G0_NOFILL_CAT_V3_NEXT_ROUTE_RANKING_2026-05-09.json",
    "g0_cat_backlog": "research/science_program_2026_05/06_outcome_testing/g0_nofill_cat_v3_categorical_evidence_synthesis_control_review/G0_NOFILL_CAT_V3_SOURCE_CONTRACT_AND_CAPTURE_BACKLOG_2026-05-09.json",
}


REQUIRED_MD = [
    "G0_NOFILL_FORWARD_PROJECTION_CONTEXT_ANCHOR_2026-05-09.md",
    "G0_NOFILL_FORWARD_PROJECTION_DECISION_LEDGER_2026-05-09.md",
    "G0_NOFILL_FORWARD_PROJECTION_EVIDENCE_CHAIN_RECONCILIATION_2026-05-09.md",
    "G0_NOFILL_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_RANKING_2026-05-09.md",
    "G0_NOFILL_FORWARD_SOURCE_COST_EXECUTION_SEPARATION_LEDGER_2026-05-09.md",
    "G0_NOFILL_FORWARD_DUPLICATE_AND_DENOMINATOR_CONTROL_REVIEW_2026-05-09.md",
    "G0_NOFILL_FORWARD_HOSTILE_REVIEW_AND_FAILURE_MODE_LEDGER_2026-05-09.md",
    "G0_NOFILL_FORWARD_FORBIDDEN_ROUTE_LEDGER_2026-05-09.md",
    "G0_NOFILL_FORWARD_NEXT_PROMPT_PACK_2026-05-09.md",
    "G0_NOFILL_FORWARD_COMPLETION_AUDIT_2026-05-09.md",
]

REQUIRED_JSON = [
    "G0_NOFILL_FORWARD_PROJECTION_FIELD_REQUIREMENT_MATRIX_2026-05-09.json",
    "G0_NOFILL_FORWARD_CAPTURE_SCHEMA_REQUIREMENTS_2026-05-09.json",
    "G0_NOFILL_FORWARD_COMPLETION_AUDIT_2026-05-09.json",
]


FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "config/",
    "prompts/",
    "scripts/",
    "tests/",
    "run_agent.py",
    "start_all.bat",
)

FORBIDDEN_VALUE_TOKENS = [
    "broker_actual_r",
    "actual_r",
    "synthetic_path_r",
    "win_rate",
    "expectancy",
    "r_multiple",
    "slippage_price",
    "mt5_order_ticket",
    "pending_ticket",
    "mt5_deal_id",
    "mt5_position_id",
    "account_history",
    "order_send_success",
    "broker_fill_state",
]


LIFECYCLE_REQUIRED_FIELDS = [
    {
        "field_name": "pending_intent_created_utc",
        "field_family": "pending_lifecycle",
        "requirement_level": "mandatory",
        "source_asof_rule": "Captured at intent creation; never reconstructed from fill or order history.",
        "missing_policy": "fail_closed_missing_status",
    },
    {
        "field_name": "pending_horizon_start_utc",
        "field_family": "pending_lifecycle",
        "requirement_level": "mandatory",
        "source_asof_rule": "Frozen from the pending intent source row.",
        "missing_policy": "fail_closed_missing_status",
    },
    {
        "field_name": "pending_horizon_end_utc",
        "field_family": "pending_lifecycle",
        "requirement_level": "mandatory",
        "source_asof_rule": "Frozen from cancel/expiry policy at decision time.",
        "missing_policy": "fail_closed_missing_status",
    },
    {
        "field_name": "cancel_expiry_utc",
        "field_family": "pending_lifecycle",
        "requirement_level": "mandatory_with_status",
        "source_asof_rule": "Source-safe cancel/expiry timestamp only; not a broker-result label.",
        "missing_policy": "explicit_not_observed_or_missing_status",
    },
    {
        "field_name": "cancel_expiry_reason_status",
        "field_family": "pending_lifecycle",
        "requirement_level": "mandatory",
        "source_asof_rule": "Closed categorical source reason such as horizon_expired, stale_poi, or unavailable.",
        "missing_policy": "fail_closed_missing_status",
    },
    {
        "field_name": "entry_touch_first_utc",
        "field_family": "entry_touch_observability",
        "requirement_level": "mandatory_with_status",
        "source_asof_rule": "First side-aware entry touch from tick/lower-TF path source, or explicit no-touch proof.",
        "missing_policy": "explicit_no_touch_or_missing_status",
    },
    {
        "field_name": "side_aware_entry_touch_status",
        "field_family": "entry_touch_observability",
        "requirement_level": "mandatory",
        "source_asof_rule": "BUY uses ask-side touch, SELL uses bid-side touch; never midpoint-only unless flagged.",
        "missing_policy": "fail_closed_if_quote_side_unknown",
    },
    {
        "field_name": "terminal_area_touch_status",
        "field_family": "terminal_area_observability",
        "requirement_level": "mandatory",
        "source_asof_rule": "Categorical terminal-area touch/no-touch/ambiguous status from source-safe path window.",
        "missing_policy": "fail_closed_missing_status",
    },
    {
        "field_name": "terminal_area_first_touch_utc",
        "field_family": "terminal_area_observability",
        "requirement_level": "mandatory_with_status",
        "source_asof_rule": "First source-safe terminal-area touch timestamp; null only with no-touch or missing proof.",
        "missing_policy": "explicit_no_touch_or_missing_status",
    },
    {
        "field_name": "protective_area_touch_status",
        "field_family": "terminal_area_observability",
        "requirement_level": "mandatory",
        "source_asof_rule": "Protective/stop-area touch status is captured as path context, not R outcome.",
        "missing_policy": "fail_closed_missing_status",
    },
    {
        "field_name": "protective_area_first_touch_utc",
        "field_family": "terminal_area_observability",
        "requirement_level": "mandatory_with_status",
        "source_asof_rule": "First source-safe protective-area touch timestamp, preserving same-tick ambiguity.",
        "missing_policy": "explicit_no_touch_or_missing_status",
    },
    {
        "field_name": "event_order_resolution_method",
        "field_family": "event_order_resolution",
        "requirement_level": "mandatory",
        "source_asof_rule": "Records tick, lower-TF, same-bar ambiguous, or source-impossible resolution method.",
        "missing_policy": "fail_closed_ambiguous_or_impossible",
    },
    {
        "field_name": "same_tick_same_bar_ambiguity_status",
        "field_family": "event_order_resolution",
        "requirement_level": "mandatory",
        "source_asof_rule": "Must preserve ambiguity instead of choosing entry, terminal, or protective ordering.",
        "missing_policy": "fail_closed_ambiguous",
    },
    {
        "field_name": "lower_tf_coverage_window_start_utc",
        "field_family": "source_coverage",
        "requirement_level": "mandatory",
        "source_asof_rule": "Coverage start for the source used to prove touch/no-touch.",
        "missing_policy": "fail_closed_missing_status",
    },
    {
        "field_name": "lower_tf_coverage_window_end_utc",
        "field_family": "source_coverage",
        "requirement_level": "mandatory",
        "source_asof_rule": "Coverage end for the source used to prove touch/no-touch.",
        "missing_policy": "fail_closed_missing_status",
    },
    {
        "field_name": "missing_coverage_intervals",
        "field_family": "source_coverage",
        "requirement_level": "mandatory",
        "source_asof_rule": "Explicit coverage gaps; absent gaps must be represented as an empty source-hashed list.",
        "missing_policy": "fail_closed_if_unknown",
    },
    {
        "field_name": "row_level_denominator_member",
        "field_family": "duplicate_denominator",
        "requirement_level": "mandatory",
        "source_asof_rule": "Accepted-first row-level denominator membership from frozen source-control packet.",
        "missing_policy": "fail_closed_missing_denominator_control",
    },
    {
        "field_name": "nofill_duplicate_key_count_member",
        "field_family": "duplicate_denominator",
        "requirement_level": "mandatory",
        "source_asof_rule": "Primary duplicate-key membership after accepted-first filtering.",
        "missing_policy": "fail_closed_missing_denominator_control",
    },
    {
        "field_name": "duplicate_group_id_count_member",
        "field_family": "duplicate_denominator",
        "requirement_level": "mandatory",
        "source_asof_rule": "Secondary duplicate-group membership after accepted-first filtering.",
        "missing_policy": "fail_closed_missing_denominator_control",
    },
    {
        "field_name": "nofill_duplicate_key_sha256",
        "field_family": "duplicate_denominator",
        "requirement_level": "mandatory",
        "source_asof_rule": "SHA256-only duplicate key; raw duplicate key text must not be emitted.",
        "missing_policy": "fail_closed_missing_hash",
    },
    {
        "field_name": "duplicate_group_id_sha256",
        "field_family": "duplicate_denominator",
        "requirement_level": "mandatory",
        "source_asof_rule": "SHA256-only duplicate group; raw group text must not be emitted.",
        "missing_policy": "fail_closed_missing_hash",
    },
    {
        "field_name": "session_tag",
        "field_family": "regime_session_review_control",
        "requirement_level": "mandatory",
        "source_asof_rule": "Decision-time session/kill-zone tag, never post-outcome grouping.",
        "missing_policy": "fail_closed_missing_status",
    },
    {
        "field_name": "regime_context_status",
        "field_family": "regime_session_review_control",
        "requirement_level": "mandatory_with_status",
        "source_asof_rule": "Decision-time regime/context status if already source-safe; otherwise explicit unavailable status.",
        "missing_policy": "explicit_unavailable_or_missing_status",
    },
    {
        "field_name": "sample_floor_policy_id",
        "field_family": "regime_session_review_control",
        "requirement_level": "mandatory",
        "source_asof_rule": "Frozen sample-floor policy identifier for later review compatibility, not a promotion claim.",
        "missing_policy": "fail_closed_missing_policy",
    },
    {
        "field_name": "perturbation_ready_bucket",
        "field_family": "regime_session_review_control",
        "requirement_level": "mandatory",
        "source_asof_rule": "Source-safe bucket keys needed for future perturbation/stress tests.",
        "missing_policy": "fail_closed_missing_status",
    },
    {
        "field_name": "kill_switch_observability_status",
        "field_family": "regime_session_review_control",
        "requirement_level": "mandatory",
        "source_asof_rule": "Status-only hook showing whether a future implementation can be reviewed without changing kill-switch behavior.",
        "missing_policy": "fail_closed_missing_status",
    },
    {
        "field_name": "source_artifact_hash",
        "field_family": "source_provenance",
        "requirement_level": "mandatory",
        "source_asof_rule": "SHA256 of every source artifact used by the row.",
        "missing_policy": "fail_closed_missing_hash",
    },
    {
        "field_name": "parser_code_hash",
        "field_family": "source_provenance",
        "requirement_level": "mandatory",
        "source_asof_rule": "SHA256 of parser/verifier code version that projected the row.",
        "missing_policy": "fail_closed_missing_hash",
    },
    {
        "field_name": "forbidden_field_scan_status",
        "field_family": "no_leak_control",
        "requirement_level": "mandatory",
        "source_asof_rule": "Pass/fail scan over output keys and values before any artifact is accepted.",
        "missing_policy": "fail_closed",
    },
]


def repo_rel(path: str) -> Path:
    return REPO_ROOT / path


def read_json(rel_path: str) -> Any:
    with repo_rel(rel_path).open(encoding="utf-8") as fh:
        return json.load(fh)


def write_json(name: str, data: Any) -> None:
    path = BASE / name
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(name: str, text: str) -> None:
    path = BASE / name
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def git_oneline() -> str:
    result = subprocess.run(
        ["git", "log", "-1", "--oneline"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN_HEAD"


def base_flags() -> dict[str, Any]:
    return {
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_result_scoring": False,
        "opens_live_wiring": False,
        "opens_paid_api_or_databento_route": False,
        "opens_registry_edit": False,
        "changes_live_trading_behavior": False,
    }


def projection_field_requirements(addendum_schema: dict[str, Any]) -> list[dict[str, Any]]:
    requirements: list[dict[str, Any]] = []
    for field in addendum_schema["fields"]:
        name = field["field_name"]
        req = field.get("required_or_optional", "required")
        family = field.get("schema_family", "unknown")
        level = "mandatory"
        if req == "optional_with_status":
            level = "optional_value_mandatory_status"
        elif "explicit_missing" in req:
            level = "mandatory_with_explicit_missing_status"
        elif name.endswith("_redaction_status") or name.endswith("_label_status"):
            level = "mandatory_closed_or_redaction_status"
        requirements.append(
            {
                "field_name": name,
                "field_family": family,
                "requirement_level": level,
                "required_or_optional_source": req,
                "source_asof_rule": field.get("source_asof_rule"),
                "missing_policy": field.get("null_missing_status_vocabulary", []),
                "hash_provenance_requirements": field.get("hash_provenance_requirements", []),
                "duplicate_denominator_effect": field.get("duplicate_denominator_effect"),
                "future_cost_or_execution_support": name
                in {
                    "decision_spread_status",
                    "decision_spread_value_source_safe",
                    "decision_spread_unit",
                    "entry_touch_spread_status",
                    "entry_touch_spread_value_source_safe",
                    "spread_source_hash",
                    "slippage_label_status",
                    "slippage_value_redaction_status",
                    "execution_quality_label_status",
                    "execution_quality_value_redaction_status",
                    "cost_testing_gate_status",
                },
                "result_or_cost_label_opened_now": False,
                "verifier_assertions": field.get("verifier_assertions", []),
            }
        )
    requirements.extend(LIFECYCLE_REQUIRED_FIELDS)
    return requirements


def route_ranking() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "route": "NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_HARDENING_AND_OFFLINE_PROJECTION_PROTOTYPE",
            "evidence_class": "source_control_design_and_offline_projection",
            "why": "It is the strongest next route because G12 accepted the repaired projection only as source/control evidence, while the remaining useful work is to freeze exact future capture fields, statuses, parser projections, fixtures, and verifiers before any live logger code is touched.",
            "allowed_now": True,
            "opens_result_scoring": False,
            "opens_live_wiring": False,
            "required_gate_before_live_wiring": "Owner-approved live-logger implementation lane after the source-capture contract/prototype passes a G12 acceptance audit.",
        },
        {
            "rank": 2,
            "route": "G12_NOFILL_FORWARD_CAPTURE_CONTRACT_ACCEPTANCE_AUDIT",
            "evidence_class": "independent_source_control_audit",
            "why": "The contract/prototype must be independently accepted before becoming canonical input for any future implementation plan.",
            "allowed_now": "after_rank_1_artifacts_exist",
            "opens_result_scoring": False,
            "opens_live_wiring": False,
            "required_gate_before_live_wiring": "G12 terminal acceptance of the source-capture contract and verifier coverage.",
        },
        {
            "rank": 3,
            "route": "OWNER_APPROVED_LIVE_LOGGER_WIRING_PLAN_PACKET",
            "evidence_class": "implementation_plan_requires_owner_approval",
            "why": "Useful as a plan only after source controls are accepted; actual code changes would touch live logger surfaces and need explicit owner approval.",
            "allowed_now": "plan_only",
            "opens_result_scoring": False,
            "opens_live_wiring": False,
            "plan_scope": "no_code_changes_in_this_g0_lane",
            "required_gate_before_live_wiring": "Explicit owner approval plus scoped implementation prompt naming files and fail-open behavior.",
        },
        {
            "rank": 4,
            "route": "OFFLINE_RESULT_OR_COST_SCORING_PACKET",
            "evidence_class": "future_result_cost_lane",
            "why": "It becomes relevant only after source-capture fields are frozen and source-safe input packets are accepted. It is forbidden in this G0 route.",
            "allowed_now": False,
            "opens_result_scoring": False,
            "would_cross_forbidden_gate": "result_cost_scoring",
            "opens_live_wiring": False,
            "required_gate_before_live_wiring": "Not a live-wiring gate; requires a separate result/cost lane.",
        },
        {
            "rank": 5,
            "route": "DIRECT_LIVE_LOGGER_WIRING_FROM_CURRENT_PROJECTION",
            "evidence_class": "forbidden_live_behavior_shortcut",
            "why": "Current evidence is accepted only as source/control projection evidence and cannot justify direct live logger code changes.",
            "allowed_now": False,
            "opens_result_scoring": False,
            "opens_live_wiring": False,
            "would_cross_forbidden_gate": "live_logger_wiring",
            "required_gate_before_live_wiring": "Rejected until rank 1 and rank 2 pass and owner opens a separate implementation lane.",
        },
    ]


def build_payload() -> dict[str, Any]:
    sources = {name: read_json(path) for name, path in UPSTREAM.items()}
    addendum_schema = sources["addendum_schema"]
    field_requirements = projection_field_requirements(addendum_schema)
    denom = sources["projection_denom"]
    missing = sources["projection_missing"]
    no_leak = sources["g12_repair_no_leak"]
    source_hash = sources["g12_repair_source_hash"]
    lifecycle_schema = sources["g12_forward_schema_audit"]
    g12_decision = sources["g12_forward_decision"]
    g12_completion = sources["g12_repair_completion"]
    flags = base_flags()

    schema_requirements = {
        "artifact": "G0_NOFILL_FORWARD_CAPTURE_SCHEMA_REQUIREMENTS",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "controlling_git_head": git_oneline(),
        **flags,
        "terminal_g12_source_projection_decision": g12_completion["terminal_decision"],
        "projection_partition": {
            "projection_row_count": denom["projection_row_count"],
            "family_counts": denom["family_counts"],
            "row_level_accepted_denominator": denom["row_level_accepted_denominator"],
            "primary_duplicate_key_denominator": denom["primary_duplicate_key_denominator"],
            "secondary_duplicate_group_denominator": denom["secondary_duplicate_group_denominator"],
            "reject_overlap_rows": denom["reject_overlap_rows"],
            "reject_overlap_denominator_effect": denom["reject_overlap_denominator_effect"],
        },
        "source_projection_usage_limits": [
            "Accepted only as source/control projection evidence.",
            "No result, cost, R, win-rate, expectancy, DSR, PBO, validation, promotion, or live behavior evidence.",
            "Source-control, source-impossible, and reject rows remain excluded from accepted denominators.",
            "Spread snapshots are source-safe quote observations only; slippage and execution-quality labels remain closed.",
        ],
        "route_ranking": route_ranking(),
        "future_capture_field_requirements": field_requirements,
        "forbidden_output_field_names": sorted(set(addendum_schema["forbidden_output_field_names"])),
        "future_owner_gate_before_live_wiring": {
            "required": True,
            "gate": "Explicit owner-approved implementation lane after source-capture contract/prototype and G12 acceptance.",
            "minimum_preconditions": [
                "G0 rank-1 source-capture contract/prototype artifacts exist.",
                "G12 acceptance audit verifies schema, redaction, no-leak, duplicate, denominator, timestamp, and source-hash controls.",
                "Implementation prompt names exact live logger files and requires fail-open/no-decision-impact behavior.",
                "No paid/API/MT5 account/order-history route is introduced without separate approval.",
            ],
        },
    }

    field_matrix = {
        "artifact": "G0_NOFILL_FORWARD_PROJECTION_FIELD_REQUIREMENT_MATRIX",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        **flags,
        "field_family_counts": {
            "addendum_projection_fields": addendum_schema["field_count"],
            "lifecycle_required_fields_added_by_g0": len(LIFECYCLE_REQUIRED_FIELDS),
            "total_future_capture_requirement_rows": len(field_requirements),
        },
        "missing_status_design_requirements": missing["exact_future_lane_requirements"],
        "current_missing_status_counts": missing["field_missing_status_counts"],
        "current_missing_row_counts": missing["field_missing_row_counts"],
        "requirements": field_requirements,
        "mandatory_fail_closed_controls": [
            "source_artifact_hash",
            "parser_code_hash",
            "forbidden_field_scan_status",
            "promotion_verdict",
            "validation_safe",
            "outcome_review_opened",
            "live_effect",
            "accepted_first_filtering_status",
            "reject_overlap_exclusion_status",
            "same_tick_same_bar_ambiguity_status",
            "mt5_order_ticket_redaction_status",
            "cost_testing_gate_status",
        ],
        "optional_value_mandatory_status_controls": [
            "decision_spread_value_source_safe",
            "entry_touch_spread_value_source_safe",
            "entry_touch_first_utc",
            "terminal_area_first_touch_utc",
            "protective_area_first_touch_utc",
        ],
        "forbidden_fields": sorted(set(FORBIDDEN_VALUE_TOKENS)),
    }

    completion_audit = {
        "artifact": "G0_NOFILL_FORWARD_COMPLETION_AUDIT",
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        **flags,
        "can_mark_goal_complete_after_verification_and_commit": True,
        "terminal_design_route_decision": route_ranking()[0]["route"],
        "prompt_to_artifact_checklist": [
            {
                "requirement": "mandatory_preflight_read",
                "artifact_or_evidence": "Context anchor lists LIVE_STATE, latest handoff, quick reference, doctrine, research_current_state, goal_session_research_discipline, and local_heavy_data_inventory.",
                "status": "PASS",
            },
            {
                "requirement": "what_g12_accepted_and_not_accepted",
                "artifact_or_evidence": "Decision ledger and evidence-chain reconciliation record ACCEPT_AS_SOURCE_CONTROL_PROJECTION_EVIDENCE_ONLY and closed result/validation/live flags.",
                "status": "PASS",
            },
            {
                "requirement": "projection_fields_useful_vs_control_only",
                "artifact_or_evidence": "Field requirement matrix and schema requirements classify capture, pending-order, spread, redaction, duplicate, and no-leak controls.",
                "status": "PASS",
            },
            {
                "requirement": "missing_status_source_safe_vs_result_liveness_requirements",
                "artifact_or_evidence": "Field requirement matrix maps current missing counts and exact future lane requirements.",
                "status": "PASS",
            },
            {
                "requirement": "future_source_capture_fields_for observability_latency_spread_touch_terminal_redaction_duplicates_noleak",
                "artifact_or_evidence": "Capture schema requirements JSON contains future_capture_field_requirements and mandatory fail-closed controls.",
                "status": "PASS",
            },
            {
                "requirement": "mandatory_optional_fail_closed_forbidden_fields",
                "artifact_or_evidence": "Field requirement matrix JSON has mandatory_fail_closed_controls, optional_value_mandatory_status_controls, and forbidden_fields.",
                "status": "PASS",
            },
            {
                "requirement": "cost_slippage_execution_support_without_opening_labels",
                "artifact_or_evidence": "Source/cost/execution separation ledger freezes spread snapshots as source fields and keeps slippage/execution labels closed.",
                "status": "PASS",
            },
            {
                "requirement": "rank_next_implementation_route",
                "artifact_or_evidence": "Capture implementation design ranking chooses source-capture contract hardening plus offline projection prototype as rank 1.",
                "status": "PASS",
            },
            {
                "requirement": "evidence_class_gate_before_live_logger_code",
                "artifact_or_evidence": "Decision ledger, ranking, forbidden ledger, and next prompt pack require owner-approved implementation after G12 acceptance.",
                "status": "PASS",
            },
            {
                "requirement": "hostile_review_failure_modes",
                "artifact_or_evidence": "Hostile review ledger covers fake edge, leakage, duplicates, timestamps, cost/slippage confusion, operational risk, and underspecification.",
                "status": "PASS",
            },
            {
                "requirement": "robust_trading_system_controls",
                "artifact_or_evidence": "Schema requirements include timestamp integrity, session/regime tags, spread/cost provenance, slippage separation, execution-quality status, latency, missed/partial/failed-fill status placeholders, duplicates, perturbation readiness, sample floor, kill-switch observability, and weekly/live-review compatibility.",
                "status": "PASS",
            },
            {
                "requirement": "hard_boundaries_preserved",
                "artifact_or_evidence": "Forbidden route ledger and verifier enforce no result scoring, validation, promotion, registry edit, live wiring, paid/API routes, MT5 account/order/history labels, or live-surface changes.",
                "status": "PASS",
            },
            {
                "requirement": "saturation_questions_answered",
                "artifact_or_evidence": "Completion audit includes saturation answers and forbidden-route ledger ties each gap to exact next gate.",
                "status": "PASS",
            },
        ],
        "saturation_answers": [
            {
                "question": "Did any accepted projection field silently imply result/cost evidence?",
                "answer": "No. G12 no-leak audit has zero forbidden projection key/value hits, slippage/execution labels remain NOT_OPENED/REDACTED status only, and spread values are source-safe quote snapshots only.",
            },
            {
                "question": "Did any source-control/source-impossible/reject row become eligible by wording drift?",
                "answer": "No. Denominator audit preserves 298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject; reject-overlap rows have zero denominator effect.",
            },
            {
                "question": "Did the design specify enough clock, write, as-of, and latency controls to avoid fake forward evidence?",
                "answer": "Yes for implementation design: capture_observed/write-start/write-complete/latency/skew/status/derivation fields are mandatory or fail-closed. They still require a later owner-approved live-wiring lane to populate prospectively.",
            },
            {
                "question": "Did ticket redaction and pending-order observability remain source-safe?",
                "answer": "Yes. The schema allows categorical pending-order mode/status fields and redaction statuses only; raw tickets and account/order/deal/position labels remain forbidden.",
            },
            {
                "question": "Did the design preserve spread, slippage, execution-quality, cost, and outcome separation?",
                "answer": "Yes. Decision/touch spread snapshots are source-safe observations; slippage, execution-quality, cost testing, R, and outcomes stay closed pending a separate result/cost lane.",
            },
            {
                "question": "Did hostile-review controls cover data integrity, costs, perturbation readiness, sample/duplicate control, regime/session tags, and kill-switch observability?",
                "answer": "Yes. These are included as schema/control requirements or explicit future implementation gates; no claim is promoted from them now.",
            },
            {
                "question": "Is the recommended next route exact enough for a future goal session?",
                "answer": "Yes. The rank-1 route names the evidence class, required artifacts, field families, forbidden fields, verifiers, owner gate, and stop condition.",
            },
        ],
        "required_artifacts": REQUIRED_MD
        + REQUIRED_JSON
        + ["G0_NOFILL_FORWARD_VERIFICATION_RESULT_2026-05-09.json"],
        "verification_result_artifact": "G0_NOFILL_FORWARD_VERIFICATION_RESULT_2026-05-09.json",
        "verification_requirements": [
            "Parse generated JSON.",
            "Run py_compile on generated builder/verifier/test.",
            "Run focused pytest for this route.",
            "Run the generated verifier.",
            "Rerun or cite G12 repair-reaudit verifier.",
            "Run committed-diff live-surface check.",
            "Regenerate LIVE_STATE.",
        ],
    }

    return {
        "sources": sources,
        "field_matrix": field_matrix,
        "schema_requirements": schema_requirements,
        "completion_audit": completion_audit,
        "flags": flags,
        "denom": denom,
        "missing": missing,
        "no_leak": no_leak,
        "source_hash": source_hash,
        "lifecycle_schema": lifecycle_schema,
        "g12_decision": g12_decision,
    }


def md_header(title: str) -> str:
    return (
        f"# {title}\n\n"
        f"Route: `{ROUTE_ID}`\n"
        f"Promotion posture: `{PROMOTION_VERDICT}`\n"
        "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`\n"
    )


def render_context_anchor(payload: dict[str, Any]) -> str:
    lines = [
        md_header("G0 NOFILL Forward Projection Context Anchor"),
        "## Scope",
        "",
        "This is a G0 governance/design lane. It uses accepted source/control projection evidence to specify future source-capture implementation requirements. It does not score outcomes, validate, promote, edit registries, wire live loggers, call paid/API routes, or touch live trading surfaces.",
        "",
        "## Controlling Inputs Read",
        "",
    ]
    for name, path in UPSTREAM.items():
        lines.append(f"- `{name}`: `{path}`")
    lines.extend(
        [
            "",
            "## Preflight Context",
            "",
            "- `.context/LIVE_STATE.md` regenerated and read before this builder was run.",
            "- Latest handoff read: `.context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md`.",
            "- Core context read: quick reference card, research operating doctrine, research current state, goal-session research discipline, and local-heavy data inventory.",
            "",
            "## Boundary",
            "",
            "- Accepted source projection may guide field contracts, missing-status design, redaction controls, and verification gates.",
            "- It may not become result/cost evidence, validation-safe evidence, promotion evidence, live logger wiring, registry approval, or live trading behavior.",
        ]
    )
    return "\n".join(lines)


def render_decision_ledger(payload: dict[str, Any]) -> str:
    denom = payload["denom"]
    completion = payload["sources"]["g12_repair_completion"]
    ranking = route_ranking()
    lines = [
        md_header("G0 NOFILL Forward Projection Decision Ledger"),
        f"Terminal G0 design decision: `{ranking[0]['route']}`.",
        "",
        f"G12 actually accepted: `{completion['terminal_decision']}`.",
        "",
        "G12 did not accept result/cost scoring, validation, promotion, registry edits, live logger wiring, paid/API routes, broker/account/order-history labels, or live behavior.",
        "",
        "## Evidence",
        "",
        f"- Projection partition: `{denom['universe_equation']}`.",
        f"- Accepted denominators: row-level `{denom['row_level_accepted_denominator']}`, primary duplicate-key `{denom['primary_duplicate_key_denominator']}`, secondary duplicate-group `{denom['secondary_duplicate_group_denominator']}`.",
        f"- Reject-overlap rows: `{denom['reject_overlap_rows']}` with zero denominator effect.",
        "- G12 repair blockers `G12-PROJ-BLOCKER-001`, `G12-PROJ-BLOCKER-002`, and `G12-PROJ-WARN-001` are closed in the accepted repair reaudit.",
        "",
        "## Next Gate",
        "",
        "Before any code changes to live logger wiring, the next evidence-class gate is: owner-approved implementation lane after a source-capture contract/offline projection prototype passes independent G12 acceptance. This G0 route only specifies the design.",
    ]
    return "\n".join(lines)


def render_evidence_chain(payload: dict[str, Any]) -> str:
    denom = payload["denom"]
    no_leak = payload["no_leak"]
    source_hash = payload["source_hash"]
    lifecycle = payload["lifecycle_schema"]
    lines = [
        md_header("G0 NOFILL Forward Projection Evidence Chain Reconciliation"),
        "| Chain Link | Status | Evidence | Boundary |",
        "|---|---|---|---|",
        "| CAT V3 source-control rebuild | accepted upstream | Accepted/source-control/source-impossible/reject families were frozen before projection. | Source/control only. |",
        "| CAT V3 result contract/count packet | quarantined control evidence | Count denominators are row-level 225, primary 182, secondary 139. | Not validation or promotion. |",
        "| Forward lifecycle capture contract audit | accepted with exact blockers | G12 accepted schema intent but required latency, pending-order, and spread/slippage addendum fields. | No raw logs consumed directly. |",
        "| Forward contract addendum/projection builder | repaired and audited | Addendum added 26 fields; projection emitted 298 rows. | Source/control projection only. |",
        "| G12 projection repair reaudit | accepted | Terminal decision `ACCEPT_AS_SOURCE_CONTROL_PROJECTION_EVIDENCE_ONLY`. | No result/cost/live use. |",
        "| This G0 route | design synthesis | Ranks next route and freezes field/schema controls. | No implementation wiring. |",
        "",
        "## Reconciled Counts",
        "",
        f"- Projection rows: `{denom['projection_row_count']}`.",
        f"- Family counts: `{denom['family_counts']}`.",
        f"- Required source-control rows remain `{', '.join(denom['source_control_rows'])}`.",
        f"- Required source-impossible rows remain `{', '.join(denom['source_impossible_rows'])}`.",
        "",
        "## No-Leak And Hash Evidence",
        "",
        f"- Forbidden projection key hits: `{len(no_leak['forbidden_projection_key_hits'])}`.",
        f"- Forbidden projection value-token hits: `{len(no_leak['forbidden_projection_value_token_hits'])}`.",
        f"- Spread source hash non-null rows: `{no_leak['spread_source_hash_non_null_rows']}`.",
        f"- Source hash records: `{source_hash['hash_recompute']['source_hash_records']}`; parser hash records: `{source_hash['hash_recompute']['parser_hash_records']}`.",
        "",
        "## Contract Blockers Translated Into Design",
        "",
    ]
    for blocker in lifecycle["exact_contract_blockers"]:
        lines.append(f"- `{blocker['blocker_id']}`: {blocker['finding']} Fix required: {'; '.join(blocker['exact_fix'])}.")
    return "\n".join(lines)


def render_ranking(payload: dict[str, Any]) -> str:
    lines = [
        md_header("G0 NOFILL Forward Capture Implementation Design Ranking"),
        "| Rank | Route | Evidence Class | Allowed Now | Why |",
        "|---:|---|---|---|---|",
    ]
    for route in route_ranking():
        lines.append(
            f"| {route['rank']} | `{route['route']}` | `{route['evidence_class']}` | `{route['allowed_now']}` | {route['why']} |"
        )
    lines.extend(
        [
            "",
            "## Rank-1 Specification",
            "",
            "The next route should build a source-capture contract hardening and offline projection prototype. It must produce fixtures, parser/projection rules, field allowlists, source-hash and parser-hash manifests, no-leak scans, duplicate/denominator proofs, and a G12-ready verifier. It must not touch live logger code.",
            "",
            "Rank 3 is only a plan packet because live logger wiring requires explicit owner approval. Rank 4 and rank 5 are forbidden in this route.",
        ]
    )
    return "\n".join(lines)


def render_source_cost_execution(payload: dict[str, Any]) -> str:
    no_leak = payload["no_leak"]
    lines = [
        md_header("G0 NOFILL Forward Source Cost Execution Separation Ledger"),
        "| Family | Source-Safe Now | Future Use | Still Closed |",
        "|---|---|---|---|",
        "| Decision spread | `decision_spread_status`, `decision_spread_value_source_safe`, `decision_spread_unit`, `spread_source_hash` | Later cost context if a result/cost lane is opened. | Not slippage, not R, not execution quality. |",
        "| Entry-touch spread | `entry_touch_spread_status`, `entry_touch_spread_value_source_safe`, `spread_source_hash` | Later spread-at-touch context if exact touch timestamp exists. | Not fill price, not order history. |",
        "| Slippage | `slippage_label_status`, `slippage_value_redaction_status` only | Future result/cost lane can request explicit labels. | Slippage values remain redacted/closed now. |",
        "| Execution quality | `execution_quality_label_status`, `execution_quality_value_redaction_status` only | Future lane can classify missed/partial/failed fill after source gate. | No order-send result labels now. |",
        "| Outcome/cost testing | `cost_testing_gate_status` | Marks whether spread-only source control is ready. | R, WR, expectancy, DSR, PBO, validation remain closed. |",
        "",
        "## Current Source Projection Counts",
        "",
        f"- Decision spread status counts: `{no_leak['decision_spread_status_counts']}`.",
        f"- Entry-touch spread status counts: `{no_leak['entry_touch_spread_status_counts']}`.",
        "- These counts are source observability counts, not performance outcomes.",
    ]
    return "\n".join(lines)


def render_duplicate_review(payload: dict[str, Any]) -> str:
    denom = payload["denom"]
    lines = [
        md_header("G0 NOFILL Forward Duplicate And Denominator Control Review"),
        f"Universe equation: `{denom['universe_equation']}`.",
        "",
        "| Denominator | Value | Control |",
        "|---|---:|---|",
        f"| Row-level accepted | {denom['row_level_accepted_denominator']} | Accepted rows only; source-control/source-impossible/reject excluded before count. |",
        f"| Primary duplicate-key | {denom['primary_duplicate_key_denominator']} | Raw duplicate text is never emitted; SHA256 only. |",
        f"| Secondary duplicate-group | {denom['secondary_duplicate_group_denominator']} | Group collapse remains unchanged by projection fields. |",
        f"| Reject overlap rows | {denom['reject_overlap_rows']} | Zero denominator effect by accepted-first filtering. |",
        "",
        "## Future Rule",
        "",
        "Any future source-capture implementation must carry row-level, primary duplicate-key, and secondary duplicate-group membership fields plus accepted-first filtering status. A row cannot enter a result/cost lane unless a frozen source/control packet and G12 audit prove the denominator effect remains explicit.",
    ]
    return "\n".join(lines)


def render_hostile_review(payload: dict[str, Any]) -> str:
    rows = [
        ("Fake edge by source/control wording drift", "Projection accepted only as source/control evidence; forbidden ledger blocks scoring and promotion."),
        ("Hidden result/cost leakage through spread fields", "Spread values are source-safe quote snapshots; slippage/execution labels are closed statuses."),
        ("Raw ticket/order/account leakage", "Ticket fields are redaction statuses only; raw ticket, deal, position, account, fill, and order-send fields are forbidden."),
        ("Duplicate denominator inflation", "225/182/139 denominators remain explicit; reject overlaps have zero denominator effect."),
        ("Clock/write latency fake evidence", "Future fields require observed/write-start/write-complete/latency/skew/derivation status or fail-closed missing statuses."),
        ("Entry/terminal same-tick fabrication", "Event-order resolution and ambiguity statuses must preserve ambiguity or source-impossible states."),
        ("Operational live-surface risk", "No live wiring in this lane; owner-approved implementation and G12 acceptance are required before code changes."),
        ("Cost/slippage over-interpretation", "Cost testing gate stays closed until separate result/cost lane with source-safe spread manifests."),
        ("Underspecified review cadence", "Future implementation design must include weekly/live-review compatibility and kill-switch observability fields."),
    ]
    lines = [
        md_header("G0 NOFILL Forward Hostile Review And Failure Mode Ledger"),
        "| Hostile Claim | Control Response |",
        "|---|---|",
    ]
    lines.extend([f"| {claim} | {control} |" for claim, control in rows])
    return "\n".join(lines)


def render_forbidden_ledger(payload: dict[str, Any]) -> str:
    lines = [
        md_header("G0 NOFILL Forward Forbidden Route Ledger"),
        "| Forbidden Route Or Field Family | Status | Reason |",
        "|---|---|---|",
        "| Outcome scoring, R, WR, expectancy, DSR, PBO | `FORBIDDEN` | Current evidence is source/control only. |",
        "| Setting validation, outcome-review, or live-effect flags to true | `FORBIDDEN` | Required flags stay false. |",
        "| Registry edits | `FORBIDDEN` | No master registry change is authorized. |",
        "| Live logger wiring or live trading surfaces | `FORBIDDEN` | Requires separate owner-approved implementation lane. |",
        "| `src/`, prompts, config/risk/execution/permissions/safety/selectors/canaries/order behavior | `FORBIDDEN` | Live behavior surfaces are out of scope. |",
        "| MT5 order/account/history/deal/position labels | `FORBIDDEN` | Would open broker result/order evidence. |",
        "| Paid/API/Databento routes | `FORBIDDEN` | No spend or external call is authorized. |",
        "| Raw tickets, pending tickets, deal IDs, position IDs | `FORBIDDEN` | Redaction statuses only. |",
        "",
        "Any future lane that needs one of these routes must be explicitly opened by the owner and must state the evidence class it is crossing into.",
    ]
    return "\n".join(lines)


def render_next_prompt_pack(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            md_header("G0 NOFILL Forward Next Prompt Pack"),
            "## Recommended Next Goal",
            "",
            "```text",
            "/goal Build the NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_HARDENING_AND_OFFLINE_PROJECTION_PROTOTYPE lane from the G0 synthesis/control artifacts in research/science_program_2026_05/06_outcome_testing/g0_nofill_forward_projection_synthesis_control_route/. Produce source/control-only contract, fixtures, offline parser/projection prototype, redaction/no-leak verifier, duplicate/denominator audit, and G12-ready prompt pack. Do not score outcomes, validate, promote, edit registries, wire live loggers, call paid/API routes, touch src/prompts/config/risk/execution/permissions/safety/selectors/canaries/order behavior, or use MT5 order/account/history/deal/position labels. Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.",
            "```",
            "",
            "## Required Inputs",
            "",
            "- This G0 route's field matrix and schema requirements.",
            "- G12 accepted projection repair reaudit.",
            "- NOFILL forward source-safe projection builder artifacts.",
            "- NOFILL forward contract addendum projection plan.",
            "- G12 forward lifecycle capture contract audit.",
            "",
            "## Stop Condition",
            "",
            "The next route completes only when a G12-ready source-capture contract/prototype exists with exact fields, fixtures, no-leak scans, source/hash manifests, duplicate controls, forbidden route ledger, and completion audit. It must stop before live wiring.",
        ]
    )


def render_completion_audit(payload: dict[str, Any]) -> str:
    audit = payload["completion_audit"]
    lines = [
        md_header("G0 NOFILL Forward Completion Audit"),
        f"Terminal design route: `{audit['terminal_design_route_decision']}`.",
        "",
        "## Prompt-To-Artifact Checklist",
        "",
        "| Requirement | Status | Artifact Or Evidence |",
        "|---|---|---|",
    ]
    for item in audit["prompt_to_artifact_checklist"]:
        lines.append(f"| {item['requirement']} | `{item['status']}` | {item['artifact_or_evidence']} |")
    lines.extend(["", "## Saturation Pass", "", "| Question | Answer |", "|---|---|"])
    for item in audit["saturation_answers"]:
        lines.append(f"| {item['question']} | {item['answer']} |")
    lines.extend(
        [
            "",
            "## Verification Required Before Final Close",
            "",
        ]
    )
    for requirement in audit["verification_requirements"]:
        lines.append(f"- {requirement}")
    lines.extend(
        [
            "",
            f"Verifier result artifact: `{audit['verification_result_artifact']}`.",
        ]
    )
    return "\n".join(lines)


def build_artifacts() -> None:
    payload = build_payload()
    write_json("G0_NOFILL_FORWARD_PROJECTION_FIELD_REQUIREMENT_MATRIX_2026-05-09.json", payload["field_matrix"])
    write_json("G0_NOFILL_FORWARD_CAPTURE_SCHEMA_REQUIREMENTS_2026-05-09.json", payload["schema_requirements"])
    write_json("G0_NOFILL_FORWARD_COMPLETION_AUDIT_2026-05-09.json", payload["completion_audit"])

    write_md("G0_NOFILL_FORWARD_PROJECTION_CONTEXT_ANCHOR_2026-05-09.md", render_context_anchor(payload))
    write_md("G0_NOFILL_FORWARD_PROJECTION_DECISION_LEDGER_2026-05-09.md", render_decision_ledger(payload))
    write_md("G0_NOFILL_FORWARD_PROJECTION_EVIDENCE_CHAIN_RECONCILIATION_2026-05-09.md", render_evidence_chain(payload))
    write_md("G0_NOFILL_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_RANKING_2026-05-09.md", render_ranking(payload))
    write_md("G0_NOFILL_FORWARD_SOURCE_COST_EXECUTION_SEPARATION_LEDGER_2026-05-09.md", render_source_cost_execution(payload))
    write_md("G0_NOFILL_FORWARD_DUPLICATE_AND_DENOMINATOR_CONTROL_REVIEW_2026-05-09.md", render_duplicate_review(payload))
    write_md("G0_NOFILL_FORWARD_HOSTILE_REVIEW_AND_FAILURE_MODE_LEDGER_2026-05-09.md", render_hostile_review(payload))
    write_md("G0_NOFILL_FORWARD_FORBIDDEN_ROUTE_LEDGER_2026-05-09.md", render_forbidden_ledger(payload))
    write_md("G0_NOFILL_FORWARD_NEXT_PROMPT_PACK_2026-05-09.md", render_next_prompt_pack(payload))
    write_md("G0_NOFILL_FORWARD_COMPLETION_AUDIT_2026-05-09.md", render_completion_audit(payload))


def main() -> None:
    build_artifacts()
    print(f"Built {len(REQUIRED_MD) + len(REQUIRED_JSON)} G0 NOFILL forward synthesis artifacts in {BASE}")


if __name__ == "__main__":
    main()
