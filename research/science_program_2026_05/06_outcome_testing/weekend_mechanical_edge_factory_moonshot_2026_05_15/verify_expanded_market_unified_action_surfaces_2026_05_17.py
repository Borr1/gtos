#!/usr/bin/env python3
"""Verify expanded-market unified action surface checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_IMPLEMENTATION_ACTIONS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_ACTION_SURFACES"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_EVIDENCE_ACTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_EVIDENCE_ACTION_LEDGER_2026-05-17.jsonl"
INPUT_DECISION_ACTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_DECISION_ACTION_LEDGER_2026-05-17.jsonl"
INPUT_REDESIGN_ACTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REDESIGN_ACTION_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_SURFACE_LEDGER_2026-05-17.jsonl"
MEMBER_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
REDESIGN_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_unified_action_surfaces.py",
    ROUTE_DIR / "build_expanded_market_unified_action_surfaces_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, SURFACE_LEDGER, MEMBER_LEDGER, SELF_TEST_LEDGER, REDESIGN_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]


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
    input_evidence = read_jsonl(INPUT_EVIDENCE_ACTION_LEDGER)
    input_decisions = read_jsonl(INPUT_DECISION_ACTION_LEDGER)
    input_redesign = read_jsonl(INPUT_REDESIGN_ACTION_LEDGER)
    result = read_json(RESULT_PATH)
    surfaces = read_jsonl(SURFACE_LEDGER)
    members = read_jsonl(MEMBER_LEDGER)
    self_tests = read_jsonl(SELF_TEST_LEDGER)
    redesign_rows = read_jsonl(REDESIGN_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if input_result.get("ok") is not True:
        issues.append("input implementation-action result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(input_evidence) != 9266:
        issues.append("input evidence actions must equal 9266")
    if len(input_decisions) != 264:
        issues.append("input decision actions must equal 264")
    if len(input_redesign) != 153:
        issues.append("input redesign actions must equal 153")
    expected_outputs = {
        "action_surface_rows": len(surfaces),
        "action_surface_member_rows": len(members),
        "action_surface_self_test_rows": len(self_tests),
        "action_surface_redesign_rows": len(redesign_rows),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
        "surface_member_match_rows": sum(1 for row in members if row.get("surface_member_match")),
        "self_test_pass_rows": sum(
            1
            for row in self_tests
            if row.get("positive_scope_match") is True and row.get("negative_scope_mismatch_rejected") is True
        ),
    }
    for field, actual in expected_outputs.items():
        if counts.get(field) != actual:
            issues.append(f"{field} count mismatch")
    if len(surfaces) != 717:
        issues.append("action surface rows must equal 717")
    if len(members) != 9528:
        issues.append("action surface member rows must equal 9528")
    if len(self_tests) != 717:
        issues.append("self-test rows must equal 717")
    if len(redesign_rows) != 153:
        issues.append("redesign surface rows must equal 153")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if counts.get("surface_member_match_rows") != 9528:
        issues.append("every member row must match its surface")
    if counts.get("self_test_pass_rows") != 717:
        issues.append("every surface self-test must pass")
    all_rows = surfaces + members + self_tests + redesign_rows + aggregates + system_rows
    if any(not boundary_ok(row) for row in all_rows):
        issues.append("one or more output rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    implementation_inputs = [
        row for row in input_evidence + input_decisions
        if str(row.get("keep_kill_redesign_implement_decision") or "").startswith("IMPLEMENT_")
    ]
    if Counter(row.get("unified_implementation_action_row_id") for row in implementation_inputs) != Counter(
        row.get("input_unified_implementation_action_row_id") for row in members
    ):
        issues.append("implementation action ids are not covered exactly once by member rows")
    if Counter(row.get("unified_redesign_action_row_id") for row in input_redesign) != Counter(
        row.get("input_unified_redesign_action_row_id") for row in redesign_rows
    ):
        issues.append("redesign action ids are not covered exactly once")
    if any(not row.get("action_surface_expression") for row in surfaces):
        issues.append("one or more surfaces lack callable expression")
    if any(row.get("action_surface_status") != "ACTION_SURFACE_READY" for row in surfaces):
        issues.append("one or more surfaces are not ready")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "surface_rows": len(surfaces),
        "member_rows": len(members),
        "self_test_rows": len(self_tests),
        "redesign_rows": len(redesign_rows),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
