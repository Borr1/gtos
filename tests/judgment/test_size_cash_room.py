"""The size hop's cash stays inside the account's binding room. No orders."""

from __future__ import annotations

import src.judgment.nineteen as nineteen
import src.judgment.size_exit as size_exit
from src.judgment.apply_size import (
    CHALLENGE_LOGIN,
    CHALLENGE_NS,
    binding_room_usd,
    cash_anchor_levels,
    daily_room_read,
    floor_room_usd,
    honor_f5_scaler_risk,
)

# Live card read. Equity, day-start balance, and day-start equity are account scale.
LIVE = {
    "equity": 93522.57,
    "initial_balance": 100000.0,
    "overall_loss_pct": 10.0,
    "daily_percent_external": 5.0,
    "daily_percent_internal_overlay": 4.0,
    "day_start_equity": 93678.44,
    "day_start_balance": 93670.92,
    "positions_total": 0,
}
EQUITY_SCALE_CASH = 93678.44
LAUNCHER = 150.0


def _honor(monkeypatch, facts, cash, *, decided=True, score_returns="ceiling", target=LAUNCHER):
    posts = {"persist": 0, "score": 0, "anchors": None, "payload": None}

    def persist(state):
        posts["persist"] += 1
        posts["payload"] = dict(state)
        return {"size_decided": decided, "cash_usd": cash}

    def score(state, *, question_id, instructions, anchors=None, ask=None):
        posts["score"] += 1
        posts["anchors"] = list(anchors or [])
        assert question_id == "unit_usd"
        if score_returns is None:
            return None
        if score_returns == "ceiling":
            return max(value for _label, value in anchors)
        if score_returns == "above":
            return max(value for _label, value in anchors) + 1.0
        return score_returns

    monkeypatch.setattr(size_exit, "choose_size_and_persist", persist)
    monkeypatch.setattr(nineteen, "score", score)
    honored, stamp = honor_f5_scaler_risk(
        13729.0,
        trade_params=dict(facts),
        login=CHALLENGE_LOGIN,
        ns=CHALLENGE_NS,
        target_risk_usd=target,
    )
    return honored, stamp, posts


def test_binding_room_is_the_smaller_room_net_of_open_risk():
    floor = floor_room_usd(LIVE)
    daily, daily_read = daily_room_read(LIVE)
    room, read = binding_room_usd(LIVE)
    assert floor is not None and daily is not None and room is not None
    assert daily_read == "firm_rule"
    assert read == "bound"
    assert abs(floor - (93522.57 - 90000.0)) < 1e-6
    # The firm's daily floor is the day's higher start less 5% of the initial balance.
    assert abs(daily - (93522.57 - (93678.44 - 5000.0))) < 1e-6
    assert room == min(floor, daily)
    assert room == floor
    assert room < EQUITY_SCALE_CASH
    assert floor < LIVE["equity"]


def test_internal_overlay_is_not_an_account_rule():
    with_overlay = daily_room_read(LIVE)[0]
    without_overlay = daily_room_read({**LIVE, "daily_percent_internal_overlay": None})[0]
    assert with_overlay == without_overlay


def test_percent_facts_are_percents():
    half_percent = daily_room_read({**LIVE, "daily_percent_external": 0.5})[0]
    assert abs(half_percent - (93522.57 - (93678.44 - 500.0))) < 1e-6
    assert daily_room_read({**LIVE, "daily_percent_external": 100.0}) == (None, "unset")


def test_daily_room_needs_the_initial_balance():
    facts = {key: value for key, value in LIVE.items() if key != "initial_balance"}
    assert daily_room_read(facts) == (None, "unset")


def test_an_account_with_no_firm_uses_its_own_equity():
    personal = {"equity": 250.0, "positions_total": 0, "account_rules": "none"}
    room, read = binding_room_usd(personal)
    assert read == "own_equity"
    assert room == 250.0
    with_open = {**personal, "positions_total": 1, "open_risk_usd": 40.0}
    assert binding_room_usd(with_open) == (210.0, "own_equity")


