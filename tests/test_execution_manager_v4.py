from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.components import execution as exec_mod
from src.components.execution import ExecutionEngine
from src.components.execution_manager_v4 import evaluate_execution_manager_v4


@pytest.fixture(autouse=True)
def _isolate_runtime_files(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(exec_mod, "PENDING_INTENT_DIR", str(tmp_path / "meta"))
    monkeypatch.setattr(
        exec_mod,
        "CHECKPOINT_PATH",
        str(tmp_path / "meta" / "execution_checkpoint.json"),
    )
    rows: list[dict] = []
    monkeypatch.setattr(
        exec_mod,
        "record_pending_limit_lifecycle",
        lambda row: rows.append(row),
    )
    return rows


def _base_config(tmp_path: Path, *, apply: bool = False) -> dict:
    return {
        "market": {"symbol": "XAUUSD", "mt5_symbol": "XAUUSD"},
        "risk": {"risk_per_trade_pct": 1.0, "sl_absolute_min": 0.0},
        "gtos_vnext_runtime": {
            "execution_manager_v4_enabled": True,
            "execution_manager_v4_apply_to_execution": apply,
            "execution_manager_v4_log_enabled": True,
            "execution_manager_v4_log_path": str(tmp_path / "execution_v4.jsonl"),
            "execution_manager_v4_max_pending_fill_entry_drift_r": 0.25,
            "execution_manager_v4_selector_v4_packet_required": True,
            "execution_manager_v4_geometry_contract_required": True,
            "execution_manager_v4_broker_lifecycle_capture_contract_required": True,
            "broker_order_lifecycle_capture_v4_enabled": True,
            "broker_order_lifecycle_capture_v4_log_enabled": True,
            "broker_order_lifecycle_capture_v4_log_path": str(
                tmp_path / "broker_lifecycle_v4.jsonl"
            ),
            "selected_cell_pretrade_cost_model_required": True,
            "selected_cell_commission_model_required": True,
            "selected_cell_allowed_commission_model_statuses": [
                "SELECTED_CELL_RISK_LEDGER_VERIFIED_NO_EXECUTION_CRITICAL_COMMISSION_GAP",
            ],
        },
    }


def _production_params(**overrides) -> dict:
    params = {
        "direction": "LONG",
        "entry_price": 100.0,
        "stop_loss": 90.0,
        "take_profit_1": 120.0,
        "gtos_vnext_production_execution_path": True,
        "gtos_vnext_selected_cell_risk_pct": 0.25,
        "gtos_vnext_selected_cell_risk_cell_id": "risk-cell-xau",
        "gtos_vnext_selected_cell_risk_decision_basis": "unit_test",
        "gtos_vnext_selected_cell_risk_selected_policy": "momentum_exhaustion",
        "gtos_vnext_selected_cell_risk_policy_identity_status": (
            "policy_invariant_broker_geometry_for_selected_execution_policy"
        ),
        "gtos_vnext_execution_policy_id": "vnext_exec_momentum_1r_pullback_04r_cap_2r",
        "gtos_vnext_dynamic_policy_selected": "momentum_exhaustion",
        "gtos_vnext_dynamic_policy_applied": True,
        "gtos_vnext_dynamic_policy_replaced_policy": "retired_static_baseline_comparator",
        "gtos_vnext_dynamic_be_trigger_r": 1.0,
        "gtos_vnext_dynamic_final_target_r": 2.0,
        "gtos_vnext_dynamic_momentum_pullback_r": 0.4,
        "gtos_vnext_commission_model_status": (
            "SELECTED_CELL_RISK_LEDGER_VERIFIED_NO_EXECUTION_CRITICAL_COMMISSION_GAP"
        ),
        "gtos_vnext_cost_model_source": "selected_cell_risk_ledger",
    }
    params.update(overrides)
    return params


def _broker_real_headroom_snapshot(max_allowed_pct: float = 1.0) -> dict:
    return {
        "schema_version": "prop_firm_headroom_snapshot_v4",
        "source_status": "source_bound_broker_real_account_headroom",
        "evidence_class": "broker_real_account_headroom_snapshot_v4",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "account_namespace": "redacted_account_live_bee34003",
        "account_login_hash": "1" * 64,
        "daily_reset_window_id": "2026-06-06T00:00:00+00:00/redacted_account",
        "current_equity": 100500.0,
        "day_start_equity_or_balance_baseline": 100000.0,
        "available_daily_loss_headroom_pct": 3.5,
        "available_overall_loss_headroom_pct": 8.5,
        "max_allowed_new_trade_risk_pct": max_allowed_pct,
        "source_event_hash_sha256": "2" * 64,
        "snapshot_hash_sha256": "3" * 64,
        "broker_runtime_change_status": False,
        "broker_order_mutation": False,
    }


def _source_complete_overrides() -> dict:
    return {
        "candidate_id": "unit-candidate",
        "source_file": "knowledge_base/redacted_account_live_bee34003/trade_records/XAUUSD/example.json",
        "source_hash": "source-sha",
        "gtos_vnext_source_event_hash": "event-sha",
        "gtos_vnext_source_event_details": {"candidate": "unit"},
        "gtos_vnext_selector_row_id": "selector-row",
        "gtos_vnext_selector_proof_hash": "selector-proof",
        "gtos_vnext_selector_v4_action": "trade",
        "gtos_vnext_selector_v4_reason": "unit_selector_trade",
        "gtos_vnext_selector_v4_packet_hash": "selector-v4-packet-hash",
        "gtos_vnext_selector_v4_packet": {
            "action": "trade",
            "reason": "unit_selector_trade",
            "packet_hash_sha256": "selector-v4-packet-hash",
            "source_status": "source_bound_unit_fixture",
        },
        "gtos_vnext_pretrade_cost_model": {
            "status": "PASSED",
            "authority": "broker_calibrated_replay_cost",
            "cost_source_gap_status": "source_bound_cost_authority_present",
            "candidate_cost_r_fallback_is_authority": False,
            "spread_r": 0.01,
            "max_spread_r": 0.10,
            "commission_model_status": (
                "SELECTED_CELL_RISK_LEDGER_VERIFIED_NO_EXECUTION_CRITICAL_COMMISSION_GAP"
            ),
        },
        "gtos_vnext_scheduler_v4_current_candidate_id": "unit-candidate",
        "gtos_vnext_scheduler_v4_selected_candidate_id": "unit-candidate",
        "gtos_vnext_scheduler_v4_selected_action_class": "new_position",
        "gtos_vnext_scheduler_v4_packet_hash": "scheduler-v4-packet-hash",
        "gtos_vnext_scheduler_v4_packet": {
            "decision_window_id": "unit-window",
            "decision": {
                "selected_candidate_id": "unit-candidate",
                "selected_action_class": "new_position",
                "runtime_effect_now": True,
            },
            "source_boundary": {"missing_runtime_truth": []},
        },
        "gtos_vnext_same_symbol_lifecycle_action": "new_position",
        "gtos_vnext_same_symbol_lifecycle_v4_packet": {
            "action": "new_position",
            "permitted_order_intent": True,
            "reason": "unit_new_position_allowed",
        },
        "gtos_vnext_dynamic_target_stop_geometry_v4": {
            "status": "source_bound_geometry_contract_ready",
            "source_completeness": {
                "missing_source_fields": [],
                "selected_policy_same_bar_ambiguous": False,
            },
            "target_destination": {
                "exit_management_contract_status": "policy_specific_management_bound",
            },
        },
        "gtos_vnext_prop_firm_headroom_snapshot_v4": _broker_real_headroom_snapshot(),
        "decision_time_utc": "2026-06-04T20:00:00+00:00",
    }


def _ultimate_candidate_package_shadow(**overrides) -> dict:
    packet = {
        "schema": "gtos.final_moonshot.ultimate_candidate_package.scheduler_packet.v1",
        "schema_version": "ultimate_candidate_package_v1",
        "component": "ultimate_candidate_package",
        "decision_status": "shadow_scheduler_ranked_candidates",
        "decision_window_id": "unit-window",
        "shadow_selected_candidate_id": "unit-candidate",
        "selected_candidate_id": None,
        "action": "shadow_no_trade_no_execution",
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
    packet.update(overrides)
    return packet


def _engine(tmp_path: Path, *, apply: bool = False) -> ExecutionEngine:
    mt5 = MagicMock()
    mt5.get_tick.return_value = SimpleNamespace(
        ask=100.0,
        bid=99.9,
        spread_cents=10.0,
    )
    mt5.get_history_deals.return_value = []
    return ExecutionEngine(mt5, _base_config(tmp_path, apply=apply))


def test_execution_manager_v4_packet_blocks_missing_source_when_apply_enabled(
    tmp_path: Path,
):
    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=_production_params(),
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model={
            "status": "PASSED",
            "spread_r": 0.01,
            "max_spread_r": 0.10,
            "commission_model_status": (
                "SELECTED_CELL_RISK_LEDGER_VERIFIED_NO_EXECUTION_CRITICAL_COMMISSION_GAP"
            ),
        },
    )

    assert decision.action == "block"
    assert decision.should_block is True
    assert any(reason.startswith("missing_source:") for reason in decision.fatal_reasons)
    assert decision.packet["broker_runtime_change_status"] is False


def test_execution_manager_v4_blocks_selector_v4_reject_when_apply_enabled(
    tmp_path: Path,
):
    overrides = {
        **_source_complete_overrides(),
        "gtos_vnext_selector_v4_action": "reject",
        "gtos_vnext_selector_v4_reason": "hard_avoid_unit_fixture",
    }
    params = _production_params(
        **overrides,
    )

    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
    )

    assert decision.should_block is True
    assert any(
        reason == "selector_v4_action_blocks_execution:reject"
        for reason in decision.fatal_reasons
    )
    assert decision.packet["selector_v4"]["action"] == "reject"


