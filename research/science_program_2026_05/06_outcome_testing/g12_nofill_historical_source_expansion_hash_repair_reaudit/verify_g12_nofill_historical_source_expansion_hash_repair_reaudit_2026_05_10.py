"""Verifier for the independent G12 hash-repair reaudit package."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from typing import Any

import build_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10 as builder


ROUTE_DIR = builder.ROUTE_DIR
RESULT_PATH = ROUTE_DIR / builder.VERIFICATION_RESULT_NAME
PLACEHOLDER_FRAGMENTS = ("tbd", "todo", "unknown", "maybe", "not yet decided")


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


def verify_python_syntax() -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    for path in ROUTE_DIR.glob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append({"path": builder.rel(path), "error": str(exc)})
    return failures


def scan_placeholders() -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for path in sorted(list(ROUTE_DIR.glob("*.json")) + list(ROUTE_DIR.glob("*.md"))):
        if path.name == builder.VERIFICATION_RESULT_NAME:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for fragment in PLACEHOLDER_FRAGMENTS:
            if fragment in text:
                hits.append({"path": builder.rel(path), "fragment": fragment})
    return hits


def git_diff_scope() -> dict[str, Any]:
    diff = subprocess.run(["git", "diff", "--name-only"], cwd=builder.REPO_ROOT, text=True, capture_output=True, check=False)
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=builder.REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    paths = sorted(
        {
            line.strip().replace("\\", "/")
            for line in (diff.stdout + "\n" + untracked.stdout).splitlines()
            if line.strip()
        }
    )
    forbidden = [path for path in paths if any(path.startswith(prefix) for prefix in builder.FORBIDDEN_DIFF_PREFIXES)]
    return {"changed_or_untracked_paths": paths, "forbidden_live_surface_paths": forbidden, "ok": forbidden == []}


def verify() -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    missing = [name for name in builder.REQUIRED_ARTIFACTS if not (ROUTE_DIR / name).exists()]
    if missing:
        failures.append({"check": "required_artifacts_exist", "missing": missing})

    parsed: dict[str, Any] = {}
    for name in builder.JSON_ARTIFACTS:
        path = ROUTE_DIR / name
        if not path.exists():
            continue
        try:
            parsed[name] = load_json(path)
        except json.JSONDecodeError as exc:
            failures.append({"check": "json_parse", "file": name, "error": str(exc)})

    for name, payload in parsed.items():
        issues = safe_flag_issues(payload, name)
        if issues:
            failures.append({"check": "safe_flags", "file": name, "issues": issues})

    for md_path in ROUTE_DIR.glob("*.md"):
        text = md_path.read_text(encoding="utf-8", errors="replace")
        for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
            if token not in text:
                failures.append({"check": "md_control_tokens", "file": md_path.name, "missing": token})
        for token in ("validation_safe=true", "outcome_review_opened=true", "live_effect=true"):
            if token in text:
                failures.append({"check": "md_true_safe_flag", "file": md_path.name, "token": token})

    decision = parsed.get(f"{builder.PREFIX}_DECISION_LEDGER_{builder.DATE}.json", {})
    if decision.get("terminal_decision") != builder.ACCEPT_DECISION:
        failures.append({"check": "terminal_decision", "value": decision.get("terminal_decision")})
    if decision.get("remaining_exact_repair_blocker_count") != 0:
        failures.append({"check": "remaining_blockers", "value": decision.get("remaining_exact_repair_blocker_count")})

    closure = parsed.get(f"{builder.PREFIX}_EXACT_BLOCKER_CLOSURE_REAUDIT_{builder.DATE}.json", {})
    if closure.get("audit_passed") is not True or closure.get("closed_requirement_count") != 3:
        failures.append({"check": "exact_blocker_closure", "value": closure})
    roles = {record.get("role") for record in closure.get("records", [])}
    if roles != set(builder.EXPECTED_HASHES):
        failures.append({"check": "exact_blocker_roles", "value": sorted(roles)})
    for record in closure.get("records", []):
        if record.get("current_recomputed_sha256") != builder.EXPECTED_HASHES.get(record.get("role")):
            failures.append({"check": "exact_hash_value", "value": record})

    source_hash = parsed.get(f"{builder.PREFIX}_SOURCE_HASH_PARSER_HASH_RECOMPUTATION_AUDIT_{builder.DATE}.json", {})
    if source_hash.get("audit_passed") is not True:
        failures.append({"check": "source_hash_parser_hash", "value": source_hash})
    if source_hash.get("packet_parser_code_hashes") != [builder.EXPECTED_HASHES["parser_or_verifier:builder"]]:
        failures.append({"check": "packet_parser_code_hash", "value": source_hash.get("packet_parser_code_hashes")})

    semantic = parsed.get(f"{builder.PREFIX}_SEMANTIC_NO_ROW_CHANGE_REAUDIT_{builder.DATE}.json", {})
    if semantic.get("audit_passed") is not True:
        failures.append({"check": "semantic_no_row_change", "value": semantic})
    if semantic.get("observed_row_identities") != builder.EXPECTED_ROWS:
        failures.append({"check": "expected_rows", "value": semantic.get("observed_row_identities")})
    counts = semantic.get("target_admission_counts", {})
    for key, expected in builder.EXPECTED_COUNTS.items():
        if counts.get(key) != expected:
            failures.append({"check": "target_admission_counts", "key": key, "value": counts.get(key)})
    duplicates = semantic.get("duplicate_denominators", {})
    if duplicates != builder.EXPECTED_DUPLICATES:
        failures.append({"check": "duplicate_denominators", "value": duplicates})

    packet = parsed.get(f"{builder.PREFIX}_PACKET_HASH_MANIFEST_REAUDIT_{builder.DATE}.json", {})
    if packet.get("audit_passed") is not True or packet.get("packet_sha256_recomputed") != builder.EXPECTED_PACKET_SHA:
        failures.append({"check": "packet_hash_manifest", "value": packet})

    target = parsed.get(f"{builder.PREFIX}_TARGET_VERIFIER_TEST_RERUN_AUDIT_{builder.DATE}.json", {})
    if target.get("audit_passed") is not True:
        failures.append({"check": "target_verifier_tests", "value": target})
    repair = parsed.get(f"{builder.PREFIX}_REPAIR_VERIFIER_TEST_RERUN_AUDIT_{builder.DATE}.json", {})
    if repair.get("audit_passed") is not True:
        failures.append({"check": "repair_verifier_tests", "value": repair})

    noleak = parsed.get(f"{builder.PREFIX}_NOLEAK_SAFE_FLAG_LIVE_SURFACE_AUDIT_{builder.DATE}.json", {})
    if noleak.get("audit_passed") is not True:
        failures.append({"check": "noleak_safe_live_surface", "value": noleak})

    future = parsed.get(f"{builder.PREFIX}_FUTURE_ROUTE_ELIGIBILITY_LEDGER_{builder.DATE}.json", {})
    if future.get("accepted_for_next_evidence_class_prompt") is not True:
        failures.append({"check": "future_route_eligibility", "value": future})
    if future.get("validation_execution_remains_closed") is not True:
        failures.append({"check": "future_route_validation_closed", "value": future})

    syntax = parsed.get(f"{builder.PREFIX}_SYNTAX_COMPILE_AUDIT_{builder.DATE}.json", {})
    if syntax.get("audit_passed") is not True:
        failures.append({"check": "syntax_compile", "value": syntax})

    completion = parsed.get(f"{builder.PREFIX}_COMPLETION_AUDIT_{builder.DATE}.json", {})
    if completion.get("completion_standard_satisfied") is not True or completion.get("can_mark_goal_complete") is not True:
        failures.append({"check": "completion_standard", "value": completion})
    if completion.get("missing_incomplete_or_weak_requirements") != []:
        failures.append({"check": "completion_missing", "value": completion.get("missing_incomplete_or_weak_requirements")})
    requirement_ids = {row.get("requirement_id") for row in completion.get("prompt_to_artifact_checklist", [])}
    required_ids = {
        "three_repaired_hashes",
        "source_hash_manifest",
        "packet_parser_code_hash",
        "target_packet_hash_manifest",
        "semantic_no_row_change",
        "target_verifier_tests",
        "repair_verifier_tests",
        "noleak_safe_live_surface",
        "counts_2_37_9",
        "duplicates_2_2_2",
        "next_prompt_pack",
        "g12_builder_verifier_tests",
    }
    if not required_ids.issubset(requirement_ids):
        failures.append({"check": "completion_checklist_coverage", "missing": sorted(required_ids - requirement_ids)})

    placeholder_hits = scan_placeholders()
    if placeholder_hits:
        failures.append({"check": "placeholder_scan", "hits": placeholder_hits[:50]})

    syntax_failures = verify_python_syntax()
    if syntax_failures:
        failures.append({"check": "python_ast_syntax", "failures": syntax_failures})

    diff_scope = git_diff_scope()
    if diff_scope["ok"] is not True:
        failures.append({"check": "forbidden_live_surface_diff", "paths": diff_scope["forbidden_live_surface_paths"]})
    if diff_scope["changed_or_untracked_paths"]:
        warnings.append({"check": "dirty_paths_for_scoped_commit", "paths": diff_scope["changed_or_untracked_paths"]})

    result = {
        "ok": failures == [],
        "route_id": builder.ROUTE_ID,
        "schema_version": f"{builder.SCHEMA_VERSION}_verifier_v1",
        "terminal_decision": decision.get("terminal_decision"),
        "failures": failures,
        "warnings": warnings,
        "packet_row_count": 2 if semantic.get("observed_row_identities") == builder.EXPECTED_ROWS else None,
        "blocked_candidate_count": semantic.get("target_admission_counts", {}).get("blocked_candidate_count"),
        "rejected_candidate_count": semantic.get("target_admission_counts", {}).get("rejected_candidate_count"),
        "duplicate_denominators": "2/2/2" if semantic.get("duplicate_denominators") == builder.EXPECTED_DUPLICATES else None,
        "remaining_exact_repair_blocker_count": decision.get("remaining_exact_repair_blocker_count"),
        "can_mark_goal_complete": failures == [],
        "promotion_verdict": builder.PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    verification = verify()
    raise SystemExit(0 if verification["ok"] else 1)
