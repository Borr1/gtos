# Vertical Analysis Report: 101 ob_retest Trades

**Generated:** 2026-04-01
**Dataset:** 101 ob_retest trades, April 2024 — March 2026
**Baseline stats:** 64.9% WR, +0.200R expectancy, +23.69R total, p=0.014

---

## 1. Data Discovery Summary

### File Structure
- **Trade records:** `analysis/unified_trades_v2.json` — 111 trades (101 ob_retest + 10 session_sweep)
- **Session logs:** `sessions/YYYY-MM-DD_session.json` — 242 files, contain candle_time per trade
- **AI reasoning:** `batch_api/msgbatch_*_raw_results.json` — 8 files, 4,340 total candle evaluations with full structured reasoning JSON
- **Comprehensive batch:** `msgbatch_01WUZbzFQniomk49SoLRAsPg_raw_results.json` covers entire date range

### Field Availability
| Field | Available | Source |
|-------|-----------|--------|
| outcome (WIN/LOSS) | 101/101 | unified_trades_v2 |
| r_multiple | 101/101 | unified_trades_v2 |
| framework | 101/101 | unified_trades_v2 |
| candle_time (M15 trigger) | 101/101 | session files + batch reconstruction |
| kill_zone | 101/101 | unified_trades_v2 |
| direction (LONG/SHORT) | 101/101 | unified_trades_v2 |
| confidence_score | 101/101 | BROKEN: 95 scored 80, 6 scored 75 |
| setup_grade | 101/101 | unified_trades_v2 (A or A+) |
| displacement_quality | 101/101 | unified_trades_v2 |
| sweep_quality | 101/101 | unified_trades_v2 |
| liquidity_pool_type | 101/101 | unified_trades_v2 |
| Full AI reasoning JSON | 101/101 | raw_results (structured JSON with sub-objects) |
| causing_event_type (BOS/CHoCH) | **NOT AVAILABLE** as a direct field |
| BOS/CHoCH text in reasoning | 101/101 | All mention CHoCH (M15 confirmation); 54 also mention H1 BOS |

### Missing Data Notes
- `causing_event_type` does not exist as a structured field. The H1 structure break type (BOS vs CHoCH) can be partially extracted from reasoning text, but the extraction is imprecise — 54 trades mention H1 BOS explicitly, 47 are ambiguous, 0 are clearly H1 CHoCH only. This makes a clean BOS vs CHoCH split infeasible.
- The reasoning text is structured JSON (not free-form narrative), which means text-mining yields lower-dimensional features than expected. Key sub-objects: `daily_bias`, `h4_alignment`, `h1_setup`, `liquidity_sweep`, `m15_confirmation`, `overall_reasoning`.

---

## 2. Sub-Period Consistency

### Quarterly Breakdown

| Quarter | Trades | Wins | Losses | WR% | Total R | Exp/R | Verdict |
|---------|--------|------|--------|-----|---------|-------|---------|
| Q2-2024 | 3 | 2 | 1 | 66.7% | +1.82R | +0.607R | + |
| Q3-2024 | 5 | 4 | 1 | 80.0% | +1.27R | +0.254R | + |
| Q4-2024 | 2 | 1 | 1 | 50.0% | +0.03R | +0.015R | + |
| Q1-2025 | 28 | 19 | 7 | 67.9% | +6.75R | +0.241R | + |
| Q2-2025 | 14 | 7 | 7 | 50.0% | -0.79R | -0.056R | **-** |
| Q3-2025 | 7 | 6 | 1 | 85.7% | +2.11R | +0.301R | + |
| Q4-2025 | 17 | 14 | 2 | 82.4% | +7.98R | +0.469R | + |
| Q1-2026 | 25 | 17 | 8 | 68.0% | +4.52R | +0.181R | + |

**Positive expectancy quarters: 7/8 (88%)**

The only negative quarter is Q2-2025 (Apr-Jun 2025) at -0.056R — a mild negative, not a blowup. The edge is not concentrated in a few lucky months.

**Caveat:** Q2-2024 (3 trades), Q3-2024 (5 trades), and Q4-2024 (2 trades) have small sample sizes. The system produced very few trades in the first 9 months of the backtest period — likely because the earlier batch runs covered fewer dates or the market didn't present setups. The strong performance from Q1-2025 onward has much better sample sizes.

### Rolling 3-Month Windows

