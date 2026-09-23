"""Demo-terminal MT5 client for fleet PLACE.

This is not ``src.mt5.mt5_real.RealMT5`` and not the Challenge writer.
``order_send`` is reached only after ``assert_demo_place_target``.
MetaTrader5 is imported lazily so Linux CI can mock the client.
"""

from __future__ import annotations

from typing import Any, Protocol

from judgment.fleet.allowlist import FORBIDDEN_LOGINS, PlaceVeto, assert_demo_place_target
from judgment.fleet.observer_config import Observer

# Public MetaQuotes constants (avoid importing MetaTrader5 in tests).
TRADE_ACTION_DEAL = 1
ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1
ORDER_TIME_GTC = 0
ORDER_FILLING_FOK = 0
ORDER_FILLING_IOC = 1
TRADE_RETCODE_DONE = 10009
TRADE_RETCODE_DONE_PARTIAL = 10010
TRADE_RETCODE_PLACED = 10008
TRADE_ACTION_SLTP = 6
FLEET_MAGIC = 20260919


class MT5DemoClient(Protocol):
    def initialize(
        self,
        path: str | None = None,
        login: int | None = None,
        password: str | None = None,
        server: str | None = None,
        portable: bool = True,
    ) -> bool: ...

    def login(self, login: int, password: str | None = None, server: str | None = None) -> bool: ...

    def order_send(self, request: dict[str, Any]) -> Any: ...

    def positions_get(self, ticket: int | None = None, symbol: str | None = None) -> Any: ...

    def symbol_select(self, symbol: str, enable: bool = True) -> bool: ...

    def symbol_info_tick(self, symbol: str) -> Any: ...

    def account_info(self) -> Any: ...

    def shutdown(self) -> None: ...

    def last_error(self) -> tuple[Any, ...]: ...


class LiveMT5DemoClient:
    """Thin wrapper around the MetaTrader5 package for one demo terminal."""

    def __init__(self, module: Any | None = None) -> None:
        if module is None:
            try:
                import MetaTrader5 as module  # type: ignore[import-not-found]
            except ImportError as exc:
                raise PlaceVeto("metatrader5_unavailable") from exc
        self._mt5 = module

    def initialize(
        self,
        path: str | None = None,
        login: int | None = None,
        password: str | None = None,
        server: str | None = None,
        portable: bool = True,
    ) -> bool:
        kwargs: dict[str, Any] = {"portable": portable}
        if login is not None:
            kwargs["login"] = login
        if password is not None:
            kwargs["password"] = password
        if server:
            kwargs["server"] = server
        if path:
            return bool(self._mt5.initialize(path, **kwargs))
        return bool(self._mt5.initialize(**kwargs))

    def login(self, login: int, password: str | None = None, server: str | None = None) -> bool:
        kwargs: dict[str, Any] = {}
        if password is not None:
            kwargs["password"] = password
        if server:
            kwargs["server"] = server
        return bool(self._mt5.login(login, **kwargs))

    def order_send(self, request: dict[str, Any]) -> Any:
        return self._mt5.order_send(request)

    def positions_get(self, ticket: int | None = None, symbol: str | None = None) -> Any:
        kwargs: dict[str, Any] = {}
        if ticket is not None:
            kwargs["ticket"] = ticket
        if symbol is not None:
            kwargs["symbol"] = symbol
        return self._mt5.positions_get(**kwargs) if kwargs else self._mt5.positions_get()

    def symbol_select(self, symbol: str, enable: bool = True) -> bool:
        return bool(self._mt5.symbol_select(symbol, enable))

    def symbol_info_tick(self, symbol: str) -> Any:
        return self._mt5.symbol_info_tick(symbol)

    def account_info(self) -> Any:
        return self._mt5.account_info()

    def shutdown(self) -> None:
        self._mt5.shutdown()

    def last_error(self) -> tuple[Any, ...]:
        err = self._mt5.last_error()
        if isinstance(err, tuple):
            return err
        return (err,)


