#!/usr/bin/env python3
"""Verify repaired-proxy comparator execution artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_COMPARATOR_EXECUTION"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_COMPARATOR_INPUT_REPAIR_WORK"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
COMPARATOR_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPARATOR_EXECUTION_LEDGER_2026-05-17.jsonl"
PROXY_R_SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_PROXY_R_SURFACE_LEDGER_2026-05-17.jsonl"
SYMBOL_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_EXECUTION_SUMMARY_LEDGER_2026-05-17.jsonl"
COMPARATOR_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPARATOR_ACTION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

COMPARATOR_INPUT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_COMPARATOR_INPUT_LEDGER_2026-05-17.jsonl"
BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_comparator_execution_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_comparator_execution.py"


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
    input_rows = read_jsonl(COMPARATOR_INPUT_LEDGER)
    ledgers = {
        "comparator_execution_rows": read_jsonl(COMPARATOR_EXECUTION_LEDGER),
        "proxy_r_surface_rows": read_jsonl(PROXY_R_SURFACE_LEDGER),
        "symbol_summary_rows": read_jsonl(SYMBOL_SUMMARY_LEDGER),
        "comparator_action_rows": read_jsonl(COMPARATOR_ACTION_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "system_action_rows": read_jsonl(SYSTEM_ACTION_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    expected = {
        "input_comparator_rows": len(input_rows),
        "comparator_execution_rows": len(input_rows),
        "proxy_r_surface_rows": len(input_rows),
        "system_action_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")

    action_counts = Counter(str(row.get("comparator_execution_action")) for row in ledgers["comparator_execution_rows"])
    action_row_total = sum(int(row.get("comparator_execution_rows") or 0) for row in ledgers["comparator_action_rows"])
    if action_row_total != len(input_rows):
        issues.append("comparator action row total does not match input rows")
    for action, value in action_counts.items():
        if counts.get(f"action_{action.lower()}") != value:
            issues.append(f"{action} count mismatch")

    if not action_counts:
        issues.append("no comparator execution actions emitted")
    if any(row.get("source_exhaustion_gate_status") != result.get("source_exhaustion_gate_status") for row in ledgers["comparator_execution_rows"]):
        issues.append("source exhaustion gate status not attached to all comparator execution rows")

    for key, rows in ledgers.items():
        sample = rows[:100] if key in {"comparator_execution_rows", "proxy_r_surface_rows", "source_manifest_rows"} else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        COMPARATOR_EXECUTION_LEDGER,
        PROXY_R_SURFACE_LEDGER,
        SYMBOL_SUMMARY_LEDGER,
        COMPARATOR_ACTION_LEDGER,
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
        "comparator_execution_action_counts": dict(sorted(action_counts.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
