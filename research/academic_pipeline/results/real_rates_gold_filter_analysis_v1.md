# Real Rates Gold Filter Analysis — XAUUSD OB Trades

**Date:** 2026-04-13
**Analyst:** Claude Code (Strategic Research Advisor pipeline)
**Test type:** $0 retrospective analysis using existing batch data + free public TIPS data
**Hypothesis pre-stated:** Bullish gold OB + falling real rates = ALIGNED = higher WR than misaligned

---

## Executive Summary

**VERDICT: REJECT real rates as a filter. Evidence does not support implementation.**

The 8.5 percentage-point WR advantage for ALIGNED trades (69.6% vs 61.1%) is not statistically significant (p=0.74, OR=1.455). The study is under-powered by 27.6x for this effect size. Crucially, misaligned trades show **higher mean R-multiple (+0.551R vs +0.378R)**, meaning the filter would reduce expected monthly R by approximately 1.73R while eliminating only 18% of trades for marginal WR improvement. The batch data covers a single macro regime (real yields 1.58%-2.20%, always positive), limiting generalizability.

---

## 1. Data Summary

### TIPS Yield Data

**Source:** US Treasury Department — Real Yield Curve (TIPS, 10-year maturity)
**URL format:** `https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{year}/all?type=daily_treasury_real_yield_curve`
**Series name:** 10-Year Real Yield (equivalent to FRED DFII10)
**Coverage:** 2024-01-02 to 2026-04-10 (568 trading days)
**Missing data:** 0 gaps in yield series itself

**Data quality notes:**
- Two trade dates fell on US federal holidays (Presidents Day 2025-02-17, MLK Day 2026-01-19). Both filled with the prior trading day's value (T-3, i.e., prior Friday), which is standard practice for daily regime filters.
- As required by prompt protocol, T-1 day's yield was used for each trade (simulating live implementation where today's yield isn't available until end-of-day).

### Gold Trade Data

**Source:** `research/academic_pipeline/data/entry_engineering_dataset.csv`
**Total XAUUSD trades in file:** 105
**Valid for analysis** (after filtering UNKNOWN alignment and blank direction): **100 trades**
**Date range:** 2024-04-01 to 2026-03-13
**Win rate (baseline):** 63.0% (63/100) — 95% CI: 53.2%–71.8%

**Trade direction distribution:**
- LONG: 100/100 (100% of valid trades)
- SHORT: 0 (note: 5 trades excluded had blank direction field)

**Bull market bias confirmed:** Every valid gold trade in the batch was LONG. This collapses the alignment dimension to be equivalent to the rate direction dimension — there is no meaningful difference between "aligned" and "falling rates" in this dataset.

---

## 2. Real Rate Regime Distribution

Real yield range across trade dates: **1.58% to 2.20%** (mean 1.94%)

All yields are **positive** throughout the entire batch period. The dataset contains zero observations of negative real rates (which characterized the 2021-2022 gold bull run). This is a single macro regime — moderately restrictive real rates — which limits the test's discriminatory power.

**Rate direction (5-day lookback, 5 bps threshold):**

| Regime | Trades | % of Sample |
|--------|--------|-------------|
| RISING | 18 | 18.0% |
| FLAT | 59 | 59.0% |
| FALLING | 23 | 23.0% |

**Key observation:** 59% of trades occur during FLAT rate regimes (yield change within ±5bps over 5 days). This large FLAT category dominates the sample and limits statistical power in the ALIGNED/MISALIGNED comparison.

---

## 3. Alignment Analysis (Primary: 5-day lookback, 5 bps threshold)

Since all trades are LONG, alignment simplifies to:
- ALIGNED = FALLING rates (gold bull thesis + macro tailwind)
- MISALIGNED = RISING rates (gold bull thesis + macro headwind)
- FLAT = Neutral macro backdrop

