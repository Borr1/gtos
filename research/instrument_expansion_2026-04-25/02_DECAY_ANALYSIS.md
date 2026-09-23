# Per-Instrument Decay Deep Dive — Tier 1 Agent #2

**Date:** 2026-04-25
**Scope:** 24 instruments × 4 months (Jan / Feb / Mar / Apr 2026, partial)
**Data:** `data/historical_2026/` M15 + H1 (Wilder ATR(14), market-state derived BOS/OB/FVG)
**Code re-use:** `src/components/market_state.py` — `detect_swings`, `identify_structure_v2` (dead-zone divisor 8, ADR-004 v2), `detect_structure_breaks`, `identify_order_blocks`, `identify_fvgs`. Mechanical proxy uses 168-bar H1 rolling windows, no AI filter.
**Output artefacts:**
- `02_per_instrument_decay_scorecard.csv` — one row per instrument, ranked by decay score
- `02_monthly_metrics.csv` (long) — instrument × month × metric
- `02_h1_h2_split.csv` — every metric, H1 (Jan+Feb) vs H2 (Mar+Apr)
- `02_decay_clusters.csv` — pattern-string clustering
- `02_pooled_h1h2.csv` — cross-instrument pooling
- `02_results.json` — raw results object
- `02_decay_analysis.py` / `_run_parallel.py` / `_pooled_analysis.py` — code

---

## TL;DR — Headline Findings

1. **Fleet-wide decay signal is ABSENT under the mechanical OB-retest proxy.** Pooled H1 (Jan+Feb) vs H2 (Mar+Apr) BOS retest WR across 16 FULL-data instruments: **61.7% → 60.2%, delta −1.6pp, two-prop z=0.63, p=0.53**. No instrument survives Bonferroni correction (α/24 = 0.0021); no instrument survives Benjamini-Hochberg FDR (q=0.10).
2. **The CLAUDE.md "XAUUSD H1→H2 64.5% → 24.0% decay" finding is REAL on AI-filtered live trades but NOT in the mechanical proxy.** XAUUSD raw OB-retest dropped only 71% → 60% (delta −11pp, n=31/40, p=0.34) — directionally consistent but ~4× smaller than the live-realized drop. Implies the AI filter compounds (or unmasks) decay; mechanical edge is partially intact.
3. **Decay is idiosyncratic, not market-wide.** Per-asset-class pooled H1→H2 deltas: Crypto −10.2pp (p=0.11), Metals −11pp (n=1, n.s.), FX +0.7pp (no decay), Indices −0.9pp (no decay). JPY-pairs cluster −0.6pp; non-JPY FX +1.7pp.
4. **Volatility regime DID shift sharply H1→H2 in indices and energy** (ATR-M15 +40-300%) but FX and metals stayed flat or contracted. WR-delta vs ATR-pct-change correlation across 16 FULL instruments: **r = +0.13 (Pearson), p = 0.64** — the regime hypothesis ("vol drop ⇒ WR drop") is NOT supported. Decay correlates more with **per-instrument idiosyncratic noise** than with macro vol.
5. **Top 5 most-stable**: USDJPY (CV 0.03), CHFJPY (0.04), USDCHF (0.04), EURUSD (0.05), JP225 (0.07). **Top 5 most-decaying**: GBPJPY (−14pp), BTCUSD (−14pp), XAUUSD (−11pp), GBPUSD (CV 0.17 — high noise rather than monotonic), AUDUSD (−7pp).

---

## 1. Methodology

### 1.1 Mechanical edge proxies

Two binomial WR proxies, both deterministic, no AI filter:

| Proxy | Mechanism | Horizon | Sample size |
|-------|-----------|---------|-------------|
| **H1 BOS retest WR** | Slide 168-bar H1 window every 4 bars; on each bullish/bearish structure (`identify_structure_v2`, divisor 8) detect `BOS`; identify the OB (`identify_order_blocks`); on first re-entry into [ob_low, ob_high], place a `±1.5×ATR_H1` TP and `−1.0×ATR_H1` SL; first touched within 12 H1 bars wins. | 12 H1 bars | ~50-120 events per instrument-quarter |
| **Sweep+reversal WR** | Detect equal-H/L pairs (tolerance 0.10×ATR_M15, 5-50 bar partner window); on first wick beyond the level after partner-bar j, require body close back through the level by ≥0.5×ATR_M15 within 16 M15 bars. | 16 M15 bars | ~1000-2000 events per instrument-month |

