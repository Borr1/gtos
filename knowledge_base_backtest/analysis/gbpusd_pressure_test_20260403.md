# GBPUSD Deep Analysis — Pressure Test Results
**Date:** 2026-04-03
**Purpose:** Verify every number from the deep analysis before reporting

---

## Summary

```
=== PRESSURE TEST RESULTS ===
Test 1  (Data Integrity):     PASS — 242 gold sessions recovered, 149 GBPUSD separated, content verified different instruments
Test 2  (Scoring Walk):       PASS — Manually walked 2025-12-03: recomputed batch R=+4.143 (matches +4.14), corrected=+1.503 (matches +1.50)
Test 3  (5-Trade Spot Check): PASS — 5/5 matched (TP1_THEN_TIMEOUT x2, SL, SESSION_TIMEOUT, BE)
Test 4  (Direction/Grade):    PASS — 3 trades verified: all LONG, all TP1 > entry (correct for LONG)
Test 5  (Stats Recompute):    PASS — All metrics match within 0.001: mean=+0.420, t=2.419, p=0.0201, CI=[+0.080, +0.761]
Test 6  (SHORT Search):       PASS (with caveat) — 0/42 accepted trades are SHORT; 8 SHORT CANDIDATEs existed but were rejected
Test 7  (Grade Split):        PASS — A+=31 at +0.360, A=11 at +0.591; two-sample t-test p=0.565 (not significant)
Test 8  (CLOSED_BE):          PASS — All 4 BE trades verified: batch 0.75R (partial close) → corrected 1.50R (100% at TP1)
Test 9  (Trade Frequency):    PASS — GBPUSD candidate rate 2.06% discovery / 1.43% validation vs Gold 0.45%
Test 10 (Concentration):      **WARNING** — Edge not significant without best months (p=0.270)

Errors found and fixed: NONE
Warnings: 2 (see below)
```

---

## Detailed Results

### Test 1: Data Integrity — PASS

| Metric | Count | Verified |
|--------|-------|----------|
| Gold sessions (XAUUSD/) | 242 | Matches git HEAD (242) |
| GBPUSD sessions (GBPUSD/) | 149 | All new + overwritten dates present |
| Gold responses (XAUUSD/) | 210 | Restored from git |
| GBPUSD responses (GBPUSD/) | 149 | Separated correctly |

Cross-verification on 2025-03-04: Gold shows protected_swing at 2832.57 (gold price), GBPUSD shows 1.25591 (GBPUSD price). Different instruments confirmed.

No permanent data loss. All gold data recoverable and recovered.

### Test 2: Scoring Walk — PASS

Walked 2025-12-03 candle by candle (the +4.14R trade, biggest batch/corrected discrepancy):

- **Entry**: 1.32356 LONG, SL=1.32185, TP1=1.32613, Risk=0.00171
- **TP1 hit at candle 13** (2025-12-03 10:45:00): High=1.32632 >= TP1=1.32613
- **Batch scorer**: Closed 50% at +1.503R = +0.752R banked. Held 50% runner.
- **Runner at timeout**: Close=1.33516, R on remaining 50% = +3.392R.
- **My recomputed batch R**: +4.143 (batch reported +4.14) — **MATCH**
- **Corrected (100% at TP1)**: +1.503R — **MATCH** with deep analysis +1.50

The code at `backtest_runner.py:253-258` continues tracking after TP1 hit and only closes 50%.

### Test 3: 5-Trade Spot Check — PASS (5/5)

| Date | KZ | Exit | Batch R | My Walk R | Match | Corrected R | Match |
|------|-----|------|---------|-----------|-------|-------------|-------|
| 2025-03-11 | london | TP1_THEN_TIMEOUT | +1.68 | +1.679 | YES | +1.50 | YES |
| 2025-12-10 | london | TP1_THEN_TIMEOUT | +2.90 | +2.901 | YES | +1.50 | YES |
| 2024-03-01 | ny | SL | -1.00 | -1.000 | YES | -1.00 | YES |
| 2025-02-25 | ny | SESSION_TIMEOUT | +0.29 | +0.292 | YES | +0.29 | YES |
| 2024-01-25 | london | BE | +0.75 | +0.750 | YES | +1.50 | YES |

### Test 4: Direction/Grade — PASS

All 3 verified trades: direction=LONG with TP1 > entry (correct for LONG positions).

### Test 5: Statistics Recompute — PASS

| Metric | Deep Analysis | My Recompute | Diff |
|--------|--------------|--------------|------|
| Combined mean R | +0.420 | +0.4202 | 0.0002 |
| Combined t-stat | 2.419 | 2.419 | 0.000 |
| Combined p-value | 0.0201 | 0.0201 | 0.0000 |
| Combined CI | [+0.080, +0.761] | [+0.080, +0.761] | exact |
| Discovery mean R | +0.484 | +0.4842 | 0.0002 |
| Discovery p-value | 0.0196 | 0.0196 | 0.0000 |
| Validation mean R | +0.240 | +0.2400 | 0.0000 |
| Validation p-value | 0.5387 | 0.5387 | 0.0000 |

All within tolerance.

### Test 6: SHORT Search — PASS (with caveat)

**0/42 accepted trades are SHORT.** Confirmed via both trade data extraction and grep of response files.

