# System Deep Dive — Complete Understanding

**Date:** 2026-04-03
**Status:** COMPLETE
**Instruments:** GBPUSD (primary), XAUUSD (reference)
**Data:** 149 GBPUSD sessions, 242 XAUUSD sessions, all parsed PA responses

---

## Part A: How the AI Thinks

### A1: Winning Trade Reasoning (5 examples)

**Pattern: Winning trades have formulaic, confident reasoning with specific price levels and ratios.**

**WIN 1: 2024-02-06 London R=+2.38 (best GBPUSD trade)**
- Grade: A+, Confidence: 80
- Computation: `Baseline 70 + strong displacement (+5) + clean unmitigated OB (+5) = 80`
- Overall reasoning: "Strong OB retest setup with H1 unmitigated bullish OB, multiple asian_high sweeps providing liquidity, and exceptional M15 confirmation with 4.6x displacement ratio. All timeframes aligned bullish with clean structural breaks."
- Daily bias: bullish (high) — "D1 shows clear bullish structure with protected swing at 1.26488."
- H1: OB at 1.25383-1.25325, discount zone, BOS-caused
- M15: BOS at 1.25567, displacement 4.6x avg body
- Entry: 1.25354, SL: 1.25168, TP1: 1.25633

**WIN 2: 2024-01-25 London R=+0.75**
- Grade: A+, Confidence: 80
- Same formula: `Baseline 70 + strong displacement (+5) + clean unmitigated OB (+5) = 80`
- "Clean H1 OB retest setup with recent BOS creating unmitigated bullish OB in discount zone. M15 shows strong CHoCH+displacement confirming bullish momentum."

**WIN 3: 2024-05-24 London R=+1.90**
- Grade: A+, Confidence: 80
- "Strong H1 OB retest setup with clean liquidity sweep, optimal OTE retracement, and strong M15 confirmation. Price swept asian_low/pdl then returned to fresh H1 OB zone with powerful displacement confirmation."

**WIN 4: 2024-05-31 NY R=+0.06 (barely positive)**
- Grade: A+, Confidence: **85** (highest seen)
- Computation: `Baseline 70 + strong displacement (+10, ratio 6.5x) + clean OB formation (+5) = 85`
- "Exceptional setup with all criteria met" — yet only R=+0.06. **High confidence does NOT predict large R.**

**WIN 5: 2024-01-31 NY R=+0.75**
- Grade: A, Confidence: 80
- "Strong H1 OB Retest setup with BOS displacement (3.0x), unmitigated OB in discount zone at 62% retracement."

### A2: Losing Trade Reasoning (5 examples)

**Critical finding: Losing trades have IDENTICAL reasoning quality and confidence to winners. The AI cannot distinguish them.**

**LOSS 1: 2024-03-01 NY R=-1.00 (SL hit, MFE=0.51R)**
- Grade: A, Confidence: **75**
- Computation: `Baseline 70 + strong H1 displacement (+5) + clean OB formation (+5) - CHoCH rather than BOS (-5) = 75`
- "H1 BOS with strong displacement created unmitigated OB in discount zone. Price pulled back into OB and M15 confirmed with structural break."
- **Only difference from winners: mentions CHoCH penalty (-5). Still passed.**

**LOSS 2: 2024-03-13 NY R=-0.10 (timeout, MFE=0.57R)**
- Grade: A+, Confidence: **80**
- "Strong H1 OB retest setup with clean BOS at 13:00 creating unmitigated OB... All universal requirements met."
- **Indistinguishable from a winner.**

**LOSS 3: 2024-03-15 NY R=-1.00 (SL hit, MFE=0.78R)**
- Grade: A+, Confidence: **80**
- Same formula, same language.

**LOSS 4: 2024-03-18 London R=-1.00 (SL hit, MFE=0.34R)**
- Grade: A+, Confidence: **80**
- "Strong OB retest setup with H1 bullish OB in discount zone, clean liquidity sweep, and strong M15 confirmation with 3.5x displacement."

**LOSS 5: 2024-05-28 NY R=-0.74 (timeout, MFE=0.20R)**
- Grade: A+, Confidence: **80**
- "Strong H1 OB retest setup with all criteria met."