### 1.2 Volatility & structure metrics (per month)

- ATR-M15(14) and ATR-H1(14) means.
- Volatility persistence: lag-1 autocorr of squared M15 log-returns.
- Trend persistence: lag-1, lag-5 autocorr of M15 log-returns.
- Hurst exponent (R/S analysis, max_lag=50).
- Displacement candle rate (body ≥ 1.5 × avg-body-20).
- BOS-per-day, CHoCH-per-day, OB-per-day rate (over 168-bar windows).
- FVG density per 100 M15 candles.
- Equal-H/L formation count.

### 1.3 H1 vs H2 split + trend tests

For each metric:
- H1 = mean over Jan + Feb monthly values; H2 = mean over Mar + Apr.
- Welch's t-test on monthly means (n=2 vs n=2 — barely informative; reported but not headline).
- For binomial WR metrics: pooled two-proportion z-test on the underlying success/total counts (the headline test).
- Linear regression slope across 4 months (1, 2, 3, 4) — p-value with n=4 has very low power; used only to break ties.
- Stability score = `1 / (1 + std(monthly)/|mean(monthly)|)`.

### 1.4 Multiple-testing corrections

- **Bonferroni** at α=0.05 across N=24 instruments → threshold p < 0.0021.
- **Benjamini-Hochberg FDR** at q=0.10. Both applied to per-instrument H1/H2 WR p-values.

### 1.5 Data quality flags

| Flag | Apr-2026 M15 candle count | Instruments |
|------|---------------------------|-------------|
| FULL | ≥ 1500 | 16 (AUDJPY, AUDUSD, BTCUSD, CHFJPY, ETHUSD, EURGBP, EURJPY, EURUSD, GBPJPY, GBPUSD, JP225, NZDUSD, US30_cash, USDCHF, USDJPY, XAUUSD) |
| PARTIAL_APR | 100-1500 | 7 (GER40, NAS100, SPX500, UK100, UKOIL_cash, USDCAD, XAGUSD) |
| NO_APR | < 100 | 1 (USOIL_cash) |

April CSV exports cut off at different dates (range Apr 2 → Apr 24). PARTIAL_APR / NO_APR instruments have low-confidence H2 numbers and are flagged in the scorecard but **not** excluded from the per-instrument tables. Pooled fleet-wide tests use only FULL data.

---

## 2. Per-Instrument Scorecard

Sorted by composite **decay_score** (0-100, higher = more decay risk; 50 = neutral baseline).
Composite uses a weighted blend of: H1-BOS-retest WR delta (primary), sweep WR delta, OB-per-day H1/H2 % change, displacement rate H1/H2 % change. All deltas multiplied by direction-aware coefficients; significance bonuses for p<0.10. Volatility regime is informational, not punitive.

### 2.1 Top-10 highest decay risk

| Rank | Instrument | Class | Quality | Comp. dir | Score | WR-H1 | WR-H2 | Δ WR (pp) | n_total | p-val |
|------|------------|-------|---------|-----------|-------|-------|-------|-----------|---------|-------|
| 1 | **GBPJPY** | FX | FULL | DECAYING | 82.1 | 66.7% | 52.5% | **−14.2** | 94 | 0.16 |
| 2 | USOIL_cash | ENERGY | NO_APR | DECAYING | 77.4 | 52.0% | 37.5% | −14.5 | 66 | 0.31 |
| 3 | **CHFJPY** | FX | FULL | DECAYING | 73.9 | 64.2% | 59.6% | −4.5 | 105 | 0.63 |
| 4 | JP225 | INDEX | FULL | DECAYING | 68.0 | 63.4% | 54.8% | −8.7 | 83 | 0.42 |
| 5 | EURGBP | FX | FULL | STABLE | 64.1 | 65.3% | 67.6% | +2.3 | 86 | 0.83 |
| 6 | **ETHUSD** | CRYPTO | FULL | MILD_DECAY | 60.8 | 66.2% | 59.6% | −6.6 | 112 | 0.48 |
| 7 | **AUDUSD** | FX | FULL | MILD_DECAY | 60.4 | 57.8% | 51.1% | −6.7 | 90 | 0.53 |
| 8 | USDCHF | FX | FULL | STABLE | 56.2 | 62.1% | 59.6% | −2.5 | 110 | 0.79 |
| 9 | XAGUSD | METALS | PARTIAL | MILD_DECAY | 55.6 | 65.8% | 56.1% | −9.7 | 79 | 0.38 |
| 10 | **USDJPY** | FX | FULL | STABLE | 55.5 | 62.7% | 61.4% | −1.3 | 108 | 0.89 |

