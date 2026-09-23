"""Tests for execution permissions (Phase 3)."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

import src.components.permissions as _perm_mod
from src.components.permissions import (
    check_permissions,
    ExecutionDenial,
    _find_target_ob,
    _reject_if_sl_behind_liquidity_cluster,
)
from src.mt5.mt5_mock import MockMT5

ULTIMATE_PACKAGE_SURFACE_REGISTRY = (
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl"
)


def _mock_mso(m15_atr=3.0):
    """Build a minimal MSO-like object with configurable M15 ATR."""
    return SimpleNamespace(
        timeframes={"M15": SimpleNamespace(atr_14=m15_atr)},
    )


def _mock_pa(grade="A+", direction="LONG", entry=2650.0, sl=2640.0,
             rr=1.5, daily_bias="bullish"):
    """Build a minimal PrimaryAnalysisOutput-like object."""
    tp = SimpleNamespace(
        direction=direction,
        entry_price=entry,
        stop_loss=sl,
        risk_reward_ratio=rr,
        take_profit_1=entry + (entry - sl) * rr,
    )
    reasoning = SimpleNamespace(
        setup_grade=grade,
        daily_bias=SimpleNamespace(direction=daily_bias),
    )
    return SimpleNamespace(reasoning=reasoning, trade_parameters=tp)


def _mock_vnext_pa(**overrides):
    pa = _mock_pa()
    defaults = {
        "gtos_vnext_production_execution_path": True,
        "gtos_vnext_dynamic_policy_applied": True,
        "gtos_vnext_dynamic_policy_selected": "momentum_exhaustion",
        "gtos_vnext_execution_policy_id": "vnext_exec_momentum_1r_pullback_04r_cap_2r",
        "gtos_vnext_selected_cell_risk_pct": 2.0,
    }
    defaults.update(overrides)
    for key, value in defaults.items():
        setattr(pa.trade_parameters, key, value)
    return pa


def _prop_safe_config() -> dict:
    return {
        "deployment": {"phase": 3},
        "trading_enabled": True,
        "risk": {"max_daily_loss_pct": 4.0, "max_spread_cents": 30},
        "same_symbol_lifecycle_v4": {"enabled": False},
        "gtos_vnext_runtime": {
            "prop_safe_selector_enabled": True,
            "prop_safe_selector_apply_to_execution": True,
        },
    }


def _broker_real_headroom_snapshot(
    *,
    max_allowed_pct: float = 2.0,
    captured_at_utc: str | None = None,
    source_status: str = "source_bound_broker_real_account_headroom",
    evidence_class: str = "broker_real_account_headroom_snapshot_v4",
) -> dict:
    captured = captured_at_utc or datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": "prop_firm_headroom_snapshot_v4",
        "source_status": source_status,
        "evidence_class": evidence_class,
        "captured_at_utc": captured,
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


def _scheduler_v4_authority_config() -> dict:
    return {
        "deployment": {"phase": 3},
        "trading_enabled": True,
        "risk": {"max_daily_loss_pct": 4.0, "max_spread_cents": 1000},
        "same_symbol_lifecycle_v4": {"enabled": False},
        "gtos_vnext_runtime": {
            "scheduler_v4_best_trade_allocator_enabled": True,
            "scheduler_v4_best_trade_allocator_apply_to_execution": True,
            "scheduler_v4_best_trade_allocator_live_activation_allowed": True,
            "scheduler_v4_best_trade_allocator_require_full_window_source": True,
            "scheduler_v4_best_trade_allocator_critical_missing_source_tokens": [
                "full_candidate_decision_window",
                "full_open_position_snapshot",
                "full_pending_order_snapshot",
                "same_symbol_lifecycle_packet",
                "probability_debate_packet",
                "numeric_follow_avoid_mixed_packet",
            ],
            "scheduler_v4_best_trade_allocator_min_trade_score": 0.35,
            "scheduler_v4_best_trade_allocator_zero_trade_score": 0.20,
        },
    }


def _attach_scheduler_v4_source_packets(pa) -> None:
    tp = pa.trade_parameters
    tp.gtos_vnext_pending_order_snapshot = []
    tp.gtos_vnext_probability_debate_v4_packet = {"status": "source_bound_unit_fixture"}
    tp.gtos_vnext_numeric_confluence_v4_packet = {"status": "source_bound_unit_fixture"}
    tp.gtos_vnext_selector_v4_packet = {"status": "source_bound_unit_fixture", "action": "trade"}
    tp.gtos_vnext_pretrade_cost_model = {
        "status": "PASSED",
        "authority": "broker_calibrated_replay_cost",
        "cost_source_gap_status": "source_bound_cost_authority_present",
        "candidate_cost_r_fallback_is_authority": False,
        "expected_cost_r": 0.02,
        "total_cost_r": 0.02,
    }
    tp.gtos_vnext_selected_cell_risk_proof = {
        "status": "source_bound_unit_fixture",
        "risk_pct": getattr(tp, "gtos_vnext_selected_cell_risk_pct", 0.25),
    }
    tp.gtos_vnext_source_event_hash = "a" * 64


def test_scheduler_v4_terminal_gate_blocks_missing_full_window_source():
    mt5 = MockMT5()
    mt5.connect()
    mt5.set_tick(2650.0, 2650.1)
    pa = _mock_vnext_pa(candidate_id="current")

    denial = check_permissions(
        pa,
        _mock_mso(),
        {"daily_pnl_pct": 0.0},
        mt5,
        config=_scheduler_v4_authority_config(),
        symbol="XAUUSD",
        skip_gate1_safety=True,
    )

    assert denial is not None
    assert denial.reason == "scheduler_v4_full_window_source_required"
    assert "full_candidate_decision_window" in denial.details["missing_runtime_truth"]
    assert hasattr(pa.trade_parameters, "gtos_vnext_scheduler_v4_packet")


def test_scheduler_v4_terminal_gate_blocks_unselected_candidate():
    mt5 = MockMT5()
    mt5.connect()
    mt5.set_tick(2650.0, 2650.1)
    pa = _mock_vnext_pa(candidate_id="weak")
    _attach_scheduler_v4_source_packets(pa)
    pa.trade_parameters.gtos_vnext_decision_window_candidates = [
        {
            "candidate_id": "weak",
            "symbol": "XAUUSD",
            "side": "LONG",
            "requested_risk_pct": 0.25,
            "ev_r": 0.05,
            "probability": 0.51,
            "source_completeness": 1.0,
            "source_completeness_status": "complete",
            "no_leak_status": "pass",
        },
        {
            "candidate_id": "strong",
            "symbol": "EURUSD",
            "side": "LONG",
            "requested_risk_pct": 0.25,
            "ev_r": 1.20,
            "probability": 0.72,
            "source_completeness": 1.0,
            "source_completeness_status": "complete",
            "no_leak_status": "pass",
        },
    ]

    denial = check_permissions(
        pa,
        _mock_mso(),
        {"daily_pnl_pct": 0.0},
        mt5,
        config=_scheduler_v4_authority_config(),
        symbol="XAUUSD",
        skip_gate1_safety=True,
    )

    assert denial is not None
    assert denial.reason == "scheduler_v4_candidate_not_selected"
    assert denial.details["selected_candidate_id"] == "strong"
    assert pa.trade_parameters.gtos_vnext_scheduler_v4_selected_candidate_id == "strong"


def test_scheduler_v4_terminal_gate_allows_selected_candidate_and_records_packet_hash():
    mt5 = MockMT5()
    mt5.connect()
    mt5.set_tick(2650.0, 2650.1)
    pa = _mock_vnext_pa(candidate_id="strong")
    _attach_scheduler_v4_source_packets(pa)
    pa.trade_parameters.gtos_vnext_decision_window_candidates = [
        {
            "candidate_id": "weak",
            "symbol": "EURUSD",
            "side": "LONG",
            "requested_risk_pct": 0.25,
            "ev_r": 0.05,
            "probability": 0.51,
            "source_completeness": 1.0,
            "source_completeness_status": "complete",
            "no_leak_status": "pass",
        },
        {
            "candidate_id": "strong",
            "symbol": "XAUUSD",
            "side": "LONG",
            "requested_risk_pct": 0.25,
            "ev_r": 1.20,
            "probability": 0.72,
            "source_completeness": 1.0,
            "source_completeness_status": "complete",
            "no_leak_status": "pass",
        },
    ]

    denial = check_permissions(
        pa,
        _mock_mso(),
        {"daily_pnl_pct": 0.0},
        mt5,
        config=_scheduler_v4_authority_config(),
        symbol="XAUUSD",
        skip_gate1_safety=True,
    )

    assert denial is None
    assert pa.trade_parameters.gtos_vnext_scheduler_v4_selected_candidate_id == "strong"
    assert pa.trade_parameters.gtos_vnext_scheduler_v4_selected_action_class == "new_position"
    assert len(pa.trade_parameters.gtos_vnext_scheduler_v4_packet_hash) == 64


def test_scheduler_v4_terminal_gate_carries_ultimate_candidate_package_shadow_packet():
    mt5 = MockMT5()
    mt5.connect()
    mt5.set_tick(17850.0, 17850.5)
    pa = _mock_vnext_pa(candidate_id="candidate:nas-vol-long")
    _attach_scheduler_v4_source_packets(pa)
    pa.trade_parameters.gtos_vnext_decision_window_candidates = [
        {
            "candidate_id": "candidate:nas-vol-long",
            "symbol": "NAS100",
            "side": "LONG",
            "decision_time_utc": "2026-05-05T06:15:00Z",
            "requested_risk_pct": 0.25,
            "ev_r": 1.20,
            "probability": 0.72,
            "confidence": 0.8,
            "source_completeness": 1.0,
            "source_completeness_status": "complete",
            "no_leak_status": "pass",
            "origin_family": "volatility_compression_expansion",
        }
    ]
    config = _scheduler_v4_authority_config()
    config["gtos_vnext_runtime"].update(
        {
            "ultimate_candidate_package_enabled": True,
            "ultimate_candidate_package_shadow_enabled": True,
            "ultimate_candidate_package_apply_to_execution": False,
            "ultimate_candidate_package_live_activation_allowed": False,
            "ultimate_candidate_package_final_package_selected": False,
            "ultimate_candidate_package_registry_path": ULTIMATE_PACKAGE_SURFACE_REGISTRY,
            "ultimate_candidate_package_require_shadow_match_for_selector_v4": False,
        }
    )

    denial = check_permissions(
        pa,
        _mock_mso(),
        {"daily_pnl_pct": 0.0},
        mt5,
        config=config,
        symbol="NAS100",
        skip_gate1_safety=True,
    )

    assert denial is None
    packet = pa.trade_parameters.gtos_vnext_scheduler_v4_packet
    package = packet["ultimate_candidate_package_shadow"]
    selector_packet = package["selector_packets"][0]
    policy = package["execution_policy_shadow"]
    assert package["decision_status"] == "shadow_scheduler_ranked_candidates"
    assert selector_packet["matched_promote_default_off_sleeves"] == 0
    assert selector_packet["matched_scheduler_lifecycle_merge_sleeves"] >= 1
    assert selector_packet["matched_package_role_counts"] == {
        "scheduler_lifecycle_core": 1
    }
    assert package["selected_candidate_id"] is None
    assert package["approved_risk_pct"] == 0.0
    assert package["runtime_effect_now"] is False
    assert package["live_execution_activation_allowed"] is False
    assert package["broker_account_order_history_deal_position_mutation_allowed"] is False
    assert package["order_calls"] == 0
    assert policy["policy_status"] == "shadow_execution_policy_ready_not_selectable"
    assert policy["selected_order_type_architecture"] is None
    assert policy["execution_order_type_policy_selectable"] is False
    assert policy["missed_fill_opportunity_cost_allowed"] is False
    assert policy["order_calls"] == 0


@pytest.fixture(autouse=True)
def _reset_concurrent_tracker_cache():
    """Clear the 10s TTL cache in concurrent_tracker so tests don't cross-pollinate."""
    import src.components.concurrent_tracker as _ct
    _ct.reset_cache()
    yield
    _ct.reset_cache()


