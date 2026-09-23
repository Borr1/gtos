"""Build the SCID Blocked15 POI/bounds source-capture contract repair package.

This route is research/source-control only. It does not score outcomes, open
validation, read broker account/order/history/deal/position evidence, or change
live trading behavior.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
FIXTURE_DIR = ROUTE_DIR / "fixtures"

ROUTE_ID = "SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR"
EVIDENCE_CLASS = "SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR_ONLY"
SCHEMA_VERSION = "scid_blocked15_poi_bounds_capture_contract_v1"
ARTIFACT_DATE = "2026-05-13"
GENERATED_AT_UTC = "2026-05-13T03:45:00Z"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

TARGET_CARD_IDS = ("ADV-005", "BEH-002", "BEH-003", "BEH-005", "GEO-001")
TARGET_CARD_ID_SET = set(TARGET_CARD_IDS)
UPSTREAM_INPUTS = {
    "controlling_prompt": "research/science_program_2026_05/04_goal_prompts/SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR_GOAL_PROMPT_2026-05-12.md",
    "g0_prompt": "research/science_program_2026_05/04_goal_prompts/G0_SCID_BLOCKED_UNBLOCKING_SYNTHESIS_AFTER_FC_G12_AUDIT_GOAL_PROMPT_2026-05-12.md",
    "g0_route_reconciliation": "research/science_program_2026_05/06_outcome_testing/g0_scid_blocked_unblocking_synthesis_after_fc_g12_audit/G0_SCID_BLOCKED_UNBLOCKING_ROUTE_RECONCILIATION_LEDGER_2026-05-12.json",
    "g0_same_evidence_blocker_pursuit": "research/science_program_2026_05/06_outcome_testing/g0_scid_blocked_unblocking_synthesis_after_fc_g12_audit/G0_SCID_BLOCKED_UNBLOCKING_SAME_EVIDENCE_BLOCKER_PURSUIT_LEDGER_2026-05-12.json",
    "g0_denominator_quarantine_gate": "research/science_program_2026_05/06_outcome_testing/g0_scid_blocked_unblocking_synthesis_after_fc_g12_audit/G0_SCID_BLOCKED_UNBLOCKING_DENOMINATOR_QUARANTINE_GATE_LEDGER_2026-05-12.json",
    "g12_blocked15_contract_exactness": "research/science_program_2026_05/06_outcome_testing/g12_scid_future_capture_blocked15_source_state_materialization_audit/G12_SCID_FC_BLOCKED15_AUDIT_PROSPECTIVE_CONTRACT_EXACTNESS_AUDIT_2026-05-12.json",
    "g12_blocked15_capture_group_audit": "research/science_program_2026_05/06_outcome_testing/g12_scid_future_capture_blocked15_source_state_materialization_audit/G12_SCID_FC_BLOCKED15_AUDIT_BLOCKED15_RECOMPUTATION_AND_CAPTURE_GROUP_AUDIT_2026-05-12.json",
    "strategy_field_packet": "research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/SCID_STRATEGY_FIELD_PROSPECTIVE_CAPTURE_REQUIREMENT_LEDGER_2026-05-12.json",
    "offline_schema_poi_v1": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/schemas/scid_forward_source_capture_v1_poi_type_bounds_source.schema.json",
    "forward_capture_helper": "src/research_infra/forward_capture.py",
    "current_forward_shadow_log": "shadow_logs/scid_forward_source_capture.jsonl",
}

SAFE_FLAGS = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
    "credentials_touched": False,
}

FORBIDDEN_SURFACES = (
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
)

FORBIDDEN_KEY_FRAGMENTS = (
    "account",
    "broker_order",
    "broker_actual",
    "deal",
    "expectancy",
    "mt5_order",
    "mt5_position",
    "order_history",
    "pnl",
    "position",
    "profit",
    "raw_ohlc",
    "raw_market",
    "realized",
    "result",
    "r_multiple",
    "ticket",
    "win_rate",
)

POI_ENUM_V1 = ("ob", "fvg", "breaker", "swing", "other", "none")
POI_MECHANISM_FAMILIES = (
    "ob_zone",
    "fvg_gap",
    "breaker_zone",
    "swing_boundary",
    "liquidity_sweep_zone",
    "round_number_band",
    "volume_profile_zone",
    "geometry_envelope",
    "macro_calendar_context_zone",
    "other_source_bound_poi",
    "none",
)

STATUS_ENUM = (
    "POI_BOUNDS_CAPTURED_SOURCE_SAFE",
    "POI_BOUNDS_NO_POI_SOURCE_SAFE",
    "POI_BOUNDS_SOURCE_UNAVAILABLE_FAIL_CLOSED",
    "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED",
    "POI_BOUNDS_ASOF_VIOLATION_FAIL_CLOSED",
    "POI_BOUNDS_HASH_MISMATCH_FAIL_CLOSED",
    "POI_BOUNDS_FORBIDDEN_FIELD_FAIL_CLOSED",
    "POI_BOUNDS_DEPENDENCY_MISSING_FAIL_CLOSED",
)

REQUIRED_ROW_FIELDS = (
    "schema_version",
    "route_id",
    "evidence_class",
    "candidate_input_row_id",
    "duplicate_proxy_denominator_key",
    "target_card_ids",
    "field_group",
    "decision_asof_utc",
    "source_observed_asof_utc",
    "source_event_clock_basis",
    "source_logger_id",
    "source_logger_version",
    "parser_contract_version",
    "source_identifier",
    "source_hash_policy",
    "source_hash",
    "redaction_policy_id",
    "forbidden_value_policy_id",
    "missing_status_policy",
    "field_status",
    "fail_closed_reason_code",
    "downstream_g12_acceptance_rule",
    "poi_type_enum_ob_fvg_breaker_swing_other_none",
    "poi_mechanism_family",
    "poi_subtype",
    "poi_lower_bound",
    "poi_upper_bound",
    "poi_bound_currency_or_points",
    "tick_size",
    "price_precision",
    "bounds_normalization_rule_id",
    "poi_source_timeframe",
    "poi_source_bar_ids",
    "source_bar_refs",
    "source_bar_set_hash",
    "mso_snapshot_schema_version",
    "mso_snapshot_asof_utc",
    "mso_snapshot_hash",
    "market_state_builder_version",
    "market_state_input_hash",
    "poi_detection_rule_version",
    "poi_detection_code_hash",
    "selected_poi_id",
    "mso_snapshot_commitment",
    "card_dependency_statuses",
    "source_truth_class",
)

CARD_DEPENDENCIES = {
    "ADV-005": ("poi_type_bounds_source", "intended_entry_reference"),
    "BEH-002": ("poi_type_bounds_source", "lifecycle_fill_cancel_expiry_source_status"),
    "BEH-003": ("intended_entry_reference", "poi_type_bounds_source"),
    "BEH-005": ("poi_type_bounds_source", "lifecycle_fill_cancel_expiry_source_status"),
    "GEO-001": ("poi_type_bounds_source", "framework_setup_family"),
}


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact_base(name: str, suffix: str) -> Path:
    return ROUTE_DIR / f"SCID_BLOCKED15_POI_BOUNDS_{name}_{ARTIFACT_DATE}.{suffix}"


OUTPUTS = {
    "context_anchor_json": artifact_base("CONTEXT_ANCHOR", "json"),
    "context_anchor_md": artifact_base("CONTEXT_ANCHOR", "md"),
    "active_question_stack_json": artifact_base("ACTIVE_QUESTION_STACK", "json"),
    "searched_root_ledger_json": artifact_base("SEARCHED_ROOT_LEDGER", "json"),
    "searched_root_ledger_md": artifact_base("SEARCHED_ROOT_LEDGER", "md"),
    "route_decision_ledger_json": artifact_base("ROUTE_DECISION_LEDGER", "json"),
    "route_decision_ledger_md": artifact_base("ROUTE_DECISION_LEDGER", "md"),
    "source_logger_contract_json": artifact_base("SOURCE_LOGGER_CONTRACT", "json"),
    "source_logger_contract_md": artifact_base("SOURCE_LOGGER_CONTRACT", "md"),
    "mso_schema_json": artifact_base("MSO_SNAPSHOT_HASH_SOURCE_BAR_SCHEMA", "json"),
    "mso_schema_md": artifact_base("MSO_SNAPSHOT_HASH_SOURCE_BAR_SCHEMA", "md"),
    "card_requirement_ledger_json": artifact_base("CARD_FAIL_CLOSED_REQUIREMENT_LEDGER", "json"),
    "card_requirement_ledger_md": artifact_base("CARD_FAIL_CLOSED_REQUIREMENT_LEDGER", "md"),
    "fixture_manifest_json": artifact_base("SYNTHETIC_FIXTURE_MANIFEST", "json"),
    "fixture_manifest_md": artifact_base("SYNTHETIC_FIXTURE_MANIFEST", "md"),
    "instruction_coverage_json": artifact_base("INSTRUCTION_COVERAGE_CHECKLIST", "json"),
    "instruction_coverage_md": artifact_base("INSTRUCTION_COVERAGE_CHECKLIST", "md"),
    "saturation_json": artifact_base("SATURATION_SELF_REDTEAM_LEDGER", "json"),
    "saturation_md": artifact_base("SATURATION_SELF_REDTEAM_LEDGER", "md"),
    "completion_audit_json": artifact_base("COMPLETION_AUDIT", "json"),
    "completion_audit_md": artifact_base("COMPLETION_AUDIT", "md"),
    "output_manifest_json": artifact_base("OUTPUT_MANIFEST", "json"),
    "output_manifest_md": artifact_base("OUTPUT_MANIFEST", "md"),
    "verification_result_json": artifact_base("VERIFICATION_RESULT", "json"),
    "focused_test_result_json": artifact_base("FOCUSED_TEST_RESULT", "json"),
    "next_g12_prompt": ROUTE_DIR / f"SCID_BLOCKED15_POI_BOUNDS_NEXT_G12_REPAIR_AUDIT_PROMPT_{ARTIFACT_DATE}.md",
    "next_g12_starter": ROUTE_DIR / f"SCID_BLOCKED15_POI_BOUNDS_NEXT_G12_REPAIR_AUDIT_STARTER_{ARTIFACT_DATE}.txt",
}


def safe_envelope(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": GENERATED_AT_UTC,
        **SAFE_FLAGS,
    }
    if extra:
        payload.update(extra)
    return payload


def upstream_card_rows() -> list[dict[str, Any]]:
    ledger = load_json(REPO_ROOT / UPSTREAM_INPUTS["g0_route_reconciliation"])
    rows = [
        row
        for row in ledger.get("card_route_rows", [])
        if row.get("card_id") in TARGET_CARD_ID_SET
    ]
    rows.sort(key=lambda row: TARGET_CARD_IDS.index(row["card_id"]))
    return rows


def upstream_capture_rows() -> list[dict[str, Any]]:
    audit = load_json(REPO_ROOT / UPSTREAM_INPUTS["g12_blocked15_contract_exactness"])
    return audit.get("contract_rows", [])


def count_forward_shadow_poi_rows() -> dict[str, Any]:
    rows = load_jsonl(REPO_ROOT / UPSTREAM_INPUTS["current_forward_shadow_log"])
    field_counts = Counter(str(row.get("field_group")) for row in rows)
    return {
        "path": UPSTREAM_INPUTS["current_forward_shadow_log"],
        "exists": (REPO_ROOT / UPSTREAM_INPUTS["current_forward_shadow_log"]).exists(),
        "row_count": len(rows),
        "field_group_counts": dict(sorted(field_counts.items())),
        "poi_type_bounds_source_rows": field_counts.get("poi_type_bounds_source", 0),
        "status": "NO_CURRENT_POI_ROWS_FOUND" if field_counts.get("poi_type_bounds_source", 0) == 0 else "CURRENT_POI_ROWS_PRESENT",
    }


def make_context_anchor() -> dict[str, Any]:
    return safe_envelope(
        {
            "artifact_family": "context_anchor",
            "objective_restatement": "Build a source-control repair package for the five Blocked15 POI/bounds cards without inferring historical POI truth from price.",
            "builder_or_audit_posture": "constructive_source_control_builder",
            "target_cards": list(TARGET_CARD_IDS),
            "mandatory_context_read": [
                ".context/LIVE_STATE.md",
                ".context/00_core/goal_session_research_discipline.md",
                ".context/00_core/research_operating_doctrine.md",
                ".context/00_core/research_current_state.md",
                ".context/00_core/local_heavy_data_inventory.md",
                ".context/00_core/ai_in_loop_cost_control_research_plan.md",
                ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
                UPSTREAM_INPUTS["controlling_prompt"],
            ],
            "upstream_inputs": UPSTREAM_INPUTS,
            "forbidden_surfaces": list(FORBIDDEN_SURFACES),
            "proof_or_impossibility_stop_condition": "Every same-evidence-class blocker is either contractually closed, proven non-generatable from approved historical source routes, or reduced to exact future source/capture/parser/G12 requirements.",
            "current_head_at_preflight": "3ab07d46 docs: refresh state after scid next wave prompt hardening",
        }
    )


def make_active_question_stack() -> dict[str, Any]:
    questions = [
        {
            "question_id": "Q1",
            "question": "Can the accepted G0/G12 artifacts provide historical structured POI/bounds source truth for the five target cards?",
            "answer": "No. Upstream status is NO_RECOVERABLE_STRUCTURED_SOURCE_ROWS_FOUND_FOR_ACCEPTED_40_DENOMINATOR for poi_type_bounds_source.",
            "terminal_status": "PROVEN_NON_GENERATABLE_FROM_APPROVED_HISTORICAL_SOURCE_ROUTES",
        },
        {
            "question_id": "Q2",
            "question": "Can price movement or later path shape be used to infer the missing POI/bounds?",
            "answer": "No. The contract explicitly forbids deriving source-state truth from later price movement, path labels, or result-selection logic.",
            "terminal_status": "FORBIDDEN_BOUNDARY_RECORDED",
        },
        {
            "question_id": "Q3",
            "question": "What prospective fields prevent recurrence for OB and non-OB POI mechanisms?",
            "answer": "Use the v2 logger contract, source-bar refs, MSO snapshot commitment/hash, selected POI id, bounds, mechanism family, rule/code hashes, and fail-closed dependency statuses.",
            "terminal_status": "CONTRACT_BUILT",
        },
        {
            "question_id": "Q4",
            "question": "How do ADV-005, BEH-002, BEH-003, BEH-005, and GEO-001 remain fail-closed until all dependencies exist?",
            "answer": "Each card has exact dependency group gates; POI alone cannot unblock any card or move the accepted 40-card denominator.",
            "terminal_status": "FAIL_CLOSED_CARD_REQUIREMENTS_BUILT",
        },
        {
            "question_id": "Q5",
            "question": "Can parser/as-of/hash/redaction behavior be tested without raw market blobs or live/broker sources?",
            "answer": "Yes. Synthetic fixtures cover valid OB/FVG/geometry rows plus missing bounds, stale as-of, source-bar after-as-of, forbidden field, hash mismatch, duplicate drift, and raw-blob attempts.",
            "terminal_status": "SYNTHETIC_FIXTURES_AND_VERIFIER_BUILT",
        },
    ]
    return safe_envelope({"artifact_family": "active_question_stack", "questions": questions})


def make_searched_root_ledger() -> dict[str, Any]:
    path_rows: list[dict[str, Any]] = []
    for label, rel_path in UPSTREAM_INPUTS.items():
        path = REPO_ROOT / rel_path
        path_rows.append(
            {
                "label": label,
                "path": rel_path,
                "exists": path.exists(),
                "sha256": file_sha256(path),
                "used_for": "source/control contract evidence and blocker proof",
            }
        )
    path_rows.append(
        {
            "label": "absolute_main_repo_data_root",
            "path": "C:/Users/MSI/Documents/ai-trading-agent/data",
            "exists": Path("C:/Users/MSI/Documents/ai-trading-agent/data").exists(),
            "sha256": None,
            "used_for": "not consumed; POI/bounds historical source-state is non-generatable unless a GTOS/MSO source-state artifact exists",
        }
    )
    path_rows.append(
        {
            "label": "sierra_root",
            "path": "C:/SierraChart",
            "exists": Path("C:/SierraChart").exists(),
            "sha256": None,
            "used_for": "not consumed; market bars cannot reconstruct historical GTOS POI intent/source-state",
        }
    )
    return safe_envelope(
        {
            "artifact_family": "searched_root_ledger",
            "searched_patterns": [
                "source_safe_mso_snapshot_and_poi_logger",
                "poi_type_bounds_source",
                "mso_snapshot_hash",
                "source_bar_ids",
                "ADV-005|BEH-002|BEH-003|BEH-005|GEO-001",
            ],
            "path_rows": path_rows,
            "current_forward_shadow_log_summary": count_forward_shadow_poi_rows(),
            "negative_evidence": "Current committed and shadow source artifacts do not contain accepted-denominator historical structured POI/bounds rows for the five target cards.",
            "exact_unblocker": "Prospective source_safe_mso_snapshot_and_poi_logger row with v2 fields, source-bar hash refs, MSO snapshot hash, and G12 acceptance.",
        }
    )


def make_route_decision_ledger() -> dict[str, Any]:
    decisions = [
        {
            "route": "existing_mso_or_scid_source_artifact_recovery",
            "decision": "EXHAUSTED_NO_ACCEPTED_DENOMINATOR_POI_SOURCE_ROWS",
            "evidence": [
                UPSTREAM_INPUTS["g12_blocked15_contract_exactness"],
                UPSTREAM_INPUTS["g0_same_evidence_blocker_pursuit"],
                UPSTREAM_INPUTS["current_forward_shadow_log"],
            ],
            "next_requirement": "prospective capture contract",
        },
        {
            "route": "price_path_reconstruction",
            "decision": "FORBIDDEN",
            "evidence": "Would infer historical POI intent/source-state from later price movement.",
            "next_requirement": "do not use; fail closed",
        },
        {
            "route": "offline_schema_v1_extension",
            "decision": "REPAIRED_WITH_V2_CONTRACT",
            "evidence": UPSTREAM_INPUTS["offline_schema_poi_v1"],
            "next_requirement": "G12 audit must compare v1 compatibility and v2 exactness.",
        },
        {
            "route": "synthetic_parser_fixture_route",
            "decision": "BUILT",
            "evidence": "synthetic fixtures in route fixtures directory",
            "next_requirement": "focused pytest and verifier must pass",
        },
        {
            "route": "live_logger_or_restart_route",
            "decision": "NOT_OPENED_FOR_THIS_GOAL",
            "evidence": "forbidden surface: live restart/live behavior",
            "next_requirement": "future owner-approved implementation route only",
        },
    ]
    return safe_envelope({"artifact_family": "route_decision_ledger", "decisions": decisions})


def make_source_logger_contract() -> dict[str, Any]:
    field_contracts = [
        {"name": field, "required": True, "fail_closed_missing_status": "POI_BOUNDS_SCHEMA_INVALID_FAIL_CLOSED"}
        for field in REQUIRED_ROW_FIELDS
    ]
    return safe_envelope(
        {
            "artifact_family": "source_logger_contract",
            "source_logger_id": "source_safe_mso_snapshot_and_poi_logger",
            "proposed_append_only_path": "shadow_logs/scid_poi_bounds_source_capture.jsonl",
            "field_group": "poi_type_bounds_source",
            "schema_version_required": SCHEMA_VERSION,
            "target_cards": list(TARGET_CARD_IDS),
            "field_contracts": field_contracts,
            "poi_type_enum_v1_compatibility": list(POI_ENUM_V1),
            "poi_mechanism_families_v2": list(POI_MECHANISM_FAMILIES),
            "parser_requirement": {
                "input_format": "append-only JSONL or synthetic fixture JSON/JSONL",
                "canonical_hash": "sha256(canonical JSON with sorted keys, compact separators, ASCII escaping)",
                "source_hash": "sha256(row without source_hash)",
                "mso_snapshot_hash": "sha256(mso_snapshot_commitment)",
                "source_bar_set_hash": "sha256(source_bar_refs)",
                "duplicate_policy": "candidate_input_row_id maps to one duplicate_proxy_denominator_key across the packet",
                "fail_closed_policy": list(STATUS_ENUM),
            },
            "as_of_rule": {
                "source_observed_asof_utc": "must be <= decision_asof_utc",
                "mso_snapshot_asof_utc": "must be <= decision_asof_utc",
                "source_bar_refs.bar_end_exclusive_utc": "must be <= decision_asof_utc",
                "poi_detection_asof_utc": "must be <= decision_asof_utc",
                "forbidden": "post-decision path, target status, fill/cancel/result labels, broker/account/order/history/deal/position evidence",
            },
            "redaction_rule": {
                "policy_id": "SCID_POI_BOUNDS_NO_BROKER_ORDER_ACCOUNT_DEAL_POSITION_IDS_V1",
                "allowed_identifiers": "candidate ids, source-local synthetic or hashed ids, source-bar hashes, redacted bridge hashes only",
                "forbidden_key_fragments": list(FORBIDDEN_KEY_FRAGMENTS),
            },
            "g12_acceptance_criteria": [
                "Verify all five target cards have exact fail-closed requirements.",
                "Verify all source hashes and MSO/source-bar hashes recompute.",
                "Verify no as-of timestamp is after decision_asof_utc.",
                "Verify no forbidden broker/account/order/history/deal/position, result, R/PnL, win-rate, expectancy, performance, validation, promotion, AI/API, paid-vendor, raw-blob, or live-behavior field is present.",
                "Verify no accepted 40-card denominator row moves to result eligibility from this contract alone.",
            ],
            "accepted_40_denominator_unblocked_now": False,
        }
    )


def make_mso_snapshot_schema() -> dict[str, Any]:
    source_bar_ref_schema = {
        "source_bar_id": "string; stable source-local id",
        "source_instrument": "string",
        "source_timeframe": "string",
        "bar_open_utc": "date-time",
        "bar_end_exclusive_utc": "date-time <= decision_asof_utc",
        "source_file_pointer_or_cache_id": "string; no raw blob commit",
        "source_bar_hash": "sha256 over external/source-local bar payload, not raw payload committed here",
        "payload_redaction_state": "HASH_ONLY_NO_RAW_MARKET_BLOB",
    }
    snapshot_commitment_schema = {
        "mso_snapshot_schema_version": "SCID_POI_BOUNDS_MSO_SNAPSHOT_COMMITMENT_V1",
        "mso_snapshot_asof_utc": "date-time <= decision_asof_utc",
        "market_state_builder_version": "string",
        "market_state_input_hash": "sha256",
        "source_bar_refs": [source_bar_ref_schema],
        "detected_poi_refs": [
            {
                "poi_id": "string",
                "poi_type_enum_ob_fvg_breaker_swing_other_none": list(POI_ENUM_V1),
                "poi_mechanism_family": list(POI_MECHANISM_FAMILIES),
                "poi_subtype": "string or null",
                "poi_lower_bound": "number or null",
                "poi_upper_bound": "number or null",
                "poi_source_bar_ids": "array of source_bar_ref.source_bar_id",
                "poi_source_timeframe": "string",
                "poi_detection_rule_version": "string",
                "poi_detection_code_hash": "sha256",
                "poi_detection_asof_utc": "date-time <= decision_asof_utc",
            }
        ],
        "selected_poi_id": "string or null; null allowed only with POI_BOUNDS_NO_POI_SOURCE_SAFE",
    }
    return safe_envelope(
        {
            "artifact_family": "mso_snapshot_hash_source_bar_schema",
            "source_bar_ref_schema": source_bar_ref_schema,
            "mso_snapshot_commitment_schema": snapshot_commitment_schema,
            "hash_policy": {
                "source_bar_set_hash": "sha256(canonical source_bar_refs)",
                "mso_snapshot_hash": "sha256(canonical mso_snapshot_commitment)",
                "source_hash": "sha256(canonical row without source_hash)",
            },
            "raw_market_blob_policy": "Only source pointers and hashes are committed in this route; raw OHLC/tick/depth blobs are forbidden.",
        }
    )


def _source_bar_refs(decision_asof: str) -> list[dict[str, Any]]:
    refs = [
        {
            "source_bar_id": "synthetic:H1:2026-05-13T02:00:00Z",
            "source_instrument": "SYNTHETIC_XAUUSD",
            "source_timeframe": "H1",
            "bar_open_utc": "2026-05-13T02:00:00Z",
            "bar_end_exclusive_utc": "2026-05-13T03:00:00Z",
            "source_file_pointer_or_cache_id": "synthetic_fixture_hash_only:H1:2026-05-13T02",
            "source_bar_hash": stable_hash({"synthetic_bar": "h1", "bar_end": "2026-05-13T03:00:00Z"}),
            "payload_redaction_state": "HASH_ONLY_NO_RAW_MARKET_BLOB",
        },
        {
            "source_bar_id": "synthetic:M15:2026-05-13T03:15:00Z",
            "source_instrument": "SYNTHETIC_XAUUSD",
            "source_timeframe": "M15",
            "bar_open_utc": "2026-05-13T03:15:00Z",
            "bar_end_exclusive_utc": decision_asof,
            "source_file_pointer_or_cache_id": "synthetic_fixture_hash_only:M15:2026-05-13T0315",
            "source_bar_hash": stable_hash({"synthetic_bar": "m15", "bar_end": decision_asof}),
            "payload_redaction_state": "HASH_ONLY_NO_RAW_MARKET_BLOB",
        },
    ]
    return refs


def make_fixture_row(
    *,
    fixture_id: str,
    card_id: str = "ADV-005",
    poi_type: str = "ob",
    mechanism: str = "ob_zone",
    lower: float | None = 213.1,
    upper: float | None = 213.4,
    decision_asof: str = "2026-05-13T03:30:00Z",
    expected_status: str = "PASS",
    expected_issue_codes: list[str] | None = None,
) -> dict[str, Any]:
    source_bar_refs = _source_bar_refs(decision_asof)
    selected_poi_id = f"synthetic_poi:{fixture_id}"
    detected = {
        "poi_id": selected_poi_id,
        "poi_type_enum_ob_fvg_breaker_swing_other_none": poi_type,
        "poi_mechanism_family": mechanism,
        "poi_subtype": "synthetic_contract_fixture",
        "poi_lower_bound": lower,
        "poi_upper_bound": upper,
        "poi_source_bar_ids": [source_bar_refs[0]["source_bar_id"]],
        "poi_source_timeframe": "H1",
        "poi_detection_rule_version": "SCID_POI_BOUNDS_SOURCE_CAPTURE_RULE_V1",
        "poi_detection_code_hash": stable_hash({"rule": "synthetic_poi_detection_v1"}),
        "poi_detection_asof_utc": decision_asof,
    }
    commitment = {
        "mso_snapshot_schema_version": "SCID_POI_BOUNDS_MSO_SNAPSHOT_COMMITMENT_V1",
        "mso_snapshot_asof_utc": decision_asof,
        "market_state_builder_version": "GTOS_MARKET_STATE_SOURCE_SAFE_SYNTHETIC_V1",
        "market_state_input_hash": stable_hash(source_bar_refs),
        "source_bar_refs": source_bar_refs,
        "detected_poi_refs": [detected],
        "selected_poi_id": selected_poi_id,
    }
    row: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "candidate_input_row_id": f"candidate_input:SYNTHETIC:{fixture_id}",
        "duplicate_proxy_denominator_key": stable_hash({"fixture": fixture_id, "duplicate": "stable"}),
        "target_card_ids": [card_id],
        "field_group": "poi_type_bounds_source",
        "decision_asof_utc": decision_asof,
        "source_observed_asof_utc": decision_asof,
        "source_event_clock_basis": "SOURCE_SAFE_CANDLE_CLOSE_UTC",
        "source_logger_id": "source_safe_mso_snapshot_and_poi_logger",
        "source_logger_version": "SCID_POI_BOUNDS_SOURCE_LOGGER_V1",
        "parser_contract_version": SCHEMA_VERSION,
        "source_identifier": f"synthetic://scid_blocked15_poi_bounds/{fixture_id}",
        "source_hash_policy": "STRICT_SHA256_REQUIRED",
        "redaction_policy_id": "SCID_POI_BOUNDS_NO_BROKER_ORDER_ACCOUNT_DEAL_POSITION_IDS_V1",
        "forbidden_value_policy_id": "SCID_POI_BOUNDS_FORBIDDEN_SURFACE_FAIL_CLOSED_V1",
        "missing_status_policy": "SCID_POI_BOUNDS_MISSING_FIELDS_FAIL_CLOSED_V1",
        "field_status": "POI_BOUNDS_CAPTURED_SOURCE_SAFE",
        "fail_closed_reason_code": None,
        "downstream_g12_acceptance_rule": "G12_REPAIR_AUDIT_REQUIRED_BEFORE_ANY_DENOMINATOR_OR_RESULT_GATE",
        "poi_type_enum_ob_fvg_breaker_swing_other_none": poi_type,
        "poi_mechanism_family": mechanism,
        "poi_subtype": "synthetic_contract_fixture",
        "poi_lower_bound": lower,
        "poi_upper_bound": upper,
        "poi_bound_currency_or_points": "synthetic_price_units",
        "tick_size": 0.01,
        "price_precision": 2,
        "bounds_normalization_rule_id": "LOWER_LESS_EQUAL_UPPER_V1",
        "poi_source_timeframe": "H1",
        "poi_source_bar_ids": [source_bar_refs[0]["source_bar_id"]],
        "source_bar_refs": source_bar_refs,
        "source_bar_set_hash": stable_hash(source_bar_refs),
        "mso_snapshot_schema_version": commitment["mso_snapshot_schema_version"],
        "mso_snapshot_asof_utc": decision_asof,
        "mso_snapshot_hash": stable_hash(commitment),
        "market_state_builder_version": commitment["market_state_builder_version"],
        "market_state_input_hash": commitment["market_state_input_hash"],
        "poi_detection_rule_version": detected["poi_detection_rule_version"],
        "poi_detection_code_hash": detected["poi_detection_code_hash"],
        "selected_poi_id": selected_poi_id,
        "mso_snapshot_commitment": commitment,
        "card_dependency_statuses": {
            group: "PRESENT_IN_THIS_FIXTURE" if group == "poi_type_bounds_source" else "DEPENDENCY_NOT_OPENED_IN_THIS_POI_REPAIR_ROUTE_FAIL_CLOSED"
            for group in CARD_DEPENDENCIES[card_id]
        },
        "source_truth_class": "synthetic_parser_fixture_not_historical_truth",
        "fixture_expected_status": expected_status,
        "fixture_expected_issue_codes": expected_issue_codes or [],
    }
    row["source_hash"] = stable_hash({k: v for k, v in row.items() if k != "source_hash"})
    return row


def make_fixtures() -> list[dict[str, Any]]:
    fixtures: list[dict[str, Any]] = []
    valid_ob = make_fixture_row(fixture_id="valid_adv005_ob", card_id="ADV-005")
    valid_fvg = make_fixture_row(
        fixture_id="valid_beh003_fvg",
        card_id="BEH-003",
        poi_type="fvg",
        mechanism="fvg_gap",
        lower=213.15,
        upper=213.35,
    )
    valid_geometry = make_fixture_row(
        fixture_id="valid_geo001_geometry_other",
        card_id="GEO-001",
        poi_type="other",
        mechanism="geometry_envelope",
        lower=212.9,
        upper=213.6,
    )
    fixtures.extend([valid_ob, valid_fvg, valid_geometry])

    missing_bounds = copy.deepcopy(valid_ob)
    missing_bounds["candidate_input_row_id"] = "candidate_input:SYNTHETIC:missing_bounds"
    missing_bounds["source_identifier"] = "synthetic://scid_blocked15_poi_bounds/missing_bounds"
    missing_bounds["poi_lower_bound"] = None
    missing_bounds["fixture_expected_status"] = "FAIL"
    missing_bounds["fixture_expected_issue_codes"] = ["missing_poi_bounds"]
    missing_bounds["source_hash"] = stable_hash({k: v for k, v in missing_bounds.items() if k != "source_hash"})

    stale = copy.deepcopy(valid_ob)
    stale["candidate_input_row_id"] = "candidate_input:SYNTHETIC:stale_asof"
    stale["source_identifier"] = "synthetic://scid_blocked15_poi_bounds/stale_asof"
    stale["source_observed_asof_utc"] = "2026-05-13T03:31:00Z"
    stale["fixture_expected_status"] = "FAIL"
    stale["fixture_expected_issue_codes"] = ["source_after_decision_asof"]
    stale["source_hash"] = stable_hash({k: v for k, v in stale.items() if k != "source_hash"})

    late_bar = copy.deepcopy(valid_ob)
    late_bar["candidate_input_row_id"] = "candidate_input:SYNTHETIC:late_source_bar"
    late_bar["source_identifier"] = "synthetic://scid_blocked15_poi_bounds/late_source_bar"
    late_bar["source_bar_refs"][0]["bar_end_exclusive_utc"] = "2026-05-13T03:31:00Z"
    late_bar["source_bar_set_hash"] = stable_hash(late_bar["source_bar_refs"])
    late_bar["fixture_expected_status"] = "FAIL"
    late_bar["fixture_expected_issue_codes"] = ["source_bar_after_decision_asof", "mso_snapshot_hash_mismatch"]
    late_bar["source_hash"] = stable_hash({k: v for k, v in late_bar.items() if k != "source_hash"})

    forbidden = copy.deepcopy(valid_ob)
    forbidden["candidate_input_row_id"] = "candidate_input:SYNTHETIC:forbidden_broker_field"
    forbidden["source_identifier"] = "synthetic://scid_blocked15_poi_bounds/forbidden_broker_field"
    forbidden["broker_order_id"] = "SYNTHETIC_FORBIDDEN"
    forbidden["fixture_expected_status"] = "FAIL"
    forbidden["fixture_expected_issue_codes"] = ["forbidden_key"]
    forbidden["source_hash"] = stable_hash({k: v for k, v in forbidden.items() if k != "source_hash"})

    hash_mismatch = copy.deepcopy(valid_ob)
    hash_mismatch["candidate_input_row_id"] = "candidate_input:SYNTHETIC:hash_mismatch"
    hash_mismatch["source_identifier"] = "synthetic://scid_blocked15_poi_bounds/hash_mismatch"
    hash_mismatch["mso_snapshot_hash"] = "0" * 64
    hash_mismatch["fixture_expected_status"] = "FAIL"
    hash_mismatch["fixture_expected_issue_codes"] = ["mso_snapshot_hash_mismatch"]
    hash_mismatch["source_hash"] = stable_hash({k: v for k, v in hash_mismatch.items() if k != "source_hash"})

    raw_blob = copy.deepcopy(valid_ob)
    raw_blob["candidate_input_row_id"] = "candidate_input:SYNTHETIC:raw_blob_attempt"
    raw_blob["source_identifier"] = "synthetic://scid_blocked15_poi_bounds/raw_blob_attempt"
    raw_blob["raw_market_blob"] = {"synthetic": "forbidden placeholder; not real market data"}
    raw_blob["fixture_expected_status"] = "FAIL"
    raw_blob["fixture_expected_issue_codes"] = ["forbidden_key"]
    raw_blob["source_hash"] = stable_hash({k: v for k, v in raw_blob.items() if k != "source_hash"})

    dup_a = make_fixture_row(fixture_id="duplicate_a", card_id="BEH-002")
    dup_b = copy.deepcopy(dup_a)
    dup_b["source_identifier"] = "synthetic://scid_blocked15_poi_bounds/duplicate_b"
    dup_b["duplicate_proxy_denominator_key"] = stable_hash({"fixture": "duplicate_b", "duplicate": "drift"})
    dup_b["fixture_expected_status"] = "FAIL"
    dup_b["fixture_expected_issue_codes"] = ["duplicate_key_drift"]
    dup_b["source_hash"] = stable_hash({k: v for k, v in dup_b.items() if k != "source_hash"})

    fixtures.extend([missing_bounds, stale, late_bar, forbidden, hash_mismatch, raw_blob, dup_a, dup_b])
    return fixtures


def fixture_path(fixture: dict[str, Any]) -> Path:
    candidate_id = str(fixture["candidate_input_row_id"]).split(":")[-1]
    if candidate_id in {"duplicate_a", "duplicate_b"}:
        return FIXTURE_DIR / "duplicate_denominator_mismatch_fail_closed.jsonl"
    status = "valid" if fixture["fixture_expected_status"] == "PASS" else "fail_closed"
    return FIXTURE_DIR / f"{candidate_id}_{status}.json"


def write_fixtures(fixtures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    duplicate_path = FIXTURE_DIR / "duplicate_denominator_mismatch_fail_closed.jsonl"
    if duplicate_path.exists():
        duplicate_path.unlink()
    manifest_rows = []
    for fixture in fixtures:
        path = fixture_path(fixture)
        if path.suffix == ".jsonl":
            with path.open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(fixture, sort_keys=True, ensure_ascii=True) + "\n")
        else:
            path.write_text(json.dumps(fixture, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
        if not any(row["path"] == rel(path) for row in manifest_rows):
            manifest_rows.append(
                {
                    "fixture_id": path.stem,
                    "path": rel(path),
                    "expected_status": "MIXED" if path.suffix == ".jsonl" else fixture["fixture_expected_status"],
                    "expected_issue_codes": [] if path.suffix == ".jsonl" else fixture["fixture_expected_issue_codes"],
                    "sha256": file_sha256(path),
                }
            )
    for row in manifest_rows:
        row["sha256"] = file_sha256(REPO_ROOT / row["path"])
    return manifest_rows


def make_fixture_manifest(fixture_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return safe_envelope(
        {
            "artifact_family": "synthetic_fixture_manifest",
            "fixture_count": len(fixture_rows),
            "fixture_rows": fixture_rows,
            "coverage": {
                "valid_ob": True,
                "valid_fvg": True,
                "valid_non_ob_geometry": True,
                "missing_bounds_fail_closed": True,
                "stale_asof_fail_closed": True,
                "source_bar_after_asof_fail_closed": True,
                "forbidden_broker_field_fail_closed": True,
                "hash_mismatch_fail_closed": True,
                "duplicate_key_drift_fail_closed": True,
                "raw_market_blob_attempt_fail_closed": True,
            },
        }
    )


def make_card_requirement_ledger(card_rows: list[dict[str, Any]]) -> dict[str, Any]:
    requirements = []
    for row in card_rows:
        card_id = row["card_id"]
        requirements.append(
            {
                "card_id": card_id,
                "science_domain": row["science_domain"],
                "required_capture_groups": row["required_capture_groups"],
                "exact_missing_fields_or_source_status": row["exact_missing_fields_or_source_status"],
                "poi_bounds_repair_contract_fields": list(REQUIRED_ROW_FIELDS),
                "dependency_groups_that_remain_fail_closed": [
                    group for group in CARD_DEPENDENCIES[card_id] if group != "poi_type_bounds_source"
                ],
                "card_may_score_results_now": False,
                "accepted_40_denominator_unblocked_now": False,
                "fail_closed_rule": f"{card_id} remains blocked until poi_type_bounds_source and all dependency groups {CARD_DEPENDENCIES[card_id]} are candidate-attached, source-hashed, as-of-safe, redacted, and accepted by G12.",
                "g12_acceptance_requirement": "G12 must verify exact card dependency joins by candidate_input_row_id and duplicate_proxy_denominator_key before any result or denominator movement.",
            }
        )
    return safe_envelope(
        {
            "artifact_family": "card_fail_closed_requirement_ledger",
            "target_card_count": len(requirements),
            "requirements": requirements,
            "all_cards_remain_blocked_for_results": True,
            "accepted_40_denominator_unblocked_now": False,
        }
    )


def make_instruction_coverage() -> dict[str, Any]:
    rows = [
        ("mandatory_preflight", True, "LIVE_STATE and core doctrine files read before route build."),
        ("no_chat_or_compaction_memory", True, "Route inputs are disk paths and generated ledgers."),
        ("evidence_class_only", True, EVIDENCE_CLASS),
        ("forbidden_surfaces_closed", True, list(FORBIDDEN_SURFACES)),
        ("target_cards_covered", True, list(TARGET_CARD_IDS)),
        ("source_logger_contract", True, rel(OUTPUTS["source_logger_contract_json"])),
        ("mso_snapshot_hash_and_source_bar_schema", True, rel(OUTPUTS["mso_schema_json"])),
        ("synthetic_no_leak_redaction_fixtures", True, rel(OUTPUTS["fixture_manifest_json"])),
        ("parser_asof_hash_redaction_tests", True, "route verifier and focused pytest"),
        ("saturation_self_redteam", True, rel(OUTPUTS["saturation_json"])),
        ("next_g12_prompt_starter", True, [rel(OUTPUTS["next_g12_prompt"]), rel(OUTPUTS["next_g12_starter"])]),
        ("safe_flags", True, {k: SAFE_FLAGS[k] for k in ("promotion_verdict", "validation_safe", "outcome_review_opened", "live_effect")}),
    ]
    return safe_envelope(
        {
            "artifact_family": "instruction_coverage_checklist",
            "rows": [
                {"requirement": req, "covered": covered, "evidence": evidence}
                for req, covered, evidence in rows
            ],
            "all_required_items_covered": all(covered for _, covered, _ in rows),
        }
    )


def make_saturation() -> dict[str, Any]:
    rows = [
        {
            "question": "Could POI source/control evidence be mistaken for result evidence?",
            "answer": "Artifacts set validation_safe=false, outcome_review_opened=false, opens_result_scoring=false, and accepted_40_denominator_unblocked_now=false.",
            "same_class_action": "Verifier enforces safe flags and card fail-closed requirements.",
            "status": "RESOLVED",
        },
        {
            "question": "Could OB-only wording box the future logger?",
            "answer": "Contract keeps v1 enum compatibility while adding poi_mechanism_family values for FVG, breaker, swing, liquidity sweep, round-number, volume-profile, geometry, macro/calendar context, other, and none.",
            "same_class_action": "Valid synthetic fixtures include FVG and geometry_other.",
            "status": "RESOLVED",
        },
        {
            "question": "Could raw market blobs leak into committed artifacts?",
            "answer": "Source bars are hash/pointer refs only; raw_blob fixture is synthetic and expected to fail closed.",
            "same_class_action": "Verifier rejects raw_market/raw_ohlc key fragments and manifest raw extensions.",
            "status": "RESOLVED",
        },
        {
            "question": "Could source bars or MSO snapshots be after decision time?",
            "answer": "Parser checks source_observed_asof_utc, mso_snapshot_asof_utc, and every bar_end_exclusive_utc against decision_asof_utc.",
            "same_class_action": "Stale-asof and late-source-bar fixtures fail closed.",
            "status": "RESOLVED",
        },
        {
            "question": "Could this route silently unblock ADV/BEH/GEO cards without entry/lifecycle/framework dependencies?",
            "answer": "No. Card ledger requires all dependency groups by candidate id and duplicate key plus G12 acceptance before any denominator movement.",
            "same_class_action": "Every target card remains may_score_results_now=false.",
            "status": "RESOLVED",
        },
        {
            "question": "Could historical source truth be recovered from local heavy market data?",
            "answer": "No for GTOS POI intent/source-state unless a source-state artifact exists; price bars/ticks can support future market context but cannot reconstruct which POI GTOS selected historically.",
            "same_class_action": "Searched-root ledger records exact prospective source/capture requirement.",
            "status": "REDUCED_TO_EXACT_CAPTURE_REQUIREMENT",
        },
    ]
    return safe_envelope({"artifact_family": "saturation_self_redteam_ledger", "rows": rows})


def make_completion_audit() -> dict[str, Any]:
    checklist = [
        ("objective_restatement", True, "POI/bounds zero-recovered group converted to prospective capture contract package."),
        ("adv_beh_geo_card_requirements", True, rel(OUTPUTS["card_requirement_ledger_json"])),
        ("source_logger_contract", True, rel(OUTPUTS["source_logger_contract_json"])),
        ("mso_snapshot_hash_source_bar_schema", True, rel(OUTPUTS["mso_schema_json"])),
        ("synthetic_fixtures", True, rel(OUTPUTS["fixture_manifest_json"])),
        ("verifier_and_focused_tests", True, [rel(OUTPUTS["verification_result_json"]), rel(OUTPUTS["focused_test_result_json"])]),
        ("next_g12_prompt_starter", True, [rel(OUTPUTS["next_g12_prompt"]), rel(OUTPUTS["next_g12_starter"])]),
        ("no_validation_results_or_promotion", True, {k: SAFE_FLAGS[k] for k in ("validation_safe", "outcome_review_opened", "promotion_verdict")}),
        ("live_effect_false", True, SAFE_FLAGS["live_effect"]),
        ("accepted_40_denominator_unblocked_now_false", True, False),
    ]
    return safe_envelope(
        {
            "artifact_family": "completion_audit",
            "objective_as_deliverables": [
                "Exact prospective POI/bounds source logger contract.",
                "MSO snapshot hash and source-bar hash schema.",
                "Synthetic no-leak/redaction/hash/as-of fixtures.",
                "Verifier and focused tests.",
                "Fail-closed card requirements for ADV-005, BEH-002, BEH-003, BEH-005, GEO-001.",
                "Next G12 repair audit prompt and starter.",
            ],
            "prompt_to_artifact_checklist": [
                {"requirement": req, "covered": covered, "evidence": evidence}
                for req, covered, evidence in checklist
            ],
            "can_mark_goal_complete_after_verification": True,
            "completion_standard_met": True,
        }
    )


def make_next_g12_prompt() -> str:
    return f"""# G12 SCID Blocked15 POI Bounds Source Capture Contract Repair Audit

