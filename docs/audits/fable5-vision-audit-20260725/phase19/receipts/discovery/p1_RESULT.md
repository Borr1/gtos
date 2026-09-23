# p1 — THE PERSISTENCE TEST

**Eight open windows. 1,118,694 candidate emissions, 331,548 honest fills. Every cell
partition, every selection axis, every candidate the wave produced — tested for the one
failure mode that killed three headline results this week.**

Every number is produced by a script in `p1/` and lands in `p1/P1_*.json`. Nothing is
estimated, nothing is sampled. **The sealed three (June/August/September 2025) were never
opened by this lane.**

---

## 0. THE ANSWER, IN FOUR SENTENCES

**Cost is the only per-cell quantity in this system that is measurable at all, and it is
the only one that travels.** Across 27 (population × partition) combinations the
cross-window Spearman rank correlation of the toll has median **+0.9005** (min +0.7386);
of the gross edge it has median **+0.0230** (range −0.0468 … +0.3653). Measured in price
units rather than R the split is starker still — cost rank travels at **+0.9936 … +0.9989**
on every instrument-based partition, gross at **−0.10 … +0.13**.

**And it is not a power problem, which is the part nobody had established.** A random
row-split of a *single* window recovers the cost ordering at **+0.9718** and the at-market
gross ordering at **+0.0466** — so inside one month, with the calendar held fixed and no
non-stationarity available as an excuse, the instrument-level edge ordering does not agree
with **itself**. There is nothing to select on before there is anything to fail to persist.

**324 out-of-sample cell-selection arms were run** — 6 partitions × 3 axes (gross / cost /
net) × 3 selection shares × 2 protocols (strictly chronological and leave-one-month-out) ×
3 populations. **265 improve net; the median cost share of that improvement is 0.977;
ZERO produce a positive book.** The best arm in the whole grid books **−0.00789 R/trade**
and 93.6 % of its improvement is toll removed.

**Exactly one axis in this wave has an ordering that travels and is not the fee schedule:
the exit contract.** Its rank persistence is **+0.6361 on net and +0.6399 on gross**, its
cost delta against the shipped contract is **exactly 0.00000 in all eight months**, and it
is worth **+0.03472 R/trade, 8/8 months, growing** (first four +0.02819 → last four
+0.04125). It is 9.1× short of the toll it would have to pay.

---

## 1. SUBSTRATE AND VALIDATION

| | |
|---|---|
| panel | `/tmp/d1/rows3/D1_<window>.npz`, the d1b lane's roster row builder (Session PB's reproduced sealed rosters) |
| windows | 2025-10, 2025-11, 2025-12, 2026-01, 2026-02, 2026-03, 2026-04, 2026-05 |
| emissions | **1,118,694** — matches `f1_BASELINE_V1.json` exactly |
| honest fills | **331,548** — matches f1 exactly (46,270 / 41,840 / 36,026 / 43,922 / 39,225 / 45,082 / 41,084 / 38,099) |
| pooled gross | −0.08233 (f1: −0.082332672437182) |
| clean roster | 298,537 fills, gross −0.01327 (f1: −0.013268637647645) |
| contract | honest resting-limit fill, 120 M1 bars, target 2.0R, h1 broker-true four-term toll |
| corrected contract | d1b §2 — the seven at-market families are MARKET orders; reproduces d1b's +0.02402 and `structural_distance_extreme` +0.06639 exactly |
| sealed | June/August/September 2025 **not read** |