@pytest.fixture(autouse=True)
def _isolate_dormant_state(tmp_path, monkeypatch):
    """Redirect the dormant marker path into tmp_path.

    Canonical tmp_path + module-ref monkeypatch pattern (tests/conftest.py
    docstring) — prevents any test from touching pipeline_state/dormant_state.json.
    """
    import src.safety.dormant_state as _ds
    monkeypatch.setattr(_ds, "DORMANT_STATE_PATH", tmp_path / "dormant_state.json")
    yield


class TestGate3CircuitBreakers:
    def test_blocks_daily_loss_limit(self):
        mt5 = MockMT5(); mt5.connect()
        # T2.8 default cap raised 2% -> 4%, so -4.5% trips.
        state = {"daily_pnl_pct": -4.5, "trades_today": 0, "current_kill_zone": "london",
                 "trades_london": 0, "losses_today": 0}
        denial = check_permissions(_mock_pa(), _mock_mso(), state, mt5)
        assert denial is not None
        assert denial.gate == "gate3_circuit_breaker"
        assert denial.reason == "daily_loss_limit"

    def test_daily_loss_limit_honors_config_override(self):
        """An explicit config.risk.max_daily_loss_pct must override the default."""
        mt5 = MockMT5(); mt5.connect()
        state = {"daily_pnl_pct": -2.5, "trades_today": 0, "current_kill_zone": "london",
                 "trades_london": 0, "losses_today": 0}
        config = {"risk": {"max_daily_loss_pct": 2.0}}
        denial = check_permissions(_mock_pa(), _mock_mso(), state, mt5, config=config)
        assert denial is not None
        assert denial.reason == "daily_loss_limit"

    def test_vnext_prop_safe_packet_missing_fails_closed_before_order(self):
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "london"}

        denial = check_permissions(
            _mock_vnext_pa(),
            _mock_mso(),
            state,
            mt5,
            config=_prop_safe_config(),
            symbol="XAUUSD",
        )

        assert denial is not None
        assert denial.gate == "gate3_circuit_breaker"
        assert denial.reason == "vnext_prop_safe_selector_packet_missing"
        assert "gtos_vnext_prop_safe_selector_action" in denial.details["missing_fields"]

    def test_vnext_prop_safe_block_action_fails_closed(self):
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "london"}
        pa = _mock_vnext_pa(
            gtos_vnext_prop_safe_selector_action="BLOCK",
            gtos_vnext_prop_safe_selector_would_action="BLOCK",
            gtos_vnext_prop_safe_selector_applied=True,
            gtos_vnext_prop_safe_selector_reason="prop_safe_selector_current_overall_max_loss_breach",
            gtos_vnext_prop_safe_selector_after_risk_pct=0.0,
        )

        denial = check_permissions(
            pa,
            _mock_mso(),
            state,
            mt5,
            config=_prop_safe_config(),
            symbol="XAUUSD",
        )

        assert denial is not None
        assert denial.reason == "vnext_prop_safe_selector_block"
        assert denial.details["reason"] == "prop_safe_selector_current_overall_max_loss_breach"

    def test_vnext_prop_safe_allow_requires_broker_real_headroom_snapshot(self):
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "london"}
        pa = _mock_vnext_pa(
            gtos_vnext_prop_safe_selector_action="ALLOW",
            gtos_vnext_prop_safe_selector_would_action="ALLOW",
            gtos_vnext_prop_safe_selector_applied=False,
            gtos_vnext_prop_safe_selector_reason="prop_safe_selector_budget_allows_full_risk",
            gtos_vnext_prop_safe_selector_after_risk_pct=2.0,
        )

        denial = check_permissions(
            pa,
            _mock_mso(),
            state,
            mt5,
            config=_prop_safe_config(),
            symbol="XAUUSD",
        )

        assert denial is not None
        assert denial.reason == "vnext_prop_firm_headroom_snapshot_missing"
        packet = pa.trade_parameters.gtos_vnext_prop_firm_headroom_v4_packet
        assert packet["allowed"] is False
        assert packet["source_boundary"].startswith("broker_real_account_headroom")

    def test_vnext_prop_safe_replay_headroom_snapshot_does_not_clear_live_gate(self):
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "london"}
        pa = _mock_vnext_pa(
            gtos_vnext_prop_safe_selector_action="ALLOW",
            gtos_vnext_prop_safe_selector_would_action="ALLOW",
            gtos_vnext_prop_safe_selector_applied=False,
            gtos_vnext_prop_safe_selector_reason="prop_safe_selector_budget_allows_full_risk",
            gtos_vnext_prop_safe_selector_after_risk_pct=2.0,
            gtos_vnext_prop_firm_headroom_snapshot_v4=_broker_real_headroom_snapshot(
                source_status="source_bound_replay_proxy_account_curve",
                evidence_class="replay/proxy-R simulated prop-firm headroom",
            ),
        )

        denial = check_permissions(
            pa,
            _mock_mso(),
            state,
            mt5,
            config=_prop_safe_config(),
            symbol="XAUUSD",
        )

        assert denial is not None
        assert denial.reason == "vnext_prop_firm_headroom_snapshot_not_broker_real"

    def test_vnext_prop_safe_stale_headroom_snapshot_fails_closed(self):
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "london"}
        stale_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        pa = _mock_vnext_pa(
            gtos_vnext_prop_safe_selector_action="ALLOW",
            gtos_vnext_prop_safe_selector_would_action="ALLOW",
            gtos_vnext_prop_safe_selector_applied=False,
            gtos_vnext_prop_safe_selector_reason="prop_safe_selector_budget_allows_full_risk",
            gtos_vnext_prop_safe_selector_after_risk_pct=2.0,
            gtos_vnext_prop_firm_headroom_snapshot_v4=_broker_real_headroom_snapshot(
                captured_at_utc=stale_time,
            ),
        )

        denial = check_permissions(
            pa,
            _mock_mso(),
            state,
            mt5,
            config=_prop_safe_config(),
            symbol="XAUUSD",
        )

        assert denial is not None
        assert denial.reason == "vnext_prop_firm_headroom_snapshot_stale"
        assert denial.details["prop_firm_headroom_v4"]["stale_by_seconds"] > 0

    def test_vnext_prop_safe_reduce_risk_is_consumed_by_permissions(self):
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "london"}
        pa = _mock_vnext_pa(
            gtos_vnext_prop_safe_selector_action="REDUCE_RISK",
            gtos_vnext_prop_safe_selector_would_action="REDUCE_RISK",
            gtos_vnext_prop_safe_selector_applied=True,
            gtos_vnext_prop_safe_selector_reason="prop_safe_selector_reduce_risk_to_daily_budget",
            gtos_vnext_prop_safe_selector_after_risk_pct=0.5,
            gtos_vnext_prop_firm_headroom_snapshot_v4=_broker_real_headroom_snapshot(
                max_allowed_pct=0.5,
            ),
        )

        denial = check_permissions(
            pa,
            _mock_mso(),
            state,
            mt5,
            config=_prop_safe_config(),
            symbol="XAUUSD",
        )

        assert denial is None
        assert pa.trade_parameters.gtos_vnext_selected_cell_risk_pct == 0.5
        assert pa.trade_parameters.gtos_vnext_prop_firm_headroom_v4_packet["allowed"] is True

    def test_max_daily_losses_counter_no_longer_gates(self):
        """T2.8 removed the max_daily_losses=2 count gate. Gate should pass
        even with losses_today >= 2 if nothing else fails."""
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)
        state = {"daily_pnl_pct": 0, "trades_today": 5, "current_kill_zone": "london",
                 "trades_london": 0, "losses_today": 99}
        denial = check_permissions(_mock_pa(), _mock_mso(), state, mt5)
        assert denial is None

    def test_kz_trade_limit_counter_no_longer_gates(self):
        """T2.8 removed the max_kz_trades=1 cap. Same-instrument concurrency is
        allowed; the concurrent cap handles portfolio-level exposure instead."""
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)
        state = {"daily_pnl_pct": 0, "trades_today": 1, "current_kill_zone": "london",
                 "trades_london": 99, "losses_today": 0}
        denial = check_permissions(_mock_pa(), _mock_mso(), state, mt5)
        assert denial is None

    def test_blocks_mt5_disconnected(self):
        mt5 = MockMT5()  # NOT connected
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "london",
                 "trades_london": 0, "losses_today": 0}
        denial = check_permissions(_mock_pa(), _mock_mso(), state, mt5)
        assert denial is not None
        assert denial.reason == "mt5_disconnected"

    def test_blocks_spread_too_wide(self):
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.50)  # 50 cents spread
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "london",
                 "trades_london": 0, "losses_today": 0}
        from unittest.mock import patch
        with patch("src.judgment.cost_choices.withholds", return_value=True):
            denial = check_permissions(_mock_pa(), _mock_mso(), state, mt5)
        assert denial is not None
        assert denial.reason == "spread_too_wide"

    def test_wide_spread_does_not_restore_the_boolean(self):
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.50)
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "london",
                 "trades_london": 0, "losses_today": 0}
        from unittest.mock import patch
        with patch("src.judgment.cost_choices.withholds", return_value=False):
            denial = check_permissions(_mock_pa(), _mock_mso(), state, mt5)
        assert denial is None

    def test_passes_when_all_clear(self):
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)  # 18 cents
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "london",
                 "trades_london": 0, "losses_today": 0}
        denial = check_permissions(_mock_pa(), _mock_mso(), state, mt5)
        assert denial is None


