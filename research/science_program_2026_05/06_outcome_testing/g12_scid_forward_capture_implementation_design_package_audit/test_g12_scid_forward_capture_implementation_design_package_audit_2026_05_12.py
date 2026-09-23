from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATE = "2026-05-12"


def _json(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_candidate_boundary_recomputed_from_upstream_artifacts():
    payload = _json(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_CANDIDATE_BOUNDARY_AND_UPSTREAM_RECONCILIATION_{DATE}.json")
    assert payload["candidate_boundary_status"] == "PASS"
    for row in payload["checks"]:
        assert row["expected"] == 3014
        assert row["actual"] == 3014
        assert row["status"] == "PASS"
    assert "coverage boundary only" in payload["evidence_interpretation"]


def test_exact_ten_capture_groups_and_contract_keys():
    payload = _json(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_CAPTURE_GROUP_RECOMPUTATION_{DATE}.json")
    assert payload["exact_ten_capture_groups_status"] == "PASS"
    assert payload["target_capture_group_count"] == 10
    assert set(payload["required_capture_groups"]) == set(payload["observed_capture_groups"])
    assert payload["all_group_contracts_complete"] is True
    for row in payload["row_audits"]:
        assert row["required_key_status"] == "PASS"
        assert row["proposed_patch_artifact_exists"] is True
        assert row["has_no_leak_rule"] is True
        assert row["has_fail_closed_behavior"] is True


def test_manifest_repair_is_limited_to_current_g12_prompt_hardening():
    payload = _json(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_SOURCE_HASH_MANIFEST_BINDING_{DATE}.json")
    assert payload["missing_manifest_artifacts"] == []
    assert payload["blocking_unrepaired_hash_mismatches"] == []
    mismatches = payload["manifest_hash_mismatches"]
    assert mismatches
    assert {row["repair_class"] for row in mismatches} == {"CURRENT_G12_PROMPT_HARDENING_REBOUND_NONBLOCKING"}
    assert {"target_builder", "target_verifier", "target_tests", "wrapper_prompt", "route_local_prompt"} <= set(
        payload["parser_verifier_hashes"]
    )


def test_patch_owner_gate_and_no_leak_boundaries():
    payload = _json(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_PROPOSED_PATCH_OWNER_GATE_RECOMPUTATION_{DATE}.json")
    assert payload["patch_artifact_count"] == 3
    assert payload["all_patch_rows_owner_and_g12_gated"] is True
    assert all(payload["lifecycle_ltf_orderflow_fail_closed_status"].values())
    gate = payload["owner_gate_status"]
    assert gate["owner_approval_required_for_live_wiring"] is True
    assert gate["restart_now"] is False
    assert gate["has_design_audit_gate"] is True
    assert gate["has_owner_approval_gate"] is True
    assert gate["has_restart_gate"] is True
    assert gate["has_rollback_gate"] is True


def test_target_verifier_tests_and_terminal_decision_pass():
    runs = _json(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_TARGET_VERIFIER_AND_FOCUSED_TESTS_{DATE}.json")
    assert runs["target_verifier_status"]["status"] == "passed"
    assert runs["target_pytest_status"]["status"] == "passed"
    decision = _json(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_DECISION_LEDGER_{DATE}.json")
    assert decision["terminal_decision"] == "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_CONTROL_EVIDENCE_ONLY"
    assert decision["blocking_reasons"] == []


def test_completion_audit_maps_prompt_requirements():
    payload = _json(f"G12_SCID_FC_IMPL_DESIGN_AUDIT_COMPLETION_AUDIT_{DATE}.json")
    assert payload["completion_standard_satisfied"] is True
    assert payload["can_mark_goal_complete"] is True
    requirements = {row["requirement"]: row for row in payload["prompt_to_artifact_checklist"]}
    for required in [
        "mandatory preflight/context refresh",
        "recompute 3,014 candidate boundary",
        "recompute exact ten capture groups",
        "verify proposed patch artifacts, insertion-point rows, owner gates, rollback",
        "run target verifier and focused tests",
        "preserve safe flags",
    ]:
        assert requirements[required]["satisfied"] is True
