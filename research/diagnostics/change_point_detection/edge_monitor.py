"""
EdgeMonitor — Live Change-Point Detection for GTOS Trading Edge
================================================================
edge_monitor.py

Monitors the binary win/loss stream for evidence of edge decay using
three complementary detectors:

  • Shiryaev-Roberts (SR)  — minimax-optimal sequential alarm
  • CUSUM                  — classic cumulative-sum detector
  • BOCPD                  — Bayesian posterior on current win rate

Role in GTOS monitoring stack
------------------------------
  SPRT        — instrument kill switch (binary accept/reject, in src/)
  SR / CUSUM  — continuous early warning ("something may have changed")
  BOCPD       — full posterior estimate of current win rate

IMPORTANT: Alarms trigger HUMAN REVIEW, not automatic position changes.

Usage
-----
    from edge_monitor import EdgeMonitor

    monitor = EdgeMonitor(
        p0=0.62,
        p1=0.50,
        sr_threshold=490.0,    # from calibrate_detectors_v1.py
        cusum_threshold=4.4816, # from calibrate_detectors_v1.py
        bocpd_hazard=1/200,
    )

    result = monitor.update(outcome=True)   # True=win, False=loss
    print(monitor.get_dashboard())

Dependencies: numpy, scipy  (standard scientific Python)

Author: Claude Code
Date:   2026-04-11
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy.special import logsumexp


# ─────────────────────────────────────────────────────────────
# DEFAULT CALIBRATED THRESHOLDS
# (from calibrate_detectors_v1.py, p₁=0.50, ARL_target=500)
# ─────────────────────────────────────────────────────────────

# From calibrate_detectors_v1.py  (p₁=0.50, ARL_target=500, seed=42)
_DEFAULT_SR_THRESHOLD    = 453.61  # ARL verified: 510 trades ≈ 30 months
_DEFAULT_CUSUM_THRESHOLD = 2.6996  # ARL verified: 499 trades ≈ 29 months


# ─────────────────────────────────────────────────────────────
# SHIRYAEV-ROBERTS DETECTOR
# ─────────────────────────────────────────────────────────────

class SRDetector:
    """
    Shiryaev-Roberts sequential change-point detector for Bernoulli stream.

    Statistic: R₀ = 0,  Rₙ = (1 + Rₙ₋₁) · Lₙ
    Alarm:     Rₙ ≥ A

    Lₙ = (p₁/p₀)    if outcome = win
         (1-p₁)/(1-p₀) if outcome = loss

    SR is minimax-optimal for detecting an unknown changepoint time
    (Shiryaev 1963, Pollak 1985). Use it as the primary alarm.
    """

    def __init__(self, p0: float, p1: float, threshold: float):
        if not (0 < p1 < p0 < 1):
            raise ValueError(f"Require 0 < p1 < p0 < 1, got p0={p0}, p1={p1}")
        self.p0 = p0
        self.p1 = p1
        self.threshold = threshold

        self._L_win  = p1 / p0
        self._L_loss = (1.0 - p1) / (1.0 - p0)

        self.R: float = 0.0
        self.n_obs:   int = 0
        self.n_alarms: int = 0

        self._statistic_history: list[float] = []

    def update(self, outcome: bool) -> dict[str, Any]:
        """
        Process one outcome and return current state.

        Parameters
        ----------
        outcome : bool
            True = win, False = loss.

        Returns
        -------
        dict with keys:
            statistic : float   — current R value
            alarm     : bool    — True if R ≥ threshold
            pct       : float   — R / threshold (0..∞, alarm when ≥ 1.0)
        """
        L    = self._L_win if outcome else self._L_loss
        self.R = (1.0 + self.R) * L
        self.n_obs += 1
        self._statistic_history.append(self.R)

        alarming = self.R >= self.threshold
        if alarming:
            self.n_alarms += 1

        return {
            "statistic": self.R,
            "alarm":     alarming,
            "pct":       self.R / self.threshold,
        }

    def reset(self) -> None:
        """Reset SR statistic to 0 (call after operator review)."""
        self.R = 0.0

    @property
    def history(self) -> list[float]:
        return list(self._statistic_history)


# ─────────────────────────────────────────────────────────────
# CUSUM DETECTOR
# ─────────────────────────────────────────────────────────────

class CUSUMDetector:
    """
    CUSUM sequential change-point detector for Bernoulli stream.

    Statistic: S₀ = 0,  Sₙ = max(0, Sₙ₋₁ + log Lₙ)
    Alarm:     Sₙ ≥ h

    CUSUM is optimal when the changepoint time is known to occur before
    monitoring begins. Use it as a secondary confirmation alongside SR.
    """

    def __init__(self, p0: float, p1: float, threshold: float):
        if not (0 < p1 < p0 < 1):
            raise ValueError(f"Require 0 < p1 < p0 < 1, got p0={p0}, p1={p1}")
        self.p0 = p0
        self.p1 = p1
        self.threshold = threshold

        self._logL_win  = math.log(p1 / p0)
        self._logL_loss = math.log((1.0 - p1) / (1.0 - p0))

        self.S: float = 0.0
        self.n_obs:    int = 0
        self.n_alarms: int = 0

        self._statistic_history: list[float] = []

    def update(self, outcome: bool) -> dict[str, Any]:
        """
        Process one outcome and return current state.

        Returns
        -------
        dict with keys: statistic, alarm, pct
        """
        logL   = self._logL_win if outcome else self._logL_loss
        self.S = max(0.0, self.S + logL)
        self.n_obs += 1
        self._statistic_history.append(self.S)

        alarming = self.S >= self.threshold
        if alarming:
            self.n_alarms += 1

        return {
            "statistic": self.S,
            "alarm":     alarming,
            "pct":       self.S / self.threshold,
        }

    def reset(self) -> None:
        """Reset CUSUM statistic to 0."""
        self.S = 0.0

    @property
    def history(self) -> list[float]:
        return list(self._statistic_history)


# ─────────────────────────────────────────────────────────────
# BOCPD DETECTOR (Adams-MacKay 2007)
# ─────────────────────────────────────────────────────────────

class BOCPDDetector:
    """
    Bayesian Online Changepoint Detection with Beta-Bernoulli conjugate.

    Maintains a posterior distribution over the current run length r_t,
    where r_t = k means the current trading regime started k trades ago.

    This detector provides a continuous probability estimate rather than
    a binary alarm — it tells you *what the current win rate probably is*
    and *how likely a recent regime change is*.

    Parameters
    ----------
    alpha0, beta0 : float
        Beta prior hyperparameters.
        Prior mean = alpha0 / (alpha0 + beta0) should equal p₀.
        alpha0 + beta0 = prior effective sample size (confidence in prior).
        Default: alpha0=62, beta0=38 → prior mean=0.62, pseudo-count=100.
    hazard : float
        Changepoint probability per trade = 1/λ, where λ is the expected
        number of trades between regime changes.
        Default 1/200 → λ=200 trades ≈ 12 months at 17 trades/month.
    max_run_length : int
        Truncate the run-length distribution beyond this to bound memory.
        Set ≥ 3×λ to avoid significant probability loss.
    """

    def __init__(
        self,
        alpha0: float = 62.0,
        beta0:  float = 38.0,
        hazard: float = 1.0 / 200.0,
        max_run_length: int = 1500,
    ):
        self.alpha0 = alpha0
        self.beta0  = beta0
        self.hazard = hazard
        self.max_run_length = max_run_length

        # State vectors (grow by 1 per observation)
        # log P(r_t, x_{1:t}) for r_t = 0, 1, ..., t
        self._log_joint: np.ndarray = np.array([0.0])
        self._run_wins:  np.ndarray = np.array([0.0])  # wins in run
        self._run_n:     np.ndarray = np.array([0.0])  # run length

        self.n_obs: int = 0
        self._wr_history: list[float] = []
        self._cp10_history: list[float] = []
        self._last_state: dict[str, Any] = {}

    def update(self, outcome: bool) -> dict[str, Any]:
        """
        Process one outcome and return the full BOCPD state.

        Returns
        -------
        dict with keys:
            posterior_wr           : float  — E[win rate | data]
            change_prob_last_5     : float  — P(changepoint in last 5 trades)
            change_prob_last_10    : float  — P(changepoint in last 10 trades)
            change_prob_last_20    : float  — P(changepoint in last 20 trades)
            mode_run_length        : int    — most likely current run length
            lower_95_wr            : float  — 2.5th-pct credible bound on WR
            upper_95_wr            : float  — 97.5th-pct credible bound on WR
        """
        x = 1.0 if outcome else 0.0

        alpha = self.alpha0 + self._run_wins
        beta  = self.beta0  + self._run_n - self._run_wins
        totab = alpha + beta

        if outcome:
            log_pred       = np.log(alpha / totab)
            log_pred_prior = math.log(self.alpha0 / (self.alpha0 + self.beta0))
        else:
            log_pred       = np.log(beta / totab)
            log_pred_prior = math.log(self.beta0 / (self.alpha0 + self.beta0))

        log_total = float(logsumexp(self._log_joint))

        # Growth (no changepoint): run length r → r+1
        log_growth = math.log(1.0 - self.hazard) + self._log_joint + log_pred

        # Changepoint: run resets to 0
        log_cp = math.log(self.hazard) + log_total + log_pred_prior

        # Assemble new joint
        new_log_joint = np.concatenate([[log_cp], log_growth])
        new_run_wins  = np.concatenate([[0.0], self._run_wins + x])
        new_run_n     = np.concatenate([[0.0], self._run_n    + 1.0])

        # Normalize
        log_norm      = float(logsumexp(new_log_joint))
        new_log_joint = new_log_joint - log_norm

        # Truncate at max_run_length
        if len(new_log_joint) > self.max_run_length:
            keep = self.max_run_length
            tail = float(logsumexp(new_log_joint[keep:]))
            new_log_joint = new_log_joint[:keep].copy()
            new_run_wins  = new_run_wins[:keep].copy()
            new_run_n     = new_run_n[:keep].copy()
            new_log_joint[-1] = float(np.logaddexp(new_log_joint[-1], tail))
            new_log_joint -= float(logsumexp(new_log_joint))

        self._log_joint = new_log_joint
        self._run_wins  = new_run_wins
        self._run_n     = new_run_n
        self.n_obs     += 1

        state = self._build_state()
        self._last_state = state
        self._wr_history.append(state["posterior_wr"])
        self._cp10_history.append(state["change_prob_last_10"])
        return state

    def _build_state(self) -> dict[str, Any]:
        prob_rl = np.exp(self._log_joint)

        # Posterior mean win rate: weighted average of per-run posteriors
        alpha   = self.alpha0 + self._run_wins
        beta    = self.beta0  + self._run_n - self._run_wins
        wr_rl   = alpha / (alpha + beta)
        post_wr = float(np.dot(prob_rl, wr_rl))

        # Approximate 95% credible interval: mixture of Betas
        # Use weighted percentile over the mixture components
        # (Gaussian approximation: variance of mixture = E[Var] + Var[E])
        mean_wr  = post_wr
        var_rl   = (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1))
        var_mean = float(np.dot(prob_rl, (wr_rl - mean_wr) ** 2))
        e_var    = float(np.dot(prob_rl, var_rl))
        total_var = e_var + var_mean
        sd       = math.sqrt(max(total_var, 1e-12))
        lo95 = max(0.0, mean_wr - 1.96 * sd)
        hi95 = min(1.0, mean_wr + 1.96 * sd)

        # P(changepoint in last k) = P(r_t ≤ k-1) = cumsum[k-1]
        cumprob = np.cumsum(prob_rl)

        def cp_last(k: int) -> float:
            idx = min(k - 1, len(cumprob) - 1)
            return float(cumprob[idx]) if idx >= 0 else 0.0

        return {
            "posterior_wr":        post_wr,
            "lower_95_wr":         lo95,
            "upper_95_wr":         hi95,
            "change_prob_last_5":  cp_last(5),
            "change_prob_last_10": cp_last(10),
            "change_prob_last_20": cp_last(20),
            "mode_run_length":     int(np.argmax(prob_rl)),
        }

    def current_state(self) -> dict[str, Any]:
        """Return the most recent state without updating."""
        return dict(self._last_state)

    @property
    def wr_history(self) -> list[float]:
        return list(self._wr_history)

    @property
    def cp10_history(self) -> list[float]:
        return list(self._cp10_history)


# ─────────────────────────────────────────────────────────────
# EDGE MONITOR (combined)
# ─────────────────────────────────────────────────────────────

class EdgeMonitor:
    """
    Combined SR + CUSUM + BOCPD change-point monitor for GTOS trading edge.

    Call `update(outcome)` after each closed trade.
    SR and CUSUM fire binary alarms calibrated to a target false-alarm rate.
    BOCPD provides a continuous Bayesian posterior on the current win rate.

    All alarms trigger HUMAN REVIEW — not automatic position changes.

    Parameters
    ----------
    p0 : float
        Baseline (H₀) win rate.  Default 0.62 (XAUUSD batch WR).
    p1 : float
        Alternative (H₁) win rate to detect.  Default 0.50 (breakeven).
    sr_threshold : float
        SR threshold A. From calibrate_detectors_v1.py.
        Default is approximate; replace with exact calibrated value.
    cusum_threshold : float
        CUSUM threshold h. From calibrate_detectors_v1.py.
    bocpd_alpha0, bocpd_beta0 : float
        Beta prior hyperparameters for BOCPD.
        Encodes p₀ = alpha0 / (alpha0 + beta0).
    bocpd_hazard : float
        Changepoint hazard per trade = 1 / expected_run_length.
        Default 1/200 ≈ 12-month regime horizon.
    """

    def __init__(
        self,
        p0:              float = 0.62,
        p1:              float = 0.50,
        sr_threshold:    float = _DEFAULT_SR_THRESHOLD,
        cusum_threshold: float = _DEFAULT_CUSUM_THRESHOLD,
        bocpd_alpha0:    float = 62.0,
        bocpd_beta0:     float = 38.0,
        bocpd_hazard:    float = 1.0 / 200.0,
    ):
        self.p0 = p0
        self.p1 = p1

        self._sr    = SRDetector(p0, p1, sr_threshold)
        self._cusum = CUSUMDetector(p0, p1, cusum_threshold)
        self._bocpd = BOCPDDetector(bocpd_alpha0, bocpd_beta0, bocpd_hazard)

        self.n_trades: int = 0
        self._wins:    int = 0
        self._trade_history: list[int] = []

    # ── public API ────────────────────────────────────────────

    def update(self, outcome: bool) -> dict[str, Any]:
        """
        Process one trade outcome.

        Parameters
        ----------
        outcome : bool
            True = win, False = loss.

        Returns
        -------
        dict
            {
              'sr_statistic':             float,
              'sr_alarm':                 bool,
              'cusum_statistic':          float,
              'cusum_alarm':              bool,
              'bocpd_posterior_wr':       float,
              'bocpd_change_prob_last_5': float,
              'bocpd_change_prob_last_10':float,
              'bocpd_change_prob_last_20':float,
              'n_trades':                 int,
              'running_wr':               float,
            }
        """
        self.n_trades += 1
        self._wins    += int(outcome)
        self._trade_history.append(int(outcome))

        sr_state    = self._sr.update(outcome)
        cusum_state = self._cusum.update(outcome)
        bocpd_state = self._bocpd.update(outcome)

        return {
            "sr_statistic":              sr_state["statistic"],
            "sr_alarm":                  sr_state["alarm"],
            "cusum_statistic":           cusum_state["statistic"],
            "cusum_alarm":               cusum_state["alarm"],
            "bocpd_posterior_wr":        bocpd_state["posterior_wr"],
            "bocpd_change_prob_last_5":  bocpd_state["change_prob_last_5"],
            "bocpd_change_prob_last_10": bocpd_state["change_prob_last_10"],
            "bocpd_change_prob_last_20": bocpd_state["change_prob_last_20"],
            "n_trades":                  self.n_trades,
            "running_wr":                self._wins / self.n_trades,
        }

    def get_dashboard(self) -> str:
        """Return a human-readable status summary string."""
        if self.n_trades == 0:
            return "EdgeMonitor: no trades yet."

        running_wr    = self._wins / self.n_trades
        sr_stat       = self._sr.R
        sr_thresh     = self._sr.threshold
        cusum_stat    = self._cusum.S
        cusum_thresh  = self._cusum.threshold
        bocpd_st      = self._bocpd._build_state()

        sr_pct    = sr_stat    / sr_thresh    * 100
        cusum_pct = cusum_stat / cusum_thresh * 100

        sr_label    = "ALARM ***" if sr_stat    >= sr_thresh    else "OK"
        cusum_label = "ALARM ***" if cusum_stat >= cusum_thresh else "OK"

        lines = [
            "=" * 55,
            f"  EdgeMonitor  (n={self.n_trades} trades)",
            "=" * 55,
            f"  Running WR    :  {running_wr:.1%}"
            f"  ({self._wins}W / {self.n_trades - self._wins}L)",
            f"  BOCPD post WR :  {bocpd_st['posterior_wr']:.1%}"
            f"  [{bocpd_st['lower_95_wr']:.1%} – {bocpd_st['upper_95_wr']:.1%} 95% CI]",
            "",
            f"  SR stat       :  {sr_stat:>9.2f} / {sr_thresh:.1f}  "
            f"({sr_pct:.0f}%)  [{sr_label}]",
            f"  CUSUM stat    :  {cusum_stat:>9.4f} / {cusum_thresh:.4f}  "
            f"({cusum_pct:.0f}%)  [{cusum_label}]",
            "",
            f"  P(change ≤5)  :  {bocpd_st['change_prob_last_5']:.1%}",
            f"  P(change ≤10) :  {bocpd_st['change_prob_last_10']:.1%}",
            f"  P(change ≤20) :  {bocpd_st['change_prob_last_20']:.1%}",
            f"  Mode run len  :  {bocpd_st['mode_run_length']} trades",
            "=" * 55,
        ]

        if sr_stat >= sr_thresh or cusum_stat >= cusum_thresh:
            lines.append("  *** EDGE DECAY SIGNAL DETECTED ***")
            lines.append("  *** ACTION: human review required ***")
            lines.append("  *** See operator_decision_playbook.md ***")
        else:
            lines.append("  Status: monitoring, no alarm.")

        return "\n".join(lines)

    def get_state(self) -> dict[str, Any]:
        """Return full serialisable state."""
        if self.n_trades == 0:
            return {"n_trades": 0}

        bocpd_st = self._bocpd._build_state()
        return {
            "n_trades":                  self.n_trades,
            "running_wr":                self._wins / self.n_trades,
            "sr_statistic":              self._sr.R,
            "sr_threshold":              self._sr.threshold,
            "sr_alarm":                  bool(self._sr.R >= self._sr.threshold),
            "cusum_statistic":           self._cusum.S,
            "cusum_threshold":           self._cusum.threshold,
            "cusum_alarm":               bool(self._cusum.S >= self._cusum.threshold),
            "bocpd_posterior_wr":        bocpd_st["posterior_wr"],
            "bocpd_lower_95_wr":         bocpd_st["lower_95_wr"],
            "bocpd_upper_95_wr":         bocpd_st["upper_95_wr"],
            "bocpd_change_prob_last_5":  bocpd_st["change_prob_last_5"],
            "bocpd_change_prob_last_10": bocpd_st["change_prob_last_10"],
            "bocpd_change_prob_last_20": bocpd_st["change_prob_last_20"],
            "bocpd_mode_run_length":     bocpd_st["mode_run_length"],
        }

    def reset_sr(self) -> None:
        """
        Reset SR statistic to 0 after operator review.
        Does NOT reset CUSUM or BOCPD.
        """
        self._sr.reset()

    def reset_cusum(self) -> None:
        """Reset CUSUM statistic to 0 after operator review."""
        self._cusum.reset()

    def reset_all(self) -> None:
        """Reset SR and CUSUM statistics (BOCPD is not reset — it uses all history)."""
        self._sr.reset()
        self._cusum.reset()

    # ── properties ───────────────────────────────────────────

    @property
    def sr_history(self) -> list[float]:
        return self._sr.history

    @property
    def cusum_history(self) -> list[float]:
        return self._cusum.history

    @property
    def bocpd_wr_history(self) -> list[float]:
        return self._bocpd.wr_history

    @property
    def bocpd_cp10_history(self) -> list[float]:
        return self._bocpd.cp10_history


# ─────────────────────────────────────────────────────────────
# CONVENIENCE FACTORY — pre-configured for GTOS
# ─────────────────────────────────────────────────────────────

def make_gtos_monitor(
    arl_mode: str = "primary",
    sr_threshold:    float | None = None,
    cusum_threshold: float | None = None,
) -> EdgeMonitor:
    """
    Factory for GTOS-specific EdgeMonitor with calibrated defaults.

    Parameters
    ----------
    arl_mode : str
        "primary"    → ARL=500 (one false alarm per ~2.5 years)
        "aggressive" → ARL=200 (one false alarm per ~1 year)
    sr_threshold, cusum_threshold : float or None
        Override with exact values from calibrate_detectors_v1.py output.
        If None, uses approximate defaults.

    Returns
    -------
    EdgeMonitor pre-configured for XAUUSD combined-portfolio monitoring.
    """
    # Calibrated values from calibrate_detectors_v1.py (seed=42)
    _defaults = {
        "primary":    {"sr": 453.61, "cusum": 2.6996},  # ARL≈500 (~29 months)
        "aggressive": {"sr": 177.55, "cusum": 1.9982},  # ARL≈200 (~12 months)
    }
    if arl_mode not in _defaults:
        raise ValueError(f"arl_mode must be 'primary' or 'aggressive', got {arl_mode!r}")

    d = _defaults[arl_mode]
    return EdgeMonitor(
        p0=0.62,
        p1=0.50,
        sr_threshold    = sr_threshold    if sr_threshold    is not None else d["sr"],
        cusum_threshold = cusum_threshold if cusum_threshold is not None else d["cusum"],
        bocpd_alpha0=62.0,
        bocpd_beta0=38.0,
        bocpd_hazard=1.0 / 200.0,
    )


# ─────────────────────────────────────────────────────────────
# QUICK SELF-TEST
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import random
    random.seed(42)

    print("EdgeMonitor self-test")
    print("=" * 55)

    monitor = make_gtos_monitor("primary")

    # Simulate 50 trades at p=0.62
    print("\nPhase 1: 50 trades at p=0.62 (H₀ intact)")
    outcomes_h0 = [random.random() < 0.62 for _ in range(50)]
    for o in outcomes_h0:
        monitor.update(o)

    print(monitor.get_dashboard())

    # Simulate 50 trades at p=0.50
    print("\nPhase 2: 50 trades at p=0.50 (edge dead)")
    outcomes_h1 = [random.random() < 0.50 for _ in range(50)]
    for o in outcomes_h1:
        monitor.update(o)

    print(monitor.get_dashboard())
    state = monitor.get_state()
    print(f"\nFull state: n={state['n_trades']}, "
          f"SR={state['sr_statistic']:.2f}/{state['sr_threshold']:.1f} "
          f"({'ALARM' if state['sr_alarm'] else 'OK'}), "
          f"CUSUM={state['cusum_statistic']:.4f}/{state['cusum_threshold']:.4f} "
          f"({'ALARM' if state['cusum_alarm'] else 'OK'})")
    print(f"BOCPD posterior WR: {state['bocpd_posterior_wr']:.1%} "
          f"[{state['bocpd_lower_95_wr']:.1%}–{state['bocpd_upper_95_wr']:.1%}]")
    print(f"P(change in last 10): {state['bocpd_change_prob_last_10']:.1%}")
