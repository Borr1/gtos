from __future__ import annotations

import json
from pathlib import Path

from verify_scid_combined_source_search_and_forward_capture_route_2026_05_12 import verify


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
DATE_TAG = "2026-05-12"
PREFIX = "SCID_COMBINED_SOURCE_CAPTURE"


def load_json(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict]:
    rows = []
    with (ROUTE_DIR / name).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_candidate_status_covers_all_3014_rows_and_field_groups():
    summary = load_json("CANDIDATE_SOURCE_CAPTURE_STATUS_SUMMARY")
    rows = load_jsonl(f"{PREFIX}_CANDIDATE_SOURCE_CAPTURE_STATUS_{DATE_TAG}.jsonl")

    assert len(rows) == 3014
    assert summary["row_count"] == 3014
    assert summary["unique_candidate_ids"] == 3014
    assert summary["unique_duplicate_proxy_denominator_keys"] == 3014
    assert len({row["candidate_input_row_id"] for row in rows}) == 3014
    assert len({row["duplicate_proxy_denominator_key"] for row in rows}) == 3014

    expected_fields = {
        "canonical_candidate_and_denominator",
        "source_symbol_session_partition",
        "source_control_coverage_not_computable_reasons",
        "intended_side_direction",
        "intended_entry_reference",
        "intended_stop_reference",
        "intended_target_reference",
        "poi_type_bounds_source",
        "framework_setup_family",
        "lifecycle_fill_cancel_expiry_source_status",
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements",
        "baseline_control_fields",
        "broker_account_order_history_deal_position_evidence",
    }
    assert set(rows[0]["field_statuses"]) == expected_fields
    assert summary["field_status_counts"]["intended_side_direction"][
        "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_CONTRACT_FROZEN"
    ] == 3014
    assert summary["field_status_counts"]["baseline_control_fields"][
        "CONTROL_CONTRACT_FROZEN_FROM_CLOSED_SOURCE_DESCRIPTORS"
    ] == 3014
    assert summary["field_status_counts"]["broker_account_order_history_deal_position_evidence"][
        "FORBIDDEN_IN_THIS_EVIDENCE_CLASS"
    ] == 3014


def test_searched_roots_are_broad_and_do_not_accept_weak_joins_as_truth():
    searched = load_json("SEARCHED_ROOT_LEDGER")
    join = load_json("SOURCE_STATE_JOIN_RECOVERY_CANDIDATE_LEDGER")

    required_roots = {
        "accepted_strategy_field_packet",
        "accepted_g12_g0_strategy_field_artifacts",
        "accepted_scid_candidate_input_and_neutral_artifacts",
        "source_control_sibling_routes",
        "shadow_logs_source_safe_nonbroker",
        "program_control_artifacts",
        "pipeline_state_artifacts",
        "knowledge_base_nonbroker_records",
        "repo_data_text_manifests_only",
        "repo_research_archive",
        "prior_worktree_gtos_otb",
        "prior_worktree_gtos_otl",
        "prior_recovery_cache",
    }
    assert required_roots.issubset(set(searched["searched_root_ids"]))
    assert searched["totals"]["text_files_scanned"] > 0
    assert searched["hard_boundary_skips"]["raw_market_blob_suffixes"]
    assert searched["source_search_result"] == (
        "NO_NEW_EXPLICIT_HISTORICAL_STRATEGY_INTENT_SOURCE_STATE_RECOVERED_BEYOND_ACCEPTED_PACKET_DESCRIPTORS"
    )

    policies = {row["join_route"]: row["decision"] for row in join["join_candidates"]}
    assert policies["shadow_logs_symbol_time_candidate_lead"] == "NOT_ACCEPTED_WITHOUT_EXPLICIT_SCID_BINDING"
    assert policies["raw_scid_or_market_blob_reparse"].startswith("FORBIDDEN_OR_INSUFFICIENT")


def test_capture_contract_is_exact_for_required_field_groups():
    contract = load_json("FORWARD_CAPTURE_CONTRACT")
    groups = {row["field_group"]: row for row in contract["field_groups"]}

    for field in {
        "intended_side_direction",
        "intended_entry_reference",
        "intended_stop_reference",
        "intended_target_reference",
        "poi_type_bounds_source",
        "framework_setup_family",
        "lifecycle_fill_cancel_expiry_source_status",
        "lower_timeframe_asof_path_availability",
        "future_orderflow_depth_proxy_requirements",
        "baseline_control_fields",
    }:
        assert field in groups
        entry = groups[field]
        assert entry["future_source_or_logger"]
        assert entry["required_fields"]
        assert entry["parser_requirement"]
        assert entry["schema_version_required"] == "scid_forward_source_capture_v1"
        assert entry["redaction_rule"]
        assert entry["as_of_rule"]
        assert entry["no_leak_rule"]
        assert entry["g12_acceptance_requirement"]

    assert "broker" in groups["lifecycle_fill_cancel_expiry_source_status"]["no_leak_rule"]
    assert "target status" in groups["baseline_control_fields"]["no_leak_rule"]


def test_no_live_effect_and_next_g12_prompt_are_frozen():
    readiness = load_json("IMPLEMENTATION_READINESS_NO_LIVE_EFFECT_LEDGER")
    continuation = load_json("RANKED_CONTINUATION_BUNDLE")
    manifest = load_json("OUTPUT_MANIFEST")

    assert readiness["current_route_implemented_live_wiring"] is False
    assert readiness["opens_prompt_config_risk_safety_execution_canary_selector_edit"] is False
    assert continuation["ranked_continuations"][0]["route_id"] == "G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_AUDIT"

    prompt_path = ROOT / continuation["ranked_continuations"][0]["prompt_path"]
    text = prompt_path.read_text(encoding="utf-8")
    assert "Independent G12" in text
    assert "3,014" in text
    assert "NO_PROMOTION_VERDICT" in text
    assert "validation_safe=false" in text
    assert "outcome_review_opened=false" in text
    assert "live_effect=false" in text
    assert "broker account/order/history/deal/position evidence" in text

    assert all(not row["raw_market_blob"] for row in manifest["artifacts"])


def test_completion_audit_and_standalone_verifier_pass():
    result = verify()
    assert result["ok"], result["failures"]
    assert result["candidate_rows_verified"] == 3014

    completion = load_json("COMPLETION_AUDIT")
    assert completion["terminal_decision"] == "BUILT_SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_G12_AUDIT_REQUIRED"
    assert completion["standalone_verifier_ok"] is True
    assert completion["can_mark_goal_complete"] is True
    assert completion["validation_safe"] is False
    assert completion["outcome_review_opened"] is False
    assert completion["live_effect"] is False