### Key Insight: Winner vs Loser Reasoning

| Metric | Winners (n=5) | Losers (n=5) |
|--------|--------------|-------------|
| Average confidence | 81.0 | 79.0 |
| A+ grade count | 4/5 | 4/5 |
| Uses "strong" in reasoning | 5/5 | 5/5 |
| Mentions specific prices | 5/5 | 5/5 |
| Self-check doubt expressed | 0/5 | 0/5 |

**The AI is not expressing doubt on losers.** Its reasoning is a template with substituted values. There is no calibrated uncertainty — every CANDIDATE gets the same confident narrative.

### A3: NO_TRADE on Active Days

The analysis found no dates where the displacement scan showed aligned KZ activity but the batch produced no trades AND had response files. This is because the batch only processes prescreen-pass dates, and the displacement scan includes all dates. The mismatch occurs on prescreen-killed dates (Lever 3 opportunity).

### A5: Confidence Score Analysis

**GBPUSD Confidence Distribution (56 CANDIDATE trades):**
- Min: 75, Max: 85, Mean: 79.7, Median: 80
- **Extremely narrow range** — 91% of all trades are 75-85

**Confidence vs Win Rate:**

| Bin | n | Wins | Win Rate |
|-----|---|------|----------|
| 75-85 | 51 | 25 | **49.0%** |
| 85-95 | 5 | 2 | **40.0%** |

**Confidence is NOT predictive.** The 85+ bin actually has a LOWER win rate. The confidence scoring system produces a narrow band (75-85) with no predictive power.

**Confidence Computation Breakdown:**
The most common computation is: `Baseline 70 + strong displacement (+5) + clean unmitigated OB (+5) = 80`
This appears 28/56 times (50%). The formula is nearly deterministic — it's a checkbox, not a probabilistic assessment.

**XAUUSD (138 CANDIDATE trades):**
- Min: 75, Max: 85, Mean: 79.6
- 75-85 bin: 135 trades, 46.7% WR
- 85-95 bin: 3 trades, 66.7% WR (too small to draw conclusions)

Same pattern: narrow range, no predictive value.

### A4/A6: Session Memory

Session memory is only used in the live/sequential pipeline, NOT in batch mode. The batch processes each candle independently with only the system prompt's static context cached.

In the orchestrator, session memory stores the last 6 candle evaluations per KZ as compressed summaries (decision, brief reasoning). This is injected into the user message as text. **Batch results represent a floor** — live trading with session memory could be slightly better since the AI can reference recent assessments.

---

## Part B: What the AI Sees

### B1: System Prompt

**Character count: 12,120 characters**
**Estimated tokens: ~3,030**

12 sections:
1. Kill Zone Windows (configurable)
2. Universal Requirements (U1-U7)
3. Evaluation Sequence (Step 1-3)
4. H1 OB Retest Criteria (OB1-OB7)
5. H1 Breaker Block Retest Criteria (BR1-BR7)
6. Setup Grading (A+/A/B+ rubric)
7. Confidence Score Rubric
8. Critical Rules
9. Token Efficiency
10. Output Format (JSON schema)
11. Data Grounding Rules
12. Conciseness Rules

### B2: Complete MSO (2024-02-06 London, CANDIDATE trade)

**User message: 3,051 characters (~763 tokens)**

Contents:
- Session H/L + London H/L (2 lines)
- Sweeps (5 shown of 27 detected)
- H1: structure=bullish, 5 breaks, 1 unmitigated OB, 2 breakers, 5 FVGs, P/D zones, avg body/ATR
- M15: structure=bullish, 5 breaks, 2 unmitigated OBs, 1 breaker, 8 FVGs, P/D zones, avg body/ATR
- Recent M15 swings (10 entries)
- Evaluation instruction

**Key observation:** The MSO is compact (~3K chars) but information-dense. Every number is a specific price level. The AI has 4 timeframes of structural data to reason about.

### B3: Token Budget