**However**: 8 SHORT CANDIDATEs exist in response files — the AI DID propose SHORT setups, but they weren't in the final accepted trades. This means the all-LONG outcome is driven by the D1/H4 prescreen passing predominantly bullish alignment periods during the test window (Jan 2024 - Apr 2026), not by an inability to identify SHORT setups.

The 8 rejected SHORT candidates: 2024-02-02, 2024-03-12, 2024-06-05, 2024-07-30, 2025-02-18, 2025-02-20, 2025-02-25, 2025-11-27.

### Test 7: Grade Split — PASS

| Grade | n | WR | Corrected Avg R | Deep Analysis |
|-------|---|-----|----------------|---------------|
| A+ | 31 | 61.3% | +0.360 | +0.360 |
| A | 11 | 63.6% | +0.591 | +0.591 |

Two-sample t-test: t=-0.581, p=0.565 — difference is NOT statistically significant. With n=11 for A grades, this split is meaningless. Cannot conclude whether A outperforms A+ on GBPUSD.

### Test 8: CLOSED_BE — PASS

All 4 CLOSED_BE trades verified:

| Date | Entry | SL | TP1 | Batch R | Corrected R |
|------|-------|-----|-----|---------|-------------|
| 2024-01-25 | 1.27147 | 1.27065 | 1.27270 | +0.75 | +1.50 |
| 2024-01-31 | 1.26826 | 1.26604 | 1.27159 | +0.75 | +1.50 |
| 2025-03-24 | 1.29209 | 1.28979 | 1.29554 | +0.75 | +1.50 |
| 2025-12-01 | 1.32257 | 1.31996 | 1.32649 | +0.75 | +1.50 |

Mechanism: Batch scorer closes 50% at TP1 (+0.75R), moves SL to breakeven, then SL is hit at entry price (0R on remaining 50%). Total batch = +0.75R. Corrected for 100% close at TP1 = +1.50R.

Code: `backtest_runner.py:258` — `current_sl = entry  # SL to breakeven`

### Test 9: Trade Frequency — PASS

| Metric | GBPUSD Discovery | GBPUSD Validation | Gold |
|--------|-----------------|-------------------|------|
| Total candles | 2,140 | 840 | 440 (3 batches) |
| CANDIDATEs | 44 | 12 | 2 |
| Candidate rate | 2.06% | 1.43% | 0.45% |

GBPUSD produces 3-4x more candidates than gold. This aligns with the higher trade rate (28.2% vs ~16.5% of sessions).

Multi-trade sessions: 3 dates had trades in both London and NY KZs (2025-03-04, 2025-03-11, 2025-12-10).

### Test 10: Concentration Risk — **WARNING**

Monthly R breakdown:

| Month | n | Sum R | Set |
|-------|---|-------|-----|
| 2024-01 | 2 | +3.00 | discovery |
| 2024-02 | 1 | +1.50 | discovery |
| 2024-03 | 4 | -3.10 | discovery |
| 2024-05 | 3 | +0.82 | discovery |
| 2024-06 | 1 | -1.00 | discovery |
| 2024-07 | 1 | +1.50 | discovery |
| 2024-09 | 1 | -1.00 | discovery |
| 2025-02 | 3 | +1.57 | discovery |
| **2025-03** | **10** | **+8.05** | **discovery** |
| 2025-04 | 1 | -1.00 | discovery |
| 2025-05 | 1 | +1.50 | discovery |
| 2025-06 | 3 | +3.17 | discovery |
| **2025-12** | **10** | **+3.64** | **validation** |
| 2026-01 | 1 | -1.00 | validation |

**Removing best month from each set:**

| Set | Without Best Month | n | Mean R | p-value | Significant? |
|-----|-------------------|---|--------|---------|-------------|
| Discovery | Without 2025-03 | 21 | +0.331 | 0.187 | NO |
| Validation | Without 2025-12 | 1 | -1.000 | N/A | N/A |
| Combined | Without both | 22 | +0.271 | 0.270 | NO |

**The edge is positive but NOT significant without the two best months.**

---

## Warnings

### WARNING 1: Monthly Concentration
20/42 trades (48%) come from just two months (March 2025 + December 2025). The edge is NOT robust to removing either hot streak. This is a serious concern for deployment readiness.

### WARNING 2: All-LONG Directionality
While 8 SHORT CANDIDATEs were proposed by the AI, none survived to the final trade list. The test window (Jan 2024 - Apr 2026) coincided with a predominantly bullish GBPUSD trend. **The system has NOT been validated on SHORT trades.** Any bearish reversal in GBPUSD could produce untested behavior.

---

## Impact on Deployment Decision

The deep analysis numbers are **verified correct**:
- 42 trades, 61.9% WR, +0.420 corrected avg R, p=0.020

But the pressure test reveals **fragility**:
1. Edge concentrated in 2 months
2. Zero SHORT trade validation
3. Validation set (11 trades) is statistically meaningless (p=0.54)

**Recommendation**: GBPUSD is NOT ready for live demo deployment. Needs:
1. A bearish-period validation batch (to test SHORT trades)
2. Larger sample size (target 60+ trades total)
3. Multiple independent months showing positive R (not concentrated streaks)