| Alignment | n | Wins | WR | 95% CI | Mean R |
|-----------|---|------|----|--------|--------|
| ALIGNED | 23 | 16 | 69.6% | 49.1%–84.4% | +0.378 |
| MISALIGNED | 18 | 11 | 61.1% | 38.6%–79.7% | +0.551 |
| FLAT | 59 | 36 | 61.0% | 48.3%–72.4% | +0.098 |
| **BASELINE** | **100** | **63** | **63.0%** | 53.2%–71.8% | **+0.244** |

**Counterintuitive finding:** MISALIGNED trades have the highest mean R-multiple (+0.551R), nearly 50% higher than ALIGNED (+0.378R). This suggests that when gold OBs succeed against rising real rates, the moves are larger — consistent with short-squeeze dynamics where macro headwinds delay the OB trigger but the eventual move is more explosive.

---

## 4. Statistical Tests

### Fisher Exact Test — ALIGNED vs MISALIGNED (primary)

| Metric | Value |
|--------|-------|
| Contingency table | [[16, 7], [11, 7]] |
| Odds Ratio | 1.455 |
| p-value | 0.7417 |
| Effect size | +8.5 pp |
| Significant at p<0.05? | NO |
| Significant at p<0.10? | NO |

### Fisher Exact Test — ALIGNED vs FLAT

| Metric | Value |
|--------|-------|
| Odds Ratio | 1.460 |
| p-value | 0.6113 |
| Significant at p<0.05? | NO |

### Fisher Exact Test — FALLING vs RISING rates (direction-blind)

| Metric | Value |
|--------|-------|
| Odds Ratio | 1.455 |
| p-value | 0.7417 |
| Significant at p<0.05? | NO |

**Note:** The identical result for ALIGNED vs MISALIGNED and FALLING vs RISING is because all trades are LONG — these are literally the same test.

### Statistical Power Analysis

To detect an 8.5pp effect (observed difference) with 80% power at α=0.05:
- **Required n per group: 497**
- **Current n: 23 aligned, 18 misaligned**
- **Under-powered by 27.6x**

This test is severely underpowered. Even a 20pp real effect would require ~70 trades per group. Given that only 23% of gold trades occur during distinctly FALLING rate regimes, accumulating 497 such observations would require approximately **175 years of trading at current frequency** if rates remain in this regime distribution.

---

## 5. Filter Backtest

**Filter design:** Skip trades where alignment = MISALIGNED (rising rates during LONG trade setups). Trade when ALIGNED or FLAT.

| Metric | Value |
|--------|-------|
| Trades kept | 82 (82.0%) |
| Trades skipped | 18 (18.0%) |
| Kept trades WR | 63.4% (95% CI: 52.6%–73.0%) |
| Skipped trades WR | 61.1% (95% CI: 38.6%–79.7%) |
| Baseline WR | 63.0% |
| WR improvement | +0.4 pp |
| Monthly trades lost | ~3.1/month |
| Mean R — kept | +0.177R |
| Mean R — skipped | +0.551R |
| Monthly R baseline | +4.27R |
| Monthly R with filter | +2.53R |
| **Net R impact** | **-1.73R/month** |

**Critical finding:** Applying the filter would reduce expected monthly R by approximately **1.73R** while improving WR by only 0.4pp. The filter selectively eliminates the highest-R trades in the sample. This makes the filter actively harmful under current data.

The WR of skipped trades (61.1%) is nearly identical to baseline (63.0%), confirming that misaligned trades are not materially worse — they are just as viable setups as aligned ones.

---

## 6. Sensitivity Analysis

### 6a. Lookback Period (threshold fixed at 5 bps)

| Lookback | ALIGNED n | ALIGNED WR | MISALIGNED n | MISALIGNED WR | Diff | p-value |
|----------|-----------|------------|--------------|---------------|------|---------|
| 3-day | 14 | 64.3% | 13 | 53.8% | +10.4 pp | 0.704 |
| **5-day** | **23** | **69.6%** | **18** | **61.1%** | **+8.5 pp** | **0.742** |
| 10-day | 25 | 60.0% | 22 | 59.1% | +0.9 pp | 1.000 |

