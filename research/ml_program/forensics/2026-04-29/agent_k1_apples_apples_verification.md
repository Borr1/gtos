# Agent K1 — Apples-to-Apples Paired Verification of K54 v3 + Arch A + T7 NAS Lifts

**Author:** Forensic Agent K1 (Opus 4.7, max effort, subscription-only, READ-ONLY on production)
**Date:** 2026-04-29
**Methodology spec:** `agent_k1_methodology_spec.md` (LOCKED before run)
**Decision matrix:** `agent_k1_decision_matrix.csv`
**Per-claim numerical results:** `agent_k1_paired_results.json` + `agent_k1_dsr_aligned_scan.json`

---

## TL;DR — verdict at a glance

| Claim | Original lift | K1 paired lift | Survives ≥+0.04? | DSR-p T=15 N=200 | DSR-p T=20 N=200 | DSR-p T=20 N=200 + n=2,326 |
|---|---:|---:|:---:|---:|---:|---:|
| **K54 v3 vs canonical K54 v1** | +0.0484 | **+0.0484** | **YES** | 0.321 (FAILS) | 0.147 (FAILS) | **0.009 (SURVIVES)** |
| **Q1.3 Arch A vs canonical K54 v1** | +0.0492 | **+0.0339** | **NO** (compresses to +0.034) | 0.600 (FAILS) | 0.416 (FAILS) | 0.033 (BORDERLINE) |
| **T7 NAS_US30 specialist vs K54 v3 global** | +0.111 | **-0.007** (Agent C K=4/N=2 paired proxy) | **NO** (no edge under fold-aligned proxy) | 1.000 (NO EDGE) | 1.000 (NO EDGE) | 1.000 (NO EDGE) |

**Phase 2 K54 v4 readiness verdict: BORDERLINE.**
K54 v3 paired lift at +0.0484 survives the +0.04 threshold; Arch A's +0.0492 **compresses
to +0.0339** under the canonical v1 baseline (the Q1.3 audit's gate-(a) PASS verdict is
**invalidated**); T7 NAS's +0.111 lift evaporates to -0.007 under the fold-aligned Agent C
K=4/N=2 paired proxy.

The single program-defining finding: **K54 v3's headline lift survives because it was
already audited against the correct baseline (canonical v1 anchor 0.5286) by the v3 dispatch
itself; Arch A's headline lift fails because it was scored against the modeler-modified-v1
(0.5133) which is 0.0166 weaker than canonical v1.**

The +0.0166 baseline-mismatch is the primary methodology error Agent K1 detects.

---

## 1. Agent K1's discriminating methodological choice

The Q1.3 Arch A audit's `+0.0492` lift was reported as `arch_a_mean_AUC (0.5625) - v1_paired_mean_AUC (0.5133) = +0.0492` — but `v1_paired_mean = 0.5133` is the
**modeler-modified v1** (15 features, INCLUDES `symbol`), not canonical v1 (17 features,
EXCLUDES `symbol`). The canonical v1 audit at `audit/canonical_v1_rerun.md` showed:

| Configuration | Mean OOS AUC | Notes |
|---|---:|---|
| Modeler-modified v1 (15 feat, with `symbol`) | 0.5120 | Used internally as v3+ArchA baseline |
| **Canonical v1 (17 feat, NO `symbol`)** | **0.5286** | **Audit-validated baseline** |
| Δ | +0.0166 | The baseline-mismatch contribution |

K1 re-runs paired analyses on the **identical 15 CPCV folds** (verified `test_idx` exact
match across v3, ArchA, canonical-v1) but using the canonical v1 baseline. The +0.0166
contribution is mechanically subtracted from each lift claim.

---

## 2. Claim 1 — K54 v3 vs canonical K54 v1

### 2.1 Per-path AUC vectors (15 paths, identical folds)

| path | v3 AUC | canonical v1 AUC | Δ (paired) |
|---:|---:|---:|---:|
| 0 | 0.5488 | 0.5195 | +0.0294 |
| 1 | 0.6156 | 0.5666 | +0.0490 |
| 2 | 0.5124 | 0.5729 | -0.0604 |
| 3 | 0.5619 | 0.5831 | -0.0212 |
| 4 | 0.5366 | 0.5247 | +0.0118 |
| 5 | 0.6053 | 0.5091 | +0.0962 |
| 6 | 0.6436 | 0.5622 | +0.0813 |
| 7 | 0.5085 | 0.4933 | +0.0152 |
| 8 | 0.5852 | 0.4624 | +0.1228 |
| 9 | 0.6361 | 0.5659 | +0.0701 |
| 10 | 0.5606 | 0.5361 | +0.0245 |
| 11 | 0.5593 | 0.4121 | +0.1472 |
| 12 | 0.5586 | 0.5803 | -0.0217 |
| 13 | 0.6435 | 0.5068 | +0.1367 |
| 14 | 0.5784 | 0.5331 | +0.0453 |

