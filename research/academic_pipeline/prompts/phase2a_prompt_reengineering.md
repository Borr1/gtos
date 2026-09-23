# Phase 2A: Prompt Re-Engineering Test
## Date: 2026-04-12
## Written by: Strategic Research Advisor
## Basis: T2c Phase 1 results (3 effort levels), word-by-word prompt analysis, T2b memory/framing findings
## Budget: ~$12 (3 tests × 121 trades × ~$0.035/call)

---

## OVERVIEW

T2c Phase 1 showed Sonnet 4.6 over-rejects 83-88% of setups across all effort levels. Word-by-word analysis of the current prompt identified **10 specific conservatism amplifiers** and **4 missing elements** that together explain WHY over-rejection happens. This test evaluates a re-engineered prompt designed to eliminate asymmetric conservatism while preserving the statistical edge.

**Hypothesis (stated BEFORE seeing results):** The re-engineered prompt will increase Sonnet 4.6's CANDIDATE rate from 11-17% to >35% while maintaining WR >= 58%.

**What changed (summary):**
1. Identity: institutional SMC trader → quantitative setup evaluator
2. Evaluation: 7 binary pass/fail gates → 3 hard gates + scored qualifying criteria
3. Self-check: removed entirely (was asymmetric doubt amplifier)
4. Tolerances: "near" and "displacement" quantified with explicit bands
5. Calibration: added expected CANDIDATE rate and error asymmetry guidance
6. Grade gate: A/A+ only → score >= 65 (equivalent to B+ and above)
7. Conviction: added symmetric "don't over-reject" instruction

**What did NOT change:**
- JSON output schema (identical — system parses this)
- Zone freshness hard rule (backed by n=105,000+ data)
- Kill zone rules
- TP calculation (1.5x SL)
- Data grounding / anti-hallucination rules
- Internal consistency (CANDIDATE requires choch_detected=true)

---

## CHANGES WITH RATIONALE

### Change 1: Identity Reframe
**Before:** "You are an institutional gold trader with 15+ years of experience using Smart Money Concepts (SMC) and ICT methodology"
**After:** "You are a quantitative setup evaluator for an order block retest trading system"
**Why:** The institutional/SMC identity triggers narrative reasoning and conservative persona. T2b Exp4 showed SMC framing is neutral-to-negative. The system's edge is statistical zone continuation, not institutional flow reading. A quantitative framing directs the model toward data-driven analysis instead of "what would smart money do?"

### Change 2: Scored Evaluation Replaces Binary Gates
**Before:** "If ANY requirement fails, output NO_TRADE immediately" (7 binary gates)
**After:** 3 CRITICAL hard gates (bias, alignment, direction match) + 7 QUALIFYING scored criteria with tolerance bands
**Why:** Binary gates with 7 criteria make rejection exponential. A setup that's strong on 6 of 7 criteria gets killed by one borderline failure. The scoring system allows strong zone quality to compensate for moderate M15 confirmation — which is exactly what the data shows (B+ trades have 77% WR but get killed by the current binary system).

### Change 3: Self-Check Removed
**Before:** 4 doubt-inducing questions ("Am I rationalizing? Would a skeptic agree?") with "if ANY raises doubt → downgrade"
**After:** Removed entirely
**Why:** This section has no positive counterbalance. All 4 questions push toward rejection. In real markets, there are ALWAYS conflicting signals, so "are there conflicting signals I'm downplaying?" will always raise doubt. The scoring system replaces this — if the score is >= 65 with critical requirements met, the setup qualifies regardless of narrative doubt.

### Change 4: Displacement Tolerance Band
**Before:** "body >= 1.5x the 20-period average body size" (hard binary)
**After:** Strong (>= 1.5x): full 15 points. Moderate (1.2-1.5x): 10 points. Weak (< 1.2x): 0 points.
**Why:** The 1.5x threshold was the #2 rejection reason (67-75% of rejected winning trades). A displacement at 1.4x is statistically indistinguishable from 1.5x but currently fails the hard gate. The tolerance band allows moderate displacement to qualify when zone quality is high.

### Change 5: "Near" Quantified
**Before:** "Current price has pulled back into or near the OB zone" (undefined)
**After:** "within the OB zone (15 points) OR within 1x M15 ATR(14) of the nearest zone boundary (10 points)"
**Why:** This was the #1 rejection reason (82% of rejected winning trades). Sonnet 4 interprets "near" with discretion ($14 for a $2700 instrument). Sonnet 4.6 interprets it as "touching." Quantifying removes interpretation ambiguity. 1 ATR is a meaningful proximity measure that scales with instrument volatility.

### Change 6: Calibration Note Added
**Before:** No guidance on expected CANDIDATE rate
**After:** "Approximately 40-60% of setups reaching this evaluation qualify as CANDIDATE" + error asymmetry explanation
**Why:** Without an anchor, the model has no reference for how selective to be. The calibration note establishes expected behavior. The error asymmetry section counters the 6 existing conservatism directives by explicitly noting that over-rejection has a cost.

