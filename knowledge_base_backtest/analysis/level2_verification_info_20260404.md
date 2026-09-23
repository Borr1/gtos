# Level 2 Verification — Information Extraction
**Date**: 2026-04-04
**Purpose**: Map exactly what data exists at each pipeline stage for designing a deterministic verification step.

---

## SECTION A: What the AI Actually Sees

### Q1: The build_user_message() Function

The AI prompt is split into **two cached parts**: a **static context** (D1/H4/session levels — cached per session) and a **dynamic context** (H1/M15/sweeps — changes per candle). The user message wraps the dynamic part.

#### Complete `build_user_message()` — `src/prompts/primary_analyzer_prompt.py:535-581`

```python
def build_user_message(
    market_state: "MarketStateObject",
    kb_context: dict,
    current_time: str,
    kill_zone: str = "london",
    session_memory: str = "",
    cross_instrument_context: str = "",
) -> str:
    dynamic = build_dynamic_context(market_state)

    layer1 = kb_context.get("layer1", {}) if kb_context else {}
    layer3 = kb_context.get("layer3", []) if kb_context else []

    candle_time = market_state.timestamp_utc if hasattr(market_state, "timestamp_utc") else current_time

    session_block = ""
    if session_memory:
        session_block = (
            "\n## Prior Candle Assessments (this session)\n"
            "The following are your assessments of prior candles in this kill zone.\n"
            "Consider the progression: Is a setup developing across candles? "
            "Did a prior candle show a sweep or displacement that sets up the current candle? "
            "If you said WAIT or noted a developing pattern on a prior candle, "
            "check if the trigger has now occurred.\n\n"
            f"{session_memory}\n"
        )

    ci_block = ""
    if cross_instrument_context:
        ci_block = f"\n{cross_instrument_context}\n"

    return f"""## Dynamic Market Data (H1/M15 — this candle)
{dynamic}
{session_block}{ci_block}
## Current Time: {current_time}
## Candle Being Evaluated: M15 close at {candle_time}

Evaluate this candle for BOTH the OB Retest and Breaker Block Retest setups. The active kill zone is: {kill_zone}. Output your analysis as JSON."""
```

#### Complete `build_dynamic_context()` — lines 394-426

```python
def build_dynamic_context(market_state) -> str:
    d = market_state.model_dump(mode="json") if hasattr(market_state, "model_dump") else market_state
    parts = []

    parts.append(f"Candle: {d.get('timestamp_utc', 'N/A')}")

    sl = d.get("session_levels", {})
    if sl.get("session_high"):
        parts.append(f"Session H/L: {sl['session_high']:{_PRICE_FMT}}/{sl.get('session_low',0):{_PRICE_FMT}}")
    if sl.get("london_high"):
        parts.append(f"London H/L: {sl['london_high']:{_PRICE_FMT}}/{sl.get('london_low',0):{_PRICE_FMT}}")

    sweeps = d.get("detected_sweeps", [])
    if sweeps:
        parts.append(f"\n## Sweeps ({len(sweeps)})")
        for sw in sweeps[:5]:
            pool = sw.get('pool', {})
            parts.append(f"  {sw.get('sweep_type','?')} of {pool.get('type','?')} "
                       f"wick={sw.get('wick_extreme',0):{_PRICE_FMT}} close={sw.get('body_close',0):{_PRICE_FMT}} "
                       f"({sw.get('time','?')[:16]})")

    tfs = d.get("timeframes", {})
    for tf in ("H1", "M15"):
        parts.append(_format_tf(tf, tfs.get(tf, {})))

    m15_swings = tfs.get("M15", {}).get("swings", [])
    if m15_swings:
        parts.append(f"\n## Recent M15 Swings (last 10):")
        for s in m15_swings[-10:]:
            parts.append(f"  {s.get('type','?')} {s.get('price',0):{_PRICE_FMT}} ({s.get('time','N/A')[:16]})")

    return "\n".join(parts)
```

#### Complete `build_static_context()` — lines 363-391

