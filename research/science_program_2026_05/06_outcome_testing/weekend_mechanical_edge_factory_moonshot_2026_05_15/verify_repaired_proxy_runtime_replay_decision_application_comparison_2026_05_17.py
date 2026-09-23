#!/usr/bin/env python3
"""Verify runtime replay decision-application comparison artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_DECISION_APPLICATION_COMPARISON"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_DECISION_APPLICATION"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SCOPE_REVIEW_COMPARISON_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_REVIEW_COMPARISON_LEDGER_2026-05-17.jsonl"
PACKET_SCOPE_COMPARISON_LEDGER = ROUTE_DIR / f"{PREFIX}_PACKET_SCOPE_COMPARISON_LEDGER_2026-05-17.jsonl"
SIDECAR_SCOPE_COMPARISON_LEDGER = ROUTE_DIR / f"{PREFIX}_SIDECAR_SCOPE_COMPARISON_LEDGER_2026-05-17.jsonl"
ADVANCE_PACKET_LEDGER = ROUTE_DIR / f"{PREFIX}_ADVANCE_PACKET_LEDGER_2026-05-17.jsonl"
HELD_REVIEW_SCOPE_LEDGER = ROUTE_DIR / f"{PREFIX}_HELD_REVIEW_SCOPE_LEDGER_2026-05-17.jsonl"
SYSTEM_REVIEW_COMPARISON_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_REVIEW_COMPARISON_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
PACKET_APPLICATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_PACKET_APPLICATION_LEDGER_2026-05-17.jsonl"
SCOPE_APPLICATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCOPE_APPLICATION_LEDGER_2026-05-17.jsonl"
SIDECAR_APPLICATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SIDECAR_APPLICATION_LEDGER_2026-05-17.jsonl"
SYSTEM_APPLICATION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYSTEM_APPLICATION_LEDGER_2026-05-17.jsonl"

BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_decision_application_comparison_2026_05_17.py"
HELPER_MODULE = (
    ROUTE_DIR.parents[3]
    / "src/research_infra/moonshot_repaired_proxy_runtime_replay_decision_application_comparison.py"
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
    input_packets = read_jsonl(PACKET_APPLICATION_LEDGER)
    input_scopes = read_jsonl(SCOPE_APPLICATION_LEDGER)
    input_sidecars = read_jsonl(SIDECAR_APPLICATION_LEDGER)
    input_system = read_jsonl(SYSTEM_APPLICATION_LEDGER)
    ledgers = {
        "scope_review_comparison_rows": read_jsonl(SCOPE_REVIEW_COMPARISON_LEDGER),
        "packet_scope_comparison_rows": read_jsonl(PACKET_SCOPE_COMPARISON_LEDGER),
        "sidecar_scope_comparison_rows": read_jsonl(SIDECAR_SCOPE_COMPARISON_LEDGER),
        "advance_packet_rows": read_jsonl(ADVANCE_PACKET_LEDGER),
        "held_review_scope_rows": read_jsonl(HELD_REVIEW_SCOPE_LEDGER),
        "system_review_comparison_rows": read_jsonl(SYSTEM_REVIEW_COMPARISON_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    scope_counts = Counter(normalized(row.get("scope_review_comparison_class")) for row in ledgers["scope_review_comparison_rows"])
    packet_counts = Counter(normalized(row.get("packet_scope_comparison_family")) for row in ledgers["packet_scope_comparison_rows"])
    sidecar_counts = Counter(normalized(row.get("sidecar_scope_comparison_family")) for row in ledgers["sidecar_scope_comparison_rows"])
    input_packet_families = Counter(normalized(row.get("packet_application_family")) for row in input_packets)
    input_scope_families = Counter(normalized(row.get("scope_application_family")) for row in input_scopes)
    expected = {
        "input_decision_application_result_ok": int(bool(input_result.get("ok"))),
        "input_packet_application_rows": len(input_packets),
        "input_scope_application_rows": len(input_scopes),
        "input_sidecar_application_rows": len(input_sidecars),
        "input_system_application_rows": len(input_system),
        "scope_review_comparison_rows": len(input_scopes),
        "packet_scope_comparison_rows": len(input_packets),
        "sidecar_scope_comparison_rows": len(input_sidecars),
        "advance_packet_rows": input_packet_families.get("PACKET_APPLICATION_CLEAR_ADVANCE", 0)
        + input_packet_families.get("PACKET_APPLICATION_CONTEXT_ADVANCE", 0),
        "held_review_scope_rows": input_scope_families.get("SCOPE_APPLICATION_REVIEW_HOLD", 0)
        + input_scope_families.get("SCOPE_APPLICATION_SIDECAR_ONLY_REVIEW", 0),
        "scope_clear_ready_rows": scope_counts.get("SCOPE_REVIEW_COMPARISON_CLEAR_ADVANCE_READY", 0),
        "scope_clear_with_review_context_rows": scope_counts.get(
            "SCOPE_REVIEW_COMPARISON_CLEAR_ADVANCE_WITH_ATTACHED_REVIEW_CONTEXT", 0
        ),
        "scope_context_ready_rows": scope_counts.get("SCOPE_REVIEW_COMPARISON_CONTEXT_ADVANCE_READY", 0),
        "scope_context_with_review_context_rows": scope_counts.get(
            "SCOPE_REVIEW_COMPARISON_CONTEXT_ADVANCE_WITH_ATTACHED_REVIEW_CONTEXT", 0
        ),
        "scope_held_packet_rows": scope_counts.get("SCOPE_REVIEW_COMPARISON_HELD_SCOPE_WITH_HELD_PACKETS", 0),
        "scope_sidecar_only_held_rows": scope_counts.get("SCOPE_REVIEW_COMPARISON_SIDECAR_ONLY_HELD_SCOPE", 0),
        "packet_advance_with_advance_scope_rows": packet_counts.get(
            "PACKET_SCOPE_COMPARISON_ADVANCE_PACKET_WITH_ADVANCE_SCOPE", 0
        ),
        "packet_advance_against_held_scope_rows": packet_counts.get(
            "PACKET_SCOPE_COMPARISON_ADVANCE_PACKET_AGAINST_HELD_SCOPE", 0
        ),
        "packet_held_with_held_scope_rows": packet_counts.get(
            "PACKET_SCOPE_COMPARISON_HELD_PACKET_WITH_HELD_SCOPE", 0
        ),
        "packet_held_attached_to_advance_scope_rows": packet_counts.get(
            "PACKET_SCOPE_COMPARISON_HELD_PACKET_ATTACHED_TO_ADVANCE_SCOPE", 0
        ),
        "sidecar_score_damper_on_advance_scope_rows": sidecar_counts.get(
            "SIDECAR_SCOPE_COMPARISON_SCORE_DAMPER_ON_ADVANCE_SCOPE", 0
        ),
        "sidecar_score_damper_on_held_scope_rows": sidecar_counts.get(
            "SIDECAR_SCOPE_COMPARISON_SCORE_DAMPER_ON_HELD_SCOPE", 0
        ),
        "sidecar_requirement_on_advance_scope_rows": sidecar_counts.get(
            "SIDECAR_SCOPE_COMPARISON_REVIEW_REQUIREMENT_ON_ADVANCE_SCOPE", 0
        ),
        "sidecar_requirement_on_held_scope_rows": sidecar_counts.get(
            "SIDECAR_SCOPE_COMPARISON_REVIEW_REQUIREMENT_ON_HELD_SCOPE", 0
        ),
        "system_review_comparison_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")

    if packet_counts.get("PACKET_SCOPE_COMPARISON_MISSING_SCOPE_CONTEXT", 0):
        issues.append("packet scope comparison has missing scope context")
    if sidecar_counts.get("SIDECAR_SCOPE_COMPARISON_MISSING_SCOPE_CONTEXT", 0):
        issues.append("sidecar scope comparison has missing scope context")
    if not ledgers["system_review_comparison_rows"][0].get("system_review_comparison"):
        issues.append("system review-comparison row missing text")

    for key, rows in ledgers.items():
        sample = rows[:100] if key == "source_manifest_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")
    if not boundary_ok(result):
        issues.append("result is outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        SCOPE_REVIEW_COMPARISON_LEDGER,
        PACKET_SCOPE_COMPARISON_LEDGER,
        SIDECAR_SCOPE_COMPARISON_LEDGER,
        ADVANCE_PACKET_LEDGER,
        HELD_REVIEW_SCOPE_LEDGER,
        SYSTEM_REVIEW_COMPARISON_LEDGER,
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
        "scope_review_comparison_class_counts": dict(sorted(scope_counts.items())),
        "packet_scope_comparison_family_counts": dict(sorted(packet_counts.items())),
        "sidecar_scope_comparison_family_counts": dict(sorted(sidecar_counts.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
