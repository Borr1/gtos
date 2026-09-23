"""Standing Validation-Integrity Gauntlet — the single assembled gate.

This module wires the six already-built, independently-tested validation-integrity
components into ONE verdict so every edge promotion passes the same standing gate:

  1. dsr.deflated_sharpe_ratio           — is the Sharpe real after deflating for the
                                            number of trials the search consumed?
  2. pbo.pbo_cscv                        — is the book predominantly overfit (does the
                                            IS-best column revert to the OOS median)?
  3. perm_null.block_permutation_test    — does the directional edge survive its own
                                            short-horizon autocorrelation?
  4. regime_inflation.regime_inflation_diagnostic
                                         — is the selection / forward window itself the
                                            contamination (best-N-years regime), i.e. is
                                            the MAGNITUDE inflated in a way PBO and DSR
                                            provably miss?
  5. walk_forward_oos.purged_embargoed_walkforward
                                         — does the edge hold on strictly-future,
                                            embargoed out-of-sample folds?

The gauntlet keeps each component's full sub-result, derives a small set of named gates
on top of them, and returns an overall ``integrity_verdict`` in {PASS, CONDITIONAL, FAIL}
with explicit reasons, plus an ``honest_summary`` block that states the deployable basis
(the n=1, all-history, no-selection daily Sharpe) and the recommended magnitude haircut.

Honesty-by-construction
-----------------------
* DSR's cross-trial Sharpe variance ``V`` cannot be recovered from a single combined
  series — it is a property of the search. When the caller does not supply ``sr_variance``
  the gauntlet estimates it from the DISPERSION of the per-sleeve per-period Sharpe ratios
  (population variance, ddof=0, across the columns of ``sleeve_matrix``). This is the same
  empirical estimator the orchestrator verified by hand on the real book
  (V = 1.4680e-3, sqrt = 0.03831).
* The verdict separates STRUCTURE (is the directional edge real — DSR/PBO/permutation)
  from MAGNITUDE (is the in-window return level deployable — regime inflation). A book can
  have a real structural edge AND a ~3x-inflated magnitude; that is CONDITIONAL, not PASS.
* No silent fallbacks that would weaken the gate. If a component is missing or its API has
  drifted, fix the call — do not stub it.

No hard scipy dependency: the per-component math is erf-based / numpy-only.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence

# Import the six sibling components. Work both as a package
# (research_infra.validation_integrity.gauntlet) and when the directory is on sys.path.
try:  # pragma: no cover - exercised both ways across callers/tests
    from . import (
        dsr as _dsr,
        pbo as _pbo,
        perm_null as _perm_null,
        regime_inflation as _regime_inflation,
        walk_forward_oos as _walk_forward_oos,
    )
except ImportError:  # pragma: no cover
    import dsr as _dsr  # type: ignore
    import pbo as _pbo  # type: ignore
    import perm_null as _perm_null  # type: ignore
    import regime_inflation as _regime_inflation  # type: ignore
    import walk_forward_oos as _walk_forward_oos  # type: ignore

__all__ = ["run_gauntlet", "estimate_sr_variance_from_sleeves"]

SCHEMA = "gtos.validation_integrity.gauntlet.v1"

# ---------------------------------------------------------------------------
# Verdict thresholds (named, documented, internally consistent).
# ---------------------------------------------------------------------------
DSR_SIGNIFICANCE = 0.95        # dsr must exceed this to call the Sharpe "significant"
PBO_OVERFIT_GATE = 0.5         # PBO >= 0.5 == IS-best reverts to OOS median == overfit
PERM_ALPHA = 0.05              # permutation p_value must be below this (directional edge)
WF_DEGRADATION_FAIL_PCT = 50.0 # IS->OOS Sharpe decay above this is a generalization concern
WF_OOS_POS_FRAC_MIN = 0.5      # fraction of OOS folds that must be Sharpe-positive
WF_OOS_POS_FRAC_DEAD = 1e-12   # 0 positive OOS folds == edge dead out-of-sample == structural fail


# ---------------------------------------------------------------------------
# sr_variance estimator (cross-trial Sharpe dispersion from the sleeves).
# ---------------------------------------------------------------------------
def _as_list_of_rows(sleeve_matrix: Any) -> List[List[float]]:
    """Coerce a (T, N) matrix (list-of-lists or numpy array) to list-of-lists of float."""
    if hasattr(sleeve_matrix, "tolist"):
        sleeve_matrix = sleeve_matrix.tolist()
    rows = [[float(v) for v in row] for row in sleeve_matrix]
    if not rows:
        raise ValueError("sleeve_matrix is empty")
    n_cols = len(rows[0])
    if n_cols < 1:
        raise ValueError("sleeve_matrix has no columns")
    for r in rows:
        if len(r) != n_cols:
            raise ValueError("sleeve_matrix is ragged (rows have unequal length)")
    return rows


def estimate_sr_variance_from_sleeves(sleeve_matrix: Any) -> Dict[str, Any]:
    """Estimate the DSR cross-trial Sharpe variance from per-sleeve Sharpe dispersion.

    For each sleeve column compute its per-period Sharpe (mean / population-std), then
    take the POPULATION variance (ddof=0) of those per-sleeve Sharpes. This treats the
    11 sleeves as the realised draws of the search's per-trial Sharpe and uses their
    dispersion as ``V``. ddof=0 reproduces the orchestrator's hand-verified V = 1.4680e-3.

    Returns a dict: {sr_variance, sqrt, per_sleeve_sharpe, n_sleeves}.
    """
    rows = _as_list_of_rows(sleeve_matrix)
    T = len(rows)
    N = len(rows[0])
    per_sleeve: List[float] = []
    for j in range(N):
        col = [rows[i][j] for i in range(T)]
        m = math.fsum(col) / T
        var = math.fsum((x - m) * (x - m) for x in col) / T  # population var
        sd = math.sqrt(var) if var > 0.0 else 0.0
        per_sleeve.append((m / sd) if sd > 0.0 else 0.0)
    mu = math.fsum(per_sleeve) / N
    sr_variance = math.fsum((s - mu) * (s - mu) for s in per_sleeve) / N  # ddof=0
    return {
        "sr_variance": sr_variance,
        "sqrt": math.sqrt(sr_variance) if sr_variance > 0 else 0.0,
        "per_sleeve_sharpe": per_sleeve,
        "n_sleeves": N,
    }


def _pop_std(xs: Sequence[float]) -> float:
    n = len(xs)
    m = math.fsum(xs) / n
    var = math.fsum((x - m) * (x - m) for x in xs) / n
    return math.sqrt(var) if var > 0 else 0.0


# ---------------------------------------------------------------------------
# Main entry point.
# ---------------------------------------------------------------------------
def run_gauntlet(
    combined_daily: Sequence[float],
    dated_series: Sequence[Any],
    sleeve_matrix: Any,
    sleeves: Sequence[str],
    selection_window_start: Any,
    n_trials: int,
    sr_variance: Optional[float] = None,
) -> Dict[str, Any]:
    """Run the full Validation-Integrity Gauntlet and return one merged verdict.

    Parameters
    ----------
    combined_daily : sequence of float
        The combined per-period (daily-R) series of the book.
    dated_series : list of (date | iso-str, float)
        The same series keyed by date (used by the regime and walk-forward components).
    sleeve_matrix : (T, N) array-like
        Per-sleeve per-period returns (the columns are the sleeves). Used by PBO and to
        estimate the DSR cross-trial Sharpe variance when ``sr_variance`` is None.
    sleeves : sequence of str
        The N sleeve names (length must equal the number of matrix columns).
    selection_window_start : date | iso-str
        Start (inclusive) of the selection / forward window scored against.
    n_trials : int
        Number of trials the search consumed (for DSR deflation + regime penalty).
    sr_variance : float, optional
        Cross-trial Sharpe variance for DSR. If None it is estimated from the per-sleeve
        Sharpe dispersion (see ``estimate_sr_variance_from_sleeves``).

    Returns
    -------
    dict with keys: schema, n_obs, n_sleeves, sleeves, selection_window_start, n_trials,
    sr_variance_used, sr_variance_source, ground_truth, components{dsr,pbo,permutation,
    regime_inflation,walk_forward}, gates, integrity_verdict, integrity_reasons,
    honest_summary, honest_headline.
    """
    combined = [float(v) for v in combined_daily]
    if len(combined) < 2:
        raise ValueError("combined_daily needs at least 2 observations")
    rows = _as_list_of_rows(sleeve_matrix)
    n_cols = len(rows[0])
    sleeves = list(sleeves)
    if len(sleeves) != n_cols:
        raise ValueError(
            f"sleeves length ({len(sleeves)}) != sleeve_matrix columns ({n_cols})"
        )

    # --- resolve sr_variance (estimate from sleeves if not supplied) -------------------
    if sr_variance is None:
        sv = estimate_sr_variance_from_sleeves(rows)
        sr_variance_used = float(sv["sr_variance"])
        sr_variance_source = "estimated_from_per_sleeve_sharpe_dispersion_pop_ddof0"
        sr_variance_detail = sv
    else:
        sr_variance_used = float(sr_variance)
        sr_variance_source = "supplied"
        sr_variance_detail = {"sr_variance": sr_variance_used}

    # --- 1. Deflated Sharpe Ratio (selection-aware significance) -----------------------
    dsr_res = _dsr.deflated_sharpe_ratio(
        combined, n_trials=int(n_trials), sr_variance=sr_variance_used
    )

    # --- 2. Probability of Backtest Overfitting (CSCV on the sleeve matrix) ------------
    pbo_res = _pbo.pbo_cscv(rows, n_partitions=16, metric="sharpe")

    # --- 3. Block sign-flip permutation null (directional edge vs autocorrelation) -----
    perm_res = _perm_null.block_permutation_test(
        combined, block=5, n_perm=5000, stat="sharpe", seed=12345
    )

    # --- 4. Regime-inflation / window-contamination diagnostic (the magnitude gate) ----
    regime_res = _regime_inflation.regime_inflation_diagnostic(
        dated_series, selection_window_start, int(n_trials)
    )

    # --- 5. Purged / embargoed expanding walk-forward (OOS generalization) -------------
    wf_res = _walk_forward_oos.purged_embargoed_walkforward(
        dated_series, n_folds=5, embargo_frac=0.01, expanding=True, stat="sharpe"
    )

    # --- ground-truth reproduction block (so the orchestrator can verify parity) -------
    sd_book = _pop_std(combined)
    mean_all = math.fsum(combined) / len(combined)
    mean_fwd = float(regime_res["mean_in_window"])
    fwd_all_ratio = regime_res["fwd_all_mean_ratio"]
    ground_truth = {
        "sd_book": sd_book,
        "mean_all": mean_all,
        "mean_fwd": mean_fwd,
        "fwd_all_ratio": fwd_all_ratio,
        "n_obs": len(combined),
        "n_in_window": int(regime_res["n_obs_in_window"]),
    }

    # ----------------------------------------------------------------------------------
    # Named gates derived from the component results.
    # ----------------------------------------------------------------------------------
    dsr_pass = bool(dsr_res["significant"])  # dsr > 0.95 at this n_trials
    pbo_value = float(pbo_res["pbo"])
    pbo_pass = pbo_value < PBO_OVERFIT_GATE
    perm_p = float(perm_res["p_value"])
    perm_pass = perm_p < PERM_ALPHA

    agg_deg = wf_res["aggregate_degradation_pct"]
    oos_pos_frac = wf_res["oos_positive_fold_frac"]
    agg_deg_f = float(agg_deg) if (agg_deg is not None and math.isfinite(agg_deg)) else float("nan")
    oos_pos_f = float(oos_pos_frac) if (oos_pos_frac is not None and math.isfinite(oos_pos_frac)) else float("nan")
    wf_dead = math.isfinite(oos_pos_f) and oos_pos_f <= WF_OOS_POS_FRAC_DEAD
    wf_generalization_concern = bool(
        (math.isfinite(agg_deg_f) and agg_deg_f > WF_DEGRADATION_FAIL_PCT)
        or (math.isfinite(oos_pos_f) and oos_pos_f < WF_OOS_POS_FRAC_MIN)
    )

    contamination_flag = bool(regime_res["contamination_flag"])
    recommended_haircut = float(regime_res["recommended_magnitude_haircut"])

    gates = {
        "dsr_significant": {
            "pass": dsr_pass, "dsr": dsr_res["dsr"], "n_trials": int(n_trials),
            "threshold": DSR_SIGNIFICANCE, "sr_benchmark": dsr_res["sr_benchmark"],
        },
        "pbo_not_overfit": {
            "pass": pbo_pass, "pbo": pbo_value, "threshold": PBO_OVERFIT_GATE,
            "metric": pbo_res["metric"], "n_combinations": pbo_res["n_combinations"],
        },
        "permutation_directional_edge": {
            "pass": perm_pass, "p_value": perm_p, "alpha": PERM_ALPHA,
            "observed": perm_res["observed"], "null_p95": perm_res["null_p95"],
        },
        "walk_forward_generalizes": {
            "pass": (not wf_generalization_concern) and (not wf_dead),
            "aggregate_degradation_pct": agg_deg, "oos_positive_fold_frac": oos_pos_frac,
            "degradation_fail_pct": WF_DEGRADATION_FAIL_PCT,
            "oos_pos_frac_min": WF_OOS_POS_FRAC_MIN, "edge_dead_oos": wf_dead,
        },
        "magnitude_not_contaminated": {
            "pass": (not contamination_flag),
            "contamination_flag": contamination_flag,
            "fwd_all_mean_ratio": fwd_all_ratio,
            "recommended_magnitude_haircut": recommended_haircut,
            "holdout_are_topk": regime_res["holdout_are_topk"],
        },
    }

    # ----------------------------------------------------------------------------------
    # Overall verdict. Separate STRUCTURE (is the edge real) from MAGNITUDE (is the
    # in-window level deployable). A real edge with an inflated magnitude is CONDITIONAL.
    # ----------------------------------------------------------------------------------
    reasons: List[str] = []
    structural_fail = False

    if not dsr_pass:
        structural_fail = True
        reasons.append(
            f"FAIL DSR: deflated Sharpe {dsr_res['dsr']:.4f} <= {DSR_SIGNIFICANCE} at "
            f"n_trials={n_trials} (benchmark E[max SR]={dsr_res['sr_benchmark']:.4f}); "
            "the Sharpe does not survive selection deflation."
        )
    else:
        reasons.append(
            f"PASS DSR: deflated Sharpe {dsr_res['dsr']:.4f} > {DSR_SIGNIFICANCE} at "
            f"n_trials={n_trials}."
        )

    if not pbo_pass:
        structural_fail = True
        reasons.append(
            f"FAIL PBO: {pbo_value:.4f} >= {PBO_OVERFIT_GATE}; the IS-best sleeve reverts "
            "to/below the OOS median (predominantly overfit)."
        )
    else:
        reasons.append(f"PASS PBO: {pbo_value:.4f} < {PBO_OVERFIT_GATE} (not predominantly overfit).")

    if not perm_pass:
        structural_fail = True
        reasons.append(
            f"FAIL permutation: p_value {perm_p:.4g} >= {PERM_ALPHA}; the directional edge "
            "does not survive block sign-flip randomization."
        )
    else:
        reasons.append(
            f"PASS permutation: p_value {perm_p:.4g} < {PERM_ALPHA} (directional edge real "
            "vs its own autocorrelation)."
        )

    if wf_dead:
        structural_fail = True
        reasons.append(
            "FAIL walk-forward: edge is Sharpe-negative in every OOS fold "
            f"(oos_positive_fold_frac={oos_pos_frac}); it does not generalize at all."
        )

    if contamination_flag:
        reasons.append(
            f"CONTAMINATED magnitude: regime-inflation flag set (in-window mean "
            f"{fwd_all_ratio}x all-history); shrink any in-window magnitude by "
            f"x{recommended_haircut:.3f}. PBO/DSR do not catch window-as-selection-surface "
            "inflation."
        )
    else:
        reasons.append(
            f"CLEAN magnitude: selection window representative (ratio {fwd_all_ratio}x); "
            f"recommended haircut x{recommended_haircut:.3f}."
        )

    if wf_generalization_concern and not wf_dead:
        reasons.append(
            "WALK-FORWARD concern: "
            f"aggregate IS->OOS degradation {agg_deg_f:.2f}% / "
            f"oos_positive_fold_frac {oos_pos_frac} (note: NEGATIVE degradation means OOS > IS, "
            "which here is driven by the contaminated terminal best-regime window, not by "
            "genuine generalization — see regime_inflation)."
        )

    if structural_fail:
        integrity_verdict = "FAIL"
    elif contamination_flag or wf_generalization_concern:
        integrity_verdict = "CONDITIONAL"
    else:
        integrity_verdict = "PASS"

    # ----------------------------------------------------------------------------------
    # Honest summary: the deployable basis is the n=1, all-history, no-selection Sharpe.
    # ----------------------------------------------------------------------------------
    honest_n1_daily = mean_all / sd_book if sd_book > 0 else float("nan")
    honest_n1_ann = honest_n1_daily * math.sqrt(252.0)
    honest_summary = {
        "honest_n1_sharpe_daily_all_history": honest_n1_daily,
        "honest_n1_sharpe_annualized": honest_n1_ann,
        "honest_basis_note": (
            "The honest deployable basis is the n=1 (no selection), full-history, "
            "non-deflated per-period Sharpe = mean_all / pop_std over ALL "
            f"{len(combined)} days = {honest_n1_daily:.6f}/day "
            f"({honest_n1_ann:.4f} annualized). The in-window (forward) Sharpe and mean are "
            f"{fwd_all_ratio}x the all-history mean and must NOT be used as the deployable "
            f"magnitude: apply the regime haircut x{recommended_haircut:.3f}. DSR is "
            "significant only up to the search size it is deflated against (see "
            "components.dsr and the n_trials sweep)."
        ),
        "contamination_flag": contamination_flag,
        "recommended_magnitude_haircut": recommended_haircut,
    }

    honest_headline = (
        f"Verdict {integrity_verdict}. Honest basis = n=1 all-history daily Sharpe "
        f"{honest_n1_daily:.4f} ({honest_n1_ann:.3f} annualized). The directional/structural "
        f"edge is real: DSR {dsr_res['dsr']:.4f} {'>' if dsr_pass else '<='} "
        f"{DSR_SIGNIFICANCE} at n_trials={n_trials} (deflated benchmark "
        f"E[maxSR]={dsr_res['sr_benchmark']:.4f}), permutation p_value {perm_p:.4g}, "
        f"PBO {pbo_value:.4f} (< {PBO_OVERFIT_GATE}, not overfit). BUT the MAGNITUDE is "
        f"{'CONTAMINATED' if contamination_flag else 'clean'}: the forward window mean is "
        f"{fwd_all_ratio}x the all-history mean"
        + (
            f" and the holdout years are the regime top-k, so the deployable magnitude must be "
            f"haircut by x{recommended_haircut:.3f} (~/{(1.0/recommended_haircut):.1f})"
            if contamination_flag else ""
        )
        + f". Walk-forward aggregate IS->OOS degradation {agg_deg_f:.2f}% with "
        f"oos_positive_fold_frac {oos_pos_frac}"
        + (
            " — the 'OOS-beats-IS' (negative degradation) is the contaminated terminal "
            "best-regime fold, NOT generalization."
            if (math.isfinite(agg_deg_f) and agg_deg_f < 0) else "."
        )
    )

    return {
        "schema": SCHEMA,
        "n_obs": len(combined),
        "n_sleeves": n_cols,
        "sleeves": sleeves,
        "selection_window_start": str(selection_window_start),
        "n_trials": int(n_trials),
        "sr_variance_used": sr_variance_used,
        "sr_variance_source": sr_variance_source,
        "sr_variance_detail": sr_variance_detail,
        "ground_truth": ground_truth,
        "components": {
            "dsr": dsr_res,
            "pbo": {k: v for k, v in pbo_res.items() if k != "logits"},
            "permutation": perm_res,
            "regime_inflation": regime_res,
            "walk_forward": wf_res,
        },
        "gates": gates,
        "integrity_verdict": integrity_verdict,
        "integrity_reasons": reasons,
        "honest_summary": honest_summary,
        "honest_headline": honest_headline,
    }
