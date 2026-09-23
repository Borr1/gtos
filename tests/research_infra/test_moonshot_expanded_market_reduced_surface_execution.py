from __future__ import annotations

from src.research_infra.moonshot_expanded_market_reduced_surface_execution import (
    AINarrowingCapacityBlocklist,
    AINarrowingPolicyRegistry,
    ReducedSurfaceCandidateRegistry,
    ai_narrowing_event_from_source_row,
    ai_narrowing_policy_scope_event,
    ai_narrowing_runtime_config_guard_decision,
    compact_reduced_surface_execution_row,
    emit_reduced_surface_event_for_priority_group,
    event_matches_surface_scope,
    event_from_candidate_scope,
    execution_action_class,
    execution_integrity_status,
    final_review_adjusted_event_registry_scores,
    final_review_ai_narrowing_capacity_blocklist_row,
    final_review_selector_ai_narrowing_policy_row,
    final_review_selector_production_change_dossier_row,
    final_review_adjusted_selector_recommendations,
    reduced_surface_event_emitter_contract_for_priority_group,
    reduced_surface_candidate_event_rollups,
    reduced_surface_event_score,
    reduced_surface_event_from_source_row,
    reduced_surface_source_capture_priority_groups,
    required_event_fields_for_candidate,
    source_capture_contract_for_candidate,
    summarize_ai_narrowing_policy_registry_evaluations,
    summarize_ai_narrowing_policy_events,
    summarize_ai_narrowing_capacity_blocklist,
    summarize_ai_narrowing_runtime_config_guard_decisions,
    summarize_reduced_surface_event_emitter_contracts,
    summarize_reduced_surface_candidate_event_rollups,
    summarize_reduced_surface_events,
    summarize_reduced_surface_candidates,
    summarize_final_review_adjusted_event_registry_scores,
    summarize_final_review_selector_ai_narrowing_policy,
    summarize_final_review_selector_production_change_dossier,
    summarize_final_review_adjusted_selector_recommendations,
    summarize_reduced_surface_source_capture_priority_groups,
    summarize_source_capture_contracts,
)


def _execution_row(**overrides):
    row = {
        "reduced_surface_execution_row_id": "EXEC-1",
        "input_leakage_reduction_row_id": "LEAK-1",
        "input_reduced_surface_row_id": "SURF-1",
        "surface_function_name": "expanded_market_reduced_surface_abc",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "H4",
        "route_session": "london_core",
        "horizon_id": "h16",
        "source_component": "shadow_source_guard",
        "source_path": "data/historical_2026/XAUUSD_H4.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "surface_scope_sha256": "scope-sha",
        "expected_matched_selection_rows": 3,
        "matched_selection_rows": 3,
        "matched_implement_rows": 3,
        "matched_nonimplement_rows": 0,
        "matched_avoid_rows": 0,
        "matched_kill_rows": 0,
        "matched_redesign_rows": 0,
        "selection_precision": 1.0,
        "average_selected_intrabar_cost_adjusted_simulated_r": 0.25,
        "execution_status": "REDUCED_SURFACE_EXECUTION_PASS",
        "follow_inverse_default_off_avoid_class": "follow",
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_REDUCED_SURFACE_EXECUTION",
    }
    row.update(overrides)
    return row


def _surface_row(**overrides):
    row = {
        "reduced_surface_row_id": "SURF-1",
        "input_code_candidate_execution_row_id": "CODE-EXEC-1",
        "input_code_candidate_row_id": "CODE-1",
        "input_implementation_selection_row_id": "SEL-1",
        "candidate_function_name": "expanded_market_side_filter_xauusd_h4",
        "surface_function_name": "expanded_market_reduced_surface_abc",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "H4",
        "route_session": "london_core",
        "horizon_id": "h16",
        "source_component": "shadow_source_guard",
        "source_path": "data/historical_2026/XAUUSD_H4.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "surface_scope": {
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "H4",
            "route_session": "london_core",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "source_path": "data/historical_2026/XAUUSD_H4.csv",
            "source_file_sha256": "abc123",
            "selected_side": "LONG",
            "numeric_thresholds": {
                "selected_intrabar_cost_adjusted_simulated_r": 0.25,
                "temporal_winner_consistency_share": 1.0,
            },
        },
        "surface_scope_sha256": "scope-sha",
        "branch_local_code_expression": "row.get('symbol') == 'XAUUSD'",
        "target_selected_intrabar_cost_adjusted_simulated_r": 0.25,
        "target_rejected_intrabar_cost_adjusted_simulated_r": -0.10,
        "target_selected_minus_rejected_intrabar_cost_adjusted_r": 0.35,
        "target_temporal_winner_consistency_share": 1.0,
        "target_temporal_positive_winner_fold_share": 1.0,
        "target_effective_n": 3,
        "target_selected_intrabar_target_first_count": 2,
        "target_selected_intrabar_stop_first_count": 1,
        "target_selected_intrabar_neither_count": 0,
        "target_selected_intrabar_ambiguous_count": 0,
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_REDUCED_SURFACE",
    }
    row.update(overrides)
    return row


def test_execution_action_class_distinguishes_reduced_and_preserved():
    assert (
        execution_action_class("IMPLEMENT_EXPANDED_MARKET_REDUCED_SURFACE")
        == "REGISTER_DEFAULT_OFF_BRANCH_LOCAL_LEAKAGE_REDUCED_SURFACE_CANDIDATE"
    )
    assert (
        execution_action_class("IMPLEMENT_EXPANDED_MARKET_PRESERVED_REDUCED_SURFACE")
        == "REGISTER_DEFAULT_OFF_BRANCH_LOCAL_PRESERVED_REDUCED_SURFACE_CANDIDATE"
    )


def test_execution_integrity_requires_pass_precision_and_no_nonimplement_matches():
    assert execution_integrity_status(_execution_row()) == "REDUCED_SURFACE_EXECUTION_VERIFIED_PASS"
    assert (
        execution_integrity_status(_execution_row(matched_nonimplement_rows=1))
        == "REDUCED_SURFACE_EXECUTION_REPAIR_REQUIRED"
    )
    assert (
        execution_integrity_status(_execution_row(selection_precision=0.75))
        == "REDUCED_SURFACE_EXECUTION_REPAIR_REQUIRED"
    )


def test_event_matches_surface_scope_requires_base_source_and_thresholds():
    scope = _surface_row()["surface_scope"]
    event = {
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "H4",
        "route_session": "london_core",
        "horizon_id": "h16",
        "source_component": "shadow_source_guard",
        "source_path": "data/historical_2026/XAUUSD_H4.csv",
        "source_file_sha256": "abc123",
        "selected_side": "LONG",
        "selected_intrabar_cost_adjusted_simulated_r": 0.30,
        "temporal_winner_consistency_share": 1.0,
    }
    assert event_matches_surface_scope(event, scope)
    assert not event_matches_surface_scope({**event, "source_file_sha256": "wrong"}, scope)
    assert not event_matches_surface_scope({**event, "selected_intrabar_cost_adjusted_simulated_r": 0.249}, scope)


def test_compact_candidate_preserves_scope_and_disables_runtime_use():
    row = compact_reduced_surface_execution_row(
        _execution_row(),
        _surface_row(),
        candidate_row_id="MAIN-CAND-1",
        execution_source_artifact="execution.jsonl",
        execution_source_line_no=1,
        execution_source_sha256="exec-sha",
        surface_source_artifact="surface.jsonl",
        surface_source_line_no=1,
        surface_source_sha256="surface-sha",
    )
    assert row["candidate_row_id"] == "MAIN-CAND-1"
    assert row["source_reduced_surface_execution_row_id"] == "EXEC-1"
    assert row["surface_scope"]["numeric_thresholds"]["selected_intrabar_cost_adjusted_simulated_r"] == 0.25
    assert row["main_compiler_action"] == "REGISTER_DEFAULT_OFF_BRANCH_LOCAL_LEAKAGE_REDUCED_SURFACE_CANDIDATE"
    assert row["branch_local_candidate_status"] == "READY_DEFAULT_OFF_BRANCH_LOCAL_CANDIDATE"
    assert row["runtime_candidate_use_permitted"] is False
    assert row["candidate_use_allowed_now"] is False
    assert row["replay_r_reference_counted_as_new_main_result"] is False
    assert row["research_boundary"]["runtime_candidate_use_permitted"] is False