The 3-day lookback shows the largest raw WR difference (+10.4pp) but with fewer trades and no significance. The 10-day lookback produces near-zero effect. No lookback period yields p<0.10.

### 6b. BPS Threshold (lookback fixed at 5 days)

| Threshold | ALIGNED WR | MISALIGNED WR | FLAT n | Diff | p-value |
|-----------|------------|---------------|--------|------|---------|
| 3 bps | 65.6% (n=32) | 70.6% (n=34) | 34 | -5.0 pp | 0.793 |
| **5 bps** | **69.6% (n=23)** | **61.1% (n=18)** | **59** | **+8.5 pp** | **0.742** |
| 10 bps | 60.0% (n=10) | 83.3% (n=6) | 84 | -23.3 pp | 0.588 |
| 15 bps | too few | — | — | — | — |

**Notable:** At 3 bps threshold (almost all non-flat trades classified), MISALIGNED outperforms ALIGNED (-5.0pp reversal). At 10 bps, MISALIGNED strongly outperforms (+23.3pp reversal), though n=6. This pattern instability across thresholds is the hallmark of noise, not signal.

### 6c. Rate Momentum Strength (5-day, 5 bps threshold)

| Momentum | ALIGNED WR | MISALIGNED WR | Diff |
|----------|------------|---------------|------|
| Strong (>10 bps) | 60.0% (n=10) | 83.3% (n=6) | -23.3 pp |
| Weak (5-10 bps) | 76.9% (n=13) | 50.0% (n=12) | +26.9 pp |

These extreme reversals at different momentum strengths are diagnostic of random variation in a small sample. The "strong move" category shows MISALIGNED dramatically outperforming ALIGNED — the opposite of the hypothesis. Both cells are too small (n<13) for any interpretation.

### 6d. Real Yield Level vs WR

| Yield Level | n | WR |
|-------------|---|-----|
| High (>2.0%) | 25 | 72.0% |
| Mid (1.8%–2.0%) | 63 | 61.9% |
| Low (<1.8%) | 12 | 50.0% |

**Interesting but unexplained:** Higher absolute real yield levels weakly associated with higher WR. This could reflect that higher real rate environments (late 2024, early 2025) coincided with lower gold volatility and cleaner OB structures, OR it is a small-sample artifact. This finding was not pre-hypothesized and should not be acted upon without prospective validation.

---

## 7. Critical Confounds and Limitations

### 7a. All-LONG Sample — Macro Conflation

100% of valid trades are LONG. The batch period (Apr 2024 – Mar 2026) was a sustained gold bull market. This makes it impossible to separate:
1. "OB success rate improves when aligned with macro"
2. "Gold bull market produces high WR regardless of short-term rate moves"

There are zero SHORT trades to test the other half of the alignment hypothesis. This is the single largest limitation of this test.

### 7b. Single Macro Regime

Real yields ranged 1.58%–2.20% across the entire batch period — always positive, moderate restrictiveness. The gold-rates relationship is theoretically most powerful in regime shifts (negative → positive real rates or vice versa). We cannot test behavior in a negative real rate environment or during a genuine rate regime transition from this data.

### 7c. Underpowered By Design

With 23 ALIGNED and 18 MISALIGNED observations, this test had approximately 3.5% power to detect the 8.5pp effect it observed. The null result (p=0.74) is completely uninformative — failing to reject null with 3.5% power means nothing.

### 7d. Timing Mismatch

TIPS yields are end-of-day publications. Intraday gold OB trades trigger on M15/H1 candles. The 5-day lookback is a coarse daily regime filter applied to high-frequency structure. Even if real rates influence gold directionally at the daily level, the OB retest mechanism operates within hours and may be orthogonal to multi-day rate trends.

### 7e. Threshold Instability

The sign of the effect reverses across BPS thresholds (3 bps: -5pp; 5 bps: +8.5pp; 10 bps: -23pp). This is the defining characteristic of noise, not signal. A real effect should be monotonically directional across reasonable threshold choices.

---

## 8. Theoretical Assessment