### 2.2 Aggregate statistics

| Stat | Value |
|---|---:|
| Mean per-path lift | **+0.04841** |
| Std per-path lift | 0.0609 |
| SE (naive, sqrt-15) | 0.0157 |
| Paths with positive lift | 12/15 |
| Paired t-stat | 3.079 |
| Paired t p (two-sided) | **0.0082** |
| Wilcoxon stat | 16.0 |
| Wilcoxon p (two-sided) | **0.0103** |
| Block bootstrap obs | +0.0484 |
| Block bootstrap 95% CI | [+0.0255, +0.0759] |
| Block bootstrap p (one-sided lift>0) | **0.0000** |
| Pooled-AUC (n-weighted) v3 | 0.5770 |
| Pooled-AUC (n-weighted) canonical v1 | 0.5286 |
| Pooled delta | +0.0484 |

### 2.3 DSR projections (Agent E framing)

Projected SR = lift × 26.34 × sqrt(n/528):

| Cohort | T=15 | T=20 | T=50 (ONC-clustered) |
|---|---|---|---|
| **n=528 N=200** | DSR-p=0.321 (FAILS) | DSR-p=0.147 (FAILS) | DSR-p=0.0002 (SURVIVES) |
| **n=2,326 N=200** | DSR-p=0.0548 (FAILS) | **DSR-p=0.0088 (SURVIVES)** | DSR-p<0.0001 (SURVIVES) |
| **n=3,132 N=200** | DSR-p=0.0411 (BORDERLINE) | DSR-p=0.0057 (SURVIVES) | DSR-p<0.0001 (SURVIVES) |
| **n=4,892 N=200** | DSR-p=0.0291 (BORDERLINE) | DSR-p=0.0033 (SURVIVES) | DSR-p<0.0001 (SURVIVES) |

### 2.4 Verdict

**K54 v3 paired lift = +0.0484 SURVIVES at the +0.04 threshold.**

