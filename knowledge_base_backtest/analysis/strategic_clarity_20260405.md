# Strategic Clarity Investigation
**Date:** 2026-04-05
**Status:** COMPLETE
**Cost:** $0 (read-only investigation, no API calls)

---

## Investigation 1: The Full Prompt

### System Prompt (XAUUSD Default)

**Character count:** 11,698
**Estimated tokens:** ~3,900

The system prompt is built by `build_system_prompt()` in `src/prompts/primary_analyzer_prompt.py`. It is parameterized per-instrument via config values. The rendered XAUUSD prompt:

```
You are an institutional gold trader with 15+ years of experience trading XAUUSD using Smart Money Concepts (SMC) and ICT methodology. Your role is to evaluate whether an H1 Order Block Retest setup exists on the current M15 candle.

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
U6. SL REQUIREMENTS: Stop loss must be >= 1.5x M15 ATR(14) AND >= $5.00 absolute minimum.
U7. KILL ZONE: The setup trigger must occur within the active kill zone window.

## EVALUATION SEQUENCE
Step 1: Check U1 and U2 (Daily bias + H4 alignment). If either fails -> NO_TRADE.
Step 2: Evaluate BOTH frameworks on this candle: a) OB Retest (OB1-OB7), b) Breaker Block Retest (BR1-BR7). Pick best qualifying. If neither qualifies -> NO_TRADE.
Step 3: Self-check before CANDIDATE output.

[... Full OB Retest criteria OB1-OB7 ...]
[... Full Breaker Block criteria BR1-BR7 ...]
[... Setup Grading, Confidence Score, Critical Rules ...]
[... Token Efficiency rules ...]
[... Full JSON output schema with all fields ...]

## Data Grounding Rules
- Base ALL analysis on the price data provided in the Market State Object.
- Respond with ONLY valid JSON matching the schema.

## Internal Consistency Rules
- If decision is CANDIDATE, m15_confirmation.choch_detected MUST be true.
- If h1_setup.poi_identified is FALSE, decision MUST be NO_TRADE.

## Conciseness Rules
- Keep each reasoning section to 1-2 sentences.
- overall_reasoning MUST be under 100 words.
```

**GBPUSD system prompt:** 11,677 characters (~3,892 tokens). Nearly identical except: identity = "institutional forex trader", SL min = "3 pips", zone width max = "15 pips", buffer = "1.5 pips".

### User Message Structure

The user message is built by `build_user_message()` and has these components:

1. **KB Context block** (~200-500 chars, ~70-170 tokens): Rolling stats, last 10 trades, active failure patterns
2. **Static context** (sent separately for caching, ~2000-3000 chars, ~700-1000 tokens): D1 structure, H4 structure, session levels (Asian H/L, PDH/PDL), liquidity pools
3. **Dynamic context** (~2000-4000 chars, ~700-1300 tokens): H1 structure + OBs + breakers + FVGs, M15 structure + OBs + swings, detected sweeps
4. **Session memory** (~0-600 chars, ~0-200 tokens): Prior candle assessments (up to 6)
5. **Cross-instrument context** (~0-500 chars, for GBPUSD only): XAUUSD D1 direction, Asian range info
6. **Footer** (~200 chars): Current time, candle timestamp, active kill zone, instruction to evaluate

**Total user message per candle:** ~3,000-8,000 characters (~1,000-2,700 tokens)

**Total prompt per API call:** ~4,900-6,600 tokens (system + user)

### Sample User Message (candle 5 of a session)

