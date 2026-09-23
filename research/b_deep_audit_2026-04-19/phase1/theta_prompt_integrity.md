# Agent θ — Prompt + Context Integrity Audit (Phase 1, Deep Diagnostic Sprint)

**Author:** Claude Code Opus 4.7 research agent (session 35, Phase 1 dispatch, hypothesis: prompt limits AI)
**Scope:** Read-only audit of `src/prompts/primary_analyzer_prompt.py`, call site `src/components/primary_analyzer.py`, one example MSO (`knowledge_base/pipeline_state/02_market_state.json` — captured EURUSD snapshot, 329 KB, 606 sweeps, 174 M15 swings), and three T7 sim corpora. **No prompt / code changes shipped — scope only.**
**Date:** 2026-04-19
**Output:** this file → `research/b_deep_audit_2026-04-19/phase1/theta_prompt_integrity.md`
**Input artefacts produced:** `_theta_scratch/render_and_count.py`, `_theta_scratch/samples/{XAUUSD,US30_cash,USDJPY,GBPJPY,EURUSD}__{system,user}.txt`, `_theta_scratch/token_counts.json`

---

## Executive verdict

The prompt is **not being truncated**; the 200K Sonnet context is 40-60× larger than the rendered message. The real limits are **shape**, not size:

1. **The prompt contains no output-precision instruction.** The AI is not told what decimal precision to use on `entry_price/stop_loss/take_profit` for any instrument. `_PRICE_FMT` (`primary_analyzer_prompt.py:14`) controls *input-rendering* only; it never appears in the instruction text. Result: **59.7% EURUSD degenerate outputs** (entry=SL=TP, verified re-tally, n=300), **0% on XAUUSD and NAS100**. This is the #1 leak identified, quantified, and directly attributable to the prompt. **[D3-1, HIGH CONFIDENCE]**
2. **`sl_buffer_applied: 0.0` is hard-coded in the prompt schema.** Line 155 literally instructs the AI: *"sl_buffer_applied: 0.0"*, and line 236 repeats *"sl_buffer_applied: 0.0"* inside the CANDIDATE trade_parameters JSON block. The 100% universal zero across 1053/1053 XAUUSD + 165/165 NAS100 records is not an AI failure — it is an AI *compliance*. **[D3-2, HIGH CONFIDENCE]**
3. **Truncation is NOT token-budget-driven** (prompt is only 3-4k tokens). Truncation is *structural* and silent: the user message hard-slices to `sweeps[:5]`, `fvgs[-5:]`, `obs[-5:]`, `swings[-10:]`, `pools[:10]`. The MSO used to verify this was EURUSD Apr 17, which had **606 sweeps → 5 shown, 87 M15 FVGs → 5 shown, 121 liquidity pools → 10 shown, 174 M15 swings → 10 shown**. **The AI sees <5% of detected structure.** [D3-3, MEDIUM CONFIDENCE on impact; HIGH on the fact]
4. **Output rigidity kills nuance.** `decision: NO_TRADE | CANDIDATE` is binary; `confidence_score: <50-90>` is an unexplained continuous band with no semantic guidance, and empirically collapses to five discrete values (68/72/75/78/82/85) that cluster — per prior CLAUDE.md note — at 98% confidence=80. The schema has no "weak bias" or "developing" signal. **[D3-4, HIGH CONFIDENCE]**
5. **Subtle LONG primacy.** Every trade-geometry example (`C3`, `entry_price`, `stop_loss`, `take_profit_1`) lists LONG first. Combined with deterministic D1-bias-lag, this may compound NAS100's 36:1 LONG:SHORT asymmetry. [D3-5, EXPLORATORY, this is contributory; root cause is upstream]
6. **Field coverage is narrow by design** — C-gate philosophy. The prompt explicitly tells the AI to **ignore** OB/FVG/zone data for the CANDIDATE decision (lines 141-143). This is a validated design choice (T7 C-gate: CR=86%, WR=66.3% > P2A v1's CR=38%) but it means rich MSO structure is rendered but unused, which is wasteful but not a bug.

Two of the five items are direct causes of confirmed edge leaks (items 1 + 2). The other three are plausible contributors that need scoped proposals.

---

## 1. Prompt word/token budget — rendered across 5 diverse MSOs

Script: `_theta_scratch/render_and_count.py`. Used the captured MSO at `knowledge_base/pipeline_state/02_market_state.json` (EURUSD Apr 17 snapshot, 329 KB, 606 sweeps, 174 swings, 37 M15 OBs) and rendered against five per-instrument configs from `config/agent_config.yaml`.

### Token counts (char-based estimator, 3-4 chars/token)

| Instrument | price_format | system chars | user chars | total chars | total tokens (lo) | total tokens (hi) |
|------------|--------------|-------------:|-----------:|------------:|------------------:|------------------:|
| XAUUSD     | `.2f` | 8,764 | 2,909 | 11,673 | 2,918 | 3,891 |
| US30_cash  | `.2f` | 8,768 | 2,909 | 11,677 | 2,919 | 3,892 |
| USDJPY     | `.3f` | 8,855 | 3,001 | 11,856 | 2,964 | 3,952 |
| GBPJPY     | `.3f` | 8,856 | 3,001 | 11,857 | 2,964 | 3,952 |
| EURUSD     | `.5f` | 8,960 | 3,185 | 12,145 | 3,036 | 4,048 |

### Verdict: no truncation risk

Claude Sonnet 4.6 context window: **200,000 tokens**. Rendered input is **3-4k tokens**. Headroom is **40-60×**. Output cap is `max_tokens=2000` (`primary_analyzer.py:224/338`), also far from binding given the in-prompt instruction "CANDIDATE response: under 600 tokens" (line 245). **There is no token-budget truncation on the input side.**

### BUT — hidden structural truncation

The user message hard-slices the MSO in `primary_analyzer_prompt.py:_format_tf` and `build_static_context`:

| Element | Hard-slice | MSO had (Apr 17 EURUSD snapshot) | Shown | Pct |
|---------|-----------|---------------------------------|------:|----:|
| `detected_sweeps` | `[:5]` (line 396) | 606 | 5 | **0.8%** |
| `liquidity_pools` static | `[:10]` (line 367) | 123 | 10 | 8.1% |
| `order_blocks` per TF | `[-5:]` (line 286) | 37 M15 / 8 H1 / 4 H4 / 1 D1 | 5 / 5 / 4 / 1 | 13-100% |
| `breaker_blocks` per TF | `[-5:]` (line 295) | 26 M15 / 2 H1 | 5 / 2 | 19-100% |
| `fair_value_gaps` per TF | `[-5:]` (line 304) | 87 M15 / 18 H1 / 18 H4 / 8 D1 | 5 / 5 / 5 / 5 | 6-63% |
| `structure_events` per TF | `[-5:]` (line 278) | 37 M15 / 9 H1 | 5 / 5 | 14-56% |
| M15 `swings` | `[-10:]` (line 409) | 174 | 10 | **5.7%** |

**The AI sees 0.8% of detected sweeps and 5.7% of M15 swings on a realistic MSO.** The `[-5:]` / `[-10:]` slicing is deliberate-looking, but there is no comment explaining why those numbers, and the 5-of-87 M15 FVG slice for a dense instrument is a real information-loss risk. **Relevance of this is conditional** — the C-gate only uses structure_events (BOS/CHoCH), and those are already showing the last 5 which is usually the relevant set. The sweeps/pools are used for the `liquidity_sweep` observation report (not the decision), so the cost is mostly logging quality.

---

## 2. Field-coverage audit — MSO vs prompt output

### MSO schema spine (183 unique key-paths across timestamp / timeframes{D1,H4,H1,M15} / session_levels / equal_highs / equal_lows / liquidity_pools / detected_sweeps / data_quality / high_impact_events / spread_cents)

### What the prompt surfaces per-TF

From `_format_tf` (lines 262-342):
- `structure.direction`, `structure.protected_swing.{price,time}` — surfaced
- `structure_events[-5:]`: `{type, time, level_broken, direction, displacement_present, displacement_ratio}` — surfaced
- `order_blocks` (unmitigated, `[-5:]`): `{type, high, low, open, close, causing_event_type, touch_count, formation_time}` — surfaced
- `breaker_blocks` (unretested, `[-5:]`): `{direction, zone_high, zone_low, original_ob_direction, formation_time, mitigation_time}` — surfaced
- `fair_value_gaps` (unfilled, `[-5:]`): `{type, top, bottom}` — surfaced (midpoint/candle_indices/formation_time **dropped**)
- `premium_discount.{equilibrium_50, fib_62, fib_79}` — surfaced; but `{discount_zone, premium_zone, ote_zone, impulse_high, impulse_low}` are **NOT surfaced**
- `avg_candle_body`, `atr_14` — surfaced
- `clv_current`, `clv_avg_5` — surfaced (line 320)
- `bvc_buy_fraction`, `net_flow_5` — surfaced (line 328)
- `atr_session`, `session_vol_ratio` — surfaced *only if populated* (line 335); per prompt comment, XAUUSD M15 only

### MSO fields NEVER surfaced (priority-ranked by informational value)

| Rank | Field | Location | Why it matters | C-gate decision? | Observation logging? |
|-----:|-------|----------|----------------|------------------|--|
| 1 | `timeframes.{TF}.premium_discount.{discount_zone, premium_zone, ote_zone, impulse_high, impulse_low}` | per TF | H1 OB's zone=premium vs discount is a known edge qualifier (NAS100 synthesis: 0W/6L at premium vs 22W/5L at discount, Fisher p<0.001 at n=33). The prompt *asks* the AI to fill `zone: premium | discount | neutral` (line 203) but gives it only the fib levels + equilibrium. The zone-of-OB classification is ambiguous given the *zones* themselves are not rendered. | No (explicitly excluded) | **Yes — would sharpen `h1_setup.zone` observation field** |
| 2 | `equal_highs / equal_lows` arrays | root | Dense liquidity clusters drive sweep logic. Prompt renders them as individual `liquidity_pools[type=equal_highs]` truncated to first 10 (proximity-sorted). On EURUSD Apr 17, 55 equal-highs + 60 equal-lows collapse to 10 printed — visually confusing ("equal_highs: 1.18000" appears 9 times in a row, per sample). | No | Partial — sweep detection should show which pool got swept, but `liquidity_pools` ordering is by distance from PDH/PDL midpoint (line 364), not by relevance to current price. |
| 3 | `high_impact_events` | root | **Never surfaced in the prompt at all.** Feature exists (news filter at code level, see `config.economic_calendar`), but the AI is never told if the evaluated candle is near a news event. On the MSO: 0 events. Empty state obscures whether the field is plumbed. | No (code-level filter elsewhere) | Yes — could be a useful caveat the AI should know about |
| 4 | `spread_cents` (value itself) | root | Surfaced only as binary `spread_normal` via `data_quality` (line 375). Raw value not rendered. AI could make more nuanced calls in wider-spread regimes. | Optional | Yes |
| 5 | `session_levels.session_high / session_low` | root | Rendered in dynamic context line 388. Present. *(correctly surfaced)* | N/A | N/A |
| 6 | `timeframes.{TF}.swings` (non-M15) | per TF | D1/H4/H1 swings NOT surfaced — only M15 last-10. Non-M15 swings are represented only by the `structure.protected_swing` singleton. For a "read the structure carefully" task, the AI is given 6 H1 swings via the `structure_events` list, not the full swing sequence. | Partial (protected_swing is surfaced) | Contributes to `daily_bias.protected_swing_level` |
| 7 | `detected_sweeps[5:]` | root | The remaining 601 sweeps (of 606 on this MSO). These are historical and mostly irrelevant on a fresh M15 candle, but the sort is index-order (`[:5]`, not "most recent", not "nearest to current price"), which is likely wrong. Line 396 has no `reverse=True`. | No | Yes — `liquidity_sweep.detected/pool_type/sweep_quality` observation depends on these |
| 8 | `timeframes.M15.structure.swing_sequence`, `hh_count`, `hl_count`, `lh_count`, `ll_count` | per TF | Useful summary of the recent price pattern; would help the C2 (M15 non-opposition) gate decision by giving explicit "LH-LH-LH sequence = opposing H1" signal. Currently the AI must infer from the 5-element `structure_events` list. | **Yes** (directly fills C2) | — |
| 9 | `data_quality.{mt5_connected, timestamp_utc}` | root | Timestamp is redundant; mt5_connected is a safety bit the AI doesn't need. *(correctly not surfaced)* | No | No |
| 10 | `timeframes.M15.breaker_blocks.original_ob_direction, timeframe` | per TF | Line 298 surfaces original_ob_direction as "orig=". Good. `timeframe` field is self-referential and correctly dropped. | — | — |

### Priority conclusion

The three fields with **highest informational value** that are NOT surfaced:

1. **Per-TF premium_discount zones** — would improve `zone: premium | discount | neutral` accuracy, which is the key ingredient in the NAS100 premium=0% WR signal (n=6, Fisher p<0.001). [HIGH CONFIDENCE, would need prompt change]
2. **High-impact news proximity** — additive context; news calendar is filtered at code level elsewhere but the AI is not told. [MEDIUM CONFIDENCE, would need prompt change + data plumbing check]
3. **Swing-sequence string** — quick C2 gate signal for M15 non-opposition. [MEDIUM CONFIDENCE]

**Caveat:** the entire C-gate design (lines 141-143) explicitly commands the AI to *ignore* OB / FVG / zone data for the CANDIDATE decision. These fields matter for observation output and for the new prompt-schema's nuance, not for C-gate pass/fail.

---

## 3. Bias-inducing language scan

### LONG primacy (every example)

- Line 132 `C3. DIRECTION MATCH`: "H1 bullish → LONG. H1 bearish → SHORT."
- Line 150 `entry_price`: "ob_high for LONG (top of nearest unmitigated H1 OB), ob_low for SHORT (bottom of nearest unmitigated H1 OB)"
- Line 151 `stop_loss`: "below nearest significant H1/M15 swing low (LONG) or above swing high (SHORT)"
- Line 152 `take_profit_1`: "entry + 1.5 x |entry - stop_loss| (LONG) or entry - 1.5 x |stop_loss - entry| (SHORT)"
- Line 233 schema: `"direction": "LONG | SHORT"`

**LONG is always cited first.** In schemas like `bullish | bearish | ranging` (line 189), bullish is also first. Ordering in LLM prompts is known to have a mild primacy effect (citation: anthropic system-card, "first option is weakly preferred").

**Cross-reference to observed data:**
- NAS100: CANDIDATEs LONG:SHORT = 36:1 (97.3% LONG)
- XAUUSD all-intent LONG:SHORT = 154:0 (100% LONG in slice 2 — but note: XAUUSD's Q1 2026 was +11.6% trending LONG, so some skew is regime-driven, not prompt-driven)
- EURUSD all-intent LONG:SHORT = 284:16 (94.7% LONG — on a range-bound window, this is anomalous)

**Verdict:** Regime explains most of the XAUUSD skew (confirmed by T3.2 verdict). The NAS100 36:1 was 54 weeks of bearish bias during a +4.20% rally (D1-bias-lag, NOT prompt) per session 34 NAS100 synthesis. **But** EURUSD's 284:16 on a flat market cannot be explained by regime alone (the D1 signal was 74% bearish — AI should have produced at least balanced LONG:SHORT if the output geometry was symmetric). Session 34 EURUSD synthesis calls this "a prompt-level SHORT geometry failure." Combined with the LONG-first primacy and the SHORT-only path getting the *second* example in every mechanical instruction, a prompt-level fix is plausible:

**[D3-5, EXPLORATORY, 2-tier impact: small primacy effect + possible SHORT-specific degeneracy]** Balance LONG/SHORT examples by alternating order, OR add a symmetric "SHORT case mirror" block. Risk: none (semantically identical). Impact: unknown — could be 0 to meaningful.

### Session bias

- Both kill zones mentioned equally in `kz_display` (rendered from config).
- "Historical base rate: 65-80% of evaluated setups qualify as CANDIDATE" (line 114) is regime-independent language.
- No session-specific preference language.

### Structure-type bias

- Prompt enforces OB Retest framework only (line 146). This is not a bias — it is a design decision. Rejected alternatives (FVG-only, session reversal, sweep-displacement) are handled by gating, not prompt language. Agent η will explore alternative patterns; out of θ scope.

---

## 4. Output format rigidity — can the AI express nuance?

### Hard-coded binary decision (line 134-136)

```
C1 AND C2 AND C3 all pass → **CANDIDATE**
Any gate fails → **NO_TRADE**
There is no WAIT category.
```

**No middle ground.** "WAIT" is explicitly forbidden. This is intentional (C-gate design: the gate pass IS the quality gate).

### `confidence_score: <50-90>` — a useless slot

- Line 180 schema: `"confidence_score": <50-90>`
- No rule in the prompt explains how to pick a value. No definition of what 70 vs 80 vs 85 means.
- Empirically (from XAUUSD slice 2 n=272): clusters on only five values — 72 (93 records, 34%), 78 (96 records, 35%), 82 (60 records, 22%), 85 (18 records, 7%), 75 (5 records, 2%).
- EURUSD n=2280: 844 at 72 (37%), 142 at 78 (6%), 48 at 82 (2%), 20 at 85 (1%).
- Per CLAUDE.md: "confidence_scorer confirmed useless (98% get confidence=80)". 2026-04 data shows this has moved toward 72 but still discrete and semantically empty.
- **Verdict: `confidence_score` is a decorative field.** It is NOT used by the pipeline (confirmed: `confidence_filter_mode: shadow`, CLAUDE.md). Proposals:
  - **Remove it** (saves tokens, eliminates confusion) OR
  - **Define it** (e.g., "90 = 3+ displacement-present BOS in H1 same direction; 50 = mixed / 1 weak BOS") — but removal is cleaner given the C-gate design says "the gate pass IS the quality gate."

### `setup_grade: A+ | C` — also useless

- Line 222 schema + line 166 instruction: "Always 'A+' for CANDIDATE (the C-gate pass IS the quality gate). 'C' for NO_TRADE."
- This is tautological — the grade is 100% determined by decision. Code-level normalization (`primary_analyzer.py:536-540`) even accepts A/B+/B/A- as fallbacks because the AI sometimes deviates. But the legal values per prompt are only A+ and C. So any deviation is silent value loss.

### `overall_reasoning: <1-2 sentences>` — the only free-text field that matters

- This is where the AI can express nuance. But the prompt caps it at 1-2 sentences (token-pressure language). There is NO field for "setup is developing, mark interesting" or "bias weakening" or "cross-pattern observation."
- In the 818 NAS100 calls, session-memory was disabled (per CLAUDE.md) so each candle evaluation is a one-shot. There is no affordance for "watchlist."

### JSON schema rigidity — nuance is engineered out

| Nuance type | Prompt support |
|-------------|----------------|
| "Good setup but weak bias" | **No** — confidence_score does not feed decisions |
| "Developing / watch" | **No** — no WAIT |
| "Exceptionally strong setup" | **No** — setup_grade is 100% A+ or C |
| "Setup qualifies but I'd prefer a retest" | **No** — only pass/fail |
| "Cross-pattern signal" | **No** — `similar_historical_setups_considered: []` is empty in the schema and the prompt never asks for substantive content |

**Verdict:** Output is rigid by design. Adding nuance channels would make the pipeline incoherent with the existing gate-only downstream (verification.py, permissions.py). **Real lever:** if we kept the binary decision but let the AI emit a *gradient* score used in post-AI filtering (e.g., "a secondary filter requires confidence_displacement ≥ 1.5×avg body"), the primacy changes. But that is a pipeline change, not a prompt change, and out of scope.

**[D3-4, HIGH CONFIDENCE]** Remove or instrument the `confidence_score` field. If we remove it, the prompt shrinks by ~50 tokens and we eliminate an attractor for the AI's false precision. If we instrument it (e.g., explicit rubric), it could become a useful post-AI ordering signal for any future "top-k per KZ" logic.

---

## 5. SL-buffer field analysis — why is `sl_buffer_applied: 0.0` universal?

### The prompt literally instructs the AI to output zero

**Line 155 (in the "TRADE PARAMETERS" narrative):**
```
- sl_buffer_applied: 0.0
```

**Line 236 (in the CANDIDATE trade_parameters JSON schema block):**
```json
"sl_buffer_applied": 0.0,
```

Both are **literal zeros**, not placeholders like `<float>`. The AI is being compliant, not creative.

### Field-level evidence

| Corpus | Total with trade_parameters | `sl_buffer_applied == 0.0` |
|--------|----------------------------:|---------------------------:|
| XAUUSD (T3.2) | 1053 | 1053 (100.0%) |
| NAS100 (T3.1) | 165 | 165 (100.0%) |
| EURUSD (session 34) | 300 | 300 (100.0%) |

**1518 / 1518 records are `sl_buffer_applied = 0.0`.** The AI never deviates, because the prompt never allowed it to. This is not a hallucination — this is the prompt committing the pipeline to a hardcoded zero.

### Consequence

When combined with the prompt's `entry_price` rule (line 150 — "ob_high for LONG / ob_low for SHORT" i.e. the OB bound) and `stop_loss` rule (line 151 — "below nearest significant H1/M15 swing low" which is often also the OB low for tight OBs), the AI places SL exactly at or inside the OB zone bound. That triggers:

- `sl_beyond_ob` L2 gate rejections (20 on XAUUSD, 46 on NAS100, 81 on EURUSD per session 34 synthesis).
- Bit-exact SL=OB bound → any wick reaching OB bound stops the trade out.

### The fix path is contested

Per session 34 T3.2 verdict (`research/t3_2_sl_beyond_ob_cross_instrument_audit/verdict.md:212-233`): a prompt fix requiring non-zero `sl_buffer_applied` captures most of the NAS100 +13.5R upside without the XAUUSD -1R downside (the gate fix, T2.9, has the opposite cross-instrument sign). So the prompt fix is the **preferred path** but is blocked on:

1. NAS100 1-pip epsilon revalidation (tier A2, now landed — see `5bdf6f0`).
2. CEO approval (WF-1 / prompts change).

### Root-cause verdict

**[D3-2, HIGH CONFIDENCE]** `sl_buffer_applied: 0.0` is a prompt-side hard-coded directive. Removing the literal zero and replacing it with `<float, non-zero, calibrated per-instrument ATR>` + an accompanying instruction (e.g., "apply `sl_buffer_applied` ≥ 0.2 × H1 ATR below/above the OB bound; report the buffer you applied in this field") would end the universal-zero pattern at the source.

---

## 6. FX precision directive — does the prompt instruct the AI on decimal precision?

### The mechanism exists for INPUT only

`primary_analyzer_prompt.py:14`:
```python
_PRICE_FMT = ".2f"
```

and `primary_analyzer_prompt.py:22-25` (setter):
```python
def set_price_format(fmt: str) -> None:
    """Set the price format string for the current instrument."""
    global _PRICE_FMT
    _PRICE_FMT = fmt
```

Used in the f-strings at lines 271, 279, 287-289, 296-299, 305, 310, 315, 338, 340, 353-355, 368, 389, 391, 399, 410 — all of which format **numeric values written INTO the prompt for the AI to read**.

### `_PRICE_FMT` is NEVER referenced in the instruction body

Grep confirms: lines 1-254 of the system-prompt template (the instruction text) contain **zero mentions of precision, decimal places, digits, or `{_PRICE_FMT}`**. The AI is told to output `<float>` values but never told how many decimal places to use.

### Consequence

**Same test across three corpora, same script:**

| Corpus | `(entry=SL) or (entry=TP) or (SL=TP)` among non-zero CAND+L2+BL | Rate |
|--------|---------------------------------------------------------------:|-----:|
| XAUUSD (`.2f`, price ~4000) | 0 / 764 | **0.0%** |
| NAS100 (`.2f` ingested as `.1f`, price ~25000) | 0 / 203 | **0.0%** |
| EURUSD (`.5f`, price ~1.17) | 179 / 300 | **59.7%** |

**The AI rounds output to ~2 decimal places regardless of instrument.** On XAUUSD and NAS100 where the price magnitude is 4-5 digits, 2 dp is enough precision to produce distinct entry/SL/TP. On EURUSD where the price magnitude is 1.xxxx, 2 dp produces "1.18 = 1.18 = 1.18" collision → degenerate. Rendering the input as `.5f` does NOT change the AI's output precision because the prompt never instructs it to match.

### Input-rendering bug, on top of the output-precision hole

Verified in `_theta_scratch/samples/XAUUSD__user.txt`: when the EURUSD MSO (prices 1.17-1.18) is rendered with XAUUSD's `.2f` format, every OB bound prints as `1.17-1.17` or `1.18-1.18`. This is a call-site discipline issue: `set_price_format()` is global state, must be set per candle, and there is no assertion that the format matches the instrument. On NAS100 the `.1f` format on a 25000-magnitude price is adequate. On EURUSD `.5f` the format renders full precision. **The issue is output, not input** — but the input bug CAN appear in tests/backtests if the format is not set per call.

### Fix paths

**[D3-1, HIGH CONFIDENCE]** Two-part fix:

1. **Prompt addition (CEO approval required):** "Express `entry_price`, `stop_loss`, and all take_profit values to the full precision of the instrument: 5 decimal places for EURUSD/GBPUSD, 3 decimal places for USDJPY/GBPJPY/XAGUSD, 1 decimal place for NAS100, 2 decimal places for XAUUSD/US30. Never round."
2. **Post-AI validator (no approval needed, additive safety):** in `primary_analyzer.py:_parse_and_validate`, reject any CANDIDATE where `entry == stop_loss` or `entry == take_profit_1` within `1e-5`, demote to NO_TRADE with reason `degenerate_trade_parameters`. Already the pattern for `guard_candidate_null_params` (line 622).

Part 2 is allowed today per CLAUDE.md WF-1 discipline ("new safety gates — additive protection only"). Part 1 requires CEO approval.

---

## 7. TOP-5 PROMPT-CHANGE PROPOSALS (RANKED)

All changes require CEO approval per CLAUDE.md WF-1 discipline ("Changes to `prompts/` or `src/` that alter trading logic or evaluation behavior"). Batch-validation cost is re-running a T7 sim on XAUUSD (~$27) and optionally EURUSD ($30) / NAS100 ($23).

### D3-1 (HIGH CONFIDENCE) — Add FX decimal-precision instruction

**Specific change:** after line 157 (`take_profit_2, take_profit_3: 0.0`), add:

```
PRECISION: Express all prices to the native precision of the instrument.
- EURUSD, GBPUSD, AUDUSD, NZDUSD, USDCAD: 5 decimal places (e.g., 1.17234)
- USDJPY, EURJPY, GBPJPY, AUDJPY, NZDJPY, CADJPY, XAGUSD: 3 decimal places (e.g., 157.482)
- NAS100, US30: 1-2 decimal places (e.g., 26371.5 / 42318.22)
- XAUUSD: 2 decimal places (e.g., 4395.23)
Never round or truncate. Rounding introduces degenerate outputs where entry = SL.
```

**Expected impact:** eliminates 59.7% EURUSD degenerate rate (confirmed n=300). On XAUUSD/NAS100 rate is already 0%, so no effect there. If a future session broadens live to EURUSD/GBPUSD/USDJPY/GBPJPY, this is a blocker to lift.

**Risk if it lowers CR:** None plausible — the AI already outputs numbers; just at wrong precision.

**Batch-validation cost:** $30 EURUSD T7 re-run at honest fill epsilon (now that A1 is landed). Cross-check XAUUSD bit-exact reproducibility.

**WF-1 approval path:** direct CEO ask. Low-risk prompt addition; does NOT change decision logic (C-gates unchanged). **Unblocks EURUSD/GBPUSD live trading** (unresolved #7 in CLAUDE.md).

### D3-2 (HIGH CONFIDENCE) — Replace hard-coded `sl_buffer_applied: 0.0` with non-zero requirement

**Specific change:** line 155 change from:

```
- sl_buffer_applied: 0.0
```

to:

```
- sl_buffer_applied: non-zero buffer you applied to the raw swing extreme when computing stop_loss, in instrument-native units. Typical guidance: ≥0.2 × H1 ATR(14), ≥0.5 × M15 avg_candle_body, or the instrument's ob_buffer from config (shown to you in the Static Context as ATR/avg_body). Report the value applied; do not report zero unless you deliberately placed SL exactly at the swing extreme.
```

And line 236 change from `"sl_buffer_applied": 0.0,` to `"sl_buffer_applied": <float, non-zero>,`.

**Expected impact:** eliminates 100% bit-exact-SL=OB-bound rate. Per session 34 T3.2, captures ~+13R NAS100/quarter of the strict-`<` gate rejections (without needing T2.9 gate fix) and avoids the -1R XAUUSD downside. Direction on cross-instrument: positive on NAS100, neutral-positive on XAUUSD, unknown on US30/FX pairs.

**Risk if it lowers CR:** Possible — if the AI widens SLs beyond what the batch validates, the XAUUSD 62% WR baseline could shift. Risk is contained because the existing `sl_absolute_min` and `sl_floor` gates in code already clamp extreme widths.

**Batch-validation cost:** Full XAUUSD T7 re-run ($27) + NAS100 re-run ($23). ~$50 total. Compare WR and expectancy to baseline.

**WF-1 approval path:** CEO approval required. **Blocks T2.9 gate fix decision.** Per session 34 verdict, T2.prompt is the preferred path over T2.9.

### D3-3 (MEDIUM CONFIDENCE) — Sort-order + count tuning for truncated MSO fields

**Specific change:** adjust slices in `primary_analyzer_prompt.py` (this is code, not prompt text, but the user-facing prompt consequence is new) to:
- `detected_sweeps` — sort by recency (newest first), raise cap from 5 to 10.
- `liquidity_pools` — add `session_high`, `session_low`, PDH, PDL to always-rendered; sort by proximity to *current candle close*, not to `PDH/PDL midpoint`.
- `structure_events` — keep `[-5:]` (already by recency).
- Add `swing_sequence` string to the per-TF format (`"LH-LL-LH-LL"`) — a 1-line summary is almost free in tokens.
- Optional: add `premium_discount.{discount_zone, premium_zone}` top/bottom to the P/D line.

**Expected impact:** improves `zone: premium | discount` accuracy in observation output (potential +WR filter once shadow-promoted per NAS100 finding). Improves `liquidity_sweep` observation quality. Does NOT change C-gate logic so CR/WR baseline is preserved.

**Risk if it lowers CR:** minimal — C-gate decision is unchanged. Observation output quality improves. If the new `liquidity_pools` ordering shifts `liquidity_sweep.pool_type` distribution, downstream logs change shape but no logic depends on it today (confidence_filter_mode: shadow).

**Batch-validation cost:** zero (code change is in input-rendering only; re-run not strictly required, but a canary on 12 fixtures is recommended, ~$2).

**WF-1 approval path:** CEO approval required (it touches `src/prompts/`, even though no instruction-text lines change). **Soft priority — not blocking live.**

### D3-4 (HIGH CONFIDENCE) — Remove `confidence_score` field, remove `setup_grade`

**Specific change:** delete lines 180-181 (`confidence_score` + `confidence_computation`) and line 222 (`setup_grade`) from the output schema. Update `src/models/analysis_models.py` `PrimaryAnalysisOutput` to drop these fields. Update downstream code that writes them (grep will find them; they're currently shadow-logged only).

**Expected impact:**
- Saves ~50 tokens per call (~0.25¢/call across 5 instruments × 17 trades/mo × 12 candles/mo ≈ small absolute savings but free).
- Eliminates the "useless rubric" distraction per CLAUDE.md's own acknowledgement ("confidence scorer confirmed useless").
- Reduces cognitive surface area of the prompt — one less knob the AI is tempted to tune.

**Risk if it lowers CR:** minimal — no downstream code uses confidence_score at decision level (confidence_filter_mode: shadow per CLAUDE.md). Shadow loggers will lose a field; the knowledge_base trade index may have to keep a compatibility stub.

**Batch-validation cost:** $0 (canary) to $27 (XAUUSD T7 re-run for safety).

**WF-1 approval path:** CEO approval required. **Optional cleanup.** Defensible hygiene pass.

### D3-5 (EXPLORATORY) — Balance LONG/SHORT example order + add symmetric SHORT mirror

**Specific change:**
- Line 132: "H1 bullish → LONG. H1 bearish → SHORT. Mismatch → FAIL." — **keep LONG first** (pedagogically fine; not the problem).
- Line 150-152: alternate the lead. Current all-LONG-first, proposed:
  - `entry_price`: "ob_high for LONG (top of nearest unmitigated H1 OB) OR ob_low for SHORT (bottom of nearest unmitigated H1 OB)..." — **keep**
  - `stop_loss`: "above nearest significant H1/M15 swing high (SHORT) or below swing low (LONG)..." — **flip**
  - `take_profit_1`: "entry - 1.5 x |stop_loss - entry| (SHORT) or entry + 1.5 x |entry - stop_loss| (LONG)" — **flip**
- Add after line 152: "SHORT example (n ≈ SHORT direction): H1 shows 2 bearish BOS → bias bearish → LONG OB bound (top) used as entry — wait, for SHORT you use ob_low — <fully worked numeric example>."

**Expected impact:** reduces LONG primacy to zero. If the 94.7% LONG skew on flat EURUSD is even partly prompt-driven, this could lift SHORT CAND emission rate. Magnitude unknown; could be 0 or could be 5-20pp.

**Risk if it lowers CR:** minimal — the change is cosmetic symmetry.

**Batch-validation cost:** $30 EURUSD T7 re-run (requires A1 landed, which it is). $50 to also re-run XAUUSD+NAS100.

**WF-1 approval path:** CEO approval. **Exploratory — ship only if D3-1 + D3-2 + D3-3 have landed and we still see SHORT-geometry degeneracy.**

---

## 8. Ranked summary table

| Rank | Proposal | Confidence | Expected R impact | CR risk | Validation cost | Approval path | Blocks / unblocks |
|-----:|----------|-----------|-------------------|---------|-----------------|---------------|--------|
| 1 | D3-1 FX decimal precision | HIGH | Directly unblocks FX live; eliminates 59.7% EURUSD degenerate | None | $30 EURUSD T7 | CEO | Unblocks EURUSD/GBPUSD/USDJPY/GBPJPY live |
| 2 | D3-2 non-zero sl_buffer_applied | HIGH | +13R/quarter NAS100; replaces T2.9 decision | Low-medium | $50 XAUUSD+NAS100 T7 | CEO | Resolves T2.9 & T2.prompt |
| 3 | D3-4 Remove useless fields | HIGH | $0 save; hygiene only | Minimal | $0-27 | CEO | None |
| 4 | D3-3 Sort/count tuning | MEDIUM | Sharpens observation outputs; potential shadow-filter readiness | Minimal | $2 canary | CEO | Improves premium/discount signal quality |
| 5 | D3-5 SHORT-side symmetry | EXPLORATORY | Possible 5-20pp SHORT CAND lift on flat markets | Minimal | $30-50 T7 | CEO | Dependent on D3-1 ship order |

### Combined ship plan (if CEO approves all 5)

**Phase A (blocks FX live):** D3-1 alone. Single commit, batch-validate via $30 EURUSD T7.
**Phase B (edge recovery):** D3-2. Single commit, batch-validate via $50 XAUUSD+NAS100 T7. Confirm direction of cross-instrument impact. This also retires T2.9 / T2.prompt from the unresolved list.
**Phase C (hygiene):** D3-4. Single commit. $0-27 validation.
**Phase D (observation):** D3-3. Single commit. $2 canary.
**Phase E (exploratory):** D3-5 only if Phase B results show SHORT-geometry still weak.

**Total cost envelope if all 5 ship: ~$110-180 API.** Low risk of drifting above the $50/month cap since this is a one-time batch validation stream (the current month is already ~$30-40 into the live trading bill plus session 35's tier A re-score was $0).

---

## 9. Evidence + citations

| Claim | File:line or data artefact |
|-------|----------------------------|
| Prompt user message is 2.9-3.2k chars on 5 instruments | `_theta_scratch/token_counts.json` |
| Sonnet 4.6 context limit 200K tokens | Anthropic docs; `config.ai.primary_model: claude-sonnet-4-6` (CLAUDE.md) |
| Hard slices `[:5]`, `[-5:]`, `[-10:]`, `[:10]` | `src/prompts/primary_analyzer_prompt.py:278, 286, 295, 304, 367, 396, 409` |
| MSO on 2026-04-17T15:15:00Z had 606 sweeps, 174 M15 swings, 87 M15 FVGs, 121 liquidity pools | `knowledge_base/pipeline_state/02_market_state.json` — counted |
| `sl_buffer_applied: 0.0` is written literally in the prompt | `src/prompts/primary_analyzer_prompt.py:155, 236` |
| `sl_buffer_applied == 0.0` rate universal across 1518 records | `research/t3_2_sl_beyond_ob_cross_instrument_audit/sl_buffer_universality.json`, `research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/C_l2_blocked_analysis.md:85, 132` |
| `_PRICE_FMT` is used only in f-strings that render INPUT values | `src/prompts/primary_analyzer_prompt.py:271, 279, 287-289, 296-299, 305, 310, 315, 338, 340, 353-355, 368, 389, 391, 399, 410` — **never in lines 98-245 (instruction body)** |
| EURUSD degenerate output rate (entry=SL/entry=TP/SL=TP) = 59.7% among AI-proposed trades on non-zero | direct re-tally (this session) across `research/t7_live_simulation/EURUSD_t7_simulation.json` records with decision in {CANDIDATE, REJECTED_L2, BLOCKED_LIMIT} and ep!=0: 179/300 |
| XAUUSD degenerate rate = 0% | direct re-tally, same script: 0/764 |
| NAS100 degenerate rate = 0% | direct re-tally across 5 slice files: 0/203 |
| `confidence_score` clusters at 72/75/78/82/85 (5 values) on XAUUSD (n=272) | direct re-tally |
| CANDIDATE direction 36:1 LONG:SHORT on NAS100 | direct re-tally (36 LONG, 1 SHORT), confirms session 34 NAS100 synthesis |
| LONG primacy in all geometry examples | `src/prompts/primary_analyzer_prompt.py:132, 150, 151, 152, 233` |
| Tier A1/A2/A3 landed at `4af838f`, `5bdf6f0` | `git log --oneline` |
| T3.2 verdict: gate fix is NOT a clean global win; prompt fix preferred | `research/t3_2_sl_beyond_ob_cross_instrument_audit/verdict.md:212-288` |
| Session 34 EURUSD FX precision finding (2-dp on 4-dp instrument) | `research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/EURUSD_T3_1_synthesis.md:52-58` |

---

## 10. Methodology + self-critique

### What I actually did

1. Read CLAUDE.md, handoff 35, session 34 synthesis docs (EURUSD + NAS100 + T3.2).
2. Read `src/prompts/primary_analyzer_prompt.py` in full (624 lines) and `src/components/primary_analyzer.py` in full.
3. Wrote `_theta_scratch/render_and_count.py` — no AI calls, no writes to prompts/ or src/; uses production `build_system_prompt`, `build_static_context`, `build_user_message`, `set_price_format` against the live MSO from `knowledge_base/pipeline_state/02_market_state.json`.
4. Rendered 5 instrument configs; saved system + user samples to `_theta_scratch/samples/`.
5. Enumerated MSO key spine (183 paths) via introspection script.
6. Re-tallied T7 sim corpora for: `confidence_score` distribution, CANDIDATE direction, degenerate output rate, `model_used` hallucination tally.
7. Cross-referenced against session 34 T3.2 `sl_buffer_universality.json` (100% rate on 1518 records).

### Self-critique

- **n on bias-scan items is 272-2280, all in-sample.** A statistical claim about "the prompt causes X" would need a counter-prompt A/B test. I offer directional evidence and file:line causality, not proof.
- **The MSO I rendered against is a EURUSD snapshot**, so the XAUUSD and US30 samples look suspicious (all `1.18` prices because I set `.2f` on 1.1xxxx data). This is NOT the production behavior — in production, `set_price_format` is called with the correct per-instrument format (verified `primary_analyzer.py:194`). The sample files are artefacts of using one available MSO against five configs. The char counts are representative of the *prompt structure*, not of realistic per-instrument rendering. This was deliberate: the *structure* is what the audit is about.
- **The T7 sim `raw_response.model_used` fields still show `claude-opus-4-5` on 271/272 XAUUSD slice-2 records.** Per T3.2 verdict and cost math, these are AI hallucinations — actual API calls were bit-exact Sonnet 4.6 pricing. I did not audit the "model_used" hallucination further; Agent β's scope.
- **Token counting used a char-based estimator (3-4 chars/tok)**, not `tiktoken` or `anthropic.Tokenizer` (neither was available in the project's deps — `tiktoken` ImportError, anthropic SDK 0.87.0 does not expose a local tokenizer). The estimator is conservative; the absolute numbers may be ±20%. The conclusion that headroom is 40-60× is robust to that uncertainty.
- **No A/B testing performed.** All D3 proposals are scoped — the CEO decides whether to ship any.

### What I did NOT do (out of scope, for completeness)

- Did not run any Claude API call.
- Did not change any file under `src/`, `prompts/`, `config/`, or `knowledge_base/`.
- Did not attempt to re-train / tune the AI.
- Did not perform Monte-Carlo on any proposal (Agent δ's scope, also handoff Tier C1).
- Did not speak to the CEO; all findings are read-only scope docs.

---

*Agent θ, Phase 1 deep-diagnostic sprint, 2026-04-19. All deliverables are committed or ready-to-commit under `research/b_deep_audit_2026-04-19/phase1/`. No prompts or src/ changes shipped. This doc feeds Tier D3 (D3-1 through D3-5) under handoff 35 §7.*
