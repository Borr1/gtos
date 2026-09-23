#!/usr/bin/env python3
"""Verify runtime replay recommendation artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_RECOMMENDATION"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_EXECUTION"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SIGNAL_ROUTE_LEDGER = ROUTE_DIR / f"{PREFIX}_SIGNAL_ROUTE_LEDGER_2026-05-17.jsonl"
SYMBOL_RECOMMENDATION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_RECOMMENDATION_LEDGER_2026-05-17.jsonl"
UNMATCHED_SCOPE_REVIEW_LEDGER = ROUTE_DIR / f"{PREFIX}_UNMATCHED_SCOPE_REVIEW_LEDGER_2026-05-17.jsonl"
REPAIR_CONTEXT_RECOMMENDATION_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_CONTEXT_RECOMMENDATION_LEDGER_2026-05-17.jsonl"
NONREGISTRATION_RECOMMENDATION_LEDGER = ROUTE_DIR / f"{PREFIX}_NONREGISTRATION_RECOMMENDATION_LEDGER_2026-05-17.jsonl"
SYSTEM_RECOMMENDATION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_RECOMMENDATION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

REPLAY_EXECUTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REPLAY_EXECUTION_LEDGER_2026-05-17.jsonl"
SYMBOL_OUTCOME_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYMBOL_OUTCOME_LEDGER_2026-05-17.jsonl"
NONREGISTRATION_REPLAY_CARRY_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NONREGISTRATION_REPLAY_CARRY_LEDGER_2026-05-17.jsonl"
BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_recommendation_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_runtime_replay_recommendation.py"


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
    input_execution_rows = read_jsonl(REPLAY_EXECUTION_LEDGER)
    input_symbol_rows = read_jsonl(SYMBOL_OUTCOME_LEDGER)
    input_nonregistration_rows = read_jsonl(NONREGISTRATION_REPLAY_CARRY_LEDGER)
    ledgers = {
        "replay_signal_route_rows": read_jsonl(SIGNAL_ROUTE_LEDGER),
        "symbol_recommendation_rows": read_jsonl(SYMBOL_RECOMMENDATION_LEDGER),
        "unmatched_scope_review_rows": read_jsonl(UNMATCHED_SCOPE_REVIEW_LEDGER),
        "repair_context_recommendation_rows": read_jsonl(REPAIR_CONTEXT_RECOMMENDATION_LEDGER),
        "nonregistration_recommendation_rows": read_jsonl(NONREGISTRATION_RECOMMENDATION_LEDGER),
        "system_recommendation_rows": read_jsonl(SYSTEM_RECOMMENDATION_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    route_counts = Counter(str(row.get("replay_signal_route_class")) for row in ledgers["replay_signal_route_rows"])
    symbol_recommendations = Counter(
        str(row.get("symbol_recommendation")) for row in ledgers["symbol_recommendation_rows"]
    )
    expected = {
        "input_replay_execution_rows": len(input_execution_rows),
        "input_symbol_outcome_rows": len(input_symbol_rows),
        "input_nonregistration_replay_carry_rows": len(input_nonregistration_rows),
        "replay_signal_route_rows": len(input_execution_rows),
        "symbol_recommendation_rows": len(input_symbol_rows),
        "unmatched_scope_review_rows": route_counts.get("REPLAY_SCOPE_UNMATCHED_REVIEW_BRANCH_LOCAL", 0),
        "repair_context_recommendation_rows": route_counts.get("REPLAY_REPAIR_CONTEXT_CARRY_BRANCH_LOCAL", 0),
        "nonregistration_recommendation_rows": len(input_nonregistration_rows),
        "system_recommendation_rows": 1,
        "default_off_signal_route_rows": route_counts.get("DEFAULT_OFF_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL", 0),
        "avoid_redesign_signal_route_rows": route_counts.get("AVOID_REDESIGN_REPLAY_SIGNAL_CANDIDATE_BRANCH_LOCAL", 0),
        "context_only_route_rows": route_counts.get("REPLAY_SIGNAL_CONTEXT_ONLY_BRANCH_LOCAL", 0),
        "default_off_symbol_recommendation_rows": symbol_recommendations.get(
            "BRANCH_LOCAL_DEFAULT_OFF_REPLAY_SIGNAL_RECOMMENDED_FOR_COMPARISON", 0
        ),
        "avoid_redesign_symbol_recommendation_rows": symbol_recommendations.get(
            "BRANCH_LOCAL_AVOID_REDESIGN_REPLAY_SIGNAL_RECOMMENDED_FOR_COMPARISON", 0
        ),
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")
    if sum(route_counts.values()) != len(input_execution_rows):
        issues.append("route class counts do not preserve replay execution denominator")
    if not ledgers["system_recommendation_rows"][0].get("system_recommendation"):
        issues.append("system recommendation row missing recommendation text")

    for key, rows in ledgers.items():
        sample = rows[:100] if key == "source_manifest_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        SIGNAL_ROUTE_LEDGER,
        SYMBOL_RECOMMENDATION_LEDGER,
        UNMATCHED_SCOPE_REVIEW_LEDGER,
        REPAIR_CONTEXT_RECOMMENDATION_LEDGER,
        NONREGISTRATION_RECOMMENDATION_LEDGER,
        SYSTEM_RECOMMENDATION_LEDGER,
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
        "route_class_counts": dict(sorted(route_counts.items())),
        "symbol_recommendation_counts": dict(sorted(symbol_recommendations.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
