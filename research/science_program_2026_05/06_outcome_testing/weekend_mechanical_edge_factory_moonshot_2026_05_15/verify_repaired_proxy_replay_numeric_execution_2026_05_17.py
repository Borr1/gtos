#!/usr/bin/env python3
"""Verify repaired-proxy replay numeric execution artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPLAY_NUMERIC_EXECUTION"
CONTRACT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPLAY_CONTRACTS"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SOURCE_NUMERIC_METRIC_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_NUMERIC_METRIC_LEDGER_2026-05-17.jsonl"
REPLAY_NUMERIC_EVENT_LEDGER = ROUTE_DIR / f"{PREFIX}_REPLAY_NUMERIC_EVENT_LEDGER_2026-05-17.jsonl"
CONTROL_NUMERIC_EVENT_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_NUMERIC_EVENT_LEDGER_2026-05-17.jsonl"
SYMBOL_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SUMMARY_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
CONTRACT_RESULT = ROUTE_DIR / f"{CONTRACT_PREFIX}_RESULT_2026-05-17.json"
REPLAY_SCOPE_CONTRACT_LEDGER = ROUTE_DIR / f"{CONTRACT_PREFIX}_REPLAY_SCOPE_CONTRACT_LEDGER_2026-05-17.jsonl"
CONTROL_POPULATION_CONTRACT_LEDGER = ROUTE_DIR / f"{CONTRACT_PREFIX}_CONTROL_POPULATION_CONTRACT_LEDGER_2026-05-17.jsonl"
BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_replay_numeric_execution_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_replay_numeric_execution.py"


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


def expected_source_count(
    replay_contracts: list[dict[str, Any]],
    control_contracts: list[dict[str, Any]],
) -> int:
    paths = {str(row.get("market_source_path") or "") for row in replay_contracts if row.get("market_source_path")}
    paths.update(str(row.get("source_path") or "") for row in control_contracts if row.get("source_path"))
    return len(paths)


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    contract_result = read_json(CONTRACT_RESULT)
    replay_contracts = read_jsonl(REPLAY_SCOPE_CONTRACT_LEDGER)
    control_contracts = read_jsonl(CONTROL_POPULATION_CONTRACT_LEDGER)
    ledgers = {
        "source_numeric_metric_rows": read_jsonl(SOURCE_NUMERIC_METRIC_LEDGER),
        "replay_numeric_event_rows": read_jsonl(REPLAY_NUMERIC_EVENT_LEDGER),
        "control_numeric_event_rows": read_jsonl(CONTROL_NUMERIC_EVENT_LEDGER),
        "symbol_summary_rows": read_jsonl(SYMBOL_SUMMARY_LEDGER),
        "system_action_rows": read_jsonl(SYSTEM_ACTION_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")
    expected = {
        "input_replay_scope_contract_rows": 5324,
        "input_control_population_contract_rows": 173,
        "replay_numeric_event_rows": 5324,
        "control_numeric_event_rows": 173,
        "system_action_rows": 1,
        "source_numeric_metric_failures": 0,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")
    expected_sources = expected_source_count(replay_contracts, control_contracts)
    if counts.get("source_numeric_metric_rows") != expected_sources:
        issues.append(f"source_numeric_metric_rows expected {expected_sources} got {counts.get('source_numeric_metric_rows')}")
    if counts.get("replay_numeric_event_rows") != contract_result.get("counts", {}).get("replay_scope_contract_rows"):
        issues.append("replay numeric denominator does not match upstream replay contracts")
    if counts.get("control_numeric_event_rows") != contract_result.get("counts", {}).get("control_population_contract_rows"):
        issues.append("control numeric denominator does not match upstream control contracts")
    if not result.get("replay_contract_denominator_preserved"):
        issues.append("result does not mark replay contract denominator preserved")
    if not result.get("control_contract_denominator_preserved"):
        issues.append("result does not mark control contract denominator preserved")
    metric_status_counts = Counter(
        str(row.get("numeric_metric_status") or "") for row in ledgers["source_numeric_metric_rows"]
    )
    replay_status_counts = Counter(
        str(row.get("replay_numeric_event_status") or "") for row in ledgers["replay_numeric_event_rows"]
    )
    control_status_counts = Counter(
        str(row.get("control_numeric_event_status") or "") for row in ledgers["control_numeric_event_rows"]
    )
    if metric_status_counts.get("SOURCE_NUMERIC_REPAIR_REQUIRED", 0):
        issues.append("source metric repair-required rows present")
    if replay_status_counts.get("REPLAY_NUMERIC_EVENT_SOURCE_REPAIR_REQUIRED", 0):
        issues.append("replay numeric source repair-required rows present")
    if control_status_counts.get("CONTROL_NUMERIC_EVENT_SOURCE_REPAIR_REQUIRED", 0):
        issues.append("control numeric source repair-required rows present")
    for key, rows in ledgers.items():
        sample = rows[:20] if key == "replay_numeric_event_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")
    files_to_scan = [
        RESULT_PATH,
        SOURCE_NUMERIC_METRIC_LEDGER,
        REPLAY_NUMERIC_EVENT_LEDGER,
        CONTROL_NUMERIC_EVENT_LEDGER,
        SYMBOL_SUMMARY_LEDGER,
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
        "metric_status_counts": dict(sorted(metric_status_counts.items())),
        "replay_status_counts": dict(sorted(replay_status_counts.items())),
        "control_status_counts": dict(sorted(control_status_counts.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
