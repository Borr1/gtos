# Is it the sleeves, or the way we're using them?

**For Borhen. 2026-08-06. Phase 19 broad-forensic wave: 46 agents across three swarms, plus
thirteen measurement lanes on the corrected population — 1,118,694 candidates over eight open
months, and 470,472 more over three months that had never been opened by anybody.**

You asked two questions. Both are answered in the next ten lines, with numbers. Everything after
that is the working, in tables, so you can check it yourself.

---

## THE ANSWER, IN TEN LINES

1. **It is the sleeves — but not because they are wrong. Because they are too small, and because
   they do not grow.**
2. The setups carry a **real** edge. On three months nobody had ever opened: **+0.0272 R per trade
   gross**, p = 0.001, positive in all three. It is not noise and it is not zero.
3. The broker charges **0.3426 R per trade** on those same trades. That is **12.6× the entire edge**.
   In price terms — the unit that cannot be gamed — we capture **0.0119 basis points** and pay
   **3.0159**. A **253× shortfall**.
4. **The way we use them is not the problem, and this was measured three separate ways.** Our stack
   already **adds** +0.0667 R/trade over a matched control. Every downstream layer measures at
   roughly **84 % of its own best possible version**.
5. Give it a **perfect exit, a perfect entry instant, a perfect ranker and unlimited size all at
   once** and it books **+2.339 R/trade**. A **coin flip on exactly the same trades books +2.311**.
   98.8 % of that perfection is market noise available to anybody holding that instrument.
6. **The mechanism — this is the answer to "there must be a reason".** A working sleeve's edge
   **compounds with holding time**. Ours go from 3.41 bps at 2 hours to **128.04 bps at 320 hours —
   a 37.58× increase**. The broad family goes 0.2008 → 0.1938. **0.97×. It is no more right after
   two weeks than after two hours.**
7. That is why a **9.3 bps stop can never outrun a 3.0 bps spread**: we hand a third of the risk
   unit to the broker at the door, and the trade never becomes more right to earn it back.
8. **Where we go:** (a) nothing changes on either funded account — this touches none of your armed
   sleeves; (b) fix two free defects in the generator (one family is born past its own stop 68 % of
   the time; the pullback gate is written in *percent of price* while the trade is written in *R*);
   (c) fix the measurement — our bar archive is **bid-only**, and we have been scoring ourselves
   **0.0696 R/trade too generously**, which is **2.4× larger than the edge we are arguing about**.
9. **Then exactly one experiment is left, and it has never been run.** Every version we measured
   fires every 15 minutes and dies in 2 hours. **12.5 years of 4-hour and daily bars for exactly
   these 24 instruments sit on this machine, 27 MB, referenced by zero of 607 files.** The slow grid
   is the only untested form of "the setups are fine, the contract is wrong."
10. **If that fails, the family is finished and the reason is named:** its setups do not accumulate,
    so no stop width, no exit contract, no entry timing, no filter and no broker on earth makes
    0.2 beat 3.0. Every one of those four escape routes is priced in §6 and every one is closed.

---

## READ THIS FIRST — what was examined, and what was NOT

**What was examined.** The **broad V4 research family** — ten setup generators firing on 24
instruments, deciding at every 15-minute close, with a stop set from recent range and a 1.5 R
target. It has **never traded live**. Eleven months of it, candidate by candidate.

**What was NOT examined.** Your live book. `crypto`, `energy_agri`, `sub_xvol_pullback`,
`sub_mid_dn_revert` on both accounts, plus `mx_btcusd_d1_donchian_20_breakout` on FTMO. That is a
**different family with a different shape**: median stop 44–436 bps against the broad family's 9.7,
and a 320-hour horizon against 2 hours — **160× longer**. **No live P&L was read. Nothing in this
report is a reason to touch either armed account.** The live sleeves appear twice, both times as a
*control* — a known-working thing to measure the broad family against.

**Vocabulary, once each.**

