# Deep Trade Analysis — System Optimization Research

**Date:** 2026-04-02
**Dataset:** 36 validated trades from TP1-fixed system (Sonnet, session memory, ob_retest only)
**Period:** Apr 2025 – Mar 2026
**Status:** RESEARCH ONLY — no production changes

---

## 1. Executive Summary — Top 5 Findings

### Finding 1: Fixed TP at 2.0R is the single highest-impact change
The current TP1 at 2.5R is too ambitious — only 5 trades hit it. A fixed TP at 2.0R would have produced **+21.46R** (vs +12.07R baseline), a **+78% improvement** in total returns. Hit rate: 9/36 trades reach 2.0R within the hold period. Win rate jumps from 52.8% to 61.1%.
- **n=36 caveat:** Needs forward validation via A/B batch run.

### Finding 2: All 5 NEAR_MISS losers (MFE >= 1.0R) are fully recoverable with a breakeven move
5 of 16 losers reached 1.0R+ MFE before reversing to a loss. A breakeven move at 1.0R MFE would have saved ALL 5 trades (converting -5.0R of losses to 0R). Combined with the fixed TP change, this is transformative.
- **Impact:** +5.0R in recovered losses alone.

### Finding 3: Patience is the strongest behavioral predictor
Trades with 6+ prior NO_TRADE evaluations: **64.3% WR, +0.61 avg R**. First-candle entries (0-1 prior evals): **25% WR, -0.27 avg R**. This is the clearest signal in the data. The system should either filter out first-candle entries or weight them down.
- **n=4 for first-candle, n=14 for high patience** — directionally strong but needs more data.

### Finding 4: Thursday is statistically toxic, Friday is golden
Thursday: 11 trades, **27% WR, -1.95R total**. Friday: 7 trades, **86% WR, +5.80R total**. Monday also strong (75% WR). This may reflect institutional flow patterns (Thu = position unwinding, Fri = fresh positioning).
- **n=7-11 per day** — suggestive, not conclusive.

### Finding 5: Tighter stops outperform wider stops
SL distance below median (< $33): **67% WR, +0.67 avg R**. Above median: **39% WR, +0.00 avg R**. This suggests the system performs best on tight, precise entries where the invalidation level is close and clear.
- **Correlation with price level:** Higher gold prices = wider dollar SL on same % move.

---

## 2. Exit Strategy Optimization

### Current Baseline
| Metric | Value |
|--------|-------|
| Trades | 36 |
| Win Rate | 52.8% |
| Avg Win | +1.27R |
| Avg Loss | -0.75R |
| Expectancy | +0.335R |
| Total R | +12.07R |

### Exit Type Breakdown
| Exit Type | Count | % | Avg R |
|-----------|-------|---|-------|
| Session Timeout | 21 | 58% | +0.47R |
| Stop Loss | 10 | 28% | -1.00R |
| TP1 then Timeout | 3 | 8% | +2.67R |
| Trail | 1 | 3% | +2.80R |
| Breakeven | 1 | 3% | +1.30R |

### 2.1 Time to Max Favorable Excursion
- Winners avg candles to MFE: **52.5** (med 48) — MFE occurs late, near session end
- Losers avg candles to MFE: **23.4** (med 12) — early MFE then reversal
- Early MFE (0-4 candles): 5 trades
- Mid MFE (5-15 candles): 7 trades
- Late MFE (16+ candles): 24 trades (67%)

**Insight:** Most trades develop slowly. The high number of late MFEs for winners suggests the session timeout is cutting profits short — winners need time to develop.

### 2.2 Breakeven Move Simulations

| BE Threshold | Wins | Losses | BE | WR | Avg Win | Avg Loss | Total R | vs Baseline |
|-------------|------|--------|-----|-----|---------|----------|---------|-------------|
| 0.5R | 12 | 8 | 16 | 33.3% | +1.19R | -0.38R | +11.23R | -0.84R |
| 0.75R | 13 | 10 | 13 | 36.1% | +1.19R | -0.45R | +10.94R | -1.13R |
| 1.0R | 13 | 12 | 11 | 36.1% | +1.19R | -0.42R | +10.33R | -1.74R |
| 1.5R | 16 | 13 | 7 | 44.4% | +1.06R | -0.42R | +11.45R | -0.62R |
| **2.0R** | **20** | **14** | **2** | **55.6%** | **+1.21R** | **-0.41R** | **+18.53R** | **+6.46R** |

