#!/usr/bin/env python3
"""Verify runtime replay performance tables preserve rows and emit simulated-R fields."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_PERFORMANCE"
SPEC_EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_SPEC_EXECUTION"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
MISSING_FIELD_LEDGER = ROUTE_DIR / f"{PREFIX}_MISSING_SIMULATED_FIELD_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
SCORER_EXECUTION_LEDGER = ROUTE_DIR / f"{SPEC_EXEC_PREFIX}_SCORER_EXECUTION_LEDGER_2026-05-17.jsonl"
COMPARATOR_EXECUTION_LEDGER = ROUTE_DIR / f"{SPEC_EXEC_PREFIX}_COMPARATOR_EXECUTION_LEDGER_2026-05-17.jsonl"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_performance.py",
    ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_performance_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, ROW_LEDGER, AGGREGATE_LEDGER, MISSING_FIELD_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]


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


def validate_required_row_fields(rows: list[dict[str, Any]]) -> list[str]:
    required = [
        "branch",
        "family",
        "symbol",
        "route_session",
        "market_timeframe",
        "horizon_id",
        "side",
        "follow_inverse_default_off_avoid_class",
        "entry_reference",
        "stop_target_or_proxy_denominator_field",
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
        "row_disposition",
    ]
    issues: list[str] = []
    for row in rows:
        for field in required:
            if field not in row:
                issues.append(f"missing row field {field} on {row.get('performance_row_id')}")
    return issues


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    rows = read_jsonl(ROW_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    missing_rows = read_jsonl(MISSING_FIELD_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    scorer_rows = read_jsonl(SCORER_EXECUTION_LEDGER)
    comparator_rows = read_jsonl(COMPARATOR_EXECUTION_LEDGER)

    expected_rows = len(scorer_rows) + len(comparator_rows)
    counts = result.get("counts") or {}
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(rows) != expected_rows:
        issues.append(f"row ledger count {len(rows)} != input execution count {expected_rows}")
    if counts.get("performance_rows") != len(rows):
        issues.append("result performance row count mismatch")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("result aggregate row count mismatch")
    if counts.get("missing_simulated_field_rows") != len(missing_rows):
        issues.append("missing simulated field count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len({row.get("performance_row_id") for row in rows}) != len(rows):
        issues.append("performance row ids are not unique")
    if len({row.get("input_execution_row_id") for row in rows}) != len(rows):
        issues.append("input execution rows were not preserved one-to-one")
    if counts.get("rows_with_proxy_r") != sum(row.get("gross_simulated_r") is not None for row in rows):
        issues.append("rows_with_proxy_r count mismatch")
    if counts.get("rows_without_proxy_r") != sum(row.get("gross_simulated_r") is None for row in rows):
        issues.append("rows_without_proxy_r count mismatch")
    if counts.get("target_first_rows") != 0 or counts.get("stop_first_rows") != 0:
        issues.append("target/stop-first counts should remain zero without exact target/stop order")
    if counts.get("ambiguous_rows") != counts.get("rows_with_proxy_r"):
        issues.append("ambiguous proxy path count should equal proxy-R row count")
    if not aggregate_rows:
        issues.append("aggregate performance ledger is empty")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(rows):
        issues.append("aggregate row counts do not sum to row ledger count")
    if any(not boundary_ok(row) for row in rows + aggregate_rows + missing_rows + system_rows):
        issues.append("one or more ledger rows failed research boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")

    issues.extend(validate_required_row_fields(rows))
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    aggregate_decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in aggregate_rows)
    row_dispositions = Counter(row.get("row_disposition") for row in rows)
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "row_disposition_counts": dict(sorted(row_dispositions.items())),
        "aggregate_decision_counts": dict(sorted(aggregate_decisions.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
