# Trade Journal — Gold Traders Operating System
## FTMO $100K Demo | Live Start: April 7, 2026

---

# SECTION 1 — PER-TRADE LOG

Copy this block after every trade. One block per trade.

---

### Trade #___

| Field | Value |
|-------|-------|
| Date | |
| Time (UTC) | |
| Instrument | |
| Direction | LONG / SHORT |
| Kill Zone | London / NY / Tokyo |
| Entry Price | |
| SL Price | |
| SL Distance (points) | |
| TP1 / TP2 / TP3 | / / |
| RR at TP1 / TP2 / TP3 | / / |
| Lot Size | |
| Risk % | |
| AI Grade | A+ / A |
| AI Confidence Score | |
| Spread at Entry | |
| Session Memory State | ___ prior evals this session |
| Correlation Adj | No / Yes → ___ |

**Outcome:**

| Field | Value |
|-------|-------|
| Result | Win / Loss / BE / Timeout |
| R-Multiple | |
| Partials Hit | TP1 / TP2 / TP3 |
| Time in Trade | |
| MFE (max favorable) | |
| MAE (max adverse) | |
| Exit Reason | TP hit / SL hit / Timeout trail / Manual |

**SPRT Update:**

| Field | Value |
|-------|-------|
| Λ this trade | +___ (win) / -___ (loss) |
| Cumulative S_n | |
| Status | Continue / ⚠️ Approaching boundary / ✅ CONFIRM / ❌ KILL |

**Pre-Trade Agreement:** Did I agree with this trade before seeing the outcome? Yes / No / Unsure
- If No/Unsure, why: ___

**AI Reasoning Summary (2-3 sentences):**


**Post-Trade Notes:**


---

### EXAMPLE — Trade #1

| Field | Value |
|-------|-------|
| Date | 2026-04-07 |
| Time (UTC) | 08:15 |
| Instrument | XAUUSD |
| Direction | LONG |
| Kill Zone | London |
| Entry Price | 3042.50 |
| SL Price | 3034.80 |
| SL Distance | 7.70 |
| TP1 / TP2 / TP3 | 3058.20 / 3066.40 / 3078.10 |
| RR at TP1 / TP2 / TP3 | 2.04 / 3.10 / 4.62 |
| Lot Size | 1.30 |
| Risk % | 1.0% |
| AI Grade | A+ |
| AI Confidence Score | 82 |
| Spread at Entry | $0.35 |
| Session Memory State | 3 prior evals this session |
| Correlation Adj | No |

**Outcome:**

| Field | Value |
|-------|-------|
| Result | Win |
| R-Multiple | +2.31 |
| Partials Hit | TP1 ✓ / TP2 ✓ / TP3 ✗ |
| Time in Trade | 1h 47m |
| MFE | +3.10R |
| MAE | -0.22R |
| Exit Reason | Timeout trail after TP2 |

**SPRT Update:**

| Field | Value |
|-------|-------|
| Λ this trade | +0.552 |
| Cumulative S_n | +0.552 |
| Status | Continue (need S_n ≥ 2.773 to confirm) |

**Pre-Trade Agreement:** Yes — H1 CHoCH into premium, clean OB at 3041-3043, FVG in impulse, D1 bullish.

**AI Reasoning Summary:** Strong bullish displacement on H1 broke the last swing high with a single-candle impulse creating an FVG. Price retraced to the OB zone at 3042 with M15 showing rejection wicks. Align score 3/4 (D1 bull, H4 bull, H1 bull, M15 neutral).

**Post-Trade Notes:** Clean setup. Spread was tight. Session memory correctly referenced the earlier NO_TRADE at 07:30 as "price hadn't reached the OB yet." TP3 was ambitious — price stalled at London high from prior day. TP2 hit was the realistic target. Timeout trail caught +2.31R vs TP2's +3.10R — acceptable, price was stalling.

---

# SECTION 2 — DAILY LOG

Copy this block at the end of every trading day, including no-trade days.

---

### Daily Log — ____-__-__

**Evaluation Summary:**

| Instrument | Candles Evaluated | CANDIDATEs | Trades | Safety Rejections |
|------------|-------------------|------------|--------|-------------------|
| XAUUSD | | | | |
| US30 | | | | |
| USDJPY | | | | |
| GBPJPY | | | | |
| GBPUSD | | | | |
| **Total** | | | | |

**Safety Rejection Details** (if any):
- ___

**Spread Observations:**

