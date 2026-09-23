from __future__ import annotations

import json
from pathlib import Path

from src.components.broker_order_lifecycle_capture_v4 import (
    BROKER_REAL_ACCOUNT_HISTORY_STATUS,
    build_broker_order_lifecycle_capture_v4,
    record_broker_order_lifecycle_capture_v4,
)
from src.mt5.mt5_interface import OrderResult


def _trade_params(**overrides) -> dict:
    params = {
        "candidate_id": "cand-v4u",
        "decision_time_utc": "2026-06-06T06:00:00+00:00",
        "source_file": "data/historical_2026/XAUUSD_M15.csv",
        "source_hash": "source-sha",
        "gtos_vnext_source_event_hash": "event-sha",
        "gtos_vnext_selector_row_id": "selector-row",
        "gtos_vnext_selector_proof_hash": "selector-proof",
        "gtos_vnext_scheduler_v4_packet_hash": "scheduler-proof",
        "gtos_vnext_scheduler_v4_packet": {
            "decision_window_id": "window-1",
            "decision": {
                "selected_candidate_id": "cand-v4u",
                "selected_action_class": "new_position",
            },
        },
        "gtos_vnext_same_symbol_lifecycle_action": "new_position",
        "gtos_vnext_same_symbol_lifecycle_v4_packet": {
            "action": "new_position",
            "permitted_order_intent": True,
        },
        "gtos_vnext_prop_firm_headroom_snapshot_v4": {
            "schema_version": "prop_firm_headroom_snapshot_v4",
            "source_status": "source_bound_broker_real_account_headroom",
            "account_login_hash": "1" * 64,
            "source_event_hash_sha256": "2" * 64,
            "snapshot_hash_sha256": "3" * 64,
        },
        "gtos_vnext_execution_policy_id": "v4-policy",
        "gtos_vnext_dynamic_policy_selected": "momentum_exhaustion",
        "gtos_vnext_dynamic_policy_applied": True,
        "gtos_vnext_selected_cell_risk_pct": 0.25,
        "gtos_vnext_selected_cell_risk_cell_id": "risk-cell",
        "gtos_vnext_dynamic_target_stop_geometry_v4": {
            "status": "source_bound_geometry_contract_ready"
        },
    }
    params.update(overrides)
    return params


def _request() -> dict:
    return {
        "action": 1,
        "symbol": "XAUUSD",
        "volume": 0.1,
        "type": 0,
        "price": 2330.0,
        "sl": 2320.0,
        "tp": 2350.0,
        "deviation": 10,
        "magic": 20260401,
        "type_filling": 1,
    }


def _closed_ultimate_package_shadow(candidate_id: str = "candidate-package") -> dict:
    return {
        "schema": "gtos.final_moonshot.ultimate_candidate_package.scheduler_packet.v1",
        "schema_version": "ultimate_candidate_package_v1",
        "component": "ultimate_candidate_package",
        "packet_hash_sha256": "f" * 64,
        "decision_status": "shadow_scheduler_ranked_candidates",
        "shadow_selected_candidate_id": candidate_id,
        "selected_candidate_id": None,
        "approved_risk_pct": 0.0,
        "default_off": True,
        "shadow_only": True,
        "apply_to_execution": False,
        "live_activation_allowed_by_config": False,
        "final_package_selected_by_config": False,
        "runtime_effect_now": False,
        "candidate_use_allowed_now": False,
        "selected_package_denominator_use_allowed": False,
        "denominator_expansion_allowed": False,
        "clean_label_use_allowed": False,
        "training_use_allowed": False,
        "model_training_allowed": False,
        "final_package_selection_allowed": False,
        "deployment_dossier_allowed": False,
        "vps_handoff_allowed": False,
        "live_execution_activation_allowed": False,
        "broker_account_order_history_deal_position_mutation_allowed": False,
        "broker_operation": False,
        "order_calls": 0,
        "paid_api_or_vendor_call": False,
        "execution_policy_shadow": {
            "policy_status": "shadow_execution_policy_ready_not_selectable",
            "selected_order_type_architecture": None,
            "execution_order_type_policy_selectable": False,
            "missed_fill_opportunity_cost_allowed": False,
            "limit_first_vs_guarded_market_comparison_allowed": False,
            "broker_real_expectancy_claim_allowed": False,
            "action": "shadow_no_order_type_selection_no_execution",
            "approved_risk_pct": 0.0,
            "default_off": True,
            "shadow_only": True,
            "apply_to_execution": False,
            "live_activation_allowed_by_config": False,
            "final_package_selected_by_config": False,
            "runtime_effect_now": False,
            "candidate_use_allowed_now": False,
            "selected_package_denominator_use_allowed": False,
            "denominator_expansion_allowed": False,
            "clean_label_use_allowed": False,
            "training_use_allowed": False,
            "model_training_allowed": False,
            "final_package_selection_allowed": False,
            "deployment_dossier_allowed": False,
            "vps_handoff_allowed": False,
            "live_execution_activation_allowed": False,
            "broker_account_order_history_deal_position_mutation_allowed": False,
            "broker_operation": False,
            "order_calls": 0,
            "paid_api_or_vendor_call": False,
        },
    }


