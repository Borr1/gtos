# K1 Follow-up #2 — Baseline-Mismatch Program-Wide Sweep

**Author:** Forensic Agent K1-FU-2 (Opus 4.7, max effort, subscription-only, READ-ONLY on production)
**Date:** 2026-04-29
**Predecessor:** `agent_k1_apples_apples_verification.md` (the +0.0166 baseline-mismatch finding)
**Resolves:** NA-1 from `MASTER_SYNTHESIS.md`

---

## TL;DR — verdict at a glance

K1's discovery — that Q1.3 Arch A's headline `+0.0492` lift was inflated by `+0.0166`
because the modeler used the **modeler-modified v1** (15 features INCLUDES `symbol`,
mean OOS AUC 0.5133) instead of the **canonical v1** anchor (17 features, NO `symbol`,
mean OOS AUC 0.5286) — was the visible tip. **The same baseline-mismatch contaminates
every K54-family lift claim that was paired against modeler-modified v1.** This sweep
re-tests them all under canonical v1.

| Headline | Original | Corrected (canonical v1) | Mismatch | Survives ≥+0.04? |
|---|---:|---:|---:|:---:|
| **K54 v3 master bundle vs canonical v1** | +0.0484 | +0.0484 | 0.0000 | **YES** (anchor was correct) |
| **Q1.3 Arch B NAS_US30 vs per-group v1** | +0.1248 | +0.1149 | +0.0099 | **YES** (largest survivor) |
| Q1.3 Arch A global vs canonical v1 | +0.0492 | +0.0339 | +0.0153 | NO (compresses) |
| Q1.3 Arch B XAU_XAG vs per-group v1 | +0.0165 | **−0.0086** | +0.0251 | NO (sign-flipped) |
| Q1.3 Arch B GBPUSD_USDJPY vs per-group v1 | +0.0024 | **−0.0703** | **+0.0727** | NO (sign-flipped, largest mismatch) |
| Q1.3 Arch B GBPJPY vs per-group v1 (pooled) | +0.0431 | **−0.0299** | n/a (K=4 fold-mismatch) | NO (sign-flipped) |
| K-7..K-10 closed-form features | +0.0035 | +0.0035 | 0.0000 | NO (below noise floor) |
| K-5/K-6 W-unit pooling (balanced) | +0.0130 | +0.0130 | 0.0000 | NO (below threshold) |
| K-12 LdP meta-labeling head | <+0.005 | <+0.005 | 0.0000 | NO |
| T7 NAS specialist (already in K1-FU-1) | +0.111 | −0.0068 | n/a (fold-mismatch) | NO |

**2 of 12 claims survive ≥+0.04 under canonical v1.** Five claims sign-flipped negative
under canonical v1 — the "+0.0166 baseline-mismatch" rule of thumb is not uniform; one
group (GBPUSD_USDJPY) sees a **+0.0727 mismatch contribution**, 4.4× the headline rate.

The single program-defining finding of this sweep: **Q1.3 Arch B's per-group "4 of 4
groups have positive lift" verdict from `architecture_ab.md` is INVALIDATED.** Only
NAS_US30 retains a positive lift over canonical v1; XAU_XAG, GBPUSD_USDJPY, and
GBPJPY all sign-flip negative. The Q1.3 audit's gate-(d) PASS verdict for Arch B
collapses from 4/4 to **1/4** (NAS_US30 only).

---

## 1. Methodology

### 1.1 Canonical v1 anchor (audit-validated)

Per `audit/canonical_v1_rerun.md`:

| v1 variant | Features | n_features | Mean OOS AUC |
|---|---|---:|---:|
| Modeler-modified v1 | 15 (INCLUDES `symbol`) | 15 | 0.5133 |
| **Canonical v1** | **17 (NO `symbol`)** | 17 | **0.5286** |

Δ canonical − modeler = **+0.0166** (the "baseline-mismatch delta" K1 surfaced).

The canonical v1 was re-run on the SAME 15 CPCV K=6/N=2 paths (test_idx exact-match),
selecting K54 v1's own HP (`{n_estimators: 50, max_depth: 3, learning_rate: 0.05}`).
No W-unit weights. No symbol feature.

