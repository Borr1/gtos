from __future__ import annotations

import json

import build_g12_cnr061_sidecar_reaudit_2026_05_08 as build


def load_artifact(name: str) -> dict:
    return json.loads(build.OUTPUTS[name].read_text(encoding="utf-8"))


ARTIFACTS = {
    "decision": load_artifact("decision_json"),
    "source": load_artifact("source_json"),
    "noleak": load_artifact("noleak_json"),
    "blocked": load_artifact("blocked_json"),
}


def test_decision_accepts_eight_input_only_rows() -> None:
    decision = ARTIFACTS["decision"]
    assert decision["decision"] == build.DECISION_ACCEPT
    assert decision["accepted_sidecar_row_count"] == 8
    assert decision["accepted_unique_record_id_count"] == 4
    assert decision["accepted_unique_duplicate_group_count"] == 2
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False


def test_source_hash_join_and_asof_checks_pass() -> None:
    source = ARTIFACTS["source"]
    assert source["audit_status"].startswith("PASS")
    assert source["row_join_summary"]["pass_count"] == 8
    assert source["row_join_summary"]["fail_count"] == 0
    assert source["quote_path_asof_summary"]["pass_count"] == 8
    assert source["quote_path_asof_summary"]["fail_count"] == 0
    assert source["sidecar_source_evidence_summary"]["mismatch_count"] == 0
    assert source["upstream_source_search_ledger_recompute"]["strict_row_or_control_source_mismatch_count"] == 0


def test_noleak_duplicate_policy_is_explicit() -> None:
    noleak = ARTIFACTS["noleak"]
    assert noleak["audit_status"] == "PASS"
    assert noleak["forbidden_packet_row_key_hits"] == []
    assert noleak["duplicate_summary"]["sidecar_row_count"] == 8
    assert noleak["duplicate_summary"]["unique_duplicate_group_count"] == 2
    assert noleak["duplicate_group_only_join_decision"]["decision"] == "REJECT_DUPLICATE_GROUP_ONLY_JOIN_AS_INSUFFICIENT_FOR_ROW_ACCEPTANCE"


def test_blocked_rows_are_exact_and_otr061_reason_is_input_gate() -> None:
    blocked = ARTIFACTS["blocked"]
    assert blocked["audit_status"] == "PASS_EXACT_94_BLOCKED_ROWS_EXCLUDED"
    assert blocked["exclusion_counts"]["cnr_source_e0e1_t0_rows"] == 102
    assert blocked["exclusion_counts"]["accepted_sidecar_rows"] == 8
    assert blocked["exclusion_counts"]["blocked_rows"] == 94
    assert blocked["overlap_checks"]["accepted_blocked_source_hash_overlap"] == []
    assert blocked["overlap_checks"]["accepted_blocked_record_id_overlap"] == []
    otr = blocked["otr061_recovery_block_status"]
    assert otr["matched_otr061_rows_in_blocked_set"] == 2
    assert otr["reason"] == "TARGET_ALREADY_PASSED_INPUT_GATE_NOT_MISSING_TICK_EVIDENCE"
    assert otr["all_otr061_rows_target_already_passed"] is True
