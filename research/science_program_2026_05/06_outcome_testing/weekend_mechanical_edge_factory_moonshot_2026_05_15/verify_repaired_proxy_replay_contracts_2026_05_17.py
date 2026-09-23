#!/usr/bin/env python3
"""Verify repaired-proxy replay contract artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPLAY_CONTRACTS"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_EXECUTION_REGISTRY"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SOURCE_PROBE_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_PROBE_LEDGER_2026-05-17.jsonl"
REPAIR_SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_SCOPE_LEDGER_2026-05-17.jsonl"
REPLAY_SCOPE_CONTRACT_LEDGER = ROUTE_DIR / f"{PREFIX}_REPLAY_SCOPE_CONTRACT_LEDGER_2026-05-17.jsonl"
CONTROL_POPULATION_CONTRACT_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_POPULATION_CONTRACT_LEDGER_2026-05-17.jsonl"
SYMBOL_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SUMMARY_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
DEFAULT_SCOPE_REGISTRY_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_DEFAULT_SCOPE_REGISTRY_LEDGER_2026-05-17.jsonl"
AVOID_SCOPE_REGISTRY_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_AVOID_SCOPE_REGISTRY_LEDGER_2026-05-17.jsonl"
MARKET_REPLAY_NUMERIC_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_MARKET_REPLAY_NUMERIC_POPULATION_LEDGER_2026-05-17.jsonl"
BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_replay_contracts_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_replay_population.py"


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


def expected_contract_counts(
    default_scopes: list[dict[str, Any]],
    avoid_scopes: list[dict[str, Any]],
    repair_scopes: list[dict[str, Any]],
    market_rows: list[dict[str, Any]],
) -> tuple[int, int]:
    scopes_by_symbol = Counter(str(row.get("symbol") or "") for row in [*default_scopes, *avoid_scopes, *repair_scopes])
    market_by_symbol = Counter(str(row.get("symbol") or "") for row in market_rows)
    contract_rows = sum(scopes_by_symbol[symbol] * market_count for symbol, market_count in market_by_symbol.items())
    control_rows = sum(market_count for symbol, market_count in market_by_symbol.items() if not scopes_by_symbol[symbol])
    return contract_rows, control_rows


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    input_result = read_json(INPUT_RESULT)
    default_scopes = read_jsonl(DEFAULT_SCOPE_REGISTRY_LEDGER)
    avoid_scopes = read_jsonl(AVOID_SCOPE_REGISTRY_LEDGER)
    market_rows = read_jsonl(MARKET_REPLAY_NUMERIC_LEDGER)
    ledgers = {
        "source_probe_rows": read_jsonl(SOURCE_PROBE_LEDGER),
        "repair_scope_rows": read_jsonl(REPAIR_SCOPE_LEDGER),
        "replay_scope_contract_rows": read_jsonl(REPLAY_SCOPE_CONTRACT_LEDGER),
        "control_population_contract_rows": read_jsonl(CONTROL_POPULATION_CONTRACT_LEDGER),
        "symbol_summary_rows": read_jsonl(SYMBOL_SUMMARY_LEDGER),
        "system_action_rows": read_jsonl(SYSTEM_ACTION_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")
    expected_static = {
        "input_default_scope_rows": 102,
        "input_avoid_scope_rows": 154,
        "input_repair_execution_rows": 170,
        "input_market_population_rows": 301,
        "source_probe_rows": 301,
        "repair_scope_rows": 34,
        "system_action_rows": 1,
    }
    for key, value in expected_static.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")
    expected_contracts, expected_controls = expected_contract_counts(
        default_scopes,
        avoid_scopes,
        ledgers["repair_scope_rows"],
        market_rows,
    )
    if counts.get("replay_scope_contract_rows") != expected_contracts:
        issues.append(
            f"replay_scope_contract_rows expected {expected_contracts} got {counts.get('replay_scope_contract_rows')}"
        )
    if counts.get("control_population_contract_rows") != expected_controls:
        issues.append(
            "control_population_contract_rows expected "
            f"{expected_controls} got {counts.get('control_population_contract_rows')}"
        )
    if counts.get("source_probe_rows") != input_result.get("counts", {}).get("market_replay_numeric_population_rows"):
        issues.append("source probe denominator does not match upstream market replay population")
    if not result.get("market_population_denominator_preserved"):
        issues.append("result does not mark market population denominator preserved")
    for key, rows in ledgers.items():
        sample = rows[:20] if key == "replay_scope_contract_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")
    files_to_scan = [
        RESULT_PATH,
        SOURCE_PROBE_LEDGER,
        REPAIR_SCOPE_LEDGER,
        REPLAY_SCOPE_CONTRACT_LEDGER,
        CONTROL_POPULATION_CONTRACT_LEDGER,
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
    action_counts = Counter(str(row.get("replay_contract_action") or "") for row in ledgers["replay_scope_contract_rows"])
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": {key: counts.get(key) for key in sorted(counts)},
        "replay_contract_action_counts": dict(sorted(action_counts.items())),
        "source_probe_failures": result.get("source_probe_failures"),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
