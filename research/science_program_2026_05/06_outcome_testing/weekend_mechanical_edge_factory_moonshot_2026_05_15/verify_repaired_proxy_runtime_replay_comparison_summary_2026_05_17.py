#!/usr/bin/env python3
"""Verify runtime replay comparison summary artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_COMPARISON_SUMMARY"
INPUT_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_COMPARISON_PACKET"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SCOPE_COMPARISON_LEDGER = ROUTE_DIR / f"{PREFIX}_SCOPE_COMPARISON_LEDGER_2026-05-17.jsonl"
SIGNAL_COMPARISON_LEDGER = ROUTE_DIR / f"{PREFIX}_SIGNAL_COMPARISON_LEDGER_2026-05-17.jsonl"
SIDECAR_ATTACHMENT_LEDGER = ROUTE_DIR / f"{PREFIX}_SIDECAR_ATTACHMENT_LEDGER_2026-05-17.jsonl"
SYSTEM_SUMMARY_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_SUMMARY_LEDGER_2026-05-17.jsonl"
BUCKET_LEDGER = ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl"
SOURCE_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

INPUT_RESULT = ROUTE_DIR / f"{INPUT_PREFIX}_RESULT_2026-05-17.json"
COMPARISON_PACKET_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_COMPARISON_PACKET_LEDGER_2026-05-17.jsonl"
REVIEW_SIDECAR_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_REVIEW_SIDECAR_LEDGER_2026-05-17.jsonl"
COMPARISON_SCOPE_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_COMPARISON_SCOPE_LEDGER_2026-05-17.jsonl"
SYSTEM_COMPARISON_LEDGER = ROUTE_DIR / f"{INPUT_PREFIX}_SYSTEM_COMPARISON_LEDGER_2026-05-17.jsonl"

BUILDER_MODULE = ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_comparison_summary_2026_05_17.py"
HELPER_MODULE = ROUTE_DIR.parents[3] / "src/research_infra/moonshot_repaired_proxy_runtime_replay_comparison_summary.py"


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


def scope_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("symbol") or ""),
        str(row.get("route_session") or ""),
        str(row.get("horizon_id") or ""),
        str(row.get("registry_family") or ""),
    )


def signal_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("symbol") or ""),
        str(row.get("route_session") or ""),
        str(row.get("horizon_id") or ""),
        str(row.get("source_component") or ""),
    )


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    input_result = read_json(INPUT_RESULT)
    input_packet_rows = read_jsonl(COMPARISON_PACKET_LEDGER)
    input_sidecar_rows = read_jsonl(REVIEW_SIDECAR_LEDGER)
    input_scope_rows = read_jsonl(COMPARISON_SCOPE_LEDGER)
    input_system_rows = read_jsonl(SYSTEM_COMPARISON_LEDGER)
    ledgers = {
        "scope_comparison_rows": read_jsonl(SCOPE_COMPARISON_LEDGER),
        "signal_comparison_rows": read_jsonl(SIGNAL_COMPARISON_LEDGER),
        "sidecar_attachment_rows": read_jsonl(SIDECAR_ATTACHMENT_LEDGER),
        "system_summary_rows": read_jsonl(SYSTEM_SUMMARY_LEDGER),
        "bucket_rows": read_jsonl(BUCKET_LEDGER),
        "source_manifest_rows": read_jsonl(SOURCE_MANIFEST_LEDGER),
    }
    counts = result.get("counts", {})
    for key, rows in ledgers.items():
        if counts.get(key) != len(rows):
            issues.append(f"{key} count mismatch result={counts.get(key)} ledger={len(rows)}")

    scope_classes = Counter(str(row.get("scope_comparison_class")) for row in ledgers["scope_comparison_rows"])
    signal_balances = Counter(str(row.get("signal_count_balance")) for row in ledgers["signal_comparison_rows"])
    attachment_classes = Counter(str(row.get("sidecar_attachment_class")) for row in ledgers["sidecar_attachment_rows"])
    expected = {
        "input_comparison_result_ok": int(bool(input_result.get("ok"))),
        "input_comparison_packet_rows": len(input_packet_rows),
        "input_review_sidecar_rows": len(input_sidecar_rows),
        "input_comparison_scope_rows": len(input_scope_rows),
        "input_system_comparison_rows": len(input_system_rows),
        "scope_comparison_rows": len({scope_key(row) for row in input_packet_rows + input_sidecar_rows}),
        "signal_comparison_rows": len({signal_key(row) for row in input_packet_rows + input_sidecar_rows}),
        "sidecar_attachment_rows": len(input_sidecar_rows),
        "mixed_signal_scope_rows": scope_classes.get("SCOPE_COMPARISON_MIXED_DEFAULT_OFF_AND_AVOID_SIGNALS", 0),
        "default_off_only_scope_rows": scope_classes.get("SCOPE_COMPARISON_DEFAULT_OFF_SIGNAL_ONLY", 0),
        "avoid_redesign_only_scope_rows": scope_classes.get("SCOPE_COMPARISON_AVOID_REDESIGN_SIGNAL_ONLY", 0),
        "represented_context_only_scope_rows": scope_classes.get("SCOPE_COMPARISON_REPRESENTED_CONTEXT_ONLY", 0),
        "sidecar_only_scope_rows": scope_classes.get("SCOPE_COMPARISON_SIDECAR_ONLY_REVIEW", 0),
        "default_off_dominant_signal_rows": signal_balances.get("DEFAULT_OFF_REPRESENTED_COUNT_DOMINANT", 0),
        "avoid_redesign_dominant_signal_rows": signal_balances.get("AVOID_REDESIGN_REPRESENTED_COUNT_DOMINANT", 0),
        "tied_signal_rows": signal_balances.get("DEFAULT_OFF_AND_AVOID_REPRESENTED_COUNTS_TIED", 0),
        "context_only_signal_rows": signal_balances.get("REPRESENTED_CONTEXT_ONLY", 0),
        "sidecar_only_signal_rows": signal_balances.get("SIDECAR_ONLY", 0),
        "sidecars_attached_to_represented_scope_rows": attachment_classes.get(
            "SIDECAR_ATTACHED_TO_REPRESENTED_SCOPE", 0
        ),
        "sidecar_only_review_rows": attachment_classes.get("SIDECAR_ONLY_SCOPE_REVIEW", 0),
        "system_summary_rows": 1,
    }
    for key, value in expected.items():
        if counts.get(key) != value:
            issues.append(f"{key} expected {value} got {counts.get(key)}")
    if not ledgers["system_summary_rows"][0].get("system_comparison_summary"):
        issues.append("system comparison summary row missing text")

    for key, rows in ledgers.items():
        sample = rows[:100] if key == "source_manifest_rows" else rows
        if not all(boundary_ok(row) for row in sample):
            issues.append(f"{key} has rows outside concrete branch-local boundary")
    if not boundary_ok(result):
        issues.append("result is outside concrete branch-local boundary")

    files_to_scan = [
        RESULT_PATH,
        SCOPE_COMPARISON_LEDGER,
        SIGNAL_COMPARISON_LEDGER,
        SIDECAR_ATTACHMENT_LEDGER,
        SYSTEM_SUMMARY_LEDGER,
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
        "scope_comparison_class_counts": dict(sorted(scope_classes.items())),
        "signal_count_balance_counts": dict(sorted(signal_balances.items())),
        "sidecar_attachment_class_counts": dict(sorted(attachment_classes.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    raise SystemExit(0 if not issues else 1)


if __name__ == "__main__":
    main()
