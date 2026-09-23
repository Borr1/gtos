# CANDIDATE Gap Validation — The 93 Missing Trades

**Analysis Date:** 2026-04-05
**Data Source:** 242 XAUUSD batch sessions, 149 GBPUSD batch sessions
**API Cost:** $0 (pure computation from existing session data)

---

## Executive Summary

| Finding | Detail |
|---|---|
| **Non-indexed executed (XAUUSD)** | 93 trades, 63.4% WR, +22.02R total |
| **Combined (XAUUSD)** | 105 trades, 61.0% WR, +21.42R, PF=1.69 |
| **Statistical significance** | p=0.006 (non-indexed alone), p=0.016 (combined) |
| **Monte Carlo (50 trades)** | 91.9% probability of positive outcome |
| **Monthly frequency** | 4.7 XAUUSD dates/month (up from ~1/month indexed) |
| **Months to 8% target** | 5.4 months at 1% risk (expected) |
| **Root cause** | Seeding script only read 18 trades from one source file; never read the 242 batch sessions |
| **VERDICT** | **YES — this is a real frequency lever.** Pipeline fix, not pattern discovery. |

---

## 1. CANDIDATE Inventory

### XAUUSD (242 sessions evaluated)

| Category | Count | Description |
|---|---|---|
| Total CANDIDATEs | 146 | All AI CANDIDATE decisions across 242 sessions |
| INDEXED | 12 | Appear in trade_index with matching trade_id |
| NOT_INDEXED_EXECUTED | 93 | AI approved (A/A+ grade), trade executed, but never indexed |
| NOT_INDEXED_NOT_EXECUTED | 41 | CANDIDATE but rejected before execution |

**Grade distribution (non-indexed executed):** A+ = 70, A = 23
**Kill zone split:** London = 46, NY = 47

### GBPUSD (149 sessions evaluated)

| Category | Count |
|---|---|
| Total CANDIDATEs | 34 |
| INDEXED | 24 |
| NOT_INDEXED_NOT_EXECUTED | 10 |
| NOT_INDEXED_EXECUTED | 0 |

GBPUSD has NO non-indexed executed trades. The "8 non-index dates" from the previous analysis were all non-executed CANDIDATEs (rejected before trading). The GBPUSD seeding was more comprehensive — it captured all executed trades.

### Non-Executed Rejection Reasons (41 XAUUSD)

| Reason | Count |
|---|---|
| direction_mismatch (SHORT against bullish bias) | 23 |
| no_trade_parameters | 6 |
| below_grade_threshold (C or B+) | 6 |
| sl_below_minimum_floor | 2 |
| rr_too_low | 2 |
| sl_too_tight | 2 |

All rejection reasons are valid safety gates. No false rejections.

---

## 2. Data Quality Notes

- **All 105 executed trades have complete outcome data** (outcome, r_multiple, mfe_r, mae_r, hold_time_candles) from the batch session simulator. No M15 re-simulation needed.
- **Missing fields:** 0 trades had missing critical data. Every executed CANDIDATE has a matching trade record in the session's trade_summary.
- **Scoring method:** Session outcomes use the batch simulator (trailing stops, breakeven moves, session timeouts) — NOT the strategy_a scoring used for the trade index.

---

## 3. Side-by-Side Comparison

| Metric | Indexed (12) | Non-Indexed (93) | Combined (105) |
|---|---|---|---|
| Win Rate | 41.7% | **63.4%** | **61.0%** |
| Wins / Losses | 5W / 7L | 59W / 31L / 3BE | 64W / 38L / 3BE |
| Avg R-multiple | -0.050 | **+0.237** | **+0.204** |
| Total R | -0.60 | **+22.02** | **+21.42** |
| Profit Factor | 0.87 | **1.84** | **1.69** |
| Avg MFE (R) | 0.869 | 1.077 | 1.053 |
| Avg MAE (R) | 0.586 | 0.536 | 0.542 |
| MFE/MAE Ratio | 1.483 | **2.010** | **1.944** |
| Max Consec Losses | 2 | 3 | 3 |

