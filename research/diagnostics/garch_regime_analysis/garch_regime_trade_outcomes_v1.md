# GARCH-EVT Regime Analysis of Trade Outcomes (Q-5.1)

**Generated:** 2026-04-11 19:21 UTC  
**Script:** `compute_garch_regime_v1.py`  
**Question:** Does entry-time GARCH volatility state predict GTOS trade outcome?  
**Bonferroni correction:** α/20 = 0.0025

---

## 1. GARCH Parameters (H1, All Sessions)

Source: `distributional_characterization_20260411_012816.json`

| Instrument | ω (stored, pct²) | ω (decimal) | α (ARCH) | β (GARCH) | Persistence |
|-----------|----------------|------------|---------|---------|------------|
| XAUUSD | 5.3599e-04 | 5.3599e-08 | 0.0389 | 0.9517 | 0.9906 |
| US30 | 4.8640e-03 | 4.8640e-07 | 0.5376 | 0.4620 | 0.9996 |
| USDJPY | 1.2793e-04 | 1.2793e-08 | 0.0250 | 0.9674 | 0.9924 |
| GBPJPY | 1.6678e-03 | 1.6678e-07 | 0.1782 | 0.7163 | 0.8945 |
| GBPUSD | 2.0885e-03 | 2.0885e-07 | 0.2427 | 0.5603 | 0.8030 |

**Note:** US30 has extremely high ARCH coefficient (α=0.538), indicating rapid vol mean-reversion. GBPUSD/GBPJPY have lower persistence, implying vol shocks decay faster. XAUUSD and USDJPY are in the classic near-unit-root GARCH regime.

## 2. Trade Data Coverage

| Instrument | Source | n (total) | n (matched) | WR |
|-----------|--------|----------|------------|-----|
| XAUUSD | ai_session | 100 | 100 | 65.0% |
| US30 | mechanical | 2 | 2 | 50.0% |
| USDJPY | mechanical | 36 | 36 | 38.9% |
| GBPJPY | mechanical | 1 | 1 | 100.0% |
| GBPUSD | mechanical | 5 | 5 | 80.0% |

**XAUUSD:** AI-evaluated batch trades (sessions) with exact M15 entry timestamps.  
**Others:** Mechanical backtest with date+session+HHMM from cid (M15 precision).  
Instruments with n<8 are excluded from quartile analysis.

## 3. Volatility Quartile Distribution at Trade Entry

### Combined

| Quartile | n | WR | Mean R | 95% CI (Wilson) |
|---------|---|-----|--------|----------------|
| Q1 (quietest) | 36 | 38.9% | 0.393 | [0.248, 0.551] |
| Q2 | 36 | 66.7% | 0.488 | [0.503, 0.798] |
| Q3 | 34 | 61.8% | 0.313 | [0.450, 0.761] |
| Q4 (noisiest) | 35 | 68.6% | 0.666 | [0.520, 0.814] |

### USDJPY

| Quartile | n | WR | Mean R | 95% CI (Wilson) |
|---------|---|-----|--------|----------------|
| Q1 (quietest) | 9 | 22.2% | 0.059 | [0.063, 0.547] |
| Q2 | 9 | 44.4% | 0.637 | [0.189, 0.733] |
| Q3 | 9 | 55.6% | 0.587 | [0.267, 0.811] |
| Q4 (noisiest) | 9 | 33.3% | 0.304 | [0.121, 0.646] |

### XAUUSD

| Quartile | n | WR | Mean R | 95% CI (Wilson) |
|---------|---|-----|--------|----------------|
| Q1 (quietest) | 25 | 60.0% | 0.369 | [0.407, 0.766] |
| Q2 | 25 | 68.0% | 0.373 | [0.484, 0.828] |
| Q3 | 25 | 60.0% | 0.405 | [0.407, 0.766] |
| Q4 (noisiest) | 25 | 72.0% | 0.752 | [0.524, 0.857] |

## 4. Logistic Regression: win ~ log(σ²_entry)

Negative coefficient = higher volatility → lower win rate.

