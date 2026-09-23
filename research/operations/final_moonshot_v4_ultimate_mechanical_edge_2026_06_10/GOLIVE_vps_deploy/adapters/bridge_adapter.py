"""GOLIVE_vps — MT5 / bridge connection ADAPTER (scaffold, DEFAULT-OFF).

PURPOSE
=======
This module is the *interface seam* between the GTOS live runtime and the broker
transport on the VPS. It does NOT connect, does NOT log in, does NOT place orders
on import or by default. It provides:

  1. ``BridgeConfig``        — typed config + placeholders the owner fills on the VPS
                               (broker creds via ENV only, host/port for the bridge).
  2. ``BridgeAdapter``       — an ABC that mirrors ``src/mt5/mt5_interface.MT5Interface``
                               so production wiring is a drop-in once the owner supplies
                               the real transport.
  3. ``SiliconBridgeAdapter``— a concrete adapter targeting the ``nmetatrader5`` /
                               ``siliconmetatrader5`` localhost bridge (host/port
                               placeholders), GATED so it refuses to connect unless
                               BOTH the triple-gate is satisfied AND the local halt
                               flags are clear AND ``live_connect_allowed`` is opted in.
  4. ``NullBridgeAdapter``   — the default: every method returns a fail-closed result.

HARD GUARANTEES
===============
- No credentials are stored in this file. Creds come from the process environment
  (``.env`` on the VPS, gitignored) — see ``env.template``.
- Importing this module performs zero network / broker / order activity.
- ``connect()`` is fail-closed: it raises ``BridgeGateError`` unless the runtime is
  un-halted (local flag files), the triple-gate is satisfied, and the owner has
  explicitly opted into ``live_connect_allowed``. The default factory returns the
  ``NullBridgeAdapter``.
- The system is hard-halted. This scaffold prepares the seam; it does not flip it.

This file lives in the route dir (research/operations/...), NOT in production src/.
At go-live the owner promotes the reviewed adapter into ``src/mt5/`` (a PATCH is
staged under ../patches/), wires the real ``nmetatrader5`` import, and supplies VPS
host/port + broker creds. Until then it is inert scaffolding.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #
class BridgeGateError(RuntimeError):
    """Raised when a connect/order is attempted while a gate is not satisfied."""


# --------------------------------------------------------------------------- #
# Data contracts (mirror src/mt5/mt5_interface.py so this is a drop-in seam)
# --------------------------------------------------------------------------- #
@dataclass
class TickData:
    bid: float
    ask: float
    time: datetime
    spread_cents: float


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


@dataclass
class OrderResult:
    retcode: int
    order: int
    volume: float
    price: float
    comment: str
    deal: Optional[int] = None

    @property
    def success(self) -> bool:
        return self.retcode == 10009  # TRADE_RETCODE_DONE


MAGIC_NUMBER = 20260401  # matches src/mt5/mt5_interface.MAGIC_NUMBER


# --------------------------------------------------------------------------- #
# Config — placeholders the owner fills on the VPS (creds via ENV ONLY)
# --------------------------------------------------------------------------- #
@dataclass
class BridgeConfig:
    """Transport config. Creds are NEVER stored here — only ENV var *names*."""

    # ---- bridge transport (siliconmetatrader5 / nmetatrader5 localhost bridge) ----
    bridge_host: str = "127.0.0.1"          # OWNER SUPPLIES on VPS
    bridge_port: int = 8001                 # OWNER SUPPLIES on VPS (default 8001)
    transport: str = "nmetatrader5_bridge"  # or "local_mt5" if MT5 runs in-process

    # ---- terminal (Windows MT5) ----
    terminal_path: Optional[str] = None     # OWNER SUPPLIES (e.g. C:\\MT5\\FTMO\\terminal64.exe)
    portable: bool = True

    # ---- credential ENV var names (values live in the VPS .env, gitignored) ----
    env_login: str = "GTOS_MT5_LOGIN"
    env_password: str = "GTOS_MT5_PASSWORD"
    env_server: str = "GTOS_MT5_SERVER"

    # ---- gates (ALL must be opted-in by the owner before any connect) ----
    live_connect_allowed: bool = False      # owner master opt-in for THIS adapter
    profile_namespace: str = ""             # e.g. operator_profile

    # ---- identity audit (sha256 only; never the raw login) ----
    expected_login_sha256: Optional[str] = None
    expected_server: Optional[str] = None

    def resolved_credentials(self) -> dict[str, Optional[str]]:
        """Read creds from ENV at call time. Returns names mapped to presence-only
        on the public surface; the raw values are used only inside connect()."""
        return {
            "login": os.environ.get(self.env_login),
            "password": os.environ.get(self.env_password),
            "server": os.environ.get(self.env_server),
        }

    def credentials_present(self) -> dict[str, bool]:
        creds = self.resolved_credentials()
        return {k: bool(v) for k, v in creds.items()}


# --------------------------------------------------------------------------- #
# Adapter ABC — mirrors MT5Interface so production swaps are mechanical
# --------------------------------------------------------------------------- #
class BridgeAdapter(ABC):
    """Abstract broker transport. Concrete adapters MUST be fail-closed."""

    def __init__(self, config: BridgeConfig):
        self.config = config
        self._connected = False

    @abstractmethod
    def connect(self) -> bool: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    def is_connected(self) -> bool:
        return self._connected

    @abstractmethod
    def get_tick(self, symbol: str) -> Optional[TickData]: ...

    @abstractmethod
    def get_positions(self, symbol: Optional[str] = None) -> list[PositionInfo]: ...

    @abstractmethod
    def get_account_equity(self) -> float: ...

    @abstractmethod
    def get_account_balance(self) -> float: ...

    @abstractmethod
    def order_send(self, request: dict) -> OrderResult: ...

    @abstractmethod
    def get_history_deals(self, from_date: datetime, to_date: datetime,
                          symbol: Optional[str] = None) -> list[dict]: ...


# --------------------------------------------------------------------------- #
# NullBridgeAdapter — the DEFAULT. Everything is fail-closed.
# --------------------------------------------------------------------------- #
class NullBridgeAdapter(BridgeAdapter):
    """Default adapter: connects to nothing, places nothing. Returns inert/empty."""

    def connect(self) -> bool:
        self._connected = False
        return False

    def disconnect(self) -> None:
        self._connected = False

    def get_tick(self, symbol: str) -> Optional[TickData]:
        return None

    def get_positions(self, symbol: Optional[str] = None) -> list[PositionInfo]:
        return []

    def get_account_equity(self) -> float:
        return 0.0

    def get_account_balance(self) -> float:
        return 0.0

    def order_send(self, request: dict) -> OrderResult:
        # FAIL-CLOSED: never place an order from the default adapter.
        return OrderResult(
            retcode=-1, order=0, volume=0.0, price=0.0,
            comment="null_bridge_no_order_send_fail_closed",
        )

    def get_history_deals(self, from_date, to_date, symbol=None) -> list[dict]:
        return []


# --------------------------------------------------------------------------- #
# SiliconBridgeAdapter — concrete seam to nmetatrader5 localhost bridge.
# GATED. Refuses to connect unless the owner has cleared all gates.
# --------------------------------------------------------------------------- #
class SiliconBridgeAdapter(BridgeAdapter):
    """Adapter for the ``nmetatrader5`` / ``siliconmetatrader5`` localhost bridge.

    NOTE: the actual ``from nmetatrader5 import MetaTrader5`` import is deferred to
    ``connect()`` so importing THIS module never pulls the bridge. ``connect()`` is
    fail-closed behind:
      * the gate callback (triple-gate from config), AND
      * the halt callback (local halt flag files must be clear), AND
      * ``config.live_connect_allowed`` opted in, AND
      * creds present in ENV.
    The owner supplies all four. Until then this never opens a socket.
    """

    def __init__(self, config: BridgeConfig, *,
                 gate_ok=None, halt_clear=None):
        super().__init__(config)
        # Callables injected by the runtime; default to FAIL-CLOSED (deny).
        self._gate_ok = gate_ok or (lambda: False)
        self._halt_clear = halt_clear or (lambda: False)
        self._mt5 = None

    def _assert_can_connect(self) -> None:
        if not self.config.live_connect_allowed:
            raise BridgeGateError("live_connect_allowed is False (owner opt-in required)")
        if not self._gate_ok():
            raise BridgeGateError("triple-gate not satisfied (enabled AND apply_to_execution AND live_activation_allowed)")
        if not self._halt_clear():
            raise BridgeGateError("local halt flag(s) active — runtime is hard-halted")
        present = self.config.credentials_present()
        missing = [k for k, v in present.items() if not v]
        if missing:
            raise BridgeGateError(f"missing broker credentials in ENV: {missing}")

    def connect(self) -> bool:
        self._assert_can_connect()
        # Deferred import — only reached after all gates pass on the VPS.
        from nmetatrader5 import MetaTrader5  # noqa: PLC0415  (owner installs on VPS)
        creds = self.config.resolved_credentials()
        client = MetaTrader5(host=self.config.bridge_host, port=self.config.bridge_port)
        ok = client.initialize(
            login=int(creds["login"]),
            password=redacted"password"],
            server=creds["server"],
            **({"path": self.config.terminal_path} if self.config.terminal_path else {}),
            **({"portable": True} if self.config.portable else {}),
        )
        self._mt5 = client if ok else None
        self._connected = bool(ok)
        return self._connected

    def disconnect(self) -> None:
        if self._mt5 is not None:
            try:
                self._mt5.shutdown()
            finally:
                self._mt5 = None
        self._connected = False

    def _require_live(self):
        if not self._connected or self._mt5 is None:
            raise BridgeGateError("bridge not connected")
        return self._mt5

    def get_tick(self, symbol: str) -> Optional[TickData]:
        m = self._require_live()
        t = m.symbol_info_tick(symbol)
        if t is None:
            return None
        return TickData(bid=t.bid, ask=t.ask,
                        time=datetime.utcfromtimestamp(t.time),
                        spread_cents=(t.ask - t.bid) * 100.0)

    def get_positions(self, symbol: Optional[str] = None) -> list[PositionInfo]:
        m = self._require_live()
        raw = m.positions_get(symbol=symbol) if symbol else m.positions_get()
        out: list[PositionInfo] = []
        for p in (raw or []):
            if getattr(p, "magic", None) != MAGIC_NUMBER:
                continue
            out.append(PositionInfo(
                ticket=p.ticket, symbol=p.symbol, type=p.type, volume=p.volume,
                price_open=p.price_open, sl=p.sl, tp=p.tp, profit=p.profit,
                magic=p.magic, comment=p.comment,
                time=datetime.utcfromtimestamp(p.time)))
        return out

    def get_account_equity(self) -> float:
        m = self._require_live()
        info = m.account_info()
        return float(info.equity) if info else 0.0

    def get_account_balance(self) -> float:
        m = self._require_live()
        info = m.account_info()
        return float(info.balance) if info else 0.0

    def order_send(self, request: dict) -> OrderResult:
        # Re-assert gates at EVERY order — a halt mid-session must block new orders.
        self._assert_can_connect()
        m = self._require_live()
        r = m.order_send(request)
        return OrderResult(
            retcode=r.retcode, order=getattr(r, "order", 0),
            volume=getattr(r, "volume", 0.0), price=getattr(r, "price", 0.0),
            comment=getattr(r, "comment", ""), deal=getattr(r, "deal", None))

    def get_history_deals(self, from_date, to_date, symbol=None) -> list[dict]:
        m = self._require_live()
        deals = m.history_deals_get(from_date, to_date) or []
        rows = [d._asdict() if hasattr(d, "_asdict") else dict(d) for d in deals]
        if symbol:
            rows = [d for d in rows if d.get("symbol") == symbol]
        return rows


# --------------------------------------------------------------------------- #
# Factory — DEFAULT returns the NullBridgeAdapter.
# --------------------------------------------------------------------------- #
def make_bridge_adapter(config: Optional[BridgeConfig] = None, *,
                        gate_ok=None, halt_clear=None) -> BridgeAdapter:
    """Return the active adapter. DEFAULT-OFF: returns NullBridgeAdapter unless the
    owner has set ``live_connect_allowed=True`` on the config AND supplies the gate
    + halt callbacks. Even then the SiliconBridgeAdapter only connects on explicit
    ``connect()`` after re-checking all gates."""
    cfg = config or BridgeConfig()
    if not cfg.live_connect_allowed:
        return NullBridgeAdapter(cfg)
    return SiliconBridgeAdapter(cfg, gate_ok=gate_ok, halt_clear=halt_clear)
