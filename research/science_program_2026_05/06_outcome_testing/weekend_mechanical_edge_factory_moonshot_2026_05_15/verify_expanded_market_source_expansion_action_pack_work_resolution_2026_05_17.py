#!/usr/bin/env python3
"""Verify expanded-market source-expansion action pack work resolution."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PACK_EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_WORK_RESOLUTION"

PACK_EXEC_RESULT = ROUTE_DIR / f"{PACK_EXEC_PREFIX}_RESULT_2026-05-17.json"
WORK_EXECUTION_LEDGER = ROUTE_DIR / f"{PACK_EXEC_PREFIX}_WORK_EXECUTION_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_source_expansion_action_pack_work_resolution.py",
    ROUTE_DIR / "build_expanded_market_source_expansion_action_pack_work_resolution_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, ROW_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]


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


def main() -> None:
    issues: list[str] = []
    pack_exec_result = read_json(PACK_EXEC_RESULT)
    result = read_json(RESULT_PATH)
    counts = result.get("counts") or {}
    input_ids = {
        str(row.get("expanded_market_source_expansion_action_pack_work_execution_row_id") or "")
        for row in iter_jsonl(WORK_EXECUTION_LEDGER)
    }
    row_ids: set[str] = set()
    covered_input_ids: set[str] = set()
    resolution_rows = []
    status_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    rows_with_r = 0
    source_exists = 0
    hash_matches = 0
    for row in iter_jsonl(ROW_LEDGER):
        resolution_rows.append(row)
        row_ids.add(str(row.get("expanded_market_source_expansion_action_pack_work_resolution_row_id") or ""))
        covered_input_ids.add(str(row.get("input_action_pack_work_execution_row_id") or ""))
        status_counts[row.get("work_resolution_status")] += 1
        decision_counts[row.get("keep_kill_redesign_implement_decision")] += 1
        if row.get("cost_adjusted_simulated_r") is not None:
            rows_with_r += 1
        if row.get("current_source_path_exists") is True:
            source_exists += 1
        if row.get("current_source_file_hash_matches_row") is True:
            hash_matches += 1
        if not row.get("missing_work_fields"):
            issues.append("one or more work-resolution rows lacks missing work fields")
            break
        if not row.get("branch_local_work_resolution_expression_sha256"):
            issues.append("one or more work-resolution rows lacks expression hash")
            break
        if not boundary_ok(row):
            issues.append("one or more work-resolution rows failed branch-local boundary checks")
            break

    aggregate_rows = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))
    if pack_exec_result.get("ok") is not True:
        issues.append("input pack-execution result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if covered_input_ids != input_ids:
        issues.append("work-resolution rows do not consume every work-execution row exactly once")
    if len(row_ids) != len(resolution_rows):
        issues.append("work-resolution row ids are not unique")
    if counts.get("input_work_execution_rows") != len(input_ids):
        issues.append("input work-execution row count mismatch")
    if counts.get("work_resolution_rows") != len(resolution_rows):
        issues.append("work-resolution row count mismatch")
    if counts.get("rows_with_simulated_r") != rows_with_r:
        issues.append("rows-with-simulated-R count mismatch")
    if counts.get("current_source_path_exists_rows") != source_exists:
        issues.append("source path exists count mismatch")
    if counts.get("current_source_file_hash_match_rows") != hash_matches:
        issues.append("source hash match count mismatch")
    if counts.get("resolution_status_counts") != dict(sorted(status_counts.items())):
        issues.append("resolution status count mismatch")
    if counts.get("decision_counts") != dict(sorted(decision_counts.items())):
        issues.append("decision count mismatch")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(resolution_rows):
        issues.append("aggregate row counts do not sum to resolution rows")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    if len(system_rows) != 1 or counts.get("system_rows") != 1:
        issues.append("system ledger must contain one row")
    if not any(str(status).endswith("RULE_REDESIGN_NUMERIC_AVAILABLE") for status in status_counts):
        issues.append("rule-redesign numeric resolution status is absent")
    if not any(str(status).endswith("REPLAY_IMPLEMENTATION_REQUIRED") for status in status_counts):
        issues.append("replay-implementation resolution status is absent")
    if not any(str(status).endswith("SOURCE_ACQUISITION_REQUIRED") for status in status_counts):
        issues.append("source-acquisition resolution status is absent")
    if any(not boundary_ok(row) for row in aggregate_rows + issue_rows + system_rows + [result]):
        issues.append("one or more aggregate/system/result rows failed branch-local boundary checks")
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": {
            "work_resolution_rows": len(resolution_rows),
            "aggregate_rows": len(aggregate_rows),
            "issue_rows": len(issue_rows),
            "rows_with_simulated_r": rows_with_r,
        },
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
