#!/usr/bin/env python3
"""Verify expanded-market repackage execution checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
UNPACKAGED_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNPACKAGED_EVIDENCE_RESOLUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPACKAGE_EXECUTION"

UNPACKAGED_RESULT = ROUTE_DIR / f"{UNPACKAGED_PREFIX}_RESULT_2026-05-17.json"
REPACKAGE_CANDIDATE_LEDGER = ROUTE_DIR / f"{UNPACKAGED_PREFIX}_REPACKAGE_CANDIDATE_LEDGER_2026-05-17.jsonl"
RESOLUTION_LEDGER = ROUTE_DIR / f"{UNPACKAGED_PREFIX}_RESOLUTION_LEDGER_2026-05-17.jsonl"
TERMINAL_REDESIGN_LEDGER = ROUTE_DIR / f"{UNPACKAGED_PREFIX}_TERMINAL_REDESIGN_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"
REPACKAGE_EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_REPACKAGE_EVIDENCE_LEDGER_2026-05-17.jsonl"
EXISTING_EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EXISTING_EVIDENCE_LEDGER_2026-05-17.jsonl"
TERMINAL_REDESIGN_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_TERMINAL_REDESIGN_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_repackage_execution.py",
    ROUTE_DIR / "build_expanded_market_repackage_execution_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    EXECUTION_LEDGER,
    REPACKAGE_EVIDENCE_LEDGER,
    EXISTING_EVIDENCE_LEDGER,
    TERMINAL_REDESIGN_EXECUTION_LEDGER,
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
    terms = blocked_terms()
    for path in paths:
        text = read_text(path)
        for term in terms:
            if term in text:
                issues.append(f"blocked term {term!r} found in {path.relative_to(REPO)}")
    return issues


def main() -> None:
    issues: list[str] = []
    unpackaged_result = read_json(UNPACKAGED_RESULT)
    input_candidates = read_jsonl(REPACKAGE_CANDIDATE_LEDGER)
    input_resolution = read_jsonl(RESOLUTION_LEDGER)
    input_terminal = read_jsonl(TERMINAL_REDESIGN_LEDGER)
    result = read_json(RESULT_PATH)
    executions = read_jsonl(EXECUTION_LEDGER)
    repackage_evidence = read_jsonl(REPACKAGE_EVIDENCE_LEDGER)
    existing_evidence = read_jsonl(EXISTING_EVIDENCE_LEDGER)
    terminal_execution = read_jsonl(TERMINAL_REDESIGN_EXECUTION_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if unpackaged_result.get("ok") is not True:
        issues.append("input CP234 result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    expected_inputs = {
        "input candidates": (len(input_candidates), 43),
        "input resolution": (len(input_resolution), 9266),
        "input terminal redesign": (len(input_terminal), 151),
    }
    for label, (actual, wanted) in expected_inputs.items():
        if actual != wanted:
            issues.append(f"{label} count changed from {wanted} to {actual}")
    expected_outputs = {
        "repackage_execution_rows": len(executions),
        "repackage_evidence_execution_rows": len(repackage_evidence),
        "existing_evidence_preservation_rows": len(existing_evidence),
        "terminal_redesign_execution_rows": len(terminal_execution),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
    }
    for field, actual in expected_outputs.items():
        if counts.get(field) != actual:
            issues.append(f"{field} count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len(executions) != 43:
        issues.append("execution rows must equal 43")
    input_resolution_status = Counter(row.get("resolution_status") for row in input_resolution)
    if len(repackage_evidence) != input_resolution_status.get("UNPACKAGED_EVIDENCE_RESOLUTION_REPACKAGE_REQUIRED", 0):
        issues.append("repackage evidence rows must equal repackage-required resolution rows")
    if len(existing_evidence) != input_resolution_status.get("UNPACKAGED_EVIDENCE_RESOLUTION_ALREADY_IMPLEMENTED", 0):
        issues.append("existing evidence rows must equal already implemented resolution rows")
    if len(repackage_evidence) + len(existing_evidence) != len(input_resolution):
        issues.append("resolution evidence rows are not fully preserved")
    if len(terminal_execution) != len(input_terminal):
        issues.append("terminal redesign rows are not fully preserved")

    all_rows = executions + repackage_evidence + existing_evidence + terminal_execution + aggregates + system_rows
    if any(not boundary_ok(row) for row in all_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if any(row.get("repackage_execution_status") != "UNPACKAGED_REPACKAGE_EXECUTION_PASS" for row in executions):
        issues.append("one or more repackage executions did not pass")
    if counts.get("repackage_execution_pass_rows") != 43:
        issues.append("repackage execution pass rows must equal 43")
    if counts.get("repackage_execution_repair_rows") != 0:
        issues.append("repackage execution repair rows must equal 0")
    if counts.get("source_proof_pass_rows") != 43:
        issues.append("source proof pass rows must equal 43")
    if any(row.get("source_path_exists") is not True or row.get("source_file_hash_match") is not True for row in executions):
        issues.append("one or more repackage executions lack source proof")
    if any(
        row.get("terminal_redesign_execution_status") != "REPACKAGE_TERMINAL_REDESIGN_SOURCE_PROOF_PASS"
        for row in terminal_execution
    ):
        issues.append("one or more terminal redesign rows lack source proof")
    if Counter(row.get("unpackaged_repackage_candidate_row_id") for row in input_candidates) != Counter(
        row.get("input_unpackaged_repackage_candidate_row_id") for row in executions
    ):
        issues.append("input repackage candidate ids are not covered exactly once")
    if Counter(row.get("unpackaged_evidence_resolution_row_id") for row in input_resolution) != (
        Counter(row.get("input_unpackaged_evidence_resolution_row_id") for row in repackage_evidence)
        + Counter(row.get("input_unpackaged_evidence_resolution_row_id") for row in existing_evidence)
    ):
        issues.append("input resolution ids are not covered exactly once")
    if Counter(row.get("unpackaged_terminal_redesign_row_id") for row in input_terminal) != Counter(
        row.get("input_unpackaged_terminal_redesign_row_id") for row in terminal_execution
    ):
        issues.append("input terminal redesign ids are not covered exactly once")
    if any(not row.get("repackage_execution_payload_sha256") for row in executions):
        issues.append("one or more executions lack payload hash")

    decision_counts = Counter(row.get("keep_kill_redesign_implement_decision") for row in executions)
    if decision_counts.get("IMPLEMENT_EXPANDED_MARKET_UNPACKAGED_REPACKAGE_EXECUTION") != 43:
        issues.append("all repackage executions must be implement decisions")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "execution_rows": len(executions),
        "repackage_evidence_rows": len(repackage_evidence),
        "existing_evidence_rows": len(existing_evidence),
        "terminal_redesign_rows": len(terminal_execution),
        "aggregate_rows": len(aggregates),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
