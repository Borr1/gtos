# GBPUSD Batch Deep Analysis
**Date:** 2026-04-03
**Batch IDs:** Discovery=msgbatch_01NoUmtxUEP81v71PuNf7s7V, Validation=msgbatch_01GFcnn3BoVnxZs3TseQt4hD

---

## Section 0: Data Integrity Issue (RESOLVED)

### Problem
Session files use `{date}_session.json` naming with no instrument scope. GBPUSD batch overwrote gold session files for overlapping dates.

### Damage
- **60 gold session files overwritten** (GBPUSD data replaced XAUUSD data)
- **60 gold response files overwritten**
- 89 new GBPUSD-only files added (no collision)

### Recovery
- All gold data recovered from `git HEAD` (last commit before GBPUSD batch)
- Gold sessions restored to `knowledge_base_backtest/sessions/XAUUSD/` (242 files)
- GBPUSD sessions saved to `knowledge_base_backtest/sessions/GBPUSD/` (149 files)
- Same treatment for `batch_api/responses/XAUUSD/` and `batch_api/responses/GBPUSD/`

### Fix Applied
`batch_backtest.py` updated: `sessions_dir = output_dir / "sessions" / symbol` (was just `output_dir / "sessions"`). Same for responses directory. Future batches will write to instrument-scoped subdirectories.

---

## Section 1: Scoring Methodology (CRITICAL FINDING)

### How the batch scorer works (`backtest_runner.py:129-321`)

The scorer simulates a **partial close strategy**:

| Event | Action | R contribution |
|-------|--------|---------------|
| TP1 hit | Close 50%, move SL to breakeven | +tp1_r * 0.50 (= +0.75R for 1.5R TP1) |
| TP2 hit | Close 25%, trail SL to TP1 | +tp2_r * 0.25 |
| TP3 hit | Close remaining 25% | +tp3_r * 0.25 |
| SL hit (before TP1) | Close 100% | -1.0R |
| BE hit (after TP1) | Close remaining at entry | 0R on remaining, keep TP1 partial |
| Session timeout | Close remaining at last close | +(close_pnl/risk) * remaining_pct |

### Exit substates explained:

- **CLOSED_SL**: Full stop loss. R = -1.0. SL is checked BEFORE TP on each candle (conservative).
- **CLOSED_BE**: TP1 hit (50% at 0.75R), then SL hit at breakeven (0R on remaining 50%). Total = +0.75R.
- **CLOSED_TP1_THEN_TIMEOUT**: TP1 hit (50% at 0.75R), remaining 50% closed at session end price. If price kept running, remaining 50% adds significant R.
- **CLOSED_SESSION_TIMEOUT**: No TP hit. Closed at session end price. No partial close involved.

### Why batch R-multiples are inflated for Phase 1

Phase 1 deployment uses **100% close at TP1** (not partial close). Any trade that hit TP1 gets exactly +1.5R in Phase 1, but the batch scorer gives them 0.75R + (runner at timeout) which can be much higher when price keeps running after TP1.

Example: 2025-12-03 — batch R = +4.14 (TP1 hit at 1.5R, runner rode to +6.89R MFE). Corrected (100% at TP1) = +1.50R.

---

## Section 2: Corrected R-Multiples

### Correction methodology
- **CLOSED_SL** → R = -1.0 (unchanged)
- **CLOSED_BE** → R = +1.5 (TP1 was hit; with 100% close, we exit at TP1)
- **CLOSED_TP1_THEN_TIMEOUT** → R = +1.5 (TP1 was hit; 100% close at TP1)
- **CLOSED_SESSION_TIMEOUT** → R = batch_R (no TP hit; no partial close involved)

### Corrected statistics

| Metric | Combined | Discovery | Validation |
|--------|----------|-----------|------------|
| n | 42 | 31 | 11 |
| Wins | 26 | 20 | 6 |
| Losses | 16 | 11 | 5 |
| Win Rate | 61.9% | 64.5% | 54.5% |
| **Batch avg R** | **+0.573** | **+0.491** | **+0.804** |
| **Corrected avg R** | **+0.420** | **+0.484** | **+0.240** |
| Corrected total R | +17.65 | +15.01 | +2.64 |
| t-stat | 2.419 | 2.467 | 0.637 |
| **p-value** | **0.020** | **0.020** | **0.539** |
| 95% CI | [+0.080, +0.761] | [+0.099, +0.869] | [-0.499, +0.979] |
| R inflation | +0.153 | +0.007 | +0.564 |

