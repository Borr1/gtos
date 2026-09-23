# B8 — THE PAIRED-TREATMENT SHADOW HARNESS

**Build lane.** Date 2026-08-12. Breakthrough lane 8 of the owner-commissioned build program.
Commissioned from `LANE_4_BREADTH_AND_THROTTLES_V1.md` §7.1, whose recommendation this is.

**Measurement and code only.** No broker call, no VPS contact, no config byte, no `src/` edit, no
git write, no deploy. Code under `b8_paired_shadow/`; receipts under `b8_paired_shadow/receipts/`;
deployment runbook at `B8_DEPLOYMENT_RUNBOOK_V1.md`. Seed 20260812 throughout.

---

## 0. THE FIVE THINGS TO READ IF YOU READ NOTHING ELSE

> **1. The instrument reproduces known truth exactly, at 22,343-decision scale.** Every one of the
> estate's published labels is re-derived from the bars under its published contract with
> **0 mismatches and a maximum absolute error of exactly 0.0**. Lane 8's three named controls
> reproduce to the trade — **crypto 181/181, energy_agri 67/67, sub_xvol_pullback 88/88**. The
> statistics layer independently reproduces Lane 4's paired channel to six decimals (cost-band
> difference SD **0.343693 = 0.343693**, quote-side **0.776332 = 0.776332**). A/A arms return
> `INERT` and **no p-value**.
>
> **2. The first seeded question is already ANSWERED, on sealed history, and it PASSES its own
> pre-declared bar.** The **ex-ante cost gate** — refuse any decision whose modelled pre-trade
> `cost_r` exceeds 0.20 — is worth **+0.0987 R per decision, 95 % day-block CI [+0.0817, +0.1151]**,
> n = 10,180 over 557 days, t 11.61, and it crossed its O'Brien-Fleming boundary at **28.6 % of its
> information horizon** (z 11.61 against a boundary of 3.67). It survives the one-day lag (**94.3 %
> retention**) and the within-day past/future split (early +0.0945, late +0.1027 — **no leak
> signature**). This corroborates a sibling lane's funnel measurement on a completely different
> surface.
>
> **3. Lane 4's 335× is real and it is 98 % BREADTH, not pairing — and that changes how questions
> must be posed.** Measured here, pairing alone buys **2.5× to 16.1×** (median 8.4×) in calendar
> time. The rest of Lane 4's factor is the 73× ratio between the estate's arrival rate and the armed
> book's. The consequence is operational: **a treatment posed of the whole estate resolves in weeks
> (Q7: 2.9 weeks at 0.10 R, 11.7 at 0.05 R); the identical treatment posed of one armed sleeve
> resolves in centuries** (Q1: 992 weeks; Q5a: 8,238 weeks), because that sleeve fires 1.8–3.6 times
> a month no matter how well you pair it. **Pair the treatment; pose it estate-wide.**
>
> **4. The harness caught a fidelity defect in its own book layer that was producing a significant
> false positive, and fixing it reproduced Lane 4 independently.** My first cluster-cap
> implementation blocked every same-day same-cluster repeat; the book
> (`placement_ledger.py:181`) **explicitly allows same-bar unit members** and blocks only a
> later-bar re-fire. The defect reported the armed four's cap price as **+0.324 R/day, CI
> [+0.065, +0.611]** — significant. Repaired, it is **+0.083 R/day, CI [−0.028, +0.222]** — not
> significant. On Lane 4's exact three-sleeve population the repaired layer gives **+0.0714 R/day =
> +0.266 R/month against Lane 4's independently computed +0.22 R/month**, and reproduces its
> structural finding exactly (**L4 is subsumed by L5** for a three-cluster book: 90 = 90).
>
> **5. Causality is enforced at arm-registration, not reviewed afterwards.** Every arm declares the
> information set its *treatment* reads; an arm naming a post-decision input **cannot be
> constructed**, and a same-day aggregate without a declared cutoff **cannot be registered**. The
> lag and past/future companions run automatically on every question. **17 of 17 arms carry the
> `FITTED_ON_FULL_HISTORY` flag** (AG's spread model is fitted over 2000–2026 and evaluated at each
> decision) — a flag this harness raises against itself.

---

## 1. WHAT WAS BUILT

