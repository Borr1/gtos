# IS IT THE SLEEVES OR THE WAY WE USE THEM — THE VERDICT

**Lane a1, wave 19, phase 19. 2026-08-06.**

Borhen asked one question and ruled out one answer:

> *"im still not really clear if it's the sleeves or the way we're using the sleeves ... there is no
> other option than to figure this out"* — and — *"there wont be the option of the broad family is
> finished, if it's finished there must be a reason it's finished and there must be a way to know
> that."*

This document answers the question, gives the mechanism, and specifies the test that would reopen it.

Machine-readable companion: `SLEEVES_OR_USAGE_VERDICT.json`.
Every number below is traced to a committed receipt under
`phase19/receipts/discovery/`. Nothing here is new measurement; it is adjudication of thirteen
lanes, three of which were built to attack the other ten.

---

## 0. THE ANSWER

**It is the SIGNAL.** Not the usage. The setups themselves carry a directional content that is real,
reproducible, out-of-sample positive in R — and roughly two hundred and fifty times too small to
transact. The machinery around them is close to its own ceiling and, handed a signal, prints money.

The oracle ladder settles it in two numbers, on 141,230 rows over 172 trading days and eight windows
(`f2/F2_POOLED_V1.json → LADDER_TABLE_TRACK_B`):

**(1) Hand the SHIPPED machinery a correct direction call — same gate, same M15-close instant, same
2R/−1R exit, nothing else changed — and the book goes from −0.29226 to +0.59673 R/trade.**
A correct direction call is worth **+0.88898 R/trade** to the stack exactly as it is built today.
This family's direction call delivers **+0.00221** of it.

> ### **0.249 %.**
> *The broad V4 family's setups deliver one quarter of one percent of what a correct direction call
> is worth to the machinery that already exists.*

**(2) Hand the REAL direction call perfect usage — oracle exit, oracle entry instant, oracle ranker,
unlimited capacity, all at once — and the book books +2.33914 R/trade.** A coin flip on the identical
rows, instants, risk distances and toll books **+2.31133**, i.e. **98.81 %** of it. Perfect usage is
worth +2.63140 R/trade and **99.03 % of that is available to anybody** trading those instruments at
those moments. The signal's own contribution at perfect usage is **+0.02781 R/trade**, which is
**2.24 %** of the +1.24371 that getting direction right is worth at that rung, and **8.7 %** of the
0.32954 R/trade broker toll on the same rows.

| rung | what is granted | net R/trade | coin-flip on same rows | signal's own share |
|---|---|---:|---:|---:|
| R1 | shipped everything, no gate | **−0.29226** | −0.29447 | +0.00221 |
| R0 | + shipped cost gate | −0.06625 | −0.05649 | −0.00976 |
| R3b | + oracle exit (path) | +1.71862 | +1.69333 | +0.02529 |
| R4b | + oracle entry instant | **+2.33914** | +2.31133 | +0.02781 |
| R5 | + oracle **direction** | +3.58285 | +3.58381 | −0.00096 |
| R5b | oracle direction, **shipped** exit + instant | **+0.59673** | +0.59767 | −0.00094 |

R5 and R5b are the machinery's zero-check: the direction oracle is side-agnostic by construction, so
real and placebo *must* agree, and they do to four decimals. The ladder is instrumented correctly.

**Not one rung's paired signal CI excludes zero.** Pooled over eight months as independent blocks,
R1 is +0.00315 ± 0.01026 (5/8 months positive) and R4b is +0.02877 ± 0.02816 (6/8).

### The verdict in one paragraph

The broad V4 family is finished as a source of tradeable edge, and it is finished for a reason that
is a property of the setups and not of anything downstream: **they capture 0.0119 basis points of
price per trade against a 3.0159 bp round-trip toll — a factor of 253 — and that capture does not
grow with holding time.** A working sleeve's does, by 37.6× over the same horizon ladder. There is
no filter, exit contract, entry instant, ranker, sizing rule, broker or order type that recovers a
253× price-unit deficit, and this wave has now measured 282 contract shapes, 324 out-of-sample
selection arms, 1,414 rule cells, 66 ex-ante rule cells, 56 exit-surface cells, a 42× cost-cap sweep
and a five-rung oracle ladder, all of them saying so, on a held-out test the family failed.

---

## 1. THE MECHANISM — three limbs, each measured

The owner ruled out a bare negative. Here is why it is finished, in three measurements that each
stand alone.

### Limb 1 — SCALE. The setups are smaller than the cost of transacting them.

The generator emits stops of **8.09 bps** at the median against a broker spread of **0.716 bps**
(`p3_RESULT.json → PASS2.SPREAD_OVER_RISK`, 1,129,016 emissions). Spread-over-risk is **0.0926** at
the median, above 0.10 on **46.6 %** of rows, above 0.25 on 13.1 %, above 1.0 on 1.8 %.