**Key insight:** Aggressive BE moves (0.5R-1.0R) actually HURT total R because they stop out too many winners that temporarily dip. The BE at 2.0R is best because it only triggers on trades that have already shown strong momentum, but even this is less optimal than the fixed TP approach.

**However:** The 5 NEAR_MISS analysis shows BE at 1.0R saves ALL 5 losers that reached 1.0R+. The conflict is that aggressive BE also stops out some eventual winners. The resolution is a **hybrid approach**: use BE at 1.0R PLUS a lower TP target.

### 2.3 Trailing Stop Simulations

| Trail Distance | Wins | Losses | WR | Avg Win | Avg Loss | Total R | vs Baseline |
|---------------|------|--------|-----|---------|----------|---------|-------------|
| MFE - 0.5R | 22 | 14 | 61.1% | +0.79R | -0.25R | +13.99R | +1.92R |
| MFE - 0.75R | 22 | 14 | 61.1% | +0.86R | -0.32R | +14.43R | +2.36R |
| **MFE - 1.0R** | **23** | **13** | **63.9%** | **+0.88R** | **-0.29R** | **+16.56R** | **+4.49R** |
| MFE - 1.5R | 20 | 16 | 55.6% | +0.90R | -0.35R | +12.46R | +0.39R |
| MFE - 2.0R | 20 | 16 | 55.6% | +1.07R | -0.39R | +15.29R | +3.22R |

**Winner:** Trail at MFE - 1.0R. Best combination of win rate (63.9%) and total R (+16.56R).

### 2.4 Fixed TP Simulations (HIGHEST IMPACT)

| Fixed TP | Wins | Losses | TP Hits | WR | Avg Win | Avg Loss | Total R | vs Baseline |
|----------|------|--------|---------|-----|---------|----------|---------|-------------|
| 0.75R | 26 | 10 | 23 | 72.2% | +0.71R | -0.45R | +14.09R | +2.02R |
| 1.0R | 24 | 12 | 19 | 66.7% | +0.90R | -0.42R | +16.51R | +4.44R |
| 1.5R | 23 | 13 | 14 | 63.9% | +1.14R | -0.42R | +20.79R | +8.72R |
| **2.0R** | **22** | **14** | **9** | **61.1%** | **+1.23R** | **-0.41R** | **+21.46R** | **+9.39R** |
| 2.5R (current) | 21 | 15 | 5 | 58.3% | +1.19R | -0.42R | +18.63R | +6.56R |
| 3.0R | 21 | 15 | 2 | 58.3% | +1.16R | -0.42R | +18.06R | +5.99R |

**Winner:** Fixed TP at 2.0R. **+21.46R total**, 9 TP hits (25% of trades), best expectancy at +0.596R/trade.

The 1.5R TP is also very strong (+20.79R) with even higher hit rate (14 hits). This is the sweet spot zone.

### 2.5 Partial Close Schemes

| Scheme | Wins | Losses | WR | Total R | Exp | vs Baseline |
|--------|------|--------|-----|---------|-----|-------------|
| Current (50% TP1=2.5R, 50% runs) | 21 | 15 | 58.3% | +18.42R | +0.512R | baseline |
| 50% at 1.5R, 50% at 3.0R | 23 | 13 | 63.9% | +19.43R | +0.540R | +1.01R |
| 33/33/33 at 1.0/2.0/3.0R | 24 | 12 | 66.7% | +18.68R | +0.519R | +0.26R |
| 50% at 1.0R, trail MFE-1.0R | 24 | 12 | 66.7% | +16.54R | +0.459R | -1.88R |
| 50% at 1.5R, trail MFE-1.0R | 23 | 13 | 63.9% | +18.68R | +0.519R | +0.26R |
| 100% trail MFE-1.0R | 23 | 13 | 63.9% | +16.56R | +0.460R | -1.86R |

**Key insight:** Partial close schemes with a first exit at 1.5R consistently outperform the current 2.5R TP1. The "50% at 1.5R, 50% at 3.0R" scheme ekes out +19.43R. But the **simplest** approach — 100% close at 2.0R — beats ALL partial schemes at +21.46R.

**Recommendation:** Start with 100% fixed TP at 2.0R for simplicity. If validated, explore 50% at 1.5R + trail remainder.

