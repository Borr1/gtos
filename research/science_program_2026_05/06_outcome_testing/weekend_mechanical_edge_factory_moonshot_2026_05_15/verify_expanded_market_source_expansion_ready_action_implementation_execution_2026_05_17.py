#!/usr/bin/env python3
"""Verify expanded-market source-expansion ready action implementation execution."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
IMPL_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION"
ACTION_EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_ACTION_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_EXECUTION"

INPUT_RESULT = ROUTE_DIR / f"{IMPL_PREFIX}_RESULT_2026-05-17.json"
CANDIDATE_LEDGER = ROUTE_DIR / f"{IMPL_PREFIX}_CANDIDATE_LEDGER_2026-05-17.jsonl"
REDESIGN_TASK_LEDGER = ROUTE_DIR / f"{IMPL_PREFIX}_REDESIGN_TASK_LEDGER_2026-05-17.jsonl"
REPLAY_TASK_LEDGER = ROUTE_DIR / f"{IMPL_PREFIX}_REPLAY_TASK_LEDGER_2026-05-17.jsonl"
SOURCE_TASK_LEDGER = ROUTE_DIR / f"{IMPL_PREFIX}_SOURCE_TASK_LEDGER_2026-05-17.jsonl"
READY_ACTION_EXECUTION_LEDGER = ROUTE_DIR / f"{ACTION_EXEC_PREFIX}_READY_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"
MATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_MATCH_LEDGER_2026-05-17.jsonl"
TASK_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_TASK_EXECUTION_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_source_expansion_ready_action_implementation_execution.py",
    ROUTE_DIR / "build_expanded_market_source_expansion_ready_action_implementation_execution_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    EXECUTION_LEDGER,
    MATCH_LEDGER,
    TASK_EXECUTION_LEDGER,
    AGGREGATE_LEDGER,
    ISSUE_LEDGER,
    SYSTEM_LEDGER,
    SUMMARY_PATH,
]


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


def read_text(path: Path) -> str:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def count_jsonl(path: Path) -> int:
    return sum(1 for _ in iter_jsonl(path))


def boundary_ok(row: dict[str, Any]) -> bool:
    boundary = row.get("research_boundary") or {}
    return (
        boundary.get("boundary_schema") == "concrete_branch_local_research_boundary_v1"
        and boundary.get("artifact_scope") == "branch_local_research"
        and boundary.get("production_import_path") is False
        and boundary.get("mutates_order_risk_prompt_safety_or_mt5") is False
        and boundary.get("runtime_candidate_use_permitted") is False
        and boundary.get("unconditional_scalar_use_permitted") is False
    )


def blocked_terms() -> list[str]:
    return [
        "NO_" + "PROMOTION_" + "VERDICT",
        "validation" + "_safe",
        "outcome_" + "review_" + "opened",
        "live_" + "effect",
        "safe" + "_flags",
        "owner_" + "r",
        "broker_" + "r",
        "exact_" + "live_" + "r",
        "live_" + "account_" + "truth",
    ]


def scan_blocked_terms(paths: list[Path]) -> list[str]:
    issues: list[str] = []
    for path in paths:
        text = read_text(path)
        for term in blocked_terms():
            if term in text:
                issues.append(f"blocked term {term!r} found in {path.relative_to(REPO)}")
    return issues


def main() -> None:
    issues: list[str] = []
    input_result = read_json(INPUT_RESULT)
    result = read_json(RESULT_PATH)
    counts = result.get("counts") or {}
    candidate_count = count_jsonl(CANDIDATE_LEDGER)
    ready_count = count_jsonl(READY_ACTION_EXECUTION_LEDGER)
    expected_task_count = (
        count_jsonl(REDESIGN_TASK_LEDGER)
        + count_jsonl(REPLAY_TASK_LEDGER)
        + count_jsonl(SOURCE_TASK_LEDGER)
    )
    execution_rows = list(iter_jsonl(EXECUTION_LEDGER))
    match_rows = list(iter_jsonl(MATCH_LEDGER))
    task_rows = list(iter_jsonl(TASK_EXECUTION_LEDGER))
    aggregate_rows = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))
    execution_ids = {
        str(row.get("expanded_market_source_expansion_ready_action_implementation_execution_row_id") or "")
        for row in execution_rows
    }
    match_execution_ids = {
        str(row.get("input_ready_action_implementation_execution_row_id") or "")
        for row in match_rows
    }
    execution_status_counts = Counter(
        row.get("ready_action_implementation_execution_status") for row in execution_rows
    )
    task_type_counts = Counter(row.get("task_execution_type") for row in task_rows)

    if input_result.get("ok") is not True:
        issues.append("input ready-action implementation result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if counts.get("input_ready_action_implementation_result_ok") is not True:
        issues.append("input result-ok count field is not true")
    if counts.get("input_implementation_candidate_rows") != candidate_count:
        issues.append("input candidate count mismatch")
    if counts.get("held_ready_action_execution_rows") != ready_count:
        issues.append("held ready execution count mismatch")
    if counts.get("implementation_execution_rows") != len(execution_rows) or len(execution_rows) != candidate_count:
        issues.append("implementation execution row count mismatch")
    if any(row.get("ready_action_implementation_execution_status") != "SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_EXECUTION_PASS" for row in execution_rows):
        issues.append("one or more implementation executions failed")
    if any(int(row.get("held_ready_action_execution_rows_scanned") or 0) != ready_count for row in execution_rows):
        issues.append("one or more implementation candidates did not scan every ready execution row")
    if any(int(row.get("match_count") or 0) < 1 for row in execution_rows):
        issues.append("one or more implementation executions has no match")
    if counts.get("implementation_execution_pass_rows") != len(execution_rows):
        issues.append("implementation execution pass count mismatch")
    if counts.get("implementation_match_rows") != len(match_rows):
        issues.append("implementation match row count mismatch")
    if not match_execution_ids.issubset(execution_ids):
        issues.append("one or more match rows references an unknown execution row")
    if counts.get("task_execution_rows") != len(task_rows) or len(task_rows) != expected_task_count:
        issues.append("task execution row count mismatch")
    if counts.get("implementation_execution_status_counts") != dict(sorted(execution_status_counts.items())):
        issues.append("implementation execution status count mismatch")
    if counts.get("task_execution_type_counts") != dict(sorted(task_type_counts.items())):
        issues.append("task execution type count mismatch")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(execution_rows) + len(task_rows):
        issues.append("aggregate row counts do not sum to output rows")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    if len(system_rows) != 1 or counts.get("system_rows") != 1:
        issues.append("system ledger must contain one row")
    if any(
        not boundary_ok(row)
        for row in execution_rows
        + match_rows
        + task_rows
        + aggregate_rows
        + issue_rows
        + system_rows
        + [result]
    ):
        issues.append("one or more output rows failed branch-local boundary checks")
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": {
            "implementation_execution_rows": len(execution_rows),
            "implementation_match_rows": len(match_rows),
            "task_execution_rows": len(task_rows),
            "aggregate_rows": len(aggregate_rows),
            "issue_rows": len(issue_rows),
        },
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
