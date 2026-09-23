# Primary Analyzer Prompt -- Complete Feature Inventory

Source file: `src/prompts/primary_analyzer_prompt.py`
Generated: 2026-04-05
Purpose: Exhaustive catalog of every feature, rule, threshold, and decision criterion
in the production PA prompt, for use in A/B testing comparisons.

---

## 0. Identity and Framing

| # | Item | Type | Details |
|---|------|------|---------|
| 0.1 | Persona assignment | Guidance | "You are an {identity} using Smart Money Concepts (SMC) and ICT methodology." Identity is instrument-specific (e.g., "institutional gold trader with 15+ years of experience trading XAUUSD"). |
| 0.2 | Role definition | Hard rule | "Your role is to evaluate whether an H1 Order Block Retest setup exists on the current M15 candle." |
| 0.3 | Instrument-specific identities | Guidance | XAUUSD, EURUSD, GBPUSD, USDJPY, GBPJPY, NZDUSD, NAS100, US30_cash, XAGUSD each have a tailored identity string. Fallback: generic "institutional trader" for unlisted symbols. |

---

## 1. Kill Zone Windows

| # | Item | Type | Details |
|---|------|------|---------|
| 1.1 | Kill zone display | Hard rule | Configurable per instrument. Default: London Open 07:00-09:30 UTC, NY Open 13:00-15:30 UTC. |
| 1.2 | Both windows evaluated | Hard rule | "The OB Retest setup is evaluated in BOTH kill zones." |
| 1.3 | Active window communicated | Hard rule | The user message tells the PA which kill zone is active ("london" or "ny"). |

---

## 2. Universal Requirements (U1-U7)

Each is a **hard rule** -- failure of ANY requirement forces NO_TRADE immediately.

| # | Requirement | Rule Type | Details |
|---|-------------|-----------|---------|
| 2.1 | **U1 -- Directional Bias** | Hard rule | Establish bias from highest available TF. If D1 is clearly bullish/bearish, use D1. If D1 unclear/ranging, use H4+H1 consensus -- at least 2 of D1/H4/H1 must agree. No consensus --> NO_TRADE. |
| 2.2 | **U2 -- H4 Alignment** | Hard rule | If D1 bias is clear, H4 must agree with D1. If D1 unclear, H4 becomes primary HTF reference and must be clearly directional (not ranging). Both D1 and H4 unclear --> NO_TRADE. |
| 2.3 | **U3 -- M15 Confirmation** | Hard rule | M15 must show CHoCH with displacement in trade direction. CHoCH = body close beyond most recent protected M15 swing. Displacement = at least one candle with body >= 1.5x the 20-period average body size. Without both --> NO_TRADE. |
| 2.4 | **U4 -- Direction Match** | Hard rule | Trade direction must match established bias. LONG only if bullish, SHORT only if bearish. |
| 2.5 | **U5 -- Minimum RR** | Hard rule | Risk-to-reward >= 1:1.5 to first target after applying SL buffer. |
| 2.6 | **U6 -- SL Requirements** | Hard rule | Stop loss >= 1.5x M15 ATR(14) AND >= absolute minimum (instrument-specific, e.g., $5.00 for XAUUSD). |
| 2.7 | **U7 -- Kill Zone** | Hard rule | Setup trigger must occur within the active kill zone window. |

---

## 3. Evaluation Sequence (Steps 1-3)

| # | Step | Type | Details |
|---|------|------|---------|
| 3.1 | **Step 1: Bias + Alignment** | Hard rule | Establish directional bias per U1. Check U2 (H4 alignment). If no valid bias or U2 fails --> NO_TRADE. Must state bias source (Daily, or H4+H1 consensus). |
| 3.2 | **Step 2: Dual Framework Evaluation** | Hard rule | Evaluate BOTH frameworks on every candle: (a) OB Retest (OB1-OB7) and (b) Breaker Block Retest (BR1-BR7). Pick best qualifying setup. If both qualify, prefer stronger displacement + tighter zone. Neither qualifies --> NO_TRADE. |
| 3.3 | **Step 3: Self-Check** | Guidance | Before outputting CANDIDATE, ask four introspective questions: (1) Am I forcing this because no trade found recently? (2) Is displacement genuinely strong or am I rationalizing? (3) Would a skeptical institutional trader agree? (4) Are there conflicting signals I'm downplaying? Any doubt --> downgrade to WAIT or NO_TRADE. |

