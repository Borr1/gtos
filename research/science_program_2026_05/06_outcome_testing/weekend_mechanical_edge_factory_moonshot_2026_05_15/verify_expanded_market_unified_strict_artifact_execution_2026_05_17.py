#!/usr/bin/env python3
"""Verify strict artifact execution checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_READINESS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_STRICT_ARTIFACT_EXECUTION"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
SURFACE_READINESS_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SURFACE_READINESS_LEDGER_2026-05-17.jsonl"
MEMBER_READINESS_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MEMBER_READINESS_LEDGER_2026-05-17.jsonl"
REDESIGN_READINESS_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REDESIGN_READINESS_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ARTIFACT_LEDGER = ROUTE_DIR / f"{PREFIX}_ARTIFACT_LEDGER_2026-05-17.jsonl"
MEMBER_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_EXECUTION_LEDGER_2026-05-17.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_LEDGER_2026-05-17.jsonl"
REDESIGN_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_unified_strict_artifact_execution.py",
    ROUTE_DIR / "build_expanded_market_unified_strict_artifact_execution_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, ARTIFACT_LEDGER, MEMBER_EXECUTION_LEDGER, CONTROL_LEDGER, REDESIGN_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]


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
    surface_readiness = read_jsonl(SURFACE_READINESS_LEDGER)
    member_readiness = read_jsonl(MEMBER_READINESS_LEDGER)
    redesign_readiness = read_jsonl(REDESIGN_READINESS_LEDGER)
    result = read_json(RESULT_PATH)
    artifacts = read_jsonl(ARTIFACT_LEDGER)
    member_executions = read_jsonl(MEMBER_EXECUTION_LEDGER)
    controls = read_jsonl(CONTROL_LEDGER)
    redesigns = read_jsonl(REDESIGN_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    issue_rows = read_jsonl(ISSUE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if input_result.get("ok") is not True:
        issues.append("input readiness result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")

    expected = {
        "input_surface_readiness_rows": len(surface_readiness),
        "input_member_readiness_rows": len(member_readiness),
        "input_redesign_readiness_rows": len(redesign_readiness),
        "strict_artifact_rows": len(artifacts),
        "strict_artifact_member_execution_rows": len(member_executions),
        "strict_artifact_control_rows": len(controls),
        "strict_artifact_redesign_rows": len(redesigns),
        "aggregate_rows": len(aggregates),
        "issue_rows": len(issue_rows),
        "system_rows": len(system_rows),
        "artifact_ready_rows": sum(
            1 for row in artifacts if row.get("artifact_execution_status") == "STRICT_IMPLEMENTATION_ARTIFACT_READY"
        ),
        "artifact_member_execution_pass_rows": sum(
            1
            for row in member_executions
            if row.get("artifact_member_execution_status") == "STRICT_ARTIFACT_MEMBER_EXECUTION_PASS"
        ),
        "artifact_control_pass_rows": sum(
            1 for row in controls if row.get("artifact_control_status") == "STRICT_ARTIFACT_CONTROL_PASS"
        ),
        "artifact_redesign_preserved_rows": sum(
            1 for row in redesigns if row.get("artifact_redesign_status") == "STRICT_ARTIFACT_REDESIGN_EVIDENCE_PRESERVED"
        ),
        "member_rows_with_simulated_r": sum(1 for row in member_executions if row.get("missing_simulated_field") is None),
        "redesign_rows_with_simulated_r": sum(1 for row in redesigns if row.get("missing_simulated_field") is None),
    }
    for field, actual in expected.items():
        if counts.get(field) != actual:
            issues.append(f"{field} count mismatch")

    fixed = {
        "input_surface_readiness_rows": 717,
        "input_member_readiness_rows": 9528,
        "input_redesign_readiness_rows": 153,
        "strict_artifact_rows": 717,
        "strict_artifact_member_execution_rows": 9528,
        "strict_artifact_control_rows": 717,
        "strict_artifact_redesign_rows": 153,
        "issue_rows": 0,
        "system_rows": 1,
        "artifact_ready_rows": 717,
        "artifact_member_execution_pass_rows": 9528,
        "artifact_control_pass_rows": 717,
        "artifact_redesign_preserved_rows": 153,
        "member_rows_with_simulated_r": 9528,
        "redesign_rows_with_simulated_r": 153,
    }
    for field, expected_count in fixed.items():
        if counts.get(field) != expected_count:
            issues.append(f"{field} must equal {expected_count}")

    all_rows = artifacts + member_executions + controls + redesigns + aggregates + issue_rows + system_rows
    if any(not boundary_ok(row) for row in all_rows):
        issues.append("one or more output rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if Counter(row.get("strict_implementation_readiness_row_id") for row in surface_readiness) != Counter(
        row.get("input_strict_implementation_readiness_row_id") for row in artifacts
    ):
        issues.append("surface readiness rows are not covered exactly once")
    if Counter(row.get("strict_implementation_member_row_id") for row in member_readiness) != Counter(
        row.get("input_strict_implementation_member_row_id") for row in member_executions
    ):
        issues.append("member readiness rows are not covered exactly once")
    if Counter(row.get("strict_implementation_redesign_row_id") for row in redesign_readiness) != Counter(
        row.get("input_strict_implementation_redesign_row_id") for row in redesigns
    ):
        issues.append("redesign readiness rows are not covered exactly once")
    if any(row.get("missing_simulated_field") for row in member_executions + redesigns):
        issues.append("one or more artifact execution rows lack simulated R fields")
    if any(row.get("artifact_member_match") is not True for row in member_executions):
        issues.append("one or more artifact member executions failed")
    if any(row.get("positive_member_match") is not True for row in controls):
        issues.append("one or more artifact controls lack positive match")
    if any(row.get("negative_surface_mismatch_rejected") is not True for row in controls):
        issues.append("one or more artifact controls failed negative mismatch rejection")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "artifact_rows": len(artifacts),
        "member_execution_rows": len(member_executions),
        "redesign_rows": len(redesigns),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