Measured on three never-read months — the sealed test, 470,472 emissions, 97,802 clean fills
(`p2_RESULT.json → headline`):

| quantity | value |
|---|---:|
| price captured per trade | **+0.0119 bps** |
| broker toll per trade | **3.0159 bps** |
| net | **−3.0040 bps** |
| shortfall factor | **253.4×** |

Read in R the same rows say 12.6×, and R flatters the family, because R divides the price move by
the generator's own stop and the family's stops are tiny. **The price unit cannot be gamed and it is
the unit the verdict rests on.**

For calibration: the family's entire per-trade price capture is **1.66 % of one median spread** and
**3.3 % of one half-spread**. It is not competing with the broker; it is two orders of magnitude
below the broker's own bid-ask.

### Limb 2 — NO ACCUMULATION. Holding longer does not help, and widening the stop makes it worse.

This is the limb that distinguishes "these setups are small" from "these setups are finished", and
it is the wave's most important structural finding (`d3/D3_CURVE.json`, paired side-mirror, same
walker, same control, both populations, in bps of price):

| horizon | broad V4 family | live W7 sleeve book |
|---:|---:|---:|
| 2 h | 0.2008 bps | 3.4067 bps |
| 8 h | 0.2051 | 32.9574 |
| 24 h | 0.2077 | 38.4087 |
| 72 h | 0.1943 | 100.0112 |
| 160 h | 0.1904 | 103.9773 |
| 320 h | 0.1938 | 128.0388 |
| **growth 2 h → 320 h** | **0.965×** | **37.58×** |

**The broker toll is paid once per trade. A signal that does not grow with holding time can never
outrun it by holding longer.** The live sleeves clear their own toll by 2.36× to 11.46×; the broad
family reaches **0.025** at the shipped cell and **0.076** at its own best horizon (8 h). Split 159
cohorts × 6 horizons = 954 looks, each priced against *its own* measured toll: 26 cohorts beat their
toll at their best horizon, 5 hold the sign in ≥ 75 % of windows, and **zero** hold it in all eight.

