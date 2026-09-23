"""Verifier for the GTOS local research data catalog implementation route."""

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import build_gtos_local_research_data_catalog_implementation_route_2026_05_10 as builder


ROUTE_DIR = builder.ROUTE_DIR
PREFIX = builder.PREFIX
DATE = builder.DATE
RESULT_NAME = f"{PREFIX}_VERIFICATION_RESULT_{DATE}.json"
PLACEHOLDER_RE = re.compile(r"\b(TBD|TODO|unknown|maybe|later)\b|unresolved vague", re.I)
REQUIRED_JSON_ARTIFACT_FAMILIES = {
    "context_anchor",
    "root_resolver_config",
    "root_resolver_config_schema",
    "catalog_implementation_decision_ledger",
    "catalog_schema",
    "search_result_ledger",
    "missing_window_ledger",
    "acquisition_request_manifest_schema",
    "acquisition_request_manifest_example",
    "recoverable_vs_non_generatable_classification_ledger",
    "source_hash_deferral_manifest",
    "forbidden_route_noleak_audit",
    "integration_guide",
    "saturation_self_redteam_pass",
    "instruction_coverage_checklist",
    "completion_audit",
    "output_manifest",
}
REQUIRED_MARKDOWN = {
    f"{PREFIX}_INTEGRATION_GUIDE_{DATE}.md",
    f"{PREFIX}_NEXT_G12_SOURCE_CONTROL_AUDIT_PROMPT_PACK_{DATE}.md",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE}.md",
}
REQUIRED_CATALOG_FIELDS = {
    "catalog_row_id",
    "root_id",
    "root_path",
    "absolute_path",
    "relative_path",
    "repo_relative_path",
    "source_family",
    "symbol",
    "source_date",
    "source_date_range",
    "timeframe",
    "file_extension",
    "size_bytes",
    "mtime_utc",
    "hash_policy",
    "sha256",
    "hash_status",
    "large_file_hash_deferral_id",
    "allowed_evidence_class",
    "forbidden_use_notes",
    "read_actions",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def rel(path: Path) -> str:
    return builder.rel(path)


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


def parse_artifacts() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]], list[dict[str, str]]]:
    failures: list[dict[str, Any]] = []
    json_payloads: dict[str, dict[str, Any]] = {}
    catalog_rows: list[dict[str, Any]] = []
    for path in sorted(ROUTE_DIR.glob("*.json")):
        if path.name == RESULT_NAME:
            continue
        try:
            payload = load_json(path)
            json_payloads[path.name] = payload
            issues = safe_flag_issues(payload, path.name)
            if issues:
                failures.append({"check": "safe_flags", "file": path.name, "issues": issues})
        except json.JSONDecodeError as exc:
            failures.append({"check": "json_parse", "file": path.name, "error": str(exc)})
    for path in sorted(ROUTE_DIR.glob("*.jsonl")):
        try:
            rows = read_jsonl(path)
            catalog_rows.extend(rows)
            for idx, row in enumerate(rows, start=1):
                issues = safe_flag_issues(row, f"{path.name}:{idx}")
                if issues:
                    failures.append({"check": "jsonl_safe_flags", "file": path.name, "line": idx, "issues": issues})
        except json.JSONDecodeError as exc:
            failures.append({"check": "jsonl_parse", "file": path.name, "error": str(exc)})
    placeholder_hits: list[dict[str, str]] = []
    for path in sorted(list(ROUTE_DIR.glob("*.json")) + list(ROUTE_DIR.glob("*.jsonl")) + list(ROUTE_DIR.glob("*.md"))):
        if path.name == RESULT_NAME:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if PLACEHOLDER_RE.search(text):
            placeholder_hits.append({"path": rel(path), "fragment": PLACEHOLDER_RE.search(text).group(0)})  # type: ignore[union-attr]
        if path.suffix == ".md":
            for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
                if token not in text:
                    failures.append({"check": "markdown_control_tokens", "file": path.name, "missing": token})
            for token in ("validation_safe=true", "outcome_review_opened=true", "live_effect=true"):
                if token in text:
                    failures.append({"check": "markdown_true_safe_flag", "file": path.name, "token": token})
    return failures, json_payloads, catalog_rows, placeholder_hits