---

## 4. H1 Order Block Retest -- Setup Criteria (OB1-OB7)

| # | Criterion | Type | Details |
|---|-----------|------|---------|
| 4.1 | **OB1 -- H1 Structural Break** | Hard rule | H1 must show confirmed CHoCH OR BOS aligned with directional bias. Bullish CHoCH = body close above protected LH. Bullish BOS = break above last swing high. BOS is stronger but CHoCH is sufficient. OBs include blocks from both BOS and CHoCH (check causing_event_type field). No aligned CHoCH/BOS on H1 --> NO_TRADE. |
| 4.2 | **OB2 -- Unmitigated Order Block** | Hard rule | An unmitigated H1 OB must exist from the impulse leg causing the structural break. OB = last opposing candle before displacement move. Check timeframes.H1.order_blocks for unmitigated OBs. |
| 4.3 | **OB3 -- Price at OB** | Hard rule | Current price must have pulled back into or near the OB zone. |
| 4.4 | **OB4 -- Premium/Discount** | Hard rule | OB must be in correct zone relative to impulse: Longs = OB in discount (below 50% of impulse). Shorts = OB in premium (above 50% of impulse). |
| 4.5 | **OB5 -- M15 Confirmation** | Hard rule | At or near OB, M15 shows CHoCH + displacement in trade direction (per U3). |
| 4.6 | **OB6 -- Stop Loss** | Hard rule | SL beyond OB extreme (high for bearish OB, low for bullish OB) + ATR buffer. Must satisfy U6. |
| 4.7 | **OB7 -- Targets** | Hard rule | TP1 MUST be EXACTLY 1.5x SL distance from entry. Formula: LONGS: TP1 = entry + 1.5 * (entry - SL). SHORTS: TP1 = entry - 1.5 * (SL - entry). TP2 and TP3 optional (set to 0 if N/A). |

---

## 5. H1 Breaker Block Retest -- Setup Criteria (BR1-BR7)

| # | Criterion | Type | Details |
|---|-----------|------|---------|
| 5.1 | **BR1 -- Daily Bias + H4 Alignment** | Hard rule | Same as OB Retest (U1, U2). |
| 5.2 | **BR2 -- Unmitigated Breaker Block** | Hard rule | An unretested H1 breaker block must exist in MSO (check timeframes.H1.breaker_blocks where is_retested=false). Breaker direction must align with bias (bullish breaker for bullish bias, bearish for bearish). |
| 5.3 | **BR3 -- Price at Breaker Zone** | Hard rule | Current price must have pulled back into or near the breaker block zone. |
| 5.4 | **BR4 -- Displacement Quality** | Guidance | Original OB must have been broken with displacement (strong candle body through zone, not slow grind). Check if mitigation move was impulsive. |
| 5.5 | **BR5 -- Zone Quality** | Guidance | Breaker zone should be relatively tight. Zones wider than {zone_max_display} (e.g., $15 for XAUUSD) give poor RR and are lower quality. |
| 5.6 | **BR6 -- M15 Confirmation** | Hard rule | At or near breaker zone, M15 shows CHoCH + displacement (U3). Same as OB Retest. |
| 5.7 | **BR7 -- Entry + SL + TP** | Hard rule | Entry at or within breaker zone. SL beyond zone extreme. TP1 EXACTLY 1.5x SL distance. TP2/TP3 optional. SL must satisfy U6. |

Breaker block definition provided:
- An H1 OB forms (from BOS or CHoCH)
- Price returns and trades THROUGH the OB -- OB doesn't hold (mitigated)
- Zone becomes "breaker block" with direction flipped
- Price retests from OTHER SIDE --> potential entry
- Bullish breaker: bearish OB broken upside --> resistance becomes support --> retest = LONG
- Bearish breaker: bullish OB broken downside --> support becomes resistance --> retest = SHORT

---

## 6. Quality Signals (Both Frameworks)

| # | Signal | Type | Details |
|---|--------|------|---------|
| 6.1 | **FVG from displacement** | Guidance (positive) | Displacements creating a Fair Value Gap have ~11% higher continuation rates. Treat as meaningful positive signal. |
| 6.2 | **Displacement at pre-existing OB** | Guidance (caution) | Displacement at/near pre-existing OB is a mild caution signal. Resting OB orders can partially absorb momentum, reducing continuation probability by ~5%. Does NOT affect the OB Retest framework itself (OB retest entry is different from new displacement landing on old OB). |
| 6.3 | **Impulse compactness** | Guidance | Typical gold H1 impulse is 6-8 candles. OBs from impulse legs of <= 7 candles have ~85% continuation rate vs ~55% for >= 8 candles. Prefer compact, decisive impulse moves (stronger institutional commitment). |

