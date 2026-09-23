# f2 — THE DECIDING EXPERIMENT: the signals under PERFECT usage

Lane f2, wave 19. Branch `phase19/broad-forensic`.

Everything below is measured over the **whole** population of **eight months** —
**141,230 priced at-market setups over 172 trading days**, October 2025 through May 2026,
24 instruments, 7 origin families. Nothing is sampled. Nothing under `src/` was edited.
The three **sealed** months (Jun/Aug/Sep 2025) were not generated and not read.

Machine-readable: `f2/F2_LADDER_{202510,202511,202512,202601,202602,202603,202604,202605}_V1.json`,
`f2/F2_POWER_{202510,202601,202602,202603}_V1.json`, `f2/F2_POOLED_V1.json`.
Code: `f2_ladder.py`, `f2_run.py`, `f2_power.py`, `f2_pool.py`.

---

## 0. THE ANSWER, IN FIVE SENTENCES

**Give the broad V4 family's own signals a perfect exit, a perfect entry instant, a perfect
ranker and unlimited capacity, and the book is enormously positive: +2.339 net R/trade.**
**Then flip a coin for the direction on the same rows, at the same instants, with the same
risk distances and the same toll, and the coin gets +2.311 — 98.8 % of it.** The signal's own
contribution, pooled over 141,230 trades, is **+0.02877 R/trade under perfect usage and
+0.00315 R/trade as the system runs it**, against a measured broker toll of **0.32954
R/trade**: the family is short of breakeven by **11.5×** at its best conceivable usage and by
**105×** at its actual one. The measurement could not have missed anything economically
relevant — an injected edge of **+0.025 R/trade is detected at p = 0.0235 in a single month**,
and the pooled 95 % half-width is **±0.01026**, so the test resolves an effect **32× smaller
than the level the family would need to be viable**. **The verdict is SIGNAL: the setups carry
no directional information, and the single cleanest proof needs no oracle at all — they pick
the correct direction 0.297 percentage points LESS often than a coin flip on their own rows
(0.39960 vs 0.40257).**

---

## 1. WHAT WAS BUILT, AND WHY IT IS THE RIGHT OBJECT

### 1.1 The population is the roster, not the pool

Every rung is priced on Session PB's reproduced **close-only candidate roster** — the
production generator's own emissions at each M15 close, which PB matched to the sealed January
arm at **153,211 / 153,486 = 99.82 %** on a ten-decimal geometry hash. The 27,658-row
`CJ_RECLOCKED_S0R0_POOL_V1` is **not** used for any economic claim here: it is 18.03 % of
generator output, 100 % counterfactual, and filtered by a downstream outcome-decodability gate.

Collapsed to one row per setup key `(symbol, family, side, bar)` — PB's own semantics — the
at-market population is:

| month | setup keys | priced | trading days | days net-positive at R1 |
|---|---:|---:|---:|---:|
| 2025-10 | 19,929 | 19,287 | 23 | 0 |
| 2025-11 | 17,178 | 16,766 | 20 | 0 |
| 2025-12 | 18,705 | 18,090 | 23 | 0 |
| 2026-01 | 17,878 | 17,722 | 21 | 0 |
| 2026-02 | 16,748 | 16,494 | 20 | 0 |
| 2026-03 | 18,413 | 18,142 | 22 | 2 |
| 2026-04 | 18,620 | 17,922 | 22 | 0 |
| 2026-05 | 17,254 | 16,807 | 21 | 0 |
| **total** | **144,725** | **141,230** | **172** | **2** |

**Five of the eight months (Oct/Nov/Dec 2025, Apr/May 2026) had no close-only roster before
this lane**; they were generated here with PB's unmodified harness
(`pbg_run.py --min-rr 1.5 --workers 5`, 96 windows/day, the real
`generate_live_broader_origin_candidates`). This is the widest window the broad family has
ever been read on.

### 1.2 The harness reproduces the published baseline exactly

