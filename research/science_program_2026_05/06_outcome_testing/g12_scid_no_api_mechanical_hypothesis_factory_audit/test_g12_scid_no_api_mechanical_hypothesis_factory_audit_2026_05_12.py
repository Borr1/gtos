from __future__ import annotations

import json
from pathlib import Path

from verify_g12_scid_no_api_mechanical_hypothesis_factory_audit_2026_05_12 import verify


ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_NO_API_HYP_FACTORY_AUDIT"


def load_json(stem: str) -> dict:
    return json.loads((ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json").read_text(encoding="utf-8"))


def test_context_inventory_reads_builder_prompt_and_all_generated_artifacts():
    audit = load_json("CONTEXT_AND_INPUT_INVENTORY")

    assert audit["mandatory_preflight_recorded"]["generate_live_state_ran_this_session"] is True
    assert audit["mandatory_preflight_recorded"]["goal_session_research_discipline_read"] is True
    assert audit["mandatory_preflight_recorded"]["builder_prompt_read"] is True
    assert audit["input_route_file_count"] == 37
    assert audit["all_input_route_artifacts_read"] is True
    assert audit["parse_failures"] == []
    assert all(row["read"] for row in audit["required_prompt_context"])


def test_card_schema_count_recomputes_all_40_machine_checkable_cards():
    audit = load_json("CARD_SCHEMA_COUNT_RECOMPUTATION")

    assert audit["card_count_recomputed"] == 40
    assert audit["unique_card_count_recomputed"] == 40
    assert audit["required_card_field_count"] == 25
    assert audit["schema_failures"] == []
    assert audit["all_40_card_schemas_machine_checkable"] is True
    assert all(row["schema_ok"] for row in audit["card_rows"])


def test_eight_domain_coverage_and_outside_current_edge_breadth_hold():
    audit = load_json("SCIENCE_DOMAIN_AND_OUTSIDE_CURRENT_EDGE_BREADTH_AUDIT")

    assert audit["domain_count_recomputed"] == 8
    assert audit["all_eight_domains_present"] is True
    assert set(audit["domain_counts_recomputed"].values()) == {5}
    assert audit["outside_current_gtos_ob_framing_count_recomputed"] == 33
    assert min(audit["outside_current_gtos_ob_framing_by_domain"].values()) >= 3
    assert audit["failures"] == []
    assert audit["domain_and_breadth_audit_ok"] is True


def test_matrices_recompute_source_unavailable_future_gate_adversarial_and_readiness():
    audit = load_json("MATRIX_CROSSCHECK_AUDIT")

    assert audit["card_count"] == 40
    assert audit["source_field_checklist_domain_rows"] == 8
    assert audit["readiness_matrix_row_count"] == 40
    assert audit["readiness_status_counts_recomputed"] == {
        "BLOCKED_PENDING_FUTURE_CAPTURE_FIELDS": 15,
        "BLOCKED_PENDING_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION": 17,
        "PREREGISTERABLE_NOW_ACCEPTED_DESCRIPTOR_CONTROL_ONLY": 8,
    }
    assert audit["adversarial_matrix_row_count"] == 40
    assert set(audit["required_placebo_families_present"]) >= {
        "session_only",
        "volatility_only",
        "duplicate_key_random_proxy",
        "side_flip_after_capture",
        "translated_poi_after_capture",
    }
    assert audit["future_result_gate_count"] == 6
    assert audit["future_result_design_opened_now"] is False
    assert audit["future_no_api_route_count"] == 5
    assert audit["matrix_failures"] == []
    assert audit["matrix_crosscheck_ok"] is True


def test_boundary_manifest_binding_noleak_and_verifier_accept():
    boundary = load_json("BOUNDARY_CAPTURE_MANIFEST_AUDIT")
    noleak = load_json("NOLEAK_SCOPED_DIFF_AUDIT")
    decision = load_json("DECISION_LEDGER")
    result = verify(mark_focused_tests_ok=True)

    assert boundary["candidate_rows_boundary_recomputed"] == 3014
    assert boundary["duplicate_proxy_denominator_key_boundary_recomputed"] == 3014
    assert boundary["capture_group_count"] == 10
    assert boundary["all_ten_capture_groups_preserved"] is True
    assert boundary["blocking_unrepaired_hash_mismatches"] == []
    assert boundary["missing_manifest_artifacts"] == []
    assert boundary["raw_manifest_entries"] == []
    assert boundary["boundary_capture_manifest_audit_ok"] is True
    assert noleak["no_leak_scoped_diff_ok"] is True
    assert decision["terminal_decision"] == "ACCEPT_AS_G12_SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_CONTROL_EVIDENCE_ONLY"
    assert decision["terminal_blockers"] == []
    assert result["ok"], result["failures"]