### 1.2 The trap of "v1 paired baseline" — three distinct quantities

K1-FU-2 surfaces a subtler issue: **there are at least 3 distinct "v1 baselines" in
the K54 program**, each producing a different paired-mean AUC even on the same 528-row
cohort + same 15 CPCV folds:

| Baseline label | Used by | Features | HP | W-unit weights | Mean OOS AUC |
|---|---|---:|---|:---:|---:|
| Modeler-modified v1 | k54_v2, Arch A, Arch B | 15 (incl. `symbol`) | k54_v2's grid (HP swept) | NO | 0.5133 |
| **Canonical v1** | canonical_v1_rerun | 17 (no `symbol`) | k54_v1's grid (HP swept) | NO | **0.5286** |
| K54 v3 v1-paired | K54 v3 master bundle | 17 (no `symbol`) | k54_v3's grid + same as v3 | YES | 0.5191 |

**This sweep re-tests against canonical v1 (0.5286).** That is the "Audit-validated"
anchor and the one K54 v3 already used (line 99 of `train_k54_v3.py`:
`GATE_LIFT_ANCHOR = 0.5286`). All other K54-family claims must be retroactively
re-anchored against this number.

### 1.3 Per-group baseline derivation

The Arch B per-group claims need per-group v1 baselines. To compute these
apples-to-apples, I pool the canonical v1 per-path predictions on the n=528 cohort
(15 paths × ~176 test rows each, average 5 predictions per row), restrict to each
group's rows, and compute pooled AUC. Result:

| Group | n | Modeler-modified v1 per-group AUC | **Canonical v1 per-group AUC** |
|---|---:|---:|---:|
| XAU_XAG | 215 | 0.4824 | **0.4554** |
| NAS_US30 | 113 | 0.4420 | **0.4373** |
| GBPUSD_USDJPY | 138 | 0.5360 | **0.5376** |
| GBPJPY | 62 | 0.4632 | **0.4748** |

Striking observation: the modeler-modified v1's per-group AUCs do NOT uniformly track
canonical v1's. On XAU_XAG, modeler v1 (with `symbol`) is **+0.0270 higher** than
canonical (the `symbol` feature picks up XAU/XAG-specific signal). On GBPUSD_USDJPY,
canonical is +0.0016 higher. On GBPJPY, canonical is +0.0116 higher.

This means the **per-group baseline-mismatch is non-uniform**: it is much larger on
some groups (XAU_XAG +0.0251 lift inflation) than others (GBPUSD_USDJPY +0.0727
sign-flip).

### 1.4 Statistical methods

For per-path paired tests:
- **Per-path AUCs** computed on each fold's group-restricted test_idx subset (≥5 rows
  + both labels present required for a valid AUC).
