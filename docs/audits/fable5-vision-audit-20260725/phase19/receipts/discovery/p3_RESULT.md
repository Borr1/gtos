# Lane p3 — ADVERSARIAL: break the wave's strongest surviving finding

**Target** d5's headline, the strongest surviving positive claim in wave 19 and the sentence that
changes the owner-facing verdict: *"at the broker-correct fill contract the broad family's gross is
ZERO — +0.00029 R/opportunity, +0.00106 R/fill, a win rate of 38.70 % against a 38.65 % breakeven;
the negativity every prior lane published was the accounting, not the setups."*

**Population** the eight open windows of Session PB's reproduced sealed rosters (Oct/Nov/Dec 2025 +
Jan–May 2026), **1,129,016 candidate emissions**, k=15 rows, whole population, nothing sampled. The
sealed three (Jun/Aug/Sep 2025) were never opened.

**Method** written from the data — my own roster loader, my own M1 tape loader, my own walker, my own
fill classification (`p3_walk.py`). The only shared estate artifact reused is `pbg_econ.CostModel`
(the h1 four-term cost basis), because the quantity under attack is **gross** and re-deriving the
cost basis would break comparability with every published number.

---

## 0. HEADLINE

**The finding survives five attacks and dies on the sixth, and the sixth is not a modelling
argument — it is measured against the broker's own bid/ask ticks in the same windows.**

The M1 bar archive every wave-19 lane walks is **BID on open, high, low and close** — settled here
on `bridge_ftmo_m1_*` itself (the archive d8x could not reach), **223,239 bars** across four symbols
and two windows, `close == last tick BID` in **99.99 %** and `(close − mid)/spread = −0.500000` exactly.
Every walker in this estate therefore resolves the entry, the stop and the target against **one side
of the book**, for a round trip that transacts on **both**.

Re-walked at **tick resolution with true bid/ask and the side MT5 actually triggers on** — no bars,
no OHLC, no tie rule — on the four instruments the lane hold carries ticks for:

| | n rows | bar walk (d5's contract) | **tick truth** | Δ |
|---|--:|--:|--:|--:|
| **January 2026** | 14,186 | **+0.01152** | **−0.01348** | **−0.02501** |
| **April 2026** | 15,919 | −0.00927 | **−0.04620** | **−0.03693** |
| per fill, January | 4,986 | +0.03288 | **−0.03867** | **−0.07155** |
| per fill, April | 5,479 | −0.02873 | **−0.14473** | **−0.11600** |

**8 of 8 symbol-months move down; 7 of 8 are negative at the tick.** The error on gross is
**2.5–3.7 × the entire claim** it is being used to support.

The claim is a claim about the **signal** ("the setups' directional content is absent, not
negative"). It does not survive: **the gross is negative at every executable contract.** What does
survive is the estate's **net**, because the h1 cash spread charge happens to stand in for the
trigger displacement to within ±0.02–0.04 R/fill with no consistent sign. So nothing changes about
the money; what changes is the sentence.

**Corrected verdict, on the axis the owner asked for: SIGNAL.** The broad family's gross is not
zero. It is negative before the toll, negative at 1.5R and at 2.0R, negative after de-duplication,
negative on 7 of 8 measured symbol-months, and — measured against its own exact mirror on the same
rows at the same fill instants — **worse than a coin flip in 6 of 8 windows.**

---

## 1. WHY THIS IS THE FINDING TO ATTACK

After d6 killed the forming-bar candidate, d5's is the wave's strongest **surviving positive**
result: it is on the correct object (all eight windows, the whole roster), it corrects the
foundation lane (f1's clean-roster −0.01327), it carries an 8/8-window delta, and it is the basis of
the owner-facing line *"the signal is ZERO, not negative."* It also proposes the only live-actionable
rule anyone measured this week (d5's A5, +0.06860 net/opportunity).

It is also the most **attackable**, because it rests on two inferences rather than measurements:
that the order type can be read off the market's position at T, and that a bid-series walk with
unshifted levels is the right accounting for gross.

---

## 2. INDEPENDENT REPRODUCTION — EXACT

Different loader, different walker, different classification code, 1,129,016 rows against d5's
1,126,270 (+0.24 %, my drop set is slightly narrower — I do not require a confirm-minute close).

| quantity | d5 published | **p3 independent** |
|---|--:|--:|
| baseline (estate fill convention) gross / opportunity | −0.02379 | **−0.02379** |
| baseline gross / fill | −0.07963 | **−0.07968** |
| segment: reachable limits (`mkt_r0 > 0`), broker-correct | +0.00034 | **+0.00033** |
| segment: stop-entries (`mkt_r0 < 0`), estate convention | −0.76912 | **−0.76927** |
| segment: stop-entries, broker-correct | +0.01042 | **+0.01021** |
| share of the roster that is `mkt_r0 < 0` | 3.09 % | **3.09 %** |
| share of the roster's total negative gross carried by it | 99.88 % | **99.79 %** |

`EST` total gross **−26,863.8 R**; the 3.09 % stop-entry segment **−26,807.5 R**; everything else,
1,094,000 rows, **−56.3 R**. **d5's most extraordinary sub-claim is confirmed**: the estate's entire
published broad-family negativity was one accounting decision applied to 3 % of rows.

Segment shares: limits 84.54 %, at-market 12.38 %, stop-entries 3.09 % (of which born past their own
stop 2.08 %).

**One correction, and it makes d5's number bigger, not smaller.** d5 keeps the "wait for the level to
be touched" test on its *at-market* cohort — the same limit-order fiction it corrects elsewhere. An
at-market order is filled at T by construction (`mkt_r0 == 0` means the emitted entry **is** the last
print). Filling it gives that cohort +0.02080 instead of −0.00254, and the roster **+0.00317**
instead of +0.00029. Every attack below is run against the stronger version.

---

## 3. ATTACK 1 — ORDER TYPE (the inference the claim rests on): **SURVIVES**

d5 infers "a buy above the market is a STOP". Two other readings exist: the live engine has no
pending path at all (l10-X3), so those rows are either **never placed** or **placed at market**. All
three, on 1,129,016 emissions:

| treatment of the 3.09 % | gross / opportunity | CI95 (day-block, 172 blocks, 2,000 draws) |
|---|--:|--:|
| **BC** — stop entry (d5's) | **+0.00317** | [+0.00053, +0.00583] |
| **REFUSE** — never placed | +0.00285 | [+0.00025, +0.00561] |
| **MKT** — filled at the achievable price | +0.00297 | [+0.00032, +0.00563] |

Spread across the three readings: **0.00032 R.** The "zero" is not an artifact of the inferred order
type. Attack fails; the finding is **robust here**.

---

## 4. ATTACK 2 — QUOTE SIDE: **KILLS IT**

### 4.1 The premise, settled on the archive the lanes actually walk

d8x established BID on `vps-bars-20260727` M15 and flagged the transfer to `bridge_ftmo_m1_*` as
open. The lane hold carries true-UTC bid/ask ticks for XAUUSD, XAGUSD, EURUSD, USDJPY over
202510–202604. Measured, every M1 bar in the pack against the ticks inside its own minute:

| symbol · window | bars | close == last tick **BID** | close == **ASK** | (close−mid)/spread | high−max(bid) | low−min(bid) |
|---|--:|--:|--:|--:|--:|--:|
| XAUUSD 2026-01 | 28,525 | 0.99993 | 0.00000 | −0.500 | 0.00 | 0.00 |
| XAGUSD 2026-01 | 28,525 | 0.99996 | 0.00000 | −0.500 | 0.00 | 0.00 |
| EURUSD 2026-01 | 23,122 | 0.99996 | 0.23510¹ | −0.500 | 0.00 | 0.00 |
| USDJPY 2026-01 | 29,794 | 0.99993 | 0.00000 | −0.500 | 0.00 | 0.00 |
| XAUUSD 2026-04 | 27,185 | 0.99996 | — | −0.500 | 0.00 | 0.00 |
| XAGUSD 2026-04 | 27,182 | 1.00000 | — | −0.500 | 0.00 | 0.00 |
| EURUSD 2026-04 | 29,435 | 1.00000 | — | −0.500 | 0.00 | 0.00 |
| USDJPY 2026-04 | 29,471 | 0.99997 | — | −0.500 | 0.00 | 0.00 |

¹ EURUSD ticks are frequently zero-spread, so bid == ask on 23.5 % of bar ends; the mid test is
unambiguous. The table's `bars` column counts bars with ≥3 ticks **and** a positive median spread —
the rest are zero-spread minutes, not missing data. **Tick coverage measured separately: 100.000 %
of January pack bars carry ≥1 tick in all four symbols** (28,525 / 28,525 / 29,903 / 29,932);
April's tick export stops early and covers 94.84–94.90 %, which is why the walk guards every row on
`T + 120 min ≤ last tick` so both arms see identical rows. **d8x's open question 2 is closed: the
finding transfers exactly.**

Also measured, and worth carrying: the lane-hold tick rows' **`time_msc` is broker epoch while
`time`/`ts_utc` are true UTC** (2 h apart in January). A lane that keys on `time_msc` is 2–3 h off.

### 4.2 What it costs, MEASURED at tick resolution

A round trip transacts at the ask once and at the bid once. The estate resolves **both** legs against
the bid with unshifted levels — the outcome of a trader quoted the bid on both sides, who does not
exist. Re-walked on the ticks with MT5's own trigger sides (a BUY triggers on the ASK, a SELL on the
BID; a LONG's SL/TP trigger on the BID, a SHORT's on the ASK), first touch by actual tick order so
**no tie rule exists**:

| symbol | window | n | bar walk (BC) | modelled shift (SPRMT5) | **tick, level entry** | tick, true transacted |
|---|---|--:|--:|--:|--:|--:|
| XAUUSD | 2026-01 | 7,548 | +0.00095 | −0.01222 | **−0.02064** | −0.02201 |
| XAGUSD | 2026-01 | 1,273 | +0.06303 | −0.00453 | **−0.02682** | −0.04528 |
| EURUSD | 2026-01 | 2,936 | +0.00169 | −0.00110 | **−0.00399** | −0.00758 |
| USDJPY | 2026-01 | 2,429 | +0.02928 | +0.01091 | **+0.00425** | −0.01779 |
| XAUUSD | 2026-04 | 8,125 | −0.00200 | −0.03254 | **−0.04279** | −0.04594 |
| XAGUSD | 2026-04 | 1,578 | −0.04600 | −0.09915 | **−0.11945** | −0.17212 |
| EURUSD | 2026-04 | 3,383 | −0.01310 | −0.01900 | **−0.02318** | −0.03440 |
| USDJPY | 2026-04 | 2,833 | −0.00510 | −0.02675 | **−0.04270** | −0.05858 |

**8 of 8 move down. 7 of 8 are negative.** The modelled shift lands between the bar walk and the tick
truth in **8 of 8** — it recovers 40–75 % of the measured error, so **every modelled number below is
a lower bound on the damage.**

### 4.2b The obvious counter — "that is just your tie rule" — refuted by decomposition

Running the tick walk a third time with the **bid used for both legs** (the estate's own quote
convention, but at true tick ordering) splits the gap exactly:

| window | n | bar walk | → tick, BID-only | **resolution** | → tick, BID/ASK | **quote side** | total |
|---|--:|--:|--:|--:|--:|--:|--:|
| 2026-01 | 14,186 | +0.01152 | +0.00882 | **−0.00270** | −0.01348 | **−0.02231** | −0.02501 |
| 2026-04 | 15,919 | −0.00927 | −0.01349 | **−0.00422** | −0.04620 | **−0.03271** | −0.03693 |

**89.2 % and 88.6 % of the gap is the quote side; 10.8 % and 11.4 % is intrabar ordering.** At true
tick ordering with the estate's one-sided quote convention January is still **+0.0088** — the M1
OHLC is an exact aggregate of the bid ticks (`high − max(bid) = 0.00`, `low − min(bid) = 0.00` at
median, p05 and p95), so the bars are not the problem. **The problem is that there is only one side
of the book in them.** Per symbol the quote-side term runs −0.0067 (EURUSD Jan) to −0.0828
(XAGUSD Jan), and it is negative in 8 of 8.

### 4.3 The same attack, modelled, on all 24 instruments and all eight windows

| contract | fill | gross/opp | gross/fill | net/opp | net/fill |
|---|--:|--:|--:|--:|--:|
| EST — estate baseline | 0.2986 | −0.02379 | −0.07968 | −0.10679 | −0.35763 |
| **BC — d5's repaired contract** | 0.2781 | **+0.00317** | **+0.01140** | −0.07430 | −0.26718 |
| SPRMT5 — MT5 trigger sides | 0.2741 | **−0.02391** | −0.08722 | −0.09949 | −0.36298 |
| SPRSYM — d8x's symmetric form | 0.2781 | **−0.03194** | −0.11485 | −0.10941 | −0.39343 |

Day-block bootstrap, 172 blocks, 2,000 draws: BC +0.00317 [+0.00053, +0.00583] p(≤0) 0.0095;
**SPRMT5 −0.02391 [−0.02646, −0.02133] p(≤0) 1.0000**; SPRSYM −0.03194 [−0.03446, −0.02948] p 1.0000.
Paired: **SPRMT5 − BC = −0.02707 [−0.02817, −0.02596]**.

Independent replication of d8x's own instrument: s/d median **0.0926** (d8x 0.0988), mean 0.1549
(0.1405), share > 10 % **0.466** (0.494), > 25 % 0.131 (0.138); median risk 8.091 bps against a median
spread of 0.716 bps. Exit-mix shift on fills: **stop +3.95 pp, target −3.01 pp** (SPRMT5) and
+5.38/−3.92 (SPRSYM), against d8x's +2.86/−2.05 at a 240-minute horizon. Same phenomenon, reached
independently.

### 4.4 The refinement d8x's bound misses, and it matters

The bias is **side-asymmetric**, because a long's exits are quoted on the bid and a short's on the
ask. Longs are correctly walked on the exit leg; only their *entry* trigger displaces. Shorts take
the full displacement on both exit legs.

| | n | EST | BC | SPRSYM | **SPRMT5** |
|---|--:|--:|--:|--:|--:|
| LONG | 605,898 | −0.01483 | +0.00515 | −0.02678 | **−0.01181** |
| SHORT | 523,118 | −0.03418 | +0.00088 | −0.03791 | **−0.03791** |

The two models agree **exactly** on shorts (they are the same shift) and differ only on longs, where
d8x's symmetric form over-charges. **Consequence for the estate: any cohort with a short tilt has its
gross overstated more than any published figure allows for.**

### 4.5 The part that does NOT change: the net

On the four tick symbols, per fill:

| | January | April |
|---|--:|--:|
| estate net = bar gross − full h1 cost | −0.14339 | −0.22249 |
| tick truth net = tick-true gross − (h1 cost − its spread term) | −0.12743 | −0.25811 |
| estate error on **net** | **+0.0160 pessimistic** | **−0.0356 optimistic** |
| estate error on **gross** | **−0.0716 optimistic** | **−0.1160 optimistic** |

h1 spread term on those fills: 0.10730 R (Jan) / 0.11810 R (Apr) of a 0.17627 / 0.19376 total.
**The cash spread charge is a serviceable stand-in for the trigger displacement on net, and is not
one on gross.** Every published *net* number in this estate survives. Every claim of the form *"the
gross is zero, so the setups carry no directional content"* does not.

---

## 5. ATTACK 3 — BAR RESOLUTION / TIE RULE: **the claim is inside the ambiguity**

The estate resolves a same-bar stop-and-target to the stop. Flipping it to the target, same rows,
same fills: **+0.00565** vs BC's +0.00317, paired delta **+0.00248 [+0.00193, +0.00309]**.

An arbitrary intrabar convention is worth **78 % of the entire claim**. "Zero" is robust to it (both
readings round to zero); *any* claim of a positive gross is not. This is the same class of defect
that killed the wave's +0.038342 headline, one layer down — and the tick walk (§4.2) removes it
entirely, which is a second reason to prefer that number.

---

## 6. ATTACK 4 — DOUBLE COUNTING: **survives in sign, dies in resolution**

The same setup is re-emitted at consecutive M15 stamps. Compression measured, not assumed:

| dedup | n | ×compression | EST | **BC** | BC CI95 | SPRMT5 | MIRROR |
|---|--:|--:|--:|--:|---|--:|--:|
| none | 1,129,016 | 1.00 | −0.02379 | +0.00317 | [+0.00060, +0.00573] | −0.02391 | +0.00413 |
| one per sym·family·side·day | 49,861 | **22.6×** | −0.01387 | +0.01192 | [+0.00078, +0.02357] | **−0.04902** | +0.01814 |
| live placement (one per sym·day) | 4,110 | **274.7×** | −0.02506 | +0.00427 | **[−0.02789, +0.03761] p 0.384** | **−0.04690** | +0.01537 |

At the trade rate a book can actually run — 4,110 orders across 172 trading days — the "zero" is
**unresolvable**: its CI spans ±0.03. And the quote-side damage **doubles** under de-duplication
(−0.024 → −0.049), because the duplicated rows are the cheap, already-near-the-level ones.

---

## 7. ATTACK 5 — TARGET GEOMETRY: **survives**

The generator emits a target at **exactly 1.5R on every row** (50,692 of 50,692 checked, `min_rr`
1.5); the estate walks a 2.0R synthetic. Re-walked at the generator's own geometry, all 1,129,016
rows:

| contract | gross/opp @1.5R | gross/fill @1.5R | net/fill @1.5R |
|---|--:|--:|--:|
| EST | −0.02525 | −0.08456 | −0.36250 |
| BC | +0.00157 | +0.00566 | −0.27292 |
| SPRMT5 | −0.02600 | −0.09487 | −0.37063 |
| SPRSYM | −0.03447 | −0.12395 | −0.40254 |
| MIRROR | +0.00147 | +0.00529 | −0.27329 |

Every sign and every conclusion is identical. Note the mirror: at the generator's own geometry the
real book and its coin flip are **+0.00157 vs +0.00147** — a separation of 0.0001 R.

---

## 8. ATTACK 6 — SURVIVORSHIP: **survives, and closes d5's open question 3**

Every lane silently drops rows with no M1 bar at T−1m (session opens). Measured under the estate's
own contract, which does not need that bar:

| window | kept | dropped | share | EST kept | EST dropped |
|---|--:|--:|--:|--:|--:|
| 2025-10 | 164,058 | 5,566 | 3.28 % | −0.02478 | −0.03096 |
| 2025-11 | 141,763 | 5,357 | 3.64 % | −0.03450 | −0.05756 |
| 2025-12 | 150,688 | 5,463 | 3.50 % | −0.02442 | −0.04097 |
| 2026-01 | 145,885 | 5,117 | 3.39 % | −0.02577 | **−0.01759** |
| 2026-02 | 122,771 | 4,160 | 3.28 % | −0.01805 | −0.04238 |
| 2026-03 | 124,413 | 3,519 | 2.75 % | −0.02144 | −0.04426 |
| 2026-04 | 136,146 | 4,232 | 3.01 % | −0.01664 | −0.07078 |
| 2026-05 | 143,292 | 4,670 | 3.16 % | −0.02316 | −0.04287 |
| **pooled** | **1,129,016** | **38,084** | **3.26 %** | **−0.02379** | **−0.04270** |

The dropped rows are **worse in 7 of 8 windows** and fill at 0.19 against 0.30. Putting them back
moves the baseline −0.02379 → −0.02441. Small, but the exclusion is **favourable to the family**, not
neutral — nobody's number is protected by it.

---

## 9. ATTACK 7 — THE DIRECTION CALL AGAINST ITS OWN MIRROR: **the finding's own frame fails**

d5 concludes the directional content is *"absent"*. The test it never ran: the same rows, the same
fill instants, the same toll, side flipped. Because the fill trigger depends only on where the market
sits relative to the **level**, the mirror fills at exactly the same tick — so this control is exactly
paired and is **not** subject to the mirrored-limit artifact d1b found (which mirrors about the entry
and produces a marketable order).

| cohort | n | real | mirror | **signal** | CI95 | p(≤0) |
|---|--:|--:|--:|--:|---|--:|
| all | 1,129,016 | +0.00317 | +0.00413 | **−0.00096** | [−0.00662, +0.00465] | 0.639 |
| at-market | 139,741 | +0.02080 | +0.00722 | +0.01359 | [−0.00426, +0.03146] | 0.0755 |
| resting limits | 954,427 | +0.00033 | +0.00424 | −0.00391 | [−0.01007, +0.00212] | 0.882 |
| filled only | 313,960 | +0.01140 | +0.01486 | −0.00346 | [−0.02434, +0.01732] | 0.629 |

Per window: −0.00514, −0.00903, −0.00210, +0.00401, −0.00209, −0.01178, +0.02242, −0.00393 —
**positive in 2 of 8.**

So the correct statement of d5's own result is not *"the gross is zero, therefore the direction call
is neutral"*. It is: **the direction call is indistinguishable from its own mirror, and nominally
behind it, on 84.5 % of the population.** That is a stronger and more useful claim than the one it
replaces, and it is the same sign as d7's −0.04230 and the opposite of f2's +0.02877.

---

## 10. WHAT THIS DOES TO THE REST OF THE WAVE

Family table, all eight windows, gross per opportunity:

| family | n | EST | BC | **SPRMT5** | signal vs mirror | toll on fills |
|---|--:|--:|--:|--:|--:|--:|
| structural_distance_extreme | 22,812 | +0.01725 | **+0.06293** | **−0.13028** | +0.04259 | 0.6142 |
| liquidity_sweep_reclaim | 42,327 | +0.00294 | +0.02524 | −0.05236 | +0.03401 | 0.2932 |
| cross_asset_lead_lag | 20,441 | −0.01539 | +0.01643 | −0.08180 | +0.00317 | 0.4327 |
| current_breaker_re_entry | 90,041 | −0.26056 | +0.00679 | −0.00604 | +0.01007 | 0.2143 |
| displacement_continuation | 38,433 | −0.00709 | +0.00615 | −0.02102 | −0.00514 | 0.1479 |
| current_ob_retest | 256,134 | −0.00190 | +0.00103 | −0.00412 | +0.00069 | 0.1723 |
| session_open_range_break | 8,194 | −0.00980 | +0.00084 | −0.01708 | +0.00351 | 0.0903 |
| current_fvg_fill | 643,179 | −0.00393 | −0.00028 | −0.02689 | −0.00630 | 0.2740 |
| regime_transition_break | 2,299 | −0.00815 | −0.00283 | −0.00737 | −0.01448 | 0.0539 |
| volatility_compression_expansion | 5,156 | −0.04261 | −0.03675 | −0.05201 | −0.07607 | 0.0834 |

**d1b's one surviving family dies here, and the mechanism is exact.** `structural_distance_extreme`
is the estate's best broad family (8/8 windows, both geometries, survives every control except the
toll) *because* it lives in the tightest-stop cohort — its toll is 0.6142 R, the highest of the ten,
which is the same thing as saying its **s/d is the largest of the ten**. The quote-side displacement
scales with exactly that ratio, so the family whose edge is most concentrated in tight stops is the
family most destroyed by it: **+0.06293 → −0.13028.** d1b's own §4.1 already measured that its
direction value exists *only* in its two tightest risk-distance quintiles, "whose toll is 117 % of
the risk unit" — that is the tell, read one layer up.

**d8x is corroborated and refined.** Its −0.0696 R/trade bound is independently reproduced (my
measured bar-vs-tick gap per fill is −0.07155 in January), its BID premise is confirmed on the M1
packs it could not reach, and two corrections are added: the bias is **side-asymmetric** (long exits
are exactly right), and it applies to **gross, not to net** — the h1 cash spread charge already
covers the net to within ±0.04 R.

**d5's A5 arm** ("refuse at T every order not at price improvement", +0.06860 net/opportunity, 8/8
windows) is not tested here and does not need to be: it is a *per-opportunity* improvement obtained
by declining 64 % of candidates, and declining **all** of them is worth +0.10659 on the same metric.
Any refusal rule must be priced per fill or against a rate-matched random refusal. d5's own open
question 4 says so.

---

## 11. VERDICT, AND WHAT WOULD STILL HAVE TO BE TRUE

**The finding dies, and the mechanism is: the number it is made of is measured on one side of a
two-sided book.** Not look-ahead, not survivorship, not overfitting, not multiplicity — the
instrument. d5's repair of the *fill side* is real and survives everything I threw at it; its
conclusion about the *level* does not, because the level was never measurable on a bid-only tape at
the precision the claim needs (0.003 R claimed, 0.025–0.037 R of instrument error).

At the repaired-and-corrected contract, on the whole roster:

| | value |
|---|--:|
| gross / fill (BC, bid-tape) | +0.01140 |
| gross / fill (SPRMT5, lower bound on the correction) | **−0.08722** |
| gross / fill (tick truth, 4 symbols, Jan / Apr) | **−0.03867 / −0.14473** |
| toll / fill (h1 broker-true) | 0.27858 |
| net / fill | **−0.26718 (BC) … −0.36298 (SPRMT5)** |
| win rate on fills | 39.05 % |
| gross breakeven win rate | 38.57 % |
| **net breakeven win rate** | **50.49 %** |
| **gap** | **−11.43 pp** |

**What would have to be true to trade it**, stated at the corrected contract:

1. **+11.43 percentage points of win rate**, or equivalently ~0.279 R/trade of gross, against a
   measured gross that is negative and a measured signal-vs-mirror of −0.00096 ± 0.0056.
2. Or a **quote-side-immune contract**: the displacement is s/d, so the family would have to trade
   stops where s/d is small. Its median s/d is 0.0926 and 46.6 % of rows exceed 0.10 — and d1b/d7
   already measured that the family's gross **rises** as the stop tightens, i.e. its edge lives
   exactly where this correction bites hardest. The two requirements are in direct opposition.
3. Or a **direction call that beats its own mirror**. On the paired test it is behind in 6 of 8
   windows and the pooled CI contains zero from −0.0066 to +0.0047.

None of the three is close, and 1 and 2 cannot both be satisfied.

---

## 12. LIMITS OF THIS LANE

- **The tick adjudication is four instruments and two windows** (14,186 + 15,919 rows, 9.7 % and
  11.7 % of their rosters). The 24-instrument, 8-window number rests on the modelled shift, which the
  tick data shows is **conservative in 8 of 8** — so the pooled −0.02391 understates the damage.
  XAGUSD/XAUUSD ticks exist for 202510–202604; the remaining six symbol-months are a ~40 s run each.
- **MT5 trigger sides are a convention, not something I measured on this machine** (a BUY triggers on
  the ask, a SELL on the bid; a LONG's SL/TP on the bid, a SHORT's on the ask). The verdict does not
  depend on it: d8x's *symmetric* alternative is **worse** (−0.03194), and the only convention that
  produces a non-negative gross is the estate's, which quotes the same trader the bid on both legs.
- **Stops are assumed to execute at their level** in the tick walk (no slippage past the trigger).
  Real stops slip; the tick number is therefore still optimistic.
- **The mirror control is run on the bar arm.** At tick resolution the quote-side penalty is
  side-asymmetric, so a tick-level mirror would mix a mechanical term into the direction test. The
  bar-level mirror is exactly paired and is the honest version of that test.
- **Sealed three untouched.** June/August/September 2025 were not opened.

---

## 13. FILES

- `p3_RESULT.json` — every table above, machine-readable.
- `p3/p3_walk.py` — the eight-contract walker (own tape loader, own walker, own fill classification).
- `p3/p3_analyse.py`, `p3/p3_analyse2.py`, `p3/q15.py` — pooled tables, bootstrap, dedup, families.
- `p3/p3_ticks.py` — the BID verification and the tick-resolution walk.
- `p3/p3_drops.py` — the survivorship measurement.
- `p3/P3_MAIN.json`, `P3_PASS2.json`, `P3_TGT15.json`, `P3_DROPS.json`,
  `P3_TICK_{XAUUSD,XAGUSD,EURUSD,USDJPY}_{202601,202604}.json` — raw outputs.
- Per-row npz (1.13 M rows × 8 contracts × 2 geometries) at `/tmp/p3/P3_*.npz` and `/tmp/p3/P315_*.npz`
  — regenerable in ~30 s/window by `p3_walk.py <YYYYMM>` (`P3_TGT=1.5` for the second geometry).
