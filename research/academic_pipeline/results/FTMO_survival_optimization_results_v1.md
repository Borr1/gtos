# FTMO Survival Optimization Test Results

**Date:** 2026-04-13
**Source hypothesis:** Ex-bank trader Patrick — partial close / "free trade" approach
**Trades analyzed:** 129 (128 with MFE/MAE data, 1 missing)
**Monte Carlo:** 10,000 simulations × 100 trades, risk=1.0%, DD threshold=10%, profit target=10%
**Data source:** entry_engineering_dataset.csv (Oct 2024 – Mar 2026)

---

## 1. Data Summary

**Trades:** 129 total — 80 WIN, 45 LOSS, 4 BREAKEVEN
**Win rate (raw outcomes):** 62.0%
**Mean R (actual):** +0.2776R
**MFE range:** 0.000 to 6.672R, mean 1.185R
**MAE range:** 0.000 to 3.042R, mean 0.543R

**MFE threshold trigger rates (all 128 trades with MFE data):**
  MFE >= 0.50R: 68/128 = 53.1% (52 wins, 16 losses)
  MFE >= 0.75R: 57/128 = 44.5% (45 wins, 12 losses)
  MFE >= 1.00R: 47/128 = 36.7% (38 wins, 9 losses)
  MFE >= 2.00R: 25/128 = 19.5% (24 wins, 1 losses)
  MFE >= 2.50R: 20/128 = 15.6% (20 wins, 0 losses)

**Key data quality note:**
MFE values represent maximum favorable excursion of the RAW price path, not capped at TP.
This means a trade that hit TP at 1.5R may show MFE of 3.0R (price continued after would-be close).
This is CORRECT for the simulation: MFE tells us how far price went, enabling counterfactual exit placement.

---

## 2. Simulation Logic and Assumptions

**Partial close simulation rule (per trade):**

```
if MFE >= partial_threshold:
    partial_gain = partial_pct × partial_threshold   # locked immediately
    if MFE >= high_tp:
        runner_gain = runner_pct × high_tp           # runner hits big TP
    else:
        runner_gain = runner_pct × max(0, r_actual)  # runner at BE or timeout
    simulated_R = partial_gain + runner_gain
else:
    simulated_R = r_actual                           # no trigger, unchanged
```

**Key sequencing assumption:** For loss trades where MFE >= threshold — price must
pass through entry (0R) on its way from the partial threshold to the SL (-1.0R).
Therefore the runner is stopped at 0R, not at -1.0R. This is the source of the
"free trade" protection. This is a conservative and mathematically sound assumption.

**Timeout handling:** If r_actual > 0 (positive timeout, price above entry at close)
and MFE < high_tp, the runner closes at the same positive price: runner_gain = runner_pct × r_actual.
This is accurate because runner SL (at 0R) would not be triggered if price stayed above entry.

---

## 3. Per-Trade Comparison

| Strategy | Mean R | Median R | Win Rate | Std Dev | Total R (129 trades) |
|----------|--------|----------|----------|---------|----------------------|
| Current | +0.2776 | +0.1500 | 62.8% | 1.1882 | +35.81 |
| Variant A | +0.2456 | +0.2500 | 75.2% | 0.7036 | +31.68 |
| Variant B | +0.2536 | +0.2500 | 72.1% | 0.7827 | +32.72 |
| Variant C | +0.3005 | +0.2100 | 69.8% | 0.9546 | +38.76 |

**Interpretation of per-trade metrics:**

- **Variant A:** mean R -0.0320R vs current, WR +12.4%
- **Variant B:** mean R -0.0240R vs current, WR +9.3%
- **Variant C:** mean R +0.0229R vs current, WR +7.0%

**Trigger counts per variant:**

| Strategy | No Trigger | Partial Only (runner at BE) | Partial + Runner TP |
|----------|------------|------------------------------|---------------------|
| Variant A | 61 | 43 | 25 |
| Variant B | 72 | 32 | 25 |
| Variant C | 82 | 27 | 20 |

**Biggest improvements under Variant A (Patrick conservative):**

