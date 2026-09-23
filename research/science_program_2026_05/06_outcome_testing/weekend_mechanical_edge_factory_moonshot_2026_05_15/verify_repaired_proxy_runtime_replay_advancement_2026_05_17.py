#!/usr/bin/env python3
"""Verify runtime replay advancement artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_ADVANCEMENT"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_INVENTORY_ALIGNMENT"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ADVANCEMENT_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_ADVANCEMENT_DECISION_LEDGER_2026-05-17.jsonl"
REPRESENTED_SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_REPRESENTED_SURFACE_LEDGER_2026-05-17.jsonl"
ACTION_CONFLICT_REVIEW_LEDGER = ROUTE_DIR / f"{PREFIX}_ACTION_CONFLICT_REVIEW_LEDGER_2026-05-17.jsonl"
UNMATCHED_SCOPE_ADVANCEMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_UNMATCHED_SCOPE_ADVANCEMENT_LEDGER_2026-05-17.jsonl"
SYMBOL_ADVANCEMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_ADVANCEMENT_LEDGER_2026-05-17.jsonl"
SYSTEM_ADVANCEMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ADVANCEMENT_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
SIGNAL_INVENTORY_ALIGNMENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SIGNAL_INVENTORY_ALIGNMENT_LEDGER_2026-05-17.jsonl"
SYMBOL_INVENTORY_ALIGNMENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYMBOL_INVENTORY_ALIGNMENT_LEDGER_2026-05-17.jsonl"
SYSTEM_INVENTORY_ALIGNMENT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYSTEM_INVENTORY_ALIGNMENT_LEDGER_2026-05-17.jsonl"

BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_advancement_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_runtime_replay_advancement.py"

REPRESENTED_FAMILIES = {
    "REPRESENTED_SIGNAL_ADVANCES",
    "REPRESENTED_CONTEXT_ADVANCES",
    "BROAD_SCOPE_COMPATIBLE_ADVANCES",
}
CONFLICT_FAMILIES = {
    "EXACT_SCOPE_ACTION_CONFLICT_REVIEW",
    "BROAD_SCOPE_ACTION_CONFLICT_REVIEW",
}
UNMATCHED_FAMILIES = {"UNMATCHED_SCOPE_REVIEW", "NO_SCOPE_INVENTORY_REVIEW"}


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
    input_signal_rows = read_jsonl(SIGNAL_INVENTORY_ALIGNMENT_LEDGER)
    input_symbol_rows = read_jsonl(SYMBOL_INVENTORY_ALIGNMENT_LEDGER)
    input_system_rows = read_jsonl(SYSTEM_INVENTORY_ALIGNMENT_LEDGER)
    ledgers = {
        "advancement_decision_rows": read_jsonl(ADVANCEMENT_DECISION_LEDGER),
        "represented_surface_rows": read_jsonl(REPRESENTED_SURFACE_LEDGER),
        "action_conflict_review_rows": read_jsonl(ACTION_CONFLICT_REVIEW_LEDGER),
        "unmatched_scope_advancement_rows": read_jsonl(UNMATCHED_SCOPE_ADVANCEMENT_LEDGER),
        "symbol_advancement_rows": read_jsonl(SYMBOL_ADVANCEMENT_LEDGER),
        "system_advancement_rows": read_jsonl(SYSTEM_ADVANCEMENT_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    decision_rows = ledgers["advancement_decision_rows"]
    family_counts = Counter(str(row.get("advancement_family")) for row in decision_rows)
    expected = {
        "input_inventory_alignment_result_ok": int(bool(input_result.get("ok"))),
        "input_signal_inventory_alignment_rows": len(input_signal_rows),
        "input_symbol_inventory_alignment_rows": len(input_symbol_rows),
        "input_system_inventory_alignment_rows": len(input_system_rows),
        "advancement_decision_rows": len(input_signal_rows),
        "represented_surface_rows": sum(family_counts.get(value, 0) for value in REPRESENTED_FAMILIES),
        "represented_signal_advancement_rows": family_counts.get("REPRESENTED_SIGNAL_ADVANCES", 0),
        "represented_context_advancement_rows": family_counts.get("REPRESENTED_CONTEXT_ADVANCES", 0),
        "broad_scope_compatible_advancement_rows": family_counts.get("BROAD_SCOPE_COMPATIBLE_ADVANCES", 0),
        "action_conflict_review_rows": sum(family_counts.get(value, 0) for value in CONFLICT_FAMILIES),
        "exact_scope_action_conflict_rows": family_counts.get("EXACT_SCOPE_ACTION_CONFLICT_REVIEW", 0),
        "broad_scope_action_conflict_rows": family_counts.get("BROAD_SCOPE_ACTION_CONFLICT_REVIEW", 0),
        "unmatched_scope_advancement_rows": sum(family_counts.get(value, 0) for value in UNMATCHED_FAMILIES),
        "system_advancement_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")

    if len(decision_rows) != len(input_signal_rows):
        issues.append("advancement decisions do not preserve inventory alignment denominator")
    if len(decision_rows) != (
        len(ledgers["represented_surface_rows"])
        + len(ledgers["action_conflict_review_rows"])
        + len(ledgers["unmatched_scope_advancement_rows"])
    ):
        issues.append("advancement split ledgers do not sum to decision denominator")
    if not ledgers["system_advancement_rows"][0].get("system_advancement"):
        issues.append("system advancement row missing text")

    for key, rows in ledgers.items():
        sample = rows[:100] if key == "source_manifest_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")
    if not boundary_ok(result):
        issues.append("result is outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        ADVANCEMENT_DECISION_LEDGER,
        REPRESENTED_SURFACE_LEDGER,
        ACTION_CONFLICT_REVIEW_LEDGER,
        UNMATCHED_SCOPE_ADVANCEMENT_LEDGER,
        SYMBOL_ADVANCEMENT_LEDGER,
        SYSTEM_ADVANCEMENT_LEDGER,
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
        "advancement_family_counts": dict(sorted(family_counts.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
