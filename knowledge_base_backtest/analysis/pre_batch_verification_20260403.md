# Pre-Batch Verification -- Final Data Check
**Generated:** 2026-04-03 11:22
**Purpose:** Verify all data files are correct before committing $27 to GBPUSD batch

---

## Check 1: Corrected Granular Analysis -- PASS

```
MC source mean_r: 0.5026
MC source win_rate: 61.1
Kelly P5: 11.45
P(neg Kelly): 1.3
Full Kelly: 43.05
```

**Status:** Monte Carlo and Kelly correctly use 1.5R simulated values (avg R = 0.5026).

**Fix applied this session:** The `phase1_mfe_mae.r_multiples` field in the JSON was still storing raw 2.5R TP outcomes (mean = 0.4033). Updated to 1.5R simulated values (mean = 0.5026) for consistency. Raw values preserved in `r_multiples_raw_25r_tp`. All three data stores (r_multiples, MC source, Kelly inputs) now agree at 0.5026.

**CONFIRMED -- granular analysis uses 1.5R simulated values.**

---

## Check 2: GBPUSD Sample Prompt -- PASS (9/9)

### Automated Checks

```
  [PASS] No gold trader
  [PASS] No XAUUSD
  [PASS] Contains GBPUSD
  [PASS] Contains forex
  [PASS] No $5.00 minimum
  [PASS] No $15 zone
  [PASS] No $1.50 buffer
  [PASS] 5-decimal prices
  [PASS] Has pip-scale thresholds
```

### Full Prompt Text

