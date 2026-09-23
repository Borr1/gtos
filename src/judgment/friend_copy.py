"""Autonomous friend copy — Challenge fill → friend_a / redacted_account / redacted_account.

Challenge ``0`` / ``operator`` is the only deciding writer.
Friend FTMO demos copy that fill: **same lots and the same broker SL/TP**.
Agents never ``order_send``, flatten, resize, or close friend tickets.
redacted_account stays idle. Verification stays quarantined.

Default-on for the three friend namespaces only (``GTOS_FRIEND_COPY`` unset).
This file never imports ``book_owner``, ``mt5_real``, or ``order_send``.
The in-system copier (fleet observer) builds the request; it is not an agent.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    from .challenge import (
        CHALLENGE_LOGIN as _CHALLENGE_LOGIN_STR,
        CHALLENGE_MAGIC as _CHALLENGE_MAGIC_STR,
        CHALLENGE_NS,
        VERIFICATION_QUARANTINED,
    )
except ImportError:  # file-location import on the host copier
    _CHALLENGE_LOGIN_STR = "0"
    _CHALLENGE_MAGIC_STR = "0"
    CHALLENGE_NS = "operator"
    VERIFICATION_QUARANTINED = "0"

FRIEND_COPY_ENV = "GTOS_FRIEND_COPY"
SCHEMA = "gtos.judgment.friend_copy.v0"
FEEDBACK_SCHEMA = "gtos.fleet_feedback.v0"

CHALLENGE_LOGIN = int(_CHALLENGE_LOGIN_STR)
CHALLENGE_MAGIC = int(_CHALLENGE_MAGIC_STR)
VERIFICATION_LOGIN = int(VERIFICATION_QUARANTINED)
redacted_account_LOGIN = 0
redacted_account_NS = "redacted_account_live_bee34003"

FRIEND_MAGIC = 20260919
FRIEND_COPY_ENV_DEFAULT_ON = True

FRIEND_NS = frozenset(
    {
        "redacted_account_f5_minimal",
        "ftmo_redacted_account_f5_minimal",
        "ftmo_redacted_account_f5_minimal",
    }
)
FRIEND_LOGINS: dict[str, int] = {
    "redacted_account_f5_minimal": 0,
    "ftmo_redacted_account_f5_minimal": 0,
    "ftmo_redacted_account_f5_minimal": 1514684855,
}
FRIEND_LOGIN_SET = frozenset(FRIEND_LOGINS.values())
FRIEND_PATH_MARKERS = ("FTMO_Trial", "FTMO_redacted_account", "FTMO_redacted_account")

FORBIDDEN_TARGET_LOGINS = frozenset(
    {CHALLENGE_LOGIN, VERIFICATION_LOGIN, redacted_account_LOGIN}
)
FORBIDDEN_TARGET_NS = frozenset({CHALLENGE_NS, redacted_account_NS})

# Fleet MICRO_LOT invention. Challenge 0.01 is only legal via lots_placed.
MICRO_LOT = 0.01
VOLUME_POISON_KEYS = frozenset(
    {
        "volume_min",
        "volume_step",
        "volume_max",
        "micro_lot",
        "DEFAULT_MICRO_LOT",
        "lot_min",
        "lot_step",
    }
)
_LOT_EVENT_KEYS = ("lots_placed", "volume", "lots", "result_volume")
_PROTECT_SL_KEYS = (
    "broker_position_sl",
    "broker_position_fill_adjusted_stop_loss",
    "broker_position_planned_stop_loss",
    "orig_sl",
    "sl",
    "stop_loss",
)
_PROTECT_TP_KEYS = (
    "broker_position_tp",
    "broker_position_fill_adjusted_take_profit",
    "broker_position_planned_take_profit",
    "tp",
    "take_profit",
    "orig_tp",
)

TRADE_ACTION_DEAL = 1
TRADE_ACTION_SLTP = 6
ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1
ORDER_TIME_GTC = 0
ORDER_FILLING_IOC = 1
POSITION_TYPE_BUY = 0
POSITION_TYPE_SELL = 1

_CLOSED_KIND = frozenset({"close", "closed", "flatten", "sync_close"})
_CLOSED_STATUS = frozenset(
    {
        "closed",
        "broker_closed",
        "vnext_time_stop",
        "time_stop",
        "broker_closed_absent_on_reconcile",
        "flattened",
        "stopped_out",
        "target_hit",
        "stop_hit",
    }
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TRADE_RECORD_REL = Path("pipeline_state") / "ultimate_book" / CHALLENGE_NS / "trade_records"
HOST_TRADE_RECORD_ROOTS = (
    REPO_ROOT / TRADE_RECORD_REL,
    Path(r"C:host-local/redacted_host/repo") / TRADE_RECORD_REL,
)

_FALSY = frozenset({"0", "false", "no", "off"})
_TRUTHY = frozenset({"1", "true", "yes", "on"})

_SIDE_ALIASES = {
    "buy": "buy",
    "long": "buy",
    "0": "buy",
    "sell": "sell",
    "short": "sell",
    "1": "sell",
}


class FriendCopyError(ValueError):
    """Fail-closed copy contract. Never invent lots or 0.0 protection."""

    def __init__(self, reason: str, **extra: Any) -> None:
        super().__init__(reason)
        self.reason = reason
        self.extra = extra


def agent_may_mutate_friend(
    *,
    ns: Any = None,
    login: Any = None,
    environ: Mapping[str, str] | None = None,
) -> bool:
    """Agents never place, close, resize, or ``order_send`` friend tickets."""

    del ns, login, environ
    return False


def friend_copy_env_on(*, environ: Mapping[str, str] | None = None) -> bool:
    """Unset = ON. Explicit 0/false/off disables the autonomous copy path."""

    env = environ if environ is not None else os.environ
    if FRIEND_COPY_ENV not in env:
        return FRIEND_COPY_ENV_DEFAULT_ON
    raw = str(env.get(FRIEND_COPY_ENV, "")).strip().lower()
    if raw in _FALSY:
        return False
    if raw in _TRUTHY or raw == "":
        return True
    return FRIEND_COPY_ENV_DEFAULT_ON


def friend_copy_on(
    *,
    ns: Any = None,
    login: Any = None,
    environ: Mapping[str, str] | None = None,
) -> bool:
    """Default-on for the three friend namespaces only. Challenge / FN stay off."""

    if not friend_copy_env_on(environ=environ):
        return False
    token = str(ns or "").strip()
    if token in FRIEND_NS:
        return True
    parsed = _as_int(login)
    if parsed in FRIEND_LOGIN_SET and token not in FORBIDDEN_TARGET_NS:
        return True
    return False


def assert_copy_target(
    *,
    ns: Any = None,
    login: Any = None,
    terminal_path: Any = None,
) -> None:
    """Refuse Challenge, redacted_account, Verification, and the Challenge exe path."""

    parsed = _as_int(login)
    token = str(ns or "").strip()
    path = str(terminal_path or "")
    if parsed in FORBIDDEN_TARGET_LOGINS:
        raise FriendCopyError(
            "forbidden_target_login",
            login=parsed,
            place_on_challenge=False,
            redacted_account_idle=True,
        )
    if token in FORBIDDEN_TARGET_NS:
        raise FriendCopyError(
            "forbidden_target_ns",
            ns=token,
            place_on_challenge=False,
            redacted_account_idle=True,
        )
    if _challenge_terminal_path(path):
        raise FriendCopyError(
            "forbidden_challenge_terminal",
            terminal_path=path,
            place_on_challenge=False,
        )
    if token and token not in FRIEND_NS:
        raise FriendCopyError("not_friend_ns", ns=token)
    if parsed is not None and parsed not in FRIEND_LOGIN_SET:
        raise FriendCopyError("not_friend_login", login=parsed)


def fleet_comment(ticket: Any) -> str:
    return f"fleet:{ticket}"


def order_side(side: Any) -> int:
    token = _side_token(side)
    if token is None:
        raise FriendCopyError("missing_side", side=side)
    return ORDER_TYPE_BUY if token == "buy" else ORDER_TYPE_SELL


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        text = str(value).strip()
        return int(text) if text.lstrip("-").isdigit() else None


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return None
    return number


def _side_token(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return _SIDE_ALIASES.get(str(value).strip().lower())


def _side_from_geometry(record: Mapping[str, Any] | None) -> str | None:
    """SHORT: SL above fill above TP. LONG: the inverse. Host records omit top-level side."""

    if not isinstance(record, Mapping):
        return None
    fill = _as_float(
        _dig(record, "execution", "broker_position_fill_price")
        or _dig(record, "execution", "broker_position_price_open")
        or _dig(record, "execution", "broker_entry_price")
    )
    sl, tp, _, _ = resolve_copy_protection(None, record)
    if fill is None or sl is None or tp is None:
        return None
    if sl > fill > tp:
        return "sell"
    if tp > fill > sl:
        return "buy"
    return None


def _challenge_terminal_path(path: str) -> bool:
    if not path:
        return False
    if any(marker in path for marker in FRIEND_PATH_MARKERS):
        return False
    lowered = path.replace("/", "\\").lower()
    return lowered.endswith(r"\mt5\ftmo\terminal64.exe")


def _walk(obj: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(obj, Mapping):
        yield obj
        for value in obj.values():
            yield from _walk(value)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            yield from _walk(item)


def _dig(obj: Any, *keys: str) -> Any:
    cur: Any = obj
    for key in keys:
        if not isinstance(cur, Mapping) or key not in cur:
            return None
        cur = cur[key]
    return cur


def _poison_only_volume(obj: Any) -> bool:
    """True when the only numeric volume-like keys are min/step/micro_lot."""

    found_legal = False
    found_poison = False
    for row in _walk(obj):
        for key, value in row.items():
            got = _as_float(value)
            if got is None:
                continue
            if key in VOLUME_POISON_KEYS:
                found_poison = True
            elif key in _LOT_EVENT_KEYS or key in {"lots_normalized"}:
                found_legal = True
    return found_poison and not found_legal


@dataclass(frozen=True)
class CopyContract:
    """One Challenge fill, ready for the in-system copier. Never sends."""

    ok: bool
    reason: str
    ticket: Any = None
    symbol: str = ""
    side: str | None = None
    lots: float | None = None
    sl: float | None = None
    tp: float | None = None
    comment: str = ""
    lots_source: str | None = None
    sl_source: str | None = None
    tp_source: str | None = None
    place_on_challenge: bool = False
    agent_order_send: bool = False
    redacted_account_idle: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "ok": self.ok,
            "reason": self.reason,
            "ticket": self.ticket,
            "symbol": self.symbol,
            "side": self.side,
            "lots": self.lots,
            "sl": self.sl,
            "tp": self.tp,
            "comment": self.comment,
            "lots_source": self.lots_source,
            "sl_source": self.sl_source,
            "tp_source": self.tp_source,
            "place_on_challenge": False,
            "agent_order_send": False,
            "agent_may_mutate_friend": False,
            "redacted_account_idle": True,
            "never_invent_micro_lot": True,
            "never_invent_zero_protection": True,
            "never_flatten_challenge": True,
            "source_closed": self.reason == "challenge_source_closed",
            "close_friend_only": self.reason == "challenge_source_closed",
        }


def resolve_copy_lots(
    event: Mapping[str, Any] | None = None,
    trade_record: Mapping[str, Any] | None = None,
) -> tuple[float | None, str | None]:
    """Challenge fill lots. Never invent 0.01. Never copy volume_min/step."""

    placed = _lots_placed(trade_record)
    if placed is not None and placed > 0:
        return placed, "instrumentation.gtos_live_flow_execution.lots_placed"

    for blob, label in (
        (trade_record, "trade_record"),
        (event, "event"),
    ):
        if not isinstance(blob, Mapping):
            continue
        for path, source in (
            (("execution", "result", "volume"), f"{label}.execution.result.volume"),
            (("result", "volume"), f"{label}.result.volume"),
            (("execution", "request", "volume"), f"{label}.execution.request.volume"),
            (("request", "volume"), f"{label}.request.volume"),
            (("lots_normalized",), f"{label}.lots_normalized"),
        ):
            got = _as_float(_dig(blob, *path))
            if got is not None and got > 0 and not _is_unconfirmed_micro(got, placed):
                return got, source
        for key in _LOT_EVENT_KEYS:
            if key in VOLUME_POISON_KEYS:
                continue
            got = _as_float(blob.get(key))
            if got is not None and got > 0 and not _is_unconfirmed_micro(got, placed):
                return got, f"{label}.{key}"

    merged = [x for x in (trade_record, event) if isinstance(x, Mapping)]
    if any(_poison_only_volume(blob) for blob in merged):
        return None, None
    return None, None


def _lots_placed(trade_record: Mapping[str, Any] | None) -> float | None:
    if not isinstance(trade_record, Mapping):
        return None
    paths = (
        ("instrumentation", "gtos_live_flow_execution", "lots_placed"),
        ("gtos_live_flow_execution", "lots_placed"),
        ("execution", "lots_placed"),
        ("lots_placed",),
    )
    for path in paths:
        got = _as_float(_dig(trade_record, *path))
        if got is not None and got > 0:
            return got
    for row in _walk(trade_record):
        got = _as_float(row.get("lots_placed"))
        if got is not None and got > 0:
            return got
    return None


def _is_unconfirmed_micro(lot: float, lots_placed: float | None) -> bool:
    if abs(lot - MICRO_LOT) > 1e-12:
        return False
    return lots_placed is None


def resolve_copy_protection(
    event: Mapping[str, Any] | None = None,
    trade_record: Mapping[str, Any] | None = None,
) -> tuple[float | None, float | None, str | None, str | None]:
    """Challenge broker SL/TP. Zero is missing, not a value we copy."""

    sl, sl_source = _first_protection(trade_record, event, _PROTECT_SL_KEYS, "sl")
    tp, tp_source = _first_protection(trade_record, event, _PROTECT_TP_KEYS, "tp")
    if sl is None or tp is None or sl == 0 or tp == 0:
        return None, None, sl_source, tp_source
    return sl, tp, sl_source, tp_source


def _first_protection(
    trade_record: Mapping[str, Any] | None,
    event: Mapping[str, Any] | None,
    keys: Iterable[str],
    kind: str,
) -> tuple[float | None, str | None]:
    fill_key = (
        "broker_position_fill_adjusted_stop_loss"
        if kind == "sl"
        else "broker_position_fill_adjusted_take_profit"
    )
    planned_key = (
        "broker_position_planned_stop_loss"
        if kind == "sl"
        else "broker_position_planned_take_profit"
    )
    preferred = (
        ("execution", f"broker_position_{kind}"),
        ("execution", fill_key),
        ("execution", planned_key),
    )
    if isinstance(trade_record, Mapping):
        for path in preferred:
            got = _as_float(_dig(trade_record, *path))
            if _nonzero_price(got):
                return got, ".".join(path)
        for row in _walk(trade_record):
            for key in keys:
                got = _as_float(row.get(key))
                if _nonzero_price(got):
                    return got, f"trade_record.{key}"
    if isinstance(event, Mapping):
        for key in keys:
            got = _as_float(event.get(key))
            if _nonzero_price(got):
                return got, f"event.{key}"
    return None, None


def _nonzero_price(value: float | None) -> bool:
    return value is not None and value != 0


def _status_closed(status: str) -> bool:
    token = str(status or "").strip().lower()
    if not token:
        return False
    if token in _CLOSED_STATUS:
        return True
    return token.startswith("closed") or token.endswith("_closed")


def challenge_source_is_closed(
    event: Mapping[str, Any] | None = None,
    trade_record: Mapping[str, Any] | None = None,
) -> tuple[bool, str | None]:
    """True when the Challenge ticket is already done. Do not resurrect it."""

    if isinstance(event, Mapping):
        kind = str(event.get("kind") or "").strip().lower()
        if kind in _CLOSED_KIND:
            return True, "event.kind"
        if event.get("closed") is True:
            return True, "event.closed"
        if _status_closed(str(event.get("trade_lifecycle_status") or "")):
            return True, "event.trade_lifecycle_status"
        if event.get("closed_at_utc") not in (None, "", 0, "0"):
            return True, "event.closed_at_utc"
    if isinstance(trade_record, Mapping):
        if _status_closed(str(trade_record.get("trade_lifecycle_status") or "")):
            return True, "trade_lifecycle_status"
        closed_at = trade_record.get("closed_at_utc") or _dig(
            trade_record, "execution", "closed_at_utc"
        )
        if closed_at not in (None, "", 0, "0"):
            return True, "closed_at_utc"
        close_action = trade_record.get("close_action") or _dig(
            trade_record, "execution", "close_action"
        )
        if close_action not in (None, "", 0, "0"):
            return True, "close_action"
    return False, None


def protection_is_missing(position: Any) -> bool:
    if isinstance(position, Mapping):
        sl = _as_float(position.get("sl"))
        tp = _as_float(position.get("tp"))
    else:
        sl = _as_float(getattr(position, "sl", None))
        tp = _as_float(getattr(position, "tp", None))
    return (sl is None or sl == 0) or (tp is None or tp == 0)


def load_challenge_trade_record(
    ticket: Any,
    *,
    roots: Iterable[Path] | None = None,
) -> dict[str, Any] | None:
    """``pipeline_state/ultimate_book/operator/trade_records/{ticket}.json``."""

    if ticket in (None, ""):
        return None
    name = f"{ticket}.json"
    for root in roots or HOST_TRADE_RECORD_ROOTS:
        path = Path(root) / name
        if not path.is_file():
            continue
        try:
            import json

            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(payload, dict):
            return payload
    return None


def resolve_copy_contract(
    event: Mapping[str, Any] | None = None,
    trade_record: Mapping[str, Any] | None = None,
    *,
    ns: Any = None,
    login: Any = None,
    terminal_path: Any = None,
    price: Any = None,
    environ: Mapping[str, str] | None = None,
) -> CopyContract:
    """Fail closed unless Challenge lots AND Challenge SL/TP are both known."""

    row = dict(event or {})
    record = trade_record if isinstance(trade_record, Mapping) else None
    if record is None and row.get("ticket") not in (None, ""):
        record = load_challenge_trade_record(row.get("ticket"))
    ticket = row.get("ticket")
    if ticket in (None, "") and isinstance(record, Mapping):
        ticket = (
            record.get("ticket")
            or _dig(record, "execution", "ticket")
            or _dig(record, "execution", "broker_entry_deal_ticket")
        )
    symbol = str(row.get("symbol") or (record or {}).get("symbol") or "").strip()
    side = _side_token(
        row.get("side")
        or (record or {}).get("side")
        or (record or {}).get("direction")
        or _dig(record, "instrumentation", "direction")
        or _dig(record, "instrumentation", "gtos_vnext_pretrade_cost_model", "side")
        or _dig(record, "instrumentation", "gtos_vnext_source_event_details", "direction")
        or _dig(record, "execution", "side")
    )
    if side is None:
        side = _side_from_geometry(record)
    comment = fleet_comment(ticket) if ticket not in (None, "") else ""

    try:
        if ns is not None or login is not None or terminal_path:
            assert_copy_target(ns=ns, login=login, terminal_path=terminal_path)
        source_login = _as_int(row.get("source_login") or row.get("login"))
        if source_login is not None and source_login != CHALLENGE_LOGIN:
            raise FriendCopyError("source_not_challenge", source_login=source_login)
        if source_login == VERIFICATION_LOGIN:
            raise FriendCopyError("quarantined_source", source_login=source_login)
        if not friend_copy_env_on(environ=environ):
            raise FriendCopyError("friend_copy_disabled")
    except FriendCopyError as exc:
        return CopyContract(
            ok=False,
            reason=exc.reason,
            ticket=ticket,
            symbol=symbol,
            side=side,
            comment=comment,
            extra=dict(exc.extra),
        )

    if ticket in (None, ""):
        return CopyContract(ok=False, reason="missing_ticket", symbol=symbol, side=side)

    lots, lots_source = resolve_copy_lots(row, record)
    sl, tp, sl_source, tp_source = resolve_copy_protection(row, record)
    closed, closed_from = challenge_source_is_closed(row, record)
    if closed:
        return CopyContract(
            ok=False,
            reason="challenge_source_closed",
            ticket=ticket,
            symbol=symbol,
            side=side,
            lots=lots,
            sl=sl,
            tp=tp,
            lots_source=lots_source,
            sl_source=sl_source,
            tp_source=tp_source,
            comment=comment,
            extra={"source_closed_from": closed_from, "close_friend_only": True},
        )
    if not symbol:
        return CopyContract(ok=False, reason="missing_symbol", ticket=ticket, side=side)
    if side is None:
        return CopyContract(ok=False, reason="missing_side", ticket=ticket, symbol=symbol)
    if lots is None or lots <= 0:
        return CopyContract(
            ok=False,
            reason="missing_source_volume",
            ticket=ticket,
            symbol=symbol,
            side=side,
            comment=comment,
            lots_source=lots_source,
        )
    if sl is None or tp is None:
        return CopyContract(
            ok=False,
            reason="missing_challenge_protection",
            ticket=ticket,
            symbol=symbol,
            side=side,
            lots=lots,
            lots_source=lots_source,
            sl=sl,
            tp=tp,
            sl_source=sl_source,
            tp_source=tp_source,
            comment=comment,
        )
    extra: dict[str, Any] = {}
    if price is not None:
        extra["price"] = price
    return CopyContract(
        ok=True,
        reason="copy_ready",
        ticket=ticket,
        symbol=symbol,
        side=side,
        lots=lots,
        sl=sl,
        tp=tp,
        comment=comment,
        lots_source=lots_source,
        sl_source=sl_source,
        tp_source=tp_source,
        extra=extra,
    )


def copy_open_request(
    *,
    symbol: str,
    side: str,
    volume: float,
    sl: float,
    tp: float,
    comment: str,
    price: float,
    magic: int = FRIEND_MAGIC,
) -> dict[str, Any]:
    """Market DEAL with Challenge lots and Challenge SL/TP. Copier-owned."""

    lot = _as_float(volume)
    stop = _as_float(sl)
    target = _as_float(tp)
    if lot is None or lot <= 0:
        raise FriendCopyError("missing_source_volume", volume=volume)
    if stop is None or stop == 0 or target is None or target == 0:
        raise FriendCopyError(
            "missing_challenge_protection",
            sl=sl,
            tp=tp,
        )
    return {
        "action": TRADE_ACTION_DEAL,
        "symbol": str(symbol),
        "volume": float(lot),
        "type": order_side(side),
        "price": float(price),
        "sl": float(stop),
        "tp": float(target),
        "deviation": 20,
        "magic": int(magic),
        "comment": str(comment),
        "type_time": ORDER_TIME_GTC,
        "type_filling": ORDER_FILLING_IOC,
    }


def copy_sltp_request(
    *,
    symbol: str,
    position: int,
    sl: float,
    tp: float,
    magic: int = FRIEND_MAGIC,
) -> dict[str, Any]:
    """TRADE_ACTION_SLTP for an already-open friend ticket. Copier-owned."""

    stop = _as_float(sl)
    target = _as_float(tp)
    if stop is None or stop == 0 or target is None or target == 0:
        raise FriendCopyError("missing_challenge_protection", sl=sl, tp=tp)
    ticket = _as_int(position)
    if ticket is None:
        raise FriendCopyError("missing_demo_ticket", position=position)
    return {
        "action": TRADE_ACTION_SLTP,
        "symbol": str(symbol),
        "position": int(ticket),
        "sl": float(stop),
        "tp": float(target),
        "magic": int(magic),
    }


def copy_close_request(
    *,
    symbol: str,
    side: str,
    volume: float,
    position: int,
    price: float,
    comment: str = "",
    magic: int = FRIEND_MAGIC,
) -> dict[str, Any]:
    """Market DEAL close of a friend copy. Never a Challenge ticket."""

    lot = _as_float(volume)
    ticket = _as_int(position)
    if lot is None or lot <= 0:
        raise FriendCopyError("missing_close_volume", volume=volume)
    if ticket is None:
        raise FriendCopyError("missing_demo_ticket", position=position)
    open_type = order_side(side)
    close_type = ORDER_TYPE_SELL if open_type == ORDER_TYPE_BUY else ORDER_TYPE_BUY
    return {
        "action": TRADE_ACTION_DEAL,
        "symbol": str(symbol),
        "volume": float(lot),
        "type": close_type,
        "position": int(ticket),
        "price": float(price),
        "deviation": 20,
        "magic": int(magic),
        "comment": str(comment or f"fleet-close:{ticket}"),
        "type_time": ORDER_TIME_GTC,
        "type_filling": ORDER_FILLING_IOC,
        "place_on_challenge": False,
        "close_friend_only": True,
    }


def enrich_open_request(
    request: Mapping[str, Any],
    event: Mapping[str, Any] | None = None,
    trade_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Stamp Challenge lots + SL/TP onto a fleet DEAL request. Fail closed."""

    contract = resolve_copy_contract(event, trade_record)
    if not contract.ok:
        raise FriendCopyError(contract.reason, ticket=contract.ticket, symbol=contract.symbol)
    out = dict(request)
    out["volume"] = float(contract.lots or 0)
    out["sl"] = float(contract.sl or 0)
    out["tp"] = float(contract.tp or 0)
    if contract.comment:
        out.setdefault("comment", contract.comment)
    out.setdefault("magic", FRIEND_MAGIC)
    if not _nonzero_price(_as_float(out.get("sl"))) or not _nonzero_price(_as_float(out.get("tp"))):
        raise FriendCopyError("missing_challenge_protection", request=out)
    return out


