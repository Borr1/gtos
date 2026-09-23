# Session W — the door, and what walked through it

**Branch `phase5/walkforward-gate`. Blocks B420–B449. Not merged.**

---

## 0. Headline

The walk-forward gate exists, it is bound to production resolvers and to `src/costs` alone,
and **it can fail** — proven against constructed adversaries, against sleeves this programme
already knows are dead, and against three adversarial refuters who between them landed ten
defects, one of which admitted a sleeve that lost 17,840 R.

Then it was pointed at the live market-expansion book, over the full FTMO D1 archive at
broker-true cost. **Of the twelve `mx_*` sleeves the live config resolves — all of them
carrying `apply_to_execution: true` today — none is admitted at either standard you would
arm on.** One passes a standard explicitly labelled research-only.

Three of the twelve cannot be judged at all, and that is a data fact rather than a verdict:
`CADJPY` has no measured spread in the broker-truth artifact, and `EU50.cash` / `FRA40.cash`
are absent from both the artifact **and** the bars archive.

The owner-facing decision is `ADMISSION_STANDARD_OPTIONS.md`. This document is the audit
trail behind it.

---

## 1. Three claims in my own prompt were wrong, and I am following the prompt anyway where it conflicts

Per `WAVE_5_WORKING_AGREEMENT.md` §2, a prompt outranks any repo document; per §3, anything
the orchestrator hands over is a claim to test. Both applied.

