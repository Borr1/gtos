# h6 — price the repaired contract JOINTLY, and find its best form

Lane key `h6`. Wave-19 discovery. Every number below is measured on this machine from the
scripts named in §9; nothing is estimated. Machine-readable companion: `h6_RESULT.json`,
plus eleven receipt artifacts listed in §9.

---

## 0. The answer in seven lines

| | measured |
|---|---|
| **Swarm headline reproduced?** | **Yes — digit for digit, on all seven published numbers, through an independently written scorer** (§1) |
| **Best joint form of the contract** | `k=30 · trail 0.10 · no target · stop −2R · close at 60 min` — gross **+0.087644 R/trade at t +34.52**, **2.286×** the swarm's +0.038342 (§2) |
| **Does any parameterisation close the 2.457 bps gap?** | **Not on the cohort.** 0 of 25,800 contracts is net-positive ungated. Best ratio 0.4205 bps-for-bps, up from 0.094 (§3) |
| **…on any cell?** | **Yes, on 8.7 % of it** — three instruments whose hour-true round trip is ≤ 0.60 bps: **edge : cost 2.475**, n 3,807, all three months (§6) |
| **The headline's exit contract does not survive its own audit** | Under the estate's **ratified honest-trail bound** the swarm's gross goes **+0.038342 → −0.045672** and **24 of 24 gross-positive instruments → 0 of 24**. The trail's bar-resolution premium is **+0.084014 R/trade = 2.19× the entire headline** (§5.2) |
| **Placebo** | The same contract on an entry instant shifted **+60 min** books **+0.038659 at t +12.64** against the real +0.038418 at t +12.32, on the same 43,428 rows (§5.3) |
| **The cell that survives all of it** | `k=3 · plain −1R stop · no trail · no target · close at 120 min`, hour-true cost ≤ 0.60 bps. **+0.068525 R/trade net, ratio 2.475, +260.9 R over 63 days, beats 7 of 7 placebo anchors, trail premium 0.000000 by construction** (§6.1) |

**One sentence.** The repaired contract reproduces exactly and then fails two audits the swarm
did not run — its cost basis is 21.2 % too cheap and its exit rule manufactures 2.19× its own
headline out of bar resolution — but underneath both there is a real, placebo-controlled,
three-month cell where edge is 2.475× the broker toll, and it is a *no-trail* contract on the
three cheapest instruments.

---

## 1. Reproduction — exact (task 1)

Two independent paths to the same numbers. First, a fresh scorer over the shipped at-market
files (`h6_01_repro.py`). Second, a from-scratch numpy walk over M1 bars re-materialised out of
the true-UTC source (`h6_02_build_cache.py` + `h6_lib.py`), which never reads the swarm's
`K{k}_{contract}` columns at all.

| quantity | published (`E_ATMKT_POOLED_V1.json`, `e-stack_RESULT.md` §7.2/§7.5) | h6 |
|---|---:|---:|
| n | 43,755 | **43,755** |
| gross R/trade | +0.038342 | **+0.038342** |
| t(gross) | +12.345001 | **+12.345001** |
| cost R/trade | 0.181834 | **0.181834** |
| net R/trade | −0.143492 | **−0.143492** |
| t(net) | −44.876210 | **−44.876210** |
| instruments gross-positive | 24 / 24 | **24 / 24** |
| instruments net-positive | 1 / 24 (GER40) | **1 / 24** |
| days gross-positive | 53 / 63 | **53 / 63** |
| edge bps / cost bps / ratio | 0.231 / 2.457 / 0.094 | **0.231192 / 2.457133 / 0.094090** |
| Spearman(net, cost) | −0.980 | **−0.980000** |
| cost explains net (Pearson R²) | 89.65 %¹ | **97.64 %** |

¹ the synthesis's 89.65 % is its own cross-sectional variance decomposition; the plain
Pearson R² of net on cost across the 24 instruments is 0.9764 (r = −0.98813). Both say the
same thing.

