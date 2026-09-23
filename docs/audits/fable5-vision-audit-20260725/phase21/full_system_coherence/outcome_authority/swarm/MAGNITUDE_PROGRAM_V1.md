# THE MAGNITUDE PROGRAM — the kill test, and what is left standing

**Owner-approved redirect, 2026-08-12. Measurement and design only.** No live path, no config,
nothing armed, no VPS, no March. The only inputs are the true-UTC bar archives and the estate's own
committed cost artifacts; nothing was mutated.

---

## 0. The verdict, in four numbers

**The redirect as proposed does not survive its own first test, and it fails on cost, not on the
premise.** The premise is right: magnitude structure is real, it is large, and a breakout does
capture more of it than a random entry does. The magnitude it captures is roughly a fiftieth of what
the trigger costs.

| | |
|---|---:|
| Breakout exit cells measured (24 symbols, D1+H4, 2014–2026, 190,638 triggers, 36 exit contracts each) | **576** |
| Cells whose 95 % cluster-bootstrap lower bound on **net** expectancy is above zero | **0** |
| Best net expectancy anywhere in the scan (point estimate) | **+0.0232 R/trade** [−0.031, +0.080] |
| Mean broker-true cost the trigger must first pay | **0.1299 R/trade** |

And the one number that closes it. Isolating the trigger against a **matched blind-entry control** —
same symbol, same bar population, same geometry, same count — the breakout's gross advantage is
**+0.0026 R/trade** pooled, best cell **+0.0664**. On a genuine 2014–2021 → 2022–2026 holdout that
advantage **changes sign**: train mean **+0.0321**, test mean **−0.0373**, sign agreement **37.8 %**
of 576 cells, train/test correlation **0.242**.

> **This is the same shape Lane I found for every signed effect, now measured on a trigger Lane I
> never scanned.** It is a third independent instrument reaching the same conclusion, and it is why
> the kill is stated as a finding rather than as a failure to find.

**Three things did survive, and none of them is an edge.** They are cost geometry — arithmetic, not
bets — and two of them apply to money that is armed today:

1. **Entering at broker hour 00 costs 2.7–3.3× the fixed cost of any other H4 anchor** (0.1860 R vs
   0.0559–0.0682 R; the spread term alone is 0.2306 R vs 0.0495–0.0653 R at a 1-ATR stop). Mechanism
   identified inside a single symbol: EURUSD's modelled spread at hour 00 is **6.8×** its own
   other-hour spread. Metals and indices are unaffected.
2. **Widening the stop from 1.0 to 2.0 × ATR14 is worth +0.03 to +0.07 R/trade**, in all 10
   grid × vol-quintile cells, because the fixed cost terms are price quantities divided by the stop.
3. **Total cost in R rises monotonically with horizon**, from 0.061 R to 0.218 R between a 1-day and
   a 160-day hold. This **corrects Lane I's F4** for any fixed-R contract (§4).

---

## 1. What was measured, and against what

**Bars.** `LANE_INPUTS_TRUE_UTC_V1/sources/bars/deep_universe_h4d1_2014_2026` — the same 24-symbol,
true-UTC H4/D1 archive Lane I used, unmutated. Entries span 2014-01-14 → 2026-06-17.

**Trigger.** Donchian channel breakout. At the close of bar `t`, `close[t]` beyond the extreme of
bars `[t−N, t−1]`, for `N ∈ {10, 20, 40, 55}`, both sides. The channel uses **strictly prior** bars;
ATR14/ATR50 use bars ≤ t.

**Entry.** The **open of bar t+1**, never the trigger bar's own close. A close-entry backtest gives
away an instant nobody can trade; the measured entry gap is small (−0.004 to −0.006 ATR) but it is
recorded rather than assumed (`DIAG_ENTRY_GAP.csv`).

**Exit.** First-touch triple barrier from the entry price: stop `s × ATR14` for `s ∈ {1.0, 1.5, 2.0}`,
target `k × stop` for `k ∈ {1, 2, 3, 5}`, time stop `H` bars for `H ∈ {5, 20, 80}` (D1) and
`{30, 120, 480}` (H4) — matched wall clock, 5 d / 20 d / 80 d. Timeouts mark out at the close.
**Gap-through on the stop is filled at that bar's open**, so a stop can and does lose more than 1 R;
this costs 0.005 R/trade on average and 0.026 % of rows lose more than 3 R.

**The control that does the work.** For every breakout arm there is a **matched blind arm**: the same
number of entries, in the same symbol, drawn uniformly from that symbol's own valid bars (seed
20260812), run through identical geometry. Lane I established that blind entry on this surface is a
fair game gross; the blind arm here re-establishes it *paired*, so the difference isolates what the
trigger contributes and nothing else. **13,725,936 outcome rows.**

**Cost — the part that decides everything.** `src.costs.model.cost_r` is the authority, reading
`BROKER_TRUE_COSTS_V1_1.json` and `SPREAD_MODEL_V1.json`. At 2.0 ms/call it cannot price 13.7 M rows,
so the four terms were decomposed and vectorised, then **validated back against the authority on
1,500 random real rows**:

| term | max abs deviation vs `cost_r` |
|---|---:|
| spread | **0.0** (exact) |
| slippage | **0.0** (exact) |
| commission | 1.20 × 10⁻⁴ R |
| swap | 1.16 × 10⁻² R (rollover-night off-by-one at DST edges) |
| **total** | **1.16 × 10⁻² R**, against a mean total of 0.75 R on the sampled contracts |

