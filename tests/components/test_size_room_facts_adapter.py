"""The size room reads the account through RealMT5's own names. No orders."""

from __future__ import annotations

from types import SimpleNamespace

import src.judgment.equity_frame as equity_frame
from src.components.execution import ExecutionEngine
from src.judgment.apply_size import binding_room_usd


class _Raw:
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1

    def __init__(self, positions, profits):
        self._positions = positions
        self._profits = profits
        self.calls = []

    def positions_get(self):
        return list(self._positions)

    def order_calc_profit(self, order_type, symbol, volume, price_open, price_close):
        self.calls.append((order_type, symbol, volume, price_open, price_close))
        return self._profits[symbol]


class _Adapter:
    """Only the names RealMT5 really has. No account_info or positions_total."""

    def __init__(self, raw, equity=93522.57, balance=93522.57):
        self._mt5 = raw
        self._equity = equity
        self._balance = balance

    def get_account_equity(self):
        return self._equity

    def get_account_balance(self):
        return self._balance


def _engine(adapter):
    engine = object.__new__(ExecutionEngine)
    engine.mt5 = adapter
    engine._runtime_namespace = "operator"
    engine.config = {
        "gtos_vnext_runtime": {
            "prop_safe_selector_initial_balance": 100000.0,
            "prop_safe_selector_external_overall_max_loss_pct": 10.0,
            "prop_safe_selector_external_daily_loss_limit_pct": 5.0,
            "prop_safe_selector_internal_daily_overlay_enabled": True,
            "prop_safe_selector_internal_daily_overlay_pct": 4.0,
        }
    }
    return engine


def _day(monkeypatch):
    monkeypatch.setattr(
        equity_frame,
        "read_chair_day_start",
        lambda: {"day_start_balance": 93670.92, "day_start_equity": 93678.44},
    )


def test_flat_account_reads_equity_and_zero_open_risk(monkeypatch):
    _day(monkeypatch)
    facts = _engine(_Adapter(_Raw([], {})))._size_room_facts(93522.57)
    assert facts["equity"] == 93522.57
    assert facts["balance"] == 93522.57
    assert facts["positions_total"] == 0
    assert facts["open_risk_usd"] == 0.0
    assert "daily_percent_internal_overlay" not in facts
    room, read = binding_room_usd(facts)
    assert read == "bound"
    assert abs(room - 3522.57) < 1e-6


def test_open_stops_come_off_the_room_whatever_their_magic(monkeypatch):
    _day(monkeypatch)
    positions = [
        SimpleNamespace(symbol="XAUUSD", volume=0.1, price_open=4340.0, sl=4330.0, type=0, magic=0),
        SimpleNamespace(symbol="EURUSD", volume=0.2, price_open=1.1, sl=1.11, type=1, magic=0),
        SimpleNamespace(symbol="USDJPY", volume=0.1, price_open=157.0, sl=157.5, type=0, magic=0),
    ]
    # XAUUSD and EURUSD stops lose money; the USDJPY stop sits in profit and adds nothing.
    raw = _Raw(positions, {"XAUUSD": -100.0, "EURUSD": -200.0, "USDJPY": 30.0})
    facts = _engine(_Adapter(raw))._size_room_facts(93522.57)
    assert facts["positions_total"] == 3
    assert facts["open_risk_usd"] == 300.0
    assert len(raw.calls) == 3
    room, read = binding_room_usd(facts)
    assert read == "bound"
    assert abs(room - (3522.57 - 300.0)) < 1e-6


def test_a_position_without_a_stop_leaves_the_room_unset(monkeypatch):
    _day(monkeypatch)
    positions = [SimpleNamespace(symbol="XAUUSD", volume=0.1, price_open=4340.0, sl=0.0, type=0, magic=0)]
    facts = _engine(_Adapter(_Raw(positions, {"XAUUSD": -100.0})))._size_room_facts(93522.57)
    assert facts["positions_total"] == 1
    assert "open_risk_usd" not in facts
    assert binding_room_usd(facts) == (None, "unset")


def test_unreadable_equity_leaves_the_room_unset(monkeypatch):
    _day(monkeypatch)
    facts = _engine(_Adapter(_Raw([], {}), equity=0.0))._size_room_facts(93522.57)
    assert facts["equity"] is None
    assert binding_room_usd(facts) == (None, "unset")
