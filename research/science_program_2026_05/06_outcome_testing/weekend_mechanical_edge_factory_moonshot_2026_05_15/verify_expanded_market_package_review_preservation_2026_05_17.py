#!/usr/bin/env python3
"""Verify expanded-market package-review preservation checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
REVIEW_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PACKAGE_REVIEW_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PACKAGE_REVIEW_PRESERVATION"

REVIEW_RESULT = ROUTE_DIR / f"{REVIEW_PREFIX}_RESULT_2026-05-17.json"
ARTIFACT_LEDGER = ROUTE_DIR / f"{REVIEW_PREFIX}_ARTIFACT_LEDGER_2026-05-17.jsonl"
MEMBER_LEDGER = ROUTE_DIR / f"{REVIEW_PREFIX}_MEMBER_EXECUTION_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{REVIEW_PREFIX}_EVIDENCE_EXECUTION_LEDGER_2026-05-17.jsonl"
REDESIGN_LEDGER = ROUTE_DIR / f"{REVIEW_PREFIX}_REDESIGN_EXECUTION_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_CANDIDATE_LEDGER_2026-05-17.jsonl"
MEMBER_PRESERVATION_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
EVIDENCE_PRESERVATION_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
REDESIGN_PRESERVATION_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_package_review_preservation.py",
    ROUTE_DIR / "build_expanded_market_package_review_preservation_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, CANDIDATE_LEDGER, MEMBER_PRESERVATION_LEDGER, EVIDENCE_PRESERVATION_LEDGER, REDESIGN_PRESERVATION_LEDGER, SELF_TEST_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]


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
    review_result = read_json(REVIEW_RESULT)
    input_artifacts = read_jsonl(ARTIFACT_LEDGER)
    input_members = read_jsonl(MEMBER_LEDGER)
    input_evidence = read_jsonl(EVIDENCE_LEDGER)
    input_redesign = read_jsonl(REDESIGN_LEDGER)
    result = read_json(RESULT_PATH)
    candidates = read_jsonl(CANDIDATE_LEDGER)
    members = read_jsonl(MEMBER_PRESERVATION_LEDGER)
    evidence = read_jsonl(EVIDENCE_PRESERVATION_LEDGER)
    redesign = read_jsonl(REDESIGN_PRESERVATION_LEDGER)
    self_tests = read_jsonl(SELF_TEST_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if review_result.get("ok") is not True:
        issues.append("input CP231 result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    expected = {
        "input artifacts": (len(input_artifacts), 221),
        "input members": (len(input_members), 1597),
        "input evidence": (len(input_evidence), 9266),
        "input redesign": (len(input_redesign), 151),
    }
    for label, (actual, wanted) in expected.items():
        if actual != wanted:
            issues.append(f"{label} count changed from {wanted} to {actual}")
    if counts.get("package_preservation_candidate_rows") != len(candidates):
        issues.append("candidate row count mismatch")
    if counts.get("package_preservation_member_rows") != len(members):
        issues.append("member row count mismatch")
    if counts.get("package_preservation_evidence_rows") != len(evidence):
        issues.append("evidence row count mismatch")
    if counts.get("package_preservation_redesign_rows") != len(redesign):
        issues.append("redesign row count mismatch")
    if counts.get("package_preservation_self_test_rows") != len(self_tests):
        issues.append("self-test row count mismatch")
    if counts.get("aggregate_rows") != len(aggregates):
        issues.append("aggregate row count mismatch")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len(candidates) != 221:
        issues.append("candidate rows must equal 221")
    if len(members) != 1597:
        issues.append("member rows must equal 1597")
    if len(evidence) != 9266:
        issues.append("evidence rows must equal 9266")
    if len(redesign) != 151:
        issues.append("redesign rows must equal 151")
    if len(self_tests) != len(candidates):
        issues.append("each candidate must have one self-test")
    if any(not boundary_ok(row) for row in candidates + members + evidence + redesign + self_tests + aggregates + system_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if any(row.get("preservation_status") != "PACKAGE_REVIEW_PRESERVATION_READY" for row in candidates):
        issues.append("one or more preservation candidates are not ready")
    if counts.get("ready_candidate_rows") != 221:
        issues.append("ready candidate rows must equal 221")
    if counts.get("self_test_pass_rows") != 221:
        issues.append("self-test pass rows must equal 221")
    if any(not row.get("implementation_payload_sha256") for row in candidates):
        issues.append("one or more candidates lack implementation payload hash")
    if sum(as_int(row.get("member_rows_preserved")) for row in candidates) != len(members):
        issues.append("candidate member counts do not sum to member rows")
    if sum(as_int(row.get("evidence_rows_preserved")) for row in candidates) + (len(evidence) - sum(as_int(row.get("evidence_rows_preserved")) for row in candidates)) != len(evidence):
        issues.append("evidence preservation count arithmetic failed")
    if sum(as_int(row.get("member_rows")) for row in aggregates) != len(members):
        issues.append("aggregate member counts do not sum to member rows")

    if Counter(row.get("package_review_artifact_row_id") for row in input_artifacts) != Counter(
        row.get("input_package_review_artifact_row_id") for row in candidates
    ):
        issues.append("input artifact ids are not covered exactly once")
    if Counter(row.get("package_review_member_execution_row_id") for row in input_members) != Counter(
        row.get("input_package_review_member_execution_row_id") for row in members
    ):
        issues.append("input member ids are not covered exactly once")
    if Counter(row.get("package_review_evidence_execution_row_id") for row in input_evidence) != Counter(
        row.get("input_package_review_evidence_execution_row_id") for row in evidence
    ):
        issues.append("input evidence ids are not covered exactly once")
    if Counter(row.get("package_review_redesign_execution_row_id") for row in input_redesign) != Counter(
        row.get("input_package_review_redesign_execution_row_id") for row in redesign
    ):
        issues.append("input redesign ids are not covered exactly once")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "candidate_rows": len(candidates),
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