```
## System Context
Stats: 60 trades, 58% WR, +0.37R exp, PF 1.54
Last 10: [W +1.5R, L -1.0R, W +1.5R, W +0.3R, L -1.0R, W +1.5R, W +1.5R, L -1.0R, W +1.5R, W +0.1R]
Cautions:
- 3 consecutive losses detected in recent window

## Dynamic Market Data (H1/M15 - this candle)
Candle: 2025-12-22T14:45:00Z
Session H/L: 2628.50/2612.30

## H1 - Structure: bullish, Protected Swing: at 2605.20 (2025-12-20T14:00)
  Breaks (last 3 of 5):
    BOS 2025-12-22T10:00 lvl=2620.40 dir=bullish disp=True ratio=2.1
    BOS 2025-12-22T12:00 lvl=2625.80 dir=bullish disp=True ratio=1.8
    BOS 2025-12-22T14:00 lvl=2628.50 dir=bullish disp=False ratio=1.2
  Unmitigated OBs (2):
    bullish 2618.40-2615.20 (2025-12-22T09:00)
    bullish 2622.10-2620.00 (2025-12-22T11:00)
  P/D: eq=2616.85 fib62=2614.30 fib79=2612.10
  Avg body: 3.20  ATR(14): 8.45

## M15 - Structure: bullish, Protected Swing: at 2620.00 (2025-12-22T14:15)
  Breaks (last 2 of 3):
    CHoCH 2025-12-22T14:30 lvl=2624.50 dir=bullish disp=True ratio=2.3
  Unmitigated OBs (1):
    bullish 2623.00-2621.50 (2025-12-22T14:15)
  Avg body: 1.80  ATR(14): 4.20

## Recent M15 Swings (last 10):
  high 2628.50 (2025-12-22T14:00)
  low 2620.00 (2025-12-22T14:15)
  high 2627.80 (2025-12-22T14:30)

## Prior Candle Assessments (this session)
The following are your assessments of prior candles in this kill zone.
Consider the progression: Is a setup developing across candles?
- 13:15 UTC: NO_TRADE - Missing M15 CHoCH + displacement confirmation
- 13:30 UTC: NO_TRADE - Missing M15 CHoCH confirmation after H1 OB retest
- 13:45 UTC: NO_TRADE - Missing M15 CHoCH confirmation after H1 OB retest
- 14:00 UTC: NO_TRADE - Price not positioned at valid H1 POI
- 14:15 UTC: NO_TRADE - Missing M15 CHoCH + displacement confirmation
- 14:30 UTC: NO_TRADE - No M15 CHoCH + displacement confirmation detected

## Current Time: 2025-12-22T14:45:00Z
## Candle Being Evaluated: M15 close at 2025-12-22T14:45:00Z

Evaluate this candle for BOTH the OB Retest and Breaker Block Retest setups. The active kill zone is: ny. Output your analysis as JSON.
```

**NOTE:** This is a reconstructed sample. The actual rendered user messages are not saved in the batch session files. They ARE saved when `trade_capture.save_prompt: true` is enabled, but `knowledge_base/trade_records/` is currently empty (no live trades have been captured yet).

### What the AI Does NOT See (Filtered from MSO)

| MSO Field | In Prompt? | Notes |
|-----------|-----------|-------|
| `timestamp_utc` | YES | Top of dynamic context |
| `timeframes.D1` | YES (static) | Full structure, breaks, OBs, FVGs, P/D |
| `timeframes.H4` | YES (static) | Full structure, breaks, OBs, FVGs, P/D |
| `timeframes.H1` | YES (dynamic) | Full structure, breaks, OBs, breakers, FVGs, P/D |
| `timeframes.M15` | YES (dynamic) | Full structure, breaks, OBs, swings |
| `session_levels` | YES (static) | Asian H/L, PDH/PDL, session H/L, London H/L |
| `liquidity_pools` | YES (static) | All except session_high/session_low |
| `detected_sweeps` | YES (dynamic) | Up to 5 most recent |
| `equal_highs` | NO | Built into liquidity_pools but raw data not shown |
| `equal_lows` | NO | Same |
| `spread_cents` | NO | Only used for data_quality check |
| `high_impact_events` | NO | Handled by economic calendar gate, not shown to AI |
| `data_quality` | YES (static) | all_TFs_complete, spread_normal flags |
| Swing.index | NO | Only price and time shown |
| OrderBlock.open/close | NO | Only high/low shown |
| OrderBlock.formation_index | NO | Only formation_time shown |
| OrderBlock.causing_bos_index | NO | Not shown |
| StructureEvent.candle_index | NO | Only time shown |
| StructureAnalysis.hh_count/hl_count/lh_count/ll_count | NO | Only direction + swing_sequence shown (implicit) |

