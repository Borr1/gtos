#!/usr/bin/env python3
"""Verify expanded-market source-expansion action application checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
ACTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_EXECUTION"
SOURCE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_APPLICATION"

ACTION_RESULT = ROUTE_DIR / f"{ACTION_PREFIX}_RESULT_2026-05-17.json"
ACTION_ROW_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
SOURCE_EXECUTION_LEDGER = ROUTE_DIR / f"{SOURCE_PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"
SOURCE_GAP_LEDGER = ROUTE_DIR / f"{SOURCE_PREFIX}_SOURCE_GAP_PROOF_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
RULE_LEDGER = ROUTE_DIR / f"{PREFIX}_RULE_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_source_expansion_action_application.py",
    ROUTE_DIR / "build_expanded_market_source_expansion_action_application_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    ROW_LEDGER,
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


def source_execution_ids() -> set[str]:
    return {
        str(row.get("expanded_market_source_expansion_execution_row_id") or "")
        for row in iter_jsonl(SOURCE_EXECUTION_LEDGER)
    }


def source_gap_ids() -> set[str]:
    return {
        str(row.get("expanded_market_source_expansion_gap_row_id") or "")
        for row in iter_jsonl(SOURCE_GAP_LEDGER)
    }


def actionable_action_ids() -> set[str]:
    output: set[str] = set()
    for row in iter_jsonl(ACTION_ROW_LEDGER):
        decision = str(row.get("keep_kill_redesign_implement_decision") or "")
        if (
            decision.startswith("IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_MONTH_STABLE_ACTION")
            or decision.startswith("KILL_EXPANDED_MARKET_SOURCE_EXPANSION_MONTH_STABLE_ACTION")
            or decision.startswith(
                "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_SOURCE_EXPANSION_MONTH_STABLE_ACTION"
            )
        ):
            output.add(str(row.get("expanded_market_source_expansion_action_execution_row_id") or ""))
    return output


def main() -> None:
    issues: list[str] = []
    action_result = read_json(ACTION_RESULT)
    result = read_json(RESULT_PATH)
    counts = result.get("counts") or {}
    execution_ids = source_execution_ids()
    gap_ids = source_gap_ids()
    action_ids = actionable_action_ids()

    rule_rows = list(iter_jsonl(RULE_LEDGER))
    rule_ids = {
        str(row.get("expanded_market_source_expansion_action_application_rule_row_id") or "")
        for row in rule_rows
    }
    rule_action_ids = {
        str(row.get("input_source_expansion_action_execution_row_id") or "") for row in rule_rows
    }

    application_ids: set[str] = set()
    covered_execution_ids: set[str] = set()
    covered_gap_ids: set[str] = set()
    applied_rule_ids: set[str] = set()
    row_count = 0
    rows_with_r = 0
    applied_rows = 0
    status_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    for row in iter_jsonl(ROW_LEDGER):
        row_count += 1
        application_ids.add(str(row.get("expanded_market_source_expansion_action_application_row_id") or ""))
        exec_id = str(row.get("input_source_expansion_execution_row_id") or "")
        gap_id = str(row.get("input_source_expansion_gap_row_id") or "")
        rule_id = str(row.get("input_action_application_rule_row_id") or "")
        status = str(row.get("action_application_status") or "")
        if exec_id:
            covered_execution_ids.add(exec_id)
            has_simulated_r = row.get("cost_adjusted_simulated_r") is not None
            if has_simulated_r and (
                row.get("entry_reference") is None or row.get("proxy_denominator_price") is None
            ):
                issues.append("one or more source execution application rows lacks replay geometry")
                break
            if not has_simulated_r and not row.get("missing_simulated_fields"):
                issues.append(
                    "one or more noncomputed source execution application rows lacks missing-field proof"
                )
                break
        if gap_id:
            covered_gap_ids.add(gap_id)
            if not row.get("missing_simulated_fields"):
                issues.append("one or more source-gap application rows lacks missing-field proof")
                break
            if row.get("cost_adjusted_simulated_r") is not None:
                issues.append("one or more source-gap application rows unexpectedly has simulated R")
                break
        if rule_id:
            applied_rule_ids.add(rule_id)
            applied_rows += 1
            if rule_id not in rule_ids:
                issues.append("one or more applied application rows references an unknown rule")
                break
        if row.get("cost_adjusted_simulated_r") is not None:
            rows_with_r += 1
        status_counts[status] += 1
        decision_counts[row.get("keep_kill_redesign_implement_decision")] += 1
        if not boundary_ok(row):
            issues.append("one or more action application rows failed branch-local boundary checks")
            break
        if not row.get("branch_local_action_application_expression_sha256"):
            issues.append("one or more action application rows lacks application expression hash")
            break

    self_test_rows = list(iter_jsonl(SELF_TEST_LEDGER))
    aggregate_rows = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))

    if action_result.get("ok") is not True:
        issues.append("input action-execution result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(application_ids) != row_count:
        issues.append("action application row ids are not unique")
    if covered_execution_ids != execution_ids:
        issues.append("action application rows do not consume every source execution row exactly once")
    if covered_gap_ids != gap_ids:
        issues.append("action application rows do not consume every source gap row exactly once")
    if counts.get("source_execution_rows") != len(execution_ids):
        issues.append("source execution input count mismatch")
    if counts.get("source_gap_rows") != len(gap_ids):
        issues.append("source gap input count mismatch")
    if counts.get("action_rule_rows") != len(rule_rows) or rule_action_ids != action_ids:
        issues.append("compiled action rules do not match actionable CP268 action rows")
    if counts.get("action_application_rows") != row_count:
        issues.append("action application row count mismatch")
    if counts.get("rows_with_simulated_r") != rows_with_r:
        issues.append("rows-with-simulated-R count mismatch")
    if counts.get("applied_action_rows") != applied_rows:
        issues.append("applied action row count mismatch")
    if counts.get("status_counts") != dict(sorted(status_counts.items())):
        issues.append("status count mismatch")
    if counts.get("decision_counts") != dict(sorted(decision_counts.items())):
        issues.append("decision count mismatch")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != row_count:
        issues.append("aggregate row counts do not sum to application rows")
    if counts.get("self_test_rows") != len(self_test_rows):
        issues.append("self-test row count mismatch")
    if any(row.get("self_test_status") != "ACTION_APPLICATION_RULE_SELF_TEST_PASS" for row in self_test_rows):
        issues.append("one or more action application rule self-tests failed")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    if len(system_rows) != 1 or counts.get("system_rows") != 1:
        issues.append("system ledger must contain one row")
    if not any(str(decision).startswith("IMPLEMENT") for decision in decision_counts):
        issues.append("implement action application decision is absent")
    if not any(str(decision).startswith("CARRY_AS_AVOID") for decision in decision_counts):
        issues.append("avoid action application decision is absent")
    if not any(str(decision).startswith("KILL") for decision in decision_counts):
        issues.append("kill action application decision is absent")
    if any(not boundary_ok(row) for row in rule_rows + self_test_rows + aggregate_rows + issue_rows + system_rows + [result]):
        issues.append("one or more rule/self-test/aggregate/system/result rows failed branch-local boundary checks")
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": {
            "action_application_rows": row_count,
            "action_rule_rows": len(rule_rows),
            "applied_action_rows": applied_rows,
            "rows_with_simulated_r": rows_with_r,
            "aggregate_rows": len(aggregate_rows),
            "issue_rows": len(issue_rows),
        },
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
