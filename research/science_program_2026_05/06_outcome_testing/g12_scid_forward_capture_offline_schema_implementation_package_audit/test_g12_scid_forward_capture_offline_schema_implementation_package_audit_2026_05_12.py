from __future__ import annotations

import json
from pathlib import Path

from verify_g12_scid_forward_capture_offline_schema_implementation_package_audit_2026_05_12 import verify


ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_FC_SCHEMA_AUDIT"


def load_json(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_context_inventory_reads_every_input_route_artifact():
    audit = load_json("CONTEXT_AND_ARTIFACT_INVENTORY")
    inventory = audit["input_route_artifact_inventory"]

    assert audit["mandatory_preflight_recorded"]["generate_live_state_ran_this_session"] is True
    assert audit["mandatory_preflight_recorded"]["goal_session_research_discipline_read"] is True
    assert inventory["all_input_route_artifacts_read"] is True
    assert inventory["artifact_count"] >= 59
    assert inventory["parse_failures"] == []


def test_schema_contract_covers_all_groups_and_required_metadata():
    audit = load_json("SCHEMA_CONTRACT_AUDIT")
    groups = {row["field_group"]: row for row in audit["group_summaries"]}

    assert audit["candidate_rows_coverage_expectation"] == 3014
    assert audit["duplicate_proxy_denominator_key_coverage_expectation"] == 3014
    assert audit["schema_file_count"] == 11
    assert sorted(audit["accepted_capture_groups"]) == sorted(groups)
    assert audit["schema_contract_failures"] == []
    assert audit["schema_contract_audit_ok"] is True
    for group, row in groups.items():
        assert row["schema_closed_additional_properties"] is True, group
        assert row["all_common_fields_required"] is True, group
        assert row["all_group_fields_required"] is True, group
        assert row["all_contract_metadata_present"] is True, group
        assert row["as_of_rule"], group
        assert row["future_source_or_logger"], group
        assert row["no_leak_rule"], group


def test_independent_fixture_validator_recomputes_pass_and_fail_closed_cases():
    audit = load_json("FIXTURE_VALIDATOR_RECOMPUTATION_AUDIT")
    by_id = {row["fixture_id"]: row for row in audit["independent_fixture_results"]}

    assert audit["fixture_count"] == 18
    assert audit["valid_fixture_pass_count"] == 5
    assert audit["invalid_fixture_fail_closed_count"] == 13
    assert audit["fixture_validator_failures"] == []
    assert audit["fixture_validator_recomputation_ok"] is True
    assert by_id["fully_populated_synthetic_source_safe_rowset"]["observed_valid"] is True
    assert by_id["ltf_unavailable_fail_closed_valid"]["observed_valid"] is True
    assert by_id["orderflow_proxy_unavailable_fail_closed_valid"]["observed_valid"] is True
    assert by_id["forbidden_broker_identifier_fail_closed"]["observed_valid"] is False
    assert by_id["stale_asof_violation_fail_closed"]["observed_valid"] is False
    assert by_id["duplicate_denominator_mismatch_fail_closed"]["observed_valid"] is False
    assert by_id["manifest_binding_repair_continuity"]["observed_valid"] is True


def test_manifest_repair_readonly_alignment_and_no_leak_boundaries_hold():
    audit = load_json("MANIFEST_READONLY_NOLEAK_AUDIT")

    assert audit["blocking_unrepaired_hash_mismatches"] == []
    assert audit["strict_input_hash_mismatches"] == []
    assert audit["repaired_hash_binding_mismatches"]
    assert audit["nonblocking_self_manifest_mismatches"]
    assert audit["builder_repair_policy"]["current_g12_prompt_hash_supersedes_stale_pre_hardening_hash"] is True
    assert audit["builder_repair_policy"]["builder_output_manifest_self_hash_is_non_blocking"] is True
    assert audit["builder_repair_policy"]["all_other_source_input_hash_mismatches_are_strict_blockers"] is True
    assert audit["read_only_alignment_target_count"] >= 10
    assert audit["read_only_alignment_failures"] == []
    assert audit["live_wiring_absence_required_boundary"] is True
    assert audit["raw_manifest_entries"] == []
    assert audit["manifest_readonly_noleak_failures"] == []
    assert audit["manifest_readonly_noleak_audit_ok"] is True


def test_decision_next_prompt_and_standalone_verifier_pass():
    decision = load_json("DECISION_LEDGER")
    output = load_json("OUTPUT_MANIFEST")
    result = verify()

    assert result["ok"], result["failures"]
    assert result["candidate_rows_verified"] == 3014
    assert result["fixture_count_verified"] == 18
    assert decision["terminal_decision"] == "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY"
    assert decision["terminal_blockers"] == []
    assert decision["accepted_g12_control_evidence_only"] is True
    assert decision["accepted_validation_execution"] is False
    assert decision["accepted_strategy_performance"] is False
    assert decision["accepted_promotion"] is False
    assert all(output["required_artifact_families_covered"].values())
    assert all(not row["raw_market_blob"] for row in output["artifacts"])

    next_prompt = ROUTE_DIR.parents[1] / "04_goal_prompts" / "G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_PROMPT_2026-05-12.md"
    text = next_prompt.read_text(encoding="utf-8")
    assert "NO_PROMOTION_VERDICT" in text
    assert "validation_safe=false" in text
    assert "outcome_review_opened=false" in text
    assert "live_effect=false" in text
    assert "manifest-binding repair" in text