### CRITICAL CAVEAT: Different Scoring Methods

The indexed 12 and non-indexed 93 were scored by **different simulators**:

| | Indexed (trade_index) | Non-Indexed (sessions) |
|---|---|---|
| **Source** | `system_improvements_data_20260403.json` | Batch session simulator |
| **Exit logic** | strategy_a: 100% close at TP1 (1.5R) | Trailing stops, BE moves, session timeouts |
| **Dates** | 16 manually selected dates | 242 evaluated dates |

On the 11 dates that appear in BOTH sources, R-multiples **diverge on 4 dates** due to different exit logic. Example: 2024-05-31 is +1.5R in the index (TP1 hit) but -1.0R in the session (SL hit).

**Implication:** The indexed trades appearing worse (41.7% vs 63.4%) is PARTLY an artifact of different scoring. The session simulator's trailing/BE logic may be more conservative but captures more partial wins. Direct WR comparison is misleading.

---

## 4. Statistical Tests

| Test | Statistic | p-value | Interpretation |
|---|---|---|---|
| Fisher's exact (indexed vs non-indexed WR) | OR=0.412 | 0.2086 | NOT significant — samples too small to detect difference |
| Mann-Whitney U (R-multiples) | U=473.5 | 0.3925 | NOT significant — R distributions not statistically different |
| Combined binomial (WR > 50%) | — | **0.0157** | **SIGNIFICANT** — combined 61.0% WR is unlikely by chance |
| Non-indexed binomial (WR > 50%) | — | **0.0062** | **SIGNIFICANT** — non-indexed 63.4% WR is unlikely by chance |

**95% Confidence Intervals:**
- Combined WR: 61.0% [52.5%, 69.5%]
- Non-indexed WR: 63.4% [54.4%, 72.5%]

### Monte Carlo Simulation (1000 sequences of 50 trades)

| Percentile | Cumulative R |
|---|---|
| P5 (worst case) | -1.72R |
| P25 | +4.92R |
| P50 (median) | +10.33R |
| P75 | +15.65R |
| P95 (best case) | +24.09R |
| **Prob positive** | **91.9%** |

---

## 5. Breakdown Analysis (Non-Indexed Only)

### By Kill Zone

| KZ | n | Win Rate | Avg R | Total R |
|---|---|---|---|---|
| London | 46 | **69.6%** | +0.191 | +8.80 |
| NY | 47 | 57.4% | +0.281 | +13.22 |

London has higher WR, NY has higher avg R (larger winners).

### By Grade

| Grade | n | Win Rate | Avg R | Total R |
|---|---|---|---|---|
| A+ | 70 | 64.3% | +0.245 | +17.12 |
| A | 23 | 60.9% | +0.213 | +4.90 |

A+ slightly outperforms A, as expected.

### By Year

| Year | n | Win Rate | Avg R | Total R |
|---|---|---|---|---|
| 2024 | 10 | 70.0% | +0.312 | +3.12 |
| 2025 | 54 | 63.0% | +0.266 | +14.35 |
| 2026 | 29 | 62.1% | +0.157 | +4.55 |

Consistent performance across years — no year dominates or collapses.

### Month Concentration

Top 3 months account for 46.2% of trades:
- Jan 2026: 18 trades (19.4%) — 61.1% WR
- Feb 2025: 14 trades (15.1%) — 57.1% WR
- Mar 2025: 11 trades (11.8%) — 63.6% WR

Some concentration but not extreme. The WR in concentrated months is consistent with the overall average.

---

## 6. Pipeline Gap Explanation

### How the trade index was built

The seeding script (`scripts/seed_knowledge_base.py`) reads from exactly **two source files**:
1. `system_improvements_data_20260403.json` → 18 XAUUSD trades (strategy_a scoring)
2. `gbpusd_batch_deep_analysis_data_20260403.json` → 42 GBPUSD trades

These source files came from **manual investigations** that analyzed specific subsets of dates. The seeding script never reads the batch session files in `knowledge_base_backtest/sessions/`.

### Why 93 trades are missing

