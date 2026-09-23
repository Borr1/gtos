"""Tests for Execution Engine (Phase 3)."""

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.components import execution as _exec_mod
from src.components.execution import ExecutionEngine, TradeState
from src.components.poi_execution_lifecycle import (
    build_causal_poi_lifecycle_envelope,
)
from src.components.poi_state_contract import finalize_poi_state, stable_poi_id
from src.mt5.mt5_mock import MockMT5
from src.mt5.mt5_interface import (
    MAGIC_NUMBER,
    OrderResult,
    PositionInfo,
    TRADE_ACTION_SLTP,
)


@pytest.fixture
def mt5():
    m = MockMT5(balance=100000.0)
    m.connect()
    return m


@pytest.fixture
def engine(mt5):
    config = {"risk": {"risk_per_trade_pct": 1.0}}
    return ExecutionEngine(mt5, config)


# Isolate checkpoint writes to a tmp dir so tests never touch production
# state under knowledge_base/meta/execution_checkpoint.json.
@pytest.fixture(autouse=True)
def _isolate_checkpoint(tmp_path, monkeypatch):
    checkpoint_file = tmp_path / "execution_checkpoint.json"
    monkeypatch.setattr(_exec_mod, "CHECKPOINT_PATH", str(checkpoint_file))
    try:
        from src.components.ultimate_book.minimal_size import f5_close_send_none_reset
        f5_close_send_none_reset()
    except Exception:
        pass
    yield


def _trade_params(direction="LONG", entry=2650.0, sl=2640.0,
                  tp1=2670.0, tp2=2680.0, tp3=2690.0, rr=3.0):
    return {
        "direction": direction, "entry_price": entry, "stop_loss": sl,
        "take_profit_1": tp1, "take_profit_2": tp2, "take_profit_3": tp3,
        "risk_reward_ratio": rr,
    }


def _poi_lifecycle_fixture(*, fill_probability: float = 0.80):
    decision_time = "2026-05-14T01:15:00+00:00"
    source_time = "2026-05-14T01:00:00+00:00"
    source_candles = [
        "2026-05-14T00:15:00+00:00",
        "2026-05-14T00:30:00+00:00",
        "2026-05-14T00:45:00+00:00",
    ]
    poi_id = stable_poi_id(
        symbol="XAUUSD",
        timeframe="M15",
        poi_type="fair_value_gap",
        direction="bullish",
        source_candle_times=source_candles,
        zone_low=2644.0,
        zone_high=2646.0,
    )
    poi_state = finalize_poi_state(
        {
            "poi_id": poi_id,
            "poi_type": "fair_value_gap",
            "poi_timeframe": "M15",
            "poi_direction": "bullish",
            "poi_zone_low": 2644.0,
            "poi_zone_high": 2646.0,
            "poi_source_candle_times": source_candles,
            "poi_created_at_utc": source_time,
            "poi_state_asof_utc": source_time,
            "poi_age_hours": 0.0,
            "poi_touch_count": 0,
            "poi_mitigation_status": "untouched",
            "poi_filled": False,
            "poi_invalidated": False,
        }
    )
    lifecycle = build_causal_poi_lifecycle_envelope(
        poi_state=poi_state,
        decision_time_utc=decision_time,
        fillability={
            "fill_probability": fill_probability,
            "current_price_source_time_utc": source_time,
            "source_boundary": "closed_m15_predecision_asof_no_postdecision_path",
        },
        distance_to_zone_price=0.0 if fill_probability >= 0.45 else 10.0,
        distance_to_zone_atr=0.0 if fill_probability >= 0.45 else 10.0,
        distance_to_midpoint_price=0.0 if fill_probability >= 0.45 else 10.0,
        distance_to_midpoint_atr=0.0 if fill_probability >= 0.45 else 10.0,
        scheduler_readiness_floor=0.45,
        scheduler_readiness_policy_source="test_floor",
        scheduler_readiness_policy_hash_sha256="a" * 64,
    )
    return decision_time, poi_state, lifecycle