The score-1 GBPJPY case has the largest signed delta in the FULL-data set (excluding the NO_APR USOIL with n=66 and unrepresentative single-week April). With n=94, BH-FDR rank 5 of 24 (threshold 0.0208 vs observed 0.16) — does not survive correction.

### 2.2 Bottom-10 (lowest decay risk / improving)

| Rank | Instrument | Class | Quality | Comp. dir | Score | WR-H1 | WR-H2 | Δ WR (pp) | n_total | p-val |
|------|------------|-------|---------|-----------|-------|-------|-------|-----------|---------|-------|
| 14 | **GBPUSD** | FX | FULL | STABLE | 49.6 | 55.1% | 55.0% | −0.1 | 89 | 0.99 |
| 17 | US30_cash | INDEX | FULL | VOLATILE | 45.8 | 54.2% | 59.5% | +5.3 | 101 | 0.60 |
| 18 | EURUSD | FX | FULL | VOLATILE | 40.5 | 58.0% | 63.5% | +5.5 | 102 | 0.57 |
| 19 | XAUUSD | METALS | FULL | MILD_DECAY | 39.7 | 70.9% | 60.0% | −10.9 | 71 | 0.34 |
| 20 | **AUDJPY** | FX | FULL | VOLATILE | 39.4 | 66.7% | 70.5% | +3.8 | 86 | 0.71 |
| 21 | **NZDUSD** | FX | FULL | VOLATILE | 39.0 | 57.7% | 68.5% | +10.8 | 106 | 0.25 |
| 22 | NAS100 | INDEX | PARTIAL | VOLATILE | 36.7 | 50.9% | 69.0% | **+18.1** | 93 | 0.08 |
| 23 | USDCAD | FX | PARTIAL | IMPROVING | 28.6 | 70.7% | 82.6% | +11.9 | 64 | 0.29 |
| 24 | **EURJPY** | FX | FULL | IMPROVING | 24.4 | 43.2% | 60.5% | **+17.3** | 75 | 0.13 |

Note **NAS100 +18pp** is the largest improvement signal (rank 1 by FDR, p=0.078; not Bonferroni-significant) and **EURJPY +17pp** (rank 3 FDR). Both are interesting but PARTIAL_APR and small-n.

---

## 3. Monthly WR Trajectories (BOS retest, FULL data only)

Format: month-`WR%(n)`. Sample size per month is small (n=14-30 for most instruments).

| Symbol | Jan | Feb | Mar | Apr | Trajectory |
|--------|-----|-----|-----|-----|------------|
| AUDJPY | 58%(19) | 74%(23) | 71%(24) | 70%(20) | Stable-high after Jan recovery |
| AUDUSD | 68%(19) | 50%(26) | 50%(28) | 53%(17) | **Step-down in Feb, flat since** |
| BTCUSD | 78%(27) | 65%(26) | 62%(40) | 50%(26) | **Monotonic decay** |
| CHFJPY | 64%(28) | 64%(25) | 61%(28) | 58%(24) | Slow drift down |
| ETHUSD | 70%(30) | 63%(35) | 61%(33) | 57%(14) | Slow monotonic decay |
| EURGBP | 62%(24) | 68%(25) | 59%(22) | 80%(15) | **Apr spike — small n** |
| EURJPY | 40%(15) | 45%(22) | 61%(23) | 60%(15) | **Improving — Mar regime change** |
| EURUSD | 59%(29) | 57%(21) | 63%(30) | 64%(22) | Slow drift up |
| GBPJPY | 56%(25) | 76%(29) | 58%(19) | **48%(21)** | **Whipsaw, Apr crash** |
| GBPUSD | 48%(31) | 67%(18) | 64%(22) | **44%(18)** | **Whipsaw, Apr crash** |
| JP225 | 62%(21) | 65%(20) | 54%(26) | 56%(16) | Step-down in Mar |
| NZDUSD | 71%(21) | 48%(31) | 65%(26) | 71%(28) | U-shape recovery |
| US30_cash | 60%(30) | 48%(29) | 61%(23) | 58%(19) | U-shape recovery |
| USDCHF | 64%(28) | 60%(30) | 62%(24) | 57%(28) | Slow drift down |
| USDJPY | 62%(29) | 64%(22) | 64%(33) | 58%(24) | **Stable — only mild Apr dip** |
| XAUUSD | 71%(14) | 71%(17) | 65%(20) | 55%(20) | **Monotonic decay** |

