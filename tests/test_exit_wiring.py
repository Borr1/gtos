"""Tests for exit data wiring between orchestrator and trade capture.

Tests the WIRING: MFE/MAE tracking, partial close handling,
blended R computation, exit finalization, and state cleanup.
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch
from dataclasses import dataclass, field

import pytest

from src.components import orchestrator as _orch_mod
from src.components.orchestrator import SessionOrchestrator
from src.components.trade_capture import (
    create_trade_record,
    update_execution,
    save_trade_record,
    load_trade_record,
    update_exit,
)
from src.components.execution import TradeState
from src.mt5.mt5_interface import MAGIC_NUMBER, PositionInfo


# Isolation fixture — redirect any trade_capture write (the default base_path
# config at line 35 is "knowledge_base/trade_records") so a test that forgets
# to override its base_path cannot hit live knowledge_base/trade_records.
# chdir turns every Path("knowledge_base/...") into tmp_path/knowledge_base/....
# Also patch LOCK_DIR belt-and-braces (orchestrator.__new__ bypasses __init__
# so no lock is acquired, but keep the guard for future changes).
@pytest.fixture(autouse=True)
def _isolate_production_paths(tmp_path, monkeypatch):
    tmp_meta = tmp_path / "meta"
    tmp_meta.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(_orch_mod, "LOCK_DIR", str(tmp_meta))
    monkeypatch.chdir(tmp_path)
    yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_orchestrator() -> SessionOrchestrator:
    """Create a minimal orchestrator for testing exit wiring methods."""
    orch = object.__new__(SessionOrchestrator)
    orch.config = {
        "market": {"symbol": "XAUUSD"},
        "trade_capture": {"enabled": True, "base_path": "knowledge_base/trade_records"},
    }
    orch._symbol = "XAUUSD"
    orch._mt5_symbol = "XAUUSD"
    orch.mt5 = MagicMock()
    orch.execution = MagicMock()
    # Init tracking state to None
    orch._active_trade_record = None
    orch._active_trade_record_path = None
    orch._trade_entry_price = None
    orch._trade_direction = None
    orch._trade_sl_distance = None
    orch._trade_entry_time = None
    orch._mfe_price = None
    orch._mae_price = None
    orch._last_tick_price = None
    return orch


def _make_trade_state(**overrides) -> TradeState:
    """Create a TradeState for testing."""
    defaults = dict(
        ticket=0,
        direction="LONG",
        entry_price=3042.0,
        stop_loss=3035.0,
        take_profit_1=3053.5,
        take_profit_2=0,
        take_profit_3=0,
        initial_volume=0.10,
        current_volume=0.10,
        sl_distance=7.0,
        trade_id="tr_2026-04-07_0745",
        entry_time="2026-04-07T07:45:00+00:00",
    )
    defaults.update(overrides)
    return TradeState(**defaults)


def _make_record_with_execution(tmp_path=None) -> dict:
    """Create a trade record with execution data filled in."""
    record = create_trade_record(
        symbol="XAUUSD",
        kill_zone="london",
        candle_time="2026-04-07T07:45:00+00:00",
        mso={"timeframes": {}},
        prompt_system="sys",
        prompt_user="usr",
        ai_response={
            "decision": "CANDIDATE",
            "confidence_score": 80,
            "framework": "ob_retest",
            "reasoning": {"setup_grade": "A+"},
            "trade_parameters": {
                "direction": "LONG",
                "entry_price": 3042.50,
                "stop_loss": 3035.00,
                "take_profit_1": 3053.75,
                "risk_reward_ratio": 1.5,
            },
        },
        cross_instrument_context="",
        session_memory="",
        config={"trade_capture": {"enabled": True, "save_mso": True, "save_prompt": True}},
    )
    update_execution(record, {
        "executed": True,
        "timestamp": "2026-04-07T07:45:12+00:00",
        "entry_price_actual": 3042.0,
        "entry_spread": 0.25,
        "slippage": 0.10,
        "mt5_ticket": 0,
        "lot_size": 0.10,
        "risk_pct": 1.0,
    })
    record["decision_pipeline"]["final_outcome"] = "EXECUTED"
    return record


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestMFEMAELong:
    """test_mfe_mae_long_updates — price sequence for LONG trade."""

    def test_long_mfe_mae(self):
        orch = _make_orchestrator()
        ts = _make_trade_state(direction="LONG", entry_price=3042.0, sl_distance=7.0)
        orch._init_trade_tracking(ts)

        assert orch._mfe_price == 3042.0
        assert orch._mae_price == 3042.0

        # Price goes up to 3055
        orch._update_mfe_mae(3055.0)
        assert orch._mfe_price == 3055.0
        assert orch._mae_price == 3042.0

        # Price drops to 3038
        orch._update_mfe_mae(3038.0)
        assert orch._mfe_price == 3055.0
        assert orch._mae_price == 3038.0

        # Price recovers to 3060
        orch._update_mfe_mae(3060.0)
        assert orch._mfe_price == 3060.0
        assert orch._mae_price == 3038.0


class TestMFEMAEShort:
    """test_mfe_mae_short_updates — price sequence for SHORT trade."""

    def test_short_mfe_mae(self):
        orch = _make_orchestrator()
        ts = _make_trade_state(direction="SHORT", entry_price=3080.0, sl_distance=7.0)
        orch._init_trade_tracking(ts)

        # Price drops to 3065 (favorable)
        orch._update_mfe_mae(3065.0)
        assert orch._mfe_price == 3065.0
        assert orch._mae_price == 3080.0

        # Price spikes to 3088 (adverse)
        orch._update_mfe_mae(3088.0)
        assert orch._mfe_price == 3065.0
        assert orch._mae_price == 3088.0

        # Price drops to 3060 (new MFE)
        orch._update_mfe_mae(3060.0)
        assert orch._mfe_price == 3060.0
        assert orch._mae_price == 3088.0


class TestMFEMAECandleExtremes:
    """test_mfe_mae_uses_candle_extremes — both high and low update tracking."""

    def test_candle_high_low(self):
        orch = _make_orchestrator()
        ts = _make_trade_state(direction="LONG", entry_price=3042.0, sl_distance=7.0)
        orch._init_trade_tracking(ts)

        # Simulate candle with high=3055, low=3038
        # Both values should be checked
        orch._update_mfe_mae(3055.0)  # candle high
        orch._update_mfe_mae(3038.0)  # candle low
        assert orch._mfe_price == 3055.0
        assert orch._mae_price == 3038.0


class TestFullCloseSavesExit:
    """test_full_close_saves_exit_to_disk — close at TP1, verify exit on disk."""

    def test_exit_saved(self, tmp_path):
        orch = _make_orchestrator()
        record = _make_record_with_execution()

        # Save initial record to disk
        base = str(tmp_path / "trade_records")
        path = save_trade_record(record, base)
        assert path is not None

        # Set up orchestrator state
        ts = _make_trade_state(direction="LONG", entry_price=3042.0,
                               sl_distance=7.0, initial_volume=0.10)
        ts.partial_close_events = [{
            "type": "TP1_FULL_CLOSE",
            "time": "2026-04-07T08:30:00+00:00",
            "price": 3053.5,
            "volume_closed": 0.10,
        }]

        orch._init_trade_tracking(ts)
        orch._active_trade_record = record
        orch._active_trade_record_path = path
        orch._last_tick_price = 3053.5
        orch.config["trade_capture"]["base_path"] = base

        # Finalize exit
        orch._finalize_exit(ts, "tp1_full_close")

        # Load from disk and verify
        loaded = load_trade_record(path)
        assert loaded["exit"] is not None
        assert loaded["exit"]["exit_type"] == "tp1_full_close"
        assert loaded["exit"]["exit_price"] == 3053.5
        assert loaded["exit"]["actual_r"] == pytest.approx(1.6429, abs=0.01)


class TestPartialCloseDoesNotSaveExit:
    """test_partial_close_does_not_save_exit — partial TP1 does not finalize."""

    def test_partial_no_exit(self):
        orch = _make_orchestrator()
        record = _make_record_with_execution()

        ts = _make_trade_state(direction="LONG", entry_price=3042.0,
                               sl_distance=7.0, initial_volume=0.10,
                               current_volume=0.05)
        ts.partial_close_events = [{
            "type": "TP1_PARTIAL",
            "time": "2026-04-07T08:15:00+00:00",
            "price": 3053.5,
            "volume_closed": 0.05,
        }]

        orch._init_trade_tracking(ts)
        orch._active_trade_record = record
        orch._active_trade_record_path = "/tmp/fake"

        # Simulate check_and_manage_trade returning "tp1_partial"
        # Trade is still active — execution.active_trade is NOT None
        orch.execution.active_trade = ts
        orch.execution.check_and_manage_trade = MagicMock(return_value="tp1_partial")

        # Mock tick
        tick = MagicMock()
        tick.bid = 3053.5
        tick.ask = 3053.7
        orch.mt5.get_tick = MagicMock(return_value=tick)

        orch._check_trade_and_capture()

        # Exit should NOT be called since trade is still active
        assert record["exit"] is None

    def test_monitoring_result_does_not_rewrite_active_record(self):
        orch = _make_orchestrator()
        record = _make_record_with_execution()
        ts = _make_trade_state(direction="LONG", entry_price=3042.0)
        orch._init_trade_tracking(ts)
        orch._active_trade_record = record
        orch._active_trade_record_path = "/tmp/fake"
        orch.execution.active_trade = ts
        orch.execution.check_and_manage_trade = MagicMock(return_value="monitoring")
        tick = MagicMock()
        tick.bid = 3042.0
        tick.ask = 3042.2
        orch.mt5.get_tick = MagicMock(return_value=tick)

        with patch("src.components.orchestrator.save_trade_record") as save_mock:
            orch._check_trade_and_capture()

        save_mock.assert_not_called()

    def test_partial_persists_residual_lifecycle_truth(self, tmp_path):
        orch = _make_orchestrator()
        base = str(tmp_path / "trade_records")
        orch.config["trade_capture"]["base_path"] = base
        record = _make_record_with_execution()
        path = save_trade_record(record, base)

        ts = _make_trade_state(
            ticket=222222,
            direction="LONG",
            entry_price=3042.0,
            stop_loss=3042.0,
            take_profit_1=3053.5,
            take_profit_2=3065.0,
            initial_volume=0.10,
            current_volume=0.05,
        )
        ts.tp1_hit = True
        ts.sl_at_breakeven = True
        ts.partial_close_events = [{
            "type": "TP1_PARTIAL_VNEXT_PARTIAL_BE_RUNNER",
            "time": "2026-04-07T08:15:00+00:00",
            "price": 3053.5,
            "volume_closed": 0.05,
            "remaining_volume": 0.05,
            "old_ticket": 111111,
            "new_ticket": 222222,
            "sl_at_breakeven": True,
        }]

        orch._init_trade_tracking(ts)
        orch._active_trade_record = record
        orch._active_trade_record_path = path
        orch.execution.active_trade = ts
        orch.execution.check_and_manage_trade = MagicMock(
            return_value="tp1_partial_vnext_partial_be_runner"
        )
        orch.mt5.get_positions.return_value = [
            PositionInfo(
                ticket=222222,
                symbol="XAUUSD",
                type=0,
                volume=0.05,
                price_open=3042.0,
                sl=3042.0,
                tp=3065.0,
                profit=0.0,
                magic=MAGIC_NUMBER,
                comment="TP1_vnext_partia",
                time=datetime(2026, 4, 7, 8, 15, tzinfo=timezone.utc),
            )
        ]
        tick = MagicMock()
        tick.bid = 3053.5
        tick.ask = 3053.7
        orch.mt5.get_tick = MagicMock(return_value=tick)

        orch._check_trade_and_capture()

        loaded = load_trade_record(path)
        execution = loaded["execution"]
        instrumentation = loaded["instrumentation"]
        assert loaded["exit"] is None
        assert execution["position_ticket"] == 222222
        assert execution["current_volume"] == 0.05
        assert execution["active_stop_loss"] == 3042.0
        assert execution["active_take_profit"] == 3065.0
        assert execution["residual_worst_case_cash_risk_amount"] == 0.0
        assert execution["partial_close_events"][0]["remaining_volume"] == 0.05
        assert instrumentation["gtos_vnext_recovered_partial_closed"] is True
        assert instrumentation["gtos_vnext_recovered_residual_open"] is True


class TestBlendedRPartialClose:
    """test_blended_r_partial_close — 50% at +1.5R, 50% at 0R → blended +0.75R."""

    def test_blended(self):
        orch = _make_orchestrator()
        ts = _make_trade_state(
            direction="LONG",
            entry_price=3042.0,
            sl_distance=7.0,
            initial_volume=0.10,
        )
        ts.partial_close_events = [
            {
                "type": "TP1_PARTIAL",
                "time": "2026-04-07T08:15:00+00:00",
                "price": 3052.5,  # +1.5R
                "volume_closed": 0.05,
            },
            {
                "type": "CLOSE_TIMEOUT_2H",
                "time": "2026-04-07T10:00:00+00:00",
            },
        ]

        record = _make_record_with_execution()
        orch._init_trade_tracking(ts)
        orch._active_trade_record = record
        orch._active_trade_record_path = "/tmp/fake"
        orch._last_tick_price = 3042.0  # Final close at breakeven (0R)

        with patch("src.components.orchestrator.save_trade_record"):
            orch._finalize_exit(ts, "timeout_2h")

        assert record["exit"] is not None
        # 50% at +1.5R + 50% at 0R = +0.75R
        assert record["exit"]["actual_r"] == pytest.approx(0.75, abs=0.01)


class TestExitClearsAllState:
    """test_exit_clears_all_state — after exit, all tracking attributes are None."""

    def test_cleared(self):
        orch = _make_orchestrator()
        ts = _make_trade_state()
        orch._init_trade_tracking(ts)
        record = _make_record_with_execution()
        orch._active_trade_record = record
        orch._active_trade_record_path = "/tmp/fake"
        orch._last_tick_price = 3053.5

        with patch("src.components.orchestrator.save_trade_record"):
            orch._finalize_exit(ts, "tp1_full_close")

        assert orch._active_trade_record is None
        assert orch._active_trade_record_path is None
        assert orch._trade_entry_price is None
        assert orch._trade_direction is None
        assert orch._trade_sl_distance is None
        assert orch._trade_entry_time is None
        assert orch._mfe_price is None
        assert orch._mae_price is None
        assert orch._last_tick_price is None


class TestExitFailureLoggedNotRaised:
    """test_exit_failure_logged_not_raised — save failure doesn't propagate."""

    def test_no_exception(self):
        orch = _make_orchestrator()
        ts = _make_trade_state()
        orch._init_trade_tracking(ts)
        orch._active_trade_record = _make_record_with_execution()
        orch._active_trade_record_path = "/tmp/fake"
        orch._last_tick_price = 3053.5

        with patch("src.components.orchestrator.save_trade_record", side_effect=IOError("disk full")):
            # Should not raise
            orch._finalize_exit(ts, "tp1_full_close")

        # State should still be cleared (finally block)
        assert orch._active_trade_record is None


