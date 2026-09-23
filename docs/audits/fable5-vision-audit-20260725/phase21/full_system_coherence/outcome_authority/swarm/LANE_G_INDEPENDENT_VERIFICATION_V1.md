# Lane G — independent verification of today's funnel findings

**Commission:** orchestrator, 2026-08-12. *"Independently re-derive and attack the findings
produced TODAY, including the ones the orchestrator published… Assume nothing I wrote is
correct."* Five named items. Nothing live, nothing config, nothing on the VPS was touched.

**Companion:** `LANE_G_RECONCILIATION_V1.md` — the Lane C / Lane E / Lane D reconciliation,
commissioned mid-task and reported there in full. Read it first if the question is "which lane is
right".

**Method.** I re-walked the identical sealed population through the identical frozen machinery
with an independent harness (`lane_g_receipts/laneg_walk.py`), carrying a **third arm** Phase 0
did not have: **MIRROR** — same instant, same 1R stop, same 2R target, direction flipped. It is a
direction-randomised control that needs no driftless model, no volatility estimate and no horizon
correction, because it is the same paths, same geometry, same horizon and same spreads.

**Control first.** My ORIG and INV arms reproduce Phase 0's walk on **81,968 rows compared,
0 mismatched, maximum |net difference| 0.0** — and Phase 0's ORIG arm already reproduces the
sealed cache exactly. Three harnesses, one number. Everything below is a disagreement about
*interpretation*, never about the walk.

---

## Verdicts at a glance

| # | claim under attack | verdict |
|---|---|---|
| 1 | "families are anti-predictive, z = −10.8…−48.9 / −5.6…−25.0" | **REFUTED.** Two independent errors compound; a direction-flipped control reproduces the whole effect. Corrected: endorsed 0.2773 vs opposed 0.2772, **p = 0.985**. |
| 2 | "366 cells, 1 survivor vs ~11 expected under a coin-flip null" | **STRUCK on both halves.** The receipt says **316 cells, 0 survivors**. The correct null expects **0.00**, so observing 0 is the null's own prediction and carries no information. |
| 3a | Phase 0: "the true RR is 2.0, not 1.5" | **CONFIRMED** at scale, 81,968/81,968 rows. Plus a new defect: the model's own feature frame carries **1.5 on 632,934/632,934 rows**. |
| 3b | Phase 0: the inverted contract's spread charge | **CONFIRMED correctly sized, not double-counted.** Residual +0.0001, t = +0.04. Phase 0's KILL verdict stands, independently reproduced. |
| 4 | *(unasked by anyone until now)* is the funnel underpowered? | **YES, decisively.** All five monthly verdicts — including February's PASS — are indistinguishable from zero (p 0.14–0.64). Five-month total **+0.95 R on 282 trades, p = 0.96**. |
| 5 | "completion rates are stationary, so it is not a regime problem" | **CONFIRMED and quantified.** Numbers reproduce exactly; the monthly swings are pure sampling noise (ANOVA p = 0.17). Strict homogeneity fails for 5 of 10 families on immaterial magnitudes. |

---

## 1. The benchmark — the anti-predictive claim is refuted

### 1.1 Phase 0's benchmark reproduced exactly, then corrected

I re-implemented `p0_full.driftless_p` verbatim and ran it on Phase 0's own walk output. It
reproduces the published table to the last digit. Then I corrected the one thing it gets wrong.

**The error.** `driftless_p` (`p0_full.py:83-108`) computes
`down = direction*(fill − stop)`, `up = direction*(target − fill)` using the **modelled fill
price**, which sits on the executable *entry* side, against `stop`/`target`, which are compared on
the executable *exit* side. It never moves the two into one quote frame. Under
`m1_price_basis=BarQuote.BID` a LONG's entry offset is `+s` and its exit offset is `0`; a SHORT's
are `0` and `+s` (`quote_side.py:385-412`). The tape-frame entry is `fill − direction·s`, so
`down' = down − s` and `up' = up + s`. The denominator `|T − S| = 3R` is unchanged, giving the
clean correction

> **`P_corrected = P_phase0 − spread_r / 3`**