def test_summary_preserves_all_material_rows_without_counting_new_result_r():
    rows = [
        compact_reduced_surface_execution_row(
            _execution_row(),
            _surface_row(),
            candidate_row_id="MAIN-CAND-1",
            execution_source_artifact="execution.jsonl",
            execution_source_line_no=1,
            execution_source_sha256="exec-sha",
            surface_source_artifact="surface.jsonl",
            surface_source_line_no=1,
            surface_source_sha256="surface-sha",
        ),
        compact_reduced_surface_execution_row(
            _execution_row(average_selected_intrabar_cost_adjusted_simulated_r=0.15),
            _surface_row(keep_kill_redesign_implement_decision="IMPLEMENT_EXPANDED_MARKET_PRESERVED_REDUCED_SURFACE"),
            candidate_row_id="MAIN-CAND-2",
            execution_source_artifact="execution.jsonl",
            execution_source_line_no=2,
            execution_source_sha256="exec-sha",
            surface_source_artifact="surface.jsonl",
            surface_source_line_no=2,
            surface_source_sha256="surface-sha",
        ),
    ]
    summary = summarize_reduced_surface_candidates(rows)
    assert summary["rows"] == 2
    assert summary["matched_selection_rows"] == 6
    assert summary["matched_nonimplement_rows"] == 0
    assert summary["average_selected_intrabar_cost_adjusted_simulated_r_sum_reference"] == 0.4
    assert summary["replay_r_reference_counted_as_new_main_result_rows"] == 0
    assert summary["runtime_candidate_use_permitted_rows"] == 0
    assert summary["candidate_use_allowed_now_rows"] == 0


def test_registry_returns_all_default_off_matches_for_duplicate_scope():
    first = compact_reduced_surface_execution_row(
        _execution_row(),
        _surface_row(),
        candidate_row_id="MAIN-CAND-1",
        execution_source_artifact="execution.jsonl",
        execution_source_line_no=1,
        execution_source_sha256="exec-sha",
        surface_source_artifact="surface.jsonl",
        surface_source_line_no=1,
        surface_source_sha256="surface-sha",
    )
    second = {**first, "candidate_row_id": "MAIN-CAND-2"}
    registry = ReducedSurfaceCandidateRegistry([first, second])

    matches = registry.evaluate_event(event_from_candidate_scope(first))

    assert [row["candidate_row_id"] for row in matches] == ["MAIN-CAND-1", "MAIN-CAND-2"]
    assert all(row["registry_evaluation_status"] == "DEFAULT_OFF_REDUCED_SURFACE_CANDIDATE_MATCH" for row in matches)
    assert all(row["runtime_candidate_use_permitted"] is False for row in matches)
    assert all(row["candidate_use_allowed_now"] is False for row in matches)
    assert registry.summarize_registry()["duplicate_base_scope_count"] == 1


def test_source_capture_contract_names_evaluator_inputs_without_runtime_use():
    candidate = compact_reduced_surface_execution_row(
        _execution_row(),
        _surface_row(),
        candidate_row_id="MAIN-CAND-1",
        execution_source_artifact="execution.jsonl",
        execution_source_line_no=1,
        execution_source_sha256="exec-sha",
        surface_source_artifact="surface.jsonl",
        surface_source_line_no=1,
        surface_source_sha256="surface-sha",
    )
    contract = source_capture_contract_for_candidate(
        candidate,
        contract_row_id="CONTRACT-1",
        source_artifact="candidate.jsonl",
        source_line_no=1,
        source_sha256="candidate-sha",
    )

    assert contract["candidate_row_id"] == "MAIN-CAND-1"
    assert contract["source_capture_contract_status"] == "READY_DEFAULT_OFF_REDUCED_SURFACE_SOURCE_CAPTURE_CONTRACT"
    assert "source_file_sha256" in contract["required_event_fields"]
    assert "selected_intrabar_cost_adjusted_simulated_r" in contract["required_numeric_threshold_fields"]
    assert contract["event_evaluation_surface"] == "ReducedSurfaceCandidateRegistry.evaluate_event"
    assert contract["runtime_candidate_use_permitted"] is False
    assert contract["candidate_use_allowed_now"] is False
    summary = summarize_source_capture_contracts([contract])
    assert summary["rows"] == 1
    assert summary["runtime_candidate_use_permitted_rows"] == 0
    assert summary["candidate_use_allowed_now_rows"] == 0


def test_event_adapter_builds_contract_complete_registry_event_from_source_row():
    candidate = compact_reduced_surface_execution_row(
        _execution_row(),
        _surface_row(),
        candidate_row_id="MAIN-CAND-1",
        execution_source_artifact="execution.jsonl",
        execution_source_line_no=1,
        execution_source_sha256="exec-sha",
        surface_source_artifact="surface.jsonl",
        surface_source_line_no=1,
        surface_source_sha256="surface-sha",
    )
    event = reduced_surface_event_from_source_row(
        event_from_candidate_scope(candidate),
        event_row_id="EVENT-1",
        source_kind="unit_source_row",
        source_artifact="match.jsonl",
        source_line_no=7,
        source_sha256="match-sha",
        required_event_fields=required_event_fields_for_candidate(candidate),
    )
    registry = ReducedSurfaceCandidateRegistry([candidate])

    matches = registry.evaluate_event(event)

    assert event["event_adapter_status"] == "REDUCED_SURFACE_EVENT_CONTRACT_COMPLETE"
    assert event["missing_required_fields"] == []
    assert event["invalid_numeric_fields"] == []
    assert event["event_source_artifact"] == "match.jsonl"
    assert matches[0]["candidate_row_id"] == "MAIN-CAND-1"
    assert event["runtime_candidate_use_permitted"] is False
    summary = summarize_reduced_surface_events([event])
    assert summary["event_adapter_status_counts"] == {"REDUCED_SURFACE_EVENT_CONTRACT_COMPLETE": 1}
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def test_event_adapter_aliases_current_log_names_but_does_not_treat_source_hash_as_file_sha():
    event = reduced_surface_event_from_source_row(
        {
            "symbol": "XAUUSD",
            "horizon_id": "h16",
            "timeframe": "H4",
            "session": "london_core",
            "side": "LONG",
            "source_component": "shadow_source_guard",
            "source_hash": "row-hash-not-file-sha",
        },
        event_row_id="EVENT-2",
        source_kind="current_shadow_log_row",
    )

    assert event["market_timeframe"] == "H4"
    assert event["route_session"] == "london_core"
    assert event["selected_side"] == "LONG"
    assert event["source_file_sha256"] == ""
    assert event["event_adapter_status"] == "REDUCED_SURFACE_EVENT_CONTRACT_INCOMPLETE"
    assert "source_symbol" in event["missing_required_fields"]
    assert "source_path" in event["missing_required_fields"]
    assert "source_file_sha256" in event["missing_required_fields"]
    assert "selected_intrabar_cost_adjusted_simulated_r" in event["missing_required_fields"]


def test_event_adapter_preserved_candidate_contract_can_require_base_scope_only():
    base_scope = {
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "H4",
        "route_session": "london_core",
        "horizon_id": "h16",
        "source_component": "shadow_source_guard",
        "selected_side": "LONG",
    }
    candidate = compact_reduced_surface_execution_row(
        _execution_row(),
        _surface_row(
            surface_scope=base_scope,
            keep_kill_redesign_implement_decision="IMPLEMENT_EXPANDED_MARKET_PRESERVED_REDUCED_SURFACE",
        ),
        candidate_row_id="MAIN-CAND-PRESERVED",
        execution_source_artifact="execution.jsonl",
        execution_source_line_no=1,
        execution_source_sha256="exec-sha",
        surface_source_artifact="surface.jsonl",
        surface_source_line_no=1,
        surface_source_sha256="surface-sha",
    )

    event = reduced_surface_event_from_source_row(
        dict(base_scope),
        event_row_id="EVENT-3",
        required_event_fields=required_event_fields_for_candidate(candidate),
    )
    matches = ReducedSurfaceCandidateRegistry([candidate]).evaluate_event(event)

    assert required_event_fields_for_candidate(candidate) == [
        "horizon_id",
        "market_timeframe",
        "route_session",
        "selected_side",
        "source_component",
        "source_symbol",
        "symbol",
    ]
    assert event["event_adapter_status"] == "REDUCED_SURFACE_EVENT_CONTRACT_COMPLETE"
    assert event["missing_required_fields"] == []
    assert matches[0]["candidate_row_id"] == "MAIN-CAND-PRESERVED"


