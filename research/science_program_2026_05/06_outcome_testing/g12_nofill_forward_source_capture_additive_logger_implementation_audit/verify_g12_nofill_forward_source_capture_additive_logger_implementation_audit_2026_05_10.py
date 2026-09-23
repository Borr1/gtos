#!/usr/bin/env python3
"""Verify the independent G12 NOFILL source-capture implementation audit."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import build_g12_nofill_forward_source_capture_additive_logger_implementation_audit_2026_05_10 as builder

ROOT = builder.REPO_ROOT
OUT_DIR = builder.OUT_DIR
RESULT_PATH = OUT_DIR / builder.VERIFICATION_RESULT_NAME

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

ALLOWED_DIRTY_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_additive_logger_implementation_audit/",
    "research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_additive_logger_implementation/",
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
)

FORBIDDEN_LIVE_DIRTY_PREFIXES = (
    "prompts/",
    "config/",
    "src/components/",
    "src/safety/",
    "scripts/canary",
    "run_agent.py",
    "start_all.bat",
    "mt5_ea/",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git_status_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip() or line.startswith("warning:"):
            continue
        item = line[3:].replace("\\", "/")
        if " -> " in item:
            item = item.split(" -> ", 1)[1]
        paths.append(item)
    return sorted(paths)


def recursive_flag_hits(value: Any, path: str = "$") -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}"
            if key in {"validation_safe", "outcome_review_opened", "live_effect"} and item is True:
                hits.append({"path": child_path, "value": item})
            hits.extend(recursive_flag_hits(item, child_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            hits.extend(recursive_flag_hits(item, f"{path}[{index}]"))
    return hits


def verify_control_flags(name: str, payload: dict[str, Any], failures: list[dict[str, Any]]) -> None:
    if payload.get("promotion_verdict") != builder.PROMOTION_VERDICT:
        failures.append({"check": "promotion_verdict", "file": name, "value": payload.get("promotion_verdict")})
    for flag in ("validation_safe", "outcome_review_opened", "live_effect"):
        if payload.get(flag) is not False:
            failures.append({"check": "top_level_safe_flag", "file": name, "flag": flag, "value": payload.get(flag)})
    for flag in (
        "opens_result_scoring",
        "opens_validation",
        "opens_promotion",
        "opens_live_trading_behavior",
        "opens_paid_api_or_databento_route",
        "opens_registry_edit",
        "changes_live_trading_behavior",
    ):
        if payload.get(flag) is not False:
            failures.append({"check": "closed_route_flag", "file": name, "flag": flag, "value": payload.get(flag)})


def scan_placeholders() -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for path in sorted(list(OUT_DIR.glob("*.json")) + list(OUT_DIR.glob("*.md")) + list(OUT_DIR.glob("*.py"))):
        if path.name == builder.VERIFICATION_RESULT_NAME:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for fragment in BAD_FRAGMENTS:
            if fragment in text:
                hits.append({"path": builder.rel(path), "fragment": fragment})
    return hits


def scan_for_secret_markers() -> list[str]:
    hits: list[str] = []
    for path in sorted(list(OUT_DIR.glob("*.json")) + list(OUT_DIR.glob("*.md"))):
        if path.name == builder.VERIFICATION_RESULT_NAME:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "SECRET_G12_RAW_VALUE_" in text or "SECRET_G12_NESTED_RAW_VALUE_" in text:
            hits.append(builder.rel(path))
    return hits


def verify() -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    missing = [name for name in builder.REQUIRED_ARTIFACTS if not (OUT_DIR / name).exists()]
    if missing:
        failures.append({"check": "required_artifacts_exist", "missing": missing})

    parsed: dict[str, Any] = {}
    json_parse_errors: list[dict[str, str]] = []
    for name in builder.JSON_ARTIFACTS:
        path = OUT_DIR / name
        if not path.exists():
            continue
        try:
            parsed[name] = load_json(path)
        except json.JSONDecodeError as exc:
            json_parse_errors.append({"file": name, "error": str(exc)})
    if json_parse_errors:
        failures.append({"check": "json_parse", "errors": json_parse_errors})

    md_missing_tokens: list[dict[str, str]] = []
    for name in builder.MD_ARTIFACTS:
        path = OUT_DIR / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
            if token not in text:
                md_missing_tokens.append({"file": name, "missing": token})
        for literal in ("validation_safe=true", "outcome_review_opened=true", "live_effect=true"):
            if literal in text:
                failures.append({"check": "md_forbidden_true_literal", "file": name, "literal": literal})
    if md_missing_tokens:
        failures.append({"check": "md_control_tokens", "missing": md_missing_tokens})

    for name, payload in parsed.items():
        if isinstance(payload, dict):
            verify_control_flags(name, payload, failures)
            nested_true_flags = recursive_flag_hits(payload)
            if nested_true_flags:
                failures.append({"check": "nested_safe_flag_true", "file": name, "hits": nested_true_flags})

    decision = parsed.get(builder.JSON_ARTIFACTS[1], {})
    if decision.get("terminal_decision") != builder.ACCEPT_TERMINAL_DECISION:
        failures.append({"check": "terminal_decision", "value": decision.get("terminal_decision")})
    if decision.get("exact_repair_blocker_count") != 0:
        failures.append({"check": "decision_repair_blockers", "value": decision.get("exact_repair_blockers")})

    runtime = parsed.get(builder.JSON_ARTIFACTS[2], {})
    if runtime.get("runtime_field_count") != 55 or runtime.get("runtime_unique_field_count") != 55:
        failures.append({"check": "runtime_55_field_count", "value": runtime})
    if runtime.get("runtime_validator_result", {}).get("ok") is not True:
        failures.append({"check": "runtime_validator", "value": runtime.get("runtime_validator_result")})
    if runtime.get("status_counts_recomputed_from_coverage") != builder.EXPECTED_STATUS_COUNTS:
        failures.append({"check": "runtime_status_counts", "value": runtime.get("status_counts_recomputed_from_coverage")})

    future = parsed.get(builder.JSON_ARTIFACTS[3], {})
    if future.get("runtime_future_logger_field_count") != 20 or future.get("audit_passed") is not True:
        failures.append({"check": "future_field_audit", "value": future})
    for row in future.get("per_field", []):
        if row.get("emits_or_fail_closes") is not True:
            failures.append({"check": "future_field_row", "row": row})

    failopen = parsed.get(builder.JSON_ARTIFACTS[4], {})
    if failopen.get("forced_failure_exception_escaped") is not False:
        failures.append({"check": "failopen_exception", "value": failopen})
    if failopen.get("nofill_writer_call_consumed_count") != 0:
        failures.append({"check": "writer_return_consumed", "value": failopen})
    if failopen.get("audit_passed") is not True:
        failures.append({"check": "failopen_audit", "value": failopen})

    noleak = parsed.get(builder.JSON_ARTIFACTS[5], {})
    if noleak.get("secret_marker_leaks") != [] or noleak.get("forbidden_output_keys") != [] or noleak.get("raw_value_hash_hits") != []:
        failures.append({"check": "noleak_probe", "value": noleak})
    if noleak.get("audit_passed") is not True:
        failures.append({"check": "noleak_audit", "value": noleak})

    diff = parsed.get(builder.JSON_ARTIFACTS[6], {})
    if diff.get("forbidden_live_surface_paths") != [] or diff.get("unexpected_code_or_test_paths") != []:
        failures.append({"check": "diff_scope", "value": diff})
    if diff.get("runtime_nofill_writer_call_lines") is None or len(diff.get("runtime_nofill_writer_call_lines", [])) != 1:
        failures.append({"check": "runtime_writer_call_count", "value": diff.get("runtime_nofill_writer_call_lines")})

    rerun = parsed.get(builder.JSON_ARTIFACTS[7], {})
    if rerun.get("implementation_verifier_rerun_passed") is not True:
        failures.append({"check": "implementation_verifier_rerun", "value": rerun})
    if rerun.get("implementation_focused_tests_passed") is not True:
        failures.append({"check": "implementation_tests_rerun", "value": rerun})
    if rerun.get("relevant_existing_forward_capture_tests_passed") is not True:
        failures.append({"check": "forward_capture_tests_rerun", "value": rerun})
    if rerun.get("syntax_check_passed") is not True:
        failures.append({"check": "syntax_check", "value": rerun})

    hash_audit = parsed.get(builder.JSON_ARTIFACTS[8], {})
    if hash_audit.get("parser_hash_matches_forward_capture_file") is not True:
        failures.append({"check": "parser_hash", "value": hash_audit})
    drifted = [
        row for row in hash_audit.get("manifest_entries_checked", []) if row.get("matches_manifest") is not True
    ]
    if drifted:
        failures.append({"check": "source_hash_manifest_drift", "drifted": drifted})
    if hash_audit.get("rollback_disable_path_count", 0) < 3:
        failures.append({"check": "rollback_disable_paths", "value": hash_audit.get("rollback_disable_paths")})

    saturation = parsed.get(builder.JSON_ARTIFACTS[9], {})
    if saturation.get("question_count") != 8 or saturation.get("same_evidence_class_gaps_exposed") != []:
        failures.append({"check": "saturation", "value": saturation})
    for item in saturation.get("questions", []):
        if item.get("status") != "CLEARED":
            failures.append({"check": "saturation_item", "item": item})

    instruction = parsed.get(builder.JSON_ARTIFACTS[10], {})
    if instruction.get("all_requirements_covered") is not True:
        failures.append({"check": "instruction_coverage", "value": instruction})
    for row in instruction.get("coverage_rows", []):
        if row.get("status") != "PASS":
            failures.append({"check": "instruction_row", "row": row})

    repair = parsed.get(builder.JSON_ARTIFACTS[11], {})
    if repair.get("exact_repair_blocker_count") != 0 or repair.get("remaining_blockers") != []:
        failures.append({"check": "repair_blocker_ledger", "value": repair})

    completion = parsed.get(builder.JSON_ARTIFACTS[12], {})
    if completion.get("completion_standard_satisfied") is not True:
        failures.append({"check": "completion_standard", "value": completion})
    if completion.get("missing_incomplete_or_weak_requirements") != []:
        failures.append({"check": "completion_missing_or_weak", "value": completion.get("missing_incomplete_or_weak_requirements")})
    for row in completion.get("prompt_to_artifact_checklist", []):
        if row.get("status") != "PASS":
            failures.append({"check": "completion_checklist_row", "row": row})

    placeholder_hits = scan_placeholders()
    if placeholder_hits:
        failures.append({"check": "placeholder_scan", "hits": placeholder_hits})
    secret_artifact_hits = scan_for_secret_markers()
    if secret_artifact_hits:
        failures.append({"check": "secret_marker_artifact_scan", "hits": secret_artifact_hits})

    runtime_recheck, runtime_blockers = builder.runtime_55_field_contract_audit()
    future_recheck, future_blockers = builder.future_logger_field_audit()
    noleak_recheck, noleak_blockers = builder.forbidden_redaction_no_leak_audit()
    if runtime_blockers or runtime_recheck.get("runtime_field_count") != 55:
        failures.append({"check": "runtime_recompute_in_verifier", "blockers": runtime_blockers})
    if future_blockers or future_recheck.get("runtime_future_logger_field_count") != 20:
        failures.append({"check": "future_recompute_in_verifier", "blockers": future_blockers})
    if noleak_blockers:
        failures.append({"check": "noleak_recompute_in_verifier", "blockers": noleak_blockers})

    dirty_paths = git_status_paths()
    forbidden_live_dirty = [path for path in dirty_paths if path.startswith(FORBIDDEN_LIVE_DIRTY_PREFIXES)]
    outside_allowed_dirty = [
        path
        for path in dirty_paths
        if not any(path == prefix or path.startswith(prefix) for prefix in ALLOWED_DIRTY_PREFIXES)
    ]
    if forbidden_live_dirty:
        failures.append({"check": "forbidden_live_surface_dirty", "paths": forbidden_live_dirty})
    if outside_allowed_dirty:
        warnings.append({"check": "outside_allowed_dirty_informational", "paths": outside_allowed_dirty})

    result = {
        "schema_version": f"{builder.SCHEMA_VERSION}_verification_result",
        "route_id": builder.ROUTE_ID,
        **builder.CONTROL_FLAGS,
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "terminal_decision": decision.get("terminal_decision"),
        "exact_repair_blocker_count": repair.get("exact_repair_blocker_count"),
        "runtime_field_count": runtime.get("runtime_field_count"),
        "runtime_future_logger_field_count": future.get("runtime_future_logger_field_count"),
        "json_files_parsed": sorted(parsed),
        "placeholder_scan_passed": not placeholder_hits,
        "secret_marker_scan_passed": not secret_artifact_hits,
        "failures": failures,
        "warnings": warnings,
        "dirty_paths_reviewed": dirty_paths,
        "validation_or_promotion_opened": False,
        "live_behavior_changed": False,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
