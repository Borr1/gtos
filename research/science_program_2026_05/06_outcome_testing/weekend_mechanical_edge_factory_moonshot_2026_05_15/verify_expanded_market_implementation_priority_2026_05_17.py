#!/usr/bin/env python3
"""Verify expanded-market implementation-priority checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_IMPL_PRIORITY"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_ALT_SOURCE_SCORE"

INPUT_ROW_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_implementation_priority.py",
    ROUTE_DIR / "build_expanded_market_implementation_priority_2026_05_17.py",
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
        input_ids.add(str(row.get("expanded_market_alternate_source_scoring_row_id") or ""))

    output_ids: set[str] = set()
    row_count = 0
    class_counts: Counter[str] = Counter()
    tier_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    implementation_candidates = 0
    preserved_rows = 0
    for row in iter_jsonl(ROW_LEDGER):
        row_count += 1
        output_ids.add(str(row.get("input_alternate_source_scoring_row_id") or ""))
        row_class = str(row.get("implementation_priority_class") or "")
        class_counts[row_class] += 1
        tier_counts[row.get("implementation_priority_tier")] += 1
        decision_counts[row.get("keep_kill_redesign_implement_decision")] += 1
        if row_class == "implementation-priority-positive-alternate-source-repair":
            implementation_candidates += 1
        else:
            preserved_rows += 1
        if not boundary_ok(row):
            issues.append("one or more implementation-priority rows failed branch-local boundary checks")
            break
        if not row.get("source_path") or not row.get("source_file_sha256"):
            issues.append("one or more implementation-priority rows lacks source path/hash")
            break
        if any(row.get(field) in (None, "") for field in OBSERVED_FIELDS):
            issues.append("one or more implementation-priority rows lacks observed simulated R fields")
            break
        if row_class == "implementation-priority-positive-alternate-source-repair":
            if row.get("implementation_priority_score") is None:
                issues.append("positive repair priority row lacks priority score")
                break
            if not (float(row.get("alternate_source_proxy_cost_adjusted_simulated_r")) > 0.05):
                issues.append("positive repair priority row does not exceed source repair threshold")
                break
            if row.get("implementation_missing_fields"):
                issues.append("positive repair priority row must not carry missing fields")
                break
        if row_class == "source-expansion-acquisition-proof" and row.get("implementation_missing_fields") != [
            "additional_replay_source_path_hash_for_scope"
        ]:
            issues.append("source-expansion proof rows must carry source-path/hash missing field")
            break
    aggregates = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))

    expected_classes = {
        "carry-forward-existing-scored-action": 16792,
        "implementation-priority-positive-alternate-source-repair": 1734,
        "kill-nonpositive-alternate-source-repair": 3335,
        "redesign-weak-positive-alternate-source-repair": 977,
        "source-expansion-acquisition-proof": 3348,
        "weak-edge-signal-geometry-proof": 19934,
    }
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if input_count != 46120 or row_count != 46120:
        issues.append("input and output row counts must remain 46120")
    if input_ids != output_ids:
        issues.append("input alternate-source ids are not exactly preserved")
    if counts.get("input_alternate_source_scoring_rows") != input_count:
        issues.append("input count mismatch")
    if counts.get("implementation_priority_rows") != row_count:
        issues.append("output count mismatch")
    if counts.get("priority_class_counts") != expected_classes:
        issues.append(f"priority class counts mismatch: {counts.get('priority_class_counts')!r}")
    if counts.get("implementation_candidate_rows") != implementation_candidates or implementation_candidates != 1734:
        issues.append("implementation candidate count mismatch")
    if counts.get("preserved_evidence_rows") != preserved_rows or preserved_rows != 44386:
        issues.append("preserved evidence count mismatch")
    if counts.get("priority_tier_counts") != dict(sorted(tier_counts.items())):
        issues.append("priority tier count mismatch")
    if counts.get("decision_counts") != dict(sorted(decision_counts.items())):
        issues.append("decision count mismatch")
    if counts.get("aggregate_rows") != len(aggregates):
        issues.append("aggregate count mismatch")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    if len(system_rows) != 1 or counts.get("system_rows") != 1:
        issues.append("system ledger must contain one row")
    if any(not boundary_ok(row) for row in aggregates + issue_rows + system_rows + [result]):
        issues.append("one or more non-row outputs failed branch-local boundary checks")
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    print(
        json.dumps(
            {
                "ok": not issues,
                "issues": issues,
                "counts": {
                    "implementation_priority_rows": row_count,
                    "implementation_candidate_rows": implementation_candidates,
                    "preserved_evidence_rows": preserved_rows,
                    "aggregate_rows": len(aggregates),
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
