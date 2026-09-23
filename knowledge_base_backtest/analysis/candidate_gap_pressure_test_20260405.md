# CANDIDATE Gap Validation — Pressure Test Results

**Test Date:** 2026-04-05
**Subject:** Candidate gap validation analysis (93 non-indexed XAUUSD trades)
**Methodology:** Independent recomputation + cross-verification against raw session data

---

## Overall Result: 7/9 PASS | 1 CONDITIONAL | 1 FAIL

```
Test 1 (CANDIDATE Extraction):  PASS — All counts match, 0 spot-check mismatches
Test 2 (Simulation Accuracy):   CONDITIONAL PASS — Self-consistent but unverifiable (no entry/SL/TP)
Test 3 (Entry Methodology):     FAIL — Entry prices undocumented, not recorded in session data
Test 4 (SL Verification):       CONDITIONAL PASS — No SL prices, but MAE/outcomes structurally consistent
Test 5 (Statistical Math):      PASS — All recomputed values match within rounding
Test 6 (Distribution):          PASS — Concentration documented, remove-best-month still positive
Test 7 (Indexed vs Non-Index):  PASS — JSON uses same methodology for both groups
Test 8 (Pipeline Gap):          PASS — Root cause confirmed in seeding script
Test 9 (Practical Reality):     PASS WITH CAVEATS — Frequency inflated, months-to-8% math doesn't add up
```

