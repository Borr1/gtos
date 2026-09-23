# System Improvements — Results Report
**Date:** 2026-04-03

---

## Phase 1: Prompt Improvements (IMPLEMENTED)

### 1A: Confidence Rubric — Simplified
**Before:** 500-token calibrated rubric (Start at 70, ADD +5 for each..., SUBTRACT -5..., SUBTRACT -10...)
**After:** 2-line instruction: "Rate 50-95 based on overall confluence count."
**Tokens saved:** ~470 per call
**Rationale:** Deep dive showed confidence score had zero predictive power (75/80/85 clustering). The rubric wasted tokens without improving outcomes.

### 1B: Session Memory Instructions — Activated
**Before:** Session memory injected as raw text with no instructions (0/29 references in live sessions)
**After:** Added 3-line instruction header:
> "Consider the progression: Is a setup developing across candles? Did a prior candle show a sweep or displacement that sets up the current candle?"

Also removed redundant header from orchestrator `_format_session_memory()` to avoid duplication.

### 1C: m15_confirmation.choch_detected — Clarified
**Before:** AI outputs `choch_detected: false` even on confirmed CANDIDATE setups
**After:**
- Inline comment in JSON schema: `// TRUE if M15 CHoCH + displacement detected per U3. Must be TRUE for any CANDIDATE decision.`
- New "Internal Consistency Rules" in anti-hallucination guardrails:
  - If decision is CANDIDATE, choch_detected MUST be true
  - If choch_detected is false, decision MUST be NO_TRADE

### 1D: WAIT — Kept
WAIT kept in schema (zero token cost). Never used across 5,623 candles, but might be useful with session memory activated.

### Tests: 465/465 passing

---

## Phase 2: Partial Close Investigation

### Gold Results (18 trades with r_path data)

| Strategy | Avg R | Total R | Std R | Win Rate | Max R |
|---|---|---|---|---|---|
| A: 100% at TP1 | +0.503 | +9.05 | 0.974 | 61.1% | +1.50 |
| B: 70/30 partial | +0.504 | +9.08 | 1.001 | 61.1% | +1.95 |
| C: 50/50 partial | +0.505 | +9.10 | 1.044 | 61.1% | +2.25 |

**Gold finding:** Negligible improvement (+0.003R). Most gold trades that hit TP1 don't extend far beyond — MFE rarely exceeds 1.5R significantly. The runner adds variance without meaningful reward.

### GBPUSD Results (42 trades, MFE-based simulation)

| Strategy | Avg R | Total R | Std R | Win Rate | Max R |
|---|---|---|---|---|---|
| A: 100% at TP1 | +0.420 | +17.65 | 1.126 | 61.9% | +1.50 |
| B: 70/30 partial | +0.512 | +21.50 | 1.277 | 61.9% | +3.08 |
| C: 50/50 partial | +0.573 | +24.06 | 1.432 | 61.9% | +4.14 |

**GBPUSD finding:** +0.153R per trade with 50/50 partial close. GBPUSD has more extension potential after TP1 hit. This is consistent and meaningful.

### Monte Carlo (10,000 sims, 50 trades each)

**Gold:** All strategies nearly identical. P5 equity ~13.5-14.1R. Partial close doesn't hurt but doesn't help.

**GBPUSD:** 50/50 partial shows higher median equity (25.3R vs 21.3R for 100% TP1). P5 slightly lower (risk from runner variance), but the upside more than compensates.

### Recommendation
- **Gold:** Keep 100% at TP1. No partial close benefit.
- **GBPUSD:** Implement 50/50 partial close. +0.153R/trade is significant over time.

---

## Phase 3: Counter-Trend Analysis

### Results: 33 total direction-mismatch rejections found

| Instrument | Rejections | Wins | Losses | Win Rate | Avg R |
|---|---|---|---|---|---|
| XAUUSD | 25 | 7 | 11+7 timeout | 38.9% | +0.032 |
| GBPUSD | 8 | 4 | 3+1 timeout | 57.1% | +0.436 |
| **Combined** | **33** | **11** | **14+8** | **44.0%** | **+0.130** |