**1.1 "Search `src/` and `scripts/`. There is no walk-forward implementation anywhere."**
(`SESSION_W_WALKFORWARD_GATE.md:19`, restated at `WAVE_5_PLAN.md:29` as *"Verified by search
across `src/` and `scripts/` on 2026-07-29"*.) **False.**
`src/research_infra/validation_integrity/` carries 15 modules — including
`walk_forward_oos.purged_embargoed_walkforward`, `dsr`, `pbo`, `perm_null`, `sealed_holdout`,
`trial_budget_ledger`, and a `gauntlet` that already composes five of them into one verdict.
94/94 of its tests pass. It is effectively dead code (one non-test caller in the whole repo),
which is presumably why the search missed it, but it is there and it is good.

What genuinely did not exist is a **per-sleeve, cost-bound, fidelity-aware admission gate**.
So this session composed the existing statistics rather than replacing them: `dsr`, `pbo`,
`regime_inflation` and `walk_forward_oos` are all called, not reimplemented.

**1.2 "R's `live_evidence.py` already carries a day-block treatment — read it before
inventing one."** (`:60`) **False at that file.** `live_evidence.py` has no bootstrap, no
resample, no cluster-robust SE and no autocorrelation computation; its only day-keyed code
is calendar bookkeeping for a coverage note. The day-block resample is in
`scripts/build_live_evidence_calibration.py:110-236`, and it lives on the unmerged
`phase4/learning-lane` branch — unreachable from this worktree. Reimplemented here with the
same construction and the reasoning cited.

**1.3 "`metals_core` up to 12 in one day, ρ 0.511."** (`:59`) **Misattributed.** Both primary
sources — `SESSION_R_LEARNING_LANE_RESULT.md:233-238` and `IMPLEMENTATION_STATE.md` B279 —
say **`sub_xvol_pullback`** (90 trades on 33 dates). `metals_core` is a different sleeve.

**Three more, against the artifacts rather than the prompt:**

- **`idxrev` is not "measured negative before any cost was charged."** `SURVIVOR_BOOK_V1.json`
  records `gross_r: +0.00585` on n=6473 — positive, and indistinguishable from zero. The
  artifact's own `killed_reason` string ("negative before any cost") is wrong for that sleeve
  and right for `metals_ob_micro` (−0.5 on n=7). This made `idxrev` a *better* control than
  intended: a zero-edge sleeve with a 6,473-trade sample is exactly the shape that defeats a
  gate whose null ignores day-clustering.
- **`fx_jpy`'s "−0.453 R gross, p 0.0059" is a different population.** The −0.453 R is the
  **JPY cluster pooled over 41 live trades** (`GATE_G1B_RECEIPT.md:640`), not `fx_jpy`'s
  530-trade validated stream, whose gross is **+0.28235**. And the p is quoted without the
  clause that produced it: `third_review_receipts/read_g1b.md:115` continues *"Bonferroni ×12
  → **0.0706, which does NOT survive at 0.05**."* A brief whose §1 lists multiplicity as a
  required control quoted the uncorrected p.
- **There is no file called "the B7.5 partition registry."** `WAVE_5_PLAN.md:61`/`:84`,
  `JANUARY_BANK.md:218` and this session's prompt all phrase it as though one exists. The only
  partition registry in the repo is
  `research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/ULTIMATE_EDGE_PARTITION_REGISTRY.jsonl`,
  from the June v4 route. **Its hazard is real** — `TRAIN` spans `2025-06-02 .. 2026-04-17`,
  which swallows all of March 2026 — but B7.5's own contract assigns March the opposite role
  (`"untouched_for_this_treatment_historical_challenge"`,
  `B7_5_POST_ACCELERATION_DECISION_CONTRACT.json:819,829`). Authoring a correct one is Session
  Z's. This gate's local defence is a sealed `reserved_blackout` that no fold boundary may
  land inside and no trade may overlap.

**And a count correction that matters for scope.** Measured through
`admission.effective_registry` with the live flags: the effective registry is **29 sleeves**,
of which the never-validated set is **9 candidate + 12 market-expansion = 21**, not 23. The
plan's "14 `mx_*`" is the `all14_swap_adjusted` collision-winner set; the live policy is
`positive_weighted12_after_swap`, which resolves **12**. There are **16** authored `mx_*`
specs in total. All three counts are correct and they are not interchangeable.

---

## 2. What was built

`src/research_infra/walkforward/` — eight modules, 57 behavioural tests.

| module | what it owns |
|---|---|
| `spec.py` | the sealed `GateSpec`. Every knob that could move a verdict is a field and `seal()` hashes all of them — **including `pooling_weights`**, the field B7.5 sealed thresholds around and left open. |
| `fidelity.py` | the per-sleeve generation-fidelity ceiling, and the refusal. |
| `panel.py` | `TradeRecord` → broker-true cost → day panel. `cost_r` is the only cost path. |
| `folds.py` | calendar folds, label-span purge, embargo measured from realised holds. |
| `stats.py` | day-block bootstrap, block sign-flip, BH/Bonferroni, block length, p-floor. |
| `gate.py` | seven gates → `ADMIT` / `REJECT` / `NOT_EVALUABLE`. |
| `options.py` | the three admission standards. |
| `registry.py` | sleeve → broker-symbol universe, via the production resolvers only. |

**Seven gates, each of which rejected a real sleeve in the pilot** — coverage, expectancy
(per day), expectancy (per trade), lifetime, stability, robustness, significance. None is
decorative.

### Two design points worth defending

**The embargo is measured, not nominal.** The brief was right that a nominal horizon would be
wrong — across twelve live sleeves the used-fraction of horizon runs 0.4% to 105%. So the
embargo is the p99 of the sleeve's *own* realised holds, taken only from trades that closed
strictly before the fold opens. A refuter confirmed the test side cannot move it: replacing
in-fold holds with 90-day holds left the embargo unchanged.

**The fidelity ceiling refuses to transfer a rate and defend the transfer.** K's per-bar class
rate is 96%, and the register carries that — but stamped `TRANSFERRED_CLASS` with its actual
basis attached, because reading K's per-sleeve table shows **148 of the 160 agreed per-bar
intents come from three core-book sleeves, and the entire `mx_*` family is represented by one
sleeve and five intents**. The prompt's table, and `WAVE_5_PLAN.md`'s, present 96% as though
it were a measurement of the `mx_*` family. It is a class rate, and K's own B171 says: *"do
not transfer a rate and defend the transfer."*

---

## 3. Proving it can fail

`receipts/w_negative_controls.py` → `W_NEGATIVE_CONTROLS.json`. **PASS on every arm.**

Five constructed adversaries, all rejected: shuffled labels at zero expectancy, random entry
at matched frequency, a one-fold regime, a gross-positive sleeve eaten by cost, and
day-clustered noise. A positive control — a real, stable, cost-surviving edge — is admitted,
because a gate that rejects everything is exactly as useless as one that admits everything
and the failure is harder to notice.

On the real W7 caches at the most generous carry available, **nothing is admitted and neither
known-dead sleeve gets through**. Two results from that run are worth keeping:

- **`metals_core` ADMITs at zero carry (+0.635 R/day) and REJECTs at its structural horizon
  (−0.053).** The gate independently reproduces the programme's own OD-3 finding that holding
  time, not commission, is what decides the book.
- **9 of the 11 core sleeves are `NOT_EVALUABLE` at a 95% cost-coverage floor** — seven of
  them on coverage, because broker truth cannot price `DASHUSD`, `XAUEUR`, `XAGEUR`,
  `XAUAUD`, `XAGAUD`, `EU50`, `FRA40`, `US2000`, `NATGAS`; the other two (`fx_jpy`,
  `fx_jpy_ny`) on sample, because their validated stream spans one year and cannot support
  the required number of folds. The coverage half is a fact about the tick archive, not a
  verdict about the sleeves, and it is why `coverage_policy="restrict_to_priced"` exists —
  evaluate the priceable subset and stamp the verdict with exactly what was dropped.

---

## 4. What the refuters found

Three refuters, distinct lenses, defaulted to "refuted". They were worth every token.

**What survived, measured rather than asserted:** the bootstrap null construction (Efron &
Tibshirani Alg. 16.1 verbatim; p uniform under a true null, KS 0.0148–0.0236 against a 0.0304
critical value); `max(p)` validity; Benjamini–Hochberg bit-for-bit against `statsmodels` on
both rejections and q-values; and `simulate_detail` causality — 4,000 paths with the decision
bar's o/h/l/v poisoned differed on **zero**.

**What broke, and is fixed.** Ten defects. The full list is in the commit messages; the four
that mattered most:

1. **A sleeve that lost 17,840 R over 23,325 trades reached `ADMIT` under the *strictest*
   option.** Three separate attacks with one mechanism — put the losses where the scored
   statistic does not look. Fold 0 is never scored (50,000 losers there changed nothing, and
   still counted toward the sample floor); day-mean aggregation weighs twelve losers the same
   as one winner; blackout drops were reported as a *count*, not an amount. Fixed by a
   `lifetime` gate over every priced trade including fold 0, a per-**trade** expectancy floor
   beside the per-**day** one, and publishing blackout R.
2. **The significance gate was mathematically unpassable in a reachable regime.**
   `block_length_auto` used `2/√n` — a significance threshold, not a decorrelation criterion —
   and pinned the block at the `n//4` cap when no lag qualified. A block sign-flip over B
   blocks has only `2^B` outcomes, so its p floors at `(1 + n_perm·2^-B)/(n_perm+1)`; at B=4
   that is **0.063**, above every threshold all three options can set. A series with a naive
   t-statistic of **13.49** came out at gate p = 0.125, and sweeping the block moved the
   decision statistic **1250×**. Now: AR(1) decorrelation length, `min_blocks=8`, the floor
   published, and when the floor is at or above α the sleeve is `NOT_EVALUABLE` rather than
   `REJECT` — that is a statement about the evidence, not the sleeve.
3. **22.0% of the pilot's rows were duplicates** (589 of 2,675). Live places each
   `(sleeve, symbol, decision_bar)` at most once (`book_owner.py:163`); the union D1 grid
   re-fires 5-day symbols on weekend instants contributed by 7-day crypto symbols — 2/7 =
   28.6%, which is the shape of the observed rate. Verdicts do not move (duplicates are
   byte-identical, so the day-*mean* is unchanged) but the sample gate had been told it had
   28% more evidence than it had.
4. **The cost artifact is a look-ahead, and it is first-order.** Spread is measured over
   **2026-06-18 → 2026-07-24** — 37 days — and charged as a constant to a 2007–2026 panel of
   which only 6.5% is in 2026. Cost is **33%–219% of gross R** on this family and flips two
   sleeves from gross-positive to net-negative on its own. Unavoidable with the archive that
   exists; it was undisclosed, and is now stamped on every gate result. **The direction is
   knowable: spreads compressed, so every pooled OOS mean above is optimistic.**

**One defect found in a shared instrument, reported per agreement §6.4.**
`validation_integrity/regime_inflation.py:239,303-305` computes
`fwd_all_mean_ratio = mean_in_window / mean_all` and flags on `ratio >= 1.5`, a *positive*
threshold. Once `mean_all` goes negative the ratio goes negative and the flag can never fire —
**the detector is defeated monotonically by making the concealed loss bigger.** Measured:
50,000 hidden losers gave ratio −0.847, `contamination_flag` False, and the verdict string
still read `"CLEAN: selection window is representative"`. Same sign-error family as F39.
Guarded at this gate's call site; the module itself is untouched and needs a fix.

**One defect found by my own adversarial test before any refuter saw it.** A
`min_oos_positive_fold_frac` of 0.50 is the coin-flip point and carries no information, and an
absolute leave-one-out floor of "> 0.0" is scale-blind. A sleeve with all its edge in one fold
pooled to +0.653 R/day, retained +0.0225 after its best fold was deleted, and reached ADMIT.
Replaced with a scale-free retention ratio; the same adversary now rejects at 3.4% retention.

---

## 5. What I did not do, and why

**I did not walk the nine candidate sleeves through the gate.** Seven are first-of-day, where
K measured the port at **19% live-recall**. A number for those sleeves would measure the
port's latch defect. They are refused with the reason attached. K said it first and better:
*"for those, replay is not a verification method — not this port's replay, and not anyone's."*
Session Y owns the repair; I did not pre-empt it.

> **AMENDED 2026-07-29 by Session Y (`SESSION_Y_FIRST_OF_DAY_RESULT.md`, B480–B503). Refusing
> them was right; the reason was not.** K's 19% is a **code-lineage artefact**: the port ran
> mainline against a live record produced by `redacted_host`, which has no
> `sleeves/_server_clock.py`, so every session window in nine sleeves sat 3 h apart. Under the
> matching lineage the port recovers **175 of 175** missing intents, 0 newly missed, and all
> seven reach **100% live-recall**; count agreement over the 2,640 cycles goes 86.44% → 98.86%.
> Two of the seven (`ny_crypto_momentum`, `kz_london_crypto_low`) were never first-of-day at
> all — they gate on an exact `(hour, minute)` with no latch — so the 19% class rate was
> computed over a mixed population.
>
> `fidelity._MEASURED` is updated exactly as this section's handoff asked, **and nothing else
> moved**: `fidelity_floor`, `fidelity_refusal_is_hard` and `scoreable()` are untouched. Two
> things Y hands back to you: (1) `scoreable()` gates on **recall alone**, so a generator
> emitting 40% junk would pass — a precision floor belongs beside `fidelity_floor`, and that
> is your design decision, not Y's; (2) `vss_fxcross_london_up_low` carries a 96% *transferred*
> stamp resting on **nothing observed for it in 38 days**, and it is a live-allowlist sleeve.

**I did not author the B7.5 partition registry.** It does not exist, it is Session Z's scope,
and the local defence (the sealed blackout) is in place meanwhile. §1 hands Z the exact
finding.

**I did not run a full-suite A/B before writing this.** The machine had 5–10 concurrent pytest
processes from the refuters and other worktrees, and agreement §5 records that five concurrent
suites once left 108 MB free and *silently killed captures*. The capture is running now; the
receipt lands with it. **Until it does, this branch is uncertified for merge.**

**The pilot is a pilot.** The full estate walk — all 16 authored `mx_*` specs, the three orphan
cache sleeves, the deep archive, full rigour — is Session X's. This run exists so the
admission standard is a choice between outcomes rather than adjectives.

---

## 6. Handoffs

**To X (walk the estate):**
- Use `coverage_policy="restrict_to_priced"` or you will refuse most of the core book on tick
  coverage alone.
- **Set `declared_family_size`.** Multiplicity is corrected within a run; 20 sleeves judged
  singly took P(≥1 junk admission) from 8.3% to **71.7%** in a measured sweep.
- **Pass `sleeve_symbol_allowlist=build_symbol_allowlist()`.** Without it the fidelity gate
  trusts the sleeve name, and renaming bypasses it.
- **Dedupe on `(sleeve, symbol, decision_bar_iso)`** before labelling — the live idempotency
  key. 22% of the pilot's rows were duplicates.
- The purge now re-aggregates train days from surviving trades. This was latent-only on the
  one-symbol D1 family and **will fire on `sub_xvol_pullback`** (12 trades in a day) and the
  M15 JPY sleeves on day one.
- `methodology_alternatives.romano_wolf_stepm:290` is a max-t bootstrap preserving
  cross-hypothesis dependence — better suited to a correlated family than BH, but as written
  it row-resamples iid and is two-sided, so adopting it would trade away the across-day
  dependence B279 measured as the larger error. A day-blocked StepM does not exist yet.

**To Y (first-of-day repair):** the fidelity register is the contract. Update
`fidelity._MEASURED` with the repaired recall and those seven sleeves become scoreable with no
other change.

**To Z (partition registry):** §1's finding, plus — `learned_edge_dataset_builder.py:667-691`
already implements partition-registry reading and fail-closed enforcement
(`load_partition_registry`, `partition_role_for_day`, `SealedPartitionError`). The reader and
enforcer exist; only the artifact is missing.

**To the owner:** `ADMISSION_STANDARD_OPTIONS.md` §7 has the three decisions.

---

## 7. The honest summary

The door is built and it has been kicked hard. The most valuable thing in this session is not
the gate — it is that the gate, pointed at twelve sleeves that are live in the decision book
today with execution authority on, admits none of them at any standard you would arm on, and
says clearly which of them it cannot judge at all and why.

That is a clean negative, and per agreement §7 it beats a rescued pass.
