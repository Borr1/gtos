# Agent K1 — Apples-to-Apples Paired Methodology Specification (LOCKED)

**Lock ID:** `agent_k1_apples_apples_methodology_2026-04-29`
**Author:** Forensic Agent K1 (Opus 4.7, max effort, subscription-only, READ-ONLY on production)
**Date:** 2026-04-29
**Purpose:** Re-run K54 v3 + Q1.3 Arch A + Agent I T7 NAS_US30 lift claims under a single,
strictly-paired methodology so the three numbers can be directly compared. Spec is locked
**before** the verification run executes (per memory `feedback_paired_fixed_hp_discipline`).

---

## 1. Why this spec exists

Three forensic agents have produced lift numbers in tension:

| Agent | Claim | Evidence |
|---|---|---|
| **C** | NAS_US30 specialist +0.103 over global is a POOL-AGGREGATION ARTIFACT. Apples-to-apples paired delta = -0.007 (n_paths=4, t-p 0.93, DSR-p 0.999). Also flagged Arch A's +0.0492 as possibly-artifactual. | `agent_c_nas_us30_specialist_forensic.md` + `agent_c_apples_apples_paired.json` |
| **I** | T7 per-cohort 4-LightGBM on NAS_US30-only reaches AUC 0.7128 (+0.111 over Q1.4 specialist). Unpaired vs K54 v3 specialist 0.6014. | `agent_i_per_cohort_ensemble.json` + `agent_i_alternative_architectures.md` |
| **E** | Cohort projection at T=20 + n=2,326 + N=200 yields DSR-p=0.009 SURVIVES — **but this assumes lift +0.0484 is real.** | `agent_e_dsr_threshold_scan.json` |

The three claims rest on incompatible methodology choices (different K, different baselines,
different prediction-aggregation depths). This spec normalizes them.

---

## 2. CPCV configuration (locked)

| Parameter | Value | Source |
|---|---:|---|
| K | 6 | identical across K54 v1 canonical, K54 v2 Arch A, K54 v3 |
| N | 2 | identical across all three jobs |
| n_paths | 15 | C(K,N) = C(6,2) = 15 |
| purge_days | 7 | identical |
| embargo_days | 1 | identical |
| fold composition | deterministic from cohort date ordering | **VERIFIED IDENTICAL** across v3, ArchA, canonical-v1 (all 15 path test_idx vectors exact match) |

This means per-path AUC vectors `[v3_aucs[i], arch_a_aucs[i], canonical_v1_aucs[i]]` are
**comparable on the same 15 test folds** — the fundamental requirement for paired analysis.

---

## 3. Cohort

| Property | Value |
|---|---:|
| n_total | 528 |
| n_NAS_US30 | 113 (NAS100=51, US30_CASH=62) |
| n_XAU_XAG | 215 (XAUUSD=164, XAGUSD=51) |
| n_GBPJPY | 62 |
| n_GBPUSD_USDJPY | 138 (USDJPY=69, GBPUSD=69) |
| max_date | 2026-04-24 |

---

## 4. Comparison metric (locked)

**Primary:** per-path OOS-AUC (15 paths, paired across same `test_idx`).
**Aggregation across paths:** per-path mean (NOT pool-aggregated AUC across paths).
**Rationale:** Agent C demonstrated that pool-aggregation depth matters. K=4/N=2 specialist
averages ~3 predictions/row; K=6/N=2 global averages ~5 predictions/row; the differential
variance reduction creates phantom AUC differences. **Per-path-mean defeats this artifact.**

**Secondary:** stationary-block bootstrap on per-path AUC diffs (block_len=5, n_boot=5000,
seed=17). One-sided p (H1: lift > 0).

**Tertiary (T7-only):** per-row pooled AUC restricted to the NAS_US30 mask (113 rows). This
is the framing Agent C used + Agent I aggregated.

---

## 5. Feature screening (locked)

Per-fold top-100 inside-fold (de Prado AFML §8.5; never on full data).
Verified identical screening protocol used by both Arch A and K54 v3.

---

## 6. Hyperparameters (locked, fixed-HP CPCV-honest)

Per memory `feedback_paired_fixed_hp_discipline`: each architecture gets ONE selected HP
(not per-fold). HP selection = best mean OOS AUC across 27-grid × 15 paths.

| Architecture | n_estimators | max_depth | learning_rate |
|---|---:|---:|---:|
| K54 v1 canonical (17 features, NO `symbol`) | 50 | 3 | 0.05 |
| K54 v2 Arch A (top-100 screen) | 100 | 5 | 0.05 |
| K54 v3 (top-100 screen + meta + W-pool + specialist + conformal) | 200 | 3 | 0.05 |