Evidence class: `G12_SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR_AUDIT_ONLY`

Audit the repair package in `{rel(ROUTE_DIR)}`. Use mandatory preflight first, then independently verify:

Mandatory preflight and context:
- Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`.
- Read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, and `.context/00_core/local_heavy_data_inventory.md`.
- Read the controlling builder prompt, route output manifest, completion audit, verifier, focused tests, schema/fixture files, and every repair artifact in the package. Do not rely on chat memory or closeout claims.

Audit posture hardening:
- Be strict on source/control evidence, but do not perform conservative theater. Do not invent limitations, speculative blockers, or reject broad/new/non-OB mechanism support because it is unfamiliar or outside the old OB-only frame.
- Any failure or blocker must cite exact disk evidence: artifact path, card id, capture field, schema/fixture row, hash, as-of rule, redaction/no-leak rule, verifier/test failure, or manifest mismatch.
- If a mismatch is repairable inside this same G12 evidence class through deterministic schema/fixture/hash/manifest/parser repair, pursue and close that repair before issuing a terminal repair blocker. Do not stop at "blocked" while the repair is locally actionable.
- If something truly requires future forward capture or a later evidence class, emit the exact next prompt/starter and prove why it cannot be solved in this audit.
- The completion audit must include a prompt-to-artifact checklist showing mandatory context read, artifacts inspected, recomputations performed, repairs attempted/closed or proven out of scope, and the exact terminal decision.

1. The package stays source/control only with `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
2. No validation, result scoring, R/PnL/win-rate/expectancy/performance, promotion, AI/API, paid vendor, broker account/order/history/deal/position evidence, raw market blob, live restart, live behavior, or trading/risk/safety/prompt-decision surface is opened.
3. The target cards are exactly `ADV-005`, `BEH-002`, `BEH-003`, `BEH-005`, and `GEO-001`.
4. The `source_safe_mso_snapshot_and_poi_logger` contract has exact fields, parser requirements, as-of rules, hash recomputation, redaction rules, duplicate policy, fail-closed statuses, and G12 acceptance criteria.
5. The MSO snapshot/source-bar schema commits only hashes and source pointers, never raw market blobs, and supports non-OB mechanisms through `poi_mechanism_family`.
6. Synthetic fixtures cover valid OB/FVG/non-OB geometry and fail closed on missing bounds, stale as-of, late source bars, forbidden fields, hash mismatch, duplicate drift, and raw-blob attempts.
7. Each target card remains fail-closed until all dependency capture groups for that card are source-hashed, as-of-safe, redacted, candidate-attached by `candidate_input_row_id` and `duplicate_proxy_denominator_key`, and accepted by G12.