class TestSLExitRIsNegative:
    """test_sl_exit_r_is_negative — full SL hit gives actual_r ≈ -1.0."""

    def test_sl_r(self):
        orch = _make_orchestrator()
        ts = _make_trade_state(
            direction="LONG",
            entry_price=3042.0,
            stop_loss=3035.0,
            sl_distance=7.0,
        )
        ts.partial_close_events = []

        record = _make_record_with_execution()
        orch._init_trade_tracking(ts)
        orch._active_trade_record = record
        orch._active_trade_record_path = "/tmp/fake"
        orch._last_tick_price = 3035.0  # SL price

        with patch("src.components.orchestrator.save_trade_record"):
            orch._finalize_exit(ts, "broker_closed")

        assert record["exit"]["actual_r"] == pytest.approx(-1.0, abs=0.01)
        assert record["exit"]["exit_type"] == "broker_closed"


class TestBrokerDealAccountingFields:
    """Broker-closed exits persist read-only MT5 deal accounting metadata."""

    def test_broker_closed_uses_deal_accounting_fields(self):
        orch = _make_orchestrator()
        orch._mt5_symbol = "XAUUSD"
        ts = _make_trade_state(
            direction="LONG",
            entry_price=3042.0,
            stop_loss=3035.0,
            sl_distance=7.0,
        )
        ts.partial_close_events = []
        close_time = datetime(2026, 4, 7, 8, 30, tzinfo=timezone.utc)
        orch.mt5.get_history_deals.return_value = [
            {
                "ticket": 9001,
                "order": 8001,
                "position_id": ts.ticket,
                "entry": 1,
                "time": close_time,
                "volume": 0.10,
                "price": 3053.5,
                "profit": 120.0,
                "commission": -0.7,
                "swap": -0.1,
                "reason": 4,
                "comment": "tp",
            }
        ]

        record = _make_record_with_execution()
        orch._init_trade_tracking(ts)
        orch._active_trade_record = record
        orch._active_trade_record_path = "/tmp/fake"

        with patch("src.components.orchestrator.save_trade_record"), \
             patch("src.components.orchestrator.record_close_slippage") as close_log:
            orch._finalize_exit(ts, "broker_closed")

        assert record["exit"]["broker_deal_reconciled"] is True
        assert record["exit"]["broker_close_deal_id"] == 9001
        assert record["exit"]["broker_close_order_id"] == 8001
        assert record["exit"]["commission"] == -0.7
        assert record["exit"]["swap"] == -0.1
        assert record["exit"]["broker_profit"] == 120.0
        close_log.assert_called_once()
        assert close_log.call_args.kwargs["mt5_deal_id"] == 9001
        assert close_log.call_args.kwargs["accounting_source"] == "MT5_HISTORY_DEALS_READONLY"
        assert close_log.call_args.kwargs["close_time"] == close_time.isoformat()

    def test_broker_closed_merges_recovered_partial_and_clears_residual(self):
        orch = _make_orchestrator()
        orch._mt5_symbol = "XAUUSD"
        ts = _make_trade_state(
            direction="LONG",
            entry_price=3042.0,
            stop_loss=3035.0,
            sl_distance=7.0,
            initial_volume=0.10,
            current_volume=0.05,
        )
        ts.partial_close_events = []
        close_time = datetime(2026, 4, 7, 9, 0, tzinfo=timezone.utc)
        orch.mt5.get_history_deals.return_value = [
            {
                "ticket": 9002,
                "order": 8002,
                "position_id": ts.ticket,
                "entry": 1,
                "time": close_time,
                "volume": 0.05,
                "price": 3042.0,
                "profit": 0.0,
                "commission": -0.7,
                "swap": 0.0,
                "reason": 4,
                "comment": "be",
            }
        ]

        partial_event = {
            "type": "TP1_PARTIAL_RECOVERED_FROM_SLIPPAGE_LOG",
            "time": "2026-04-07T08:15:00+00:00",
            "price": 3052.5,
            "volume_closed": 0.05,
            "remaining_volume": 0.05,
            "initial_volume": 0.10,
            "r_at_close": 1.5,
            "mt5_order_id": 8001,
            "mt5_deal_id": 9001,
            "commission": -0.7,
            "sl_at_breakeven": True,
        }
        record = _make_record_with_execution()
        record.setdefault("execution", {}).update({
            "current_volume": 0.05,
            "active_stop_loss": 3042.0,
            "active_take_profit": 3056.0,
            "partial_close_events": [dict(partial_event)],
        })
        record.setdefault("lifecycle", {}).update({
            "active_trade_management_events": [dict(partial_event)],
            "last_lifecycle_result": "current_partial_record_repaired_from_broker_probe",
            "residual_position_ticket": ts.ticket,
            "residual_volume": 0.05,
            "residual_broker_stop_loss": 3042.0,
            "residual_broker_take_profit": 3056.0,
            "residual_risk_released": True,
            "broker_position_ticket": ts.ticket,
            "broker_position_volume": 0.05,
            "broker_stop_loss": 3042.0,
            "broker_take_profit": 3056.0,
            "broker_comment": "TP1_vnext_partia",
            "open_worst_case_cash_risk_amount": 0.0,
            "open_worst_case_cash_risk_status": (
                "residual_risk_released_by_breakeven_or_better_sl"
            ),
        })
        record.setdefault("instrumentation", {}).update({
            "gtos_vnext_recovered_partial_closed": True,
            "gtos_vnext_recovered_residual_open": True,
            "gtos_vnext_recovered_partial_close_events": [dict(partial_event)],
        })

        orch._init_trade_tracking(ts)
        orch._active_trade_record = record
        orch._active_trade_record_path = "/tmp/fake"

        with patch("src.components.orchestrator.save_trade_record"), \
             patch("src.components.orchestrator.record_close_slippage"):
            orch._finalize_exit(ts, "broker_closed")

        assert record["exit"]["broker_deal_reconciled"] is True
        assert record["exit"]["actual_r"] == pytest.approx(0.75, abs=0.01)
        assert len(record["exit"]["partial_closes"]) == 1
        assert record["exit"]["partial_closes"][0]["mt5_deal_id"] == 9001
        assert record["execution"]["current_volume"] == 0.0
        assert record["execution"]["active_stop_loss"] is None
        assert record["execution"]["active_take_profit"] is None
        assert record["lifecycle"]["residual_volume"] == 0.0
        assert record["lifecycle"]["residual_broker_stop_loss"] is None
        assert record["lifecycle"]["residual_broker_take_profit"] is None
        assert record["lifecycle"]["broker_position_volume"] == 0.0
        assert record["lifecycle"]["broker_stop_loss"] is None
        assert record["lifecycle"]["broker_take_profit"] is None
        assert record["lifecycle"]["broker_comment"] is None
        assert record["lifecycle"]["open_worst_case_cash_risk_amount"] == 0.0
        assert (
            record["lifecycle"]["open_worst_case_cash_risk_status"]
            == "released_by_terminal_exit"
        )
        assert (
            record["lifecycle"]["previous_residual_open_state_before_terminal_exit"]
            ["residual_volume"]
            == 0.05
        )
        assert (
            record["lifecycle"]["previous_residual_open_state_before_terminal_exit"]
            ["broker_position_volume"]
            == 0.05
        )
        assert record["instrumentation"]["gtos_vnext_recovered_residual_open"] is False
        assert record["instrumentation"]["gtos_vnext_recovered_partial_closed"] is True


class TestHoldTimeCalculation:
    """test_hold_time_calculation — entry 07:45, exit 08:30 = 45 min."""

    def test_hold_time(self):
        orch = _make_orchestrator()
        ts = _make_trade_state(entry_time="2026-04-07T07:45:00+00:00")
        ts.partial_close_events = []

        record = _make_record_with_execution()
        orch._init_trade_tracking(ts)
        orch._active_trade_record = record
        orch._active_trade_record_path = "/tmp/fake"
        orch._last_tick_price = 3053.5

        # Mock datetime.now to return 08:30
        exit_time = datetime(2026, 4, 7, 8, 30, 0, tzinfo=timezone.utc)
        with patch("src.components.orchestrator.save_trade_record"), \
             patch("src.components.orchestrator.datetime") as mock_dt:
            mock_dt.now.return_value = exit_time
            mock_dt.fromisoformat = datetime.fromisoformat
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            orch._finalize_exit(ts, "tp1_full_close")

        assert record["exit"]["hold_time_minutes"] == 45
