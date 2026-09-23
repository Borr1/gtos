#!/usr/bin/env python3
"""Verify runtime replay ranked-packet artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_RANKED_PACKET"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_DECISION_APPLICATION_COMPARISON"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
RANKED_ADVANCE_PACKET_LEDGER = ROUTE_DIR / f"{PREFIX}_RANKED_ADVANCE_PACKET_LEDGER_2026-05-17.jsonl"
HELD_SCOPE_CONTEXT_LEDGER = ROUTE_DIR / f"{PREFIX}_HELD_SCOPE_CONTEXT_LEDGER_2026-05-17.jsonl"
NEXT_BRANCH_LOCAL_PACKET_LEDGER = ROUTE_DIR / f"{PREFIX}_NEXT_BRANCH_LOCAL_PACKET_LEDGER_2026-05-17.jsonl"
SYSTEM_RANKED_PACKET_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_RANKED_PACKET_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
ADVANCE_PACKET_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_ADVANCE_PACKET_LEDGER_2026-05-17.jsonl"
HELD_REVIEW_SCOPE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_HELD_REVIEW_SCOPE_LEDGER_2026-05-17.jsonl"
SYSTEM_COMPARISON_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYSTEM_REVIEW_COMPARISON_LEDGER_2026-05-17.jsonl"

BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_ranked_packet_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_runtime_replay_ranked_packet.py"


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
    input_advance = read_jsonl(ADVANCE_PACKET_LEDGER)
    input_held = read_jsonl(HELD_REVIEW_SCOPE_LEDGER)
    input_system = read_jsonl(SYSTEM_COMPARISON_LEDGER)
    ledgers = {
        "ranked_advance_packet_rows": read_jsonl(RANKED_ADVANCE_PACKET_LEDGER),
        "held_scope_context_rows": read_jsonl(HELD_SCOPE_CONTEXT_LEDGER),
        "next_branch_local_packet_rows": read_jsonl(NEXT_BRANCH_LOCAL_PACKET_LEDGER),
        "system_ranked_packet_rows": read_jsonl(SYSTEM_RANKED_PACKET_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    tiers = Counter(normalized(row.get("packet_rank_tier")) for row in ledgers["ranked_advance_packet_rows"])
    expected = {
        "input_decision_application_comparison_result_ok": int(bool(input_result.get("ok"))),
        "input_advance_packet_rows": len(input_advance),
        "input_held_review_scope_rows": len(input_held),
        "input_system_comparison_rows": len(input_system),
        "ranked_advance_packet_rows": len(input_advance),
        "held_scope_context_rows": len(input_held),
        "next_branch_local_packet_rows": len(input_advance),
        "ranked_direct_clear_batch_rows": tiers.get("RANKED_PACKET_DIRECT_CLEAR_BATCH", 0),
        "ranked_advance_ready_batch_rows": tiers.get("RANKED_PACKET_ADVANCE_READY_BATCH", 0),
        "ranked_advance_with_context_batch_rows": tiers.get("RANKED_PACKET_ADVANCE_WITH_CONTEXT_BATCH", 0),
        "ranked_advance_with_held_scope_pressure_rows": tiers.get(
            "RANKED_PACKET_ADVANCE_WITH_HELD_SCOPE_PRESSURE", 0
        ),
        "ranked_advance_low_priority_context_rows": tiers.get(
            "RANKED_PACKET_ADVANCE_LOW_PRIORITY_CONTEXT", 0
        ),
        "system_ranked_packet_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")

    ranks = [int(row.get("packet_rank") or 0) for row in ledgers["ranked_advance_packet_rows"]]
    if ranks != list(range(1, len(ranks) + 1)):
        issues.append("ranked packet rows are not contiguous from 1")
    scores = [float(row.get("packet_rank_score") or 0.0) for row in ledgers["ranked_advance_packet_rows"]]
    if scores != sorted(scores, reverse=True):
        issues.append("ranked packet scores are not sorted descending")
    if not ledgers["system_ranked_packet_rows"][0].get("system_ranked_packet"):
        issues.append("system ranked-packet row missing text")

    for key, rows in ledgers.items():
        sample = rows[:100] if key == "source_manifest_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")
    if not boundary_ok(result):
        issues.append("result is outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        RANKED_ADVANCE_PACKET_LEDGER,
        HELD_SCOPE_CONTEXT_LEDGER,
        NEXT_BRANCH_LOCAL_PACKET_LEDGER,
        SYSTEM_RANKED_PACKET_LEDGER,
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
        "packet_rank_tier_counts": dict(sorted(tiers.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
