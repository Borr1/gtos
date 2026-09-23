import importlib.util
from pathlib import Path

import pytest


BUILDER_PATH = (
    Path(__file__).resolve().parent
    / "build_oti7_cnr_accepted_quarantined_results_2026_05_08.py"
)


def load_builder():
    spec = importlib.util.spec_from_file_location("oti7_cnr_builder", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bundle():
    return load_builder().build_bundle()


def test_oti7_scope_flags_and_blocked_rows_are_enforced(bundle):
    ledger = bundle["artifacts"]["OTI7_CNR_RESULT_LEDGER"][0]
    completion = bundle["artifacts"]["OTI7_CNR_COMPLETION_AUDIT"][0]

    assert ledger["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert ledger["validation_safe"] is False
    assert ledger["outcome_review_opened"] is False
    assert ledger["live_effect"] is False
    assert ledger["accepted_ready_row_count"] == 102
    assert ledger["blocked_rows_excluded"] == 6098
    assert ledger["countable_rows"] == 54
    assert ledger["duplicate_context_rows"] == 48
    assert completion["can_mark_goal_complete"] is True
    assert all(row["validation_safe"] is False for row in ledger["rows"])
    assert all(row["outcome_review_opened"] is False for row in ledger["rows"])
    assert all(row["live_effect"] is False for row in ledger["rows"])


def test_oti7_result_counts_are_stable_and_terminal_scoring_is_tick_based(bundle):
    ledger = bundle["artifacts"]["OTI7_CNR_RESULT_LEDGER"][0]
    source = bundle["artifacts"]["OTI7_CNR_SOURCE_HASH_PATH_COVERAGE_AUDIT"][0]

    assert ledger["status_counts"] == {
        "SCORED_STOP_FIRST": 64,
        "SCORED_TARGET_FIRST": 12,
        "UNSCOREABLE_MISSING_SOURCE_GEOMETRY": 8,
        "UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY": 18,
    }
    assert ledger["scored_rows"] == 76
    assert ledger["r_summary_all_rows"]["mean_r"] == -0.829271
    assert ledger["r_summary_countable_rows"]["scored_rows"] == 44
    assert ledger["r_summary_countable_rows"]["mean_r"] == -0.755473
    assert source["quote_recompute_mismatch_count"] == 0
    assert source["listed_source_hash_mismatch_count"] == 0
    assert source["source_file_count"] >= 13
    assert all(
        row["terminal_quote_side"] in {"bid", "ask"}
        for row in ledger["rows"]
        if row["quarantined_result_status"].startswith("SCORED_")
    )


def test_oti7_timing_duplicate_noleak_and_methodology_guards(bundle):
    ledger = bundle["artifacts"]["OTI7_CNR_RESULT_LEDGER"][0]
    duplicate = bundle["artifacts"]["OTI7_CNR_DUPLICATE_EFFECTIVE_N_AUDIT"][0]
    noleak = bundle["artifacts"]["OTI7_CNR_NOLEAK_LABEL_FAMILY_AUDIT"][0]
    methodology = bundle["artifacts"]["OTI7_CNR_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT"][0]

    expected_family_counts = {
        "SCORED_STOP_FIRST": 32,
        "SCORED_TARGET_FIRST": 6,
        "UNSCOREABLE_MISSING_SOURCE_GEOMETRY": 4,
        "UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY": 9,
    }
    for family in [
        "CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1",
        "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1",
    ]:
        assert ledger["by_timing_target"][family]["rows"] == 51
        assert ledger["by_timing_target"][family]["countable_rows"] == 27
        assert ledger["by_timing_target"][family]["status_counts"] == expected_family_counts

    assert duplicate["accepted_blocker_row_sha_overlap_count"] == 0
    assert duplicate["accepted_blocker_row_number_overlap_count"] == 0
    assert duplicate["result_scored_countable_rows"] == 44
    assert noleak["forbidden_input_key_fragment_hit_count"] == 0
    assert noleak["broker_actual_r_inspected"] is False
    assert noleak["hidden_path_labels_read"] is False
    assert methodology["dsr"]["status"] == "not_computable"
    assert methodology["pbo"]["status"] == "not_computable"
    assert methodology["effective_n"]["status"] == "descriptive_only_not_validation"