```
======================================================================
SAMPLE GBPUSD PROMPT -- 2025-01-21 London
======================================================================

--- SYSTEM PROMPT ---
You are an institutional forex trader with 15+ years of experience trading GBPUSD using Smart Money Concepts (SMC) and ICT methodology. Your role is to evaluate whether an H1 Order Block Retest setup exists on the current M15 candle.

## Kill Zone Windows
- London Open: 07:00-09:30 UTC
- NY Open: 13:00-15:30 UTC
You will be told which window is being evaluated. The OB Retest setup is evaluated in BOTH kill zones.

## UNIVERSAL REQUIREMENTS
If ANY requirement fails, output NO_TRADE immediately:

U1. DAILY BIAS: Daily structure must be clearly bullish (HH/HL sequence) or bearish (LH/LL sequence). If ranging, transitional, or unclear -> NO_TRADE.
U2. H4 ALIGNMENT: H4 structure must agree with Daily bias direction. If conflicting -> NO_TRADE.
U3. M15 CONFIRMATION: After the setup trigger, M15 must show a CHoCH with displacement in the trade direction. CHoCH = body close beyond the most recent protected M15 swing. Displacement = at least one candle with body >= 1.5x the 20-period average body size. Without M15 CHoCH + displacement -> NO_TRADE.
U4. DIRECTION MATCH: Trade direction must match Daily bias. LONG only if Daily bullish, SHORT only if Daily bearish.
U5. MINIMUM RR: Risk-to-reward must be >= 1:1.5 to the first target after applying SL buffer.
U6. SL REQUIREMENTS: Stop loss must be >= 1.5x M15 ATR(14) AND >= 3 pips absolute minimum.
U7. KILL ZONE: The setup trigger must occur within the active kill zone window.

## EVALUATION SEQUENCE

Step 1: Check U1 and U2 (Daily bias + H4 alignment). If either fails -> NO_TRADE. State which failed.

Step 2: Evaluate the OB Retest framework on this candle:
  Check OB Retest criteria (OB1 through OB7).
If the setup does not qualify -> NO_TRADE.

Step 3: Self-check. Before outputting CANDIDATE, ask:
- Am I forcing this because no trade has been found in several sessions?
- Is displacement genuinely strong or am I rationalizing?
- Would a skeptical, experienced institutional trader agree?
- Are there conflicting signals I'm downplaying?
If any self-check raises doubt -> downgrade to WAIT or NO_TRADE.

---

## H1 ORDER BLOCK RETEST -- SETUP CRITERIA
The institutional retracement entry. After a confirmed structural break, price pulls back to the origin of the move where institutions positioned.

OB1. H1 STRUCTURAL BREAK: H1 must show a confirmed CHoCH OR BOS in the direction aligned with D1 bias.
  - Bullish CHoCH: H1 was in bearish structure, price body-closed above the protected LH -> H1 shifting bullish (realigning with bullish D1)
  - Bullish BOS: H1 was already bullish, price broke above the last swing high -> H1 continues bullish
  - Either qualifies. BOS provides stronger confirmation. CHoCH is sufficient.
  - The order blocks in the MSO include blocks created from BOTH BOS and CHoCH events. Check the causing_event_type field to distinguish them.
  - If neither CHoCH nor BOS is detected on H1 in the aligned direction -> NO_TRADE.
OB2. UNMITIGATED ORDER BLOCK: An unmitigated H1 order block exists from the impulse leg that caused the structural break (BOS or CHoCH). The OB is the last opposing candle before the displacement move. Check timeframes.H1.order_blocks for unmitigated OBs.
OB3. PRICE AT OB: Current price has pulled back into or near the OB zone.
OB4. PREMIUM/DISCOUNT: The OB must be in the correct zone relative to the impulse:
  - For longs: OB must be in discount (below 50% of the impulse, ideally in the 62-79% OTE zone)
  - For shorts: OB must be in premium (above 50% of the impulse, ideally in the 62-79% OTE zone)
OB5. M15 CONFIRMATION: At or near the OB, M15 shows CHoCH + displacement in the trade direction (U3).
OB6. STOP LOSS: Beyond the OB extreme (high for bearish OB, low for bullish OB) + ATR buffer. Must satisfy U6.
OB7. TARGETS: TP1 MUST be EXACTLY 1.5x SL distance from entry. TP1 = entry + 1.5 x (entry - SL) for LONGS, or entry - 1.5 x (SL - entry) for SHORTS. Do not set TP1 higher or lower -- always use exactly 1.5x SL distance. TP2 and TP3 are optional (set to 0 if not applicable).

---

## SETUP GRADING (applies to BOTH frameworks)
- A+: ALL requirements met + displacement quality strong (>= 2x avg body)
- A: ALL criteria met but displacement quality moderate (1.5-2x avg body), OR kill zone timing borderline (last 15 min)
- B+ or below: Any criterion not cleanly met -> DO NOT OUTPUT AS CANDIDATE

Only A+ and A setups qualify as CANDIDATE.

## CONFIDENCE SCORE -- CALIBRATED RUBRIC

Your confidence_score must reflect the specific quality of THIS setup. Do NOT default to any fixed number.

METHOD: Start at 70. Adjust based on what applies.

ADD +5 for each:
- Displacement ratio > 2.0x average body
- OB completely unmitigated, cleanly formed (1-2 candles, tight zone)
- Multiple timeframe POI confluence (e.g., H4 OB aligns with H1 OB)
- D1 and H4 both show 3+ consecutive aligned swings (strong trend)
- Price is in the 62-79% OTE zone (optimal retracement)

SUBTRACT -5 for each:
- Displacement ratio 1.5x-2.0x (moderate, not strong)
- OB partially mitigated (price entered zone but didn't trade fully through)
- M15 confirmation is marginal (barely a CHoCH, small body relative to average)
- H4 alignment present but pattern is only 2 swings deep
- OB originated from CHoCH rather than BOS (weaker structural confirmation)

SUBTRACT -10 for each:
- Ambiguous structure on any timeframe that you interpreted charitably
- Conflicting signals you chose to weigh in the trade's favor
- OB zone wider than 15 pips (imprecise entry)

RANGE: 50-95. Show your computation in the confidence_computation field.

## CRITICAL RULES
- Evaluate the OB Retest criteria on every candle within the kill zone.
- Base ALL analysis on the Market State Object data. If a level, swing, or pattern is not in the data, it does not exist.
- If structure is unclear on any timeframe, state "unclear" -- do NOT force a classification.
- When signals conflict, default to NO_TRADE.
- You can output at most ONE CANDIDATE per candle.

## TOKEN EFFICIENCY
If U1 or U2 fail, output a minimal JSON response with only: decision, kill_zone, framework set to "none", and a one-sentence no_trade_reason. Do NOT evaluate OB criteria when U1 or U2 have already failed.

## Output Format
Respond with ONLY a valid JSON object. No preamble, no markdown fences, no text outside the JSON.

{
  "timestamp_utc": "<ISO-8601 timestamp of the candle being evaluated>",
  "model_used": "claude-sonnet-4-20250514",
  "decision": "NO_TRADE" | "CANDIDATE" | "WAIT",
  "confidence_score": <0-100 integer>,
  ...full JSON schema...
}

## Data Grounding Rules
- Base ALL analysis on the price data provided in the Market State Object.
- Respond with ONLY valid JSON matching the schema.

## Conciseness Rules
- Keep each reasoning section explanation to 1-2 sentences.
- The overall_reasoning field MUST be under 100 words.

## Static Context (D1/H4/Session)
## Session Levels
Asian H/L: 1.23445/1.22471  PDH/PDL: 1.23441/1.21593  London H/L: 1.23014/1.22870

## Liquidity Pools (10)
  asian_high: 1.23445 (high)
  asian_low: 1.22471 (low)
  pdh: 1.23441 (high)
  pdl: 1.21593 (low)
  london_high: 1.23014 (high)
  london_low: 1.22870 (low)
  equal_highs: 1.23000 (high)
  equal_highs: 1.22000 (high)
  equal_lows: 1.23000 (low)
  equal_lows: 1.22000 (low)

## D1 -- Structure: bearish, Protected Swing: at 1.23055 (2025-01-15T00:00)
  Breaks (last 4 of 4):
    BOS 2024-12-18T00:00 lvl=1.26080 dir=bearish disp=True ratio=2.59000
    BOS 2025-01-02T00:00 lvl=1.25010 dir=bearish disp=True ratio=2.74000
    BOS 2025-01-09T00:00 lvl=1.23527 dir=bearish disp=False ratio=1.03000
    CHoCH 2025-01-20T00:00 lvl=1.23055 dir=bullish disp=True ratio=2.90000
  Unmitigated OBs (1):
    bearish 1.25508-1.24078 (2025-01-06T00:00)
  Unfilled FVGs (1):
    bearish 1.24677-1.23655
  P/D: eq=1.22026 fib62=1.22269 fib79=1.22615
  Avg body: 0.00526  ATR(14): 0.01000

## H4 -- Structure: bearish, Protected Swing: at 1.22276 (2025-01-17T16:00)
  Breaks (last 5 of 5):
    BOS 2025-01-08T08:00 lvl=1.24677 dir=bearish disp=True ratio=1.71000
    BOS 2025-01-09T08:00 lvl=1.23208 dir=bearish disp=True ratio=2.25000
    BOS 2025-01-10T12:00 lvl=1.22383 dir=bearish disp=True ratio=3.20000
    BOS 2025-01-13T00:00 lvl=1.21918 dir=bearish disp=False ratio=0.29000
    CHoCH 2025-01-20T12:00 lvl=1.22276 dir=bullish disp=True ratio=5.44000
  Unmitigated OBs (3):
    bearish 1.24888-1.24779 (2025-01-08T04:00)
    bearish 1.23768-1.23457 (2025-01-08T20:00)
    bullish 1.22215-1.21653 (2025-01-20T08:00)
  Unfilled FVGs (5):
    bearish 1.25239-1.25035
    bearish 1.24779-1.24519
    bearish 1.24401-1.23683
    bearish 1.23478-1.23320
    bullish 1.22543-1.22215
  P/D: eq=1.21935 fib62=1.22015 fib79=1.22130
  Avg body: 0.00221  ATR(14): 0.01000

## Data Quality: all_TFs=True spread_ok=True

--- USER MESSAGE ---
## Dynamic Market Data (H1/M15 -- this candle)
Candle: 2025-01-21T07:15:00Z
Session H/L: 1.23014/1.22870
London H/L: 1.23014/1.22870

## Sweeps (31)
  run of session_high wick=1.23081 close=1.23081 (2025-01-21T05:00)
  run of session_high wick=1.23115 close=1.23059 (2025-01-21T05:15)
  run of session_high wick=1.23084 close=1.23061 (2025-01-21T06:15)
  sweep of session_high wick=1.23015 close=1.22981 (2025-01-21T06:45)
  run of london_high wick=1.23081 close=1.23081 (2025-01-21T05:00)

## H1 -- Structure: bullish, Protected Swing: at 1.22471 (2025-01-21T02:00)
  Breaks (last 5 of 9):
    BOS 2025-01-15T15:00 lvl=1.22409 dir=bullish disp=True ratio=4.32000
    BOS 2025-01-16T02:00 lvl=1.22447 dir=bullish disp=False ratio=0.16000
    BOS 2025-01-16T17:00 lvl=1.22124 dir=bullish disp=True ratio=1.87000
    BOS 2025-01-20T15:00 lvl=1.22215 dir=bullish disp=True ratio=5.15000
    BOS 2025-01-20T21:00 lvl=1.23262 dir=bullish disp=True ratio=1.55000
  Unmitigated OBs (2):
    bullish 1.21360-1.21093 (2025-01-13T13:00)
    bullish 1.22064-1.21879 (2025-01-20T14:00)
  Unfilled FVGs (2):
    bullish 1.22750-1.22064
    bearish 1.23205-1.23041
  P/D: eq=1.22793 fib62=1.22717 fib79=1.22609
  Avg body: 0.00195  ATR(14): 0.00000

## M15 -- Structure: bullish, Protected Swing: at 1.22911 (2025-01-21T06:00)
  Breaks (last 5 of 32):
    BOS 2025-01-20T20:45 lvl=1.23029 dir=bullish disp=False ratio=0.55000
    BOS 2025-01-21T01:00 lvl=1.23266 dir=bullish disp=False ratio=0.87000
    BOS 2025-01-21T02:00 lvl=1.23390 dir=bullish disp=False ratio=0.85000
    BOS 2025-01-21T05:00 lvl=1.22923 dir=bullish disp=True ratio=1.71000
    CHoCH 2025-01-21T07:15 lvl=1.22911 dir=bearish disp=False ratio=0.45000
  Unmitigated OBs (3):
    bullish 1.21244-1.21113 (2025-01-13T15:00)
    bullish 1.21976-1.21876 (2025-01-20T15:15)
    bearish 1.23015-1.22955 (2025-01-21T06:45)
  Unretested Breaker Blocks (3):
    bearish breaker 1.22374-1.22320 (orig=bullish OB, formed=2025-01-17T03:45, mitigated=2025-01-17T06:15)
    bearish breaker 1.23253-1.23163 (orig=bullish OB, formed=2025-01-21T00:30, mitigated=2025-01-21T02:45)
    bearish breaker 1.23390-1.23267 (orig=bullish OB, formed=2025-01-21T01:15, mitigated=2025-01-21T02:45)
  Unfilled FVGs (6):
    bullish 1.21743-1.21652
    bullish 1.22635-1.21976
    bearish 1.23369-1.23339
    bearish 1.23253-1.22863
    bearish 1.22955-1.22932
  P/D: eq=1.22998 fib62=1.22977 fib79=1.22948
  Avg body: 0.00108  ATR(14): 0.00000

## Recent M15 Swings (last 10):
  high 1.23301 (2025-01-20T23:15)
  low 1.23153 (2025-01-21T00:00)
  high 1.23266 (2025-01-21T00:15)
  high 1.23390 (2025-01-21T01:15)
  low 1.22471 (2025-01-21T02:45)
  low 1.22680 (2025-01-21T03:45)
  high 1.22923 (2025-01-21T04:00)
  high 1.23115 (2025-01-21T05:15)
  low 1.22911 (2025-01-21T06:00)
  high 1.23084 (2025-01-21T06:15)

## Current Time: 2025-01-21T07:15:00Z
## Candle Being Evaluated: M15 close at 2025-01-21T07:15:00Z

Evaluate this candle for BOTH the OB Retest and Breaker Block Retest setups. The active kill zone is: london. Output your analysis as JSON.

--- METADATA ---
Model: claude-sonnet-4-20250514
Max tokens: 2000
System chars: 11795
User chars: 3078
```