Rung R1 on January is **n = 17,722, gross +0.038180, cost 0.335605, net −0.297425**.
PB's published `close_arm` for the same month is **n = 17,722, gross +0.038179684,
cost 0.335605167, net −0.297425483**. Identical to every printed digit. Two contract details
had to be right to get there, and both are recorded because either one silently moves the
answer by more than the entire measured signal:

1. **The forward path starts at stamp D+1, not D.** A market order sent at instant `D` fills
   at the close of stamp `D−1`; the sealed sidecar's walk then runs `D+1 … D+120`. Including
   the fill minute cost 0.014 R/trade of gross on the first pass here (x3 §5a measured 0.003 R
   on its own population). `f2_ladder.r_frames` takes the fill column `j` and slices `j+2 …`.
2. **The entry is the generator's own emitted price**, not the tape's last print. PB proved the
   two are equal at 0.0 relative error on 198,539/198,539 at-market emissions — but only where
   the tape *has* that minute; using the tape dropped 270 January rows and moved gross by
   0.014 R.

The tie rule (target and stop both reachable inside one M1 bar → **stop wins**), the horizon
(120 M1 bars), the four-term broker-true cost model (hour-aware tick spread + broker-true
commission + measured price-unit slippage + swap on broker-midnight crossings) and the 1.5R
generator geometry with the shipped downstream 2.0R `momentum_exhaustion` target are all PB's,
unchanged.

### 1.3 The ladder, and the control that makes it readable

| rung | what is replaced by a perfect version |
|---|---|
| **R0** | nothing — the shipped cost gate (`spread_r ≤ 0.10` **and** `cost_r ≤ 0.15`, L8/L11) plus the shipped exit contract |
| **R1** | the gate: admit every emission |
| **R2** | the ranker: at the system's **own daily capacity** (= the number R0 admits that day), keep the rows that will win |
| **R3** | the exit: per trade, the best contract on its own realised path |
| **R4** | the entry instant: the best of the 15 M1 stamps covering the following M15 bar, risk distance held at the generator's own `d` |
| **R5** | the direction: take whichever side the path rewarded |

**Two matched placebos are computed identically at every rung, and they are the point of the
lane.** An oracle exit is enormously positive on *any* entry; a rung's level says nothing on
its own.

* **PLACEBO-SIDE** — identical rows, identical instants, identical risk distances, identical
  toll, **random side**. It isolates the *directional* claim, and because it shares every row
  with the real arm the per-row difference is **paired** and the toll cancels exactly.
* **PLACEBO-TIME** — same symbol and same trading day, **random instant** drawn from the
  system's own 96-window grid, random side. It isolates the *whole* signal, timing included.

**`real − placebo` at each rung is what the signal contributes once that layer is perfect.**

### 1.4 Two oracle-exit definitions, because one of them is a trap

`R3b/R4b` (**path oracle**) exits at the best **close** anywhere on the path — a real print, a
real fill. `R3c` (**intrabar oracle**) exits at the best intrabar extreme. The gap is the
**bar-resolution premium** that killed this week's headline #1: pooled it is
**+0.18849 R/trade, 8.48 % of the intrabar oracle's own level**. Nothing here is banked on
`R3c`; it is published to price the trap. The exit menu's `trail_1R` and `be_runner` arms both
build their trigger level from strictly prior bars for the same reason.

---

## 2. THE LADDER — TRACK A, CAPACITY-MATCHED (pooled, 8 months, 141,230 rows)

Each rung is re-ranked under its own realised outcome, then cut to the shipped gate's own daily
trade count. `delta` is the change from the rung below; `coin-flip share` is that same delta
measured on PLACEBO-SIDE, divided by the real delta.

