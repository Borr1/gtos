from __future__ import annotations

from src.components.dynamic_target_stop_geometry_v4 import (
    build_target_stop_geometry_v4_contract,
)
from src.research_infra import v4_timewarp_simulated_live_research_loop as timewarp


def test_build_trade_params_emits_live_shape_geometry_and_decision_time_aliases() -> None:
    geometry_contract = {
        "packet_hash_sha256": "geometry-hash",
        "selected_policy": "momentum_exhaustion",
        "execution_policy_id": "policy-v4",
    }
    params = timewarp.build_trade_params(
        candidate={
            "candidate_id": "candidate-1",
            "symbol": "XAUUSD",
            "side": "LONG",
            "decision_time_utc": "2026-04-21T08:00:00+00:00",
            "entry_price": 2300.0,
            "stop_loss": 2295.0,
            "take_profit_1": 2310.0,
            "risk_reward_ratio": 2.0,
        },
        selector_packet={"action": "reduce-risk", "packet_hash_sha256": "selector-hash"},
        scheduler_packet={"decision": {"selected_action_class": "reduce-risk"}},
        lifecycle_packet={"action": "allow"},
        geometry_contract=geometry_contract,
        risk_pct=0.05,
        source_hash="source-hash",
        source_path="/tmp/source.csv",
        cost_r=0.12,
    )

    assert params["decision_time_utc"] == "2026-04-21T08:00:00+00:00"
    assert params["asof_utc"] == "2026-04-21T08:00:00+00:00"
    assert params["gtos_vnext_dynamic_target_stop_geometry_v4"] == geometry_contract
    assert params["gtos_vnext_target_stop_geometry_v4"] == geometry_contract
    assert params["gtos_vnext_dynamic_target_stop_geometry_v4_packet"] == geometry_contract
    assert params["gtos_vnext_target_stop_geometry_v4_packet"] == geometry_contract
    assert params["target_stop_geometry_v4"] == geometry_contract
    assert params["gtos_vnext_production_execution_path"] is False


def test_build_trade_params_reconciles_selector_action_from_package_risk_authority() -> None:
    geometry_contract = {
        "packet_hash_sha256": "geometry-hash",
        "selected_policy": "momentum_exhaustion",
        "execution_policy_id": "policy-v4",
    }
    params = timewarp.build_trade_params(
        candidate={
            "candidate_id": "candidate-reconciled-selector",
            "symbol": "XAUUSD",
            "side": "LONG",
            "decision_time_utc": "2026-04-21T08:00:00+00:00",
            "entry_price": 2300.0,
            "stop_loss": 2295.0,
            "take_profit_1": 2310.0,
            "risk_reward_ratio": 2.0,
            "scheduler_materialization_selector_action": "open-reduced-risk",
            "scheduler_materialization_selector_reason": (
                "admission_quality_dynamic_router_refused_candidate_use"
            ),
        },
        selector_packet={
            "action": "reject",
            "reason": "admission_quality_dynamic_router_refused_candidate_use",
            "packet_hash_sha256": "selector-hash",
        },
        scheduler_packet={"decision": {"selected_action_class": "new_position"}},
        lifecycle_packet={"action": "new_position"},
        geometry_contract=geometry_contract,
        risk_pct=0.05,
        source_hash="source-hash",
        source_path="/tmp/source.csv",
        cost_r=0.12,
        risk_authority={
            "risk_decision": "open-reduced-risk",
            "package_new_entry_authority_selector_action": "open-reduced-risk",
            "package_new_entry_authority_selector_reason": (
                "admission_quality_dynamic_router_refused_candidate_use"
            ),
        },
    )

    assert params["gtos_vnext_selector_v4_action"] == "open-reduced-risk"
    assert params["gtos_vnext_selector_v4_packet"]["action"] == "open-reduced-risk"
    assert params["gtos_vnext_selector_v4_original_action"] == "reject"
    assert params["gtos_vnext_selector_v4_action_reconciled_from_package_authority"] is True
    assert params["gtos_vnext_selector_v4_reconciled_action_source"] == (
        "runtime_risk_package_authority"
    )
    assert params["gtos_vnext_selector_v4_packet_hash"] == "selector-hash"


def test_timewarp_geometry_source_status_satisfies_asof_contract() -> None:
    contract = build_target_stop_geometry_v4_contract(
        config={"gtos_vnext_runtime": {}},
        selected_policy="momentum_exhaustion",
        execution_policy_id="policy-v4",
        source_event={
            "source_path_feature_status": "computed_from_source_ohlc_asof_timewarp_replay",
            "source_window_complete": True,
            "ordered_path_status": "pending_post_asof_replay",
            "selected_policy_ordered_path_status": "ordered_path_pending_postdecision_replay",
            "selected_policy_same_bar_ambiguous": False,
        },
        trade_params={"entry_price": 100.0, "stop_loss": 99.0, "direction": "LONG"},
        entry_price=100.0,
        stop_loss=99.0,
        direction="LONG",
        final_target_r=2.0,
    )

    assert contract["status"] == "source_bound_geometry_contract_ready"
    assert contract["source_completeness"]["missing_source_fields"] == []
