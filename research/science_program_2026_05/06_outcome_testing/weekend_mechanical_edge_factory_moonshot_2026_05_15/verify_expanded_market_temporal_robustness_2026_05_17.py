#!/usr/bin/env python3
"""Verify expanded-market temporal robustness checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PERFORMANCE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PROXY_R_PERFORMANCE"
SIDE_PAIR_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SIDE_PAIR_ROBUSTNESS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_TEMPORAL_ROBUSTNESS"

PERFORMANCE_RESULT = ROUTE_DIR / f"{PERFORMANCE_PREFIX}_RESULT_2026-05-17.json"
PERFORMANCE_LEDGER = ROUTE_DIR / f"{PERFORMANCE_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
SIDE_PAIR_RESULT = ROUTE_DIR / f"{SIDE_PAIR_PREFIX}_RESULT_2026-05-17.json"
SIDE_PAIR_LEDGER = ROUTE_DIR / f"{SIDE_PAIR_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
FOLD_LEDGER = ROUTE_DIR / f"{PREFIX}_FOLD_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_temporal_robustness.py",
    ROUTE_DIR / "build_expanded_market_temporal_robustness_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, ROW_LEDGER, FOLD_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
REQUIRED_TEMPORAL_FIELDS = (
    "temporal_robustness_row_id",
    "input_side_pair_robustness_row_id",
    "input_long_performance_row_id",
    "input_short_performance_row_id",
    "symbol",
    "source_symbol",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "source_component",
    "source_path",
    "source_file_sha256",
    "overall_winner_side",
    "overall_winner_cost_adjusted_simulated_r",
    "winner_consistency_share",
    "positive_winner_fold_share",
    "min_test_effective_n",
    "worst_test_fold_winner_cost_adjusted_simulated_r",
    "recent_half_winner_cost_adjusted_simulated_r",
    "recent_quarter_winner_cost_adjusted_simulated_r",
    "follow_inverse_default_off_avoid_class",
    "keep_kill_redesign_implement_decision",
)
REQUIRED_FOLD_FIELDS = (
    "temporal_fold_row_id",
    "input_side_pair_robustness_row_id",
    "fold_id",
    "symbol",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "source_path",
    "overall_winner_side",
    "fold_winner_side",
    "long_cost_adjusted_simulated_r",
    "short_cost_adjusted_simulated_r",
    "winner_cost_adjusted_simulated_r",
    "side_edge_spread_cost_adjusted_r",
    "effective_n",
    "fold_matches_overall_winner",
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
    performance_result = read_json(PERFORMANCE_RESULT)
    side_pair_result = read_json(SIDE_PAIR_RESULT)
    performance_rows = read_jsonl(PERFORMANCE_LEDGER)
    side_pair_rows = read_jsonl(SIDE_PAIR_LEDGER)
    result = read_json(RESULT_PATH)
    temporal_rows = read_jsonl(ROW_LEDGER)
    fold_rows = read_jsonl(FOLD_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    issue_rows = read_jsonl(ISSUE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if performance_result.get("ok") is not True:
        issues.append("input CP216 result is not ok")
    if side_pair_result.get("ok") is not True:
        issues.append("input CP217 result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(performance_rows) != 45220:
        issues.append(f"input performance row count changed from 45220 to {len(performance_rows)}")
    if len(side_pair_rows) != 22610:
        issues.append(f"input side-pair row count changed from 22610 to {len(side_pair_rows)}")
    if counts.get("input_performance_rows") != len(performance_rows):
        issues.append("result input performance count mismatch")
    if counts.get("input_side_pair_rows") != len(side_pair_rows):
        issues.append("result input side-pair count mismatch")
    if counts.get("temporal_robustness_rows") != len(temporal_rows):
        issues.append("temporal row count mismatch")
    if counts.get("temporal_fold_rows") != len(fold_rows):
        issues.append("fold row count mismatch")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if counts.get("issue_rows") != len(issue_rows):
        issues.append("issue row count mismatch")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len(temporal_rows) + len(issue_rows) != len(side_pair_rows):
        issues.append("not every side-pair row produced temporal rows or issue proof")
    if len(fold_rows) != len(temporal_rows) * 4:
        issues.append("fold rows must equal four folds per temporal robustness row")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(temporal_rows):
        issues.append("aggregate row counts do not sum to temporal rows")
    if any(not boundary_ok(row) for row in temporal_rows + fold_rows + aggregate_rows + issue_rows + system_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if any(field not in row for row in temporal_rows for field in REQUIRED_TEMPORAL_FIELDS):
        issues.append("one or more temporal rows lacks a required field")
    if any(field not in row for row in fold_rows for field in REQUIRED_FOLD_FIELDS):
        issues.append("one or more fold rows lacks a required field")
    if len({row.get("temporal_robustness_row_id") for row in temporal_rows}) != len(temporal_rows):
        issues.append("temporal row ids are not unique")
    if len({row.get("temporal_fold_row_id") for row in fold_rows}) != len(fold_rows):
        issues.append("fold row ids are not unique")
    side_ids = {row.get("side_pair_robustness_row_id") for row in side_pair_rows}
    temporal_side_ids = {row.get("input_side_pair_robustness_row_id") for row in temporal_rows}
    issue_side_ids = {row.get("input_side_pair_robustness_row_id") for row in issue_rows}
    if side_ids != temporal_side_ids | issue_side_ids:
        issues.append("temporal and issue rows do not exactly cover side-pair ids")
    fold_counts = Counter(row.get("input_side_pair_robustness_row_id") for row in fold_rows)
    if any(count != 4 for count in fold_counts.values()):
        issues.append("one or more temporal row lacks exactly four fold rows")
    if not all(fold_id in {row.get("fold_id") for row in fold_rows} for fold_id in ("FULL_REPLAY", "EARLY_HALF", "RECENT_HALF", "RECENT_QUARTER")):
        issues.append("one or more required fold ids is absent")
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in temporal_rows)
    fold_decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in fold_rows)
    if not decisions:
        issues.append("decision counts are empty")
    if not any(str(decision).startswith("IMPLEMENT") for decision in decisions):
        issues.append("implementation decision class is absent")
    if not any(str(decision).startswith("REDESIGN") for decision in decisions):
        issues.append("redesign decision class is absent")
    if not any(row.get("overall_winner_side") == "LONG" for row in temporal_rows):
        issues.append("LONG overall winner rows are absent")
    if not any(row.get("overall_winner_side") == "SHORT" for row in temporal_rows):
        issues.append("SHORT overall winner rows are absent")
    if not any(row.get("route_session") == "tokyo_kz" for row in temporal_rows):
        issues.append("tokyo session rows are absent")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "decision_counts": dict(sorted(decisions.items())),
        "fold_decision_counts": dict(sorted(fold_decisions.items())),
        "temporal_rows": len(temporal_rows),
        "fold_rows": len(fold_rows),
        "aggregate_rows": len(aggregate_rows),
        "issue_rows": len(issue_rows),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
