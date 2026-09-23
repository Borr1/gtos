#!/usr/bin/env python3
"""Verify runtime replay spec-execution artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_SPEC_EXECUTION"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_SPEC_MATERIALIZATION"
RERUN_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_REPLAY_SCORE_RERUN"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SCORER_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_EXECUTION_LEDGER_2026-05-17.jsonl"
COMPARATOR_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPARATOR_EXECUTION_LEDGER_2026-05-17.jsonl"
RESULT_LEDGER = ROUTE_DIR / f"{PREFIX}_RESULT_LEDGER_2026-05-17.jsonl"
SCOPE_ROLLUP_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_ROLLUP_LEDGER_2026-05-17.jsonl"
SYSTEM_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
SCORER_SPEC_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCORER_SPEC_LEDGER_2026-05-17.jsonl"
COMPARATOR_SPEC_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_COMPARATOR_SPEC_LEDGER_2026-05-17.jsonl"
SYSTEM_SPEC_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
DEFAULT_OFF_RERUN_LEDGER = ROUTE_DIR / f"{RERUN_PREFIX}_DEFAULT_OFF_SCORE_RERUN_LEDGER_2026-05-17.jsonl"
AVOID_RERUN_LEDGER = ROUTE_DIR / f"{RERUN_PREFIX}_AVOID_COMPARATOR_RERUN_LEDGER_2026-05-17.jsonl"

BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_spec_execution_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_runtime_replay_spec_execution.py"


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
    input_scorer_specs = read_jsonl(SCORER_SPEC_LEDGER)
    input_comparator_specs = read_jsonl(COMPARATOR_SPEC_LEDGER)
    input_system_specs = read_jsonl(SYSTEM_SPEC_LEDGER)
    input_default_reruns = read_jsonl(DEFAULT_OFF_RERUN_LEDGER)
    input_avoid_reruns = read_jsonl(AVOID_RERUN_LEDGER)
    ledgers = {
        "scorer_spec_execution_rows": read_jsonl(SCORER_EXECUTION_LEDGER),
        "comparator_spec_execution_rows": read_jsonl(COMPARATOR_EXECUTION_LEDGER),
        "spec_execution_result_rows": read_jsonl(RESULT_LEDGER),
        "spec_execution_scope_rollup_rows": read_jsonl(SCOPE_ROLLUP_LEDGER),
        "system_spec_execution_rows": read_jsonl(SYSTEM_EXECUTION_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    scorer_counts = Counter(normalized(row.get("scorer_spec_execution_class")) for row in ledgers["scorer_spec_execution_rows"])
    comparator_counts = Counter(
        normalized(row.get("comparator_spec_execution_class")) for row in ledgers["comparator_spec_execution_rows"]
    )
    join_counts = Counter(normalized(row.get("spec_execution_join_status")) for row in ledgers["spec_execution_result_rows"])
    expected = {
        "input_spec_materialization_result_ok": int(bool(input_result.get("ok"))),
        "input_scorer_spec_rows": len(input_scorer_specs),
        "input_comparator_spec_rows": len(input_comparator_specs),
        "input_system_spec_materialization_rows": len(input_system_specs),
        "input_default_off_rerun_rows": len(input_default_reruns),
        "input_avoid_rerun_rows": len(input_avoid_reruns),
        "scorer_spec_execution_rows": len(input_scorer_specs),
        "comparator_spec_execution_rows": len(input_comparator_specs),
        "spec_execution_result_rows": len(input_scorer_specs) + len(input_comparator_specs),
        "spec_execution_exact_join_rows": join_counts.get("SPEC_EXECUTION_REPLAY_SCORE_JOINED_EXACT", 0),
        "spec_execution_unmatched_rows": join_counts.get("SPEC_EXECUTION_REPLAY_SCORE_UNMATCHED", 0),
        "scorer_positive_replay_score_rows": scorer_counts.get("SCORER_SPEC_EXECUTION_POSITIVE_REPLAY_SCORE", 0),
        "scorer_weak_positive_replay_score_rows": scorer_counts.get(
            "SCORER_SPEC_EXECUTION_WEAK_POSITIVE_REPLAY_SCORE", 0
        ),
        "scorer_negative_replay_score_rows": scorer_counts.get("SCORER_SPEC_EXECUTION_NEGATIVE_REPLAY_SCORE", 0),
        "comparator_strong_avoid_score_rows": comparator_counts.get(
            "COMPARATOR_SPEC_EXECUTION_STRONG_AVOID_SCORE", 0
        ),
        "comparator_avoid_score_rows": comparator_counts.get("COMPARATOR_SPEC_EXECUTION_AVOID_SCORE", 0),
        "comparator_weak_or_positive_score_rows": comparator_counts.get(
            "COMPARATOR_SPEC_EXECUTION_WEAK_OR_POSITIVE_SCORE", 0
        ),
        "system_spec_execution_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")
    if counts.get("spec_execution_unmatched_rows") != 0:
        issues.append("spec execution has unmatched replay-score rows")
    if not ledgers["system_spec_execution_rows"][0].get("system_spec_execution"):
        issues.append("system spec-execution row missing text")

    for key, rows in ledgers.items():
        sample = rows[:100] if key == "source_manifest_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")
    if not boundary_ok(result):
        issues.append("result is outside concrete branch-local boundary")

    blocked_hits = scan_blocked_terms(
        [
            RESULT_PATH,
            SCORER_EXECUTION_LEDGER,
            COMPARATOR_EXECUTION_LEDGER,
            RESULT_LEDGER,
            SCOPE_ROLLUP_LEDGER,
            SYSTEM_EXECUTION_LEDGER,
            BUCKET_LEDGER,
            SOURCE_MANIFEST_LEDGER,
            SUMMARY_PATH,
            BUILDER_MODULE,
            HELPER_MODULE,
            Path(__file__),
        ]
    )
    if blocked_hits:
        issues.append(f"blocked boundary terms present: {blocked_hits}")

    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": {key: counts.get(key) for key in sorted(counts)},
        "scorer_spec_execution_class_counts": dict(sorted(scorer_counts.items())),
        "comparator_spec_execution_class_counts": dict(sorted(comparator_counts.items())),
        "spec_execution_join_status_counts": dict(sorted(join_counts.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