| Trade | Outcome | r_actual | sim_r | MFE | Delta |
|-------|---------|----------|-------|-----|-------|
| bt_2025-09-30_london_001_xauus | LOSS | -1.000 | +1.250 | 2.100 | +2.250 |
| bt_2026-01-16_london_001_xauus | LOSS | -1.000 | +0.250 | 1.509 | +1.250 |
| bt_2026-01-13_ny_002_xauusd | LOSS | -1.000 | +0.250 | 1.148 | +1.250 |
| bt_2025-12-30_ny_001_xauusd | LOSS | -1.000 | +0.250 | 1.739 | +1.250 |
| bt_2025-12-18_london_001_xauus | LOSS | -1.000 | +0.250 | 0.868 | +1.250 |
| bt_2025-12-01_ny_001_gbpusd | LOSS | -1.000 | +0.250 | 1.007 | +1.250 |
| bt_2025-10-09_ny_002_xauusd | LOSS | -1.000 | +0.250 | 0.660 | +1.250 |
| bt_2025-06-26_ny_001_xauusd | LOSS | -1.000 | +0.250 | 1.131 | +1.250 |
| bt_2025-06-25_london_001_xauus | LOSS | -1.000 | +0.250 | 0.508 | +1.250 |
| bt_2025-03-24_london_001_xauus | LOSS | -1.000 | +0.250 | 0.729 | +1.250 |

**Biggest degradations under Variant A:**

| Trade | Outcome | r_actual | sim_r | MFE | Delta |
|-------|---------|----------|-------|-----|-------|
| bt_2025-05-05_london_001_xauus | WIN | +3.990 | +1.250 | 6.563 | -2.740 |
| bt_2025-01-30_london_001_xauus | WIN | +3.770 | +1.250 | 6.672 | -2.520 |
| bt_2025-04-17_ny_001_xauusd | WIN | +3.470 | +1.250 | 5.302 | -2.220 |
| bt_2025-03-13_ny_002_xauusd | WIN | +3.350 | +1.250 | 4.607 | -2.100 |
| bt_2026-01-22_london_001_xauus | WIN | +3.310 | +1.250 | 4.315 | -2.060 |
| bt_2026-03-06_ny_001_xauusd | WIN | +3.030 | +1.250 | 3.704 | -1.780 |
| bt_2025-03-05_london_001_gbpus | WIN | +2.700 | +1.250 | 4.213 | -1.450 |
| bt_2026-02-03_ny_002_xauusd | WIN | +2.690 | +1.250 | 3.882 | -1.440 |
| bt_2025-03-04_london_001_gbpus | WIN | +2.640 | +1.250 | 4.052 | -1.390 |
| bt_2025-12-10_ny_001_gbpusd | WIN | +2.450 | +1.250 | 3.902 | -1.200 |

---

## 4. Monte Carlo FTMO Results

_(10,000 simulations × 100 trades, 1% risk/trade, starting equity $100K, 10% max DD fail, 10% profit target)_

| Strategy | P(pass) | DD Breach Rate | Mean Max DD | Mean Terminal Equity |
|----------|---------|----------------|-------------|----------------------|
| Current | **93.4%** | 0.5% | 1.69% | $131,655 |
| Variant A | **98.0%** | 0.0% | 0.68% | $127,655 |
| Variant B | **97.7%** | 0.0% | 0.85% | $128,654 |
| Variant C | **98.3%** | 0.0% | 0.97% | $134,784 |

**Difference vs Current:**

| Strategy | ΔP(pass) | ΔDD Breach Rate | ΔMean Max DD | ΔMean Terminal |
|----------|----------|-----------------|--------------|----------------|
| Variant A | **+4.6%** | -0.5% | -1.01% | $-4,000 |
| Variant B | **+4.3%** | -0.5% | -0.84% | $-3,001 |
| Variant C | **+4.9%** | -0.5% | -0.72% | $+3,129 |

---

## 5. Statistical Tests

**Proportion tests: P(pass FTMO) — variant vs current**

_(Two-proportion z-test, H0: equal pass rates, two-tailed)_

