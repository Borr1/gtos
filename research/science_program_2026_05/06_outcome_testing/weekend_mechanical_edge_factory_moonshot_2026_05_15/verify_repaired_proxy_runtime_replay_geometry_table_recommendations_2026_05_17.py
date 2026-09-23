#!/usr/bin/env python3
"""Verify branch-local recommendation rows from code-surface execution."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_RECOMMENDATIONS"
EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_SURFACE_EXECUTION"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RECOMMENDATION_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
EXECUTION_LEDGER = ROUTE_DIR / f"{EXEC_PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_recommendations.py",
    ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_geometry_table_recommendations_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, RECOMMENDATION_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]


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
    rows = read_jsonl(RECOMMENDATION_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    execution_rows = read_jsonl(EXECUTION_LEDGER)
    counts = result.get("counts") or {}

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if counts.get("input_execution_result_ok") != 1:
        issues.append("input execution result was not marked ok")
    if len(rows) != len(execution_rows):
        issues.append("recommendation rows do not preserve execution rows")
    if counts.get("recommendation_rows") != len(rows):
        issues.append("recommendation count mismatch")
    if counts.get("aggregate_recommendation_rows") != len(aggregate_rows):
        issues.append("aggregate recommendation count mismatch")
    if counts.get("repair_recommendation_rows") != 0:
        issues.append("repair recommendation rows should be zero")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len({row.get("geometry_table_recommendation_row_id") for row in rows}) != len(rows):
        issues.append("recommendation row ids are not unique")
    if any(row.get("surface_score") is None for row in rows):
        issues.append("one or more recommendation rows lack surface score")
    if any(not boundary_ok(row) for row in rows + aggregate_rows + system_rows):
        issues.append("one or more ledger rows failed research boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(rows):
        issues.append("aggregate row counts do not sum to recommendation rows")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    kinds = Counter(row.get("recommendation_kind") for row in rows)
    aggregate_actions = Counter(row.get("aggregate_recommendation_action") for row in aggregate_rows)
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "recommendation_kind_counts": dict(sorted(kinds.items())),
        "aggregate_recommendation_action_counts": dict(sorted(aggregate_actions.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