def test_an_account_that_declares_nothing_still_needs_its_rules():
    undeclared = {"equity": 250.0, "positions_total": 0}
    assert binding_room_usd(undeclared) == (None, "unset")


def test_no_firm_still_needs_readable_open_risk():
    unreadable = {"equity": 250.0, "positions_total": 2, "account_rules": "none"}
    assert binding_room_usd(unreadable) == (None, "unset")


def test_equity_scale_cash_is_replaced_by_a_score_inside_the_room(monkeypatch):
    honored, stamp, posts = _honor(monkeypatch, LIVE, EQUITY_SCALE_CASH)
    room = stamp["binding_room_usd"]
    assert posts["persist"] == 1
    assert posts["score"] == 1
    assert set(posts["payload"]) == {
        "login",
        "namespace",
        "open_ticket",
        "launcher_f5_minimal_size_usd",
        "launcher_notional_initial_usd",
    }
    values = [item["usd"] for item in stamp["cash_anchors"]]
    assert values
    assert max(values) == room
    assert all(value <= room for value in values)
    assert EQUITY_SCALE_CASH not in values
    assert LIVE["equity"] not in values
    assert honored == room
    assert honored <= room
    assert stamp["f5_scaler_honor"] == "size_cash_anchors"
    assert stamp["open_risk_usd"] == 0.0
    assert stamp["open_risk_read"] == "flat"


def test_empty_score_leaves_the_oversized_cash_unset(monkeypatch):
    honored, stamp, posts = _honor(monkeypatch, LIVE, EQUITY_SCALE_CASH, score_returns=None)
    assert posts["score"] == 1
    assert honored is None
    assert stamp["f5_scaler_honor"] == "size_not_decided"


def test_score_above_the_room_stays_unset(monkeypatch):
    honored, _stamp, posts = _honor(monkeypatch, LIVE, EQUITY_SCALE_CASH, score_returns="above")
    assert posts["score"] == 1
    assert honored is None


def test_cash_already_inside_the_room_is_kept(monkeypatch):
    honored, stamp, posts = _honor(monkeypatch, LIVE, LAUNCHER)
    assert posts["persist"] == 1
    assert posts["score"] == 0
    assert honored == LAUNCHER
    assert stamp["f5_scaler_honor"] == "size_choice"
    assert honored <= stamp["binding_room_usd"]


def test_undecided_hop_stays_unset(monkeypatch):
    honored, stamp, posts = _honor(monkeypatch, LIVE, None, decided=False)
    assert posts["score"] == 0
    assert honored is None
    assert stamp["f5_scaler_honor"] == "size_not_decided"


def test_open_risk_shrinks_the_room(monkeypatch):
    facts = {**LIVE, "positions_total": 1, "open_risk_usd": 1000.0}
    floor = floor_room_usd(facts)
    daily, _read = daily_room_read(facts)
    room, read = binding_room_usd(facts)
    assert read == "bound"
    assert room == min(floor, daily) - 1000.0
    honored, stamp, posts = _honor(monkeypatch, facts, floor)
    assert posts["score"] == 1
    assert honored == stamp["binding_room_usd"]
    assert honored <= room
    assert floor > room


def test_unreadable_open_risk_leaves_the_cash_unset(monkeypatch):
    facts = {**LIVE, "positions_total": 1}
    honored, stamp, posts = _honor(monkeypatch, facts, LAUNCHER)
    assert posts["persist"] == 0
    assert posts["score"] == 0
    assert honored is None
    assert stamp["binding_room_read"] == "unset"
    assert stamp["open_risk_read"] == "unset"


def test_missing_daily_facts_leave_the_cash_unset(monkeypatch):
    facts = {key: value for key, value in LIVE.items() if not str(key).startswith("day_start")}
    honored, _stamp, posts = _honor(monkeypatch, facts, LAUNCHER)
    assert posts["persist"] == 0
    assert honored is None


def test_anchor_levels_exclude_account_scale():
    anchors = cash_anchor_levels(LIVE, target=LAUNCHER)
    values = [value for _label, value in anchors]
    assert LAUNCHER in values
    assert max(values) == binding_room_usd(LIVE)[0]
    assert LIVE["equity"] not in values
    assert LIVE["day_start_equity"] not in values
    assert LIVE["day_start_balance"] not in values