| Instrument | Avg Spread (London KZ) | Avg Spread (NY KZ) | Avg Spread (Tokyo KZ) | Gated Count |
|------------|------------------------|---------------------|----------------------|-------------|
| XAUUSD | | | n/a | |
| US30 | | | n/a | |
| USDJPY | | n/a | | |
| GBPJPY | | n/a | | |
| GBPUSD | | | n/a | |

**Technical Issues:**

| Time (UTC) | Issue | Impact | Resolved? |
|------------|-------|--------|-----------|
| | | | |

**Market Regime (quick read, not analysis):**

| Instrument | Regime | D1 Bias | Notes |
|------------|--------|---------|-------|
| XAUUSD | Trending / Ranging / Volatile | Bull / Bear / Unclear | |
| US30 | | | |
| USDJPY | | | |
| GBPJPY | | | |
| GBPUSD | | | |

**Day Metrics:**

| Metric | Value |
|--------|-------|
| API Cost | $ |
| Trades Today | |
| Day P&L (R) | |
| Cumulative P&L (R) | |
| Portfolio Drawdown | % |
| Emergency Stops Triggered | 0 |

**Notes:**


---

### EXAMPLE — Daily Log — 2026-04-07

**Evaluation Summary:**

| Instrument | Candles Evaluated | CANDIDATEs | Trades | Safety Rejections |
|------------|-------------------|------------|--------|-------------------|
| XAUUSD | 7 | 1 | 1 | 0 |
| US30 | 5 | 0 | 0 | 0 |
| USDJPY | 6 | 1 | 0 | 1 |
| GBPJPY | 5 | 0 | 0 | 0 |
| GBPUSD | 6 | 0 | 0 | 0 |
| **Total** | **29** | **2** | **1** | **1** |

**Safety Rejection Details:**
- USDJPY 01:45 UTC: CANDIDATE rejected — spread $0.048 exceeded $0.036 gate (Tokyo KZ widening)

**Spread Observations:**

| Instrument | Avg Spread (London KZ) | Avg Spread (NY KZ) | Avg Spread (Tokyo KZ) | Gated Count |
|------------|------------------------|---------------------|----------------------|-------------|
| XAUUSD | $0.32 | $0.28 | n/a | 0 |
| US30 | $1.80 | $1.50 | n/a | 0 |
| USDJPY | n/a | n/a | $0.04 | 1 |
| GBPJPY | n/a | n/a | $0.09 | 0 |
| GBPUSD | $0.12 | $0.10 | n/a | 0 |

**Technical Issues:**

| Time (UTC) | Issue | Impact | Resolved? |
|------------|-------|--------|-----------|
| 06:58 | GBPJPY process restart — PID lock stale from weekend | Missed first London candle | Yes, 07:16 |

**Market Regime:**

| Instrument | Regime | D1 Bias | Notes |
|------------|--------|---------|-------|
| XAUUSD | Trending | Bull | Clean HH/HL on H1 all session |
| US30 | Ranging | Unclear | Tight 200pt range, no displacement |
| USDJPY | Trending | Bear | Yen strength, clean structure |
| GBPJPY | Volatile | Unclear | Whipsawed around 192.00 |
| GBPUSD | Trending | Bull | Followed cable strength theme |

**Day Metrics:**

| Metric | Value |
|--------|-------|
| API Cost | $0.42 |
| Trades Today | 1 |
| Day P&L (R) | +2.31 |
| Cumulative P&L (R) | +2.31 |
| Portfolio Drawdown | 0% |
| Emergency Stops Triggered | 0 |

**Notes:** First live day. System ran cleanly after PID lock fix. The USDJPY safety rejection was correct — spread was genuinely wide at Tokyo open. Gold trade was textbook. US30 correctly stayed out — no displacement in a tight range. Good start but n=1 means nothing.

---

# SECTION 3 — WEEKLY REVIEW

Copy this block every Friday (or Sunday before next week).

---

### Week ___ Review (____-__-__ to ____-__-__)

**SPRT Status:**

| Instrument | Trades (cum) | Wins (cum) | S_n | Status | Boundary Distance |
|------------|-------------|------------|-----|--------|-------------------|
| XAUUSD | | | | Continue / Confirm / Kill | ___ to confirm, ___ to kill |
| US30 | | | | | |
| USDJPY | | | | | |
| GBPJPY | | | | | |
| GBPUSD | | | | | |
| **Portfolio** | | | | | |

**Rolling Performance:**