for both directions. Because the error scales with the spread, it manufactured the *largest*
apparent anti-signal in exactly the families with the *largest* spread.

| family | barrier n | hit | Phase 0 bench / z | **corrected bench / z** | Δbench |
|---|---:|---:|---:|---:|---:|
| `liquidity_sweep_reclaim` | 18,642 | 0.2742 | 0.3598 / −24.99 | 0.3077 / **−10.19** | −0.0520 |
| `displacement_continuation` | 10,904 | 0.2353 | 0.3419 / −23.78 | 0.3150 / **−18.14** | −0.0269 |
| `structural_distance_extreme` | 11,008 | 0.3128 | 0.4074 / −21.61 | 0.3117 / **+0.27** | −0.0957 |
| `cross_asset_lead_lag` | 9,935 | 0.3113 | 0.3746 / −13.55 | 0.3132 / **−0.42** | −0.0614 |
| `session_open_range_break` | 1,699 | 0.1984 | 0.3417 / −12.55 | 0.3200 / **−10.83** | −0.0217 |
| `volatility_compression_expansion` | 313 | 0.1022 | 0.3349 / −8.79 | 0.2871 / **−7.43** | −0.0477 |
| `regime_transition_break` | 154 | 0.1234 | 0.3341 / −5.57 | 0.3153 / **−5.17** | −0.0188 |
| **POOLED** | **52,655** | **0.2773** | 0.3680 / **−44.70** | 0.3114 / **−17.49** | −0.0566 |

**Two of seven families move to indistinguishable from a driftless walk** — including
`structural_distance_extreme`, which was the plan's largest claimed anti-signal *and* its largest
claimed inverted edge, and `cross_asset_lead_lag`. The published range "z = −5.6…−25.0" becomes
**+0.27 … −18.14**.

**Phase 0 saw the signature and read it backwards.** Its §7(a) reassures that *"the magnitude does
grow with spread on three families… which is the expected signature of a spread that widens the
entry-side barrier gap, not of a fabricated signal."* Spread-scaling of the anti-signal is exactly
what a benchmark biased by `spread_r/3` produces. That sentence must be struck.

**The quote frame is verified, not assumed.** Per row, an intrabar stop must realise
`gross = −1 − drift − spread_r` (LONG) or `−1 − drift` (SHORT — the same spread, moved into the
barrier geometry). Measured on all barrier rows the identity holds to **|residual| < 1e-9 on
98.48 % / 98.38 % / 98.27 % / 98.68 %** of (STOP,LONG)/(STOP,SHORT)/(TARGET,LONG)/(TARGET,SHORT);
the ~1.6 % residual is the `SUCCESSOR_M1_OPEN_GAP` branch. Receipt: `frame_check2.py`.

> **A side-asymmetry worth recording separately.** Because the barriers are set on a bid-frame
> anchor for both directions, a LONG must travel the full `R` of tape to be stopped and `2R` to
> reach target, while a SHORT is stopped after `R − s` and needs `2R + s`. The sealed labeler
> therefore **structurally handicaps SHORT candidates by one spread of barrier geometry**. It is
> small (median `spread_r` 0.087) but it is systematic, it biases any family with a side imbalance,
> and no document names it. My per-row benchmark absorbs it; a pooled one cannot.

### 1.2 The finite horizon — and why the whole benchmark family is unusable

The orchestrator asked whether the benchmark needs a finite-horizon adjustment and whether
barrier-conditional subsetting biases it. **Yes to both, and the effect is larger than the
correction above.** A driftless walk with a time limit does not reach a barrier almost surely, and
conditioning on absorption before the horizon over-weights *fast* absorptions, which favours the
*nearer* barrier — the stop at 1R against the target at 2R. So the barrier-conditional target rate
is below the unconditional `d_down/(d_down+d_up)` **for any signal at all, including none.**

Rather than model it, I measured it. The MIRROR arm — direction flipped, geometry preserved — has
**no directional information by construction** and scores **z = −19.78** against the same corrected
benchmark, against the signal arm's −17.49. Both sit ~0.035 below their own driftless benchmark.

