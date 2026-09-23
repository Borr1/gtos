#!/usr/bin/env python3
"""Verify expanded-market unpackaged evidence resolution checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
FINAL_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_FINAL_IMPLEMENTATION_DECISIONS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_UNPACKAGED_EVIDENCE_RESOLUTION"

FINAL_RESULT = ROUTE_DIR / f"{FINAL_PREFIX}_RESULT_2026-05-17.json"
FINAL_EVIDENCE_LEDGER = ROUTE_DIR / f"{FINAL_PREFIX}_EVIDENCE_LEDGER_2026-05-17.jsonl"
FINAL_REDESIGN_LEDGER = ROUTE_DIR / f"{FINAL_PREFIX}_REDESIGN_LEDGER_2026-05-17.jsonl"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RESOLUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_RESOLUTION_LEDGER_2026-05-17.jsonl"
REPACKAGE_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_REPACKAGE_CANDIDATE_LEDGER_2026-05-17.jsonl"
TERMINAL_REDESIGN_LEDGER = ROUTE_DIR / f"{PREFIX}_TERMINAL_REDESIGN_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_unpackaged_evidence_resolution.py",
    ROUTE_DIR / "build_expanded_market_unpackaged_evidence_resolution_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    RESOLUTION_LEDGER,
    REPACKAGE_CANDIDATE_LEDGER,
    TERMINAL_REDESIGN_LEDGER,
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


def group_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, str, str, str]:
    return (
        str(row.get("symbol") or ""),
        str(row.get("market_timeframe") or ""),
        str(row.get("route_session") or ""),
        str(row.get("horizon_id") or ""),
        str(row.get("source_component") or ""),
        str(row.get("selected_side") or ""),
        str(row.get("source_path") or ""),
        str(row.get("source_file_sha256") or ""),
    )


def main() -> None:
    issues: list[str] = []
    final_result = read_json(FINAL_RESULT)
    input_evidence = read_jsonl(FINAL_EVIDENCE_LEDGER)
    input_redesign = read_jsonl(FINAL_REDESIGN_LEDGER)
    result = read_json(RESULT_PATH)
    resolution = read_jsonl(RESOLUTION_LEDGER)
    candidates = read_jsonl(REPACKAGE_CANDIDATE_LEDGER)
    terminal_redesign = read_jsonl(TERMINAL_REDESIGN_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    counts = result.get("counts") or {}

    if final_result.get("ok") is not True:
        issues.append("input CP233 result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(input_evidence) != 9266:
        issues.append("input evidence rows must equal 9266")
    if len(input_redesign) != 151:
        issues.append("input redesign rows must equal 151")
    expected_counts = {
        "unpackaged_evidence_resolution_rows": len(resolution),
        "unpackaged_repackage_candidate_rows": len(candidates),
        "terminal_redesign_rows": len(terminal_redesign),
        "aggregate_rows": len(aggregates),
        "system_rows": len(system_rows),
    }
    for field, actual in expected_counts.items():
        if counts.get(field) != actual:
            issues.append(f"{field} count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len(resolution) != len(input_evidence):
        issues.append("resolution rows must preserve all input evidence rows")
    if len(terminal_redesign) != len(input_redesign):
        issues.append("terminal redesign rows must preserve all input redesign rows")

    all_rows = resolution + candidates + terminal_redesign + aggregates + system_rows
    if any(not boundary_ok(row) for row in all_rows):
        issues.append("one or more ledger rows failed branch-local boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")

    input_status_counts = Counter(row.get("final_implementation_evidence_status") for row in input_evidence)
    resolution_status_counts = Counter(row.get("resolution_status") for row in resolution)
    if counts.get("already_implemented_evidence_rows") != input_status_counts.get(
        "FINAL_IMPLEMENTATION_EVIDENCE_DECISION_PASS", 0
    ):
        issues.append("already implemented evidence count mismatch")
    if counts.get("repackage_required_evidence_rows") != resolution_status_counts.get(
        "UNPACKAGED_EVIDENCE_RESOLUTION_REPACKAGE_REQUIRED", 0
    ):
        issues.append("repackage-required evidence count mismatch")
    if counts.get("underpowered_evidence_rows") != resolution_status_counts.get(
        "UNPACKAGED_EVIDENCE_RESOLUTION_REDESIGN_UNDERPOWERED", 0
    ):
        issues.append("underpowered evidence count mismatch")
    if counts.get("kill_evidence_rows") != resolution_status_counts.get(
        "UNPACKAGED_EVIDENCE_RESOLUTION_KILL_NONPOSITIVE_R", 0
    ):
        issues.append("kill evidence count mismatch")
    if counts.get("missing_simulated_r_rows") != resolution_status_counts.get(
        "UNPACKAGED_EVIDENCE_RESOLUTION_MISSING_SIMULATED_R", 0
    ):
        issues.append("missing simulated R count mismatch")

    required_repackage_keys = {
        group_key(row)
        for row in resolution
        if row.get("resolution_status") == "UNPACKAGED_EVIDENCE_RESOLUTION_REPACKAGE_REQUIRED"
    }
    candidate_keys = {group_key(row) for row in candidates}
    if candidate_keys != required_repackage_keys:
        issues.append("repackage candidate keys do not match required repackage evidence groups")
    if Counter(row.get("final_implementation_evidence_row_id") for row in input_evidence) != Counter(
        row.get("input_final_implementation_evidence_row_id") for row in resolution
    ):
        issues.append("input evidence ids are not covered exactly once")
    if Counter(row.get("final_implementation_redesign_row_id") for row in input_redesign) != Counter(
        row.get("input_final_implementation_redesign_row_id") for row in terminal_redesign
    ):
        issues.append("input redesign ids are not covered exactly once")
    if any(not row.get("repackage_candidate_payload_sha256") for row in candidates):
        issues.append("one or more repackage candidates lack payload hash")

    decision_counts = Counter(row.get("keep_kill_redesign_implement_decision") for row in resolution)
    if decision_counts.get("IMPLEMENT_EXPANDED_MARKET_EXISTING_FINAL_DECISION_EVIDENCE") != counts.get(
        "already_implemented_evidence_rows"
    ):
        issues.append("implemented evidence decision count mismatch")
    if decision_counts.get("REDESIGN_EXPANDED_MARKET_UNPACKAGED_EVIDENCE_REPACKAGE") != counts.get(
        "repackage_required_evidence_rows"
    ):
        issues.append("repackage evidence decision count mismatch")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "resolution_rows": len(resolution),
        "repackage_candidate_rows": len(candidates),
        "terminal_redesign_rows": len(terminal_redesign),
        "aggregate_rows": len(aggregates),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
