#!/usr/bin/env python3
"""Verify repaired-proxy execution registry artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_EXECUTION_REGISTRY"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_EXECUTION_SPECS"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
DEFAULT_SCOPE_REGISTRY_LEDGER = ROUTE_DIR / f"{PREFIX}_DEFAULT_SCOPE_REGISTRY_LEDGER_2026-05-17.jsonl"
AVOID_SCOPE_REGISTRY_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_SCOPE_REGISTRY_LEDGER_2026-05-17.jsonl"
EVENT_REGISTRY_APPLICATION_LEDGER = ROUTE_DIR / f"{PREFIX}_EVENT_REGISTRY_APPLICATION_LEDGER_2026-05-17.jsonl"
AVOID_COMPARATOR_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_COMPARATOR_EXECUTION_LEDGER_2026-05-17.jsonl"
REPAIR_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_EXECUTION_LEDGER_2026-05-17.jsonl"
MARKET_REPLAY_NUMERIC_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_REPLAY_NUMERIC_POPULATION_LEDGER_2026-05-17.jsonl"
SYMBOL_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_ACTION_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_execution_registry_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_execution_registry.py"


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
    input_result = read_json(INPUT_RESULT)
    ledgers = {
        "default_scope_registry_rows": read_jsonl(DEFAULT_SCOPE_REGISTRY_LEDGER),
        "avoid_scope_registry_rows": read_jsonl(AVOID_SCOPE_REGISTRY_LEDGER),
        "event_registry_application_rows": read_jsonl(EVENT_REGISTRY_APPLICATION_LEDGER),
        "avoid_comparator_execution_rows": read_jsonl(AVOID_COMPARATOR_EXECUTION_LEDGER),
        "repair_execution_rows": read_jsonl(REPAIR_EXECUTION_LEDGER),
        "market_replay_numeric_population_rows": read_jsonl(MARKET_REPLAY_NUMERIC_LEDGER),
        "symbol_action_rows": read_jsonl(SYMBOL_ACTION_LEDGER),
        "system_action_rows": read_jsonl(SYSTEM_ACTION_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")
    expected = {
        "input_default_spec_rows": 12303,
        "input_avoid_spec_rows": 5443,
        "input_repair_task_rows": 170,
        "input_exact_proxy_bridge_rows": 17916,
        "input_market_population_rows": 301,
        "default_scope_registry_rows": 102,
        "avoid_scope_registry_rows": 154,
        "event_registry_application_rows": 17916,
        "avoid_comparator_execution_rows": 5443,
        "repair_execution_rows": 170,
        "market_replay_numeric_population_rows": 301,
        "system_action_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")
    if counts.get("event_registry_application_rows") != input_result.get("counts", {}).get("exact_proxy_bridge_rows"):
        issues.append("event registry denominator does not match upstream bridge denominator")
    status_counts = Counter(
        str(row.get("execution_registry_status") or "") for row in ledgers["event_registry_application_rows"]
    )
    if status_counts.get("EXECUTION_REGISTRY_EVENT_HAS_NO_SPEC_MATCH", 0):
        issues.append("unmatched registry application rows present")
    if sum(status_counts.values()) != 17916:
        issues.append("registry status rows do not sum to 17916")
    for key, rows in ledgers.items():
        sample = rows[:10] if key == "event_registry_application_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")
    files_to_scan = [
        RESULT_PATH,
        DEFAULT_SCOPE_REGISTRY_LEDGER,
        AVOID_SCOPE_REGISTRY_LEDGER,
        EVENT_REGISTRY_APPLICATION_LEDGER,
        AVOID_COMPARATOR_EXECUTION_LEDGER,
        REPAIR_EXECUTION_LEDGER,
        MARKET_REPLAY_NUMERIC_LEDGER,
        SYMBOL_ACTION_LEDGER,
        SYSTEM_ACTION_LEDGER,
        BUCKET_LEDGER,
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
        "status_counts": dict(sorted(status_counts.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