---

## 7. Setup Grading

| # | Grade | Type | Details |
|---|-------|------|---------|
| 7.1 | **A+** | Hard rule (threshold) | ALL requirements met + displacement quality strong (>= 2x avg body). |
| 7.2 | **A** | Hard rule (threshold) | ALL criteria met but displacement quality moderate (1.5-2x avg body), OR kill zone timing borderline (last 15 min). |
| 7.3 | **B+ or below** | Hard rule (threshold) | Any criterion not cleanly met --> DO NOT output as CANDIDATE. |
| 7.4 | **CANDIDATE eligibility** | Hard rule | Only A+ and A setups qualify as CANDIDATE. |

---

## 8. Confidence Score

| # | Item | Type | Details |
|---|------|------|---------|
| 8.1 | Score range | Hard rule | 50-95, based on overall confluence count. Higher = more confirming factors aligned. |
| 8.2 | Computation display | Hard rule | Must show a one-line computation in confidence_computation field (e.g., "Baseline 70 + strong displacement (+5) - partial OB (-5) = 70"). |

---

## 9. Critical Rules

| # | Rule | Type | Details |
|---|------|------|---------|
| 9.1 | Dual framework evaluation | Hard rule | Evaluate BOTH OB Retest AND Breaker Block Retest on every candle within kill zone. |
| 9.2 | Data grounding | Hard rule | Base ALL analysis on MSO data. If a level/swing/pattern is not in the data, it does not exist. |
| 9.3 | Unclear structure | Hard rule | If structure unclear on any TF, state "unclear" -- do NOT force a classification. |
| 9.4 | Conflicting signals | Hard rule | When signals conflict, default to NO_TRADE. |
| 9.5 | One CANDIDATE max | Hard rule | At most ONE CANDIDATE per candle. |

---

## 10. Token Efficiency

| # | Rule | Type | Details |
|---|------|------|---------|
| 10.1 | Early termination | Hard rule | If U1 or U2 fail, output minimal JSON with only: decision, kill_zone, framework="none", and one-sentence no_trade_reason. Do NOT evaluate OB criteria when U1/U2 already failed. |

---

## 11. Anti-Hallucination Guardrail (Appended to Every System Prompt)

### 11.1 Data Grounding Rules

| # | Rule | Type | Details |
|---|------|------|---------|
| 11.1.1 | MSO-only analysis | Hard rule | Base ALL analysis on price data in MSO. If a price level/swing/pattern is not present in MSO, it does not exist. |
| 11.1.2 | Unclear = "unclear" | Hard rule | If cannot determine structure direction with high confidence, state "unclear" -- do not force classification. |
| 11.1.3 | JSON-only output | Hard rule | Respond with ONLY valid JSON matching schema. Must start with { and end with }. No preamble, no markdown fences, no explanation outside JSON. |

### 11.2 Internal Consistency Rules

| # | Rule | Type | Details |
|---|------|------|---------|
| 11.2.1 | CANDIDATE requires CHoCH | Hard rule | If decision is CANDIDATE, m15_confirmation.choch_detected MUST be true (otherwise violates U3). |
| 11.2.2 | No CHoCH = NO_TRADE | Hard rule | If m15_confirmation.choch_detected is false, decision MUST be NO_TRADE. |
| 11.2.3 | No POI = NO_TRADE | Hard rule | If h1_setup.poi_identified is FALSE or h1_setup.poi_type is "none", decision MUST be NO_TRADE. The OB retest framework requires price to pull back to an H1 POI. Without valid H1 POI, setup sequence is incomplete regardless of M15 confirmation quality. |

### 11.3 Conciseness Rules

| # | Rule | Type | Details |
|---|------|------|---------|
| 11.3.1 | Section brevity | Hard rule | Keep each reasoning section explanation to 1-2 sentences. State conclusion and key evidence only. |
| 11.3.2 | Overall reasoning limit | Hard rule | overall_reasoning field MUST be under 100 words. |
| 11.3.3 | No repetition | Hard rule | Do NOT repeat information already captured in structured fields (direction, confidence, prices). |
| 11.3.4 | NO_TRADE brevity | Guidance | For NO_TRADE decisions, be especially brief -- state which step failed and why in one sentence per section. |

