# Codebase Audit — 2026-03-31

## 1. Project Structure

```
src/
  components/     # Core pipeline components
    market_state.py      (633 lines) — Component 2: deterministic MSO builder
    primary_analyzer.py  (409 lines) — Component 3A: AI reasoning engine
    knowledge_base.py    (485 lines) — Component 5: KB layer management
    debate.py            (368 lines) — Component 3B: bull/bear debate
    adaptive_review.py   (584 lines) — Component 7: rule adaptation
    dashboard.py         (159 lines) — Monitoring dashboard
    monitoring.py        (183 lines) — Metrics/alerting
    orchestrator.py      (7 lines)   — Stub
    data_ingestion.py    (5 lines)   — Stub
    execution.py         (6 lines)   — Stub
  models/
    market_state_models.py  (153 lines) — Pydantic MSO schema
    analysis_models.py      (105 lines) — PA output schema
    trade_models.py         (358 lines) — Trade/session models
    debate_models.py        (69 lines)  — Debate models
  prompts/
    primary_analyzer_prompt.py  (405 lines) — PA system + user prompt
    judge_prompt.py             (149 lines) — Debate judge
    bull_agent_prompt.py        (80 lines)
    bear_agent_prompt.py        (84 lines)
    postmortem_prompt.py        (67 lines)
  utils/
    file_io.py       (53 lines)
    time_utils.py    (91 lines)
    validation.py    (59 lines)
  llm_backend.py   (390 lines) — API/subscription routing

scripts/
  batch_backtest.py          (1038 lines) — Batch API backtester
  backtest_runner.py         (1115 lines) — Sequential backtester
  historical_data_loader.py  (783 lines)  — CSV→MSO replay engine
  comprehensive_analysis.py  (1347 lines) — Analysis script (Session 0)
  session1_deep_analysis.py  (923 lines)  — Deep analysis (Session 1)
  test_live_api.py           (388 lines)
  verify_billing.py          (56 lines)

tests/   262 tests, ALL PASSING
  test_market_state.py       (571 lines)
  test_integration.py        (867 lines)
  test_knowledge_base.py     (563 lines)
  test_adaptive_review.py    (532 lines)
  test_batch_backtest.py     (413 lines)
  test_prompts.py            (405 lines)
  test_primary_analyzer.py   (362 lines)
  test_debate.py             (463 lines)
  test_monitoring.py         (347 lines)
  test_llm_backend.py        (302 lines)
  test_lifecycle.py          (185 lines)
  test_safety_checks.py      (185 lines)

config/agent_config.yaml   (96 lines)
data/historical/           4 CSV files (D1, H4, H1, M15)
```

Total: ~15,800 lines of Python across 35+ files.

## 2. Source File Inventory

| File | Lines | Purpose | Key Classes/Functions |
|------|-------|---------|----------------------|
| src/components/market_state.py | 633 | Deterministic MSO builder | `detect_swings`, `identify_structure`, `detect_structure_breaks`, `identify_order_blocks`, `identify_fvgs`, `calculate_premium_discount`, `detect_sweeps`, `compute_market_state` |
| src/components/primary_analyzer.py | 409 | AI reasoning engine via Claude API | `PrimaryAnalyzer.analyze()`, `.build_prompt()`, `._call_claude()`, `._parse_and_validate()`, `_normalize_pa_fields()` |
| src/components/knowledge_base.py | 485 | 3-layer KB: rolling stats, compressed insights, vector retrieval | `KnowledgeBase`, `assemble_full_context()` |
| src/components/debate.py | 368 | Bull/bear debate engine | `DebateEngine`, `run_debate()` |
| src/components/adaptive_review.py | 584 | Rule adaptation system | `AdaptiveReview`, `review_recent_trades()` |
| src/prompts/primary_analyzer_prompt.py | 405 | FULL PA prompt (system + user builder) | `SYSTEM_PROMPT`, `build_static_context()`, `build_dynamic_context()`, `build_user_message()` |
| scripts/batch_backtest.py | 1038 | Batch API backtester | `prescreen_date()`, `collect_prompts()`, `submit_batch()`, `process_results()`, `_safety_check()`, `generate_report()` |
| scripts/backtest_runner.py | 1115 | Sequential backtester | `evaluate_hypothetical_outcome()` |
| scripts/historical_data_loader.py | 783 | CSV→MSO replay | `parse_tradingview_csv()`, `replay_london_open()`, `replay_ny_open()`, `build_raw_data()`, `compute_session_levels()` |
| src/models/market_state_models.py | 153 | MSO Pydantic schema | `MarketStateObject`, `TimeframeState`, `Swing`, `StructureEvent`, `OrderBlock`, `FairValueGap`, `LiquiditySweep` |
| src/models/analysis_models.py | 105 | PA output schema | `PrimaryAnalysisOutput`, `TradeParameters`, `PrimaryAnalysisReasoning` |

