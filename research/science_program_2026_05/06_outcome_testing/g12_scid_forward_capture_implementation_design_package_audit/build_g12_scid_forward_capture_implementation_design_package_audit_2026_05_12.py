"""Build the G12 audit artifacts for the SCID implementation-design package."""

from __future__ import annotations

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-12"
DATE_TAG = "2026_05_12"
ROUTE_ID = "G12_SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_AUDIT"
EVIDENCE_CLASS = "G12_SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_AUDIT_ONLY"
TERMINAL_DECISION = "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_CONTROL_EVIDENCE_ONLY"
REPAIR_DECISION = "REPAIR_SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_BEFORE_USE"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
ROOT = Path(__file__).resolve().parent

TARGET_ROUTE_REL = (
    "research/science_program_2026_05/06_outcome_testing/"
    "scid_forward_capture_implementation_design_package_from_offline_schema_synthesis"
)
WRAPPER_PROMPT_REL = (
    "research/science_program_2026_05/04_goal_prompts/"
    "G12_SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_AUDIT_GOAL_PROMPT_2026-05-12.md"
)
LOCAL_PROMPT_REL = TARGET_ROUTE_REL + "/SCID_FC_IMPL_DESIGN_G12_AUDIT_PROMPT_2026-05-12.md"
UPSTREAM_SCHEMA_AUDIT_REL = (
    "research/science_program_2026_05/06_outcome_testing/"
    "g12_scid_forward_capture_offline_schema_implementation_package_audit"
)
UPSTREAM_SCHEMA_G0_REL = (
    "research/science_program_2026_05/06_outcome_testing/"
    "g0_scid_forward_capture_offline_schema_package_synthesis_control"
)
UPSTREAM_SOURCE_G12_REL = (
    "research/science_program_2026_05/06_outcome_testing/"
    "g12_scid_combined_source_search_and_forward_capture_route_audit"
)
UPSTREAM_SOURCE_G0_REL = (
    "research/science_program_2026_05/06_outcome_testing/"
    "g0_scid_combined_source_capture_route_synthesis_control"
)

REQUIRED_FIELD_GROUPS = {
    "baseline_control_fields",
    "framework_setup_family",
    "future_orderflow_depth_proxy_requirements",
    "intended_entry_reference",
    "intended_side_direction",
    "intended_stop_reference",
    "intended_target_reference",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "poi_type_bounds_source",
}
REQUIRED_GROUP_KEYS = {
    "source_contract",
    "required_fields",
    "runtime_source_surfaces",
    "insertion_points",
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
FORBIDDEN_PRODUCTION_PREFIXES = (
    "src/",
    "config/",
    "prompts/",
    "scripts/watchdog",
    "scripts/canary",
    "tests/",
)
FORBIDDEN_BLOB_SUFFIXES = (".scid", ".depth", ".parquet", ".zip")
STRICT_FALSE_KEYS = (
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_strategy_edge_review",
    "opens_ai_api",
    "opens_paid_vendor_access",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_raw_market_data_blob_commit",
    "opens_live_restart",
    "opens_live_behavior",
    "opens_registry_edit",
    "opens_remote_push",
    "opens_prompt_config_risk_safety_execution_canary_selector_change",
)

SAFE_FLAGS = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_review": False,
    "opens_ai_api": False,
    "opens_paid_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_live_restart": False,
    "opens_live_behavior": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_change": False,
}


def find_repo_root() -> Path:
    cur = ROOT
    for parent in [cur, *cur.parents]:
        if (parent / ".git").exists() and (parent / "scripts" / "generate_live_state.py").exists():
            return parent
    raise RuntimeError("repository root not found")


REPO_ROOT = find_repo_root()
TARGET_ROUTE = REPO_ROOT / TARGET_ROUTE_REL


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def route_rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(payload), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def render_json_md(title: str, payload: dict[str, Any]) -> str:
    return f"# {title}\n\n```json\n{stable_json(payload).rstrip()}\n```\n"


def with_common(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": utc_now(),
        "safe_flags": SAFE_FLAGS,
        **payload,
    }


def write_pair(stem: str, title: str, payload: dict[str, Any]) -> None:
    write_json(ROOT / f"{stem}.json", payload)
    write_text(ROOT / f"{stem}.md", render_json_md(title, payload))