**Potentially untapped fields:**
- `high_impact_events` — the AI doesn't know about upcoming economic events (handled by a separate gate)
- `spread_cents` — the AI can't factor in spread cost
- `OrderBlock.open/close` — the AI only sees H/L of the OB, not the body boundaries (relevant for OTE calculations)
- `StructureAnalysis.*_count` — the AI infers structure from swing_sequence but doesn't get explicit HH/HL/LH/LL counts

---

## Investigation 2: Winner vs Loser Reasoning Side-by-Side

### CRITICAL FINDING: Full AI Responses Are NOT Saved

The batch session files (`knowledge_base_backtest/sessions/`) store only **summary data** per candle evaluation:
- `decision`, `reason`, `confidence`, `setup_grade`, `framework`
- `confidence_grade`, `confidence_price_levels`, `confidence_hesitation`
- `debate_triggered`, `debate_verdict`, `trade_executed`, `trade_id`

The **full JSON response** from Claude (with all reasoning sections, trade_parameters, overall_reasoning, etc.) is **NOT persisted** in batch mode. There is no `knowledge_base_backtest/responses/` directory.

The `trade_capture` module DOES save full prompts and responses, but only during live/paper trading (writes to `knowledge_base/trade_records/`), which is currently empty.

### What We DO Have: Summary Comparison

**3 Winners (r=1.5, clean TP1):**

| Trade ID | Date | Symbol | KZ | Grade | Confidence | Reason (NO_TRADE candles before) |
|----------|------|--------|----|-------|------------|----------------------------------|
| bt_2025-12-22_ny | 2025-12-22 | XAUUSD | ny | A+ | 85 | Triggered at 14:45 after 6 NO_TRADEs waiting for M15 CHoCH |
| bt_2025-03-04_london | 2025-03-04 | GBPUSD | london | A+ | N/A | Full session with trade |
| bt_2024-04-18_ny | 2024-04-18 | XAUUSD | ny | null | N/A | Earlier batch format |

**3 Losers (r=-1.0, clean SL):**

| Trade ID | Date | Symbol | KZ | Grade | Confidence | Reason (NO_TRADE candles before) |
|----------|------|--------|----|-------|------------|----------------------------------|
| bt_2025-05-08_london | 2025-05-08 | XAUUSD | london | null | N/A | H1 bearish conflicting with D1 bullish all session |
| bt_2025-03-06_london | 2025-03-06 | GBPUSD | london | A+ | N/A | Macro headwind: XAUUSD D1 bearish vs LONG GBPUSD |
| bt_2024-03-01_ny | 2024-03-01 | GBPUSD | ny | A | N/A | Earlier batch format |

### Observable Pattern from Summaries

**Winner sessions** show:
- Clean progression: multiple NO_TRADEs citing specific missing criteria (M15 CHoCH, not at POI), then a sudden CANDIDATE when confirmation arrives
- The reason text before the CANDIDATE is specific and structural ("Missing M15 CHoCH", "Price not at H1 POI")

**Loser sessions** show:
- More diverse rejection reasons — some cite macro headwinds, others cite alignment conflicts
- The sessions that eventually produce a CANDIDATE-turned-loss often show conflicting signals earlier in the session

### Gap: What We Need

To do a proper winner vs. loser reasoning comparison, we need the full JSON response. **Action item:** Enable response persistence in batch mode, or run a small batch (6 trades) with `trade_capture.save_prompt: true` to capture full reasoning.

---

## Investigation 3: The Evaluation Funnel

### Raw Numbers (from all batch session files)

```
XAUUSD Funnel:
  Sessions evaluated:            242
  Total candles evaluated:       4,303
  API calls made:                3,730 (86.7% of candles)
  CANDIDATE decisions:           146 (3.9% of API calls)
  Trades in trade_index:         18 (12.3% of batch CANDIDATEs became index entries)

GBPUSD Funnel:
  Sessions evaluated:            149
  Total candles evaluated:       3,323
  API calls made:                3,104 (93.4% of candles)
  CANDIDATE decisions:           34 (1.1% of API calls)
  Trades in trade_index:         42 (includes pre-split sessions)

Combined (including old mixed sessions):
  Total sessions:                722
  Total candles evaluated:       13,739
  Total CANDIDATEs:              321 (2.3% of candles)
  Total index trades:            60
```