**A control that cannot carry information reproduces the entire "anti-predictive" finding.** Every
z-value in this program computed against a driftless-walk benchmark — the plan's −10.8…−48.9,
Phase 0's −5.6…−25.0, my corrected −17.49, Lane E's below-1/3 table — is measuring the contract's
geometry and horizon, not the entries.

### 1.3 The assumption-free answer

Three tests, increasing in rigour, all on the same 81,968 candidates:

| test | statistic | result |
|---|---|---|
| raw paired discordance (signal target vs mirror target) | binomial | z = +1.03, **p = 0.30** |
| difference-in-differences vs each arm's own corrected benchmark | z | +0.0079, **z = +2.54** |
| **geometry-matched two-sample** (endorsed vs opposed, like-for-like side and geometry) | two-proportion z | 0.2773 vs 0.2772, **z = +0.02, p = 0.985** |

Economics on the same set: signal direction **−0.2725 R/fill**, flipped direction **−0.2762**,
difference +0.0037 (t = +0.60). **Taking the other side of every candidate loses the same money.**

Per family, geometry-matched: `cross_asset_lead_lag` +3.38 and `displacement_continuation` +2.64
and `session_open_range_break` +2.75 are *pro*-predictive; `structural_distance_extreme` −2.81 and
`liquidity_sweep_reclaim` −2.60 are *anti*; three are null. Against seven looks, Bonferroni at
0.05 admits only `cross_asset_lead_lag` (p = 7.2e-4), positive. It is a wash.

### 1.4 What the pool actually is

For a driftless tape, `E[terminal_gross_r] = −E[spread_r]` **exactly**, for any geometry,
direction or horizon (optional stopping: the P&L is the tape travel minus one crossed spread).
Measured over 74,249 MARKET fills:

| | `E[gross]` | `−E[spread_r]` | residual | t |
|---|---:|---:|---:|---:|
| full population, signal direction | −0.1331 | −0.1409 | **+0.0078** | +1.84 |
| full population, flipped direction | −0.1354 | −0.1409 | +0.0055 | +1.29 |
| cost-eligible (`cost_r ≤ 0.20`), signal | −0.0544 | −0.0563 | **+0.0019** | +0.37 |
| cost-eligible, flipped | −0.0540 | −0.0563 | +0.0023 | +0.44 |

By month (cost-eligible): +0.029 / −0.008 / −0.015 / −0.006 / +0.005. Nothing anywhere.

> **The single sentence that replaces the funnel plan's diagnosis.** The candidate pool is
> **directionally uninformative — a fair coin — and its measured negative expectancy is exactly its
> own transaction cost.** `E[net] = −E[cost_r] + 0.008 ± 0.004`. Not "anti-predictive", not
> "uniformly negative", not "the pool has the sign reversed".

This is a materially different diagnosis with a different repair. Anti-predictive says *fix or
invert the signal*. Zero-edge-minus-cost says *the cost term is 100 % of the loss*, which points
at instrument selection, entry hour, and stop width — and at the fact that the ceiling of every
one of those levers is break-even, not profit. See `LANE_G_RECONCILIATION_V1.md` §4.

---

## 2. The pool scan — the null was refuted by its own data

**First, the receipt does not say what the document says.** `POOL_ANSWERS.json`
(sha256 `a9a9d3c1…`, identical in `/private/tmp` and the durable hold) reports:

| scan | cells meeting size | survivors (all 5 months positive) | coin-flip E |
|---|---:|---:|---:|
| family | 9 | **0** | 0.28 |
| family × symbol | 141 | **0** | 4.41 |
| family × session | 122 | **0** | 3.81 |
| family × side | 20 | **0** | 0.62 |
| symbol | 24 | **0** | 0.75 |
| **total** | **316** | **0** | **9.88** |

The published text says **366 cells, 1 survivor, ≈11 expected**. Every `top` list in the receipt is
empty. **Three numbers in the headline sentence are unsupported by the cited receipt.**

**Second, and more important, the null is meaningless.** `cell_scan` sets
`expected_survivors_under_coinflip_null = sized × 0.5^5` (`puzzle_pool.py:117`), which assumes
`P(month mean > 0) = 0.5` per cell-month — true only if every cell's *true* mean is exactly zero.
The same study measures the pool mean at ≈−0.09 R per resolved candidate. Under a negative mean,
`P(month mean > 0)` is far below 0.5 and the expected survivor count collapses.

