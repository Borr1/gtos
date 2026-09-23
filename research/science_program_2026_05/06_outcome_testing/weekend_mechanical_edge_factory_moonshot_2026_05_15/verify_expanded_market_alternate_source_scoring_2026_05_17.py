#!/usr/bin/env python3
"""Verify expanded-market alternate-source scoring checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_ALT_SOURCE_SCORE"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_REPAIR_REACH"

INPUT_ROW_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_alternate_source_scoring.py",
    ROUTE_DIR / "build_expanded_market_alternate_source_scoring_2026_05_17.py",
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
        input_ids.add(str(row.get("expanded_market_source_repair_reachability_row_id") or ""))

    output_ids: set[str] = set()
    row_count = 0
    scoring_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    scored_rows = 0
    missing_rows = 0
    for row in iter_jsonl(ROW_LEDGER):
        row_count += 1
        output_ids.add(str(row.get("input_source_repair_reachability_row_id") or ""))
        score_class = str(row.get("alternate_source_scoring_class") or "")
        scoring_counts[score_class] += 1
        decision_counts[row.get("keep_kill_redesign_implement_decision")] += 1
        score_value = row.get("alternate_source_proxy_cost_adjusted_simulated_r")
        missing_fields = row.get("alternate_source_missing_fields") or []
        if score_value is None:
            missing_rows += 1
        else:
            scored_rows += 1
        if not boundary_ok(row):
            issues.append("one or more scoring rows failed branch-local boundary checks")
            break
        if not row.get("source_path") or not row.get("source_file_sha256"):
            issues.append("one or more scoring rows lacks source path/hash")
            break
        if any(row.get(field) in (None, "") for field in OBSERVED_FIELDS):
            issues.append("one or more scoring rows lacks observed simulated R fields")
            break
        if not missing_fields and score_value is None:
            issues.append("scored alternate-source row lacks proxy R")
            break
        if score_class == "alternate-source-positive-repair" and not (float(score_value) > 0.05):
            issues.append("positive alternate-source rows must exceed threshold")
            break
        if score_class == "alternate-source-weak-positive-repair" and not (0.0 < float(score_value) <= 0.05):
            issues.append("weak-positive alternate-source rows must be in threshold band")
            break
        if score_class == "alternate-source-nonpositive-repair" and not (float(score_value) <= 0.0):
            issues.append("nonpositive alternate-source rows must be nonpositive")
            break
    aggregates = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))

    expected_scoring_counts = {
        "alternate-source-nonpositive-repair": 3335,
        "alternate-source-positive-repair": 1734,
        "alternate-source-weak-positive-repair": 977,
        "scored-action-carried-forward": 16792,
        "source-expansion-new-source-required": 3348,
        "weak-edge-preserved-for-signal-redesign": 19934,
    }
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if input_count != 46120 or row_count != 46120:
        issues.append("input and output row counts must remain 46120")
    if input_ids != output_ids:
        issues.append("input reachability ids are not exactly preserved")
    if counts.get("input_reachability_rows") != input_count:
        issues.append("input count mismatch")
    if counts.get("alternate_source_scoring_rows") != row_count:
        issues.append("output count mismatch")
    if counts.get("scoring_class_counts") != expected_scoring_counts:
        issues.append(f"scoring class counts mismatch: {counts.get('scoring_class_counts')!r}")
    if counts.get("scored_rows") != scored_rows or scored_rows != 22838:
        issues.append("scored row count mismatch")
    if counts.get("missing_rows") != missing_rows or missing_rows != 23282:
        issues.append("missing row count mismatch")
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
                    "alternate_source_scoring_rows": row_count,
                    "aggregate_rows": len(aggregates),
                    "scored_rows": scored_rows,
                    "missing_rows": missing_rows,
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
