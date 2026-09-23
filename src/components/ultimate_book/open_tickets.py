"""Live open tickets for a question that is about the open book.

The read is the lock-wrapped raw ``positions_get``. An empty result is a
flat book. ``None`` is a failed read. The card says ``none`` or ``unread``.
Question text names a ticket only when that read returned one.
"""

from __future__ import annotations

from typing import Any


def _field(row: Any, name: str) -> Any:
    value = getattr(row, name, None)
    if value is None and isinstance(row, dict):
        value = row.get(name)
    return value


def read_open_positions(raw: Any) -> list[dict[str, Any]] | None:
    """Rows from ``positions_get``. ``None`` when the read did not return rows."""
    if raw is None:
        return None
    fn = getattr(raw, "positions_get", None)
    if not callable(fn):
        return None
    try:
        rows = fn()
    except Exception:
        return None
    if rows is None:
        return None
    positions: list[dict[str, Any]] = []
    for row in rows:
        ticket = _field(row, "ticket")
        try:
            ticket_i: int | None = int(ticket)
        except (TypeError, ValueError):
            ticket_i = None
        symbol = _field(row, "symbol")
        comment = _field(row, "comment")
        positions.append(
            {
                "ticket": ticket_i,
                "symbol": "" if symbol is None else str(symbol),
                "comment": "" if comment is None else str(comment),
            }
        )
    return positions


def read_open_tickets(raw: Any) -> list[int] | None:
    """Tickets from ``positions_get``. ``None`` when the read did not return rows."""
    positions = read_open_positions(raw)
    if positions is None:
        return None
    return [row["ticket"] for row in positions if isinstance(row["ticket"], int)]


def open_ticket_card(raw: Any) -> dict[str, Any]:
    tickets = read_open_tickets(raw)
    if tickets is None:
        return {"open_tickets": "unread"}
    if not tickets:
        return {"open_tickets": "none"}
    return {"open_tickets": tickets}


def question_ticket_text(tickets: list[int] | None) -> str:
    """Empty when the book is flat or the read failed."""
    if not tickets:
        return ""
    if len(tickets) == 1:
        return f"Open ticket {tickets[0]}."
    shown = ", ".join(str(ticket) for ticket in tickets)
    return f"Open tickets {shown}."


def writer_terminal() -> Any:
    """The MetaTrader5 module after the launcher wraps ``positions_get``.

    A missing module is an unread terminal. It is not an empty book.
    """
    try:
        import MetaTrader5 as mt5
    except Exception:
        return None
    if not callable(getattr(mt5, "positions_get", None)):
        return None
    return mt5


def question_with_open_tickets(instructions: str, raw: Any) -> tuple[str, dict[str, Any]]:
    """Card plus question text. A flat or unread book adds no ticket text."""
    card = open_ticket_card(raw)
    tickets = card["open_tickets"]
    named = question_ticket_text(tickets if isinstance(tickets, list) else None)
    text = str(instructions or "").rstrip()
    if named:
        text = f"{text} {named}"
    return text, card