### Change 7: Grade Gate Lowered (via scoring)
**Before:** "Only A+ and A setups qualify as CANDIDATE" / "B+ or below: DO NOT OUTPUT AS CANDIDATE"
**After:** Score >= 65 qualifies (equivalent to B+ range in old grading)
**Why:** T2c data shows B+ trades have 77% WR — the BEST performers. The current system kills them. The scoring threshold of 65 allows strong setups that have one moderate-but-acceptable criterion to pass.

### Change 8: Symmetric Conviction
**Before:** "If the setup is genuinely weak, say NO_TRADE rather than hedging a CANDIDATE" (one-directional)
**After:** Added: "If the setup genuinely meets criteria (score >= 65 + critical requirements pass), output CANDIDATE. Do not invent additional concerns beyond the scoring framework."
**Why:** The current prompt has 6 directives that push toward NO_TRADE and zero that push toward CANDIDATE. This creates a massive asymmetric bias. Adding the symmetric instruction tells the model: trust the score.

### Change 9: "When signals conflict" Reframed
**Before:** "When signals conflict, default to NO_TRADE"
**After:** Removed. The scoring system handles conflicts naturally — conflicting signals reduce the score but don't auto-kill.
**Why:** Signals always conflict in real markets. This rule gave the model a universal escape hatch to reject any trade.

### Change 10: Output Length Guidance
**Before:** "Keep each reasoning section to 1-2 sentences" (but no total cap — Sonnet 4.6 outputs 1,200+ tokens)
**After:** "NO_TRADE: under 400 tokens. CANDIDATE: under 700 tokens."
**Why:** More analysis = more opportunities to find reasons to reject (analysis paralysis). Sonnet 4 outputs ~500 tokens. Sonnet 4.6 outputs 1,200+. The cap forces concise, decision-focused reasoning.

---

## THE RE-ENGINEERED SYSTEM PROMPT

The following is the EXACT system prompt text to send to the API. Template variables (`{kz_display}`, `{sl_min_display}`, `{zone_max_display}`) should be replaced with the values from the original batch prompt for each trade (or use XAUUSD defaults: London 07:00-10:30 / NY 13:00-17:00, SL min $5.00, zone max $15).

For non-XAUUSD trades, use the kill zone and SL values from that instrument's batch prompt.