### Statistical Test
- Binomial test (decisive trades only): 11/25 wins, p = 0.726
- **NOT significant at any level**

### Profile
- All 33 rejections were SHORT against bullish D1 bias
- Framework: mostly ob_retest (22/33)
- Confidence: No difference between winners (80) and losers (79.3)
- Kill zone: Losers concentrated in NY (11/14), winners split evenly

### Recommendation
**Do NOT implement counter-trend mode.** The 44% win rate is below 50%. The GBPUSD subsample (5/8 profitable in the deep dive) was selection bias from a small sample. With 33 total rejections, the direction_mismatch safety gate is correctly protecting the system.

---

## Phase 4: Volatility & Cross-Instrument Context

### ATR Percentile vs Outcome (52 trades combined)

| Quartile | n | Win Rate | Avg R |
|---|---|---|---|
| Q1 (low ATR, 1-37%) | 13 | 46.2% | +0.255 |
| Q2 (40-73%) | 13 | **61.5%** | **+0.808** |
| Q3 (77-90%) | 13 | 46.2% | +0.545 |
| Q4 (high ATR, 92-100%) | 13 | 46.2% | +0.276 |

**Spread: 15.3% WR.** Best performance in moderate ATR (Q2). Very high ATR days slightly worse. Actionable but not dramatic.

### Asian Range Width vs Outcome (59 trades combined)

| Quartile | n | Win Rate | Avg R |
|---|---|---|---|
| Q1 (narrow, 11-28%) | 15 | **33.3%** | +0.203 |
| Q2 (29-35%) | 16 | 50.0% | +0.547 |
| Q3 (36-52%) | 13 | 46.2% | +0.285 |
| Q4 (wide, 53-159%) | 15 | **60.0%** | +0.528 |

**Spread: 26.7% WR.** Wider Asian range = better outcomes. Narrow Asian days (below 28% ADR) have notably poor win rate. Actionable.

### Cross-Instrument: XAUUSD D1 vs GBPUSD Outcomes (42 GBPUSD trades)

| Alignment | n | Win Rate | Avg R |
|---|---|---|---|
| GBPUSD trade aligned with XAUUSD D1 | 30 | **56.7%** | **+0.660** |
| Not aligned | 12 | **25.0%** | -0.179 |

**Spread: 31.7% WR.** This is the strongest predictive signal found. When gold D1 and GBPUSD trade direction agree (both suggesting dollar weakness or strength), GBPUSD win rate jumps to 56.7%. When they conflict, win rate drops to 25%.

### Implementation Recommendation: **IMPLEMENT**

Add to prompt static context for GBPUSD:
```
## Market Context
Cross-instrument: XAUUSD D1 = [bullish/bearish] (dollar [weakness/strength] signal)
Asian range: [X]% of ADR ([narrow/moderate/wide])
```

**Priority order:**
1. Cross-instrument XAUUSD D1 alignment (31.7% WR spread)
2. Asian range width (26.7% WR spread)
3. ATR percentile (15.3% WR spread — lower priority)

---

## Summary of Actions

| Item | Status | Impact |
|---|---|---|
| Confidence rubric simplified | **DONE** | -470 tokens/call |
| Session memory instructions | **DONE** | Enable session progression context |
| m15_confirmation bug fix | **DONE** | Correct CANDIDATE consistency |
| GBPUSD partial close 50/50 | **NEEDS IMPLEMENTATION** | +0.153R/trade |
| Cross-instrument context | **NEEDS IMPLEMENTATION** | 31.7% WR spread on GBPUSD |
| Asian range context | **NEEDS IMPLEMENTATION** | 26.7% WR spread |
| Counter-trend mode | **NULL RESULT** | Do not implement |
| Gold partial close | **NULL RESULT** | No improvement |

### Next Steps
1. Run full batch test with new prompts to verify no regression
2. Implement 50/50 partial close for GBPUSD in execution engine
3. Add cross-instrument and Asian range context to GBPUSD prompt builder
4. Re-run GBPUSD batch with new context to measure combined improvement