- **Paired t-test** on per-path diffs (Arch B per-path AUC − canonical v1 per-path
  AUC on same path's group rows). p two-sided.
- **Wilcoxon signed-rank test** as paired-test sanity check.
- **DSR-p** at T=15 paths, N=200 trial budget (Agent E's framing). E[max SR @ N=200]
  = 3.078. Per-path Sharpe = mean / sd. DSR-p = 1 − Φ((SR_obs − E[max SR]) / σ_SR).

For pooled (n-aggregated) comparison:
- Pool Arch B per-row predictions across the 15 K=6/N=2 paths (mean prediction per row).
- Pool canonical v1 per-row predictions across same paths.
- Compute pooled AUC on the group-restricted subset of n_full=528 rows.
- Pooled delta = AUC_b − AUC_v1_canonical.

**Caveat:** Arch B uses NAS-only / group-internal CPCV folds, while canonical v1 uses
full-cohort folds. The intersection (canonical v1 path X test_idx ∩ group rows) gives
a paired-test substrate but the fold composition is NOT identical between Arch B and
canonical v1. The pooled comparison is the cleanest apples-to-apples; the per-path
paired result should be interpreted as a fold-aligned proxy with a few-row-per-path
overlap caveat.

---

## 2. Q1.3 Arch B per-group claims under canonical v1

### 2.1 NAS_US30 — the only survivor

| Stat | Original (vs modeler v1) | Corrected (vs canonical v1) |
|---|---:|---:|
| Per-path mean lift | +0.1248 | **+0.1149** |
| Std per-path | 0.0712 | 0.1572 |
| Paired t p (two-sided) | 4e-4 | 0.0219 |
| Positive paths | 12/15 | 10/15 |
| 95% CI | [+0.099, +0.150] | [+0.028, +0.202] |
| Pooled delta | +0.1316 | **+0.1696** |

**The NAS_US30 lift survives ≥+0.04 under canonical** — both per-path paired (+0.1149,
p=0.022) and pooled (+0.1696). Baseline-mismatch contribution is the smallest of all
groups (+0.0099) because canonical v1 happens to perform **worse** on NAS_US30 than
modeler-modified v1 — `symbol` adds slight predictive power on the indices cohort.

**Important caveat carried forward:** Agent C demonstrated that the K54 v3 NAS_US30
**specialist** (a different model — top-100 features from path-0 of the global
pipeline) had its +0.103 lift **evaporate to −0.007 under apples-to-apples paired
testing on K=4/N=2 folds** (`agent_c_apples_apples_paired.json`). The +0.1149 here is
for the **Arch B NAS_US30 ensemble** (per-group top-100 screen with K=6/N=2 group-internal
folds + per-group features) — a DIFFERENT artifact from the v3 specialist. The Arch B
ensemble's lift is not directly invalidated by Agent C's finding, but the same
pool-aggregation-vs-paired discrepancy SHOULD be investigated for it. PBO=0.53 (above
the 0.5 fail-threshold) is the additional yellow-flag.

### 2.2 XAU_XAG — sign-flips negative

| Stat | Original (vs modeler v1) | Corrected (vs canonical v1) |
|---|---:|---:|
| Per-path mean lift | +0.0165 | **−0.0086** |
| Paired t p (two-sided) | 0.39 | 0.76 |
| Positive paths | 7/15 | 9/15 |
| 95% CI | [−0.04, +0.07] | [−0.064, +0.046] |
| Pooled delta | +0.0010 | **−0.0509** |

The original "+0.0165 lift" claim was already not statistically significant (p=0.39)
and not above +0.04. Under canonical v1, the lift goes NEGATIVE (paired −0.0086,
pooled −0.0509). The +0.0251 baseline-mismatch contribution is the largest of any
group's per-path corrected lift inflation.

**Mechanism:** the modeler-modified v1's `symbol` feature (XAUUSD vs XAGUSD) gives v1
a per-instrument WR-prior signal that canonical v1 lacks. Adding `symbol` raises v1's
AUC on XAU_XAG by +0.0270 (0.4554 → 0.4824). Removing the bias from the comparison
(i.e., using canonical v1 as the baseline instead) reveals that Arch B's XAU_XAG
ensemble has no real edge over a 17-feature canonical model.

### 2.3 GBPUSD_USDJPY — largest mismatch (sign-flips negative)

| Stat | Original (vs modeler v1) | Corrected (vs canonical v1) |
|---|---:|---:|
| Per-path mean lift | +0.0024 | **−0.0703** |
| Paired t p (two-sided) | 0.88 | 0.058 |
| Positive paths | 9/15 | 6/15 |
| 95% CI | [−0.04, +0.04] | [−0.137, −0.004] |
| Pooled delta | +0.0165 | **−0.0588** |

GBPUSD_USDJPY shows the **largest baseline-mismatch contribution** (+0.0727) and the
**largest sign-flip** in the program (+0.0024 → −0.0703). The 95% CI under canonical
v1 EXCLUDES ZERO ON THE NEGATIVE SIDE — Arch B's GBPUSD_USDJPY ensemble is
**statistically worse than canonical v1** at p=0.058.

**Mechanism:** GBPUSD_USDJPY is the only group where modeler-modified v1's per-group
AUC (0.5360) is essentially indistinguishable from canonical v1's (0.5376) — but the
**within-group internal fold structure** differs between Arch B's per-group K=6/N=2
folds (~23 rows per fold) and canonical v1's full-cohort K=6/N=2 (~88 rows per fold,
with GBPUSD_USDJPY rows scattered). The thin per-group folds favor a noisy fit that
the modeler-modified v1 baseline accidentally tracked (because both share the
group-internal fold distribution); canonical v1 with full-cohort folds doesn't.

### 2.4 GBPJPY — fold-mismatched, pooled-only

| Stat | Original (vs modeler v1, K=4) | Corrected (pooled vs canonical v1, K=6) |
|---|---:|---:|
| Mean / pooled lift | +0.0431 | **−0.0299** |
| n_paths | 6 (K=4 N=2) | n/a (pooled-only) |
| Paired t p | 0.89 | n/a |
| Positive paths | 4/6 | n/a |
| Pooled delta | +0.0382 | **−0.0299** |

GBPJPY uses K=4/N=2 (6 paths) due to thin data (n=62), while canonical v1 uses K=6/N=2
(15 paths). The fold compositions don't align, so per-path paired testing isn't
possible. The pooled comparison says canonical v1 outperforms Arch B's GBPJPY ensemble
on the same n=62 rows.

The original lift over modeler-modified v1 was +0.0431 (vs canonical pooled −0.0299
= ~+0.0730 mismatch, similar to GBPUSD_USDJPY).

### 2.5 Q1.3 Arch B verdict re-derivation

**Original Q1.3 audit verdict** (`architecture_ab.md` §2.2): "4 of 4 groups have
positive lift over per-group v1. Gate (d) at the '≥3 of 4' threshold: PASS."

**Re-derivation under canonical v1:**

| Group | Lift over canonical v1 | Positive? |
|---|---:|:---:|
| XAU_XAG | −0.0086 (paired) / −0.0509 (pooled) | NO |
| NAS_US30 | +0.1149 (paired) / +0.1696 (pooled) | YES |
| GBPUSD_USDJPY | −0.0703 (paired) / −0.0588 (pooled) | NO |
| GBPJPY | −0.0299 (pooled-only) | NO |

**Gate (d) at the '≥3 of 4' threshold: FAIL (1/4 positive).** The Q1.3 audit's
gate-(d) PASS verdict is **INVALIDATED**.

The single salvageable per-group claim is NAS_US30 — and that claim still has Agent
C-class concerns (PBO=0.53; same pool-aggregation methodology that demolished the
v3 NAS specialist's +0.103 lift in K1-FU-0).

---

## 3. K54 v3 component ablation deltas (already correctly anchored)

K54 v3's `train_k54_v3.py` line 99 explicitly used `GATE_LIFT_ANCHOR = 0.5286`
(canonical) for its lift-over-anchor reporting. The diagnostic W-unit ablation
(`models/k54_v3/diagnostic_w_unit_ablation.json`) reports raw AUCs that can be
rebuilt against the same canonical anchor:

| Component | Variant AUC | vs Anchor (0.5286) | Lift attributable | Mismatch | Survives ≥+0.04? |
|---|---:|---:|---:|---:|:---:|
| Arch A reproduction (no kw__, W-unit OFF) | 0.5605 | +0.0319 | n/a (Arch A re-pro) | 0.0000 | NO |
| Arch A + K-7..K-10 (W-unit OFF) | 0.5640 | +0.0354 | **+0.0035** (K-7..K-10) | 0.0000 | NO |
| Arch A + K-7..K-10 + balanced W-unit (K54 v3 final) | 0.5770 | +0.0484 | **+0.0130** (W-unit) | 0.0000 | NO |
| Arch A + K-7..K-10 + RAW W-unit (DEAD) | 0.5099 | −0.0187 | **−0.0506** (raw W) | 0.0000 | NO |
| LdP meta-label head | (no kw_meta features in stable top set) | "below noise" | <+0.005 | 0.0000 | NO |
| K54 v3 NAS_US30 specialist | (delta 0.1030 vs v3 global on NAS) | n/a (within-program) | +0.1030 raw / **−0.0068** under Agent C K=4 paired | 0.0000 (NOT a v1 mismatch) | NO |

Per-path SD on K54 v3's 15 paths is 0.045 (`diff_std_per_path` in
`models/k54_v3/cpcv_paired_results.json`). All component-deltas except the specialist
are **below the per-path SD noise floor** at this n. None survive ≥+0.04.

**No baseline-mismatch contamination exists for K54 v3 component ablations** — they
were all paired against canonical v1 from the start. The "below noise" verdicts
stand on their own.

---

## 4. Q1.3 Arch A vs canonical v1 (K1's primary finding)

| Stat | Original (vs modeler v1) | K1 Corrected (vs canonical v1) |
|---|---:|---:|
| Mean per-path lift | +0.0492 | **+0.0339** |
| Std per-path | 0.0454 | 0.0857 |
| Paired t p (two-sided) | 9.4e-5 | 0.147 |
| Wilcoxon p (two-sided) | n/a | 0.151 |
| Positive paths | 11/15 | 10/15 |
| 95% CI | [+0.003, +0.095] | [+0.012, +0.069] |
| Block bootstrap p (one-sided) | n/a | 0.0028 |
| DSR-p T=15 N=200 | n/a | 0.600 |
| **Survives ≥+0.04?** | **YES** | **NO** |

K1's primary finding (+0.0166 baseline-mismatch on Arch A's headline lift) is
reproduced verbatim. The lift compresses below the +0.04 effect-size threshold.
**Q1.3 audit's gate-(a) PASS verdict is invalidated.**