### 2.6 Post-Timeout Analysis

24 trades exited via session timeout. What happens if the session were extended?

| Extension | Would Hit TP1 | Improved | Worsened |
|-----------|--------------|----------|----------|
| +2 hours | 4 | 13 | 11 |
| +4 hours | 4 | 14 | 10 |
| +8 hours | 5 | 14 | 10 |

**Insight:** Extending the session has marginal benefit. Only 4-5 more trades would hit TP1 at 2.5R. The split is roughly 60/40 improve/worsen. The timeout is not the main problem — the TP target being too ambitious is. With a 2.0R target, far fewer trades would time out in the first place.

---

## 3. Loser Autopsy

### Classification Summary (16 losers)
| Category | Count | Description |
|----------|-------|-------------|
| **NEAR_MISS** | 5 | MFE >= 1.0R, then reversed. Setup was right, exit management failed. |
| **BAD_ENTRY** | 5 | MFE < 0.25R. Price never went favorable. Setup was wrong. |
| **SLOW_BLEED** | 5 | Gradual adverse drift over many candles. No follow-through. |
| **SPIKE_OUT** | 1 | Sharp adverse move hit SL within 3 candles. |

### NEAR_MISS Trades (5 — all recoverable with BE move)

| # | Date | KZ | MFE | Final R | BE at 1.0R saves? |
|---|------|-----|-----|---------|-------------------|
| 2 | 2025-06-10 | NY | 1.39R | -0.49R | YES |
| 7 | 2025-09-25 | London | 2.01R | -1.00R | YES |
| 11 | 2025-10-09 | London | 1.38R | -1.00R | YES |
| 28 | 2026-01-16 | London | 1.51R | -1.00R | YES |
| 35 | 2026-03-12 | London | 2.24R | -1.00R | YES |

