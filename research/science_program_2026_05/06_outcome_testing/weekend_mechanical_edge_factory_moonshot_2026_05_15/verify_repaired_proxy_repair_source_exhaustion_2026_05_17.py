#!/usr/bin/env python3
"""Verify repaired-proxy repair source exhaustion artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPAIR_SOURCE_EXHAUSTION"
LOOKUP_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPAIR_ACQUISITION_SOURCE_LOOKUP"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
REQUIREMENT_EXHAUSTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REQUIREMENT_EXHAUSTION_LEDGER_2026-05-17.jsonl"
SOURCE_FAMILY_EXHAUSTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_FAMILY_EXHAUSTION_LEDGER_2026-05-17.jsonl"
REPAIR_EXECUTION_EXHAUSTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_EXECUTION_EXHAUSTION_LEDGER_2026-05-17.jsonl"
SOURCE_PATH_PROOF_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_PATH_PROOF_LEDGER_2026-05-17.jsonl"
EXHAUSTION_GATE_LEDGER = ROUTE_DIR / f"{PREFIX}_EXHAUSTION_GATE_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

LOOKUP_RESULT = ROUTE_DIR / f"{LOOKUP_PREFIX}_RESULT_2026-05-17.json"
LOOKUP_EXECUTION_LEDGER = ROUTE_DIR / f"{LOOKUP_PREFIX}_LOOKUP_EXECUTION_LEDGER_2026-05-17.jsonl"
FIELD_FULFILLMENT_LEDGER = ROUTE_DIR / f"{LOOKUP_PREFIX}_FIELD_FULFILLMENT_LEDGER_2026-05-17.jsonl"
SOURCE_CANDIDATE_LOOKUP_LEDGER = ROUTE_DIR / f"{LOOKUP_PREFIX}_SOURCE_CANDIDATE_LOOKUP_LEDGER_2026-05-17.jsonl"
BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_repair_source_exhaustion_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_repair_source_exhaustion.py"


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
    lookup_result = read_json(LOOKUP_RESULT)
    lookup_rows = read_jsonl(LOOKUP_EXECUTION_LEDGER)
    field_rows = read_jsonl(FIELD_FULFILLMENT_LEDGER)
    source_candidate_rows = read_jsonl(SOURCE_CANDIDATE_LOOKUP_LEDGER)
    ledgers = {
        "requirement_exhaustion_rows": read_jsonl(REQUIREMENT_EXHAUSTION_LEDGER),
        "source_family_exhaustion_rows": read_jsonl(SOURCE_FAMILY_EXHAUSTION_LEDGER),
        "repair_execution_exhaustion_rows": read_jsonl(REPAIR_EXECUTION_EXHAUSTION_LEDGER),
        "source_path_proof_rows": read_jsonl(SOURCE_PATH_PROOF_LEDGER),
        "exhaustion_gate_rows": read_jsonl(EXHAUSTION_GATE_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "system_action_rows": read_jsonl(SYSTEM_ACTION_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    expected = {
        "input_lookup_result_ok": int(bool(lookup_result.get("ok"))),
        "input_lookup_execution_rows": len(lookup_rows),
        "input_field_fulfillment_rows": len(field_rows),
        "requirement_exhaustion_rows": len(field_rows),
        "source_path_proof_rows": len(source_candidate_rows),
        "exhaustion_gate_rows": 1,
        "system_action_rows": 1,
        "repair_rerun_ready_rows": 0,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")

    requirement_by_id = Counter(
        str(row.get("input_acquisition_requirement_row_id")) for row in ledgers["requirement_exhaustion_rows"]
    )
    if set(requirement_by_id.values()) != {1}:
        issues.append("requirement exhaustion rows are not one-per-field-fulfillment row")

    execution_status_counts = Counter(
        str(row.get("repair_execution_exhaustion_status")) for row in ledgers["repair_execution_exhaustion_rows"]
    )
    expected_execution_statuses = {
        "DIRECT_IDENTIFIER_REPAIR_EXHAUSTED_NO_ROW_KEY_JOIN": 170,
        "SCOPE_IDENTITY_REPAIR_EXHAUSTED_EXACT_JOIN_FIELDS_ABSENT": 18,
    }
    for status, value in expected_execution_statuses.items():
        if execution_status_counts.get(status, 0) != value:
            issues.append(f"{status} expected {value} got {execution_status_counts.get(status, 0)}")

    gate = ledgers["exhaustion_gate_rows"][0] if ledgers["exhaustion_gate_rows"] else {}
    if gate.get("source_exhaustion_gate_status") != "EXACT_PROXY_RERUN_GATE_HELD_SOURCE_EXHAUSTION_PROVEN_CURRENT_BRANCH":
        issues.append("source exhaustion gate status drifted")
    if any(row.get("repair_rerun_ready_after_exhaustion") for row in ledgers["repair_execution_exhaustion_rows"]):
        issues.append("repair execution exhaustion row unexpectedly ready")

    requirement_class_counts = Counter(str(row.get("exhaustion_class")) for row in ledgers["requirement_exhaustion_rows"])
    expected_classes = {
        "FIELD_EXISTS_IN_SOURCE_FAMILY_BUT_REQUIREMENT_HAS_NO_ROW_KEY_JOIN": 510,
        "ROW_KEY_JOINED_BUT_REQUIRED_FIELD_ABSENT_IN_BRANCH_LOCAL_SOURCES": 54,
    }
    for cls, value in expected_classes.items():
        if requirement_class_counts.get(cls, 0) != value:
            issues.append(f"{cls} expected {value} got {requirement_class_counts.get(cls, 0)}")

    for key, rows in ledgers.items():
        sample = rows[:100] if key in {"requirement_exhaustion_rows", "source_manifest_rows"} else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        REQUIREMENT_EXHAUSTION_LEDGER,
        SOURCE_FAMILY_EXHAUSTION_LEDGER,
        REPAIR_EXECUTION_EXHAUSTION_LEDGER,
        SOURCE_PATH_PROOF_LEDGER,
        EXHAUSTION_GATE_LEDGER,
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
        "requirement_exhaustion_class_counts": dict(sorted(requirement_class_counts.items())),
        "repair_execution_exhaustion_status_counts": dict(sorted(execution_status_counts.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