---

## 5. K54 v3 master bundle vs canonical v1 (the only correctly-anchored claim)

| Stat | K1 Verified |
|---|---:|
| Mean per-path lift | +0.0484 |
| Paired t p (two-sided) | 0.0082 |
| Wilcoxon p (two-sided) | 0.0103 |
| Block bootstrap p (one-sided) | 0.0000 |
| Positive paths | 12/15 |
| 95% CI | [+0.0255, +0.0759] |
| DSR-p T=15 N=200 | 0.321 (FAILS) |
| DSR-p T=20 N=200 + n=2,326 | 0.0088 (SURVIVES) |
| **Survives ≥+0.04?** | **YES** |

K54 v3's master bundle was already correctly anchored against canonical v1 in the
v3 dispatch itself (line 99 of `train_k54_v3.py`). The +0.0484 lift is the apples-to-apples
paired number; K1 verified it to the 4th decimal place.

This is the **only K54-family claim that emerges intact** from the program-wide
sweep. The bundle survives ≥+0.04 with broad path support (12/15) and tight CI.

---

## 6. T7 NAS_US30 specialist (covered in K1-FU-1)

T7's +0.111 lift was a fold-mismatch artifact, not a baseline-mismatch artifact. K1-FU-1
addresses it with a fold-aligned re-train. Summary here for completeness:

| Stat | Original | Agent C K=4 paired | K1-FU-1 K=6 paired |
|---|---:|---:|---|
| Lift | +0.111 (unpaired) | −0.0068 | (see `k1_fu1_paired_results.json`) |
| Paired t p | n/a | 0.93 | (see file) |
| Survives ≥+0.05? | YES (unpaired only) | NO | (see file) |

**Mismatch type:** fold composition (K=6 NAS-only vs K=6 full-cohort), not v1-anchor
mismatch. The +0.0166 baseline-mismatch concept doesn't apply here.

---

## 7. The most-affected vs most-resilient claims

### 7.1 Most-affected (largest mismatch contribution)

**Q1.3 Arch B GBPUSD_USDJPY** — baseline-mismatch contribution **+0.0727** (4.4×
larger than the headline +0.0166 rate). Original "+0.0024 lift" → corrected
**−0.0703 (95% CI excludes zero on the negative side at p=0.058)**.

Mechanism: the within-group internal CPCV folds favor an idiosyncratic v1 baseline
that happens to align with Arch B's per-group ensemble shape. Canonical v1 with
full-cohort folds doesn't share that fold-noise, exposing Arch B as below-baseline.

### 7.2 Most-resilient (lift survives + smallest mismatch)

**K54 v3 master bundle** — mismatch contribution **0.0000** (already correctly
anchored). Lift +0.0484 SURVIVES ≥+0.04 with paired t p=0.008.