def test_event_score_and_candidate_rollup_preserve_duplicate_default_off_matches():
    first = compact_reduced_surface_execution_row(
        _execution_row(),
        _surface_row(),
        candidate_row_id="MAIN-CAND-1",
        execution_source_artifact="execution.jsonl",
        execution_source_line_no=1,
        execution_source_sha256="exec-sha",
        surface_source_artifact="surface.jsonl",
        surface_source_line_no=1,
        surface_source_sha256="surface-sha",
    )
    second = {**first, "candidate_row_id": "MAIN-CAND-2"}
    event = reduced_surface_event_from_source_row(
        event_from_candidate_scope(first),
        event_row_id="EVENT-1",
        required_event_fields=required_event_fields_for_candidate(first),
    )
    event["expected_candidate_row_id"] = "MAIN-CAND-1"
    event["expected_candidate_found"] = True
    registry = ReducedSurfaceCandidateRegistry([first, second])

    score = reduced_surface_event_score(event, registry, event_score_row_id="SCORE-1")
    rollups = reduced_surface_candidate_event_rollups([first, second], [event])
    rollup_by_id = {row["candidate_row_id"]: row for row in rollups}

    assert score["event_score_status"] == "DEFAULT_OFF_REDUCED_SURFACE_EVENT_SCORED_MATCH"
    assert score["registry_matched_candidate_row_ids"] == ["MAIN-CAND-1", "MAIN-CAND-2"]
    assert rollup_by_id["MAIN-CAND-1"]["event_registry_match_rows"] == 1
    assert rollup_by_id["MAIN-CAND-1"]["expected_candidate_event_rows"] == 1
    assert rollup_by_id["MAIN-CAND-2"]["event_registry_match_rows"] == 1
    assert rollup_by_id["MAIN-CAND-2"]["expected_candidate_event_rows"] == 0
    assert rollup_by_id["MAIN-CAND-2"]["duplicate_scope_event_match_rows"] == 1
    summary = summarize_reduced_surface_candidate_event_rollups(rollups)
    assert summary["event_registry_match_rows"] == 2
    assert summary["expected_candidate_event_rows"] == 1
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def test_incomplete_event_is_not_scored_and_rolls_up_as_no_match():
    candidate = compact_reduced_surface_execution_row(
        _execution_row(),
        _surface_row(),
        candidate_row_id="MAIN-CAND-1",
        execution_source_artifact="execution.jsonl",
        execution_source_line_no=1,
        execution_source_sha256="exec-sha",
        surface_source_artifact="surface.jsonl",
        surface_source_line_no=1,
        surface_source_sha256="surface-sha",
    )
    event = reduced_surface_event_from_source_row(
        {"symbol": "XAUUSD"},
        event_row_id="EVENT-INCOMPLETE",
    )

    score = reduced_surface_event_score(event, ReducedSurfaceCandidateRegistry([candidate]))
    rollup = reduced_surface_candidate_event_rollups([candidate], [event])[0]

    assert score["event_score_status"] == "DEFAULT_OFF_REDUCED_SURFACE_EVENT_NOT_SCORED_CONTRACT_INCOMPLETE"
    assert score["registry_matched_candidate_rows"] == 0
    assert rollup["event_registry_match_rows"] == 0
    assert (
        rollup["candidate_event_rollup_status"]
        == "DEFAULT_OFF_REDUCED_SURFACE_CANDIDATE_NO_EVENT_MATCHES_REPAIR_REQUIRED"
    )


def test_source_capture_priority_groups_rank_all_base_scopes_and_required_fields():
    first = compact_reduced_surface_execution_row(
        _execution_row(),
        _surface_row(),
        candidate_row_id="MAIN-CAND-1",
        execution_source_artifact="execution.jsonl",
        execution_source_line_no=1,
        execution_source_sha256="exec-sha",
        surface_source_artifact="surface.jsonl",
        surface_source_line_no=1,
        surface_source_sha256="surface-sha",
    )
    second = {**first, "candidate_row_id": "MAIN-CAND-2"}
    event = reduced_surface_event_from_source_row(
        event_from_candidate_scope(first),
        event_row_id="EVENT-1",
        required_event_fields=required_event_fields_for_candidate(first),
    )
    event["expected_candidate_row_id"] = "MAIN-CAND-1"
    event["expected_candidate_found"] = True
    rollups = reduced_surface_candidate_event_rollups([first, second], [event])
    contracts = [
        source_capture_contract_for_candidate(
            candidate,
            contract_row_id=f"CONTRACT-{index}",
            source_artifact="candidate.jsonl",
            source_line_no=index,
            source_sha256="candidate-sha",
        )
        for index, candidate in enumerate([first, second], start=1)
    ]

    priorities = reduced_surface_source_capture_priority_groups(rollups, contracts)
    priority = priorities[0]

    assert len(priorities) == 1
    assert priority["source_capture_priority_rank"] == 1
    assert priority["candidate_rows"] == 2
    assert priority["event_registry_match_rows"] == 2
    assert priority["expected_candidate_event_rows"] == 1
    assert priority["duplicate_scope_event_match_rows"] == 1
    assert priority["source_capture_priority_class"] == "LEAKAGE_REDUCED_SOURCE_IDENTITY_AND_NUMERIC_CAPTURE"
    assert "source_file_sha256" in priority["required_event_fields"]
    assert "selected_intrabar_cost_adjusted_simulated_r" in priority["required_numeric_threshold_fields"]
    summary = summarize_reduced_surface_source_capture_priority_groups(priorities)
    assert summary["rows"] == 1
    assert summary["candidate_rows"] == 2
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def test_source_capture_priority_group_preserved_scope_needs_base_capture_only():
    base_scope = {
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "H4",
        "route_session": "london_core",
        "horizon_id": "h16",
        "source_component": "shadow_source_guard",
        "selected_side": "LONG",
    }
    candidate = compact_reduced_surface_execution_row(
        _execution_row(),
        _surface_row(
            surface_scope=base_scope,
            keep_kill_redesign_implement_decision="IMPLEMENT_EXPANDED_MARKET_PRESERVED_REDUCED_SURFACE",
        ),
        candidate_row_id="MAIN-CAND-PRESERVED",
        execution_source_artifact="execution.jsonl",
        execution_source_line_no=1,
        execution_source_sha256="exec-sha",
        surface_source_artifact="surface.jsonl",
        surface_source_line_no=1,
        surface_source_sha256="surface-sha",
    )
    event = reduced_surface_event_from_source_row(
        dict(base_scope),
        event_row_id="EVENT-PRESERVED",
        required_event_fields=required_event_fields_for_candidate(candidate),
    )
    rollups = reduced_surface_candidate_event_rollups([candidate], [event])
    contracts = [
        source_capture_contract_for_candidate(
            candidate,
            contract_row_id="CONTRACT-PRESERVED",
            source_artifact="candidate.jsonl",
            source_line_no=1,
            source_sha256="candidate-sha",
        )
    ]

    priority = reduced_surface_source_capture_priority_groups(rollups, contracts)[0]

    assert priority["source_capture_priority_class"] == "PRESERVED_BASE_SCOPE_CAPTURE"
    assert priority["required_source_identity_fields"] == []
    assert priority["required_numeric_threshold_fields"] == []
    assert priority["source_capture_priority_status"] == "DEFAULT_OFF_REDUCED_SURFACE_SOURCE_CAPTURE_PRIORITY_READY"