### Key observations:
1. **Discovery corrected avg R = +0.484** — essentially unchanged from batch (+0.491) because most TP1 trades had moderate runner extensions
2. **Validation corrected avg R = +0.240** — significantly deflated from batch (+0.804) because validation had huge runners (2025-12-03: +4.14, 2025-12-22: +3.46)
3. **Combined p-value = 0.020** — still statistically significant at 5% level
4. **Validation p-value = 0.539** — NOT significant (n=11 too small, high variance)

---

## Section 3: Direction and Grade Breakdown

### Direction
**ALL 42 trades are LONG.** Zero short trades. This is concerning — it suggests the AI is biased toward long setups on GBPUSD, or the D1/H4 pre-screen filters primarily passed bullish alignment periods.

### Grade breakdown

| Grade | n | WR | Corrected Avg R | p-value |
|-------|---|--------|----------------|---------|
| A+ | 31 | 61.3% | +0.360 | 0.076 |
| A | 11 | 63.6% | +0.591 | 0.151 |

A grades outperform A+ on corrected R (+0.591 vs +0.360), which is the OPPOSITE of gold. However, n=11 for A grades is too small to draw conclusions.

---

## Section 4: Trade Frequency

| Metric | GBPUSD | Gold (est.) |
|--------|--------|-------------|
| Sessions | 149 | 242 |
| Trade dates | 39 | ~40 |
| Total trades | 42 | 95 |
| Trade rate | 28.2% | ~39.3% |
| Multi-trade sessions | 3 | ~10 |

GBPUSD trade rate (28.2%) is lower than gold (~39.3%). The pre-screen filters may be stricter for GBPUSD, or the AI is more selective.

---

## Section 5: MFE/MAE Analysis

### MFE progression
| Threshold | Count | % of trades |
|-----------|-------|-------------|
| 0.5R | 32 | 76% |
| 1.0R | 23 | 55% |
| 1.5R | 20 | 48% |
| 2.0R | 17 | 40% |
| 3.0R | 12 | 29% |

- **Median MFE: 1.359R** — healthy, close to TP1
- **Mean MFE: 1.893R** — dragged up by runners
- **Median MAE: 0.492R** — concerning; half of trades see 0.5R adverse excursion

### Losing trades (16):
- Median MFE before reversal: 0.429R
- 8/16 (50%) reached 0.5R+ favorable before losing
- This suggests potential for a trail-to-BE strategy BEFORE TP1

### r_path data
r_path is stored in batch results but NOT propagated to session files. Available for future analysis directly from `evaluate_hypothetical_outcome()` return values.

---

## Section 6: Gold Batch Scoring Comparison

### Gold batch scoring
Gold uses the SAME partial-close scorer. However, gold had **zero CLOSED_TP1_THEN_TIMEOUT** outcomes and 29 CLOSED_BE outcomes.

This means gold TP1 (at 2.5R in the old config) was rarely reached, and when it was, the trade typically reverted to breakeven. The gold batch R-multiples are actually **deflated** compared to 100% TP1 close:

| Metric | Gold Batch | Gold Corrected (100% TP1) |
|--------|-----------|--------------------------|
| Avg R | +0.244 | +0.653 |
| Inflation | -0.409 | — |

Gold's batch scoring is the **opposite** of GBPUSD: it UNDERESTIMATES the 100% TP1 close because most gold TP1 hits resulted in BE (0.75R) instead of the full 1.5R they'd get with 100% close.

**NOTE:** Gold Phase 1 TP calibration (+0.503R at 1.5R) was computed via separate r_path simulation, not the batch scorer. The gold Phase 1 numbers are independently validated and unaffected by this scoring issue.

---

## Conclusions and Deployment Decision

### GBPUSD Corrected Numbers (100% TP1 close)
- **42 trades, 61.9% WR, +0.420 avg R, p=0.020**
- Discovery (31): +0.484 avg R, p=0.020
- Validation (11): +0.240 avg R, p=0.539 (not significant)

### Concerns
1. **ALL 42 trades are LONG** — zero directional diversity
2. **Validation is weak** — only 11 trades, 54.5% WR, not statistically significant
3. **High MAE** — median 0.492R means trades routinely come close to SL before winning
4. **50% of losers saw 0.5R+ MFE** — potential early exit opportunities missed

### Recommendation
The corrected numbers are positive but not compelling enough for immediate deployment. The all-LONG issue is a red flag — the system needs to demonstrate it can trade GBPUSD in both directions before going live. Consider:
1. Running a SHORT-biased validation batch (bearish D1 periods)
2. Increasing validation sample to 30+ trades
3. Investigating why MAE is so high (SL placement may need adjustment for GBPUSD volatility)