### Key observations

- **Whipsaw pattern (high CV, big swings month-to-month, mostly hover near mean WR):** GBPJPY, GBPUSD, EURGBP, NZDUSD, US30_cash. These are NOT decaying — they are noisy.
- **True monotonic decay (4-month decline):** XAUUSD (71→55%), BTCUSD (78→50%), ETHUSD (70→57%), USDCHF (64→57%), CHFJPY (64→58%). Mechanical proxy detects what live data confirms for XAUUSD.
- **Improving (4-month rise or U-shape recovery):** EURJPY (40→60%), EURUSD (59→64%), AUDJPY (post-Jan ~70%).
- **Stable:** USDJPY, USDCHF, AUDJPY, CHFJPY (all CV < 0.10, mean ~60-68%).

---

## 4. Cross-Instrument Pooling (FULL data, n=16 instruments)

### 4.1 Fleet-wide H1 vs H2 BOS retest WR

| Period | Wins | n | WR | 95% Wilson CI |
|--------|------|---|-----|---------------|
| H1 (Jan+Feb) | 487 | 789 | 61.72% | [58.27%, 65.04%] |
| H2 (Mar+Apr) | 450 | 748 | 60.16% | [56.61%, 63.61%] |
| **Delta** | | | **−1.56pp** | two-prop z=0.628, **p=0.530** |

**Interpretation.** The fleet-wide mechanical OB-retest mechanism is intact. CIs overlap heavily; the delta is well within sampling noise. **The data does NOT support a "fleet-wide structural decay" thesis.**

### 4.2 Per asset class

| Class | n inst. | H1 WR | H2 WR | Delta | p |
|-------|---------|-------|-------|-------|---|
| FX | 11 | 60.4% (n=540) | 61.1% (n=511) | +0.7pp | 0.82 |
| INDEX | 2 (FULL only: JP225, US30_cash) | 58.0% (n=100) | 57.1% (n=84) | −0.9pp | 0.91 |
| CRYPTO | 2 | 68.6% (n=118) | 58.4% (n=113) | −10.2pp | 0.106 |
| METALS | 1 (XAUUSD; XAGUSD partial) | 71.0% (n=31) | 60.0% (n=40) | −11.0pp | 0.34 |

CRYPTO + METALS show the largest directional decay; both fail to clear p=0.05 individually. FX as a class has the largest sample (n=540/511) and is **flat**.

### 4.3 JPY pairs vs non-JPY FX

| Group | n inst. | H1 WR | H2 WR | Delta | p |
|-------|---------|-------|-------|-------|---|
| JPY-pairs (GBPJPY, USDJPY, CHFJPY, AUDJPY, EURJPY) | 5 | 61.6% (n=237) | 61.0% (n=231) | −0.6pp | 0.90 |
| non-JPY (EURUSD, EURGBP, AUDUSD, NZDUSD, USDCHF, GBPUSD) | 6 | 59.4% (n=303) | 61.1% (n=280) | +1.7pp | 0.68 |

No JPY-specific decay at the pooled level. Within JPY: GBPJPY −14pp dominates the negative side; EURJPY +17pp dominates the positive side. They cancel.

---

## 5. Bonferroni / FDR — No Per-Instrument Decay Survives

Top-8 per-instrument H1/H2 BOS WR p-values (smallest p first):

| Rank | Symbol | Δ WR | n | p | Bonferroni (α/24=0.0021) | BH-FDR (q=0.10) |
|------|--------|------|---|---|--------------------------|------------------|
| 1 | NAS100 | +18.1pp | 93 | 0.0778 | NO | NO (thresh 0.0042) |
| 2 | BTCUSD | −14.1pp | 119 | 0.111 | NO | NO |
| 3 | EURJPY | +17.3pp | 75 | 0.134 | NO | NO |
| 4 | UKOIL_cash | −16.7pp | 72 | 0.157 | NO | NO |
| 5 | GBPJPY | −14.2pp | 94 | 0.165 | NO | NO |
| 6 | NZDUSD | +10.8pp | 106 | 0.248 | NO | NO |
| 7 | USDCAD | +11.9pp | 64 | 0.292 | NO | NO |
| 8 | USOIL_cash | −14.5pp | 66 | 0.312 | NO | NO |