I re-ran the scan under two defensible nulls, 500 permutations each (`pool_null.py`):

| scan | observed all-5-**positive** | coin-flip E | **N2** E (cell labels permuted within month) | N2 p95 | **N3** E (month labels permuted within cell) |
|---|---:|---:|---:|---:|---:|
| family | 0 | 0.28 | **0.00** | 0 | 0.00 |
| family × symbol | 0 | 4.41 | **0.00** | 0 | 2.37 |
| family × session | 0 | 3.81 | **0.00** | 0 | 0.39 |
| family × side | 0 | 0.62 | **0.00** | 0 | 0.00 |
| symbol | 0 | 0.75 | **0.00** | 0 | 0.00 |
| **total** | **0** | **9.88** | **0.00** | **0** | **2.75** |

* **N2** is the null the claim needs: *no cell differs from the pool*. Cell labels are permuted
  within month, preserving cell sizes, month effects and the pool's own negative mean. It expects
  **0.00 survivors with a 95th percentile of 0.** Observing 0 is precisely what "there is no edge
  anywhere" predicts — **and precisely what "there is an edge somewhere" would also often predict,
  because the scan has no power.** The scan cannot distinguish the two hypotheses. It re-states
  that the pool mean is negative and nothing else.
* **N3** (the orchestrator's suggestion — month labels permuted within cell, preserving each cell's
  own mean) expects 2.75; observing 0 is a weak signal of within-cell month instability
  (Poisson p ≈ 0.06), not of edge.
* The informative tail is the other one: **209 cells are all-5-negative against an N2 expectation of
  272.1.** Fewer uniformly-negative cells than a homogeneous pool would produce means there *is*
  real cross-cell heterogeneity in the mean — and §1.4 identifies it as **cost** heterogeneity, not
  edge heterogeneity.

**The scan restated correctly.** `net + cost_r` is the cost-free edge (§1.4), so the pool question
should have been asked on that. Over 146,745 filled occurrences and 164 family×symbol cells with
n ≥ 150, BH q ≤ 0.10 admits 21 cells, 19 of them positive — but **17 of the 19 are LIMIT-family
cells**, which `LANE_G_RECONCILIATION_V1.md` §2.3 shows are a half-spread fill-selection artifact.
The two MARKET-family survivors are `session_open_range_break|AUDJPY` (n 288, +0.181, q 0.019, 5/5
months) and `cross_asset_lead_lag|NAS100` (n 753, +0.131, q 0.065, 4/5). Both are small, both are
inside a 164-cell search, and neither is a program. Receipt: `pool_edge.json`.

---

## 3. Phase 0's two corrections — both verified

### 3a. RR = 2.0 — CONFIRMED, and there is a second defect underneath it

Measured directly from the sealed compact event sinks over all five months
(`laneg_walk.py` → `mirror.py`):

* `|take_profit_1 − entry_price| / |entry_price − stop_loss|` = **2.0 to within 1e-9 on
  81,968 / 81,968 rows** (min = max = 2.0000000000);
* the `risk_reward_ratio` field is **2.0 on 81,968 / 81,968**;
* `dynamic_geometry_policy = momentum_exhaustion` on **81,968 / 81,968**;
* `raw_target_r = 2.0`; `policy_target_r = 2.0` where present (37,377 rows, `None` on the rest).

Phase 0's largest correction is independently confirmed, and its attribution to
`dynamic_execution_policy.py:167-186` is consistent with every field on the row.

> **NEW — and it explains how the 1.5 error happened, because 1.5 is genuinely in the artifact.**
> In the model's own predecision feature frame,
> **`target_distance_atr / stop_distance_atr` = 1.5 exactly on 632,934 / 632,934 rows** — every
> candidate occurrence in all five months. The generator writes it that way
> (`current_ob_retest_geometry_candidate.py:23,181`: `TARGET_DISTANCE_D = 1.5`). So the ridge is
> trained and scored on a feature vector that encodes a **1.5R** target while the order it is
> predicting carries a **2.0R** target. That is a live modelling defect, not a documentation one:
> `target_distance_atr` is a real feature and it is wrong by 33 % on every row. It also means the
> funnel plan's 1.5 was not carelessness — it read one part of the artifact and Phase 0 read
> another, and **the artifact disagrees with itself.**