**Per-candle:**
- Input tokens: avg 1,530 (min 1,306, max 1,716)
- Output tokens: avg 706 (min 571, max 764)
- No truncation detected (max 764 vs 2,000 limit)
- Context utilization: **0.8% of 200K window**

**Per-session (20 candles):**
- Input: ~28,000 tokens
- Output: ~14,000 tokens
- Total: ~42,000 tokens
- **Room for 4-5x more context if needed**

**Cache behavior:**
- System prompt + static D1/H4 context is cached (~4,600 tokens)
- Dynamic M15/H1 data changes per candle (~1,300 tokens fresh)
- Cache hit rate varies (batch API manages caching differently from sequential)

### B4: M5 Refinement

**System prompt (33 words):**
"You are an expert {symbol} scalper specializing in M5 entry refinement within confirmed Smart Money setups. A CANDIDATE trade has already been confirmed on M15. Your job is to find the tightest valid stop loss based on M5 structural levels within the setup zone."

**User message (~300 tokens):**
- Confirmed M15 setup details (direction, entry, SL, zone)
- 36 M5 candles formatted as `time | O H L C`
- 6-point analysis instruction
- JSON output schema

**Output (~100 tokens):**
```json
{"decision": "REFINED", "m5_quality": "HIGH", "m5_sl": 2880.50, "m5_sl_distance": 4.20, "m5_structure": "higher_low", "reasoning": "Clean M5 higher-low at 2880.50 with displacement..."}
```

M5 refinement is extremely lightweight — ~400 tokens total per call vs ~2,200 for the PA.

---

## Part C: Where the AI Fails

### C1: Loss Categorization (16 GBPUSD losses)

| Category | Count | % | Description |
|----------|-------|---|-------------|
| **market_condition** | **10** | **62%** | Normal losses — correct direction but market reversed. MFE 0.20-0.86R. |
| SL_too_tight | 2 | 13% | Had 1.0R+ MFE but still hit SL (2024-06-05: MFE=1.42R; 2025-04-29: MFE=1.24R) |
| immediate_reversal | 2 | 13% | Never went in direction (MFE < 0.20R). Setup looked good but failed instantly. |
| timing_error | 2 | 13% | Slightly underwater at session timeout (R > -0.5). |

**Key finding:** 62% of losses are irreducible market randomness — the AI correctly identified the setup, but the market moved against. Only 13% (SL too tight) are fixable by the system, and 13% (immediate reversals) suggest the AI occasionally misreads the market.

### SL Too Tight Analysis (2 trades)

**2024-06-05 NY:** MFE 1.42R → SL hit at -1.00R. Price reached +1.42R above entry then reversed to hit SL. A trailing stop to breakeven after 1R would have saved this trade.

**2025-04-29 London:** MFE 1.24R → SL hit. Same pattern — exceeded TP1 threshold then reversed.

Both trades would have been saved by the 50/50 partial close strategy (close half at TP1, trail SL to BE on runner).

### C2: Safety Rejections

| Rejection | Count | Meaning |
|-----------|-------|---------|
| direction_mismatch | 8 | AI tried to trade against D1 bias |
| sl_too_tight | 3 | Proposed SL below ATR threshold |
| below_grade | 2 | AI graded B+ or lower |

The 8 direction mismatches are the AI occasionally outputting SHORT on bullish D1 days (or vice versa). The safety check correctly catches these.

### C4: Multi-Candle Decision Patterns

**When does the CANDIDATE fire?**

```
Candle  1:  1    (earliest)
Candle  2:  3
Candle  3:  2
Candle  4:  4
Candle  5:  2
Candle  6:  2
Candle  7:  3
Candle  8: 10    ← PEAK (this is 09:00 UTC in London, 14:00 in NY)
Candle  9:  1
Candle 10:  2
Candle 18:  8    ← SECOND PEAK (late in NY session)
Mean position: 10.6
```

**Two peaks:** Candle 8 (09:00 London / 14:00 NY) and candle 18 (late session). The AI waits for the setup to develop before firing. Very few first-candle entries.

**Non-trading session pattern:**
- 243 non-trading KZ sessions
- **100% immediate NO_TRADE** on every candle (no WAIT decisions)
- Zero "warming up" behavior

