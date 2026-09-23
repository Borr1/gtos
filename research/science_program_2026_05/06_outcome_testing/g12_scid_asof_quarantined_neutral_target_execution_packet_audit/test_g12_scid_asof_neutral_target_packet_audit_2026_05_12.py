from __future__ import annotations

import json
import sys
from functools import cache
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROUTE_DIR))

import build_g12_scid_asof_neutral_target_packet_audit_2026_05_12 as builder


def load_json(name: str) -> dict:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


@cache
def build_once() -> dict:
    return builder.build_all()


def test_audit_accepts_only_control_evidence_after_full_recomputation() -> None:
    result = build_once()
    assert result["terminal_decision"] == builder.ACCEPT_DECISION
    assert result["terminal_statuses_recomputed"] == 3014 * 4 * 2
    assert result["target_row_hash_mismatch_count"] == 0
    completion = load_json(f"{builder.PREFIX}_COMPLETION_AUDIT_{builder.DATE_TAG}.json")
    assert completion["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert completion["validation_safe"] is False
    assert completion["outcome_review_opened"] is False
    assert completion["live_effect"] is False
    assert completion["terminal_decision"] == builder.ACCEPT_DECISION


def test_source_hash_binding_recomputes_inputs_and_scid_segments() -> None:
    build_once()
    source = load_json(f"{builder.PREFIX}_SOURCE_HASH_INPUT_BINDING_AUDIT_{builder.DATE_TAG}.json")
    assert source["all_input_artifact_hashes_match_target_binding"] is True
    assert source["candidate_rows_sha256_matches_manifest"] is True
    assert source["bar_rows_sha256_matches_manifest"] is True
    assert source["accepted_scid_segments_rehashed"] is True
    assert source["accepted_scid_segment_rehash_audit"]["segment_count"] == 9


def test_terminal_grid_row_hashes_and_not_computable_reasons_match() -> None:
    build_once()
    terminal = load_json(f"{builder.PREFIX}_TERMINAL_GRID_RECOMPUTATION_AUDIT_{builder.DATE_TAG}.json")
    row_target = load_json(f"{builder.PREFIX}_ROW_TARGET_RECOMPUTATION_AUDIT_{builder.DATE_TAG}.json")
    not_audit = load_json(f"{builder.PREFIX}_NOT_COMPUTABLE_REASON_AUDIT_{builder.DATE_TAG}.json")
    assert terminal["full_terminal_grid_pass"] is True
    assert terminal["recomputed_terminal_row_hash_digest"] == terminal["target_terminal_row_hash_digest"]
    assert row_target["full_row_hash_recomputation_pass"] is True
    assert row_target["target_row_hash_mismatch_count"] == 0
    assert row_target["descriptor_row_hash_mismatch_count"] == 0
    assert not_audit["reason_counts_match_target"] is True
    assert not_audit["not_computable_rows_have_target_values"] == 0


def test_aggregate_denominator_and_noleak_checks_pass() -> None:
    build_once()
    aggregate = load_json(f"{builder.PREFIX}_AGGREGATE_MATRIX_RECOMPUTATION_AUDIT_{builder.DATE_TAG}.json")
    denominator = load_json(f"{builder.PREFIX}_DUPLICATE_CONCENTRATION_DENOMINATOR_AUDIT_{builder.DATE_TAG}.json")
    noleak = load_json(f"{builder.PREFIX}_NOLEAK_EVIDENCE_CLASS_AUDIT_{builder.DATE_TAG}.json")
    assert aggregate["availability_summary_matches"] is True
    assert aggregate["aggregate_matrices_hash_match"] is True
    assert aggregate["partition_symbol_session_matrix_hash_match"] is True
    assert aggregate["positive_return_fraction_label_present_and_neutral"] is True
    assert denominator["all_denominator_checks_pass"] is True
    assert denominator["partition_counts"]["SEALED_VALIDATION_CANDIDATE_DESIGN"] == 2432
    assert denominator["partition_counts"]["STRESS_ROBUSTNESS_CANDIDATE_DESIGN"] == 582
    assert noleak["all_noleak_checks_pass"] is True
    assert noleak["checks"]["not_computable_rows_fail_closed_without_values"] is True


def test_next_g0_prompt_pack_and_decision_ledger_are_emitted() -> None:
    build_once()
    next_prompt = ROUTE_DIR / f"{builder.PREFIX}_NEXT_G0_SYNTHESIS_CONTROL_PROMPT_PACK_{builder.DATE_TAG}.md"
    assert next_prompt.exists()
    text = next_prompt.read_text(encoding="utf-8")
    assert "NO_PROMOTION_VERDICT" in text
    assert "validation_safe=false" in text
    decision = load_json(f"{builder.PREFIX}_DECISION_LEDGER_{builder.DATE_TAG}.json")
    assert decision["terminal_decision"] == builder.ACCEPT_DECISION
    assert decision["accepted_validation_execution"] is False
    assert decision["accepted_strategy_performance"] is False