class TestGate1SafetyChecks:
    def _good_state(self):
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "london",
                 "trades_london": 0, "losses_today": 0}
        return mt5, state

    def test_rejects_below_grade(self):
        mt5, state = self._good_state()
        denial = check_permissions(_mock_pa(grade="B+"), _mock_mso(), state, mt5)
        assert denial is not None
        assert "below_grade_threshold" in denial.reason

    def test_rejects_no_trade_params(self):
        mt5, state = self._good_state()
        pa = SimpleNamespace(reasoning=SimpleNamespace(setup_grade="A+"), trade_parameters=None)
        denial = check_permissions(pa, _mock_mso(), state, mt5)
        assert denial is not None
        assert denial.reason == "no_trade_parameters"

    def test_rejects_direction_mismatch(self):
        mt5, state = self._good_state()
        denial = check_permissions(
            _mock_pa(direction="SHORT", daily_bias="bullish"),
            _mock_mso(), state, mt5,
        )
        assert denial is not None
        assert "direction_mismatch" in denial.reason

    def test_rejects_low_rr(self):
        mt5, state = self._good_state()
        denial = check_permissions(_mock_pa(rr=1.0), _mock_mso(), state, mt5)
        assert denial is not None
        assert "rr_too_low" in denial.reason

    def test_rejects_inverted_tp_sl_by_default_from_negative_expectancy_evidence(self, monkeypatch):
        monkeypatch.setattr(_perm_mod, "_log_inverted_tp", lambda *args, **kwargs: None)
        mt5, state = self._good_state()
        pa = _mock_pa(entry=2650.0, sl=2640.0, rr=1.5)
        pa.trade_parameters.take_profit_1 = 2649.0

        denial = check_permissions(pa, _mock_mso(), state, mt5)

        assert denial is not None
        assert denial.reason == "inverted_tp_sl_blocked_negative_expectancy"
        assert denial.details["source_path"] == "knowledge_base/wf1_inverted_tp_analysis.md"
        assert denial.details["corrected_avg_r"] == -0.325
        assert denial.details["inverted_candidate_rate_pct"] == 7.03
        assert pa.trade_parameters.take_profit_1 == 2649.0

    def test_inverted_tp_auto_correct_requires_explicit_rollback_config(self, monkeypatch):
        monkeypatch.setattr(_perm_mod, "_log_inverted_tp", lambda *args, **kwargs: None)
        mt5, state = self._good_state()
        pa = _mock_pa(entry=2650.0, sl=2640.0, rr=1.5)
        pa.trade_parameters.take_profit_1 = 2649.0
        config = {
            "risk": {
                "inverted_geometry_policy": "auto_correct",
                "min_rr": 1.5,
                "sl_absolute_min": 0.001,
            }
        }

        denial = check_permissions(pa, _mock_mso(m15_atr=0.0), state, mt5, config=config)

        assert denial is None
        assert pa.trade_parameters.take_profit_1 == 2665.0
        assert pa.trade_parameters.stop_loss == 2640.0
        assert pa.trade_parameters.risk_reward_ratio == 1.5

    def test_rejects_sl_too_small(self):
        mt5, state = self._good_state()
        # SL distance = $3.00 (below $5.00 floor)
        denial = check_permissions(
            _mock_pa(entry=2650.0, sl=2647.0), _mock_mso(), state, mt5,
        )
        assert denial is not None
        assert "sl_below_minimum_floor" in denial.reason

    def test_rejects_sl_tight_vs_atr(self):
        mt5, state = self._good_state()
        # SL distance = $5.50, ATR = $5.0, 1.5*ATR = $7.50
        denial = check_permissions(
            _mock_pa(entry=2650.0, sl=2644.5), _mock_mso(m15_atr=5.0), state, mt5,
        )
        assert denial is not None
        assert "sl_too_tight" in denial.reason

    def test_passes_valid_trade(self):
        mt5, state = self._good_state()
        denial = check_permissions(
            _mock_pa(grade="A", entry=2650.0, sl=2640.0, rr=1.5, daily_bias="bullish"),
            _mock_mso(m15_atr=3.0), state, mt5,
        )
        assert denial is None

    def test_agent_config_rejects_inverted_geometry_by_default(self):
        with Path("config/agent_config.yaml").open("r", encoding="utf-8") as handle:
            cfg = yaml.safe_load(handle)

        risk = cfg["risk"]
        assert risk["inverted_geometry_policy"] == "reject"
        assert risk["inverted_geometry_source_path"] == "knowledge_base/wf1_inverted_tp_analysis.md"
        assert risk["inverted_geometry_corrected_avg_r"] == -0.325


def _mock_mso_with_h1_ob(ob, m15_atr=0.05):
    """MSO with a real H1 order block — for testing Gate1 OB exception."""
    h1_tf = SimpleNamespace(order_blocks=[ob], breaker_blocks=[])
    return SimpleNamespace(
        timeframes={
            "M15": SimpleNamespace(atr_14=m15_atr),
            "H1": h1_tf,
        }
    )


def _mock_pa_ob_retest(direction="LONG", entry=214.109, sl=214.002, rr=1.5,
                       framework="ob_retest"):
    """PA object with framework set — for Gate1 ob_retest SL exception tests."""
    daily_bias = "bullish" if direction == "LONG" else "bearish"
    sl_dist = abs(entry - sl)
    tp1 = (entry + sl_dist * rr) if direction == "LONG" else (entry - sl_dist * rr)
    tp = SimpleNamespace(
        direction=direction,
        entry_price=entry,
        stop_loss=sl,
        risk_reward_ratio=rr,
        take_profit_1=tp1,
    )
    reasoning = SimpleNamespace(
        setup_grade="A+",
        daily_bias=SimpleNamespace(direction=daily_bias),
    )
    return SimpleNamespace(reasoning=reasoning, trade_parameters=tp, framework=framework)


class TestGate1OBRestestSLException:
    """Tests for the ob_retest structural SL exception to the sl_floor check.

    Scenario: GBPJPY April 13, 2026 — OB zone 214.023–214.129 (10.6 pips),
    sl_absolute_min=0.118 (11.8 pips). AI-placed SL at 214.002 gives distance 0.107,
    below floor. Both trades were winners. The fix: bypass sl_floor when framework=ob_retest
    and SL is confirmed below ob_low (LONG) or above ob_high (SHORT).
    """

    _GBPJPY_OB_LONG = SimpleNamespace(type="bullish", mitigated=False, low=214.023, high=214.129)
    # GBPJPY config: sl_absolute_min=0.118, sl_buffer_dollars=0.014
    _GBPJPY_RISK = {"sl_absolute_min": 0.118, "sl_buffer_dollars": 0.014}

    def _good_state(self):
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(214.10, 214.12)  # ~2 pip spread — passes Gate3
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "london",
                 "trades_london": 0, "losses_today": 0}
        return mt5, state

    def test_sl_floor_rejection_without_ob_exception(self):
        """Exception disabled: sl_below_minimum_floor must still reject."""
        mt5, state = self._good_state()
        pa = _mock_pa_ob_retest()
        mso = _mock_mso_with_h1_ob(self._GBPJPY_OB_LONG)
        config = {"gate1": {"ob_retest_sl_exception": False}, "risk": self._GBPJPY_RISK}
        denial = check_permissions(pa, mso, state, mt5, config=config)
        assert denial is not None
        assert "sl_below_minimum_floor" in denial.reason

    def test_sl_floor_bypass_for_ob_retest_long(self):
        """GBPJPY Apr-13 exact scenario: OB 214.023–214.129, entry 214.109, SL 214.002.
        sl_distance=0.107 < sl_floor=0.118 but SL is below ob_low → exception allows trade."""
        mt5, state = self._good_state()
        pa = _mock_pa_ob_retest(direction="LONG", entry=214.109, sl=214.002)
        mso = _mock_mso_with_h1_ob(self._GBPJPY_OB_LONG)
        config = {"gate1": {"ob_retest_sl_exception": True}, "risk": self._GBPJPY_RISK}
        denial = check_permissions(pa, mso, state, mt5, config=config)
        assert denial is None

    def test_sl_floor_bypass_for_ob_retest_short(self):
        """SHORT mirror: OB 214.050–214.130, entry 214.060, SL 214.150.
        sl_distance=0.090 < sl_floor=0.118 but SL is above ob_high → exception allows trade."""
        mt5, state = self._good_state()
        ob_short = SimpleNamespace(type="bearish", mitigated=False, low=214.050, high=214.130)
        pa = _mock_pa_ob_retest(direction="SHORT", entry=214.060, sl=214.150)
        mso = _mock_mso_with_h1_ob(ob_short)
        config = {"gate1": {"ob_retest_sl_exception": True}, "risk": self._GBPJPY_RISK}
        denial = check_permissions(pa, mso, state, mt5, config=config)
        assert denial is None

    def test_sl_floor_still_rejects_non_ob_retest(self):
        """Other frameworks (e.g. breaker_retest) are NOT exempt from sl_floor."""
        mt5, state = self._good_state()
        pa = _mock_pa_ob_retest(framework="breaker_retest")
        mso = _mock_mso_with_h1_ob(self._GBPJPY_OB_LONG)
        config = {"gate1": {"ob_retest_sl_exception": True}, "risk": self._GBPJPY_RISK}
        denial = check_permissions(pa, mso, state, mt5, config=config)
        assert denial is not None
        assert "sl_below_minimum_floor" in denial.reason

    def test_sl_floor_still_rejects_if_sl_not_at_ob_boundary(self):
        """ob_retest with exception enabled, but SL is inside OB (not below ob_low) → rejected.
        This guards against using the exception as a blanket bypass for all tight SLs."""
        mt5, state = self._good_state()
        # SL at 214.030 is INSIDE the OB (above ob_low=214.023), not at boundary
        pa = _mock_pa_ob_retest(direction="LONG", entry=214.109, sl=214.030)
        mso = _mock_mso_with_h1_ob(self._GBPJPY_OB_LONG)
        config = {"gate1": {"ob_retest_sl_exception": True}, "risk": self._GBPJPY_RISK}
        denial = check_permissions(pa, mso, state, mt5, config=config)
        assert denial is not None
        assert "sl_below_minimum_floor" in denial.reason

    def test_sl_floor_rejects_wrong_ob_type_for_long(self):
        """LONG trade matching a bearish OB should NOT bypass sl_floor.
        Guards against the exception firing on the wrong structural anchor."""
        mt5, state = self._good_state()
        ob_wrong_type = SimpleNamespace(type="bearish", mitigated=False, low=214.023, high=214.129)
        pa = _mock_pa_ob_retest(direction="LONG", entry=214.109, sl=214.002)
        mso = _mock_mso_with_h1_ob(ob_wrong_type)
        config = {"gate1": {"ob_retest_sl_exception": True}, "risk": self._GBPJPY_RISK}
        denial = check_permissions(pa, mso, state, mt5, config=config)
        assert denial is not None
        assert "sl_below_minimum_floor" in denial.reason

    def test_sl_floor_rejects_wrong_ob_type_for_short(self):
        """SHORT trade matching a bullish OB should NOT bypass sl_floor."""
        mt5, state = self._good_state()
        ob_wrong_type = SimpleNamespace(type="bullish", mitigated=False, low=214.050, high=214.130)
        pa = _mock_pa_ob_retest(direction="SHORT", entry=214.060, sl=214.150)
        mso = _mock_mso_with_h1_ob(ob_wrong_type)
        config = {"gate1": {"ob_retest_sl_exception": True}, "risk": self._GBPJPY_RISK}
        denial = check_permissions(pa, mso, state, mt5, config=config)
        assert denial is not None
        assert "sl_below_minimum_floor" in denial.reason