def test_final_review_adjusted_priority_groups_keep_redesign_subset_out_of_ready_status():
    first = compact_reduced_surface_execution_row(
        _execution_row(),
        _surface_row(),
        candidate_row_id="MAIN-CAND-1",
        execution_source_artifact="execution.jsonl",
        execution_source_line_no=1,
        execution_source_sha256="exec-sha",
        surface_source_artifact="surface.jsonl",
        surface_source_line_no=1,
        surface_source_sha256="surface-sha",
    )
    second = {**first, "candidate_row_id": "MAIN-CAND-2"}
    event = reduced_surface_event_from_source_row(
        event_from_candidate_scope(first),
        event_row_id="EVENT-1",
        required_event_fields=required_event_fields_for_candidate(first),
    )
    event["expected_candidate_row_id"] = "MAIN-CAND-1"
    event["expected_candidate_found"] = True
    rollups = reduced_surface_candidate_event_rollups([first, second], [event])
    for rollup in rollups:
        rollup["final_review_overlay_bound"] = True
        if rollup["candidate_row_id"] == "MAIN-CAND-1":
            rollup["final_review_adjusted_rollup_status"] = "DEFAULT_OFF_FINAL_REVIEW_IMPLEMENT_READY"
            rollup["main_compiler_final_review_action"] = "KEEP_DEFAULT_OFF_FINAL_REVIEW_IMPLEMENT_CANDIDATE"
        else:
            rollup["final_review_adjusted_rollup_status"] = "DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_REDESIGN"
            rollup["main_compiler_final_review_action"] = "REDESIGN_DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_CANDIDATE"
    contracts = [
        source_capture_contract_for_candidate(
            candidate,
            contract_row_id=f"CONTRACT-{index}",
            source_artifact="candidate.jsonl",
            source_line_no=index,
            source_sha256="candidate-sha",
        )
        for index, candidate in enumerate([first, second], start=1)
    ]

    priority = reduced_surface_source_capture_priority_groups(rollups, contracts)[0]
    emitter_contract = reduced_surface_event_emitter_contract_for_priority_group(
        priority,
        contract_row_id="EMITTER-1",
        source_artifact="priority.jsonl",
        source_line_no=1,
        source_sha256="priority-sha",
    )
    summary = summarize_reduced_surface_source_capture_priority_groups([priority])

    assert priority["source_capture_priority_status"] == (
        "DEFAULT_OFF_FINAL_REVIEW_SOURCE_CAPTURE_PRIORITY_IMPLEMENT_READY_WITH_REDESIGN_SUBSET"
    )
    assert priority["final_review_source_capture_class"] == (
        "FINAL_REVIEW_IMPLEMENT_READY_WITH_CAPACITY_REDESIGN_SUBSET_CAPTURE"
    )
    assert priority["implementation_ready_candidate_rows"] == 1
    assert priority["capacity_blocked_candidate_rows"] == 1
    assert priority["implementation_ready_candidate_row_ids"] == ["MAIN-CAND-1"]
    assert priority["capacity_blocked_candidate_row_ids"] == ["MAIN-CAND-2"]
    assert emitter_contract["emitter_contract_status"] == (
        "READY_DEFAULT_OFF_FINAL_REVIEW_EVENT_EMITTER_CONTRACT_WITH_REDESIGN_SUBSET"
    )
    assert summary["implementation_ready_candidate_rows"] == 1
    assert summary["capacity_blocked_candidate_rows"] == 1
    assert summary["final_review_adjusted_rollup_status_counts"]["DEFAULT_OFF_FINAL_REVIEW_IMPLEMENT_READY"] == 1


def test_final_review_redesign_only_priority_blocks_event_emitter_contract():
    candidate = compact_reduced_surface_execution_row(
        _execution_row(),
        _surface_row(),
        candidate_row_id="MAIN-CAND-BLOCKED",
        execution_source_artifact="execution.jsonl",
        execution_source_line_no=1,
        execution_source_sha256="exec-sha",
        surface_source_artifact="surface.jsonl",
        surface_source_line_no=1,
        surface_source_sha256="surface-sha",
    )
    event = reduced_surface_event_from_source_row(
        event_from_candidate_scope(candidate),
        event_row_id="EVENT-BLOCKED",
        required_event_fields=required_event_fields_for_candidate(candidate),
    )
    rollup = reduced_surface_candidate_event_rollups([candidate], [event])[0]
    rollup["final_review_overlay_bound"] = True
    rollup["final_review_adjusted_rollup_status"] = "DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_REDESIGN"
    rollup["main_compiler_final_review_action"] = "REDESIGN_DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_CANDIDATE"
    contract = source_capture_contract_for_candidate(
        candidate,
        contract_row_id="CONTRACT-BLOCKED",
        source_artifact="candidate.jsonl",
        source_line_no=1,
        source_sha256="candidate-sha",
    )

    priority = reduced_surface_source_capture_priority_groups([rollup], [contract])[0]
    emitter_contract = reduced_surface_event_emitter_contract_for_priority_group(
        priority,
        contract_row_id="EMITTER-BLOCKED",
        source_artifact="priority.jsonl",
        source_line_no=1,
        source_sha256="priority-sha",
    )
    emitted = emit_reduced_surface_event_for_priority_group(
        event_from_candidate_scope(candidate),
        priority,
        event_row_id="EMITTED-BLOCKED",
    )

    assert priority["source_capture_priority_status"] == "DEFAULT_OFF_FINAL_REVIEW_SOURCE_CAPTURE_PRIORITY_REDESIGN_ONLY"
    assert priority["implementation_ready_candidate_rows"] == 0
    assert priority["capacity_blocked_candidate_rows"] == 1
    assert emitter_contract["emitter_contract_status"] == (
        "BLOCKED_DEFAULT_OFF_FINAL_REVIEW_REDESIGN_EVENT_EMITTER_CONTRACT"
    )
    assert emitted["emitter_contract_status"] == "REDUCED_SURFACE_EVENT_EMITTER_CONTRACT_BLOCKED_FINAL_REVIEW_REDESIGN"


def test_final_review_adjusted_registry_scores_split_ready_and_capacity_blocked_matches():
    first = compact_reduced_surface_execution_row(
        _execution_row(),
        _surface_row(),
        candidate_row_id="MAIN-CAND-1",
        execution_source_artifact="execution.jsonl",
        execution_source_line_no=1,
        execution_source_sha256="exec-sha",
        surface_source_artifact="surface.jsonl",
        surface_source_line_no=1,
        surface_source_sha256="surface-sha",
    )
    second = {**first, "candidate_row_id": "MAIN-CAND-2"}
    event = reduced_surface_event_from_source_row(
        event_from_candidate_scope(first),
        event_row_id="EVENT-1",
        required_event_fields=required_event_fields_for_candidate(first),
    )
    event["expected_candidate_row_id"] = "MAIN-CAND-1"
    overlays = [
        {
            "candidate_row_id": "MAIN-CAND-1",
            "final_review_adjusted_rollup_status": "DEFAULT_OFF_FINAL_REVIEW_IMPLEMENT_READY",
            "main_compiler_final_review_action": "KEEP_DEFAULT_OFF_FINAL_REVIEW_IMPLEMENT_CANDIDATE",
        },
        {
            "candidate_row_id": "MAIN-CAND-2",
            "final_review_adjusted_rollup_status": "DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_REDESIGN",
            "main_compiler_final_review_action": "REDESIGN_DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_CANDIDATE",
        },
    ]

    scores = final_review_adjusted_event_registry_scores([event], [first, second], overlays)
    summary = summarize_final_review_adjusted_event_registry_scores(scores)

    assert scores[0]["final_review_registry_score_status"] == (
        "DEFAULT_OFF_FINAL_REVIEW_REGISTRY_SCORE_IMPLEMENT_READY_WITH_REDESIGN_MATCHES"
    )
    assert scores[0]["registry_match_rows"] == 2
    assert scores[0]["implementation_ready_registry_match_rows"] == 1
    assert scores[0]["capacity_blocked_registry_match_rows"] == 1
    assert scores[0]["expected_candidate_found_in_registry"] is True
    assert scores[0]["expected_candidate_implementation_ready"] is True
    assert scores[0]["candidate_use_allowed_now"] is False
    assert summary["registry_match_rows"] == 2
    assert summary["implementation_ready_registry_match_rows"] == 1
    assert summary["capacity_blocked_registry_match_rows"] == 1


