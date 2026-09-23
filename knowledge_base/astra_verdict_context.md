# Astra Deep Dive Context — WF-1 System Assessment

**Purpose:** Full context package for Astra's next-level verdict on architecture viability.
**Date:** 2026-04-09 (Day 4 of WF-1 live trading)

---

## 1. The Exact U1 Prompt Wording

Source: `src/prompts/primary_analyzer_prompt.py` line 147

```
U1. DIRECTIONAL BIAS: Establish directional bias from the highest available timeframe. 
If Daily structure is clearly bullish or bearish, use Daily as the primary bias. 
If Daily is unclear or ranging, use H4 and H1 directional consensus — at least two 
of D1/H4/H1 must agree on direction for a valid bias. If no timeframe consensus 
exists → NO_TRADE.

U2. H4 ALIGNMENT: If Daily bias is clear, H4 must agree with Daily direction. 
If Daily is unclear, H4 direction becomes the primary higher-timeframe reference — 
H4 must be clearly directional (not ranging). If both Daily and H4 are unclear → NO_TRADE.
```

The full evaluation flow from the prompt:

```
Step 1: Establish directional bias per U1. Check U2 (H4 alignment with the 
established bias). If no valid bias can be established or U2 fails → NO_TRADE. 
State the bias source used (Daily, or H4+H1 consensus if Daily is unclear).

Step 2: Evaluate BOTH frameworks on this candle:
  a) OB Retest criteria (OB1 through OB7)
  b) Breaker Block Retest criteria (BR1 through BR7)
Pick the best qualifying setup. If both qualify, prefer the one with stronger 
displacement and tighter zone. If neither qualifies → NO_TRADE.
```

There is also a short-circuit instruction at line 244:

```
If U1 or U2 fail, output a minimal JSON response with only: decision, kill_zone, 
framework set to "none", and a one-sentence no_trade_reason. Do NOT evaluate OB 
criteria when U1 or U2 have already failed.
```

This means when U1 fails, the AI doesn't even look at setups. It exits immediately.

---

## 2. Real Live Examples: Input → Model Output

### Example A: AI Gets It Right (Apr 6, 07:15 UTC — XAUUSD)

**Input context provided to AI:**
- Alignment score: 3/4 bullish (D1=transitional, H4=bullish, H1=bullish, M15=bullish)
- XAUUSD D1 cross-instrument context injected
- Full H4/H1/M15 candle data

**AI output:**
```json
{
  "decision": "NO_TRADE",
  "daily_bias_direction": "bullish",     ← CORRECT: used H4+H1 fallthrough
  "daily_bias_confidence": "medium",
  "h4_aligned": true,                    ← CORRECT
  "h1_poi_identified": false,
  "no_trade_reason": "Price not at any H1 point of interest required for either framework"
}
```

U1 passed correctly. AI moved to Step 2, found no POI, said NO_TRADE for the right reason.

### Example B: AI Gets It Wrong (Apr 6, 07:45 UTC — XAUUSD, 30 min later)

**Input context provided to AI:**
- Alignment score: 3/4 bullish (D1=transitional, H4=bullish, H1=bullish, M15=bullish)
- Same structure, same data source, same prompt

**AI output:**
```json
{
  "decision": "NO_TRADE",
  "daily_bias_direction": "ranging",     ← WRONG: ignored H4+H1 fallthrough
  "h4_aligned": false,                   ← WRONG: H4 was bullish (verified from MT5)
  "no_trade_reason": "No directional bias consensus and price not at H1 POI"
}
```

U1 failed. AI short-circuited. Never evaluated setups.

### Example C: AI Finds Setup But Inverts TP/SL (Apr 7, 01:15 UTC — USDJPY)

**AI output:**
```json
{
  "decision": "CANDIDATE",
  "ai_grade": "A+",
  "ai_confidence": 85,
  "ai_direction": "LONG",
  "ai_framework": "ob_retest",
  "trade_parameters": {
    "entry_price": 159.464,
    "stop_loss": 159.516,      ← ABOVE entry on a LONG (wrong)
    "take_profit_1": 159.386,  ← BELOW entry on a LONG (wrong)
    "risk_reward_ratio": 1.5
  }
}
```

