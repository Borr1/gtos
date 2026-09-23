"""Focused tests for the G12 G0EXP R1 audit artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from verify_g12_g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_audit_2026_05_13 import (
    verify,
)


ROOT = Path(__file__).resolve().parents[4]
AUDIT_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-13"
PREFIX = "G12_G0EXP_R1"
TERMINAL_DECISION = "ACCEPT_AS_G12_G0EXP_R1_SOURCE_CONTROL_AUDIT_WITH_SAME_CLASS_HASH_REPAIR"


def load(stem: str):
    path = AUDIT_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_decision_repair_and_safe_flags():
    decision = load("DECISION_LEDGER")
    repair = load("REPAIR_LEDGER")

    assert decision["terminal_decision"] == TERMINAL_DECISION
    assert repair["terminal_repair_status"] == "CLOSED"
    assert repair["remaining_exact_source_access_export_capture_requirements"] == []
    assert decision["remaining_exact_source_access_export_capture_requirements"] == []
    assert decision["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False


def test_recomputation_and_quarantine():
    recomputation = load("RECOMPUTATION_EVIDENCE")
    decision = load("DECISION_LEDGER")

    assert recomputation["r1_output_manifest_mismatches_after_repair"] == []
    assert len(recomputation["required_upstream_input_hash_rows"]) >= 10
    assert all(row["exists"] for row in recomputation["required_upstream_input_hash_rows"])
    assert decision["quarantine_audit"]["r1_new_denominator_rows_added"] == 0
    assert decision["quarantine_audit"]["adjacent_overflow_entered_accepted_40"] == []
    assert decision["no_raw_blob_audit"]["raw_market_blob_artifact_count"] == 0


def test_verifier_evidence_and_completion_checklist():
    verifier = load("VERIFIER_TEST_EVIDENCE")
    completion = load("COMPLETION_AUDIT")

    assert verifier["r1_verifier_ok"] is True
    assert verifier["focused_tests_ok"] is True
    assert verifier["r1_final_verification_result"]["focused_tests_marked_ok"] is True
    assert completion["completion_standard_satisfied"] is True
    assert all(row["satisfied"] is True for row in completion["prompt_to_artifact_checklist"])


def test_standalone_audit_verifier_passes():
    result = verify(write_result=False)

    assert result["ok"], result["failures"]
