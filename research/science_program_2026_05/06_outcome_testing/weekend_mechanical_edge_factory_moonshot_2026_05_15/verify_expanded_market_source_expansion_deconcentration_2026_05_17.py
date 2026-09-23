#!/usr/bin/env python3
"""Verify expanded-market source-expansion deconcentration checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_DECONCENTRATION"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
INPUT_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"
INPUT_GAP_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SOURCE_GAP_PROOF_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
MONTH_LEDGER = ROUTE_DIR / f"{PREFIX}_MONTH_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_source_expansion_deconcentration.py",
    ROUTE_DIR / "build_expanded_market_source_expansion_deconcentration_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    ROW_LEDGER,
    MONTH_LEDGER,
    AGGREGATE_LEDGER,
    ISSUE_LEDGER,
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


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


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
    for path in paths:
        text = read_text(path)
        for term in blocked_terms():
            if term in text:
                issues.append(f"blocked term {term!r} found in {path.relative_to(REPO)}")
    return issues


def ids(path: Path, field: str) -> set[str]:
    return {str(row.get(field) or "") for row in iter_jsonl(path)}


def main() -> None:
    issues: list[str] = []
    input_result = read_json(INPUT_RESULT)
    result = read_json(RESULT_PATH)
    counts = result.get("counts") or {}
    input_execution_ids = ids(INPUT_EXECUTION_LEDGER, "expanded_market_source_expansion_execution_row_id")
    input_gap_ids = ids(INPUT_GAP_LEDGER, "expanded_market_source_expansion_gap_row_id")

    row_ids: set[str] = set()
    covered_execution_ids: set[str] = set()
    covered_gap_ids: set[str] = set()
    row_count = 0
    rows_with_r = 0
    decision_counts: Counter[str] = Counter()
    for row in iter_jsonl(ROW_LEDGER):
        row_count += 1
        row_ids.add(str(row.get("expanded_market_source_expansion_deconcentration_row_id") or ""))
        execution_id = str(row.get("input_source_expansion_execution_row_id") or "")
        gap_id = str(row.get("input_source_expansion_gap_row_id") or "")
        if execution_id:
            covered_execution_ids.add(execution_id)
        if gap_id:
            covered_gap_ids.add(gap_id)
        if row.get("deconcentrated_cost_adjusted_simulated_r") is not None:
            rows_with_r += 1
        decision_counts[row.get("keep_kill_redesign_implement_decision")] += 1
        if not boundary_ok(row):
            issues.append("one or more deconcentration rows failed branch-local boundary checks")
            break
        status = row.get("source_expansion_deconcentration_status")
        if status == "SOURCE_EXPANSION_DECONCENTRATION_REPLAYED" and row.get("deconcentrated_effective_n") is None:
            issues.append("one or more replayed rows lacks deconcentrated effective-N")
            break
        if status != "SOURCE_EXPANSION_DECONCENTRATION_REPLAYED" and not row.get("missing_simulated_fields"):
            issues.append("one or more preserved noncomputable rows lacks missing simulated fields")
            break

    month_count = 0
    for row in iter_jsonl(MONTH_LEDGER):
        month_count += 1
        if not boundary_ok(row):
            issues.append("one or more month fold rows failed branch-local boundary checks")
            break
        if row.get("cost_adjusted_simulated_r") is None:
            issues.append("one or more month fold rows lacks simulated R")
            break

    aggregate_rows = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))

    if input_result.get("ok") is not True:
        issues.append("input source-expansion result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(input_execution_ids) != input_result.get("counts", {}).get("source_expansion_execution_rows"):
        issues.append("input execution count disagrees with CP266 result")
    if len(input_gap_ids) != input_result.get("counts", {}).get("source_gap_proof_rows"):
        issues.append("input gap count disagrees with CP266 result")
    if row_count != len(input_execution_ids) + len(input_gap_ids):
        issues.append("deconcentration rows do not preserve every CP266 execution and gap row")
    if covered_execution_ids != input_execution_ids:
        issues.append("not every CP266 execution row is covered")
    if covered_gap_ids != input_gap_ids:
        issues.append("not every CP266 source-gap row is covered")
    if len(row_ids) != row_count:
        issues.append("deconcentration row ids are not unique")
    if counts.get("input_execution_rows") != len(input_execution_ids):
        issues.append("result input execution count mismatch")
    if counts.get("input_gap_rows") != len(input_gap_ids):
        issues.append("result input gap count mismatch")
    if counts.get("deconcentration_rows") != row_count:
        issues.append("result deconcentration row count mismatch")
    if counts.get("rows_with_deconcentrated_r") != rows_with_r:
        issues.append("result rows-with-R count mismatch")
    if counts.get("month_rows") != month_count or month_count <= 0:
        issues.append("month fold row count mismatch or zero")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    if len(system_rows) != 1 or counts.get("system_rows") != 1:
        issues.append("system ledger must contain one row")
    if counts.get("decision_counts") != dict(sorted(decision_counts.items())):
        issues.append("decision count mismatch")
    if any(not boundary_ok(row) for row in aggregate_rows + issue_rows + system_rows + [result]):
        issues.append("one or more aggregate/system/result rows failed branch-local boundary checks")
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": {
            "deconcentration_rows": row_count,
            "rows_with_deconcentrated_r": rows_with_r,
            "month_rows": month_count,
            "aggregate_rows": len(aggregate_rows),
            "issue_rows": len(issue_rows),
        },
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
