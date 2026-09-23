#!/usr/bin/env python3
"""Verify repaired proxy execution-spec checkpoint artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_EXECUTION_SPECS"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
LEDGERS = {
    "default_off_scorer_spec_rows": ROUTE_DIR / f"{PREFIX}_DEFAULT_OFF_SCORER_SPEC_LEDGER_2026-05-17.jsonl",
    "default_off_scope_rows": ROUTE_DIR / f"{PREFIX}_DEFAULT_OFF_SCOPE_LEDGER_2026-05-17.jsonl",
    "avoid_comparator_spec_rows": ROUTE_DIR / f"{PREFIX}_AVOID_COMPARATOR_SPEC_LEDGER_2026-05-17.jsonl",
    "avoid_scope_rows": ROUTE_DIR / f"{PREFIX}_AVOID_SCOPE_LEDGER_2026-05-17.jsonl",
    "repair_task_rows": ROUTE_DIR / f"{PREFIX}_REPAIR_TASK_LEDGER_2026-05-17.jsonl",
    "repair_scope_rows": ROUTE_DIR / f"{PREFIX}_REPAIR_SCOPE_LEDGER_2026-05-17.jsonl",
    "exact_proxy_bridge_rows": ROUTE_DIR / f"{PREFIX}_EXACT_PROXY_BRIDGE_LEDGER_2026-05-17.jsonl",
    "cost_source_rows": ROUTE_DIR / f"{PREFIX}_COST_SOURCE_LEDGER_2026-05-17.jsonl",
    "cost_symbol_rows": ROUTE_DIR / f"{PREFIX}_COST_SYMBOL_LEDGER_2026-05-17.jsonl",
    "market_population_rows": ROUTE_DIR / f"{PREFIX}_MARKET_EXPANSION_POPULATION_LEDGER_2026-05-17.jsonl",
    "source_search_rows": ROUTE_DIR / f"{PREFIX}_EXACT_R_SOURCE_SEARCH_LEDGER_2026-05-17.jsonl",
    "system_recommendation_rows": ROUTE_DIR / f"{PREFIX}_SYSTEM_RECOMMENDATION_LEDGER_2026-05-17.jsonl",
    "bucket_rows": ROUTE_DIR / f"{PREFIX}_BUCKET_LEDGER_2026-05-17.jsonl",
    "source_manifest_rows": ROUTE_DIR / f"{PREFIX}_SOURCE_MANIFEST_LEDGER_2026-05-17.jsonl",
}
OTHER_OUTPUTS = [
    RESULT_PATH,
    ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md",
]
LEGACY_TOKENS = [
    "NO_" + "PROMOTION_VERDICT",
    "validation_" + "safe",
    "outcome_review_" + "opened",
    "live_" + "effect",
    "safe_" + "flags",
]


def long_path(path: Path) -> str:
    text = str(path)
    if len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def count_jsonl(path: Path) -> int:
    count = 0
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                json.loads(line)
                count += 1
    return count


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def token_scan(paths: list[Path]) -> list[str]:
    issues = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in LEGACY_TOKENS:
            if token in text:
                issues.append(f"legacy_boundary_token:{path.name}:{token}")
    return issues


def main() -> int:
    issues = []
    result = read_json(RESULT_PATH)
    counts = result.get("counts") or {}
    actual_counts = {}
    for key, path in LEDGERS.items():
        actual = count_jsonl(path)
        actual_counts[key] = actual
        if actual != counts.get(key):
            issues.append(f"count_mismatch:{key}:expected={counts.get(key)}:actual={actual}")

    if counts.get("input_default_off_rows") != 12303:
        issues.append("default_input_count_not_12303")
    if counts.get("input_avoid_redesign_rows") != 5443:
        issues.append("avoid_input_count_not_5443")
    if counts.get("input_repair_required_rows") != 170:
        issues.append("repair_input_count_not_170")
    if counts.get("default_off_scope_rows") != 102:
        issues.append("default_scope_count_not_102")
    if counts.get("avoid_scope_rows") != 154:
        issues.append("avoid_scope_count_not_154")
    if counts.get("repair_scope_rows") != 34:
        issues.append("repair_scope_count_not_34")
    if not result.get("input_denominator_preserved"):
        issues.append("input_denominator_not_preserved")
    if counts.get("market_population_rows", 0) <= 0:
        issues.append("market_population_rows_missing")
    if counts.get("cost_source_rows", 0) <= 0:
        issues.append("cost_source_rows_missing")
    boundary = result.get("research_boundary") or {}
    if boundary.get("boundary_schema") != "concrete_branch_local_research_boundary_v1":
        issues.append("boundary_schema_mismatch")
    if boundary.get("runtime_candidate_use_permitted") is not False:
        issues.append("runtime_candidate_use_boundary_open")
    if boundary.get("unconditional_scalar_use_permitted") is not False:
        issues.append("scalar_use_boundary_open")

    issues.extend(token_scan(list(LEDGERS.values()) + OTHER_OUTPUTS))
    print(json.dumps({"ok": not issues, "issues": issues, "counts": actual_counts}, indent=2, sort_keys=True))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
