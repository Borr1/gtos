#!/usr/bin/env python3
"""Verify expanded-market portfolio artifact selection checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
ARTIFACT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_FINAL_BRANCH_ARTIFACTS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_PORTFOLIO_ARTIFACT_SELECTION"

ARTIFACT_RESULT = ROUTE_DIR / f"{ARTIFACT_PREFIX}_RESULT_2026-05-17.json"
ARTIFACT_LEDGER = ROUTE_DIR / f"{ARTIFACT_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
EVIDENCE_EXECUTION_LEDGER = ROUTE_DIR / f"{ARTIFACT_PREFIX}_EVIDENCE_EXECUTION_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SELECTION_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
CONCENTRATION_LEDGER = ROUTE_DIR / f"{PREFIX}_CONCENTRATION_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_portfolio_artifact_selection.py",
    ROUTE_DIR / "build_expanded_market_portfolio_artifact_selection_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, SELECTION_LEDGER, EVIDENCE_LEDGER, CONCENTRATION_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]


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


def as_int(value: Any) -> int:
    if value is None or value == "" or isinstance(value, bool):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def main() -> None:
    issues: list[str] = []
    artifact_result = read_json(ARTIFACT_RESULT)
    artifacts = read_jsonl(ARTIFACT_LEDGER)
    input_evidence = read_jsonl(EVIDENCE_EXECUTION_LEDGER)
    result = read_json(RESULT_PATH)
    selections = read_jsonl(SELECTION_LEDGER)
    evidence = read_jsonl(EVIDENCE_LEDGER)
    concentration = read_jsonl(CONCENTRATION_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if artifact_result.get("ok") is not True:
        issues.append("input CP226 result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(artifacts) != 1748:
        issues.append(f"input artifact count changed from 1748 to {len(artifacts)}")
    if len(input_evidence) != 9266:
        issues.append(f"input evidence execution count changed from 9266 to {len(input_evidence)}")
    if counts.get("portfolio_artifact_selection_rows") != len(selections):
        issues.append("selection row count mismatch")
    if counts.get("portfolio_artifact_selection_evidence_rows") != len(evidence):
        issues.append("evidence row count mismatch")
    if counts.get("portfolio_concentration_rows") != len(concentration):
        issues.append("concentration row count mismatch")
    if counts.get("aggregate_rows") != len(aggregates):
        issues.append("aggregate row count mismatch")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len(selections) != len(artifacts):
        issues.append("selection rows must match artifact rows")
    if len(evidence) != len(input_evidence):
        issues.append("selection evidence rows must match input evidence rows")
    if sum(as_int(row.get("evidence_execution_rows")) for row in selections) != len(evidence):
        issues.append("selection evidence counts do not sum to evidence rows")
    if sum(as_int(row.get("row_count")) for row in aggregates) != len(selections):
        issues.append("aggregate row counts do not sum to selection rows")
    if any(not boundary_ok(row) for row in selections + evidence + concentration + aggregates + system_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if len({row.get("portfolio_artifact_selection_row_id") for row in selections}) != len(selections):
        issues.append("selection row ids are not unique")
    if len({row.get("portfolio_artifact_selection_evidence_row_id") for row in evidence}) != len(evidence):
        issues.append("evidence row ids are not unique")
    if len({row.get("portfolio_concentration_row_id") for row in concentration}) != len(concentration):
        issues.append("concentration row ids are not unique")

    input_artifact_ids = [row.get("final_branch_artifact_row_id") for row in artifacts]
    output_artifact_ids = [row.get("input_final_branch_artifact_row_id") for row in selections]
    if Counter(input_artifact_ids) != Counter(output_artifact_ids):
        issues.append("input artifact ids are not covered exactly once")
    input_evidence_ids = [row.get("final_branch_artifact_evidence_execution_row_id") for row in input_evidence]
    output_evidence_ids = [row.get("input_final_branch_artifact_evidence_execution_row_id") for row in evidence]
    if Counter(input_evidence_ids) != Counter(output_evidence_ids):
        issues.append("input evidence ids are not covered exactly once")
    if not any(row.get("concentration_status") == "CONCENTRATION_GUARD_REQUIRED" for row in concentration):
        issues.append("no concentration guard rows were emitted")
    if counts.get("selected_rows", 0) <= 0:
        issues.append("selected row count is zero")
    if counts.get("preserved_redesign_or_kill_rows", 0) <= 0:
        issues.append("preserved redesign/kill row count is zero")
    selected_plus_preserved = counts.get("selected_rows", 0) + counts.get("preserved_redesign_or_kill_rows", 0)
    if selected_plus_preserved != len(selections):
        issues.append("selected plus preserved rows do not equal selection rows")
    if any(not row.get("source_path") or not row.get("source_file_sha256") for row in selections):
        issues.append("one or more selection rows lack source path/hash")

    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in selections)
    if not any(str(decision).startswith("IMPLEMENT") for decision in decisions):
        issues.append("implement selection decision class is absent")
    if not any(str(decision).startswith("REDESIGN") for decision in decisions):
        issues.append("redesign concentration decision class is absent")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "decision_counts": dict(sorted(decisions.items())),
        "selection_rows": len(selections),
        "evidence_rows": len(evidence),
        "concentration_rows": len(concentration),
        "aggregate_rows": len(aggregates),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