```python
def build_static_context(market_state) -> str:
    d = market_state.model_dump(mode="json") if hasattr(market_state, "model_dump") else market_state
    parts = []

    sl = d.get("session_levels", {})
    parts.append("## Session Levels")
    line = (f"Asian H/L: {sl.get('asian_high',0):{_PRICE_FMT}}/{sl.get('asian_low',0):{_PRICE_FMT}}  "
            f"PDH/PDL: {sl.get('pdh',0):{_PRICE_FMT}}/{sl.get('pdl',0):{_PRICE_FMT}}")
    if sl.get("london_high"):
        line += f"  London H/L: {sl['london_high']:{_PRICE_FMT}}/{sl.get('london_low',0):{_PRICE_FMT}}"
    parts.append(line)

    pools = d.get("liquidity_pools", [])
    static_pools = [p for p in pools if p.get("type") not in ("session_high", "session_low")]
    if static_pools:
        parts.append(f"\n## Liquidity Pools ({len(static_pools)})")
        for p in static_pools[:10]:
            parts.append(f"  {p.get('type','?')}: {p.get('price',0):{_PRICE_FMT}} ({p.get('side','?')})")

    tfs = d.get("timeframes", {})
    for tf in ("D1", "H4"):
        parts.append(_format_tf(tf, tfs.get(tf, {})))

    dq = d.get("data_quality", {})
    parts.append(f"\n## Data Quality: all_TFs={dq.get('all_timeframes_complete',False)} spread_ok={dq.get('spread_normal',False)}")

    return "\n".join(parts)
```

#### Complete `_format_tf()` — lines 307-360

```python
def _format_tf(tf_name: str, tf_data: dict) -> str:
    if not tf_data:
        return f"\n## {tf_name}: No data"
    parts = []
    structure = tf_data.get("structure", {})
    direction = structure.get("direction", "N/A") if structure else "N/A"
    ps = structure.get("protected_swing", {}) if structure else {}
    ps_str = f"at {ps.get('price', 0):{_PRICE_FMT}} ({ps.get('time', 'N/A')[:16]})" if ps and ps.get("price") else "none"

    parts.append(f"\n## {tf_name} — Structure: {direction}, Protected Swing: {ps_str}")

    breaks = tf_data.get("structure_events", [])
    if breaks:
        parts.append(f"  Breaks (last {min(5, len(breaks))} of {len(breaks)}):")
        for b in breaks[-5:]:
            parts.append(f"    {b.get('type','?')} {b.get('time','?')[:16]} lvl={b.get('level_broken',0):{_PRICE_FMT}} "
                       f"dir={b.get('direction','?')} disp={b.get('displacement_present',False)} "
                       f"ratio={b.get('displacement_ratio',0):.1f}")

    obs = [ob for ob in tf_data.get("order_blocks", []) if not ob.get("mitigated", False)]
    if obs:
        parts.append(f"  Unmitigated OBs ({len(obs)}):")
        for ob in obs[-5:]:
            parts.append(f"    {ob.get('type','?')} {ob.get('high',0):{_PRICE_FMT}}-{ob.get('low',0):{_PRICE_FMT}} "
                       f"({ob.get('formation_time','?')[:16]})")

    breakers = [b for b in tf_data.get("breaker_blocks", []) if not b.get("is_retested", False)]
    if breakers:
        parts.append(f"  Unretested Breaker Blocks ({len(breakers)}):")
        for bb in breakers[-5:]:
            parts.append(f"    {bb.get('direction','?')} breaker {bb.get('zone_high',0):{_PRICE_FMT}}-{bb.get('zone_low',0):{_PRICE_FMT}} "
                       f"(orig={bb.get('original_ob_direction','?')} OB, "
                       f"formed={bb.get('formation_time','?')[:16]}, "
                       f"mitigated={bb.get('mitigation_time','?')[:16]})")

    fvgs = [f for f in tf_data.get("fair_value_gaps", []) if not f.get("filled", False)]
    if fvgs:
        parts.append(f"  Unfilled FVGs ({len(fvgs)}):")
        for fvg in fvgs[-5:]:
            parts.append(f"    {fvg.get('type','?')} {fvg.get('top',0):{_PRICE_FMT}}-{fvg.get('bottom',0):{_PRICE_FMT}}")

    pd = tf_data.get("premium_discount")
    if pd:
        parts.append(f"  P/D: eq={pd.get('equilibrium_50',0):{_PRICE_FMT}} "
                   f"fib62={pd.get('fib_62',0):{_PRICE_FMT}} fib79={pd.get('fib_79',0):{_PRICE_FMT}}")

    avg = tf_data.get("avg_candle_body", 0)
    atr = tf_data.get("atr_14", 0)
    if avg or atr:
        parts.append(f"  Avg body: {avg:{_PRICE_FMT}}  ATR(14): {atr:{_PRICE_FMT}}")

    return "\n".join(parts)
```

