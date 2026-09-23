"""Verifier for the GTOS research capability limitation closure route."""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
DATE = "2026-05-10"
PREFIX = "GTOS_CAP_LIMIT_CLOSURE"
ROUTE_ID = "GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
LIMITATION_FAMILIES = {
    "market_data_absence",
    "historical_source_state_absence",
    "contamination_embargo_rejects",
    "worktree_blindness",
    "evidence_class_gate_friction",
    "data_catalog_weakness",
    "parser_hash_drift",
}
SAFE_FLAG_FALSE_KEYS = ("validation_safe", "outcome_review_opened", "live_effect")
FORBIDDEN_TRUE_KEYS = (
    "opens_result_scoring",
    "opens_validation",
    "opens_promotion",
    "opens_registry_edit",
    "opens_paid_api_or_databento_route",
    "opens_remote_push",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "opens_mt5_order_account_history_behavior",
    "changes_live_trading_behavior",
    "credentials_touched",
)
FORBIDDEN_DIFF_PREFIXES = (
    "src/components/",
    "src/safety/",
    "prompts/",
    "config/",
    "scripts/canary_fixtures/",
    "canaries/",
)
PLACEHOLDER_RE = re.compile(r"\b(TBD|TODO|unknown|maybe|later)\b|unresolved vague", re.I)
REQUIRED_ARTIFACT_FAMILIES = {
    "context_anchor",
    "source_hash_manifest",
    "limitation_decision_ledger",
    "market_data_acquisition_ladder",
    "historical_source_state_truth_taxonomy",
    "contamination_embargo_router",
    "worktree_bootstrap_data_root_resolver_design",
    "evidence_class_router_and_fast_audit_template",
    "local_research_data_catalog_schema",
    "parser_hash_drift_control_policy",
    "forbidden_route_ledger",
    "implementation_dependency_graph_and_route_ranking",
    "completion_audit",
    "instruction_coverage_checklist",
    "saturation_self_redteam_pass",
    "missing_window_ledger",
    "local_research_data_catalog_search_result_ledger",
}


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def with_safe_flags(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out.update(
        {
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
            "opens_result_scoring": False,
            "opens_validation": False,
            "opens_promotion": False,
            "opens_registry_edit": False,
            "opens_paid_api_or_databento_route": False,
            "opens_remote_push": False,
            "opens_live_restart": False,
            "opens_live_trading_behavior": False,
            "opens_mt5_order_account_history_behavior": False,
            "changes_live_trading_behavior": False,
            "credentials_touched": False,
        }
    )
    return out


def scan_safe_flags(obj: Any, path: str = "$") -> list[str]:
    issues: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}"
            if key in SAFE_FLAG_FALSE_KEYS and value is not False:
                issues.append(f"{child} must be false")
            if key in FORBIDDEN_TRUE_KEYS and value is True:
                issues.append(f"{child} opens forbidden surface")
            if key == "promotion_verdict" and value != PROMOTION_VERDICT:
                issues.append(f"{child} must be {PROMOTION_VERDICT}")
            issues.extend(scan_safe_flags(value, child))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            issues.extend(scan_safe_flags(item, f"{path}[{idx}]"))
    return issues


