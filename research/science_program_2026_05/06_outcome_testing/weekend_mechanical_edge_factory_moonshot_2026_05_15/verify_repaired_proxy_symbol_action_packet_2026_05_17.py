#!/usr/bin/env python3
"""Verify repaired-proxy symbol action packet artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SYMBOL_ACTION_PACKET"
EXEC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_COMPARATOR_EXECUTION"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"
REGISTER_ACTIONS = {
    "REGISTER_DEFAULT_OFF_SCORER_COMPARATOR",
    "REGISTER_AVOID_REDESIGN_COMPARATOR",
}

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SYMBOL_ACTION_PACKET_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_ACTION_PACKET_LEDGER_2026-05-17.jsonl"
COMPARATOR_REGISTRATION_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPARATOR_REGISTRATION_LEDGER_2026-05-17.jsonl"
COMPARATOR_NONREGISTRATION_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPARATOR_NONREGISTRATION_LEDGER_2026-05-17.jsonl"
SYMBOL_PROXY_SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_PROXY_SURFACE_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

COMPARATOR_EXECUTION_LEDGER = ROUTE_DIR / f"{EXEC_PREFIX}_COMPARATOR_EXECUTION_LEDGER_2026-05-17.jsonl"
BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_symbol_action_packet_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_symbol_action_packet.py"


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


def symbol_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (str(row.get("symbol") or ""), str(row.get("route_session") or ""), str(row.get("horizon_id") or ""))


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    input_rows = read_jsonl(COMPARATOR_EXECUTION_LEDGER)
    ledgers = {
        "symbol_action_packet_rows": read_jsonl(SYMBOL_ACTION_PACKET_LEDGER),
        "comparator_registration_rows": read_jsonl(COMPARATOR_REGISTRATION_LEDGER),
        "comparator_nonregistration_rows": read_jsonl(COMPARATOR_NONREGISTRATION_LEDGER),
        "symbol_proxy_surface_rows": read_jsonl(SYMBOL_PROXY_SURFACE_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "system_action_rows": read_jsonl(SYSTEM_ACTION_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    expected_packets = len({symbol_key(row) for row in input_rows})
    expected_registration = sum(1 for row in input_rows if str(row.get("comparator_execution_action") or "") in REGISTER_ACTIONS)
    expected_nonregistration = len(input_rows) - expected_registration
    expected = {
        "input_comparator_execution_rows": len(input_rows),
        "symbol_action_packet_rows": expected_packets,
        "comparator_registration_rows": expected_registration,
        "comparator_nonregistration_rows": expected_nonregistration,
        "symbol_proxy_surface_rows": expected_packets,
        "system_action_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")

    packet_total = sum(int(row.get("comparator_execution_rows") or 0) for row in ledgers["symbol_action_packet_rows"])
    if packet_total != len(input_rows):
        issues.append("symbol action packet rows do not preserve comparator execution denominator")
    registration_actions = Counter(str(row.get("registration_family")) for row in ledgers["comparator_registration_rows"])
    nonregistration_actions = Counter(str(row.get("comparator_execution_action")) for row in ledgers["comparator_nonregistration_rows"])
    if sum(registration_actions.values()) != expected_registration:
        issues.append("registration rows do not preserve register-action denominator")
    if sum(nonregistration_actions.values()) != expected_nonregistration:
        issues.append("nonregistration rows do not preserve nonregister-action denominator")

    for key, rows in ledgers.items():
        sample = rows[:100] if key in {"source_manifest_rows"} else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        SYMBOL_ACTION_PACKET_LEDGER,
        COMPARATOR_REGISTRATION_LEDGER,
        COMPARATOR_NONREGISTRATION_LEDGER,
        SYMBOL_PROXY_SURFACE_LEDGER,
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
        "registration_family_counts": dict(sorted(registration_actions.items())),
        "nonregistration_action_counts": dict(sorted(nonregistration_actions.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