def test_execution_manager_v4_allows_selector_v4_reduce_risk_when_apply_enabled(
    tmp_path: Path,
):
    overrides = {
        **_source_complete_overrides(),
        "gtos_vnext_selector_v4_action": "reduce-risk",
        "gtos_vnext_selector_v4_reason": "selector_v4_reduced_risk_unit_fixture",
        "gtos_vnext_selector_v4_packet": {
            "action": "reduce-risk",
            "reason": "selector_v4_reduced_risk_unit_fixture",
            "packet_hash_sha256": "selector-v4-packet-hash",
            "source_status": "source_bound_unit_fixture",
        },
    }
    params = _production_params(**overrides)

    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
    )

    assert decision.should_block is False
    assert decision.action == "allow"
    assert not any("selector_v4_action_blocks_execution" in reason for reason in decision.fatal_reasons)
    assert decision.packet["selector_v4"]["normalized_action"] == "reduce-risk"
    assert decision.packet["prop_firm_headroom_contract"]["status"] == (
        "source_bound_broker_real_headroom_ready"
    )
    assert decision.packet["broker_order_lifecycle_capture_v4"]["status"] == (
        "pre_order_capture_contract_ready"
    )
    assert decision.packet["broker_order_lifecycle_capture_v4"][
        "pre_order_capture_contract"
    ]["missing_fields"] == []


