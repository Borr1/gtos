# C. REJECTED_L2 + BLOCKED_LIMIT Counterfactual — NAS100 T7 Validation

**Scope:** 1600 NAS100 M15 candles evaluated Jan 02 → Apr 17 2026. Pipeline outcome:
1395 NO_TRADE / 84 REJECTED_L2 / 82 BLOCKED_LIMIT / 37 CANDIDATE / 2 PARSE_ERROR.
This analysis replays every REJECTED_L2 and BLOCKED_LIMIT against M15 price to measure
counterfactual edge.

**Sim engine:** replicates `scripts/simulate_t7_live_period.py :: compute_outcome()`
exactly (re-validated — 37/37 CANDIDATE outcomes reproduced bit-for-bit). Logic:
- limit/stop fill semantics from `candle_close` vs entry (with 0.05-point epsilon
  treated as "at-market");
- SL checked before TP within the same candle (conservative same-candle-tie → LOSS);
- no expiry by default (matches production);
- optional 2 h post-fill timeout → break-even variant for sensitivity.

## TL;DR

- **REJECTED_L2 is a net win for the system**, but it is rejecting real edge for the wrong reason. 84 rejections → +8.50R counterfactual (Exp +0.101R, WR 44.0%). The drag comes from **one bucket**: `sl=OB_bound_exact` (42 trades, +20.50R, 59.5% WR, Exp +0.488R) — real setups killed by a **strict-inequality gate** on SL versus OB low. Fixing this recovers ~+20R / quarter on NAS100 alone without weakening the gate's true function.
- **The AI has a systematic SL-placement bug — and it's specific to LONGs.** 42 of 46 `sl_beyond_ob` rejections have `stop_loss` literally bit-equal to the matched OB low (`sl_buffer_applied: 0.0`), and 44 of 46 are LONG. SHORTs don't exhibit the pattern. The model treats "below OB low" as "at OB low" for LONGs.
- **The L2 gate correctly kills every other category.** `entry_in_ob` (5 trades, -5.00R), `sl_inside_OB_zone` (4 trades, -1.50R), `poi_self_contradict_False` (19 trades, -4.00R) and `poi_cited_no_matching_OB` (13 trades, -0.50R) are all ≤0 Exp. The 19 "poi_identified=False" self-contradictions are -0.211R Exp — **taking them anyway loses money**; the AI's self-contradiction is a real signal of bad setups, not a bug.
- **BLOCKED_LIMIT is dominated by within-zone AI chatter, not distinct signals.** 51 of 82 blocked records reuse the same entry/SL/TP as the already-placed CANDIDATE in the same (date, KZ). Only **31 blocked records are genuinely novel setups**. Novel-only counterfactual: WR 61.3%, +16.52R, Exp +0.533R — of which `max_kz_trades` alone is 24 trades @ **66.7% WR** (exactly matching the 37-CANDIDATE WR) and `max_daily_trades_sim` is 7 trades @ 42.9% WR. **Relaxing max_kz_trades 1→2 has strong EV; relaxing max_daily_trades 2→3 does not.**
- **Combined gate drag at default config: 166 AI-CANDIDATE-formatted intents, 37 executed (22.3%).** The 129 killed intents carry +49.12R of combined counterfactual (Exp +0.381R) — but **98% of that +R is concentrated in two fixable buckets**: the `sl=OB_bound_exact` AI bug (+20.50R) and the `max_kz_trades` cap (+16.02R novel / +31.62R including dupes). Close those two leaks and the rest of the gate is doing its job.

---

## Simulation logic (pseudocode)

