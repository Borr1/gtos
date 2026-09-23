#!/usr/bin/env python3
"""Verify expanded-market package-slices checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
FINAL_REVIEW_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_FINAL_REVIEW_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PACKAGE_SLICES"

FINAL_REVIEW_RESULT = ROUTE_DIR / f"{FINAL_REVIEW_PREFIX}_RESULT_2026-05-17.json"
FINAL_REVIEW_LEDGER = ROUTE_DIR / f"{FINAL_REVIEW_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
FINAL_REVIEW_EVIDENCE_LEDGER = ROUTE_DIR / f"{FINAL_REVIEW_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SLICE_LEDGER = ROUTE_DIR / f"{PREFIX}_SLICE_LEDGER_2026-05-17.jsonl"
MEMBER_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
REDESIGN_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_CARRY_LEDGER_2026-05-17.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_package_slices.py",
    ROUTE_DIR / "build_expanded_market_package_slices_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    SLICE_LEDGER,
    MEMBER_LEDGER,
    EVIDENCE_LEDGER,
    REDESIGN_LEDGER,
    CONTROL_LEDGER,
    SELF_TEST_LEDGER,
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
    final_review_result = read_json(FINAL_REVIEW_RESULT)
    input_rows = read_jsonl(FINAL_REVIEW_LEDGER)
    input_evidence = read_jsonl(FINAL_REVIEW_EVIDENCE_LEDGER)
    result = read_json(RESULT_PATH)
    slices = read_jsonl(SLICE_LEDGER)
    members = read_jsonl(MEMBER_LEDGER)
    evidence = read_jsonl(EVIDENCE_LEDGER)
    redesign = read_jsonl(REDESIGN_LEDGER)
    controls = read_jsonl(CONTROL_LEDGER)
    self_tests = read_jsonl(SELF_TEST_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if final_review_result.get("ok") is not True:
        issues.append("input CP229 result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(input_rows) != 1748:
        issues.append(f"input final-review count changed from 1748 to {len(input_rows)}")
    if len(input_evidence) != 9266:
        issues.append(f"input final-review evidence count changed from 9266 to {len(input_evidence)}")
    if counts.get("package_slice_rows") != len(slices):
        issues.append("package slice row count mismatch")
    if counts.get("package_member_rows") != len(members):
        issues.append("package member row count mismatch")
    if counts.get("package_evidence_rows") != len(evidence):
        issues.append("package evidence row count mismatch")
    if counts.get("package_redesign_carry_rows") != len(redesign):
        issues.append("package redesign carry row count mismatch")
    if counts.get("package_control_rows") != len(controls):
        issues.append("package control row count mismatch")
    if counts.get("package_self_test_rows") != len(self_tests):
        issues.append("package self-test row count mismatch")
    if counts.get("aggregate_rows") != len(aggregates):
        issues.append("aggregate row count mismatch")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len(members) != 1597:
        issues.append("package member rows must equal 1597 final-review implement rows")
    if len(redesign) != 151:
        issues.append("redesign carry rows must equal 151 final-review redesign rows")
    if len(evidence) != len(input_evidence):
        issues.append("package evidence rows must preserve every final-review evidence row")
    if len(controls) != len(slices) or len(self_tests) != len(slices):
        issues.append("each package slice must have one control and one self-test row")
    if any(not boundary_ok(row) for row in slices + members + evidence + redesign + controls + self_tests + aggregates + system_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if len({row.get("package_slice_row_id") for row in slices}) != len(slices):
        issues.append("package slice ids are not unique")
    if len({row.get("package_member_row_id") for row in members}) != len(members):
        issues.append("package member ids are not unique")
    if len({row.get("package_evidence_row_id") for row in evidence}) != len(evidence):
        issues.append("package evidence ids are not unique")
    if any(row.get("self_test_status") != "PACKAGE_SLICE_SELF_TEST_PASS" for row in self_tests):
        issues.append("one or more package self-tests failed")
    if any(row.get("control_status") != "PACKAGE_CONTROL_PASS" for row in controls):
        issues.append("one or more package controls failed")
    if sum(as_int(row.get("member_rows")) for row in slices) != len(members):
        issues.append("slice member counts do not sum to member ledger rows")
    if sum(as_int(row.get("package_evidence_rows")) for row in slices) > len(evidence):
        issues.append("slice evidence counts exceed evidence ledger rows")
    if sum(as_int(row.get("package_member_rows")) for row in aggregates) != len(members):
        issues.append("aggregate member counts do not sum to member ledger rows")

    implement_input_ids = [
        row.get("final_review_row_id")
        for row in input_rows
        if row.get("keep_kill_redesign_implement_decision") == "IMPLEMENT_EXPANDED_MARKET_FINAL_REVIEW_BRANCH_LOCAL"
    ]
    member_input_ids = [row.get("input_final_review_row_id") for row in members]
    if Counter(implement_input_ids) != Counter(member_input_ids):
        issues.append("final-review implement ids are not covered exactly once")
    redesign_input_ids = [
        row.get("final_review_row_id")
        for row in input_rows
        if row.get("keep_kill_redesign_implement_decision") != "IMPLEMENT_EXPANDED_MARKET_FINAL_REVIEW_BRANCH_LOCAL"
    ]
    redesign_output_ids = [row.get("input_final_review_row_id") for row in redesign]
    if Counter(redesign_input_ids) != Counter(redesign_output_ids):
        issues.append("final-review redesign ids are not covered exactly once")
    input_evidence_ids = [row.get("final_review_evidence_row_id") for row in input_evidence]
    output_evidence_ids = [row.get("input_final_review_evidence_row_id") for row in evidence]
    if Counter(input_evidence_ids) != Counter(output_evidence_ids):
        issues.append("final-review evidence ids are not covered exactly once")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "package_slice_rows": len(slices),
        "package_member_rows": len(members),
        "package_evidence_rows": len(evidence),
        "redesign_carry_rows": len(redesign),
        "aggregate_rows": len(aggregates),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