### Pre-Screen Funnel (from frequency investigation data)

The pre-screen operates BEFORE any API calls. From the frequency investigation (582 XAUUSD trading days, 586 GBPUSD):

```
XAUUSD Pre-Screen:
  Total trading days:            582
  D1 clear (bullish/bearish):    232 (40%)
  D1 clear + H4 aligned:        182 (31%)  <-- PASS pre-screen
  Killed at D1 unclear:          350 (60%)
  Killed at H4 mismatch:         50 (9%)

GBPUSD Pre-Screen:
  Total trading days:            586
  D1 clear:                      247 (42%)
  D1 clear + H4 aligned:        134 (23%)  <-- PASS pre-screen
  Killed at D1 unclear:          339 (58%)
  Killed at H4 mismatch:         113 (19%)
```

### Full Funnel (estimated end-to-end)

```
XAUUSD Complete Funnel:
  Trading days (27 months):      582
  Pass pre-screen:               182 (31%)
  Candles evaluated (API calls): ~3,730
  CANDIDATE decisions:           146 (3.9% of API calls)
  Pass L2 verification:          [data not separately tracked]
  Pass Gate 1:                   [data not separately tracked]
  Final trades (index):          18
  Conversion: 582 days -> 18 trades = 3.1% day-to-trade rate
  Conversion: 3,730 API calls -> 18 trades = 0.48% call-to-trade rate

GBPUSD Complete Funnel:
  Trading days:                  586
  Pass pre-screen:               134 (23%)
  Candles evaluated:             ~3,104
  CANDIDATE decisions:           34 (1.1% of API calls)
  Final trades (index):          42
  Conversion: 586 days -> 42 trades = 7.2% day-to-trade rate
  Conversion: 3,104 API calls -> 42 trades = 1.35% call-to-trade rate
```

**Note:** XAUUSD shows 146 CANDIDATEs but only 18 index trades. GBPUSD shows 34 CANDIDATEs but 42 index trades (which includes the older pre-split batch sessions counted separately). The discrepancy suggests many CANDIDATEs get filtered by L2 verification or Gate 1 safety checks, particularly in XAUUSD.

### Key Insight

**97-99% of all API calls produce NO_TRADE.** The system is extremely selective. Combined conversion from candle-to-trade is approximately **0.4-1.4%**.

---

## Investigation 4: MSO Sample Structure

### Full MarketStateObject Fields

```python
class MarketStateObject(BaseModel):
    timestamp_utc: str                           # ISO-8601 timestamp
    timeframes: dict[str, TimeframeState]         # D1, H4, H1, M15
    session_levels: SessionLevels                  # Session price levels
    equal_highs: list[EqualLevel]                  # Equal highs detected
    equal_lows: list[EqualLevel]                   # Equal lows detected
    liquidity_pools: list[LiquidityPool]           # All liquidity targets
    detected_sweeps: list[LiquiditySweep]          # Recent sweep events
    spread_cents: Optional[float]                  # Current spread
    high_impact_events: Optional[list[EconEvent]]  # Upcoming economic events
    data_quality: DataQuality                      # Data integrity flags
```

### TimeframeState (one per D1, H4, H1, M15)

```python
class TimeframeState(BaseModel):
    swings: list[Swing]                  # [{index, type, price, time}, ...]
    structure: StructureAnalysis          # direction + protected_swing + counts
    structure_events: list[StructureEvent] # BOS/CHoCH events with displacement
    order_blocks: list[OrderBlock]         # OBs with mitigated status
    breaker_blocks: list[BreakerBlock]     # Failed-OB zones
    fair_value_gaps: list[FairValueGap]    # Imbalance zones
    premium_discount: Optional[PremiumDiscount]  # Fib zones
    avg_candle_body: float                 # 20-period average body
    atr_14: float                          # ATR(14)
```

### Sub-model Details

