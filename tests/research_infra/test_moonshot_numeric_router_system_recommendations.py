from __future__ import annotations

from src.research_infra.moonshot_numeric_router_system_recommendations import (
    NumericRouterImplementationCatalog,
    build_numeric_router_family_action_specs,
    build_numeric_router_catalog_entries,
    compact_numeric_router_output_row,
    compact_numeric_router_action_queue_row,
    compact_scope_system_decision,
    compact_system_recommendation,
    summarize_numeric_router_family_action_specs,
    summarize_numeric_router_catalog_entries,
    summarize_numeric_router_catalog_event_contracts,
    summarize_numeric_router_catalog_event_emitter_dry_runs,
    summarize_numeric_router_catalog_scope_event_emitter_contracts,
    summarize_numeric_router_catalog_source_capture_plans,
    summarize_numeric_router_source_repair_execution_plans,
    summarize_numeric_router_source_repair_slippage_identity_adapters,
    summarize_numeric_router_source_repair_slippage_selection_events,
    summarize_numeric_router_source_repair_slippage_join_contracts,
    summarize_numeric_router_source_repair_future_slippage_lifecycle_emitter_events,
    summarize_numeric_router_source_repair_slippage_lifecycle_join_events,
    summarize_numeric_router_source_repair_source_packet_traces,
    summarize_numeric_router_source_repair_selector_events,
    summarize_numeric_router_source_repair_execution_identity_capture_contracts,
    summarize_numeric_router_source_repair_execution_identity_capture_events,
    summarize_numeric_router_source_repair_selector_routes,
    summarize_numeric_router_source_repair_selector_surfaces,
    summarize_numeric_router_source_component_bridge_audits,
    summarize_numeric_router_action_queue,
    summarize_numeric_router_output_rows,
    summarize_scope_system_decisions,
    summarize_system_recommendations,
    numeric_router_catalog_event_contract_for_entry,
    numeric_router_catalog_event_from_entry,
    numeric_router_catalog_event_from_source_row,
    numeric_router_catalog_event_from_source_row_with_component_bridge,
    numeric_router_catalog_event_from_source_row_with_catalog_attachment,
    numeric_router_catalog_event_emitter_dry_run_for_source_rows,
    numeric_router_catalog_scope_event_emitter_contract_for_source,
    numeric_router_catalog_source_capture_plan_for_adapter_spec,
    numeric_router_source_component_bridge_audit_for_source,
    numeric_router_source_repair_execution_plan_for_entry,
    numeric_router_source_repair_slippage_identity_adapter_for_contract,
    numeric_router_source_repair_slippage_identity_payload_from_adapter,
    numeric_router_source_repair_slippage_selection_event_from_adapter,
    numeric_router_source_repair_slippage_join_contract_for_plan,
    numeric_router_source_repair_slippage_join_event_from_row,
    numeric_router_source_repair_source_packet_trace_for_proof_row,
    numeric_router_source_repair_selector_event_from_surface,
    numeric_router_source_repair_execution_identity_capture_contract_for_route,
    numeric_router_source_repair_execution_identity_capture_event_from_slippage_row,
    numeric_router_source_repair_future_slippage_lifecycle_emitter_event_from_contract,
    numeric_router_source_repair_execution_identity_lifecycle_join_event_from_pair,
    numeric_router_source_repair_slippage_lifecycle_pairs,
    numeric_router_source_repair_selector_route_for_event,
    numeric_router_source_repair_selector_surface_for_selection_event,
)


def test_compact_scope_system_decision_keeps_default_off_boundary():
    row = compact_scope_system_decision(
        {
            "scope_system_decision_row_id": "SCOPE-1",
            "input_scope_router_decision_row_id": "INPUT-1",
            "symbol": "XAUUSD",
            "source_component": "market_gap_code",
            "implementation_candidate_type": "DEFAULT_OFF_SCORER_REGISTRY_SCOPE",
            "router_scope_decision": "IMPLEMENT_DEFAULT_OFF_SCORER_SCOPE_WITH_GUARDS",
            "row_count": 10,
            "score_count": 4,
            "scorer_event_count": 4,
            "avoid_inverse_event_count": 2,
            "context_stress_event_count": 1,
            "source_repair_event_count": 3,
            "summary_only_terminal": False,
        },
        source_artifact="scope.jsonl",
        source_line_no=1,
        source_sha256="scope-sha",
    )
    summary = summarize_scope_system_decisions([row])

    assert row["runtime_score_allowed"] is False
    assert row["candidate_use_allowed_now"] is False
    assert row["research_boundary"]["production_import_path"] is False
    assert summary["rows"] == 1
    assert summary["row_count_sum"] == 10
    assert summary["summary_only_terminal_rows"] == 0


def test_compact_system_recommendation_preserves_counts_without_runtime_use():
    row = compact_system_recommendation(
        {
            "system_recommendation_row_id": "RECO-1",
            "system_recommendation": "Register default-off surfaces.",
            "scope_system_decision_rows": 290,
            "scorer_registry_surface_rows": 5341,
            "avoid_comparator_score_rows": 4115,
            "context_guard_input_rows": 1513,
            "source_repair_proof_rows": 17753,
            "not_completion": True,
            "not_terminal": True,
        },
        source_artifact="system.jsonl",
        source_line_no=1,
        source_sha256="system-sha",
    )
    summary = summarize_system_recommendations([row])

    assert row["candidate_use_allowed_now"] is False
    assert row["runtime_candidate_use_permitted"] is False
    assert row["replay_r_reference_counted_as_new_main_result"] is False
    assert summary["scope_system_decision_rows"] == 290
    assert summary["source_repair_proof_rows"] == 17753


def test_compact_numeric_router_output_row_preserves_source_row_without_runtime_use():
    row = compact_numeric_router_output_row(
        {"scorer_surface_status": "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS", "score": 0.15},
        output_family="scorer_registry_surface",
        output_row_id="OUT-1",
        source_artifact="scorer.jsonl",
        source_line_no=1,
        source_sha256="scorer-sha",
    )
    summary = summarize_numeric_router_output_rows([row])

    assert row["source_row"]["score"] == 0.15
    assert row["runtime_score_allowed"] is False
    assert row["runtime_candidate_use_permitted"] is False
    assert row["candidate_use_allowed_now"] is False
    assert summary["rows"] == 1
    assert summary["output_family_counts"]["scorer_registry_surface"] == 1


def test_compact_numeric_router_action_queue_row_derives_action_without_source_payload_duplication():
    output = compact_numeric_router_output_row(
        {
            "registry_surface_status": "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS",
            "symbol": "NAS100",
            "source_component": "registry_scorer_module",
            "registry_surface_score": 0.15,
        },
        output_family="scorer_registry_surface",
        output_row_id="OUT-1",
        source_artifact="scorer.jsonl",
        source_line_no=1,
        source_sha256="scorer-sha",
    )

    action = compact_numeric_router_action_queue_row(
        output,
        action_row_id="ACTION-1",
        source_artifact="wrapped.jsonl",
        source_line_no=1,
        source_sha256="wrapped-sha",
    )
    summary = summarize_numeric_router_action_queue([action])

    assert "source_row" not in action
    assert action["numeric_router_action"] == "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS"
    assert action["registry_surface_score"] == 0.15
    assert action["runtime_candidate_use_permitted"] is False
    assert summary["rows"] == 1
    assert summary["numeric_router_action_counts"]["DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS"] == 1


def test_build_numeric_router_family_action_specs_groups_default_off_scorer_rows():
    rows = [
        {
            "numeric_router_action_row_id": "ACTION-1",
            "output_family": "scorer_registry_surface",
            "numeric_router_action": "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS",
            "symbol": "NAS100",
            "route_session": "off_core_session",
            "horizon_id": "h4",
            "source_component": "registry_scorer_module",
            "primitive_flag": "DELTA_IMPULSE_P95_SAME_SYMBOL_SESSION",
            "proxy_r_class": "STRONG_POSITIVE_PROXY_R",
            "target_stop_order_class": "TARGET_STOP_ORDER_NOT_SOURCE_BOUND",
            "registry_surface_score": 0.2,
            "source_row_id": "ROW-1",
            "source_artifact": "scorer.jsonl",
            "source_sha256": "scorer-sha",
            "source_line_no": 1,
        },
        {
            "numeric_router_action_row_id": "ACTION-2",
            "output_family": "scorer_registry_surface",
            "numeric_router_action": "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS",
            "symbol": "NAS100",
            "route_session": "off_core_session",
            "horizon_id": "h4",
            "source_component": "registry_scorer_module",
            "primitive_flag": "DELTA_IMPULSE_P95_SAME_SYMBOL_SESSION",
            "proxy_r_class": "STRONG_POSITIVE_PROXY_R",
            "target_stop_order_class": "TARGET_STOP_ORDER_NOT_SOURCE_BOUND",
            "registry_surface_score": 0.1,
            "source_row_id": "ROW-2",
            "source_artifact": "scorer.jsonl",
            "source_sha256": "scorer-sha",
            "source_line_no": 2,
        },
    ]

    specs = build_numeric_router_family_action_specs(rows)
    summary = summarize_numeric_router_family_action_specs(specs)

    assert len(specs) == 1
    assert specs[0]["activation_state"] == "DEFAULT_OFF"
    assert specs[0]["family_spec_type"] == "default_off_scorer_registry_surface_spec"
    assert specs[0]["implementation_target"] == "default_off_research_scorer_registry_catalog"
    assert specs[0]["input_action_rows"] == 2
    assert specs[0]["registry_surface_score_stats"]["mean"] == 0.15
    assert specs[0]["source_locator_refs"][0]["line_count"] == 2
    assert specs[0]["runtime_candidate_use_permitted"] is False
    assert summary["input_action_rows"] == 2
    assert summary["numeric_router_action_counts"]["DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS"] == 2


def test_build_numeric_router_family_action_specs_routes_avoid_context_and_repair_targets():
    rows = [
        {
            "numeric_router_action_row_id": "ACTION-1",
            "output_family": "avoid_comparator_score",
            "numeric_router_action": "AVOID_CURRENT_ENTRY_STOP_FIRST_PROXY",
            "symbol": "GBPJPY",
            "source_component": "nofill_far_miss_avoid",
            "proxy_r_class": "STRONG_NEGATIVE_PROXY_R",
            "avoid_comparator_score": -0.42,
            "source_artifact": "avoid.jsonl",
            "source_sha256": "avoid-sha",
            "source_line_no": 10,
        },
        {
            "numeric_router_action_row_id": "ACTION-2",
            "output_family": "context_guard_input",
            "numeric_router_action": "MERGE_AS_CONTEXT_STRESS_GUARD_INPUT",
            "symbol": "XAUUSD",
            "source_component": "shadow_source_guard",
            "proxy_r_class": "NEUTRAL_PROXY_R",
            "source_artifact": "context.jsonl",
            "source_sha256": "context-sha",
            "source_line_no": 20,
        },
        {
            "numeric_router_action_row_id": "ACTION-3",
            "output_family": "source_repair_proof",
            "numeric_router_action": "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R",
            "symbol": "NAS100",
            "source_component": "registry_scorer_module",
            "repair_action": "join_or_reconstruct_broker_execution_geometry_fields",
            "missing_field_count": 12,
            "source_artifact": "repair.jsonl",
            "source_sha256": "repair-sha",
            "source_line_no": 30,
        },
    ]

    specs = build_numeric_router_family_action_specs(rows)
    spec_types = {row["family_spec_type"] for row in specs}
    summary = summarize_numeric_router_family_action_specs(specs)

    assert "avoid_filter_stop_first_proxy_spec" in spec_types
    assert "context_stress_guard_input_spec" in spec_types
    assert "source_repair_broker_execution_geometry_queue_spec" in spec_types
    assert summary["input_action_rows"] == 3
    assert summary["implementation_target_counts"]["default_off_avoid_filter_spec_catalog"] == 1
    assert summary["implementation_target_counts"]["default_off_context_guard_spec_catalog"] == 1
    assert summary["implementation_target_counts"]["source_repair_queue_catalog"] == 1
    assert all(row["candidate_use_allowed_now"] is False for row in specs)


