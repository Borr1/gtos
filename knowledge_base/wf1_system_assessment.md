# WF-1 System Assessment — Days 1-4 (April 6-9, 2026)

## The Numbers

| Metric | Live (4 days) | Backtest Reference |
|--------|--------------|-------------------|
| Total evaluations | 373 | 12,006 |
| CANDIDATEs | 1 (0.3%) | 640 (5.3%) |
| Trades executed | **0** | 100 |
| CANDIDATE rate | 0.3% | 5.3% |
| Expected trades/month | ~5 (from CANDIDATE rate) | 6.7 |
| Actual trades/month so far | **0** | 6.7 |

## Is the System Working?

**The plumbing works.** Processes start, connect to MT5, evaluate every M15 candle on schedule, call the AI, get responses, log everything. The canary check passes, safety gates catch bad outputs, data is being tracked. From an engineering standpoint, everything is functional.

**The system is not trading.** Zero trades executed in 4 days. The one CANDIDATE found (USDJPY Apr 7 Tokyo) had inverted TP/SL and was correctly blocked by the safety gate. The system is effectively a very expensive monitoring tool right now.

## What's Breaking — The U1 Bottleneck

**77% of all NO_TRADE decisions (286 out of 372) are blocked by U1** — the directional bias rule.

The pattern is the same across all instruments and all days:
- Local align score: 3/4 (D1=transitional, H4=bullish, H1=bullish, M15=bullish)
- AI decision: "ranging, no consensus"
- The prompt says: "if D1 is unclear, use H4+H1 consensus — at least 2 of 3 must agree"
- H4 and H1 both agree → should pass → AI blocks it anyway

This isn't a market condition issue. The AI is misinterpreting its own prompt. It treats D1=transitional as a hard blocker even though the prompt explicitly provides a fallthrough path.

**Only 17% of blocks are the intended "price not at POI" filter** — the actual SMC-based filtering that should be doing the work.

## What's Not at Full Potential

### 1. The AI Is Too Conservative on U1 (77% of all blocks)
The prompt is correct. The AI doesn't reliably follow it. On Day 1, it correctly applied the H4+H1 fallthrough at 07:15 and 07:30, then inexplicably flipped at 07:45 with identical data. This inconsistency — not conservatism — is the core problem.

### 2. Inverted TP/SL (4.9% of CANDIDATEs in backtest)
When the AI DOES find a setup, it sometimes puts TP below entry on a LONG (or SL below entry on a SHORT). The safety gate catches it, but the valid setup is wasted. 30 out of 611 backtest CANDIDATEs had this issue. Our one live CANDIDATE hit it too.

### 3. Cold Start Memory
Session memory resets every KZ and every restart. The AI has no context from previous evaluations. This may amplify the U1 inconsistency — the AI at 07:45 doesn't "remember" it said bullish at 07:30.

### 4. Malformed Responses
3 retries on Apr 8 XAUUSD alone. Each retry costs an extra API call and 15 seconds. The AI sometimes returns invalid JSON.

## Do We Have an Edge?

**The backtest says yes.** The mechanical backtest proved the AI filter produces +0.475 R/trade vs +0.175 for mechanical entries — the AI adds real value by selecting which OB retests to trade. The backtest had 65% WR across 100 trades over 15 months.

**But the edge can't manifest if the system never trades.** The U1 bottleneck means the AI's setup evaluation (the part that actually has edge) never gets to run. It's like having a great striker but never getting the ball past midfield.

## What Can Be Fixed

### Fixable Within WF-1 Rules (safety gates, not prompt changes)

1. **Inverted TP/SL auto-correction** — Post-process the AI output: if direction=LONG and TP < entry, swap the distances. This is a safety/validation fix, not a prompt change. The AI identified the setup correctly, it just computed prices wrong.

2. **MT5 reconnection** — Add `mt5.initialize()` retry when `copy_rates_from_pos` returns None. Currently a restart of MT5 kills all processes silently.

### Fixable in WF-2 (requires prompt or context changes)

3. **U1 enforcement** — Two approaches:
   - **Option A:** Add explicit instruction in the prompt: "When D1 is transitional AND H4+H1 are both bullish or both bearish, you MUST set daily_bias to that direction, NOT ranging."
   - **Option B:** Pre-compute the bias in code (deterministic) and inject it as a fixed parameter the AI cannot override. If D1=transitional and H4+H1 agree, code says bias=bullish and the AI works from there.
   - Option B is stronger because it removes LLM variance from a binary decision.

4. **Session memory warm-start** — Load last 6 evaluations from JSONL on bootstrap. Implementation guide in wf1_observations.md.

5. **Malformed response handling** — Consider using structured output / JSON mode if the API supports it, to eliminate retry costs.

## The AI and Markets Question

The market structure the system trades on (liquidity sweeps, order blocks, displacement) is rooted in institutional order flow. AI adoption in markets primarily affects:
- **Speed of reaction** to news/data (already dominated by algo HFT)
- **Pattern recognition at microsecond scale** (not our timeframe)
- **Crowding of momentum strategies** (could affect us if SMC becomes too crowded)

The OB retest framework is specifically designed around market microstructure that persists because of HOW large orders are executed, not because retail traders don't know about it. Institutional block orders create OBs whether AI is involved or not.

The bigger AI risk isn't market competition — it's the U1 problem. If the AI model degrades or becomes more conservative over time (model drift), the system could slowly stop trading without anyone noticing. The canary test is the defense against this, but it only checks output format, not decision quality.

## Verdict

**The system has edge but can't express it.** The AI-as-filter architecture is proven (+0.475 R/trade vs +0.175 mechanical). But in live trading, the AI is blocking 77% of evaluations on U1 before it even looks at the actual setup. The fix is straightforward (deterministic bias pre-computation or prompt reinforcement) but can't be deployed until WF-2 unless we classify it as a bug fix rather than a change.

**Recommendation:** Classify the U1 misapplication as a bug — the prompt already says the right thing, the AI isn't following it. A deterministic pre-computation of bias (Option B above) doesn't change the prompt, doesn't change the trading logic, and simply ensures the AI receives accurate bias information instead of being asked to compute it unreliably.

**If we don't fix this, WF-1 will produce zero trades and zero data to evaluate.** That defeats the entire purpose of the walk-forward test.