### 11.4 Reasoning Quality Signals

| # | Signal | Type | Details |
|---|--------|------|---------|
| 11.4.1 | Data grounding score | Guidance | Reference 8+ distinct price levels in analysis (highs, lows, OB zones, FVGs, SL, TP). Analyses citing specific prices outperform vague ones by +17pp win rate. |
| 11.4.2 | Conviction clarity score | Guidance | Avoid hedging phrases (however, although, unclear, mixed, choppy, minimal, weak) unless genuinely applicable. Analyses with <= 2 hedging phrases outperform by +13pp. |
| 11.4.3 | Hedging vs NO_TRADE | Guidance | If setup is genuinely weak, say NO_TRADE rather than hedging a CANDIDATE. |

---

## 12. Output Format / JSON Schema

### 12.1 Top-Level Fields

| # | Field | Type | Details |
|---|-------|------|---------|
| 12.1.1 | timestamp_utc | Required | ISO-8601 timestamp of candle being evaluated. |
| 12.1.2 | model_used | Required | Model identifier string. |
| 12.1.3 | decision | Required | "NO_TRADE" or "CANDIDATE" or "WAIT". |
| 12.1.4 | confidence_score | Required | 0-100 integer. |
| 12.1.5 | confidence_computation | Required | String showing computation breakdown. |
| 12.1.6 | framework | Required | "ob_retest" or "breaker_retest" or "none". |
| 12.1.7 | kill_zone | Required | "london" or "ny". |
| 12.1.8 | frameworks_evaluated | Required | Object with ob_retest and breaker_retest sub-objects, each with qualified (bool) and reason (string). |
| 12.1.9 | no_trade_reason | Required | Brief reason if NO_TRADE, else null. |
| 12.1.10 | wait_reason | Required | Brief reason if WAIT, else null. |

### 12.2 Reasoning Sub-Object

| # | Field | Type | Details |
|---|-------|------|---------|
| 12.2.1 | daily_bias | Required | direction (bullish/bearish/ranging), confidence (high/medium/low), protected_swing_level (float or 0.0), explanation (1-2 sentences). |
| 12.2.2 | h4_alignment | Required | aligned (bool), h4_pois_identified (array of OB/FVG descriptions), explanation. |
| 12.2.3 | h1_setup | Required | poi_identified (bool), poi_type (OB/FVG/liquidity_zone/none), poi_price_level (float), zone (premium/discount/neutral), fib_retracement_pct (float 0-100), causing_event_type (BOS/CHoCH/unknown), explanation. |
| 12.2.4 | liquidity_sweep | Required | detected (bool), pool_type (asian_high/asian_low/pdh/pdl/equal_highs/equal_lows/session_high/session_low/london_high/london_low/none), sweep_quality (clean/messy/ambiguous), sweep_price (float), explanation. |
| 12.2.5 | m15_confirmation | Required | choch_detected (bool -- must be TRUE for CANDIDATE), displacement_quality (strong/medium/weak/none), displacement_candle_body_vs_avg_ratio (float), explanation. |
| 12.2.6 | similar_historical_setups_considered | Required | Array (can be empty). |
| 12.2.7 | setup_grade | Required | "A+" / "A" / "B+" / "B" / "C". |
| 12.2.8 | overall_reasoning | Required | 2-4 sentence summary, under 100 words. |

### 12.3 Trade Parameters (when CANDIDATE)

| # | Field | Type | Details |
|---|-------|------|---------|
| 12.3.1 | direction | Required | "LONG" or "SHORT". |
| 12.3.2 | entry_price | Required | Float. |
| 12.3.3 | stop_loss | Required | Float. |
| 12.3.4 | sl_buffer_applied | Required | Float. |
| 12.3.5 | take_profit_1 | Required | Float. Exactly 1.5x SL distance from entry. |
| 12.3.6 | take_profit_2 | Required | Float. 0 if not applicable. |
| 12.3.7 | take_profit_3 | Required | Float. 0 if not applicable. |
| 12.3.8 | risk_reward_ratio | Required | Float. |
| 12.3.9 | position_size_lots | Required | Fixed at 0.01. |

---

## 13. Cross-Instrument and Volatility Context (Optional Block)

Enabled per instrument via config `cross_instrument_context.enabled`. When enabled, injected into user message.