| Instrument | Last 10 WR | Last 10 Exp(R) | Batch WR | Delta |
|------------|-----------|---------------|----------|-------|
| XAUUSD | | | 62.0% | |
| US30 | | | 58.5% | |
| USDJPY | | | 75.8% | |
| GBPJPY | | | 57.1% | |
| GBPUSD | | | 83.3% | |
| **Portfolio** | | | ~60% | |

**Week Summary:**

| Metric | This Week | 4-Week Avg | Batch Baseline |
|--------|-----------|------------|---------------|
| Total Trades | | | ~4/week |
| Portfolio WR | | | ~60% |
| Portfolio Exp(R) | | | +0.28R |
| Week P&L (R) | | | |
| Cumulative P&L (R) | | | |
| Max Drawdown | | | |

**Direction Breakdown:**

| | LONG Trades | LONG WR | SHORT Trades | SHORT WR |
|---|------------|---------|-------------|----------|
| This week | | | | |
| Cumulative | | | | |

**CUSUM Tracker:**

| Instrument | S_deterioration | S_improvement | Signal? |
|------------|----------------|---------------|---------|
| XAUUSD | | | |
| US30 | | | |
| USDJPY | | | |
| GBPJPY | | | |
| Portfolio | | | |

(Update after each trade: S = max(0, S_prev + (0.278 - actual_R) - 0.5) for deterioration)

**Correlation Events:**
- USDJPY + GBPJPY same-day signals: ___ times this week
- Same-day same-direction: ___ | Opposite direction: ___
- Max daily JPY exposure: ___% (limit: 2%)

**Instruments Approaching Boundaries:**
- ___

**Session Memory Observations:**

| Metric | Value |
|--------|-------|
| Avg first-eval CANDIDATE rate | |
| Avg later-eval CANDIDATE rate | |
| First-eval trade WR | |
| Later-eval trade WR | |

**Comparison to Expectations:**
- Trade frequency vs expected: ___
- WR vs batch baseline: ___
- Expectancy vs batch baseline: ___
- Anything surprising: ___

**Action Items for Next Week:**
1. ___
2. ___
3. ___

**Prompt Change Temptation Log:**
(Write down things you want to change but MUST NOT change yet. Review after walk-forward window closes.)
- ___

---

### EXAMPLE — Week 1 Review (2026-04-07 to 2026-04-11)

**SPRT Status:**

| Instrument | Trades (cum) | Wins (cum) | S_n | Status | Boundary Distance |
|------------|-------------|------------|-----|--------|-------------------|
| XAUUSD | 2 | 2 | +1.104 | Continue | 1.669 to confirm, 2.660 to kill |
| US30 | 1 | 0 | -0.526 | Continue | 3.299 to confirm, 1.030 to kill |
| USDJPY | 1 | 1 | +0.637 | Continue | 2.136 to confirm, 2.193 to kill |
| GBPJPY | 0 | 0 | 0.000 | Continue | — |
| GBPUSD | 0 | 0 | 0.000 | Continue | — |
| **Portfolio** | **4** | **3** | **+0.919** | Continue | 1.854 to confirm, 2.475 to kill |

**Rolling Performance:**

| Instrument | Last 10 WR | Last 10 Exp(R) | Batch WR | Delta |
|------------|-----------|---------------|----------|-------|
| XAUUSD | 100% (n=2) | +1.90R | 62.0% | +38pp (meaningless at n=2) |
| US30 | 0% (n=1) | -1.00R | 58.5% | — |
| USDJPY | 100% (n=1) | +1.48R | 75.8% | — |
| GBPJPY | — | — | 57.1% | — |
| GBPUSD | — | — | 83.3% | — |
| **Portfolio** | **75% (n=4)** | **+1.07R** | ~60% | +15pp (n too small) |

**Week Summary:**

| Metric | This Week | 4-Week Avg | Batch Baseline |
|--------|-----------|------------|---------------|
| Total Trades | 4 | 4 (wk1 only) | ~4/week |
| Portfolio WR | 75% | 75% | ~60% |
| Portfolio Exp(R) | +1.07R | +1.07R | +0.28R |
| Week P&L (R) | +4.28R | +4.28R | |
| Cumulative P&L (R) | +4.28R | | |
| Max Drawdown | 0.52% | | |

**Direction Breakdown:**

| | LONG Trades | LONG WR | SHORT Trades | SHORT WR |
|---|------------|---------|-------------|----------|
| This week | 3 | 100% | 1 | 0% |
| Cumulative | 3 | 100% | 1 | 0% |

