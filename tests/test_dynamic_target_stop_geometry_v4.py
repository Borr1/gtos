import json

from src.components.dynamic_target_stop_geometry_v4 import (
    SLTP_LIFECYCLE_REQUIRED_EVENTS,
    TARGET_STOP_GEOMETRY_V4_EVIDENCE_CLASS,
    build_target_stop_geometry_v4_contract,
)


def _config() -> dict:
    return {
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_momentum_trigger_r": 1.0,
            "moonshot_dynamic_execution_router_momentum_final_target_r": 2.0,
            "moonshot_dynamic_execution_router_momentum_pullback_r": 0.4,
            "moonshot_dynamic_execution_router_partial_trigger_r": 1.0,
            "moonshot_dynamic_execution_router_partial_final_target_r": 3.0,
            "moonshot_dynamic_execution_router_partial_close_ratio": 0.5,
            "moonshot_dynamic_execution_router_trailing_trigger_r": 1.0,
            "moonshot_dynamic_execution_router_trailing_final_target_r": 3.0,
            "moonshot_dynamic_execution_router_trailing_gap_r": 0.5,
            "moonshot_dynamic_target_stop_geometry_v4_default_thesis_horizon_m15_bars": 32,
            "moonshot_dynamic_target_stop_geometry_v4_stale_review_m15_bars": 24,
        }
    }


def _source_event() -> dict:
    return {
        "source_mode": "OHLC_M15_CSV",
        "source_path_feature_status": "computed_from_source_ohlc_asof",
        "source_window_complete": True,
        "ordered_path_status": "ordered_path_not_ambiguous_in_m15_replay",
        "selected_policy_ordered_path_status": (
            "ordered_path_not_ambiguous_in_m15_replay"
        ),
        "selected_policy_same_bar_ambiguous": False,
    }


def test_dynamic_target_stop_geometry_contract_binds_momentum_prices_and_capture() -> None:
    contract = build_target_stop_geometry_v4_contract(
        config=_config(),
        selected_policy="momentum_exhaustion",
        execution_policy_id="vnext_exec_momentum_1r_pullback_04r_cap_2r",
        source_event=_source_event(),
        trade_params={"direction": "LONG", "entry_price": 100.0, "stop_loss": 98.0},
        stage="unit_test",
    )

    assert contract["status"] == "source_bound_geometry_contract_ready"
    assert contract["evidence_class"] == TARGET_STOP_GEOMETRY_V4_EVIDENCE_CLASS
    assert contract["broker_runtime_change_status"] is False
    assert contract["validation_result_status"] is False
    assert contract["outcome_result_rows_status"] is False
    assert len(contract["source_event_hash_sha256"]) == 64
    assert len(contract["packet_hash_sha256"]) == 64
    assert contract["packet_hash"] == contract["packet_hash_sha256"]
    assert contract["stop_invalidation"]["risk_distance"] == 2.0
    assert contract["target_destination"]["trigger_price"] == 102.0
    assert contract["target_destination"]["final_target_price"] == 104.0
    assert contract["target_destination"]["final_target_r"] == 2.0
    assert contract["target_destination"]["management_model"] == (
        "exit_on_mfe_pullback_or_final_cap"
    )
    assert contract["target_destination"]["momentum_pullback_r"] == 0.4
    assert contract["target_destination"]["promoted_policy_family"] == (
        "momentum_primary_partial_exception_router"
    )
    assert contract["target_destination"]["exit_management_contract_status"] == (
        "policy_specific_management_fields_bound"
    )
    assert contract["thesis_horizon"]["horizon_m15_bars"] == 32
    assert contract["thesis_horizon"]["stale_review_m15_bars"] == 24
    assert set(SLTP_LIFECYCLE_REQUIRED_EVENTS).issubset(
        set(contract["modification_lifecycle_capture"]["required_events"])
    )
    assert contract["modification_lifecycle_capture"]["capture_status"] == (
        "prospective_capture_required"
    )