def test_build_numeric_router_catalog_entries_prioritizes_source_repair_before_default_off_catalogs():
    family_specs = [
        {
            "numeric_router_family_spec_id": "SPEC-1",
            "implementation_target": "default_off_research_scorer_registry_catalog",
            "output_family": "scorer_registry_surface",
            "family_spec_type": "default_off_scorer_registry_surface_spec",
            "numeric_router_action": "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS",
            "symbol": "NAS100",
            "input_action_rows": 50,
            "source_locator_refs": [{"source_artifact": "scorer.jsonl", "line_count": 50}],
        },
        {
            "numeric_router_family_spec_id": "SPEC-2",
            "implementation_target": "source_repair_queue_catalog",
            "output_family": "source_repair_proof",
            "family_spec_type": "source_repair_broker_execution_geometry_queue_spec",
            "numeric_router_action": "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R",
            "symbol": "NAS100",
            "input_action_rows": 10,
            "source_locator_refs": [{"source_artifact": "repair.jsonl", "line_count": 10}],
        },
    ]

    entries = build_numeric_router_catalog_entries(family_specs)
    summary = summarize_numeric_router_catalog_entries(entries)

    assert entries[0]["catalog_type"] == "source_repair_queue_entry"
    assert entries[0]["catalog_priority_bucket"] == "P0_SOURCE_REPAIR_EXACT_R_GEOMETRY"
    assert entries[0]["catalog_entry_status"] == "READY_FOR_SOURCE_REPAIR_QUEUE"
    assert entries[1]["catalog_type"] == "default_off_scorer_registry_catalog_entry"
    assert entries[1]["activation_state"] == "DEFAULT_OFF"
    assert entries[1]["runtime_candidate_use_permitted"] is False
    assert summary["rows"] == 2
    assert summary["input_action_rows"] == 60
    assert summary["catalog_priority_bucket_input_action_counts"]["P0_SOURCE_REPAIR_EXACT_R_GEOMETRY"] == 10


def test_build_numeric_router_catalog_entries_routes_avoid_and_context_catalogs():
    family_specs = [
        {
            "numeric_router_family_spec_id": "SPEC-1",
            "implementation_target": "default_off_avoid_filter_spec_catalog",
            "output_family": "avoid_comparator_score",
            "family_spec_type": "avoid_filter_stop_first_proxy_spec",
            "numeric_router_action": "AVOID_CURRENT_ENTRY_STOP_FIRST_PROXY",
            "symbol": "GBPJPY",
            "input_action_rows": 7,
            "source_locator_refs": [{"source_artifact": "avoid.jsonl", "line_count": 7}],
        },
        {
            "numeric_router_family_spec_id": "SPEC-2",
            "implementation_target": "default_off_context_guard_spec_catalog",
            "output_family": "context_guard_input",
            "family_spec_type": "context_stress_guard_input_spec",
            "numeric_router_action": "MERGE_AS_CONTEXT_STRESS_GUARD_INPUT",
            "symbol": "XAUUSD",
            "input_action_rows": 3,
            "source_locator_refs": [{"source_artifact": "context.jsonl", "line_count": 3}],
        },
    ]

    entries = build_numeric_router_catalog_entries(family_specs)
    summary = summarize_numeric_router_catalog_entries(entries)

    assert {row["catalog_type"] for row in entries} == {
        "default_off_avoid_filter_catalog_entry",
        "default_off_context_guard_catalog_entry",
    }
    assert summary["catalog_priority_bucket_counts"]["P1_AVOID_STOP_FIRST_PROXY"] == 1
    assert summary["catalog_priority_bucket_counts"]["P4_CONTEXT_STRESS_GUARD_INPUT"] == 1
    assert all(row["candidate_use_allowed_now"] is False for row in entries)


def test_numeric_router_implementation_catalog_matches_default_off_entry_without_runtime_use():
    entries = build_numeric_router_catalog_entries(
        [
            {
                "numeric_router_family_spec_id": "SPEC-1",
                "implementation_target": "default_off_research_scorer_registry_catalog",
                "output_family": "scorer_registry_surface",
                "family_spec_type": "default_off_scorer_registry_surface_spec",
                "numeric_router_action": "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS",
                "symbol": "NAS100",
                "horizon_id": "h4",
                "source_component": "registry_scorer_module",
                "primitive_flag": "DELTA_IMPULSE_P95_SAME_SYMBOL_SESSION",
                "proxy_r_class": "STRONG_POSITIVE_PROXY_R",
                "target_stop_order_class": "TARGET_STOP_ORDER_NOT_SOURCE_BOUND",
                "input_action_rows": 2,
                "source_locator_refs": [{"source_artifact": "scorer.jsonl", "line_count": 2}],
            }
        ]
    )
    catalog = NumericRouterImplementationCatalog(entries)

    matches = catalog.evaluate_event(numeric_router_catalog_event_from_entry(entries[0]))

    assert len(matches) == 1
    assert matches[0]["input_numeric_router_catalog_entry_id"] == entries[0]["numeric_router_catalog_entry_id"]
    assert matches[0]["catalog_evaluation_status"] == "DEFAULT_OFF_NUMERIC_ROUTER_CATALOG_MATCH"
    assert matches[0]["runtime_candidate_use_permitted"] is False
    assert matches[0]["candidate_use_allowed_now"] is False
    assert catalog.summarize_catalog()["catalog_entries"] == 1


def test_numeric_router_implementation_catalog_skips_source_repair_queue_by_default():
    entries = build_numeric_router_catalog_entries(
        [
            {
                "numeric_router_family_spec_id": "SPEC-1",
                "implementation_target": "source_repair_queue_catalog",
                "output_family": "source_repair_proof",
                "family_spec_type": "source_repair_broker_execution_geometry_queue_spec",
                "numeric_router_action": "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R",
                "symbol": "NAS100",
                "source_component": "registry_scorer_module",
                "repair_action": "join_or_reconstruct_broker_execution_geometry_fields",
                "missing_field_count": "12",
                "input_action_rows": 5,
                "source_locator_refs": [{"source_artifact": "repair.jsonl", "line_count": 5}],
            }
        ]
    )
    catalog = NumericRouterImplementationCatalog(entries)
    event = numeric_router_catalog_event_from_entry(entries[0])

    assert catalog.evaluate_event(event) == []
    assert len(catalog.evaluate_event(event, include_source_repair=True)) == 1
    assert catalog.summarize_catalog()["source_repair_queue_entries"] == 1


def test_numeric_router_catalog_event_contract_names_only_required_nonempty_fields():
    entry = build_numeric_router_catalog_entries(
        [
            {
                "numeric_router_family_spec_id": "SPEC-1",
                "implementation_target": "default_off_context_guard_spec_catalog",
                "output_family": "context_guard_input",
                "family_spec_type": "context_stress_guard_input_spec",
                "numeric_router_action": "MERGE_AS_CONTEXT_STRESS_GUARD_INPUT",
                "symbol": "XAUUSD",
                "route_session": "",
                "source_component": "registry_scorer_module",
                "primitive_flag": "SPREAD_SHOCK_P95_SAME_SYMBOL_SESSION",
                "proxy_r_class": "NEUTRAL_PROXY_R",
                "input_action_rows": 3,
                "source_locator_refs": [{"source_artifact": "context.jsonl", "line_count": 3}],
            }
        ]
    )[0]

    contract = numeric_router_catalog_event_contract_for_entry(
        entry,
        contract_row_id="CONTRACT-1",
        source_artifact="catalog.jsonl",
        source_line_no=1,
        source_sha256="catalog-sha",
    )
    summary = summarize_numeric_router_catalog_event_contracts([contract])

    assert "symbol" in contract["required_event_fields"]
    assert "route_session" not in contract["required_event_fields"]
    assert contract["source_capture_contract_status"] == "READY_DEFAULT_OFF_NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT"
    assert contract["runtime_candidate_use_permitted"] is False
    assert summary["ready_contract_rows"] == 1
    assert summary["required_event_field_counts"]["primitive_flag"] == 1


def test_numeric_router_catalog_event_from_source_row_reports_missing_required_fields():
    event = numeric_router_catalog_event_from_source_row(
        {
            "symbol": "XAUUSD",
            "source_component": "registry_scorer_module",
        },
        event_row_id="EVENT-1",
        required_event_fields=["symbol", "source_component", "primitive_flag"],
    )

    assert event["event_adapter_status"] == "NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT_INCOMPLETE"
    assert event["missing_required_fields"] == ["primitive_flag"]
    assert event["runtime_candidate_use_permitted"] is False


def test_numeric_router_catalog_event_from_source_row_maps_supported_aliases():
    event = numeric_router_catalog_event_from_source_row(
        {
            "broker_symbol": "XAGUSD",
            "session": "london",
            "strategy_family": "current_live_baseline",
        },
        event_row_id="EVENT-1",
        required_event_fields=["symbol", "route_session", "source_component"],
    )

    assert event["event_adapter_status"] == "NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT_COMPLETE"
    assert event["symbol"] == "XAGUSD"
    assert event["route_session"] == "london"
    assert event["source_component"] == "current_live_baseline"
    assert event["event_field_sources"] == {
        "symbol": "broker_symbol",
        "route_session": "session",
        "source_component": "strategy_family",
    }


def test_numeric_router_catalog_event_component_bridge_blocks_loose_framework_aliases_without_explicit_map():
    event = numeric_router_catalog_event_from_source_row_with_component_bridge(
        {
            "symbol": "XAUUSD",
            "session": "london",
            "strategy_family": "current_live_baseline",
        },
        event_row_id="EVENT-1",
        required_event_fields=["symbol", "route_session", "source_component"],
    )

    assert event["event_adapter_status"] == "NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT_INCOMPLETE"
    assert event["source_component"] == ""
    assert event["source_component_bridge_status"] == "SOURCE_COMPONENT_SEMANTIC_BRIDGE_REQUIRED"
    assert event["missing_required_fields"] == ["source_component"]


def test_numeric_router_catalog_event_component_bridge_accepts_explicit_map():
    event = numeric_router_catalog_event_from_source_row_with_component_bridge(
        {
            "symbol": "XAUUSD",
            "session": "london",
            "strategy_family": "current_live_baseline",
        },
        event_row_id="EVENT-1",
        required_event_fields=["symbol", "route_session", "source_component"],
        source_component_bridge={"current_live_baseline": "default_off_application"},
    )

    assert event["event_adapter_status"] == "NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT_COMPLETE"
    assert event["source_component"] == "default_off_application"
    assert event["event_field_sources"]["source_component"] == "bridge:current_live_baseline"
    assert event["source_component_bridge_status"] == "SOURCE_COMPONENT_BRIDGED_BY_EXPLICIT_MAP"


