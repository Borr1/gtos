# Attrition recovery — the four findings the estate paid for and abandoned

**Commission:** orchestrator, 2026-08-12, owner-approved the same day (*"proceed as proposed and
recommended in everything"*). Lane D's census found that ~50 of ~190 positive findings (26 %) died
of pure attrition — nothing refuted them, nobody continued them — and named the top of that list.
This lane went and got them.

**Scope discipline.** Measurement only. No live path, no config, no arming, no VPS, nothing on a
broker. Every number below is recomputed from sealed inputs on this machine. **No verdict here is
an admission**: the padded-BH repair (`gate.py:1104-1109`) belongs to a separate lane, and where
the arithmetic of admission appears it is reported as arithmetic, never as a promotion.

**Receipts:** `attrition_receipts/` — eight JSON artifacts and the seven scripts that wrote them.
Every script reads sealed caches and writes only to `/private/tmp`.

---

## 0. The answer, in four lines

| # | target | verdict | what changed |
|---|---|---|---|
| **1** | FB `current_ob_retest` 1.5D / 0.25D — +1.6467 net R/trade, n 1,340 | **EVAPORATED** | Reproduced **exactly** from raw inputs, then killed by its own controls. **474 of 1,340 rows (35.4 %) book a target hit at the FIRST observation** — the resting limit was never touched. Require the limit to fill and **+2.8624 gross becomes −0.0336**; net **+1.6467 → −1.2493**, day-block CI95 [−1.510, −0.995]. |
| **2** | AH `volume_surge_reversal × index × D1 @ VOL_REGIME==hi` — +0.2248 R/day, p 0.0127, 5/5 folds | **STILL UNRESOLVED, and smaller than advertised** | Reproduced exactly. **It survives the instrument**: the quote-side correction is −0.0086 R and migration exposure is **zero**, so +0.2266 gross restates at **+0.2048 R/trade** after broker-true spread and slippage. What does not survive is the **regime gate**: the cell was the argmax of a 9-cell enumeration, and under 20,000 label permutations **P(any cell shows 5/5 positive folds) = 0.801**. The conditioning effect is +0.158 ± 0.126 (t 1.25, p 0.21 raw, 1.00 after its own bill). |
| **3** | the three pooling merges — "at m ≤ 16 the two best sleeves ADMIT; the estate bills 59" | **EVAPORATED (arithmetic)** | Executed. The merges take the family **59 → 46**, not 59 → 16. They close **13 of the 43** members that separate the estate from its own admission bar and are **30 short**. Nothing admits at any step. The one candidate the merges could reach is the CQ inverted breaker — the candidate with the strongest independent evidence of being an artifact. |
| **4** | the funnel's abstain discipline — +18.9 / +6.6 / +28.9583 R, "never negative" | **EVAPORATED** | The three figures are **not on one basis** (two actual, one worst-case). On a common actual basis they are **+18.911 / +6.600 / +2.743** — an 85 % decay, none significant paired by day (p 0.170 / 0.231 / 0.669). On the worst-case basis **49–91 % of each margin is a differential censoring charge**. And the rule carries no information: a **count-matched random abstention does as well or better, p = 0.593**. |

**Two of the four are completed kills, one is a completed arithmetic kill, and one shrank into an
honest, small, instrument-clean number.** The estate's largest un-pursued positive is worth
**+0.205 R/trade on 203 trades with a day-block interval that includes zero**, not a program.

**The instrument finding that generalises.** Target 1 exposes a defect that is **not** Lane D's
quote-side walker and has no entry in any register: **the barrier clock starts at the decision
instant, not at the fill instant, on a family whose orders are resting limits.** Every published
number for a LIMIT family walked this way is measuring excursion from a price the book never
paid. That is `current_ob_retest`, `current_fvg_fill` and `current_breaker_re_entry` — three of
the ten funnel families and **550,966 of 632,934 pool rows.**

---

## 1. Method — the instrument comes first

Constraint A of the commission: *verify the instrument before you believe any number.* Lane D
established that the estate's walkers resolved barriers against a BID archive without crossing the
spread (published gross +2,520.7 R → −619.8 R over 22,354 trades); Lane G established that the
wave-21 funnel caches are on the **repaired** side. So the question is per-artifact, and it was
asked per-artifact.

| target | artifact walked | per-row identity | population identity | side of the repair |
|---|---|---|---|---|
| 1 FB | `CJ_RECLOCKED_S0R0_POOL_V1` + `CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1` | reproduced the published cell to the last digit from raw inputs (§2.1) | mean `spread_r` 0.2281 in original-R = **0.9126 R at the 0.25D stop** | **pre-repair, and it is the smaller of its two defects** |
| 2 AH | `AF_FAMILY_TRADES.json.gz` | `r_gross ∈ {−1.0, +2.0}` **exactly on 610 of 610 rows** — a pure barrier walker, no quote crossing anywhere in gross | broker-true mid spread ÷ stop distance = **0.008569 mean** | **pre-repair, and the repair is worth −0.0086 R here** |
| 3 merges | none — arithmetic on declared families | n/a | n/a | n/a |
| 4 funnel | Lane G's `pool_table.npz` over the five sealed months | Lane G's `gross = −1 − drift − spread_r`, exact on 98.3–98.7 % | reproduced independently: MARKET `E[net] −0.27254`, `E[cost_r] 0.28098`, **`E[net+cost] +0.00844 ± 0.00422`** | **post-repair** (Lane G, confirmed here) |

**Two of the four sit on the pre-repair side and it does not matter for either**, for opposite
reasons: on target 2 the correction is 0.86 % of the number, and on target 1 the correction is real
(gross 2.8624 → 2.0404) but is dwarfed by a defect nobody had named.

---

## 2. TARGET 1 — FB's `current_ob_retest` at 1.5D / 0.25D. **EVAPORATED.**

**The claim** (Lane D rank 5, ledger row H9): TRAIN n=799 +1.630823 net R/trade; HOLDOUT n=541
+1.670197; FULL n=1,340 +2.862377 gross / +1.646719 net; family-wise max-T p = 0.001; TRAIN-selected
and HOLDOUT-persistent in both directions; the declared bill already sunk at gate node O1.

### 2.1 The control: exact reproduction

`attrition_receipts/fb_rewalk.py` re-walks the cell from the January pool and the ordered-path
sidecar, with the tick override for the four tick-capable symbols, under `GRID_PROTOCOL`'s rules
(D = |entry − stop_loss|, 120-minute horizon, conservative same-M1-bar stop, `gross = target_d/stop_d
| −1 | terminal/stop_d`, `net = gross − cost_r/stop_d`).

| | published | reproduced |
|---|---:|---:|
| FULL gross | 2.862376572451229 | **2.862377** |
| FULL net | 1.6467194254150541 | **1.646719** |
| TARGET / STOP / HORIZON | 707 / 549 / 84 | **707 / 549 / 84** |

Nothing below is a disagreement about the walk.

### 2.2 The kill: 35 % of the "trades" never existed

`current_ob_retest` is a **limit** family — 1,243 of 1,340 rows carry `effective_order_type: limit`
and 1,268 carry `fill_realism_class: passive_queue_confirmed`. The walker anchors the barriers on
`entry_price` (the resting limit level) and **starts the clock at the decision instant**. For a
retest setup the limit sits behind the market by construction, so the favourable barrier is
frequently already behind price before a single bar elapses.

Measured on the 1,340 rows:

* **signed displacement at the decision instant: mean +1.105 D favourable, median +1.043 D**;
  **83.0 % of rows start already favourable**;
* **474 rows (35.4 %) register the 1.5D target as hit at the FIRST observation**;
* 179 rows are already past the 0.25D stop at the first observation.

A 6:1 reward-to-risk contract booking a **52.8 % target rate** (707/1,340) against a driftless
expectation of 0.25/1.75 = **14.3 %** is a 3.7× lift. This is where it comes from.

### 2.3 The four arms

| arm | gross | net | day-block CI95 on net | p(≤0) | TARGET/STOP/HORIZON |
|---|---:|---:|---|---:|---|
| **CONTROL** (published) | **+2.862377** | **+1.646719** | [+1.3050, +1.9388] | 0.0000 | 707 / 549 / 84 |
| **MIRROR** (direction flipped, same paths) | −0.549915 | −1.765572 | [−2.0065, −1.5264] | 1.0000 | 82 / 1,243 / 14 |
| **SPREAD_CORRECTED** (one crossed spread, per side) | +2.040407 | +0.824750 | [+0.4617, +1.1706] | 0.0000 | 564 / 722 / 54 |
| **FILL_GATED** (barrier clock starts when the limit is touched) | **−0.033644** | **−1.249302** | [−1.5103, −0.9946] | 1.0000 | 90 / 915 / 210 |
| FILL_GATED + MIRROR | −0.863610 | −2.079267 | [−2.2490, −1.9145] | 1.0000 | 16 / 1,267 / 16 |
| FILL_GATED + SPREAD_CORRECTED | −0.484042 | −1.699699 | [−1.9248, −1.4492] | 1.0000 | 40 / 1,061 / 114 |

**Requiring the order to fill removes 100 % of the gross and more.** 125 of the 1,340 limits are
never touched inside the 120-minute horizon at all. Restricting to the 1,243 rows the pool itself
labels `limit` reproduces every line to within 0.02 R (`FB_REWALK_LIMITONLY.json`), so this is not
a mixed-order-type artefact.

The **spread** correction is real and secondary: it costs 0.822 R of gross (2.862 → 2.040), which
is 4× the family's 0.2281 mean `spread_r` because the 0.25D stop divides the R unit by four. It
was never the main defect.

### 2.4 What the population actually is

Every one of the 1,340 rows carries `missed_opportunity_r_scoreability_status:
diagnostic_opportunity_r_scoreable`. 1,214 of 1,340 carry `selector_action: reject`; 835 were
blocked by `cost_authority`. **This is a diagnostic missed-opportunity pool, and FB's grid read it
as an executable book.** That is the category error underneath the number, and it is the same shape
as FA's independent finding that the 0.25D breaker *"bought ZERO trades because 100 % refuse at the
pre-trade cost gate."* Both sessions were looking at the same wall from opposite sides.

### 2.5 Two corrections to the record

* **"FG ranks it #1 next action"** (`LANE_D_POSITIVE_FINDINGS_LEDGER_V1.md:516` and `:676`) is a
  mis-citation. `phase19/SESSION_FG_SOL_REPAIR_INTEGRATION_RESULT.md` lists *"OB-retest
  1.5D/0.25D"* at **priority 5 of 8**; priority 1 is the FD semantic/authority repairs. Lane D's own
  ranked table also places it 5th, so the sentence contradicts its own table.
* The A2 verification that certified this cell (*"5/5 claims VERIFIED, all exact, 0.0 deviation, no
  refutations"*) is **correct and irrelevant**: it verified that FB computed its own walk correctly.
  It never asked whether the walk describes a trade. Exactness is not validity.

**Verdict: EVAPORATED — instrument artifact, mechanism identified and priced, no follow-up work
warranted.** Remove from the queue. `src/research_infra/current_ob_retest_geometry_candidate.py`
should stay default-off, and its docstring should carry the fill-anchoring caveat.

---

## 3. TARGET 2 — AH's `volume_surge_reversal × index × D1 @ VOL_REGIME==hi`. **STILL UNRESOLVED.**

**The claim** (Lane D rank 3, *"the largest un-pursued positive in the corpus"*): +0.2248 R/day,
raw p 0.0127, 5 of 5 out-of-sample folds positive, n 203; routed to the owner and to the next
session as *"the strongest new candidate this wave produced."*

### 3.1 The control: exact reproduction

`attrition_receipts/ah_repro.py` rebuilds the regime spine from the bars archive with AF's own
`label_regimes`/`bucket` and re-derives the cell:

| | published | reproduced |
|---|---:|---:|
| n | 203 | **203** |
| `mean_r_gross` | 0.2266 | **0.22660** |
| chronological quintile means | [0.09756, 0.46341, 0.17073, 0.09756, 0.30769] | **identical** |

### 3.2 The instrument: this one is clean, and that is the recovered part

`r_gross` takes exactly two values across the whole 610-trade family — **+2.0 on 228 rows and −1.0
on 382 rows** — so the walker charges no quote crossing at all inside gross. The correction is
therefore a level shift plus any barrier migration, and both are small **because a D1 index stop is
100–170× the spread**:

| term | value |
|---|---:|
| published gross | +0.226601 |
| broker-true mid `spread_r` (FTMO, ny session, `BROKER_TRUE_COSTS_V1_1`) | mean 0.008569, median 0.006120, max 0.023512 |
| quote-frame level correction | **+0.218032** (Δ −0.008569) |
| SHORT target rows exposed to migration (MFE cleared 2.0R by < one spread) | **0 of 69 SHORT rows** (3 LONG rows, structurally immune) |
| worst-case migration bound | +0.218032 (unchanged — nothing to migrate) |
| less broker-true slippage 0.0132 R; commission on index = 0.0 (MEASURED) | **+0.204832 R/trade** |

**Lane D's bent ruler does not reach this family**, and the restated +0.2048 R/trade cross-checks
AH's own cost-charged gate figure of +0.2248 to within 0.02 R. *This is a real, instrument-clean
number.*

### 3.3 What does not survive: the regime gate is not doing the work

| statistic | value |
|---|---|
| pooled family (ungated, n 610) | **+0.121311 R/trade** gross |
| `VOL_REGIME==hi` (n 203) | +0.226601 |
| everything else (n 407) | +0.068796 |
| **conditioning effect** (hi − rest) | **+0.157805 ± 0.125907, t +1.25, p 0.210**; × the 9-cell enumeration → **1.000** |
| cell vs zero, trade-level | t +2.18, p 0.029, CI95 [+0.023, +0.430] |
| cell vs zero, **day-block bootstrap** (100 decision days, 20,000 draws) | CI95 **[−0.029, +0.485]**, p(≤0) 0.043 — **the interval contains zero** |

And the selection is the decisive term. `ah_conditioning.py:693-695` picks the cell with
`max(key=(fold_positive_frac, mean_r_gross))` over the nine enumerated cells — **the 5/5 fold
statistic is the selection criterion, then reported as the finding's strength.** Under 20,000
permutations of the regime-label vector (cell sizes preserved, r_gross series fixed):

* **P(any of the nine enumerated cells shows 5/5 positive chronological folds) = 0.801**
* P(the best cell's mean ≥ the observed +0.22660) = 0.710

Seeing a 5/5 cell in this enumeration is the *expected* outcome. AH knew part of this and published
it: `bonferroni_within_enumeration = 0.1143`, and its own verdict on the cell was **REJECT**.

### 3.4 A correction to Lane D's attrition claim

*"The string `VOL_REGIME == hi` appears in no document of any later phase"* is **false as worded**
and true in substance. The spaced form appears nowhere after phase 8; the canonical unspaced form
`VOL_REGIME==hi` appears **85+ times in `phase10/receipts/REGIME_CONDITIONING_V1.json`** and 3 times
in `SESSION_AO_REGIME_AND_POOLING_RESULT.md`. AO re-used the *gate* on three unrelated sleeves
(`asia_pdl_fade`, `sub_mid_dn_revert`, `sub_xvol_pullback`) and admitted none. **The cell was never
re-tested** — that part stands, and it is the weaker claim that should be quoted onward.

### 3.5 What it is worth, honestly

The recovered finding is not the regime cell. It is the **family**: `volume_surge_reversal × index
× D1`, n 610, **+0.1213 R/trade gross → ≈ +0.0995 net of broker-true spread and slippage**, which
reproduces AH's own ungated +0.0999 at p 0.1204. Six carriers, one mechanism, one of only two of
AF's thirty families to pass the two-clause coherence test.

**Verdict: STILL UNRESOLVED — needs the family measured as ONE member with six carriers on a
population that was not used to pick the cell.** That is exactly merge 2 of target 3, which is why
these two items are the same item. It is *not* worth an owner decision at +0.205 R/trade on a
day-block interval that includes zero.

---

## 4. TARGET 3 — the three pooling merges. **EVAPORATED (arithmetic).**

**The claim** (Lane D rank 4): *"At m ≤ 16 the two best sleeves ADMIT; the estate bills 59. The
three merges are already written and need NO code and NO data."*

Executed in `attrition_receipts/merge_arith.py` against `CANDIDATE_FAMILY_V27` (59 declared, 57
looks) and the 28 real p-values of `AI_GATE_AT_DECLARED_FAMILY_V1@CANDIDATE_BOOK_V1@all_declared`
(the same 32-sleeve submission `SLEEVE_FORENSIC_REPORT.md` §7.1 quotes; ALL_ERAS, flat 37-day
snapshot — its own population caveat carries).

| step | m | BH rank-1 bar α 0.10 | admits |
|---|---:|---:|---|
| declared V27 | 59 | 0.001695 | **0** |
| − 3 exact duplicate series (Lane B: same trade series, `n_exact` 10/10) | 56 | 0.001786 | 0 |
| − 2 rows that produced no look | 54 | 0.001852 | 0 |
| **merge 1** — `mx_btcusd` + `mx_ethusd` + `vol_compression` → 1 | 52 | 0.001923 | 0 |
| **merge 2** — 6 index volume-surge → 1 | 47 | 0.002128 | 0 |
| **merge 3** — killzone → 1 | **46** | 0.002174 | **0** |
| *(reference)* Lane B's full collapse to 25 base mechanisms | 25 | 0.004000 | 0 |

Largest declared family at which each candidate admits, α 0.10:

| candidate | p_raw | submitted with its siblings | submitted alone (the padded gate) |
|---|---:|---:|---:|
| `sub_xvol_pullback` (**ARMED**) | 0.006099 | m ≤ **16** | m ≤ 16 |
| `mx_btcusd_d1_donchian_20_breakout` | 0.011999 | m ≤ **16** | m ≤ 8 |
| `cq_current_breaker_re_entry_inverted_5d_stop_0p25d` | 0.002600 | — (submitted alone) | m ≤ **38** |

**The three merges take the family from 59 to 46. The bar that matters is 16. They close 13 of the
43 members in the way and finish 30 short.** No step of the chain admits anything, and neither does
the maximal collapse to 25 mechanisms.

Two things follow, and both are worth more than the merges were.

1. **The one candidate the merge arithmetic can reach is the CQ inverted breaker** (needs m ≤ 38;
   reached only by the full 25-mechanism collapse). It is also the candidate the discovery lane
   measures as **103.4 % artifact** — 81.33 % of its trades come from candidates whose stop was
   already broken, and on the 596 genuinely takeable trades it books −2.644 R/trade — and which FA
   proved is **inexpressible in the engine**. A merge programme whose only beneficiary is that
   candidate is not a repair.
2. **The estate's admission problem is not the bill's redundancy, it is the bill's size.** Merging
   duplicate hypotheses is correct bookkeeping and it is worth 13 members. Reaching 16 from 59 by
   merging would require collapsing the estate to a quarter of its declared mechanisms, which
   `candidate_family.py`'s own docstring forbids: *"under a shrinking family, the cheapest way to
   admit a candidate is to withdraw its unsuccessful siblings."*

**Verdict: EVAPORATED — a completed arithmetic result. Rank 4 comes off the queue.** The merges
should still be *declared* as bookkeeping (merge 2 is the right shape for target 2's family), but
they must never again be described as a route to an admission.

**Constraint B, honoured:** nothing here re-declares, re-sizes or re-bills any family. The BH
arithmetic above is reported at the estate's existing declaration and at each merge as a
measurement. The admission verdicts remain the gate-repair lane's.

---

## 5. TARGET 4 — the funnel's abstain discipline. **EVAPORATED.**

**The claim** (Lane D rank 2, ledger row A3): +18.9 R (Feb), +6.6 R (Apr+May), +28.9583 R
(Jun+Jul), *"worst-case basis"*, three virgin reads, never negative, the one **passing** gate in the
read that killed the rule, and nothing was ever built on it.

### 5.1 The three numbers are not on one basis

| window | abstain sel/res/cens | mixed sel/res/cens | margin, **actual** | margin, **worst-case** | published |
|---|---|---|---:|---:|---|
| February 2026 | 106 / 105 / 1 | 360 / 342 / 18 | **+18.9106** | +37.2830 | +18.9 ← actual |
| April+May 2026 | 67 / 66 / 1 | 317 / 254 / 63 | **+6.5999** | +71.6993 | +6.6 ← actual |
| June+July 2026 | 117 / 111 / 6 | 282 / 251 / 31 | +2.7432 | **+28.9583** | +28.9583 ← worst-case |

Two of the three published figures are the **actual** margin and the third is the **worst-case**
margin. Lane D's ledger labels all three *"worst-case basis"*; `JUNJUL_READ_RESULT.md` labels its
own gate *"(worst-case)"* correctly. The series has been read as a strengthening trend
(+18.9 → +6.6 → +29.0) when on a common basis it is a **collapse**:

* **actual basis: +18.911 → +6.600 → +2.743** (−85 % across three reads);
* worst-case basis: +37.283 → +71.699 → +28.958.

### 5.2 On the worst-case basis, 49–91 % of the margin is a censoring charge

`worst_case_net_r` charges every censored trade a full stop. `mixed` holds far more censored trades
than `abstain` because limit orders censor:

| window | censoring charge, abstain | censoring charge, mixed | share of the worst-case margin |
|---|---:|---:|---:|
| February | +1.024 | +19.397 | **49.3 %** |
| April+May | +1.073 | +66.173 | **90.8 %** |
| June+July | +6.120 | +32.335 | **90.5 %** |

The June/July headline of **+28.9583 R is 90.5 % "mixed carried 25 more unresolvable trades."**

### 5.3 Paired by day, on either basis

| window | actual: total / t / p | worst-case: total / t / p |
|---|---|---|
| February (20 days) | +18.911 / +1.372 / **0.170** | +37.283 / +2.651 / 0.008 |
| April+May (43 days) | +6.600 / +1.197 / **0.231** | +71.699 / +5.626 / <0.0001 |
| June+July (42 days) | +2.743 / +0.427 / **0.669** | +28.958 / +3.333 / 0.0009 |

**Not one of the three actual-basis margins is distinguishable from zero.** The worst-case ones are,
and §5.2 says what they are measuring.

### 5.4 The falsification: the rule carries no information

Lane G's diagnosis was the leading hypothesis and it survives. Independently reproduced here on
Lane G's five-month pool table (146,745 resolved rows):

| population | n | E[net] | E[cost_r] | **E[net + cost_r]** |
|---|---:|---:|---:|---:|
| MARKET families (abstain's book) | 74,249 | −0.27254 ± 0.00436 | 0.28098 | **+0.00844 ± 0.00422** |
| LIMIT families (what abstain skips) | 72,496 | −0.19067 ± 0.00467 | 0.24450 | +0.05383 ± 0.00461 |
| `current_fvg_fill` | 60,911 | −0.19761 | 0.25214 | +0.05453 (= 1.07 × half its own spread) |

The LIMIT rows' apparent cost-free edge is the half-spread fill-selection artifact Lane G named;
their **net** is their own cost. So abstaining buys exactly the cost of the trades not taken — and
any rule that skips the same number of windows buys the same thing. Tested two ways:

**(a) On the published books, per decision.** Across all five months, inside `mixed`:

| | decisions | net | per decision |
|---|---:|---:|---:|
| LIMIT-topped (**what abstain skips**) | 661 | −20.9712 R | **−0.03173** |
| MARKET-topped (**what abstain takes**) | 298 | −6.3281 R | **−0.02124** |

The skipped half is worse by **0.0105 R per decision**. Skipping 661 decisions at random in a pool
whose mean decision is −0.028466 R would have saved **+18.816 R**; skipping *these* 661 saved
+20.971 R. **The entire information content of the abstain rule is +2.155 R over five months —
7.6 % of the +28.25 R five-month actual margin.** The other 92.4 % is "took 661 fewer negative-
expectancy decisions."

**(b) Count-matched control, 20,000 draws** (`funnel_limit.py`, on the reconstructed top-of-window
book: 646 windows with `pred ≥ 0.10`, 375 LIMIT-topped):

| | R saved |
|---|---|
| skipping the LIMIT-topped windows | **+29.72** |
| skipping 375 windows **at random** | mean **+32.89**, CI95 [+6.69, +58.89] |
| **P(random abstention saves at least as much)** | **0.593** |

A coin does it better than half the time.

**The two tests disagree in sign, and that is the result.** (a) is the published book, where the
LIMIT-topped half is worse by 0.0105 R/decision, so the rule's excess over random is **+2.155 R**.
(b) is a reconstruction of the top-of-window book from Lane G's pool table (646 windows with
`pred ≥ 0.10` among resolved rows, against the published book's 959 decisions — the reconstruction
is an approximation of the policy, not the policy), where the LIMIT-topped rows are the *better*
half (E[net] −0.0793 ± 0.0520 against MARKET's −0.0991 ± 0.0668) and the excess is negative. The
two bracket zero at a scale of ±3 R against a per-trade sd of 1.14 R. **Both are ways of saying the
same thing: which windows you skip does not matter; how many you skip does.**

### 5.5 Does it transfer to the sleeve corpus?

No, and the reason is structural rather than statistical. The rule's operative content is *"do not
pay a spread for a candidate with no edge."* On the funnel corpus that is worth money because
`E[net] = −E[cost_r]` there. On a corpus with positive expectancy the same rule is a **cost**, not a
benefit — every skipped trade forgoes its edge. And the rule has no expression on the sleeve estate
in any case: every sleeve order is a market order, so there is no LIMIT-topped window to abstain on.
The generalisable form — *abstain when expected cost exceeds expected edge* — is the estate's
pre-trade cost gate, which already exists and which FA showed is the thing that refuses 100 % of
high-RR candidates.

**Verdict: EVAPORATED — the "one quantity that survived every out-of-sample read" is a trade-count
effect in a negative-expectancy pool, published on an inconsistent basis, and it is 7.6 % as large
as advertised even before significance.** Rank 2 comes off the queue.

---

## 6. What survives, ranked by value

| rank | what | value, restated | class | next step |
|---|---|---|---|---|
| **1** | **`volume_surge_reversal × index × D1`, the FAMILY** (not the regime cell) | **+0.1213 R/trade gross, ≈ +0.0995 net** of broker-true spread and slippage, n 610 over 100 decision days, six carriers, one mechanism | OOS-w, instrument-clean, **survives the quote-side repair with a −0.0086 R correction and zero migration** | declare it as **one member with six carriers** (merge 2), then gate once. Hours. It will not admit at any current family size — the point is to stop billing it six times. |
| **2** | **the merge bookkeeping itself** | 59 → 46 declared members, and the honest statement of what that does and does not buy | arithmetic, complete | declare merges 1–3 as provenance rows. **Never again cite them as a route to an admission.** |
| — | FB `current_ob_retest` 1.5D/0.25D | **nil** — the number is an artifact of a decision-anchored barrier clock on a resting limit | closed | remove from the queue; add the caveat to the transform's docstring |
| — | the funnel abstain discipline | **+2.155 R over five months** of actual information content, p 0.593 against a count-matched control | closed | remove from the queue |

**And one thing this lane found that is worth more than any of the four.**

> **The barrier clock is anchored at the decision instant, not the fill instant, and three of the
> ten funnel families are resting-limit families.** On FB's cell that defect is worth **+2.90 R per
> trade** — larger than the quote-side defect that reset the whole estate's published gross. It
> reaches `current_ob_retest`, `current_fvg_fill` and `current_breaker_re_entry`: **550,966 of the
> pool's 632,934 rows.** It is not in `MISMATCH_AND_RISK_REGISTER.md`, not in the phase-20 repair
> set, and not in Lane D's artifact census. Any number ever published for a LIMIT family from a
> decision-anchored walk is measuring excursion from a price the book never paid, and every such
> number should be re-derived under a fill gate before it is quoted again.

Two ledger corrections are filed above and should be applied at source before either sentence is
quoted onward: the FG "#1 next action" mis-citation (§2.5) and the `VOL_REGIME == hi` string claim
(§3.4).

---

*Every figure above is reproducible from `attrition_receipts/` against the sealed pools
(`CJ_RECLOCKED_S0R0_POOL_V1`, `CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1`, `AF_FAMILY_TRADES`), the
bars archive at `/Users/borr/GTOSActive/vps-bars-20260727`, the tick hold at
`lane-inputs-true-utc-hold-20260805`, Lane G's `pool_table.npz`, and the three committed funnel
validation results. No live path, config, or VPS artifact was read or written. This document confers
no promotion, arming, sizing or activation authority.*