def parse_route_artifacts() -> tuple[list[str], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    issues: list[str] = []
    artifacts: dict[str, dict[str, Any]] = {}
    for path in sorted(ROUTE_DIR.glob("*.json")):
        try:
            payload = load_json(path)
            artifacts[path.name] = payload
            issues.extend(scan_safe_flags(payload, rel(path)))
        except Exception as exc:  # pragma: no cover
            issues.append(f"{rel(path)} JSON parse failed: {exc}")
    jsonl_rows: list[dict[str, Any]] = []
    for path in sorted(ROUTE_DIR.glob("*.jsonl")):
        try:
            rows = read_jsonl(path)
            jsonl_rows.extend(rows)
            for idx, row in enumerate(rows, start=1):
                issues.extend(scan_safe_flags(row, f"{rel(path)}:{idx}"))
        except Exception as exc:  # pragma: no cover
            issues.append(f"{rel(path)} JSONL parse failed: {exc}")
    for path in sorted(ROUTE_DIR.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8")
            if "NO_PROMOTION_VERDICT" not in text:
                issues.append(f"{rel(path)} missing NO_PROMOTION_VERDICT")
            if "validation_safe=true" in text or "outcome_review_opened=true" in text or "live_effect=true" in text:
                issues.append(f"{rel(path)} contains true safe flag text")
            if PLACEHOLDER_RE.search(text):
                issues.append(f"{rel(path)} contains placeholder or vague blocker token")
        except Exception as exc:  # pragma: no cover
            issues.append(f"{rel(path)} Markdown parse failed: {exc}")
    for path in list(ROUTE_DIR.glob("*.json")) + list(ROUTE_DIR.glob("*.jsonl")):
        text = path.read_text(encoding="utf-8")
        if PLACEHOLDER_RE.search(text):
            issues.append(f"{rel(path)} contains placeholder or vague blocker token")
    return issues, artifacts, jsonl_rows


def verify_required_artifacts(artifacts: dict[str, dict[str, Any]]) -> list[str]:
    families = {payload.get("artifact_family") for payload in artifacts.values()}
    missing = REQUIRED_ARTIFACT_FAMILIES - families
    return [f"missing artifact family: {family}" for family in sorted(missing)]


def verify_limitation_coverage() -> list[str]:
    issues: list[str] = []
    decision = load_json(ROUTE_DIR / f"{PREFIX}_LIMITATION_DECISION_LEDGER_{DATE}.json")
    families = set(decision.get("limitation_families", []))
    if families != LIMITATION_FAMILIES:
        issues.append(f"limitation families mismatch: {sorted(families)}")
    rows = decision.get("rows", [])
    if len(rows) != 7:
        issues.append(f"expected 7 limitation rows, found {len(rows)}")
    for row in rows:
        if not row.get("artifact_refs"):
            issues.append(f"{row.get('limitation_family')} has no artifact refs")
        if row.get("forbidden_boundary_preserved") is not True:
            issues.append(f"{row.get('limitation_family')} does not preserve forbidden boundary")
    return issues


def verify_catalog(jsonl_rows: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    catalog_rows = [row for row in jsonl_rows if row.get("artifact_family") == "local_research_data_catalog_row"]
    if not catalog_rows:
        issues.append("catalog prototype has zero rows")
        return issues
    required = {
        "root_id",
        "root_path",
        "source_type",
        "symbol",
        "source_date",
        "timeframe",
        "window_utc",
        "source_file",
        "hash_status",
        "lineage",
        "as_of_policy",
        "allowed_evidence_class",
    }
    for row in catalog_rows:
        missing = required - set(row)
        if missing:
            issues.append(f"catalog row {row.get('row_id')} missing fields {sorted(missing)}")
        if row.get("allowed_evidence_class") != "SOURCE_CONTROL_ONLY":
            issues.append(f"catalog row {row.get('row_id')} opens wrong evidence class")
        if row.get("hash_status") == "sha256_complete" and not row.get("file_hash_sha256"):
            issues.append(f"catalog row {row.get('row_id')} lacks hash despite sha256_complete")
    return issues


def verify_source_state_and_contamination() -> list[str]:
    issues: list[str] = []
    taxonomy = load_json(ROUTE_DIR / f"{PREFIX}_HISTORICAL_SOURCE_STATE_TRUTH_TAXONOMY_{DATE}.json")
    non_gen = set(taxonomy.get("non_generatable_historical_fields", []))
    if "pending_lifecycle_group_id" not in non_gen or "broker_actual_r" not in non_gen:
        issues.append("source-state taxonomy does not include core non-generatable fields")
    if "Price movement cannot backfill" not in taxonomy.get("price_movement_backfill_rule", ""):
        issues.append("source-state taxonomy lacks price movement backfill rule")
    router = load_json(ROUTE_DIR / f"{PREFIX}_CONTAMINATION_EMBARGO_ROUTER_{DATE}.json")
    guard = router.get("denominator_guard", {})
    if "G12_source_control_acceptance" not in guard.get("sealed_validation_denominator_requires", []):
        issues.append("contamination router lacks G12 denominator guard")
    if guard.get("rejects_count_as") != "source_control_rejects_only":
        issues.append("contamination router reject denominator guard is weak")
    return issues


def verify_hash_policy() -> list[str]:
    issues: list[str] = []
    policy = load_json(ROUTE_DIR / f"{PREFIX}_PARSER_HASH_DRIFT_CONTROL_POLICY_{DATE}.json")
    text_policy = policy.get("raw_sha_versus_lf_normalized_text_sha_policy", {})
    if "raw_sha256_required" not in text_policy.get("parser_code", ""):
        issues.append("parser code policy is not strict raw SHA")
    classes = {row.get("class"): row for row in policy.get("mutable_context_classification", [])}
    if "STRICT_HASH_REQUIRED" not in classes:
        issues.append("hash policy lacks STRICT_HASH_REQUIRED")
    live_state_class = classes.get("GENERATED_CONTEXT_VOLATILE", {})
    if ".context/LIVE_STATE.md" not in live_state_class.get("examples", []):
        issues.append("hash policy does not classify LIVE_STATE as generated context")
    repair = policy.get("next_repair_route_template", {})
    if "score outcomes" not in repair.get("forbidden_actions", []):
        issues.append("repair route template does not forbid outcome scoring")
    return issues


def verify_forbidden_diff_scan() -> dict[str, Any]:
    proc = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    changed = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].replace("\\", "/")
        changed.append(path)
    forbidden = [path for path in changed if path.startswith(FORBIDDEN_DIFF_PREFIXES)]
    return {
        "changed_or_untracked_paths": changed,
        "forbidden_live_surface_paths": forbidden,
        "ok": not forbidden,
        "returncode": proc.returncode,
        "stderr_tail": proc.stderr[-1000:],
    }


def verify_python_syntax() -> list[str]:
    issues: list[str] = []
    for path in [
        ROUTE_DIR / "build_gtos_research_capability_limitation_closure_control_route_2026_05_10.py",
        ROUTE_DIR / "verify_gtos_research_capability_limitation_closure_control_route_2026_05_10.py",
        ROUTE_DIR / "test_gtos_research_capability_limitation_closure_control_route_2026_05_10.py",
    ]:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            issues.append(f"{rel(path)} syntax parse failed: {exc}")
    return issues


def verify() -> dict[str, Any]:
    parse_issues, artifacts, jsonl_rows = parse_route_artifacts()
    issues = []
    issues.extend(parse_issues)
    issues.extend(verify_required_artifacts(artifacts))
    issues.extend(verify_limitation_coverage())
    issues.extend(verify_catalog(jsonl_rows))
    issues.extend(verify_source_state_and_contamination())
    issues.extend(verify_hash_policy())
    issues.extend(verify_python_syntax())
    diff_scan = verify_forbidden_diff_scan()
    if not diff_scan["ok"]:
        issues.append(f"forbidden live-surface diff paths: {diff_scan['forbidden_live_surface_paths']}")
    result = with_safe_flags(
        {
            "artifact_family": "verification_result",
            "can_mark_goal_complete": not issues,
            "catalog_row_count": len([row for row in jsonl_rows if row.get("artifact_family") == "local_research_data_catalog_row"]),
            "diff_scope": diff_scan,
            "failure_count": len(issues),
            "failures": issues,
            "limitation_family_count": len(LIMITATION_FAMILIES),
            "ok": not issues,
            "placeholder_scan_passed": not any("placeholder" in issue for issue in issues),
            "route_id": ROUTE_ID,
            "schema_version": f"{ROUTE_ID.lower()}_verifier_v1",
        }
    )
    output = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE}.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    sys.exit(0 if result["ok"] else 1)
