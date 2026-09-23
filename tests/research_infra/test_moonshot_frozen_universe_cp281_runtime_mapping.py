from __future__ import annotations

from src.research_infra.moonshot_frozen_universe_cp281_runtime_mapping import (
    CP281BranchDecisionRegistry,
    CP281ReadyRuntimeRegistry,
    DEFAULT_RULE_REPLAY_RESULT_TABLE_LEDGER,
    branch_decision_event_from_row,
    build_aggregate_mapping_rows,
    build_branch_decision_rows,
    build_branch_scope_replay_event_rows,
    build_branch_scope_replay_match_rows,
    build_branch_scope_contract_rows,
    build_branch_scope_registry_self_check_rows,
    build_registry_self_check_rows,
    build_rule_replay_event_rows,
    build_rule_replay_match_rows,
    build_rule_replay_result_table_rows,
    build_rule_mapping_rows,
    build_source_capture_contract_rows,
    cp281_audit_event_source_rows,
    cp281_branch_scope_events_from_source_row,
    cp281_contract_required_fields,
    event_from_rule_mapping,
    summarize_branch_scope_source_rows,
    summarize_branch_decisions,
    summarize_branch_scope_replay_materialization,
    summarize_branch_scope_registry,
    summarize_mapping,
    summarize_rule_replay_execution_materialization,
)


def _rule_rows():
    return [
        {
            "action_class": "follow_rule",
            "branch_local_runtime_role": "branch-local follow scorer/rule",
            "cost_adjusted_simulated_r": 0.25,
            "effective_n": 12,
            "frozen_ready_action_runtime_rule_row_id": "RULE-1",
            "gross_simulated_r": 0.3,
            "horizon_id": "h16",
            "input_implementation_ready_bundle_row_id": "READY-1",
            "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_FOLLOW_READY_ACTION",
            "market_timeframe": "M5",
            "match_fields": [
                "symbol_family",
                "symbol",
                "source_symbol",
                "market_timeframe",
                "route_session",
                "horizon_id",
                "side",
                "source_path_sha256",
                "source_file_sha256",
            ],
            "match_scope": {
                "symbol_family": "USDJPY_6J_FAMILY",
                "symbol": "USDJPY_6J",
                "source_symbol": "USDJPY",
                "market_timeframe": "M5",
                "route_session": "tokyo_kz",
                "horizon_id": "h16",
                "side": "LONG",
                "source_path_sha256": "a" * 64,
                "source_file_sha256": "b" * 64,
            },
            "missing_match_fields": [],
            "route_session": "tokyo_kz",
            "rule_expression_sha256": "c" * 64,
            "side": "LONG",
            "source_action_closure_artifact": "route/action.jsonl",
            "source_action_closure_row_count": 1,
            "source_file_sha256": "b" * 64,
            "source_path": "data/historical/USDJPY_M5.csv",
            "source_path_sha256": "a" * 64,
            "source_row_count": 1,
            "source_row_ids_sha256": "d" * 64,
            "source_symbol": "USDJPY",
            "stress_simulated_r": 0.2,
            "symbol": "USDJPY_6J",
            "symbol_family": "USDJPY_6J_FAMILY",
            "tests_needed": ["tests/research_infra/test_moonshot_unified_execution_scorer.py"],
        },
        {
            "action_class": "avoid_filter",
            "branch_local_runtime_role": "branch-local avoid filter/rule",
            "cost_adjusted_simulated_r": -0.4,
            "effective_n": 7,
            "frozen_ready_action_runtime_rule_row_id": "RULE-2",
            "gross_simulated_r": -0.35,
            "horizon_id": "h32",
            "input_implementation_ready_bundle_row_id": "READY-2",
            "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_AVOID_READY_ACTION",
            "market_timeframe": "M1",
            "match_fields": [
                "symbol_family",
                "symbol",
                "source_symbol",
                "market_timeframe",
                "route_session",
                "horizon_id",
                "side",
                "source_path_sha256",
                "source_file_sha256",
            ],
            "match_scope": {
                "symbol_family": "US30_YM_FAMILY",
                "symbol": "US30_YM",
                "source_symbol": "US30",
                "market_timeframe": "M1",
                "route_session": "ny_core",
                "horizon_id": "h32",
                "side": "SHORT",
                "source_path_sha256": "e" * 64,
                "source_file_sha256": "f" * 64,
            },
            "missing_match_fields": [],
            "route_session": "ny_core",
            "rule_expression_sha256": "g" * 64,
            "side": "SHORT",
            "source_action_closure_artifact": "route/action.jsonl",
            "source_action_closure_row_count": 1,
            "source_file_sha256": "f" * 64,
            "source_path": "data/historical/US30_M1.csv",
            "source_path_sha256": "e" * 64,
            "source_row_count": 1,
            "source_row_ids_sha256": "h" * 64,
            "source_symbol": "US30",
            "stress_simulated_r": -0.45,
            "symbol": "US30_YM",
            "symbol_family": "US30_YM_FAMILY",
            "tests_needed": ["tests/research_infra/test_moonshot_unified_execution_scorer.py"],
        },
    ]


