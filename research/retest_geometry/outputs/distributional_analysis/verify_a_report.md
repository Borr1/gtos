# Tier 1 Distributional Analysis — Verification (n=726) + Wick-vs-Close Re-derivation
**Analyst:** verify_a (independent of verify_b)
**Date:** 2026-04-18
**Primary CSV:** `research/retest_geometry/outputs/a2_v2_validation/combined_retests.csv` (n=726, ADR-003-compliant timing fix verified by A3_v2)
**Secondary CSV:** `research/retest_geometry/outputs/historical/combined_retests.csv` (n=121, distrib_a/b headline source)
**Underlying M15 corpus:** `data/historical/{SYMBOL}_M15.csv` (full 2-year window, used by A1_v2)

---

## Executive Summary

**The headline finding from distrib_a/b survives and STRENGTHENS at n=726:** P(WIN | retest does not penetrate the far OB edge) = **100% (452/452)**, Wilson 95% lower bound **99.16%**. With 6× the sample, the lower bound moves from distrib_a's 93.5% to 99.16%. **Zero non-penetration losers across n=726.** This is the strongest single signal in the dataset.

**The wick-vs-close split, performed by re-walking M15 candles for every n=726 row, decomposes the previously-conflated 40% "P(WIN | penetrated)" number into two structurally different regimes:**

| Regime (Geom A) | n | n_eligible | Wins | Losses | WR | Wilson 95% CI |
|---|---|---|---|---|---|---|
| **not_penetrated** | 466 | 452 | 452 | 0 | **100.0%** | [99.16%, 100%] |
| **wick_only** (defended) | 56 | 56 | 39 | 17 | **69.6%** | [56.7%, 80.1%] |
| **close_penetrated** (broken) | 204 | 199 | 37 | 162 | **18.6%** | [13.8%, 24.6%] |

3-way chi² p = 4.6e-106. Pairwise Fisher exact: not_pen vs wick_only p = 4.6e-18 (OR = ∞), wick_only vs close_pen p = 1.6e-12 (**OR = 10.04** — defended-wick is 10× more likely to be a winner than close-broken).

**The CEO's hypothesis is exactly right.** A wick-based "penetration" definition collapses two opposite signals into one. The actionable cut is **close past far edge**, not wick past far edge.

**Practical implications for production**

1. **Penetration shadow logger and any future exit gate must trigger on close-past-edge, not wick-past-edge.** Defended-wick events should NOT trigger an exit (70% WR going forward); close-past-edge events SHOULD (19% WR going forward).
2. **Of 204 close-penetration events, 125 (61%) occur at least one M15 candle BEFORE the SL is hit** — i.e., the gate fires early enough to act. WR of these "lead-time" close-penetrations is 27.5%, so a same-candle-close-exit gate would prevent ~87 of 162 losses while sacrificing ~33 of 37 winners.
3. **A limit-at-edge entry pattern is now well-defined.** Defended-wick (n=56, 70% WR) and not-penetrated (n=452, 100% WR) are the two targetable populations. Both leave price *near or inside* the OB; close-broken is the regime to avoid.

---

## 1. Schema Verification

### 1.1 a2_v2 CSV (n=726) field inventory vs n=121

The n=726 schema is a **subset** of n=121. Five fields used by distrib_a are missing and were derived row-wise:

| Missing field | Derivation |
|---|---|
| `mae_a_pct_ob_body` | `mae_a_pips / ob_body_size_pips * 100` |
| `mae_b_pct_ob_body` | `mae_b_pips / ob_body_size_pips * 100` |
| `penetration_a_atr` | `penetration_a_pips * pip_size / h1_atr_at_retest` |
| `penetration_b_atr` | `penetration_b_pips * pip_size / h1_atr_at_retest` |
| `ob_body_size_pct_price` | not used in Q1-Q5; skipped |

**`pip_size` lookup matches A2_v2_validation.py line 107** (XAUUSD=0.1, US30_cash=1.0, USDJPY/GBPJPY=0.01, GBPUSD=0.0001).

**Sanity:** the existing column `ob_body_size` (price-units) reconciles to `ob_body_size_pips * pip_size` with max abs diff = 1.42e-14 (float-precision only).

**A critical schema NUANCE:** `ob_body_size` in n=726 ≡ `abs(ob_close - ob_open)` (the OB *candle's* body open-to-close). In n=121 (study.py), `ob_body_size` ≡ `ob_high - ob_low` (the OB candle's *full range*). This means `mae_pct_ob_body` denominators differ between samples — they are **not directly comparable as percentages**. Use ATR units for cross-sample comparison.

### 1.2 Outcome breakdown

| Geometry | CONTINUED | REVERSED | UNRESOLVED | n_eligible | WR |
|---|---|---|---|---|---|
| Geom A | 528 | 179 | 19 | 707 | **74.68%** |
| Geom B | 170 | 283 | 273 | 453 | 37.53% |

Matches distrib_a's a2_v2 cross-check (74.6%) within float rounding.

