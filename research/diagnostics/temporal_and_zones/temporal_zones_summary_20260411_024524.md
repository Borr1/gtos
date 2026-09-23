# GTOS Temporal Pattern & Zone Analysis — B1, B2, B3
**Generated:** 20260411_024524 UTC
**Bonferroni α\*:** 0.000161 (n_tests=311)
**Significance markers:** `**` = Bonferroni-significant, `*` = raw p<0.05

---

## B1 — Asia Range → London Prediction (Q-0.2)

**Session definition:** Asia = 00:00–07:00 UTC, London = instrument kill zone start–end

### Correlation: Asia Range vs London Range

| Instrument | N Days | Pearson r | p | Spearman r | p |
|------------|--------|-----------|---|------------|---|
| XAUUSD | 641 | 0.8274 | 0.0000** | 0.7959 | 0.0000** |
| US30 | 875 | 0.6164 | 0.0000** | 0.5374 | 0.0000** |
| USDJPY | 833 | 0.5673 | 0.0000** | 0.5765 | 0.0000** |
| GBPJPY | 833 | 0.5159 | 0.0000** | 0.4166 | 0.0000** |
| GBPUSD | 833 | 0.2769 | 0.0000** | 0.3062 | 0.0000** |

### Regression: London_range = α + β × Asia_range

| Instrument | α | β | R² | p(β) |
|------------|---|---|----|------|
| XAUUSD | 3.9011 | 0.6268 | 0.6847 | 0.0000** |
| US30 | 54.1732 | 0.551 | 0.38 | 0.0000** |
| USDJPY | 0.2111 | 0.3921 | 0.3218 | 0.0000** |
| GBPJPY | 0.4152 | 0.3668 | 0.2662 | 0.0000** |
| GBPUSD | 0.0035 | 0.34 | 0.0767 | 0.0000** |

### Direction Test: Does Asia Range Predict London Return?

| Instrument | β (range→return) | R² | p(β) | Interpretation |
|------------|-------------------|----|------|----------------|
| XAUUSD | -0.0571 | 0.012 | 0.0055* | Weak |
| US30 | 0.0606 | 0.0041 | 0.0596 | No directional signal |
| USDJPY | -0.0567 | 0.0055 | 0.0324* | Weak |
| GBPJPY | -0.0321 | 0.0013 | 0.3018 | No directional signal |
| GBPUSD | -0.0599 | 0.0011 | 0.3373 | No directional signal |

### Quartile Analysis: XAUUSD (Asia range quartiles → London range)

| Asia Quartile | N | Asia Mean | London Mean | London Std | Expansion Rate (>1.5ADR) |
|---------------|---|-----------|-------------|------------|--------------------------|
| Q1 | 161 | 6.5823 | 8.3742 | 3.2602 | 0.0 |
| Q2 | 160 | 11.8623 | 11.8567 | 5.0149 | 0.0 |
| Q3 | 160 | 21.7512 | 17.0279 | 7.9935 | 0.0 |
| Q4 | 160 | 64.391 | 43.8942 | 39.1937 | 0.0312 |

### XAUUSD: Threshold Tests ($)

| Asia Range Threshold | N | London Mean | Normal London Mean | KS p |
|---------------------|---|-------------|-------------------|------|
| asia_lt_10.0 | 192 | 8.8207 | 30.3509 | 0.0000** |
| asia_lt_12.0 | 252 | 9.5764 | 30.3509 | 0.0000** |
| asia_lt_15.0 | 319 | 10.0936 | 30.3509 | 0.0000** |

---

## B2 — Intraday Momentum: First-Half → Second-Half (Q-14.7)

**Primary splits:** London 07:00–08:30 → 08:30–10:30 | NY 13:00–14:15 → 14:15–15:30 UTC
**Robustness:** London 07:00–09:00 → 09:00–10:30 | NY 13:00–14:30 → 14:30–15:30 UTC