The AI either sees a setup or doesn't. It doesn't gradually build conviction across candles. **This means WAIT decisions are essentially never used** — the binary nature (CANDIDATE/NO_TRADE) is the actual operating mode.

---

## Part D: Partial Close Analysis

### From GBPUSD Batch Data

The batch already computed 50/50 partial close results. Key comparison:

| Strategy | Avg R | Total R | Note |
|----------|-------|---------|------|
| 100% at TP1 (1.5R) | +0.420 | +17.65 | Current config |
| 50/50 partial | +0.573 | +24.06 | From batch scorer |
| Difference | +0.153 | +6.41 | +36% improvement |

The 2 SL-too-tight losses (MFE > 1R) would have been converted to small wins under partial close, contributing ~2R of the +6.41R improvement. The remaining ~4.41R comes from runners on winning trades that continued beyond 1.5R.

---

## Part E: Architecture Deep Dive

### E1: Orchestrator Flow (One KZ)

```
For each M15 candle close in kill zone:
  1. Data ingestion: MT5 pulls current M15 candle data
  2. MSO build: compute_market_state() runs deterministic analysis (swings, OBs, FVGs, etc.)
  3. Pre-screen: Check D1+H4 direction (first candle only per day)
  4. Session memory: Build text summary of last 6 candle assessments in this KZ
  5. Prompt build: build_prompt() creates system + user message
     - Static context (D1/H4/session levels) → cached across candles
     - Dynamic context (H1/M15/sweeps) → fresh each candle
     - Session memory injected into user message
  6. API call: Claude evaluates and returns JSON
  7. Parse + validate: Extract PrimaryAnalysisOutput
  8. Safety check: Grade >= A, direction matches D1, RR >= 1.3, SL >= 1.5 ATR
  9. If CANDIDATE:
     a. M5 refinement (if enabled): tighten SL using M5 structure
     b. Permission check: gate3 circuit breakers then gate1 safety
     c. Execute trade via MT5
     d. Update session state (trades_today++, trades_{kz}++)
     e. SKIP remaining candles in this KZ
  10. Update session memory with this candle's assessment
```

### E2: What Changes Between Candles

- **MSO rebuilt from scratch** each candle (not incremental). 15 minutes of price action can create new M15 breaks, new OBs, new FVGs, shift P/D zones.
- **H1/H4/D1 structure CAN change** between candles — unlikely on H4/D1 within 15 min, but H1 can shift.
- **Session memory** includes the previous candle's assessment (in live mode).

### E3: Token Flow (One Session)

For a 20-candle session:
- **Cached (identical across candles):** System prompt + D1/H4 static context = ~4,600 tokens
- **Dynamic per candle:** H1/M15 data = ~1,300-1,500 tokens
- **Output per candle:** ~700 tokens
- **Total session:** ~28,000 input + 14,000 output = 42,000 tokens

