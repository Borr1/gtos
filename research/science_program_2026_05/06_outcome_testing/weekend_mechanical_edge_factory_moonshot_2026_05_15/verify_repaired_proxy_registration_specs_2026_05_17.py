#!/usr/bin/env python3
"""Verify repaired-proxy registration spec artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REGISTRATION_SPECS"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_SYMBOL_ACTION_PACKET"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
REGISTRATION_SPEC_LEDGER = ROUTE_DIR / f"{PREFIX}_REGISTRATION_SPEC_LEDGER_2026-05-17.jsonl"
RUNTIME_GUARD_LEDGER = ROUTE_DIR / f"{PREFIX}_RUNTIME_GUARD_LEDGER_2026-05-17.jsonl"
SYMBOL_REGISTRATION_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_REGISTRATION_SUMMARY_LEDGER_2026-05-17.jsonl"
NONREGISTRATION_CONTEXT_LEDGER = ROUTE_DIR / f"{PREFIX}_NONREGISTRATION_CONTEXT_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

COMPARATOR_REGISTRATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_COMPARATOR_REGISTRATION_LEDGER_2026-05-17.jsonl"
COMPARATOR_NONREGISTRATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_COMPARATOR_NONREGISTRATION_LEDGER_2026-05-17.jsonl"
BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_registration_specs_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_registration_specs.py"


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
    input_registration_rows = read_jsonl(COMPARATOR_REGISTRATION_LEDGER)
    input_nonregistration_rows = read_jsonl(COMPARATOR_NONREGISTRATION_LEDGER)
    ledgers = {
        "registration_spec_rows": read_jsonl(REGISTRATION_SPEC_LEDGER),
        "runtime_guard_rows": read_jsonl(RUNTIME_GUARD_LEDGER),
        "symbol_registration_summary_rows": read_jsonl(SYMBOL_REGISTRATION_SUMMARY_LEDGER),
        "nonregistration_context_rows": read_jsonl(NONREGISTRATION_CONTEXT_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "system_action_rows": read_jsonl(SYSTEM_ACTION_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    family_counts = Counter(str(row.get("registration_spec_family")) for row in ledgers["registration_spec_rows"])
    expected = {
        "input_comparator_registration_rows": len(input_registration_rows),
        "input_comparator_nonregistration_rows": len(input_nonregistration_rows),
        "registration_spec_rows": len(input_registration_rows),
        "runtime_guard_rows": len(input_registration_rows),
        "nonregistration_context_rows": len(input_nonregistration_rows),
        "system_action_rows": 1,
        "default_off_registration_spec_rows": family_counts.get("default_off_repaired_proxy_scorer_comparator", 0),
        "avoid_redesign_registration_spec_rows": family_counts.get("avoid_redesign_repaired_proxy_comparator", 0),
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")
    if family_counts.get("default_off_repaired_proxy_scorer_comparator", 0) != 75:
        issues.append("default-off registration spec count drifted")
    if family_counts.get("avoid_redesign_repaired_proxy_comparator", 0) != 148:
        issues.append("avoid/redesign registration spec count drifted")
    if any(row.get("runtime_candidate_use_permitted") for row in ledgers["registration_spec_rows"]):
        issues.append("registration spec row exposes runtime candidate permission")
    for row in ledgers["runtime_guard_rows"]:
        guard = row.get("guard_conditions") or {}
        if guard.get("production_import_path") is not False or guard.get("order_risk_prompt_safety_mt5_mutation") is not False:
            issues.append("runtime guard has forbidden surface enabled")
            break

    for key, rows in ledgers.items():
        sample = rows[:100] if key == "source_manifest_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        REGISTRATION_SPEC_LEDGER,
        RUNTIME_GUARD_LEDGER,
        SYMBOL_REGISTRATION_SUMMARY_LEDGER,
        NONREGISTRATION_CONTEXT_LEDGER,
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
        "registration_spec_family_counts": dict(sorted(family_counts.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
