#!/usr/bin/env python3
"""Verify expanded-market source-expansion action pack execution checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
APPLICATION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_APPLICATION"
PACK_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACKS"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACK_EXECUTION"

APPLICATION_ROW_LEDGER = ROUTE_DIR / f"{APPLICATION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
PACK_RESULT = ROUTE_DIR / f"{PACK_PREFIX}_RESULT_2026-05-17.json"
PACK_LEDGER = ROUTE_DIR / f"{PACK_PREFIX}_PACK_LEDGER_2026-05-17.jsonl"
WORK_LEDGER = ROUTE_DIR / f"{PACK_PREFIX}_WORK_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_EXECUTION_LEDGER_2026-05-17.jsonl"
MATCH_LEDGER = ROUTE_DIR / f"{PREFIX}_MATCH_LEDGER_2026-05-17.jsonl"
WORK_EXECUTION_LEDGER = ROUTE_DIR / f"{PREFIX}_WORK_EXECUTION_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_source_expansion_action_pack_execution.py",
    ROUTE_DIR / "build_expanded_market_source_expansion_action_pack_execution_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    EXECUTION_LEDGER,
    MATCH_LEDGER,
    WORK_EXECUTION_LEDGER,
    AGGREGATE_LEDGER,
    ISSUE_LEDGER,
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


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


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
    for path in paths:
        text = read_text(path)
        for term in blocked_terms():
            if term in text:
                issues.append(f"blocked term {term!r} found in {path.relative_to(REPO)}")
    return issues


def count_jsonl(path: Path) -> int:
    return sum(1 for _ in iter_jsonl(path))


def main() -> None:
    issues: list[str] = []
    pack_result = read_json(PACK_RESULT)
    result = read_json(RESULT_PATH)
    counts = result.get("counts") or {}
    application_count = count_jsonl(APPLICATION_ROW_LEDGER)
    pack_count = count_jsonl(PACK_LEDGER)
    work_count = count_jsonl(WORK_LEDGER)

    execution_rows = list(iter_jsonl(EXECUTION_LEDGER))
    match_rows = list(iter_jsonl(MATCH_LEDGER))
    work_execution_rows = list(iter_jsonl(WORK_EXECUTION_LEDGER))
    aggregate_rows = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))

    execution_ids = {
        str(row.get("expanded_market_source_expansion_action_pack_execution_row_id") or "")
        for row in execution_rows
    }
    matched_execution_ids = {
        str(row.get("input_action_pack_execution_row_id") or "") for row in match_rows
    }
    status_counts = Counter(row.get("action_pack_execution_status") for row in execution_rows)
    work_status_counts = Counter(row.get("work_status") for row in work_execution_rows)

    if pack_result.get("ok") is not True:
        issues.append("input action-pack result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if counts.get("candidate_application_rows") != application_count:
        issues.append("candidate application row count mismatch")
    if counts.get("input_action_pack_rows") != pack_count:
        issues.append("input action pack count mismatch")
    if counts.get("input_work_rows") != work_count:
        issues.append("input work row count mismatch")
    if counts.get("action_pack_execution_rows") != len(execution_rows) or len(execution_rows) != pack_count:
        issues.append("action pack execution row count mismatch")
    if len(execution_ids) != len(execution_rows):
        issues.append("action pack execution ids are not unique")
    if any(row.get("action_pack_execution_status") != "ACTION_PACK_EXECUTION_PASS" for row in execution_rows):
        issues.append("one or more action pack executions failed")
    if any(int(row.get("candidate_rows_scanned") or 0) != application_count for row in execution_rows):
        issues.append("one or more action pack executions did not scan every candidate row")
    if any(int(row.get("match_count") or 0) < 1 for row in execution_rows):
        issues.append("one or more action pack executions has no match row")
    if not matched_execution_ids.issubset(execution_ids):
        issues.append("one or more match rows references an unknown execution row")
    if counts.get("match_rows") != len(match_rows):
        issues.append("match row count mismatch")
    if counts.get("work_execution_rows") != len(work_execution_rows) or len(work_execution_rows) != work_count:
        issues.append("work execution row count mismatch")
    if any(row.get("work_execution_status") != "ACTION_PACK_WORK_EXECUTION_PRESERVED" for row in work_execution_rows):
        issues.append("one or more work execution rows is not preserved")
    if any(not row.get("missing_work_fields") for row in work_execution_rows):
        issues.append("one or more work execution rows lacks missing work fields")
    if counts.get("action_pack_execution_pass_rows") != status_counts.get("ACTION_PACK_EXECUTION_PASS", 0):
        issues.append("action pack pass count mismatch")
    if counts.get("execution_status_counts") != dict(sorted(status_counts.items())):
        issues.append("execution status count mismatch")
    if counts.get("work_status_counts") != dict(sorted(work_status_counts.items())):
        issues.append("work status count mismatch")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(execution_rows) + len(work_execution_rows):
        issues.append("aggregate row counts do not sum to execution plus work rows")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    if len(system_rows) != 1 or counts.get("system_rows") != 1:
        issues.append("system ledger must contain one row")
    if any(
        not boundary_ok(row)
        for row in execution_rows
        + match_rows
        + work_execution_rows
        + aggregate_rows
        + issue_rows
        + system_rows
        + [result]
    ):
        issues.append("one or more output rows failed branch-local boundary checks")
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": {
            "action_pack_execution_rows": len(execution_rows),
            "match_rows": len(match_rows),
            "work_execution_rows": len(work_execution_rows),
            "aggregate_rows": len(aggregate_rows),
            "issue_rows": len(issue_rows),
        },
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