def _self_test_rows():
    return [
        {
            "frozen_ready_action_runtime_self_test_row_id": "SELF-1",
            "input_runtime_rule_row_id": "RULE-1",
            "self_test_status": "FROZEN_READY_ACTION_RUNTIME_SELF_TEST_PASS",
            "matched": True,
            "has_cost_stress_evidence": True,
        },
        {
            "frozen_ready_action_runtime_self_test_row_id": "SELF-2",
            "input_runtime_rule_row_id": "RULE-2",
            "self_test_status": "FROZEN_READY_ACTION_RUNTIME_SELF_TEST_PASS",
            "matched": True,
            "has_cost_stress_evidence": True,
        },
    ]


def _mapping_rows():
    return build_rule_mapping_rows(
        _rule_rows(),
        _self_test_rows(),
        source_rule_artifact="route/rules.jsonl",
        source_rule_artifact_sha256="1" * 64,
        source_self_test_artifact="route/self_tests.jsonl",
        source_self_test_artifact_sha256="2" * 64,
        moonshot_head="abc",
        moonshot_status_clean=True,
    )


def test_rule_mapping_preserves_follow_and_avoid_rows_with_controls():
    rows = _mapping_rows()

    assert len(rows) == 2
    assert {row["action_class"] for row in rows} == {"follow_rule", "avoid_filter"}
    assert rows[0]["main_surface_action"] == "REGISTER_DEFAULT_OFF_CP281_FOLLOW_SCORER_RULE"
    assert rows[1]["main_surface_action"] == "REGISTER_DEFAULT_OFF_CP281_AVOID_FILTER_RULE"
    assert all(row["source_capture_contract_ready"] for row in rows)
    assert all(row["runtime_candidate_use_permitted"] is False for row in rows)
    assert all(row["candidate_use_allowed_now"] is False for row in rows)


def test_registry_evaluates_self_events_and_keeps_default_off_controls():
    rows = _mapping_rows()
    registry = CP281ReadyRuntimeRegistry(rows)
    event = event_from_rule_mapping(rows[0])
    matches = registry.evaluate_event(event)

    assert any(match["cp281_rule_row_id"] == "RULE-1" for match in matches)
    assert all(match["runtime_candidate_use_permitted"] is False for match in matches)
    assert all(match["candidate_use_allowed_now"] is False for match in matches)


def test_rule_replay_execution_materialization_builds_grouped_result_tables():
    rows = _mapping_rows()
    registry = CP281ReadyRuntimeRegistry(rows)
    event_rows = build_rule_replay_event_rows(rows)
    match_rows = build_rule_replay_match_rows(event_rows, registry=registry)
    result_table_rows = build_rule_replay_result_table_rows(match_rows)
    summary = summarize_rule_replay_execution_materialization(
        event_rows=event_rows,
        match_rows=match_rows,
        result_table_rows=result_table_rows,
    )

    assert len(event_rows) == 2
    assert len(match_rows) == 2
    assert summary["matched_event_rows"] == 2
    assert summary["unmatched_event_rows"] == 0
    assert summary["own_rule_match_rows"] == 2
    assert summary["event_action_class_counts"] == {"avoid_filter": 1, "follow_rule": 1}
    assert summary["matched_action_class_counts"] == {"avoid_filter": 1, "follow_rule": 1}
    assert summary["live_shadow_matching_role"] == "SECONDARY_EVENT_FIELD_INTEGRATION_EVIDENCE_ONLY_NOT_STRATEGY_EVIDENCE"
    assert all(row["source_evidence_role"] == "CP281_NATIVE_RULE_REPLAY_EVENT_FROM_HISTORICAL_READY_SLICE" for row in event_rows)
    assert all(row["runtime_candidate_use_permitted"] is False for row in event_rows + match_rows + result_table_rows)
    assert all(row["candidate_use_allowed_now"] is False for row in event_rows + match_rows + result_table_rows)

    groups = {row["result_table_group"]: row for row in result_table_rows if row["result_table_group"] in {"overall", "action_class"}}
    assert groups["overall"]["cost_adjusted_simulated_r"]["sum"] == -0.15
    assert groups["overall"]["gross_simulated_r"]["sum"] == -0.05
    assert groups["overall"]["follow_vs_avoid_role"] == "follow_and_avoid_mixed"
    assert any(
        row["result_table_group"] == "action_class"
        and row["result_table_dimensions"] == {"matched_action_class": "follow_rule"}
        and row["cost_adjusted_simulated_r"]["sum"] == 0.25
        for row in result_table_rows
    )