---

## 7. Baseline for lift (locked)

**Baseline:** K54 v1 canonical (17-feature, NO `symbol`). Selected per
`audit/canonical_v1_rerun.md` §2 because:
- The modeler-modified-v1 baseline (with `symbol`) is shown to be **0.0166 weaker** than
  canonical v1 (0.5120 vs 0.5286, paired across the same 15 folds).
- Both K54 v3 and Arch A reported lift **vs the modeler-modified v1**, which inflates lift
  by 0.0166 systematically.
- Honest comparison **MUST** use the canonical v1 anchor 0.5286.

This is the single largest methodological correction Agent K1 enforces.

---

## 8. DSR computation (locked)

Bailey-Lopez de Prado 2014 Deflated Sharpe Ratio (AFML eq 11.5; skew=0, kurt=3 — matches
Agent B + Agent E forensic conventions).

**Two parallel projections:**

### Projection A — Per-path SR (direct from CPCV per-path AUC diffs)

```
SR_per_path = mean_diff / std_diff_per_path
sigma_SR = sqrt( (1 - skew*SR + (kurt-1)/4 * SR^2) / (T_paths - 1) )
DSR_p = 1 - Phi( (SR_per_path - sr_max) / sigma_SR )
sr_max = expected_max_sharpe(N_trials) = sqrt(2*log(N)) - euler/sqrt(2*log(N))
```

This is the paired-AUC-Sharpe framing — what the per-path-mean lift actually buys you in
SR space, computed at T=15 actual paths.

### Projection B — Cohort-scaled SR (Agent E's framing)

Per Agent E's `_agent_e_compute.py`:
```
projected_SR = lift * (BASE_SR / BASE_LIFT) * sqrt(n / BASE_N)
             = lift * 26.34 * sqrt(n / 528)
```

Where BASE_SR=1.2748 + BASE_LIFT=0.0484 + BASE_N=528 are the K54 v3 calibration anchors.
DSR-p computed via the same Bailey-Lopez de Prado AFML eq 11.5.

This is the cohort-projection framing — what the lift WOULD buy you in SR space if cohort
expanded to n.

**K1 reports both.** Projection A reflects current evidence; Projection B reflects the
Phase 2 expansion projection.

**Trial budget scan:**
- T_paths in {15, 20, 50}
- N_trials in {50 (after ONC clustering), 200 (current Phase 1 cumulative)}
- cohort_n in {528 (current), 2326 (Phase 2 minimum), 3132 (aggressive_a), 4892 (aggressive_b)}

---

## 9. Block bootstrap (locked)

Stationary block bootstrap (Politis-Romano 1994):
- block_len = 5 (covers ~5-day adjacent fold dependency window)
- n_boot = 5000
- seed = 17 (deterministic)
- One-sided p: H1: lift > 0

---

## 10. Verdict thresholds (locked)

| Comparison | Threshold | Rationale |
|---|---:|---|
| K54 v3 vs canonical v1 | lift ≥ +0.04 | Q1.4 brief gate (a) effect-size threshold |
| Arch A vs canonical v1 | lift ≥ +0.04 | Same; was passing-via-modeler-baseline at +0.0492 |
| T7 NAS specialist vs v3 global (NAS only) | lift ≥ +0.05 | Q1.4 gate (d.specialist) threshold |

Combined verdict logic:
- If both K54 v3 + Arch A lifts BOTH survive at ≥+0.04: Phase 2 K54 v4 dispatch APPROVED.
- If one or both compress to +0.02–0.035: BORDERLINE; defer K54 v4; pivot to position-mgmt.
- If both compress to <+0.02: K54 family dead at this n; Phase 2 = position-management only.

---

## 11. Out-of-scope for Agent K1

- **Re-training Agent I T7** on the SAME 15 K=6/N=2 paths as K54 v3 global. This requires
  retraining infra not available in subscription-only K1 mode. The fold-aligned T7 vs
  v3-global comparison must be deferred to a follow-up dispatch.
- **API-spend tests** (T3 regime-input-to-AI). Subscription-only.
- **Holdout 2026-05-13+ tests.** Holdout window untouched per K54 v3 dispatch policy.

---

## 12. Reproducibility

All code in `_agent_k1_verify.py` + `_agent_k1_dsr_align.py`. Seeds locked. Deterministic
modulo numpy/scipy version churn (pinned to current Python environment).

Re-run command:
```
python research/ml_program/forensics/2026-04-29/_agent_k1_verify.py
python research/ml_program/forensics/2026-04-29/_agent_k1_dsr_align.py
```

---

*End of methodology spec. LOCKED before verification execution.*