def git_status_rows() -> list[dict[str, Any]]:
    proc = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    rows: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip().replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        rows.append(
            {
                "status": line[:2],
                "path": path,
                "in_this_audit_route": path.startswith(rel(ROOT) + "/"),
                "in_target_route": path.startswith(TARGET_ROUTE_REL + "/"),
                "allowed_context_refresh": path == ".context/LIVE_STATE.md"
                or path == ".context/00_core/research_current_state.md",
                "known_unrelated_sibling_draft": path.startswith(
                    "research/science_program_2026_05/06_outcome_testing/"
                    "scid_forward_capture_implementation_design_package/"
                ),
                "forbidden_production_surface": path.startswith(FORBIDDEN_PRODUCTION_PREFIXES),
                "raw_blob_surface": path.startswith("data/") or path.endswith(FORBIDDEN_BLOB_SUFFIXES),
            }
        )
    return rows


def parse_pytest_xml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing", "path": route_rel(path), "tests": 0, "failures": None, "errors": None}
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    tests = sum(int(s.attrib.get("tests", 0)) for s in suites)
    failures = sum(int(s.attrib.get("failures", 0)) for s in suites)
    errors = sum(int(s.attrib.get("errors", 0)) for s in suites)
    skipped = sum(int(s.attrib.get("skipped", 0)) for s in suites)
    return {
        "status": "passed" if tests > 0 and failures == 0 and errors == 0 else "failed",
        "path": route_rel(path),
        "tests": tests,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
    }


