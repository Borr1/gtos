# KB: Validation & Monitoring Framework — Statistical Evaluation of the Trading System

**Version:** 1.0 | **Date:** 2026-04-05 | **Status:** Final Synthesis  
**Sources:** 6 research sessions + 1 Claude Code empirical analysis + 1 red team review  
**Purpose:** Complete statistical framework for batch evaluation, live monitoring, and kill/confirm decisions. Searchable by `project_knowledge_search`.

---

## 1. How Much to Trust Current Batch Results

### 1.1 What Was Tested and How

The system was batch-tested across 4 instruments using the same prompt on the same date range (Oct 2025 – Mar 2026 for gold, same period for others). Approximately 5 prompt versions were tested on gold before the final version was selected. Six instruments were initially screened; four passed (WR > breakeven), one held as observer, one killed.

**Multiple testing exposure:**
- **Prompt selection (gold):** ~5 versions on same data. Effective independent trials ≈ 1.8 (due to high correlation — versions share identical structural detection, pipeline, and execution rules; only interpretation differs). Bonferroni-adjusted α = 0.05/1.8 ≈ 0.028.
- **Instrument selection:** 6 tested, 4 kept. This is a filter, not optimization — but selection bias exists.
- **Total conceivable tests:** ~30 (5 prompts × 6 instruments). Most conservative Bonferroni correction uses N=30.

### 1.2 Statistical Significance After All Corrections

**Gold (XAUUSD) — Primary Instrument:**

| Test | Raw p-value | Bonferroni (30 tests) | Significant? |
|---|---|---|---|
| WR vs breakeven (35.7%) | **1.14e-09** | **3.42e-08** | **YES** |
| WR vs 50% | **0.004** | **0.12** | NO (marginal) |
| Expectancy vs 0 | 0.046 | 1.38 | NO |

The gold WR edge survives even the most aggressive multiple testing correction. The expectancy edge does NOT survive Bonferroni. **Interpretation:** We are confident the system wins more often than it loses against breakeven. We are less confident about the exact magnitude of profit per trade. [HIGH confidence for existence of edge; MEDIUM for magnitude]

**Other Instruments:**

| Instrument | k/n | H0 (breakeven WR) | Raw p-value | Bonferroni (6) | Survives? |
|---|---|---|---|---|---|
| XAUUSD | 80/129 | 35.7% | 1.14e-09 | 6.85e-09 | **YES** |
| US30 | 24/41 | 34.5% | 1.39e-03 | 8.34e-03 | **YES** |
| USDJPY | 25/33 | 40.0% | 3.27e-05 | 1.96e-04 | **YES** |
| GBPJPY | 24/42 | 41.7% | 3.10e-02 | 0.186 | **NO** |

**GBPJPY fails family-wise correction.** It is the weakest instrument — shortest leash, earliest kill trigger. [HIGH confidence]

### 1.3 Wilson Score 95% Confidence Intervals

These are the true bounds on win rate, accounting for sample size:

| Instrument | Observed WR | n | 95% CI Lower | 95% CI Upper | Breakeven WR | Margin above BE |
|---|---|---|---|---|---|---|
| XAUUSD | 62.0% | 129 | **53.4%** | 69.9% | 35.7% | +17.7pp |
| US30 | 58.5% | 41 | **43.3%** | 72.2% | 34.5% | +8.8pp |
| USDJPY | 75.8% | 33 | **59.0%** | 87.2% | 40.0% | +19.0pp |
| GBPJPY | 57.1% | 42 | **42.2%** | 70.8% | 41.7% | **+0.5pp** |

All CI lower bounds exceed breakeven. GBPJPY's margin is razor-thin (+0.5pp) — any additional live friction or slight WR degradation pushes it below breakeven. [HIGH confidence]

### 1.4 Selection Bias Assessment

If all 6 instruments had TRUE breakeven WR and we kept the best 4, the expected apparent WR of the kept instruments would be only 55.1%. Our observed mean across kept instruments is ~63.4%. The probability of the null producing ≥63.4% is approximately 5.1%. Combined with gold's individual significance (p=1.14e-09), selection bias alone cannot explain the results. Selection bias would inflate observed WR by ~6-8pp at most; our observed WRs exceed breakeven by 9-28pp. [HIGH confidence]

### 1.5 Deflated Sharpe Ratio Check

