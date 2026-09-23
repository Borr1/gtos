#!/usr/bin/env python3
"""Verify runtime replay inventory alignment artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_INVENTORY_ALIGNMENT"
RECOMMENDATION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_RECOMMENDATION"
UNIFIED_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_UNIFIED_SYSTEM_RECOMMENDATION_MERGE_BUNDLE"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SIGNAL_INVENTORY_ALIGNMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_SIGNAL_INVENTORY_ALIGNMENT_LEDGER_2026-05-17.jsonl"
SYMBOL_INVENTORY_ALIGNMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_INVENTORY_ALIGNMENT_LEDGER_2026-05-17.jsonl"
SYSTEM_INVENTORY_ALIGNMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_INVENTORY_ALIGNMENT_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

SIGNAL_ROUTE_LEDGER = ROUTE_DIR / f"{RECOMMENDATION_PREFIX}_SIGNAL_ROUTE_LEDGER_2026-05-17.jsonl"
UNIFIED_CANDIDATE_LEDGER = ROUTE_DIR / f"{UNIFIED_PREFIX}_UNIFIED_CANDIDATE_LEDGER_2026-05-17.jsonl"
BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_inventory_alignment_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_runtime_replay_inventory_alignment.py"


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
    input_signal_rows = read_jsonl(SIGNAL_ROUTE_LEDGER)
    input_unified_rows = read_jsonl(UNIFIED_CANDIDATE_LEDGER)
    ledgers = {
        "signal_inventory_alignment_rows": read_jsonl(SIGNAL_INVENTORY_ALIGNMENT_LEDGER),
        "symbol_inventory_alignment_rows": read_jsonl(SYMBOL_INVENTORY_ALIGNMENT_LEDGER),
        "system_inventory_alignment_rows": read_jsonl(SYSTEM_INVENTORY_ALIGNMENT_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    alignment_classes = Counter(
        str(row.get("inventory_alignment_class")) for row in ledgers["signal_inventory_alignment_rows"]
    )
    expected = {
        "input_signal_route_rows": len(input_signal_rows),
        "input_unified_candidate_rows": len(input_unified_rows),
        "signal_inventory_alignment_rows": len(input_signal_rows),
        "system_inventory_alignment_rows": 1,
        "exact_scope_compatible_rows": alignment_classes.get("INVENTORY_ALIGNMENT_EXACT_SCOPE_COMPATIBLE", 0),
        "exact_scope_present_different_action_rows": alignment_classes.get(
            "INVENTORY_ALIGNMENT_EXACT_SCOPE_PRESENT_DIFFERENT_ACTION", 0
        ),
        "broad_scope_compatible_rows": alignment_classes.get("INVENTORY_ALIGNMENT_BROAD_SCOPE_COMPATIBLE", 0),
        "broad_scope_present_different_action_rows": alignment_classes.get(
            "INVENTORY_ALIGNMENT_BROAD_SCOPE_PRESENT_DIFFERENT_ACTION", 0
        ),
        "no_scope_inventory_rows": alignment_classes.get("INVENTORY_ALIGNMENT_NO_SCOPE_IN_UNIFIED_INVENTORY", 0),
        "replay_scope_unmatched_review_rows": alignment_classes.get(
            "INVENTORY_ALIGNMENT_REPLAY_SCOPE_UNMATCHED_REVIEW", 0
        ),
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")
    if sum(alignment_classes.values()) != len(input_signal_rows):
        issues.append("alignment classes do not preserve signal route denominator")
    if not ledgers["system_inventory_alignment_rows"][0].get("system_inventory_alignment"):
        issues.append("system inventory alignment row missing text")

    for key, rows in ledgers.items():
        sample = rows[:100] if key == "source_manifest_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        SIGNAL_INVENTORY_ALIGNMENT_LEDGER,
        SYMBOL_INVENTORY_ALIGNMENT_LEDGER,
        SYSTEM_INVENTORY_ALIGNMENT_LEDGER,
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
        "inventory_alignment_class_counts": dict(sorted(alignment_classes.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