| Term | Meaning here |
|---|---|
| **R** | One risk unit. If the stop is 40 points away, 1 R = 40 points. "+2 R" = made twice what it risked. All per-trade numbers are in R unless marked bps. |
| **bps** | Basis point = 0.01 % of the instrument's price. Used whenever R would mislead — see the box in §2. |
| **Gross** | Before broker costs. The raw price move. |
| **Net** | After spread + commission + slippage + swap. |
| **The toll** | Total broker cost per trade. Same thing as "cost". |
| **Emission / candidate** | One setup the generator produced. Most never become trades. |
| **Fill-honest** | The trade only counts if the market actually traded the entry price. |
| **The roster** | The **correct** population: every candidate the sealed replay arms actually produced. 1,167,100 of them over eight months. |
| **The pool** | The old 27,658-row object every published number used. It is the wrong object — see Correction 1. |
| **Placebo / coin flip** | The identical trades, identical instants, identical stops and identical costs, with the **direction picked at random**. If our result equals the coin flip's, our direction call is worth nothing. |
| **p** | Probability the result is luck. 0.001 = one in a thousand. |
| **Out of sample** | Measured on months that did not choose the rule. |

---

## 1. THE THREE CORRECTIONS — numbers you have already been given that were wrong

### Correction 1 — the object everyone analysed was the set of trades we did NOT take

Every broad-family number in this estate for months was computed on a 27,658-row "pool". That pool
is **18.03 % of what the generator produced and is 100 % counterfactual** — by construction it is
the *missed-opportunity ledger*, the trades the system considered and declined.

Worse, its admission test conditions on **what price did after the decision**
(`v4_timewarp…:28130-28140`). Measured by joining it row-by-row to the roster:

| | in the pool | not in the pool |
|---|---:|---:|
| rows | 208,852 (17.9 %) | 958,248 (82.1 %) |
| fill rate | **99.43 %** | **14.29 %** |
| born already past its own stop | **10.57 %** | **0.15 %** |
| gross R/trade | −0.18246 | +0.01004 |

That is a **7.0× enrichment in fill rate and a 70× enrichment in structurally dead rows**, selected
on the future. Findings *about the decline gate* are correctly measured there. Anything generalised
from it to "the system's trades" was invalid.

**The correct object exists and this wave rebuilt it**: the sealed arms' own candidate rosters,
reproduced at **99.82 % on a 10-decimal geometry hash**. Every number in this report is on that.

### Correction 2 — the target is 1.5 R, not 2.0 R, and the famous "11-point hole" was blamed on the wrong thing

You were told: *"the book needs a 45.94 % win rate and gets 34.68 %"* — an 11.3-point hole, presented
as evidence the setups don't work. That was computed against a target the system does not use, on
the wrong object. Recomputed correctly:

| basis | win rate | breakeven needed | gap |
|---|---:|---:|---:|
| published (wrong object, wrong target) | 34.68 % | 45.94 % | **−11.26 pp** |
| correct object, **gross** (before the broker) | 37.98 % | 38.55 % | **−0.57 pp** |
| correct object, **net** (after the broker) | 37.98 % | 50.58 % | **−12.60 pp** |
| **the 464 trades the system actually took, gross** | **47.20 %** | 44.13 % | **+3.07 pp** |

**The headline number was roughly right. The reason you were given for it was wrong.** It was never
that the setups lose. Before costs they are within **half a percentage point** of break-even, and the
trades we actually selected were **three points better** than break-even. **The eleven points is the
broker, and only the broker.**

### Correction 3 — three headlines were built and killed this week. Each has a mechanism.

| headline you were shown | what killed it |
|---|---|
| "+0.038342 R/trade gross-positive on **24 of 24 instruments**" | Its 0.25 R trailing stop manufactured **+0.084014 R/trade of bar-resolution premium** — **2.19× the entire headline**. A tight trail read on 1-minute bars books exits at prices that never printed. |
| "cells where the edge beats the broker toll" | **Died out of sample.** A book reading +0.076498 booked **−0.044700** on two unseen months: its **gross collapsed 97 % while its toll moved 2.8 %**. Ranked by instrument, cost order travels between months at **+0.826** and edge order at **+0.024** (the same test over 27 ways of cutting the population gives **+0.9005** and **+0.0230** — see §3). Selecting on affordability re-discovers the fee schedule. |
| "decide on the forming bar, don't wait for the 15-minute close" — the wave's last survivor | **Failed its sealed test on September 2025**: implementable book **−0.30551** against the incumbent's **−0.28041**. Mechanism: a setup that fires inside a bar and does *not* survive to that bar's close has **already lost −0.55503 R by the time the close arrives — 98.0 % of its entire loss**. You cannot cancel out of it, because the damage is done before the information arrives. |

