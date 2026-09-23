"""Bind autonomous friend_copy onto the fleet DemoMirrorAdapter.

Unique file. The in-system copier (fleet observer) owns demo ``order_send``.
Agents never place, close, or resize. ``agent_order_send`` stays false.
The copy is the lots and the SL/TP of the Challenge ticket that is already
open. An empty ticket leaves that copy unset and does not send.
Challenge / redacted_account stay off this path.

Loaded by file path on the host so ``src.judgment.__init__`` is never imported
into the observer process.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Mapping

_BIND_DIR = Path(__file__).resolve().parent
_FRIEND_COPY_PATH = _BIND_DIR / "friend_copy.py"


def _load_friend_choice() -> Any:
    """File-path load. Do not import ``src.judgment`` (package init)."""

    path = _BIND_DIR / "friend_choice.py"
    name = "gtos_friend_choice_standalone"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load friend_choice from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_BOOK_BY_LOGIN = {
    0: "sh",
    0: "redacted_account",
    1514684855: "redacted_account",
}


def _choice_for_open_copy(
    adapter: Any,
    position: Any,
    event: Mapping[str, Any],
    demo_ticket: int,
) -> dict[str, Any]:
    """Ask before any close send. No answer, a tie, or a non-close winner does not send."""

    try:
        choice = _load_friend_choice()
        comment = str(getattr(position, "comment", "") or "")
        source_text = comment.split(":", 1)[1].strip() if comment.startswith("fleet:") else str(event.get("ticket") or "")
        login = int(getattr(adapter, "demo_login", 0) or 0)
        return choice.manage_open_copy(
            book=_BOOK_BY_LOGIN.get(login, ""),
            login=login,
            friend_ticket=int(demo_ticket),
            source_ticket=int(source_text),
            symbol=str(getattr(position, "symbol", "") or event.get("symbol") or ""),
            volume=_open_number(getattr(position, "volume", None)),
            side=_open_side_from_position(position),
            price_open=getattr(position, "price_open", None),
            sl=getattr(position, "sl", None),
            tp=getattr(position, "tp", None),
            profit=getattr(position, "profit", None),
            comment=comment,
            magic=getattr(position, "magic", None),
            printer_close={"ticket": event.get("ticket"), "kind": event.get("kind")},
        )
    except Exception as exc:  # noqa: BLE001 — a failed ask must not flatten
        return {
            "send": False,
            "decision_emitted": False,
            "error": type(exc).__name__,
            "order_send": False,
        }


def _load_friend_copy() -> Any:
    name = "gtos_friend_copy_standalone"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, _FRIEND_COPY_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load friend_copy from {_FRIEND_COPY_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_fc = _load_friend_copy()

FriendCopyError = _fc.FriendCopyError
assert_copy_target = _fc.assert_copy_target
challenge_source_is_closed = _fc.challenge_source_is_closed
copy_close_request = _fc.copy_close_request
copy_open_request = _fc.copy_open_request
copy_sltp_request = _fc.copy_sltp_request
feedback_label_row = _fc.feedback_label_row
fleet_comment = _fc.fleet_comment
load_challenge_trade_record = _fc.load_challenge_trade_record
protection_is_missing = _fc.protection_is_missing
resolve_copy_contract = _fc.resolve_copy_contract
FRIEND_MAGIC = _fc.FRIEND_MAGIC
POSITION_TYPE_BUY = _fc.POSITION_TYPE_BUY

_DONE = {10009, 10010, 10008}


def _result_ok(result: Any) -> bool:
    return getattr(result, "retcode", None) in _DONE


def _result_ticket(result: Any) -> int | None:
    for key in ("order", "deal"):
        value = getattr(result, key, None)
        if value not in (None, 0, "0", ""):
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
    return None


def _tick_price(tick: Any, side: str, *, closing: bool = False) -> float:
    token = str(side).strip().lower()
    buy = token in {"buy", "long", "0"}
    if closing:
        return float(tick.bid if buy else tick.ask)
    return float(tick.ask if buy else tick.bid)


def _fail(adapter: Any, reason: str, event: Mapping[str, Any], *, action: str, **extra: Any) -> dict[str, Any]:
    if hasattr(adapter, "_fail"):
        return adapter._fail(reason, event, action=action, **extra)
    row = {
        "ok": False,
        "reason": reason,
        "action": action,
        "ticket": event.get("ticket"),
        "place_on_challenge": False,
        "order_send": False,
        "agent_order_send": False,
        "redacted_account_idle": True,
        "copier_owned": True,
    }
    row.update(extra)
    return row


def _contract_for(adapter: Any, event: Mapping[str, Any]):
    ticket = event.get("ticket")
    record = load_challenge_trade_record(ticket)
    return resolve_copy_contract(
        event,
        record,
        login=getattr(adapter, "demo_login", None),
        terminal_path=getattr(adapter, "terminal_path", None),
    ), record


def _ticket_key(ticket: Any) -> str:
    return str(ticket)


def _open_side_from_position(position: Any) -> str:
    pos_type = int(getattr(position, "type", POSITION_TYPE_BUY) or 0)
    return "buy" if pos_type == POSITION_TYPE_BUY else "sell"


def _is_friend_copy_position(position: Any) -> bool:
    comment = str(getattr(position, "comment", "") or "")
    magic = int(getattr(position, "magic", 0) or 0)
    return comment.startswith("fleet:") or magic == FRIEND_MAGIC


def _open_number(value: Any) -> float | None:
    """A ticket level. A missing value and zero stay unset."""

    try:
        if value is None or isinstance(value, bool):
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number <= 0 or number == float("inf"):
        return None
    return number


def _first_open_level(rows: Any) -> float | None:
    if not isinstance(rows, list):
        return None
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        number = _open_number(row.get("value"))
        if number is not None:
            return number
    return None


def bind(
    ticket: Mapping[str, Any] | None = None,
    trade_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Lots and SL/TP of the Challenge ticket that is already open.

    An empty ticket leaves the copy unset. This function does not send.
    """

    lots = sl = tp = None
    try:
        event = ticket if isinstance(ticket, Mapping) else None
        record = trade_record if isinstance(trade_record, Mapping) else None
        facts = _fc._volume_facts(event, record)
        legal = facts.get("legal") if isinstance(facts, Mapping) else None
        lots = _first_open_level(legal)
        sl = _first_open_level(_fc._protection_facts(event, record, _fc._PROTECT_SL_KEYS, "sl"))
        tp = _first_open_level(_fc._protection_facts(event, record, _fc._PROTECT_TP_KEYS, "tp"))
    except Exception:  # noqa: BLE001 — an empty ticket must not raise
        lots = sl = tp = None
    return {
        "ok": lots is not None and sl is not None and tp is not None,
        "lots": lots,
        "sl": sl,
        "tp": tp,
        "volume": lots,
        "order_send": False,
        "agent_order_send": False,
        "place_on_challenge": False,
        "copier_owned": True,
    }


