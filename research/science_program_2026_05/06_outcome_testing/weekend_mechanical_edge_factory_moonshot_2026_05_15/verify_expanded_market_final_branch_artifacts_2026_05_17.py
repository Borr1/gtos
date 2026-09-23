#!/usr/bin/env python3
"""Verify expanded-market final branch artifact checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
CANDIDATE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_REDUCED_IMPLEMENTATION_CANDIDATES"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_FINAL_BRANCH_ARTIFACTS"

CANDIDATE_RESULT = ROUTE_DIR / f"{CANDIDATE_PREFIX}_RESULT_2026-05-17.json"
CANDIDATE_LEDGER = ROUTE_DIR / f"{CANDIDATE_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
EVIDENCE_LEDGER = ROUTE_DIR / f"{CANDIDATE_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ARTIFACT_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
EVIDENCE_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EVIDENCE_EXECUTION_LEDGER_2026-05-17.jsonl"
CONTROL_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_final_branch_artifacts.py",
    ROUTE_DIR / "build_expanded_market_final_branch_artifacts_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    ARTIFACT_LEDGER,
    EVIDENCE_EXECUTION_LEDGER,
    CONTROL_LEDGER,
    AGGREGATE_LEDGER,
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
    candidate_result = read_json(CANDIDATE_RESULT)
    candidates = read_jsonl(CANDIDATE_LEDGER)
    input_evidence = read_jsonl(EVIDENCE_LEDGER)
    result = read_json(RESULT_PATH)
    artifacts = read_jsonl(ARTIFACT_LEDGER)
    evidence_executions = read_jsonl(EVIDENCE_EXECUTION_LEDGER)
    controls = read_jsonl(CONTROL_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if candidate_result.get("ok") is not True:
        issues.append("input CP225 result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(candidates) != 1748:
        issues.append(f"input candidate count changed from 1748 to {len(candidates)}")
    if len(input_evidence) != 9266:
        issues.append(f"input evidence count changed from 9266 to {len(input_evidence)}")
    if counts.get("final_branch_artifact_rows") != len(artifacts):
        issues.append("artifact row count mismatch")
    if counts.get("artifact_evidence_execution_rows") != len(evidence_executions):
        issues.append("evidence execution row count mismatch")
    if counts.get("artifact_control_rows") != len(controls):
        issues.append("control row count mismatch")
    if counts.get("aggregate_rows") != len(aggregates):
        issues.append("aggregate row count mismatch")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len(artifacts) != len(candidates):
        issues.append("artifact rows must match candidate rows")
    if len(evidence_executions) != len(input_evidence):
        issues.append("evidence executions must match input evidence rows")
    if len(controls) != len(artifacts):
        issues.append("control rows must match artifact rows")
    if sum(as_int(row.get("row_count")) for row in aggregates) != len(artifacts):
        issues.append("aggregate row counts do not sum to artifact rows")
    if any(not boundary_ok(row) for row in artifacts + evidence_executions + controls + aggregates + system_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if len({row.get("final_branch_artifact_row_id") for row in artifacts}) != len(artifacts):
        issues.append("artifact row ids are not unique")
    if len({row.get("final_branch_artifact_evidence_execution_row_id") for row in evidence_executions}) != len(
        evidence_executions
    ):
        issues.append("evidence execution row ids are not unique")
    if len({row.get("final_branch_artifact_control_row_id") for row in controls}) != len(controls):
        issues.append("control row ids are not unique")

    input_candidate_ids = [row.get("implementation_candidate_row_id") for row in candidates]
    artifact_candidate_ids = [row.get("input_implementation_candidate_row_id") for row in artifacts]
    if Counter(input_candidate_ids) != Counter(artifact_candidate_ids):
        issues.append("input candidate ids are not covered exactly once")
    input_evidence_ids = [row.get("implementation_candidate_evidence_row_id") for row in input_evidence]
    output_evidence_ids = [row.get("input_implementation_candidate_evidence_row_id") for row in evidence_executions]
    if Counter(input_evidence_ids) != Counter(output_evidence_ids):
        issues.append("input evidence ids are not covered exactly once")

    if any(row.get("artifact_status") != "FINAL_BRANCH_LOCAL_ARTIFACT_READY" for row in artifacts):
        issues.append("one or more artifacts are not ready")
    if any(row.get("artifact_match") is not True for row in evidence_executions):
        issues.append("one or more evidence executions did not match")
    if any(row.get("control_rejected") is not True for row in controls):
        issues.append("one or more controls were not rejected")
    if any(not row.get("source_path") or not row.get("source_file_sha256") for row in artifacts):
        issues.append("one or more artifacts lack source path/hash")
    if any(not row.get("branch_local_code_expression") or not row.get("artifact_scope_definition") for row in artifacts):
        issues.append("one or more artifacts lack executable scope definition")
    if counts.get("ready_artifact_rows") != len(artifacts):
        issues.append("ready artifact count does not match artifact rows")
    if counts.get("evidence_execution_pass_rows") != len(evidence_executions):
        issues.append("evidence pass count does not match evidence execution rows")
    if counts.get("control_rejected_rows") != len(controls):
        issues.append("control rejected count does not match control rows")

    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in artifacts)
    if not any(str(decision).startswith("IMPLEMENT") for decision in decisions):
        issues.append("implement artifact decision class is absent")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "decision_counts": dict(sorted(decisions.items())),
        "artifact_rows": len(artifacts),
        "evidence_execution_rows": len(evidence_executions),
        "control_rows": len(controls),
        "aggregate_rows": len(aggregates),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