| Model | Fields | In Prompt? |
|-------|--------|-----------|
| **Swing** | index, type (high/low), price, time | price + time only |
| **StructureAnalysis** | direction, protected_swing, swing_sequence, hh/hl/lh/ll_count | direction + protected_swing only |
| **StructureEvent** | type (BOS/CHoCH), direction, level_broken, close_price, candle_index, time, displacement_present, displacement_ratio | All except candle_index and close_price |
| **OrderBlock** | type, high, low, open, close, formation_index, formation_time, causing_bos_index, mitigated, causing_event_type | type + high + low + formation_time only (unmitigated only) |
| **BreakerBlock** | zone_high, zone_low, direction, original_ob_direction, formation_time, mitigation_time, causing_event, is_retested, timeframe | All shown for unretested only |
| **FairValueGap** | type, top, bottom, midpoint, candle_indices, formation_time, filled | type + top + bottom only (unfilled only) |
| **PremiumDiscount** | impulse_low/high, equilibrium_50, fib_62, fib_79, discount/premium/ote zones | eq + fib62 + fib79 only |
| **SessionLevels** | asian_high/low, pdh/pdl, session_high/low, london_high/low | All shown |
| **LiquidityPool** | type, price, side | All shown (static pools in static context) |
| **LiquiditySweep** | pool, sweep_type, wick_extreme, body_close, candle_index, time | All except candle_index |
| **EconEvent** | name, time, importance | NOT shown to AI |
| **DataQuality** | all_timeframes_complete, spread_normal, mt5_connected, timestamp_utc | Flags shown |

### Fields COMPUTED but NOT Shown to AI

1. **OrderBlock.open/close** — The candle body boundaries of the OB. Only high/low are shown. The AI can't distinguish between a full-body OB (strong) and a thin-wick OB (weak).
2. **StructureAnalysis.hh_count/hl_count/lh_count/ll_count** — Explicit swing classification counts. The AI only sees `direction` which is derived from these.
3. **OrderBlock.causing_event_type** — Whether the OB was created by a BOS or CHoCH. This IS mentioned in the prompt instructions but the formatted OB data doesn't include it.
4. **FairValueGap.midpoint** — The 50% level of the FVG.
5. **Swing.index** — The candle array index (not useful for the AI).
6. **EconEvent** data — Completely hidden from the AI, handled by a separate gate.
7. **spread_cents** — Not shown; only used for data quality pre-check.

### Fields That Could Add Value If Shown

| Field | Potential Value | Risk |
|-------|----------------|------|
| **OrderBlock.causing_event_type** | The prompt says to check this but the formatted data doesn't include it. BOS-caused OBs may be higher quality than CHoCH-caused OBs. | Low risk — already referenced in prompt instructions. **Should probably be added.** |
| **OrderBlock.open/close** | Full-body OBs (close near high/low) indicate stronger institutional positioning. | Moderate — adds complexity to an already long prompt. |
| **high_impact_events** | Knowing an NFP release is 2 hours away could help the AI avoid trades that will be disrupted. | High value but the economic calendar gate already handles this pre-AI. |
| **StructureAnalysis.*_count** | Explicit "3 HH + 3 HL" vs just "bullish" gives the AI more nuance for borderline structure. | Moderate — could help with transitional/weak bullish cases. |

---

## Investigation 5: Session Memory Implementation

### How It Works

**Location:** `src/components/orchestrator.py`, lines 508-555

**Build process:**
1. After each candle evaluation, `_update_session_memory()` creates a compressed summary
2. Summary format: `"{decision} - {reason[:100]}"` for NO_TRADE, or `"CANDIDATE ({grade}, conf={conf}) - {dir} entry={entry}, SL={sl}, TP1={tp1}"` for CANDIDATE
3. Stored as `{"time": "HH:MM UTC", "kill_zone": "london/ny", "decision": "...", "summary": "..."}`
4. Max 6 entries per kill zone (FIFO eviction)

**Injection:** `_format_session_memory()` renders the last 6 entries as:
```
- 07:15 UTC: NO_TRADE - Daily bias is ranging/transitional
- 07:30 UTC: NO_TRADE - Missing M15 CHoCH confirmation
- 07:45 UTC: NO_TRADE - Price not at H1 POI
```