| Instrument | Session | N | Pearson r | p | β | p(β) | Sign Rate | Binom p |
|------------|---------|---|-----------|---|---|------|-----------|---------|
| XAUUSD | London_primary | 514 | -0.1815 | 0.0000** | -0.187 | 0.0000** | 0.5156 | 0.2541 |
| XAUUSD | London_robust | 514 | -0.1659 | 0.0002** | -0.1317 | 0.0002** | 0.4825 | 0.7990 |
| XAUUSD | NY_primary | 516 | 0.0279 | 0.5271 | 0.0622 | 0.5271 | 0.4826 | 0.7985 |
| XAUUSD | NY_robust | 516 | 0.004 | 0.9284 | 0.0075 | 0.9284 | 0.5 | 0.5176 |
| US30 | London_primary | 1095 | -0.0107 | 0.7240 | -0.0169 | 0.7240 | 0.4694 | 0.9801 |
| US30 | London_robust | 1095 | 0.0194 | 0.5222 | 0.0231 | 0.5222 | 0.4968 | 0.5955 |
| US30 | NY_primary | 1093 | -0.0245 | 0.4177 | -0.0307 | 0.4177 | 0.4959 | 0.6188 |
| US30 | NY_robust | 1093 | 0.019 | 0.5313 | 0.0213 | 0.5313 | 0.4867 | 0.8179 |
| USDJPY | London_primary | 521 | 0.0694 | 0.1136 | 0.0444 | 0.1136 | 0.5221 | 0.1676 |
| USDJPY | London_robust | 521 | 0.123 | 0.0049* | 0.0493 | 0.0049* | 0.4952 | 0.6037 |
| USDJPY | NY_primary | 521 | -0.0495 | 0.2595 | -0.0481 | 0.2595 | 0.5048 | 0.4305 |
| USDJPY | NY_robust | 521 | -0.0035 | 0.9368 | -0.0029 | 0.9368 | 0.499 | 0.5349 |
| GBPJPY | London_primary | 1042 | 0.0441 | 0.1552 | 0.0325 | 0.1552 | 0.5077 | 0.3211 |
| GBPJPY | London_robust | 1042 | 0.0954 | 0.0020* | 0.0426 | 0.0020* | 0.5048 | 0.3902 |
| GBPJPY | NY_primary | 1043 | -0.0216 | 0.4862 | -0.0228 | 0.4862 | 0.5014 | 0.4753 |
| GBPJPY | NY_robust | 1043 | -0.0036 | 0.9064 | -0.0032 | 0.9064 | 0.5034 | 0.4263 |
| GBPUSD | London_primary | 521 | -0.023 | 0.5998 | -0.025 | 0.5998 | 0.4837 | 0.7848 |
| GBPUSD | London_robust | 521 | -0.0319 | 0.4681 | -0.03 | 0.4681 | 0.499 | 0.5349 |
| GBPUSD | NY_primary | 521 | 0.0217 | 0.6220 | 0.023 | 0.6220 | 0.5393 | 0.0398* |
| GBPUSD | NY_robust | 521 | 0.0396 | 0.3668 | 0.0355 | 0.3668 | 0.5163 | 0.2417 |

### Economic Significance

| Instrument | Session | H2 Mean (bps) | H2 Mean|H1↑ (bps) | Conditional Edge (bps) |
|------------|---------|---------------|-----------------|------------------------|
| XAUUSD | London_primary | 0.261 | 0.562 | 0.301 |
| XAUUSD | NY_primary | -2.495 | -3.862 | -1.368 |
| US30 | London_primary | 0.068 | -0.991 | -1.059 |
| US30 | NY_primary | 1.764 | 1.836 | 0.072 |
| USDJPY | London_primary | -0.368 | 0.016 | 0.384 |
| USDJPY | NY_primary | -0.268 | -0.867 | -0.599 |
| GBPJPY | London_primary | -0.099 | 0.335 | 0.434 |
| GBPJPY | NY_primary | 0.57 | 0.645 | 0.074 |
| GBPUSD | London_primary | 0.138 | -0.466 | -0.604 |
| GBPUSD | NY_primary | 0.111 | 0.958 | 0.847 |

---

## B3 — VWAP Reversion (Q-13.2)

**VWAP definition:** typical_price × tick_volume, anchored daily at 00:00 UTC
**Deviation metric:** (close − VWAP) / ATR₁₄
**Reversion criterion:** |future deviation| ≤ 0.25 ATR within N M15 bars
**OB continuation benchmark:** ~70% (mechanical, from historical backtest)