**Scorer agreement, recomputed from raw bars, not copied:** the h6 walk reproduces all four
shipped columns on **100.000 % of 43,755 rows each**, max |diff| **5.0e-09** (the shipped
files' own 8-decimal rounding) — `K5_TRAIL025`, `K0_INC`, `K0_TRAIL025`, `K5_INC`
(`H6_VALIDATE_V1.json`). A float32 path cache flips 1.14 % of trail verdicts; the cache is
float64 for this reason and the note is left here so nobody repeats it.

---

## 2. The joint sweep (task 2)

**28,800 contracts × 4 cost-gate populations = 103,200 scored cells** (`h6_04_sweep.py`,
869 s). Axes: `k ∈ 16 delays · trail ∈ 10 · target ∈ 6 · stop ∈ 5 · maxbars ∈ 6`.

### 2.1 The optimum, and the fact that matters more than the optimum

| | k | trail | target | stop | maxbars | n | gross | t(gross) | cost | net | ratio_R | ratio_bps | trunc |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| shipped (`k=0`, 2R/−1R) | 0 | — | 2.0 | −1.0 | — | 43,755 | −0.065576 | −11.79 | 0.18183 | −0.247410 | −0.361 | −0.444 | 0.316 |
| swarm repaired | 5 | 0.25 | — | −1.0 | — | 43,755 | +0.038342 | +12.35 | 0.18183 | −0.143492 | 0.2109 | 0.0941 | 0.063 |
| **h6 joint optimum** | **30** | **0.10** | **—** | **−2.0** | **60** | 43,633 | **+0.087644** | **+34.52** | 0.18156 | **−0.093913** | **0.4827** | **0.4205** | 0.118 |

**Of 25,800 ungated contracts, 21,263 (82.4 %) are gross-positive and ZERO are net-positive.**
The optimum is 2.286× the swarm's gross and lifts the edge:toll ratio 4.47× — and still loses
0.094 R on every trade.

### 2.2 Ablation — MARGINAL, not standalone

`standalone` = the shipped contract with that one axis moved to its optimal value.
`marginal` = the optimum with that one axis moved back to its shipped default.

| axis | shipped → optimum | standalone ΔNet | **marginal ΔNet** | standalone ΔGross | marginal ΔGross |
|---|---|--:|--:|--:|--:|
| `trail` | none → 0.10 | +0.071447 | **+0.077955** | +0.071447 | +0.077955 |
| `k` | 0 → 30 | +0.060180 | **+0.071373** | +0.059903 | +0.071096 |
| `stop` | −1.0 → −2.0 | **−0.018234** | **+0.011857** | −0.018234 | +0.011857 |
| `target` | 2.0 → none | +0.018579 | +0.004185 | +0.018579 | +0.004186 |
| `maxbars` | none → 60 | +0.001213 | **+0.000079** | +0.001213 | +0.000080 |
| **sum** | | **+0.133185** | **+0.165449** | | |
| **joint gain** | | **+0.153497** | | | |

**h6-F1 — the contract's own axes are COMPLEMENTS; the wave-1 levers were substitutes.**
The five axes' standalone values sum to **−15.25 %** of the joint gain (they under-count), and
their leave-one-out marginals over-count by only **7.8 %**. The six wave-1 levers double-counted
**66.8 %** (`e-stack` §4.1). Opposite sign, and it is mechanical: the wave-1 levers were six
views of one quantity (`mkt_r`), while entry timing, trail distance and stop distance act on
different objects.

**h6-F2 — widening the stop flips sign between standalone and joint.** `stop −2.0` alone is
worth **−0.018234**; at the optimum it is worth **+0.011857**. It corroborates the estate's
"stop width is a bet-size dial, not an edge dial" (the ratio is invariant to a pure rescaling)
while showing the dial interacts with the trail. Note the risk normalisation: at `stop −2.0`
each trade risks two declared R, so the optimum's net is **−0.046962 per unit of risk actually
committed**, against the swarm's −0.143492.

**h6-F3 — `k=5` is not the best delay even inside the swarm's own contract.** Gross by k at
TRAIL025: k=0 −0.022470 · k=1 +0.030002 · k=2 +0.036782 · **k=5 +0.038342** · **k=8 +0.046035
(t 14.157)** · k=15 +0.037852 · **k=30 +0.044512 (t 14.311)**. The published k=5 leaves
**+0.0077 R/trade (20 %)** on the table.

### 2.3 The fourth component the brief named is identically zero

**h6-F4 — the fill floor cannot act on the live-expressible cohort, in any month.**
`execution_fill_probability` takes exactly **two** values here — 0.92 (28,512 rows) and 0.95
(207) — and is **absent on all 14,884 March rows** (Jan 14,809/14,905 · Feb 13,910/13,966 ·
Mar **0**/14,884). Among rows that carry one, floors of 0.45 / 0.70 / 0.80 / 0.90 refuse
**0, 0, 0, 0**. Scored: floor 0.45 leaves n at 43,755 and net at **−0.143492 — a marginal
contribution of exactly 0.000000.** This confirms `E_NESTING_V1`'s January finding on three
months and extends it: the +0.0837 R/trade the fill-floor removal is worth is defined entirely
on resting limits the live engine cannot place.

### 2.4 The gate is the only lever with a large marginal

Corrected ablation at the joint point (band nested inside delay, since a cancel band cannot
exist without a wait): **gate +0.17067 · delay+band +0.04668 · band alone +0.02599 ·
exit −0.00081 · floor 0.00000** (`H6_DEEP_SWARM_V1.json` → `D_summary`).

**h6-F5 — the trailing exit's marginal value is −0.0008 at the joint point, against +0.043
standalone.** Priced jointly with the cost gate, the swarm's chosen exit does nothing. Priced
inside the cell that actually pays it does worse than nothing: the swarm's TRAIL025 books
**+0.00072 R/trade (ratio 1.02)** there against **+0.06853 (ratio 2.48)** for the same entry
with no trail at all — **the exit contract destroys 99 % of the cell's value** (`H6_DOSSIER_V1.json`,
cells `I` vs `B`).