| rung | n | win rate | gross R | cost R | **net R** | placebo net | **SIGNAL** | delta | coin-flip share of delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **R0** as the system runs it | 58,618 | 0.4283 | +0.00223 | 0.06848 | **−0.06625** | −0.05649 | **−0.00976** | — | — |
| **R1** + no gate | 141,230 | 0.3996 | +0.02328 | 0.31553 | **−0.29226** | −0.29447 | **+0.00221** | −0.22601 | 1.0530 |
| **R2** + oracle ordering | 58,618 | 0.8878 | +1.23913 | 0.23666 | **+1.00247** | +1.00091 | **+0.00156** | +1.29473 | 1.0005 |
| **R3** + oracle exit | 58,618 | 1.0000 | +3.27016 | 0.31566 | **+2.95450** | +2.91839 | **+0.03611** | +1.95203 | 0.9823 |
| **R4** + oracle entry | 58,618 | 1.0000 | +4.38121 | 0.36002 | **+4.02119** | +3.96981 | **+0.05138** | +1.06669 | 0.9857 |
| **R5** + oracle direction | 58,618 | 1.0000 | +6.94086 | 0.41565 | **+6.52521** | +6.52687 | **−0.00166** | +2.50402 | 1.0212 |

**Every rung delta is 98.2 %–105.3 % reproduced by a coin flip.** No layer of the ladder buys
anything attributable to the signal.

**R0 is the one place a real, live-implementable layer adds value, and it adds it by trading
less.** The shipped gate admits **40.97 %** of emissions and improves the book by
**+0.22601 R/trade** — the largest real (non-oracle) improvement anywhere in this receipt. Its
**signal** contribution is **−0.00976**: it makes the directional content slightly *worse*
while removing 78 % of the toll (0.31553 → 0.06848). **It is a toll filter, not a selector**,
and that distinction is the whole result of §5.

---

## 3. THE LADDER — TRACK B, FULL POPULATION (the decomposition that answers the question)

No capacity constraint, so the rows are identical at every rung and the levels are directly
comparable.

| rung | n | gross R | **net R** | placebo net | **SIGNAL** | placebo / real |
|---|---:|---:|---:|---:|---:|---:|
| R1 no gate, shipped exit | 141,230 | +0.02328 | **−0.29226** | −0.29447 | **+0.00221** | 100.8 % |
| R3 oracle exit — menu | 141,230 | +1.38560 | **+1.07007** | +1.05073 | **+0.01933** | 98.2 % |
| R3b oracle exit — path | 141,230 | +2.03415 | **+1.71862** | +1.69333 | **+0.02529** | 98.5 % |
| R3c oracle exit — intrabar *(unachievable)* | 141,230 | +2.22264 | +1.90711 | +1.87451 | +0.03260 | 98.3 % |
| R4 oracle entry + menu exit | 140,946 | +2.26442 | **+1.94958** | +1.92389 | **+0.02569** | 98.7 % |
| R4b oracle entry + path exit | 140,946 | +2.65398 | **+2.33914** | +2.31133 | **+0.02781** | 98.8 % |
| R5 oracle direction | 140,946 | +3.89769 | **+3.58285** | +3.58381 | **−0.00096** | 100.0 % |
| R5b direction only, shipped exit | 141,230 | +0.91226 | +0.59673 | +0.59767 | −0.00094 | 100.2 % |

**R5 is the sanity check that proves the machinery can see zero when zero is the truth.** The
direction oracle is side-agnostic by construction, so real and placebo *must* coincide — and
they do, to 0.001 R/trade. Any rung where the real arm genuinely separated would stand out
against that floor; none does.

### 3.1 The paired significance statement

PLACEBO-SIDE shares every row, instant, risk distance and toll with the real arm, so the
per-row difference is paired and the toll cancels exactly. Day-block bootstrap, 2,000 draws,
pooled across months as independent blocks.

| rung | n paired | pooled signal | 95 % half-width | months positive |
|---|---:|---:|---:|---:|
| R1 shipped exit | 141,230 | **+0.00315** | ±0.01026 | 5/8 |
| R3 oracle exit — menu | 141,230 | +0.02027 | ±0.02498 | 6/8 |
| R3b oracle exit — path | 141,230 | +0.02623 | ±0.02745 | 5/8 |
| R4 oracle entry + menu exit | 140,946 | +0.02666 | ±0.02559 | 7/8 |
| R4b oracle entry + path exit | 140,946 | **+0.02877** | ±0.02816 | 6/8 |

