"""regime_inflation.py — REGIME-INFLATION / WINDOW-CONTAMINATION diagnostic.

THE NOVEL, LOAD-BEARING GATE. PBO and DSR test whether *a strategy* beats *a benchmark*
on a *given* sample. They provably MISS the failure mode that wrecked the magnitude estimate
of the 11-sleeve book: the SELECTION WINDOW ITSELF is the contamination. When the period you
score against (and select / size / publish a forward table off) is a best-N-years regime AND
the holdout years are the very top of the whole history, the in-window magnitude is inflated
in a way that survives PBO (combinatorial reshuffles of the SAME contaminated window keep the
contamination) and survives DSR (DSR deflates the strategy's Sharpe for multiple testing, not
the *window's* representativeness vs the long-run basis).

The 2026-06-15 reality-check audit proved this on the book: structural pass-rate is REAL, but
the return/speed MAGNITUDE is ~3x INFLATED, while PBO=13.5% and DSR>0.92 did NOT flag it. This
module makes that failure mode mechanical and reproducible.

WHAT IT MEASURES (each an independent angle on "the window is not the deployable basis"):
  1. fwd_all_mean_ratio       in-window mean / all-history mean. The headline inflation factor.
  2. per-year structure       per-year means, dispersion, and whether the holdout years are the
                              literal top-k of ALL years by mean (the cleanest contamination tell).
  3. topk_day_concentration   share of NET and of POSITIVE in-window PnL carried by the top
                              {10,20,50} days — outlier fragility that MC-resamples into every
                              projection (a few days drive the whole forward table).
  4. selection_surface_penalty  the OVER-AND-ABOVE-DSR penalty: treat the window as a surface that
                              n_trials candidates were scored against keeping the best, and charge
                              the expected max-of-N Sharpe (Bailey & Lopez de Prado, "The Sharpe
                              Ratio Efficient Frontier" / False Strategy Theorem) as a multiplicative
                              haircut on the in-window mean. The cross-trial SR variance is estimated
                              from the cross-PERIOD (per-year) SR dispersion, deconvolved for
                              finite-sample SR estimation noise (Lo 2002 SR standard error) so thin
                              partial years and pure sampling jitter do not masquerade as real
                              regime heterogeneity.
  5. recommended_magnitude_haircut  one honest multiplier to apply to ANY in-window magnitude.
                              The most conservative of the regime basis (shrink the window to the
                              all-history mean) and the selection-surface penalty — i.e. take the
                              LARGER inflation, never the product, so overlapping effects are not
                              double-counted. Reproduces ~1/3 for the contaminated book and ~1.0 for
                              a clean, representative window.

Pure-stdlib math (math.erf + a numerically-stable inverse via Acklam + one Halley step). No hard
scipy dependency. This is a measurement gate that decides what real money trades, so it ships with
a known-answer test (tests/research_infra/test_vig_regime_inflation.py).

A SIGN DEFECT LIVED HERE FROM AUTHORSHIP UNTIL 2026-07-29 (B451). READ THIS BEFORE TRUSTING
AN OLD `contamination_flag`.
----------------------------------------------------------------------------------------------
Metric 1 is a RATIO, and a ratio of two means is only a multiple when the denominator is
positive. Every threshold in this module was written as `ratio >= 1.5` — a positive test. Once
the all-history mean went negative the ratio went negative, the flag became structurally
unreachable, and `recommended_magnitude_haircut` fell to its no-op 1.0 branch. **The detector
was therefore defeated monotonically by making the concealed loss bigger**, which is the exact
inverse of what it is for: an adversarial refuter hid 50,000 losing trades, measured
`fwd_all_mean_ratio = -0.847`, `contamination_flag = False`, and a verdict string that read
"CLEAN: selection window is representative". Same family as F39 (a cost term credited with the
wrong sign).

The fix does not touch `fwd_all_mean_ratio` — it is a published field and redefining it would
silently change every reader. What changed:

  * the ratio thresholds apply only when `mean_all > 0` (`ratio_is_a_multiple`);
  * `mean_win > 0 >= mean_all` is now its OWN contamination class
    (`sign_flip_contamination`), because a scored window that is positive while the sleeve's own
    history is not is the strongest available evidence of window-as-selection-surface, not the
    absence of it;
  * in that class the regime haircut goes to `_HAIRCUT_FLOOR` instead of 1.0;
  * a window whose own mean is non-positive reports CLEAN **vacuously**, and says so, because
    there is no optimistic inflation to detect;
  * every result carries `inflation_basis` so a downstream reader cannot re-apply a bare
    `>= 1.5` test without seeing which regime it is in.

Callers that guarded this defect at their own call site (`walkforward/gate.py`) are now
redundant rather than load-bearing, and their guard doubles as a cross-check.
"""
from __future__ import annotations

