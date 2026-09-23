#!/usr/bin/env python3
"""Verify repaired-proxy score bridge action packet artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCORE_BRIDGE_ACTION_PACKET"
SCORE_BRIDGE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCORE_BRIDGE_REBUILD"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ACTION_SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_ACTION_SCOPE_LEDGER_2026-05-17.jsonl"
COMPARATOR_PACKET_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPARATOR_PACKET_LEDGER_2026-05-17.jsonl"
REPAIR_ROUTING_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_ROUTING_LEDGER_2026-05-17.jsonl"
SYMBOL_MARKET_PACKET_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_MARKET_PACKET_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

SCORE_BRIDGE_RESULT = ROUTE_DIR / f"{SCORE_BRIDGE_PREFIX}_RESULT_2026-05-17.json"
REBUILT_BRIDGE_LEDGER = ROUTE_DIR / f"{SCORE_BRIDGE_PREFIX}_REBUILT_EXACT_PROXY_BRIDGE_LEDGER_2026-05-17.jsonl"
REPAIR_CONTEXT_BRIDGE_LEDGER = ROUTE_DIR / f"{SCORE_BRIDGE_PREFIX}_REPAIR_CONTEXT_BRIDGE_LEDGER_2026-05-17.jsonl"
MISSING_SCORE_SCOPE_LEDGER = ROUTE_DIR / f"{SCORE_BRIDGE_PREFIX}_MISSING_SCORE_SCOPE_LEDGER_2026-05-17.jsonl"
BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_score_bridge_action_packet_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_score_bridge_action_packet.py"


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


def action_group_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        str(row.get("symbol") or ""),
        str(row.get("route_session") or ""),
        str(row.get("horizon_id") or ""),
        str(row.get("source_component") or ""),
        str(row.get("rerun_registry_family") or ""),
        str(row.get("score_bridge_rebuild_status") or ""),
        str(row.get("score_bridge_next_action") or ""),
    )


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    score_bridge_result = read_json(SCORE_BRIDGE_RESULT)
    bridge_rows = read_jsonl(REBUILT_BRIDGE_LEDGER)
    repair_context_rows = read_jsonl(REPAIR_CONTEXT_BRIDGE_LEDGER)
    missing_rows = read_jsonl(MISSING_SCORE_SCOPE_LEDGER)
    ledgers = {
        "action_scope_rows": read_jsonl(ACTION_SCOPE_LEDGER),
        "comparator_packet_rows": read_jsonl(COMPARATOR_PACKET_LEDGER),
        "repair_routing_rows": read_jsonl(REPAIR_ROUTING_LEDGER),
        "symbol_market_packet_rows": read_jsonl(SYMBOL_MARKET_PACKET_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "system_action_rows": read_jsonl(SYSTEM_ACTION_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    expected_action_scopes = len({action_group_key(row) for row in bridge_rows})
    expected_comparator_scopes = len(
        {
            action_group_key(row)
            for row in bridge_rows
            if row.get("score_bridge_rebuild_status") == "SCORE_BRIDGE_REBUILT_WITH_REPLAY_SCORE_SCOPE"
        }
    )
    expected_repair_routes = len(repair_context_rows) + len(missing_rows)
    expected = {
        "input_rebuilt_bridge_rows": score_bridge_result.get("counts", {}).get("rebuilt_exact_proxy_bridge_rows"),
        "input_repair_context_bridge_rows": score_bridge_result.get("counts", {}).get("repair_context_bridge_rows"),
        "input_missing_score_scope_rows": score_bridge_result.get("counts", {}).get("missing_score_scope_rows"),
        "action_scope_rows": expected_action_scopes,
        "comparator_packet_rows": expected_comparator_scopes,
        "repair_routing_rows": expected_repair_routes,
        "system_action_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")

    if not result.get("bridge_denominator_preserved"):
        issues.append("result does not mark bridge denominator preserved")
    if not result.get("repair_routing_denominator_preserved"):
        issues.append("result does not mark repair routing denominator preserved")
    action_bridge_sum = sum(int(row.get("bridge_rows") or 0) for row in ledgers["action_scope_rows"])
    if action_bridge_sum != len(bridge_rows):
        issues.append(f"action scope bridge row sum expected {len(bridge_rows)} got {action_bridge_sum}")
    repair_family_counts = Counter(str(row.get("repair_route_family") or "") for row in ledgers["repair_routing_rows"])
    if repair_family_counts.get("IDENTIFIER_LINKAGE_REPAIR_REQUIRED", 0) != len(repair_context_rows):
        issues.append("repair-context rows are not fully routed to identifier linkage repair")
    if repair_family_counts.get("SCOPE_IDENTITY_REPAIR_REQUIRED", 0) != len(missing_rows):
        issues.append("missing score-scope rows are not fully routed to scope identity repair")
    packet_status_counts = Counter(
        str(row.get("comparator_packet_status") or "") for row in ledgers["comparator_packet_rows"]
    )
    if not packet_status_counts:
        issues.append("no comparator packet rows emitted")

    for key, rows in ledgers.items():
        sample = rows[:50] if key in {"action_scope_rows", "comparator_packet_rows", "repair_routing_rows"} else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        ACTION_SCOPE_LEDGER,
        COMPARATOR_PACKET_LEDGER,
        REPAIR_ROUTING_LEDGER,
        SYMBOL_MARKET_PACKET_LEDGER,
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
        "repair_route_family_counts": dict(sorted(repair_family_counts.items())),
        "comparator_packet_status_counts": dict(sorted(packet_status_counts.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