def test_limit_intent_persists_candidate_and_causal_poi_identity_across_restart(
    mt5,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(_exec_mod, "PENDING_INTENT_DIR", str(tmp_path))
    config = {"risk": {"risk_per_trade_pct": 1.0}}
    engine = ExecutionEngine(mt5, config)
    monkeypatch.setattr(engine, "_enforce_runtime_halt_clear", lambda *args, **kwargs: None)
    decision_time, poi_state, lifecycle = _poi_lifecycle_fixture()
    params = _trade_params(entry=2645.0, sl=2638.0, tp1=2660.0)
    params.update(
        {
            "candidate_id": "candidate-poi-pending",
            "decision_time_utc": decision_time,
            "canonical_replay_candidate_instance_key": (
                f"candidate-poi-pending@@{decision_time}"
            ),
            "source_bound_replay_candidate_instance_key": (
                f"candidate-poi-pending@@{decision_time}"
            ),
            "candidate_instance_identity_status": "materialized",
            "poi_id": poi_state["poi_id"],
            "poi_state_hash_sha256": poi_state["poi_state_hash_sha256"],
            "poi_state": poi_state,
            "causal_poi_lifecycle_required": True,
            "causal_poi_lifecycle": lifecycle,
            "causal_poi_lifecycle_hash_sha256": lifecycle[
                "lifecycle_hash_sha256"
            ],
        }
    )

    intent = engine.set_limit_intent(params, account_balance=100000.0)

    assert intent is not None
    assert intent.candidate_id == "candidate-poi-pending"
    assert intent.decision_time_utc == decision_time
    assert intent.poi_id == poi_state["poi_id"]
    assert intent.causal_poi_lifecycle_hash_sha256 == lifecycle[
        "lifecycle_hash_sha256"
    ]
    reloaded = ExecutionEngine(mt5, config).pending_intent
    assert reloaded is not None
    assert reloaded.canonical_replay_candidate_instance_key == (
        f"candidate-poi-pending@@{decision_time}"
    )
    assert reloaded.causal_poi_lifecycle == lifecycle


def test_limit_intent_rejects_valid_but_dormant_poi_lifecycle(
    mt5,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(_exec_mod, "PENDING_INTENT_DIR", str(tmp_path))
    engine = ExecutionEngine(mt5, {"risk": {"risk_per_trade_pct": 1.0}})
    monkeypatch.setattr(engine, "_enforce_runtime_halt_clear", lambda *args, **kwargs: None)
    decision_time, poi_state, lifecycle = _poi_lifecycle_fixture(
        fill_probability=0.10
    )
    params = _trade_params(entry=2645.0, sl=2638.0, tp1=2660.0)
    params.update(
        {
            "candidate_id": "candidate-dormant-poi",
            "decision_time_utc": decision_time,
            "poi_state": poi_state,
            "causal_poi_lifecycle_required": True,
            "causal_poi_lifecycle": lifecycle,
            "causal_poi_lifecycle_hash_sha256": lifecycle[
                "lifecycle_hash_sha256"
            ],
        }
    )

    assert engine.set_limit_intent(params, account_balance=100000.0) is None
    assert engine.pending_intent is None


def test_trading_m15_bars_since_skips_closed_market(engine):
    """timestop-wallclock-vs-trading-bars: the time-stop counts actual PRINTED M15 bars since entry
    (trading bars), NOT wall-clock -- so a weekend gap is skipped (wall-clock would be ~288 bars; the
    real printed count is 16). Fall back to None (-> wall-clock) when the feed is empty."""
    entry = datetime(2026, 6, 12, 20, 0, tzinfo=timezone.utc)   # Friday 20:00 UTC
    from datetime import timedelta
    bars = []
    for k in range(4):                                          # 4 bars BEFORE entry (not counted)
        bars.append({"time": (entry - timedelta(minutes=15 * (4 - k))).isoformat()})
    for k in range(1, 11):                                      # 10 Friday-evening bars AFTER entry
        bars.append({"time": (entry + timedelta(minutes=15 * k)).isoformat()})
    mon = entry + timedelta(days=3)                             # weekend GAP, then Monday
    for k in range(6):                                          # 6 Monday bars (last is forming)
        bars.append({"time": (mon + timedelta(minutes=15 * k)).isoformat()})
    engine.mt5.get_candles = lambda sym, tf, n: bars
    # closed bars after entry = 10 Friday + (6 Monday - 1 forming) = 15
    assert engine._trading_m15_bars_since(entry, budget=48) == 15
    engine.mt5.get_candles = lambda sym, tf, n: []              # feed empty -> fall back to wall-clock
    assert engine._trading_m15_bars_since(entry, 48) is None


def test_normalize_volume_rejects_sub_min_lot(engine):
    """COMP-6: a unit sized below the broker volume_min returns None (rejected, not floored) -- open_trade
    then stamps the distinct terminal 'below_min_lot' reason so the book sheds the breadth unit ONCE per
    bar instead of retrying it as a transient failure. At/above min -> step-aligned down to a valid lot."""
    sym = SimpleNamespace(volume_min=1.0, volume_step=0.1, volume_max=100.0)
    assert engine._normalize_volume(0.4, sym, require_broker_geometry=True) is None     # sub-min -> rejected
    assert engine._normalize_volume(2.45, sym, require_broker_geometry=True) == pytest.approx(2.4)
    assert engine._normalize_volume(1.0, sym, require_broker_geometry=True) == pytest.approx(1.0)


def test_open_trade_rejects_wrong_side_sl_after_price_move(engine, mt5):
    """sl-no-floor-or-side-validation-vs-fresh-tick: if price moved between the decision tick and the
    fresh fill tick so the SL is now on the WRONG side (LONG with sl >= entry), open_trade rejects with a
    clear reason instead of arming a wrong-side stop / chasing."""
    mt5.set_tick(2629.0, 2630.0)                       # fresh ask 2630 is BELOW the LONG sl 2640
    tp = _trade_params(direction="LONG", entry=2650.0, sl=2640.0)
    assert engine.open_trade(tp, 100000.0) is None
    assert engine._last_open_trade_block_reason == "sl_wrong_side_vs_fresh_tick"
    # SHORT mirror: fresh bid below the SL is fine; fresh bid ABOVE the short sl is the wrong side
    mt5.set_tick(2660.0, 2661.0)                       # fresh bid 2660 is ABOVE the SHORT sl 2655
    tp2 = _trade_params(direction="SHORT", entry=2650.0, sl=2655.0)
    assert engine.open_trade(tp2, 100000.0) is None
    assert engine._last_open_trade_block_reason == "sl_wrong_side_vs_fresh_tick"


def test_open_trade_records_same_symbol_lifecycle_store(mt5, tmp_path):
    store_path = tmp_path / "same_symbol_lifecycle_store.json"
    engine = ExecutionEngine(
        mt5,
        {
            "risk": {
                "risk_per_trade_pct": 1.0,
                "same_symbol_lifecycle_v4": {
                    "lifecycle_store_path": str(store_path),
                },
            },
        },
    )
    mt5.set_tick(bid=2650.0, ask=2650.1)
    params = _trade_params()
    params.update(
        {
            "candidate_id": "entry-candidate-xau",
            "gtos_vnext_thesis_id": "thesis-xau-london-continuation",
            "risk_pct": 0.25,
            "gtos_vnext_probability": 0.58,
            "gtos_vnext_expected_value_r": 0.20,
            "gtos_vnext_execution_policy_id": "unit-momentum-policy",
            "gtos_vnext_dynamic_policy_selected": "momentum_exhaustion",
        }
    )

    state = engine.open_trade(params, account_balance=100000.0)

    assert state is not None
    payload = json.loads(store_path.read_text())
    row = payload["tickets"][str(state.ticket)]
    assert row["thesis_id"] == "thesis-xau-london-continuation"
    assert row["risk_pct"] == 0.25
    assert row["probability_at_entry"] == 0.58
    assert row["ev_r_at_entry"] == 0.20
    assert row["source_status"] == "durable_same_symbol_lifecycle_store_v4"
    assert len(row["record_hash_sha256"]) == 64


def test_partial_be_runner_does_not_duplicate_partial_when_broker_residual_exists(
    mt5,
    engine,
):
    trade = TradeState(
        ticket=700100,
        direction="LONG",
        entry_price=100.0,
        stop_loss=100.0,
        take_profit_1=101.0,
        take_profit_2=103.0,
        take_profit_3=0.0,
        initial_volume=0.20,
        current_volume=0.20,
        sl_distance=1.0,
        trade_id="residual_guard",
        gtos_vnext_dynamic_policy_selected="partial_be_runner",
        gtos_vnext_dynamic_policy_applied=True,
        gtos_vnext_execution_policy_id="vnext_exec_partial_50_at_1r_be_runner_to_3r",
        gtos_vnext_dynamic_be_trigger_r=1.0,
        gtos_vnext_dynamic_final_target_r=3.0,
        gtos_vnext_dynamic_final_target_price=103.0,
        sl_at_breakeven=True,
        position_confirmed=True,
    )
    engine.active_trade = trade
    mt5.set_positions([
        PositionInfo(
            ticket=trade.ticket,
            symbol="XAUUSD",
            type=0,
            volume=0.10,
            price_open=trade.entry_price,
            sl=trade.entry_price,
            tp=trade.take_profit_2,
            profit=0.0,
            magic=MAGIC_NUMBER,
            comment="TP1_vnext_partia",
            time=datetime.now(timezone.utc),
        )
    ])
    mt5.set_tick(bid=101.25, ask=101.30)

    status = engine.check_and_manage_trade({})

    assert status == "tp1_partial_already_reflected_vnext_partial_be_runner"
    assert engine.active_trade is trade
    assert trade.tp1_hit is True
    assert trade.current_volume == pytest.approx(0.10)
    assert not [request for request in mt5._order_log if request.get("action") == 1]
    assert any(
        event.get("type") == "TP1_PARTIAL_ALREADY_REFLECTED_BY_BROKER"
        for event in trade.partial_close_events
    )


def test_sltp_no_changes_retcode_is_benign_when_sl_already_matches(mt5, engine):
    trade = TradeState(
        ticket=700101,
        direction="LONG",
        entry_price=100.0,
        stop_loss=100.0,
        take_profit_1=101.0,
        take_profit_2=103.0,
        take_profit_3=0.0,
        initial_volume=0.10,
        current_volume=0.10,
        sl_distance=1.0,
    )
    mt5.set_positions([
        PositionInfo(
            ticket=trade.ticket,
            symbol="XAUUSD",
            type=0,
            volume=trade.current_volume,
            price_open=trade.entry_price,
            sl=trade.entry_price,
            tp=trade.take_profit_2,
            profit=0.0,
            magic=MAGIC_NUMBER,
            comment="already_be",
            time=datetime.now(timezone.utc),
        )
    ])
    mt5.order_send = lambda request: OrderResult(
        retcode=10025,
        order=request["position"],
        volume=0.0,
        price=0.0,
        comment="No changes",
    )

    assert engine._modify_sl(
        trade.ticket,
        trade.entry_price,
        trade=trade,
        modify_reason="unit_no_changes",
    )
    assert trade.partial_close_events[-1]["benign_retcode_status"] == (
        "no_changes_already_matched"
    )
    assert engine._modify_tp(
        trade.ticket,
        trade.take_profit_2,
        trade=trade,
        modify_reason="unit_no_changes_tp",
    )
    assert trade.partial_close_events[-1]["modify_kind"] == "TP"
    assert trade.partial_close_events[-1]["benign_retcode_status"] == (
        "no_changes_already_matched"
    )


def _exit_policy_v4_engine(mt5, **overrides):
    runtime = {
        "moonshot_exit_policy_v4_enabled": True,
        "moonshot_exit_policy_v4_apply_to_execution": True,
        "moonshot_exit_policy_v4_partial_trigger_r": 1.0,
        "moonshot_exit_policy_v4_partial_close_ratio": 0.5,
        "moonshot_exit_policy_v4_be_trigger_r": 1.0,
        "moonshot_exit_policy_v4_trailing_trigger_r": 1.0,
        "moonshot_exit_policy_v4_trailing_gap_r": 0.5,
        "moonshot_exit_policy_v4_stale_thesis_bars": 12,
        "moonshot_exit_policy_v4_stale_min_mfe_r": 0.35,
        "moonshot_exit_policy_v4_stale_adverse_r": -0.25,
        "moonshot_exit_policy_v4_time_stop_bars": 32,
        "moonshot_dynamic_execution_router_partial_close_ratio": 0.5,
        "moonshot_dynamic_execution_router_partial_final_target_r": 3.0,
    }
    runtime.update(overrides)
    return ExecutionEngine(
        mt5,
        {"risk": {"risk_per_trade_pct": 1.0}, "gtos_vnext_runtime": runtime},
    )


def _v4_trade(policy="momentum_exhaustion", **overrides):
    data = {
        "ticket": 710001,
        "direction": "LONG",
        "entry_price": 100.0,
        "stop_loss": 99.0,
        "take_profit_1": 101.0,
        "take_profit_2": 103.0,
        "take_profit_3": 0.0,
        "initial_volume": 0.20,
        "current_volume": 0.20,
        "sl_distance": 1.0,
        "trade_id": "exit_policy_v4_unit",
        "entry_time": "2026-06-02T10:00:00+00:00",
        "gtos_vnext_dynamic_policy_selected": policy,
        "gtos_vnext_dynamic_policy_applied": True,
        "gtos_vnext_execution_policy_id": f"unit_{policy}",
        "gtos_vnext_dynamic_be_trigger_r": 1.0,
        "gtos_vnext_dynamic_final_target_r": 3.0,
        "gtos_vnext_dynamic_trail_gap_r": 0.5,
        "position_confirmed": True,
    }
    data.update(overrides)
    return TradeState(**data)


class TestExitPolicyV4Runtime:
    def test_input_uses_broker_visible_stop_before_local_trade_stop(self, mt5):
        engine = _exit_policy_v4_engine(mt5)
        trade = _v4_trade(policy="trailing_runner", stop_loss=99.0)
        position = PositionInfo(
            ticket=trade.ticket,
            symbol="XAUUSD",
            type=0,
            volume=trade.current_volume,
            price_open=trade.entry_price,
            sl=101.0,
            tp=trade.take_profit_2,
            profit=30.0,
            magic=MAGIC_NUMBER,
            comment="v4",
            time=datetime.now(timezone.utc),
        )

        policy_input = engine._exit_policy_v4_input(
            trade,
            current_price=101.4,
            current_candle={"time_utc": "2026-06-02T10:45:00+00:00"},
            position=position,
        )

        assert policy_input.current_stop_r == pytest.approx(1.0)

    def test_source_gap_holds_and_records_no_broker_action(self, mt5):
        engine = _exit_policy_v4_engine(mt5)
        trade = _v4_trade(entry_time="")
        engine.active_trade = trade
        mt5.set_positions([
            PositionInfo(
                ticket=trade.ticket,
                symbol="XAUUSD",
                type=0,
                volume=trade.current_volume,
                price_open=trade.entry_price,
                sl=trade.stop_loss,
                tp=trade.take_profit_2,
                profit=0.0,
                magic=MAGIC_NUMBER,
                comment="v4",
                time=datetime.now(timezone.utc),
            )
        ])
        mt5.set_tick(bid=100.2, ask=100.3)

        status = engine.check_and_manage_trade({})

        assert status == "monitoring"
        assert engine.active_trade is trade
        assert mt5._order_log == []
        assert any(
            event.get("type") == "EXIT_POLICY_V4_DECISION"
            and event.get("status") == "source_gap_fail_closed"
            for event in trade.partial_close_events
        )

    def test_stale_thesis_closes_ticket_bound_position(self, mt5):
        engine = _exit_policy_v4_engine(mt5)
        trade = _v4_trade(policy="momentum_exhaustion")
        engine.active_trade = trade
        mt5.set_positions([
            PositionInfo(
                ticket=trade.ticket,
                symbol="XAUUSD",
                type=0,
                volume=trade.current_volume,
                price_open=trade.entry_price,
                sl=trade.stop_loss,
                tp=trade.take_profit_2,
                profit=-10.0,
                magic=MAGIC_NUMBER,
                comment="v4",
                time=datetime.now(timezone.utc),
            )
        ])
        mt5.set_tick(bid=99.6, ask=99.7)

        status = engine.check_and_manage_trade(
            {"time_utc": "2026-06-02T13:00:00+00:00"}
        )

        assert status == "v4_stale_thesis_no_progress"
        assert engine.active_trade is None
        assert mt5.get_positions("XAUUSD") == []
        assert any(
            event.get("action") == "CLOSE_STALE_THESIS"
            for event in trade.partial_close_events
        )

    def test_opportunity_cost_close_uses_source_bound_scheduler_context(self, mt5):
        engine = _exit_policy_v4_engine(mt5)
        trade = _v4_trade(policy="momentum_exhaustion")
        engine.active_trade = trade
        mt5.set_positions([
            PositionInfo(
                ticket=trade.ticket,
                symbol="XAUUSD",
                type=0,
                volume=trade.current_volume,
                price_open=trade.entry_price,
                sl=trade.stop_loss,
                tp=trade.take_profit_2,
                profit=5.0,
                magic=MAGIC_NUMBER,
                comment="v4",
                time=datetime.now(timezone.utc),
            )
        ])
        mt5.set_tick(bid=100.1, ask=100.2)

        status = engine.check_and_manage_trade(
            {
                "time_utc": "2026-06-02T12:00:00+00:00",
                "opportunity_cost_r": 1.4,
                "competing_candidate_ev_r": 0.9,
                "opportunity_cost_source_status": "opportunity_cost_replay_bound",
            }
        )

        assert status == "v4_stale_thesis_opportunity_cost_close"
        assert engine.active_trade is None
        assert mt5.get_positions("XAUUSD") == []
        assert any(
            event.get("action") == "CLOSE_STALE_THESIS"
            and event.get("reason")
            == "opportunity_cost_or_scheduler_regret_dominates_stale_hold"
            for event in trade.partial_close_events
        )

    def test_opportunity_cost_close_fails_closed_without_source_status(self, mt5):
        engine = _exit_policy_v4_engine(mt5)
        trade = _v4_trade(policy="momentum_exhaustion")
        engine.active_trade = trade
        mt5.set_positions([
            PositionInfo(
                ticket=trade.ticket,
                symbol="XAUUSD",
                type=0,
                volume=trade.current_volume,
                price_open=trade.entry_price,
                sl=trade.stop_loss,
                tp=trade.take_profit_2,
                profit=5.0,
                magic=MAGIC_NUMBER,
                comment="v4",
                time=datetime.now(timezone.utc),
            )
        ])
        mt5.set_tick(bid=100.1, ask=100.2)

        status = engine.check_and_manage_trade(
            {
                "time_utc": "2026-06-02T12:00:00+00:00",
                "opportunity_cost_r": 1.4,
            }
        )

        assert status == "monitoring"
        assert engine.active_trade is trade
        assert mt5.get_positions("XAUUSD") != []
        assert any(
            event.get("status") == "source_gap_fail_closed"
            and "opportunity_cost_source_missing" in event.get("source_gaps", [])
            for event in trade.partial_close_events
        )

    def test_partial_be_runner_uses_v4_partial_action_without_duplicate(self, mt5):
        engine = _exit_policy_v4_engine(mt5)
        trade = _v4_trade(policy="partial_be_runner")
        engine.active_trade = trade
        mt5.set_positions([
            PositionInfo(
                ticket=trade.ticket,
                symbol="XAUUSD",
                type=0,
                volume=trade.current_volume,
                price_open=trade.entry_price,
                sl=trade.stop_loss,
                tp=trade.take_profit_2,
                profit=20.0,
                magic=MAGIC_NUMBER,
                comment="v4",
                time=datetime.now(timezone.utc),
            )
        ])
        mt5.set_tick(bid=101.05, ask=101.15)

        status = engine.check_and_manage_trade(
            {"time_utc": "2026-06-02T10:30:00+00:00"}
        )

        assert status == "tp1_partial_vnext_partial_be_runner"
        assert engine.active_trade is trade
        assert trade.tp1_hit is True
        assert trade.current_volume == pytest.approx(0.10)
        assert any(
            event.get("action") == "PARTIAL_CLOSE_TO_BE"
            for event in trade.partial_close_events
        )
        assert any(
            event.get("type") == "TP1_PARTIAL_VNEXT_PARTIAL_BE_RUNNER"
            for event in trade.partial_close_events
        )

    def test_trailing_runner_raises_stop_from_v4_decision(self, mt5):
        engine = _exit_policy_v4_engine(mt5)
        trade = _v4_trade(
            policy="trailing_runner",
            stop_loss=100.0,
            sl_at_breakeven=True,
            tp1_hit=True,
            gtos_vnext_dynamic_trail_stop_r=0.0,
        )
        engine.active_trade = trade
        mt5.set_positions([
            PositionInfo(
                ticket=trade.ticket,
                symbol="XAUUSD",
                type=0,
                volume=trade.current_volume,
                price_open=trade.entry_price,
                sl=trade.stop_loss,
                tp=trade.take_profit_2,
                profit=30.0,
                magic=MAGIC_NUMBER,
                comment="v4",
                time=datetime.now(timezone.utc),
            )
        ])
        mt5.set_tick(bid=101.4, ask=101.5)

        status = engine.check_and_manage_trade(
            {"time_utc": "2026-06-02T10:45:00+00:00"}
        )

        assert status == "exit_policy_v4_raised_trailing_stop"
        assert trade.stop_loss == pytest.approx(100.9)
        assert any(
            event.get("action") == "RAISE_TRAILING_STOP"
            for event in trade.partial_close_events
        )

    def test_abort_tighten_preserves_negative_target_r(self, mt5):
        engine = _exit_policy_v4_engine(
            mt5,
            moonshot_exit_policy_v4_abort_adverse_r=0.4,
            moonshot_exit_policy_v4_abort_adverse_max_mfe_r=0.25,
            moonshot_exit_policy_v4_abort_stop_r=-0.5,
        )
        trade = _v4_trade(policy="time_stop")
        engine.active_trade = trade
        mt5.set_positions([
            PositionInfo(
                ticket=trade.ticket,
                symbol="XAUUSD",
                type=0,
                volume=trade.current_volume,
                price_open=trade.entry_price,
                sl=trade.stop_loss,
                tp=trade.take_profit_2,
                profit=-10.0,
                magic=MAGIC_NUMBER,
                comment="v4",
                time=datetime.now(timezone.utc),
            )
        ])
        mt5.set_tick(bid=99.55, ask=99.65)

        status = engine.check_and_manage_trade(
            {"time_utc": "2026-06-02T10:45:00+00:00"}
        )

        assert status == "exit_policy_v4_abort_tightened_stop"
        assert trade.stop_loss == pytest.approx(99.5)
        assert trade.gtos_vnext_dynamic_trail_stop_r == pytest.approx(-0.5)
        assert trade.sl_at_breakeven is False
        assert mt5.get_positions("XAUUSD")[0].sl == pytest.approx(99.5)
        assert any(
            request.get("action") == TRADE_ACTION_SLTP
            and request.get("sl") == pytest.approx(99.5)
            for request in mt5._order_log
        )
        assert any(
            event.get("type") == "VNEXT_DYNAMIC_SL_MODIFY_SUCCESS"
            and event.get("target_r") == pytest.approx(-0.5)
            for event in trade.partial_close_events
        )


class TestPendingIntentStaleness:
    def _engine_config(self):
        return {
            "risk": {"risk_per_trade_pct": 1.0},
            "market": {
                "symbol": "XAUUSD",
                "kill_zones": {
                    "london": {"start_utc": "07:00", "end_utc": "10:30"},
                    "ny": {"start_utc": "13:00", "end_utc": "17:00"},
                },
            },
        }

    def _persist_intent(self, tmp_path, monkeypatch, placed_time: str) -> Path:
        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()
        monkeypatch.setattr(_exec_mod, "PENDING_INTENT_DIR", str(meta_dir))
        intent = _exec_mod.PendingLimitIntent(
            direction="LONG",
            limit_price=2645.0,
            stop_loss=2638.0,
            take_profit_1=2660.0,
            risk_pct=1.0,
            trade_id="pending-unit61",
            placed_time=placed_time,
            account_balance=100000.0,
        )
        path = meta_dir / "pending_intent_XAUUSD.pkl"
        with path.open("wb") as f:
            pickle.dump(intent, f, protocol=pickle.HIGHEST_PROTOCOL)
        return path

    def _freeze_execution_now(self, monkeypatch, fixed_now: datetime) -> None:
        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                if tz is None:
                    return fixed_now.replace(tzinfo=None)
                return fixed_now.astimezone(tz)

        monkeypatch.setattr(_exec_mod, "datetime", FixedDateTime)

    def test_same_utc_day_pending_intent_before_first_kz_survives_restart(
        self, mt5, tmp_path, monkeypatch
    ):
        """Unit61: same-day pending limits are not stale just because KZ has not started."""
        self._freeze_execution_now(
            monkeypatch,
            datetime(2026, 4, 20, 8, 0, tzinfo=timezone.utc),
        )
        path = self._persist_intent(
            tmp_path,
            monkeypatch,
            "2026-04-20T04:00:00+00:00",
        )

        engine = ExecutionEngine(mt5, self._engine_config())

        assert engine.pending_intent is not None
        assert engine.pending_intent.trade_id == "pending-unit61"
        assert path.exists()

    def test_previous_utc_day_pending_intent_before_first_kz_is_discarded(
        self, mt5, tmp_path, monkeypatch
    ):
        """Unit61: previous-day pending limits are cleared even when under 24 hours old."""
        self._freeze_execution_now(
            monkeypatch,
            datetime(2026, 4, 20, 8, 0, tzinfo=timezone.utc),
        )
        path = self._persist_intent(
            tmp_path,
            monkeypatch,
            "2026-04-19T23:30:00+00:00",
        )

        engine = ExecutionEngine(mt5, self._engine_config())

        assert engine.pending_intent is None
        assert not path.exists()


class TestOpenTrade:
    def test_opens_trade_successfully(self, mt5, engine):
        state = engine.open_trade(_trade_params(), 100000.0)
        assert state is not None
        assert state.direction == "LONG"
        assert state.initial_volume > 0
        assert len(mt5.get_positions()) == 1


    def test_position_sizing(self, mt5, engine):
        # Balance=100000, risk=1%, SL=$10 → risk=$1000 → lots = 1000/(10*100) = 1.00
        state = engine.open_trade(_trade_params(sl=2640.0), 100000.0)
        assert state is not None
        # Entry is tick.ask=2650.18, SL=2640.00, dist=10.18, lots=1000/(10.18*100)=0.98
        assert state.initial_volume == 0.98

    def test_no_tick_returns_none(self, engine):
        engine.mt5._tick = None
        result = engine.open_trade(_trade_params(), 100000.0)
        assert result is None


class TestPartialCloseResidualResolution:
    def test_same_ticket_stale_full_volume_is_retried_before_residual_accept(
        self,
        mt5,
        engine,
        monkeypatch,
    ):
        trade = TradeState(
            ticket=700100,
            direction="LONG",
            entry_price=100.0,
            stop_loss=99.0,
            take_profit_1=101.0,
            take_profit_2=103.0,
            take_profit_3=0.0,
            initial_volume=10.48,
            current_volume=10.48,
            sl_distance=1.0,
            trade_id="partial-stale-volume",
        )
        stale_same_ticket = PositionInfo(
            ticket=700100,
            symbol="XAUUSD",
            type=0,
            volume=10.48,
            price_open=100.0,
            sl=99.0,
            tp=101.0,
            profit=0.0,
            magic=MAGIC_NUMBER,
            comment="vnext",
            time=datetime.now(timezone.utc),
        )
        refreshed_residual = PositionInfo(
            ticket=700100,
            symbol="XAUUSD",
            type=0,
            volume=5.24,
            price_open=100.0,
            sl=100.0,
            tp=103.0,
            profit=0.0,
            magic=MAGIC_NUMBER,
            comment="TP1_vnext_partia",
            time=datetime.now(timezone.utc),
        )
        monkeypatch.setattr(_exec_mod.time, "sleep", lambda *_args, **_kwargs: None)
        monkeypatch.setattr(mt5, "get_positions", lambda _symbol: [refreshed_residual])

        residual = engine._find_residual_position_after_partial(
            trade,
            [stale_same_ticket],
            closed_ticket=700100,
            closed_volume=5.24,
            previous_volume=10.48,
            close_result=OrderResult(
                retcode=10009,
                order=800100,
                volume=5.24,
                price=101.0,
                comment="partial",
            ),
            close_reason="tp1_partial_vnext_partial_be_runner",
        )

        assert residual is refreshed_residual
        assert residual.volume == pytest.approx(5.24)
        assert not [
            event for event in trade.partial_close_events
            if event.get("type") == "PARTIAL_CLOSE_RESIDUAL_TICKET_UNRESOLVED"
        ]


class TestSafePlaceOrder:
    def test_writes_and_clears_checkpoint(self, mt5, engine):
        checkpoint_path = Path(_exec_mod.CHECKPOINT_PATH)

        # During execution the checkpoint exists briefly; after it should be gone
        request = {
            "action": 1, "symbol": "XAUUSD", "volume": 0.10,
            "type": 0, "magic": MAGIC_NUMBER,
        }
        result = engine.safe_place_order(request)
        assert result is not None
        assert result.success
        assert not checkpoint_path.exists()

    def test_returns_result_on_success(self, mt5, engine):
        request = {"action": 1, "volume": 0.10, "magic": MAGIC_NUMBER}
        result = engine.safe_place_order(request)
        assert result.success


class TestPartialClose:
    def test_tp1_full_close_100pct(self, mt5, engine):
        """Default config: tp1_close_pct=100, so TP1 hit closes entire position."""
        state = engine.open_trade(_trade_params(), 100000.0)
        assert state is not None

        # Simulate price hitting TP1
        mt5.set_tick(2670.00, 2670.18)
        action = engine.check_and_manage_trade({})
        assert action == "tp1_full_close"
        assert engine.active_trade is None  # Position fully closed

    def test_tp1_partial_close_legacy(self, mt5):
        """Legacy path: tp1_close_pct=50 does partial close, moves SL to BE."""
        config = {"risk": {"risk_per_trade_pct": 1.0, "tp1_close_pct": 50}}
        engine = ExecutionEngine(mt5, config)
        state = engine.open_trade(_trade_params(), 100000.0)
        assert state is not None
        initial_vol = state.initial_volume
        old_ticket = state.ticket

        # Simulate price hitting TP1
        mt5.set_tick(2670.00, 2670.18)
        action = engine.check_and_manage_trade({})
        assert action == "tp1_partial"
        assert engine.active_trade.tp1_hit
        assert engine.active_trade.ticket != old_ticket
        assert engine.active_trade.current_volume < initial_vol
        assert engine.active_trade.sl_at_breakeven

    def test_vnext_partial_close_binds_residual_ticket_with_same_symbol_hedge(self, mt5):
        """Partial-close management must not bind to the first same-symbol ticket."""
        config = {
            "risk": {"risk_per_trade_pct": 1.0, "tp1_close_pct": 50},
            "gtos_vnext_runtime": {
                "moonshot_dynamic_execution_router_partial_close_ratio": 0.5,
                "moonshot_dynamic_execution_router_partial_final_target_r": 3.0,
            },
        }
        engine = ExecutionEngine(mt5, config)
        state = engine.open_trade(_trade_params(), 100000.0)
        assert state is not None
        state.gtos_vnext_dynamic_policy_applied = True
        state.gtos_vnext_dynamic_policy_selected = "partial_be_runner"
        state.gtos_vnext_execution_policy_id = "unit_partial_policy"
        old_ticket = state.ticket
        opposite_ticket = 88001
        mt5._positions.insert(
            0,
            PositionInfo(
                ticket=opposite_ticket,
                symbol="XAUUSD",
                type=1,
                volume=0.33,
                price_open=2648.0,
                sl=2660.0,
                tp=2630.0,
                profit=0.0,
                magic=MAGIC_NUMBER,
                comment="opposite_short",
                time=datetime.now(timezone.utc),
            ),
        )

        mt5.set_tick(2670.00, 2670.18)
        action = engine.check_and_manage_trade({})

        assert action == "tp1_partial_vnext_partial_be_runner"
        assert engine.active_trade is not None
        assert engine.active_trade.ticket != opposite_ticket
        assert engine.active_trade.ticket != old_ticket
        residual = next(p for p in mt5._positions if p.ticket == engine.active_trade.ticket)
        assert residual.type == 0
        modify_tickets = [
            request.get("position")
            for request in mt5._order_log
            if request.get("action") == TRADE_ACTION_SLTP
        ]
        assert modify_tickets
        assert all(ticket == residual.ticket for ticket in modify_tickets)

    def test_vnext_partial_close_reconciles_delayed_residual_before_be_modify(
        self,
        mt5,
        monkeypatch,
    ):
        """A successful partial close can outpace MT5 positions_get propagation."""
        config = {
            "risk": {"risk_per_trade_pct": 1.0, "tp1_close_pct": 50},
            "gtos_vnext_runtime": {
                "moonshot_dynamic_execution_router_partial_close_ratio": 0.5,
                "moonshot_dynamic_execution_router_partial_final_target_r": 3.0,
            },
        }
        engine = ExecutionEngine(mt5, config)
        state = engine.open_trade(_trade_params(), 100000.0)
        assert state is not None
        state.gtos_vnext_dynamic_policy_applied = True
        state.gtos_vnext_dynamic_policy_selected = "partial_be_runner"
        state.gtos_vnext_execution_policy_id = "unit_partial_policy"
        old_ticket = state.ticket

        original_get_positions = mt5.get_positions
        original_order_send = mt5.order_send
        close_seen = {"value": False}
        hidden_reads = {"count": 0}

        def laggy_get_positions(symbol="XAUUSD"):
            if not close_seen["value"]:
                return original_get_positions(symbol)
            if hidden_reads["count"] < 2:
                hidden_reads["count"] += 1
                return []
            return original_get_positions(symbol)

        def order_send_with_position_lag(request):
            result = original_order_send(request)
            if request.get("action") == 1 and request.get("position") == old_ticket:
                close_seen["value"] = True
            return result

        monkeypatch.setattr(_exec_mod.time, "sleep", lambda *_args, **_kwargs: None)
        monkeypatch.setattr(mt5, "get_positions", laggy_get_positions)
        monkeypatch.setattr(mt5, "order_send", order_send_with_position_lag)

        mt5.set_tick(2670.00, 2670.18)
        action = engine.check_and_manage_trade({})

        assert action == "tp1_partial_vnext_partial_be_runner"
        assert engine.active_trade is not None
        assert engine.active_trade.ticket != old_ticket
        assert engine.active_trade.sl_at_breakeven is True
        assert hidden_reads["count"] == 2
        assert any(
            event.get("type") == "PARTIAL_CLOSE_RESIDUAL_TICKET_RECONCILED"
            for event in engine.active_trade.partial_close_events
        )
        assert any(
            request.get("action") == TRADE_ACTION_SLTP
            and request.get("position") == engine.active_trade.ticket
            for request in mt5._order_log
        )
        partial_requests = [
            request for request in mt5._order_log
            if request.get("action") == 1 and request.get("position") == old_ticket
        ]
        assert len(partial_requests) == 1

    def test_tp2_partial_close_after_tp1_legacy(self, mt5):
        """TP2 partial only triggers when using legacy partial close (tp1_close_pct < 100)."""
        config = {"risk": {"risk_per_trade_pct": 1.0, "tp1_close_pct": 50}}
        engine = ExecutionEngine(mt5, config)
        state = engine.open_trade(_trade_params(), 100000.0)
        # Hit TP1 (partial close)
        mt5.set_tick(2670.00, 2670.18)
        engine.check_and_manage_trade({})
        assert engine.active_trade.tp1_hit

        # Hit TP2
        mt5.set_tick(2680.00, 2680.18)
        action = engine.check_and_manage_trade({})
        assert action == "tp2_partial"
        assert engine.active_trade.tp2_hit

    def test_broker_closed_detection(self, mt5, engine):
        state = engine.open_trade(_trade_params(), 100000.0)
        # First call: position visible to MT5 → confirms it (sets
        # position_confirmed=True so the post-fill propagation race guard
        # disengages for this trade).
        engine.check_and_manage_trade({})
        assert engine.active_trade is not None
        assert engine.active_trade.position_confirmed is True
        # Now remove all positions (simulating broker SL hit) — true close.
        mt5._positions.clear()
        action = engine.check_and_manage_trade({})
        assert action == "broker_closed"
        assert engine.active_trade is None

    def test_broker_closed_race_guard_suppresses_false_close(self, mt5, engine):
        """Post-fill MT5 propagation race: positions_get returns empty within
        ~13ms of order_send while MT5 is still propagating. The guard returns
        "monitoring" instead of "broker_closed" until either (a) we see the
        position at least once, or (b) 5s elapses. Prevents the orch from
        falsely retiring a real LIVE position (observed 2026-04-29 NAS100
        ticket 234432798).
        """
        state = engine.open_trade(_trade_params(), 100000.0)
        # Simulate the race: position never appears in positions_get
        # (MT5 internal state hasn't propagated yet).
        mt5._positions.clear()
        # entry_time is 'now' so age < 5s → guard kicks in.
        action = engine.check_and_manage_trade({})
        assert action == "monitoring", (
            f"Race guard should defer broker_closed within 5s of fill; got {action}"
        )
        assert engine.active_trade is not None, (
            "Race guard must keep active_trade alive — orch tracks it"
        )
        assert engine.active_trade.position_confirmed is False

    def test_broker_closed_race_guard_clears_after_first_sight(self, mt5, engine):
        """After the position is seen at least once, position_confirmed=True
        and a subsequent empty positions_get IS treated as a real broker close
        (no false-defer). This is the normal SL/TP-hit detection path.
        """
        state = engine.open_trade(_trade_params(), 100000.0)
        # First check: position is visible (MT5 has propagated).
        engine.check_and_manage_trade({})
        assert engine.active_trade.position_confirmed is True
        # Now broker actually closes (TP/SL hit).
        mt5._positions.clear()
        action = engine.check_and_manage_trade({})
        # No deferral — confirmed positions exit cleanly on disappearance.
        assert action == "broker_closed"
        assert engine.active_trade is None

    def test_vnext_broker_closed_defers_when_position_absent_without_close_deal(
        self, mt5, engine
    ):
        state = engine.open_trade(_trade_params(), 100000.0)
        state.gtos_vnext_dynamic_policy_applied = True
        state.gtos_vnext_dynamic_policy_selected = "partial_be_runner"
        state.gtos_vnext_execution_policy_id = "vnext_exec_partial_be_runner"

        engine.check_and_manage_trade({})
        assert engine.active_trade.position_confirmed is True

        mt5._positions.clear()
        mt5._mt5 = SimpleNamespace(history_deals_get=lambda *args: [])

        action = engine.check_and_manage_trade({})

        assert action == "monitoring"
        assert engine.active_trade is state

    def test_vnext_broker_closed_defers_when_deal_history_unavailable(
        self, mt5, engine
    ):
        state = engine.open_trade(_trade_params(), 100000.0)
        state.gtos_vnext_dynamic_policy_applied = True
        state.gtos_vnext_dynamic_policy_selected = "partial_be_runner"
        state.gtos_vnext_execution_policy_id = "vnext_exec_partial_be_runner"

        engine.check_and_manage_trade({})
        assert engine.active_trade.position_confirmed is True

        mt5._positions.clear()
        mt5.get_history_deals = lambda *args, **kwargs: None
        mt5._mt5 = None

        action = engine.check_and_manage_trade({})

        assert action == "monitoring"
        assert engine.active_trade is state

    def test_vnext_broker_closed_accepts_absent_position_with_close_deal(
        self, mt5, engine
    ):
        state = engine.open_trade(_trade_params(), 100000.0)
        state.gtos_vnext_dynamic_policy_applied = True
        state.gtos_vnext_dynamic_policy_selected = "partial_be_runner"
        state.gtos_vnext_execution_policy_id = "vnext_exec_partial_be_runner"

        engine.check_and_manage_trade({})
        assert engine.active_trade.position_confirmed is True

        mt5._positions.clear()
        mt5._mt5 = SimpleNamespace(
            history_deals_get=lambda *args: [
                SimpleNamespace(position_id=state.ticket, entry=1)
            ]
        )

        action = engine.check_and_manage_trade({})

        assert action == "broker_closed"
        assert engine.active_trade is None

    def test_vnext_broker_closed_accepts_wrapper_dict_close_deal(
        self, mt5, engine
    ):
        state = engine.open_trade(_trade_params(), 100000.0)
        state.gtos_vnext_dynamic_policy_applied = True
        state.gtos_vnext_dynamic_policy_selected = "partial_be_runner"
        state.gtos_vnext_execution_policy_id = "vnext_exec_partial_be_runner"

        engine.check_and_manage_trade({})
        assert engine.active_trade.position_confirmed is True

        mt5._positions.clear()
        mt5.get_history_deals = lambda *args, **kwargs: [
            {"position_id": state.ticket, "entry": 1}
        ]

        action = engine.check_and_manage_trade({})

        assert action == "broker_closed"
        assert engine.active_trade is None

    def test_tp1_full_close_zero_price_fallback_long(self, mt5, engine, caplog):
        """TP1 full-close: MT5 result.price=0.0 -> fall back to tick.bid for LONG.

        Regression for CLAUDE.md unresolved #7 (A2 scope-out).  The partial-close
        paths write ``result.price`` into ``trade.partial_close_events`` which
        orchestrator.py:1674-1691 consumes for R attribution and exit-price
        logging.  A raw 0.0 would corrupt time-in-trade shadow logger R.
        """
        import logging
        from src.mt5.mt5_interface import OrderResult

        engine.open_trade(_trade_params(direction="LONG"), 100000.0)
        assert engine.active_trade is not None

        # Wrap order_send: force price=0.0 on the TP1 close request only, leave
        # fill + modify paths unchanged.
        original_send = mt5.order_send

        def zero_price_close(request):
            res = original_send(request)
            if request.get("action") == 1 and "position" in request:
                return OrderResult(
                    retcode=res.retcode, order=res.order, volume=res.volume,
                    price=0.0, comment=res.comment,
                )
            return res

        mt5.order_send = zero_price_close
        # For a LONG close the fallback must use tick.bid, not tick.ask.
        mt5.set_tick(bid=2670.10, ask=2670.28)

        with caplog.at_level(logging.WARNING, logger="src.components.execution"):
            action = engine.check_and_manage_trade({})

        assert action == "tp1_full_close"
        # The full-close event's price must be the bid fallback, not 0.0.
        # active_trade is cleared after full close, so we fetch from the MT5 log
        # of order_send requests instead.  Easier: inspect the caplog + verify
        # the stored event via a fresh engine probe is not possible here --
        # active_trade is None.  Assert via the warning message that the
        # fallback was chosen and exposed the expected bid price.
        warnings = [r.getMessage() for r in caplog.records
                    if r.levelname == "WARNING"]
        assert any(
            "TP1 full close price returned 0.0 from MT5" in w and "2670.10" in w
            for w in warnings
        ), f"expected TP1 full-close bid fallback; got {warnings}"
        assert not any("2670.28" in w for w in warnings), \
            f"LONG close must NOT use tick.ask as fallback; got {warnings}"

    def test_tp1_full_close_zero_price_fallback_short(self, mt5, engine, caplog):
        """TP1 full-close SHORT: fallback must be tick.ask (SHORT closes lift the ask)."""
        import logging
        from src.mt5.mt5_interface import OrderResult

        engine.open_trade(_trade_params(direction="SHORT", entry=2650.0,
                                        sl=2660.0, tp1=2630.0), 100000.0)
        assert engine.active_trade.direction == "SHORT"

        original_send = mt5.order_send

        def zero_price_close(request):
            res = original_send(request)
            if request.get("action") == 1 and "position" in request:
                return OrderResult(
                    retcode=res.retcode, order=res.order, volume=res.volume,
                    price=0.0, comment=res.comment,
                )
            return res

        mt5.order_send = zero_price_close
        # Price below TP1 (2630.0) triggers TP1 hit for SHORT.
        mt5.set_tick(bid=2628.05, ask=2628.20)

        with caplog.at_level(logging.WARNING, logger="src.components.execution"):
            action = engine.check_and_manage_trade({})

        assert action == "tp1_full_close"
        warnings = [r.getMessage() for r in caplog.records
                    if r.levelname == "WARNING"]
        # SHORT close must use ask (2628.20), NOT bid (2628.05).
        assert any(
            "TP1 full close price returned 0.0 from MT5" in w and "2628.20" in w
            for w in warnings
        ), f"expected SHORT TP1 ask fallback; got {warnings}"
        assert not any("2628.05" in w for w in warnings), \
            f"SHORT close must NOT use tick.bid as fallback; got {warnings}"

    def test_tp1_full_close_nonzero_price_no_fallback(self, mt5, engine, caplog):
        """Negative case: TP1 full close with a non-zero price logs NO fallback warning."""
        import logging

        engine.open_trade(_trade_params(direction="LONG"), 100000.0)
        mt5.set_tick(bid=2670.00, ask=2670.18)

        with caplog.at_level(logging.WARNING, logger="src.components.execution"):
            action = engine.check_and_manage_trade({})

        assert action == "tp1_full_close"
        # No fallback warning should appear under normal fill.
        warnings = [r.getMessage() for r in caplog.records
                    if r.levelname == "WARNING"]
        assert not any(
            "TP1 full close price returned 0.0 from MT5" in w
            for w in warnings
        ), f"expected no fallback when price>0; got {warnings}"

    def test_tp1_partial_close_zero_price_fallback_long(self, mt5, caplog):
        """TP1 partial-close legacy path: MT5 price=0.0 -> tick.bid for LONG.

        ``trade.partial_close_events[-1]["price"]`` is written to JSON and fed
        to orchestrator R attribution at orchestrator.py:1686; a stored 0.0
        would produce a spurious negative R.
        """
        import logging
        from src.mt5.mt5_interface import OrderResult

        config = {"risk": {"risk_per_trade_pct": 1.0, "tp1_close_pct": 50}}
        engine = ExecutionEngine(mt5, config)
        engine.open_trade(_trade_params(direction="LONG"), 100000.0)

        original_send = mt5.order_send

        def zero_price_close(request):
            res = original_send(request)
            if request.get("action") == 1 and "position" in request:
                return OrderResult(
                    retcode=res.retcode, order=res.order, volume=res.volume,
                    price=0.0, comment=res.comment,
                )
            return res

        mt5.order_send = zero_price_close
        mt5.set_tick(bid=2670.15, ask=2670.33)

        with caplog.at_level(logging.WARNING, logger="src.components.execution"):
            action = engine.check_and_manage_trade({})

        assert action == "tp1_partial"
        # Stored event price must be the bid fallback, not 0.0.
        events = engine.active_trade.partial_close_events
        tp1_events = [event for event in events if event.get("type") == "TP1_PARTIAL"]
        assert len(tp1_events) == 1
        assert tp1_events[0]["price"] == 2670.15, \
            f"TP1_PARTIAL event price must be tick.bid fallback; got {tp1_events[0]['price']}"
        warnings = [r.getMessage() for r in caplog.records
                    if r.levelname == "WARNING"]
        assert any(
            "TP1 partial close price returned 0.0 from MT5" in w and "2670.15" in w
            for w in warnings
        ), f"expected TP1 partial bid fallback warning; got {warnings}"

    def test_tp1_partial_close_nonzero_price_no_fallback(self, mt5, caplog):
        """Negative case: TP1 partial with a real price logs no fallback + stores real price."""
        import logging

        config = {"risk": {"risk_per_trade_pct": 1.0, "tp1_close_pct": 50}}
        engine = ExecutionEngine(mt5, config)
        engine.open_trade(_trade_params(direction="LONG"), 100000.0)
        mt5.set_tick(bid=2670.00, ask=2670.18)

        with caplog.at_level(logging.WARNING, logger="src.components.execution"):
            action = engine.check_and_manage_trade({})

        assert action == "tp1_partial"
        events = engine.active_trade.partial_close_events
        tp1_events = [event for event in events if event.get("type") == "TP1_PARTIAL"]
        assert len(tp1_events) == 1
        assert tp1_events[0]["price"] > 0
        warnings = [r.getMessage() for r in caplog.records
                    if r.levelname == "WARNING"]
        assert not any(
            "TP1 partial close price returned 0.0 from MT5" in w
            for w in warnings
        ), f"expected no fallback when price>0; got {warnings}"

    def test_tp2_partial_close_zero_price_fallback_long(self, mt5, caplog):
        """TP2 partial-close legacy path: MT5 price=0.0 -> tick.bid for LONG."""
        import logging
        from src.mt5.mt5_interface import OrderResult

        config = {"risk": {"risk_per_trade_pct": 1.0, "tp1_close_pct": 50}}
        engine = ExecutionEngine(mt5, config)
        engine.open_trade(_trade_params(direction="LONG"), 100000.0)

        # Step 1: hit TP1 normally to leave trade in partial state so TP2 path
        # becomes eligible.
        mt5.set_tick(bid=2670.00, ask=2670.18)
        engine.check_and_manage_trade({})
        assert engine.active_trade.tp1_hit

        # Step 2: patch order_send only for the TP2 close.
        original_send = mt5.order_send

        def zero_price_close(request):
            res = original_send(request)
            if request.get("action") == 1 and "position" in request:
                return OrderResult(
                    retcode=res.retcode, order=res.order, volume=res.volume,
                    price=0.0, comment=res.comment,
                )
            return res

        mt5.order_send = zero_price_close
        # Hit TP2 (2680.0)
        mt5.set_tick(bid=2680.22, ask=2680.40)

        with caplog.at_level(logging.WARNING, logger="src.components.execution"):
            action = engine.check_and_manage_trade({})

        assert action == "tp2_partial"
        events = engine.active_trade.partial_close_events
        tp2_events = [e for e in events if e.get("type") == "TP2_PARTIAL"]
        assert len(tp2_events) == 1
        assert tp2_events[0]["price"] == 2680.22, \
            f"TP2_PARTIAL event price must be tick.bid fallback; got {tp2_events[0]['price']}"
        warnings = [r.getMessage() for r in caplog.records
                    if r.levelname == "WARNING"]
        assert any(
            "TP2 partial close price returned 0.0 from MT5" in w and "2680.22" in w
            for w in warnings
        ), f"expected TP2 partial bid fallback warning; got {warnings}"
        assert not any("2680.40" in w for w in warnings), \
            f"LONG TP2 close must NOT use tick.ask; got {warnings}"

    def test_tp2_partial_close_zero_price_fallback_short(self, mt5, caplog):
        """TP2 partial SHORT: fallback must be tick.ask, not bid."""
        import logging
        from src.mt5.mt5_interface import OrderResult

        config = {"risk": {"risk_per_trade_pct": 1.0, "tp1_close_pct": 50}}
        engine = ExecutionEngine(mt5, config)
        engine.open_trade(_trade_params(direction="SHORT", entry=2650.0,
                                        sl=2660.0, tp1=2630.0, tp2=2620.0,
                                        tp3=2610.0), 100000.0)

        # Hit TP1 normally.
        mt5.set_tick(bid=2628.00, ask=2628.15)
        engine.check_and_manage_trade({})
        assert engine.active_trade.tp1_hit

        original_send = mt5.order_send

        def zero_price_close(request):
            res = original_send(request)
            if request.get("action") == 1 and "position" in request:
                return OrderResult(
                    retcode=res.retcode, order=res.order, volume=res.volume,
                    price=0.0, comment=res.comment,
                )
            return res

        mt5.order_send = zero_price_close
        # Hit TP2 (2620.0) from the SHORT side.
        mt5.set_tick(bid=2618.10, ask=2618.25)

        with caplog.at_level(logging.WARNING, logger="src.components.execution"):
            action = engine.check_and_manage_trade({})

        assert action == "tp2_partial"
        events = engine.active_trade.partial_close_events
        tp2_events = [e for e in events if e.get("type") == "TP2_PARTIAL"]
        assert len(tp2_events) == 1
        # SHORT close uses tick.ask, not tick.bid.
        assert tp2_events[0]["price"] == 2618.25
        warnings = [r.getMessage() for r in caplog.records
                    if r.levelname == "WARNING"]
        assert any(
            "TP2 partial close price returned 0.0 from MT5" in w and "2618.25" in w
            for w in warnings
        ), f"expected TP2 SHORT ask fallback warning; got {warnings}"
        assert not any("2618.10" in w for w in warnings), \
            f"SHORT TP2 close must NOT use tick.bid; got {warnings}"

    def test_tp2_partial_close_nonzero_price_no_fallback(self, mt5, caplog):
        """Negative case: TP2 partial with real price logs no fallback."""
        import logging

        config = {"risk": {"risk_per_trade_pct": 1.0, "tp1_close_pct": 50}}
        engine = ExecutionEngine(mt5, config)
        engine.open_trade(_trade_params(direction="LONG"), 100000.0)
        # Hit TP1
        mt5.set_tick(bid=2670.00, ask=2670.18)
        engine.check_and_manage_trade({})
        # Hit TP2
        mt5.set_tick(bid=2680.00, ask=2680.18)

        with caplog.at_level(logging.WARNING, logger="src.components.execution"):
            action = engine.check_and_manage_trade({})

        assert action == "tp2_partial"
        warnings = [r.getMessage() for r in caplog.records
                    if r.levelname == "WARNING"]
        assert not any(
            "TP2 partial close price returned 0.0 from MT5" in w
            for w in warnings
        ), f"expected no fallback when price>0; got {warnings}"

    def test_tp1_full_close_zero_price_no_tick(self, mt5, engine, caplog):
        """TP1 full close with zero price AND no tick -> degraded-data warning; action still succeeds."""
        import logging
        from src.mt5.mt5_interface import OrderResult

        engine.open_trade(_trade_params(direction="LONG"), 100000.0)
        # Trigger TP1 via a real tick first so check_and_manage_trade routes to
        # full-close.  Then clobber both order_send (zero price) AND get_tick
        # (None) on the very next call.
        mt5.set_tick(bid=2670.00, ask=2670.18)

        def zero_price_send(request):
            # Still accept modify requests if any precede the close.
            if request.get("action") == 1 and "position" in request:
                return OrderResult(
                    retcode=10009, order=request["position"],
                    volume=request.get("volume", 0.0), price=0.0,
                    comment="mock zero price",
                )
            # Shouldn't be reached in TP1-full path, but be defensive.
            return OrderResult(retcode=10011, order=0, volume=0.0, price=0.0,
                               comment="unexpected")

        # Wire up AFTER open_trade (which needs a real tick) but BEFORE
        # check_and_manage_trade reads the tick for its price compare.  Since
        # check_and_manage_trade ALSO calls get_tick for the current-price
        # check, we must preserve that first read: provide get_tick that
        # returns the tick once, then None.
        call_count = {"n": 0}
        def get_tick_once_then_none(symbol="XAUUSD"):
            call_count["n"] += 1
            if call_count["n"] == 1:
                # First call: inside check_and_manage_trade for price compare.
                from datetime import datetime, timezone as _tz
                from src.mt5.mt5_interface import TickData
                return TickData(bid=2670.00, ask=2670.18,
                                time=datetime.now(_tz.utc), spread_cents=18.0)
            # Subsequent calls (the fallback lookup): degraded.
            return None

        mt5.order_send = zero_price_send
        mt5.get_tick = get_tick_once_then_none

        with caplog.at_level(logging.WARNING, logger="src.components.execution"):
            action = engine.check_and_manage_trade({})

        assert action == "tp1_full_close", \
            f"must still complete TP1 full close under degraded data; got {action}"
        assert engine.active_trade is None
        warnings = [r.getMessage() for r in caplog.records
                    if r.levelname == "WARNING"]
        assert any(
            "TP1 full close price returned 0.0 from MT5 and no tick available" in w
            for w in warnings
        ), f"expected TP1 full-close degraded-data warning; got {warnings}"


class TestClosePosition:
    def test_close_full_position(self, mt5, engine):
        engine.open_trade(_trade_params(), 100000.0)
        assert engine.active_trade is not None
        result = engine.close_position("manual")
        assert result
        assert engine.active_trade is None
        assert len(mt5.get_positions()) == 0

    def test_close_position_emits_close_side_slippage_log(self, mt5, engine, tmp_path, monkeypatch):
        import src.components.slippage_shadow_logger as _sl_mod

        log_file = tmp_path / "slippage.jsonl"
        monkeypatch.setattr(_sl_mod, "SHADOW_LOG_PATH", str(log_file))

        state = engine.open_trade(_trade_params(), 100000.0)
        assert state is not None
        mt5.set_tick(bid=2661.25, ask=2661.40)

        assert engine.close_position("manual")

        rows = [json.loads(line) for line in log_file.read_text().splitlines()]
        close_rows = [row for row in rows if row.get("slippage_event_type") == "close"]
        assert len(close_rows) == 1
        row = close_rows[0]
        assert row["ticket"] == state.ticket
        assert row["close_reason"] == "manual"
        assert row["close_event_type"] == "FULL_POSITION_CLOSE"
        assert row["requested_price"] == pytest.approx(2661.25)
        assert row["volume_closed"] == pytest.approx(state.initial_volume)
        assert row["remaining_volume"] == 0.0
        assert row["mt5_deal_id_status"] == "ACCOUNT_HISTORY_REQUIRED"
        assert row["commission_status"] == "ACCOUNT_HISTORY_REQUIRED"
        assert row["no_execution_effect"] is True

    def test_close_no_position(self, engine):
        assert not engine.close_position("manual")

    def test_close_zero_price_fallback_long(self, mt5, engine, caplog):
        """MT5 can return result.price=0.0 on close; fall back to tick.bid for LONG.

        Regression for USDJPY 2026-04-23 09:30 UTC trailing-BE force close
        where result.price came back as 0.0 (audited in
        research/thursday_2026-04-23_analysis/USDJPY_analysis.md).  The fill
        side already has this fallback at execution.py:417-425; close side
        must mirror it.
        """
        import logging

        engine.open_trade(_trade_params(direction="LONG"), 100000.0)
        assert engine.active_trade is not None

        # Force result.price=0.0 on the close order_send, keep SL/TP modify
        # behavior intact so only the close path is exercised.
        original_send = mt5.order_send

        def zero_price_close(request):
            res = original_send(request)
            if request.get("action") == 1 and "position" in request:
                from src.mt5.mt5_interface import OrderResult
                return OrderResult(
                    retcode=res.retcode, order=res.order, volume=res.volume,
                    price=0.0, comment=res.comment,
                )
            return res

        mt5.order_send = zero_price_close
        # Set a known tick so the fallback is deterministic; for a LONG close
        # we hit the bid.
        mt5.set_tick(bid=2661.25, ask=2661.40)

        with caplog.at_level(logging.WARNING, logger="src.components.execution"):
            ok = engine.close_position("sl_modification_failed")

        assert ok
        assert engine.active_trade is None
        # Warning must mention the fallback and the tick.bid price.
        warnings = [r.getMessage() for r in caplog.records
                    if r.levelname == "WARNING"]
        assert any(
            "Close price returned 0.0 from MT5" in w and "2661.25" in w
            for w in warnings
        ), f"expected fallback warning; got {warnings}"

    def test_close_zero_price_fallback_short(self, mt5, engine, caplog):
        """Mirror fallback for SHORT close must use tick.ask (SHORT closes lift the ask)."""
        import logging
        from src.mt5.mt5_interface import OrderResult

        engine.open_trade(_trade_params(direction="SHORT", entry=2650.0,
                                        sl=2660.0, tp1=2630.0), 100000.0)
        assert engine.active_trade is not None
        assert engine.active_trade.direction == "SHORT"

        original_send = mt5.order_send

        def zero_price_close(request):
            res = original_send(request)
            if request.get("action") == 1 and "position" in request:
                return OrderResult(
                    retcode=res.retcode, order=res.order, volume=res.volume,
                    price=0.0, comment=res.comment,
                )
            return res

        mt5.order_send = zero_price_close
        mt5.set_tick(bid=2638.10, ask=2638.25)

        with caplog.at_level(logging.WARNING, logger="src.components.execution"):
            ok = engine.close_position("manual")
        assert ok

        warnings = [r.getMessage() for r in caplog.records
                    if r.levelname == "WARNING"]
        # SHORT close must use the ask (2638.25) as fallback, NOT the bid.
        assert any(
            "Close price returned 0.0 from MT5" in w and "2638.25" in w
            for w in warnings
        ), f"expected SHORT fallback using tick.ask; got {warnings}"
        assert not any("2638.10" in w for w in warnings), \
            f"SHORT close must NOT use tick.bid as fallback; got {warnings}"

    def test_close_zero_price_no_tick_available(self, mt5, engine, caplog):
        """If MT5 returns 0.0 and tick is also unavailable, log and proceed.

        Short-circuits order_send so the Mock's `self._tick.bid` read doesn't
        trigger before we get to the fallback branch; get_tick is mocked
        separately to return None and exercise the null-tick warning path.
        """
        import logging
        from src.mt5.mt5_interface import OrderResult

        engine.open_trade(_trade_params(), 100000.0)
        ticket = engine.active_trade.ticket

        # Short-circuit order_send entirely for the close request: return a
        # success result with price=0.0 without touching the MockMT5
        # internals (which rely on _tick).
        def zero_price_send(request):
            if request.get("action") == 1 and "position" in request:
                # Simulate broker success but with price=0.0
                return OrderResult(
                    retcode=10009, order=request["position"],
                    volume=request.get("volume", 0.0), price=0.0,
                    comment="mock zero price close",
                )
            # Shouldn't happen in this test, but fall through defensively.
            return OrderResult(retcode=10011, order=0, volume=0, price=0,
                               comment="unexpected")

        mt5.order_send = zero_price_send
        # get_tick returns None -> fallback cannot resolve, warning only.
        mt5.get_tick = lambda symbol="XAUUSD": None

        with caplog.at_level(logging.WARNING, logger="src.components.execution"):
            ok = engine.close_position("manual")

        assert ok, f"close_position must still return True on zero-price success; ticket={ticket}"
        assert engine.active_trade is None
        warnings = [r.getMessage() for r in caplog.records
                    if r.levelname == "WARNING"]
        assert any("no tick available" in w for w in warnings), warnings

    def test_close_10011_does_not_clear_or_flatten(self, mt5, engine, caplog):
        """order_send None/10011 is broker-unknown: keep active_trade, no disk close."""
        import logging
        from src.components.ultimate_book.minimal_size import (
            f5_close_send_none_reset,
            f5_close_send_none_seen,
            f5_close_send_none_should_defer_disk_closed,
        )

        f5_close_send_none_reset()
        engine.open_trade(_trade_params(), 100000.0)
        ticket = engine.active_trade.ticket
        sends = {"n": 0}

        def none_send(_request):
            sends["n"] += 1
            return OrderResult(
                retcode=10011, order=0, volume=0, price=0,
                comment="MT5 returned None",
            )

        mt5.order_send = none_send
        with caplog.at_level(logging.ERROR, logger="src.components.execution"):
            ok = engine.close_position("vnext_time_stop")
        assert ok is False
        assert engine.active_trade is not None
        assert engine.active_trade.ticket == ticket
        assert sends["n"] == 1
        assert f5_close_send_none_seen(ticket)
        assert f5_close_send_none_should_defer_disk_closed(ticket)
        assert any("Failed to close position" in r.getMessage() for r in caplog.records)

    def test_close_10011_backoff_skips_order_send(self, mt5, engine):
        from src.components.ultimate_book.minimal_size import f5_close_send_none_reset

        f5_close_send_none_reset()
        engine.open_trade(_trade_params(), 100000.0)
        sends = {"n": 0}

        def none_send(_request):
            sends["n"] += 1
            return OrderResult(
                retcode=10011, order=0, volume=0, price=0,
                comment="MT5 returned None",
            )

        mt5.order_send = none_send
        assert engine.close_position("f5_manage") is False
        assert sends["n"] == 1
        assert engine.close_position("f5_manage") is False
        assert sends["n"] == 1
        assert engine.active_trade is not None

    def test_close_10011_absent_sit_does_not_send_or_flatten(self, mt5, engine):
        from src.components.ultimate_book.minimal_size import (
            f5_close_send_none_is_dead,
            f5_close_send_none_reset,
        )

        f5_close_send_none_reset()
        engine.open_trade(_trade_params(), 100000.0)
        sends = {"n": 0}

        def none_send(_request):
            sends["n"] += 1
            return OrderResult(
                retcode=10011, order=0, volume=0, price=0,
                comment="MT5 returned None",
            )

        mt5.order_send = none_send
        assert engine.close_position("vnext_time_stop") is False
        mt5._positions.clear()
        assert engine.close_position("vnext_time_stop") is False
        assert sends["n"] == 1
        assert engine.active_trade is not None
        assert f5_close_send_none_is_dead(engine.active_trade.ticket)

    def test_check_and_manage_defers_disk_closed_after_10011(self, mt5, engine):
        from src.components.ultimate_book.minimal_size import f5_close_send_none_reset

        f5_close_send_none_reset()
        engine.open_trade(_trade_params(), 100000.0)
        engine.check_and_manage_trade({})
        assert engine.active_trade.position_confirmed is True

        def none_send(_request):
            return OrderResult(
                retcode=10011, order=0, volume=0, price=0,
                comment="MT5 returned None",
            )

        mt5.order_send = none_send
        assert engine.close_position("vnext_time_stop") is False
        mt5._positions.clear()
        action = engine.check_and_manage_trade({})
        assert action == "monitoring"
        assert engine.active_trade is not None


class TestTimeoutTrailing:
    def test_handle_timeout_moves_sl_to_be_when_in_profit(self, mt5, engine):
        engine.open_trade(_trade_params(), 100000.0)
        # Tick must show profit: bid > entry for LONG
        mt5.set_tick(bid=2655.0, ask=2655.18)
        action = engine.handle_timeout_trailing()
        assert action == "trailing"
        assert engine.active_trade.sl_at_breakeven

    def test_handle_timeout_skips_be_when_underwater(self, mt5, engine):
        engine.open_trade(_trade_params(), 100000.0)
        original_sl = engine.active_trade.stop_loss
        # Tick shows loss: bid < entry for LONG
        mt5.set_tick(bid=2645.0, ask=2645.18)
        action = engine.handle_timeout_trailing()
        assert action == "trailing"
        assert not engine.active_trade.sl_at_breakeven
        assert engine.active_trade.stop_loss == original_sl
        assert engine.active_trade is not None  # NOT closed

    def test_handle_timeout_no_trade(self, engine):
        assert engine.handle_timeout_trailing() == "no_trade"


class TestJ46J49BreakevenGating:
    """BUG #27 (2026-04-28): when J46-J49 v2 is active, SL→BE must
    fire ONLY when current R-progress >= tp1_distance_r (3.0R), NOT
    on any-positive-profit. Triggered by orphan adoption at +0.74R
    on GBPJPY 2026-04-28.
    """

    def _j46_j49_engine(self, mt5):
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
                },
            },
        }
        return ExecutionEngine(mt5, config)

    def test_orphan_adopt_at_low_r_does_not_move_sl_to_be(self, mt5):
        """An adopted orphan position at +0.5R must not trigger BE move
        when J46-J49 is active (BE trigger is 3R).
        """
        engine = self._j46_j49_engine(mt5)
        # GBPJPY-shaped scenario: entry 215.20, SL 214.89 (~31 pips =
        # 0.31 sl_distance), BE trigger requires +0.93 move (3R).
        entry = 215.20
        sl = 214.89
        tp = 216.43  # 6R higher target (4 * 0.31 above entry... actually 4 not 6 for this math)
        # 6R = entry + 6*0.31 = 215.20 + 1.86 = 217.06
        tp = 217.06
        mt5._positions.append(PositionInfo(
            ticket=233955223, symbol="GBPJPY", type=0, volume=7.76,
            price_open=entry, sl=sl, tp=tp, profit=1390.55,
            magic=MAGIC_NUMBER, comment="adopted",
            time=datetime.now(timezone.utc),
        ))
        # Engine fixture uses XAUUSD, override symbol
        engine.symbol = "GBPJPY"

        actions = engine.reconcile_on_startup()
        assert any("orphan_adopted" in a for a in actions)
        assert engine.active_trade is not None
        assert engine.active_trade.ticket == 233955223
        original_sl = engine.active_trade.stop_loss

        # Set tick at +0.74R (mid-cascade GBPJPY price 215.55900)
        # progress = (215.559 - 215.20) / 0.31 = 1.16R — actually let's
        # use the production number directly
        # +0.74R means current = 215.20 + 0.74 * 0.31 = 215.4294
        mt5.set_tick(bid=215.4294, ask=215.4310)

        action = engine.handle_timeout_trailing()
        assert action == "trailing"
        # CRITICAL: SL must NOT have been moved to BE.
        assert not engine.active_trade.sl_at_breakeven, (
            "SL was moved to BE at +0.74R when J46-J49 trigger is +3R "
            "(this is BUG #27)"
        )
        assert engine.active_trade.stop_loss == original_sl
        # Position must remain open.
        assert engine.active_trade is not None

    def test_orphan_adopt_at_3r_does_trigger_be(self, mt5):
        """Positive case: when adopted orphan is actually at +3R,
        BE move must fire (J46-J49 trigger semantics).
        """
        engine = self._j46_j49_engine(mt5)
        entry = 215.20
        sl = 214.89  # sl_distance = 0.31
        tp = 217.06  # 6R
        mt5._positions.append(PositionInfo(
            ticket=233955223, symbol="GBPJPY", type=0, volume=7.76,
            price_open=entry, sl=sl, tp=tp, profit=4500.0,
            magic=MAGIC_NUMBER, comment="adopted",
            time=datetime.now(timezone.utc),
        ))
        engine.symbol = "GBPJPY"

        engine.reconcile_on_startup()
        assert engine.active_trade is not None

        # +3R: current = 215.20 + 3 * 0.31 = 216.13
        mt5.set_tick(bid=216.13, ask=216.14)

        action = engine.handle_timeout_trailing()
        assert action == "trailing"
        # BE trigger satisfied → SL should now be at entry.
        assert engine.active_trade.sl_at_breakeven, (
            "BE move should fire at +3R when J46-J49 active"
        )
        assert engine.active_trade.stop_loss == entry

    def test_orphan_adopt_above_3r_does_trigger_be(self, mt5):
        """Edge: at +3.5R BE must still fire (>= comparison)."""
        engine = self._j46_j49_engine(mt5)
        entry = 215.20
        sl = 214.89
        tp = 217.06
        mt5._positions.append(PositionInfo(
            ticket=233955223, symbol="GBPJPY", type=0, volume=7.76,
            price_open=entry, sl=sl, tp=tp, profit=5500.0,
            magic=MAGIC_NUMBER, comment="adopted",
            time=datetime.now(timezone.utc),
        ))
        engine.symbol = "GBPJPY"
        engine.reconcile_on_startup()

        # +3.5R
        mt5.set_tick(bid=215.20 + 3.5 * 0.31, ask=215.21 + 3.5 * 0.31)
        engine.handle_timeout_trailing()
        assert engine.active_trade.sl_at_breakeven

    def test_underwater_orphan_does_not_move_sl(self, mt5):
        """If adopted orphan is underwater, original SL stays."""
        engine = self._j46_j49_engine(mt5)
        entry = 215.20
        sl = 214.89
        mt5._positions.append(PositionInfo(
            ticket=233955223, symbol="GBPJPY", type=0, volume=7.76,
            price_open=entry, sl=sl, tp=217.06, profit=-500.0,
            magic=MAGIC_NUMBER, comment="adopted",
            time=datetime.now(timezone.utc),
        ))
        engine.symbol = "GBPJPY"
        engine.reconcile_on_startup()
        original_sl = engine.active_trade.stop_loss

        # Underwater for LONG (current < entry)
        mt5.set_tick(bid=215.05, ask=215.06)
        engine.handle_timeout_trailing()
        assert not engine.active_trade.sl_at_breakeven
        assert engine.active_trade.stop_loss == original_sl
        assert engine.active_trade is not None

    def test_short_orphan_at_low_r_does_not_move_sl(self, mt5):
        """SHORT direction: same gating applies."""
        engine = self._j46_j49_engine(mt5)
        entry = 215.20
        sl = 215.51  # SHORT SL above entry, sl_distance = 0.31
        mt5._positions.append(PositionInfo(
            ticket=233955224, symbol="GBPJPY", type=1, volume=7.76,
            price_open=entry, sl=sl, tp=213.34, profit=500.0,
            magic=MAGIC_NUMBER, comment="adopted",
            time=datetime.now(timezone.utc),
        ))
        engine.symbol = "GBPJPY"
        engine.reconcile_on_startup()
        assert engine.active_trade.direction == "SHORT"

        # +0.5R for SHORT: current = entry - 0.5 * 0.31 = 215.045
        mt5.set_tick(bid=215.04, ask=215.05)
        engine.handle_timeout_trailing()
        assert not engine.active_trade.sl_at_breakeven

    def test_legacy_path_still_fires_on_any_profit(self, mt5):
        """Regression: when J46-J49 disabled, legacy any-profit BE still works."""
        # Use the default fixture engine (no position_mgmt section).
        config = {"risk": {"risk_per_trade_pct": 1.0}}
        engine = ExecutionEngine(mt5, config)
        engine.open_trade(_trade_params(), 100000.0)
        # Tiny profit, well below 3R but legacy fires on any-profit.
        mt5.set_tick(bid=2650.50, ask=2650.65)
        engine.handle_timeout_trailing()
        assert engine.active_trade.sl_at_breakeven, (
            "Legacy (J46-J49 disabled) any-profit BE behavior must remain"
        )


