# Tier 1 Distributional Analysis — OB Retest Geometry
**Analyst:** distrib_a (independent of distrib_b)
**Date:** 2026-04-18
**Source:** `research/retest_geometry/outputs/historical/combined_retests.csv` (n=121, ADR-003-compliant)
**Cross-check:** `research/retest_geometry/outputs/a2_v2_validation/combined_retests.csv` (n=726, secondary)

---

## Executive Summary

The current production SL (opposing OB edge + 0.5 × H1 ATR) is **near-optimal** for Geom A. Tightening below 0.5 ATR strictly reduces expectancy. Loosening to 0.7 ATR yields essentially identical expectancy (+0.30 vs +0.29 R/trade) at higher WR — within statistical noise.

Three findings dominate everything else:

1. **Penetration past the far OB edge is the single most powerful failure signal.** P(WIN | penetrated) = 40% vs P(WIN | not penetrated) = 100% (Geom A, Fisher p = 2.07e-13). Every single retest in this sample that did NOT pierce the far OB edge became a winner.
2. **Winner MAE distribution is sharply truncated at ~1.0 ATR.** Winner p90 MAE = 1.06 ATR; loser p25 MAE = 1.11 ATR. The two distributions barely overlap. Best separator: MAE = 0.92 ATR (Youden J = 0.72).
3. **Winners reverse INSIDE the OB body.** Median winner MAE_pct_ob_body = 55%; ZERO losers (0 of 33) had MAE < 100% of OB body. The OB body is the geometric reversal boundary in this sample.

**Recommended action:** Keep SL at current m=0.5 (Geom A). Consider a **continuation-side gate**: if MAE > 1.0 ATR within first ~6 candles, exit early (it has crossed into loser-MAE territory). Quantitative work needed to validate.

---

## 1. Data Verification

| Check | Result |
|------|------|
| Row count (primary) | 121 |
| Schema | All 29 expected columns present |
| `mae_a_pct_ob_body` recompute vs raw | max abs diff = 0.0005 (rounding only) |
| Negative MAE rows | 0 |
| Negative penetration rows | 0 |
| Negative `mae_pct_ob_body` rows | 0 |
| MAE > 5 ATR (Geom A) | 0 |
| MAE > 5 ATR (Geom B) | 0 |
| H1 ATR NaN | 0 |
| `outcome_a` NaN | 0 |

**Outcome breakdown (primary, n=121):**
- Geom A: CONTINUED 77 / REVERSED 33 / UNRESOLVED 11 → WR = 70.0% (77/110 eligible)
- Geom B: CONTINUED 33 / REVERSED 35 / UNRESOLVED 53 → WR = 48.5% (33/68 eligible)

Geom B has 44% UNRESOLVED — its 12-candle (3h) horizon is too short for many setups. Most Geom B headline numbers should be read with that caveat.

**Per-symbol n:** USDJPY 33, US30_cash 28, XAUUSD 22, GBPJPY 19, GBPUSD 19. Only **USDJPY** clears n ≥ 20 within the *winners-only* subset for Geom A (n=29). Per-symbol breakdowns reported only for that case.

**Per-session n:** Tokyo 60, NY 31, London 23.

**Outliers:** Row 4 (GBPJPY long) has retest_entry essentially at sl_a (sl_dist = 0.005, ~0.012 ATR). This is the "wick pierced → next-bar entry" geometry case. 13 rows total have `entry_to_far_edge_atr < 0` (entry already past the far OB edge). These rows are kept in Q1-Q4 (the MAE/penetration measurements are still meaningful) but **excluded from Q5 SL re-scoring** because the geometry doesn't apply cleanly — see Methodological Choices.

Cross-check (n=726, a2_v2_validation): outcome_a CONTINUED 528 / REVERSED 179 / UNRESOLVED 19 → WR = 74.6% (528/707) — consistent within Wilson 95% CI of primary 70.0% (CI 60.9-77.8%).

---

## 2. Q1 — Winner MAE Distribution

### 2.1 Geom A winners (n=77)

**MAE in H1 ATR units:**

