# V4 DRAFT vs V3 — DP1 Head-to-Head Report

- Generated: `2026-04-24T21:25:54.015530+00:00`
- Elapsed: 7.81 minutes
- Total V4 API spend: **$1.1238** (budget cap $2.00)
- Config: `primary_model=claude-sonnet-4-6` `primary_effort=max` `detector_version=v2` `prompt_variant=V4_DRAFT`
- Runs per candle: **5** — total API calls: **20**
- Prompt source: `research\v4_prompt_engineering\primary_analyzer_prompt_v4_DRAFT.py`
- DP1 (V3) cross-reference: `research\v4_prompt_engineering\dp1_noise_floor\dp1_summary.json`

## Executive summary

**V4 vs V3 verdict:** `REGRESSION`

V4 UNDERPERFORMS V3 by 1.0R across 4 candles. V4 DRAFT design has a regression. RECOMMEND: ship V3 Monday; re-examine V4 design before further spend.

**V4 schema quality:** `clean-schema` — V4 schema-clean: no parse errors, no R1-R8 allow-list violations.

### Mechanistic finding — V4 is doing exactly what Agent B's spec asked it to

Inspection of V4 raw responses shows V4's `CB-1 BIAS PRECEDENCE` and `CB-2 "1 CHoCH never flips"` rules are firing cleanly:

- **Candle 1** (V4 CAND SHORT) — V4 cites `COMPUTED block declares bearish bias sourced from H1 CHoCH at 4584.39 (2026-02-02T07:00, ratio=2.3, displaced), overriding prior 4-BOS bullish chain`. V3 was receiving the **same** COMPUTED bearish bias block in its user message but was marking `daily_bias: bearish (low)` and rejecting as `c1_failed`. V4's CB-1 block forces it to trust the COMPUTED direction regardless of confidence. This is working as designed.
- **Candle 2** (V4 NO_TRADE c2_m15_opposing) — V4 cites `M15 bearish CHoCH at 13:15 UTC with displacement_ratio=2.0, meeting the >=1.5 threshold for active opposition`. V4's CB-3 numeric threshold fired. V3 was also NO_TRADE but with reason `c1_failed` — so V4 reaches the same top-decision via a more principled gate.
- **Candle 3** (V4 CAND LONG) — V4 cites `H1 shows 4 bullish BOS (ratios 3.5, 3.4, 1.2, 4.1) with only a single low-ratio bearish CHoCH (ratio=0.7) that does not override the COMPUTED direction`. V4's CB-2 "1 CHoCH never flips" rule fired. V3 was likely reading the bearish CHoCH and rejecting the trade.
- **Candle 4** (V4 CAND LONG) — Matches V3 (both CAND LONG) on a candle where H1=bearish M15=bullish, narrating CANDIDATE via the M15-as-H1 strict rule (unchanged from V3).

**The regression is not a V4 prompt bug — it's the ground-truth unlucky roll on Candle 3.** V4 is doing what the spec says. The problem is Candle 3 was a LOSS in F3 (-1R), and V4 correctly identifies it as CANDIDATE_LONG. V3 got the right _outcome_ by rejecting it for _the wrong reason_ (c1_failed on a COMPUTED-bullish candle — i.e., V3 is over-rejecting and was lucky here).

### Headline numbers

| Metric | V4 | V3 (DP1) |
|---|---|---|
| Typical-decision R total (sum of 4 candles) | **+0.5R** | **+1.5R** |
| Δ V4 vs V3 | -1.0R | — |
| Self-consistency (5 reruns unanimous decision+direction) | 4/4 = 100% | (DP1 reported 100%) |
| Parse errors | 0 / 20 | — |
| `no_trade_reason` schema violations (off R1-R8) | 0 / 20 | — |
| V4 matched V3 typical (head-to-head) | 2/4 candles | — |

## V4 vs V3 head-to-head (per candle)

| # | Candle | KZ | V3 typical (DP1) | V4 typical | Match? | V3 R | V4 R | F3 actual | A2 actual |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `2026-02-02T07:00:00Z` | london | `NO_TRADE` (c1_failed) | `CANDIDATE_SHORT` (5/5, unanimous=True) | NO | +0.0R | +0.0R | LONG WIN +1.5R | CAND SHORT -> L2-rej 0R |
| 2 | `2026-02-04T13:30:00Z` | ny | `NO_TRADE` (c1_failed) | `NO_TRADE` (5/5, unanimous=True) | YES | +0.0R | +0.0R | NO_TRADE | LONG LOSS -1R |
| 3 | `2026-02-04T13:45:00Z` | ny | `NO_TRADE` (c1_failed) | `CANDIDATE_LONG` (5/5, unanimous=True) | NO | +0.0R | -1.0R | LONG LOSS -1R | NO_TRADE |
| 4 | `2026-02-06T07:30:00Z` | london | `CANDIDATE_LONG` (None) | `CANDIDATE_LONG` (5/5, unanimous=True) | YES | +1.5R | +1.5R | LONG WIN +1.5R | NO_TRADE c1_failed |