def _copy_from_ticket(event: Mapping[str, Any] | None) -> tuple[dict[str, Any], Any]:
    row = event if isinstance(event, Mapping) else None
    ticket = row.get("ticket") if row is not None else None
    record = load_challenge_trade_record(ticket)
    return bind(row, record), record


def _unset_copy(
    *,
    action: str,
    ticket: Any = None,
    copied: Mapping[str, Any] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Empty copy. Lots stay unset. Nothing is sent."""

    levels = copied or {}
    row = {
        "ok": False,
        "reason": None,
        "action": action,
        "ticket": ticket,
        "lots": levels.get("lots"),
        "sl": levels.get("sl"),
        "tp": levels.get("tp"),
        "volume": levels.get("lots"),
        "order_send": False,
        "agent_order_send": False,
        "place_on_challenge": False,
        "copier_owned": True,
    }
    row.update(extra)
    return row


def friend_sync_close(
    adapter: Any,
    event: Mapping[str, Any],
    mapped: Any = None,
) -> dict[str, Any]:
    """Close a friend copy when the Challenge source is done. Never Challenge."""

    try:
        assert_copy_target(
            login=getattr(adapter, "demo_login", None),
            terminal_path=getattr(adapter, "terminal_path", None),
        )
    except FriendCopyError as exc:
        return _fail(
            adapter,
            exc.reason,
            event,
            action="sync_close",
            place_on_challenge=False,
            never_flatten_challenge=True,
        )
    ticket = event.get("ticket")
    key = _ticket_key(ticket)
    if mapped is None and hasattr(adapter, "ticket_map"):
        mapped = adapter.ticket_map.get(key)
    if mapped is None:
        return {
            "ok": True,
            "reason": "no_friend_copy_to_close",
            "action": "sync_close",
            "ticket": ticket,
            "order_send": False,
            "agent_order_send": False,
            "place_on_challenge": False,
            "close_friend_only": True,
        }
    if getattr(adapter, "dry_run", False) or (isinstance(mapped, str) and str(mapped).startswith("dry:")):
        if hasattr(adapter, "ticket_map"):
            adapter.ticket_map.pop(key, None)
        return {
            "ok": True,
            "reason": "dry_run_close",
            "action": "sync_close",
            "ticket": ticket,
            "demo_ticket": mapped,
            "order_send": False,
            "agent_order_send": False,
            "place_on_challenge": False,
            "close_friend_only": True,
            "copier_owned": True,
        }
    mt5 = getattr(adapter, "mt5", None)
    if mt5 is None:
        return _fail(adapter, "mt5_client_required", event, action="sync_close")
    try:
        demo_ticket = int(mapped)
    except (TypeError, ValueError):
        return _fail(adapter, "invalid_mapped_ticket", event, action="sync_close", mapped=mapped)
    positions = mt5.positions_get(ticket=demo_ticket) or ()
    if not positions:
        if hasattr(adapter, "ticket_map"):
            adapter.ticket_map.pop(key, None)
            if hasattr(adapter, "persist"):
                adapter.persist()
        return {
            "ok": True,
            "reason": "demo_position_already_gone",
            "action": "sync_close",
            "ticket": ticket,
            "demo_ticket": demo_ticket,
            "order_send": False,
            "agent_order_send": False,
            "place_on_challenge": False,
            "close_friend_only": True,
        }
    position = positions[0]
    if not _is_friend_copy_position(position):
        return _fail(
            adapter,
            "refuse_non_copy_ticket",
            event,
            action="sync_close",
            demo_ticket=demo_ticket,
            never_flatten_challenge=True,
        )
    choice = _choice_for_open_copy(adapter, position, event, demo_ticket)
    if not choice.get("send"):
        return {
            "ok": True,
            "reason": "choice_left_open",
            "action": "sync_close",
            "ticket": ticket,
            "demo_ticket": demo_ticket,
            "choice": choice.get("choice"),
            "probability": choice.get("probability"),
            "probabilities": choice.get("probabilities"),
            "decision_emitted": bool(choice.get("decision_emitted")),
            "order_send": False,
            "agent_order_send": False,
            "place_on_challenge": False,
            "close_friend_only": True,
            "gesture_flatten": False,
            "error": choice.get("error"),
        }
    symbol = str(getattr(position, "symbol", None) or event.get("symbol") or "")
    if not mt5.symbol_select(symbol, True):
        return _fail(adapter, "symbol_select_failed", event, action="sync_close")
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return _fail(adapter, "no_tick", event, action="sync_close")
    side = _open_side_from_position(position)
    volume = _open_number(getattr(position, "volume", None))
    try:
        price = _open_number(_tick_price(tick, side, closing=True))
    except Exception:  # noqa: BLE001 — an empty ticket must not raise
        price = None
    if volume is None or price is None:
        return _unset_copy(
            action="sync_close",
            ticket=ticket,
            demo_ticket=demo_ticket,
            close_friend_only=True,
        )
    try:
        request = copy_close_request(
            symbol=symbol,
            side=side,
            volume=volume,
            position=demo_ticket,
            price=price,
            comment=f"fleet-close:{ticket}",
        )
    except FriendCopyError:
        return _unset_copy(
            action="sync_close",
            ticket=ticket,
            copied={"lots": volume, "sl": None, "tp": None},
            demo_ticket=demo_ticket,
            close_friend_only=True,
        )
    result = mt5.order_send(request)
    if not _result_ok(result):
        return _fail(
            adapter,
            "order_send_failed",
            event,
            action="sync_close",
            retcode=getattr(result, "retcode", None),
            copier_owned=True,
            close_friend_only=True,
            never_flatten_challenge=True,
        )
    if hasattr(adapter, "ticket_map"):
        adapter.ticket_map.pop(key, None)
        if hasattr(adapter, "persist"):
            adapter.persist()
    return {
        "ok": True,
        "reason": "closed_friend_copy",
        "action": "sync_close",
        "ticket": ticket,
        "demo_ticket": demo_ticket,
        "volume": request["volume"],
        "place_on_challenge": False,
        "agent_order_send": False,
        "copier_owned": True,
        "close_friend_only": True,
        "never_flatten_challenge": True,
        "request": request,
        "feedback": feedback_label_row(ticket=ticket, symbol=symbol, timing="copy_close"),
    }


def friend_sync_fill(adapter: Any, event: Mapping[str, Any]) -> dict[str, Any]:
    """Open with Challenge lots AND Challenge SL/TP, or refuse. Copier-owned."""

    blocked = adapter._preflight(event, action="sync_fill") if hasattr(adapter, "_preflight") else None
    if blocked is not None:
        return blocked
    ticket = event.get("ticket")
    key = _ticket_key(ticket)
    copied, record = _copy_from_ticket(event)
    if not copied["ok"]:
        pending = _unset_copy(action="sync_fill", ticket=ticket, copied=copied)
        pending["trade_record_loaded"] = record is not None
        return pending
    contract, record = _contract_for(adapter, event)
    mapped = adapter.ticket_map.get(key) if hasattr(adapter, "ticket_map") else None
    if not contract.ok:
        if contract.reason == "challenge_source_closed":
            if mapped is not None:
                closed = friend_sync_close(adapter, event, mapped)
                return {
                    "ok": True,
                    "reason": "source_closed_friend_close",
                    "action": "sync_fill",
                    "ticket": ticket,
                    "demo_ticket": mapped,
                    "place_on_challenge": False,
                    "order_send": False,
                    "agent_order_send": False,
                    "copier_owned": True,
                    "close_friend_only": True,
                    "never_flatten_challenge": True,
                    "close": closed,
                    "feedback": feedback_label_row(
                        ticket=ticket,
                        symbol=contract.symbol or str(event.get("symbol") or ""),
                        timing="source_closed",
                    ),
                }
            return _fail(
                adapter,
                "challenge_source_closed",
                event,
                action="sync_fill",
                lots=copied["lots"],
                sl=copied["sl"],
                tp=copied["tp"],
                close_friend_only=True,
                never_flatten_challenge=True,
            )
        return _fail(
            adapter,
            contract.reason,
            event,
            action="sync_fill",
            lots=copied["lots"],
            sl=copied["sl"],
            tp=copied["tp"],
            lots_source=contract.lots_source,
            sl_source=contract.sl_source,
            tp_source=contract.tp_source,
            never_invent_zero_protection=True,
        )
    if mapped is not None:
        levels = friend_sync_levels(adapter, event, mapped, contract=contract)
        return {
            "ok": True,
            "reason": "already_mapped",
            "action": "sync_fill",
            "ticket": ticket,
            "demo_ticket": mapped,
            "volume": copied["lots"],
            "sl": copied["sl"],
            "tp": copied["tp"],
            "place_on_challenge": False,
            "order_send": False,
            "agent_order_send": False,
            "copier_owned": True,
            "levels": levels,
            "feedback": feedback_label_row(ticket=ticket, symbol=contract.symbol, timing="already_mapped"),
        }

    symbol = str(contract.symbol or event.get("symbol") or "")
    side = str(contract.side or event.get("side") or "")
    comment = contract.comment or fleet_comment(ticket)
    if getattr(adapter, "dry_run", False):
        demo_ticket = f"dry:{key}"
        adapter.ticket_map[key] = demo_ticket
        if hasattr(adapter, "persist"):
            adapter.persist()
        price = _open_number(event.get("price"))
        request = None
        if price is not None:
            try:
                request = copy_open_request(
                    symbol=symbol,
                    side=side,
                    volume=copied["lots"],
                    sl=copied["sl"],
                    tp=copied["tp"],
                    comment=comment,
                    price=price,
                )
            except FriendCopyError:
                request = None
        return {
            "ok": True,
            "reason": "dry_run",
            "action": "sync_fill",
            "ticket": ticket,
            "demo_ticket": demo_ticket,
            "volume": copied["lots"],
            "sl": copied["sl"],
            "tp": copied["tp"],
            "comment": comment,
            "symbol": symbol,
            "side": side,
            "place_on_challenge": False,
            "order_send": False,
            "agent_order_send": False,
            "copier_owned": True,
            "request": request,
            "trade_record_loaded": record is not None,
        }

    mt5 = getattr(adapter, "mt5", None)
    if mt5 is None:
        return _fail(adapter, "mt5_client_required", event, action="sync_fill")
    if not mt5.symbol_select(symbol, True):
        return _fail(adapter, "symbol_select_failed", event, action="sync_fill")
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return _fail(adapter, "no_tick", event, action="sync_fill")
    try:
        price = _open_number(_tick_price(tick, side))
    except Exception:  # noqa: BLE001 — an empty ticket must not raise
        price = None
    if price is None:
        return _unset_copy(action="sync_fill", ticket=ticket, copied=copied)
    try:
        request = copy_open_request(
            symbol=symbol,
            side=side,
            volume=copied["lots"],
            sl=copied["sl"],
            tp=copied["tp"],
            comment=comment,
            price=price,
        )
    except FriendCopyError:
        return _unset_copy(action="sync_fill", ticket=ticket, copied=copied)
    if "sl" not in request or "tp" not in request:
        return _unset_copy(action="sync_fill", ticket=ticket, copied=copied)
    result = mt5.order_send(request)
    if not _result_ok(result):
        return _fail(
            adapter,
            "order_send_failed",
            event,
            action="sync_fill",
            retcode=getattr(result, "retcode", None),
            copier_owned=True,
        )
    demo_ticket = _result_ticket(result)
    if demo_ticket is None:
        return _fail(adapter, "missing_demo_ticket", event, action="sync_fill")
    adapter.ticket_map[key] = demo_ticket
    if hasattr(adapter, "persist"):
        adapter.persist()
    return {
        "ok": True,
        "reason": "opened",
        "action": "sync_fill",
        "ticket": ticket,
        "demo_ticket": demo_ticket,
        "volume": copied["lots"],
        "sl": copied["sl"],
        "tp": copied["tp"],
        "comment": comment,
        "symbol": symbol,
        "side": side,
        "place_on_challenge": False,
        "agent_order_send": False,
        "copier_owned": True,
        "request": request,
        "trade_record_loaded": record is not None,
        "feedback": feedback_label_row(ticket=ticket, symbol=symbol, timing="copy_open"),
    }


def friend_sync_levels(
    adapter: Any,
    event: Mapping[str, Any],
    mapped: Any,
    contract: Any = None,
) -> dict[str, Any]:
    """Observer TRADE_ACTION_SLTP from Challenge protection. Not an agent SSH place."""

    copied, _record = _copy_from_ticket(event)
    if not copied["ok"]:
        return _unset_copy(action="sync_levels", ticket=event.get("ticket"), copied=copied)
    if contract is None:
        contract, _record = _contract_for(adapter, event)
    if not contract.ok:
        return {
            "ok": False,
            "reason": contract.reason,
            "lots": copied["lots"],
            "sl": copied["sl"],
            "tp": copied["tp"],
            "order_send": False,
            "agent_order_send": False,
            "place_on_challenge": False,
        }
    sl = copied["sl"]
    tp = copied["tp"]
    if getattr(adapter, "dry_run", False) or (isinstance(mapped, str) and str(mapped).startswith("dry:")):
        return {
            "ok": True,
            "reason": "dry_run",
            "lots": copied["lots"],
            "sl": sl,
            "tp": tp,
            "order_send": False,
            "agent_order_send": False,
            "copier_owned": True,
        }
    mt5 = getattr(adapter, "mt5", None)
    if mt5 is None:
        return {"ok": False, "reason": "mt5_client_required", "order_send": False, "agent_order_send": False}
    try:
        demo_ticket = int(mapped)
    except (TypeError, ValueError):
        return {
            "ok": False,
            "reason": "invalid_mapped_ticket",
            "mapped": mapped,
            "order_send": False,
            "agent_order_send": False,
        }
    positions = mt5.positions_get(ticket=demo_ticket) or ()
    if not positions:
        return {
            "ok": True,
            "reason": "demo_position_already_gone",
            "order_send": False,
            "agent_order_send": False,
        }
    position = positions[0]
    symbol = str(getattr(position, "symbol", None) or contract.symbol or event.get("symbol") or "")
    cur_sl = _open_number(getattr(position, "sl", None))
    cur_tp = _open_number(getattr(position, "tp", None))
    if cur_sl is not None and cur_tp is not None and abs(sl - cur_sl) < 1e-9 and abs(tp - cur_tp) < 1e-9:
        return {
            "ok": True,
            "reason": "levels_already",
            "sl": sl,
            "tp": tp,
            "lots": copied["lots"],
            "order_send": False,
            "agent_order_send": False,
            "copier_owned": True,
        }
    try:
        request = copy_sltp_request(symbol=symbol, position=demo_ticket, sl=sl, tp=tp)
    except FriendCopyError:
        return _unset_copy(action="sync_levels", ticket=event.get("ticket"), copied=copied)
    result = mt5.order_send(request)
    if not _result_ok(result):
        return {
            "ok": False,
            "reason": "sltp_failed",
            "retcode": getattr(result, "retcode", None),
            "lots": copied["lots"],
            "sl": sl,
            "tp": tp,
            "order_send": False,
            "agent_order_send": False,
            "copier_owned": True,
        }
    return {
        "ok": True,
        "reason": "levels_applied",
        "lots": copied["lots"],
        "sl": sl,
        "tp": tp,
        "demo_ticket": demo_ticket,
        "copier_owned": True,
        "agent_order_send": False,
        "place_on_challenge": False,
    }


def protect_open_copies(adapter: Any) -> list[dict[str, Any]]:
    """Protect live copies; close friend zombies when Challenge source is done.

    Copier-owned. Never flattens Challenge / redacted_account tickets.
    """

    mt5 = getattr(adapter, "mt5", None)
    if mt5 is None or getattr(adapter, "dry_run", False):
        return []
    outcomes: list[dict[str, Any]] = []
    mapped = dict(getattr(adapter, "ticket_map", {}) or {})
    comment_hits: dict[str, Any] = {}
    try:
        positions = mt5.positions_get() or ()
    except Exception:  # noqa: BLE001 — protect path must not kill the observer
        return []
    for position in positions:
        comment = str(getattr(position, "comment", "") or "")
        if not comment.startswith("fleet:"):
            continue
        challenge_ticket = comment.split(":", 1)[1].strip()
        if challenge_ticket:
            comment_hits[challenge_ticket] = int(getattr(position, "ticket"))
    keys = set(mapped) | set(comment_hits)
    for key in keys:
        demo_ticket = mapped.get(key, comment_hits.get(key))
        event = {"kind": "fill", "ticket": key, "source_login": _fc.CHALLENGE_LOGIN}
        record = load_challenge_trade_record(key)
        if record:
            event["symbol"] = str(record.get("symbol") or "")
            side = record.get("side") or record.get("direction")
            if side not in (None, ""):
                event["side"] = str(side)
        closed, closed_from = challenge_source_is_closed(event, record)
        if closed:
            row = friend_sync_close(adapter, event, demo_ticket)
            row["ticket"] = key
            row["source_closed_from"] = closed_from
            outcomes.append(row)
            continue
        copied = bind(event, record)
        if not copied["ok"]:
            outcomes.append(_unset_copy(action="sync_levels", ticket=key, copied=copied))
            continue
        contract = resolve_copy_contract(
            event,
            record,
            login=getattr(adapter, "demo_login", None),
            terminal_path=getattr(adapter, "terminal_path", None),
        )
        if not contract.ok:
            outcomes.append(
                {
                    "ok": False,
                    "reason": contract.reason,
                    "ticket": key,
                    "lots": copied["lots"],
                    "sl": copied["sl"],
                    "tp": copied["tp"],
                    "order_send": False,
                    "agent_order_send": False,
                }
            )
            continue
        row = friend_sync_levels(adapter, event, demo_ticket, contract=contract)
        row["ticket"] = key
        outcomes.append(row)
    return outcomes


def install(adapter_cls: Any) -> Any:
    """Patch ``DemoMirrorAdapter.sync_fill`` / ``sync_levels`` / ``sync_close`` / ``connect``."""

    adapter_cls.sync_fill = friend_sync_fill
    adapter_cls.sync_levels = friend_sync_levels
    adapter_cls.sync_close = friend_sync_close
    orig_connect = getattr(adapter_cls, "connect", None)

    def connect(self: Any) -> dict[str, Any]:
        out = orig_connect(self) if callable(orig_connect) else {"ok": True}
        if not getattr(self, "dry_run", False):
            try:
                out["protect"] = protect_open_copies(self)
            except Exception as exc:  # noqa: BLE001 — never take down the observer
                out["protect_error"] = repr(exc)
        return out

    adapter_cls.connect = connect
    adapter_cls._friend_copy_bound = True
    return adapter_cls