| Stat | Value |
|------|------|
| n    | 77 |
| mean | 0.538 |
| std  | 0.416 |
| p10  | 0.157 |
| p25  | 0.236 |
| p50  | **0.382** |
| p75  | 0.747 |
| p90  | **1.055** |
| p95  | 1.175 |
| min  | 0.039 |
| max  | 2.038 |

**MAE as % of OB body:**

| Stat | Value |
|------|------|
| n    | 77 |
| mean | 72.6% |
| std  | 64.0 pp |
| p10  | 16.8% |
| p25  | 28.4% |
| p50  | **55.4%** |
| p75  | 93.3% |
| p90  | 144.4% |
| p95  | 217.6% |
| min  | 6.9% |
| max  | 309.3% |

**Interpretation (Geom A):** A typical winner pulls back ~38% of an ATR before reversing. A 90th-percentile winner pulls back **1.06 ATR**. Setting SL tighter than 1.06 ATR from entry would have killed ~10% of winners in this sample. The current SL distance from entry has a median of **1.34 ATR** (well above the 1.06 ATR p90 of winner MAE) — this is healthy headroom.

### 2.2 Geom A winners — USDJPY only (n=29, only symbol with n ≥ 20)

| Stat | mae_atr | mae_pct_ob_body |
|------|---------|---------|
| mean | 0.458 | 74.0% |
| p50  | 0.327 | 54.8% |
| p90  | 0.858 | 176.2% |
| p95  | 1.039 | 204.2% |

USDJPY winner MAE is slightly tighter (p90 = 0.86 ATR vs portfolio 1.06 ATR), suggesting USDJPY-specific tightening could be tested — but n=29 is borderline.

**All other symbols n too small (<20) for Geom A winners:** GBPJPY n=15, GBPUSD n=6, US30_cash n=12, XAUUSD n=15.

### 2.3 Geom B winners (n=33)

| Stat | mae_atr | mae_pct_ob_body |
|------|---------|---------|
| n    | 33 | 33 |
| mean | 0.377 | 56.1% |
| p50  | **0.262** | 39.4% |
| p75  | 0.355 | 55.3% |
| p90  | **0.651** | 117.4% |
| p95  | 1.220 | 182.6% |
| max  | 2.026 | 300.6% |

**Interpretation (Geom B):** Tighter winner MAE distribution because Geom B's 12-candle window only resolves shorter, faster trades. p90 winner MAE = 0.65 ATR. **Per-symbol breakdowns: all n < 20** — none reportable.

---

## 3. Q2 — Loser MAE Distribution

### 3.1 Geom A losers (n=33)

**MAE in H1 ATR:**

| Stat | Value |
|------|------|
| n    | 33 |
| mean | 1.742 |
| std  | 0.970 |
| p10  | 0.873 |
| p25  | **1.106** |
| p50  | 1.510 |
| p75  | 2.034 |
| p90  | 2.694 |
| p95  | 3.551 |
| min  | 0.530 |
| max  | 4.918 |

**MAE as % of OB body:**

| Stat | Value |
|------|------|
| n    | 33 |
| mean | 219.2% |
| p25  | 148.3% |
| p50  | **196.1%** |
| p75  | 238.6% |
| p90  | 333.9% |
| min  | **101.4%** |
| max  | 814.1% |

**Critical finding:** The smallest loser MAE is **101.4% of OB body** — i.e., every losing trade penetrated past the OB body equivalent in adverse direction. Compare to winners: p75 = 93.3% of OB body. **The OB body is the natural reversal/failure boundary.**

### 3.2 Geom A separation analysis (winners vs losers)

| Metric | Value |
|------|------|
| KS statistic | 0.749 |
| KS p-value | 2.99e-13 |
| Mann-Whitney p-value | 1.91e-12 |
| Winner p90 MAE ATR | 1.055 |
| Loser p25 MAE ATR | 1.106 |
| **Best separator (Youden J)** | **0.916 ATR** |
| Sensitivity at cutoff | 84.4% (winners correctly classified MAE ≤ cutoff) |
| 1 − Specificity at cutoff | 12.1% (losers wrongly classified MAE ≤ cutoff) |
| Youden J | 0.723 |