def test_pre_order_contract_is_ready_without_broker_real_label() -> None:
    packet = build_broker_order_lifecycle_capture_v4(
        stage="pre_order_contract",
        trade_params=_trade_params(),
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model={"status": "PASSED"},
        generated_at_utc="2026-06-06T06:00:01+00:00",
    )

    assert packet["status"] == "pre_order_capture_contract_ready"
    assert packet["broker_real_entry_label_ready"] is False
    assert packet["pre_order_capture_contract"]["missing_fields"] == []
    assert packet["remaining_capture_requirement"]["requirement_id"] == (
        "v4u_forward_broker_order_deal_lifecycle_capture"
    )
    assert packet["packet_hash_sha256"]


def test_broker_lifecycle_carries_closed_ultimate_package_shadow_boundary() -> None:
    package = _closed_ultimate_package_shadow("candidate-broker-package")
    trade_params = _trade_params()
    trade_params["gtos_vnext_scheduler_v4_packet"]["ultimate_candidate_package_shadow"] = (
        package
    )

    packet = build_broker_order_lifecycle_capture_v4(
        stage="pre_order_contract",
        trade_params=trade_params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model={"status": "PASSED"},
        generated_at_utc="2026-06-06T06:00:01+00:00",
    )

    assert packet["status"] == "pre_order_capture_contract_ready"
    assert packet["ultimate_candidate_package_shadow_status"] == (
        "default_off_shadow_authority_closed"
    )
    assert packet["ultimate_candidate_package_shadow_authority_closed"] is True
    assert packet["ultimate_candidate_package_shadow_packet_present"] is True
    assert packet["ultimate_candidate_package_shadow_packet_hash"] == "f" * 64
    assert packet["ultimate_candidate_package_shadow_selected_candidate_id"] == (
        "candidate-broker-package"
    )
    assert packet["ultimate_candidate_package_selected_candidate_id"] is None
    assert packet["ultimate_candidate_package_approved_risk_pct"] == 0.0
    assert packet["ultimate_candidate_package_order_calls"] == 0
    assert packet["ultimate_candidate_package_runtime_effect_now"] is False
    assert (
        packet["ultimate_candidate_package_live_execution_activation_allowed"]
        is False
    )
    assert (
        packet["ultimate_candidate_package_final_package_selection_allowed"]
        is False
    )
    assert packet["ultimate_candidate_package_selected_order_type_architecture"] is None
    assert (
        packet["ultimate_candidate_package_execution_order_type_policy_selectable"]
        is False
    )
    assert packet["ultimate_candidate_package_gate_violations"] == []
    assert packet["ultimate_candidate_package_shadow_boundary"]["authority_closed"] is True