def test_execution_manager_v4_uses_supplied_replay_clock_deterministically(
    tmp_path: Path,
):
    generated_at_utc = "2026-01-02T08:15:00+00:00"
    params = _production_params(**_source_complete_overrides())

    first = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
        generated_at_utc=generated_at_utc,
    )
    second = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
        generated_at_utc=generated_at_utc,
    )

    assert first.packet == second.packet
    assert first.packet["generated_at_utc"] == generated_at_utc
    assert first.packet["broker_order_lifecycle_capture_v4"][
        "generated_at_utc"
    ] == generated_at_utc


@pytest.mark.parametrize(
    ("cost_overrides", "expected_reason"),
    [
        (
            {"authority": "timewarp_candidate_cost_proxy"},
            "missing_cost:pretrade_cost_model_authority_broker_calibrated_replay_cost",
        ),
        (
            {"cost_source_gap_status": "default_spread_floor_no_source"},
            "missing_cost:pretrade_cost_model_source_bound_cost_authority_present",
        ),
        (
            {"candidate_cost_r_fallback_is_authority": True},
            "missing_cost:pretrade_cost_model_candidate_cost_fallback_not_authority",
        ),
    ],
)
def test_execution_manager_v4_blocks_weak_cost_authority_when_apply_enabled(
    tmp_path: Path,
    cost_overrides: dict,
    expected_reason: str,
):
    params = _production_params(**_source_complete_overrides())
    params["gtos_vnext_pretrade_cost_model"] = {
        **params["gtos_vnext_pretrade_cost_model"],
        **cost_overrides,
    }

    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
    )

    assert decision.action == "block"
    assert decision.should_block is True
    assert expected_reason in decision.fatal_reasons
    assert decision.packet["cost_context"]["status"] == "cost_incomplete"


def test_execution_manager_v4_accepts_complete_refused_cost_packet_contract(
    tmp_path: Path,
):
    params = _production_params(**_source_complete_overrides())
    packet = {
        **params["gtos_vnext_pretrade_cost_model"],
        "status": "REFUSED",
        "refusal_reasons": [
            "total_cost_r_exceeds_limit:0.200000>0.150000"
        ],
    }
    params["gtos_vnext_pretrade_cost_model"] = packet

    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=packet,
    )

    assert decision.should_block is False
    assert "missing_cost:pretrade_cost_model_status_passed" not in decision.fatal_reasons
    assert decision.packet["cost_context"]["status"] == "cost_complete"
    assert decision.packet["cost_context"]["pretrade_cost_model_status"] == "REFUSED"


def test_execution_manager_v4_blocks_missing_broker_lifecycle_capture_fields(
    tmp_path: Path,
):
    overrides = _source_complete_overrides()
    overrides.pop("gtos_vnext_scheduler_v4_packet_hash")
    overrides.pop("gtos_vnext_same_symbol_lifecycle_v4_packet")
    params = _production_params(**overrides)

    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
    )

    assert decision.should_block is True
    assert "missing_broker_lifecycle_capture:scheduler_packet_hash" in (
        decision.fatal_reasons
    )
    assert "missing_broker_lifecycle_capture:same_symbol_lifecycle_packet" in (
        decision.fatal_reasons
    )
    assert decision.packet["broker_order_lifecycle_capture_v4"]["status"] == (
        "pre_order_capture_contract_gap"
    )


def test_execution_manager_v4_blocks_missing_prop_firm_headroom_snapshot(
    tmp_path: Path,
):
    overrides = _source_complete_overrides()
    overrides.pop("gtos_vnext_prop_firm_headroom_snapshot_v4")
    params = _production_params(**overrides)

    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
    )

    assert decision.should_block is True
    assert "prop_firm_headroom_v4_snapshot_missing" in decision.fatal_reasons
    assert decision.packet["prop_firm_headroom_contract"]["packet"]["allowed"] is False