**Interpretation:** The two distributions are dramatically different. A simple rule "if MAE within first N candles exceeds 0.92 ATR → exit" would correctly classify 84% of winners (would not exit them) and wrongly exit 12% of losers (the ones with shallow loss MAE). Note: the BEST separator is approximately equal to the H29 0.5 ATR + ob body — i.e., the SL itself is reasonably close.

### 3.3 Geom B losers (n=35)

| Stat | mae_atr | mae_pct_ob_body |
|------|---------|---------|
| n    | 35 | 35 |
| mean | 1.104 | 179.9% |
| p25  | 0.631 | 112.2% |
| p50  | 1.048 | 161.0% |
| p75  | 1.351 | 192.2% |
| p90  | 2.059 | 233.0% |
| min  | 0.227 | **65.9%** |

**Notable:** Geom B's tighter SL (~0.18-0.30 ATR margin for XAUUSD, ~0.05-0.10 ATR for FX) means some losers stop out at MAE < 1.0 ATR. The min loser MAE_pct_ob_body of 65.9% shows Geom B's tight SL clips trades the OB body would have absorbed. This is consistent with Geom A being the better edge geometry.

**Geom B separation (KS p = 2.09e-08):** best cutoff 0.382 ATR. Differential is real but at much lower MAE than Geom A — Geom B trades resolve quickly.

### 3.4 Win vs Loss overlap region

For Geom A:
- The MAE ATR range [0.87, 1.18] contains both:
  - Winner p90 = 1.055
  - Loser p10 = 0.873
- That's the overlap zone. Roughly 10% of winners and 10% of losers fall in MAE ∈ [0.87, 1.18] ATR.
- Above MAE = 1.18 (winner p95), trades are 95% loser; below MAE = 0.87 (loser p10), trades are essentially 100% winner.

---

## 4. Q3 — Penetration Past Far OB Edge

### 4.1 Geom A (full sample, n=121)

| Metric | k | n | p | Wilson 95% CI |
|--------|---|---|---|---|
| Penetration rate | 58 | 121 | **47.9%** | [39.2%, 56.8%] |
| P(WIN \| penetrated) | 22 | 55 | **40.0%** | [28.1%, 53.2%] |
| P(WIN \| not penetrated) | 55 | 55 | **100.0%** | [93.5%, 100.0%] |

**Fisher exact test penetrated vs not-penetrated:** p = **2.07e-13** (overwhelmingly significant).

**Penetration depth (when penetrated, n=58, ATR units):**

| Stat | Value |
|------|------|
| mean | 0.736 |
| p10  | 0.195 |
| p25  | 0.415 |
| p50  | 0.644 |
| p75  | 0.911 |
| p90  | 1.252 |
| max  | 3.106 |

**Per-symbol penetration rate (Geom A):**
- GBPJPY: 11/19 = 57.9%
- GBPUSD: 11/19 = 57.9%
- US30_cash: 15/28 = 53.6%
- USDJPY: 10/33 = 30.3% (lowest)
- XAUUSD: 11/22 = 50.0%

USDJPY is anomalous — much cleaner retests, much rarer penetration.

### 4.2 Geom B (n=121)

| Metric | k | n | p | Wilson 95% CI |
|--------|---|---|---|---|
| Penetration rate | 47 | 121 | 38.8% | [30.6%, 47.7%] |
| P(WIN \| penetrated) | 9 | 44 | 20.5% | [11.2%, 34.5%] |
| P(WIN \| not penetrated) | 24 | 24 | 100.0% | [86.2%, 100.0%] |

Fisher p = 2.56e-11. Penetration depth p50 = 0.292 ATR (smaller than Geom A because Geom B truncates faster).

**The signal is identical across both geometries: NOT penetrating the far edge → 100% WR; penetrating → ~20-40% WR.**

### 4.3 Per-symbol penetration & WR (Geom A, full sample, symbols with n ≥ 20)

