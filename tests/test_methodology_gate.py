from __future__ import annotations

import math

from src.research_infra import methodology_gate as gate


def test_training_overlap_weighted_se_inflates_naive_se():
    diffs = [0.01, 0.03, 0.02, 0.04, -0.01]

    result = gate.training_overlap_weighted_standard_error(diffs, rho=0.5)

    expected_design_effect = 1.0 + (len(diffs) - 1) * 0.5
    assert math.isclose(result.design_effect, expected_design_effect)
    assert result.weighted_se > result.naive_se
    assert math.isclose(result.weighted_se, result.naive_se * math.sqrt(expected_design_effect))


def test_effective_n_shrinks_correlated_trial_budget():
    effective_n = gate.effective_n_from_average_correlation(100, 0.5)

    assert 1.0 <= effective_n < 100
    assert math.isclose(effective_n, 100 / (1 + 99 * 0.5))


def test_cscv_pbo_detects_persistent_skill_as_low_overfit():
    matrix = [
        [2.0, 1.0, 0.5],
        [2.1, 0.8, 0.4],
        [1.9, 1.1, 0.3],
        [2.2, 0.7, 0.2],
    ]

    result = gate.cscv_pbo(matrix)

    assert result.pbo == 0.0
    assert result.n_combinations_used == 6


def test_missing_hardening_columns_blocks_promotion_p_values():
    out = gate.evaluate_hardened_claim({"claim_id": "x", "methodology_status": "pass"})

    assert out["promotion_p_value_allowed"] is False
    assert out["methodology_status"] == "blocked_missing_hardening_columns"
    assert "pbo_status" in out["missing_hardening_columns"]


def test_discovery_row_requires_no_promotion_and_reason():
    row = gate.build_methodology_row(
        claim_id="path_v3_same_dataset",
        evidence_class="same_dataset_discovery",
        latest_artifact_path="research/example.md",
    )
    out = gate.evaluate_hardened_claim(row)

    assert row["promotion_p_value_allowed"] is False
    assert row["methodology_status"] == "discovery_only"
    assert row["not_computable_reason"]
    assert out["promotion_p_value_allowed"] is False
    assert out["methodology_status"] == "blocked_or_discovery"


def test_promotion_candidate_requires_all_methodology_passes_and_artifact():
    row = gate.build_methodology_row(
        claim_id="registered_unseen_claim",
        evidence_class="registered_unseen_validation",
        methodology_status="pass",
        latest_artifact_path="research/registered_unseen_claim.md",
        dsr_p=0.001,
        pbo=0.2,
        effective_n=5,
    )

    out = gate.evaluate_hardened_claim(row)

    assert row["promotion_p_value_allowed"] is True
    assert out["promotion_p_value_allowed"] is True
    assert out["methodology_status"] == "pass"


def test_missing_artifact_blocks_even_when_metrics_pass():
    row = gate.build_methodology_row(
        claim_id="registered_unseen_claim",
        evidence_class="registered_unseen_validation",
        methodology_status="pass",
        latest_artifact_path="",
        dsr_p=0.001,
        pbo=0.2,
        effective_n=5,
    )

    out = gate.evaluate_hardened_claim(row)

    assert row["promotion_p_value_allowed"] is False
    assert out["promotion_p_value_allowed"] is False
    assert out["methodology_status"] == "blocked_missing_artifact"

