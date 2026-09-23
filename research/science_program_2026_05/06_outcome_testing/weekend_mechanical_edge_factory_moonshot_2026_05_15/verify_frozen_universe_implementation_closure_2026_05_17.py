#!/usr/bin/env python3
"""Verify the frozen moonshot implementation-readiness closure packet."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterator


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]
PREFIX = "HISTORICAL_OHLC_GTOS_REPLAY_FROZEN_UNIVERSE_IMPLEMENTATION_CLOSURE"
DATE = "2026-05-17"

RESULT_PATH = ROUTE_DIR / f"{PREFIX}_RESULT_{DATE}.json"
FROZEN_MANIFEST_LEDGER = ROUTE_DIR / f"{PREFIX}_FROZEN_UNIVERSE_MANIFEST_LEDGER_{DATE}.jsonl"
COVERAGE_LEDGER = ROUTE_DIR / f"{PREFIX}_MARKET_TIMEFRAME_SOURCE_COVERAGE_LEDGER_{DATE}.jsonl"
ACTION_CLOSURE_LEDGER = ROUTE_DIR / f"{PREFIX}_ACTION_CLOSURE_LEDGER_{DATE}.jsonl"
IMPLEMENTATION_READY_LEDGER = ROUTE_DIR / f"{PREFIX}_IMPLEMENTATION_READY_BUNDLE_LEDGER_{DATE}.jsonl"
REPAIR_NEEDED_LEDGER = ROUTE_DIR / f"{PREFIX}_REPAIR_NEEDED_BUNDLE_LEDGER_{DATE}.jsonl"
KILL_PRESERVE_LEDGER = ROUTE_DIR / f"{PREFIX}_KILL_PRESERVE_LEDGER_{DATE}.jsonl"
MAIN_HANDOFF_LEDGER = ROUTE_DIR / f"{PREFIX}_MAIN_HANDOFF_BUNDLE_LEDGER_{DATE}.jsonl"
COMPLETION_AUDIT_LEDGER = ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_LEDGER_{DATE}.jsonl"
ISSUE_LEDGER = ROUTE_DIR / f"{PREFIX}_ISSUE_LEDGER_{DATE}.jsonl"
SYSTEM_LEDGER = ROUTE_DIR / f"{PREFIX}_SYSTEM_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"{PREFIX}_SUMMARY_{DATE}.md"

CODE_FILES = [
    REPO / "src/research_infra/moonshot_frozen_universe_implementation_closure.py",
    ROUTE_DIR / "build_frozen_universe_implementation_closure_2026_05_17.py",
    Path(__file__),
]
OUTPUT_FILES = [
    RESULT_PATH,
    FROZEN_MANIFEST_LEDGER,
    COVERAGE_LEDGER,
    ACTION_CLOSURE_LEDGER,
    IMPLEMENTATION_READY_LEDGER,
    REPAIR_NEEDED_LEDGER,
    KILL_PRESERVE_LEDGER,
    MAIN_HANDOFF_LEDGER,
    COMPLETION_AUDIT_LEDGER,
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


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line.lstrip("\ufeff"))


def count_jsonl(path: Path) -> int:
    return sum(1 for _ in iter_jsonl(path))


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
        if not path.exists():
            issues.append(f"missing file for blocked-term scan: {rel(path)}")
            continue
        with open(long_path(path), "r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, start=1):
                for term in terms:
                    if term in line:
                        issues.append(f"blocked term {term!r} found in {rel(path)}:{line_no}")
    return issues


def stream_validate_action_rows(path: Path) -> tuple[int, Counter, list[str]]:
    issues: list[str] = []
    counts: Counter = Counter()
    rows = 0
    for row in iter_jsonl(path):
        rows += 1
        classification = row.get("classification")
        counts[str(classification)] += 1
        if not classification:
            issues.append(f"missing classification at action row {rows}")
        if not row.get("concrete_outcome"):
            issues.append(f"missing concrete outcome at action row {rows}")
        if not row.get("source_artifact_path"):
            issues.append(f"missing source artifact at action row {rows}")
        if not boundary_ok(row):
            issues.append(f"boundary failure at action row {rows}")
        if len(issues) > 20:
            break
    return rows, counts, issues


def stream_validate_bundle(path: Path, id_field: str) -> tuple[int, list[str]]:
    issues: list[str] = []
    rows = 0
    for row in iter_jsonl(path):
        rows += 1
        if not row.get(id_field):
            issues.append(f"missing {id_field} at row {rows}")
        if not row.get("concrete_outcome"):
            issues.append(f"missing concrete outcome at row {rows}")
        if not row.get("code_surface"):
            issues.append(f"missing code surface at row {rows}")
        if not boundary_ok(row):
            issues.append(f"boundary failure at row {rows}")
        if len(issues) > 20:
            break
    return rows, issues


def main() -> None:
    issues: list[str] = []
    for path in OUTPUT_FILES:
        if not path.exists():
            issues.append(f"missing output file {rel(path)}")
    if issues:
        print(json.dumps({"ok": False, "issues": issues}, indent=2, sort_keys=True))
        raise SystemExit(1)

    result = read_json(RESULT_PATH)
    counts = result.get("counts") or {}
    manifest_rows = count_jsonl(FROZEN_MANIFEST_LEDGER)
    coverage_rows = count_jsonl(COVERAGE_LEDGER)
    action_rows, action_class_counts, action_issues = stream_validate_action_rows(
        ACTION_CLOSURE_LEDGER
    )
    impl_rows, impl_issues = stream_validate_bundle(
        IMPLEMENTATION_READY_LEDGER, "implementation_ready_bundle_row_id"
    )
    repair_rows, repair_issues = stream_validate_bundle(
        REPAIR_NEEDED_LEDGER, "repair_needed_bundle_row_id"
    )
    kill_rows, kill_issues = stream_validate_bundle(
        KILL_PRESERVE_LEDGER, "kill_preserve_bundle_row_id"
    )
    handoff_rows = count_jsonl(MAIN_HANDOFF_LEDGER)
    audit_rows = list(iter_jsonl(COMPLETION_AUDIT_LEDGER))
    issue_rows = list(iter_jsonl(ISSUE_LEDGER))
    system_rows = list(iter_jsonl(SYSTEM_LEDGER))

    if result.get("ok") is not True:
        issues.append("result ok is not true")
    if not boundary_ok(result):
        issues.append("result boundary failed")
    if counts.get("input_artifacts_consumed") != manifest_rows:
        issues.append("manifest row count mismatch")
    if counts.get("coverage_rows") != coverage_rows:
        issues.append("coverage row count mismatch")
    if counts.get("action_closure_rows") != action_rows:
        issues.append("action closure row count mismatch")
    if counts.get("implementation_ready_rows") != impl_rows:
        issues.append("implementation-ready row count mismatch")
    if counts.get("repair_needed_rows") != repair_rows:
        issues.append("repair-needed row count mismatch")
    if counts.get("kill_preserve_rows") != kill_rows:
        issues.append("kill/preserve row count mismatch")
    if counts.get("main_handoff_rows") != handoff_rows:
        issues.append("main handoff row count mismatch")
    if counts.get("issue_rows") != len(issue_rows) or issue_rows:
        issues.append("issue ledger must be empty")
    if len(audit_rows) != 1:
        issues.append("completion audit must have one row")
    else:
        audit = audit_rows[0]
        if not boundary_ok(audit):
            issues.append("completion audit boundary failed")
        for field in (
            "no_new_discovery_lane",
            "no_top_n_cutoff",
            "all_input_artifacts_hashed",
            "all_jsonl_rows_scanned",
            "all_action_rows_have_concrete_outcome",
            "all_market_source_rows_accounted_in_coverage",
        ):
            if audit.get(field) is not True:
                issues.append(f"completion audit field {field} is not true")
        if audit.get("representative_sampling_used") is not False:
            issues.append("completion audit indicates representative sampling")
        if int(audit.get("unclassified_action_rows") or 0) != 0:
            issues.append("completion audit has unclassified action rows")
    if len(system_rows) != 1 or not boundary_ok(system_rows[0]):
        issues.append("system ledger row missing or boundary failed")
    if action_class_counts.get("implementation_ready", 0) != impl_rows:
        issues.append("implementation-ready classification count mismatch")
    if not impl_rows:
        issues.append("implementation-ready bundle is empty")
    if not repair_rows:
        issues.append("repair-needed bundle is empty")
    if not kill_rows:
        issues.append("kill/preserve bundle is empty")
    if not coverage_rows:
        issues.append("coverage ledger is empty")
    if not manifest_rows:
        issues.append("frozen manifest is empty")

    issues.extend(action_issues)
    issues.extend(impl_issues)
    issues.extend(repair_issues)
    issues.extend(kill_issues)
    issues.extend(scan_blocked_terms(CODE_FILES + OUTPUT_FILES))

    verdict = {
        "ok": not issues,
        "issues": issues,
        "counts": {
            "manifest_rows": manifest_rows,
            "coverage_rows": coverage_rows,
            "action_rows": action_rows,
            "implementation_ready_rows": impl_rows,
            "repair_needed_rows": repair_rows,
            "kill_preserve_rows": kill_rows,
            "main_handoff_rows": handoff_rows,
            "issue_rows": len(issue_rows),
        },
    }
    print(json.dumps(verdict, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
