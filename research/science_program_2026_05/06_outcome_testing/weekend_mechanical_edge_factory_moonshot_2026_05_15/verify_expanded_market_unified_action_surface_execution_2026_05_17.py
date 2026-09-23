#!/usr/bin/env python3
"""Verify expanded-market unified action surface execution checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
ACTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_IMPLEMENTATION_ACTIONS"
SURFACE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_ACTION_SURFACES"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_EXECUTION"

ACTION_RESULT = ROUTE_DIR / f"{ACTION_PREFIX}_RESULT_2026-05-17.json"
SURFACE_RESULT = ROUTE_DIR / f"{SURFACE_PREFIX}_RESULT_2026-05-17.json"
EVIDENCE_ACTION_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_EVIDENCE_ACTION_LEDGER_2026-05-17.jsonl"
DECISION_ACTION_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_DECISION_ACTION_LEDGER_2026-05-17.jsonl"
TERMINAL_ACTION_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_TERMINAL_ACTION_LEDGER_2026-05-17.jsonl"
SURFACE_LEDGER = ROUTE_DIR / f"{SURFACE_PREFIX}_SURFACE_LEDGER_2026-05-17.jsonl"
MEMBER_LEDGER = ROUTE_DIR / f"{SURFACE_PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
SURFACE_REDESIGN_LEDGER = ROUTE_DIR / f"{SURFACE_PREFIX}_REDESIGN_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SURFACE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SURFACE_EXECUTION_LEDGER_2026-05-17.jsonl"
MEMBER_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_EXECUTION_LEDGER_2026-05-17.jsonl"
REDESIGN_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_EXECUTION_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_unified_action_surface_execution.py",
    ROUTE_DIR / "build_expanded_market_unified_action_surface_execution_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    SURFACE_EXECUTION_LEDGER,
    MEMBER_EXECUTION_LEDGER,
    REDESIGN_EXECUTION_LEDGER,
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
    input_evidence_actions = read_jsonl(EVIDENCE_ACTION_LEDGER)
    input_decision_actions = read_jsonl(DECISION_ACTION_LEDGER)
    input_terminal_actions = read_jsonl(TERMINAL_ACTION_LEDGER)
    input_surfaces = read_jsonl(SURFACE_LEDGER)
    input_members = read_jsonl(MEMBER_LEDGER)
    input_redesigns = read_jsonl(SURFACE_REDESIGN_LEDGER)

    result = read_json(RESULT_PATH)
    surface_rows = read_jsonl(SURFACE_EXECUTION_LEDGER)
    member_rows = read_jsonl(MEMBER_EXECUTION_LEDGER)
    redesign_rows = read_jsonl(REDESIGN_EXECUTION_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    issue_rows = read_jsonl(ISSUE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if action_result.get("ok") is not True:
        issues.append("input action result is not ok")
    if surface_result.get("ok") is not True:
        issues.append("input surface result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")

    expected_input_counts = {
        "input_evidence_action_rows": len(input_evidence_actions),
        "input_decision_action_rows": len(input_decision_actions),
        "input_terminal_action_rows": len(input_terminal_actions),
        "input_surface_rows": len(input_surfaces),
        "input_surface_member_rows": len(input_members),
        "input_surface_redesign_rows": len(input_redesigns),
    }
    expected_output_counts = {
        "surface_execution_rows": len(surface_rows),
        "member_execution_rows": len(member_rows),
        "redesign_execution_rows": len(redesign_rows),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issue_rows),
        "system_rows": len(system_rows),
        "surface_execution_pass_rows": sum(
            1 for row in surface_rows if row.get("execution_status") == "ACTION_SURFACE_EXECUTION_PASS"
        ),
        "member_execution_pass_rows": sum(
            1 for row in member_rows if row.get("execution_status") == "ACTION_SURFACE_MEMBER_EXECUTION_PASS"
        ),
        "redesign_execution_preserved_rows": sum(
            1
            for row in redesign_rows
            if row.get("execution_status") == "REDESIGN_ACTION_EXECUTION_PRESERVED_WITH_NUMERIC_PROOF"
        ),
        "member_rows_with_simulated_r": sum(1 for row in member_rows if row.get("missing_simulated_field") is None),
        "redesign_rows_with_simulated_r": sum(1 for row in redesign_rows if row.get("missing_simulated_field") is None),
    }
    for field, actual in {**expected_input_counts, **expected_output_counts}.items():
        if counts.get(field) != actual:
            issues.append(f"{field} count mismatch")

    fixed_counts = {
        "input_evidence_action_rows": 9266,
        "input_decision_action_rows": 264,
        "input_terminal_action_rows": 151,
        "input_surface_rows": 717,
        "input_surface_member_rows": 9528,
        "input_surface_redesign_rows": 153,
        "surface_execution_rows": 717,
        "member_execution_rows": 9528,
        "redesign_execution_rows": 153,
        "issue_rows": 2,
        "system_rows": 1,
        "surface_execution_pass_rows": 715,
        "member_execution_pass_rows": 9528,
        "redesign_execution_preserved_rows": 153,
        "member_rows_with_simulated_r": 9528,
        "redesign_rows_with_simulated_r": 153,
    }
    for field, expected in fixed_counts.items():
        if counts.get(field) != expected:
            issues.append(f"{field} must equal {expected}")

    if any(not boundary_ok(row) for row in surface_rows + member_rows + redesign_rows + aggregate_rows + issue_rows + system_rows):
        issues.append("one or more output rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")

    if Counter(row.get("unified_action_surface_row_id") for row in input_surfaces) != Counter(
        row.get("input_unified_action_surface_row_id") for row in surface_rows
    ):
        issues.append("surface rows are not covered exactly once")
    if Counter(row.get("unified_action_surface_member_row_id") for row in input_members) != Counter(
        row.get("input_unified_action_surface_member_row_id") for row in member_rows
    ):
        issues.append("member rows are not covered exactly once")
    if Counter(row.get("unified_action_surface_redesign_row_id") for row in input_redesigns) != Counter(
        row.get("input_unified_action_surface_redesign_row_id") for row in redesign_rows
    ):
        issues.append("redesign rows are not covered exactly once")

    if any(row.get("missing_expected_member_rows") != 0 for row in surface_rows):
        issues.append("one or more surfaces missed expected members")
    if any(row.get("unexpected_execution_match_rows") != 0 for row in surface_rows):
        issues.append("one or more surfaces matched unexpected actions")
    predicate_extra_total = sum(int(row.get("predicate_extra_match_rows") or 0) for row in surface_rows)
    if predicate_extra_total != 3:
        issues.append("predicate-only extra match total must equal 3")
    issue_surface_ids = Counter(row.get("input_unified_action_surface_row_id") for row in issue_rows)
    predicate_extra_surface_ids = Counter(
        row.get("input_unified_action_surface_row_id")
        for row in surface_rows
        if int(row.get("predicate_extra_match_rows") or 0) > 0
    )
    if issue_surface_ids != predicate_extra_surface_ids:
        issues.append("predicate-extra surfaces are not preserved exactly once in issue rows")
    if any(row.get("missing_simulated_field") for row in member_rows + redesign_rows):
        issues.append("one or more execution rows lack simulated R fields")
    if any(row.get("source_action_present") is not True for row in member_rows + redesign_rows):
        issues.append("one or more execution rows lack source action")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "surface_execution_rows": len(surface_rows),
        "member_execution_rows": len(member_rows),
        "redesign_execution_rows": len(redesign_rows),
        "issue_rows": len(issue_rows),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
