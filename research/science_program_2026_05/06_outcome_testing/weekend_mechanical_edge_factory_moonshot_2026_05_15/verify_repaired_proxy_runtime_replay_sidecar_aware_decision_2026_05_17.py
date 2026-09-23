#!/usr/bin/env python3
"""Verify runtime replay sidecar-aware decision artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_SIDECAR_AWARE_DECISION"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_SIDECAR_AWARE_SCORE"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
PACKET_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_PACKET_DECISION_LEDGER_2026-05-17.jsonl"
SCOPE_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_DECISION_LEDGER_2026-05-17.jsonl"
SIDECAR_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_SIDECAR_DECISION_LEDGER_2026-05-17.jsonl"
SYSTEM_DECISION_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_DECISION_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
PACKET_SCORE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_PACKET_SCORE_LEDGER_2026-05-17.jsonl"
SCOPE_SCORE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCOPE_SCORE_LEDGER_2026-05-17.jsonl"
SIDECAR_SCORE_IMPACT_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SIDECAR_SCORE_IMPACT_LEDGER_2026-05-17.jsonl"
SYSTEM_SCORE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYSTEM_SCORE_LEDGER_2026-05-17.jsonl"

BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_sidecar_aware_decision_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_runtime_replay_sidecar_aware_decision.py"


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
    input_packet_scores = read_jsonl(PACKET_SCORE_LEDGER)
    input_scope_scores = read_jsonl(SCOPE_SCORE_LEDGER)
    input_sidecar_impacts = read_jsonl(SIDECAR_SCORE_IMPACT_LEDGER)
    input_system_scores = read_jsonl(SYSTEM_SCORE_LEDGER)
    ledgers = {
        "packet_decision_rows": read_jsonl(PACKET_DECISION_LEDGER),
        "scope_decision_rows": read_jsonl(SCOPE_DECISION_LEDGER),
        "sidecar_decision_rows": read_jsonl(SIDECAR_DECISION_LEDGER),
        "system_decision_rows": read_jsonl(SYSTEM_DECISION_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    packet_counts = Counter(str(row.get("packet_decision_family")) for row in ledgers["packet_decision_rows"])
    scope_counts = Counter(str(row.get("scope_decision_class")) for row in ledgers["scope_decision_rows"])
    sidecar_counts = Counter(str(row.get("sidecar_decision_family")) for row in ledgers["sidecar_decision_rows"])
    expected = {
        "input_sidecar_score_result_ok": int(bool(input_result.get("ok"))),
        "input_packet_score_rows": len(input_packet_scores),
        "input_scope_score_rows": len(input_scope_scores),
        "input_sidecar_score_impact_rows": len(input_sidecar_impacts),
        "input_system_score_rows": len(input_system_scores),
        "packet_decision_rows": len(input_packet_scores),
        "scope_decision_rows": len(input_scope_scores),
        "sidecar_decision_rows": len(input_sidecar_impacts),
        "packet_clear_advance_rows": packet_counts.get("PACKET_DECISION_CLEAR_ADVANCE", 0),
        "packet_context_advance_rows": packet_counts.get("PACKET_DECISION_CONTEXT_ADVANCE", 0),
        "packet_review_hold_rows": packet_counts.get("PACKET_DECISION_REVIEW_HOLD", 0),
        "packet_review_only_rows": packet_counts.get("PACKET_DECISION_REVIEW_ONLY", 0),
        "scope_clear_advance_rows": scope_counts.get("SCOPE_DECISION_HAS_CLEAR_ADVANCE_PACKET", 0),
        "scope_context_advance_rows": scope_counts.get("SCOPE_DECISION_HAS_CONTEXT_ADVANCE_PACKET", 0),
        "scope_review_held_rows": scope_counts.get("SCOPE_DECISION_REVIEW_HELD_PACKET_SCOPE", 0),
        "scope_sidecar_only_review_rows": scope_counts.get("SCOPE_DECISION_SIDECAR_ONLY_REVIEW", 0),
        "sidecar_score_damper_rows": sidecar_counts.get("SIDECAR_DECISION_SCORE_DAMPER", 0),
        "sidecar_scope_review_requirement_rows": sidecar_counts.get(
            "SIDECAR_DECISION_SCOPE_REVIEW_REQUIREMENT", 0
        ),
        "system_decision_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")
    if not ledgers["system_decision_rows"][0].get("system_decision"):
        issues.append("system decision row missing text")

    for key, rows in ledgers.items():
        sample = rows[:100] if key == "source_manifest_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")
    if not boundary_ok(result):
        issues.append("result is outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        PACKET_DECISION_LEDGER,
        SCOPE_DECISION_LEDGER,
        SIDECAR_DECISION_LEDGER,
        SYSTEM_DECISION_LEDGER,
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
        "packet_decision_family_counts": dict(sorted(packet_counts.items())),
        "scope_decision_class_counts": dict(sorted(scope_counts.items())),
        "sidecar_decision_family_counts": dict(sorted(sidecar_counts.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