def test_rule_replay_result_table_contract_accepts_action_and_rule_aliases():
    contracts = [
        {
            "event_required_fields": [
                "matched_action_class",
                "matched_cp281_rule_row_id",
            ]
        }
    ]
    required_fields = cp281_contract_required_fields(contracts)
    audit = cp281_audit_event_source_rows(
        [
            {
                "action_class": "follow_rule",
                "cp281_rule_row_id": "RULE-1",
            },
            {
                "source_action_class": "avoid_filter",
                "source_cp281_rule_row_id": "RULE-2",
            },
        ],
        required_fields=required_fields,
    )

    assert audit["rows_with_all_required_fields"] == 2
    assert audit["missing_required_fields"] == []
    assert audit["field_availability_status"] == "CURRENT_SOURCE_CAN_FEED_CP281_READY_RUNTIME_REGISTRY"


def test_default_rule_replay_result_table_ledger_points_at_materialized_artifact():
    assert DEFAULT_RULE_REPLAY_RESULT_TABLE_LEDGER.as_posix().endswith(
        "MAIN_ORCH48_CP281_RULE_REPLAY_EXECUTION_MATERIALIZATION_RESULT_TABLE_LEDGER_2026-05-18.jsonl"
    )


def test_source_capture_contract_and_self_check_cover_each_rule():
    rows = _mapping_rows()
    contracts = build_source_capture_contract_rows(rows)
    self_checks = build_registry_self_check_rows(rows)

    assert len(contracts) == len(rows)
    assert len(self_checks) == len(rows)
    assert all(contract["event_required_field_count"] == 9 for contract in contracts)
    assert all(row["self_check_status"] == "CP281_READY_RUNTIME_REGISTRY_SELF_CHECK_PASS" for row in self_checks)


def test_aggregate_rows_and_summary_preserve_counts():
    rows = _mapping_rows()
    aggregate_rows = build_aggregate_mapping_rows(
        [
            {
                "action_class": "follow_rule",
                "average_cost_adjusted_simulated_r": 0.25,
                "average_stress_simulated_r": 0.2,
                "effective_n_sum": 12,
                "frozen_ready_action_runtime_aggregate_row_id": "AGG-1",
                "horizon_id": "h16",
                "market_timeframe": "M5",
                "route_session": "tokyo_kz",
                "rule_count": 1,
                "side": "LONG",
                "source_row_count": 1,
                "symbol_family": "USDJPY_6J_FAMILY",
            }
        ],
        source_aggregate_artifact="route/aggregates.jsonl",
        source_aggregate_artifact_sha256="3" * 64,
        moonshot_head="abc",
        moonshot_status_clean=True,
    )
    contracts = build_source_capture_contract_rows(rows)
    self_checks = build_registry_self_check_rows(rows)
    summary = summarize_mapping(
        rule_mapping_rows=rows,
        aggregate_mapping_rows=aggregate_rows,
        source_capture_contract_rows=contracts,
        registry_self_check_rows=self_checks,
        cp281_result_counts={"rule_rows": 2, "source_rows_represented": 2},
        moonshot_head="abc",
        moonshot_status_clean=True,
    )

    assert len(aggregate_rows) == 1
    assert summary["rule_mapping_rows"] == 2
    assert summary["action_class_counts"] == {"avoid_filter": 1, "follow_rule": 1}
    assert summary["implementation_effect"]["all_cp281_ready_runtime_rows_preserved"] is True


