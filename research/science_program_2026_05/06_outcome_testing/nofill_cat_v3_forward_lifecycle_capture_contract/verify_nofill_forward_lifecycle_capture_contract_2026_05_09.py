from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from build_nofill_forward_lifecycle_capture_contract_2026_05_09 import (
    FIELD_FAMILIES,
    FORBIDDEN_SOURCE_FIELD_NAMES,
    PROMOTION_VERDICT,
    REQUIRED_FIELD_NAMES,
    ROUTE_DIR,
    ROUTE_ID,
    REPO_ROOT,
    contract_fields,
    required_output_files,
    safety_flags,
    write_json,
    write_text,
)


ALLOWED_CHANGED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_forward_lifecycle_capture_contract",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)
FORBIDDEN_CHANGED_PREFIXES = (
    "src/",
    "prompts/",
    "config/agent_config.yaml",
    "config/profiles/",
    "scripts/canary",
    "scripts/canary_fixtures/",
    "run_agent.py",
    "knowledge_base/",
    "pipeline_state/",
    "shadow_logs/",
)
FORBIDDEN_TRUE_FLAGS = ("validation_safe", "outcome_review_opened", "live_effect")
FORBIDDEN_SOURCE_TYPES = (
    "account_history",
    "order_history",
    "mt5_account",
    "mt5_order",
    "mt5_deal",
    "paid_api",
    "databento",
    "credential",
    "remote_push",
)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def flatten_json(obj: Any, path: str = "") -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{path}.{key}" if path else str(key)
            rows.extend(flatten_json(value, child))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            rows.extend(flatten_json(value, f"{path}[{idx}]"))
    else:
        rows.append((path, obj))
    return rows