class TestGate1OBRestestSLTooTightBypass:
    """Tests for the ob_retest exception bypassing the sl_too_tight (1.5*ATR) check.

    Scenario: GBPJPY April 14, 2026 -- same OB 214.023-214.129, M15 ATR ~0.108.
    SL distance 0.13 < 1.5*ATR 0.162 -> sl_too_tight fires.
    With ob_retest exception, the ATR check should be bypassed when SL is
    confirmed structurally placed below the OB boundary.
    """

    _GBPJPY_OB_LONG = SimpleNamespace(type="bullish", mitigated=False, low=214.023, high=214.129)
    _GBPJPY_RISK = {"sl_absolute_min": 0.118, "sl_buffer_dollars": 0.014}
    _REALISTIC_ATR = 0.108  # Real GBPJPY M15 ATR from Apr 14

    def _good_state(self):
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(214.10, 214.12)
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "ny",
                 "trades_ny": 0, "losses_today": 0}
        return mt5, state

    def test_sl_too_tight_bypassed_for_ob_retest_long(self):
        """LONG with adequate sweep margin: SL 0.043 below OB low (0.40 ATR).
        Production uses 0.5 ATR margin; these tests exercise the code default
        of 0.3 ATR (no explicit override in config), so buffer 0.043 > 0.0324."""
        mt5, state = self._good_state()
        # SL=213.980: dist=0.149 (< 1.5*ATR=0.162), buffer=0.043 (test uses 0.3 ATR default: > 0.0324)
        pa = _mock_pa_ob_retest(direction="LONG", entry=214.129, sl=213.980)
        mso = _mock_mso_with_h1_ob(self._GBPJPY_OB_LONG, m15_atr=self._REALISTIC_ATR)
        config = {"gate1": {"ob_retest_sl_exception": True}, "risk": self._GBPJPY_RISK}
        denial = check_permissions(pa, mso, state, mt5, config=config)
        assert denial is None

    def test_sl_too_tight_bypassed_for_ob_retest_short(self):
        """SHORT with adequate sweep margin: SL 0.050 above OB high (0.46 ATR).
        Production uses 0.5 ATR margin; these tests exercise the 0.3 ATR default."""
        mt5, state = self._good_state()
        ob_short = SimpleNamespace(type="bearish", mitigated=False, low=214.050, high=214.130)
        # SL=214.180: dist=0.120 (> floor 0.118, < 1.5*ATR=0.162), buffer=0.050 (> 0.0324 at 0.3 default)
        pa = _mock_pa_ob_retest(direction="SHORT", entry=214.060, sl=214.180)
        mso = _mock_mso_with_h1_ob(ob_short, m15_atr=self._REALISTIC_ATR)
        config = {"gate1": {"ob_retest_sl_exception": True}, "risk": self._GBPJPY_RISK}
        denial = check_permissions(pa, mso, state, mt5, config=config)
        assert denial is None

    def test_sweep_margin_blocks_tight_sl_long(self):
        """LONG with SL only 0.024 below OB low (0.22 ATR < 0.5 ATR production threshold).
        Also < 0.3 ATR code default (0.0324), so the test rejects regardless of
        which threshold is active. Apr-16 XAUUSD scenario: SL too close to OB
        boundary gets swept as liquidity."""
        mt5, state = self._good_state()
        # SL=213.999: buffer=0.024 -- in the retail sweep zone for 0.3 or 0.5 ATR
        pa = _mock_pa_ob_retest(direction="LONG", entry=214.129, sl=213.999)
        mso = _mock_mso_with_h1_ob(self._GBPJPY_OB_LONG, m15_atr=self._REALISTIC_ATR)
        config = {"gate1": {"ob_retest_sl_exception": True}, "risk": self._GBPJPY_RISK}
        denial = check_permissions(pa, mso, state, mt5, config=config)
        assert denial is not None

    def test_sweep_margin_blocks_tight_sl_short(self):
        """SHORT with SL only 0.010 above OB high (0.09 ATR < 0.5 ATR production threshold).
        Also < 0.3 ATR code default. Exception should not apply -- SL is in the
        liquidity sweep zone either way."""
        mt5, state = self._good_state()
        ob_short = SimpleNamespace(type="bearish", mitigated=False, low=214.050, high=214.130)
        # SL=214.140: buffer=0.010 (< 0.0324), dist=0.080 (< floor 0.118)
        pa = _mock_pa_ob_retest(direction="SHORT", entry=214.060, sl=214.140)
        mso = _mock_mso_with_h1_ob(ob_short, m15_atr=self._REALISTIC_ATR)
        config = {"gate1": {"ob_retest_sl_exception": True}, "risk": self._GBPJPY_RISK}
        denial = check_permissions(pa, mso, state, mt5, config=config)
        assert denial is not None

    def test_sl_too_tight_still_blocks_without_exception(self):
        """Exception disabled: sl_too_tight must still reject even for ob_retest."""
        mt5, state = self._good_state()
        pa = _mock_pa_ob_retest(direction="LONG", entry=214.129, sl=213.999)
        mso = _mock_mso_with_h1_ob(self._GBPJPY_OB_LONG, m15_atr=self._REALISTIC_ATR)
        config = {"gate1": {"ob_retest_sl_exception": False}, "risk": self._GBPJPY_RISK}
        denial = check_permissions(pa, mso, state, mt5, config=config)
        assert denial is not None
        assert "sl_too_tight" in denial.reason

    def test_sl_too_tight_still_blocks_non_ob_retest(self):
        """Other frameworks are NOT exempt from sl_too_tight."""
        mt5, state = self._good_state()
        pa = _mock_pa_ob_retest(framework="breaker_retest", entry=214.129, sl=213.999)
        mso = _mock_mso_with_h1_ob(self._GBPJPY_OB_LONG, m15_atr=self._REALISTIC_ATR)
        config = {"gate1": {"ob_retest_sl_exception": True}, "risk": self._GBPJPY_RISK}
        denial = check_permissions(pa, mso, state, mt5, config=config)
        assert denial is not None
        assert "sl_too_tight" in denial.reason

    def test_sl_too_tight_still_blocks_sl_inside_ob(self):
        """SL inside OB (above ob_low for LONG) -- exception must NOT apply."""
        mt5, state = self._good_state()
        # SL at 214.030 is above ob_low=214.023 (inside OB)
        pa = _mock_pa_ob_retest(direction="LONG", entry=214.129, sl=214.030)
        mso = _mock_mso_with_h1_ob(self._GBPJPY_OB_LONG, m15_atr=self._REALISTIC_ATR)
        config = {"gate1": {"ob_retest_sl_exception": True}, "risk": self._GBPJPY_RISK}
        denial = check_permissions(pa, mso, state, mt5, config=config)
        assert denial is not None
        # Could hit sl_floor or sl_too_tight -- either is a valid rejection
        assert "sl_below_minimum_floor" in denial.reason or "sl_too_tight" in denial.reason

    def test_sl_too_tight_still_blocks_wrong_ob_type(self):
        """LONG trade matching a bearish OB should NOT bypass sl_too_tight."""
        mt5, state = self._good_state()
        ob_wrong = SimpleNamespace(type="bearish", mitigated=False, low=214.023, high=214.129)
        pa = _mock_pa_ob_retest(direction="LONG", entry=214.129, sl=213.999)
        mso = _mock_mso_with_h1_ob(ob_wrong, m15_atr=self._REALISTIC_ATR)
        config = {"gate1": {"ob_retest_sl_exception": True}, "risk": self._GBPJPY_RISK}
        denial = check_permissions(pa, mso, state, mt5, config=config)
        assert denial is not None

    def test_generic_sl_too_tight_unchanged(self):
        """Non-OB-retest trade with tight SL still rejected (regression guard)."""
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.0, 2650.1)
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "ny",
                 "trades_ny": 0, "losses_today": 0}
        # SL distance = $5.50, ATR = $5.0, 1.5*ATR = $7.50 -> too tight
        denial = check_permissions(
            _mock_pa(entry=2650.0, sl=2644.5), _mock_mso(m15_atr=5.0), state, mt5,
        )
        assert denial is not None
        assert "sl_too_tight" in denial.reason

    def test_apr13_gbpusd_live_config_structural_sl_bypasses_sl_too_tight_only_for_ob_retest(self):
        """Handoff 16 exact blocker: GBPUSD 14:00 had a structural OB SL
        tighter than 1.5*ATR. The live config should allow that only when the
        framework is ob_retest and the SL has the configured sweep margin.
        """
        from src.utils.config import apply_instrument_overrides

        with Path("config/agent_config.yaml").open("r", encoding="utf-8") as handle:
            cfg = apply_instrument_overrides(yaml.safe_load(handle), "GBPUSD")

        ob = SimpleNamespace(
            type="bullish",
            mitigated=False,
            low=1.26990,
            high=1.27020,
        )
        mso = _mock_mso_with_h1_ob(ob, m15_atr=0.00078)
        state = {"deterministic_bias": "bullish"}

        # SL distance 0.00061 < 1.5*ATR 0.00117, but SL is 0.00041 below
        # ob.low, clearing the live 0.5*ATR sweep-margin requirement.
        ob_retest = _mock_pa_ob_retest(
            direction="LONG",
            entry=1.27010,
            sl=1.26949,
            framework="ob_retest",
        )
        denial = _perm_mod._gate1_safety_checks(
            ob_retest, mso, state, config=cfg, symbol="GBPUSD",
        )
        assert denial is None

        non_ob_retest = _mock_pa_ob_retest(
            direction="LONG",
            entry=1.27010,
            sl=1.26949,
            framework="breaker_re_entry",
        )
        denial = _perm_mod._gate1_safety_checks(
            non_ob_retest, mso, state, config=cfg, symbol="GBPUSD",
        )
        assert denial is not None
        assert "sl_too_tight" in denial.reason

    def test_live_xau_config_blocks_apr16_sweep_zone_but_allows_survivor_margin(
        self, tmp_path, monkeypatch,
    ):
        """Apr 16 XAU: 0.36 ATR sweep hit the tight stop; 0.74 ATR survived."""
        from src.utils.config import apply_instrument_overrides

        log_path = tmp_path / "ob_retest_sl_exception_decisions.jsonl"
        monkeypatch.setattr(
            _perm_mod,
            "OB_RETEST_SL_EXCEPTION_LOG_PATH",
            str(log_path),
        )
        config_path = Path(__file__).resolve().parents[1] / "config" / "agent_config.yaml"
        with config_path.open("r", encoding="utf-8") as handle:
            cfg = apply_instrument_overrides(yaml.safe_load(handle), "XAUUSD")
        cfg.setdefault("deployment", {})["phase"] = 3
        cfg["trading_enabled"] = True
        cfg.setdefault("market_whiteboard_v2", {})["enabled"] = False
        cfg.setdefault("shadow_loggers", {}).setdefault(
            "cross_instrument_correlation_decisions_logger",
            {},
        )["enabled"] = False
        cfg.setdefault("runtime_control", {})["audit_log_path"] = str(
            tmp_path / "runtime_control_atomic_halt_audit.jsonl"
        )
        cfg["runtime_control"]["halt_flag_paths"] = [
            str(tmp_path / "GTOS_HARD_PRODUCTION_HALT.flag"),
            str(tmp_path / "RESEARCH_RUNTIME_HALT.flag"),
            str(tmp_path / "AUTOSTART_DISABLED.flag"),
        ]

        assert cfg["gate1"]["ob_retest_sl_min_buffer_atr"] == 0.5

        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(4789.90, 4790.10)
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "ny",
                 "trades_ny": 0, "losses_today": 0}
        ob = SimpleNamespace(type="bullish", mitigated=False, low=4784.0, high=4790.0)
        mso = _mock_mso_with_h1_ob(ob, m15_atr=10.0)

        swept_stop = _mock_pa_ob_retest(direction="LONG", entry=4790.0, sl=4780.4)
        denial = check_permissions(swept_stop, mso, state, mt5, config=cfg, symbol="XAUUSD")
        assert denial is not None
        assert "sl_too_tight" in denial.reason

        survivor_stop = _mock_pa_ob_retest(direction="LONG", entry=4790.0, sl=4776.6)
        denial = check_permissions(survivor_stop, mso, state, mt5, config=cfg, symbol="XAUUSD")
        assert denial is None

    def test_structural_sl_bypass_logs_override_and_preserved_sweep_margin(
        self, tmp_path, monkeypatch,
    ):
        """Unit 56 / ADR 004: accepted structural bypasses are observable."""
        from src.utils.config import apply_instrument_overrides

        log_path = tmp_path / "ob_retest_sl_exception_decisions.jsonl"
        monkeypatch.setattr(
            _perm_mod,
            "OB_RETEST_SL_EXCEPTION_LOG_PATH",
            str(log_path),
        )
        with Path("config/agent_config.yaml").open("r", encoding="utf-8") as handle:
            cfg = apply_instrument_overrides(yaml.safe_load(handle), "GBPUSD")

        ob = SimpleNamespace(
            type="bullish",
            mitigated=False,
            low=1.26990,
            high=1.27020,
        )
        mso = _mock_mso_with_h1_ob(ob, m15_atr=0.00078)
        state = {"deterministic_bias": "bullish"}
        pa = _mock_pa_ob_retest(
            direction="LONG",
            entry=1.27010,
            sl=1.26949,
            framework="ob_retest",
        )

        denial = _perm_mod._gate1_safety_checks(
            pa, mso, state, config=cfg, symbol="GBPUSD",
        )

        assert denial is None
        row = json.loads(log_path.read_text(encoding="utf-8").splitlines()[-1])
        assert row["gate_context"] == "sl_too_tight"
        assert row["applies"] is True
        assert row["reason"] == "matched_structural_sl_exception"
        assert row["structural_override"] is True
        assert row["sweep_margin_status"] == "PASS"
        assert "sl_too_tight" in row["bypassed_gates"]
        assert "sweep_margin_min_buffer_atr" in row["preserved_gates"]
        assert "sweep_margin_min_buffer_atr" not in row["bypassed_gates"]

    def test_apr16_sweep_zone_rejection_logs_sweep_margin_failure(
        self, tmp_path, monkeypatch,
    ):
        """Unit 56 / ADR 004: adverse sweep-margin evidence stays a block."""
        from src.utils.config import apply_instrument_overrides

        log_path = tmp_path / "ob_retest_sl_exception_decisions.jsonl"
        monkeypatch.setattr(
            _perm_mod,
            "OB_RETEST_SL_EXCEPTION_LOG_PATH",
            str(log_path),
        )
        config_path = Path(__file__).resolve().parents[1] / "config" / "agent_config.yaml"
        with config_path.open("r", encoding="utf-8") as handle:
            cfg = apply_instrument_overrides(yaml.safe_load(handle), "XAUUSD")
        cfg.setdefault("deployment", {})["phase"] = 3
        cfg["trading_enabled"] = True
        cfg.setdefault("market_whiteboard_v2", {})["enabled"] = False
        cfg.setdefault("shadow_loggers", {}).setdefault(
            "cross_instrument_correlation_decisions_logger",
            {},
        )["enabled"] = False
        cfg.setdefault("runtime_control", {})["audit_log_path"] = str(
            tmp_path / "runtime_control_atomic_halt_audit.jsonl"
        )
        cfg["runtime_control"]["halt_flag_paths"] = [
            str(tmp_path / "GTOS_HARD_PRODUCTION_HALT.flag"),
            str(tmp_path / "RESEARCH_RUNTIME_HALT.flag"),
            str(tmp_path / "AUTOSTART_DISABLED.flag"),
        ]

        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(4789.90, 4790.10)
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "ny",
                 "trades_ny": 0, "losses_today": 0}
        ob = SimpleNamespace(type="bullish", mitigated=False, low=4784.0, high=4790.0)
        mso = _mock_mso_with_h1_ob(ob, m15_atr=10.0)
        swept_stop = _mock_pa_ob_retest(direction="LONG", entry=4790.0, sl=4780.4)

        denial = check_permissions(swept_stop, mso, state, mt5, config=cfg, symbol="XAUUSD")

        assert denial is not None
        assert "sl_too_tight" in denial.reason
        row = json.loads(log_path.read_text(encoding="utf-8").splitlines()[-1])
        assert row["gate_context"] == "sl_too_tight"
        assert row["applies"] is False
        assert row["reason"] == "sweep_margin_too_small"
        assert row["structural_override"] is False
        assert row["sweep_margin_status"] == "FAIL"
        assert row["bypassed_gates"] == []
        assert row["preserved_gates"] == ["sweep_margin_min_buffer_atr"]
        assert row["sl_boundary_buffer"] == pytest.approx(3.6)
        assert row["min_buffer_required"] == pytest.approx(5.0)