def test_open_ultimate_package_shadow_blocks_broker_lifecycle_package_use() -> None:
    package = _closed_ultimate_package_shadow("candidate-broker-package")
    package["selected_candidate_id"] = "candidate-broker-package"

    packet = build_broker_order_lifecycle_capture_v4(
        stage="entry_fill_reconciled",
        trade_params=_trade_params(),
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        order_request=_request(),
        order_result=OrderResult(
            retcode=10009,
            order=777,
            deal=888,
            volume=0.1,
            price=2330.2,
            comment="filled",
        ),
        entry_deal_accounting={
            "account_history_lookup_status": BROKER_REAL_ACCOUNT_HISTORY_STATUS,
            "account_history_lookup_attempted": True,
            "account_history_lookup_attempt_count": 1,
            "deal_ticket": 888,
            "broker_fill_time_utc": "2026-06-06T06:00:03+00:00",
            "broker_entry_price": 2330.2,
            "commission": -3.5,
            "swap": 0.0,
        },
        execution_manager_packet={
            "scheduler_v4": {"ultimate_candidate_package_shadow": package}
        },
        generated_at_utc="2026-06-06T06:00:04+00:00",
    )

    assert packet["status"] == "source_required_for_broker_real_entry_label"
    assert packet["broker_real_entry_label_ready"] is False
    assert packet["ultimate_candidate_package_shadow_status"] == (
        "ultimate_candidate_package_shadow_authority_open"
    )
    assert packet["ultimate_candidate_package_shadow_authority_closed"] is False
    assert "selected_candidate_id_not_closed" in (
        packet["ultimate_candidate_package_gate_violations"]
    )
    assert "ultimate_candidate_package_shadow_authority_not_closed" in (
        packet["missing_fields"]
    )


def test_broker_real_entry_label_requires_order_deal_and_cost_reconciliation() -> None:
    packet = build_broker_order_lifecycle_capture_v4(
        stage="entry_fill_reconciled",
        trade_params=_trade_params(),
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        order_request=_request(),
        order_result=OrderResult(
            retcode=10009,
            order=777,
            deal=888,
            volume=0.1,
            price=2330.2,
            comment="filled",
        ),
        entry_deal_accounting={
            "account_history_lookup_status": BROKER_REAL_ACCOUNT_HISTORY_STATUS,
            "account_history_lookup_attempted": True,
            "account_history_lookup_attempt_count": 1,
            "deal_ticket": 888,
            "broker_fill_time_utc": "2026-06-06T06:00:03+00:00",
            "broker_entry_price": 2330.2,
            "commission": -3.5,
            "swap": 0.0,
        },
        generated_at_utc="2026-06-06T06:00:04+00:00",
    )

    assert packet["status"] == "broker_real_entry_lifecycle_reconciled"
    assert packet["broker_real_entry_label_ready"] is True
    assert packet["remaining_capture_requirement"] is None
    assert packet["deal_cost_reconciliation"]["missing_fields"] == []


def test_replay_or_proxy_accounting_is_not_broker_real_truth() -> None:
    packet = build_broker_order_lifecycle_capture_v4(
        stage="entry_fill_reconciled",
        trade_params=_trade_params(),
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        order_request=_request(),
        order_result=OrderResult(
            retcode=10009,
            order=777,
            deal=888,
            volume=0.1,
            price=2330.2,
            comment="filled",
        ),
        entry_deal_accounting={
            "account_history_lookup_status": "proxy_replay_reconciled",
            "deal_ticket": 888,
            "broker_fill_time_utc": "2026-06-06T06:00:03+00:00",
            "broker_entry_price": 2330.2,
            "commission": -3.5,
            "swap": 0.0,
        },
        generated_at_utc="2026-06-06T06:00:04+00:00",
    )

    assert packet["broker_real_entry_label_ready"] is False
    assert "account_history_deal_reconciliation" in packet["missing_fields"]
    assert "broker_real_source_status_not_replay_proxy_or_simulated" in (
        packet["missing_fields"]
    )


def test_lifecycle_capture_logger_writes_jsonl_when_enabled(tmp_path: Path) -> None:
    log_path = tmp_path / "broker_lifecycle.jsonl"
    packet = build_broker_order_lifecycle_capture_v4(
        stage="pre_order_contract",
        trade_params=_trade_params(),
        symbol="XAUUSD",
        generated_at_utc="2026-06-06T06:00:01+00:00",
    )

    record_broker_order_lifecycle_capture_v4(
        packet,
        config={
            "gtos_vnext_runtime": {
                "broker_order_lifecycle_capture_v4_enabled": True,
                "broker_order_lifecycle_capture_v4_log_enabled": True,
                "broker_order_lifecycle_capture_v4_log_path": str(log_path),
            }
        },
    )

    rows = [json.loads(line) for line in log_path.read_text().splitlines()]
    assert rows == [packet]