| Instrument | n | Coef | p-value | Pseudo-R² | Bonferroni Sig | Direction |
|-----------|---|------|---------|----------|--------------|---------|
| Combined | 144 | 0.4098 | 0.0232 | 0.0293 | False | higher vol → higher WR |
| GBPJPY | 1 | — | — | — | — | n=1 < 20 — insufficient for logit |
| GBPUSD | 5 | — | — | — | — | n=5 < 20 — insufficient for logit |
| US30 | 2 | — | — | — | — | n=2 < 20 — insufficient for logit |
| USDJPY | 36 | 1.2823 | 0.2826 | 0.0248 | False | higher vol → higher WR |
| XAUUSD | 100 | 0.1830 | 0.4767 | 0.0041 | False | higher vol → higher WR |

## 5. MAE Analysis by Volatility State
(XAUUSD AI trades only — MAE not available for mechanical backtest)

| Quartile | n | Mean MAE_R | Median MAE_R | Mean R |
|---------|---|----------|------------|--------|
| Q1 | 25 | 0.677 | 0.510 | 0.369 |
| Q2 | 25 | 0.556 | 0.391 | 0.373 |
| Q3 | 25 | 0.553 | 0.303 | 0.405 |
| Q4 | 25 | 0.379 | 0.146 | 0.752 |

Kruskal-Wallis (MAE across quartiles): p=0.1201, Bonferroni sig: False
Mann-Whitney Q1 vs Q4 MAE: p=0.0312

## 6. Markov Regime 2×2 Table (Fisher Exact Test)

2-state Gaussian HMM fitted via forward-backward algorithm using stored parameters.

| Instrument | Quiet n | Quiet WR | Volatile n | Volatile WR | OR | Fisher p | Bonf Sig |
|-----------|--------|---------|-----------|-----------|-----|---------|---------|
| Combined | 111 | 57.7% | 33 | 63.6% | 0.778 | 0.6872 | False |
| USDJPY | 26 | 38.5% | 10 | 40.0% | 0.938 | 1.0000 | False |
| XAUUSD | 81 | 63.0% | 19 | 73.7% | 0.607 | 0.4348 | False |

## 7. Tail Analysis: ξ_standardized vs ξ_raw

Comparing GPD shape parameter for raw returns vs GARCH-standardized residuals.
**If ξ_std < ξ_raw:** GARCH explains some tail risk (thinner tails after vol-adjustment).
**If ξ_std ≈ ξ_raw:** Tail risk is in the innovation process — GARCH doesn't help.

| Instrument | Tail | ξ_raw (stored) | ξ_raw (fitted) | ξ_std | Diff (std−raw) | Interpretation |
|-----------|-----|-------------|-------------|------|--------------|--------------|
| XAUUSD | lower | 0.3500 | 0.3500 | 0.1934 | -0.1566 | GARCH helps (thinner tails) |
| XAUUSD | upper | 0.2563 | 0.2563 | 0.1491 | -0.1071 | GARCH helps (thinner tails) |
| US30 | lower | 0.1970 | 0.1970 | 0.2060 | +0.0090 | neutral (tail in innovation) |
| US30 | upper | 0.2084 | 0.2084 | 0.1995 | -0.0089 | neutral (tail in innovation) |
| USDJPY | lower | 0.2186 | 0.2186 | 0.2362 | +0.0176 | neutral (tail in innovation) |
| USDJPY | upper | 0.2127 | 0.2127 | 0.2223 | +0.0096 | neutral (tail in innovation) |
| GBPJPY | lower | 0.1790 | 0.1790 | 0.1683 | -0.0107 | neutral (tail in innovation) |
| GBPJPY | upper | 0.1382 | 0.1382 | 0.1371 | -0.0011 | neutral (tail in innovation) |
| GBPUSD | lower | 0.1569 | 0.1569 | 0.2122 | +0.0553 | GARCH inflates |
| GBPUSD | upper | 0.1399 | 0.1399 | 0.1652 | +0.0254 | neutral (tail in innovation) |

## 8. Tail-Vulnerable Trades

Trades entered when σ_entry > p75 of full H1 σ series (elevated tail risk environment).

| Instrument | TV n | TV WR | Non-TV n | Non-TV WR | MW p |
|-----------|-----|------|---------|---------|-----|
| GBPJPY | 0 | N/A | 1 | 100.0% | N/A |
| GBPUSD | 4 | 75.0% | 1 | 100.0% | N/A |
| US30 | 1 | 0.0% | 1 | 100.0% | N/A |
| USDJPY | 1 | 100.0% | 35 | 37.1% | N/A |
| XAUUSD | 27 | 70.4% | 73 | 63.0% | 0.4986 |