class TestGate1TouchCountRejection:
    """Multi-touch OB rejection gate (KEEP-at-2 default 2026-04-25).

    Evidence — TWO orthogonal lines:
      (1) Founding population-walk: Touch-1 OB retest WR = 72.7%
          (n=23,575) vs Touch-2+ = 31.5% (n=82,572). Default threshold
          ``>= 2``.
      (2) Wave 1 audit A11 (research/touch_count_audit/, see
          analyze_output.txt + stats_output.txt) suggested LOOSEN_TO_3
          on pooled data. A19 reviewer pass (REVIEWER_PASS.md)
          REJECTED LOOSEN_TO_3 with HIGH confidence: H1/H2 regime
          stratification showed touch=2 advantage REVERSES in Mar-Apr
          2026 (touch=2 Exp R = -0.688R, n=8). Bonferroni p=1.0 across
          all pairs; ~10% statistical power for δ=0.20R at n=98. Default
          KEPT at 2 for Monday FTMO challenge launch; ADR-005 shadow
          logger collects live distribution for ≥6 weeks before any
          re-evaluation.

    Default threshold 2 (REJECT touches >= 2). Knob:
    ``gate1.touch_count_reject_threshold`` in config — flip via 1-line
    config change once we have ≥30 production rejection events.

    Gate placed before SL/TP geometry checks so stale zones are cut
    early. Behavior: reject any trade whose target H1 OB has
    ``touch_count >= threshold``.
    """

    # Valid, generous-SL OB-retest setup that passes all downstream gates.
    # Using XAUUSD-style prices with a comfortable SL so SL gates don't fire.
    _ENTRY = 2650.0
    _SL = 2630.0            # $20 SL — above floor ($5) and 1.5*ATR ($4.5)
    _OB_LOW = 2648.0
    _OB_HIGH = 2652.0
    _M15_ATR = 3.0

    def _good_state(self):
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.0, 2650.18)
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "london",
                 "trades_london": 0, "losses_today": 0}
        return mt5, state

    def _ob(self, touch_count: int):
        return SimpleNamespace(
            type="bullish", mitigated=False,
            low=self._OB_LOW, high=self._OB_HIGH,
            touch_count=touch_count,
        )

    def _pa(self):
        return _mock_pa_ob_retest(
            direction="LONG", entry=self._ENTRY, sl=self._SL, rr=1.5,
        )

    def test_touch_count_0_passes(self):
        """Fresh OB (0 touches) — must pass through to (and past) the gate."""
        mt5, state = self._good_state()
        mso = _mock_mso_with_h1_ob(self._ob(touch_count=0), m15_atr=self._M15_ATR)
        denial = check_permissions(self._pa(), mso, state, mt5)
        assert denial is None

    def test_touch_count_1_passes(self):
        """First retest (1 touch) — below default threshold of 2; must pass."""
        mt5, state = self._good_state()
        mso = _mock_mso_with_h1_ob(self._ob(touch_count=1), m15_atr=self._M15_ATR)
        denial = check_permissions(self._pa(), mso, state, mt5)
        assert denial is None

    def test_touch_count_2_rejects_under_default_keep_at_2(self):
        """A19 KEEP-at-2 (2026-04-25): default threshold remains 2 for
        Monday FTMO launch despite A11's LOOSEN_TO_3 suggestion. The
        reviewer pass found touch=2 advantage REVERSES in H2-2026 (touch=2
        Exp R = -0.688R, n=8). touch=2 must REJECT under default threshold
        2 (touches >= threshold)."""
        mt5, state = self._good_state()
        mso = _mock_mso_with_h1_ob(self._ob(touch_count=2), m15_atr=self._M15_ATR)
        denial = check_permissions(self._pa(), mso, state, mt5)
        assert denial is not None, (
            f"touch=2 must REJECT under default threshold 2, got pass"
        )
        assert denial.reason == "touch_count_too_high"
        assert denial.details["touch_count"] == 2
        assert denial.details["threshold"] == 2

    def test_touch_count_3_rejects_under_default(self):
        """touch=3 well above default threshold 2; must reject."""
        mt5, state = self._good_state()
        mso = _mock_mso_with_h1_ob(self._ob(touch_count=3), m15_atr=self._M15_ATR)
        denial = check_permissions(self._pa(), mso, state, mt5)
        assert denial is not None
        assert denial.reason == "touch_count_too_high"
        assert denial.details["touch_count"] == 3
        assert denial.details["threshold"] == 2

    def test_touch_count_4_rejects_under_default(self):
        """touch=4 — well above default threshold; must reject."""
        mt5, state = self._good_state()
        mso = _mock_mso_with_h1_ob(self._ob(touch_count=4), m15_atr=self._M15_ATR)
        denial = check_permissions(self._pa(), mso, state, mt5)
        assert denial is not None
        assert denial.reason == "touch_count_too_high"
        assert denial.details["touch_count"] == 4
        assert denial.details["threshold"] == 2

    @pytest.mark.parametrize(
        "touches, threshold, should_reject",
        [
            # threshold == 1 (extreme tight): only touch=0 passes
            (0, 1, False),
            (1, 1, True),
            (2, 1, True),
            # threshold == 2 (default — A19 KEEP-at-2 verdict 2026-04-25):
            # founding-evidence-aligned, touch=1 passes, touch>=2 rejects
            (1, 2, False),
            (2, 2, True),
            (3, 2, True),
            # threshold == 3 (LOOSEN_TO_3 — REJECTED by A19 reviewer pass for
            # Monday but knob still functions; flip is 1-line config change
            # once shadow logger collects ≥30 production rejection events)
            (1, 3, False),
            (2, 3, False),
            (3, 3, True),
            (4, 3, True),
            # threshold == 4: even touch=3 passes
            (2, 4, False),
            (3, 4, False),
            (4, 4, True),
        ],
    )
    def test_touch_count_threshold_knob_parametric(
        self, touches: int, threshold: int, should_reject: bool
    ):
        """Parametric coverage of gate1.touch_count_reject_threshold knob.

        Verifies the gate's threshold semantics across the matrix of
        (touch_count, threshold) pairs the CEO might dial through. Asserts
        ``touches >= threshold`` rejects, ``touches < threshold`` passes.
        Covers default threshold=2 (Monday-FTMO ship), threshold=3
        (A19-rejected LOOSEN_TO_3 — knob still functions for future flips),
        threshold=1 (paranoid override), threshold=4 (further loosening).
        """
        mt5, state = self._good_state()
        mso = _mock_mso_with_h1_ob(self._ob(touch_count=touches), m15_atr=self._M15_ATR)
        cfg = {"gate1": {"touch_count_reject_threshold": threshold}}
        denial = check_permissions(self._pa(), mso, state, mt5, config=cfg)
        if should_reject:
            assert denial is not None, (
                f"touches={touches}, threshold={threshold}: expected reject, got pass"
            )
            assert denial.reason == "touch_count_too_high"
            assert denial.details["touch_count"] == touches
            assert denial.details["threshold"] == threshold
        else:
            assert denial is None, (
                f"touches={touches}, threshold={threshold}: expected pass, "
                f"got denial: {denial}"
            )

    def test_touch_count_default_when_config_omits_knob(self):
        """When config has no gate1.touch_count_reject_threshold, default is 2.

        Critical invariant: existing agent_config.yaml installs without the
        knob must continue to work; default 2 (A19 KEEP-at-2) is baked
        into the gate.
        """
        mt5, state = self._good_state()
        # touch=1 must pass with no config dict at all
        mso1 = _mock_mso_with_h1_ob(self._ob(touch_count=1), m15_atr=self._M15_ATR)
        denial1 = check_permissions(self._pa(), mso1, state, mt5, config=None)
        assert denial1 is None
        # touch=2 must REJECT under default threshold 2
        mso = _mock_mso_with_h1_ob(self._ob(touch_count=2), m15_atr=self._M15_ATR)
        denial = check_permissions(self._pa(), mso, state, mt5, config=None)
        assert denial is not None
        assert denial.details["threshold"] == 2
        # Empty gate1 dict still defaults to 2
        denial2 = check_permissions(self._pa(), mso, state, mt5, config={"gate1": {}})
        assert denial2 is not None
        assert denial2.details["threshold"] == 2
        # touch=3 still rejects with default
        mso3 = _mock_mso_with_h1_ob(self._ob(touch_count=3), m15_atr=self._M15_ATR)
        denial3 = check_permissions(self._pa(), mso3, state, mt5, config={"gate1": {}})
        assert denial3 is not None
        assert denial3.details["threshold"] == 2


# ---------------------------------------------------------------------------
# Liquidity-cluster SL gate tests (handoff 19 / Apr 16 regression)
# ---------------------------------------------------------------------------