Setup identification was correct. Price level computation was inverted. Safety gate caught it.

---

## 3. Canary Test Format

Source: `scripts/canary_test.py`

The canary test sends 10 frozen fixture prompts to the same model (claude-sonnet-4-20250514) and checks:
- Does the response parse as valid JSON?
- Does the decision match the baseline? (CANDIDATE stays CANDIDATE, NO_TRADE stays NO_TRADE)
- Do key fields match? (framework, direction, POI type)
- Keyword drift detection on reasoning text

Pass threshold: 9/10 must match baseline.
Runtime: ~35 seconds.
Runs once per kill zone entry.

It checks output FORMAT stability, NOT decision QUALITY. A canary that says "ranging" instead of "bullish" on U1 would still pass if the response format is valid.

---

## 4. Backtest AI Filter: Same Model/Prompt or Simplified?

**Same model, same prompt.** The batch backtest used:
- Model: claude-sonnet-4-20250514 (identical to live)
- Prompt: identical primary_analyzer_prompt.py
- Data: historical M15/H1/H4/D1 candles fed in the same MSO format
- API: Anthropic Batch API (cheaper, same model)

The backtest was NOT a simplified approximation. It was the exact same pipeline minus MT5 live data and execution. Every one of the 12,006 evaluations went through the full prompt with the full reasoning chain.

Key backtest result: 640 CANDIDATEs out of 12,006 evaluations (5.3%). Live: 1 out of 373 (0.3%). That's a 17x drop in CANDIDATE rate.

---

## 5. TP/SL Generation Logic

The AI generates trade parameters inside its JSON response. There is NO separate TP/SL computation module. The prompt says:

```
trade_parameters: {
  entry_price: <price where limit order should be placed>,
  stop_loss: <price for stop loss — must be beyond the OB zone>,
  take_profit_1: <first target — use next H1 swing or liquidity pool>,
  take_profit_2: <second target — optional, use H4 level if visible>,
  risk_reward_ratio: <computed RR to TP1>,
  direction: "LONG" or "SHORT"
}
```

The AI computes all price levels. There is no post-processing to validate geometric consistency (TP above entry for LONG, SL below entry for LONG). The safety gate in `primary_analyzer.py` catches inversions AFTER the AI returns them, but rejects the trade instead of correcting it.

---

## 6. CANDIDATE Rate: Live vs Backtest by Session/Instrument

### Backtest (12,006 evaluations over ~15 months)

| Instrument | Evals | CANDIDATEs | Rate |
|-----------|-------|------------|------|
| XAUUSD | 6,801 | ~400 | 5.9% |
| USDJPY | 3,648 | ~120 | 3.3% |
| GBPUSD | 987 | ~50 | 5.1% |
| US30 | 362 | ~20 | 5.5% |
| GBPJPY | 208 | ~50 | 24% |

### Live WF-1 (373 evaluations over 4 days)

| Instrument | Evals | CANDIDATEs | Rate | Primary Block |
|-----------|-------|------------|------|---------------|
| XAUUSD | 74 | 0 | 0% | U1 (93%) |
| USDJPY | 105 | 1 | 1.0% | U1 (36%), POI (55%) |
| GBPJPY | 106 | 0 | 0% | U1 (91%) |
| GBPUSD | 30 | 0 | 0% | U1 (100%) |
| US30 | 58 | 0 | 0% | U1 (91%) |

The CANDIDATE rate collapsed from 5.3% (backtest) to 0.3% (live). The cause is almost entirely U1 blocking.

USDJPY is the healthiest — only 36% U1 blocks, most rejections are the correct "price not at POI" filter. But even there, CANDIDATE rate is 1% vs 3.3% backtest.

---

## 7. Backtest/Live Mismatch Diagnosis

