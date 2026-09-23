"""FRIEND_COPY_CONTRACT_V0 — Challenge printer fills copy in-system onto friends.

Unique file. No broker. No agent-place. No invented 0.01 lot floor.

Challenge ``0`` is the printer. SH / redacted_account / redacted_account copy that fill
(same lots, same SL, same TP, same side, same symbol). redacted_account stays idle.
Verification ``0`` is quarantined.

A Cursor agent does **not** place into friend books. MICRO_LOT 0.01 on a
Challenge 0.87 / 1.75 printer fill is ``agent_place_min_lot``, not a copy.
"""

from __future__ import annotations

from typing import Any, Mapping

from .challenge import CHALLENGE_LOGIN, CHALLENGE_MAGIC, CHALLENGE_NS, VERIFICATION_QUARANTINED

MappingLike = Mapping[str, Any]

SCHEMA = "gtos.judgment.friend_copy_contract.v0"

PRINTER_LOGIN = CHALLENGE_LOGIN
PRINTER_NS = CHALLENGE_NS
PRINTER_MAGIC = CHALLENGE_MAGIC

FRIEND_BOOKS: dict[str, dict[str, str]] = {
    "0": {
        "name": "SH",
        "ns": "redacted_account_f5_minimal",
        "terminal": r"C:\MT5\FTMO_Trial",
    },
    "0": {
        "name": "redacted_account",
        "ns": "ftmo_redacted_account_f5_minimal",
        "terminal": r"C:\MT5\FTMO_redacted_account",
    },
    "1514684855": {
        "name": "redacted_account",
        "ns": "ftmo_redacted_account_f5_minimal",
        "terminal": r"C:\MT5\FTMO_redacted_account",
    },
}
FRIEND_LOGINS = frozenset(FRIEND_BOOKS)
FRIEND_NAMESPACES = frozenset(book["ns"] for book in FRIEND_BOOKS.values())

redacted_account_IDLE = "0"
redacted_account_NS = "redacted_account_live_bee34003"

# Named Challenge printer fills (chair sit). Copy these lots/SL/TP. Do not flatten.
PRINTER_NAMED_FILLS: dict[int, dict[str, Any]] = {
    294088097: {
        "symbol": "EURUSD",
        "side": "SHORT",
        "lots": 0.87,
        "sl": 1.14844,
        "tp": 1.14697,
        "sleeve": "sub_mid_dn_re",
    },
    294092360: {
        "symbol": "NZDUSD",
        "side": "SHORT",
        "lots": 1.75,
        "sl": 0.57318,
        "tp": 0.57169,
        "sleeve": "sub_mid_dn_re",
    },
}
CHAIR_NAMED_OPEN_TICKETS = frozenset(PRINTER_NAMED_FILLS)
CHAIR_NAMED_CLOSED_NO_TOUCH = frozenset({294069721})
LEAVE_ORIG_TICKETS = CHAIR_NAMED_OPEN_TICKETS | CHAIR_NAMED_CLOSED_NO_TOUCH | frozenset({293332188})

# Agent-place leftover MICRO_LOT tickets (10:16Z sit). Not a copy. Do not flatten.
AGENT_PLACE_MIN_LOT_TICKETS = frozenset(
    {546434379, 546434380, 546434381, 546434384, 546434385, 546434386}
)

INVENTED_MIN_LOT = 0.01
LOT_DECIMALS = 2
PRICE_DECIMALS = 5

COPY_KINDS = (
    "in_system_copy",
    "agent_place_min_lot",
    "missing_sl_tp",
    "lots_mismatch",
    "missing_printer",
    "not_a_copy",
)


def _login_text(value: Any) -> str:
    if value is None or value == "":
        return ""
    return str(value).strip()