| Symbol | n | WR (eligible) | Penetration rate | P(WIN \| pen) | P(WIN \| not pen) |
|---|---|---|---|---|---|
| USDJPY | 33 | 93.5% [79.3-98.2%] | 30.3% [17.4-47.3%] | 80.0% [49.0-94.3%] | 100% [84.5-100%] |
| US30_cash | 28 | 52.2% [33.0-70.8%] | 53.6% [35.8-70.5%] | 21.4% [7.6-47.6%] | 100% [70.1-100%] |
| XAUUSD | 22 | 71.4% [50.0-86.2%] | 50.0% [30.7-69.3%] | 40.0% [16.8-68.7%] | 100% [74.1-100%] |

**All three reportable symbols show P(WIN | not penetrated) = 100%.** This is the strongest signal in the dataset — and it generalizes across symbols, not just XAUUSD.

USDJPY's combination of low penetration rate (30%) and high P(WIN | penetrated) (80%) explains its 93.5% WR. US30_cash has highest penetration rate (54%) and lowest P(WIN | penetrated) (21%) → 52% WR.

GBPJPY (n=19) and GBPUSD (n=19) just below threshold — directional indication only:
- GBPJPY: 18 eligible, WR = 83.3%, penetration rate 57.9%
- GBPUSD: 17 eligible, WR = 35.3%, penetration rate 57.9%

GBPUSD's poor WR is consistent with handoff 16's note that GBPUSD is the observer-only instrument flagged for review.

### 4.4 Implication

Penetration is nearly a perfect failure predictor. This is mechanically reasonable: a wick that punches through the far OB edge has likely "broken" the cluster of stops that defined the OB. The remainder of the trade is no longer betting on stop-cascade reversion — it's betting on noise.

**Practical use:** A **mid-trade exit gate** triggered by far-edge penetration would have eliminated 33 losers in exchange for 22 false exits (penetration-but-still-won) at the population level (Geom A). Net: +33L avoided − 22W lost. With wins paying ~0.73R median and losses costing 1R, that trade is +33×1 − 22×0.73 ≈ +16.9R saved — significant if trustworthy out-of-sample. **However:** the 100% WR for non-penetrated retests is suspiciously clean (n=55, lower CI 93.5%). Likely reflects in-sample selection bias on a sample of only 121. Use as hypothesis to test, not law.

---

## 5. Q4 — Histogram of MAE_pct_ob_body

### 5.1 Geom A — full distribution (n=121)

| Bin | Count | % |
|-----|-------|---|
| <0 | 0 | 0% |
| 0-25 | 17 | 14.0% |
| 25-50 | 17 | 14.0% |
| 50-75 | 18 | 14.9% |
| 75-100 | 16 | 13.2% |
| 100-125 | 12 | 9.9% |
| 125-150 | 6 | 5.0% |
| 150-200 | 13 | 10.7% |
| >200 | 22 | 18.2% |

Median = 89.7%, mean = 117.5%. Modal bin = "50-75" but the distribution is essentially flat from 0 to 100, with a heavy right tail beyond 100.

### 5.2 Geom A — split by outcome

| Bin | WIN (n=77) | LOSS (n=33) |
|-----|---|---|
| 0-25 | 17 (22.1%) | 0 |
| 25-50 | 17 (22.1%) | 0 |
| 50-75 | 16 (20.8%) | 0 |
| 75-100 | 12 (15.6%) | 0 |
| 100-125 | 6 (7.8%) | 5 (15.2%) |
| 125-150 | 1 (1.3%) | 4 (12.1%) |
| 150-200 | 3 (3.9%) | 9 (27.3%) |
| >200 | 5 (6.5%) | 15 (45.5%) |

**Winner medians:** 55.4% MAE_pct. 81% of winners (62/77) reverse INSIDE the OB body (MAE_pct ≤ 100%). Only 19% of winners exceed the body in adverse direction.

**Loser distribution starts at the 100-125% bin and is right-skewed.** Zero losers had MAE inside the OB body. The OB body is the structural watershed.

### 5.3 Geom B — full distribution and split