The academic literature (Erb & Harvey 2013, Baur & Lucey 2010) documents that real rates explain gold price levels over multi-year horizons. The relationship is well-established at monthly/quarterly frequencies. There is no strong academic basis for expecting this macro relationship to manifest at the 5-day rate change / intraday OB retest level. The mechanism mismatch is fundamental:

- **Academic finding:** Real yield level (not change direction) predicts gold price level over years
- **Our test:** Real yield change direction (5-day) predicts intraday OB trade success

These are very different claims. Our OB edge comes from structural stop-cascade dynamics that play out in hours — a macro regime filter operating on weeks of rate movement is theoretically too coarse to affect that mechanism.

---

## 9. Recommendation

### VERDICT: REJECT real rates filter

**Criteria checked:**

| Criterion | Threshold | Observed | Pass? |
|-----------|-----------|----------|-------|
| WR difference (ALIGNED vs MISALIGNED) | ≥10 pp | +8.5 pp | NO |
| p-value | <0.05 | 0.74 | NO |
| Filter doesn't kill too many trades | <30% frequency drop | 18% drop | YES |
| WR improvement > frequency cost | Net R positive | -1.73R/month | NO |
| Effect stable across thresholds | Same direction | NO (reverses) | NO |

**Decision:** Do NOT implement a real rates filter. Continue purely technical approach.

**Reasoning:**
1. No statistically significant WR difference by alignment (p=0.74)
2. Applying the filter reduces expected monthly R by 1.73R
3. Effect sign reverses across parameter choices — consistent with noise
4. Test is under-powered by 27.6x even at observed effect size
5. Theoretical mechanism mismatch: macro annual cycles vs intraday OB dynamics
6. The prior tests of macro filters (DXY: R²=0.136, COT: p=0.495) also found null results — consistent pattern across all macro inputs tested

---

## 10. What This Confirms

This null result is useful. Combined with prior work:

| Macro Factor | Test | Result |
|-------------|------|--------|
| COT positioning | Spearman correlation (n=209) | p=0.495, NULL |
| DXY correlation | Regression (n=816 days) | R²=0.136, too weak for filter |
| Real rates (TIPS 10-yr) | Fisher exact by alignment | p=0.74, NULL |

**Pattern:** Three independent macro inputs, three null results. The GTOS edge is structural/mechanical (OB zone precision, stop-cascade dynamics) and does not benefit from macro overlay at the frequencies being tested. This confirms the decision to remain purely technical.

---

## 11. If We Wanted More Data

To properly power this test for the 8.5pp effect size observed:
- Need **497 trades per group** in non-FLAT rate regimes
- At current XAUUSD frequency (~17 trades/month), 23% in FALLING regimes → ~4 FALLING-regime trades/month
- To reach 497 aligned trades: **~124 months (10+ years)** at current frequency
- This test is not feasibly powered from internal data alone

If the CEO wishes to pursue this further, the practical path is:
1. **Shadow log** the real rate regime for every live XAUUSD trade prospectively
2. Revisit after 50+ non-FLAT observations (approximately 2-3 years of live trading)
3. Cross-validate against any available external research on intraday gold-rates relationship

---

## Appendix A: Raw Data Summary

**Yield data file:** `research/academic_pipeline/data/dfii10_real_yield.json` (568 entries, 2024-01-02 to 2026-04-10)
**Annotated trade file:** `research/academic_pipeline/data/real_rates_annotated_trades.json` (105 trades with rate annotations)
**Source:** US Treasury Department Real Yield Curve CSV API

**Annotated trade fields added:**
- `real_yield` — 10-year real yield on T-1 day
- `rate_direction_5d` — RISING/FALLING/FLAT (5-day, 5bps threshold)
- `alignment_5d` — ALIGNED/MISALIGNED/FLAT (5-day primary)
- `alignment_3d` — same for 3-day lookback
- `alignment_10d` — same for 10-day lookback

---

*Analysis run by Claude Code, April 13, 2026. All data sourced from public sources (US Treasury.gov). Zero API cost. No data fabricated.*