---

## 3. In bps, against the 2.457 bps toll (task 3)

| form | n | edge bps | cost bps | **ratio** |
|---|--:|--:|--:|--:|
| shipped `k=0` 2R/−1R | 43,755 | −1.1846 | 2.6692 | −0.444 |
| swarm repaired | 43,755 | +0.2312 | 2.6692 | 0.087 |
| **h6 joint optimum, ungated** | 43,633 | +1.0337 | 2.6700 | **0.387** |
| + hour-true cost ≤ 1.0 bps | 16,009 | +0.5685 | 0.7166 | 0.793 |
| + hour-true cost ≤ 0.8 bps | 9,861 | +0.6605 | 0.6122 | **1.079** |
| + hour-true cost ≤ 0.68 bps | 5,378 | +0.7235 | 0.5161 | **1.402** |
| **+ hour-true cost ≤ 0.60 bps** | 3,806 | **+0.9601** | **0.4616** | **2.080** |
| + hour-true cost ≤ 0.50 bps | 3,269 | +0.9381 | 0.4508 | 2.081 |

(cost bps is 2.669 not 2.457 because these rows are priced at hour-true spread — see §5.1.)

**Answer to task 3.** No parameterisation of the contract closes the gap on the population:
the best of 25,800 gets from **9.4 % to 42.1 %** of the toll and stops. The gap closes **only**
by refusing instrument-hours whose round trip exceeds ~0.65 bps, and that leaves **8.7 % of the
cohort**. The crossing is sharp and reproducible: on the no-trail contract the cell goes
**cap 0.70 bps → net −0.00375, ratio 0.95** and **cap 0.60 bps → net +0.06853, ratio 2.48.**

---

## 4. Equity, day-level positivity, truncation (task 4)

Truncation share = trades that did **not** exit on a price level (stop or target) but were
marked out at the time stop or the substrate's 2-hour wall.

| form | n | net (hour cost) | days net+ | days gross+ | final R | max DD R | **truncated** |
|---|--:|--:|--:|--:|--:|--:|--:|
| swarm repaired, ungated | 43,755 | −0.181986 | **0 / 63** | 53 / 63 | −7,962.8 | −7,814.7 | 6.3 % |
| h6 optimum, ungated | 43,633 | −0.132324 | **0 / 63** | 62 / 63 | −5,773.7 | −5,656.2 | 11.8 % |
| h6 optimum, hour cap 0.60 | 3,806 | **+0.030160** | 39 / 63 | 45 / 63 | **+114.8** | −17.4 | 10.9 % |
| **headline cell (§6.1)** | 3,807 | **+0.068525** | 32 / 63 | 35 / 63 | **+260.9** | −78.5 | **49.4 %** |
| XAUUSD `k=30 trail 0.10 mb60` | 1,994 | +0.035196 | **42 / 63** | 45 / 63 | +70.2 | **−14.1** | **8.2 %** |