## 3. Primary Analyzer Prompt (COMPLETE)

### System Prompt (SYSTEM_PROMPT + ANTI_HALLUCINATION)

```
You are an institutional gold trader with 15+ years of experience trading XAUUSD using Smart Money Concepts (SMC) and ICT methodology. Your role is to evaluate market conditions across MULTIPLE setup frameworks and determine whether ANY A+ setup exists on the current M15 candle.

## Kill Zone Windows
- London Open: 07:00–09:30 UTC
- NY Open: 13:00–15:30 UTC
You will be told which window is being evaluated. Apply the correct session context.

## UNIVERSAL REQUIREMENTS (Apply to ALL Frameworks)
Every framework shares these non-negotiable conditions. If ANY universal requirement fails, output NO_TRADE immediately:

U1. DAILY BIAS: Daily structure must be clearly bullish (HH/HL sequence) or bearish (LH/LL sequence). If ranging, transitional, or unclear → NO_TRADE.
U2. H4 ALIGNMENT: H4 structure must agree with Daily bias direction. If conflicting → NO_TRADE.
U3. M15 CONFIRMATION: After the setup trigger, M15 must show a CHoCH with displacement in the trade direction. CHoCH = body close beyond the most recent protected M15 swing. Displacement = at least one candle with body >= 1.5x the 20-period average body size. Without M15 CHoCH + displacement → NO_TRADE.
U4. DIRECTION MATCH: Trade direction must match Daily bias. LONG only if Daily bullish, SHORT only if Daily bearish.
U5. MINIMUM RR: Risk-to-reward must be >= 1:3 to the first target after applying SL buffer.
U6. SL REQUIREMENTS: Stop loss must be >= 1.5x M15 ATR(14) AND >= $5.00 absolute minimum.
U7. KILL ZONE: The setup trigger must occur within the active kill zone window.

## EVALUATION SEQUENCE

Step 1: Check Universal Requirements U1 and U2 (Daily bias + H4 alignment). If either fails → NO_TRADE. State which failed and why.

Step 2: Evaluate ALL FOUR frameworks below independently. For each framework, determine if its specific criteria are met. Do NOT stop after the first framework — evaluate all four.

Step 3: If ANY framework produces a fully qualifying A+ setup → output CANDIDATE with the best one (highest RR, cleanest structure). If multiple qualify, select the single best and note the others in reasoning.

Step 4: Self-check. Before outputting CANDIDATE, ask:
- Am I forcing this because no trade has been found in several sessions?
- Is displacement genuinely strong or am I rationalizing?
- Would a skeptical, experienced institutional trader agree?
- Are there conflicting signals I'm downplaying?
If any self-check raises doubt → downgrade to WAIT or NO_TRADE.

---

## FRAMEWORK 1: SESSION LIQUIDITY SWEEP
The signature London/NY Open reversal trade.

F1-A. IDENTIFY LIQUIDITY: A defined liquidity pool must exist. Valid pools:
  - For London window: Asian session high/low, PDH/PDL, equal highs/lows near Asian range
  - For NY window: London session high/low, PDH/PDL, equal highs/lows near London range
F1-B. SWEEP DETECTED: Price wicked beyond the liquidity level but the candle body closed back inside. This is a sweep (wick beyond + body inside), NOT a run (body closes beyond). If the body closed beyond the level, this is a breakout, not a sweep — skip this framework.
F1-C. SWEEP DIRECTION: The sweep must be AGAINST the daily bias (e.g., in a bullish market, price sweeps a low — grabbing long stop-losses — before reversing upward).
F1-D. M15 CONFIRMATION: After the sweep, M15 shows CHoCH + displacement in the trade direction (Universal Requirement U3).
F1-E. ENTRY: At the close of the displacement candle, or limit order at 50% retracement of the displacement candle.
F1-F. STOP LOSS: Beyond the sweep wick extreme + ATR buffer. Must satisfy U6.
F1-G. TARGETS: TP1 at nearest opposing liquidity. TP2 at next structural level. TP3 at HTF liquidity target.

---

## FRAMEWORK 2: H1 ORDER BLOCK RETEST AFTER BOS
The institutional retracement entry.

F2-A. H1 BOS CONFIRMED: H1 must have a confirmed Break of Structure — a candle body closing beyond the most recent H1 protected swing high (bullish) or protected swing low (bearish). A CHoCH alone is insufficient — this must be a BOS (break of the trend's protected swing, not just an internal swing).
F2-B. UNMITIGATED ORDER BLOCK: An unmitigated H1 order block exists from the impulse leg that caused the BOS. The OB is the last opposing candle before the displacement move that broke structure.
F2-C. PRICE AT OB: Current price has pulled back into or near the OB zone.
F2-D. PREMIUM/DISCOUNT: The OB must be in the correct zone relative to the impulse:
  - For longs: OB must be in discount (below 50% of the impulse, ideally in the 62-79% OTE zone)
  - For shorts: OB must be in premium (above 50% of the impulse, ideally in the 62-79% OTE zone)
F2-E. M15 CONFIRMATION: At or near the OB, M15 shows CHoCH + displacement in the trade direction (U3).
F2-F. STOP LOSS: Beyond the OB extreme + ATR buffer. Must satisfy U6.
F2-G. TARGETS: TP1 above/below the OB origin (the high/low that was broken for BOS). TP2 at next structural level. TP3 at HTF target.

---

## FRAMEWORK 3: EQUAL HIGHS/LOWS SWEEP + REVERSAL

F3-A. EQUAL LEVELS IDENTIFIED: H1 shows equal highs or equal lows (2+ swing points at approximately the same price, within $2.50 tolerance on gold).
F3-B. SWEEP OF EQUAL LEVEL: Price swept beyond the equal level during the kill zone window. Same sweep criteria as Framework 1: wick beyond + body close inside.
F3-C. CORRECT DIRECTION: In a bullish market, look for equal lows being swept → then reversal up. In a bearish market, look for equal highs being swept → then reversal down. The sweep is AGAINST the bias, the trade is WITH the bias.
F3-D. M15 CONFIRMATION: After the sweep, M15 shows CHoCH + displacement in the trade direction (U3).
F3-E. ENTRY: At the close of the displacement candle or 50% retracement of displacement.
F3-F. STOP LOSS: Beyond the sweep wick of the equal level + ATR buffer. Must satisfy U6.
F3-G. TARGETS: TP1 at nearest opposing liquidity. TP2 at next structural level. TP3 at HTF target.

---

## FRAMEWORK 4: FVG FILL IN DISCOUNT/PREMIUM

F4-A. VALID H1 FVG: An unmitigated H1 Fair Value Gap exists that was created by displacement (the impulse candle that formed the FVG must have a body >= 1.5x the average body). Small, choppy FVGs are noise.
F4-B. FVG IN CORRECT ZONE: The FVG must be in discount (for longs) or premium (for shorts).
F4-C. PRICE ENTERS FVG: Current price has entered or is testing the FVG zone during the kill zone window.
F4-D. M15 CONFIRMATION: Upon entering/testing the FVG, M15 shows CHoCH + displacement in the trade direction (U3). Price must REACT to the FVG, not just pass through it.
F4-E. ENTRY: At the close of the M15 displacement candle.
F4-F. STOP LOSS: Beyond the FVG extreme or beyond the most recent H1 swing, whichever provides better structure + ATR buffer. Must satisfy U6.
F4-G. TARGETS: TP1 at the origin of the FVG. TP2 at next structural level. TP3 at HTF target.

---

## SETUP GRADING (Same for All Frameworks)
- A+: ALL universal requirements met + ALL framework-specific criteria met + displacement quality strong (>= 2x avg body)
- A: ALL criteria met but displacement quality is moderate (1.5-2x avg body), OR kill zone timing is borderline (last 15 min of window)
- B+ or below: Any framework criterion not cleanly met → DO NOT OUTPUT AS CANDIDATE

Only A+ and A setups qualify as CANDIDATE. Everything else is NO_TRADE.

## CRITICAL RULES
- Evaluate ALL four frameworks on every candle. Do not stop after finding one NO_TRADE framework.
- Base ALL analysis on the Market State Object data. If a level, swing, or pattern is not in the data, it does not exist.
- If structure is unclear on any timeframe, state "unclear" — do NOT force a classification.
- When signals conflict, default to NO_TRADE.
- Do NOT blend criteria between frameworks. Each framework stands alone with its own complete checklist.
- You can output at most ONE CANDIDATE per candle (the best qualifying framework).

## TOKEN EFFICIENCY
If Universal Requirements U1 or U2 fail, output a minimal JSON response with only: decision, kill_zone, framework set to "none", and a one-sentence no_trade_reason. Do NOT evaluate individual frameworks when U1 or U2 have already failed.

## Output Format
[JSON schema as defined in primary_analyzer_prompt.py lines 140-210]

## Data Grounding Rules
- Base ALL analysis on the price data provided in the Market State Object.
- If you cannot determine a structure direction with high confidence from the data provided, state 'unclear'.
- Respond with ONLY valid JSON matching the schema.

## Conciseness Rules
- Keep each reasoning section explanation to 1-2 sentences.
- The overall_reasoning field MUST be under 100 words.
- Do NOT repeat information already captured in structured fields.
- For NO_TRADE decisions, be especially brief.
```

