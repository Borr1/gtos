#!/usr/bin/env python3
"""Verify expanded-market code-candidates checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_IMPLEMENTATION_SELECTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_CODE_CANDIDATES"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_SELECTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
CODE_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_code_candidates.py",
    ROUTE_DIR / "build_expanded_market_code_candidates_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, CODE_CANDIDATE_LEDGER, EVIDENCE_LEDGER, SELF_TEST_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
REQUIRED_CANDIDATE_FIELDS = (
    "code_candidate_row_id",
    "input_implementation_selection_row_id",
    "symbol",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "source_component",
    "selected_side",
    "candidate_scope",
    "candidate_scope_sha256",
    "candidate_function_name",
    "branch_local_code_expression",
    "branch_local_action",
    "selected_intrabar_cost_adjusted_simulated_r",
    "rejected_intrabar_cost_adjusted_simulated_r",
    "selected_minus_rejected_intrabar_cost_adjusted_r",
    "keep_kill_redesign_implement_decision",
)
REQUIRED_EVIDENCE_FIELDS = (
    "code_evidence_row_id",
    "input_implementation_selection_row_id",
    "selection_decision",
    "evidence_family",
    "branch_local_evidence_action",
    "keep_kill_redesign_implement_decision",
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


def decision_family(decision: str | None) -> str:
    text = "" if decision is None else str(decision)
    if text.startswith("IMPLEMENT"):
        return "implement"
    if "AVOID" in text:
        return "avoid"
    if text.startswith("KILL"):
        return "kill"
    if text.startswith("REDESIGN"):
        return "redesign"
    return "missing"


def main() -> None:
    issues: list[str] = []
    input_result = read_json(INPUT_RESULT)
    selection_rows = read_jsonl(INPUT_SELECTION_LEDGER)
    result = read_json(RESULT_PATH)
    candidate_rows = read_jsonl(CODE_CANDIDATE_LEDGER)
    evidence_rows = read_jsonl(EVIDENCE_LEDGER)
    self_test_rows = read_jsonl(SELF_TEST_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if input_result.get("ok") is not True:
        issues.append("input CP220 result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(selection_rows) != 22610:
        issues.append(f"input selection row count changed from 22610 to {len(selection_rows)}")
    if counts.get("input_selection_rows") != len(selection_rows):
        issues.append("input selection count mismatch")
    if counts.get("code_candidate_rows") != len(candidate_rows):
        issues.append("code candidate row count mismatch")
    if counts.get("code_evidence_rows") != len(evidence_rows):
        issues.append("evidence row count mismatch")
    if counts.get("self_test_rows") != len(self_test_rows):
        issues.append("self-test row count mismatch")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len(candidate_rows) + len(evidence_rows) != len(selection_rows):
        issues.append("candidate plus evidence rows do not preserve every selection row")
    if len(self_test_rows) != len(candidate_rows):
        issues.append("self-test rows must match candidate rows")
    if counts.get("self_test_pass_rows") != len(candidate_rows):
        issues.append("every code candidate must have a passing self-test")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(candidate_rows) + len(evidence_rows):
        issues.append("aggregate row counts do not sum to candidate plus evidence rows")
    if any(not boundary_ok(row) for row in candidate_rows + evidence_rows + self_test_rows + aggregate_rows + system_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if any(field not in row for row in candidate_rows for field in REQUIRED_CANDIDATE_FIELDS):
        issues.append("one or more code candidate rows lacks a required field")
    if any(field not in row for row in evidence_rows for field in REQUIRED_EVIDENCE_FIELDS):
        issues.append("one or more evidence rows lacks a required field")
    if len({row.get("code_candidate_row_id") for row in candidate_rows}) != len(candidate_rows):
        issues.append("code candidate row ids are not unique")
    if len({row.get("code_evidence_row_id") for row in evidence_rows}) != len(evidence_rows):
        issues.append("evidence row ids are not unique")
    selection_ids = {row.get("implementation_selection_row_id") for row in selection_rows}
    output_ids = {row.get("input_implementation_selection_row_id") for row in candidate_rows + evidence_rows}
    if selection_ids != output_ids:
        issues.append("candidate and evidence rows do not exactly cover selection row ids")
    implement_input_count = sum(
        1 for row in selection_rows if decision_family(row.get("keep_kill_redesign_implement_decision")) == "implement"
    )
    if len(candidate_rows) != implement_input_count:
        issues.append("code candidate count does not match implement selection rows")
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in candidate_rows + evidence_rows)
    if not any(str(decision).startswith("IMPLEMENT") for decision in decisions):
        issues.append("implementation decision class is absent")
    if not any("AVOID" in str(decision) for decision in decisions):
        issues.append("avoid-intelligence decision class is absent")
    if not any(str(decision).startswith("KILL") for decision in decisions):
        issues.append("kill decision class is absent")
    if not any(str(decision).startswith("REDESIGN") for decision in decisions):
        issues.append("redesign decision class is absent")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "decision_counts": dict(sorted(decisions.items())),
        "code_candidate_rows": len(candidate_rows),
        "code_evidence_rows": len(evidence_rows),
        "self_test_rows": len(self_test_rows),
        "aggregate_rows": len(aggregate_rows),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
