#!/usr/bin/env python3
"""Verify runtime replay geometry repair tables preserve rows and source proof."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_REPAIR"
PERF_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_PERFORMANCE"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
PATH_SCAN_LEDGER = ROUTE_DIR / f"{PREFIX}_PATH_SCAN_LEDGER_2026-05-17.jsonl"
MISSING_FIELD_LEDGER = ROUTE_DIR / f"{PREFIX}_MISSING_GEOMETRY_FIELD_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
PERFORMANCE_ROW_LEDGER = ROUTE_DIR / f"{PERF_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_repair.py",
    ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_geometry_repair_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, ROW_LEDGER, AGGREGATE_LEDGER, PATH_SCAN_LEDGER, MISSING_FIELD_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]


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


def validate_row_fields(rows: list[dict[str, Any]]) -> list[str]:
    required = [
        "geometry_repair_row_id",
        "input_performance_row_id",
        "source_path",
        "source_file_sha256",
        "proxy_entry_price",
        "proxy_stop_price",
        "proxy_target_price",
        "proxy_denominator_price",
        "path_order_result",
        "fill_status",
        "underlying_proxy_path_r",
        "action_adjusted_geometry_r",
        "cost_adjusted_geometry_r",
        "stress_geometry_r",
        "geometry_result_class",
        "target_first_count",
        "stop_first_count",
        "neither_count",
        "ambiguous_count",
        "remaining_missing_geometry_fields",
        "geometry_repair_decision",
    ]
    issues: list[str] = []
    for row in rows:
        for field in required:
            if field not in row:
                issues.append(f"missing geometry field {field} on {row.get('geometry_repair_row_id')}")
    return issues


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    rows = read_jsonl(ROW_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    scans = read_jsonl(PATH_SCAN_LEDGER)
    missing = read_jsonl(MISSING_FIELD_LEDGER)
    system = read_jsonl(SYSTEM_LEDGER)
    perf_rows = read_jsonl(PERFORMANCE_ROW_LEDGER)
    counts = result.get("counts") or {}

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(rows) != len(perf_rows):
        issues.append(f"geometry rows {len(rows)} != performance rows {len(perf_rows)}")
    if counts.get("geometry_repair_rows") != len(rows):
        issues.append("geometry row count mismatch")
    if counts.get("aggregate_geometry_rows") != len(aggregates):
        issues.append("aggregate row count mismatch")
    if counts.get("path_scan_rows") != len(scans):
        issues.append("path scan row count mismatch")
    if counts.get("missing_geometry_field_rows") != len(missing):
        issues.append("missing field row count mismatch")
    if len(system) != 1:
        issues.append("system ledger must contain one row")
    if len({row.get("geometry_repair_row_id") for row in rows}) != len(rows):
        issues.append("geometry repair row ids are not unique")
    if len({row.get("input_performance_row_id") for row in rows}) != len(rows):
        issues.append("performance rows were not preserved one-to-one")
    if sum(int(row.get("row_count") or 0) for row in aggregates) != len(rows):
        issues.append("aggregate row counts do not sum to geometry row count")
    if counts.get("deterministic_geometry_r_rows") != sum(row.get("action_adjusted_geometry_r") is not None for row in rows):
        issues.append("deterministic geometry-R count mismatch")
    if counts.get("ambiguous_rows") != sum(int(row.get("ambiguous_count") or 0) for row in rows):
        issues.append("ambiguous row count mismatch")
    if counts.get("target_first_rows") != sum(int(row.get("target_first_count") or 0) for row in rows):
        issues.append("target-first count mismatch")
    if counts.get("stop_first_rows") != sum(int(row.get("stop_first_count") or 0) for row in rows):
        issues.append("stop-first count mismatch")
    if any(row.get("source_file_sha256") in (None, "") for row in rows):
        issues.append("one or more geometry rows lack source file hash")
    if any(row.get("path_scan_status") != "PROXY_PATH_SCAN_COMPLETE" for row in scans):
        issues.append("one or more path scans did not complete")
    if any(not boundary_ok(row) for row in rows + aggregates + scans + missing + system):
        issues.append("one or more ledger rows failed research boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")

    issues.extend(validate_row_fields(rows))
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    row_decisions = Counter(row.get("geometry_repair_decision") for row in rows)
    aggregate_decisions = Counter(row.get("geometry_keep_kill_redesign_implement_decision") for row in aggregates)
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "geometry_repair_decision_counts": dict(sorted(row_decisions.items())),
        "aggregate_decision_counts": dict(sorted(aggregate_decisions.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