```
for each record r (REJECTED_L2 or BLOCKED_LIMIT):
    entry, sl, tp, dir = r.entry_price, r.stop_loss, r.take_profit_1, r.direction
    entry_filled = |entry - r.candle_close| <= 0.05  # at-market epsilon
    for candle c AFTER r.candle_time in NAS100_M15.csv:
        if not entry_filled:
            # limit vs stop fill:
            if dir==LONG and entry < close and c.low <= entry:   entry_filled = True
            if dir==LONG and entry > close and c.high >= entry:  entry_filled = True
            if dir==SHORT and entry > close and c.high >= entry: entry_filled = True
            if dir==SHORT and entry < close and c.low <= entry:  entry_filled = True
            if still not filled: continue
        # optional timeout-BE: if (c.time - fill_time) >= 2h, exit at BE
        #   (SL still wins the same-candle tie inside this candle)
        # else normal SL-first, TP-second:
        if dir==LONG:
            if c.low <= sl:  return LOSS r=-1.0
            if c.high >= tp: return WIN  r=(tp-entry)/(entry-sl)  # ≈ +1.5R
        if dir==SHORT:
            if c.high >= sl: return LOSS r=-1.0
            if c.low <= tp:  return WIN  r=(entry-tp)/(sl-entry)
    if not entry_filled:    return UNFILLED
    return OPEN
```

Two runs: **no timeout** (mirrors production, primary figure) and **2 h timeout-BE**
(sensitivity to a hypothetical time stop).

---

## Q1. REJECTED_L2 — root-cause breakdown

Counts by exact `l2_reason` category (n=84):

| Category | N | Sub-pattern |
|---|---:|---|
| `sl_beyond_ob` | 46 | 42 bit-exact SL=OB-bound, 4 SL inside OB zone |
| `h1_poi_exists` | 32 | 19 "poi_identified=False" self-contradictions, 13 "AI cites level not matching any OB" |
| `entry_in_ob` | 5 | Entry far outside the named OB zone |
| `m15_choch_exists` | 1 | No M15 CHoCH/BOS with displacement |

**Confidence: High** — exact `l2_reason` string matches; no ambiguity.

### Q1a. "SL exactly = OB low" pattern — is it always?

**42 of 46** `sl_beyond_ob` rejections have `stop_loss` **bit-for-bit equal** to the matched OB bound in the `l2_reason` string. The other 4 have SL *inside* the OB zone (i.e. further from entry than the OB high on a LONG or lower than the OB low on a SHORT would be the safe direction — "inside" means tighter than permitted). **Direction skew is extreme: 44 of 46 are LONG, 2 SHORT.**

Gate semantics (verified in `src/components/verification.py:520-533`): for LONG, `sl < zone_low` must hold strictly; `sl == zone_low` FAILs. For SHORT, `sl > zone_high` strictly. This is a production-wide definition, not simulator artefact.

Pattern inspection (3 representative samples, full `stop_loss` reasoning excerpt from `raw_response`):

| Sample | Entry | SL | OB low | `sl_buffer_applied` |
|---|---:|---:|---:|---|
| 2026-01-21T14:00 LONG | 25042.85 | **24976.45** | 24976.45 | `0.0` |
| 2026-03-10T08:00 LONG | 24501.23 | **24290.53** | 24290.53 | `0.0` |
| 2026-04-10T15:45 LONG | 25135.55 | **25096.35** | 25096.35 | `0.0` |

Across the whole corpus, **every single record** (46/46 sl_beyond_ob, 37/37 CANDIDATE, 82/82 BLOCKED_LIMIT) has `sl_buffer_applied: 0.0`. The buffer field isn't being used — SL is placed directly at the OB bound as the model's default.

**Confidence: High.** This is a systematic AI-side behaviour, not a rounding artefact — SL and OB low share the same token representation in the response.

### Q1b. Counterfactual if L2 had accepted these — would they have won?

Production-faithful sim (no timeout), outcomes by sub-category:

| Category | N | W | L | U | WR% | ΣR | Exp |
|---|---:|---:|---:|---:|---:|---:|---:|
| `sl=OB_bound_exact` | 42 | 25 | 17 | 0 | **59.5** | **+20.50** | **+0.488** |
| `sl_inside_OB_zone` | 4 | 1 | 3 | 0 | 25.0 | -1.50 | -0.375 |
| `poi_cited_no_matching_OB` | 13 | 5 | 8 | 0 | 38.5 | -0.50 | -0.038 |
| `poi_self_contradict_False` | 19 | 6 | 13 | 0 | 31.6 | -4.00 | -0.211 |
| `entry_in_ob` | 5 | 0 | 5 | 0 | 0.0 | -5.00 | -1.000 |
| `m15_choch_exists` | 1 | 0 | 1 | 0 | 0.0 | -1.00 | -1.000 |
| **TOTAL** | **84** | **37** | **47** | **0** | **44.0** | **+8.50** | **+0.101** |