```text
You are a quantitative setup evaluator for an order block retest trading system. Your task is to determine whether the current M15 candle meets the criteria for an entry setup based on price structure, zone quality, and trigger confirmation.

Your evaluation must be DATA-DRIVEN — based on the specific price levels, structural breaks, and zone positions in the Market State Object provided. Do not infer, assume, or narrativize beyond what the data shows.

## Kill Zone Windows
{kz_display}
You will be told which window is being evaluated.

## CALIBRATION
Based on validated historical performance across 300+ trades:
- Approximately 40-60% of setups reaching this evaluation qualify as CANDIDATE.
- The system's edge comes from order block zone continuation mechanics (~65-70% win rate on qualifying zones). This is a STATISTICAL edge — your job is to verify the setup meets structural criteria, not to predict the individual trade's outcome.
- Over-rejection is as costly as over-acceptance. Rejecting a qualifying setup costs the system +0.20R expected value. Both false positives and false negatives have real costs.
- If you find yourself rejecting more than 70% of evaluated setups, recalibrate — your thresholds are likely too strict for the statistical edge this system exploits.

## CRITICAL REQUIREMENTS (any failure → NO_TRADE)
These are hard gates. If any fails, do not evaluate further — output a minimal NO_TRADE JSON.

C1. DIRECTIONAL BIAS: Establish directional bias from available timeframes. If the most recent D1 structural break (BOS or CHoCH) establishes a clear direction, use D1 as the primary bias. If D1 has no recent structural break or is ambiguous, use H4 direction as the primary reference. If H4 is also unclear, require at least two of D1/H4/H1 to agree on direction. If no directional agreement exists → NO_TRADE.

C2. H4 ALIGNMENT: H4 must not ACTIVELY OPPOSE the established bias direction. H4 ranging or unclear is acceptable when D1 is clearly directional — H4 merely needs to not contradict. Only a clear H4 structural bias in the OPPOSITE direction to D1 triggers failure.

C3. DIRECTION MATCH: Trade direction must align with the established bias. LONG only if bias is bullish, SHORT only if bias is bearish.

## QUALIFYING CRITERIA (evaluate and score)
Score each factor. Decision is based on total score + critical requirements.

Q1. H1 STRUCTURAL BREAK: H1 should show a confirmed structural break in the trade direction.
  - BOS (break of protected swing in trend direction): 15 points
  - CHoCH (shift from opposing to aligned direction): 12 points
  - No confirmed break in aligned direction: 0 points

Q2. UNMITIGATED ORDER BLOCK: An unmitigated H1 OB exists from the impulse that caused the structural break. Check timeframes.H1.order_blocks where mitigated=false.
  - Present and from the relevant impulse: 20 points
  - Not present or already mitigated: 0 points

Q3. PRICE PROXIMITY TO ZONE: How close is the current price to the OB zone?
  - Price within the OB zone boundaries (between zone high and low): 15 points
  - Price within 1x M15 ATR(14) of the nearest zone boundary: 10 points
  - Price beyond 1 ATR from the zone: 0 points

Q4. PREMIUM/DISCOUNT POSITION: Is the OB on the correct side of the impulse?
  - Longs: OB in discount (below 50% of impulse) = 10 points
  - Shorts: OB in premium (above 50% of impulse) = 10 points
  - At equilibrium (45-55% of impulse): 5 points
  - Wrong side: 0 points

Q5. M15 CONFIRMATION: Does M15 show CHoCH + displacement in the trade direction?
  - CHoCH detected = body close beyond the most recent protected M15 swing in the trade direction
  - Strong displacement: candle body >= 1.5x the 20-period average body = 15 points
  - Moderate displacement: candle body 1.2-1.5x average body = 10 points
  - Weak or no displacement (< 1.2x or no CHoCH): 0 points

Q6. MINIMUM RISK-REWARD: Risk-to-reward to TP1 after applying SL buffer.
  - RR >= 1.5: 10 points
  - RR < 1.5: 0 points

Q7. STOP LOSS ADEQUACY: SL beyond the OB extreme + ATR buffer.
  - SL >= 1.5x M15 ATR(14) AND >= {sl_min_display}: 5 points
  - SL insufficient: 0 points

BONUS QUALITY FACTORS:
  - Zone is first touch (not previously retested): +5 points
  - Displacement created an FVG (gap between candle bodies): +3 points
  - Impulse leg is compact (7 or fewer H1 candles): +2 points

Maximum possible score: 100.

## DECISION THRESHOLDS
- Score >= 65 AND all critical requirements (C1-C3) pass → CANDIDATE
- Score 45-64 → WAIT (setup developing, specific trigger pending)
- Score < 45 OR any critical requirement fails → NO_TRADE

## ZONE FRESHNESS RULE (HARD — applies to both frameworks)
Only trade the FIRST retest of an order block zone. If price has previously entered this OB zone and been rejected or continued, the zone is CONSUMED — do not trade it again. First-touch continuation rate: 72.7% (n=23,575); subsequent touches: 31.5% (n=82,572). An OB marked as mitigated in the MSO must NOT generate a CANDIDATE.

## BREAKER BLOCK RETEST (alternative framework)
If the OB Retest does not reach score >= 65, also evaluate the Breaker Block Retest:

BR1. An unretested H1 breaker block exists (check breaker_blocks where is_retested=false). Breaker direction must align with the established bias. (20 points for Q2 equivalent)
BR2. Price at or within 1x M15 ATR of the breaker zone. (15/10/0 for Q3)
BR3. Original OB was broken with displacement, not slow grind. (contributes to Q1 score)
BR4. Zone width < {zone_max_display}. If wider, reduce Q2 score by 10.
BR5. M15 CHoCH + displacement at the zone. (same scoring as Q5)
BR6. Entry within the breaker zone. SL beyond zone extreme. TP1 = EXACTLY 1.5x SL distance from entry. Must satisfy Q7 minimum.

Score the breaker block using the same scoring table (substitute breaker zone for OB zone in Q2-Q4). If both frameworks score >= 65, pick the higher score. Report both in frameworks_evaluated.

## TARGETS
TP1 MUST be EXACTLY 1.5x SL distance from entry:
  - LONG: TP1 = entry + 1.5 x (entry - SL)
  - SHORT: TP1 = entry - 1.5 x (SL - entry)
Do not deviate from 1.5x. TP2 and TP3 are optional (set to 0 if not applicable).

## CONFIDENCE SCORE
Map your evaluation score to confidence:
  - Score 65-74 → confidence 65-72
  - Score 75-84 → confidence 73-80
  - Score 85+ → confidence 81-90
Show your score breakdown in the confidence_computation field, e.g.: "Q1=15 Q2=20 Q3=10 Q4=10 Q5=15 Q6=10 Q7=5 +zone_first=5 = 90 → conf 85"

## SETUP GRADE
Map score to grade for backward compatibility:
  - Score 85+: A+
  - Score 75-84: A
  - Score 65-74: B+
  - Score 50-64: B
  - Score < 50: C

## DECISION INTEGRITY
- If the score is >= 65 and all critical requirements pass, output CANDIDATE. Do not invent additional concerns beyond the scoring framework. Trust the score.
- If the score is < 45 or a critical requirement fails, output NO_TRADE.
- Base your evaluation ONLY on the data in the Market State Object and the scoring criteria above. No external assumptions, no narrative interpretation.

## OUTPUT RULES
- Respond with ONLY valid JSON matching the schema below. No preamble, no markdown fences.
- For NO_TRADE: state which requirement failed or the score breakdown. Total response under 500 tokens.
- For CANDIDATE: include full score breakdown and trade parameters. Total response under 800 tokens.
- If C1 or C2 fail, output a minimal JSON with only: decision, kill_zone, framework="none", no_trade_reason. Do NOT evaluate scoring criteria when bias is not established.

## Data Grounding Rules
- Base ALL analysis on the price data in the Market State Object. If a price level, swing, or pattern is not in the MSO, it does not exist.
- If you cannot determine a structure direction with high confidence from the data, state "unclear" — do not force a classification.
- Respond with ONLY valid JSON. Your response MUST start with { and end with }.

## Internal Consistency Rules
- If decision is CANDIDATE, m15_confirmation.choch_detected MUST be true. A CANDIDATE requires confirmed M15 confirmation.
- If h1_setup.poi_identified is FALSE or h1_setup.poi_type is "none", the decision MUST be NO_TRADE.

## Output Schema
```json
{
  "timestamp_utc": "<ISO-8601 timestamp of the candle being evaluated>",
  "model_used": "<model identifier>",
  "decision": "NO_TRADE | CANDIDATE | WAIT",
  "confidence_score": <0-100 integer>,
  "confidence_computation": "<score breakdown, e.g. Q1=15 Q2=20 Q3=10 ... = 80 → conf 78>",
  "framework": "ob_retest | breaker_retest | none",
  "kill_zone": "london | ny",
  "frameworks_evaluated": {
    "ob_retest": {"qualified": <bool>, "score": <int>, "reason": "<summary>"},
    "breaker_retest": {"qualified": <bool>, "score": <int>, "reason": "<summary>"}
  },
  "reasoning": {
    "daily_bias": {
      "direction": "bullish | bearish | ranging",
      "confidence": "high | medium | low",
      "protected_swing_level": <float>,
      "explanation": "<1 sentence>"
    },
    "h4_alignment": {
      "aligned": <bool>,
      "h4_pois_identified": ["<OB/FVG>"],
      "explanation": "<1 sentence>"
    },
    "h1_setup": {
      "poi_identified": <bool>,
      "poi_type": "OB | FVG | liquidity_zone | none",
      "poi_price_level": <float>,
      "zone": "premium | discount | neutral",
      "fib_retracement_pct": <float>,
      "causing_event_type": "BOS | CHoCH | unknown",
      "explanation": "<1 sentence>"
    },
    "liquidity_sweep": {
      "detected": <bool>,
      "pool_type": "<type or none>",
      "sweep_quality": "clean | messy | ambiguous",
      "sweep_price": <float>,
      "explanation": "<1 sentence>"
    },
    "m15_confirmation": {
      "choch_detected": <bool>,
      "displacement_quality": "strong | medium | weak | none",
      "displacement_candle_body_vs_avg_ratio": <float>,
      "explanation": "<1 sentence>"
    },
    "similar_historical_setups_considered": [],
    "setup_grade": "A+ | A | B+ | B | C",
    "overall_reasoning": "<2-3 sentences max>"
  },
  "trade_parameters": null,
  "no_trade_reason": "<if NO_TRADE>",
  "wait_reason": "<if WAIT>"
}
```

When decision is "CANDIDATE", trade_parameters MUST be:
```json
{
  "direction": "LONG | SHORT",
  "entry_price": <float>,
  "stop_loss": <float>,
  "sl_buffer_applied": <float>,
  "take_profit_1": <float>,
  "take_profit_2": <float>,
  "take_profit_3": <float>,
  "risk_reward_ratio": <float>,
  "position_size_lots": 0.01
}
```
```