| # | Item | Type | Details |
|---|------|------|---------|
| 13.1 | XAUUSD D1 direction | Guidance | Reports XAUUSD D1 structure direction and inferred dollar direction via configurable mapping. |
| 13.2 | Asian session range | Guidance | Reports Asian range as absolute value and percentage of ADR, with category label. |
| 13.3 | **Conflicting direction rule** | Guidance (strong) | If proposed trade direction CONFLICTS with XAUUSD D1 direction (e.g., LONG GBPUSD but gold D1 bearish), this is a "significant macro headwind." Both instruments respond to USD flows. Require "exceptionally strong H1+M15 confluence" to proceed. If confluence not exceptional --> NO_TRADE. |
| 13.4 | **Narrow Asian range rule** | Guidance (strong) | If Asian range < 28% of ADR, pre-London session built minimal liquidity. Displacement setups in narrow-range environments have historically shown 33% win rate. Require stronger-than-normal displacement quality (> 2.5x average body) to proceed. |
| 13.5 | **Combined unfavorable rule** | Hard rule | If BOTH signals unfavorable (conflicting direction AND narrow Asian range) --> NO_TRADE regardless of other factors. |

---

## 14. Knowledge Base / System Context (User Message)

Injected into user message when KB data is available.

| # | Item | Type | Details |
|---|------|------|---------|
| 14.1 | Rolling stats | Guidance | Trade count, win rate, expectancy (R), profit factor. |
| 14.2 | Last 10 trades | Guidance | Win/Loss with R-multiple for each. |
| 14.3 | Active failure patterns | Guidance (caution) | Up to 3 caution descriptions from failure pattern detection. |
| 14.4 | Current regime | Guidance | Regime label (from layer1). |

---

## 15. Session Memory (User Message)

| # | Item | Type | Details |
|---|------|------|---------|
| 15.1 | Prior candle assessments | Guidance | Previous candle evaluations from current kill zone session are provided. |
| 15.2 | Progression awareness | Guidance | Prompt asks: "Is a setup developing across candles? Did a prior candle show a sweep or displacement that sets up the current candle? If you said WAIT or noted a developing pattern on a prior candle, check if the trigger has now occurred." |

---

## 16. Configurable Parameters (Instrument-Specific)

| # | Parameter | Source | Default (XAUUSD) |
|---|-----------|--------|-------------------|
| 16.1 | sl_absolute_min | config.risk.sl_absolute_min | 5.0 ($5.00) |
| 16.2 | zone_width_max | config.prompt.zone_width_max | 15.0 ($15) |
| 16.3 | ob_buffer | config.prompt.ob_buffer | 1.50 ($1.50) |
| 16.4 | price_format | config.prompt.price_format | ".2f" |
| 16.5 | kill_zones | config.market.kill_zones | London 07:00-09:30, NY 13:00-15:30 |
| 16.6 | Unit system | Derived from symbol | Pips (standard forex), pips (JPY pairs), points (indices), dollars (gold/silver/other) |

---

## 17. Complete Decision Tree: TRADE vs NO_TRADE

Summary of all conditions that force NO_TRADE:

| # | Condition | Source |
|---|-----------|--------|
| 17.1 | No directional consensus across D1/H4/H1 | U1 |
| 17.2 | H4 does not align with D1 (when D1 clear) | U2 |
| 17.3 | Both D1 and H4 are unclear/ranging | U2 |
| 17.4 | No M15 CHoCH with displacement in trade direction | U3 |
| 17.5 | Trade direction does not match established bias | U4 |
| 17.6 | Risk-to-reward < 1:1.5 | U5 |
| 17.7 | Stop loss < 1.5x M15 ATR(14) or < absolute minimum | U6 |
| 17.8 | Setup trigger outside active kill zone | U7 |
| 17.9 | No H1 CHoCH or BOS in aligned direction (OB path) | OB1 |
| 17.10 | No unmitigated H1 OB from impulse leg (OB path) | OB2 |
| 17.11 | Price not at/near OB zone (OB path) | OB3 |
| 17.12 | OB not in correct premium/discount zone (OB path) | OB4 |
| 17.13 | No unretested breaker block aligned with bias (BR path) | BR2 |
| 17.14 | Price not at/near breaker zone (BR path) | BR3 |
| 17.15 | Neither OB Retest nor Breaker Retest qualifies | Step 2 |
| 17.16 | Self-check raises doubt | Step 3 |
| 17.17 | Setup grade B+ or below | Grading |
| 17.18 | h1_setup.poi_identified is FALSE or poi_type is "none" | Anti-hallucination 11.2.3 |
| 17.19 | m15_confirmation.choch_detected is false | Anti-hallucination 11.2.2 |
| 17.20 | Conflicting signals across timeframes | Critical Rule 9.4 |
| 17.21 | Both cross-instrument signals unfavorable (conflicting direction + narrow Asian range) | Cross-instrument 13.5 |