**Cache hit rate in batch:** Variable (0-300%+ reported — the batch API's caching is opaque). In sequential mode with prompt caching, the system prompt tokens are read from cache on candles 2-20, saving ~80% of the static portion.

---

## Part F: Opportunity Identification

### F1: Computed But Unused Information

All MSO fields ARE sent to the AI via `model_dump()`. The prompt builder explicitly formats:
- Session levels (Asian H/L, PDH/PDL, London H/L)
- Liquidity pools (up to 10)
- D1/H4/H1/M15: structure, breaks, unmitigated OBs, breakers, FVGs, P/D zones, avg body, ATR

**Not computed but potentially useful:**
- **Volatility regime:** D1 ATR percentile (is today's range normal, compressed, or expanding?)
- **Asian range width vs ADR:** Indicator of potential range expansion
- **Pre-KZ range:** How much has price already moved before the KZ opened?
- **Prior session displacement count:** How active was the previous session?
- **DXY correlation:** Dollar strength context for GBP/EUR

These would require ~50-100 additional tokens each in the MSO.

### F2: Cross-Instrument Data

Currently each instrument is evaluated in isolation. With 5 instruments loaded:
- DXY D1 direction available (from DXY_D1.csv)
- EURUSD as inverse-dollar proxy
- Gold direction as risk sentiment indicator

**Injection method:** A single line in the static context:
```
## Cross-Instrument: DXY=bearish, XAUUSD=bullish, EURUSD=bullish
```
Cost: ~20 additional tokens. Value: unknown but could reduce false signals on days where the dollar context conflicts.

### F3: Context Agent Feasibility

**Current architecture:** One monolithic PA call per candle.
- System prompt: ~3,000 tokens (12 sections)
- Static context: ~1,600 tokens (D1/H4/session levels)
- Dynamic context: ~1,300 tokens (H1/M15/sweeps)
- Output: ~700 tokens
- Total per candle: ~6,600 tokens
- Total per session (20 candles): ~29,000 input + 14,000 output

**Proposed two-agent architecture:**
- Context Agent (once per session): Input ~8,000 tokens (full MSO + rich system prompt), Output ~500 tokens (session plan: bias, key levels, expected setups)
- Entry Agent (per candle): Input ~2,500 tokens (plan + M15 data only + slim system prompt), Output ~500 tokens

**Estimated per session:** 8,500 + 20 × 3,000 = 68,500 tokens

**Verdict:** The context agent would **increase** total token usage (~2.3x), not decrease it. The current system is already efficient because prompt caching handles the static/dynamic split well. The two-agent architecture only makes sense if:
1. The Entry Agent prompt can be drastically shorter (remove framework criteria, rely on Context Agent's plan)
2. Or if the Context Agent provides information the current system CAN'T (cross-session patterns, multi-instrument correlation)

**A better optimization target:** The confidence scoring section of the prompt (~500 tokens) produces no predictive value (A5 showed confidence doesn't predict outcomes). Removing it would save ~500 × 20 = 10,000 cache-read tokens per session.

---

## Summary of Key Findings

### The AI's Reasoning is Templatic
Every CANDIDATE gets near-identical confident language. Losers and winners are indistinguishable in reasoning quality, grade, and confidence. The self-check step (Step 3 in the prompt) never fires — zero trades show doubt.

### Confidence Scoring Has Zero Predictive Power
75-85 range, 91% of trades at 80. Win rate flat across bins. The computation is a deterministic checkbox (displacement_present + OB_unmitigated → 80). This entire system (~500 prompt tokens) should be simplified or removed.

### 62% of Losses Are Irreducible
Market condition losses where the AI correctly identified the setup but the market reversed. These cannot be fixed by better reasoning — they're the cost of business. The 13% SL-too-tight losses ARE fixable (partial close / trailing stop).

### Session Memory Is Unused in Batch
All batch results are without session memory. Live performance should be >=  batch performance since session memory adds context.

### Token Budget Has 99% Headroom
0.8% of context window used. There is massive room to add richer context (volatility regime, cross-instrument data, session memory, multi-timeframe confluence scoring) without approaching limits.

### WAIT Decisions Never Occur
100% of non-trading sessions are immediate NO_TRADE on every candle. The AI operates in pure binary mode. The WAIT mechanism in the prompt is dead code.

---

## Structured Data

Full data saved to: `knowledge_base_backtest/analysis/system_deep_dive_data_20260403.json`

Contains:
- `winning_trades_reasoning`: 5 objects with full verbatim reasoning
- `losing_trades_reasoning`: 5 objects with full verbatim reasoning
- `candidate_confidences_gbpusd`: 56 trades with confidence, computation, outcome
- `candidate_confidences_xauusd`: 138 trades with confidence, outcome
- `loss_categorization`: {market_condition: 10, SL_too_tight: 2, immediate_reversal: 2, timing_error: 2}
- `candidate_timing`: array of candle positions when CANDIDATE fires
- `decision_patterns`: {no_trade_sessions: 243, immediate_notrade: 243, warmup: 0}
- `token_analysis`: per-candle token counts (10 samples)
- `session_token_usage`: per-session totals (20 sessions)
- `system_prompt_sections`: 12 section headers
- `context_agent_estimate`: token projections for two-agent architecture