#### What the AI SEES vs. What's OMITTED

**What the AI SEES per timeframe:**
- Structure direction + protected swing price/time
- Last 5 structure breaks: type (BOS/CHoCH), time, level_broken, direction, displacement_present (bool), displacement_ratio (float)
- Up to 5 unmitigated OBs: type, high-low range, formation_time
- Up to 5 unretested breaker blocks: direction, zone high-low, original OB direction, formation/mitigation time
- Up to 5 unfilled FVGs: type, top-bottom
- Premium/Discount: eq=, fib62=, fib79=
- Avg candle body (20-period) + ATR(14)

**What the AI SEES additionally:**
- Session levels: Asian H/L, PDH/PDL, Session H/L, London H/L
- All liquidity pools with type/price/side
- Detected sweeps: sweep_type, pool type, wick_extreme, body_close, time
- Last 10 M15 swings: type (high/low), price, time
- Cross-instrument context (if enabled): XAUUSD D1 direction, Asian range % of ADR
- Session memory: prior candle assessments from same kill zone

**What gets OMITTED (exists in MSO but not shown):**
- Raw candle OHLC data — NOT passed, only computed summaries
- Individual candle body sizes — only avg_candle_body per timeframe
- Mitigated OBs — filtered out in formatting
- Retested breaker blocks — filtered out
- Filled FVGs — filtered out
- Swing sequence labels (HH/HL/LH/LL) — in MSO StructureAnalysis but not formatted
- HH/HL/LH/LL counts — in MSO but not in prompt
- OB `open`, `close`, `formation_index`, `causing_bos_index`, `causing_event_type` — per OB in MSO but prompt shows only type + high-low + formation_time
- Full swing lists for D1/H4 (only M15 last 10 shown)

### Q2: Real Prompt from a CANDIDATE Trade

**Session files do NOT contain the full prompt.** They store only summary metadata per candle (decision, confidence, grade, framework, trade_id).

**Response files (batch_api/) contain the full AI JSON output** but NOT the input prompt.

**No saved prompts exist in the backtest artifacts.** To reconstruct a real prompt, you must: (1) load raw candle data for the date, (2) call `compute_market_state()` to rebuild the MSO, (3) call the prompt builders.

The batch backtest generates prompts on-the-fly via `PrimaryAnalyzer.build_prompt()` and submits them to the Anthropic Batch API. The prompt text is ephemeral.

---

## SECTION B: What the MSO Contains

### Q3: Complete MSO Schema

Source: `src/models/market_state_models.py`

#### Top-Level MSO (`MarketStateObject`)

| Field | Type | Source |
|-------|------|--------|
| `timestamp_utc` | str | From raw_data |
| `timeframes` | dict[str, TimeframeState] | `_build_timeframe_state()` per D1/H4/H1/M15 |
| `session_levels` | SessionLevels | From raw_data |
| `equal_highs` | list[EqualLevel] | From raw_data (H4 + H1 combined) |
| `equal_lows` | list[EqualLevel] | From raw_data (H4 + H1 combined) |
| `liquidity_pools` | list[LiquidityPool] | `_build_liquidity_pools()` |
| `detected_sweeps` | list[LiquiditySweep] | `detect_sweeps()` on M15 candles |
| `spread_cents` | Optional[float] | From raw_data |
| `high_impact_events` | Optional[list[EconEvent]] | From raw_data |
| `data_quality` | DataQuality | From raw_data |

#### Per-Timeframe (`TimeframeState`)