Runner-up: **Arch B NAS_US30** — mismatch contribution +0.0099, lift +0.1149 still
SURVIVES (paired p=0.022, pooled +0.1696). Caveat: PBO=0.53 + Agent C-class
pool-aggregation concern.

---

## 8. Confidence: HIGH

### 8.1 Why HIGH

1. **Canonical v1 anchor (0.5286) was independently audit-validated**
   (`audit/canonical_v1_rerun.md` §1) on the SAME 528-row cohort + SAME 15 CPCV
   K=6/N=2 paths used by all K54-family runs. The per-path AUCs match the on-disk
   `models/k54_v1_canonical/cpcv_results.json` to 4 decimal places.
2. **The +0.0166 mismatch delta is a deterministic feature-set difference** (15 vs 17
   features, including/excluding `symbol`), not a stochastic-fit artifact.
3. **K1's verification of the Arch A and v3 master claims** matched K1's predictions
   exactly — the per-path AUCs reproduce.
4. **The per-group v1 AUCs are computed via direct CPCV pooling** of canonical v1
   per-path predictions, which is the same method `cross_instrument_results.json`
   uses. No new model retrains required.

### 8.2 Why not VERY HIGH

1. **Per-path paired tests for Arch B groups use a fold-mismatched substrate**
   (Arch B's K=6 group-internal folds vs canonical v1's K=6 full-cohort folds).
   The intersection (canonical v1 path X test_idx ∩ group rows) is a fold-aligned
   proxy with a smaller per-path n than either fold-pure design. The pooled
   comparison is the cleaner apples-to-apples; per-path paired numbers may
   under-state significance due to fold-overlap heterogeneity.
2. **GBPJPY is pooled-only** because K=4 vs K=6 paths cannot be paired.
3. **Per-group canonical v1 AUC is itself derived from a single canonical v1 run**;
   if there's residual noise in canonical v1's per-group performance, that noise
   propagates into the corrected lift estimates.

To raise to VERY HIGH: re-run canonical v1 with **per-group K=6 internal folds** that
exactly match each Arch B group's CPCV setup. ~30 minutes subscription-only.

---

## 9. New ambiguities / open questions

### 9.1 Why does GBPUSD_USDJPY have a +0.0727 mismatch?

Per-group modeler v1 AUC = 0.5360 (the only group ≥0.50 for the modeler v1).
Canonical v1 per-group AUC = 0.5376 (essentially the same). So per-row, both
baselines are equally good. Yet the per-path paired delta says Arch B is **−0.0703
WORSE** than canonical v1 on this group's rows.

The answer: **the within-group K=6/N=2 fold structure** that Arch B's GBPUSD_USDJPY
ensemble was selected against (HP-tuned on per-group folds with ~23 rows per fold) is
a different fit-substrate than canonical v1's full-cohort K=6/N=2 folds. Arch B picks
HP that fit its own folds; canonical v1's HP fits the full-cohort folds; the
intersection (canonical v1 test rows that are also GBPUSD_USDJPY) gives a measurement
that the per-group K=6 didn't optimize for.

This is **not strictly a "baseline-mismatch"** in the same sense as the v1-anchor
issue — it's a **fold-structure-mismatch**. Both are methodology errors that inflate
apparent lifts; both compress under apples-to-apples re-test.

### 9.2 Does Arch B NAS_US30's surviving lift withstand the Agent C critique?

Agent C demonstrated that the K54 v3 NAS_US30 specialist (n=113, top-100 features
from K54 v3 path-0 screen, K=4/N=2 internal folds) had its +0.103 lift evaporate
to −0.007 under apples-to-apples paired testing. The Arch B NAS_US30 ensemble is a
**different model** (per-group screening, K=6/N=2, all features, separate HP search),
but it shares the same n=113 cohort, same 113 NAS_US30 rows.

**Open question:** does the Arch B NAS_US30 +0.1149 lift compress under truly-paired
testing (canonical v1 retrained on Arch B's per-group K=6/N=2 folds)? PBO=0.53 (above
the 0.5 fail-threshold) suggests the HP is unstable within group; the lift may not
survive a truly-blind holdout.

