#!/usr/bin/env python3
"""Verify repaired-proxy repair execution artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPAIR_WORK_EXECUTION"
WORK_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_COMPARATOR_INPUT_REPAIR_WORK"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
REPAIR_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
FIELD_COVERAGE_LEDGER = ROUTE_DIR / f"{PREFIX}_FIELD_COVERAGE_LEDGER_2026-05-17.jsonl"
EXECUTION_BATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_EXECUTION_BATCH_LEDGER_2026-05-17.jsonl"
RERUN_GATE_LEDGER = ROUTE_DIR / f"{PREFIX}_RERUN_GATE_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

WORK_RESULT = ROUTE_DIR / f"{WORK_PREFIX}_RESULT_2026-05-17.json"
REPAIR_WORK_ORDER_LEDGER = ROUTE_DIR / f"{WORK_PREFIX}_REPAIR_WORK_ORDER_LEDGER_2026-05-17.jsonl"
BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_repair_execution_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_repair_execution.py"


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
    work_result = read_json(WORK_RESULT)
    work_rows = read_jsonl(REPAIR_WORK_ORDER_LEDGER)
    ledgers = {
        "repair_execution_rows": read_jsonl(REPAIR_EXECUTION_LEDGER),
        "field_coverage_rows": read_jsonl(FIELD_COVERAGE_LEDGER),
        "execution_batch_rows": read_jsonl(EXECUTION_BATCH_LEDGER),
        "rerun_gate_rows": read_jsonl(RERUN_GATE_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "system_action_rows": read_jsonl(SYSTEM_ACTION_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    expected_field_rows = sum(len(row.get("required_fields") or []) for row in work_rows)
    expected_field_keys = len(
        {
            (str(row.get("repair_route_family") or ""), str(field))
            for row in work_rows
            for field in row.get("required_fields") or []
        }
    )
    expected = {
        "input_repair_work_order_rows": work_result.get("counts", {}).get("repair_work_order_rows"),
        "repair_execution_rows": len(work_rows),
        "field_coverage_rows": expected_field_keys,
        "rerun_gate_rows": 1,
        "system_action_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")
    if expected_field_rows <= 0:
        issues.append("repair work orders have no required fields")
    if not result.get("repair_work_order_denominator_preserved"):
        issues.append("repair work order denominator not preserved")

    status_counts = Counter(str(row.get("repair_execution_status") or "") for row in ledgers["repair_execution_rows"])
    if status_counts.get("REPAIR_EXECUTION_BLOCKED_MISSING_DIRECT_IDENTIFIER_FIELDS", 0) != 170:
        issues.append("direct identifier blocked count drifted")
    if status_counts.get("REPAIR_EXECUTION_BLOCKED_MISSING_SCOPE_IDENTITY_FIELDS", 0) != 18:
        issues.append("scope identity blocked count drifted")
    if counts.get("rerun_eligible_rows") != 0:
        issues.append("rerun eligible rows should remain zero until repair fields are supplied")
    if counts.get("blocked_repair_rows") != len(work_rows):
        issues.append("blocked repair rows should equal all work orders")
    gate_rows = ledgers["rerun_gate_rows"]
    if gate_rows[0].get("rerun_gate_status") != "EXACT_PROXY_RERUN_GATE_HELD_ALL_REPAIR_WORK_ORDERS_BLOCKED":
        issues.append("rerun gate status should hold while all repairs are blocked")
    if result.get("exact_proxy_rerun_gate_status") != gate_rows[0].get("rerun_gate_status"):
        issues.append("result rerun gate status does not match ledger")

    for key, rows in ledgers.items():
        sample = rows[:50] if key == "repair_execution_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        REPAIR_EXECUTION_LEDGER,
        FIELD_COVERAGE_LEDGER,
        EXECUTION_BATCH_LEDGER,
        RERUN_GATE_LEDGER,
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
        "repair_execution_status_counts": dict(sorted(status_counts.items())),
        "rerun_gate_status": gate_rows[0].get("rerun_gate_status"),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