def verify_required_artifacts(json_payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    families = {payload.get("artifact_family") for payload in json_payloads.values()}
    missing = REQUIRED_JSON_ARTIFACT_FAMILIES - families
    if missing:
        failures.append({"check": "required_json_artifact_families", "missing": sorted(missing)})
    missing_md = sorted(name for name in REQUIRED_MARKDOWN if not (ROUTE_DIR / name).exists())
    if missing_md:
        failures.append({"check": "required_markdown_artifacts", "missing": missing_md})
    catalog = ROUTE_DIR / f"{PREFIX}_CATALOG_{DATE}.jsonl"
    if not catalog.exists():
        failures.append({"check": "catalog_jsonl_exists", "missing": catalog.name})
    for script_name in (
        "build_gtos_local_research_data_catalog_implementation_route_2026_05_10.py",
        "verify_gtos_local_research_data_catalog_implementation_route_2026_05_10.py",
        "test_gtos_local_research_data_catalog_implementation_route_2026_05_10.py",
    ):
        if not (ROUTE_DIR / script_name).exists():
            failures.append({"check": "route_tooling_exists", "missing": script_name})
    return failures


def verify_catalog(catalog_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    if not catalog_rows:
        return [{"check": "catalog_rows", "issue": "zero catalog rows"}]
    hashed = 0
    deferrals = 0
    for row in catalog_rows:
        missing = REQUIRED_CATALOG_FIELDS - set(row)
        if missing:
            failures.append({"check": "catalog_required_fields", "row": row.get("catalog_row_id"), "missing": sorted(missing)})
        if row.get("allowed_evidence_class") != "SOURCE_CONTROL_ONLY":
            failures.append({"check": "catalog_evidence_class", "row": row.get("catalog_row_id"), "value": row.get("allowed_evidence_class")})
        if row.get("hash_status") == "sha256_complete":
            hashed += 1
            if not row.get("sha256"):
                failures.append({"check": "catalog_sha_missing", "row": row.get("catalog_row_id")})
        elif row.get("hash_status") == "deferred_large_file_requires_dedicated_hash_manifest":
            deferrals += 1
            if row.get("large_file_hash_deferral_id") == "not_applicable":
                failures.append({"check": "catalog_deferral_missing", "row": row.get("catalog_row_id")})
        else:
            failures.append({"check": "catalog_hash_status", "row": row.get("catalog_row_id"), "value": row.get("hash_status")})
        lower_path = str(row.get("absolute_path", "")).lower()
        if any(fragment in lower_path for fragment in builder.SENSITIVE_PATH_FRAGMENTS):
            failures.append({"check": "catalog_sensitive_path_leak", "row": row.get("catalog_row_id")})
    if hashed == 0:
        failures.append({"check": "catalog_hashed_count", "issue": "no hashed files"})
    if deferrals == 0:
        failures.append({"check": "catalog_deferral_count", "issue": "no large-file deferral records"})
    return failures


def verify_ledgers(json_payloads: dict[str, dict[str, Any]], catalog_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    root_config = json_payloads.get(f"{PREFIX}_ROOT_RESOLVER_CONFIG_{DATE}.json", {})
    root_ids = {root.get("root_id") for root in root_config.get("roots", [])}
    required_roots = {
        "current_worktree_data_root",
        "absolute_main_data_root",
        "absolute_main_tick_root",
        "absolute_main_shadow_logs",
        "prior_worktree_root",
        "sierra_chart_root",
        "sierra_chart_data_root",
    }
    if not required_roots.issubset(root_ids):
        failures.append({"check": "root_config_required_roots", "missing": sorted(required_roots - root_ids)})

    search = json_payloads.get(f"{PREFIX}_SEARCH_RESULT_LEDGER_{DATE}.json", {})
    if search.get("query_count", 0) < 5:
        failures.append({"check": "search_query_count", "value": search.get("query_count")})
    if search.get("positive_query_count", 0) < 1 or search.get("negative_query_count", 0) < 1:
        failures.append(
            {
                "check": "search_positive_negative_evidence",
                "positive": search.get("positive_query_count"),
                "negative": search.get("negative_query_count"),
            }
        )
    for row in search.get("rows", []):
        if row.get("match_count", 0) == 0 and not row.get("negative_evidence"):
            failures.append({"check": "search_negative_evidence_missing", "query_id": row.get("query_id")})
        if row.get("match_count", 0) > 0 and not row.get("positive_evidence"):
            failures.append({"check": "search_positive_evidence_missing", "query_id": row.get("query_id")})

    missing = json_payloads.get(f"{PREFIX}_MISSING_WINDOW_LEDGER_{DATE}.json", {})
    if missing.get("recoverable_market_data_count", 0) < 1:
        failures.append({"check": "missing_recoverable_market_data_count", "value": missing.get("recoverable_market_data_count")})
    if missing.get("non_generatable_source_state_count", 0) < 1:
        failures.append({"check": "missing_non_generatable_count", "value": missing.get("non_generatable_source_state_count")})
    blocker_codes = {row.get("blocker_code") for row in missing.get("rows", [])}
    if "NON_GENERATABLE_SOURCE_STATE" not in blocker_codes:
        failures.append({"check": "missing_non_generatable_blocker_code", "codes": sorted(str(code) for code in blocker_codes)})

    acquisition = json_payloads.get(f"{PREFIX}_ACQUISITION_REQUEST_MANIFEST_EXAMPLE_{DATE}.json", {})
    if acquisition.get("request_count", 0) < 1:
        failures.append({"check": "acquisition_request_count", "value": acquisition.get("request_count")})
    if any(request.get("execution_status") != "not_executed_manifest_only" for request in acquisition.get("requests", [])):
        failures.append({"check": "acquisition_execution_status", "issue": "non_manifest_request"})

    hash_manifest = json_payloads.get(f"{PREFIX}_SOURCE_HASH_DEFERRAL_MANIFEST_{DATE}.json", {})
    if hash_manifest.get("hashed_file_count") != sum(1 for row in catalog_rows if row.get("hash_status") == "sha256_complete"):
        failures.append({"check": "hash_manifest_hashed_count"})
    if hash_manifest.get("large_file_deferral_count") != sum(
        1 for row in catalog_rows if row.get("hash_status") == "deferred_large_file_requires_dedicated_hash_manifest"
    ):
        failures.append({"check": "hash_manifest_deferral_count"})

    classification = json_payloads.get(f"{PREFIX}_RECOVERABLE_NON_GENERATABLE_CLASSIFICATION_LEDGER_{DATE}.json", {})
    classes = {row.get("class") for row in classification.get("classification_rows", [])}
    if "recoverable_market_data" not in classes or "non_generatable_historical_gtos_source_state" not in classes:
        failures.append({"check": "classification_required_classes", "classes": sorted(str(item) for item in classes)})

    noleak = json_payloads.get(f"{PREFIX}_FORBIDDEN_ROUTE_NOLEAK_AUDIT_{DATE}.json", {})
    if noleak.get("audit_passed") is not True:
        failures.append({"check": "noleak_audit_passed", "value": noleak})

    completion = json_payloads.get(f"{PREFIX}_COMPLETION_AUDIT_{DATE}.json", {})
    if completion.get("completion_standard_satisfied") is not True or completion.get("can_mark_goal_complete") is not True:
        failures.append({"check": "completion_standard", "value": completion})
    if completion.get("missing_incomplete_or_weak_requirements") != []:
        failures.append({"check": "completion_missing_requirements", "value": completion.get("missing_incomplete_or_weak_requirements")})
    requirement_ids = {row.get("requirement_id") for row in completion.get("prompt_to_artifact_checklist", [])}
    required_requirement_ids = {
        "objective_route",
        "reusable_read_only_tool",
        "catalog_jsonl",
        "search_missing_acquisition",
        "recoverable_vs_non_generatable",
        "hash_and_deferral",
        "no_leak_forbidden_surfaces",
        "integration_guide",
        "verifier_focused_tests",
        "safe_flags",
    }
    if not required_requirement_ids.issubset(requirement_ids):
        failures.append({"check": "completion_checklist_coverage", "missing": sorted(required_requirement_ids - requirement_ids)})
    return failures


def verify_python_syntax() -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for path in ROUTE_DIR.glob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append({"check": "python_ast_syntax", "file": path.name, "error": str(exc)})
    return failures


def verify_diff_scope() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    diff_scope = builder.git_diff_scope()
    failures: list[dict[str, Any]] = []
    if not diff_scope["ok"]:
        failures.append({"check": "forbidden_live_surface_diff", "paths": diff_scope["forbidden_live_surface_paths"]})
    return failures, diff_scope


def verify() -> dict[str, Any]:
    failures, json_payloads, catalog_rows, placeholder_hits = parse_artifacts()
    failures.extend(verify_required_artifacts(json_payloads))
    failures.extend(verify_catalog(catalog_rows))
    failures.extend(verify_ledgers(json_payloads, catalog_rows))
    failures.extend(verify_python_syntax())
    diff_failures, diff_scope = verify_diff_scope()
    failures.extend(diff_failures)
    if placeholder_hits:
        failures.append({"check": "placeholder_scan", "hits": placeholder_hits[:80]})
    result = builder.with_safe_flags(
        {
            "artifact_family": "verification_result",
            "route_id": builder.ROUTE_ID,
            "schema_version": f"{builder.SCHEMA_VERSION}_verifier_v1",
            "terminal_decision": builder.TERMINAL_DECISION,
            "ok": failures == [],
            "can_mark_goal_complete": failures == [],
            "failure_count": len(failures),
            "failures": failures,
            "catalog_row_count": len(catalog_rows),
            "json_artifact_count": len(json_payloads),
            "diff_scope": diff_scope,
            "placeholder_scan_passed": placeholder_hits == [],
        }
    )
    return result


def main() -> int:
    result = verify()
    (ROUTE_DIR / RESULT_NAME).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