**Not one rung's confidence interval excludes zero**, on the widest population the broad family
has ever been measured over.

---

## 4. THE FOUR QUESTIONS THE BRIEF ASKED, ANSWERED

### 4.1 At R3/R4 — perfect usage, real signals — is the book positive?

**Yes, and it is not close: +1.719 to +2.339 net R/trade at R3b/R4b, +2.955 to +4.021 at the
capacity-matched rungs.** *And that is not evidence for the signal*, because the identical
ladder on a coin flip returns +1.693 to +2.311 — **98.8 %** of it. The correct reading of
"perfect usage makes it positive" is that **perfect usage mines path volatility, which is
available to anybody who trades that instrument at that minute with that stop.**

**The signal-attributable book at perfect usage is +0.02877 R/trade against a 0.32954 R/trade
toll: −0.30076 R/trade short of breakeven.**

### 4.2 How far short is R4 of breakeven — in R, and in bps?

| quantity | pooled (8 months) | range across months |
|---|---:|---|
| broker toll | **0.32954 R/trade** | 0.2409 … 0.3892 |
| broker toll, in price bps | **3.0577 bps** | 2.9641 … 3.1525 |
| one R, in price bps | **21.920 bps** | 17.15 … 32.56 |
| toll as a share of risk | **13.95 %** | |
| R1 gross | +0.02328 R = **+0.1877 bps** (mean) | −0.445 … +0.557 bps |
| R1 **signal** | +0.00315 R = **−0.0759 bps** (mean) | −1.110 … +0.399 bps |
| R4b gross | +2.65398 R = **+32.889 bps** (mean) | 25.18 … 46.80 bps |
| R4b **signal** | +0.02877 R = **+0.0813 bps** (mean) | −0.637 … +0.740 bps |

**Shortfall at R4, on signal alone: −0.30076 R/trade. The signal is 8.7 % of the toll and
would have to be 11.5× larger to break even.** As the system actually runs it (R1) the signal
is **0.96 % of the toll** and would have to be **105× larger**.

**The bps line is the transferable one, because it does not depend on stop geometry.** The
broker charges **3.058 bps** and holds it inside ±3.1 % across eight months — it is a fee
schedule, not a variable. The family's directional information is worth **−0.08 to +0.08 bps,
and its sign flips between months (negative in 3 of 8 at R1, 3 of 8 at R4).** The toll is
roughly **40×** the signal's magnitude, and the signal's sign is a coin flip month to month.

### 4.3 Which oracle rung buys the most?

| oracle | delta, net R/trade | share of the oracle stack | coin-flip share of that delta |
|---|---:|---:|---:|
| direction (R4→R5) | **+2.50402** | 36.7 % | 102.1 % |
| exit (R2→R3) | +1.95203 | 28.6 % | 98.2 % |
| ordering (R1→R2) | +1.29473 | 19.0 % | 100.1 % |
| entry instant (R3→R4) | +1.06669 | 15.7 % | 98.6 % |

**The exit is the largest layer a live system could plausibly move** (direction is not a
"layer" — it *is* the signal). But the naming is a trap, and the trap is the point: **every one
of these deltas is 98–102 % reproduced on random rows.** The takeaway is not "work on exits";
it is **"exit geometry is worth ~+1.95 R/trade to anybody, including a coin flip, so an exit
improvement is never evidence of an edge."** That is exactly the lesson this week's dead
headline #1 paid for — its trailing stop manufactured +0.084 R/trade of bar-resolution premium
— and here it is generalised: the whole oracle stack behaves that way.

### 4.4 R5 vs R4 — how much is direction versus everything else?

**+2.50402 R/trade, 36.7 % of the total oracle stack.** Direction is the single largest
component, it is exactly the quantity the generator claims to supply, and the measured signal
contribution at that rung is **−0.00166 R/trade**.

**The cleanest version of the same fact needs no oracle at all.** Under the shipped contract,
pooled over 141,230 trades:

