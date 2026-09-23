# d7 — WHAT WOULD HAVE TO BE TRUE for the broad V4 family to pay

Lane d7, wave 19. Inverse reasoning: instead of asking whether it works, solve for the change
each lever would have to deliver, measure what each lever *can* deliver on the same rows, and
give the owner the ratio. Everything below is measured on this machine over whole populations.
Nothing is sampled. The three READ-RESTRICTED windows (jun/aug/sep 2025) were not opened.

**Populations.** Two, both correct, and every number says which.
- **8-window CLEAN roster** — f1's canonical object, reproduced here from `f1_rows/RR_*.json.gz`
  day-restricted to each sealed arm's own trading days: **298,537 honest fills** over
  Oct/Nov/Dec 2025 + Jan/Feb/Mar/Apr/May 2026. Stage 1 reproduces f1 to five decimals
  (gross −0.01327, toll 0.28118, net −0.29445, wr 0.37979, payoff 1.5943).
- **5-window re-walk** — Oct/Nov/Dec 2025 + Apr/May 2026, walked here from the M1 tape with the
  paired side placebo, **181,149 honest fills / 100 day blocks**. The five whose regenerated
  rosters survive on disk. Its shipped-cell gross (−0.01200) matches the 8-window CLEAN figure
  (−0.01327) to 0.0013 R, which is the cross-check that the two populations are the same object.

**Verdict axis.** §2 (the cost lever is arithmetically impossible) is **USAGE, and closed**.
§3 (exit geometry is worth +0.083 R and 89–113 % of it is a coin flip) is **SIGNAL**. §4 (the
direction call is significantly worse than its own mirror where the entry price actually
existed) is **SIGNAL**. §5 (two free repairs; the second is new) is **USAGE**, repairable, and
takes the family's gross across zero for the first time. §6 (no ex-ante rule reaches the bar
out of sample) is **SIGNAL**. §8 (14.4 years to resolve the taken book) is **NEITHER** — it is
an epistemic fact about the decision.

---

## 0. THE ANSWER, IN SIX SENTENCES

**Solve the algebra and the cost lever dies first, on arithmetic alone.** For the book to break
even the toll must fall to the gross; the gross is **−0.01327 R/trade**, so the required toll is
**negative**. A free broker — a 100 % cost reduction, the physical limit of every engineering
repair available — leaves the book at **−0.01327 R/trade**. There is no transaction-cost
programme that makes this family profitable.

**Every other lever resolves to the same quantity: directional content, and the family has
less than none.** Against its own exactly-paired mirror — same rows, same fill bars, same risk
distances, same toll, adverse and favourable swapped — the family books **−0.04765 R/trade**
(CI95 [−0.0742, −0.0197]); restricted to the at-market rows whose entry price was actually
available in the decision bar, **−0.04230** (CI95 [−0.0658, −0.0207], n = 77,126). **Taking the
opposite side of every signal is worth about +0.05 R/trade — and still loses 0.27.**

**One new repair is worth taking anyway.** POI candidates whose level is already at market at
the decision instant (11,021 rows, 6.1 % of clean fills) book **−0.20415** gross against a mirror
booking **+0.22389**. Dropping them — free, no new data, the same shape of defect as f1's
`current_breaker_re_entry` — takes the clean roster's gross from **−0.01200 to +0.00044**, the
first non-negative gross this family has ever recorded, **against a toll of 0.30785.**

---

## 1. THE BASELINE ALGEBRA, EXACTLY

CLEAN roster, 8 windows, 298,537 honest fills, target 2.0R, h1 broker-true cost.