**Zero instruments have a statistically significant H1→H2 WR change after multiple-testing correction.** Two important caveats:

- This is **not** evidence of "no decay" — the sample sizes per instrument-period (n=30-60) give limited power to detect 5-10pp deltas.
- The XAUUSD live-realized story (CLAUDE.md item 9: H1 64.5% n=31 → H2 24.0% n=25, χ² p=0.006) is far stronger than the mechanical-proxy result (71% → 60%, p=0.34). The live-realized signal is **AI-filtered + small-n + idiosyncratic period boundaries**; the mechanical proxy strips the AI filter and aggregates to 71 events.

---

## 6. Volatility Regime Hypothesis — REJECTED

H1 → H2 ATR-M15 % change, sorted asc:

| Symbol | ATR_H1 | ATR_H2 | Pct change |
|--------|--------|--------|------------|
| XAGUSD | 0.72 | 0.47 | **−35.1%** |
| ETHUSD | 12.6 | 9.6 | −23.6% |
| USDJPY | 0.116 | 0.094 | −18.6% |
| EURJPY | 0.118 | 0.096 | −18.6% |
| GBPJPY | 0.153 | 0.126 | −17.3% |
| BTCUSD | 290 | 246 | −15.4% |
| CHFJPY | 0.143 | 0.121 | −15.3% |
| XAUUSD | 15.0 | 14.1 | −5.9% |
| AUDJPY | 0.103 | 0.100 | −3.3% |
| EURGBP | 0.000349 | 0.000340 | −2.4% |
| (USDCAD) | 0.000637 | 0.000646 | +1.5% |
| USDCHF | 0.000551 | 0.000575 | +4.3% |
| (NAS100) | 39.2 | 44.5 | +13.5% |
| NZDUSD | 0.000502 | 0.000586 | +16.8% |
| GBPUSD | 0.000822 | 0.000963 | +17.1% |
| EURUSD | 0.000626 | 0.000749 | +19.5% |
| AUDUSD | 0.000592 | 0.000749 | +26.4% |
| US30_cash | 50.3 | 70.4 | +39.7% |
| (SPX500) | 7.6 | 11.0 | +44.6% |
| JP225 | 106 | 162 | +52.4% |
| (UK100) | 10.4 | 16.4 | +57.3% |
| (GER40) | 29.4 | 50.0 | +70.4% |
| (UKOIL_cash) | 0.19 | 0.74 | +287.8% |
| (USOIL_cash) | 0.19 | 0.85 | +355.1% |

(Parens = PARTIAL_APR — Apr ATR can be skewed by missing data or an extreme few days.)

**Three macro clusters:**

1. **Vol contraction**: JPY-pairs, metals, crypto. ATR fell 15-35%.
2. **Vol expansion**: USD-pairs (especially commodity dollars), indices, energy. ATR rose 15-355%.
3. **Vol stable**: EURGBP, AUDJPY, USDCHF, USDCAD (all near 0).

### 6.1 WR-delta vs vol-delta correlation

Pearson r = +0.13 (p=0.64), Spearman ρ = +0.19 (p=0.49) across 16 FULL-data instruments.

**The "vol regime drives WR" hypothesis is REJECTED.** Vol-contracting instruments (JPY pairs, metals, crypto) include both decayers (XAUUSD −11pp, BTCUSD −14pp, GBPJPY −14pp, CHFJPY −5pp) AND improvers (EURJPY +17pp, AUDJPY +4pp, USDJPY −1pp). Vol-expanding instruments (FX-USD majors, indices) include improvers (NAS100 +18pp, US30 +5pp, EURUSD +6pp, NZDUSD +11pp) AND a noise-generator (GBPUSD ~0pp).

WR-delta vs **displacement-rate-delta**: r = +0.30 (p=0.26), Spearman = +0.29 (p=0.27). Marginal positive correlation — instruments where displacement rate grew tended to have stable/improving WR. But with only 16 points and p=0.27, this is suggestive, not conclusive.

WR-delta vs **OB-per-day-delta**: r = +0.03 (p=0.91). Zero correlation — OB supply changes do not predict WR changes.

