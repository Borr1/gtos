"""Standalone verifier for the SCID implementation design package."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-12"
ROUTE_DIR = Path(__file__).resolve().parent
BUILDER_PATH = ROUTE_DIR / "build_scid_forward_capture_implementation_design_package_2026_05_12.py"
PYTEST_XML = ROUTE_DIR / f"SCID_FC_IMPL_DESIGN_PYTEST_RESULT_{DATE}.xml"


def load_builder():
    spec = importlib.util.spec_from_file_location("scid_impl_design_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load builder from {BUILDER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_builder()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(stable_json(payload), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def find_repo_root() -> Path:
    cur = ROUTE_DIR
    for parent in [cur, *cur.parents]:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not locate repository root")


def parse_pytest_xml() -> dict[str, Any]:
    if not PYTEST_XML.exists():
        return {
            "status": "not_observed",
            "path": PYTEST_XML.relative_to(ROUTE_DIR).as_posix(),
            "tests": None,
            "failures": None,
            "errors": None,
            "skipped": None,
        }
    root = ET.parse(PYTEST_XML).getroot()
    if root.tag == "testsuite":
        tests = int(root.attrib.get("tests", 0))
        failures = int(root.attrib.get("failures", 0))
        errors = int(root.attrib.get("errors", 0))
        skipped = int(root.attrib.get("skipped", 0))
    else:
        tests = sum(int(node.attrib.get("tests", 0)) for node in root.findall("testsuite"))
        failures = sum(int(node.attrib.get("failures", 0)) for node in root.findall("testsuite"))
        errors = sum(int(node.attrib.get("errors", 0)) for node in root.findall("testsuite"))
        skipped = sum(int(node.attrib.get("skipped", 0)) for node in root.findall("testsuite"))
    return {
        "status": "passed" if tests > 0 and failures == 0 and errors == 0 else "failed",
        "path": PYTEST_XML.relative_to(ROUTE_DIR).as_posix(),
        "tests": tests,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
    }


def route_relative(path: Path) -> str:
    return path.relative_to(ROUTE_DIR).as_posix()


def check_git_scope(failures: list[str], notes: list[str]) -> dict[str, Any]:
    repo_root = find_repo_root()
    result = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        failures.append(f"git status failed: {result.stderr.strip()}")
        return {"repo_root": str(repo_root), "status_lines": [], "disallowed": []}

    route_prefix = ROUTE_DIR.relative_to(repo_root).as_posix() + "/"
    ignored_research_prefixes = {
        "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package/"
    }
    allowed_exact = {".context/LIVE_STATE.md"}
    status_lines = [line for line in result.stdout.splitlines() if line.strip()]
    disallowed: list[str] = []
    ignored_research: list[str] = []
    for line in status_lines:
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        path = path.strip('"').replace("\\", "/")
        if path.startswith(route_prefix):
            continue
        if any(path.startswith(prefix) for prefix in ignored_research_prefixes):
            ignored_research.append(path)
            continue
        if path in allowed_exact:
            notes.append(f"Allowed generated context refresh present: {path}")
            continue
        disallowed.append(path)

    if disallowed:
        failures.append(f"Disallowed working-tree changes outside research route: {disallowed}")
    if ignored_research:
        notes.append(
            "Ignored sibling research-only untracked files outside this package: "
            + ", ".join(ignored_research)
        )
    return {
        "repo_root": str(repo_root),
        "status_lines": status_lines,
        "disallowed": disallowed,
        "ignored_research": ignored_research,
    }


def verify_package(write_result: bool = True) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []

    expected_names = {row["capture_group"] for row in builder.CAPTURE_GROUPS}
    if len(expected_names) != 10:
        failures.append(f"Builder has {len(expected_names)} unique capture groups, expected 10")

    required_artifacts = [
        f"SCID_FC_IMPL_DESIGN_CONTEXT_ANCHOR_{DATE}.json",
        f"SCID_FC_IMPL_DESIGN_G12_G0_RECONCILIATION_{DATE}.json",
        f"SCID_FC_IMPL_DESIGN_CAPTURE_GROUP_LEDGER_{DATE}.json",
        f"SCID_FC_IMPL_DESIGN_INSERTION_POINT_LEDGER_{DATE}.json",
        f"SCID_FC_IMPL_DESIGN_PROPOSED_PATCH_PLAN_{DATE}.json",
        f"SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_{DATE}.json",
        f"SCID_FC_IMPL_DESIGN_OWNER_APPROVAL_RESTART_ROLLBACK_GATE_DOSSIER_{DATE}.json",
        f"SCID_FC_IMPL_DESIGN_SEQUENCING_LEDGER_{DATE}.json",
        f"SCID_FC_IMPL_DESIGN_SATURATION_SELF_REDTEAM_LEDGER_{DATE}.json",
        f"SCID_FC_IMPL_DESIGN_G12_AUDIT_PROMPT_{DATE}.md",
        f"SCID_FC_IMPL_DESIGN_G12_AUDIT_STARTER_{DATE}.txt",
        f"SCID_FC_IMPL_DESIGN_OUTPUT_MANIFEST_{DATE}.json",
        f"SCID_FC_IMPL_DESIGN_COMPLETION_AUDIT_{DATE}.json",
        f"SCID_FC_IMPL_DESIGN_CLOSEOUT_VERIFICATION_{DATE}.json",
    ]
    for name in required_artifacts:
        if not (ROUTE_DIR / name).exists():
            failures.append(f"Missing required artifact: {name}")

    ledger_path = ROUTE_DIR / f"SCID_FC_IMPL_DESIGN_CAPTURE_GROUP_LEDGER_{DATE}.json"
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        groups = ledger.get("capture_groups", [])
        names = {row.get("capture_group") for row in groups}
        if names != expected_names:
            failures.append(f"Capture group names mismatch: {sorted(names)} != {sorted(expected_names)}")
        if ledger.get("candidate_rows_expected") != builder.CANDIDATE_ROWS_EXPECTED:
            failures.append("Candidate boundary mismatch in capture group ledger")
        required_group_keys = {
            "source_contract",
            "source_asof_rule",
            "no_leak_rule",
            "redaction_rule",
            "fail_closed_behavior",
            "duplicate_policy",
            "rollback_plan",
            "test_plan",
            "g12_acceptance_criteria",
            "proposed_patch_artifact",
        }
        for row in groups:
            missing = sorted(required_group_keys - set(row))
            if missing:
                failures.append(f"{row.get('capture_group')} missing group keys: {missing}")
            for key in required_group_keys:
                if not row.get(key):
                    failures.append(f"{row.get('capture_group')} has empty required key: {key}")
    else:
        groups = []

    for json_path in sorted(ROUTE_DIR.glob("SCID_FC_IMPL_DESIGN_*.json")):
        data = json.loads(json_path.read_text(encoding="utf-8"))
        safe_flags = data.get("safe_flags")
        if not safe_flags:
            failures.append(f"{json_path.name} missing safe_flags")
            continue
        expected_false = [
            "validation_safe",
            "outcome_review_opened",
            "live_effect",
            "broker_or_account_evidence_opened",
            "ai_api_call_opened",
            "paid_vendor_call_opened",
            "raw_blob_capture_opened",
            "result_scoring_opened",
            "performance_claim_opened",
            "prompt_change_opened",
            "config_change_opened",
            "risk_logic_change_opened",
            "execution_logic_change_opened",
            "canary_or_selector_change_opened",
        ]
        if safe_flags.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append(f"{json_path.name} has wrong promotion_verdict")
        for key in expected_false:
            if safe_flags.get(key) is not False:
                failures.append(f"{json_path.name} safe flag {key} is not false")

    patch_dir = ROUTE_DIR / "proposed_patches"
    patch_files = sorted(patch_dir.glob("*.patch.md"))
    if len(patch_files) < 3:
        failures.append("Expected at least three proposed patch artifacts")
    for patch_file in patch_files:
        text = patch_file.read_text(encoding="utf-8")
        for marker in ["PROPOSED ONLY - DO NOT APPLY IN THIS ROUTE", "NO_PRODUCTION_EDIT_IN_THIS_ROUTE"]:
            if marker not in text:
                failures.append(f"{route_relative(patch_file)} missing marker: {marker}")

    forbidden_terms = ["actual_r", "synthetic_path_r", "slippage_price", "mt5_order_ticket"]
    redaction_path = ROUTE_DIR / f"SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_{DATE}.json"
    if redaction_path.exists():
        redaction = json.loads(redaction_path.read_text(encoding="utf-8"))
        forbidden_list = redaction.get("forbidden_fields", [])
        for term in forbidden_terms:
            if term not in forbidden_list:
                failures.append(f"Redaction plan missing forbidden lifecycle/result term: {term}")

    git_scope = check_git_scope(failures, notes)
    pytest_status = parse_pytest_xml()

    ok = not failures
    can_mark_goal_complete = ok and pytest_status["status"] == "passed"
    if pytest_status["status"] == "not_observed":
        warnings.append("Focused pytest JUnit result not observed yet; completion audit remains not complete.")

    result = {
        "route_id": builder.ROUTE_ID,
        "evidence_class": builder.EVIDENCE_CLASS,
        "generated_at_utc": utc_now(),
        "safe_flags": builder.SAFE_FLAGS,
        "ok": ok,
        "can_mark_goal_complete": can_mark_goal_complete,
        "failures": failures,
        "warnings": warnings,
        "notes": notes,
        "candidate_rows_verified": builder.CANDIDATE_ROWS_EXPECTED,
        "capture_groups_verified": len(expected_names),
        "pytest_status": pytest_status,
        "git_scope": git_scope,
    }

    if write_result:
        write_json(ROUTE_DIR / f"SCID_FC_IMPL_DESIGN_VERIFICATION_RESULT_{DATE}.json", result)
        write_text(
            ROUTE_DIR / f"SCID_FC_IMPL_DESIGN_VERIFICATION_RESULT_{DATE}.md",
            builder.render_json_as_md("SCID FC Implementation Design Verification Result", result),
        )
        completion = {
            "route_id": builder.ROUTE_ID,
            "schema_version": builder.SCHEMA_VERSION,
            "generated_at_utc": utc_now(),
            "safe_flags": builder.SAFE_FLAGS,
            "artifact_type": "completion_audit",
            "can_mark_goal_complete": can_mark_goal_complete,
            "completion_status": "COMPLETE" if can_mark_goal_complete else "INCOMPLETE",
            "verifier_ok": ok,
            "focused_tests_status": pytest_status,
            "failures": failures,
            "warnings": warnings,
            "candidate_rows_verified": builder.CANDIDATE_ROWS_EXPECTED,
            "capture_groups_verified": len(expected_names),
            "no_production_changes": not git_scope["disallowed"],
            "preserved_flags": {
                "NO_PROMOTION_VERDICT": True,
                "validation_safe_false": True,
                "outcome_review_opened_false": True,
                "live_effect_false": True,
            },
        }
        closeout = {
            "route_id": builder.ROUTE_ID,
            "schema_version": builder.SCHEMA_VERSION,
            "generated_at_utc": utc_now(),
            "safe_flags": builder.SAFE_FLAGS,
            "artifact_type": "closeout_verification",
            "closeout_status": "COMPLETE" if can_mark_goal_complete else "INCOMPLETE",
            "no_production_changes_verified": not git_scope["disallowed"],
            "restart_required_now": False,
            "owner_approval_required_before_runtime_wiring": True,
            "live_effect": False,
            "validation_safe": False,
            "outcome_review_opened": False,
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "verifier_result_path": f"SCID_FC_IMPL_DESIGN_VERIFICATION_RESULT_{DATE}.json",
            "pytest_result_path": pytest_status["path"],
        }
        write_json(ROUTE_DIR / f"SCID_FC_IMPL_DESIGN_COMPLETION_AUDIT_{DATE}.json", completion)
        write_text(
            ROUTE_DIR / f"SCID_FC_IMPL_DESIGN_COMPLETION_AUDIT_{DATE}.md",
            builder.render_json_as_md("SCID FC Implementation Design Completion Audit", completion),
        )
        write_json(ROUTE_DIR / f"SCID_FC_IMPL_DESIGN_CLOSEOUT_VERIFICATION_{DATE}.json", closeout)
        write_text(
            ROUTE_DIR / f"SCID_FC_IMPL_DESIGN_CLOSEOUT_VERIFICATION_{DATE}.md",
            builder.render_json_as_md("SCID FC Implementation Design Closeout Verification", closeout),
        )
        builder.refresh_output_manifest("verifier")

    return result


if __name__ == "__main__":
    verification = verify_package(write_result=True)
    print(stable_json(verification).rstrip())
    sys.exit(0 if verification["ok"] else 1)