def protection_sync_plan(
    *,
    challenge_ticket: Any,
    demo_ticket: Any,
    demo_symbol: str,
    demo_sl: Any,
    demo_tp: Any,
    event: Mapping[str, Any] | None = None,
    trade_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Plan a copier SLTP when the friend ticket still shows 0.0 / 0.0."""

    position = {"sl": demo_sl, "tp": demo_tp, "symbol": demo_symbol, "ticket": demo_ticket}
    seed = dict(event or {})
    if not seed:
        seed = {"ticket": challenge_ticket, "symbol": demo_symbol, "side": "sell"}
    contract = resolve_copy_contract(seed, trade_record)
    if not contract.ok:
        return {
            "ok": False,
            "reason": contract.reason,
            "action": "sync_protection",
            "ticket": challenge_ticket,
            "demo_ticket": demo_ticket,
            "order_send": False,
            "agent_order_send": False,
            "place_on_challenge": False,
        }
    if not protection_is_missing(position):
        return {
            "ok": True,
            "reason": "already_protected",
            "action": "sync_protection",
            "ticket": challenge_ticket,
            "demo_ticket": demo_ticket,
            "sl": contract.sl,
            "tp": contract.tp,
            "order_send": False,
            "agent_order_send": False,
            "place_on_challenge": False,
        }
    request = copy_sltp_request(
        symbol=demo_symbol or contract.symbol,
        position=int(demo_ticket),
        sl=float(contract.sl or 0),
        tp=float(contract.tp or 0),
    )
    return {
        "ok": True,
        "reason": "protect_ready",
        "action": "sync_protection",
        "ticket": challenge_ticket,
        "demo_ticket": demo_ticket,
        "lots": contract.lots,
        "sl": contract.sl,
        "tp": contract.tp,
        "request": request,
        "order_send": False,
        "agent_order_send": False,
        "place_on_challenge": False,
        "copier_owned": True,
    }


def feedback_label_row(
    *,
    ticket: Any,
    symbol: str,
    timing: str = "copy_open",
    note: str = "",
) -> dict[str, Any]:
    """Close-loop LABEL only. ``place`` stays false."""

    return {
        "schema": FEEDBACK_SCHEMA,
        "verb": "LABEL",
        "place": False,
        "never_place": True,
        "timing": timing,
        "ticket": ticket,
        "symbol": symbol,
        "source_login": CHALLENGE_LOGIN,
        "note": note,
        "agent_order_send": False,
        "place_on_challenge": False,
    }


def print_plan(
    event: Mapping[str, Any] | None = None,
    trade_record: Mapping[str, Any] | None = None,
    *,
    ns: str = "redacted_account_f5_minimal",
    login: int = 0,
    price: float = 0.0,
) -> dict[str, Any]:
    """CLI / observer dry plan. Never sends."""

    contract = resolve_copy_contract(
        event,
        trade_record,
        ns=ns,
        login=login,
    )
    payload: dict[str, Any] = contract.as_dict()
    payload["ns"] = ns
    payload["demo_login"] = login
    payload["agent_may_mutate_friend"] = agent_may_mutate_friend(ns=ns, login=login)
    payload["friend_copy_on"] = friend_copy_on(ns=ns, login=login)
    if contract.ok:
        open_req = copy_open_request(
            symbol=contract.symbol,
            side=str(contract.side),
            volume=float(contract.lots or 0),
            sl=float(contract.sl or 0),
            tp=float(contract.tp or 0),
            comment=contract.comment,
            price=float(price or 0),
        )
        payload["open_request"] = open_req
        payload["open_request_has_sl_tp"] = "sl" in open_req and "tp" in open_req
        payload["feedback"] = feedback_label_row(
            ticket=contract.ticket,
            symbol=contract.symbol,
            note="copy_plan",
        )
    if contract.reason == "challenge_source_closed":
        payload["close_friend_only"] = True
        payload["never_flatten_challenge"] = True
        payload["source_closed_from"] = (contract.extra or {}).get("source_closed_from")
    payload["order_send"] = False
    return payload


# Measured 2026-09-21 Challenge fills. Used by CLI --print-plan when no files given.
MEASURED_CHALLENGE_FILLS: tuple[dict[str, Any], ...] = (
    {
        "event": {
            "kind": "fill",
            "ticket": 294088097,
            "symbol": "EURUSD",
            "side": "short",
            "source_login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
        },
        "trade_record": {
            "ticket": 294088097,
            "symbol": "EURUSD",
            "side": "SHORT",
            "execution": {
                "broker_position_sl": 1.14844,
                "broker_position_tp": 1.14697,
                "request": {"volume": 0.87},
                "result": {"volume": 0.87},
            },
            "instrumentation": {"gtos_live_flow_execution": {"lots_placed": 0.87}},
            "volume_min": 0.01,
            "volume_step": 0.01,
        },
        "ns": "redacted_account_f5_minimal",
        "login": 0,
        "price": 1.14795,
        "demo_ticket": 546460735,
    },
    {
        "event": {
            "kind": "fill",
            "ticket": 294092360,
            "symbol": "NZDUSD",
            "side": "short",
            "source_login": CHALLENGE_LOGIN,
            "ns": CHALLENGE_NS,
        },
        "trade_record": {
            "ticket": 294092360,
            "symbol": "NZDUSD",
            "side": "SHORT",
            "execution": {
                "broker_position_sl": 0.57318,
                "broker_position_tp": 0.57169,
                "request": {"volume": 1.75},
                "result": {"volume": 1.75},
            },
            "instrumentation": {"gtos_live_flow_execution": {"lots_placed": 1.75}},
            "volume_min": 0.01,
            "volume_step": 0.01,
        },
        "ns": "ftmo_redacted_account_f5_minimal",
        "login": 0,
        "price": 0.57267,
        "demo_ticket": 546460779,
    },
)