def _mock_pool(pool_type: str, price: float, side: str):
    """Build a minimal LiquidityPool-like object for the gate."""
    return SimpleNamespace(type=pool_type, price=price, side=side)


def _mock_mso_with_pools(pools, m15_atr: float = 1.0):
    """MSO stub with M15 ATR and liquidity_pools for the cluster gate."""
    return SimpleNamespace(
        timeframes={"M15": SimpleNamespace(atr_14=m15_atr)},
        liquidity_pools=pools,
    )


def _pa_for_cluster(direction="LONG", entry=4789.38, sl=4779.38):
    """PA object sized so sl_floor/sl_too_tight do NOT fire downstream.

    Uses wide SL (dist=10.0) and ATR=6.0 so 1.5*ATR=9.0 <= sl_dist=10.0.
    This lets full check_permissions() pipeline tests measure the
    liquidity-cluster gate in isolation.
    """
    daily_bias = "bullish" if direction == "LONG" else "bearish"
    sl_dist = abs(entry - sl)
    tp1 = entry + sl_dist * 1.5 if direction == "LONG" else entry - sl_dist * 1.5
    tp = SimpleNamespace(
        direction=direction,
        entry_price=entry,
        stop_loss=sl,
        risk_reward_ratio=1.5,
        take_profit_1=tp1,
    )
    reasoning = SimpleNamespace(
        setup_grade="A+",
        daily_bias=SimpleNamespace(direction=daily_bias),
    )
    return SimpleNamespace(reasoning=reasoning, trade_parameters=tp, framework="ob_retest")


@pytest.fixture
def _isolate_liquidity_shadow_log(tmp_path, monkeypatch):
    """Redirect the shadow-log cwd so tests never write to real shadow_logs/."""
    monkeypatch.chdir(tmp_path)
    yield tmp_path


class TestGate1LiquidityCluster:
    """Deterministic SL-behind-liquidity-cluster gate.

    Apr 16 NY XAUUSD -1R: SL 4788.08 sat 0.05 pts below an equal_lows pool
    @ 4788.13. Price swept to 4785.05 and took the stop. MSO had the pool
    data but no gate consumed it. This test class covers:
      1. Apr 16 regression (enabled -> reject)
      2. Far pool (passes even when enabled)
      3. Wrong-side pool (ignored)
      4. SHORT variant
      5. SHORT wrong-side pool
      6. Empty pools list (pass)
      7. MSO without liquidity_pools attr (pass)
      8. Zero ATR (pass silently, no shadow log)
      9. Disabled flag still writes shadow log but does not reject
     10. Multiple pools — first violating pool wins
     11. Unsupported pool type (e.g. FVG-like) ignored
    """

    _GATE_CFG_ON = {
        "gate1": {
            "sl_liquidity_cluster_enabled": True,
            "sl_liquidity_cluster_margin_atr": 0.5,
        }
    }
    _GATE_CFG_OFF = {
        "gate1": {
            "sl_liquidity_cluster_enabled": False,
            "sl_liquidity_cluster_margin_atr": 0.5,
        }
    }

    def test_agent_config_wires_apr17_liquidity_gate_shadow_then_enforceable(
            self, _isolate_liquidity_shadow_log):
        """Live config keeps Apr17 liquidity gate shadow-only but enforceable."""
        from src.utils.config import apply_instrument_overrides

        config_path = Path(__file__).resolve().parents[1] / "config" / "agent_config.yaml"
        with config_path.open("r", encoding="utf-8") as handle:
            cfg = apply_instrument_overrides(yaml.safe_load(handle), "XAUUSD")
        assert cfg["gate1"]["sl_liquidity_cluster_enabled"] is False
        assert cfg["gate1"]["sl_liquidity_cluster_margin_atr"] == 0.5

        pools = [
            _mock_pool("asian_low", 4786.65, "low"),
            _mock_pool("london_low", 4787.44, "low"),
            _mock_pool("equal_lows", 4788.13, "low"),
        ]
        mso = _mock_mso_with_pools(pools, m15_atr=6.7291)
        pa = _pa_for_cluster(direction="LONG", entry=4796.28, sl=4786.65)

        denial = _reject_if_sl_behind_liquidity_cluster(
            pa, pa.trade_parameters, mso, config=cfg,
        )
        assert denial is None
        log_file = (
            Path(_isolate_liquidity_shadow_log)
            / "shadow_logs"
            / "liquidity_distance_log.jsonl"
        )
        records = [
            json.loads(line)
            for line in log_file.read_text(encoding="utf-8").splitlines()
        ]
        assert any(r["decision"] == "would_reject" for r in records)

        cfg["gate1"]["sl_liquidity_cluster_enabled"] = True
        denial = _reject_if_sl_behind_liquidity_cluster(
            pa, pa.trade_parameters, mso, config=cfg,
        )
        assert denial is not None
        assert denial.reason == "sl_behind_liquidity_cluster"
        assert denial.details["pool_type"] == "asian_low"

    def _good_state(self):
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(4789.0, 4789.18)
        state = {"daily_pnl_pct": 0, "trades_today": 0,
                 "current_kill_zone": "ny", "trades_ny": 0, "losses_today": 0}
        return mt5, state

    # --- 1. Apr 16 regression -------------------------------------------------

    def test_liquidity_gate_apr16_regression(self, _isolate_liquidity_shadow_log):
        """LONG SL 4779.38, equal_lows pool @ 4779.43 (0.05 above SL).
        M15 ATR=6.0 -> margin=3.0. Distance 0.05 << 3.0 -> reject when enabled."""
        mt5, state = self._good_state()
        # Pool is at 4779.43, 0.05 pts above SL
        pools = [_mock_pool("equal_lows", 4779.43, "low")]
        mso = _mock_mso_with_pools(pools, m15_atr=6.0)
        pa = _pa_for_cluster(direction="LONG", entry=4789.38, sl=4779.38)
        denial = check_permissions(pa, mso, state, mt5, config=self._GATE_CFG_ON)
        assert denial is not None
        assert denial.reason == "sl_behind_liquidity_cluster"
        assert denial.details["pool_type"] == "equal_lows"
        assert denial.details["pool_price"] == 4779.43
        assert denial.details["direction"] == "LONG"
        # Shadow log written
        log_file = Path(_isolate_liquidity_shadow_log) / "shadow_logs" / "liquidity_distance_log.jsonl"
        assert log_file.exists()
        records = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()]
        assert any(r["decision"] == "reject" for r in records)

    # --- 1b. Apr 16 REAL trade-record regression -----------------------------

    def test_liquidity_gate_apr16_real_trade_record(self, _isolate_liquidity_shadow_log):
        """REAL Apr 16 NY XAUUSD numbers from knowledge_base/trade_records/.

        Handoff 19 misreported entry/SL. Actual trade:
          entry=4796.28, SL=4786.65, direction=LONG, M15 ATR=6.7291
          asian_low pool @ 4786.65 (sits EXACTLY on the SL)
          london_low pool @ 4787.44
          equal_lows pool  @ 4788.13
        margin_required = 6.7291 * 0.5 = 3.36.
        asian_low distance=0.00 -> most egregious violator, returned first.
        Gate MUST reject with pool_type='asian_low'.
        """
        mt5, state = self._good_state()
        mt5.set_tick(4796.20, 4796.36)
        pools = [
            _mock_pool("asian_low",   4786.65, "low"),
            _mock_pool("london_low",  4787.44, "low"),
            _mock_pool("equal_lows",  4788.13, "low"),
        ]
        mso = _mock_mso_with_pools(pools, m15_atr=6.7291)
        pa = _pa_for_cluster(direction="LONG", entry=4796.28, sl=4786.65)
        denial = check_permissions(pa, mso, state, mt5, config=self._GATE_CFG_ON)
        assert denial is not None, "Liquidity gate must block the real Apr 16 trade"
        assert denial.reason == "sl_behind_liquidity_cluster"
        # asian_low sits on the SL — it's iterated first and is the most egregious
        assert denial.details["pool_type"] == "asian_low"
        assert denial.details["pool_price"] == 4786.65
        assert denial.details["direction"] == "LONG"
        # Shadow log records the decision as 'reject'
        log_file = Path(_isolate_liquidity_shadow_log) / "shadow_logs" / "liquidity_distance_log.jsonl"
        assert log_file.exists()
        records = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()]
        assert any(r["decision"] == "reject" for r in records)

    # --- 2. Far pool passes (LONG) -------------------------------------------

    def test_liquidity_gate_long_far_pool_passes(self, _isolate_liquidity_shadow_log):
        """Pool is far enough that gate passes even when enabled."""
        mt5, state = self._good_state()
        # Pool 10 pts below SL, margin 3.0 -> distance 10 > 3.0 -> pass
        pools = [_mock_pool("equal_lows", 4769.38, "low")]
        mso = _mock_mso_with_pools(pools, m15_atr=6.0)
        pa = _pa_for_cluster(direction="LONG", entry=4789.38, sl=4779.38)
        denial = check_permissions(pa, mso, state, mt5, config=self._GATE_CFG_ON)
        assert denial is None

    # --- 3. Wrong-side pool (LONG, pool above entry) is ignored --------------

    def test_liquidity_gate_long_pool_above_entry_ignored(self, _isolate_liquidity_shadow_log):
        """LONG: pool above entry is not a same-side cluster — ignored."""
        mt5, state = self._good_state()
        # Pool at 4800 (above entry 4789.38) — ignored regardless of distance
        pools = [_mock_pool("equal_highs", 4800.0, "high")]
        mso = _mock_mso_with_pools(pools, m15_atr=6.0)
        pa = _pa_for_cluster(direction="LONG", entry=4789.38, sl=4779.38)
        denial = check_permissions(pa, mso, state, mt5, config=self._GATE_CFG_ON)
        assert denial is None

    # --- 4. SHORT rejection ---------------------------------------------------

    def test_liquidity_gate_short_reject(self, _isolate_liquidity_shadow_log):
        """SHORT: SL above entry, equal_highs pool between entry and SL -> reject."""
        mt5, state = self._good_state()
        # SHORT entry=100, sl=101 (dist=1.0); pool equal_highs @ 100.9 (0.1 below SL)
        # Use a config that allows such small SL for the test by setting
        # ATR tiny so 1.5*ATR < sl_dist AND sl_floor low enough.
        mt5.set_tick(99.9, 100.1)
        pools = [_mock_pool("equal_highs", 100.9, "high")]
        mso = _mock_mso_with_pools(pools, m15_atr=0.5)  # 1.5*ATR=0.75 < sl_dist=1.0
        # margin = 0.5*0.5 = 0.25; distance 100.9 to 101 = 0.1 < 0.25 -> reject
        pa = _pa_for_cluster(direction="SHORT", entry=100.0, sl=101.0)
        cfg = {
            "gate1": {
                "sl_liquidity_cluster_enabled": True,
                "sl_liquidity_cluster_margin_atr": 0.5,
            },
            "risk": {"sl_absolute_min": 0.5, "max_spread_cents": 30},
        }
        denial = check_permissions(pa, mso, state, mt5, config=cfg)
        assert denial is not None
        assert denial.reason == "sl_behind_liquidity_cluster"
        assert denial.details["direction"] == "SHORT"
        assert denial.details["pool_type"] == "equal_highs"

    # --- 5. SHORT wrong-side pool (below entry) ignored ----------------------

    def test_liquidity_gate_short_pool_below_entry_ignored(self, _isolate_liquidity_shadow_log):
        """SHORT: pool below entry is not relevant — ignored."""
        pools = [_mock_pool("equal_lows", 4770.0, "low")]
        mso = _mock_mso_with_pools(pools, m15_atr=6.0)
        pa = _pa_for_cluster(direction="SHORT", entry=4789.38, sl=4799.38)
        denial = _reject_if_sl_behind_liquidity_cluster(pa, pa.trade_parameters, mso,
                                                        config=self._GATE_CFG_ON)
        assert denial is None

    # --- 6. Empty pools list passes silently ---------------------------------

    def test_liquidity_gate_empty_pools_passes(self, _isolate_liquidity_shadow_log):
        mso = _mock_mso_with_pools([], m15_atr=6.0)
        pa = _pa_for_cluster()
        denial = _reject_if_sl_behind_liquidity_cluster(pa, pa.trade_parameters, mso,
                                                        config=self._GATE_CFG_ON)
        assert denial is None

    # --- 7. MSO without liquidity_pools attr passes --------------------------

    def test_liquidity_gate_mso_without_liquidity_pools_attr(self, _isolate_liquidity_shadow_log):
        """Gate must not crash if the MSO lacks the liquidity_pools attr."""
        mso = SimpleNamespace(timeframes={"M15": SimpleNamespace(atr_14=6.0)})
        pa = _pa_for_cluster()
        denial = _reject_if_sl_behind_liquidity_cluster(pa, pa.trade_parameters, mso,
                                                        config=self._GATE_CFG_ON)
        assert denial is None

    # --- 8. Zero ATR returns None silently and writes no shadow log ----------

    def test_liquidity_gate_zero_atr_no_log(self, _isolate_liquidity_shadow_log):
        """If M15 ATR is 0 the gate is a no-op (and writes no shadow log)."""
        pools = [_mock_pool("equal_lows", 4779.43, "low")]
        mso = _mock_mso_with_pools(pools, m15_atr=0.0)
        pa = _pa_for_cluster(direction="LONG", entry=4789.38, sl=4779.38)
        denial = _reject_if_sl_behind_liquidity_cluster(pa, pa.trade_parameters, mso,
                                                        config=self._GATE_CFG_ON)
        assert denial is None
        log_file = Path(_isolate_liquidity_shadow_log) / "shadow_logs" / "liquidity_distance_log.jsonl"
        assert not log_file.exists()

    # --- 9. Disabled flag: shadow log written, no reject ---------------------

    def test_liquidity_gate_disabled_still_logs(self, _isolate_liquidity_shadow_log):
        """gate1.sl_liquidity_cluster_enabled=False -> never rejects, but
        the shadow log captures 'would_reject' decisions for CEO review."""
        pools = [_mock_pool("equal_lows", 4779.43, "low")]
        mso = _mock_mso_with_pools(pools, m15_atr=6.0)
        pa = _pa_for_cluster(direction="LONG", entry=4789.38, sl=4779.38)
        denial = _reject_if_sl_behind_liquidity_cluster(pa, pa.trade_parameters, mso,
                                                        config=self._GATE_CFG_OFF)
        assert denial is None
        log_file = Path(_isolate_liquidity_shadow_log) / "shadow_logs" / "liquidity_distance_log.jsonl"
        assert log_file.exists()
        records = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()]
        assert any(r["decision"] == "would_reject" for r in records)

    # --- 10. Multiple pools — first violating pool wins ----------------------

    def test_liquidity_gate_multiple_pools_first_violation(self, _isolate_liquidity_shadow_log):
        """With pdl far (no violation) and equal_lows + session_low both violating,
        the FIRST violating pool (equal_lows per MSO iteration order) is reported."""
        pools = [
            _mock_pool("pdl", 4700.0, "low"),         # far, not violating
            _mock_pool("equal_lows", 4779.43, "low"),  # violating, first in order
            _mock_pool("session_low", 4779.50, "low"),  # also violating
        ]
        mso = _mock_mso_with_pools(pools, m15_atr=6.0)
        pa = _pa_for_cluster(direction="LONG", entry=4789.38, sl=4779.38)
        denial = _reject_if_sl_behind_liquidity_cluster(pa, pa.trade_parameters, mso,
                                                        config=self._GATE_CFG_ON)
        assert denial is not None
        assert denial.details["pool_type"] == "equal_lows"
        assert denial.details["pool_price"] == 4779.43

    # --- 11. Unsupported pool type ignored -----------------------------------

    def test_liquidity_gate_unsupported_pool_type_ignored(self, _isolate_liquidity_shadow_log):
        """A pool with a type NOT in _LIQUIDITY_CLUSTER_POOL_TYPES is ignored.

        The recognized set is equal_highs/lows, PDH/PDL, asian/session/london
        high/low. Anything else (e.g. hypothetical fvg pool) passes silently.
        """
        pools = [_mock_pool("fvg_high", 4779.43, "low")]
        mso = _mock_mso_with_pools(pools, m15_atr=6.0)
        pa = _pa_for_cluster(direction="LONG", entry=4789.38, sl=4779.38)
        denial = _reject_if_sl_behind_liquidity_cluster(pa, pa.trade_parameters, mso,
                                                        config=self._GATE_CFG_ON)
        assert denial is None