Full 63-point daily equity curves for every cell are in `H6_FINAL_V1.json` and
`H6_DOSSIER_V1.json` (`equity_net_R`). Headline cell, monthly: **+142.5 R (Jan) · +61.8 (Feb)
· +56.5 (Mar)**; it draws to −78.5 R at its worst against a +260.9 R finish.

**h6-F6 — the truncation share is the binding caveat on the index cells and NOT on the gold
cell.** The headline cell's net is monotone in the horizon and roughly 7× larger at the wall
than at 15 minutes (`+0.00977 → +0.06853`, ratio 1.21 → 2.48), so half its trades are an
unresolved mark at exactly the horizon the substrate cannot extend past (`w0` README: every path
is capped at 120 M1 bars). The XAUUSD cell is the opposite — net **+0.0354 / +0.0352 / +0.0295 /
+0.0305** at maxbars 45 / 60 / 90 / 120 — horizon-**in**sensitive, 8.2 % truncation.

---

## 5. Two audits the swarm did not run, and both change the answer

### 5.1 The cost basis is 21.2 % too cheap, and its clock is wrong for two of three months

`e_lib.real_cost_parts` charges `spread_bps_median` — one flat number per symbol. The same tick
artifact carries `spread_bps_median_by_broker_hour`, and inside a symbol that varies up to
**11.3×**. Re-charging every trade at the spread of the broker hour it actually traded in:

- mean cost **0.181834 → 0.220328 R/trade, +21.2 %**; 31.1 % of rows pay more than the median;
  p90 ratio 1.148, **p99 6.918, max 11.322**.
- the swarm headline's net goes **−0.143492 → −0.181986**, ratio_R 0.211 → 0.174.

**h6-F7 — l10's broker-hour convention (flat UTC+3) is wrong for January and February.**
Broker wall clock is `America/New_York + 7 h` (CLAUDE.md §4), which is **UTC+2** before
2026-03-08 and UTC+3 after. Measured agreement between the two conventions on this cohort:
**0.0 % of January rows, 0.0 % of February rows, 76.0 % of March rows, 25.9 % overall.** Every
hour-indexed statement built on the flat +3 offset over a pre-DST window is displaced by one
hour. (`l10_scripts/l10x_09_hours_and_minstop.py:7`, `OFF=3`.)

### 5.2 The published exit contract fails the estate's own ratified trail bound

`e_lib.walk` arms the trail off a bar's **high** and only tests the tightened stop from the
**next** bar (the l11 rule). Intrabar retracement through the trail inside the arming bar is
never charged. The estate already ratified the conservative bound for exactly this
(B613's honest trail bound; AD's 95.8 % intrabar finding). Testing the tightened stop against
the arming bar's own low:

| contract | as published | **honest bound** | premium |
|---|--:|--:|--:|
| **swarm TRAIL025, k=5** | **+0.038342** (t +12.35) | **−0.045672** (t −17.02) | **+0.084014** |
| TRAIL050, k=5 | +0.018420 | −0.065385 | +0.083805 |
| h6 optimum (trail 0.10) | +0.087644 (t +34.52) | +0.044630 (t +18.71) | +0.043014 |
| shipped 2R/−1R, k=5 | +0.000668 | +0.000668 | **0.000000** |
| stop-only, k=5 | +0.021874 | +0.021874 | **0.000000** |

**h6-F8 — the swarm's entire published headline is smaller than the bar-resolution premium of
its own trailing stop.** The premium is **+0.084014 R/trade = 2.19× the +0.038342 headline**;
under the honest bound the repaired contract is gross-**negative** and **0 of 24** instruments
is gross-positive instead of 24 of 24. Three facts pin it as the trail term and not a coding
difference: it is **exactly 0.000000** for both non-trail contracts, it is essentially identical
at trail 0.25 and trail 0.50 (+0.084014 vs +0.083805 — a per-bar effect, not a distance effect),
and it reproduces on placebo entries (+0.078582 at a +60 min anchor, +0.078011 at +120).