---

## TEST METHODOLOGY

### Data Source
Same 121 MSOs from T2c (originally from T2b, which extracted them from batch data). Each MSO contains a system prompt + user message. For Phase 2A, the system prompt is REPLACED with the new prompt above. The user message (containing the MSO market data) is kept UNCHANGED, including session memory where present.

### Why keep session memory in Phase 2A
Phase 2A isolates the SYSTEM PROMPT change only. Session memory is in the user message. Changing both simultaneously would confound the result. Phase 2C (separate test) will test memory removal.

### Test Configurations

| Test | Model | Effort | max_tokens | System Prompt |
|------|-------|--------|------------|---------------|
| P2A-1 | claude-sonnet-4-20250514 (Sonnet 4) | none | 2000 | NEW (above) |
| P2A-2 | claude-sonnet-4-6 (Sonnet 4.6) | high | 2000 | NEW (above) |
| P2A-3 | claude-sonnet-4-6 (Sonnet 4.6) | max | 2000 | NEW (above) |

**max_tokens = 2000** for all tests (matches the original batch config, eliminates the T2c confounder where max_tokens was 4096). The new prompt's output length guidance (500 for NO_TRADE, 800 for CANDIDATE) keeps responses well within 2000 tokens.

**temperature = 0** for all tests (matches all prior experiments).

### Comparison Matrix (against prior results, CORRECTED baselines)

| Config | CR | WR | CR*WR | Source |
|--------|----|----|-------|--------|
| Sonnet 4 batch (old prompts) | 55.8% | 61.1% | 0.341 | T2b data |
| Sonnet 4.6 medium (old prompts) | 13.2% | 50.0% | 0.066 | T2c medium re-run |
| Sonnet 4.6 high (old prompts) | 17.4% | 52.4% | 0.091 | T2c high |
| Sonnet 4.6 max (old prompts) | 16.5% | 60.0% | 0.099 | T2c max |
| **P2A-1: Sonnet 4 (NEW prompt)** | ? | ? | ? | This test |
| **P2A-2: Sonnet 4.6 high (NEW prompt)** | ? | ? | ? | This test |
| **P2A-3: Sonnet 4.6 max (NEW prompt)** | ? | ? | ? | This test |

### Key Comparisons
1. **P2A-1 vs Sonnet 4 batch**: Does the new prompt improve Sonnet 4? (Prompt effect on old model)
2. **P2A-2 vs T2c high**: Does the new prompt fix Sonnet 4.6? (Prompt effect on new model)
3. **P2A-1 vs P2A-2**: Clean model comparison on IDENTICAL new prompt (first truly controlled comparison)
4. **P2A-2 vs P2A-3**: Does effort level matter with the new prompt?

