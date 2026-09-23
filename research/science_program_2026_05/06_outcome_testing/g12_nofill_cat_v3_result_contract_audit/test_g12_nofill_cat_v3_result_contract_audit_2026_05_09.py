from __future__ import annotations

import json
import os
import sys
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
if str(OUT_DIR) not in sys.path:
    sys.path.insert(0, str(OUT_DIR))

import build_g12_nofill_cat_v3_result_contract_audit_2026_05_09 as builder
import verify_g12_nofill_cat_v3_result_contract_audit_2026_05_09 as verifier


DATE = "2026-05-09"


def load_json(name: str) -> dict:
    with (OUT_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_builder_accepts_frozen_contract_and_preserves_exact_counts() -> None:
    inputs = builder.load_inputs()
    metrics = builder.compute_metrics(inputs)
    source_hash = builder.build_source_hash_audit(inputs)
    noleak = builder.build_noleak_denominator_audit(inputs, metrics)
    duplicate = builder.build_duplicate_audit(metrics, inputs)
    saturation = builder.build_saturation_review(inputs, metrics)
    decision = builder.build_decision_ledger(inputs, metrics, source_hash, noleak, duplicate, saturation)
    facts = decision["verified_starting_facts"]
    assert decision["overall_decision"] == builder.DECISION
    assert decision["decision_status"] == "PASS_ACCEPTED"
    assert facts["terminal_family_counts"] == {
        "accepted": 225,
        "reject": 65,
        "source_control": 4,
        "source_impossible": 4,
    }
    assert facts["eligible_rows"] == 225
    assert facts["exclusion_rows"] == 73
    assert facts["source_control_rows"] == [
        "NOFILL-CAT-ROW-0049",
        "NOFILL-CAT-ROW-0050",
        "NOFILL-CAT-ROW-0051",
        "NOFILL-CAT-ROW-0241",
    ]
    assert facts["source_impossible_rows"] == [
        "NOFILL-CAT-ROW-0130",
        "NOFILL-CAT-ROW-0143",
        "NOFILL-CAT-ROW-0165",
        "NOFILL-CAT-ROW-0178",
    ]
    assert facts["accepted_unique_nofill_duplicate_keys"] == 182
    assert facts["accepted_unique_duplicate_group_ids"] == 139
    assert facts["current_lane_result_records_produced"] == 0
    assert facts["current_lane_scored_metric_values"] == 0


def test_noleak_audit_excludes_all_nonaccepted_rows_and_blocks_scoring_families() -> None:
    inputs = builder.load_inputs()
    metrics = builder.compute_metrics(inputs)
    noleak = builder.build_noleak_denominator_audit(inputs, metrics)
    assert noleak["status"] == "PASS"
    assert noleak["recomputed_universe"]["eligibility_row_count"] == 225
    assert noleak["recomputed_universe"]["exclusion_row_count"] == 73
    assert noleak["exclusion_controls"]["source_control_rows"] == [
        "NOFILL-CAT-ROW-0049",
        "NOFILL-CAT-ROW-0050",
        "NOFILL-CAT-ROW-0051",
        "NOFILL-CAT-ROW-0241",
    ]
    assert noleak["exclusion_controls"]["source_impossible_rows"] == [
        "NOFILL-CAT-ROW-0130",
        "NOFILL-CAT-ROW-0143",
        "NOFILL-CAT-ROW-0165",
        "NOFILL-CAT-ROW-0178",
    ]
    assert noleak["exclusion_controls"]["exclusion_denominator_violations"] == []
    assert noleak["exclusion_controls"]["nonaccepted_denominator_violations"] == []
    assert noleak["forbidden_field_hits"]["v3_row_ledger"] == []
    assert noleak["forbidden_field_hits"]["contract_ledgers"] == []
    assert noleak["label_boundary"]["categorical_labels_are_performance"] is False
    assert noleak["label_boundary"]["current_lane_result_records_produced"] == 0


def test_duplicate_audit_catches_reject_overlap_without_denominator_laundering() -> None:
    inputs = builder.load_inputs()
    metrics = builder.compute_metrics(inputs)
    duplicate = builder.build_duplicate_audit(metrics, inputs)
    assert duplicate["status"] == "PASS"
    state = duplicate["recomputed_duplicate_state"]
    assert state["accepted_row_count"] == 225
    assert state["accepted_unique_nofill_duplicate_keys"] == 182
    assert state["accepted_unique_duplicate_group_ids"] == 139
    assert state["accepted_canonical_duplicate_member_count"] == 182
    assert state["accepted_noncanonical_projection_count"] == 43
    assert state["accepted_duplicate_label_conflict_count"] == 0
    overlap = duplicate["overlap_red_team"]
    assert overlap["source_control_key_overlap_with_accepted"] == []
    assert overlap["source_impossible_key_overlap_with_accepted"] == []
    assert overlap["reject_key_overlap_with_accepted_count"] == 47
    assert "must not add to or subtract from" in overlap["interpretation"]


def test_source_hash_audit_rechecks_schema_records_and_records_hash_exceptions() -> None:
    inputs = builder.load_inputs()
    source = builder.build_source_hash_audit(inputs)
    assert source["status"] == "PASS"
    recheck = source["source_schema_recheck"]
    assert recheck["record_count"] == 30
    assert recheck["strict_failure_count"] == 0
    assert recheck["missing_record_count"] == 0
    assert recheck["line_ending_only_mismatch_count"] == 1
    assert recheck["mutable_context_presence_count"] == 8


def test_saturation_and_verifier_pass_without_nested_pytest() -> None:
    inputs = builder.load_inputs()
    metrics = builder.compute_metrics(inputs)
    saturation = builder.build_saturation_review(inputs, metrics)
    assert saturation["status"] == "PASS"
    assert saturation["same_evidence_class_ambiguities_closed_or_routed"] is True
    assert len(saturation["questions"]) >= 12
    assert any("broker-native USDJPY quote-event sequence" in item for item in saturation["external_requirements"])

    os.environ["G12_NOFILL_CAT_V3_RESULT_CONTRACT_AUDIT_SKIP_NESTED_PYTEST"] = "1"
    results = verifier.verify_audit(run_pytest=False, write_audit=False, require_committed=False)
    assert results["verification_status"]["status"] == "PASS"
    assert results["artifact_commit_check"]["status"] == "SKIPPED"
    assert results["verification_status"]["can_mark_goal_complete"] is False
