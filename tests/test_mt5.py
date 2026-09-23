"""Tests for MT5 abstraction layer (Phase 1)."""

import sys
import time
from datetime import datetime, timezone
from types import SimpleNamespace

from src.mt5 import create_mt5, MAGIC_NUMBER
from src.mt5.mt5_interface import (
    OrderResult,
    PositionInfo,
    TRADE_ACTION_SLTP,
    ORDER_SEND_NONE_RETCODE,
    is_order_send_none,
)
from src.mt5.mt5_mock import MockMT5
from src.mt5.mt5_real import RealMT5


class TestMockMT5Connection:
    def test_connect_disconnect(self):
        mt5 = MockMT5()
        assert not mt5.is_connected()
        assert mt5.connect()
        assert mt5.is_connected()
        mt5.disconnect()
        assert not mt5.is_connected()

    def test_account_balance(self):
        mt5 = MockMT5(balance=50000.0)
        mt5.connect()
        assert mt5.get_account_balance() == 50000.0
        assert mt5.get_account_equity() == 50000.0

    def test_margin_mode(self):
        mt5 = MockMT5()
        assert mt5.get_margin_mode() == "netting"


class TestMockMT5Orders:
    def test_order_send_creates_position(self):
        mt5 = MockMT5()
        mt5.connect()
        result = mt5.order_send({
            "action": 1, "symbol": "XAUUSD", "volume": 0.10,
            "type": 0, "price": 2650.00, "sl": 2640.00, "tp": 2670.00,
            "magic": MAGIC_NUMBER, "comment": "test",
        })
        assert result.success
        assert result.volume == 0.10
        positions = mt5.get_positions("XAUUSD")
        assert len(positions) == 1
        assert positions[0].volume == 0.10
        assert positions[0].sl == 2640.00

    def test_order_log(self):
        mt5 = MockMT5()
        mt5.connect()
        mt5.order_send({"action": 1, "volume": 0.05, "magic": MAGIC_NUMBER})
        assert len(mt5._order_log) == 1

    def test_sltp_modify(self):
        mt5 = MockMT5()
        mt5.connect()
        result = mt5.order_send({
            "action": 1, "symbol": "XAUUSD", "volume": 0.10,
            "type": 0, "price": 2650.00, "sl": 2640.00, "tp": 2670.00,
            "magic": MAGIC_NUMBER,
        })
        ticket = result.order

        # Modify SL/TP
        mod_result = mt5.order_send({
            "action": TRADE_ACTION_SLTP, "symbol": "XAUUSD", "position": ticket,
            "sl": 2650.00, "tp": 2680.00,
        })
        assert mod_result.success
        pos = mt5.get_positions()[0]
        assert pos.sl == 2650.00
        assert pos.tp == 2680.00


class TestMockMT5Filtering:
    def test_get_positions_filters_by_magic(self):
        mt5 = MockMT5()
        mt5.connect()
        # Our position
        mt5.order_send({
            "action": 1, "volume": 0.10, "magic": MAGIC_NUMBER,
        })
        # Foreign position (different magic)
        foreign = PositionInfo(
            ticket=99999, symbol="XAUUSD", type=0, volume=1.0,
            price_open=2600.0, sl=0, tp=0, profit=0.0,
            magic=12345, comment="foreign", time=datetime.now(timezone.utc),
        )
        mt5._positions.append(foreign)

        # Only our position should be returned
        positions = mt5.get_positions()
        assert len(positions) == 1
        assert positions[0].magic == MAGIC_NUMBER


class TestMockMT5PartialClose:
    def test_partial_close_changes_ticket(self):
        mt5 = MockMT5()
        mt5.connect()
        result = mt5.order_send({
            "action": 1, "symbol": "XAUUSD", "volume": 0.10,
            "type": 0, "price": 2650.00, "sl": 2640.00, "tp": 2670.00,
            "magic": MAGIC_NUMBER,
        })
        old_ticket = result.order

        # Partial close: sell 0.05 of the 0.10
        close_result = mt5.order_send({
            "action": 1, "symbol": "XAUUSD", "volume": 0.05,
            "type": 1, "position": old_ticket, "magic": MAGIC_NUMBER,
        })
        assert close_result.success

        positions = mt5.get_positions()
        assert len(positions) == 1
        remaining = positions[0]
        assert remaining.volume == 0.05
        assert remaining.ticket != old_ticket  # New ticket after partial close
        assert remaining.sl == 0.0  # SL does NOT carry over
        assert remaining.tp == 0.0  # TP does NOT carry over

    def test_full_close_removes_position(self):
        mt5 = MockMT5()
        mt5.connect()
        result = mt5.order_send({
            "action": 1, "volume": 0.10, "type": 0, "magic": MAGIC_NUMBER,
        })
        mt5.order_send({
            "action": 1, "volume": 0.10, "type": 1,
            "position": result.order, "magic": MAGIC_NUMBER,
        })
        assert len(mt5.get_positions()) == 0


