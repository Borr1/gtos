from __future__ import annotations

from scripts import analyze_lane1_remaining_methodology_triage as triage
from src.research_infra.methodology_alternatives import (
    auc_rank_binary,
    bayesian_normal_normal_posterior,
    newey_west_mean_test,
    romano_wolf_stepm,
    stationary_bootstrap_mean_test,
)


def test_auc_rank_binary_handles_ties_and_missing_class():
    auc = auc_rank_binary([0, 1, 0, 1], [0.1, 0.9, 0.4, 0.9])
    assert auc.n == 4
    assert auc.n_positive == 2
    assert auc.n_negative == 2
    assert auc.auc == 1.0

    no_auc = auc_rank_binary([1, 1], [0.2, 0.3])
    assert no_auc.auc is None


def test_newey_west_mean_test_detects_positive_mean():
    result = newey_west_mean_test([0.10, 0.14, 0.13, 0.17, 0.16, 0.12], max_lag=1)
    assert result.mean > 0
    assert result.standard_error > 0
    assert result.p_one_sided_greater is not None
    assert result.p_one_sided_greater < 0.05


def test_stationary_bootstrap_mean_test_recenters_null():
    result = stationary_bootstrap_mean_test(
        [0.10, 0.14, 0.13, 0.17, 0.16, 0.12],
        reps=300,
        average_block_length=2,
        seed=7,
    )
    assert result.observed_mean > 0
    assert result.p_value_greater < 0.10


def test_bayesian_normal_normal_posterior_shrinks_toward_prior():
    posterior = bayesian_normal_normal_posterior(
        observed_mean=0.05,
        observed_se=0.05,
        prior_mean=0.0,
        prior_sd=0.05,
        thresholds=(0.0, 0.04),
    )
    assert 0.0 < posterior.posterior_mean < 0.05
    assert posterior.threshold_probabilities["p_theta_gte_0"] > 0.5
    assert posterior.threshold_probabilities["p_theta_gte_0.04"] < posterior.threshold_probabilities["p_theta_gte_0"]


def test_romano_wolf_stepm_rejects_strong_column_only():
    matrix = [
        [0.30, 0.01],
        [0.28, -0.02],
        [0.35, 0.03],
        [0.31, -0.01],
        [0.33, 0.02],
        [0.29, -0.03],
        [0.36, 0.01],
        [0.32, -0.02],
    ]

    result = romano_wolf_stepm(matrix, alpha=0.05, reps=300, seed=11)

    assert result.n_observations == 8
    assert result.n_hypotheses == 2
    assert 0 in result.rejected_indices
    assert 1 not in result.rejected_indices