| Window | Trades | WR% | Total R | Exp/R | V |
|--------|--------|-----|---------|-------|---|
| 2024-04 to 2024-06 | 3 | 66.7% | +1.82R | +0.607R | + |
| 2024-05 to 2024-07 | 3 | 100.0% | +2.11R | +0.703R | + |
| 2024-06 to 2024-08 | 4 | 100.0% | +2.27R | +0.568R | + |
| 2024-07 to 2024-09 | 5 | 80.0% | +1.27R | +0.254R | + |
| 2024-08 to 2024-10 | 4 | 50.0% | -0.81R | -0.202R | - |
| 2024-09 to 2024-11 | 3 | 33.3% | -0.97R | -0.323R | - |
| 2024-10 to 2024-12 | 2 | 50.0% | +0.03R | +0.015R | + |
| 2024-11 to 2025-01 | 5 | 80.0% | +5.31R | +1.062R | + |
| 2024-12 to 2025-02 | 18 | 66.7% | +4.39R | +0.244R | + |
| 2025-01 to 2025-03 | 28 | 67.9% | +6.75R | +0.241R | + |
| 2025-02 to 2025-04 | 27 | 59.3% | +0.27R | +0.010R | + |
| 2025-03 to 2025-05 | 17 | 64.7% | +3.87R | +0.228R | + |
| 2025-04 to 2025-06 | 14 | 50.0% | -0.79R | -0.056R | - |
| 2025-05 to 2025-07 | 10 | 60.0% | +0.38R | +0.038R | + |
| 2025-06 to 2025-08 | 7 | 42.9% | -2.30R | -0.329R | - |
| 2025-07 to 2025-09 | 7 | 85.7% | +2.11R | +0.301R | + |
| 2025-08 to 2025-10 | 15 | 93.3% | +6.51R | +0.434R | + |
| 2025-09 to 2025-11 | 15 | 93.3% | +6.51R | +0.434R | + |
| 2025-10 to 2025-12 | 17 | 82.4% | +7.98R | +0.469R | + |
| 2025-11 to 2026-01 | 25 | 68.0% | +6.57R | +0.263R | + |
| 2025-12 to 2026-02 | 31 | 67.7% | +8.72R | +0.281R | + |
| 2026-01 to 2026-03 | 25 | 68.0% | +4.52R | +0.181R | + |

**Positive rolling windows: 18/22 (82%)**

The 4 negative windows cluster around two periods: late 2024 (Sep-Nov, small n) and mid-2025 (Apr-Aug). Neither represents a catastrophic drawdown.

### Trade Count vs Win Rate Correlation

Pearson correlation: **0.044** — essentially zero. The system does NOT trade more in trending months. The edge is not inflated by regime-clustering.

### VERDICT: **DURABLE**

The edge passes the durability test convincingly:
- 7/8 quarters positive (88%), exceeding the 75% threshold
- 18/22 rolling windows positive (82%)
- No correlation between trade frequency and win rate
- The one negative quarter (Q2-2025) was mild at -0.056R per trade, not a collapse
- The edge persists across the high-sample-size recent period (Q1-2025 onward)

---

## 3. BOS vs CHoCH Split

### Availability
`causing_event_type` does not exist as a structured field in the data. Attempted to reconstruct from reasoning text.

### Results
All 101 ob_retest trades reference CHoCH in the M15 confirmation (this is expected — the framework requires M15 CHoCH as entry confirmation). 54 trades also explicitly mention H1 BOS in the reasoning text; 47 do not mention it clearly.

The "unclear" group (47 trades) likely uses BOS too but the text just doesn't spell it out — the ob_retest framework structurally requires an H1 structure break. Since the classification is driven by text presence rather than a structured field, the resulting split is unreliable.

**H1 BOS mentioned (54 trades):** 61.1% WR, +0.096R expectancy
**H1 BOS not mentioned (47 trades):** implied but unclear

### Verdict
**SKIP** — Cannot produce a clean BOS vs CHoCH split. The ob_retest framework inherently uses both (H1 BOS + M15 CHoCH), so the distinction would need to be "H1 BOS-sourced OB" vs "H1 CHoCH-sourced OB", which requires a structured `causing_event_type` field that doesn't exist.

**Recommendation:** If this analysis is desired, add `causing_event_type` as an explicit field in the Primary Analyzer's JSON output schema. It should capture whether the OB that was retested was formed by a BOS or CHoCH event at H1.

---

## 4. Time-Within-Kill-Zone

| Bucket | N | WR% | Total R | Exp/R |
|--------|---|-----|---------|-------|
| London Early (07:00-08:15) | 29 | 65.5% | +3.15R | +0.109R |
| London Late (08:15-09:30) | 29 | **82.8%** | +8.09R | +0.279R |
| NY Early (13:00-14:15) | 25 | 60.0% | +8.64R | **+0.346R** |
| NY Late (14:15-15:30) | 18 | 66.7% | +3.81R | +0.212R |

### Key Finding: London Late is Significantly Better

London early vs late WR difference: **17.2%** (65.5% vs 82.8%) with 29 trades in each group.

This is a meaningful split. London setups that trigger in the 08:15-09:30 window win at 82.8% vs 65.5% for the 07:00-08:15 window. This makes intuitive sense: early London candles may be reacting to the session open volatility, while later candles have had time for structure to develop.