class TestReconciliation:
    def test_detects_orphan_position(self, mt5, engine):
        # Add position directly to MT5 (simulating crash recovery)
        mt5._positions.append(PositionInfo(
            ticket=55555, symbol="XAUUSD", type=0, volume=0.10,
            price_open=2650.0, sl=2640.0, tp=2670.0, profit=50.0,
            magic=MAGIC_NUMBER, comment="test",
            time=datetime.now(timezone.utc),
        ))
        actions = engine.reconcile_on_startup()
        assert any("orphan_adopted" in a for a in actions)
        assert engine.active_trade is not None
        assert engine.active_trade.ticket == 55555

    def test_detects_phantom_trade(self, mt5, engine):
        engine.active_trade = TradeState(
            ticket=99999, direction="LONG", entry_price=2650.0,
            stop_loss=2640.0, take_profit_1=2670.0, take_profit_2=0,
            take_profit_3=0, initial_volume=0.10, current_volume=0.10,
            sl_distance=10.0,
        )
        actions = engine.reconcile_on_startup()
        assert any("phantom_closed" in a for a in actions)
        assert engine.active_trade is None

    def test_detects_checkpoint(self, mt5, engine):
        # Write a checkpoint file
        Path(_exec_mod.CHECKPOINT_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(_exec_mod.CHECKPOINT_PATH, "w") as f:
            json.dump({"action": "place_order", "status": "pending"}, f)
        actions = engine.reconcile_on_startup()
        assert any("checkpoint_found" in a for a in actions)
        assert not Path(_exec_mod.CHECKPOINT_PATH).exists()


class TestSLModificationFailure:
    """BUG #28 (2026-04-28): SL-modification failure must NOT close the
    position. The original SL is the safety floor — leave it in place,
    retry, alert the CEO. Closing on failure threw away an existing
    valid SL and capped the GBPJPY trade at +0.74R when it could have
    run to +6R / +$11.2k.
    """

    def test_sl_modification_failure_does_not_close_position(
        self, mt5, engine, monkeypatch, caplog
    ):
        """When _modify_sl fails on every retry, position must remain open
        with the original SL. notify_alert is called; close_position is NOT.
        """
        import logging

        engine.open_trade(_trade_params(), 100000.0)
        original_sl = engine.active_trade.stop_loss
        original_ticket = engine.active_trade.ticket

        # Make all SLTP modifications fail
        original_send = mt5.order_send

        def failing_send(request):
            if request.get("action") == TRADE_ACTION_SLTP:
                from src.mt5.mt5_interface import OrderResult
                return OrderResult(
                    retcode=10011, order=0, volume=0, price=0, comment="fail",
                )
            return original_send(request)

        mt5.order_send = failing_send

        # Speed up the retry loop for testing.
        monkeypatch.setattr(engine, "_sl_modify_backoff", lambda _idx: None)

        # Track notify_alert calls.
        alerts: list[str] = []

        def fake_notify_alert(text):
            alerts.append(text)

        import src.notifications as _notif_mod
        monkeypatch.setattr(_notif_mod, "notify_alert", fake_notify_alert)

        with caplog.at_level(logging.ERROR, logger="src.components.execution"):
            engine._move_sl_to_breakeven(
                engine.active_trade, engine.active_trade.ticket,
            )

        # CRITICAL: position must still be open, with original SL preserved.
        assert engine.active_trade is not None, \
            "Position must NOT be closed on SL-modification failure (BUG #28)"
        assert engine.active_trade.ticket == original_ticket
        assert engine.active_trade.stop_loss == original_sl, (
            f"Original SL {original_sl} must be preserved; got "
            f"{engine.active_trade.stop_loss}"
        )
        assert not engine.active_trade.sl_at_breakeven, \
            "sl_at_breakeven must NOT be set when modification failed"

        # CEO must have been alerted.
        assert len(alerts) == 1, f"Expected exactly 1 alert; got {alerts}"
        assert "[CRITICAL]" in alerts[0]
        assert "SL->BE failed" in alerts[0]
        assert str(original_ticket) in alerts[0]

        # Error log must mention "leaving existing SL" and "NOT closing".
        errs = [r.getMessage() for r in caplog.records if r.levelname == "ERROR"]
        assert any(
            "leaving existing SL" in e and "NOT closing" in e for e in errs
        ), f"Expected ERROR mentioning preserved SL; got {errs}"

    def test_sl_modification_succeeds_on_retry(
        self, mt5, engine, monkeypatch
    ):
        """Transient broker failure should be recovered by retry."""
        engine.open_trade(_trade_params(), 100000.0)
        entry = engine.active_trade.entry_price

        original_send = mt5.order_send
        attempts = {"sltp": 0}

        def flaky_send(request):
            if request.get("action") == TRADE_ACTION_SLTP:
                attempts["sltp"] += 1
                if attempts["sltp"] < 3:
                    from src.mt5.mt5_interface import OrderResult
                    return OrderResult(
                        retcode=10011, order=0, volume=0, price=0,
                        comment="transient",
                    )
            return original_send(request)

        mt5.order_send = flaky_send
        monkeypatch.setattr(engine, "_sl_modify_backoff", lambda _idx: None)

        engine._move_sl_to_breakeven(
            engine.active_trade, engine.active_trade.ticket,
        )

        assert engine.active_trade is not None
        assert engine.active_trade.sl_at_breakeven
        assert engine.active_trade.stop_loss == entry

    def test_sl_modification_succeeds_first_try(self, mt5, engine):
        """Happy path still works — no retry needed."""
        engine.open_trade(_trade_params(), 100000.0)
        entry = engine.active_trade.entry_price
        engine._move_sl_to_breakeven(
            engine.active_trade, engine.active_trade.ticket,
        )
        assert engine.active_trade is not None
        assert engine.active_trade.sl_at_breakeven
        assert engine.active_trade.stop_loss == entry


class TestVNextDynamicSLModificationFailure:
    def _trade(self, ticket: int = 700001) -> TradeState:
        return TradeState(
            ticket=ticket,
            direction="LONG",
            entry_price=100.0,
            stop_loss=99.0,
            take_profit_1=101.0,
            take_profit_2=103.0,
            take_profit_3=0.0,
            initial_volume=0.10,
            current_volume=0.10,
            sl_distance=1.0,
            gtos_vnext_dynamic_policy_applied=True,
            gtos_vnext_dynamic_policy_selected="momentum_exhaustion",
            gtos_vnext_execution_policy_id="vnext_exec_momentum_1r_pullback_04r_cap_2r",
            gtos_vnext_dynamic_be_trigger_r=1.0,
            gtos_vnext_dynamic_final_target_r=2.0,
            gtos_vnext_dynamic_momentum_pullback_r=0.4,
        )

    def test_momentum_start_records_and_alerts_failed_initial_dynamic_sl_modify(
        self, mt5, engine, monkeypatch
    ):
        trade = self._trade()
        mt5._positions.append(PositionInfo(
            ticket=trade.ticket,
            symbol="XAUUSD",
            type=0,
            volume=trade.current_volume,
            price_open=trade.entry_price,
            sl=trade.stop_loss,
            tp=trade.take_profit_2,
            profit=0.0,
            magic=MAGIC_NUMBER,
            comment="vnext",
            time=datetime.now(timezone.utc),
        ))
        monkeypatch.setattr(engine, "_sl_modify_backoff", lambda _idx: None)
        monkeypatch.setattr(_exec_mod.time, "sleep", lambda *_args, **_kwargs: None)

        original_send = mt5.order_send

        def failing_modify(request):
            if request.get("action") == TRADE_ACTION_SLTP:
                return OrderResult(
                    retcode=10011,
                    order=trade.ticket,
                    volume=0,
                    price=0,
                    comment="freeze level reject",
                )
            return original_send(request)

        mt5.order_send = failing_modify
        alerts: list[str] = []

        import src.notifications as _notif_mod

        monkeypatch.setattr(_notif_mod, "notify_alert", alerts.append)

        action = engine._start_vnext_momentum_exhaustion(trade)

        assert action == "tp1_momentum_exhaustion_started_sl_modify_failed"
        assert trade.tp1_hit
        assert not trade.sl_at_breakeven
        assert trade.stop_loss == 99.0
        assert alerts and "vNext dynamic SL modify failed" in alerts[0]
        failed_events = [
            event
            for event in trade.partial_close_events
            if event.get("type") == "VNEXT_DYNAMIC_SL_MODIFY_FAILED"
        ]
        assert failed_events
        assert failed_events[-1]["actual_stop_loss_preserved"] == 99.0
        started_events = [
            event
            for event in trade.partial_close_events
            if event.get("type") == "TP1_MOMENTUM_EXHAUSTION_STARTED"
        ]
        assert started_events[-1]["initial_sl_modify_success"] is False
        assert started_events[-1]["residual_risk_status"] == (
            "initial_dynamic_sl_modify_failed_original_sl_preserved"
        )

    def test_sltp_modify_uses_real_mt5_trade_action_sltp(self, mt5, engine):
        trade = self._trade()
        mt5._positions.append(PositionInfo(
            ticket=trade.ticket,
            symbol="XAUUSD",
            type=0,
            volume=trade.current_volume,
            price_open=trade.entry_price,
            sl=trade.stop_loss,
            tp=trade.take_profit_2,
            profit=0.0,
            magic=MAGIC_NUMBER,
            comment="vnext",
            time=datetime.now(timezone.utc),
        ))
        captured: list[dict] = []
        original_send = mt5.order_send

        def capture_send(request):
            captured.append(dict(request))
            return original_send(request)

        mt5.order_send = capture_send

        assert engine._modify_sl(
            trade.ticket,
            trade.entry_price,
            trade=trade,
            modify_reason="unit_sltp_constant",
        )
        assert captured
        assert captured[-1]["action"] == TRADE_ACTION_SLTP

    def test_hydrate_vnext_dynamic_policy_reads_execution_block(self, engine):
        trade = TradeState(
            ticket=700001,
            direction="SHORT",
            entry_price=100.0,
            stop_loss=101.0,
            take_profit_1=99.0,
            take_profit_2=97.0,
            take_profit_3=0.0,
            initial_volume=0.10,
            current_volume=0.10,
            sl_distance=1.0,
        )
        engine.active_trade = trade
        record = {
            "instrumentation": {},
            "execution": {
                "gtos_vnext_dynamic_policy_selected": "partial_be_runner",
                "gtos_vnext_execution_policy_id": (
                    "vnext_exec_partial_50_at_1r_be_runner_to_3r"
                ),
                "gtos_vnext_dynamic_policy_applied": True,
                "gtos_vnext_dynamic_policy_replaced_policy": "static_fixed_target",
                "gtos_vnext_dynamic_policy_candidate_action": (
                    "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE"
                ),
                "gtos_vnext_dynamic_policy_decision_status": "vnext_candidate_ready",
                "gtos_vnext_dynamic_policy_source_quality_action": (
                    "SOURCE_OK_FOR_DEFAULT_OFF_REPLAY"
                ),
                "gtos_vnext_dynamic_policy_exit_management_action": (
                    "ROUTE_EXIT_POLICY_BY_PROMOTED_MOMENTUM_PRIMARY_EXCEPTION_LAYER"
                ),
                "gtos_vnext_dynamic_policy_prop_action": (
                    "ALLOW_UNLESS_EXTERNAL_PROP_GOVERNOR_BLOCKS"
                ),
                "gtos_vnext_dynamic_policy_fixed_target_role": (
                    "baseline_comparator_only"
                ),
                "gtos_vnext_dynamic_be_trigger_r": 1.0,
                "gtos_vnext_dynamic_final_target_r": 3.0,
                "gtos_vnext_dynamic_time_stop_bars": 32,
            },
        }

        assert engine.hydrate_vnext_dynamic_policy_from_record(
            record,
            modify_broker_tp=False,
        )
        assert trade.gtos_vnext_dynamic_policy_selected == "partial_be_runner"
        assert trade.gtos_vnext_dynamic_policy_applied is True
        assert trade.gtos_vnext_execution_policy_id == (
            "vnext_exec_partial_50_at_1r_be_runner_to_3r"
        )
        assert trade.gtos_vnext_dynamic_be_trigger_r == pytest.approx(1.0)
        assert trade.gtos_vnext_dynamic_final_target_r == pytest.approx(3.0)
        assert trade.take_profit_1 == pytest.approx(99.0)
        assert trade.take_profit_2 == pytest.approx(97.0)

    def test_recovered_partial_be_runner_repairs_sltp_without_new_partial(
        self, mt5, engine, monkeypatch
    ):
        trade = TradeState(
            ticket=700002,
            direction="LONG",
            entry_price=100.0,
            stop_loss=99.0,
            take_profit_1=101.0,
            take_profit_2=102.0,
            take_profit_3=0.0,
            initial_volume=0.05,
            current_volume=0.05,
            sl_distance=1.0,
        )
        engine.active_trade = trade
        mt5._positions.append(PositionInfo(
            ticket=trade.ticket,
            symbol="XAUUSD",
            type=0,
            volume=trade.current_volume,
            price_open=trade.entry_price,
            sl=99.0,
            tp=102.0,
            profit=0.0,
            magic=MAGIC_NUMBER,
            comment="TP1_vnext_partia",
            time=datetime.now(timezone.utc),
        ))
        monkeypatch.setattr(engine, "_sl_modify_backoff", lambda _idx: None)
        monkeypatch.setattr(_exec_mod.time, "sleep", lambda *_args, **_kwargs: None)
        record = {
            "instrumentation": {
                "gtos_vnext_dynamic_policy_selected": "partial_be_runner",
                "gtos_vnext_execution_policy_id": (
                    "vnext_exec_partial_50_at_1r_be_runner_to_3r"
                ),
                "gtos_vnext_dynamic_policy_applied": True,
                "gtos_vnext_dynamic_be_trigger_r": 1.0,
                "gtos_vnext_dynamic_final_target_r": 3.0,
                "gtos_vnext_recovered_partial_closed": True,
                "gtos_vnext_recovered_residual_open": True,
            }
        }

        assert engine.hydrate_vnext_dynamic_policy_from_record(
            record,
            modify_broker_tp=False,
            repair_recovered_sltp=True,
        )

        position = mt5.get_positions("XAUUSD")[0]
        assert trade.tp1_hit is True
        assert trade.sl_at_breakeven is True
        assert position.sl == trade.entry_price
        assert position.tp == trade.take_profit_2
        partial_events = [
            event for event in trade.partial_close_events
            if "TP1_PARTIAL" in event.get("type", "")
        ]
        assert partial_events == []

    def test_recovered_partial_be_runner_restores_source_geometry_and_partial_event(
        self, mt5, engine
    ):
        trade = TradeState(
            ticket=700003,
            direction="SHORT",
            entry_price=72300.0,
            stop_loss=72300.0,
            take_profit_1=70778.0,
            take_profit_2=0.0,
            take_profit_3=0.0,
            initial_volume=0.25,
            current_volume=0.25,
            sl_distance=0.0,
            trade_id="adopted_700003",
        )
        engine.active_trade = trade
        mt5._positions.append(PositionInfo(
            ticket=trade.ticket,
            symbol="XAUUSD",
            type=1,
            volume=0.25,
            price_open=72306.74,
            sl=72300.67,
            tp=70778.26,
            profit=0.0,
            magic=MAGIC_NUMBER,
            comment="TP1_vnext_partia",
            time=datetime.now(timezone.utc),
        ))
        record = {
            "execution": {
                "executed_entry_price": 72306.74,
                "stop_loss": 72808.13535714285,
                "sl_distance": 501.39535714284284,
                "initial_volume": 0.5,
                "fill_time_utc": "2026-06-01T12:01:32+00:00",
                "cash_risk_amount": 251.991575,
                "risk_pct": 0.25,
            },
            "instrumentation": {
                "gtos_vnext_dynamic_policy_selected": "partial_be_runner",
                "gtos_vnext_execution_policy_id": (
                    "vnext_exec_partial_50_at_1r_be_runner_to_3r"
                ),
                "gtos_vnext_dynamic_policy_applied": True,
                "gtos_vnext_dynamic_be_trigger_r": 1.0,
                "gtos_vnext_dynamic_final_target_r": 3.0,
                "gtos_vnext_recovered_partial_closed": True,
                "gtos_vnext_recovered_residual_open": True,
                "gtos_vnext_recovered_partial_close_events": [
                    {
                        "type": "TP1_PARTIAL_RECOVERED_FROM_SLIPPAGE_LOG",
                        "time": "2026-06-01T13:27:25+00:00",
                        "price": 71774.21,
                        "volume_closed": 0.25,
                        "close_reason": "tp1_partial_vnext_partial_be_runner",
                        "mt5_order_id": 242242253,
                        "initial_volume": 0.5,
                        "remaining_volume": 0.25,
                        "sl_distance": 501.39535714284284,
                    }
                ],
            },
        }

        assert engine.hydrate_vnext_dynamic_policy_from_record(
            record,
            modify_broker_tp=False,
            repair_recovered_sltp=False,
        )

        assert trade.entry_price == pytest.approx(72306.74)
        assert trade.sl_distance == pytest.approx(501.39535714284284)
        assert trade.initial_volume == pytest.approx(0.5)
        assert trade.current_volume == pytest.approx(0.25)
        assert trade.cash_risk_amount == pytest.approx(251.991575)
        assert trade.risk_pct_at_entry == pytest.approx(0.25)
        assert trade.entry_time == "2026-06-01T12:01:32+00:00"
        recovered_partials = [
            event for event in trade.partial_close_events
            if event.get("type") == "TP1_PARTIAL_RECOVERED_FROM_SLIPPAGE_LOG"
        ]
        assert len(recovered_partials) == 1
        assert recovered_partials[0]["price"] == pytest.approx(71774.21)
        assert recovered_partials[0]["volume_closed"] == pytest.approx(0.25)

    def test_recovered_partial_geometry_ignores_breakeven_stop_as_risk_denominator(
        self, mt5, engine
    ):
        trade = TradeState(
            ticket=700004,
            direction="SHORT",
            entry_price=76.02,
            stop_loss=76.02,
            take_profit_1=75.463,
            take_profit_2=0.0,
            take_profit_3=0.0,
            initial_volume=0.04,
            current_volume=0.04,
            sl_distance=0.0,
            trade_id="adopted_700004",
        )
        engine.active_trade = trade
        record = {
            "limit_intent": {
                "trade_id": "lim_XAGUSD_2026-06-02_131507",
                "stop_loss": 76.593,
            },
            "execution": {
                "executed_entry_price": 76.02,
                "stop_loss": 76.02,
                "sl_distance": 0.00000000000003,
                "initial_volume": 0.08,
            },
            "instrumentation": {
                "gtos_vnext_dynamic_policy_selected": "partial_be_runner",
                "gtos_vnext_execution_policy_id": (
                    "vnext_exec_partial_50_at_1r_be_runner_to_3r"
                ),
                "gtos_vnext_dynamic_policy_applied": True,
                "gtos_vnext_dynamic_be_trigger_r": 1.0,
                "gtos_vnext_dynamic_final_target_r": 3.0,
                "gtos_vnext_recovered_partial_closed": True,
                "gtos_vnext_recovered_partial_close_events": [
                    {
                        "type": "TP1_PARTIAL_RECOVERED_FROM_SLIPPAGE_LOG",
                        "time": "2026-06-02T14:22:11+00:00",
                        "price": 75.343,
                        "volume_closed": 0.04,
                        "initial_volume": 0.08,
                        "remaining_volume": 0.04,
                        "sl_distance": 0.573,
                    }
                ],
            },
        }

        assert engine.hydrate_vnext_dynamic_policy_from_record(
            record,
            modify_broker_tp=False,
            repair_recovered_sltp=False,
        )

        assert trade.sl_distance == pytest.approx(0.573)
        assert trade.take_profit_1 == pytest.approx(75.447)
        assert trade.take_profit_2 == pytest.approx(74.301)

    def test_recovered_partial_tp_repair_skips_target_not_beyond_entry(
        self, mt5, engine
    ):
        trade = TradeState(
            ticket=700005,
            direction="SHORT",
            entry_price=76.02,
            stop_loss=76.02,
            take_profit_1=76.02,
            take_profit_2=76.02,
            take_profit_3=0.0,
            initial_volume=0.04,
            current_volume=0.04,
            sl_distance=0.00000000000003,
            trade_id="adopted_700005",
        )
        trade.gtos_vnext_dynamic_policy_selected = "partial_be_runner"
        trade.gtos_vnext_dynamic_policy_applied = True
        trade.sl_at_breakeven = True
        engine.active_trade = trade
        mt5._positions.append(PositionInfo(
            ticket=trade.ticket,
            symbol="XAUUSD",
            type=1,
            volume=trade.current_volume,
            price_open=trade.entry_price,
            sl=trade.entry_price,
            tp=74.301,
            profit=0.0,
            magic=MAGIC_NUMBER,
            comment="TP1_vnext_partia",
            time=datetime.now(timezone.utc),
        ))

        engine._repair_recovered_partial_be_runner_sltp(trade)

        assert mt5._order_log == []
        assert any(
            event.get("type") == "VNEXT_RECOVERED_PARTIAL_TP_REPAIR_SKIPPED"
            for event in trade.partial_close_events
        )


class TestCloseNotification:
    """BUG #31: close_position must fire notify_trade_closed exactly once
    per trade_id. Today's GBPJPY close fired silently because no path
    notified, leaving the operator with no Telegram visibility into the
    close. Edge cases: orchestrator restarted mid-close; J48 time-stop
    closed natively in execution.py; safety-handler force-close (now
    blocked by BUG #28 fix but covered defensively). Dedup ensures we
    don't double-fire when orchestrator's exit-detection path also runs.
    """

    def _close_via_engine(self, engine, mt5, trade_id="TEST-001"):
        """Open + record + close path. Returns the captured close_price."""
        engine.open_trade(_trade_params(), 100000.0)
        engine.active_trade.trade_id = trade_id
        # Pre-populate the entry_time so hold_minutes computes cleanly.
        if not engine.active_trade.entry_time:
            engine.active_trade.entry_time = datetime.now(timezone.utc).isoformat()
        ticket = engine.active_trade.ticket
        engine.close_position("manual_test")
        return ticket

    def test_close_position_fires_notify_trade_closed_once(
        self, mt5, engine, monkeypatch,
    ):
        """Happy path: close_position fires notify_trade_closed exactly once
        with the right symbol + result + entry/exit + R-progress."""
        captured: list[dict] = []

        def _stub(**kwargs):
            captured.append(kwargs)

        # Module-ref monkeypatch on src.notifications (canonical pattern).
        import src.notifications as _notif_mod
        monkeypatch.setattr(_notif_mod, "notify_trade_closed", _stub)

        self._close_via_engine(engine, mt5, trade_id="GBPJPY-2026-04-28-001")

        assert len(captured) == 1, "expected exactly 1 notify_trade_closed call"
        call = captured[0]
        assert call["result"] == "manual_test"
        assert call["trade_id"] == "GBPJPY-2026-04-28-001"
        assert call["entry_price"] > 0
        assert call["exit_price"] > 0
        # actual_r should be a finite float (sign depends on close direction)
        assert isinstance(call["actual_r"], (int, float))

    def test_dedup_prevents_double_fire_for_same_trade_id(
        self, mt5, engine, monkeypatch,
    ):
        """If close_position is somehow called twice for the same trade_id
        (e.g., orphan-recovery + safety-handler in legacy paths), only the
        FIRST call fires the notification. Idempotency guard."""
        captured: list[dict] = []
        import src.notifications as _notif_mod
        monkeypatch.setattr(
            _notif_mod, "notify_trade_closed", lambda **k: captured.append(k),
        )

        # First close
        self._close_via_engine(engine, mt5, trade_id="DEDUP-TEST")
        assert len(captured) == 1

        # Manually trigger _notify_close_if_unsent again with the same id —
        # simulating a duplicate close path. Use a temp TradeState that
        # has the same trade_id.
        ghost = TradeState(
            ticket=999, direction="LONG", entry_price=2650.0,
            stop_loss=2640.0, take_profit_1=2670.0, take_profit_2=2680.0,
            take_profit_3=2690.0, initial_volume=0.1, current_volume=0.0,
            sl_distance=10.0, trade_id="DEDUP-TEST",
            entry_time=datetime.now(timezone.utc).isoformat(),
        )
        engine._notify_close_if_unsent(ghost, "secondary_close", 2660.0)
        assert len(captured) == 1, "second call must NOT re-fire (dedup)"

    def test_no_trade_id_skips_notification(self, mt5, engine, monkeypatch):
        """Missing trade_id → no notification (we have no key to dedup on)."""
        captured: list[dict] = []
        import src.notifications as _notif_mod
        monkeypatch.setattr(
            _notif_mod, "notify_trade_closed", lambda **k: captured.append(k),
        )

        engine.open_trade(_trade_params(), 100000.0)
        engine.active_trade.trade_id = ""   # explicit empty
        engine.close_position("no_id_test")
        assert len(captured) == 0

    def test_notification_failure_does_not_break_close(
        self, mt5, engine, monkeypatch,
    ):
        """Notification dispatch error must NOT bubble out of close_position
        (the close itself must always succeed; notification is best-effort)."""
        def _broken_notify(**kwargs):
            raise RuntimeError("simulated Telegram outage")

        import src.notifications as _notif_mod
        monkeypatch.setattr(_notif_mod, "notify_trade_closed", _broken_notify)

        engine.open_trade(_trade_params(), 100000.0)
        engine.active_trade.trade_id = "FAIL-TEST"
        # Must NOT raise.
        result = engine.close_position("notify_fails")
        assert result is True
        # active_trade still cleared cleanly
        assert engine.active_trade is None

    def test_actual_r_correct_sign_for_long_winner(
        self, mt5, engine, monkeypatch,
    ):
        """LONG closing above entry → positive R; LONG below entry → negative R."""
        captured: list[dict] = []
        import src.notifications as _notif_mod
        monkeypatch.setattr(
            _notif_mod, "notify_trade_closed", lambda **k: captured.append(k),
        )

        # Construct a trade state directly to control entry/sl_distance/close.
        winner = TradeState(
            ticket=1234, direction="LONG", entry_price=100.0,
            stop_loss=98.0, take_profit_1=104.0, take_profit_2=106.0,
            take_profit_3=110.0, initial_volume=1.0, current_volume=1.0,
            sl_distance=2.0, trade_id="WINNER-LONG",
            entry_time=datetime.now(timezone.utc).isoformat(),
        )
        engine._notify_close_if_unsent(winner, "tp_hit", 103.0)  # +1.5R win
        assert len(captured) == 1
        assert captured[0]["actual_r"] == pytest.approx(1.5, rel=1e-6)

    def test_actual_r_correct_sign_for_short_loser(
        self, mt5, engine, monkeypatch,
    ):
        """SHORT closing above entry → negative R."""
        captured: list[dict] = []
        import src.notifications as _notif_mod
        monkeypatch.setattr(
            _notif_mod, "notify_trade_closed", lambda **k: captured.append(k),
        )
        loser = TradeState(
            ticket=1235, direction="SHORT", entry_price=100.0,
            stop_loss=102.0, take_profit_1=96.0, take_profit_2=94.0,
            take_profit_3=90.0, initial_volume=1.0, current_volume=1.0,
            sl_distance=2.0, trade_id="LOSER-SHORT",
            entry_time=datetime.now(timezone.utc).isoformat(),
        )
        engine._notify_close_if_unsent(loser, "sl_hit", 102.0)  # -1R loss
        assert len(captured) == 1
        assert captured[0]["actual_r"] == pytest.approx(-1.0, rel=1e-6)
