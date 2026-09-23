#!/usr/bin/env python3
"""Verify expanded-market implementation-candidate execution checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_IMPL_CANDIDATE_EXECUTION"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_IMPL_CANDIDATES"
PRIORITY_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_IMPL_PRIORITY"

INPUT_CANDIDATE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_CANDIDATE_LEDGER_2026-05-17.jsonl"
INPUT_EVIDENCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
INPUT_PRIORITY_LEDGER = ROUTE_DIR / f"{PRIORITY_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"
EVIDENCE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_impl_candidate_execution.py",
    ROUTE_DIR / "build_expanded_market_impl_candidate_execution_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    EXECUTION_LEDGER,
    EVIDENCE_EXECUTION_LEDGER,
    CONTROL_LEDGER,
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

    priority_ids: set[str] = set()
    for row in iter_jsonl(INPUT_PRIORITY_LEDGER):
        priority_ids.add(str(row.get("expanded_market_implementation_priority_row_id") or ""))

    candidate_ids: set[str] = set()
    for row in iter_jsonl(INPUT_CANDIDATE_LEDGER):
        candidate_ids.add(str(row.get("input_implementation_priority_row_id") or ""))

    evidence_ids: set[str] = set()
    input_evidence_class_counts: Counter[str] = Counter()
    for row in iter_jsonl(INPUT_EVIDENCE_LEDGER):
        evidence_ids.add(str(row.get("input_implementation_priority_row_id") or ""))
        input_evidence_class_counts[row.get("evidence_preservation_class")] += 1

    execution_ids: set[str] = set()
    execution_count = 0
    execution_pass_count = 0
    execution_decisions: Counter[str] = Counter()
    for row in iter_jsonl(EXECUTION_LEDGER):
        execution_count += 1
        execution_ids.add(str(row.get("input_implementation_priority_row_id") or ""))
        execution_decisions[row.get("keep_kill_redesign_implement_decision")] += 1
        if not boundary_ok(row):
            issues.append("one or more candidate execution rows failed branch-local boundary checks")
            break
        if row.get("candidate_execution_status") == "EXPANDED_MARKET_IMPL_CANDIDATE_EXECUTION_PASS":
            execution_pass_count += 1
        else:
            issues.append("one or more candidate executions did not pass")
            break
        if row.get("candidate_scope_match") is not True or row.get("held_priority_row_found") is not True:
            issues.append("one or more candidate executions lacks held-row match proof")
            break
        if row.get("execution_cost_adjusted_simulated_r") in (None, ""):
            issues.append("one or more candidate executions lacks simulated R")
            break

    evidence_execution_ids: set[str] = set()
    evidence_execution_count = 0
    evidence_class_counts: Counter[str] = Counter()
    evidence_decisions: Counter[str] = Counter()
    for row in iter_jsonl(EVIDENCE_EXECUTION_LEDGER):
        evidence_execution_count += 1
        evidence_execution_ids.add(str(row.get("input_implementation_priority_row_id") or ""))
        evidence_class_counts[row.get("evidence_preservation_class")] += 1
        evidence_decisions[row.get("keep_kill_redesign_implement_decision")] += 1
        if not boundary_ok(row):
            issues.append("one or more evidence execution rows failed branch-local boundary checks")
            break
        if row.get("evidence_execution_status") != "PRESERVED_NONCANDIDATE_PRIORITY_EVIDENCE_EXECUTION":
            issues.append("one or more evidence execution rows lacks preservation status")
            break

    control_ids: set[str] = set()
    control_count = 0
    control_pass_count = 0
    control_decisions: Counter[str] = Counter()
    for row in iter_jsonl(CONTROL_LEDGER):
        control_count += 1
        control_ids.add(str(row.get("input_implementation_priority_row_id") or ""))
        control_decisions[row.get("keep_kill_redesign_implement_decision")] += 1
        if not boundary_ok(row):
            issues.append("one or more control rows failed branch-local boundary checks")
            break
        if row.get("control_status") == "EXPANDED_MARKET_IMPL_CANDIDATE_CONTROL_PASS":
            control_pass_count += 1
        else:
            issues.append("one or more candidate controls did not pass")
            break
        if row.get("noncandidate_scope_leakage_count") != 0:
            issues.append("candidate controls must report zero noncandidate leakage")
            break

    aggregates = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))
    decision_counts = dict(sorted((execution_decisions + evidence_decisions + control_decisions).items()))

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(priority_ids) != 46120:
        issues.append("priority input count must be 46120")
    if len(candidate_ids) != 1734 or len(evidence_ids) != 44386:
        issues.append("input candidate/evidence counts mismatch")
    if candidate_ids | evidence_ids != priority_ids:
        issues.append("candidate and evidence inputs do not preserve every priority row")
    if candidate_ids & evidence_ids:
        issues.append("candidate and evidence inputs overlap")
    if execution_count != 1734 or execution_pass_count != 1734:
        issues.append("candidate execution count mismatch")
    if execution_ids != candidate_ids:
        issues.append("candidate execution ids do not match candidate inputs")
    if evidence_execution_count != 44386:
        issues.append("evidence execution count mismatch")
    if evidence_execution_ids != evidence_ids:
        issues.append("evidence execution ids do not match evidence inputs")
    if evidence_class_counts != input_evidence_class_counts:
        issues.append("evidence class counts were not preserved")
    if control_count != 1734 or control_pass_count != 1734:
        issues.append("control count mismatch")
    if control_ids != candidate_ids:
        issues.append("control ids do not match candidate inputs")
    if counts.get("input_candidate_rows") != len(candidate_ids):
        issues.append("result input candidate count mismatch")
    if counts.get("input_evidence_rows") != len(evidence_ids):
        issues.append("result input evidence count mismatch")
    if counts.get("candidate_execution_rows") != execution_count:
        issues.append("result execution count mismatch")
    if counts.get("candidate_execution_pass_rows") != execution_pass_count:
        issues.append("result execution pass count mismatch")
    if counts.get("evidence_execution_rows") != evidence_execution_count:
        issues.append("result evidence count mismatch")
    if counts.get("control_rows") != control_count or counts.get("control_pass_rows") != control_pass_count:
        issues.append("result control count mismatch")
    if counts.get("decision_counts") != decision_counts:
        issues.append("result decision count mismatch")
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
                    "candidate_execution_rows": execution_count,
                    "evidence_execution_rows": evidence_execution_count,
                    "control_rows": control_count,
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
