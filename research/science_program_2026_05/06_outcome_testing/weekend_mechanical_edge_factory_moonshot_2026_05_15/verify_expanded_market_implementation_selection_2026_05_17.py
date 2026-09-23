#!/usr/bin/env python3
"""Verify expanded-market implementation-selection checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
SIDE_PAIR_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SIDE_PAIR_ROBUSTNESS"
TEMPORAL_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_TEMPORAL_ROBUSTNESS"
INTRABAR_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_INTRABAR_GEOMETRY"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_IMPLEMENTATION_SELECTION"

SIDE_PAIR_RESULT = ROUTE_DIR / f"{SIDE_PAIR_PREFIX}_RESULT_2026-05-17.json"
SIDE_PAIR_LEDGER = ROUTE_DIR / f"{SIDE_PAIR_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
TEMPORAL_RESULT = ROUTE_DIR / f"{TEMPORAL_PREFIX}_RESULT_2026-05-17.json"
TEMPORAL_LEDGER = ROUTE_DIR / f"{TEMPORAL_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
INTRABAR_RESULT = ROUTE_DIR / f"{INTRABAR_PREFIX}_RESULT_2026-05-17.json"
INTRABAR_LEDGER = ROUTE_DIR / f"{INTRABAR_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_implementation_selection.py",
    ROUTE_DIR / "build_expanded_market_implementation_selection_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, ROW_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
REQUIRED_SELECTION_FIELDS = (
    "implementation_selection_row_id",
    "input_side_pair_robustness_row_id",
    "input_temporal_robustness_row_id",
    "input_selected_intrabar_geometry_row_id",
    "input_rejected_intrabar_geometry_row_id",
    "symbol",
    "source_symbol",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "source_component",
    "source_path",
    "source_file_sha256",
    "selected_side",
    "rejected_side",
    "side_pair_decision",
    "temporal_decision",
    "selected_intrabar_decision",
    "rejected_intrabar_decision",
    "selected_intrabar_cost_adjusted_simulated_r",
    "rejected_intrabar_cost_adjusted_simulated_r",
    "selected_minus_rejected_intrabar_cost_adjusted_r",
    "effective_n",
    "branch_local_candidate_family",
    "branch_local_candidate_expression",
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
    side_pair_result = read_json(SIDE_PAIR_RESULT)
    temporal_result = read_json(TEMPORAL_RESULT)
    intrabar_result = read_json(INTRABAR_RESULT)
    side_pair_rows = read_jsonl(SIDE_PAIR_LEDGER)
    temporal_rows = read_jsonl(TEMPORAL_LEDGER)
    intrabar_rows = read_jsonl(INTRABAR_LEDGER)
    result = read_json(RESULT_PATH)
    selection_rows = read_jsonl(ROW_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    issue_rows = read_jsonl(ISSUE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if side_pair_result.get("ok") is not True:
        issues.append("input CP217 result is not ok")
    if temporal_result.get("ok") is not True:
        issues.append("input CP218 result is not ok")
    if intrabar_result.get("ok") is not True:
        issues.append("input CP219 result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(side_pair_rows) != 22610:
        issues.append(f"input side-pair row count changed from 22610 to {len(side_pair_rows)}")
    if len(temporal_rows) != 22610:
        issues.append(f"input temporal row count changed from 22610 to {len(temporal_rows)}")
    if len(intrabar_rows) != 45220:
        issues.append(f"input intrabar row count changed from 45220 to {len(intrabar_rows)}")
    if counts.get("implementation_selection_rows") != len(selection_rows):
        issues.append("selection row count mismatch")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if counts.get("issue_rows") != len(issue_rows):
        issues.append("issue row count mismatch")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len(selection_rows) + len(issue_rows) != len(side_pair_rows):
        issues.append("not every side-pair row produced selection row or issue proof")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(selection_rows):
        issues.append("aggregate row counts do not sum to selection rows")
    if any(not boundary_ok(row) for row in selection_rows + aggregate_rows + issue_rows + system_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if any(field not in row for row in selection_rows for field in REQUIRED_SELECTION_FIELDS):
        issues.append("one or more selection rows lacks a required field")
    if len({row.get("implementation_selection_row_id") for row in selection_rows}) != len(selection_rows):
        issues.append("selection row ids are not unique")
    if len({row.get("implementation_selection_issue_row_id") for row in issue_rows}) != len(issue_rows):
        issues.append("issue row ids are not unique")
    side_pair_ids = {row.get("side_pair_robustness_row_id") for row in side_pair_rows}
    selection_ids = {row.get("input_side_pair_robustness_row_id") for row in selection_rows}
    issue_ids = {row.get("input_side_pair_robustness_row_id") for row in issue_rows}
    if side_pair_ids != selection_ids | issue_ids:
        issues.append("selection and issue ids do not exactly cover side-pair ids")
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in selection_rows)
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
    if not any(row.get("selected_side") == "LONG" for row in selection_rows):
        issues.append("LONG selected rows are absent")
    if not any(row.get("selected_side") == "SHORT" for row in selection_rows):
        issues.append("SHORT selected rows are absent")
    if not any(row.get("route_session") == "tokyo_kz" for row in selection_rows):
        issues.append("tokyo session rows are absent")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "decision_counts": dict(sorted(decisions.items())),
        "selection_rows": len(selection_rows),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issue_rows),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