| quantity | symbol | value |
|---|---|---|
| gross expectancy | G | **−0.01327** R/trade |
| broker toll | C | **+0.28118** R/trade |
| net | G−C | **−0.29445** R/trade |
| win rate | p | 0.37979 |
| mean winner | a | 1.43652 R |
| mean loser | b | 0.90105 R |
| payoff | a/b | 1.5943 |
| breakeven win rate, **gross** | b/(a+b) | 0.38547 → short **0.568 pp** |
| breakeven win rate, **net** | (b+C)/(a+b) | **0.50575** → short **12.597 pp** |
| toll in price terms | | **3.002 bps**, range 2.92–3.15 over 8 windows (**±3.9 %** — a fee schedule) |
| median risk distance | d | **9.28 bps** |
| toll as a share of one R | C | **13.95 %** |
| exit mix | | stop 52.86 %, target 22.48 %, horizon 24.65 % |
| loser composition | | **85.24 % of losers are hard stops at exactly −1.0R**; the soft 14.76 % average −0.330 |

Per window the clean gross runs **−0.0355 … +0.0189** (April 2026 positive) and the toll
**0.196 … 0.331**. The gross moves 0.054 R across eight months; the toll moves 0.135 R. **The
variance in this book is the toll's, not the signal's.**

---

## 2. THE FOUR SINGLE LEVERS, SOLVED

Each solved for net = 0 holding everything else fixed. `required / plausible` uses a **measured**
denominator, never an assumed one; §6 and §7 derive them.

| # | lever | required change | as a multiple | measured plausible change | **ratio** | type |
|---|---|---|---|---|---|---|
| **L1** | win rate | 0.37979 → **0.50575** = **+12.597 pp** | ×1.332 | **+0.51 pp** — best out-of-sample lift any rule built from the system's own observables achieves (§7) | **24.5×** | research |
| **L2** | winner size | a 1.4365 → **2.2118**; payoff 1.594 → **2.455** | ×1.540 | the entire 56-cell exit-geometry surface moves gross **+0.11610** (§3) — and **89–113 % of it is reproduced by a coin flip** | **2.60× on gross; unbounded on attributable value** | engineering, not attributable |
| **L3** | loser size | b 0.9011 → **0.4263** = **−52.7 %**, *with zero win-rate loss* | ×0.473 | measured on real paths: an exit at 0.426R **kills 37.6 % of the winners** | **infeasible as specified** | engineering |
| **L4** | cost | C 0.28118 → **−0.01327** | **negative** | 100 % (a free broker) | **IMPOSSIBLE** | engineering |

**L4 is the load-bearing row and it is pure arithmetic.** The required toll is below zero, so no
cost reduction of any size closes the gap. Stated as a bound: **the maximum value of every
transaction-cost, broker-selection, spread-timing and slippage repair in this programme,
combined and taken to perfection, is +0.28118 R/trade — and it lands the book at −0.01327.**

**L3 is feasible in the algebra and dead in the mechanism.** Cutting losers to 0.426R with the
position size held at the original risk distance (so the toll in R does not move) exactly closes
the gap — but the measurement of what such an exit does to the winners is §3, and it removes
more than it saves at every threshold.

### 2.1 The joint isoquant — because levers must never be summed

Net = 0 requires `p·a − (1−p)·b = C`. Cutting the toll and lifting the win rate together:

| toll cut | toll after | win rate needed | vs today |
|---:|---:|---:|---:|
| 0 % | 0.28118 | 0.50575 | +12.597 pp |
| 25 % | 0.21089 | 0.47568 | +9.589 pp |
| 50 % | 0.14059 | 0.44561 | +6.582 pp |
| 75 % | 0.07030 | 0.41554 | +3.575 pp |
| 90 % | 0.02812 | 0.39749 | +1.771 pp |
| **100 % (free broker)** | 0.00000 | 0.38547 | **+0.568 pp** |

**Even at zero transaction cost the family is still 0.568 pp short of its own payoff-implied
breakeven.** After the two free repairs of §5 that residual closes — gross +0.00044 — which is
the exact and complete statement of what would have to be true: **this family is profitable in
one configuration only, the one where trading is free.**

---

## 3. THE EXIT-GEOMETRY LEVER, PRICED JOINTLY AND CONTROLLED