The h6 optimum keeps **+0.044630 at t +18.71 with 24 of 24 instruments gross-positive** under
the bound, so the *joint* sweep result is not destroyed by it — only the swarm's parameterisation
is. But its net at hour-true cost is −0.175337, and even inside the cheapest cell it is
−0.006944 (ratio 0.851): **no trail-bearing cell in this lane's search pays under both audits.**

### 5.3 Placebo anchor

Rebuild the identical cohort — same instrument, same side, same risk unit, same cost, same
contract — entered at a bar close shifted away from the decision instant. 4 contracts × 8
delays × 7 shifts (`H6_PLACEBO_PANEL_V1.json`).

| contract, k=5 | REAL | −120 | −90 | −60 | +60 | +90 | +120 | +180 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| swarm TRAIL025 | +0.03834 | +0.04293 | +0.04955 | +0.06990 | **+0.03866** | +0.05145 | +0.04910 | +0.05596 |
| h6 optimum | +0.08085 | +0.04196 | +0.03735 | +0.06808 | +0.08224 | +0.08647 | +0.08663 | +0.09140 |
| shipped 2R/−1R | +0.00067 | −0.01423 | −0.02351 | +0.01283 | −0.00080 | +0.00575 | +0.00410 | +0.01751 |
| stop-only | +0.02187 | −0.11592 | −0.10133 | −0.03968 | +0.02243 | +0.03542 | +0.02993 | +0.03344 |

**h6-F9 — the swarm's headline does not beat a random entry under its own contract.** At the
+60 min anchor the identical contract books **+0.038659 at t +12.641** against the real
**+0.038418 at t +12.315** on the same 43,428 rows; against the mean of all seven anchors the
real cohort is **−0.012736 BELOW** the placebo, and it is below the placebo mean at every one of
the eight delays tested.

Two caveats that keep this honest, and both point the same way. Backward anchors are
*anti*-correlated with a momentum trigger rather than decorrelated, and forward anchors still sit
inside the signal's own 2-hour horizon — so neither is a clean null. But the contrast that
carries the finding needs no null at all: on the **same placebo entries**, the fixed 2R/−1R
contract books −0.024…+0.018 while the trailing contract books +0.037…+0.070. The trail is worth
**+0.0509 R/trade on entries chosen at random**, and the real cohort's whole TRAIL025-minus-INC
gap at k=5 is +0.0377.

---

## 6. The hunt — where edge : cost is above 1

**197,891 cells searched** across this lane (103,200 sweep + 91,080 instrument hunt + 1,960
in-cap contract grid + 1,123 + 462 lever grids + 256 placebo + 10 dossier forms). Report the
count with the leads. Census: of 91,080 hunt cells, **20,492 (22.5 %) have ratio_R > 1 at
n ≥ 40** and **3,800 of 28,512 (13.3 %) at n ≥ 1,000** — so a raw ratio > 1 is common and means
little on its own. What follows is filtered on n, month-consistency, and the two audits of §5.

### 6.1 The one cell that survives everything — h6-F10

> **`k=3` delay · plain −1R stop · no target · no trail · close at 120 min · hour-true
> round-trip cost ≤ 0.60 bps** — which resolves to **{GER40, NAS100, US30_cash}**.

| | value |
|---|---|
| n | **3,807** (8.7 % of the cohort), 63 trading days |
| gross / cost / **net** (hour-true) | +0.114982 / 0.046457 / **+0.068525 R/trade** |
| **edge : cost** | **ratio_R 2.475 · ratio_bps 2.036** (edge 0.9398 bps vs 0.4616 bps) |
| t(net) | **+2.069** · day-block bootstrap CI **[−0.0174, +0.1622]**, **P(≤0) = 0.0715** |
| months | **3 / 3 positive** — Jan +0.1091 (n 1,307) · Feb +0.0500 (1,237) · Mar +0.0447 (1,263) |
| equity | **+260.9 R**, max DD −78.5 R, 32 / 63 days net-positive |
| win rate | 0.3636 (a low-win, fat-right-tail profile) |
| **trail premium** | **0.000000 by construction** — no trail in the contract (§5.2) |
| **placebo** | real +0.068525 vs anchors −0.1404 / −0.1261 / −0.0271 / +0.0209 / −0.0268 / −0.0227 / +0.0263 — **beats 7 of 7**; signal vs forward-anchor mean **+0.069091** |
| **caveat** | **49.4 % truncation**: half the trades are marked out at the 2-hour wall, and net rises monotonically with the horizon (+0.00977 at 15 min → +0.06853 at 120). The substrate cannot see past 120 minutes. |
| **caveat** | P(≤0) 0.0715 does not clear the estate's α = 0.10 rank-1 bar once 197,891 looks are counted. This is a lead. |

