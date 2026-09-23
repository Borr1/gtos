"""
Tests for OB limit order flow.
Validates that implementation matches the backtest assumptions from
research/academic_pipeline/results/entry_scenario_analysis_v1.md
and research/academic_pipeline/results/filter_validation_v1.md.
"""
import json
import pytest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone


# Per-test isolation of the persisted pending_intent directory so tests
# never touch production state under knowledge_base/meta/.
@pytest.fixture(autouse=True)
def _isolate_pending_intent_dir(tmp_path, monkeypatch):
    from src.components import execution as _exec
    monkeypatch.setattr(_exec, "PENDING_INTENT_DIR", str(tmp_path))
    monkeypatch.setattr(_exec, "CHECKPOINT_PATH", str(tmp_path / "execution_checkpoint.json"))
    yield
    for p in Path(tmp_path).glob("pending_intent_*.pkl"):
        try:
            p.unlink()
        except OSError:
            pass


# â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _make_analysis(entry_price, direction="LONG", tp=None, sl=None):
    analysis = MagicMock()
    analysis.trade_parameters.entry_price = entry_price
    analysis.trade_parameters.direction = direction
    analysis.trade_parameters.stop_loss = sl or (entry_price - 20)
    analysis.trade_parameters.take_profit_1 = tp or (entry_price + 30)
    return analysis

def _make_mso(current_price):
    m15_candle = MagicMock()
    m15_candle.close = current_price
    m15_tf = MagicMock()
    m15_tf.candles = [m15_candle]
    mso = MagicMock()
    mso.timeframes = {"M15": m15_tf}
    return mso

def _make_engine():
    from src.components.execution import ExecutionEngine
    mt5 = MagicMock()
    mt5.get_tick.return_value = MagicMock(ask=4460.0, bid=4459.0)
    config = {"market": {"symbol": "XAUUSD"}, "risk": {"risk_per_trade_pct": 1.0}}
    return ExecutionEngine(mt5, config)


def _install_symbol_info(mt5, **overrides):
    info = SimpleNamespace(
        trade_tick_size=0.01,
        trade_tick_value=1.0,
        volume_min=0.03,
        volume_step=0.03,
        volume_max=10.0,
        filling_mode=3,
        spread=12,
    )
    for key, value in overrides.items():
        setattr(info, key, value)

    def _order_calc_profit(order_type, _symbol, volume, price_open, price_close):
        price_delta = (
            float(price_close) - float(price_open)
            if int(order_type) == 0
            else float(price_open) - float(price_close)
        )
        return (
            price_delta
            / float(info.trade_tick_size)
            * float(info.trade_tick_value)
            * float(volume)
        )

    mt5._mt5 = SimpleNamespace(
        symbol_info=lambda _symbol: info,
        order_calc_profit=_order_calc_profit,
    )
    return info

# â”€â”€ Gap Filter Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def test_gap_ceiling_pass_long():
    """Gap 1.0% below 1.5% ceiling â†’ PASS."""
    from src.components.verification import _check_gap_ceiling
    # ob_high=4421.39, current=4465.60 â†’ gap=(4465.60-4421.39)/4421.39*100=1.0%
    analysis = _make_analysis(entry_price=4421.39, direction="LONG")
    mso = _make_mso(current_price=4465.60)
    result = _check_gap_ceiling(analysis, mso, {"filters": {"max_gap_pct": 1.5}})
    assert result.status == "PASS"
    assert "1.0" in result.detail or "Gap" in result.detail

def test_gap_ceiling_fail_long():
    """Gap 2.0% above 1.5% ceiling â†’ FAIL."""
    from src.components.verification import _check_gap_ceiling
    # ob_high=4421.39, current=4509.82 â†’ gapâ‰ˆ2.0%
    analysis = _make_analysis(entry_price=4421.39, direction="LONG")
    mso = _make_mso(current_price=4509.82)
    result = _check_gap_ceiling(analysis, mso, {"filters": {"max_gap_pct": 1.5}})
    assert result.status == "FAIL"

def test_gap_ceiling_pass_short():
    """SHORT direction: gap computed as (entry - current) / entry."""
    from src.components.verification import _check_gap_ceiling
    # ob_low=4405.55, current=4384.37 â†’ gap=(4405.55-4384.37)/4405.55=0.48% â†’ PASS
    analysis = _make_analysis(entry_price=4405.55, direction="SHORT")
    mso = _make_mso(current_price=4384.37)
    result = _check_gap_ceiling(analysis, mso, {"filters": {"max_gap_pct": 1.5}})
    assert result.status == "PASS"

def test_gap_ceiling_skip_no_trade_params():
    """No trade_parameters â†’ SKIP."""
    from src.components.verification import _check_gap_ceiling
    analysis = MagicMock()
    analysis.trade_parameters = None
    result = _check_gap_ceiling(analysis, MagicMock(), {})
    assert result.status == "SKIP"

def test_gap_ceiling_skip_no_m15():
    """No M15 candles in MSO â†’ SKIP."""
    from src.components.verification import _check_gap_ceiling
    analysis = _make_analysis(entry_price=4421.39)
    mso = MagicMock()
    mso.timeframes = {}
    result = _check_gap_ceiling(analysis, mso, {})
    assert result.status == "SKIP"

def test_gap_ceiling_configurable_threshold():
    """max_gap_pct=2.0 allows 1.9% gap that 1.5 would reject."""
    from src.components.verification import _check_gap_ceiling
    analysis = _make_analysis(entry_price=4421.39, direction="LONG")
    mso = _make_mso(current_price=4505.42)  # ~1.9% gap
    result_strict = _check_gap_ceiling(analysis, mso, {"filters": {"max_gap_pct": 1.5}})
    result_loose  = _check_gap_ceiling(analysis, mso, {"filters": {"max_gap_pct": 2.0}})
    assert result_strict.status == "FAIL"
    assert result_loose.status == "PASS"

# â”€â”€ Limit Intent Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def test_agent_config_wires_apr13_limit_architecture_gap_ceiling():
    """Unit 40 evidence selected max_gap_pct=1.5 as the live limit-entry
    ceiling. Production config must reject a 1.6% stale-zone gap while
    allowing a 1.4% pullback candidate.
    """
    import yaml
    from src.components.verification import _check_gap_ceiling

    with Path("config/agent_config.yaml").open("r", encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle)

    assert cfg["filters"]["max_gap_pct"] == 1.5

    analysis = _make_analysis(entry_price=4421.39, direction="LONG")
    assert _check_gap_ceiling(
        analysis,
        _make_mso(current_price=4421.39 * 1.014),
        cfg,
    ).status == "PASS"
    assert _check_gap_ceiling(
        analysis,
        _make_mso(current_price=4421.39 * 1.016),
        cfg,
    ).status == "FAIL"