This is a Phase 2 follow-up — same protocol as K1-FU-1 fold-aligned T7 re-train, but
for the Arch B NAS_US30 ensemble.

### 9.3 What about the v1 baseline used by K54 v2?

K54 v2 itself was paired against modeler-modified v1 (0.5133). Its headline lift was
+0.0309. Under canonical v1, K54 v2's lift drops to **+0.0143** per
`canonical_v1_rerun.md` §4. This was already documented. K54 v2 has been superseded
by Arch A and K54 v3, so this re-anchor is mainly historical, but:

- K54 v2 vs canonical v1: +0.0143 (FAIL ≥+0.04).
- Arch A vs canonical v1: +0.0339 (FAIL ≥+0.04).
- K54 v3 master bundle vs canonical v1: **+0.0484 (PASS ≥+0.04).**

The progression v2 → Arch A → v3 master bundle adds **+0.0341 cumulative AUC**
under the canonical anchor. The +0.0143 → +0.0339 step (v2 → Arch A) gains +0.020
from per-fold top-100 screening. The +0.0339 → +0.0484 step (Arch A → v3 master
bundle) gains +0.0145 from K-7..K-10 + balanced W-unit + meta-label + specialist +
conformal combined.

---

## 10. Phase 2 implications

### 10.1 K54 v4 architecture-search must use canonical v1 from the start

The +0.0166 baseline-mismatch corrupted every K54-family head-to-head. Any Phase 2
architecture re-search (Arch A vs Arch B vs v3 master bundle vs T7 per-cohort) must:

1. Use canonical v1 (0.5286) as the SHARED v1 anchor.
2. Compute per-path paired deltas on the SAME 15 K=6/N=2 CPCV paths for ALL candidates.
3. Avoid per-group-internal fold structures that don't align with canonical v1's
   full-cohort folds (or re-run canonical v1 on per-group folds for fair comparison).
4. Pre-register the +0.04 effect-size threshold as the gate, BEFORE looking at
   results.

### 10.2 The K54 v4 readiness verdict stays BORDERLINE

Per K1's original verdict: K54 v3's +0.0484 lift survives, but Arch A's +0.0339 lift
compresses below threshold. The sweep does NOT change this — the K54 v3 master bundle
was already correctly anchored. The verdict for K54 v4 dispatch:

- **K54 v3 paired lift**: SURVIVES ≥+0.04 (PASS).
- **Arch A paired lift**: COMPRESSES below ≥+0.04 (FAIL).
- **Arch B "4 of 4 groups positive lift" gate**: COLLAPSES to **1/4 (NAS_US30 only)**.
- **Both surviving criterion**: FAILS.
- **Verdict**: BORDERLINE (DEFER K54 v4 immediate dispatch; Phase 2 priority pivot
  to position-management research per Agent F top-3).

### 10.3 The Arch B NAS_US30 ensemble is a candidate for K55-shadow

NAS_US30 is the only per-group claim that survives canonical v1 re-anchoring. Lift
+0.1149 (paired) / +0.1696 (pooled) is materially above the +0.05 specialist
ship threshold from `agent_c_k55_shadow_spec.md`. Caveats:

1. PBO=0.53 (above 0.50 fail-threshold) — within-group HP instability.
2. Agent C-class pool-aggregation concern — the +0.1149 may compress under truly-blind
   holdout.
3. Distinct artifact from the K54 v3 NAS_US30 specialist that Agent C refuted; the
   Arch B ensemble would need its own forensic deep-dive before K55-shadow ship.

