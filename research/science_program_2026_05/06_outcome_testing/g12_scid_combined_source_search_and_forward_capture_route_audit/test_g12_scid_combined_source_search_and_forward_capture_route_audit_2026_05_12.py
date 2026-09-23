from __future__ import annotations

import json
from pathlib import Path

from verify_g12_scid_combined_source_search_and_forward_capture_route_audit_2026_05_12 import verify


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[3]
DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT"


def load_json(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_row_coverage_denominator_and_row_hashes_are_recomputed():
    audit = load_json("ROW_COVERAGE_DENOMINATOR_RECOMPUTATION_AUDIT")

    assert audit["builder_candidate_rows"] == 3014
    assert audit["builder_unique_candidate_input_row_ids"] == 3014
    assert audit["builder_unique_duplicate_proxy_denominator_keys"] == 3014
    assert audit["packet_candidate_rows"] == 3014
    assert audit["packet_unique_candidate_input_row_ids"] == 3014
    assert audit["packet_unique_duplicate_proxy_denominator_keys"] == 3014
    assert audit["candidate_id_set_drift"]["missing_from_builder"] == []
    assert audit["candidate_id_set_drift"]["extra_in_builder"] == []
    assert audit["denominator_mismatch_count"] == 0
    assert audit["top_level_mismatch_count"] == 0
    assert audit["row_hash_mismatch_count"] == 0
    assert audit["row_coverage_denominator_recomputation_ok"] is True


def test_field_status_counts_cover_required_families_exactly():
    audit = load_json("FIELD_STATUS_RECOMPUTATION_AUDIT")
    counts = audit["field_status_counts_recomputed"]

    assert counts["intended_side_direction"]["NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_CONTRACT_FROZEN"] == 3014
    assert counts["intended_entry_reference"]["NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_CONTRACT_FROZEN"] == 3014
    assert counts["intended_stop_reference"]["NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_CONTRACT_FROZEN"] == 3014
    assert counts["intended_target_reference"]["NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_CONTRACT_FROZEN"] == 3014
    assert counts["poi_type_bounds_source"]["NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_CONTRACT_FROZEN"] == 3014
    assert counts["framework_setup_family"]["NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_CONTRACT_FROZEN"] == 3014
    assert counts["lifecycle_fill_cancel_expiry_source_status"]["NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_CONTRACT_FROZEN"] == 3014
    assert counts["lower_timeframe_asof_path_availability"]["RECOVERABLE_MARKET_CONTEXT_CAPTURE_CONTRACT_FROZEN"] == 3014
    assert counts["future_orderflow_depth_proxy_requirements"]["RECOVERABLE_MARKET_CONTEXT_CAPTURE_CONTRACT_FROZEN"] == 3014
    assert counts["baseline_control_fields"]["CONTROL_CONTRACT_FROZEN_FROM_CLOSED_SOURCE_DESCRIPTORS"] == 3014
    assert counts["broker_account_order_history_deal_position_evidence"]["FORBIDDEN_IN_THIS_EVIDENCE_CLASS"] == 3014
    assert audit["summary_count_mismatches"] == []
    assert audit["unexpected_status_row_count"] == 0
    assert audit["field_status_recomputation_ok"] is True


def test_source_saturation_and_hash_binding_repair_are_explicit():
    saturation = load_json("SOURCE_SEARCH_SATURATION_AUDIT")
    binding = load_json("SOURCE_HASH_MANIFEST_BINDING_AUDIT")

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
    assert required_roots.issubset(set(saturation["builder_searched_root_ids"]))
    assert saturation["required_root_ids_missing_from_builder_ledger"] == []
    assert saturation["builder_totals"]["files_seen"] >= 13143
    assert saturation["builder_totals"]["files_selected_for_parse"] >= 987
    assert saturation["weak_symbol_time_policy"] == "NOT_ACCEPTED_WITHOUT_EXPLICIT_SCID_BINDING"
    assert saturation["historical_recovery_explicit_new_strategy_intent_recoveries"] == 0
    assert saturation["source_search_saturation_ok"] is True

    assert binding["missing_manifest_artifacts"] == []
    assert binding["raw_blob_manifest_entries"] == []
    assert binding["blocking_unrepaired_hash_mismatches"] == []
    assert binding["input_hash_blockers"] == []
    assert any("G12_SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_AUDIT" in path for path in binding["repaired_hash_binding_mismatches"])
    assert binding["source_hash_manifest_binding_ok_after_repair"] is True


def test_capture_contract_and_forbidden_surface_boundaries_hold():
    contract = load_json("CAPTURE_CONTRACT_EXACTNESS_AUDIT")
    noleak = load_json("NOLEAK_FORBIDDEN_SURFACE_AUDIT")
    groups = {row["field_group"]: row for row in contract["field_groups"]}

    for field in [
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
    ]:
        assert field in groups
        assert groups[field]["future_source_or_logger"]
        assert groups[field]["required_fields"]
        assert groups[field]["parser_requirement"]
        assert groups[field]["schema_version_required"] == "scid_forward_source_capture_v1"
        assert groups[field]["redaction_rule"]
        assert groups[field]["as_of_rule"]
        assert groups[field]["no_leak_rule"]
        assert groups[field]["g12_acceptance_requirement"]

    assert contract["capture_contract_exactness_ok"] is True
    assert noleak["candidate_safe_flag_violation_count"] == 0
    assert noleak["forbidden_broker_field_violation_count"] == 0
    assert noleak["builder_related_commit_forbidden_live_surface_violations"] == []
    assert noleak["builder_manifest_raw_market_blob_paths"] == []
    assert noleak["noleak_forbidden_surface_ok"] is True


def test_decision_manifest_next_prompt_and_verifier_pass():
    decision = load_json("DECISION_LEDGER")
    manifest = load_json("OUTPUT_MANIFEST")
    result = verify()

    assert result["ok"], result["failures"]
    assert result["candidate_rows_verified"] == 3014
    assert decision["terminal_decision"] == (
        "ACCEPT_AS_G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_CONTROL_EVIDENCE_ONLY_WITH_MANIFEST_BINDING_REPAIR"
    )
    assert decision["accepted_g12_control_evidence_only"] is True
    assert decision["accepted_validation_execution"] is False
    assert decision["accepted_strategy_performance"] is False
    assert decision["accepted_promotion"] is False
    assert decision["terminal_blockers"] == []
    assert all(manifest["required_artifact_families_covered"].values())
    assert all(not row["raw_market_blob"] for row in manifest["artifacts"])

    next_prompt = ROOT / decision["next_prompt_path"]
    text = next_prompt.read_text(encoding="utf-8")
    assert "NO_PROMOTION_VERDICT" in text
    assert "validation_safe=false" in text
    assert "outcome_review_opened=false" in text
    assert "live_effect=false" in text
    assert "manifest-binding repair" in text
