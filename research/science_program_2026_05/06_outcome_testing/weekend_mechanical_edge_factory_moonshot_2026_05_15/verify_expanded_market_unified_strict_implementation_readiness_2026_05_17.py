#!/usr/bin/env python3
"""Verify strict implementation-readiness checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_STRICT_ACTION_SURFACE_REPAIR"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_READINESS"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
STRICT_SURFACE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_STRICT_SURFACE_LEDGER_2026-05-17.jsonl"
STRICT_SURFACE_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_STRICT_SURFACE_EXECUTION_LEDGER_2026-05-17.jsonl"
STRICT_MEMBER_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_STRICT_MEMBER_EXECUTION_LEDGER_2026-05-17.jsonl"
STRICT_REDESIGN_PRESERVATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_STRICT_REDESIGN_PRESERVATION_LEDGER_2026-05-17.jsonl"
STRICT_REPAIR_PROOF_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_STRICT_REPAIR_PROOF_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_SURFACE_READINESS_LEDGER_2026-05-17.jsonl"
MEMBER_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_READINESS_LEDGER_2026-05-17.jsonl"
REDESIGN_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_READINESS_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_unified_strict_implementation_readiness.py",
    ROUTE_DIR / "build_expanded_market_unified_strict_implementation_readiness_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, SURFACE_LEDGER, MEMBER_LEDGER, REDESIGN_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]


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
    strict_surfaces = read_jsonl(STRICT_SURFACE_LEDGER)
    strict_executions = read_jsonl(STRICT_SURFACE_EXECUTION_LEDGER)
    member_executions = read_jsonl(STRICT_MEMBER_EXECUTION_LEDGER)
    redesign_preservations = read_jsonl(STRICT_REDESIGN_PRESERVATION_LEDGER)
    repair_proofs = read_jsonl(STRICT_REPAIR_PROOF_LEDGER)
    result = read_json(RESULT_PATH)
    surface_rows = read_jsonl(SURFACE_LEDGER)
    member_rows = read_jsonl(MEMBER_LEDGER)
    redesign_rows = read_jsonl(REDESIGN_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    issue_rows = read_jsonl(ISSUE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if input_result.get("ok") is not True:
        issues.append("input strict repair result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")

    expected = {
        "input_strict_surface_rows": len(strict_surfaces),
        "input_strict_surface_execution_rows": len(strict_executions),
        "input_strict_member_execution_rows": len(member_executions),
        "input_strict_redesign_preservation_rows": len(redesign_preservations),
        "input_strict_repair_proof_rows": len(repair_proofs),
        "strict_implementation_surface_rows": len(surface_rows),
        "strict_implementation_member_rows": len(member_rows),
        "strict_implementation_redesign_rows": len(redesign_rows),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issue_rows),
        "system_rows": len(system_rows),
        "implementation_ready_surface_rows": sum(
            1 for row in surface_rows if row.get("implementation_readiness_status") == "STRICT_IMPLEMENTATION_READY"
        ),
        "implementation_ready_member_rows": sum(
            1 for row in member_rows if row.get("implementation_member_status") == "STRICT_IMPLEMENTATION_MEMBER_READY"
        ),
        "redesign_evidence_preserved_rows": sum(
            1
            for row in redesign_rows
            if row.get("implementation_redesign_status") == "STRICT_IMPLEMENTATION_REDESIGN_EVIDENCE_PRESERVED"
        ),
        "member_rows_with_simulated_r": sum(1 for row in member_rows if row.get("missing_simulated_field") is None),
        "redesign_rows_with_simulated_r": sum(1 for row in redesign_rows if row.get("missing_simulated_field") is None),
    }
    for field, actual in expected.items():
        if counts.get(field) != actual:
            issues.append(f"{field} count mismatch")

    fixed = {
        "input_strict_surface_rows": 717,
        "input_strict_surface_execution_rows": 717,
        "input_strict_member_execution_rows": 9528,
        "input_strict_redesign_preservation_rows": 153,
        "input_strict_repair_proof_rows": 2,
        "strict_implementation_surface_rows": 717,
        "strict_implementation_member_rows": 9528,
        "strict_implementation_redesign_rows": 153,
        "issue_rows": 0,
        "system_rows": 1,
        "implementation_ready_surface_rows": 717,
        "implementation_ready_member_rows": 9528,
        "redesign_evidence_preserved_rows": 153,
        "member_rows_with_simulated_r": 9528,
        "redesign_rows_with_simulated_r": 153,
    }
    for field, expected_count in fixed.items():
        if counts.get(field) != expected_count:
            issues.append(f"{field} must equal {expected_count}")

    all_rows = surface_rows + member_rows + redesign_rows + aggregate_rows + issue_rows + system_rows
    if any(not boundary_ok(row) for row in all_rows):
        issues.append("one or more output rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if Counter(row.get("strict_action_surface_row_id") for row in strict_surfaces) != Counter(
        row.get("input_strict_action_surface_row_id") for row in surface_rows
    ):
        issues.append("strict surfaces are not covered exactly once")
    if Counter(row.get("strict_action_surface_member_execution_row_id") for row in member_executions) != Counter(
        row.get("input_strict_action_surface_member_execution_row_id") for row in member_rows
    ):
        issues.append("strict member executions are not covered exactly once")
    if Counter(row.get("strict_action_surface_redesign_preservation_row_id") for row in redesign_preservations) != Counter(
        row.get("input_strict_action_surface_redesign_preservation_row_id") for row in redesign_rows
    ):
        issues.append("strict redesign preservations are not covered exactly once")
    if any(row.get("missing_simulated_field") for row in member_rows + redesign_rows):
        issues.append("one or more readiness rows lack simulated R fields")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "surface_rows": len(surface_rows),
        "member_rows": len(member_rows),
        "redesign_rows": len(redesign_rows),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