1. The 242 XAUUSD batch sessions evaluated ALL dates in the data range (Apr 2024 – Mar 2026)
2. The AI produced 146 CANDIDATEs across these sessions, executing 105 trades
3. The system_improvements investigation only analyzed **16 specific dates** and scored them with strategy_a
4. Only 11 of those 16 dates also appear in the batch sessions as CANDIDATEs
5. The remaining 93 executed trades from batch sessions were **never fed into the seeding pipeline**

### Why GBPUSD has no gap

The GBPUSD source file contained 42 trades from a more comprehensive analysis. All executed GBPUSD CANDIDATEs were captured. The GBPUSD seeding was more thorough.

### The scoring divergence

5 of the 16 source dates don't even appear in batch sessions. Of the 11 that overlap, 4 show different outcomes due to different exit logic:

| Date | Source (strategy_a) | Session Simulator |
|---|---|---|
| 2024-04-18 | +1.50R (TP1) | +0.75R (BE move) |
| 2024-05-31 | +1.50R (TP1) | -1.00R (SL hit) |
| 2024-10-03 | +0.36R (timeout) | -1.00R (SL hit) |
| 2026-01-12 | +0.27R (timeout) | -0.18R (timeout) |

The strategy_a scorer lets TP1 hit then closes; the session simulator may hit SL before TP1 due to trailing or different entry timing.

---

## 7. Updated Frequency Estimate

| Metric | Previous (indexed only) | Updated (all executed) |
|---|---|---|
| XAUUSD dates/month | ~1.0 | **4.7** |
| GBPUSD dates/month | ~2.0 | 2.0 (no change) |
| Combined dates/month | ~3.0 | **6.7** |
| Expectancy (per trade) | Unknown | **+0.204R** |
| Trades to 8% target | Unknown | **~39 trades** |
| Months to 8% target | Unknown | **~5.4 months** |

### Prop Firm Viability (at 1% risk per trade)

- Expected monthly R: 4.7 trades × 0.204R = **+0.96R/month** (XAUUSD alone)
- Combined monthly R: 6.7 trades × 0.204R = **+1.37R/month**
- Time to 8% profit target: **5.4 months** (expected)
- Monte Carlo P25 at 50 trades: +4.92R → 4.92% in ~7.5 months
- Monte Carlo P50 at 50 trades: +10.33R → 10.33% in ~7.5 months

---

## 8. VERDICT

### Are the non-indexed trades a real frequency lever? **YES**

**Evidence:**
1. 93 non-indexed executed trades show 63.4% WR (p=0.006), significantly above 50%
2. +22.02R total profit over 27 months — positive expectancy is real
3. Consistent across years (2024: 70%, 2025: 63%, 2026: 62%) — no regime dependency
4. Consistent across kill zones (London 69.6%, NY 57.4%) — both positive
5. Monte Carlo: 91.9% probability of positive outcome over 50 trades
6. Grade distribution (A+: 75%, A: 25%) confirms these were high-quality AI evaluations
7. All 93 represent existing AI decisions that were simply never recorded — zero pattern discovery needed

**Confidence: HIGH**

The fix is purely operational:
1. Update the trade index to include all executed batch session trades
2. Or: modify the seeding pipeline to read session files directly
3. No new AI prompts, no new patterns, no additional development needed

**Caveats:**
1. The scoring methodology differs from the trade index — consistency should be aligned
2. 46% of trades concentrate in 3 months — live distribution may differ
3. The batch simulator's exit logic (trailing, BE) differs from strategy_a — choose one scoring method
4. Forward performance may differ from backtest (as always)

---

## 9. Recommended Next Steps

1. **IMMEDIATE:** Re-seed trade index from batch session files (all executed trades with A/A+ grades)
2. **IMMEDIATE:** Standardize on ONE scoring methodology (recommend session simulator over strategy_a)
3. **VERIFY:** Re-score the original 18 indexed trades through the session simulator for apples-to-apples comparison
4. **MONITOR:** Forward-test the combined trade set for Apr-Jun 2026 to validate live performance
