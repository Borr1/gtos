#!/usr/bin/env python3
"""Verify expanded-market source-expansion rule match action application."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_PERFORMANCE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_ACTION_APPLICATION"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
PERFORMANCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
REPLAY_PERFORMANCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REPLAY_TASK_PERFORMANCE_LEDGER_2026-05-17.jsonl"
SOURCE_PERFORMANCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_TASK_PERFORMANCE_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_ACTION_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_ACTION_SELF_TEST_LEDGER_2026-05-17.jsonl"
REPLAY_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REPLAY_TASK_ACTION_LEDGER_2026-05-17.jsonl"
SOURCE_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_TASK_ACTION_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_source_expansion_rule_match_action_application.py",
    ROUTE_DIR / "build_expanded_market_source_expansion_rule_match_action_application_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    ACTION_LEDGER,
    SELF_TEST_LEDGER,
    REPLAY_ACTION_LEDGER,
    SOURCE_ACTION_LEDGER,
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
    input_performance_count = count_jsonl(PERFORMANCE_LEDGER)
    input_replay_count = count_jsonl(REPLAY_PERFORMANCE_LEDGER)
    input_source_count = count_jsonl(SOURCE_PERFORMANCE_LEDGER)

    action_rows = list(iter_jsonl(ACTION_LEDGER))
    self_test_rows = list(iter_jsonl(SELF_TEST_LEDGER))
    replay_rows = list(iter_jsonl(REPLAY_ACTION_LEDGER))
    source_rows = list(iter_jsonl(SOURCE_ACTION_LEDGER))
    aggregate_rows = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))
    action_ids = {
        str(row.get("expanded_market_source_expansion_rule_match_action_row_id") or "")
        for row in action_rows
    }
    self_test_action_ids = {
        str(row.get("input_rule_match_action_row_id") or "") for row in self_test_rows
    }
    action_status_counts = Counter(row.get("rule_match_action_status") for row in action_rows)
    action_decision_counts = Counter(row.get("keep_kill_redesign_implement_decision") for row in action_rows)

    if input_result.get("ok") is not True:
        issues.append("input rule-match performance result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if counts.get("input_rule_match_performance_result_ok") is not True:
        issues.append("input result-ok count field is not true")
    if counts.get("input_rule_match_performance_rows") != input_performance_count:
        issues.append("input performance row count mismatch")
    if counts.get("rule_match_action_rows") != len(action_rows):
        issues.append("rule match action row count mismatch")
    if len(action_rows) != input_performance_count:
        issues.append("action rows do not preserve every input performance row")
    if counts.get("action_self_test_rows") != len(self_test_rows) or len(self_test_rows) != len(action_rows):
        issues.append("action self-test row count mismatch")
    if action_ids != self_test_action_ids:
        issues.append("self-test rows do not cover every action row")
    if any(row.get("self_test_status") != "SOURCE_EXPANSION_RULE_MATCH_ACTION_SELF_TEST_PASS" for row in self_test_rows):
        issues.append("one or more action self-tests failed")
    if counts.get("action_self_test_pass_rows") != len(self_test_rows):
        issues.append("self-test pass count mismatch")
    if counts.get("replay_task_action_rows") != len(replay_rows) or len(replay_rows) != input_replay_count:
        issues.append("replay task action count mismatch")
    if counts.get("source_task_action_rows") != len(source_rows) or len(source_rows) != input_source_count:
        issues.append("source task action count mismatch")
    if counts.get("action_status_counts") != dict(sorted(action_status_counts.items())):
        issues.append("action status count mismatch")
    if counts.get("action_decision_counts") != dict(sorted(action_decision_counts.items())):
        issues.append("action decision count mismatch")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != (
        len(action_rows) + len(replay_rows) + len(source_rows)
    ):
        issues.append("aggregate row counts do not sum to output action rows")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    if len(system_rows) != 1 or counts.get("system_rows") != 1:
        issues.append("system ledger must contain one row")
    if any(
        not boundary_ok(row)
        for row in action_rows
        + self_test_rows
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
            "rule_match_action_rows": len(action_rows),
            "action_self_test_rows": len(self_test_rows),
            "replay_task_action_rows": len(replay_rows),
            "source_task_action_rows": len(source_rows),
            "aggregate_rows": len(aggregate_rows),
            "issue_rows": len(issue_rows),
        },
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
