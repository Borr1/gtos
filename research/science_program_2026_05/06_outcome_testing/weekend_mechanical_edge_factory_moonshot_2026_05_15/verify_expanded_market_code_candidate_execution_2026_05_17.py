#!/usr/bin/env python3
"""Verify expanded-market code-candidate execution checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
CANDIDATE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_CODE_CANDIDATES"
SELECTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_IMPLEMENTATION_SELECTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION"

CANDIDATE_RESULT = ROUTE_DIR / f"{CANDIDATE_PREFIX}_RESULT_2026-05-17.json"
CANDIDATE_LEDGER = ROUTE_DIR / f"{CANDIDATE_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
SELECTION_LEDGER = ROUTE_DIR / f"{SELECTION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
MATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_MATCH_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_code_candidate_execution.py",
    ROUTE_DIR / "build_expanded_market_code_candidate_execution_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, EXECUTION_LEDGER, MATCH_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]


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
    candidate_result = read_json(CANDIDATE_RESULT)
    candidates = read_jsonl(CANDIDATE_LEDGER)
    selections = read_jsonl(SELECTION_LEDGER)
    result = read_json(RESULT_PATH)
    executions = read_jsonl(EXECUTION_LEDGER)
    matches = read_jsonl(MATCH_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if candidate_result.get("ok") is not True:
        issues.append("input CP221 result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(candidates) != 1748:
        issues.append(f"input code candidate count changed from 1748 to {len(candidates)}")
    if len(selections) != 22610:
        issues.append(f"input selection count changed from 22610 to {len(selections)}")
    if counts.get("code_candidate_execution_rows") != len(executions):
        issues.append("execution row count mismatch")
    if counts.get("code_candidate_match_rows") != len(matches):
        issues.append("match row count mismatch")
    if counts.get("aggregate_rows") != len(aggregates):
        issues.append("aggregate row count mismatch")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len(executions) != len(candidates):
        issues.append("execution rows must match candidate rows")
    if sum(int(row.get("matched_selection_rows") or 0) for row in executions) != len(matches):
        issues.append("execution matched row counts do not sum to match rows")
    if sum(int(row.get("row_count") or 0) for row in aggregates) != len(executions):
        issues.append("aggregate row counts do not sum to execution rows")
    if any(not boundary_ok(row) for row in executions + matches + aggregates + system_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if len({row.get("code_candidate_execution_row_id") for row in executions}) != len(executions):
        issues.append("execution row ids are not unique")
    if len({row.get("code_candidate_match_row_id") for row in matches}) != len(matches):
        issues.append("match row ids are not unique")
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in executions)
    if not decisions:
        issues.append("decision counts are empty")
    if not any(str(decision).startswith("IMPLEMENT") for decision in decisions):
        issues.append("execution pass decision class is absent")
    if not any(str(decision).startswith("REDESIGN") for decision in decisions):
        issues.append("execution repair decision class is absent")
    if not any(row.get("match_status") == "MATCHED_IMPLEMENT_SELECTION" for row in matches):
        issues.append("implement match rows are absent")
    if not any(row.get("match_status") == "MATCHED_NONIMPLEMENT_SELECTION" for row in matches):
        issues.append("nonimplement match rows are absent")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "decision_counts": dict(sorted(decisions.items())),
        "execution_rows": len(executions),
        "match_rows": len(matches),
        "aggregate_rows": len(aggregates),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