NY shows a smaller 6.7% difference (not meaningful with these sample sizes), though NY Early has the highest raw expectancy (+0.346R) driven by larger winning trades.

### Verdict
**NOTEWORTHY** — London late-KZ (08:15-09:30) substantially outperforms London early-KZ. Not yet actionable as a filter (you'd be cutting 29 trades), but worth monitoring. Could inform position sizing: full size for London late, reduced for London early.

---

## 5. London vs NY Enhanced

### Overall
| Session | N | WR% | Exp/R | Total R |
|---------|---|-----|-------|---------|
| London | 58 | **74.1%** | +0.194R | +11.24R |
| NY | 43 | 62.8% | **+0.290R** | +12.45R |

London wins more often. NY wins bigger when it wins. Total R is nearly identical.

### By Quarter
| Quarter | Lon N | Lon WR | Lon Exp | NY N | NY WR | NY Exp |
|---------|-------|--------|---------|------|-------|--------|
| Q2-2024 | 2 | 50.0% | +0.885R | 1 | 100.0% | +0.050R |
| Q3-2024 | 2 | 100.0% | +0.155R | 3 | 66.7% | +0.320R |
| Q4-2024 | 1 | 100.0% | +0.140R | 1 | 0.0% | -0.110R |
| Q1-2025 | 19 | 73.7% | +0.159R | 9 | 55.6% | +0.414R |
| Q2-2025 | 8 | 62.5% | +0.099R | 6 | 33.3% | -0.263R |
| Q3-2025 | 4 | 75.0% | +0.100R | 3 | 100.0% | +0.570R |
| Q4-2025 | 6 | 83.3% | +0.237R | 11 | 81.8% | +0.596R |
| Q1-2026 | 16 | 75.0% | +0.212R | 9 | 55.6% | +0.126R |

London's WR advantage is consistent — it outperforms NY in 6/8 quarters. NY compensates with larger average wins when conditions align (Q1-2025, Q4-2025).

### By Direction
| Group | N | WR% | Exp/R |
|-------|---|-----|-------|
| London LONG | 55 | 72.7% | +0.195R |
| London SHORT | 2 | 100.0% | +0.070R |
| NY LONG | 40 | 62.5% | +0.306R |
| NY SHORT | 3 | 66.7% | +0.073R |

The system is overwhelmingly LONG-biased (95/101 trades). SHORT sample sizes are too small to draw conclusions (5 total).

### Verdict
London's WR advantage (74.1% vs 62.8%) is real and persistent across quarters. It's not a regime artifact. However, NY's higher expectancy means both sessions contribute meaningful edge. **Do not filter out NY trades** — both sessions are profitable.

---

## 6. Reasoning Text Mining

### Feature Distributions (101 trades)

| Feature | Min | Max | Mean | Median |
|---------|-----|-----|------|--------|
| quality_score | 0 | 4 | 0.8 | 1.0 |
| hesitation_score | 0 | 5 | 1.8 | 2.0 |
| net_confidence | -5 | 3 | -1.0 | -1.0 |
| word_count | 23 | 50 | 34.5 | 34.0 |
| price_level_count | 2 | 15 | 8.3 | 8.0 |
| disp_ratio (M15) | 0 | 8.6 | 1.4 | 1.5 |

Note: Quality scores are low because the reasoning is structured JSON, not free-form narrative. Terms like "strong displacement" appear sparingly. Hesitation terms ("however", "moderate", "only") are more frequent.

### Best Single Feature: price_level_count

**price_level_count >= 8:** 68 trades, **75.0% WR**, +0.370R expectancy
**price_level_count < 8:** 33 trades, **57.6% WR**, -0.044R expectancy
**Delta: +17.4%** with adequate sample sizes (68 vs 33)

This is the strongest predictor found. Trades where the AI cites 8+ distinct price levels win at 75.0% with strong positive expectancy. Trades with fewer than 8 price references are coin-flip negative-expectancy.

**Interpretation:** When the AI grounds its reasoning in more specific price levels, the structural analysis is more thorough and the setup is better-defined. Fewer price references may indicate the AI is working with less clear structure.

### Second Best: hesitation_score

**hesitation_score <= 2:** 71 trades, **73.2% WR**, +0.341R expectancy
**hesitation_score > 2:** 30 trades, **60.0% WR**, -0.018R expectancy
**Delta: +13.2%**

When the AI uses more hedging language (however, moderate, only, unclear, etc.), the setup is less clean and wins less. Low-hesitation trades have strong positive expectancy; high-hesitation trades are break-even.

### COUNTER-INTUITIVE Finding: displacement_quality Inverted

**disp_ratio < 1.6:** 51 trades, **76.5% WR**, +0.491R expectancy
**disp_ratio >= 1.6:** 50 trades, **62.0% WR**, -0.027R expectancy
**Delta: -14.5%**

Higher reported displacement ratios correlate with WORSE outcomes. This is suspicious and may indicate:
1. The AI reports higher displacement in volatile/choppy conditions that also produce more reversals
2. Lower displacement ratios correspond to "quiet" structural moves that are more reliable
3. The displacement ratio calculation may not be working as intended in the backtest

Similarly: **quality_score >= 2** (20 trades, 50.0% WR) performs far WORSE than **quality_score < 2** (81 trades, 74.1% WR). When the AI uses lots of superlatives ("strong", "clean", "decisive"), the trades actually lose more. This may be over-enthusiasm bias.

### Structured Field Analysis

| Field | Value | N | WR% | Exp/R |
|-------|-------|---|-----|-------|
| setup_grade | A+ | 70 | 71.4% | +0.312R |
| setup_grade | A | 31 | 64.5% | +0.060R |
| liq_pool_type | asian_high | 24 | **79.2%** | +0.321R |
| liq_pool_type | none | 45 | 66.7% | +0.338R |
| liq_pool_type | asian_low | 15 | 60.0% | -0.054R |

**Asian high sweeps** (24 trades, 79.2% WR) are the best-performing liquidity pool type with adequate sample size.

### Combination Analysis

No two-feature combination produced a reliably better split than the single features above when requiring 20+ trades per group. The dataset of 101 trades is too small for reliable multi-feature filters.

### Recommended Confidence Proxy

**Primary proxy: price_level_count >= 8**
- 67% of trades qualify (68/101)
- Qualified: 75.0% WR, +0.370R expectancy
- Disqualified: 57.6% WR, -0.044R expectancy
- Delta: 17.4% WR, +0.414R expectancy difference

**Secondary proxy: hesitation_score <= 2**
- 70% of trades qualify (71/101)
- Qualified: 73.2% WR, +0.341R expectancy
- Disqualified: 60.0% WR, -0.018R expectancy

**DO NOT USE as confidence proxies:**
- quality_score (inverted — more quality words = worse outcomes)
- disp_ratio (inverted — higher displacement = worse outcomes)
- net_confidence (poor split)
- displacement_quality structured field (95/101 = "strong", no variance)
- sweep_quality structured field (55 clean vs 45 ambiguous, only 4% WR difference)

---

## 7. Action Items

### Priority 1: Implement Immediately
1. **Add `price_level_count` as a post-hoc confidence metric.** Count distinct price levels (regex `\d{4}\.\d{1,2}`) in the reasoning JSON. Threshold at >= 8. Use for position sizing: full size above threshold, reduced (0.5x) below.

2. **Add `hesitation_count` as a secondary metric.** Count occurrences of: however, although, but, concern, unclear, uncertain, ambiguous, mixed, choppy, ranging, moderate, medium, only, barely, minimal. Threshold at <= 2.

3. **Do NOT use the existing confidence_score** — it's broken (nearly all 80s) and cannot be trusted.

### Priority 2: Add to Primary Analyzer Schema
4. **Add `causing_event_type` field** (BOS or CHoCH) to the Primary Analyzer JSON output. This would enable the BOS vs CHoCH split analysis that was blocked by missing data.

5. **Add `price_level_count` as an explicit output field** rather than relying on regex extraction from text.

### Priority 3: Monitor / Test Forward
6. **London late-KZ advantage** (82.8% WR after 08:15 vs 65.5% before). Monitor this in live trading. If it holds, consider reduced sizing for pre-08:15 London trades.

7. **Asian high sweep advantage** (79.2% WR, 24 trades). This is the best-performing liquidity pool type. Worth tracking as a potential filter, but needs more data.

8. **Investigate inverted displacement ratio.** Why do higher displacement ratios predict worse outcomes? This may reveal a bug in the displacement calculation or a genuine market insight (overextended displacement = overreaction = reversal risk).

### Skip / Do Not Implement
- BOS vs CHoCH filter — data not available in structured form
- Direction-based filter — 95% of trades are LONG, insufficient SHORT data
- Multi-feature combination filters — dataset too small for reliable multi-variable models
- Kill zone filter (drop NY) — NY has lower WR but higher expectancy, both sessions profitable

---

## Appendix: Raw Data Checksums

- 101 ob_retest trades analyzed
- 101/101 matched to candle timestamps
- 101/101 matched to reasoning JSON
- Date range: 2024-04-01 to 2026-03-12
- Total R: +23.69R
- Outcomes: 70 WIN, 28 LOSS, 3 BREAKEVEN
- Win rate: 69.3% (70/101) — higher than the previously reported 64.9% because the earlier analysis may have counted BREAKEVENs as losses or used a different trade set
- Expectancy: +0.235R per trade
