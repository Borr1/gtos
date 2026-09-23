#!/usr/bin/env python3
"""Verify branch-local code surface execution rows."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_SURFACE_EXECUTION"
SURF_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_SURFACES"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
SCORER_SURFACE_LEDGER = ROUTE_DIR / f"{SURF_PREFIX}_SCORER_SURFACE_LEDGER_2026-05-17.jsonl"
AVOID_SURFACE_LEDGER = ROUTE_DIR / f"{SURF_PREFIX}_AVOID_SURFACE_LEDGER_2026-05-17.jsonl"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_code_surface_execution.py",
    ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_geometry_table_code_surface_execution_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, EXECUTION_LEDGER, ISSUE_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]


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
    rows = read_jsonl(EXECUTION_LEDGER)
    issue_rows = read_jsonl(ISSUE_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    surface_rows = read_jsonl(SCORER_SURFACE_LEDGER) + read_jsonl(AVOID_SURFACE_LEDGER)
    counts = result.get("counts") or {}

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if counts.get("input_surface_result_ok") != 1:
        issues.append("input surface result was not marked ok")
    if len(rows) != len(surface_rows):
        issues.append("surface execution rows do not preserve surfaces")
    if counts.get("code_surface_execution_rows") != len(rows):
        issues.append("execution count mismatch")
    if counts.get("code_surface_execution_issue_rows") != len(issue_rows):
        issues.append("issue count mismatch")
    if counts.get("aggregate_code_surface_execution_rows") != len(aggregate_rows):
        issues.append("aggregate count mismatch")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len({row.get("geometry_table_code_surface_execution_row_id") for row in rows}) != len(rows):
        issues.append("execution row ids are not unique")
    if any(row.get("surface_execution_status") != "CODE_SURFACE_EXECUTION_PASS" for row in rows):
        issues.append("one or more surface executions did not pass")
    if issue_rows:
        issues.append("issue ledger should be empty")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(rows):
        issues.append("aggregate row counts do not sum to execution rows")
    if any(not boundary_ok(row) for row in rows + issue_rows + aggregate_rows + system_rows):
        issues.append("one or more ledger rows failed research boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    statuses = Counter(row.get("surface_execution_status") for row in rows)
    verdict = {"ok": not issues, "issues": issues, "counts": counts, "surface_execution_status_counts": dict(sorted(statuses.items()))}
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