def test_branch_decision_rows_preserve_aggregate_members():
    rows = _mapping_rows()
    aggregate_rows = build_aggregate_mapping_rows(
        [
            {
                "action_class": "follow_rule",
                "average_cost_adjusted_simulated_r": 0.25,
                "average_stress_simulated_r": 0.2,
                "effective_n_sum": 12,
                "frozen_ready_action_runtime_aggregate_row_id": "AGG-1",
                "horizon_id": "h16",
                "market_timeframe": "M5",
                "route_session": "tokyo_kz",
                "rule_count": 1,
                "side": "LONG",
                "source_row_count": 1,
                "symbol_family": "USDJPY_6J_FAMILY",
            },
            {
                "action_class": "avoid_filter",
                "average_cost_adjusted_simulated_r": -0.4,
                "average_stress_simulated_r": -0.45,
                "effective_n_sum": 7,
                "frozen_ready_action_runtime_aggregate_row_id": "AGG-2",
                "horizon_id": "h32",
                "market_timeframe": "M1",
                "route_session": "ny_core",
                "rule_count": 1,
                "side": "SHORT",
                "source_row_count": 1,
                "symbol_family": "US30_YM_FAMILY",
            },
        ],
        source_aggregate_artifact="route/aggregates.jsonl",
        source_aggregate_artifact_sha256="3" * 64,
        moonshot_head="abc",
        moonshot_status_clean=True,
    )
    decisions = build_branch_decision_rows(rule_mapping_rows=rows, aggregate_mapping_rows=aggregate_rows)
    summary = summarize_branch_decisions(decisions)

    assert len(decisions) == 2
    assert {row["branch_decision_action"] for row in decisions} == {
        "DEFAULT_OFF_CP281_BRANCH_AVOID_FILTER_READY",
        "DEFAULT_OFF_CP281_BRANCH_FOLLOW_SCORER_READY",
    }
    assert all(row["all_member_rows_preserved"] for row in decisions)
    assert summary["ready_branch_decision_rows"] == 2
    assert summary["ready_follow_scope_rows"] == 1
    assert summary["ready_avoid_scope_rows"] == 1


def test_cp281_event_field_availability_uses_aliases_and_repair_actions():
    contracts = build_source_capture_contract_rows(_mapping_rows())
    required_fields = cp281_contract_required_fields(contracts)
    audit = cp281_audit_event_source_rows(
        [
            {
                "symbol_family": "USDJPY_6J_FAMILY",
                "symbol": "USDJPY_6J",
                "source_symbol": "USDJPY",
                "timeframe": "M5",
                "session": "tokyo_kz",
                "horizon_id": "h16",
                "selected_side": "LONG",
            }
        ],
        required_fields=required_fields,
    )

    assert audit["rows_with_scope_required_fields"] == 1
    assert audit["rows_with_all_required_fields"] == 0
    assert audit["field_availability_status"] == "CURRENT_SOURCE_HAS_CP281_SCOPE_BUT_MISSING_SOURCE_HASH_CONTRACT"
    assert audit["source_capture_repair_action"] == "ADD_SOURCE_PATH_SHA256_AND_SOURCE_FILE_SHA256_TO_EVENT_OUTPUT"


def test_branch_scope_registry_matches_portable_aggregate_events():
    rule_rows = _mapping_rows()
    aggregate_rows = build_aggregate_mapping_rows(
        [
            {
                "action_class": "follow_rule",
                "average_cost_adjusted_simulated_r": 0.25,
                "average_stress_simulated_r": 0.2,
                "effective_n_sum": 12,
                "frozen_ready_action_runtime_aggregate_row_id": "AGG-1",
                "horizon_id": "h16",
                "market_timeframe": "M5",
                "route_session": "tokyo_kz",
                "rule_count": 1,
                "side": "LONG",
                "source_row_count": 1,
                "symbol_family": "USDJPY_6J_FAMILY",
            }
        ],
        source_aggregate_artifact="route/aggregates.jsonl",
        source_aggregate_artifact_sha256="3" * 64,
        moonshot_head="abc",
        moonshot_status_clean=True,
    )
    decisions = build_branch_decision_rows(rule_mapping_rows=rule_rows, aggregate_mapping_rows=aggregate_rows)
    registry = CP281BranchDecisionRegistry(decisions)
    event = branch_decision_event_from_row(decisions[0])
    matches = registry.evaluate_event(event)
    contracts = build_branch_scope_contract_rows(decisions)
    self_checks = build_branch_scope_registry_self_check_rows(decisions)
    summary = summarize_branch_scope_registry(
        branch_decision_rows=decisions,
        contract_rows=contracts,
        self_check_rows=self_checks,
    )

    assert matches[0]["cp281_aggregate_row_id"] == "AGG-1"
    assert matches[0]["runtime_candidate_use_permitted"] is False
    assert contracts[0]["event_required_field_count"] == 5
    assert self_checks[0]["self_check_status"] == "CP281_BRANCH_SCOPE_REGISTRY_SELF_CHECK_PASS"
    assert summary["branch_scope_self_check_pass_rows"] == 1


