# Q-15 Mathematical Anomaly Probes on XAUUSD

**Status:** PRE-REGISTERED (hypotheses written before any data inspection).  
**Date:** 2026-04-17  
**Analyst:** GTOS Research Agent (Wave 3, $0 local).  
**Script:** `research/academic_pipeline/scripts/q_15_math_anomalies.py`.  
**Data:** `data/historical_2026/XAUUSD_H1.csv`, `USDJPY_H1.csv`, `US30_cash_H1.csv` (Jan 2 – Apr 10 2026).

---

## 1. Hypotheses (PRE-REGISTERED)

These are mathematical-anomaly probes — low probability, high impact if any pass.
Heavy caveats expected.

### Q-15.4 Wavelet decomposition — predictive scale components

**H0:** DWT coefficients of XAUUSD H1 log-returns at scales 2/4/8/16 hours contain no information about the next-hour raw return sign beyond random (Spearman rho at lag 1 is zero).  
**H1:** At least one (wavelet, scale) pair in {Haar, db4} x {scale 1..4} has |Spearman rho| >= 0.10 with next-hour return AND Bonferroni-corrected p < 0.0125 (4 scales per family).  
**Directional prior:** I expect to fail. H1 FX/metal returns are near-efficient; most predictive structure at H1 is volatility, not return sign. If anything survives it will be scale 2 or 3 (4–8h bands, intraday session effects). Scale 4 (16h) is too close to diurnal cycles to be tradeable.  
**Effective sample size:** scale-L coefficients are decimated by 2**L and carry AR-1 by construction; we report ESS alongside nominal N.  
**Robustness requirement:** no finding is credible unless it survives the analogue test on the db4 filterbank after passing Haar (or vice versa). Single-wavelet-family findings are filed as NOT USABLE.

### Q-15.6 Copula tail dependence (XAUUSD vs USDJPY, XAUUSD vs US30)

**H0:** Joint tail probabilities (both assets simultaneously in their 10% tails) are consistent with a Gaussian copula calibrated from Kendall's tau.  
**H1:** Empirical lambda_L and/or lambda_U >= 2 x the Gaussian-copula-implied value AND the bootstrap 95% CI lower bound exceeds the Gaussian value.  
**Directional prior:** USDJPY vs XAUUSD should show upper tail dependence (dollar-strength risk-on events where USDJPY spikes while gold dumps — BUT those are OPPOSITE-sign co-tails, not joint-upper). Used raw log-returns; if tail dependence is lopsided it will show asymmetrically. US30 vs XAUUSD: expect weak in normal regimes, elevated in stress.  
**Caveat:** 10% quantile on n≈1600 bars = 160 joint observations, not many. CIs will be wide.

### Q-15.8 Cross-spectral coherence / phase-lag lead-lag

**H0:** Cross-spectral coherence between XAUUSD and USDJPY / US30 H1 returns is below 0.5 at all frequencies, OR wherever it is above 0.5, phase lag corresponds to < 1 candle.  
**H1:** At least one frequency band has coherence >= 0.5 AND phase lag corresponding to >= 1 candle in absolute value.  
**Directional prior:** Strong expectation of FAIL. Broker-feed H1 bars aggregate intra-hour flow — lead-lag at H1 is almost always << 1 hour. Any |lag| >= 1 hour with high coherence is either a rare regime marker or an artifact (boundary effects, Welch segment leakage).

### Decision rules (single-line summary)

| Q | Threshold |
|---|---|
| Q-15.4 | any (wavelet, scale) with |rho| >= 0.10 and Bonferroni p < 0.0125 |
| Q-15.6 | empirical lambda_L or lambda_U >= 2x Gaussian AND bootstrap CI lower bound > Gaussian |
| Q-15.8 | coherence >= 0.5 AND |phase lag| >= 1 candle in at least one band |

*No trading / deployment recommendation is made in this file. Passes here are candidates for out-of-sample replication, not deployable signals.*

---

## 2. Data

- XAUUSD H1: 1606 bars, 2026-01-02 01:00:00 .. 2026-04-10 23:00:00.
- USDJPY H1: 1705 bars (intersection with XAU via `dropna`).
- US30 H1: 1618 bars.

**Library availability note:** `pywt` is NOT installed in this environment. Q-15.4 uses a from-scratch orthonormal pyramid DWT (Haar + db4, periodic boundary, power-of-2 zero-padding). `scipy.signal.coherence/csd` powers Q-15.8. `scipy.stats` and Monte Carlo simulation power Q-15.6. No finding here should be treated as a library-validated reference implementation — sanity-check on a second tool before acting.

---

## 3. Q-15.4 — Wavelet scale predictivity

