from __future__ import annotations

import json
from pathlib import Path

import verify_g12_scid_future_capture_blocked15_source_state_materialization_audit_2026_05_12 as verifier


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-12"
PREFIX = "G12_SCID_FC_BLOCKED15_AUDIT"
TERMINAL_ACCEPT = "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY"


def artifact(stem: str) -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE}.json"


def read_json(stem: str):
    return json.loads(artifact(stem).read_text(encoding="utf-8"))


def test_blocked15_recomputed_from_upstream_and_ten_capture_groups_visible():
    audit = read_json("BLOCKED15_RECOMPUTATION_AND_CAPTURE_GROUP_AUDIT")

    assert audit["ok"] is True
    assert audit["recomputed_blocked15_count"] == 15
    assert audit["all_ten_capture_groups_visible"] is True
    assert len(audit["accepted_capture_groups_recomputed"]) == 10
    assert audit["missing_field_mapping_failures"] == []


def test_recovered_rows_schema_redaction_and_source_state_boundary():
    audit = read_json("RECOVERED_ROW_SCHEMA_REDACTION_AUDIT")

    assert audit["ok"] is True
    assert audit["recovered_row_count"] == 1213
    assert audit["forbidden_row_key_hits"] == []
    assert audit["asof_failure_count"] == 0
    assert audit["rows_are_source_state_examples_only"] is True
    assert audit["accepted_40_result_denominator_closure_from_recovered_rows"] is False


def test_contracts_and_denominator_quarantine_remain_fail_closed():
    contract = read_json("PROSPECTIVE_CONTRACT_EXACTNESS_AUDIT")
    denominator = read_json("DENOMINATOR_QUARANTINE_AND_SAFE_FLAG_AUDIT")

    assert contract["ok"] is True
    assert contract["contract_count"] == 10
    assert contract["all_cards_remain_blocked_for_results"] is True
    assert denominator["ok"] is True
    assert denominator["accepted_40_denominator_unchanged"] is True
    assert denominator["accepted_denominator_count"] == 40
    assert denominator["target_manifest_raw_blob_artifacts"] == []


def test_search_saturation_and_target_verifier_tests_passed():
    search = read_json("SOURCE_SEARCH_SATURATION_AUDIT")
    rerun = read_json("TARGET_VERIFIER_TEST_RERUN_LEDGER")

    assert search["ok"] is True
    assert all(search["required_search_categories"].values())
    assert rerun["target_verifier_ok"] is True
    assert rerun["target_focused_tests_ok"] is True


def test_decision_accepts_only_control_evidence_and_verifier_passes():
    decision = read_json("DECISION_LEDGER")
    report = verifier.verify(write=False)

    assert decision["terminal_decision"] == TERMINAL_ACCEPT
    assert decision["terminal_blockers"] == []
    assert decision["accepted_g12_control_evidence_only"] is True
    assert decision["accepted_validation_execution"] is False
    assert decision["accepted_strategy_performance"] is False
    assert decision["accepted_promotion"] is False
    assert report["ok"] is True
