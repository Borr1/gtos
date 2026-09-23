"""Focused tests for the G12 READY8 adversarial-control review."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
PREFIX = "G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT"
DATE_TAG = "2026-05-15"
TERMINAL_DECISION = (
    "ACCEPT_AS_G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_CANONICAL_DOWNSTREAM_CONTROL_EVIDENCE_NO_PROMOTION"
)


def load_module(filename: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROUTE_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


verifier = load_module(
    "verify_g12_ready8_adv_control_placebo_drift_audit_review_2026_05_15.py",
    "g12_ready8_adv_control_verifier",
)


def artifact(stem: str) -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json"


def test_decision_accepts_control_evidence_only() -> None:
    decision = json.loads(artifact("DECISION_LEDGER").read_text(encoding="utf-8"))
    assert decision["accepted"] is True
    assert decision["terminal_decision"] == TERMINAL_DECISION
    assert decision["terminal_blockers"] == []
    assert decision["promotion_verdict"] == "NO_PROMOTION_VERDICT"
    assert decision["validation_safe"] is False
    assert decision["outcome_review_opened"] is False
    assert decision["live_effect"] is False
    assert "promotion" in decision["not_accepted_as"]


def test_recomputation_reconciles_counts_and_classifications() -> None:
    recomp = json.loads(artifact("RECOMPUTATION_LEDGER").read_text(encoding="utf-8"))
    counts = recomp["row_count_recomputation"]
    assert counts["adv001_placebo"] == 4288
    assert counts["adv003_placebo"] == 12611
    assert counts["comparison_mapping"] == 10563
    assert counts["concentration"] == 79746
    assert counts["underpower"] == 79746
    assert recomp["control_envelope_math_mismatch_count"] == 0
    assert recomp["control_match_missing_rows"] == 0
    assert recomp["explained_weakened_key_set_matches_mapping"] is True
    assert recomp["residual_key_set_matches_mapping"] is True
    assert recomp["control_envelope_classification_counts"] == {
        "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 2608,
        "MATERIALLY_WEAKENED_BY_ADV_CONTROL_DRIFT": 14,
        "NOT_NUMERIC_NOT_ADJUSTABLE": 3622,
        "RESIDUAL_PRESERVED_AFTER_ADV_CONTROL_ENVELOPE": 1,
        "UNDERPOWERED_PRESERVED_NOT_DECISION": 4318,
    }


def test_adv_controls_are_not_edge_cards() -> None:
    recomp = json.loads(artifact("RECOMPUTATION_LEDGER").read_text(encoding="utf-8"))
    assert recomp["control_cards_are_not_edge_cards"] is True
    assert recomp["adv_card_id_counts"]["ADV-001"] == {"ADV-001": 4288}
    assert recomp["adv_card_id_counts"]["ADV-003"] == {"ADV-003": 12611}
    assert sorted(recomp["nonadv_cards_observed"]) == [
        "BEH-001",
        "HAZ-001",
        "HAZ-005",
        "MAC-001",
        "MAC-004",
        "UNC-004",
    ]


def test_no_unresolved_same_g12_issues() -> None:
    discrepancy = json.loads(artifact("DISCREPANCY_REPAIR_LEDGER").read_text(encoding="utf-8"))
    questions = json.loads(artifact("QUESTION_AMBIGUITY_ROUTE_LEDGER").read_text(encoding="utf-8"))
    saturation = json.loads(artifact("SATURATION_SELF_RED_TEAM_LEDGER").read_text(encoding="utf-8"))
    assert discrepancy["same_g12_repairable_items_remaining"] == 0
    assert discrepancy["issues"] == []
    assert questions["unresolved_blockers"] == []
    assert questions["ambiguities"] == []
    assert saturation["artifact_inspection_gap_set"] == []
    assert saturation["actionable_ambiguity_set"] == []


def test_verifier_accepts_g12_review_package() -> None:
    result = verifier.verify(mark_focused_tests_ok=False)
    assert result["ok"], result["failures"]
    assert result["terminal_decision"] == TERMINAL_DECISION