# ---------------------------------------------------------------------------
# _find_target_ob tolerance tests (handoff 19 / sl_buffer_dollars)
# ---------------------------------------------------------------------------


class TestFindTargetOBTolerance:
    """_find_target_ob applies a risk_cfg.sl_buffer_dollars tolerance when matching.

    Entry one tick outside the OB high should still map to the OB when the
    tolerance is set; entry well outside must not match.
    """

    def test_entry_just_above_ob_high_matches_with_tolerance(self):
        """OB high=214.129; entry=214.139 (0.01 above). sl_buffer_dollars=0.014
        extends the match band, so the OB is returned."""
        ob = SimpleNamespace(
            type="bullish", mitigated=False,
            low=214.023, high=214.129, touch_count=1,
        )
        mso = _mock_mso_with_h1_ob(ob, m15_atr=0.1)
        tp = SimpleNamespace(direction="LONG", entry_price=214.139,
                             stop_loss=213.99, take_profit_1=214.3)
        matched = _find_target_ob(tp, mso, risk_cfg={"sl_buffer_dollars": 0.014})
        assert matched is ob

    def test_entry_far_below_ob_low_no_match(self):
        """Entry 0.05 below OB low; tolerance is only 0.014 -> no match."""
        ob = SimpleNamespace(
            type="bullish", mitigated=False,
            low=214.023, high=214.129, touch_count=1,
        )
        mso = _mock_mso_with_h1_ob(ob, m15_atr=0.1)
        tp = SimpleNamespace(direction="LONG", entry_price=213.973,
                             stop_loss=213.8, take_profit_1=214.3)
        matched = _find_target_ob(tp, mso, risk_cfg={"sl_buffer_dollars": 0.014})
        assert matched is None


# ---------------------------------------------------------------------------
# Gate 0: deployment.phase enforcement (T0.2 / Q014)
# ---------------------------------------------------------------------------


class TestGate0DeploymentPhase:
    """deployment.phase config flag enforcement.

    Mapping (CEO-approved 2026-04-18):
      phase == 1 -> reject "deployment_phase_1_block_all_orders"
      phase == 2 -> reject "deployment_phase_2_log_only"
      phase == 3 -> pass through (current live FTMO demo)
      missing / non-int / unknown -> reject "deployment_phase_invalid" (fail-closed)

    Gate 0 runs BEFORE Gate 3 circuit breakers, so a misconfig cannot be masked
    by an unrelated earlier rejection reason.
    """

    def _good_state(self):
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "london",
                 "trades_london": 0, "losses_today": 0}
        return mt5, state

    def test_phase_1_blocks_all_orders(self):
        mt5, state = self._good_state()
        # Otherwise-valid passing setup; Gate 0 must fire first.
        denial = check_permissions(
            _mock_pa(grade="A", entry=2650.0, sl=2640.0, rr=1.5, daily_bias="bullish"),
            _mock_mso(m15_atr=3.0), state, mt5,
            config={"deployment": {"phase": 1}},
        )
        assert denial is not None
        assert denial.gate == "gate0_deployment_phase"
        assert denial.reason == "deployment_phase_1_block_all_orders"
        assert denial.details["phase"] == 1

    def test_phase_2_log_only(self):
        mt5, state = self._good_state()
        denial = check_permissions(
            _mock_pa(grade="A", entry=2650.0, sl=2640.0, rr=1.5, daily_bias="bullish"),
            _mock_mso(m15_atr=3.0), state, mt5,
            config={"deployment": {"phase": 2}},
        )
        assert denial is not None
        assert denial.gate == "gate0_deployment_phase"
        assert denial.reason == "deployment_phase_2_log_only"
        assert denial.details["phase"] == 2

    def test_phase_3_passes_through(self):
        """Zero behavior delta at phase=3 — an otherwise-passing setup must still pass.

        This is the live-system invariant: GTOS is on phase=3 as of 2026-04-18.
        """
        mt5, state = self._good_state()
        denial = check_permissions(
            _mock_pa(grade="A", entry=2650.0, sl=2640.0, rr=1.5, daily_bias="bullish"),
            _mock_mso(m15_atr=3.0), state, mt5,
            config={"deployment": {"phase": 3}},
        )
        assert denial is None

    def test_missing_deployment_key_fails_closed(self):
        """No ``deployment`` block at all -> gate fails closed.

        Bypasses the conftest shim by calling the unwrapped real gate (exposed
        on the module as ``_REAL_DEPLOYMENT_PHASE_GATE``) so the real
        fail-closed logic runs even though the shim would otherwise mask the
        missing-key case.
        """
        real_gate = _perm_mod._REAL_DEPLOYMENT_PHASE_GATE
        denial_empty = real_gate({})
        assert denial_empty is not None
        assert denial_empty.gate == "gate0_deployment_phase"
        assert denial_empty.reason == "deployment_phase_invalid"

        denial_none = real_gate(None)
        assert denial_none is not None
        assert denial_none.gate == "gate0_deployment_phase"
        assert denial_none.reason == "deployment_phase_invalid"

        denial_wrong_type = real_gate({"deployment": "not_a_dict"})
        assert denial_wrong_type is not None
        assert denial_wrong_type.gate == "gate0_deployment_phase"
        assert denial_wrong_type.reason == "deployment_phase_invalid"

    def test_invalid_phase_value_fails_closed(self):
        """Non-int or unknown int -> fail closed with deployment_phase_invalid.

        Covers two fail-closed cases: a string value (``"live"``) and an unknown
        integer (``99``). Both must reject with the same reason string so the
        CEO's alert rule can match a single pattern. Each case also asserts its
        distinct ``details["reason"]`` sub-key (``"non_int"`` vs
        ``"unknown_value"``) so a regression that collapses the two branches is
        caught — the top-level reason alone cannot distinguish them.
        """
        mt5, state = self._good_state()
        denial_str = check_permissions(
            _mock_pa(grade="A", entry=2650.0, sl=2640.0, rr=1.5, daily_bias="bullish"),
            _mock_mso(m15_atr=3.0), state, mt5,
            config={"deployment": {"phase": "live"}},
        )
        assert denial_str is not None
        assert denial_str.gate == "gate0_deployment_phase"
        assert denial_str.reason == "deployment_phase_invalid"
        assert denial_str.details["reason"] == "non_int"
        assert denial_str.details["phase"] == "live"

        denial_99 = check_permissions(
            _mock_pa(grade="A", entry=2650.0, sl=2640.0, rr=1.5, daily_bias="bullish"),
            _mock_mso(m15_atr=3.0), state, mt5,
            config={"deployment": {"phase": 99}},
        )
        assert denial_99 is not None
        assert denial_99.gate == "gate0_deployment_phase"
        assert denial_99.reason == "deployment_phase_invalid"
        assert denial_99.details["reason"] == "unknown_value"
        assert denial_99.details["phase"] == 99

    def test_gate_0_fires_before_gate_3_circuit_breaker(self):
        """Ordering invariant: Gate 0 must fire before Gate 3.

        Constructs a session state that would ALSO trip Gate 3 (daily loss
        limit exceeded + mt5 disconnected — two separate circuit breakers)
        combined with ``deployment.phase == 1``. If the gate ordering ever
        regresses so Gate 3 runs first, the denial would carry
        ``gate3_circuit_breaker`` instead of ``gate0_deployment_phase`` and
        this test would fail. Locking the order keeps a misconfig diagnostic
        from being masked by an unrelated circuit-breaker reason.
        """
        mt5 = MockMT5()
        # Deliberately DO NOT connect mt5 so is_connected() returns False
        # (a Gate 3 trigger). Also set daily loss past the 4% cap and carry
        # stale values for the removed kz/daily-loss counter gates — these
        # should NOT gate under T2.8, but we include them to make the test
        # resistant to accidental gate reintroductions.
        state = {
            "daily_pnl_pct": -5.0,          # would trip Gate 3 daily_loss_limit
            "losses_today": 99,              # removed under T2.8 (ignored)
            "current_kill_zone": "london",
            "trades_london": 5,              # removed under T2.8 (ignored)
            "trades_today": 0,
        }
        denial = check_permissions(
            _mock_pa(grade="A", entry=2650.0, sl=2640.0, rr=1.5, daily_bias="bullish"),
            _mock_mso(m15_atr=3.0), state, mt5,
            config={"deployment": {"phase": 1}},
        )
        assert denial is not None
        assert denial.gate == "gate0_deployment_phase", (
            f"Gate 0 must fire before Gate 3 — got {denial.gate} / {denial.reason}"
        )
        assert denial.reason == "deployment_phase_1_block_all_orders"
        assert denial.details["phase"] == 1


