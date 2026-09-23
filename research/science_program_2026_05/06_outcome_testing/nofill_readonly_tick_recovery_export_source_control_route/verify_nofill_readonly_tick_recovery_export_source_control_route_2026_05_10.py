"""Verifier for the NOFILL read-only tick recovery/export route."""

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import build_nofill_readonly_tick_recovery_export_source_control_route_2026_05_10 as builder


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


def scan_python_syntax() -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for path in sorted(ROUTE_DIR.glob("*.py")):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append({"path": builder.rel(path), "error": str(exc)})
    return failures


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
    for path in sorted(ROUTE_DIR.glob("*.md")) + [builder.repo_path(builder.NEXT_G12_PROMPT_PATH)]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
            if token not in text:
                failures.append({"check": "md_safe_tokens", "file": builder.rel(path), "missing": token})
        match = PLACEHOLDER_RE.search(text)
        if match:
            failures.append({"check": "placeholder_scan", "file": builder.rel(path), "token": match.group(0)})
    return parsed, failures


def verify_required_artifacts() -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    missing = [name for name in builder.REQUIRED_ARTIFACTS if not (ROUTE_DIR / name).exists()]
    if missing:
        failures.append({"check": "required_artifacts_exist", "missing": missing})
    if not builder.repo_path(builder.NEXT_G12_PROMPT_PATH).exists():
        failures.append({"check": "next_g12_prompt_exists", "missing": builder.NEXT_G12_PROMPT_PATH})
    return failures


def verify_counts(parsed: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    completion = parsed.get(f"{builder.PREFIX}_COMPLETION_AUDIT_{builder.DATE}.json", {})
    expected = {
        "tick_export_dependent_blocker_count": 31,
        "grouped_request_count": 22,
        "recovered_grouped_request_count": 20,
        "remaining_owner_export_request_count": 2,
        "recovered_candidate_row_count": 28,
        "remaining_candidate_row_count": 3,
        "contamination_embargo_excluded_row_count": 12,
    }
    for key, value in expected.items():
        if completion.get(key) != value:
            failures.append({"check": "completion_count", "key": key, "expected": value, "actual": completion.get(key)})
    if completion.get("can_mark_goal_complete") is not True:
        failures.append({"check": "completion_can_mark_goal_complete", "value": completion.get("can_mark_goal_complete")})
    if completion.get("missing_incomplete_or_weak_requirements") != []:
        failures.append(
            {
                "check": "completion_missing_requirements",
                "value": completion.get("missing_incomplete_or_weak_requirements"),
            }
        )
    recovery = parsed.get(f"{builder.PREFIX}_RECOVERY_LADDER_LEDGER_{builder.DATE}.json", {})
    if len(recovery.get("candidate_rows", [])) != 31:
        failures.append({"check": "candidate_recovery_row_count", "value": len(recovery.get("candidate_rows", []))})
    if len(recovery.get("grouped_rows", [])) != 22:
        failures.append({"check": "grouped_recovery_row_count", "value": len(recovery.get("grouped_rows", []))})
    owner = parsed.get(f"{builder.PREFIX}_OWNER_ACTION_MANIFEST_{builder.DATE}.json", {})
    remaining = owner.get("market_data_export_requests", [])
    remaining_keys = {(row.get("symbol"), row.get("source_date")) for row in remaining}
    if remaining_keys != {("XAUUSD", "2026-04-15"), ("XAUUSD", "2026-04-16")}:
        failures.append({"check": "remaining_owner_export_exact_windows", "value": sorted(remaining_keys)})
    return failures


def verify_source_hashes(parsed: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    manifest = parsed.get(f"{builder.PREFIX}_SOURCE_HASH_MANIFEST_{builder.DATE}.json", {})
    rows = manifest.get("rows", [])
    if len(rows) != 20:
        failures.append({"check": "source_hash_row_count", "expected": 20, "actual": len(rows)})
    for row in rows:
        path = builder.repo_path(row["source_path"])
        if not path.exists():
            failures.append({"check": "source_file_exists", "path": row["source_path"]})
            continue
        actual_sha = builder.sha256_file(path)
        if actual_sha != row.get("source_sha256"):
            failures.append(
                {
                    "check": "source_file_sha256",
                    "path": row["source_path"],
                    "expected": row.get("source_sha256"),
                    "actual": actual_sha,
                }
            )
        fields = row.get("field_availability", {})
        missing = [field for field in builder.REQUIRED_TICK_FIELDS if not fields.get(field)]
        if missing:
            failures.append({"check": "source_field_availability", "path": row["source_path"], "missing": missing})
        if row.get("source_file_sha256_field_status") != "recorded_in_source_hash_manifest":
            failures.append({"check": "source_file_sha256_field_status", "row": row.get("owner_request_id")})
        candidates = row.get("window_coverage", {}).get("candidate_times_inside_source_span", [])
        if not candidates or not all(item.get("inside_source_span") for item in candidates):
            failures.append({"check": "candidate_times_inside_source_span", "row": row.get("owner_request_id")})
    return failures


def verify_boundaries(parsed: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    noleak = parsed.get(f"{builder.PREFIX}_NOLEAK_AUDIT_{builder.DATE}.json", {})
    if noleak.get("audit_status") != "PASS":
        failures.append({"check": "noleak_audit_status", "value": noleak})
    if noleak.get("account_order_history_deal_position_api_used_any") is not False:
        failures.append({"check": "forbidden_api_use", "value": noleak.get("account_order_history_deal_position_api_used_any")})
    staging = parsed.get(f"{builder.PREFIX}_LARGE_FILE_STAGING_POLICY_AUDIT_{builder.DATE}.json", {})
    if staging.get("policy_status") != "PASS":
        failures.append({"check": "staging_policy_status", "value": staging.get("policy_status")})
    if staging.get("raw_market_data_files_changed_or_untracked_visible_to_git") != []:
        failures.append(
            {
                "check": "raw_market_data_visible_to_git",
                "value": staging.get("raw_market_data_files_changed_or_untracked_visible_to_git"),
            }
        )
    if staging.get("raw_market_data_files_gitignored") is not True or staging.get("raw_market_data_files_not_tracked") is not True:
        failures.append({"check": "raw_market_data_ignore_track_status", "value": staging})
    recovery = parsed.get(f"{builder.PREFIX}_RECOVERY_LADDER_LEDGER_{builder.DATE}.json", {})
    contamination = [row for row in recovery.get("candidate_rows", []) if row.get("contamination_or_embargo_blocked")]
    if len(contamination) != 12:
        failures.append({"check": "contamination_count", "value": len(contamination)})
    if any("CONTAMINATION_EXCLUDED" not in row.get("terminal_status", "") for row in contamination):
        failures.append({"check": "contamination_terminal_status", "rows": contamination})
    if any("ticks_do_not_admit_candidate" not in row.get("source_state_boundary", "") for row in recovery.get("candidate_rows", [])):
        failures.append({"check": "source_state_boundary_missing"})
    return failures


def verify() -> dict[str, Any]:
    parsed, failures = parse_artifacts()
    failures.extend(verify_required_artifacts())
    failures.extend(verify_counts(parsed))
    failures.extend(verify_source_hashes(parsed))
    failures.extend(verify_boundaries(parsed))

    syntax_failures = scan_python_syntax()
    if syntax_failures:
        failures.append({"check": "python_syntax", "failures": syntax_failures})

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
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
