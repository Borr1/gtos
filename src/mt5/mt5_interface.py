"""Abstract interface for MT5 operations.

Defines the contract that both MockMT5 (macOS development/testing)
and RealMT5 (Windows production) must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class TickData:
    bid: float
    ask: float
    time: datetime
    spread_cents: float  # (ask - bid) * 100


@dataclass
class PositionInfo:
    ticket: int
    symbol: str
    type: int  # 0=BUY, 1=SELL
    volume: float
    price_open: float
    sl: float
    tp: float
    profit: float
    magic: int
    comment: str
    time: datetime


# MetaTrader5.order_send returned None. RealMT5 wraps that as this retcode plus
# comment "MT5 returned None". Official TRADE_RETCODE_ERROR is also 10011; both
# mean the send did not execute. Neither is TRADE_RETCODE_DONE (10009).
ORDER_SEND_NONE_RETCODE = 10011


def is_order_send_none(result) -> bool:
    """True when order_send returned None or the RealMT5 10011 wrapper.

    Broker-unknown: not a fill, not a confirmed close. Callers must not stamp
    disk ``closed`` and must not hammer order_send every poll.
    """
    if result is None:
        return True
    try:
        retcode = int(getattr(result, "retcode", 0) or 0)
    except (TypeError, ValueError):
        retcode = 0
    if retcode == ORDER_SEND_NONE_RETCODE:
        return True
    comment = str(getattr(result, "comment", "") or "")
    return "MT5 returned None" in comment


@dataclass
class OrderResult:
    retcode: int
    order: int  # ticket number
    volume: float
    price: float
    comment: str
    deal: Optional[int] = None
    request_id: Optional[int] = None
    retcode_external: Optional[int] = None

    # retcodes that mean the order EXECUTED and a (possibly smaller) position now exists.
    _DONE_RETCODES = (10009, 10010)  # TRADE_RETCODE_DONE, TRADE_RETCODE_DONE_PARTIAL

    @property
    def success(self) -> bool:
        # A PARTIAL fill (10010) executed a position too (at self.volume) — treating it as a failure made
        # the book believe the order failed while a real (smaller) position existed -> orphan + re-place
        # risk. self.volume carries the actually-filled lots, so downstream sizing/exits scale correctly.
        return self.retcode in OrderResult._DONE_RETCODES


MAGIC_NUMBER = 20260401  # Unique identifier for this agent

# ---------------------------------------------------------------------------
# BROKER-SIDE IDENTITY PER DECISION SURFACE (F5, 2026-08-12)
# ---------------------------------------------------------------------------
# The magic used to be ONE module constant shared by every worker, and every
# position read filtered on it. That is safe while one book runs per account
# and becomes a live-behaviour change on ARMED money the moment a second one
# does, because namespace isolates every FILE surface and NO broker surface:
#
#   RealMT5.get_open_positions (mt5_real.py:358) feeds
#   book_engine._open_risk_pct (book_engine.py:860), which returns the FULL
#   gross-risk cap when ANY position it can see has sl == 0, price_open == 0,
#   or an unreadable value_per_point (book_engine.py:878-884). One experiment
#   position on a symbol without instrument config -- and redacted_account already
#   silently skips 13 symbol/sleeve pairs on exactly that -- would make the
#   ARMED book read `gross_risk_cap_exhausted` and stop opening any unit at
#   all, SILENTLY, with a healthy-looking log.
#
# So the magic is a pure function of the runtime namespace. A namespace and
# not an environment variable, because the namespace is ALREADY the uniqueness
# key for the single-instance lock, the conviction ledger, the placement
# ledger, the trade records, the governor state, the supervisor's liveness
# match and `set_activation_context` -- so it cannot be set wrong
# independently of everything else, the way a free environment variable could.
#
# An unknown namespace returns the ARMED magic. That is deliberate: a typo
# must not mint a new broker identity, it must land the worker on the identity
# whose positions the rest of the system already knows how to manage.
MAGIC_F5_MINIMAL = 0  # the minimal-size experiment (F5)

#: Broker order-comment prefix per identity. MT5 truncates comments to 16
#: chars, so every producer slices ``[:16]`` after prefixing.
COMMENT_PREFIX_ARMED = "W7:"
COMMENT_PREFIX_F5_MINIMAL = "F5:"

_NAMESPACE_MAGIC: dict[str, int] = {
    "operator": MAGIC_F5_MINIMAL,
    "redacted_account_f5_minimal": MAGIC_F5_MINIMAL,
}

_MAGIC_COMMENT_PREFIX: dict[int, str] = {
    MAGIC_NUMBER: COMMENT_PREFIX_ARMED,
    MAGIC_F5_MINIMAL: COMMENT_PREFIX_F5_MINIMAL,
}


def magic_for_namespace(namespace: "str | None") -> int:
    """The broker-side identity of a decision surface, from its namespace.

    Unknown/absent namespaces return :data:`MAGIC_NUMBER` -- the armed book's
    identity -- so a typo can never mint an unmanaged third identity.
    """

    return _NAMESPACE_MAGIC.get(str(namespace or ""), MAGIC_NUMBER)


def comment_prefix_for_magic(magic: "int | None") -> str:
    """The order-comment prefix that goes with a broker identity."""

    try:
        return _MAGIC_COMMENT_PREFIX.get(int(magic), COMMENT_PREFIX_ARMED)
    except (TypeError, ValueError):
        return COMMENT_PREFIX_ARMED


def comment_prefix_for_namespace(namespace: "str | None") -> str:
    """The order-comment prefix of a decision surface, from its namespace."""

    return comment_prefix_for_magic(magic_for_namespace(namespace))


# MetaTrader5 trade action constants used by the runtime. Keeping the values
# here avoids importing the Windows-only MetaTrader5 package in unit tests.
TRADE_ACTION_DEAL = 1
TRADE_ACTION_PENDING = 5
TRADE_ACTION_SLTP = 6
# Added 2026-07-26 for the activation-token request classifier, which has to
# reason about every action the runtime can send — not just the three it
# currently sends. Values are MetaTrader5's own enum.
TRADE_ACTION_MODIFY = 7
TRADE_ACTION_REMOVE = 8
# MetaTrader5 order types. The live book currently sends only BUY/SELL (0/1)
# as TRADE_ACTION_DEAL. BUY_LIMIT/SELL_LIMIT are the T4 native pending rail
# and are used only when TradeIntent.entry_price is set.
ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1
ORDER_TYPE_BUY_LIMIT = 2
ORDER_TYPE_SELL_LIMIT = 3


class MT5Interface(ABC):
    """Abstract interface for MT5 operations."""

    @abstractmethod
    def connect(self) -> bool:
        """Connect to MT5 terminal. Returns True if successful."""

    @abstractmethod
    def disconnect(self):
        """Disconnect from MT5 terminal."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection to MT5 is alive."""

    @abstractmethod
    def get_tick(self, symbol: str = "XAUUSD") -> Optional[TickData]:
        """Get current tick data."""

    @abstractmethod
    def get_candles(self, symbol: str, timeframe: int, count: int) -> list[dict]:
        """Get OHLCV candles. Returns list of {time, open, high, low, close, volume}."""

    @abstractmethod
    def get_candles_range(self, symbol: str, timeframe: int, date_from: datetime, date_to: datetime) -> list[dict]:
        """Get OHLCV candles between two datetimes. Returns list of {time, open, high, low, close, volume}."""

    @abstractmethod
    def get_ticks_range(self, symbol: str, date_from: datetime, date_to: datetime) -> list[dict]:
        """Get bid/ask ticks between two datetimes without placing or modifying orders."""

    @abstractmethod
    def get_positions(self, symbol: str = "XAUUSD") -> list[PositionInfo]:
        """Get all open positions for symbol, filtered by MAGIC_NUMBER."""

    @abstractmethod
    def get_account_balance(self) -> float:
        """Get current account balance."""

    @abstractmethod
    def get_account_equity(self) -> float:
        """Get current account equity."""

    @abstractmethod
    def get_margin_mode(self) -> str:
        """Returns 'netting' or 'hedging'."""

    @abstractmethod
    def order_send(self, request: dict) -> OrderResult:
        """Send an order to MT5. Returns OrderResult."""

    @abstractmethod
    def get_history_deals(self, from_date: datetime, to_date: datetime,
                          symbol: str = "XAUUSD") -> Optional[list[dict]]:
        """Get historical deals for reconciliation; None means the broker fetch failed."""