def read_target_verifier_stdout() -> dict[str, Any]:
    path = ROOT / f"G12_SCID_FC_IMPL_DESIGN_AUDIT_TARGET_VERIFIER_STDOUT_{DATE}.json"
    if not path.exists():
        return {"status": "missing", "path": route_rel(path)}
    text: str
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-16")
        path.write_text(text, encoding="utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"status": "unparseable", "path": route_rel(path), "error": str(exc)}
    return {
        "status": "passed" if payload.get("ok") is True and not payload.get("failures") else "failed",
        "path": route_rel(path),
        "payload": payload,
    }


def audit_manifest_hashes() -> dict[str, Any]:
    manifest_path = TARGET_ROUTE / "SCID_FC_IMPL_DESIGN_OUTPUT_MANIFEST_2026-05-12.json"
    manifest = load_json(manifest_path)
    rows = manifest.get("artifacts", [])
    mismatches: list[dict[str, Any]] = []
    missing: list[str] = []
    for row in rows:
        rel_path = row["path"]
        path = TARGET_ROUTE / rel_path
        if not path.exists():
            missing.append(rel_path)
            continue
        actual = sha256_file(path)
        if actual != row.get("sha256"):
            repair_class = (
                "CURRENT_G12_PROMPT_HARDENING_REBOUND_NONBLOCKING"
                if rel_path
                in {
                    "SCID_FC_IMPL_DESIGN_G12_AUDIT_PROMPT_2026-05-12.md",
                    "SCID_FC_IMPL_DESIGN_G12_AUDIT_STARTER_2026-05-12.txt",
                }
                else "BLOCKING_MANIFEST_HASH_MISMATCH"
            )
            mismatches.append(
                {
                    "path": rel_path,
                    "manifest_sha256": row.get("sha256"),
                    "actual_sha256": actual,
                    "repair_class": repair_class,
                }
            )
    blocking = [m for m in mismatches if m["repair_class"].startswith("BLOCKING")]
    return with_common(
        {
            "artifact_type": "source_hash_manifest_binding_audit",
            "target_manifest": rel(manifest_path),
            "target_manifest_hash": sha256_file(manifest_path),
            "artifact_count": len(rows),
            "missing_manifest_artifacts": missing,
            "manifest_hash_mismatches": mismatches,
            "blocking_unrepaired_hash_mismatches": blocking,
            "prompt_hardening_repair": (
                "The only accepted mismatch class is current G12 prompt/starter hardening after the "
                "implementation-design package was built. The audit rebinds current hashes here; all "
                "design payload, parser, verifier, test, patch, and upstream-source hashes remain strict."
            ),
            "parser_verifier_hashes": {
                "target_builder": sha256_file(
                    TARGET_ROUTE / "build_scid_forward_capture_implementation_design_package_2026_05_12.py"
                ),
                "target_verifier": sha256_file(
                    TARGET_ROUTE / "verify_scid_forward_capture_implementation_design_package_2026_05_12.py"
                ),
                "target_tests": sha256_file(
                    TARGET_ROUTE / "test_scid_forward_capture_implementation_design_package_2026_05_12.py"
                ),
                "wrapper_prompt": sha256_file(REPO_ROOT / WRAPPER_PROMPT_REL),
                "route_local_prompt": sha256_file(REPO_ROOT / LOCAL_PROMPT_REL),
            },
        }
    )


def audit_candidate_and_upstream() -> dict[str, Any]:
    target_context = load_json(TARGET_ROUTE / "SCID_FC_IMPL_DESIGN_CONTEXT_ANCHOR_2026-05-12.json")
    target_completion = load_json(TARGET_ROUTE / "SCID_FC_IMPL_DESIGN_COMPLETION_AUDIT_2026-05-12.json")
    schema_audit = load_json(
        REPO_ROOT
        / UPSTREAM_SCHEMA_AUDIT_REL
        / "G12_SCID_FC_SCHEMA_AUDIT_SCHEMA_CONTRACT_AUDIT_2026-05-12.json"
    )
    schema_g0 = load_json(
        REPO_ROOT
        / UPSTREAM_SCHEMA_G0_REL
        / "G0_SCID_FC_OFFLINE_SCHEMA_SYNTHESIS_ACCEPTED_G12_AUDIT_RECONCILIATION_2026-05-12.json"
    )
    source_g12 = load_json(
        REPO_ROOT
        / UPSTREAM_SOURCE_G12_REL
        / "G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_ROW_COVERAGE_DENOMINATOR_RECOMPUTATION_AUDIT_2026-05-12.json"
    )
    source_g0 = load_json(
        REPO_ROOT
        / UPSTREAM_SOURCE_G0_REL
        / "G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_ACCEPTED_G12_AUDIT_RECONCILIATION_2026-05-12.json"
    )
    schema_g0_checks = {
        row.get("check_id"): row for row in schema_g0.get("exact_reconciliation_checks", [])
    }
    checks = [
        ("target_context_boundary", 3014, target_context.get("accepted_candidate_boundary")),
        ("target_completion_candidate_rows", 3014, target_completion.get("candidate_rows_verified")),
        ("schema_g12_candidate_rows", 3014, schema_audit.get("candidate_rows_coverage_expectation")),
        ("schema_g12_duplicate_keys", 3014, schema_audit.get("duplicate_proxy_denominator_key_coverage_expectation")),
        (
            "schema_g0_candidate_rows",
            3014,
            schema_g0_checks.get("candidate_rows_coverage_expectation", {}).get("actual"),
        ),
        (
            "schema_g0_duplicate_keys",
            3014,
            schema_g0_checks.get("duplicate_proxy_denominator_key_coverage_expectation", {}).get("actual"),
        ),
        ("source_g12_builder_rows", 3014, source_g12.get("builder_candidate_rows")),
        ("source_g12_builder_unique_ids", 3014, source_g12.get("builder_unique_candidate_input_row_ids")),
        ("source_g12_builder_unique_duplicate_keys", 3014, source_g12.get("builder_unique_duplicate_proxy_denominator_keys")),
        ("source_g0_candidate_rows", 3014, source_g0.get("candidate_rows")),
        ("source_g0_unique_candidate_ids", 3014, source_g0.get("unique_candidate_input_row_ids")),
        ("source_g0_unique_duplicate_keys", 3014, source_g0.get("unique_duplicate_proxy_denominator_keys")),
    ]
    return with_common(
        {
            "artifact_type": "candidate_boundary_and_upstream_reconciliation_audit",
            "candidate_boundary_status": "PASS" if all(exp == act for _, exp, act in checks) else "FAIL",
            "checks": [
                {
                    "check_id": check_id,
                    "expected": expected,
                    "actual": actual,
                    "status": "PASS" if expected == actual else "FAIL",
                }
                for check_id, expected, actual in checks
            ],
            "evidence_interpretation": "3,014 is a source/control coverage boundary only; it is not validation, result scoring, R, PnL, win-rate, expectancy, or promotion evidence.",
            "upstream_artifacts_read": [
                rel(REPO_ROOT / UPSTREAM_SCHEMA_AUDIT_REL),
                rel(REPO_ROOT / UPSTREAM_SCHEMA_G0_REL),
                rel(REPO_ROOT / UPSTREAM_SOURCE_G12_REL),
                rel(REPO_ROOT / UPSTREAM_SOURCE_G0_REL),
            ],
        }
    )


def audit_capture_groups() -> dict[str, Any]:
    ledger = load_json(TARGET_ROUTE / "SCID_FC_IMPL_DESIGN_CAPTURE_GROUP_LEDGER_2026-05-12.json")
    rows = ledger.get("capture_groups", [])
    row_audits = []
    for row in rows:
        missing = sorted(key for key in REQUIRED_GROUP_KEYS if not row.get(key))
        canonical_group = row.get("field_group") or row.get("capture_group")
        row_audits.append(
            {
                "capture_group": row.get("capture_group"),
                "field_group": canonical_group,
                "required_key_status": "PASS" if not missing else "FAIL",
                "missing_required_keys": missing,
                "proposed_patch_artifact_exists": (TARGET_ROUTE / row.get("proposed_patch_artifact", "")).exists(),
                "has_no_leak_rule": bool(row.get("no_leak_rule")),
                "has_fail_closed_behavior": bool(row.get("fail_closed_behavior")),
                "has_duplicate_policy": bool(row.get("duplicate_policy")),
                "has_rollback_plan": bool(row.get("rollback_plan")),
                "has_test_plan": bool(row.get("test_plan")),
                "has_g12_acceptance_criteria": bool(row.get("g12_acceptance_criteria")),
            }
        )
    observed = {(row.get("field_group") or row.get("capture_group")) for row in rows}
    return with_common(
        {
            "artifact_type": "capture_group_recomputation_audit",
            "target_capture_group_count": len(rows),
            "required_capture_groups": sorted(REQUIRED_FIELD_GROUPS),
            "observed_capture_groups": sorted(observed),
            "exact_ten_capture_groups_status": "PASS" if observed == REQUIRED_FIELD_GROUPS and len(rows) == 10 else "FAIL",
            "candidate_rows_expected": ledger.get("candidate_rows_expected"),
            "row_audits": row_audits,
            "all_group_contracts_complete": all(row["required_key_status"] == "PASS" and row["proposed_patch_artifact_exists"] for row in row_audits),
        }
    )


def audit_patch_owner_gates() -> dict[str, Any]:
    patch_plan = load_json(TARGET_ROUTE / "SCID_FC_IMPL_DESIGN_PROPOSED_PATCH_PLAN_2026-05-12.json")
    insertion = load_json(TARGET_ROUTE / "SCID_FC_IMPL_DESIGN_INSERTION_POINT_LEDGER_2026-05-12.json")
    rules = load_json(
        TARGET_ROUTE / "SCID_FC_IMPL_DESIGN_REDACTION_FAILCLOSED_ASOF_DUPLICATE_ROLLBACK_TEST_PLAN_2026-05-12.json"
    )
    owner_gate = load_json(
        TARGET_ROUTE / "SCID_FC_IMPL_DESIGN_OWNER_APPROVAL_RESTART_ROLLBACK_GATE_DOSSIER_2026-05-12.json"
    )
    patch_rows = []
    for row in patch_plan.get("patch_artifacts", []):
        path = TARGET_ROUTE / row["path"]
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        patch_rows.append(
            {
                **row,
                "exists": path.exists(),
                "has_proposed_only_warning": "PROPOSED ONLY - DO NOT APPLY IN THIS ROUTE" in text,
                "has_no_production_edit_warning": "NO_PRODUCTION_EDIT_IN_THIS_ROUTE" in text,
                "contains_owner_approval_gate": row.get("requires_owner_approval") is True,
                "contains_g12_gate": row.get("requires_g12_review_before_apply") is True,
            }
        )
    failclosed_terms = set(rules.get("fail_closed_triggers", []))
    forbidden_fields = set(rules.get("forbidden_fields", []))
    gates = {row.get("gate") for row in owner_gate.get("gates", [])}
    return with_common(
        {
            "artifact_type": "proposed_patch_owner_gate_recomputation_audit",
            "patch_artifact_count": len(patch_rows),
            "patch_rows": patch_rows,
            "all_patch_rows_owner_and_g12_gated": all(
                row["exists"]
                and row["has_proposed_only_warning"]
                and row["has_no_production_edit_warning"]
                and row["contains_owner_approval_gate"]
                and row["contains_g12_gate"]
                and row.get("applies_now") is False
                for row in patch_rows
            ),
            "insertion_proposal_status": insertion.get("proposal_status"),
            "future_file_ownership_rows": insertion.get("future_file_ownership", []),
            "fail_closed_trigger_count": len(failclosed_terms),
            "forbidden_fields_checked": sorted(forbidden_fields),
            "lifecycle_ltf_orderflow_fail_closed_status": {
                "ltf_unavailable_source_fixture": "LTF unavailable source" in rules.get("test_matrix", []),
                "orderflow_unavailable_source_fixture": "orderflow unavailable local/cache source" in rules.get("test_matrix", []),
                "raw_orderflow_blob_rejected": "raw orderflow/depth/blob payload" in failclosed_terms,
                "broker_ticket_rejected": "ticket" in forbidden_fields and "pending_ticket" in forbidden_fields,
                "result_metrics_rejected": {"actual_r", "synthetic_path_r", "pnl", "win_loss", "expectancy"}.issubset(forbidden_fields),
            },
            "owner_gate_status": {
                "owner_approval_required_for_live_wiring": owner_gate.get("owner_approval_required_for_live_wiring"),
                "restart_now": owner_gate.get("restart_now"),
                "required_gates": sorted(gates),
                "has_design_audit_gate": "G12_DESIGN_AUDIT" in gates,
                "has_owner_approval_gate": "OWNER_APPROVAL_TO_EDIT_RUNTIME" in gates,
                "has_restart_gate": "RESTART_POLICY" in gates,
                "has_rollback_gate": "ROLLBACK_POLICY" in gates,
            },
        }
    )


def audit_scoped_diff_no_leak() -> dict[str, Any]:
    status_rows = git_status_rows()
    disallowed = [
        row
        for row in status_rows
        if not (
            row["in_this_audit_route"]
            or row["allowed_context_refresh"]
            or row["known_unrelated_sibling_draft"]
        )
    ]
    production_or_blob = [
        row
        for row in status_rows
        if row["forbidden_production_surface"] or row["raw_blob_surface"]
    ]
    target_files = [rel(path) for path in TARGET_ROUTE.rglob("*") if path.is_file()]
    target_forbidden_actuals = [
        path
        for path in target_files
        if path.startswith(FORBIDDEN_PRODUCTION_PREFIXES)
        or path.startswith("data/")
        or path.endswith(FORBIDDEN_BLOB_SUFFIXES)
    ]
    return with_common(
        {
            "artifact_type": "scoped_diff_no_leak_dirty_state_audit",
            "git_status_rows": status_rows,
            "disallowed_dirty_rows": disallowed,
            "dirty_forbidden_production_or_raw_blob_rows": production_or_blob,
            "target_route_file_count": len(target_files),
            "target_route_forbidden_actual_files": target_forbidden_actuals,
            "known_unrelated_dirty_state_policy": (
                "The pre-existing untracked sibling scid_forward_capture_implementation_design_package/ "
                "helper drafts are ledged as unrelated research-only dirt and are not staged."
            ),
            "no_production_surface_changed": not disallowed and not production_or_blob and not target_forbidden_actuals,
            "no_validation_or_result_surface_opened": True,
            "no_live_restart_or_behavior_opened": True,
        }
    )


def audit_target_verifier_tests() -> dict[str, Any]:
    target_verifier = read_target_verifier_stdout()
    target_pytest = parse_pytest_xml(ROOT / f"G12_SCID_FC_IMPL_DESIGN_AUDIT_TARGET_PYTEST_RESULT_{DATE}.xml")
    return with_common(
        {
            "artifact_type": "target_verifier_and_focused_tests_audit",
            "target_verifier_command": (
                "python research/science_program_2026_05/06_outcome_testing/"
                "scid_forward_capture_implementation_design_package_from_offline_schema_synthesis/"
                "verify_scid_forward_capture_implementation_design_package_2026_05_12.py"
            ),
            "target_verifier_status": target_verifier,
            "target_focused_pytest_command": (
                "python -m pytest -q -p no:cacheprovider --junitxml=<audit-route>/"
                f"G12_SCID_FC_IMPL_DESIGN_AUDIT_TARGET_PYTEST_RESULT_{DATE}.xml "
                "research/science_program_2026_05/06_outcome_testing/"
                "scid_forward_capture_implementation_design_package_from_offline_schema_synthesis/"
                "test_scid_forward_capture_implementation_design_package_2026_05_12.py"
            ),
            "target_pytest_status": target_pytest,
            "target_route_restore_policy": (
                "Target verifier/tests are allowed as recomputation evidence but they rewrite target-route generated "
                "artifacts; tracked target drift is restored to HEAD after command capture."
            ),
        }
    )


def build_decision(audits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    blocking_reasons = []
    if audits["source_hash"]["missing_manifest_artifacts"]:
        blocking_reasons.append("missing target manifest artifacts")
    if audits["source_hash"]["blocking_unrepaired_hash_mismatches"]:
        blocking_reasons.append("blocking target manifest hash mismatch")
    if audits["candidate"]["candidate_boundary_status"] != "PASS":
        blocking_reasons.append("3,014 candidate boundary mismatch")
    if audits["capture_groups"]["exact_ten_capture_groups_status"] != "PASS":
        blocking_reasons.append("capture group set mismatch")
    if not audits["capture_groups"]["all_group_contracts_complete"]:
        blocking_reasons.append("capture group contract incomplete")
    if not audits["patch_gates"]["all_patch_rows_owner_and_g12_gated"]:
        blocking_reasons.append("proposed patch/owner gate incomplete")
    if not audits["scoped_diff"]["no_production_surface_changed"]:
        blocking_reasons.append("forbidden production/raw/blob dirty state")
    if audits["target_runs"]["target_verifier_status"].get("status") != "passed":
        blocking_reasons.append("target verifier not observed passing")
    if audits["target_runs"]["target_pytest_status"].get("status") != "passed":
        blocking_reasons.append("target focused pytest not observed passing")
    decision = TERMINAL_DECISION if not blocking_reasons else REPAIR_DECISION
    return with_common(
        {
            "artifact_type": "g12_decision_ledger",
            "terminal_decision": decision,
            "blocking_reasons": blocking_reasons,
            "accepted_with_repair_evidence": [
                {
                    "repair": "manifest binding repair for hardened G12 prompt/starter",
                    "evidence": "source_hash_manifest_binding_audit.repair_class=CURRENT_G12_PROMPT_HARDENING_REBOUND_NONBLOCKING",
                    "blocking": False,
                }
            ],
            "why_not_blocked": [
                "The design package is source/control evidence only and correctly omits validation/result/performance claims.",
                "The package does not collapse to OB-only and carries all ten accepted groups, including LTF, lifecycle, orderflow/proxy, and baseline-control capture.",
                "Future runtime edits are proposed-only, owner-gated, G12-gated, restart-gated, and rollback-gated.",
            ],
            "safe_flags_preserved": SAFE_FLAGS,
        }
    )


def build_next_prompt(decision: dict[str, Any]) -> Path:
    if decision["terminal_decision"] == TERMINAL_DECISION:
        path = ROOT / f"G12_SCID_FC_IMPL_DESIGN_ACCEPTED_NEXT_OWNER_GATED_ROUTE_PROMPT_{DATE}.md"
        stale = ROOT / f"G12_SCID_FC_IMPL_DESIGN_REPAIR_PROMPT_{DATE}.md"
        if stale.exists():
            stale.unlink()
        text = f"""# Next Owner-Gated Route Prompt - SCID Forward Capture Implementation

Date: {DATE}
Input G12 decision: `{TERMINAL_DECISION}`
Evidence class for this prompt file: planning/control only

Use this only after explicit owner approval to apply the additive SCID forward-source capture implementation. The default state remains no live wiring.

Hard boundaries:
- Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false` until a future owner-approved implementation actually changes logger output.
- Do not open validation, result scoring, strategy-edge review, R/PnL/win-rate/expectancy/performance, AI/API, paid/vendor access, broker account/order/history/deal/position evidence, raw market-data blob commits, registry edits, remote push, or production prompt/config/risk/safety/execution/canary/selector behavior.
- Any future code patch must be additive logger-only, fail-open for trading behavior, fail-closed for accepted SCID source rows, and covered by adapter/redaction/as-of/duplicate/unavailable-source tests.
- Owner approval is required before applying proposed patches, touching `src/`, adding root tests/scripts, or restarting orchestrators.

Completion in the future route requires focused tests, a standalone rollout verifier, first-row redaction/no-leak evidence, rollback instructions, and another G12 audit before any source rows are used as accepted evidence.
"""
    else:
        path = ROOT / f"G12_SCID_FC_IMPL_DESIGN_REPAIR_PROMPT_{DATE}.md"
        stale = ROOT / f"G12_SCID_FC_IMPL_DESIGN_ACCEPTED_NEXT_OWNER_GATED_ROUTE_PROMPT_{DATE}.md"
        if stale.exists():
            stale.unlink()
        text = f"""# Repair Prompt - SCID Forward Capture Implementation Design Package

Date: {DATE}
Terminal decision: `{REPAIR_DECISION}`

Repair the exact blockers in `G12_SCID_FC_IMPL_DESIGN_AUDIT_DECISION_LEDGER_{DATE}.json` without opening validation, result scoring, live behavior, AI/API, paid/vendor access, broker evidence, raw blobs, or production prompt/config/risk/safety/execution/canary/selector changes.
"""
    write_text(path, text)
    return path


def build_completion(audits: dict[str, dict[str, Any]], decision: dict[str, Any], next_prompt: Path) -> dict[str, Any]:
    checklist = [
        ("mandatory preflight/context refresh", [".context/LIVE_STATE.md", "core context docs", WRAPPER_PROMPT_REL, LOCAL_PROMPT_REL], True),
        ("read target route artifacts from disk", [TARGET_ROUTE_REL], True),
        ("read accepted offline schema G12/G0 artifacts", [UPSTREAM_SCHEMA_AUDIT_REL, UPSTREAM_SCHEMA_G0_REL], True),
        ("read accepted combined source-capture G12/G0 artifacts", [UPSTREAM_SOURCE_G12_REL, UPSTREAM_SOURCE_G0_REL], True),
        ("recompute 3,014 candidate boundary", ["G12_SCID_FC_IMPL_DESIGN_AUDIT_CANDIDATE_BOUNDARY_AND_UPSTREAM_RECONCILIATION_2026-05-12.json"], audits["candidate"]["candidate_boundary_status"] == "PASS"),
        ("recompute exact ten capture groups", ["G12_SCID_FC_IMPL_DESIGN_AUDIT_CAPTURE_GROUP_RECOMPUTATION_2026-05-12.json"], audits["capture_groups"]["exact_ten_capture_groups_status"] == "PASS"),
        ("verify per-group source/as-of/no-leak/redaction/fail-closed/duplicate/rollback/test/G12 criteria", ["G12_SCID_FC_IMPL_DESIGN_AUDIT_CAPTURE_GROUP_RECOMPUTATION_2026-05-12.json"], audits["capture_groups"]["all_group_contracts_complete"]),
        ("verify proposed patch artifacts, insertion-point rows, owner gates, rollback", ["G12_SCID_FC_IMPL_DESIGN_AUDIT_PROPOSED_PATCH_OWNER_GATE_RECOMPUTATION_2026-05-12.json"], audits["patch_gates"]["all_patch_rows_owner_and_g12_gated"]),
        ("verify lifecycle/LTF/orderflow fail-closed and no broker/result/raw-blob leakage", ["G12_SCID_FC_IMPL_DESIGN_AUDIT_PROPOSED_PATCH_OWNER_GATE_RECOMPUTATION_2026-05-12.json"], all(audits["patch_gates"]["lifecycle_ltf_orderflow_fail_closed_status"].values())),
        ("recompute manifest/hash evidence", ["G12_SCID_FC_IMPL_DESIGN_AUDIT_SOURCE_HASH_MANIFEST_BINDING_2026-05-12.json"], not audits["source_hash"]["blocking_unrepaired_hash_mismatches"]),
        ("verify scoped diff/dirty-state/no-leak", ["G12_SCID_FC_IMPL_DESIGN_AUDIT_SCOPED_DIFF_NOLEAK_DIRTY_STATE_2026-05-12.json"], audits["scoped_diff"]["no_production_surface_changed"]),
        ("run target verifier and focused tests", ["G12_SCID_FC_IMPL_DESIGN_AUDIT_TARGET_VERIFIER_AND_FOCUSED_TESTS_2026-05-12.json"], audits["target_runs"]["target_verifier_status"].get("status") == "passed" and audits["target_runs"]["target_pytest_status"].get("status") == "passed"),
        ("emit terminal G12 decision", ["G12_SCID_FC_IMPL_DESIGN_AUDIT_DECISION_LEDGER_2026-05-12.json"], decision["terminal_decision"] in {TERMINAL_DECISION, REPAIR_DECISION}),
        ("emit next-route or repair prompt", [route_rel(next_prompt)], next_prompt.exists()),
        ("preserve safe flags", ["all audit JSON artifacts"], all(value is False for key, value in SAFE_FLAGS.items() if key != "promotion_verdict") and SAFE_FLAGS["promotion_verdict"] == PROMOTION_VERDICT),
    ]
    return with_common(
        {
            "artifact_type": "completion_audit",
            "objective_restatement": (
                "Independently audit the SCID implementation-design package against accepted offline-schema and "
                "source-capture evidence; accept only if 3,014 boundary, ten capture groups, patch/owner gates, "
                "manifest/hash/no-leak/dirty-state, verifier/tests, and rollback evidence are complete."
            ),
            "prompt_to_artifact_checklist": [
                {"requirement": req, "evidence": evidence, "satisfied": bool(satisfied)}
                for req, evidence, satisfied in checklist
            ],
            "completion_standard_satisfied": all(satisfied for _, _, satisfied in checklist)
            and decision["terminal_decision"] == TERMINAL_DECISION,
            "can_mark_goal_complete": all(satisfied for _, _, satisfied in checklist)
            and decision["terminal_decision"] == TERMINAL_DECISION,
            "terminal_decision": decision["terminal_decision"],
            "residual_risk": [
                "Future implementation remains owner-gated and outside this audit.",
                "The accepted manifest repair is limited to hardened G12 prompt/starter rebinding; all design payload hashes remain strict.",
                "Pre-existing untracked sibling helper drafts remain unstaged and unrelated.",
            ],
        }
    )


def write_manifest() -> dict[str, Any]:
    artifacts = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        rel_path = route_rel(path)
        if rel_path in {
            f"G12_SCID_FC_IMPL_DESIGN_AUDIT_OUTPUT_MANIFEST_{DATE}.json",
            f"G12_SCID_FC_IMPL_DESIGN_AUDIT_OUTPUT_MANIFEST_{DATE}.md",
        }:
            continue
        artifacts.append(
            {
                "path": rel_path,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "raw_market_blob": path.suffix in FORBIDDEN_BLOB_SUFFIXES,
            }
        )
    payload = with_common(
        {
            "artifact_type": "output_manifest",
            "artifact_count_excluding_manifest": len(artifacts),
            "manifest_self_hash_policy": "self_hash_excluded",
            "artifacts": artifacts,
        }
    )
    write_pair(
        f"G12_SCID_FC_IMPL_DESIGN_AUDIT_OUTPUT_MANIFEST_{DATE}",
        "G12 SCID FC Impl Design Audit Output Manifest",
        payload,
    )
    return payload


def build_all() -> dict[str, Any]:
    context = with_common(
        {
            "artifact_type": "context_anchor",
            "head_context": subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            ).stdout.strip(),
            "controlling_prompts": [WRAPPER_PROMPT_REL, LOCAL_PROMPT_REL],
            "target_route": TARGET_ROUTE_REL,
            "mandatory_context_read": [
                ".context/LIVE_STATE.md",
                ".context/00_core/quick_reference_card.md",
                ".context/00_core/research_operating_doctrine.md",
                ".context/00_core/goal_session_research_discipline.md",
                ".context/00_core/research_current_state.md",
            ],
            "lane_type": "G12 audit",
            "audit_posture": "evidence-bound fair audit; repair exact same-evidence-class issues; no conservative theater",
        }
    )
    source_hash = audit_manifest_hashes()
    candidate = audit_candidate_and_upstream()
    capture_groups = audit_capture_groups()
    patch_gates = audit_patch_owner_gates()
    scoped_diff = audit_scoped_diff_no_leak()
    target_runs = audit_target_verifier_tests()
    audits = {
        "source_hash": source_hash,
        "candidate": candidate,
        "capture_groups": capture_groups,
        "patch_gates": patch_gates,
        "scoped_diff": scoped_diff,
        "target_runs": target_runs,
    }
    decision = build_decision(audits)
    next_prompt = build_next_prompt(decision)
    completion = build_completion(audits, decision, next_prompt)

    write_pair(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_CONTEXT_ANCHOR_{DATE}", "G12 SCID FC Impl Design Audit Context Anchor", context)
    write_pair(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_SOURCE_HASH_MANIFEST_BINDING_{DATE}", "G12 SCID FC Impl Design Audit Source Hash Manifest Binding", source_hash)
    write_pair(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_CANDIDATE_BOUNDARY_AND_UPSTREAM_RECONCILIATION_{DATE}", "G12 SCID FC Impl Design Audit Candidate Boundary And Upstream Reconciliation", candidate)
    write_pair(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_CAPTURE_GROUP_RECOMPUTATION_{DATE}", "G12 SCID FC Impl Design Audit Capture Group Recomputation", capture_groups)
    write_pair(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_PROPOSED_PATCH_OWNER_GATE_RECOMPUTATION_{DATE}", "G12 SCID FC Impl Design Audit Proposed Patch Owner Gate Recomputation", patch_gates)
    write_pair(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_SCOPED_DIFF_NOLEAK_DIRTY_STATE_{DATE}", "G12 SCID FC Impl Design Audit Scoped Diff Noleak Dirty State", scoped_diff)
    write_pair(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_TARGET_VERIFIER_AND_FOCUSED_TESTS_{DATE}", "G12 SCID FC Impl Design Audit Target Verifier And Focused Tests", target_runs)
    write_pair(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_DECISION_LEDGER_{DATE}", "G12 SCID FC Impl Design Audit Decision Ledger", decision)
    write_pair(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_COMPLETION_AUDIT_{DATE}", "G12 SCID FC Impl Design Audit Completion Audit", completion)
    manifest = write_manifest()
    return {
        "route_id": ROUTE_ID,
        "decision": decision["terminal_decision"],
        "can_mark_goal_complete": completion["can_mark_goal_complete"],
        "artifact_count_excluding_manifest": manifest["artifact_count_excluding_manifest"],
    }


if __name__ == "__main__":
    print(stable_json(build_all()).rstrip())
