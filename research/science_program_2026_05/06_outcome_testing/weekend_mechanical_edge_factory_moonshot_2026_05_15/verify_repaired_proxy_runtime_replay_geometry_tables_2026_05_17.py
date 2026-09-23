#!/usr/bin/env python3
"""Verify concrete geometry tables preserve implementation candidates."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_TABLES"
IMPL_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_LOCAL_REPAIRED_PROXY_RUNTIME_REPLAY_GEOMETRY_IMPLEMENTATION"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
SCORER_TABLE_LEDGER = ROUTE_DIR / f"{PREFIX}_SCORER_TABLE_LEDGER_2026-05-17.jsonl"
AVOID_TABLE_LEDGER = ROUTE_DIR / f"{PREFIX}_AVOID_INTELLIGENCE_TABLE_LEDGER_2026-05-17.jsonl"
KILL_TABLE_LEDGER = ROUTE_DIR / f"{PREFIX}_KILL_TABLE_LEDGER_2026-05-17.jsonl"
REDIRECTION_TASK_LEDGER = ROUTE_DIR / f"{PREFIX}_REDIRECTION_TASK_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

IMPLEMENTATION_ROW_LEDGER = ROUTE_DIR / f"{IMPL_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
IMPLEMENTATION_AGGREGATE_LEDGER = ROUTE_DIR / f"{IMPL_PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_tables.py",
    ROUTE_DIR / "build_branch_local_repaired_proxy_runtime_replay_geometry_tables_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    SCORER_TABLE_LEDGER,
    AVOID_TABLE_LEDGER,
    KILL_TABLE_LEDGER,
    REDIRECTION_TASK_LEDGER,
    SYSTEM_LEDGER,
    SUMMARY_PATH,
]


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


def table_input_ids(rows: list[dict[str, Any]], field: str) -> set[str]:
    return {str(row.get(field)) for row in rows if row.get(field)}


def table_row_ids(rows: list[dict[str, Any]]) -> list[str]:
    ids: list[str] = []
    for row in rows:
        row_id_field = next((key for key in row if key.endswith("_row_id")), "")
        ids.append(str(row.get(row_id_field)))
    return ids


def validate_required_fields(rows: list[dict[str, Any]], fields: list[str], row_id_field: str) -> list[str]:
    issues: list[str] = []
    for row in rows:
        for field in fields:
            if field not in row:
                issues.append(f"missing table field {field} on {row.get(row_id_field)}")
    return issues


def main() -> None:
    issues: list[str] = []
    result = read_json(RESULT_PATH)
    scorer_rows = read_jsonl(SCORER_TABLE_LEDGER)
    avoid_rows = read_jsonl(AVOID_TABLE_LEDGER)
    kill_rows = read_jsonl(KILL_TABLE_LEDGER)
    redirection_rows = read_jsonl(REDIRECTION_TASK_LEDGER)
    system_rows = read_jsonl(SYSTEM_LEDGER)
    implementation_rows = read_jsonl(IMPLEMENTATION_ROW_LEDGER)
    aggregate_rows = read_jsonl(IMPLEMENTATION_AGGREGATE_LEDGER)
    counts = result.get("counts") or {}

    implementation_kind_counts = Counter(row.get("implementation_kind") for row in implementation_rows)
    aggregate_action_counts = Counter(row.get("aggregate_implementation_action") for row in aggregate_rows)
    table_rows = scorer_rows + avoid_rows + kill_rows + redirection_rows

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if counts.get("input_implementation_result_ok") != 1:
        issues.append("input implementation result was not marked ok")
    if counts.get("input_implementation_rows") != len(implementation_rows):
        issues.append("input implementation row count mismatch")
    if counts.get("input_aggregate_implementation_rows") != len(aggregate_rows):
        issues.append("input aggregate row count mismatch")
    if counts.get("scorer_table_rows") != len(scorer_rows):
        issues.append("scorer table count mismatch")
    if counts.get("avoid_intelligence_table_rows") != len(avoid_rows):
        issues.append("avoid table count mismatch")
    if counts.get("kill_table_rows") != len(kill_rows):
        issues.append("kill table count mismatch")
    if counts.get("redirection_task_rows") != len(redirection_rows):
        issues.append("redirection task count mismatch")
    if counts.get("system_rows") != len(system_rows):
        issues.append("system row count mismatch")
    if len(system_rows) != 1:
        issues.append("system ledger must contain one row")
    row_ids = table_row_ids(table_rows)
    if len(row_ids) != len(set(row_ids)):
        issues.append("one or more table row ids are duplicated")

    expected_scorer = implementation_kind_counts.get("GEOMETRY_SCORER_PROTOTYPE_IMPLEMENTATION", 0)
    expected_avoid = implementation_kind_counts.get("GEOMETRY_AVOID_INTELLIGENCE_IMPLEMENTATION", 0)
    expected_kill = (
        implementation_kind_counts.get("GEOMETRY_AVOID_COMPARATOR_KILL_IMPLEMENTATION", 0)
        + implementation_kind_counts.get("GEOMETRY_DEFAULT_OFF_KILL_IMPLEMENTATION", 0)
    )
    expected_redirection = aggregate_action_counts.get("OPEN_BRANCH_LOCAL_REDIRECTION_TASK_FOR_AGGREGATE", 0)

    if len(scorer_rows) != expected_scorer:
        issues.append(f"scorer table rows {len(scorer_rows)} != expected {expected_scorer}")
    if len(avoid_rows) != expected_avoid:
        issues.append(f"avoid table rows {len(avoid_rows)} != expected {expected_avoid}")
    if len(kill_rows) != expected_kill:
        issues.append(f"kill table rows {len(kill_rows)} != expected {expected_kill}")
    if len(redirection_rows) != expected_redirection:
        issues.append(f"redirection task rows {len(redirection_rows)} != expected {expected_redirection}")

    implementation_ids = {str(row.get("geometry_implementation_row_id")) for row in implementation_rows}
    aggregate_ids = {str(row.get("aggregate_implementation_row_id")) for row in aggregate_rows}
    if not table_input_ids(scorer_rows + avoid_rows + kill_rows, "input_geometry_implementation_row_id").issubset(
        implementation_ids
    ):
        issues.append("one or more table rows reference unknown implementation rows")
    if not table_input_ids(redirection_rows, "input_aggregate_implementation_row_id").issubset(aggregate_ids):
        issues.append("one or more redirection rows reference unknown aggregate rows")
    if any(not boundary_ok(row) for row in table_rows + system_rows):
        issues.append("one or more table rows failed research boundary checks")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if any(row.get("table_application_status") != "BRANCH_LOCAL_GEOMETRY_SCORER_TABLE_READY" for row in scorer_rows):
        issues.append("one or more scorer rows have wrong status")
    if any(
        row.get("table_application_status") != "BRANCH_LOCAL_GEOMETRY_AVOID_INTELLIGENCE_TABLE_READY"
        for row in avoid_rows
    ):
        issues.append("one or more avoid rows have wrong status")
    if any(row.get("table_application_status") != "BRANCH_LOCAL_GEOMETRY_KILL_TABLE_READY" for row in kill_rows):
        issues.append("one or more kill rows have wrong status")
    if any(
        row.get("table_application_status") != "BRANCH_LOCAL_REDIRECTION_TASK_READY"
        for row in redirection_rows
    ):
        issues.append("one or more redirection rows have wrong status")

    shared_fields = [
        "branch_local_table_key",
        "symbol",
        "route_session",
        "market_timeframe",
        "horizon_id",
        "source_component",
        "path_order_result",
        "expected_cost_adjusted_geometry_r",
        "remaining_missing_geometry_fields",
        "table_application_status",
    ]
    issues.extend(validate_required_fields(scorer_rows, shared_fields, "geometry_scorer_table_row_id"))
    issues.extend(validate_required_fields(avoid_rows, shared_fields, "geometry_avoid_table_row_id"))
    issues.extend(validate_required_fields(kill_rows, shared_fields + ["kill_reason"], "geometry_kill_table_row_id"))

    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": counts,
        "implementation_kind_counts": dict(sorted(implementation_kind_counts.items())),
        "aggregate_action_counts": dict(sorted(aggregate_action_counts.items())),
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