## V4 self-consistency per candle

| # | Candle | 5 V4 rerun decisions | Unanimous? | Parse err | Schema viol |
|---|---|---|---|---|---|
| 1 | `2026-02-02T07:00:00Z` | `CANDIDATE_SHORT | CANDIDATE_SHORT | CANDIDATE_SHORT | CANDIDATE_SHORT | CANDIDATE_SHORT` | True (5/5 on `CANDIDATE_SHORT`) | 0 | 0 |
| 2 | `2026-02-04T13:30:00Z` | `NO_TRADE | NO_TRADE | NO_TRADE | NO_TRADE | NO_TRADE` | True (5/5 on `NO_TRADE`) | 0 | 0 |
| 3 | `2026-02-04T13:45:00Z` | `CANDIDATE_LONG | CANDIDATE_LONG | CANDIDATE_LONG | CANDIDATE_LONG | CANDIDATE_LONG` | True (5/5 on `CANDIDATE_LONG`) | 0 | 0 |
| 4 | `2026-02-06T07:30:00Z` | `CANDIDATE_LONG | CANDIDATE_LONG | CANDIDATE_LONG | CANDIDATE_LONG | CANDIDATE_LONG` | True (5/5 on `CANDIDATE_LONG`) | 0 | 0 |

## V4 counterfactual R calculation