def test_numeric_router_catalog_source_capture_plan_splits_alias_route_and_catalog_scope_fields():
    rows = [
        numeric_router_catalog_source_capture_plan_for_adapter_spec(
            {
                "adapter_spec_row_id": "SPEC-1",
                "source_path": "shadow_logs/candidate_path_follow.jsonl",
                "source_exists": True,
                "source_rows_scanned": 10,
                "required_event_field": "route_session",
                "adapter_resolution": "MISSING_REQUIRES_UPSTREAM_CAPTURE",
                "alias_candidates": ["route_session", "session", "kill_zone"],
                "alias_presence_counts": {},
            },
            plan_row_id="PLAN-1",
            contract_rows_requiring_field=1055,
        ),
        numeric_router_catalog_source_capture_plan_for_adapter_spec(
            {
                "adapter_spec_row_id": "SPEC-2",
                "source_path": "shadow_logs/candidate_features_log.jsonl",
                "source_exists": True,
                "source_rows_scanned": 10,
                "required_event_field": "source_component",
                "adapter_resolution": "ALIAS_AVAILABLE_NEEDS_ADAPTER_MAPPING",
                "alias_candidates": ["source_component", "strategy_family", "framework"],
                "alias_presence_counts": {"framework": 10},
            },
            plan_row_id="PLAN-2",
            contract_rows_requiring_field=1072,
        ),
        numeric_router_catalog_source_capture_plan_for_adapter_spec(
            {
                "adapter_spec_row_id": "SPEC-3",
                "source_path": "shadow_logs/strategy_follow_candidates.jsonl",
                "source_exists": True,
                "source_rows_scanned": 10,
                "required_event_field": "primitive_flag",
                "adapter_resolution": "MISSING_REQUIRES_UPSTREAM_CAPTURE",
                "alias_candidates": ["primitive_flag"],
                "alias_presence_counts": {},
            },
            plan_row_id="PLAN-3",
            contract_rows_requiring_field=882,
        ),
    ]
    summary = summarize_numeric_router_catalog_source_capture_plans(rows)

    assert rows[0]["source_capture_plan_status"] == "PRODUCER_ROUTE_SESSION_CAPTURE_PATCHED_OR_REQUIRED"
    assert rows[0]["source_capture_owner"] == "scripts/follow_live_candidate_paths.py::build_follow_row"
    assert rows[1]["source_capture_plan_status"] == "CURRENT_SOURCE_FIELD_ALIAS_ADAPTABLE"
    assert rows[1]["current_log_field_complete"] is True
    assert rows[2]["source_capture_plan_status"] == "NUMERIC_ROUTER_CATALOG_SCOPE_ATTACHMENT_REQUIRED"
    assert rows[2]["source_capture_owner"] == "numeric_router_catalog_entry_scope"
    assert summary["current_log_complete_field_rows"] == 1
    assert summary["requires_code_or_upstream_capture_rows"] == 2
    assert summary["current_source_complete_event_sources"] == 0


def test_numeric_router_catalog_scope_event_emitter_contract_closes_catalog_owned_fields():
    contract = numeric_router_catalog_event_contract_for_entry(
        {
            "numeric_router_catalog_entry_id": "CAT-1",
            "input_numeric_router_family_spec_id": "SPEC-1",
            "catalog_type": "default_off_scorer_registry_catalog_entry",
            "catalog_priority_bucket": "P3_SCORER_DEFAULT_OFF_SURFACE",
            "numeric_router_action": "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS",
            "implementation_target": "default_off_research_scorer_registry_catalog",
            "symbol": "XAGUSD",
            "route_session": "london",
            "horizon_id": "h4",
            "source_component": "current_live_baseline",
            "primitive_flag": "DELTA_IMPULSE_P95_SAME_SYMBOL_SESSION",
            "proxy_r_class": "STRONG_POSITIVE_PROXY_R",
            "target_stop_order_class": "TARGET_FIRST_PROXY_DOMINANT",
            "input_action_rows": 3,
        },
        contract_row_id="CONTRACT-1",
        source_artifact="catalog.jsonl",
        source_line_no=1,
        source_sha256="catalog-sha",
    )
    plan_rows = [
        {
            "required_event_field": "symbol",
            "source_capture_plan_status": "CURRENT_SOURCE_FIELD_DIRECTLY_ADAPTABLE",
        },
        {
            "required_event_field": "route_session",
            "source_capture_plan_status": "PRODUCER_ROUTE_SESSION_CAPTURE_PATCHED_OR_REQUIRED",
        },
        {
            "required_event_field": "source_component",
            "source_capture_plan_status": "CURRENT_SOURCE_FIELD_ALIAS_ADAPTABLE",
        },
        {
            "required_event_field": "horizon_id",
            "source_capture_plan_status": "NUMERIC_ROUTER_CATALOG_SCOPE_ATTACHMENT_REQUIRED",
        },
        {
            "required_event_field": "primitive_flag",
            "source_capture_plan_status": "NUMERIC_ROUTER_CATALOG_SCOPE_ATTACHMENT_REQUIRED",
        },
        {
            "required_event_field": "proxy_r_class",
            "source_capture_plan_status": "NUMERIC_ROUTER_CATALOG_SCOPE_ATTACHMENT_REQUIRED",
        },
        {
            "required_event_field": "target_stop_order_class",
            "source_capture_plan_status": "NUMERIC_ROUTER_CATALOG_SCOPE_ATTACHMENT_REQUIRED",
        },
    ]

    emitter = numeric_router_catalog_scope_event_emitter_contract_for_source(
        source_path="shadow_logs/candidate_path_follow.jsonl",
        source_plan_rows=plan_rows,
        contract_rows=[contract],
        emitter_contract_id="EMITTER-1",
    )
    summary = summarize_numeric_router_catalog_scope_event_emitter_contracts([emitter])

    assert emitter["event_emitter_contract_status"] == "READY_DEFAULT_OFF_CATALOG_SCOPE_EVENT_EMITTER_CONTRACT"
    assert emitter["source_adapter_prospectively_complete"] is True
    assert emitter["historical_current_log_complete_after_catalog_attachment"] is False
    assert emitter["producer_patched_source_fields"] == ["route_session"]
    assert set(emitter["catalog_scope_attachment_fields"]) == {
        "horizon_id",
        "primitive_flag",
        "proxy_r_class",
        "target_stop_order_class",
    }
    assert summary["source_adapter_prospectively_complete_rows"] == 1
    assert summary["catalog_scope_attachment_field_source_rows"]["primitive_flag"] == 1
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def test_numeric_router_catalog_event_attaches_catalog_scope_fields_after_source_match():
    entry = build_numeric_router_catalog_entries(
        [
            {
                "numeric_router_family_spec_id": "SPEC-1",
                "implementation_target": "default_off_research_scorer_registry_catalog",
                "output_family": "scorer_registry_surface",
                "family_spec_type": "default_off_scorer_registry_surface_spec",
                "numeric_router_action": "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS",
                "symbol": "XAGUSD",
                "route_session": "london",
                "horizon_id": "h4",
                "source_component": "current_live_baseline",
                "primitive_flag": "DELTA_IMPULSE_P95_SAME_SYMBOL_SESSION",
                "proxy_r_class": "STRONG_POSITIVE_PROXY_R",
                "target_stop_order_class": "TARGET_FIRST_PROXY_DOMINANT",
                "input_action_rows": 2,
            }
        ]
    )[0]
    contract = numeric_router_catalog_event_contract_for_entry(
        entry,
        contract_row_id="CONTRACT-1",
        source_artifact="catalog.jsonl",
        source_line_no=1,
        source_sha256="catalog-sha",
    )

    event = numeric_router_catalog_event_from_source_row_with_catalog_attachment(
        {
            "symbol": "XAGUSD",
            "session": "london",
            "strategy_family": "current_live_baseline",
        },
        contract,
        event_row_id="EVENT-1",
    )
    matches = NumericRouterImplementationCatalog([entry]).evaluate_event(event)

    assert event["event_adapter_status"] == "NUMERIC_ROUTER_CATALOG_EVENT_COMPLETE_AFTER_CATALOG_SCOPE_ATTACHMENT"
    assert event["missing_required_fields"] == []
    assert event["catalog_scope_attached_fields"] == [
        "horizon_id",
        "primitive_flag",
        "proxy_r_class",
        "target_stop_order_class",
    ]
    assert event["primitive_flag"] == "DELTA_IMPULSE_P95_SAME_SYMBOL_SESSION"
    assert len(matches) == 1
    assert matches[0]["runtime_candidate_use_permitted"] is False


def test_numeric_router_catalog_event_emitter_dry_run_counts_all_matching_source_rows():
    contract = numeric_router_catalog_event_contract_for_entry(
        {
            "numeric_router_catalog_entry_id": "CAT-1",
            "input_numeric_router_family_spec_id": "SPEC-1",
            "catalog_type": "default_off_scorer_registry_catalog_entry",
            "catalog_priority_bucket": "P3_SCORER_DEFAULT_OFF_SURFACE",
            "numeric_router_action": "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS",
            "implementation_target": "default_off_research_scorer_registry_catalog",
            "symbol": "GBPJPY",
            "route_session": "tokyo",
            "source_component": "current_live_baseline",
            "primitive_flag": "FAR_MISS_RETEST",
            "proxy_r_class": "STRONG_POSITIVE_PROXY_R",
            "target_stop_order_class": "TARGET_FIRST_PROXY_DOMINANT",
            "input_action_rows": 3,
        },
        contract_row_id="CONTRACT-1",
        source_artifact="catalog.jsonl",
        source_line_no=1,
        source_sha256="catalog-sha",
    )

    dry_run = numeric_router_catalog_event_emitter_dry_run_for_source_rows(
        source_path="shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl",
        source_rows=[
            {"symbol": "GBPJPY", "session": "tokyo", "strategy_family": "current_live_baseline"},
            {"symbol": "GBPJPY", "session": "tokyo", "strategy_family": "current_live_baseline"},
            {"symbol": "GBPJPY", "session": "ny", "strategy_family": "current_live_baseline"},
        ],
        contract_rows=[contract],
        dry_run_row_id="DRY-RUN-1",
    )
    summary = summarize_numeric_router_catalog_event_emitter_dry_runs([dry_run])

    assert dry_run["dry_run_status"] == "CURRENT_ROWS_EMIT_COMPLETE_DEFAULT_OFF_CATALOG_EVENTS"
    assert dry_run["source_rows_scanned"] == 3
    assert dry_run["source_rows_with_contract_match_after_catalog_attachment"] == 2
    assert dry_run["unique_contracts_matched_after_catalog_attachment"] == 1
    assert dry_run["emitted_complete_catalog_event_count"] == 2
    assert summary["emitted_complete_catalog_event_count"] == 2
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def test_numeric_router_source_component_bridge_audit_requires_explicit_mapping_when_vocabularies_do_not_overlap():
    row = numeric_router_source_component_bridge_audit_for_source(
        source_path="shadow_logs/candidate_path_follow.jsonl",
        current_source_component_counts={"ob_retest": 10, "breaker_re_entry": 2},
        catalog_source_component_counts={"shadow_source_guard": 5, "market_gap_code": 4},
        bridge_audit_row_id="BRIDGE-1",
    )
    summary = summarize_numeric_router_source_component_bridge_audits([row])

    assert row["source_component_bridge_status"] == "SOURCE_COMPONENT_SEMANTIC_BRIDGE_REQUIRED_BEFORE_EVENT_MATCH"
    assert row["exact_match_values"] == []
    assert row["bridge_required_values"] == ["breaker_re_entry", "ob_retest"]
    assert row["semantic_guardrail"].startswith("do_not_treat_framework_strategy_family")
    assert summary["sources_requiring_semantic_bridge"] == 1
    assert summary["global_catalog_uncovered_values"] == ["market_gap_code", "shadow_source_guard"]
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def test_numeric_router_source_repair_execution_plan_maps_exact_r_geometry_without_broker_operation():
    entry = build_numeric_router_catalog_entries(
        [
            {
                "numeric_router_family_spec_id": "SPEC-1",
                "implementation_target": "source_repair_queue_catalog",
                "output_family": "source_repair_proof",
                "family_spec_type": "source_repair_broker_execution_geometry_queue_spec",
                "numeric_router_action": "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R",
                "symbol": "NAS100",
                "source_component": "registry_scorer_module",
                "repair_action": "join_or_reconstruct_broker_execution_geometry_fields",
                "missing_field_count": "12",
                "input_action_rows": 10,
                "source_locator_refs": [{"source_artifact": "repair.jsonl", "line_count": 10}],
            }
        ]
    )[0]

    plan = numeric_router_source_repair_execution_plan_for_entry(
        entry,
        plan_row_id="PLAN-1",
        source_artifact="source_repair_queue.jsonl",
        source_line_no=1,
        source_sha256="repair-sha",
    )
    summary = summarize_numeric_router_source_repair_execution_plans([plan])

    assert plan["source_repair_plan_kind"] == "broker_execution_geometry_exact_r_repair_plan"
    assert plan["required_source_class"] == "broker_execution_geometry_fields"
    assert plan["requires_broker_operation_now"] is False
    assert plan["runtime_candidate_use_permitted"] is False
    assert summary["ready_plan_rows"] == 1
    assert summary["source_repair_plan_kind_input_action_counts"]["broker_execution_geometry_exact_r_repair_plan"] == 10


