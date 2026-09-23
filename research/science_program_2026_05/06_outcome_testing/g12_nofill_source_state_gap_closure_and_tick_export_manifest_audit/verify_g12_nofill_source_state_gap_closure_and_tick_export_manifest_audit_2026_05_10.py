"""Verifier for the G12 NOFILL source-state gap closure audit route."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from typing import Any

import build_g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit_2026_05_10 as builder


ROUTE_DIR = builder.ROUTE_DIR
RESULT_NAME = f"{builder.PREFIX}_VERIFICATION_RESULT_{builder.DATE}.json"


def load_json(name: str) -> dict[str, Any]:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


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
    names: set[str] = set()
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
        names.update(line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip())
    return sorted(names)


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


def verify() -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    missing = [name for name in builder.REQUIRED_ARTIFACTS if not (ROUTE_DIR / name).exists()]
    if missing:
        failures.append({"check": "required_artifacts_exist", "missing": missing})
    next_prompt_path = builder.REPO_ROOT / builder.NEXT_PROMPT_PATH
    if not next_prompt_path.exists():
        failures.append({"check": "next_controlling_prompt_exists", "missing": builder.NEXT_PROMPT_PATH})

    parsed: dict[str, dict[str, Any]] = {}
    for name in builder.JSON_OUTPUTS:
        path = ROUTE_DIR / name
        if not path.exists():
            continue
        try:
            parsed[name] = load_json(name)
        except json.JSONDecodeError as exc:
            failures.append({"check": "json_parse", "file": name, "error": str(exc)})

    for name, payload in parsed.items():
        issues = safe_flag_issues(payload, name)
        if issues:
            failures.append({"check": "safe_flags", "file": name, "issues": issues})

    for md_path in sorted(list(ROUTE_DIR.glob("*.md")) + ([next_prompt_path] if next_prompt_path.exists() else [])):
        text = md_path.read_text(encoding="utf-8", errors="replace")
        for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
            if token not in text:
                failures.append({"check": "md_safe_tokens", "file": builder.rel(md_path), "missing": token})

    decision = parsed.get(f"{builder.PREFIX}_DECISION_LEDGER_{builder.DATE}.json", {})
    if decision.get("terminal_decision") != builder.TERMINAL_DECISION:
        failures.append({"check": "terminal_decision", "value": decision.get("terminal_decision")})
    if decision.get("exact_repair_blockers") != []:
        failures.append({"check": "exact_repair_blockers", "value": decision.get("exact_repair_blockers")})

    counts = parsed.get(f"{builder.PREFIX}_INDEPENDENT_COUNT_RECONCILIATION_{builder.DATE}.json", {})
    recomputed = counts.get("recomputed_counts", {})
    expected = counts.get("expected_counts", {})
    checks = {
        "admitted_source_bound_rows": recomputed.get("admitted_source_bound_rows_from_g0_row_ledger"),
        "blocked_rows": recomputed.get("blocker_rows_from_active_pursuit_rows"),
        "rejected_rows": recomputed.get("reject_rows_from_g0_reject_rows"),
        "duplicate_denominators": recomputed.get("duplicate_denominators_from_g0_duplicate_review"),
        "tick_export_rows": recomputed.get("tick_export_rows"),
        "contamination_embargo_rows": recomputed.get("contamination_embargo_rows"),
        "recovered_source_state_count": recomputed.get("recovered_source_state_count"),
        "field_closure_rows": recomputed.get("field_closure_rows"),
    }
    for key, actual in checks.items():
        if actual != expected.get(key):
            failures.append({"check": "count_reconciliation", "key": key, "expected": expected.get(key), "actual": actual})

    hash_audit = parsed.get(f"{builder.PREFIX}_TARGET_ARTIFACT_INVENTORY_SOURCE_HASH_AUDIT_{builder.DATE}.json", {})
    if hash_audit.get("audit_status") != "PASS":
        failures.append({"check": "target_artifact_hash_audit", "value": hash_audit.get("audit_status")})
    if hash_audit.get("strict_source_hash_mismatches") != []:
        failures.append({"check": "strict_source_hash_mismatches", "value": hash_audit.get("strict_source_hash_mismatches")})
    for row in hash_audit.get("target_artifact_hashes", []):
        if row.get("exists") is not True or not row.get("sha256"):
            failures.append({"check": "target_artifact_hash_row", "row": row})

    pursuit = parsed.get(f"{builder.PREFIX}_ACTIVE_PURSUIT_LADDER_AUDIT_{builder.DATE}.json", {})
    if pursuit.get("audit_status") != "PASS" or pursuit.get("row_count") != 37:
        failures.append({"check": "active_pursuit_audit", "value": pursuit.get("audit_status")})
    if any(row.get("audit_status") != "PASS" for row in pursuit.get("rows", [])):
        failures.append({"check": "active_pursuit_row_failure"})

    tick = parsed.get(f"{builder.PREFIX}_TICK_EXPORT_MANIFEST_AUDIT_{builder.DATE}.json", {})
    if tick.get("audit_status") != "PASS" or tick.get("tick_export_dependent_blocker_count") != 31:
        failures.append({"check": "tick_export_audit", "value": tick.get("audit_status")})

    contam = parsed.get(f"{builder.PREFIX}_CONTAMINATION_EMBARGO_EXCLUSION_AUDIT_{builder.DATE}.json", {})
    if contam.get("audit_status") != "PASS" or contam.get("contamination_embargo_blocker_count") != 17:
        failures.append({"check": "contamination_audit", "value": contam.get("audit_status")})
    if contam.get("g0_reject_row_count") != 9:
        failures.append({"check": "reject_count", "value": contam.get("g0_reject_row_count")})

    recovered = parsed.get(f"{builder.PREFIX}_RECOVERED_SOURCE_STATE_NEGATIVE_EVIDENCE_AUDIT_{builder.DATE}.json", {})
    if recovered.get("audit_status") != "PASS" or recovered.get("recovered_source_state_count") != 0:
        failures.append({"check": "recovered_source_state_audit", "value": recovered.get("audit_status")})

    proof = parsed.get(f"{builder.PREFIX}_NON_GENERATABLE_TRUTH_PROOF_AUDIT_{builder.DATE}.json", {})
    if proof.get("audit_status") != "PASS" or proof.get("row_count") != 37:
        failures.append({"check": "non_generatable_truth_audit", "value": proof.get("audit_status")})

    fields = parsed.get(f"{builder.PREFIX}_FORWARD_CAPTURE_55_FIELD_CLOSURE_AUDIT_{builder.DATE}.json", {})
    if fields.get("audit_status") != "PASS" or fields.get("field_count") != 55:
        failures.append({"check": "field_closure_audit", "value": fields.get("audit_status")})
    if fields.get("field_names_match_runtime_contract") is not True:
        failures.append({"check": "runtime_field_contract_match", "value": fields})

    owner = parsed.get(f"{builder.PREFIX}_OWNER_ACTION_EXACTNESS_AUDIT_{builder.DATE}.json", {})
    if owner.get("audit_status") != "PASS":
        failures.append({"check": "owner_action_exactness", "value": owner.get("audit_status")})
    grouping = parsed.get(f"{builder.PREFIX}_OWNER_EXPORT_REQUEST_GROUPING_AUDIT_{builder.DATE}.json", {})
    if grouping.get("audit_status") != "PASS":
        failures.append({"check": "owner_export_grouping", "value": grouping.get("audit_status")})
    if grouping.get("grouped_market_data_request_count") != 22:
        failures.append({"check": "owner_grouped_request_count", "value": grouping.get("grouped_market_data_request_count")})

    noleak = parsed.get(f"{builder.PREFIX}_NOLEAK_FORBIDDEN_ROUTE_LIVE_SURFACE_AUDIT_{builder.DATE}.json", {})
    if noleak.get("audit_status") != "PASS":
        failures.append({"check": "noleak_audit", "value": noleak.get("audit_status")})

    rerun = parsed.get(f"{builder.PREFIX}_TARGET_VERIFIER_TEST_RERUN_LEDGER_{builder.DATE}.json", {})
    if rerun.get("audit_status") != "PASS":
        failures.append({"check": "target_rerun_ledger", "value": rerun.get("audit_status")})
    if rerun.get("target_focused_tests", {}).get("pre_g12_artifact_creation_rerun_returncode") != 0:
        failures.append({"check": "target_tests_rerun", "value": rerun.get("target_focused_tests")})

    ranking = parsed.get(f"{builder.PREFIX}_NEXT_ROUTE_RANKING_LEDGER_{builder.DATE}.json", {})
    if ranking.get("audit_status") != "PASS":
        failures.append({"check": "next_route_ranking", "value": ranking.get("audit_status")})
    if ranking.get("ranked_next_routes", [{}])[0].get("route_id") != "NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE":
        failures.append({"check": "rank_one_next_route", "value": ranking.get("ranked_next_routes")})
    prompt_text = next_prompt_path.read_text(encoding="utf-8", errors="replace") if next_prompt_path.exists() else ""
    for token in ("31", "22", "NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE", "market-data source-control"):
        if token not in prompt_text:
            failures.append({"check": "next_controlling_prompt_content", "missing": token})

    saturation = parsed.get(f"{builder.PREFIX}_SATURATION_SELF_REDTEAM_AUDIT_{builder.DATE}.json", {})
    if saturation.get("same_evidence_class_gaps_remaining") != []:
        failures.append({"check": "saturation_remaining_gaps", "value": saturation.get("same_evidence_class_gaps_remaining")})

    completion = parsed.get(f"{builder.PREFIX}_COMPLETION_AUDIT_{builder.DATE}.json", {})
    if completion.get("can_mark_goal_complete") is not True or completion.get("completion_standard_satisfied") is not True:
        failures.append({"check": "completion_audit", "value": completion})
    if completion.get("missing_incomplete_or_weak_requirements") != []:
        failures.append({"check": "completion_missing", "value": completion.get("missing_incomplete_or_weak_requirements")})
    if len(completion.get("prompt_to_artifact_checklist", [])) < 12:
        failures.append({"check": "prompt_to_artifact_checklist", "value": len(completion.get("prompt_to_artifact_checklist", []))})

    scope = diff_scope()
    if not scope["ok"]:
        failures.append({"check": "diff_scope", "value": scope})

    syntax_failures = scan_python_syntax()
    if syntax_failures:
        failures.append({"check": "python_syntax", "failures": syntax_failures})

    result = {
        "route_id": builder.ROUTE_ID,
        "schema_version": builder.SCHEMA_VERSION,
        "ok": failures == [],
        "can_mark_goal_complete": failures == [],
        "failures": failures,
        "warnings": warnings,
        "diff_scope": scope,
        "artifact_count_checked": len(builder.REQUIRED_ARTIFACTS),
        **builder.SAFE_FALSE_PAYLOAD,
    }
    (ROUTE_DIR / RESULT_NAME).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
