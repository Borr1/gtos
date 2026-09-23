"""Verifier for the G12 NOFILL read-only tick recovery source-control audit."""

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import build_g12_nofill_readonly_tick_recovery_export_source_control_audit_2026_05_10 as builder


ROUTE_DIR = builder.ROUTE_DIR
RESULT_NAME = f"{builder.PREFIX}_VERIFICATION_RESULT_{builder.DATE}.json"
PLACEHOLDER_RE = re.compile(r"\b(TBD|TODO|unknown|maybe|later)\b|unresolved vague", re.I)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_flag_issues(value: Any, path: str = "$") -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in builder.SAFE_FALSE_KEYS and item is not False:
                issues.append({"path": child, "value": item})
            if key == "promotion_verdict" and item != builder.PROMOTION_VERDICT:
                issues.append({"path": child, "value": item})
            issues.extend(safe_flag_issues(item, child))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            issues.extend(safe_flag_issues(item, f"{path}[{idx}]"))
    return issues


def git_changed_paths() -> list[str]:
    paths: set[str] = set()
    for args in (["diff", "--name-only", "HEAD"], ["ls-files", "--others", "--exclude-standard"]):
        result = subprocess.run(
            ["git", *args],
            cwd=builder.REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        paths.update(line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip())
    return sorted(paths)


def diff_scope() -> dict[str, Any]:
    paths = git_changed_paths()
    forbidden = [path for path in paths if any(path.startswith(prefix) for prefix in builder.FORBIDDEN_DIFF_PREFIXES)]
    outside_allowed = [
        path for path in paths if not any(path.startswith(prefix) for prefix in builder.ALLOWED_DIFF_PREFIXES)
    ]
    return {
        "changed_or_untracked_paths": paths,
        "forbidden_live_surface_paths": forbidden,
        "outside_allowed_scope_paths": outside_allowed,
        "ok": forbidden == [] and outside_allowed == [],
    }


def parse_artifacts() -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    parsed: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []
    for path in sorted(ROUTE_DIR.glob("*.json")):
        if path.name == RESULT_NAME:
            continue
        try:
            payload = load_json(path)
            parsed[path.name] = payload
        except json.JSONDecodeError as exc:
            failures.append({"check": "json_parse", "file": path.name, "error": str(exc)})
            continue
        issues = safe_flag_issues(payload, path.name)
        if issues:
            failures.append({"check": "safe_flags", "file": path.name, "issues": issues})

    for path in sorted(ROUTE_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in (
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "outcome_review_opened=false",
            "live_effect=false",
        ):
            if token not in text:
                failures.append({"check": "md_safe_tokens", "file": builder.rel(path), "missing": token})
        match = PLACEHOLDER_RE.search(text)
        if match:
            failures.append({"check": "placeholder_scan", "file": builder.rel(path), "token": match.group(0)})
    return parsed, failures


def verify_required_artifacts() -> list[dict[str, Any]]:
    missing = [name for name in builder.REQUIRED_ARTIFACTS if not (ROUTE_DIR / name).exists()]
    return [{"check": "required_artifacts_exist", "missing": missing}] if missing else []


def verify_python_syntax() -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for path in sorted(ROUTE_DIR.glob("*.py")):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append({"check": "python_syntax", "path": builder.rel(path), "error": str(exc)})
    return failures


def verify_counts(parsed: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    machine = parsed.get(f"{builder.PREFIX}_MACHINE_LEDGER_{builder.DATE}.json", {})
    count_recon = machine.get("count_reconciliation", {})
    if not count_recon.get("all_count_checks_pass"):
        failures.append({"check": "count_reconciliation", "value": count_recon.get("count_checks")})
    expected = {
        "upstream_tick_export_rows": 31,
        "g12_grouped_request_rows": 22,
        "target_recovered_grouped_rows": 20,
        "owner_action_remaining_requests": 2,
        "target_recovered_candidate_rows": 28,
        "target_remaining_candidate_rows": 3,
        "target_contamination_embargo_excluded_rows": 12,
    }
    counts = count_recon.get("counts", {})
    for key, value in expected.items():
        if counts.get(key) != value:
            failures.append({"check": "expected_count", "key": key, "expected": value, "actual": counts.get(key)})
    parse_info = machine.get("target_json_parse", {})
    if parse_info.get("target_json_artifact_count", 0) < 16 or not parse_info.get("target_json_all_parse_and_safe"):
        failures.append({"check": "target_json_parse_safe", "value": parse_info})
    return failures


def verify_source_audit(parsed: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    source = parsed.get(f"{builder.PREFIX}_SOURCE_HASH_WINDOW_COVERAGE_AUDIT_{builder.DATE}.json", {})
    if source.get("recovered_source_file_count") != 20:
        failures.append({"check": "recovered_source_file_count", "value": source.get("recovered_source_file_count")})
    if source.get("rehashed_local_source_file_count") != 20:
        failures.append({"check": "rehashed_local_source_file_count", "value": source.get("rehashed_local_source_file_count")})
    if not source.get("all_recovered_sources_pass"):
        failures.append({"check": "all_recovered_sources_pass", "value": source})
    for row in source.get("rows", []):
        if row.get("audit_status") != "PASS":
            failures.append({"check": "source_row_status", "row": row.get("owner_request_id"), "value": row})
        if row.get("actual_in_requested_window_row_count", 0) <= 0:
            failures.append({"check": "source_in_window_count", "row": row.get("owner_request_id")})
    return failures


def verify_remaining(parsed: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    remaining = parsed.get(f"{builder.PREFIX}_REMAINING_REQUEST_EXHAUSTION_AUDIT_{builder.DATE}.json", {})
    if remaining.get("exact_remaining_requests") != ["XAUUSD|2026-04-15", "XAUUSD|2026-04-16"]:
        failures.append({"check": "remaining_keys", "value": remaining.get("exact_remaining_requests")})
    if not remaining.get("recovery_ladder_exhaustion_pass"):
        failures.append({"check": "recovery_ladder_exhaustion_pass", "value": remaining})
    if not remaining.get("sierra_same_market_scid_audit", {}).get("scid_window_rows_present"):
        failures.append({"check": "sierra_scid_rows_present", "value": remaining.get("sierra_same_market_scid_audit")})
    if remaining.get("sierra_same_market_scid_audit", {}).get("admitted_as_recovered_tick_source") is not False:
        failures.append({"check": "sierra_not_admitted_boundary", "value": remaining.get("sierra_same_market_scid_audit")})
    for row in remaining.get("zero_tick_rows", []):
        for key in (
            "wrong_symbol_ruled_out",
            "wrong_utc_day_ruled_out",
            "terminal_disconnected_ruled_out",
            "unavailable_symbol_ruled_out",
            "extraction_error_ruled_out",
            "source_state_boundary_preserved",
        ):
            if row.get(key) is not True:
                failures.append({"check": f"zero_tick_{key}", "row": row.get("owner_request_id"), "value": row})
    return failures


def verify_boundaries(parsed: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    noleak = parsed.get(f"{builder.PREFIX}_NOLEAK_STAGING_AUDIT_{builder.DATE}.json", {})
    if noleak.get("audit_status") != "PASS":
        failures.append({"check": "noleak_audit_status", "value": noleak})
    if not noleak.get("raw_tick_or_csv_files_not_tracked_or_staged"):
        failures.append({"check": "raw_files_not_tracked_or_staged", "value": noleak})
    if noleak.get("forbidden_live_surface_paths") or noleak.get("outside_allowed_scope_paths"):
        failures.append({"check": "forbidden_or_outside_scope_paths", "value": noleak})
    next_route = parsed.get(f"{builder.PREFIX}_NEXT_ROUTE_RECOMMENDATION_{builder.DATE}.json", {})
    if not next_route.get("non_passive_next_route") or not next_route.get("one_line_starter"):
        failures.append({"check": "non_passive_next_route", "value": next_route})
    completion = parsed.get(f"{builder.PREFIX}_COMPLETION_AUDIT_{builder.DATE}.json", {})
    if completion.get("can_mark_goal_complete") is not True:
        failures.append({"check": "completion_can_mark_goal_complete", "value": completion})
    if completion.get("missing_incomplete_or_weak_requirements") != []:
        failures.append({"check": "completion_missing_requirements", "value": completion})
    if completion.get("terminal_decision") != builder.TERMINAL_DECISION:
        failures.append({"check": "terminal_decision", "value": completion.get("terminal_decision")})
    return failures


def verify() -> dict[str, Any]:
    parsed, failures = parse_artifacts()
    failures.extend(verify_required_artifacts())
    failures.extend(verify_python_syntax())
    failures.extend(verify_counts(parsed))
    failures.extend(verify_source_audit(parsed))
    failures.extend(verify_remaining(parsed))
    failures.extend(verify_boundaries(parsed))

    scope = diff_scope()
    if not scope["ok"]:
        failures.append({"check": "diff_scope", "value": scope})

    result = builder.base_payload(
        "verification_result",
        ok=not failures,
        can_mark_goal_complete=not failures,
        failures=failures,
        diff_scope=scope,
        parsed_json_count=len(parsed),
    )
    (ROUTE_DIR / RESULT_NAME).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    verification = verify()
    print(json.dumps(verification, indent=2, sort_keys=True))
    raise SystemExit(0 if verification["ok"] else 1)