def test_numeric_router_source_repair_execution_plan_maps_join_absence_and_spread_attachment():
    entries = build_numeric_router_catalog_entries(
        [
            {
                "numeric_router_family_spec_id": "SPEC-1",
                "implementation_target": "source_repair_queue_catalog",
                "output_family": "source_repair_proof",
                "family_spec_type": "source_repair_join_absence_proof_queue_spec",
                "numeric_router_action": "SOURCE_JOIN_REPAIR_REQUIRED_WITH_CURRENT_PACKET_ABSENCE_PROOF",
                "input_action_rows": 2,
                "source_locator_refs": [{"source_artifact": "repair.jsonl", "line_count": 2}],
            },
            {
                "numeric_router_family_spec_id": "SPEC-2",
                "implementation_target": "source_repair_queue_catalog",
                "output_family": "source_repair_proof",
                "family_spec_type": "source_repair_broker_geometry_attachment_queue_spec",
                "numeric_router_action": "BROKER_GEOMETRY_ATTACHMENT_REQUIRED_FOR_EXACT_SPREAD_PROXY",
                "input_action_rows": 3,
                "source_locator_refs": [{"source_artifact": "repair.jsonl", "line_count": 3}],
            },
        ]
    )
    plans = [
        numeric_router_source_repair_execution_plan_for_entry(
            entry,
            plan_row_id=f"PLAN-{index}",
            source_artifact="source_repair_queue.jsonl",
            source_line_no=index,
            source_sha256="repair-sha",
        )
        for index, entry in enumerate(entries, start=1)
    ]
    required_classes = {row["required_source_class"] for row in plans}

    assert "source_join_keys_or_original_packet_rows" in required_classes
    assert "broker_spread_or_quote_geometry_fields" in required_classes
    assert all(row["candidate_use_allowed_now"] is False for row in plans)


def test_numeric_router_source_repair_slippage_join_contract_requires_identity_carry_through():
    plan = numeric_router_source_repair_execution_plan_for_entry(
        build_numeric_router_catalog_entries(
            [
                {
                    "numeric_router_family_spec_id": "SPEC-1",
                    "implementation_target": "source_repair_queue_catalog",
                    "output_family": "source_repair_proof",
                    "family_spec_type": "source_repair_broker_execution_geometry_queue_spec",
                    "numeric_router_action": "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R",
                    "symbol": "NAS100",
                    "source_component": "registry_scorer_module",
                    "repair_action": "join_or_reconstruct_broker_execution_geometry_fields",
                    "missing_field_count": "12",
                    "input_action_rows": 10,
                }
            ]
        )[0],
        plan_row_id="PLAN-1",
        source_artifact="source_repair_queue.jsonl",
        source_line_no=1,
        source_sha256="repair-sha",
    )

    contract = numeric_router_source_repair_slippage_join_contract_for_plan(
        plan,
        contract_row_id="JOIN-1",
        source_artifact="source_repair_plan.jsonl",
        source_line_no=1,
        source_sha256="plan-sha",
    )
    summary = summarize_numeric_router_source_repair_slippage_join_contracts([contract])

    assert contract["slippage_join_contract_status"] == "READY_PROSPECTIVE_SLIPPAGE_ROW_IDENTITY_JOIN_CONTRACT"
    assert contract["slippage_row_identity_binding_required"] is True
    assert contract["required_source_repair_identity_fields"] == [
        "source_repair_plan_row_id",
        "input_numeric_router_catalog_entry_id",
        "input_numeric_router_family_spec_id",
    ]
    assert "order_ticket" in contract["required_order_identity_any_of"]
    assert "executed_exit_price" in contract["required_slippage_geometry_fields"]
    assert contract["source_repair_identity_key"] == "PLAN-1|MAIN-ORCH48-NUMERIC-ROUTER-CATALOG-ENTRY-00000001|SPEC-1"
    assert summary["slippage_row_identity_binding_required_rows"] == 1
    assert summary["exact_r_repaired_by_this_contract_rows"] == 0
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def test_numeric_router_source_repair_slippage_join_event_is_complete_only_with_identity_and_order_key():
    contract = {
        "slippage_join_contract_row_id": "JOIN-1",
        "slippage_join_contract_status": "READY_PROSPECTIVE_SLIPPAGE_ROW_IDENTITY_JOIN_CONTRACT",
        "input_source_repair_plan_row_id": "PLAN-1",
        "input_numeric_router_catalog_entry_id": "CAT-1",
        "input_numeric_router_family_spec_id": "SPEC-1",
        "source_repair_identity_key": "PLAN-1|CAT-1|SPEC-1",
        "required_source_repair_identity_fields": [
            "source_repair_plan_row_id",
            "input_numeric_router_catalog_entry_id",
            "input_numeric_router_family_spec_id",
        ],
        "required_order_identity_any_of": ["order_ticket", "deal_ticket"],
        "required_slippage_geometry_fields": ["order_ticket", "deal_ticket", "executed_entry_price"],
    }

    incomplete = numeric_router_source_repair_slippage_join_event_from_row(
        {"order_ticket": 123},
        contract,
        event_row_id="EVENT-1",
    )
    zero_ticket = numeric_router_source_repair_slippage_join_event_from_row(
        {
            "source_repair_plan_row_id": "PLAN-1",
            "input_numeric_router_catalog_entry_id": "CAT-1",
            "input_numeric_router_family_spec_id": "SPEC-1",
            "order_ticket": 0,
            "executed_entry_price": 100.5,
        },
        contract,
        event_row_id="EVENT-ZERO",
    )
    complete = numeric_router_source_repair_slippage_join_event_from_row(
        {
            "source_repair_plan_row_id": "PLAN-1",
            "input_numeric_router_catalog_entry_id": "CAT-1",
            "input_numeric_router_family_spec_id": "SPEC-1",
            "order_ticket": 123,
            "executed_entry_price": 100.5,
        },
        contract,
        event_row_id="EVENT-2",
    )

    assert incomplete["slippage_join_event_status"] == "SOURCE_REPAIR_SLIPPAGE_JOIN_IDENTITY_INCOMPLETE"
    assert incomplete["missing_source_repair_identity_fields"] == [
        "source_repair_plan_row_id",
        "input_numeric_router_catalog_entry_id",
        "input_numeric_router_family_spec_id",
    ]
    assert zero_ticket["slippage_join_event_status"] == "SOURCE_REPAIR_SLIPPAGE_JOIN_IDENTITY_INCOMPLETE"
    assert zero_ticket["captured_order_identity_fields"] == []
    assert complete["slippage_join_event_status"] == "SOURCE_REPAIR_SLIPPAGE_JOIN_IDENTITY_COMPLETE"
    assert complete["captured_order_identity_fields"] == ["order_ticket"]
    assert complete["source_repair_identity_key"] == "PLAN-1|CAT-1|SPEC-1"
    assert complete["missing_slippage_geometry_fields"] == ["deal_ticket"]
    assert complete["exact_r_repaired_by_this_event"] is False