López de Prado's Deflated Sharpe Ratio accounts for testing multiple strategies. With N=5 prompt versions and T=129 trades:
- Observed Sharpe (in R-multiples) ≈ 0.232
- Expected max SR under null with N=5 ≈ 0.158
- Observed exceeds null maximum, but margin is thin.

**Net assessment:** The edge exists. The magnitude has wider uncertainty bands than the existence. [HIGH confidence for existence; MEDIUM for size]

---

## 2. SPRT Decision Tables — Use From Trade 1

The Sequential Probability Ratio Test (SPRT) provides mechanical confirm/kill/continue boundaries at every trade count. These replace emotional judgment with pre-calculated protocols.

### 2.1 XAUUSD (H0: 35.7% breakeven, H1: 62.0% batch WR)

| Cumulative Trades | Wins to CONFIRM | Wins to KILL | Continue Range |
|---|---|---|---|
| 10 | ≥ 8 | ≤ 3 | 4–7 |
| 15 | ≥ 10 | ≤ 5 | 6–9 |
| 20 | ≥ 13 | ≤ 8 | 9–12 |
| **25** | **≥ 15** | **≤ 10** | **11–14** |
| 30 | ≥ 18 | ≤ 13 | 14–17 |
| 40 | ≥ 23 | ≤ 18 | 19–22 |
| 50 | ≥ 27 | ≤ 22 | 23–26 |

### 2.2 Portfolio Level (H0: 37.7%, H1: 62.8%, ~14.5 trades/month)

| Cumulative Trades | Wins to CONFIRM | Wins to KILL | Continue Range |
|---|---|---|---|
| 10 | ≥ 8 | ≤ 3 | 4–7 |
| 15 | ≥ 11 | ≤ 6 | 7–10 |
| 20 | ≥ 13 | ≤ 8 | 9–12 |
| 30 | ≥ 18 | ≤ 13 | 14–17 |
| 50 | ≥ 28 | ≤ 23 | 24–27 |

### 2.3 GBPJPY (H0: 41.7%, H1: 57.1%) — Widest Continue Range, Hardest to Resolve

| Cumulative Trades | Wins to CONFIRM | Wins to KILL | Continue Range |
|---|---|---|---|
| 10 | ≥ 10 | ≤ 2 | 3–9 |
| 20 | ≥ 15 | ≤ 7 | 8–14 |
| 30 | ≥ 20 | ≤ 12 | 13–19 |
| 50 | ≥ 30 | ≤ 22 | 23–29 |

**GBPJPY requires the most trades to resolve** because its observed WR is closest to its breakeven WR. At portfolio level, ~20 trades should start showing signal. [HIGH confidence — computed directly from SPRT formulas]

### 2.4 SPRT Formula Reference

After each trade, update cumulative log-likelihood:
- After win: Λ = log(p₁ / p₀) where p₁ = alternative WR, p₀ = null (breakeven) WR
- After loss: Λ = log((1-p₁) / (1-p₀))
- Cumulative: S_n = Σ Λ_i
- CONFIRM if S_n ≥ log((1-β)/α) ≈ 2.773 (at α=0.05, β=0.20)
- KILL if S_n ≤ log(β/(1-α)) ≈ -1.556

---

## 3. Power Analysis — How Long Things Take

### 3.1 Trades Needed to Detect Edge at Various True WRs (Gold)

| True WR | Trades Needed (80% power) | Months at 4.5/mo |
|---|---|---|
| 62% (batch) | 21 | **5 months** |
| 58% | 30 | 7 months |
| 55% | 40 | 9 months |
| 52% | 56 | 12 months |

Even if the edge degrades to 55%, we would know within 9 months. At batch WR, statistical proof takes 5 months. [HIGH confidence]

### 3.2 Trades Needed to Detect WR Degradation

Detecting a 7pp WR drop (from 62% to 55%) at 80% power requires approximately 307 trades. At 4.5 trades/month gold-only, that is 68 months. At portfolio level (~14.5/month), approximately 21 months. **This is why the CUSUM and SPRT monitoring are essential — waiting for statistical proof of degradation would take too long for practical use.** [HIGH confidence]

---

## 4. Expected Performance Ranges for Live Trading

### 4.1 Degradation Scenarios — Gold Only (4.5 trades/month, 1% risk on $100K)