Strikingly the K1 paired lift exactly matches the originally-reported lift_vs_anchor (0.0484)
because K54 v3's `cpcv_paired_results.json` summary explicitly used `auc_v1_anchor_cpcv_honest =
0.5286` (the canonical anchor), not the modeler-modified-v1 baseline. K54 v3's lift was
ALREADY audited against the correct baseline. **The K54 v3 dispatch did the right thing;
Arch A's audit did not.**

Block bootstrap p_one = 0.0000 + paired t p_two = 0.0082 + Wilcoxon p_two = 0.0103 form a
**three-way agreement that the lift is non-zero**. The dispatch's "Stouffer combined p =
0.024" is MORE conservative than the Wilcoxon/t-test agree on, but all three are below the
α=0.05 ceiling.

DSR survives at T=20 + n=2,326 + N=200 (Agent E's Phase 2 minimum), confirming Agent E's
projection.

---

## 3. Claim 2 — Q1.3 Arch A vs canonical K54 v1

### 3.1 Per-path AUC vectors

| path | Arch A AUC | canonical v1 AUC | Δ (paired) |
|---:|---:|---:|---:|
| 0 | 0.4611 | 0.5195 | -0.0584 |
| 1 | 0.5426 | 0.5666 | -0.0240 |
| 2 | 0.5191 | 0.5729 | -0.0538 |
| 3 | 0.5928 | 0.5831 | +0.0097 |
| 4 | 0.6372 | 0.5247 | +0.1124 |
| 5 | 0.6138 | 0.5091 | +0.1047 |
| 6 | 0.6349 | 0.5622 | +0.0727 |
| 7 | 0.5397 | 0.4933 | +0.0464 |
| 8 | 0.5559 | 0.4624 | +0.0935 |
| 9 | 0.6403 | 0.5659 | +0.0743 |
| 10 | 0.4366 | 0.5361 | -0.0996 |
| 11 | 0.6087 | 0.4121 | +0.1966 |
| 12 | 0.4932 | 0.5803 | -0.0871 |
| 13 | 0.6132 | 0.5068 | +0.1064 |
| 14 | 0.5480 | 0.5331 | +0.0149 |

### 3.2 Aggregate statistics

| Stat | Value |
|---|---:|
| Mean per-path lift | **+0.03392** |
| Std per-path lift | 0.0857 |
| SE (naive) | 0.0221 |
| Paths with positive lift | 10/15 |
| Paired t-stat | 1.534 |
| Paired t p (two-sided) | **0.1474** (FAILS α=0.05) |
| Wilcoxon stat | 34.0 |
| Wilcoxon p (two-sided) | 0.1514 (FAILS) |
| Block bootstrap obs | +0.0339 |
| Block bootstrap 95% CI | [+0.0124, +0.0693] |
| Block bootstrap p (one-sided lift>0) | **0.0028** |
| Pooled-AUC (n-weighted) Arch A | 0.5625 |
| Pooled-AUC (n-weighted) canonical v1 | 0.5286 |
| Pooled delta | +0.0339 |

### 3.3 DSR projections (Agent E framing)

| Cohort | T=15 | T=20 | T=50 |
|---|---|---|---|
| n=528 N=200 | DSR-p=0.600 (FAILS) | DSR-p=0.416 (FAILS) | DSR-p=0.014 (BORDERLINE) |
| n=2,326 N=200 | DSR-p=0.126 (FAILS) | DSR-p=0.033 (BORDERLINE) | <0.0001 (SURVIVES) |
| n=3,132 N=200 | DSR-p=0.087 (FAILS) | DSR-p=0.018 (BORDERLINE) | <0.0001 (SURVIVES) |
| n=4,892 N=200 | DSR-p=0.053 (FAILS) | DSR-p=0.008 (SURVIVES) | <0.0001 (SURVIVES) |

### 3.4 Verdict

**Q1.3 Arch A paired lift = +0.0339 FAILS at the +0.04 threshold.**

This is the **most consequential finding of Agent K1**:

1. **Arch A's headline +0.0492 lift was inflated by the +0.0166 baseline-mismatch contribution**
   (modeler-modified v1 baseline 0.5133 vs canonical v1 0.5286).
2. Under canonical v1 baseline, the lift is +0.0339 — **below the Q1.3 brief's +0.04 effect-size
   threshold** (which Arch A was the only K54-family architecture to clear in the audit).
3. The Arch A audit's "Stouffer combined p = 9.4e-5" was computed against the wrong baseline.
   Recomputed paired t-test against canonical baseline gives p_two = 0.147 (FAILS).
4. **The Q1.3 audit's "Arch A passes Q1.3 gate (a)" finding is INVALIDATED.**

The block bootstrap one-sided p = 0.0028 says "the lift is directionally positive" — but
that is a much weaker claim than "the lift exceeds +0.04 with statistical significance".

DSR cohort projection survives only at n≥4,892 + T=20 (the most aggressive Phase 2 plan),
or n≥2,326 + T=50 (which requires ONC-clustered methodology not yet in scope).

---

## 4. Claim 3 — Agent I T7 NAS_US30 per-cohort vs K54 v3 global on NAS+US30

### 4.1 The structural problem

Agent I T7 trains a per-cohort 4-LightGBM, where the NAS_US30 sub-model uses K=6/N=2 CPCV
splits **on the n=113 NAS_US30 sub-cohort only**. K54 v3 global uses K=6/N=2 CPCV on the
full n=528 cohort, and predictions on NAS rows are extracted from those folds.

**The fold compositions differ.** Agent I's 15 NAS-only folds have different `test_idx`
than K54 v3's 15 full-cohort folds restricted to NAS rows. Per-fold paired comparison is
therefore impossible without retraining T7 on the same K=6 full-cohort folds.

### 4.2 Available evidence

| Evidence type | Source | Value |
|---|---|---:|
| Agent I T7 NAS_US30 per-cohort mean AUC | `agent_i_per_cohort_ensemble.json` | 0.7128 |
| K54 v3 global pooled AUC on NAS rows | computed by K1 from CPCV preds | 0.4984 |
| K54 v3 specialist pooled AUC on NAS (Q1.4) | `specialist_results.json` | 0.6014 |
| **Agent C K=4/N=2 paired delta (specialist - global)** | `agent_c_apples_apples_paired.json` | **-0.0068** |
| Agent I unpaired vs v3 global on NAS (UPPER BOUND) | computation | +0.2144 |
| Agent I unpaired vs v3 specialist on NAS (UPPER BOUND) | computation | +0.1114 |

### 4.3 The honest range

The fold-aligned proxy that K1 endorses is **Agent C's K=4/N=2 paired test on NAS_US30 v3
specialist vs v3 global** (`agent_c_apples_apples_paired.json`). This is the **only** test
that uses identical folds for paired comparison on NAS_US30. The result: **paired delta = -0.007** (n_paths=4, t-p=0.93, DSR-p=0.999, sr=-0.0495).

The honest range for "T7 NAS specialist apples-to-apples paired delta vs K54 v3 global"
is bounded by Agent C's -0.007 (paired, fold-aligned) and Agent I's +0.111 (unpaired,
different folds).

### 4.4 DSR projections

Under Agent E framing (lift × 26.34 × sqrt(n/528)):

**Using the Agent C K=4/N=2 paired proxy (-0.007 lift)** — DSR-p = 1.0 (no edge to defend).

**Using the Agent I unpaired upper-bound (+0.111 lift, vs Q1.4 specialist)** — DSR-p
SURVIVES at T=20 N=200 + n=528 (DSR-p=0.0067), but this is the **upper bound** that the
fold-alignment problem invalidates.

### 4.5 Verdict

**T7 NAS specialist's apples-to-apples paired lift cannot be confirmed to ≥+0.05 from
existing evidence.** Agent C's fold-aligned K=4/N=2 paired proxy says no edge (-0.007).
Agent I's unpaired number (+0.111) is suggestive but not fold-paired.

To resolve: **a follow-up dispatch must retrain Agent I T7 on the SAME 15 K=6/N=2 full-cohort
folds as K54 v3, then compute per-row paired AUC on the NAS_US30 mask.** This is the only
way to convert Agent I's claim into apples-to-apples evidence.

---

## 5. Decision matrix

| Claim | Original lift | Apples-to-apples lift | Survives ≥+0.04? | DSR-p T=15 N=200 | DSR-p T=20 N=200 | DSR-p T=20 N=200 + n=2,326 | Phase 2 implication |
|---|---:|---:|:---:|---:|---:|---:|---|
| K54 v3 vs canonical K54 v1 | +0.0484 | **+0.0484** | **YES** | 0.321 | 0.147 | **0.009 (SURVIVES)** | K54 v4 dispatch viable post-cohort-expansion |
| Q1.3 Arch A vs canonical K54 v1 | +0.0492 | **+0.0339** | **NO** (-0.034) | 0.600 | 0.416 | 0.033 (BORDERLINE) | Q1.3 gate-(a) PASS invalidated |
| T7 NAS vs v3 global on NAS (Agent C K=4 paired proxy) | +0.111 | **-0.007** | **NO** (no edge) | 1.000 | 1.000 | 1.000 | T7 K55-shadow needs fold-aligned re-test |

---

## 6. Phase 2 K54 v4 readiness verdict — **BORDERLINE**

**Decision logic:**

- K54 v3 paired lift = +0.0484 → **survives +0.04 threshold**
- Arch A paired lift = +0.0339 → **compresses to +0.034 (below +0.04)**
- Both required for Phase 2 K54 v4 minimum + T=20 dispatch per Agent E + the dispatch brief.

**Consequence:** since Arch A compresses below +0.04 under the corrected baseline, the
"both surviving" criterion fails. The verdict is **BORDERLINE**, NOT **APPROVED**.

**Recommended Phase 2 sequencing:**

1. **DEFER K54 v4 immediate dispatch**, since:
   - The K54 v3 lift surviving alone is necessary but not sufficient (the Q1.3 architecture
     selection that landed Arch A as the recommended substrate is now invalidated).
   - Arch A vs canonical v1 lift compression (-0.0153) suggests the v3 lift is partly absorbing
     "Arch A goodness" that doesn't isolate as a standalone architecture win. K54 v4 design
     needs a recomputed architecture-search baseline.

2. **Pivot Phase 2 first dispatch to position-management research** (Agent F top-3
   discoveries), per the dispatch brief's BORDERLINE-fallback path.

3. **Plan a corrected K54 v4 architecture search** for Phase 2 second wave — using
   canonical v1 as baseline from the start, and including the K54 v3 master bundle as
   one architecture-candidate vs Arch A vs Arch B.

4. **K55-shadow ship target** — defer until Agent I T7 is re-dispatched on the SAME 15 K=6
   full-cohort folds as K54 v3 (the fold-aligned re-test). Until then, neither the Q1.4
   specialist (which Agent C refuted) nor T7 (which K1 cannot apples-to-apples confirm)
   has fold-aligned positive evidence.

---

## 7. Open ambiguities / new findings

### 7.1 The +0.0166 baseline-mismatch is a program-wide pattern, not just Arch A

The same baseline-mismatch (modeler-modified v1 with `symbol` ≈ 0.5133 vs canonical v1
without `symbol` ≈ 0.5286) affects:
- All Q1.3 Arch B per-group lifts.
- All K54 v3 component-ablation deltas (`agent_a_component_ablation.json` and similar).
- All Agent I T2/T3/T4/T7 frame deltas in `agent_i_alternative_architectures.md` that
  reference K54 v1 anchor 0.5286 as "the K54 v1 baseline" — these are NOT mismatched
  because they cite the canonical 0.5286, but their ratio of "what's a real lift vs what
  fits below the +0.0166 baseline-mismatch noise" is unclear without re-running.

**Recommendation:** Phase 2 audit pass should sweep all K54-family lift claims through
the canonical v1 baseline test.

### 7.2 The K54 v3 + canonical anchor agreement is reassuring

K54 v3's dispatch did the correct thing — it used `auc_v1_anchor_cpcv_honest = 0.5286`
explicitly in `cpcv_paired_results.json`. The +0.0484 lift_vs_anchor IS the apples-to-apples
paired lift (verified by K1 to the 4th decimal place). This is the only K54-family claim
where the original number survives K1's re-verification.

### 7.3 Agent E's Phase 2 minimum projection is intact

Agent E's verdict at T=20 + n=2,326 + N=200 + lift=0.0484 → DSR-p=0.0088 SURVIVES is
**confirmed by K1**. This is the correct Phase 2 minimum cohort-target IF lift is +0.0484
and IF the lift is real (which K1 confirms paired, t-p=0.0082).

But the K54 v4 DEFER recommendation stands because the architecture selection (which Arch A
vs Arch B vs ensemble was supposed to settle) is now unsettled.

### 7.4 The Agent C / Agent I tension is unresolved

Agent C says NAS specialist effect is artifact (-0.007 paired); Agent I says T7 NAS specialist
effect is +0.111 (unpaired). Both can be true: Agent C tests K54 v3's specialist (per-fold
top-100 from path-0 of full cohort screen); Agent I tests a per-cohort top-100 inside-NAS
screen. Different feature sets → different effective models. K1 cannot resolve which is the
"true" T7 effect without retraining.

---

## 8. File index

- `agent_k1_methodology_spec.md` — locked methodology (this dispatch's protocol)
- `agent_k1_apples_apples_verification.md` — this synthesis
- `agent_k1_paired_results.json` — per-claim numerical detail
- `agent_k1_decision_matrix.csv` — readable decision table
- `agent_k1_dsr_aligned_scan.json` — DSR scan under Agent E's projection framing
- `agent_k1_methodology_spec.json` — JSON-form methodology spec
- `_agent_k1_verify.py` — main reproducer script
- `_agent_k1_dsr_align.py` — Agent-E-aligned DSR scan script

---

## 9. Eight-bullet summary (orchestrator return)

1. **Apples-to-apples methodology spec headline**: All three claims re-tested on the
   IDENTICAL 15 CPCV folds (K=6, N=2, purge=7d, embargo=1d, fold composition VERIFIED
   identical via `test_idx` exact-match across v3, ArchA, canonical-v1 jobs). Per-path mean
   AUC (NOT pool-aggregation) is the primary aggregator. Canonical v1 (17 features, NO
   `symbol`, mean OOS AUC 0.5286) is the baseline (NOT the modeler-modified v1 0.5133).

2. **K54 v3 paired delta** = **+0.0484** (paired t p=0.0082, Wilcoxon p=0.0103, bootstrap
   p_one=0.0000, 12/15 paths positive). **SURVIVES the +0.04 threshold.** DSR survives at
   T=20 + n=2,326 + N=200 (DSR-p=0.0088), confirming Agent E's Phase 2 minimum projection.
   K54 v3's lift was already audited against canonical baseline by the v3 dispatch — the
   number survives K1 verification at the 4th decimal place.

3. **Arch A paired delta** = **+0.0339** (paired t p=0.147 FAILS, Wilcoxon p=0.151,
   bootstrap p_one=0.0028 directionally positive only). **COMPRESSES below the +0.04
   threshold.** Original +0.0492 was inflated by +0.0166 baseline-mismatch (modeler-modified
   v1 with `symbol` is 0.0166 weaker than canonical v1). **The Q1.3 audit's "Arch A passes
   gate (a)" verdict is INVALIDATED** under the canonical baseline.

4. **T7 NAS_US30 paired delta** = **-0.007** (Agent C K=4/N=2 paired proxy on NAS specialist
   vs global, t-p=0.93, DSR-p=0.999, sr=-0.0495). **FAILS** the +0.05 threshold. Agent I's
   unpaired +0.111 cannot be apples-to-apples confirmed because T7's K=6 NAS-only folds
   differ from K54 v3's K=6 full-cohort folds. Honest range is [-0.007, +0.111] depending
   on whether per-cohort feature screening rescues the paired delta — needs a fold-aligned
   T7 re-train to resolve.

5. **Phase 2 K54 v4 readiness verdict: BORDERLINE.** K54 v3 lift survives at +0.04 alone,
   but Arch A compresses to +0.034 (below threshold). The "both surviving" criterion for
   APPROVED fails. Recommended sequencing: (a) DEFER K54 v4 dispatch; (b) Phase 2 first
   wave = position-management discoveries (Agent F top-3); (c) plan corrected K54 v4
   architecture search using canonical v1 baseline + ALL three architectures (v3, Arch A,
   per-cohort) on the SAME folds.

6. **New ambiguities**: (a) The +0.0166 modeler-vs-canonical baseline-mismatch is a
   program-wide pattern; all K54-family lift claims should be re-tested under canonical
   baseline. (b) Agent C K=4 paired vs Agent I K=6 unpaired on NAS_US30 specialist gives
   contradictory deltas (-0.007 vs +0.111); K1 cannot resolve without retrained T7 on
   K54 v3's exact 15 folds. (c) Agent E's projection cohort scaling assumption (lift held
   constant at +0.0484 as cohort scales 528 → 2,326) is itself untested under cohort
   expansion — that confirmation depends on the Phase 2 backfill.

7. **Recommended follow-up dispatches** (priority order):
   - **Spawn fold-aligned T7 re-train**: retrain Agent I T7 NAS_US30 specialist on the
     SAME 15 K=6/N=2 full-cohort CPCV folds as K54 v3, save per-row predictions, compute
     paired delta vs K54 v3 global on NAS_US30 mask. This resolves the -0.007 vs +0.111
     contradiction. ~1 hour subscription-only.
   - **Spawn baseline-mismatch sweep**: re-test all Q1.3 Arch B per-group lifts and all
     K54 v3 component-ablation deltas under canonical v1 baseline. Same paired methodology.
     ~1-2 hours subscription-only.
   - **Phase 2 architecture re-search dispatch**: with the corrected baseline numbers,
     re-rank Arch A vs Arch B vs K54 v3 master bundle vs T7 per-cohort under a single
     fold-aligned protocol. ~3-4 hours subscription-only.

8. **Key file paths**:
   - `research/ml_program/forensics/2026-04-29/agent_k1_apples_apples_verification.md` (this synthesis)
   - `research/ml_program/forensics/2026-04-29/agent_k1_methodology_spec.md` (locked protocol)
   - `research/ml_program/forensics/2026-04-29/agent_k1_paired_results.json` (numerical detail)
   - `research/ml_program/forensics/2026-04-29/agent_k1_decision_matrix.csv` (readable table)
   - `research/ml_program/forensics/2026-04-29/agent_k1_dsr_aligned_scan.json` (Agent-E-aligned DSR scan)
   - `research/ml_program/forensics/2026-04-29/_agent_k1_verify.py` (reproducer)
   - `research/ml_program/forensics/2026-04-29/_agent_k1_dsr_align.py` (Agent E framing alignment)

---

*End. K1 dispatch complete. READ-ONLY on production. No model artifacts modified. The
existing K54 v3 + Arch A + T7 results files remain on disk; this dispatch supersedes their
INTERPRETATION via apples-to-apples paired methodology.*