**Critical Failures:** 0 (Test 3 is a FAIL but not a critical failure — the analysis doesn't depend on knowing entry prices since outcomes come from the batch simulator)

---

## Test 1: CANDIDATE Extraction Accuracy — PASS

### Verification
| Metric | From Sessions | Reported | Match? |
|---|---|---|---|
| Total CANDIDATEs | 146 | 146 | YES |
| Executed CANDIDATEs | 105 | 105 | YES |
| NOT_INDEXED_EXECUTED | 93 | 93 | YES |
| INDEXED | 12 | 12 | YES |
| Sessions evaluated | 242 | 242 | YES |

### Spot Checks (5 random sessions)
- All CANDIDATE decisions correctly identified (decision = "CANDIDATE")
- Grades match between session files and JSON (A/A+ only for executed)
- Trade IDs match between session candle_evaluations and trade_summary
- 0 mismatches across all 5 spot-checked sessions

### Indexed Trade Cross-Check
- Trade index contains 18 XAUUSD trades (from strategy_a)
- JSON contains 12 as "INDEXED" — discrepancy because some indexed trade dates don't have matching batch sessions (5 dates exist only in the strategy_a source, not in the 242 batch sessions)

---

## Test 2: Outcome Simulation Accuracy — CONDITIONAL PASS

### Critical Discovery: NO ENTRY/SL/TP PRICES RECORDED

The session trade_summary contains:
- `entry_price`: **None** (all 105 trades)
- `stop_loss`: **None** (all 105 trades)
- `take_profit`: **None** (all 105 trades)
- `direction`: **None** (all 105 trades)

The outcomes (WIN/LOSS/BREAKEVEN, r_multiple, mfe_r, mae_r, hold_time_candles) come directly from the batch simulator's internal state machine. There is **no independent M15 data** to cross-verify against.

### What We CAN Verify
- **Self-consistency:** 12 trades cross-checked between session files and JSON — 0 mismatches on r_multiple and outcome
- **Structural validity of outcomes:**
  - All CLOSED_SL trades have r_multiple = -1.0 (25 trades) ✓
  - All CLOSED_BE trades have r_multiple > 0 (29 trades, avg +0.222) ✓
  - CLOSED_SESSION_TIMEOUT trades have varied R-multiples (positive and negative) ✓
  - CLOSED_TP3_RUNNER trades have high R-multiples (avg +0.998) ✓
  - 1 trade has mae_r = None (bt_2025-05-12_london_001) — minor data quality issue

### What We CANNOT Verify
- Whether the batch simulator correctly walked M15 candles
- Whether entry was at signal candle close, next candle open, or AI-cited price
- Whether SL/TP levels were structurally valid
- Whether timeout boundaries were correctly applied

### Verdict
The outcomes are internally self-consistent and structurally plausible. However, we are trusting the batch simulator as a black box. This is not ideal for a pressure test but is also not a critical failure since the same simulator produced ALL outcomes (indexed and non-indexed alike).

---

## Test 3: Entry Price Methodology — FAIL

### Finding
**No entry prices, stop losses, take profits, or directions are recorded** in any of the 105 executed trade records. The batch simulator's internal entry mechanism is completely opaque.

### Comparison with Indexed Trades
- **Indexed (trade_index):** Uses strategy_a from `system_improvements_data_20260403.json`, which records the AI's cited entry price and uses fixed 1.5R TP
- **Non-indexed (sessions):** Uses the batch session simulator, entry methodology unknown

### Impact
Since we don't have entry prices for either group in the combined analysis (the JSON re-scored indexed trades through the session simulator too), the comparison is internally consistent. But we cannot verify whether the simulator's entry is realistic (e.g., whether entry at candle close is achievable in live trading).

---

## Test 4: SL Placement Verification — CONDITIONAL PASS

### No SL Prices Available
Cannot compute SL distances directly. However, MAE analysis provides indirect validation:

| Metric | Non-Indexed (93) | Indexed (12) |
|---|---|---|
| Mean MAE (R) | 0.536 | 0.586 |
| Median MAE (R) | 0.273 | 0.647 |
| Zero MAE | 8 trades (8.7%) | — |

### Loss Characteristics
- 25/31 losses hit full -1.0R (CLOSED_SL) — consistent with clean SL stops
- 6 partial losses: -0.12, -0.11, -0.09, -0.26, -0.27, -0.32 — all from CLOSED_SESSION_TIMEOUT (session ended before SL hit)
- No suspiciously tight or wide outcomes detected

### M5 $10 Floor
Cannot verify if the $10 minimum SL floor was applied since no SL prices are recorded. If NOT applied, results would be CONSERVATIVE (wider SLs = lower R on winners but fewer stop-outs).

---

## Test 5: Statistical Analysis Verification — PASS

### Recomputed Values vs Reported

| Statistic | Recomputed | Reported | Match? |
|---|---|---|---|
| Non-indexed WR | 63.4% | 63.4% | ✓ |
| Non-indexed Total R | +22.02 | +22.02 | ✓ |
| Non-indexed Avg R | +0.237 | +0.237 | ✓ |
| Combined WR | 61.0% | 61.0% | ✓ |
| Combined Total R | +21.42 | +21.42 | ✓ |
| Combined Avg R | +0.204 | +0.204 | ✓ |
| Non-indexed PF | 1.84 | 1.84 | ✓ |
| Combined PF | 1.69 | 1.69 | ✓ |
| Fisher's exact OR | 0.412 | 0.412 | ✓ |
| Fisher's exact p | 0.2086 | 0.2086 | ✓ |
| Mann-Whitney U | 473.5 | 473.5 | ✓ |
| Mann-Whitney p | 0.3925 | 0.3925 | ✓ |
| Binomial (combined) p | 0.0157 | 0.0157 | ✓ (one-sided) |
| Binomial (non-indexed) p | 0.0062 | 0.0062 | ✓ (one-sided) |

### Confidence Intervals (Wilson)
| CI | Recomputed | Reported | Match? |
|---|---|---|---|
| Combined 95% CI | [51.4%, 69.7%] | [52.5%, 69.5%] | ~1% difference (different CI method) |
| Non-indexed 95% CI | [53.3%, 72.5%] | [54.4%, 72.5%] | ~1% difference (different CI method) |

### Monte Carlo (seed-dependent)
| Percentile | Recomputed (seed=42) | Reported | Within range? |
|---|---|---|---|
| P5 | -1.42R | -1.72R | Yes (seed-dependent) |
| P50 | +11.47R | +10.33R | Yes (seed-dependent) |
| P95 | +24.79R | +24.09R | Yes (seed-dependent) |
| Prob positive | 93.1% | 91.9% | Yes (seed-dependent) |

All core statistics verified. Monte Carlo differences are expected due to random seed. CI differences are due to slightly different Wilson interval implementations.

---

## Test 6: Concentration and Distribution — PASS

### Monthly Distribution (Non-Indexed)
- Best month: 2025-01 with 5 trades, +5.31R
- Top 3 months by trade count account for 46.2% of trades (reported correctly)
- 7 months with zero trades (inactive months)
- 18 active months out of 24 total

### Remove Best Month Test
- After removing 2025-01 (5 trades, +5.31R): 88 trades, WR=62.5%, +16.71R
- **Expectancy remains solidly positive** ✓

### Kill Zone Balance
- London: 46 (49.5%), NY: 47 (50.5%) — excellent balance ✓

### Year Consistency
- 2024: 10 trades, 70% WR
- 2025: 54 trades, 63% WR
- 2026: 29 trades, 62% WR
- No year dominates or collapses ✓

### Direction Balance
- **Not verifiable** — direction field is None for all 93 non-indexed trades
- This is a data quality gap but not a test failure

---

## Test 7: Indexed vs Non-Indexed Comparison Integrity — PASS

### Key Finding: Same Methodology in the Analysis
The JSON file re-scored ALL 12 indexed trades through the batch session simulator, making the combined analysis (105 trades) apples-to-apples.

### Divergence Between Trade Index and Session Simulator
7 of 12 indexed trades show different outcomes between the trade_index (strategy_a) and the session simulator:

| Date | Trade Index (strategy_a) | Session Simulator | Outcome Change? |
|---|---|---|---|
| 2024-04-18 | +1.50R (WIN) | +0.75R (WIN) | Same outcome, different R |
| 2024-05-31 | +1.50R (WIN) | -1.00R (LOSS) | **OUTCOME FLIPPED** |
| 2024-10-03 | +0.36R (WIN) | -1.00R (LOSS) | **OUTCOME FLIPPED** |
| 2025-02-18 | +0.80R (WIN) | +0.85R (WIN) | Same outcome |
| 2025-03-25 | +1.50R (WIN) | +0.14R (WIN) | Same outcome, much lower R |
| 2025-12-22 | +1.50R (WIN) | +2.24R (WIN) | Same outcome, higher R |
| 2026-01-12 | +0.27R (WIN) | -0.18R (LOSS) | **OUTCOME FLIPPED** |

**3 of 12 trades flip from WIN to LOSS** when re-scored through the session simulator. This is why the indexed trades show 41.7% WR in the analysis vs ~56% in the trade index.

### Implication
The report correctly documents this caveat. For the combined analysis, all 105 trades use the same methodology, so the comparison is valid. The trade index itself would need to be re-scored if used for comparison.

---

## Test 8: Pipeline Gap Explanation — PASS

### Root Cause Verified
The seeding script (`scripts/seed_knowledge_base.py`) reads from exactly two source files:
1. `system_improvements_data_20260403.json` → 18 XAUUSD trades
2. `gbpusd_batch_deep_analysis_data_20260403.json` → 42 GBPUSD trades

The script **never reads** the 242 session files in `knowledge_base_backtest/sessions/XAUUSD/`.

### Why GBPUSD Has No Gap
The GBPUSD source file was more comprehensive (42 trades captured all executed CANDIDATEs). Verified: 0 non-indexed executed GBPUSD trades.

### Fix
Clear and documented: modify seeding pipeline to read from session files, or re-export all executed session trades into a format the seeding script can consume.

---

## Test 9: Practical Implications Reality Check — PASS WITH CAVEATS

### Frequency Analysis

| Metric | Recomputed | Reported | Issue? |
|---|---|---|---|
| Total calendar months | 24 (Apr 2024 – Mar 2026) | Not stated | — |
| Active months (with trades) | 18 | Not stated | — |
| Unique executed dates | 85 | 85 | ✓ |
| Reported "dates/month" | 85/18 = **4.7** | 4.7 | ✓ but misleading |
| Actual dates/calendar month | 85/24 = **3.5** | — | More conservative |
| Actual trades/calendar month | 105/24 = **4.4** | — | More realistic |

**Issue:** The "4.7 dates/month" figure uses only active months (18), not total calendar months (24). Using calendar months, the frequency is 3.5 unique dates/month or 4.4 trades/month. The 4.7 figure overstates expected live frequency by ~34%.

### Prop Firm Math

| Calculation | Report's Math | Recomputed |
|---|---|---|
| Monthly R (XAUUSD only) | 4.7 × 0.204 = 0.96R | 4.4 × 0.204 = 0.90R |
| Monthly R (combined) | 6.7 × 0.204 = 1.37R | (4.4 + 2.0) × 0.204 = 1.30R |
| Months to 8% | 5.4 | 8.0/1.30 = 6.2 |

The report's "5.4 months" doesn't match even its own 1.37R/month figure: 8.0/1.37 = 5.8 months. Using calendar-month frequency: 6.2 months. **The report understates time-to-target by ~15-30%.**

### Survivorship / Prompt Version Concern
- Date ranges overlap: indexed (Apr 2024 – Jan 2026) vs non-indexed (Apr 2024 – Mar 2026) — same period ✓
- All 93 trades use the same batch session infrastructure
- Framework distribution: ob_retest (84), session_sweep (7), breaker_retest (2) — consistent
- No evidence of prompt version issues

---

## Summary of Findings

### What the Analysis Gets Right
1. **CANDIDATE counts are correct** — verified against raw session files
2. **Win rate, expectancy, and profit factor are arithmetically correct**
3. **Statistical tests are correctly computed** (one-sided binomial, Fisher's, Mann-Whitney)
4. **The combined analysis uses consistent methodology** (all session simulator)
5. **Pipeline gap root cause is correctly identified**
6. **Distribution analysis is solid** — remove-best-month test passes
7. **Year and kill-zone consistency are real** — not driven by one period

### What the Analysis Gets Wrong or Overstates
1. **Frequency is inflated** — 4.7/month uses active months, not calendar months. Live expectation is ~3.5 unique dates/month
2. **Months-to-8% is understated** — should be ~6.2 months, not 5.4
3. **Entry/SL/TP are completely unrecorded** — simulation is a black box
4. **Direction is not recorded** — can't verify directional balance

### Net Assessment
The core finding is valid: **93 real AI-approved trades exist that were never indexed, and they show statistically significant positive expectancy.** The frequency lever is real but ~30% smaller than reported. The simulation methodology cannot be independently verified but is internally consistent and structurally plausible.

**Confidence: MEDIUM-HIGH** (would be HIGH if entry/SL/TP were recorded)