| Field | Type | Computed By |
|-------|------|-------------|
| `swings` | list[Swing] | `detect_swings()` |
| `structure` | StructureAnalysis | `identify_structure()` |
| `structure_events` | list[StructureEvent] | `detect_structure_breaks()` |
| `order_blocks` | list[OrderBlock] | `identify_order_blocks()` |
| `breaker_blocks` | list[BreakerBlock] | `identify_breaker_blocks()` |
| `fair_value_gaps` | list[FairValueGap] | `identify_fvgs()` |
| `premium_discount` | Optional[PremiumDiscount] | `calculate_premium_discount()` |
| `avg_candle_body` | float | `avg_candle_body(candles, period=20)` |
| `atr_14` | float | `calculate_atr(candles, period=14)` |

### Q3a: Order Blocks — YES, fully detected and stored

```python
class OrderBlock(BaseModel):
    type: Literal["bullish", "bearish"]
    high: float
    low: float
    open: float
    close: float
    formation_index: int
    formation_time: str
    causing_bos_index: int
    mitigated: bool = False
    causing_event_type: str = "BOS"  # "BOS" or "CHoCH"
```

- **Per-timeframe**: YES — each TimeframeState has its own order_blocks list
- **Unmitigated determination**: `mitigated=True` if any candle after BOS has low <= OB.high (bullish) or high >= OB.low (bearish). See `identify_order_blocks()` lines 278-350.
- **Detection**: Walks backward up to 10 candles from each BOS/CHoCH to find last opposing candle. Deduplicates by formation_index.

### Q3b: Displacement / Candle Body Data

- **Individual M15 OHLC in MSO**: NO. Raw candles consumed during computation, not stored.
- **20-period average body size**: YES — `avg_candle_body` per timeframe
- **Pre-computed displacement ratio**: YES — per StructureEvent: `displacement_ratio` (body/avg_body) and `displacement_present` (True if >= 1.5)
- **Closest available for raw data**: Would need to re-pull candles from data source.

### Q3c: Liquidity Sweeps — YES, deterministic

```python
class LiquiditySweep(BaseModel):
    pool: LiquidityPool       # type, price, side
    sweep_type: Literal["sweep", "run"]
    wick_extreme: float
    body_close: float
    candle_index: int
    time: str
```

Pools built from: asian_high/low, pdh/pdl, session_high/low, london_high/low, equal_highs/lows.

- **Asian H/L**: YES — `SessionLevels.asian_high/low`
- **PDH/PDL**: YES — `SessionLevels.pdh/pdl`
- Sweeps detected on last 10 M15 candles against all pools.

### Q3d: Structure / Swings

```python
class Swing(BaseModel):
    index: int
    type: Literal["high", "low"]
    price: float
    time: str

class StructureAnalysis(BaseModel):
    direction: Literal["bullish", "bearish", "transitional", "insufficient_data"]
    protected_swing: Optional[Swing]
    swing_sequence: list[str]  # ["HH", "HL", "HH"] — NOT shown in prompt
    hh_count: int = 0          # NOT shown in prompt
    hl_count: int = 0
    lh_count: int = 0
    ll_count: int = 0
```

- D1 bias: deterministic — `timeframes["D1"].structure.direction`
- H4 alignment: deterministic — `timeframes["H4"].structure.direction`

### Q3e: Fib Retracement / Premium-Discount — YES, deterministic

```python
class PremiumDiscount(BaseModel):
    impulse_low: float
    impulse_high: float
    equilibrium_50: float
    fib_62: float
    fib_79: float
    discount_zone: PriceZone   # top, bottom
    premium_zone: PriceZone    # top, bottom
    ote_zone: PriceZone        # 62-79% fib zone, top, bottom
```

Computed per-timeframe from most recent impulse leg.

### Q4: Real MSO

**MSOs are NOT saved to disk per historical trade.** `pipeline_state/02_market_state.json` is overwritten each candle. Session files don't contain MSOs.

To get a real MSO, must regenerate from raw candle data via `compute_market_state()`.

---

## SECTION C: What's Saved from Historical Trades

### Q5: Session File Contents

Full structure of `sessions/XAUUSD/2024-04-01_session.json`:

```json
{
  "date": "2024-04-01",
  "day_of_week": "Monday",
  "session_start_utc": "2024-04-01T07:00:00Z",
  "session_end_utc": "2024-04-01T15:30:00Z",
  "pre_session": null,
  "candle_evaluations": [
    {
      "candle_time": "2024-04-01T08:00:00Z",
      "kill_zone": "london",
      "decision": "CANDIDATE",
      "reason": null,
      "confidence": 80,
      "setup_grade": "A+",
      "framework": "ob_retest",
      "debate_triggered": false,
      "debate_verdict": "AUTO_APPROVED",
      "trade_executed": true,
      "trade_id": "bt_2024-04-01_london_001"
    }
  ],
  "trade_summary": {
    "trade_taken": true,
    "trades": 1,
    "trade_id": "bt_2024-04-01_london_001",
    "outcome": "WIN",
    "r_multiple": 1.5
  },
  "errors": [],
  "api_calls_count": 14,
  "api_cost_estimate_usd": 0
}
```

**Session files do NOT contain:**
- The MSO that was used
- The full AI JSON response (reasoning, trade_parameters)
- The prompt that was sent
- Raw candle data
- Trade parameter details (entry, SL, TP)

### Q6: Response File Contents

**There is NO `knowledge_base_backtest/responses/` directory.** Response files are in `knowledge_base_backtest/batch_api/responses/{SYMBOL}/`.

These contain the **full parsed AI output** — all reasoning fields, trade_parameters, confidence computation. This is the complete `PrimaryAnalysisOutput` as JSON, keyed by custom_id (e.g., `"2024-04-01_london_0800"`).

**Response files do NOT contain:** the input prompt, the MSO, or raw candle data.

### Q7: File Counts

