#!/usr/bin/env python3
"""Verify geometry implementation candidates preserve rows and pass self-tests."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_IMPLEMENTATION"
GEOM_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_REPAIR"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
ROW_LEDGER = ROUTE_DIR / f"{PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"
GEOMETRY_ROW_LEDGER = ROUTE_DIR / f"{GEOM_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_implementation.py",
    ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_geometry_implementation_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, ROW_LEDGER, AGGREGATE_LEDGER, SELF_TEST_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]


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


def read_text(path: Path) -> str:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        return handle.read()


def boundary_ok(row: dict[str, Any]) -> bool:
    boundary = row.get("research_boundary") or {}
    return (
        boundary.get("boundary_schema") == "concrete_branch_local_research_boundary_v1"
        and boundary.get("artifact_scope") == "branch_local_research"
        and boundary.get("production_import_path") is False
        and boundary.get("mutates_order_risk_prompt_safety_or_mt5") is False
        and boundary.get("runtime_candidate_use_permitted") is False
        and boundary.get("unconditional_scalar_use_permitted") is False
    )


def blocked_terms() -> list[str]:
    return [
        "NO_" + "PROMOTION_" + "VERDICT",
        "validation" + "_safe",
        "outcome_" + "review_" + "opened",
        "live_" + "effect",
        "safe" + "_flags",
        "owner_" + "r",
        "broker_" + "r",
        "exact_" + "live_" + "r",
        "live_" + "account_" + "truth",
    ]


def scan_blocked_terms(paths: list[Path]) -> list[str]:
    issues: list[str] = []
    terms = blocked_terms()
    for path in paths:
        text = read_text(path)
        for term in terms:
            if term in text:
                issues.append(f"blocked term {term!r} found in {path.relative_to(REPO)}")
    return issues


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    rows = read_jsonl(ROW_LEDGER)
    aggregates = read_jsonl(AGGREGATE_LEDGER)
    self_tests = read_jsonl(SELF_TEST_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    geometry_rows = read_jsonl(GEOMETRY_ROW_LEDGER)
    counts = result.get("counts") or {}

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if len(rows) != len(geometry_rows):
        issues.append(f"implementation rows {len(rows)} != geometry rows {len(geometry_rows)}")
    if len(self_tests) != len(rows):
        issues.append("self-test rows do not match implementation rows")
    if counts.get("geometry_implementation_rows") != len(rows):
        issues.append("implementation row count mismatch")
    if counts.get("aggregate_implementation_rows") != len(aggregates):
        issues.append("aggregate implementation row count mismatch")
    if counts.get("implementation_self_test_rows") != len(self_tests):
        issues.append("self-test row count mismatch")
    if counts.get("self_test_pass_rows") != len(self_tests):
        issues.append("not all self-test rows passed")
    if counts.get("self_test_repair_rows") != 0:
        issues.append("self-test repair rows should be zero")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len({row.get("geometry_implementation_row_id") for row in rows}) != len(rows):
        issues.append("implementation row ids are not unique")
    if len({row.get("input_geometry_repair_row_id") for row in rows}) != len(rows):
        issues.append("geometry repair rows were not preserved one-to-one")
    if any(row.get("implementation_self_test_status") != "GEOMETRY_IMPLEMENTATION_SELF_TEST_PASS" for row in rows):
        issues.append("one or more implementation rows failed embedded self-test")
    if any(row.get("implementation_self_test_status") != "GEOMETRY_IMPLEMENTATION_SELF_TEST_PASS" for row in self_tests):
        issues.append("one or more self-test ledger rows failed")
    if any(not row.get("implementation_payload") for row in rows):
        issues.append("one or more implementation rows lack payload")
    if any(not boundary_ok(row) for row in rows + aggregates + self_tests + system_rows):
        issues.append("one or more ledger rows failed research boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    kind_counts = Counter(row.get("implementation_kind") for row in rows)
    aggregate_action_counts = Counter(row.get("aggregate_implementation_action") for row in aggregates)
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "implementation_kind_counts": dict(sorted(kind_counts.items())),
        "aggregate_implementation_action_counts": dict(sorted(aggregate_action_counts.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
