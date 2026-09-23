from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path


DATE = "2026-05-13"
ROUTE_ID = "G0_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_LEARNING_SYNTHESIS_AFTER_G12_AUDIT"
EVIDENCE_CLASS = "G0_SCID_READY8_DISCRIMINATIVE_NUMERICAL_SCREEN_LEARNING_SYNTHESIS_ONLY"
RANK1_ROUTE = "G0_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_OPENING_GATE_AFTER_NUMERICAL_SCREEN_G12_AUDIT"
ROWSET_SHA = "fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3"

ROUTE_DIR = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
NEXT_PROMPT = ROOT / f"research/science_program_2026_05/04_goal_prompts/{RANK1_ROUTE}_GOAL_PROMPT_{DATE}.md"
NEXT_STARTER = ROUTE_DIR / f"{RANK1_ROUTE}_STARTER_{DATE}.txt"


def io_path(path: Path) -> str:
    resolved = str(path.resolve(strict=False))
    if os.name == "nt" and not resolved.startswith("\\\\?\\"):
        return "\\\\?\\" + resolved
    return resolved


def read_json(path: Path):
    with open(io_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text(path: Path) -> str:
    with open(io_path(path), "r", encoding="utf-8") as handle:
        return handle.read()


def out_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"G0_SCID_READY8_DISC_NUMERIC_LEARNING_{stem}_{DATE}{suffix}"


def load_verifier_module():
    path = ROUTE_DIR / "verify_g0_scid_ready8_discriminative_learning_synthesis_after_g12_audit_2026_05_13.py"
    spec = importlib.util.spec_from_file_location("ready8_disc_learning_verify", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_exact_facts_and_safe_flags_are_bound():
    fact = read_json(out_path("FACT_RECONCILIATION_LEDGER"))
    assert fact["route_id"] == ROUTE_ID
    assert fact["evidence_class"] == EVIDENCE_CLASS
    assert fact["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert fact["validation_safe"] is False
    assert fact["outcome_review_opened"] is False
    assert fact["live_effect"] is False

    accepted = fact["accepted_exact_facts"]
    assert accepted["ready_cards"] == 8
    assert accepted["source_candidates"] == 3014
    assert accepted["rowset_rows"] == 24112
    assert accepted["rowset_hash"] == ROWSET_SHA
    assert accepted["target_result_rows"] == 192896
    assert accepted["computable_rows"] == 162336
    assert accepted["fail_closed_rows"] == 30560
    assert accepted["g0_screen_ledger_counts"] == {
        "aggregate": 4561,
        "ambiguity": 8691,
        "candidate": 24112,
        "contrast": 3400,
        "data_backing": 17380,
        "explanation": 8689,
        "failure": 2161,
        "partition": 192,
    }


def test_every_required_learning_family_is_preserved_or_killed():
    findings = read_json(out_path("KILLED_AND_PRESERVED_FINDINGS_LEDGER"))
    classes = {row["class"] for row in findings["preserved_findings"] + findings["killed_or_bounded_findings"]}
    assert {
        "positive_control",
        "pass_control_non_applicable_fail_closed",
        "horizon_target_family",
        "duplicate_concentration",
        "positive_negative_inverse_neutral",
        "fail_closed_failure_anatomy",
        "candidate_full_population",
        "descriptor_symbol_partition",
        "forbidden_claim",
        "performance_conversion",
        "denominator_error",
        "route_loop",
        "forbidden_surface",
    }.issubset(classes)
    assert findings["same_evidence_class_learning_remaining"] == 0


def test_question_stack_preserves_seed_and_data_opened_questions():
    questions = read_json(out_path("QUESTION_STACK_LEDGER"))
    ids = {row["question_id"] for row in questions["questions"]}
    assert "seed_01_accepted_screen_proves" in ids
    assert "seed_08_prompt_hardening" in ids
    assert "generated_horizon_target_family" in ids
    assert "generated_failure_anatomy" in ids
    assert questions["same_evidence_class_unanswered_questions_remaining"] == 0
    assert questions["same_evidence_class_learning_remaining"] == 0


def test_rank1_is_non_looping_opening_gate_not_validation():
    decision = read_json(out_path("DECISION_LEDGER"))
    routes = read_json(out_path("ROUTE_RANKING_LEDGER"))
    assert decision["terminal_decision"].startswith("OPEN_RANK1_G0_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_OPENING_GATE")
    assert decision["rank1_route"] == RANK1_ROUTE
    assert routes["rank1_selected"] == RANK1_ROUTE
    assert routes["rank1_is_audit"] is False
    assert routes["rank1_opens_validation"] is False
    assert routes["no_another_audit_as_rank1"] is True


def test_next_prompt_and_starter_are_hardened():
    prompt = read_text(NEXT_PROMPT)
    starter = read_text(NEXT_STARTER)
    assert "This is a gate. It is not validation" in prompt
    assert "same_evidence_class_learning_remaining=0" in prompt
    assert "Do not open validation" in prompt
    assert str(NEXT_PROMPT.relative_to(ROOT)).replace("\\", "/") in starter
    assert "NO_PROMOTION_VERDICT" in starter
    assert "validation_safe=false" in starter


def test_standalone_verifier_passes_without_writing():
    verifier = load_verifier_module()
    result = verifier.verify(mark_focused_tests_ok=True, write_result=False)
    assert result["ok"] is True
    assert result["can_mark_goal_complete"] is True
    assert result["same_evidence_class_learning_remaining"] == 0
