from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from build_g12_nofill_pending_source_contract_audit_2026_05_09 import (
    DECISION,
    EXPECTED_ACCEPTED_SPLIT,
    EXPECTED_DUPLICATE_POSTURE,
    EXPECTED_LABEL_COUNTS,
    EXPECTED_PARTITION,
    EXPECTED_SOURCE_LANE_COUNTS,
    PROMOTION_VERDICT,
    REPO_ROOT,
    REQUIRED_FIELD_FAMILIES,
    ROUTE_DIR,
    ROW_LEDGER,
    build_duplicate_review,
    read_jsonl,
    recompute_counts,
    required_output_files,
)


ALLOWED_CHANGED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v2_pending_source_contract_audit/",
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


def run(cmd: list[str], env: dict[str, str] | None = None) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, env=env)
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
    return [line.strip().strip('"').replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()]


def git_status_paths() -> list[str]:
    proc = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        return [f"GIT_ERROR: {proc.stderr.strip()}"]
    paths = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip().strip('"').replace("\\", "/")
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
    # by the committed G12 audit diff while preserving workspace dirt as
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


def verify_counts() -> dict[str, Any]:
    counts = recompute_counts(read_jsonl(ROW_LEDGER))
    failures = []
    if counts["partition"] != EXPECTED_PARTITION:
        failures.append({"partition": counts["partition"]})
    if counts["accepted_split"] != EXPECTED_ACCEPTED_SPLIT:
        failures.append({"accepted_split": counts["accepted_split"]})
    if counts["accepted_label_counts"] != EXPECTED_LABEL_COUNTS:
        failures.append({"accepted_label_counts": counts["accepted_label_counts"]})
    if counts["accepted_source_lane_counts"] != EXPECTED_SOURCE_LANE_COUNTS:
        failures.append({"accepted_source_lane_counts": counts["accepted_source_lane_counts"]})
    if counts["duplicate_posture"] != EXPECTED_DUPLICATE_POSTURE:
        failures.append({"duplicate_posture": counts["duplicate_posture"]})
    return {
        "counts": {
            "partition": counts["partition"],
            "accepted_split": counts["accepted_split"],
            "accepted_label_counts": counts["accepted_label_counts"],
            "accepted_source_lane_counts": counts["accepted_source_lane_counts"],
            "duplicate_posture": counts["duplicate_posture"],
        },
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }


def verify_decision() -> dict[str, Any]:
    decision = read_json(ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_CONTRACT_DECISION_LEDGER_2026-05-09.json")
    failures = []
    if decision.get("decision") != DECISION:
        failures.append({"decision": decision.get("decision")})
    if decision.get("status") != "PASS":
        failures.append({"status": decision.get("status")})
    if decision.get("decision_scope") != "future_source_control_routing_only":
        failures.append({"decision_scope": decision.get("decision_scope")})
    answers = {item["question_id"]: item for item in decision.get("audit_question_answers", [])}
    for qid in [f"AQ-{idx:03d}" for idx in range(1, 10)]:
        if qid not in answers:
            failures.append({"missing_audit_question": qid})
    closed = [
        item
        for item in decision.get("route_decisions", [])
        if item.get("route") == "NOFILL_CAT_V2_QUANTITATIVE_RESULT_LANE"
        and item.get("decision") == "REJECT_FOR_THIS_LANE_AND_KEEP_CLOSED"
    ]
    if not closed:
        failures.append({"closed_quantitative_result_lane": False})
    return {"failures": failures, "status": "PASS" if not failures else "FAIL"}


def verify_schema_review() -> dict[str, Any]:
    review = read_json(ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_SCHEMA_FIELD_REVIEW_2026-05-09.json")
    failures = []
    if review.get("status") != "PASS":
        failures.append({"status": review.get("status")})
    if review.get("field_count") != 46:
        failures.append({"field_count": review.get("field_count")})
    if review.get("missing_required_families"):
        failures.append({"missing_required_families": review.get("missing_required_families")})
    if review.get("forbidden_schema_field_names"):
        failures.append({"forbidden_schema_field_names": review.get("forbidden_schema_field_names")})
    families = set(review.get("family_counts", {}))
    missing_families = sorted(set(REQUIRED_FIELD_FAMILIES) - families)
    if missing_families:
        failures.append({"missing_family_counts": missing_families})
    failed_fields = [item for item in review.get("field_reviews", []) if item.get("status") != "PASS"]
    if failed_fields:
        failures.append({"failed_fields": failed_fields})
    return {"failures": failures, "status": "PASS" if not failures else "FAIL"}


def verify_duplicate_review() -> dict[str, Any]:
    review = read_json(ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_DUPLICATE_DENOMINATOR_REVIEW_2026-05-09.json")
    failures = []
    if review.get("status") != "PASS":
        failures.append({"status": review.get("status")})
    if review.get("duplicate_posture") != EXPECTED_DUPLICATE_POSTURE:
        failures.append({"duplicate_posture": review.get("duplicate_posture")})
    if review.get("valid_example_errors"):
        failures.append({"valid_example_errors": review.get("valid_example_errors")})
    invalid_failures = [item for item in review.get("invalid_case_results", []) if item.get("status") != "PASS"]
    if invalid_failures:
        failures.append({"invalid_case_failures": invalid_failures})
    if not review.get("invalid_case_results"):
        failures.append({"invalid_case_results": "missing"})
    return {"failures": failures, "status": "PASS" if not failures else "FAIL"}


def verify_noleak_blocker_review() -> dict[str, Any]:
    review = read_json(ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_NOLEAK_AND_BLOCKER_REVIEW_2026-05-09.json")
    failures = []
    if review.get("status") != "PASS":
        failures.append({"status": review.get("status")})
    if review.get("blocker_total") != 8:
        failures.append({"blocker_total": review.get("blocker_total")})
    if review.get("reject_total") != 65:
        failures.append({"reject_total": review.get("reject_total")})
    if review.get("row_boundary_violations"):
        failures.append({"row_boundary_violations": review.get("row_boundary_violations")})
    if review.get("accepted_labels_input_only") is not True:
        failures.append({"accepted_labels_input_only": review.get("accepted_labels_input_only")})
    if review.get("blockers_and_rejects_outside_labels_denominators_result_validation_promotion") is not True:
        failures.append({"blockers_rejects_boundary": False})
    if review.get("source_access_lane_decision") != "CAN_RUN_FROM_CONTRACT_AS_WRITTEN_FOR_SOURCE_CONTROL_ROUTING_ONLY":
        failures.append({"source_access_lane_decision": review.get("source_access_lane_decision")})
    return {"failures": failures, "status": "PASS" if not failures else "FAIL"}


def verify_capture_backlog_review() -> dict[str, Any]:
    review = read_json(ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_CAPTURE_BACKLOG_REVIEW_2026-05-09.json")
    failures = []
    if review.get("status") != "PASS":
        failures.append({"status": review.get("status")})
    if review.get("live_wiring_authorized_by_this_audit") is not False:
        failures.append({"live_wiring_authorized_by_this_audit": review.get("live_wiring_authorized_by_this_audit")})
    if review.get("missing_topic_fields"):
        failures.append({"missing_topic_fields": review.get("missing_topic_fields")})
    failed_items = [item for item in review.get("item_reviews", []) if item.get("status") != "PASS"]
    if failed_items:
        failures.append({"failed_items": failed_items})
    return {"failures": failures, "status": "PASS" if not failures else "FAIL"}


def verify_completion_audit() -> dict[str, Any]:
    audit = read_json(ROUTE_DIR / "G12_NOFILL_PENDING_SOURCE_COMPLETION_AUDIT_2026-05-09.json")
    failures = []
    if audit.get("completion_status") not in {
        "BUILT_PENDING_VERIFIER_AND_FOCUSED_TESTS",
        "VERIFIED_BY_G12_PENDING_SOURCE_CONTRACT_AUDIT_VERIFIER",
    }:
        failures.append({"completion_status": audit.get("completion_status")})
    missing_outputs = [name for name in audit.get("required_output_files", []) if not (ROUTE_DIR / name).exists()]
    if missing_outputs:
        failures.append({"missing_outputs": missing_outputs})
    fail_items = [item for item in audit.get("prompt_to_artifact_checklist", []) if item.get("status") == "FAIL"]
    if fail_items:
        failures.append({"checklist_fail_items": fail_items})
    return {"failures": failures, "status": "PASS" if not failures else "FAIL"}


def run_focused_pytest() -> dict[str, Any]:
    if os.environ.get("G12_PENDING_SOURCE_AUDIT_SKIP_NESTED_PYTEST") == "1":
        return {"status": "SKIPPED", "reason": "G12_PENDING_SOURCE_AUDIT_SKIP_NESTED_PYTEST=1"}
    env = dict(os.environ)
    env["G12_PENDING_SOURCE_AUDIT_SKIP_NESTED_PYTEST"] = "1"
    proc = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            str(ROUTE_DIR / "test_g12_nofill_pending_source_contract_audit_2026_05_09.py"),
            "-q",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=env,
    )
    return {
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-3000:],
        "stderr_tail": proc.stderr[-3000:],
    }


def write_completion(verification: dict[str, Any]) -> None:
    builder_path = ROUTE_DIR / "build_g12_nofill_pending_source_contract_audit_2026_05_09.py"
    spec = importlib.util.spec_from_file_location("g12_pending_source_audit_builder", builder_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load audit builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.write_completion_audit(
        status="VERIFIED_BY_G12_PENDING_SOURCE_CONTRACT_AUDIT_VERIFIER",
        verification=verification,
    )


def verify_audit(run_pytest: bool = True, write_audit: bool = True) -> dict[str, Any]:
    py_compile = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            str(ROUTE_DIR / "build_g12_nofill_pending_source_contract_audit_2026_05_09.py"),
            str(ROUTE_DIR / "verify_g12_nofill_pending_source_contract_audit_2026_05_09.py"),
            str(ROUTE_DIR / "test_g12_nofill_pending_source_contract_audit_2026_05_09.py"),
        ]
    )
    results = {
        "required_files": verify_required_files(),
        "generated_json_and_markdown": verify_generated_json_and_markdown(),
        "counts": verify_counts(),
        "decision": verify_decision(),
        "schema_review": verify_schema_review(),
        "duplicate_review": verify_duplicate_review(),
        "noleak_blocker_review": verify_noleak_blocker_review(),
        "capture_backlog_review": verify_capture_backlog_review(),
        "completion_audit": verify_completion_audit(),
        "py_compile": {"status": "PASS" if py_compile["returncode"] == 0 else "FAIL", **py_compile},
        "focused_pytest": run_focused_pytest() if run_pytest else {"status": "SKIPPED", "reason": "run_pytest=False"},
        "live_surface_diff": live_surface_check(),
    }
    status = "PASS" if all(item.get("status") in {"PASS", "SKIPPED"} for item in results.values()) else "FAIL"
    verification = {
        "artifact_family": "G12_NOFILL_PENDING_SOURCE_CONTRACT_AUDIT_VERIFICATION",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "verification_status": {"status": status},
        "can_mark_goal_complete": status == "PASS",
        "results": results,
    }
    if write_audit and status == "PASS":
        write_completion(verification)
    return verification


def main() -> int:
    report = verify_audit(run_pytest=True, write_audit=True)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["verification_status"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
