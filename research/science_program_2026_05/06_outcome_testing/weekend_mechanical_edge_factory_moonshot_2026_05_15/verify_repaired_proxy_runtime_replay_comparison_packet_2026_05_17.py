#!/usr/bin/env python3
"""Verify runtime replay comparison packet artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_COMPARISON_PACKET"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_ADVANCEMENT"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
COMPARISON_PACKET_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPARISON_PACKET_LEDGER_2026-05-17.jsonl"
REVIEW_SIDECAR_LEDGER = ROUTE_DIR / f"{PREFIX}_REVIEW_SIDECAR_LEDGER_2026-05-17.jsonl"
COMPARISON_SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPARISON_SCOPE_LEDGER_2026-05-17.jsonl"
SYSTEM_COMPARISON_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_COMPARISON_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
REPRESENTED_SURFACE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REPRESENTED_SURFACE_LEDGER_2026-05-17.jsonl"
ACTION_CONFLICT_REVIEW_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ACTION_CONFLICT_REVIEW_LEDGER_2026-05-17.jsonl"
UNMATCHED_SCOPE_ADVANCEMENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_UNMATCHED_SCOPE_ADVANCEMENT_LEDGER_2026-05-17.jsonl"
SYMBOL_ADVANCEMENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYMBOL_ADVANCEMENT_LEDGER_2026-05-17.jsonl"
SYSTEM_ADVANCEMENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYSTEM_ADVANCEMENT_LEDGER_2026-05-17.jsonl"

BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_comparison_packet_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_runtime_replay_comparison_packet.py"


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


def scope_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("symbol") or ""),
        str(row.get("route_session") or ""),
        str(row.get("horizon_id") or ""),
        str(row.get("registry_family") or ""),
    )


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    input_result = read_json(INPUT_RESULT)
    represented_rows = read_jsonl(REPRESENTED_SURFACE_LEDGER)
    action_conflict_rows = read_jsonl(ACTION_CONFLICT_REVIEW_LEDGER)
    unmatched_rows = read_jsonl(UNMATCHED_SCOPE_ADVANCEMENT_LEDGER)
    symbol_advancement_rows = read_jsonl(SYMBOL_ADVANCEMENT_LEDGER)
    system_advancement_rows = read_jsonl(SYSTEM_ADVANCEMENT_LEDGER)
    ledgers = {
        "comparison_packet_rows": read_jsonl(COMPARISON_PACKET_LEDGER),
        "review_sidecar_rows": read_jsonl(REVIEW_SIDECAR_LEDGER),
        "comparison_scope_rows": read_jsonl(COMPARISON_SCOPE_LEDGER),
        "system_comparison_rows": read_jsonl(SYSTEM_COMPARISON_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    packet_rows = ledgers["comparison_packet_rows"]
    sidecar_rows = ledgers["review_sidecar_rows"]
    packet_roles = Counter(str(row.get("comparison_packet_role")) for row in packet_rows)
    sidecar_families = Counter(str(row.get("review_sidecar_family")) for row in sidecar_rows)
    expected = {
        "input_advancement_result_ok": int(bool(input_result.get("ok"))),
        "input_represented_surface_rows": len(represented_rows),
        "input_action_conflict_review_rows": len(action_conflict_rows),
        "input_unmatched_scope_advancement_rows": len(unmatched_rows),
        "input_symbol_advancement_rows": len(symbol_advancement_rows),
        "input_system_advancement_rows": len(system_advancement_rows),
        "comparison_packet_rows": len(represented_rows),
        "default_off_comparison_packet_rows": packet_roles.get("DEFAULT_OFF_REPLAY_SIGNAL_COMPARISON_INPUT", 0),
        "avoid_redesign_comparison_packet_rows": packet_roles.get("AVOID_REDESIGN_REPLAY_SIGNAL_COMPARISON_INPUT", 0),
        "represented_context_comparison_packet_rows": packet_roles.get(
            "REPRESENTED_REPLAY_CONTEXT_COMPARISON_INPUT", 0
        ),
        "review_sidecar_rows": len(action_conflict_rows) + len(unmatched_rows),
        "action_conflict_review_sidecar_rows": sidecar_families.get("ACTION_CONFLICT_REVIEW_SIDECAR", 0),
        "unmatched_scope_review_sidecar_rows": sidecar_families.get("UNMATCHED_SCOPE_REVIEW_SIDECAR", 0),
        "system_comparison_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")

    if len(packet_rows) != len(represented_rows):
        issues.append("comparison packet rows do not preserve represented surface denominator")
    if len(sidecar_rows) != len(action_conflict_rows) + len(unmatched_rows):
        issues.append("review sidecars do not preserve review input denominator")
    expected_scope_count = len({scope_key(row) for row in packet_rows + sidecar_rows})
    if counts.get("comparison_scope_rows") != expected_scope_count:
        issues.append(f"comparison_scope_rows expected {expected_scope_count} got {counts.get('comparison_scope_rows')}")
    if not ledgers["system_comparison_rows"][0].get("system_comparison"):
        issues.append("system comparison row missing text")

    for key, rows in ledgers.items():
        sample = rows[:100] if key == "source_manifest_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")
    if not boundary_ok(result):
        issues.append("result is outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        COMPARISON_PACKET_LEDGER,
        REVIEW_SIDECAR_LEDGER,
        COMPARISON_SCOPE_LEDGER,
        SYSTEM_COMPARISON_LEDGER,
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
        "comparison_packet_role_counts": dict(sorted(packet_roles.items())),
        "review_sidecar_family_counts": dict(sorted(sidecar_families.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