def test_execution_manager_v4_builds_headroom_snapshot_from_runtime_account_state(
    tmp_path: Path,
):
    overrides = _source_complete_overrides()
    overrides.pop("gtos_vnext_prop_firm_headroom_snapshot_v4")
    overrides["gtos_vnext_prop_firm_headroom_account_state_v4"] = {
        "schema_version": "prop_firm_headroom_account_state_v4",
        "account_namespace": "redacted_account_live_bee34003",
        "account_login": 0,
        "current_balance": 100000.0,
        "current_equity": 100250.0,
        "day_start_equity_or_balance_baseline": 100000.0,
        "initial_balance": 100000.0,
        "daily_loss_limit_pct": 5.0,
        "overall_loss_limit_pct": 10.0,
        "new_trade_buffer_pct": 0.25,
        "daily_reset_window_id": "2026-06-06/redacted_account",
    }
    params = _production_params(**overrides)

    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
    )

    headroom = decision.packet["prop_firm_headroom_contract"]
    assert headroom["status"] == "source_bound_broker_real_headroom_ready"
    assert headroom["snapshot_source"] == "runtime_account_state_adapter"
    assert headroom["packet"]["allowed"] is True
    assert "prop_firm_headroom_v4_snapshot_missing" not in decision.fatal_reasons
    assert "account_login" not in headroom["packet"]["snapshot"]


def test_execution_manager_v4_blocks_scheduler_v4_zero_trade_when_apply_enabled(
    tmp_path: Path,
):
    params = _production_params(
        **{
            **_source_complete_overrides(),
            "gtos_vnext_scheduler_v4_selected_action_class": "zero_trade",
            "gtos_vnext_scheduler_v4_selected_candidate_id": None,
            "gtos_vnext_scheduler_v4_packet": {
                "decision_window_id": "unit-window",
                "decision": {
                    "selected_candidate_id": None,
                    "selected_action_class": "zero_trade",
                    "runtime_effect_now": False,
                },
                "source_boundary": {"missing_runtime_truth": []},
            },
        }
    )

    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
    )

    assert decision.should_block is True
    assert "scheduler_v4_selected_zero_trade" in decision.fatal_reasons
    assert decision.packet["scheduler_v4"]["selected_action_class"] == "zero_trade"


def test_execution_manager_v4_blocks_unselected_scheduler_candidate(
    tmp_path: Path,
):
    params = _production_params(
        **{
            **_source_complete_overrides(),
            "gtos_vnext_scheduler_v4_selected_candidate_id": "better-candidate",
            "gtos_vnext_scheduler_v4_packet": {
                "decision_window_id": "unit-window",
                "decision": {
                    "selected_candidate_id": "better-candidate",
                    "selected_action_class": "new_position",
                    "runtime_effect_now": True,
                },
                "source_boundary": {"missing_runtime_truth": []},
            },
        }
    )

    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
    )

    assert decision.should_block is True
    assert "scheduler_v4_candidate_not_selected" in decision.fatal_reasons


def test_execution_manager_v4_allows_multi_selected_scheduler_candidate(
    tmp_path: Path,
):
    params = _production_params(
        **{
            **_source_complete_overrides(),
            "gtos_vnext_scheduler_v4_selected_candidate_id": "primary-candidate",
            "gtos_vnext_scheduler_v4_selected_candidate_ids": [
                "primary-candidate",
                "unit-candidate",
            ],
            "gtos_vnext_scheduler_v4_packet": {
                "decision_window_id": "unit-window",
                "decision": {
                    "selected_candidate_id": "primary-candidate",
                    "selected_candidate_ids": [
                        "primary-candidate",
                        "unit-candidate",
                    ],
                    "selected_action_class": "new_position",
                    "runtime_effect_now": True,
                },
                "source_boundary": {"missing_runtime_truth": []},
            },
        }
    )

    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
    )

    assert "scheduler_v4_candidate_not_selected" not in decision.fatal_reasons
    assert decision.packet["scheduler_v4"]["selected_candidate_ids"] == [
        "primary-candidate",
        "unit-candidate",
    ]


def test_execution_manager_v4_blocks_live_scheduler_selected_action_when_live_effect_false(
    tmp_path: Path,
):
    overrides = _source_complete_overrides()
    overrides["gtos_vnext_scheduler_v4_packet"] = {
        **overrides["gtos_vnext_scheduler_v4_packet"],
        "decision": {
            "selected_candidate_id": "unit-candidate",
            "selected_candidate_ids": ["unit-candidate"],
            "selected_action_class": "new_position",
            "runtime_effect_now": False,
            "selected_option": {
                "candidate_id": "unit-candidate",
                "action_class": "new_position",
                "runtime_eligible": True,
            },
        },
    }
    params = _production_params(**overrides)

    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
    )

    assert decision.should_block is True
    assert "scheduler_v4_selected_action_not_runtime_eligible" in decision.fatal_reasons
    assert decision.packet["scheduler_v4"]["replay_runtime_effect_now"] is False


