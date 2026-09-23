#!/usr/bin/env python3
"""Sync a gtos.news_calendar.v1 snapshot FROM the live HIGH spine.

Does not invent events. Refuses to write data/news_calendar.json
(the June week of record). Frozen archive is history, not a merge source.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.judgment.news_calendar_sync import (
    DEFAULT_OUT,
    DEFAULT_SPINE,
    JUNE_WEEK_OF_RECORD,
    JuneWeekOfRecordError,
    sync_from_spine,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spine", type=Path, default=DEFAULT_SPINE)
    parser.add_argument("--stub", type=Path, default=None, help="Optional VPS stub for ticket match-only")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.out.resolve() == JUNE_WEEK_OF_RECORD.resolve():
        print("REFUSE: will not overwrite June week-of-record data/news_calendar.json", file=sys.stderr)
        return 2
    try:
        snap = sync_from_spine(
            spine_path=args.spine,
            stub_path=args.stub,
            out_path=args.out,
            write=not args.dry_run,
        )
    except JuneWeekOfRecordError as exc:
        print(f"REFUSE: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "n_events": snap["n_events"],
        "status": snap["status"],
        "invented": False,
        "june_week_of_record_untouched": True,
        "wrote": snap.get("wrote") if not args.dry_run else None,
        "source_spine": snap["source_spine"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