| module | what it is |
|---|---|
| `substrate.py` | the paired substrate: 22,354 held decisions from `AQ_ESTATE_TRADES_V2.json.gz` + 123 bar series from `vps-bars-20260727`, with a fingerprinted cache (108 s cold, ~1 s warm) |
| `arms.py` | the `Arm` contract: one dimension varied, the held tuple asserted, every fill from the sanctioned labeller `walkforward.exits.replay` |
| `causality.py` | information-set declaration, registration-time refusal, the within-day past/future screen, the lag-companion gate |
| `paired_stats.py` | paired summaries, day-block bootstrap, O'Brien-Fleming alpha spending, the all-declared multiplicity ledger |
| `evaluate.py` | complete-case pairing, the pairing proof, book-level daily differencing |
| `questions.py` | the seven seeded questions, each with arms, pairing class, pass bar and population declared before the look |
| `controls.py` | C1–C7, the reproduction and adversarial controls |
| `emit_decisions.py` | **Lane 4 rung 1 itself** — the full 29-sleeve estate as a read-only shadow book, driving the estate's own `GenerationPort` over a bar source, appending decisions in the schema `live_shadow` reads back |
| `live_shadow.py` | the forward seam: preflight, live-decision intake, duplicate-refusing merge, the daily read |
| `run_harness.py` | the CLI that produces every receipt below |
| `test_b8_paired_shadow.py` | **28 behavioural tests**, all passing |

**The emitter is rung 1, running.** `emit_decisions.py` drives
`replay_policy.generation.GenerationPort` — which wraps `UltimateBookLiveEngine._generate_intents`,
the code path `run_book.py` itself runs — so the shadow book is the *book*, not a re-implementation
of the rules: the include-flag registry, the DF-1 filter, warmup, bar-count and broker-symbol
resolution all come from the engine. Measured on this machine over 2026-07-01..07-20, H4 grid:
**115 cycles, 72 candidates, 20 distinct decisions across 9 sleeves, 27.6 s**, from an active
registry of **32 sleeves**. One runner serves two bar sources with no code change — `CsvBarSource`
over the archive here, and a `BarSource` backed by `ShadowReadOnlyMT5Adapter` on the VPS. Two safety
properties are enforced in code rather than by convention: `runtime_config` forces the three live
gates false **after** merging (so a config that had them on cannot arm the emitter), and the
research `include_clean3` override is applied to the config *dict*, never to the R2-bound,
token-digest-bound file on disk.

**Zero broker mutation, proved rather than asserted (C6).** Static: an AST scan of every module finds
**no** mutation call site and **no** banned import (`MetaTrader5`, `socket`, `requests`, `urllib`,
`http`, `httpx`). The single `order_send` token in the package is `controls.py`'s own refusal probe,
reported separately as a *deliberate probe* rather than whitelisted silently — a scan that hides its
own exception is the scan an adversary edits first. Dynamic: `ShadowReadOnlyMT5Adapter.order_send`
raises `ShadowMutationRefused: forward-shadow lane must never transmit an order`.

### 1.1 Pairing is TYPED, and that is the whole instrument

A paired design that silently correlates its arms produces confident nonsense. Four classes, each
with its own meaning of *n*:

| class | what is shared | questions |
|---|---|---|
| `TRADE_PAIRED` | same decision, same bars, same entry; only the exit contract or charged cost differs | Q1, Q2, Q3 |
| `ENTRY_PAIRED` | same *signal*; the entry instant differs, so the arms do not share a fill — a grid confound is priced with a third arm | Q5a, Q5b |
| `SELECTION_PAIRED` | the treatment *removes* decisions; concordant rows contribute an exact 0 | Q4, Q7 |
| `BOOK_PAIRED` | a portfolio throttle; pairing is at the day level after the book is built | Q6 |

---

## 2. THE REPRODUCTION CONTROL — SEVEN CHECKS, ALL GREEN

`receipts/B8_CONTROLS_V1.json`. Total runtime **1.9 s** warm.

| # | control | result |
|---|---|---|
| **C1** | **Label identity.** Re-derive every published `r_gross` from the bars under the published contract | **22,343 rows checked, 0 mismatches, max abs error 0.0.** 11 decisions skipped, every one named and accounted (`no bars for XAUUSD/H4 @ 2005-03-23`, 9 × `sub_mid_dn_revert` on 2002–2006 JPY crosses) — the archive begins after those decisions |
| **C2** | **Population identity** | **29/29 sleeves reconciled** (26 exactly, 3 after named skips); `total_declared 22,354 = walked 22,343 + skipped 11`, **unaccounted 0**. Lane 8's named controls: **crypto 181/181, energy_agri 67/67, sub_xvol_pullback 88/88** |
| **C3** | **Statistics layer** against Lane 4's `G_PAIRED_AND_COSTLINE_V1.json` | n 10,180 = 10,180; cost-band SD **0.343693 = 0.343693**; cost-band mean **−0.03466 = −0.03466**; quote-side SD **0.776332 = 0.776332**; unpaired SD 1.4565 vs 1.4566. Measured noise reduction **4.2379** vs Lane 4's projected **4.2123** |
| **C4** | **A/A null** — two arms, one contract | `verdict = INERT`, `p_value = None`, `pairing_verdict = INERT_ARMS`. **The harness refuses to produce a t** |
| **C5** | **Sham treatment** — `maxbars` 80 → 400, genuinely different and economically near-inert | 20.4 % discordance, mean +0.0536, labelled `MEASURED` with the block/iid SE ratio surfaced. The check is not that the delta is zero; it is that a thin contrast is *labelled* as one |
| **C6** | **Read-only**, static + dynamic | static clean; 1 declared probe; `order_send` raises |
| **C7** | **Paired reproduction** of swarm2 Lane 8's `energy_agri` exit A/B | Lane 8 **−0.28829** (n 72, expanded surface); B8 **−0.294338** (n 67, live surface). Same sign, **2.1 % magnitude gap**, different symbol populations |