def connect_demo_terminal(
    observer: Observer,
    client: MT5DemoClient,
    *,
    password: str | None = None,
) -> int:
    """Initialize one demo terminal. Refuse Challenge login/path before IPC."""
    login = assert_demo_place_target(
        login=observer.demo_login,
        terminal_path=observer.terminal_path,
        account_kind=observer.account_kind,
    )
    secret = password if password is not None else observer.password()
    if not secret:
        raise PlaceVeto("missing_demo_password_env", password_env=observer.password_env)
    if not observer.server:
        raise PlaceVeto("missing_demo_server", observer_id=observer.id)
    ok = client.initialize(
        observer.terminal_path,
        login=login,
        password=redacted
        server=observer.server,
        portable=True,
    )
    if not ok:
        raise PlaceVeto("mt5_initialize_failed", last_error=_safe_last_error(client))
    info = client.account_info()
    connected = getattr(info, "login", None) if info is not None else None
    try:
        connected_login = int(connected) if connected is not None else None
    except (TypeError, ValueError):
        connected_login = None
    if connected_login is None or connected_login in FORBIDDEN_LOGINS:
        client.shutdown()
        raise PlaceVeto(
            "connected_login_forbidden",
            connected_login=connected_login,
            place_on_challenge=False,
        )
    if connected_login != login:
        client.shutdown()
        raise PlaceVeto("connected_login_mismatch", connected_login=connected_login, expected=login)
    return connected_login


def _safe_last_error(client: MT5DemoClient) -> tuple[Any, ...]:
    try:
        return client.last_error()
    except Exception:  # noqa: BLE001 — last_error is diagnostic only
        return ()


def order_side(side: str) -> int:
    token = str(side).strip().lower()
    if token in {"buy", "long"}:
        return ORDER_TYPE_BUY
    if token in {"sell", "short"}:
        return ORDER_TYPE_SELL
    raise PlaceVeto("missing_side", side=side)


def opposite_side(order_type: int) -> int:
    return ORDER_TYPE_SELL if order_type == ORDER_TYPE_BUY else ORDER_TYPE_BUY


def result_ok(result: Any) -> bool:
    retcode = getattr(result, "retcode", None)
    return retcode in {TRADE_RETCODE_DONE, TRADE_RETCODE_DONE_PARTIAL, TRADE_RETCODE_PLACED}


def result_ticket(result: Any) -> int | None:
    for key in ("order", "deal"):
        value = getattr(result, key, None)
        if value not in (None, 0, "0", ""):
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
    return None


def market_open_request(
    *,
    symbol: str,
    side: str,
    volume: float,
    comment: str,
    price: float,
    sl: float | None = None,
    tp: float | None = None,
) -> dict[str, Any]:
    request = {
        "action": TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(volume),
        "type": order_side(side),
        "price": float(price),
        "deviation": 20,
        "magic": FLEET_MAGIC,
        "comment": comment,
        "type_time": ORDER_TIME_GTC,
        "type_filling": ORDER_FILLING_IOC,
    }
    if sl not in (None, "", 0, 0.0) and float(sl) > 0:
        request["sl"] = float(sl)
    if tp not in (None, "", 0, 0.0) and float(tp) > 0:
        request["tp"] = float(tp)
    return request


def market_sltp_request(
    *,
    symbol: str,
    position: int,
    sl: float,
    tp: float,
) -> dict[str, Any]:
    return {
        "action": TRADE_ACTION_SLTP,
        "symbol": symbol,
        "position": int(position),
        "sl": float(sl),
        "tp": float(tp),
        "magic": FLEET_MAGIC,
    }


def market_close_request(
    *,
    symbol: str,
    volume: float,
    position: int,
    comment: str,
    price: float,
    position_type: int,
) -> dict[str, Any]:
    return {
        "action": TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(volume),
        "type": opposite_side(int(position_type)),
        "position": int(position),
        "price": float(price),
        "deviation": 20,
        "magic": FLEET_MAGIC,
        "comment": comment,
        "type_time": ORDER_TIME_GTC,
        "type_filling": ORDER_FILLING_IOC,
    }


def tick_price(tick: Any, side: str, *, closing: bool = False) -> float:
    token = str(side).strip().lower()
    buy = token in {"buy", "long", "0"}
    if closing:
        return float(tick.bid if buy else tick.ask)
    return float(tick.ask if buy else tick.bid)