def test_numeric_router_source_repair_slippage_identity_adapter_emits_default_off_payload_only_for_ready_contract():
    ready_contract = {
        "slippage_join_contract_row_id": "JOIN-1",
        "slippage_join_contract_status": "READY_PROSPECTIVE_SLIPPAGE_ROW_IDENTITY_JOIN_CONTRACT",
        "slippage_row_identity_binding_required": True,
        "input_source_repair_plan_row_id": "PLAN-1",
        "input_numeric_router_catalog_entry_id": "CAT-1",
        "input_numeric_router_family_spec_id": "SPEC-1",
        "input_action_rows": 10,
        "required_order_identity_any_of": ["order_ticket", "deal_ticket"],
        "required_slippage_geometry_fields": ["order_ticket", "executed_entry_price"],
    }
    not_applicable_contract = {
        "slippage_join_contract_row_id": "JOIN-2",
        "slippage_join_contract_status": "NOT_SLIPPAGE_JOIN_APPLICABLE_SOURCE_PACKET_REQUIRED",
        "slippage_row_identity_binding_required": False,
        "input_source_repair_plan_row_id": "PLAN-2",
        "input_numeric_router_catalog_entry_id": "CAT-2",
        "input_numeric_router_family_spec_id": "SPEC-2",
        "input_action_rows": 3,
    }

    adapter = numeric_router_source_repair_slippage_identity_adapter_for_contract(
        ready_contract,
        adapter_row_id="ADAPTER-1",
        source_artifact="join_contract.jsonl",
        source_line_no=1,
        source_sha256="join-sha",
    )
    blocked = numeric_router_source_repair_slippage_identity_adapter_for_contract(
        not_applicable_contract,
        adapter_row_id="ADAPTER-2",
        source_artifact="join_contract.jsonl",
        source_line_no=2,
        source_sha256="join-sha",
    )
    summary = summarize_numeric_router_source_repair_slippage_identity_adapters([adapter, blocked])

    assert adapter["slippage_identity_adapter_status"] == "READY_DEFAULT_OFF_SOURCE_REPAIR_IDENTITY_PAYLOAD"
    assert adapter["source_repair_identity_key"] == "PLAN-1|CAT-1|SPEC-1"
    assert adapter["trade_params_source_repair_identity_patch"] == {
        "source_repair_identity": {
            "source_repair_plan_row_id": "PLAN-1",
            "input_numeric_router_catalog_entry_id": "CAT-1",
            "input_numeric_router_family_spec_id": "SPEC-1",
        }
    }
    assert numeric_router_source_repair_slippage_identity_payload_from_adapter(adapter) == {
        "source_repair_plan_row_id": "PLAN-1",
        "input_numeric_router_catalog_entry_id": "CAT-1",
        "input_numeric_router_family_spec_id": "SPEC-1",
    }
    assert blocked["slippage_identity_adapter_status"] == "NOT_APPLICABLE_SOURCE_PACKET_REQUIRED"
    assert blocked["trade_params_source_repair_identity_patch"] is None
    assert numeric_router_source_repair_slippage_identity_payload_from_adapter(blocked) == {}
    assert summary["rows"] == 2
    assert summary["input_action_rows"] == 13
    assert summary["payload_ready_rows"] == 1
    assert summary["trade_params_patch_rows"] == 1
    assert summary["exact_r_repaired_by_this_adapter_rows"] == 0
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def test_numeric_router_source_repair_slippage_selection_event_requires_matching_selected_identity():
    adapter = {
        "slippage_identity_adapter_row_id": "ADAPTER-1",
        "slippage_identity_adapter_status": "READY_DEFAULT_OFF_SOURCE_REPAIR_IDENTITY_PAYLOAD",
        "input_slippage_join_contract_row_id": "JOIN-1",
        "input_source_repair_plan_row_id": "PLAN-1",
        "input_numeric_router_catalog_entry_id": "CAT-1",
        "input_numeric_router_family_spec_id": "SPEC-1",
        "source_repair_identity_key": "PLAN-1|CAT-1|SPEC-1",
        "source_repair_identity_payload": {
            "source_repair_plan_row_id": "PLAN-1",
            "input_numeric_router_catalog_entry_id": "CAT-1",
            "input_numeric_router_family_spec_id": "SPEC-1",
        },
    }

    ready = numeric_router_source_repair_slippage_selection_event_from_adapter(
        adapter,
        {
            "source_repair_plan_row_id": "PLAN-1",
            "input_numeric_router_catalog_entry_id": "CAT-1",
            "input_numeric_router_family_spec_id": "SPEC-1",
        },
        selection_event_row_id="SEL-1",
    )
    mismatch = numeric_router_source_repair_slippage_selection_event_from_adapter(
        adapter,
        {
            "source_repair_plan_row_id": "PLAN-X",
            "input_numeric_router_catalog_entry_id": "CAT-1",
            "input_numeric_router_family_spec_id": "SPEC-1",
        },
        selection_event_row_id="SEL-2",
    )
    not_applicable = numeric_router_source_repair_slippage_selection_event_from_adapter(
        {"slippage_identity_adapter_status": "NOT_APPLICABLE_SOURCE_PACKET_REQUIRED"},
        {},
        selection_event_row_id="SEL-3",
    )
    summary = summarize_numeric_router_source_repair_slippage_selection_events([ready, mismatch, not_applicable])

    assert ready["slippage_selection_event_status"] == "READY_DEFAULT_OFF_TRADE_PARAMS_SOURCE_REPAIR_IDENTITY_PATCH"
    assert ready["trade_params_source_repair_identity_patch"] == {
        "source_repair_identity": {
            "source_repair_plan_row_id": "PLAN-1",
            "input_numeric_router_catalog_entry_id": "CAT-1",
            "input_numeric_router_family_spec_id": "SPEC-1",
        }
    }
    assert mismatch["slippage_selection_event_status"] == "SOURCE_REPAIR_SELECTION_IDENTITY_MISMATCH"
    assert mismatch["trade_params_source_repair_identity_patch"] is None
    assert not_applicable["slippage_selection_event_status"] == (
        "SOURCE_REPAIR_SELECTION_NOT_APPLICABLE_SOURCE_PACKET_REQUIRED"
    )
    assert summary["rows"] == 3
    assert summary["trade_params_patch_rows"] == 1
    assert summary["exact_r_repaired_by_this_selection_event_rows"] == 0
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def test_numeric_router_source_repair_source_packet_trace_proves_packet_exists_without_execution_identity():
    plan = {
        "source_repair_plan_row_id": "PLAN-1",
        "input_numeric_router_catalog_entry_id": "CAT-1",
        "input_numeric_router_family_spec_id": "SPEC-1",
        "source_component": "nofill_far_miss_retest",
        "symbol": "GBPJPY",
        "route_session": "tokyo_kz",
    }
    proof_row = {
        "source_repair_proof_row_id": "PROOF-1",
        "input_numeric_result_row_id": "RESULT-1",
        "input_source_repair_execution_row_id": "EXEC-1",
        "source_component": "nofill_far_miss_retest",
        "source_row_id": "OHLC-GTOS-NOFILL-RETEST-REDESIGN-00001",
        "source_manifest_hash": "manifest-sha",
        "source_repair_system_decision": "SOURCE_JOIN_REPAIR_REQUIRED_WITH_CURRENT_PACKET_ABSENCE_PROOF",
        "exact_missing_field_proof": ["order_ticket", "deal_ticket"],
        "symbol": "GBPJPY",
        "route_session": "tokyo_kz",
    }
    branch_packet = {
        "retest_redesign_branch_id": "OHLC-GTOS-NOFILL-RETEST-REDESIGN-00001",
        "route_candidate_id": "GBPJPY|tokyo_kz|LOWER_WICK_EXHAUSTION|h4",
        "side": "LONG",
        "target_stop_contract_id": "TS-1",
        "m1_source_status": "MT5_M1_BARS_AVAILABLE",
    }
    join_packet = {
        "retest_redesign_branch_id": "OHLC-GTOS-NOFILL-RETEST-REDESIGN-00001",
        "route_candidate_id": "GBPJPY|tokyo_kz|LOWER_WICK_EXHAUSTION|h4",
        "target_stop_result": "TARGET_TOUCH_FIRST_OR_ONLY_M1_PROXY",
        "tick_source_status": "TICK_SOURCE_UNAVAILABLE",
    }

    trace = numeric_router_source_repair_source_packet_trace_for_proof_row(
        plan,
        proof_row,
        trace_row_id="TRACE-1",
        source_artifact="proof.jsonl",
        source_line_no=10,
        source_sha256="proof-sha",
        source_packet_id_field="retest_redesign_branch_id",
        original_packet_row=branch_packet,
        original_packet_source_artifact="branch.jsonl",
        original_packet_source_line_no=1,
        original_packet_source_sha256="branch-sha",
        source_join_packet_row=join_packet,
        source_join_source_artifact="join.jsonl",
        source_join_source_line_no=2,
        source_join_source_sha256="join-sha",
    )
    summary = summarize_numeric_router_source_repair_source_packet_traces([trace])

    assert trace["source_packet_trace_status"] == (
        "SOURCE_PACKET_TRACE_COMPLETE_PACKET_FOUND_EXECUTION_IDENTITY_ABSENT"
    )
    assert trace["original_source_packet_found"] is True
    assert trace["source_join_packet_found"] is True
    assert trace["source_packet_trace_repaired_source_absence_proof"] is True
    assert trace["direct_execution_identity_fields_present"] == []
    assert trace["requires_prospective_execution_identity_capture"] is True
    assert trace["exact_r_repaired_by_this_trace"] is False
    assert trace["runtime_candidate_use_permitted"] is False
    assert summary["rows"] == 1
    assert summary["source_absence_proof_repaired_rows"] == 1
    assert summary["direct_execution_identity_found_rows"] == 0
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def test_numeric_router_source_repair_source_packet_trace_surfaces_missing_packet_and_direct_identity():
    plan = {"source_repair_plan_row_id": "PLAN-1"}
    proof_row = {
        "source_repair_proof_row_id": "PROOF-1",
        "source_row_id": "ROW-1",
        "source_component": "nofill_far_miss_retest",
    }

    missing = numeric_router_source_repair_source_packet_trace_for_proof_row(
        plan,
        proof_row,
        trace_row_id="TRACE-MISSING",
        source_artifact="proof.jsonl",
        source_line_no=1,
        source_sha256="proof-sha",
        source_packet_id_field="retest_redesign_branch_id",
        original_packet_row=None,
        source_join_packet_row=None,
    )
    direct = numeric_router_source_repair_source_packet_trace_for_proof_row(
        plan,
        proof_row,
        trace_row_id="TRACE-DIRECT",
        source_artifact="proof.jsonl",
        source_line_no=2,
        source_sha256="proof-sha",
        source_packet_id_field="retest_redesign_branch_id",
        original_packet_row={"retest_redesign_branch_id": "ROW-1", "order_ticket": 123},
        source_join_packet_row={"retest_redesign_branch_id": "ROW-1"},
    )
    summary = summarize_numeric_router_source_repair_source_packet_traces([missing, direct])

    assert missing["source_packet_trace_status"] == "SOURCE_PACKET_TRACE_ORIGINAL_PACKET_MISSING"
    assert missing["source_packet_trace_repaired_source_absence_proof"] is False
    assert direct["source_packet_trace_status"] == (
        "SOURCE_PACKET_TRACE_PACKET_FOUND_DIRECT_EXECUTION_IDENTITY_PRESENT"
    )
    assert direct["direct_execution_identity_fields_present"] == ["order_ticket"]
    assert summary["source_packet_trace_status_counts"] == {
        "SOURCE_PACKET_TRACE_ORIGINAL_PACKET_MISSING": 1,
        "SOURCE_PACKET_TRACE_PACKET_FOUND_DIRECT_EXECUTION_IDENTITY_PRESENT": 1,
    }
    assert summary["direct_execution_identity_found_rows"] == 1
    assert summary["exact_r_repaired_by_this_trace_rows"] == 0


def test_numeric_router_source_repair_selector_surface_unifies_identity_and_packet_context_rows():
    ready_selection = {
        "slippage_selection_event_row_id": "SEL-1",
        "slippage_selection_event_status": "READY_DEFAULT_OFF_TRADE_PARAMS_SOURCE_REPAIR_IDENTITY_PATCH",
        "input_slippage_identity_adapter_row_id": "ADAPTER-1",
        "input_slippage_join_contract_row_id": "JOIN-1",
        "input_source_repair_plan_row_id": "PLAN-1",
        "input_numeric_router_catalog_entry_id": "CAT-1",
        "input_numeric_router_family_spec_id": "SPEC-1",
        "trade_params_source_repair_identity_patch": {
            "source_repair_identity": {
                "source_repair_plan_row_id": "PLAN-1",
                "input_numeric_router_catalog_entry_id": "CAT-1",
                "input_numeric_router_family_spec_id": "SPEC-1",
            }
        },
    }
    ready_adapter = {
        "slippage_identity_adapter_status": "READY_DEFAULT_OFF_SOURCE_REPAIR_IDENTITY_PAYLOAD",
        "input_action_rows": 10,
    }
    packet_selection = {
        "slippage_selection_event_row_id": "SEL-2",
        "slippage_selection_event_status": "SOURCE_REPAIR_SELECTION_NOT_APPLICABLE_SOURCE_PACKET_REQUIRED",
        "input_slippage_identity_adapter_row_id": "ADAPTER-2",
        "input_source_repair_plan_row_id": "PLAN-2",
        "input_numeric_router_catalog_entry_id": "CAT-2",
        "input_numeric_router_family_spec_id": "SPEC-2",
    }
    packet_summary = {
        "source_packet_trace_plan_status": "SOURCE_PACKET_TRACE_PLAN_COMPLETE_EXECUTION_IDENTITY_ABSENT",
        "input_action_rows": 3,
        "trace_rows": 3,
        "source_component": "nofill_far_miss_retest",
        "symbol": "GBPJPY",
        "route_session": "tokyo_kz",
        "source_packet_id_field": "retest_redesign_branch_id",
        "original_source_packet_artifact": "branch.jsonl",
        "source_join_packet_artifact": "join.jsonl",
        "direct_execution_identity_found_rows": 0,
    }

    ready = numeric_router_source_repair_selector_surface_for_selection_event(
        ready_selection,
        ready_adapter,
        None,
        selector_row_id="SURFACE-1",
        source_artifact="selection.jsonl",
        source_line_no=1,
        source_sha256="selection-sha",
    )
    packet = numeric_router_source_repair_selector_surface_for_selection_event(
        packet_selection,
        None,
        packet_summary,
        selector_row_id="SURFACE-2",
        source_artifact="selection.jsonl",
        source_line_no=2,
        source_sha256="selection-sha",
    )
    summary = summarize_numeric_router_source_repair_selector_surfaces([ready, packet])

    assert ready["source_repair_selector_surface_status"] == (
        "READY_DEFAULT_OFF_SOURCE_REPAIR_EXECUTION_IDENTITY_SELECTOR"
    )
    assert ready["trade_params_source_repair_identity_patch"] == ready_selection[
        "trade_params_source_repair_identity_patch"
    ]
    assert ready["source_packet_context_payload"] is None
    assert packet["source_repair_selector_surface_status"] == (
        "READY_DEFAULT_OFF_SOURCE_PACKET_CONTEXT_SELECTOR_EXECUTION_IDENTITY_ABSENT"
    )
    assert packet["trade_params_source_repair_identity_patch"] is None
    assert packet["source_packet_context_payload"]["source_packet_id_field"] == "retest_redesign_branch_id"
    assert packet["requires_prospective_execution_identity_capture"] is True
    assert summary["rows"] == 2
    assert summary["input_action_rows"] == 13
    assert summary["trade_params_source_repair_identity_patch_rows"] == 1
    assert summary["trade_params_source_repair_identity_patch_input_action_rows"] == 10
    assert summary["source_packet_context_payload_rows"] == 1
    assert summary["source_packet_context_payload_input_action_rows"] == 3
    assert summary["exact_r_repaired_by_this_selector_rows"] == 0
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def test_numeric_router_source_repair_selector_surface_keeps_packet_rows_not_ready_without_trace_summary():
    selection = {
        "slippage_selection_event_row_id": "SEL-1",
        "slippage_selection_event_status": "SOURCE_REPAIR_SELECTION_NOT_APPLICABLE_SOURCE_PACKET_REQUIRED",
        "input_source_repair_plan_row_id": "PLAN-1",
    }

    surface = numeric_router_source_repair_selector_surface_for_selection_event(
        selection,
        None,
        None,
        selector_row_id="SURFACE-1",
        source_artifact="selection.jsonl",
        source_line_no=1,
        source_sha256="selection-sha",
    )

    assert surface["source_repair_selector_surface_status"] == (
        "SOURCE_REPAIR_SELECTOR_SOURCE_PACKET_CONTEXT_MISSING"
    )
    assert surface["source_packet_context_payload"] is None
    assert surface["trade_params_source_repair_identity_patch"] is None
    assert surface["runtime_candidate_use_permitted"] is False