# ---------------------------------------------------------------------------
# Gate 0.5: per-instrument trading_enabled flag (observer-mode formalization)
# ---------------------------------------------------------------------------


class TestGate05TradingEnabled:
    """Per-instrument ``trading_enabled`` flag.

    Promoted from label (comments/handoffs) to gate on 2026-04-24 after the
    Thursday 2026-04-23 audit found that "observer-only" was not code-enforced:
    GBPUSD ran the full pipeline with 1.0% risk and only the pre-AI cost-governor
    gate prevented a real ``mt5.order_send`` from firing.

    Flag lives at the TOP LEVEL of the per-instrument-merged config (populated
    from ``instruments.<SYMBOL>.trading_enabled`` by apply_instrument_overrides).
    Default is True so instruments without explicit config continue to trade.

    Ordering invariant: Gate 0.5 runs BEFORE Gate 3 (circuit breakers) and
    BEFORE Gate 1 (safety checks), so an observer-mode instrument is blocked
    regardless of CANDIDATE quality.
    """

    def _good_state(self):
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(2650.00, 2650.18)
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "london",
                 "trades_london": 0, "losses_today": 0}
        return mt5, state

    def _passing_pa(self):
        """Grade-A setup that would otherwise pass the full gate stack."""
        return _mock_pa(grade="A", entry=2650.0, sl=2640.0, rr=1.5,
                        daily_bias="bullish")

    def test_trading_enabled_flag_allows_live_instrument(self):
        """XAUUSD with trading_enabled=true passes gate."""
        mt5, state = self._good_state()
        config = {"deployment": {"phase": 3}, "trading_enabled": True}
        denial = check_permissions(
            self._passing_pa(), _mock_mso(m15_atr=3.0), state, mt5,
            config=config, symbol="XAUUSD",
        )
        assert denial is None

    def test_trading_enabled_flag_blocks_observer_instrument(self):
        """GBPUSD with trading_enabled=false rejected with correct reason."""
        mt5, state = self._good_state()
        config = {"deployment": {"phase": 3}, "trading_enabled": False}
        denial = check_permissions(
            self._passing_pa(), _mock_mso(m15_atr=3.0), state, mt5,
            config=config, symbol="GBPUSD",
        )
        assert denial is not None
        assert denial.gate == "gate0_5_trading_enabled"
        assert denial.reason == "trading_disabled_for_instrument:GBPUSD"
        assert denial.details["symbol"] == "GBPUSD"
        assert denial.details["trading_enabled"] is False

    def test_trading_enabled_defaults_true_when_missing(self):
        """Instruments without explicit config default to trading_enabled=true.

        The only guarantee: Gate 0.5 does NOT reject when the flag is absent.
        Downstream gates may still reject; here we use an otherwise-passing
        setup so we can assert a pass (denial is None) — if Gate 0.5 silently
        blocked on the missing key, this test would fail with a
        ``gate0_5_trading_enabled`` denial.
        """
        mt5, state = self._good_state()
        # deployment.phase=3 + no ``trading_enabled`` key at all.
        config = {"deployment": {"phase": 3}}
        denial = check_permissions(
            self._passing_pa(), _mock_mso(m15_atr=3.0), state, mt5,
            config=config, symbol="SOME_NEW_SYMBOL",
        )
        assert denial is None, (
            f"Missing trading_enabled should default to True; got {denial}"
        )

    def test_trading_enabled_gate_runs_before_gate1(self):
        """Observer block fires even if CANDIDATE would otherwise pass.

        Also covers the ordering invariants: Gate 0.5 runs BEFORE Gate 1
        (safety checks) and BEFORE Gate 3 (circuit breakers). Construct a
        state that would trip Gate 1 (low grade) and Gate 3 (daily loss
        limit exceeded + MT5 disconnected) simultaneously; if ordering
        regresses, the denial would carry ``gate1_safety`` /
        ``gate3_circuit_breaker`` instead of ``gate0_5_trading_enabled``.
        """
        mt5 = MockMT5()  # deliberately NOT connected -> Gate 3 mt5_disconnected
        state = {
            "daily_pnl_pct": -5.0,          # would trip Gate 3 daily_loss_limit
            "losses_today": 99,
            "current_kill_zone": "london",
            "trades_london": 5,
            "trades_today": 0,
        }
        config = {"deployment": {"phase": 3}, "trading_enabled": False}
        # Use a sub-grade PA that would trip Gate 1 if we got there.
        pa = _mock_pa(grade="B+", entry=2650.0, sl=2640.0, rr=1.5,
                      daily_bias="bullish")
        denial = check_permissions(
            pa, _mock_mso(m15_atr=3.0), state, mt5,
            config=config, symbol="GBPUSD",
        )
        assert denial is not None
        assert denial.gate == "gate0_5_trading_enabled", (
            f"Gate 0.5 must fire before Gate 1 and Gate 3 — "
            f"got {denial.gate} / {denial.reason}"
        )
        assert denial.reason == "trading_disabled_for_instrument:GBPUSD"

    def test_gate_0_fires_before_gate_0_5(self):
        """Ordering invariant: deployment.phase gate still wins.

        A phase=1 deployment with trading_enabled=False must reject with the
        deployment_phase reason, not the trading_disabled reason. Keeps the
        deployment phase diagnostic from being masked by a flag we're about
        to flip anyway. (Prevents a regression where Gate 0.5 gets hoisted
        above Gate 0 during a refactor.)
        """
        mt5, state = self._good_state()
        config = {"deployment": {"phase": 1}, "trading_enabled": False}
        denial = check_permissions(
            self._passing_pa(), _mock_mso(m15_atr=3.0), state, mt5,
            config=config, symbol="GBPUSD",
        )
        assert denial is not None
        assert denial.gate == "gate0_deployment_phase"
        assert denial.reason == "deployment_phase_1_block_all_orders"

    def test_config_loader_flattens_flag_from_nested_instruments_block(self):
        """End-to-end: apply_instrument_overrides surfaces
        instruments.GBPUSD.trading_enabled as config['trading_enabled'].

        This is the production code path — ensures the schema we commit in
        agent_config.yaml actually reaches permissions.py in the shape the
        gate expects.
        """
        from src.utils.config import apply_instrument_overrides

        raw = {
            "market": {"symbol": "XAUUSD"},
            "deployment": {"phase": 3},
            "instruments": {
                "XAUUSD": {"trading_enabled": True},
                "GBPUSD": {"trading_enabled": False},
            },
        }
        merged_x = apply_instrument_overrides(raw, "XAUUSD")
        merged_g = apply_instrument_overrides(raw, "GBPUSD")
        # instruments section is popped after merge.
        assert "instruments" not in merged_x
        assert "instruments" not in merged_g
        # Flag surfaces at top level.
        assert merged_x["trading_enabled"] is True
        assert merged_g["trading_enabled"] is False

        # And the gate honors what the loader produced.
        mt5, state = self._good_state()
        denial_x = check_permissions(
            self._passing_pa(), _mock_mso(m15_atr=3.0), state, mt5,
            config=merged_x, symbol="XAUUSD",
        )
        assert denial_x is None
        denial_g = check_permissions(
            self._passing_pa(), _mock_mso(m15_atr=3.0), state, mt5,
            config=merged_g, symbol="GBPUSD",
        )
        assert denial_g is not None
        assert denial_g.gate == "gate0_5_trading_enabled"


class TestGate06KilledInstrumentPolicy:
    """Evidence-killed instruments stay blocked even if trading_enabled flips."""

    def _good_state(self):
        mt5 = MockMT5(); mt5.connect()
        mt5.set_tick(0.6000, 0.6002)
        state = {"daily_pnl_pct": 0, "trades_today": 0, "current_kill_zone": "london",
                 "trades_london": 0, "losses_today": 0}
        return mt5, state

    def _passing_pa(self):
        return _mock_pa(grade="A", entry=0.6000, sl=0.5950, rr=1.5,
                        daily_bias="bullish")

    def test_killed_instrument_policy_blocks_nzdusd_even_when_trading_enabled(self):
        mt5, state = self._good_state()
        config = {
            "deployment": {"phase": 3},
            "trading_enabled": True,
            "risk": {"sl_absolute_min": 0.001},
            "killed_instrument_policy": {
                "enabled": True,
                "symbols": {
                    "NZDUSD": {
                        "reason": "nzdusd_ai_execution_destroyed_mechanical_ob_edge",
                        "source_path": ".context/02_session_handoffs/05_apr7_complete.md",
                        "source_line_no": 60,
                    }
                },
            },
        }

        denial = check_permissions(
            self._passing_pa(), _mock_mso(m15_atr=0.001), state, mt5,
            config=config, symbol="NZDUSD",
        )

        assert denial is not None
        assert denial.gate == "gate0_6_killed_instrument"
        assert denial.reason == "killed_instrument:NZDUSD"
        assert denial.details["reason"] == "nzdusd_ai_execution_destroyed_mechanical_ob_edge"
        assert denial.details["source_line_no"] == 60

    def test_killed_instrument_policy_is_symbol_scoped(self):
        mt5, state = self._good_state()
        config = {
            "deployment": {"phase": 3},
            "trading_enabled": True,
            "risk": {"sl_absolute_min": 0.001},
            "killed_instrument_policy": {
                "enabled": True,
                "symbols": {
                    "NZDUSD": {"reason": "killed_by_evidence"},
                },
            },
        }

        denial = check_permissions(
            self._passing_pa(), _mock_mso(m15_atr=0.001), state, mt5,
            config=config, symbol="GBPUSD",
        )

        assert denial is None

    def test_agent_config_wires_nzdusd_killed_policy(self):
        with Path("config/agent_config.yaml").open("r", encoding="utf-8") as handle:
            cfg = yaml.safe_load(handle)

        policy = cfg["killed_instrument_policy"]

        assert policy["enabled"] is True
        assert policy["symbols"]["NZDUSD"]["reason"] == (
            "nzdusd_ai_execution_destroyed_mechanical_ob_edge"
        )
        assert policy["symbols"]["NZDUSD"]["source_line_no"] == 60
