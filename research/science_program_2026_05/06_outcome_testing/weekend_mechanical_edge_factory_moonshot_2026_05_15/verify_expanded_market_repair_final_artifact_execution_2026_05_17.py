#!/usr/bin/env python3
"""Verify expanded-market repair final artifact execution checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPAIR_FINAL_ARTIFACTS"
HELD_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REPAIR_APPLICATION_EXECUTION"

INPUT_ARTIFACT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ARTIFACT_LEDGER_2026-05-17.jsonl"
INPUT_EVIDENCE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
INPUT_CONTROL_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_CONTROL_LEDGER_2026-05-17.jsonl"
HELD_EXECUTION_LEDGER = ROUTE_DIR / f"{HELD_PREFIX}_APPLICATION_EXECUTION_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ARTIFACT_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_ARTIFACT_EXECUTION_LEDGER_2026-05-17.jsonl"
EVIDENCE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_EXECUTION_LEDGER_2026-05-17.jsonl"
CONTROL_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_EXECUTION_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_repair_final_artifact_execution.py",
    ROUTE_DIR / "build_expanded_market_repair_final_artifact_execution_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, ARTIFACT_EXECUTION_LEDGER, EVIDENCE_EXECUTION_LEDGER, CONTROL_EXECUTION_LEDGER, AGGREGATE_LEDGER, ISSUE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]


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


def ids_from(path: Path, field: str) -> set[str]:
    return {str(row.get(field) or "") for row in iter_jsonl(path)}


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    counts = result.get("counts") or {}

    input_artifact_ids = ids_from(INPUT_ARTIFACT_LEDGER, "expanded_market_repair_final_artifact_row_id")
    input_evidence_ids = ids_from(INPUT_EVIDENCE_LEDGER, "expanded_market_repair_final_artifact_evidence_row_id")
    input_control_ids = ids_from(INPUT_CONTROL_LEDGER, "expanded_market_repair_final_artifact_control_row_id")
    held_ids = ids_from(HELD_EXECUTION_LEDGER, "expanded_market_repair_application_execution_row_id")

    artifact_input_ids: set[str] = set()
    held_input_ids: set[str] = set()
    artifact_count = 0
    artifact_pass_count = 0
    decision_counts: Counter[str] = Counter()
    for row in iter_jsonl(ARTIFACT_EXECUTION_LEDGER):
        artifact_count += 1
        artifact_input_ids.add(str(row.get("input_repair_final_artifact_row_id") or ""))
        held_input_ids.add(str(row.get("input_repair_application_execution_row_id") or ""))
        decision_counts[row.get("keep_kill_redesign_implement_decision")] += 1
        if not boundary_ok(row):
            issues.append("one or more artifact execution rows failed branch-local boundary checks")
            break
        if row.get("final_artifact_execution_status") == "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_PASS":
            artifact_pass_count += 1
        else:
            issues.append("one or more artifact executions did not pass")
            break
        if row.get("held_repair_application_execution_found") is not True or row.get("final_artifact_execution_match") is not True:
            issues.append("one or more artifact executions lacks held-row match proof")
            break

    evidence_input_ids: set[str] = set()
    evidence_count = 0
    for row in iter_jsonl(EVIDENCE_EXECUTION_LEDGER):
        evidence_count += 1
        evidence_input_ids.add(str(row.get("input_repair_final_artifact_evidence_row_id") or ""))
        decision_counts[row.get("keep_kill_redesign_implement_decision")] += 1
        if not boundary_ok(row):
            issues.append("one or more evidence execution rows failed branch-local boundary checks")
            break
        if row.get("final_artifact_execution_evidence_status") != "PRESERVED_NONCANDIDATE_REPAIR_FINAL_ARTIFACT_EXECUTION_EVIDENCE":
            issues.append("one or more evidence execution rows lacks preservation status")
            break

    control_input_ids: set[str] = set()
    control_count = 0
    control_pass_count = 0
    for row in iter_jsonl(CONTROL_EXECUTION_LEDGER):
        control_count += 1
        control_input_ids.add(str(row.get("input_repair_final_artifact_control_row_id") or ""))
        decision_counts[row.get("keep_kill_redesign_implement_decision")] += 1
        if not boundary_ok(row):
            issues.append("one or more control execution rows failed branch-local boundary checks")
            break
        if row.get("control_status") == "EXPANDED_MARKET_REPAIR_FINAL_ARTIFACT_EXECUTION_CONTROL_PASS":
            control_pass_count += 1
        else:
            issues.append("one or more control executions did not pass")
            break
        if row.get("noncandidate_scope_leakage_count") != 0:
            issues.append("control executions must report zero leakage")
            break

    aggregates = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if artifact_count != 1734 or artifact_pass_count != 1734:
        issues.append("artifact execution count mismatch")
    if artifact_input_ids != input_artifact_ids:
        issues.append("artifact executions do not consume every artifact row")
    if held_input_ids != held_ids:
        issues.append("artifact executions do not consume every held repair execution row")
    if evidence_count != 44386:
        issues.append("evidence execution count mismatch")
    if evidence_input_ids != input_evidence_ids:
        issues.append("evidence executions do not consume every evidence row")
    if control_count != 1734 or control_pass_count != 1734:
        issues.append("control execution count mismatch")
    if control_input_ids != input_control_ids:
        issues.append("control executions do not consume every control row")
    if counts.get("artifact_execution_rows") != artifact_count:
        issues.append("result artifact execution count mismatch")
    if counts.get("artifact_execution_pass_rows") != artifact_pass_count:
        issues.append("result artifact pass count mismatch")
    if counts.get("evidence_execution_rows") != evidence_count:
        issues.append("result evidence count mismatch")
    if counts.get("control_execution_rows") != control_count or counts.get("control_execution_pass_rows") != control_pass_count:
        issues.append("result control count mismatch")
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
                    "artifact_execution_rows": artifact_count,
                    "evidence_execution_rows": evidence_count,
                    "control_execution_rows": control_count,
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
