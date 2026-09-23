#!/usr/bin/env python3
"""Verify all-row replay performance matrix after geometry table recommendations."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_PERFORMANCE_MATRIX"
PERF_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_PERFORMANCE"
REC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_RECOMMENDATIONS"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
MATRIX_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
MISSING_FIELD_LEDGER = ROUTE_DIR / f"{PREFIX}_SIMULATED_MISSING_FIELD_LEDGER_2026-05-17.jsonl"
JOIN_ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_JOIN_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
PERFORMANCE_LEDGER = ROUTE_DIR / f"{PERF_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
RECOMMENDATION_LEDGER = ROUTE_DIR / f"{REC_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_performance_matrix.py",
    ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_geometry_table_performance_matrix_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    MATRIX_LEDGER,
    AGGREGATE_LEDGER,
    MISSING_FIELD_LEDGER,
    JOIN_ISSUE_LEDGER,
    SYSTEM_LEDGER,
    SUMMARY_PATH,
]

REQUIRED_ROW_FIELDS = (
    "branch",
    "family",
    "symbol",
    "route_session",
    "market_timeframe",
    "horizon_id",
    "side",
    "follow_inverse_default_off_avoid_class",
    "default_off_avoid_class",
    "entry_reference",
    "stop_target_or_proxy_denominator_field",
    "stop_target_or_proxy_denominator_value",
    "path_order_result",
    "fill_status",
    "gross_simulated_r",
    "cost_adjusted_simulated_r",
    "stress_simulated_r",
    "win_count",
    "loss_count",
    "flat_count",
    "no_fill_count",
    "target_first_count",
    "stop_first_count",
    "neither_count",
    "ambiguous_count",
    "effective_n_key",
    "scope_effective_n",
    "scope_concentration_share_of_all_rows",
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


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    rows = read_jsonl(MATRIX_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    missing_rows = read_jsonl(MISSING_FIELD_LEDGER)
    join_rows = read_jsonl(JOIN_ISSUE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    performance_rows = read_jsonl(PERFORMANCE_LEDGER)
    recommendation_rows = read_jsonl(RECOMMENDATION_LEDGER)
    counts = result.get("counts") or {}

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if counts.get("input_performance_result_ok") != 1:
        issues.append("input performance result was not marked ok")
    if counts.get("input_geometry_result_ok") != 1:
        issues.append("input geometry result was not marked ok")
    if counts.get("input_recommendation_result_ok") != 1:
        issues.append("input recommendation result was not marked ok")
    if len(rows) != len(performance_rows):
        issues.append("matrix rows do not preserve every performance row")
    if counts.get("matrix_rows") != len(rows):
        issues.append("matrix row count mismatch")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if counts.get("simulated_missing_field_rows") != len(missing_rows):
        issues.append("missing simulated field count mismatch")
    if counts.get("source_join_issue_rows") != len(join_rows):
        issues.append("source join issue count mismatch")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len({row.get("performance_matrix_row_id") for row in rows}) != len(rows):
        issues.append("matrix row ids are not unique")
    if any(not boundary_ok(row) for row in rows + aggregate_rows + missing_rows + join_rows + system_rows):
        issues.append("one or more ledger rows failed research boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(rows):
        issues.append("aggregate row counts do not sum to matrix rows")
    if any(field not in row for row in rows for field in REQUIRED_ROW_FIELDS):
        issues.append("one or more matrix rows lack a required trading-performance field")
    if counts.get("rows_with_simulated_r") != len(rows):
        issues.append("not every matrix row has simulated R")
    if counts.get("rows_without_simulated_r") != 0:
        issues.append("rows without simulated R should be zero for this checkpoint")
    if counts.get("rows_with_table_recommendation") != len(recommendation_rows):
        issues.append("table recommendation match count does not equal recommendation input rows")
    if missing_rows:
        issues.append("simulated missing-field ledger should be empty after deterministic geometry repair")
    if join_rows:
        issues.append("source join issue ledger should be empty")

    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in rows)
    required_decisions = {
        "IMPLEMENT_BRANCH_LOCAL_SCORER_FROM_REPLAY_GEOMETRY_TABLE",
        "CARRY_AS_AVOID_INTELLIGENCE_FROM_REPLAY_GEOMETRY_TABLE",
        "KILL_AVOID_COMPARATOR_FROM_REPLAY_GEOMETRY",
        "KILL_DEFAULT_OFF_FROM_REPLAY_GEOMETRY",
    }
    if not required_decisions.issubset(set(decisions)):
        issues.append("matrix decisions do not include expected implement/carry/kill classes")
    path_counts = Counter(row.get("path_order_result") for row in rows)
    if not path_counts.get("TARGET_FIRST_PROXY_PATH"):
        issues.append("target-first rows are missing")
    if not path_counts.get("STOP_FIRST_PROXY_PATH"):
        issues.append("stop-first rows are missing")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "decision_counts": dict(sorted(decisions.items())),
        "path_order_counts": dict(sorted(path_counts.items())),
        "aggregate_rows": len(aggregate_rows),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