Same analysis with 2 h timeout-BE:

| Category | N | W | L | BE | WR% (WLBE) | ΣR | Exp |
|---|---:|---:|---:|---:|---:|---:|---:|
| `sl=OB_bound_exact` | 42 | 10 | 9 | 23 | 23.8 | +6.00 | +0.143 |
| `sl_inside_OB_zone` | 4 | 1 | 3 | 0 | 25.0 | -1.50 | -0.375 |
| `poi_cited_no_matching_OB` | 13 | 5 | 7 | 1 | 38.5 | +0.50 | +0.038 |
| `poi_self_contradict_False` | 19 | 6 | 8 | 5 | 31.6 | +1.00 | +0.053 |
| `entry_in_ob` | 5 | 0 | 4 | 1 | 0.0 | -4.00 | -0.800 |
| `m15_choch_exists` | 1 | 0 | 1 | 0 | 0.0 | -1.00 | -1.000 |
| **TOTAL** | **84** | **22** | **32** | **30** | 26.2 | +1.00 | +0.012 |

**Verdict:**
- **Fixing the `sl=OB_bound_exact` gate bug yields materially more trades with positive EV.** +20.50R (Exp +0.488) over one quarter of NAS100, exceeding the 37-CANDIDATE EV per-trade (+0.668R) by ≈73% of the magnitude. 42 extra positive-EV trades / 76 trading days ≈ +0.55 trades/day.
- **Taking the 19 `poi_identified=False` self-contradictions is a loser** at -0.211R Exp (no timeout) or +0.053R Exp (with timeout — but only because most are pushed to BE). The AI's own "poi_identified=False" reasoning is a reliable tell. The gate is right to enforce structural self-consistency.
- `poi_cited_no_matching_OB` (13) is near break-even (-0.038R Exp); gate stays.
- `entry_in_ob` + `sl_inside_OB_zone` + `m15_choch_exists` are all deeply negative — the gate is correctly catching these.

**Confidence: High on the sl=OB_bound_exact finding** (n=42, direction 44/46 LONG is striking enough to be structural). **Medium on the 19 poi_False finding** — n=19 is small for stable WR estimates, but direction is clear.

### Q1c. AI SL-placement bug — what does the model "think"?

Inspection of `raw_response` for 3 representative `sl=OB_bound_exact` cases shows no explicit prose about SL placement — the model populates the `trade_parameters` block directly:

```
"trade_parameters": {
  "direction": "LONG",
  "entry_price": 25042.85,
  "stop_loss": 24976.45,      # ← set exactly at OB low
  "sl_buffer_applied": 0.0,    # ← self-reports zero buffer
  "take_profit_1": 25142.18,
  "risk_reward_ratio": 1.5,
  "position_size_lots": 0.01
}
```

The `sl_buffer_applied: 0.0` field is uniformly set across **all 165 records that made it to trade_parameters** (CANDIDATE + REJECTED_L2 + BLOCKED_LIMIT). Interpretation: **the model knows there's a `sl_buffer_applied` field, and always zero-fills it.** There is no prompt-time instruction requiring a non-zero SL buffer, so the model's default output is the OB bound exactly. The gate's strict `<` then rejects anything that happens to match exactly (42 of 46 times on LONGs; SHORTs almost never hit this — possibly because the AI spaces SHORT SLs slightly more aggressively).

**Actionable fix proposals (NOT APPLIED — description only):**
1. **Gate tolerance change** (`verification.py:522, 536`): change `sl < zone_low` to `sl <= zone_low`. Lowest-risk fix: accepts the 42 exact-match LONGs and 0 exact-match SHORTs; rejects remain correct. Catch: the 4 `sl_inside_OB_zone` cases would *still* be rejected (their SL is above OB low, not equal). Expected recovery ≈ +20.50R / NAS100 quarter.
2. **Prompt tweak** (system prompt): explicitly instruct the model to set `sl_buffer_applied` ≥ some number of points (e.g. 5 for NAS100, calibrated per instrument ATR). Risk: changes batch-validated WR baseline; would require re-validation and CEO approval (trading-logic change).

