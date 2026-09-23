#!/usr/bin/env python3
"""Verify expanded-market source-expansion rule match performance."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_CANDIDATE_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_RULE_MATCH_PERFORMANCE"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
RULE_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_RULE_EXECUTION_LEDGER_2026-05-17.jsonl"
MATCH_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MATCH_LEDGER_2026-05-17.jsonl"
REPLAY_TASK_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REPLAY_TASK_EXECUTION_LEDGER_2026-05-17.jsonl"
SOURCE_TASK_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_TASK_EXECUTION_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
PERFORMANCE_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
REPLAY_TASK_PERFORMANCE_LEDGER = ROUTE_DIR / f"{PREFIX}_REPLAY_TASK_PERFORMANCE_LEDGER_2026-05-17.jsonl"
SOURCE_TASK_PERFORMANCE_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_TASK_PERFORMANCE_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_source_expansion_rule_match_performance.py",
    ROUTE_DIR / "build_expanded_market_source_expansion_rule_match_performance_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    PERFORMANCE_LEDGER,
    REPLAY_TASK_PERFORMANCE_LEDGER,
    SOURCE_TASK_PERFORMANCE_LEDGER,
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
    input_rule_count = count_jsonl(RULE_EXECUTION_LEDGER)
    input_match_count = count_jsonl(MATCH_LEDGER)
    input_replay_count = count_jsonl(REPLAY_TASK_EXECUTION_LEDGER)
    input_source_count = count_jsonl(SOURCE_TASK_EXECUTION_LEDGER)

    performance_rows = list(iter_jsonl(PERFORMANCE_LEDGER))
    replay_rows = list(iter_jsonl(REPLAY_TASK_PERFORMANCE_LEDGER))
    source_rows = list(iter_jsonl(SOURCE_TASK_PERFORMANCE_LEDGER))
    aggregate_rows = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))

    performance_ids = {
        str(row.get("input_rule_candidate_execution_row_id") or "") for row in performance_rows
    }
    input_ids = {
        str(row.get("expanded_market_source_expansion_rule_candidate_execution_row_id") or "")
        for row in iter_jsonl(RULE_EXECUTION_LEDGER)
    }
    decision_counts = Counter(row.get("keep_kill_redesign_implement_decision") for row in performance_rows)
    action_counts = Counter(row.get("follow_inverse_default_off_avoid_class") for row in performance_rows)

    if input_result.get("ok") is not True:
        issues.append("input rule-candidate execution result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if counts.get("input_rule_candidate_execution_result_ok") is not True:
        issues.append("input result-ok count field is not true")
    if counts.get("input_rule_execution_rows") != input_rule_count:
        issues.append("input rule execution count mismatch")
    if counts.get("input_rule_match_rows") != input_match_count:
        issues.append("input rule match count mismatch")
    if counts.get("rule_match_performance_rows") != len(performance_rows):
        issues.append("rule match performance count mismatch")
    if len(performance_rows) != input_rule_count:
        issues.append("rule match performance rows do not preserve every rule execution row")
    if performance_ids != input_ids:
        issues.append("rule match performance ids do not match input rule execution ids")
    if counts.get("matched_rows_preserved") != input_match_count:
        issues.append("matched row preservation count mismatch")
    if any(
        int(row.get("observed_match_rows") or 0)
        != int(row.get("candidate_reported_match_count") or 0)
        for row in performance_rows
    ):
        issues.append("one or more performance rows has a reported/observed match mismatch")
    if any(
        int(row.get("win_count") or 0)
        + int(row.get("loss_count") or 0)
        + int(row.get("zero_count") or 0)
        != int(row.get("observed_match_rows") or 0)
        for row in performance_rows
    ):
        issues.append("one or more win/loss/zero counts do not sum to observed matches")
    if counts.get("replay_task_performance_rows") != len(replay_rows) or len(replay_rows) != input_replay_count:
        issues.append("replay task performance count mismatch")
    if counts.get("source_task_performance_rows") != len(source_rows) or len(source_rows) != input_source_count:
        issues.append("source task performance count mismatch")
    if counts.get("decision_counts") != dict(sorted(decision_counts.items())):
        issues.append("decision count mismatch")
    if counts.get("action_class_counts") != dict(sorted(action_counts.items())):
        issues.append("action class count mismatch")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != (
        len(performance_rows) + len(replay_rows) + len(source_rows)
    ):
        issues.append("aggregate row counts do not sum to output rows")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    if len(system_rows) != 1 or counts.get("system_rows") != 1:
        issues.append("system ledger must contain one row")
    if any(
        not boundary_ok(row)
        for row in performance_rows
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
            "rule_match_performance_rows": len(performance_rows),
            "replay_task_performance_rows": len(replay_rows),
            "source_task_performance_rows": len(source_rows),
            "aggregate_rows": len(aggregate_rows),
            "issue_rows": len(issue_rows),
        },
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