def test_execution_manager_v4_allows_no_broker_replay_scheduler_selected_option(
    tmp_path: Path,
):
    simulated_headroom = {
        **_broker_real_headroom_snapshot(),
        "source_status": "source_bound_replay_simulated_account_headroom",
        "evidence_class": "replay_simulated_prop_firm_headroom_snapshot_v4",
    }
    overrides = _source_complete_overrides()
    overrides["gtos_vnext_prop_firm_headroom_snapshot_v4"] = simulated_headroom
    overrides["gtos_vnext_live_as_if_replay_no_broker_authority"] = True
    overrides["gtos_vnext_replay_broker_mutation_enabled"] = False
    overrides["gtos_vnext_scheduler_v4_packet"] = {
        **overrides["gtos_vnext_scheduler_v4_packet"],
        "decision": {
            "selected_candidate_id": "unit-candidate",
            "selected_candidate_ids": ["unit-candidate"],
            "selected_action_class": "new_position",
            "runtime_effect_now": False,
            "selected_option": {
                "candidate_id": "unit-candidate",
                "action_class": "new_position",
                "runtime_eligible": True,
            },
        },
    }
    params = _production_params(**overrides)

    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
    )

    assert decision.should_block is False
    assert "scheduler_v4_selected_action_not_runtime_eligible" not in decision.fatal_reasons
    assert "prop_firm_headroom_v4_snapshot_not_broker_real" not in decision.fatal_reasons
    assert (
        "live_promotion_only:prop_firm_headroom_v4_snapshot_not_broker_real"
        in decision.warning_reasons
    )
    assert decision.packet["scheduler_v4"]["runtime_effect_now"] is False
    assert decision.packet["scheduler_v4"]["replay_runtime_effect_now"] is True
    assert decision.packet["identity"]["replay_no_broker_authority"] is True


def test_execution_manager_v4_reconciles_signed_source_required_close_reverse_replay(
    tmp_path: Path,
):
    overrides = _source_complete_overrides()
    overrides.update(
        {
            "gtos_vnext_live_as_if_replay_no_broker_authority": True,
            "gtos_vnext_replay_broker_mutation_enabled": False,
            "gtos_vnext_scheduler_v4_selected_action_class": "close_and_reverse",
            "gtos_vnext_scheduler_v4_packet": {
                "decision_window_id": "unit-window",
                "decision": {
                    "selected_candidate_id": "unit-candidate",
                    "selected_candidate_ids": ["unit-candidate"],
                    "selected_action_class": "close_and_reverse",
                    "runtime_effect_now": False,
                    "selected_option": {
                        "candidate_id": "unit-candidate",
                        "action_class": "close_and_reverse",
                        "runtime_eligible": True,
                    },
                },
                "source_boundary": {"missing_runtime_truth": []},
            },
            "gtos_vnext_same_symbol_lifecycle_action": "source_required_fail_closed",
            "gtos_vnext_same_symbol_lifecycle_v4_packet": {
                "action": "source_required_fail_closed",
                "permitted_order_intent": False,
                "reason": "same_symbol_candidate_durable_lifecycle_capture_missing",
            },
            "gtos_vnext_timewarp_runtime_risk_authority_v4": {
                "same_symbol_lifecycle_permission_reconcile_applied": True,
                "same_symbol_lifecycle_permission_reconcile_reason": (
                    "package_opposite_side_close_reverse_lifecycle_reconciled_for_replay"
                ),
                "same_symbol_lifecycle_reconciled_action": "close_and_reverse",
                "same_symbol_lifecycle_action": "close_and_reverse",
                "package_opposite_side_close_reverse_lifecycle_reconcile": {
                    "applied": True,
                    "reason": (
                        "package_opposite_side_close_reverse_lifecycle_reconciled_for_replay"
                    ),
                    "same_symbol_lifecycle_action": "close_and_reverse",
                },
                "package_new_entry_authority_valid": True,
                "package_new_entry_authority_target_action_intent": (
                    "close_and_reverse"
                ),
                "package_new_entry_authority_failures": [],
                "source_required_broker_lifecycle_truth_satisfied": False,
            },
        }
    )
    params = _production_params(**overrides)

    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
    )

    assert decision.should_block is False
    assert decision.action == "allow"
    assert (
        "same_symbol_lifecycle_v4_not_permitted:source_required_fail_closed"
        not in decision.fatal_reasons
    )
    assert (
        "same_symbol_lifecycle_v4_manager_action_required:close_and_reverse"
        not in decision.fatal_reasons
    )
    lifecycle = decision.packet["lifecycle_contract"]
    assert lifecycle["action"] == "close_and_reverse"
    assert lifecycle["permitted_order_intent"] is True
    assert lifecycle["original_action"] == "source_required_fail_closed"
    assert lifecycle["original_permitted_order_intent"] is False
    assert lifecycle["replay_lifecycle_reconcile"]["applied"] is True
    assert (
        lifecycle["replay_lifecycle_reconcile"]["signed_package_authority_valid"]
        is True
    )
    assert lifecycle["packet"]["original_action"] == "source_required_fail_closed"
    assert lifecycle["packet"]["action"] == "close_and_reverse"
    assert decision.packet["broker_order_lifecycle_capture_v4"][
        "ticket_thesis_lifecycle"
    ]["same_symbol_lifecycle_action"] == "close_and_reverse"