Per instrument inside it: **GER40** n 1,069 net +0.1194 (ratio 4.22) · **US30_cash** n 1,941
net +0.0737 (2.31) · **NAS100** n 796 net −0.0125 (0.65). Direction-balanced —
LONG 47.7 % (net +0.0148) / SHORT 52.3 % (net +0.0442) — so it is not index drift.

### 6.2 Three instruments clear 1.0 with no selection at all — h6-F11

The h6 joint optimum contract, chosen on **pooled** gross over 25,800 candidates, applied to the
**whole** cohort with **no** cost gate and **no** cancel band, priced at hour-true cost. The
instrument dimension is untouched by the selection:

| instrument | n | gross | cost | net | **ratio_R** | t(net) |
|---|--:|--:|--:|--:|--:|--:|
| **XAUUSD** | 1,994 | +0.1092 | 0.07268 | **+0.0365** | **1.50** | **+2.94** |
| **US30_cash** | 1,941 | +0.0840 | 0.05612 | **+0.0279** | **1.50** | +2.06 |
| **NAS100** | 1,902 | +0.0705 | 0.05382 | **+0.0166** | **1.31** | +1.46 |
| GER40 | 1,850 | +0.0767 | 0.08155 | −0.0048 | 0.94 | −0.40 |
| JP225 | 1,623 | +0.0587 | 0.08341 | −0.0247 | 0.70 | −2.05 |
| …19 more | | | | all negative | 0.23 … 0.60 | |

**3 of 24 instruments clear edge : cost = 1 at n ≈ 1,900–2,000 each, with no per-instrument
selection.** They are not simply the cheapest: EURUSD (0.686 bps) and GBPUSD (0.746) are cheaper
than XAUUSD (1.282) and lose. It is a two-dimensional story — cost **and** edge — not a cost
screen. (This contract carries trail 0.10, so §5.2's +0.043014 discount applies to the gross
column; the ordering does not move.)

### 6.3 The cleanest single instrument cell — h6-F12

**XAUUSD, `k=30 · trail 0.10 · no target · stop −1R · close at 60 min`:** n 1,994,
net **+0.035196** at hour-true cost, ratio_R 1.48, **t +3.19**, bootstrap **P(≤0) = 0.001**,
**42 / 63 days net-positive**, final +70.2 R against a max drawdown of only **−14.1 R (5.0×
return/DD)**, **truncation 8.2 %** and net essentially flat across maxbars 45→120. Months:
Jan −0.00004 · Feb +0.0759 · Mar +0.0363. It is the best-of-240 contracts for that instrument
and it carries a trail, so it must be discounted by §5.2 — but it is the only cell in the lane
that is simultaneously significant, horizon-insensitive and low-drawdown.

### 6.4 The R-denominated cost gate crosses 1.0 where the swarm said it never does

On the swarm's own contract and its own flat cost basis, gating on `cost_true`:

| gate (R) | n | gross | cost | net | **ratio_R** | trunc | Jan / Feb / Mar net |
|---|--:|--:|--:|--:|--:|--:|---|
| none | 43,755 | +0.0383 | 0.1818 | −0.14349 | 0.211 | 0.063 | −0.167 / −0.146 / −0.117 |
| ≤ 0.05 | 9,942 | +0.0144 | 0.0283 | −0.01388 | 0.510 | 0.174 | −0.001 / −0.012 / −0.023 |
| ≤ 0.03 | 5,362 | +0.0091 | 0.0184 | −0.00930 | 0.493 | 0.209 | −0.000 / −0.005 / −0.017 |
| **≤ 0.02** | **2,963** | +0.0157 | 0.0131 | **+0.00263** | **1.201** | 0.249 | +0.018 / −0.009 / +0.003 |
| ≤ 0.01 | 819 | +0.0173 | 0.0073 | +0.01002 | 2.376 | 0.326 | +0.070 / −0.039 / +0.016 |
| ≤ 0.0075 | 376 | +0.0353 | 0.0055 | +0.02971 | 6.360 | 0.412 | +0.088 / +0.017 / +0.023 |