---

## 2. WHAT WAS FOUND

### FIND 1 — The setups carry a real edge, and it replicates on months nobody had opened

Three windows were sealed all year — **June, August and September 2025, 470,472 candidates** — and
opened once, on a hypothesis written down and committed *before* the seal was broken.

| window | fills | gross R/trade | toll | net |
|---|---:|---:|---:|---:|
| June 2025 | 22,494 | **+0.04024** | | −0.24127 |
| August 2025 | 36,403 | **+0.02501** | | −0.32224 |
| September 2025 | 38,905 | **+0.02166** | | −0.35198 |
| **pooled** | **97,802** | **+0.02718** | **0.34262** | **−0.31545** |

95 % interval [+0.01096, +0.04293], **p(≤0) = 0.001**, positive in 3 of 3. Win rate 39.34 % against a
**gross** breakeven of 38.19 % — **1.15 points to the good** — and a **net** breakeven of 52.66 %.

**This is the strongest positive statement anywhere in the wave, and it is the one to hold on to:
the setups are not noise.** They are simply 12.6× too small to pay for themselves.

### FIND 2 — The toll is a pure function of our own stop width, and no threshold anywhere escapes it

Split the whole population into ten buckets by how tight the stop is:

| stop width (bps) | gross R/trade | broker toll | net |
|---|---:|---:|---:|
| 0.32 – 2.89 | **+0.00745** | **0.72996** | −0.72251 |
| 15.97 – 23.27 | −0.00532 | 0.22217 | −0.22749 |
| 41.56 + | −0.04069 | **0.09818** | **−0.13887** (best) |

**The toll falls 7.4× across the deciles. The gross never leaves a ±0.04 band and has no trend.**
The tightest decile hands **73.0 % of its risk unit** to the broker before the trade starts. The
best net cell is still −0.139, and every step along the curve moves the same way — there is no
sweet spot in the middle to aim at.

> **Why we stop quoting R and start quoting bps here.** R divides the price move by our own stop, so
> a tight stop makes every number look bigger — both the edge *and* the cost. In price terms the
> toll disperses only **1.6× across families** while in R it disperses **11.5×**. The "expensive
> instruments" story was mostly our own stop widths. The cheapest family in R pays a *higher* price
> toll than the most expensive one.

### FIND 3 — The way we are using them is not the problem. Measured three independent ways.

**(a) Against a matched control.** Take the 507 trades the system actually executed, and compare
each to trades in the same window, same instrument, same stop width (±25 %), that it declined:

| comparison | n | our advantage | 95 % interval | p |
|---|---:|---:|---|---:|
| vs the trades it declined | 396 | **+0.14961** | [+0.03964, +0.26157] | 0.0027 |
| vs a random roster draw | 397 | +0.08800 | [−0.02279, +0.20079] | 0.060 |
| vs a clean roster draw | 397 | **+0.06667** | [−0.04363, +0.17962] | 0.123 |

Selection **adds** ~+0.045 gross; trade management **adds** a further ~+0.023. The stack is not
destroying a good signal — **it is the reason the number is near zero instead of well below it.**

**(b) Layer by layer against each layer's own perfect version.** Capture of the theoretical ceiling:
gate **16.75 %**, ranking **10.81 %**, exit **−0.44 %**, entry timing **0 %** (no such layer exists),
sizing undefined (it is a constant — every one of the 507 trades carried risk 0.1 %). But of each
layer's headroom, the share **reachable from anything observable before the decision** is: gate
3.88 %, exit 2.32 %, timing 2.80 %, **ranking 12.80 %**. Everything else is hindsight.

**(c) The oracle ladder, with a coin-flip control.** This is the decisive one.

| what we grant it | net R/trade | a coin flip on the same rows | our share |
|---|---:|---:|---:|
| shipped stack | −0.29226 | −0.29447 | +0.00221 |
| + perfect exit | +1.71862 | +1.69333 | +0.02529 |
| + perfect entry instant too | **+2.33914** | **+2.31133** | **+0.02781** |

