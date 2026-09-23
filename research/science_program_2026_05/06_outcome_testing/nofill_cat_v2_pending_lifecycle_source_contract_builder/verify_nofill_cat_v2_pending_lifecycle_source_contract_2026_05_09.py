from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from build_nofill_cat_v2_pending_lifecycle_source_contract_2026_05_09 import (
    DUPLICATE_CONTROL_REQUIRED_FIELDS,
    EXPECTED_ACCEPTED_SPLIT,
    EXPECTED_DUPLICATE_POSTURE,
    EXPECTED_LABEL_COUNTS,
    EXPECTED_PARTITION,
    EXPECTED_REJECT_COUNTS,
    EXPECTED_SOURCE_LANE_COUNTS,
    FORBIDDEN_DECISION_TIME_FIELD_NAMES,
    PROMOTION_VERDICT,
    REPO_ROOT,
    REQUIRED_FIELD_FAMILIES,
    ROUTE_DIR,
    ROW_LEDGER,
    contract_fields,
    read_jsonl,
    recompute_counts,
    required_output_files,
    validate_duplicate_denominator_record,
)


ALLOWED_CHANGED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_pending_lifecycle_source_contract_builder/",
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
FORBIDDEN_JSON_TRUE_FLAGS = ("validation_safe", "outcome_review_opened", "live_effect")


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
        paths.append(path)
    return paths


def committed_range_paths() -> list[str]:
    two_commit = git_paths(["diff", "--name-only", "HEAD~2..HEAD"])
    if two_commit and not any(path.startswith("GIT_ERROR:") for path in two_commit):
        return two_commit
    one_commit = git_paths(["diff", "--name-only", "HEAD~1..HEAD"])
    return one_commit


def live_surface_check() -> dict[str, Any]:
    working_paths = git_paths(["diff", "--name-only", "HEAD"])
    staged_paths = git_paths(["diff", "--cached", "--name-only"])
    status_paths = git_status_paths()
    committed_paths = committed_range_paths()
    # Main often has unrelated live-monitoring/runtime dirt. Verify this lane
    # by the committed source-contract diff while preserving workspace dirt as
    # informational context.
    if committed_paths and not any(path.startswith("GIT_ERROR:") for path in committed_paths):
        checked_paths = sorted(set(staged_paths + committed_paths))
        checked_scope = "committed_lane_diff"
    else:
        checked_paths = sorted(set(working_paths + staged_paths + status_paths + committed_paths))
        checked_scope = "workspace_and_commit_diff"
    forbidden = [
        path
        for path in checked_paths
        if path
        and not path.startswith("GIT_ERROR:")
        and (
            any(path.startswith(prefix) for prefix in FORBIDDEN_CHANGED_PREFIXES)
            or not any(path.startswith(prefix) for prefix in ALLOWED_CHANGED_PREFIXES)
        )
    ]
    return {
        "working_paths": working_paths,
        "staged_paths": staged_paths,
        "status_paths": status_paths,
        "committed_range_paths": committed_paths,
        "checked_paths": checked_paths,
        "checked_scope": checked_scope,
        "workspace_paths_informational_only": checked_scope == "committed_lane_diff",
        "forbidden_paths": forbidden,
        "status": "PASS" if not forbidden else "FAIL",
    }


def verify_required_files() -> dict[str, Any]:
    missing = [name for name in required_output_files() if not (ROUTE_DIR / name).exists()]
    return {"missing": missing, "status": "PASS" if not missing else "FAIL"}