**h6-F13 — the swarm's "the edge : cost ratio never exceeds 0.31 in any decile" is a statement
about its risk-distance deciles, not its cost bands, and the pooled cheapest cost band was in
its own receipt unpooled.** `e-stack` §7.4 lists the 0–0.02 band per month (613 / 807 / 1,543
rows at +0.0181 / −0.0093 / +0.0027) — the same 2,963 rows, never added up. Pooled they are
**net +0.00263 at ratio 1.201**. This is a reading correction, not a contradiction, and the
lane's own §5 audits mean the cell should be read on the no-trail contract instead.

### 6.5 Census of instruments that produce a robust paying cell

Cells with n ≥ 150, **all three months net-positive**, and ratio_R > 1, out of 91,080:
**US30_cash 1,039 · GER40 726 · XAUUSD 268 · NAS100 243 · UK100 117 · JP225 114 · XAGUSD 36 ·
SPX500 34 · USDJPY 16 · BTCUSD 4.** Fourteen instruments produce none at any parameterisation
searched. The paying set is a stable, small, index-plus-metals cluster.

---

## 7. What this lane says the mechanism is

The swarm's closing observation was right — cost disperses ~12× while edge is roughly flat, so
cells where edge/cost > 1 must exist — and they do. But the swarm's own number for "edge" does
not survive:

1. **The edge it measured is mostly its exit rule.** +0.084014 of trailing-stop bar premium
   against a +0.038342 headline, present on random entries, absent from any no-trail contract.
2. **The toll it measured is 21.2 % too cheap**, because one flat median spread per symbol
   averages away an 11.3× intraday range.
3. **The four components it asked to be priced jointly are not four.** The fill floor is exactly
   zero here; the exit is −0.0008 at the joint point and −0.068 inside the cell that pays; the
   cancel window is worth +0.026 to +0.047; **the cost gate is worth +0.171 and is the whole
   thing.** The lever that pays is not a contract parameter at all — it is refusing to trade
   instrument-hours whose round trip exceeds ~0.65 bps.
4. **Underneath all of it there is a real cell**: a three-minute wait, a plain stop, a two-hour
   exit, on the three instruments the broker charges least, worth **2.475× its own toll over
   3,807 trades and three months, beating seven of seven placebo anchors.** It is not
   significant at the estate's bar (P(≤0) 0.0715 on 197,891 looks) and half its trades die at
   the substrate's wall. It is the best thing found and it is a lead, not a result.

**The next measurement, precisely.** The two things that would settle it are (a) a substrate
that extends past 120 minutes, because the index cell's entire magnitude lives between minute 90
and minute 120 and no one can see whether it keeps going or gives back; and (b) an intrabar
(tick) evaluation of the trail, because +0.084 R/trade of the estate's exit economics currently
rests on M1 OHLC resolution and this lane has now measured that premium on two contracts and
seven placebo anchors.

---

## 8. Findings register