def test_final_review_adjusted_registry_scores_mark_redesign_only_events_blocked():
    candidate = compact_reduced_surface_execution_row(
        _execution_row(),
        _surface_row(),
        candidate_row_id="MAIN-CAND-BLOCKED",
        execution_source_artifact="execution.jsonl",
        execution_source_line_no=1,
        execution_source_sha256="exec-sha",
        surface_source_artifact="surface.jsonl",
        surface_source_line_no=1,
        surface_source_sha256="surface-sha",
    )
    event = reduced_surface_event_from_source_row(
        event_from_candidate_scope(candidate),
        event_row_id="EVENT-BLOCKED",
        required_event_fields=required_event_fields_for_candidate(candidate),
    )
    event["expected_candidate_row_id"] = "MAIN-CAND-BLOCKED"
    overlays = [
        {
            "candidate_row_id": "MAIN-CAND-BLOCKED",
            "final_review_adjusted_rollup_status": "DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_REDESIGN",
            "main_compiler_final_review_action": "REDESIGN_DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_CANDIDATE",
        }
    ]

    scores = final_review_adjusted_event_registry_scores([event], [candidate], overlays)

    assert scores[0]["final_review_registry_score_status"] == (
        "DEFAULT_OFF_FINAL_REVIEW_REGISTRY_SCORE_REDESIGN_BLOCKED_MATCHES_ONLY"
    )
    assert scores[0]["implementation_ready_registry_match_rows"] == 0
    assert scores[0]["capacity_blocked_registry_match_rows"] == 1
    assert scores[0]["expected_candidate_capacity_blocked"] is True
    assert scores[0]["runtime_candidate_use_permitted"] is False


def test_final_review_adjusted_selector_recommendations_add_blocklist_for_mixed_scope():
    scores = [
        {
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "H4",
            "route_session": "london_core",
            "horizon_id": "h16",
            "source_component": "market_gap_code",
            "selected_side": "LONG",
            "registry_match_rows": 2,
            "implementation_ready_registry_match_rows": 1,
            "capacity_blocked_registry_match_rows": 1,
            "binding_repair_registry_match_rows": 0,
            "expected_candidate_found_in_registry": True,
            "expected_candidate_implementation_ready": True,
            "expected_candidate_capacity_blocked": False,
            "implementation_ready_candidate_row_ids": ["MAIN-CAND-1"],
            "capacity_blocked_candidate_row_ids": ["MAIN-CAND-2"],
            "binding_repair_candidate_row_ids": [],
            "final_review_registry_score_status": (
                "DEFAULT_OFF_FINAL_REVIEW_REGISTRY_SCORE_IMPLEMENT_READY_WITH_REDESIGN_MATCHES"
            ),
        }
    ]

    recommendations = final_review_adjusted_selector_recommendations(scores)
    summary = summarize_final_review_adjusted_selector_recommendations(recommendations)

    assert recommendations[0]["selector_recommendation_status"] == (
        "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_IMPLEMENT_READY_WITH_REDESIGN_BLOCKLIST"
    )
    assert recommendations[0]["capacity_blocked_selector_blocklist_required"] is True
    assert recommendations[0]["implementation_ready_candidate_row_ids"] == ["MAIN-CAND-1"]
    assert recommendations[0]["capacity_blocked_candidate_row_ids"] == ["MAIN-CAND-2"]
    assert recommendations[0]["candidate_use_allowed_now"] is False
    assert summary["rows"] == 1
    assert summary["event_rows"] == 1
    assert summary["capacity_blocked_selector_blocklist_required_rows"] == 1


def test_final_review_adjusted_selector_recommendations_block_redesign_only_scope():
    scores = [
        {
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "H4",
            "route_session": "london_core",
            "horizon_id": "h16",
            "source_component": "market_gap_code",
            "selected_side": "LONG",
            "registry_match_rows": 1,
            "implementation_ready_registry_match_rows": 0,
            "capacity_blocked_registry_match_rows": 1,
            "binding_repair_registry_match_rows": 0,
            "expected_candidate_found_in_registry": True,
            "expected_candidate_implementation_ready": False,
            "expected_candidate_capacity_blocked": True,
            "implementation_ready_candidate_row_ids": [],
            "capacity_blocked_candidate_row_ids": ["MAIN-CAND-BLOCKED"],
            "binding_repair_candidate_row_ids": [],
            "final_review_registry_score_status": "DEFAULT_OFF_FINAL_REVIEW_REGISTRY_SCORE_REDESIGN_BLOCKED_MATCHES_ONLY",
        }
    ]

    recommendation = final_review_adjusted_selector_recommendations(scores)[0]

    assert recommendation["selector_recommendation_status"] == "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_BLOCK_REDESIGN_ONLY_SCOPE"
    assert recommendation["implementation_ready_candidate_rows"] == 0
    assert recommendation["capacity_blocked_candidate_rows"] == 1
    assert recommendation["runtime_candidate_use_permitted"] is False


def test_final_review_selector_production_change_dossier_marks_mixed_scope_default_off():
    recommendation = {
        "selector_recommendation_rank": 7,
        "selector_recommendation_status": "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_IMPLEMENT_READY_WITH_REDESIGN_BLOCKLIST",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "H4",
        "route_session": "london_core",
        "horizon_id": "h16",
        "source_component": "market_gap_code",
        "selected_side": "LONG",
        "event_rows": 3,
        "registry_match_rows": 5,
        "implementation_ready_registry_match_rows": 3,
        "capacity_blocked_registry_match_rows": 2,
        "expected_candidate_found_in_registry_rows": 3,
        "expected_candidate_implementation_ready_rows": 2,
        "expected_candidate_capacity_blocked_rows": 1,
        "implementation_ready_candidate_rows": 1,
        "capacity_blocked_candidate_rows": 1,
        "capacity_blocked_selector_blocklist_required": True,
        "implementation_ready_candidate_row_ids": ["MAIN-CAND-1"],
        "capacity_blocked_candidate_row_ids": ["MAIN-CAND-2"],
        "final_review_registry_score_status_counts": {
            "DEFAULT_OFF_FINAL_REVIEW_REGISTRY_SCORE_IMPLEMENT_READY_WITH_REDESIGN_MATCHES": 3
        },
    }

    row = final_review_selector_production_change_dossier_row(
        recommendation,
        dossier_row_id="DOSSIER-1",
        source_artifact="selector.jsonl",
        source_line_no=10,
        source_sha256="selector-sha",
    )
    summary = summarize_final_review_selector_production_change_dossier([row])

    assert row["production_change_dossier_status"] == (
        "PROD_CHANGE_DOSSIER_DEFAULT_OFF_SELECTOR_IMPLEMENT_READY_WITH_REDESIGN_BLOCKLIST"
    )
    assert row["mechanical_selector_scope_draft_ready_for_separate_review"] is True
    assert row["separate_production_change_review_required"] is True
    assert row["production_change_opened_now"] is False
    assert row["runtime_candidate_use_permitted"] is False
    assert "MECHANICAL_SELECTOR_WITH_CAPACITY_BLOCKLIST" in row["ai_architecture_recommendation"]
    assert summary["mechanical_selector_scope_draft_ready_for_separate_review_rows"] == 1
    assert summary["capacity_blocked_selector_blocklist_required_rows"] == 1
    assert summary["production_change_opened_now_rows"] == 0