Two arms are carried on every row: the **real** arm and its **exact mirror about the entry
price** (d1's zero-Monte-Carlo coin-flip control), so every directional claim below is a
paired difference with no simulation error.

---

## 2. THE PERSISTENCE MATRIX — `p1/P1_MATRIX_V1.json`

All 28 window pairs, per partition. `cross` = mean pairwise Spearman across the 8 windows.
`split-row` = the same rank correlation between two random halves of a **single** window,
averaged over 25 draws and 8 windows — the reliability ceiling, i.e. how much of the
ordering is measurable at all. `split-day` = between two random halves of the **trading
days** of a single window.

### 2.1 Clean roster (no born-past-stop, no `current_breaker_re_entry`)

| partition | k | COST cross | COST split-row | GROSS cross | GROSS split-row | GROSS split-day |
|---|---:|---:|---:|---:|---:|---:|
| instrument | 24 | **+0.7794** | +0.9757 | **+0.0093** | +0.4333 | +0.1451 |
| family | 9 | **+0.9869** | +0.9903 | **−0.0065** | +0.4638 | −0.0052 |
| broker hour | 24 | **+0.9580** | +0.9812 | **+0.1338** | +0.5185 | +0.0427 |
| instrument × family | 155 | +0.9374 | +0.9854 | +0.0053 | +0.2944 | +0.0651 |
| instrument × hour | 409 | +0.8866 | +0.9581 | +0.0181 | +0.3064 | +0.0317 |
| family × hour | 163 | +0.9738 | +0.9838 | +0.0229 | +0.4265 | +0.0128 |
| instrument × side | 48 | +0.7780 | +0.9660 | +0.0513 | +0.4931 | +0.0542 |
| instrument × vol tercile | 82 | +0.7386 | +0.9450 | −0.0090 | +0.3987 | +0.0410 |

### 2.2 At-market cohort — where the estate's one positive gross lives

| partition | k | COST cross | COST split-row | GROSS cross | GROSS split-row |
|---|---:|---:|---:|---:|---:|
| instrument | 24 | +0.8030 | +0.9718 | **+0.0228** | **+0.0466** |
| family | 7 | +0.9809 | +0.9855 | +0.0383 | +0.4161 |
| broker hour | 24 | +0.9191 | +0.9622 | +0.0146 | +0.4606 |
| instrument × family | 119 | +0.9469 | +0.9840 | +0.0169 | **+0.1174** |
| instrument × hour | 238 | +0.8498 | +0.9202 | −0.0097 | **+0.0823** |
| instrument × fam × hour | 74 | +0.9288 | — | −0.0774 | — |

**Read the split-row column.** On the at-market cohort — the only cohort in the estate with
a positive pooled gross — the instrument edge ordering fails to reproduce against a random
half of its **own month** (+0.0466). The failure is not that edge stops travelling. It is
that at cell resolution there is no edge ordering to travel.

The ALL_FILLS population shows the opposite (instrument gross split-row +0.7397) and that
is a trap: it is the defective `current_breaker_re_entry` family, whose born-past-stop rows
book a mechanical ≈ −0.998 and concentrate by instrument, manufacturing a stable ordering
that is arithmetic, not edge. Removing it takes the ceiling 0.7397 → 0.4333 (clean) →
0.0466 (at-market).

### 2.3 Same test in price units — `p1/P1_TOLLNEUTRAL_V1.json` → `A_rank_units`

R divides the price move by the stop distance, so both gross-in-R and cost-in-R scale as
1/d. Re-measuring in basis points removes that shared axis:

| population | partition | gross_R | **gross_bps** | cost_R | **cost_bps** |
|---|---|---:|---:|---:|---:|
| CLEAN | instrument | +0.0093 | **−0.0088** | +0.7794 | **+0.9936** |
| CLEAN | family | −0.0065 | −0.0077 | +0.9869 | +0.8244 |
| CLEAN | inst × family | +0.0053 | −0.0030 | +0.9374 | **+0.9770** |
| CLEAN | inst × hour | +0.0181 | +0.0058 | +0.8866 | **+0.9986** |
| CLEAN | inst × fam × hour | −0.0042 | +0.0020 | +0.9375 | **+0.9966** |
| AT_MARKET | instrument | +0.0228 | −0.0826 | +0.8030 | **+0.9944** |
| AT_MARKET | inst × hour | −0.0097 | −0.0055 | +0.8498 | **+0.9989** |

**In price units the toll ordering is a near-deterministic function of the cell.** It is
the fee schedule, literally. The edge ordering is zero in both unit systems.

---

## 3. IS THERE ANYTHING TO SELECT ON? — `p1/P1_VAR_V1.json`

`var(observed cell means) = var(true cell means) + E[s²/n]`, so the real between-cell
dispersion is recoverable. Averaged over the 8 windows:

| population | partition | GROSS true sd | of observed | **signal share** | COST true sd | signal share | ratio g/c |
|---|---|---:|---:|---:|---:|---:|---:|
| CLEAN | instrument | 0.04442 | 0.05756 | 58.8 % | 0.15172 | 98.8 % | **0.293** |
| CLEAN | family | 0.03346 | 0.04192 | 61.5 % | 0.19307 | 99.8 % | **0.173** |
| CLEAN | broker hour | 0.04876 | 0.05902 | 67.8 % | 0.18030 | 99.4 % | 0.270 |
| CLEAN | inst × family | 0.11976 | 0.16229 | 54.3 % | 0.26154 | 98.3 % | 0.458 |
| **AT_MARKET** | **instrument** | **0.01452** | 0.04889 | **13.1 %** | 0.15980 | 98.6 % | **0.091** |
| AT_MARKET | inst × family | 0.05942 | 0.12862 | 22.3 % | 0.28319 | 98.2 % | 0.210 |
| AT_MARKET | inst × hour | 0.07930 | 0.20126 | 15.8 % | 0.29198 | 96.0 % | 0.272 |

**86.9 % of the observed spread in per-instrument at-market edge is sampling noise. 1.4 %
of the spread in per-instrument toll is.** Every optimiser this estate has ever run found
the fee schedule because the fee schedule is the only axis with dispersion above its own
measurement error.

**The oracle ceiling** (`p1/P1_CEILING_V1.json`) — what a rule that knew each cell's *true*
within-month edge with zero estimation error could buy, at `τ·φ(z_q)/q`:

| population | partition | oracle gain keeping best 50 % | keeping best 10 % | same for COST (10 %) |
|---|---|---:|---:|---:|
| AT_MARKET | instrument | +0.01159 | +0.02548 | +0.28045 |
| AT_MARKET | inst × family | +0.04741 | +0.10427 | +0.49699 |
| CLEAN | family | +0.02670 | +0.05872 | +0.33883 |

Against a toll of 0.280–0.311 R/trade. **Perfect foreknowledge of instrument edge is worth
+0.025 R/trade; perfect foreknowledge of instrument cost is worth +0.280.** And the
cross-window rank persistence says essentially none of even that τ travels to the next
month.

---

## 4. THE OUT-OF-SAMPLE ARM GRID — `p1/P1_OOS_V1.json`, `p1/P1_TOLLNEUTRAL_V1.json`

324 arms. Fit the cell ordering on the training months, keep the top fraction, apply to
the held-out month, decompose against that month's own whole-population baseline:
`d_net = d_gross − d_cost`.

| | |
|---|---:|
| arms | **324** (6 partitions × 3 axes × 3 shares × 2 protocols × 3 populations) |
| arms that improve net | **265** |
| **median cost share of the improvement** | **0.977** |
| arms with cost share < 0.5 | 31 |
| **arms producing a net-positive book** | **0** |
| best absolute net achieved | **−0.00789** (AT_MARKET, inst × family, cheapest 10 %, LOMO) — cost share 0.936 |
| best under the strictly chronological protocol | −0.01806 (same cell, EXPANDING) — cost share 0.942 |

### 4.1 The toll-neutral test — is any gross-rank persistence real edge?

Selecting on train-fitted gross-in-R **does** lift out-of-sample gross, sometimes in 8 of 8
held-out months. Two candidate explanations: a travelling edge ordering, or the 1/d axis
shared by gross-in-R and cost-in-R. Test: regress each cell's train gross on its train cost
(quadratic) and select on the **residual**; and score every arm against a random-cell null
matched on selected-row share, 200 draws per month.

| arm | d_gross | null | z | d_cost | d_net | months net+ | book |
|---|---:|---:|---:|---:|---:|---:|---:|
| AT_MARKET inst×fam×hour, gross, q0.10 | +0.09201 | −0.00025 | **+2.66** | +0.21697 | −0.12496 | 0/8 | −0.44002 |
| AT_MARKET inst×fam×hour, **resid**, q0.10 | +0.08702 | +0.00132 | +2.42 | +0.15959 | −0.07257 | 0/8 | −0.38719 |
| CLEAN inst×fam×hour, gross, q0.10 | +0.09637 | +0.00042 | +2.19 | +0.17766 | −0.08129 | 0/8 | −0.37417 |
| CLEAN broker_hour, resid, q0.50 | +0.01745 | +0.00043 | +1.50 | −0.00740 | +0.02485 | 8/8 | −0.26933 |

**Over the 72 gross/residual arms the maximum |z| is +2.66, against an expected maximum of
+2.92 for 72 pure-noise draws** (median |z| 0.41 and p90 1.05 over all 108 arms including
the cost axis, whose expected max is +3.06). **Not one gross-selection arm exceeds what
noise alone produces at this multiplicity.** The finest partition does lift
gross by +0.092 — and buys +0.217 of toll doing it, because the cells that carry gross-in-R
are the tight-stop cells where a fixed price toll is a large R toll. That coupling is
mechanical and it is why residualising on cost removes most of the apparent gain.

---

## 5. THE ONE AXIS THAT TRAVELS AND IS NOT THE FEE SCHEDULE — `p1/P1_USAGE_V1.json`

Same rank-persistence test, run on the **usage** axes d2 published per window on the
identical at-market population.

| axis | k | rank persistence NET | rank persistence GROSS | rank persistence COST |
|---|---:|---:|---:|---:|
| **exit contract** | 12 | **+0.6361** | **+0.6399** | +0.6355 |
| entry offset j | 15 | +0.2722 | **+0.0325** | **+0.8740** |
| gate grid | 80 | +0.6427 | **+0.0013** | **+0.9936** |

### 5.1 EXIT — the survivor

`stop_only_horizon` against the shipped `target_2.0R`, per month:

| window | d_gross | d_cost | d_net |
|---|---:|---:|---:|
| 2025-10 | +0.03691 | **+0.00000** | +0.03691 |
| 2025-11 | +0.03232 | +0.00000 | +0.03232 |
| 2025-12 | +0.02327 | +0.00000 | +0.02327 |
| 2026-01 | +0.02027 | +0.00000 | +0.02027 |
| 2026-02 | +0.02198 | +0.00000 | +0.02198 |
| 2026-03 | +0.06031 | +0.00000 | +0.06031 |
| 2026-04 | +0.05611 | +0.00000 | +0.05611 |
| 2026-05 | +0.02659 | +0.00000 | +0.02659 |
| **mean** | **+0.03472** | **+0.00000** | **+0.03472** |

**8 of 8 months, cost share of the improvement exactly 0.000, and it grows** — first four
+0.02819, last four +0.04125. The full menu ordering is monotone in the target ladder in
every month: `target_1.0R` ranks 11th–12th of 12 in all eight, `target_1.5R` 9th–11th, and
**the shipped `target_2.0R` ranks 7th–10th of 12 in every single month**. `stop_only_horizon`
never ranks worse than 4th.

**Independently corroborated on my own substrate.** The exit table above is d2's per-window
artifact; re-walking the 1.5R → 2.0R step myself on the same rosters gives a gain that is
positive in **8 of 8 windows** on the at-market cohort (+0.01874 / +0.00260 / +0.00051 /
+0.01356 / +0.00995 / +0.00700 / +0.00938 / +0.00849) and 6 of 8 on the clean roster. The
direction of the ladder is the same object measured two ways.

**How much of it is signal** (`p1/P1_EXITPLACEBO_V1.json`). Widening the target 1.5R → 2.0R
is a pure exit change, so the exact mirror arm measures how much of the gain a coin flip
also gets on the same rows: real +0.00468, mirror +0.00120 — **the coin flip reproduces
25.5 %** on the clean roster and **58.7 %** on the at-market cohort. So the exit ordering is
partly tape geometry available to any participant and partly this book's own asymmetry. For
a book already taking these trades the +0.03472 is real money either way; as *evidence of
signal* it is at most partial. **And it is 9.1× short of the 0.31553 toll on the same rows,
so it cannot rescue the family.**

### 5.2 ENTRY OFFSET j=5 — killed as an edge claim

d2's `j=5` wins in 8 of 8 months. Decomposed:

| | mean | first four | last four |
|---|---:|---:|---:|
| d_gross | **+0.00299** (sign flips in 3 of 8 months) | | |
| d_cost | **−0.01327** | | |
| d_net | +0.01626 | +0.01858 | +0.01394 |
| **cost share of d_net** | **+0.816** | | |

Its rank persistence is **+0.8740 on cost and +0.0325 on gross**. This is the fee schedule
at minute resolution — the intra-bar spread premium d8x measured (+3.89 % median in the
first 60 s after an M15 boundary) — not a timing edge. **Keep it as a cost repair; it is
not evidence about the signal.**

### 5.3 GATE GRID — the ordering IS the fee schedule

80 gate cells, gross rank persistence **+0.0013**, cost rank persistence **+0.9936**. The
pooled-best cell (`cost<=0.03`) ranks 13th, 16th, 13th, 6th, 1st, 2nd, 4th, 9th across the
eight months — the *level* is stable, the *choice* is not.

---

## 6. THE CANDIDATE REGISTER — `p1/P1_CAND_V1.json`, `p1/P1_CORRECTED_V1.json`

Corrected contract (at-market families as market orders, POI as resting limits).

| candidate | n | gross | cost | net | months gross+ | first→last gross | slope/month |
|---|---:|---:|---:|---:|---:|---:|---:|
| **at-market cohort** | 135,803 | **+0.02402** | 0.30825 | −0.28424 | **8/8** | −0.00232 | −0.00008 |
| **`structural_distance_extreme`** | 22,612 | **+0.06639** | 0.62322 | −0.55683 | **8/8** | −0.01269 | +0.00060 |
| `liquidity_sweep_reclaim` | 41,152 | +0.02754 | 0.29604 | −0.26850 | 5/8 | −0.02143 | −0.00042 |
| `cross_asset_lead_lag` | 20,052 | +0.02428 | 0.44458 | −0.42030 | 7/8 | +0.01725 | +0.00526 |
| `displacement_continuation` | 36,929 | +0.00797 | 0.14729 | −0.13932 | 5/8 | +0.02079 | −0.00016 |
| `session_open_range_break` | 7,855 | +0.00250 | 0.08833 | −0.08583 | 5/8 | **−0.03894** | **−0.01503** |
| `regime_transition_break` | 2,216 | −0.00455 | 0.05447 | −0.05901 | 3/8 | −0.00312 | −0.00054 |
| `volatility_compression_expansion` | 4,987 | −0.03284 | 0.08383 | −0.11667 | 2/8 | +0.01235 | +0.00205 |
| `current_breaker_re_entry` (clean rows) | 10,449 | −0.08144 | 0.24104 | −0.32249 | 1/8 | +0.02604 | −0.00155 |
| POI limit filled in the decision bar | 41,435 | **−0.62732** | 0.24712 | −0.87444 | 0/8 | +0.10540 | +0.01602 |
| POI limit filled later (genuine pullback) | 155,607 | −0.00418 | 0.26317 | −0.26735 | 3/8 | +0.02333 | +0.00755 |

### 6.1 Chronological decay of the paired directional signal (real minus exact mirror)

| candidate | signal per window (Oct-25 → May-26) | mean | months+ | first four | last four | decay |
|---|---|---:|---:|---:|---:|---:|
| at-market cohort | +0.0238 +0.0283 −0.0048 +0.0257 +0.0031 +0.0083 +0.0375 −0.0004 | **+0.01518** | 6/8 | +0.01824 | +0.01212 | **−33.6 %** |
| `structural_distance_extreme` | +0.0101 −0.0421 +0.1694 +0.1084 −0.0179 +0.0730 +0.0739 −0.0518 | +0.04038 | 5/8 | +0.06146 | +0.01931 | **−68.6 %** |
| `liquidity_sweep_reclaim` | +0.0479 +0.1010 −0.0332 +0.0806 −0.0406 −0.0125 +0.0651 +0.0837 | +0.03649 | 5/8 | +0.04904 | +0.02393 | −51.2 % |
| `cross_asset_lead_lag` | −0.0295 +0.0618 −0.1059 +0.0522 −0.0356 +0.0413 +0.0664 +0.0140 | +0.00810 | 5/8 | −0.00534 | +0.02154 | rising |

**The two 8/8 results are level results, not ordering results.** The at-market cohort's
gross is positive in all eight windows and its per-instrument, per-hour and per-cell
orderings carry nothing (§2.2). It is a small pooled constant you cannot aim.

### 6.2 b1's two limbs, on three windows b1 never had

b1-BOOK-V1's post-mortem attributed its out-of-sample failure to the hour limb inverting.
The instrument-limb analogue on the extended panel (clean roster, limit contract, the same
three instruments; the cheap-hour split reproduced as that window's cheapest cost quartile
— **an analogue of b1's `toll_bps ≤ 0.60` gate, not a replication of b1-BOOK-V1**):

| | pooled gross | pooled cost | pooled net | months gross+ |
|---|---:|---:|---:|---:|
| three instruments, cheapest cost quartile | **−0.03433** | 0.04326 | −0.07759 | 2/8 |
| three instruments, the rest | −0.01131 | 0.19253 | −0.20384 | 2/8 |

Over eight windows the cheap-toll subset is **worse** on gross by 0.0230 R/trade — the
opposite sign to b1's in-window +0.1361. The three extra 2025 windows do not rescue it and
do not contradict its post-mortem: they confirm it on 60 % more data.

### 6.3 Affordability thresholds, re-tested for persistence

| rule | n | gross | cost | net | months gross+ |
|---|---:|---:|---:|---:|---:|
| cost ≤ 0.30 | 217,241 | −0.01841 | 0.12306 | −0.14147 | 1/8 |
| cost ≤ 0.15 (shipped) | 143,744 | −0.02626 | 0.07760 | −0.10386 | 2/8 |
| cost ≤ 0.05 | 41,403 | −0.03904 | 0.03042 | −0.06946 | 1/8 |
| cost ≤ 0.03 | 19,553 | −0.04418 | 0.01929 | −0.06348 | 1/8 |
| cheapest toll decile (d1b's killed cell) | 29,858 | −0.04542 | 0.02636 | −0.07177 | 2/8 |

Monotone: every tightening of the affordability cap **lowers the gross**. f2's cost-cap
sweep reproduces on this panel and extends to the three 2025 windows. d1b's cheapest-decile
result stays dead: −0.04542 gross, 2/8 months.

---

## 7. THE KILL LIST, BY NAME

| finding | verdict | the number that kills it |
|---|---|---|
| **d2 entry offset `j=5`** as an edge/timing result | **KILLED as edge; survives as a cost repair** | cost share of d_net **+0.816**; gross rank persistence **+0.0325** vs cost **+0.8740**; gross component +0.00299 with the sign flipping in 3 of 8 months |
| **d2 gate grid / any affordability threshold** | **KILLED — it IS the fee schedule** | gate-cell gross rank persistence **+0.0013**, cost **+0.9936**; every tightening lowers gross (§6.3) |
| **any instrument-, family-, hour- or cell-conditioning rule** | **KILLED** | 324 OOS arms, **0 net-positive**, median cost share **0.977**; over the 72 gross/residual arms max &#124;z&#124; vs a random-cell null is **+2.66**, below the **+2.92** expected max of 72 pure-noise draws |
| **d1b's cheapest-toll decile** (already retracted by its own lane) | **CONFIRMED DEAD on 8 windows** | −0.04542 gross, 2/8 months positive |
| **b1's hour limb** | **CONFIRMED DEAD on 3 additional windows** | cheap-quartile gross −0.03433 vs expensive −0.01131 — the in-window +0.1361 advantage inverts on the full panel |
| **`structural_distance_extreme` as a selectable family** | **DEMOTED** | gross 8/8 at +0.06639, but its paired signal decays **−68.6 %** first→last half and is positive in only 5 of 8 months; family-level gross rank persistence **−0.0065** so you cannot pick which family, and its toll is **9.4× its gross** |
| **the at-market cohort's +0.02402 as a targetable edge** | **DEMOTED to a pooled constant** | 8/8 positive, but instrument gross split-half reliability **+0.0466** — the ordering does not reproduce inside its own month |
| **`current_breaker_re_entry` / POI-filled-in-decision-bar** | **CONFIRMED as defects, not edges** | −0.08144 (1/8) and −0.62732 (0/8); both are structural, both repairable, neither is a signal claim |
| **d2 exit swap to `stop_only_horizon`** | **SURVIVES** | +0.03472 R/trade, **8/8 months, d_cost exactly 0.00000 in all eight**, rank persistence +0.6361/+0.6399, and rising |

---

## 8. WHAT WOULD HAVE TO BE TRUE

For any cell-conditioning rule to make the broad family viable, the per-cell edge dispersion
would have to be (a) larger than its own measurement error and (b) stable month to month.
Measured:

| requirement | measured | shortfall |
|---|---|---|
| per-instrument at-market edge dispersion must exceed sampling noise | **13.1 %** of the observed spread is real | the ordering fails against its own month at +0.0466 |
| that ordering must travel | cross-window Spearman **+0.0228** (gross) vs **+0.8030** (cost) | 35× |
| perfect foreknowledge of instrument edge must cover the toll | oracle at best-10 % = **+0.02548** against a **0.30825** toll | **12.1×** |
| the exit lever must cover the toll | **+0.03472** against **0.31553** | **9.1×** |

**The honest statement of the mechanism, in one line: the fee schedule is the only
cross-sectionally stable quantity this system emits, so every optimiser that has ever been
pointed at it has returned the fee schedule — not because the search was naive, but because
at cell resolution nothing else in the object has dispersion above its own noise floor.**

---

## 9. LIMITS

1. Eight windows, October 2025 – May 2026. **The sealed three were not opened.** Everything
   here is in-window for the wave as a whole, even where it is out-of-sample for a
   particular arm.
2. The panel's walker inherits the estate's BID-archive bias (d8x: −0.0696 R/trade with a
   constant sign). A constant-sign bias cannot move a **rank** correlation between cells,
   which is what this lane measures, but it does mean every *level* here is optimistic.
3. The exit-contract persistence is read from d2's published per-window artifacts, not
   re-walked here; the target-ladder placebo (§5.1) is my own measurement and covers only
   the 1.5R → 2.0R step, so the coin-flip share of the full `stop_only_horizon` step is
   bounded, not measured.
4. `b1_LIMB_*` is an analogue of b1's gate on this panel's contract, not a replication of
   b1-BOOK-V1 (different substrate, different entry rule, different horizon).
5. The variance decomposition's `true_sd` is a within-month quantity and therefore an
   **upper bound** on the travelling dispersion; the cross-window rank correlations say
   almost none of it travels.
