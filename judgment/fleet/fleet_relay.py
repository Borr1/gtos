#!/usr/bin/env python3
"""Tail Challenge book-event ledgers → fleet_event.v0 outbox. One process.

Subscribe only. Does not place, remint, flatten, or invent tickets.
Source login hard-lock 0; quarantine 0.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from judgment.fleet.common import (  # noqa: E402
    DEFAULT_RELAY_STATE,
    SOURCE_LOGIN,
    append_jsonl,
    atomic_write_json,
    candidate_ledgers,
    load_json,
    login_decision,
    normalize_book_row,
    pick_ledger,
    resolve_outbox,
    validate_fleet_event,
)


def _load_state(path: Path) -> dict:
    return load_json(path, {"offset_bytes": 0, "path": None, "emitted": 0})


def _reset_if_rotated(state: dict, ledger: Path) -> dict:
    size = ledger.stat().st_size
    offset = int(state.get("offset_bytes") or 0)
    if state.get("path") != str(ledger) or offset > size:
        return {"offset_bytes": 0, "path": str(ledger), "emitted": int(state.get("emitted") or 0)}
    state["path"] = str(ledger)
    return state


def relay_once(
    *,
    ledger: Path,
    outbox: Path,
    state_path: Path,
) -> dict:
    state = _reset_if_rotated(_load_state(state_path), ledger)
    emitted = 0
    skipped = 0
    quarantined = 0
    foreign = 0
    invalid = 0
    with ledger.open("rb") as handle:
        handle.seek(int(state.get("offset_bytes") or 0))
        while True:
            line = handle.readline()
            if not line:
                break
            state["offset_bytes"] = handle.tell()
            try:
                row = json.loads(line.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                invalid += 1
                continue
            if not isinstance(row, dict):
                invalid += 1
                continue
            ok, reason = login_decision(row)
            if not ok:
                if reason == "quarantined_login":
                    quarantined += 1
                elif reason == "foreign_login":
                    foreign += 1
                skipped += 1
                continue
            event = normalize_book_row(row)
            if event is None:
                skipped += 1
                continue
            errors = validate_fleet_event(event)
            if errors:
                invalid += 1
                continue
            append_jsonl(outbox, event)
            emitted += 1
            state["emitted"] = int(state.get("emitted") or 0) + 1
    atomic_write_json(state_path, state)
    return {
        "ok": True,
        "ledger": str(ledger),
        "outbox": str(outbox),
        "offset": state["offset_bytes"],
        "emitted": emitted,
        "skipped": skipped,
        "quarantined": quarantined,
        "foreign": foreign,
        "invalid": invalid,
        "source_login": SOURCE_LOGIN,
        "place": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="process new lines and exit (cron)")
    parser.add_argument("--follow", action="store_true", help="one process; poll for new lines")
    parser.add_argument("--sleep-s", type=float, default=2.0)
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--outbox", type=Path, default=None)
    parser.add_argument("--state", type=Path, default=DEFAULT_RELAY_STATE)
    args = parser.parse_args(argv)

    if not args.once and not args.follow:
        args.once = True
    if args.outbox is None:
        args.outbox = resolve_outbox()

    ledger = pick_ledger(args.ledger)
    if ledger is None:
        looked = [str(args.ledger)] if args.ledger else [str(p) for p in candidate_ledgers()]
        print(json.dumps({"ok": False, "reason": "no_book_event_ledger", "looked": looked}))
        return 0

    if args.once and not args.follow:
        print(json.dumps(relay_once(ledger=ledger, outbox=args.outbox, state_path=args.state)))
        return 0

    while True:
        print(json.dumps(relay_once(ledger=ledger, outbox=args.outbox, state_path=args.state)), flush=True)
        time.sleep(max(0.2, float(args.sleep_s)))


if __name__ == "__main__":
    raise SystemExit(main())