### User Message Assembly

The user message is split into two parts for prompt caching:

**Static context** (cached per session — D1/H4/session levels/liquidity pools):
- `build_static_context()` formats D1 and H4 timeframe data, session levels (Asian H/L, PDH/PDL), and liquidity pools

**Dynamic context** (changes per candle — H1/M15/sweeps):
- `build_dynamic_context()` formats H1 and M15 timeframe data, detected sweeps, and recent M15 swings
- Also includes: current time, kill zone indicator, and instruction to evaluate all four frameworks

**Key observation about confidence scoring**: The prompt only says `"confidence_score": <0-100 integer>` with NO calibration guidance. No examples, no ranges, no definition of what 50 vs 80 vs 95 means. This explains why the AI defaults to 85 for 90/91 trades.

## 4. Batch Backtest Pipeline

### 4.1 Date Processing
- Iterates day by day from `--start` to `--end`, skipping weekends
- For each weekday, checks M15 data exists for that date
- If pre-screening enabled, runs `prescreen_date()` (see 4.2)
- For each passing date, generates 10 M15 candles for London (07:15-09:30) and 10 for NY (13:15-15:30) = 20 candles max per session

### 4.2 Pre-screening (EXACT code)
```python
def prescreen_date(date_str, all_candles, config):
    # Build MSO from first London candle
    candle_gen = replay_london_open(date_str, all_candles)
    first_raw = next(candle_gen)
    mso = compute_market_state(first_raw, config)
    tfs = mso.timeframes

    # Layer 1: D1 bias must be clearly bullish or bearish
    d1 = tfs.get("D1")
    d1_dir = d1.structure.direction  # Must be "bullish" or "bearish"
    if d1_dir not in ("bullish", "bearish"):
        return False, f"L1_d1_{d1_dir}"

    # Layer 2: H4 must agree with D1
    h4 = tfs.get("H4")
    h4_dir = h4.structure.direction
    if h4_dir not in ("bullish", "bearish"):
        return False, f"L2_h4_{h4_dir}"
    if h4_dir != d1_dir:
        return False, f"L2_h4_conflict_{h4_dir}_vs_d1_{d1_dir}"

    return True, ""
```