| | win rate | gross R/trade |
|---|---:|---:|
| the real signal | **0.39960** | +0.02328 |
| a coin flip on the same rows | **0.40257** | +0.02012 |
| a random instant, random side | 0.40937 | +0.01513 |

**The setups pick the correct direction 0.297 percentage points LESS often than a coin flip on
their own rows.** The small positive gross gap (+0.0032 R) comes from asymmetry among the
losers, not from being right more often. At a 2R target against a 1R stop a genuine one-point
win-rate edge would be worth ≈ +0.03 R/trade; the family delivers a **negative** 0.30-point one.

---

## 5. IS THERE ANY COST CAP AT WHICH THIS PAYS? (no — and the mechanism is legible)

The shipped gate is a cost filter. Pushed to its limit, over all eight months:

| cap on `cost_r` | n | share of pop. | gross R | cost R | **net R** | placebo net | signal | months net + |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| none | 141,230 | 97.6 % | +0.02328 | 0.31553 | **−0.29226** | −0.29447 | +0.00221 | 0/8 |
| ≤ 0.50 | 117,173 | 81.0 % | +0.01031 | 0.16431 | −0.15400 | −0.15287 | −0.00112 | 0/8 |
| ≤ 0.30 | 98,128 | 67.9 % | +0.00640 | 0.12088 | −0.11448 | −0.11284 | −0.00164 | 0/8 |
| ≤ 0.20 | 79,791 | 55.2 % | +0.00573 | 0.09230 | −0.08657 | −0.08643 | −0.00013 | 0/8 |
| **≤ 0.15 (shipped)** | 65,381 | 45.2 % | +0.00340 | 0.07439 | −0.07099 | −0.06724 | −0.00374 | 0/8 |
| ≤ 0.10 | 45,683 | 31.6 % | +0.00090 | 0.05303 | −0.05213 | −0.04640 | −0.00573 | 0/8 |
| ≤ 0.07 | 31,803 | 22.0 % | +0.00199 | 0.03925 | −0.03726 | −0.03064 | −0.00663 | 1/8 |
| ≤ 0.05 | 21,357 | 14.8 % | +0.00198 | 0.02912 | −0.02714 | −0.02161 | −0.00553 | 1/8 |
| ≤ 0.03 | 10,968 | 7.6 % | +0.01528 | 0.01878 | **−0.00349** | −0.00696 | +0.00347 | 4/8 |
| ≤ 0.02 | 5,879 | 4.1 % | −0.00738 | 0.01336 | −0.02074 | −0.00953 | −0.01122 | 2/8 |
| ≤ 0.01 | 1,466 | 1.0 % | −0.00167 | 0.00747 | −0.00914 | −0.00422 | −0.00492 | 3/8 |

**There is no cap at which the book is net-positive.** *(On the first seven months the
`≤ 0.03` cell was marginally positive at +0.00283; adding May 2026 turned it to −0.00349. A
cell that changes sign on one extra month was never a threshold.)*

**The mechanism, stated exactly.** Across a 42× sweep of the cap the **gross never leaves the
band −0.007 … +0.023 R/trade** — tightening affordability does not find better trades. What
moves is the toll: 0.3155 → 0.0075, a 42× reduction. **Net therefore converges toward zero
from below and never crosses it.** This is this week's dead headline #2 measured from the
other side and given its mechanism: **selecting on affordability buys a smaller toll, never a
bigger edge, so it converges on the fee schedule and stops.** It is not a strategy; it is a
limit.

---

## 6. THE DETECTION FLOOR — why "no signal" is a result and not an absence

"We measured nothing" is only a claim if the measurement could have seen something.
`f2_power.py` injects a **known** directional edge into the same rows — on a random
`q`-fraction the generator's side is replaced by the side the realised path rewarded — and runs
the identical paired test against the identical PLACEBO-SIDE arm.

January 2026 (n = 17,722; only about half of an injected row actually changes side):