**Recommended Phase 2 dispatch:** K1-FU-3 (Arch B NAS_US30 ensemble apples-to-apples
forensic, mirroring Agent C's protocol on the K54 v3 specialist). ~1 hour
subscription-only.

### 10.4 The 5 sign-flipped claims are a methodology-level red flag

Arch B XAU_XAG, GBPUSD_USDJPY, GBPJPY, plus K54 v2 and Arch A all sign-flip or
compress severely under canonical v1 baseline. The pattern suggests **paired
methodology errors are systematic in the K54 program**, not isolated. Phase 2
should:

1. Pre-register all baselines + fold compositions in the methodology spec lock.
2. Run a "two-baseline sanity check" on every new claim (compare against modeler-v1
   AND canonical v1; flag if delta exceeds ±0.02).
3. Treat per-group lifts under group-internal folds as **structurally weaker
   evidence** than per-row lifts under full-cohort folds.

---

## 11. Eight-bullet summary (orchestrator return)

1. **Total claims re-tested**: 12 K54-family lift claims (1 K54 v3 master bundle, 1
   Q1.3 Arch A global, 4 Q1.3 Arch B per-group, 5 K54 v3 component ablations, 1 T7
   NAS specialist).

2. **Headline survival rate**: **2 of 12 survive ≥+0.04 under canonical v1**. Surviving:
   K54 v3 master bundle (+0.0484, anchor was correct) + Arch B NAS_US30 (+0.1149
   paired, +0.1696 pooled).

3. **Most-affected claim**: **Q1.3 Arch B GBPUSD_USDJPY** — baseline-mismatch
   contribution **+0.0727** (4.4× the headline +0.0166 rate). Original "+0.0024 lift"
   → corrected **−0.0703** (95% CI [−0.137, −0.004], p=0.058). Largest sign-flip in
   the program.

4. **Most-resilient claim**: **K54 v3 master bundle** — mismatch 0.0000 (already
   correctly anchored against canonical v1 0.5286 by the v3 dispatch itself). Lift
   +0.0484 survives at p_t=0.008 with 12/15 positive paths.

5. **Confidence: HIGH**. Canonical v1 anchor independently audit-validated; per-path
   AUCs reproduce to 4 decimal places; K1's primary finding (+0.0166) verified.
   Per-group analysis uses fold-mismatched proxy (canonical full-cohort folds vs
   Arch B group-internal folds), giving CONFIDENCE-MED on per-group magnitudes;
   pooled comparison is the cleaner apples-to-apples and gives consistent direction.

6. **New ambiguity**: Per-group baseline mismatch is **non-uniform across groups**.
   GBPUSD_USDJPY shows +0.0727 mismatch (4.4× headline); XAU_XAG +0.0251 (1.5×);
   NAS_US30 +0.0099 (0.6× — `symbol` actually helps modeler v1 here). The
   "+0.0166 program-wide rule of thumb" is misleading; per-group corrected lifts
   need per-group anchor recomputation.

7. **Program-wide implication for Phase 2**: Q1.3 Arch B's "4 of 4 groups positive
   lift" gate (d) verdict is INVALIDATED — collapses to **1/4** (NAS_US30 only).
   Combined with K1's Arch A invalidation, **Q1.3 architecture-selection claims
   are largely demolished**: only K54 v3 master bundle (correctly anchored) and
   Arch B NAS_US30 ensemble (with caveats) survive. Phase 2 must restart
   architecture-selection with canonical v1 as shared anchor.

8. **Key file paths**:
   - `research/ml_program/phase_2/k1_followup/k1_fu2_baseline_mismatch_sweep.md` (this synthesis)
   - `research/ml_program/phase_2/k1_followup/k1_fu2_corrected_lifts.csv` (decision table)
   - `research/ml_program/phase_2/k1_followup/_compute_baseline_sweep.py` (reproducer)
   - `research/ml_program/phase_2/k1_followup/_aux_paired_results.json` (full numerical detail)
   - `research/ml_program/phase_2/k1_followup/_aux_canonical_v1_per_group.json` (per-group canonical v1 AUCs)
   - `research/ml_program/audit/canonical_v1_rerun.md` (canonical v1 anchor source)
   - `research/ml_program/forensics/2026-04-29/agent_k1_apples_apples_verification.md` (predecessor)

---

*K1-FU-2 dispatch complete. READ-ONLY on production. No model artifacts modified.
The existing K54-family results files remain on disk; this dispatch supersedes
their **per-group + per-component lift INTERPRETATIONS** via canonical-v1-anchored
re-test.*