**C1–C3 verify three different things and none substitutes for another.** C1 verifies the walker,
C3 verifies the estimator, C7 verifies the two composed on a contrast another lane measured
independently. A harness that passed only C1 could still have a broken estimator; one that passed
only C3 could be walking a different program.

---

## 3. THE SEEDED QUESTIONS — MEASURED

`receipts/B8_QUESTIONS_V1.json`. Cost convention: mid spread band through the r1 quote-side anchor
(`r_new_mid`), i.e. **spread only** — Lane 4 §1's caveat carries, and it is why this harness
publishes treatment *differences*, where a common residual cost cancels exactly, and refuses to
publish an arm *level* as an economic claim.

All intervals are **day-block bootstrap** (2,000 resamples, whole trading days), never i.i.d.

| # | question | n | Δ R/decision | 95 % CI (block) | disc. | ρ arms | pairing × | seq. vs 0 | **verdict vs own bar** |
|---|---|---:|---:|---|---:|---:|---:|---|---|
| **Q1** | `--frontier-exits sub_xvol_pullback` 3R → **4R** (ARMED) | 88 | **+0.2788** | [−0.0150, +0.5212] | 53.4 % | 0.911 | 2.14 | CONTINUE | **UNRESOLVED** (bar 0.10 R) |
| **Q2** | `mx_btcusd` 2R → **5R** (disarmed) | 318 | **+0.3746** | [+0.1658, +0.5908] | 45.0 % | 0.709 | 1.12 | **STOP_EFFECT** | **UNRESOLVED** (bar 0.20 R) |
| **Q3** | `energy_agri` plain 4R → **live scale-out** (ARMED) | 67 | **−0.2943** | [−0.6077, +0.0296] | 44.8 % | 0.920 | 2.04 | CONTINUE | **UNRESOLVED** (bar 0.15 R) |
| **Q4** | spread-geometry floor 0.10 on the armed four | 860 | **+0.0818** | [+0.0160, +0.1398] | 31.2 % | 0.895 | 2.11 | CONTINUE | **UNRESOLVED** (bar 0.05 R) |
| **Q5a** | entry hour 1, `sub_mid_dn_revert` | 45 | +0.0889 | [−0.1702, +0.4000] | 6.7 % | 0.867 | 1.94 | CONTINUE | **UNRESOLVED** |
| **Q5b** | entry hour 1, `mx_btcusd` | 100 | −0.0300 | [−0.1500, +0.0600] | 3.0 % | 0.938 | 2.84 | CONTINUE | **UNRESOLVED** |
| **Q7** | **ex-ante cost gate 0.20, whole estate** | **10,180** | **+0.0987** | **[+0.0817, +0.1151]** | 25.5 % | 0.884 | 2.02 | **STOP_EFFECT** | **PASS** (bar 0.02 R) |

**Q2's row is the one to read carefully, because it is the shape a careless reader gets wrong.**
`STOP_EFFECT_VS_ZERO` and `UNRESOLVED` are not in tension: the sequential monitor answers *is there
an effect*, the pass bar answers *is it big enough to act on*. Q2's effect excludes zero and its
lower bound (+0.166) sits below its own 0.20 R bar. The harness names the sequential decision
`STOP_EFFECT_VS_ZERO` for exactly this reason, and every receipt carries a
`what_this_does_not_say` field.

### 3.1 Q7 in full, because it is the one that is answered

* **Effect** +0.0987 R per arriving decision, block CI [+0.0817, +0.1151], t 11.61, p < 1e−15.
* **Discordance** 25.5 % — 2,599 of 10,180 decisions are refused by the gate. `top1pct_share` 0.103
  and Kish n_eff 2,076: this is a population effect, not five rows in a trench coat.
