#!/usr/bin/env python3
"""Verify expanded-market source-repair reachability checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_REPAIR_REACH"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_ACTION_CLASS_PERF"

INPUT_ROW_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_source_repair_reachability.py",
    ROUTE_DIR / "build_expanded_market_source_repair_reachability_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, ROW_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]
OBSERVED_FIELDS = (
    "observed_gross_simulated_r",
    "observed_cost_adjusted_simulated_r",
    "observed_stress_simulated_r",
    "observed_deconcentrated_cost_adjusted_simulated_r",
    "observed_deconcentrated_stress_simulated_r",
)


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
    counts = result.get("counts") or {}
    input_ids: set[str] = set()
    input_count = 0
    for row in iter_jsonl(INPUT_ROW_LEDGER):
        input_count += 1
        input_ids.add(str(row.get("expanded_market_action_class_performance_row_id") or ""))

    row_count = 0
    output_ids: set[str] = set()
    reachability_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    reachable_rows = 0
    missing_rows = 0
    source_repair_rows = 0
    source_repair_unscored_alternate_rows = 0
    for row in iter_jsonl(ROW_LEDGER):
        row_count += 1
        output_ids.add(str(row.get("input_action_class_performance_row_id") or ""))
        reachability = str(row.get("source_repair_reachability_class") or "")
        action_class = str(row.get("action_class") or "")
        reachability_counts[reachability] += 1
        action_counts[action_class] += 1
        decision_counts[row.get("keep_kill_redesign_implement_decision")] += 1
        if row.get("repair_missing_fields"):
            missing_rows += 1
        else:
            reachable_rows += 1
        if action_class == "redesign-source-repair":
            source_repair_rows += 1
            if reachability == "source-repair-alternate-source-unscored":
                source_repair_unscored_alternate_rows += 1
        if not boundary_ok(row):
            issues.append("one or more reachability rows failed branch-local boundary checks")
            break
        if not row.get("source_path") or not row.get("source_file_sha256"):
            issues.append("one or more reachability rows lacks source path/hash")
            break
        if any(row.get(field) in (None, "") for field in OBSERVED_FIELDS):
            issues.append("one or more reachability rows lacks observed simulated R fields")
            break
        if not row.get("repair_missing_fields") and row.get("repair_action_cost_adjusted_simulated_r") is None:
            issues.append("one or more reachable rows lacks repair action R")
            break
        if reachability == "source-expansion-new-source-required" and row.get("alternate_source_path_count") != 0:
            issues.append("source-expansion-new-source rows must have zero alternate source paths")
            break
    aggregates = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if input_count != 46120:
        issues.append(f"input action row count changed from 46120 to {input_count}")
    if row_count != input_count or row_count != counts.get("source_repair_reachability_rows"):
        issues.append("reachability rows do not cover every action-class input row")
    if input_ids != output_ids:
        issues.append("input action-class ids are not exactly preserved")
    if counts.get("input_action_class_rows") != input_count:
        issues.append("input count mismatch")
    if counts.get("aggregate_rows") != len(aggregates):
        issues.append("aggregate count mismatch")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    if len(system_rows) != 1 or counts.get("system_rows") != 1:
        issues.append("system ledger must contain one row")
    if counts.get("reachable_repair_rows") != reachable_rows:
        issues.append("reachable row count mismatch")
    if counts.get("missing_repair_rows") != missing_rows:
        issues.append("missing row count mismatch")
    if counts.get("reachability_class_counts") != dict(sorted(reachability_counts.items())):
        issues.append("reachability class count mismatch")
    if counts.get("decision_counts") != dict(sorted(decision_counts.items())):
        issues.append("decision count mismatch")
    expected_action_counts = {
        "avoid": 9688,
        "default-off": 1715,
        "follow": 5389,
        "redesign-source-expansion": 3348,
        "redesign-source-repair": 6046,
        "redesign-weak-edge": 19934,
    }
    if action_counts != expected_action_counts:
        issues.append(f"action class counts mismatch: {dict(action_counts)!r}")
    if source_repair_rows != 6046:
        issues.append("source-repair row count must remain 6046")
    if source_repair_unscored_alternate_rows != source_repair_rows:
        issues.append("every source-repair row should have alternate source paths requiring alternate-source scoring")
    if any(not boundary_ok(row) for row in aggregates + issue_rows + system_rows + [result]):
        issues.append("one or more non-row outputs failed branch-local boundary checks")
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    print(
        json.dumps(
            {
                "ok": not issues,
                "issues": issues,
                "counts": {
                    "source_repair_reachability_rows": row_count,
                    "aggregate_rows": len(aggregates),
                    "reachable_repair_rows": reachable_rows,
                    "missing_repair_rows": missing_rows,
                    "issue_rows": len(issue_rows),
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