---

## SCRIPT STRUCTURE

Each test runs as an independent Python script. All three can run in parallel.

```python
#!/usr/bin/env python3
"""Phase 2A — Prompt Re-Engineering Test: [CONFIG NAME]"""

import json, glob, time, csv, os
from pathlib import Path
from anthropic import Anthropic

# ── CONFIG ──────────────────────────────────────────────
MODEL = "..."          # "claude-sonnet-4-20250514" or "claude-sonnet-4-6"
EFFORT = None          # None, "high", or "max"
MAX_TOKENS = 2000
TEMPERATURE = 0
TEST_NAME = "P2A_..."  # "P2A_s4_new", "P2A_s46_high_new", "P2A_s46_max_new"

# ── NEW SYSTEM PROMPT (paste the full text from above) ──
NEW_SYSTEM_PROMPT = """..."""  # The exact text from the "RE-ENGINEERED SYSTEM PROMPT" section

# ── LOAD MSOs ───────────────────────────────────────────
# Same loading logic as T2c scripts
DATA_DIR = Path("knowledge_base_backtest/batch_api")
ENTRY_CSV = Path("research/academic_pipeline/data/entry_engineering_dataset.csv")

# Load the 121 T1 trade IDs and outcomes from entry_engineering_dataset.csv
import pandas as pd
df = pd.read_csv(ENTRY_CSV)
trade_ids = set(df["trade_id"].tolist())
outcomes = dict(zip(df["trade_id"], zip(df["outcome"], df["r_multiple"], df["win"])))

# Load batch prompts — extract user_message only (system prompt is REPLACED)
msos = {}
for fp_path in sorted(DATA_DIR.glob("*_full_prompts.json")):
    with open(fp_path) as f:
        records = json.load(f)
    for rec in records:
        tid = rec.get("custom_id", "")
        if tid in trade_ids and tid not in msos:  # First match wins
            prompt_data = rec.get("prompt", {})
            # Extract USER message only — system prompt is replaced
            user_msg = prompt_data.get("user_message", "")
            # Extract kill zone and instrument info from the original system prompt
            # for template variable substitution
            orig_system = ""
            sys_field = prompt_data.get("system", [])
            if isinstance(sys_field, list) and sys_field:
                orig_system = sys_field[0].get("text", "")
            elif isinstance(sys_field, str):
                orig_system = sys_field
            
            msos[tid] = {
                "trade_id": tid,
                "user_message": user_msg,
                "original_system_prompt": orig_system,  # For reference only
                "date": rec.get("date", ""),
                "candle_time": rec.get("candle_time", ""),
                "kill_zone": rec.get("kill_zone", ""),
            }

print(f"Loaded {len(msos)} MSOs (target: 121)")

# ── SUBSTITUTE TEMPLATE VARIABLES ───────────────────────
# Detect instrument from trade_id to set correct thresholds
def get_prompt_for_trade(trade_id):
    """Return the new system prompt with correct template variables."""
    prompt = NEW_SYSTEM_PROMPT
    
    symbol = "XAUUSD"  # default
    if "gbpusd" in trade_id:
        symbol = "GBPUSD"
    elif "gbpjpy" in trade_id:
        symbol = "GBPJPY"
    elif "usdjpy" in trade_id:
        symbol = "USDJPY"
    elif "us30" in trade_id:
        symbol = "US30"
    
    # KZ display
    KZ_MAP = {
        "XAUUSD": "- London Open: 07:00-10:30 UTC\n- NY Open: 13:00-17:00 UTC (skip 13:00-13:15)",
        "GBPUSD": "- London Open: 07:00-12:00 UTC\n- NY Open: 13:00-15:30 UTC",
        "GBPJPY": "- London Open: 07:00-09:30 UTC\n- NY Open: 13:00-15:30 UTC",
        "USDJPY": "- London Open: 07:00-09:30 UTC\n- NY Open: 13:00-15:30 UTC",
        "US30": "- London Open: 08:00-10:30 UTC\n- NY Open: 13:30-16:00 UTC",
    }
    prompt = prompt.replace("{kz_display}", KZ_MAP.get(symbol, KZ_MAP["XAUUSD"]))
    
    # SL min
    SL_MAP = {"XAUUSD": "$5.00", "GBPUSD": "50 pips", "GBPJPY": "50 pips",
              "USDJPY": "50 pips", "US30": "50 points"}
    prompt = prompt.replace("{sl_min_display}", SL_MAP.get(symbol, "$5.00"))
    
    # Zone max
    ZM_MAP = {"XAUUSD": "$15", "GBPUSD": "150 pips", "GBPJPY": "150 pips",
              "USDJPY": "150 pips", "US30": "150 points"}
    prompt = prompt.replace("{zone_max_display}", ZM_MAP.get(symbol, "$15"))
    
    return prompt

# ── RUN EVALUATIONS ─────────────────────────────────────
client = Anthropic()
results = []
cost_log = []
total_cost = 0.0

for i, (tid, mso) in enumerate(sorted(msos.items()), 1):
    system_prompt = get_prompt_for_trade(tid)
    
    kwargs = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "system": system_prompt,
        "messages": [{"role": "user", "content": mso["user_message"]}],
    }
    
    # Add effort parameter for Sonnet 4.6
    if EFFORT is not None:
        # Note: effort goes in the API request, not in messages
        # Check current Anthropic SDK syntax for output_config
        pass  # Implementation depends on SDK version — see T2c scripts for reference
    
    try:
        response = client.messages.create(**kwargs)
        
        # Parse response
        text = response.content[0].text
        # Try to extract JSON
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON in text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(text[start:end])
            else:
                parsed = {"decision": "ERROR", "error": "No valid JSON in response"}
        
        # Extract key fields
        decision = parsed.get("decision", "ERROR")
        confidence = parsed.get("confidence_score", 0)
        grade = parsed.get("reasoning", {}).get("setup_grade", "C")
        framework = parsed.get("framework", "none")
        
        # Cost tracking
        in_tok = response.usage.input_tokens
        out_tok = response.usage.output_tokens
        cost = (in_tok * 3.0 / 1_000_000) + (out_tok * 15.0 / 1_000_000)
        total_cost += cost
        
        outcome, r_mult, win = outcomes.get(tid, ("UNKNOWN", 0, 0))
        
        results.append({
            "trade_id": tid,
            "candle_time": mso.get("candle_time", ""),
            "symbol": "XAUUSD" if "xauusd" in tid else
                      "GBPUSD" if "gbpusd" in tid else
                      "GBPJPY" if "gbpjpy" in tid else
                      "USDJPY" if "usdjpy" in tid else
                      "US30" if "us30" in tid else "UNKNOWN",
            "kill_zone": mso.get("kill_zone", ""),
            "outcome": outcome,
            "r_multiple": r_mult,
            "win": win,
            "original_decision": "CANDIDATE",  # All 121 were originally executed
            "original_confidence": 0,
            "new_decision": decision,
            "new_confidence": confidence,
            "new_setup_grade": grade,
            "new_framework": framework,
            "new_response": parsed,
        })
        
        cost_log.append({
            "trade_id": tid,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "cost": cost,
            "cumulative_cost": total_cost,
        })
        
        print(f"  [{i}/121] {tid} → {decision} (grade={grade}, conf={confidence}) (${total_cost:.4f})")
        
    except Exception as e:
        print(f"  [{i}/121] {tid} → ERROR: {e}")
        results.append({
            "trade_id": tid,
            "outcome": outcomes.get(tid, ("UNKNOWN",))[0],
            "new_decision": "ERROR",
            "error": str(e),
        })
    
    # Rate limiting
    time.sleep(0.5)

# ── COMPUTE SUMMARY STATISTICS ──────────────────────────
n_total = len(results)
n_cand = sum(1 for r in results if r.get("new_decision") == "CANDIDATE")
n_no_trade = sum(1 for r in results if r.get("new_decision") == "NO_TRADE")
n_wait = sum(1 for r in results if r.get("new_decision") == "WAIT")
n_other = n_total - n_cand - n_no_trade - n_wait

cand_results = [r for r in results if r.get("new_decision") == "CANDIDATE"]
cand_wins = sum(1 for r in cand_results if r.get("outcome") == "WIN")
cand_wr = cand_wins / n_cand if n_cand > 0 else 0
cr = n_cand / n_total if n_total > 0 else 0
cr_wr = cr * cand_wr

# Lost trades analysis
lost = [r for r in results if r.get("new_decision") != "CANDIDATE" and r.get("outcome") in ("WIN", "LOSS")]
lost_wins = sum(1 for r in lost if r.get("outcome") == "WIN")
lost_wr = lost_wins / len(lost) if lost else 0

# Grade distribution
from collections import Counter
grades = Counter(r.get("new_setup_grade", "?") for r in results)
confs = Counter(r.get("new_confidence", 0) for r in cand_results)

# Average tokens
avg_in = sum(c["input_tokens"] for c in cost_log) / len(cost_log) if cost_log else 0
avg_out = sum(c["output_tokens"] for c in cost_log) / len(cost_log) if cost_log else 0

summary = {
    "candidate_rate": round(cr, 4),
    "wr": round(cand_wr, 4),
    "cr_wr": round(cr_wr, 4),
    "n_candidate": n_cand,
    "n_no_trade": n_no_trade,
    "n_wait": n_wait,
    "n_other": n_other,
    "n_total": n_total,
    "lost_trades_n": len(lost),
    "lost_trades_wr": round(lost_wr, 4),
    "avg_confidence": round(sum(r.get("new_confidence", 0) for r in cand_results) / n_cand, 1) if n_cand else 0,
    "avg_input_tokens": round(avg_in, 0),
    "avg_output_tokens": round(avg_out, 0),
    "total_cost": round(total_cost, 4),
}

# ── SAVE OUTPUTS ────────────────────────────────────────
OUT_DIR = Path("research/academic_pipeline/data")
REPORT_DIR = Path("research/academic_pipeline/results")

# Raw JSON
with open(OUT_DIR / f"{TEST_NAME}_results.json", "w") as f:
    json.dump({"metadata": {"model": MODEL, "effort_level": str(EFFORT), "prompt": "phase2a_reengineered",
                             "n_msos": n_total, "total_cost": total_cost, "date": "2026-04-12",
                             "max_tokens": MAX_TOKENS},
               "summary": summary,
               "distributions": {"confidence": dict(confs), "grade": dict(grades)},
               "rows": results}, f, indent=2, default=str)

# Cost log CSV
with open(OUT_DIR / f"{TEST_NAME}_cost_log.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["trade_id", "input_tokens", "output_tokens", "cost", "cumulative_cost"])
    w.writeheader()
    w.writerows(cost_log)

# Markdown report
report = f"""# Phase 2A: {TEST_NAME}

**Date:** 2026-04-12
**Model:** {MODEL}
**Effort:** {EFFORT or 'none'}
**Prompt:** Phase 2A re-engineered (scored evaluation, no self-check, quantified tolerances)
**N MSOs:** {n_total}
**Total cost:** ${total_cost:.4f}
**max_tokens:** {MAX_TOKENS}

## Results

| Metric | Value |
|--------|-------|
| CANDIDATE rate | {cr:.1%} ({n_cand}/{n_total}) |
| WR (of CANDIDATEs) | {cand_wr:.1%} (n={n_cand}) |
| CR x WR | {cr_wr:.4f} |
| Lost trades WR | {lost_wr:.1%} (n={len(lost)}) |
| WAIT count | {n_wait} |
| Avg output tokens | {avg_out:.0f} |
| Total cost | ${total_cost:.4f} |

## Comparison to T2c (old prompt)

| Config | CR | WR | CR*WR |
|--------|----|----|-------|
| Sonnet 4 batch (old prompts) | 55.8% | 61.1% | 0.341 |
| T2c S4.6 high (old prompt) | 17.4% | 52.4% | 0.091 |
| T2c S4.6 max (old prompt) | 16.5% | 60.0% | 0.099 |
| **{TEST_NAME} (NEW prompt)** | **{cr:.1%}** | **{cand_wr:.1%}** | **{cr_wr:.4f}** |

## Grade Distribution
{dict(grades)}

## Confidence Distribution (CANDIDATEs)
{dict(confs)}

## Score Breakdown
TODO: Extract score breakdowns from confidence_computation fields

## Raw Decision Log
| trade_id | outcome | new_decision | confidence | grade |
|----------|---------|--------------|------------|-------|
"""

for r in results:
    report += f"| {r['trade_id'][:40]} | {r.get('outcome','?')} | {r.get('new_decision','?')} | {r.get('new_confidence',0)} | {r.get('new_setup_grade','?')} |\n"

with open(REPORT_DIR / f"{TEST_NAME}_results_v1.md", "w") as f:
    f.write(report)

print(f"\nDone. CR={cr:.1%}, WR={cand_wr:.1%}, CR*WR={cr_wr:.4f}")
print(f"Cost: ${total_cost:.4f}")
print(f"Results: {OUT_DIR / TEST_NAME}_results.json")
print(f"Report: {REPORT_DIR / TEST_NAME}_results_v1.md")
```

