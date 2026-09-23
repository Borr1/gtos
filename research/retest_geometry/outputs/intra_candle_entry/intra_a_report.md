# Tier 2 Intra-Candle Limit-at-Edge Entry Study — `intra_a` report

**Agent:** `intra_a` (independent code path)
**Date:** 2026-04-18
**Input CSV:** `research/retest_geometry/outputs/a2_v2_validation/combined_retests.csv` (n=726)
**Sim window:** 48 M15 candles (Geom A)
**Spec:** `research/retest_geometry/tier2_intra_candle_entry_spec.md`
**Parent ADR:** ADR 003

---

## 1. Schema verification & raw OHLC availability

- **Total rows processed:** 726 (all 726 rows from A2_v2_validation; 0 errors)
- **Per-symbol counts:** GBPJPY=150, GBPUSD=150, US30_cash=143, USDJPY=136, XAUUSD=147
- **Per-side counts:** long=384, short=342
- **Per-session counts:** London=197, NY=186, Tokyo=182, Off-Session=161
- **Rows with derivable midpoint anchor (read from H1 raw):** 726/726

**Raw M15 availability:** All 726 retests had matching M15 candles in `data/historical/{SYMBOL}_M15.csv`. No silent gaps encountered for the retest window 2026-01-02 .. 2026-04-17. The XAUUSD 126-day silent gap mentioned in the session 24 handoff falls outside this study's retest range.

**OB zone derivation:** OB high/low were derived from CSV fields (`sl_a_price`, `target_a_price`, `ob_body_size`, `h1_atr_at_retest`):
- long: `ob_low = sl_a_price + 0.5 * h1_atr_at_retest`; `ob_high = target_a_price - ob_body_size`
- short: `ob_high = sl_a_price - 0.5 * h1_atr_at_retest`; `ob_low = target_a_price + ob_body_size`
- Verified against the OB structure formula `target_a = ob_high + ob_body` (long) and `target_a = ob_low - ob_body` (short).

**Anchors:**
- Far-edge anchor: `ob_low` (long) / `ob_high` (short)
- Midpoint anchor: `(ob_open + ob_close) / 2` of the H1 OB candle, read from raw H1 by `ob_formation_ts`

---

## 2. Fill rate by method (overall + per-symbol + per-session)

### 2.1 Overall

| Anchor | Method | Filled | Total | Rate | Wilson 95% CI |
|---|---|---|---|---|---|
| far_edge | market | 726 | 726 | 100.0% | [99.5%, 100.0%] |
| far_edge | limit | 520 | 726 | 71.6% | [68.2%, 74.8%] |
| far_edge | hybrid | 726 | 726 | 100.0% | [99.5%, 100.0%] |
| midpoint | market | 726 | 726 | 100.0% | [99.5%, 100.0%] |
| midpoint | limit | 637 | 726 | 87.7% | [85.2%, 89.9%] |
| midpoint | hybrid | 726 | 726 | 100.0% | [99.5%, 100.0%] |