def test_numeric_router_source_repair_selector_event_builds_catalog_routable_event():
    catalog_entry = {
        "numeric_router_catalog_entry_id": "CAT-1",
        "input_numeric_router_family_spec_id": "SPEC-1",
        "catalog_type": "source_repair_queue_entry",
        "catalog_priority_bucket": "P0_SOURCE_REPAIR_EXACT_R_GEOMETRY",
        "catalog_priority_rank": 0,
        "numeric_router_action": "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R",
        "implementation_target": "source_repair_queue_catalog",
        "symbol": "XAUUSD",
        "route_session": "ny_core",
        "source_component": "nofill_far_miss_retest",
        "repair_action": "join_or_reconstruct_broker_execution_geometry_fields",
        "missing_field_count": "12",
        "input_action_rows": 7,
    }
    selector_surface = {
        "source_repair_selector_surface_row_id": "SURFACE-1",
        "source_repair_selector_surface_status": "READY_DEFAULT_OFF_SOURCE_REPAIR_EXECUTION_IDENTITY_SELECTOR",
        "source_repair_selector_payload_type": "trade_params_source_repair_identity",
        "input_source_repair_plan_row_id": "PLAN-1",
        "input_numeric_router_catalog_entry_id": "CAT-1",
        "input_numeric_router_family_spec_id": "SPEC-1",
        "input_action_rows": 7,
        "trade_params_source_repair_identity_patch": {
            "source_repair_identity": {
                "source_repair_plan_row_id": "PLAN-1",
                "input_numeric_router_catalog_entry_id": "CAT-1",
                "input_numeric_router_family_spec_id": "SPEC-1",
            }
        },
    }

    event = numeric_router_source_repair_selector_event_from_surface(
        selector_surface,
        catalog_entry,
        event_row_id="EVENT-1",
        source_artifact="selector.jsonl",
        source_line_no=1,
        source_sha256="selector-sha",
    )
    summary = summarize_numeric_router_source_repair_selector_events([event])

    assert event["source_repair_selector_event_status"] == (
        "SOURCE_REPAIR_SELECTOR_EVENT_READY_FOR_DEFAULT_OFF_ROUTER"
    )
    assert event["source_repair_selector_event_routable"] is True
    assert event["symbol"] == "XAUUSD"
    assert event["repair_action"] == "join_or_reconstruct_broker_execution_geometry_fields"
    assert event["catalog_entry_id_match"] is True
    assert event["default_catalog_evaluation_would_skip_source_repair"] is True
    assert summary["event_routable_rows"] == 1
    assert summary["event_routable_input_action_rows"] == 7
    assert summary["exact_r_repaired_by_this_event_rows"] == 0
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def test_numeric_router_source_repair_selector_route_requires_include_source_repair():
    entries = [
        {
            "numeric_router_catalog_entry_id": "CAT-1",
            "input_numeric_router_family_spec_id": "SPEC-1",
            "catalog_type": "source_repair_queue_entry",
            "catalog_priority_bucket": "P0_SOURCE_REPAIR_EXACT_R_GEOMETRY",
            "catalog_priority_rank": 0,
            "numeric_router_action": "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R",
            "implementation_target": "source_repair_queue_catalog",
            "symbol": "XAUUSD",
            "route_session": "ny_core",
            "source_component": "nofill_far_miss_retest",
            "repair_action": "join_or_reconstruct_broker_execution_geometry_fields",
            "missing_field_count": "12",
            "input_action_rows": 7,
        }
    ]
    catalog = NumericRouterImplementationCatalog(entries)
    selector_surface = {
        "source_repair_selector_surface_row_id": "SURFACE-1",
        "source_repair_selector_surface_status": "READY_DEFAULT_OFF_SOURCE_REPAIR_EXECUTION_IDENTITY_SELECTOR",
        "source_repair_selector_payload_type": "trade_params_source_repair_identity",
        "input_source_repair_plan_row_id": "PLAN-1",
        "input_numeric_router_catalog_entry_id": "CAT-1",
        "input_numeric_router_family_spec_id": "SPEC-1",
        "input_action_rows": 7,
        "trade_params_source_repair_identity_patch": {
            "source_repair_identity": {
                "source_repair_plan_row_id": "PLAN-1",
                "input_numeric_router_catalog_entry_id": "CAT-1",
                "input_numeric_router_family_spec_id": "SPEC-1",
            }
        },
    }
    event = numeric_router_source_repair_selector_event_from_surface(
        selector_surface,
        entries[0],
        event_row_id="EVENT-1",
        source_artifact="selector.jsonl",
        source_line_no=1,
        source_sha256="selector-sha",
    )
    default_matches = catalog.evaluate_event(event)
    source_repair_matches = catalog.evaluate_event(event, include_source_repair=True)
    route = numeric_router_source_repair_selector_route_for_event(
        event,
        source_repair_matches,
        route_row_id="ROUTE-1",
        source_artifact="event.jsonl",
        source_line_no=1,
        source_sha256="event-sha",
    )
    summary = summarize_numeric_router_source_repair_selector_routes([route])

    assert default_matches == []
    assert len(source_repair_matches) == 1
    assert route["source_repair_selector_route_status"] == (
        "ROUTED_DEFAULT_OFF_SOURCE_REPAIR_IDENTITY_SELECTOR_TO_QUEUE"
    )
    assert route["router_path_ready_default_off"] is True
    assert route["trade_params_source_repair_identity_patch"] == selector_surface[
        "trade_params_source_repair_identity_patch"
    ]
    assert route["expected_catalog_entry_match_count"] == 1
    assert route["catalog_evaluation_include_source_repair"] is True
    assert route["default_catalog_evaluation_would_skip_source_repair"] is True
    assert summary["router_path_ready_default_off_rows"] == 1
    assert summary["trade_params_source_repair_identity_patch_input_action_rows"] == 7
    assert summary["exact_r_repaired_by_this_route_rows"] == 0
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def test_numeric_router_source_repair_selector_route_preserves_packet_context_capture_boundary():
    catalog_entry = {
        "numeric_router_catalog_entry_id": "CAT-1",
        "input_numeric_router_family_spec_id": "SPEC-1",
        "catalog_type": "source_repair_queue_entry",
        "catalog_priority_bucket": "P0_SOURCE_REPAIR_JOIN_ABSENCE_PROOF",
        "catalog_priority_rank": 0,
        "numeric_router_action": "SOURCE_JOIN_REPAIR_REQUIRED_WITH_CURRENT_PACKET_ABSENCE_PROOF",
        "implementation_target": "source_repair_queue_catalog",
        "symbol": "GBPJPY",
        "route_session": "tokyo_kz",
        "source_component": "nofill_far_miss_retest",
        "repair_action": "acquire_or_rebuild_missing_source_join_before_exact_r",
        "missing_field_count": "12",
        "input_action_rows": 3,
    }
    selector_surface = {
        "source_repair_selector_surface_row_id": "SURFACE-1",
        "source_repair_selector_surface_status": (
            "READY_DEFAULT_OFF_SOURCE_PACKET_CONTEXT_SELECTOR_EXECUTION_IDENTITY_ABSENT"
        ),
        "source_repair_selector_payload_type": "source_packet_context_without_execution_identity",
        "input_source_repair_plan_row_id": "PLAN-1",
        "input_numeric_router_catalog_entry_id": "CAT-1",
        "input_numeric_router_family_spec_id": "SPEC-1",
        "input_action_rows": 3,
        "source_packet_context_payload": {
            "source_component": "nofill_far_miss_retest",
            "symbol": "GBPJPY",
            "route_session": "tokyo_kz",
            "direct_execution_identity_found_rows": 0,
        },
        "requires_prospective_execution_identity_capture": True,
    }
    event = numeric_router_source_repair_selector_event_from_surface(
        selector_surface,
        catalog_entry,
        event_row_id="EVENT-1",
        source_artifact="selector.jsonl",
        source_line_no=1,
        source_sha256="selector-sha",
    )
    matches = NumericRouterImplementationCatalog([catalog_entry]).evaluate_event(event, include_source_repair=True)
    route = numeric_router_source_repair_selector_route_for_event(
        event,
        matches,
        route_row_id="ROUTE-1",
        source_artifact="event.jsonl",
        source_line_no=1,
        source_sha256="event-sha",
    )
    summary = summarize_numeric_router_source_repair_selector_routes([route])

    assert event["source_repair_selector_event_status"] == (
        "SOURCE_REPAIR_SELECTOR_EVENT_PACKET_CONTEXT_READY_FOR_PROSPECTIVE_CAPTURE_ROUTER"
    )
    assert route["source_repair_selector_route_status"] == (
        "ROUTED_SOURCE_PACKET_CONTEXT_SELECTOR_TO_PROSPECTIVE_EXECUTION_IDENTITY_CAPTURE_QUEUE"
    )
    assert route["source_packet_context_payload"]["direct_execution_identity_found_rows"] == 0
    assert route["trade_params_source_repair_identity_patch"] is None
    assert route["requires_prospective_execution_identity_capture"] is True
    assert summary["source_packet_context_payload_rows"] == 1
    assert summary["requires_prospective_execution_identity_capture_input_action_rows"] == 3
    assert summary["slippage_join_repaired_by_this_route_rows"] == 0
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def _all_source_repair_capture_patch_rows() -> list[dict[str, str]]:
    fields = [
        "broker_fill_time_utc",
        "commission",
        "deal_ticket",
        "executed_entry_price",
        "executed_exit_price",
        "executed_lot_size",
        "executed_stop_price",
        "executed_target_price",
        "order_ticket",
        "partial_exit_lifecycle",
        "slippage_price",
        "swap",
    ]
    return [
        {
            "slippage_capture_patch_row_id": f"PATCH-{index:04d}",
            "missing_field": field,
            "prospective_capture_status": "PROSPECTIVE_SLIPPAGE_CAPTURE_SCHEMA_PRESENT_WITH_STATUS_GUARDS",
        }
        for index, field in enumerate(fields, start=1)
    ]


def test_numeric_router_source_repair_execution_identity_contract_binds_identity_route_to_capture_schema():
    route = {
        "source_repair_selector_route_row_id": "ROUTE-1",
        "source_repair_selector_route_status": "ROUTED_DEFAULT_OFF_SOURCE_REPAIR_IDENTITY_SELECTOR_TO_QUEUE",
        "input_source_repair_selector_event_row_id": "EVENT-1",
        "input_source_repair_selector_surface_row_id": "SURFACE-1",
        "input_source_repair_plan_row_id": "PLAN-1",
        "input_numeric_router_catalog_entry_id": "CAT-1",
        "input_numeric_router_family_spec_id": "SPEC-1",
        "router_path_ready_default_off": True,
        "source_repair_queue_match_count": 1,
        "expected_catalog_entry_match_count": 1,
        "input_action_rows": 9,
        "trade_params_source_repair_identity_patch": {
            "source_repair_identity": {
                "source_repair_plan_row_id": "PLAN-1",
                "input_numeric_router_catalog_entry_id": "CAT-1",
                "input_numeric_router_family_spec_id": "SPEC-1",
            }
        },
    }
    catalog_entry = {
        "symbol": "XAUUSD",
        "route_session": "ny_core",
        "horizon_id": "h16",
        "source_component": "nofill_far_miss_retest",
        "repair_action": "join_or_reconstruct_broker_execution_geometry_fields",
        "numeric_router_action": "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R",
        "catalog_priority_bucket": "P0_SOURCE_REPAIR_EXACT_R_GEOMETRY",
    }

    contract = numeric_router_source_repair_execution_identity_capture_contract_for_route(
        route,
        _all_source_repair_capture_patch_rows(),
        contract_row_id="CONTRACT-1",
        source_artifact="routes.jsonl",
        source_line_no=1,
        source_sha256="routes-sha",
        source_repair_queue_entry=catalog_entry,
    )
    summary = summarize_numeric_router_source_repair_execution_identity_capture_contracts([contract])

    assert contract["execution_identity_capture_contract_status"] == (
        "READY_DEFAULT_OFF_EXECUTION_IDENTITY_CAPTURE_CONTRACT_WITH_SOURCE_REPAIR_IDENTITY"
    )
    assert contract["source_repair_queue_route_bound"] is True
    assert contract["row_identity_bound_to_numeric_router_source_repair_queue"] is True
    assert contract["capture_patch_field_count"] == 12
    assert contract["source_repair_identity_key"] == "PLAN-1|CAT-1|SPEC-1"
    assert contract["required_order_identity_any_of"] == ["order_ticket", "deal_ticket"]
    assert contract["requires_execution_capture_row_for_exact_r"] is True
    assert contract["exact_r_repaired_by_this_contract"] is False
    assert contract["runtime_candidate_use_permitted"] is False
    assert summary["trade_params_source_repair_identity_patch_rows"] == 1
    assert summary["row_identity_bound_to_numeric_router_source_repair_queue_rows"] == 1
    assert summary["requires_execution_capture_row_for_exact_r_rows"] == 1
    assert summary["exact_r_repaired_by_this_contract_rows"] == 0


