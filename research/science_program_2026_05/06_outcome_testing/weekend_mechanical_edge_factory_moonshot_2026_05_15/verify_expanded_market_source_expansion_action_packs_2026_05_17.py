#!/usr/bin/env python3
"""Verify expanded-market source-expansion action packs checkpoint."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
APPLICATION_PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_APPLICATION"
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_EXPANDED_MARKET_SOURCE_EXPANSION_ACTION_PACKS"

APPLICATION_RESULT = ROUTE_DIR / f"{APPLICATION_PREFIX}_RESULT_2026-05-17.json"
APPLICATION_ROW_LEDGER = ROUTE_DIR / f"{APPLICATION_PREFIX}_ROW_LEDGER_2026-05-17.jsonl"
APPLICATION_RULE_LEDGER = ROUTE_DIR / f"{APPLICATION_PREFIX}_RULE_LEDGER_2026-05-17.jsonl"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_2026-05-17.json"
PACK_LEDGER = ROUTE_DIR / f"{PREFIX}_PACK_LEDGER_2026-05-17.jsonl"
WORK_LEDGER = ROUTE_DIR / f"{PREFIX}_WORK_LEDGER_2026-05-17.jsonl"
SELF_TEST_LEDGER = ROUTE_DIR / f"{PREFIX}_SELF_TEST_LEDGER_2026-05-17.jsonl"
AGGREGATE_LEDGER = ROUTE_DIR / f"{PREFIX}_AGGREGATE_LEDGER_2026-05-17.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_2026-05-17.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_2026-05-17.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_expanded_market_source_expansion_action_packs.py",
    ROUTE_DIR / "build_expanded_market_source_expansion_action_packs_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    PACK_LEDGER,
    WORK_LEDGER,
    SELF_TEST_LEDGER,
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


def application_ids_and_applied() -> tuple[set[str], set[str], int]:
    all_ids: set[str] = set()
    applied_ids: set[str] = set()
    rule_ids: set[str] = set()
    for row in iter_jsonl(APPLICATION_ROW_LEDGER):
        row_id = str(row.get("expanded_market_source_expansion_action_application_row_id") or "")
        all_ids.add(row_id)
        if row.get("action_application_status") in {
            "ACTION_APPLICATION_EXACT_RULE_APPLIED",
            "ACTION_APPLICATION_SCOPE_RULE_APPLIED",
        }:
            applied_ids.add(row_id)
            rule_ids.add(str(row.get("input_action_application_rule_row_id") or ""))
    return all_ids, applied_ids, len(rule_ids)


def main() -> None:
    issues: list[str] = []
    application_result = read_json(APPLICATION_RESULT)
    result = read_json(RESULT_PATH)
    counts = result.get("counts") or {}
    all_application_ids, applied_application_ids, input_rule_count = application_ids_and_applied()

    pack_rows = list(iter_jsonl(PACK_LEDGER))
    work_rows = list(iter_jsonl(WORK_LEDGER))
    self_tests = list(iter_jsonl(SELF_TEST_LEDGER))
    aggregate_rows = list(iter_jsonl(AGGREGATE_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))

    pack_application_ids = {
        str(row.get("input_source_expansion_action_application_row_id") or "") for row in pack_rows
    }
    work_application_ids = {
        str(row.get("input_source_expansion_action_application_row_id") or "") for row in work_rows
    }
    pack_ids = {
        str(row.get("expanded_market_source_expansion_action_pack_row_id") or "") for row in pack_rows
    }
    self_test_pack_ids = {str(row.get("input_action_pack_row_id") or "") for row in self_tests}

    if application_result.get("ok") is not True:
        issues.append("input action-application result is not ok")
    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if pack_application_ids != applied_application_ids:
        issues.append("action packs do not cover exactly the applied CP269 action rows")
    if pack_application_ids & work_application_ids:
        issues.append("one or more application rows appears in both pack and work ledgers")
    if pack_application_ids | work_application_ids != all_application_ids:
        issues.append("pack/work ledgers do not consume every application row exactly once")
    if len(pack_ids) != len(pack_rows):
        issues.append("action pack row ids are not unique")
    if self_test_pack_ids != pack_ids:
        issues.append("self-tests do not cover every action pack exactly once")
    if any(row.get("self_test_status") != "ACTION_PACK_SELF_TEST_PASS" for row in self_tests):
        issues.append("one or more action pack self-tests failed")
    if any(not row.get("branch_local_action_pack_expression_sha256") for row in pack_rows):
        issues.append("one or more action packs lacks expression hash")
    if any(row.get("cost_adjusted_simulated_r") is None for row in pack_rows):
        issues.append("one or more action packs lacks simulated R")
    if any(not row.get("missing_work_fields") for row in work_rows):
        issues.append("one or more work rows lacks missing work fields")
    if any(not row.get("branch_local_action_pack_work_expression_sha256") for row in work_rows):
        issues.append("one or more work rows lacks work expression hash")

    pack_kind_counts = Counter(row.get("action_pack_kind") for row in pack_rows)
    work_status_counts = Counter(row.get("work_status") for row in work_rows)
    decision_counts = Counter(
        [row.get("keep_kill_redesign_implement_decision") for row in pack_rows]
        + [row.get("keep_kill_redesign_implement_decision") for row in work_rows]
    )
    if counts.get("input_application_rows") != len(all_application_ids):
        issues.append("input application row count mismatch")
    if counts.get("input_action_rule_rows") != sum(1 for _ in iter_jsonl(APPLICATION_RULE_LEDGER)):
        issues.append("input action rule count mismatch")
    if counts.get("action_pack_rows") != len(pack_rows):
        issues.append("action pack row count mismatch")
    if counts.get("replay_work_rows") != len(work_rows):
        issues.append("replay work row count mismatch")
    if counts.get("self_test_rows") != len(self_tests):
        issues.append("self-test row count mismatch")
    if counts.get("self_test_pass_rows") != len(self_tests):
        issues.append("self-test pass count mismatch")
    if counts.get("pack_kind_counts") != dict(sorted(pack_kind_counts.items())):
        issues.append("pack kind count mismatch")
    if counts.get("work_status_counts") != dict(sorted(work_status_counts.items())):
        issues.append("work status count mismatch")
    if counts.get("decision_counts") != dict(sorted(decision_counts.items())):
        issues.append("decision count mismatch")
    if counts.get("aggregate_rows") != len(aggregate_rows):
        issues.append("aggregate row count mismatch")
    if sum(int(row.get("row_count") or 0) for row in aggregate_rows) != len(pack_rows) + len(work_rows):
        issues.append("aggregate row counts do not sum to pack plus work rows")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    if len(system_rows) != 1 or counts.get("system_rows") != 1:
        issues.append("system ledger must contain one row")
    if input_rule_count <= 0:
        issues.append("applied action rows did not reference input rules")
    if not any(str(kind).endswith("follow-action-pack") for kind in pack_kind_counts):
        issues.append("follow action pack is absent")
    if not any(str(kind).endswith("avoid-intelligence-action-pack") for kind in pack_kind_counts):
        issues.append("avoid action pack is absent")
    if not any(str(kind).endswith("default-off-action-pack") for kind in pack_kind_counts):
        issues.append("default-off action pack is absent")
    if any(
        not boundary_ok(row)
        for row in pack_rows + work_rows + self_tests + aggregate_rows + issue_rows + system_rows + [result]
    ):
        issues.append("one or more output rows failed branch-local boundary checks")
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": {
            "action_pack_rows": len(pack_rows),
            "replay_work_rows": len(work_rows),
            "self_test_rows": len(self_tests),
            "aggregate_rows": len(aggregate_rows),
            "issue_rows": len(issue_rows),
        },
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