import datetime as _dt
import math
import statistics
from collections import defaultdict

__all__ = [
    "regime_inflation_diagnostic",
    "expected_max_sharpe",
    "expected_max_z",
    "norm_cdf",
    "norm_ppf",
]

_EULER_GAMMA = 0.5772156649015328606
_RATIO_FLAG = 1.5            # fwd/all mean ratio at/above which the window is a red flag
_RATIO_HOLDOUT_GATE = 1.2    # holdout-are-topk only counts as contamination above this ratio
_DEFAULT_MIN_YEAR_DAYS = 30  # a year needs this many obs to inform cross-period SR variance
_TOPK = (10, 20, 50)
_HAIRCUT_FLOOR = 0.05        # never claim a strategy's deployable magnitude is literally ~0


# ----------------------------------------------------------------------------------------------
# Normal CDF / inverse-CDF (stdlib only)
# ----------------------------------------------------------------------------------------------
def norm_cdf(x: float) -> float:
    """Standard-normal CDF via math.erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_ppf(p: float) -> float:
    """Standard-normal inverse-CDF (quantile). Acklam rational approximation refined by one
    Halley step against math.erf; accurate to ~1e-15 on (0,1). Raises on p outside (0,1)."""
    if not (0.0 < p < 1.0):
        raise ValueError(f"norm_ppf requires 0<p<1, got {p}")
    # Acklam coefficients
    a = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00)
    b = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00)
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00)
    plow, phigh = 0.02425, 1.0 - 0.02425
    if p < plow:
        q = math.sqrt(-2.0 * math.log(p))
        x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    elif p <= phigh:
        q = p - 0.5
        r = q * q
        x = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
            (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)
    else:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        x = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    # one Halley refinement step
    e = norm_cdf(x) - p
    u = e * math.sqrt(2.0 * math.pi) * math.exp(x * x / 2.0)
    x = x - u / (1.0 + x * u / 2.0)
    return x


# ----------------------------------------------------------------------------------------------
# Expected maximum of N standard normals / N Sharpe estimates (False Strategy Theorem)
# ----------------------------------------------------------------------------------------------
def expected_max_z(n_trials: int) -> float:
    """E[max of N i.i.d. standard normals], Bailey & Lopez de Prado approximation:
        (1-gamma)*Z^-1(1 - 1/N) + gamma*Z^-1(1 - 1/(N*e)).
    Returns 0.0 for N<=1 (no selection -> no expected-max inflation)."""
    n = int(n_trials)
    if n <= 1:
        return 0.0
    return ((1.0 - _EULER_GAMMA) * norm_ppf(1.0 - 1.0 / n)
            + _EULER_GAMMA * norm_ppf(1.0 - 1.0 / (n * math.e)))


def expected_max_sharpe(n_trials: int, sr_variance: float) -> float:
    """Expected best-of-N Sharpe achievable by pure selection luck, given cross-trial SR variance:
        E[max SR] = expected_max_z(N) * sqrt(sr_variance).
    This is the benchmark a selected strategy/window must clear to claim a real (non-selection) SR."""
    v = max(0.0, float(sr_variance))
    return expected_max_z(n_trials) * math.sqrt(v)


# ----------------------------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------------------------
def _to_date(x) -> _dt.date:
    if isinstance(x, _dt.datetime):
        return x.date()
    if isinstance(x, _dt.date):
        return x
    if isinstance(x, str):
        return _dt.date.fromisoformat(x[:10])
    raise TypeError(f"unsupported date type {type(x)!r}: {x!r}")


def _sharpe(vals) -> float | None:
    """Per-observation Sharpe (mean/pop-std). None if undefined (n<2 or zero std)."""
    if len(vals) < 2:
        return None
    sd = statistics.pstdev(vals)
    if sd <= 0:
        return None
    return statistics.fmean(vals) / sd


def _estimate_sr_variance(per_year_vals: dict, min_year_days: int) -> dict:
    """Method-of-moments estimate of the TRUE cross-period (per-year) Sharpe variance.

    observed cross-year SR variance = true between-year SR variance + mean finite-sample SR
    estimation variance. Lo (2002): Var(SR_hat) ~ (1 + 0.5*SR^2)/T for ~i.i.d. returns. We subtract
    that average estimation variance so sampling jitter and thin partial years do not inflate the
    cross-period dispersion. Returns the deconvolved variance (>=0) plus the components used."""
    full = {y: v for y, v in per_year_vals.items() if len(v) >= min_year_days}
    srs, estv, nday = {}, {}, {}
    for y, v in full.items():
        sr = _sharpe(v)
        if sr is None:
            continue
        srs[y] = sr
        estv[y] = (1.0 + 0.5 * sr * sr) / len(v)
        nday[y] = len(v)
    if len(srs) < 2:
        return dict(sr_variance=0.0, v_observed=0.0, mean_est_variance=0.0,
                    n_full_years=len(srs), per_year_sharpe={y: round(s, 5) for y, s in srs.items()},
                    note="insufficient full years (<2) to estimate cross-period SR variance")
    v_obs = statistics.variance(list(srs.values()))          # sample variance across years
    mean_estv = statistics.fmean([estv[y] for y in srs])
    v_true = max(0.0, v_obs - mean_estv)
    return dict(sr_variance=v_true, v_observed=v_obs, mean_est_variance=mean_estv,
                n_full_years=len(srs),
                per_year_sharpe={y: round(s, 5) for y, s in srs.items()},
                note="deconvolved (Lo-2002 estimation-noise corrected)")


def _topk_concentration(window_vals) -> dict:
    """Share of NET and of POSITIVE in-window PnL carried by the top-k days, k in {10,20,50}."""
    desc = sorted(window_vals, reverse=True)
    net = sum(window_vals)
    pos = sum(v for v in window_vals if v > 0)
    out = {}
    for k in _TOPK:
        kk = min(k, len(desc))
        topsum = sum(desc[:kk])
        out[str(k)] = dict(
            k_used=kk,
            net_share=(round(topsum / net, 5) if net != 0 else None),
            positive_share=(round(topsum / pos, 5) if pos > 0 else None),
        )
    return out


# ----------------------------------------------------------------------------------------------
# main diagnostic
# ----------------------------------------------------------------------------------------------
def regime_inflation_diagnostic(dated_series, selection_window_start, n_trials,
                                sr_variance=None, min_year_days=_DEFAULT_MIN_YEAR_DAYS) -> dict:
    """Regime-inflation / window-contamination diagnostic.

    Parameters
    ----------
    dated_series : list[(date | iso-str, float)]
        Per-period (typically daily) returns with their dates.
    selection_window_start : date | iso-str
        Start (inclusive) of the selection / holdout / forward window that was scored against.
    n_trials : int
        Number of candidate evaluations scored against this same window keeping the best.
    sr_variance : float, optional
        Cross-trial Sharpe variance for the selection-surface penalty. If None it is estimated
        from per-year SR dispersion (deconvolved for finite-sample SR estimation noise).
    min_year_days : int
        Minimum observations for a year to inform the cross-period SR variance estimate.

    Returns a dict with: fwd_all_mean_ratio, per_year_mean, year_dispersion, holdout_years,
    holdout_years_rank, holdout_are_topk, topk_day_concentration, selection_surface_penalty,
    recommended_magnitude_haircut, contamination_flag, verdict, plus transparency sub-fields.
    """
    if not dated_series:
        raise ValueError("dated_series is empty")
    start = _to_date(selection_window_start)

    pairs = [(_to_date(d), float(r)) for d, r in dated_series]
    all_vals = [r for _, r in pairs]
    win_vals = [r for d, r in pairs if d >= start]
    if not win_vals:
        raise ValueError(f"no observations on/after selection_window_start={start}")

    mean_all = statistics.fmean(all_vals)
    mean_win = statistics.fmean(win_vals)

    # --- 1. headline inflation ratio -------------------------------------------------------------
    fwd_all_mean_ratio = (mean_win / mean_all) if mean_all != 0 else float("inf")

    # --- 2. per-year structure -------------------------------------------------------------------
    by_year = defaultdict(list)
    for d, r in pairs:
        by_year[d.year].append(r)
    per_year_mean = {y: statistics.fmean(v) for y, v in sorted(by_year.items())}
    pym_vals = list(per_year_mean.values())
    ymax, ymin = max(pym_vals), min(pym_vals)
    year_dispersion = (ymax / ymin) if ymin != 0 else float("inf")  # literal max/min as requested

    holdout_years = sorted({d.year for d, _ in pairs if d >= start})

    # rank = 1 + (# years with STRICTLY greater mean). Ties share a rank.
    holdout_years_rank = {
        y: 1 + sum(1 for o, m in per_year_mean.items() if m > per_year_mean[y])
        for y in holdout_years
    }
    # holdout_are_topk: holdout years occupy the k highest means AND there is a strict gap to the
    # (k+1)-th year (so an all-equal "clean" history never trips it).
    k = len(holdout_years)
    n_years = len(per_year_mean)
    years_by_mean = sorted(per_year_mean, key=lambda y: per_year_mean[y], reverse=True)
    if 0 < k < n_years:
        gap = per_year_mean[years_by_mean[k - 1]] > per_year_mean[years_by_mean[k]]
        holdout_are_topk = bool(gap and set(years_by_mean[:k]) == set(holdout_years))
    elif k == n_years:
        holdout_are_topk = False  # window spans every year -> no contrast
    else:
        holdout_are_topk = False

    # --- 3. top-day concentration (in-window outlier fragility) -----------------------------------
    topk_day_concentration = _topk_concentration(win_vals)

    # --- 4. selection-surface penalty (over-and-above DSR) ---------------------------------------
    if sr_variance is None:
        srv = _estimate_sr_variance(by_year, min_year_days)
        sr_variance_used = srv["sr_variance"]
        sr_variance_source = "estimated_from_per_year_dispersion"
    else:
        srv = dict(sr_variance=float(sr_variance), v_observed=None, mean_est_variance=None,
                   n_full_years=None, per_year_sharpe=None, note="supplied")
        sr_variance_used = float(sr_variance)
        sr_variance_source = "supplied"

    sr_window = _sharpe(win_vals)
    emax_sr = expected_max_sharpe(n_trials, sr_variance_used)
    if sr_window is None or sr_window <= 0:
        # window has no positive Sharpe -> selection inflation is not the operative risk here
        selection_surface_penalty = 1.0
    else:
        selection_surface_penalty = max(0.0, 1.0 - emax_sr / sr_window)

    # --- 4b. THE SIGN DEFECT, fixed 2026-07-29 (B451) ---------------------------------------------
    # `fwd_all_mean_ratio = mean_win / mean_all` is only a multiple when `mean_all > 0`. Once the
    # full-history mean goes NEGATIVE the ratio goes negative, every downstream test of the form
    # `ratio >= 1.5` becomes unreachable, and the haircut branch below fell to its no-op 1.0 arm.
    # So the detector was defeated MONOTONICALLY by making the concealed loss bigger: an
    # adversarial refuter in Session W hid 50,000 losing trades, got `ratio = -0.847`,
    # `contamination_flag = False`, and a verdict string that still read "CLEAN: selection window
    # is representative". Same sign-error family as F39.
    #
    # A negative ratio is not the absence of contamination. It is the STRONGEST form of the thing
    # this module exists to catch — the scored window is positive while the sleeve's own history
    # is not — so it is flagged here and haircut to the floor. Session W guarded its own call site
    # (`walkforward/gate.py:248-257`); this is the module fix that guard was standing in for, and
    # the guard is now redundant rather than load-bearing.
    #
    # `fwd_all_mean_ratio` itself is left exactly as it was: it is a published field and rounding
    # it into a different quantity would break every reader. What changes is that its
    # INTERPRETATION is now explicit, in `inflation_basis`, and no threshold is applied to it in a
    # regime where the comparison is meaningless.
    ratio_is_a_multiple = mean_all > 0
    window_positive_history_not = (mean_win > 0) and (mean_all <= 0)
    # Branch on the WINDOW's sign first. Amended 2026-07-30 (AE, B873) while closing FOURTH_REVIEW
    # section 4.3: the previous order tested `ratio_is_a_multiple` first, so a positive history with a
    # LOSING window (mean_all +0.22, mean_win -0.10) was published as `ratio_of_positive_means`
    # when only the denominator was positive, and its verdict read "CLEAN: selection window is
    # representative" of a window 145 % below the history it is compared against. Neither
    # `contamination_flag` nor `recommended_magnitude_haircut` reads this field or this order --
    # both key off `ratio_is_a_multiple` / `window_positive_history_not` directly -- so no verdict
    # moves; what changes is that a published label stops describing the wrong regime.
    if mean_win <= 0:
        inflation_basis = "window_nonpositive_no_optimistic_inflation"
    elif ratio_is_a_multiple:
        inflation_basis = "ratio_of_positive_means"
    else:
        inflation_basis = "sign_flip_window_positive_history_nonpositive"

    # --- 5. recommended magnitude haircut --------------------------------------------------------
    # regime basis: shrink the in-window mean to the all-history mean (never haircut UP).
    if ratio_is_a_multiple and math.isfinite(fwd_all_mean_ratio) and fwd_all_mean_ratio > 0:
        regime_basis_haircut = 1.0 / max(1.0, fwd_all_mean_ratio)
    elif window_positive_history_not:
        # The all-history mean is the deployable basis and it is <= 0. There is no positive
        # multiple to shrink BY, and 1.0 (the old branch) says "deploy the window magnitude in
        # full", which is the exact opposite of the correct answer.
        regime_basis_haircut = _HAIRCUT_FLOOR
    else:
        regime_basis_haircut = 1.0
    # combine WITHOUT double-counting: take the larger inflation = the more conservative haircut.
    recommended_magnitude_haircut = max(
        _HAIRCUT_FLOOR, min(regime_basis_haircut, selection_surface_penalty))
    # WHICH TERM BINDS, AND WHETHER THE NUMBER IS MEASURED OR CLAMPED. Added 2026-07-30 (Session AU,
    # B1560) on the first receipt in this programme to publish this field beside a headline. The
    # combination above is a `min` under a floor, so `recommended_magnitude_haircut` alone cannot tell
    # a reader whether it is a REGIME statement, a SELECTION-SURFACE statement, or the floor. On the
    # estate's standing admission (`mx_btcusd @ target_5R`, RECORDED/mid) it reads 0.05, and the
    # decomposition is the whole story: regime basis 0.835, selection-surface penalty **0.0** because
    # the expected max-of-128 Sharpe (0.551) exceeds the arm's own window Sharpe (0.323). So the
    # published 0.05 is the FLOOR, not a measurement -- and quoting it as "shrink by 20x" would be as
    # wrong as quoting it as "~1.0".
    _binding = ("selection_surface" if selection_surface_penalty < regime_basis_haircut
                else ("regime_basis" if regime_basis_haircut < 1.0 else "none"))
    _at_floor = recommended_magnitude_haircut <= _HAIRCUT_FLOOR + 1e-12
    # ...and the RESOLUTION of the selection-surface term, which is the same class of caveat AO made
    # binding for permutation p-values: a penalty computed from a cross-period SR variance estimated
    # on two full years is not a measurement of anything. The value is NOT changed -- changing it
    # would move every published verdict -- only its evaluability is stated.
    _srv_years = int((srv or {}).get("n_full_years") or 0)
    _ss_evaluable = (sr_variance_source != "estimated_from_per_year_dispersion") or _srv_years >= 3

    # --- flag + verdict --------------------------------------------------------------------------
    ratio_red = (ratio_is_a_multiple and math.isfinite(fwd_all_mean_ratio)
                 and fwd_all_mean_ratio >= _RATIO_FLAG)
    sign_red = window_positive_history_not
    holdout_red = (holdout_are_topk and n_years >= 3
                   and (sign_red
                        or (ratio_is_a_multiple and math.isfinite(fwd_all_mean_ratio)
                            and fwd_all_mean_ratio >= _RATIO_HOLDOUT_GATE)))
    contamination_flag = bool(ratio_red or sign_red or holdout_red)

    top50 = topk_day_concentration["50"]["positive_share"]
    if contamination_flag:
        reasons = []
        if sign_red:
            reasons.append(
                f"the scored window mean is POSITIVE ({mean_win:+.6g}) while the full-history "
                f"mean is not ({mean_all:+.6g}); the ratio {fwd_all_mean_ratio:.2f} is not a "
                f"multiple and no ratio threshold can fire on it")
        if ratio_red:
            reasons.append(f"in-window mean is {fwd_all_mean_ratio:.2f}x the all-history mean")
        if holdout_red:
            reasons.append(
                f"holdout years {holdout_years} are the top-{k} of {n_years} by mean")
        if top50 is not None and top50 >= 0.5:
            reasons.append(f"top-50 window days = {top50*100:.1f}% of positive PnL (outlier-fragile)")
        verdict = (
            "CONTAMINATED: " + "; ".join(reasons)
            + f". Shrink any in-window magnitude by x{recommended_magnitude_haircut:.3f} "
            f"(~/{(1.0/recommended_magnitude_haircut):.1f}) toward the deployable basis. "
            "PBO/DSR do not catch window-as-selection-surface inflation.")
    elif inflation_basis == "window_nonpositive_no_optimistic_inflation":
        why = (f"the all-history mean is {mean_all:+.6g}, so the ratio {fwd_all_mean_ratio:.2f} is "
               "not a multiple either" if mean_all <= 0 else
               f"the all-history mean is {mean_all:+.6g}, so the window UNDERPERFORMS its own "
               f"history (ratio {fwd_all_mean_ratio:.2f}) rather than being representative of it")
        verdict = (
            f"CLEAN (vacuously): the scored window mean is not positive ({mean_win:+.6g}), so "
            f"there is no optimistic inflation to detect — {why}. No ratio threshold was applied. "
            "This is not a statement that the sleeve is fine.")
    else:
        # The "(~1.0)" this branch used to print was HARDCODED beside an interpolated value, so an arm
        # whose haircut had fallen to the 0.05 floor published the sentence
        # `recommended magnitude haircut x0.050 (~1.0)` -- a 20x misstatement inside the sentence that
        # quotes the number, and it landed on the estate's standing admission. Same class as the
        # PARTIAL UNIVERSE stamp AP repaired in `gate.py`: prose asserting something the fields it
        # sits beside contradict. Fixed 2026-07-30 (Session AU, B1560); no field's VALUE moved.
        if _at_floor:
            tail = (f"recommended magnitude haircut x{recommended_magnitude_haircut:.3f}, which is "
                    f"the FLOOR and not a measurement: the binding term is "
                    f"{_binding} (regime basis x{regime_basis_haircut:.3f}, selection-surface "
                    f"penalty x{selection_surface_penalty:.3f})"
                    + ("" if _ss_evaluable else
                       f" -- and that penalty rests on a cross-period SR variance estimated from "
                       f"{_srv_years} full year(s), so it is NOT_EVALUABLE_AT_THIS_RESOLUTION")
                    + ". Do not read the floor as 'shrink 20x' NOR as '~1.0'.")
        elif recommended_magnitude_haircut >= 0.95:
            tail = (f"recommended magnitude haircut "
                    f"x{recommended_magnitude_haircut:.3f} (~1.0).")
        else:
            tail = (f"recommended magnitude haircut x{recommended_magnitude_haircut:.3f} "
                    f"(~/{(1.0 / recommended_magnitude_haircut):.1f}) on the {_binding} basis -- a "
                    f"representative window can still carry a magnitude haircut, and this one does.")
        verdict = (
            f"CLEAN: selection window is representative (mean ratio {fwd_all_mean_ratio:.2f}x); "
            f"holdout years not regime-extreme; " + tail)

    return dict(
        fwd_all_mean_ratio=round(fwd_all_mean_ratio, 5) if math.isfinite(fwd_all_mean_ratio) else None,
        #: Which regime `fwd_all_mean_ratio` was read in. A reader that applies a `>= 1.5`
        #: test to the ratio without checking this is reproducing the defect fixed in B451.
        inflation_basis=inflation_basis,
        ratio_is_a_multiple=bool(ratio_is_a_multiple),
        sign_flip_contamination=bool(window_positive_history_not),
        mean_in_window=round(mean_win, 6),
        mean_all=round(mean_all, 6),
        n_obs=len(all_vals),
        n_obs_in_window=len(win_vals),
        per_year_mean={y: round(m, 5) for y, m in per_year_mean.items()},
        year_dispersion=round(year_dispersion, 4) if math.isfinite(year_dispersion) else None,
        year_mean_max=round(ymax, 5),
        year_mean_min=round(ymin, 5),
        holdout_years=holdout_years,
        holdout_years_rank=holdout_years_rank,
        holdout_are_topk=holdout_are_topk,
        n_total_years=n_years,
        topk_day_concentration=topk_day_concentration,
        selection_surface_penalty=round(selection_surface_penalty, 5),
        selection_surface_detail=dict(
            sr_window=(round(sr_window, 5) if sr_window is not None else None),
            n_trials=int(n_trials),
            expected_max_z=round(expected_max_z(n_trials), 5),
            expected_max_sharpe=round(emax_sr, 5),
            sr_variance_used=round(sr_variance_used, 6),
            sr_variance_source=sr_variance_source,
            sr_variance_estimate=srv,
        ),
        regime_basis_haircut=round(regime_basis_haircut, 5),
        recommended_magnitude_haircut=round(recommended_magnitude_haircut, 5),
        #: Which of the two terms produced the haircut, whether it is the floor rather than a
        #: measurement, and whether the selection-surface term had the resolution to say anything.
        #: A reader quoting `recommended_magnitude_haircut` without these three is quoting a `min`
        #: under a clamp as though it were an estimate (Session AU, B1560).
        haircut_binding_term=_binding,
        haircut_at_floor=bool(_at_floor),
        selection_surface_evaluable=bool(_ss_evaluable),
        contamination_flag=contamination_flag,
        verdict=verdict,
    )
