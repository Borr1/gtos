#!/usr/bin/env python3
"""Verify frozen ready-action runtime rule materialization."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
CLOSURE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_IMPLEMENTATION_CLOSURE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_READY_ACTION_RUNTIME"
DATE = "2026-05-17"

INPUT_READY_LEDGER = ROUTE_DIR / f"{CLOSURE_PREFIX}_IMPLEMENTATION_READY_BUNDLE_LEDGER_{DATE}.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_{DATE}.json"
RULE_LEDGER = ROUTE_DIR / f"{PREFIX}_RULE_LEDGER_{DATE}.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_{DATE}.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_{DATE}.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_{DATE}.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_{DATE}.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_frozen_universe_ready_action_runtime.py",
    ROUTE_DIR / "build_frozen_universe_ready_action_runtime_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    RULE_LEDGER,
    SELF_TEST_LEDGER,
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


def rel(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line.lstrip("\ufeff"))


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
        with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        for term in blocked_terms():
            if term in text:
                issues.append(f"blocked term {term!r} found in {rel(path)}")
    return issues


def main() -> None:
    issues: list[str] = []
    for path in OUTPUT_FILES:
        if not path.exists():
            issues.append(f"missing output {rel(path)}")
    if issues:
        print(json.dumps({"ok": False, "issues": issues}, indent=2, sort_keys=True))
        raise SystemExit(1)

    result = read_json(RESULT_PATH)
    counts = result.get("counts") or {}
    input_ready_count = count_jsonl(INPUT_READY_LEDGER)
    rule_rows = list(iter_jsonl(RULE_LEDGER))
    self_tests = list(iter_jsonl(SELF_TEST_LEDGER))
    aggregates = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))
    action_counts = Counter(row.get("action_class") for row in rule_rows)
    self_test_counts = Counter(row.get("self_test_status") for row in self_tests)

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if counts.get("input_ready_rows") != input_ready_count:
        issues.append("input ready row count mismatch")
    if counts.get("rule_rows") != len(rule_rows) or len(rule_rows) != input_ready_count:
        issues.append("runtime rule row count mismatch")
    if counts.get("self_test_rows") != len(self_tests) or len(self_tests) != len(rule_rows):
        issues.append("self-test row count mismatch")
    if counts.get("aggregate_rows") != len(aggregates):
        issues.append("aggregate row count mismatch")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    if counts.get("action_class_counts") != dict(sorted(action_counts.items())):
        issues.append("action class counts mismatch")
    if counts.get("self_test_status_counts") != dict(sorted(self_test_counts.items())):
        issues.append("self-test status counts mismatch")
    if any(row.get("missing_match_fields") for row in rule_rows):
        issues.append("one or more runtime rules has missing match fields")
    if any(row.get("self_test_status") != "FROZEN_READY_ACTION_RUNTIME_SELF_TEST_PASS" for row in self_tests):
        issues.append("one or more self-tests did not pass")
    if not action_counts.get("follow_rule") or not action_counts.get("avoid_filter"):
        issues.append("runtime rules must include both follow and avoid classes")
    if len(system_rows) != 1 or not boundary_ok(system_rows[0]):
        issues.append("system row missing or boundary failed")
    if any(not boundary_ok(row) for row in rule_rows + self_tests + aggregates + issue_rows):
        issues.append("one or more ledger rows failed boundary checks")
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": {
            "input_ready_rows": input_ready_count,
            "rule_rows": len(rule_rows),
            "self_test_rows": len(self_tests),
            "aggregate_rows": len(aggregates),
            "issue_rows": len(issue_rows),
            "action_class_counts": dict(sorted(action_counts.items())),
        },
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
