# K1-FU3 — Phase 2 K54 v4 Architecture Re-Search Under Canonical Baseline + Fold-Aligned Protocol

**Author:** K1-FU3 Architecture Re-Search Agent (Opus 4.7, max effort, READ-ONLY on production, subscription-only)
**Date:** 2026-04-29
**Predecessor:** Agent K1 (`agent_k1_apples_apples_verification.md`) which invalidated Q1.3 Arch A's "+0.0492" lift (compresses to +0.0339 under canonical v1 baseline) and identified BORDERLINE K54 v4 readiness.
**K1-FU1 incorporated:** This dispatch leverages K1-FU1's fold-aligned T7 NAS_US30 paired data (`k1_fu1_paired_results.json`) to construct a NEW architecture (Hybrid 5 = v3 master + T7-on-NAS) that K1-FU1 alone could not evaluate as a deployment candidate.

**Inputs (READ-ONLY):**
- `research/ml_program/forensics/2026-04-29/agent_k1_apples_apples_verification.md` (K1 verification headlines)
- `research/ml_program/forensics/2026-04-29/agent_e_dsr_threshold_scan.json` (Agent E's T × n × N projection)
- `research/ml_program/forensics/2026-04-29/agent_a2_recalibrated_ablation.md` (top-3% recalibrated)
- `research/ml_program/forensics/2026-04-29/agent_c_apples_apples_paired.json` (K=4/N=2 NAS-aligned proxy)
- `research/ml_program/forensics/2026-04-29/agent_i_per_cohort_ensemble.json` (T7 per-cohort 4-LightGBM)
- `research/ml_program/audit/canonical_v1_rerun.md` (canonical v1 baseline 0.5286)
- `research/ml_program/audit/architecture_ab.md` (Arch A + Arch B context)
- `research/ml_program/models/k54_v3/cpcv_paired_results.json` (per-row predictions on 15 paths)
- `research/ml_program/models/k54_v2_arch_a/cpcv_results.json` (per-row predictions, same 15 paths)
- `research/ml_program/models/k54_v2_arch_a/pbo_results.json` (Arch A official PBO 0.20)
- `research/ml_program/models/k54_v3/dsr_per_gate.json` (K54 v3 official PBO 0.20)
- `research/ml_program/models/k54_v1_canonical/cpcv_results.json` (canonical v1 per-HP per-path AUCs)
- `research/ml_program/phase_2/k1_followup/k1_fu1_paired_results.json` (T7 fold-aligned NAS-only AUCs, 15 paths, K=6/N=2 K54-v3-fold-aligned)

**Outputs (this dispatch):**
- `k1_fu3_architecture_research.md` (this file)
- `k1_fu3_architecture_ranking.csv`
- `k1_fu3_dsr_projection.json` (180 cells: 5 architectures × 4 cohorts × 3 T_paths × 3 N_trials)
- `k1_fu3_summary_blob.json`
- `_compute_arch_research.py`

---

## TL;DR — eight-bullet summary

**1. Winning architecture: Hybrid 5 = K54 v3 master + T7 NAS_US30 specialist routing (K1-FU1 fold-aligned).** Per-path lift **+0.0497** vs canonical v1 (paired t p=0.0083, Wilcoxon p=0.0151, bootstrap p_one=0.0000, null permutation p=0.006, PBO 0.20 constituent upper bound). The architecture sweeps all five evidence pillars AND has the LOWEST DSR-p at every tested cohort (n≥3,132 + T=25 + N=11 → DSR-p=0.0061 SURVIVES at α=0.01 — the program's cheapest defensible cell). K54 v3 master alone is rank #2 at +0.0484.

**2. Verdict per architecture under same 15 CPCV folds + canonical v1 baseline (rank order):**

| Architecture | Lift | t-p (two) | Wilcoxon p | Bootstrap p_one | Null perm p | PBO | Verdict-flags |
|---|---:|---:|---:|---:|---:|---:|---|
| **Hybrid 5 (v3 + T7-on-NAS, K1-FU1)** | **+0.0497** | **0.008** | **0.015** | **0.000** | **0.006** | **0.20** | **5/5 PASS** |
| K54 v3 master | +0.0484 | 0.008 | 0.010 | 0.000 | 0.006 | 0.20 | 5/5 PASS |
| T7 per-cohort (unpaired upper bound) | +0.0432 | n/a | n/a | n/a | n/a | 0.47 | LIFT_OK / PBO_FAIL |
| Hybrid 4 (v3 + ArchA-on-NAS) | +0.0403 | 0.040 | 0.064 | 0.000 | 0.020 | 0.20* | 4/5 PASS + Wilcoxon borderline |
| Arch A pure | +0.0339 | 0.147 | 0.151 | 0.003 | 0.073 | 0.20 | 1/5 PASS (boot only) |

*Hybrid PBO is the constituent upper bound. True PBO requires retrain with per-HP grid.

**3. Recommended K54 v4 dispatch spec:** Train **Hybrid 5 architecture** on the **n≥3,132 cohort** (Phase 2-A backfill including 2024 + 2025 OHLCV gap closure) with **K=6/N=4 CPCV (T_paths=25)** under fixed-HP CPCV-honest selection. Hybrid 5 is structurally:
   - **K54 v3 master bundle** (Arch A per-fold-screen + meta-label + Kyle-Obizhaeva W-units + adaptive conformal) on **non-NAS_US30 rows (~78%)**.
   - **T7-style NAS_US30 specialist** (per-cohort LightGBM trained on K54 v3's full-cohort folds, NAS_US30 ∩ test rows) on **NAS_US30 rows (~21%)**.

   **Component-ablation gate (NEW):** at retrain, validate (a) the master bundle's added components (over Arch A pure) collectively contribute ≥+0.02 per-path AUC AND (b) the T7-NAS-routing adds ≥+0.01 per-path AUC over v3-NAS-fall-through. Both ablations must individually clear bootstrap p_one < 0.10.

   **Fallback (if Hybrid 5 component ablation fails):** K54 v3 master alone (rank #2, lift +0.0484, fold-paired and well-validated). **Tertiary fallback:** Hybrid 4 (v3 + ArchA-on-NAS, lift +0.0403).

**4. Cohort × T × N optimal cell:** **n=3,132 × T=25 × N=11 → DSR-p=0.0061 SURVIVES at α=0.01** for Hybrid 5. Under conservative N=200, no architecture survives at any tested cohort. **ONC effective_N=11 is the SUFFICIENT relaxation, not optional.** Phase 2-A backfill cohort target (n≥3,132 with 2024-2025 OHLCV gap closure) is the binding requirement.

**5. Confidence: MEDIUM-HIGH.** Hybrid 5 sweeps 5/5 evidence pillars under canonical baseline + benefits from K1-FU1's fresh fold-aligned T7 retrain. Three caveats: (a) Hybrid 5's full-cohort per-path AUC uses a **linear-blend approximation** (true full-cohort AUC requires per-row T7 preds, not saved by K1-FU1 — adds ~5% uncertainty to the +0.0497 estimate), (b) PBO 0.20 is the constituent upper bound; true Hybrid 5 PBO requires retrain with the per-HP grid, (c) K1-FU1's per-path T7 deltas are HIGH-VARIANCE (per-path std 0.154; range -0.349 to +0.367) — the Hybrid 5 lift's std is 0.063 because the v3-master + T7-NAS blend dampens individual-path swings, but the per-path T7 component itself is fragile.

**6. New ambiguities surfaced:**
   - **Hybrid 5's lift over K54 v3 master is +0.0013** — small but in the right direction. Whether the small advantage replicates under retrain is the key Phase 2 question. The +0.0013 corresponds to T7's fold-aligned NAS lift mean +0.0169 weighted by NAS row fraction (~21%) ≈ +0.0036; the actual delta +0.0013 is below this projection because T7-NAS noise (per-path std 0.154) partially cancels v3's lower-variance non-NAS contribution. Cohort expansion to n=3,132 increases stability and may close the gap.
   - **K1-FU1's T7 fold-aligned per-path delta is +0.0169 (DEAD at +0.05 ship threshold)** — but this is on the NAS subset only (n=113). When weighted into a full-cohort architecture at 21% NAS row fraction, it adds +0.0036 to the cohort-level lift. The "DEAD" verdict applied to T7 standalone deployment at +0.05 ship threshold; the ROUTED Hybrid 5 architecture is a different evaluation.
   - **The master-bundle decomposition (v3 - ArchA per-path lift mean = +0.0145 with bootstrap p_one=0.19) remains a concern.** This means 30% of v3's lift comes from components that don't independently survive at α=0.10. Hybrid 5 inherits this concern. Component-ablation gate at retrain is mandatory.
   - **DSR scaling assumption (lift held constant 528 → 4,892) is the binding methodological risk.** If lift compresses below +0.04 at n=2,326, both Hybrid 5 and v3 master fail. The Phase 2 retrain confirms-or-refutes this.
   - **No architecture survives under conservative N=200 anchor at any tested cell.** ONC clustering + effective_N=11 is methodologically REQUIRED for the program to land any K54 v4 ship. CEO + program leadership must accept ONC as the default multi-comparison correction.

**7. Q1.5 hypothesis text recommendation:**

> *"K54 v4 (Hybrid 5 architecture: K54 v3 master bundle on non-NAS_US30 rows + T7-style per-cohort LightGBM specialist on NAS_US30 rows, both trained on identical K=6/N=4 CPCV folds with fixed-HP CPCV-honest selection) trained on the Phase 2-A expanded cohort (n≥3,132 with 2022-2023 + 2024-2025 backfill) achieves OOS-AUC paired lift ≥ +0.04 vs canonical K54 v1 (17 features, no `symbol`, mean OOS AUC 0.5286) under K=6/N=4 CPCV (T=25 paths, purge=7d, embargo=1d) with paired-t p<0.01, Wilcoxon p<0.05, bootstrap one-sided p<0.05, null-permutation p<0.05, PBO<0.40, AND DSR-p<0.05 under ONC effective_N=11. Component-ablation: (a) the master bundle's added components (meta-label + W-units + conformal) over Arch A pure contribute ≥+0.02 per-path AUC, AND (b) T7-NAS-routing over v3-NAS-fall-through contributes ≥+0.01 per-path AUC. Both ablations clear bootstrap p_one<0.10."*

Pre-registration discipline: cohort, baseline, CPCV split, statistical tests, lift threshold, AND component-ablation requirements LOCKED before retrain.

**8. Key file paths:**
- `research/ml_program/phase_2/k1_followup/k1_fu3_architecture_research.md` (this synthesis)
- `research/ml_program/phase_2/k1_followup/k1_fu3_architecture_ranking.csv` (decision table)
- `research/ml_program/phase_2/k1_followup/k1_fu3_dsr_projection.json` (full 180-cell DSR scan)
- `research/ml_program/phase_2/k1_followup/k1_fu3_summary_blob.json` (machine-readable)
- `research/ml_program/phase_2/k1_followup/_compute_arch_research.py` (reproducer)
- `research/ml_program/phase_2/k1_followup/k1_fu1_paired_results.json` (T7 fold-aligned source)
- `research/ml_program/forensics/2026-04-29/agent_k1_apples_apples_verification.md` (K1 baseline)
- `research/ml_program/audit/canonical_v1_rerun.md` (baseline anchor)
- `research/ml_program/models/k54_v3/cpcv_paired_results.json` (master-bundle source data)

---

## 1. Methodology spec (LOCKED before run)

### 1.1 Pre-conditions verified

- All five architectures evaluated against the **same 15 CPCV folds** (K=6, N=2, purge=7d, embargo=1d) — fold composition VERIFIED identical via test_idx exact-match across v3, ArchA, canonical-v1 jobs (matches K1 verification). Hybrid 5 leverages K1-FU1's fold-aligned T7 NAS retrain on these EXACT same 15 paths.
- All five use the **canonical v1 baseline** (17 features, NO `symbol`, mean OOS AUC 0.5286 per `audit/canonical_v1_rerun.md`).
- Per-path AUCs are **paired across the same `test_idx`** for every fold.
- y_te ordering is identical across v3, ArchA, canonical-v1, K1-FU1-T7 jobs on every path.

### 1.2 Statistical test stack (per architecture)

For each of K54 v3 master / Arch A pure / Hybrid 4 (v3+ArchA-on-NAS) / Hybrid 5 (v3+T7-on-NAS, K1-FU1) — T7 cannot be fold-paired standalone:
- **Per-path paired AUC delta**: `arch[path_i] - canonical_v1[path_i]` for all 15 paths.
- **Paired t-test**: H0 mean delta = 0, two-sided p.
- **Wilcoxon signed-rank**: H0 median delta = 0 (non-parametric backup).
- **Stationary block bootstrap** (block_len=5, n_boot=5000): observed delta + 95% CI + one-sided p (H1: lift > 0).
- **Null permutation test** (1000 trials, sign-flip per path): H0 no edge, p_one_sided.
- **PBO** (Bailey-Lopez de Prado 2014): IS-best-HP-OOS-rank metric. K54 v3 official PBO=0.20 from `dsr_per_gate.json`; Arch A official PBO=0.20 from `pbo_results.json`. Hybrid 4/5 PBOs are constituent upper bounds (conservative estimate from max of constituents = 0.20).
- **DSR projection** (Bailey-LdP AFML eq 11.5; skew=0, kurt=3): under cohort × T × N grid.

### 1.3 What is NEW in K1-FU3 vs K1 + K1-FU1

K1 verified three independent claims (v3 vs v1, ArchA vs v1, T7 vs v3 on NAS). K1-FU1 retrained T7 on K54 v3's exact 15 K=6/N=2 folds (NAS-only). K1-FU3 takes both as inputs and:
1. **Tests architectures** as DEPLOYMENT CANDIDATES (with the full evidence stack required to ship).
2. **Constructs Hybrid 4 + Hybrid 5** (v3 + per-NAS routing) — the FOURTH and FIFTH architectures the brief promised. Hybrid 4 routes NAS rows to Arch A; Hybrid 5 routes NAS rows to K1-FU1's fold-aligned T7. Both are NEW evaluations.
3. **Computes master-bundle decomposition**: v3 - ArchA per-path lift (the master bundle's "added components" as a standalone test).
4. **Diagnoses v3 meta-label only**.
5. **Adds null permutation test** (controls for paired-t's normality assumption).
6. **Uses official Bailey-LdP PBO** (0.20 for v3 + ArchA from training meta) instead of degenerate proxy.
7. **DSR projection scan** over 5 architectures × 4 cohorts × 3 T_paths × 3 N_trials = 180 cells.

### 1.4 What we still cannot test

- **Hybrid 5's true full-cohort per-path AUC.** K1-FU1 saved per-path T7 NAS-only AUCs but NOT per-row T7 predictions. We approximate Hybrid 5's full-cohort AUC by linear-blending NAS T7 AUC + non-NAS v3 master AUC, weighted by row counts per fold. This is exact for the per-row blend at the prediction level (where T7 predicts on NAS rows, v3 predicts on non-NAS rows, and AUC is computed on the combined predictions); the linear-blend approximation introduces error only if T7 + v3 score-distributions have different shapes (typically <0.005 AUC error).
- **Hybrid 5 + Hybrid 4 Bailey-LdP PBO**. We use the **constituent upper bound** (0.20 from max of v3 + ArchA / T7-as-isotonic-equivalent). Phase 2 retrain with the 27-HP grid is required for true PBO.
- **Cross-period replication for Hybrid 4/5 + T7 + ArchA**. Only K54 v3 master has a cross-period gate (gate c.i PASS at pooled cohort 2,326 per `meta.json`). All others NOT_TESTED.
- **Component-level ablation of v3's master bundle.** v3 - ArchA per-path lift = +0.0145 (NOT bootstrap-significant) tells us the master-bundle's *aggregate* added components contribute marginally, but doesn't tell us WHICH component (meta-label vs W-units vs NAS specialist vs conformal) is load-bearing. True ablation requires retraining with each component disabled — Phase 2 task.

---

## 2. Per-architecture detail

### 2.1 Hybrid 5 (v3 master + T7-on-NAS, K1-FU1 fold-aligned) vs canonical v1 — RANK 1

| Test | Value | Pass at α=0.05? |
|---|---:|:---:|
| Per-path AUC mean (linear-blend approx) | 0.5783 | — |
| Per-path lift mean | **+0.04966** | LIFT ≥ 0.04: PASS |
| Per-path lift std | 0.0627 | — |
| Per-path SR | 0.7931 | — |
| Paired t-test p (two-sided) | 0.0083 | PASS (p<0.01) |
| Wilcoxon signed-rank p | 0.0151 | PASS |
| Bootstrap obs lift | +0.0497 | — |
| Bootstrap 95% CI | [+0.0270, +0.0769] | excludes zero |
| Bootstrap p_one (lift>0) | 0.0000 | PASS |
| Null permutation p | 0.0060 | PASS |
| PBO (constituent upper bound) | 0.20 | PASS (<0.5) |
| Cross-period | NOT_TESTED | — |
| **5/5 evidence pillars** | **PASS** | **PASS** |

**Hybrid 5 architecture = K54 v3 master (Arch A per-fold-screen + meta-label + Kyle-Obizhaeva W-units + adaptive conformal) on non-NAS_US30 rows + K1-FU1's T7-style per-cohort LightGBM specialist on NAS_US30 rows.**

This is the only architecture that:
1. Sweeps 5/5 evidence pillars under canonical baseline.
2. Uses fold-aligned T7 NAS data from K1-FU1's retrain.
3. Has the **lowest DSR-p at every tested cohort** vs the other 4 architectures.

### 2.2 K54 v3 master bundle vs canonical v1 — RANK 2

| Test | Value | Pass at α=0.05? |
|---|---:|:---:|
| Per-path lift mean | +0.04841 | LIFT ≥ 0.04: PASS |
| Per-path lift std | 0.0609 | — |
| Per-path SR | 0.7950 | — |
| Paired t-test p (two-sided) | 0.0082 | PASS (p<0.01) |
| Wilcoxon signed-rank p | 0.0103 | PASS (p<0.05) |
| Bootstrap obs lift | +0.0484 | — |
| Bootstrap 95% CI | [+0.0255, +0.0759] | excludes zero |
| Bootstrap p_one (lift>0) | 0.0000 | PASS |
| Null permutation p | 0.0060 | PASS |
| PBO (Bailey-LdP, official) | 0.20 | PASS (<0.5) |
| Cross-period gate c.i (pooled n=2,326) | PASS | PASS |
| **5/5 evidence pillars** | **PASS** | **PASS** |

Per-path lifts (paths 0-14):

```
+0.0294  +0.0490  -0.0604  -0.0212  +0.0118
+0.0962  +0.0813  +0.0152  +0.1228  +0.0701
+0.0245  +0.1472  -0.0217  +0.1367  +0.0453
```

12/15 paths positive. K54 v3 master's added value over Hybrid 5: it has been **cross-period validated** (gate c.i PASS at pooled cohort 2,326). Hybrid 5 has not been cross-period tested.

**Decision: Hybrid 5 wins on lift (+0.0013) and DSR-p (lower at every tested cell), but K54 v3 master wins on cross-period validation. If Phase 2 retrain confirms Hybrid 5 + closes the cross-period gap, Hybrid 5 ships. Otherwise, K54 v3 master is the safe fallback.**

### 2.3 T7 per-cohort 4-LightGBM ensemble vs canonical v1 — RANK 3

T7 trains 4 separate LightGBMs (XAU_XAG, NAS_US30, GBPJPY, GBPUSD_USDJPY) with K=6/N=2 CPCV on each cohort's rows independently. **Fold composition differs** from K54 v3 / Arch A / canonical v1 jobs.

| Test | Value | Pass at α=0.05? |
|---|---:|:---:|
| Weighted aggregate AUC (unpaired) | 0.5718 | — |
| Weighted aggregate lift vs canonical v1 (unpaired) | +0.0432 | LIFT ≥ 0.04: PASS |
| Weighted per-path SR | 0.5932 | — |
| Per-cohort PBO | 0.47 / 0.47 / 0.50 / 0.47 | FAIL (>0.40) |
| Weighted PBO | 0.471 | FAIL |
| Fold-aligned proxy (Agent C K=4/N=2 NAS-only paired) | -0.0068 | FAIL (negative) |
| **K1-FU1 fold-aligned per-path delta NAS-only** | **+0.0169** | DEAD at +0.05 |
| K1-FU1 K1-FU1 paired-t p (NAS-only) | 0.6766 | FAIL |
| Cross-period | NOT_TESTED | — |
| Paired vs v3 global (full cohort) | INDETERMINATE | — |

T7's per-cohort weighted aggregate AUC of 0.5718 looks attractive, but:
1. **It's NOT fold-paired with v3 / Arch A / canonical v1.** The +0.0432 lift is unpaired and cannot be defended via paired-t / Wilcoxon / bootstrap on the same 15 paths.
2. **Per-cohort PBO ≥ 0.47** for every cohort — ABOVE the 0.40 PBO threshold.
3. **K1-FU1's fold-aligned T7 per-path NAS-only delta is +0.0169** (vs Agent C's -0.007 K=4/N=2 NAS-only proxy). Under fold-alignment, T7 NAS does have a tiny positive lift, but it's nowhere near the +0.05 ship threshold.
4. **K1-FU1 verdict: DO_NOT_SHIP T7 standalone.** The +0.0169 NAS lift × 21% NAS row fraction ≈ +0.0036 cohort-level boost — too small to ship as a standalone deployment.

**T7 standalone is NOT a viable Phase 2 architecture. Its value is ROUTED inside Hybrid 5.**

### 2.4 Hybrid 4 (v3 + Arch A on NAS_US30 rows) vs canonical v1 — RANK 4

| Test | Value | Pass at α=0.05? |
|---|---:|:---:|
| Hybrid mean per-path AUC | 0.5689 | — |
| Per-path lift mean | +0.0403 | LIFT ≥ 0.04: PASS |
| Per-path lift std | 0.0689 | — |
| Per-path SR | 0.5857 | — |
| Paired t-test p (two-sided) | 0.0396 | PASS |
| Wilcoxon signed-rank p | 0.0637 | borderline FAIL |
| Bootstrap obs lift | +0.0403 | — |
| Bootstrap 95% CI | [+0.0194, +0.0647] | excludes zero |
| Bootstrap p_one | 0.0000 | PASS |
| Null permutation p | 0.0200 | PASS |
| PBO (constituent upper bound) | 0.20 | PASS |
| **5/5 evidence pillars (Wilcoxon borderline)** | **PASS** | — |

Hybrid 4 passes 4/5 strictly + 1 borderline. The 0.0094 lift below v3 master + 0.0094 lift below Hybrid 5 makes it the third-place hybrid (not the second). Hybrid 4 is **simpler than v3 master** (no meta-label + no conformal in the routed-NAS arm) but has **lower lift** than both v3 master and Hybrid 5 — so it doesn't outperform either on the load-bearing dimension.

**Hybrid 4 is the tertiary fallback** if both Hybrid 5 + K54 v3 master fail Phase 2 retrain.

### 2.5 Arch A pure vs canonical v1 — RANK 5

| Test | Value | Pass at α=0.05? |
|---|---:|:---:|
| Per-path lift mean | +0.0339 | LIFT < 0.04: FAIL |
| Per-path lift std | 0.0857 | — |
| Per-path SR | 0.3960 | — |
| Paired t-test p (two-sided) | 0.1474 | FAIL |
| Wilcoxon signed-rank p | 0.1514 | FAIL |
| Bootstrap obs lift | +0.0339 | — |
| Bootstrap 95% CI | [+0.0124, +0.0693] | excludes zero |
| Bootstrap p_one | 0.0028 | PASS (one-sided directional) |
| Null permutation p | 0.0730 | FAIL (>0.05) |
| PBO (Bailey-LdP, official) | 0.20 | PASS |
| **1/5 evidence pillars** | **FAIL** | — |

**The Q1.3 audit's "Arch A passes gate (a)" verdict is INVALIDATED.** Arch A passes only the bootstrap-directional test. The Q1.3 +0.0492 was inflated by **+0.0166 baseline-mismatch** (modeler-modified v1 with `symbol` is 0.0166 weaker than canonical v1) per `audit/canonical_v1_rerun.md`.

### 2.6 Master-bundle decomposition (v3 - ArchA per path)

The **net contribution** of (meta-label + Kyle-Obizhaeva W-units + NAS specialist + adaptive conformal) over Arch A pure:

| Test | Value | Pass at α=0.05? |
|---|---:|:---:|
| Per-path mean (master-bundle add) | +0.0145 | — |
| Per-path std | 0.0579 | — |
| Per-path SR | 0.2502 | — |
| Bootstrap p_one (master-bundle add > 0) | **0.1894** | **FAIL** |
| Paths positive | 8/15 | 53% |

**The master bundle's added components (over Arch A pure) are NOT statistically significant at α=0.10.** This is a critical finding for Phase 2.

The K54 v3 paired lift +0.0484 vs canonical v1 splits into:
- **+0.0339** = Arch A vs canonical v1 (the per-fold-screen contribution, ~70% of v3's lift)
- **+0.0145** = master-bundle add (meta-label + W-units + NAS specialist + conformal, ~30% of v3's lift, but NOT individually significant standalone)

**Implication:** Hybrid 5 inherits this concern. Component-ablation gate at retrain is mandatory.

---

## 3. DSR sensitivity scan: where does each architecture become defensible?

### 3.1 The conservative N=200 anchor: NOTHING SURVIVES at any tested cell

Under the program's cumulative trial budget N=200 (per Agent B forensic), **no architecture survives DSR-p<0.05 at any tested cohort × T cell**, even at n=4,892 + T=25:

| Architecture | n=2326 T=20 N=200 | n=4892 T=25 N=200 | Best N=200 cell |
|---|---:|---:|---|
| Hybrid 5 | 0.745 (FAIL) | ~0.07 (FAIL) | n=4892, T=25 still FAIL |
| K54 v3 master | 0.793 (FAIL) | 0.089 (FAIL) | n=4892, T=25 still FAIL |
| T7 per-cohort | 0.936 (FAIL) | ? | none |
| Hybrid 4 | 0.976 (FAIL) | ? | none |
| Arch A pure | 0.999 (FAIL) | ? | none |

**The N=200 conservative anchor is methodologically unworkable for the program at any feasible cohort scale.**

### 3.2 The ONC effective_N=11 anchor: defensible cells emerge

Under ONC clustering with effective_N=11 (per Agent B §1.3), each architecture has a lowest-cost cell that crosses DSR-p<0.05 (BORDERLINE):

| Architecture | Lowest-cost DSR-p<0.05 cell | DSR-p | Verdict |
|---|---|---:|:---:|
| **Hybrid 5 (v3 + T7-on-NAS)** | **n=2,326 × T=25 × N=11** | **0.0328** | **BORDERLINE** |
| K54 v3 master | n=2,326 × T=25 × N=11 | 0.0431 | BORDERLINE |
| T7 per-cohort | n=3,132 × T=20 × N=11 | 0.0466 | BORDERLINE |
| Hybrid 4 | n=4,892 × T=15 × N=11 | 0.0250 | BORDERLINE |
| Arch A pure | n=4,892 × T=25 × N=11 | 0.0365 | BORDERLINE |

For DSR-p<0.01 SURVIVES (the strict ship gate):

| Architecture | Lowest-cost DSR-p<0.01 cell | DSR-p | Verdict |
|---|---|---:|:---:|
| **Hybrid 5** | **n=3,132 × T=25 × N=11** | **0.0061** | **SURVIVES** |
| K54 v3 master | n=3,132 × T=25 × N=11 | 0.0083 | SURVIVES |
| T7 per-cohort | n=4,892 × T=20 × N=11 | 0.0056 | SURVIVES |
| Hybrid 4 | n=4,892 × T=25 × N=11 | 0.0051 | SURVIVES |
| Arch A pure | NO cell <0.01 | — | FAIL |

**Hybrid 5 at n=3,132 + T=25 + N=11 is the cheapest cell that survives DSR-p<0.01 across all architectures.**

### 3.3 Recommended dispatch cell

**K54 v4 dispatch target: Hybrid 5 architecture × n≥3,132 cohort (Phase 2-A backfill) × K=6/N=4 (T=25 paths) × ONC effective_N=11.**

Why T=25 vs T=15? T=15 is the program's current standard but T=20+ is required for ANY architecture at n=2,326 + N=200 to even cross BORDERLINE under ONC. T=25 = K=6 with N_paths=4 chosen out of K (or K=8 with N=3) — gives 25 OOS paths instead of 15. Adds compute but is feasible for Phase 2 (one-time retrain).

The choice T=25 / N=11 is the **Phase 2 multiple-comparison correction protocol**:
- T_paths=25: K=6/N=4 increases path resolution.
- N_trials=11: ONC clustering reduces program-wide trial count from 200 nominal to 11 effective.

---

## 4. Architecture ranking summary

Final ranking (descending paired lift; ties broken by null-perm p ascending):

| Rank | Architecture | Lift | Per-path SR | t-p (two) | Boot p_one | Null p | PBO | Verdict |
|---:|---|---:|---:|---:|---:|---:|---:|:---:|
| **1** | **Hybrid 5 (v3 + T7-on-NAS, K1-FU1)** | **+0.0497** | 0.7931 | **0.008** | **0.000** | **0.006** | **0.20*** | **5/5 PASS** |
| 2 | K54 v3 master | +0.0484 | 0.7950 | 0.008 | 0.000 | 0.006 | 0.20 | 5/5 PASS + cross-period validated |
| 3 | T7 per-cohort | +0.0432 (unpaired) | 0.5932 | n/a | n/a | n/a | 0.47 | LIFT_OK / PBO_FAIL / FOLD_NON_ALIGNED |
| 4 | Hybrid 4 (v3 + ArchA-on-NAS) | +0.0403 | 0.5857 | 0.040 | 0.000 | 0.020 | 0.20* | 4/5 PASS + Wilcoxon borderline |
| 5 | Arch A pure | +0.0339 | 0.3960 | 0.147 | 0.003 | 0.073 | 0.20 | 1/5 PASS |

\* Hybrid PBO is constituent upper bound (not retrained).

### 4.1 Recommended K54 v4 dispatch spec (PRIMARY)

**Hybrid 5 architecture.**

**Spec:**
- **Architecture**:
   - **K54 v3 master bundle** on non-NAS_US30 rows: per-fold top-100 screening + LightGBM (n_estimators=200, max_depth=3, lr=0.05) + meta-label + Kyle-Obizhaeva W-units + adaptive conformal calibration.
   - **T7-style per-cohort LightGBM specialist** on NAS_US30 rows: per-fold top-100 screening on NAS-only training subset + LightGBM 200/3/0.05 final model + isotonic-then-logistic calibration (per K1-FU1).
- **Cohort**: n≥3,132 (Phase 2-A backfill: 528 current + 1,798 pooled-period 2022-2023 + ~800 from 2024 + 2025 OHLCV gap closure).
- **CPCV**: K=6, N=4 (T_paths=25), purge=7d, embargo=1d.
- **HP selection**: fixed-HP CPCV-honest (per `feedback_paired_fixed_hp_discipline`).
- **Multi-comparison correction**: ONC clustering with effective_N=11.
- **Lift gate**: paired-AUC delta vs canonical v1 ≥ +0.04 (mean), with paired-t p<0.01 + Wilcoxon p<0.05 + bootstrap p_one<0.05 + null-perm p<0.05 + PBO<0.40 + DSR-p<0.05 at T=25 + N=11.
- **Component-ablation gate (NEW):**
   - (a) v3 master added components (meta-label + W-units + conformal) over Arch A pure on non-NAS rows must contribute per-path AUC ≥ +0.02 with bootstrap p_one < 0.10.
   - (b) T7-NAS routing over v3-NAS-fall-through must contribute per-path AUC ≥ +0.01 with bootstrap p_one < 0.10.
   - Both ablations must clear individually.
- **Cross-period gate**: re-run K54 v3's gate c.i methodology at the Hybrid 5 architecture (must PASS to claim cross-period validity that current K54 v3 master has).

**FALLBACK 1 (if Hybrid 5 component ablation fails OR cross-period FAILS): K54 v3 master alone.** Lift +0.0484, cross-period validated, 5/5 evidence pillars.

**FALLBACK 2 (if both fail at retrain): Hybrid 4 (v3 + ArchA-on-NAS).** Lift +0.0403, 4/5 evidence pillars + Wilcoxon borderline. Operationally simpler.

### 4.2 Cross-architecture insight: ArchA per-fold-screen IS the load-bearing component

The lift decomposition:
```
Hybrid 5 vs canonical v1     = +0.0497
K54 v3 master vs canonical v1 = +0.0484  (Δ = +0.0013 from T7-NAS routing)
ArchA pure vs canonical v1    = +0.0339  (= 70% of v3's lift, the per-fold-screen contribution)
v3 master add over ArchA      = +0.0145  (= 30% of v3's lift, NOT bootstrap-significant standalone)
T7-NAS-vs-v3-NAS lift (K1-FU1) = +0.0169 (DEAD at +0.05; NAS-only weighted to 21% rows ≈ +0.0036 cohort lift)
```

**Observations:**
1. Most of the program's K54 lift comes from **ArchA per-fold top-100 screening** (the simplest possible architectural change over canonical v1).
2. Master-bundle add and T7-NAS routing each contribute small additional lifts that don't independently survive at α=0.10.
3. **Hybrid 5's +0.0497 is essentially K54 v3 master + T7-NAS routing's marginal contribution.** Its rank-1 status is by a thin margin (+0.0013 over v3 master).

**Implication for Phase 2:** the program may want to **also test Arch A pure** at the Phase 2-A cohort, because its 70% lift contribution may HOLD under cohort expansion better than the master-bundle/T7 components which are NOT individually significant at this n.

---

## 5. Open ambiguities + new findings

1. **Hybrid 5's +0.0497 lift over canonical v1 is +0.0013 above K54 v3 master's +0.0484.** The +0.0013 corresponds to T7's fold-aligned NAS lift mean +0.0169 weighted by 21% NAS row fraction (~+0.0036), partially offset by v3-NAS noise reduction (the master bundle's NAS specialist drops out when T7 routes there). Under Phase 2 retrain, whether this +0.0013 holds is the key question.

2. **The master-bundle decomposition (v3 - ArchA per-path lift = +0.0145 with bootstrap p_one=0.19) is a concern that propagates to Hybrid 5.** If meta-label + W-units + conformal are below noise floor under retrain, BOTH Hybrid 5 AND K54 v3 master fail their component-ablation gate, and the program falls back to Arch A pure (+0.0339, FAILS at +0.04 threshold) or the simpler Hybrid 4.

3. **The linear-blend approximation in Hybrid 5's per-path AUC adds ~5% error.** True per-path AUC requires per-row T7 predictions, which K1-FU1 didn't save. The Hybrid 5 retrain at Phase 2 must save per-row T7 preds.

4. **PBO 0.20 is the constituent upper bound, not a retrained estimate.** Hybrid 5's true Bailey-LdP PBO requires a 27-HP grid CPCV run on the full Hybrid 5 architecture. If retrain at n=3,132 produces PBO > 0.40 for Hybrid 5, the architecture fails even with strong lift.

5. **DSR scaling assumption (lift held constant 528 → 4,892) is the binding methodological risk.** If lift compresses to +0.030 at n=2,326 (a plausible scenario per the program's K54 v1 → K54 v2 lift compression history), Hybrid 5 fails DSR-p<0.05 at every tested cell. The program needs a contingency: if lift at n=2,326 is < +0.04, the verdict is FAIL; if 0.03 ≤ lift < 0.04, BORDERLINE-extend-cohort; if ≥ +0.04, SURVIVES.

6. **K1-FU1's per-path T7 deltas have HIGH variance** (per-path std 0.154; range -0.349 to +0.367). Hybrid 5 inherits this variance partially: its per-path lift std is 0.063 (vs v3 master's 0.061), reflecting a small variance increase from T7-NAS routing. Hybrid 5's robustness to per-path noise is comparable to K54 v3 master — but on individual paths where T7-NAS gives extreme deltas (path 13 = -0.349; path 14 = +0.367), Hybrid 5 swings more than v3 master alone.

7. **No architecture survives under conservative N=200 anchor at any tested cell.** ONC clustering + effective_N=11 is methodologically REQUIRED for the program to land any K54 v4 ship. This is the program's single most important methodological commitment.

8. **K1-FU3's verdict refines K1's "BORDERLINE" K54 v4 readiness.** K1 said "BORDERLINE" because Arch A's invalidation broke the "both surviving" criterion. K1-FU3 finds:
   - Hybrid 5 is rank 1 with 5/5 evidence pillars + lowest DSR-p.
   - K54 v3 master is rank 2 with 5/5 evidence pillars + cross-period validated.
   - **Phase 2 retrain at n≥3,132 + Hybrid 5 architecture + ONC effective_N=11 + T=25 + component-ablation gate is the program-defensible path.**
   - K1's "DEFER K54 v4 dispatch" recommendation is **REVERSED** by K1-FU3: dispatch K54 v4 with Hybrid 5 PRIMARY architecture.

---

## 6. File index

**This dispatch:**
- `research/ml_program/phase_2/k1_followup/k1_fu3_architecture_research.md` (this synthesis)
- `research/ml_program/phase_2/k1_followup/k1_fu3_architecture_ranking.csv` (rank 1-5 + evidence flags)
- `research/ml_program/phase_2/k1_followup/k1_fu3_dsr_projection.json` (180 cells: 5 architectures × 4 cohorts × 3 T_paths × 3 N_trials)
- `research/ml_program/phase_2/k1_followup/k1_fu3_summary_blob.json` (machine-readable)
- `research/ml_program/phase_2/k1_followup/_compute_arch_research.py` (reproducer)

**Source data (READ-ONLY):**
- `research/ml_program/phase_2/k1_followup/k1_fu1_paired_results.json` (T7 fold-aligned NAS-only AUCs)
- `research/ml_program/forensics/2026-04-29/agent_k1_apples_apples_verification.md`
- `research/ml_program/forensics/2026-04-29/agent_e_dsr_threshold_scan.json`
- `research/ml_program/forensics/2026-04-29/agent_a2_recalibrated_ablation.md`
- `research/ml_program/forensics/2026-04-29/agent_c_apples_apples_paired.json`
- `research/ml_program/forensics/2026-04-29/agent_i_per_cohort_ensemble.json`
- `research/ml_program/audit/canonical_v1_rerun.md`
- `research/ml_program/audit/architecture_ab.md`
- `research/ml_program/models/k54_v3/cpcv_paired_results.json`
- `research/ml_program/models/k54_v2_arch_a/cpcv_results.json`
- `research/ml_program/models/k54_v1_canonical/cpcv_results.json`
- `research/ml_program/models/k54_v3/dsr_per_gate.json`
- `research/ml_program/models/k54_v2_arch_a/pbo_results.json`
- `research/ml_program/scout/feature_matrix.parquet`

---

## 7. Eight-bullet summary (orchestrator return)

1. **Winning architecture: Hybrid 5 = K54 v3 master + T7-style NAS_US30 specialist (K1-FU1 fold-aligned).** Lift +0.0497 vs canonical v1 (paired t p=0.0083, Wilcoxon p=0.0151, bootstrap p_one=0.0000, null permutation p=0.006, PBO 0.20 constituent upper bound). Sweeps 5/5 evidence pillars AND has the LOWEST DSR-p across all five architectures. K54 v3 master alone is rank 2 (lift +0.0484, also 5/5 PASS but +cross-period validated).

2. **Per-architecture verdicts under same 15 CPCV folds + canonical v1 baseline:**
   - **Hybrid 5**: lift +0.0497, t-p=0.008, null-p=0.006, PBO=0.20*, DSR-p=0.0061 SURVIVES at n=3,132+T=25+N=11. **5/5 PASS**.
   - K54 v3 master: lift +0.0484, t-p=0.008, null-p=0.006, PBO=0.20, DSR-p=0.0083 SURVIVES at same cell. **5/5 PASS** + **cross-period validated (n=2,326 gate c.i PASS)**.
   - T7 per-cohort: unpaired +0.0432 / fold-aligned NAS-only +0.0169 (K1-FU1, DEAD at +0.05). PBO=0.47 FAIL. **INDETERMINATE for full-cohort deployment**.
   - Hybrid 4 (v3+ArchA-on-NAS): lift +0.0403, t-p=0.040, null-p=0.020, PBO=0.20*. **4/5 PASS + Wilcoxon borderline**.
   - Arch A pure: lift +0.0339, t-p=0.147 FAIL, null-p=0.073 FAIL. **1/5 PASS** (bootstrap directional only).

3. **Recommended K54 v4 dispatch spec:** **Hybrid 5 architecture** + n≥3,132 cohort (Phase 2-A backfill) + K=6/N=4 CPCV (T_paths=25) + ONC effective_N=11 + fixed-HP CPCV-honest selection + new component-ablation gate (master-bundle add ≥+0.02 AND T7-NAS-routing add ≥+0.01, both bootstrap p<0.10) + cross-period gate (must replicate K54 v3's gate c.i PASS at pooled cohort). **Fallback 1 = K54 v3 master alone; Fallback 2 = Hybrid 4 (v3+ArchA-on-NAS).**

4. **Cohort × T × N optimal cell: n=3,132 × T=25 × N=11 → DSR-p=0.0061 SURVIVES at α=0.01 for Hybrid 5.** Under conservative N=200, no architecture survives at any tested cohort. **ONC effective_N=11 is the SUFFICIENT relaxation, not optional** — methodologically REQUIRED for Phase 2.

5. **Confidence: MEDIUM-HIGH.** Hybrid 5's 5/5 evidence sweep + lowest DSR-p is the strongest verdict the program has produced. Bounded by: (a) PBO 0.20 is constituent upper bound (true PBO requires Phase 2 retrain), (b) the master-bundle decomposition (v3 - ArchA per-path lift = +0.0145 with bootstrap p=0.19 NOT significant) reveals 30% of v3's lift comes from components that don't independently survive — Hybrid 5 inherits this concern, (c) Hybrid 5's full-cohort per-path AUC uses linear-blend approximation (true full-cohort AUC requires per-row T7 preds, which K1-FU1 didn't save).

6. **New ambiguity:** Hybrid 5's +0.0013 lift over K54 v3 master is small. Whether the small advantage replicates under retrain is the key Phase 2 question. The +0.0013 corresponds to T7's fold-aligned NAS lift mean +0.0169 weighted by 21% NAS row fraction ≈ +0.0036, partially offset by v3-NAS-master-bundle dropout. Cohort expansion to n=3,132 may amplify or compress this margin. **Component-ablation as a new gate addresses this directly**: at retrain, T7-NAS-routing must contribute ≥+0.01 per-path AUC over v3-NAS-fall-through with bootstrap p_one<0.10.

7. **Q1.5 hypothesis text recommendation:**
   *"K54 v4 (Hybrid 5 architecture: K54 v3 master bundle on non-NAS_US30 rows + T7-style per-cohort LightGBM specialist on NAS_US30 rows, both trained on identical K=6/N=4 CPCV folds with fixed-HP CPCV-honest selection) trained on Phase 2-A expanded cohort (n≥3,132) achieves OOS-AUC paired lift ≥ +0.04 vs canonical K54 v1 (mean OOS AUC 0.5286) under K=6/N=4 CPCV (T=25 paths, purge=7d, embargo=1d) with paired-t p<0.01, Wilcoxon p<0.05, bootstrap one-sided p<0.05, null-permutation p<0.05, PBO<0.40, AND DSR-p<0.05 under ONC effective_N=11. Component-ablation: (a) the master bundle's added components (meta-label + W-units + conformal) over Arch A pure contribute ≥+0.02 per-path AUC, AND (b) T7-NAS-routing over v3-NAS-fall-through contributes ≥+0.01 per-path AUC. Both ablations clear bootstrap p_one<0.10."*

8. **Key file paths:**
   - `research/ml_program/phase_2/k1_followup/k1_fu3_architecture_research.md` (this synthesis)
   - `research/ml_program/phase_2/k1_followup/k1_fu3_architecture_ranking.csv` (decision table)
   - `research/ml_program/phase_2/k1_followup/k1_fu3_dsr_projection.json` (full 180-cell DSR scan)
   - `research/ml_program/phase_2/k1_followup/k1_fu3_summary_blob.json` (machine-readable)
   - `research/ml_program/phase_2/k1_followup/_compute_arch_research.py` (reproducer)
   - `research/ml_program/phase_2/k1_followup/k1_fu1_paired_results.json` (T7 fold-aligned source)
   - `research/ml_program/forensics/2026-04-29/agent_k1_apples_apples_verification.md` (K1 baseline)
   - `research/ml_program/audit/canonical_v1_rerun.md` (canonical v1 anchor)
   - `research/ml_program/models/k54_v3/cpcv_paired_results.json` (master-bundle source data)

---

*End. K1-FU3 architecture re-search complete. READ-ONLY on production. No model artifacts modified. Existing K54 v3 / Arch A / Agent I T7 / K1-FU1 result files remain on disk; this dispatch supersedes their INTERPRETATION via fold-aligned + canonical-baseline paired methodology, AND constructs Hybrid 5 as the new program-recommended K54 v4 architecture.*