* **Pairing** ρ between arms 0.884; measured noise reduction 2.02×; the variance identity
  `Var(D) = Va + Vb − 2·Cov` holds to −0.0 exactly.
* **Block vs i.i.d. SE** 0.008503 vs 0.006750, ratio 1.26 — **the i.i.d. interval was optimistic by
  26 %**, which is precisely why it is not the reported one.
* **Sequential** at information fraction 0.286 the observed z is 11.61 against an O'Brien-Fleming
  boundary of 3.67 (nominal 1.96). **STOP.** Boundary schedule: t=0.25 → 3.92, t=0.5 → 2.77,
  t=0.75 → 2.26, t=1.0 → 1.96.
* **Causality** — the two automatic companions:
  * **lag 1 day**: +0.0931 against +0.0987 unlagged, **94.3 % retention**, CI [+0.0762, +0.1097].
  * **within-day split**: early half +0.0945 (t 8.58, n 4,966), late half +0.1027 (t 12.87,
    n 5,214), gap +0.0082. **Flag OK** — both halves agree in sign and near-agree in magnitude.
    A leak would put the effect in the late half.
* **Sibling corroboration.** A sibling lane pre-registered the same treatment on the **funnel** and
  measured +0.04786 R/day, t 3.50, P(≤0) 0.0003. This is the same treatment on the **29-sleeve
  estate**. The units differ (R/decision here, R/day there) and the surfaces are independent;
  the agreement is in sign, in causal cleanliness, and in the order of the calendar cost.

### 3.2 Q6 — the cluster cap, and the false positive the harness caught on itself

`BOOK_PAIRED`: two throttle regimes over the same arriving stream, differenced day by day, resampled
by day.

| population | days | accepted, cap ON → OFF | Δ R/day | 95 % CI (block) |
|---|---:|---:|---:|---|
| full 29-sleeve estate, forward | 557 | 4,168 → 7,243 (**+73.8 %**) | **−0.5477** | [−0.8779, −0.1749] |
| armed four, forward | 108 | 143 → 151 (+5.6 %) | +0.0833 | [−0.0278, +0.2222] |
| Lane 4's armed three, forward | 70 | 90 → 94 (+4.4 %) | +0.0714 | [−0.0429, +0.2429] |

**On the full estate the cap is worth +0.55 R/day** — removing it admits 3,075 extra decisions whose
marginal contribution is materially negative (total R −29.5 → −334.6). That is the sleeve-surface
restatement of Lane 4 §2.3's funnel finding: **these throttles remove candidates that are worse than
what they keep.** On the armed set the cap's price is **not distinguishable from zero**, which is a
different and much weaker claim than the one my first implementation made.

**The defect, stated plainly because it is the most instructive thing in this build.** My first
`cap_builder` blocked every same-day same-cluster repeat. The book does not:
`placement_ledger.cluster_placed_today_other_bar` (`:173-184`) returns
`any(b != decision_bar_iso)`, so **every member of the same bar's unit places** and only a
*later-bar* re-fire is blocked — because admission's correlated unit *is* one unit spread across
members on one bar. The wrong version reported the armed four's cap price as **+0.3241 R/day, CI
[+0.0648, +0.6111]**: significant, actionable, and false. Repaired, the same question answers
**+0.0833, CI [−0.0278, +0.2222]**: not significant.

**Two independent confirmations that the repair is right, not merely different.** The uncapped
forward count reproduces Lane 4 exactly (**138 = 138** on the armed three), and Lane 4's structural
finding — *for a three-sleeve, three-cluster book, L4 is subsumed by L5* — reproduces exactly
(L5-only 90 = L4+L5 90). At Lane 4's own population the repaired price is **+0.0714 R/day =
+0.266 R/month against its independently computed +0.22 R/month**.

**The residual, unreconciled.** Lane 4 publishes 87 accepted where the repaired layer gives 90, and
92 where it gives 94 (a 3.3 % gap). It localises to the day key: Lane 4's 92 is reproduced *exactly*
by keying L4 on `(sleeve, symbol, ENTRY day)`, while `book_owner.py:2055` keys on
`decision_day`. This harness follows the source. Q6's **sign and structure are settled; its
magnitude carries a ±3 % keying caveat.**

### 3.3 What the harness says about the other five, and what it refuses to say

* **Q1** — the 4R contract on the armed `sub_xvol_pullback` is worth **+0.279 R/trade** and its
  interval **includes zero** at the block bootstrap ([−0.015, +0.521]) while the i.i.d. one would
  not. It does not clear its own 0.10 R bar and it does not admit under the declared family
  (q 0.127). **This is not a proposal**, and AS handoff 3's *"do not propose it"* stands.