def test_final_review_selector_production_change_dossier_blocks_redesign_only_scope():
    row = final_review_selector_production_change_dossier_row(
        {
            "selector_recommendation_status": "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_BLOCK_REDESIGN_ONLY_SCOPE",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "H4",
            "route_session": "london_core",
            "horizon_id": "h16",
            "source_component": "market_gap_code",
            "selected_side": "LONG",
            "capacity_blocked_candidate_rows": 2,
            "capacity_blocked_selector_blocklist_required": True,
        },
        dossier_row_id="DOSSIER-1",
        source_artifact="selector.jsonl",
        source_line_no=10,
        source_sha256="selector-sha",
    )

    assert row["production_change_dossier_status"] == "PROD_CHANGE_DOSSIER_DEFAULT_OFF_SELECTOR_REDESIGN_ONLY_BLOCKED"
    assert row["mechanical_selector_scope_draft_ready_for_separate_review"] is False
    assert row["live_selector_change_now"] is False
    assert row["ai_architecture_recommendation"] == (
        "KEEP_AI_UNCHANGED_FOR_SCOPE_AND_ROUTE_MECHANICAL_SCOPE_TO_REDESIGN"
    )


def test_ai_narrowing_capacity_blocklist_extracts_mixed_scope_candidate_ids():
    dossier = final_review_selector_production_change_dossier_row(
        {
            "selector_recommendation_status": "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_IMPLEMENT_READY_WITH_REDESIGN_BLOCKLIST",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "H1",
            "route_session": "off_core_session",
            "horizon_id": "h16",
            "source_component": "shadow_source_guard",
            "selected_side": "LONG",
            "capacity_blocked_candidate_row_ids": ["CAND-BLOCKED-1", "CAND-BLOCKED-2"],
            "implementation_ready_candidate_row_ids": ["CAND-READY-1"],
            "capacity_blocked_candidate_rows": 2,
            "implementation_ready_candidate_rows": 1,
            "capacity_blocked_selector_blocklist_required": True,
        },
        dossier_row_id="DOSSIER-BLOCKLIST",
        source_artifact="selector.jsonl",
        source_line_no=10,
        source_sha256="selector-sha",
    )

    row = final_review_ai_narrowing_capacity_blocklist_row(
        dossier,
        blocklist_row_id="BLOCKLIST-1",
        source_artifact="dossier.jsonl",
        source_line_no=1,
        source_sha256="dossier-sha",
    )
    summary = summarize_ai_narrowing_capacity_blocklist([row])

    assert row["ai_narrowing_capacity_blocklist_status"] == (
        "AI_NARROWING_CAPACITY_BLOCKLIST_REQUIRED_FOR_PRE_AI_SELECTOR_REVIEW"
    )
    assert row["pre_ai_selector_blocklist_required_before_runtime_enablement"] is True
    assert row["capacity_blocked_candidate_rows"] == 2
    assert row["capacity_blocklist_active_now"] is False
    assert row["ai_call_skip_allowed_now"] is False
    assert row["runtime_candidate_use_permitted"] is False
    assert summary["pre_ai_selector_blocklist_scope_rows"] == 1
    assert summary["unique_pre_ai_selector_blocked_candidate_ids"] == 2


def test_ai_narrowing_capacity_blocklist_preserves_redesign_only_scope_without_ai_narrowing():
    dossier = final_review_selector_production_change_dossier_row(
        {
            "selector_recommendation_status": "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_BLOCK_REDESIGN_ONLY_SCOPE",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "H4",
            "route_session": "london_core",
            "horizon_id": "h16",
            "source_component": "market_gap_code",
            "selected_side": "LONG",
            "capacity_blocked_candidate_row_ids": ["CAND-REDESIGN"],
            "capacity_blocked_candidate_rows": 1,
        },
        dossier_row_id="DOSSIER-REDESIGN",
        source_artifact="selector.jsonl",
        source_line_no=10,
        source_sha256="selector-sha",
    )
    row = final_review_ai_narrowing_capacity_blocklist_row(
        dossier,
        blocklist_row_id="BLOCKLIST-REDESIGN",
        source_artifact="dossier.jsonl",
        source_line_no=1,
        source_sha256="dossier-sha",
    )

    assert row["ai_narrowing_capacity_blocklist_status"] == (
        "AI_NARROWING_CAPACITY_BLOCKLIST_PRESERVED_REDESIGN_ONLY_KEEP_AI_UNCHANGED"
    )
    assert row["pre_ai_selector_blocklist_required_before_runtime_enablement"] is False
    assert row["keep_ai_unchanged_redesign_only_scope"] is True
    assert row["current_ai_runtime_behavior"] == "UNCHANGED_DEFAULT_AI_DECISION_GATE"


def test_ai_narrowing_capacity_blocklist_registry_blocks_only_listed_candidate_ids():
    blocklist = AINarrowingCapacityBlocklist(
        [
            {
                "ai_narrowing_capacity_blocklist_row_id": "BLOCKLIST-1",
                "ai_narrowing_capacity_blocklist_status": (
                    "AI_NARROWING_CAPACITY_BLOCKLIST_REQUIRED_FOR_PRE_AI_SELECTOR_REVIEW"
                ),
                "pre_ai_selector_blocklist_required_before_runtime_enablement": True,
                "capacity_blocked_candidate_row_ids": ["CAND-BLOCKED"],
                "runtime_candidate_use_permitted": False,
                "capacity_blocklist_active_now": False,
            }
        ]
    )

    blocked = blocklist.evaluate_candidate("CAND-BLOCKED", evaluation_row_id="EVAL-BLOCKED")
    clear = blocklist.evaluate_candidate("CAND-CLEAR", evaluation_row_id="EVAL-CLEAR")

    assert blocked["ai_narrowing_capacity_blocklist_eval_status"] == (
        "AI_NARROWING_CAPACITY_BLOCKLIST_MATCH_BLOCK_PRE_AI_SELECTOR"
    )
    assert blocked["pre_ai_selector_candidate_blocked"] is True
    assert blocked["ai_call_skip_allowed_now"] is False
    assert clear["ai_narrowing_capacity_blocklist_eval_status"] == "AI_NARROWING_CAPACITY_BLOCKLIST_NO_MATCH"
    assert clear["pre_ai_selector_candidate_blocked"] is False
    assert blocklist.summarize()["unique_candidate_ids"] == 1


def test_ai_narrowing_policy_marks_implement_ready_scope_as_default_off_pre_ai_review():
    dossier = final_review_selector_production_change_dossier_row(
        {
            "selector_recommendation_status": "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_IMPLEMENT_READY_SCOPE",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "H4",
            "route_session": "london_core",
            "horizon_id": "h16",
            "source_component": "market_gap_code",
            "selected_side": "LONG",
            "event_rows": 4,
            "registry_match_rows": 6,
            "implementation_ready_candidate_rows": 2,
            "capacity_blocked_candidate_rows": 0,
        },
        dossier_row_id="DOSSIER-1",
        source_artifact="selector.jsonl",
        source_line_no=10,
        source_sha256="selector-sha",
    )

    row = final_review_selector_ai_narrowing_policy_row(
        dossier,
        policy_row_id="POLICY-1",
        source_artifact="dossier.jsonl",
        source_line_no=1,
        source_sha256="dossier-sha",
    )
    summary = summarize_final_review_selector_ai_narrowing_policy([row])

    assert row["ai_narrowing_policy_status"] == "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY"
    assert row["ai_role_after_owner_approval"] == "MECHANICAL_SELECTOR_CAN_PRECEDE_AI_FOR_SCOPE_AFTER_REVIEW"
    assert row["ai_narrowing_review_ready"] is True
    assert row["capacity_blocklist_required_before_ai_narrowing"] is False
    assert row["current_ai_runtime_behavior"] == "UNCHANGED_DEFAULT_AI_DECISION_GATE"
    assert row["live_ai_runtime_change_now"] is False
    assert row["paid_api_or_vendor_call"] is False
    assert summary["ai_narrowing_review_ready_rows"] == 1
    assert summary["live_ai_runtime_change_now_rows"] == 0