| injected `q` | rows whose side actually changed | recovered R1 signal | 95 % CI | p(≤0) |
|---:|---:|---:|---|---:|
| **0.000 (the real signal)** | 0.00 % | **+0.00794** | [−0.01565, +0.03426] | 0.2785 |
| 0.005 | 0.25 % | +0.01218 | [−0.01164, +0.03893] | 0.1720 |
| 0.010 | 0.56 % | +0.01681 | [−0.00627, +0.04188] | 0.0810 |
| **0.020** | **1.03 %** | **+0.02516** | **[+0.00048, +0.05235]** | **0.0235** |
| 0.030 | 1.52 % | +0.03502 | [+0.01063, +0.06157] | 0.0030 |
| 0.050 | 2.46 % | +0.04840 | [+0.02555, +0.07423] | 0.0000 |
| 0.100 | 5.27 % | +0.09880 | [+0.07461, +0.12510] | 0.0000 |
| 0.200 | 9.81 % | +0.17785 | [+0.15498, +0.20266] | 0.0000 |
| 0.500 | 25.80 % | +0.46067 | [+0.43316, +0.49100] | 0.0000 |

**Three more months reproduce it.** February 2026's first cell excluding zero is `q = 0.05`
(+0.04698, p = 0.0075); March 2026's is `q = 0.03`; **October 2025 — a month generated by this
lane and never read before — is `q = 0.030` (+0.02254, p = 0.0335), and its own `q = 0` real
signal is NEGATIVE at −0.00377 (p = 0.6285).** **Recovery is linear in the injection across
three decades** in every month — the check that the estimator is unbiased, not merely quiet.

**The floor.** One month detects **+0.025 R/trade**. Pooled over eight months the 95 %
half-width at R1 is **±0.01026**, so the pooled floor is ≈ **+0.010 R/trade**.

**Against the bar that matters: the family needs +0.32954 R/trade to break even. The test
resolves +0.010. It is 32× more sensitive than the level required for viability, and it sees
nothing.** There is no room left for "the edge is there but too small to see" — an edge that
small is worthless by the same arithmetic that makes it invisible.

---

## 7. PER FAMILY AND PER INSTRUMENT — nothing is hiding in the mix

Pooled over 8 months. `sig/toll` is the signal as a fraction of that cohort's own toll — the
ratio that would have to reach **1.0** for the cohort to pay for itself on its own signal.

| origin family | n | R1 net | signal R1 | mo + | signal R4-path | mo + | toll | **sig/toll** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| session_open_range_break | 8,195 | −0.08796 | **+0.02423** | 5/8 | +0.01809 | 6/8 | 0.09030 | **0.268** |
| liquidity_sweep_reclaim | 42,754 | −0.27694 | +0.01391 | 6/8 | +0.04486 | 5/8 | 0.30321 | 0.046 |
| structural_distance_extreme | 23,282 | −0.57156 | +0.01353 | 4/8 | +0.06995 | 5/8 | 0.64011 | 0.021 |
| cross_asset_lead_lag | 20,869 | −0.43444 | +0.00835 | 5/8 | +0.01195 | 4/8 | 0.45822 | 0.018 |
| displacement_continuation | 38,606 | −0.14364 | −0.01827 | 2/8 | +0.00167 | 3/8 | 0.15053 | −0.121 |
| volatility_compression_expansion | 5,217 | −0.12677 | −0.03486 | 2/8 | −0.00704 | 3/8 | 0.08724 | −0.400 |
| regime_transition_break | 2,307 | −0.05822 | −0.03588 | 1/8 | −0.01884 | 2/8 | 0.05520 | −0.650 |

**Four of seven families carry a positive signal, three negative; the best reaches 27 % of its
own toll and none reaches 100 %.** `session_open_range_break` is the only cohort worth naming
— +0.024 R/trade of directional content, positive in 5 of 8 months, on a **cheap** toll of
0.090 R — and even it is **3.7× short of paying for itself**. It is 5.8 % of the population.

By instrument (all 24 measured; best five and worst three shown):