def verify_counts() -> dict[str, Any]:
    counts = recompute_counts(read_jsonl(ROW_LEDGER))
    failures = []
    if counts["partition"] != EXPECTED_PARTITION:
        failures.append({"partition": counts["partition"]})
    if counts["accepted_split"] != EXPECTED_ACCEPTED_SPLIT:
        failures.append({"accepted_split": counts["accepted_split"]})
    if counts["accepted_label_counts"] != dict(sorted(EXPECTED_LABEL_COUNTS.items())):
        failures.append({"accepted_label_counts": counts["accepted_label_counts"]})
    if counts["accepted_source_lane_counts"] != dict(sorted(EXPECTED_SOURCE_LANE_COUNTS.items())):
        failures.append({"accepted_source_lane_counts": counts["accepted_source_lane_counts"]})
    for key, expected in EXPECTED_DUPLICATE_POSTURE.items():
        if counts["duplicate_posture"].get(key) != expected:
            failures.append({f"duplicate_posture.{key}": counts["duplicate_posture"].get(key)})
    blocked_with_label = [
        row.get("packet_row_id")
        for row in counts["blocked_rows"]
        if row.get("categorical_input_label") is not None
        or row.get("categorical_lifecycle_label") is not None
        or row.get("in_accepted_packet_denominator") is not False
    ]
    rejected_with_label = [
        row.get("packet_row_id")
        for row in counts["rejected_rows"]
        if row.get("categorical_input_label") is not None
        or row.get("categorical_lifecycle_label") is not None
        or row.get("in_accepted_packet_denominator") is not False
    ]
    if blocked_with_label:
        failures.append({"blocked_with_label_or_denominator": blocked_with_label})
    if rejected_with_label:
        failures.append({"rejected_with_label_or_denominator": rejected_with_label})
    return {
        "counts": {
            "partition": counts["partition"],
            "accepted_split": counts["accepted_split"],
            "accepted_label_counts": counts["accepted_label_counts"],
            "accepted_source_lane_counts": counts["accepted_source_lane_counts"],
            "duplicate_posture": counts["duplicate_posture"],
            "blocker_code_counts": counts["blocker_code_counts"],
            "reject_code_counts": counts["reject_code_counts"],
        },
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }


def verify_generated_json_and_markdown() -> dict[str, Any]:
    json_failures = []
    parsed_json = []
    for name in required_output_files():
        if not name.endswith(".json"):
            continue
        path = ROUTE_DIR / name
        data = read_json(path)
        parsed_json.append(name)
        text = path.read_text(encoding="utf-8", errors="replace")
        if PROMOTION_VERDICT not in text:
            json_failures.append({"file": name, "issue": "missing_NO_PROMOTION_VERDICT"})
        for key_path, value in flatten_json(data):
            leaf = key_path.split(".")[-1].split("[")[0]
            if leaf in FORBIDDEN_JSON_TRUE_FLAGS and value is not False:
                json_failures.append({"file": name, "path": key_path, "value": value})

    markdown_failures = []
    parsed_markdown = []
    for name in required_output_files():
        if not name.endswith(".md"):
            continue
        path = ROUTE_DIR / name
        parsed_markdown.append(name)
        if PROMOTION_VERDICT not in path.read_text(encoding="utf-8", errors="replace"):
            markdown_failures.append({"file": name, "issue": "missing_NO_PROMOTION_VERDICT"})

    return {
        "json_files": parsed_json,
        "markdown_files": parsed_markdown,
        "json_failures": json_failures,
        "markdown_failures": markdown_failures,
        "status": "PASS" if parsed_json and parsed_markdown and not json_failures and not markdown_failures else "FAIL",
    }


