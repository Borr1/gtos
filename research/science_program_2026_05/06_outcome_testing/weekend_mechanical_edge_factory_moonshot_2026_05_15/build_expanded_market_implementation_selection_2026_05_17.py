#!/usr/bin/env python3
"""Build implementation-selection rows from expanded-market robustness ledgers."""

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

from src.research_infra.moonshot_expanded_market_implementation_selection import (
    EXPANDED_MARKET_IMPLEMENTATION_SELECTION_SURFACE,
    aggregate_implementation_selection_rows,
    implementation_selection_rows,
    research_boundary,
    system_implementation_selection_rows,
)


SIDE_PAIR_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SIDE_PAIR_ROBUSTNESS"
TEMPORAL_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_TEMPORAL_ROBUSTNESS"
INTRABAR_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_INTRABAR_GEOMETRY"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_IMPLEMENTATION_SELECTION"

SIDE_PAIR_RESULT = ROUTE_DIR / f"{SIDE_PAIR_PREFIX}_RESULT_2026-05-17.json"
SIDE_PAIR_LEDGER = ROUTE_DIR / f"{SIDE_PAIR_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
TEMPORAL_RESULT = ROUTE_DIR / f"{TEMPORAL_PREFIX}_RESULT_2026-05-17.json"
TEMPORAL_LEDGER = ROUTE_DIR / f"{TEMPORAL_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
INTRABAR_RESULT = ROUTE_DIR / f"{INTRABAR_PREFIX}_RESULT_2026-05-17.json"
INTRABAR_LEDGER = ROUTE_DIR / f"{INTRABAR_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_implementation_selection.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_implementation_selection_2026_05_17.py"
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
        (RESULT_PATH, "expanded_market_implementation_selection_result"),
        (ROW_LEDGER, "expanded_market_implementation_selection_rows"),
        (AGGREGATE_LEDGER, "expanded_market_implementation_selection_aggregates"),
        (ISSUE_LEDGER, "expanded_market_implementation_selection_issues"),
        (SYSTEM_LEDGER, "expanded_market_implementation_selection_system"),
        (SUMMARY_PATH, "expanded_market_implementation_selection_summary"),
        (BUILDER_MODULE, "expanded_market_implementation_selection_builder"),
        (VERIFIER_MODULE, "expanded_market_implementation_selection_verifier"),
        (HELPER_MODULE, "expanded_market_implementation_selection_helper"),
        (TEST_MODULE, "expanded_market_implementation_selection_tests"),
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
    manifest["latest_expanded_market_implementation_selection"] = {
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
                if payload.get("checkpoint") == 220 and payload.get("event") == "expanded_market_implementation_selection":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 220 - Expanded-Market Implementation Selection"
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

Trigger: direct continuation after Checkpoint 219. Side-pair, temporal, and intrabar decisions were intersected into concrete branch-local implementation-selection rows.

Rows:
- input side-pair rows: {counts['input_side_pair_rows']}
- temporal input rows: {counts['input_temporal_rows']}
- intrabar input rows: {counts['input_intrabar_rows']}
- implementation-selection rows: {counts['implementation_selection_rows']}
- aggregate selection rows: {counts['aggregate_rows']}
- issue rows: {counts['issue_rows']}
- implement selection rows: {counts['implement_rows']}
- avoid-intelligence selection rows: {counts['avoid_rows']}
- kill selection rows: {counts['kill_rows']}
- redesign selection rows: {counts['redesign_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: materialize implement rows into branch-local code candidates and preserve non-implement rows as row-level avoid, kill, or redesign evidence.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Implementation Selection",
            "",
            "This checkpoint intersects side-pair, temporal, and intrabar decisions into concrete branch-local implementation-selection rows.",
            "",
            "## Counts",
            "",
            f"- Input side-pair rows: `{counts['input_side_pair_rows']}`",
            f"- Input temporal rows: `{counts['input_temporal_rows']}`",
            f"- Input intrabar rows: `{counts['input_intrabar_rows']}`",
            f"- Implementation-selection rows: `{counts['implementation_selection_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Issue rows: `{counts['issue_rows']}`",
            "",
            "## Decisions",
            "",
            f"`{json.dumps(counts['decision_counts'], sort_keys=True)}`",
            "",
            "## Continuation",
            "",
            "Materialize implement rows into branch-local code candidates and preserve non-implement rows as row-level evidence.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    side_pair_result = read_json(SIDE_PAIR_RESULT)
    temporal_result = read_json(TEMPORAL_RESULT)
    intrabar_result = read_json(INTRABAR_RESULT)
    side_pair_rows = read_jsonl(SIDE_PAIR_LEDGER)
    temporal_rows = read_jsonl(TEMPORAL_LEDGER)
    intrabar_rows = read_jsonl(INTRABAR_LEDGER)
    temporal_by_pair_id = {str(row.get("input_side_pair_robustness_row_id")): row for row in temporal_rows}
    intrabar_by_performance_id = {str(row.get("input_expanded_market_performance_row_id")): row for row in intrabar_rows}

    selection_rows, issue_rows = implementation_selection_rows(
        side_pair_rows,
        temporal_by_pair_id,
        intrabar_by_performance_id,
    )
    aggregate_rows = aggregate_implementation_selection_rows(selection_rows)
    system_rows = system_implementation_selection_rows(selection_rows, aggregate_rows, issue_rows, len(side_pair_rows))
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in selection_rows)
    classes = Counter(row.get("follow_inverse_default_off_avoid_class") for row in selection_rows)
    counts = {
        "input_side_pair_result_ok": bool(side_pair_result.get("ok")),
        "input_temporal_result_ok": bool(temporal_result.get("ok")),
        "input_intrabar_result_ok": bool(intrabar_result.get("ok")),
        "input_side_pair_rows": len(side_pair_rows),
        "input_temporal_rows": len(temporal_rows),
        "input_intrabar_rows": len(intrabar_rows),
        "implementation_selection_rows": len(selection_rows),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issue_rows),
        "system_rows": len(system_rows),
        "source_path_count": len({row.get("source_path") for row in selection_rows}),
        "symbol_count": len({row.get("symbol") for row in selection_rows}),
        "decision_counts": dict(sorted(decisions.items())),
        "class_counts": dict(sorted(classes.items())),
        "implement_rows": sum(str(decision).startswith("IMPLEMENT") for decision in decisions.elements()),
        "avoid_rows": sum("AVOID" in str(decision) for decision in decisions.elements()),
        "kill_rows": sum(str(decision).startswith("KILL") for decision in decisions.elements()),
        "redesign_rows": sum(str(decision).startswith("REDESIGN") for decision in decisions.elements()),
    }

    write_jsonl(ROW_LEDGER, selection_rows)
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
            "side_pair_result": str(SIDE_PAIR_RESULT.relative_to(REPO)).replace("\\", "/"),
            "side_pair_ledger": str(SIDE_PAIR_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "temporal_result": str(TEMPORAL_RESULT.relative_to(REPO)).replace("\\", "/"),
            "temporal_ledger": str(TEMPORAL_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "intrabar_result": str(INTRABAR_RESULT.relative_to(REPO)).replace("\\", "/"),
            "intrabar_ledger": str(INTRABAR_LEDGER.relative_to(REPO)).replace("\\", "/"),
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
        "expanded_market_implementation_selection_surface": EXPANDED_MARKET_IMPLEMENTATION_SELECTION_SURFACE,
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 220,
            "event": "expanded_market_implementation_selection",
            "generated_utc": generated_at,
            "input_side_pair_rows": counts["input_side_pair_rows"],
            "implementation_selection_rows": counts["implementation_selection_rows"],
            "aggregate_rows": counts["aggregate_rows"],
            "issue_rows": counts["issue_rows"],
            "continuation": "continue to branch-local code candidates from implementation-selection rows.",
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
