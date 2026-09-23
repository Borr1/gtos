#!/usr/bin/env python3
"""Verify expanded-market unified stress qualification checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_NUMERIC_EVIDENCE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_STRESS_QUALIFICATION"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_EVIDENCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
INPUT_TERMINAL_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_TERMINAL_LEDGER_2026-05-17.jsonl"
INPUT_DECISION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_DECISION_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
TERMINAL_LEDGER = ROUTE_DIR / f"{PREFIX}_TERMINAL_LEDGER_2026-05-17.jsonl"
DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_unified_stress_qualification.py",
    ROUTE_DIR / "build_expanded_market_unified_stress_qualification_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    EVIDENCE_LEDGER,
    TERMINAL_LEDGER,
    DECISION_LEDGER,
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
    input_result = read_json(INPUT_RESULT)
    input_evidence = read_jsonl(INPUT_EVIDENCE_LEDGER)
    input_terminal = read_jsonl(INPUT_TERMINAL_LEDGER)
    input_decisions = read_jsonl(INPUT_DECISION_LEDGER)
    result = read_json(RESULT_PATH)
    evidence_rows = read_jsonl(EVIDENCE_LEDGER)
    terminal_rows = read_jsonl(TERMINAL_LEDGER)
    decision_rows = read_jsonl(DECISION_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    issue_rows = read_jsonl(ISSUE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if input_result.get("ok") is not True:
        issues.append("input numeric evidence result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")

    expected_inputs = {
        "input evidence": (len(input_evidence), 9266),
        "input terminal": (len(input_terminal), 151),
        "input decisions": (len(input_decisions), 264),
    }
    for label, (actual, wanted) in expected_inputs.items():
        if actual != wanted:
            issues.append(f"{label} count changed from {wanted} to {actual}")

    expected_outputs = {
        "stress_evidence_rows": len(evidence_rows),
        "stress_terminal_rows": len(terminal_rows),
        "stress_decision_rows": len(decision_rows),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issue_rows),
        "system_rows": len(system_rows),
    }
    for field, actual in expected_outputs.items():
        if counts.get(field) != actual:
            issues.append(f"{field} count mismatch")

    if len(evidence_rows) != 9266:
        issues.append("stress evidence rows must equal 9266")
    if len(terminal_rows) != 151:
        issues.append("stress terminal rows must equal 151")
    if len(decision_rows) != 264:
        issues.append("stress decision rows must equal 264")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if counts.get("qualified_evidence_rows") != 9265:
        issues.append("qualified evidence rows must equal 9265")
    if counts.get("qualified_decision_rows") != 263:
        issues.append("qualified decision rows must equal 263")
    if counts.get("terminal_capacity_rows") != 151:
        issues.append("terminal capacity rows must equal 151")
    if counts.get("issue_rows") != 2:
        issues.append("issue rows must equal 2 under current stress thresholds")

    all_rows = evidence_rows + terminal_rows + decision_rows + aggregate_rows + issue_rows + system_rows
    if any(not boundary_ok(row) for row in all_rows):
        issues.append("one or more output rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if Counter(row.get("input_unified_final_evidence_row_id") for row in input_evidence) != Counter(
        row.get("input_unified_final_evidence_row_id") for row in evidence_rows
    ):
        issues.append("input evidence ids are not covered once")
    if Counter(row.get("input_unified_final_terminal_redesign_row_id") for row in input_terminal) != Counter(
        row.get("input_unified_final_terminal_redesign_row_id") for row in terminal_rows
    ):
        issues.append("input terminal ids are not covered once")
    if Counter(row.get("unified_numeric_decision_row_id") for row in input_decisions) != Counter(
        row.get("input_unified_numeric_decision_row_id") for row in decision_rows
    ):
        issues.append("input decision ids are not covered once")
    if any(row.get("cost_positive_pass") is not True for row in evidence_rows + terminal_rows + decision_rows):
        issues.append("all current stress rows should pass positive-cost flag")
    if any(row.get("stress_positive_pass") is not True for row in evidence_rows + terminal_rows + decision_rows):
        issues.append("all current stress rows should pass positive-stress flag")
    if sum(1 for row in evidence_rows if row.get("stress_blocking_reason") == "underpowered_effective_n") != 1:
        issues.append("one evidence row should be underpowered")
    if sum(1 for row in decision_rows if row.get("stress_blocking_reason") == "underpowered_effective_n") != 1:
        issues.append("one decision row should be underpowered")
    if any(row.get("stress_blocking_reason") != "terminal_capacity_not_performance_failure" for row in terminal_rows):
        issues.append("terminal rows should remain capacity redesign, not numeric failure")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "evidence_rows": len(evidence_rows),
        "terminal_rows": len(terminal_rows),
        "decision_rows": len(decision_rows),
        "aggregate_rows": len(aggregate_rows),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