### Sample Memory Content (candle 5 of NY session, from 2025-12-22)

```
- 13:15 UTC: NO_TRADE - Missing M15 CHoCH + displacement confirmation (U3 violation)
- 13:30 UTC: NO_TRADE - Missing M15 CHoCH confirmation after H1 OB retest
- 13:45 UTC: NO_TRADE - Missing M15 CHoCH confirmation after H1 OB retest
- 14:00 UTC: NO_TRADE - Price not positioned at valid H1 POI for OB retest setup
- 14:15 UTC: NO_TRADE - Missing M15 CHoCH + displacement confirmation (U3 violation)
- 14:30 UTC: NO_TRADE - No M15 CHoCH + displacement confirmation detected
```

### Prompt Instructions About Memory

```
## Prior Candle Assessments (this session)
The following are your assessments of prior candles in this kill zone.
Consider the progression: Is a setup developing across candles?
Did a prior candle show a sweep or displacement that sets up the current candle?
If you said WAIT or noted a developing pattern on a prior candle,
check if the trigger has now occurred.
```

### Assessment: Would an AI Actually Use This?

**Partially, but with significant limitations:**

1. **What works:** The instruction is clear about WHAT to do — look for setup progression across candles. The memory format shows time + decision + reason, which allows the AI to see a narrative (e.g., "5 candles of M15 CHoCH missing, then suddenly one appeared").

2. **What's weak:**
   - The compressed summaries are just reasons for NO_TRADE. They don't include what WAS present (e.g., "H1 OB was valid, just needed M15 CHoCH"). The AI can't easily see "everything was ready except one trigger."
   - No price data in the memory — the AI can't see "price was at 2620 and now it's at 2625, so it pulled back to the OB."
   - WAIT decisions are rare in practice (most sessions are all NO_TRADE until a sudden CANDIDATE). The instruction to "check if the trigger has now occurred" assumes WAIT is used, but the prompt rules force NO_TRADE for most failure modes.

3. **Net assessment:** The session memory is **marginally useful** for the "M15 CHoCH finally appeared" case but **not useful** for the more subtle "price was developing towards the OB over 3 candles" case. The memory lacks the price context needed to see setup development.

**Potential improvement:** Include key prices in the memory summary (e.g., "NO_TRADE - M15 CHoCH missing, price at 2620, H1 OB at 2618-2615"). This would let the AI track price approaching the OB.

---

## Investigation 6: H4 OB Retest Data

### Source
`knowledge_base_backtest/analysis/frequency_multiplier_investigation_20260403.md` + `.json`

### The "70-85% Continuation" Numbers

| Instrument | n (sample size) | 3h Continuation % | MFE/MAE Ratio |
|------------|----------------|-------------------|---------------|
| XAUUSD | 20 | **85.0%** | **2.20** |
| NAS100 | 18 | **77.8%** | **1.74** |
| XAGUSD | 15 | **73.3%** | **2.31** |
| GBPUSD | 18 | **72.2%** | **1.40** |
| EURUSD | 17 | **70.6%** | **1.00** |

**How computed:**
- Identified H4 OBs that formed on D1+H4 aligned dates
- Filtered to those retested during kill zone hours
- Measured 3-hour continuation rate (price continuing in the expected direction after touching the H4 OB zone)
- MFE/MAE = Maximum Favorable Excursion / Maximum Adverse Excursion over 3 hours

**Critical caveat:** n=15-20 per instrument. Very small samples. High variance.

### The "~20% Overlap" — Corrected to 100%

The initial frequency investigation cited ~20% overlap, but after the pressure test correction, the actual overlap is **100%**.

Every H4 OB retest opportunity occurs on a date that already passes the standard pre-screen (D1 clear + H4 aligned). This is by definition — the H4 OB retest requires D1+H4 alignment, which IS the pre-screen.

**Implication:** H4 OB retest adds ZERO new trade dates. It's a quality lever (alternative entry on existing dates), not a frequency lever.