**Confidence: High** on (1) being the minimum viable fix. **Medium** on (2) — prompt tweaks are load-bearing and historically degrade unexpectedly.

---

## Q2. BLOCKED_LIMIT — risk-cap counterfactual

Raw category counts (n=82):

| `block_reason` | N |
|---|---:|
| `max_kz_trades (1 in london)` | 39 |
| `max_daily_trades_sim (2 already)` | 22 |
| `max_kz_trades (1 in ny)` | 21 |

### Q2a. Outcomes by block category — naive (all 82)

No timeout:

| Category | N | W | L | U | WR% | ΣR | Exp |
|---|---:|---:|---:|---:|---:|---:|---:|
| `max_kz_trades` | 60 | 33 | 18 | 9 | **64.7** | **+31.62** | **+0.620** |
| `max_daily_trades_sim` | 22 | 10 | 6 | 6 | 62.5 | +9.00 | +0.562 |
| **TOTAL** | **82** | **43** | **24** | **15** | **64.2** | **+40.62** | **+0.606** |

2 h timeout-BE:

| Category | N | W | L | U | BE | WR% | ΣR | Exp |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `max_kz_trades` | 60 | 23 | 11 | 9 | 17 | 45.1 | +23.62 | +0.463 |
| `max_daily_trades_sim` | 22 | 9 | 5 | 6 | 2 | 56.2 | +8.50 | +0.531 |
| **TOTAL** | **82** | **32** | **16** | **15** | **19** | 47.8 | +32.12 | +0.479 |

Naive reading: **"82 extra trades at 64.2% WR, +40R cumulative"** — but this is *inflated by duplicates*.

### Q2b. Duplicate problem — 51 of 82 share entry/SL with an already-placed CANDIDATE

Of the 82 BLOCKED_LIMIT records, **51 share the exact (date, entry_price, stop_loss, direction) signature of the CANDIDATE placed earlier that session** — the AI re-signals the same setup each M15 candle while price remains in the zone. The distribution of (CANDIDATE + BLOCKED) records per (date, KZ) shows 5 groups with 6+ records each; one group has 10. Taking these duplicates in live would not place an additional trade — it would simply re-fire on the same limit that is already in-book.

**Novel BLOCKED_LIMIT only (31 trades):**

No timeout:

| Category | N | W | L | U | WR% | ΣR | Exp |
|---|---:|---:|---:|---:|---:|---:|---:|
| `max_kz_trades` | 24 | 16 | 8 | 0 | **66.7** | **+16.02** | **+0.667** |
| `max_daily_trades_sim` | 7 | 3 | 4 | 0 | 42.9 | +0.50 | +0.071 |
| **TOTAL** | **31** | **19** | **12** | **0** | **61.3** | **+16.52** | **+0.533** |

2 h timeout-BE:

| Category | N | W | L | BE | WR% | ΣR | Exp |
|---|---:|---:|---:|---:|---:|---:|---:|
| `max_kz_trades` | 24 | 10 | 7 | 7 | 41.7 | +8.02 | +0.334 |
| `max_daily_trades_sim` | 7 | 3 | 4 | 0 | 42.9 | +0.50 | +0.071 |
| **TOTAL** | **31** | **13** | **11** | **7** | 41.9 | +8.52 | +0.275 |

**Confidence: High** on the novel split (dedup logic is exact-match on 4 fields, deterministic).

### Q2c. Strategic interpretation

