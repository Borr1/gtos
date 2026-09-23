#!/usr/bin/env python3
"""Verify runtime replay decision bundle artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_DECISION_BUNDLE"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_SIDECAR_AWARE_DECISION"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
FINAL_PACKET_BUNDLE_LEDGER = ROUTE_DIR / f"{PREFIX}_FINAL_PACKET_BUNDLE_LEDGER_2026-05-17.jsonl"
FINAL_SCOPE_BUNDLE_LEDGER = ROUTE_DIR / f"{PREFIX}_FINAL_SCOPE_BUNDLE_LEDGER_2026-05-17.jsonl"
FINAL_SIDECAR_BUNDLE_LEDGER = ROUTE_DIR / f"{PREFIX}_FINAL_SIDECAR_BUNDLE_LEDGER_2026-05-17.jsonl"
SYSTEM_BUNDLE_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_BUNDLE_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
PACKET_DECISION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_PACKET_DECISION_LEDGER_2026-05-17.jsonl"
SCOPE_DECISION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SCOPE_DECISION_LEDGER_2026-05-17.jsonl"
SIDECAR_DECISION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SIDECAR_DECISION_LEDGER_2026-05-17.jsonl"
SYSTEM_DECISION_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYSTEM_DECISION_LEDGER_2026-05-17.jsonl"

BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_decision_bundle_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_runtime_replay_decision_bundle.py"


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
    input_packets = read_jsonl(PACKET_DECISION_LEDGER)
    input_scopes = read_jsonl(SCOPE_DECISION_LEDGER)
    input_sidecars = read_jsonl(SIDECAR_DECISION_LEDGER)
    input_system = read_jsonl(SYSTEM_DECISION_LEDGER)
    ledgers = {
        "final_packet_bundle_rows": read_jsonl(FINAL_PACKET_BUNDLE_LEDGER),
        "final_scope_bundle_rows": read_jsonl(FINAL_SCOPE_BUNDLE_LEDGER),
        "final_sidecar_bundle_rows": read_jsonl(FINAL_SIDECAR_BUNDLE_LEDGER),
        "system_bundle_rows": read_jsonl(SYSTEM_BUNDLE_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    packet_counts = Counter(str(row.get("final_packet_bundle_class")) for row in ledgers["final_packet_bundle_rows"])
    scope_counts = Counter(str(row.get("final_scope_bundle_class")) for row in ledgers["final_scope_bundle_rows"])
    sidecar_counts = Counter(str(row.get("final_sidecar_bundle_class")) for row in ledgers["final_sidecar_bundle_rows"])
    expected = {
        "input_sidecar_decision_result_ok": int(bool(input_result.get("ok"))),
        "input_packet_decision_rows": len(input_packets),
        "input_scope_decision_rows": len(input_scopes),
        "input_sidecar_decision_rows": len(input_sidecars),
        "input_system_decision_rows": len(input_system),
        "final_packet_bundle_rows": len(input_packets),
        "final_scope_bundle_rows": len(input_scopes),
        "final_sidecar_bundle_rows": len(input_sidecars),
        "final_packet_clear_advance_rows": packet_counts.get("FINAL_BUNDLE_PACKET_CLEAR_ADVANCE", 0),
        "final_packet_context_advance_rows": packet_counts.get("FINAL_BUNDLE_PACKET_CONTEXT_ADVANCE", 0),
        "final_packet_review_hold_rows": packet_counts.get("FINAL_BUNDLE_PACKET_REVIEW_HOLD", 0),
        "final_packet_review_only_rows": packet_counts.get("FINAL_BUNDLE_PACKET_REVIEW_ONLY", 0),
        "final_scope_clear_advance_rows": scope_counts.get("FINAL_BUNDLE_SCOPE_CLEAR_ADVANCE", 0),
        "final_scope_context_advance_rows": scope_counts.get("FINAL_BUNDLE_SCOPE_CONTEXT_ADVANCE", 0),
        "final_scope_review_held_rows": scope_counts.get("FINAL_BUNDLE_SCOPE_REVIEW_HELD", 0),
        "final_scope_sidecar_only_review_rows": scope_counts.get("FINAL_BUNDLE_SCOPE_SIDECAR_ONLY_REVIEW", 0),
        "final_sidecar_score_damper_rows": sidecar_counts.get("FINAL_BUNDLE_SIDECAR_SCORE_DAMPER", 0),
        "final_sidecar_scope_review_requirement_rows": sidecar_counts.get(
            "FINAL_BUNDLE_SIDECAR_SCOPE_REVIEW_REQUIREMENT", 0
        ),
        "system_bundle_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")
    if not ledgers["system_bundle_rows"][0].get("system_bundle"):
        issues.append("system bundle row missing text")

    for key, rows in ledgers.items():
        sample = rows[:100] if key == "source_manifest_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")
    if not boundary_ok(result):
        issues.append("result is outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        FINAL_PACKET_BUNDLE_LEDGER,
        FINAL_SCOPE_BUNDLE_LEDGER,
        FINAL_SIDECAR_BUNDLE_LEDGER,
        SYSTEM_BUNDLE_LEDGER,
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
        "final_packet_bundle_class_counts": dict(sorted(packet_counts.items())),
        "final_scope_bundle_class_counts": dict(sorted(scope_counts.items())),
        "final_sidecar_bundle_class_counts": dict(sorted(sidecar_counts.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
