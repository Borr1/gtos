#!/usr/bin/env python3
"""Verify repaired-proxy repair field acquisition artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPAIR_FIELD_ACQUISITION"
EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPAIR_WORK_EXECUTION"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ACQUISITION_REQUIREMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_ACQUISITION_REQUIREMENT_LEDGER_2026-05-17.jsonl"
ACQUISITION_BATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_ACQUISITION_BATCH_LEDGER_2026-05-17.jsonl"
SOURCE_CANDIDATE_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_CANDIDATE_LEDGER_2026-05-17.jsonl"
UNBLOCK_PLAN_LEDGER = ROUTE_DIR / f"{PREFIX}_UNBLOCK_PLAN_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

EXEC_RESULT = ROUTE_DIR / f"{EXEC_PREFIX}_RESULT_2026-05-17.json"
REPAIR_EXECUTION_LEDGER = ROUTE_DIR / f"{EXEC_PREFIX}_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_repair_acquisition_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_repair_acquisition.py"


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
    exec_result = read_json(EXEC_RESULT)
    execution_rows = read_jsonl(REPAIR_EXECUTION_LEDGER)
    ledgers = {
        "acquisition_requirement_rows": read_jsonl(ACQUISITION_REQUIREMENT_LEDGER),
        "acquisition_batch_rows": read_jsonl(ACQUISITION_BATCH_LEDGER),
        "source_candidate_rows": read_jsonl(SOURCE_CANDIDATE_LEDGER),
        "unblock_plan_rows": read_jsonl(UNBLOCK_PLAN_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "system_action_rows": read_jsonl(SYSTEM_ACTION_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    expected_requirements = sum(len(row.get("missing_required_fields") or []) for row in execution_rows)
    expected_batches = len(
        {
            (str(row.get("repair_route_family") or ""), str(field))
            for row in execution_rows
            for field in row.get("missing_required_fields") or []
        }
    )
    expected = {
        "input_repair_execution_rows": exec_result.get("counts", {}).get("repair_execution_rows"),
        "acquisition_requirement_rows": expected_requirements,
        "acquisition_batch_rows": expected_batches,
        "unblock_plan_rows": 3,
        "system_action_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")
    if not result.get("blocked_execution_rows_expanded"):
        issues.append("blocked execution rows were not fully expanded")

    requirement_counts = Counter(
        str(row.get("missing_required_field") or "") for row in ledgers["acquisition_requirement_rows"]
    )
    expected_field_counts = {
        "candidate_lock_metadata": 170,
        "direct_trade_candidate_identifier": 170,
        "ticket_identifier": 170,
        "symbol": 18,
        "route_session": 18,
        "horizon_id": 18,
    }
    for field, value in expected_field_counts.items():
        if requirement_counts.get(field, 0) != value:
            issues.append(f"{field} acquisition count expected {value} got {requirement_counts.get(field, 0)}")
    if requirement_counts.get("source_component", 0) != 0:
        issues.append("source_component should not require acquisition because it is present on scope rows")

    source_family_counts = Counter(
        str(row.get("acquisition_source_family") or "") for row in ledgers["acquisition_requirement_rows"]
    )
    if source_family_counts.get("SCOPE_IDENTITY_SOURCE", 0) != 54:
        issues.append("scope identity source requirement count drifted")
    if not ledgers["source_candidate_rows"]:
        issues.append("source candidate rows were not emitted")

    for key, rows in ledgers.items():
        sample = rows[:50] if key == "acquisition_requirement_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        ACQUISITION_REQUIREMENT_LEDGER,
        ACQUISITION_BATCH_LEDGER,
        SOURCE_CANDIDATE_LEDGER,
        UNBLOCK_PLAN_LEDGER,
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
        "acquisition_requirement_field_counts": dict(sorted(requirement_counts.items())),
        "acquisition_source_family_counts": dict(sorted(source_family_counts.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