### 4.3 AI Call Assembly
- System prompt: `SYSTEM_PROMPT + "\n\n## Static Context\n" + build_static_context(mso)` with `cache_control: ephemeral`
- User message: `build_user_message(mso, kb_context, current_time, kill_zone)`
- Model: claude-sonnet-4-20250514, max_tokens: 2000 (batch) / 1500 (live), temperature: 0

### 4.4 Dual Kill Zone Handling
- London and NY are processed separately per date
- Max ONE trade per kill zone per day (2 trades max per day)
- After first CANDIDATE in a kill zone, remaining candles get "SKIP"
- PA session cache is reset between London and NY windows

### 4.5 Outcome Simulation (EXACT code — evaluate_hypothetical_outcome)
Partial close logic:
- **TP1 hit**: Close 50% at TP1 R, move SL to breakeven
- **TP2 hit**: Close 25% at TP2 R, trail SL to TP1
- **TP3 hit**: Close remaining 25% at TP3 R (full runner)
- **SL hit pre-TP1**: Full -1.0R loss
- **SL hit post-TP1 at BE**: 0R on remainder (already banked TP1 partial)
- **Trail hit post-TP2**: Positive R on remainder at trail level
- **Session timeout**: Close remaining at last candle's close price
- WIN threshold: total_r > 0.05, LOSS threshold: total_r < -0.05, else BREAKEVEN