### Script Variants
Create three scripts by setting CONFIG at the top:

**P2A_s4_new.py:**
```python
MODEL = "claude-sonnet-4-20250514"
EFFORT = None
TEST_NAME = "P2A_s4_new"
```

**P2A_s46_high_new.py:**
```python
MODEL = "claude-sonnet-4-6"
EFFORT = "high"
TEST_NAME = "P2A_s46_high_new"
```
Add to kwargs: check T2c_effort_high.py for the correct effort parameter syntax.

**P2A_s46_max_new.py:**
```python
MODEL = "claude-sonnet-4-6"
EFFORT = "max"
TEST_NAME = "P2A_s46_max_new"
```
Add to kwargs: check T2c_effort_max.py for the correct effort parameter syntax.

**IMPORTANT:** Copy the effort parameter implementation from the T2c scripts exactly. The effort parameter uses `output_config={"effort": level}` in the API call. Check `T2c_effort_high.py` for the working implementation.

---

## DECISION GATES (pre-committed)

### Primary Gate: Does the new prompt fix Sonnet 4.6?
Compare P2A-2 (S4.6 high, new prompt) against T2c high (S4.6 high, old prompt):

| Outcome | Criteria | Action |
|---------|----------|--------|
| **CR >= 35% AND WR >= 58%** | Major improvement, viable for production | Proceed to implementation: deploy new prompt + Sonnet 4.6 |
| **CR 25-35% AND WR >= 55%** | Meaningful improvement, not sufficient alone | Combine with Phase 2C (memory removal) for additional +55% CR |
| **CR < 25% OR WR < 55%** | New prompt insufficient for S4.6 | Lock Sonnet 4 as model; apply new prompt to Sonnet 4 for its frequency benefit |

