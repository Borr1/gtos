# LANE E — Generator logic review: do these ideas make sense, and does the code build them?

> ## ⛔ ONE HEADLINE AMENDED 2026-08-12 — `LANE_G_RECONCILIATION_V1.md` §2, §2.1, §2.2
>
> **"Every family's target-hit rate is below the driftless null" (§0 item 3, §2's
> `barrier_economics` table) — AMEND. The rates reproduce exactly; the inference does not.**
>
> The below-⅓ rate is a property of the **contract**, not of the entries. Three measurements
> settle it, all on the same population:
>
> * **A direction-flipped control on the identical paths gives 0.2772 against the signal arm's
>   0.2773.** Same instants, same 1R stop, same 2R target, direction flipped — no directional
>   information by construction — and it scores **z = −19.78** against a corrected driftless
>   benchmark, *worse* than the signal arm's −17.49. Geometry-matched (endorsed LONGs against
>   flipped-from-SHORT LONGs, and likewise for SHORTs): **0.2773 vs 0.2772, z = +0.02,
>   p = 0.985.** [`lane_g_receipts/mirror_geometry_matched.json`]
> * **Spearman(corridor width in ATR, target-hit rate) = −0.9636 (p = 0.00003)** across these
>   ten families — the *same* corridor artifact this lane already withdrew its positive
>   time-stop reading for, driving the *same* rank order in the hit rate. On Lane G's
>   measurement the time-stop correlation is **−0.9394 (p = 0.0001)**, stronger than the
>   −0.612 published here. **This lane's own corridor withdrawal was correct and it is not
>   partial: it removes the interpretation of both buckets.**
> * A driftless walk inside an asymmetric corridor `[−1R, +2R]` with a finite horizon has a
>   barrier-conditional target rate below ⅓ **for any signal at all, including none**:
>   conditioning on absorption before the horizon over-weights fast absorptions, which favours
>   the nearer barrier. The exact identity is
>   `p_target = 1/3 − P(ts)·E[cf|ts] / (3·P(bar))`, and it also shows **this lane and Lane C
>   were never in conflict** — a positive time-stop bucket arithmetically *requires* a hit rate
>   below ⅓. The two are one fact seen from two sides.
>
> **The correct replacement statement:** the pool is **directionally uninformative — a fair coin
> charged its own spread**. `E[gross + spread_r] = +0.0078 ± 0.0042 R/fill` on n = 74,249, and
> `E[net] = −E[cost_r] + 0.008 ± 0.004`. The break-even hit rates in §2 remain correct as
> *arithmetic*; what they are compared against does not support "the entries are bad".
>
> **Untouched by this amendment:** everything this lane says about what the code builds versus
> what the ideas describe — the missing *arrive → reverse → enter* confirmation, the
> `structural_distance_extreme` population shape (98.45 % of 13,206 emissions with the trend
> running toward the faded extreme), and the per-family logic reviews. Those are code readings,
> not benchmark readings, and Lane G bears on none of them.
>
> **Scope.** Decisive **for these ten broad-origin candidate families only** — not for the armed
> sleeve estate, AD's exit frontier, or the pooling merges.

**Date** 2026-08-11 · **Lane** E of the owner-commissioned coherence swarm · **Scope** read-only.
No live path, config, or VPS was touched.

**Primary source** `src/components/broader_origin_generators.py` (3,768 lines) as it stands in the
wave-21 worktree, read at `/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809`.
Contrast reading: `src/components/ultimate_book/sleeves/` (the live book) and
`src/components/broad_origin_emission_contract.py`.

**Measured cross-checks** the five-month cached candidate populations
(`/private/tmp/w21-puzzle-cache/rows_{feb,apr,may,jun,jul}.pkl.gz`; durable copy
`/Users/borr/GTOSActive/hermes-evidence-hold-20260727/w21-puzzle-cache-20260812/`) —
**632,934 emissions, 146,745 filled**, Feb/Apr/May/Jun/Jul 2026, all ten production families.
Receipts and the two scripts that produced them are in `lane_e_receipts/` beside this file.

---

## 0. The owner's question, answered first

> *"When the logic of these trades or these candidates — you see the price, we reach a point, and
> then it goes back, and then you go in or something… Do these ideas actually make sense to you as
> an intelligent model?"*

**The ideas are real ideas. Six of the ten are things a competent discretionary trader genuinely
does. But almost none of them is what the code builds.** The gap is always the same shape, and it is
the shape your question already named: *"we reach a point, and then it goes back, and then you go
in."* That sentence has three steps — **arrive, reverse, enter**. The code has one. It enters at the
close of the bar that arrived. There is no "and then it goes back" anywhere in this module. Nine of
the ten families place their order on the same bar that produced the observation, at that bar's
close, with no confirmation of any kind that the market did the thing the idea is about.

Three findings say it more precisely than any prose can:

1. **`structural_distance_extreme` fires SHORT when the close is at the top of its 50-bar range.**
   That is a breakout, traded as a reversal. Measured: **98.45 % of its 13,206 emissions occur with
   the prevailing trend running *toward* the extreme it is fading, and only 1.55 % occur in a flat
   market** — so the range-bound condition its concept requires is not merely unconfirmed, it is
   nearly absent from the population. It cannot be filtered back in; it was never there.
   (`LANE_E_CONFIRMATION_TESTS_V1.json` → `T3_sde_population_shape`.)

2. **On 11.29 % of decision instants the module emits a LONG and a SHORT on the same symbol at the
   same timestamp.** The most common pair is `structural_distance_extreme` + `displacement_continuation`
   (352 instants in February alone): one family reads a large up-bar closing at a 50-bar high as a
   short, the other reads the identical bar as a long. The families are not expressing a view; they
   are ten independent pattern-matchers over one bar with no arbiter.

3. **Every family's target-hit rate is below the driftless null.** On the executed 2R-target / 1R-stop
   contract a coin flip hits target 1/3 of the time. Measured over 108,790 barrier-resolved trades,
   the ten families run **0.102 to 0.313**. Not one reaches the null. And cost pushes the break-even
   hit rate to 0.363–0.494. (`barrier_economics.json`.)

So: the ideas are not stupid. The implementations are not the ideas. And the geometry attached to
them is, in several cases, arithmetically incapable of expressing any idea at all.

---

## 1. Verdict table

