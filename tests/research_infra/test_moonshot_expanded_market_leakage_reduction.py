from src.research_infra.moonshot_expanded_market_leakage_reduction import (
    compact_leakage_reduction_row,
    event_matches_reduction_scope,
    extract_scope,
    main_action_class,
    summarize_leakage_reduction_intake,
)


def _base_row(**overrides):
    row = {
        "leakage_reduction_row_id": "OHLC-GTOS-EXPANDED-MARKET-LEAKAGE-REDUCTION-0000001",
        "input_code_candidate_execution_row_id": "exec-1",
        "input_code_candidate_row_id": "candidate-1",
        "input_implementation_selection_row_id": "select-1",
        "candidate_function_name": "expanded_market_side_filter_TEST_M15_h16",
        "symbol": "TEST",
        "source_symbol": "TEST",
        "market_timeframe": "M15",
        "route_session": "london_kz",
        "horizon_id": "h16",
        "source_component": "unit_test",
        "source_path": "data/TEST_M15.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "target_selected_intrabar_cost_adjusted_simulated_r": 0.30,
        "target_selected_minus_rejected_intrabar_cost_adjusted_r": 0.45,
        "target_temporal_winner_consistency_share": 1.0,
        "target_temporal_positive_winner_fold_share": 1.0,
        "target_effective_n": 36,
        "target_selected_intrabar_target_first_count": 30,
        "target_selected_intrabar_stop_first_count": 5,
        "target_selected_intrabar_neither_count": 1,
        "target_selected_intrabar_ambiguous_count": 0,
        "matched_selection_rows": 1,
        "matched_implement_rows": 1,
        "matched_nonimplement_rows": 0,
        "matched_avoid_rows": 0,
        "matched_kill_rows": 0,
        "matched_redesign_rows": 0,
        "selection_precision": 1.0,
        "average_selected_intrabar_cost_adjusted_simulated_r": 0.30,
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_LEAKAGE_REDUCED_CODE_CANDIDATE",
    }
    row.update(overrides)
    return row


def test_extract_scope_rebuilds_thresholded_scope_when_missing():
    scope = extract_scope(_base_row())

    assert scope["symbol"] == "TEST"
    assert scope["source_path"] == "data/TEST_M15.csv"
    assert scope["source_file_sha256"] == "abc123"
    assert scope["numeric_thresholds"]["selected_intrabar_cost_adjusted_simulated_r"] == 0.30
    assert scope["numeric_thresholds"]["selected_minus_rejected_intrabar_cost_adjusted_r"] == 0.45


def test_event_matches_reduction_scope_requires_source_hash_and_thresholds():
    scope = extract_scope(_base_row())
    matching_event = {
        "symbol": "TEST",
        "source_symbol": "TEST",
        "market_timeframe": "M15",
        "route_session": "london_kz",
        "horizon_id": "h16",
        "source_component": "unit_test",
        "selected_side": "LONG",
        "source_path": "data/TEST_M15.csv",
        "source_file_sha256": "abc123",
        "selected_intrabar_cost_adjusted_simulated_r": 0.31,
        "selected_minus_rejected_intrabar_cost_adjusted_r": 0.45,
        "temporal_winner_consistency_share": 1.0,
        "temporal_positive_winner_fold_share": 1.0,
    }

    assert event_matches_reduction_scope(matching_event, scope) is True

    wrong_hash = {**matching_event, "source_file_sha256": "def456"}
    too_weak = {**matching_event, "selected_intrabar_cost_adjusted_simulated_r": 0.29}

    assert event_matches_reduction_scope(wrong_hash, scope) is False
    assert event_matches_reduction_scope(too_weak, scope) is False


def test_compact_leakage_reduction_row_preserves_replay_reference_without_counting_as_result():
    compact = compact_leakage_reduction_row(
        _base_row(),
        intake_row_id="MAIN-INTAKE-000001",
        source_artifact="moonshot.jsonl",
        source_line_no=3,
        source_sha256="sha",
    )

    assert compact["main_action_class"] == "IMPLEMENT_DEFAULT_OFF_LEAKAGE_REDUCED"
    assert compact["main_compiler_action"] == "REGISTER_DEFAULT_OFF_LEAKAGE_REDUCED_SIDE_FILTER_SCOPE"
    assert compact["target_selected_intrabar_cost_adjusted_simulated_r"] == 0.30
    assert compact["proxy_r_reference_counted_as_result"] is False
    assert compact["research_boundary"]["runtime_candidate_use_permitted"] is False
    assert compact["source_line_no"] == 3


def test_preserved_and_redesign_action_classes_are_distinct():
    assert (
        main_action_class("IMPLEMENT_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION_PRESERVED")
        == "IMPLEMENT_DEFAULT_OFF_PRESERVED"
    )
    assert main_action_class("REDESIGN_EXPANDED_MARKET_LEAKAGE_REDUCTION_REMAINS") == "REDESIGN"


def test_summarize_leakage_reduction_intake_counts_all_material_rows():
    rows = [
        compact_leakage_reduction_row(
            _base_row(),
            intake_row_id="MAIN-INTAKE-000001",
            source_artifact="moonshot.jsonl",
            source_line_no=1,
            source_sha256="sha",
        ),
        compact_leakage_reduction_row(
            _base_row(
                leakage_reduction_row_id="OHLC-GTOS-EXPANDED-MARKET-LEAKAGE-REDUCTION-0000002",
                keep_kill_redesign_implement_decision="IMPLEMENT_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION_PRESERVED",
                matched_selection_rows=2,
                matched_implement_rows=2,
                target_selected_intrabar_cost_adjusted_simulated_r=0.10,
                average_selected_intrabar_cost_adjusted_simulated_r=0.12,
            ),
            intake_row_id="MAIN-INTAKE-000002",
            source_artifact="moonshot.jsonl",
            source_line_no=2,
            source_sha256="sha",
        ),
    ]

    summary = summarize_leakage_reduction_intake(rows)

    assert summary["rows"] == 2
    assert summary["main_action_class_counts"] == {
        "IMPLEMENT_DEFAULT_OFF_LEAKAGE_REDUCED": 1,
        "IMPLEMENT_DEFAULT_OFF_PRESERVED": 1,
    }
    assert summary["target_selected_intrabar_cost_adjusted_simulated_r_rows"] == 2
    assert summary["target_selected_intrabar_cost_adjusted_simulated_r_sum_reference"] == 0.4
    assert summary["matched_selection_rows"] == 3
    assert summary["matched_implement_rows"] == 3
    assert summary["proxy_r_reference_counted_as_result_rows"] == 0
    assert summary["runtime_candidate_use_permitted_rows"] == 0
