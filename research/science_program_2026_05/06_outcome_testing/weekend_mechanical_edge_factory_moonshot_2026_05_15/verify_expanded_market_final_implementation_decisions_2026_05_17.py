#!/usr/bin/env python3
"""Verify expanded-market final implementation decision checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PRESERVATION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PACKAGE_REVIEW_PRESERVATION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_FINAL_IMPLEMENTATION_DECISIONS"

PRESERVATION_RESULT = ROUTE_DIR / f"{PRESERVATION_PREFIX}_RESULT_2026-05-17.json"
CANDIDATE_LEDGER = ROUTE_DIR / f"{PRESERVATION_PREFIX}_CANDIDATE_LEDGER_2026-05-17.jsonl"
MEMBER_LEDGER = ROUTE_DIR / f"{PRESERVATION_PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PRESERVATION_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
REDESIGN_LEDGER = ROUTE_DIR / f"{PRESERVATION_PREFIX}_REDESIGN_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_DECISION_LEDGER_2026-05-17.jsonl"
MEMBER_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
EVIDENCE_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
REDESIGN_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_LEDGER_2026-05-17.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_final_implementation_decisions.py",
    ROUTE_DIR / "build_expanded_market_final_implementation_decisions_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    DECISION_LEDGER,
    MEMBER_DECISION_LEDGER,
    EVIDENCE_DECISION_LEDGER,
    REDESIGN_DECISION_LEDGER,
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
    preservation_result = read_json(PRESERVATION_RESULT)
    input_candidates = read_jsonl(CANDIDATE_LEDGER)
    input_members = read_jsonl(MEMBER_LEDGER)
    input_evidence = read_jsonl(EVIDENCE_LEDGER)
    input_redesign = read_jsonl(REDESIGN_LEDGER)
    result = read_json(RESULT_PATH)
    decisions = read_jsonl(DECISION_LEDGER)
    members = read_jsonl(MEMBER_DECISION_LEDGER)
    evidence = read_jsonl(EVIDENCE_DECISION_LEDGER)
    redesign = read_jsonl(REDESIGN_DECISION_LEDGER)
    controls = read_jsonl(CONTROL_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if preservation_result.get("ok") is not True:
        issues.append("input CP232 result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    expected = {
        "input candidates": (len(input_candidates), 221),
        "input members": (len(input_members), 1597),
        "input evidence": (len(input_evidence), 9266),
        "input redesign": (len(input_redesign), 151),
    }
    for label, (actual, wanted) in expected.items():
        if actual != wanted:
            issues.append(f"{label} count changed from {wanted} to {actual}")

    count_checks = {
        "final_implementation_decision_rows": len(decisions),
        "final_implementation_member_rows": len(members),
        "final_implementation_evidence_rows": len(evidence),
        "final_implementation_redesign_rows": len(redesign),
        "final_implementation_control_rows": len(controls),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
    }
    for field, actual in count_checks.items():
        if counts.get(field) != actual:
            issues.append(f"{field} count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len(decisions) != 221:
        issues.append("final decision rows must equal 221")
    if len(members) != 1597:
        issues.append("member decision rows must equal 1597")
    if len(evidence) != 9266:
        issues.append("evidence decision rows must equal 9266")
    if len(redesign) != 151:
        issues.append("redesign decision rows must equal 151")
    if len(controls) != len(decisions):
        issues.append("each final decision must have one control row")

    all_rows = decisions + members + evidence + redesign + controls + aggregates + system_rows
    if any(not boundary_ok(row) for row in all_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")

    if any(row.get("final_implementation_decision_status") != "FINAL_IMPLEMENTATION_DECISION_READY" for row in decisions):
        issues.append("one or more final implementation decisions are not ready")
    if counts.get("ready_final_implementation_decision_rows") != 221:
        issues.append("ready final implementation decision rows must equal 221")
    if counts.get("member_pass_rows") != 1597:
        issues.append("member pass rows must equal 1597")
    tied_input_evidence = sum(1 for row in input_evidence if row.get("input_package_preservation_candidate_row_id"))
    untied_input_evidence = len(input_evidence) - tied_input_evidence
    if counts.get("evidence_pass_rows") != tied_input_evidence:
        issues.append("evidence pass rows must equal tied input evidence rows")
    if counts.get("unpackaged_evidence_rows") != untied_input_evidence:
        issues.append("unpackaged evidence rows must equal untied input evidence rows")
    if counts.get("terminal_redesign_rows") != 151:
        issues.append("terminal redesign rows must equal 151")
    if counts.get("control_pass_rows") != 221:
        issues.append("control pass rows must equal 221")

    if sum(as_int(row.get("member_rows_decided")) for row in decisions) != len(members):
        issues.append("decision member counts do not sum to member rows")
    if sum(as_int(row.get("evidence_rows_decided")) for row in decisions) != tied_input_evidence:
        issues.append("decision evidence counts do not sum to tied evidence rows")
    if sum(as_int(row.get("member_rows")) for row in aggregates) != len(members):
        issues.append("aggregate member counts do not sum to member rows")

    if Counter(row.get("package_preservation_candidate_row_id") for row in input_candidates) != Counter(
        row.get("input_package_preservation_candidate_row_id") for row in decisions
    ):
        issues.append("input candidate ids are not covered exactly once")
    if Counter(row.get("package_preservation_member_row_id") for row in input_members) != Counter(
        row.get("input_package_preservation_member_row_id") for row in members
    ):
        issues.append("input member ids are not covered exactly once")
    if Counter(row.get("package_preservation_evidence_row_id") for row in input_evidence) != Counter(
        row.get("input_package_preservation_evidence_row_id") for row in evidence
    ):
        issues.append("input evidence ids are not covered exactly once")
    if Counter(row.get("package_preservation_redesign_row_id") for row in input_redesign) != Counter(
        row.get("input_package_preservation_redesign_row_id") for row in redesign
    ):
        issues.append("input redesign ids are not covered exactly once")

    decision_counts = Counter(row.get("keep_kill_redesign_implement_decision") for row in decisions)
    evidence_counts = Counter(row.get("keep_kill_redesign_implement_decision") for row in evidence)
    redesign_counts = Counter(row.get("keep_kill_redesign_implement_decision") for row in redesign)
    if decision_counts.get("IMPLEMENT_EXPANDED_MARKET_FINAL_BRANCH_LOCAL_DECISION") != 221:
        issues.append("all final candidate decisions must be implement decisions")
    if evidence_counts.get("IMPLEMENT_EXPANDED_MARKET_FINAL_DECISION_EVIDENCE") != tied_input_evidence:
        issues.append("tied evidence implement count mismatch")
    if evidence_counts.get("REDESIGN_EXPANDED_MARKET_FINAL_DECISION_UNPACKAGED_EVIDENCE") != untied_input_evidence:
        issues.append("untied evidence redesign count mismatch")
    if redesign_counts.get("REDESIGN_EXPANDED_MARKET_FINAL_BRANCH_LOCAL_CAPACITY") != 151:
        issues.append("terminal capacity redesign count mismatch")
    if any(not row.get("final_decision_payload_sha256") for row in decisions):
        issues.append("one or more final decisions lack payload hash")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "decision_rows": len(decisions),
        "member_rows": len(members),
        "evidence_rows": len(evidence),
        "redesign_rows": len(redesign),
        "aggregate_rows": len(aggregates),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
