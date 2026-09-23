#!/usr/bin/env python3
"""Verify expanded-market intrabar geometry checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PROXY_R_PERFORMANCE"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_INTRABAR_GEOMETRY"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_PERFORMANCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
PROOF_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_ACCESS_PROOF_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_intrabar_geometry.py",
    ROUTE_DIR / "build_expanded_market_intrabar_geometry_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, ROW_LEDGER, AGGREGATE_LEDGER, PROOF_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
REQUIRED_GEOMETRY_FIELDS = (
    "intrabar_geometry_row_id",
    "input_expanded_market_performance_row_id",
    "input_expansion_matrix_row_id",
    "input_market_population_row_id",
    "symbol",
    "source_symbol",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "side",
    "source_component",
    "source_path",
    "source_file_sha256",
    "entry_reference",
    "proxy_entry_price",
    "proxy_denominator_price",
    "proxy_target_price",
    "proxy_stop_price",
    "path_order_result",
    "path_order_counts",
    "fill_status",
    "gross_simulated_r",
    "cost_adjusted_simulated_r",
    "stress_simulated_r",
    "horizon_close_proxy_cost_adjusted_simulated_r",
    "intrabar_minus_horizon_close_cost_adjusted_r",
    "win_count",
    "loss_count",
    "zero_count",
    "target_first_count",
    "stop_first_count",
    "neither_count",
    "ambiguous_count",
    "effective_n",
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
    input_result = read_json(INPUT_RESULT)
    input_rows = read_jsonl(INPUT_PERFORMANCE_LEDGER)
    result = read_json(RESULT_PATH)
    geometry_rows = read_jsonl(ROW_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    proof_rows = read_jsonl(PROOF_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if input_result.get("ok") is not True:
        issues.append("input CP216 result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(input_rows) != 45220:
        issues.append(f"input performance row count changed from 45220 to {len(input_rows)}")
    if counts.get("input_performance_rows") != len(input_rows):
        issues.append("result input performance count mismatch")
    if counts.get("intrabar_geometry_rows") != len(geometry_rows):
        issues.append("geometry row count mismatch")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if counts.get("source_access_proof_rows") != len(proof_rows):
        issues.append("source/access proof row count mismatch")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len(geometry_rows) + len(proof_rows) != len(input_rows):
        issues.append("not every CP216 performance row produced intrabar geometry or proof")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(geometry_rows):
        issues.append("aggregate row counts do not sum to geometry rows")
    if any(not boundary_ok(row) for row in geometry_rows + aggregate_rows + proof_rows + system_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if any(field not in row for row in geometry_rows for field in REQUIRED_GEOMETRY_FIELDS):
        issues.append("one or more geometry rows lacks a required field")
    if len({row.get("intrabar_geometry_row_id") for row in geometry_rows}) != len(geometry_rows):
        issues.append("geometry row ids are not unique")
    if len({row.get("intrabar_noncomputable_row_id") for row in proof_rows}) != len(proof_rows):
        issues.append("proof row ids are not unique")
    input_ids = {row.get("expanded_market_performance_row_id") for row in input_rows}
    geometry_ids = {row.get("input_expanded_market_performance_row_id") for row in geometry_rows}
    proof_ids = {row.get("input_expanded_market_performance_row_id") for row in proof_rows}
    if input_ids != geometry_ids | proof_ids:
        issues.append("geometry and proof row ids do not exactly cover input performance ids")
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in geometry_rows)
    path_counts: Counter[str] = Counter()
    for row in geometry_rows:
        path_counts.update(row.get("path_order_counts") or {})
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
    if path_counts.get("TARGET_FIRST_INTRABAR_PATH", 0) <= 0:
        issues.append("target-first intrabar paths are absent")
    if path_counts.get("STOP_FIRST_INTRABAR_PATH", 0) <= 0:
        issues.append("stop-first intrabar paths are absent")
    if path_counts.get("AMBIGUOUS_TARGET_AND_STOP_SAME_BAR", 0) <= 0:
        issues.append("ambiguous intrabar paths are absent")
    if not any(row.get("route_session") == "tokyo_kz" for row in geometry_rows):
        issues.append("tokyo session rows are absent")
    if not any(row.get("horizon_id") == "h32" for row in geometry_rows):
        issues.append("h32 rows are absent")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "decision_counts": dict(sorted(decisions.items())),
        "path_order_counts": dict(sorted(path_counts.items())),
        "geometry_rows": len(geometry_rows),
        "aggregate_rows": len(aggregate_rows),
        "source_access_proof_rows": len(proof_rows),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
