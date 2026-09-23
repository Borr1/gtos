"""J46-J49 v2 policy tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.components import execution as _exec_mod
from src.components import j46_j49_policy
from src.components.execution import ExecutionEngine, TradeState
from src.mt5.mt5_mock import MockMT5


def _on_config():
    return {
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
    }


def _off_config():
    return {
        "risk": {"risk_per_trade_pct": 1.0},
        "position_mgmt": {"j46_j49_v2": {"enabled": False}},
    }


def _trade_params(direction="LONG", entry=2650.0, sl=2640.0, tp1=2665.0,
                  tp2=2680.0, tp3=2690.0, rr=1.5):
    return {
        "direction": direction, "entry_price": entry, "stop_loss": sl,
        "take_profit_1": tp1, "take_profit_2": tp2, "take_profit_3": tp3,
        "risk_reward_ratio": rr,
    }


def _dynamic_be_context():
    return {
        "gtos_vnext_dynamic_policy_selected": "be_after_trigger",
        "gtos_vnext_dynamic_policy_applied": True,
        "gtos_vnext_dynamic_policy_replaced_policy": "retired_static_baseline_comparator",
        "gtos_vnext_dynamic_policy_candidate_action": (
            "TRADE_VNEXT_PRIMARY_CANDIDATE"
        ),
        "gtos_vnext_dynamic_policy_decision_status": "vnext_candidate_ready",
        "gtos_vnext_dynamic_policy_source_quality_action": (
            "SOURCE_OK_FOR_DEFAULT_OFF_REPLAY"
        ),
        "gtos_vnext_dynamic_policy_exit_management_action": (
            "REPLACE_RETIRED_STATIC_BASELINE_WITH_BE_AFTER_TRIGGER_DEFAULT_OFF"
        ),
        "gtos_vnext_dynamic_policy_prop_action": (
            "ALLOW_UNLESS_EXTERNAL_PROP_GOVERNOR_BLOCKS"
        ),
        "gtos_vnext_dynamic_policy_fixed_target_role": "baseline_comparator_only",
        "gtos_vnext_dynamic_be_trigger_r": 1.0,
        "gtos_vnext_dynamic_final_target_r": 1.5,
        "gtos_vnext_dynamic_time_stop_bars": None,
    }


@pytest.fixture
def mt5():
    m = MockMT5(balance=100000.0)
    m.connect()
    return m


@pytest.fixture(autouse=True)
def _isolate_checkpoint(tmp_path, monkeypatch):
    checkpoint_file = tmp_path / "execution_checkpoint.json"
    monkeypatch.setattr(_exec_mod, "CHECKPOINT_PATH", str(checkpoint_file))
    monkeypatch.setattr(_exec_mod, "PENDING_INTENT_DIR", str(tmp_path))
    yield


def test_targets_computed_correctly():
    cfg = _on_config()
    long_tp1, long_tp2 = j46_j49_policy.compute_targets(
        entry=2650.0, sl_distance=10.0, direction="LONG", config=cfg,
    )
    assert long_tp1 == pytest.approx(2680.0)
    assert long_tp2 == pytest.approx(2710.0)

    short_tp1, short_tp2 = j46_j49_policy.compute_targets(
        entry=2650.0, sl_distance=10.0, direction="SHORT", config=cfg,
    )
    assert short_tp1 == pytest.approx(2620.0)
    assert short_tp2 == pytest.approx(2590.0)


def test_open_trade_overrides_broker_tp_to_6r(mt5):
    engine = ExecutionEngine(mt5, _on_config())
    state = engine.open_trade(_trade_params(), 100000.0)
    assert state is not None
    # Inspect the order_send log: last DEAL request must carry tp = 6R target
    deal_requests = [r for r in mt5._order_log if r.get("action") == 1
                     and "position" not in r]
    assert len(deal_requests) >= 1
    deal = deal_requests[0]
    sl = deal["sl"]
    entry_for_request = deal["price"]
    expected_tp_6r = entry_for_request + 6.0 * abs(entry_for_request - sl)
    assert deal["tp"] == pytest.approx(expected_tp_6r, abs=1e-6)


def test_moonshot_dynamic_policy_replaces_j46_j49_broker_tp_override(mt5):
    engine = ExecutionEngine(mt5, _on_config())
    params = _trade_params(tp1=2665.0)
    params.update(_dynamic_be_context())

    state = engine.open_trade(params, 100000.0)

    assert state is not None
    deal_requests = [r for r in mt5._order_log if r.get("action") == 1
                     and "position" not in r]
    deal = deal_requests[0]
    expected_trigger = deal["price"] + abs(deal["price"] - deal["sl"])
    expected_final = deal["price"] + 1.5 * abs(deal["price"] - deal["sl"])
    assert deal["tp"] == pytest.approx(expected_final, abs=1e-6)
    assert state.j46_j49_active is False
    assert state.take_profit_1 == pytest.approx(expected_trigger, abs=1e-6)
    assert state.take_profit_2 == pytest.approx(expected_final, abs=1e-6)
    assert state.gtos_vnext_dynamic_be_after_trigger_active is True
    assert state.gtos_vnext_dynamic_be_trigger_r == pytest.approx(1.0)
    assert state.gtos_vnext_dynamic_final_target_r == pytest.approx(1.5)
    assert state.gtos_vnext_dynamic_policy_selected == "be_after_trigger"
    assert state.gtos_vnext_dynamic_policy_applied is True
    assert state.gtos_vnext_dynamic_policy_replaced_policy == "retired_static_baseline_comparator"


def test_moonshot_dynamic_be_after_trigger_moves_sl_without_closing_long(mt5):
    engine = ExecutionEngine(mt5, _on_config())
    params = _trade_params()
    params.update(_dynamic_be_context())
    state = engine.open_trade(params, 100000.0)
    assert state is not None
    initial_volume = state.current_volume

    mt5.set_tick(bid=state.take_profit_1, ask=state.take_profit_1 + 0.18)
    action = engine.check_and_manage_trade({})

    assert action == "tp1_be_only_vnext_moonshot"
    assert engine.active_trade is not None
    assert engine.active_trade.tp1_hit is True
    assert engine.active_trade.current_volume == pytest.approx(initial_volume)
    assert engine.active_trade.sl_at_breakeven is True
    assert engine.active_trade.stop_loss == pytest.approx(state.entry_price)
    close_requests = [
        r for r in mt5._order_log if r.get("action") == 1 and "position" in r
    ]
    assert close_requests == []


def test_moonshot_dynamic_be_after_trigger_final_target_closes_long(mt5):
    engine = ExecutionEngine(mt5, _on_config())
    params = _trade_params()
    params.update(_dynamic_be_context())
    state = engine.open_trade(params, 100000.0)
    assert state is not None

    mt5.set_tick(bid=state.take_profit_1, ask=state.take_profit_1 + 0.18)
    engine.check_and_manage_trade({})
    assert engine.active_trade is not None

    mt5.set_tick(
        bid=engine.active_trade.take_profit_2,
        ask=engine.active_trade.take_profit_2 + 0.18,
    )
    action = engine.check_and_manage_trade({})

    assert action == "tp2_final_target_vnext_be_after_trigger"
    assert engine.active_trade is None
    close_requests = [
        r for r in mt5._order_log if r.get("action") == 1 and "position" in r
    ]
    assert close_requests[-1]["comment"] == "TP2_vnext_be_final"


def test_moonshot_dynamic_be_after_trigger_short_management(mt5):
    engine = ExecutionEngine(mt5, _on_config())
    params = _trade_params(direction="SHORT", sl=2660.0, tp1=2635.0)
    params.update(_dynamic_be_context())
    state = engine.open_trade(params, 100000.0)
    assert state is not None
    assert state.take_profit_1 == pytest.approx(
        state.entry_price - state.sl_distance,
        abs=1e-6,
    )
    assert state.take_profit_2 == pytest.approx(
        state.entry_price - 1.5 * state.sl_distance,
        abs=1e-6,
    )

    mt5.set_tick(bid=state.take_profit_1 - 0.18, ask=state.take_profit_1)
    assert engine.check_and_manage_trade({}) == "tp1_be_only_vnext_moonshot"
    assert engine.active_trade is not None
    assert engine.active_trade.sl_at_breakeven is True

    mt5.set_tick(
        bid=engine.active_trade.take_profit_2 - 0.18,
        ask=engine.active_trade.take_profit_2,
    )
    assert (
        engine.check_and_manage_trade({})
        == "tp2_final_target_vnext_be_after_trigger"
    )
    assert engine.active_trade is None


def test_moonshot_dynamic_policy_hydration_can_skip_broker_tp_modify(mt5):
    engine = ExecutionEngine(mt5, _on_config())
    state = engine.open_trade(_trade_params(), 100000.0)
    assert state is not None
    engine.active_trade = TradeState(
        ticket=state.ticket,
        direction=state.direction,
        entry_price=state.entry_price,
        stop_loss=state.stop_loss,
        take_profit_1=state.take_profit_1,
        take_profit_2=0.0,
        take_profit_3=0.0,
        initial_volume=state.initial_volume,
        current_volume=state.current_volume,
        sl_distance=state.sl_distance,
        position_confirmed=True,
    )

    before_modify_count = len([r for r in mt5._order_log if r.get("action") == 2])
    record = {"instrumentation": _dynamic_be_context()}
    assert engine.hydrate_vnext_dynamic_policy_from_record(
        record,
        modify_broker_tp=False,
    ) is True

    after_modify_count = len([r for r in mt5._order_log if r.get("action") == 2])
    assert after_modify_count == before_modify_count
    assert engine.active_trade.gtos_vnext_dynamic_be_after_trigger_active is True


def test_moonshot_dynamic_be_after_trigger_pending_fill_uses_live_management(mt5):
    engine = ExecutionEngine(mt5, _on_config())
    params = _trade_params(entry=2650.0, sl=2640.0, tp1=2665.0)
    engine.set_limit_intent(
        params,
        account_balance=100000.0,
        telemetry_context=_dynamic_be_context(),
    )

    state = engine.check_limit_fill({
        "time": "2026-05-26T13:00:00+00:00",
        "open": 2651.0,
        "high": 2652.0,
        "low": 2649.0,
        "close": 2651.5,
    })

    assert state is not None
    assert engine.pending_intent is None
    assert state.gtos_vnext_dynamic_be_after_trigger_active is True
    assert state.take_profit_1 == pytest.approx(
        state.entry_price + state.sl_distance,
        abs=1e-6,
    )
    assert state.take_profit_2 == pytest.approx(
        state.entry_price + 1.5 * state.sl_distance,
        abs=1e-6,
    )


def test_open_trade_preserves_ai_tp1(mt5):
    engine = ExecutionEngine(mt5, _on_config())
    state = engine.open_trade(_trade_params(tp1=2665.0), 100000.0)
    assert state is not None
    assert state.original_ai_tp1 == pytest.approx(2665.0)
    # When enabled, take_profit_1 is the software-tracked 3R target.
    # entry_price is filled_price; sl_distance is computed from pre-fill tick.
    # Targets were computed pre-fill against tick.ask (entry tick), so the
    # invariant we can assert against TradeState is "tp1 equals 3R from
    # the broker-known entry tick", which we capture from the order log.
    deal_requests = [r for r in mt5._order_log if r.get("action") == 1
                     and "position" not in r]
    deal = deal_requests[0]
    pre_fill_entry = deal["price"]
    pre_fill_sl_dist = abs(pre_fill_entry - deal["sl"])
    expected_tp1_3r = pre_fill_entry + 3.0 * pre_fill_sl_dist
    expected_tp2_6r = pre_fill_entry + 6.0 * pre_fill_sl_dist
    assert state.take_profit_1 == pytest.approx(expected_tp1_3r, abs=1e-6)
    assert state.take_profit_2 == pytest.approx(expected_tp2_6r, abs=1e-6)
    assert state.take_profit_3 == pytest.approx(0.0)


def test_tp1_hit_triggers_be_only_no_close(mt5):
    engine = ExecutionEngine(mt5, _on_config())
    state = engine.open_trade(_trade_params(), 100000.0)
    assert state is not None
    initial_volume = state.current_volume

    # Push price to the software-tracked TP1 (3R level)
    tp1_3r = state.take_profit_1
    mt5.set_tick(bid=tp1_3r, ask=tp1_3r + 0.18)
    action = engine.check_and_manage_trade({})

    assert action == "tp1_be_only_j46_j49"
    assert engine.active_trade is not None
    assert engine.active_trade.tp1_hit is True
    assert engine.active_trade.current_volume == pytest.approx(initial_volume)
    assert engine.active_trade.sl_at_breakeven is True
    assert engine.active_trade.stop_loss == pytest.approx(state.entry_price)


def test_tp2_hit_triggers_full_close(mt5):
    engine = ExecutionEngine(mt5, _on_config())
    state = engine.open_trade(_trade_params(), 100000.0)
    assert state is not None

    # First, hit TP1 (3R) to set tp1_hit
    tp1_3r = state.take_profit_1
    mt5.set_tick(bid=tp1_3r, ask=tp1_3r + 0.18)
    engine.check_and_manage_trade({})
    assert engine.active_trade.tp1_hit is True

    # Now hit TP2 (6R)
    tp2_6r = engine.active_trade.take_profit_2
    mt5.set_tick(bid=tp2_6r, ask=tp2_6r + 0.18)
    action = engine.check_and_manage_trade({})

    assert action == "tp2_higher_target_j46_j49"
    assert engine.active_trade is None


def test_time_stop_after_12_bars_closes_at_market(mt5):
    engine = ExecutionEngine(mt5, _on_config())
    state = engine.open_trade(_trade_params(), 100000.0)
    assert state is not None

    # Backdate entry_time so 13 M15 bars (>12) have elapsed
    past = datetime.now(timezone.utc) - timedelta(minutes=13 * 15)
    engine.active_trade.entry_time = past.isoformat()

    action = engine.check_time_stop_and_close()
    assert action == "j46_j49_time_stop"
    assert engine.active_trade is None


def test_time_stop_before_12_bars_returns_none(mt5):
    engine = ExecutionEngine(mt5, _on_config())
    state = engine.open_trade(_trade_params(), 100000.0)
    assert state is not None

    past = datetime.now(timezone.utc) - timedelta(minutes=10 * 15)
    engine.active_trade.entry_time = past.isoformat()

    action = engine.check_time_stop_and_close()
    assert action is None
    assert engine.active_trade is not None


def test_time_stop_with_unparseable_entry_time_returns_none(mt5):
    engine = ExecutionEngine(mt5, _on_config())
    state = engine.open_trade(_trade_params(), 100000.0)
    assert state is not None

    engine.active_trade.entry_time = "not-a-date"
    action = engine.check_time_stop_and_close()
    assert action is None
    assert engine.active_trade is not None

    engine.active_trade.entry_time = ""
    action = engine.check_time_stop_and_close()
    assert action is None
    assert engine.active_trade is not None


def test_time_stop_disabled_returns_none(mt5):
    engine = ExecutionEngine(mt5, _off_config())
    engine.active_trade = TradeState(
        ticket=1, direction="LONG", entry_price=2650.0, stop_loss=2640.0,
        take_profit_1=2665.0, take_profit_2=0, take_profit_3=0,
        initial_volume=0.10, current_volume=0.10, sl_distance=10.0,
        entry_time=(datetime.now(timezone.utc) - timedelta(hours=10)).isoformat(),
    )
    action = engine.check_time_stop_and_close()
    assert action is None


def test_time_stop_no_active_trade_returns_none(mt5):
    engine = ExecutionEngine(mt5, _on_config())
    assert engine.active_trade is None
    action = engine.check_time_stop_and_close()
    assert action is None


def test_sl_hit_before_tp1_old_path(mt5):
    engine = ExecutionEngine(mt5, _on_config())
    state = engine.open_trade(_trade_params(), 100000.0)
    assert state is not None

    # Confirm the position once (clears the post-fill propagation race
    # guard added 2026-04-29 to prevent NAS100-class false closes).
    engine.check_and_manage_trade({})
    assert engine.active_trade.position_confirmed is True

    # Now simulate broker SL hit by clearing positions â€” true close.
    mt5._positions.clear()
    action = engine.check_and_manage_trade({})
    assert action == "broker_closed"
    assert engine.active_trade is None


def test_disabled_flag_preserves_legacy_behavior(mt5):
    engine = ExecutionEngine(mt5, _off_config())
    state = engine.open_trade(_trade_params(tp1=2665.0), 100000.0)
    assert state is not None

    # Broker TP must equal AI TP1 (legacy), not 6R
    deal_requests = [r for r in mt5._order_log if r.get("action") == 1
                     and "position" not in r]
    deal = deal_requests[0]
    assert deal["tp"] == pytest.approx(2665.0)
    # original_ai_tp1 still populated for shadow logger consumption
    assert state.original_ai_tp1 == pytest.approx(2665.0)
    assert state.take_profit_1 == pytest.approx(2665.0)


def test_bars_elapsed_since_fill():
    base = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
    assert j46_j49_policy.bars_elapsed_since_fill(
        base, base + timedelta(minutes=12 * 15),
    ) == 12
    assert j46_j49_policy.bars_elapsed_since_fill(
        base, base + timedelta(minutes=11 * 15),
    ) == 11
    assert j46_j49_policy.bars_elapsed_since_fill(
        base, base + timedelta(minutes=12 * 15 + 14),
    ) == 12
    assert j46_j49_policy.bars_elapsed_since_fill(
        base, base + timedelta(minutes=12 * 15 + 15),
    ) == 13
    # Naive entry should be coerced to UTC
    naive = datetime(2026, 4, 28, 12, 0, 0)
    assert j46_j49_policy.bars_elapsed_since_fill(
        naive, base + timedelta(minutes=180),
    ) == 12


def test_is_enabled_default_off():
    assert j46_j49_policy.is_enabled({}) is False
    assert j46_j49_policy.is_enabled({"position_mgmt": {}}) is False


def test_short_tp1_hit_triggers_be_only(mt5):
    engine = ExecutionEngine(mt5, _on_config())
    # SHORT: entry from bid=2650.0, SL above
    state = engine.open_trade(_trade_params(
        direction="SHORT", entry=2650.0, sl=2660.0, tp1=2635.0,
    ), 100000.0)
    assert state is not None
    initial_volume = state.current_volume
    tp1_3r = state.take_profit_1  # entry - 3*sl_distance
    # For SHORT, current_price must be <= tp1_3r; check_and_manage_trade
    # uses tick.ask for SHORT current_price
    mt5.set_tick(bid=tp1_3r - 0.18, ask=tp1_3r)
    action = engine.check_and_manage_trade({})
    assert action == "tp1_be_only_j46_j49"
    assert engine.active_trade.tp1_hit is True
    assert engine.active_trade.current_volume == pytest.approx(initial_volume)


def test_shadow_logger_replay_old_tp1_hit():
    from src.components.j46_j49_shadow_logger import compute_j46_j49_shadow

    entry_time = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    exit_time = entry_time + timedelta(minutes=180)

    bars = [
        {"time": entry_time + timedelta(minutes=i),
         "open": 2650.0, "high": 2666.0 if i == 30 else 2660.0,
         "low": 2649.0, "close": 2660.0}
        for i in range(0, 60, 1)
    ]

    def fetcher(d_from, d_to):
        return bars

    row = compute_j46_j49_shadow(
        fill_id="t1", instrument="XAUUSD", direction="LONG",
        entry_time=entry_time, exit_time=exit_time,
        entry_price=2650.0, original_sl=2640.0, original_ai_tp1=2665.0,
        sl_distance=10.0,
        actual_exit_price=2680.0, actual_exit_time=exit_time,
        actual_r=3.0, actual_exit_reason="tp2_higher_target_j46_j49",
        bar_fetcher=fetcher,
    )
    assert row["hypothetical_old"] is not None
    assert row["hypothetical_old"]["exit_reason"] == "old_tp1_hit"
    assert row["hypothetical_old"]["hypothetical_R"] == pytest.approx(1.5)
    assert row["actual_close"]["realized_R"] == pytest.approx(3.0)
    assert row["delta_r"] == pytest.approx(1.5)
    assert row["shadow_better"] is True


def test_shadow_logger_replay_old_sl_hit_adverse_first():
    from src.components.j46_j49_shadow_logger import compute_j46_j49_shadow

    entry_time = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    exit_time = entry_time + timedelta(minutes=60)

    bars = [
        {"time": entry_time + timedelta(minutes=i),
         "open": 2650.0,
         "high": 2666.0 if i == 5 else 2655.0,
         "low": 2639.0 if i == 5 else 2649.0,
         "close": 2645.0}
        for i in range(0, 60)
    ]

    def fetcher(d_from, d_to):
        return bars

    row = compute_j46_j49_shadow(
        fill_id="t2", instrument="XAUUSD", direction="LONG",
        entry_time=entry_time, exit_time=exit_time,
        entry_price=2650.0, original_sl=2640.0, original_ai_tp1=2665.0,
        sl_distance=10.0,
        actual_exit_price=2640.0, actual_exit_time=exit_time,
        actual_r=-1.0, actual_exit_reason="broker_closed",
        bar_fetcher=fetcher,
    )
    assert row["hypothetical_old"]["exit_reason"] == "old_sl_hit"
    assert row["hypothetical_old"]["hypothetical_R"] == pytest.approx(-1.0)


def test_shadow_logger_never_raises_on_fetch_failure():
    from src.components.j46_j49_shadow_logger import compute_j46_j49_shadow

    def bad_fetcher(d_from, d_to):
        raise RuntimeError("boom")

    entry_time = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    exit_time = entry_time + timedelta(minutes=60)

    row = compute_j46_j49_shadow(
        fill_id="t3", instrument="XAUUSD", direction="LONG",
        entry_time=entry_time, exit_time=exit_time,
        entry_price=2650.0, original_sl=2640.0, original_ai_tp1=2665.0,
        sl_distance=10.0,
        actual_exit_price=2680.0, actual_exit_time=exit_time,
        actual_r=3.0, actual_exit_reason="tp2_higher_target_j46_j49",
        bar_fetcher=bad_fetcher,
    )
    assert row["hypothetical_old"] is None
    assert "error" in row
