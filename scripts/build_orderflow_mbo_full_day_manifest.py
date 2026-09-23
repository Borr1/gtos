#!/usr/bin/env python3
"""Build UTC-midnight MBO manifests for registered orderflow hypotheses.

Research/tooling only. MBO book reconstruction needs requests that start at
UTC midnight so Databento can provide the synthetic starting book snapshot.
This script converts already-built GTOS event manifests into tight full-day
MBO fetch groups while keeping event features scoped to the original windows.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import timedelta
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.orderflow_event_manifest import iso_utc, parse_utc  # noqa: E402


DEFAULT_INPUT = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_EVENT_WINDOW_MANIFEST_PROXY_EXPANDED_2026-05-02.json"
)
DEFAULT_OUTPUT_JSON = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_NAS100_MBO_FULL_DAY_MANIFEST_2026-05-02.json"
)
DEFAULT_OUTPUT_MD = (
    "research/databento_orderflow_capture_2026-05-02/"
    "ORDERFLOW_NAS100_MBO_FULL_DAY_MANIFEST_2026-05-02.md"
)


def load_json(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_payload(
    source_manifest: dict[str, Any],
    *,
    gtos_symbol: str,
    futures_symbol: str,
    candidate_dates_only: bool,
    include_context_on_candidate_dates: bool,
    end_buffer_minutes: int,
) -> dict[str, Any]:
    source_events = [
        event
        for event in source_manifest.get("events") or []
        if event.get("symbol") == gtos_symbol and futures_symbol in (event.get("databento_symbols") or [])
    ]
    candidate_dates = {
        str(event["canonical_m15_close_utc"])[:10]
        for event in source_events
        if event.get("event_class") == "candidate"
    }
    selected: list[dict[str, Any]] = []
    for event in source_events:
        day = str(event["canonical_m15_close_utc"])[:10]
        if candidate_dates_only and day not in candidate_dates:
            continue
        if not include_context_on_candidate_dates and event.get("event_class") != "candidate":
            continue
        selected.append(event)

    by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in selected:
        by_day[str(event["canonical_m15_close_utc"])[:10]].append(event)

    groups: list[dict[str, Any]] = []
    for day, day_events in sorted(by_day.items()):
        closes = [parse_utc(event["canonical_m15_close_utc"]) for event in day_events]
        day_start = parse_utc(f"{day}T00:00:00+00:00")
        end = max(closes) + timedelta(minutes=end_buffer_minutes)
        groups.append(
            {
                "group_id": f"mbo_{gtos_symbol.lower()}_{futures_symbol.lower().replace('.', '')}_{day.replace('-', '')}",
                "databento_symbols": [futures_symbol],
                "start_utc": iso_utc(day_start),
                "end_utc": iso_utc(end),
                "event_ids": [event["event_id"] for event in sorted(day_events, key=lambda item: item["canonical_m15_close_utc"])],
                "gtos_symbols": [gtos_symbol],
                "event_classes": sorted(Counter(event["event_class"] for event in day_events).items()),
                "event_count": len(day_events),
                "mbo_start_policy": "UTC_MIDNIGHT_SYNTHETIC_BOOK_SNAPSHOT_REQUIRED",
            }
        )

    return {
        "schema_version": "orderflow_mbo_full_day_manifest_v1",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "inputs": {
            "source_manifest_schema_version": source_manifest.get("schema_version"),
            "gtos_symbol": gtos_symbol,
            "futures_symbol": futures_symbol,
            "candidate_dates_only": candidate_dates_only,
            "include_context_on_candidate_dates": include_context_on_candidate_dates,
            "end_buffer_minutes": end_buffer_minutes,
        },
        "events": selected,
        "fetch_groups": groups,
        "synthesis": {
            "summary": (
                "This manifest scopes MBO pulls to NAS100/NQ event dates that contain GTOS candidates. "
                "Each request starts at UTC midnight for Databento synthetic book reconstruction, while "
                "feature extraction remains limited to as-of pre60/event15 event windows."
            ),
            "event_count": len(selected),
            "fetch_group_count": len(groups),
            "candidate_dates": sorted(candidate_dates),
            "event_class_counts": dict(sorted(Counter(event["event_class"] for event in selected).items())),
            "ambiguities": [
                "Raw request coverage includes pre-event dead time from midnight because MBO reconstruction requires the starting book snapshot.",
                "Analysis features must not use data after each event's canonical close.",
                "Context rows are restricted to dates that also contain NAS100 candidates.",
            ],
            "next_steps": [
                "Estimate the MBO groups before fetching.",
                "Execute only if the cost cap passes.",
                "Run the registered no-leak MBO extractor on pre60/event15 windows only.",
            ],
        },
    }


def write_json(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(payload: dict[str, Any], path: Path | str) -> None:
    out = Path(path)
    synth = payload["synthesis"]
    lines = [
        "# NAS100 MBO Full-Day Manifest",
        "",
        "Date: 2026-05-02",
        "Scope: research/tooling only",
        f"Promotion verdict: `{payload['promotion_verdict']}`",
        "",
        "## Synthesis",
        "",
        synth["summary"],
        "",
        "## Coverage",
        "",
        f"- Events: {synth['event_count']}",
        f"- Fetch groups: {synth['fetch_group_count']}",
        f"- Candidate dates: {synth['candidate_dates']}",
        f"- Event class counts: {synth['event_class_counts']}",
        "",
        "## Fetch Groups",
        "",
        "| Group | Start UTC | End UTC | Events | Classes |",
        "|---|---|---|---:|---|",
    ]
    for group in payload["fetch_groups"]:
        lines.append(
            "| "
            f"{group['group_id']} | {group['start_utc']} | {group['end_utc']} | "
            f"{group['event_count']} | {group['event_classes']} |"
        )
    lines.extend(
        [
            "",
            "## Ambiguity Ledger",
            "",
            *[f"- {item}" for item in synth["ambiguities"]],
            "",
            "## Next Steps",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(synth["next_steps"], start=1)],
            "",
        ]
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", default=DEFAULT_INPUT)
    parser.add_argument("--gtos-symbol", default="NAS100")
    parser.add_argument("--futures-symbol", default="NQ.v.0")
    parser.add_argument("--include-all-dates", action="store_true")
    parser.add_argument("--candidates-only", action="store_true")
    parser.add_argument("--end-buffer-minutes", type=int, default=0)
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = build_payload(
        load_json(args.source_manifest),
        gtos_symbol=args.gtos_symbol,
        futures_symbol=args.futures_symbol,
        candidate_dates_only=not args.include_all_dates,
        include_context_on_candidate_dates=not args.candidates_only,
        end_buffer_minutes=args.end_buffer_minutes,
    )
    write_json(payload, args.output_json)
    write_markdown(payload, args.output_md)
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    print(
        f"events={payload['synthesis']['event_count']} "
        f"groups={payload['synthesis']['fetch_group_count']} "
        f"classes={payload['synthesis']['event_class_counts']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
