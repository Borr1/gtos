#!/usr/bin/env python3
"""Verify expanded-market final-review execution checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
DECONCENTRATION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_DECONCENTRATION_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_FINAL_REVIEW_EXECUTION"

DECONCENTRATION_RESULT = ROUTE_DIR / f"{DECONCENTRATION_PREFIX}_RESULT_2026-05-17.json"
DECONCENTRATION_LEDGER = ROUTE_DIR / f"{DECONCENTRATION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
DECONCENTRATION_EVIDENCE_LEDGER = ROUTE_DIR / f"{DECONCENTRATION_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
DECONCENTRATION_CAPACITY_LEDGER = ROUTE_DIR / f"{DECONCENTRATION_PREFIX}_CAPACITY_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
CAPACITY_LEDGER = ROUTE_DIR / f"{PREFIX}_CAPACITY_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_final_review_execution.py",
    ROUTE_DIR / "build_expanded_market_final_review_execution_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    ROW_LEDGER,
    EVIDENCE_LEDGER,
    CAPACITY_LEDGER,
    ISSUE_LEDGER,
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


def as_float(value: Any) -> float | None:
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> None:
    issues: list[str] = []
    deconcentration_result = read_json(DECONCENTRATION_RESULT)
    input_rows = read_jsonl(DECONCENTRATION_LEDGER)
    input_evidence = read_jsonl(DECONCENTRATION_EVIDENCE_LEDGER)
    input_capacity = read_jsonl(DECONCENTRATION_CAPACITY_LEDGER)
    result = read_json(RESULT_PATH)
    rows = read_jsonl(ROW_LEDGER)
    evidence = read_jsonl(EVIDENCE_LEDGER)
    capacity_rows = read_jsonl(CAPACITY_LEDGER)
    issue_rows = read_jsonl(ISSUE_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if deconcentration_result.get("ok") is not True:
        issues.append("input CP228 result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(input_rows) != 1748:
        issues.append(f"input deconcentration count changed from 1748 to {len(input_rows)}")
    if len(input_evidence) != 9266:
        issues.append(f"input evidence count changed from 9266 to {len(input_evidence)}")
    if len(input_capacity) != 280:
        issues.append(f"input capacity count changed from 280 to {len(input_capacity)}")
    if counts.get("final_review_rows") != len(rows):
        issues.append("final review row count mismatch")
    if counts.get("final_review_evidence_rows") != len(evidence):
        issues.append("final review evidence row count mismatch")
    if counts.get("final_review_capacity_rows") != len(capacity_rows):
        issues.append("final review capacity count mismatch")
    if counts.get("final_review_issue_rows") != len(issue_rows):
        issues.append("final review issue count mismatch")
    if counts.get("aggregate_rows") != len(aggregates):
        issues.append("aggregate row count mismatch")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len(rows) != len(input_rows):
        issues.append("final review rows must preserve every input row")
    if len(evidence) != len(input_evidence):
        issues.append("final review evidence must preserve every input evidence row")
    if len(capacity_rows) != len(input_capacity):
        issues.append("final review capacity rows must preserve every input capacity row")
    if issue_rows:
        issues.append("final review issue ledger is not empty")
    if any(not boundary_ok(row) for row in rows + evidence + capacity_rows + issue_rows + aggregates + system_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")

    if len({row.get("final_review_row_id") for row in rows}) != len(rows):
        issues.append("final review row ids are not unique")
    if len({row.get("final_review_evidence_row_id") for row in evidence}) != len(evidence):
        issues.append("final review evidence row ids are not unique")
    if len({row.get("final_review_capacity_row_id") for row in capacity_rows}) != len(capacity_rows):
        issues.append("final review capacity row ids are not unique")

    input_deconcentration_ids = [row.get("deconcentration_row_id") for row in input_rows]
    output_deconcentration_ids = [row.get("input_deconcentration_row_id") for row in rows]
    if Counter(input_deconcentration_ids) != Counter(output_deconcentration_ids):
        issues.append("input deconcentration ids are not covered exactly once")
    input_evidence_ids = [row.get("deconcentration_evidence_row_id") for row in input_evidence]
    output_evidence_ids = [row.get("input_deconcentration_evidence_row_id") for row in evidence]
    if Counter(input_evidence_ids) != Counter(output_evidence_ids):
        issues.append("input deconcentration evidence ids are not covered exactly once")
    input_capacity_ids = [row.get("deconcentration_capacity_row_id") for row in input_capacity]
    output_capacity_ids = [row.get("input_deconcentration_capacity_row_id") for row in capacity_rows]
    if Counter(input_capacity_ids) != Counter(output_capacity_ids):
        issues.append("input capacity ids are not covered exactly once")
    if sum(as_int(row.get("final_review_evidence_rows")) for row in rows) != len(evidence):
        issues.append("final review evidence counts do not sum to evidence ledger rows")
    if sum(as_int(row.get("row_count")) for row in aggregates) != len(rows):
        issues.append("aggregate row counts do not sum to final review rows")
    if any(not row.get("source_path") or not row.get("source_file_sha256") for row in rows):
        issues.append("one or more final review rows lack source path/hash")
    if any(row.get("final_review_evidence_status") != "FINAL_REVIEW_EVIDENCE_COMPLETE" for row in rows):
        issues.append("one or more final review rows lack complete evidence")
    if any(abs(as_float(row.get("average_selected_intrabar_cost_adjusted_recompute_delta")) or 0.0) > 1e-9 for row in rows):
        issues.append("one or more recomputed evidence means differ from row means")
    if any((as_float(row.get("max_capacity_utilization")) or 0.0) > 1.0 + 1e-9 for row in rows):
        issues.append("one or more final review rows exceed capacity")

    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in rows)
    if decisions.get("IMPLEMENT_EXPANDED_MARKET_FINAL_REVIEW_BRANCH_LOCAL") != 1597:
        issues.append("implement final-review row count is not 1597")
    if decisions.get("REDESIGN_EXPANDED_MARKET_FINAL_REVIEW_CAPACITY_BLOCKED") != 151:
        issues.append("capacity-blocked final-review row count is not 151")
    if counts.get("implement_rows") + counts.get("redesign_rows") != len(rows):
        issues.append("implement plus redesign counts do not equal final review rows")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "decision_counts": dict(sorted(decisions.items())),
        "final_review_rows": len(rows),
        "final_review_evidence_rows": len(evidence),
        "final_review_capacity_rows": len(capacity_rows),
        "aggregate_rows": len(aggregates),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