| instrument | n | R1 net | signal R1 | mo + | signal R4-path | mo + | toll | sig/toll |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| USDCHF | 6,270 | −0.35986 | +0.04165 | 6/8 | +0.05062 | 5/8 | 0.4024 | +0.104 |
| XAGUSD | 5,976 | −0.28454 | +0.02270 | 5/8 | −0.01049 | 5/8 | 0.3286 | +0.069 |
| GBPJPY | 6,554 | −0.40798 | +0.01662 | 5/8 | +0.06138 | 5/8 | 0.4517 | +0.037 |
| US30_cash | 6,406 | −0.07059 | +0.01407 | 5/8 | +0.02115 | 3/8 | 0.0827 | +0.170 |
| EURJPY | 5,029 | −0.30476 | +0.01282 | 4/8 | +0.05388 | 5/8 | 0.3532 | +0.036 |
| … 14 others … | | | | | | | | |
| NAS100 | 6,908 | −0.07579 | −0.02051 | 2/8 | +0.01379 | 4/8 | 0.0853 | −0.241 |
| AUDJPY | 5,199 | −0.37125 | −0.02628 | 2/8 | −0.01964 | 2/8 | 0.3960 | −0.066 |
| EURUSD | 5,066 | −0.22051 | −0.04115 | 2/8 | +0.03180 | 5/8 | 0.2315 | −0.178 |

**16 of 24 instruments positive at R1, 16 of 24 at R4 — but not the same 16** (XAGUSD is
2nd-best at R1 and negative at R4; EURUSD is worst at R1 and positive at R4). **The largest
|sig/toll| over all 24 is 0.241.** That is the shape of noise partitioned 24 ways, not of a
subset carrying an edge.

**Consistency check on the whole thing: at R1 the book is net-positive on 2 of 172 trading
days.**

---

## 8. WHAT WOULD HAVE TO BE TRUE FOR THIS FAMILY TO WORK

The owner ruled out "it is finished" without a reason. Here is the reason, as conditions with
the numbers each would have to hit.

1. **The direction call would have to become right.** It is currently right **0.297 pp less
   often than a coin flip** (0.39960 vs 0.40257). The gap to breakeven is
   `toll − gross = 0.32954 − 0.02328 = 0.30626 R/trade`; at the shipped 2R/1R geometry each
   converted trade moves −1 R → +2 R, so **10.21 % of the entire book would have to convert
   from a stop into a target**, taking the win rate from **0.39960 to 0.50169** — a **+10.21
   percentage-point** move. Nothing measured in three swarms and 46 agents moves a win rate by
   ten points.
   *(Recomputed on the correct population as the brief requires. The estate's published "needs
   45.94 %, gets 34.68 %" was computed on the 27,658-row counterfactual pool against a target
   the generator does not emit; both halves were wrong. On the roster, at the shipped
   downstream 2.0R geometry and the measured toll: **needs 50.17 %, gets 39.96 %**. The pooled
   shipped-contract exit mix over 141,230 priced trades is **stop 49.11 %, target 21.94 %,
   horizon truncation 28.96 %**.)*
2. **Or the toll would have to fall 6×, and it cannot help.** The toll is **3.0577 bps**,
   stable to ±3.1 % over eight months — a fee schedule. One R averages **21.920 bps**, so the
   toll eats **13.95 % of risk per trade**. For the measured gross of +0.02328 R to cover it,
   one R would have to be **≥ 131.37 bps — 5.99× the current ATR-derived stop**. **But R scales
   as 1/d**: a 5.99× wider stop divides the gross-in-R by 5.99 and leaves the ratio exactly
   where it was. **Widening the stop cannot work, and this is the arithmetic reason the toll
   is not the lever.**
3. **Or a conditioning variable would have to exist that separates the pool.** This lane did
   not test conditioning — but it bounds it hard: **any conditioner has to find at least
   +0.330 R/trade of directional content inside a population whose total measured directional
   content is +0.003 ± 0.010.** A subset can only carry more than the whole if another subset
   carries less, so a viable conditioner must be near-perfect on a very small slice. The two
   natural first cuts — 24 instruments and 7 families — top out at **27 % of toll on 5.8 % of
   the population**, with signs that disagree between rungs.
