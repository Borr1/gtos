"""Pretty-print JSONL files — one indented JSON object per record.

Usage
-----
    python scripts/view_jsonl.py shadow_logs/j46_j49_shadow_outcomes.jsonl
    python scripts/view_jsonl.py shadow_logs/heartbeat_flatten_events.jsonl --tail 5
    cat shadow_logs/daily_pnl_history.jsonl | python scripts/view_jsonl.py -

Each record is printed with 2-space indent, separated by a `---` divider so
multi-record files are scannable. ``--tail N`` prints only the last N
records (useful for long-running shadow loggers).

This is a viewer only — it never writes back to the file. Run it whenever
the in-VS-Code line-wrap isn't enough (e.g., deeply nested records like
knowledge_base/trade_records/*.json).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _iter_lines(source: str | Path):
    if source == "-":
        for line in sys.stdin:
            yield line
        return
    p = Path(source)
    if not p.exists():
        sys.exit(f"file not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            yield line


def main() -> None:
    ap = argparse.ArgumentParser(description="Pretty-print a JSONL file.")
    ap.add_argument("path", help="Path to the .jsonl file (or '-' for stdin).")
    ap.add_argument(
        "--tail", type=int, default=None,
        help="Print only the last N records (default: all).",
    )
    ap.add_argument(
        "--head", type=int, default=None,
        help="Print only the first N records (default: all).",
    )
    ap.add_argument(
        "--keys", nargs="*",
        help="Print only the listed top-level keys per record (others dropped).",
    )
    ap.add_argument(
        "--write-pretty", action="store_true",
        help=(
            "Write a sibling ``<basename>.pretty.json`` file with a JSON array "
            "of all records (each indented). Open that in VS Code for full "
            "editor view (scroll/search/fold). The .pretty.json files are "
            ".gitignored — they are local-only previews."
        ),
    )
    args = ap.parse_args()

    records: list[dict] = []
    for raw in _iter_lines(args.path):
        raw = raw.strip()
        if not raw:
            continue
        try:
            records.append(json.loads(raw))
        except json.JSONDecodeError as exc:
            # Preserve the unparseable line so the viewer doesn't silently
            # hide format errors — but flag it.
            records.append({"__JSON_DECODE_ERROR__": str(exc), "raw": raw})

    if args.head is not None:
        records = records[: args.head]
    if args.tail is not None:
        records = records[-args.tail :]

    if args.keys:
        records = [{k: r.get(k) for k in args.keys} for r in records]

    if args.write_pretty:
        if args.path == "-":
            sys.exit("--write-pretty requires a file path (not stdin '-').")
        src = Path(args.path)
        # Strip .jsonl/.json suffix and append .pretty.json so the new file
        # gets full JSON syntax highlighting in VS Code.
        stem = src.name
        if stem.endswith(".jsonl"):
            stem = stem[: -len(".jsonl")]
        elif stem.endswith(".json"):
            stem = stem[: -len(".json")]
        out = src.parent / f"{stem}.pretty.json"
        out.write_text(
            json.dumps(records, indent=2, sort_keys=False, default=str),
            encoding="utf-8",
        )
        print(f"Wrote pretty preview: {out}")
        print(f"  records={len(records)}")
        print(f"  open in VS Code: code \"{out}\"")
    else:
        for i, r in enumerate(records):
            if i:
                print("---")
            print(json.dumps(r, indent=2, sort_keys=False, default=str))

    if not records:
        print("(no records)", file=sys.stderr)


if __name__ == "__main__":
    main()