**Geom B's UNRESOLVED rate (37.6%) is even worse than n=121's 44%.** Geom B's 12-candle horizon truncates ~half of all setups before resolution; the WR is downward-biased. **Headlines are Geom A only.**

### 1.3 Per-symbol n (now n>=30 threshold is meaningful)

| Symbol | n | Geom A eligible | Geom A WR |
|---|---|---|---|
| GBPJPY | 150 | 147 | 79.6% |
| GBPUSD | 150 | 145 | 75.2% |
| XAUUSD | 147 | 142 | 74.6% |
| US30_cash | 143 | 134 | 67.2% |
| USDJPY | 136 | 136 | 76.5% |

All five symbols clear n=30 for both winners-only and losers-only subsets. **Per-symbol breakdowns are reportable for the first time at this scale.**

### 1.4 Underlying M15 raw-data availability

Verified all five symbols' `data/historical/{SYM}_M15.csv` files cover the 2026-01-01 to 2026-04-17 window used by A2_v2. **0 rows in n=726 had M15 raw data missing.**

| Symbol | M15 rows | Date span |
|---|---|---|
| XAUUSD | 48,360 | 2024-04-01 → 2026-04-17 |
| USDJPY | similar | similar |
| GBPUSD | similar | similar (via symlink to ../data) |
| GBPJPY | similar | 2022-03-28 → 2026-04-17 |
| US30_cash | similar | 2022-01-06 → 2026-04-17 |

### 1.5 Edge/data sanity

| Check | Result |
|---|---|
| Negative MAE (Geom A) | 0 |
| Negative penetration_atr | 0 |
| Negative MAE_pct_ob_body | 0 |
| MAE > 5 ATR (Geom A) | 1 (USDJPY 2026-01-14 long, mae=5.59 ATR — extreme but valid) |
| Loser min MAE_pct_ob_body | 0% (n=2; same-candle SL+TP entries on M15 with mae<=0 due to terminal classification edge) |
| Penetration > 0 but eligible WR mismatch | None (all penetration > 0 cases are wick or close, all penetration == 0 cases are not_penetrated) |
| Walk vs CSV outcome consistency | 723/726 = **99.6% match** (3 residuals all REVERSED/UNRESOLVED → CONTINUED, traced to same-candle ambiguity edge cases — see §3.4) |

---

## 2. Task A — Q1-Q5 on n=726

### 2.1 Q1 — Winner MAE distribution

#### Geom A winners (n=528)

**MAE in H1 ATR units:**

| Stat | Value |
|---|---|
| n | 528 |
| mean | 0.302 |
| std | 0.331 |
| p10 | 0.0405 |
| p25 | 0.0905 |
| p50 | **0.240** |
| p75 | 0.443 |
| p90 | **0.865** |
| p95 | 1.040 |
| min | 0.000 |
| max | 2.295 |

**Comparison to distrib_a (n=121):** p50 was 0.382 ATR (now 0.240); p90 was 1.055 ATR (now 0.865). Both metrics SHRINK with the larger sample — winners pull back even less than the smaller sample suggested. **The "SL of 1.34 ATR has plenty of headroom over winner p90 = 0.86 ATR" conclusion strengthens.**

**MAE as % of OB body** (denominator = candle body, not range):

| Stat | Value |
|---|---|
| n | 528 |
| mean | 86.1% |
| p10 | 11.3% |
| p25 | 22.6% |
| p50 | **85.4%** |
| p75 | 117.0% |
| p90 | 219.1% |
| p95 | 305.6% |