* **Q3** — `energy_agri`'s live scale-out costs **−0.294 R/trade** against the plain contract its
  published economics describe, with C7 showing Lane 8's independent −0.288 on a different symbol
  surface. That is now **four instruments** on one armed sleeve (AD §6.2 −0.308 R/day, AU +0.2302
  restamp, Lane 8 −0.28829, B8 −0.294338). The interval still crosses zero at n = 67 and the block
  bootstrap ([−0.608, +0.030]); the *estimate* is stable, the *evidence* is thin, and at 3.1
  decisions/month the shadow needs **504 weeks** to settle it. **Q3 is the clearest case in this
  build for why sleeve-specific questions cannot be accelerated: pairing already buys 8.36×, and
  8.36× of 4,216 weeks is still 504.**
* **Q4** — the spread floor is worth **+0.082 R/decision** on the armed four (q 0.029, admits under
  the declared family), but it does not clear its own 0.05 R bar at the block interval's lower bound
  (+0.016). Its within-day screen is `OK` (early +0.056, late +0.146).
* **Q5a/Q5b** — both `NEAR_INERT` by construction and the harness says so. At 6.7 % and **3.0 %**
  discordance with Kish n_eff of **3**, these contrasts rest on a handful of outcome flips. Q5b's
  −0.030 R/trade is in the same direction and the same order as `run_book.py:186`'s own predicted
  **−0.019 R/trade** for this sleeve — a fifth, unplanned agreement with an estate document. **Q5a
  is flagged `SIGN_DISAGREEMENT`** by the within-day screen (early +0.205 n 39, late −0.667 n 6);
  at n=6 that is a small-sample artefact, and the screen's own text says to investigate rather than
  conclude.

**Why entry-timing contrasts are near-inert, structurally.** Under a stop/target contract R is
*quantised*: a stop is exactly −1 R and a target exactly +k R regardless of where the entry was
anchored, because the levels hang off the anchor. Moving the entry by an hour therefore changes R
only when it changes *which level is hit*. This is a property of the estate's contract, not of the
harness, and it means entry-timing questions carry far less information per decision than their n
suggests. The harness surfaces it through discordance; nothing else in the estate does.

---

## 4. THE MEASURED SPEED-UP — AND THE CORRECTION TO LANE 4's 335×

Requirement 5 was to quantify the speed-up actually achieved, not the one projected.

| question | forward rate | pairing SD | unpaired SD | **paired weeks @ own bar** | **unpaired weeks** | **measured speed-up** |
|---|---:|---:|---:|---:|---:|---:|
| Q1 xvol 4R | 3.6/mo | 1.028 | 1.941 | 991.6 | 9,100.5 | **9.18×** |
| Q2 btc 5R | 3.2/mo | 1.947 | 3.078 | 1,007.6 | 2,525.2 | **2.51×** |
| Q3 energy scale-out | 3.1/mo | 1.014 | 2.072 | 504.1 | 4,215.7 | **8.36×** |
| Q4 spread floor | 10.9/mo | 0.875 | 1.845 | 955.9 | 8,515.9 | **8.91×** |
| Q5a entry hour | 1.8/mo | 1.041 | 2.021 | 8,238.5 | 62,095.9 | **7.54×** |
| Q5b entry hour | 3.2/mo | 0.521 | 1.482 | 1,156.0 | 18,631.6 | **16.12×** |
| **Q7 cost gate** | **542.7/mo** | **0.681** | **1.373** | **72.9** | **592.6** | **8.13×** |

**Pairing buys 2.5×–16.1×, median 8.4×. It does not buy 335×.**

Lane 4's 335× is arithmetically correct and it decomposes as
`(0.7318/0.3437)² × (542.6/7.4) = 4.53 × 73.3 = 332`. **Only 4.5× of it is pairing; 73× is
breadth** — asking the question of the 29-sleeve estate rather than of the armed three. My measured
pairing factor (median 8.4×) is *larger* than Lane 4's 4.5×, and the calendar answer is still
centuries for a sleeve-specific question, because a sleeve that fires 3 times a month cannot be
accelerated by any estimator.

**The operational rule this yields, which is the build's main product:**

> **Pair the treatment; pose it estate-wide.** A treatment that is *about* the estate (a cost gate, a
> throttle, an admission rule) inherits both factors and resolves in weeks. A treatment that is
> *about one sleeve* (an exit contract, an entry convention) inherits only the pairing factor and
> resolves in years, however well it is paired.

**Days-to-answer for the estate-wide class, from Q7's measured paired SD of 0.681 at 542.7
decisions/month:**