### 3b. The inverted-spread charge — correctly sized, NOT double-counted

The concern was that Phase 0's inverted arm might be charged the spread twice. It is not.

* **The arithmetic identities hold exactly**: `net == gross − deductible` and
  `cost_r == spread_r + deductible` each fail on **0 of 74,249** rows. So the walk carries exactly
  one spread, mechanically inside `terminal_gross_r`, and adds the slippage/commission/swap
  deductible once, rescaled by the risk-unit ratio (correct: the same price cost is half as many R
  when the risk unit doubles).
* **The martingale test on the inverted arm** — if the inverted contract were charged two spreads,
  `E[gross_inv] + E[spread/reward]` would come out at `−E[spread]`, not zero. Measured pooled:
  `E[gross_inv] = −0.0702` against `−E[spread_inv] = −0.0703`, **residual +0.0001, t = +0.04**
  (n = 74,044). Per family the residual ranges −0.014 to +0.018 with |t| ≤ 3.2.

**Phase 0's KILL verdict stands and is independently reproduced.** My INV arm matches its INV arm
on 81,968 rows with max |net difference| 0.0. The inversion is negative in every family. What must
be struck from Phase 0 is only its §2/§7(a) claim that the anti-signal survives correction — see §1.

---

## 4. Underpower — the question nobody asked, and it changes the verdict on the program

Per-trade `actual_net_r` from the sealed `selected_candidates` of all three validation results,
primary policy `market_top_abstain` (`power.py`, `final_checks.py`):

| month | n | total R | mean | se | t | p | 95 % CI on the total |
|---|---:|---:|---:|---:|---:|---:|---|
| February | 105 | **+14.17** | +0.1349 | 0.1094 | +1.23 | **0.220** | [−8.61, +36.94] |
| April | 49 | −7.74 | −0.1580 | 0.1316 | −1.20 | 0.236 | [−20.71, +5.22] |
| May | 17 | +5.13 | +0.3018 | 0.2690 | +1.12 | 0.278 | [−4.56, +14.82] |
| June | 45 | +3.96 | +0.0881 | 0.1888 | +0.47 | 0.643 | [−13.16, +21.09] |
| July | 66 | **−14.57** | −0.2207 | 0.1475 | −1.50 | 0.139 | [−34.00, +4.87] |
| **June+July** | 111 | **−10.60** | −0.0955 | 0.1168 | −0.82 | **0.415** | [−36.29, +15.08] |
| **all five** | **282** | **+0.95** | **+0.0034** | 0.0677 | **+0.05** | **0.960** | **[−36.63, +38.53]** |

> **Not one monthly verdict in this program is distinguishable from zero.** February's **PASS** is
> p = 0.22. April/May's **REJECT** is p = 0.24 / 0.28. June/July's **REJECT** is p = 0.42. And the
> five months together are **+0.95 R on 282 trades, p = 0.96** — dead flat.

The orchestrator's framing of June+July as −16.72 R uses the censoring-conservative
`worst_case_net_r`; the realised figure is −10.60 R. Neither is significant.

**Power.** Per-trade sd of the selected book is **1.1369 R**. At the 282 trades actually taken the
minimum detectable edge at 80 % power (α = 0.05, two-sided) is **±0.1897 R/trade = ±53.5 R over
five months**. The observed +0.0034 is well inside it.

**Trades needed**, at the observed cadence of 56 trades/month:

| true edge | trades for 80 % power | months | what that is per month |
|---:|---:|---:|---:|
| 0.30 R/trade | 113 | **2.0** | 16.9 R |
| 0.20 | 254 | **4.5** | 11.3 R |
| 0.15 | 451 | **8.0** | 8.5 R |
| 0.10 | 1,014 | **18.0** | 5.6 R |
| 0.05 | 4,058 | **71.9** | 2.8 R |

