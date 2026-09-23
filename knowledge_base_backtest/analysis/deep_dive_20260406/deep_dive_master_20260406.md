# Deep Dive Master Findings Report — 2026-04-06

## Executive Summary

129 trades analyzed (105 XAUUSD, 24 GBPUSD). 62.0% win rate, mean R=+0.278, profit factor 2.17. The edge is REAL and STABLE across 2+ years of data. Half-Kelly suggests 9.91% risk (aggressive); optimal prop-firm risk is 0.75-1.0%.

---

## TIER 1: CONFIRMED FINDINGS (Bonferroni-surviving, validated, immediately actionable)

### F1. `align` score predicts displacement continuation
- **p=0.0**, effect=0.141, n=7496
- The `align` alignment score is the strongest single predictor of cont_3h in the displacement DB
- Also the #1 distinguisher of revisit success vs failure (p=2e-06)
- **Action**: Elevate `align` in the analyzer prompt scoring

### F2. `creates_fvg` predicts continuation
- **p=0.0**, effect=0.111, n=7496
- Displacements that create a Fair Value Gap continue at 11pp higher rate
- **Action**: Add FVG creation as a positive signal in displacement evaluation

### F3. `at_ob` predicts continuation
- **p=1.1e-05**, effect=0.056, n=7496
- Also #2 revisit distinguisher (p=5e-06)
- **Action**: Weight at_ob flag in OB retest scoring

### F4. `ct` (counter-trend) flag matters
- **p=0.000472**, effect=0.052, n=7496
- Counter-trend displacements have ~5pp lower continuation
- **Action**: Downweight counter-trend setups in confidence scoring

### F5. FVG Fill 80-100% is the sweet spot
- 80-100% fill: 71.4% continuation (n=168) — EXACT MATCH with comprehensive analysis
- Below 50% fill: ~20-28% continuation
- Monotonic relationship confirmed: deeper fill = better continuation up to 100%
- Over 100% fill: 63.6% (n=1025) — still strong but degraded vs 80-100%
- **Action**: Implement FVG fill depth filter — prefer 80-100% fills

### F6. Impulse candle count predicts OB quality
- **r=-0.31, p=0.0** — fewer impulse candles = stronger OB
- Single-candle impulse OBs are the strongest
- **NEW FINDING** — not in any prior analysis
- impulse_atr_multiple (p=0.97) and body_ratio_avg (p=0.12) are NOT significant
- **Action**: Prefer OBs formed by sharp, single-candle displacements

### F7. Retracement depth matters for OBs (chi-sq p=0.0001)
- 50-70% retracement: 22.2% continuation (n=9, LOW N)
- 70-80%: 54.3% (n=35)
- 80-85%: 63.4% (n=101)
- 85-90%: 78.7% (n=202) ← PEAK
- 90-95%: 74.4% (n=328)
- 95-100%: 75.4% (n=130)
- Median split (91.4%) NOT significant (p=0.13), but bins ARE (p=0.0001)
- Key insight: the relationship is NOT linear — it rises sharply from 50% to 85%, then plateaus
- Practical threshold: 80%+ retracement (encompassing 85%+ of OBs) is the actionable filter
- The dead OTE binary zone (62-79%) was testing the WRONG range — most OBs are 80%+

---

## TIER 2: SUGGESTIVE (p < 0.01 or practically important, but not Bonferroni-confirmed)

### F8. `fvg_pct` predicts continuation
- p=3e-06, effect=0.086 — survives Bonferroni technically
- But: may be correlated with `creates_fvg` — measuring the same underlying feature

### F9. `direction` matters for continuation
- p=0.0, effect=0.086 — bullish vs bearish displacement
- Not directly actionable (the system already trades in the displacement direction)

### F10. `origin_revisited` strongly predicts continuation
- p=0.0, effect=0.541 — SEMI-OUTCOME (tautological with cont_3h)
- ⚠️ Cannot use as a predictor — it occurs within the same measurement window
- Only useful for understanding the mechanism: price revisiting the origin IS the continuation

### F11. FVG adds 67% more trading opportunities
- FVG-only KZ dates: 179 vs OB-only: 67 vs Both: 200
- FVG Fill framework would increase trade frequency by ~67%
- Strong recommendation to implement FVG Fill framework

### F12. Trending regime favors the system
- Trending: 64.4% WR, mean R=+0.253 (n=87)
- Ranging: 44.4% WR, mean R=-0.034 (n=18)
- Fisher p=0.18 — NOT significant, but the direction is concerning
- n=18 for ranging is too small for conclusions

---

## TIER 3: NULL FINDINGS (Confirmed dead — no effect)

### N1. H4 alignment is DEAD
- h4_dir × cont_3h: **p=0.764** — completely null
- h4_aligned_d1: also null
- H4 when D1 unclear: still null
- **Action**: Do NOT elevate H4 above D1 in the prompt. H4 adds nothing.

### N2. D1 alignment is DEAD (confirmed)
- d1_dir × cont_3h: p=0.93 (prior) — still null on 7496 records

### N3. OTE zone is DEAD (confirmed again)
- in_ote × cont_3h: p=0.61 on 7496 records
- **Action**: Remove OTE zone preference from prompt

### N4. All 10 "untested promising features" are NULL
- strength, levels_swept, liq_depth, mss, m15_aligned, kz_min, crosses_rn, exhaust, first_kz: ALL p > 0.05
- Only `align` (already confirmed) showed significance
- The 95-field screen killed every feature not in Tier 1