**Every rung is 98–105 % reproduced by a coin flip.** Perfect exits are worth ~+1.95 R/trade *to
anybody* trading that instrument. That is why "work on exits" is not a prescription this evidence
supports — and it is the general form of the trailing-stop headline that died this week.

### FIND 4 — THE MECHANISM: a working sleeve's edge compounds. This one does not.

Same walker, same coin-flip control, same units, on both populations:

| holding time | **live sleeves** (bps of price captured) | **broad family** (bps) |
|---|---:|---:|
| 2 hours | 3.41 | 0.2008 |
| 8 hours | 32.96 | 0.2051 |
| 24 hours | 38.41 | 0.2077 |
| 72 hours | 100.01 | 0.1943 |
| 160 hours | 103.98 | 0.1904 |
| 320 hours | **128.04** | **0.1938** |
| **growth, 2 h → 320 h** | **37.58×** | **0.97×** |
| median stop | 215.4 bps | **9.7 bps** |
| toll at 320 h | 29.23 bps | 3.19 bps |
| **edge ÷ toll at 320 h** | **4.38** | **0.06** |

**This is the answer to "there must be a reason it's finished."** A real setup is a statement about
where price is going, and the further price goes, the more right you are. Our broad setups are right
about the next couple of hours by a fifth of a basis point and **stop getting more right**. There is
nothing to hold *for*. So the only way to profit is to trade a stop so tight that the edge is a large
fraction of it — and at that stop the spread is a **larger** fraction still.

**It was tested the other way round too, exhaustively.** Six stop widths × six horizons × five
targets × the live sleeves' own scale-out shape, plus 90 volatility-matched cells = **282 live-
sleeve-shaped contracts transplanted onto the broad family. Zero net-positive.** Best cell −0.00698,
positive in 0 of 8 months. And the closer the contract gets to a live sleeve's, the **worse** the
direction call: at 400 bps / 4 R / 320 h — crypto's shape — it is **significantly worse than a coin
flip** (−0.01504, p 0.995).

Reversed: put a live sleeve on the broad family's contract and it goes **+0.6970 → −0.9585 R/trade**.
68.7 % of its trades are stopped inside two hours by a 9.28 bps stop.

### FIND 5 — Three defects. Two are free to fix. One family causes 74 % of the published loss.

| defect | what it is | size |
|---|---|---|
| **`current_breaker_re_entry` is born past its stop** | It emits candidates whose stop the market has **already breached** at the decision instant. Those fill 100 % of the time — they are marketable by construction — and book a mechanical −0.998 R. | 68.0 % of the family's fills. It is 9.85 % of all fills and **74 % of the entire published negativity**. Removing it moves the roster gross **−0.0823 → −0.0180**. |
| **The pullback gate is written in the wrong unit** | The three "wait for a pullback to a level" families are admitted by a distance test denominated in **percent of price** (1.0 %) while the trade they then build is denominated in **R**, with a median risk of 7.4–8.9 bps. | That is an **11.2–13.5 R admission radius on a 1.5 R trade**. Result: **84–92 % of these candidates are already behind their own target when they are born**, and 25.7 % of the breaker family is already past its own stop, fills 100 %, and books **−1.304 R net each**. |
| **Stale-bar entries** | The decision walks back to the last closed bar with **no maximum-age check**, so across a weekend or a session gap it prices the entry off a bar that closed hours ago. | 3.35 % of at-market entries. Median displacement to the next real print: **2.42 R**. 67 % are displaced by more than a full R. |

**And the honest half.** Repair the unit defect and the surviving, correctly-formed limit book is
69,233 fills at gross **−0.01065** against a **0.23916** toll. **The repairs fix the books, not the
economics.** They are still worth doing, because every future number computed on this generator is
wrong until they are, and because this exact defect class — scoring fills that could not happen —
produced three dead headlines in one week.

### FIND 6 — Our own measurement is biased, and the bias is bigger than the thing we are measuring

Settled where nobody had looked: the bar archive and the tick archive overlap by 37 days.

- **The bars are BID on open, high, low and close.** 76,734 M15 bars × 29 symbols: bar close equals
  the last tick bid **100.00 % of the time**; `(close − mid) / spread = −0.500000` exactly, in all 29.
  Confirmed again on the M1 packs the lanes actually walk (223,239 bars, 99.99 %).
