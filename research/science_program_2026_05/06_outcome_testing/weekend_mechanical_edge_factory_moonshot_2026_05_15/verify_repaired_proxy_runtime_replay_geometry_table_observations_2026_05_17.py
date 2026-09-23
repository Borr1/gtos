#!/usr/bin/env python3
"""Verify branch-local observation rows from geometry table execution."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_OBSERVATIONS"
EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_EXECUTION"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SCORER_OBSERVATION_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_OBSERVATION_LEDGER_2026-05-17.jsonl"
AVOID_OBSERVATION_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_OBSERVATION_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SOURCE_GAP_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_GAP_PRESERVATION_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

SCORER_EXECUTION_LEDGER = ROUTE_DIR / f"{EXEC_PREFIX}_SCORER_EXECUTION_LEDGER_2026-05-17.jsonl"
AVOID_EXECUTION_LEDGER = ROUTE_DIR / f"{EXEC_PREFIX}_AVOID_EXECUTION_LEDGER_2026-05-17.jsonl"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_observations.py",
    ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_geometry_table_observations_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    SCORER_OBSERVATION_LEDGER,
    AVOID_OBSERVATION_LEDGER,
    AGGREGATE_LEDGER,
    SOURCE_GAP_LEDGER,
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


def validate_observation_fields(rows: list[dict[str, Any]]) -> list[str]:
    required = [
        "geometry_table_observation_row_id",
        "input_geometry_table_execution_row_id",
        "input_geometry_table_row_id",
        "input_geometry_repair_row_id",
        "input_performance_row_id",
        "input_replay_numeric_event_row_id",
        "observation_kind",
        "family",
        "symbol",
        "route_session",
        "market_timeframe",
        "horizon_id",
        "source_component",
        "entry_reference",
        "path_order_result",
        "fill_status",
        "gross_simulated_r",
        "cost_adjusted_simulated_r",
        "stress_simulated_r",
        "win_count",
        "loss_count",
        "target_first_count",
        "stop_first_count",
        "observation_signal",
        "observation_action",
    ]
    issues: list[str] = []
    for row in rows:
        for field in required:
            if field not in row:
                issues.append(f"missing observation field {field} on {row.get('geometry_table_observation_row_id')}")
    return issues


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    scorer_rows = read_jsonl(SCORER_OBSERVATION_LEDGER)
    avoid_rows = read_jsonl(AVOID_OBSERVATION_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    gap_rows = read_jsonl(SOURCE_GAP_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    scorer_execution_rows = read_jsonl(SCORER_EXECUTION_LEDGER)
    avoid_execution_rows = read_jsonl(AVOID_EXECUTION_LEDGER)
    counts = result.get("counts") or {}
    all_rows = scorer_rows + avoid_rows

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if counts.get("input_execution_result_ok") != 1:
        issues.append("input execution result was not marked ok")
    if len(scorer_rows) != len(scorer_execution_rows):
        issues.append("scorer observation rows do not preserve scorer execution rows")
    if len(avoid_rows) != len(avoid_execution_rows):
        issues.append("avoid observation rows do not preserve avoid execution rows")
    if counts.get("scorer_observation_rows") != len(scorer_rows):
        issues.append("scorer observation count mismatch")
    if counts.get("avoid_observation_rows") != len(avoid_rows):
        issues.append("avoid observation count mismatch")
    if counts.get("total_observation_rows") != len(all_rows):
        issues.append("total observation count mismatch")
    if counts.get("aggregate_observation_rows") != len(aggregate_rows):
        issues.append("aggregate observation count mismatch")
    if counts.get("source_gap_preservation_rows") != len(gap_rows):
        issues.append("source gap preservation count mismatch")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len({row.get("geometry_table_observation_row_id") for row in all_rows}) != len(all_rows):
        issues.append("observation row ids are not unique")
    if any(row.get("cost_adjusted_simulated_r") is None for row in all_rows):
        issues.append("one or more observation rows lack cost-adjusted simulated R")
    if any(row.get("source_gap_fields") for row in all_rows):
        issues.append("one or more observation rows preserved a source gap")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(all_rows):
        issues.append("aggregate row counts do not sum to observation rows")
    if any(not boundary_ok(row) for row in all_rows + aggregate_rows + gap_rows + system_rows):
        issues.append("one or more ledger rows failed research boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")

    issues.extend(validate_observation_fields(all_rows))
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    signals = Counter(row.get("observation_signal") for row in all_rows)
    aggregate_actions = Counter(row.get("aggregate_observation_action") for row in aggregate_rows)
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "observation_signal_counts": dict(sorted(signals.items())),
        "aggregate_observation_action_counts": dict(sorted(aggregate_actions.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