def test_execution_manager_v4_keeps_unsigned_source_required_replay_blocked(
    tmp_path: Path,
):
    overrides = _source_complete_overrides()
    overrides.update(
        {
            "gtos_vnext_live_as_if_replay_no_broker_authority": True,
            "gtos_vnext_replay_broker_mutation_enabled": False,
            "gtos_vnext_scheduler_v4_selected_action_class": "close_and_reverse",
            "gtos_vnext_scheduler_v4_packet": {
                "decision_window_id": "unit-window",
                "decision": {
                    "selected_candidate_id": "unit-candidate",
                    "selected_candidate_ids": ["unit-candidate"],
                    "selected_action_class": "close_and_reverse",
                    "runtime_effect_now": False,
                    "selected_option": {
                        "candidate_id": "unit-candidate",
                        "action_class": "close_and_reverse",
                        "runtime_eligible": True,
                    },
                },
                "source_boundary": {"missing_runtime_truth": []},
            },
            "gtos_vnext_same_symbol_lifecycle_action": "source_required_fail_closed",
            "gtos_vnext_same_symbol_lifecycle_v4_packet": {
                "action": "source_required_fail_closed",
                "permitted_order_intent": False,
                "reason": "same_symbol_candidate_durable_lifecycle_capture_missing",
            },
            "gtos_vnext_timewarp_runtime_risk_authority_v4": {
                "same_symbol_lifecycle_permission_reconcile_applied": True,
                "same_symbol_lifecycle_reconciled_action": "close_and_reverse",
                "package_opposite_side_close_reverse_lifecycle_reconcile": {
                    "applied": True,
                    "same_symbol_lifecycle_action": "close_and_reverse",
                },
                "package_new_entry_authority_valid": False,
                "package_new_entry_authority_target_action_intent": (
                    "close_and_reverse"
                ),
                "source_required_broker_lifecycle_truth_satisfied": False,
            },
        }
    )
    params = _production_params(**overrides)

    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
    )

    assert decision.should_block is True
    assert (
        "same_symbol_lifecycle_v4_not_permitted:source_required_fail_closed"
        in decision.fatal_reasons
    )
    lifecycle = decision.packet["lifecycle_contract"]
    assert lifecycle["action"] == "source_required_fail_closed"
    assert lifecycle["replay_lifecycle_reconcile"]["applied"] is False
    assert (
        lifecycle["replay_lifecycle_reconcile"]["signed_package_authority_valid"]
        is False
    )


def test_execution_manager_v4_keeps_live_close_reverse_manager_required(
    tmp_path: Path,
):
    overrides = _source_complete_overrides()
    overrides.update(
        {
            "gtos_vnext_scheduler_v4_selected_action_class": "close_and_reverse",
            "gtos_vnext_scheduler_v4_packet": {
                "decision_window_id": "unit-window",
                "decision": {
                    "selected_candidate_id": "unit-candidate",
                    "selected_candidate_ids": ["unit-candidate"],
                    "selected_action_class": "close_and_reverse",
                    "runtime_effect_now": True,
                },
                "source_boundary": {"missing_runtime_truth": []},
            },
            "gtos_vnext_same_symbol_lifecycle_action": "close_and_reverse",
            "gtos_vnext_same_symbol_lifecycle_v4_packet": {
                "action": "close_and_reverse",
                "permitted_order_intent": False,
                "reason": (
                    "same_symbol_close_reduce_reverse_requires_execution_manager_before_new_order"
                ),
            },
            "gtos_vnext_timewarp_runtime_risk_authority_v4": {
                "same_symbol_lifecycle_permission_reconcile_applied": True,
                "same_symbol_lifecycle_reconciled_action": "close_and_reverse",
                "package_new_entry_authority_valid": True,
                "package_new_entry_authority_target_action_intent": (
                    "close_and_reverse"
                ),
                "package_new_entry_authority_failures": [],
            },
        }
    )
    params = _production_params(**overrides)

    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
    )

    assert decision.should_block is True
    assert (
        "same_symbol_lifecycle_v4_manager_action_required:close_and_reverse"
        in decision.fatal_reasons
    )
    assert decision.packet["lifecycle_contract"]["replay_lifecycle_reconcile"][
        "applied"
    ] is False


def test_execution_manager_v4_carries_closed_ultimate_package_shadow_boundary(
    tmp_path: Path,
):
    overrides = _source_complete_overrides()
    overrides["gtos_vnext_scheduler_v4_packet"] = {
        **overrides["gtos_vnext_scheduler_v4_packet"],
        "ultimate_candidate_package_shadow": _ultimate_candidate_package_shadow(),
    }
    params = _production_params(**overrides)

    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
    )

    package = decision.packet["scheduler_v4"]["ultimate_candidate_package_shadow"]
    assert decision.should_block is False
    assert package["status"] == "default_off_shadow_authority_closed"
    assert package["shadow_selected_candidate_id"] == "unit-candidate"
    assert package["selected_candidate_id"] is None
    assert package["approved_risk_pct"] == 0.0
    assert package["runtime_effect_now"] is False
    assert package["live_execution_activation_allowed"] is False
    assert package["final_package_selection_allowed"] is False
    assert package["order_calls"] == 0
    assert package["execution_policy_status"] == (
        "shadow_execution_policy_ready_not_selectable"
    )
    assert package["selected_order_type_architecture"] is None
    assert package["execution_order_type_policy_selectable"] is False
    assert package["gate_violations"] == []