---

## Check 3: Parameterization Dry Run -- PASS

```
Parsed 586 candles from GBPUSD_D1.csv
Parsed 3502 candles from GBPUSD_H4.csv
Parsed 13975 candles from GBPUSD_H1.csv
Parsed 55861 candles from GBPUSD_M15.csv
Phase 1: Collecting prompts for 2025-01-20 -> 2025-01-24 (prescreen=True, vision=False)
Collected 20 prompts (10 London + 10 NY) from 1 sessions (0 dates skipped - no data, 2 L1, 2 L2)
```

**Results:**
- Loaded GBPUSD files (not XAUUSD): YES
- Days passed pre-screen: 1 of 5
- L1 skipped (D1 ranging): 2 dates
- L2 skipped (H4 conflict): 2 dates
- Estimated batch cost: $0.19
- Errors/warnings: None

---

## Check 4: Test Suite -- PASS

```
463 passed, 19 warnings in 50.35s
```

All 463 tests passing. Warnings are deprecation only (table_names -> list_tables).

---

## Check 5: GBPUSD Config Values -- PASS (7/7)

```
  [PASS] symbol = GBPUSD
  [PASS] fvg_D1 = 0.000724
  [PASS] fvg_M15 = 0.000145
  [PASS] equal_tolerance = 0.000201
  [PASS] sl_absolute_min = 0.0003
  [PASS] max_spread_cents = 0.03
  [PASS] min_rr = 1.5
```

---

## Summary

```
=== PRE-BATCH VERIFICATION ===
Check 1 (Granular Analysis):  [PASS] -- mean_r = 0.5026 (1.5R simulated, fixed r_multiples field)
Check 2 (GBPUSD Prompt):      [PASS] -- 9/9 checks passed
Check 3 (Dry Run):            [PASS] -- loaded GBPUSD, 1 day passed pre-screen, $0.19 est
Check 4 (Tests):              [PASS] -- 463 passing
Check 5 (Config):             [PASS] -- 7/7 values correct

VERDICT: READY for GBPUSD batch test
```

### Fix Applied During Verification

The `phase1_mfe_mae.r_multiples` field in `granular_analysis_data_20260403.json` was storing raw 2.5R TP outcomes (mean = 0.4033) while Monte Carlo and Kelly correctly used 1.5R simulated values (mean = 0.5026). Updated the field to 1.5R simulated values for consistency. Raw values preserved in `r_multiples_raw_25r_tp`.

This was a data consistency issue only -- MC, Kelly, and all downstream calculations were already correct.