### 4.6 Safety Checks (EXACT code with thresholds)
```python
def _safety_check(pa, mso):
    # 1. Grade filter: must be A+ or A
    grade = pa.reasoning.setup_grade
    if grade not in ("A+", "A"):
        return f"below_grade_threshold: {grade}"

    # 2. Trade parameters must exist
    tp = pa.trade_parameters
    if not tp:
        return "no_trade_parameters"

    # 3. Direction must match daily bias
    daily_dir = pa.reasoning.daily_bias.direction
    if daily_dir == "bullish" and tp.direction == "SHORT":
        return "direction_mismatch"
    if daily_dir == "bearish" and tp.direction == "LONG":
        return "direction_mismatch"

    # 4. Minimum RR: 2.5 (NOT 3.0 from config!)
    if tp.risk_reward_ratio < 2.5:
        return f"rr_too_low: {tp.risk_reward_ratio}"

    # 5. SL floor: $5.00 minimum
    sl_distance = abs(tp.entry_price - tp.stop_loss)
    if sl_distance < 5.0:
        return f"sl_below_minimum_floor"

    # 6. SL vs ATR: must be >= 1.5x M15 ATR(14)
    m15_atr = mso.timeframes["M15"].atr_14
    if m15_atr > 0 and sl_distance < m15_atr * 1.5:
        return f"sl_too_tight"

    return None  # All checks pass
```

**NOTE**: Safety check uses RR >= 2.5, but the prompt says RR >= 3.0 (U5). This is a discrepancy — the prompt is stricter than the safety check.

### 4.7 Output Format
- **Session manifests**: `sessions/{date}_session.json` — candle evaluations, trade summary
- **Raw PA responses**: `batch_api/responses/{date}_responses.json` — full AI JSON per candle
- **Batch results**: `batch_api/msgbatch_{id}_results.json` — per-session summaries
- **Batch report**: `batch_api/msgbatch_{id}_report.txt` — aggregate statistics

## 5. Market State Analyzer (Component 2)

### 5.1 Structure Event Detection (BOS/CHoCH)

**BOS (Break of Structure):**
- In bullish structure: candle body closes ABOVE the most recent swing high → bullish BOS
- In bearish structure: candle body closes BELOW the most recent swing low → bearish BOS
- Each broken level is tracked to avoid duplicate BOS events
- Displacement annotated: `displacement_ratio = candle_body / avg_body`, `displacement_present = ratio >= 1.5`

**CHoCH (Change of Character):**
- Only fires once per structure direction
- In bullish structure: candle body closes BELOW the protected swing (most recent swing low) → bearish CHoCH
- In bearish structure: candle body closes ABOVE the protected swing (most recent swing high) → bullish CHoCH
- Only checked on candles AFTER the protected swing index

**Key limitation**: CHoCH fires only once (`choch_fired` flag). If the first CHoCH candle has weak displacement, the system won't detect subsequent stronger CHoCH candles.

### 5.2 Order Block Detection
- Only created from BOS events (NOT CHoCH)
- Walks backward up to 10 candles from BOS to find the last opposing candle (bearish candle before bullish BOS, vice versa)
- OB = that candle's high/low range
- Mitigated = any subsequent candle's low touched OB high (bullish) or high touched OB low (bearish)

### 5.3 MSO Schema
```
MarketStateObject:
  timestamp_utc: str
  timeframes: {D1, H4, H1, M15} → TimeframeState
    swings: [Swing(index, type, price, time)]
    structure: StructureAnalysis(direction, protected_swing, swing_sequence, hh/hl/lh/ll counts)
    structure_events: [StructureEvent(type=BOS|CHoCH, direction, level_broken, displacement_ratio)]
    order_blocks: [OrderBlock(type, high, low, formation_time, mitigated)]
    fair_value_gaps: [FairValueGap(type, top, bottom, filled)]
    premium_discount: PremiumDiscount(equilibrium_50, fib_62, fib_79, zones)
    avg_candle_body: float
    atr_14: float
  session_levels: SessionLevels(asian_high/low, pdh/pdl, session_high/low, london_high/low)
  equal_highs/equal_lows: [EqualLevel]
  liquidity_pools: [LiquidityPool(type, price, side)]
  detected_sweeps: [LiquiditySweep(pool, sweep_type=sweep|run, wick_extreme, body_close)]
  data_quality: DataQuality
```

