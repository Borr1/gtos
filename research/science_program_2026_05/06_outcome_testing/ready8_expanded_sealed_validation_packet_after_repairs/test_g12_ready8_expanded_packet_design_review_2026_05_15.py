from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("verify_g12_ready8_expanded_packet_design_review_2026_05_15.py")
SPEC = importlib.util.spec_from_file_location("g12_verify", MODULE_PATH)
assert SPEC and SPEC.loader
g12_verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(g12_verify)


def _audit() -> dict:
    return g12_verify.build_audit(record_focused_tests=False, write=False)


def test_independent_g12_recomputation_has_no_errors() -> None:
    audit = _audit()
    assert audit["errors"] == []
    assert audit["decision"]["terminal_decision"] == g12_verify.TERMINAL_DECISION


def test_manifest_and_source_hashes_recompute_cleanly() -> None:
    recompute = _audit()["recomputation"]
    assert recompute["r7_output_manifest_audit"]["mismatch_count"] == 0
    assert recompute["r7_source_hash_audit"]["mismatch_count"] == 0
    assert recompute["prerequisite_acceptance_audit"]["source_hash_mismatch_count"] == 0


def test_failure_intelligence_is_preserved_not_erased() -> None:
    checks = _audit()["recomputation"]["failure_intelligence_checks"]
    assert checks["missing_required_branch_statuses"] == []
    assert checks["unknown_doctrine_classes"] == []
    assert checks["whole_intelligence_kill_count"] == 0
    assert checks["killed_bad_scope_count"] == 0
    assert checks["killed_status_counts"]["CONTROL_EXPLAINED_EDGE_CLAIM_KILLED_INTELLIGENCE_PRESERVED"] == 2608
    assert _audit()["recomputation"]["branch_status_counts"]["INVERSE_AVOID_FILTER_DESIGN_PRESERVED"] == 21


def test_packet_boundaries_remain_design_only_and_safe() -> None:
    recompute = _audit()["recomputation"]
    assert recompute["safe_boundary_scan"]["failure_count"] == 0
    assert recompute["packet_design_checks"]["non_design_only_packet_rows"] == []
    assert recompute["policy_checks"]["no_leak_status"] == "design_only_no_scoring_opened"
    assert recompute["policy_checks"]["adv_controls_are_not_edge_cards"] is True


def test_same_g12_manifest_repair_is_recorded_and_closed() -> None:
    repair = _audit()["discrepancy_repair"]
    assert repair["same_g12_issue_count_found"] == 4
    assert repair["same_g12_issue_count_repaired"] == 4
    assert repair["same_g12_repairable_items_remaining"] == 0
    assert repair["issues"][0]["actual_sha256"] == "862263fa1f46c20f0d1e4dac5ffcc75abd55c08211b2c3864c5f8764b9d87793"
    assert repair["issues"][1]["affected_source_count"] == 9
    assert repair["issues"][2]["affected_source_count"] == 2
    assert repair["issues"][3]["issue_id"] == "G12-R7-MANIFEST-002"
    assert repair["issues"][3]["issue_class"] == "parent_manifest_child_audit_artifact_ownership_drift"
    assert "parent manifest_hashes_match=true" in repair["issues"][3]["post_repair_verification"]


def test_completion_audit_covers_prompt_requirements() -> None:
    completion = _audit()["completion"]
    checklist = completion["prompt_to_artifact_checklist"]
    assert len(checklist) >= 10
    assert all(item["satisfied"] for item in checklist if item["requirement"] != "Emit completion audit, verifier/focused tests, output manifest, and exact decision")
    assert completion["same_g12_repairable_items_remaining"] == 0
    assert completion["terminal_blockers"] == []
