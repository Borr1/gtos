#!/usr/bin/env python3
"""Verify the final CP282 frozen-universe main handoff packet."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_MAIN_HANDOFF"
DATE = "2026-05-17"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_{DATE}.json"
ARTIFACT_LEDGER = ROUTE_DIR / f"{PREFIX}_ARTIFACT_LEDGER_{DATE}.jsonl"
COUNT_CHECK_LEDGER = ROUTE_DIR / f"{PREFIX}_COUNT_CHECK_LEDGER_{DATE}.jsonl"
CONSUMPTION_ORDER_LEDGER = ROUTE_DIR / f"{PREFIX}_CONSUMPTION_ORDER_LEDGER_{DATE}.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_{DATE}.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_{DATE}.md"
VERIFIER_RESULT = ROUTE_DIR / f"{PREFIX}_VERIFIER_RESULT_{DATE}.json"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_frozen_universe_main_handoff.py",
    ROUTE_DIR / "build_frozen_universe_main_handoff_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    ARTIFACT_LEDGER,
    COUNT_CHECK_LEDGER,
    CONSUMPTION_ORDER_LEDGER,
    ISSUE_LEDGER,
    SYSTEM_LEDGER,
    SUMMARY_PATH,
]


def long_path(path: Path) -> str:
    text = str(path)
    if len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def rel(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def read_json(path: Path) -> dict[str, Any]:
    with open(long_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with open(long_path(path), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line.lstrip("\ufeff"))


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
        with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        for term in blocked_terms():
            if term in text:
                issues.append(f"blocked term {term!r} found in {rel(path)}")
    return issues


def main() -> None:
    issues: list[str] = []
    for path in OUTPUT_FILES:
        if not path.exists():
            issues.append(f"missing output {rel(path)}")
    if issues:
        verdict = {"ok": False, "issues": issues}
        write_json(VERIFIER_RESULT, verdict)
        print(json.dumps(verdict, indent=2, sort_keys=True))
        raise SystemExit(1)

    result = read_json(RESULT_PATH)
    counts = result.get("counts") or {}
    artifacts = list(iter_jsonl(ARTIFACT_LEDGER))
    checks = list(iter_jsonl(COUNT_CHECK_LEDGER))
    order_rows = list(iter_jsonl(CONSUMPTION_ORDER_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if result.get("cp280_role") != "universe_freeze":
        issues.append("CP280 role mismatch")
    if result.get("cp281_role") != "executable_ready_slice_materialization":
        issues.append("CP281 role mismatch")
    if counts.get("artifact_rows") != len(artifacts):
        issues.append("artifact row count mismatch")
    if counts.get("count_check_rows") != len(checks):
        issues.append("count-check row count mismatch")
    if counts.get("consumption_order_rows") != len(order_rows) or len(order_rows) != 5:
        issues.append("consumption order row count mismatch")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    expected_order = [
        "ready_runtime_rules_first",
        "rule_performance_evidence_second",
        "action_execution_proof_third",
        "repair_needed_bundle_fourth",
        "full_frozen_closure_fifth",
    ]
    if [row.get("handoff_class") for row in sorted(order_rows, key=lambda row: row["priority_order"])] != expected_order:
        issues.append("main consumption order mismatch")
    if any(row.get("check_pass") is not True for row in checks):
        issues.append("one or more count checks failed")
    for key, expected in (
        ("implementation_ready_rows_consumed", 461),
        ("follow_rule_inputs", 173),
        ("avoid_filter_inputs", 288),
        ("aggregate_scopes", 107),
        ("represented_source_rows", 6428),
        ("repair_needed_rows_preserved", 243649),
        ("kill_preserve_rows_preserved", 25811),
        ("coverage_rows_preserved", 28474),
        ("main_handoff_rows", 5),
    ):
        if counts.get(key) != expected:
            issues.append(f"{key} expected {expected} got {counts.get(key)}")
    if len(system_rows) != 1 or not boundary_ok(system_rows[0]):
        issues.append("system row missing or boundary failed")
    if any(not boundary_ok(row) for row in artifacts + checks + order_rows + issue_rows + [result]):
        issues.append("one or more output rows failed boundary checks")
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": {
            "artifact_rows": len(artifacts),
            "count_check_rows": len(checks),
            "consumption_order_rows": len(order_rows),
            "issue_rows": len(issue_rows),
            "implementation_ready_rows_consumed": counts.get("implementation_ready_rows_consumed"),
            "repair_needed_rows_preserved": counts.get("repair_needed_rows_preserved"),
        },
    }
    write_json(VERIFIER_RESULT, verdict)
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