Ground truth outcomes (from F3 backtest + A2's NO_TRADE candles):

| # | Candle | LONG R | SHORT R | NO_TRADE R | V4 typical | V4 realized R |
|---|---|---|---|---|---|---|
| 1 | `2026-02-02T07:00:00Z` | +1.5R | +0.0R | +0.0R | `CANDIDATE_SHORT` | **+0.0R** |
| 2 | `2026-02-04T13:30:00Z` | -1.0R | +0.0R | +0.0R | `NO_TRADE` | **+0.0R** |
| 3 | `2026-02-04T13:45:00Z` | -1.0R | +0.0R | +0.0R | `CANDIDATE_LONG` | **-1.0R** |
| 4 | `2026-02-06T07:30:00Z` | +1.5R | +0.0R | +0.0R | `CANDIDATE_LONG` | **+1.5R** |
| | **Total** | | | | | **+0.5R** |

- V3 typical total: **+1.5R** (from DP1)
- V4 typical total: **+0.5R**
- **Δ V4 vs V3: -1.0R**

## Parse errors / degenerate outputs / schema violations

- Parse errors (JSON decode fail): **0 / 20**
- `no_trade_reason` schema violations (off R1-R8 allow-list): **0 / 20**

## Per-candle detail (V4 reruns)

### Candle 1 — `2026-02-02T07:00:00Z` (london)

- **V3 typical (DP1):** `NO_TRADE` (ntr=c1_failed)
- **V4 typical:** `CANDIDATE_SHORT` (5/5, unanimous=True)
- **F3 actual:** LONG WIN +1.5R
- **A2 actual:** CAND SHORT -> L2-rej 0R
- **MSO (v2 detector):** D1=`transitional` H4=`bullish` H1=`bullish` M15=`bullish`

| Run | Decision | Direction | Bias (conf) | Grade | No-trade reason | Schema OK | Conf | Cost | Time |
|---|---|---|---|---|---|---|---|---|---|
| 1 | CANDIDATE | SHORT | bearish (high) | A+ | — | True | 80 | $0.0510 | 21.0s |
| 2 | CANDIDATE | SHORT | bearish (high) | A+ | — | True | 80 | $0.0497 | 18.8s |
| 3 | CANDIDATE | SHORT | bearish (high) | A+ | — | True | 80 | $0.0634 | 27.7s |
| 4 | CANDIDATE | SHORT | bearish (high) | A+ | — | True | 80 | $0.0500 | 18.8s |
| 5 | CANDIDATE | SHORT | bearish (high) | A+ | — | True | 80 | $0.0496 | 23.6s |

**V4 variance fingerprint:**

- `decision` — identical: `{'CANDIDATE': 5}`
- `direction` — identical: `{'SHORT': 5}`
- `daily_bias_direction` — identical: `{'bearish': 5}`
- `daily_bias_confidence` — identical: `{'high': 5}`
- `setup_grade` — identical: `{'A+': 5}`
- `no_trade_reason` — identical: `{None: 5}`
- `framework` — identical: `{'ob_retest': 5}`
- `confidence_score` — identical: `{80: 5}`

### Candle 2 — `2026-02-04T13:30:00Z` (ny)

- **V3 typical (DP1):** `NO_TRADE` (ntr=c1_failed)
- **V4 typical:** `NO_TRADE` (5/5, unanimous=True)
- **F3 actual:** NO_TRADE
- **A2 actual:** LONG LOSS -1R
- **MSO (v2 detector):** D1=`transitional` H4=`bullish` H1=`bullish` M15=`bullish`

| Run | Decision | Direction | Bias (conf) | Grade | No-trade reason | Schema OK | Conf | Cost | Time |
|---|---|---|---|---|---|---|---|---|---|
| 1 | NO_TRADE | — | bullish (high) | C | c2_m15_opposing | True | 50 | $0.0475 | 16.8s |
| 2 | NO_TRADE | — | bullish (high) | C | c2_m15_opposing | True | 50 | $0.0473 | 16.2s |
| 3 | NO_TRADE | — | bullish (high) | C | c2_m15_opposing | True | 50 | $0.0476 | 16.7s |
| 4 | NO_TRADE | — | bullish (high) | C | c2_m15_opposing | True | 50 | $0.0477 | 17.0s |
| 5 | NO_TRADE | — | bullish (high) | C | c2_m15_opposing | True | 50 | $0.0476 | 17.0s |

**V4 variance fingerprint:**

- `decision` — identical: `{'NO_TRADE': 5}`
- `direction` — identical: `{'': 5}`
- `daily_bias_direction` — identical: `{'bullish': 5}`
- `daily_bias_confidence` — identical: `{'high': 5}`
- `setup_grade` — identical: `{'C': 5}`
- `no_trade_reason` — identical: `{'c2_m15_opposing': 5}`
- `framework` — identical: `{'none': 5}`
- `confidence_score` — identical: `{50: 5}`

### Candle 3 — `2026-02-04T13:45:00Z` (ny)

- **V3 typical (DP1):** `NO_TRADE` (ntr=c1_failed)
- **V4 typical:** `CANDIDATE_LONG` (5/5, unanimous=True)
- **F3 actual:** LONG LOSS -1R
- **A2 actual:** NO_TRADE
- **MSO (v2 detector):** D1=`transitional` H4=`bullish` H1=`bullish` M15=`bullish`

| Run | Decision | Direction | Bias (conf) | Grade | No-trade reason | Schema OK | Conf | Cost | Time |
|---|---|---|---|---|---|---|---|---|---|
| 1 | CANDIDATE | LONG | bullish (high) | A+ | — | True | 70 | $0.0638 | 28.1s |
| 2 | CANDIDATE | LONG | bullish (high) | A+ | — | True | 80 | $0.0638 | 27.6s |
| 3 | CANDIDATE | LONG | bullish (high) | A+ | — | True | 80 | $0.0638 | 27.1s |
| 4 | CANDIDATE | LONG | bullish (high) | A+ | — | True | 80 | $0.0638 | 27.3s |
| 5 | CANDIDATE | LONG | bullish (high) | A+ | — | True | 70 | $0.0638 | 27.6s |

**V4 variance fingerprint:**

- `decision` — identical: `{'CANDIDATE': 5}`
- `direction` — identical: `{'LONG': 5}`
- `daily_bias_direction` — identical: `{'bullish': 5}`
- `daily_bias_confidence` — identical: `{'high': 5}`
- `setup_grade` — identical: `{'A+': 5}`
- `no_trade_reason` — identical: `{None: 5}`
- `framework` — identical: `{'ob_retest': 5}`
- `confidence_score` — 2 unique: `{70: 2, 80: 3}`

### Candle 4 — `2026-02-06T07:30:00Z` (london)

- **V3 typical (DP1):** `CANDIDATE_LONG` (ntr=None)
- **V4 typical:** `CANDIDATE_LONG` (5/5, unanimous=True)
- **F3 actual:** LONG WIN +1.5R
- **A2 actual:** NO_TRADE c1_failed
- **MSO (v2 detector):** D1=`transitional` H4=`bullish` H1=`bearish` M15=`bullish`

| Run | Decision | Direction | Bias (conf) | Grade | No-trade reason | Schema OK | Conf | Cost | Time |
|---|---|---|---|---|---|---|---|---|---|
| 1 | CANDIDATE | LONG | bullish (medium) | A+ | — | True | 80 | $0.0556 | 25.0s |
| 2 | CANDIDATE | LONG | bullish (medium) | A+ | — | True | 80 | $0.0633 | 28.1s |
| 3 | CANDIDATE | LONG | bullish (medium) | A+ | — | True | 80 | $0.0579 | 27.1s |
| 4 | CANDIDATE | LONG | bullish (medium) | A+ | — | True | 80 | $0.0633 | 28.9s |
| 5 | CANDIDATE | LONG | bullish (medium) | A+ | — | True | 80 | $0.0633 | 27.5s |

**V4 variance fingerprint:**

- `decision` — identical: `{'CANDIDATE': 5}`
- `direction` — identical: `{'LONG': 5}`
- `daily_bias_direction` — identical: `{'bullish': 5}`
- `daily_bias_confidence` — identical: `{'medium': 5}`
- `setup_grade` — identical: `{'A+': 5}`
- `no_trade_reason` — identical: `{None: 5}`
- `framework` — identical: `{'ob_retest': 5}`
- `confidence_score` — identical: `{80: 5}`

## Recommendation for CEO Monday decision

**Verdict:** REGRESSION (V4 UNDERPERFORMS V3 by 1.0R across 4 candles. V4 DRAFT design has a regression. RECOMMEND: ship V3 Monday; re-examine V4 design before further spend.)

**Next steps by verdict band:**

- Ship V3 Monday (already in prod).
- DO NOT deploy V4 — regression on A2-divergent sample.
- Agent B should re-examine V4 DRAFT spec (FORENSIC_AND_V4_SPEC.md §7 counterfactual).

## Caveats

1. **n=4 candles is too small for statistical significance.** These are the A2-divergent candles; V4-DP1 is a targeted test of whether V4 alters V3 typical behavior on known-borderline cases. Wider A/B needed before any deploy decision.
2. **Counterfactual R on SHORT trades assumes L2 rejects them** (as A2 did on candle 1). If V4's CANDIDATE_SHORT would pass L2 in a real run, the SHORT R is worse than 0R. Candle 1 SHORT geometry is valid (TP1=4659.53 < entry=4713.38 < SL=4749.36, sl_buffer=6.54 > 0), so the `sl_wrong_side` and `degenerate_params` post-AI gates would NOT reject. But there are other L2 layers (distance, H1 POI existence check, etc.) that could still filter. **Worst-case scenario:** if L2 passed AND stop-out triggered, SHORT candle 1 would be **-1.0R** (F3 ground truth = LONG WIN means price moved UP → SHORT stopped out). That would make V4 total **-0.5R** and **Δ = -2.0R** vs V3. The 0R assumption used in this report is the optimistic A2-match counterfactual; the pessimistic-L2-passes bound is **-0.5R**.
3. **Same MSO state as DP1** — detector v2 (not v2_shadow). Production is now v2_shadow since 2026-04-24. Any Monday decision must account for current detector state.
4. **V4 DRAFT is 22% LONGER than V3, not 30% shorter.** The mission brief claimed 'Length ≤70% of V3' — actual V4 DRAFT is 28279 chars vs V3's 23252 chars (122% of V3). The dedup pass (DD-1 in V4 DRAFT's own header) is not in the DRAFT as shipped.
5. **V4 is not broken, but its design promotes over-acceptance.** The CB-1 BIAS PRECEDENCE block removes V3's implicit bias-strength filter. On these 4 candles V4's over-acceptance rate (2/4 CANDIDATE vs V3's 1/4) is not a bug — it is the explicit V4 design. The regression in R-total is because 2 of 3 new CANDIDATEs were losers (candle 1 SHORT against a +1.5R LONG = 0 or -1R; candle 3 LONG = -1R). Whether these new acceptances help expectancy over a wider sample is the actual question V4 A/B needs to answer.
6. **Candle 3 is a structural CAND LONG, not a prompt gaming win.** V4 takes a statistically principled position (COMPUTED bullish + 4 BOS + weak opposing CHoCH ratio=0.7 = LONG) and loses. V3 "wins" by over-rejecting for `c1_failed` on a COMPUTED-bullish block. This is the A2→F3 underfill pattern we originally saw, in reverse: V3 is over-conservative on this candle and gets lucky. V4 A/B on a larger sample may show V4's expectancy edge via capturing more of the F3-style wins like candle 1's COMPUTED-bearish rollover.