| effect | **paired** | unpaired |
|---|---:|---:|
| 0.10 R | **2.9 weeks** | 23.7 weeks |
| 0.05 R | **11.7 weeks** | 94.8 weeks |
| 0.02 R | **72.9 weeks** | 592.6 weeks |

Lane 4 projected 3.0 weeks at 0.05 R using the cost-band treatment's SD of 0.3437; the ex-ante cost
gate's SD is 0.681, so the honest figure for **this** treatment class is **11.7 weeks**. Lane 4's
3.0 weeks is reproduced exactly for the treatment it was measured on (C3: SD 0.343693, 2.97 weeks).
**Different treatments buy different amounts of pairing, and the harness measures it per question
rather than assuming a constant.**

---

## 5. THE PAIRING PROOF — REPORTED, NOT ASSUMED

The brief required proof the arms are genuinely paired. Every question carries it.

| question | ρ between arms | Var identity holds | discordance | verdict |
|---|---:|---|---:|---|
| Q1 | 0.911 | ✓ (−0.0) | 53.4 % | PAIRED |
| Q2 | 0.709 | ✓ | 45.0 % | PAIRED |
| Q3 | 0.920 | ✓ | 44.8 % | PAIRED |
| Q4 | 0.895 | ✓ | 31.2 % | PAIRED |
| Q5a | 0.867 | ✓ | 6.7 % | PAIRED |
| Q5b | 0.938 | ✓ | 3.0 % | PAIRED |
| Q7 | 0.884 | ✓ | 25.5 % | PAIRED |
| **C4 A/A** | — | — | **0.0 %** | **INERT_ARMS** |

Three verdicts exist and all three are reachable: `PAIRED`, `INERT_ARMS` (identical arms — C4 hits
it), `SUSPECT_INDEPENDENT` (ρ < 0.2 — pinned by a synthetic test). The noise reduction is not
asserted: it falls out of the measured covariance through `Var(D) = Va + Vb − 2·Cov`, checked
numerically to −0.0 on every contrast.

---

## 6. CAUSALITY — BUILT IN, BECAUSE A PERMUTATION NULL CANNOT SEE A LEAK

`causality.py`, `receipts/B8_CAUSALITY_LEDGER_V1.json`. Commissioned mid-build after a sibling lane's
only OOS-predictive finding was killed as a lookahead artifact: its regime features aggregated over
**every candidate on the trading day**, including candidates generated after the trade being scored,
and it survived walk-forward, strictly-prior training, daily prequential refit and **four separate
permutation nulls**.

**The standard, recorded in the harness's own source so it is not re-learned: a permutation null is
NECESSARY AND NOT SUFFICIENT.** A permutation null permutes *labels*; a leak present in every
permutation contaminates the null and the alternative identically, so the contrast between them is
clean while both are wrong.

**Three mechanisms, all enforced rather than documented:**

1. **Registration-time refusal.** Every `Arm` declares an `InformationSet` and validation runs in
   `__post_init__`. An arm naming a `POST_DECISION` input **cannot be constructed**; a
   `same_day_aggregate` input without a declared `cutoff_discipline` **cannot be registered**. Both
   are pinned by tests. The distinction that makes this workable is stated in the module: every
   arm's *label* comes from bars after the decision — that is the outcome and it is meant to. What
   may never come from after the decision is the *treatment rule*.
2. **Automatic companions.** The within-day past/future split runs on **every** question; the
   one-day lag runs wherever the treatment reads time-indexed market state. Where a lag is
   meaningless — lagging *"apply a 4R target"* by a day is still *"apply a 4R target"* — the harness
   returns `NOT_APPLICABLE` **with the reason**, because a fabricated companion that always passes
   is worse than none.
3. **A flag the harness raises against itself.** **All 17 registered arms** carry
   `FITTED_ON_FULL_HISTORY`: AG's spread model is evaluated at each decision's own instant (causal)
   but was *fitted* over 2000–2026, so a 2019 decision is priced by a model that saw 2026. This is
   model-in-sample rather than feature-in-sample leakage — it cannot manufacture a per-decision
   signal the way a same-day aggregate can — but it is not nothing, and it is stamped on every arm
   rather than mentioned once in a footnote. **No arm in this build reads a same-day aggregate.**

**Result of the screens on the only question that passed:** Q7 retains 94.3 % of its effect under a
one-day lag and shows +0.0945 early / +0.1027 late within the day. Neither is the leak signature.

---

## 7. MULTIPLICITY — THE FAMILY IS EVERY ARM EVER REGISTERED

`receipts/B8_MULTIPLICITY_LEDGER.jsonl` (append-only) and `B8_QUESTIONS_V1.json → multiplicity`.