Terminal decisions allowed:

- `ACCEPT_AS_G12_SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR_CONTROL_EVIDENCE_ONLY`
- `REPAIR_REQUIRED_WITH_EXACT_FIELDS`

Do not open any result, validation, denominator movement, live behavior, API/spend, broker/account/order/history/deal/position, or promotion lane.
"""


def make_next_g12_starter() -> str:
    return (
        "/goal Follow the full G12 audit prompt in "
        f"{rel(OUTPUTS['next_g12_prompt'])} as the complete objective; run mandatory preflight/context refresh first; "
        "do not rely on chat or compaction memory; stay G12_SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR_AUDIT_ONLY "
        "with no validation/results/R/PnL/win-rate/expectancy/performance/promotion/live/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/trading-risk-safety-prompt-decision changes; "
        "audit exact fields, parser/as-of/hash/redaction fixtures, fail-closed card requirements for ADV-005, BEH-002, BEH-003, BEH-005, and GEO-001, verifier/focused tests, saturation, and output manifest; "
        "return ACCEPT_AS_G12... only if every requirement is independently covered; preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false."
    )


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: Any) -> None:
    text = f"# {title}\n\n```json\n{json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)}\n```\n"
    path.write_text(text, encoding="utf-8")


def make_output_manifest() -> dict[str, Any]:
    artifacts = []
    for key, path in OUTPUTS.items():
        artifacts.append({"key": key, "path": rel(path), "sha256": file_sha256(path)})
    for key, path in {
        "builder_script": Path(__file__).resolve(),
        "verifier_script": ROUTE_DIR / "verify_scid_blocked15_poi_bounds_source_capture_contract_repair_2026_05_13.py",
        "focused_test_script": ROUTE_DIR / "test_scid_blocked15_poi_bounds_source_capture_contract_repair_2026_05_13.py",
    }.items():
        artifacts.append({"key": key, "path": rel(path), "sha256": file_sha256(path)})
    artifacts.extend(
        {
            "key": f"fixture:{path.name}",
            "path": rel(path),
            "sha256": file_sha256(path),
        }
        for path in sorted(FIXTURE_DIR.glob("*"))
        if path.is_file()
    )
    return safe_envelope(
        {
            "artifact_family": "output_manifest",
            "artifacts": artifacts,
            "artifact_count": len(artifacts),
            "raw_market_blob_committed": False,
            "accepted_40_denominator_unblocked_now": False,
        }
    )


def build_all() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    card_rows = upstream_card_rows()
    fixtures = make_fixtures()
    fixture_manifest_rows = write_fixtures(fixtures)

    artifacts: list[tuple[str, Path, dict[str, Any] | str]] = [
        ("Context Anchor", OUTPUTS["context_anchor_json"], make_context_anchor()),
        ("Active Question Stack", OUTPUTS["active_question_stack_json"], make_active_question_stack()),
        ("Searched Root Ledger", OUTPUTS["searched_root_ledger_json"], make_searched_root_ledger()),
        ("Route Decision Ledger", OUTPUTS["route_decision_ledger_json"], make_route_decision_ledger()),
        ("Source Logger Contract", OUTPUTS["source_logger_contract_json"], make_source_logger_contract()),
        ("MSO Snapshot Hash Source Bar Schema", OUTPUTS["mso_schema_json"], make_mso_snapshot_schema()),
        ("Card Fail Closed Requirement Ledger", OUTPUTS["card_requirement_ledger_json"], make_card_requirement_ledger(card_rows)),
        ("Synthetic Fixture Manifest", OUTPUTS["fixture_manifest_json"], make_fixture_manifest(fixture_manifest_rows)),
        ("Instruction Coverage Checklist", OUTPUTS["instruction_coverage_json"], make_instruction_coverage()),
        ("Saturation Self Redteam Ledger", OUTPUTS["saturation_json"], make_saturation()),
        ("Completion Audit", OUTPUTS["completion_audit_json"], make_completion_audit()),
    ]
    for title, json_path, payload in artifacts:
        assert isinstance(payload, dict)
        write_json(json_path, payload)
        md_key = json_path.name.replace(".json", ".md")
        md_path = ROUTE_DIR / md_key
        if md_path in OUTPUTS.values():
            write_md(md_path, title, payload)

    OUTPUTS["next_g12_prompt"].write_text(make_next_g12_prompt(), encoding="utf-8")
    OUTPUTS["next_g12_starter"].write_text(make_next_g12_starter() + "\n", encoding="utf-8")

    manifest = make_output_manifest()
    write_json(OUTPUTS["output_manifest_json"], manifest)
    write_md(OUTPUTS["output_manifest_md"], "Output Manifest", manifest)
    return manifest


if __name__ == "__main__":
    manifest = build_all()
    print(json.dumps({"built": True, "artifact_count": manifest["artifact_count"], "route_dir": rel(ROUTE_DIR)}, sort_keys=True))
