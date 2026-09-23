"""The size room reads the account through RealMT5's own names."""

from __future__ import annotations

from types import SimpleNamespace

import src.judgment.equity_frame as equity_frame
from src.components.execution import ExecutionEngine
from src.judgment.apply_size import binding_room_usd


class _Raw:
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_TYPE_BUY_LIMIT = 2
    ORDER_TYPE_SELL_LIMIT = 3
    ORDER_TYPE_BUY_STOP = 4
    ORDER_TYPE_SELL_STOP = 5
    ORDER_TYPE_BUY_STOP_LIMIT = 6
    ORDER_TYPE_SELL_STOP_LIMIT = 7

    def __init__(self, positions, profits, orders=None):
        self._positions = positions
        self._orders = [] if orders is None else orders
        self._profits = profits
        self.calls = []

    def positions_get(self):
        return list(self._positions)

    def orders_get(self):
        return list(self._orders)

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
        lambda *_args, **_kwargs: {
            "day_start_balance": 93670.92,
            "day_start_equity": 93678.44,
        },
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


def test_pending_limit_stop_risk_counts_whatever_its_magic(monkeypatch):
    _day(monkeypatch)
    orders = [
        SimpleNamespace(
            symbol="GBPUSD",
            volume_current=0.4,
            price_open=1.3,
            sl=1.29,
            type=_Raw.ORDER_TYPE_BUY_LIMIT,
            magic=99,
        )
    ]
    raw = _Raw([], {"GBPUSD": -80.0}, orders=orders)
    facts = _engine(_Adapter(raw))._size_room_facts(93522.57)
    assert facts["positions_total"] == 0
    assert facts["pending_orders_total"] == 1
    assert facts["pending_stop_risk_usd"] == 80.0
    assert facts["open_risk_usd"] == 80.0
    assert raw.calls == [(_Raw.ORDER_TYPE_BUY, "GBPUSD", 0.4, 1.3, 1.29)]
    room, read = binding_room_usd(facts)
    assert read == "bound"
    assert abs(room - (3522.57 - 80.0)) < 1e-6


def test_pending_without_a_stop_leaves_the_room_unset(monkeypatch):
    _day(monkeypatch)
    orders = [
        SimpleNamespace(
            symbol="GBPUSD",
            volume_current=0.4,
            price_open=1.3,
            sl=0.0,
            type=_Raw.ORDER_TYPE_SELL_LIMIT,
            magic=0,
        )
    ]
    facts = _engine(_Adapter(_Raw([], {"GBPUSD": -80.0}, orders=orders)))._size_room_facts(93522.57)
    assert facts["pending_orders_total"] == 1
    assert "open_risk_usd" not in facts
    assert "pending_stop_risk_usd" not in facts
    assert binding_room_usd(facts) == (None, "unset")


def test_unreadable_orders_leave_the_room_unset(monkeypatch):
    _day(monkeypatch)

    class _NoOrders(_Raw):
        def orders_get(self):
            return None

    facts = _engine(_Adapter(_NoOrders([], {})))._size_room_facts(93522.57)
    assert facts["positions_total"] is None
    assert "pending_orders_total" not in facts
    assert "open_risk_usd" not in facts
    assert binding_room_usd(facts) == (None, "unset")


def test_unknown_pending_type_leaves_the_room_unset(monkeypatch):
    _day(monkeypatch)
    orders = [
        SimpleNamespace(
            symbol="GBPUSD",
            volume_current=0.4,
            price_open=1.3,
            sl=1.29,
            type=99,
            magic=1,
        )
    ]
    facts = _engine(_Adapter(_Raw([], {"GBPUSD": -80.0}, orders=orders)))._size_room_facts(93522.57)
    assert "open_risk_usd" not in facts
    assert binding_room_usd(facts) == (None, "unset")


def test_a_calc_that_rejects_pending_types_still_counts_the_limit(monkeypatch):
    _day(monkeypatch)

    class _MarketOnly(_Raw):
        def order_calc_profit(self, order_type, symbol, volume, price_open, price_close):
            if order_type not in (self.ORDER_TYPE_BUY, self.ORDER_TYPE_SELL):
                raise RuntimeError("pending type")
            return super().order_calc_profit(order_type, symbol, volume, price_open, price_close)

    orders = [
        SimpleNamespace(
            symbol="GBPUSD",
            volume_current=0.4,
            price_open=1.3,
            sl=1.29,
            type=_Raw.ORDER_TYPE_BUY_LIMIT,
            magic=99,
        )
    ]
    raw = _MarketOnly([], {"GBPUSD": -80.0}, orders=orders)
    facts = _engine(_Adapter(raw))._size_room_facts(93522.57)
    assert facts["pending_stop_risk_usd"] == 80.0
    assert facts["open_risk_usd"] == 80.0
    assert raw.calls == [(_Raw.ORDER_TYPE_BUY, "GBPUSD", 0.4, 1.3, 1.29)]


def test_a_stop_limit_is_valued_at_its_limit_price(monkeypatch):
    _day(monkeypatch)
    orders = [
        SimpleNamespace(
            symbol="GBPUSD",
            volume_current=0.4,
            price_open=1.31,
            price_stoplimit=1.30,
            sl=1.29,
            type=_Raw.ORDER_TYPE_BUY_STOP_LIMIT,
            magic=99,
        )
    ]
    raw = _Raw([], {"GBPUSD": -40.0}, orders=orders)
    facts = _engine(_Adapter(raw))._size_room_facts(93522.57)
    assert facts["pending_stop_risk_usd"] == 40.0
    assert raw.calls == [(_Raw.ORDER_TYPE_BUY, "GBPUSD", 0.4, 1.30, 1.29)]
