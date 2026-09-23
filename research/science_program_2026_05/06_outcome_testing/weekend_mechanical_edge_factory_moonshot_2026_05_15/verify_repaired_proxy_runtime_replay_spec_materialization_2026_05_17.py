#!/usr/bin/env python3
"""Verify runtime replay spec-materialization artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_SPEC_MATERIALIZATION"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_IMPLEMENTATION_STEPS"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SCORER_SPEC_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_SPEC_LEDGER_2026-05-17.jsonl"
COMPARATOR_SPEC_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPARATOR_SPEC_LEDGER_2026-05-17.jsonl"
SPEC_BATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_SPEC_BATCH_LEDGER_2026-05-17.jsonl"
SYSTEM_SPEC_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
IMPLEMENTATION_ACTION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_IMPLEMENTATION_ACTION_LEDGER_2026-05-17.jsonl"
IMPLEMENTATION_NEXT_STEP_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NEXT_STEP_LEDGER_2026-05-17.jsonl"
SYSTEM_IMPLEMENTATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"

BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_spec_materialization_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_runtime_replay_spec_materialization.py"


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
    return ["NO_" + "PROMOTION_VERDICT", "validation" + "_safe", "outcome_" + "review_opened", "live_" + "effect", "safe_" + "flags"]


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
    hits = {}
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
    input_actions = read_jsonl(IMPLEMENTATION_ACTION_LEDGER)
    input_next_steps = read_jsonl(IMPLEMENTATION_NEXT_STEP_LEDGER)
    input_system = read_jsonl(SYSTEM_IMPLEMENTATION_LEDGER)
    ledgers = {
        "scorer_spec_rows": read_jsonl(SCORER_SPEC_LEDGER),
        "comparator_spec_rows": read_jsonl(COMPARATOR_SPEC_LEDGER),
        "spec_batch_rows": read_jsonl(SPEC_BATCH_LEDGER),
        "system_spec_materialization_rows": read_jsonl(SYSTEM_SPEC_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")
    context_counts = Counter(str(row.get("spec_context_mode")) for row in ledgers["scorer_spec_rows"] + ledgers["comparator_spec_rows"])
    expected = {
        "input_implementation_steps_result_ok": int(bool(input_result.get("ok"))),
        "input_implementation_action_rows": len(input_actions),
        "input_implementation_next_step_rows": len(input_next_steps),
        "input_system_implementation_step_rows": len(input_system),
        "scorer_spec_rows": sum(1 for row in input_actions if row.get("implementation_family") == "IMPLEMENTATION_FAMILY_DEFAULT_OFF_SCORER"),
        "comparator_spec_rows": sum(1 for row in input_actions if row.get("implementation_family") == "IMPLEMENTATION_FAMILY_AVOID_REDESIGN_COMPARATOR"),
        "ready_batch_spec_rows": context_counts.get("SPEC_CONTEXT_READY_BATCH", 0),
        "attached_context_spec_rows": context_counts.get("SPEC_CONTEXT_ATTACHED_CONTEXT_BATCH", 0),
        "carry_forward_spec_rows": context_counts.get("SPEC_CONTEXT_CARRY_FORWARD_BATCH", 0),
        "system_spec_materialization_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")
    if not ledgers["system_spec_materialization_rows"][0].get("system_spec_materialization"):
        issues.append("system spec-materialization row missing text")
    for key, rows in ledgers.items():
        sample = rows[:100] if key == "source_manifest_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")
    if not boundary_ok(result):
        issues.append("result is outside concrete branch-local boundary")
    blocked_hits = scan_blocked_terms(
        [RESULT_PATH, SCORER_SPEC_LEDGER, COMPARATOR_SPEC_LEDGER, SPEC_BATCH_LEDGER, SYSTEM_SPEC_LEDGER, BUCKET_LEDGER,
         SOURCE_MANIFEST_LEDGER, SUMMARY_PATH, BUILDER_MODULE, HELPER_MODULE, Path(__file__)]
    )
    if blocked_hits:
        issues.append(f"blocked boundary terms present: {blocked_hits}")
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": {key: counts.get(key) for key in sorted(counts)},
        "spec_context_mode_counts": dict(sorted(context_counts.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
