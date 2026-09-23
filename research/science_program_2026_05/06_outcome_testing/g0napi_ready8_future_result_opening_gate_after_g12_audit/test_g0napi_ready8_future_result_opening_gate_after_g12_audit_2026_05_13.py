"""Focused tests for the G0 ready-8 future result-opening gate."""

from __future__ import annotations

import json

from build_g0napi_ready8_future_result_opening_gate_after_g12_audit_2026_05_13 import (
    NEXT_RESULT_PROMPT,
    NEXT_RESULT_STARTER,
    TERMINAL_OPEN,
    build_artifacts,
    output_path,
)
from verify_g0napi_ready8_future_result_opening_gate_after_g12_audit_2026_05_13 import verify


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_recomputed_gate_opens_without_evidence_failures():
    result = build_artifacts(write_outputs=False)
    assert result["opened"] is True
    assert result["terminal_decision"] == TERMINAL_OPEN
    assert result["evidence_failures"] == []
    counts = result["reconciliation"]["rowset_counts"]
    assert counts["source_candidate_count_recomputed"] == 3014
    assert counts["ready_card_count_recomputed"] == 8
    assert counts["rowset_row_count_recomputed"] == 24112
    assert counts["row_hash_mismatch_count"] == 0
    assert counts["asof_violation_count"] == 0
    assert counts["forbidden_row_field_hit_count"] == 0


def test_repair_ledger_clears_g0_and_line_ending_followups():
    repair = read_json(output_path("SAME_EVIDENCE_CLASS_REPAIR_LEDGER"))
    statuses = {row["followup_id"]: row["terminal_status"] for row in repair["same_class_followups_pursued"]}
    assert statuses["READY8-G0-GATE-001"] == "CLEARED_BY_G0_GATE_OPEN_DECISION"
    assert statuses["READY8-EOL-HASH-001"] == "REPAIRED_AND_CLEARED"
    eol = next(row for row in repair["same_class_followups_pursued"] if row["followup_id"] == "READY8-EOL-HASH-001")
    assert eol["raw_rowset_sha256_after_repair"] == eol["manifest_rowset_sha256"]
    assert eol["lf_normalized_rowset_sha256_after_repair"] == eol["manifest_rowset_sha256"]
    assert eol["gitattributes_line_present"] is True


def test_future_result_prompt_is_broad_and_still_quarantined():
    prompt = NEXT_RESULT_PROMPT.read_text(encoding="utf-8")
    for phrase in [
        "SCID_NOAPI_READY8_QUARANTINED_TARGET_RESULT_PACKET_ONLY",
        "ADV-001",
        "UNC-004",
        "3,014",
        "24,112",
        "neutral_close_to_close_return_m15_horizons_v1",
        "neutral_high_low_excursion_m15_horizons_v1",
        "Adjacent families may be inventoried and routed as sidecars",
        "Do not compute or claim R, PnL, win rate, expectancy",
        "NO_PROMOTION_VERDICT",
        "validation_safe=false",
        "live_effect=false",
    ]:
        assert phrase in prompt
    starter = NEXT_RESULT_STARTER.read_text(encoding="utf-8").strip()
    assert starter.startswith("/goal Follow the full controlling prompt")
    assert "\n" not in starter
    assert "8 ready cards" in starter
    assert "3014 source candidates" in starter
    assert "24112 ready rows" in starter


def test_verifier_dry_run_passes_without_opening_forbidden_surfaces():
    result = verify(write_result=False, mark_focused_tests_ok=True)
    assert result["ok"] is True
    assert result["failure_count"] == 0
    assert result["opens_result_scoring"] is False
    assert result["opens_validation"] is False
    assert result["opens_ai_api"] is False
    assert result["opens_broker_account_order_history_deal_position_evidence"] is False
    assert result["live_effect"] is False
