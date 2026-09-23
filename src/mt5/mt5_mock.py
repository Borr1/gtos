"""Mock MT5 for development on macOS and testing."""

from datetime import datetime, timezone
from typing import Optional

from .mt5_interface import (
    MAGIC_NUMBER,
    MT5Interface,
    OrderResult,
    PositionInfo,
    TRADE_ACTION_SLTP,
    TickData,
)


class MockMT5(MT5Interface):
    """Mock MT5 for development on macOS and testing."""

    def __init__(self, balance: float = 100000.0):
        self._connected = False
        self._balance = balance
        self._equity = balance
        self._positions: list[PositionInfo] = []
        self._next_ticket = 10001
        self._tick = TickData(bid=2650.00, ask=2650.18,
                              time=datetime.now(timezone.utc), spread_cents=18.0)
        self._order_log: list[dict] = []  # For test assertions
        self._candles: dict[int, list[dict]] = {}  # tf_const -> candles
        self._ticks: dict[str, list[dict]] = {}

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self):
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    # --- Test helpers ---

    def set_tick(self, bid: float, ask: float):
        """Test helper: set current price."""
        self._tick = TickData(bid=bid, ask=ask, time=datetime.now(timezone.utc),
                              spread_cents=(ask - bid) * 100)

    def set_positions(self, positions: list[PositionInfo]):
        """Test helper: set current positions."""
        self._positions = positions

    def set_candles(self, timeframe: int, candles: list[dict]):
        """Test helper: set candles for a timeframe."""
        self._candles[timeframe] = candles

    def set_ticks(self, symbol: str, ticks: list[dict]):
        """Test helper: set historical bid/ask ticks."""
        self._ticks[symbol] = ticks

    # --- Interface implementation ---

    def get_tick(self, symbol: str = "XAUUSD") -> Optional[TickData]:
        return self._tick

    def get_candles(self, symbol: str, timeframe: int, count: int) -> list[dict]:
        candles = self._candles.get(timeframe, [])
        return candles[-count:] if candles else []

    def get_candles_range(self, symbol: str, timeframe: int, date_from, date_to) -> list[dict]:
        candles = self._candles.get(timeframe, [])
        from datetime import datetime as _dt
        results = []
        for c in candles:
            t = c.get("time", "")
            if isinstance(t, str):
                try:
                    ct = _dt.fromisoformat(t)
                except ValueError:
                    continue
            else:
                ct = t
            if hasattr(ct, 'timestamp') and hasattr(date_from, 'timestamp'):
                if date_from <= ct <= date_to:
                    results.append(c)
        return results

    def get_ticks_range(self, symbol: str, date_from: datetime, date_to: datetime) -> list[dict]:
        ticks = self._ticks.get(symbol, [])
        results = []
        for tick in ticks:
            raw_ts = tick.get("ts_utc") or tick.get("time")
            if isinstance(raw_ts, str):
                try:
                    ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                except ValueError:
                    continue
            else:
                ts = raw_ts
            if hasattr(ts, "tzinfo") and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if hasattr(ts, "timestamp") and date_from <= ts <= date_to:
                results.append(dict(tick))
        return results

    def get_positions(self, symbol: str = "XAUUSD") -> list[PositionInfo]:
        return [p for p in self._positions if p.magic == MAGIC_NUMBER]

    def get_account_balance(self) -> float:
        return self._balance

    def get_account_equity(self) -> float:
        return self._equity

    def get_margin_mode(self) -> str:
        return "netting"

    def order_send(self, request: dict) -> OrderResult:
        self._order_log.append(request)

        ticket = self._next_ticket
        self._next_ticket += 1

        volume = request.get("volume", 0.01)
        price = request.get("price", self._tick.bid)

        # TRADE_ACTION_SLTP — modify SL/TP on existing position
        if request.get("action") == TRADE_ACTION_SLTP:
            target_ticket = request.get("position", 0)
            for p in self._positions:
                if p.ticket == target_ticket:
                    p.sl = request.get("sl", p.sl)
                    p.tp = request.get("tp", p.tp)
                    break
            return OrderResult(retcode=10009, order=target_ticket,
                               volume=0, price=0, comment="Mock SLTP modify")

        # TRADE_ACTION_DEAL with position = close or partial close
        elif "position" in request:
            old_pos = None
            for i, p in enumerate(self._positions):
                if p.ticket == request["position"]:
                    old_pos = self._positions.pop(i)
                    break

            # Simulate MT5 ticket-change on partial close
            if old_pos and volume < old_pos.volume:
                remaining_volume = round(old_pos.volume - volume, 2)
                if remaining_volume >= 0.01:
                    new_pos = PositionInfo(
                        ticket=ticket,  # NEW ticket number
                        symbol=old_pos.symbol,
                        type=old_pos.type,
                        volume=remaining_volume,
                        price_open=old_pos.price_open,
                        sl=0.0,    # SL does NOT carry over on real MT5
                        tp=0.0,    # TP does NOT carry over on real MT5
                        profit=old_pos.profit,
                        magic=old_pos.magic,
                        comment=old_pos.comment,
                        time=old_pos.time,
                    )
                    self._positions.append(new_pos)
        else:
            # New position
            pos = PositionInfo(
                ticket=ticket, symbol=request.get("symbol", "XAUUSD"),
                type=request.get("type", 0), volume=volume,
                price_open=price, sl=request.get("sl", 0), tp=request.get("tp", 0),
                profit=0.0, magic=request.get("magic", MAGIC_NUMBER),
                comment=request.get("comment", ""), time=datetime.now(timezone.utc),
            )
            self._positions.append(pos)

        return OrderResult(retcode=10009, order=ticket, volume=volume,
                           price=price, comment="Mock fill")

    def get_history_deals(self, from_date: datetime, to_date: datetime,
                          symbol: str = "XAUUSD") -> list[dict]:
        return []