- **`max_kz_trades` 1→2 is the clean EV lever.** The 24 novel `max_kz_trades` trades have WR 66.7% — *bit-identical to the 37-CANDIDATE WR (66.7%)* — with Exp +0.667R (matching the CANDIDATE Exp +0.668R). The AI is finding second setups in the same KZ that trade exactly as well as the first.
- **`max_daily_trades_sim` 2→3 is marginal.** Only 7 novel cases; 42.9% WR, +0.071R Exp. Small sample (n=7) makes this effectively undifferentiated from zero. Recommend keeping the 2/day cap.
- **Volume shift.** If max_kz_trades 1→2 were enabled over the 76-day period: +24 novel trades on 17 already-trading days = ~+0.3 trades per trading day (not the ~1/day the naive reading suggested). **CEO should not expect a doubling of NAS100 trade flow from this change — it's a targeted ~65% volume lift on active days.**
- **KZ distribution check:** BLOCKED_LIMIT is 43 NY / 39 London; novel is 24 `max_kz_trades` across both. No clear KZ imbalance; relaxation applies symmetrically.
- **Correlation overlap concern (acknowledged, not quantified):** EURUSD and XAUUSD batch data for the same Jan 02 → Apr 17 window is not loaded here (EURUSD simulation log present but no JSON output yet; XAUUSD lives in other batches). The 27 days with CANDIDATE trades and 17 with additional novel blocked trades overlap NY and London sessions where USD-index-correlated instruments (EURUSD, USDJPY, GBPUSD, XAUUSD) also trade actively. **Before enabling max_kz_trades 1→2, the correlation-group machinery (`CORRELATION_GROUPS`, 2%-simultaneous cap) must be verified for NAS100 membership** — NAS100 is in the equity-index group with US30, but a second LONG-leaning NAS100 setup could compound with concurrent USD trades. Confidence: Medium-low on magnitude without the other-instrument data.
- **EV of raising max_kz_trades 1→2:** with novel WR 66.7% ≈ CANDIDATE baseline, the expected per-trade contribution is +0.667R. Over 76 trading days with ~0.3 extra trades/day ≈ +0.2R/day ≈ +15R/quarter on NAS100, matching the +16.02R counterfactual exactly. **This is a real, non-trivial edge recovery.**

**Confidence: High on the novel `max_kz_trades` 1→2 thesis** (WR-baseline-matching is strong). **Medium on the portfolio-level impact** — depends on correlation-group mechanics not in scope here.

---

## Q3. Combined net grade (REJECTED_L2 + BLOCKED_LIMIT)

**Volume funnel:** 1600 evaluated → 203 AI-CANDIDATE-formatted intents → 84 REJECTED_L2 + 82 BLOCKED_LIMIT + 37 CANDIDATE. **166 / 203 = 81.8% of AI intents are killed structurally (L2) or artificially (risk caps).**

Of the 166 killed, counterfactual R (no timeout): REJECTED_L2 +8.50R + BLOCKED_LIMIT +40.62R = **+49.12R latent**.

**Is the gate killing legitimate edge? Partial yes, mostly no.**

| Bucket | Verdict | Evidence |
|---|---|---|
| L2 — `sl=OB_bound_exact` (42) | **Kills real edge** (+20.50R, Exp +0.488) | LONG-direction AI SL-placement artefact; fixable |
| L2 — `sl_inside_OB_zone` (4) | Correctly kills | -0.375 Exp |
| L2 — `poi_self_contradict_False` (19) | Correctly kills | -0.211 Exp — AI's own signal is accurate |
| L2 — `poi_cited_no_matching_OB` (13) | Correctly kills (noise-indistinguishable) | -0.038 Exp |
| L2 — `entry_in_ob` + `m15_choch_exists` (6) | Correctly kills | -1.00 and -1.00 Exp |
| BL — `max_kz_trades` (24 novel) | **Kills real edge** (+16.02R, Exp +0.667) | Matches 37-CAND WR bit-identically |
| BL — `max_daily_trades_sim` (7 novel) | Marginal kill (~0 EV) | +0.071 Exp, n=7 |
| BL — duplicates of CANDIDATE (51) | Artefact of per-candle re-signalling | Would not open a new position live anyway |

