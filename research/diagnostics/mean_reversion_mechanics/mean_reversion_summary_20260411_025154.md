# GTOS Mean-Reversion Mechanics Analysis
*Generated 20260411_025154 UTC*
*Bonferroni α\* = 0.000192 (260 total hypothesis tests)*

## A1: Ornstein-Uhlenbeck Half-Life

**Interpretation:** HL = N H1 bars means price reverts halfway to fair value in N bars.
Trailing stop timeout recommendation: ~1.5 × HL bars after entry.

### All 5 Instruments — H1, SMA50 Detrend

| Instrument | Half-Life (bars) | 95% CI | β p-value | Mean Reversion? |
|------------|-----------------|--------|-----------|-----------------|
| XAUUSD | 25.4 [21.9–28.9] | — | 0.0000 | YES |
| US30 | 21.4 [19.1–23.8] | — | 0.0000 | YES |
| USDJPY | 23.8 [21.1–26.5] | — | 0.0000 | YES |
| GBPJPY | 21.2 [18.9–23.4] | — | 0.0000 | YES |
| GBPUSD | 21.4 [19.1–23.7] | — | 0.0000 | YES |

### XAUUSD — Timeframe Comparison (SMA50)

| TF | HL (bars) | HL (hours) | β p-value |
|----|----------|------------|-----------|
| M15 | 21.8 | 5.4h | 0.0000 |
| H1 | 25.4 | 25.4h | 0.0000 |
| H4 | 23.2 | 92.8h | 0.0000 |

### XAUUSD H1 — Subgroup Comparison (SMA50)

| Subgroup | Half-Life (bars) | β p-value |
|----------|-----------------|-----------|
| All Hours | 25.4 [21.9–28.9] | 0.0000 |
| Kill Zone only | 20.9 [16.5–25.3] | 0.0000 |
| Off Hours | 24.2 [20.1–28.2] | 0.0000 |
| 2024 | 23.4 [18.6–28.3] | 0.0000 |
| 2025 | 23.7 [18.7–28.6] | 0.0000 |
| 2026 (partial) | 26.4 [14.2–38.6] | 0.0000 |

## A2: Fractional Integration / Hurst Exponent

**d = H − 0.5:**  d > 0 → persistent (trending)  |  d ≈ 0 → random walk  |  d < 0 → anti-persistent

### All 5 Instruments — H1

| Instrument | GPH (√n) d | GPH (n⁰·⁶⁵) d | Whittle d | R/S H | DFA H | Class. |
|------------|-----------|----------------|-----------|-------|-------|--------|
| XAUUSD | -0.049 | +0.014 | -0.009 | 0.504 | 0.460 | NEUTRAL |
| US30 | -0.100 | -0.074 | -0.002 | 0.499 | 0.448 | NEUTRAL |
| USDJPY | -0.074 | -0.026 | +0.006 | 0.473 | 0.498 | NEUTRAL |
| GBPJPY | -0.030 | -0.055 | +0.001 | 0.484 | 0.459 | NEUTRAL |
| GBPUSD | -0.034 | -0.024 | -0.011 | 0.530 | 0.489 | NEUTRAL |

### XAUUSD — Timeframe Comparison

| TF | GPH (√n) d | Whittle d | R/S H | DFA H | Class. |
|----|-----------|-----------|-------|-------|--------|
| M15 | -0.098 | -0.005 | 0.504 | 0.449 | NEUTRAL |
| H1 | -0.049 | -0.009 | 0.504 | 0.460 | NEUTRAL |
| H4 | +0.031 | +0.017 | 0.547 | 0.466 | NEUTRAL |
| D1 | +0.135 | -0.020 | 0.567 | 0.463 | NEUTRAL |

### XAUUSD H1 — Year-by-Year Stability

| Year | n returns | GPH d | Whittle d | R/S H | DFA H |
|------|-----------|-------|-----------|-------|-------|
| 2024 | 5937 | -0.087 | +0.002 | 0.542 | 0.521 |
| 2025 | 5898 | +0.025 | -0.014 | 0.540 | 0.451 |
| 2026 | 1411 | +0.130 | -0.012 | 0.606 | 0.549 |

## A3: Compression-Before-Expansion

**Expansion ratio** = mean(ATR_ratio after compressed) / mean(ATR_ratio after normal).
Ratio > 1 → compression predicts expansion.
\* = p<0.05 nominal  |  \*\* = p < Bonferroni α\* = 0.00019

### XAUUSD H1 — All Thresholds, Lag +1 Bar

| Threshold | N comp | N normal | Expansion Ratio | p (1-sided) | Sig |
|-----------|--------|----------|-----------------|-------------|-----|
| 0.5 | 0 | 14684 | — | — |  |
| 0.6 | 0 | 14684 | — | — |  |
| 0.7 | 0 | 14684 | — | — |  |
| 0.8 | 268 | 14416 | 0.789 | 1.0000 |  |

### All Instruments H1 — Threshold 0.7, Lags 1 / 2 / 4 / 8

| Instrument | Lag 1 | Lag 2 | Lag 4 | Lag 8 |
|------------|-------|-------|-------|-------|
| XAUUSD | — | — | — | — |
| US30 | 0.707 | 0.751 | 0.877 | 1.089* |
| USDJPY | 0.682 | 0.697 | 0.728 | 0.902 |
| GBPJPY | — | — | — | — |
| GBPUSD | — | — | — | — |

### GARCH / AR(1) Comparison (ATR < 70% threshold)

| Instrument | AR(1) coef | Compression coef | p-value | Independent of GARCH? |
|------------|-----------|-----------------|---------|----------------------|
| XAUUSD | 0.940 | 0.0000 | — | no |
| US30 | 0.949 | 0.0092 | 0.1844 | no |
| USDJPY | 0.936 | -0.0117 | 0.2077 | no |
| GBPJPY | 0.943 | -0.0104 | 0.6828 | no |
| GBPUSD | 0.947 | 0.0000 | — | no |

### ATR Autocorrelation Summary (first 3 lags, H1)

| Instrument | ACF(1) | ACF(2) | ACF(3) |
|------------|--------|--------|--------|
| XAUUSD | 0.940 | 0.834 | 0.706 |
| US30 | 0.948 | 0.840 | 0.694 |
| USDJPY | 0.936 | 0.837 | 0.726 |
| GBPJPY | 0.943 | 0.849 | 0.738 |
| GBPUSD | 0.947 | 0.846 | 0.713 |

## GTOS Trading Implications

### A1 → Trailing Stop Timeout
- XAUUSD H1 mean-reversion half-life (SMA50): **25.4 bars**
  → Timeout at 1.5× HL = **38 H1 bars ≈ 38h**
  → Trades still open after 38 bars are fighting a dying reversion.
- Kill Zone HL: 20.9 bars (FASTER than all-hours, ratio=0.82)

### A2 → Regime Diagnosis
- XAUUSD H1 fractional d classification: **NEUTRAL** (d≈-0.015)
  → Confirms VR-test result: linear momentum/reversion strategies won't extract edge.
  → GTOS edge must be NONLINEAR (OB zone precision) — consistent with findings.

### A3 → Pre-Screen & Position Sizing

---
*Plots: /Users/borr/Documents/trading/gold-agent/research/diagnostics/mean_reversion_mechanics/plots*