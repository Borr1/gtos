#!/usr/bin/env python3
"""Verify runtime replay sidecar-aware score artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_SIDECAR_AWARE_SCORE"
SUMMARY_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_COMPARISON_SUMMARY"
PACKET_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_COMPARISON_PACKET"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
PACKET_SCORE_LEDGER = ROUTE_DIR / f"{PREFIX}_PACKET_SCORE_LEDGER_2026-05-17.jsonl"
SCOPE_SCORE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_SCORE_LEDGER_2026-05-17.jsonl"
SIDECAR_SCORE_IMPACT_LEDGER = ROUTE_DIR / f"{PREFIX}_SIDECAR_SCORE_IMPACT_LEDGER_2026-05-17.jsonl"
SYSTEM_SCORE_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_SCORE_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

INPUT_RESULT = ROUTE_DIR / f"{SUMMARY_PREFIX}_RESULT_2026-05-17.json"
COMPARISON_PACKET_LEDGER = ROUTE_DIR / f"{PACKET_PREFIX}_COMPARISON_PACKET_LEDGER_2026-05-17.jsonl"
SCOPE_COMPARISON_LEDGER = ROUTE_DIR / f"{SUMMARY_PREFIX}_SCOPE_COMPARISON_LEDGER_2026-05-17.jsonl"
SIGNAL_COMPARISON_LEDGER = ROUTE_DIR / f"{SUMMARY_PREFIX}_SIGNAL_COMPARISON_LEDGER_2026-05-17.jsonl"
SIDECAR_ATTACHMENT_LEDGER = ROUTE_DIR / f"{SUMMARY_PREFIX}_SIDECAR_ATTACHMENT_LEDGER_2026-05-17.jsonl"
SYSTEM_SUMMARY_LEDGER = ROUTE_DIR / f"{SUMMARY_PREFIX}_SYSTEM_SUMMARY_LEDGER_2026-05-17.jsonl"

BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_sidecar_aware_score_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_runtime_replay_sidecar_aware_score.py"


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
    input_packet_rows = read_jsonl(COMPARISON_PACKET_LEDGER)
    input_scope_rows = read_jsonl(SCOPE_COMPARISON_LEDGER)
    input_signal_rows = read_jsonl(SIGNAL_COMPARISON_LEDGER)
    input_attachment_rows = read_jsonl(SIDECAR_ATTACHMENT_LEDGER)
    input_system_rows = read_jsonl(SYSTEM_SUMMARY_LEDGER)
    ledgers = {
        "packet_score_rows": read_jsonl(PACKET_SCORE_LEDGER),
        "scope_score_rows": read_jsonl(SCOPE_SCORE_LEDGER),
        "sidecar_score_impact_rows": read_jsonl(SIDECAR_SCORE_IMPACT_LEDGER),
        "system_score_rows": read_jsonl(SYSTEM_SCORE_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    score_classes = Counter(str(row.get("sidecar_aware_score_class")) for row in ledgers["packet_score_rows"])
    impact_classes = Counter(str(row.get("sidecar_score_impact_class")) for row in ledgers["sidecar_score_impact_rows"])
    expected = {
        "input_comparison_summary_result_ok": int(bool(input_result.get("ok"))),
        "input_comparison_packet_rows": len(input_packet_rows),
        "input_scope_comparison_rows": len(input_scope_rows),
        "input_signal_comparison_rows": len(input_signal_rows),
        "input_sidecar_attachment_rows": len(input_attachment_rows),
        "input_system_summary_rows": len(input_system_rows),
        "packet_score_rows": len(input_packet_rows),
        "scope_score_rows": len(input_scope_rows),
        "sidecar_score_impact_rows": len(input_attachment_rows),
        "score_high_clear_rows": score_classes.get("COMPARISON_SCORE_HIGH_CLEAR", 0),
        "score_usable_with_context_rows": score_classes.get("COMPARISON_SCORE_USABLE_WITH_CONTEXT", 0),
        "score_context_or_damped_rows": score_classes.get("COMPARISON_SCORE_CONTEXT_ONLY_OR_SIDECAR_DAMPED", 0),
        "score_review_only_rows": score_classes.get("COMPARISON_SCORE_REVIEW_ONLY", 0),
        "sidecar_damps_represented_scope_rows": impact_classes.get("SIDECAR_DAMPS_REPRESENTED_SCOPE_SCORE", 0),
        "sidecar_held_for_scope_review_rows": impact_classes.get("SIDECAR_HELD_FOR_SCOPE_REVIEW", 0),
        "system_score_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")
    if not ledgers["system_score_rows"][0].get("system_score"):
        issues.append("system score row missing text")
    if any(row.get("score_usage") != "BRANCH_LOCAL_COMPARISON_PRIORITY_ONLY" for row in ledgers["packet_score_rows"]):
        issues.append("packet score rows contain unexpected score usage")

    for key, rows in ledgers.items():
        sample = rows[:100] if key == "source_manifest_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")
    if not boundary_ok(result):
        issues.append("result is outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        PACKET_SCORE_LEDGER,
        SCOPE_SCORE_LEDGER,
        SIDECAR_SCORE_IMPACT_LEDGER,
        SYSTEM_SCORE_LEDGER,
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
        "sidecar_aware_score_class_counts": dict(sorted(score_classes.items())),
        "sidecar_score_impact_class_counts": dict(sorted(impact_classes.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