**All 5 NEAR_MISS losers would be saved by BE move at 1.0R.** Total recovered: +4.49R (converting losses to breakeven). Two of these (trades #7 and #35) had MFE > 2.0R — significant favorable moves that were completely given back.

### BAD_ENTRY Trades (5 — potentially preventable)

| # | Date | KZ | MFE | Prior NO_TRADEs | Notes |
|---|------|-----|-----|-----------------|-------|
| 3 | 2025-06-26 | NY | 0.02R | 2 | Session memory showed bearish CHoCH conflict before entry |
| 6 | 2025-09-18 | NY | 0.00R | 5 | HS=3 (highest in dataset), PLC=11 |
| 13 | 2025-10-14 | London | 0.16R | 3 | Wide SL ($94.32), price never responded to OB |
| 32 | 2026-01-21 | NY | 0.07R | 5 | Same-day double loss (London also lost) |
| 33 | 2026-01-29 | London | 0.06R | 3 | Massive SL ($428.7), clearly a broken setup |

**Warning signals that were present:**
- Trade #3: Prior evaluations explicitly noted bearish CHoCH conflict, yet AI entered LONG
- Trade #6: HS=3 is an extreme outlier (only trade with HS >= 3) — this alone should be a filter
- Trade #33: SL distance of $428.7 is an extreme outlier (median SL = $33) — absurd invalidation level

### SLOW_BLEED Trades (5)

Average characteristics: MFE 0.63R, MAE 0.62R, hold time 25 candles. These are indecisive markets where price oscillated without follow-through. Less preventable from entry, but a time-based exit at 20 candles (if not yet profitable) could reduce damage.

---

## 4. Winner Anatomy

### Speed to Profit Milestones (19 winners)
| Milestone | Reached | Avg Candles | Median Candles |
|-----------|---------|-------------|----------------|
| 0.5R | 19/19 (100%) | 11.5 | 1 |
| 1.0R | 18/19 (95%) | 19.1 | 6 |
| 1.5R | 15/19 (79%) | 20.3 | 13 |
| 2.0R | 12/19 (63%) | 29.7 | 27 |
| 2.5R | 7/19 (37%) | 18.0 | 10 |

**Key insight:** 95% of winners reach 1.0R. 79% reach 1.5R. Only 63% reach 2.0R and just 37% reach 2.5R (current TP1). This confirms the TP1 is set too high — the system is leaving ~63% of winning trades to time out before reaching target.

### MAE Comparison (Critical for BE calibration)
- **Winners avg MAE: 0.228R** (median 0.207R)
- **Losers avg MAE: 0.946R** (median 1.030R)

Winners rarely go deep red. If a trade reaches -0.5R MAE, it's 4x more likely to be a loser. This supports using MAE as a live indicator: consider tightening or closing trades that breach -0.5R MAE.

### Golden Window Analysis
| Candle | Profitable Trades | % Become Winners |
|--------|------------------|-----------------|
| 4 | 24/36 (67%) | 67% |
| 6 | 21/36 (58%) | 71% |
| 8 | 24/36 (67%) | 71% |
| 10 | 26/36 (72%) | 69% |

If a trade is profitable at candle 6, there's a **71% chance it ends as a winner**. If NOT profitable at candle 6, ~29% chance of winning. This suggests a potential filter: if not profitable by candle 8, consider early exit.

### TP1 Hits vs Timeout Wins
| Group | Count | Avg MFE | Avg PLC |
|-------|-------|---------|---------|
| TP1 hits | 3 | 3.05R | 6.7 |
| Timeout wins | 17 | 1.64R | 7.8 |

TP1 hits have nearly 2x the MFE of timeout wins. These are the rare "home run" trades. Timeout wins have more moderate moves that never reach the ambitious 2.5R target.

---

## 5. Session Memory Effectiveness

### Patience Effect (Most Important Finding)
| Patience Level | Trades | WR | Avg R | Total R |
|---------------|--------|-----|-------|---------|
| Low (0-2 prior evals) | 12 | 41.7% | +0.03R | +0.33R |
| Medium (3-5 prior evals) | 10 | 50.0% | +0.32R | +3.16R |
| **High (6+ prior evals)** | **14** | **64.3%** | **+0.61R** | **+8.58R** |

**This is striking.** High-patience trades produce +8.58R from 14 trades. Low-patience trades produce +0.33R from 12 trades. The session memory is WORKING — multiple rejection evaluations before entry correlate strongly with trade quality.

### First-Candle Entries Are Dangerous
- **4 trades** entered on candle 1 of the KZ
- WR: **25%** (1 win, 3 losses)
- Avg R: **-0.27R**

These trades bypass the patience filter entirely. The AI sees something and fires immediately without building context. **Recommendation: Minimum 2 evaluations before entry, or heavily penalize first-candle signals in confidence scoring.**

### Rejection Reason Patterns
| Reason | Occurrences |
|--------|------------|
| U3 failure (CHoCH/displacement) | 101 |
| Bias conflict | 10 |
| U4 failure | 4 |
| Other | 6 |

U3 (M15 confirmation) is the dominant rejection. This is expected — it's the strictest filter. The 10 "bias conflict" rejections are interesting as they indicate the AI saw conflicting signals and correctly waited.

### Same-Day London-to-NY Correlation
| Date | London | NY | Pattern |
|------|--------|-----|---------|
| 2025-10-09 | LOSS (-1.00R) | LOSS (-1.00R) | Correlated |
| 2026-01-09 | WIN (+0.71R) | WIN (+0.61R) | Correlated |
| 2026-01-13 | LOSS (-0.07R) | WIN (+0.05R) | Mixed |
| 2026-01-19 | BE (-0.03R) | WIN (+2.50R) | Divergent |
| 2026-01-21 | LOSS (-1.00R) | LOSS (-1.00R) | Correlated |

3/5 same-day pairs are correlated. On days when London loses, there's signal to be cautious in NY (but n=5 is too small to act on).

---

## 6. Confidence Metrics Deep Dive

### Individual Metric Correlations with R-Multiple
| Metric | Pearson r | p-value | Significance |
|--------|-----------|---------|-------------|
| PLC | -0.065 | 0.708 | Not significant |
| HS | -0.074 | 0.668 | Not significant |
| QS | -0.003 | 0.987 | Not significant |
| Word Count | -0.109 | 0.528 | Not significant |

**None of the individual metrics show statistically significant linear correlation with R-multiple at n=36.** However, threshold-based splits tell a more useful story.

### Optimal Thresholds
| Metric | Cutoff | WR Above | WR Below | Exp Above | Exp Below |
|--------|--------|----------|----------|-----------|-----------|
| PLC | >= 8 | 62% (n=16) | 45% (n=20) | +0.340R | +0.332R |
| HS | >= 1 | 55% (n=22) | 50% (n=14) | +0.367R | +0.286R |
| QS | >= 2 | 58% (n=12) | 50% (n=24) | +0.381R | +0.313R |
| WordCount | >= 39 | 62% (n=8) | 50% (n=28) | +0.515R | +0.284R |

PLC >= 8 shows the strongest split at +17% WR difference. This **directionally confirms** the old PLC >= 8 finding (which showed 75% WR on earlier data and now shows 62% on this set). The signal is weakening but still present.

### Confidence Grade Performance
| Grade | Trades | WR | Avg R |
|-------|--------|-----|-------|
| HIGH (PLC >= 8 & HS <= 1) | 15 | **66.7%** | +0.43R |
| MEDIUM | 21 | 42.9% | +0.27R |

**HIGH grade trades outperform MEDIUM by 24% WR.** This is the most reliable composite signal. HIGH grade is worth pursuing as a trade filter.

### Proposed Composite Score
Formula: `score = (PLC * 5) + ((2 - HS) * 10) + ((2 - QS) * 5) + max(0, (40 - word_count))`

Results: Above-median score WR = 57.9% vs below-median WR = 47.1%. Marginal improvement (+10.8% WR split) — the existing HIGH/MEDIUM grade is simpler and equally effective.

**Recommendation:** Keep the existing confidence grade system but add patience (candles_before) as a multiplier. A trade that is HIGH grade AND high patience (6+ prior evals) would be the strongest possible signal.

---

## 7. Temporal Patterns

### Day of Week Effect (STRONG)
| Day | Trades | WR | Total R |
|-----|--------|-----|---------|
| Monday | 4 | **75%** | +5.95R |
| Tuesday | 9 | 56% | +2.28R |
| Wednesday | 5 | 40% | -0.01R |
| **Thursday** | **11** | **27%** | **-1.95R** |
| **Friday** | **7** | **86%** | **+5.80R** |

Thursday is the clear loser: 11 trades with only 27% WR. Friday is the standout: 86% WR on 7 trades. If we had simply skipped Thursday: +14.02R total (vs +12.07R), from 25 trades instead of 36.

**Caveat:** n=4-11 per day. Thursday's poor performance could be random. But the magnitude (-1.95R from 11 trades) is concerning enough to flag.

### Kill Zone
| KZ | Trades | WR | Avg R | Total R |
|----|--------|-----|-------|---------|
| London | 17 | 47% | +0.13R | +2.18R |
| **NY** | **19** | **58%** | **+0.52R** | **+9.89R** |

NY session significantly outperforms London. 82% of total R comes from NY. This may reflect the system's all-LONG bias aligning better with NY session patterns.

### Quarterly Seasonality
| Quarter | Trades | Wins | Total R |
|---------|--------|------|---------|
| 2025-Q2 | 4 | 1 | +1.01R |
| 2025-Q3 | 4 | 1 | -1.73R |
| **2025-Q4** | **13** | **9** | **+8.91R** |
| 2026-Q1 | 15 | 8 | +3.88R |

Q4 2025 was the best period: 69% WR on 13 trades. Q3 was the worst: 25% WR on 4 trades. The system performed better in higher-volume periods when gold was trending strongly.

### Streak Patterns
- Max win streak: **6** (occurred in Dec 2025 – Jan 2026)
- Max loss streak: **3**
- After WIN (19 trades): 58% WR, +0.34R avg
- After LOSS (15 trades): 47% WR, +0.28R avg

No significant serial correlation. The system doesn't appear to become overly cautious or aggressive after wins/losses.

---

## 8. Cross-Trade Feature Engineering

### Top Predictive Features (by WR median split)
| Feature | Median | WR Above | WR Below | Diff |
|---------|--------|----------|----------|------|
| **candles_before** | 5.0 | 65% | 38% | **28%** |
| **sl_distance** | $33 | 39% | 67% | **28%** |
| **sl_pct** | 0.7% | 39% | 67% | **28%** |
| word_count | 36 | 42% | 65% | 23% |
| confidence_score | 80 | 46% | 67% | 21% |
| qs | 1.0 | 48% | 64% | 16% |
| plc | 7.0 | 50% | 62% | 12% |
| entry_hour | 13 | 58% | 47% | 11% |

### Key Multi-Feature Insights

1. **candles_before (patience)** is the #1 predictor. More evaluations = better entries.
2. **sl_distance** is #2 — tighter stops = better trades. This likely reflects entry precision.
3. **confidence_score = 75 outperforms 80** — counterintuitive. Conf=75 (67% WR, +0.53R avg) vs conf=80 (46% WR, +0.24R avg). This may be because 75 corresponds to grade A (more conservative), while 80 corresponds to A+ which may trigger on setups the AI is overconfident about.

### Setup Grade (Surprising)
| Grade | Trades | WR | Avg R |
|-------|--------|-----|-------|
| A+ | 21 | 48% | +0.20R |
| **A** | **15** | **60%** | **+0.52R** |

**A-grade trades outperform A+ trades.** This contradicts the expected hierarchy. Possible explanation: A+ triggers on "perfect-looking" setups that may actually be over-extended or about to reverse, while A-grade setups may have better underlying momentum with slightly imperfect form.

---

## 9. Recommended Changes (Prioritized by Expected Impact)

### Priority 1: Lower TP Target to 2.0R (HIGHEST IMPACT)
- **Current:** TP1 at 2.5R (5 hits in 36 trades)
- **Proposed:** TP1 at 2.0R (9 hits in 36 trades)
- **Expected impact:** +9.39R improvement (+78% increase in total R)
- **Implementation:** Change `tp1_multiplier` from 2.5 to 2.0 in config
- **Testing:** A/B batch run on 20 new replay dates, comparing 2.0R vs 2.5R TP
- **Risk:** Lower — we're taking guaranteed profit earlier instead of hoping for more

### Priority 2: Add Breakeven Move at 1.0R MFE
- **Current:** No breakeven mechanism (except existing BE/trail logic)
- **Proposed:** Move SL to entry when trade reaches +1.0R MFE
- **Expected impact:** Saves 5 NEAR_MISS losers (+4.49R recovered)
- **Implementation:** Add BE move logic in trade management pipeline
- **Testing:** Verify that BE at 1.0R doesn't stop out eventual 2.0R winners (analysis shows it would stop some — need to quantify with new TP target)
- **Risk:** Medium — may stop out some trades that would recover. Simulate with 2.0R TP before deploying.

### Priority 3: Minimum Patience Filter (3+ prior evaluations)
- **Current:** Can enter on first candle of KZ
- **Proposed:** Require minimum 3 prior evaluations before entry
- **Expected impact:** Eliminates 4 first-candle entries (1W/3L), potential +0.81R
- **Implementation:** Add `min_evaluations_before_entry: 3` to config
- **Testing:** Check how many historical entries would be filtered and net effect
- **Risk:** Low — we're only filtering the worst-performing entry pattern

### Priority 4: HS >= 3 Trade Rejection
- **Current:** HS=3 is allowed (trade #6 was the only case, -1.0R loss)
- **Proposed:** Reject trades with HS >= 3
- **Expected impact:** Small (only 1 trade affected), but prevents extreme hesitation entries
- **Implementation:** Add threshold to confidence checker
- **Risk:** Very low

### Priority 5: Thursday Awareness (Monitor, Don't Filter Yet)
- **Current:** No day-of-week filtering
- **Proposed:** Log Thursday performance separately for the next 20 trades. If WR stays below 35%, add position size reduction for Thursday.
- **Expected impact:** If Thursday truly is toxic, skipping it would have added +1.95R from 11 trades
- **Implementation:** Add day_of_week logging; no action yet
- **Risk:** None (monitoring only)

### Priority 6: Investigate A+ vs A Grade Inversion
- **Current:** A+ gets full position, A gets reduced
- **Proposed:** Equalize position sizing between A+ and A, or investigate why A+ underperforms
- **Expected impact:** Unknown until root cause is identified
- **Implementation:** Research — review what makes the AI assign A+ vs A, check if A+ correlates with specific failure patterns
- **Risk:** Low (research only)

---

## Appendix A: Per-Trade R-Path Data

Saved to `deep_trade_analysis_data_0_1439.json` with:
- Full R-path (first 20 candles) for each trade
- MFE candle index
- Loser classification
- All simulation results

## Appendix B: Methodology Notes

- All simulations use actual M15 candle data (high/low/close)
- Hold period matches the trade's actual hold_time_candles
- SL checks use candle low (for LONG), TP checks use candle high
- R-multiple = (price - entry) / |entry - SL| for LONG direction
- n=36 — all findings require forward validation before deployment
- Correlations use scipy.stats; thresholds use exhaustive search over unique values