| Comparison | P(pass) Current | P(pass) Variant | z-stat | p-value | Cohen h | Significant? |
|------------|-----------------|-----------------|--------|---------|---------|--------------|
| Current vs Variant A | 93.39% | 97.99% | +16.017 | 0.0000 | +0.236 | YES (p<0.05) |
| Current vs Variant B | 93.39% | 97.65% | +14.562 | 0.0000 | +0.212 | YES (p<0.05) |
| Current vs Variant C | 93.39% | 98.33% | +17.534 | 0.0000 | +0.261 | YES (p<0.05) |

**Welch t-test: Mean max drawdown — variant vs current**

_(H0: equal mean max DD, two-tailed)_

| Comparison | DD Current | DD Variant | t-stat | p-value | Significant? |
|------------|------------|------------|--------|---------|--------------|
| Current vs Variant A | 1.691% | 0.685% | -45.181 | 0.0000 | YES (p<0.05) |
| Current vs Variant B | 1.691% | 0.847% | -36.575 | 0.0000 | YES (p<0.05) |
| Current vs Variant C | 1.691% | 0.975% | -30.150 | 0.0000 | YES (p<0.05) |

**Terminal equity ratio (variant / current):**

- **Variant A:** 0.970x current (127,655 vs 131,655) — ✓ >= 90%
- **Variant B:** 0.977x current (128,654 vs 131,655) — ✓ >= 90%
- **Variant C:** 1.024x current (134,784 vs 131,655) — ✓ >= 90%

---

## 6. Pattern Analysis: What Changes Under Partial Close

**By outcome type — Variant A (most conservative, clearest signal):**

**WIN trades (n=80):** mean delta -0.3030R, 34 degraded, 30 unchanged, 16 improved
**LOSS trades (n=45):** mean delta +0.4469R, 0 degraded, 29 unchanged, 16 improved
**BREAKEVEN trades (n=4):** mean delta +0.0000R, 0 degraded, 4 unchanged, 0 improved

**Losses saved by Variant A (MFE reached 0.5R before SL):**

  Count: 16 losses rescued (out of 45 total losses)
  Average rescue delta: +1.2569R per rescued trade
  Average rescued outcome: +0.3125R (was -0.9444R)

**Wins degraded by Variant A (partial at 0.5R reduces upside):**
  Count: 34 wins degraded (out of 80 total wins)
  Average degradation: -0.8051R per degraded trade

**The core tradeoff (Variant A):**
  Losses converted: 16 at avg rescue +1.2569R each
  = Total gain from saving losses: +20.1100R
  Wins degraded: 34 at avg -0.8051R each
  = Total cost from degrading wins: -27.3750R
  Net change over full batch: -4.1300R

---

## 7. Verdict and Recommendation

**Pre-committed decision criteria:**
  CONFIRM: ΔP(pass) >= +5pp AND p < 0.05 AND terminal equity >= 90% of current
  REJECT: ΔP(pass) <= 0 OR terminal equity drops > 20%
  INCONCLUSIVE: meets some but not all criteria (usually: improvement real but below 5pp threshold)

### Variant A: **INCONCLUSIVE**
  ΔP(pass) = +4.6% (just below 5pp threshold), p-value = 0.0000 ✓, terminal ratio = 0.970x ✓
  → Statistically significant improvement. Fails only on 5pp magnitude threshold.

### Variant B: **INCONCLUSIVE**
  ΔP(pass) = +4.3% (below 5pp threshold), p-value = 0.0000 ✓, terminal ratio = 0.977x ✓
  → Statistically significant improvement. Fails only on 5pp magnitude threshold.

### Variant C: **INCONCLUSIVE** (borderline CONFIRM)
  ΔP(pass) = +4.9% (0.1pp below 5pp threshold), p-value = 0.0000 ✓, terminal ratio = 1.024x ✓
  → Meets statistical significance AND terminal equity criteria. Misses CONFIRM by 0.1pp on pass rate.
  → **This is the pre-committed threshold. It must not be moved post-hoc.**

### Overall Recommendation

**None of the three variants meet all CONFIRM criteria under the pre-committed gate.**