### H4 OB Generation Rate

- 167-184 total H4 OBs per instrument over 27 months
- ~6-7/month when D1+H4 align
- Only 0.6-0.7/month survive to be retested during kill zone hours
- Rising to 0.5-1.1/month including extended hours

### Displacement Thresholds for H4

The displacement threshold is the same as H1: candle body >= 1.5x the 20-period average body size. This is set in `config.model_a.displacement_min_ratio: 1.5`.

---

## Investigation 7: What Happened in the Last 2 Weeks

### Available Evidence

**Log files found:**
- `backtest.log` — 0 bytes (empty)
- `batch_backtest.log` — 0 bytes (empty)
- `replay.log` — 0 bytes (empty)
- `phase1_*.log` — 322KB total, from 2026-04-03 (batch backtest runs, not live)

**Trade records:** `knowledge_base/trade_records/` — empty directory (no live trades captured)

**Pipeline state:** Not checked (would contain the most recent MSO if the system ran)

**Session files:** No live session files exist. All session files in `knowledge_base_backtest/sessions/` are from batch backtest runs.

### Diagnosis: Zero Observability of Live System

**The live system produces NO persistent telemetry.** Specifically:

1. **No live session logs** — When the orchestrator runs and evaluates candles in real-time, the evaluation results go to Python logging (stdout/stderr) and to `pipeline_state/` files that get overwritten each cycle. Nothing persists to a queryable format.

2. **No NO_TRADE audit trail** — When a candle is evaluated and rejected, the only record is a log line. There is no cumulative file showing "on 2026-03-25, 10 candles were evaluated, all NO_TRADE for reasons X, Y, Z."

3. **No pre-screen log** — When the pre-screen kills a session before any API calls, there's no record of why. The system silently skips the day.

4. **trade_capture only fires on trades** — The `trade_capture` module saves records only when a trade is executed (or when a CANDIDATE is rejected by L2/Gate). If the system never reaches CANDIDATE, nothing is saved.

### What WOULD Need to Exist

To answer "why no trades for 2 weeks?", you'd need:

| Telemetry | Purpose | Exists? |
|-----------|---------|---------|
| Daily pre-screen log | "2026-03-25: D1=transitional, SKIPPED" | NO |
| Per-candle evaluation log (persistent) | "07:15 UTC: NO_TRADE, M15 CHoCH missing" | NO (only in-memory + stdout) |
| Session summary file | "London session: 10 candles, 0 CANDIDATEs, top rejection reason: X" | NO for live |
| Economic calendar blocks | "Blocked 13:00-15:30 due to NFP" | Only logged to stdout |
| System health check | "MT5 connected, data quality OK" | Only at startup |

**Bottom line:** The system is a black box during live operation. The ONLY way to know what happened is to manually review Python log output — which may not even be captured if the process runs unattended.

**Recommendation:** Add a daily session summary writer that persists to `knowledge_base/live_sessions/` in the same format as the batch session files. This is a ~30 line code change in the orchestrator.

---

## Summary of Key Findings

1. **The prompt is well-structured** at ~3,900 system tokens + ~1,000-2,700 user tokens per call. Total ~5,000-6,600 tokens per API call.

2. **Full AI responses are NOT saved** in batch mode. We cannot compare winner vs. loser reasoning. This is the #1 gap for understanding AI decision quality.

3. **97-99% of API calls produce NO_TRADE.** The funnel is: 582 days -> 182 pass pre-screen (31%) -> ~3,730 API calls -> 146 CANDIDATEs (3.9%) -> 18 index trades (0.48%).

4. **The MSO is comprehensive** but the prompt filters out several potentially useful fields, notably `OrderBlock.causing_event_type` (already referenced in prompt instructions but not in formatted data).

5. **Session memory is marginal** — it shows prior NO_TRADE reasons but lacks price context needed to track setup development across candles.

6. **H4 OB retest data** shows extraordinary edge (70-85% continuation) but 100% overlap with existing trade dates and tiny samples (n=15-20).

7. **Zero live system observability.** No persistent logs, no session summaries, no daily audit trail. The system is a black box during operation.