### Secondary Gate: Model comparison (P2A-1 vs P2A-2)
| Outcome | Criteria | Action |
|---------|----------|--------|
| **P2A-2 CR within 10pp of P2A-1** | New prompt equalizes models | Either model viable — choose S4.6 (current, supported) |
| **P2A-1 CR > P2A-2 CR by >15pp** | Model difference persists despite prompt fix | Lock Sonnet 4 until S4.6 calibration improves |
| **P2A-2 CR > P2A-1 CR** | S4.6 actually benefits MORE from new prompt | Strong signal for S4.6 + new prompt |

### Tertiary Gate: Effort level (P2A-2 vs P2A-3)
| Outcome | Criteria | Action |
|---------|----------|--------|
| **Within 5pp CR and 3pp WR** | Effort doesn't matter (as in T2c) | Use high effort (cheaper) |
| **Max significantly better** | More compute helps with new prompt | Use max effort (still cheap — $0.61/month) |

### Quality Checks
- Lost trades WR: If > 65%, still over-rejecting. If < 55%, filtering correctly.
- Grade inversion: Check if B+ still has higher WR than A+. If yes, grading is still miscalibrated.
- Score distribution: Should be spread across 30-90, not clustered. If clustered at one value, scoring rubric needs adjustment.
- CANDIDATE overlap with T2c: How many new prompt CANDIDATEs overlap with old prompt CANDIDATEs? High overlap + more = prompt unlocked additional trades. Low overlap = prompt changed judgment entirely (investigate).