The obvious escape — widen the stop so the fixed toll is a smaller fraction of R — was priced
exhaustively and it fails in the *direction* nobody expected. **0 of 282 live-sleeve-shaped
contracts is net-positive** (six stop widths × six horizons × five targets, plus 90 ATR-matched
cells sized by the sleeves' own rule). And the closer the contract gets to a live sleeve's, the
*worse* the direction call becomes: at the crypto-shaped cell (400 bps stop, 4R target, 320 h) the
family is **significantly worse than a coin flip**, −0.01504 R/trade, CI95 [−0.02645, −0.00366],
p(≤0) 0.9948. The reverse transplant is symmetric: put a working sleeve on the broad family's
contract and it goes from +0.6970 to **−0.9585** R/trade, with 68.7 % of its trades stopped inside
two hours by a 9.28 bp stop.

**So the family's information is a short-horizon, sub-spread flicker.** It is not a small version of
a sleeve's edge; it is a different kind of object, and there is no contract that converts one into
the other.

### Limb 3 — THE INSTRUMENT WAS FLATTERING IT, by more than the quantity being argued about.

The M15 and M1 bar archives every wave-19 lane walks are **BID** on open/high/low/close. Settled
twice, independently, exactly:

- 76,734 M15 bars × 29 symbols against the broker's own ticks: median (close − last tick bid)/spread
  = **0.000000** across all 29 symbols; median (close − mid)/spread = **−0.500000** across all 29;
  bar close exactly equal to the last tick bid on **100.00 %** of bars (`d8x_RESULT.md` §2).
- 223,239 M1 bars × 4 symbols × 2 windows, inside the analysis windows, on the packs the lanes
  actually load: close == last tick bid on 99.993–100.000 %; (close − mid)/spread median −0.500 in
  8 of 8 (`p3_RESULT.md` §4.1).

A long buys the ask and sells the bid; a short sells the bid and buys the ask. Against a bid series
the true triggers are stop at (d − s) and target at (T·d + s). **Every walker in this estate applies
neither shift.** The resulting optimism has a **constant sign** and is worth:

| measurement | R per fill |
|---|---:|
| d8x first-order bound at the shipped 240-bar horizon | **−0.0696** |
| p3 tick truth, January 2026, 4 symbols, 14,186 rows | **−0.0715** |
| p3 tick truth, April 2026, 4 symbols, 15,919 rows | **−0.1160** |
| p3 modelled MT5-side shift, 8 windows, 313,960 fills | **−0.0986** |

Decomposed against the "that is just your tie-break rule" objection: **89.2 % and 88.6 % of the
bar-vs-tick gap is the quote side**, 10.8 % and 11.4 % is intrabar ordering (`p3/P3_DECOMP.json`).
The M1 OHLC is an exact aggregate of the bid ticks, so this is not a resolution artifact.

**Now put that next to every positive gross this wave produced:**

| claim | R/fill | smallest measured bias ÷ claim |
|---|---:|---:|
| f2 signal at perfect usage | +0.02877 | **2.42×** |
| d1b at-market gross, fill convention corrected | +0.02402 | **2.90×** |
| p2 **sealed** clean roster gross | +0.02718 | **2.56×** |
| d5/p3 broker-correct-fill gross | +0.01140 | **6.10×** |

**Every surviving positive number in this wave is between 2.4 and 6.1 times smaller than the
instrument's own measured, constant-sign error.** Corrected on ticks, the gross is negative:
−0.0387 R/fill (January) and −0.1447 R/fill (April) on the four symbols with tick coverage.

One honest qualification, and it matters: **the NET numbers survive.** The estate charges a cash
spread term as a cost, which approximately accounts for the same physical fact the trigger
displacement represents — p3 measured the net error at ±0.02–0.04 R/fill *with no consistent sign*,
against a gross error of −0.07 to −0.12 R/fill *always the same sign*. So: **every published NET
number in this estate stands; every claim about the GROSS being positive does not.** The verdict
rests on net, which is −0.29 to −0.32 everywhere, so the verdict is unaffected — but the "the signal
is exactly zero" framing was itself an artifact, and the true reading is zero-to-negative.

### Why the three limbs are one mechanism

The family emits setups whose risk distance is comparable to the spread (limb 1); its information
does not accumulate, so no horizon or contract makes the risk distance large enough to matter
(limb 2); and the measurement that made the residual look non-negative was itself a half-spread
(limb 3). All three are the same statement seen from three sides: **this generator's setups live
inside the bid-ask.**

---

## 2. WHY IT IS NOT THE USAGE — the case, stated at its strongest

The usage was the hypothesis this wave was built to test, and it was tested harder than the signal.
It is not the problem, and four independent measurements say so.

**(a) The layers are near their own ceilings.** Priced layer by layer against both an oracle and a
feasible out-of-sample alternative on the correct population (`d2_RESULT.json →
LAYER_TABLE_LEAVE_ONE_ORACLE_IN`): the gate captures **83.8 %** of the range between a random gate
and the best feasible gate ((−0.06625 − (−0.27843)) / (−0.02534 − (−0.27843))). The exit layer's
capture is **negative** (−0.44 %) — the shipped `target_2.0R` ranks 10th of 12 runnable contracts and
sits below its own menu mean. The entry-timing layer's capture is **0 %** because no such layer
exists: the system decides at M15 closes and nothing else.

**(b) The remaining headroom is unreachable.** The largest real-vs-oracle gap is RANKING, worth
+2.267 R/trade of range at the system's own 2.948-trades-per-day capacity — and a 38-feature ridge
on every pre-decision observable, leave-one-month-out, captures **12.80 %** of it and books −0.00009.
The reachable share of the gate's oracle gap is **3.88 %**, of the exit's **2.32 %**, of the entry
timing's **2.80 %**.

**(c) Priced jointly, every deployable repair is worth +0.00553 against a +0.29226 gap — a factor of
52.9.** Standalone they sum to +0.12114; on the same rows they deliver +0.00553, a double-count
factor of **21.9×**. This is the estate's standing rule (never sum standalone lever values) applied
at its worst observed overlap.

**(d) The usage ADDS, measured against a matched control.** Selection picks candidates worth
+0.0667 R/trade gross over a geometry-matched roster draw (matched on window, symbol and risk
distance ±25 %; CI95 [−0.0436, +0.1796]), management adds a further +0.023, and the arm's own cost
model charges 0.074 where the plain contract charges 0.281. **Whatever is wrong, the downstream stack
is the reason the number is near zero rather than far below it.**

**And the one large "usage" number is not a selector.** The shipped cost gate is worth +0.22601
R/trade — the largest non-oracle improvement measured anywhere in this wave — and it earns it by
**trading 59 % less**, not by choosing better: its signal contribution is **−0.00976** (negative),
and under an oracle exit it turns actively **harmful**, −0.36933. It is a toll filter. That is why
R0 beats R1 and the ladder is non-monotone at its first rung.

**Verdict on the usage axis:** the usage carries three genuine, fixable defects (§4), worth at
most +0.055 R/trade combined against a 0.28–0.34 toll. None of them changes the sign of anything.
**Usage is not why this is finished.**

---

## 3. WHAT "NO EDGE" MEANS NUMERICALLY, AND WHAT WOULD HAVE TO BE TRUE

"No edge" here does **not** mean "noise". The family's directional lean is real and reproducible:
+0.02718 gross R/fill on three never-read months at p(≤0) = 0.001, positive in 3 of 3
(`p2_RESULT.json`); +0.1490 bps at p 0.0045, 7 of 8 windows (`d3`); +0.02391 against its own exact
mirror on the sealed cohort where no fill selection can exist, 3 of 3 windows (`p2` H6). It is a
detectable object.

**"No edge" means this:**

| quantity | measured | needed | factor |
|---|---:|---:|---:|
| price captured per trade | **0.0119 bps** | 3.0159 bps | **253.4×** |
| gross R per trade | +0.02718 | 0.34262 | 12.6× |
| win rate (net breakeven) | 39.05 % | 50.49 % | **+11.43 pp** |
| signal ÷ toll, whole family, at its best horizon | 0.076 | 1.0 | 13.2× |
| accumulation 2 h → 320 h | 0.965× | ≥ ~10× | 10.4× |

**Three levers exist and all three are closed:**

1. **Capture more price.** Would require 253×. 282 contract shapes were priced; 0 are net-positive;
   the direction call gets *worse* as the contract widens.
2. **Pay less toll.** Closed on arithmetic, and this is the cleanest kill in the wave: break-even
   requires the toll to fall to the gross, and the gross is negative, so the required toll is
   **negative**. A **free broker** — 100 % cost elimination, the physical limit of every
   transaction-cost, broker-selection, spread-timing and slippage repair that could ever be
   proposed — leaves the book at **−0.01327 R/trade**. Even with a 100 % cost cut the book still
   needs +0.568 pp of win rate (`d7_RESULT.md` §2.1).
3. **Select the good cells.** Closed empirically and mechanically. The broker toll's cell ordering
   travels at Spearman **+0.9005**; the edge's at **+0.0230**. The at-market edge ordering does not
   reproduce against a **random half of its own month** (+0.0466 against the toll's +0.9718) — so it
   is not non-stationarity, there is no ordering to be non-stationary about. 324 out-of-sample
   selection arms produced **zero positive books**, with a median **97.7 %** of every improvement
   being toll removed. And the oracle ceiling — perfect foreknowledge of each cell's true within-
   month edge, zero estimation error — buys **+0.02548 R/trade** against a 0.30825 toll, **12.1×
   short**. *You cannot select your way out of this even with hindsight.*

**The detection floor proves the negative is a result, not an absence.** Injecting a known
directional edge into the same rows recovers it linearly across three decades in four separate
months; January resolves an injection where only **1.03 %** of rows change side (+0.02516,
p 0.0235). The pooled 95 % half-width is **±0.01026 R/trade**, so the test resolves an effect
**32.1× smaller** than the level the family needs — and sees nothing.

### The way to know — the test that would reopen this

The owner asked for a way to know. Here it is, and it is cheap enough to run on any number of
candidate families without spending held-out data:

> **THE ACCUMULATION SCREEN.** For a candidate family, walk its rows against a paired side-mirror at
> horizons {2, 8, 24, 72, 160, 320} h and express the signal in **basis points of price**, not R.
> Admit to economic evaluation only if **(i)** capture grows by ≥ 10× from 2 h to 320 h, and
> **(ii)** capture at the family's natural horizon exceeds its own measured toll in bps.
>
> Broad V4 scores **0.97×** and **0.076**. The live W7 sleeves score **37.58×** and **2.36–11.46×**.

Two properties make this the right gate. It is **pre-economic** — it never reads a P&L, so it costs
no multiplicity and no held-out month. And it is **the property that actually separates the two
generators this estate owns**, measured, on the same walker, with the same control. If a future
broad-family variant passes it, the family is reopened on evidence. If nothing passes it, that is
the answer, and it will have been reached for a stated reason.

---

## 4. THE CORRECTED RECORD

Every published estate number this wave overturns. Old, new, reason.

| # | published claim | OLD | NEW | why it was wrong | lane |
|---|---|---|---|---|---|
| 1 | broad family gross expectancy | **−0.217496** R/trade | −0.01327 (clean roster) → +0.00106 (broker-correct fill) → **negative** once the quote side is charged | the −0.2175 is `opportunity_net_proxy_r + cost_r`, the engine's counterfactual proxy — not a path walk. The same rows walked on the tape give +0.0409 (market fill) or −0.2367 (honest fill): three numbers on one object spanning 0.28 R | f1 §2, d5, p3 |
| 2 | the breakeven gap | **"needs 45.94 %, gets 34.68 %" = −11.26 pp** | clean roster **37.98 % vs 38.55 % = −0.57 pp**; the TAKEN set is **+3.07 pp** | computed at a 2.0R target the system does not use (`risk.min_rr` = **1.5**) and on the counterfactual pool. Both 1.5R and 2.0R walks were then carried and **the sign of every conclusion is unchanged** | f1 §6 |
| 3 | the analysed population | **27,658-row pool** | **1,118,694** emissions / **331,548** honest fills / 8 windows | the pool is 18.03 % of generator output and 100 % counterfactual; its admission test reads a post-decision outcome (`v4_timewarp:28130-28140`) — fill rate 99.43 % vs 14.29 %, born-past-stop 10.57 % vs 0.15 %. **The largest selection event in the system, and it is a look-ahead** | d2 §4, f1 |
| 4 | born-past-stop share | **12.72 %** of the system's candidates | **2.02 %** of emissions, 6.81 % of fills, **0.00 %** of taken trades | pool enriched 6.1× in structurally dead rows | f1 §6 |
| 5 | the taken book | never measured | n = 464 scored, gross **+0.05505**, net **−0.01932**, −0.98 % of account over 8 months | nobody had looked at the trades the system actually made | f1 §3 |
| 6 | decision grid | 95 windows/day | **96** | — | PB |
| 7 | the bar archive's quote side | assumed MID (h3's own #1 open question) | **BID**, exactly, on 76,734 M15 + 223,239 M1 bars | never checked against ticks | d8x §2, p3 §4.1 |
| 8 | every GROSS walked on those bars | as published | optimistic by **−0.0696 to −0.1160 R/fill**, constant sign | triggers never shifted to the traded side | d8x, p3 |
| 9 | the 8-gate ledger's P1 spread gate | −0.00391 (pool) | **+0.00264** (roster) — **SIGN FLIP** | population | d2 §3 |
| 10 | d2's entry offset j = 5 (+0.01626, 8/8 months) | read as a timing edge | **81.6 % fee schedule**; gross component +0.00299 and it flips sign in 3 of 8 months | cost ordering persists at +0.8740, gross ordering at +0.0325 | p1 §5.2 |
| 11 | PB's forming-bar BOOK figures | both double-counted | Jan EARLY5 partial −0.45006 → **−0.29009** | `pbg_analyze.py:351-352` adds cohorts already contained in the arms | d6 §2 |
| 12 | f1's roster family table | 7 at-market families priced as limits | at-market cohort −0.00486 → **+0.02402**; four family signs flip | those families emit entry == the last print, i.e. a market order (0.0000 bps gap at p50, p90 **and** p99) | d1b §2 |
| 13 | AK's `sub_xvol_pullback @ target_4R` | +1.157 R/day | +0.130 at AK's own standard, +0.3435 at the ratified rule — and it **REJECTS** at all four bands | a level read as a delta (8.9×), then gated at a standard that does not govern the estate | carried, AU/BD |
| 14 | tick archive provenance (quoted in CLAUDE.md §4) | 51 files / **263,894,769** rows | 61 files / **300,538,915** accepted ticks | manifest sealed 2026-07-26; six files written 2026-07-30 | d8x §3 |
| 15 | h2's "no April/May 2026 M1 bars exist on this machine" | premise for declaring itself untestable | both packs exist; **eleven** months of M1 are on disk | directory read | d8x §4 |
| 16 | the wave's surviving candidate (forming-bar decision) | +0.1956 / +0.1930 / +0.2366 R/trade, 63/63 days | paired effect **replicates** on a fifth window (+0.18063) — the implementable book **FAILS**: −0.30551 vs the incumbent's −0.28041 | the headline is a *paired* delta living only on setups that also emit at the close, which is not knowable at decision time | d6, p2 H5b |
| 17 | `structural_distance_extreme` — the estate's one real family | 15 consecutive positive windows across 3 harnesses | **−0.13028** once the quote side is charged | its edge exists **only** in its two tightest risk-distance quintiles, which is exactly where spread-over-risk is largest. Its own quote-side correction is **0.19321 R/fill = 1.54× its sealed gross** | p3 §10, d1b §4.1 |

Two of these deserve to be read together, because between them they explain most of the estate's
history with this family: **#1/#3** mean that every number published before this wave described a
counterfactual missed-opportunity ledger — the trades the system *did not take* — enriched 6.1× in
structurally dead rows and admitted by a gate that reads the future. **#7/#8/#17** mean that the
residual positives that survived the population correction were measuring the bid-ask.

---

## 5. WHAT SURVIVES

Four things. One is an economic result, one is a source defect, one is an instrument repair, one is
a method. **None of them saves the broad family, and I am not going to pretend otherwise.**

### 5.1 The exit contract — the only axis whose ordering travels and is not the fee schedule

`stop_only_horizon` beats the shipped `target_2.0R`.

- **Persistence** (`p1 §5.1`): rank persistence **+0.6399 on GROSS** and +0.6361 on net, against
  +0.0013 for the gate grid's gross and +0.0325 for the entry offset's. The cost delta is **exactly
  0.00000 in all eight months** — this is the only lever in the wave with zero cost content. The
  menu ordering is monotone in the target ladder in every single month.
- **Magnitude** (`d2 §7`): +0.03500 R/trade pooled, day-block CI95 [+0.01854, +0.05163], positive in
  **8 of 8** open months, and it survives leave-one-month-out.
- **Sealed test** (`p2` H3): **+0.01002**, positive in 3 of 3 unseen months (+0.01248 / +0.01822 /
  +0.00093) — but CI95 [−0.01537, +0.03774] and it **fails its own pre-declared +0.02 bar**. Under
  half its in-sample value.
- **Adversarial** (`d7 §3`): the 56-cell exit surface is a **coin flip at every single cell** — the
  paired mirror captures 108.5 % of the best cell's gain and the signal is negative at all 56. So
  the exit contract is a *contract* improvement available to any participant, **not evidence of an
  edge**. Which is precisely why it transfers.

**Standing:** real, 11 of 11 windows positive across open and sealed, zero cost content, ordering
travels. Worth +0.010 to +0.035 R/trade. It moves the broad family from −0.292 to −0.257. **It
changes nothing here and it is the wave's one transferable asset** — its natural home is the live
sleeve book, where one R is 44–436 bps instead of 8.

### 5.2 The POI admission gate — a real source defect, free to repair

`_zone_proximity_pct` returns gap/price and is compared to `poi_proximity_tolerance_pct = 0.01`
(**1.0 % of price**), while the candidate it then builds is denominated in **R** at a median risk of
7.41–8.91 bps. That is an **11.2–13.5 R admission radius on a 1.5 R trade**
(`broader_origin_generators.py:1201, :1391, :1446`; tolerance at `config/agent_config.yaml:4032`).

Consequence, measured on 1,066,352 POI emissions: only **7.9–14.4 %** of them are the contract the
family describes. **25.7 %** of `current_breaker_re_entry` emissions are born past their own stop,
fill **100 %** of the time because they are marketable by construction, are **69.5 % of that
family's fills**, book **−1.3038 R net each**, and are **91.8 % of its entire negativity**. That one
family is 74 % of the whole published negativity of the roster.

**Standing:** the repair is correct, one predicate at three call sites, behind an absent-false key,
and it eliminates the entire dead bin. It also **does not save the family** — d4 priced it honestly:
the repaired, correctly-formed resting-limit book books **−0.24981 R/fill**. Fix it because it is a
defect in shared machinery, not because it recovers anything.

### 5.3 The walker quote-side repair — an instrument, not a result

Stated in §1 limb 3. p3 refines d8x's form: the shift is **asymmetric**. A long's exits are quoted
on the bid and are already walked correctly; only its entry trigger displaces. A short takes the
displacement on **both** exit legs. The two models agree to the digit on shorts and differ only on
longs.

**Standing:** this is the highest-value forward item in the whole wave, because it is the
precondition for any future usage measurement in this estate meaning anything — **every usage lever
found this wave is smaller than the bias**, and the same walkers price the live sleeve work.

### 5.4 The accumulation discriminant — the method

§3. The one genuinely new idea the wave produced, and the only thing here that generalises beyond
this family.

### What DIED, each with its mechanism

| result | mechanism of death | lane |
|---|---|---|
| forming-bar decision (+0.1956, 63/63 days) | the phantom leg has already lost **−0.55503 R = 98.0 %** of its entire 120-bar loss by the time the bar closes, so cancel-at-close saves nothing; failed the sealed test at −0.30551 vs −0.28041 | d6, p2 |
| `structural_distance_extreme` (15/15 windows) | its edge lives only in its two tightest-stop quintiles, i.e. exactly where the quote-side error is largest; its own correction is 1.54× its sealed gross | p3, d1b |
| affordability / cheapest-toll selection | selecting on affordability re-discovers the fee schedule: cost rank travels at +0.9005, edge rank at +0.0230; 324 OOS arms, 0 positive books, median 97.7 % of every gain is toll | p1, f2, d7 |
| entry offset j = 5 | 81.6 % fee schedule; gross component flips sign in 3 of 8 months | p1 |
| the cheapest-toll decile (+0.17209, 8/8, 16/16) | built and killed **inside its own lane** — 1,297 contaminated rows carried +0.164 of the +0.172 | d1b §7 |
| breaker inversion (+11.9 R/trade published) | the fill-blind convention; priced honestly it is **−0.08795** net and the whole-family +1.374 figure is the mirror of born-past-stop rows | d1b §6 |
| cell/instrument/family selection generally | the oracle ceiling with zero estimation error is +0.02548 against a 0.30825 toll | p1 |

---

## 6. WHAT TO DO NEXT — ordered, with what each is worth and what it costs

**1. Stop spending measurement on the broad V4 family as a source of tradeable edge. Cost: zero.
Worth: everything currently burning on it.**
The price-unit deficit is 253×, the accumulation is 0.97×, the sealed test is spent, and the estate
has **no held-out data left** — all three sealed months are recorded SPENT. There is no measurement
that can now change this verdict, which is itself the strongest reason to stop. Related owner
decision, on the record: the TAKEN book (507 trades, net −0.01932 R/trade, −0.98 % of account over
eight months) **cannot be adjudicated by running it — 14.4 years** for the 95 % CI half-width to
equal its own deficit. Any argument for keeping it live has to rest on something other than the
expectation of learning from it.

**2. Repair the walkers' quote side. Cost: ~1 hour. Worth: removes a −0.0696 to −0.1160 R/fill
constant-sign bias.**
Stop at (d − s), target at (T·d + s), with p3's measured asymmetry (long: entry trigger only; short:
both exit legs). This bias is **larger than every usage lever this wave found**, so until it lands,
no future usage measurement in this estate is interpretable — including on the sleeves, which share
the walkers. It converts d8x's bound into a book.

**3. Port the exit-contract finding to the live sleeve book. Cost: already wired
(`run_book.py --frontier-exits`, default off) plus AD's existing 1,631-cell frontier. Worth: the
same +0.010–0.035 R/trade of ordering, on trades where one R is 44–436 bps instead of 8.**
The finding has zero cost content and its ordering travels — the only lever in the wave of which
both are true. Its value on the broad family is arithmetically irrelevant; on the sleeves it is not.
Gate it at the ratified rule before anything is armed.

**4. Fix the POI %-vs-R gate. Cost: one predicate at three call sites plus tests, behind an
absent-false key. Worth: eliminates a bin that is 25.7 % of one family's emissions, fills 100 % of
the time, and books −1.3038 R each.**
Hygiene on shared generator machinery. Do not present it as economic salvation; the repaired book is
still −0.24981 R/fill.

**5. Stand up the accumulation screen as the estate's pre-economic admission gate. Cost: about a
day, reusing d3's harness. Worth: it makes the first look at a candidate family cheap.**
This is the direct answer to *"without restricting or narrowing down the edge just because we
couldn't answer a couple of questions"* — the reason this estate rationed itself to two or three
months all year is that every look was expensive. A screen that reads no P&L costs no multiplicity
and no held-out month, so the estate can look at *many* families instead of few. Specify it once,
pin it with a test, require it before any economic evaluation.

**6. Run the screen on the 12.5-year H4/D1 archive nobody has opened. Cost: hours.
Worth: it establishes the base rate — d3's 37.58× currently has no null.**
`deep_universe_h4d1_2014_2026`: 48 files, **exactly the broad family's 24 instruments**, H4 + D1,
2014-01-02 → 2026-06-15, 439,895 bars, 27 MB, **zero references in any script or receipt in the
entire discovery corpus**. Until this is run we do not know whether 37.58× means "a working sleeve
accumulates" or "these instruments accumulate over 2014–2026 and anything measured on them will".
That distinction decides whether the screen is a discriminant or a tautology, so it comes before any
new family is screened.

**7. Capture new held-out data. Cost: a data pull. Worth: without it nothing can ever be adjudicated
again.**
Three results died out of sample this week and the sealed three are what caught the fourth. The
estate is now at zero. Do this before the next candidate exists, not after.

**Explicitly NOT recommended:** any further broad-family filter, ranker, cost-cap, session rule,
instrument subset, entry-offset, sizing rule or exit sweep. Between them p1's 324 arms, d7's 66
ex-ante cells and 56 exit cells, d6's 1,414 rule cells, f2's 42× cost-cap sweep and d3's 282
contracts have covered that space, and the oracle ceiling says the space is empty even with
hindsight.

---

## 7. WHAT I GOT WRONG — the register

Mandatory, and it includes this wave's own lanes.

### 7.1 The estate's standing errors, corrected here

1. **The population.** For a year the family was analysed on a 27,658-row counterfactual pool that
   is 18.03 % of output and admitted by a gate that reads the future. Every generalisation from it
   to "the system's trades" was invalid. The corrected object is 1,118,694 emissions.
2. **The headline expectancy.** −0.217496 was never a path walk. It was the engine's own
   counterfactual proxy plus cost. Three walkable numbers exist on the same rows spanning 0.28 R.
3. **`risk.min_rr` is 1.5, not 2.0.** Every breakeven in the estate was computed against a target
   the system does not use, turning a −0.57 pp gap into a published −11.26 pp one — a 20× overstatement.
4. **The bar archive's quote side was never checked.** It is BID, it was always BID, and h3 filed
   the question as open while four lanes walked it as if it were mid.
5. **The tick manifest** under-declares the archive by 10 files and ≥ 36.6 M rows, and CLAUDE.md §4
   quotes the stale figure.

### 7.2 This wave's own lanes — errors found and published by the lanes themselves

I am recording these because a wave that only audits its predecessors is not auditing anything.

- **d1b built a headline and killed it**: a cheapest-toll decile reading +0.17209 gross, 8/8 months,
  16/16 instruments, direction value at p 0.0000 — of which **+0.164 of the +0.172 came from 1,297
  contaminated rows**. It was caught only because it disagreed with f2's cost-cap sweep by an order
  of magnitude. *The disagreement was the detector; had the two lanes not overlapped it would have
  shipped.*
- **d3 found a walker defect worth 36.2× on gross**: a `partial_be_runner` arming on "MFE ever
  touched +arm_r inside the horizon" credits the partial on rows whose stop already fired. Same
  defect class as this week's headline #1, one layer up.
- **d6 corrected PB's published book figures** in both directions — both arms double-counted a
  cohort they already contained.
- **d7's own headline did not replicate.** Its direction inversion (−0.04230, CI excluding zero,
  0/5 windows) is contradicted by the sealed test on the same cohort construction (+0.02391, 3/3
  windows). *I have not silently averaged them* — see §7.3.
