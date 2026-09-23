#!/usr/bin/env python3
"""Execute reduced expanded-market surfaces against held implementation-selection rows."""

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

from src.research_infra.moonshot_expanded_market_reduced_surface_execution import (
    EXPANDED_MARKET_REDUCED_SURFACE_EXECUTION,
    aggregate_execution_rows,
    execute_reduced_surfaces,
    reduced_surface_rows,
    research_boundary,
    self_test_rows,
    system_execution_rows,
)


REDUCTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_LEAKAGE_REDUCTION"
SELECTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_IMPLEMENTATION_SELECTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_SURFACE_EXECUTION"

REDUCTION_RESULT = ROUTE_DIR / f"{REDUCTION_PREFIX}_RESULT_2026-05-17.json"
REDUCTION_LEDGER = ROUTE_DIR / f"{REDUCTION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
REDUCTION_MATCH_LEDGER = ROUTE_DIR / f"{REDUCTION_PREFIX}_MATCH_LEDGER_2026-05-17.jsonl"
SELECTION_LEDGER = ROUTE_DIR / f"{SELECTION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_reduced_surface_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_reduced_surface_execution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_SURFACE_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
MATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_MATCH_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
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
        (RESULT_PATH, "expanded_market_reduced_surface_execution_result"),
        (SURFACE_LEDGER, "expanded_market_reduced_surface_rows"),
        (SELF_TEST_LEDGER, "expanded_market_reduced_surface_self_tests"),
        (EXECUTION_LEDGER, "expanded_market_reduced_surface_execution_rows"),
        (MATCH_LEDGER, "expanded_market_reduced_surface_execution_match_rows"),
        (AGGREGATE_LEDGER, "expanded_market_reduced_surface_execution_aggregates"),
        (SYSTEM_LEDGER, "expanded_market_reduced_surface_execution_system"),
        (SUMMARY_PATH, "expanded_market_reduced_surface_execution_summary"),
        (BUILDER_MODULE, "expanded_market_reduced_surface_execution_builder"),
        (VERIFIER_MODULE, "expanded_market_reduced_surface_execution_verifier"),
        (HELPER_MODULE, "expanded_market_reduced_surface_execution_helper"),
        (TEST_MODULE, "expanded_market_reduced_surface_execution_tests"),
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
    manifest["artifacts"] = [entry for entry in existing if (entry.get("path"), entry.get("type")) not in new_keys] + entries
    manifest["latest_expanded_market_reduced_surface_execution"] = {
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
                if payload.get("checkpoint") == 224 and payload.get("event") == "expanded_market_reduced_surface_execution":
                    continue
                kept_lines.append(stripped)
    kept_lines.append(json.dumps(event, sort_keys=True))
    with open(long_path(SPRINT_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 224 - Expanded-Market Reduced Surface Execution"
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

Trigger: direct continuation after Checkpoint 223. Reduced leakage predicates were materialized as branch-local surfaces, self-tested, and executed against held implementation-selection rows.

Rows:
- input leakage-reduction rows: {counts['input_leakage_reduction_rows']}
- input leakage-reduction match rows: {counts['input_leakage_reduction_match_rows']}
- input implementation-selection rows: {counts['input_selection_rows']}
- reduced surface rows: {counts['reduced_surface_rows']}
- self-test rows: {counts['self_test_rows']}
- execution rows: {counts['execution_rows']}
- execution match rows: {counts['execution_match_rows']}
- aggregate rows: {counts['aggregate_rows']}
- execution pass rows: {counts['execution_pass_rows']}
- execution repair rows: {counts['execution_repair_rows']}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: collapse passing reduced executions into row-level branch-local implementation candidates with the replay geometry preserved.
"""
    with open(long_path(ACTIVE_LEDGER), "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text.rstrip() + "\n\n" + addition.strip() + "\n")


def build_summary(counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Reduced Surface Execution",
            "",
            "This checkpoint materializes reduced leakage predicates as executable branch-local surfaces and executes them against held selection rows.",
            "",
            "## Counts",
            "",
            f"- Input leakage-reduction rows: `{counts['input_leakage_reduction_rows']}`",
            f"- Input leakage-reduction match rows: `{counts['input_leakage_reduction_match_rows']}`",
            f"- Input implementation-selection rows: `{counts['input_selection_rows']}`",
            f"- Reduced surface rows: `{counts['reduced_surface_rows']}`",
            f"- Self-test rows: `{counts['self_test_rows']}`",
            f"- Execution rows: `{counts['execution_rows']}`",
            f"- Execution match rows: `{counts['execution_match_rows']}`",
            f"- Aggregate rows: `{counts['aggregate_rows']}`",
            f"- Execution pass rows: `{counts['execution_pass_rows']}`",
            f"- Execution repair rows: `{counts['execution_repair_rows']}`",
            "",
            "## Decisions",
            "",
            f"`{json.dumps(counts['decision_counts'], sort_keys=True)}`",
            "",
            "## Continuation",
            "",
            "Collapse passing reduced executions into row-level branch-local implementation candidates with replay geometry preserved.",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    reduction_result = read_json(REDUCTION_RESULT)
    reduction_rows = read_jsonl(REDUCTION_LEDGER)
    reduction_matches = read_jsonl(REDUCTION_MATCH_LEDGER)
    selections = read_jsonl(SELECTION_LEDGER)
    surfaces = reduced_surface_rows(reduction_rows)
    self_tests = self_test_rows(surfaces, reduction_matches)
    executions, execution_matches = execute_reduced_surfaces(surfaces, selections)
    aggregates = aggregate_execution_rows(executions)
    system_rows = system_execution_rows(surfaces, self_tests, executions, execution_matches, aggregates, len(reduction_rows), len(selections))
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in executions)
    counts = {
        "input_result_ok": bool(reduction_result.get("ok")),
        "input_leakage_reduction_rows": len(reduction_rows),
        "input_leakage_reduction_match_rows": len(reduction_matches),
        "input_selection_rows": len(selections),
        "reduced_surface_rows": len(surfaces),
        "self_test_rows": len(self_tests),
        "execution_rows": len(executions),
        "execution_match_rows": len(execution_matches),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
        "self_test_pass_rows": sum(
            1 for row in self_tests if row.get("self_test_status") == "REDUCED_SURFACE_SELF_TEST_PASS"
        ),
        "execution_pass_rows": sum(
            1 for row in executions if row.get("execution_status") == "REDUCED_SURFACE_EXECUTION_PASS"
        ),
        "execution_repair_rows": sum(
            1 for row in executions if row.get("execution_status") == "REDUCED_SURFACE_EXECUTION_REPAIR"
        ),
        "decision_counts": dict(sorted(decisions.items())),
    }
    write_jsonl(SURFACE_LEDGER, surfaces)
    write_jsonl(SELF_TEST_LEDGER, self_tests)
    write_jsonl(EXECUTION_LEDGER, executions)
    write_jsonl(MATCH_LEDGER, execution_matches)
    write_jsonl(AGGREGATE_LEDGER, aggregates)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(counts))
    output_files = [SURFACE_LEDGER, SELF_TEST_LEDGER, EXECUTION_LEDGER, MATCH_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
    result = {
        "ok": True,
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "counts": counts,
        "inputs": {
            "reduction_result": str(REDUCTION_RESULT.relative_to(REPO)).replace("\\", "/"),
            "reduction_ledger": str(REDUCTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "reduction_match_ledger": str(REDUCTION_MATCH_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "selection_ledger": str(SELECTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "surface_ledger": str(SURFACE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "self_test_ledger": str(SELF_TEST_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "execution_ledger": str(EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "match_ledger": str(MATCH_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "research_boundary": research_boundary(),
        "expanded_market_reduced_surface_execution_surface": EXPANDED_MARKET_REDUCED_SURFACE_EXECUTION,
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 224,
            "event": "expanded_market_reduced_surface_execution",
            "generated_utc": generated_at,
            "input_leakage_reduction_rows": counts["input_leakage_reduction_rows"],
            "reduced_surface_rows": counts["reduced_surface_rows"],
            "execution_rows": counts["execution_rows"],
            "execution_match_rows": counts["execution_match_rows"],
            "aggregate_rows": counts["aggregate_rows"],
            "execution_pass_rows": counts["execution_pass_rows"],
            "execution_repair_rows": counts["execution_repair_rows"],
            "continuation": "continue to row-level branch-local implementation candidates with replay geometry preserved.",
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