class TestOrderResult:
    def test_success_property(self):
        assert OrderResult(retcode=10009, order=1, volume=0.1, price=2650, comment="ok").success
        assert not OrderResult(retcode=10011, order=0, volume=0, price=0, comment="fail").success

    def test_order_send_none_wrapper(self):
        assert ORDER_SEND_NONE_RETCODE == 10011
        assert is_order_send_none(None)
        wrapped = OrderResult(
            retcode=ORDER_SEND_NONE_RETCODE, order=0, volume=0, price=0,
            comment="MT5 returned None",
        )
        assert is_order_send_none(wrapped)
        assert not wrapped.success


class TestFactory:
    def test_create_mock(self):
        mt5 = create_mt5("mock", balance=25000.0)
        assert isinstance(mt5, MockMT5)
        mt5.connect()
        assert mt5.get_account_balance() == 25000.0


class TestRealMT5History:
    def test_connect_passes_terminal_path_and_portable_flag(self, monkeypatch):
        calls = []
        fake_mt5 = SimpleNamespace(
            initialize=lambda **kwargs: calls.append(kwargs) or True,
        )
        monkeypatch.setitem(sys.modules, "MetaTrader5", fake_mt5)

        real = RealMT5(terminal_path="C:/MT5/FTMO/terminal64.exe", portable=True)

        assert real.connect()
        assert calls == [{"path": "C:/MT5/FTMO/terminal64.exe", "portable": True}]

    def test_candle_from_pos_timestamps_subtract_broker_offset(self):
        real = RealMT5()
        true_utc = datetime(2026, 5, 1, 14, 0, tzinfo=timezone.utc)
        broker_epoch = int(true_utc.timestamp()) + 10_800

        class FakeMT5:
            def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
                assert (symbol, timeframe, start_pos, count) == ("XAUUSD", 15, 0, 1)
                return [(broker_epoch, 4626.0, 4628.0, 4624.5, 4627.5, 100)]

        real._mt5 = FakeMT5()
        real._connected = True
        real._broker_offset_seconds = 10_800
        real._broker_offset_detected = True

        candles = real.get_candles("XAUUSD", 15, 1)

        assert candles == [
            {
                "time": "2026-05-01T14:00:00+00:00",
                "open": 4626.0,
                "high": 4628.0,
                "low": 4624.5,
                "close": 4627.5,
                "volume": 100,
            }
        ]

    def test_candle_range_timestamps_subtract_broker_offset(self):
        real = RealMT5()
        true_utc = datetime(2026, 5, 1, 14, 15, tzinfo=timezone.utc)
        broker_epoch = int(true_utc.timestamp()) + 10_800
        calls = []

        class FakeMT5:
            def copy_rates_range(self, symbol, timeframe, date_from, date_to):
                calls.append((symbol, timeframe, date_from, date_to))
                return [(broker_epoch, 4627.5, 4629.0, 4626.5, 4628.25, 80)]

        real._mt5 = FakeMT5()
        real._connected = True
        real._broker_offset_seconds = 10_800
        real._broker_offset_detected = True
        start = datetime(2026, 5, 1, 14, 0, tzinfo=timezone.utc)
        end = datetime(2026, 5, 1, 15, 0, tzinfo=timezone.utc)

        candles = real.get_candles_range("XAUUSD", 15, start, end)

        assert calls == [("XAUUSD", 15, start, end)]
        assert candles[0]["time"] == "2026-05-01T14:15:00+00:00"
        assert candles[0]["close"] == 4628.25

    def test_history_deal_query_uses_broker_time_bounds(self):
        real = RealMT5()
        calls = []

        class FakeMT5:
            def symbol_info_tick(self, symbol):
                return SimpleNamespace(time=1_771_654_000, bid=4626.25, ask=4626.80)

            def history_deals_get(self, from_date, to_date, group=None):
                calls.append((from_date, to_date, group))
                return []

        real._mt5 = FakeMT5()
        real._connected = True
        real._broker_offset_seconds = 10_800
        real._broker_offset_detected = True

        start = datetime(2026, 5, 1, 14, 0, tzinfo=timezone.utc)
        end = datetime(2026, 5, 1, 14, 5, tzinfo=timezone.utc)
        real.get_history_deals(start, end, "XAUUSD")

        query_from, query_to, group = calls[0]
        assert query_from == datetime(2026, 5, 1, 17, 0, tzinfo=timezone.utc)
        assert query_to == datetime(2026, 5, 1, 17, 5, tzinfo=timezone.utc)
        assert group == "*XAUUSD*"

    def test_positions_warm_broker_offset_before_time_conversion(self):
        real = RealMT5()
        true_utc = datetime.now(timezone.utc).replace(microsecond=0)
        broker_epoch = int(true_utc.timestamp()) + 10_800

        class FakeMT5:
            def symbol_info_tick(self, symbol):
                return SimpleNamespace(
                    time=broker_epoch,
                    bid=30287.0,
                    ask=30288.0,
                )

            def positions_get(self, symbol=None):
                assert symbol == "NAS100"
                return [
                    SimpleNamespace(
                        ticket=242231894,
                        symbol="NDX100",
                        type=1,
                        volume=0.21,
                        price_open=30287.97,
                        sl=30404.2,
                        tp=29939.29,
                        profit=-10.0,
                        magic=MAGIC_NUMBER,
                        comment="GoldAgent_OBRetest",
                        time=broker_epoch,
                    )
                ]

        real._mt5 = FakeMT5()
        real._connected = True

        positions = real.get_positions("NAS100")

        assert real.get_broker_offset_seconds() == 10_800
        assert positions[0].time == true_utc

    def test_zero_tick_does_not_poison_broker_offset_detection(self):
        real = RealMT5()
        true_utc = datetime.now(timezone.utc).replace(microsecond=0)
        broker_epoch = int(true_utc.timestamp()) + 10_800

        class FakeMT5:
            def symbol_info_tick(self, symbol):
                if symbol == "AUDJPY":
                    return SimpleNamespace(time=0, bid=0.0, ask=0.0)
                return SimpleNamespace(time=broker_epoch, bid=30287.0, ask=30288.0)

        real._mt5 = FakeMT5()
        real._connected = True

        assert real.get_tick("AUDJPY") is None
        assert real.get_broker_offset_seconds() == 0
        assert real._broker_offset_detected is False

        tick = real.get_tick("NAS100")

        assert tick is not None
        assert real.get_broker_offset_seconds() == 10_800
        assert tick.time == true_utc

    def test_fresh_tick_repairs_plausible_nonzero_offset_from_stale_redetection(self):
        real = RealMT5()
        true_utc = datetime.now(timezone.utc).replace(microsecond=0)

        class FakeMT5:
            def symbol_info_tick(self, symbol):
                if symbol == "UKOIL_cash":
                    # Two hours stale on a UTC+3 server: raw-now looks like UTC+1,
                    # which is still inside the broad plausible-offset band.
                    epoch = int(true_utc.timestamp()) + 10_800 - (2 * 3600)
                else:
                    epoch = int(true_utc.timestamp()) + 10_800
                return SimpleNamespace(time=epoch, bid=1.0, ask=1.1)

        real._mt5 = FakeMT5()
        real._connected = True
        real._broker_offset_seconds = 10_800
        real._broker_offset_detected = True
        real._broker_offset_detected_at = time.monotonic() - (7 * 3600)

        stale_tick = real.get_tick("UKOIL_cash")
        assert stale_tick is not None
        assert real.get_broker_offset_seconds() == 3600

        fresh_tick = real.get_tick("EURUSD")
        assert fresh_tick is not None
        assert real.get_broker_offset_seconds() == 10_800
        assert abs((fresh_tick.time - true_utc).total_seconds()) < 1

    def test_candle_read_repairs_plausible_nonzero_offset_before_conversion(self):
        real = RealMT5()
        true_utc = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        broker_epoch = int(true_utc.timestamp()) + 10_800

        class FakeMT5:
            def symbol_info_tick(self, symbol):
                return SimpleNamespace(time=broker_epoch, bid=1.0, ask=1.1)

            def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
                return [(broker_epoch, 1.0, 1.2, 0.9, 1.1, 10)]

        real._mt5 = FakeMT5()
        real._connected = True
        real._broker_offset_seconds = 3600
        real._broker_offset_detected = True
        real._broker_offset_detected_at = time.monotonic()

        candles = real.get_candles("EURUSD", 15, 1)

        assert real.get_broker_offset_seconds() == 10_800
        assert candles[0]["time"] == true_utc.isoformat()

    def test_get_tick_lazily_selects_hidden_symbol_once(self):
        real = RealMT5()
        true_utc = datetime.now(timezone.utc).replace(microsecond=0)
        broker_epoch = int(true_utc.timestamp()) + 10_800

        class FakeMT5:
            def __init__(self):
                self.selected: list[tuple[str, bool]] = []

            def symbol_info(self, symbol):
                return SimpleNamespace(visible=False)

            def symbol_select(self, symbol, enabled):
                self.selected.append((symbol, enabled))
                return True

            def symbol_info_tick(self, symbol):
                if not self.selected:
                    return None
                return SimpleNamespace(time=broker_epoch, bid=30287.0, ask=30288.0)

        fake = FakeMT5()
        real._mt5 = fake
        real._connected = True

        tick = real.get_tick("US100.cash")
        second_tick = real.get_tick("US100.cash")

        assert tick is not None
        assert second_tick is not None
        assert fake.selected == [("US100.cash", True)]
        assert real.get_broker_offset_seconds() == 10_800

    def test_tick_range_query_uses_broker_time_bounds_and_normalizes_rows(self):
        real = RealMT5()
        true_utc = datetime(2026, 5, 1, 14, 1, 2, 123000, tzinfo=timezone.utc)
        calls = []

        class FakeMT5:
            COPY_TICKS_ALL = 3

            def copy_ticks_range(self, symbol, date_from, date_to, flags):
                calls.append((symbol, date_from, date_to, flags))
                return [
                    SimpleNamespace(
                        time=int(true_utc.timestamp()) + 10_800,
                        time_msc=int((true_utc.timestamp() + 10_800) * 1000),
                        bid=4626.25,
                        ask=4626.80,
                        last=0.0,
                        volume=1,
                        volume_real=0.0,
                        flags=6,
                    )
                ]

        real._mt5 = FakeMT5()
        real._connected = True
        real._broker_offset_seconds = 10_800
        real._broker_offset_detected = True
        start = datetime(2026, 5, 1, 14, 0, tzinfo=timezone.utc)
        end = datetime(2026, 5, 1, 14, 5, tzinfo=timezone.utc)

        ticks = real.get_ticks_range("XAUUSD", start, end)

        assert calls == [
            (
                "XAUUSD",
                datetime(2026, 5, 1, 17, 0, tzinfo=timezone.utc),
                datetime(2026, 5, 1, 17, 5, tzinfo=timezone.utc),
                3,
            )
        ]
        assert ticks == [
            {
                "ts_utc": "2026-05-01T14:01:02.123000+00:00",
                "time_msc": int((true_utc.timestamp() + 10_800) * 1000),
                "bid": 4626.25,
                "ask": 4626.80,
                "last": 0.0,
                "volume": 1.0,
                "volume_real": 0.0,
                "flags": 6,
            }
        ]