**Headline numbers:**
- Far-edge limit fills on **71.6%** of CANDIDATEs (520/726; Wilson 95% [68.2%, 74.8%])
- Midpoint limit fills on **87.7%** of CANDIDATEs (637/726; Wilson 95% [85.2%, 89.9%])
- Market entry fills 100% by definition; hybrid is 100% (hybrid falls back to full market when limit doesn't fill)

### 2.2 Fill horizon (which candle did the limit fill?)

| Anchor | On retest candle (off=0) | Within 2 candles (off≤1) | Within 3 (off≤2) | Within 5 (off≤4) | Within 48 (entire window) |
|---|---|---|---|---|---|
| far_edge | 89 | 151 | 189 | 247 | 520 |
| midpoint | 238 | 349 | 391 | 452 | 637 |

### 2.3 Same-price and gap-fill counts

- Far-edge limit fills exactly at market price (entry == close): **0** rows (treated as differential = 0R per CEO decision)
- Midpoint limit fills exactly at market price: **1** rows
- Far-edge limit fills via gap-open (open already past anchor): **20** rows
- Midpoint limit fills via gap-open: **49** rows

### 2.4 Per-symbol fill rates (limit only — market is 100% by construction)

| Symbol | n | Far-edge limit fill rate | Midpoint limit fill rate |
|---|---|---|---|
| GBPJPY | 150 | 73.3% [65.7%, 79.8%] | 89.3% [83.4%, 93.3%] |
| GBPUSD | 150 | 71.3% [63.6%, 78.0%] | 87.3% [81.1%, 91.7%] |
| US30_cash | 143 | 75.5% [67.9%, 81.8%] | 89.5% [83.4%, 93.5%] |
| USDJPY | 136 | 68.4% [60.2%, 75.6%] | 87.5% [80.9%, 92.0%] |
| XAUUSD | 147 | 69.4% [61.5%, 76.3%] | 85.0% [78.4%, 89.9%] |

### 2.5 Per-session fill rates

| Session | n | Far-edge limit | Midpoint limit |
|---|---|---|---|
| London | 197 | 75.1% [68.6%, 80.6%] | 88.3% [83.1%, 92.1%] |
| NY | 186 | 75.8% [69.2%, 81.4%] | 91.4% [86.5%, 94.6%] |
| Off-Session | 161 | 58.4% [50.7%, 65.7%] | 82.0% [75.3%, 87.2%] |
| Tokyo | 182 | 75.3% [68.5%, 81.0%] | 88.5% [83.0%, 92.3%] |

---

## 3. Mean/median R per resolved setup, by method

'Resolved' = filled AND outcome ∈ {CONTINUED, REVERSED} (UNRESOLVED and NO_FILL excluded). R is computed from the *re-derived* SL distance using the new entry price.

| Anchor | Method | n_resolved | WR | Mean R | Median R | Boot 95% CI |
|---|---|---|---|---|---|---|
| far_edge | market | 709 | 77.2% | -0.006 | +0.077 | [-0.065, +0.056] |
| far_edge | limit | 498 | 39.4% | +0.155 | -1.000 | [+0.016, +0.298] |
| far_edge | hybrid | 709 | 77.2% | +0.247 | +0.318 | [+0.177, +0.318] |
| midpoint | market | 709 | 77.2% | -0.006 | +0.077 | [-0.065, +0.056] |
| midpoint | limit | 606 | 66.5% | +0.123 | +0.387 | [+0.048, +0.202] |
| midpoint | hybrid | 709 | 77.2% | +0.091 | +0.234 | [+0.035, +0.148] |

### 3.1 R per CANDIDATE (treating missed limits and unresolved as 0R)

This metric tells you the expected R per CANDIDATE you'd see in production, accounting for the fact that the limit may not fill.

| Anchor | Method | n | Mean R per candidate | Median | Boot 95% CI |
|---|---|---|---|---|---|
| far_edge | market | 726 | -0.006 | +0.070 | [-0.063, +0.054] |
| far_edge | limit | 726 | +0.106 | +0.000 | [+0.009, +0.204] |
| far_edge | hybrid | 726 | +0.241 | +0.310 | [+0.172, +0.312] |
| midpoint | market | 726 | -0.006 | +0.070 | [-0.063, +0.054] |
| midpoint | limit | 726 | +0.103 | +0.256 | [+0.040, +0.171] |
| midpoint | hybrid | 726 | +0.089 | +0.220 | [+0.035, +0.146] |
| far_edge | two_leg_hybrid | 726 | +0.077 | +0.000 | [+0.010, +0.145] |
| midpoint | two_leg_hybrid | 726 | +0.057 | +0.177 | [+0.004, +0.112] |

**Note on two_leg_hybrid:** Alternative interpretation of hybrid where market and limit are treated as TWO separate positions with equal weight, R averaged. Spec definition (single blended-entry position) is reported as `hybrid` rows.

---

## 4. R differential (limit/hybrid vs market)

### 4.1 Paired R differential on rows where BOTH methods resolved

| Anchor | Comparison | n_paired | Mean diff | Median diff | Boot 95% CI | Wilcoxon p |
|---|---|---|---|---|---|---|
| far_edge | limit_minus_market | 498 | +0.240 | +0.000 | [+0.108, +0.368] | 0.0000 |
| far_edge | hybrid_minus_market | 709 | +0.253 | +0.000 | [+0.207, +0.298] | 0.0000 |
| midpoint | limit_minus_market | 605 | +0.150 | +0.203 | [+0.077, +0.219] | 0.0000 |
| midpoint | hybrid_minus_market | 709 | +0.097 | +0.091 | [+0.062, +0.127] | 0.0000 |

### 4.2 Per-CANDIDATE R differential (missed limits and unresolved → 0R)

| Anchor | Comparison | n | Mean diff | Boot 95% CI |
|---|---|---|---|---|
| far_edge | limit_minus_market | 726 | +0.112 | [+0.023, +0.204] |
| far_edge | hybrid_minus_market | 726 | +0.247 | [+0.204, +0.294] |
| far_edge | two_leg_hybrid_minus_market | 726 | +0.082 | [+0.038, +0.128] |
| midpoint | limit_minus_market | 726 | +0.109 | [+0.045, +0.168] |
| midpoint | hybrid_minus_market | 726 | +0.095 | [+0.062, +0.125] |
| midpoint | two_leg_hybrid_minus_market | 726 | +0.063 | [+0.031, +0.092] |

**Hybrid R interpretations diverge.** Spec literal `hybrid` (single position at blended entry) gives a much larger headline benefit than the production-realistic `two_leg_hybrid` (two separate positions, R averaged). The mechanism: blended entry has a TIGHTER SL distance than market, so each TP hit yields a HIGHER R-multiple. In real trading, the limit leg often fills LATER than the market leg, so they have separate timelines and outcomes, making `two_leg_hybrid` the more realistic estimate.

---

## 5. Missed-setup analysis

On rows where the limit did NOT fill, what would the market entry have produced?

| Anchor | n_missed | Continued | Reversed | WR_market_on_missed | Mean R_market | Median R_market | Boot 95% CI |
|---|---|---|---|---|---|---|---|
| far_edge | 206 | 193 | 0 | 100.0% | +0.175 | +0.157 | [+0.133, +0.221] |
| midpoint | 89 | 87 | 0 | 100.0% | +0.087 | +0.130 | [+0.029, +0.147] |

**Interpretation:** This is the expected R FOREGONE per setup if you switched to pure-limit (no market fallback). Multiply by miss count to get total foregone R.

---

## 6. Per-symbol & per-session breakdowns (n>=5)

### 6.1 Per-symbol limit-minus-market R differential (paired resolved)

| Symbol | Far-edge n_p | Far-edge mean diff | Far-edge 95% CI | Mid n_p | Mid mean diff | Mid 95% CI |
|---|---|---|---|---|---|---|
| GBPJPY | 106 | +0.128 | [-0.243, +0.475] | 128 | +0.075 | [-0.200, +0.298] |
| GBPUSD | 103 | +0.295 | [+0.026, +0.575] | 125 | +0.138 | [+0.005, +0.260] |
| US30_cash | 104 | +0.315 | [+0.055, +0.587] | 119 | +0.199 | [+0.067, +0.328] |
| USDJPY | 89 | +0.121 | [-0.135, +0.388] | 114 | +0.198 | [+0.063, +0.325] |
| XAUUSD | 96 | +0.332 | [+0.096, +0.575] | 119 | +0.149 | [+0.035, +0.264] |

### 6.2 Per-session limit-minus-market R differential (paired resolved)

| Session | Far-edge n_p | Far-edge mean diff | Far-edge 95% CI | Mid n_p | Mid mean diff | Mid 95% CI |
|---|---|---|---|---|---|---|
| London | 144 | +0.295 | [+0.060, +0.529] | 168 | +0.123 | [+0.007, +0.230] |
| NY | 137 | +0.458 | [+0.221, +0.691] | 161 | +0.230 | [+0.113, +0.346] |
| Off-Session | 85 | -0.133 | [-0.549, +0.209] | 121 | +0.049 | [-0.227, +0.246] |
| Tokyo | 132 | +0.194 | [-0.019, +0.419] | 155 | +0.177 | [+0.063, +0.297] |

### 6.3 OB-size quintile stratification (Q5)

Stratified by `ob_body_size_atr` quintile (per CEO decision: stratify, do NOT subset).

| OB-size quintile | n | Far-edge fill | Far-edge n_p | Far-edge mean diff | Far-edge 95% CI | Mid fill | Mid n_p | Mid mean diff | Mid 95% CI |
|---|---|---|---|---|---|---|---|---|---|
| Q1_smallest | 146 | 84.9% | 123 | +0.351 | [+0.152, +0.547] | 91.8% | 133 | +0.185 | [+0.065, +0.303] |
| Q2 | 145 | 74.5% | 104 | +0.237 | [-0.126, +0.533] | 89.7% | 127 | +0.188 | [-0.081, +0.370] |
| Q3 | 145 | 67.6% | 95 | +0.318 | [+0.029, +0.607] | 86.9% | 123 | +0.201 | [+0.077, +0.326] |
| Q4 | 145 | 71.7% | 98 | -0.056 | [-0.309, +0.207] | 86.9% | 121 | +0.033 | [-0.115, +0.170] |
| Q5_largest | 145 | 59.3% | 78 | +0.347 | [-0.027, +0.743] | 83.4% | 101 | +0.137 | [-0.030, +0.304] |

---

## 7. Pre-committed hypothesis verdict

**H1 (primary):** Limit-at-far-edge adds ≥ +0.2R per filled setup vs market AND fills >40% of CANDIDATEs
- Far-edge limit fill rate: 71.6% (>40% threshold)
- Far-edge limit-minus-market mean R (paired resolved): +0.240
- Boot 95% CI: [+0.108, +0.368]
- CI strictly above zero: True | CI lower bound exceeds +0.2 threshold: False
- **Verdict (point-estimate): HOLDS**
- **Caveat:** Mean exceeds +0.2R threshold but CI lower bound (+0.108) is below threshold. Pre-committed verdict criterion is point-estimate based; under a stricter CI-must-clear-threshold standard, H1 would be UNDETERMINED.

**H2 (alternative):** Hybrid 50/50 (far-edge anchor) per CANDIDATE produces ≥ +0.1R over pure market
- Far-edge hybrid-minus-market mean R (per CANDIDATE): +0.247 (boot 95% CI lo: +0.204)
- CI strictly above zero: True
- **Verdict: HOLDS**

**H2b (midpoint variant):** Limit-at-midpoint adds ≥ +0.1R per filled setup AND fills >50% of CANDIDATEs
- Midpoint limit fill rate: 87.7%
- Midpoint limit-minus-market mean R (paired resolved): +0.150 (boot 95% CI lo: +0.077)
- CI strictly above zero: True
- **Verdict: HOLDS**

**H3 (null):** No anchor produces meaningful improvement (all diffs <+0.05R OR fill rates <30%)
- All diffs below +0.05R: False
- All fill rates below 30%: False
- **Verdict: DOES NOT HOLD**

### Final decision (per spec decision tree)

**Decision per spec tree:** H1 holds → recommend deploying hybrid 50/50 (far-edge anchor) to live shadow first.

---

## 8. Limitations & methodological choices

1. **Market entry definition.** Per spec: market entry = retest M15 candle close. This differs from the A2_v2 study CSV's entry rule (`retest_entry_price`), which uses next-candle open if the retest candle's close falls outside the OB zone. Recomputing market R from raw data using the spec's literal definition yields slightly different numbers than the CSV's `continuation_r_a` field, particularly for deep-wick retests where close < ob_low (long).

2. **R sign convention.** R = (target − entry)/SL_distance for long; R = (entry − target)/SL_distance for short. For 'CONTINUED' setups where the entry already started past the target (e.g., a short whose retest closed below the target line), R can be negative — TP fires immediately on the next candle, but the trade actually loses money relative to entry. This is the semantically correct P&L convention; A2_v2's CSV uses abs(target − entry)/SL_dist which always reports positive R on CONTINUED, masking these 'lose-on-the-way-down' cases.

3. **Same-bar SL+TP+entry resolution.** Per spec edge case #3, if the limit fills AND SL hits AND TP hits all within the same M15 candle, conservative pessimistic resolution (SL before TP) is applied. For market entries (filled at close), only candles after the retest candle are walked forward — no intra-bar checks on the entry candle.

4. **Gap fills.** If the next candle's open is already past the limit price, the limit fills at the gap open price (which is BETTER than the limit for the buyer in absolute terms but may give a degenerate SL distance if the open gaps below SL). Tracked via `_via_gap` flag.

5. **Hybrid R definition.** Two interpretations reported:
   - `hybrid` (spec literal): single position with blended entry = 0.5×market + 0.5×limit. Single SL distance from blended entry. Single R outcome.
   - `two_leg_hybrid` (sensitivity): two separate equal-weight positions; R averaged. When one leg wins and the other loses (rare but real for deep wicks), the two interpretations differ materially. Reported in §3.1.

6. **OB body midpoint requires raw H1 read.** The CSV does not store `ob_open` and `ob_close` separately, only `ob_body_size = abs(ob_close - ob_open)`. Midpoint is computed by reading the H1 candle at `ob_formation_ts` from `data/historical/{SYMBOL}_H1.csv` and computing `(open + close) / 2`.

7. **OB zone derivation algebra.** OB high/low are derived analytically from CSV fields rather than re-detected. This avoids spec drift but inherits any rounding errors in `target_a_price` and `sl_a_price`. Manually spot-checked against the formula `target_a = ob_high + ob_body` (long) for 10 rows.

8. **Window length.** 48 M15 candles (12h) for SL/TP resolution, matching Geometry A. UNRESOLVED outcomes treated as missed setups (R = None for resolved, R = 0 for per-candidate aggregations).

9. **Wilcoxon signed-rank.** Two-sided p-value via normal approximation, applied to paired R differentials. Implementation is in-house (no scipy.stats import) — uses standard rank-sum statistic with normal approximation; valid for n ≥ 10 nonzero differences. For very small samples or all-zero differences, returns None.

10. **Bootstrap CI.** 5000 resamples, percentile method, seed=42 for reproducibility.

11. **Data quality.** All 726 retests had matching M15 candles. No errors during simulation. The XAUUSD silent gap (per session 24 handoff) lies before this study's window and does not affect any rows.

---

## Appendix: Convergence cross-check inputs

These numbers are the convergence-check targets for `intra_b`:

- Far-edge limit fill rate: **71.63%** (520/726)
- Midpoint limit fill rate: **87.74%** (637/726)
- Far-edge limit-minus-market mean R (paired resolved): **+0.240** (n_paired = 498)
- Midpoint limit-minus-market mean R (paired resolved): **+0.150** (n_paired = 605)
- H1 verdict: **HOLDS**
- H2 verdict: **HOLDS**
- H2b verdict: **HOLDS**
- H3 verdict: **DOES NOT HOLD**