Declared family **17 arms**, 10 with p-values, BH at the estate's ratified α = 0.10 (all-declared
basis, `CANDIDATE_FAMILY_V1.json → ratified_rule`). **5 admit:**

| arm | p | BH threshold | admits |
|---|---:|---:|---|
| `estate@ex_ante_cost_gate_0.2` | < 1e−15 | 0.0059 | ✓ |
| `estate@ex_ante_cost_gate_0.2_lag1d` | < 1e−15 | 0.0118 | ✓ |
| `sub_mid_dn_revert@entry_decision_close_native` (grid confound control) | 7.4e−6 | 0.0176 | ✓ |
| `mx_btcusd@target_5R` | 5.4e−4 | 0.0235 | ✓ |
| `armed4@spread_geometry_floor_0.1` | 8.5e−3 | 0.0294 | ✓ |
| `sub_xvol_pullback@target_4R` | 0.0449 | 0.0353 | ✗ (q 0.127) |
| `energy_agri@partial_be_runner_2R` | 0.0717 | 0.0412 | ✗ (q 0.174) |

The ledger counts **arms, not conclusions**: the seven registered-but-untested arms (controls,
aux confounds) sit in the denominator. An arm you registered and did not report is a look you took.
The ledger is append-only across loads and a test pins that a re-run cannot shrink the family.

---

## 8. WHAT I GOT WRONG, AND THE LIMITS

**Five defects found by my own adversarial passes, all in this build, all fixed before publication.**

1. **The selection-class power arithmetic was wrong by ~1/discordance².** The first draft powered
   `SELECTION_PAIRED` contrasts off the discordant subset *and* divided the arrival rate by the
   discordance. Since `sd_all² ≈ discordance · E[d² | discordant]`, the two routes agree only when
   the discordant mean is zero. At Q7's 25.5 % discordance it would have **overstated the calendar
   cost roughly tenfold**. The estimand is now uniform across all four classes — the mean difference
   per *arriving* decision — and `time_to_answer` no longer accepts a discordance argument at all.
2. **The book layer's cluster cap did not match the book** (§3.2). It produced a significant false
   positive on armed money.
3. **The static read-only scan flagged its own refusal probe.** Fixed by reporting the probe
   separately rather than whitelisting it, so the exception is visible in the receipt.
4. **The emitter anchored forward entries at the CYCLE instant, not the decision bar's close.**
   A cycle at 00:00 can surface a bar that closed at 21:00 (measured: a 180-minute surfacing lag on
   14 of 20 emitted decisions). Anchoring on the cycle would have silently re-anchored every forward
   decision and broken pairing against sealed history, whose anchor is `bars[i].c` — the sanctioned
   labeller's. Fixed to the bar close, with `surfacing_lag_minutes` kept alongside rather than
   discarded.
5. **The emitter's resume-dedupe key was type-unstable.** The file stores the timeframe as a name
   (`"H4"`), the engine returns the integer (`16388`), so a reloaded key never matched and a
   **restarted emitter would re-append every decision it had already written**. Double-counted
   decisions inflate the sequential monitor's information fraction, which is the entire basis of its
   alpha spending — a restart would have bought an unearned early stop. Fixed with a normalising
   `_key`, verified by a resume run (**0 appended, 72 duplicates, file unchanged at 20 rows**) and
   pinned by a test.

**Limits, stated so nobody inherits them as assumptions.**

* **The cost convention is spread-only.** Every number here is gross of commission and swap. It is
  the right convention for a *difference* — a common residual cancels exactly — and the wrong one
  for a level. The harness never publishes a level as an economic claim. For `SELECTION` arms the
  cancellation is **not** exact: the treated arm takes fewer trades, so it pays less residual cost
  than the control, and **Q4's and Q7's effects are therefore conservative** (a fuller cost model
  makes a gate that removes trades look better, not worse).
* **The spread model is fitted on the full archive** (§6). Flagged on all 17 arms.
* **Sleeve-specific questions are not accelerable** (§4). This is the harness's headline limitation
  and no amount of estimator work moves it.
* **Q5's entry-hour questions are M15-coverage-bound.** The M15 archive begins 2023-12-31, so those
  questions run on the forward window only — a coverage bound, reported, not a filter chosen after
  the look. n = 45 and n = 100 respectively.
* **The entry-hour deferral is bounded by the sleeve's own entry-lateness window** (2 h on H4, 12 h
  on D1), exactly as `run_book.py --entry-hour` bounds it. Decisions whose entry cannot reach the
  target hour inside that window are `ArmUnavailable` and drop from both arms under the
  complete-case rule. The population is therefore *decisions the flag can actually treat*, which is
  the right population and a smaller one.