**Conclusion: Decay (where it exists) is idiosyncratic per-instrument, not driven by a unified macro regime variable.**

---

## 7. Stability Ranking (CV of monthly WR, FULL data only)

Stability score = 1 / (1 + CV).

| Rank | Symbol | Mean WR | CV | Months |
|------|--------|---------|-----|--------|
| 1 | **USDJPY** | 61.9% | 0.035 | 4 |
| 2 | **CHFJPY** | 61.8% | 0.040 | 4 |
| 3 | USDCHF | 61.0% | 0.044 | 4 |
| 4 | **EURUSD** | 60.7% | 0.047 | 4 |
| 5 | JP225 | 59.3% | 0.075 | 4 |
| 6 | ETHUSD | 62.7% | 0.075 | 4 |
| 7 | US30_cash | 56.8% | 0.088 | 4 |
| 8 | **AUDJPY** | 68.2% | 0.090 | 4 |
| 9 | XAUUSD | 65.5% | 0.100 | 4 |
| 10 | EURGBP | 67.4% | 0.118 | 4 |
| 11 | AUDUSD | 55.3% | 0.138 | 4 |
| 12 | NZDUSD | 64.2% | 0.147 | 4 |
| 13 | BTCUSD | 63.9% | 0.155 | 4 |
| 14 | GBPUSD | 55.8% | 0.171 | 4 |
| 15 | GBPJPY | 59.3% | 0.173 | 4 |
| 16 | EURJPY | 51.6% | 0.176 | 4 |

USDJPY-CHFJPY-USDCHF-EURUSD form a "ultra-stable" cluster (CV < 0.05). All four are major FX with high liquidity and consistent intraday structure — the OB-retest mechanism is extremely reliable on these.

---

## 8. AI-Side vs Market-Side Decay Decomposition

The CEO question (item 8 in `feedback_decay_is_ceo_number_one_concern.md`) asks: is decay AI-side (filter degradation) or market-side (mechanism weakening)?

Compare CLAUDE.md's **live-realized R per touch stratum / per month** to my **mechanical-proxy WR per month**:

| Symbol | CLAUDE.md live H1 WR | CLAUDE.md live H2 WR | Live Δ | Mechanical H1 WR | Mechanical H2 WR | Mech Δ | Decomposition |
|--------|----------------------|----------------------|--------|-------------------|-------------------|--------|---------------|
| **XAUUSD** | 64.5% (n=31) | 24.0% (n=25) | **−40.5pp** | 71.0% (n=31) | 60.0% (n=40) | −11.0pp | **~30pp AI-side**, ~11pp market-side |
| USDJPY | n.a. (FN profile, intermittent live) | n.a. | n.a. | 62.7% (n=51) | 61.4% (n=57) | −1.3pp | Mechanism intact |
| GBPJPY | n.a. | n.a. | n.a. | 66.7% (n=54) | 52.5% (n=40) | −14.2pp | **Material market-side decay** |
| US30_cash | n.a. | n.a. | n.a. | 54.2% (n=59) | 59.5% (n=42) | +5.3pp | Mechanism stable/improving |

**Read.** XAUUSD's catastrophic live-realized decay (−40.5pp, p=0.006) is **only ~25-30% explained by market-side mechanism weakening**. The remaining 70-75% must be AI-filter behaviour (touch-count selection, regime classification under bullish-only v1 detector during Jan-Apr, prompt drift, FN-vs-FTMO profile changes, etc.). This is consistent with CLAUDE.md item 11 (A2 v2-active backtest — XAUUSD LONG-WR 33.3% vs F3's 45.5%) and item 9's quarterly decay framing.

**By contrast, GBPJPY shows a clean market-side −14pp**: the mechanism itself weakened. This is significant because GBPJPY has been observer-mode in the live system; the decay is endogenous to the instrument, not an AI artefact.

---

## 9. Per-Instrument Verdicts (FULL data, May 2026 deployment lens)

Per the CEO instruction, each instrument is answered against four questions:
1. **STABLE or DECAYING** in dimensions that matter to OB-retest edge?
2. **If decaying, which dimension?**
3. **AI-side or market-side?**
4. **Confidence** given sample size.