Conditions that allow CANDIDATE:

| # | Condition |
|---|-----------|
| C1 | Valid directional bias established (U1 passes) |
| C2 | H4 aligned with bias (U2 passes) |
| C3 | Either OB Retest (OB1-OB7) or Breaker Retest (BR1-BR7) fully qualifies |
| C4 | M15 CHoCH + displacement confirmed (U3 passes) |
| C5 | Direction matches bias (U4 passes) |
| C6 | RR >= 1:1.5 (U5 passes) |
| C7 | SL meets both ATR and absolute minimum requirements (U6 passes) |
| C8 | Within active kill zone (U7 passes) |
| C9 | Setup grade is A+ or A |
| C10 | Self-check passes without doubt |
| C11 | All internal consistency rules satisfied (CHoCH true, POI identified) |

---

## 18. Implicit Biases and Nudges

Features in the prompt that may influence decision rate beyond neutral evaluation:

| # | Feature | Direction | Details |
|---|---------|-----------|---------|
| 18.1 | Self-check questions | Conservatism bias | Four questions all push toward doubt/downgrade. No balancing question like "Am I being too cautious?" |
| 18.2 | Hedging phrase penalty | Aggression bias | Discourages hedging language (+13pp stat), which may push the model to sound more confident even when uncertainty exists. Partially offset by "if genuinely weak, say NO_TRADE." |
| 18.3 | Data grounding reward | Neutral | Encourages citing 8+ price levels (+17pp stat). Rewards thoroughness. |
| 18.4 | Impulse compactness signal | Conservatism bias | 85% vs 55% continuation rate comparison favors rejecting trades with longer impulse legs. |
| 18.5 | Conflicting signals default | Conservatism bias | "When signals conflict, default to NO_TRADE" -- no room for judgment on degree of conflict. |
| 18.6 | B+ grade rejection | Conservatism bias | Any criterion not cleanly met = B+ or below = rejected. Binary pass/fail on "cleanly met." |
| 18.7 | FVG positive signal | Aggression bias (mild) | +11% continuation rate encourages trading when FVG present. |
| 18.8 | OB absorption caution | Conservatism bias (mild) | -5% continuation rate discourages trades at pre-existing OB zones. |
| 18.9 | Narrow Asian range gate | Conservatism bias | 33% win rate stat + 2.5x body requirement creates high bar for narrow-range sessions. |
| 18.10 | Failure patterns injection | Conservatism bias | Active failure patterns from KB shown as "Cautions" -- no corresponding "Strengths" section. |

---

## 19. Data Provided to the Model (User Message Structure)

| # | Block | Content |
|---|-------|---------|
| 19.1 | Static context (cached) | D1 structure, H4 structure, session levels (Asian H/L, PDH/PDL, London H/L), liquidity pools (excluding session H/L), data quality flags. |
| 19.2 | Dynamic context (per candle) | Current candle timestamp, session H/L, London H/L, detected sweeps, H1 structure + OBs + breakers + FVGs + premium/discount + avg body + ATR, M15 structure + OBs + breakers + FVGs + premium/discount + avg body + ATR, recent M15 swings (last 10). |
| 19.3 | KB context | Rolling stats, last 10 trades, active failure patterns (up to 3). |
| 19.4 | Session memory | Prior candle assessments from current kill zone session. |
| 19.5 | Cross-instrument context | XAUUSD D1 direction + dollar inference, Asian range vs ADR. |
| 19.6 | Additional context | Generic additional context slot (passthrough). |
| 19.7 | Final instruction | "Evaluate this candle for BOTH the OB Retest and Breaker Block Retest setups. The active kill zone is: {kill_zone}. Output your analysis as JSON." |

---

## 20. MSO Character Limit

| # | Item | Type | Details |
|---|------|------|---------|
| 20.1 | _MAX_MSO_CHARS | Hard limit | 60,000 characters (~20,000 tokens at ~3 chars/token). |
