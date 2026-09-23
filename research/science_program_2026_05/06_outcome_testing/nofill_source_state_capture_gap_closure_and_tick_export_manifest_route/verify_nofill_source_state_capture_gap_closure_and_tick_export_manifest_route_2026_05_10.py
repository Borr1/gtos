"""Verifier for the NOFILL source-state gap closure route."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import build_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10 as builder


sys.path.insert(0, str(builder.REPO_ROOT))
from src.research_infra import forward_capture as fc  # noqa: E402


ROUTE_DIR = builder.ROUTE_DIR
RESULT_NAME = f"{builder.PREFIX}_VERIFICATION_RESULT_{builder.DATE}.json"
FORBIDDEN_TRUE_TOKENS = ("validation_safe=true", "outcome_review_opened=true", "live_effect=true")
PLACEHOLDER_FRAGMENTS = ("tbd", "todo", "maybe")


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


def scan_text_artifacts() -> dict[str, Any]:
    placeholder_hits: list[dict[str, str]] = []
    true_flag_hits: list[dict[str, str]] = []
    for path in sorted(list(ROUTE_DIR.glob("*.json")) + list(ROUTE_DIR.glob("*.md"))):
        if path.name == RESULT_NAME:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        lower = text.lower()
        for token in FORBIDDEN_TRUE_TOKENS:
            if token in lower:
                true_flag_hits.append({"path": path.name, "token": token})
        for fragment in PLACEHOLDER_FRAGMENTS:
            if fragment in lower:
                placeholder_hits.append({"path": path.name, "fragment": fragment})
    return {
        "placeholder_hits": placeholder_hits,
        "true_flag_hits": true_flag_hits,
        "ok": placeholder_hits == [] and true_flag_hits == [],
    }


def verify() -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    missing = [name for name in builder.REQUIRED_ARTIFACTS if not (ROUTE_DIR / name).exists()]
    if missing:
        failures.append({"check": "required_artifacts_exist", "missing": missing})

    parsed: dict[str, dict[str, Any]] = {}
    for name in builder.JSON_ARTIFACTS:
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

    for md_path in sorted(ROUTE_DIR.glob("*.md")):
        text = md_path.read_text(encoding="utf-8", errors="replace")
        for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
            if token not in text:
                failures.append({"check": "md_safe_tokens", "file": md_path.name, "missing": token})

    context = parsed.get(f"{builder.PREFIX}_CONTEXT_ANCHOR_{builder.DATE}.json", {})
    if not context.get("catalog_builder_rerun", {}).get("rerun_ok"):
        failures.append({"check": "catalog_builder_rerun", "value": context.get("catalog_builder_rerun")})
    if context.get("prompt_path") != builder.PROMPT_PATH:
        failures.append({"check": "prompt_path", "value": context.get("prompt_path")})

    decision = parsed.get(f"{builder.PREFIX}_DECISION_LEDGER_{builder.DATE}.json", {})
    if decision.get("terminal_decision") != builder.TERMINAL_DECISION:
        failures.append({"check": "terminal_decision", "value": decision.get("terminal_decision")})
    counts = decision.get("accepted_upstream_counts", {})
    expected_counts = {
        "admitted_source_bound_rows": 2,
        "blocked_rows": 37,
        "rejected_rows": 9,
        "duplicate_denominators": builder.EXPECTED_DUPLICATE_DENOMINATORS,
        "repaired_packet_hash": builder.EXPECTED_PACKET_SHA,
    }
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            failures.append({"check": "accepted_counts", "key": key, "expected": expected, "actual": counts.get(key)})

    g0 = parsed.get(f"{builder.PREFIX}_G0_BLOCKER_INGESTION_RECONCILIATION_{builder.DATE}.json", {})
    if g0.get("reconciled_counts", {}).get("blocker_rows") != 37:
        failures.append({"check": "g0_blocker_ingestion", "value": g0.get("reconciled_counts")})

    catalog = parsed.get(f"{builder.PREFIX}_ACTIVE_CATALOG_REFRESH_SEARCH_LEDGER_{builder.DATE}.json", {})
    active_counts = catalog.get("active_catalog_counts", {})
    if active_counts.get("catalog_row_count") != 1200:
        failures.append({"check": "catalog_row_count", "value": active_counts})
    if active_counts.get("hash_manifest_hashed_file_count") != 1076:
        failures.append({"check": "catalog_hash_count", "value": active_counts})
    if active_counts.get("hash_manifest_large_file_deferral_count") != 124:
        failures.append({"check": "catalog_deferral_count", "value": active_counts})

    taxonomy = parsed.get(f"{builder.PREFIX}_SOURCE_STATE_GAP_TAXONOMY_LEDGER_{builder.DATE}.json", {})
    if taxonomy.get("row_count") != 37 or len(taxonomy.get("rows", [])) != 37:
        failures.append({"check": "taxonomy_row_count", "value": taxonomy.get("row_count")})
    if taxonomy.get("non_generatable_historical_gtos_source_state_count") != 37:
        failures.append({"check": "source_state_count", "value": taxonomy.get("non_generatable_historical_gtos_source_state_count")})
    if taxonomy.get("tick_export_dependent_count") != 31:
        failures.append({"check": "taxonomy_tick_count", "value": taxonomy.get("tick_export_dependent_count")})
    if taxonomy.get("contamination_embargo_count") != 17:
        failures.append({"check": "taxonomy_contamination_count", "value": taxonomy.get("contamination_embargo_count")})

    pursuit = parsed.get(f"{builder.PREFIX}_ACTIVE_PURSUIT_LADDER_LEDGER_{builder.DATE}.json", {})
    pursuit_rows = pursuit.get("rows", [])
    if pursuit.get("row_count") != 37 or len(pursuit_rows) != 37:
        failures.append({"check": "pursuit_row_count", "value": pursuit.get("row_count")})
    if not pursuit.get("all_terminal_statuses_allowed"):
        failures.append({"check": "terminal_status_allowed", "value": pursuit.get("terminal_status_counts")})
    statuses = {row.get("terminal_status") for row in pursuit_rows}
    if not statuses <= builder.ALLOWED_TERMINAL_STATUSES:
        failures.append({"check": "terminal_status_vocab", "value": sorted(statuses)})
    for row in pursuit_rows:
        if len(row.get("active_pursuit_ladder", [])) != 6:
            failures.append({"check": "pursuit_ladder_steps", "candidate_id": row.get("candidate_id")})
        if not row.get("exact_next_action"):
            failures.append({"check": "exact_next_action", "candidate_id": row.get("candidate_id")})

    recovered = parsed.get(f"{builder.PREFIX}_RECOVERED_SOURCE_STATE_MANIFEST_{builder.DATE}.json", {})
    if recovered.get("recovered_source_state_count") != 0 or recovered.get("negative_evidence_row_count") != 37:
        failures.append({"check": "recovered_manifest", "value": recovered})

    forward = parsed.get(f"{builder.PREFIX}_FORWARD_CAPTURE_REQUIREMENT_MATRIX_{builder.DATE}.json", {})
    if forward.get("accepted_contract_field_count") != 55 or len(forward.get("fields", [])) != 55:
        failures.append({"check": "forward_field_count", "value": forward.get("accepted_contract_field_count")})

    closure = parsed.get(f"{builder.PREFIX}_55_FIELD_CLOSURE_LEDGER_{builder.DATE}.json", {})
    if closure.get("field_count") != 55 or closure.get("all_fields_closed") is not True:
        failures.append({"check": "field_55_closure", "value": closure.get("field_count")})
    runtime_fields = list(fc.NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS)
    closure_names = [row["field_name"] for row in closure.get("rows", [])]
    if sorted(runtime_fields) != sorted(closure_names):
        failures.append({"check": "runtime_field_names_match", "missing": sorted(set(runtime_fields) - set(closure_names))})

    tick = parsed.get(f"{builder.PREFIX}_TICK_EXPORT_EXTRACTION_MANIFEST_{builder.DATE}.json", {})
    if tick.get("tick_export_dependent_blocker_count") != 31 or len(tick.get("rows", [])) != 31:
        failures.append({"check": "tick_manifest_count", "value": tick.get("tick_export_dependent_blocker_count")})
    for row in tick.get("rows", []):
        if "account/order/history/deal/position" not in " ".join(row.get("no_leak_constraints", [])):
            failures.append({"check": "tick_no_leak_constraints", "candidate_id": row.get("candidate_id")})

    contam = parsed.get(f"{builder.PREFIX}_CONTAMINATION_EMBARGO_HANDLING_LEDGER_{builder.DATE}.json", {})
    if contam.get("contamination_embargo_blocker_count") != 17 or len(contam.get("rows", [])) != 17:
        failures.append({"check": "contamination_count", "value": contam.get("contamination_embargo_blocker_count")})
    for row in contam.get("rows", []):
        if row.get("handling_status") != "CONTAMINATION_EMBARGO_EXCLUDED":
            failures.append({"check": "contamination_status", "candidate_id": row.get("candidate_id")})

    owner = parsed.get(f"{builder.PREFIX}_OWNER_ACTION_MANIFEST_{builder.DATE}.json", {})
    if owner.get("owner_tick_export_request_count", 0) <= 0:
        failures.append({"check": "owner_tick_requests", "value": owner.get("owner_tick_export_request_count")})
    if owner.get("forward_capture_owner_approval_required") is not True:
        failures.append({"check": "owner_forward_capture_request", "value": owner})

    proof = parsed.get(f"{builder.PREFIX}_NON_GENERATABLE_TRUTH_PROOF_LEDGER_{builder.DATE}.json", {})
    if proof.get("row_count") != 37:
        failures.append({"check": "non_generatable_row_count", "value": proof.get("row_count")})
    if proof.get("all_rows_price_tick_bar_backfill_possible") is not False:
        failures.append({"check": "non_generatable_backfill_flag", "value": proof.get("all_rows_price_tick_bar_backfill_possible")})

    contract = parsed.get(f"{builder.PREFIX}_CONTRACT_UPDATE_PROPOSAL_{builder.DATE}.json", {})
    if contract.get("schema_change_required_now") is not False:
        failures.append({"check": "contract_no_schema_change", "value": contract})

    noleak = parsed.get(f"{builder.PREFIX}_NOLEAK_FORBIDDEN_ROUTE_AUDIT_{builder.DATE}.json", {})
    if noleak.get("forbidden_evidence_surfaces_opened") != []:
        failures.append({"check": "forbidden_evidence_surfaces", "value": noleak})
    scope = diff_scope()
    if not scope["ok"]:
        failures.append({"check": "diff_scope", "value": scope})

    parallel = parsed.get(f"{builder.PREFIX}_PARALLELIZATION_AFTER_BOTTLENECK_LEDGER_{builder.DATE}.json", {})
    if len(parallel.get("parallel_routes_after_this_route", [])) < 3:
        failures.append({"check": "parallel_routes", "value": parallel})

    next_g12_path = ROUTE_DIR / f"{builder.PREFIX}_NEXT_G12_AUDIT_PROMPT_PACK_{builder.DATE}.md"
    next_g12 = next_g12_path.read_text(encoding="utf-8", errors="replace") if next_g12_path.exists() else ""
    for token in (
        "G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT",
        "37/37",
        "31",
        "17",
        "55/55",
        "NO_PROMOTION_VERDICT",
        "validation_safe=false",
        "outcome_review_opened=false",
        "live_effect=false",
    ):
        if token not in next_g12:
            failures.append({"check": "next_g12_prompt", "missing": token})

    optional_path = ROUTE_DIR / f"{builder.PREFIX}_OPTIONAL_PARALLEL_PROMPT_PACKS_{builder.DATE}.md"
    optional = optional_path.read_text(encoding="utf-8", errors="replace") if optional_path.exists() else ""
    for token in ("NOFILL_READONLY_TICK_RECOVERY_MANIFEST_FOR_BLOCKED_WINDOWS", "NOFILL_REJECT_CONTAMINATION_FIXTURE_LEARNING_ROUTE"):
        if token not in optional:
            failures.append({"check": "optional_parallel_prompt", "missing": token})

    checklist = parsed.get(f"{builder.PREFIX}_INSTRUCTION_COVERAGE_CHECKLIST_{builder.DATE}.json", {})
    if checklist.get("all_requirements_mapped") is not True:
        failures.append({"check": "instruction_checklist", "value": checklist})
    if len(checklist.get("prompt_to_artifact_checklist", [])) < 21:
        failures.append({"check": "instruction_checklist_count", "value": len(checklist.get("prompt_to_artifact_checklist", []))})

    completion = parsed.get(f"{builder.PREFIX}_COMPLETION_AUDIT_{builder.DATE}.json", {})
    if completion.get("can_mark_goal_complete") is not True or completion.get("completion_standard_satisfied") is not True:
        failures.append({"check": "completion_audit", "value": completion})
    if completion.get("missing_incomplete_or_weak_requirements") != []:
        failures.append({"check": "completion_missing", "value": completion.get("missing_incomplete_or_weak_requirements")})

    syntax_failures = scan_python_syntax()
    if syntax_failures:
        failures.append({"check": "python_syntax", "failures": syntax_failures})

    text_scan = scan_text_artifacts()
    if not text_scan["ok"]:
        failures.append({"check": "artifact_text_scan", "value": text_scan})

    result = {
        "route_id": builder.ROUTE_ID,
        "schema_version": builder.SCHEMA_VERSION,
        "ok": failures == [],
        "can_mark_goal_complete": failures == [],
        "failures": failures,
        "warnings": warnings,
        "diff_scope": scope,
        "runtime_forward_capture_field_count": len(runtime_fields),
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