| Location | Count |
|----------|-------|
| `sessions/XAUUSD/` | **242 files** |
| `sessions/GBPUSD/` | **149 files** |
| `responses/` (top-level) | **0** (doesn't exist) |
| `batch_api/responses/` | Exists for both symbols |

**Of the historical trades**: All have session files. Most have full AI response files in `batch_api/responses/`. NONE have MSO, prompt, or candle data saved.

**Retroactive verification requires re-running the pipeline** (re-ingesting candle data → rebuilding MSO) — not just reading saved files.

---

## SECTION D: Pipeline Architecture

### Q8: Full CANDIDATE Pipeline

From `orchestrator.py:_process_candle()` (lines 219-353):

```
Step 1: raw_data = ingest_live_data(mt5, config)                    [data_ingestion.py]
Step 2: mso = compute_market_state(raw_data, config)                 [market_state.py]
Step 3: prescreen_mso(mso) → D1 clear + H4 aligned?                 [orchestrator.py:668]
Step 4: memory_block = self._format_session_memory()
Step 5: analysis = analyzer.analyze(mso, kz, memory, ci)             [primary_analyzer.py]
Step 6: update session memory
  └─ If decision != CANDIDATE → log and return
Step 6b: conf_metrics = score_confidence(analysis)                   [confidence_scorer.py]
  └─ If mode=active and grade=LOW → reject
Step 6c: M5 Entry Refinement (if enabled)                            [m5_refinement.py]
Step 7: denial = check_permissions(analysis, mso, state, mt5)        [permissions.py]
  └─ Gate 3 (circuit breakers) FIRST, then Gate 1 (safety checks)
  └─ If denied → reject
Step 8: execution.open_trade(...)                                     [execution.py]
```

**Bull/Bear debate (Gate 2)**: NOT in live code. `permissions.py` docstring says "Gate 2 (debate/meta-review) stubbed for live." Session files have `debate_triggered`/`debate_verdict` fields but they're set to `false`/`"AUTO_APPROVED"` in batch backtest.

### Q9: Gate 1 Complete Code

#### Gate 3 — `_gate3_circuit_breakers()` (lines 36-69)

```python
def _gate3_circuit_breakers(session_state, mt5):
    # 1. Daily loss >= -2.0% → deny
    # 2. trades_today >= max_daily_trades (2) → deny
    # 3. trades_{kz} >= 1 → deny
    # 4. MT5 disconnected → deny
    # 5. Spread > 30 cents → deny
```

#### Gate 1 — `_gate1_safety_checks()` (lines 72-152)

```python
def _gate1_safety_checks(trade_params, mso, session_state):
    pa = trade_params  # Full PA output
    reasoning = getattr(pa, "reasoning", None)

    # CHECK 1: Grade must be A+ or A
    grade = reasoning.setup_grade if reasoning else "C"
    if grade not in ("A+", "A"):
        return ExecutionDenial("gate1_safety", f"below_grade_threshold: {grade}", {"grade": grade})

    tp = getattr(pa, "trade_parameters", None)
    if not tp:
        return ExecutionDenial("gate1_safety", "no_trade_parameters", {})

    # CHECK 2: Direction must match daily bias
    daily_dir = reasoning.daily_bias.direction if reasoning else "ranging"
    if daily_dir == "bullish" and tp.direction == "SHORT": return deny
    if daily_dir == "bearish" and tp.direction == "LONG": return deny

    # CHECK 3: R:R >= 1.3
    if tp.risk_reward_ratio < 1.3: return deny

    sl_distance = abs(tp.entry_price - tp.stop_loss)

    # CHECK 4: TP1 on correct side of entry
    if tp.direction == "LONG" and tp.take_profit_1 <= tp.entry_price: return deny
    if tp.direction == "SHORT" and tp.take_profit_1 >= tp.entry_price: return deny

    # CHECK 5: TP1 between 1.3R and 2.0R
    if sl_distance > 0 and tp.take_profit_1:
        tp1_r = abs(tp.take_profit_1 - tp.entry_price) / sl_distance
        if tp1_r < 1.3: return deny
        if tp1_r > 2.0: return deny

    # CHECK 6: SL >= $5.00 absolute floor
    if sl_distance < 5.0: return deny

    # CHECK 7: SL >= 1.5x M15 ATR(14)
    m15_atr = mso.timeframes.get("M15").atr_14 if mso.timeframes.get("M15") else 0
    if m15_atr > 0 and sl_distance < m15_atr * 1.5: return deny

    # CHECK 8: SL <= 2.5% of entry price
    sl_pct = (sl_distance / tp.entry_price) * 100
    if sl_pct > 2.5: return deny

    return None
```

### Q10: Insertion Point for Verification Step

**Recommended: between Step 6 (CANDIDATE returned) and Step 6b (confidence scoring).**

In `orchestrator.py`, after line 261:

```python
            if analysis.decision != "CANDIDATE":
                ...
                return

            # ──── INSERT LEVEL 2 VERIFICATION HERE ────
            # verification_result = verify_candidate(analysis, mso)
            # if not verification_result.passed:
            #     self._log_candle("REJECTED_L2", verification_result.reason, kill_zone)
            #     return
            # ──── END INSERTION ────

            # 6b. Confidence scoring (shadow or active mode)
            conf_metrics = score_confidence(analysis.model_dump())
```

This is the cleanest point: AI has spoken, MSO is available, no execution logic has run yet.

---

## SECTION E: Critical Unknowns — The Verification Matrix

### Q11: What the AI Computes vs. What It Receives

| Data Point | In MSO? | Shown in Prompt? | Computed by AI? | Deterministically Verifiable? |
|---|---|---|---|---|
| **H1 order block price levels** | YES — `H1.order_blocks[].high/low/open/close` | YES — type + high-low + formation_time (no open/close/causing_event_type) | AI selects WHICH OB is POI | PARTIALLY — can verify cited OB exists in MSO |
| **H1 OB mitigated status** | YES — `OrderBlock.mitigated` bool | Only unmitigated shown (mitigated filtered) | NO — deterministic filter | YES — can verify AI doesn't cite a mitigated OB |
| **H1 OB causing_event_type** | YES — "BOS" or "CHoCH" per OB | NO — not in prompt formatting | AI infers from visible BOS/CHoCH events | YES from MSO — can cross-check AI's claim |
| **M15 displacement ratio** | YES — per StructureEvent | YES — `ratio=X.X` per break | NO — receives it | YES — verify from MSO events |
| **M15 avg body (20-period)** | YES — `avg_candle_body` | YES — "Avg body: X.XX" | NO — receives it | YES |
| **Liquidity sweep detection** | YES — `detected_sweeps[]` | YES — type, wick, close, time | AI interprets quality | PARTIALLY — can verify sweep exists |
| **Asian session high/low** | YES — `session_levels` | YES — in static context | NO — from raw data | YES |
| **PDH/PDL** | YES — `session_levels` | YES — in static context | NO — from raw data | YES |
| **D1 bias direction** | YES — `D1.structure.direction` | YES — "D1 — Structure: X" | NO — deterministic | YES |
| **H4 alignment** | YES — `H4.structure.direction` | YES — shown similarly | NO — deterministic | YES |
| **Premium/discount zone** | YES — per-TF `PremiumDiscount` | YES — eq, fib62, fib79 | AI classifies zone | YES — can check price vs fib levels |
| **Fib retracement %** | YES (indirectly) — impulse range in MSO | YES — fib levels shown | AI computes % or we can | YES — compute from impulse_high/low |
| **M15 CHoCH detected** | YES — `M15.structure_events[]` | YES — in structure breaks | AI confirms | YES — verify CHoCH event exists |
| **M15 CHoCH + displacement** | YES — event has `displacement_present` | YES — disp bool+ratio shown | AI should agree | YES — CHoCH exists AND displacement_present=true |
| **H1 structural break exists** | YES — `H1.structure_events[]` | YES — shown in breaks | AI references | YES — verify BOS/CHoCH in aligned direction |
| **OB in correct P/D zone** | YES — OB prices + P/D zones both in MSO | YES — both shown | AI determines match | YES — cross-check OB price range vs P/D zones |
| **Entry within OB zone** | OB zone in MSO | N/A — AI picks entry | YES — AI chooses | YES — verify entry between OB.low and OB.high |
| **SL beyond OB extreme** | OB extreme in MSO | N/A — AI places SL | YES — AI chooses | YES — verify SL beyond OB high (bearish) or low (bullish) |
| **TP1 = 1.5x SL distance** | N/A | N/A | YES — AI computes | YES — arithmetic: TP1_dist / SL_dist == 1.5 |
| **Direction matches D1 bias** | D1 direction in MSO | Both shown | AI should match | YES — trade direction == D1.structure.direction |
| **Breaker block zone** | YES — `H1.breaker_blocks[]` | YES — direction, zone | AI selects which | PARTIALLY — verify cited breaker exists |
| **Setup grade** | N/A | N/A | YES — AI assigns | NO — subjective judgment |
| **Confidence score** | N/A | N/A | YES — AI assigns | NO — subjective judgment |
| **Sweep quality** | N/A | N/A | YES — AI assesses | NO — subjective |

---

## Summary of Key Findings

1. **MSO is extremely rich** — deterministically computes OBs, breakers, sweeps, structure, fib levels, displacement ratios, all per-timeframe. Most of what the AI "decides" it actually reads from the MSO.

2. **Prompt FILTERS the MSO heavily** — only unmitigated OBs, last 5 events, no raw OHLC, no causing_event_type per OB. AI must sometimes infer what MSO knows explicitly.

3. **Session files are THIN** — no MSO, no prompt, no full AI response, no candle data. Retroactive verification requires re-running the pipeline.

4. **Response files (batch_api/) have full AI output** — all reasoning fields and trade_parameters. Enough to verify the AI's claims against a reconstructed MSO.

5. **Fully verifiable from MSO (Level 2 checks)**:
   - H1 OB exists and is unmitigated
   - H1 OB causing_event_type matches AI claim
   - M15 CHoCH exists with displacement_present=true
   - Displacement ratio >= 1.5 (or >= 2.0 for A+)
   - OB in correct premium/discount zone
   - Entry price within OB zone
   - SL beyond OB extreme + buffer
   - TP1 = exactly 1.5x SL distance
   - D1/H4 alignment matches MSO
   - Direction matches D1 bias

6. **NOT verifiable deterministically** (AI judgment only):
   - Setup grade
   - Confidence score
   - Sweep quality assessment
   - "Is displacement genuinely strong?"

7. **Insertion point is clean** — between PA CANDIDATE output and confidence scoring in orchestrator.py, one function call.