## 9. Filter Simulation: Remove Q4 (Noisiest) Entries

| Instrument | Full n | Full WR | Full Exp | Filt n | Filt WR | Filt Exp | Net ΔR | MW p | Bonf Sig |
|-----------|-------|--------|---------|-------|--------|---------|-------|-----|---------|
| Combined | 141 | 58.9% | 0.466 | 106 | 57.5% | 0.402 | -23.0R | 0.5832 | False |
| USDJPY | 36 | 38.9% | 0.397 | 27 | 40.7% | 0.428 | -2.7R | 0.7132 | False |
| XAUUSD | 100 | 65.0% | 0.475 | 75 | 62.7% | 0.382 | -18.8R | 0.4019 | False |

## 10. All P-values (Bonferroni Corrected)

Correction: α/20 = 0.0025

| Test | p-value | Significant? |
|-----|---------|------------|
| Logit win~log(σ²) [Combined] | 0.0232 | No |
| MAE Mann-Whitney Q1 vs Q4 (XAUUSD) | 0.0312 | No |
| MAE Kruskal-Wallis (XAUUSD quartiles) | 0.1201 | No |
| Logit win~log(σ²) [USDJPY] | 0.2826 | No |
| Filter MW Q4-removed [XAUUSD] | 0.4019 | No |
| Fisher exact Markov [XAUUSD] | 0.4348 | No |
| Logit win~log(σ²) [XAUUSD] | 0.4767 | No |
| Filter MW Q4-removed [Combined] | 0.5832 | No |
| Fisher exact Markov [Combined] | 0.6872 | No |
| Filter MW Q4-removed [USDJPY] | 0.7132 | No |
| Fisher exact Markov [USDJPY] | 1.0000 | No |

---

## 11. Conclusion

### **NULL RESULT — GARCH volatility state at trade entry does NOT predict trade outcome.**

**Logistic regression (XAUUSD):** coef=0.1830, p=0.4767

**Filter simulation (XAUUSD):** Removing Q4 entries changes expectancy from 0.475R to 0.382R (ΔR = -18.8R on 100 trades).  
WR change: 65.0% → 62.7%

**Tail analysis:** GARCH standardization of residuals — see Section 7 for whether GARCH captures or fails to capture tail risk per instrument.

**Action:** Do NOT implement a GARCH-based entry filter. Volatility state is not an actionable signal.

**Unexpected direction note:** Where any relationship exists, it runs POSITIVE (higher volatility →
higher WR / higher mean R), not negative. This is consistent across XAUUSD (Q1 WR=60%, Q4 WR=72%),
USDJPY (non-monotone), and the combined logit (coef=+0.41). A plausible explanation: high-volatility
bars are when OB zones form with the most aggressive impulse momentum, which is exactly when the OB
continuation signal is strongest. ATR-based SL sizing already controls for volatility at the
position-sizing level, so there's no uncontrolled tail risk amplification. In any case, the effect
fails even the uncorrected α=0.05 threshold for XAUUSD alone (p=0.477), confirming no practical
significance. Removing Q4 trades hurts expectancy by -18.8R on XAUUSD — an additional strong
argument against filtering.

**Tail analysis summary:** GARCH does reduce GPD ξ for XAUUSD (raw ξ=0.35 → standardized ξ=0.19
on lower tail), meaning GARCH vol-clustering explains some but not all of gold's fat tails. For
FX instruments (USDJPY, GBPJPY, GBPUSD), ξ_std ≈ ξ_raw — the heavy tails are in the innovation
process, not in the vol clustering. McNeil-Frey (2000) caveat about ATR underestimating tail risk
remains relevant for XAUUSD specifically.

### Instrument-specific notes:

- **XAUUSD** (n=100): coef=0.1830, p=0.4767 (not significant)
- **US30** (n=2): n=2 < 20 — insufficient for logit
- **USDJPY** (n=36): coef=1.2823, p=0.2826 (not significant)
- **GBPJPY** (n=1): n=1 < 20 — insufficient for logit
- **GBPUSD** (n=5): n=5 < 20 — insufficient for logit

---

*All findings are exploratory. No changes to live trading system without CEO approval.*
*Bonferroni threshold: 0.0025 (20 tests).*
