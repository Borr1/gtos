#!/usr/bin/env python3
"""Execute ready-action implementation candidates against held ready executions."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.research_infra.moonshot_expanded_market_source_expansion_ready_action_implementation_execution import (
    EXPANDED_MARKET_SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_EXECUTION,
    aggregate_execution_rows,
    boundary_row,
    implementation_execution_row,
    implementation_match_rows,
    research_boundary,
    status_counts,
    task_execution_row,
)


IMPL_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION"
ACTION_EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_ACTION_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_EXECUTION"

INPUT_RESULT = ROUTE_DIR / f"{IMPL_PREFIX}_RESULT_2026-05-17.json"
CANDIDATE_LEDGER = ROUTE_DIR / f"{IMPL_PREFIX}_CANDIDATE_LEDGER_2026-05-17.jsonl"
REDESIGN_TASK_LEDGER = ROUTE_DIR / f"{IMPL_PREFIX}_REDESIGN_TASK_LEDGER_2026-05-17.jsonl"
REPLAY_TASK_LEDGER = ROUTE_DIR / f"{IMPL_PREFIX}_REPLAY_TASK_LEDGER_2026-05-17.jsonl"
SOURCE_TASK_LEDGER = ROUTE_DIR / f"{IMPL_PREFIX}_SOURCE_TASK_LEDGER_2026-05-17.jsonl"
READY_ACTION_EXECUTION_LEDGER = ROUTE_DIR / f"{ACTION_EXEC_PREFIX}_READY_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"

HELPER_MODULE = REPO / "src/research_infra/moonshot_expanded_market_source_expansion_ready_action_implementation_execution.py"
BUILDER_MODULE = Path(__file__)
VERIFIER_MODULE = ROUTE_DIR / "verify_expanded_market_source_expansion_ready_action_implementation_execution_2026_05_17.py"
TEST_MODULE = REPO / "tests/research_infra/test_moonshot_unified_execution_scorer.py"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"
MATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_MATCH_LEDGER_2026-05-17.jsonl"
TASK_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_TASK_EXECUTION_LEDGER_2026-05-17.jsonl"
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


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


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
        (RESULT_PATH, "expanded_market_source_expansion_ready_action_implementation_execution_result"),
        (EXECUTION_LEDGER, "expanded_market_source_expansion_ready_action_implementation_execution_rows"),
        (MATCH_LEDGER, "expanded_market_source_expansion_ready_action_implementation_match_rows"),
        (TASK_EXECUTION_LEDGER, "expanded_market_source_expansion_ready_action_implementation_task_execution_rows"),
        (AGGREGATE_LEDGER, "expanded_market_source_expansion_ready_action_implementation_execution_aggregates"),
        (ISSUE_LEDGER, "expanded_market_source_expansion_ready_action_implementation_execution_issues"),
        (SYSTEM_LEDGER, "expanded_market_source_expansion_ready_action_implementation_execution_system"),
        (SUMMARY_PATH, "expanded_market_source_expansion_ready_action_implementation_execution_summary"),
        (BUILDER_MODULE, "expanded_market_source_expansion_ready_action_implementation_execution_builder"),
        (VERIFIER_MODULE, "expanded_market_source_expansion_ready_action_implementation_execution_verifier"),
        (HELPER_MODULE, "expanded_market_source_expansion_ready_action_implementation_execution_helper"),
        (TEST_MODULE, "expanded_market_source_expansion_ready_action_implementation_execution_tests"),
    ]
    return [
        {"path": str(path.relative_to(REPO)).replace("\\", "/"), "status": "created", "type": kind}
        for path, kind in entries
    ]


def update_manifest(generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST)
    entries = manifest_entries()
    types = {entry["type"] for entry in entries}
    existing = manifest.setdefault("artifacts", [])
    manifest["artifacts"] = [row for row in existing if row.get("type") not in types] + entries
    manifest["latest_expanded_market_source_expansion_ready_action_implementation_execution"] = {
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
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    kept_lines.append(line.rstrip("\n"))
                    continue
                if row.get("event") == event.get("event"):
                    continue
                kept_lines.append(json.dumps(row, sort_keys=True))
    kept_lines.append(json.dumps(event, sort_keys=True))
    write_text(SPRINT_LEDGER, "\n".join(kept_lines) + "\n")


def replace_active_checkpoint(generated_at: str, counts: dict[str, Any]) -> None:
    marker = "## Checkpoint 279 - Expanded-Market Source Expansion Ready Action Implementation Execution"
    text = ACTIVE_LEDGER.read_text(encoding="utf-8", errors="replace") if ACTIVE_LEDGER.exists() else ""
    if marker in text:
        text = text[: text.index(marker)].rstrip() + "\n\n"
    addition = f"""{marker}

