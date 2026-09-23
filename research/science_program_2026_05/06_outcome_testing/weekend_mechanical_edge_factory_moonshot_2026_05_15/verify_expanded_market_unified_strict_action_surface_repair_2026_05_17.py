#!/usr/bin/env python3
"""Verify strict predicate repair rows for expanded-market unified action surfaces."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
ACTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_IMPLEMENTATION_ACTIONS"
SURFACE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_ACTION_SURFACES"
EXECUTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_STRICT_ACTION_SURFACE_REPAIR"

ACTION_RESULT = ROUTE_DIR / f"{ACTION_PREFIX}_RESULT_2026-05-17.json"
SURFACE_RESULT = ROUTE_DIR / f"{SURFACE_PREFIX}_RESULT_2026-05-17.json"
EXECUTION_RESULT = ROUTE_DIR / f"{EXECUTION_PREFIX}_RESULT_2026-05-17.json"
EVIDENCE_ACTION_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_EVIDENCE_ACTION_LEDGER_2026-05-17.jsonl"
DECISION_ACTION_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_DECISION_ACTION_LEDGER_2026-05-17.jsonl"
TERMINAL_ACTION_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_TERMINAL_ACTION_LEDGER_2026-05-17.jsonl"
SURFACE_LEDGER = ROUTE_DIR / f"{SURFACE_PREFIX}_SURFACE_LEDGER_2026-05-17.jsonl"
MEMBER_LEDGER = ROUTE_DIR / f"{SURFACE_PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
EXECUTION_REDESIGN_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_REDESIGN_EXECUTION_LEDGER_2026-05-17.jsonl"
EXECUTION_ISSUE_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
STRICT_SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_STRICT_SURFACE_LEDGER_2026-05-17.jsonl"
STRICT_SURFACE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_STRICT_SURFACE_EXECUTION_LEDGER_2026-05-17.jsonl"
STRICT_MEMBER_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_STRICT_MEMBER_EXECUTION_LEDGER_2026-05-17.jsonl"
STRICT_REDESIGN_PRESERVATION_LEDGER = ROUTE_DIR / f"{PREFIX}_STRICT_REDESIGN_PRESERVATION_LEDGER_2026-05-17.jsonl"
STRICT_REPAIR_PROOF_LEDGER = ROUTE_DIR / f"{PREFIX}_STRICT_REPAIR_PROOF_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_unified_strict_action_surface_repair.py",
    ROUTE_DIR / "build_expanded_market_unified_strict_action_surface_repair_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    STRICT_SURFACE_LEDGER,
    STRICT_SURFACE_EXECUTION_LEDGER,
    STRICT_MEMBER_EXECUTION_LEDGER,
    STRICT_REDESIGN_PRESERVATION_LEDGER,
    STRICT_REPAIR_PROOF_LEDGER,
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
    for path in paths:
        text = read_text(path)
        for term in blocked_terms():
            if term in text:
                issues.append(f"blocked term {term!r} found in {path.relative_to(REPO)}")
    return issues


def main() -> None:
    issues: list[str] = []
    action_result = read_json(ACTION_RESULT)
    surface_result = read_json(SURFACE_RESULT)
    execution_result = read_json(EXECUTION_RESULT)
    input_evidence_actions = read_jsonl(EVIDENCE_ACTION_LEDGER)
    input_decision_actions = read_jsonl(DECISION_ACTION_LEDGER)
    input_terminal_actions = read_jsonl(TERMINAL_ACTION_LEDGER)
    input_surfaces = read_jsonl(SURFACE_LEDGER)
    input_members = read_jsonl(MEMBER_LEDGER)
    input_redesign_executions = read_jsonl(EXECUTION_REDESIGN_LEDGER)
    input_previous_issues = read_jsonl(EXECUTION_ISSUE_LEDGER)

    result = read_json(RESULT_PATH)
    strict_surfaces = read_jsonl(STRICT_SURFACE_LEDGER)
    strict_executions = read_jsonl(STRICT_SURFACE_EXECUTION_LEDGER)
    member_executions = read_jsonl(STRICT_MEMBER_EXECUTION_LEDGER)
    redesign_preservations = read_jsonl(STRICT_REDESIGN_PRESERVATION_LEDGER)
    repair_proofs = read_jsonl(STRICT_REPAIR_PROOF_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    issue_rows = read_jsonl(ISSUE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if action_result.get("ok") is not True:
        issues.append("input action result is not ok")
    if surface_result.get("ok") is not True:
        issues.append("input surface result is not ok")
    if execution_result.get("ok") is not True:
        issues.append("input action-surface execution result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")

    expected_counts = {
        "input_evidence_action_rows": len(input_evidence_actions),
        "input_decision_action_rows": len(input_decision_actions),
        "input_terminal_action_rows": len(input_terminal_actions),
        "input_surface_rows": len(input_surfaces),
        "input_surface_member_rows": len(input_members),
        "input_redesign_execution_rows": len(input_redesign_executions),
        "input_previous_issue_rows": len(input_previous_issues),
        "strict_surface_rows": len(strict_surfaces),
        "strict_surface_execution_rows": len(strict_executions),
        "strict_member_execution_rows": len(member_executions),
        "strict_redesign_preservation_rows": len(redesign_preservations),
        "strict_repair_proof_rows": len(repair_proofs),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issue_rows),
        "system_rows": len(system_rows),
        "strict_surface_execution_pass_rows": sum(
            1
            for row in strict_executions
            if row.get("strict_execution_status") == "STRICT_ACTION_SURFACE_EXECUTION_PASS"
        ),
        "strict_member_execution_pass_rows": sum(
            1
            for row in member_executions
            if row.get("strict_member_execution_status") == "STRICT_ACTION_SURFACE_MEMBER_EXECUTION_PASS"
        ),
        "hash_guard_repaired_surface_rows": sum(
            1
            for row in strict_surfaces
            if row.get("strict_repair_mode") == "HASH_GUARD_REPAIRED_PREDICATE_BREADTH"
        ),
        "member_rows_with_simulated_r": sum(1 for row in member_executions if row.get("missing_simulated_field") is None),
        "redesign_rows_with_simulated_r": sum(
            1 for row in redesign_preservations if row.get("missing_simulated_field") is None
        ),
    }
    for field, actual in expected_counts.items():
        if counts.get(field) != actual:
            issues.append(f"{field} count mismatch")

    fixed_counts = {
        "input_evidence_action_rows": 9266,
        "input_decision_action_rows": 264,
        "input_terminal_action_rows": 151,
        "input_surface_rows": 717,
        "input_surface_member_rows": 9528,
        "input_redesign_execution_rows": 153,
        "input_previous_issue_rows": 2,
        "strict_surface_rows": 717,
        "strict_surface_execution_rows": 717,
        "strict_member_execution_rows": 9528,
        "strict_redesign_preservation_rows": 153,
        "strict_repair_proof_rows": 2,
        "issue_rows": 0,
        "system_rows": 1,
        "strict_surface_execution_pass_rows": 717,
        "strict_member_execution_pass_rows": 9528,
        "hash_guard_repaired_surface_rows": 2,
        "member_rows_with_simulated_r": 9528,
        "redesign_rows_with_simulated_r": 153,
    }
    for field, expected in fixed_counts.items():
        if counts.get(field) != expected:
            issues.append(f"{field} must equal {expected}")

    all_rows = (
        strict_surfaces
        + strict_executions
        + member_executions
        + redesign_preservations
        + repair_proofs
        + aggregate_rows
        + issue_rows
        + system_rows
    )
    if any(not boundary_ok(row) for row in all_rows):
        issues.append("one or more output rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")

    if Counter(row.get("unified_action_surface_row_id") for row in input_surfaces) != Counter(
        row.get("input_unified_action_surface_row_id") for row in strict_surfaces
    ):
        issues.append("surface rows are not covered exactly once by strict surfaces")
    if Counter(row.get("unified_action_surface_member_row_id") for row in input_members) != Counter(
        row.get("input_unified_action_surface_member_row_id") for row in member_executions
    ):
        issues.append("surface members are not covered exactly once by strict member executions")
    if Counter(row.get("unified_action_surface_redesign_execution_row_id") for row in input_redesign_executions) != Counter(
        row.get("input_unified_action_surface_redesign_execution_row_id") for row in redesign_preservations
    ):
        issues.append("redesign executions are not covered exactly once")
    if any(row.get("missing_expected_member_rows") != 0 for row in strict_executions):
        issues.append("one or more strict surfaces missed expected members")
    if any(row.get("unexpected_strict_match_rows") != 0 for row in strict_executions):
        issues.append("one or more strict surfaces matched unexpected rows")
    if any(row.get("missing_simulated_field") for row in member_executions + redesign_preservations):
        issues.append("one or more strict execution rows lack simulated R fields")
    if any(int(row.get("previous_predicate_extra_match_rows") or 0) <= 0 for row in repair_proofs):
        issues.append("repair proof rows must preserve previous predicate breadth")
    if any(int(row.get("unexpected_strict_match_rows") or 0) != 0 for row in repair_proofs):
        issues.append("repair proof rows must show zero unexpected strict matches")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "strict_surface_rows": len(strict_surfaces),
        "strict_member_execution_rows": len(member_executions),
        "strict_repair_proof_rows": len(repair_proofs),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
