#!/usr/bin/env python3
"""Verify expanded-market implementation-candidates checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_IMPL_CANDIDATES"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_IMPL_PRIORITY"

INPUT_ROW_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_CANDIDATE_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_impl_candidates.py",
    ROUTE_DIR / "build_expanded_market_impl_candidates_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    CANDIDATE_LEDGER,
    EVIDENCE_LEDGER,
    SELF_TEST_LEDGER,
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

    input_ids: set[str] = set()
    input_candidate_ids: set[str] = set()
    input_evidence_ids: set[str] = set()
    input_class_counts: Counter[str] = Counter()
    input_tier_counts: Counter[str] = Counter()
    input_count = 0
    for row in iter_jsonl(INPUT_ROW_LEDGER):
        input_count += 1
        row_id = str(row.get("expanded_market_implementation_priority_row_id") or "")
        input_ids.add(row_id)
        row_class = str(row.get("implementation_priority_class") or "")
        input_class_counts[row_class] += 1
        input_tier_counts[row.get("implementation_priority_tier")] += 1
        if row_class == "implementation-priority-positive-alternate-source-repair":
            input_candidate_ids.add(row_id)
        else:
            input_evidence_ids.add(row_id)

    candidate_input_ids: set[str] = set()
    candidate_count = 0
    candidate_class_counts: Counter[str] = Counter()
    candidate_decisions: Counter[str] = Counter()
    candidate_scope_hashes: set[str] = set()
    for row in iter_jsonl(CANDIDATE_LEDGER):
        candidate_count += 1
        candidate_input_ids.add(str(row.get("input_implementation_priority_row_id") or ""))
        candidate_class_counts[row.get("implementation_priority_class")] += 1
        candidate_decisions[row.get("keep_kill_redesign_implement_decision")] += 1
        candidate_scope_hashes.add(str(row.get("branch_local_candidate_scope_sha256") or ""))
        if not boundary_ok(row):
            issues.append("one or more candidate rows failed branch-local boundary checks")
            break
        if row.get("implementation_priority_class") != "implementation-priority-positive-alternate-source-repair":
            issues.append("candidate ledger contains a non-positive-repair row")
            break
        if not row.get("source_path") or not row.get("source_file_sha256"):
            issues.append("one or more candidate rows lacks source path/hash")
            break
        if row.get("candidate_cost_adjusted_simulated_r") in (None, ""):
            issues.append("one or more candidate rows lacks candidate simulated R")
            break
        if not row.get("branch_local_candidate_scope_sha256") or not row.get("branch_local_candidate_scope"):
            issues.append("one or more candidate rows lacks branch-local scope")
            break

    evidence_input_ids: set[str] = set()
    evidence_count = 0
    evidence_class_counts: Counter[str] = Counter()
    evidence_decisions: Counter[str] = Counter()
    for row in iter_jsonl(EVIDENCE_LEDGER):
        evidence_count += 1
        evidence_input_ids.add(str(row.get("input_implementation_priority_row_id") or ""))
        evidence_class_counts[row.get("evidence_preservation_class")] += 1
        evidence_decisions[row.get("keep_kill_redesign_implement_decision")] += 1
        if not boundary_ok(row):
            issues.append("one or more evidence rows failed branch-local boundary checks")
            break
        if row.get("evidence_preservation_class") == "implementation-priority-positive-alternate-source-repair":
            issues.append("evidence ledger contains a positive-repair candidate row")
            break
        if not row.get("source_path") or not row.get("source_file_sha256"):
            issues.append("one or more evidence rows lacks source path/hash")
            break

    self_test_count = 0
    self_test_pass_count = 0
    self_test_candidate_ids: set[str] = set()
    for row in iter_jsonl(SELF_TEST_LEDGER):
        self_test_count += 1
        self_test_candidate_ids.add(str(row.get("input_implementation_priority_row_id") or ""))
        if not boundary_ok(row):
            issues.append("one or more self-test rows failed branch-local boundary checks")
            break
        if row.get("self_test_status") == "EXPANDED_MARKET_IMPL_CANDIDATE_SELF_TEST_PASS":
            self_test_pass_count += 1
        else:
            issues.append("one or more candidate self-tests failed")
            break
        if not (
            row.get("positive_scope_match") is True
            and row.get("negative_side_mismatch_rejected") is True
            and row.get("negative_source_hash_mismatch_rejected") is True
            and row.get("negative_threshold_underflow_rejected") is True
        ):
            issues.append("one or more self-tests lacks positive/negative control proof")
            break

    aggregates = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))
    decision_counts = dict(sorted((candidate_decisions + evidence_decisions).items()))

    expected_input_classes = {
        "carry-forward-existing-scored-action": 16792,
        "implementation-priority-positive-alternate-source-repair": 1734,
        "kill-nonpositive-alternate-source-repair": 3335,
        "redesign-weak-positive-alternate-source-repair": 977,
        "source-expansion-acquisition-proof": 3348,
        "weak-edge-signal-geometry-proof": 19934,
    }
    expected_evidence_classes = {
        key: value
        for key, value in expected_input_classes.items()
        if key != "implementation-priority-positive-alternate-source-repair"
    }
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if input_count != 46120:
        issues.append("input row count must be 46120")
    if candidate_count != 1734 or evidence_count != 44386:
        issues.append("candidate/evidence row counts mismatch")
    if input_class_counts != expected_input_classes:
        issues.append(f"input class counts mismatch: {dict(input_class_counts)!r}")
    if candidate_input_ids != input_candidate_ids:
        issues.append("candidate input ids do not exactly match positive repair input ids")
    if evidence_input_ids != input_evidence_ids:
        issues.append("evidence input ids do not exactly match noncandidate input ids")
    if candidate_input_ids & evidence_input_ids:
        issues.append("candidate and evidence ledgers overlap on input ids")
    if candidate_input_ids | evidence_input_ids != input_ids:
        issues.append("candidate and evidence ledgers do not preserve every input id")
    if len(candidate_scope_hashes) != candidate_count:
        issues.append("candidate scope hashes must be row-unique")
    if self_test_count != candidate_count or self_test_pass_count != candidate_count:
        issues.append("self-test counts must equal candidate count and all pass")
    if self_test_candidate_ids != candidate_input_ids:
        issues.append("self-test candidate ids do not match candidate ledger ids")
    if candidate_class_counts != {"implementation-priority-positive-alternate-source-repair": 1734}:
        issues.append("candidate class counts mismatch")
    if evidence_class_counts != expected_evidence_classes:
        issues.append(f"evidence class counts mismatch: {dict(evidence_class_counts)!r}")
    if counts.get("input_implementation_priority_rows") != input_count:
        issues.append("result input count mismatch")
    if counts.get("implementation_candidate_rows") != candidate_count:
        issues.append("result candidate count mismatch")
    if counts.get("preserved_evidence_rows") != evidence_count:
        issues.append("result evidence count mismatch")
    if counts.get("self_test_rows") != self_test_count:
        issues.append("result self-test count mismatch")
    if counts.get("self_test_pass_rows") != self_test_pass_count:
        issues.append("result self-test pass count mismatch")
    if counts.get("candidate_class_counts") != dict(sorted(candidate_class_counts.items())):
        issues.append("result candidate class counts mismatch")
    if counts.get("evidence_class_counts") != dict(sorted(evidence_class_counts.items())):
        issues.append("result evidence class counts mismatch")
    if counts.get("priority_tier_counts") != dict(sorted(input_tier_counts.items())):
        issues.append("result priority tier counts mismatch")
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
                    "implementation_candidate_rows": candidate_count,
                    "preserved_evidence_rows": evidence_count,
                    "self_test_rows": self_test_count,
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