- **Every walker resolves stops and targets against them with unshifted levels.** But a long buys the
  ask and sells the bid: its true stop is one spread *nearer* than we score it and its true target one
  spread *further*.
- **Measured bias at the shipped horizon: −0.0696 R/trade, with a constant sign.**

That is **5.2× f1's entire measured gross deficit** and **2.4× the entire signal being arbitrated**.
Walked directly on bid/ask ticks for four instruments over two months, the bar walk's optimism
measures **−0.02501** (January) and **−0.03693** (April) per opportunity — of which **89 %** is the
side of the book, not intra-bar ordering.

**Consequence you should hold on to: any "usage" lever worth less than 0.07 R/trade is currently
unfalsifiable.** That covers the exit swap (+0.035), the entry offset (+0.016), and every
selection rule anybody has proposed.

### FIND 7 — The one thing that got BIGGER, and it says the machinery is fine

On **exactly the eight windows** where the broad family books ≈ 0, our *other* generator — the live
sleeve family — books:

| population | n trades | R/trade | 95 % interval | p(≤0) |
|---|---:|---:|---|---:|
| all sleeve trades in-window | 4,352 | **+0.15555** | [+0.09191, +0.22088] | 0.000 |
| the five armed sleeves only | 138 | **+1.24084** | [+0.73792, +1.69053] | 0.000 |

Different instruments, different contracts, and a research walk rather than live P&L — so this is
**not** a like-for-like economic comparison and must not be quoted as one. But it settles one thing:
**the generator, the walker and the cost model are not broken. The broad family's contract is.**

A related fact worth knowing: **24.9 % of live-sleeve trades sit on 18 instruments the broad family
has never emitted a single candidate on.** The two systems are not even looking at the same market.

---

## 3. WE LOOKED EVERYWHERE. HERE IS WHERE.

You said: *"if we know where to look we must look."* This is the search, priced.

| what was swept | cells / arms / rules | positive books |
|---|---:|---:|
| out-of-sample cell-selection arms (6 partitions × 3 axes × 3 shares × 2 protocols × 3 populations) | 324 | **0** |
| live-sleeve-shaped contract transplants (stop × horizon × target × exit policy, flat and volatility-matched) | 282 | **0** |
| cohort × horizon looks, each priced against its own toll | 954 | **0** hold the sign in every window |
| fixed exit contracts (loser cut × target) | 56 | **0** with positive signal |
| forming-bar separator rules (single + pair thresholds) | 1,414 | **0** train-positive, **0** test-positive |
| ex-ante selection rules at 11 selection rates, fitted then run forward | 66 | **0** |
| family subsets, implementable | 127 | **0** |
| broker cost caps, 42× sweep | 11 | **0** |
| **total** | **3,234** | **0** |

**And the detection floor is measured, so "nothing found" is a result and not an absence.** Injecting
a known directional edge into the same rows recovers it linearly across three decades of size, in
four separate months — January resolves an effect where only **1.03 % of rows change side**
(p = 0.0235). **The test can see an effect 32× smaller than the level the family needs, and it sees
nothing.**

**The one ordering that survived, and it is not the fee schedule.** Rank every cell — instrument,
family, hour — by cost in one month, then check whether the same ranking holds in the next month.
A score of +1.00 means the order is identical; 0.00 means this month's ranking tells you nothing
about next month's. Across 27 ways of cutting the population the **broker toll's** ranking travels
at a median of **+0.9005**; the **edge's** at **+0.0230**. In price units the toll travels at **+0.9936** —
it *is* the fee schedule. Only one thing in the entire wave orders on edge and travels: **the exit
contract** (+0.6399 on gross, zero cost content). Swapping the shipped 2 R target for
`stop_only_horizon` is worth **+0.03472 R/trade, positive in 8 of 8 months**. Out of sample it
shrank to **+0.01002** and lost significance — and it is below the walker-bias floor from Find 6.

---

## 4. THE LEVERS, PRICED TOGETHER — never add them up