L2 and L3 are the same lever seen from two ends, so they were swept as one surface: soft loser
cut `x ∈ {1.0 … 0.10}` × target `tr ∈ {1.0 … 12.0}`, 56 cells, on the 5-window re-walk
(181,149 fills), honest-limit fill, conservative tie, **position size held at the original risk
distance so the toll in R is identical in every cell**. `d7_exit2.py`, `D7_STAGE5.json`.

Gross, real (the shipped cell is x=1.0 / tr=2.0):

| x \ tr | 1.0 | 1.5 | **2.0** | 3.0 | 5.0 | 8.0 | 12.0 |
|---|---|---|---|---|---|---|---|
| **1.0** | −0.02788 | −0.01408 | **−0.01200** | −0.00431 | +0.00291 | +0.01039 | +0.01459 |
| 0.50 | −0.00518 | +0.00867 | +0.01136 | +0.01856 | +0.02373 | +0.02808 | +0.03064 |
| 0.30 | +0.01929 | +0.03329 | +0.03624 | +0.04391 | +0.04969 | +0.05392 | +0.05501 |
| 0.20 | +0.03829 | +0.05215 | +0.05477 | +0.06397 | +0.07066 | +0.07520 | +0.07692 |
| **0.10** | +0.06761 | +0.08067 | +0.08313 | +0.09237 | +0.09836 | +0.10196 | **+0.10410** |

**The surface is real: the best cell is worth +0.11610 R/trade of gross over the shipped
geometry.** It is also the largest single non-oracle improvement measured anywhere in this wave.
And it is worth **38.4 %** of the 0.30212 toll, so it does not close the gap on its own. (The
narrower 42-cell first pass, `D7_STAGE4.json`, stopped at x = 0.20 / tr = 5.0 and reported
+0.0827 = 27.4 %; the optimum is on the extended grid's boundary, so **the surface is still
rising at x = 0.10, tr = 12.0** and the true ceiling is higher than either figure — which does
not help, because §3's control applies to every cell equally.)

**Then the control.** PLACEBO-SIDE keeps every row, every fill bar, every risk distance and the
identical toll, and only swaps adverse for favourable:

| x \ tr | 1.0 | **2.0** | 5.0 | 12.0 |
|---|---|---|---|---|
| **1.0** real | −0.02788 | **−0.01200** | +0.00291 | +0.01459 |
| **1.0** placebo | +0.01527 | **+0.03564** | +0.05652 | +0.07450 |
| **0.10** real | +0.06761 | +0.08313 | +0.09836 | +0.10410 |
| **0.10** placebo | +0.10686 | +0.13044 | +0.15313 | +0.16158 |

**The placebo is higher at all 56 cells.** It captures **89.5 %–438.7 %** of every gain over the
shipped cell (median ≈ 112 %), and `real − placebo` is negative at every cell, from −0.0393 to
−0.0693. Day-block bootstrap, 1,500 draws over 100 blocks, at four representative cells:

| cell | real | placebo | signal | CI95 |
|---|---:|---:|---:|---|
| x1.0 tr2.0 (shipped) | −0.01200 | +0.03564 | **−0.04765** | [−0.07450, −0.01951] |
| x0.5 tr2.0 | +0.01136 | +0.06520 | **−0.05385** | [−0.07284, −0.03430] |
| x0.2 tr5.0 | +0.07066 | +0.12837 | **−0.05771** | [−0.07623, −0.03772] |
| x0.1 tr12.0 | +0.10410 | +0.16158 | **−0.05748** | [−0.07805, −0.03558] |

**So the exit lever is real and it is not the family's.** A tight stop with a far target is worth
+0.116 R/trade to anybody trading those instruments at those instants in either direction — it is
the payoff geometry of the tape, not information. This is f2's finding (the exit rung is 98.2 %
coin-flip reproducible) reproduced on a *fixed, implementable* contract rather than an oracle,
and sharpened: here the coin flip does not merely match the real arm, **it beats it at every
cell.**

**The winner-kill measurement that closes L3**, from the same walk: of the trades that reach 2R
before their 1R stop, a soft exit at x kills

