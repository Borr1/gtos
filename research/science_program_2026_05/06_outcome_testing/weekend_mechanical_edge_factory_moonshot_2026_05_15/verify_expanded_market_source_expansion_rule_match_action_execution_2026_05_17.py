#!/usr/bin/env python3
"""Verify expanded-market source-expansion rule match action execution."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
ACTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_ACTION_APPLICATION"
PERFORMANCE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_PERFORMANCE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_ACTION_EXECUTION"

ACTION_RESULT = ROUTE_DIR / f"{ACTION_PREFIX}_RESULT_2026-05-17.json"
ACTION_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_ACTION_LEDGER_2026-05-17.jsonl"
REPLAY_ACTION_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_REPLAY_TASK_ACTION_LEDGER_2026-05-17.jsonl"
SOURCE_ACTION_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_SOURCE_TASK_ACTION_LEDGER_2026-05-17.jsonl"
PERFORMANCE_LEDGER = ROUTE_DIR / f"{PERFORMANCE_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
READY_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_READY_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"
READY_MATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_READY_ACTION_MATCH_LEDGER_2026-05-17.jsonl"
REDESIGN_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"
REPLAY_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REPLAY_TASK_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"
SOURCE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_TASK_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

READY_ACTION_STATUSES = {
    "SOURCE_EXPANSION_RULE_MATCH_ACTION_FOLLOW_READY",
    "SOURCE_EXPANSION_RULE_MATCH_ACTION_AVOID_READY",
}

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_source_expansion_rule_match_action_execution.py",
    ROUTE_DIR / "build_expanded_market_source_expansion_rule_match_action_execution_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    READY_EXECUTION_LEDGER,
    READY_MATCH_LEDGER,
    REDESIGN_EXECUTION_LEDGER,
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
    action_result = read_json(ACTION_RESULT)
    result = read_json(RESULT_PATH)
    counts = result.get("counts") or {}
    action_rows = list(iter_jsonl(ACTION_LEDGER))
    ready_action_count = sum(
        1 for row in action_rows if row.get("rule_match_action_status") in READY_ACTION_STATUSES
    )
    redesign_action_count = len(action_rows) - ready_action_count
    performance_count = count_jsonl(PERFORMANCE_LEDGER)
    replay_action_count = count_jsonl(REPLAY_ACTION_LEDGER)
    source_action_count = count_jsonl(SOURCE_ACTION_LEDGER)

    ready_rows = list(iter_jsonl(READY_EXECUTION_LEDGER))
    match_rows = list(iter_jsonl(READY_MATCH_LEDGER))
    redesign_rows = list(iter_jsonl(REDESIGN_EXECUTION_LEDGER))
    replay_rows = list(iter_jsonl(REPLAY_EXECUTION_LEDGER))
    source_rows = list(iter_jsonl(SOURCE_EXECUTION_LEDGER))
    aggregate_rows = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))
    ready_ids = {
        str(row.get("expanded_market_source_expansion_rule_match_ready_action_execution_row_id") or "")
        for row in ready_rows
    }
    match_ready_ids = {str(row.get("input_ready_action_execution_row_id") or "") for row in match_rows}
    ready_status_counts = Counter(row.get("ready_action_execution_status") for row in ready_rows)
    redesign_status_counts = Counter(row.get("redesign_action_execution_status") for row in redesign_rows)

    if action_result.get("ok") is not True:
        issues.append("input rule-match action result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if counts.get("input_rule_match_action_result_ok") is not True:
        issues.append("input result-ok count field is not true")
    if counts.get("input_rule_match_action_rows") != len(action_rows):
        issues.append("input action row count mismatch")
    if counts.get("held_performance_rows") != performance_count:
        issues.append("held performance row count mismatch")
    if counts.get("ready_action_rows") != ready_action_count:
        issues.append("ready action count mismatch")
    if counts.get("ready_action_execution_rows") != len(ready_rows) or len(ready_rows) != ready_action_count:
        issues.append("ready action execution row count mismatch")
    if any(row.get("ready_action_execution_status") != "SOURCE_EXPANSION_RULE_MATCH_READY_ACTION_EXECUTION_PASS" for row in ready_rows):
        issues.append("one or more ready action executions failed")
    if any(int(row.get("held_performance_rows_scanned") or 0) != performance_count for row in ready_rows):
        issues.append("one or more ready actions did not scan every held performance row")
    if any(int(row.get("match_count") or 0) < 1 for row in ready_rows):
        issues.append("one or more ready action executions has no matched row")
    if counts.get("ready_action_match_rows") != len(match_rows):
        issues.append("ready action match row count mismatch")
    if not match_ready_ids.issubset(ready_ids):
        issues.append("one or more ready match rows references an unknown ready execution row")
    if counts.get("ready_action_execution_pass_rows") != len(ready_rows):
        issues.append("ready action pass count mismatch")
    if counts.get("ready_action_execution_status_counts") != dict(sorted(ready_status_counts.items())):
        issues.append("ready action status count mismatch")
    if counts.get("redesign_action_execution_rows") != len(redesign_rows) or len(redesign_rows) != redesign_action_count:
        issues.append("redesign action execution count mismatch")
    if any(row.get("redesign_action_execution_status") != "SOURCE_EXPANSION_RULE_MATCH_REDESIGN_ACTION_PRESERVED" for row in redesign_rows):
        issues.append("one or more redesign action execution rows is not preserved")
    if counts.get("redesign_action_execution_status_counts") != dict(sorted(redesign_status_counts.items())):
        issues.append("redesign action status count mismatch")
    if counts.get("replay_task_action_execution_rows") != len(replay_rows) or len(replay_rows) != replay_action_count:
        issues.append("replay task action execution count mismatch")
    if counts.get("source_task_action_execution_rows") != len(source_rows) or len(source_rows) != source_action_count:
        issues.append("source task action execution count mismatch")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != (
        len(ready_rows) + len(redesign_rows) + len(replay_rows) + len(source_rows)
    ):
        issues.append("aggregate row counts do not sum to output rows")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    if len(system_rows) != 1 or counts.get("system_rows") != 1:
        issues.append("system ledger must contain one row")
    if any(
        not boundary_ok(row)
        for row in ready_rows
        + match_rows
        + redesign_rows
        + replay_rows
        + source_rows
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
            "ready_action_execution_rows": len(ready_rows),
            "ready_action_match_rows": len(match_rows),
            "redesign_action_execution_rows": len(redesign_rows),
            "replay_task_action_execution_rows": len(replay_rows),
            "source_task_action_execution_rows": len(source_rows),
            "issue_rows": len(issue_rows),
        },
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
