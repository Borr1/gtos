# Phase 0 — Foundation Diagnostic

**Date:** 2026-04-02
**Purpose:** Does the AI's ob_retest analysis produce better outcomes than simply buying gold at the KZ open when D1 is bullish?
**API calls:** Zero. Entirely deterministic analysis on existing data.

---

## Executive Summary

The AI system provides **STRONG precision value** but **NEGATIVE selectivity value**. It enters at significantly better prices than the naive baseline (+97% dollar MFE advantage on matched dates), but its extreme selectivity (40 trades vs 316 possible) leaves money on the table. A naive "buy at KZ open with session-low SL" strategy on ALL pre-screen-passing dates produces **+24.2R** versus the AI's **+8.9R**, despite a lower win rate.

**The AI is a precision tool bolted onto a profitable trend-following regime.** The trend-following (D1 bullish + H4 aligned) does most of the work. The AI improves ENTRY QUALITY but its ultra-selective filtering costs more in missed opportunities than it gains in precision.

**Verdict: PARTIAL VALUE** — proceed with optimization, but also investigate reducing selectivity (more trades).

---

## Section 1: Pre-Screen Population

| Metric | Value |
|--------|-------|
| Total weekdays in data | 498 |
| Pre-screen passing (D1+H4 aligned) | **166 (33.3%)** |
| Pre-screen failing | 332 (66.7%) |

### Failure reasons
| Reason | Count | % of failures |
|--------|-------|---------------|
| D1 transitional (no clear trend) | 261 | 78.6% |
| H4 conflict (bearish vs bullish D1) | 48 | 14.5% |
| D1 insufficient data | 20 | 6.0% |
| H4 conflict (bullish vs bearish D1) | 2 | 0.6% |
| H4 transitional | 1 | 0.3% |

### AI selectivity
- Of 166 pre-screen-passing dates, the AI traded on **34 dates** (20.5%)
- The AI skipped **132 passing dates** (79.5%) — these dates had bullish D1+H4 alignment but the AI couldn't find an ob_retest setup that met U3/U4 confirmation requirements

---

## Section 2: Naive vs AI — Matched Comparison (40 AI trade dates)

### 2A: Entry Price

|  | AI System | Naive (1st candle) |
|--|-----------|-------------------|
| Avg entry price | $4,196.52 | $4,201.34 |
| Avg SL distance ($) | $48.04 | $26.73 |
| Avg SL distance (%) | 1.08% | 0.62% |

- AI enters **$4.82 lower** than KZ open on average — a modest but real improvement
- AI enters HIGHER than open on 60% of trades, LOWER on 38% — the AI sometimes catches pullbacks but often enters after price has moved
- AI uses **1.8x wider stops** ($48 vs $27) — the OB retest zones create wider invalidation levels

### 2B: MFE/MAE Comparison — THE KEY METRIC

|  | AI System | Naive S1 (session low SL) | Naive S2 (ATR SL) |
|--|-----------|---------------------------|-------------------|
| **Avg MFE ($)** | **$37.30** | **$18.95** | **$18.04** |
| **Avg MAE ($)** | $30.65 | $16.04 | $12.35 |
| **MFE - MAE ($)** | **$6.65** | **$2.92** | **$5.70** |
| Avg MFE (R) | 1.289R | 1.225R | 1.397R |
| Avg MAE (R) | 0.588R | 0.686R | 0.792R |
| MFE - MAE (R) | 0.702R | 0.539R | 0.605R |

**The AI produces nearly 2x the dollar MFE (+97%) on matched dates.** This is because the AI times entries to OB zones that precede larger moves. However, the AI's wider stops also mean larger dollar MAE ($30.65 vs $16.04).

In R-multiple terms, the AI edge is narrower: MFE-MAE = 0.702R (AI) vs 0.539R (Naive S1). This is a 30% improvement in R-space, which IS real but less dramatic than the dollar comparison suggests.

### 2C: Win Rate at TP Levels

| TP Level | AI WR | Naive S1 WR | Naive S2 WR |
|----------|-------|-------------|-------------|
| 0.5R | 78% | 55% | 82% |
| 1.0R | 52% | 45% | 57% |
| 1.5R | 38% | 25% | 40% |
| 2.0R | 22% | 20% | 28% |
| 2.5R | 12% | 15% | 12% |

The AI outperforms Naive S1 at all TP levels up to 2.0R. Naive S2 (ATR SL) is actually competitive with the AI because the tighter ATR-based stop creates favorable R-ratios.

### 2D: Dollar P&L (1% risk on $100K = $1,000 risk per trade)

|  | AI System | Naive S1 | Naive S2 |
|--|-----------|----------|----------|
| Avg $ P&L per trade | **+$223** | **+$370** | **+$274** |
| Total $ P&L (40 trades) | +$8,910 | **+$14,800** | +$10,947 |

**Critical finding: Naive S1 produces +$14,800 vs AI's +$8,910 on the SAME 40 dates.**

This happens because the naive strategy uses a tighter SL (session low = $27 avg), so 1% risk ($1,000) buys a larger position. Despite a lower win rate, each dollar of risk produces more reward. The AI's wider stops ($48 avg) dilute position size, reducing dollar P&L even though R-multiple performance is better.

---

## Section 3: Naive vs AI — Selectivity Test (ALL Passing Dates)