def test_set_limit_intent_stores_correctly():
    """set_limit_intent stores PendingLimitIntent with correct fields."""
    from src.components.execution import PendingLimitIntent
    engine = _make_engine()
    params = {"direction": "LONG", "entry_price": 4421.39,
              "stop_loss": 4401.99, "take_profit_1": 4450.49,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    intent = engine.set_limit_intent(params, account_balance=100000.0)
    assert isinstance(intent, PendingLimitIntent)
    assert engine.pending_intent is intent
    assert intent.direction == "LONG"
    assert intent.limit_price == 4421.39
    assert intent.stop_loss == 4401.99
    assert intent.expiry_candles == 192
    assert intent.account_balance == 100000.0
    assert intent.pending_order_mode == "INTERNAL_CANDLE_POLLED_INTENT"
    assert intent.broker_pending_order_created is False
    assert intent.mt5_order_ticket is None
    assert intent.native_pending_order_type is None


def test_set_limit_intent_persists_vnext_dynamic_policy_for_fill():
    engine = _make_engine()
    params = {"direction": "LONG", "entry_price": 4421.39,
              "stop_loss": 4401.99, "take_profit_1": 4450.49,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    intent = engine.set_limit_intent(
        params,
        account_balance=100000.0,
        telemetry_context={
            "gtos_vnext_dynamic_policy_selected": "be_after_trigger",
            "gtos_vnext_dynamic_policy_applied": True,
            "gtos_vnext_dynamic_policy_replaced_policy": "retired_static_baseline_comparator",
            "gtos_vnext_dynamic_policy_candidate_action": (
                "TRADE_VNEXT_PRIMARY_CANDIDATE"
            ),
        },
    )

    assert intent.gtos_vnext_dynamic_policy_selected == "be_after_trigger"
    assert intent.gtos_vnext_dynamic_policy_applied is True
    assert intent.gtos_vnext_dynamic_policy_replaced_policy == "retired_static_baseline_comparator"

    with patch.object(engine, "open_trade", return_value=MagicMock()) as mock_open:
        engine.check_limit_fill({"time": "2026-01-07 10:00:00",
                                 "open": 4430.0, "high": 4432.0,
                                 "low": 4421.00, "close": 4428.0})

    _, kwargs = mock_open.call_args
    assert kwargs["trade_params"]["gtos_vnext_dynamic_policy_selected"] == (
        "be_after_trigger"
    )
    assert kwargs["trade_params"]["gtos_vnext_dynamic_policy_applied"] is True
    assert kwargs["trade_params"]["gtos_vnext_dynamic_policy_replaced_policy"] == (
        "retired_static_baseline_comparator"
    )


def test_selected_cell_risk_persists_through_pending_fill():
    engine = _make_engine()
    params = {
        "direction": "LONG",
        "entry_price": 4421.39,
        "stop_loss": 4401.99,
        "take_profit_1": 4450.49,
        "take_profit_2": 0.0,
        "take_profit_3": 0.0,
        "risk_reward_ratio": 1.5,
        "gtos_vnext_dynamic_policy_selected": "be_after_trigger",
        "gtos_vnext_dynamic_policy_applied": True,
    }
    intent = engine.set_limit_intent(
        params,
        account_balance=100000.0,
        risk_pct_override=0.25,
        telemetry_context={
            "gtos_vnext_selected_cell_risk_pct": 0.25,
            "gtos_vnext_selected_cell_risk_cell_id": "risk-cell-xau-london-long",
            "gtos_vnext_selected_cell_risk_decision_basis": "vnext_cell_evidence_tier:micro_positive_ev_floor",
        },
    )

    assert intent.risk_pct == 0.25
    assert intent.gtos_vnext_selected_cell_risk_pct == 0.25
    assert intent.gtos_vnext_selected_cell_risk_cell_id == "risk-cell-xau-london-long"

    with patch.object(engine, "open_trade", return_value=MagicMock()) as mock_open:
        engine.check_limit_fill(
            {
                "time": "2026-01-07 10:00:00",
                "open": 4430.0,
                "high": 4432.0,
                "low": 4421.00,
                "close": 4428.0,
            }
        )

    _, kwargs = mock_open.call_args
    assert kwargs["risk_pct_override"] == 0.25
    assert kwargs["trade_params"]["gtos_vnext_selected_cell_risk_pct"] == 0.25
    assert kwargs["trade_params"]["gtos_vnext_selected_cell_risk_cell_id"] == (
        "risk-cell-xau-london-long"
    )


def test_broader_origin_limit_fill_keeps_dynamic_policy_from_trade_params():
    engine = _make_engine()
    params = {
        "direction": "LONG",
        "entry_price": 4421.39,
        "stop_loss": 4401.99,
        "take_profit_1": 4450.49,
        "take_profit_2": 0.0,
        "take_profit_3": 0.0,
        "risk_reward_ratio": 1.5,
        "gtos_vnext_dynamic_policy_selected": "be_after_trigger",
        "gtos_vnext_dynamic_policy_applied": True,
        "gtos_vnext_dynamic_policy_replaced_policy": "retired_static_baseline_comparator",
        "gtos_vnext_dynamic_policy_candidate_action": (
            "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE"
        ),
        "gtos_vnext_dynamic_policy_decision_status": "approved_for_execution",
    }
    intent = engine.set_limit_intent(
        params,
        account_balance=100000.0,
        telemetry_context={
            "source_branch": "gtos_vnext_broader_origin_pre_ai",
            "candidate_id": "broadorigin_dynamic_fill",
        },
    )

    assert intent.gtos_vnext_dynamic_policy_selected == "be_after_trigger"
    assert intent.gtos_vnext_dynamic_policy_applied is True

    with patch.object(engine, "open_trade", return_value=MagicMock()) as mock_open:
        engine.check_limit_fill(
            {
                "time": "2026-01-07 10:00:00",
                "open": 4430.0,
                "high": 4432.0,
                "low": 4421.00,
                "close": 4428.0,
            }
        )

    _, kwargs = mock_open.call_args
    assert kwargs["trade_params"]["gtos_vnext_dynamic_policy_selected"] == "be_after_trigger"
    assert kwargs["trade_params"]["gtos_vnext_dynamic_policy_applied"] is True
    assert kwargs["trade_params"]["gtos_vnext_dynamic_policy_replaced_policy"] == (
        "retired_static_baseline_comparator"
    )
    assert kwargs["trade_params"]["gtos_vnext_dynamic_policy_candidate_action"] == (
        "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE"
    )


def test_broader_origin_pending_fill_opens_trade_with_vnext_be_after_trigger_not_j46_j49():
    from src.components.execution import ExecutionEngine
    from src.mt5.mt5_mock import MockMT5

    mt5 = MockMT5(balance=100000.0)
    mt5.connect()
    config = {
        "risk": {"risk_per_trade_pct": 1.0},
        "position_mgmt": {
            "j46_j49_v2": {
                "enabled": True,
                "partial_close_ratio": 0.0,
                "be_trigger": "immediate_on_tp1",
                "time_stop_bars": 12,
                "tp1_distance_r": 3.0,
                "higher_target_r": 6.0,
            }
        },
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_be_trigger_r": 1.0,
            "moonshot_dynamic_execution_router_be_final_target_r": 1.5,
            "moonshot_dynamic_execution_router_be_time_stop_bars": None,
        },
    }
    engine = ExecutionEngine(mt5, config)
    params = {
        "direction": "LONG",
        "entry_price": 2650.0,
        "stop_loss": 2640.0,
        "take_profit_1": 2665.0,
        "take_profit_2": 0.0,
        "take_profit_3": 0.0,
        "risk_reward_ratio": 1.5,
        "gtos_vnext_dynamic_policy_selected": "be_after_trigger",
        "gtos_vnext_dynamic_policy_applied": True,
        "gtos_vnext_dynamic_policy_replaced_policy": "retired_static_baseline_comparator",
        "gtos_vnext_dynamic_policy_candidate_action": (
            "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE"
        ),
    }
    engine.set_limit_intent(
        params,
        account_balance=100000.0,
        telemetry_context={"source_branch": "gtos_vnext_broader_origin_pre_ai"},
    )

    state = engine.check_limit_fill(
        {
            "time": "2026-05-26T13:00:00+00:00",
            "open": 2651.0,
            "high": 2652.0,
            "low": 2649.0,
            "close": 2651.5,
        }
    )

    assert state is not None
    assert engine.pending_intent is None
    assert state.j46_j49_active is False
    assert state.gtos_vnext_dynamic_be_after_trigger_active is True
    assert state.gtos_vnext_dynamic_policy_candidate_action == (
        "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE"
    )
    assert state.take_profit_1 == pytest.approx(
        state.entry_price + state.sl_distance,
        abs=1e-6,
    )
    assert state.take_profit_2 == pytest.approx(
        state.entry_price + 1.5 * state.sl_distance,
        abs=1e-6,
    )


def test_vnext_pending_dynamic_policy_survives_disk_reload_and_config_drift():
    from src.components.execution import ExecutionEngine
    from src.mt5.mt5_mock import MockMT5

    mt5 = MockMT5(balance=100000.0)
    mt5.connect()
    placement_config = {
        "risk": {"risk_per_trade_pct": 1.0},
        "position_mgmt": {"j46_j49_v2": {"enabled": True}},
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_be_trigger_r": 0.8,
            "moonshot_dynamic_execution_router_be_final_target_r": 2.2,
            "moonshot_dynamic_execution_router_be_time_stop_bars": 7,
        },
    }
    placement_engine = ExecutionEngine(mt5, placement_config)
    params = {
        "direction": "LONG",
        "entry_price": 2650.0,
        "stop_loss": 2640.0,
        "take_profit_1": 2665.0,
        "take_profit_2": 0.0,
        "take_profit_3": 0.0,
        "risk_reward_ratio": 1.5,
        "gtos_vnext_dynamic_policy_selected": "be_after_trigger",
        "gtos_vnext_dynamic_policy_applied": True,
        "gtos_vnext_dynamic_policy_replaced_policy": "retired_static_baseline_comparator",
        "gtos_vnext_dynamic_policy_candidate_action": (
            "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE"
        ),
    }
    placement_engine.set_limit_intent(
        params,
        account_balance=100000.0,
        telemetry_context={
            "source_branch": "gtos_vnext_broader_origin_pre_ai",
            "gtos_vnext_source_event_hash": "source-event-sha",
            "gtos_vnext_source_event_details": {
                "symbol": "XAUUSD",
                "candidate_origin_family": "origin_liquidity_sweep_reclaim",
            },
            "gtos_vnext_activation_family": (
                "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE"
            ),
            "gtos_vnext_origin_family": "origin_liquidity_sweep_reclaim",
            "gtos_vnext_selector_row_id": "selector-row-1",
            "gtos_vnext_selector_proof_hash": "selector-proof-sha",
        },
    )

    drifted_config = {
        "risk": {"risk_per_trade_pct": 1.0},
        "position_mgmt": {"j46_j49_v2": {"enabled": True}},
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_be_trigger_r": 1.0,
            "moonshot_dynamic_execution_router_be_final_target_r": 1.5,
            "moonshot_dynamic_execution_router_be_time_stop_bars": None,
        },
    }
    restored_engine = ExecutionEngine(mt5, drifted_config)

    assert restored_engine.pending_intent is not None
    assert restored_engine.pending_intent.gtos_vnext_dynamic_be_trigger_r == 0.8
    assert restored_engine.pending_intent.gtos_vnext_dynamic_final_target_r == 2.2
    assert restored_engine.pending_intent.gtos_vnext_dynamic_time_stop_bars == 7
    assert restored_engine.pending_intent.gtos_vnext_source_event_hash == (
        "source-event-sha"
    )

    state = restored_engine.check_limit_fill(
        {
            "time": "2026-05-26T13:00:00+00:00",
            "open": 2651.0,
            "high": 2652.0,
            "low": 2649.0,
            "close": 2651.5,
        }
    )

    assert state is not None
    assert restored_engine.pending_intent is None
    assert state.j46_j49_active is False
    assert state.gtos_vnext_dynamic_be_after_trigger_active is True
    assert state.gtos_vnext_dynamic_be_trigger_r == pytest.approx(0.8)
    assert state.gtos_vnext_dynamic_final_target_r == pytest.approx(2.2)
    assert state.gtos_vnext_dynamic_time_stop_bars == 7
    assert state.take_profit_1 == pytest.approx(
        state.entry_price + 0.8 * state.sl_distance,
        abs=1e-6,
    )
    assert state.take_profit_2 == pytest.approx(
        state.entry_price + 2.2 * state.sl_distance,
        abs=1e-6,
    )
    assert state.gtos_vnext_dynamic_placement_be_trigger_price == pytest.approx(
        2650.0 + 0.8 * 10.0,
        abs=1e-6,
    )
    assert state.gtos_vnext_source_event_hash == "source-event-sha"
    assert state.gtos_vnext_origin_family == "origin_liquidity_sweep_reclaim"
    assert state.gtos_vnext_selector_row_id == "selector-row-1"


def test_vnext_dynamic_unsupported_policy_fails_closed_before_order():
    from src.components.execution import ExecutionEngine
    from src.mt5.mt5_mock import MockMT5

    mt5 = MockMT5(balance=100000.0)
    mt5.connect()
    engine = ExecutionEngine(mt5, {"risk": {"risk_per_trade_pct": 1.0}})

    state = engine.open_trade(
        {
            "direction": "LONG",
            "entry_price": 2650.0,
            "stop_loss": 2640.0,
            "take_profit_1": 2665.0,
            "gtos_vnext_dynamic_policy_selected": "liquidity_sweep_exit",
            "gtos_vnext_dynamic_policy_applied": True,
            "gtos_vnext_dynamic_policy_replaced_policy": "retired_static_baseline_comparator",
        },
        account_balance=100000.0,
    )

    assert state is None
    assert mt5._order_log == []


def test_vnext_partial_be_runner_opens_and_manages_partial_then_final():
    from src.components.execution import ExecutionEngine
    from src.mt5.mt5_mock import MockMT5

    mt5 = MockMT5(balance=100000.0)
    mt5.connect()
    config = {
        "risk": {"risk_per_trade_pct": 1.0},
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_partial_trigger_r": 1.0,
            "moonshot_dynamic_execution_router_partial_final_target_r": 3.0,
            "moonshot_dynamic_execution_router_partial_close_ratio": 0.5,
        },
    }
    engine = ExecutionEngine(mt5, config)

    state = engine.open_trade(
        {
            "direction": "LONG",
            "entry_price": 2650.0,
            "stop_loss": 2640.0,
            "take_profit_1": 2665.0,
            "gtos_vnext_dynamic_policy_selected": "partial_be_runner",
            "gtos_vnext_dynamic_policy_applied": True,
            "gtos_vnext_dynamic_policy_replaced_policy": "retired_static_baseline_comparator",
        },
        account_balance=100000.0,
    )

    assert state is not None
    assert state.take_profit_1 == pytest.approx(state.entry_price + state.sl_distance)
    assert state.take_profit_2 == pytest.approx(state.entry_price + 3.0 * state.sl_distance)

    mt5.set_tick(bid=state.take_profit_1, ask=state.take_profit_1 + 0.18)
    action = engine.check_and_manage_trade({})

    assert action == "tp1_partial_vnext_partial_be_runner"
    assert engine.active_trade is not None
    assert engine.active_trade.tp1_hit is True
    assert engine.active_trade.sl_at_breakeven is True
    assert engine.active_trade.current_volume < state.initial_volume

    mt5.set_tick(
        bid=engine.active_trade.take_profit_2,
        ask=engine.active_trade.take_profit_2 + 0.18,
    )
    action = engine.check_and_manage_trade({})

    assert action == "tp2_final_target_vnext_partial_be_runner"
    assert engine.active_trade is None


