#!/usr/bin/env python3
"""Verify expanded-market proxy-R performance checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PROXY_R_PERFORMANCE"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_EXECUTION_SPECS"
COMPUTED_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_COMPUTED_ACTION_EXECUTION_BUNDLE"
WORK_ORDER_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_WORK_ORDER_EXECUTION_BUNDLE"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
PERFORMANCE_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
NONCOMPUTABLE_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_ACCESS_PROOF_LEDGER_2026-05-17.jsonl"
SEED_CONSUMPTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SEED_CONSUMPTION_LEDGER_2026-05-17.jsonl"
DISCOVERED_SOURCE_LEDGER = ROUTE_DIR / f"{PREFIX}_DISCOVERED_OHLC_SOURCE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
MARKET_POPULATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MARKET_EXPANSION_POPULATION_LEDGER_2026-05-17.jsonl"
COMPUTED_EXPANSION_MATRIX = (
    ROUTE_DIR / f"{COMPUTED_PREFIX}_MARKET_TIMEFRAME_SESSION_HORIZON_EXPANSION_MATRIX_2026-05-17.jsonl"
)
WORK_ORDER_EXPANSION_MATRIX = (
    ROUTE_DIR / f"{WORK_ORDER_PREFIX}_MARKET_TIMEFRAME_SESSION_HORIZON_EXPANSION_MATRIX_2026-05-17.jsonl"
)

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_proxy_r_performance.py",
    ROUTE_DIR / "build_expanded_market_proxy_r_performance_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    PERFORMANCE_LEDGER,
    AGGREGATE_LEDGER,
    NONCOMPUTABLE_LEDGER,
    SEED_CONSUMPTION_LEDGER,
    DISCOVERED_SOURCE_LEDGER,
    SYSTEM_LEDGER,
    SUMMARY_PATH,
]
REQUIRED_PERFORMANCE_FIELDS = (
    "expanded_market_performance_row_id",
    "input_expansion_matrix_row_id",
    "input_market_population_row_id",
    "symbol",
    "source_path",
    "source_file_sha256",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "side",
    "entry_reference",
    "proxy_entry_price",
    "proxy_denominator_price",
    "proxy_target_price",
    "proxy_stop_price",
    "path_order_result",
    "fill_status",
    "gross_simulated_r",
    "cost_adjusted_simulated_r",
    "stress_simulated_r",
    "win_count",
    "loss_count",
    "zero_count",
    "effective_n",
    "effective_n_after_duplicate_collapse",
    "concentration_top_month_share",
    "follow_inverse_default_off_avoid_class",
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
    performance_rows = read_jsonl(PERFORMANCE_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    noncomputable_rows = read_jsonl(NONCOMPUTABLE_LEDGER)
    seed_rows = read_jsonl(SEED_CONSUMPTION_LEDGER)
    discovered_rows = read_jsonl(DISCOVERED_SOURCE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    market_rows = read_jsonl(MARKET_POPULATION_LEDGER)
    expansion_rows = read_jsonl(COMPUTED_EXPANSION_MATRIX)
    work_order_rows = read_jsonl(WORK_ORDER_EXPANSION_MATRIX)
    counts = result.get("counts") or {}

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    expected_market = len(market_rows)
    expected_expansion = len(expansion_rows)
    if expected_market != 301:
        issues.append(f"market population seed count changed from 301 to {expected_market}")
    if expected_expansion != 1145:
        issues.append(f"computed expansion matrix seed count changed from 1145 to {expected_expansion}")
    if len(work_order_rows) != 1145:
        issues.append("work-order expansion matrix seed count is not 1145")
    if counts.get("input_market_population_rows") != expected_market:
        issues.append("result market population count mismatch")
    if counts.get("input_expansion_matrix_rows") != expected_expansion:
        issues.append("result expansion matrix count mismatch")
    if counts.get("input_work_order_expansion_matrix_rows") != len(work_order_rows):
        issues.append("result work-order expansion count mismatch")
    if counts.get("performance_rows") != len(performance_rows):
        issues.append("performance row count mismatch")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if counts.get("source_access_proof_rows") != len(noncomputable_rows):
        issues.append("source/access proof row count mismatch")
    if counts.get("seed_consumption_rows") != len(seed_rows):
        issues.append("seed consumption row count mismatch")
    if counts.get("discovered_ohlc_source_rows") != len(discovered_rows):
        issues.append("discovered OHLC source row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if counts.get("rows_with_simulated_r") != len(performance_rows):
        issues.append("every performance row must have cost-adjusted simulated R")
    if counts.get("rows_without_simulated_r") != 0:
        issues.append("rows_without_simulated_r must be zero for scored performance rows")
    if not performance_rows:
        issues.append("performance rows are empty")
    if len(seed_rows) != expected_market + expected_expansion:
        issues.append("seed consumption rows do not preserve both seed universes")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(performance_rows):
        issues.append("aggregate row counts do not sum to performance rows")
    if any(not boundary_ok(row) for row in performance_rows + aggregate_rows + noncomputable_rows + seed_rows + discovered_rows + system_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if any(field not in row for row in performance_rows for field in REQUIRED_PERFORMANCE_FIELDS):
        issues.append("one or more performance rows lacks a required field")
    if len({row.get("expanded_market_performance_row_id") for row in performance_rows}) != len(performance_rows):
        issues.append("performance row ids are not unique")
    if len({row.get("expanded_market_noncomputable_row_id") for row in noncomputable_rows}) != len(noncomputable_rows):
        issues.append("source/access proof ids are not unique")
    market_ids = {row.get("market_population_row_id") for row in market_rows}
    consumed_market = {
        row.get("input_market_population_row_id")
        for row in performance_rows
        if row.get("input_market_population_row_id")
    }
    proof_market = {
        row.get("input_market_population_row_id")
        for row in noncomputable_rows
        if row.get("input_market_population_row_id")
    }
    if not market_ids.issubset(consumed_market | proof_market):
        issues.append("not every market population source produced performance rows or source/access proof")
    expansion_ids = {row.get("market_timeframe_session_horizon_expansion_row_id") for row in expansion_rows}
    consumed_expansion = {
        row.get("input_expansion_matrix_row_id")
        for row in performance_rows + noncomputable_rows
        if row.get("input_expansion_matrix_row_id")
    }
    if not expansion_ids.issubset(consumed_expansion):
        issues.append("not every expansion matrix row produced performance or source/access proof")
    market_paths = {row.get("source_path") for row in market_rows}
    scored_or_proved_paths = {row.get("source_path") for row in performance_rows + noncomputable_rows}
    if not market_paths.issubset(scored_or_proved_paths):
        issues.append("market source paths are not fully scored or proved non-computable")
    if not any(row.get("source_access_proof_rows_generated") for row in seed_rows):
        issues.append("source/access proof rows were not tied back to seed consumption")
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in performance_rows)
    if not decisions:
        issues.append("decision counts are empty")
    if not any(str(decision).startswith("IMPLEMENT") for decision in decisions):
        issues.append("implementation decision class is absent")
    if not any("AVOID" in str(decision) for decision in decisions):
        issues.append("avoid-intelligence decision class is absent")
    if not any(str(decision).startswith("KILL") for decision in decisions):
        issues.append("kill decision class is absent")
    if not any(str(decision).startswith("REDESIGN") for decision in decisions):
        issues.append("redesign decision class is absent")
    if not any(row.get("route_session") == "tokyo_kz" for row in performance_rows):
        issues.append("tokyo session rows are absent")
    if not any(row.get("horizon_id") == "h32" for row in performance_rows):
        issues.append("h32 rows are absent")
    if not any(row.get("side") == "LONG" for row in performance_rows):
        issues.append("LONG side rows are absent")
    if not any(row.get("side") == "SHORT" for row in performance_rows):
        issues.append("SHORT side rows are absent")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "decision_counts": dict(sorted(decisions.items())),
        "performance_rows": len(performance_rows),
        "aggregate_rows": len(aggregate_rows),
        "source_access_proof_rows": len(noncomputable_rows),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
