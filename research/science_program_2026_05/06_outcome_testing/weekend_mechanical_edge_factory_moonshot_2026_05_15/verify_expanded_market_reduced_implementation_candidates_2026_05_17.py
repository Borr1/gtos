#!/usr/bin/env python3
"""Verify expanded-market reduced implementation-candidate checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
EXECUTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_SURFACE_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_IMPLEMENTATION_CANDIDATES"

EXECUTION_RESULT = ROUTE_DIR / f"{EXECUTION_PREFIX}_RESULT_2026-05-17.json"
SURFACE_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_SURFACE_LEDGER_2026-05-17.jsonl"
EXECUTION_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
MATCH_LEDGER = ROUTE_DIR / f"{EXECUTION_PREFIX}_MATCH_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_reduced_implementation_candidates.py",
    ROUTE_DIR / "build_expanded_market_reduced_implementation_candidates_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, CANDIDATE_LEDGER, EVIDENCE_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]


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
    surfaces = read_jsonl(SURFACE_LEDGER)
    executions = read_jsonl(EXECUTION_LEDGER)
    matches = read_jsonl(MATCH_LEDGER)
    result = read_json(RESULT_PATH)
    candidates = read_jsonl(CANDIDATE_LEDGER)
    evidence = read_jsonl(EVIDENCE_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if execution_result.get("ok") is not True:
        issues.append("input CP224 result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(surfaces) != 1748:
        issues.append(f"input surface count changed from 1748 to {len(surfaces)}")
    if len(executions) != 1748:
        issues.append(f"input execution count changed from 1748 to {len(executions)}")
    if len(matches) != 9266:
        issues.append(f"input match count changed from 9266 to {len(matches)}")
    if counts.get("implementation_candidate_rows") != len(candidates):
        issues.append("candidate row count mismatch")
    if counts.get("implementation_candidate_evidence_rows") != len(evidence):
        issues.append("evidence row count mismatch")
    if counts.get("aggregate_rows") != len(aggregates):
        issues.append("aggregate row count mismatch")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len(candidates) != len(executions):
        issues.append("candidate rows must match execution rows")
    if len(evidence) != len(matches):
        issues.append("evidence rows must match execution match rows")
    if sum(as_int(row.get("matched_selection_rows")) for row in candidates) != len(evidence):
        issues.append("candidate matched row counts do not sum to evidence rows")
    if sum(as_int(row.get("row_count")) for row in aggregates) != len(candidates):
        issues.append("aggregate row counts do not sum to candidate rows")
    if any(not boundary_ok(row) for row in candidates + evidence + aggregates + system_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if len({row.get("implementation_candidate_row_id") for row in candidates}) != len(candidates):
        issues.append("candidate row ids are not unique")
    if len({row.get("implementation_candidate_evidence_row_id") for row in evidence}) != len(evidence):
        issues.append("evidence row ids are not unique")

    input_execution_ids = [row.get("reduced_surface_execution_row_id") for row in executions]
    output_execution_ids = [row.get("input_reduced_surface_execution_row_id") for row in candidates]
    if Counter(input_execution_ids) != Counter(output_execution_ids):
        issues.append("input execution ids are not covered exactly once")
    input_match_ids = [row.get("reduced_surface_execution_match_row_id") for row in matches]
    output_match_ids = [row.get("input_reduced_surface_execution_match_row_id") for row in evidence]
    if Counter(input_match_ids) != Counter(output_match_ids):
        issues.append("input match ids are not covered exactly once")

    if any(row.get("implementation_candidate_status") != "IMPLEMENTATION_CANDIDATE_READY" for row in candidates):
        issues.append("one or more candidates are not ready")
    if any(as_int(row.get("matched_nonimplement_rows")) != 0 for row in candidates):
        issues.append("one or more candidates retained non-implement matches")
    if any(not row.get("source_path") or not row.get("source_file_sha256") for row in candidates):
        issues.append("one or more candidates lack source path/hash")
    if any(not row.get("branch_local_code_expression") for row in candidates):
        issues.append("one or more candidates lack branch-local expression")
    required_geometry_fields = [
        "average_selected_intrabar_cost_adjusted_simulated_r",
        "average_selected_minus_rejected_intrabar_cost_adjusted_r",
        "selected_intrabar_target_first_count_total",
        "selected_intrabar_stop_first_count_total",
        "selected_intrabar_path_count_total",
        "target_first_share",
        "stop_first_share",
        "matched_effective_n_sum",
    ]
    for row in candidates:
        missing = [field for field in required_geometry_fields if row.get(field) is None]
        if missing:
            issues.append(f"candidate {row.get('implementation_candidate_row_id')} missing geometry fields: {missing}")
            break
    if any(row.get("matched_decision_family") != "implement" for row in evidence):
        issues.append("one or more evidence rows are not implement-family")

    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in candidates)
    if not any(str(decision).startswith("IMPLEMENT") for decision in decisions):
        issues.append("implement candidate decision class is absent")
    if counts.get("ready_candidate_rows") != len(candidates):
        issues.append("ready candidate count does not match candidate rows")
    if counts.get("redesign_candidate_rows") != 0:
        issues.append("redesign candidate count is not zero")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "decision_counts": dict(sorted(decisions.items())),
        "candidate_rows": len(candidates),
        "evidence_rows": len(evidence),
        "aggregate_rows": len(aggregates),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
