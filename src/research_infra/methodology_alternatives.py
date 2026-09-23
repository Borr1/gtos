"""Research-only alternative methodology tests for GTOS lift claims.

The functions in this module are offline research helpers. They do not import
production trading code and must not be used as live decision logic.
"""

from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class AucResult:
    n: int
    n_positive: int
    n_negative: int
    auc: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HACMeanTest:
    n: int
    mean: float
    max_lag: int
    long_run_variance: float
    standard_error: float
    statistic: float | None
    p_two_sided_normal: float | None
    p_one_sided_greater: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StationaryBootstrapTest:
    n: int
    observed_mean: float
    reps: int
    average_block_length: int
    p_value_greater: float
    bootstrap_sd: float
    null_q025: float
    null_q975: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BayesianNormalPosterior:
    observed_mean: float
    observed_se: float
    prior_mean: float
    prior_sd: float
    posterior_mean: float
    posterior_sd: float
    threshold_probabilities: dict[str, float]
    bayes_factor_h1_gt_0: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RomanoWolfStepMResult:
    n_observations: int
    n_hypotheses: int
    alpha: float
    reps: int
    rejected_indices: list[int]
    observed_t: list[float | None]
    critical_values_by_step: list[float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def finite_floats(values: Iterable[float]) -> list[float]:
    out = [float(value) for value in values]
    return [value for value in out if math.isfinite(value)]


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def normal_two_sided_p(z_score: float) -> float:
    return float(math.erfc(abs(z_score) / math.sqrt(2.0)))


def normal_one_sided_greater_p(z_score: float) -> float:
    return float(1.0 - normal_cdf(z_score))


def auc_rank_binary(y_true: Sequence[int], scores: Sequence[float]) -> AucResult:
    """Return rank-based binary AUC with average ranks for ties.

    Returns ``auc=None`` if either class is absent.
    """

    if len(y_true) != len(scores):
        raise ValueError("y_true and scores must have equal length")
    pairs = [(float(score), int(label)) for label, score in zip(y_true, scores)]
    pairs = [(score, label) for score, label in pairs if math.isfinite(score) and label in {0, 1}]
    if not pairs:
        return AucResult(n=0, n_positive=0, n_negative=0, auc=None)

    n_pos = sum(1 for _, label in pairs if label == 1)
    n_neg = sum(1 for _, label in pairs if label == 0)
    if n_pos == 0 or n_neg == 0:
        return AucResult(n=len(pairs), n_positive=n_pos, n_negative=n_neg, auc=None)

    sorted_pairs = sorted(enumerate(pairs), key=lambda item: item[1][0])
    ranks = [0.0] * len(sorted_pairs)
    i = 0
    while i < len(sorted_pairs):
        j = i + 1
        score = sorted_pairs[i][1][0]
        while j < len(sorted_pairs) and sorted_pairs[j][1][0] == score:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            original_idx = sorted_pairs[k][0]
            ranks[original_idx] = avg_rank
        i = j

    rank_sum_pos = sum(rank for rank, (_, label) in zip(ranks, pairs) if label == 1)
    auc = (rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return AucResult(n=len(pairs), n_positive=n_pos, n_negative=n_neg, auc=float(auc))


def newey_west_mean_test(values: Iterable[float], *, max_lag: int | None = None) -> HACMeanTest:
    """Diebold-Mariano-style mean test with Newey-West HAC variance.

    Positive values mean the candidate outperformed the benchmark. For classic
    DM loss differentials, pass ``benchmark_loss - candidate_loss`` if lower
    loss is better.
    """

    x = finite_floats(values)
    n = len(x)
    if n < 2:
        raise ValueError("at least two finite observations are required")
    mean = sum(x) / n
    centered = [value - mean for value in x]
    if max_lag is None:
        max_lag = max(0, int(n ** (1.0 / 3.0)))
    max_lag = min(max_lag, n - 1)

    gamma0 = sum(value * value for value in centered) / n
    long_run_variance = gamma0
    for lag in range(1, max_lag + 1):
        cov = sum(centered[i] * centered[i - lag] for i in range(lag, n)) / n
        weight = 1.0 - lag / (max_lag + 1.0)
        long_run_variance += 2.0 * weight * cov
    long_run_variance = max(0.0, long_run_variance)
    se = math.sqrt(long_run_variance / n) if long_run_variance > 0 else 0.0
    statistic = mean / se if se > 0 else None
    p_two = normal_two_sided_p(statistic) if statistic is not None else None
    p_gt = normal_one_sided_greater_p(statistic) if statistic is not None else None
    return HACMeanTest(
        n=n,
        mean=float(mean),
        max_lag=int(max_lag),
        long_run_variance=float(long_run_variance),
        standard_error=float(se),
        statistic=float(statistic) if statistic is not None else None,
        p_two_sided_normal=float(p_two) if p_two is not None else None,
        p_one_sided_greater=float(p_gt) if p_gt is not None else None,
    )


def stationary_bootstrap_mean_test(
    values: Iterable[float],
    *,
    reps: int = 2000,
    average_block_length: int = 5,
    seed: int = 42,
) -> StationaryBootstrapTest:
    """Stationary-bootstrap one-sided p-value for mean(values) > 0.

    The bootstrap distribution is recentered to the null mean of zero. This is
    a SPA-style diagnostic for a single lift sequence; use the report caveats
    when CPCV paths are dependent.
    """

    x = finite_floats(values)
    n = len(x)
    if n < 2:
        raise ValueError("at least two finite observations are required")
    if reps < 1:
        raise ValueError("reps must be positive")
    if average_block_length < 1:
        raise ValueError("average_block_length must be positive")

    rng = random.Random(seed)
    obs = sum(x) / n
    p_geom = 1.0 / average_block_length
    null_means: list[float] = []
    for _ in range(reps):
        sample: list[float] = []
        while len(sample) < n:
            start = rng.randrange(n)
            block_len = 1
            while rng.random() > p_geom:
                block_len += 1
            for offset in range(block_len):
                sample.append(x[(start + offset) % n])
                if len(sample) >= n:
                    break
        boot_mean = sum(sample) / n
        null_means.append(boot_mean - obs)

    tail = sum(1 for value in null_means if value >= obs) / reps
    mean_null = sum(null_means) / reps
    sd = math.sqrt(sum((value - mean_null) ** 2 for value in null_means) / max(1, reps - 1))
    sorted_null = sorted(null_means)
    q025 = sorted_null[min(reps - 1, max(0, int(0.025 * reps)))]
    q975 = sorted_null[min(reps - 1, max(0, int(0.975 * reps)))]
    return StationaryBootstrapTest(
        n=n,
        observed_mean=float(obs),
        reps=int(reps),
        average_block_length=int(average_block_length),
        p_value_greater=float(tail),
        bootstrap_sd=float(sd),
        null_q025=float(q025),
        null_q975=float(q975),
    )


def bayesian_normal_normal_posterior(
    *,
    observed_mean: float,
    observed_se: float,
    prior_mean: float = 0.0,
    prior_sd: float = 0.05,
    thresholds: Sequence[float] = (0.0, 0.02, 0.04),
) -> BayesianNormalPosterior:
    """Conjugate normal posterior for a lift estimate."""

    if observed_se <= 0 or prior_sd <= 0:
        raise ValueError("observed_se and prior_sd must be positive")
    obs_var = observed_se * observed_se
    prior_var = prior_sd * prior_sd
    post_var = 1.0 / (1.0 / obs_var + 1.0 / prior_var)
    post_mean = post_var * (observed_mean / obs_var + prior_mean / prior_var)
    post_sd = math.sqrt(post_var)
    probs = {
        f"p_theta_gte_{threshold:g}": float(1.0 - normal_cdf((threshold - post_mean) / post_sd))
        for threshold in thresholds
    }
    # Savage-Dickey approximation for one-sided H1 over H0 point mass at zero.
    prior_density_zero = math.exp(-0.5 * ((0.0 - prior_mean) / prior_sd) ** 2) / (prior_sd * math.sqrt(2.0 * math.pi))
    post_density_zero = math.exp(-0.5 * ((0.0 - post_mean) / post_sd) ** 2) / (post_sd * math.sqrt(2.0 * math.pi))
    bayes_factor = prior_density_zero / post_density_zero if post_density_zero > 0 else None
    return BayesianNormalPosterior(
        observed_mean=float(observed_mean),
        observed_se=float(observed_se),
        prior_mean=float(prior_mean),
        prior_sd=float(prior_sd),
        posterior_mean=float(post_mean),
        posterior_sd=float(post_sd),
        threshold_probabilities=probs,
        bayes_factor_h1_gt_0=float(bayes_factor) if bayes_factor is not None else None,
    )


def _column(values: Sequence[Sequence[float]], idx: int) -> list[float]:
    return [float(row[idx]) for row in values]


def _studentized_mean(values: Sequence[float]) -> float | None:
    n = len(values)
    if n < 2:
        return None
    mean = sum(values) / n
    var = sum((value - mean) ** 2 for value in values) / (n - 1)
    se = math.sqrt(var / n) if var > 0 else 0.0
    return mean / se if se > 0 else None


def romano_wolf_stepm(
    performance_differentials: Sequence[Sequence[float]],
    *,
    alpha: float = 0.05,
    reps: int = 2000,
    seed: int = 42,
) -> RomanoWolfStepMResult:
    """Romano-Wolf StepM max-t bootstrap over a matrix of lift differentials.

    The input shape is observations x hypotheses. Columns are centered under
    the null before row-resampling so cross-hypothesis dependence is preserved.
    """

    matrix = [[float(value) for value in row] for row in performance_differentials]
    if len(matrix) < 2:
        raise ValueError("at least two observations are required")
    n_obs = len(matrix)
    n_hyp = len(matrix[0])
    if n_hyp < 1:
        raise ValueError("at least one hypothesis is required")
    if any(len(row) != n_hyp for row in matrix):
        raise ValueError("performance_differentials must be rectangular")

    columns = [_column(matrix, idx) for idx in range(n_hyp)]
    observed = [_studentized_mean(col) for col in columns]
    col_means = [sum(col) / n_obs for col in columns]
    centered = [[row[idx] - col_means[idx] for idx in range(n_hyp)] for row in matrix]

    remaining = set(range(n_hyp))
    rejected: list[int] = []
    critical_values: list[float] = []
    rng = random.Random(seed)

    while remaining:
        boot_max: list[float] = []
        for _ in range(reps):
            sample = [centered[rng.randrange(n_obs)] for _ in range(n_obs)]
            max_t = 0.0
            for idx in remaining:
                col = [row[idx] for row in sample]
                t_stat = _studentized_mean(col)
                if t_stat is not None:
                    max_t = max(max_t, abs(t_stat))
            boot_max.append(max_t)
        boot_max.sort()
        crit = boot_max[min(reps - 1, max(0, int(math.ceil((1.0 - alpha) * reps)) - 1))]
        critical_values.append(float(crit))

        candidates = [
            (idx, abs(observed[idx]) if observed[idx] is not None else -1.0)
            for idx in remaining
        ]
        idx, max_obs = max(candidates, key=lambda item: item[1])
        if max_obs > crit:
            rejected.append(idx)
            remaining.remove(idx)
        else:
            break

    return RomanoWolfStepMResult(
        n_observations=n_obs,
        n_hypotheses=n_hyp,
        alpha=float(alpha),
        reps=int(reps),
        rejected_indices=rejected,
        observed_t=[float(value) if value is not None else None for value in observed],
        critical_values_by_step=critical_values,
    )
