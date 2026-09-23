#!/usr/bin/env python3
"""Verify deconcentrated scorer-surface execution checkpoint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_DECON_SCORER_EXEC"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_DECONCENTRATED_SCORER_SURFACES"
SELECTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_DECONCENTRATED_IMPLEMENTATION_SELECTION"

INPUT_SURFACE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SURFACE_LEDGER_2026-05-17.jsonl"
INPUT_MEMBER_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MEMBER_LEDGER_2026-05-17.jsonl"
INPUT_EVIDENCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NONIMPLEMENT_EVIDENCE_LEDGER_2026-05-17.jsonl"
INPUT_SELECTION_LEDGER = ROUTE_DIR / f"{SELECTION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SURFACE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SURFACE_EXECUTION_LEDGER_2026-05-17.jsonl"
MEMBER_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_MEMBER_EXECUTION_LEDGER_2026-05-17.jsonl"
EVIDENCE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_NONIMPLEMENT_EVIDENCE_EXECUTION_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_deconcentrated_scorer_surface_execution.py",
    ROUTE_DIR / "build_expanded_market_deconcentrated_scorer_surface_execution_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    SURFACE_EXECUTION_LEDGER,
    MEMBER_EXECUTION_LEDGER,
    EVIDENCE_EXECUTION_LEDGER,
    AGGREGATE_LEDGER,
    ISSUE_LEDGER,
    SYSTEM_LEDGER,
    SUMMARY_PATH,
]
REQUIRED_R_FIELDS = (
    "gross_simulated_r",
    "cost_adjusted_simulated_r",
    "stress_simulated_r",
    "deconcentrated_cost_adjusted_simulated_r",
    "deconcentrated_stress_simulated_r",
)


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


def selection_id(row: dict[str, Any]) -> str:
    return str(row.get("expanded_market_deconcentrated_selection_row_id") or row.get("input_selection_row_id") or "")


def missing_r_fields(row: dict[str, Any]) -> list[str]:
    return [field for field in REQUIRED_R_FIELDS if row.get(field) in (None, "")]


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    input_surfaces = read_jsonl(INPUT_SURFACE_LEDGER)
    input_members = read_jsonl(INPUT_MEMBER_LEDGER)
    input_evidence = read_jsonl(INPUT_EVIDENCE_LEDGER)
    input_selection = read_jsonl(INPUT_SELECTION_LEDGER)
    surface_exec = read_jsonl(SURFACE_EXECUTION_LEDGER)
    member_exec = read_jsonl(MEMBER_EXECUTION_LEDGER)
    evidence_exec = read_jsonl(EVIDENCE_EXECUTION_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    issue_rows = read_jsonl(ISSUE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    expected_counts = {
        "input_scorer_surface_rows": len(input_surfaces),
        "input_scorer_member_rows": len(input_members),
        "input_nonimplement_evidence_rows": len(input_evidence),
        "input_selection_rows": len(input_selection),
        "surface_execution_rows": len(surface_exec),
        "member_execution_rows": len(member_exec),
        "nonimplement_evidence_execution_rows": len(evidence_exec),
        "aggregate_rows": len(aggregates),
        "issue_rows": len(issue_rows),
        "system_rows": len(system_rows),
    }
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            issues.append(f"{key} mismatch: result has {counts.get(key)!r}, observed {expected!r}")
    if len(input_selection) != 46120:
        issues.append(f"input selection count changed from 46120 to {len(input_selection)}")
    if len(input_surfaces) != 488:
        issues.append(f"input surface count changed from 488 to {len(input_surfaces)}")
    if len(input_members) != 5389:
        issues.append(f"input member count changed from 5389 to {len(input_members)}")
    if len(input_evidence) != 40731:
        issues.append(f"input evidence count changed from 40731 to {len(input_evidence)}")
    if len(surface_exec) != len(input_surfaces):
        issues.append("surface execution rows do not cover every scorer surface")
    if len(member_exec) != len(input_members):
        issues.append("member execution rows do not cover every scorer member")
    if len(evidence_exec) != len(input_evidence):
        issues.append("evidence execution rows do not cover every non-implement evidence row")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if issue_rows:
        issues.append("issue ledger must be empty for the current execution")
    if len(aggregates) != 3:
        issues.append("aggregate ledger must contain three family rows")
    if counts.get("surface_execution_pass_rows") != len(surface_exec):
        issues.append("every scorer surface must execute as pass")
    if counts.get("surface_execution_redesign_rows") != 0:
        issues.append("surface redesign count must be zero")
    if any(row.get("execution_status") != "DECONCENTRATED_SCORER_SURFACE_EXECUTION_PASS" for row in surface_exec):
        issues.append("one or more surface executions did not pass")
    if any(row.get("matched_unexpected_rows") != 0 for row in surface_exec):
        issues.append("one or more surface executions matched unexpected rows")
    if any(row.get("missing_expected_member_rows") != 0 for row in surface_exec):
        issues.append("one or more surface executions missed expected member rows")
    if any(row.get("matched_nonimplement_rows") != 0 for row in surface_exec):
        issues.append("one or more surface executions matched non-implement rows")
    if any(row.get("member_execution_status") != "EXPECTED_IMPLEMENT_MEMBER_MATCH" for row in member_exec):
        issues.append("one or more member executions are not expected implement matches")
    if any(row.get("evidence_execution_status") != "NONIMPLEMENT_NUMERIC_EVIDENCE_PRESERVED" for row in evidence_exec):
        issues.append("one or more evidence rows were not preserved")
    member_input_ids = {selection_id(row) for row in input_members}
    member_exec_ids = {row.get("input_selection_row_id") for row in member_exec}
    if member_input_ids != member_exec_ids:
        issues.append("member execution ids do not exactly match scorer member ids")
    evidence_input_ids = {selection_id(row) for row in input_evidence}
    evidence_exec_ids = {row.get("input_selection_row_id") for row in evidence_exec}
    if evidence_input_ids != evidence_exec_ids:
        issues.append("evidence execution ids do not exactly match evidence ids")
    if any(not row.get("source_path") or not row.get("source_file_sha256") for row in surface_exec + member_exec + evidence_exec):
        issues.append("one or more execution rows lacks source path/hash")
    if any(missing_r_fields(row) for row in member_exec + evidence_exec):
        issues.append("one or more member/evidence execution rows lacks simulated R fields")
    if any(row.get("missing_simulated_fields") not in ([], None) for row in member_exec + evidence_exec):
        issues.append("one or more execution rows carries missing simulated fields")
    if any(not boundary_ok(row) for row in surface_exec + member_exec + evidence_exec + aggregates + issue_rows + system_rows + [result]):
        issues.append("one or more rows failed branch-local boundary checks")
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    print(
        json.dumps(
            {
                "ok": not issues,
                "issues": issues,
                "counts": {
                    "surface_execution_rows": len(surface_exec),
                    "surface_execution_pass_rows": counts.get("surface_execution_pass_rows"),
                    "member_execution_rows": len(member_exec),
                    "nonimplement_evidence_execution_rows": len(evidence_exec),
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