- **d5's central claim was overturned by p3 within the same wave.** "The gross is ZERO at the
  broker-correct fill contract" reproduced to five decimals and then died to a quote-side error 8–12×
  the size of the claim.
- **f1's roster family table** priced seven of ten families under the wrong order type.
- **d1b's mirrored-limit control is an artifact on the three POI families** — mirroring a resting
  limit about its entry produces an order marketable at once, at a price the book cannot get. So the
  unconditional POI direction test *does not exist* in this wave.
- **h2 declared itself untestable on a false premise** — the April and May bars it said were absent
  are in the directory it loads from.

### 7.3 What this document could still be wrong about

- **The direction sign is genuinely unresolved and I have not hidden it.** f2 says +0.02877, p2's
  sealed test says +0.02391 in 3 of 3 windows, d7 says −0.04230 in 0 of 5, p3's paired mirror over
  eight windows says −0.00096 (positive in 2 of 8). **I have adjudicated this as "zero within a band
  10–30× smaller than the toll", not as a positive or a negative**, because the disagreement is
  smaller than the measurement error of the instrument that produced all four numbers (§1 limb 3).
  If a future measurement resolves the sign, **it does not change the verdict** — the verdict rests
  on the 253× price-unit shortfall and the 0.97× accumulation, neither of which depends on the sign.
  That is deliberate: I have tried to make the verdict robust to the thing the wave could not settle.
