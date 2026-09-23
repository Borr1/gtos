"""Surgical Challenge book → ``judgment/live/fleet_events.jsonl`` emit.

The Challenge writer (login 0) is the only allowed producer.
This module never places, remints, or talks to a demo terminal.

Exact wire (also in ``FLEET_EVENT_WIRE.md``):

1. **Direct (this module).** After a Challenge fill/close, call
   ``emit_place`` / ``emit_close``. One append. No broker I/O.
2. **Relay (already present, was dormant on VPS).** ``fleet_relay.py``
   tails ``book_event_ledger.jsonl`` / ``book_event_spoken.jsonl`` and
   writes the same outbox. Start it from ``vps_start_workers.ps1``.

Do not import this from ``f5_launch`` activation-token code or
``place_seat_trust`` KEEP tickets. Those files stay untouched.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from judgment.fleet.allowlist import FORBIDDEN_LOGINS, PlaceVeto
from judgment.fleet.common import (
    SOURCE_LOGIN,
    append_jsonl,
    normalize_book_row,
    resolve_outbox,
    validate_fleet_event,
)

PLACE_ALIASES = frozenset({"place", "fill", "open", "opened", "deal_in"})
CLOSE_ALIASES = frozenset({"close", "closed", "deal_out"})


def _require_challenge_source(login: Any) -> int:
    try:
        parsed = int(login)
    except (TypeError, ValueError) as exc:
        raise PlaceVeto("source_login_required", place_on_challenge=False) from exc
    if parsed != SOURCE_LOGIN:
        raise PlaceVeto(
            "source_login_not_challenge",
            login=parsed,
            place_on_challenge=False,
            forbidden_logins=sorted(FORBIDDEN_LOGINS),
        )
    return parsed


def emit_book_event(
    row: Mapping[str, Any],
    *,
    outbox: Path | None = None,
) -> dict[str, Any]:
    """Normalize one Challenge place/close row onto the fleet outbox.

    Returns the written event. Refuses quarantine / foreign logins.
    Never calls MT5.
    """
    payload = dict(row)
    payload.setdefault("source_login", SOURCE_LOGIN)
    payload.setdefault("login", SOURCE_LOGIN)
    _require_challenge_source(payload.get("source_login") or payload.get("login"))
    kind = str(payload.get("kind") or payload.get("event") or payload.get("type") or "").strip().lower()
    if kind in PLACE_ALIASES:
        payload["kind"] = "fill"
    elif kind in CLOSE_ALIASES:
        payload["kind"] = "close"
    event = normalize_book_row(payload)
    if event is None:
        raise PlaceVeto("event_not_normalizable", place_on_challenge=False)
    errors = validate_fleet_event(event)
    if errors:
        raise PlaceVeto("event_invalid", errors=errors, place_on_challenge=False)
    path = resolve_outbox(outbox)
    append_jsonl(path, event)
    return {
        "ok": True,
        "outbox": str(path),
        "event": event,
        "place_on_challenge": False,
        "broker_mutate": False,
    }


def emit_place(
    *,
    ticket: Any,
    symbol: str,
    side: str | None = None,
    sleeve: str | None = None,
    ts_utc: str | None = None,
    outbox: Path | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "kind": "fill",
        "ticket": ticket,
        "symbol": symbol,
        "side": side,
        "sleeve": sleeve,
        "source_login": SOURCE_LOGIN,
        "login": SOURCE_LOGIN,
    }
    if ts_utc:
        row["ts_utc"] = ts_utc
    if extra:
        row.update(dict(extra))
    return emit_book_event(row, outbox=outbox)


def emit_close(
    *,
    ticket: Any,
    symbol: str,
    side: str | None = None,
    sleeve: str | None = None,
    exit_class: str | None = None,
    ts_utc: str | None = None,
    outbox: Path | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "kind": "close",
        "ticket": ticket,
        "symbol": symbol,
        "side": side,
        "sleeve": sleeve,
        "exit_class": exit_class,
        "source_login": SOURCE_LOGIN,
        "login": SOURCE_LOGIN,
    }
    if ts_utc:
        row["ts_utc"] = ts_utc
    if extra:
        row.update(dict(extra))
    return emit_book_event(row, outbox=outbox)