def test_numeric_router_source_repair_execution_identity_contract_preserves_packet_context_gap():
    route = {
        "source_repair_selector_route_row_id": "ROUTE-1",
        "source_repair_selector_route_status": (
            "ROUTED_SOURCE_PACKET_CONTEXT_SELECTOR_TO_PROSPECTIVE_EXECUTION_IDENTITY_CAPTURE_QUEUE"
        ),
        "input_source_repair_selector_event_row_id": "EVENT-1",
        "input_source_repair_selector_surface_row_id": "SURFACE-1",
        "input_source_repair_plan_row_id": "PLAN-1",
        "input_numeric_router_catalog_entry_id": "CAT-1",
        "input_numeric_router_family_spec_id": "SPEC-1",
        "router_path_ready_default_off": True,
        "source_repair_queue_match_count": 1,
        "expected_catalog_entry_match_count": 1,
        "input_action_rows": 3,
        "requires_prospective_execution_identity_capture": True,
        "source_packet_context_payload": {
            "symbol": "GBPJPY",
            "route_session": "tokyo_kz",
            "source_component": "nofill_far_miss_retest",
            "direct_execution_identity_found_rows": 0,
        },
    }

    contract = numeric_router_source_repair_execution_identity_capture_contract_for_route(
        route,
        _all_source_repair_capture_patch_rows(),
        contract_row_id="CONTRACT-1",
        source_artifact="routes.jsonl",
        source_line_no=1,
        source_sha256="routes-sha",
    )
    summary = summarize_numeric_router_source_repair_execution_identity_capture_contracts([contract])

    assert contract["execution_identity_capture_contract_status"] == (
        "READY_DEFAULT_OFF_PACKET_CONTEXT_CAPTURE_CONTRACT_EXECUTION_IDENTITY_ABSENT"
    )
    assert contract["source_repair_identity_key"] == ""
    assert contract["trade_params_source_repair_identity_patch"] is None
    assert contract["source_packet_context_payload"]["direct_execution_identity_found_rows"] == 0
    assert contract["source_packet_route_requires_prospective_execution_identity_capture"] is True
    assert contract["requires_execution_capture_row_for_exact_r"] is True
    assert summary["source_packet_context_payload_rows"] == 1
    assert summary["source_packet_route_requires_prospective_execution_identity_capture_rows"] == 1
    assert summary["trade_params_source_repair_identity_patch_rows"] == 0
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def test_numeric_router_source_repair_execution_identity_contract_marks_missing_capture_schema_fields():
    route = {
        "source_repair_selector_route_row_id": "ROUTE-1",
        "source_repair_selector_route_status": "ROUTED_DEFAULT_OFF_SOURCE_REPAIR_IDENTITY_SELECTOR_TO_QUEUE",
        "input_source_repair_plan_row_id": "PLAN-1",
        "input_numeric_router_catalog_entry_id": "CAT-1",
        "input_numeric_router_family_spec_id": "SPEC-1",
        "router_path_ready_default_off": True,
        "source_repair_queue_match_count": 1,
        "expected_catalog_entry_match_count": 1,
        "input_action_rows": 9,
        "trade_params_source_repair_identity_patch": {
            "source_repair_identity": {
                "source_repair_plan_row_id": "PLAN-1",
                "input_numeric_router_catalog_entry_id": "CAT-1",
                "input_numeric_router_family_spec_id": "SPEC-1",
            }
        },
    }

    contract = numeric_router_source_repair_execution_identity_capture_contract_for_route(
        route,
        [{"slippage_capture_patch_row_id": "PATCH-0001", "missing_field": "order_ticket"}],
        contract_row_id="CONTRACT-1",
        source_artifact="routes.jsonl",
        source_line_no=1,
        source_sha256="routes-sha",
    )
    summary = summarize_numeric_router_source_repair_execution_identity_capture_contracts([contract])

    assert contract["execution_identity_capture_contract_status"] == (
        "EXECUTION_IDENTITY_CAPTURE_CONTRACT_MISSING_CAPTURE_SCHEMA_FIELDS"
    )
    assert contract["capture_patch_fields_bound_to_route"] is False
    assert "deal_ticket" in contract["missing_capture_schema_fields"]
    assert contract["requires_execution_capture_row_for_exact_r"] is False
    assert summary["missing_capture_schema_field_rows"] == 1
    assert summary["requires_execution_capture_row_for_exact_r_rows"] == 0


def test_numeric_router_source_repair_execution_identity_event_completes_with_matching_slippage_row():
    contract = {
        "execution_identity_capture_contract_row_id": "CONTRACT-1",
        "execution_identity_capture_contract_status": (
            "READY_DEFAULT_OFF_EXECUTION_IDENTITY_CAPTURE_CONTRACT_WITH_SOURCE_REPAIR_IDENTITY"
        ),
        "input_source_repair_selector_route_row_id": "ROUTE-1",
        "input_source_repair_plan_row_id": "PLAN-1",
        "input_numeric_router_catalog_entry_id": "CAT-1",
        "input_numeric_router_family_spec_id": "SPEC-1",
        "source_repair_identity_key": "PLAN-1|CAT-1|SPEC-1",
        "required_source_repair_identity_fields": [
            "source_repair_plan_row_id",
            "input_numeric_router_catalog_entry_id",
            "input_numeric_router_family_spec_id",
        ],
        "required_order_identity_any_of": ["order_ticket", "deal_ticket"],
        "required_execution_geometry_fields": [
            "broker_fill_time_utc",
            "commission",
            "deal_ticket",
            "executed_entry_price",
            "executed_exit_price",
            "executed_lot_size",
            "executed_stop_price",
            "executed_target_price",
            "order_ticket",
            "partial_exit_lifecycle",
            "slippage_price",
            "swap",
        ],
    }
    slippage_row = {
        "source_repair_plan_row_id": "PLAN-1",
        "input_numeric_router_catalog_entry_id": "CAT-1",
        "input_numeric_router_family_spec_id": "SPEC-1",
        "source_repair_identity_key": "PLAN-1|CAT-1|SPEC-1",
        "order_ticket": 123,
        "deal_ticket": 456,
        "broker_fill_time_utc": "2026-05-18T00:00:00+00:00",
        "commission": 0.0,
        "executed_entry_price": 2400.0,
        "executed_exit_price": 2403.0,
        "executed_lot_size": 1.0,
        "executed_stop_price": 2397.0,
        "executed_target_price": 2406.0,
        "partial_exit_lifecycle": "FULL_EXIT",
        "slippage_price": 0.01,
        "swap": 0.0,
        "symbol": "XAUUSD",
    }

    event = numeric_router_source_repair_execution_identity_capture_event_from_slippage_row(
        contract,
        slippage_row,
        event_row_id="EVENT-1",
        source_artifact="contracts.jsonl",
        source_line_no=1,
        source_sha256="contract-sha",
        slippage_source_artifact="slippage.jsonl",
        slippage_source_line_no=1,
        slippage_source_sha256="slippage-sha",
    )
    summary = summarize_numeric_router_source_repair_execution_identity_capture_events([event])

    assert event["execution_identity_capture_event_status"] == "EXECUTION_IDENTITY_CAPTURE_EVENT_CONTRACT_COMPLETE"
    assert event["slippage_row_bound_to_contract"] is True
    assert event["slippage_join_repaired_by_this_event"] is True
    assert event["exact_r_repaired_by_this_event"] is False
    assert summary["contract_complete_event_rows"] == 1
    assert summary["slippage_row_bound_to_contract_rows"] == 1
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def test_numeric_router_source_repair_execution_identity_event_marks_missing_current_slippage_identity():
    contract = {
        "execution_identity_capture_contract_row_id": "CONTRACT-1",
        "execution_identity_capture_contract_status": (
            "READY_DEFAULT_OFF_EXECUTION_IDENTITY_CAPTURE_CONTRACT_WITH_SOURCE_REPAIR_IDENTITY"
        ),
        "source_repair_identity_key": "PLAN-1|CAT-1|SPEC-1",
        "required_source_repair_identity_fields": [
            "source_repair_plan_row_id",
            "input_numeric_router_catalog_entry_id",
            "input_numeric_router_family_spec_id",
        ],
        "required_order_identity_any_of": ["order_ticket", "deal_ticket"],
        "required_execution_geometry_fields": ["order_ticket", "deal_ticket", "slippage_price"],
    }
    event = numeric_router_source_repair_execution_identity_capture_event_from_slippage_row(
        contract,
        {"ticket": 123, "symbol": "XAUUSD", "slippage_price": 0.01},
        event_row_id="EVENT-1",
        source_artifact="contracts.jsonl",
        source_line_no=1,
        source_sha256="contract-sha",
        slippage_source_artifact="slippage.jsonl",
        slippage_source_line_no=1,
        slippage_source_sha256="slippage-sha",
    )
    summary = summarize_numeric_router_source_repair_execution_identity_capture_events([event])

    assert event["execution_identity_capture_event_status"] == (
        "EXECUTION_IDENTITY_CAPTURE_EVENT_SOURCE_REPAIR_IDENTITY_MISSING"
    )
    assert event["slippage_row_bound_to_contract"] is False
    assert "source_repair_plan_row_id" in event["missing_source_repair_identity_fields"]
    assert summary["missing_source_repair_identity_event_rows"] == 1
    assert summary["slippage_join_repaired_by_this_event_rows"] == 0


def test_numeric_router_source_repair_execution_identity_event_preserves_packet_context_absence():
    contract = {
        "execution_identity_capture_contract_row_id": "CONTRACT-1",
        "execution_identity_capture_contract_status": (
            "READY_DEFAULT_OFF_PACKET_CONTEXT_CAPTURE_CONTRACT_EXECUTION_IDENTITY_ABSENT"
        ),
        "required_source_repair_identity_fields": [
            "source_repair_plan_row_id",
            "input_numeric_router_catalog_entry_id",
            "input_numeric_router_family_spec_id",
        ],
        "required_order_identity_any_of": ["order_ticket", "deal_ticket"],
        "required_execution_geometry_fields": ["order_ticket", "deal_ticket", "slippage_price"],
    }
    event = numeric_router_source_repair_execution_identity_capture_event_from_slippage_row(
        contract,
        {"ticket": 123, "symbol": "GBPJPY", "slippage_price": 0.01},
        event_row_id="EVENT-1",
        source_artifact="contracts.jsonl",
        source_line_no=1,
        source_sha256="contract-sha",
        slippage_source_artifact="slippage.jsonl",
        slippage_source_line_no=1,
        slippage_source_sha256="slippage-sha",
    )
    summary = summarize_numeric_router_source_repair_execution_identity_capture_events([event])

    assert event["execution_identity_capture_event_status"] == (
        "EXECUTION_IDENTITY_CAPTURE_EVENT_PACKET_CONTEXT_EXECUTION_IDENTITY_ABSENT"
    )
    assert event["slippage_row_bound_to_contract"] is False
    assert summary["packet_context_execution_identity_absent_event_rows"] == 1
    assert summary["slippage_join_repaired_by_this_event_rows"] == 0


def _complete_future_execution_values() -> dict:
    return {
        "order_ticket": 123,
        "deal_ticket": 456,
        "broker_fill_time_utc": "2026-05-18T00:00:00+00:00",
        "commission": 0.0,
        "executed_entry_price": 2400.0,
        "executed_exit_price": 2403.0,
        "executed_lot_size": 0.1,
        "executed_stop_price": 2397.0,
        "executed_target_price": 2406.0,
        "partial_exit_lifecycle": "FULL_EXIT",
        "slippage_price": 0.01,
        "swap": 0.0,
    }