## 6. Safety Checks (Complete List)

| Check | Threshold | Applied When | On Fail |
|-------|-----------|-------------|---------|
| Grade filter | Must be A+ or A | Post-CANDIDATE | Reject with "below_grade_threshold" |
| Trade parameters exist | Not null | Post-CANDIDATE | Reject with "no_trade_parameters" |
| Direction vs daily bias | Must match | Post-CANDIDATE | Reject with "direction_mismatch" |
| Minimum RR | >= 2.5 (code) / >= 3.0 (prompt U5) | Post-CANDIDATE | Reject with "rr_too_low" |
| SL floor | >= $5.00 | Post-CANDIDATE | Reject with "sl_below_minimum_floor" |
| SL vs ATR | >= 1.5x M15 ATR(14) | Post-CANDIDATE | Reject with "sl_too_tight" |

**Discrepancy**: The safety check code uses RR >= 2.5 but the prompt tells the AI to require RR >= 3.0 (U5). The prompt is the first filter (AI self-enforces), and the safety check is a backstop.

## 7. Output Schema and Parsing

Response is expected as raw JSON (no fences). Parsing pipeline:
1. `strip_json_fences()` — removes markdown code fences if present
2. `json.loads()` — parse to dict
3. `_normalize_pa_fields()` — fixes common AI misnamings:
   - Framework names: "session_liquidity_sweep" → "session_sweep", "order_block_retest" → "ob_retest"
   - Pool types: "equal_high" → "equal_highs"
   - POI types: "order_block" → "OB"
   - Grade clamping: "A-" → "B+", "D"/"F" → "C"
4. `PrimaryAnalysisOutput.model_validate()` — Pydantic validation

## 8. Test Suite Status

- **262 tests, ALL PASSING** (38.42s)
- Coverage areas: market_state, primary_analyzer, knowledge_base, debate, monitoring, batch_backtest, integration, prompts, safety_checks, lifecycle, llm_backend

## 9. Data Coverage

| File | Rows | Start | End |
|------|------|-------|-----|
| XAUUSD_D1.csv | 773 | 2023-04-03 | 2026-03-30 |
| XAUUSD_H4.csv | 4,630 | 2023-03-31 | 2026-03-30 |
| XAUUSD_H1.csv | 14,717 | 2023-10-02 | 2026-03-30 |
| XAUUSD_M15.csv | 47,143 | 2024-04-01 | 2026-03-30 |

M15 data starts Apr 2024, limiting backtesting range. All other timeframes have deeper history.

## 10. Configuration and Thresholds

From `config/agent_config.yaml`:

| Parameter | Value | Location |
|-----------|-------|----------|
| risk_per_trade_pct | 1.0% | config |
| max_daily_loss_pct | 2.0% | config |
| min_rr | 3.0 | config (but safety check uses 2.5) |
| max_spread_cents | 30 | config |
| sl_buffer_dollars | 1.20 | config |
| displacement_min_ratio | 1.5 | config |
| equal_level_tolerance | $2.50 | config |
| primary_model | claude-sonnet-4-20250514 | config |
| swing_detection_min_bars | 2 (all TFs) | config |
| fvg_min_gap | D1:5.0, H4:3.0, H1:2.0, M15:1.0 | config |
| lookback candles | D1:30, H4:80, H1:168, M15:672 | config |
| London KZ | 07:00-09:30 UTC | config |
| NY KZ | 13:00-15:30 UTC | config |

Hardcoded thresholds in code:
- Safety check RR floor: 2.5 (batch_backtest.py:683)
- SL floor: $5.00 (batch_backtest.py:688)
- SL vs ATR: 1.5x (batch_backtest.py:692)
- Displacement threshold: 1.5x avg body (market_state.py:217)
- WIN threshold: total_r > 0.05 (backtest_runner.py:210)
- LOSS threshold: total_r < -0.05 (backtest_runner.py:210)
- Max MSO chars: 60,000 (primary_analyzer_prompt.py:217)

## 11. Analysis Data Available

From prior sessions:
- `unified_trades.json` — 91 trades with 25 fields each
- `session1_decisions.json` — strategic decisions with evidence
- `session1_deep_analysis.md` — full Session 1 analysis
- `full_analysis_report.md` — Session 0 comprehensive analysis
- 210 response files in `batch_api/responses/`
- 242 session files in `sessions/`
