#!/usr/bin/env python3
"""Promote fleet_feedback inbox rows → close_loop LABEL jsonl.

Maps timing → miss_type via fleet_feedback.v0. Appends LABEL only.
Never place / remint / flatten. Does not call MT5 or the Challenge writer.
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
    CLOSE_LOOP_SCHEMA,
    DEFAULT_INBOX,
    DEFAULT_LABELS,
    DEFAULT_PROMOTE_STATE,
    SOURCE_LOGIN,
    append_jsonl,
    atomic_write_json,
    close_loop_miss_type,
    load_json,
    miss_type_for_timing,
    utc_now,
    validate_fleet_feedback,
)


def label_row(feedback: dict) -> dict:
    errors = validate_fleet_feedback(feedback)
    if errors:
        raise ValueError(f"invalid feedback: {errors}")
    timing = str(feedback["timing"])
    mapped = str(feedback.get("miss_type") or miss_type_for_timing(timing))
    observer_id = str(feedback["observer_id"])
    return {
        "schema": CLOSE_LOOP_SCHEMA,
        "verb": "LABEL",
        "never_place": True,
        "never_remint": True,
        "never_flatten": True,
        "place": False,
        "remint": False,
        "flatten": False,
        "source_login": SOURCE_LOGIN,
        "ticket": feedback["ticket"],
        "symbol": feedback.get("symbol"),
        "timing": timing,
        "human_timing_vote": timing,
        "miss_type": mapped,
        "close_loop_miss_type": close_loop_miss_type(mapped),
        "observer_id": observer_id,
        "observer_ids": [observer_id],
        "fleet_event_id": feedback.get("fleet_event_id"),
        "note": feedback.get("note"),
        "confidence": feedback.get("confidence"),
        "ts_utc": utc_now(),
        "feedback_ts_utc": feedback.get("ts_utc"),
        "origin": "gtos.fleet_feedback.v0",
    }


def promote_once(
    *,
    inbox: Path,
    labels: Path,
    state_path: Path,
) -> dict:
    state = load_json(state_path, {"offset_bytes": 0, "path": None, "promoted": 0})
    if not inbox.is_file():
        return {
            "ok": True,
            "reason": "no_inbox",
            "inbox": str(inbox),
            "promoted": 0,
            "place": False,
        }
    size = inbox.stat().st_size
    if state.get("path") != str(inbox) or int(state.get("offset_bytes") or 0) > size:
        state = {"offset_bytes": 0, "path": str(inbox), "promoted": int(state.get("promoted") or 0)}
    promoted = 0
    skipped = 0
    with inbox.open("rb") as handle:
        handle.seek(int(state.get("offset_bytes") or 0))
        while True:
            line = handle.readline()
            if not line:
                break
            state["offset_bytes"] = handle.tell()
            try:
                row = json.loads(line.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                skipped += 1
                continue
            if not isinstance(row, dict):
                skipped += 1
                continue
            try:
                out = label_row(row)
            except ValueError:
                skipped += 1
                continue
            if out.get("verb") != "LABEL" or out.get("place") is True:
                skipped += 1
                continue
            append_jsonl(labels, out)
            promoted += 1
            state["promoted"] = int(state.get("promoted") or 0) + 1
    state["path"] = str(inbox)
    atomic_write_json(state_path, state)
    return {
        "ok": True,
        "inbox": str(inbox),
        "labels": str(labels),
        "promoted": promoted,
        "skipped": skipped,
        "offset": state["offset_bytes"],
        "place": False,
        "verb": "LABEL",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inbox", type=Path, default=DEFAULT_INBOX)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--state", type=Path, default=DEFAULT_PROMOTE_STATE)
    args = parser.parse_args(argv)
    print(json.dumps(promote_once(inbox=args.inbox, labels=args.labels, state_path=args.state)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