However, the direction of evidence is clear and statistically robust:
- All three variants show p < 0.0001 improvement in P(pass)
- All three eliminate DD breaches completely (0.5% → 0.0%)
- All three reduce mean max DD by 40–60% (1.69% → 0.68–0.97%)
- Variant C increases terminal equity (+$3,129) AND improves pass rate AND passes p < 0.05

**Actionable next step: Shadow-test Variant C on live trades.**
Log hypothetical partial close outcomes (33% @ 1.0R, runner TP 2.5R) without executing them.
After 30+ live trades, re-run this analysis with live data. If Variant C shows ΔP(pass) >= 5pp
on live data, promote to WF-2 execution.

**Do NOT adopt yet.** The pre-committed gate exists to prevent post-hoc rationalization.

### The Root Cause of the Near-Miss

Patrick's "free trade" philosophy originated in institutional scalping with 3:1 RR and
discretionary duration. GTOS runs fixed 2-hour timeouts with systematic entries.
The partial close benefit (loss rescue) is partially offset by the systematic reduction in
winner R on trades that don't reach the runner TP.

**The core math (Variant A):**
- 16 losses rescued (avg: +1.26R rescue each) = total gain +20.1R
- 34 wins degraded (avg: -0.81R cost each) = total cost -27.4R
- Net: -4.1R over 129 trades (−0.032R per trade)

Variant C is different: 33% @ 1.0R with runner to 2.5R. The higher partial (1.0R vs 0.5R)
and the higher runner TP (2.5R vs 2.0R) together produce net POSITIVE expectancy (+0.023R/trade)
while still rescuing 9 full losses. This is why Variant C is borderline CONFIRM.

**Critical finding from L4 analysis (B36):** P(2R | 1R reached) = 53.2%. This means
holding at 1R is statistically optimal. Patrick's partial at 0.5R violates this:
you give up 50% position at 0.5R, well before the current system's average exit.
Variant C (partial at 1.0R) does NOT violate this — it takes only 33%, keeping 67% to run.

### Note on L4 vs This Simulation (P(pass) discrepancy)

**L4 Monte Carlo showed P(pass) = 45.9%. This simulation shows 93.4%. Why?**

The L4 simulation used a **theoretical binary model**: 62% of trades = +1.5R, 38% = −1.0R.
This simulation uses the **actual empirical R-distribution** (mean=+0.278R, std=1.188R,
including many small positive timeout exits in the 0–0.5R range).

The actual system produces many small positive outcomes (40 of 80 wins are in the 0–0.5R range),
which dramatically smooth the equity curve. The L4 binary model overstates outcome volatility.

**Both are correct for their purpose:**
- L4 binary model: worst-case theoretical stress test (assumes every win is +1.5R, every loss −1.0R)
- This simulation: empirical reality (captures timeout smoothing, partial exits already in data)

For FTMO planning purposes, the truth is between the two. The empirical simulation is more
accurate for the actual system. The binary model is more conservative.

---

## 8. Limitations and Caveats

1. **Sample size:** 129 trades. Monte Carlo resamples from this empirical distribution.
   The variance in pass rates is driven partly by small-sample uncertainty in the R-distribution.

2. **No daily drawdown simulation:** FTMO's 5% daily DD limit is not modeled.
   Partial close reduces intraday position at risk, which may help with daily DD compliance
   beyond what this simulation shows.

3. **MFE sequencing:** We assume MFE always occurs before the SL is hit.
   For the 9-16 losses with MFE >= threshold, this is almost certainly true (price went
   favorable then reversed). For the very few cases where price gap-reverses, the assumption fails.
   Likely affects < 2 trades.

4. **Constant risk assumption:** 1% of current equity (floating). FTMO often measured
   against initial balance. Using initial balance would reduce bust rate variance.

5. **90-trade FTMO window:** FTMO evaluation typically spans 30-60 calendar days with
   variable trade frequency. 100 trades assumes roughly monthly frequency × 6 months.
   At current ~17 trades/month, this represents ~6 months of trading.

6. **Existing data:** This simulation uses Oct 2024 – Mar 2026 batch data, not live FTMO
   account data. Live implementation may show different behavior due to market regime.

---

*Report generated by FTMO_survival_optimization.py*
*2026-04-13 01:33*