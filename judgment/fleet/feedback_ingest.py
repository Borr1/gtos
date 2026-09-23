#!/usr/bin/env python3
"""Ingest one human fleet_feedback.v0 row. LABEL only. CLI only.

No HTTP: this repo has no local-webhook pattern for book/close events.
Chair never places from this path.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from judgment.fleet.common import (  # noqa: E402
    DEFAULT_INBOX,
    FLEET_FEEDBACK_SCHEMA,
    SOURCE_LOGIN,
    append_jsonl,
    miss_type_for_timing,
    timing_enum,
    utc_now,
    validate_fleet_feedback,
)


def build_row(
    *,
    observer_id: str,
    ticket: str,
    timing: str,
    symbol: str = "",
    note: str = "",
    confidence: float | None = None,
    fleet_event_id: str = "",
) -> dict:
    row = {
        "schema": FLEET_FEEDBACK_SCHEMA,
        "ts_utc": utc_now(),
        "observer_id": observer_id,
        "ticket": ticket,
        "symbol": symbol or None,
        "timing": timing,
        "miss_type": miss_type_for_timing(timing),
        "note": note or None,
        "confidence": confidence,
        "fleet_event_id": fleet_event_id or None,
        "source_login": SOURCE_LOGIN,
        "verb": "LABEL",
        "place": False,
    }
    errors = validate_fleet_feedback(row)
    if errors:
        raise ValueError(f"invalid fleet_feedback: {errors}")
    return row


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observer-id", required=True)
    parser.add_argument("--ticket", required=True)
    parser.add_argument("--timing", required=True, choices=timing_enum())
    parser.add_argument("--symbol", default="")
    parser.add_argument("--note", default="")
    parser.add_argument("--confidence", type=float, default=None)
    parser.add_argument("--fleet-event-id", default="")
    parser.add_argument("--inbox", type=Path, default=DEFAULT_INBOX)
    args = parser.parse_args(argv)
    try:
        row = build_row(
            observer_id=args.observer_id,
            ticket=args.ticket,
            timing=args.timing,
            symbol=args.symbol,
            note=args.note,
            confidence=args.confidence,
            fleet_event_id=args.fleet_event_id,
        )
    except ValueError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    append_jsonl(args.inbox, row)
    print(json.dumps({"ok": True, "inbox": str(args.inbox), "row": row, "place": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