---

## OUTPUT FILES

| File | Content |
|------|---------|
| `research/academic_pipeline/data/P2A_s4_new_results.json` | Raw results, Sonnet 4 |
| `research/academic_pipeline/data/P2A_s46_high_new_results.json` | Raw results, S4.6 high |
| `research/academic_pipeline/data/P2A_s46_max_new_results.json` | Raw results, S4.6 max |
| `research/academic_pipeline/results/P2A_s4_new_results_v1.md` | Report, Sonnet 4 |
| `research/academic_pipeline/results/P2A_s46_high_new_results_v1.md` | Report, S4.6 high |
| `research/academic_pipeline/results/P2A_s46_max_new_results_v1.md` | Report, S4.6 max |
| `research/academic_pipeline/data/P2A_*_cost_log.csv` | Cost tracking |

---

## CONSTRAINTS FOR EXECUTION AGENTS

1. **Do NOT modify the new system prompt.** Use it exactly as written above. Template variables must be substituted but the text is otherwise frozen.
2. **Do NOT modify user messages.** Keep them exactly as extracted from batch data, including session memory.
3. **Use max_tokens=2000** for all tests (NOT 4096 as in T2c).
4. **Use temperature=0** for all tests.
5. **Copy effort parameter implementation from T2c scripts** — do not guess the syntax.
6. **Save ALL responses** including full JSON, not just summary statistics.
7. **Track cost per call** in the cost log CSV.
8. **Do NOT rerun failed calls** — log them as ERROR and continue.
9. **Rate limit:** 0.5s delay between calls minimum.
10. **Budget cap:** $6 per test. If cost exceeds $6, stop and report partial results.

---

## PREREQUISITES

```bash
pip install anthropic pandas  # Should already be installed from T2c
```

Verify batch data exists:
```bash
ls knowledge_base_backtest/batch_api/*_full_prompts.json | wc -l  # Should be 18
ls research/academic_pipeline/data/entry_engineering_dataset.csv  # Must exist
```

Verify T2c effort scripts for reference:
```bash
ls research/academic_pipeline/T2c_effort_high.py  # Copy effort param syntax from here
```

---

## PRESSURE TEST LOG

### Issues Found and Fixed Before Delivery

1. **Issue:** max_tokens=4096 was an uncontrolled variable in T2c. **Fix:** All P2A tests use max_tokens=2000 (matches original batch config).

2. **Issue:** T2c used 10+ different batch system prompts across 121 trades. **Fix:** P2A uses ONE standardized new prompt for all 121 trades. This eliminates prompt variation as a confounder.

3. **Issue:** Template variables (kill zones, SL mins) differ by instrument. **Fix:** Script detects instrument from trade_id and substitutes correct values.

4. **Issue:** Some batch user messages include session memory, others don't. **Fix:** Keep user messages unchanged. Phase 2C will test memory removal separately.

5. **Issue:** The scoring system might produce scores that cluster at specific values (like the current confidence rubber stamp at 80). **Mitigation:** The score has 10 independent components across a 0-100 range, making clustering unlikely. But verify in results — if >50% of trades score exactly the same, the rubric needs adjustment.

6. **Issue:** The output JSON schema adds a "score" field to frameworks_evaluated that the current system might not parse. **Fix:** Score is inside frameworks_evaluated (an informational field), not in the main decision fields. The system parses decision, framework, trade_parameters, setup_grade, and confidence_score — all of which are present and compatible.

7. **Issue:** The scoring threshold of 65 is arbitrary. **Mitigation:** Pre-committed decision gates evaluate the results regardless of the threshold's accuracy. If 65 produces CR of 80% (too permissive), we know to raise it. If it produces CR of 20% (still too strict), we know to lower it. The first test IS the calibration run.

8. **Issue:** "Moderate displacement (1.2-1.5x)" might let through genuinely weak confirmations. **Mitigation:** Moderate displacement only scores 10 (vs 15 for strong). A setup needs 55+ points from other criteria to reach the 65 threshold with moderate displacement. This means zone quality must be high to compensate — exactly the behavior we want.

---

*Prompt designed: April 12, 2026*
*Strategic Research Advisor*
*Total changes: 10 conservatism fixes + 4 new elements*
*Expected test cost: ~$12 for all 3 configurations*