def test_execution_manager_v4_blocks_open_ultimate_package_shadow_authority(
    tmp_path: Path,
):
    package = _ultimate_candidate_package_shadow(
        selected_candidate_id="unit-candidate",
        approved_risk_pct=0.25,
        runtime_effect_now=True,
        live_execution_activation_allowed=True,
        execution_policy_shadow={
            **_ultimate_candidate_package_shadow()["execution_policy_shadow"],
            "selected_order_type_architecture": "limit_first",
            "execution_order_type_policy_selectable": True,
            "order_calls": 1,
        },
    )
    overrides = _source_complete_overrides()
    overrides["gtos_vnext_scheduler_v4_packet"] = {
        **overrides["gtos_vnext_scheduler_v4_packet"],
        "ultimate_candidate_package_shadow": package,
    }
    params = _production_params(**overrides)

    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
    )

    package_context = decision.packet["scheduler_v4"][
        "ultimate_candidate_package_shadow"
    ]
    assert decision.should_block is True
    assert "ultimate_candidate_package_shadow_authority_not_closed" in (
        decision.fatal_reasons
    )
    assert package_context["status"] == "ultimate_candidate_package_shadow_authority_open"
    assert "selected_candidate_id_not_closed" in package_context["gate_violations"]
    assert "approved_risk_pct_not_zero" in package_context["gate_violations"]
    assert "runtime_effect_now_not_false" in package_context["gate_violations"]
    assert (
        "execution_policy_shadow.selected_order_type_architecture_not_closed"
        in package_context["gate_violations"]
    )
    assert (
        "execution_policy_shadow.execution_order_type_policy_selectable_not_false"
        in package_context["gate_violations"]
    )
    assert (
        "execution_policy_shadow.order_calls_not_zero"
        in package_context["gate_violations"]
    )


def test_execution_manager_v4_blocks_missing_lifecycle_owner_packet(
    tmp_path: Path,
):
    params = _production_params(**_source_complete_overrides())
    params.pop("gtos_vnext_same_symbol_lifecycle_v4_packet")
    params.pop("gtos_vnext_same_symbol_lifecycle_action")

    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
    )

    assert decision.should_block is True
    assert any(reason.startswith("missing_lifecycle:") for reason in decision.fatal_reasons)


def test_execution_manager_v4_blocks_ambiguous_geometry_before_order(
    tmp_path: Path,
):
    overrides = _source_complete_overrides()
    overrides["gtos_vnext_dynamic_target_stop_geometry_v4"] = {
        **overrides["gtos_vnext_dynamic_target_stop_geometry_v4"],
        "source_completeness": {
            "missing_source_fields": [],
            "selected_policy_same_bar_ambiguous": True,
        },
    }
    params = _production_params(
        **overrides,
        selected_policy_same_bar_ambiguous=True,
    )

    decision = evaluate_execution_manager_v4(
        config=_base_config(tmp_path, apply=True),
        trade_params=params,
        symbol="XAUUSD",
        broker_symbol="XAUUSD",
        pretrade_cost_model=params["gtos_vnext_pretrade_cost_model"],
    )

    assert decision.should_block is True
    assert any(
        reason == "missing_geometry_contract:selected_policy_same_bar_ambiguous"
        for reason in decision.fatal_reasons
    )
    assert decision.packet["geometry_contract"]["terminal_order_guard"] == (
        "execution_manager_v4_blocks_gapped_geometry_before_order"
    )


def test_open_trade_v4_blocks_before_safe_place_order_when_apply_enabled(
    tmp_path: Path,
):
    engine = _engine(tmp_path, apply=True)
    engine.safe_place_order = MagicMock()
    params = _production_params()

    state = engine.open_trade(params, account_balance=100000.0)

    assert state is None
    engine.safe_place_order.assert_not_called()
    assert params["gtos_vnext_execution_manager_v4_action"] == "block"
    assert params["gtos_vnext_execution_manager_v4_packet"]["component"] == (
        "execution_manager_v4"
    )


def test_pending_intent_v4_blocks_before_persistence_when_apply_enabled(
    tmp_path: Path,
):
    engine = _engine(tmp_path, apply=True)
    params = _production_params()

    intent = engine.set_limit_intent(
        params,
        account_balance=100000.0,
        telemetry_context={"candidate_id": "candidate-missing-source"},
    )

    assert intent is None
    assert engine.pending_intent is None
    assert not Path(engine._pending_intent_path).exists()


def test_pending_intent_can_carry_observe_packet_when_apply_disabled(
    tmp_path: Path,
):
    engine = _engine(tmp_path, apply=False)
    params = _production_params(**_source_complete_overrides())
    intent = engine.set_limit_intent(
        params,
        account_balance=100000.0,
        telemetry_context={
            **_source_complete_overrides(),
            "candidate_id": "candidate-1",
        },
    )

    assert intent.gtos_vnext_execution_manager_v4_action == "observe_only"
    assert intent.gtos_vnext_prop_firm_headroom_snapshot_v4["schema_version"] == (
        "prop_firm_headroom_snapshot_v4"
    )
    assert intent.gtos_vnext_execution_manager_v4_packet is not None
    assert intent.gtos_vnext_execution_manager_v4_packet["entry_timing"][
        "pending_context"
    ]["stage"] == "pending_intent_created"
    assert intent.gtos_vnext_scheduler_v4_packet is not None
    assert intent.gtos_vnext_selector_v4_packet is not None
    assert intent.gtos_vnext_same_symbol_lifecycle_v4_packet is not None
    assert intent.gtos_vnext_pretrade_cost_model is not None

    with patch.object(engine, "open_trade", return_value=MagicMock()) as mock_open:
        engine.check_limit_fill(
            {
                "time": "2026-06-04T20:15:00+00:00",
                "open": 101.0,
                "high": 102.0,
                "low": 99.5,
                "close": 100.5,
            }
        )

    trade_params = mock_open.call_args.kwargs["trade_params"]
    assert trade_params["gtos_vnext_prop_firm_headroom_snapshot_v4"]["source_status"] == (
        "source_bound_broker_real_account_headroom"
    )
    assert trade_params["gtos_vnext_execution_manager_v4_action"] == "observe_only"
    assert trade_params["gtos_vnext_scheduler_v4_packet"] is not None
    assert trade_params["gtos_vnext_selector_v4_packet"] is not None
    assert trade_params["gtos_vnext_same_symbol_lifecycle_v4_packet"] is not None
    assert trade_params["gtos_vnext_pretrade_cost_model"] is not None
    assert trade_params["gtos_vnext_execution_manager_v4_packet"]["entry_timing"][
        "pending_context"
    ]["stage"] == "pending_fill_triggered"