def test_dynamic_target_stop_geometry_contract_ignores_future_outcome_fields() -> None:
    source_event = _source_event()
    source_event["actual_r"] = 9.99
    contract = build_target_stop_geometry_v4_contract(
        config=_config(),
        selected_policy="momentum_exhaustion",
        execution_policy_id="vnext_exec_momentum_1r_pullback_04r_cap_2r",
        source_event=source_event,
        trade_params={
            "direction": "SHORT",
            "entry_price": 100.0,
            "stop_loss": 103.0,
            "broker_real_pnl_cash": 1234.56,
        },
        stage="unit_test",
    )

    assert contract["status"] == "geometry_source_gap_requires_repair"
    assert contract["source_completeness"]["source_complete"] is False
    assert contract["source_completeness"]["future_outcome_fields_ignored"] == [
        "source_event.actual_r",
        "trade_params.broker_real_pnl_cash",
    ]
    assert contract["target_destination"]["trigger_price"] == 97.0
    assert contract["target_destination"]["final_target_price"] == 94.0
    serialized = json.dumps(contract, sort_keys=True)
    assert "1234.56" not in serialized
    assert "9.99" not in serialized
    assert len(contract["source_event_hash_sha256"]) == 64
    assert len(contract["packet_hash_sha256"]) == 64


def test_dynamic_target_stop_geometry_does_not_reuse_static_take_profit_as_destination() -> None:
    contract = build_target_stop_geometry_v4_contract(
        config=_config(),
        selected_policy="momentum_exhaustion",
        execution_policy_id="vnext_exec_momentum_1r_pullback_04r_cap_2r",
        source_event=_source_event(),
        trade_params={
            "direction": "LONG",
            "entry_price": 100.0,
            "stop_loss": 98.0,
            "take_profit_1": 103.0,
        },
        stage="unit_test",
    )

    assert contract["target_destination"]["final_target_r"] == 2.0
    assert contract["target_destination"]["final_target_price"] == 104.0
    assert contract["target_destination"]["static_fixed_r_boundary"].startswith(
        "retired_static"
    )


def test_dynamic_target_stop_geometry_contract_binds_partial_runner_management() -> None:
    contract = build_target_stop_geometry_v4_contract(
        config=_config(),
        selected_policy="partial_be_runner",
        execution_policy_id="vnext_exec_partial_50_at_1r_be_runner_to_3r",
        source_event=_source_event(),
        trade_params={"direction": "LONG", "entry_price": 100.0, "stop_loss": 98.0},
        stage="unit_test",
    )

    assert contract["status"] == "source_bound_geometry_contract_ready"
    assert contract["target_destination"]["final_target_r"] == 3.0
    assert contract["target_destination"]["final_target_price"] == 106.0
    assert contract["target_destination"]["partial_close_ratio"] == 0.5
    assert contract["target_destination"]["management_model"] == (
        "partial_close_then_move_stop_to_breakeven_runner"
    )
    assert contract["target_destination"]["exit_management_contract_status"] == (
        "policy_specific_management_fields_bound"
    )


def test_dynamic_target_stop_geometry_contract_binds_trailing_runner_gap() -> None:
    contract = build_target_stop_geometry_v4_contract(
        config=_config(),
        selected_policy="trailing_runner",
        execution_policy_id="vnext_exec_trailing_1r_gap_05r_cap_3r",
        source_event=_source_event(),
        trade_params={"direction": "SHORT", "entry_price": 100.0, "stop_loss": 102.0},
        stage="unit_test",
    )

    assert contract["status"] == "source_bound_geometry_contract_ready"
    assert contract["target_destination"]["final_target_price"] == 94.0
    assert contract["target_destination"]["trail_gap_r"] == 0.5
    assert contract["target_destination"]["management_model"] == (
        "raise_stop_by_mfe_trailing_gap_after_trigger"
    )