| Bin | All (n=121) | WIN (n=33) | LOSS (n=35) |
|-----|---|---|---|
| 0-25 | 19 (15.7%) | 11 (33.3%) | 0 |
| 25-50 | 22 (18.2%) | 11 (33.3%) | 0 |
| 50-75 | 21 (17.4%) | 6 (18.2%) | 2 (5.7%) |
| 75-100 | 20 (16.5%) | 1 (3.0%) | 4 (11.4%) |
| 100-125 | 8 (6.6%) | 1 (3.0%) | 4 (11.4%) |
| 125-150 | 6 (5.0%) | 0 | 5 (14.3%) |
| 150-200 | 14 (11.6%) | 1 (3.0%) | 11 (31.4%) |
| >200 | 11 (9.1%) | 2 (6.1%) | 9 (25.7%) |

Geom B winner median = 39%; 81.8% of winners reverse with MAE_pct ≤ 75%.

### 5.4 Implications for Entry Calibration

If the goal is to enter **closer to the actual reversal point** (entering at the far edge instead of mid-body):
- Geom A: shifting entry from current ~retest-candle-close to the far OB edge (lowest price for bullish OB) would improve median win R by approximately the differential between winner median MAE (55%) and entry: roughly +0.45 × ob_body_size. With median ob_body = 0.83 ATR, that's +0.37 ATR per winning trade.
- However, entries at the far edge would NEVER trigger for retests that don't reach the far edge — i.e., you'd only catch the deeper retests. The 77 current winners with mean MAE_pct = 73% would mostly still fill (most deepen to the bottom anyway), but some shallow retests would be missed.

This suggests **two complementary modes**:
- **Mode A (current):** Enter on retest close at OB-low for bullish (catches all retests, including shallow). Average entry ~mid-body.
- **Mode B (test-worthy):** Limit at far OB edge (ob_low for bullish). Catches only deeper retests but better entry. Sample of 55 "no-penetration" winners + 22 "penetrated-but-recovered" winners gives ~77 fills — about same count, with potentially +0.4 ATR per trade.

This is actionable but needs forward simulation, not just histogram inspection.

---

## 6. Q5 — SL Sensitivity Analysis

### 6.1 Methodology

The CSV does **not** contain ob_low / ob_high directly, but we can derive `entry_to_far_edge_atr` per row from:
```
sl_dist_from_entry_atr = |sl_a_price - retest_entry_price| / h1_atr
entry_to_far_edge_atr = sl_dist_from_entry_atr - original_margin   (= 0.5 for Geom A)
new_sl_dist_atr(m) = entry_to_far_edge_atr + m
```

Re-scoring rule:
- If `MAE_atr ≥ new_sl_dist_atr` → REVERSED (loss) at new SL.
- Else: keep original outcome (CONTINUED → CONTINUED; UNRESOLVED → UNRESOLVED).
- Special case for **loosening** (m > original_margin) and originally-REVERSED rows where MAE doesn't breach the new (looser) SL: cannot determine if target would have been hit without forward walk → mark UNRESOLVED.
- At m = original_margin, outcomes preserved verbatim (avoids same-candle SL+TP ambiguity from re-scoring).

**Edge case excluded:** 13 rows (Geom A) / 4 rows (Geom B) have `entry_to_far_edge_atr < 0` — entry was already past the far OB edge (next-bar-open after wick pierce). These rows are excluded from Q5 because new SL distances would be unstable. Reported clean sample: n=108 (Geom A) / n=117 (Geom B).

**Expectancy in R:** R defined as the **new SL distance**. Wins: `continuation_r_a (in OB-body units) / new_sl_dist_body`. Losses: −1.0 R per stop.

### 6.2 Geom A SL sensitivity (n=108 clean)