def run(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
    return {
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def git_paths(args: list[str]) -> list[str]:
    proc = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        return [f"GIT_ERROR: {proc.stderr.strip()}"]
    return [line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()]


def git_status_paths() -> list[str]:
    proc = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        return [f"GIT_ERROR: {proc.stderr.strip()}"]
    paths = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip().replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path.rstrip("/"))
    return paths


def live_surface_check() -> dict[str, Any]:
    committed_paths = git_paths(["diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"])
    checked_paths = sorted(set(committed_paths))
    forbidden = []
    for path in checked_paths:
        if not path or path.startswith("GIT_ERROR:"):
            forbidden.append(path)
            continue
        if any(path.startswith(prefix) for prefix in FORBIDDEN_CHANGED_PREFIXES):
            forbidden.append(path)
            continue
        if not any(path.startswith(prefix) for prefix in ALLOWED_CHANGED_PREFIXES):
            forbidden.append(path)
    return {
        "policy": "check_committed_scope_only; unrelated_workspace_dirt_is_informational",
        "forbidden_paths": forbidden,
        "status": "PASS" if not forbidden else "FAIL",
    }


def verify_required_files() -> dict[str, Any]:
    missing = [name for name in required_output_files() if not (ROUTE_DIR / name).exists()]
    return {"missing": missing, "status": "PASS" if not missing else "FAIL"}


def verify_json_flags() -> dict[str, Any]:
    failures = []
    parsed = []
    for name in required_output_files():
        if not name.endswith(".json"):
            continue
        path = ROUTE_DIR / name
        data = read_json(path)
        parsed.append(name)
        for flag, expected in safety_flags().items():
            if flag in data and data[flag] != expected:
                failures.append({"file": name, "flag": flag, "value": data[flag], "expected": expected})
        for key_path, value in flatten_json(data):
            leaf = key_path.split(".")[-1].split("[")[0]
            if leaf in FORBIDDEN_TRUE_FLAGS and value is not False:
                failures.append({"file": name, "path": key_path, "value": value, "issue": "forbidden_true_flag"})
        if PROMOTION_VERDICT not in path.read_text(encoding="utf-8", errors="replace"):
            failures.append({"file": name, "issue": "missing_NO_PROMOTION_VERDICT"})
    return {"parsed": parsed, "failures": failures, "status": "PASS" if parsed and not failures else "FAIL"}


def verify_markdown_flags() -> dict[str, Any]:
    failures = []
    parsed = []
    required_literals = [
        f"promotion_verdict: `{PROMOTION_VERDICT}`",
        "validation_safe: `false`",
        "outcome_review_opened: `false`",
        "live_effect: `false`",
        "opens_result_scoring: `false`",
        "changes_live_trading_behavior: `false`",
    ]
    for name in required_output_files():
        if not name.endswith(".md"):
            continue
        text = (ROUTE_DIR / name).read_text(encoding="utf-8", errors="replace")
        parsed.append(name)
        for literal in required_literals:
            if literal not in text:
                failures.append({"file": name, "missing": literal})
    return {"parsed": parsed, "failures": failures, "status": "PASS" if parsed and not failures else "FAIL"}


def verify_schema() -> dict[str, Any]:
    schema = read_json(ROUTE_DIR / "NOFILL_FORWARD_SOURCE_FIELD_SCHEMA_2026-05-09.json")
    fields = schema.get("contract_fields", [])
    field_names = [field.get("field_name") for field in fields]
    families = {field.get("field_family") for field in fields}
    required_metadata = {
        "field_name",
        "field_family",
        "required_or_optional",
        "allowed_source_types",
        "as_of_rule",
        "hash_requirement",
        "no_leak_role",
        "forbidden_substitute_fields",
        "capture_mode",
        "verification_rule",
    }
    missing_names = [name for name in REQUIRED_FIELD_NAMES if name not in field_names]
    missing_families = [family for family in sorted(FIELD_FAMILIES) if family not in families]
    metadata_failures = [
        {"field_name": field.get("field_name"), "missing": sorted(required_metadata - set(field))}
        for field in fields
        if required_metadata - set(field)
    ]
    forbidden_field_names = sorted(set(field_names) & FORBIDDEN_SOURCE_FIELD_NAMES)
    forbidden_source_types = []
    for field in fields:
        for source_type in field.get("allowed_source_types", []):
            lowered = str(source_type).lower()
            if any(token in lowered for token in FORBIDDEN_SOURCE_TYPES):
                forbidden_source_types.append({"field_name": field.get("field_name"), "source_type": source_type})
    expected_from_builder = contract_fields()
    builder_mismatch = len(fields) != len(expected_from_builder)
    failures = []
    if missing_names:
        failures.append({"missing_field_names": missing_names})
    if missing_families:
        failures.append({"missing_families": missing_families})
    if metadata_failures:
        failures.append({"metadata_failures": metadata_failures})
    if forbidden_field_names:
        failures.append({"forbidden_field_names": forbidden_field_names})
    if forbidden_source_types:
        failures.append({"forbidden_source_types": forbidden_source_types})
    if builder_mismatch:
        failures.append({"builder_mismatch": True})
    return {
        "field_count": len(fields),
        "family_count": len(families),
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }


def verify_duplicate_policy() -> dict[str, Any]:
    policy = read_json(ROUTE_DIR / "NOFILL_FORWARD_DUPLICATE_DENOMINATOR_POLICY_2026-05-09.json")
    text = json.dumps(policy, sort_keys=True)
    required_terms = [
        "nofill_duplicate_key",
        "duplicate_group_id",
        "accepted-first",
        "reject-overlap",
        "source-control",
        "source-impossible",
        "canonical_row_id",
    ]
    missing = [term for term in required_terms if term not in text]
    denominators = policy.get("denominators", {})
    expected_denominators = {
        "row_level_accepted_inputs": 225,
        "unique_nofill_duplicate_key": 182,
        "secondary_duplicate_group_id": 139,
    }
    failures = []
    if missing:
        failures.append({"missing_terms": missing})
    if denominators != expected_denominators:
        failures.append({"denominators": denominators, "expected": expected_denominators})
    return {"failures": failures, "status": "PASS" if not failures else "FAIL"}


def verify_backlog_and_next_prompts() -> dict[str, Any]:
    backlog = read_json(ROUTE_DIR / "NOFILL_FORWARD_CAPTURE_BACKLOG_AND_IMPLEMENTATION_ROUTE_2026-05-09.json")
    next_prompt = (ROUTE_DIR / "NOFILL_FORWARD_NEXT_PROMPT_PACK_2026-05-09.md").read_text(encoding="utf-8", errors="replace")
    failures = []
    if backlog.get("implementation_status") != "contract_only_no_live_wiring":
        failures.append({"implementation_status": backlog.get("implementation_status")})
    if not any(item.get("item") == "usdjpy_broker_native_quote_event_sequence_source_access" for item in backlog.get("backlog", [])):
        failures.append({"missing_backlog_item": "usdjpy quote sequence"})
    if "G12_NOFILL_CAT_V3_FORWARD_LIFECYCLE_CAPTURE_CONTRACT_AUDIT" not in next_prompt:
        failures.append({"next_prompt": "missing G12 audit prompt"})
    if "USDJPY Quote Event Sequence Source Access" not in next_prompt:
        failures.append({"next_prompt": "missing USDJPY source access prompt"})
    return {"failures": failures, "status": "PASS" if not failures else "FAIL"}


def update_completion_audit(results: dict[str, Any]) -> None:
    status = "PASS" if all(value.get("status") == "PASS" for value in results.values()) else "FAIL"
    json_path = ROUTE_DIR / "NOFILL_FORWARD_COMPLETION_AUDIT_2026-05-09.json"
    audit = read_json(json_path)
    audit["verification_results"] = {
        "status": status,
        "checks": results,
        "commands": [
            "python -m py_compile build_nofill_forward_lifecycle_capture_contract_2026_05_09.py verify_nofill_forward_lifecycle_capture_contract_2026_05_09.py",
            "python -B -m pytest test_nofill_forward_lifecycle_capture_contract_2026_05_09.py -q -p no:cacheprovider",
            "python verify_nofill_forward_lifecycle_capture_contract_2026_05_09.py",
        ],
    }
    audit["can_mark_goal_complete"] = status == "PASS"
    write_json(json_path, audit)

    md = (
        "# NOFILL Forward Completion Audit 2026-05-09\n\n"
        f"- route_id: `{ROUTE_ID}`\n"
        f"- promotion_verdict: `{PROMOTION_VERDICT}`\n"
        "- validation_safe: `false`\n"
        "- outcome_review_opened: `false`\n"
        "- live_effect: `false`\n"
        "- opens_result_scoring: `false`\n"
        "- changes_live_trading_behavior: `false`\n\n"
        "## Verification Status\n\n"
        f"`{status}`\n\n"
        "## Checks\n\n"
        + "\n".join(f"- `{name}`: `{result.get('status')}`" for name, result in results.items())
        + "\n"
    )
    write_text(ROUTE_DIR / "NOFILL_FORWARD_COMPLETION_AUDIT_2026-05-09.md", md)


def main() -> int:
    results = {
        "required_files": verify_required_files(),
        "json_flags": verify_json_flags(),
        "markdown_flags": verify_markdown_flags(),
        "schema": verify_schema(),
        "duplicate_policy": verify_duplicate_policy(),
        "backlog_and_next_prompts": verify_backlog_and_next_prompts(),
        "live_surface": live_surface_check(),
    }
    update_completion_audit(results)
    print(json.dumps(results, indent=2, sort_keys=True))
    if not all(value.get("status") == "PASS" for value in results.values()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