**The correct verdict on the funnel's five-month read is "underpowered", not "rejected".** Five
months at this cadence can only resolve an edge of ≈0.19 R/trade — roughly **10 R/month**, which is
larger than any edge the program ever claimed. To resolve the 0.10 R/trade scale the funnel was
built for takes **18 months** of the same cadence, or a book that trades ~3× more often.

**This does not rescue the funnel** — §1.4 measures the pool's gross edge at zero on 74,249 fills,
where the standard error is 0.004 rather than 0.068, and *that* measurement is decisive. But it
does change what should be said about the *method*: the monthly one-shot frozen read, as
constructed, cannot resolve the effect sizes it is being used to adjudicate. Any future window read
should be pre-registered with its power stated, or it will keep producing verdicts that are
sampling noise wearing a decision's clothes.

---

## 5. Stationarity — confirmed, and it confirms the noise story

The published figures reproduce exactly. `liquidity_sweep_reclaim` target rate by month:
**0.221 / 0.230 / 0.224 / 0.219 / 0.216** (published 22.1/23.0/22.4/21.9/21.6 %).
`structural_distance_extreme`: **0.298 / 0.314 / 0.314 / 0.313 / 0.310** (published 29.8–31.4 %).

**Strict homogeneity is a stronger claim than the data supports**, and for five of ten families a
χ² test on the full TARGET/STOP/TIME_STOP mix rejects it:

| family | χ² p | | family | χ² p |
|---|---:|---|---|---:|
| `current_fvg_fill` | 1.05e-12 | | `structural_distance_extreme` | 0.204 |
| `session_open_range_break` | 2.27e-10 | | `current_ob_retest` | 0.293 |
| `current_breaker_re_entry` | 1.63e-03 | | `regime_transition_break` | 0.310 |
| `liquidity_sweep_reclaim` | 2.03e-02 | | `displacement_continuation` | 0.088 |
| `volatility_compression_expansion` | 1.40e-02 | | `cross_asset_lead_lag` | 0.056 |

The magnitudes are immaterial (`liquidity_sweep_reclaim`'s target rate moves 0.216→0.230 across
five months on n≈4,000–5,000/month). **Say "stationary to within ±0.01 on the target rate", not
"stationary"** — the conclusion drawn from it is unaffected, but the χ² is easy for a reviewer to
run and it will read as an overclaim.

**The inference is confirmed and is now quantified — this is the strongest independent support for
the noise reading.** Stationary completion rates and wild monthly swings in the *selected* book are
not merely compatible; the swings are exactly what a zero-mean process produces at these counts:

| month | n | total | sd(total) under a zero-mean null | z |
|---|---:|---:|---:|---:|
| feb | 105 | +14.17 | 11.65 | **+1.22** |
| apr | 49 | −7.74 | 7.96 | −0.97 |
| may | 17 | +5.13 | 4.69 | +1.09 |
| jun | 45 | +3.96 | 7.63 | +0.52 |
| jul | 66 | −14.57 | 9.24 | **−1.58** |

One-way ANOVA across the five months: **F = 1.608, p = 0.172**. Kruskal–Wallis: **p = 0.111**. The
five monthly means are not distinguishable from a single common mean. **The month-to-month swing
is selection noise, not regime** — and the population underneath it is stationary because it has
nothing in it to shift.

---

## 6. What must be amended, struck, or is now independently confirmed

### STRIKE

| where | text |
|---|---|
| `FUNNEL_ROOT_CAUSE_AND_V2_PLAN.md` §0 | *"it is that **every candidate family is directionally anti-predictive**: against a driftless-walk benchmark of a 40 % hit rate… the families deliver 10–31 %, at z = −10.8 to −48.9"* |
| `FUNNEL_ROOT_CAUSE_AND_V2_PLAN.md` §1, row *"Does the pool contain edge anywhere?"* | *"366 conditioned cells… 1 survivor… against ≈11 expected by coin-flip null. The pool is not 'mostly bad with gems' — it is uniformly negative."* Receipt says 316/0; correct null expects 0.00. |
| `FUNNEL_ROOT_CAUSE_AND_V2_PLAN.md` §3 preamble + amendment banner | *"the families still run z = −5.6…−25.0. The pool is anti-predictive"* |
| `PHASE0_INVERSION_TRUTH_V1.md` §0, §2, §10 | *"The anti-signal itself is real and survives correction… z = −5.6 … −25.0 — so §1 and §2 of the plan stand"* and *"The anti-predictive finding itself, at corrected magnitudes"* |
| `PHASE0_INVERSION_TRUTH_V1.md` §7(a) | *"The magnitude does grow with spread on three families… which is the expected signature of a spread that widens the entry-side barrier gap, not of a fabricated signal."* It is the signature of a benchmark biased by `spread_r/3`. |