def _routed_dynamic_decision(
    framework="fvg_fill",
    session_bucket="ny_broad",
    displacement=0.5,
    liquidity="no_prior_20_sweep",
    candidate_origin_family=None,
    activated_origin_families=None,
    broader_origin_allowed=False,
    live_generation_status=None,
    primary_policy=None,
):
    from src.components.gtos_vnext_runtime import (
        GTOSVNextRuntimeDecision,
        evaluate_vnext_moonshot_dynamic_execution,
    )

    decision = GTOSVNextRuntimeDecision(
        decision="FOLLOW",
        event={
            "symbol": "XAUUSD",
            "side": "LONG",
            "framework": framework,
            "route_session": session_bucket.replace("_broad", ""),
        },
        enabled=True,
        apply_to_execution=True,
        matched=True,
        reason="matched_vnext_route_scope",
        evidence={"matched_rows": 3},
    )
    cfg = {
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_enabled": True,
            "moonshot_dynamic_execution_router_apply_to_execution": True,
            "moonshot_dynamic_execution_router_condition_challenger_enabled": True,
            "moonshot_dynamic_execution_router_condition_challenger_policy": (
                "condition_asof_displacement_v1"
            ),
            "moonshot_dynamic_execution_router_policy": (
                primary_policy or "momentum_exhaustion"
            ),
            "moonshot_dynamic_execution_router_momentum_exception_policy": (
                "partial_be_runner"
            ),
            "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner": [
                "cross_asset_lead_lag",
                "displacement_continuation",
                "liquidity_sweep_reclaim",
                "regime_transition_break",
                "session_open_range_break",
                "volatility_compression_expansion",
            ],
            "moonshot_dynamic_execution_router_broker_native_eligible_symbols": [
                "XAUUSD"
            ],
            "moonshot_dynamic_execution_router_default_source_mode": "OHLC_M15_CSV",
            "moonshot_dynamic_execution_router_default_source_path_feature_status": (
                "computed_from_source_ohlc_asof"
            ),
            "moonshot_dynamic_execution_router_default_source_window_complete": True,
            "moonshot_dynamic_execution_router_default_ordered_path_status": (
                "ordered_path_not_ambiguous_in_m15_replay"
            ),
            "moonshot_dynamic_execution_router_require_configured_kill_zone": True,
        },
    }
    return evaluate_vnext_moonshot_dynamic_execution(
        decision=decision,
        config=cfg,
        candidate_context={
            "framework": framework,
            "session_bucket": session_bucket,
            "kill_zone_position": f"in_{session_bucket.replace('_broad', '')}_early",
            "current_bar_displacement_atr14": displacement,
            "liquidity_sweep_proxy_state": liquidity,
            "source_window_complete": True,
            "selected_policy_same_bar_ambiguous": False,
            "candidate_origin_family": candidate_origin_family
            or f"origin_current_{framework}",
            "activated_origin_families": activated_origin_families or [],
            "broader_origin_allowed": broader_origin_allowed,
            "live_generation_status": live_generation_status,
        },
    )


def _engine_with_dynamic_config():
    from src.components.execution import ExecutionEngine
    from src.mt5.mt5_mock import MockMT5

    mt5 = MockMT5(balance=100000.0)
    mt5.connect()
    config = {
        "risk": {"risk_per_trade_pct": 1.0},
        "position_mgmt": {"j46_j49_v2": {"enabled": True}},
        "gtos_vnext_runtime": {
            "moonshot_dynamic_execution_router_partial_trigger_r": 1.0,
            "moonshot_dynamic_execution_router_partial_final_target_r": 3.0,
            "moonshot_dynamic_execution_router_partial_close_ratio": 0.5,
            "moonshot_dynamic_execution_router_trailing_trigger_r": 1.0,
            "moonshot_dynamic_execution_router_trailing_final_target_r": 3.0,
            "moonshot_dynamic_execution_router_trailing_gap_r": 0.5,
            "moonshot_dynamic_execution_router_momentum_trigger_r": 1.0,
            "moonshot_dynamic_execution_router_momentum_final_target_r": 2.0,
            "moonshot_dynamic_execution_router_momentum_pullback_r": 0.4,
        },
    }
    return ExecutionEngine(mt5, config), mt5


def _pending_params_from_router(routed):
    return {
        "direction": "LONG",
        "entry_price": 2650.0,
        "stop_loss": 2640.0,
        "take_profit_1": 2665.0,
        "take_profit_2": 0.0,
        "take_profit_3": 0.0,
        "risk_reward_ratio": 1.5,
        "gtos_vnext_execution_policy_id": routed.execution_policy_id,
        "gtos_vnext_dynamic_policy_selected": routed.selected_policy,
        "gtos_vnext_dynamic_policy_applied": routed.applied,
        "gtos_vnext_dynamic_policy_replaced_policy": routed.replaced_policy,
        "gtos_vnext_dynamic_policy_candidate_action": routed.candidate_action,
        "gtos_vnext_dynamic_policy_decision_status": routed.decision_status,
    }


def test_vnext_partial_be_runner_pending_fill_uses_router_decision_and_lifecycle():
    routed = _routed_dynamic_decision(
        framework="ob_retest",
        session_bucket="london",
        displacement=0.25,
        candidate_origin_family="origin_liquidity_sweep_reclaim",
        activated_origin_families=["liquidity_sweep_reclaim"],
        live_generation_status="generated_live_asof",
    )
    assert routed.selected_policy == "partial_be_runner"
    assert routed.applied is True
    assert routed.execution_policy_id

    engine, mt5 = _engine_with_dynamic_config()
    engine.set_limit_intent(
        _pending_params_from_router(routed),
        account_balance=100000.0,
    )
    state = engine.check_limit_fill(
        {
            "time": "2026-05-27T13:30:00+00:00",
            "open": 2651.0,
            "high": 2652.0,
            "low": 2649.0,
            "close": 2651.5,
        }
    )

    assert state is not None
    assert state.gtos_vnext_execution_policy_id == routed.execution_policy_id
    assert state.j46_j49_active is False
    mt5.set_tick(bid=state.take_profit_1, ask=state.take_profit_1 + 0.18)
    assert engine.check_and_manage_trade({}) == "tp1_partial_vnext_partial_be_runner"
    assert engine.active_trade is not None
    assert engine.active_trade.sl_at_breakeven is True
    mt5.set_tick(
        bid=engine.active_trade.take_profit_2,
        ask=engine.active_trade.take_profit_2 + 0.18,
    )
    assert engine.check_and_manage_trade({}) == "tp2_final_target_vnext_partial_be_runner"
    assert engine.active_trade is None


def test_vnext_trailing_runner_pending_fill_trails_and_final_closes_from_router():
    routed = _routed_dynamic_decision(
        framework="fvg_fill",
        session_bucket="ny_broad",
        displacement=1.25,
        primary_policy="trailing_runner",
    )
    assert routed.selected_policy == "trailing_runner"
    assert routed.execution_policy_id

    engine, mt5 = _engine_with_dynamic_config()
    engine.set_limit_intent(
        _pending_params_from_router(routed),
        account_balance=100000.0,
    )
    state = engine.check_limit_fill(
        {
            "time": "2026-05-27T13:30:00+00:00",
            "open": 2651.0,
            "high": 2652.0,
            "low": 2649.0,
            "close": 2651.5,
        }
    )

    assert state is not None
    assert state.gtos_vnext_execution_policy_id == routed.execution_policy_id
    mt5.set_tick(bid=state.take_profit_1, ask=state.take_profit_1 + 0.18)
    assert engine.check_and_manage_trade({}) == "tp1_trailing_runner_started"
    assert engine.active_trade is not None
    assert engine.active_trade.gtos_vnext_dynamic_trail_stop_r == pytest.approx(0.5)
    assert engine.active_trade.stop_loss > engine.active_trade.entry_price

    mt5.set_tick(
        bid=engine.active_trade.entry_price + 2.2 * engine.active_trade.sl_distance,
        ask=engine.active_trade.entry_price + 2.2 * engine.active_trade.sl_distance + 0.18,
    )
    assert engine.check_and_manage_trade({}) == "vnext_trailing_runner_sl_modified"
    assert engine.active_trade.gtos_vnext_dynamic_trail_stop_r == pytest.approx(1.7)

    mt5.set_tick(
        bid=engine.active_trade.take_profit_2,
        ask=engine.active_trade.take_profit_2 + 0.18,
    )
    assert engine.check_and_manage_trade({}) == "tp2_final_target_vnext_trailing_runner"
    assert engine.active_trade is None


def test_vnext_momentum_exhaustion_pending_fill_closes_on_pullback_from_router():
    routed = _routed_dynamic_decision(
        framework="fvg_fill",
        session_bucket="ny_broad",
        displacement=1.25,
        liquidity="swept_prior_20_low",
    )
    assert routed.selected_policy == "momentum_exhaustion"
    assert routed.execution_policy_id

    engine, mt5 = _engine_with_dynamic_config()
    engine.set_limit_intent(
        _pending_params_from_router(routed),
        account_balance=100000.0,
    )
    state = engine.check_limit_fill(
        {
            "time": "2026-05-27T13:30:00+00:00",
            "open": 2651.0,
            "high": 2652.0,
            "low": 2649.0,
            "close": 2651.5,
        }
    )

    assert state is not None
    mt5.set_tick(
        bid=state.entry_price + 1.2 * state.sl_distance,
        ask=state.entry_price + 1.2 * state.sl_distance + 0.18,
    )
    assert engine.check_and_manage_trade({}) == "tp1_momentum_exhaustion_started"
    mt5.set_tick(
        bid=state.entry_price + 1.2 * state.sl_distance,
        ask=state.entry_price + 1.2 * state.sl_distance + 0.18,
    )
    assert engine.check_and_manage_trade({}) == "monitoring"
    mt5.set_tick(
        bid=state.entry_price + 0.7 * state.sl_distance,
        ask=state.entry_price + 0.7 * state.sl_distance + 0.18,
    )
    assert engine.check_and_manage_trade({}) == "vnext_momentum_exhaustion_pullback"
    assert engine.active_trade is None


