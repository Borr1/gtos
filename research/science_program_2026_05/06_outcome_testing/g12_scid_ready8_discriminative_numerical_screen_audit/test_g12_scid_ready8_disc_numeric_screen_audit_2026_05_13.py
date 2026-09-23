from __future__ import annotations

import json
from pathlib import Path

import build_g12_scid_ready8_disc_numeric_screen_audit_2026_05_13 as builder


def read_json(path: Path):
    with open(builder.io_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def test_decision_accepts_quarantined_control_only():
    decision = read_json(builder.output_path("DECISION_LEDGER"))
    assert decision["terminal_decision"] == builder.TERMINAL_DECISION
    assert decision["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False
    assert decision["opens_validation"] is False
    assert decision["opens_strategy_edge_claims"] is False


def test_recomputed_counts_hashes_and_target_population():
    recomputation = read_json(builder.output_path("RECOMPUTATION_LEDGER"))
    checks = recomputation["accepted_upstream_facts_recomputed"]
    assert checks["ready_cards_8"] is True
    assert checks["source_candidates_3014"] is True
    assert checks["rowset_rows_24112"] is True
    assert checks["rowset_hash_exact"] is True
    assert checks["old_redundant_rowset_excluded"] is True
    assert checks["target_rows_192896"] is True
    assert checks["computable_rows_162336"] is True
    assert checks["fail_closed_rows_30560"] is True
    assert checks["horizons_exact"] is True
    assert checks["target_families_exact"] is True
    assert recomputation["target_result_recompute"]["unique_target_result_row_id_count"] == 192896
    assert recomputation["target_result_recompute"]["unique_target_result_row_hash_count"] == 192896


def test_large_ledger_parsing_and_no_shortcut_proof():
    recomputation = read_json(builder.output_path("RECOMPUTATION_LEDGER"))
    line_counts = recomputation["g0_large_ledger_recompute"]["line_counts"]
    assert line_counts == {
        "aggregate": 4561,
        "ambiguity": 8691,
        "candidate": 24112,
        "contrast": 3400,
        "data_backing": 17380,
        "explanation": 8689,
        "failure": 2161,
        "partition": 192,
    }
    no_shortcut = recomputation["no_shortcut_recompute"]
    assert no_shortcut["candidate_rows_equal_repaired_rowset_rows"] is True
    assert no_shortcut["candidate_target_cells_equal_full_target_population"] is True
    assert no_shortcut["top_n_or_compact_substitute_detected"] is False


def test_explanation_ambiguity_and_data_backing_coverage():
    recomputation = read_json(builder.output_path("RECOMPUTATION_LEDGER"))
    checks = recomputation["accepted_upstream_facts_recomputed"]
    assert checks["explanations_have_data_backing"] is True
    assert checks["data_backing_has_no_unowned_ids"] is True
    assert checks["no_explanation_performance_conversion"] is True
    assert checks["ambiguity_repairable_remaining_zero"] is True
    ledgers = recomputation["g0_large_ledger_recompute"]["ledgers"]
    assert ledgers["explanation"]["phenomenon_type_counts"]
    assert ledgers["ambiguity"]["ambiguity_terminal_status_counts"]
    assert ledgers["failure"]["combined_fail_closed_family_counts"]
    assert ledgers["contrast"]["movement_shift_class_counts"]


def test_repair_and_completion_have_no_remaining_same_g12_items():
    repair = read_json(builder.output_path("REPAIR_LEDGER"))
    completion = read_json(builder.output_path("COMPLETION_AUDIT"))
    assert repair["same_g12_repairable_items_remaining"] == 0
    assert repair["same_g12_unanswered_audit_questions_remaining"] == 0
    assert completion["same_g12_repairable_items_remaining"] == 0
    assert completion["same_g12_unanswered_audit_questions_remaining"] == 0
    assert completion["all_prompt_requirements_satisfied"] is True
    assert completion["missing_incomplete_or_weakly_verified_requirements"] == []


def test_next_g0_prompt_and_starter_are_bound_to_discriminative_audit():
    assert builder.file_exists(builder.NEXT_G0_PROMPT)
    assert builder.file_exists(builder.NEXT_G0_STARTER)
    prompt_text = Path(builder.NEXT_G0_PROMPT).read_text(encoding="utf-8")
    starter_text = Path(builder.NEXT_G0_STARTER).read_text(encoding="utf-8")
    assert "G12_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_AUDIT" in prompt_text
    assert "g12_scid_ready8_discriminative_numerical_screen_audit" in prompt_text
    assert "NO_PROMOTION_VERDICT" in starter_text
    assert "validation_safe=false" in starter_text
