#!/usr/bin/env python3
"""Verify expanded-market deconcentration execution checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SELECTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PORTFOLIO_ARTIFACT_SELECTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_DECONCENTRATION_EXECUTION"

SELECTION_RESULT = ROUTE_DIR / f"{SELECTION_PREFIX}_RESULT_2026-05-17.json"
SELECTION_LEDGER = ROUTE_DIR / f"{SELECTION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
SELECTION_EVIDENCE_LEDGER = ROUTE_DIR / f"{SELECTION_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
CAPACITY_LEDGER = ROUTE_DIR / f"{PREFIX}_CAPACITY_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_deconcentration_execution.py",
    ROUTE_DIR / "build_expanded_market_deconcentration_execution_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    ROW_LEDGER,
    EVIDENCE_LEDGER,
    CAPACITY_LEDGER,
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


def as_int(value: Any) -> int:
    if value is None or value == "" or isinstance(value, bool):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def capacity_key(row: dict[str, Any]) -> tuple[str, str]:
    value = row.get("capacity_value")
    if isinstance(value, list):
        normalized_value = "|".join(str(part) for part in value)
    else:
        normalized_value = "" if value is None else str(value)
    return str(row.get("capacity_dimension")), normalized_value


def main() -> None:
    issues: list[str] = []
    selection_result = read_json(SELECTION_RESULT)
    input_selections = read_jsonl(SELECTION_LEDGER)
    input_evidence = read_jsonl(SELECTION_EVIDENCE_LEDGER)
    result = read_json(RESULT_PATH)
    rows = read_jsonl(ROW_LEDGER)
    evidence = read_jsonl(EVIDENCE_LEDGER)
    capacity_rows = read_jsonl(CAPACITY_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if selection_result.get("ok") is not True:
        issues.append("input CP227 result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(input_selections) != 1748:
        issues.append(f"input selection count changed from 1748 to {len(input_selections)}")
    if len(input_evidence) != 9266:
        issues.append(f"input evidence count changed from 9266 to {len(input_evidence)}")
    if counts.get("deconcentration_rows") != len(rows):
        issues.append("deconcentration row count mismatch")
    if counts.get("deconcentration_evidence_rows") != len(evidence):
        issues.append("deconcentration evidence row count mismatch")
    if counts.get("deconcentration_capacity_rows") != len(capacity_rows):
        issues.append("capacity row count mismatch")
    if counts.get("aggregate_rows") != len(aggregates):
        issues.append("aggregate row count mismatch")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len(rows) != len(input_selections):
        issues.append("deconcentration rows must preserve every input selection row")
    if len(evidence) != len(input_evidence):
        issues.append("deconcentration evidence must preserve every input evidence row")
    if any(not boundary_ok(row) for row in rows + evidence + capacity_rows + aggregates + system_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")

    if len({row.get("deconcentration_row_id") for row in rows}) != len(rows):
        issues.append("deconcentration row ids are not unique")
    if len({row.get("deconcentration_evidence_row_id") for row in evidence}) != len(evidence):
        issues.append("deconcentration evidence row ids are not unique")
    if len({row.get("deconcentration_capacity_row_id") for row in capacity_rows}) != len(capacity_rows):
        issues.append("capacity row ids are not unique")

    input_selection_ids = [row.get("portfolio_artifact_selection_row_id") for row in input_selections]
    output_selection_ids = [row.get("input_portfolio_artifact_selection_row_id") for row in rows]
    if Counter(input_selection_ids) != Counter(output_selection_ids):
        issues.append("input selection ids are not covered exactly once")
    input_evidence_ids = [row.get("portfolio_artifact_selection_evidence_row_id") for row in input_evidence]
    output_evidence_ids = [row.get("input_portfolio_artifact_selection_evidence_row_id") for row in evidence]
    if Counter(input_evidence_ids) != Counter(output_evidence_ids):
        issues.append("input evidence ids are not covered exactly once")
    if sum(as_int(row.get("evidence_execution_rows")) for row in rows) != len(evidence):
        issues.append("row evidence counts do not sum to evidence ledger rows")
    if sum(as_int(row.get("row_count")) for row in aggregates) != len(rows):
        issues.append("aggregate row counts do not sum to deconcentration rows")

    base_selected_inputs = [
        row for row in input_selections if row.get("portfolio_selection_status") == "PORTFOLIO_ARTIFACT_SELECTED"
    ]
    if counts.get("base_selected_rows") != len(base_selected_inputs):
        issues.append("base selected output count does not match CP227 selected rows")
    selected_rows = [row for row in rows if row.get("capacity_selected") is True]
    blocked_rows = [row for row in rows if row.get("capacity_selected") is not True]
    if counts.get("capacity_selected_rows") != len(selected_rows):
        issues.append("capacity selected count mismatch")
    if counts.get("redesign_preserved_rows") != len(blocked_rows):
        issues.append("redesign preserved count mismatch")
    if len(selected_rows) + len(blocked_rows) != len(rows):
        issues.append("selected plus preserved rows do not equal deconcentration rows")
    if counts.get("capacity_added_rows", 0) <= 0:
        issues.append("no guarded rows were selected under capacity")
    if counts.get("redesign_preserved_rows", 0) <= 0:
        issues.append("no guarded rows were preserved with capacity blockers")
    if counts.get("capacity_filled_rows", 0) <= 0:
        issues.append("no capacity-filled rows were emitted")
    if any(not row.get("source_path") or not row.get("source_file_sha256") for row in rows):
        issues.append("one or more deconcentration rows lack source path/hash")
    if any(row.get("capacity_selected") is not True and not row.get("capacity_blocking_dimensions") for row in rows):
        issues.append("one or more blocked rows lack blocking dimensions")

    capacity_by_key = {capacity_key(row): row for row in capacity_rows}
    for cap_row in capacity_rows:
        selected_count = as_int(cap_row.get("selected_artifact_rows"))
        limit = as_int(cap_row.get("capacity_limit_rows"))
        if selected_count > limit:
            issues.append(f"capacity violation for {capacity_key(cap_row)} selected {selected_count} > {limit}")
    if len(capacity_by_key) != len(capacity_rows):
        issues.append("capacity dimension/value rows are not unique")

    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in rows)
    if "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATION_BASE_SELECTED" not in decisions:
        issues.append("base selected decision class is absent")
    if "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATION_CAPACITY_SELECTED" not in decisions:
        issues.append("capacity selected decision class is absent")
    if "REDESIGN_EXPANDED_MARKET_DECONCENTRATION_CAPACITY_BLOCKED" not in decisions:
        issues.append("capacity blocked decision class is absent")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "decision_counts": dict(sorted(decisions.items())),
        "deconcentration_rows": len(rows),
        "deconcentration_evidence_rows": len(evidence),
        "capacity_rows": len(capacity_rows),
        "aggregate_rows": len(aggregates),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