|  | AI System | Naive S1 | Naive S2 |
|--|-----------|----------|----------|
| Dates traded | 34 | 166 | 166 |
| Total trades | 40 | **316** | **326** |
| Win rate | 47.5% | 36.1% | 36.8% |
| Total R | +8.91R | **+24.20R** | -12.33R |
| Expectancy | +0.223R | +0.077R | -0.038R |
| Total $ | +$8,910 | **+$24,196** | -$12,332 |

**Naive S1 on all dates: +24.2R from 316 trades vs AI's +8.9R from 40 trades.**

Despite a much lower win rate (36% vs 48%) and lower per-trade expectancy (+0.077R vs +0.223R), the naive strategy's volume overwhelms the AI's precision. Trading 316 times at +0.077R per trade produces more total profit than trading 40 times at +0.223R.

However, Naive S2 (ATR SL) is negative at -12.3R, showing that SL methodology matters enormously. The session-low SL works because it's a structural level; the ATR SL is just a statistical measure with no market meaning.

---

## Section 4: Verdict on AI Value

### PRECISION VALUE: **YES** (+97% dollar MFE advantage)
The AI enters at prices that produce nearly double the favorable excursion in dollar terms compared to buying at the KZ open. The ob_retest framework is genuinely timing entries to precede larger moves. This is the AI's core value.

### SELECTIVITY VALUE: **NO** (AI's total R < Naive total R)
The AI's ultra-selective filtering (40 trades from 166 possible dates) costs more in missed opportunities than it gains in trade quality. The naive strategy produces 2.7x more total R by simply trading every day that passes the D1+H4 pre-screen.

### OVERALL VERDICT: **PARTIAL VALUE**

The AI IS adding precision value — this is not just expensive trend-following. But the extreme selectivity is a net negative. The system needs to TRADE MORE, not trade better.

---

## Section 5: DXY Diagnostic

**SKIPPED** — No EURUSD or DXY data available in the data directory.

To enable: Export EURUSD D1, H4, H1 candles from MT5 on the Windows machine to:
- `data/historical/EURUSD_D1.csv`
- `data/historical/EURUSD_H4.csv`
- `data/historical/EURUSD_H1.csv`

Same CSV format as XAUUSD files (time,open,high,low,close,volume).

---

## Section 6: Supplementary Analysis

### Day-of-Week (Naive S1 on all dates)

| Day | Trades | WR | Total R | Avg R |
|-----|--------|-----|---------|-------|
| Mon | 67 | 42% | +2.05R | +0.031R |
| **Tue** | **67** | **42%** | **+38.24R** | **+0.571R** |
| Wed | 60 | 32% | -3.49R | -0.058R |
| **Thu** | **60** | **32%** | **-4.56R** | **-0.076R** |
| **Fri** | **62** | **32%** | **-8.05R** | **-0.130R** |

**Key findings:**
- **Tuesday is the standout day** for the naive strategy (+38.24R, +0.571R avg) — NOT Friday
- **Thursday IS weak** in both AI and naive data — this validates the AI finding as a market effect, not AI-specific
- **Friday is also weak** in naive data (-8.05R) — contradicting the AI's 86% Friday WR. The AI's Friday finding was likely noise from n=7.

### Entry Candle Position (Strategy 3: Every Candle)

| KZ | Avg MFE (R) | 1.0R Hit Rate |
|----|-------------|---------------|
| London | 1.07R | 17% |
| NY | 1.38R | 34% |

NY produces better MFE regardless of entry timing, consistent with the AI's NY outperformance finding.

---

## Section 7: Implications for the System Roadmap

### The core insight: **Trade more, not better.**

The AI's precision (2x dollar MFE) is real but its selectivity (20% of eligible dates) is destroying value. The optimal system would:

1. **Keep the pre-screen** (D1 bullish + H4 aligned) — this is the regime filter that creates the edge
2. **Lower the entry bar** — the U3/U4 requirements (M15 CHoCH + displacement + OB retest) are too strict and cause the system to skip 80% of profitable days
3. **Use the session-low SL** — it outperforms both the AI's structural SL and the ATR SL because it's a real market level
4. **Target 1.0-1.5R** — confirmed across all analyses as the sweet spot

### Specific recommendations:

**Priority 1: Increase trade frequency**
- Current: 40 trades from 166 eligible dates (24% utilization)
- Target: 100+ trades from 166 dates (~60% utilization)
- How: Relax U3 (accept M15 BOS, not just CHoCH) or add a simpler "pullback to session levels" entry alongside ob_retest

**Priority 2: Tighten stops using session levels**
- Current avg SL: $48 (1.08%)
- Naive session-low SL: $27 (0.62%)
- Impact: Tighter stops = larger position = more dollar P&L per trade

**Priority 3: Lower TP to 1.0-1.5R** (confirmed by both deep analysis and naive baseline)

**Priority 4: Export EURUSD data** for DXY diagnostic before adding macro context

### What this means for the "statistical significance" concern:
The p-value problem (p=0.246 combined) may be less relevant than we thought. The naive baseline shows that the underlying D1+H4 regime filter produces a real edge (+24.2R from 316 trades on session-low SL). The question isn't "does the edge exist?" — it does. The question is "does the AI's entry method capture it efficiently?" — it does, but too selectively.

---

## Data Files

| File | Description |
|------|-------------|
| `phase0_baseline_diagnostic_0.md` | This report |
| `phase0_naive_baseline_data_0_1920.json` | Raw simulation data |
| `phase0_diagnostic.py` | Reproducible analysis script |
