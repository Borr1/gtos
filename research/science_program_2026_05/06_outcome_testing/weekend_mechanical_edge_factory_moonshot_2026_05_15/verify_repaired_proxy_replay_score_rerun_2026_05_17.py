#!/usr/bin/env python3
"""Verify repaired-proxy replay score-rerun artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPLAY_SCORE_RERUN"
NUMERIC_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPLAY_NUMERIC_EXECUTION"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
CONTROL_CONTEXT_LEDGER = ROUTE_DIR / f"{PREFIX}_CONTROL_CONTEXT_LEDGER_2026-05-17.jsonl"
SCORE_RERUN_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORE_RERUN_LEDGER_2026-05-17.jsonl"
DEFAULT_OFF_RERUN_LEDGER = ROUTE_DIR / f"{PREFIX}_DEFAULT_OFF_SCORE_RERUN_LEDGER_2026-05-17.jsonl"
AVOID_RERUN_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_COMPARATOR_RERUN_LEDGER_2026-05-17.jsonl"
REPAIR_CONTEXT_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_CONTEXT_RERUN_LEDGER_2026-05-17.jsonl"
SYMBOL_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_SYMBOL_SUMMARY_LEDGER_2026-05-17.jsonl"
SYSTEM_ACTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_ACTION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

NUMERIC_RESULT = ROUTE_DIR / f"{NUMERIC_PREFIX}_RESULT_2026-05-17.json"
REPLAY_NUMERIC_EVENT_LEDGER = ROUTE_DIR / f"{NUMERIC_PREFIX}_REPLAY_NUMERIC_EVENT_LEDGER_2026-05-17.jsonl"
CONTROL_NUMERIC_EVENT_LEDGER = ROUTE_DIR / f"{NUMERIC_PREFIX}_CONTROL_NUMERIC_EVENT_LEDGER_2026-05-17.jsonl"
BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_replay_score_rerun_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_replay_score_rerun.py"


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
    numeric_result = read_json(NUMERIC_RESULT)
    replay_numeric_rows = read_jsonl(REPLAY_NUMERIC_EVENT_LEDGER)
    control_numeric_rows = read_jsonl(CONTROL_NUMERIC_EVENT_LEDGER)
    ledgers = {
        "control_context_rows": read_jsonl(CONTROL_CONTEXT_LEDGER),
        "score_rerun_rows": read_jsonl(SCORE_RERUN_LEDGER),
        "default_off_score_rerun_rows": read_jsonl(DEFAULT_OFF_RERUN_LEDGER),
        "avoid_comparator_rerun_rows": read_jsonl(AVOID_RERUN_LEDGER),
        "repair_context_rerun_rows": read_jsonl(REPAIR_CONTEXT_LEDGER),
        "symbol_summary_rows": read_jsonl(SYMBOL_SUMMARY_LEDGER),
        "system_action_rows": read_jsonl(SYSTEM_ACTION_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")
    expected = {
        "input_replay_numeric_event_rows": 5324,
        "input_control_numeric_event_rows": 173,
        "score_rerun_rows": 5324,
        "system_action_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")
    if counts.get("score_rerun_rows") != numeric_result.get("counts", {}).get("replay_numeric_event_rows"):
        issues.append("score rerun denominator does not match upstream replay numeric rows")
    if not result.get("score_rerun_denominator_preserved"):
        issues.append("result does not mark score rerun denominator preserved")
    input_family_counts = Counter(str(row.get("registry_family") or "") for row in replay_numeric_rows)
    if counts.get("default_off_score_rerun_rows") != input_family_counts.get("default_off_repaired_proxy_scorer", 0):
        issues.append("default-off family count mismatch")
    if counts.get("avoid_comparator_rerun_rows") != input_family_counts.get("avoid_redesign_repaired_proxy_comparator", 0):
        issues.append("avoid comparator family count mismatch")
    if counts.get("repair_context_rerun_rows") != input_family_counts.get("source_or_broker_geometry_repair", 0):
        issues.append("repair family count mismatch")
    expected_contexts = len({str(row.get("timeframe") or "") for row in control_numeric_rows})
    if counts.get("control_context_rows") != expected_contexts:
        issues.append(f"control_context_rows expected {expected_contexts} got {counts.get('control_context_rows')}")
    score_status_counts = Counter(str(row.get("replay_score_rerun_status") or "") for row in ledgers["score_rerun_rows"])
    if score_status_counts.get("REPLAY_SCORE_RERUN_NO_BASE_SCOPE_SCORE", 0):
        issues.append("score rerun rows missing base scope score")
    for key, rows in ledgers.items():
        sample = rows[:20] if key == "score_rerun_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")
    files_to_scan = [
        RESULT_PATH,
        CONTROL_CONTEXT_LEDGER,
        SCORE_RERUN_LEDGER,
        DEFAULT_OFF_RERUN_LEDGER,
        AVOID_RERUN_LEDGER,
        REPAIR_CONTEXT_LEDGER,
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
        "score_status_counts": dict(sorted(score_status_counts.items())),
        "input_family_counts": dict(sorted(input_family_counts.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