### AMEND

| where | to what |
|---|---|
| `FUNNEL_ROOT_CAUSE_AND_V2_PLAN.md` §1 row *"Is it the sleeves/families?"* | keep "all 10 families negative per candidate" (true), replace the causal reading: the pool is **directionally uninformative and its loss equals its cost**, `E[gross + spread_r] = +0.008 ± 0.004`, direction-flipped control +0.006. |
| `FUNNEL_ROOT_CAUSE_AND_V2_PLAN.md` §1 row *"Is it costs?"* — *"**No.**"* | **invert it.** Costs are not a tenth of the problem; on the correct accounting they are **all** of it. The 0.047–0.049 R figure is the cost of the *selected* slice; over the pool, `E[cost_r]` is **0.2812** (MARKET, full population, `E[net]` −0.2730) and **0.1057** (cost-eligible, `E[net]` −0.1039) — in both cases equal to the entire loss to within +0.008. |
| `FUNNEL_ROOT_CAUSE_AND_V2_PLAN.md` §1 row *"Is it regimes?"* | keep "No", tighten to "stationary to within ±0.01 on the target rate"; add the ANOVA (p 0.172) as the positive evidence, which is stronger than the stationarity argument it currently rests on. |
| `FUNNEL_ROOT_CAUSE_AND_V2_PLAN.md` §1 row *"Is it geometry?"* | the target was not merely "unchosen" — **the feature frame and the order disagree**: `target_distance_atr/stop_distance_atr` = 1.5 on 632,934/632,934 rows while the traded RR is 2.0 on 81,968/81,968. |
| all five monthly verdicts (`FEBRUARY_…_R2`, `APRMAY_READ_RESULT`, `JUNJUL_READ_RESULT`, `THREE_MONTH_POSTMORTEM_V1`) | stamp each with its p-value and CI. February's PASS is p = 0.22; June/July's REJECT is p = 0.42; the five together are p = 0.96. **Underpowered, not rejected.** |

### CONFIRMED — independently, and now stronger than when published

* **Phase 0's RR = 2.0 correction.** 81,968/81,968, three independent fields.
* **Phase 0's inverted-spread correction.** Correctly sized, not double-counted; residual +0.0001, t = +0.04.
* **Phase 0's KILL verdict on the inversion.** Reproduced on 81,968 rows, 0 mismatches, max |Δnet| 0.0.
* **Phase 0's control** (its walk reproduces the sealed cache exactly). Verified a second time by a third harness.
* **The stationarity inference** (§5) — and the ANOVA makes the noise reading decisive rather than suggestive.
* **The selector's relative skill and the concentration/momentum-chasing amplifiers** (plan §2) — not re-tested here; nothing in this audit bears on them.

### NEW (not previously claimed by anyone)

1. **The pool is a fair coin charged its own spread.** `E[net] = −E[cost_r] + 0.008 ± 0.004`.
2. **The feature frame carries RR 1.5 while the order carries RR 2.0**, on every row of all five months.
3. **The labeler structurally handicaps SHORT candidates by one spread of barrier geometry** (§1.1).
4. **The five-month program is underpowered by ~2×** relative to the effect sizes it adjudicates (§4).

---

*Everything above is reproducible from `lane_g_receipts/` against `/private/tmp/w21-puzzle-cache`
(durable copy at `hermes-evidence-hold-20260727/w21-puzzle-cache-20260812/`), the sealed candidate
roots `/private/tmp/w21-market-top-{feb-r2,aprmay-r3,junjul-r4}`, and the frozen M1 sources at
`lane-inputs-true-utc-hold-20260805`. No live path, config, or VPS artifact was read or written.*