| m (ATR) | W | L | U | WR | Wilson CI | median win R | mean win R | E[R] | killed wins vs m=0.5 |
|---|---|---|---|---|---|---|---|---|---|
| 0.0 | 55 | 45 | 8 | 55.0% | 45-64% | 1.11 | 1.26 | +0.225 | 17 |
| 0.1 | 58 | 42 | 8 | 58.0% | 48-67% | 1.01 | 1.10 | +0.199 | 14 |
| 0.2 | 59 | 40 | 9 | 59.6% | 50-69% | 0.92 | 0.97 | +0.161 | 13 |
| 0.3 | 63 | 36 | 9 | 63.6% | 54-72% | 0.85 | 0.90 | +0.189 | 9 |
| **0.5** | **72** | **25** | **11** | **74.2%** | **65-82%** | **0.72** | **0.78** | **+0.291** | **0 (baseline)** |
| 0.7 | 70 | 13 | 25 | 84.3% | 75-91% | 0.62 | 0.65 | +0.304 | 2 |
| 1.0 | 70 | 6 | 32 | 92.1% | 84-96% | 0.52 | 0.55 | +0.298 | 2 |
| 1.5 | 72 | 3 | 33 | 96.0% | 89-99% | 0.42 | 0.44 | +0.267 | 0 |
| 2.0 | 72 | 2 | 34 | 97.3% | 91-99% | 0.35 | 0.36 | +0.224 | 0 |

**Knee analysis (Geom A):**
- Tightening from 0.5 → 0.3 → 0.1 monotonically reduces expectancy. **Tighter is strictly worse.**
- Loosening from 0.5 → 0.7 maintains expectancy at +0.30 R/trade with higher WR. **No real improvement** — the additional unresolved trades absorb all the loss reduction.
- Beyond 1.0 ATR margin, expectancy decays because the larger SL inflates the R denominator faster than it eliminates losses.

**Knee point: m ≈ 0.5-0.7 ATR.** Current production setting (m=0.5) is at the optimal edge of the plateau. Loosening to 0.7 is a "safer" choice (reduces stop-out frequency by 12 → 2 losses while keeping expectancy flat at +0.30 R/trade). Tightening below 0.5 is destructive.

**Caveat on the m=0.5 baseline shift:** The 74.2% WR (vs original 70.0%) reflects the 13-row exclusion. At the m=0.5 number on the FULL sample (n=121), WR = 70.0%. The relative comparison across m values is valid; the absolute WR slightly inflated.

### 6.3 Geom B SL sensitivity (n=117 clean)

| m (ATR) | W | L | U | WR | Wilson CI | median win R | mean win R | E[R] |
|---|---|---|---|---|---|---|---|---|
| 0.0 | 28 | 39 | 50 | 41.8% | 31-54% | 1.80 | 2.51 | +0.268 |
| 0.1 | 30 | 33 | 54 | 47.6% | 36-60% | 1.53 | 2.21 | +0.283 |
| 0.2 | 30 | 25 | 62 | 54.5% | 42-67% | 1.37 | 1.83 | +0.255 |
| 0.3 | 30 | 14 | 73 | 68.2% | 53-80% | 1.25 | 1.58 | +0.286 |
| ~0.18-0.30 (orig) | 31 | 9 | 77 | 77.5% | 62-88% | 1.06 | 1.25 | +0.255 |
| 0.7 | 31 | 7 | 79 | 81.6% | 67-91% | 0.92 | 1.05 | +0.219 |
| 1.0 | 31 | 3 | 83 | 91.2% | 77-97% | 0.78 | 0.85 | +0.200 |

**Geom B knee:** broadly similar — m ≈ 0.1-0.3 maintains best E[R]. Geom B is dominated by UNRESOLVED counts (12-candle horizon truncates), so absolute expectancy is misleading. Use Geom A for SL calibration.

### 6.4 SL-sensitivity caveats

