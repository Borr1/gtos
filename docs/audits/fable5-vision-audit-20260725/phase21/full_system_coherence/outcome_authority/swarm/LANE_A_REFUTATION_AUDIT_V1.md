# LANE A — the refutation audit

**Commission (owner, via the swarm orchestrator):** *"so many refuting happening, so many killing of
ideas over the simplest and smallest of things… all these refutes and refuting is not supposed to
kill, the idea is supposed to build and actually do and improve things."*

**Scope.** Audit the **kills**, not the findings. For every significant refutation in this program's
history: what was killed, what killed it, was the killing evidence held to the same standard the
estate holds a positive finding to, and what would revival cost.

**Method.** Read-only. Every load-bearing claim below was re-measured from source — raw sealed rows,
the committed code, and the sealed validation JSONs — not read out of the receipt that made the
claim. Receipts: `swarm/laneA_receipts/LANE_A_RECEIPTS.json`. Nothing live, no config, no VPS.

---

## 0. The verdict in one page

**The program's kills are, with two exceptions, technically correct. The problem is not that they are
wrong; it is that they are asymmetric.** A positive finding in this estate must clear a population
rule, a cost band, fold positivity, retention, expectancy, lifetime, fidelity, sample, *and* a
Benjamini-Hochberg bill against an all-declared family that grows monotonically with the calendar. A
kill must clear one number, and that number is never given an error bar. There is **no power
calculation, no minimum-detectable-effect statement, and no confidence interval anywhere in phases
19–21**, on either side of any verdict.

Three specific results:

1. **The five-month funnel verdict on the *selected book* is underpowered in both directions and is
   published as a one-directional kill.** Pooled over all five sealed months the selected book is
   **+0.954 R on 282 trades, t = +0.050**. February's +14.168 is t = +1.234; July's −14.566 is
   t = −1.497. Zero sits inside every monthly and pooled interval. The honest label is *"no detectable
   edge either way"*, not *"reliable loss"* and not *"February was the outlier."* **The estate already
   measured this and set it aside**: `THREE_MONTH_POSTMORTEM_V1.md` §5.4 says BAR-2, the bar carrying
   an interval, *"would not have passed even February"* — and BAR-3, a point-estimate bar, was ratified
   instead. *(The separate, pool-level kill — that the candidate families are anti-predictive — is
   sound and heavily powered. The program's closure survives. Its stated reason does not.)*

2. **The CS inverted-breaker REJECT is unsound as stated, and correct in outcome for two reasons CS
   never gave.** The exact permutation null was available, was cheaper to compute than the Monte-Carlo
   estimate the gate used, **was computed**, and **admits at the same 59-member bill**
   (q = 0.0576, or 0.0864 on the matched convention). The stated REJECT (q = 0.1534) is an artifact of
   estimator choice. The candidate should nonetheless stay dead: at the wave-21 slippage authority it
   rejects under the *exact* null too, and its target rate is **14.3× the driftless first-passage rate
   for its own geometry** — an artifact signature no session tested.

3. **Phase 0's kill of the inversion thesis is sound, and it is the best-executed kill in the
   program.** Both of its load-bearing corrections check out independently: the true RR **is** 2.0 (I
   recomputed it from raw sealed rows, not from Phase 0's receipt), and the inverted-spread charge is
   **not** double-counted and is correctly sized — in fact Phase 0 chose the *favourable* denominator
   for the thing it was killing. Do not reopen it.

**One defect nobody in the program has noticed, found while checking (3):** across the **same 632,934
candidate occurrences**, the funnel ridge's training features encode a **1.5** risk-reward geometry
(`target_distance_atr / stop_distance_atr = 1.5000`, no dispersion) while the sealed rows the labeler
resolves carry **2.0** (no dispersion). One population, two contradictory geometries. That is a live
feature/label mismatch in the funnel V1 stack, and it is where the RR-1.5 premise came from.

---

## 1. The standard I applied

I held each kill to the four tests the estate applies to a positive finding:

| test | question |
|---|---|
| **path-complete** | does the killing measurement resolve the same object, through machinery that can express it? |
| **cost-true** | is the cost charge correctly sized, once, and in the right units? |
| **out-of-sample** | is the kill measured where the thing was not fitted? |
| **premise-verified** | was the assumption the kill rests on checked, or inherited? |

Plus one the estate does not apply to itself:

| **symmetric** | did the kill clear the same bar the finding had to, *including an error bar*? |

---

## 2. Adjudication A — the CS inverted-breaker REJECT

`phase19/SESSION_CS_BREAKER_FOLDS_RESULT.md`; gate receipt
`phase19/receipts/CS_CURRENT_BREAKER_RATIFIED_GATE_V1.json`.

**What was killed.** `cq_current_breaker_inverted_target_5d_stop_0p25d_v1` — an inverted
`current_breaker_re_entry` contract, target 5 D, stop 0.25 D where D = the original stop distance
(`src/components/current_breaker_re_entry_repair.py:28-29, 92-93`), reward:risk **20 : 1**.

**Economics at the kill.** Three chronological OOS folds, all positive: +11.252 / +7.454 / +3.852
R/trade. Equal-by-fold pooled **+7.519 R**. Drop-the-best retention 75.18 %. Full-lifetime **+12.592
R/trade** over 6,536 priced RECORDED trades. **Every frozen gate passed except significance.**

**What killed it.** One statistical gate: `q = 0.1534` from `raw p = 0.0026` under Benjamini-Hochberg
at α = 0.10 across a declared family of 59.

### 2.1 What checks out

- **The BH arithmetic is exactly right.** 0.0025997400 × 59 = 0.15338466. The candidate is rank 1, so
  BH here is *identical to Bonferroni*.
- **The gate ran as ratified.** `CANDIDATE_BOOK_V1`, all-declared basis, `B_balanced`, α = 0.10 — the
  rule Borhen ratified on 2026-07-30. Declaration preceded every economic read; the plan was committed
  at `7d2f2d4f3` before April or May economics were decoded. CS's process discipline is not in
  question anywhere in this section.

### 2.2 One objection I raised against the kill, and then refuted myself

The p-value is exactly `26/10001` — a Monte-Carlo block permutation, 10,000 draws, 25 exceedances.
The BH rank-1 bar is 0.10/59 = 0.0016949, and the Clopper-Pearson 95 % interval on the true p is
[0.001619, 0.003688] — **the bar is inside the interval**, which looked like AO's B1321 resolution-floor
problem one register over.

**It is not.** The operational question is whether a re-seeded run would flip the verdict:
`P(k ≤ 15 | Binomial(10 000, 0.0026)) = 0.0141` — about **0.3 of 20 seeds**. AO's pair admission
flipped on **4 of 20**. The CS Monte-Carlo verdict is seed-stable. **This objection fails and I record
it as failed.**

### 2.3 The defect that does hold: the exact null was available, cheaper, and admits

`phase21/WAVE21_INTEGRATION.md` §10, reporting a re-run of this very gate:

> exact-null tail **2 → 11 of 2048**; MC tail **25 → 80 of 10,000**

The block-permutation space has **2,048 achievable sign assignments** (2¹¹). Enumerating it exactly
costs 2,048 evaluations. The gate instead drew **10,000** Monte-Carlo samples from that same
2,048-point space — *more expensive and less accurate*. And the two estimators disagree on the verdict:

| null estimator | p | q at m = 59 | verdict at α = 0.10 |
|---|---:|---:|:--|
| **exact enumeration**, k/n | 2/2048 = 0.000977 | **0.0576** | **ADMIT** |
| **exact enumeration**, (1+k)/(n+1) | 3/2049 = 0.001464 | **0.0864** | **ADMIT** |
| Monte-Carlo, (1+k)/(N+1) — *what the gate used* | 26/10001 = 0.002600 | 0.1534 | REJECT |

`0.0576` is not my arithmetic — it is the number §10 itself prints, labelled **ADMIT**.

**This is shipped-code behaviour, not one session's slip.**
`src/research_infra/validation_integrity/perm_null.py:196-202` always draws random sign vectors; there
is **no branch that enumerates exactly when the achievable space is small**, and no exact-enumeration
path exists anywhere in `src/`. And `src/research_infra/walkforward/gate.py:1027-1040` computes a
`p_floor` into telemetry but `:1151-1152` refuses only when `p_floor >= spec.alpha` — so **nothing in
the pipeline ever relates an observed p to its own resolution.** AO proposed exactly that guard at
B1322 (a 2× headroom rule that would have caught its own arm and nothing else in its session); **it was
never implemented.**

**Consequence:** every gate verdict in this program whose p sits within Monte-Carlo noise of its BH bar
was decided by a random seed and an estimator choice, and no receipt says so.

### 2.4 The family denominator, audited

The declared family is `CANDIDATE_BOOK_V1` at the V27 tip, 59 members, whose own stated purpose is
*"The pool an arming decision draws from: every sleeve the live config's own resolvers can build."*

| finding | detail |
|---|---|
| **the judged candidate is not a member by that rule** | it is not a sleeve the live config's resolvers can build. V27's `membership_identity_claim` records it as *"rebased from the parallel fork CQ_CANDIDATE_FAMILY_V…"* — an integration decision, not the family's membership rule. |
| **58 of 59 members were never tested** | `family_members_padded_at_p1 = 58`, `n_sleeves_judged_this_run = 1`. BH bought exactly zero power over Bonferroni; the family is pure denominator. |
| **4 literal duplicates** | `ch_p1_hist::m1::mx_btcusd_target5_redacted_account`, `::m2::mx_ethusd…`, `::m2::mx_avausd…`, `::m2::mx_nzdjpy…` are re-tests of members 15, 17, 14, 22 — **already counted**. |
| **19 nested near-duplicates** | 5 × `overlay_metalabel_fx_jpy_*` (nested thresholds on one sleeve), 5 × `thr_sub_xvol_pullback_*` (ditto), 6 × `mxf_volume_surge_reversal_*` (one mechanism, six symbols), 3 × `mxf_energy_fvg_retest_*` (one mechanism, three symbols). |
| **direct precedent, ignored** | wave 8 found the historical 69-look family **double-counted** — W's and X's looks were subsets of AA's 32 — and that published q-values were **over-corrected**. The same defect class is present here and was not re-checked. |
| **the bar moved, not the evidence** | `CANDIDATE_BOOK_V1` was **32** declared at V1 (ratified 2026-07-30) and **59** at V27 (2026-08-01). The largest family at which this candidate still admits on the MC p is **38**. An identical candidate tested two days earlier admits under every convention. |
| **the estate says so itself** | `gate_result.family.n_trials_basis`: *"FLOOR, not a measurement. No trial-budget ledger artifact exists anywhere in the repo."* |

### 2.5 Is +12.59 R/trade at 5D/0.25D economically plausible? No — and this is the finding

Independent question, independent answer. Under a driftless walk,
`P(target first) = 0.25 / (5 + 0.25) = 4.76 %`.

| capture | TARGET / STOP / HORIZON | target share | **× driftless** | z vs driftless |
|---|---|---:|---:|---:|
| April 2026 | 2,506 / 738 / 427 (n 3,671) | 68.3 % (77.3 % of barrier-resolved) | **14.3× (16.2×)** | **+194** |
| May 2026 | 1,832 / 865 / 674 (n 3,371) | 54.3 % (67.9 %) | **11.4× (14.3×)** | **+154** |

**The program killed its own inversion thesis on families running 0.7–0.9× their driftless rate at
z = −5.6 … −25.0.** It never once pointed the same benchmark at a candidate that came in *above* it.
A 20:1 contract delivering a 68 % hit rate is not an edge; it is a measurement defect.

Three corroborating facts, all from the estate's own receipts:

- The repaired 0.25 D stop is **a fraction of a spread wide**. CS's own cost decomposition puts mean
  spread at **0.730 R** against that 0.25 D risk unit. In the funnel cache the family's median
  `spread_r` is 0.0890 in original units = **0.356 R** in repaired units.
- The family's entry rests a **median 3.75 D** from the market (`distance_to_limit_risk`, p75 6.71,
  p90 10.41), non-marketable on 97.1 % of rows — so the 5 D target sits at or beyond the current market
  on **37.3 %** of rows.
- **Two sessions disagree about whether this object is even resolvable, and nobody reconciled them.**
  `PHASE0_INVERSION_TRUTH_V1.md` §6 measured that the committed labeler **cannot** express an inverted
  LIMIT contract for this exact family — **4,258 of 4,360 rows (97.7 %) censor** as
  `CENSORED_SUBMISSION_BAR_LIMIT_TOUCH_ORDERING`, structurally, because `limit_touched` is hardwired to
  direction (`quote_side.py:1249-1250`). CS resolved **3,671 / 3,671 with zero censoring and zero
  ambiguity** through a different path stack (the CK sidecar). Phase 0 wrote *"the two are not in
  conflict and neither supports the other"* — true of the economics, and it leaves the contradiction
  about the machinery standing.

### 2.6 The kill that actually holds — and CS did not make it

`WAVE21_INTEGRATION.md` §10 / B3406. At the wave-21 artifact-bound slippage authority, six of the
sleeve's sixteen symbols (AUDJPY, CHFJPY, EURJPY, UKOIL.cash, USOIL.cash, XAGUSD) have **no reconciled
price-domain slippage sample** and fail closed. Evaluable universe: 10 of 16 symbols, 63.556 % of
trades. Exact null **11/2048 → q = 0.317**; MC null 80/10,000 → q = 0.3169. **REJECT under both
estimators, both conventions, and any family down to m ≈ 18.**

### 2.7 Adjudication

> **The stated kill is UNSOUND. The outcome is CORRECT, on evidence CS did not have and did not
> produce. Do not revive the candidate — re-kill it properly, and fix the estimator.**

And the dangerous part: CS's own repair queue names **BREADTH** — *"pool the mechanism across a
genuinely declared family, or evaluate it through the book-level diversifier door."* That tells a
successor the way to revive this candidate is to **change the family accounting**. Under §2.3–2.4 that
would work — and it would arm a 14×-driftless artifact.

**Correct order of work, cheapest first:** (1) re-issue the verdict under the exact null so the record
says what actually decided it; (2) the driftless check and the Phase-0-vs-CS censoring reconciliation
(~1 session, no new data) — **if the candidate fails these it is dead and the capture is not worth
buying**; (3) only then, the six-symbol slippage capture.

---

## 3. Adjudication B — Phase 0's kill of the inversion thesis

`PHASE0_INVERSION_TRUTH_V1.md` (commit `728440500`). **Verdict: SOUND. Do not reopen.**

Phase 0 is the only kill in this program that was pre-registered with a numeric gate and a named kill
branch, controlled against the sealed cache, adversarially attacked by its own author, sensitivity-banded,
and honest about refuting its own most-feared failure mode by ~250×. It reproduces the sealed cache
exactly (81,968 rows, 0 mismatches, max difference 0.0), which is what licenses everything after it.

### 3.1 Correction (a) — "the true RR is 2.0" — **CONFIRMED INDEPENDENTLY**

I did not take this from Phase 0's receipt. I recomputed
`|take_profit_1 − entry_price| / |entry_price − stop_loss|` **from the raw sealed compact `missed` rows**
across all three sealed candidate roots — **632,934 rows, every one 2.0000**, with the independent
`risk_reward_ratio` field agreeing on all 632,934 and every row stamped
`dynamic_geometry_policy: momentum_exhaustion`. (Phase 0 checked its 81,968 MARKET-family rows; this
covers the full population including the LIMIT families.)
Source confirmed at `src/research/dynamic_execution_policy.py:167-186`
(`momentum_exhaustion_policy(..., final_target_r: float = 2.0)`). **The plan's 1.5 was wrong; Phase 0's
2.0 is right; the 75–80 % edge removal follows.**

### 3.2 A defect found while checking it, which nobody in the program has noticed

The funnel ridge's own **training features** encode 1.5: over the plan's five-month feature cache,
`target_distance_atr / stop_distance_atr` is **1.5000 on 632,934 of 632,934 rows** — a single value, no
dispersion.

**The row counts are identical because it is the same population.** The same 632,934 candidate
occurrences carry a **2.0** geometry in the sealed rows the labeler resolves and a **1.5** geometry in
the features the model is fitted on. That is not an approximation gap; it is a one-to-one contradiction.

**The model was trained on features describing a contract the labeler did not run.** This is where the
1.5 premise came from — it was not carelessness, it was read off the feature layer, which is genuinely
1.5. It is a live feature/label geometry mismatch in the funnel V1 stack, independent of Phase 0, and
it is unrecorded anywhere. It also sharpens Phase 0 §10's own point: the effective target is not the
sanity floor it names, *and the model cannot see the real one.*

### 3.3 Correction (b) — the inverted-spread charge — **NOT DOUBLE-COUNTED, AND CORRECTLY SIZED**

The concern was legitimate — an over-charging kill is as wrong as an under-charging finding. It does
not hold. Four independent checks:

1. **Component identity.** On a sealed day, `cost_r == spread_r + expected_slippage_r + commission_r +
   swap_cost_r` on **5,195 of 5,195 rows, zero mismatches**. So `cost_r` *does* contain spread.
2. **The sealed deductible excludes it.** `candidate_funnel_analysis.py:163-166` sums **only**
   `expected_slippage_r + swap_cost_r + commission_r`, and `net = gross − deductible`. Spread is
   deliberately not in the deductible.
3. **Spread enters exactly once, mechanically.** The entry transacts on the executable *entry* side and
   the barriers are compared against the executable *exit* side (`quote_side.py:385-413`, `:1218-1247`)
   — one round trip, in both directions, for both arms.
4. **The rescale is right.** Phase 0's inverted deductible is the same three terms × `risk/risk_inv`.
   Every term is a fixed **price** amount; the inverted risk unit is 2× the original; so each is halved
   in R. Correct — and *generous* to the inversion.

**And the denominator choice runs the same way.** The `cost_r ≤ 0.20` eligibility gate is applied in
**original** units, which excludes exactly the expensive rows where the inversion does worst
(`structural_distance_extreme`: full population −0.2848, cost-eligible **−0.0560**). Phase 0 killed the
thesis on the population most favourable to it. Confirmed further by the low-spread-band re-walk, which
moves every family by only +0.0014…+0.0041 against a gate of +0.03.

### 3.4 The one caveat worth recording (not a challenge to the verdict)

The three LIMIT families are **bounded, not measured** — including `current_fvg_fill`, the estate's
largest at 305 k candidates, bounded at −0.0488 via a bias model
(`bias = 0.0189 + 0.5053 × median spread_r`, corr 0.96) fitted on seven *MARKET* families. Phase 0 says
so plainly and argues the bias runs conservative (an inverted LIMIT is a STOP, whose fill convention is
adverse). Accept the bound — but the correct evidence label is **TRANSFERRED**, not MEASURED, for that
part of the pool, and Phase 0's own §10 already lists it as "not falsified, and left open."

---

## 4. Adjudication C — the funnel's five-month verdict

**Two different claims are bundled under one verdict, and they have wildly different power.**

### 4.1 The POOL-level kill is sound — do not soften it

623,000 candidate occurrences, 176,000 resolved-filled. Against a per-row driftless benchmark computed
from the actual modelled fill price on the actual executable side, every family runs **z = −5.6 …
−25.0**. Stratified by spread quintile the anti-signal appears in **all 35 quintiles including the
cheapest**. Adversarial pass: excluding each family's worst symbol moves nothing; 7 of 70 half-month
cells positive; direction mapping independently confirmed at corr +0.562 / 78.3 % sign agreement over
120 symbol-months. **This kill is heavily powered and well-controlled. The funnel program's closure
rests on it and survives this audit.**

### 4.2 The SELECTED-BOOK verdict is underpowered in both directions

Per-trade `actual_net_r` read straight out of the three sealed validation JSONs:

| window | n | total R | mean | t | 95 % CI on total | zero inside? |
|---|---:|---:|---:|---:|---|:--:|
| **February (sealed PASS)** | 105 | **+14.168** | +0.1349 | **+1.234** | [−8.34, +36.68] | **yes** |
| April | 49 | −7.742 | −0.1580 | −1.201 | [−20.38, +4.89] | **yes** |
| May | 17 | +5.130 | +0.3018 | +1.122 | [−3.83, +14.09] | **yes** |
| June | 45 | +3.964 | +0.0881 | +0.466 | [−12.69, +20.62] | **yes** |
| July | 66 | −14.566 | −0.2207 | −1.497 | [−33.64, +4.51] | **yes** |
| Apr+May (sealed REJECT) | 66 | −2.612 | −0.0396 | −0.326 | [−18.30, +13.07] | **yes** |
| Jun+Jul (sealed REJECT) | 111 | −10.602 | −0.0955 | −0.818 | [−36.00, +14.80] | **yes** |
| **POOLED, all five months** | **282** | **+0.954** | +0.0034 | **+0.050** | [−36.46, +38.37] | **yes** |
| Pooled excluding February | 177 | −13.214 | −0.0747 | −0.869 | [−43.00, +16.57] | **yes** |

*(20,000-resample bootstrap intervals agree with the normal intervals to within 0.5 R throughout.)*

**Power.** sd = 1.137 R/trade. At 80 % power, α = 0.05 two-sided:

| effect to detect | trades required | months at the observed rate (~56/mo) |
|---|---:|---:|
| +0.10 R/trade | 1,015 | **~18** |
| +0.15 R/trade | 452 | ~8 |
| +0.20 R/trade | 254 | ~4.5 |

The program read **282 trades in five months**. It could never have detected the effect it was looking
for. And the reverse question — the one nobody asked — has the same answer: **the negative verdict is
not distinguishable from noise either.**

### 4.3 The estate measured this and set it aside

`THREE_MONTH_POSTMORTEM_V1.md` §5.4, verbatim:

> **BAR-2 is the honest-statistics bar: it would not have passed even February** — a single ~20-day
> month at this trade rate rarely clears a 95 % day-resample bar, which is precisely the sample-size
> statement of §2.3.

BAR-2 (20,000 day-resamples, seed 20260811) is the only bar in the program carrying an interval. It was
computed, it rejected the PASS month, and it was **reported-not-used** at every subsequent read
(Jun/Jul: *"BAR-2 REJECT (reported, not used; bootstrap p05 −35.76)"*). **BAR-3 — a point-estimate bar
with no error term — was ratified instead**, and it is the bar that passes February and rejects
April+May by 1.7 R of tolerance.

The postmortem itself is even-handed: February *"is consistent with a thin per-window edge — and also
with selection luck; the score's own magnitude cannot tell them apart."* The later documents convert
that into a one-sided claim — *"reliable loss"*, *"February was the outlier, not the norm"* (B3418),
*"the pool is uniformly negative"*. **Only the last of those three is supported.**

### 4.4 What was thrown out with it

**Relative skill is the one quantity positive in every read** — discipline minus naive-mixed:
**+18.9 R** (Feb), **+6.6 R** (Apr+May), **+28.96 R** (Jun+Jul). It is a **paired** comparison over the
same windows, which is a far better-powered design than the absolute at this sample size. Every read
names it as *"what survives"*, and **no phase has ever made it the object of a prereg.** It is the
program's most durable measured asset and it has never been tested for significance in either direction.

### 4.5 Adjudication

> **The pool kill: SOUND. The selected-book verdict: UNDERPOWERED, and published one-directionally.**
> The correct statement is *"no detectable edge either way at n = 282; MDE at 80 % power is ~1,015
> trades."* The program still closes — on §4.1, not on §4.2.

---

## 5. The kill ledger

Ranked within each class by the economic value of what was killed. `S` = sound, `U` = unsound as
stated, `P` = underpowered, `T` = transferred/bounded rather than measured, `A` = artifact of
infrastructure rather than evidence.

### 5.1 Kills I judge UNSOUND, UNDERPOWERED, or ASYMMETRIC — ranked by value killed

| # | what was killed | economics at the kill | killed by | judgment | revival cost |
|---|---|---|---|:--:|---|
| **1** | **The funnel selected-book five-month record** (Feb PASS → Apr/May REJECT → Jun/Jul REJECT); with it, the LSR-scoped live arming and V2 Phases 1–4 | 282 trades, pooled **+0.954 R**, t +0.050; every month's CI straddles zero | a **point-estimate gate (BAR-3)** ratified *after* the interval-bearing bar (BAR-2) was measured to reject even the PASS month | **P** | **Free.** Re-state with intervals. The program still closes on the pool finding; what is recoverable is the relative-skill asset (§4.4) |
| **2** | **`cq_current_breaker_…_5d_stop_0p25d`** (CS) | 3 positive OOS folds, pooled **+7.519 R/trade**, 75.2 % drop-best retention, lifetime +12.592 on 6,536 trades; **only** significance failed | **BH q = 0.1534** on a **Monte-Carlo** p, where the **exact null was cheaper, was computed, and admits (q 0.0576 / 0.0864)**, against a family with 4 literal duplicates that grew 32 → 59 in two days | **U** *(outcome correct — §2.6, §2.5)* | Do **not** revive. Re-kill under the exact null + driftless check (~1 session, free) |
| **3** | **`sub_xvol_pullback @ target_4R`** — on an **ARMED** sleeve (AK B968 → AS B1526/B1527 → AU B1553) | AK published **+1.157 R/day**; the true delta is **+0.130** at AK's own standard and **+0.3435** at the ratified rule — the level was read as the delta, **8.9× overstated**, and cited three times before correction. Verdict: q 0.384 at m 48, 3.8× above the bar | statistical gate — **after** two premise errors (wrong magnitude, wrong population standard: no `spread_band`, no era key = ALL_ERAS flat 37-day snapshot) | **U→S** | Already correctly re-killed. **But** AU found the sleeve's *train* window is −0.190 / −0.278 R against a *test* window of +1.02 / +1.37 — a **sign inversion on armed money**, filed as "do not propose" rather than escalated |
| **4** | **`energy_agri`'s live `partial_be_runner` scale-out** — **ARMED** (AD B757, AU) | live contract **−0.308 R/day** vs the plain exit (n 67); AU corroborated a **+0.2302 R/day** restamp error at every band through a second instrument | measurement, thin sample | **S**, but **under-escalated** | n/a — this is a *finding on armed money* filed as "a question, not a recommendation" |
| **5** | **`cp_true_utc_ny_metals_long_v1`** (CR) — NOT_EVALUABLE | **no economics were ever read at the gate.** Fidelity **PASSED** at recall 1.000 (249/249) | a **missing data artifact** — a training-lane projection was discarding fill UTC/price, exit UTC, gross R, terminal reason, source path/sha on all 121 filled rows | **A** | CR-CAPTURE-1..4: expensive but bounded. The forward projection is **already repaired** (`cuts.py:894-956`) |
| **6** | **AO's `sub_xvol_pullback + mx_btcusd` pair admission** (B1320–B1322) | n 44, **+1.7864 R/day**, p 0.0042, **q 0.0819** — inside the bar | **permutation resolution floor**: 8 blocks → 2⁸ achievable assignments → `p_floor` 0.004006 vs observed 0.004200, headroom **1.048×**; verdict flips on **4 of 20 seeds** | **S** — the best-executed kill in the program | n/a. **But its own generalisation (a 2× headroom guard) was never implemented** — `gate.py:1151-1152` still refuses only when `p_floor ≥ α`. That omission is why §2.3 was never caught |
| **7** | **The LIMIT third of the funnel pool** (Phase 0 §6) — `current_fvg_fill` 305 k candidates, `current_ob_retest`, `current_breaker_re_entry` | bounded at −0.0488 / −0.0519 / −0.0747 | a **transferred** bias model fitted on seven MARKET families, plus a demonstrated machinery degeneracy (97.7 % censor) | **T** | One focused session on `quote_side.py` (STOP order type). Phase 0 argues the bound is conservative; it is right that it is a bound, not a measurement |

### 5.2 Kills I judge SOUND — do not reopen

| what was killed | economics at the kill | killed by | why it holds |
|---|---|---|---|
| **The inversion thesis** (Phase 0) | claimed +0.0927 / +0.0864 / +0.0718 R/trade, 5/5 months → measured **−0.056 / −0.053 / −0.066**, **0/5 months**, 34/35 family-months negative | pre-registered gate + exact re-walk | §3. Both corrections verified independently; control exact; denominator favourable to the thing killed |
| **The funnel pool is anti-predictive** | 10 families, all negative every month; 366 conditioned cells → **1** survivor vs ~11 by coin flip | measurement at z = −5.6…−25.0, 176 k trades | §4.1 |
| **Breadth as the estate's cure** (AF B807–B809) | 246 members × 30 families × 134,027 trades → **0 admit**; 23/30 are mixtures | measurement + a *pre-declared* two-clause test that 2/30 pass | Monotone across 6 nested sets; the block records its own first draft being corrected adversarially |
| **Member conditioning** (AH B1013–B1015) | helps in **11 of 22** — a coin flip; trade-weighted **−0.004525 R/trade** over 16,248 vs 24,603 | held-out measurement, rule fixed first | Both weightings published; all residual biases run *toward* flattering selection |
| **The `vr` tilt as an arming candidate** (AR, AZ B1853–B1854) | book headline +1.119 pp shown to be **85 % equity-path artifact** | the session's **own control** | The author refuted his own headline; the ordering survives as a *sizing* signal (ρ 0.4073, perm p 0.00025) |
| **The B7.5 separability mine** (AW B1760–B1766) | **0 of 212** pre-declared cells separate; ceiling 16.9 % vs 33.3 % break-even | pre-declaration + measurement | TRAIN baseline reproduces to six decimals |
| **The broad family on virgin February** (CP B2852–B2854) | gross −0.1506 R/row, net −0.6400, **20/20 days negative**, precision 0.309 vs 0.606 break-even | a **pre-committed** five-way reject conjunction, frozen at `5878f4289` *before* the arm | Textbook. Protocol committed before the outcome existed |
| **`fx_jpy` disarmed** (AV B1629–B1631) | negative at **every** cost band; all five declared cuts REJECT or NOT_EVALUABLE | measurement | Acted on armed money, promptly |
| **The OD-ALL-IN armed-set extension** (CL B2657–B2663) | direct-addition set measured **EMPTY on both accounts**; both JPY sleeves −0.1121 ΔP2 | measurement at firm-true rules | Refused to launder a sensitivity win (`metals_softband` +0.0449 recorded DO_NOT_ARM) |
| **February run 1** (B3410) | never scored | the rule's own runtime clause — flat `cost_r=0.12`, `None` components | The cleanest kill in the file: executed **to protect a virgin window** |

### 5.3 Kills whose PREMISE was never independently checked — the list the commission asked for

Every one of these was later found false, or is found false here. The pattern is that **the correction
almost always runs in favour of the thing that was killed.**

| kill | the premise | how it failed | direction of the correction |
|---|---|---|---|
| **H2** — the test-suite story | "the 10 failures are an LFS/sparse-checkout artifact" then "`selector_v4.py:4004-4016` never consults `entry_quality_fill_probability`" | single-cause LFS story refuted by its own reviewer (B39); the `:4004-4016` story wrong — `:3995-4001` **does** consult it, the real gate is `_complete_execution_fillability_atom` `:453-537`. **The defect was in the fixtures** | acting on it would have touched a **contract-bound** file for nothing (re-seal + ~16.5 h/window) |
| **H3** — the memory story | "15.3 GB is a GiB/GB echo of 8.61 GB"; "the source layer's 5× materialisation is the cause"; "≤3 GB/arm" | 15.32/8.61 = **1.779**, two fields not one (B81/B83). Killing every source-layer copy moved the arm **+3.5 %** (B84). Real owner is the **evidence machinery at 60.6 %** | the ≤3 GB gate was **withdrawn**; the struck claim survived in `AGENTS.md` for weeks (B148) |
| **AK's frontier magnitude** | "+1.157 R/day" is the improvement | it is the **level**; delta +0.130 — **8.9× overstated**; and measured at a standard that does not govern (ALL_ERAS, flat snapshot, no band) | at the **ratified** rule the delta is **+0.3435 — 2.6× larger** (B1526) |
| **AQ's `asian_fade` 0.88 R/day** | the largest single labelling error in the estate | **100 % construction artifact** (B1561): `AD.Variant(family="time_stop", target_mode="native")` defaults the trail/partial fields to `None`, deleting a `trailing_runner` sleeve's own exit policy. True error **+0.0000** | the estate no longer has a "largest labelling error"; but **`energy_agri` is ARMED and its true restamp error is +0.2302 R/day** |
| **AR's book-return instrument** | compounded book return measures a sizing change | **85 % equity-path artifact**, by the author's own control | now a binding standard |
| **B10 → B11** | "sparse-masking REFUTED by experiment" | *"I compared counts, not sets, and the conclusion was wrong"* | kill of a kill |
| **B1075 → B1093** — the most economically consequential | "AD's tier restatement is worth **negative**" (P2 0.9172 → 0.7548, book-days 117 → 310) | **WITHDRAWN.** `recost_w7_validation.row_cost:873` charges `swap × min(nights, SLEEVE_MAX_NIGHTS)` and **never consults `CARRY_STRUCTURAL`** | corrected answer is **+36 %/month and 12 days sooner** for 2.6 pp of `p_pass` |
| **B1160 → B1171** | "the DSR leaves the verdict unchanged" | **struck — the DSR was never computed.** `gate.py:844-845` writes it to telemetry and no gate key consumes it, so "unchanged" was true *by construction* | repaired DSR 1.0000 → 0.9731, `significant: true` at every level |
| **B1090** | a receipt's closing line "no threshold was loosened" | **was false** | α 0.20 is `C_exploratory`, whose own sealed note reads *"RESEARCH TRIAGE ONLY… Do not let a C-pass reach a book"* |
| **B1450** | "the hour-01 convention cannot be measured before 2024 from any data on this machine" | **refuted** — `data/` holds H1 for 12 of 14 cohort symbols, four predating the M15 archive | *"an absence I never searched for"* |
| **B700** | a sealed sentence: "not a defect that can be fixed here — it is the only tick measurement that exists" | **struck** — the MT5 bar `spread` column is populated back to 2000/2010 across 50 symbols | |
| **RR-1.5** *(this audit)* | `FUNNEL_ROOT_CAUSE` §1/§3: "the live value is the config sanity floor, 1.5 R" | true RR is **2.0** on 81,968/81,968 rows | killed the funnel's one constructive finding |
| **the feature/label geometry mismatch** *(this audit — still unchecked by anyone)* | that the ridge's features describe the contract the labeler runs | **they do not**: features at RR **1.5** on 632,934/632,934 rows, labeler at **2.0** | open defect |

---

## 6. The structural pattern

Five things, each measured above, that together explain the owner's complaint.

1. **The burden of proof is asymmetric.** A finding must clear nine gates plus a multiplicity bill. A
   kill must clear one number, and no kill in this program except Phase 0 has ever been
   pre-registered, controlled, and sensitivity-banded the way findings are required to be.

2. **The multiplicity bill is a function of the calendar, not of evidence.**
   `freeze_rule.look_taken_ACQUISITION_raises_the_bill_and_that_is_deliberate` plus monotonicity means
   identical evidence admits in July and rejects in August. `CANDIDATE_BOOK_V1` went **32 → 59 in two
   days**; the CS candidate admits at any m ≤ 38. The estate's own stamp on the denominator is *"FLOOR,
   not a measurement. No trial-budget ledger artifact exists anywhere in the repo."* Wave 8 already
   found this family double-counting once and called the resulting q-values **over-corrected**.

3. **No error bar is ever attached to a kill.** Zero power calculations, zero MDE statements, zero
   confidence intervals anywhere in phases 19–21. The single bar that carried an interval (BAR-2) was
   computed, found to reject even the PASS month, and replaced with a point-estimate bar.

4. **The benchmark is applied in one direction only.** The driftless first-passage benchmark is
   well-built and was used to kill a positive thesis at z = −5.6…−25.0. It has never been pointed at a
   candidate that came in *above* it — including one at **14.3× driftless** that reached the declared
   candidate family.

5. **The estimator is noisier than it needs to be, and the guard that would catch it was designed and
   not built.** `perm_null.py:196-202` always Monte-Carlos, with no exact-enumeration branch;
   `gate.py:1151-1152` relates a p only to α, never to its own resolution; AO's B1322 headroom guard
   was proposed and never implemented.

**And the tell:** when a kill in this program is re-examined, the correction usually runs *in favour of
the thing that was killed* — B1093 (+36 %/month), B1526 (2.6× larger), B1377 (a ×5.3 improvement
mis-stated as a level), B1450 (the data existed). That is the signature of a system tuned to
false-negative rather than false-positive error, which is the correct tuning for *arming* and the wrong
tuning for *learning*.

---

## 7. What to do, cheapest first

| # | action | cost | what it unblocks |
|---|---|---|---|
| 1 | **Re-state the funnel selected-book verdict with intervals.** Replace "reliable loss" / "February was the outlier" with "no detectable edge either way at n = 282; MDE at 80 % power ≈ 1,015 trades". Keep the pool kill exactly as it stands | free | stops a false lesson propagating into V2's design |
| 2 | **Make the exact permutation null mandatory when the achievable assignment space is small** (≤ ~10⁵ — it is *cheaper* there), and implement AO's B1322 headroom guard | ~1 hour + tests | every past and future significance verdict within MC noise of its bar |
| 3 | **Re-issue the CS verdict under the exact null**, so the record says what actually decided it | ~1 hour | the record; and it stops the "change the family accounting" revival path being taken blind |
| 4 | **Point the driftless first-passage benchmark at every ADMIT and near-ADMIT**, not only at kills. Start with the CS breaker (14.3×) and `mx_btcusd @ target_5R` — the one live admission | ~1 session | catches artifacts *before* the multiplicity argument, which is the cheap end |
| 5 | **Reconcile Phase 0 §6 vs CS**: the committed labeler censors 97.7 % of inverted `current_breaker_re_entry` rows; the CK sidecar censored 0 of 3,671. One is wrong about this family | ~1 session | decides whether the six-symbol slippage capture is worth buying |
| 6 | **File the feature/label geometry mismatch** (features RR 1.5, labeler RR 2.0) as a defect of record | ~1 session | correctness of the funnel V1 stack whether or not it reopens |
| 7 | **De-monotonize or split the family bill** — bill a candidate against the hypotheses that could have produced *its* result, not against every sleeve the live config can build | owner decision | removes the calendar dependence from the evidence standard |
| 8 | **Give relative skill its own prereg** (+18.9 / +6.6 / +28.96, 3 of 3 reads, paired design) | ~1 session | the program's most durable measured asset, currently discarded as a by-product |

---

## Receipts

`swarm/laneA_receipts/LANE_A_RECEIPTS.json` — every number in §2–§4 that I measured myself:

| key | what |
|---|---|
| `R1_rr_independent_verification` | RR recomputed from **raw sealed compact rows** across all three candidate roots — not from Phase 0's receipt |
| `R2_feature_label_geometry_mismatch` | `target_distance_atr / stop_distance_atr` over the ridge's own training features |
| `R3_spread_double_count_check` | component identity, deductible definition, spread path, rescale, and eligibility-gate direction |
| `R4_five_month_power` | per-trade CIs, bootstrap CIs, t-statistics and MDE for every window and the pooled record |
| `R5_cs_breaker_driftless_plausibility` | the 5D/0.25D geometry against driftless first passage; family microstructure |
| `R6_cs_kill_forensics` | BH arithmetic, p provenance, the seed-stability concern I refuted, the exact-vs-MC null, the family composition audit, and the kill that holds |

*Read-only audit. No live path, config, VPS, broker module, or sealed campaign byte was touched.*
