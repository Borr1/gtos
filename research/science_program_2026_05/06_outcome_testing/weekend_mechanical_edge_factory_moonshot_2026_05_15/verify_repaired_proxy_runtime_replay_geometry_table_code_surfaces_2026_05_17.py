#!/usr/bin/env python3
"""Verify executable branch-local code surfaces from geometry table candidates."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_SURFACES"
CAND_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLE_CODE_CANDIDATES"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SCORER_SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_SURFACE_LEDGER_2026-05-17.jsonl"
AVOID_SURFACE_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_SURFACE_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

SCORER_CANDIDATE_LEDGER = ROUTE_DIR / f"{CAND_PREFIX}_SCORER_CODE_CANDIDATE_LEDGER_2026-05-17.jsonl"
AVOID_CANDIDATE_LEDGER = ROUTE_DIR / f"{CAND_PREFIX}_AVOID_CODE_CANDIDATE_LEDGER_2026-05-17.jsonl"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_table_code_surfaces.py",
    ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_geometry_table_code_surfaces_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [RESULT_PATH, SCORER_SURFACE_LEDGER, AVOID_SURFACE_LEDGER, SELF_TEST_LEDGER, AGGREGATE_LEDGER, SYSTEM_LEDGER, SUMMARY_PATH]


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


def validate_surface_fields(rows: list[dict[str, Any]]) -> list[str]:
    required = [
        "geometry_table_code_surface_row_id",
        "input_geometry_table_code_candidate_row_id",
        "code_surface_kind",
        "surface_function",
        "surface_module",
        "surface_action",
        "surface_cost_adjusted_simulated_r",
        "surface_scope_fields",
        "production_import_permitted",
        "symbol",
        "route_session",
        "market_timeframe",
        "horizon_id",
        "source_component",
        "source_file_sha256",
        "path_order_result",
    ]
    issues: list[str] = []
    for row in rows:
        for field in required:
            if field not in row:
                issues.append(f"missing surface field {field} on {row.get('geometry_table_code_surface_row_id')}")
    return issues


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    scorer_rows = read_jsonl(SCORER_SURFACE_LEDGER)
    avoid_rows = read_jsonl(AVOID_SURFACE_LEDGER)
    self_tests = read_jsonl(SELF_TEST_LEDGER)
    aggregate_rows = read_jsonl(AGGREGATE_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    scorer_candidates = read_jsonl(SCORER_CANDIDATE_LEDGER)
    avoid_candidates = read_jsonl(AVOID_CANDIDATE_LEDGER)
    counts = result.get("counts") or {}
    all_rows = scorer_rows + avoid_rows

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if counts.get("input_candidate_result_ok") != 1:
        issues.append("input candidate result was not marked ok")
    if len(scorer_rows) != len(scorer_candidates):
        issues.append("scorer surfaces do not preserve scorer candidates")
    if len(avoid_rows) != len(avoid_candidates):
        issues.append("avoid surfaces do not preserve avoid candidates")
    if counts.get("total_code_surface_rows") != len(all_rows):
        issues.append("total surface count mismatch")
    if counts.get("surface_self_test_rows") != len(self_tests):
        issues.append("self-test count mismatch")
    if counts.get("self_test_pass_rows") != len(self_tests):
        issues.append("not all surface self-tests passed")
    if counts.get("self_test_repair_rows") != 0:
        issues.append("surface self-test repair rows should be zero")
    if counts.get("aggregate_code_surface_rows") != len(aggregate_rows):
        issues.append("aggregate surface count mismatch")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    if len({row.get("geometry_table_code_surface_row_id") for row in all_rows}) != len(all_rows):
        issues.append("surface row ids are not unique")
    if any(row.get("surface_cost_adjusted_simulated_r") is None for row in all_rows):
        issues.append("one or more surfaces lack simulated R")
    if any(row.get("production_import_permitted") is not False for row in all_rows):
        issues.append("one or more surfaces permit production import")
    if any(row.get("surface_self_test_status") != "GEOMETRY_CODE_SURFACE_SELF_TEST_PASS" for row in self_tests):
        issues.append("one or more self-tests did not pass")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(all_rows):
        issues.append("aggregate row counts do not sum to surfaces")
    if any(not boundary_ok(row) for row in all_rows + self_tests + aggregate_rows + system_rows):
        issues.append("one or more ledger rows failed research boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")

    issues.extend(validate_surface_fields(all_rows))
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    actions = Counter(row.get("surface_action") for row in all_rows)
    tests = Counter(row.get("surface_self_test_status") for row in self_tests)
    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "surface_action_counts": dict(sorted(actions.items())),
        "surface_self_test_status_counts": dict(sorted(tests.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