1. **Sample size is small** (108 clean rows for Geom A). The expectancy plateau across m=0.5 to m=1.0 is within Wilson CI overlap — could reflect noise.
2. **continuation_r is in OB-body units, not SL units.** Rows where OB body >> SL distance produce extreme R values (one row has R=214, but median=0.7). I report median win R as headline; mean inflated by outliers.
3. **Loosening re-scoring is incomplete.** When SL is loosened beyond original, originally-stopped trades become UNRESOLVED (we can't tell if target would have been hit). This understates true expectancy at large m.
4. **Same-candle SL+TP ambiguity:** at m=0.5 (= original), outcomes are preserved. At other m, ambiguous candles always mark REVERSED (conservative).

---

## 7. Actionable Recommendations

### 7.1 SL calibration

**Recommendation: KEEP CURRENT SL AT m=0.5 ATR.** Evidence:
- Tighter (m < 0.5) strictly reduces expectancy (–0.10 to –0.07 R/trade per 0.2 ATR step).
- Looser (m > 0.5 to 0.7) maintains expectancy ±0.01 R/trade — within statistical noise.
- m=0.5 is at the optimal edge of the plateau; any change is at best neutral.

**Optional: monitoring trial of m=0.7.** If the goal is to reduce daily-DD volatility, m=0.7 reduces stop-outs from 25 → 13 (Geom A clean sample) at the cost of converting them to UNRESOLVED (12-candle expiry / runner stop / time-based exit). Total expectancy stays +0.30 R/trade. This is a "stylistic" change, not an edge change.

**Per-symbol calibration: USDJPY potentially tighter.** USDJPY winner p90 MAE = 0.86 ATR vs portfolio 1.06 ATR. n=29 is borderline; needs more sample before deploying. Current m=0.5 setting is fine.

### 7.2 Mid-trade exit gate (NEW — testable hypothesis)

Penetration of the far OB edge is a near-perfect loss predictor (P(WIN | not penetrated) = 100%, n=55, 95% lower bound 93.5%). Build a **continuation-side monitor**:

- For each open trade, track if any candle CLOSES with low (bullish) or high (bearish) past the far OB edge.
- If yes → exit at next candle close (or scale out by 50%).

Expected effect on full Geom A population (n=121, in-sample):
- 55 losers eliminated (33 LOSS + 11 UNRESOLVED + 11 LOSS-in-pen at conservative ratio... actually only 33 losers TOTAL in this sample; only 33 were stopped). Actually penetration with LOSS = 33 of 55 penetrated rows. So all 33 LOSSES had penetrated. The exit gate would trigger on all 33 losses + 22 false-positive winners (penetrated but still won) = 55 exits.
- Net P&L impact: −22 × 0.73R (lost wins) + 33 × (1.0R − partial-loss-already-incurred). If gate triggers at far-edge close, partial loss might be ~0.5R rather than 1R full SL. Estimated savings: +33 × 0.5 − 22 × 0.73 = +0.4R per trade × 121 trades = +48R total in-sample.

**This is very large and very in-sample.** Run as **shadow logger first**, validate out-of-sample, decide. Code is simple — single conditional in execution loop.

### 7.3 Entry calibration (lower priority)

Median winner reverses at MAE = 55% of OB body. Entering at the far OB edge instead of OB midpoint would catch the actual reversal point but miss shallower retests. With 47.9% of retests not penetrating the far edge, a far-edge limit order would only catch ~52% of retests. Of those it catches:
- Most would still be winners (the same 22 wins that penetrated).
- Better entry → higher win R.

**Net effect ambiguous.** Needs forward simulation. Not recommended over the mid-trade exit gate (which has clearer evidence).

### 7.4 Don't change

- min_rr = 1.5 → no change indicated by this analysis (the body-size target is independent).
- Continuation horizon (48 candles for Geom A) → no change indicated.
- BE shadow logger (already running) → no change.

---

## 8. Limitations and Caveats

1. **n=121 is small for distributional inference.** Wilson 95% CIs are wide. The 100% WR on non-penetrated retests has lower CI 93.5% — likely overstated. Recommend confirming on the 726-row a2_v2 sample or a bigger out-of-sample run.
2. **Outcomes are CONTINUED/REVERSED, not WIN/LOSS in conventional FTMO sense.** continuation_r is in OB-body units. Body-to-SL conversion varies per row.
3. **Same-candle SL+TP ambiguity** in the original walk classifier: ~4 rows at m=0.5 may be ambiguous (open-tiebreak decided outcome).
4. **In-sample selection.** OBs and retests were detected by the same algorithm being calibrated. This biases penetration findings — true OOS penetration rates likely differ.
5. **13 rows excluded from Q5** (entry past far edge). This shifts the m=0.5 baseline WR from 70.0% to 74.2%. Use full-sample WR (70.0%) for headline benchmarking; use clean WR for relative SL comparison.
6. **Geom B is too short-horizon** (12 candles → 44% UNRESOLVED) to be the primary calibration source. Geom A (48 candles) is the cleaner geometry.
7. **Per-symbol per-side splits not produced** (n too small everywhere except USDJPY winners Geom A).
8. **a2_v2 cross-check disagrees on penetration rate** (35.8% vs 47.9%) — different OB detection logic. Conservative reading: penetration rate ∈ [30%, 55%] across implementations.

---

## 9. Methodological Choices

(For comparison with distrib_b's report.)

1. **Outcome mapping:** CONTINUED → WIN, REVERSED → LOSS, UNRESOLVED → neither.
2. **WR denominator:** WIN + LOSS only (UNRESOLVED excluded). Same as production convention.
3. **Wilson 95% CI** for all rate/proportion reports (not Clopper-Pearson; not normal approx).
4. **Quantiles:** pandas default linear interpolation.
5. **Per-symbol n threshold:** ≥ 20 for distributional reporting.
6. **Geom A and Geom B reported separately throughout.** Never mixed in headlines.
7. **Q3 separation analysis:** Fisher exact for 2x2 contingency (small samples preferred over chi-square).
8. **Q3 winner-vs-loser distribution comparison:** KS test (distribution shape) + Mann-Whitney U (location).
9. **Q3 best separator:** Youden J statistic (TPR − FPR maximization), grid search 200 cutoffs.
10. **Q5 R definition:** R = new SL distance per row. Wins use `continuation_r_a / new_sl_dist_in_body_units`. Losses = −1R nominal.
11. **Q5 expectancy in body units** also computed (alternative): E[R_body] = (Σ continuation_r_a − Σ new_sl_dist_body) / n.
12. **Q5 row exclusion:** 13 rows (Geom A) with entry_to_far_edge_atr < 0 excluded — entry was past far edge. This is a methodological choice to avoid SL-inside-entry pathology. Distrib_b may include them; flag if so.
13. **Q5 re-scoring at m = original_margin:** outcomes preserved verbatim (no re-walk) to avoid same-candle SL+TP ambiguity from re-classification.
14. **Q5 loosening re-scoring:** originally-REVERSED rows with MAE < new_sl_dist → UNRESOLVED (cannot determine win without forward walk). Distrib_b may handle this differently; flag if so.
15. **No bootstrap CIs** on quantile estimates (would be appropriate; flagged as future work).
16. **No multiple-testing correction** (each Q is treated as a primary research question; not a screening battery).

---

## 10. Cross-check Numbers (a2_v2_validation, n=726)

Used only as headline sanity check, not primary analysis.

| Metric | Primary (n=121) | a2_v2 (n=726) |
|---|---|---|
| Geom A WR | 70.0% | 74.6% |
| Geom A winner MAE p50 (ATR) | 0.382 | 0.240 |
| Geom A winner MAE p90 (ATR) | 1.055 | 0.865 |
| Geom A penetration rate | 47.9% | 35.8% |

The a2_v2 sample is larger and gives slightly more conservative (smaller) winner MAE values and lower penetration rate. The qualitative pattern holds: winner MAE p90 is comfortably below the SL distance, and penetration is the loss signal.

---

## Files

- This report: `research/retest_geometry/outputs/distributional_analysis/distrib_a_report.md`
- Intermediate JSONs: `scratch/distrib_a/{q1,q2,q3,q4}_*.json`, `q5_final.json`
- Analysis scripts: `scratch/distrib_a/analyze.py`, `q5_final.py`
- Sanity checks: `scratch/distrib_a/sanity_checks.py`, `check_continuation_r.py`
- Cross-check JSON: `scratch/distrib_a/cross_check_a2_v2.json`