4. **What is NOT required, and this is the load-bearing negative.** No downstream engineering
   fixes this. A perfect exit, a perfect entry instant, a perfect ranker and unlimited capacity
   were **granted simultaneously** and left the signal-attributable book at +0.029 R/trade
   against a 0.330 R/trade toll. **Every remaining repair to gating, ordering, exits, entry
   timing, sizing or scheduling is bounded above by a number 11.5× too small.**

---

## 9. LIMITS OF THIS RESULT — read before citing it

1. **Scope is the at-market cohort of the broad V4 origin generator**, eight months, one
   broker's cost schedule (FTMO). It says nothing about the live W7 sleeve book, which is a
   separate system on separate evidence.
2. **The POI families are excluded** (`current_fvg_fill`, `current_ob_retest`,
   `current_breaker_re_entry` — 87 % of raw emissions). They are resting-limit orders the live
   engine cannot place, and PB measured them at 83.0 % no-fill and −0.0473 net R/trade. They
   are not rescued by this lane and were not tested by it.
3. **Horizon is 120 M1 bars**, the sealed sidecar's own convention; 28.96 % of shipped-contract
   exits are horizon truncations. A longer horizon raises every oracle rung — and raises the
   placebo by the same amount, since the oracle's value *is* path volatility. The R1 baseline
   is unaffected in the 71 % of trades that resolve.
4. **PLACEBO-SIDE inherits the signal's instants and risk distances**, so `real − PLACEBO-SIDE`
   is strictly the **directional** content. PLACEBO-TIME covers the rest — random instant on
   the same day, random side — and agrees: pooled R1 signal vs PLACEBO-TIME is **−0.00149**,
   vs **+0.03902** at R3b and **+0.04956** at R4b, all inside the noise band. **So neither the
   direction call nor the choice of *when* to fire carries measurable information.** A claim
   that the family's value lies in some *third* channel — position sizing, correlation,
   portfolio construction — is not tested here.
5. **The cost model is the current measured schedule applied to Oct–Dec 2025 as well.** The
   toll is flat to ±3.1 % across all eight months, which is evidence the schedule is stable,
   not proof it was identical in 2025.
6. **The three sealed months (Jun/Aug/Sep 2025) were not opened**, not generated, and not read.
7. **`risk.min_rr` correction applied.** The generator emits at 1.5R (verified on the roster:
   `|tp − e| / |e − sl| = 1.5000`); the shipped downstream `momentum_exhaustion` geometry
   targets 2.0R, which is what R0/R1 price and what PB's baseline uses. The oracle exit menu
   spans 1.0R … 5.0R plus three time stops, a breakeven runner, a 1R trail and pure hold, so
   the target choice is not load-bearing from R3 upward.
8. **PLACEBO-TIME draws instants uniformly on the 96-window grid**, so it can land in hours the
   generator never fires in; its toll therefore differs slightly from the real arm's. That is
   why PLACEBO-SIDE, which is exactly toll-matched, carries the headline and PLACEBO-TIME is
   the corroborating control.

---

## 10. REPRODUCTION

```bash
cd docs/audits/fable5-vision-audit-20260725/phase19/receipts

# rosters for the five months that had none (close-only; ~9 min/month on 5 cores)
python3 pbg/pbg_run.py --month 202510 --min-rr 1.5 --workers 5 --out /tmp/f2_close_202510

# the ladder + both placebos + the cost-cap sweep (~4 min/month)
python3 discovery/f2_run.py --in /tmp/f2_close_202510 --month 202510 \
        --out discovery/f2/F2_LADDER_202510_V1.json

# the detection floor
python3 discovery/f2_power.py --in /tmp/pbg_full_jan --month 202601 \
        --out discovery/f2/F2_POWER_202601_V1.json

# pool everything
python3 discovery/f2_pool.py
```
