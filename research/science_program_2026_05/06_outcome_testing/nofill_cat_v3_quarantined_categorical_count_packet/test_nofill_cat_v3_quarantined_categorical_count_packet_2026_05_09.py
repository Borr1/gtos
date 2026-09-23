from __future__ import annotations

import json
import os
import sys
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
if str(OUT_DIR) not in sys.path:
    sys.path.insert(0, str(OUT_DIR))

import build_nofill_cat_v3_quarantined_categorical_count_packet_2026_05_09 as builder
import verify_nofill_cat_v3_quarantined_categorical_count_packet_2026_05_09 as verifier


DATE = "2026-05-09"


def load_json(name: str) -> dict:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def load_jsonl(name: str) -> list[dict]:
    return [json.loads(line) for line in (OUT_DIR / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def test_builder_inputs_recompute_exact_accepted_and_exclusion_universe() -> None:
    inputs = builder.load_inputs()
    accepted = builder.join_accepted_rows(inputs)
    exclusions = builder.join_exclusion_rows(inputs)
    assert len(accepted) == 225
    assert len({row["packet_row_id"] for row in accepted}) == 225
    assert len(exclusions) == 73
    assert len({row["packet_row_id"] for row in exclusions}) == 73
    assert {row["v3_terminal_family"] for row in accepted} == {"accepted"}
    assert all(row["source_safe_input_only"] is True for row in accepted)
    assert {row["label_class"] for row in accepted} == {"input_only_categorical"}
    exclusion_ids = {row["packet_row_id"] for row in exclusions}
    assert builder.SOURCE_CONTROL_ROWS <= exclusion_ids
    assert builder.SOURCE_IMPOSSIBLE_ROWS <= exclusion_ids
    assert not ({row["packet_row_id"] for row in accepted} & exclusion_ids)


def test_count_ledgers_match_frozen_row_key_and_group_denominators() -> None:
    inputs = builder.load_inputs()
    accepted = builder.join_accepted_rows(inputs)
    count = builder.build_count_ledger(accepted)
    assert count["accepted_row_level_total"] == 225
    assert count["primary_unique_nofill_duplicate_key_total"] == 182
    assert count["secondary_unique_duplicate_group_id_total"] == 139
    assert count["row_level_label_counts"] == builder.EXPECTED_LABEL_COUNTS
    assert count["primary_nofill_duplicate_key_label_counts"] == builder.EXPECTED_KEY_LABEL_COUNTS
    assert count["secondary_duplicate_group_id_label_counts"] == builder.EXPECTED_GROUP_LABEL_COUNTS
    assert "298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject" in count["universe_equation_asserted_before_counts"]


def test_duplicate_conflict_audit_distinguishes_projection_variance_from_blockers() -> None:
    inputs = builder.load_inputs()
    accepted = builder.join_accepted_rows(inputs)
    conflict = builder.duplicate_conflict_audit(accepted)
    assert conflict["accepted_duplicate_key_label_conflict_count"] == 0
    assert conflict["accepted_duplicate_key_source_geometry_conflict_count"] == 0
    assert conflict["accepted_duplicate_key_source_ordering_blocker_count"] == 0
    assert conflict["accepted_duplicate_key_denominator_conflict_count"] == 0
    assert conflict["accepted_projection_variance_key_count"] == 5
    assert conflict["accepted_projection_variance_noncanonical_row_count"] == 43
    duplicate = builder.build_duplicate_diagnostics(accepted, conflict)
    assert duplicate["accepted_noncanonical_projection_count"] == 43
    assert duplicate["max_duplicate_key_row_count"] == 14


def test_reject_overlap_has_zero_denominator_effect() -> None:
    inputs = builder.load_inputs()
    accepted = builder.join_accepted_rows(inputs)
    exclusions = builder.join_exclusion_rows(inputs)
    overlap = builder.build_reject_overlap_audit(accepted, exclusions)
    assert overlap["reject_row_count"] == 65
    assert overlap["reject_key_overlap_with_accepted_count"] == 47
    assert overlap["reject_group_overlap_with_accepted_count"] == 47
    assert overlap["source_control_key_overlap_with_accepted"] == []
    assert overlap["source_impossible_key_overlap_with_accepted"] == []
    assert overlap["denominator_effect"]["row_level_count_delta_from_rejects"] == 0
    assert overlap["denominator_effect"]["nofill_duplicate_key_count_delta_from_rejects"] == 0
    assert overlap["denominator_effect"]["duplicate_group_id_count_delta_from_rejects"] == 0


def test_source_hash_noleak_audit_accepts_only_line_ending_prompt_drift() -> None:
    inputs = builder.load_inputs()
    accepted = builder.join_accepted_rows(inputs)
    exclusions = builder.join_exclusion_rows(inputs)
    audit = builder.build_source_hash_noleak_audit(inputs, accepted, exclusions)
    assert audit["status"] == "PASS"
    assert audit["source_schema_recheck"]["strict_failure_count"] == 0
    assert audit["source_schema_recheck"]["missing_record_count"] == 0
    assert audit["source_schema_recheck"]["line_ending_only_mismatch_count"] == 1
    assert audit["forbidden_row_key_hit_count"] == 0
    assert audit["forbidden_row_string_hit_count"] == 0
    assert audit["safe_flag_issue_packet_row_ids"] == []


def test_generated_artifacts_and_verifier_cover_objective_without_nested_pytest() -> None:
    # This test intentionally reads existing artifacts instead of rebuilding
    # them so committed verification cannot churn context timestamps or HEAD.
    accepted = load_jsonl(f"NOFILL_CAT_V3_COUNT_ACCEPTED_INPUT_ROWS_{DATE}.jsonl")
    exclusions = load_jsonl(f"NOFILL_CAT_V3_COUNT_EXCLUSION_PROOF_LEDGER_{DATE}.jsonl")
    completion = load_json(f"NOFILL_CAT_V3_COUNT_COMPLETION_AUDIT_{DATE}.json")
    assert len(accepted) == 225
    assert len(exclusions) == 73
    assert completion["promotion_verdict"] == "NO_PROMOTION_VERDICT"

    os.environ["NOFILL_CAT_V3_COUNT_PACKET_SKIP_NESTED_PYTEST"] = "1"
    results = verifier.verify_packet(run_pytest=False, write_audit=False, require_committed=False)
    assert results["verification_status"]["status"] == "PASS"
    assert results["artifact_commit_check"]["status"] == "SKIPPED"
    assert results["verification_status"]["can_mark_goal_complete"] is False
