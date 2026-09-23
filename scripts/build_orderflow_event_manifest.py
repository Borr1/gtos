#!/usr/bin/env python3
"""Build Databento event-window manifests from GTOS shadow logs.

Research/tooling only. This script does not fetch data by itself; it produces a
disciplined harvest plan that can be reviewed before spending Databento credits.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.orderflow_event_manifest import (  # noqa: E402
    build_payload,
    read_jsonl,
)


DEFAULT_SOURCE = "shadow_logs/candidate_features_log.jsonl"
DEFAULT_OUTPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_EVENT_WINDOW_MANIFEST_OF_DATA_2_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_EVENT_WINDOW_MANIFEST_OF_DATA_2_2026-05-02.md"
)


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    synth = payload["synthesis"]
    lines = [
        "# Orderflow Event Window Manifest",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Summary",
        "",
        synth["summary"],
        "",
        "## Counts",
        "",
        f"- Rows loaded: {payload['inputs']['rows_loaded']}",
        f"- Events selected: {synth['event_count']}",
        f"- Merged fetch groups: {synth['fetch_group_count']}",
        f"- Truncated event windows: {synth['truncated_event_windows']}",
        f"- Symbol counts: {synth['symbol_counts']}",
        f"- Event class counts: {synth['event_class_counts']}",
        "",
        "## Fetch Groups",
        "",
        "| Group | Symbols | Start UTC | End UTC | Events | Classes |",
        "|---|---|---|---:|---:|---|",
    ]
    for group in payload["fetch_groups"]:
        lines.append(
            "| "
            f"{group['group_id']} | "
            f"{','.join(group['databento_symbols'])} | "
            f"{group['start_utc']} | "
            f"{group['end_utc']} | "
            f"{group['event_count']} | "
            f"{group['event_classes']} |"
        )
    lines.extend(
        [
            "",
            "## Ambiguity Ledger",
            "",
            *[f"- {item}" for item in synth["ambiguities"]],
            "",
            "## Open Questions",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["open_questions"], start=1)],
            "",
            "## Next Steps",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["next_steps"], start=1)],
            "",
        ]
    )
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--pre-minutes", type=int, default=60)
    parser.add_argument("--post-minutes", type=int, default=60)
    parser.add_argument("--merge-gap-minutes", type=int, default=15)
    parser.add_argument(
        "--available-end-utc",
        help="Optional Databento availability cap. Events at/after this UTC time are excluded; crossing windows are truncated.",
    )
    parser.add_argument("--candidates-only", action="store_true")
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    source = Path(args.source)
    if not source.exists():
        parser.exit(2, f"source not found: {source}\n")
    rows = read_jsonl(source)
    payload = build_payload(
        rows,
        source_path=source,
        pre_minutes=args.pre_minutes,
        post_minutes=args.post_minutes,
        merge_gap_minutes=args.merge_gap_minutes,
        candidates_only=args.candidates_only,
        available_end_utc=args.available_end_utc,
    )
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        f"events={payload['synthesis']['event_count']} "
        f"fetch_groups={payload['synthesis']['fetch_group_count']} "
        f"symbols={payload['synthesis']['symbol_counts']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