| Instrument | Verdict | Driving dimension | AI vs Market | Confidence (n) |
|------------|---------|-------------------|--------------|---------------|
| **USDJPY** | STABLE — CV 0.035, Δ−1.3pp | n.a. | n.a. | High (n=108) |
| **CHFJPY** | STABLE — CV 0.040, Δ−4.5pp (slow drift) | Mild WR drift | Market-side mild | Medium (n=105) |
| **USDCHF** | STABLE — CV 0.044, Δ−2.5pp | n.a. | n.a. | High (n=110) |
| **EURUSD** | STABLE+ — CV 0.047, Δ+5.5pp | Slight improvement | Market-side mild + | High (n=102) |
| **AUDJPY** | STABLE+ — CV 0.090, Δ+3.8pp; mean 68% | Slight improvement | Market-side + | Medium (n=86) |
| **EURGBP** | STABLE — CV 0.118, Δ+2.3pp; Apr 80% n=15 outlier | Apr spike noise | Market-side, noisy | Medium (n=86) |
| **NZDUSD** | STABLE+ — CV 0.147, Δ+10.8pp | U-shape recovery | Market-side + | Medium (n=106) |
| **JP225** | MILD_DECAY — Δ−8.7pp; ATR +52% | Vol regime change + WR drop | Market-side | Medium (n=83) |
| **US30_cash** | VOLATILE → improving recently; Δ+5.3pp | Whipsaw recovery | Market-side recovery | Medium (n=101) |
| **XAUUSD** | DECAYING (mechanical −11pp) + DECAYING (live −40pp) | Both mech + AI | **~30pp AI-side, 11pp market-side** | Medium (mech n=71; live n=56) |
| **GBPJPY** | DECAYING — Δ−14.2pp | WR drop with whipsaw | Market-side, clean | Medium (n=94) |
| **GBPUSD** | VOLATILE — CV 0.171, Apr 44% n=18 | High noise; not monotonic | Market-side, noise | Medium (n=89) |
| **AUDUSD** | MILD_DECAY — Δ−6.7pp; step-down Feb | Single-month regime shift | Market-side | Medium (n=90) |
| **EURJPY** | IMPROVING — Δ+17.3pp; Mar regime change | WR recovery | Market-side + | Medium (n=75) |
| **BTCUSD** | DECAYING — Δ−14.1pp monotonic | Monotonic decay | Market-side | Medium (n=119) |
| **ETHUSD** | MILD_DECAY — Δ−6.6pp monotonic; vol −24% | WR + vol contraction | Market-side | Medium (n=112) |

### PARTIAL_APR / NO_APR — low-confidence verdicts

NAS100 (PARTIAL): +18pp directional improvement is the strongest signal in the entire fleet (p=0.078) but n=14 in April. **Re-test in May.**
EURJPY (FULL): +17pp, p=0.13. **Re-test in May.**
USDCAD (PARTIAL): +12pp, n=23 H2. **Re-test in May.**

---

## 10. Decay Clusters (`02_decay_clusters.csv`)

5-letter pattern strings from `[h1_bos_retest, ob_per_day, displacement, atr_m15, vol_persistence]` → `[D=decay, I=improving, S=stable, V=volatile]`. n=4 month linear-regression p<0.10 to call S/D/I; otherwise V.

| Pattern | Members | Interpretation |
|---------|---------|----------------|
| `SSVSV` | EURGBP, EURJPY (improving variant), EURUSD, GBPUSD, NZDUSD, USDJPY | "Boring" FX — most metrics undetermined at n=4, no trend |
| `SSVVV` | AUDUSD, JP225, UK100, USOIL_cash, XAGUSD | Edge metrics stable, vol/regime volatile |
| `DSVVV` | BTCUSD, XAUUSD | **Edge mechanism decay; volatile vol regime** |
| `DSVSD` | CHFJPY | Decay + dead-zone vol persistence — odd |
| `SSVSD` | GBPJPY, AUDJPY | Stable headline; vol persistence decay (info only) |

Most members fall into "noisy, undetermined" patterns because n=4 monthly samples give very low statistical power. The patterns are descriptive, not predictive.

---

## 11. Mechanism-Specific Conclusions for the OB-Retest Framework

The live system runs `model_a.enabled_frameworks: [ob_retest]` only. The H1 BOS retest mechanical proxy is the most direct backtest mirror of that production framework (modulo AI filter, touch-count gate, kill-zone restriction).

**Implications for May 2026 expansion:**

