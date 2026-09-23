#!/usr/bin/env python3
"""Verify expanded-market package-review execution checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PACKAGE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PACKAGE_SLICES"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PACKAGE_REVIEW_EXECUTION"

PACKAGE_RESULT = ROUTE_DIR / f"{PACKAGE_PREFIX}_RESULT_2026-05-17.json"
PACKAGE_SLICE_LEDGER = ROUTE_DIR / f"{PACKAGE_PREFIX}_SLICE_LEDGER_2026-05-17.jsonl"
PACKAGE_MEMBER_LEDGER = ROUTE_DIR / f"{PACKAGE_PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
PACKAGE_EVIDENCE_LEDGER = ROUTE_DIR / f"{PACKAGE_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
PACKAGE_REDESIGN_LEDGER = ROUTE_DIR / f"{PACKAGE_PREFIX}_REDESIGN_CARRY_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ARTIFACT_LEDGER = ROUTE_DIR / f"{PREFIX}_ARTIFACT_LEDGER_2026-05-17.jsonl"
MEMBER_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_EXECUTION_LEDGER_2026-05-17.jsonl"
EVIDENCE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_EXECUTION_LEDGER_2026-05-17.jsonl"
REDESIGN_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REDESIGN_EXECUTION_LEDGER_2026-05-17.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_package_review_execution.py",
    ROUTE_DIR / "build_expanded_market_package_review_execution_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, ARTIFACT_LEDGER, MEMBER_EXECUTION_LEDGER, EVIDENCE_EXECUTION_LEDGER, REDESIGN_EXECUTION_LEDGER, CONTROL_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]


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
    package_result = read_json(PACKAGE_RESULT)
    input_slices = read_jsonl(PACKAGE_SLICE_LEDGER)
    input_members = read_jsonl(PACKAGE_MEMBER_LEDGER)
    input_evidence = read_jsonl(PACKAGE_EVIDENCE_LEDGER)
    input_redesign = read_jsonl(PACKAGE_REDESIGN_LEDGER)
    result = read_json(RESULT_PATH)
    artifacts = read_jsonl(ARTIFACT_LEDGER)
    members = read_jsonl(MEMBER_EXECUTION_LEDGER)
    evidence = read_jsonl(EVIDENCE_EXECUTION_LEDGER)
    redesign = read_jsonl(REDESIGN_EXECUTION_LEDGER)
    controls = read_jsonl(CONTROL_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if package_result.get("ok") is not True:
        issues.append("input CP230 result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(input_slices) != 221:
        issues.append(f"input package slice count changed from 221 to {len(input_slices)}")
    if len(input_members) != 1597:
        issues.append(f"input package member count changed from 1597 to {len(input_members)}")
    if len(input_evidence) != 9266:
        issues.append(f"input package evidence count changed from 9266 to {len(input_evidence)}")
    if len(input_redesign) != 151:
        issues.append(f"input package redesign count changed from 151 to {len(input_redesign)}")
    if counts.get("package_review_artifact_rows") != len(artifacts):
        issues.append("artifact row count mismatch")
    if counts.get("package_review_member_execution_rows") != len(members):
        issues.append("member execution row count mismatch")
    if counts.get("package_review_evidence_execution_rows") != len(evidence):
        issues.append("evidence execution row count mismatch")
    if counts.get("package_review_redesign_execution_rows") != len(redesign):
        issues.append("redesign execution row count mismatch")
    if counts.get("package_review_control_rows") != len(controls):
        issues.append("control row count mismatch")
    if counts.get("aggregate_rows") != len(aggregates):
        issues.append("aggregate row count mismatch")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len(artifacts) != len(input_slices):
        issues.append("artifacts must preserve every package slice")
    if len(members) != len(input_members):
        issues.append("member executions must preserve every package member")
    if len(evidence) != len(input_evidence):
        issues.append("evidence executions must preserve every package evidence row")
    if len(redesign) != len(input_redesign):
        issues.append("redesign executions must preserve every redesign row")
    if len(controls) != len(input_slices):
        issues.append("controls must preserve every package slice")
    if any(not boundary_ok(row) for row in artifacts + members + evidence + redesign + controls + aggregates + system_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if any(row.get("package_review_execution_status") != "PACKAGE_REVIEW_EXECUTION_PASS" for row in artifacts):
        issues.append("one or more package review artifacts failed execution")
    if counts.get("artifact_pass_rows") != 221:
        issues.append("artifact pass rows must equal 221")
    if counts.get("member_pass_rows") != 1597:
        issues.append("member pass rows must equal 1597")
    expected_implement_evidence = sum(1 for row in input_evidence if row.get("input_package_slice_row_id"))
    if counts.get("evidence_pass_rows") != expected_implement_evidence:
        issues.append("evidence pass rows must equal implement package evidence rows")
    if sum(as_int(row.get("member_rows_executed")) for row in artifacts) != len(members):
        issues.append("artifact member counts do not sum to member executions")
    if sum(as_int(row.get("evidence_rows_executed")) for row in artifacts) != counts.get("evidence_pass_rows"):
        issues.append("artifact evidence counts do not sum to passing evidence rows")
    if sum(as_int(row.get("member_rows")) for row in aggregates) != len(members):
        issues.append("aggregate member counts do not sum to member executions")

    if Counter(row.get("package_slice_row_id") for row in input_slices) != Counter(
        row.get("input_package_slice_row_id") for row in artifacts
    ):
        issues.append("package slice ids are not covered exactly once")
    if Counter(row.get("package_member_row_id") for row in input_members) != Counter(
        row.get("input_package_member_row_id") for row in members
    ):
        issues.append("package member ids are not covered exactly once")
    if Counter(row.get("package_evidence_row_id") for row in input_evidence) != Counter(
        row.get("input_package_evidence_row_id") for row in evidence
    ):
        issues.append("package evidence ids are not covered exactly once")
    if Counter(row.get("package_redesign_carry_row_id") for row in input_redesign) != Counter(
        row.get("input_package_redesign_carry_row_id") for row in redesign
    ):
        issues.append("redesign carry ids are not covered exactly once")
    if any(not row.get("package_artifact_expression_sha256") for row in artifacts):
        issues.append("one or more artifacts lack expression hash")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "artifact_rows": len(artifacts),
        "member_execution_rows": len(members),
        "evidence_execution_rows": len(evidence),
        "redesign_execution_rows": len(redesign),
        "aggregate_rows": len(aggregates),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
