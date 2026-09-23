"""Shared methodology guardrails for GTOS research claims.

This module is research-only. It centralizes the CPCV-honest standard error,
effective-N, CSCV PBO, and hardening-column checks used by offline research
reports. Production trading code must not import it.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence


DEFAULT_CPCV_RHO = 0.6429
DEFAULT_DSR_P_THRESHOLD = 0.01
DEFAULT_PBO_THRESHOLD = 0.40
DEFAULT_EFFECTIVE_N_MIN = 3.0

REQUIRED_HARDENING_COLUMNS = (
    "methodology_status",
    "dsr_status",
    "pbo_status",
    "effective_n_status",
    "promotion_p_value_allowed",
    "not_computable_reason",
    "latest_artifact_path",
)

DISCOVERY_ONLY_CLASSES = {
    "same_dataset_discovery",
    "same_dataset_discovery_variants",
    "posthoc_diagnostic",
    "label_limited_orderflow_diagnostic",
    "price_transfer_not_alpha",
}

PASS_STATUSES = {"pass", "passed", "survives"}


@dataclass(frozen=True)
class WeightedStandardError:
    n: int
    mean: float
    sample_std: float
    naive_se: float
    rho: float
    design_effect: float
    weighted_se: float
    t_stat: float | None
    p_two_sided_normal_approx: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PBOResult:
    pbo: float
    n_periods: int
    n_strategies: int
    split_size: int
    n_combinations_total: int
    n_combinations_used: int
    method: str = "cscv_pbo"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _finite_floats(values: Iterable[float]) -> list[float]:
    out = [float(value) for value in values]
    return [value for value in out if math.isfinite(value)]


def _normal_two_sided_p(z_score: float) -> float:
    return float(math.erfc(abs(z_score) / math.sqrt(2.0)))


def training_overlap_weighted_standard_error(
    diffs: Iterable[float],
    *,
    rho: float = DEFAULT_CPCV_RHO,
) -> WeightedStandardError:
    """Return CPCV-honest SE inflated for overlapping training sets.

    Formula used in the Q1 methodology doctrine:

    ``SE = sqrt(sample_var / n * (1 + (n - 1) * rho))``
    """

    values = _finite_floats(diffs)
    n = len(values)
    if n < 2:
        raise ValueError("at least two finite diffs are required")

    min_rho = -1.0 / (n - 1)
    if rho < min_rho:
        raise ValueError(f"rho={rho} gives negative design effect for n={n}")

    mean = sum(values) / n
    sample_var = sum((value - mean) ** 2 for value in values) / (n - 1)
    sample_std = math.sqrt(sample_var)
    naive_se = sample_std / math.sqrt(n)
    design_effect = 1.0 + (n - 1) * rho
    weighted_se = math.sqrt((sample_var / n) * design_effect)
    t_stat = mean / weighted_se if weighted_se > 0 else None
    p_two = _normal_two_sided_p(t_stat) if t_stat is not None else None

    return WeightedStandardError(
        n=n,
        mean=float(mean),
        sample_std=float(sample_std),
        naive_se=float(naive_se),
        rho=float(rho),
        design_effect=float(design_effect),
        weighted_se=float(weighted_se),
        t_stat=float(t_stat) if t_stat is not None else None,
        p_two_sided_normal_approx=float(p_two) if p_two is not None else None,
    )


def effective_n_from_average_correlation(
    n_trials: int,
    avg_pair_correlation: float,
) -> float:
    """Shrink a nominal trial count by average pairwise trial correlation."""

    if n_trials < 1:
        raise ValueError("n_trials must be positive")
    if n_trials == 1 or avg_pair_correlation <= 0:
        return float(n_trials)

    denom = 1.0 + (n_trials - 1) * float(avg_pair_correlation)
    if denom <= 0:
        return float(n_trials)
    return float(min(n_trials, max(1.0, n_trials / denom)))


def effective_n_participation_ratio(eigenvalues: Iterable[float]) -> float:
    """Return participation-ratio effective N from non-negative eigenvalues."""

    vals = [max(0.0, value) for value in _finite_floats(eigenvalues)]
    if not vals:
        raise ValueError("at least one finite eigenvalue is required")
    denom = sum(value * value for value in vals)
    if denom <= 0:
        return 1.0
    return float((sum(vals) ** 2) / denom)


def cumulative_trial_budget(
    *,
    existing_program_trials: int,
    new_trials: int,
    avg_pair_correlation: float | None = None,
) -> dict[str, Any]:
    """Summarize nominal and effective trial budget for a new research claim."""

    total = int(existing_program_trials) + int(new_trials)
    if total < 1:
        raise ValueError("cumulative trial budget must be positive")
    effective_n = (
        effective_n_from_average_correlation(total, avg_pair_correlation)
        if avg_pair_correlation is not None
        else float(total)
    )
    return {
        "existing_program_trials": int(existing_program_trials),
        "new_trials": int(new_trials),
        "cumulative_trial_count": int(total),
        "avg_pair_correlation": avg_pair_correlation,
        "effective_n": float(effective_n),
    }


def cscv_pbo(
    performance_matrix: Sequence[Sequence[float]],
    *,
    max_combinations: int | None = 2000,
) -> PBOResult:
    """Compute CSCV Probability of Backtest Overfitting.

    ``performance_matrix`` is periods x strategies, where higher is better.
    The implementation selects the best strategy in-sample and checks whether
    that strategy ranks below the OOS median.
    """

    rows = [list(_finite_floats(row)) for row in performance_matrix]
    if len(rows) < 2:
        raise ValueError("at least two periods are required")
    n_strategies = len(rows[0])
    if n_strategies < 2:
        raise ValueError("at least two strategies are required")
    if any(len(row) != n_strategies for row in rows):
        raise ValueError("performance_matrix must be rectangular")

    n_periods = len(rows)
    split_size = n_periods // 2
    if split_size < 1 or split_size == n_periods:
        raise ValueError("invalid CSCV split size")

    all_combos = list(itertools.combinations(range(n_periods), split_size))
    n_total = len(all_combos)
    if max_combinations is not None and n_total > max_combinations:
        stride = math.ceil(n_total / max_combinations)
        combos = all_combos[::stride][:max_combinations]
    else:
        combos = all_combos

    below_median = 0
    for is_idx_tuple in combos:
        is_idx = set(is_idx_tuple)
        oos_idx = [idx for idx in range(n_periods) if idx not in is_idx]
        is_means = [
            sum(rows[idx][strategy] for idx in is_idx) / len(is_idx)
            for strategy in range(n_strategies)
        ]
        selected = max(range(n_strategies), key=lambda strategy: is_means[strategy])
        oos_means = [
            sum(rows[idx][strategy] for idx in oos_idx) / len(oos_idx)
            for strategy in range(n_strategies)
        ]
        selected_oos = oos_means[selected]
        rank_best_is_high = 1 + sum(value <= selected_oos for value in oos_means if value != selected_oos)
        # Ties at the selected value receive the midpoint of their tied ranks.
        ties = sum(value == selected_oos for value in oos_means)
        if ties > 1:
            rank_best_is_high += (ties - 1) / 2.0
        omega = rank_best_is_high / (n_strategies + 1.0)
        logit = math.log(omega / (1.0 - omega))
        if logit < 0:
            below_median += 1

    pbo = below_median / len(combos)
    return PBOResult(
        pbo=float(pbo),
        n_periods=n_periods,
        n_strategies=n_strategies,
        split_size=split_size,
        n_combinations_total=n_total,
        n_combinations_used=len(combos),
    )


def missing_hardening_columns(row: Mapping[str, Any]) -> list[str]:
    return [column for column in REQUIRED_HARDENING_COLUMNS if column not in row]


def _status_from_metric(value: Any, *, threshold: float, lower_is_better: bool) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "not_computable"
    if not math.isfinite(numeric):
        return "not_computable"
    passed = numeric < threshold if lower_is_better else numeric >= threshold
    return "pass" if passed else "fail"


def build_methodology_row(
    *,
    claim_id: str,
    evidence_class: str,
    latest_artifact_path: str,
    dsr_p: float | None = None,
    pbo: float | None = None,
    effective_n: float | None = None,
    methodology_status: str | None = None,
    not_computable_reason: str = "",
    promotion_verdict: str = "NO_PROMOTION_VERDICT",
) -> dict[str, Any]:
    """Build a hardened claim row with the required methodology columns."""

    if evidence_class in DISCOVERY_ONLY_CLASSES:
        row_methodology_status = methodology_status or "discovery_only"
        dsr_status = "not_computable"
        pbo_status = "not_computable"
        effective_n_status = "not_computable"
        promotion_allowed = False
        reason = not_computable_reason or f"{evidence_class}_not_promotion_grade"
    else:
        row_methodology_status = methodology_status or "candidate"
        dsr_status = _status_from_metric(dsr_p, threshold=DEFAULT_DSR_P_THRESHOLD, lower_is_better=True)
        pbo_status = _status_from_metric(pbo, threshold=DEFAULT_PBO_THRESHOLD, lower_is_better=True)
        effective_n_status = _status_from_metric(
            effective_n,
            threshold=DEFAULT_EFFECTIVE_N_MIN,
            lower_is_better=False,
        )
        reason = not_computable_reason
        promotion_allowed = (
            row_methodology_status in PASS_STATUSES
            and dsr_status == "pass"
            and pbo_status == "pass"
            and effective_n_status == "pass"
            and bool(latest_artifact_path)
        )

    return {
        "claim_id": claim_id,
        "evidence_class": evidence_class,
        "promotion_verdict": promotion_verdict,
        "methodology_status": row_methodology_status,
        "dsr_status": dsr_status,
        "pbo_status": pbo_status,
        "effective_n_status": effective_n_status,
        "promotion_p_value_allowed": bool(promotion_allowed),
        "not_computable_reason": reason,
        "latest_artifact_path": latest_artifact_path,
        "metrics": {
            "dsr_p": dsr_p,
            "pbo": pbo,
            "effective_n": effective_n,
        },
    }


def evaluate_hardened_claim(row: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate whether a hardened report row may expose promotion p-values."""

    missing = missing_hardening_columns(row)
    if missing:
        return {
            "methodology_status": "blocked_missing_hardening_columns",
            "promotion_p_value_allowed": False,
            "missing_hardening_columns": missing,
            "not_computable_reason": "missing_required_methodology_columns",
        }

    statuses = [
        str(row.get("methodology_status")),
        str(row.get("dsr_status")),
        str(row.get("pbo_status")),
        str(row.get("effective_n_status")),
    ]
    reason = str(row.get("not_computable_reason") or "")
    artifact = str(row.get("latest_artifact_path") or "")
    claimed_allowed = row.get("promotion_p_value_allowed") is True
    all_pass = all(status in PASS_STATUSES for status in statuses)

    if not artifact:
        return {
            "methodology_status": "blocked_missing_artifact",
            "promotion_p_value_allowed": False,
            "missing_hardening_columns": [],
            "not_computable_reason": "latest_artifact_path_missing",
        }
    if reason and not all_pass:
        return {
            "methodology_status": "blocked_or_discovery",
            "promotion_p_value_allowed": False,
            "missing_hardening_columns": [],
            "not_computable_reason": reason,
        }
    return {
        "methodology_status": "pass" if all_pass and claimed_allowed else "blocked_by_methodology_status",
        "promotion_p_value_allowed": bool(all_pass and claimed_allowed),
        "missing_hardening_columns": [],
        "not_computable_reason": "" if all_pass and claimed_allowed else "one_or_more_methodology_statuses_not_pass",
    }

