#!/usr/bin/env python3
"""Verify repaired-proxy runtime candidate registry artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_CANDIDATE_REGISTRY"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_CANDIDATE_BUNDLE"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
REGISTRY_MODULE_LEDGER = ROUTE_DIR / f"{PREFIX}_REGISTRY_MODULE_LEDGER_2026-05-17.jsonl"
EVENT_PROBE_LEDGER = ROUTE_DIR / f"{PREFIX}_EVENT_PROBE_LEDGER_2026-05-17.jsonl"
SYMBOL_REGISTRY_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_REGISTRY_ROLLUP_LEDGER_2026-05-17.jsonl"
NONREGISTRATION_REGISTRY_REVIEW_LEDGER = ROUTE_DIR / f"{PREFIX}_NONREGISTRATION_REGISTRY_REVIEW_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

RUNTIME_CANDIDATE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_RUNTIME_CANDIDATE_LEDGER_2026-05-17.jsonl"
GUARD_CHECK_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_GUARD_CHECK_LEDGER_2026-05-17.jsonl"
NONREGISTRATION_REVIEW_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NONREGISTRATION_REVIEW_LEDGER_2026-05-17.jsonl"
BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_candidate_registry_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_runtime_candidate_registry.py"


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
    input_candidate_rows = read_jsonl(RUNTIME_CANDIDATE_LEDGER)
    input_guard_rows = read_jsonl(GUARD_CHECK_LEDGER)
    input_nonregistration_rows = read_jsonl(NONREGISTRATION_REVIEW_LEDGER)
    ledgers = {
        "registry_module_rows": read_jsonl(REGISTRY_MODULE_LEDGER),
        "registry_event_probe_rows": read_jsonl(EVENT_PROBE_LEDGER),
        "symbol_registry_rollup_rows": read_jsonl(SYMBOL_REGISTRY_ROLLUP_LEDGER),
        "nonregistration_registry_review_rows": read_jsonl(NONREGISTRATION_REGISTRY_REVIEW_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "system_action_rows": read_jsonl(SYSTEM_ACTION_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    family_counts = Counter(str(row.get("runtime_candidate_family")) for row in ledgers["registry_module_rows"])
    status_counts = Counter(str(row.get("registry_entry_status")) for row in ledgers["registry_module_rows"])
    probe_outcomes = Counter(str(row.get("probe_event_outcome")) for row in ledgers["registry_event_probe_rows"])
    expected = {
        "input_runtime_candidate_rows": len(input_candidate_rows),
        "input_guard_check_rows": len(input_guard_rows),
        "input_nonregistration_review_rows": len(input_nonregistration_rows),
        "registry_module_rows": len(input_candidate_rows),
        "registered_registry_module_rows": len(input_candidate_rows),
        "blocked_registry_module_rows": 0,
        "registry_event_probe_rows": len(input_candidate_rows),
        "probe_scope_matched_rows": len(input_candidate_rows),
        "nonregistration_registry_review_rows": len(input_nonregistration_rows),
        "system_action_rows": 1,
        "default_off_registry_module_rows": family_counts.get(
            "branch_local_default_off_repaired_proxy_scorer_candidate", 0
        ),
        "avoid_redesign_registry_module_rows": family_counts.get(
            "branch_local_avoid_redesign_repaired_proxy_comparator_candidate", 0
        ),
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")
    if family_counts.get("branch_local_default_off_repaired_proxy_scorer_candidate", 0) != 75:
        issues.append("default-off registry module count drifted")
    if family_counts.get("branch_local_avoid_redesign_repaired_proxy_comparator_candidate", 0) != 148:
        issues.append("avoid/redesign registry module count drifted")
    if status_counts.get("RUNTIME_CANDIDATE_REGISTRY_ENTRY_REGISTERED_BRANCH_LOCAL", 0) != len(input_candidate_rows):
        issues.append("registry entry status count drifted")
    probe_good = (
        probe_outcomes.get("DEFAULT_OFF_SCORER_EVENT_ACCEPTED_BRANCH_LOCAL", 0)
        + probe_outcomes.get("AVOID_REDESIGN_COMPARATOR_EVENT_TRIGGERED_BRANCH_LOCAL", 0)
    )
    if probe_good != len(input_candidate_rows):
        issues.append(f"registry probe accepted/triggered count expected {len(input_candidate_rows)} got {probe_good}")
    if any(row.get("production_import_path") for row in ledgers["registry_module_rows"]):
        issues.append("registry module row exposes production import path")
    if any(row.get("mutates_order_risk_prompt_safety_or_mt5") for row in ledgers["registry_module_rows"]):
        issues.append("registry module row exposes order/risk/prompt/safety/MT5 mutation")
    rollup_total = sum(int(row.get("registry_module_rows") or 0) for row in ledgers["symbol_registry_rollup_rows"])
    if rollup_total != len(input_candidate_rows):
        issues.append(f"symbol registry rollup total expected {len(input_candidate_rows)} got {rollup_total}")

    for key, rows in ledgers.items():
        sample = rows[:100] if key == "source_manifest_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        REGISTRY_MODULE_LEDGER,
        EVENT_PROBE_LEDGER,
        SYMBOL_REGISTRY_ROLLUP_LEDGER,
        NONREGISTRATION_REGISTRY_REVIEW_LEDGER,
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
        "runtime_candidate_family_counts": dict(sorted(family_counts.items())),
        "registry_entry_status_counts": dict(sorted(status_counts.items())),
        "probe_event_outcome_counts": dict(sorted(probe_outcomes.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
