import importlib.util
from pathlib import Path


BUILDER_PATH = (
    Path(__file__).resolve().parent
    / "build_oti4_g6_opening_drive_quarantined_results_2026_05_07.py"
)


def load_builder():
    spec = importlib.util.spec_from_file_location("oti4_g6_opening_drive_builder", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_oti4_uses_only_accepted_packet_and_preserves_quarantine_flags():
    builder = load_builder()
    bundle = builder.build_bundle()
    ledger = bundle["result_ledger"]

    assert ledger["packet_id"] == "OTG0-PKT-062"
    assert ledger["experiment_id"] == "G6-EXP-003-OPENING-DRIVE-CONTINUATION"
    assert ledger["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert ledger["validation_safe"] is False
    assert ledger["outcome_review_opened"] is False
    assert ledger["broker_actual_r_inspected"] is False
    assert ledger["blocked_packet_outcomes_inspected"] is False
    assert ledger["live_trade_results_inspected"] is False
    assert ledger["raw_path_order_labels_inspected"] is False


def test_oti4_proves_opening_drive_result_not_computable_from_packet():
    builder = load_builder()
    bundle = builder.build_bundle()
    ledger = bundle["result_ledger"]
    source = bundle["source_report"]

    assert ledger["raw_record_count"] == 86
    assert ledger["unique_duplicate_group_count"] == 19
    assert ledger["prereg_countable_unique_groups"] == 0
    assert ledger["summary_result"]["status"] == "NOT_COMPUTABLE"
    assert ledger["summary_result"]["computed_continuation_expectancy_r"] is None
    assert ledger["opening_status_counts"] == {"SOURCE_BLOCKED_NO_RANGE_BARS_ASOF": 86}
    assert source["row_source_hash_failure_count"] == 0
    assert source["rows_with_range_bars"] == 0
    assert source["rows_with_path_bars"] == 0
    assert source["rows_decision_after_ohlc_last"] == 86
    assert all(row["quarantined_result_status"] == "NOT_COMPUTABLE_SOURCE_BLOCKED" for row in ledger["rows"])


def test_oti4_duplicate_label_noleak_and_stats_guards_are_explicit():
    builder = load_builder()
    bundle = builder.build_bundle()

    duplicate = bundle["duplicate_report"]
    label = bundle["label_report"]
    noleak = bundle["noleak_report"]
    methodology = bundle["methodology"]
    completion = bundle["completion"]

    assert duplicate["denominator_inflation_factor_raw_over_unique"] > 4.0
    assert duplicate["prereg_countable_unique_groups"] == 0
    assert label["broker_path_lifecycle_pooling_allowed"] is False
    assert label["synthetic_path_result_values_computed"] is False
    assert noleak["forbidden_record_key_hit_count"] == 0
    assert noleak["hidden_path_label_search"]["raw_candidate_ltf_path_order_opened"] is False
    assert methodology["dsr"]["status"] == "not_computable"
    assert methodology["pbo"]["status"] == "not_computable"
    assert methodology["effective_n"]["status"] == "not_computable"
    assert completion["can_mark_goal_complete"] is True