1. **Top tier (highest expected stability, deploy with confidence):** USDJPY, CHFJPY, USDCHF, EURUSD. All have CV < 0.05 and mean WR 60-62%. EURJPY is borderline (improving but high CV).
2. **Active live, monitor:** XAUUSD (continue, but plan v2 promotion + monthly-decay shadow ALERT — Item 12), USDJPY (continue), GBPJPY (live observer per CLAUDE.md; **flag −14pp mechanical decay — do NOT promote to live trading without further investigation**), GBPUSD (observer per `gbpusd_observer_mode_decision_2026-04-24.md`; high CV confirms thinness), US30_cash (continue, mild U-shape recovery).
3. **Candidates worth probing for May add:** AUDJPY (mean 68%, CV 0.09, +3.8pp delta — best risk-adjusted), NZDUSD (Δ+10.8pp recovery, CV 0.15 borderline), EURUSD (CV 0.05).
4. **Avoid for now:** BTCUSD (monotonic decay −14pp + crypto liquidity issues), GBPJPY trading promotion (−14pp decay), AUDUSD (step-down decay, mean WR 55%), EURJPY (improving but n=15-22 per month).

---

## 12. Limitations & Honest Caveats

1. **n=4 months has very low statistical power.** Per-instrument p-values rarely cross 0.10 even for 15pp deltas with n=80-100. This analysis is correlational/directional, not confirmatory.
2. **April 2026 data is partial for 8 instruments.** Their H2 numbers should be re-validated end-of-April or end-of-May.
3. **Mechanical proxy ≠ live realized.** XAUUSD demonstrates the gap is large (−40pp live vs −11pp mechanical). The mechanical proxy is necessary-but-not-sufficient evidence.
4. **The proxy uses `identify_structure_v2` (divisor 8).** ADR-004 v1 vs v2 cutover started 2026-04-24 — Jan-Apr live data was 100% v1-bullish. This decay analysis uses v2 throughout. The "what would v1 mechanical have looked like" question is out of scope but answerable by re-running with `--detector-version v1` (a one-line change).
5. **Out-of-sample test for the scorecard is weak** — no walk-forward CV. May 2026 first-2-weeks live data will validate or invalidate the rankings.
6. **Sweep+reversal WR (~70% across all) is robust but volatile in absolute terms.** The mechanism is highly stable cross-instrument (CV < 0.03 across all instruments after pooling; only USDJPY +2.8pp and GER40 −5.2pp hit p<0.05). Sweep-reversal is **not the source of the OB-retest decay** — confirmed.
7. **No control for kill-zone vs full-day events.** Live edge is restricted to KZ; mechanical proxy uses all 24h. The live decay number could be larger if KZ-specific decay exists.
8. **No correlation-cluster overlap correction.** EURJPY/USDJPY/GBPJPY are correlated (>0.6 daily). My pooled tests treat them as independent, which inflates effective n. The true effective n for the JPY-cluster is closer to 1.5-2 instruments.

---

## 13. Recommendations Tied to Monday FTMO Challenge

1. **Stay on existing 5 (XAUUSD, US30, USDJPY, GBPJPY, GBPUSD).** No mechanical evidence supports adding new instruments before live-data validation. USDJPY is the safest carry — keep risk normal. XAUUSD: ship S1 monthly-decay alert (Item 12), keep on v2_shadow until 14d+ promotion gate clears.
2. **GBPJPY**: This analysis flags clean market-side decay (−14pp Δ, n=94). It is currently observer-mode. **Do NOT promote to live trading on May 1.** Re-evaluate end-May after another 30 H1-BOS samples accumulate.
3. **GBPUSD**: high CV is consistent with the observer-cost-decision (`project_gbpusd_observer_cost.md`); the mechanical analysis adds no new signal. Carry on observer through April per memo, revisit end-of-month.
4. **For May 1 promotion candidates**, the mechanical analysis suggests this priority order: **AUDJPY > NZDUSD > EURUSD > CHFJPY > EURGBP**. AUDJPY has the best (mean WR × stability × directional improvement) profile. Defer to A1's structural screen and A3's microstructure analysis for final selection.
5. **Re-run this analysis end-of-May** with a fully-populated April + first 3 weeks of May. The H1/H2 split becomes Jan+Feb+Mar vs Apr+May with 50% more H2 power.

---

*Analysis: 2026-04-25 by Tier 1 Agent #2. Code: `02_decay_analysis.py` + `_run_parallel.py` + `_pooled_analysis.py`. Runtime: ~33 seconds across 8 worker processes. $0 API spend.*