- **The live-sleeve control in d3 is in-sample, n = 134, and all five sleeves REJECT at the ratified
  gate.** The 37.58× accumulation figure is therefore optimistic, and the receipt says so. A 10×
  haircut still leaves it 66× above the broad family, so the discriminant survives — but until
  item 6 runs, **the accumulation screen's threshold is calibrated on one arguably-lucky sample.**
  This is the largest single soft spot in the verdict.
- **p3's tick truth covers 4 symbols and 2 windows**; the 8-window figure is modelled. The model and
  the measurement agree to within 4 % on January, which is why I have leaned on it, but it is a
  model.
- **The lane-count risk of this document.** a1 is a synthesis lane. Its characteristic failure is
  manufacturing coherence — reading thirteen lanes as one argument when they are thirteen. I have
  tried to guard it by leading with the single construction that needs no synthesis (the oracle
  ladder's two numbers, one artifact, one population) and by naming every disagreement rather than
  resolving it by assertion. Readers should treat §1 as load-bearing and §2 as corroborating.
- **What would falsify this verdict:** a candidate family on these instruments that passes the
  accumulation screen. Nothing else. Not a better filter, not a better exit, not a cheaper broker —
  §3 closes all three arithmetically.

---

## 8. THE ANSWER, RESTATED FOR THE OWNER

You asked whether it is the sleeves or the way we use them.

**It is the sleeves.** The way we use them is close to as good as it can get: hand the machinery you
already own a correct direction call and it makes **+0.5967 R/trade** instead of losing 0.2923. The
setups deliver **0.249 %** of that.

The reason — the thing you asked for, so that "finished" is a finding and not a shrug — is that these
setups fire on a scale smaller than the cost of trading them and **their information does not grow
with time**. They capture **0.0119 basis points** of price per trade, which is **1.7 % of one
spread**, against a **3.0159 bp** round-trip toll. Held for two hours or for two weeks, the number
is the same: 0.20 bps at 2 h, 0.19 bps at 320 h. A sleeve that works goes from 3.4 bps to 128.0 bps
over that same stretch — that is what an edge looks like when you hold it, and this family has never
had it.

That is also the way to know, for anything you build next: **measure whether it accumulates, before
you measure whether it pays.** It costs hours, it spends no held-out data, and it is the one property
that separates the thing that works from the thing that does not. It does not narrow the search — it
is what makes a wide search affordable.

---

*Receipt: `phase19/receipts/discovery/a1verdict_RESULT.md` / `.json`.
Companion data: `SLEEVES_OR_USAGE_VERDICT.json`.
Adjudicates lanes f1, f2, d1b, d2, d3, d4, d5, d6, d7, d8x, p1, p2, p3 — full receipts under
`phase19/receipts/discovery/`.*