| family | 5-mo emissions | **concept** | **implementation** | **geometry** | disposition |
|---|---:|---|---|---|---|
| `current_fvg_fill` | 368,325 | **coherent** (imbalance fill) | **weak proxy** — no reaction required, zone-midpoint limit | **incoherent** — 0.56 ATR corridor, 2 h | REPAIRABLE, high value |
| `current_ob_retest` | 145,721 | **coherent** (institutional retest) | **weak proxy** — no touch/age test recorded or applied | **mismatched** — H1 zone, M15 ATR, 2 h | REPAIRABLE |
| `current_breaker_re_entry` | 36,920 | **coherent** (polarity flip) | **weak proxy**, and **side is inverted** | mismatched | REPAIRABLE — inversion already built |
| `liquidity_sweep_reclaim` | 25,021 | **coherent but crowded** (stop raid) | **broken** — a 0.02-ATR poke counts as a "sweep" | **hostile** — 0.25 ATR beyond the sweep high | REPAIRABLE, direction inverted |
| `structural_distance_extreme` | 13,206 | **incoherent as written** | **inverted** — breakout traded as reversal | **hostile** — 0.35 ATR corridor, 7-min median life | **RETIRE or INVERT** |
| `displacement_continuation` | 22,630 | **coherent** (momentum) | **partial** — no trend agreement, no pullback | plausible, horizon short | REPAIRABLE, low value |
| `cross_asset_lead_lag` | 12,072 | **coherent** (transmission lag) | **partial** — no liquidity-hours gate, no correlation test | plausible | REPAIRABLE, direction inverted |
| `session_open_range_break` | 4,790 | **coherent** (ORB) | **faithful** | **broken** — 4.3 ATR target in 8 bars | RETIRE at this horizon |
| `regime_transition_break` | 1,290 | **coherent** | **partial** — no volatility-expansion test | **broken** — 8.5 ATR target in 8 bars | REPAIRABLE, wrong timeframe |
| `volatility_compression_expansion` | 2,959 | **coherent** (squeeze) | **faithful** | **broken** — 10.3 ATR target in 8 bars | RETIRE at this horizon |

Three further families exist in code and are default-off, so they carry no population:
`range_extreme_reversion`, `microstructure_absorption_reversal`, `microstructure_vdelta_divergence`
(§13).

---

## 2. The four defects that are not any single family's fault

Before the family-by-family reading, four module-level facts. Each one damages every family, and
each is a small code change.

### D1 — One horizon for ten families, and it is 2 hours

Every candidate resolves inside a 2-hour label window (measured: the maximum
`label_span_end − label_span_start` is exactly 2.00 h across all ten families, all five months).
Eight M15 bars. The module's own table says this out loud about one family and it is true of
several: `regime_transition_break`'s provenance note reads *"its birth registry required H1/H4/D1
and it shipped on M15, so its horizon is wrong before its target is"*
(`broader_origin_generators.py:3275-3277`).

Measured median target distance on the **executed** 2R contract, against an 8-bar M15 window:

| family | target, in M15 ATRs | time-stop share of filled | target-hit share |
|---|---:|---:|---:|
| `volatility_compression_expansion` | **10.29** | 87.1 % | 1.3 % |
| `regime_transition_break` | **8.54** | 87.4 % | 1.6 % |
| `session_open_range_break` | **4.34** | 64.5 % | 7.0 % |
| `displacement_continuation` | 3.67 | 47.4 % | 12.4 % |
| `current_ob_retest` | 2.51 | 48.3 % | 11.8 % |
| `structural_distance_extreme` | **0.72** | 1.0 % | 31.0 % |

Read the two ends of that table together. At the top, three families are asked to travel 4–10 ATR in
eight bars; they cannot, so 64–87 % of their trades end at the clock, and the "2R target" printed on
them is decoration. At the bottom, one family's entire trade lives inside 0.72 ATR — its **median
time to resolution is 7 minutes** (p25 3 min, p75 16 min; `resolution_time.json`). A structural
mean-reversion idea that is over in seven minutes is not that idea. It is a spread-crossing lottery
wearing its name.

### D2 — One take-profit for ten families, and nobody chose it

`FAMILY_TARGET_RR` (`:3240-3287`) declares a target for each family. **Every single row is labelled
`UNCHOSEN`** — the module's own honesty label meaning *"nobody ever chose it; it is the risk floor's
value, written down."* The floor is `risk.min_rr`, whose config comment says it is a *sanity floor*.
The module says so itself at `:3224`: *"Every row is UNCHOSEN today. That is the finding, not an
omission."*

That is correct and it is worse than it looks in one specific way: **the cached predecision feature
`target_distance_atr` is computed on a 1.5R basis while the executed contract realises 2.0R gross at
target** (measured: median gross at target = exactly 2.0000 for the three LIMIT families, n=16,136).
Anything reading the feature and the label together is reading two different contracts. I flag it and
leave it to the machinery lane; it does not change any verdict here, only the arithmetic of D1 (I
have used the executed basis throughout).

### D3 — There is no confirmation step anywhere in the module

I checked every trigger. The context variables the module computes — `trend_state_m15`,
`session_at_candidate`, `atr14/atr50` — are attached to **every** candidate as telemetry, and are read
by the trigger of exactly **two** families: `regime_transition_break` (trend transition) and
`session_open_range_break` (session). The other eight fire without consulting regime, session,
volatility state, or the behaviour of the bar after the signal bar — because there is no bar after
the signal bar. Entry is `bar.close` of the trigger bar, on a MARKET order, for all seven
single-symbol families.

