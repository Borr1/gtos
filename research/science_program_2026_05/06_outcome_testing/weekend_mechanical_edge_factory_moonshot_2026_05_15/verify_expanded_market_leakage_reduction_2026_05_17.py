#!/usr/bin/env python3
"""Verify expanded-market leakage-reduction checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
CANDIDATE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_CODE_CANDIDATES"
EXECUTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION"
SELECTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_IMPLEMENTATION_SELECTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_LEAKAGE_REDUCTION"

CANDIDATE_LEDGER = ROUTE_DIR / f"{CANDIDATE_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
EXECUTION_RESULT = ROUTE_DIR / f"{EXECUTION_PREFIX}_RESULT_2026-05-17.json"
EXECUTION_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
SELECTION_LEDGER = ROUTE_DIR / f"{SELECTION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
MATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_MATCH_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_leakage_reduction.py",
    ROUTE_DIR / "build_expanded_market_leakage_reduction_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, ROW_LEDGER, MATCH_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]


def long_path(path: Path) -> str:
    text = str(path)
    if len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        return [json.loads(line) for line in handle if line.strip()]


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
    terms = blocked_terms()
    for path in paths:
        text = read_text(path)
        for term in terms:
            if term in text:
                issues.append(f"blocked term {term!r} found in {path.relative_to(REPO)}")
    return issues


def main() -> None:
    issues: list[str] = []
    execution_result = read_json(EXECUTION_RESULT)
    candidates = read_jsonl(CANDIDATE_LEDGER)
    executions = read_jsonl(EXECUTION_LEDGER)
    selections = read_jsonl(SELECTION_LEDGER)
    result = read_json(RESULT_PATH)
    rows = read_jsonl(ROW_LEDGER)
    matches = read_jsonl(MATCH_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if execution_result.get("ok") is not True:
        issues.append("input CP222 result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(candidates) != 1748:
        issues.append(f"input code candidate count changed from 1748 to {len(candidates)}")
    if len(executions) != 1748:
        issues.append(f"input execution count changed from 1748 to {len(executions)}")
    if len(selections) != 22610:
        issues.append(f"input selection count changed from 22610 to {len(selections)}")
    if counts.get("leakage_reduction_rows") != len(rows):
        issues.append("reduction row count mismatch")
    if counts.get("leakage_reduction_match_rows") != len(matches):
        issues.append("match row count mismatch")
    if counts.get("aggregate_rows") != len(aggregates):
        issues.append("aggregate row count mismatch")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len(rows) != len(executions):
        issues.append("reduction rows must match execution rows")
    if sum(int(row.get("matched_selection_rows") or 0) for row in rows) != len(matches):
        issues.append("reduction matched row counts do not sum to match rows")
    if sum(int(row.get("row_count") or 0) for row in aggregates) != len(rows):
        issues.append("aggregate row counts do not sum to reduction rows")
    if any(not boundary_ok(row) for row in rows + matches + aggregates + system_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if len({row.get("leakage_reduction_row_id") for row in rows}) != len(rows):
        issues.append("reduction row ids are not unique")
    if len({row.get("leakage_reduction_match_row_id") for row in matches}) != len(matches):
        issues.append("match row ids are not unique")

    input_execution_ids = [row.get("code_candidate_execution_row_id") for row in executions]
    output_execution_ids = [row.get("input_code_candidate_execution_row_id") for row in rows]
    if Counter(input_execution_ids) != Counter(output_execution_ids):
        issues.append("input execution ids are not covered exactly once")

    input_pass_rows = sum(1 for row in executions if row.get("execution_status") == "CODE_CANDIDATE_EXECUTION_PASS")
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in rows)
    preserved_pass_rows = decisions.get("IMPLEMENT_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION_PRESERVED", 0)
    if preserved_pass_rows != input_pass_rows:
        issues.append(f"preserved pass rows {preserved_pass_rows} do not match input pass rows {input_pass_rows}")
    if not any(str(decision).startswith("IMPLEMENT") for decision in decisions):
        issues.append("implement reduction decision class is absent")
    remaining_repair_rows = sum(count for decision, count in decisions.items() if str(decision).startswith("REDESIGN"))
    if counts.get("remaining_repair_rows") != remaining_repair_rows:
        issues.append("remaining repair row count does not match redesign decisions")
    if remaining_repair_rows and not any(str(decision).startswith("REDESIGN") for decision in decisions):
        issues.append("redesign reduction decision class is absent despite remaining repairs")

    for row in rows:
        decision = str(row.get("keep_kill_redesign_implement_decision"))
        if decision == "IMPLEMENT_EXPANDED_MARKET_LEAKAGE_REDUCED_CODE_CANDIDATE":
            if int(row.get("matched_implement_rows") or 0) <= 0 or int(row.get("matched_nonimplement_rows") or 0) != 0:
                issues.append(f"reduced implement row has invalid match counts: {row.get('leakage_reduction_row_id')}")
        if decision == "REDESIGN_EXPANDED_MARKET_LEAKAGE_REDUCTION_REMAINS":
            if int(row.get("matched_nonimplement_rows") or 0) <= 0:
                issues.append(f"remaining redesign row lacks nonimplement match: {row.get('leakage_reduction_row_id')}")
        if decision.startswith("IMPLEMENT") and not row.get("source_path"):
            issues.append(f"implement reduction row missing source path: {row.get('leakage_reduction_row_id')}")
        if decision.startswith("IMPLEMENT") and not row.get("source_file_sha256"):
            issues.append(f"implement reduction row missing source hash: {row.get('leakage_reduction_row_id')}")

    if not any(row.get("match_status") == "REDUCED_IMPLEMENT_MATCH" for row in matches):
        issues.append("implement match rows are absent")
    if decisions.get("REDESIGN_EXPANDED_MARKET_LEAKAGE_REDUCTION_REMAINS", 0) and not any(
        row.get("match_status") == "REDUCED_NONIMPLEMENT_MATCH" for row in matches
    ):
        issues.append("nonimplement match rows are absent for remaining redesign rows")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "decision_counts": dict(sorted(decisions.items())),
        "reduction_rows": len(rows),
        "match_rows": len(matches),
        "aggregate_rows": len(aggregates),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