| lever | worth **alone** | what it really is |
|---|---:|---|
| the shipped cost gate | **+0.21648** | Real — but it works by **trading 78 % less**, and it makes the direction call slightly *worse*. Under a perfect exit it turns **harmful (−0.36933)**. It is a toll filter, not a selector. |
| swap the exit contract | +0.03500 | The only edge-ordering that travels. Shrinks to +0.01002 out of sample. Below the measurement floor. |
| enter 5 minutes after the close instead of at it | +0.01626 | **81.6 % fee schedule.** Its gross component is +0.00299 and flips sign in 3 of 8 months. |
| best of 56 exit contracts | +0.11610 gross | **A coin flip on the same rows gets 108.5 % of it.** |
| rank the candidates better | +0.09714 | **87.2 % unreachable** from anything observable before the decision. A 38-feature model out of sample books −0.00009. |
| **all four, priced jointly on the same rows, out of sample** | **+0.00553** | against a **+0.29226** gap to breakeven. **A factor of 52.9.** |

**The double-count factor is 21.9×** — the worst ever recorded here. Six levers worth +1.266 R alone
delivered +0.421 together. **Never sum standalone lever values. Price them jointly, on the same rows,
always.**

---

## 5. THE WHOLE FAMILY, END TO END, ON THE CORRECT OBJECT

Eight open months, October 2025 – May 2026:

| stage | n | gross R/trade | toll | net |
|---|---:|---:|---:|---:|
| every candidate emitted | 1,118,694 | −0.02440 | 0.08318 | −0.10758 |
| …those that actually filled | 331,548 | −0.08233 | 0.28066 | −0.36299 |
| …after removing the broken family and trades born past their stop | 298,537 | **−0.01327** | **0.28118** | −0.29445 |
| …**the 464 trades the system actually took and scored** | 464 | **+0.05505** | 0.07437 | **−0.01932** |

Read the last row carefully. **The trades we actually took are roughly break-even, not a
catastrophe** — net −0.01932 R/trade, which at your 0.1 % risk unit is **−0.896 % of account over
eight months**. The published −0.2175 disaster figure was the engine's own counterfactual proxy on
the wrong object. Three different numbers exist for the same 27,658 rows, spanning 0.28 R.

**But that book cannot be adjudicated by running it.** Its deficit (0.01932) is **2.5× smaller than
its own standard error** (0.04789). To measure whether it is above or below zero would take
**10,951 trades = 14.4 years** at its measured rate. Any argument for keeping it live has to rest on
something other than the expectation of learning from it.

---

## 6. WHAT WOULD HAVE TO BE TRUE — every escape route, closed

| route | what it would take | what is measured |
|---|---|---|
| **Win more often** | +10.21 to +12.60 percentage points | The gross gap is **−0.57 pp**. To close it, 10 % of the whole book must convert a −1 R stop into a +2 R target. |
| **Pay the broker less** | The toll must fall to the gross. The gross is **negative**. | A **104.72 % cost reduction** is required. **A free broker is not enough** — at zero cost the book is still at its gross. This closes the entire cost-engineering axis: broker selection, spread timing, slippage, execution venue. |
| **Use a wider stop** | 5.99× wider (≥131 bps) | At 400 bps the direction call is **significantly worse than a coin flip** (p 0.995). Widening does not reveal a hidden edge; it removes the only regime the edge lives in. |
| **Hold longer** | The signal must accumulate **21.4×** | Measured accumulation: **0.97×**. |
| **Cut losers smaller** | Mean loser from 0.9011 R to 0.4263 R (−52.7 %) | Algebraically this is the one lever that closes the gap. On real paths a stop tight enough to do it **kills 37.6 % of the winners**, and 85.2 % of losers are already at exactly −1 R. |
| **Select better cells** | Any partition that travels | **324 arms, 0 positive books.** Median 97.7 % of every improvement is toll removed, not edge added. Even with **perfect foreknowledge** of each cell's true edge and zero estimation error, keeping the best 10 % buys +0.025 R against a 0.308 toll — **12.1× short**. |

---

## 7. WHAT IS THIN — stated plainly, not buried

1. **The +0.0272 sealed gross is measured with a walker we now know is optimistic by 0.024–0.070
   R/trade.** Corrected, the family's true gross is **zero or slightly negative**. The honest reading
   is: *at the fidelity we can currently measure, the broad family's gross is indistinguishable from
   zero.* Find 1's "the setups are real" survives in *sign* and is fragile in *level*.
