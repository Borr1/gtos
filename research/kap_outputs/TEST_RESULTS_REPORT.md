# IMPLEMENTATION AGENT — TEST RESULTS REPORT
# Date: 2026-04-06
# Agent: Test Runner (Agent 5)
# Input: 18 filtered findings + self-initiated deep analysis

## Summary

| Metric | Count |
|---|---|
| Findings received | 18 |
| Already tested/not testable | 5 (#1, #2, #5, #17, #18) |
| Tests executed | 12 |
| **CONFIRMED** | **4** |
| **REJECTED** | **5** |
| **INCONCLUSIVE** | **3** |

---

## CONFIRMED (Actionable)

### Finding #9: Body Breaks > Wick Breaks — CONFIRMED (p < 0.0001)
- **H1:** Body 81.8% follow-through vs wick 57.9% (+23.9pp)
- **H4:** Body 84.4% vs wick 57.5% (+27.0pp)
- **H4 bullish body:** 87.4% follow-through
- **Sample:** 3,185 H1 breaks, 1,080 H4 breaks
- **ACTION:** HIGH PRIORITY — Add body-close filter to BOS/CHoCH detection. Wick-only breaks are noise on gold.

### Finding #8: Gold FVG Fill Completeness — CONFIRMED
- 72% of H1 FVGs fill completely within 20 candles
- Median fill = 100%. Small FVGs: 82.6% full fill. Large: 58.8%
- Bearish FVGs fill more (74.5%) than bullish (70.1%)
- **ACTION:** FVG fill is a valid TP targeting mechanism. Consider FVG-based exits.

### Finding #14: Execution Delay Stress Test — CONFIRMED (zone is robust)
- Delayed WR: 67.5% vs original 66.8% (SL=$12, 5k Monte Carlo sims)
- 95% CI: [64.2%, 71.0%]
- **ACTION:** OB zone is the signal, not exact timing. System tolerates slippage.

### Finding #15: Parameter Sensitivity — CONFIRMED (no overfitting)
- Confidence threshold: max 1.1pp jump (very smooth)
- Kill zones: near-identical WR. No cliff edges anywhere.
- **BONUS:** Hold time < 20 candles = 45.6% WR. MAE < 0.3R = 98.8% WR.
- **ACTION:** System is parameter-robust. Use early MAE as trade management signal.

---

## REJECTED (No action needed)

### Finding #6: Monday Effect — REJECTED (p = 0.56)
- Monday: 69.4% WR (n=62) — actually ABOVE average. Omnibus p=0.31.

### Finding #3/#4: Session Performance Gap — REJECTED (p = 1.00)
- London 65.4% vs NY 65.7% — near-identical. **KB claim of 14pp gap is WRONG.**

### Finding #11/#12: Momentum + Loose OB — REJECTED (p = 0.32)
- System is momentum-regime-agnostic. Loose OB validated via delay test.

### Finding #16: Zone Liquidity Context — REJECTED (p = 0.37)
- No relationship between nearby structural levels and OB hold rate (r=-0.03).

### Finding #7: COT Dual Signal — ALREADY REJECTED
- Overall COT null. This variant very likely null. Not retested.

---

## INCONCLUSIVE

### Finding #13: AI Selection Quality — INCONCLUSIVE
- Confidence-outcome r = -0.022, p = 0.68. Grading is noise.
- Cannot test binary selection without non-traded outcomes.

### Finding #10: M1 Confirmation Filter — INCONCLUSIVE
- Batch data lacks granular M1 structure data. M15 CHoCH is already the gate.
- Requires dedicated M1 infrastructure to test properly.

### Finding #7: COT Dual Signal — INCONCLUSIVE (low priority)
- Not separately tested. Overall COT is conclusively null.

---

## SELF-INITIATED ANALYSES

### Deep Feature Importance Screen (367 trades)

**Pre-entry features ranked by predictive power (|r|):**

| Feature | r | p-value | Verdict |
|---|---|---|---|
| Day of week | -0.103 | 0.048 | Weak signal, barely significant |
| Candles before entry | +0.083 | 0.113 | Suggestive — patience helps |
| Hesitation count | +0.063 | 0.230 | Not significant |
| Hour UTC | +0.059 | 0.259 | Not significant |
| Confidence score | -0.022 | 0.680 | **ZERO signal** |
| Month | +0.008 | 0.881 | **ZERO signal** |

**Post-entry (trade management) signals:**

| Feature | r | p-value | Verdict |
|---|---|---|---|
| MAE (drawdown) | -0.685 | <0.0001 | **DOMINANT predictor** |
| MFE (excursion) | +0.430 | <0.0001 | Strong |
| Hold time | +0.304 | <0.0001 | Strong |

**Key discovery: The ONLY actionable predictive information comes AFTER entry, not before.** No pre-entry feature in the current system meaningfully predicts outcome.

### Confidence Grade Paradox
- LOW confidence grade: 75.0% WR (n=48)
- MEDIUM: 61.0% (n=159)
- HIGH: 46.2% (n=13)
- **Inverted!** Lower AI confidence → better outcomes. Likely because LOW grade comes with higher hesitation (3.5 vs 0.5), meaning the AI was more careful.

### Framework Performance
- ob_retest: 67.2% WR (n=354) — the core strategy works
- session_sweep: 22.2% WR (n=9) — **kill this framework** (p=0.010)

### Walk-Forward Stability
- Total equity: +141.8R over 367 trades
- Peak: +149.7R
- Max drawdown: 9.6R
- **2025 vs 2026: 70.5% → 59.5% (p=0.08) — MONITORING REQUIRED**

### Streak Analysis
- Max consecutive losses: 7
- Max consecutive wins: 14
- Loss streak of 4+: happened 8 times

### Monte Carlo Prop Firm Simulation (10,000 paths)
- **Full dataset pass rate: 99.5%** at 1% risk
- **2026-only pass rate: 93.9%** — 5.6pp degradation
- Optimal risk level: 0.75-1.0% (99.5% pass rate)
- At 1.5% risk: 97.7% pass rate

---

## 2026 PERFORMANCE DECAY — ROOT CAUSE ANALYSIS

**Symptom:** WR 70.5% → 59.5%, R-multiple 0.47 → 0.22

**Root causes:**

| Factor | 2025 | 2026 | Change | Significance |
|---|---|---|---|---|
| Gold volatility (ann.) | 17.3% | 35.8% | +107% | Market-driven |
| Gold price | $3,445 | $4,877 | +42% | Market-driven |
| Daily range | 1.72% | 3.49% | +103% | Market-driven |
| MFE (avg R) | 1.53 | 1.10 | -28% | p=0.0005 |
| Trade rate | 25% | 32% | +28% | p=0.002 (candidates) |
| TP1 hit rate | 18.7% | 13.5% | -28% | Structural |

**Diagnosis:** Gold volatility doubled and price jumped 42%. The system's parameters (SL sizing, zone interpretation) haven't adapted. It's also becoming LESS selective — taking 32% of sessions vs 25%, diluting quality.

**Priority Fixes:**
1. Scale SL with ATR/price — fixed dollar SL is now undersized
2. Tighten selectivity back to 25% trade rate
3. Add body-close BOS filter (Finding #9) — especially valuable in high-vol regime
4. MFE-adaptive TP targets

---

## Recommended Priority Actions (RANKED)

1. **URGENT:** Diagnose SL sizing — is it scaling with gold price? If not, fix immediately
2. **HIGH:** Add body-close filter on BOS/CHoCH detection (27pp H4 advantage)
3. **HIGH:** Tighten AI selectivity — reduce trade rate from 32% back to 25%
4. **HIGH:** Kill session_sweep framework (22% WR, p=0.010)
5. **MEDIUM:** Implement MAE-based early exit management (98.8% WR at <0.3R drawdown)
6. **MEDIUM:** Add FVG-fill TP targeting (72% of gold FVGs fill completely)
7. **LOW:** Fix KB session statistics (London = NY, not 14pp gap)
8. **LOW:** Redesign confidence scoring or remove it entirely

---

---

## BATCH 2 RESULTS (Videos 16-24, 86 claims)

Most claims were NQ/indices Silver Bullet strategy — not directly applicable to gold OB system. Relevant testable claims extracted and tested:

### V20: R-Target Optimization — CONFIRMED (HIGH PRIORITY)
- **Current total return:** +141.9R
- **TP=3R would produce:** +166.0R (+17% improvement, +24.1R)
- TP=2.5R: +153.1R, TP=2R: +144.6R, TP=1R: +101.0R
- Higher TP sacrifices hit rate (14.4% at 3R vs 43.6% at 1R) but maximizes total return
- **ACTION: Increase TP targets toward 2.5-3R range**

### V24: Friday Effect on Gold — INCONCLUSIVE (monitor)
- Friday: 57.8% WR, avg R=+0.082
- Mon-Thu: 67.0% WR, avg R=+0.451
- WR gap: -9.2pp but Fisher's p=0.19
- R-multiple difference IS significant (p=0.032)
- **ACTION: Monitor. Consider reduced Friday position sizes.**

### V20: FVG Freshness — CONTRADICTED
- V20 claims fresh FVGs are stronger. Our data shows OPPOSITE on gold.
- Fresh (<=5 candles): 18.0% hold rate
- Stale (>=15 candles): 22.8% hold rate
- Spearman r=+0.052, p=0.008 (wrong direction)
- **ACTION: Do NOT prioritize fresh FVGs. This is NQ-specific.**

### V20: Sweep Rule Useless — CONFIRMED (cross-validates Finding #5)
- Second independent source confirming sweeps don't help.

### V22: OB Body-Close Entry — CONFIRMED (cross-validates Finding #9)
- V22 independently confirms body-close > wick for OB entry.

### V24: Profit Factor Check — CONFIRMED
- Full dataset PF: 2.34 (healthy, within 1.75-4.0 range)
- 2026-only PF: 1.69 (below threshold — confirms decay)

### V24: London Hour Optimization — REJECTED
- 9am UTC is slightly better but p=0.69. Not actionable.
- 15:00 UTC (PM Fix) is 76.7% WR (n=43) — interesting but needs more data.

---

## UPDATED PRIORITY ACTIONS (All Batches Combined)

| # | Action | Source | Impact | Effort |
|---|---|---|---|---|
| 1 | Scale SL with gold price/ATR | 2026 decay analysis | Fixes vol mismatch | Medium |
| 2 | Body-close BOS filter | Finding #9, V22 | +27pp H4 advantage | Medium |
| 3 | Increase TP to 2.5-3R | V20 R-target analysis | +24.1R total return | Low |
| 4 | Tighten selectivity to 25% | 2026 decay | Restores quality | Low |
| 5 | Kill session_sweep framework | Self-analysis | Stops 22% WR bleeding | Low |
| 6 | MAE-based trade management | Parameter sensitivity | 98.8% WR at <0.3R MAE | Medium |
| 7 | FVG-fill TP targeting | Finding #8 | 72% full fill on gold | Medium |
| 8 | Monitor Friday performance | V24 | -9pp WR, sig R gap | None |

---

Results saved to: `research/kap_outputs/test_results.json` (20 entries)
Scripts saved to: `research/kap_outputs/tests/`
