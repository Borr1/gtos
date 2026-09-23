#!/usr/bin/env python3
"""Verify expanded-market source-expansion rule candidate execution."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
TASK_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_WORK_TASK_MATERIALIZATION"
WORK_RES_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_WORK_RESOLUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_CANDIDATE_EXECUTION"

TASK_RESULT = ROUTE_DIR / f"{TASK_PREFIX}_RESULT_2026-05-17.json"
RULE_LEDGER = ROUTE_DIR / f"{TASK_PREFIX}_RULE_CANDIDATE_LEDGER_2026-05-17.jsonl"
REPLAY_TASK_LEDGER = ROUTE_DIR / f"{TASK_PREFIX}_REPLAY_TASK_LEDGER_2026-05-17.jsonl"
SOURCE_TASK_LEDGER = ROUTE_DIR / f"{TASK_PREFIX}_SOURCE_TASK_LEDGER_2026-05-17.jsonl"
WORK_RES_ROW_LEDGER = ROUTE_DIR / f"{WORK_RES_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RULE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_RULE_EXECUTION_LEDGER_2026-05-17.jsonl"
MATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_MATCH_LEDGER_2026-05-17.jsonl"
REPLAY_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REPLAY_TASK_EXECUTION_LEDGER_2026-05-17.jsonl"
SOURCE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_TASK_EXECUTION_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_source_expansion_rule_candidate_execution.py",
    ROUTE_DIR / "build_expanded_market_source_expansion_rule_candidate_execution_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    RULE_EXECUTION_LEDGER,
    MATCH_LEDGER,
    REPLAY_EXECUTION_LEDGER,
    SOURCE_EXECUTION_LEDGER,
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


def count_jsonl(path: Path) -> int:
    return sum(1 for _ in iter_jsonl(path))


def main() -> None:
    issues: list[str] = []
    task_result = read_json(TASK_RESULT)
    result = read_json(RESULT_PATH)
    counts = result.get("counts") or {}
    rule_count = count_jsonl(RULE_LEDGER)
    replay_count = count_jsonl(REPLAY_TASK_LEDGER)
    source_count = count_jsonl(SOURCE_TASK_LEDGER)
    work_count = count_jsonl(WORK_RES_ROW_LEDGER)

    rule_exec_rows = list(iter_jsonl(RULE_EXECUTION_LEDGER))
    match_rows = list(iter_jsonl(MATCH_LEDGER))
    replay_exec_rows = list(iter_jsonl(REPLAY_EXECUTION_LEDGER))
    source_exec_rows = list(iter_jsonl(SOURCE_EXECUTION_LEDGER))
    aggregate_rows = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))
    status_counts = Counter(row.get("rule_candidate_execution_status") for row in rule_exec_rows)
    rule_exec_ids = {
        str(row.get("expanded_market_source_expansion_rule_candidate_execution_row_id") or "")
        for row in rule_exec_rows
    }
    match_exec_ids = {str(row.get("input_rule_candidate_execution_row_id") or "") for row in match_rows}

    if task_result.get("ok") is not True:
        issues.append("input task-materialization result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if counts.get("candidate_work_resolution_rows") != work_count:
        issues.append("candidate work-resolution count mismatch")
    if counts.get("input_rule_candidate_rows") != rule_count:
        issues.append("input rule candidate count mismatch")
    if counts.get("rule_candidate_execution_rows") != len(rule_exec_rows) or len(rule_exec_rows) != rule_count:
        issues.append("rule candidate execution row count mismatch")
    if len(rule_exec_ids) != len(rule_exec_rows):
        issues.append("rule candidate execution row ids are not unique")
    if any(row.get("rule_candidate_execution_status") != "SOURCE_EXPANSION_RULE_CANDIDATE_EXECUTION_PASS" for row in rule_exec_rows):
        issues.append("one or more rule candidate executions failed")
    if any(int(row.get("candidate_rows_scanned") or 0) != work_count for row in rule_exec_rows):
        issues.append("one or more rule candidate executions did not scan every work-resolution row")
    if any(int(row.get("match_count") or 0) < 1 for row in rule_exec_rows):
        issues.append("one or more rule candidate executions has no match row")
    if not match_exec_ids.issubset(rule_exec_ids):
        issues.append("one or more match rows references an unknown rule execution row")
    if counts.get("match_rows") != len(match_rows):
        issues.append("match row count mismatch")
    if counts.get("replay_task_execution_rows") != len(replay_exec_rows) or len(replay_exec_rows) != replay_count:
        issues.append("replay task execution count mismatch")
    if counts.get("source_task_execution_rows") != len(source_exec_rows) or len(source_exec_rows) != source_count:
        issues.append("source task execution count mismatch")
    if any(row.get("replay_task_execution_status") != "SOURCE_EXPANSION_REPLAY_TASK_EXECUTION_PRESERVED" for row in replay_exec_rows):
        issues.append("one or more replay task execution rows is not preserved")
    if any(row.get("source_task_execution_status") != "SOURCE_EXPANSION_SOURCE_TASK_EXECUTION_PRESERVED" for row in source_exec_rows):
        issues.append("one or more source task execution rows is not preserved")
    if counts.get("rule_candidate_execution_pass_rows") != status_counts.get("SOURCE_EXPANSION_RULE_CANDIDATE_EXECUTION_PASS", 0):
        issues.append("rule execution pass count mismatch")
    if counts.get("execution_status_counts") != dict(sorted(status_counts.items())):
        issues.append("execution status count mismatch")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(rule_exec_rows) + len(replay_exec_rows) + len(source_exec_rows):
        issues.append("aggregate row counts do not sum to output execution rows")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    if len(system_rows) != 1 or counts.get("system_rows") != 1:
        issues.append("system ledger must contain one row")
    if any(
        not boundary_ok(row)
        for row in rule_exec_rows
        + match_rows
        + replay_exec_rows
        + source_exec_rows
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
            "rule_candidate_execution_rows": len(rule_exec_rows),
            "match_rows": len(match_rows),
            "replay_task_execution_rows": len(replay_exec_rows),
            "source_task_execution_rows": len(source_exec_rows),
            "issue_rows": len(issue_rows),
        },
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