### XAUUSD — London Session VWAP Reversion Table

> Session VWAP anchored to London KZ start (07:00 UTC), resets each day.
> Reversion = CUMULATIVE: price ever reaches |dev| ≤ 0.25 ATR within N bars.

| Deviation Threshold | Lag 1 | Lag 2 | Lag 4 | Lag 8 |
|---------------------|-------|-------|-------|-------|
| 0.5 ATR | 11.6% (n=3386) 1.0000 | 21.4% (n=3386) 1.0000 | 34.3% (n=3386) 1.0000 | 42.9% (n=3386) 1.0000 |
| 1.0 ATR | 5.1% (n=1749) 1.0000 | 12.3% (n=1749) 1.0000 | 24.5% (n=1749) 1.0000 | 32.1% (n=1749) 1.0000 |
| 1.5 ATR | 2.6% (n=831) 1.0000 | 8.3% (n=831) 1.0000 | 17.6% (n=831) 1.0000 | 22.6% (n=831) 1.0000 |
| 2.0 ATR | 2.5% (n=357) 1.0000 | 5.6% (n=357) 1.0000 | 13.2% (n=357) 1.0000 | 17.1% (n=357) 1.0000 |

### XAUUSD — NY Session VWAP Reversion Table (1.0 ATR dev)

| Threshold | Lag 1 | Lag 2 | Lag 4 | Lag 8 |
|-----------|-------|-------|-------|-------|
| 1.0 ATR | 6.3% (n=2213) 1.0000 | 13.7% (n=2213) 1.0000 | 24.4% (n=2213) 1.0000 | 31.7% (n=2213) 1.0000 |

### All-Instrument Summary — London Session VWAP (1.0 ATR, Lag 4 cumulative)

| Instrument | N Events | Reversion Rate | Binom p | vs OB (70%) |
|------------|----------|----------------|---------|-------------|
| XAUUSD | 1749 | 24.5% | 1.0000 | WEAKER |
| US30 | 2168 | 22.8% | 1.0000 | WEAKER |
| USDJPY | 931 | 19.4% | 1.0000 | WEAKER |
| GBPJPY | 2284 | 23.1% | 1.0000 | WEAKER |
| GBPUSD | 3528 | 22.3% | 1.0000 | WEAKER |

### Displacement Speed Analysis (XAUUSD London, 1.0 ATR dev, Lag 4 cumulative)

- **fast_displacement:** n=758, reversion rate = 0.2573
- **slow_displacement:** n=987, reversion rate = 0.2361

### Daily VWAP Reference (bias check)
- Mean KZ deviation (daily VWAP): 0.4045 ATR — Positive mean bias confirms trending behaviour during KZ; daily VWAP is not the right anchor.

---

## GTOS Implications Summary

### B1 — Pre-screen recalibration
- Asia–London correlation: r=0.8274, p=0.0000 — statistically significant. Narrow Asia days are NOT identical to random days; pre-screen should consider this.

### B2 — Directional bias signal
- London first-half → second-half: β=-0.187, p=0.0000 (**Bonferroni-significant**). Conditional edge: 0.301 bps. PROMOTE to candidate directional filter in Component 3A evaluation context.

### B3 — VWAP as alternative zone type
- VWAP reversion rate (1.0 ATR, lag-4): 24.5% — WEAKER than OB benchmark (70%). Do NOT replace OB zones with VWAP zones. May serve as a confirming filter (price at VWAP + at OB zone = confluence).

---

## Methodology Notes

- **Asia timezone:** UTC confirmed. Monday first-bar offset (01:00 UTC) handled by requiring ≥ 3 bars in session.
- **VWAP quality:** Tick volume used as proxy; bar-count fallback for constant-volume days. VWAP from H1 vs M15 quality check not applicable (no H1 VWAP equivalent — different granularity).
- **B2 alternative split:** Both 08:30 and 09:00 midpoints tested for robustness.
- **Bonferroni:** Applied across all primary hypothesis tests in this batch (not post-hoc).
- **Total tests in Bonferroni pool:** 311 (at time of writing)