| x | 0.75 | 0.60 | 0.50 | **0.426** | 0.30 | 0.20 |
|---|---|---|---|---|---|---|
| winners killed | 14.28 % | 24.32 % | 31.63 % | **37.63 %** | 48.42 % | 57.70 % |

L3 asked for b → 0.4263 **with zero win-rate loss**. The measurement is 37.63 % of winners lost.
That is why the joint surface never reaches the toll even though the single-lever algebra said
the cut was feasible.

---

## 4. THE DIRECTION TEST, WITH THE ARTIFACT REMOVED

Stage 7 ran the paired placebo under both fill contracts on the *same* at-market rows and days,
and the two answers disagreed in sign:

| contract | n | real | placebo | **signal** | CI95 | windows + |
|---|---:|---:|---:|---:|---|---|
| **C0 market** (no fill condition) | 83,433 | +0.02306 | +0.00528 | **+0.01777** | [−0.00310, +0.03905] | 3/5 |
| **C1 honest limit** (the shipped contract) | 82,576 | −0.00671 | +0.03010 | **−0.03681** | [−0.05775, −0.01527] | 0/5 |

93.4 % of these rows fill in the **first** bar, where the two contracts are identical by
construction — so the entire 0.055 R gap is carried by the other 6.6 %. Bucketing by fill lag
(`d7_filllag.py`) shows exactly what those rows are:

| at-market bucket | n | C1 real | C1 signal | **C0 real** | **C0 signal** |
|---|---:|---:|---:|---:|---:|
| lag 0 — entry available in the decision bar | 77,126 | −0.00941 | −0.04230 | −0.00941 | −0.04230 |
| lag 1–5 | 3,434 | −0.02333 | −0.05555 | −0.00673 | +0.02897 |
| lag 6–30 | 1,389 | +0.10929 | +0.19835 | **+0.38347** | +0.83615 |
| lag 31+ | 627 | +0.16038 | +0.22081 | **+1.04910** | +1.87203 |
| **never fills** | 0 | — | — | **+1.73228** | +2.69913 |

**The positive market-fill signal is an artifact of 2,873 rows (3.4 %) whose emitted entry price
was never available.** They contribute **+0.0557** of the +0.01777; the 93.4 % that could
actually be entered contribute **−0.0391**. This is f1's phantom-fill hazard (*"walking POI limit
candidates as market orders manufactures +1.54 R/trade"*) appearing inside the **at-market**
cohort, where nobody had looked for it.

**The clean number, and it is the lane's headline on the signal axis:**

> On the **77,126** at-market rows whose entry price existed in the decision bar — no fill
> selection, no phantom credit, market and limit contracts identical — the broad family's
> direction call books **−0.00941** gross while its own exact mirror books **+0.03289**.
> **Signal −0.04230, CI95 [−0.06583, −0.02066], p(signal ≥ 0) = 0.0000, 0 of 5 windows positive.**

**This corrects a foundation number.** f2's `real − PLACEBO-SIDE = +0.00315 ± 0.01026` is
computed at a market fill over all at-market rows, which is the construction that includes the
never-touched rows; on the five windows this lane re-walked, that construction reproduces
(+0.01777) and decomposes as above. **f2's conclusion is unchanged and strengthened** — the
signal was already 32× short of the bar; it is now measurably on the wrong side of zero.

---

## 5. THE TWO FREE REPAIRS — and the first non-negative gross this family has recorded

5-window re-walk, 203,427 honest fills, paired placebo, day-block bootstrap (`D7_STAGE9.json`).

