#!/usr/bin/env python3
"""Verify matrix-surface execution against held performance matrix rows."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_MATRIX_SURFACE_EXECUTION"
SURFACE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_MATRIX_SURFACES"
MATRIX_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_PERFORMANCE_MATRIX"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SURFACE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SURFACE_EXECUTION_LEDGER_2026-05-17.jsonl"
TERMINAL_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_TERMINAL_EXECUTION_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
MATRIX_LEDGER = ROUTE_DIR / f"{MATRIX_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
SCORER_SURFACE_LEDGER = ROUTE_DIR / f"{SURFACE_PREFIX}_SCORER_SURFACE_LEDGER_2026-05-17.jsonl"
AVOID_SURFACE_LEDGER = ROUTE_DIR / f"{SURFACE_PREFIX}_AVOID_SURFACE_LEDGER_2026-05-17.jsonl"
TERMINAL_LEDGER = ROUTE_DIR / f"{SURFACE_PREFIX}_TERMINAL_DECISION_LEDGER_2026-05-17.jsonl"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_matrix_surface_execution.py",
    ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_geometry_table_matrix_surface_execution_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    SURFACE_EXECUTION_LEDGER,
    TERMINAL_EXECUTION_LEDGER,
    ISSUE_LEDGER,
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


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    surface_exec_rows = read_jsonl(SURFACE_EXECUTION_LEDGER)
    terminal_exec_rows = read_jsonl(TERMINAL_EXECUTION_LEDGER)
    issue_rows = read_jsonl(ISSUE_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    matrix_rows = read_jsonl(MATRIX_LEDGER)
    surface_rows = read_jsonl(SCORER_SURFACE_LEDGER) + read_jsonl(AVOID_SURFACE_LEDGER)
    terminal_rows = read_jsonl(TERMINAL_LEDGER)
    counts = result.get("counts") or {}
    all_exec = surface_exec_rows + terminal_exec_rows

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if counts.get("input_surface_result_ok") != 1:
        issues.append("input surface result was not marked ok")
    if counts.get("input_matrix_rows") != len(matrix_rows):
        issues.append("input matrix count mismatch")
    if counts.get("input_surface_rows") != len(surface_rows):
        issues.append("input surface count mismatch")
    if counts.get("input_terminal_rows") != len(terminal_rows):
        issues.append("input terminal count mismatch")
    if len(surface_exec_rows) != len(surface_rows):
        issues.append("surface execution rows do not preserve surfaces")
    if len(terminal_exec_rows) != len(terminal_rows):
        issues.append("terminal execution rows do not preserve terminal decisions")
    if len(all_exec) != len(matrix_rows):
        issues.append("executions do not preserve every matrix row")
    if counts.get("surface_execution_rows") != len(surface_exec_rows):
        issues.append("surface execution count mismatch")
    if counts.get("terminal_execution_rows") != len(terminal_exec_rows):
        issues.append("terminal execution count mismatch")
    if counts.get("total_execution_rows") != len(all_exec):
        issues.append("total execution count mismatch")
    if counts.get("aggregate_execution_rows") != len(aggregate_rows):
        issues.append("aggregate execution count mismatch")
    if counts.get("execution_issue_rows") != len(issue_rows):
        issues.append("execution issue count mismatch")
    if issue_rows:
        issues.append("execution issue ledger should be empty")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len({row.get("matrix_surface_execution_row_id") for row in surface_exec_rows}) != len(surface_exec_rows):
        issues.append("surface execution row ids are not unique")
    if len({row.get("terminal_matrix_execution_row_id") for row in terminal_exec_rows}) != len(terminal_exec_rows):
        issues.append("terminal execution row ids are not unique")
    if any(row.get("surface_execution_status") != "PERFORMANCE_MATRIX_SURFACE_EXECUTION_PASS" for row in surface_exec_rows):
        issues.append("one or more surface executions did not pass")
    if any(row.get("terminal_execution_status") != "TERMINAL_MATRIX_DECISION_EXECUTION_PRESERVED" for row in terminal_exec_rows):
        issues.append("one or more terminal executions were not preserved")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(all_exec):
        issues.append("aggregate row counts do not sum to all executions")
    if any(not boundary_ok(row) for row in all_exec + issue_rows + aggregate_rows + system_rows):
        issues.append("one or more ledger rows failed research boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")

    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in all_exec)
    expected = {
        "IMPLEMENT_BRANCH_LOCAL_SCORER_FROM_REPLAY_GEOMETRY_TABLE": 532,
        "CARRY_AS_AVOID_INTELLIGENCE_FROM_REPLAY_GEOMETRY_TABLE": 106,
        "KILL_AVOID_COMPARATOR_FROM_REPLAY_GEOMETRY": 262,
        "KILL_DEFAULT_OFF_FROM_REPLAY_GEOMETRY": 157,
    }
    for decision, expected_count in expected.items():
        if decisions.get(decision) != expected_count:
            issues.append(f"decision {decision} count mismatch")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "decision_counts": dict(sorted(decisions.items())),
        "surface_execution_rows": len(surface_exec_rows),
        "terminal_execution_rows": len(terminal_exec_rows),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