def _ready_execution_identity_contract() -> dict:
    return {
        "execution_identity_capture_contract_row_id": "CONTRACT-1",
        "execution_identity_capture_contract_status": (
            "READY_DEFAULT_OFF_EXECUTION_IDENTITY_CAPTURE_CONTRACT_WITH_SOURCE_REPAIR_IDENTITY"
        ),
        "input_source_repair_selector_route_row_id": "ROUTE-1",
        "input_source_repair_plan_row_id": "PLAN-1",
        "input_numeric_router_catalog_entry_id": "CAT-1",
        "input_numeric_router_family_spec_id": "SPEC-1",
        "input_action_rows": 5,
        "source_repair_identity_key": "PLAN-1|CAT-1|SPEC-1",
        "source_repair_identity_payload": {
            "source_repair_plan_row_id": "PLAN-1",
            "input_numeric_router_catalog_entry_id": "CAT-1",
            "input_numeric_router_family_spec_id": "SPEC-1",
        },
        "required_source_repair_identity_fields": [
            "source_repair_plan_row_id",
            "input_numeric_router_catalog_entry_id",
            "input_numeric_router_family_spec_id",
        ],
        "required_order_identity_any_of": ["order_ticket", "deal_ticket"],
        "required_execution_geometry_fields": [
            "broker_fill_time_utc",
            "commission",
            "deal_ticket",
            "executed_entry_price",
            "executed_exit_price",
            "executed_lot_size",
            "executed_stop_price",
            "executed_target_price",
            "order_ticket",
            "partial_exit_lifecycle",
            "slippage_price",
            "swap",
        ],
    }


def test_numeric_router_future_slippage_lifecycle_emitter_builds_contract_complete_payload():
    event = numeric_router_source_repair_future_slippage_lifecycle_emitter_event_from_contract(
        _ready_execution_identity_contract(),
        _complete_future_execution_values(),
        event_row_id="EMITTER-1",
        source_artifact="contracts.jsonl",
        source_line_no=1,
        source_sha256="contract-sha",
    )
    summary = summarize_numeric_router_source_repair_future_slippage_lifecycle_emitter_events([event])

    assert event["future_slippage_lifecycle_emitter_status"] == (
        "READY_DEFAULT_OFF_FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_CONTRACT_COMPLETE"
    )
    assert event["future_execution_identity_capture_event_status_if_emitted"] == (
        "EXECUTION_IDENTITY_CAPTURE_EVENT_CONTRACT_COMPLETE"
    )
    assert event["source_repair_identity_written_to_future_entry_payload"] is True
    assert event["future_close_payload_joinable_by_order_ticket"] is True
    assert event["future_slippage_row_bound_to_contract_if_emitted"] is True
    assert event["future_entry_slippage_row_payload"]["source_repair_identity_key"] == "PLAN-1|CAT-1|SPEC-1"
    assert event["future_close_slippage_row_payload"]["executed_exit_price"] == 2403.0
    assert event["future_merged_lifecycle_execution_identity_payload"]["executed_target_price"] == 2406.0
    assert event["slippage_join_repaired_by_this_emitter"] is False
    assert event["exact_r_repaired_by_this_emitter"] is False
    assert summary["future_contract_complete_if_emitted_rows"] == 1
    assert summary["source_repair_identity_written_to_future_entry_payload_rows"] == 1
    assert summary["future_close_payload_joinable_by_order_ticket_rows"] == 1
    assert summary["slippage_join_repaired_by_this_emitter_rows"] == 0
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def test_numeric_router_future_slippage_lifecycle_emitter_marks_missing_geometry():
    execution_values = _complete_future_execution_values()
    execution_values.pop("commission")
    event = numeric_router_source_repair_future_slippage_lifecycle_emitter_event_from_contract(
        _ready_execution_identity_contract(),
        execution_values,
        event_row_id="EMITTER-1",
        source_artifact="contracts.jsonl",
        source_line_no=1,
        source_sha256="contract-sha",
    )
    summary = summarize_numeric_router_source_repair_future_slippage_lifecycle_emitter_events([event])

    assert event["future_slippage_lifecycle_emitter_status"] == (
        "FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_EXECUTION_GEOMETRY_INCOMPLETE"
    )
    assert "commission" in event["missing_execution_geometry_fields"]
    assert event["future_entry_slippage_row_payload"] is None
    assert event["future_close_slippage_row_payload"] is None
    assert summary["execution_geometry_incomplete_rows"] == 1
    assert summary["future_contract_complete_if_emitted_rows"] == 0


def test_numeric_router_future_slippage_lifecycle_emitter_preserves_packet_context_absence():
    contract = _ready_execution_identity_contract()
    contract["execution_identity_capture_contract_status"] = (
        "READY_DEFAULT_OFF_PACKET_CONTEXT_CAPTURE_CONTRACT_EXECUTION_IDENTITY_ABSENT"
    )
    contract["source_repair_identity_key"] = ""
    contract["source_repair_identity_payload"] = None

    event = numeric_router_source_repair_future_slippage_lifecycle_emitter_event_from_contract(
        contract,
        _complete_future_execution_values(),
        event_row_id="EMITTER-1",
        source_artifact="contracts.jsonl",
        source_line_no=1,
        source_sha256="contract-sha",
    )
    summary = summarize_numeric_router_source_repair_future_slippage_lifecycle_emitter_events([event])

    assert event["future_slippage_lifecycle_emitter_status"] == (
        "FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_PACKET_CONTEXT_EXECUTION_IDENTITY_ABSENT"
    )
    assert event["source_repair_identity_written_to_future_entry_payload"] is False
    assert event["future_slippage_row_bound_to_contract_if_emitted"] is False
    assert summary["packet_context_execution_identity_absent_rows"] == 1
    assert summary["future_entry_slippage_row_payload_rows"] == 0


def _complete_slippage_lifecycle_pair() -> dict:
    return {
        "slippage_lifecycle_pair_id": "PAIR-1",
        "ticket": "123",
        "entry_slippage_row": {
            "_source_line_no": 10,
            "ticket": 123,
            "slippage_event_type": "entry",
            "source_repair_plan_row_id": "PLAN-1",
            "input_numeric_router_catalog_entry_id": "CAT-1",
            "input_numeric_router_family_spec_id": "SPEC-1",
            "source_repair_identity_key": "PLAN-1|CAT-1|SPEC-1",
            "order_ticket": 123,
            "deal_ticket": 456,
            "broker_fill_time_utc": "2026-05-18T00:00:00+00:00",
            "executed_entry_price": 2400.0,
            "executed_stop_price": 2397.0,
            "executed_target_price": 2406.0,
            "executed_lot_size": 0.1,
            "slippage_price": 0.01,
        },
        "close_slippage_row": {
            "_source_line_no": 11,
            "ticket": 123,
            "slippage_event_type": "close",
            "order_ticket": 789,
            "deal_ticket": 456,
            "broker_fill_time_utc": "2026-05-18T01:00:00+00:00",
            "commission": -0.7,
            "executed_entry_price": 2400.0,
            "executed_exit_price": 2403.0,
            "executed_lot_size": 0.1,
            "executed_stop_price": 2397.0,
            "executed_target_price": 2406.0,
            "partial_exit_lifecycle": "FULL_EXIT",
            "slippage_price": -0.01,
            "swap": 0.0,
        },
    }


def test_numeric_router_slippage_lifecycle_pairs_match_entry_and_close_by_ticket():
    pairs = numeric_router_source_repair_slippage_lifecycle_pairs(
        [
            {"ticket": 1, "trigger": "limit_fill", "symbol": "XAUUSD"},
            {"ticket": 1, "slippage_event_type": "close", "symbol": "XAUUSD"},
            {"ticket": 2, "slippage_event_type": "close", "symbol": "XAUUSD"},
        ]
    )

    assert len(pairs) == 1
    assert pairs[0]["ticket"] == "1"
    assert pairs[0]["entry_slippage_row"]["trigger"] == "limit_fill"
    assert pairs[0]["close_slippage_row"]["slippage_event_type"] == "close"


def test_numeric_router_slippage_lifecycle_join_completes_from_entry_identity_and_close_geometry():
    event = numeric_router_source_repair_execution_identity_lifecycle_join_event_from_pair(
        _ready_execution_identity_contract(),
        _complete_slippage_lifecycle_pair(),
        event_row_id="LIFE-1",
        source_artifact="contracts.jsonl",
        source_line_no=1,
        source_sha256="contract-sha",
        slippage_source_artifact="slippage.jsonl",
        slippage_source_sha256="slippage-sha",
    )
    summary = summarize_numeric_router_source_repair_slippage_lifecycle_join_events([event])

    assert event["slippage_lifecycle_join_status"] == "SLIPPAGE_LIFECYCLE_JOIN_CONTRACT_COMPLETE"
    assert event["slippage_lifecycle_pair_bound_to_contract"] is True
    assert event["slippage_lifecycle_join_repaired_by_this_event"] is True
    assert event["exact_r_repaired_by_this_lifecycle_join"] is False
    assert event["merged_lifecycle_execution_identity_payload"]["source_repair_identity_key"] == "PLAN-1|CAT-1|SPEC-1"
    assert event["merged_lifecycle_execution_identity_payload"]["executed_exit_price"] == 2403.0
    assert summary["slippage_lifecycle_pair_bound_to_contract_rows"] == 1
    assert summary["slippage_lifecycle_join_repaired_by_this_event_rows"] == 1
    assert summary["runtime_candidate_use_permitted_rows"] == 0


def test_numeric_router_slippage_lifecycle_join_marks_missing_current_identity():
    pair = _complete_slippage_lifecycle_pair()
    for row in (pair["entry_slippage_row"], pair["close_slippage_row"]):
        row.pop("source_repair_plan_row_id", None)
        row.pop("input_numeric_router_catalog_entry_id", None)
        row.pop("input_numeric_router_family_spec_id", None)
        row.pop("source_repair_identity_key", None)

    event = numeric_router_source_repair_execution_identity_lifecycle_join_event_from_pair(
        _ready_execution_identity_contract(),
        pair,
        event_row_id="LIFE-1",
        source_artifact="contracts.jsonl",
        source_line_no=1,
        source_sha256="contract-sha",
        slippage_source_artifact="slippage.jsonl",
        slippage_source_sha256="slippage-sha",
    )
    summary = summarize_numeric_router_source_repair_slippage_lifecycle_join_events([event])

    assert event["slippage_lifecycle_join_status"] == "SLIPPAGE_LIFECYCLE_JOIN_SOURCE_REPAIR_IDENTITY_MISSING"
    assert "source_repair_plan_row_id" in event["missing_source_repair_identity_fields"]
    assert event["merged_lifecycle_execution_identity_payload"] is None
    assert summary["missing_source_repair_identity_lifecycle_rows"] == 1
    assert summary["slippage_lifecycle_join_repaired_by_this_event_rows"] == 0


def test_numeric_router_slippage_lifecycle_join_preserves_packet_context_absence():
    contract = _ready_execution_identity_contract()
    contract["execution_identity_capture_contract_status"] = (
        "READY_DEFAULT_OFF_PACKET_CONTEXT_CAPTURE_CONTRACT_EXECUTION_IDENTITY_ABSENT"
    )
    contract["source_repair_identity_key"] = ""
    contract["source_repair_identity_payload"] = None

    event = numeric_router_source_repair_execution_identity_lifecycle_join_event_from_pair(
        contract,
        _complete_slippage_lifecycle_pair(),
        event_row_id="LIFE-1",
        source_artifact="contracts.jsonl",
        source_line_no=1,
        source_sha256="contract-sha",
        slippage_source_artifact="slippage.jsonl",
        slippage_source_sha256="slippage-sha",
    )
    summary = summarize_numeric_router_source_repair_slippage_lifecycle_join_events([event])

    assert event["slippage_lifecycle_join_status"] == (
        "SLIPPAGE_LIFECYCLE_JOIN_PACKET_CONTEXT_EXECUTION_IDENTITY_ABSENT"
    )
    assert event["slippage_lifecycle_pair_bound_to_contract"] is False
    assert summary["packet_context_execution_identity_absent_lifecycle_rows"] == 1
