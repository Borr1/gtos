#!/usr/bin/env python3
"""Verify repaired-proxy repair acquisition source lookup artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPAIR_ACQUISITION_SOURCE_LOOKUP"
ACQ_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPAIR_FIELD_ACQUISITION"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SOURCE_CANDIDATE_LOOKUP_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_CANDIDATE_LOOKUP_LEDGER_2026-05-17.jsonl"
LOOKUP_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_LOOKUP_EXECUTION_LEDGER_2026-05-17.jsonl"
FIELD_FULFILLMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_FIELD_FULFILLMENT_LEDGER_2026-05-17.jsonl"
REPAIR_RERUN_READINESS_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_RERUN_READINESS_LEDGER_2026-05-17.jsonl"
RERUN_GATE_LEDGER = ROUTE_DIR / f"{PREFIX}_RERUN_GATE_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

ACQUISITION_REQUIREMENT_LEDGER = ROUTE_DIR / f"{ACQ_PREFIX}_ACQUISITION_REQUIREMENT_LEDGER_2026-05-17.jsonl"
SOURCE_CANDIDATE_LEDGER = ROUTE_DIR / f"{ACQ_PREFIX}_SOURCE_CANDIDATE_LEDGER_2026-05-17.jsonl"
BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_repair_acquisition_source_lookup_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_repair_acquisition_lookup.py"


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
    input_requirements = read_jsonl(ACQUISITION_REQUIREMENT_LEDGER)
    input_sources = read_jsonl(SOURCE_CANDIDATE_LEDGER)
    ledgers = {
        "source_candidate_lookup_rows": read_jsonl(SOURCE_CANDIDATE_LOOKUP_LEDGER),
        "lookup_execution_rows": read_jsonl(LOOKUP_EXECUTION_LEDGER),
        "field_fulfillment_rows": read_jsonl(FIELD_FULFILLMENT_LEDGER),
        "repair_rerun_readiness_rows": read_jsonl(REPAIR_RERUN_READINESS_LEDGER),
        "rerun_gate_rows": read_jsonl(RERUN_GATE_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "system_action_rows": read_jsonl(SYSTEM_ACTION_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    expected_lookup_rows = len(input_requirements) * 3
    expected = {
        "acquisition_requirement_rows": len(input_requirements),
        "input_source_candidate_rows": len(input_sources),
        "source_candidate_lookup_rows": len(input_sources),
        "lookup_execution_rows": expected_lookup_rows,
        "field_fulfillment_rows": len(input_requirements),
        "rerun_gate_rows": 1,
        "system_action_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")

    fulfillment_by_requirement = Counter(
        str(row.get("input_acquisition_requirement_row_id")) for row in ledgers["field_fulfillment_rows"]
    )
    if set(fulfillment_by_requirement.values()) != {1}:
        issues.append("field fulfillment rows are not one-per-requirement")

    attempts_by_requirement = Counter(
        str(row.get("input_acquisition_requirement_row_id")) for row in ledgers["lookup_execution_rows"]
    )
    if set(attempts_by_requirement.values()) != {3}:
        issues.append("lookup execution rows are not three-per-requirement")

    ready_count = sum(1 for row in ledgers["repair_rerun_readiness_rows"] if row.get("repair_rerun_ready") is True)
    if counts.get("repair_rerun_ready_rows") != ready_count:
        issues.append("repair_rerun_ready_rows count does not match readiness ledger")
    gate = ledgers["rerun_gate_rows"][0] if ledgers["rerun_gate_rows"] else {}
    if gate.get("repair_rerun_ready_rows") != ready_count:
        issues.append("rerun gate ready count does not match readiness ledger")
    if ready_count == 0 and gate.get("repair_rerun_gate_status") != "EXACT_PROXY_RERUN_GATE_HELD_NO_FIELD_LOOKUP_REPAIRED_ROWS":
        issues.append("rerun gate should remain held when no repair rows are ready")

    fulfilled_rows = [
        row
        for row in ledgers["field_fulfillment_rows"]
        if row.get("field_fulfillment_status") == "FIELD_FULFILLED_BY_BRANCH_LOCAL_LOOKUP"
    ]
    if counts.get("field_fulfilled_rows") != len(fulfilled_rows):
        issues.append("field_fulfilled_rows count does not match fulfillment ledger")
    if any(not row.get("fulfilled_value") for row in fulfilled_rows):
        issues.append("fulfilled field row missing fulfilled_value")

    source_status_counts = Counter(
        str(row.get("source_candidate_lookup_status")) for row in ledgers["source_candidate_lookup_rows"]
    )
    lookup_status_counts = Counter(str(row.get("lookup_execution_status")) for row in ledgers["lookup_execution_rows"])
    field_status_counts = Counter(str(row.get("field_fulfillment_status")) for row in ledgers["field_fulfillment_rows"])

    for key, rows in ledgers.items():
        sample = rows[:100] if key in {"lookup_execution_rows", "field_fulfillment_rows", "source_manifest_rows"} else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        SOURCE_CANDIDATE_LOOKUP_LEDGER,
        LOOKUP_EXECUTION_LEDGER,
        FIELD_FULFILLMENT_LEDGER,
        REPAIR_RERUN_READINESS_LEDGER,
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
        "source_candidate_lookup_status_counts": dict(sorted(source_status_counts.items())),
        "lookup_execution_status_counts": dict(sorted(lookup_status_counts.items())),
        "field_fulfillment_status_counts": dict(sorted(field_status_counts.items())),
        "repair_rerun_ready_rows": ready_count,
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