2. **The lanes disagree on the sign of the direction call, and all three are small.** On the sealed
   months it beats its mirror by **+0.02391** (3/3 windows). On an exactly-paired mirror over eight
   windows it is **−0.00096** (a null). On the fill-lag-zero cohort one lane read **−0.04230**.
   The truthful statement is: **the direction call is somewhere between slightly positive and
   slightly negative, and it is certainly tiny.**
3. **`structural_distance_extreme` — the one family that looked genuinely real — is unresolved.**
   Gross-positive in **15 consecutive windows across three independently written harnesses**
   (+0.06639 over eight open months, **+0.12522** over three sealed ones). But its edge lives
   entirely in its two tightest stop quintiles (median 1.3–2.1 bps), which is exactly where the
   spread correction bites hardest — and under MT5-true trigger sides it reads **−0.13028**. That
   correction was measured on **4 instruments over 2 months** of tick data, not on this family
   directly. **It needs one tick re-walk to settle, and it is the single most interesting unsettled
   thing in the estate.**
4. **The live-sleeve control is in-sample and small** (n = 134 in one lane, 4,352 in the other), and
   all five sleeves reject at the ratified admission gate. It supports "the machinery works",
   not "the sleeves are proven."
5. **The held-out set is spent.** June, August and September 2025 were opened once, on a
   pre-declared hypothesis, and are recorded as spent in three places. **There is no untouched month
   left for this family in 2025–2026.** The next honest out-of-sample test has to come from a
   different era — which is exactly what §8 item 4 proposes.

---

## 8. WHERE WE GO FROM HERE — ordered, with what each is worth and what it costs

### 0. Change nothing on either funded account. Cost: zero.

Everything above measures a 2-hour, 9-bps-stop research family that has never traded live. Your armed
sleeves are a 320-hour, 200–436-bps contract on partly different instruments. **Nothing here
transfers, in either direction.** Find 7 is the only place the two meet and it is a control, not a
recommendation.

### 1. Fix the measurement. Worth: makes every sub-0.07 R finding falsifiable. Cost: ~1 hour of compute.

Re-walk the eight windows with spread-shifted triggers — stop at (d − s), target at (T·d + s) — on
machinery that already exists. Today the **−0.0696 R/trade** bar-vs-tick bias is a *bound*; this
converts it into a *book*. Until it is done, the exit swap (+0.035), the entry offset (+0.016) and
every selection rule in the estate are inside the error bar of their own measurement.

**Do this first.** It is the cheapest item on the list and it decides whether items 3 and 4 are even
readable.

### 2. Fix the two generator defects. Worth: removes 74 % of the family's published loss and unblocks every future number. Cost: ~1 session.

One predicate, three call sites, behind an absent-false key so nothing sealed moves:

- refuse any candidate whose stop is already breached at the decision instant;
- re-denominate the pullback admission test in **R** instead of percent of price (require the
  distance-to-fill to be less than the target in R).

**Be clear about what this does not buy.** The repaired book is still gross −0.011 against a 0.239
toll. This is bookkeeping hygiene with real teeth: it makes the generator's output honest, and three
of this week's four dead headlines were this defect class.

### 3. Settle `structural_distance_extreme` on ticks. Worth: it is the estate's last live economic candidate. Cost: ~half a session.

15 consecutive positive windows across three harnesses is the strongest replication anywhere here.
The quote-side correction that appears to kill it was measured on four other instruments. **Walk
this family's own trades on bid/ask ticks and get a number.** If it survives, it is the only
broad-family cell worth another hour. If it dies, it dies with a mechanism — its edge lived where
the spread is largest — and that is a clean close.

### 4. The one experiment that has never been run: the slow grid. Worth: the only untested form of "the setups are fine, the contract is wrong." Cost: ~1 session, no arms, no seal break, no VPS.

Everything measured this wave fires at 15-minute closes and dies in two hours. We transplanted the
live sleeves' **contract** onto the broad family's **instants** — 282 cells, zero positive. We have
**never** built the same setup logic on a slow structural grid.

**The data is here and has never been opened**: `deep_universe_h4d1_2014_2026` — 48 files, **exactly
the broad family's own 24 instruments**, H4 + D1, 2014-01-02 → 2026-06-15, **439,895 bars, 12.5
years, 27 MB** — sitting in the same folder every lane loads its minute bars from, with **zero
references across all 607 discovery files.**