### N5. h16-h17 NOT different from h13-h15
- Fisher p=0.52
- **Action**: Do NOT extend NY KZ to 17:00

### N6. BE stop HURTS at every trigger level
- Every trigger from 0.5R to 1.5R results in net negative R per trade
- 0.5R trigger: saves 11 losers but stops 19 winners → net -0.195R/trade
- **Action**: Do NOT implement breakeven stop

### N7. DOW effect not significant
- Best: Tuesday (75.8% WR), Worst: Wednesday (53.9%)
- Fisher p=0.10 — NOT significant
- **Action**: No DOW-based filters

### N8. No regime is significantly different
- All regime tests p > 0.05 (volatility p=0.80, trend p=0.18, range p=0.67)
- Trending DIRECTION suggests better performance but n=18 for ranging is insufficient

### N9. FVG size does NOT predict continuation
- p=0.57 — completely null

### N10. impulse_atr_multiple does NOT predict OB quality
- p=0.97 — completely null
- It's the NUMBER of candles, not the SIZE of the impulse

---

## TIER 4: BLOCKED (Couldn't test — data still needed)

### B1. Calendar event impact on trades
- Calendar only covers 2026-04 to 2026-05 (31 events)
- Cannot retroactively tag historical trades (2024-03 to 2026-03)
- Need MQL5 calendar export from Windows for full date range

### B2. GBPUSD displacement feature screen
- No GBPUSD displacement database exists
- GBPUSD M15 only has 700 rows (2026 only)
- Need Windows re-download of GBPUSD candles

### B3. GBPUSD FVG gap investigation
- GBPUSD per-record FVG: only 18 records → insufficient for analysis
- The 17pp gap (XAUUSD 55.9% vs GBPUSD 38.9%) cannot be properly investigated

### B4. Lasso feature redundancy
- Only 59 XAUUSD trades linked to displacement DB (46 unlinked)
- Too few for reliable multivariate analysis
- Need better trade-displacement linking or more trades

---

## Monte Carlo Executive Summary

### Prop Firm Pass Probability (Combined 129 trades, 10K simulations, 100 trades each)

| Risk % | P(+8% before -5%) | P(+8% before -10%) | P(DD>5%) | Median Final | 95th pct Consec Loss |
|--------|-------------------|-------------------|----------|-------------|---------------------|
| 0.50% | 57.0% | 73.6% | 26.6% | $114,400 | 6 |
| 0.75% | 72.3% | 87.1% | 47.9% | $122,000 | 6 |
| **1.00%** | **81.4%** | **93.5%** | **65.5%** | **$130,400** | **6** |
| 1.25% | 85.3% | 95.0% | 78.2% | $139,800 | 6 |
| 1.50% | 86.7% | 94.7% | 86.2% | $149,800 | 6 |
| 2.00% | 85.7% | 91.1% | 93.8% | $171,800 | 6 |

### Recommended Risk Levels
- **Conservative deployment**: 0.75% (72% prop firm pass, 48% chance of exceeding 5% DD)
- **Standard deployment**: 1.0% (81% prop firm pass, but 66% chance of hitting 5% DD at some point)
- **Kelly half**: 9.91% (WAY too aggressive for prop firm — only for personal account)

### Time to First Payout
- At 1.0% risk, median trades to reach +3%: ~20 trades
- At 5.2 trades/month average: ~4 months to first payout

### Block Bootstrap (autocorrelation check)
- i.i.d. bootstrap: 81.4% pass rate
- Block bootstrap (block=5): 80.8% pass rate
- Difference: -0.6pp → NO autocorrelation detected

---

## Edge Stability Verdict

The edge is REAL. 129 trades over 2+ years with 62.0% win rate, +0.278 mean R, and 2.17 profit factor. Rolling 20-trade windows show only 9/110 with negative expectancy. First half (67.2% WR) is slightly stronger than second half (58.5% WR) — a 9pp decay that needs monitoring. The longest dry spell was 106 days. Autocorrelation is absent (runs test p=1.0). The max drawdown at 1% risk is 5.89% — tight against the 5% prop firm limit. The system generates ~5.2 trades/month, which means a 100-trade evaluation would take ~19 months.

**Honest assessment**: The edge is real and non-trivial, but the 5% DD limit is a genuine risk at 1.0% position size. At 0.75%, the system is safer but slower. The first-half vs second-half decay (67.2% → 58.5%) warrants monitoring — if WR drops below 55% in the next 30 trades, the edge may be eroding.

---

## BE Stop Recommendation

**DO NOT IMPLEMENT.** At every trigger level tested (0.5R through 1.5R), moving to breakeven is net negative. The system's winners need room to run — MFE peaks at candle 12 (3 hours), meaning winners accelerate late. BE stops cut winners at a higher rate than they save losers.

---

## Framework Expansion Priorities (Updated)

1. **FVG Fill (HIGH priority)**: 67% more trading dates, 55.9% overall continuation, 71.4% at 80-100% fill depth. Implement with fill depth filter (80-100% preferred).
2. **H4 OB Retest**: NOT supported. H4 alignment is dead (p=0.76).
3. **Session Sweep Reversal**: No new data. Still blocked.
4. **NY KZ Extension to 17:00**: NOT supported (p=0.52).

---

## What's Still Unknown

1. Calendar event impact (need historical calendar data)
2. GBPUSD feature screen (need displacement DB and M15 candles)
3. True multivariate feature importance (need more linked trade-displacement data)
4. Why WR decayed from 67% to 59% in the second half
5. Whether `align` score can be computed/used in real-time trading
6. Optimal FVG Fill implementation parameters beyond fill depth