Four decisions taken explicitly rather than by default, each of which moves the answer:

- **`spread_band="mid"`** — the Session AG era model, not the 2026 tick snapshot. Charging 2026
  spreads to 2014 bars understates FX materially over this window and the bias has no consistent
  sign. This is the single most important cost decision in the study.
- **V1_1**, which corrects the two false `zero` FTMO oil commissions to $5.00/lot.
- **Favourable swap floored to zero** (the authority's own rule). No carry credit is ever booked as
  income here.
- **Slippage:** the authority's price-domain model covers 15 of these 24 symbols on FTMO and
  **refuses the other 9 outright** (`NOT_EVALUABLE` — which is why `cost_r` itself could only price
  883 of the 1,500 validation rows). Where it refuses, the fallback is the artifact's own pooled
  TRANSFERRED `value_r` charged as a **fixed R that does not dilute when the stop is widened** — the
  conservative direction, since a wider stop is this study's main cost lever. Coverage is carried
  per row (`slip_cov`).

**Intervals** are a cluster bootstrap over **symbol × calendar quarter**, 1,000 draws, seed 20260812.
This is not decoration: an 80-day D1 barrier re-entered every few days produces massively overlapping
holds, and the measured **design effect is 3.5–3.6×** — the naive standard error understates the true
one by 1.9×. Every interval in this document is the clustered one.

---

## 2. The kill test

### 2.1 The map

`BREAKOUT_ECONOMICS.csv.gz` — 576 breakout cells and 576 matched blind cells.

| arm | cells | cells gross > 0 | pooled gross | pooled cost | pooled net | cells net > 0 | cells net CI-lo > 0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| BREAKOUT | 576 | 292 | **+0.0119** | 0.1299 | **−0.1180** | 14 | **0** |
| BLIND | 576 | 279 | +0.0093 | 0.1356 | −0.1264 | 3 | 0 |

The ten best cells by net expectancy are all `k = 5` (the widest target) and seven of ten are
`s = 2.0` (the widest stop) — both of which are **cost effects**, not edge effects: a wide stop
divides the fixed cost by a larger number, and a wide target reduces the number of round trips per
unit of travel. The best cell in 576 is H4 / channel 55 / LONG / `s` 2.0 / `k` 5 / `H` 30 at
**+0.0232 R/trade, CI [−0.0306, +0.0798]**.

**Not one cell in 576 has a lower bound above zero.** Under the optimistic intrabar rule (§2.5) it is
17 cells positive on point estimate, and still **zero** with a lower bound above zero.

### 2.2 The trigger's own contribution

`BREAKOUT_DELTA.csv`. Pooled per-trade mean of the breakout arm minus the blind arm, per cell,
cluster-bootstrapped jointly.

| grid | side | cells | mean gross delta | cells > 0 | cells CI-lo > 0 |
|---|---|---:|---:|---:|---:|
| D1 | LONG | 144 | +0.0133 | 110 | 0 |
| D1 | SHORT | 144 | −0.0385 | 20 | 0 |
| H4 | LONG | 144 | +0.0220 | 133 | 11 |
| H4 | SHORT | 144 | +0.0136 | 112 | 28 |

**The trigger is not nothing.** 375 of 576 cells show a positive gross delta, 39 with a lower bound
above zero, and the best is +0.0664 R/trade. That is a real conditional effect and it deserves to be
stated as one rather than rounded to zero.

**It is also not enough, by a factor of about fifty.** The mean gross delta is +0.0026 R/trade
against a mean cost of 0.1299 R/trade. The best delta in the entire scan, +0.0664, still leaves that
cell's absolute net expectancy inside its own confidence interval around zero.

> **One estimator warning, because it cost me the first version of this table and it will cost the
> next reader too.** The first pass computed the delta as an unweighted mean over clusters and got
> **−0.26 R/trade** — a confident kill with the wrong sign. Quarters that fire many breakouts are
> systematically the good ones (`corr(cluster trade count, cluster mean) = 0.49`), so an unweighted
> cluster mean silently reweights the estimate toward quiet quarters. The pooled per-trade mean is
> what a trader earns; the cluster is for the **interval**, never for the estimator. The two differ
> by 0.37 R here.

### 2.3 The thesis's own test: realised travel beyond the trigger

The redirect's stated condition is that *realised travel beyond the trigger exceeds the cost of the
trigger plus the whipsaw rate*. Measured directly, in ATR units, over the longest horizon
(`DIAG_PATH_EXTREMES.csv`):

| grid, channel, side | MFE blind | MFE breakout | MAE blind | MAE breakout | MFE/MAE blind | MFE/MAE breakout |
|---|---:|---:|---:|---:|---:|---:|
| D1, 55, LONG | 6.151 | **7.140** | 4.602 | 5.274 | 1.3365 | **1.3538** |
| D1, 55, SHORT | 4.750 | 4.515 | 5.404 | 5.112 | 0.8790 | 0.8832 |
| H4, 55, LONG | 16.090 | **17.387** | 12.462 | 13.437 | 1.2912 | 1.2939 |
| H4, 55, SHORT | 12.558 | 11.536 | 15.041 | 13.549 | 0.8349 | 0.8514 |

**The first half of the thesis is confirmed and the second half is refuted in the same row.** A
breakout genuinely does buy more travel — MFE rises 16 % on D1 LONG, exactly as Lane I's magnitude
map predicts. But it buys **more travel in both directions**: MAE rises 15 % alongside. The ratio of
favourable to adverse travel — the only part that can be monetised at fixed risk — improves by
**1.3 %**, from 1.3365 to 1.3538.

Magnitude without direction expands both tails. A breakout is a magnitude event, so it expands both
tails. That is the whole result in one sentence, and it is why the barrier economics come out where
they do.

### 2.4 The holdout, which is decisive

`DELTA_TRAIN_TEST.csv`. Gross delta computed separately on 2014–2021 and 2022–2026:

| | train 2014–2021 | test 2022–2026 |
|---|---:|---:|
| mean gross delta over 576 cells | **+0.0321** | **−0.0373** |
| sign agreement | | **218 / 576 = 37.8 %** |
| train/test correlation | | **0.242** |
| cells positive in **both** halves | | 127 / 576 |

Sign agreement **below 50 %** is worse than a coin flip. The trigger effect that exists in the full
sample is a training-half effect that inverts.

**The two cells that pass every full-sample screen fail this one.** H4 / channel 40 and 55 / LONG /
`s` 2.0 / `k` 5 / `H` 30 are the only cells in 576 that are simultaneously net-positive and have a
trigger-gross lower bound above zero. Split by era:

| cell | era | n | net | net CI | gross delta | delta CI |
|---|---|---:|---:|---|---:|---|
| H4 ch40 | train | 8,762 | −0.0181 | [−0.095, +0.048] | +0.0609 | [−0.010, +0.138] |
| H4 ch40 | test | 8,692 | +0.0377 | [−0.037, +0.110] | +0.0328 | [−0.040, +0.098] |
| H4 ch55 | train | 7,606 | −0.0030 | [−0.086, +0.070] | +0.0832 | [+0.009, +0.163] |
| H4 ch55 | test | 7,465 | +0.0500 | [−0.029, +0.127] | +0.0463 | [−0.028, +0.116] |

Every one of these eight intervals contains zero except the train-half delta on channel 55. There is
nothing here to arm.

### 2.5 The three adversarial passes I ran against my own kill

A negative result is as easy to manufacture as a positive one. Each of these was an attempt to break
the kill; none did.

**(a) The intrabar tie rule.** A bar reaching both barriers has unknowable ordering. Scoring it STOP
is pessimistic and would hit breakouts harder, since their post-entry path is larger relative to
entry ATR14. Measured: the ambiguous rate is **0.04 %–0.65 %**, and the breakout-minus-blind delta
moves by **less than 0.002 R** across the STOP / TARGET / EXCLUDE rules (`TIE_BOUNDED_DELTA.csv.gz`).
Not the driver.

**(b) The loss tail.** Gap-honest stop fills produce a −19.3 R outlier (GER40 2019-10-24, plausibly
a bad archive bar). Winsorising every gross return at −3 R moves the pooled mean by **+0.0022 R**.
Not the driver.

**(c) The per-symbol positives, which look like the strongest result in the study and are the
weakest.** Nine of 48 D1 `(symbol, side)` cells are net-positive at the longest horizon, and the seven
largest are all LONG on assets that rose over 2014–2026: BTCUSD +0.417, XAUUSD +0.260, ETHUSD +0.181,
USDJPY +0.141, US100_cash +0.125, USOIL_cash +0.110, UKOIL_cash +0.103. (H4: 7 of 48 positive.)
Lane I §7.2 warned that this is secular drift. The drift-free instrument is the paired delta, and it
does **not** simply dissolve — `corr(level, drift-free delta) = 0.841`, and 6 of 96 symbol-sides have
a delta lower bound above zero. Those six are BTCUSD LONG (D1, H4), BTCUSD SHORT (H4), ETHUSD LONG
and SHORT (H4), XAUUSD LONG (H4). But split by era (`SURVIVOR_HOLDOUT.csv`), **five of six lose
significance on 2022–2026**, and BTCUSD LONG on D1 collapses from a net level of **+0.592 to +0.071**.

**One cell survives even this**, and it is worth naming precisely because it is the only one:
**BTCUSD SHORT on H4**, delta **+0.207 [+0.056, +0.337]** in train and **+0.208 [+0.058, +0.337]** in
test. Two independent halves, near-identical point estimates, both intervals excluding zero, on a
*short* — so it is not drift. Its net **level**, however, is −0.053 in train and +0.040 in test. It
is a stable conditional effect that is not a profitable contract. It is recorded in §6 as the single
honest candidate this study produced, and not proposed for anything.

---

## 3. The estate's own standing admission, re-measured independently

`mx_btcusd_d1_donchian_20_breakout @ target_5R` is exactly a cell in this grid: D1, channel 20,
BTCUSD, stop 1 R, target 5 R, horizon 80 own bars. This study reaches it from a completely different
pipeline — different bar loader, different labeller, different cost path — and it is the closest thing
to an independent replication the estate has had.

| side | arm | n | gross | cost | of which carry | net | net CI |
|---|---|---:|---:|---:|---:|---:|---|
| LONG | breakout | 241 | +0.961 | 0.245 | **0.200** | **+0.716** | [+0.032, +1.232] |
| LONG | blind | 241 | +0.129 | 0.278 | 0.251 | −0.148 | |
| SHORT | breakout | 110 | +0.116 | 0.266 | 0.240 | −0.150 | [−0.628, +0.320] |

**It replicates on the long side**, with a drift-free delta of **+0.832 [+0.232, +1.313]** — the
largest single effect in this entire study, and the estate was right to find it. Three qualifications
belong with it:

- **It decays exactly as AN measured.** Train 2014–2021 net **+1.044**, test 2022–2026 net **+0.246**
  — a 4.2× decay, the same chronological pattern AN found (recent folds 13.2 % of early folds). Size
  on the recent half.
- **Carry is 82 % of its cost** and this study prices it explicitly: 0.200 R per trade of swap at
  FTMO's −30 %/yr BTCUSD rate over a ~96-hour median hold. At a 1-ATR stop on an 80-day contract that
  term is not a rounding error, it is a fifth of the risk unit.
- **n = 241 across 33 clusters.** The interval reaches from +0.03 to +1.23. And this is not an
  independent look in the multiplicity sense: it is a replication of a cell the estate already
  selected, on the same underlying prices.

The sleeve was disarmed by the owner on 2026-08-05 (`src/safety/armed_set.py:9`). Nothing here argues
for re-arming it; it argues that the finding was real, smaller now than when it was found, and
carry-heavy.

---

## 4. The horizon result — and a correction to Lane I's F4

`HORIZON_SWEEP.csv`. One geometry (Donchian-20, stop 2.0 × ATR14, target 3 R, 24 symbols), ten
horizons, both grids, so the horizon is the only thing that moves.

D1, LONG (`n` = 4,772 per row):

| H (bars) | mean hold (h) | cost fixed | cost carry | **cost total** | gross | net | net CI | timeout rate |
|---:|---:|---:|---:|---:|---:|---:|---|---:|
| 1 | 24 | 0.0537 | 0.0074 | **0.0611** | 0.0268 | −0.0343 | [−0.046, −0.023] | 0.983 |
| 3 | 70 | 0.0537 | 0.0186 | 0.0722 | 0.0517 | −0.0205 | [−0.046, +0.003] | 0.899 |
| 8 | 168 | 0.0537 | 0.0445 | 0.0982 | 0.1014 | +0.0032 | [−0.043, +0.054] | 0.702 |
| **12** | **231** | 0.0537 | 0.0590 | 0.1127 | 0.1169 | **+0.0042** | [−0.053, +0.067] | 0.595 |
| 20 | 329 | 0.0537 | 0.0844 | 0.1381 | 0.1346 | −0.0035 | [−0.078, +0.072] | 0.426 |
| 80 | 605 | 0.0537 | 0.1501 | 0.2038 | 0.1570 | −0.0468 | [−0.147, +0.051] | 0.079 |
| 160 | 690 | 0.0537 | 0.1645 | **0.2182** | 0.1541 | −0.0640 | [−0.167, +0.034] | 0.026 |

**Lane I's F4 — "cost drag falls as 1/√t while conditional IR does not fall" — is arithmetically
correct and does not transfer to a fixed-R contract.** F4's denominator is the *dispersion* of the
forward return, which grows as √t while a one-off cost stays flat. A barrier contract's denominator
is the **stop**, which does not grow at all, and its numerator contains **carry, which is linear in
t**. Measured on this grid, total cost in R rises **3.6×** from a 1-day to a 160-day hold, and the
cost minimum is always the shortest horizon available.

The optimum is therefore **interior and driven by two opposing terms**, not monotone in either
direction: gross expectancy rises with horizon and plateaus around 20 bars (0.027 → 0.135 → 0.157)
while carry keeps climbing. Net peaks at **H = 12 bars, a ~231-hour hold**, at **+0.0042 R/trade**
whose interval spans zero.

Three consequences worth carrying forward:

1. **"Lengthen the contract" is not free, and its price is now measured.** Lane I's recommendation 2
   is right for the broad candidate surface's 2-hour span — that surface is far below any optimum —
   and wrong as a general direction. There is a maximum, and past it every additional day is bought
   with carry at a fixed R denominator.
2. **The armed book's 320-hour H4 contract sits at or just past the optimum on this instrument**,
   not "near the best end of the curve". On the H4 LONG sweep, net at H = 96 (107 h mean hold) is
   −0.0297 and at H = 720 is −0.0327 — flat, because H4 breakouts resolve long before the time stop.
   The statement that the sleeve estate is favourably positioned survives; the reason given for it
   does not.
3. **Carry is the term that makes long horizons expensive and it is wildly instrument-specific**
   (`SYMBOL_CARRY.csv`). At the longest horizon, carry per trade runs from **0.000 R** (any side
   where the broker's swap is favourable — 16 of 48 symbol-sides on D1) to **0.427 R** (UKOIL_cash
   SHORT) and 0.305 R (US500_cash LONG). **Any long-horizon family must select the side on which
   carry is zero**, and that is a broker fact available before any market measurement.

---

## 5. Where the magnitude map does and does not transfer

### 5.1 The entry hour — a large, real, cost-side effect

`ENTRY_HOUR.csv`. H4 breakouts, all contracts pooled, by broker wall hour:

| broker hour | n | gross | cost fixed | **net** | net CI |
|---:|---:|---:|---:|---:|---|
| 08 | 671,436 | +0.0311 | 0.0682 | **−0.0696** | [−0.108, −0.034] |
| 20 | 1,379,160 | +0.0365 | 0.0559 | −0.0741 | [−0.100, −0.046] |
| 12 | 1,073,664 | +0.0115 | 0.0573 | −0.0811 | [−0.108, −0.051] |
| 04 | 736,272 | +0.0112 | 0.0668 | −0.0898 | [−0.123, −0.055] |
| 16 | 1,171,080 | −0.0014 | 0.0572 | −0.0993 | [−0.127, −0.074] |
| **00** | 768,564 | **+0.0727** | **0.1860** | **−0.1500** | [−0.187, −0.111] |

**Hour 00 has the best gross expectancy of any anchor and by far the worst net.** The fixed cost
there is 2.7–3.3× every other hour, and the gross advantage — which is Lane I's F1 travel profile showing
up — does not come close to paying for it.

The mechanism is identified inside a single symbol, so it is not a composition artifact
(spread in R at a 1-ATR stop):

| symbol | hour 00 | hours 04–20 |
|---|---:|---:|
| EURUSD | **0.1196** | 0.0165 – 0.0222 |
| XAUUSD | 0.0302 | 0.0297 – 0.0337 |
| US100_cash | 0.0112 | 0.0119 – 0.0132 |

**The rollover penalty is an FX-class effect. Metals and indices do not have it.** That precision
matters: a blanket "never enter at hour 00" rule would be right for FX and pointless for the two
classes where most of the armed book lives.

This corroborates AH's FX-D1 hour finding and AM/AQ's hour-01 entry convention **through a completely
different channel** — those measured an edge difference, this measures a cost difference, on 12 years
instead of one window. Two instruments, one conclusion.

> **One caveat, stated because it bounds the claim.** The hour-of-week multiplier is a *model* term
> fitted from ticks in the 2026 reference window and extrapolated across 2014–2026. The direction is
> a structural broker fact (rollover), the magnitude is modelled. `SPREAD_MODEL_V1.json`'s own
> `honest_limit` governs.

### 5.2 The stop-width lever — deterministic, and it works

`STOP_WIDTH_LEVER.csv`. Net R/trade by stop width and within-symbol ATR14/ATR50 quintile:

| grid | vol quintile | s = 1.0 | s = 1.5 | s = 2.0 |
|---|---|---:|---:|---:|
| D1 | Q0 (compressed) | −0.1393 | −0.1123 | **−0.0844** |
| D1 | Q4 (elevated) | −0.0844 | −0.0897 | −0.0910 |
| H4 | Q0 | −0.1373 | −0.0801 | **−0.0679** |
| H4 | Q4 | −0.0703 | −0.0481 | **−0.0441** |

Total cost falls from 0.180 → 0.133 R (D1 Q0) and 0.153 → 0.110 R (H4 Q0) as the stop widens, because
spread, commission and the price-domain part of slippage are all price quantities divided by the
stop. This is arithmetic. It is bounded by two things the study charges honestly: the pooled-R
slippage fallback on 9 of 24 symbols does not dilute, and a wider stop holds longer, so carry rises.

### 5.3 Lane I's F2 does **not** transfer to a fixed-R contract, and the sign is the surprise

F2 — `ATR14/ATR50 → forward travel per unit of ATR14`, Q0/Q4 ratio up to 1.42×, monotone, 13/13 years,
24/24 symbols — is the most stable structural fact in the estate. The intuitive move is to prefer
compressed-vol entries, where each ATR of risk buys 42 % more travel.

**Measured on a fixed-R barrier contract, that is backwards.** From `CONDITIONING.csv.gz`, pooled net by
quintile: on H4, Q0 −0.1131 and Q4 **−0.0588**; on D1, Q0 −0.1438 and Q4 −0.1135. The elevated-vol
quintile wins on both grids.

Two reasons, both mechanical, both worth stating because the naive reading is a trap:

1. **A driftless barrier is scale-free.** With a stop at `a` and a target at `b`, the probability of
   reaching the target first is `a/(a+b)` regardless of volatility. More travel per unit of ATR14
   does not move expectancy at all — it just resolves the trade sooner.
2. **It does move cost, in the wrong direction.** Compressed ATR14 means a *tighter stop in price*,
   and cost in R is `cost_price / (s × ATR14)`. Measured: total cost 0.1803 R at Q0 versus 0.1426 R
   at Q4 on D1 at `s` = 1.0.

**So the correct use of F2 is the opposite of a filter: it is a stop-scaling term.** Scaling the stop
*up* when ATR14/ATR50 is compressed keeps cost-in-R flat across the vol-ratio range and gives back
the extra travel F2 promises. Its measured worth is bounded by the Q0→Q4 cost spread, **~0.038 R/trade
on D1**, and it is a cost repair, not an edge. Using F2 the other way — entering preferentially in
compressed vol — would have made every contract in this study *worse*.

---

## 6. Task 2 — the family, and why it is not declared

The brief says to specify the family if the thesis survives. **It did not, and registering a family I
have already measured to be net-negative would be precisely the estate's documented failure mode** —
a family that grew 32 → 59 in three days, each addition justified by the scan that produced it.

So: **no breakout family is declared for arming, and none is proposed for the candidate book.** The
576-cell scan is billed as what it is — a map, not a look. Its cells must not be re-mined later; the
holdout in §2.4 is the reason.

What follows is the smallest honest residue, in two parts.

### 6.1 The one candidate, registered for the shadow lane only — 2 members

Named before measuring anything further, count fixed at two, both derived from §2.5(c)'s survivor and
its nearest sibling rather than from the scan's winner:

| # | member | grid | trigger | side | stop | target | horizon | rationale |
|---|---|---|---|---|---|---|---|---|
| **M1** | `bo_btcusd_h4_dc20_short` | H4 | Donchian 20 | SHORT | 2.0 × ATR14 | 3 R | 96 bars | the only cell in 576 whose drift-free delta reproduces across both halves with both intervals excluding zero (+0.207 train / +0.208 test) |
| **M2** | `bo_ethusd_h4_dc20_short` | H4 | Donchian 20 | SHORT | 2.0 × ATR14 | 3 R | 96 bars | same construction on the paired asset; delta +0.201 train / +0.093 test — the pre-declared sibling that makes M1 falsifiable rather than unique |

Fixed by declaration, not to be tuned: entry at the next H4 open; **never at broker hour 00**;
stop 2.0 × ATR14 with the F2 scaling of §5.3 (`stop = 2.0 × ATR14 × (ATR14/ATR50)^(−0.5)`, the
exponent that flattens the measured Q0→Q4 cost spread); target 3 R; time stop 96 H4 bars; SHORT only,
which is also the side where crypto carry is not zero — so **carry must be charged, not assumed away**
(BTCUSD SHORT carries 0.074 R even at the longest horizon measured).

**Declared expectation, on the record, before any forward data exists:** net expectancy
**between −0.05 and +0.05 R/trade**, most likely near zero. This study's own estimate of the level is
−0.053 (train) and +0.040 (test). *If the forward record lands in that band, the family is dead and
should be retired, not re-parameterised.* Anything outside ±0.15 R/trade is more likely a measurement
defect than an edge and should be investigated as one.

### 6.2 The three geometry repairs, which are what this study actually produced

None is a family, none needs an edge, none needs a multiplicity bill, and two touch armed money. In
descending order of measured value:

| # | repair | measured value | evidence | status |
|---|---|---:|---|---|
| **G1** | Do not enter FX-class instruments at broker hour 00 | **+0.060 to +0.080 R/trade** | §5.1; mechanism identified within EURUSD (6.8× spread), absent in metals and indices | corroborates AH/AM through cost; **applies to the armed book's FX exposure** |
| **G2** | Widen the fixed stop from 1.0 to 2.0 × ATR14 | **+0.03 to +0.07 R/trade**, 10/10 cells | §5.2; arithmetic, not a bet | a live-contract change; owner's call, priced here |
| **G3** | Select the side on which broker carry is zero, at any horizon beyond a few days | up to **0.43 R/trade** avoided | §4, `SYMBOL_CARRY.csv`; 16 of 48 D1 symbol-sides carry exactly 0.000 R | a broker fact, knowable before any market measurement |

G1 and G3 are strictly free. G2 trades cost against position sizing at a fixed cash risk and is
therefore a real decision with two sides, not a repair.

---

## 7. Task 3 — the forward validation path, and the power that kills it

There is no unread historical window: the three 2025 windows were spent by wave 19, February is
used-once, **March 2026 is reserved and stays reserved**. So the only honest path is development on
spent surface — which is what §§1–5 are, and they are billed as a map — followed by **forward
validation through the deployed shadow lane**.

Lane A found no power calculation anywhere in phases 19–21. Here is one.

### 7.1 The arithmetic

Two-sample-free one-sided test at α = 0.05, power 0.80, per-trade net R dispersion measured on this
corpus, inflated by the **measured** design effect of 3.5–3.6 from overlapping holds:

```
n  =  (z₀.₉₅ + z₀.₈₀)² · σ² / δ²  ·  DEFF
```

`σ` = 1.299 (D1) / 1.707 (H4); `DEFF` = 3.54 / 3.59; trade rate at Donchian-20 across all 24 symbols
= 383/yr (D1), 1,948/yr (H4).

| effect to detect | grid | trades needed | **years, all 24 symbols** | years, a 3-symbol live book |
|---|---|---:|---:|---:|
| **+0.09 R/trade** (Lane I's required edge) | H4 | 7,980 | **4.1** | 32.8 |
| +0.09 R/trade | D1 | 4,560 | **11.9** | 95.3 |
| +0.05 R/trade | H4 | 25,855 | 13.3 | 106.2 |
| **+0.0232 R/trade** (this study's best cell) | H4 | 120,087 | **61.6** | 493.1 |
| +0.0232 R/trade | D1 | 68,615 | 179.2 | 1,433.6 |

**Read the second column, not the first.** Even at the estate's own required edge of +0.09 R/trade —
an effect 3.9× larger than anything this study measured — the shadow lane needs **4.1 years** running
all 24 symbols on H4, or **32.8 years** at the three-symbol scale of the armed book. To validate the
effect this study actually found would take **61.6 years**.

**The forward shadow lane cannot validate a breakout edge family. Not slowly — not at all.** That is
not a criticism of the lane; it is the arithmetic of a 1.7 R per-trade dispersion against a 0.02 R
signal. Any future proposal to "let the shadow lane decide" on a per-trade edge of this size should
be answered with this table.

### 7.2 What the shadow lane *can* validate, and should be asked to instead

The per-trade **cost** has 100–144× less variance than the per-trade **net return**
(σ_cost 0.108 / 0.170 versus σ_net 1.299 / 1.707). Power scales with `1/σ²`, so the same lane
resolves a cost question two orders of magnitude faster:

| question | grid | trades needed | **time, 24 symbols** |
|---|---|---:|---:|
| Is the cost model biased by ≥ 0.02 R/trade? | H4 | 1,610 | **9.9 months** |
| Is the cost model biased by ≥ 0.02 R/trade? | D1 | 640 | 20.0 months |
| Is it biased by ≥ 0.01 R/trade? | H4 | 6,437 | 3.3 years |

**Every conclusion in this document is a cost conclusion.** The kill is a cost kill; G1, G2 and G3 are
cost repairs. The one thing the shadow lane can decide in under a year is exactly the thing all of
them rest on.

### 7.3 What the shadow would have to log

Per intent, whether or not it fills — a censored row is a row the estate paid to generate:

- `symbol`, `account`, `side`, `trigger_utc`, `entry_utc` (broker-true), `broker_hour`
- `channel_len`, `close_at_trigger`, `channel_extreme`, `break_extension_atr`
- `atr14`, `atr50`, `vol_regime`, and the **stop distance in price**, which is the R denominator
- `requested_price`, `executed_entry`, `executed_stop` — the three fields
  `SLIPPAGE_PRICE_V1.json`'s own capture requirement names, and whose absence is why `cost_r`
  refuses 9 of these 24 symbols today
- realised `spread_at_entry` from the tick, not the bar (the bar `spread` column is the within-bar
  **minimum**, per AH)
- realised commission and **realised swap per rollover**, from the deal record
- exit reason (`stop` / `target` / `time`), exit price, exit UTC, bars held, rollovers crossed
- `mfe_price`, `mae_price` over the life of the position

The first five bullets close the slippage-coverage hole; bullets six and seven make the cost model
falsifiable at the 9.9-month resolution of §7.2. **That is the deliverable to ask the lane for.**

---

## 8. What would survive pre-registration, and what is a scan artifact

Stated explicitly, because this lane scanned 576 cells.

**Would survive** — mechanism identified, holdout-stable, or arithmetic:

- **K1. Breakout entries are not net-positive after broker-true cost**, at any of 576 geometries on
  24 symbols over 12.4 years. 0 cells with a lower bound above zero. Robust to all three intrabar
  rules and to winsorising the loss tail.
- **K2. A breakout expands MFE and MAE together.** The favourable-to-adverse travel ratio improves by
  1.3 %, while the trigger costs 0.13 R. The direct test of the redirect's own stated condition.
- **K3. Total cost in R rises monotonically with horizon** for a fixed-R contract (3.6× from 1 day to
  160 days), because carry is linear in time while the R denominator is fixed. Arithmetic.
- **K4. The rollover-hour cost penalty is FX-class-specific**, ~6.8× in EURUSD's modelled spread,
  absent in metals and indices. Mechanism identified within a single symbol.
- **K5. Widening the stop reduces cost in R proportionally**, 10 of 10 grid × quintile cells.
  Arithmetic.
- **K6. Carry is zero on 16 of 48 D1 symbol-sides and up to 0.43 R/trade on others.** A broker fact.
- **K7. The power statement of §7.1.** A property of the measured dispersion, not a fit.

**Would not survive, and is named here so nobody mines it later:**

- **Every cell in the 576-cell scan, without exception.** The 14 net-positive cells, the 39 with
  significant gross deltas, and the 2 that pass both screens: the trigger delta's sign agreement
  between halves is 37.8 %, below a coin flip.
- **The per-symbol LONG positives** (BTCUSD +0.417, XAUUSD +0.260, ETHUSD +0.181, USDJPY +0.141).
  Secular drift plus a trigger effect that decays 4.2× between halves.
- **The vol-ratio quintile as an entry filter.** It is a cost gradient wearing an edge's clothes, and
  the naive direction is the wrong one (§5.3).
- **BTCUSD SHORT on H4**, the one cross-period-stable cell, as anything other than a shadow-lane
  registration. Its delta is stable; its level is not profitable.
- **The `mx_btcusd` replication of §3** as an independent look. It is the same cell on the same
  prices that the estate already selected.

---

## 9. What I got wrong, and the limits

- **The first version of the paired delta was wrong by 0.37 R and confidently in the wrong
  direction**, because `pivot_table(aggfunc="mean")` silently changed the estimator from a pooled
  per-trade mean to an unweighted mean over clusters. It produced a clean, decisive, wrong kill
  (−0.26 R/trade, 576/576 cells negative) that I nearly wrote up. It was caught by noticing that the
  pooled arm means in a different table disagreed in sign. **The lesson is general: the cluster is
  for the interval, never for the estimator**, and any two aggregations that disagree in sign should
  stop the write-up.
- **I expected the intrabar tie rule to be the driver and it was not** — 0.04–0.65 % of rows. The
  check was worth running and the hypothesis was wrong.
- **The blind control does not control for conditional drift.** It matches the unconditional bar
  population, so it removes a symbol's average drift but not "drift concentrated in the periods when
  breakouts fire". For BTCUSD LONG that is precisely the confound, and the holdout — not the control
  — is what settles it. A better control would resample within trend state; I did not build one.
- **The 9 symbols without price-domain slippage** are charged a pooled TRANSFERRED constant. The
  direction is conservative for the stop-width lever, but those symbols' absolute cost levels carry a
  weaker warrant than the other 15, and `cost_r` itself refuses them.
- **The spread era model is extrapolated** across 2014–2026 from a 2026 reference window. Its own
  `honest_limit` validates it at ratios of 0.78–1.30; several quarters in this window sit outside
  that. 33 % of priced rows carry a MODELLED era class and 27.5 % a non-decidable one (`spread_cov` is on every
  row). A materially different historical spread path would move every absolute net level here,
  though not the breakout-minus-blind delta, which pays the same spread in both arms.
- **The swap term deviates from the authority by up to 0.0116 R** on rollover-night counting at DST
  boundaries. Bounded, one-sided, and small against a 0.13 R mean cost — but not zero.
- **The horizon sweep is one geometry.** Donchian-20, stop 2.0 ATR, target 3 R. The shape of the cost
  curve is arithmetic and generalises; the location of the net optimum at H = 12 does not.
- **No fill model.** Every trigger is assumed to fill at the next open. For a breakout — an order
  competing with everyone else's breakout order — that is optimistic, and the estate's own
  `entry_quality_fill_probability` machinery exists because it is. This biases the study *toward* the
  thesis, which is the right direction for a kill test and the wrong one for anything else.
- **Nothing here was billed against a candidate family**, except the two members declared in §6.1.
  The 576 cells are a population map; they declare no rule and must not be re-mined.

---

## 10. What this concludes, for the owner's question

**Stop predicting direction was right. Exploit magnitude at longer horizons does not follow, and this
study is where that step breaks.**

Lane I's finding stands entirely: magnitude structure is large, monotone, and stable across 13 years
and 24 symbols, while directional structure is empty. The redirect's inference was that a breakout
converts magnitude into money without needing direction. Measured on 190,638 triggers and 13.7 M
trade-outcomes, it does not — because **a magnitude event expands both tails**, and a fixed-risk
contract can only monetise the difference between them. That difference is 1.3 %; the trigger costs
13 %.

The estate has now measured, three independent ways, that this market surface is a fair game gross
and that its entire deficit is cost. Lane I measured it on blind entries. Lane G corroborated it on
the recorded feature set. This study measured it on the one structure that was supposed to be the
exception, and found the same thing with a small real trigger effect that inverts out of sample.

**That is not a dead end, it is a redirection of where the work goes.** Every survivor in this
document is a cost fact: the rollover hour, the stop width, the carry side, the horizon optimum. They
do not simply add — G1 is FX-class-restricted and G2 trades against position sizing — but G2 alone is
worth **+0.03 to +0.07 R/trade** on every contract measured, G1 a further **+0.06 to +0.08** on the
FX cohort, and G3 avoids up to **0.43 R/trade** on the wrong carry side. That is the same order as the
edge the estate has been searching for and has never found, and it is arithmetic rather than bets.
Two of them apply to money that is armed today.

And the forward lane should be pointed at the question it can actually answer. It cannot resolve a
0.02 R/trade edge in 61 years. It can resolve whether the cost model is biased by 0.02 R/trade in ten
months, and every conclusion above rests on that model being right.

---

### Receipts

`magnitude_program_receipts/` — `KILL_TEST_SUMMARY.json` (headline numbers with provenance);
`BREAKOUT_ECONOMICS.csv.gz` (576 + 576 cells); `BREAKOUT_DELTA.csv`; `CELL_SCREEN.csv.gz`;
`HORIZON_SWEEP.csv`, `HORIZON_COST_CURVE.csv`; `ENTRY_HOUR.csv`; `STOP_WIDTH_LEVER.csv`;
`CONDITIONING.csv.gz`; `SYMBOL_CARRY.csv`, `SYMBOL_DELTA.csv`, `SURVIVOR_HOLDOUT.csv`;
`DELTA_TRAIN_TEST.csv`, `STABILITY_{YEAR,SYMBOL,ERA}.csv.gz`; `TIE_RATE.csv`,
`TIE_BOUNDED_DELTA.csv.gz`, `BREAKOUT_NET_{STOP,TARGET}.csv`; `DIAG_{PATH_EXTREMES,ENTRY_GAP,SYMBOL_TRAVEL}.csv`;
`COST_VALIDATION.csv.gz` (the vectorised cost layer against `cost_r`, row by row);
`POWER_TABLE.csv`, `POWER_COST_TABLE.csv`, `POWER_INPUTS.csv`.
Producing scripts under `magnitude_program_receipts/scripts/` (`mp_build`, `mp_cost`, `mp_analyze`,
`mp_diag`, `mp_tie`, `mp_horizon`, `mp_design`, `mp_final`). Seed 20260812 throughout, 1,000
bootstrap draws, cluster = symbol × calendar quarter.

**Inputs, none mutated:**
`/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/deep_universe_h4d1_2014_2026`;
`research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json`;
`research/operations/spread_model_2026_07_29/SPREAD_MODEL_V1.json`;
`docs/audits/fable5-vision-audit-20260725/phase21/cost/SLIPPAGE_PRICE_V1.json`;
`src/costs/model.py`, `src/costs/spread_model.py`, `src/costs/slippage_model.py`,
`src/costs/fx_conversion.py`, `src/utils/broker_clock.py` as the cost and clock authorities.
No live path, no config, no R2-bound file, no VPS, no March 2026 was touched.
