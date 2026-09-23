#!/usr/bin/env python3
"""Verify deconcentrated scorer-surface checkpoint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_DECONCENTRATED_SCORER_SURFACES"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_DECONCENTRATED_IMPLEMENTATION_SELECTION"
IMPLEMENT_DECISION = "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATED_SCORER_CANDIDATE"

INPUT_SELECTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_SURFACE_LEDGER_2026-05-17.jsonl"
MEMBER_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_NONIMPLEMENT_EVIDENCE_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_deconcentrated_scorer_surfaces.py",
    ROUTE_DIR / "build_expanded_market_deconcentrated_scorer_surfaces_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    SURFACE_LEDGER,
    MEMBER_LEDGER,
    EVIDENCE_LEDGER,
    SELF_TEST_LEDGER,
    AGGREGATE_LEDGER,
    ISSUE_LEDGER,
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
    result = read_json(RESULT_PATH)
    input_rows = read_jsonl(INPUT_SELECTION_LEDGER)
    surfaces = read_jsonl(SURFACE_LEDGER)
    members = read_jsonl(MEMBER_LEDGER)
    evidence = read_jsonl(EVIDENCE_LEDGER)
    self_tests = read_jsonl(SELF_TEST_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    issue_rows = read_jsonl(ISSUE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    implement_inputs = [row for row in input_rows if row.get("keep_kill_redesign_implement_decision") == IMPLEMENT_DECISION]
    nonimplement_inputs = [row for row in input_rows if row.get("keep_kill_redesign_implement_decision") != IMPLEMENT_DECISION]
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(input_rows) != 46120:
        issues.append(f"input selection count changed from 46120 to {len(input_rows)}")
    if counts.get("input_selection_rows") != len(input_rows):
        issues.append("input selection count mismatch")
    if counts.get("scorer_member_rows") != len(members) or len(members) != len(implement_inputs):
        issues.append("member rows do not cover every implement input")
    if counts.get("nonimplement_evidence_rows") != len(evidence) or len(evidence) != len(nonimplement_inputs):
        issues.append("evidence rows do not cover every non-implement input")
    if counts.get("scorer_surface_rows") != len(surfaces):
        issues.append("surface row count mismatch")
    if counts.get("self_test_rows") != len(self_tests) or len(self_tests) != len(surfaces):
        issues.append("self-test rows must match surface rows")
    if counts.get("self_test_pass_rows") != len(self_tests):
        issues.append("every surface self-test must pass")
    if counts.get("aggregate_rows") != len(aggregates):
        issues.append("aggregate row count mismatch")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    if len(system_rows) != 1 or counts.get("system_rows") != 1:
        issues.append("system ledger must contain one row")
    if any(not boundary_ok(row) for row in surfaces + members + evidence + self_tests + aggregates + issue_rows + system_rows + [result]):
        issues.append("one or more rows failed branch-local boundary checks")
    input_implement_ids = {row.get("expanded_market_deconcentrated_selection_row_id") for row in implement_inputs}
    member_input_ids = {row.get("input_selection_row_id") for row in members}
    if input_implement_ids != member_input_ids:
        issues.append("implement input ids are not exactly preserved in member rows")
    input_nonimplement_ids = {row.get("expanded_market_deconcentrated_selection_row_id") for row in nonimplement_inputs}
    evidence_input_ids = {row.get("input_selection_row_id") for row in evidence}
    if input_nonimplement_ids != evidence_input_ids:
        issues.append("non-implement input ids are not exactly preserved in evidence rows")
    surface_ids = {row.get("expanded_market_deconcentrated_scorer_surface_row_id") for row in surfaces}
    if len(surface_ids) != len(surfaces):
        issues.append("surface row ids are not unique")
    if {row.get("input_scorer_surface_row_id") for row in members} - surface_ids:
        issues.append("member row references unknown surface")
    if any(not row.get("source_path") or not row.get("source_file_sha256") for row in members + evidence + surfaces):
        issues.append("one or more scorer/evidence rows lacks source path/hash")
    if any(row.get("self_test_status") != "DECONCENTRATED_SCORER_SURFACE_SELF_TEST_PASS" for row in self_tests):
        issues.append("one or more self-tests did not pass")
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    print(
        json.dumps(
            {
                "ok": not issues,
                "issues": issues,
                "counts": {
                    "input_selection_rows": len(input_rows),
                    "scorer_surface_rows": len(surfaces),
                    "scorer_member_rows": len(members),
                    "nonimplement_evidence_rows": len(evidence),
                    "self_test_rows": len(self_tests),
                    "issue_rows": len(issue_rows),
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