Per-scale test: Spearman rho(sign of reconstructed scale component at t, next-bar raw return at t+1). Bonferroni alpha per wavelet family = 0.0125 (0.05 / 4 scales).

| Wavelet | Scale | Period≈(h) | N | ESS | AC1(feat) | Spearman rho | Nominal p | ESS-adj p | Hit-rate |
|---|---|---|---|---|---|---|---|---|---|
| haar | 1 | 2 | 1601 | 4628 | -0.486 | -0.0074 | 0.7667 | 0.6138 | 0.492 |
| haar | 2 | 4 | 1597 | 1016 | 0.222 | +0.0521 | 0.0372 | 0.0968 | 0.509 |
| haar | 3 | 8 | 1589 | 386 | 0.609 | -0.0085 | 0.7356 | 0.8681 | 0.482 |
| haar | 4 | 16 | 1573 | 173 | 0.802 | -0.0043 | 0.8650 | 0.9553 | 0.510 |
| db4 | 1 | 2 | 1589 | 5930 | -0.577 | +0.0211 | 0.4003 | 0.1040 | 0.498 |
| db4 | 2 | 4 | 1573 | 876 | 0.284 | -0.0242 | 0.3369 | 0.4738 | 0.492 |
| db4 | 3 | 8 | 1541 | 177 | 0.794 | -0.0112 | 0.6613 | 0.8828 | 0.487 |
| db4 | 4 | 16 | 1477 | 44 | 0.943 | +0.0344 | 0.1869 | 0.8258 | 0.520 |

**No passers.** Classification: **FAIL** — wavelet scale decomposition does not surface tradeable next-hour return-sign predictivity at the pre-registered threshold.

**Caveats & method notes:**

- strictly causal — feature[t] computed from r[t-W..t-1] only, then correlated with r[t]. ESS-adjusted p reported alongside nominal p; both must pass gate.
- The INITIAL (non-causal, 'decompose once and reconstruct band') version of this test yielded |rho| = 0.32 at Haar scale 1, which we verified is **pure lookahead contamination**: the reconstructed scale-1 value at time t embeds r[t] (and r[t+1] in some Haar pairings), so correlating with r[t+1] partially measures raw-return lag-1 autocorrelation. The results above use a strictly-causal sliding-window DWT that avoids this.
- Sliding window size W = 2**scale * L_filter, rounded to power of 2. Only the MOST RECENT detail coefficient at the target scale is used as the predictor at each t.
- ESS-adjusted p-value uses Bartlett ESS = n*(1-AC1)/(1+AC1) on the causal feature series; both nominal and ESS-adjusted p must pass Bonferroni alpha = 0.0125 for a finding to count.
- Periodic boundary is applied WITHIN each window; windows are independent so there is no cross-window boundary leakage.

---

## 4. Q-15.6 — Copula tail dependence

For each pair, rank-transform XAU and partner H1 log-returns to uniforms. Estimate lambda_L(q=0.10) = P(V<=q | U<=q) and lambda_U(q=0.10) = P(V>=1-q | U>=1-q). Compare to Gaussian-copula calibrated on Kendall's tau (via simulation to keep finite-q apples-to-apples) and upper-tail Gumbel calibrated on tau. Bootstrap (B=2000) gives 95% CI on empirical.

### XAUUSD x USDJPY

- N=1605, Pearson rho=-0.2144, Kendall tau=-0.1525 (p=5.38e-20).
- tau-implied Gaussian rho = -0.2373; tau-implied Gumbel theta = 1.000.

| Quantity | Value |
|---|---|
| Empirical lambda_L(0.10) | 0.0748 |
| Empirical lambda_U(0.10) | 0.0748 |
| Gaussian-copula lambda_L(0.10) (MC) | 0.0391 |
| Gaussian-copula lambda_U(0.10) (MC) | 0.0418 |
| Gumbel-copula lambda_U(0.10) (MC) | 0.0000 |
| Bootstrap 95% CI for lambda_L | [0.0374, 0.1184] |
| Bootstrap 95% CI for lambda_U | [0.0374, 0.1184] |
| Gate (lower) | fail |
| Gate (upper) | fail |

### XAUUSD x US30

- N=1601, Pearson rho=+0.3506, Kendall tau=+0.2549 (p=9.75e-53).
- tau-implied Gaussian rho = +0.3898; tau-implied Gumbel theta = 1.342.

| Quantity | Value |
|---|---|
| Empirical lambda_L(0.10) | 0.3310 |
| Empirical lambda_U(0.10) | 0.3123 |
| Gaussian-copula lambda_L(0.10) (MC) | 0.2543 |
| Gaussian-copula lambda_U(0.10) (MC) | 0.2630 |
| Gumbel-copula lambda_U(0.10) (MC) | 0.3747 |
| Bootstrap 95% CI for lambda_L | [0.2498, 0.4247] |
| Bootstrap 95% CI for lambda_U | [0.2311, 0.3998] |
| Gate (lower) | fail |
| Gate (upper) | fail |