**Median = 85% of CANDLE BODY** (vs distrib_a's 55% of OB-RANGE). The two are not comparable as percentages — the candle body is a smaller denominator, inflating the percent. The substantive conclusion ("winners reverse near or inside the OB body") persists in interpretation.

#### Per-symbol Geom A winners (n>=30 threshold met for all five)

| Symbol | n | mae_atr p50 | mae_atr p90 | mae_atr p95 |
|---|---|---|---|---|
| GBPJPY | 117 | 0.244 | 0.851 | 1.075 |
| GBPUSD | 109 | 0.231 | 0.776 | 0.911 |
| US30_cash | 90 | 0.301 | 1.001 | 1.235 |
| USDJPY | 104 | 0.225 | 0.679 | 0.826 |
| XAUUSD | 108 | 0.230 | 0.929 | 1.150 |

**USDJPY has the tightest winner MAE distribution** (p90 = 0.68 ATR vs portfolio 0.86 ATR), confirming distrib_a's per-symbol indication. **US30_cash is widest** (p90 = 1.00 ATR). All five symbols' p90 are well within the production SL distance of ~1.3 ATR from entry.

#### Geom B winners (n=170)

| Stat | mae_atr | mae_pct_ob_body |
|---|---|---|
| n | 170 | 170 |
| p50 | **0.171** | 50.6% |
| p90 | **0.583** | 173.5% |
| p95 | 0.730 | 254.9% |

Tighter than Geom A, as expected (12-candle horizon truncates faster trades).

### 2.2 Q2 — Loser MAE distribution + separation

#### Geom A losers (n=179)

**MAE in H1 ATR:**

| Stat | Value |
|---|---|
| n | 179 |
| mean | 1.396 |
| p10 | 0.654 |
| p25 | **0.906** |
| p50 | 1.388 |
| p75 | 1.737 |
| p90 | 2.319 |
| p95 | 2.554 |
| min | 0.000 |
| max | 5.591 |

**Comparison to distrib_a (n=121):** p25 was 1.106 (now 0.906) — losers stop SOONER on average in the larger sample. Winner p90 = 0.86 ATR vs loser p25 = 0.91 ATR — **the overlap zone barely exists**. The two distributions are nearly disjoint at p90/p25 boundary.

**MAE as % of OB body** (candle body):

| Stat | Value |
|---|---|
| p50 | 451% |
| p25 | 244% |
| p90 | 1059% |
| min | 0% |

**Min MAE_pct_ob_body = 0%** in n=726 (vs distrib_a's 101.4% in n=121). Two losers have MAE = 0 — these are same-candle SL+TP cases on candle j=1 where the open-tiebreak resolved as REVERSED before any adverse excursion was recorded. They are real losses but artifactual zero-MAEs. **Dropping these two does not change WR or any rate.**

**Losers inside the OB candle body (mae_pct < 100%):** 7 of 179 = **3.9%** (vs n=121's 0/33 = 0%). All 7 have penetration_a_pips > 0 — i.e., even "shallow" losers had at least a wick past the far edge.

#### Geom A separation analysis

| Metric | Value |
|---|---|
| KS statistic | 0.792 |
| KS p-value | 5.6e-72 |
| Mann-Whitney p-value | < 1e-100 |
| Winner p90 MAE ATR | 0.865 |
| Loser p25 MAE ATR | 0.906 |
| **Best Youden separator** | **0.534 ATR** |
| Sensitivity at cutoff | 87.7% |
| 1 − Specificity at cutoff | 15.9% |
| Youden J | 0.719 |

**Best separator shifted from distrib_a's 0.916 ATR to 0.534 ATR.** This is because the larger sample's winner MAE p50 is 0.24 ATR (much tighter than n=121's 0.38 ATR) — the optimal cut moves left. Youden J is essentially identical (0.72 → 0.72), so separation quality is preserved.

### 2.3 Q3 — Penetration past far OB edge (Geom A, full sample)

| Metric | k | n | p | Wilson 95% CI |
|---|---|---|---|---|
| Penetration rate | 260 | 726 | **35.81%** | [32.4%, 39.4%] |
| P(WIN \| penetrated) | 76 | 255 | **29.80%** | [24.5%, 35.7%] |
| P(WIN \| not penetrated) | 452 | 452 | **100.0%** | [99.16%, 100%] |

**Fisher exact penetrated vs not-penetrated:** p = **8.6e-107** (vs distrib_a's 2.07e-13). The signal is now *overwhelmingly* significant.

**Penetration depth (when penetrated, n=260, ATR):**

| Stat | Value |
|---|---|
| mean | 0.687 |
| p10 | 0.097 |
| p25 | 0.272 |
| p50 | 0.617 |
| p75 | 0.831 |
| p90 | 1.072 |
| p95 | 1.520 |
| max | 5.530 |

**Distrib_a comparison:** distrib_a's pen_depth p50 = 0.644 ATR vs verify_a's 0.617 ATR. Numerically near-identical. ✓

#### Per-symbol Q3 (Geom A, all five reportable n>=30)

| Symbol | n | WR | Pen rate | P(WIN \| pen) | P(WIN \| not pen) |
|---|---|---|---|---|---|
| GBPJPY | 150 | 79.6% [72.4-85.3%] | 31.3% [24.5-39.0%] | 36.2% [25.0-49.1%] | **100% [96.4-100%]** |
| GBPUSD | 150 | 75.2% [67.6-81.4%] | 41.3% [33.7-49.4%] | 35.5% [25.6-46.9%] | **100% [95.6-100%]** |
| US30_cash | 143 | 67.2% [58.9-74.5%] | 35.0% [27.7-43.1%] | 24.0% [14.9-36.3%] | **100% [95.8-100%]** |
| USDJPY | 136 | 76.5% [68.7-82.8%] | 32.4% [25.0-40.7%] | 27.3% [17.7-39.6%] | **100% [96.0-100%]** |
| XAUUSD | 147 | 74.6% [67.0-81.0%] | 38.1% [30.6-46.2%] | 23.2% [14.8-34.6%] | **100% [95.9-100%]** |

**100% WR on non-penetrated holds for ALL FIVE SYMBOLS independently** with Wilson lower bounds 95.6-96.4%. This is no longer a small-n artifact.

### 2.4 Q3 Geom B (n=726)

| Metric | k | n | p | Wilson 95% CI |
|---|---|---|---|---|
| Penetration rate | 308 | 726 | 42.4% | [38.9%, 46.0%] |
| P(WIN \| penetrated) | 32 | 273 | 11.7% | [8.4%, 16.2%] |
| P(WIN \| not penetrated) | 138 | 180 | 76.7% | [69.9%, 82.3%] |

Fisher p = 1.85e-44. Geom B's "P(WIN | not penetrated) = 76.7%" is **lower** than Geom A's 100% — because Geom B's tight SL clips trades that the OB body would have absorbed. Geom A is the cleaner geometry.

### 2.5 Q4 — Histogram of MAE_pct_ob_body (Geom A)

(Note: denominator = candle body, **NOT** range — different from distrib_a.)

| Bin | All (n=726) | WIN (n=528) | LOSS (n=179) |
|---|---|---|---|
| 0-25 | 14.6% | 19.5% | 1.7% |
| 25-50 | 11.3% | 15.5% | 0.6% |
| 50-75 | 11.0% | 14.6% | 0.6% |
| 75-100 | 10.6% | 13.6% | 1.1% |
| 100-125 | 8.4% | 9.5% | 5.0% |
| 125-150 | 6.5% | 6.4% | 6.7% |
| 150-200 | 11.4% | 8.5% | 19.0% |
| >200 | 26.2% | 12.5% | 65.4% |

**Winners reverse with MAE_pct_ob_body ≤ 100% in 53.8% of cases** (vs n=121's 81%; gap due to denominator change, not behaviour change).
**Losers reverse with MAE_pct_ob_body ≤ 100% in 3.9% of cases** (vs 0%; only marginal change, signal preserved).
**The body-based threshold remains a strong discriminator: winners cluster low, losers cluster high.**

### 2.6 Q5 — SL sensitivity (Geom A)

#### Methodology

Same as distrib_a:
- `entry_to_far_edge_atr = sl_a_dist_atr - 0.5` (because original m=0.5)
- Excluded **41 rows** (5.6% of n=726) with `entry_to_far_edge_atr < 0`. Distrib_a excluded 13 rows (10.7% of n=121). Smaller proportion of edge-cases at larger n is consistent with detection logic stability.
- Re-scoring: tighter m → REVERSED if `mae >= new_sl`; looser m → originally-REVERSED becomes UNRESOLVED if mae < new_sl.
- m = 0.5 preserves outcomes verbatim.

#### Geom A SL sensitivity (n=685 clean)

| m (ATR) | W | L | U | WR | Wilson CI |
|---|---|---|---|---|---|
| 0.0 | 443 | 228 | 14 | 66.0% | [62.4-69.5%] |
| 0.1 | 465 | 205 | 15 | 69.4% | [65.8-72.8%] |
| 0.2 | 480 | 189 | 16 | 71.7% | [68.2-75.0%] |
| 0.3 | 493 | 176 | 16 | 73.7% | [70.2-76.9%] |
| **0.5** | **514** | **152** | **19** | **77.2%** | **[73.8-80.2%]** |
| 0.7 | 514 | 71 | 100 | 87.9% | [85.0-90.3%] |
| 1.0 | 514 | 26 | 145 | 95.2% | [93.0-96.7%] |
| 1.5 | 514 | 8 | 163 | 98.5% | [97.0-99.2%] |
| 2.0 | 514 | 5 | 166 | 99.0% | [97.8-99.6%] |

**WR rises monotonically across all 9 values of m.** The "knee" is no longer flat between 0.5 and 0.7 — at n=726, going from m=0.5 to m=0.7 adds 11pp of WR (77% → 88%), with 81 fewer losses (152→71) at the cost of 81 more UNRESOLVED.

**Important caveat on E[R]:** I include expectancy_r values in `scratch/verify_a/q1_q5_n726.json`, but they are NOT directly comparable to distrib_a's because the n=726 CSV stores `continuation_r_a` as `abs(target - entry) / sl_dist` per A2_v2 line 697, where target = ob_high + ob_body and sl_dist depends on entry depth. Median win continuation_r in n=726 = 0.234 R; in n=121 = 1.178 R. The two CSVs use different scaling. **Distrib_a's E[R] curve cannot be reproduced from n=726 without re-running A2_v2 with body-based R denominator.** I report the Q5 WR table as the substantive output; the E[R] derivation is left as future work for a follow-up reviewer.

#### What does survive cross-sample on Q5?

- **Tighter SL is strictly worse.** Both n=121 and n=726 show monotonic WR decrease as m → 0.0.
- **Loosening from 0.5 → 0.7 → 1.0 → 1.5 → 2.0 increases WR.** N=121 had it as a flat plateau; n=726 shows it as a clean monotonic increase — but the additional UNRESOLVED count grows roughly equally, so the EXPECTED VALUE depends on how UNRESOLVEDs are scored (most reasonable: 0R, since the system would scratch).
- **Production m=0.5 sits in the middle of the WR curve.** Whether to loosen to 0.7 depends on tolerance for stop-out frequency (152 → 71) vs UNRESOLVED frequency (19 → 100).

#### Recommendation

Re-run Q5 with a re-scored R-multiple convention (R relative to per-row new SL distance) before making any SL change. The current "expectancy" curve is unit-mismatched. **WR-only conclusion: production m=0.5 is fine; m=0.7 is a reasonable WR-improving option but adds many UNRESOLVEDs.**

---

## 3. Task B — Wick-vs-close penetration analysis (Geom A only)

### 3.1 Re-derivation methodology

For each n=726 row, I re-walked the M15 candles from entry to outcome termination, mirroring `A2_v2_validation.py classify()` exactly:

**Far-edge geometry (per A2_v2 lines 572-585 and 631-668):**
- **Long (bullish OB):** far edge = `ob_low`. Wick penetration when `M15.low < ob_low`. **Close penetration when `M15.close < ob_low`.**
- **Short (bearish OB):** far edge = `ob_high`. Wick penetration when `M15.high > ob_high`. **Close penetration when `M15.close > ob_high`.**

`ob_low` and `ob_high` are not stored in the CSV but are exactly recoverable:
- For long: `ob_low = sl_a_price + 0.5 * h1_atr_at_retest` (because `sl_a = ob_low - 0.5*ATR`)
- For long: `ob_high = target_a_price - ob_body_size` (because `target_a = ob_high + ob_body`)
- Mirror for short.

**Walk parameters (per A2_v2):**
- Window: 48 M15 candles past entry
- Start index: `entry_idx + 1`, where `entry_idx` follows A2_v2's rule:
  - If `retest_candle.close ∈ [ob_low, ob_high]` → entry on close, `entry_idx = retest_idx`
  - Else → entry on next bar open, `entry_idx = retest_idx + 1`
- Termination: same `low<=sl OR high>=tp` (long; mirror short), with same-bar SL+TP open-tiebreak.

**Per-row classification:**
- `not_penetrated`: `penetration_a_pips == 0` (verified ground truth: 100% match with my walk's "no wick past edge")
- `wick_only`: `penetration > 0` AND no candle CLOSED past the far edge during the walk
- `close_penetrated`: at least one walked candle CLOSED past the far edge

**Validation against A2_v2 ground truth (outcome consistency):** 723/726 = 99.6% of rows my walk reaches the same `outcome_a` as the CSV. The 3 residuals (US30_cash 2026-01-09 short, GBPUSD 2026-03-02 long, GBPUSD 2026-03-23 long) are same-candle SL+TP edge cases at H1 ATR boundaries; the wick-vs-close classification for these residuals is independent of which terminal outcome the CSV records, so they remain correctly classified.

### 3.2 Three-regime breakdown (full sample)

| Regime | n | n_eligible | Wins | Losses | UNRESOLVED | WR | Wilson 95% CI |
|---|---|---|---|---|---|---|---|
| **not_penetrated** | 466 | 452 | 452 | 0 | 14 | **100.0%** | [99.16%, 100%] |
| **wick_only** | 56 | 56 | 39 | 17 | 0 | **69.6%** | [56.7%, 80.1%] |
| **close_penetrated** | 204 | 199 | 37 | 162 | 5 | **18.6%** | [13.8%, 24.6%] |
| Total | 726 | 707 | 528 | 179 | 19 | 74.7% | [71.4-77.7%] |

### 3.3 Statistical separation

**3-way chi² on contingency [[452,0], [39,17], [37,162]]:** χ² = 485.1, dof = 2, p = **4.6e-106**

**Pairwise Fisher exact:**

| Comparison | Table (W,L) vs (W,L) | p-value | OR |
|---|---|---|---|
| not_penetrated vs wick_only | (452,0) vs (39,17) | **4.6e-18** | ∞ |
| not_penetrated vs close_pen | (452,0) vs (37,162) | **1.5e-117** | ∞ |
| **wick_only vs close_pen** | (39,17) vs (37,162) | **1.6e-12** | **10.04** |

**The pairwise wick-only vs close-penetrated test is the headline of Task B.** Defended-wick events are **10× more likely to be winners** than close-broken events. The "P(WIN | penetrated) = 30%" number from §2.3 is an *average* across two structurally different populations whose true WRs are 70% and 19%.

### 3.4 Why the original "penetrated" lump misled

In n=726, of 260 rows with `penetration_a_pips > 0`:
- 56 (21.5%) are wick-only — defended candles
- 204 (78.5%) are close-penetrated — actually broken

The 30% lump WR = (39 + 37) / (56 + 199) = 76 / 255 ≈ 29.8% is a weighted average where the wick-only minority pulls the number UP and the close-broken majority pulls it down. Since the close-broken are 4× more frequent, the lump number reflects them more — but it still understates how bad close-broken really is (19%) and overstates how bad defended-wick really is (70%).

### 3.5 Per-subset distributions

#### Not-penetrated (n=466)

| Stat | mae_atr | penetration_atr |
|---|---|---|
| p50 | 0.182 | 0 (by definition) |
| p90 | 0.766 | 0 |
| p95 | 1.110 | 0 |
| max | 2.295 | 0 |

#### Wick-only (n=56)

| Stat | mae_atr | penetration_atr |
|---|---|---|
| p50 | 0.641 | 0.165 |
| p75 | 0.891 | 0.563 |
| p90 | 1.636 | 0.741 |
| p95 | 2.123 | 0.830 |
| max | 5.591 | 2.651 |

#### Close-penetrated (n=204)

| Stat | mae_atr | penetration_atr |
|---|---|---|
| p50 | 1.260 | 0.642 |
| p75 | 1.708 | 0.835 |
| p90 | 2.218 | 1.256 |
| p95 | 2.549 | 1.622 |
| max | 5.530 | 5.530 |

**Observation:** Wick-only's penetration depth p50 = 0.17 ATR is *much shallower* than close-penetrated's p50 = 0.64 ATR. Defended candles tend to wick only ~17% of an ATR past the far edge before snapping back. Broken-close candles wick ~4× deeper on average.

### 3.6 Per-symbol consistency check

| Symbol | not_pen WR (n) | wick_only WR (n) | close_pen WR (n) |
|---|---|---|---|
| GBPJPY | 100% (99/99) | 75.0% (9/12) | 22.2% (8/36) |
| GBPUSD | 100% (83/83) | 64.7% (11/17) | 24.4% (11/45) |
| US30_cash | 100% (88/88) | 55.6% (5/9) | 18.4% (7/38) |
| USDJPY | 100% (92/92) | 77.8% (7/9) | 14.3% (5/35) |
| XAUUSD | 100% (90/90) | 77.8% (7/9) | 13.3% (6/45) |

**The pattern holds across all 5 symbols.** not_pen = 100% universally; wick_only = 56-78% (n=9-17, somewhat noisy per-symbol but consistently above 50%); close_pen = 13-24% universally below 25%.

### 3.7 Timing of close-penetration signal

For an exit gate to be actionable, the close-past-edge signal must arrive **before** the SL is hit. I tracked `first_close_pen_j` (the candle index of the first close past edge) and compared to `candles_walked` (the candle on which the trade terminated).

| Cohort | n | First close-pen candle (j=1, ..., j=k stats) |
|---|---|---|
| All close_pen | 204 | mean=5.8, p25=1, p50=3, p75=7, max=48 |
| Close_pen winners | 37 | mean=4.1, p25=1, p50=2, p75=5, max=20 |
| Close_pen losers | 162 | mean=5.7, p25=1, p50=3, p75=7, max=48 |

| Threshold | n with first_close_pen_j ≤ K | P(LOSS) of those |
|---|---|---|
| j ≤ 1 | 58 | 78.9% |
| j ≤ 2 | 94 | 76.3% |
| j ≤ 3 | 115 | 77.9% |
| j ≤ 5 | 140 | 79.7% |
| j ≤ 10 | 165 | 79.8% |

**Acting at any j threshold yields ~78% loss rate.** A close-past-edge gate triggered at the very first candle (j=1) would correctly identify ~80% of trades as losers.

#### Lead time before SL

Of 204 close-penetrations: **125 (61%)** occur on a candle BEFORE the SL is hit (i.e., SL is hit later or never; the close-pen signal has lead time). For these 125:
- WR = 27.5% (33 winners / 87 losses among 120 eligible)
- An exit-on-close gate would prevent ~87 losses while sacrificing ~33 winners

**This is the practical "lead-time" cohort for a real-time exit gate.** The remaining 75 close-pens occur ON the SL candle itself — gate provides no lead time benefit there (SL would fire anyway).

---

## 4. Task C — Synthesis

### 4.1 Tier 1 picture at n=726

| Finding | n=121 (distrib_a) | n=726 (verify_a) | Verdict |
|---|---|---|---|
| P(WIN \| not penetrated) | 100% (Wilson lower 93.5%) | **100%** (Wilson lower **99.16%**) | **STRENGTHENED** |
| Sample n on the 100% claim | 55 | **452** | 8× confidence multiplier |
| Per-symbol generalization | 3 of 5 symbols passed n>=20 threshold | **5 of 5** symbols pass n>=30, all 100% | **STRENGTHENED** |
| Penetration rate (Geom A) | 47.9% | 35.8% | A2_v2's stricter detection halves misclassification |
| P(WIN \| penetrated) | 40% | **30%** | **DETERIORATED** — but see wick-vs-close split |
| Winner MAE p90 (ATR) | 1.06 | 0.86 | Tighter (signal sharper) |
| Loser MAE p25 (ATR) | 1.11 | 0.91 | Tighter (signal sharper) |
| Best Youden separator (ATR) | 0.92 | 0.53 | Cut moves left with tighter winner dist |
| Youden J | 0.72 | 0.72 | Identical separation quality |
| Geom A WR (eligible) | 70.0% | 74.7% | Higher (consistent with sharper signal) |
| Q5 m=0.5 → 0.7 expectancy | "flat plateau" | "monotonic WR increase" | Re-derive with consistent R unit before acting |

### 4.2 Wick-vs-close: the actionable split

The CEO's intuition is empirically vindicated:

| Event | True WR (n=726) | Lump WR (old framing) |
|---|---|---|
| **Defended wick** (close back inside OB) | **69.6%** [56.7%, 80.1%] | These two were averaged into the |
| **Close past far edge** (true break) | **18.6%** [13.8%, 24.6%] | misleading "40% P(WIN \| pen)" number |

**Defended-wick events should NOT trigger exit/cancel logic.** They behave like ordinary penetration tests that the OB defended — close to coin flip, slightly worse than coin flip.

**Close-past-edge events are the true failure signal.** 81% loss rate when they happen. This is the structural break the OB framework is supposed to flag.

### 4.3 Implications for the penetration shadow logger spec

**Recommendation: shadow logger must use close-past-edge as the trigger, not wick-past-edge.**

1. **Per-trade tracking:** for each open position, compute far_edge from sl_a + 0.5*ATR (long) or sl_a - 0.5*ATR (short). On every M15 candle close, check `close < far_edge` (long) or `close > far_edge` (short).
2. **Log:** trade_id, candle_ts, far_edge, close, distance_past_edge_atr, time_since_entry. Don't act on the signal yet — accumulate ~30 events to validate live before promoting to gate.
3. **Compare live to backtest:** the live close-past-edge population should produce ~19% WR forward. If it produces meaningfully higher (e.g., >40%), the in-sample bias warning from distrib_a's caveat applies — DO NOT promote.
4. **DO NOT** alarm on wick-only events. They are 70% winners — alarming would flag them as bad signal when they're actually OK trades.

### 4.4 Implications for an intra-candle limit-at-edge entry pattern

A "limit at far edge" entry pattern targets price re-touching the OB low (long) or OB high (short). With this verification:

- **Defended-wick + not-penetrated together = the actionable target population.** 452 + 56 = 508 of 726 retests (70%) — these are the "good" outcomes.
- **The 39 wins among defended-wick** are entries that DID dip past the far edge briefly but reclaimed — a limit-at-edge order would have filled at a BETTER price than the original retest entry.
- **Of 56 wick-only events, 39 wins → 70% WR.** A limit-at-edge entry pattern would inherit this WR for the "wick" cohort.
- **Combined population:** 508 fills, 491 wins / 17 losses → **P(WIN \| limit-at-edge fills, given trade fills WITHOUT closing past edge) = 96.6%**. Assumes the order is canceled if a CLOSE past edge occurs before fill.

But: the not_penetrated cohort (n=452) has retests that DID NOT reach the far edge. A limit at the far edge would NOT have filled for these. Retest rate at far edge = 56 / 726 = 7.7% — most retests don't reach the far edge with a wick. So a limit-at-edge order misses 92% of trade opportunities.

**Net conclusion:** limit-at-edge as a *replacement* for current entry would dramatically reduce trade frequency. It might be useful as a *supplement*: if no in-OB fill occurs but the candle's wick reaches the far edge and closes back inside the OB, fill at the far edge. This is the "deep tag and reclaim" pattern. Quantitative work is needed; this report only validates that the underlying population's WR is high.

### 4.5 Action items (prioritized)

1. **PRIORITY 1 — Penetration shadow logger spec:** must trigger on M15 close past far edge, NOT wick past far edge. Numbers: ~78% loss rate when triggered (in sample), ~61% have lead time before SL hit (actionable cases). See §3.7. (Owner: tooling.)
2. **PRIORITY 2 — Validate live:** wait for ~30 close-past-edge events in live trading. If forward WR is consistent with the in-sample 19%, promote shadow → gate. If forward WR is >40%, hold the gate; treat in-sample 100%/19% as overstated. (Owner: monitoring.)
3. **PRIORITY 3 — Q5 R-unit re-derivation:** re-run Q5 with `continuation_r_a` re-scaled to per-row new-SL R. Current Q5 expectancies in this report are NOT comparable to distrib_a's (different cont_r conventions per CSV). The WR-only conclusion (production m=0.5 fine; m=0.7 is OK) does not depend on this fix. (Owner: research.)
4. **PRIORITY 4 — Limit-at-edge entry pattern simulation:** test "fill on wick to far edge, cancel on close past far edge" as a supplemental entry — quantify trade frequency vs current. (Owner: research.)

---

## 5. Limitations and Methodological Choices

### Methodological choices

1. **Outcome mapping:** CONTINUED → WIN, REVERSED → LOSS, UNRESOLVED → neither. Same as distrib_a/b production convention.
2. **WR denominator:** WIN + LOSS only.
3. **Wilson 95% CI** for all rate/proportion reports.
4. **Quantiles:** pandas default linear interpolation.
5. **Per-symbol n threshold:** ≥ 30 for distributional reporting at n=726 (raised from distrib_a's n=20 because we have 6× the sample).
6. **Geom A and Geom B reported separately** throughout. Headlines are Geom A.
7. **Q3 separation analysis:** Fisher exact for 2x2; chi² for 3x2.
8. **Q3 winner-vs-loser:** KS test (shape) + Mann-Whitney U (location).
9. **Best separator:** Youden J grid search, 200 cutoffs.
10. **Q5 row exclusion:** rows with `entry_to_far_edge_atr < 0` (entry was already past far edge after wick). Excluded 41 of 726 (5.6%) — same exclusion logic as distrib_a; smaller proportion at larger n.
11. **Q5 same-margin preservation:** at m = 0.5 (= original), outcomes preserved verbatim to avoid same-candle SL+TP ambiguity from re-classification.
12. **Q5 loosening re-scoring:** originally-REVERSED rows with mae < new_sl → UNRESOLVED.
13. **Wick-vs-close walk:** mirrors A2_v2_validation.classify() exactly. Validated by 99.6% outcome match against CSV ground truth. The 3 residual mismatches (3/726 = 0.4%) are at same-candle SL+TP edge cases and don't affect classification.
14. **Far-edge derivation in re-walk:** `ob_low = sl_a + 0.5*ATR` (long); `ob_high = sl_a - 0.5*ATR` (short). Verified algebraically against A2_v2 lines 573 and 584.
15. **Entry-index logic in re-walk:** uses A2_v2's actual rule (`retest_close in [ob_low, ob_high]` → entry on close, else next bar open). I initially used a price-match heuristic and got 24/726 walk-vs-CSV mismatches; switching to the position-based rule reduced this to 3/726.
16. **Penetration depth in ATR:** derived as `penetration_pips * pip_size / h1_atr_at_retest`. Verified by recomputing distrib_a's penetration p50 = 0.644 ATR (mine: 0.617 ATR — close, sample difference).

### Limitations

1. **Q5 expectancy values are unit-mismatched** between n=121 (R in OB-body units) and n=726 (R in original-SL units). I report WR-only conclusions for Q5; expectancy values in `q1_q5_n726.json` are NOT directly comparable to distrib_a's. To get apples-to-apples expectancy, re-walk the CSV with body-based R.
2. **OB body denominator difference:** n=121 uses `ob_high - ob_low` (range), n=726 uses `ob_close - ob_open` (candle body). MAE_pct_ob_body percentages are not cross-comparable. ATR-based metrics ARE comparable.
3. **Close-pen signal "lead time before SL"** of 61% is in-sample; the actual live action effectiveness depends on M15 candle close timing — a real-time gate must wait for candle close which adds 1-15 minutes of latency. In fast-moving markets, the SL may fire intra-candle in the very M15 bar that closes past edge.
4. **In-sample selection bias** still applies — A2_v2's OB detector and walk classifier are the SAME logic that produced the rows being analyzed. The 100% WR on non-penetrated has Wilson lower 99.16%, but if the OB detector is biased to surface only resolution-friendly OBs, this number is overstated. Recommend: validate forward against live retests on 4-week rolling window.
5. **No bootstrap CIs** on quantile estimates (would be appropriate; deferred).
6. **No multiple-testing correction** — each Q is treated as a primary research question; not a screening battery.
7. **3 walk-vs-CSV outcome residuals (0.4%)** from same-candle SL+TP edge cases. Wick-vs-close classification for these is intrinsically robust (penetration_a_pips ground truth is from CSV, walk only adds the close-past-edge check), but the overall outcome attribution for those 3 rows comes from the CSV not the walk. They are reported in their CSV-claimed outcomes.
8. **Wick-vs-close on n=121 NOT performed.** The n=726 sample is 6× larger; redoing on n=121 would have been redundant. The pattern is so strong in n=726 (chi² p = 4.6e-106) that the smaller sample is unlikely to overturn it.

---

## 6. Files

- This report: `research/retest_geometry/outputs/distributional_analysis/verify_a_report.md`
- Schema check: `scratch/verify_a/schema_check.py` → `scratch/verify_a/schema_summary.json`, `scratch/verify_a/n726_with_derived.csv`
- Q1-Q5 analysis: `scratch/verify_a/analyze_n726.py` → `scratch/verify_a/q1_q5_n726.json`
- Wick-vs-close re-walk: `scratch/verify_a/wick_vs_close.py` → `scratch/verify_a/n726_with_wick_close.csv`, `scratch/verify_a/wick_vs_close_summary.json`
- Edge case sanity: `scratch/verify_a/edge_cases.py` → `scratch/verify_a/edge_case_summary.json`
- Walk mismatch debug: `scratch/verify_a/walk_mismatch.py`, `scratch/verify_a/replicate_classify.py`, `scratch/verify_a/debug_mismatch.py`
- Timing analysis: `scratch/verify_a/timing_analysis.py` → `scratch/verify_a/timing_analysis.json`
- Side-by-side comparison: `scratch/verify_a/compare_n121.py` → `scratch/verify_a/compare_n121_n726.json`
- Sanity checks: `scratch/verify_a/sanity_n726.py`