def _lots(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return round(float(value), LOT_DECIMALS)
    except (TypeError, ValueError):
        return None


def _price(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return round(float(value), PRICE_DECIMALS)
    except (TypeError, ValueError):
        return None


def _side(value: Any) -> str:
    raw = str(value or "").strip().upper()
    if raw in {"SELL", "SHORT", "1"}:
        return "SHORT"
    if raw in {"BUY", "LONG", "0"}:
        return "LONG"
    return raw


def _symbol(value: Any) -> str:
    return str(value or "").strip().upper().replace(".CASH", "").replace("_", "")


def is_friend_login(login: Any) -> bool:
    return _login_text(login) in FRIEND_LOGINS


def is_printer_login(login: Any) -> bool:
    return _login_text(login) == PRINTER_LOGIN


def identity_surface() -> dict[str, Any]:
    return {
        "printer_login": PRINTER_LOGIN,
        "printer_ns": PRINTER_NS,
        "printer_magic": PRINTER_MAGIC,
        "friends": {
            login: {"name": book["name"], "ns": book["ns"]}
            for login, book in FRIEND_BOOKS.items()
        },
        "redacted_account_idle": redacted_account_IDLE,
        "verification_quarantined": VERIFICATION_QUARANTINED,
        "invented_min_lot": INVENTED_MIN_LOT,
        "never_agent_place": True,
        "never_invent_min_lot": True,
    }


def score_copy(
    printer: MappingLike | None,
    friend: MappingLike,
) -> dict[str, Any]:
    """Judge one friend fill against the Challenge printer fill.

    Does not place. Does not invent 0.01. Matching lots + SL + TP is a copy.
    """

    friend_login = _login_text(friend.get("login") or friend.get("account"))
    friend_ns = str(friend.get("ns") or friend.get("namespace") or "")
    friend_lots = _lots(friend.get("lots") or friend.get("volume"))
    friend_sl = _price(friend.get("sl"))
    friend_tp = _price(friend.get("tp"))
    friend_side = _side(friend.get("side"))
    friend_symbol = _symbol(friend.get("symbol"))
    friend_ticket = friend.get("ticket")

    row: dict[str, Any] = {
        "schema": SCHEMA,
        "friend_login": friend_login,
        "friend_name": (FRIEND_BOOKS.get(friend_login) or {}).get("name"),
        "friend_ns": friend_ns,
        "friend_ticket": friend_ticket,
        "friend_lots": friend_lots,
        "friend_sl": friend_sl,
        "friend_tp": friend_tp,
        "friend_side": friend_side,
        "friend_symbol": friend_symbol,
        "printer_login": PRINTER_LOGIN,
        "printer_ticket": None,
        "printer_lots": None,
        "printer_sl": None,
        "printer_tp": None,
        "lots_match": False,
        "sl_match": False,
        "tp_match": False,
        "side_match": False,
        "symbol_match": False,
        "kind": "missing_printer",
        "is_copy": False,
        "agent_place": False,
        "invented_min_lot": False,
        "never_agent_place": True,
        "apply": False,
    }

    if not is_friend_login(friend_login):
        row["kind"] = "not_a_copy"
        row["fail_closed_reason"] = "login_not_friend"
        return row

    src = dict(printer or {})
    if not src:
        comment = str(friend.get("comment") or "")
        for ticket, named in PRINTER_NAMED_FILLS.items():
            if f"fleet:{ticket}" in comment or str(friend.get("source_ticket")) == str(ticket):
                src = {"ticket": ticket, **named}
                break
    if not src:
        return row

    printer_lots = _lots(src.get("lots") or src.get("volume"))
    printer_sl = _price(src.get("sl"))
    printer_tp = _price(src.get("tp"))
    printer_side = _side(src.get("side"))
    printer_symbol = _symbol(src.get("symbol"))
    printer_ticket = src.get("ticket")

    row["printer_ticket"] = printer_ticket
    row["printer_lots"] = printer_lots
    row["printer_sl"] = printer_sl
    row["printer_tp"] = printer_tp
    row["printer_side"] = printer_side
    row["printer_symbol"] = printer_symbol
    row["printer_sleeve"] = src.get("sleeve")

    lots_match = (
        friend_lots is not None
        and printer_lots is not None
        and friend_lots == printer_lots
    )
    sl_present = friend_sl not in (None, 0.0)
    tp_present = friend_tp not in (None, 0.0)
    sl_match = sl_present and printer_sl not in (None, 0.0) and friend_sl == printer_sl
    tp_match = tp_present and printer_tp not in (None, 0.0) and friend_tp == printer_tp
    side_match = bool(friend_side) and friend_side == printer_side
    symbol_match = bool(friend_symbol) and friend_symbol == printer_symbol

    row["lots_match"] = lots_match
    row["sl_match"] = sl_match
    row["tp_match"] = tp_match
    row["side_match"] = side_match
    row["symbol_match"] = symbol_match

    invented = friend_lots == INVENTED_MIN_LOT and printer_lots != INVENTED_MIN_LOT
    row["invented_min_lot"] = invented
    if invented:
        row["kind"] = "agent_place_min_lot"
        row["agent_place"] = True
        row["is_copy"] = False
        return row

    if not sl_present or not tp_present:
        row["kind"] = "missing_sl_tp"
        row["is_copy"] = False
        return row

    if not lots_match:
        row["kind"] = "lots_mismatch"
        row["is_copy"] = False
        return row

    if lots_match and sl_match and tp_match and side_match and symbol_match:
        row["kind"] = "in_system_copy"
        row["is_copy"] = True
        row["agent_place"] = False
        return row

    row["kind"] = "not_a_copy"
    row["is_copy"] = False
    return row