def _enable_profit_harvest_v4(engine, **overrides):
    cfg = engine.config.setdefault("gtos_vnext_runtime", {})
    cfg.update(
        {
            "profit_harvest_mfe_capture_v4_enabled": True,
            "profit_harvest_mfe_capture_v4_min_mfe_r": 0.25,
            "profit_harvest_mfe_capture_v4_stop_activation_mfe_r": 0.25,
            "profit_harvest_mfe_capture_v4_target_activation_fraction": 0.0,
            "profit_harvest_mfe_capture_v4_trail_gap_r": 0.35,
            "profit_harvest_mfe_capture_v4_protect_floor_r": 0.0,
            "profit_harvest_mfe_capture_v4_cost_aware_protect_floor_enabled": False,
            "profit_harvest_mfe_capture_v4_cost_aware_margin_r": 0.0,
            "profit_harvest_mfe_capture_v4_close_on_giveback_r": 0.50,
            "profit_harvest_mfe_capture_v4_stale_minutes": 360,
            "profit_harvest_mfe_capture_v4_stale_min_mfe_r": 0.25,
            "profit_harvest_mfe_capture_v4_stale_close_below_r": 0.0,
            "profit_harvest_mfe_capture_v4_armed_stale_close_enabled": False,
            "profit_harvest_mfe_capture_v4_armed_stale_minutes": 30,
            "profit_harvest_mfe_capture_v4_armed_stale_min_mfe_r": 0.25,
            "profit_harvest_mfe_capture_v4_armed_stale_close_below_r": 0.0,
            "profit_harvest_mfe_capture_v4_min_hold_minutes_before_stop_raise": 0,
        }
    )
    cfg.update(overrides)


def _filled_partial_runner_state(engine, mt5):
    routed = _routed_dynamic_decision(
        framework="ob_retest",
        session_bucket="london",
        displacement=0.25,
        candidate_origin_family="origin_liquidity_sweep_reclaim",
        activated_origin_families=["liquidity_sweep_reclaim"],
        live_generation_status="generated_live_asof",
    )
    engine.set_limit_intent(
        _pending_params_from_router(routed),
        account_balance=100000.0,
    )
    state = engine.check_limit_fill(
        {
            "time": "2026-05-27T13:30:00+00:00",
            "open": 2651.0,
            "high": 2652.0,
            "low": 2649.0,
            "close": 2651.5,
        }
    )
    assert state is not None
    assert engine.active_trade is state
    assert mt5.get_positions(engine.symbol)
    return state


def test_profit_harvest_v4_default_off_does_not_manage_subtrigger_mfe():
    engine, mt5 = _engine_with_dynamic_config()
    state = _filled_partial_runner_state(engine, mt5)

    mt5.set_tick(
        bid=state.entry_price + 0.30 * state.sl_distance,
        ask=state.entry_price + 0.30 * state.sl_distance + 0.18,
    )

    assert engine.check_and_manage_trade({}) == "monitoring"
    assert engine.active_trade is not None
    assert engine.active_trade.sl_at_breakeven is False


def test_profit_harvest_v4_protects_subtrigger_mfe_when_enabled():
    engine, mt5 = _engine_with_dynamic_config()
    _enable_profit_harvest_v4(engine)
    state = _filled_partial_runner_state(engine, mt5)

    mt5.set_tick(
        bid=state.entry_price + 0.30 * state.sl_distance,
        ask=state.entry_price + 0.30 * state.sl_distance + 0.18,
    )

    assert engine.check_and_manage_trade({}) == (
        "vnext_profit_harvest_mfe_capture_v4_sl_modified"
    )
    assert engine.active_trade is not None
    assert engine.active_trade.sl_at_breakeven is True
    assert engine.active_trade.gtos_vnext_profit_harvest_triggered is True
    assert any(
        event["type"] == "VNEXT_PROFIT_HARVEST_MFE_CAPTURE_V4_ARMED"
        for event in engine.active_trade.partial_close_events
    )


def test_profit_harvest_v4_defers_stop_raise_until_stop_activation_mfe():
    engine, mt5 = _engine_with_dynamic_config()
    _enable_profit_harvest_v4(
        engine,
        profit_harvest_mfe_capture_v4_min_mfe_r=0.50,
        profit_harvest_mfe_capture_v4_stop_activation_mfe_r=0.70,
    )
    state = _filled_partial_runner_state(engine, mt5)

    mt5.set_tick(
        bid=state.entry_price + 0.60 * state.sl_distance,
        ask=state.entry_price + 0.60 * state.sl_distance + 0.18,
    )

    assert engine.check_and_manage_trade({}) == "monitoring"
    assert engine.active_trade is not None
    assert engine.active_trade.gtos_vnext_profit_harvest_triggered is True
    assert (
        engine.active_trade.gtos_vnext_profit_harvest_stop_activation_confirmed
        is False
    )
    assert engine.active_trade.sl_at_breakeven is False

    mt5.set_tick(
        bid=state.entry_price + 0.75 * state.sl_distance,
        ask=state.entry_price + 0.75 * state.sl_distance + 0.18,
    )

    assert engine.check_and_manage_trade({}) == (
        "vnext_profit_harvest_mfe_capture_v4_sl_modified"
    )
    assert engine.active_trade is not None
    assert (
        engine.active_trade.gtos_vnext_profit_harvest_stop_activation_confirmed
        is True
    )
    assert engine.active_trade.sl_at_breakeven is True


def test_profit_harvest_v4_closes_on_subtrigger_giveback_when_enabled():
    engine, mt5 = _engine_with_dynamic_config()
    _enable_profit_harvest_v4(engine)
    state = _filled_partial_runner_state(engine, mt5)

    mt5.set_tick(
        bid=state.entry_price + 0.75 * state.sl_distance,
        ask=state.entry_price + 0.75 * state.sl_distance + 0.18,
    )
    assert engine.check_and_manage_trade({}) == (
        "vnext_profit_harvest_mfe_capture_v4_sl_modified"
    )
    mt5.set_tick(
        bid=state.entry_price + 0.20 * state.sl_distance,
        ask=state.entry_price + 0.20 * state.sl_distance + 0.18,
    )

    assert engine.check_and_manage_trade({}) == (
        "vnext_profit_harvest_mfe_capture_v4_giveback_close"
    )
    assert engine.active_trade is None


def test_profit_harvest_v4_closes_stale_positive_mfe_thesis():
    from datetime import timedelta

    engine, mt5 = _engine_with_dynamic_config()
    _enable_profit_harvest_v4(
        engine,
        profit_harvest_mfe_capture_v4_close_on_giveback_r=1.0,
        profit_harvest_mfe_capture_v4_stale_minutes=30,
    )
    state = _filled_partial_runner_state(engine, mt5)
    state.entry_time = (datetime.now(timezone.utc) - timedelta(minutes=45)).isoformat()

    mt5.set_tick(
        bid=state.entry_price + 0.30 * state.sl_distance,
        ask=state.entry_price + 0.30 * state.sl_distance + 0.18,
    )
    assert engine.check_and_manage_trade({}) == (
        "vnext_profit_harvest_mfe_capture_v4_sl_modified"
    )
    mt5.set_tick(
        bid=state.entry_price - 0.05 * state.sl_distance,
        ask=state.entry_price - 0.05 * state.sl_distance + 0.18,
    )

    assert engine.check_and_manage_trade({}) == (
        "vnext_profit_harvest_mfe_capture_v4_stale_close"
    )
    assert engine.active_trade is None