def test_ai_narrowing_policy_keeps_ai_unchanged_for_redesign_only_scope():
    dossier = final_review_selector_production_change_dossier_row(
        {
            "selector_recommendation_status": "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_BLOCK_REDESIGN_ONLY_SCOPE",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "H4",
            "route_session": "london_core",
            "horizon_id": "h16",
            "source_component": "market_gap_code",
            "selected_side": "LONG",
            "capacity_blocked_candidate_rows": 2,
        },
        dossier_row_id="DOSSIER-1",
        source_artifact="selector.jsonl",
        source_line_no=10,
        source_sha256="selector-sha",
    )

    row = final_review_selector_ai_narrowing_policy_row(
        dossier,
        policy_row_id="POLICY-1",
        source_artifact="dossier.jsonl",
        source_line_no=1,
        source_sha256="dossier-sha",
    )

    assert row["ai_narrowing_policy_status"] == (
        "AI_NARROWING_POLICY_KEEP_AI_UNCHANGED_MECHANICAL_SCOPE_REDESIGN_ONLY"
    )
    assert row["ai_role_after_owner_approval"] == "KEEP_PRIMARY_ANALYZER_FULL_SCOPE_FOR_THIS_SELECTOR_SCOPE"
    assert row["ai_narrowing_review_ready"] is False
    assert row["runtime_candidate_use_permitted"] is False


def test_ai_narrowing_event_adapter_aliases_base_scope_without_enabling_ai_skip():
    dossier = final_review_selector_production_change_dossier_row(
        {
            "selector_recommendation_status": "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_IMPLEMENT_READY_SCOPE",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "H4",
            "route_session": "london_core",
            "horizon_id": "h16",
            "source_component": "market_gap_code",
            "selected_side": "LONG",
        },
        dossier_row_id="DOSSIER-1",
        source_artifact="selector.jsonl",
        source_line_no=10,
        source_sha256="selector-sha",
    )
    policy = final_review_selector_ai_narrowing_policy_row(
        dossier,
        policy_row_id="POLICY-1",
        source_artifact="dossier.jsonl",
        source_line_no=1,
        source_sha256="dossier-sha",
    )
    event = ai_narrowing_event_from_source_row(
        {
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "timeframe": "H4",
            "session": "london_core",
            "side": "LONG",
            "horizon_id": "h16",
            "component": "market_gap_code",
        },
        event_row_id="EVENT-1",
        source_kind="unit_current_shadow_log_row",
    )
    evaluation = AINarrowingPolicyRegistry([policy]).evaluate_event(event, evaluation_row_id="EVAL-1")
    summary = summarize_ai_narrowing_policy_events([event])

    assert event["event_adapter_status"] == "AI_NARROWING_EVENT_CONTRACT_COMPLETE"
    assert event["missing_required_fields"] == []
    assert event["market_timeframe"] == "H4"
    assert event["route_session"] == "london_core"
    assert event["selected_side"] == "LONG"
    assert event["source_component"] == "market_gap_code"
    assert evaluation["matched_policy_rows"] == 1
    assert event["ai_call_skip_allowed_now"] is False
    assert summary["contract_complete_rows"] == 1
    assert summary["ai_call_skip_allowed_now_rows"] == 0


def test_ai_narrowing_event_adapter_marks_current_partial_rows_incomplete():
    event = ai_narrowing_event_from_source_row(
        {
            "symbol": "XAUUSD",
            "session": "london",
            "side": "LONG",
        },
        event_row_id="EVENT-2",
        source_kind="current_shadow_log_row",
    )
    summary = summarize_ai_narrowing_policy_events([event])

    assert event["route_session"] == "london"
    assert event["selected_side"] == "LONG"
    assert event["event_adapter_status"] == "AI_NARROWING_EVENT_CONTRACT_INCOMPLETE"
    assert "horizon_id" in event["missing_required_fields"]
    assert "market_timeframe" in event["missing_required_fields"]
    assert "source_component" in event["missing_required_fields"]
    assert "source_symbol" in event["missing_required_fields"]
    assert summary["event_adapter_status_counts"] == {"AI_NARROWING_EVENT_CONTRACT_INCOMPLETE": 1}
    assert summary["missing_required_field_counts"]["horizon_id"] == 1


def test_ai_narrowing_policy_registry_matches_ready_scope_without_runtime_enablement():
    dossier = final_review_selector_production_change_dossier_row(
        {
            "selector_recommendation_status": "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_IMPLEMENT_READY_SCOPE",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "H4",
            "route_session": "london_core",
            "horizon_id": "h16",
            "source_component": "market_gap_code",
            "selected_side": "LONG",
        },
        dossier_row_id="DOSSIER-1",
        source_artifact="selector.jsonl",
        source_line_no=10,
        source_sha256="selector-sha",
    )
    policy = final_review_selector_ai_narrowing_policy_row(
        dossier,
        policy_row_id="POLICY-1",
        source_artifact="dossier.jsonl",
        source_line_no=1,
        source_sha256="dossier-sha",
    )

    registry = AINarrowingPolicyRegistry([policy])
    event = ai_narrowing_policy_scope_event(policy, event_row_id="EVENT-1")
    evaluation = registry.evaluate_event(event, evaluation_row_id="EVAL-1")
    summary = summarize_ai_narrowing_policy_registry_evaluations([evaluation])

    assert evaluation["matched_policy_rows"] == 1
    assert evaluation["ai_narrowing_registry_eval_status"] == "AI_NARROWING_REGISTRY_MATCH_PRE_AI_SELECTOR_REVIEW_READY"
    assert evaluation["ai_narrowing_review_ready"] is True
    assert evaluation["ai_call_skip_allowed_now"] is False
    assert evaluation["live_ai_runtime_change_now"] is False
    assert summary["matched_policy_rows"] == 1
    assert summary["ai_narrowing_review_ready_rows"] == 1
    assert summary["ai_call_skip_allowed_now_rows"] == 0


def test_ai_narrowing_policy_registry_no_match_keeps_ai_gate():
    registry = AINarrowingPolicyRegistry([])
    evaluation = registry.evaluate_event(
        {
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "H4",
            "route_session": "london_core",
            "horizon_id": "h16",
            "source_component": "market_gap_code",
            "selected_side": "LONG",
        },
        evaluation_row_id="EVAL-1",
    )

    assert evaluation["matched_policy_rows"] == 0
    assert evaluation["ai_narrowing_registry_eval_status"] == "AI_NARROWING_REGISTRY_NO_POLICY_MATCH_KEEP_AI"
    assert evaluation["current_ai_runtime_behavior"] == "UNCHANGED_DEFAULT_AI_DECISION_GATE"
    assert evaluation["ai_narrowing_review_ready"] is False


def test_ai_narrowing_runtime_config_guard_default_off_keeps_ai_on_for_ready_policy():
    dossier = final_review_selector_production_change_dossier_row(
        {
            "selector_recommendation_status": "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_IMPLEMENT_READY_SCOPE",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "H4",
            "route_session": "london_core",
            "horizon_id": "h16",
            "source_component": "market_gap_code",
            "selected_side": "LONG",
        },
        dossier_row_id="DOSSIER-1",
        source_artifact="selector.jsonl",
        source_line_no=10,
        source_sha256="selector-sha",
    )
    policy = final_review_selector_ai_narrowing_policy_row(
        dossier,
        policy_row_id="POLICY-1",
        source_artifact="dossier.jsonl",
        source_line_no=1,
        source_sha256="dossier-sha",
    )
    evaluation = AINarrowingPolicyRegistry([policy]).evaluate_event(
        ai_narrowing_policy_scope_event(policy, event_row_id="EVENT-1"),
        evaluation_row_id="EVAL-1",
    )

    decision = ai_narrowing_runtime_config_guard_decision(
        evaluation,
        config={"ai_narrowing": {"enabled": False, "mode": "shadow"}},
        runtime_halt_active=True,
        decision_row_id="DECISION-1",
    )
    summary = summarize_ai_narrowing_runtime_config_guard_decisions([decision])

    assert decision["ai_narrowing_review_ready"] is True
    assert decision["ai_narrowing_runtime_guard_decision_status"] == "AI_NARROWING_RUNTIME_KEEP_AI_CONFIG_DISABLED"
    assert "CONFIG_DISABLED" in decision["runtime_enablement_gate_failures"]
    assert "RUNTIME_HALT_ACTIVE" in decision["runtime_enablement_gate_failures"]
    assert decision["runtime_eligible_after_all_gates"] is False
    assert decision["ai_call_skip_allowed_now"] is False
    assert decision["current_ai_runtime_behavior"] == "UNCHANGED_DEFAULT_AI_DECISION_GATE"
    assert summary["ai_call_skip_allowed_now_rows"] == 0
    assert summary["runtime_guard_config_enabled_rows"] == 0


