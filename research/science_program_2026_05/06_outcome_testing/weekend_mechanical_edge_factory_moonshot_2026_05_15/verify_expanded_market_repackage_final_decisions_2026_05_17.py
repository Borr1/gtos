#!/usr/bin/env python3
"""Verify expanded-market repackage final decision checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
EXECUTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPACKAGE_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPACKAGE_FINAL_DECISIONS"

EXECUTION_RESULT = ROUTE_DIR / f"{EXECUTION_PREFIX}_RESULT_2026-05-17.json"
EXECUTION_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"
REPACKAGE_EVIDENCE_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_REPACKAGE_EVIDENCE_LEDGER_2026-05-17.jsonl"
EXISTING_EVIDENCE_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_EXISTING_EVIDENCE_LEDGER_2026-05-17.jsonl"
TERMINAL_REDESIGN_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_TERMINAL_REDESIGN_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
EXISTING_CARRY_LEDGER = ROUTE_DIR / f"{PREFIX}_EXISTING_EVIDENCE_LEDGER_2026-05-17.jsonl"
TERMINAL_CARRY_LEDGER = ROUTE_DIR / f"{PREFIX}_TERMINAL_REDESIGN_LEDGER_2026-05-17.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_repackage_final_decisions.py",
    ROUTE_DIR / "build_expanded_market_repackage_final_decisions_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    DECISION_LEDGER,
    EVIDENCE_LEDGER,
    EXISTING_CARRY_LEDGER,
    TERMINAL_CARRY_LEDGER,
    CONTROL_LEDGER,
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


def as_int(value: Any) -> int:
    if value is None or value == "" or isinstance(value, bool):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def main() -> None:
    issues: list[str] = []
    execution_result = read_json(EXECUTION_RESULT)
    input_executions = read_jsonl(EXECUTION_LEDGER)
    input_evidence = read_jsonl(REPACKAGE_EVIDENCE_LEDGER)
    input_existing = read_jsonl(EXISTING_EVIDENCE_LEDGER)
    input_terminal = read_jsonl(TERMINAL_REDESIGN_LEDGER)
    result = read_json(RESULT_PATH)
    decisions = read_jsonl(DECISION_LEDGER)
    evidence = read_jsonl(EVIDENCE_LEDGER)
    existing = read_jsonl(EXISTING_CARRY_LEDGER)
    terminal = read_jsonl(TERMINAL_CARRY_LEDGER)
    controls = read_jsonl(CONTROL_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if execution_result.get("ok") is not True:
        issues.append("input CP235 result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    expected_inputs = {
        "input executions": (len(input_executions), 43),
        "input repackage evidence": (len(input_evidence), 813),
        "input existing evidence": (len(input_existing), 8453),
        "input terminal redesign": (len(input_terminal), 151),
    }
    for label, (actual, wanted) in expected_inputs.items():
        if actual != wanted:
            issues.append(f"{label} count changed from {wanted} to {actual}")
    expected_outputs = {
        "repackage_final_decision_rows": len(decisions),
        "repackage_final_evidence_rows": len(evidence),
        "repackage_final_existing_evidence_rows": len(existing),
        "repackage_final_terminal_redesign_rows": len(terminal),
        "repackage_final_control_rows": len(controls),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
    }
    for field, actual in expected_outputs.items():
        if counts.get(field) != actual:
            issues.append(f"{field} count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len(controls) != len(decisions):
        issues.append("each decision must have one control")
    all_rows = decisions + evidence + existing + terminal + controls + aggregates + system_rows
    if any(not boundary_ok(row) for row in all_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")

    if any(row.get("repackage_final_decision_status") != "REPACKAGE_FINAL_DECISION_READY" for row in decisions):
        issues.append("one or more final decisions are not ready")
    if counts.get("ready_repackage_final_decision_rows") != 43:
        issues.append("ready final decision rows must equal 43")
    if counts.get("repair_repackage_final_decision_rows") != 0:
        issues.append("repair final decision rows must equal 0")
    if counts.get("evidence_pass_rows") != 813:
        issues.append("evidence pass rows must equal 813")
    if counts.get("control_pass_rows") != 43:
        issues.append("control pass rows must equal 43")
    if sum(as_int(row.get("candidate_evidence_rows_decided")) for row in decisions) != len(evidence):
        issues.append("decision evidence counts do not sum to evidence rows")
    if sum(as_int(row.get("candidate_evidence_rows_decided")) for row in aggregates) != len(evidence):
        issues.append("aggregate evidence counts do not sum to evidence rows")

    if Counter(row.get("repackage_execution_row_id") for row in input_executions) != Counter(
        row.get("input_repackage_execution_row_id") for row in decisions
    ):
        issues.append("input execution ids are not covered exactly once")
    if Counter(row.get("repackage_evidence_execution_row_id") for row in input_evidence) != Counter(
        row.get("input_repackage_evidence_execution_row_id") for row in evidence
    ):
        issues.append("input repackage evidence ids are not covered exactly once")
    if Counter(row.get("existing_evidence_preservation_row_id") for row in input_existing) != Counter(
        row.get("input_existing_evidence_preservation_row_id") for row in existing
    ):
        issues.append("input existing evidence ids are not covered exactly once")
    if Counter(row.get("repackage_terminal_redesign_execution_row_id") for row in input_terminal) != Counter(
        row.get("input_repackage_terminal_redesign_execution_row_id") for row in terminal
    ):
        issues.append("input terminal redesign ids are not covered exactly once")
    if any(not row.get("repackage_final_decision_payload_sha256") for row in decisions):
        issues.append("one or more decisions lack payload hash")
    decision_counts = Counter(row.get("keep_kill_redesign_implement_decision") for row in decisions)
    if decision_counts.get("IMPLEMENT_EXPANDED_MARKET_REPACKAGE_FINAL_DECISION") != 43:
        issues.append("all repackage final decisions must be implement decisions")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "decision_rows": len(decisions),
        "evidence_rows": len(evidence),
        "existing_rows": len(existing),
        "terminal_rows": len(terminal),
        "aggregate_rows": len(aggregates),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