**Declare the pass condition before running it**, and it should be about accumulation, not level:
the same setup logic emitted at H4/D1 closes with volatility-scaled stops must show a signal that
**grows at least 3× from its shortest to its longest horizon** and clears its own toll on held-out
years. That is the property that separates a working sleeve from this family, and it is the only
property nobody has ever selected on.

It also buys something we currently lack: a **base rate**. The 37.58× accumulation figure for a
working sleeve has no null. Twelve and a half years across 24 instruments gives it one.

### 5. If item 4 fails, close the family — and here is the sentence to close it with.

> *The broad V4 family's setups pick a direction that is right by about a fifth of a basis point over
> the next two hours, and never becomes more right no matter how long you hold it. The broker charges
> three basis points. Its win rate is within half a point of break-even before costs and twelve
> points short after them. A free broker is not enough, because the required toll is negative. A
> wider stop makes the direction call worse than a coin flip. And 3,234 configurations were priced
> across eight independent lanes without producing a single positive book.*

That is a mechanism, a measurement, and a falsifier — not "it doesn't work."

### 6. Separately, and this is where I would spend the session after: the generator that DOES accumulate.

On the identical eight windows the live-sleeve family books **+0.15555 R/trade** on 4,352 trades with
the interval clear of zero, and the armed five book **+1.24084** on 138. That is a research walk on a
different instrument set, so treat the level with suspicion — but the **contrast** is the most
informative single number in this report. **The estate's problem was never that it cannot build a
signal. It is that it spent eleven months measuring the one family whose signal has no time to
work in.**

---

## SOURCES

Every number above is from a committed receipt under
`docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/`. The load-bearing ones,
re-read from the JSON artifacts while writing this:

| claim | artifact |
|---|---|
| roster baseline (−0.01327 / 0.28118 / −0.29445 on 298,537) | `f1_BASELINE_V1.json → roster.roster_pooled.filled_clean` |
| oracle ladder + coin flip (+2.33914 vs +2.31133) | `f2/F2_POOLED_V1.json → LADDER_TABLE_TRACK_B`, `PAIRED_SIGNAL_POOLED` |
| accumulation curve (37.58× vs 0.97×) | `d3/D3_CURVE.json` |
| 282 transplants, 0 positive | `d3/D3_ANALYSIS.json`, `d3/D3_ATR_POOLED.json` |
| POI percent-vs-R gate, born-past-stop economics | `d4_out/POI_8MO.json`, `POIECON_POOLED.json` |
| layer capture, gate ledger, sizing constant | `D2_POOLED_V1.json`, `D2_GATE_ROSTER_V1.json`, `D2_STACK_V1.json` |
| forming-bar mechanism (−0.55503 at the close) | `D6_CANCEL_V1.json`, `D6_FINAL_V1.json` |
| cost lever infeasible (required toll −0.01327) | `d7/D7_STAGE1.json → cohorts.CLEAN.levers.L4_cost` |
| bid archive + −0.0696 bound | `D8X_QUOTESIDE_V1.json`, `D8X_GEOM_V1.json → touch_rates` |
| live-sleeve control (+0.15555 / +1.24084) | `D8X_CROSS_V1.json → ALL`, `armed_only` |
| persistence (+0.9005 cost vs +0.0230 edge), 324 arms | `P1_MATRIX_V1.json`, `P1_OOS_V1.json`, `P1_TOLLNEUTRAL_V1.json` |
| sealed three months (+0.02718, p 0.001) | `P2_SEALED_V1.json → H1_signal_is_zero` |
| forming bar fails sealed (−0.30551 vs −0.28041) | `P2_SEALED_SEP_H5.json → b_implementable` |
| tick truth (−0.02501 Jan, −0.03693 Apr) | `p3_RESULT.json → TICK.POOLED_202601/202604` |
| never-opened 12.5-year archive | `d8x_RESULT.json → never_opened_data` |

Full prose receipts: `f1_RESULT.md`, `f2_RESULT.md`, `d1b_RESULT.md`, `d2_RESULT.md`,
`d3_RESULT.md`, `d4_RESULT.md`, `d5_RESULT.md`, `d6_RESULT.md`, `d7_RESULT.md`, `d8x_RESULT.md`,
`p1_RESULT.md`, `p2_RESULT.md`, `p3_RESULT.md`.