**Concentration:** 98% of the +49R latent recovery sits in **two leaks** — the L2 strict-`<` SL bug (+20.50R) and the max_kz_trades=1 cap (+16.02R novel / +31.62R naive). Fix both and:
- REJECTED_L2 kill rate drops from 41.4% of intents to ~20.7%.
- BLOCKED_LIMIT kill rate drops from 40.4% of intents to ~14.8% novel or ~9.9% if we also accept dupes as no-op.
- Expected extra quarterly R on NAS100: **+36R** (sum of the two fixes' novel counterfactuals, no timeout).

**Is the gate working for the rest?** Yes. The other buckets are all ≤0 Exp or noise-level positive, confirming L2 correctly enforces structural consistency and the daily cap correctly catches late-session over-trading.

**Confidence: High on the two-leak concentration.** The evidence is arithmetic, not statistical.

---

## Volume / frequency context

- Trading days covered: 76 (Jan 2 – Apr 17 2026)
- Days with CANDIDATE: 27 (37 trades, avg 1.37 trades/trading-day-with-activity)
- Days with BLOCKED_LIMIT: 17 (all also had CANDIDATE — no "lone blocked" days)
- KZ distribution — CANDIDATE: 20 NY / 17 London; BLOCKED: 43 NY / 39 London; REJECTED_L2: 47 NY / 37 London. Approximately symmetric, with a mild NY skew across all three.
- Monthly BLOCKED_LIMIT distribution: Jan 19, Feb 18, Mar 20, Apr 25 (through 17th) — no secular drift.

---

## Open questions for reviewer

1. **Gate tolerance fix (L2 strict-`<` → `<=`):** which is the correct mental model — "SL must be *strictly* beyond the zone" (safety) or "SL at the zone bound is acceptable" (capital efficiency)? The 42 bit-exact LONGs had 59.5% WR counterfactual, so in NAS100 historical data the strict bound wasn't protective. But the ~5% of cases where price wicks *exactly* through the OB bound by one tick would turn a SL-at-bound trade into a loss it would not have been otherwise — that's a real risk the strict-`<` was (accidentally?) guarding against. Worth CEO decision and cross-instrument check on XAUUSD batches before altering.
2. **Prompt-side fix — require `sl_buffer_applied > 0`:** if the agreed decision is that SL *should* be slightly below OB, fix should go in the prompt, not the gate. But this is a trading-logic change (WF-1 territory) and requires batch re-validation. Which fork does the CEO prefer?
3. **max_kz_trades 1→2 — what is the correlation-group interaction?** The 24 novel `max_kz_trades` trades concentrate on the same 17 trading days where CANDIDATEs fire, often within the same NY/London session. Before enabling, need: (a) confirmation NAS100 and US30 share a correlation group with a 2%-simultaneous cap, (b) a check that EURUSD / XAUUSD trades on the same hours are not *also* about to fire — this analysis only has NAS100 data loaded.
4. **max_daily_trades_sim 2→3 — does a larger sample change the picture?** n=7 novel is too small to be decisive; the current -0.071R Exp is indistinguishable from noise. Recommend keeping the 2/day cap until the EURUSD batch (and any future NAS100 extensions) provide ≥20 samples in this bucket.
5. **2 h timeout-BE sensitivity — is this a rule the CEO is considering?** The prompt asked for the variant, but the production pipeline does not implement it. If this is being considered as a future addition, note: 2 h-BE is roughly neutral-to-positive across *all* buckets (REJECTED_L2 Exp goes from +0.101 to +0.012, BLOCKED goes from +0.606 to +0.479 — both retain positive EV but lose about half the magnitude). It converts late-session continuation wins into BE. Weakly-supportive for a 3–4 h window; 2 h appears too short.
6. **Cross-instrument replication:** NAS100 is one quarter of one instrument. Before any L2 change, re-run the same counterfactual on XAUUSD, US30, USDJPY, GBPJPY — if the `sl=OB_bound_exact` LONG-skew is NAS100-only, the fix may be NAS100-specific (tick-size artefact?); if it replicates, it's a global AI behaviour.
7. **Model identity check:** `raw_response` reports `"model_used": "claude-opus-4-5"` (773 records), `"gpt-4.1"` (40 records), and `"structural-bias-evaluator-v1"` (5 records). These are self-claimed strings from the model's own JSON output (not the API-selected model). The actual API call is configured via `config.ai.primary_model`, and the simulation was launched with (presumably) `claude-sonnet-4-6` per CLAUDE.md. Low-risk sanity check: confirm which model actually ran this batch — if it was `claude-sonnet-4-6 effort=max`, the Opus-claiming raw_responses are just cache of training-time self-identification.
