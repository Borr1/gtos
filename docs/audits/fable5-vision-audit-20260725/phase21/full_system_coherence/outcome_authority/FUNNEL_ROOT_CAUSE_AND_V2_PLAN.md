# The funnel puzzle — root cause, and the V2 plan

**Owner commission 2026-08-12** ("find out what is wrong exactly … where the whole
puzzle fell down, is it regimes is it sleeves is it training is it filtering is it
geometry is it probability is it risk is it scheduler is it timeouts … iterate them
in a full plan and solve the puzzle"). Orchestrator-run, no subagents. Post-read
autopsy: February, April, May, June, July 2026 are all read and sealed, so nothing
here spends validation currency.

**Evidence base.** Full candidate populations for all five read months, rebuilt
through the frozen loader chain with the frozen ridge fitted at each month boundary
on the frozen prequential protocol: **623,000 candidate occurrences, 176,000
resolved-filled**, cached at `/private/tmp/w21-puzzle-cache` with receipts
`ANSWERS.json`, `POOL_ANSWERS.json`, `DIRECTION_ANSWERS.json`,
`INVERSION_ANSWERS.json`. Every number below is measured, not inferred.

---

> ## ⛔ AMENDED 2026-08-12 — PHASE 0 RAN AND KILLED THIS DOCUMENT'S REPAIR PATH
>
> **`PHASE0_INVERSION_TRUTH_V1.md` (commit `728440500`) supersedes §3, §4-Phase-0
> and §6 below.** The inversion thesis — this document's one constructive finding —
> is **dead**, and it died of two arithmetic errors of mine, not of the risk §6
> predicted. Read the amendment before acting on anything here.
>
> | | claimed here | measured in Phase 0 |
> |---|---:|---:|
> | `structural_distance_extreme` inverted | +0.0927 R | **−0.0560 R**, 0/5 months |
> | `liquidity_sweep_reclaim` inverted | +0.0864 R | **−0.0534 R**, 0/5 months |
> | `cross_asset_lead_lag` inverted | +0.0718 R | **−0.0658 R**, 0/5 months |
> | `displacement_continuation` inverted | +0.0308 R | **−0.0514 R**, 0/5 months |
>
> 34 of 35 family-months negative, every family t = −3.9…−13.0, best cell in the
> entire study +0.0103. **Phase 0's kill branch fires as written; Phases 1–3 were
> conditional on that gate and are not reached.**
>
> **My two errors, named plainly.**
> 1. **The RR is 2.0, not 1.5.** I read `risk.min_rr: 1.5` and the `"UNCHOSEN"`
>    `FAMILY_TARGET_RR` table and stopped there. The sealed rows' `take_profit_1`
>    is actually written by the `momentum_exhaustion` dynamic execution policy at
>    `final_target_r = 2.0` (`dynamic_execution_policy.py:167-186`) — **2.0 on
>    81,968 of 81,968 rows**. So the driftless benchmark is **0.3333, not 0.400**,
>    and the inverted mirror pays **0.500, not 0.667**. That single correction
>    removes 75–80 % of the claimed edge.
> 2. **The arithmetic never charged the inverted contract its own spread.** It
>    reused the original's touch sequence, which was resolved on the *opposite*
>    quote side. The tell is direct: 0–7.1 % of candidates have **both** arms stop
>    (impossible for clean mirrors), correlating 0.995 with `spread_r`. Worth
>    another −0.06 to −0.17 R.
>
> **§6 item 1 — the failure I called most likely — is refuted by ~250×.**
> Inverted-entry adverse fill measures **0.0057 R** (+ ≤0.0006 R latency drift)
> against the ≥0.15 R I feared, on 21,449 trigger instants across 88.7 M ticks.
> Momentum-entry slippage was never the problem. My arithmetic was.
>
> **What survives, and it is the important half: §1 and §2 stand.** Against a
> corrected per-row driftless benchmark built from the actual fill price on the
> actual executable side, the families still run **z = −5.6…−25.0**. The pool is
> anti-predictive — **it simply is not invertible**, because the friction of taking
> the other side exceeds the anti-signal. Phase 0's control re-walks the *original*
> contract and reproduces the sealed cache exactly (**81,968 rows, 0 mismatches,
> max difference 0.0**), so the harness that killed this is trustworthy.
>
> **Consequence:** the V1 funnel pool is not repairable by inversion. Everything in
> §1, §2 and §5 (diagnosis, amplifiers, roadmap tracks) remains valid; §3's repair
> path and §4's Phases 1–4 do not.

---

## 0. The answer in five sentences

The system was built to **select** from a candidate pool, on the unexamined premise
that the pool contains extractable edge. It does not: every family is
negative-expectancy in every month, and of 366 conditioned subpopulations with
adequate sample, **one** is positive in all five months where a coin-flip null
predicts about eleven. The reason is not regimes, costs, training, or the scheduler
— it is that **every candidate family is directionally anti-predictive**: against a
driftless-walk benchmark of a 40 % hit rate at the configured 1.5R target, the
families deliver 10–31 %, at z = −10.8 to −48.9, stably in all five months. The
selector then converted "no edge" into "reliable loss" through cell concentration
and prequential momentum-chasing. ~~But the pool is not dead — it is inverted:
taking the opposite side of the three strongest anti-signals is worth +0.07 to
+0.09 R per trade, positive in all five months, by exact arithmetic on the same
price paths, with the entire edge living inside a cost band that must now be
measured properly.~~ **STRUCK 2026-08-12 by Phase 0 (see the amendment above): the
pool is anti-predictive but NOT invertible. At the true RR of 2.0 and with the
inverted contract charged its own spread, every family measures −0.02 to −0.07 R
per trade, 0 of 5 months positive. The anti-signal is real and smaller than the
friction required to trade against it.**

---

## 1. Question by question

| the owner's question | verdict | the measurement |
|---|---|---|
| **Is it regimes?** | **No — refuted.** | Family completion mixes are *stationary*: `liquidity_sweep_reclaim`'s target rate is 22.1 / 23.0 / 22.4 / 21.9 / 21.6 % across Feb/Apr/May/Jun/Jul; `structural_distance_extreme` 29.8–31.4 %. Nothing about the families' behaviour shifted. Regime matters only for *which* cell is temporarily lucky. |
| **Is it the sleeves/families?** | **Yes — the deepest layer.** | All 10 families negative per candidate, pooled and per month. Best `current_ob_retest` −0.008 R, worst `structural_distance_extreme` −0.569 R. Not one family is positive in even two of five months. |
| **Is it training?** | **Contributory, not causal.** | The prequential update works as designed — it just fits noise. Combined with `symbol_x_family` one-hot features it becomes a **cell-momentum chaser**: June's UK100×SDE luck entered training and boosted exactly that coefficient for July. |
| **Is it filtering?** | **Yes, and it is mis-aimed.** | Eligibility filters *cost* (≤0.2 R), never *quality*. The MARKET-top-abstain rule means the traded slice is not the ranked-best slice: in June 1,575 windows had top < 0.10, 414 abstained on LIMIT, **49 traded** — 2.4 % of windows. |
| **Is it geometry?** | **Yes — and the target was never chosen.** | `FAMILY_TARGET_RR` marks every family `"UNCHOSEN"` with the provenance *"risk.min_rr at the time of the decoupling; no founding artifact names a target."* The live value is the config **sanity floor, 1.5R**, which demands a 40 % hit rate. No family exceeds 31 %. Realized stops also overrun design: −1.07 to **−1.41 R** against −1.00 designed (SDE worst, and its target underpays at +1.24 vs 1.5). |
| **Is it probability?** | **Yes — near-zero skill, broken calibration.** | Population Spearman 0.011–0.041. Top predicted decile is **negative in 4 of 5 months**. Predicted +0.15…+0.19 against realized −0.21 on July's selected book. |
| **Is it risk/sizing?** | **Contributory.** | Flat 1R per trade with no cell-exposure budget: **69 % of July's book was one symbol×family** (UK100×SDE, 47 of 68 trades). |
| **Is it the scheduler?** | **Yes — a real hole.** | One-trade-per-window + same-symbol occupancy does not stop serial re-entry: a fast stop frees the slot and the next window re-enters the same cell. Measured **up to 8 trades/day on one cell**, 6/day twice in July. |
| **Is it timeouts?** | **Family-specific, real.** | Time-stop share: `session_open_range_break` **64 %**, `volatility_compression_expansion` 87 %, `current_ob_retest` 48 %, `displacement_continuation` 47 %. For those families the horizon, not the signal, decides most outcomes. `structural_distance_extreme` 1 %, `liquidity_sweep_reclaim` 19 %. |
| **Is it costs?** | **No.** | Realized cost ≈ 0.047–0.049 R per selected trade, against family deficits of 0.10–0.57 R. Costs are a tenth of the problem — *but see §4, they become decisive for the repair.* |
| **(unasked) Is it the labeler's sign?** | **No — checked, and it passes.** | On falling NAS100 (−3.54 % in July) shorts earned **+0.055 R** while longs lost −0.161; on rising UK100 (+2.00 %) longs beat shorts by +0.045. Direction mapping is correct, so the anti-signal below is a market fact, not a bug. |
| **(unasked) Does the pool contain edge anywhere?** | **No — and this is the finding.** | 366 conditioned cells (family, family×symbol, family×session, family×side, symbol) with adequate sample; **1 survivor** positive in all five months against **≈11 expected by coin-flip null**. The pool is not "mostly bad with gems" — it is uniformly negative. |

---

## 2. Where the puzzle actually fell down

**The architecture inverted the burden of proof.** Every layer — probability,
ranking, cost gating, occupancy, exit geometry, the frozen-prereg discipline — was
built to *choose well from a pool*. Nobody ever established that the pool was
choosable-from. Five months of full-population measurement says it was not, and the
evidence was always in reach: it needed one query, not one more model.

Three amplifiers turned that into the observed loss:

1. **Concentration.** The ridge's top-of-book is one cell 46–54 % of the time
   (Feb `ETHUSD|current_fvg_fill` 266/550; Jun/Jul `GER40|current_breaker_re_entry`
   230/426 and 149/323). The book is never diversified; it is a bet on one cell.
2. **Momentum-chasing on cells.** June's UK100×SDE returned **+10.06 R on 28
   trades while that cell's own population was −7.48 R that month** — luck on a
   −0.60 R/candidate cell. Prequential training banked the luck; July took **47
   trades on the same cell and got the population's true expectancy, −12.69 R**.
3. **No brake.** The postmortem's SD5 trailing brake would have cut June+July from
   −16.72 R to **−5.33 R** (17 stand-down days) — damage control that cannot
   create a positive.

**What is genuinely good and must be kept.** The selection layer has *real relative
skill*: discipline-beats-naive is +18.9 R (Feb), +6.6 R (Apr+May), **+28.96 R
(Jun+Jul)** — it reliably avoids the worst of a bad pool; top-1 beats ranks 2–5 in
4 of 5 months. And critically, **that skill survives inversion** (§3): ranking the
inverted trades by the ridge's *worst* predictions yields +0.061 R against +0.017 R
for its best, positive in 4 of 5 months. The selector is not wasted work — it was
pointed at a pool with the sign reversed.

---

## 3. ~~The constructive finding: the pool is inverted, not empty~~ — SUPERSEDED

> **This whole section is superseded by `PHASE0_INVERSION_TRUTH_V1.md`.** The
> benchmark column below uses 0.400, which is wrong — the true RR is 2.0, so the
> driftless benchmark is **0.3333**. The families remain anti-predictive against the
> corrected benchmark (z = −5.6…−25.0, measured per-row on the executable side), so
> the *direction* of this section's finding survives; its *magnitude* and its
> inverted-expectancy table below do not. Read the table as the erroneous version
> kept on the record, not as evidence.

Against a driftless walk at 1.5R/−1R (P(target first) = 0.400) — **the wrong
benchmark; see the note above**:

| family | barrier n | hit rate | vs 0.400 | z | time-stop share |
|---|---:|---:|---:|---:|---:|
| `current_fvg_fill` | 49,782 | 0.293 | −0.107 | −48.9 | 18 % |
| `liquidity_sweep_reclaim` | 18,642 | 0.274 | −0.126 | −35.1 | 19 % |
| `displacement_continuation` | 10,904 | 0.235 | −0.165 | −35.1 | 47 % |
| `current_ob_retest` | 3,931 | 0.228 | −0.172 | −22.1 | 48 % |
| `structural_distance_extreme` | 11,008 | 0.313 | −0.087 | −18.7 | 1 % |
| `cross_asset_lead_lag` | 9,935 | 0.311 | −0.089 | −18.0 | 9 % |
| `session_open_range_break` | 1,699 | 0.198 | −0.202 | −17.0 | 64 % |
| `current_breaker_re_entry` | 2,576 | 0.260 | −0.140 | −14.5 | 35 % |
| `volatility_compression_expansion` | 313 | 0.102 | −0.298 | −10.8 | 87 % |

Every family, every month (per-month rates vary by ≤0.03). A driftless entry is
break-even gross at any RR; these are **systematically worse than driftless**, which
means the entries carry information with the sign reversed.

**Inverted expectancy — exact path arithmetic** (which barrier a path touched first
is direction-independent; same price levels, roles swapped, so the inverted risk
unit is the old 1.5R target distance and the inverted target pays 0.667 R_new).
Valid only for MARKET-entry families; LIMIT families' fills change under inversion
and are excluded:

| family (MARKET) | filled n | inverted R/trade | months positive | range |
|---|---:|---:|---:|---|
| `structural_distance_extreme` | 11,118 | **+0.0927** | **5/5** | +0.081 … +0.116 |
| `liquidity_sweep_reclaim` | 23,049 | **+0.0864** | **5/5** | +0.068 … +0.101 |
| `cross_asset_lead_lag` | 10,919 | **+0.0718** | **5/5** | +0.064 … +0.082 |
| `displacement_continuation` | 20,737 | +0.0308 | 4/5 | −0.003 … +0.051 |

**The honest boundary, stated up front: the entire edge lives inside the cost
band.** At +0.05 R/side of cost the top three are +0.07…+0.09; at 0.10 R they are
+0.02…+0.04; **at 0.15 R every one of them is negative.** Measured cost on selected
trades was 0.047–0.049 R — but those were *fade* entries. Inverted trades enter
**with** momentum, where slippage is systematically worse. Nothing here is bankable
until that cost is measured on the inverted side, and that is Phase 0's whole job.

Independent corroboration from a different measurement path: the estate's own
Session CQ found an **inverted `current_breaker_re_entry`** worth +11.9 net R/trade
on TRAIN and holdout January VAL (`CANDIDATE_FAMILY_V27.json`) — the same thesis,
found from the other end, before this analysis existed.

---

## 4. V2 — a pool-first program, gated

The rule that governs everything below: **no selector work until the pool is
proven non-negative.** Each phase has a numeric gate and a kill branch.

### Phase 0 — Inversion truth (the decisive experiment) — **RAN 2026-08-12: GATE FAILED, KILL BRANCH FIRED**

> Result: no family clears the gate; every one is **negative in 5 of 5 months**
> (−0.023 to −0.066 R/trade). `PHASE0_INVERSION_TRUTH_V1.md`, commit `728440500`.
> Phases 1–4 below were conditional on this gate and are **not reached**. They are
> retained as the record of what was planned, not as work queued.
Re-walk the inverted contract properly instead of by arithmetic: real entries on
the inverted side, broker-true four-component costs, **momentum-entry slippage
measured rather than assumed** (the estate's slippage capture plus the tick archive),
per-family, over all five read months.
- **Gate:** at least one MARKET family clears **+0.03 R/trade after true costs, in
  ≥4 of 5 months**, with the cost term measured on inverted entries.
- **Kill branch:** if the whole edge is inside the slippage, the funnel program
  closes honestly and effort redirects to the armed estate. That is a real possible
  outcome and it is cheap to reach.

### Phase 1 — Geometry design (the target was never chosen)
The 1.5R target is a config sanity floor with `"UNCHOSEN"` provenance. For families
surviving Phase 0: MFE/MAE walks to find where price actually goes; sweep RR and
stop placement per family; fix the stop overrun (−1.07…−1.41 vs −1.00 designed) by
testing structure-based versus ATR-based stops. Enable the already-built,
currently-default-off `broad_origin_target_policy_enabled` per-family table with
values that are *measured* rather than inherited.
- **Gate:** a per-family geometry that improves Phase 0's expectancy out-of-month.

### Phase 2 — Selector V2 (only if Phases 0–1 pass)
Retrain on inverted labels — the existing ordering skill transfers (+0.044 spread,
4/5 months). Then, in priority order: **(a)** drop or heavily regularize
`symbol_x_family` one-hots (the memorization channel behind the June→July
disaster); **(b)** a calibration layer (isotonic/Platt) so "predicted 0.10 R" means
0.10 R — V1's largest single measured defect; **(c)** regime × family interactions
(the model has `trend_state_m15` but no interaction, so it cannot learn "don't fade
extremes in a trend"); **(d)** **cell-exposure budget** — hard cap per
symbol×family per day and per month, sized so no cell can be 69 % of a book;
**(e)** cell cooldown after consecutive losses; **(f)** the SD5 trailing brake as a
book-level stand-down.
- **Gate:** on held-back months, V2 beats both the inverted-pool average and the
  naive-mixed comparator.

### Phase 3 — Frozen validation
Same one-shot discipline that produced this quarter's honest verdicts: hash-sealed
prereg, pre-declared bar, owner trigger, no outcome reads before freeze.
**Surface reality, for the owner's decision:** the four 2025 windows are
**funnel-virgin but estate-spent** — wave-19's lane p2 consumed `june_2025`,
`august_2025` and `september_2025`, and `december_2025` was never restricted
(`V2_2025_WINDOWS_READINESS_V1.md`, commit `97487ca1e`). They are mechanically
ready (four `WindowSpec` lines; `june_2025` additionally needs an M15 lead-in or a
declared 06-12 start). Reading them is a funnel-first, not unseen-window, claim —
the same disclosure class as the junjul band. **Owner's call whether that standard
is acceptable; engineering is ready either way.**

### Phase 4 — Forward and live
The shadow lane (dual-lane, daily prequential refit, read-only) carries V2 forward
on the live feed. Incubation ceremony only after a Phase-3 pass, at the sizing
already approved (0.10 %/trade, max 2 concurrent, FTMO first), with the final
number stated at the ceremony.

---

## 5. Roadmap — all tracks

| track | state | next |
|---|---|---|
| **Funnel V2** | root cause established; V1 closed | Phase 0 inversion truth — the one thing that decides the program |
| **Armed estate** | 4 sleeves live both accounts + `mx_btcusd` on FTMO; untouched by any of this | unchanged; independent of the funnel |
| **Forward shadow** | merged (`eed6c496b`), daily refit merged (`1c9266850`), VPS deploy in progress | finish deploy; it becomes V2's forward instrument |
| **Validation surface** | Feb/Apr/May/Jun/Jul spent; 2025 windows funnel-virgin but estate-spent | owner decision on the 2025 standard; monthly forward windows are now a solved pipeline |
| **Data infrastructure** | June/July lesson: generators need deep pre-window history (D1 ≥ 30 bars, H4 ≥ 72, M15 weeks) | every future window export carries a ≥6-week lead-in by default |

---

## 6. What would falsify this analysis — **and what actually did**

Stated so the next session can attack it rather than inherit it. **It did, within
hours, and the scoreboard is below** (`PHASE0_INVERSION_TRUTH_V1.md`):

| # | predicted risk | outcome |
|---|---|---|
| 1 | inverted slippage ≥ 0.15 R erases the repair | **REFUTED by ~250×** — measured 0.0057 R adverse fill + ≤0.0006 R latency over 21,449 triggers / 88.7 M ticks. Not the problem at all. |
| 2 | time-stop re-pricing unreliable; `structural_distance_extreme` safest at 1 % | **INVERTED** — the `−gross/1.5` approximation is optimistic in *every* family, and SDE has the **largest** per-trade error (−0.168 R): the error scales with **spread**, not time-stop share. |
| 3 | LIMIT families unmeasured | **RESOLVED as not-worth-building** — an inverted limit is a *stop-entry* order; the committed machinery cannot express it (4,258 of 4,360 rows censor). |
| 4 | a fill/labeling asymmetry could mimic the anti-signal | **CLEARED independently** — direction mapping confirmed at corr +0.562 over 120 symbol-months, 78.3 % sign agreement, 0.85 % geometry censors. |
| — | *(unlisted, and it is what killed it)* | **My RR was wrong (1.5 vs the true 2.0) and my arithmetic never charged the inverted contract its own spread.** Neither risk appeared in this list. The lesson for the next session: the failure came from a premise I did not think to question, not from the uncertainties I did. |

Original list, retained:

1. **Inverted-side slippage ≥ 0.15 R** would erase the entire repair. Phase 0 measures
   exactly this, and it is the most likely way this fails.
2. **The time-stop re-pricing** in the inversion arithmetic is an approximation
   (−gross/1.5); families with high time-stop share (`displacement_continuation` 47 %)
   are the least reliable rows in that table. `structural_distance_extreme` (1 %) and
   `liquidity_sweep_reclaim` (19 %) are the most reliable.
3. **LIMIT families are excluded** from the inversion arithmetic by construction —
   their fill dynamics change under inversion. `current_fvg_fill` is the largest
   family in the estate (305k candidates) and its inversion is *unmeasured*.
4. If a **fill/labeling asymmetry** favouring the stop side existed, it would mimic
   the anti-signal. The direction check (§1, last row) rules out a sign error, and
   ambiguous first-touch cases are CENSORED rather than resolved as stops
   (6,152 + 6,231 censored rows), but a subtler asymmetry has not been excluded.

---

*Receipts: `/private/tmp/w21-puzzle-cache/{ANSWERS,POOL_ANSWERS,DIRECTION_ANSWERS,INVERSION_ANSWERS}.json`
(durable copy under the evidence hold). Sealed inputs: `FEBRUARY_…_R2.json`,
`APRIL_MAY_…_V1.json`, `JUNE_JULY_…_V1.json`.*