Compare the live book. `sleeves/crypto.py` — the armed sleeve — is a Donchian-20 H4 breakout **gated
on `autocorr(60) >= 0.15`**: it asks *"does this market trend right now?"* before taking a trend
trade. `sleeves/structural_retest.py` fixes direction from the HTF regime ("LONG in an up-trend,
SHORT in a down-trend"), restricts itself to a whitelist of verified `(class, session, regime,
vol-state)` cells, and exits on 2R **or 32 bars (8 hours)**. That is what a confirmed setup looks
like in this codebase. The broader-origin families have none of it.

### D4 — Cost is the largest single term in most of these families' losses

Costs, in the trade's own risk unit, median over filled trades with complete cost labels:

| family | median all-in cost (R) | mean net R | mean R before deducted cost | **cost share of the loss** |
|---|---:|---:|---:|---:|
| `structural_distance_extreme` | **0.4804** | −0.5688 | −0.2783 | 51 % |
| `cross_asset_lead_lag` | 0.2810 | −0.3240 | −0.1476 | 54 % |
| `liquidity_sweep_reclaim` | 0.2167 | −0.2916 | −0.1493 | 49 % |
| `current_breaker_re_entry` | 0.2015 | −0.1914 | −0.0523 | **73 %** |
| `current_ob_retest` | 0.1653 | −0.1347 | −0.0368 | **73 %** |
| `current_fvg_fill` | 0.1612 | −0.1976 | −0.0475 | **76 %** |
| `regime_transition_break` | 0.0612 | −0.0640 | −0.0217 | 66 % |

The cost-adjusted break-even target-hit rate follows directly. On a 2R/1R contract a driftless walk
hits target 1/3 of the time; charging cost `c` raises break-even to `(1+c)/3`:

| family | observed hit | driftless null | **break-even after cost** |
|---|---:|---:|---:|
| `structural_distance_extreme` | 0.3128 | 0.3333 | **0.4935** |
| `liquidity_sweep_reclaim` | 0.2742 | 0.3333 | **0.4128** |
| `current_fvg_fill` | 0.2927 | 0.3333 | 0.3913 |
| `current_ob_retest` | 0.2277 | 0.3333 | 0.3911 |

`structural_distance_extreme` needs to be right **49.3 %** of the time to break even, and is right
31.3 %. Sixteen of those nineteen missing points are the cost of a 0.35-ATR corridor. **Six of the
ten families are, before anything else is true about them, too small to pay for themselves.** A trade
whose stop is 0.35 ATR away on M15 is not a trade; it is a bet on the spread.

There is a second, quieter geometry tax. Because the MARKET families enter at the trigger bar's close
and are filled with slippage, their realised payoff ratio is not the nominal 2.0:

| family | gross at target | gross at stop | **effective payoff** |
|---|---:|---:|---:|
| `structural_distance_extreme` | +1.600 | −1.057 | **1.51** (nominal 2.00) |
| `cross_asset_lead_lag` | +1.790 | −1.043 | 1.72 |
| `liquidity_sweep_reclaim` | +1.856 | −1.019 | 1.82 |
| the three LIMIT families | +2.000 | −1.000 | 2.00 |

A tight stop does not just raise cost per R; it converts a nominal 2:1 into a real 1.5:1 before the
idea is even tested. (`effective_payoff.json`.)

---

## 3. `current_fvg_fill` — 58 % of the whole population

**The concept.** A fair-value gap is a three-bar imbalance: price moved so fast that one bar's range
does not overlap the bar two back, leaving a band no trade occurred in. The claim is that price
returns to fill it. **Coherent as a mechanism** — it is a statement about auction incompleteness, and
it is also the single most widely taught ICT pattern on the internet, which is a reason to expect the
naive version to be arbitraged flat rather than negative. It is a *magnet* claim, not a *direction*
claim: it says price will come back to the level, and says nothing about what happens next.

**The implementation** (`:1921-2162`). For every unfilled, un-invalidated M15 FVG within a proximity
tolerance of price, place a **limit order at the zone midpoint**, with the stop at the far edge plus
0.25 ATR, and a 2R target. It denies filled, invalidated, or too-distant gaps and it carries a full
POI lifecycle. That admission machinery is genuinely good work.

**But it converts the magnet claim into a direction claim without argument.** The concept says price
returns to the gap. The code says: *when price returns to the gap, it will then continue in the
gap's original direction.* Nothing in the trigger tests the second half. There is no rejection
candle, no reaction, no lower-timeframe shift — the order simply rests at the midpoint and whatever
arrives, fills. **This is the exact step your question named** ("and then it goes back, and then you
go in"): the code goes in *at* the going-back, not *after* it.

**Measured**: mean −0.1976 R over 60,911 filled trades, negative in all five months. **76 % of that
loss is cost** — the raw path edge is −0.0475 R, i.e. statistically the direction is close to
worthless rather than wrong. Target-hit 29.3 % against a 33.3 % null.

**The concept's own conditioning variable refutes the concept's own premise.** ICT doctrine says a
*fresh* imbalance is the strongest. Measured by age at decision:

| FVG age at decision | n | mean net R |
|---|---:|---:|
| ≤ 1 h | 21,865 | **−0.2375** |
| 1–6 h | 18,188 | −0.2242 |
| 6–24 h | 11,059 | −0.1502 |
| > 24 h | 9,799 | **−0.1128** |

Monotone, and monotone *against* the doctrine: the freshest gaps are the worst by 0.125 R. Freshness
is not an edge here; it is a marker for fast markets that run a 0.56-ATR stop. Every bucket is
negative in all five months, so this is a diagnosis, not a filter that rescues the family.

**Geometry verdict: incoherent.** Median stop 0.56 ATR, median executed target 1.04 ATR, 2-hour
horizon. A gap-fill trade's natural invalidation is *the gap failing to hold* — i.e. price closing
decisively through the far edge — which is a structural event, not a 0.56-ATR excursion. And its
natural objective is the prior swing or the next imbalance, not a fixed 2R. Both ends are wrong for
the idea.

**Verdict: conceptually sound, badly implemented, and the highest-value repair in the estate by
volume.** 368,325 emissions in five months is 58 % of everything this module produces. A repair that
moves this family half a tenth of an R moves more R than every other family combined.

---

## 4. `current_ob_retest`

**The concept.** An order block is the last opposing candle before an impulsive move — the footprint
of institutional accumulation. Price returning to it should find resting orders. **Coherent**, and
again very widely known.

**The implementation** (`:2164-2230`). For every un-mitigated H1 order block within the proximity
tolerance, place a limit at the zone midpoint with a 0.5-ATR buffer stop.

Three faithfulness failures:

1. **The concept's central conditioning variable is read and then discarded.** `:2211` extracts
   `"touch_count": _int_attr(ob, "touch_count", 0)` into the candidate's source fields — and no
   trigger condition ever tests it. The whole idea is that an order block is *depleted* by being
   traded through; a fifth touch is not the same trade as a first touch. The code treats them
   identically. Worse, the field is named `touch_count`, not `poi_touch_count`, so it does not reach
   the feature set either — in the five-month population `poi_touch_count` is **absent (n=0)** for
   this family and for `current_breaker_re_entry`, while `current_fvg_fill` carries it. So the one
   variable that would test the concept is neither used nor recorded.
2. **No reaction requirement.** Same defect as FVG: the limit fills on arrival.
3. **Timeframe mismatch.** The zone is H1; the ATR that sizes the stop, the bar that dates the
   decision, and the 2-hour clock are all M15. An H1 order block's retest is an H1 event given an
   M15 lifetime.

**Measured**: −0.1347 R on 7,603 filled; **73 % of it cost**; raw path edge −0.0368 R. Fill rate is
only **5.2 %** — 145,721 emissions produce 7,603 trades, because a limit at an H1 zone midpoint
rarely gets reached inside two hours. 48.3 % of the ones that do fill end at the clock.

**Verdict: conceptually sound, implementation omits the one test the concept demands.** Repairable,
and the repair is cheap: filter on `touch_count == 0` and carry it as a feature. I could not measure
what that filter is worth because the field is not in the population — **that is itself the finding**.

---

## 5. `current_breaker_re_entry`

**The concept.** A breaker is an order block that failed: price broke through it, so the zone flips
polarity — old support becomes resistance. **Coherent**, and mechanically the most defensible of the
three POI families, because a *failed* level has an identifiable population of trapped participants.

**The implementation** (`:2232-2290`). Un-retested H1 breakers, limit at midpoint, 0.25-ATR buffer,
side from the breaker's declared `direction`.

**The side appears to be inverted, and the estate already knows.** `src/components/current_breaker_re_entry_repair.py`
exists, is committed, and is default-off: it takes a breaker candidate, **inverts the side**, and
re-geometries to target 5D / stop 0.25D. Its docstring records that *"January true-UTC path evidence
selected this exact predeclared cell."* CLAUDE.md prices it at **+11.9 net R/trade on January TRAIN
and HOLDOUT VAL**. My population agrees in sign: the as-shipped family is −0.1914 R over 3,982 filled
trades, negative in all five months, target-hit 26.0 % against a 33.3 % null — a 7.4-point directional
deficit, the second-largest in the estate.

Note what the repair actually says. Inverting the side means the trade is *"price returned to the
failed level and will now break back through it"* — i.e. the breaker is not holding as flipped
resistance; it is being consumed. That is a coherent alternative mechanism, and the estate found it
by measurement rather than by argument. It deserves to be stated as a mechanism, not just as a sign
flip, before it is armed.

**Verdict: conceptually sound; the shipped side is backwards; the fix is already written and
default-off.**

---

## 6. `liquidity_sweep_reclaim` — the family the brief asked about specifically

**The concept.** Price pokes above a visible high where stop orders rest, triggers them, finds no
follow-through, and snaps back inside the range. The trapped breakout buyers become forced sellers.
**Coherent, and one of the few genuinely mechanical stories in retail technical analysis** — it names
a real population of orders. It is also completely mainstream (stop hunt, liquidity grab, Turtle
Soup, spring/upthrust), so the naive version should be crowded.

**Does the code verify a sweep of resting liquidity AND a reclaim back inside? No. It fires on a much
weaker proxy.** The entire trigger is two lines (`:1409-1410`):

```python
swept_high = bar.high > p_high20 and bar.close < p_high20
swept_low  = bar.low  < p_low20  and bar.close > p_low20
```

Against the checklist in the brief:

| the concept requires | the code requires |
|---|---|
| a **sweep of resting liquidity** — a level with orders actually behind it | `bar.high > p_high20`, where `p_high20` is a *rolling* 20-bar max recomputed every bar. No equal-highs cluster, no session/PDH/PDL anchor, no age of the level. |
| **depth** — the raid must go far enough to trip stops | none. Measured: the median penetration is **0.189 ATR; 60.7 % of "sweeps" penetrate by < 0.25 ATR and 29.2 % by < 0.10 ATR.** A 0.02-ATR poke qualifies. |
| **speed** — the raid and rejection happen fast | none. A bar that drifts above and drifts back over 15 minutes is identical to a violent wick. |
| **displacement on the reclaim** — a decisive move back inside | none. The only requirement is `close < p_high20`, satisfied by one tick. No close-location test, no body test, no requirement of a bearish body on a short. |
| **context** — the level must be the extreme of a range, not the middle of a trend | none. |

That last row is the one that produces the volume: because `p_high20` is a rolling maximum, an
uptrending market generates a `swept_high` short **every time a bar pokes to a new high and closes
under the previous 20-bar high** — which is an ordinary pullback bar. Measured: 7,259 of 23,049
filled trades are SHORT in a `strong_up` trend, and that is the second-worst cell (−0.2965 R).

**Measured overall**: −0.2916 R on 23,049 filled, negative in all five months. Target-hit 27.4 % vs
33.3 % null — a real 5.9-point directional deficit on large n. Raw path edge −0.1493 R, so unlike
the POI families this one is not merely paying cost; **it is pointing the wrong way**, which is what
the estate's own inversion receipt reports (`INVERSION_ANSWERS.json`: inverted **+0.0864 R**, positive
in **5 of 5** months, n=23,049).

**I tested the two repairs the concept implies, and one of them failed.** Declared before reading:

- **Depth conditions it, monotonically.** Q1 (≤0.086 ATR) −0.3562 → Q4 (>0.367 ATR) −0.2369, a
  +0.119 R spread. So the concept is right that depth matters — but Q4 is still deeply negative.
- **Reclaim decisiveness does not.** Bucketing on trigger-bar body/range: Q1 −0.3063, Q2 −0.2580,
  Q3 −0.3104, Q4 −0.2919. Non-monotone, no signal.
- **Both together are worse, not better.** Deep sweep *and* decisive reclaim: **−0.3279** on n=662.

**That refutes my own prior.** I expected reclaim quality to be the missing confirmation; it is not.
The honest reading is that the *depth* half of the concept survives and the *reclaim* half does not,
and neither is worth enough to rescue a family that is directionally inverted to begin with.

**Geometry verdict: hostile, and knowingly so.** Stop = `bar.high + 0.25 * ATR` — i.e. **0.25 ATR
beyond the exact price at which the stop-run just occurred**. This is the brief's example and it is
correct: you are placing your stop inside the zone whose defining property is that stops get run
there. Median risk 0.886 ATR, median cost **0.2167 R (21.7 % of the risk unit)**, break-even hit rate
0.4128 against an observed 0.2742.

**One more code fact worth knowing.** The `if / elif` at `:1411` and `:1428` means a bar that sweeps
**both** the prior high and the prior low emits **nothing**. In the concept's own vocabulary a
double-sided raid is the *strongest* signal there is. The implementation discards it.

**Verdict: conceptually sound, badly implemented, directionally inverted as shipped.** Highest
per-trade repair value after the POI families.

---

## 7. `structural_distance_extreme` — the brief's template case, confirmed and worse

**The trigger** (`:1562-1598`):

```python
pos50 = _close_position(series, index, 50)      # (close - min_low_50) / (max_high_50 - min_low_50)
if pos50 >= 0.97:   SHORT, stop = bar.high + 0.25*atr14
elif pos50 <= 0.03: LONG,  stop = bar.low  - 0.25*atr14
```

`_close_position` (`:3406-3413`) **includes the current bar** in the 50-bar window. So `pos50 >= 0.97`
means the bar closed within 3 % of the top of its own 50-bar range — which, with the current bar
included, almost always means *this bar just made the 50-bar high and closed near it*. **That is the
definition of a breakout bar.** The code shorts it.

The brief's characterisation is exactly right and I can now put numbers on it:

- **98.45 %** of the 13,206 emissions occur with the prevailing 20-bar trend running *toward* the
  extreme being faded. **1.55 %** occur in a flat market.
- The flat subset — the only cells where the mean-reversion concept even applies — is **149 filled
  trades over five months**, mean **−0.5158 R**, negative in all five months.
- There is **no reversal confirmation of any kind** in the trigger. Not a lower high, not a bearish
  close, not a failure to make a new high on the next bar, not a break of the prior swing. Nothing.
  The family name says "extreme"; the code says "highest close in fifty bars"; those are opposite
  things in a trending market and the population is 98 % trending.

**Measured**: **−0.5688 R** over 11,118 filled trades — by a wide margin the worst family in the
estate — negative in all five months, stop-hit 68.0 %, target-hit 31.0 %.

**Geometry verdict: hostile beyond repair at this design.** Median total risk **0.353 ATR**, of which
0.25 ATR is the fixed buffer, so the actual structural component (`high − close`) is about 0.10 ATR.
Median all-in cost **0.4804 R = 48 % of the risk unit**. Effective payoff 1.51 against a nominal 2.0.
**Median time to resolution: 7 minutes.** Break-even hit rate 0.4935 against an observed 0.3128.

Be precise about *why* it loses, because the naive reading is wrong. The directional deficit versus
the driftless null is only −2.1 points (0.3128 vs 0.3333) — real (z ≈ −4.7 on n=11,008) but small.
**The dominant term is cost**: 51 % of the loss. So this family is not primarily "a good idea pointed
backwards"; it is **a corridor so tight that crossing the spread twice consumes half the risk unit,
with a mild anti-signal on top**. The estate's inversion receipt agrees in magnitude: inverting it
earns **+0.0927 R** (5 of 5 months, n=11,118) — positive, consistent, and *small*, because the
inverted trade pays the same 0.48 R.

**Verdict: retire by argument, or re-found it as a breakout continuation with adult geometry.** The
name is wrong, the direction is wrong, the population contains none of the condition its concept
requires, and its corridor is a cost lottery. Do not spend another measurement campaign on it. If
anyone wants the inverted version, it is a *new* family — a 50-bar-high momentum entry — and it needs
a stop measured in ATRs, not in ticks.

---

## 8. `displacement_continuation`

**The concept.** A large-range, large-body bar signals a real order-flow imbalance; momentum
persists. **Coherent**, and the closest to an academically supported effect in the set (short-horizon
momentum after high-volume expansion bars).

**The implementation** (`:1446-1465`). `bar_range/ATR >= 1.5 and body/ATR >= 0.75` → enter at the
close, side from the sign of the body, stop 0.25 ATR beyond the bar's extreme.

Two omissions the concept implies:

1. **No trend agreement.** `side = "LONG" if bar.close > bar.open else "SHORT"` reads the trigger bar
   alone. A violent up-bar inside a strong downtrend — a short squeeze, a news spike, a
   stop-cascade reversal — is bought exactly as eagerly as a trend-confirming impulse. Measured:
   with-trend −0.1231 (n=12,501), against-trend −0.1423 (n=4,023), flat −0.1710 (n=4,213). The
   filter separates in the predicted direction but by only 0.019 R and **all three buckets are
   negative in all five months**. Trend agreement is not the missing lever.
2. **No pullback.** Entering at the close of an expansion bar means buying the top of the move. The
   professional version of this trade waits for a shallow retracement and enters on the resumption;
   the code takes the worst available price by construction. This is the "and then it goes back"
   step again, missing.

**Measured**: −0.1366 R on 20,737 filled. Target-hit 23.5 % vs 33.3 % null — a **9.8-point deficit**,
the third-largest. Raw path edge −0.0657 R. 47.4 % end at the clock, because a 3.67-ATR target in
eight bars is a reach even for a family that just proved the market is moving fast.

**Geometry verdict: mismatched.** The stop at 0.25 ATR beyond an expansion bar's extreme is the one
place the geometry is arguably right (the bar's extreme *is* the invalidation). The horizon is the
problem: displacement decays over hours, and the trade is given two.

**Verdict: conceptually sound, weakly implemented, and low-value.** Its deficit is directional, so an
inversion exists (+0.0308 R, 4 of 5 months) but it is small and not stable. Repair only if the
horizon question is being answered for the whole module anyway.

---

## 9. `cross_asset_lead_lag`

**The concept.** A leader instrument moves; a correlated laggard has not yet responded; you take the
laggard. **Coherent, and the only family here whose edge is a genuine microstructure claim rather
than a chart pattern.** It is also the one most obviously competed away at 15-minute resolution — this
is what latency arbitrage exists to eat.

**The implementation** (`:1675-1768`). For a `(leader, lag)` pair, require `|leader move| ≥ 1.0
leader-ATR` on the previous M15 bar and `|lag move| ≤ 0.5 lag-ATR` on the current one; take the lag
in the leader's direction at the close, stop 0.25 lag-ATR beyond the current bar's extreme.

That is a faithful and reasonably careful expression of the idea — impulse threshold,
non-response threshold, correct one-bar lag alignment, source-quality and staleness checks on the
leader. Two things it does not do:

1. **No liquidity-hours gate.** Lead-lag transmission requires both instruments to be actively
   traded. Measured: London+NY sessions −0.2496 (n=3,548) versus all other hours −0.3598 (n=7,371);
   the worst hour bucket is 20:00–21:00 UTC at **−0.9787** (n=123). **Two-thirds of the emissions are
   outside the hours the mechanism needs.**
2. **No live correlation test.** `LEAD_LAG_PAIRS` is a static table. Whether the pair is actually
   co-moving today is never checked, and a lead-lag trade on a decorrelated pair is a coin flip with
   costs.

The volatility state conditions it strongly and monotonically: `atr14/atr50` Q1 −0.4321 → Q4 −0.2052,
a **+0.227 R spread**, the largest conditioning spread I found anywhere. Every bucket still negative.

**Measured**: −0.3240 R on 10,919 filled, negative in all five months. Target-hit 31.1 % vs 33.3 %.
Cost 0.281 R = 54 % of the loss. Effective payoff 1.72. Median life 20 minutes — appropriate for the
idea, which is a point in its favour.

**Verdict: conceptually sound, partially implemented, and the direction is inverted**
(`INVERSION_ANSWERS.json`: **+0.0718 R**, 5 of 5 months, n=10,919). An inverted lead-lag has a real
mechanism behind it — *overreaction and mean-reversion of the laggard* rather than *catch-up* — and
that is a testable, publishable claim rather than a sign flip. It is the most intellectually
interesting result in the set.

---

## 10. `session_open_range_break`

**The concept.** Volatility clusters at the session open; the first N minutes define a range; a break
of that range extends. **Coherent and well-documented** (opening range breakout is one of the oldest
systematic ideas that has actually survived out-of-sample in the literature, on *daily* opens).

**The implementation** (`:1603-1672`). Walks back to the session's first bar, takes the range of the
first **two M15 bars** (`range_close_index = range_start_index + 1`, `range_bars = bars[start:close+1]`),
refuses if any later bar already closed outside it, and fires on the first close beyond. Stop at the
opposite side of the opening range plus 0.10 ATR.

**This is the most faithful implementation in the module.** A 30-minute opening range, one signal per
session, correct first-break-only logic, stop at the structurally correct place. I have no
conceptual complaint about the trigger at all.

**Its problem is entirely geometry.** Because the stop is the *far side of the opening range*, the
risk unit is large — median 2.17 ATR — and the 2R target is therefore **4.34 ATR away, to be reached
within the same 2-hour window**. Measured: **64.5 % end at the clock**, target-hit 7.0 %,
mean −0.0977 R. Nothing conditions it: range width Q1 −0.0701 / Q4 −0.0971 (non-monotone), bars since
open flat, trend flat. The raw path edge is −0.0348 R — essentially zero — and 64 % of the published
loss is cost.

**Verdict: sound concept, faithful code, incoherent horizon.** This family is not evidence against
opening-range breakout. It is evidence that you cannot test opening-range breakout on a two-hour
clock. **Retire it at this horizon; it is the single best candidate for re-running at 8–24 hours**,
where the concept lives.

---

## 11. `regime_transition_break`

**The concept.** Trend regimes change; catching the transition early is worth more than joining a
mature trend. **Coherent**, though "regime" is the vaguest word in the set.

**The implementation** (`:1524-1560`). `trend_state` (20-bar close change / 50-bar ATR) newly reaches
`strong_up` from something that was not `up`/`strong_up`, **and** the close exceeds the prior-20 high
→ LONG, stop at the prior-20 low minus 0.10 ATR.

The trend-transition test plus breakout confirmation is real logic — this is the only family whose
trigger contains two independent conditions. What it omits is the confirmation the concept most
obviously implies: **a regime change is a change in volatility, not only in direction.** The code
never tests whether volatility is expanding.

**I tested that, and it is the only concept-implied filter in the whole study that reaches zero:**

| filter | n | mean net R | months positive |
|---|---:|---:|---:|
| none (as shipped) | 1,222 | −0.0640 | 1 / 5 |
| `atr14/atr50 ≥ 1.2` | 516 | −0.0122 | 3 / 5 |
| `atr14/atr50 ≥ 1.3` | 357 | +0.0012 | 3 / 5 |
| `atr14/atr50 ≥ 1.4` | 242 | **+0.0257** | 3 / 5 |

Be honest about what that is: +0.0257 ± 0.0371 is **0.7 sigma**, on 242 trades, positive in 3 of 5
months. **It is not an edge. It is a family behaving the way its concept predicts**, which is more
than any other family in this module manages, and it is worth saying so.

**Geometry verdict: broken.** Median risk 4.28 ATR (the stop is 20 bars away), median executed target
**8.54 ATR**, horizon 2 hours → **87.4 % end at the clock** and target-hit is 1.6 %. The module's own
provenance note already says the birth registry required H1/H4/D1.

**Verdict: sound concept, partial implementation, wrong timeframe.** With 1,290 emissions in five
months it is too small to matter economically as-is — but it is the one family whose *concept* the
data affirms, and it belongs in any re-run at H1/H4.

---

## 12. `volatility_compression_expansion`

**The concept.** Volatility mean-reverts: compression precedes expansion, and the direction of the
break carries. **Coherent and well-supported** — this is the same idea as the live book's
`vol_compression` sleeve and as every squeeze indicator ever written.

**The implementation** (`:1467-1510`). Prior bar's `ATR14/ATR50 ≤ 0.75` **and** current
`range/ATR14 ≥ 1.25` **and** close beyond the prior-20 high/low. Stop at `min(bar.low, prior_20_low) −
0.20 ATR`. **Faithful** — compression, then expansion, then structural break, in that order. This is
good code.

**And it is arithmetically incapable of working at this horizon.** The stop reaches back to the
20-bar extreme, so median risk is **5.23 ATR**; the 2R target is therefore **10.29 ATR away, inside
eight M15 bars**. Measured: **87.1 % end at the clock**, target-hit **1.3 %** (313 barrier
resolutions out of 2,419 filled trades). The compression ratio does not condition the outcome
(Q1 −0.1411 → Q4 −0.1033, non-monotone) — it cannot, because the outcome is not being determined by
the setup; it is being determined by where price happens to sit at the two-hour mark.

**Measured**: −0.1142 R on 2,419 filled. Only 34 % of that is cost — the lowest cost share in the
set, because the risk unit is large — so this family is the cleanest demonstration that **the losses
here are not a cost story; they are a horizon story.**

**Verdict: sound concept, faithful code, geometry that forecloses the test.** Retire at 2 hours.
Compare against the live `vol_compression` sleeve, which runs the same idea on a horizon that lets it
resolve.

---

## 13. The three default-off families (code read only)

Not present in the five-month population — `enable_mined_families` and `enable_microstructure`
default False — so these are conceptual/code judgements with no measurement behind them.

- **`range_extreme_reversion`** (`:1365-1407`). Close in the outer quartile of the 50-bar range, with
  a thrust cap (`bar_range < 1.5 * ATR`) → fade, stop 1.0 ATR. **This is the honest version of
  `structural_distance_extreme`**: a wider band (25 %, not 3 %), a stop matched to the drift scale
  (1.0 ATR, not 0.35), and a thrust cap that explicitly *excludes* the breakout bars that constitute
  98 % of SDE's population. The docstring cites a real mine (`ULTIMATE_ORIGIN_DISCOVERY_MINE_V2`,
  +0.7…1.35 ATR drift over 4–32 bars). **It is still missing a reversal confirmation and its measured
  drift horizon (4–32 M15 bars) exceeds the 2-hour label window at the top end.** If any
  mean-reversion family is worth re-running, it is this one, not SDE.
- **`microstructure_absorption_reversal` / `microstructure_vdelta_divergence`** (`:1240-1306`). Fade
  the extreme when range-per-volume collapses (absorption), or when a new extreme prints on contrary
  signed volume (divergence). **Conceptually the strongest triggers in the file** — they are the only
  ones that consult volume, and both encode a genuine order-flow claim. Two caveats a trader should
  raise: MT5 `tick_volume` is a tick *count*, not traded size, so "absorption" is being inferred from
  quote activity; and the 2.5-ATR stop is the only sensible stop in the module. Worth measuring.

---

## 14. Adversarial pass on my own strongest finding — and why I am withdrawing it

Mid-analysis I found something that looked like the headline of the report:

> **For 8 of 10 families, the trades that reach the 2-hour clock without touching either barrier are
> profitable — +0.13 to +0.21 R net, positive in 5 of 5 months, on large n** (FVG +0.1879 on 11,129;
> LSR +0.2105 on 4,407; displacement +0.151 on 9,833). The obvious reading: *the direction is fine;
> the stop is killing it.*

**That reading is wrong, and the data refutes it internally.** Conditioning on "never touched either
barrier" is conditioning on survival inside an asymmetric corridor (−1R, +2R). A driftless walk
conditioned to stay inside that corridor has its endpoint distribution pulled toward the corridor
*midpoint*, which is **+0.5R** — so a positive conditional mean is what the null predicts, not what an
edge predicts. The prediction that distinguishes them: the tighter the corridor relative to the
2-hour walk, the stronger the pull.

Measured across the ten families: **Spearman(corridor width, time-stop mean) = −0.612 (p 0.060)** and
**Spearman(time-stop share, time-stop mean) = −0.624 (p 0.054)**. The widest-corridor families —
`regime_transition_break` (8.5 ATR) at +0.024 and `volatility_compression_expansion` (10.3 ATR) at
**−0.021** — sit at zero exactly as the null requires, while the tight-corridor families sit high.
That is the mechanical signature, not a directional one. (`corridor_null.json`.)

**Withdrawn.** I record it because it is the most attractive wrong conclusion available in this data
set, and the next reader will find it too.

---

## 15. Synthesis — the three lists the brief asked for

### 15.1 Conceptually sound but badly implemented (repairable; the estate's unexploited assets)

Ordered by volume × repairability.

| rank | family | what is sound | what is broken | **the specific code change** |
|---|---|---|---|---|
| 1 | `current_fvg_fill` (368k) | imbalance-fill magnet | fills the magnet as if it were a direction; no reaction test; 0.56-ATR corridor on a 2 h clock | require a **reaction bar** before entry: on arrival in the zone, wait for the *next closed M15 bar* to close back out of the zone in the trade's direction, then enter at that close. Implement as a two-state POI (`ARRIVED` → `REACTED`) in `_fvg_poi_state`, and gate emission at `:2007` on `poi_state["reacted"] is True`. Separately: stop at the far edge of the *originating impulse*, not zone-edge + 0.25 ATR. |
| 2 | `liquidity_sweep_reclaim` (25k) | stop-raid mechanism; **depth conditions it monotonically** (+0.119 R Q1→Q4) | any 0.02-ATR poke counts; no level quality; rolling-max level makes every uptrend pullback a short; **direction inverted** | at `:1409-1410` add a depth floor — `bar.high - p_high20 >= K * atr14` with `K ≈ 0.30` (the measured Q4 cut is 0.367) — and a level-quality test: `p_high20` must be at least `M` bars old (`argmax` of the window ≤ index − M) so a fresh rolling high does not qualify. Then **re-test the side**: the estate's inversion receipt is +0.0864 R, 5/5 months. Also remove the `elif` at `:1428` so double-sided sweeps emit. |
| 3 | `current_ob_retest` (146k) | institutional-retest mechanism | the concept's central variable is read at `:2211` and never used or recorded | rename to `poi_touch_count` so it reaches `predecision_features`, and gate emission on `touch_count == 0`. **This is a two-line change that makes the family measurable for the first time.** Then the timeframe fix: use an H1 ATR for an H1 zone. |
| 4 | `current_breaker_re_entry` (37k) | polarity flip after failure | side inverted; 26.0 % hit vs 33.3 % null | the inversion is already written and default-off in `current_breaker_re_entry_repair.py`. Before arming it, **state the mechanism** — the flipped trade is "the failed level is being consumed", which is a different claim from "the level flipped" — and re-derive the 5D/0.25D geometry rather than inheriting it. |
| 5 | `cross_asset_lead_lag` (12k) | genuine transmission mechanism; correct lag alignment | no liquidity-hours gate (2/3 of emissions outside London/NY); no live correlation test; **direction inverted** | gate emission on `session in {london, ny}` at `:1729`, and add a rolling correlation precondition on the pair (e.g. 60-bar return correlation ≥ 0.3) before the impulse test. Then re-test the side (+0.0718 R, 5/5 months). |
| 6 | `regime_transition_break` (1.3k) | **the only family whose data behaves as its concept predicts** | no volatility-expansion test; 8.5-ATR target on a 2 h clock | add `atr14/atr50 >= 1.3` to the condition at `:1525`/`:1543` (measured: −0.064 → +0.001; at ≥1.4, +0.026). Then move it to H1/H4, which its own birth registry required and its own provenance note admits. |

### 15.2 Conceptually weak regardless of implementation — retire by argument, not by campaign

| family | the argument |
|---|---|
| **`structural_distance_extreme`** | Its trigger, `close_position_in_lookback_range(50) >= 0.97`, is a **breakout detector**, and no amount of confirmation-adding changes that: 98.45 % of its population is trending toward the extreme and only 1.55 % is flat, so the condition its concept needs **is not in the data it generates**. Its corridor (0.35 ATR, 7-minute median life, 0.48 R cost, effective payoff 1.51) is a cost lottery in either direction. There is nothing here to repair — the name, the direction, the population and the geometry are all wrong simultaneously. If the inverted version is wanted, it is a **new family** (50-bar-high momentum) and must be founded, not patched. |
| **`session_open_range_break`** *(at this horizon)* | The code is faithful; the concept is fine; the 2-hour clock forecloses the test (64.5 % time-stop, 7.0 % target-hit, raw path edge −0.035 R ≈ zero). Retire the M15/2 h instance **by argument** and, if ORB is wanted, re-found it at 8–24 h. Do not run another campaign on the 2-hour version — it cannot produce information. |
| **`volatility_compression_expansion`** *(at this horizon)* | Same argument, sharper: a **10.29-ATR target inside eight M15 bars** is reached 1.3 % of the time. 87.1 % of trades are decided by the clock, so the setup is not being measured at all. Its low cost share (34 %) proves the loss is horizon, not friction. Retire the instance; the live book already runs this concept properly in `vol_compression`. |
| **`displacement_continuation`** *(low priority)* | Not weak, but not worth the queue slot: the concept-implied filter (trend agreement) separates by only 0.019 R with every bucket negative in every month, and its 9.8-point directional deficit makes it an inversion candidate at +0.031 R — small and 4/5 months. Repair it only as a by-product of the module-wide horizon fix. |

### 15.3 The missing confirmation that would plausibly flip a family — named, with the code change

Ranked by my confidence that the change moves the sign, stated honestly:

1. **`current_fvg_fill` — the reaction bar.** *Highest confidence, largest prize.* Today the limit
   rests at the zone midpoint and fills on arrival; the concept's second half ("and then it goes
   back") is never tested. Change: two-state POI, emit only after a closed M15 bar reacts out of the
   zone. Touches `_fvg_poi_state` (`:2609`) and the emission gate (`:2007`). **58 % of all emissions
   run through this path.**
2. **`current_ob_retest` — first touch only.** *Highest confidence per line of code.* Two lines
   (`:2211` rename + a `touch_count == 0` gate). It may not flip the family, but **it is currently
   impossible to know**, because the variable is neither used nor recorded — which is the more
   damning finding.
3. **`liquidity_sweep_reclaim` — the depth floor plus the level-age test.** Depth is measured-monotone
   (+0.119 R). It will not flip the family alone; combined with the inversion the estate already
   measured (+0.0864 R, 5/5) it is the most likely composite flip in the set. Note that I **tested
   the reclaim-decisiveness confirmation and it failed** (−0.328 on the joint cell) — do not add it.
4. **`regime_transition_break` — the volatility-expansion gate.** Measured to move −0.064 → +0.026 at
   `atr14/atr50 ≥ 1.4`. 0.7 sigma, so this is a *directional* claim, not an admission — but it is the
   only concept-implied filter in the study that crosses zero, and it costs one clause.
5. **`cross_asset_lead_lag` — the liquidity-hours gate.** Worth +0.110 R between London/NY and the
   rest, and it removes two-thirds of the emissions on a mechanism argument rather than a fitted
   threshold. Combined with the measured inversion (+0.0718 R, 5/5) this is the most *interesting*
   candidate, because inverted lead-lag is a publishable mechanism (laggard overreaction), not a sign
   flip.

**And the one change that would help every family at once**: give each family its own horizon and its
own target. `FAMILY_TARGET_RR` already exists, is already wired through the single choke point in
`_candidate` (`:2734-2741`), and every row in it says `UNCHOSEN`. The horizon has no equivalent
structure at all. Three families are currently asked to travel 4–10 ATR in eight bars; one is asked to
express structural mean reversion inside seven minutes. **No confirmation step, no filter, and no
inversion can repair a contract that cannot resolve.**

---

## 16. What I would say to a trader in one paragraph

These are ten real setups that a competent discretionary trader would recognise, implemented by
someone who wrote down the *observation* and forgot the *entry*. Every one of them enters at the
close of the bar that produced the signal, with a stop placed a quarter of an ATR beyond the exact
level where the market just proved it likes to hunt, aiming at a fixed multiple nobody chose, inside
a two-hour window nobody matched to the idea. Six of the ten are too small to pay their own spread —
one of them spends 48 % of its risk on cost and is over in seven minutes. Three are asked to travel
four to ten ATRs in eight bars and are therefore not being tested at all. And on one instant in nine,
two of them take opposite sides of the same bar on the same symbol. The ideas are fine. Fix the
entry, fix the stop, fix the clock — in that order — and then find out whether the ideas are any good,
because right now nothing in this population answers that question.

---

## Receipts

All in `lane_e_receipts/` beside this file. Read-only analysis; no source file was modified.

| file | what it holds |
|---|---|
| `lane_e_analysis.py` | pass 1 — per-family census, geometry, cost, resolution mix, concept-implied conditioning |
| `lane_e_pass3.py` | pass 3 — the declared confirmation tests T1–T7 |
| `LANE_E_FAMILY_MEASURES_V1.json` | pass-1 output over 632,934 emissions |
| `LANE_E_CONFIRMATION_TESTS_V1.json` | T1–T7 with per-month means and month-positive counts |
| `barrier_economics.json` | target-hit rate vs driftless null vs cost-adjusted break-even |
| `cost_decomposition.json` | net / before-deducted-cost / cost, and cost share of loss |
| `effective_payoff.json` | realised gross at target and at stop → effective payoff ratio |
| `resolution_time.json` | p25 / median / p75 minutes to resolution, per family |
| `corridor_null.json` | the corridor-width null that withdraws §14 |

Population: `/private/tmp/w21-puzzle-cache/rows_{feb,apr,may,jun,jul}.pkl.gz`; durable copy
`/Users/borr/GTOSActive/hermes-evidence-hold-20260727/w21-puzzle-cache-20260812/`. Estate receipts
cited but not produced here: `DIRECTION_ANSWERS.json` (barrier hit rates, anti-predictive verdicts)
and `INVERSION_ANSWERS.json` (tradeable inversions), both in the same cache directory.

**Line numbers** are as read on 2026-08-11 in
`/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809/src/components/broader_origin_generators.py`,
which carries uncommitted machinery edits and was not modified by this lane.
