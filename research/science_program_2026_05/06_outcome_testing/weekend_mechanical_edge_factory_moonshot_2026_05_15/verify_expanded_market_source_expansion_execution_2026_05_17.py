#!/usr/bin/env python3
"""Verify expanded-market source-expansion execution checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPAIR_IMPLEMENTATION_ACCEPTANCE_EXECUTION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_EXECUTION"

INPUT_EVIDENCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_EVIDENCE_EXECUTION_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"
SOURCE_GAP_PROOF_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_GAP_PROOF_LEDGER_2026-05-17.jsonl"
INPUT_CONSUMPTION_LEDGER = ROUTE_DIR / f"{PREFIX}_INPUT_CONSUMPTION_LEDGER_2026-05-17.jsonl"
DISCOVERED_SOURCE_LEDGER = ROUTE_DIR / f"{PREFIX}_DISCOVERED_OHLC_SOURCE_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_source_expansion_execution.py",
    ROUTE_DIR / "build_expanded_market_source_expansion_execution_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    EXECUTION_LEDGER,
    SOURCE_GAP_PROOF_LEDGER,
    INPUT_CONSUMPTION_LEDGER,
    DISCOVERED_SOURCE_LEDGER,
    AGGREGATE_LEDGER,
    ISSUE_LEDGER,
    SYSTEM_LEDGER,
    SUMMARY_PATH,
]

REQUIRED_EXECUTION_FIELDS = (
    "expanded_market_source_expansion_execution_row_id",
    "input_acceptance_execution_evidence_row_id",
    "source_expansion_input_source_path",
    "source_expansion_input_source_file_sha256",
    "source_expansion_candidate_source_path",
    "source_expansion_candidate_source_file_sha256",
    "symbol_family",
    "symbol",
    "source_symbol",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "side",
    "score_status",
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
    "target_first_count",
    "stop_first_count",
    "neither_count",
    "ambiguous_count",
    "effective_n",
    "duplicate_row_count",
    "effective_n_after_duplicate_collapse",
    "concentration_top_month_share",
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


def target_input_ids() -> set[str]:
    ids: set[str] = set()
    for row in iter_jsonl(INPUT_EVIDENCE_LEDGER):
        if (
            row.get("evidence_preservation_class") == "source-expansion-acquisition-proof"
            and row.get("source_repair_reachability_class") == "source-expansion-new-source-required"
        ):
            ids.add(
                str(
                    row.get(
                        "expanded_market_repair_implementation_acceptance_evidence_execution_row_id"
                    )
                    or ""
                )
            )
    return ids


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    counts = result.get("counts") or {}
    input_ids = target_input_ids()

    execution_input_counts: Counter[str] = Counter()
    execution_ids: set[str] = set()
    execution_count = 0
    scored_count = 0
    noncomputable_count = 0
    decision_counts: Counter[str] = Counter()
    for row in iter_jsonl(EXECUTION_LEDGER):
        execution_count += 1
        execution_ids.add(str(row.get("expanded_market_source_expansion_execution_row_id") or ""))
        input_id = str(row.get("input_acceptance_execution_evidence_row_id") or "")
        execution_input_counts[input_id] += 1
        decision_counts[row.get("keep_kill_redesign_implement_decision")] += 1
        if not boundary_ok(row):
            issues.append("one or more execution rows failed branch-local boundary checks")
            break
        if any(field not in row for field in REQUIRED_EXECUTION_FIELDS):
            issues.append("one or more execution rows lacks a required field")
            break
        if row.get("source_expansion_candidate_source_path") == row.get("source_expansion_input_source_path"):
            issues.append("one or more execution rows uses the original source as alternate source")
            break
        if row.get("score_status") == "EXPANDED_MARKET_PROXY_R_SCORED":
            scored_count += 1
            if row.get("cost_adjusted_simulated_r") is None:
                issues.append("one or more scored execution rows lacks cost-adjusted simulated R")
                break
            if row.get("missing_simulated_fields"):
                issues.append("one or more scored execution rows still reports missing simulated fields")
                break
        else:
            noncomputable_count += 1
            if not row.get("missing_simulated_fields"):
                issues.append("one or more noncomputable execution rows lacks missing simulated fields")
                break

    gap_input_counts: Counter[str] = Counter()
    gap_ids: set[str] = set()
    gap_count = 0
    for row in iter_jsonl(SOURCE_GAP_PROOF_LEDGER):
        gap_count += 1
        gap_ids.add(str(row.get("expanded_market_source_expansion_gap_row_id") or ""))
        input_id = str(row.get("input_acceptance_execution_evidence_row_id") or "")
        gap_input_counts[input_id] += 1
        decision_counts[row.get("keep_kill_redesign_implement_decision")] += 1
        if not boundary_ok(row):
            issues.append("one or more source gap rows failed branch-local boundary checks")
            break
        if row.get("missing_simulated_fields") != ["additional_replay_source_path_hash_for_scope"]:
            issues.append("one or more source gap rows lacks exact missing simulated field proof")
            break
        if row.get("source_expansion_gap_status") != "NO_ALTERNATE_LOCAL_OHLC_SOURCE_FOR_SYMBOL_TIMEFRAME":
            issues.append("one or more source gap rows has unexpected gap status")
            break

    consumption_input_ids: set[str] = set()
    consumption_count = 0
    for row in iter_jsonl(INPUT_CONSUMPTION_LEDGER):
        consumption_count += 1
        input_id = str(row.get("input_acceptance_execution_evidence_row_id") or "")
        consumption_input_ids.add(input_id)
        execution_rows = int(row.get("execution_rows_generated") or 0)
        gap_rows = int(row.get("source_gap_rows_generated") or 0)
        scored_rows = int(row.get("execution_rows_with_simulated_r") or 0)
        if not boundary_ok(row):
            issues.append("one or more input consumption rows failed branch-local boundary checks")
            break
        if execution_rows + gap_rows < 1:
            issues.append("one or more input rows generated neither execution nor gap proof")
            break
        if execution_rows != execution_input_counts.get(input_id, 0):
            issues.append("input consumption execution count does not match execution ledger")
            break
        if gap_rows != gap_input_counts.get(input_id, 0):
            issues.append("input consumption gap count does not match gap ledger")
            break
        if scored_rows > execution_rows:
            issues.append("input consumption scored rows exceed execution rows")
            break

    discovered_count = 0
    for row in iter_jsonl(DISCOVERED_SOURCE_LEDGER):
        discovered_count += 1
        if not boundary_ok(row):
            issues.append("one or more discovered source rows failed branch-local boundary checks")
            break

    aggregate_rows = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(input_ids) != 3348:
        issues.append(f"target source-expansion input count changed from 3348 to {len(input_ids)}")
    if counts.get("input_source_expansion_rows") != len(input_ids):
        issues.append("result input source-expansion count mismatch")
    if consumption_count != len(input_ids) or consumption_input_ids != input_ids:
        issues.append("input consumption ledger does not consume every target input row exactly once")
    if set(execution_input_counts) | set(gap_input_counts) != input_ids:
        issues.append("execution/gap ledgers do not cover every target input row")
    if len(execution_ids) != execution_count:
        issues.append("execution row ids are not unique")
    if len(gap_ids) != gap_count:
        issues.append("source gap row ids are not unique")
    if counts.get("source_expansion_execution_rows") != execution_count:
        issues.append("execution row count mismatch")
    if counts.get("execution_rows_with_simulated_r") != scored_count:
        issues.append("scored execution row count mismatch")
    if counts.get("noncomputable_execution_rows") != noncomputable_count:
        issues.append("noncomputable execution row count mismatch")
    if counts.get("source_gap_proof_rows") != gap_count:
        issues.append("source gap proof count mismatch")
    if counts.get("input_consumption_rows") != consumption_count:
        issues.append("input consumption count mismatch")
    if counts.get("discovered_ohlc_source_rows") != discovered_count or discovered_count <= 0:
        issues.append("discovered source count mismatch or zero")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != execution_count + gap_count:
        issues.append("aggregate row counts do not sum to execution plus gap rows")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    if len(system_rows) != 1 or counts.get("system_rows") != 1:
        issues.append("system ledger must contain one row")
    if counts.get("decision_counts") != dict(sorted(decision_counts.items())):
        issues.append("decision count mismatch")
    if scored_count <= 0:
        issues.append("source-expansion execution produced no simulated-R rows")
    if gap_count <= 0:
        issues.append("source-expansion execution produced no source-gap proof rows")
    if any(not boundary_ok(row) for row in aggregate_rows + issue_rows + system_rows + [result]):
        issues.append("one or more aggregate/system/result rows failed branch-local boundary checks")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": {
            "input_source_expansion_rows": len(input_ids),
            "source_expansion_execution_rows": execution_count,
            "execution_rows_with_simulated_r": scored_count,
            "source_gap_proof_rows": gap_count,
            "input_consumption_rows": consumption_count,
            "discovered_ohlc_source_rows": discovered_count,
            "aggregate_rows": len(aggregate_rows),
            "issue_rows": len(issue_rows),
        },
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