| Scenario | WR | Exp/trade | Monthly R | Monthly $ | Months to +10% |
|---|---|---|---|---|---|
| Batch holds | 62% | +0.736R | +3.31R | +$3,312 | 3.0 |
| Slight degrad (-4pp) | 58% | +0.624R | +2.81R | +$2,808 | 3.6 |
| Session memory boost (+4pp) | 66% | +0.848R | +3.82R | +$3,816 | 2.6 |
| Significant degrad (-10pp) | 52% | +0.456R | +2.05R | +$2,052 | 4.9 |
| Edge mostly lost (45%) | 45% | +0.260R | +1.17R | +$1,170 | 8.5 |

### 4.2 Full Portfolio (~14.5 trades/month)

| Scenario | Monthly R | Monthly $ | Months to +10% |
|---|---|---|---|
| Batch holds | +9.73R | +$9,731 | 1.0 |
| Slight degrad (-4pp) | +8.19R | +$8,185 | 1.2 |
| Session memory boost (+4pp) | +11.28R | +$11,277 | 0.9 |
| Signif degrad (-10pp) | +5.87R | +$5,866 | 1.7 |

**Even with -10pp degradation across all instruments, the portfolio still generates positive expectancy.** Diversification is the real safety net. Single-instrument gold requires 3+ months even at batch WR. [HIGH confidence for the math; MEDIUM for the degradation scenarios being the right ones to model]

### 4.3 Cold-Start Penalty

The first 10-15 trades per instrument will underperform because session memory starts empty. Session memory approximately doubles expectancy (from ~+0.22R to ~+0.66R per trade based on earlier validation). Until the memory window fills (~6 evaluations), expect performance at or below the memoryless batch baseline. This is NOT edge decay — it is a known startup cost. [MEDIUM confidence — session memory effect validated but mechanism uncertain]

### 4.4 Sources of Live Friction (Not Present in Batch)

- **Spread variability:** Batch used fixed spread assumptions; live spreads vary, especially around data releases
- **Slippage:** Real market orders may execute 1-3 pips from target
- **Timing precision:** Batch evaluates at candle close; live system has execution latency
- **Market regime changes:** Batch data is from a specific bull market period; live conditions may differ

Expected net impact: -0.05R to -0.15R per trade from friction, partially or fully offset by +0.15R to +0.30R from session memory. Net effect is uncertain but likely positive. [MEDIUM confidence]

---

## 5. Live Monitoring Protocol

### 5.1 After Every Trade

| Check | What to Log | Red Flag |
|---|---|---|
| Execution quality | Actual fill vs target, spread at entry | Slippage > 3 pips or spread > $0.50 |
| Position sizing | Actual lot size vs intended | Any deviation > 5% |
| SL/TP placement | Actual vs system-calculated | Any deviation |
| SPRT update | Update cumulative Λ, check boundaries | Kill boundary approached |
| Reasoning quality | Read AI evaluation text | Gibberish, contradictions, or pure narrative without data reference |

### 5.2 Daily Review

| Check | What to Compute | Red Flag |
|---|---|---|
| Trade count | How many trades taken today | > 2 per instrument per day is suspicious (max 1 per KZ rule) |
| Kill zone compliance | Were trades inside KZ boundaries? | Any trade outside KZ |
| NO_TRADE reasons | Sample 2-3 rejections | AI rejecting everything (over-conservative) or nothing (under-selective) |

### 5.3 Weekly Review