class TestMockMT5Candles:
    def test_set_and_get_candles(self):
        mt5 = MockMT5()
        candles = [{"time": "2026-01-01T00:00:00", "open": 2600, "high": 2610,
                     "low": 2595, "close": 2605, "volume": 100}]
        mt5.set_candles(15, candles)
        result = mt5.get_candles("XAUUSD", 15, 10)
        assert len(result) == 1
        assert result[0]["close"] == 2605

    def test_get_candles_empty(self):
        mt5 = MockMT5()
        assert mt5.get_candles("XAUUSD", 15, 10) == []


def test_get_margin_mode_maps_netting_vs_hedging():
    """The book asserts a HEDGING account at startup (per-(symbol,sleeve) multi-position is unsafe on
    netting). get_margin_mode must map MT5 margin_mode 0 -> netting, else -> hedging."""
    from src.mt5.mt5_real import RealMT5
    a = RealMT5.__new__(RealMT5)

    class _Info:
        def __init__(self, mm):
            self.margin_mode = mm

    class _M:
        def __init__(self, mm):
            self._mm = mm
        def account_info(self):
            return _Info(self._mm)
    a._mt5 = _M(0)
    assert a.get_margin_mode() == "netting"
    a._mt5 = _M(2)
    assert a.get_margin_mode() == "hedging"


def test_order_result_success_includes_partial_fill():
    """A partial fill (10010 DONE_PARTIAL) executed a position and must count as success (self.volume =
    filled lots); only non-DONE retcodes are failures."""
    from src.mt5.mt5_interface import OrderResult
    assert OrderResult(retcode=10009, order=1, volume=1.0, price=1.0, comment="").success is True
    assert OrderResult(retcode=10010, order=1, volume=0.5, price=1.0, comment="").success is True
    assert OrderResult(retcode=10027, order=0, volume=0.0, price=0.0, comment="").success is False
