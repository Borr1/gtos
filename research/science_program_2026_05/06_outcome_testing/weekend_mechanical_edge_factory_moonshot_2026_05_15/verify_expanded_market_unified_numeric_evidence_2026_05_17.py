#!/usr/bin/env python3
"""Verify expanded-market unified numeric evidence checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
UNIFIED_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_FINAL_DECISIONS"
PERFORMANCE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PROXY_R_PERFORMANCE"
INTRABAR_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_INTRABAR_GEOMETRY"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_NUMERIC_EVIDENCE"

UNIFIED_RESULT = ROUTE_DIR / f"{UNIFIED_PREFIX}_RESULT_2026-05-17.json"
UNIFIED_DECISION_LEDGER = ROUTE_DIR / f"{UNIFIED_PREFIX}_DECISION_LEDGER_2026-05-17.jsonl"
UNIFIED_EVIDENCE_LEDGER = ROUTE_DIR / f"{UNIFIED_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
UNIFIED_TERMINAL_LEDGER = ROUTE_DIR / f"{UNIFIED_PREFIX}_TERMINAL_REDESIGN_LEDGER_2026-05-17.jsonl"
PERFORMANCE_RESULT = ROUTE_DIR / f"{PERFORMANCE_PREFIX}_RESULT_2026-05-17.json"
PERFORMANCE_LEDGER = ROUTE_DIR / f"{PERFORMANCE_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
INTRABAR_RESULT = ROUTE_DIR / f"{INTRABAR_PREFIX}_RESULT_2026-05-17.json"
INTRABAR_LEDGER = ROUTE_DIR / f"{INTRABAR_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
TERMINAL_LEDGER = ROUTE_DIR / f"{PREFIX}_TERMINAL_LEDGER_2026-05-17.jsonl"
DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_2026-05-17.jsonl"
SOURCE_ACCESS_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_ACCESS_PROOF_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_unified_numeric_evidence.py",
    ROUTE_DIR / "build_expanded_market_unified_numeric_evidence_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    EVIDENCE_LEDGER,
    TERMINAL_LEDGER,
    DECISION_LEDGER,
    SOURCE_ACCESS_LEDGER,
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
    unified_result = read_json(UNIFIED_RESULT)
    performance_result = read_json(PERFORMANCE_RESULT)
    intrabar_result = read_json(INTRABAR_RESULT)
    unified_decisions = read_jsonl(UNIFIED_DECISION_LEDGER)
    unified_evidence = read_jsonl(UNIFIED_EVIDENCE_LEDGER)
    unified_terminal = read_jsonl(UNIFIED_TERMINAL_LEDGER)
    performance_rows = read_jsonl(PERFORMANCE_LEDGER)
    intrabar_rows = read_jsonl(INTRABAR_LEDGER)

    result = read_json(RESULT_PATH)
    evidence_rows = read_jsonl(EVIDENCE_LEDGER)
    terminal_rows = read_jsonl(TERMINAL_LEDGER)
    decision_rows = read_jsonl(DECISION_LEDGER)
    source_access_rows = read_jsonl(SOURCE_ACCESS_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    issue_rows = read_jsonl(ISSUE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if unified_result.get("ok") is not True:
        issues.append("input unified final decision result is not ok")
    if performance_result.get("ok") is not True:
        issues.append("input expanded-market performance result is not ok")
    if intrabar_result.get("ok") is not True:
        issues.append("input intrabar result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")

    expected_input_counts = {
        "unified decisions": (len(unified_decisions), 264),
        "unified evidence": (len(unified_evidence), 9266),
        "unified terminal": (len(unified_terminal), 151),
        "performance rows": (len(performance_rows), 45220),
        "intrabar rows": (len(intrabar_rows), 45220),
    }
    for label, (actual, wanted) in expected_input_counts.items():
        if actual != wanted:
            issues.append(f"{label} count changed from {wanted} to {actual}")

    expected_outputs = {
        "unified_numeric_evidence_rows": len(evidence_rows),
        "unified_numeric_terminal_rows": len(terminal_rows),
        "unified_numeric_decision_rows": len(decision_rows),
        "source_access_proof_rows": len(source_access_rows),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issue_rows),
        "system_rows": len(system_rows),
    }
    for field, actual in expected_outputs.items():
        if counts.get(field) != actual:
            issues.append(f"{field} count mismatch")

    if len(evidence_rows) != 9266:
        issues.append("numeric evidence rows must equal 9266")
    if len(terminal_rows) != 151:
        issues.append("numeric terminal rows must equal 151")
    if len(decision_rows) != 264:
        issues.append("numeric decision rows must equal 264")
    if len(source_access_rows) != 29:
        issues.append("source/access proof rows must equal 29")
    if issue_rows:
        issues.append("numeric issue ledger must be empty for the current joined sources")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if counts.get("rows_with_simulated_r") != 9417:
        issues.append("rows_with_simulated_r must equal evidence plus terminal rows")
    if counts.get("rows_without_simulated_r") != 0:
        issues.append("rows_without_simulated_r must equal zero")
    if counts.get("source_access_confirmed_rows") != 29:
        issues.append("all source/access proof rows must be confirmed")

    all_rows = evidence_rows + terminal_rows + decision_rows + source_access_rows + aggregate_rows + issue_rows + system_rows
    if any(not boundary_ok(row) for row in all_rows):
        issues.append("one or more output rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")

    if Counter(row.get("unified_final_evidence_row_id") for row in unified_evidence) != Counter(
        row.get("input_unified_final_evidence_row_id") for row in evidence_rows
    ):
        issues.append("unified evidence ids are not covered once")
    if Counter(row.get("unified_final_terminal_redesign_row_id") for row in unified_terminal) != Counter(
        row.get("input_unified_final_terminal_redesign_row_id") for row in terminal_rows
    ):
        issues.append("unified terminal ids are not covered once")
    if Counter(row.get("unified_final_decision_row_id") for row in unified_decisions) != Counter(
        row.get("input_unified_final_decision_row_id") for row in decision_rows
    ):
        issues.append("unified decision ids are not covered once")
    if any(row.get("missing_simulated_fields") for row in evidence_rows + terminal_rows):
        issues.append("one or more numeric rows are missing simulated fields")
    if any(not row.get("input_expanded_market_performance_row_id") for row in evidence_rows + terminal_rows):
        issues.append("one or more numeric rows lack performance-row join id")
    if any(not row.get("input_intrabar_geometry_row_id") for row in evidence_rows + terminal_rows):
        issues.append("one or more numeric rows lack intrabar-row join id")
    if any(row.get("cost_adjusted_simulated_r") is None for row in evidence_rows + terminal_rows):
        issues.append("one or more numeric rows lack cost-adjusted simulated R")
    if any(row.get("source_access_status") != "SOURCE_PATH_HASH_CONFIRMED" for row in evidence_rows + terminal_rows):
        issues.append("one or more numeric rows lack confirmed source access status")
    if any(row.get("source_access_status") != "SOURCE_PATH_HASH_CONFIRMED" for row in source_access_rows):
        issues.append("one or more source/access proof rows are not confirmed")
    if sum(1 for row in evidence_rows if row.get("keep_kill_redesign_implement_decision") == "IMPLEMENT_EXPANDED_MARKET_UNIFIED_NUMERIC_EVIDENCE") != 9266:
        issues.append("all evidence numeric rows should be implement evidence")
    if sum(1 for row in terminal_rows if row.get("keep_kill_redesign_implement_decision") == "REDESIGN_EXPANDED_MARKET_UNIFIED_NUMERIC_TERMINAL") != 151:
        issues.append("all terminal numeric rows should remain redesign terminal")
    if sum(1 for row in decision_rows if row.get("keep_kill_redesign_implement_decision") == "IMPLEMENT_EXPANDED_MARKET_UNIFIED_NUMERIC_DECISION") != 264:
        issues.append("all numeric decision rows should be implement decisions")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "evidence_rows": len(evidence_rows),
        "terminal_rows": len(terminal_rows),
        "decision_rows": len(decision_rows),
        "source_access_rows": len(source_access_rows),
        "aggregate_rows": len(aggregate_rows),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