def test_vnext_time_stop_policy_closes_at_configured_bar_count():
    from datetime import timedelta
    from src.components.execution import ExecutionEngine
    from src.mt5.mt5_mock import MockMT5

    mt5 = MockMT5(balance=100000.0)
    mt5.connect()
    engine = ExecutionEngine(
        mt5,
        {
            "risk": {"risk_per_trade_pct": 1.0},
            "gtos_vnext_runtime": {
                "moonshot_dynamic_execution_router_time_stop_bars": 1,
                "moonshot_dynamic_execution_router_time_stop_target_r": 1.5,
            },
        },
    )

    state = engine.open_trade(
        {
            "direction": "LONG",
            "entry_price": 2650.0,
            "stop_loss": 2640.0,
            "take_profit_1": 2665.0,
            "gtos_vnext_dynamic_policy_selected": "time_stop",
            "gtos_vnext_dynamic_policy_applied": True,
            "gtos_vnext_dynamic_policy_replaced_policy": "retired_static_baseline_comparator",
        },
        account_balance=100000.0,
    )

    assert state is not None
    state.entry_time = (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()
    mt5.set_tick(bid=state.entry_price + 1.0, ask=state.entry_price + 1.18)

    action = engine.check_time_stop_and_close()

    assert action == "vnext_time_stop"
    assert engine.active_trade is None


def test_vnext_pending_fill_missing_dynamic_be_params_fails_closed_and_retries():
    engine = _make_engine()
    params = {
        "direction": "LONG",
        "entry_price": 4421.39,
        "stop_loss": 4401.99,
        "take_profit_1": 4450.49,
        "take_profit_2": 0.0,
        "take_profit_3": 0.0,
        "risk_reward_ratio": 1.5,
        "gtos_vnext_dynamic_policy_selected": "be_after_trigger",
        "gtos_vnext_dynamic_policy_applied": True,
        "gtos_vnext_dynamic_policy_replaced_policy": "retired_static_baseline_comparator",
    }
    intent = engine.set_limit_intent(params, account_balance=100000.0)
    intent.gtos_vnext_dynamic_be_trigger_r = None
    intent.gtos_vnext_dynamic_final_target_r = None
    engine.pending_intent = intent

    result = engine.check_limit_fill(
        {
            "time": "2026-01-07 10:00:00",
            "open": 4430.0,
            "high": 4432.0,
            "low": 4421.00,
            "close": 4428.0,
        }
    )

    assert result is None
    assert engine.pending_intent is not None
    assert engine.mt5.order_send.call_count == 0


def test_restored_limit_fill_falls_back_to_current_balance():
    """Old restored intents without persisted balance must not size as min-lot."""
    engine = _make_engine()
    engine.mt5.get_tick.return_value = MagicMock(ask=4401.0, bid=4400.0)
    engine.mt5.get_account_balance.return_value = 101233.28
    params = {"direction": "SHORT", "entry_price": 4405.55,
              "stop_loss": 4426.00, "take_profit_1": 4374.91,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    engine.set_limit_intent(params, account_balance=100000.0)

    # Simulate a schema-compatible pickle produced before account_balance was
    # persisted: the intent exists, but the process has restarted and the
    # in-memory balance is gone.
    delattr(engine.pending_intent, "account_balance")
    engine._pending_account_balance = 0.0

    with patch.object(engine, "open_trade", return_value=MagicMock()) as mock_open:
        result = engine.check_limit_fill({"time": "t", "open": 4395.0,
                                           "high": 4406.0, "low": 4393.0,
                                           "close": 4394.0})

    assert result is not None
    assert mock_open.called
    _, kwargs = mock_open.call_args
    assert kwargs["account_balance"] == 101233.28

def test_check_limit_fill_triggers_on_touch():
    """LONG: candle low â‰¤ limit_price triggers open_trade."""
    engine = _make_engine()
    params = {"direction": "LONG", "entry_price": 4421.39,
              "stop_loss": 4401.99, "take_profit_1": 4450.49,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    engine.set_limit_intent(params, account_balance=100000.0)

    with patch.object(engine, "open_trade", return_value=MagicMock()) as mock_open:
        result = engine.check_limit_fill({"time": "2026-01-07 10:00:00",
                                           "open": 4430.0, "high": 4432.0,
                                           "low": 4421.00, "close": 4428.0})
    assert mock_open.called
    assert result is not None
    assert engine.pending_intent is None  # cleared after fill


def test_limit_fill_executes_market_order_at_current_tick_not_limit_price(
    tmp_path, monkeypatch,
):
    """Software pending limits use candle-touch intent, then a market deal."""
    from src.components import pending_limit_lifecycle_logger as lifecycle_mod
    from src.mt5.mt5_interface import OrderResult

    log_path = tmp_path / "pending_limit_lifecycle.jsonl"
    monkeypatch.setattr(
        lifecycle_mod,
        "PENDING_LIMIT_LIFECYCLE_LOG_PATH",
        str(log_path),
    )

    engine = _make_engine()
    engine.mt5.get_tick.return_value = MagicMock(
        ask=4460.0,
        bid=4459.0,
        spread_cents=100.0,
    )
    monkeypatch.setattr(engine, "_calculate_lots", lambda _distance, _risk, **_kwargs: 0.10)

    captured_request = {}

    def _fake_safe_place_order(request):
        captured_request.update(request)
        return OrderResult(
            retcode=10009,
            order=987654,
            volume=request["volume"],
            price=0.0,
            comment="filled_with_zero_price_fallback",
            deal=123456,
        )

    monkeypatch.setattr(engine, "safe_place_order", _fake_safe_place_order)

    params = {
        "direction": "LONG",
        "entry_price": 4421.39,
        "stop_loss": 4401.99,
        "take_profit_1": 4450.49,
        "take_profit_2": 0.0,
        "take_profit_3": 0.0,
        "risk_reward_ratio": 1.5,
    }
    engine.set_limit_intent(params, account_balance=100000.0)

    state = engine.check_limit_fill(
        {
            "time": "2026-01-07 10:00:00",
            "open": 4430.0,
            "high": 4461.0,
            "low": 4421.00,
            "close": 4458.0,
        },
        telemetry_context={"source_branch": "unit54_tier2_execution_model"},
    )

    assert state is not None
    assert engine.pending_intent is None
    assert captured_request["action"] == 1
    assert captured_request["price"] == 4460.0
    assert captured_request["price"] != params["entry_price"]
    assert state.entry_price == 4460.0
    assert state.entry_price != params["entry_price"]

    row = json.loads(log_path.read_text(encoding="utf-8").splitlines()[-1])
    assert row["intent_after_check"] == "order_send_success_filled"
    assert row["pending_order_mode"] == "INTERNAL_CANDLE_POLLED_INTENT"
    assert row["broker_pending_order_created"] is False
    assert row["pending_execution_model"] == (
        "INTERNAL_CANDLE_POLLED_MARKET_ORDER_ON_TOUCH"
    )
    assert row["broker_order_entry_mode"] == "MARKET_ORDER"
    assert row["broker_order_action"] == "TRADE_ACTION_DEAL"
    assert row["pending_limit_requested_price"] == params["entry_price"]
    assert row["market_order_requested_price"] == 4460.0
    assert row["market_order_price_source"] == "current_tick_ask_bid_at_touch"
    assert row["executed_entry_price"] == 4460.0
    assert row["execution_price_delta_from_limit"] == pytest.approx(38.61)


def test_vnext_selected_cell_order_uses_broker_volume_filling_and_deviation(monkeypatch):
    from src.components.execution import ExecutionEngine
    from src.mt5.mt5_interface import OrderResult

    engine = _make_engine()
    engine.mt5.get_tick.return_value = MagicMock(
        ask=4460.0,
        bid=4459.0,
        spread_cents=100.0,
    )
    _install_symbol_info(
        engine.mt5,
        trade_tick_size=0.01,
        trade_tick_value=1.0,
        volume_min=0.03,
        volume_step=0.03,
        volume_max=3.0,
        filling_mode=3,
        spread=17,
    )
    captured_request = {}

    def _fake_safe_place_order(request):
        captured_request.update(request)
        return OrderResult(
            retcode=10009,
            order=987655,
            volume=request["volume"],
            price=request["price"],
            comment="mock fill",
            deal=123457,
        )

    monkeypatch.setattr(engine, "safe_place_order", _fake_safe_place_order)
    state = engine.open_trade(
        {
            "direction": "LONG",
            "stop_loss": 4450.0,
            "take_profit_1": 4475.0,
            "gtos_vnext_selected_cell_risk_pct": 0.25,
            "gtos_vnext_selected_cell_risk_cell_id": "risk-cell-xau",
            "gtos_vnext_selected_cell_risk_decision_basis": "vnext_cell_evidence_tier:micro_positive_ev_floor",
        },
        account_balance=100000.0,
        risk_pct_override=0.25,
    )

    assert state is not None
    assert captured_request["volume"] == pytest.approx(0.24)
    assert captured_request["type_filling"] == 1
    assert captured_request["deviation"] == 17
    assert state.gtos_vnext_selected_cell_risk_cell_id == "risk-cell-xau"


def _enable_vnext_production_selected_cell(engine):
    engine.config.setdefault("risk", {})["risk_per_trade_pct"] = 2.0
    # A production-path fixture must identify the account whose broker-true
    # schedule it expects the live cost gate to charge. redacted_account covers both
    # XAUUSD and the GER30 broker alias exercised below.
    engine.config["broker_profile"] = {
        "broker": "redacted_account",
        "server": "redacted_account-Server 2",
        "broker_account_namespace": "redacted_account_live_bee34003",
    }
    engine.config["gtos_vnext_runtime"] = {
        "enabled": True,
        "mode": "production_replacement_vnext_moonshot",
        "apply_to_execution": True,
        "selected_cell_pretrade_cost_model_required": True,
        "selected_cell_pretrade_max_spread_r": 0.10,
        "selected_cell_commission_model_required": True,
        "selected_cell_allowed_commission_model_statuses": [
            "SELECTED_CELL_RISK_LEDGER_VERIFIED_NO_EXECUTION_CRITICAL_COMMISSION_GAP",
        ],
    }


def _vnext_production_params(**overrides):
    params = {
        "direction": "LONG",
        "stop_loss": 4450.0,
        "take_profit_1": 4475.0,
        "gtos_vnext_production_execution_path": True,
        "gtos_vnext_selected_cell_risk_pct": 0.25,
        "gtos_vnext_selected_cell_risk_cell_id": "risk-cell-xau",
        "gtos_vnext_selected_cell_risk_decision_basis": "selected_cell_current_broker_geometry",
        "gtos_vnext_selected_cell_risk_selected_policy": "momentum_exhaustion",
        "gtos_vnext_selected_cell_risk_source_policy": "be_after_trigger",
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
    }
    params.update(overrides)
    return params


def test_vnext_production_selected_cell_uses_selected_risk_without_profile_fallback(monkeypatch):
    from src.mt5.mt5_interface import OrderResult

    engine = _make_engine()
    _enable_vnext_production_selected_cell(engine)
    engine.mt5.get_tick.return_value = MagicMock(
        ask=4460.0,
        bid=4459.0,
        spread_cents=100.0,
    )
    engine.mt5.get_history_deals.return_value = []
    _install_symbol_info(engine.mt5, volume_min=0.03, volume_step=0.03, volume_max=3.0)
    captured_request = {}

    def _fake_safe_place_order(request):
        captured_request.update(request)
        return OrderResult(10009, 987656, request["volume"], request["price"], "mock fill", deal=123458)

    monkeypatch.setattr(engine, "safe_place_order", _fake_safe_place_order)
    state = engine.open_trade(
        _vnext_production_params(),
        account_balance=100000.0,
    )

    assert state is not None
    assert captured_request["volume"] == pytest.approx(0.24)
    assert state.gtos_vnext_selected_cell_risk_cell_id == "risk-cell-xau"


def test_vnext_selected_cell_sizes_index_from_order_calc_profit_not_tick_value(monkeypatch):
    from src.components.execution import ExecutionEngine
    from src.mt5.mt5_interface import OrderResult
    import src.components.execution as execution_module

    mt5 = MagicMock()
    mt5.get_tick.return_value = MagicMock(
        ask=25064.69,
        bid=25064.34,
        spread_cents=35.0,
    )
    mt5.get_history_deals.return_value = []
    config = {
        "market": {"symbol": "GER40", "mt5_symbol": "GER30"},
        "risk": {"risk_per_trade_pct": 2.0},
    }
    engine = ExecutionEngine(mt5, config)
    _enable_vnext_production_selected_cell(engine)
    info = _install_symbol_info(
        engine.mt5,
        trade_tick_size=0.01,
        trade_tick_value=0.012,
        volume_min=0.01,
        volume_step=0.01,
        volume_max=50.0,
        filling_mode=3,
        spread=35,
    )

    def _ger30_order_calc_profit(order_type, _symbol, volume, price_open, price_close):
        price_delta = (
            float(price_close) - float(price_open)
            if int(order_type) == 0
            else float(price_open) - float(price_close)
        )
        return price_delta * 11.63 * float(volume)

    engine.mt5._mt5 = SimpleNamespace(
        symbol_info=lambda _symbol: info,
        order_calc_profit=_ger30_order_calc_profit,
    )
    captured_request = {}

    def _fake_safe_place_order(request):
        captured_request.update(request)
        return OrderResult(10009, 242667071, request["volume"], 25064.34, "mock fill", deal=226451124)

    captured_slippage = {}
    monkeypatch.setattr(engine, "safe_place_order", _fake_safe_place_order)
    monkeypatch.setattr(
        execution_module,
        "record_slippage",
        lambda **kwargs: captured_slippage.update(kwargs),
    )
    state = engine.open_trade(
        _vnext_production_params(
            stop_loss=25009.49,
            take_profit_1=25229.94,
            gtos_vnext_selected_cell_risk_cell_id="risk-cell-ger30",
        ),
        account_balance=100610.10,
    )

    assert state is not None
    assert captured_request["volume"] == pytest.approx(0.39)
    assert captured_request["volume"] < 0.50
    assert state.cash_risk_amount == pytest.approx(248.25, rel=0.01)
    assert state.cash_risk_amount_status == "BROKER_ORDER_CALC_PROFIT_VERIFIED"
    assert captured_slippage["cash_risk_amount"] == pytest.approx(state.cash_risk_amount)
    assert captured_slippage["dynamic_exit_action_timeline"]["cash_risk_amount_status"] == (
        "BROKER_ORDER_CALC_PROFIT_VERIFIED"
    )
    assert state.broker_cash_risk_per_lot == pytest.approx(636.0, rel=0.01)
    diagnostic = state.broker_lot_sizing_diagnostic
    assert diagnostic["method"] == "broker_order_calc_profit"
    assert diagnostic["broker_cash_risk_per_lot"] == pytest.approx(641.98, rel=0.01)
    assert diagnostic["tick_value_cash_risk_per_lot"] == pytest.approx(66.24)
    assert diagnostic["broker_to_tick_value_risk_ratio"] == pytest.approx(9.69, rel=0.01)


def test_vnext_production_selected_cell_refuses_missing_selected_risk_before_profile_fallback(monkeypatch):
    engine = _make_engine()
    _enable_vnext_production_selected_cell(engine)
    engine.mt5.get_tick.return_value = MagicMock(
        ask=4460.0,
        bid=4459.0,
        spread_cents=100.0,
    )
    _install_symbol_info(engine.mt5)
    mock_order = MagicMock()
    monkeypatch.setattr(engine, "safe_place_order", mock_order)

    state = engine.open_trade(
        _vnext_production_params(
            gtos_vnext_selected_cell_risk_pct=None,
            gtos_vnext_selected_cell_risk_cell_id=None,
        ),
        account_balance=100000.0,
    )

    assert state is None
    mock_order.assert_not_called()


def test_vnext_production_selected_cell_refuses_risk_override_mismatch(monkeypatch):
    engine = _make_engine()
    _enable_vnext_production_selected_cell(engine)
    engine.mt5.get_tick.return_value = MagicMock(
        ask=4460.0,
        bid=4459.0,
        spread_cents=100.0,
    )
    _install_symbol_info(engine.mt5)
    mock_order = MagicMock()
    monkeypatch.setattr(engine, "safe_place_order", mock_order)

    state = engine.open_trade(
        _vnext_production_params(),
        account_balance=100000.0,
        risk_pct_override=1.0,
    )

    assert state is None
    mock_order.assert_not_called()


def test_vnext_production_selected_cell_refuses_missing_policy_risk_identity(monkeypatch):
    engine = _make_engine()
    _enable_vnext_production_selected_cell(engine)
    engine.mt5.get_tick.return_value = MagicMock(
        ask=4460.0,
        bid=4459.0,
        spread_cents=100.0,
    )
    _install_symbol_info(engine.mt5)
    mock_order = MagicMock()
    monkeypatch.setattr(engine, "safe_place_order", mock_order)

    state = engine.open_trade(
        _vnext_production_params(
            gtos_vnext_selected_cell_risk_selected_policy=None,
            gtos_vnext_selected_cell_risk_policy_identity_status=None,
        ),
        account_balance=100000.0,
    )

    assert state is None
    mock_order.assert_not_called()


def test_vnext_production_selected_cell_refuses_mismatched_policy_risk_identity(monkeypatch):
    engine = _make_engine()
    _enable_vnext_production_selected_cell(engine)
    engine.mt5.get_tick.return_value = MagicMock(
        ask=4460.0,
        bid=4459.0,
        spread_cents=100.0,
    )
    _install_symbol_info(engine.mt5)
    mock_order = MagicMock()
    monkeypatch.setattr(engine, "safe_place_order", mock_order)

    state = engine.open_trade(
        _vnext_production_params(
            gtos_vnext_selected_cell_risk_selected_policy="be_after_trigger",
            gtos_vnext_selected_cell_risk_policy_identity_status="exact_selected_policy_risk_match",
        ),
        account_balance=100000.0,
    )

    assert state is None
    mock_order.assert_not_called()


def test_vnext_production_selected_cell_refuses_missing_commission_model(monkeypatch):
    engine = _make_engine()
    _enable_vnext_production_selected_cell(engine)
    engine.mt5.get_tick.return_value = MagicMock(
        ask=4460.0,
        bid=4459.0,
        spread_cents=100.0,
    )
    _install_symbol_info(engine.mt5)
    mock_order = MagicMock()
    monkeypatch.setattr(engine, "safe_place_order", mock_order)

    state = engine.open_trade(
        _vnext_production_params(gtos_vnext_commission_model_status=None),
        account_balance=100000.0,
    )

    assert state is None
    mock_order.assert_not_called()


def test_vnext_production_risk_rejects_only_execution_critical_unresolved_reasons():
    engine = _make_engine()
    _enable_vnext_production_selected_cell(engine)

    risk_pct, error = engine._resolve_vnext_production_risk_pct(
        _vnext_production_params(
            gtos_vnext_selected_cell_risk_unresolved_reasons=[
                "commission_fields_not_exposed_in_current_symbol_info_snapshot",
            ],
            gtos_vnext_selected_cell_risk_execution_critical_unresolved_reasons=[],
        ),
        risk_pct_override=None,
    )

    assert risk_pct == pytest.approx(0.25)
    assert error is None

    risk_pct, error = engine._resolve_vnext_production_risk_pct(
        _vnext_production_params(
            gtos_vnext_selected_cell_risk_unresolved_reasons=[
                "commission_fields_not_exposed_in_current_symbol_info_snapshot",
            ],
            gtos_vnext_selected_cell_risk_execution_critical_unresolved_reasons=[
                "eligible_symbol_has_missing_broker_geometry_field_no_default_substitution_allowed",
            ],
        ),
        risk_pct_override=None,
    )

    assert risk_pct is None
    assert error.startswith("selected_cell_risk_has_unresolved_reasons:")


def test_vnext_production_risk_allows_runtime_reduction_below_selected_cell():
    engine = _make_engine()
    _enable_vnext_production_selected_cell(engine)

    risk_pct, error = engine._resolve_vnext_production_risk_pct(
        _vnext_production_params(),
        risk_pct_override=0.125,
    )

    assert risk_pct == pytest.approx(0.125)
    assert error is None


def test_vnext_production_risk_rejects_runtime_override_above_selected_cell():
    engine = _make_engine()
    _enable_vnext_production_selected_cell(engine)

    risk_pct, error = engine._resolve_vnext_production_risk_pct(
        _vnext_production_params(),
        risk_pct_override=0.5,
    )

    assert risk_pct is None
    assert error == "risk_pct_override_exceeds_selected_cell:override=0.5 selected=0.25"


def test_entry_fill_attempts_history_deal_reconciliation_or_marks_unresolved(monkeypatch):
    from src.mt5.mt5_interface import OrderResult
    import src.components.execution as execution_module

    engine = _make_engine()
    _enable_vnext_production_selected_cell(engine)
    engine.mt5.get_tick.return_value = MagicMock(
        ask=4460.0,
        bid=4459.0,
        spread_cents=100.0,
    )
    engine.mt5.get_history_deals.return_value = []
    _install_symbol_info(engine.mt5, volume_min=0.03, volume_step=0.03, volume_max=3.0)

    def _fake_safe_place_order(request):
        return OrderResult(10009, 987657, request["volume"], request["price"], "mock fill", deal=123459)

    captured_slippage = {}
    monkeypatch.setattr(engine, "safe_place_order", _fake_safe_place_order)
    monkeypatch.setattr(
        execution_module,
        "record_slippage",
        lambda **kwargs: captured_slippage.update(kwargs),
    )

    execution_policy_id = "vnext_exec_trailing_1r_gap_05r_cap_3r"
    state = engine.open_trade(
        _vnext_production_params(
            gtos_vnext_execution_policy_id=execution_policy_id,
            gtos_vnext_dynamic_policy_selected="trailing_runner",
            gtos_vnext_dynamic_policy_applied=True,
            gtos_vnext_dynamic_be_trigger_r=1.0,
            gtos_vnext_dynamic_final_target_r=3.0,
            gtos_vnext_dynamic_trail_gap_r=0.5,
            gtos_vnext_selected_cell_risk_selected_policy="trailing_runner",
        ),
        account_balance=100000.0,
    )

    assert state is not None
    assert engine.mt5.get_history_deals.call_count == 5
    assert captured_slippage["account_history_lookup_attempted"] is True
    assert captured_slippage["account_history_lookup_status"] == "UNRESOLVED_AFTER_HISTORY_ATTEMPT"
    assert captured_slippage["account_history_lookup_attempt_count"] == 5
    assert captured_slippage["commission_status"] == "UNRESOLVED_AFTER_HISTORY_ATTEMPT"
    assert captured_slippage["pretrade_cost_model_status"] == "PASSED"
    assert captured_slippage["dynamic_exit_action_timeline"]["execution_policy_id"] == execution_policy_id


def test_entry_fill_retries_history_deal_reconciliation_until_accounting_captured(monkeypatch):
    from datetime import datetime, timezone
    from src.mt5.mt5_interface import OrderResult
    import src.components.execution as execution_module

    engine = _make_engine()
    _enable_vnext_production_selected_cell(engine)
    engine.mt5.get_tick.return_value = MagicMock(
        ask=4460.0,
        bid=4459.0,
        spread_cents=100.0,
    )
    engine.mt5.get_history_deals.side_effect = [
        [],
        [
            {
                "ticket": 123459,
                "order": 987657,
                "position_id": 987657,
                "entry": 0,
                "time": datetime(2026, 5, 28, 23, 46, 5, tzinfo=timezone.utc),
                "commission": -0.65,
                "swap": 0.0,
            }
        ],
    ]
    _install_symbol_info(engine.mt5, volume_min=0.03, volume_step=0.03, volume_max=3.0)

    def _fake_safe_place_order(request):
        return OrderResult(10009, 987657, request["volume"], request["price"], "mock fill", deal=0)

    captured_slippage = {}
    monkeypatch.setattr(engine, "safe_place_order", _fake_safe_place_order)
    monkeypatch.setattr(
        execution_module,
        "record_slippage",
        lambda **kwargs: captured_slippage.update(kwargs),
    )

    state = engine.open_trade(
        _vnext_production_params(
            gtos_vnext_execution_policy_id="vnext_exec_partial_50_at_1r_be_runner_to_3r",
            gtos_vnext_dynamic_policy_selected="partial_be_runner",
            gtos_vnext_dynamic_policy_applied=True,
            gtos_vnext_dynamic_be_trigger_r=1.0,
            gtos_vnext_dynamic_final_target_r=3.0,
            gtos_vnext_selected_cell_risk_selected_policy="partial_be_runner",
        ),
        account_balance=100000.0,
    )

    assert state is not None
    assert engine.mt5.get_history_deals.call_count == 2
    assert captured_slippage["account_history_lookup_status"] == "RECONCILED_FROM_ACCOUNT_HISTORY"
    assert captured_slippage["account_history_lookup_attempt_count"] == 2
    assert captured_slippage["commission"] == -0.65
    assert captured_slippage["commission_status"] == "RECONCILED_FROM_ACCOUNT_HISTORY"
    assert captured_slippage["broker_fill_time_utc"] == "2026-05-28T23:46:05+00:00"


def test_close_fill_reconciles_history_deal_accounting_into_close_slippage(monkeypatch):
    from datetime import datetime, timezone
    from src.components.execution import TradeState
    from src.mt5.mt5_interface import OrderResult
    import src.components.execution as execution_module

    engine = _make_engine()
    engine.mt5.get_history_deals.return_value = [
        {
            "ticket": 777001,
            "order": 222333,
            "position_id": 987657,
            "entry": 1,
            "time": datetime(2026, 5, 29, 10, 15, 30, tzinfo=timezone.utc),
            "price": 4475.0,
            "commission": -0.65,
            "swap": -0.05,
            "profit": 100.0,
        }
    ]
    trade = TradeState(
        ticket=987657,
        direction="LONG",
        entry_price=4460.0,
        stop_loss=4450.0,
        take_profit_1=4480.0,
        take_profit_2=0.0,
        take_profit_3=0.0,
        initial_volume=1.0,
        current_volume=1.0,
        sl_distance=10.0,
        cash_risk_amount=200.0,
        entry_time="2026-05-29T10:00:00+00:00",
    )
    captured_close = {}
    monkeypatch.setattr(
        execution_module,
        "record_close_slippage",
        lambda **kwargs: captured_close.update(kwargs),
    )

    metadata = engine._record_close_slippage_event(
        trade=trade,
        result=OrderResult(10009, 222333, 1.0, 4475.0, "closed", deal=0),
        close_reason="manual",
        close_event_type="FULL_POSITION_CLOSE",
        close_price=4475.0,
        close_volume=1.0,
        expected_close_price=4474.9,
        spread_at_request=12.0,
        partial_close=False,
        remaining_volume=0.0,
    )

    assert engine.mt5.get_history_deals.call_count == 1
    assert metadata["account_history_lookup_status"] == "RECONCILED_FROM_ACCOUNT_HISTORY"
    assert metadata["mt5_deal_id"] == 777001
    assert metadata["commission"] == -0.65
    assert metadata["swap"] == -0.05
    assert metadata["broker_profit"] == 100.0
    assert captured_close["mt5_deal_id"] == 777001
    assert captured_close["commission"] == -0.65
    assert captured_close["swap"] == -0.05
    assert captured_close["broker_profit"] == 100.0
    assert captured_close["close_time"] == "2026-05-29T10:15:30+00:00"
    assert captured_close["accounting_source"] == "MT5_HISTORY_DEALS_READONLY"


def test_close_fill_history_deal_reconciliation_fails_open(monkeypatch):
    from src.components.execution import TradeState
    from src.mt5.mt5_interface import OrderResult
    import src.components.execution as execution_module

    engine = _make_engine()
    engine.mt5.get_history_deals.return_value = []
    trade = TradeState(
        ticket=987657,
        direction="SHORT",
        entry_price=4460.0,
        stop_loss=4470.0,
        take_profit_1=4440.0,
        take_profit_2=0.0,
        take_profit_3=0.0,
        initial_volume=1.0,
        current_volume=1.0,
        sl_distance=10.0,
        entry_time="2026-05-29T10:00:00+00:00",
    )
    captured_close = {}
    monkeypatch.setattr(
        execution_module,
        "record_close_slippage",
        lambda **kwargs: captured_close.update(kwargs),
    )

    metadata = engine._record_close_slippage_event(
        trade=trade,
        result=OrderResult(10009, 222333, 1.0, 4450.0, "closed", deal=0),
        close_reason="manual",
        close_event_type="FULL_POSITION_CLOSE",
        close_price=4450.0,
        close_volume=1.0,
        expected_close_price=4450.1,
        spread_at_request=12.0,
        partial_close=False,
        remaining_volume=0.0,
    )

    assert engine.mt5.get_history_deals.call_count == 3
    assert metadata["account_history_lookup_status"] == "UNRESOLVED_AFTER_HISTORY_ATTEMPT"
    assert metadata["commission"] is None
    assert metadata["swap"] is None
    assert captured_close["commission"] is None
    assert captured_close["swap"] is None
    assert captured_close["accounting_source"] == "EXECUTION_ORDER_RESULT"


def test_zero_order_result_uses_broker_entry_deal_price_for_state_and_slippage(monkeypatch):
    from datetime import datetime, timezone
    from src.mt5.mt5_interface import OrderResult
    import src.components.execution as execution_module

    engine = _make_engine()
    _enable_vnext_production_selected_cell(engine)
    engine.mt5.get_tick.return_value = MagicMock(
        ask=4460.0,
        bid=4459.0,
        spread_cents=100.0,
    )
    engine.mt5.get_history_deals.return_value = [
        {
            "ticket": 123459,
            "order": 987657,
            "position_id": 987657,
            "entry": 0,
            "time": datetime(2026, 5, 28, 23, 46, 5, tzinfo=timezone.utc),
            "price": 4458.5,
            "commission": -0.65,
            "swap": 0.0,
        }
    ]
    _install_symbol_info(engine.mt5, volume_min=0.03, volume_step=0.03, volume_max=3.0)

    def _fake_safe_place_order(request):
        return OrderResult(10009, 987657, request["volume"], 0.0, "zero broker result", deal=123459)

    captured_slippage = {}
    monkeypatch.setattr(engine, "safe_place_order", _fake_safe_place_order)
    monkeypatch.setattr(
        execution_module,
        "record_slippage",
        lambda **kwargs: captured_slippage.update(kwargs),
    )

    state = engine.open_trade(
        _vnext_production_params(
            stop_loss=4450.0,
            gtos_vnext_execution_policy_id="vnext_exec_partial_50_at_1r_be_runner_to_3r",
            gtos_vnext_dynamic_policy_selected="partial_be_runner",
            gtos_vnext_dynamic_policy_applied=True,
            gtos_vnext_dynamic_be_trigger_r=1.0,
            gtos_vnext_dynamic_final_target_r=3.0,
            gtos_vnext_selected_cell_risk_selected_policy="partial_be_runner",
        ),
        account_balance=100000.0,
    )

    assert state is not None
    assert state.entry_price == pytest.approx(4458.5)
    assert state.take_profit_1 == pytest.approx(4468.5)
    assert state.take_profit_2 == pytest.approx(4488.5)
    assert captured_slippage["fill_price"] == pytest.approx(4458.5)
    assert captured_slippage["executed_entry_price"] == pytest.approx(4458.5)
    assert captured_slippage["raw_order_result_fill_price"] == 0.0
    assert captured_slippage["fill_price_source_override"] == "broker_entry_deal_history"
    assert captured_slippage["fill_price_status_override"] == "BROKER_HISTORY_RECONCILED"
    assert captured_slippage["account_history_lookup_match_keys"]["price"] == pytest.approx(4458.5)


def test_vnext_selected_cell_order_fails_closed_without_broker_geometry(monkeypatch):
    engine = _make_engine()
    engine.mt5.get_tick.return_value = MagicMock(
        ask=4460.0,
        bid=4459.0,
        spread_cents=100.0,
    )
    engine.mt5._mt5 = SimpleNamespace(symbol_info=lambda _symbol: None)
    mock_order = MagicMock()
    monkeypatch.setattr(engine, "safe_place_order", mock_order)

    state = engine.open_trade(
        {
            "direction": "LONG",
            "stop_loss": 4450.0,
            "take_profit_1": 4475.0,
            "gtos_vnext_selected_cell_risk_pct": 0.25,
            "gtos_vnext_selected_cell_risk_cell_id": "risk-cell-xau",
        },
        account_balance=100000.0,
        risk_pct_override=0.25,
    )

    assert state is None
    mock_order.assert_not_called()


def test_vnext_selected_cell_order_fails_closed_without_order_calc_profit(monkeypatch):
    engine = _make_engine()
    engine.mt5.get_tick.return_value = MagicMock(
        ask=4460.0,
        bid=4459.0,
        spread_cents=100.0,
    )
    info = _install_symbol_info(engine.mt5)
    engine.mt5._mt5 = SimpleNamespace(symbol_info=lambda _symbol: info)
    mock_order = MagicMock()
    monkeypatch.setattr(engine, "safe_place_order", mock_order)

    state = engine.open_trade(
        {
            "direction": "LONG",
            "stop_loss": 4450.0,
            "take_profit_1": 4475.0,
            "gtos_vnext_selected_cell_risk_pct": 0.25,
            "gtos_vnext_selected_cell_risk_cell_id": "risk-cell-xau",
        },
        account_balance=100000.0,
        risk_pct_override=0.25,
    )

    assert state is None
    assert engine._last_lot_sizing_diagnostic["status"] == (
        "broker_order_calc_profit_required_unavailable"
    )
    mock_order.assert_not_called()


def test_vnext_be_final_close_uses_broker_geometry_not_legacy_deviation(monkeypatch):
    from src.components.execution import TradeState
    from src.mt5.mt5_interface import OrderResult

    engine = _make_engine()
    engine.mt5.get_tick.return_value = MagicMock(
        ask=4480.0,
        bid=4479.0,
        spread_cents=100.0,
    )
    _install_symbol_info(
        engine.mt5,
        volume_min=0.03,
        volume_step=0.03,
        volume_max=3.0,
        filling_mode=3,
        spread=31,
    )
    monkeypatch.setattr("src.components.execution.record_close_slippage", lambda **_kwargs: None)
    captured_request = {}

    def _fake_safe_place_order(request):
        captured_request.update(request)
        return OrderResult(
            retcode=10009,
            order=765432,
            volume=request["volume"],
            price=4479.0,
            comment="mock close",
            deal=123458,
        )

    monkeypatch.setattr(engine, "safe_place_order", _fake_safe_place_order)
    trade = TradeState(
        ticket=4242,
        direction="LONG",
        entry_price=4460.0,
        stop_loss=4450.0,
        take_profit_1=4475.0,
        take_profit_2=4490.0,
        take_profit_3=0.0,
        initial_volume=0.24,
        current_volume=0.24,
        sl_distance=10.0,
        gtos_vnext_dynamic_policy_selected="be_after_trigger",
        gtos_vnext_dynamic_policy_applied=True,
        gtos_vnext_dynamic_be_after_trigger_active=True,
        gtos_vnext_dynamic_be_trigger_r=1.5,
        gtos_vnext_dynamic_final_target_r=3.0,
        gtos_vnext_dynamic_final_target_price=4490.0,
        gtos_vnext_selected_cell_risk_pct=0.25,
        gtos_vnext_selected_cell_risk_cell_id="risk-cell-xau",
    )
    engine.active_trade = trade

    result = engine._execute_tp2_partial(trade, MagicMock())

    assert result == "tp2_final_target_vnext_be_after_trigger"
    assert captured_request["volume"] == pytest.approx(0.24)
    assert captured_request["deviation"] == 31
    assert captured_request["type_filling"] == 1
    assert captured_request["comment"] == "TP2_vnext_be_final"


def test_vnext_close_position_fails_closed_without_broker_geometry(monkeypatch):
    from src.components.execution import TradeState

    engine = _make_engine()
    engine.mt5.get_tick.return_value = MagicMock(ask=4480.0, bid=4479.0)
    engine.mt5._mt5 = SimpleNamespace(symbol_info=lambda _symbol: None)
    mock_order = MagicMock()
    monkeypatch.setattr(engine, "safe_place_order", mock_order)
    engine.active_trade = TradeState(
        ticket=4242,
        direction="LONG",
        entry_price=4460.0,
        stop_loss=4450.0,
        take_profit_1=4475.0,
        take_profit_2=4490.0,
        take_profit_3=0.0,
        initial_volume=0.24,
        current_volume=0.24,
        sl_distance=10.0,
        gtos_vnext_dynamic_policy_selected="be_after_trigger",
        gtos_vnext_dynamic_policy_applied=True,
        gtos_vnext_dynamic_be_after_trigger_active=True,
        gtos_vnext_selected_cell_risk_pct=0.25,
        gtos_vnext_selected_cell_risk_cell_id="risk-cell-xau",
    )

    assert engine.close_position("vnext_time_stop") is False
    mock_order.assert_not_called()


def test_check_limit_fill_no_trigger_above():
    """LONG: candle low > limit_price â€” does not trigger."""
    engine = _make_engine()
    params = {"direction": "LONG", "entry_price": 4421.39,
              "stop_loss": 4401.99, "take_profit_1": 4450.49,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    engine.set_limit_intent(params, account_balance=100000.0)

    result = engine.check_limit_fill({"time": "t", "open": 4430.0, "high": 4432.0,
                                       "low": 4425.0, "close": 4428.0})
    assert result is None
    assert engine.pending_intent is not None  # still pending


def test_check_limit_fill_cancels_long_when_tp_reached_without_entry_touch():
    """LONG: if TP area is reached before entry touch, the stale intent is gone."""
    engine = _make_engine()
    params = {"direction": "LONG", "entry_price": 4421.39,
              "stop_loss": 4401.99, "take_profit_1": 4450.49,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    engine.set_limit_intent(params, account_balance=100000.0)

    with patch.object(engine, "open_trade") as mock_open:
        result = engine.check_limit_fill({"time": "t", "open": 4445.0, "high": 4451.0,
                                           "low": 4425.0, "close": 4448.0})
    assert result is None
    assert not mock_open.called
    assert engine.pending_intent is None


def test_check_limit_fill_cancels_short_when_tp_reached_without_entry_touch():
    """SHORT: if TP area is reached before entry touch, the stale intent is gone."""
    engine = _make_engine()
    params = {"direction": "SHORT", "entry_price": 4405.55,
              "stop_loss": 4426.00, "take_profit_1": 4374.91,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    engine.set_limit_intent(params, account_balance=100000.0)

    with patch.object(engine, "open_trade") as mock_open:
        result = engine.check_limit_fill({"time": "t", "open": 4385.0, "high": 4390.0,
                                           "low": 4374.0, "close": 4380.0})
    assert result is None
    assert not mock_open.called
    assert engine.pending_intent is None


def test_check_limit_fill_expires():
    """After 48 hours of clock time, intent expires regardless of candle count."""
    engine = _make_engine()
    params = {"direction": "LONG", "entry_price": 4421.39,
              "stop_loss": 4401.99, "take_profit_1": 4450.49,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    engine.set_limit_intent(params, account_balance=100000.0)

    # Backdate placed_time to simulate 49h elapsed â€” no mocking needed
    from datetime import datetime, timezone, timedelta
    past_time = (datetime.now(timezone.utc) - timedelta(hours=49)).isoformat()
    engine.pending_intent.placed_time = past_time

    non_trigger = {"time": "t", "open": 4500.0, "high": 4502.0,
                   "low": 4498.0, "close": 4500.0}
    result = engine.check_limit_fill(non_trigger)
    assert result is None
    assert engine.pending_intent is None

def test_cancel_limit_intent():
    """cancel_limit_intent clears pending_intent."""
    engine = _make_engine()
    params = {"direction": "LONG", "entry_price": 4421.39,
              "stop_loss": 4401.99, "take_profit_1": 4450.49,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    engine.set_limit_intent(params, account_balance=100000.0)
    assert engine.pending_intent is not None
    engine.cancel_limit_intent(reason="test")
    assert engine.pending_intent is None

def test_short_limit_triggers_on_high():
    """SHORT: candle high >= limit_price triggers open_trade."""
    engine = _make_engine()
    # Realistic tick for SHORT fill: bid must be below SL for viability check
    engine.mt5.get_tick.return_value = MagicMock(ask=4401.0, bid=4400.0)
    params = {"direction": "SHORT", "entry_price": 4405.55,
              "stop_loss": 4426.00, "take_profit_1": 4374.91,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    engine.set_limit_intent(params, account_balance=100000.0)

    with patch.object(engine, "open_trade", return_value=MagicMock()) as mock_open:
        result = engine.check_limit_fill({"time": "t", "open": 4395.0, "high": 4406.0,
                                           "low": 4393.0, "close": 4394.0})
    assert mock_open.called
    assert result is not None


# â”€â”€ Limit Fill Viability Tests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def test_limit_fill_abort_price_beyond_sl_long():
    """LONG: price below SL at fill time -> cancel intent, don't execute."""
    engine = _make_engine()
    # Tick is below the SL â€” price blew through
    engine.mt5.get_tick.return_value = MagicMock(ask=4395.0, bid=4394.0)
    params = {"direction": "LONG", "entry_price": 4421.39,
              "stop_loss": 4401.99, "take_profit_1": 4450.49,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    engine.set_limit_intent(params, account_balance=100000.0)

    with patch.object(engine, "open_trade") as mock_open:
        result = engine.check_limit_fill({"time": "t", "open": 4410.0, "high": 4412.0,
                                           "low": 4393.0, "close": 4395.0})
    assert not mock_open.called
    assert result is None
    assert engine.pending_intent is None  # cancelled, not preserved


def test_limit_fill_abort_price_beyond_sl_short():
    """SHORT: price above SL at fill time -> cancel intent, don't execute."""
    engine = _make_engine()
    # Tick is above the SL â€” price blew through
    engine.mt5.get_tick.return_value = MagicMock(ask=4430.0, bid=4429.0)
    params = {"direction": "SHORT", "entry_price": 4405.55,
              "stop_loss": 4426.00, "take_profit_1": 4374.91,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    engine.set_limit_intent(params, account_balance=100000.0)

    with patch.object(engine, "open_trade") as mock_open:
        result = engine.check_limit_fill({"time": "t", "open": 4395.0, "high": 4435.0,
                                           "low": 4393.0, "close": 4430.0})
    assert not mock_open.called
    assert result is None
    assert engine.pending_intent is None


def test_limit_fill_abort_sl_too_close():
    """Remaining SL cushion < sl_absolute_min -> cancel intent."""
    from src.components.execution import ExecutionEngine
    mt5 = MagicMock()
    # Price very close to SL (only 3.0 away, sl_absolute_min is 5.0)
    mt5.get_tick.return_value = MagicMock(ask=4405.0, bid=4404.0)
    config = {"market": {"symbol": "XAUUSD"},
              "risk": {"risk_per_trade_pct": 1.0, "sl_absolute_min": 5.0}}
    engine = ExecutionEngine(mt5, config)

    params = {"direction": "LONG", "entry_price": 4421.39,
              "stop_loss": 4401.99, "take_profit_1": 4450.49,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    engine.set_limit_intent(params, account_balance=100000.0)

    with patch.object(engine, "open_trade") as mock_open:
        result = engine.check_limit_fill({"time": "t", "open": 4410.0, "high": 4412.0,
                                           "low": 4404.0, "close": 4405.0})
    assert not mock_open.called
    assert result is None
    assert engine.pending_intent is None


def test_limit_fill_retry_on_no_tick():
    """No tick data at fill time -> keep intent for retry next candle."""
    engine = _make_engine()
    engine.mt5.get_tick.return_value = None
    params = {"direction": "LONG", "entry_price": 4421.39,
              "stop_loss": 4401.99, "take_profit_1": 4450.49,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    engine.set_limit_intent(params, account_balance=100000.0)

    result = engine.check_limit_fill({"time": "t", "open": 4425.0, "high": 4426.0,
                                       "low": 4420.0, "close": 4422.0})
    assert result is None
    assert engine.pending_intent is not None  # preserved for retry


def test_limit_fill_retry_on_order_failure():
    """open_trade returns None (MT5 error) -> keep intent for retry."""
    engine = _make_engine()
    params = {"direction": "LONG", "entry_price": 4421.39,
              "stop_loss": 4401.99, "take_profit_1": 4450.49,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    engine.set_limit_intent(params, account_balance=100000.0)

    with patch.object(engine, "open_trade", return_value=None):
        result = engine.check_limit_fill({"time": "t", "open": 4425.0, "high": 4426.0,
                                           "low": 4420.0, "close": 4422.0})
    assert result is None
    assert engine.pending_intent is not None  # preserved for retry


def test_limit_fill_passes_original_sl_distance():
    """open_trade receives sl_distance_override = original limit->SL distance."""
    engine = _make_engine()
    params = {"direction": "LONG", "entry_price": 4421.39,
              "stop_loss": 4401.99, "take_profit_1": 4450.49,
              "take_profit_2": 0.0, "take_profit_3": 0.0, "risk_reward_ratio": 1.5}
    engine.set_limit_intent(params, account_balance=100000.0)

    expected_sl_dist = abs(4421.39 - 4401.99)  # 19.40

    with patch.object(engine, "open_trade", return_value=MagicMock()) as mock_open:
        engine.check_limit_fill({"time": "t", "open": 4425.0, "high": 4426.0,
                                  "low": 4420.0, "close": 4422.0})

    assert mock_open.called
    _, kwargs = mock_open.call_args
    assert "sl_distance_override" in kwargs
    assert abs(kwargs["sl_distance_override"] - expected_sl_dist) < 0.01


def test_limit_fill_open_trade_uses_original_risk_distance_for_r_tracking(monkeypatch):
    """A market fill at/near SL must not collapse Telegram R to zero."""
    from src.mt5.mt5_interface import OrderResult

    engine = _make_engine()
    engine.mt5.get_tick.return_value = MagicMock(
        ask=4460.0,
        bid=4459.0,
        spread_cents=100.0,
    )
    captured_sizing_distance = {}

    def _fake_calculate_lots(distance, _risk, **_kwargs):
        captured_sizing_distance["distance"] = distance
        return 0.10

    monkeypatch.setattr(engine, "_calculate_lots", _fake_calculate_lots)
    monkeypatch.setattr(
        engine,
        "safe_place_order",
        lambda request: OrderResult(
            retcode=10009,
            order=987656,
            volume=request["volume"],
            price=request["price"],
            comment="mock fill",
            deal=123458,
        ),
    )

    state = engine.open_trade(
        {
            "direction": "SHORT",
            "stop_loss": 4459.0,
            "take_profit_1": 4399.0,
            "take_profit_2": 0.0,
            "take_profit_3": 0.0,
            "risk_reward_ratio": 3.0,
        },
        account_balance=100000.0,
        sl_distance_override=20.0,
    )

    assert state is not None
    assert captured_sizing_distance["distance"] == pytest.approx(20.0)
    assert state.sl_distance == pytest.approx(20.0)
    assert (state.entry_price - 4439.0) / state.sl_distance == pytest.approx(1.0)


def test_entry_in_ob_passes_when_entry_is_ob_high():
    """
    Core backtest assumption: when AI quotes entry_price = ob_high,
    _check_entry_in_ob must PASS (entry is at the zone top = within zone).

    This is the prompt fix that unblocks 97% of previously rejected setups.
    Backtest validated 61.4% WR (+82R) assuming this check passes.
    If this test fails, the architecture fix is broken.
    """
    from src.components.verification import _check_entry_in_ob

    analysis = MagicMock()
    analysis.trade_parameters.entry_price = 4421.39   # ob_high
    analysis.trade_parameters.direction = "LONG"
    analysis.trade_parameters.stop_loss = 4401.99

    matched_ob = MagicMock()
    matched_ob.low = 4405.55
    matched_ob.high = 4421.39

    config = {"verification": {"ob_tolerance_pct": 0.2}}
    result = _check_entry_in_ob(analysis, matched_ob, None, config)

    assert result.status == "PASS", (
        f"entry_price=ob_high must PASS entry_in_ob. Got: {result.status} â€” {result.detail}"
    )