Generated: {generated_at}

Trigger: direct continuation after Checkpoint 278. Follow/avoid implementation candidates were executed against every held ready-action execution row; redesign/replay/source implementation tasks were preserved as execution rows.

Rows:
- held ready-action execution rows scanned per candidate: {counts["held_ready_action_execution_rows"]}
- implementation execution rows: {counts["implementation_execution_rows"]}
- implementation match rows: {counts["implementation_match_rows"]}
- task execution rows: {counts["task_execution_rows"]}
- aggregate rows: {counts["aggregate_rows"]}
- issue rows: {counts["issue_rows"]}

Boundary: branch-local research only; no order, risk, prompt, safety, MT5, production import, runtime candidate-use, or unconditional scalar path changed.

Immediate continuation: use passing implementation executions for branch-local follow/avoid code surfaces and preserve task execution rows.
"""
    write_text(ACTIVE_LEDGER, text.rstrip() + "\n\n" + addition)


def build_summary(generated_at: str, counts: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Expanded-Market Source Expansion Ready Action Implementation Execution",
            "",
            f"Generated: {generated_at}",
            "",
            "This checkpoint executes CP278 implementation candidates against held ready-action execution rows.",
            "",
            f"- Implementation execution rows: `{counts['implementation_execution_rows']}`",
            f"- Implementation match rows: `{counts['implementation_match_rows']}`",
            f"- Task execution rows: `{counts['task_execution_rows']}`",
            f"- Issue rows: `{counts['issue_rows']}`",
            "",
        ]
    )


def main() -> None:
    generated_at = now_utc()
    input_result = read_json(INPUT_RESULT)
    candidates = list(iter_jsonl(CANDIDATE_LEDGER))
    ready_rows = list(iter_jsonl(READY_ACTION_EXECUTION_LEDGER))
    ready_rows_by_id = {
        str(row.get("expanded_market_source_expansion_rule_match_ready_action_execution_row_id") or ""): row
        for row in ready_rows
    }
    task_sources = [
        ("redesign_implementation_task", list(iter_jsonl(REDESIGN_TASK_LEDGER))),
        ("replay_implementation_task", list(iter_jsonl(REPLAY_TASK_LEDGER))),
        ("source_implementation_task", list(iter_jsonl(SOURCE_TASK_LEDGER))),
    ]
    execution_rows: list[dict[str, Any]] = []
    match_rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for candidate in candidates:
        execution = implementation_execution_row(candidate, ready_rows, len(execution_rows) + 1)
        execution_rows.append(execution)
        match_rows.extend(
            implementation_match_rows(candidate, execution, ready_rows_by_id, len(match_rows) + 1)
        )
        if execution.get("ready_action_implementation_execution_status") != "SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_EXECUTION_PASS":
            issues.append(
                boundary_row(
                    {
                        "expanded_market_source_expansion_ready_action_implementation_execution_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-READY-ACTION-IMPL-EXEC-ISSUE-{len(issues) + 1:07d}"
                        ),
                        "issue_type": "READY_ACTION_IMPLEMENTATION_EXECUTION_REPAIR_REQUIRED",
                        "input_ready_action_implementation_candidate_row_id": candidate.get(
                            "expanded_market_source_expansion_ready_action_implementation_candidate_row_id"
                        ),
                        "match_count": execution.get("match_count"),
                        "cost_mismatch_count": execution.get("cost_mismatch_count"),
                        "stress_mismatch_count": execution.get("stress_mismatch_count"),
                    }
                )
            )

    task_execution_rows: list[dict[str, Any]] = []
    for task_type, rows in task_sources:
        for row in rows:
            task_execution_rows.append(task_execution_row(row, task_type, len(task_execution_rows) + 1))
    aggregate_rows = aggregate_execution_rows(execution_rows, task_execution_rows)
    counts = {
        "input_ready_action_implementation_result_ok": input_result.get("ok"),
        "input_implementation_candidate_rows": len(candidates),
        "held_ready_action_execution_rows": len(ready_rows),
        "implementation_execution_rows": len(execution_rows),
        "implementation_execution_pass_rows": sum(
            1
            for row in execution_rows
            if row.get("ready_action_implementation_execution_status")
            == "SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_EXECUTION_PASS"
        ),
        "implementation_match_rows": len(match_rows),
        "task_execution_rows": len(task_execution_rows),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issues),
        "system_rows": 1,
        "total_negative_mismatch_scans": sum(
            int(row.get("negative_mismatch_count") or 0) for row in execution_rows
        ),
        "implementation_execution_status_counts": status_counts(
            execution_rows, "ready_action_implementation_execution_status"
        ),
        "task_execution_type_counts": status_counts(task_execution_rows, "task_execution_type"),
    }
    system_rows = [
        boundary_row(
            {
                "expanded_market_source_expansion_ready_action_implementation_execution_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-READY-ACTION-IMPL-EXEC-SYSTEM-0001"
                ),
                **counts,
                "metadata": {
                    "candidate_ledger": str(CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "ready_action_execution_ledger": str(READY_ACTION_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
                    "no_top_n_cutoff": True,
                },
            }
        )
    ]
    output_files = [
        EXECUTION_LEDGER,
        MATCH_LEDGER,
        TASK_EXECUTION_LEDGER,
        AGGREGATE_LEDGER,
        ISSUE_LEDGER,
        SYSTEM_LEDGER,
        SUMMARY_PATH,
    ]
    write_jsonl(EXECUTION_LEDGER, execution_rows)
    write_jsonl(MATCH_LEDGER, match_rows)
    write_jsonl(TASK_EXECUTION_LEDGER, task_execution_rows)
    write_jsonl(AGGREGATE_LEDGER, aggregate_rows)
    write_jsonl(ISSUE_LEDGER, issues)
    write_jsonl(SYSTEM_LEDGER, system_rows)
    write_text(SUMMARY_PATH, build_summary(generated_at, counts))
    result = {
        "artifact": PREFIX,
        "generated_utc": generated_at,
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "inputs": {
            "ready_action_implementation_result": str(INPUT_RESULT.relative_to(REPO)).replace("\\", "/"),
            "implementation_candidate_ledger": str(CANDIDATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "ready_action_execution_ledger": str(READY_ACTION_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "redesign_task_ledger": str(REDESIGN_TASK_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "replay_task_ledger": str(REPLAY_TASK_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "source_task_ledger": str(SOURCE_TASK_LEDGER.relative_to(REPO)).replace("\\", "/"),
        },
        "outputs": {
            "implementation_execution_ledger": str(EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "implementation_match_ledger": str(MATCH_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "task_execution_ledger": str(TASK_EXECUTION_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "aggregate_ledger": str(AGGREGATE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "issue_ledger": str(ISSUE_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "system_ledger": str(SYSTEM_LEDGER.relative_to(REPO)).replace("\\", "/"),
            "summary": str(SUMMARY_PATH.relative_to(REPO)).replace("\\", "/"),
        },
        "output_sha256": output_sha256(output_files),
        "expanded_market_source_expansion_ready_action_implementation_execution_surface": (
            EXPANDED_MARKET_SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_EXECUTION
        ),
        "research_boundary": research_boundary(),
    }
    write_json(RESULT_PATH, result)
    update_manifest(generated_at)
    replace_sprint_event(
        {
            "checkpoint": 279,
            "event": "checkpoint_279_expanded_market_source_expansion_ready_action_implementation_execution",
            "generated_utc": generated_at,
            "result": str(RESULT_PATH.relative_to(REPO)).replace("\\", "/"),
            "counts": counts,
            "boundary": research_boundary(),
        }
    )
    replace_active_checkpoint(generated_at, counts)
    print(json.dumps({"ok": result["ok"], "counts": counts}, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