def verify_schema_fields() -> dict[str, Any]:
    schema = read_json(ROUTE_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_SCHEMA_FIELDS_2026-05-09.json")
    fields = schema.get("contract_fields", [])
    families = {field.get("field_family") for field in fields}
    missing_families = [family for family in REQUIRED_FIELD_FAMILIES if family not in families]
    required_metadata = {
        "field_name",
        "field_family",
        "source_timing",
        "as_of_rule",
        "allowed_source_types",
        "required_or_optional",
        "no_leak_role",
        "forbidden_substitute_fields",
        "hash_requirements",
        "duplicate_denominator_role",
        "capture_availability",
    }
    metadata_failures = [
        {"field_name": field.get("field_name"), "missing": sorted(required_metadata - set(field))}
        for field in fields
        if required_metadata - set(field)
    ]
    forbidden_field_names = sorted(
        set(field.get("field_name") for field in fields) & FORBIDDEN_DECISION_TIME_FIELD_NAMES
    )
    return {
        "field_count": len(fields),
        "missing_families": missing_families,
        "metadata_failures": metadata_failures,
        "forbidden_field_names": forbidden_field_names,
        "status": "PASS" if fields and not missing_families and not metadata_failures and not forbidden_field_names else "FAIL",
    }


def verify_duplicate_control() -> dict[str, Any]:
    control = read_json(ROUTE_DIR / "NOFILL_CAT_V2_DUPLICATE_DENOMINATOR_VERIFIER_CONTROL_2026-05-09.json")
    missing_required = [field for field in DUPLICATE_CONTROL_REQUIRED_FIELDS if field not in control.get("required_fields", [])]
    valid_errors = validate_duplicate_denominator_record(control["valid_example"])
    invalid_failures = []
    for item in control["invalid_examples"]:
        errors = validate_duplicate_denominator_record(item["record"])
        if not errors:
            invalid_failures.append({"case_id": item["case_id"], "issue": "invalid_example_accepted"})
        if errors != item["expected_errors"]:
            invalid_failures.append({"case_id": item["case_id"], "expected": item["expected_errors"], "actual": errors})
    for key, expected in EXPECTED_DUPLICATE_POSTURE.items():
        if control["duplicate_posture"].get(key) != expected:
            invalid_failures.append({"duplicate_posture": key, "actual": control["duplicate_posture"].get(key)})
    return {
        "missing_required": missing_required,
        "valid_example_errors": valid_errors,
        "invalid_failures": invalid_failures,
        "status": "PASS" if not missing_required and not valid_errors and not invalid_failures else "FAIL",
    }


def verify_blocker_reject_boundary() -> dict[str, Any]:
    taxonomy = read_json(ROUTE_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_BLOCKER_TAXONOMY_2026-05-09.json")
    failures = []
    if taxonomy.get("blocker_total") != 8:
        failures.append({"blocker_total": taxonomy.get("blocker_total")})
    if taxonomy.get("reject_total") != 65:
        failures.append({"reject_total": taxonomy.get("reject_total")})
    blocker_count = sum(item.get("count", 0) for item in taxonomy.get("blocker_families", []))
    reject_count = sum(item.get("count", 0) for item in taxonomy.get("reject_families", []))
    if blocker_count != 8:
        failures.append({"blocker_family_sum": blocker_count})
    if reject_count != 65:
        failures.append({"reject_family_sum": reject_count})
    reject_counts = {item["family_id"]: item["count"] for item in taxonomy.get("reject_families", [])}
    for key, expected in EXPECTED_REJECT_COUNTS.items():
        if reject_counts.get(key) != expected:
            failures.append({f"reject_counts.{key}": reject_counts.get(key)})
    for item in taxonomy.get("blocker_families", []):
        if item.get("result_use") != "forbidden":
            failures.append({"blocker_result_use": item})
        if "outside_accepted_labels_and_denominators" not in item.get("denominator_policy", ""):
            failures.append({"blocker_denominator_policy": item})
    for item in taxonomy.get("reject_families", []):
        if "no_label_no_denominator_no_result_use" not in item.get("policy", ""):
            failures.append({"reject_policy": item})
    return {"failures": failures, "status": "PASS" if not failures else "FAIL"}


def verify_capture_backlog() -> dict[str, Any]:
    backlog = read_json(ROUTE_DIR / "NOFILL_CAT_V2_PENDING_SOURCE_CAPTURE_BACKLOG_2026-05-09.json")
    failures = []
    for item in backlog.get("backlog_items", []):
        if item.get("may_modify_live_code_in_this_lane") is not False:
            failures.append({"live_code_change_allowed": item["backlog_id"]})
        forbidden = set(item.get("forbidden", []))
        if not forbidden:
            failures.append({"missing_forbidden_boundary": item["backlog_id"]})
    if backlog.get("changes_live_trading_behavior") is not False:
        failures.append({"changes_live_trading_behavior": backlog.get("changes_live_trading_behavior")})
    return {"failures": failures, "status": "PASS" if not failures else "FAIL"}


def verify_builder_field_source() -> dict[str, Any]:
    fields = contract_fields()
    field_names = {field["field_name"] for field in fields}
    required_names = {
        "pending_create_utc",
        "pending_cancel_or_expiry_utc",
        "cancel_or_expiry_reason_code",
        "active_pending_window_start_utc",
        "active_pending_window_end_utc",
        "decision_asof_utc",
        "side_aware_entry_touch_status",
        "terminal_area_touch_status",
        "protective_level_touch_status",
        "no_touch_proof_through_utc",
        "source_coverage_status",
        "quote_side_used",
        "source_granularity",
        "parser_version",
        "source_hash_manifest",
        "source_path_list",
        "nofill_duplicate_key",
        "duplicate_group_id",
        "canonical_counting_row_id",
        "row_level_denominator_scope",
        "unique_key_denominator_scope",
        "noncanonical_projection_exclusion_policy",
        "missing_source_blocker_family",
        "same_tick_same_bar_ambiguity_status",
        "label_family",
    }
    missing = sorted(required_names - field_names)
    return {"missing": missing, "status": "PASS" if not missing else "FAIL"}


def main() -> int:
    required = verify_required_files()
    counts = verify_counts()
    json_md = verify_generated_json_and_markdown()
    schema = verify_schema_fields()
    duplicate = verify_duplicate_control()
    blocker = verify_blocker_reject_boundary()
    backlog = verify_capture_backlog()
    builder_fields = verify_builder_field_source()
    py_compile = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            str(ROUTE_DIR / "build_nofill_cat_v2_pending_lifecycle_source_contract_2026_05_09.py"),
            str(ROUTE_DIR / "verify_nofill_cat_v2_pending_lifecycle_source_contract_2026_05_09.py"),
            str(ROUTE_DIR / "test_nofill_cat_v2_pending_lifecycle_source_contract_2026_05_09.py"),
        ]
    )
    pytest = run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(ROUTE_DIR / "test_nofill_cat_v2_pending_lifecycle_source_contract_2026_05_09.py"),
            "-q",
        ]
    )
    live_surface = live_surface_check()
    checks = {
        "required_files": required,
        "counts": counts,
        "generated_json_and_markdown": json_md,
        "schema_fields": schema,
        "duplicate_control": duplicate,
        "blocker_reject_boundary": blocker,
        "capture_backlog": backlog,
        "builder_field_source": builder_fields,
        "py_compile": py_compile,
        "focused_pytest": pytest,
        "live_surface_diff": live_surface,
    }
    status = all(
        [
            required["status"] == "PASS",
            counts["status"] == "PASS",
            json_md["status"] == "PASS",
            schema["status"] == "PASS",
            duplicate["status"] == "PASS",
            blocker["status"] == "PASS",
            backlog["status"] == "PASS",
            builder_fields["status"] == "PASS",
            py_compile["returncode"] == 0,
            pytest["returncode"] == 0,
            live_surface["status"] == "PASS",
        ]
    )
    result = {
        "route_id": "NOFILL_CAT_V2_PENDING_LIFECYCLE_SOURCE_CONTRACT_BUILDER",
        "status": "PASS" if status else "FAIL",
        "can_mark_goal_complete": status,
        "checks": checks,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if status else 1


if __name__ == "__main__":
    raise SystemExit(main())
