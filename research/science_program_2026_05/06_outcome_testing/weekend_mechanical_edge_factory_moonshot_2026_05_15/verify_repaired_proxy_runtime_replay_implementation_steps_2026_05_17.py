#!/usr/bin/env python3
"""Verify runtime replay implementation-step artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_IMPLEMENTATION_STEPS"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_RANKED_PACKET"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
IMPLEMENTATION_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_IMPLEMENTATION_ACTION_LEDGER_2026-05-17.jsonl"
IMPLEMENTATION_SCOPE_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_ROLLUP_LEDGER_2026-05-17.jsonl"
IMPLEMENTATION_NEXT_STEP_LEDGER = ROUTE_DIR / f"{PREFIX}_NEXT_STEP_LEDGER_2026-05-17.jsonl"
SYSTEM_IMPLEMENTATION_STEP_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
NEXT_BRANCH_LOCAL_PACKET_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_NEXT_BRANCH_LOCAL_PACKET_LEDGER_2026-05-17.jsonl"
RANKED_ADVANCE_PACKET_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_RANKED_ADVANCE_PACKET_LEDGER_2026-05-17.jsonl"
SYSTEM_RANKED_PACKET_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYSTEM_RANKED_PACKET_LEDGER_2026-05-17.jsonl"

BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_implementation_steps_2026_05_17.py"
HELPER_MODULE = (
    ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_runtime_replay_implementation_steps.py"
)


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


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


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
    input_next = read_jsonl(NEXT_BRANCH_LOCAL_PACKET_LEDGER)
    input_ranked = read_jsonl(RANKED_ADVANCE_PACKET_LEDGER)
    input_system = read_jsonl(SYSTEM_RANKED_PACKET_LEDGER)
    ledgers = {
        "implementation_action_rows": read_jsonl(IMPLEMENTATION_ACTION_LEDGER),
        "implementation_scope_rollup_rows": read_jsonl(IMPLEMENTATION_SCOPE_ROLLUP_LEDGER),
        "implementation_next_step_rows": read_jsonl(IMPLEMENTATION_NEXT_STEP_LEDGER),
        "system_implementation_step_rows": read_jsonl(SYSTEM_IMPLEMENTATION_STEP_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    family_counts = Counter(normalized(row.get("implementation_family")) for row in ledgers["implementation_action_rows"])
    step_counts = Counter(normalized(row.get("implementation_step_family")) for row in ledgers["implementation_action_rows"])
    expected = {
        "input_ranked_packet_result_ok": int(bool(input_result.get("ok"))),
        "input_next_branch_local_packet_rows": len(input_next),
        "input_ranked_advance_packet_rows": len(input_ranked),
        "input_system_ranked_packet_rows": len(input_system),
        "implementation_action_rows": len(input_next),
        "implementation_next_step_rows": len(input_next),
        "default_off_scorer_action_rows": family_counts.get("IMPLEMENTATION_FAMILY_DEFAULT_OFF_SCORER", 0),
        "avoid_redesign_comparator_action_rows": family_counts.get(
            "IMPLEMENTATION_FAMILY_AVOID_REDESIGN_COMPARATOR", 0
        ),
        "ready_scorer_batch_rows": step_counts.get("IMPLEMENTATION_STEP_READY_SCORER_BATCH", 0),
        "ready_comparator_batch_rows": step_counts.get("IMPLEMENTATION_STEP_READY_COMPARATOR_BATCH", 0),
        "context_scorer_batch_rows": step_counts.get("IMPLEMENTATION_STEP_CONTEXT_SCORER_BATCH", 0),
        "context_comparator_batch_rows": step_counts.get("IMPLEMENTATION_STEP_CONTEXT_COMPARATOR_BATCH", 0),
        "context_carry_scorer_rows": step_counts.get("IMPLEMENTATION_STEP_CONTEXT_CARRY_SCORER", 0),
        "context_carry_comparator_rows": step_counts.get("IMPLEMENTATION_STEP_CONTEXT_CARRY_COMPARATOR", 0),
        "system_implementation_step_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")
    if not ledgers["system_implementation_step_rows"][0].get("system_implementation_steps"):
        issues.append("system implementation-step row missing text")

    for key, rows in ledgers.items():
        sample = rows[:100] if key == "source_manifest_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")
    if not boundary_ok(result):
        issues.append("result is outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        IMPLEMENTATION_ACTION_LEDGER,
        IMPLEMENTATION_SCOPE_ROLLUP_LEDGER,
        IMPLEMENTATION_NEXT_STEP_LEDGER,
        SYSTEM_IMPLEMENTATION_STEP_LEDGER,
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
        "implementation_family_counts": dict(sorted(family_counts.items())),
        "implementation_step_family_counts": dict(sorted(step_counts.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