| Metric | Compute | Action Threshold |
|---|---|---|
| Rolling WR | Per instrument, last 10 trades | If < 45% for any instrument, heighten monitoring |
| SPRT cumulative | Check all instruments against decision tables | Kill boundary → halt that instrument |
| Equity curve | Plot cumulative R | Check for sustained drawdown |
| Trade frequency | Trades per week | < 2 portfolio trades/week for 2+ weeks → investigate pre-screen |
| Reasoning quality | Read 2-3 AI reasoning outputs | Degraded reasoning → flag for prompt review (but don't change yet) |

### 5.4 Monthly Review

| Metric | Compute | Action |
|---|---|---|
| 30-trade rolling WR | Per instrument | Compare to batch baseline |
| Equity curve | Plot cumulative R | Check for drift, sustained drawdown |
| CUSUM | Update deterioration/improvement trackers | Signal if threshold breached |
| Session memory effect | Compare first-eval vs later-eval performance | Quantify memory contribution |
| LONG vs SHORT | Separate direction performance | Track toward 21-trade SHORT validation |
| Correlation exposure | Max daily exposure across correlated instruments | Should never exceed 2% total risk |
| System cost | API + infrastructure | Should be < $50/month |

### 5.5 Quarterly Review (Critical)

| Metric | Purpose | Context |
|---|---|---|
| Sub-period WR comparison | Detect temporal decay | The batch showed 73.2% → 71.4% → 63.6% → 59.4% quarterly WR. This 9pp/quarter decay trend must be tracked. 307 trades needed to confirm significance, but the trend warrants active monitoring. |
| H1 autocorrelation | Monitor underlying momentum structure | If 20-period H1 return autocorrelation trends toward zero, expect edge decay regardless of OB-specific statistics |
| Walk-forward window completion | Assess prompt stability | No prompt changes during 3-month windows. Evaluate and modify only at window boundaries |

---

## 6. Emergency Stop Conditions

### Immediate Halt (Stop ALL Trading, Investigate Before Resuming)

1. Portfolio drawdown exceeds 4% of account (approaching FTMO 5% daily limit)
2. Any single trade loses > 1.5R (indicates SL or position sizing bug)
3. More than 2 trades placed in a single kill zone (max 1 per KZ rule)
4. Trade placed outside kill zones
5. MT5 shows different position than system logs
6. Total correlation-adjusted risk exceeds 2% simultaneously

### Instrument-Specific Halt

1. SPRT crosses kill boundary for that instrument
2. 5 consecutive losses on a single instrument
3. Spread consistently exceeds $1.00 during kill zones (liquidity regime change)

---

## 7. Walk-Forward Discipline

### 7.1 Current Evidence Level

| Level | Status |
|---|---|
| Batch validated (positive expectancy on historical data) | ✅ 4 instruments |
| Cross-validated (same prompt across instruments) | ✅ 4/6 passed |
| Walk-forward validated (positive expectancy on unseen data) | ❌ Starts April 7, 2026 |
| Live validated (real execution conditions) | ❌ Starts April 7, 2026 |
| Regime-robust (bull, bear, and range conditions) | ⚠️ Bull only (insufficient SHORT data) |
| Statistically confirmed per instrument (SPRT confirm) | ❌ Requires 10-30 live trades each |

### 7.2 Walk-Forward Protocol

| Window | Prompt Dev Period | Test Period (Hands-Off) | Min Trades in Test |
|---|---|---|---|
| WF-1 | Oct 2025 – Mar 2026 | Apr – Jun 2026 | 15 per instrument |
| WF-2 | Oct 2025 – Jun 2026 | Jul – Sep 2026 | 15 per instrument |
| WF-3 | Oct 2025 – Sep 2026 | Oct – Dec 2026 | 15 per instrument |

**Critical rule:** During each test window, NO prompt changes. Log anomalies, flag concerns, but do not modify. After the window closes, analyze results, make changes if needed, begin the next window. At ~14.5 trades/month portfolio, a 3-month window yields ~44 trades. This is the minimum for meaningful walk-forward evaluation. [HIGH confidence — this is standard methodology]

### 7.3 First-Week Protocol (April 7-11, 2026)

**Monday April 7:**
- Monitor London KZ (3 PM local, 07:00 UTC) — first real evaluation
- Monitor NY KZ (9 PM local, 13:00 UTC) — second evaluation window
- Log everything: every candle evaluation, every CANDIDATE, every NO_TRADE reason
- DO NOT INTERVENE unless emergency stop conditions are met

**Tuesday-Friday:**
- Continue monitoring with reduced intensity (check after each KZ, not during)
- Log actual spreads vs spread gate
- By Friday: expect 3-8 total trades across all instruments

**End of Week 1 Assessment:**
- 0 trades: check pre-screen — market may be in low-conviction regime
- 1-3 trades: too few for statistics. Note results, continue.
- 4-8 trades: compute preliminary WR, update SPRT. If portfolio WR > 50%, strong start.
- > 8 trades: formal SPRT update.

**Standing rule for all of Week 1:** NO PROMPT CHANGES. NO PARAMETER CHANGES. The only acceptable intervention is fixing bugs that prevent the system from functioning (crashes, data errors, execution failures).

---

## 8. When to Deploy Capital (Funded Account)

### Prerequisites (ALL Must Be Met)

1. Portfolio SPRT has not crossed kill boundary after 30+ trades
2. No single instrument killed by SPRT
3. Maximum drawdown has not exceeded 3% on demo
4. No emergency stops triggered
5. System running ≥ 4 weeks without manual intervention
6. WR across all instruments ≥ 50%

**Recommended earliest funded deployment:** May 5, 2026 (4 weeks of live data)

**Recommended initial funded risk:** 0.75% per trade (not 1.0%) until SPRT confirms edge for at least 2 instruments. Scale to 1.0% after confirmation. [MEDIUM confidence — conservative approach appropriate given transition from batch to live]

---

## 9. Regime Change Detection

### 9.1 CUSUM (Cumulative Sum Control Chart)

Track cumulative deviation from expected performance:
- S_t = max(0, S_{t-1} + (expected - actual) - allowance)
- Signal when S_t exceeds threshold
- For the deterioration tracker: expected = batch WR, actual = live result, allowance = small tolerance
- The improvement tracker runs symmetrically to detect when performance exceeds expectations

CUSUM detects gradual shifts faster than simple WR monitoring because it accumulates small deviations over time. [HIGH confidence — standard quality control methodology]

### 9.2 Autocorrelation Monitoring

Track rolling 20-period H1 return autocorrelation for gold. If this metric trends toward zero, momentum in gold at the H1 timescale is decaying. This is the earliest warning signal for edge decay — it will show before OB continuation rates degrade, because the OB retest mechanism depends on underlying momentum persistence. [MEDIUM confidence — theoretically grounded but not yet validated as a leading indicator for this specific system]

### 9.3 Sub-Period Consistency

The batch showed quarterly WR of 73.2% → 71.4% → 63.6% → 59.4%. This 9pp/quarter decay is the primary forward concern. Three possibilities: genuine edge decay, regime change, or sampling noise. The p-value for the first-half vs second-half split (67.2% vs 58.5%) is 0.307 — not significant. At current sample sizes, we cannot distinguish between these explanations. Live data will resolve this within 12-18 months. [MEDIUM confidence — trend is real but cause is unknown]

---

## 10. Key Numbers Quick Reference

| Parameter | Value | Source |
|---|---|---|
| Gold batch WR | 62.0% | 129 trades, Oct 2025-Mar 2026 |
| Gold breakeven WR | 35.7% | 1.0R avg loss / (1.0R + 1.8R avg win) |
| Gold Wilson 95% CI | [53.4%, 69.9%] | n=129 |
| Gold Bonferroni-corrected p (30 tests) | 3.42e-08 | Still highly significant |
| Portfolio batch WR | ~60% | 238 trades, 4 instruments |
| SPRT confirm boundary | S_n ≥ 2.773 | log(16), α=0.05, β=0.20 |
| SPRT kill boundary | S_n ≤ -1.556 | log(0.211) |
| Min walk-forward window | 3 months | ~44 portfolio trades |
| Trades to detect 7pp WR drop | ~307 | 80% power |
| Session memory boost | ~2x expectancy | +0.22R → +0.66R/trade |
| Conservative planning WR | 59% | Per conservative estimate |
| Conservative planning expectancy | +0.154R/trade | Per conservative estimate |
| Earliest funded deployment | May 5, 2026 | 4 weeks live data |
| GBPJPY CI margin above breakeven | +0.5pp | Razor-thin — shortest leash |
| Prompt-neutral test cost | ~$5-10 | 30 re-evaluations |
| SHORT validation sample needed | 21 trades | ~10-21 months at current frequency |

---

## 11. Key Formulas Reference

### Wilson Score Interval
```
p̂_center = (p̂ + z²/2n) / (1 + z²/n)
margin = z × √(p̂(1-p̂)/n + z²/4n²) / (1 + z²/n)
CI = [p̂_center - margin, p̂_center + margin]
z = 1.96 for 95% CI
```

### Breakeven Win Rate
```
WR_be = avg_loser / (avg_loser + avg_winner)
```

### Expectancy
```
E = (WR × avg_winner) - ((1-WR) × avg_loser)
```

---

*End of Document 2. Approximately 5,200 words.*