* **`BOOK_PAIRED` prices R and says nothing about risk.** Q6 has no equity path and no governor, so
  it cannot see `p_fail_daily` — the quantity on which Lane 4 rung 2 rejects the cap relaxation.
  **A positive R price for removing the cap is not a recommendation to remove it.**
* **Q6's magnitude carries a ±3 % keying caveat** (§3.2); its sign and structure do not.
* **The forward seam is built and exercised OFFLINE, never against a live feed.** The emitter runs
  end to end here against the bar archive and its output round-trips through `live_shadow`'s intake
  (pinned by a test); the preflight passes on this machine. But **no live shadow row has been
  ingested**, because the deployed lane is on the VPS and this lane does not contact it. Two
  consequences: the harness as shipped still loads sealed history only — wiring the forward stream
  in is a three-line edit specified in the runbook §3.3 — and the emitter's behaviour against a
  `ShadowReadOnlyMT5Adapter` bar source is **[UNVERIFIED]**, argued from the `BarSource` protocol
  rather than measured.
* **The emitter's own decisions are NOT the sealed store's decisions and must not be pooled naively
  with them.** They are produced by the same engine on the same archive, but the sealed store was
  generated in one pass with its own duplicate handling (`n_duplicates_dropped: 1239`).
  `merge_forward` refuses duplicates on the pairing key, which is the right guard for *forward*
  rows; re-emitting a historical window that the store already covers is not a use this build
  validates.
* **No candidate is declared and no rule is proposed.** Q7 clears its own pre-declared bar on
  *sealed history*; turning that into a generation-side proposal is a separate act requiring the
  estate's admission standard and an owner decision.
* **Q3's four instruments agree in sign and disagree in unit.** AD §6.2 is R/day, AU is a restamp
  error, Lane 8 and B8 are R/trade. Do not add them.

---

## 9. RECEIPTS

| file | what |
|---|---|
| `b8_paired_shadow/receipts/B8_CONTROLS_V1.json` | C1–C7, §2 |
| `b8_paired_shadow/receipts/B8_QUESTIONS_V1.json` | every question, its pairing proof, its sequential look, its temporal companions, the multiplicity and causality ledgers, §3–§7 |
| `b8_paired_shadow/receipts/B8_CAUSALITY_LEDGER_V1.json` | every arm's declared information set and verdict, §6 |
| `b8_paired_shadow/receipts/B8_MULTIPLICITY_LEDGER.jsonl` | append-only declared family, §7 |
| `b8_paired_shadow/receipts/B8_PREFLIGHT_V1.json` | the deployment preflight, run on this machine |
| `b8_paired_shadow/*.py` | the harness |
| `b8_paired_shadow/test_b8_paired_shadow.py` | 28 behavioural tests, all passing |
| `B8_DEPLOYMENT_RUNBOOK_V1.md` | the runbook for the existing `gtos-shadow` clone — **not deployed** |

**Reproduce everything:**

```bash
cd docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/outcome_authority/swarm2/breakthrough
PYTHONPATH=<repo>:. python3 -m pytest b8_paired_shadow/test_b8_paired_shadow.py -q   # 28 tests, ~2 s
PYTHONPATH=<repo>:. python3 -m b8_paired_shadow.run_harness                          # ~70 s warm, ~3 min cold
# rung 1 itself: the read-only 29-sleeve shadow book over any window of the archive
PYTHONPATH=<repo>:. python3 -m b8_paired_shadow.emit_decisions \
    --out /tmp/decisions.jsonl --start 2026-07-01 --end 2026-07-20 --timeframes H4
```

**Inputs bound, none mutated:**
`docs/audits/fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz`;
`docs/audits/fable5-vision-audit-20260725/phase20/forward/receipts/R1_ESTATE_ROWS_V2.json.gz`;
`swarm2/lane4_receipts/G_PAIRED_AND_COSTLINE_V1.json`;
`swarm2/lane8_receipts/LANE8_MEASUREMENTS_V1.json`;
`/Users/borr/GTOSActive/vps-bars-20260727/` (read-only, outside the repo);
`research/operations/spread_model_2026_07_29/`;
`src/components/ultimate_book/{execution_packets,admission,primitives,symbol_map,bar_provider}.py`,
`sleeves/registry.py`, `src/safety/armed_set.py`,
`src/research_infra/walkforward/{exits,quote_side}.py`,
`src/research_infra/replay_policy/generation.py` (the emitter's `GenerationPort` driver),
`src/research_infra/wave21_forward_shadow/mt5_read_only.py`,
`src/utils/broker_clock.py`, `config/profiles/operator_profile.yaml` (all imported unchanged).

**No live path, no config byte, no R2-bound file, no VPS contact, no git write, no `src/` edit,
no deploy.**
