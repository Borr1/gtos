#!/usr/bin/env python3
"""Verify expanded-market source-expansion ready action implementation."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_ACTION_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
READY_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_READY_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"
REDESIGN_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REDESIGN_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"
REPLAY_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REPLAY_TASK_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"
SOURCE_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_TASK_ACTION_EXECUTION_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_CANDIDATE_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
REDESIGN_TASK_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_TASK_LEDGER_2026-05-17.jsonl"
REPLAY_TASK_LEDGER = ROUTE_DIR / f"{PREFIX}_REPLAY_TASK_LEDGER_2026-05-17.jsonl"
SOURCE_TASK_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_TASK_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_source_expansion_ready_action_implementation.py",
    ROUTE_DIR / "build_expanded_market_source_expansion_ready_action_implementation_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    CANDIDATE_LEDGER,
    SELF_TEST_LEDGER,
    REDESIGN_TASK_LEDGER,
    REPLAY_TASK_LEDGER,
    SOURCE_TASK_LEDGER,
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
    ready_input_count = count_jsonl(READY_EXECUTION_LEDGER)
    redesign_input_count = count_jsonl(REDESIGN_EXECUTION_LEDGER)
    replay_input_count = count_jsonl(REPLAY_EXECUTION_LEDGER)
    source_input_count = count_jsonl(SOURCE_EXECUTION_LEDGER)

    candidate_rows = list(iter_jsonl(CANDIDATE_LEDGER))
    self_test_rows = list(iter_jsonl(SELF_TEST_LEDGER))
    redesign_rows = list(iter_jsonl(REDESIGN_TASK_LEDGER))
    replay_rows = list(iter_jsonl(REPLAY_TASK_LEDGER))
    source_rows = list(iter_jsonl(SOURCE_TASK_LEDGER))
    aggregate_rows = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))
    candidate_ids = {
        str(row.get("expanded_market_source_expansion_ready_action_implementation_candidate_row_id") or "")
        for row in candidate_rows
    }
    self_test_candidate_ids = {
        str(row.get("input_ready_action_implementation_candidate_row_id") or "")
        for row in self_test_rows
    }
    candidate_status_counts = Counter(row.get("ready_action_implementation_status") for row in candidate_rows)
    candidate_decision_counts = Counter(row.get("keep_kill_redesign_implement_decision") for row in candidate_rows)

    if input_result.get("ok") is not True:
        issues.append("input rule-match action execution result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if counts.get("input_rule_match_action_execution_result_ok") is not True:
        issues.append("input result-ok count field is not true")
    if counts.get("input_ready_action_execution_rows") != ready_input_count:
        issues.append("input ready execution count mismatch")
    if counts.get("ready_implementation_candidate_rows") != len(candidate_rows):
        issues.append("candidate row count mismatch")
    if len(candidate_rows) != ready_input_count:
        issues.append("candidates do not preserve every ready execution row")
    if counts.get("implementation_self_test_rows") != len(self_test_rows) or len(self_test_rows) != len(candidate_rows):
        issues.append("self-test count mismatch")
    if candidate_ids != self_test_candidate_ids:
        issues.append("self-tests do not cover every candidate")
    if any(row.get("self_test_status") != "SOURCE_EXPANSION_READY_ACTION_IMPLEMENTATION_SELF_TEST_PASS" for row in self_test_rows):
        issues.append("one or more self-tests failed")
    if counts.get("implementation_self_test_pass_rows") != len(self_test_rows):
        issues.append("self-test pass count mismatch")
    if counts.get("redesign_implementation_task_rows") != len(redesign_rows) or len(redesign_rows) != redesign_input_count:
        issues.append("redesign implementation task count mismatch")
    if counts.get("replay_implementation_task_rows") != len(replay_rows) or len(replay_rows) != replay_input_count:
        issues.append("replay implementation task count mismatch")
    if counts.get("source_implementation_task_rows") != len(source_rows) or len(source_rows) != source_input_count:
        issues.append("source implementation task count mismatch")
    if counts.get("candidate_status_counts") != dict(sorted(candidate_status_counts.items())):
        issues.append("candidate status count mismatch")
    if counts.get("candidate_decision_counts") != dict(sorted(candidate_decision_counts.items())):
        issues.append("candidate decision count mismatch")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != (
        len(candidate_rows) + len(redesign_rows) + len(replay_rows) + len(source_rows)
    ):
        issues.append("aggregate row counts do not sum to output rows")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    if len(system_rows) != 1 or counts.get("system_rows") != 1:
        issues.append("system ledger must contain one row")
    if any(
        not boundary_ok(row)
        for row in candidate_rows
        + self_test_rows
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
            "ready_implementation_candidate_rows": len(candidate_rows),
            "implementation_self_test_rows": len(self_test_rows),
            "redesign_implementation_task_rows": len(redesign_rows),
            "replay_implementation_task_rows": len(replay_rows),
            "source_implementation_task_rows": len(source_rows),
            "issue_rows": len(issue_rows),
        },
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
