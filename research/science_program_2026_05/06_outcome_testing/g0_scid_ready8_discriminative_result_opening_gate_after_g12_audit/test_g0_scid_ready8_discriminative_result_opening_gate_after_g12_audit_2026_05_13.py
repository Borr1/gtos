"""Focused tests for the G0 READY8 discriminative result-opening gate."""

from __future__ import annotations

import json

from build_g0_scid_ready8_discriminative_result_opening_gate_after_g12_audit_2026_05_13 import (
    EXPECTED_ROWSET_ROWS,
    EXPECTED_ROWSET_SHA256,
    EXPECTED_SOURCE_CANDIDATES,
    NEXT_PROMPT,
    NEXT_STARTER,
    READY_CARDS,
    TERMINAL_OPEN,
    build_artifacts,
    out,
)
from verify_g0_scid_ready8_discriminative_result_opening_gate_after_g12_audit_2026_05_13 import verify


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_gate_recomputes_and_opens_next_prompt():
    result = build_artifacts(write_outputs=False)
    assert result["opened"] is True
    assert result["terminal_decision"] == TERMINAL_OPEN
    assert result["issues"] == []
    rowset = result["rowset"]
    assert rowset["rowset_sha256"] == EXPECTED_ROWSET_SHA256
    assert rowset["valid_json_rows"] == EXPECTED_ROWSET_ROWS
    assert rowset["candidate_input_row_id_count"] == EXPECTED_SOURCE_CANDIDATES
    assert rowset["duplicate_proxy_denominator_key_count"] == EXPECTED_SOURCE_CANDIDATES
    assert rowset["card_ids"] == READY_CARDS
    assert rowset["forbidden_row_field_hit_count"] == 0
    assert rowset["asof_violation_count"] == 0


def test_denominator_and_fail_closed_policy_are_frozen():
    denominator = read_json(out("DENOMINATOR_GATE_LEDGER"))
    assert denominator["role_counts"]["per_card_pass_row"] == 12100
    assert denominator["role_counts"]["per_card_contrast_row"] == 7530
    assert denominator["role_counts"]["per_card_non_applicable_row"] == 3685
    assert denominator["role_counts"]["per_card_fail_closed_row"] == 797
    assert denominator["denominator_integrity_checks"]["non_applicable_as_pass_count"] == 0
    assert denominator["denominator_integrity_checks"]["fail_closed_as_pass_count"] == 0
    assert denominator["adversarial_control_cards"]["ADV-001"].endswith("not an edge-card pass claim")
    assert denominator["adversarial_control_cards"]["ADV-003"].endswith("not an edge-card pass claim")


def test_next_prompt_binds_repaired_rowset_not_old_redundant_rowset():
    prompt = NEXT_PROMPT.read_text(encoding="utf-8")
    assert "SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_ONLY" in prompt
    assert EXPECTED_ROWSET_SHA256 in prompt
    assert "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl" in prompt
    assert "SCID_NOAPI_READY8_ROWSET_ROWS_2026-05-12.jsonl" not in prompt
    assert "7077a0f3fa3da2c854f2a0daab856d876992b927eb3228a161eb1cf02babb54d" not in prompt
    assert "neutral_close_to_close_return_m15_horizons_v1" in prompt
    assert "neutral_high_low_excursion_m15_horizons_v1" in prompt
    assert "must not be described as trading performance" in prompt

    starter = NEXT_STARTER.read_text(encoding="utf-8").strip()
    assert "\n" not in starter
    assert starter.startswith("/goal Follow the full controlling prompt")
    assert "3014 source candidates" in starter
    assert "24112 rowset rows" in starter
    assert EXPECTED_ROWSET_SHA256 in starter


def test_verifier_dry_run_passes_without_forbidden_surfaces():
    result = verify(write_result=False, mark_focused_tests_ok=True)
    assert result["ok"] is True
    assert result["failure_count"] == 0
    assert result["accepted_g12_verifier_ok"] is True
    assert result["opens_result_scoring"] is False
    assert result["opens_validation"] is False
    assert result["opens_ai_api"] is False
    assert result["opens_broker_account_order_history_deal_position_evidence"] is False
    assert result["live_effect"] is False