**CUSUM Tracker:**

| Instrument | S_deterioration | S_improvement | Signal? |
|------------|----------------|---------------|---------|
| XAUUSD | 0.000 | 1.122 | No |
| US30 | 0.778 | 0.000 | No |
| USDJPY | 0.000 | 0.702 | No |
| GBPJPY | 0.000 | 0.000 | No |
| Portfolio | 0.000 | 2.284 | No |

**Correlation Events:**
- USDJPY + GBPJPY same-day signals: 0 times
- Max daily JPY exposure: 1.0% (within limit)

**Instruments Approaching Boundaries:** None

**Session Memory Observations:**

| Metric | Value |
|--------|-------|
| Avg first-eval CANDIDATE rate | 18% (2/11) |
| Avg later-eval CANDIDATE rate | 6% (1/18) |
| First-eval trade WR | 50% (1/2) |
| Later-eval trade WR | 100% (2/2) |

**Comparison to Expectations:**
- Trade frequency: 4 trades vs ~4 expected — on target
- WR: 75% vs 60% batch — above but n=4 is noise
- The US30 loss was a timeout trail that got stopped at BE then reversed — annoying but system worked correctly
- Session memory appears functional: later evaluations are more selective (6% vs 18% CANDIDATE rate)

**Action Items for Next Week:**
1. Monitor GBPJPY — zero evaluations reaching CANDIDATE. Is pre-screen killing everything? Check logs.
2. Verify the US30 timeout trail was correctly implemented (did it trail at BE or at entry?)
3. Keep logging spreads — Tokyo spreads were wider than expected on USDJPY

**Prompt Change Temptation Log:**
- Want to tighten US30 timeout from 2h to 1.5h after seeing the BE trail loss. NOT CHANGING. Need 20+ US30 trades before any timeout adjustment has statistical meaning.
- GBPJPY silence is tempting me to widen the pre-screen. DO NOT TOUCH. If it doesn't trade for 2 weeks, that's data too.

---

# REFERENCE — SPRT Λ VALUES

Keep this table handy. Look up the Λ value after each trade and add it to the running S_n.

| Instrument | p₀ (breakeven) | p₁ (batch) | Λ_win | Λ_loss | Confirm (S_n ≥) | Kill (S_n ≤) |
|------------|---------------|------------|-------|--------|-----------------|-------------|
| XAUUSD | 0.357 | 0.620 | +0.552 | -0.526 | +2.773 | -1.556 |
| US30 | 0.345 | 0.585 | +0.528 | -0.520 | +2.773 | -1.556 |
| USDJPY | 0.400 | 0.758 | +0.637 | -0.869 | +2.773 | -1.556 |
| GBPJPY | 0.417 | 0.571 | +0.314 | -0.292 | +2.773 | -1.556 |
| GBPUSD | 0.333 | 0.833 | +0.916 | -1.099 | +2.773 | -1.556 |
| Portfolio | 0.380 | 0.600 | +0.457 | -0.438 | +2.773 | -1.556 |

**Quick mental math:** For gold, each win adds ~+0.55, each loss subtracts ~-0.53. Almost symmetric. You need cumulative S_n of +2.77 to confirm (roughly 5 net wins above breakeven) or -1.56 to kill (roughly 3 net losses below breakeven).

---

# REFERENCE — EMERGENCY STOP CHECKLIST

If ANY of these trigger, halt ALL trading and investigate before resuming.

- [ ] Portfolio drawdown > 4%
- [ ] Any single trade loses > 1.5R
- [ ] More than 1 trade placed in a single kill zone
- [ ] Trade placed outside kill zones
- [ ] MT5 position doesn't match system logs
- [ ] 5 consecutive losses on any single instrument
- [ ] Spread consistently > $1.00 on gold during KZ

---

# REFERENCE — WEEK 1 STANDING RULES

1. **NO PROMPT CHANGES.** Write temptations in the log. Do not act on them.
2. **NO PARAMETER CHANGES.** No SL adjustments, no RR changes, no KZ modifications.
3. **Only acceptable interventions:** fixing crashes, data errors, execution bugs.
4. **First 3 trades per instrument are burn-in.** Don't count toward SPRT.
5. **Log everything even if boring.** No-trade days are data.
6. **Don't extrapolate from small samples.** 2 wins doesn't mean 100% WR. 1 loss doesn't mean the system is broken.
