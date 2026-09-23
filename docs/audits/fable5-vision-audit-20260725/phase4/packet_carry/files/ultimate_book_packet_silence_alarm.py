#!/usr/bin/env python3
"""Silence alarm for the ultimate-book runtime learning packet stream.

Read-only. Opens no broker connection, imports nothing from the execution path, and writes only
the report file it is asked to write. Safe to run against a live host's exported logs.

**Why a silence alarm at all.** The packet stream is the only live evidence this programme has.
A book that has stopped emitting looks exactly like a book with nothing to say, and the second is
the normal state -- 4,325 of 99,112 packets in the live window are `cycle_no_candidates`. Nothing
distinguishes "quiet" from "dead" without a calibrated expectation.

**The threshold is measured, not assumed.** The first version of this tool assumed a 60 s grid and
excused weekends on the broker clock. Both were wrong, and running it against the live export is
what showed it: it reported 46 % coverage and 1,633 breaches, which would have been a tool that
cried wolf 1,633 times. What the export actually says (41,270 + 57,840 inter-packet gaps,
2026-06-18..07-25):

    p50      0.0 s   -- packets arrive in bursts; a cycle emits several at once
    p90     60.4 s   -- the poll cadence
    p99    909.6 s   -- a ~15 min idle pattern between M15 bar closes, entirely normal
    > 30 min:  43 gaps (FTMO) and 5 (redacted_account) across 37 days

So the default threshold is **1800 s**, which sits above the M15 idle pattern and below anything
that could be a healthy book. And the book emits on all seven broker weekdays (Sat 7,193 packets,
Sun 5,900) -- there is no weekend to excuse, so this version does not pretend to.

**Derived, not accumulated -- where that actually applies.** A gap analysis is intrinsically
observational, and dressing it up as a set-difference over an invented grid is what produced the
false alarm above. The place set-difference genuinely belongs is the **namespace roster**: a book
that dies completely emits nothing at all and therefore cannot appear in any observed set. Pass
`--expect-namespace` once per book that should be alive; a namespace in the expected set and
absent from the observed set is the loudest signal this tool can produce, and it is the one an
accumulator would silently miss.

Usage:
    python3 scripts/ultimate_book_packet_silence_alarm.py \\
        --packets shadow_logs/ultimate_book_runtime_learning_packets.jsonl \\
        --expect-namespace operator_profile \\
        --expect-namespace redacted_account_live_bee34003

Exit codes: 0 = healthy; 1 = silence, a missing namespace, or rejection markers; 2 = cannot evaluate.
"""

from __future__ import annotations

import argparse
import gzip
import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Measured on vps-export-20260725; see the module docstring for the distribution this comes from.
DEFAULT_SILENCE_THRESHOLD_SECONDS = 1800.0
MEASURED_BASELINE = {
    "source": "vps-export-20260725 ultimate_book_runtime_learning_packets.jsonl.gz",
    "window_utc": "2026-06-18T17:06:50Z..2026-07-25T22:05:28Z",
    "gaps_measured": 99110,
    "p50_seconds": 0.0,
    "p90_seconds": 60.4,
    "p99_seconds": 909.6,
    "note": "p99 is the ~15 min M15 idle pattern, not an outage",
}
REJECTED_EVENT_TYPE = "packet_rejected"


