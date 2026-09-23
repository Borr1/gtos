#!/usr/bin/env python3
"""Build side-pair robustness tables from expanded-market proxy-R performance rows."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_side_pair_robustness import (
    EXPANDED_MARKET_SIDE_PAIR_ROBUSTNESS_SURFACE,
    aggregate_side_pair_rows,
    research_boundary,
    side_pair_rows,
    system_side_pair_rows,
)


INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PROXY_R_PERFORMANCE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SIDE_PAIR_ROBUSTNESS"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_PERFORMANCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_side_pair_robustness.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_side_pair_robustness_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
OUTPUT_MANIFEST = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"
ACTIVE_LEDGER = ROUTE_DIR / "ABSOLUTE_NORTH_STAR_ACTIVE_DOCTRINE_LEDGER_2026-05-15.md"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def long_path(path: Path) -> str:
    text = str(path)
    if len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def output_sha256(paths: list[Path]) -> dict[str, str]:
    digest: dict[str, str] = {}
    for path in paths:
        hasher = hashlib.sha256()
        with open(long_path(path), "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        digest[path.name] = hasher.hexdigest()
    return digest


def manifest_entries() -> list[dict[str, str]]:
    entries = [
        (RESULT_PATH, "expanded_market_side_pair_result"),
        (ROW_LEDGER, "expanded_market_side_pair_rows"),
        (AGGREGATE_LEDGER, "expanded_market_side_pair_aggregates"),
        (ISSUE_LEDGER, "expanded_market_side_pair_issues"),
        (SYSTEM_LEDGER, "expanded_market_side_pair_system"),
        (SUMMARY_PATH, "expanded_market_side_pair_summary"),
        (BUILDER_MODULE, "expanded_market_side_pair_builder"),
        (VERIFIER_MODULE, "expanded_market_side_pair_verifier"),
        (HELPER_MODULE, "expanded_market_side_pair_helper"),
        (TEST_MODULE, "expanded_market_side_pair_tests"),
    ]
    return [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_entries()
    existing = manifest.setdefault("artifacts", [])
    new_keys = {(entry["path"], entry["type"]) for entry in entries}
    manifest["artifacts"] = [
        entry for entry in existing if (entry.get("path"), entry.get("type")) not in new_keys
    ] + entries
    manifest["latest_expanded_market_side_pair_robustness"] = {
        "generated_utc": generated_at,
        "files": entries,
        "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
    }
    manifest["last_updated_utc"] = generated_at
    write_json(OUTPUT_MANIFEST, manifest)


def replace_sprint_event(event: dict[str, Any]) -> None:
    kept_lines: list[str] = []
    if SPRINT_LEDGER.exists():
        with open(long_path(SPRINT_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError:
                    kept_lines.append(stripped)
                    continue
                if payload.get("checkpoint") == 217 and payload.get("event") == "expanded_market_side_pair_robustness":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 217 - Expanded-Market Side-Pair Robustness"
    text = ""
    if ACTIVE_LEDGER.exists():
        with open(long_path(ACTIVE_LEDGER), "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    start = text.find(marker)
    if start != -1:
        next_start = text.find("\n## Checkpoint ", start + len(marker))
        text = text[:start].rstrip() + ("\n\n" + text[next_start:].lstrip() if next_start != -1 else "\n")
    addition = f"""
{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 216. Expanded-market proxy-R performance rows were paired LONG versus SHORT by source path, symbol, timeframe, session, horizon, and source component to measure side robustness without creating a new routing layer.

Rows:
- input expanded-market performance rows: {counts['input_performance_rows']}
- paired side-comparison rows: {counts['side_pair_rows']}
- unpaired issue rows: {counts['issue_rows']}
- aggregate side-comparison rows: {counts['aggregate_rows']}
- paired input performance rows: {counts['paired_input_performance_rows']}
- unpaired input performance rows: {counts['unpaired_input_performance_rows']}
- implement side-filter rows: {counts['implement_rows']}
- avoid-intelligence side-pair rows: {counts['avoid_rows']}
- kill side-pair rows: {counts['kill_rows']}
- redesign side-pair rows: {counts['redesign_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: consume these side-pair results into the next numeric robustness plate; do not stop at side-pair inventory.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Side-Pair Robustness",
            "",
            "This checkpoint converts CP216 performance rows into row-preserving LONG-versus-SHORT robustness comparisons across source path, symbol, timeframe, session, horizon, and source component.",
            "",
            "## Counts",
            "",
            f"- Input performance rows: `{counts['input_performance_rows']}`",
            f"- Side-pair rows: `{counts['side_pair_rows']}`",
            f"- Issue rows: `{counts['issue_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Paired input performance rows: `{counts['paired_input_performance_rows']}`",
            f"- Unpaired input performance rows: `{counts['unpaired_input_performance_rows']}`",
            f"- Source paths represented: `{counts['source_path_count']}`",
            f"- Symbols represented: `{counts['symbol_count']}`",
            "",
            "## Decisions",
            "",
            f"`{json.dumps(counts['decision_counts'], sort_keys=True)}`",
            "",
            "## Winner Sides",
            "",
            f"`{json.dumps(counts['winner_side_counts'], sort_keys=True)}`",
            "",
            "## Continuation",
            "",
            "Consume these paired robustness rows into the next numeric robustness plate.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    performance_rows = read_jsonl(INPUT_PERFORMANCE_LEDGER)
    pair_rows, issue_rows = side_pair_rows(performance_rows)
    aggregate_rows = aggregate_side_pair_rows(pair_rows)
    system_rows = system_side_pair_rows(pair_rows, aggregate_rows, issue_rows, len(performance_rows))

    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in pair_rows)
    classes = Counter(row.get("follow_inverse_default_off_avoid_class") for row in pair_rows)
    winner_sides = Counter(row.get("winner_side") for row in pair_rows)
    paired_input_performance_rows = len(pair_rows) * 2
    unpaired_input_performance_rows = len(issue_rows)
    counts = {
        "input_result_ok": bool(input_result.get("ok")),
        "input_performance_rows": len(performance_rows),
        "side_pair_rows": len(pair_rows),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issue_rows),
        "system_rows": len(system_rows),
        "paired_input_performance_rows": paired_input_performance_rows,
        "unpaired_input_performance_rows": unpaired_input_performance_rows,
        "input_rows_accounted_for": paired_input_performance_rows + unpaired_input_performance_rows,
        "source_path_count": len({row.get("source_path") for row in pair_rows}),
        "symbol_count": len({row.get("symbol") for row in pair_rows}),
        "winner_side_counts": dict(sorted(winner_sides.items())),
        "decision_counts": dict(sorted(decisions.items())),
        "class_counts": dict(sorted(classes.items())),
        "implement_rows": sum(str(decision).startswith("IMPLEMENT") for decision in decisions.elements()),
        "avoid_rows": sum("AVOID" in str(decision) for decision in decisions.elements()),
        "kill_rows": sum(str(decision).startswith("KILL") for decision in decisions.elements()),
        "redesign_rows": sum(str(decision).startswith("REDESIGN") for decision in decisions.elements()),
    }

    write_jsonl(ROW_LEDGER, pair_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(ISSUE_LEDGER, issue_rows)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))

    output_files = [ROW_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    result = {
        "ok": True,
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "counts": counts,
        "inputs": {
            "input_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "input_performance_ledger": str(INPUT_PERFORMANCE_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "row_ledger": str(ROW_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "research_boundary": research_boundary(),
        "expanded_market_side_pair_robustness_surface": EXPANDED_MARKET_SIDE_PAIR_ROBUSTNESS_SURFACE,
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 217,
            "event": "expanded_market_side_pair_robustness",
            "generated_utc": generated_at,
            "input_performance_rows": counts["input_performance_rows"],
            "side_pair_rows": counts["side_pair_rows"],
            "aggregate_rows": counts["aggregate_rows"],
            "issue_rows": counts["issue_rows"],
            "paired_input_performance_rows": counts["paired_input_performance_rows"],
            "unpaired_input_performance_rows": counts["unpaired_input_performance_rows"],
            "continuation": "continue to the next numeric robustness plate after side-pair robustness commit.",
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