| id | finding | numbers |
|---|---|---|
| **h6-F1** | contract axes are complements; wave-1 levers were substitutes | standalone sum −15.25 % of joint gain vs +66.8 % double-count |
| **h6-F2** | stop width flips sign standalone → joint | −0.018234 → +0.011857 |
| **h6-F3** | k=5 is not the best delay | k=8 +0.046035 vs k=5 +0.038342 (+20 %) |
| **h6-F4** | fill floor is identically inert | 2 efp values, 0 refusals ≤0.90, Mar 0/14,884, marginal 0.000000 |
| **h6-F5** | the trailing exit's marginal is ~0, and negative in the paying cell | −0.00081 at joint point; +0.00072 vs +0.06853 in-cell |
| **h6-F6** | truncation is the binding caveat on index cells, not on gold | 49.4 % vs 8.2 %; +0.00977@15min → +0.06853@120min |
| **h6-F7** | l10's broker-hour convention is wrong pre-DST | 0.0 % Jan / 0.0 % Feb / 76.0 % Mar agreement |
| **h6-F8** | the headline is smaller than its own trail's bar premium | premium +0.084014 = 2.19×; honest bound −0.045672, 0/24 |
| **h6-F9** | the headline does not beat a random entry | placebo +0.038659 (t 12.64) vs real +0.038418 (t 12.32) |
| **h6-F10** | **the surviving paying cell** | n 3,807, net +0.068525, ratio 2.475, 3/3 months, 7/7 placebos |
| **h6-F11** | 3 of 24 instruments clear 1.0 with no per-instrument selection | XAUUSD 1.50 · US30 1.50 · NAS100 1.31 |
| **h6-F12** | the cleanest single cell | XAUUSD n 1,994, +0.0352, t +3.19, P 0.001, DD −14.1 R |
| **h6-F13** | the swarm's own cheapest cost band pools net-positive | n 2,963, +0.00263, ratio 1.201 |

---

## 9. Artifacts

Scripts (all in `docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/`):

| script | what |
|---|---|
| `h6_01_repro.py` | reproduce the swarm headline from the shipped at-market files |
| `h6_02_build_cache.py` | re-materialise all 43,755 R paths from true-UTC M1 bars (float64) |
| `h6_lib.py` | the one joint scorer: vectorised honest walk + populations + stats + bootstrap |
| `h6_03_validate.py` | 100 %-exact agreement with four shipped columns; efp census |
| `h6_04_sweep.py` | 28,800 contracts × 4 gates (869 s) |
| `h6_05_joint.py`, `h6_06_deep.py` | band × gate × floor grids, ablations, train/test |
| `h6_07_hunt.py`, `h6_08_hunt_read.py` | 91,080 instrument × contract × gate × band cells |
| `h6_09_hourcost.py` | hour-true broker spread re-costing, DST-aware broker clock |
| `h6_10_frontier.py` | the affordability frontier and its horizon sensitivity |
| `h6_11_sweep_read.py`, `h6_12_dossier.py`, `h6_13_final.py` | reads, dossiers, final forms |
| `h6_14_controls.py`, `h6_15_placebo_panel.py` | side split + placebo anchors (7 shifts) |
| `h6_16_trailbound.py` | the ratified honest-trail bound |

Receipts: `H6_REPRO_V1.json` · `H6_VALIDATE_V1.json` · `H6_CACHE_BUILD_V1.json` ·
`h6_SWEEP_V1.jsonl.gz` (103,200 cells) + `H6_SWEEP_BUILD_V1.json` + `H6_SWEEP_TOP_V1.json` ·
`h6_HUNT_V1.jsonl.gz` (91,080 cells) + `H6_HUNT_BUILD_V1.json` + `H6_HUNT_TOP_V1.json` ·
`H6_JOINT_SWARM_V1.json` · `H6_DEEP_SWARM_V1.json` · `H6_HOURCOST_V1.json` ·
`H6_FRONTIER_V1.json` · `H6_DOSSIER_V1.json` · `H6_FINAL_V1.json` · `H6_CONTROLS_V1.json` ·
`H6_PLACEBO_PANEL_V1.json` · `H6_TRAILBOUND_V1.json` · `H6_HEADLINE_CELL_PLACEBO_V1.json` ·
`h6_RESULT.json`. Data: `h6_ATMKT_PATHS.npz` (79.5 MB) · `h6_ATMKT_META.jsonl.gz` ·
`h6_cost_hour.npy` · `h6_broker_hour.npy`.

Source citations used above: `e_lib.py:54-74` (the walk, and the next-bar trail test),
`e_lib.py:103-122` (the flat-median cost basis), `e_score.py:34` (the shipped 0.10/0.15 gate),
`l10_scripts/l10x_09_hours_and_minstop.py:7` (`OFF=3`), `L10X_TICK_SPREAD_V1.json`
(`spread_bps_median_by_broker_hour`), `w0_WORKING_SET_README.md` (the 120-bar horizon cap),
CLAUDE.md §4 (broker clock = `America/New_York + 7 h`).