def test_branch_scope_source_adapter_fans_out_horizons_and_scores_matches():
    rule_rows = _mapping_rows()
    aggregate_rows = build_aggregate_mapping_rows(
        [
            {
                "action_class": "follow_rule",
                "average_cost_adjusted_simulated_r": 0.25,
                "average_stress_simulated_r": 0.2,
                "effective_n_sum": 12,
                "frozen_ready_action_runtime_aggregate_row_id": "AGG-1",
                "horizon_id": "h16",
                "market_timeframe": "M15",
                "route_session": "tokyo_kz",
                "rule_count": 1,
                "side": "LONG",
                "source_row_count": 1,
                "symbol_family": "USDJPY_6J_FAMILY",
            }
        ],
        source_aggregate_artifact="route/aggregates.jsonl",
        source_aggregate_artifact_sha256="3" * 64,
        moonshot_head="abc",
        moonshot_status_clean=True,
    )
    decisions = build_branch_decision_rows(rule_mapping_rows=rule_rows, aggregate_mapping_rows=aggregate_rows)
    registry = CP281BranchDecisionRegistry(decisions)
    source_row = {
        "symbol": "USDJPY",
        "session": "tokyo_kz",
        "selected_side": "LONG",
    }
    events = cp281_branch_scope_events_from_source_row(source_row)
    summary = summarize_branch_scope_source_rows([source_row], registry=registry)

    assert len(events) == 3
    assert events[0]["symbol_family"] == "USDJPY_6J_FAMILY"
    assert summary["source_rows_with_cp281_branch_scope_events"] == 1
    assert summary["derived_cp281_branch_scope_event_rows"] == 3
    assert summary["registry_matched_event_rows"] == 1
    assert summary["registry_match_rows"] == 1


def test_branch_scope_replay_materialization_preserves_duplicate_conflicts():
    scope = {
        "symbol_family": "XAGUSD_SILVER_FAMILY",
        "market_timeframe": "M1",
        "route_session": "london_core",
        "horizon_id": "h32",
        "side": "LONG",
    }
    decisions = [
        {
            "row_key": "follow-key",
            "cp281_aggregate_row_id": "AGG-FOLLOW",
            "action_class": "follow_rule",
            "aggregate_scope": {"action_class": "follow_rule", **scope},
            "branch_decision_action": "DEFAULT_OFF_CP281_BRANCH_FOLLOW_SCORER_READY",
            "branch_decision_status": "READY_DEFAULT_OFF_CP281_BRANCH_DECISION",
            "main_system_surface": "cp281_default_off_follow_scorer_registry",
            "member_rule_count": 2,
            "cost_adjusted_simulated_r": {"count": 2, "min": 0.1, "max": 0.2, "mean": 0.15, "sum": 0.3},
            "stress_simulated_r": {"count": 2, "min": 0.05, "max": 0.1, "mean": 0.075, "sum": 0.15},
        },
        {
            "row_key": "avoid-key",
            "cp281_aggregate_row_id": "AGG-AVOID",
            "action_class": "avoid_filter",
            "aggregate_scope": {"action_class": "avoid_filter", **scope},
            "branch_decision_action": "DEFAULT_OFF_CP281_BRANCH_AVOID_FILTER_READY",
            "branch_decision_status": "READY_DEFAULT_OFF_CP281_BRANCH_DECISION",
            "main_system_surface": "cp281_default_off_avoid_filter_registry",
            "member_rule_count": 3,
            "cost_adjusted_simulated_r": {"count": 3, "min": -0.3, "max": -0.1, "mean": -0.2, "sum": -0.6},
            "stress_simulated_r": {"count": 3, "min": -0.35, "max": -0.2, "mean": -0.25, "sum": -0.75},
        },
    ]
    registry = CP281BranchDecisionRegistry(decisions)
    event_rows = build_branch_scope_replay_event_rows(decisions)
    match_rows = build_branch_scope_replay_match_rows(event_rows, registry=registry)
    summary = summarize_branch_scope_replay_materialization(event_rows=event_rows, match_rows=match_rows)

    assert len(event_rows) == 2
    assert len(match_rows) == 4
    assert summary["branch_scope_replay_event_rows"] == 2
    assert summary["branch_scope_replay_match_rows"] == 4
    assert summary["duplicate_scope_event_rows"] == 2
    assert summary["duplicate_scope_match_rows"] == 4
    assert summary["action_conflict_match_rows"] == 2
    assert summary["own_branch_match_rows"] == 2
