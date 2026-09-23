#!/usr/bin/env python3
"""Verify expanded-market source-expansion work task materialization."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
WORK_RES_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_WORK_RESOLUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_WORK_TASK_MATERIALIZATION"

WORK_RES_RESULT = ROUTE_DIR / f"{WORK_RES_PREFIX}_RESULT_2026-05-17.json"
WORK_RES_ROW_LEDGER = ROUTE_DIR / f"{WORK_RES_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RULE_LEDGER = ROUTE_DIR / f"{PREFIX}_RULE_CANDIDATE_LEDGER_2026-05-17.jsonl"
RULE_SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_RULE_SELF_TEST_LEDGER_2026-05-17.jsonl"
REPLAY_TASK_LEDGER = ROUTE_DIR / f"{PREFIX}_REPLAY_TASK_LEDGER_2026-05-17.jsonl"
SOURCE_TASK_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_TASK_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_source_expansion_work_task_materialization.py",
    ROUTE_DIR / "build_expanded_market_source_expansion_work_task_materialization_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    RULE_LEDGER,
    RULE_SELF_TEST_LEDGER,
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


def input_status_counts() -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in iter_jsonl(WORK_RES_ROW_LEDGER):
        counts[row.get("work_resolution_status")] += 1
    return counts


def main() -> None:
    issues: list[str] = []
    work_result = read_json(WORK_RES_RESULT)
    result = read_json(RESULT_PATH)
    counts = result.get("counts") or {}
    status_counts = input_status_counts()

    rule_rows = list(iter_jsonl(RULE_LEDGER))
    self_tests = list(iter_jsonl(RULE_SELF_TEST_LEDGER))
    replay_rows = list(iter_jsonl(REPLAY_TASK_LEDGER))
    source_rows = list(iter_jsonl(SOURCE_TASK_LEDGER))
    aggregate_rows = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))
    output_input_ids = (
        {str(row.get("input_work_resolution_row_id") or "") for row in rule_rows}
        | {str(row.get("input_work_resolution_row_id") or "") for row in replay_rows}
        | {str(row.get("input_work_resolution_row_id") or "") for row in source_rows}
    )
    input_ids = {
        str(row.get("expanded_market_source_expansion_action_pack_work_resolution_row_id") or "")
        for row in iter_jsonl(WORK_RES_ROW_LEDGER)
    }
    rule_classes = Counter(row.get("rule_candidate_class") for row in rule_rows)
    decisions = Counter(
        [row.get("keep_kill_redesign_implement_decision") for row in rule_rows]
        + [row.get("keep_kill_redesign_implement_decision") for row in replay_rows]
        + [row.get("keep_kill_redesign_implement_decision") for row in source_rows]
    )

    if work_result.get("ok") is not True:
        issues.append("input work-resolution result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if output_input_ids != input_ids:
        issues.append("task rows do not consume every work-resolution row exactly once")
    if counts.get("input_work_resolution_rows") != len(input_ids):
        issues.append("input work-resolution count mismatch")
    if counts.get("rule_candidate_rows") != len(rule_rows):
        issues.append("rule candidate count mismatch")
    if counts.get("rule_candidate_rows") != status_counts.get("ACTION_PACK_WORK_RESOLUTION_RULE_REDESIGN_NUMERIC_AVAILABLE", 0):
        issues.append("rule candidate count does not match numeric work-resolution rows")
    if counts.get("replay_task_rows") != len(replay_rows):
        issues.append("replay task count mismatch")
    if counts.get("replay_task_rows") != status_counts.get("ACTION_PACK_WORK_RESOLUTION_REPLAY_IMPLEMENTATION_REQUIRED", 0):
        issues.append("replay task count does not match replay-required rows")
    if counts.get("source_task_rows") != len(source_rows):
        issues.append("source task count mismatch")
    if counts.get("source_task_rows") != status_counts.get("ACTION_PACK_WORK_RESOLUTION_SOURCE_ACQUISITION_REQUIRED", 0):
        issues.append("source task count does not match source-required rows")
    if counts.get("rule_self_test_rows") != len(self_tests):
        issues.append("rule self-test count mismatch")
    if counts.get("rule_self_test_pass_rows") != len(self_tests):
        issues.append("rule self-test pass count mismatch")
    if any(row.get("self_test_status") != "SOURCE_EXPANSION_RULE_CANDIDATE_SELF_TEST_PASS" for row in self_tests):
        issues.append("one or more rule self-tests failed")
    if any(not row.get("branch_local_rule_candidate_expression_sha256") for row in rule_rows):
        issues.append("one or more rule candidates lacks expression hash")
    if any(not row.get("replay_task_expression_sha256") for row in replay_rows):
        issues.append("one or more replay tasks lacks expression hash")
    if any(not row.get("source_task_expression_sha256") for row in source_rows):
        issues.append("one or more source tasks lacks expression hash")
    if counts.get("rule_candidate_class_counts") != dict(sorted(rule_classes.items())):
        issues.append("rule candidate class count mismatch")
    if counts.get("decision_counts") != dict(sorted(decisions.items())):
        issues.append("decision count mismatch")
    if counts.get("rows_with_simulated_r") != sum(row.get("cost_adjusted_simulated_r") is not None for row in rule_rows):
        issues.append("rows-with-simulated-R count mismatch")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(rule_rows) + len(replay_rows) + len(source_rows):
        issues.append("aggregate row counts do not sum to task rows")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    if len(system_rows) != 1 or counts.get("system_rows") != 1:
        issues.append("system ledger must contain one row")
    if not any(str(value).startswith("rule-redesign-positive") for value in rule_classes):
        issues.append("positive rule candidate class is absent")
    if not any(str(value).startswith("rule-redesign-negative") for value in rule_classes):
        issues.append("negative rule candidate class is absent")
    if any(
        not boundary_ok(row)
        for row in rule_rows
        + self_tests
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
            "rule_candidate_rows": len(rule_rows),
            "replay_task_rows": len(replay_rows),
            "source_task_rows": len(source_rows),
            "aggregate_rows": len(aggregate_rows),
            "issue_rows": len(issue_rows),
        },
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
