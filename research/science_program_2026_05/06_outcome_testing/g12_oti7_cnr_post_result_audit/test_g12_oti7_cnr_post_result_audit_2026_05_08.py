import importlib.util
from pathlib import Path

import pytest


BUILDER_PATH = (
    Path(__file__).resolve().parent
    / "build_g12_oti7_cnr_post_result_audit_2026_05_08.py"
)


def load_builder():
    spec = importlib.util.spec_from_file_location("g12_oti7_post_builder_test", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def artifacts():
    return load_builder().build_bundle()["artifacts"]


def test_decision_accepts_only_quarantined_negative_discovery_evidence(artifacts):
    decision = artifacts["decision"][0]
    completion = artifacts["completion"][0]

    assert decision["decision"] == "ACCEPT_AS_QUARANTINED_NEGATIVE_DISCOVERY_EVIDENCE"
    assert decision["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False
    assert decision["negative_result_is_rejection_reason"] is False
    assert decision["small_effective_n_is_rejection_reason"] is False
    assert completion["can_mark_goal_complete"] is True


def test_row_scope_excludes_blocked_rows_and_preserves_duplicate_policy(artifacts):
    rowdup = artifacts["row_duplicate"][0]
    scope = rowdup["row_scope_controls"]

    assert rowdup["audit_status"] == "PASS"
    assert scope["accepted_rows_processed"] == 102
    assert scope["jsonl_rows"] == 102
    assert scope["g12_ready_rows"] == 102
    assert scope["blocked_rows_excluded"] == 6098
    assert scope["accepted_blocked_row_sha_overlap_count"] == 0
    assert scope["accepted_blocked_row_number_overlap_count"] == 0
    assert scope["countable_rows"] == 54
    assert scope["duplicate_context_rows"] == 48
    assert scope["countable_unique_duplicate_groups"] == 27
    assert scope["scored_countable_unique_duplicate_groups"] == 22


def test_source_and_noleak_controls_are_clean(artifacts):
    source = artifacts["source_noleak"][0]
    controls = source["source_controls"]

    assert source["audit_status"] == "PASS"
    assert controls["source_file_count"] == 16
    assert controls["source_rehash_missing_count"] == 0
    assert controls["source_rehash_mismatch_count"] == 0
    assert controls["quote_recompute_mismatch_count"] == 0
    assert controls["listed_source_hash_mismatch_count"] == 0
    assert controls["g12_strict_hash_mismatch_count"] == 0
    assert controls["g12_asof_issue_count"] == 0
    assert controls["ready_input_forbidden_key_hit_count"] == 0
    assert controls["flag_issues"] == []
    assert source["label_family_boundary"]["broker_actual_r_inspected"] is False
    assert source["label_family_boundary"]["hidden_path_labels_read"] is False


def test_geometry_quote_side_and_result_counts_are_stable(artifacts):
    geometry = artifacts["geometry"][0]
    controls = geometry["geometry_quote_controls"]

    assert geometry["audit_status"] == "PASS"
    assert controls["issue_count"] == 0
    assert controls["status_counts"] == {
        "SCORED_STOP_FIRST": 64,
        "SCORED_TARGET_FIRST": 12,
        "UNSCOREABLE_MISSING_SOURCE_GEOMETRY": 8,
        "UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY": 18,
    }
    assert controls["scored_rows"] == 76
    assert controls["unscoreable_rows"] == 26
    assert controls["target_already_passed_count"] == 0
    assert controls["target_first_r_values"]["n"] == 12
    assert controls["target_first_r_values"]["min"] == 0.054478
    assert controls["target_first_r_values"]["max"] == 0.108085


def test_negative_forensics_and_methodology_do_not_promote(artifacts):
    forensics = artifacts["forensics"][0]
    methodology = artifacts["methodology"][0]
    next_map = artifacts["next_map"][0]

    assert forensics["scored_stop_first_rate"] == 0.842105
    assert forensics["countable_scored_stop_first_rate"] == 0.772727
    assert forensics["by_side"]["LONG"]["r_summary_scored"]["mean_r"] == -1.0
    assert methodology["methodology_status"] == "PASS_DESCRIPTIVE_ONLY_NOT_VALIDATION"
    assert methodology["dsr"]["status"] == "not_computable"
    assert methodology["pbo"]["status"] == "not_computable"
    assert methodology["validation_safe_barrier"]["validation_safe"] is False
    assert "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK outcomes remain closed" in next_map["blocked_family_exclusions_preserved"]