def test_pending_intent_builds_and_persists_headroom_snapshot_from_account_state(
    tmp_path: Path,
):
    engine = _engine(tmp_path, apply=False)
    overrides = _source_complete_overrides()
    overrides.pop("gtos_vnext_prop_firm_headroom_snapshot_v4")
    overrides["gtos_vnext_prop_firm_headroom_account_state_v4"] = {
        "schema_version": "prop_firm_headroom_account_state_v4",
        "account_namespace": "redacted_account_live_bee34003",
        "account_login": 0,
        "current_balance": 100000.0,
        "current_equity": 100250.0,
        "day_start_equity_or_balance_baseline": 100000.0,
        "initial_balance": 100000.0,
        "daily_loss_limit_pct": 5.0,
        "overall_loss_limit_pct": 10.0,
        "new_trade_buffer_pct": 0.25,
        "daily_reset_window_id": "2026-06-06/redacted_account",
    }
    params = _production_params(**overrides)

    intent = engine.set_limit_intent(
        params,
        account_balance=100000.0,
        telemetry_context={"candidate_id": "candidate-account-state"},
    )

    assert intent is not None
    assert intent.gtos_vnext_prop_firm_headroom_snapshot_v4["schema_version"] == (
        "prop_firm_headroom_snapshot_v4"
    )
    assert intent.gtos_vnext_prop_firm_headroom_snapshot_v4["source_status"] == (
        "source_bound_broker_real_account_headroom"
    )
    assert "account_login" not in intent.gtos_vnext_prop_firm_headroom_snapshot_v4
    assert intent.gtos_vnext_prop_firm_headroom_v4_packet["allowed"] is True


def test_pending_fill_preserves_v4_packets_when_apply_enabled(
    tmp_path: Path,
):
    engine = _engine(tmp_path, apply=True)
    params = _production_params(**_source_complete_overrides())
    intent = engine.set_limit_intent(
        params,
        account_balance=100000.0,
        telemetry_context=_source_complete_overrides(),
    )

    assert intent is not None
    assert intent.gtos_vnext_target_stop_geometry_v4["status"] == (
        "source_bound_geometry_contract_ready"
    )

    with patch.object(engine, "open_trade", return_value=MagicMock()) as mock_open:
        state = engine.check_limit_fill(
            {
                "time": "2026-06-04T20:15:00+00:00",
                "open": 100.0,
                "high": 101.0,
                "low": 99.5,
                "close": 100.5,
            }
        )

    assert state is not None
    mock_open.assert_called_once()
    trade_params = mock_open.call_args.kwargs["trade_params"]
    assert trade_params["gtos_vnext_scheduler_v4_packet"] is not None
    assert trade_params["gtos_vnext_selector_v4_packet"] is not None
    assert trade_params["gtos_vnext_same_symbol_lifecycle_v4_packet"] is not None
    assert trade_params["gtos_vnext_pretrade_cost_model"] is not None
    assert trade_params["gtos_vnext_dynamic_target_stop_geometry_v4"]["status"] == (
        "source_bound_geometry_contract_ready"
    )
    assert trade_params["gtos_vnext_execution_manager_v4_action"] == "allow"


def test_pending_fill_v4_blocks_excessive_entry_drift_before_open_trade(
    tmp_path: Path,
    _isolate_runtime_files,
):
    engine = _engine(tmp_path, apply=True)
    engine.mt5.get_tick.return_value = SimpleNamespace(
        ask=103.0,
        bid=102.9,
        spread_cents=10.0,
    )
    params = _production_params(**_source_complete_overrides())
    engine.set_limit_intent(
        params,
        account_balance=100000.0,
        telemetry_context=_source_complete_overrides(),
    )

    with patch.object(engine, "open_trade", return_value=MagicMock()) as mock_open:
        state = engine.check_limit_fill(
            {
                "time": "2026-06-04T20:15:00+00:00",
                "open": 101.0,
                "high": 104.0,
                "low": 99.5,
                "close": 103.0,
            }
        )

    assert state is None
    mock_open.assert_not_called()
    assert engine.pending_intent is None
    assert _isolate_runtime_files[-1]["intent_after_check"] == (
        "execution_manager_v4_blocked"
    )