def test_ai_narrowing_runtime_config_guard_records_eligibility_without_runtime_permission():
    evaluation = {
        "ai_narrowing_registry_eval_row_id": "EVAL-READY",
        "selector_scope_key": "scope-key",
        "symbol": "XAUUSD",
        "source_symbol": "XAUUSD",
        "market_timeframe": "H4",
        "route_session": "london_core",
        "horizon_id": "h16",
        "source_component": "market_gap_code",
        "selected_side": "LONG",
        "matched_policy_rows": 1,
        "matched_policy_row_ids": ["POLICY-1"],
        "ai_narrowing_registry_eval_status": "AI_NARROWING_REGISTRY_MATCH_PRE_AI_SELECTOR_REVIEW_READY",
        "ai_narrowing_review_ready": True,
        "capacity_blocklist_required_before_ai_narrowing": False,
    }

    decision = ai_narrowing_runtime_config_guard_decision(
        evaluation,
        config={
            "ai_narrowing": {
                "enabled": True,
                "mode": "active",
                "allow_ai_call_skip": True,
                "owner_approval_confirmed": True,
                "production_change_review_approved": True,
                "runtime_halt_removed": True,
                "capacity_blocklist_active": False,
            }
        },
        runtime_halt_active=False,
    )

    assert decision["runtime_enablement_gate_failures"] == []
    assert decision["runtime_eligible_after_all_gates"] is True
    assert decision["ai_narrowing_runtime_guard_decision_status"] == (
        "AI_NARROWING_RUNTIME_ELIGIBLE_AFTER_ALL_GATES_BUT_NOT_WIRED"
    )
    assert decision["ai_call_skip_allowed_now"] is False
    assert decision["runtime_candidate_use_permitted"] is False
    assert decision["candidate_use_allowed_now"] is False


def test_ai_narrowing_runtime_config_guard_requires_capacity_blocklist_for_mixed_scope():
    decision = ai_narrowing_runtime_config_guard_decision(
        {
            "ai_narrowing_registry_eval_row_id": "EVAL-BLOCKLIST",
            "selector_scope_key": "scope-key",
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "market_timeframe": "H4",
            "route_session": "london_core",
            "horizon_id": "h16",
            "source_component": "market_gap_code",
            "selected_side": "LONG",
            "matched_policy_rows": 1,
            "matched_policy_row_ids": ["POLICY-1"],
            "ai_narrowing_registry_eval_status": (
                "AI_NARROWING_REGISTRY_MATCH_PRE_AI_SELECTOR_REVIEW_WITH_CAPACITY_BLOCKLIST"
            ),
            "ai_narrowing_review_ready": True,
            "capacity_blocklist_required_before_ai_narrowing": True,
        },
        config={
            "ai_narrowing": {
                "enabled": True,
                "mode": "active",
                "allow_ai_call_skip": True,
                "owner_approval_confirmed": True,
                "production_change_review_approved": True,
                "runtime_halt_removed": True,
                "capacity_blocklist_active": False,
            }
        },
        runtime_halt_active=False,
    )

    assert "CAPACITY_BLOCKLIST_NOT_ACTIVE" in decision["runtime_enablement_gate_failures"]
    assert decision["ai_narrowing_runtime_guard_decision_status"] == (
        "AI_NARROWING_RUNTIME_KEEP_AI_CAPACITY_BLOCKLIST_REQUIRED"
    )
    assert decision["runtime_eligible_after_all_gates"] is False
    assert decision["ai_call_skip_allowed_now"] is False


def test_event_emitter_contract_and_helper_emit_complete_source_row():
    candidate = compact_reduced_surface_execution_row(
        _execution_row(),
        _surface_row(),
        candidate_row_id="MAIN-CAND-1",
        execution_source_artifact="execution.jsonl",
        execution_source_line_no=1,
        execution_source_sha256="exec-sha",
        surface_source_artifact="surface.jsonl",
        surface_source_line_no=1,
        surface_source_sha256="surface-sha",
    )
    event = reduced_surface_event_from_source_row(
        event_from_candidate_scope(candidate),
        event_row_id="EVENT-1",
        required_event_fields=required_event_fields_for_candidate(candidate),
    )
    event["expected_candidate_row_id"] = "MAIN-CAND-1"
    event["expected_candidate_found"] = True
    rollup = reduced_surface_candidate_event_rollups([candidate], [event])[0]
    contract = source_capture_contract_for_candidate(
        candidate,
        contract_row_id="CONTRACT-1",
        source_artifact="candidate.jsonl",
        source_line_no=1,
        source_sha256="candidate-sha",
    )
    priority = reduced_surface_source_capture_priority_groups([rollup], [contract])[0]

    emitter_contract = reduced_surface_event_emitter_contract_for_priority_group(
        priority,
        contract_row_id="EMITTER-1",
        source_artifact="priority.jsonl",
        source_line_no=1,
        source_sha256="priority-sha",
    )
    emitted = emit_reduced_surface_event_for_priority_group(
        event_from_candidate_scope(candidate),
        priority,
        event_row_id="EMITTED-1",
        source_artifact="future.jsonl",
        source_line_no=3,
        source_sha256="future-sha",
    )

    assert emitter_contract["emitter_contract_status"] == "READY_DEFAULT_OFF_REDUCED_SURFACE_EVENT_EMITTER_CONTRACT"
    assert emitter_contract["event_emitter_surface"] == "emit_reduced_surface_event_for_priority_group"
    assert emitter_contract["source_hash_alias_policy"] == "DO_NOT_TREAT_GENERIC_SOURCE_HASH_AS_SOURCE_FILE_SHA256"
    assert emitted["event_adapter_status"] == "REDUCED_SURFACE_EVENT_CONTRACT_COMPLETE"
    assert emitted["emitter_contract_status"] == "REDUCED_SURFACE_EVENT_EMITTER_CONTRACT_COMPLETE"
    assert emitted["source_capture_priority_rank"] == 1
    summary = summarize_reduced_surface_event_emitter_contracts([emitter_contract])
    assert summary["rows"] == 1
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def test_event_emitter_helper_keeps_source_hash_only_row_incomplete():
    priority = {
        "source_capture_priority_rank": 1,
        "source_capture_priority_class": "LEAKAGE_REDUCED_SOURCE_IDENTITY_AND_NUMERIC_CAPTURE",
        "source_capture_priority_status": "DEFAULT_OFF_REDUCED_SURFACE_SOURCE_CAPTURE_PRIORITY_READY",
        "required_event_fields": [
            "horizon_id",
            "market_timeframe",
            "route_session",
            "selected_side",
            "source_component",
            "source_file_sha256",
            "source_path",
            "source_symbol",
            "symbol",
            "selected_intrabar_cost_adjusted_simulated_r",
        ],
    }
    emitted = emit_reduced_surface_event_for_priority_group(
        {
            "symbol": "XAUUSD",
            "source_symbol": "XAUUSD",
            "horizon_id": "h16",
            "timeframe": "H4",
            "session": "london_core",
            "side": "LONG",
            "source_component": "shadow_source_guard",
            "source_hash": "not-a-file-hash",
            "selected_intrabar_cost_adjusted_simulated_r": 0.2,
        },
        priority,
    )

    assert emitted["emitter_contract_status"] == "REDUCED_SURFACE_EVENT_EMITTER_CONTRACT_INCOMPLETE"
    assert "source_file_sha256" in emitted["missing_required_fields"]
    assert "source_path" in emitted["missing_required_fields"]