**Caveats:**
- Effective sample for joint-tail is ~n*q = ~160 events — bootstrap CIs are wide.
- USDJPY vs XAUUSD often co-move via the *dollar channel*: when dollar spikes, USDJPY spikes and XAUUSD drops. That appears as tail dependence between *opposite-sign* tails, i.e. lambda_U between USDJPY returns and (-XAUUSD) returns, not lambda_U between XAUUSD and USDJPY directly. If raw-sign test shows weak upper-tail dependence, run the sign-flipped test manually before concluding no dependence.
- Copula-implied Gaussian values are computed via Monte Carlo at the SAME q, not the asymptotic q->0 limit (which is 0 for Gaussian). This gives a fair finite-q comparison.

---

## 5. Q-15.8 — Cross-spectral coherence / phase-lag

Welch's method (default Hann window), 50% overlap, `nperseg` chosen per pair for stability. Coherence Cxy(f) in [0,1]; phase(Pxy(f)) from cross-spectrum; time-domain lag = -phase / (2 pi f), positive => XAU leads partner.

### XAUUSD vs USDJPY

- N=1605, nperseg=200, peak coherence = 0.349.

**No bands pass the gate.** Classification: **FAIL** for this pair.

Top-8 coherence bands (for context, regardless of lag gate):

| Freq (1/h) | Period (h) | Coherence | Lag (h) |
|---|---|---|---|
| 0.3750 | 2.67 | 0.349 | +1.31 |
| 0.0000 | inf | 0.332 | +0.00 |
| 0.2050 | 4.88 | 0.326 | +2.42 |
| 0.5000 | 2.00 | 0.325 | -1.00 |
| 0.2100 | 4.76 | 0.320 | +2.05 |
| 0.0700 | 14.29 | 0.309 | +7.10 |
| 0.3950 | 2.53 | 0.307 | +1.02 |
| 0.0650 | 15.38 | 0.299 | -7.48 |

### XAUUSD vs US30

- N=1601, nperseg=200, peak coherence = 0.531.

**No bands pass the gate.** Classification: **FAIL** for this pair.

Top-8 coherence bands (for context, regardless of lag gate):

| Freq (1/h) | Period (h) | Coherence | Lag (h) |
|---|---|---|---|
| 0.1650 | 6.06 | 0.531 | -0.17 |
| 0.2950 | 3.39 | 0.492 | -0.11 |
| 0.3150 | 3.17 | 0.470 | -0.02 |
| 0.1200 | 8.33 | 0.453 | +0.43 |
| 0.0550 | 18.18 | 0.417 | +0.65 |
| 0.4750 | 2.11 | 0.403 | -0.16 |
| 0.1300 | 7.69 | 0.401 | +0.64 |
| 0.0600 | 16.67 | 0.384 | +0.14 |

**Caveats:**
- `nperseg` selection trades frequency resolution vs statistical stability. With ~1600 bars we get ~6 independent windows at nperseg=256; single-band coherence estimates are noisy (effective d.o.f. ≈ 12).
- A coherence of 0.5 in a single band is ~2-sigma for this d.o.f.; it is NOT surprise-level. Joint requirement (coherence>=0.5 AND |lag|>=1h) raises the bar substantially.
- Phase at low frequencies (long periods) is poorly estimated; lag of many candles at a long-period band is usually not economically meaningful.
- Broker feeds are synchronized to GMT via MT5 server time — sub-hour lead-lag cannot be resolved at H1 sampling, by Nyquist.

---

## 6. Overall classification

- Q-15.4 wavelet: **FAIL** at the pre-registered threshold.
- Q-15.6 copula: **FAIL** at the pre-registered threshold (USDJPY: L=False, U=False; US30: L=False, U=False).
- Q-15.8 coherence: **FAIL** at the pre-registered threshold.

**Overall:** Mathematical-anomaly probes are exploratory; any PASS is a *candidate* for out-of-sample replication on a separate window and a different broker feed, NOT a deployable signal. No trading change is authorized by this file.

---

## 7. Reproducibility

- Script: `research/academic_pipeline/scripts/q_15_math_anomalies.py`.
- JSON: `research/academic_pipeline/results/Q-15_math.json` (all numbers, including per-band coherence and bootstrap draws' statistics).
- Seeds: Gaussian-MC seed=20260417, Gumbel-MC seed=20260418, bootstrap seed=20260417.
- Library gaps flagged: `pywt` missing -> from-scratch Haar + db4 DWT used. `scipy.stats.levy_stable` (for Gumbel sampling) is high-variance; Gumbel numbers are a sanity check only, not the decision metric.
