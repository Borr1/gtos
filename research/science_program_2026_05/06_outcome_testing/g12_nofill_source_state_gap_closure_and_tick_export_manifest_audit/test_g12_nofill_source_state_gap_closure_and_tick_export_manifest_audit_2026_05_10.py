"""Focused tests for the G12 NOFILL source-state gap closure audit."""

from __future__ import annotations

import json
from pathlib import Path

import build_g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit_2026_05_10 as builder
import verify_g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit_2026_05_10 as verifier


ROUTE_DIR = Path(__file__).resolve().parent


def _json(name: str) -> dict:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def test_terminal_decision_counts_and_flags() -> None:
    decision = _json(f"{builder.PREFIX}_DECISION_LEDGER_{builder.DATE}.json")
    counts = _json(f"{builder.PREFIX}_INDEPENDENT_COUNT_RECONCILIATION_{builder.DATE}.json")

    assert decision["terminal_decision"] == builder.TERMINAL_DECISION
    assert decision["exact_repair_blockers"] == []
    assert decision["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False

    recomputed = counts["recomputed_counts"]
    assert recomputed["admitted_source_bound_rows_from_g0_row_ledger"] == 2
    assert recomputed["blocker_rows_from_active_pursuit_rows"] == 37
    assert recomputed["reject_rows_from_g0_reject_rows"] == 9
    assert recomputed["duplicate_denominators_from_g0_duplicate_review"] == "2/2/2"
    assert recomputed["tick_export_rows"] == 31
    assert recomputed["contamination_embargo_rows"] == 17
    assert recomputed["recovered_source_state_count"] == 0
    assert recomputed["field_closure_rows"] == 55


def test_row_level_audits_close_required_denominators() -> None:
    pursuit = _json(f"{builder.PREFIX}_ACTIVE_PURSUIT_LADDER_AUDIT_{builder.DATE}.json")
    tick = _json(f"{builder.PREFIX}_TICK_EXPORT_MANIFEST_AUDIT_{builder.DATE}.json")
    contamination = _json(f"{builder.PREFIX}_CONTAMINATION_EMBARGO_EXCLUSION_AUDIT_{builder.DATE}.json")
    recovered = _json(f"{builder.PREFIX}_RECOVERED_SOURCE_STATE_NEGATIVE_EVIDENCE_AUDIT_{builder.DATE}.json")
    proof = _json(f"{builder.PREFIX}_NON_GENERATABLE_TRUTH_PROOF_AUDIT_{builder.DATE}.json")
    fields = _json(f"{builder.PREFIX}_FORWARD_CAPTURE_55_FIELD_CLOSURE_AUDIT_{builder.DATE}.json")

    assert pursuit["audit_status"] == "PASS"
    assert pursuit["row_count"] == 37
    assert all(row["audit_status"] == "PASS" for row in pursuit["rows"])
    assert tick["audit_status"] == "PASS"
    assert tick["tick_export_dependent_blocker_count"] == 31
    assert contamination["audit_status"] == "PASS"
    assert contamination["contamination_embargo_blocker_count"] == 17
    assert contamination["g0_reject_row_count"] == 9
    assert recovered["audit_status"] == "PASS"
    assert recovered["recovered_source_state_count"] == 0
    assert proof["audit_status"] == "PASS"
    assert proof["row_count"] == 37
    assert fields["audit_status"] == "PASS"
    assert fields["field_count"] == 55
    assert fields["field_names_match_runtime_contract"] is True


def test_owner_grouping_source_hash_noleak_and_next_prompt() -> None:
    hashes = _json(f"{builder.PREFIX}_TARGET_ARTIFACT_INVENTORY_SOURCE_HASH_AUDIT_{builder.DATE}.json")
    owner = _json(f"{builder.PREFIX}_OWNER_ACTION_EXACTNESS_AUDIT_{builder.DATE}.json")
    grouping = _json(f"{builder.PREFIX}_OWNER_EXPORT_REQUEST_GROUPING_AUDIT_{builder.DATE}.json")
    noleak = _json(f"{builder.PREFIX}_NOLEAK_FORBIDDEN_ROUTE_LIVE_SURFACE_AUDIT_{builder.DATE}.json")
    rerun = _json(f"{builder.PREFIX}_TARGET_VERIFIER_TEST_RERUN_LEDGER_{builder.DATE}.json")
    ranking = _json(f"{builder.PREFIX}_NEXT_ROUTE_RANKING_LEDGER_{builder.DATE}.json")

    assert hashes["audit_status"] == "PASS"
    assert hashes["strict_source_hash_mismatches"] == []
    assert all(row["exists"] and row["sha256"] for row in hashes["target_artifact_hashes"])
    assert owner["audit_status"] == "PASS"
    assert owner["owner_market_data_export_request_count"] == 22
    assert owner["forward_capture_request_count"] == 1
    assert owner["access_request_count"] == 1
    assert grouping["audit_status"] == "PASS"
    assert grouping["grouped_market_data_request_count"] == 22
    assert grouping["tick_export_dependent_blocker_count"] == 31
    assert grouping["candidate_coverage_ok"] is True
    assert grouping["actual_symbol_set"] == ["GBPJPY", "GBPUSD", "US30_cash", "USDJPY", "XAUUSD"]
    assert noleak["audit_status"] == "PASS"
    assert rerun["audit_status"] == "PASS"
    assert rerun["target_focused_tests"]["pre_g12_artifact_creation_rerun_returncode"] == 0
    assert ranking["ranked_next_routes"][0]["route_id"] == "NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE"
    assert (builder.REPO_ROOT / builder.NEXT_PROMPT_PATH).exists()


def test_completion_and_verifier_accept_route() -> None:
    completion = _json(f"{builder.PREFIX}_COMPLETION_AUDIT_{builder.DATE}.json")
    assert completion["completion_standard_satisfied"] is True
    assert completion["can_mark_goal_complete"] is True
    assert completion["missing_incomplete_or_weak_requirements"] == []

    result = verifier.verify()
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
    assert result["failures"] == []
