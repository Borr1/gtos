#!/usr/bin/env python3
"""Verify expanded-market unified final decision checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PACKAGE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_FINAL_IMPLEMENTATION_DECISIONS"
REPACKAGE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPACKAGE_FINAL_DECISIONS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNIFIED_FINAL_DECISIONS"

PACKAGE_RESULT = ROUTE_DIR / f"{PACKAGE_PREFIX}_RESULT_2026-05-17.json"
PACKAGE_DECISION_LEDGER = ROUTE_DIR / f"{PACKAGE_PREFIX}_DECISION_LEDGER_2026-05-17.jsonl"
PACKAGE_MEMBER_LEDGER = ROUTE_DIR / f"{PACKAGE_PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
PACKAGE_EVIDENCE_LEDGER = ROUTE_DIR / f"{PACKAGE_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
REPACKAGE_RESULT = ROUTE_DIR / f"{REPACKAGE_PREFIX}_RESULT_2026-05-17.json"
REPACKAGE_DECISION_LEDGER = ROUTE_DIR / f"{REPACKAGE_PREFIX}_DECISION_LEDGER_2026-05-17.jsonl"
REPACKAGE_EVIDENCE_LEDGER = ROUTE_DIR / f"{REPACKAGE_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
REPACKAGE_EXISTING_LEDGER = ROUTE_DIR / f"{REPACKAGE_PREFIX}_EXISTING_EVIDENCE_LEDGER_2026-05-17.jsonl"
REPACKAGE_TERMINAL_LEDGER = ROUTE_DIR / f"{REPACKAGE_PREFIX}_TERMINAL_REDESIGN_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_2026-05-17.jsonl"
MEMBER_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
TERMINAL_LEDGER = ROUTE_DIR / f"{PREFIX}_TERMINAL_REDESIGN_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_unified_final_decisions.py",
    ROUTE_DIR / "build_expanded_market_unified_final_decisions_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, DECISION_LEDGER, MEMBER_LEDGER, EVIDENCE_LEDGER, TERMINAL_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]


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
    package_result = read_json(PACKAGE_RESULT)
    repackage_result = read_json(REPACKAGE_RESULT)
    package_decisions = read_jsonl(PACKAGE_DECISION_LEDGER)
    package_members = read_jsonl(PACKAGE_MEMBER_LEDGER)
    package_evidence = read_jsonl(PACKAGE_EVIDENCE_LEDGER)
    repackage_decisions = read_jsonl(REPACKAGE_DECISION_LEDGER)
    repackage_evidence = read_jsonl(REPACKAGE_EVIDENCE_LEDGER)
    repackage_existing = read_jsonl(REPACKAGE_EXISTING_LEDGER)
    repackage_terminal = read_jsonl(REPACKAGE_TERMINAL_LEDGER)
    result = read_json(RESULT_PATH)
    decisions = read_jsonl(DECISION_LEDGER)
    members = read_jsonl(MEMBER_LEDGER)
    evidence = read_jsonl(EVIDENCE_LEDGER)
    terminal = read_jsonl(TERMINAL_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if package_result.get("ok") is not True:
        issues.append("input package result is not ok")
    if repackage_result.get("ok") is not True:
        issues.append("input repackage result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    expected_inputs = {
        "package decisions": (len(package_decisions), 221),
        "package members": (len(package_members), 1597),
        "package evidence": (len(package_evidence), 9266),
        "repackage decisions": (len(repackage_decisions), 43),
        "repackage evidence": (len(repackage_evidence), 813),
        "repackage existing evidence": (len(repackage_existing), 8453),
        "repackage terminal": (len(repackage_terminal), 151),
    }
    for label, (actual, wanted) in expected_inputs.items():
        if actual != wanted:
            issues.append(f"{label} count changed from {wanted} to {actual}")
    expected_outputs = {
        "unified_final_decision_rows": len(decisions),
        "unified_final_member_rows": len(members),
        "unified_final_evidence_rows": len(evidence),
        "unified_terminal_redesign_rows": len(terminal),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
    }
    for field, actual in expected_outputs.items():
        if counts.get(field) != actual:
            issues.append(f"{field} count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len(decisions) != 264:
        issues.append("unified final decision rows must equal 264")
    if len(members) != 1597:
        issues.append("unified final member rows must equal 1597")
    if len(evidence) != 9266:
        issues.append("unified final evidence rows must equal 9266")
    if len(terminal) != 151:
        issues.append("unified terminal redesign rows must equal 151")
    all_rows = decisions + members + evidence + terminal + aggregates + system_rows
    if any(not boundary_ok(row) for row in all_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    origin_counts = Counter(row.get("decision_origin") for row in decisions)
    if origin_counts.get("package_final") != 221:
        issues.append("package final decision count mismatch")
    if origin_counts.get("repackage_final") != 43:
        issues.append("repackage final decision count mismatch")
    evidence_origin_counts = Counter(row.get("evidence_origin") for row in evidence)
    if evidence_origin_counts.get("package_final") != 8453:
        issues.append("package final evidence count mismatch")
    if evidence_origin_counts.get("repackage_final") != 813:
        issues.append("repackage final evidence count mismatch")
    if counts.get("repackage_existing_rows_deduplicated") != 8453:
        issues.append("repackage existing evidence dedup count mismatch")
    if counts.get("ready_unified_final_decision_rows") != 264:
        issues.append("ready unified final decisions must equal 264")
    if any(row.get("unified_final_decision_status") != "UNIFIED_FINAL_DECISION_READY" for row in decisions):
        issues.append("one or more unified final decisions are not ready")
    if Counter(row.get("final_implementation_decision_row_id") for row in package_decisions) != Counter(
        row.get("input_final_implementation_decision_row_id") for row in decisions if row.get("decision_origin") == "package_final"
    ):
        issues.append("package decision ids are not covered exactly once")
    if Counter(row.get("repackage_final_decision_row_id") for row in repackage_decisions) != Counter(
        row.get("input_repackage_final_decision_row_id") for row in decisions if row.get("decision_origin") == "repackage_final"
    ):
        issues.append("repackage decision ids are not covered exactly once")
    package_pass_evidence = [
        row for row in package_evidence
        if row.get("final_implementation_evidence_status") == "FINAL_IMPLEMENTATION_EVIDENCE_DECISION_PASS"
    ]
    if Counter(row.get("final_implementation_evidence_row_id") for row in package_pass_evidence) != Counter(
        row.get("input_final_implementation_evidence_row_id") for row in evidence if row.get("evidence_origin") == "package_final"
    ):
        issues.append("package pass evidence ids are not covered exactly once")
    if Counter(row.get("repackage_final_evidence_row_id") for row in repackage_evidence) != Counter(
        row.get("input_repackage_final_evidence_row_id") for row in evidence if row.get("evidence_origin") == "repackage_final"
    ):
        issues.append("repackage evidence ids are not covered exactly once")
    if Counter(row.get("repackage_final_terminal_redesign_row_id") for row in repackage_terminal) != Counter(
        row.get("input_repackage_final_terminal_redesign_row_id") for row in terminal
    ):
        issues.append("terminal redesign ids are not covered exactly once")
    if any(not row.get("unified_final_decision_payload_sha256") for row in decisions):
        issues.append("one or more unified decisions lack payload hash")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "decision_rows": len(decisions),
        "member_rows": len(members),
        "evidence_rows": len(evidence),
        "terminal_rows": len(terminal),
        "aggregate_rows": len(aggregates),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
