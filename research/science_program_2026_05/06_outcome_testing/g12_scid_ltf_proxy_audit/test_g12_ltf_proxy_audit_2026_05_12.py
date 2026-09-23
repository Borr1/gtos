"""Focused tests for the G12 SCID LTF/orderflow/proxy source-expansion audit."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent


def load_module(name: str, file_name: str):
    spec = importlib.util.spec_from_file_location(name, ROUTE_DIR / file_name)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_module(
    "g12_ltf_proxy_builder",
    "build_g12_ltf_proxy_audit_2026_05_12.py",
)
verifier = load_module(
    "g12_ltf_proxy_verifier",
    "verify_g12_ltf_proxy_audit_2026_05_12.py",
)


def test_recomputes_3014_candidate_boundary_and_ten_capture_groups():
    src = builder.load_sources()
    audit = builder.audit_candidate_boundary_and_capture_groups(src)

    summary = audit["candidate_summary_recomputed"]
    assert summary["candidate_rows"] == 3014
    assert summary["unique_candidate_input_row_ids"] == 3014
    assert summary["unique_duplicate_proxy_denominator_keys"] == 3014
    assert audit["ten_capture_groups_recomputed_from_reconciliation"] == builder.EXPECTED_CAPTURE_GROUPS
    assert audit["candidate_boundary_capture_groups_ok"] is True


def test_inventory_hash_deferrals_are_exact_and_rehash_cleanly():
    src = builder.load_sources()
    audit = builder.audit_source_inventory_hash_deferral(src)

    assert audit["source_inventory_count_recomputed"] == 844
    assert audit["hash_status_counts_recomputed"] == dict(sorted(builder.EXPECTED_HASH_STATUS_COUNTS.items()))
    assert audit["missing_hash_or_deferral_count"] == 0
    assert audit["hash_mismatch_count"] == 0
    assert audit["raw_market_blob_commits_added"] == 0
    assert audit["forbidden_broker_account_order_history_deal_position_sources_consumed"] == 0
    assert audit["source_inventory_hash_deferral_ok"] is True


def test_ladder_and_matrices_cover_roots_groups_and_source_counts():
    src = builder.load_sources()
    ladder = builder.audit_acquisition_ladder(src)
    coverage = builder.audit_coverage_matrices(src)

    assert ladder["searched_root_count_recomputed"] == 14
    assert ladder["selected_source_count_sum_recomputed"] == 844
    assert ladder["searched_beyond_current_worktree"] is True
    assert ladder["acquisition_ladder_saturation_ok"] is True
    assert coverage["missing_candidate_groups"] == []
    assert coverage["matrix_source_count_mismatches"] == []
    assert coverage["result_denominator_opened"] is False
    assert coverage["coverage_matrices_ok"] is True


def test_proxy_context_labels_and_approval_gates_are_strict():
    src = builder.load_sources()
    audit = builder.audit_proxy_validity_approval_asof(src)

    assert audit["all_proxy_rows_context_only"] is True
    assert audit["broker_native_cfd_truth_claims"] == 0
    assert audit["proxy_label_failures"] == []
    assert set(audit["approval_gate_ids"]) == builder.EXPECTED_APPROVAL_GATES
    assert audit["unresolved_vague_blockers"] == []
    assert audit["duplicate_policy"]["candidate_input_row_id_expected_unique"] == 3014
    assert audit["duplicate_policy"]["duplicate_proxy_denominator_key_expected_unique"] == 3014
    assert audit["proxy_validity_approval_asof_ok"] is True


def test_build_accepts_without_opening_forbidden_surfaces():
    result = builder.build(write=False, closeout=False)

    assert result["terminal_decision"] == builder.TERMINAL_ACCEPT
    assert result["candidate_rows"] == 3014
    assert result["source_inventory_count"] == 844


def test_verifier_accepts_generated_artifacts_after_builder_run():
    result = verifier.verify(write=False, mark_focused_tests_ok=False)

    assert result["ok"] is True
    assert result["failures"] == []
    assert result["terminal_decision"] == verifier.TERMINAL_ACCEPT
    assert result["candidate_rows_verified"] == 3014