| cohort | n | gross | toll | net | placebo | **signal** | CI95 |
|---|---:|---:|---:|---:|---:|---:|---|
| ALL FILLS | 203,427 | −0.08973 | 0.30114 | −0.39088 | +0.18652 | −0.27626 | [−0.31407, −0.23641] |
| **− `current_breaker_re_entry`** (f1's repair) | 181,149 | −0.01200 | 0.30212 | −0.31412 | +0.03564 | −0.04765 | [−0.07423, −0.01970] |
| **− POI level already at market** (new) | 170,128 | **+0.00044** | 0.30785 | −0.30741 | +0.02345 | **−0.02301** | [−0.04998, +0.00434] |

The new defect, isolated:

| POI cohort | n | gross | toll | placebo | signal | CI95 |
|---|---:|---:|---:|---:|---:|---|
| **level already at market** (fills in the decision bar) | **11,021** | **−0.20415** | 0.21364 | **+0.22389** | **−0.42804** | [−0.50638, −0.34989] |
| genuine pullback (fills later) | 87,552 | **+0.00719** | 0.28538 | +0.01718 | −0.00999 | [−0.05794, +0.04107] |

**A fair-value-gap or order-block retest whose level is already trading is not a retest — it is a
broken level, and the family is on the wrong side of it by 0.43 R.** It is 11.2 % of POI fills
and 6.1 % of clean fills. It is the same shape as `current_breaker_re_entry`, which f1 measured
as 68.0 % born past its own stop: **both are candidates that are dead at emission**, and between
them they carry every statistically-significant negative in this population. Dropping both is
free, needs no new data, and leaves a residual (`POI_GENUINE_PULLBACK` signal −0.00999,
CI crossing zero) that is honestly indistinguishable from a coin flip.

**And it changes nothing about the verdict.** Gross **+0.00044** against a toll of **0.30785**.
The repair is worth +0.01244 R/trade — **4.0 % of the toll**.

---

## 6. IS THERE A CONDITIONER? THE REQUIREMENT, AND WHAT IS ATTAINABLE

**The requirement**, model-based (score = ρ·probit(rank of true net) + √(1−ρ²)·N(0,1), bisected
on ρ, 3 noise draws per evaluation, whole 298,537-row clean population):

| selection rate | oracle net | required ρ | **required AUC** |
|---|---:|---:|---:|
| 50 % | +0.7497 | 0.302 | 0.6372 |
| 10 % | +1.9015 | 0.135 | 0.5607 |
| 1 % | +1.9718 | 0.085 | 0.5384 |
| 0.048 % (the system's own rate) | +1.9888 | 0.061 | 0.5272 |

**What is attainable**, out of sample, train Oct 2025–Jan 2026 → test Feb–May 2026:

| ex-ante score | test AUC (winner vs loser) | Cohen's d equivalent |
|---|---:|---:|
| risk distance alone | 0.5292 | 0.104 |
| train-fitted (symbol × family) **net** | 0.5169 | 0.060 |
| train-fitted (symbol × family) **gross** | **0.5031** | **0.011** |

**The model-based requirement and the attainable number are the same size, which is precisely why
the model must not be trusted here** — so the question was re-asked without a model. Six real
ex-ante rules were fitted on Oct–Jan and *run* on Feb–May at every selection rate
(`d7_empirical.py`, `D7_STAGE3.json`). Selected rows, realised:

| rule | retain 25 % | 10 % | 5 % | **2 %** | 1 % | 0.5 % |
|---|---:|---:|---:|---:|---:|---:|
| S1 cheapest ex-ante toll | −0.07014 | −0.07623 | −0.12273 | −0.14251 | −0.10576 | −0.05806 |
| S2 widest risk distance | −0.15394 | −0.13114 | −0.12698 | −0.16710 | −0.17919 | −0.23126 |
| S3 train-fitted gross | −0.26809 | −0.37194 | −0.42174 | −0.45592 | −0.29535 | −0.10664 |
| S4 train-fitted net | −0.10648 | −0.08710 | −0.06003 | −0.07568 | **−0.03962** | −0.07041 |
| **S5 pred gross − pred toll** | −0.09263 | −0.06838 | −0.07577 | **−0.04101** | −0.05413 | −0.04085 |
| S6 random control | −0.25488 | −0.23861 | −0.23171 | −0.23176 | −0.22872 | −0.24440 |

**Zero of 66 out-of-sample cells is positive.** The best cell with n ≥ 200 is S4 at 1 %
(n = 1,494): net **−0.03962**, t = −1.47, win rate 0.4846 against a required 0.5072 — still
**2.26 pp short**. Under a rolling refit (train on everything before the test month, four
folds, S5) **1 of 16 cells is positive** (Feb 2026 at 10 %, +0.0118).

**And the mechanism is legible in S3 versus S1.** Ranking on train-fitted *gross* does lift the
gross out of sample (−0.0087 → **+0.0802** at 1 %) — **and it lifts the toll with it**
(0.2551 → 0.3756), because the cells with gross are the tight-stop cells where a fixed price
toll is a large share of R. Ranking on *cheapness* does the reverse. **Every rule that finds edge
buys toll; every rule that avoids toll loses edge.** That is the coupling, it is structural, and
it is why S5 — which prices both — is the only rule that gets within 0.04 of zero and still never
crosses it.

**Persistence, re-measured on this population** (24 symbols / 9 families, train → test Spearman):

| | cost rank | gross rank |
|---|---:|---:|
| by symbol | **+0.713** | **−0.077** |
| by family | **+1.000** | +0.400 (9 cells) |

This reproduces the wave's 0.826 / 0.024 on the correct object: **cost is a persistent property of
an instrument, edge is not.** Acting on it: selecting the 11 symbols with positive train gross
makes the test gross **worse** (−0.01203 vs −0.00873).

---

## 7. THE INSTRUMENT QUESTION — "if it traded only where the toll is cheapest"

**First, the dispersion is not what it looks like.** The R-toll disperses **11.5×** by family and
**5.2×** by symbol — but the *price* toll disperses only **1.6×** by family (2.203–3.523 bps) and
is flat to ±3.9 % across eight months. The R-toll dispersion is **the generator's own stop
width**, not a fee schedule:

| family | toll (R) | toll (bps) | median d (bps) | gross |
|---|---:|---:|---:|---:|
| `regime_transition_break` | **0.05474** | 3.201 | 44.30 | −0.01142 |
| `session_open_range_break` | 0.08901 | 2.203 | 18.12 | −0.00996 |
| `liquidity_sweep_reclaim` | 0.29879 | 2.960 | 7.93 | +0.00273 |
| `structural_distance_extreme` | **0.63022** | **2.646** | **3.17** | +0.00687 |

The cheapest family in R pays a **higher** price toll than the most expensive one. Same for
symbols: `EURGBP` costs 1.562 bps and 0.53968 R (d = 3.73); `ETHUSD` costs 12.739 bps and
0.50240 R (d = 28.48). **"Trade where the toll is cheapest" is, mechanically, "trade where the
stop is widest."**

**Second, the frontier, out of sample.** Predictor = each symbol's Oct–Jan median price toll ÷
this row's own risk distance, applied to Feb–May and never refitted:

| retain | n | toll (R) | gross | net | win rate | **required** | gap | median d |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 % | 149,388 | 0.25505 | −0.00873 | −0.26378 | 0.3817 | 0.4954 | −11.37 pp | 10.35 |
| 50 % | 74,694 | 0.08211 | −0.01973 | −0.10184 | 0.3985 | 0.4488 | −5.03 pp | 14.83 |
| **25 %** | 37,347 | **0.04726** | −0.02289 | **−0.07014** | 0.4094 | 0.4485 | **−3.92 pp** | 23.78 |
| 10 % | 14,939 | 0.02492 | −0.05131 | −0.07623 | 0.4145 | 0.4663 | −5.18 pp | 40.62 |
| 5 % | 7,469 | 0.01631 | −0.10642 | −0.12273 | 0.4018 | 0.5034 | −10.16 pp | 56.58 |
| 1 % | 1,494 | 0.00822 | −0.09755 | −0.10576 | 0.4404 | 0.5612 | −12.08 pp | 92.65 |

**The answer to "what would it need in edge terms": +0.04726 R/trade where −0.02289 exists — a
shortfall of 0.07014 R/trade, or +3.92 pp of win rate.** That is the smallest requirement
anywhere in this estate, **13.4× smaller than the headline 12.597 pp** — and it is still **7.62×**
the largest out-of-sample win-rate lift the system's own observables produce (+0.51 pp, §6).

**The frontier is non-monotone and that is the ceiling.** Net bottoms at retain 25 % and gets
*worse* as the cohort gets cheaper: the toll keeps falling (0.047 → 0.008) but the gross falls
faster (−0.023 → −0.098). Sorting on **realised** cost — an upper bound no ex-ante rule can beat
— has the same shape and the same floor (best −0.04883 at retain 10 %). **Widening runs out of
road before the toll runs out**, which is f1's decile finding reproduced out of sample under an
implementable rule.

---

## 8. THE OWNER TABLE — for this to pay, X must move by Y

**In account terms.** At the arm's 0.1 % risk unit and the measured cadence of **63.4
trades/month**, the taken book books **−0.1224 %/month** (−0.98 % over eight months). An 8 %
phase-1 target inside six months requires **+0.2104 R/trade net**; the taken set delivers
**−0.01932**. **The move required is +0.2297 R/trade — 3.1× the arm's entire cost model,
1.5× the h1 broker-true toll, and 4.8× the family's whole measured directional information
content (|signal| ≈ 0.048).**

| # | what must move | by how much | is it possible? | evidence |
|---|---|---|---|---|
| 1 | **Toll → 0** (free broker, perfect execution) | −100 %, the physical limit | **Not sufficient.** Lands at −0.01327; after §5's repairs, +0.00044 | §2, §5 |
| 2 | **Win rate**, whole population | **+12.597 pp** | **No.** Best OOS-validated lift from the system's own structure is +0.51 pp → **24.5×** | §6 |
| 3 | **Win rate**, cheapest-toll quartile | **+3.92 pp** — the smallest requirement in the estate | **No, and it is the closest miss.** 7.62× the attainable lift; 0 of 66 OOS cells positive | §7, §6 |
| 4 | **Exit geometry** | worth +0.30212 | **No.** The whole 56-cell surface is worth +0.11610 (38.4 %), and 89–113 % of it is a coin flip — the placebo is higher at **56 of 56 cells** | §3 |
| 5 | **Loser size** b → 0.4263 with no winner loss | −52.7 % | **No.** Measured: kills 37.6 % of winners | §3 |
| 6 | **Direction call** ≥ its own mirror | +0.04230 just to reach parity | **Not established.** It is significantly *below* the mirror where the entry existed | §4 |
| 7 | **Drop the two dead-at-emission cohorts** | +0.01244 R/trade (gross → +0.00044) | **Yes — free, today.** But it is 4.0 % of the toll | §5 |
| 8 | **Know whether the taken book already pays** | 10,951 trades | **No.** 172.8 months = **14.4 years** at 63.4 trades/month | §8.1 |

### 8.1 The number that ends the argument about live evidence

The taken set books net **−0.01932 ± 0.04789** (n = 464, sd 1.0316) — a deficit of 0.01932
against a standard error 2.5× larger than itself. For the 95 % interval to shrink to the size of
its own deficit takes **10,951 trades**; to half of it, **43,803**. At the measured **63.4
trades/month** that is **172.8 months — 14.4 years — of live trading to learn whether this book
is profitable**, and 57.6 years to measure it well. **The taken book cannot be adjudicated by
running it.** Any decision to keep it live has to be justified by something other than the
expectation of learning from it.

### 8.2 Engineering problem or research problem

- **Engineering, and already at its ceiling:** cost (L4 — bounded above by 0.281 and the bound is
  not enough), exit geometry (L2/L3 — the surface is swept and the best cell is a coin flip),
  the two dead-at-emission repairs (§5 — do them, they are free and they are the only rows in
  this population with a significant signal).
- **Research, and the only remaining question:** does a conditioner exist that separates the
  ±0.04 gross band into a cell large enough to pay 0.047–0.281 R? Six rules over four rolling
  folds say no (1 of 16 cells positive, 0 of 66 net-positive). The requirement in its friendliest
  form is **+3.92 pp of win rate inside the cheapest quartile**; the best measured OOS answer is
  **+0.51 pp**.
- **Neither:** the 14.4-year resolution time. That is not a lever, it is the reason the decision
  cannot be deferred to the forward record.

---

## 9. LIMITS — read before citing

1. **Two populations, and the placebo work is the 5-window one.** §1, §2, §6, §7 are the 8-window
   CLEAN roster (298,537 fills). §3, §4, §5 are the 5-window re-walk (181,149–203,427 fills;
   Oct/Nov/Dec 2025 + Apr/May 2026) because only those regenerated rosters survived on disk.
   Jan/Feb/Mar 2026 are **absent from every placebo number here**, and they are three of the four
   months the estate has looked at most. The two populations agree at the shipped cell to 0.0013 R.
2. **PLACEBO-SIDE inherits the real side's fill bar.** For at-market rows this is immaterial
   (93.4 % fill in the decision bar); for POI rows the mirror is being handed an entry instant its
   own limit would not have produced. §4's headline is therefore quoted on the at-market
   entry-available cohort, where the objection does not apply.
3. **The toll is one broker's measured schedule (FTMO, h1 four-term, hour-aware) applied to all
   eight windows**, including Oct–Dec 2025. It is flat to ±3.9 %, which is evidence the schedule is
   stable, not proof it was identical in 2025.
4. **The conditioner requirement in §6 is model-based** (a Gaussian-copula noisy oracle) and its
   answer disagrees with the model-free one. The empirical curves, not the required-AUC table, are
   the finding; the table is published because the disagreement is itself informative.
5. **The horizon is 120 M1 bars** throughout; 24.65 % of clean exits are horizon truncations. A
   longer horizon raises the exit surface and raises the placebo with it.
6. **§5's second repair is a rule about the candidate at emission**, measured on 5 windows. It has
   not been run on Jan/Feb/Mar and it has not been proposed to the live book — nothing in this
   population is the live W7 sleeve book.
7. **The three sealed windows were not opened**, not generated, not referenced.
8. **`risk.min_rr` = 1.5 is the generator's; 2.0R is the downstream policy target** and is what
   every number here walks, matching f1 and f2.

---

## 10. RECEIPTS

| artifact | what |
|---|---|
| `d7_RESULT.json` | every table above, machine-readable, plus the owner table |
| `d7/D7_STAGE1.json` | baseline algebra + all four single-lever solves, 6 cohorts, per window, per family, per symbol |
| `d7/D7_STAGE2.json` | conditioner requirement, cheapest-toll frontier (ex-ante + oracle), persistence, both isoquants, resolution, account terms |
| `d7/D7_STAGE3.json` | six ex-ante rules × 11 selection rates, out of sample; rolling refit; best cell by window |
| `d7/D7_STAGE4.json` | first exit surface (42 cells) + winner-kill fractions |
| `d7/D7_STAGE5.json` | extended exit surface (56 cells) with the paired side placebo + day-block CIs |
| `d7/D7_STAGE6.json` | placebo split by family and by POI/at-market + fill-lag census |
| `d7/D7_STAGE7.json` | the fill-contract discriminator (C0 vs C1 on the same rows) |
| `d7/D7_STAGE8.json` | fill-lag buckets — where the phantom signal lives |
| `d7/D7_STAGE9.json` | the two free repairs, priced, with bootstrap CIs |
| `d7_solve.py` → `d7_frontier.py` → `d7_empirical.py` → `d7_exit.py` → `d7_exit2.py` → `d7_exit3.py` → `d7_fillctl.py` → `d7_filllag.py` → `d7_final.py` | dependency order |

Reproduce: `python3 d7_solve.py` (reads `f1_rows/`, ~4 min), then the rest in order. The exit
walks need the regenerated rosters at `/tmp/f1/roster_<yyyymm>/`; rebuild any missing month with
`f1_gen_rosters.sh` (~5 min/month).