def test_pending_inside_open_risk_is_not_taken_twice():
    base, _read = binding_room_usd({**LIVE, "open_risk_usd": 0.0, "pending_orders_total": 0})
    facts = {
        **LIVE,
        "open_risk_usd": 50.0,
        "pending_orders_total": 1,
        "pending_stop_risk_usd": 50.0,
        "cycle_risk_usd": 100.0,
    }
    room, read = binding_room_usd(facts)
    assert base is not None and room is not None
    assert read == "bound"
    assert abs(room - (base - 150.0)) < 1e-6


def test_pending_orders_without_a_risk_leave_the_room_unset():
    facts = {**LIVE, "pending_orders_total": 2}
    room, read = binding_room_usd(facts)
    assert room is None
    assert read == "unset"


def test_a_limit_fill_carries_the_allocation_cash(monkeypatch):
    from src.components.execution import PendingLimitIntent, fill_cash_from_pending
    from src.judgment.apply_size import CASH_CARRY

    CASH_CARRY.clear()

    intent = PendingLimitIntent(
        direction="LONG",
        limit_price=100.0,
        stop_loss=99.0,
        take_profit_1=102.0,
        risk_pct=0.01,
        allocation_cash_usd=180.0,
        min_lot_risk_usd=40.0,
        allocation_sleeve="metals_core",
    )
    carried = fill_cash_from_pending(intent)
    assert carried == {
        "allocation_cash_usd": 180.0,
        "min_lot_risk_usd": 40.0,
        "sleeve": "metals_core",
    }
    honored, stamp, posts = _honor(
        monkeypatch,
        {**LIVE, **carried, "symbol": "XAUUSD", "open_risk_usd": 0.0},
        99999.0,
    )
    assert posts["persist"] == 0
    assert posts["score"] == 0
    assert honored == 180.0
    assert stamp["f5_scaler_honor"] == "allocation_cash"
    assert CASH_CARRY[-1]["allocation_cash_usd"] == 180.0
    assert CASH_CARRY[-1]["final_check"] == "inside_room"


def test_room_facts_come_from_the_size_room_read(monkeypatch):
    from src.components.execution import ExecutionEngine
    from src.judgment.apply_size import read_binding_room_facts

    def fake(self, _balance):
        assert self._runtime_namespace == "operator"
        return {"open_risk_usd": 12.0, "pending_orders_total": 1, "pending_stop_risk_usd": 12.0}

    monkeypatch.setattr(ExecutionEngine, "_size_room_facts", fake)
    facts = read_binding_room_facts(object(), {}, namespace="operator")
    assert facts["open_risk_usd"] == 12.0
    assert facts["pending_stop_risk_usd"] == 12.0


def test_carried_cash_is_not_asked_again(monkeypatch):
    honored, stamp, posts = _honor(
        monkeypatch,
        {**LIVE, "allocation_cash_usd": 200.0, "min_lot_risk_usd": 40.0, "open_risk_usd": 0.0},
        99999.0,
    )
    assert posts["persist"] == 0
    assert posts["score"] == 0
    assert honored == 200.0
    assert stamp["f5_scaler_honor"] == "allocation_cash"
    assert stamp["rounded_risk_usd"] == 200.0


def test_carried_cash_above_the_room_after_the_minimum_lot_is_refused(monkeypatch):
    room, _read = binding_room_usd({**LIVE, "open_risk_usd": 0.0})
    honored, stamp, posts = _honor(
        monkeypatch,
        {
            **LIVE,
            "allocation_cash_usd": 10.0,
            "min_lot_risk_usd": room + 50.0,
            "open_risk_usd": 0.0,
        },
        99999.0,
    )
    assert posts["persist"] == 0
    assert posts["score"] == 0
    assert honored is None
    assert stamp["f5_scaler_honor"] == "allocation_above_room"
    assert stamp["rounded_risk_usd"] == room + 50.0
