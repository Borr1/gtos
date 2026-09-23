#!/usr/bin/env python3
"""Verify the NOFILL forward source-capture implementation design package."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from build_nofill_forward_source_capture_implementation_design_plan_2026_05_10 import (
    DATE,
    PROMOTION_VERDICT,
    ROOT,
    ROUTE_DIR,
    ROUTE_ID,
    TERMINAL_STATUSES,
)

SCHEMA_VERSION = "nofill_forward_source_capture_implementation_design_plan_verifier_v1"

BAD_FRAGMENTS = tuple(
    item.lower()
    for item in (
        "tb" + "d",
        "to" + "do",
        "un" + "known",
        "may" + "be",
        "la" + "ter",
        "not" + " " + "yet" + " " + "decided",
    )
)

REQUIRED_JSON_ARTIFACTS = (
    f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_CONTEXT_ANCHOR_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CONTRACT_IMPLEMENTATION_MAP_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_EXISTING_SOURCE_INVENTORY_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_EMISSION_DESIGN_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_FIELD_REDACTION_POLICY_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_FAIL_CLOSED_STATUS_VOCABULARY_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_PARSER_PROJECTION_SCHEMA_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_FIXTURE_TEST_MATRIX_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_HASH_MANIFEST_REQUIREMENTS_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_OPERATIONAL_RISK_ROLLBACK_LEDGER_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_G12_ACCEPTANCE_CHECKLIST_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DEPENDENCY_GRAPH_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_OWNER_APPROVAL_GATE_LEDGER_{DATE}.json",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_COMPLETION_AUDIT_{DATE}.json",
)

REQUIRED_MD_ARTIFACTS = (
    f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_CONTEXT_ANCHOR_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_CONTRACT_IMPLEMENTATION_MAP_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_EXISTING_SOURCE_INVENTORY_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_EMISSION_DESIGN_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_FIELD_REDACTION_POLICY_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_FAIL_CLOSED_STATUS_VOCABULARY_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_PARSER_PROJECTION_SCHEMA_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_FIXTURE_TEST_MATRIX_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_HASH_MANIFEST_REQUIREMENTS_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_OPERATIONAL_RISK_ROLLBACK_LEDGER_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_G12_ACCEPTANCE_CHECKLIST_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DEPENDENCY_GRAPH_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_OWNER_APPROVAL_GATE_LEDGER_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_NEXT_PROMPT_PACK_{DATE}.md",
    f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_COMPLETION_AUDIT_{DATE}.md",
)

ALLOWED_DIRTY_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_implementation_design_plan/",
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
)

REQUIRED_FUTURE_ROW_COLUMNS = (
    "target_source_surface",
    "target_schema_field",
    "redaction_rule",
    "fail_closed_missing_status",
    "test_fixture",
    "rollback_rule",
    "g12_acceptance_check",
)


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_json_artifacts() -> tuple[list[str], dict[str, str]]:
    parsed: list[str] = []
    errors: dict[str, str] = {}
    for path in sorted(ROUTE_DIR.glob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
            parsed.append(path.name)
        except json.JSONDecodeError as exc:
            errors[path.name] = str(exc)
    return parsed, errors


def scan_placeholders() -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for path in sorted(list(ROUTE_DIR.glob("*.json")) + list(ROUTE_DIR.glob("*.md"))):
        if path.name.endswith("_VERIFICATION_RESULT_2026-05-10.json"):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for fragment in BAD_FRAGMENTS:
            if fragment in text:
                hits.append({"path": path.name, "fragment": fragment})
    return hits


def git_dirty_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        item = line[3:].replace("\\", "/")
        if " -> " in item:
            item = item.split(" -> ", 1)[1]
        paths.append(item)
    return paths


def verify_field_map(field_map: dict[str, Any], failures: dict[str, Any]) -> dict[str, Any]:
    fields = field_map.get("fields") or []
    names = [row.get("field_name") for row in fields]
    statuses = [row.get("terminal_implementation_design_status") for row in fields]
    counts = Counter(statuses)

    if field_map.get("field_count") != 55 or len(fields) != 55:
        failures["field_count"] = {"declared": field_map.get("field_count"), "actual": len(fields)}
    if len(set(names)) != 55:
        failures["field_names_unique"] = {"unique": len(set(names)), "actual": len(names)}
    bad_statuses = sorted(set(statuses) - TERMINAL_STATUSES)
    if bad_statuses:
        failures["terminal_status_values"] = bad_statuses
    if sum(counts.values()) != 55:
        failures["terminal_status_counts_sum"] = dict(counts)

    future_rows = [row for row in fields if row.get("terminal_implementation_design_status") == "FUTURE_LOGGER_FIELD_REQUIRED"]
    missing_future = []
    for row in future_rows:
        missing_cols = [col for col in REQUIRED_FUTURE_ROW_COLUMNS if not row.get(col)]
        if missing_cols:
            missing_future.append({"field_name": row.get("field_name"), "missing": missing_cols})
    if missing_future:
        failures["future_logger_row_requirements"] = missing_future

    blocked_rows = [
        row
        for row in fields
        if row.get("terminal_implementation_design_status")
        == "BLOCKED_WITH_EXACT_OWNER_APPROVAL_OR_SOURCE_REQUIREMENT"
    ]
    missing_blocker = [
        row.get("field_name")
        for row in blocked_rows
        if not row.get("owner_or_source_requirement") or row.get("owner_or_source_requirement") == "No owner action for this design step"
    ]
    if missing_blocker:
        failures["blocked_row_requirements"] = missing_blocker

    return {
        "field_count": len(fields),
        "unique_field_count": len(set(names)),
        "terminal_status_counts": dict(sorted(counts.items())),
        "future_logger_field_count": len(future_rows),
        "blocked_field_count": len(blocked_rows),
    }


def verify_flags(payloads: list[dict[str, Any]], failures: dict[str, Any]) -> None:
    bad: list[dict[str, Any]] = []
    for payload in payloads:
        name = payload.get("_artifact_name")
        if payload.get("promotion_verdict") != PROMOTION_VERDICT:
            bad.append({"artifact": name, "field": "promotion_verdict", "value": payload.get("promotion_verdict")})
        for flag in ("validation_safe", "outcome_review_opened", "live_effect"):
            if payload.get(flag) is not False:
                bad.append({"artifact": name, "field": flag, "value": payload.get(flag)})
        for flag in ("opens_result_scoring", "opens_live_wiring"):
            if payload.get(flag) is True:
                bad.append({"artifact": name, "field": flag, "value": payload.get(flag)})
    if bad:
        failures["closed_route_flags"] = bad


def build_report() -> dict[str, Any]:
    failures: dict[str, Any] = {}
    missing_json = [name for name in REQUIRED_JSON_ARTIFACTS if not (ROUTE_DIR / name).exists()]
    missing_md = [name for name in REQUIRED_MD_ARTIFACTS if not (ROUTE_DIR / name).exists()]
    if missing_json:
        failures["missing_json_artifacts"] = missing_json
    if missing_md:
        failures["missing_md_artifacts"] = missing_md

    parsed_json, json_errors = parse_json_artifacts()
    if json_errors:
        failures["json_parse_errors"] = json_errors

    payloads: list[dict[str, Any]] = []
    for name in REQUIRED_JSON_ARTIFACTS:
        path = ROUTE_DIR / name
        if path.exists():
            payload = read_json(path)
            payload["_artifact_name"] = name
            payloads.append(payload)
    verify_flags(payloads, failures)

    field_summary: dict[str, Any] = {}
    field_path = ROUTE_DIR / f"NOFILL_FORWARD_SOURCE_CONTRACT_IMPLEMENTATION_MAP_{DATE}.json"
    if field_path.exists():
        field_summary = verify_field_map(read_json(field_path), failures)

    placeholder_hits = scan_placeholders()
    if placeholder_hits:
        failures["placeholder_hits"] = placeholder_hits

    dirty = git_dirty_paths()
    forbidden_dirty = [
        path for path in dirty if not any(path == prefix or path.startswith(prefix) for prefix in ALLOWED_DIRTY_PREFIXES)
    ]
    if forbidden_dirty:
        failures["forbidden_dirty_paths"] = forbidden_dirty

    report = {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_result_scoring": False,
        "opens_live_wiring": False,
        "opens_registry_edit": False,
        "opens_paid_api_or_databento_route": False,
        "changes_live_trading_behavior": False,
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "failures": failures,
        "json_files_parsed": parsed_json,
        "field_summary": field_summary,
        "dirty_paths_reviewed": dirty,
        "required_artifact_count": len(REQUIRED_JSON_ARTIFACTS) + len(REQUIRED_MD_ARTIFACTS),
        "placeholder_scan_passed": not placeholder_hits,
        "terminal_verdict": (
            "ACCEPT_AS_SOURCE_CONTROL_IMPLEMENTATION_DESIGN_ONLY"
            if not failures
            else "REJECT_WITH_EXACT_FAILURES"
        ),
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-result", action="store_true")
    args = parser.parse_args(argv)
    report = build_report()
    if args.write_result:
        out = ROUTE_DIR / f"NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_VERIFICATION_RESULT_{DATE}.json"
        out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
