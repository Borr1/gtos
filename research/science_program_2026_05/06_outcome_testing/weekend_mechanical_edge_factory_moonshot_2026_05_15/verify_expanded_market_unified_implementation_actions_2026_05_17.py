#!/usr/bin/env python3
"""Verify expanded-market unified implementation action checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_STRESS_QUALIFICATION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_IMPLEMENTATION_ACTIONS"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_EVIDENCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
INPUT_TERMINAL_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_TERMINAL_LEDGER_2026-05-17.jsonl"
INPUT_DECISION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_DECISION_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_ACTION_LEDGER_2026-05-17.jsonl"
TERMINAL_LEDGER = ROUTE_DIR / f"{PREFIX}_TERMINAL_ACTION_LEDGER_2026-05-17.jsonl"
DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_DECISION_ACTION_LEDGER_2026-05-17.jsonl"
REDESIGN_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_ACTION_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_unified_implementation_actions.py",
    ROUTE_DIR / "build_expanded_market_unified_implementation_actions_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    EVIDENCE_LEDGER,
    TERMINAL_LEDGER,
    DECISION_LEDGER,
    REDESIGN_LEDGER,
    AGGREGATE_LEDGER,
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
    for path in paths:
        text = read_text(path)
        for term in blocked_terms():
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
    evidence_actions = read_jsonl(EVIDENCE_LEDGER)
    terminal_actions = read_jsonl(TERMINAL_LEDGER)
    decision_actions = read_jsonl(DECISION_LEDGER)
    redesign_actions = read_jsonl(REDESIGN_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}
    all_actions = evidence_actions + terminal_actions + decision_actions

    if input_result.get("ok") is not True:
        issues.append("input stress result is not ok")
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
        "evidence_action_rows": len(evidence_actions),
        "terminal_action_rows": len(terminal_actions),
        "decision_action_rows": len(decision_actions),
        "redesign_action_rows": len(redesign_actions),
        "aggregate_rows": len(aggregate_rows),
        "system_rows": len(system_rows),
        "total_action_rows": len(all_actions),
    }
    for field, actual in expected_outputs.items():
        if counts.get(field) != actual:
            issues.append(f"{field} count mismatch")

    if len(evidence_actions) != 9266:
        issues.append("evidence action rows must equal 9266")
    if len(terminal_actions) != 151:
        issues.append("terminal action rows must equal 151")
    if len(decision_actions) != 264:
        issues.append("decision action rows must equal 264")
    if len(redesign_actions) != 153:
        issues.append("redesign action rows must equal 153")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if counts.get("implementation_action_rows") != 9528:
        issues.append("implementation action rows must equal 9528")
    if counts.get("terminal_capacity_action_rows") != 151:
        issues.append("terminal capacity action rows must equal 151")
    if counts.get("underpowered_redesign_action_rows") != 2:
        issues.append("underpowered redesign action rows must equal 2")

    all_rows = all_actions + redesign_actions + aggregate_rows + system_rows
    if any(not boundary_ok(row) for row in all_rows):
        issues.append("one or more output rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if Counter(row.get("unified_stress_qualification_row_id") for row in input_evidence) != Counter(
        row.get("input_unified_stress_qualification_row_id") for row in evidence_actions
    ):
        issues.append("input evidence stress ids are not covered once")
    if Counter(row.get("unified_stress_qualification_row_id") for row in input_terminal) != Counter(
        row.get("input_unified_stress_qualification_row_id") for row in terminal_actions
    ):
        issues.append("input terminal stress ids are not covered once")
    if Counter(row.get("unified_stress_decision_row_id") for row in input_decisions) != Counter(
        row.get("input_unified_stress_decision_row_id") for row in decision_actions
    ):
        issues.append("input stress decision ids are not covered once")

    status_counts = Counter(row.get("branch_local_action_status") for row in all_actions)
    if status_counts.get("SCORER_ROW_ACTION_READY") != 9265:
        issues.append("scorer row action ready count must equal 9265")
    if status_counts.get("DECISION_SCOPE_ACTION_READY") != 263:
        issues.append("decision scope action ready count must equal 263")
    if status_counts.get("TERMINAL_CAPACITY_REDESIGN_ACTION") != 151:
        issues.append("terminal capacity redesign action count must equal 151")
    if status_counts.get("UNDERPOWERED_REDESIGN_ACTION") != 2:
        issues.append("underpowered redesign action count must equal 2")
    implement_actions = [
        row for row in all_actions
        if str(row.get("keep_kill_redesign_implement_decision") or "").startswith("IMPLEMENT_")
    ]
    if any(not row.get("branch_local_action_expression_sha256") for row in implement_actions):
        issues.append("one or more implementation actions lack expression hash")
    if any(not row.get("branch_local_action_scope_sha256") for row in implement_actions):
        issues.append("one or more implementation actions lack scope hash")
    if any(row.get("cost_adjusted_simulated_r") is None for row in implement_actions):
        issues.append("one or more implementation actions lack cost-adjusted simulated R")
    if any(row.get("stress_simulated_r") is None for row in implement_actions):
        issues.append("one or more implementation actions lack stress simulated R")

    redesign_source_ids = Counter(
        row.get("unified_implementation_action_row_id")
        for row in all_actions
        if str(row.get("keep_kill_redesign_implement_decision") or "").startswith(("REDESIGN_", "KILL_"))
    )
    redesign_ledger_ids = Counter(row.get("input_unified_implementation_action_row_id") for row in redesign_actions)
    if redesign_source_ids != redesign_ledger_ids:
        issues.append("redesign ledger does not exactly cover redesign/kill action rows")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "evidence_actions": len(evidence_actions),
        "terminal_actions": len(terminal_actions),
        "decision_actions": len(decision_actions),
        "redesign_actions": len(redesign_actions),
        "aggregate_rows": len(aggregate_rows),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
