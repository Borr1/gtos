#!/usr/bin/env python3
"""Verify expanded-market consensus deconcentration checkpoint."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_CONSENSUS_DECONCENTRATION"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_CONSENSUS_ROBUSTNESS"

INPUT_CONSENSUS_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
DECONCENTRATION_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_consensus_deconcentration.py",
    ROUTE_DIR / "build_expanded_market_consensus_deconcentration_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, DECONCENTRATION_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
REQUIRED_FIELDS = (
    "expanded_market_deconcentration_row_id",
    "input_source_consensus_row_id",
    "symbol_family",
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
    "deconcentrated_effective_n",
    "source_path_deconcentration_weight",
    "raw_top_source_path_effective_n_share",
    "deconcentrated_top_source_path_effective_n_share",
    "deconcentrated_cost_adjusted_simulated_r",
    "deconcentrated_stress_simulated_r",
    "missing_simulated_fields",
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
    input_rows = read_jsonl(INPUT_CONSENSUS_LEDGER)
    decon_rows = read_jsonl(DECONCENTRATION_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    issue_rows = read_jsonl(ISSUE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(input_rows) != 46120:
        issues.append(f"input source-consensus count changed from 46120 to {len(input_rows)}")
    if counts.get("input_source_consensus_rows") != len(input_rows):
        issues.append("input source-consensus count mismatch")
    if counts.get("deconcentration_rows") != len(decon_rows):
        issues.append("deconcentration row count mismatch")
    if len(decon_rows) != len(input_rows):
        issues.append("deconcentration rows must preserve every input source-consensus row")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if counts.get("issue_rows") != len(issue_rows):
        issues.append("issue row count mismatch")
    if len(system_rows) != 1 or counts.get("system_rows") != 1:
        issues.append("system ledger must contain one row")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(decon_rows):
        issues.append("aggregate row counts do not sum to deconcentration rows")
    if len({row.get("expanded_market_deconcentration_row_id") for row in decon_rows}) != len(decon_rows):
        issues.append("deconcentration row ids are not unique")
    if len({row.get("expanded_market_deconcentration_aggregate_row_id") for row in aggregate_rows}) != len(
        aggregate_rows
    ):
        issues.append("aggregate row ids are not unique")
    if any(not boundary_ok(row) for row in decon_rows + aggregate_rows + issue_rows + system_rows + [result]):
        issues.append("one or more rows failed branch-local boundary checks")
    if any(field not in row for row in decon_rows for field in REQUIRED_FIELDS):
        issues.append("one or more deconcentration rows lacks a required field")
    input_ids = {row.get("expanded_market_source_consensus_row_id") for row in input_rows}
    decon_input_ids = {row.get("input_source_consensus_row_id") for row in decon_rows}
    if decon_input_ids != input_ids:
        issues.append("deconcentration rows do not preserve all source-consensus input ids")
    missing_ids = {
        row.get("expanded_market_deconcentration_row_id") for row in decon_rows if row.get("missing_simulated_fields")
    }
    issue_ids = {row.get("input_deconcentration_row_id") for row in issue_rows}
    if missing_ids != issue_ids:
        issues.append("issue rows do not match missing simulated-field deconcentration rows")
    if counts.get("rows_with_simulated_r") != len(decon_rows) - len(issue_rows):
        issues.append("rows_with_simulated_r mismatch")
    if any(not row.get("source_path") or not row.get("source_file_sha256") for row in decon_rows):
        issues.append("one or more deconcentration rows lacks source path/hash")
    if not any(float(row.get("source_path_deconcentration_weight") or 0.0) < 1.0 for row in decon_rows):
        issues.append("no row received a deconcentration weight below one")
    if any(float(row.get("source_path_deconcentration_weight") or 0.0) < 0.0 for row in decon_rows):
        issues.append("negative deconcentration weight found")
    decision_total = sum((counts.get("decision_counts") or {}).values())
    if decision_total != len(decon_rows):
        issues.append("decision counts do not sum to deconcentration row count")
    class_total = sum((counts.get("class_counts") or {}).values())
    if class_total != len(decon_rows):
        issues.append("class counts do not sum to deconcentration row count")
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    print(
        json.dumps(
            {
                "ok": not issues,
                "issues": issues,
                "counts": {
                    "input_source_consensus_rows": len(input_rows),
                    "deconcentration_rows": len(decon_rows),
                    "aggregate_rows": len(aggregate_rows),
                    "issue_rows": len(issue_rows),
                    "rows_with_simulated_r": counts.get("rows_with_simulated_r"),
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
