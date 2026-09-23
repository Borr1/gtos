#!/usr/bin/env python3
"""Verify repaired-proxy score bridge rebuild artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SCORE_BRIDGE_REBUILD"
SCORE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPLAY_SCORE_RERUN"
BRIDGE_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_EXECUTION_SPECS"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"
SCOPE_JOIN_FIELDS = ("symbol", "route_session", "horizon_id", "source_component")

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SCORE_SCOPE_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORE_SCOPE_SUMMARY_LEDGER_2026-05-17.jsonl"
REBUILT_BRIDGE_LEDGER = ROUTE_DIR / f"{PREFIX}_REBUILT_EXACT_PROXY_BRIDGE_LEDGER_2026-05-17.jsonl"
REPAIR_CONTEXT_BRIDGE_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_CONTEXT_BRIDGE_LEDGER_2026-05-17.jsonl"
MISSING_SCORE_SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_MISSING_SCORE_SCOPE_LEDGER_2026-05-17.jsonl"
SYMBOL_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SUMMARY_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

SCORE_RESULT = ROUTE_DIR / f"{SCORE_PREFIX}_RESULT_2026-05-17.json"
SCORE_RERUN_LEDGER = ROUTE_DIR / f"{SCORE_PREFIX}_SCORE_RERUN_LEDGER_2026-05-17.jsonl"
EXACT_PROXY_BRIDGE_LEDGER = ROUTE_DIR / f"{BRIDGE_PREFIX}_EXACT_PROXY_BRIDGE_LEDGER_2026-05-17.jsonl"
BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_score_bridge_rebuild_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_score_bridge_rebuild.py"


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


def aggregate_scope_key(row: dict[str, Any]) -> str:
    existing = row.get("aggregate_scope_key")
    if existing:
        return str(existing)
    return "|".join(
        f"{field}={row.get(field) or ''}"
        for field in SCOPE_JOIN_FIELDS
    )


def scope_join_tuple(row: dict[str, Any]) -> tuple[str, ...]:
    return tuple("" if row.get(field) is None else str(row.get(field)) for field in SCOPE_JOIN_FIELDS)


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
    score_result = read_json(SCORE_RESULT)
    score_rows = read_jsonl(SCORE_RERUN_LEDGER)
    original_bridge_rows = read_jsonl(EXACT_PROXY_BRIDGE_LEDGER)
    ledgers = {
        "score_scope_summary_rows": read_jsonl(SCORE_SCOPE_SUMMARY_LEDGER),
        "rebuilt_exact_proxy_bridge_rows": read_jsonl(REBUILT_BRIDGE_LEDGER),
        "repair_context_bridge_rows": read_jsonl(REPAIR_CONTEXT_BRIDGE_LEDGER),
        "missing_score_scope_rows": read_jsonl(MISSING_SCORE_SCOPE_LEDGER),
        "symbol_summary_rows": read_jsonl(SYMBOL_SUMMARY_LEDGER),
        "system_action_rows": read_jsonl(SYSTEM_ACTION_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")
    expected_scopes = len({str(row.get("aggregate_scope_key") or "") for row in score_rows})
    expected = {
        "input_score_rerun_rows": 5324,
        "input_exact_proxy_bridge_rows": 17916,
        "score_scope_summary_rows": expected_scopes,
        "rebuilt_exact_proxy_bridge_rows": 17916,
        "system_action_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")
    if counts.get("input_score_rerun_rows") != score_result.get("counts", {}).get("score_rerun_rows"):
        issues.append("input score count does not match score-rerun result")
    if counts.get("rebuilt_exact_proxy_bridge_rows") != len(original_bridge_rows):
        issues.append("rebuilt bridge denominator does not match original bridge rows")
    if not result.get("bridge_denominator_preserved"):
        issues.append("result does not mark bridge denominator preserved")
    status_counts = Counter(
        str(row.get("score_bridge_rebuild_status") or "") for row in ledgers["rebuilt_exact_proxy_bridge_rows"]
    )
    join_method_counts = Counter(
        str(row.get("score_scope_join_method") or "") for row in ledgers["rebuilt_exact_proxy_bridge_rows"]
    )
    score_scope_keys = {str(row.get("aggregate_scope_key") or "") for row in ledgers["score_scope_summary_rows"]}
    score_scope_tuples = {scope_join_tuple(row) for row in ledgers["score_scope_summary_rows"]}
    expected_missing = sum(
        1
        for row in original_bridge_rows
        if aggregate_scope_key(row) not in score_scope_keys and scope_join_tuple(row) not in score_scope_tuples
    )
    expected_joined = len(original_bridge_rows) - expected_missing
    if counts.get("score_scope_joined_rows") != expected_joined:
        issues.append(f"score_scope_joined_rows expected {expected_joined} got {counts.get('score_scope_joined_rows')}")
    if counts.get("missing_score_scope_rows") != expected_missing:
        issues.append(f"missing_score_scope_rows expected {expected_missing} got {counts.get('missing_score_scope_rows')}")
    if counts.get("missing_score_scope_rows") == counts.get("rebuilt_exact_proxy_bridge_rows"):
        issues.append("score bridge rebuild joined zero rows")
    if counts.get("missing_score_scope_rows") != status_counts.get("SCORE_BRIDGE_REBUILT_NO_REPLAY_SCORE_SCOPE_MATCH", 0):
        issues.append("missing score-scope row count mismatch")
    if counts.get("repair_context_bridge_rows") != status_counts.get("SCORE_BRIDGE_REBUILT_WITH_REPAIR_CONTEXT_SCOPE", 0):
        issues.append("repair context bridge row count mismatch")
    if join_method_counts.get("computed_aggregate_scope_key", 0) <= 0:
        issues.append("no rows joined through computed aggregate scope key")
    if join_method_counts.get("no_replay_score_scope_match", 0) != expected_missing:
        issues.append("no-match join method count does not match expected missing rows")
    joined_rows = [
        row for row in ledgers["rebuilt_exact_proxy_bridge_rows"]
        if row.get("score_bridge_rebuild_status") != "SCORE_BRIDGE_REBUILT_NO_REPLAY_SCORE_SCOPE_MATCH"
    ]
    if any(not row.get("input_score_scope_summary_row_id") for row in joined_rows[:100]):
        issues.append("sample joined bridge rows do not carry score scope summary ids")
    for key, rows in ledgers.items():
        sample = rows[:20] if key == "rebuilt_exact_proxy_bridge_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")
    files_to_scan = [
        RESULT_PATH,
        SCORE_SCOPE_SUMMARY_LEDGER,
        REBUILT_BRIDGE_LEDGER,
        REPAIR_CONTEXT_BRIDGE_LEDGER,
        MISSING_SCORE_SCOPE_LEDGER,
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
        "bridge_status_counts": dict(sorted(status_counts.items())),
        "score_scope_join_method_counts": dict(sorted(join_method_counts.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
