#!/usr/bin/env python3
"""Verify repaired-proxy comparator input and repair-work artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_COMPARATOR_INPUT_REPAIR_WORK"
ACTION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCORE_BRIDGE_ACTION_PACKET"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
COMPARATOR_INPUT_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPARATOR_INPUT_LEDGER_2026-05-17.jsonl"
COMPARATOR_SYMBOL_QUEUE_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPARATOR_SYMBOL_QUEUE_LEDGER_2026-05-17.jsonl"
REPAIR_WORK_ORDER_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_WORK_ORDER_LEDGER_2026-05-17.jsonl"
REPAIR_BATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_BATCH_LEDGER_2026-05-17.jsonl"
RERUN_PLAN_LEDGER = ROUTE_DIR / f"{PREFIX}_RERUN_PLAN_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

ACTION_RESULT = ROUTE_DIR / f"{ACTION_PREFIX}_RESULT_2026-05-17.json"
COMPARATOR_PACKET_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_COMPARATOR_PACKET_LEDGER_2026-05-17.jsonl"
REPAIR_ROUTING_LEDGER = ROUTE_DIR / f"{ACTION_PREFIX}_REPAIR_ROUTING_LEDGER_2026-05-17.jsonl"
BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_comparator_input_repair_work_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_comparator_input_repair_work.py"


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
    action_result = read_json(ACTION_RESULT)
    packet_rows = read_jsonl(COMPARATOR_PACKET_LEDGER)
    repair_rows = read_jsonl(REPAIR_ROUTING_LEDGER)
    ledgers = {
        "comparator_input_rows": read_jsonl(COMPARATOR_INPUT_LEDGER),
        "comparator_symbol_queue_rows": read_jsonl(COMPARATOR_SYMBOL_QUEUE_LEDGER),
        "repair_work_order_rows": read_jsonl(REPAIR_WORK_ORDER_LEDGER),
        "repair_batch_rows": read_jsonl(REPAIR_BATCH_LEDGER),
        "rerun_plan_rows": read_jsonl(RERUN_PLAN_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "system_action_rows": read_jsonl(SYSTEM_ACTION_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    expected_symbol_queue = len(
        {
            (
                str(row.get("symbol") or ""),
                str(row.get("route_session") or ""),
                str(row.get("horizon_id") or ""),
            )
            for row in packet_rows
        }
    )
    expected_repair_batches = len({str(row.get("repair_route_family") or "") for row in repair_rows})
    expected = {
        "input_comparator_packet_rows": action_result.get("counts", {}).get("comparator_packet_rows"),
        "input_repair_routing_rows": action_result.get("counts", {}).get("repair_routing_rows"),
        "comparator_input_rows": len(packet_rows),
        "comparator_symbol_queue_rows": expected_symbol_queue,
        "repair_work_order_rows": len(repair_rows),
        "repair_batch_rows": expected_repair_batches,
        "rerun_plan_rows": 4,
        "system_action_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")

    if not result.get("comparator_packet_denominator_preserved"):
        issues.append("comparator packet denominator not preserved")
    if not result.get("repair_routing_denominator_preserved"):
        issues.append("repair routing denominator not preserved")

    family_counts = Counter(str(row.get("comparator_input_family") or "") for row in ledgers["comparator_input_rows"])
    if family_counts.get("DEFAULT_OFF_SCORER_COMPARATOR_INPUT", 0) != 102:
        issues.append("default-off comparator input count drifted from action-packet verifier count")
    if family_counts.get("AVOID_REDESIGN_COMPARATOR_INPUT", 0) != 152:
        issues.append("avoid comparator input count drifted from action-packet verifier count")
    repair_counts = Counter(str(row.get("repair_route_family") or "") for row in ledgers["repair_work_order_rows"])
    if repair_counts.get("IDENTIFIER_LINKAGE_REPAIR_REQUIRED", 0) != 170:
        issues.append("identifier repair work order count drifted")
    if repair_counts.get("SCOPE_IDENTITY_REPAIR_REQUIRED", 0) != 18:
        issues.append("scope identity repair work order count drifted")
    if not all(row.get("required_fields") for row in ledgers["repair_work_order_rows"][:50]):
        issues.append("sample repair work orders are missing required fields")

    for key, rows in ledgers.items():
        sample = rows[:50] if key in {"comparator_input_rows", "repair_work_order_rows"} else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        COMPARATOR_INPUT_LEDGER,
        COMPARATOR_SYMBOL_QUEUE_LEDGER,
        REPAIR_WORK_ORDER_LEDGER,
        REPAIR_BATCH_LEDGER,
        RERUN_PLAN_LEDGER,
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
        "comparator_input_family_counts": dict(sorted(family_counts.items())),
        "repair_work_order_family_counts": dict(sorted(repair_counts.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
