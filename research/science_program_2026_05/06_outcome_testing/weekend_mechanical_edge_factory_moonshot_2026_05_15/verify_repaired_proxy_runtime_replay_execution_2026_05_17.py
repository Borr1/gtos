#!/usr/bin/env python3
"""Verify repaired-proxy runtime replay execution artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_EXECUTION"
REGISTRY_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_CANDIDATE_REGISTRY"
SCORE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPLAY_SCORE_RERUN"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
REPLAY_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REPLAY_EXECUTION_LEDGER_2026-05-17.jsonl"
MODULE_MATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_MODULE_MATCH_LEDGER_2026-05-17.jsonl"
SYMBOL_OUTCOME_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_OUTCOME_LEDGER_2026-05-17.jsonl"
NONREGISTRATION_REPLAY_CARRY_LEDGER = ROUTE_DIR / f"{PREFIX}_NONREGISTRATION_REPLAY_CARRY_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

REGISTRY_MODULE_LEDGER = ROUTE_DIR / f"{REGISTRY_PREFIX}_REGISTRY_MODULE_LEDGER_2026-05-17.jsonl"
NONREGISTRATION_REGISTRY_REVIEW_LEDGER = ROUTE_DIR / f"{REGISTRY_PREFIX}_NONREGISTRATION_REGISTRY_REVIEW_LEDGER_2026-05-17.jsonl"
SCORE_RERUN_LEDGER = ROUTE_DIR / f"{SCORE_PREFIX}_SCORE_RERUN_LEDGER_2026-05-17.jsonl"
BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_execution_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_runtime_replay_execution.py"


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


def blocked_boundary_terms() -> list[str]:
    return [
        "NO_" + "PROMOTION_VERDICT",
        "validation" + "_safe",
        "outcome_" + "review_opened",
        "live_" + "effect",
        "safe_" + "flags",
    ]


def boundary_ok(row: dict[str, Any]) -> bool:
    boundary = row.get("research_boundary") or {}
    return (
        boundary.get("boundary_schema") == BOUNDARY_SCHEMA
        and boundary.get("artifact_scope") == "branch_local_research"
        and boundary.get("production_import_path") is False
        and boundary.get("mutates_order_risk_prompt_safety_or_mt5") is False
        and boundary.get("runtime_candidate_use_permitted") is False
        and boundary.get("unconditional_scalar_use_permitted") is False
    )


def scan_blocked_terms(paths: list[Path]) -> dict[str, list[str]]:
    blocked = blocked_boundary_terms()
    hits: dict[str, list[str]] = {}
    for path in paths:
        with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        found = [term for term in blocked if term in text]
        if found:
            hits[path.name] = found
    return hits


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    input_registry_rows = read_jsonl(REGISTRY_MODULE_LEDGER)
    input_score_rows = read_jsonl(SCORE_RERUN_LEDGER)
    input_nonregistration_rows = read_jsonl(NONREGISTRATION_REGISTRY_REVIEW_LEDGER)
    ledgers = {
        "replay_registry_execution_rows": read_jsonl(REPLAY_EXECUTION_LEDGER),
        "replay_module_match_rows": read_jsonl(MODULE_MATCH_LEDGER),
        "symbol_outcome_rows": read_jsonl(SYMBOL_OUTCOME_LEDGER),
        "nonregistration_replay_carry_rows": read_jsonl(NONREGISTRATION_REPLAY_CARRY_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "system_action_rows": read_jsonl(SYSTEM_ACTION_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    execution_status = Counter(
        str(row.get("replay_registry_execution_status")) for row in ledgers["replay_registry_execution_rows"]
    )
    input_families = Counter(str(row.get("registry_family")) for row in input_score_rows)
    module_outcomes = Counter(str(row.get("module_event_outcome")) for row in ledgers["replay_module_match_rows"])
    expected = {
        "input_registry_module_rows": len(input_registry_rows),
        "input_score_rerun_rows": len(input_score_rows),
        "input_nonregistration_registry_review_rows": len(input_nonregistration_rows),
        "replay_registry_execution_rows": len(input_score_rows),
        "nonregistration_replay_carry_rows": len(input_nonregistration_rows),
        "system_action_rows": 1,
        "repair_context_replay_rows": input_families.get("source_or_broker_geometry_repair", 0),
        "replay_module_match_rows": sum(
            int(row.get("matching_registry_module_rows") or 0) for row in ledgers["replay_registry_execution_rows"]
        ),
        "triggered_or_accepted_replay_rows": execution_status.get(
            "REPLAY_REGISTRY_EXECUTION_CANDIDATE_TRIGGERED_BRANCH_LOCAL", 0
        ),
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")
    status_total = sum(execution_status.values())
    if status_total != len(input_score_rows):
        issues.append(f"execution status total expected {len(input_score_rows)} got {status_total}")
    match_outcome_total = sum(module_outcomes.values())
    if match_outcome_total != counts.get("replay_module_match_rows"):
        issues.append("module outcome count does not equal module match rows")
    rows_with_matches = sum(
        1 for row in ledgers["replay_registry_execution_rows"] if int(row.get("matching_registry_module_rows") or 0) > 0
    )
    if counts.get("replay_rows_with_matching_registry") != rows_with_matches:
        issues.append("rows-with-matching-registry count drifted")
    if rows_with_matches > len(input_score_rows):
        issues.append("rows-with-matching-registry exceeds replay denominator")

    for key, rows in ledgers.items():
        sample = rows[:100] if key == "source_manifest_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        REPLAY_EXECUTION_LEDGER,
        MODULE_MATCH_LEDGER,
        SYMBOL_OUTCOME_LEDGER,
        NONREGISTRATION_REPLAY_CARRY_LEDGER,
        BUCKET_LEDGER,
        SYSTEM_ACTION_LEDGER,
        SOURCE_MANIFEST_LEDGER,
        SUMMARY_PATH,
        BUILDER_MODULE,
        HELPER_MODULE,
        Path(__file__),
    ]
    blocked_hits = scan_blocked_terms(files_to_scan)
    if blocked_hits:
        issues.append(f"blocked boundary terms present: {blocked_hits}")

    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": {key: counts.get(key) for key in sorted(counts)},
        "execution_status_counts": dict(sorted(execution_status.items())),
        "input_registry_family_counts": dict(sorted(input_families.items())),
        "module_event_outcome_counts": dict(sorted(module_outcomes.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