### Is it prompt design?
Partially. The U1 fallthrough path exists but is written as narrative text, not structured logic. The AI interprets it inconsistently. The short-circuit instruction at line 244 ("do NOT evaluate OB criteria when U1 has already failed") amplifies the damage — one wrong U1 call kills the entire candle.

### Is it model variance?
Yes, primarily. The 07:15→07:45 flip on identical data is textbook LLM inconsistency. Same prompt, same context, different output. The batch backtest ran all evaluations in one batch job — the model may have been in a different "mode" or the batch API may handle context differently than real-time API.

### Is it environment mismatch?
Possibly. The backtest fed historical candles from CSV files. Live feeds from MT5 real-time. Data format is identical (MSO) but the candle values are different (historical vs live). If the current market regime has more D1 transitional days than the backtest period, U1 blocks would be higher. But 77% is too extreme for regime alone.

### Is it market regime?
Partially. Gold has been choppy recently (tariff uncertainty, USD ranging). But the backtest covered similar choppy periods and still produced 5.3% CANDIDATEs. The AI handled D1=transitional correctly in the backtest at least some of the time.

### Is it architecture error?
**Yes, this is the root cause.** The AI is on the critical path of a deterministic binary decision (bias = bullish/bearish/ranging). LLMs are unreliable at deterministic binary rules. The architecture should compute this in code and give the AI only the qualitative assessment work it's good at.

---

## 8. The Architecture Diagram

```
Current (broken):

  MT5 Data → MSO → [AI decides EVERYTHING] → Safety Gate → Execute
                     ↑
                     U1 bias (fails 77%)
                     U2 alignment
                     Setup evaluation
                     Trade parameters
                     All in one LLM call

Proposed (fixed):

  MT5 Data → MSO → [CODE: deterministic bias + validation]
                     ↓
                     bias = computed, injected as fact
                     TP/SL geometry = validated/corrected
                     ↓
                   [AI: qualitative assessment only]
                     ↓
                     POI quality scoring
                     Displacement strength
                     Setup narrative
                     Confidence ranking
                     ↓
                   Safety Gate → Execute
```

The AI moves from "judge of everything" to "expert advisor within guardrails."

---

## 9. What Astra Should Judge

1. **Is the backtest edge real or is it an artifact of the batch API behaving differently?**
   - The batch API uses the same model but processes prompts differently (no conversation state, potentially different temperature/sampling)
   - If the batch API was less conservative on U1, the entire backtest edge could be inflated

2. **Is the deterministic bias pre-computation the right fix, or does it just mask a deeper architecture problem?**
   - If we hardcode bias, the AI still computes TP/SL (which it gets wrong 4.9% of the time)
   - Should the AI compute ANY price levels, or should code do that too?

3. **Is the CANDIDATE→trade conversion rate viable even if we fix U1?**
   - 640 CANDIDATEs → 100 trades in backtest (15.6% conversion)
   - The 85% that didn't convert were filtered by debate/safety/L2 verification
   - Is that conversion rate achievable in live, or will safety gates block more?

4. **Is this architecture fundamentally viable, or should the AI be removed entirely?**
   - The mechanical backtest showed mechanical entries produce +0.175 R/trade
   - The AI filter produces +0.475 R/trade
   - But that's only if the AI WORKS. If it doesn't work reliably, mechanical > broken AI

---

## 10. Files for Reference

| File | What It Contains |
|------|-----------------|
| `knowledge_base/wf1_observations.md` | 5 observations with details and fix plans |
| `knowledge_base/wf1_system_assessment.md` | System verdict and recommendations |
| `knowledge_base/live_evaluations/*/2026-04-*.jsonl` | Every AI decision with full fields |
| `knowledge_base/trade_records/USDJPY/2026-04-07_tokyo_0115.json` | The one live CANDIDATE (blocked) |
| `mechanical_vs_ai_comparison.md` | Mechanical backtest proving AI adds value |
| `src/prompts/primary_analyzer_prompt.py` | The full AI prompt |
| `src/components/orchestrator.py` | The orchestrator (bias computation, pipeline flow) |
| `src/components/primary_analyzer.py` | AI call logic, safety gates, retry logic |
