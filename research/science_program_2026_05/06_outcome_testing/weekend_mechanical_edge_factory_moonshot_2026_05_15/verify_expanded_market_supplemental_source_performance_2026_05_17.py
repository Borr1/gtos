#!/usr/bin/env python3
"""Verify supplemental expanded-market source performance checkpoint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SUPPLEMENTAL_SOURCE_PERFORMANCE"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PROXY_R_PERFORMANCE"

INPUT_PERFORMANCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
PERFORMANCE_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
SOURCE_LEDGER = ROUTE_DIR / f"{PREFIX}_ADDITIONAL_SOURCE_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
MISSING_FIELD_LEDGER = ROUTE_DIR / f"{PREFIX}_MISSING_SIMULATED_FIELD_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_supplemental_source_performance.py",
    ROUTE_DIR / "build_expanded_market_supplemental_source_performance_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    PERFORMANCE_LEDGER,
    SOURCE_LEDGER,
    AGGREGATE_LEDGER,
    MISSING_FIELD_LEDGER,
    SYSTEM_LEDGER,
    SUMMARY_PATH,
]
REQUIRED_PERFORMANCE_FIELDS = (
    "expanded_market_supplemental_performance_row_id",
    "performance_source_family",
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
    "target_first_count",
    "stop_first_count",
    "neither_count",
    "ambiguous_count",
    "effective_n",
    "effective_n_after_duplicate_collapse",
    "concentration_top_month_share",
    "missing_simulated_fields",
    "follow_inverse_default_off_avoid_class",
    "keep_kill_redesign_implement_decision",
)
SESSIONS = {"ALL_SESSIONS", "tokyo_kz", "london_core", "ny_core", "off_core_session"}
HORIZONS = {"h4", "h16", "h32"}
SIDES = {"LONG", "SHORT"}


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
    input_rows = read_jsonl(INPUT_PERFORMANCE_LEDGER)
    performance_rows = read_jsonl(PERFORMANCE_LEDGER)
    source_rows = read_jsonl(SOURCE_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    missing_rows = read_jsonl(MISSING_FIELD_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(input_rows) != 45220:
        issues.append(f"input seed-floor performance count changed from 45220 to {len(input_rows)}")
    if counts.get("input_seed_floor_performance_rows") != len(input_rows):
        issues.append("input seed-floor count mismatch")
    if counts.get("additional_source_rows") != len(source_rows):
        issues.append("additional source row count mismatch")
    expected_additional = len(source_rows) * len(SESSIONS) * len(HORIZONS) * len(SIDES)
    if counts.get("additional_source_performance_rows") != expected_additional:
        issues.append("additional source performance count does not cover every session/horizon/side")
    if counts.get("combined_performance_rows") != len(performance_rows):
        issues.append("combined performance row count mismatch")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if counts.get("missing_simulated_field_rows") != len(missing_rows):
        issues.append("missing simulated-field row count mismatch")
    if counts.get("rows_with_simulated_r") != len(performance_rows) - len(missing_rows):
        issues.append("rows_with_simulated_r count mismatch")
    if len(system_rows) != 1 or counts.get("system_rows") != 1:
        issues.append("system ledger must contain one row")
    if len({row.get("expanded_market_supplemental_performance_row_id") for row in performance_rows}) != len(
        performance_rows
    ):
        issues.append("supplemental performance row ids are not unique")
    if len({row.get("supplemental_source_row_id") for row in source_rows}) != len(source_rows):
        issues.append("additional source row ids are not unique")
    if len({row.get("expanded_market_supplemental_aggregate_row_id") for row in aggregate_rows}) != len(
        aggregate_rows
    ):
        issues.append("aggregate row ids are not unique")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(performance_rows):
        issues.append("aggregate row counts do not sum to combined performance rows")
    if any(
        not boundary_ok(row)
        for row in performance_rows + source_rows + aggregate_rows + missing_rows + system_rows + [result]
    ):
        issues.append("one or more rows failed branch-local boundary checks")
    if any(field not in row for row in performance_rows for field in REQUIRED_PERFORMANCE_FIELDS):
        issues.append("one or more performance rows lacks a required field")

    input_ids = {row.get("expanded_market_performance_row_id") for row in input_rows}
    copied_ids = {
        row.get("input_expanded_market_performance_row_id")
        for row in performance_rows
        if row.get("performance_source_family") == "cp216_seed_floor_ohlc_csv"
    }
    if copied_ids != input_ids:
        issues.append("CP216 seed-floor row ids were not preserved exactly")

    additional_rows = [
        row for row in performance_rows if row.get("performance_source_family") == "sierra_scid_source_bound_m15"
    ]
    if len(additional_rows) != expected_additional:
        issues.append("additional source performance ledger count mismatch")
    source_ids = {row.get("supplemental_source_row_id") for row in source_rows}
    additional_source_ids = {row.get("input_supplemental_source_row_id") for row in additional_rows}
    if additional_source_ids != source_ids:
        issues.append("not every additional source row produced performance rows")
    for source in source_rows:
        combos = {
            (row.get("route_session"), row.get("horizon_id"), row.get("side"))
            for row in additional_rows
            if row.get("input_supplemental_source_row_id") == source.get("supplemental_source_row_id")
        }
        expected_combos = {(session, horizon, side) for session in SESSIONS for horizon in HORIZONS for side in SIDES}
        if combos != expected_combos:
            issues.append(f"incomplete session/horizon/side grid for {source.get('source_symbol')}")
            break
    missing_input_ids = {row.get("input_supplemental_performance_row_id") for row in missing_rows}
    actual_missing_ids = {
        row.get("expanded_market_supplemental_performance_row_id")
        for row in performance_rows
        if row.get("missing_simulated_fields")
    }
    if missing_input_ids != actual_missing_ids:
        issues.append("missing simulated-field ledger does not match performance rows")
    scored_rows = [
        row
        for row in performance_rows
        if not row.get("missing_simulated_fields")
        and (
            row.get("gross_simulated_r") is None
            or row.get("cost_adjusted_simulated_r") is None
            or row.get("stress_simulated_r") is None
        )
    ]
    if scored_rows:
        issues.append("one or more scored rows lacks gross/cost/stress simulated R")
    if any(not row.get("source_path") or not row.get("source_file_sha256") for row in performance_rows):
        issues.append("one or more performance rows lacks source path/hash")
    if any(int(row.get("source_parsed_ohlc_rows") or 0) <= 0 for row in source_rows):
        issues.append("one or more additional source rows has no parsed OHLC rows")
    if not aggregate_rows:
        issues.append("aggregate rows are empty")
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    print(
        json.dumps(
            {
                "ok": not issues,
                "issues": issues,
                "counts": {
                    "input_seed_floor_performance_rows": len(input_rows),
                    "additional_source_rows": len(source_rows),
                    "additional_source_performance_rows": len(additional_rows),
                    "combined_performance_rows": len(performance_rows),
                    "aggregate_rows": len(aggregate_rows),
                    "missing_simulated_field_rows": len(missing_rows),
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