def _open(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def _parse_utc(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _percentile(sorted_values: list[float], fraction: float) -> float:
    if not sorted_values:
        return 0.0
    return sorted_values[min(len(sorted_values) - 1, int(fraction * len(sorted_values)))]


def evaluate(
    packet_path: Path,
    *,
    threshold_seconds: float,
    expected_namespaces: list[str],
) -> dict:
    instants: dict[str, list[datetime]] = defaultdict(list)
    event_counts: dict[str, Counter] = defaultdict(Counter)
    rejected: Counter = Counter()
    unparseable = 0
    total = 0

    with _open(packet_path) as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                unparseable += 1
                continue
            instant = _parse_utc(row.get("created_at_utc"))
            if instant is None:
                unparseable += 1
                continue
            namespace = str(row.get("namespace") or "unattributed")
            instants[namespace].append(instant)
            event_type = str(row.get("event_type"))
            event_counts[namespace][event_type] += 1
            if event_type == REJECTED_EVENT_TYPE:
                rejected[namespace] += 1

    observed = set(instants)
    # The set-difference that matters: a book that died emits nothing and so can never appear
    # in an observed set. Only an independently-declared expected roster can catch that.
    missing_namespaces = sorted(set(expected_namespaces) - observed) if expected_namespaces else []
    unexpected_namespaces = (
        sorted(observed - set(expected_namespaces)) if expected_namespaces else []
    )

    report = {
        "packet_path": str(packet_path),
        "total_lines": total,
        "unparseable_lines": unparseable,
        "threshold_seconds": threshold_seconds,
        "measured_baseline": MEASURED_BASELINE,
        "expected_namespaces": sorted(expected_namespaces),
        "observed_namespaces": sorted(observed),
        "missing_namespaces": missing_namespaces,
        "unexpected_namespaces": unexpected_namespaces,
        "namespaces": {},
        "silent": bool(missing_namespaces),
    }

    for namespace, stamps in sorted(instants.items()):
        stamps.sort()
        gaps = sorted((b - a).total_seconds() for a, b in zip(stamps, stamps[1:]))
        breaches = [
            {
                "from_utc": a.isoformat(),
                "to_utc": b.isoformat(),
                "minutes": round((b - a).total_seconds() / 60.0, 1),
            }
            for a, b in zip(stamps, stamps[1:])
            if (b - a).total_seconds() > threshold_seconds
        ]
        breaches.sort(key=lambda r: -r["minutes"])
        span_seconds = (stamps[-1] - stamps[0]).total_seconds()
        silent_seconds = sum(g for g in gaps if g > threshold_seconds)

        report["namespaces"][namespace] = {
            "packets": len(stamps),
            "first_packet_utc": stamps[0].isoformat(),
            "last_packet_utc": stamps[-1].isoformat(),
            "span_hours": round(span_seconds / 3600.0, 2),
            "gap_p50_seconds": round(statistics.median(gaps), 1) if gaps else None,
            "gap_p90_seconds": round(_percentile(gaps, 0.90), 1) if gaps else None,
            "gap_p99_seconds": round(_percentile(gaps, 0.99), 1) if gaps else None,
            "gap_max_seconds": round(gaps[-1], 1) if gaps else None,
            "silence_breaches": len(breaches),
            "silent_hours": round(silent_seconds / 3600.0, 2),
            "silent_fraction_of_span": (
                round(silent_seconds / span_seconds, 6) if span_seconds > 0 else None
            ),
            "longest_silences": breaches[:20],
            "packet_rejected_markers": rejected.get(namespace, 0),
            "event_type_counts": dict(event_counts[namespace]),
        }
        if breaches:
            report["silent"] = True

    # A rejection marker is not silence, but it is the other way this stream can mislead a reader,
    # and anyone checking one should be shown the other.
    report["total_packet_rejected_markers"] = int(sum(rejected.values()))
    report["healthy"] = (
        not report["silent"] and report["total_packet_rejected_markers"] == 0 and unparseable == 0
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--packets",
        default="shadow_logs/ultimate_book_runtime_learning_packets.jsonl",
        help="packet JSONL (.gz accepted)",
    )
    parser.add_argument(
        "--threshold-seconds",
        type=float,
        default=DEFAULT_SILENCE_THRESHOLD_SECONDS,
        help=f"gap beyond which a stream counts as silent (default {DEFAULT_SILENCE_THRESHOLD_SECONDS:.0f}s, measured)",
    )
    parser.add_argument(
        "--expect-namespace",
        action="append",
        default=[],
        dest="expected_namespaces",
        help="a namespace that MUST be emitting; repeat per book. Absence is reported by set-difference.",
    )
    parser.add_argument("-o", "--output", default=None, help="write the JSON report here")
    ns = parser.parse_args()

    path = Path(ns.packets)
    if not path.is_absolute():
        path = REPO / path
    if not path.is_file():
        print(f"REFUSING: no packet log at {path}", file=sys.stderr)
        return 2

    report = evaluate(
        path,
        threshold_seconds=ns.threshold_seconds,
        expected_namespaces=ns.expected_namespaces,
    )
    text = json.dumps(report, indent=2, sort_keys=True)
    if ns.output:
        out = Path(ns.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(text)

    for namespace in report["missing_namespaces"]:
        print(f"DEAD: {namespace} emitted no packets at all", file=sys.stderr)
    for namespace, block in report["namespaces"].items():
        if block["silence_breaches"]:
            print(
                f"SILENT: {namespace} -- {block['silence_breaches']} gap(s) over "
                f"{ns.threshold_seconds:.0f}s; longest {block['longest_silences'][0]['minutes']} min "
                f"at {block['longest_silences'][0]['from_utc']}",
                file=sys.stderr,
            )
        if block["packet_rejected_markers"]:
            print(
                f"REFUSED: {namespace} -- {block['packet_rejected_markers']} packet_rejected "
                f"marker(s); inspect the .quarantine.jsonl sidecar",
                file=sys.stderr,
            )
    return 0 if report["healthy"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
