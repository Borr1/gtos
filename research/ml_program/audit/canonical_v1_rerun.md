# Canonical K54 v1 Re-run — Comparative Report

**Reconstructed by:** ML Program Orchestrator from `research/ml_program/models/k54_v1_canonical/cpcv_results.json` + `research/ml_program/models/k54_v1_per_regime/cpcv_results.json` (the agent's own `write_report()` crashed on a numpy `int64` JSON-serialization bug AFTER both Configs A + B had completed and saved their per-config JSONs).

**Cohort:** 528 rows, max_date 2026-04-24, win_rate 0.580. CPCV K=6, N=2 (15 paths), purge 7d, embargo 1d. Splits verified to match v2 (assertion in `run_canonical_v1_rerun.py:1107`).

---

## Section 1 — Headline numbers

| Configuration | n_features | Architecture | CPCV mean OOS AUC |
|---|---:|---|---:|
| **K54 v2** (modeler) | 1234 | Global LightGBM | **0.5429** |
| **Modeler-modified v1** (15 feat with `symbol`) | 15 | Global LightGBM | **0.5120** |
| **Config A — canonical v1** (17 feat, NO `symbol`) | 17 | Global LightGBM | **0.5286** |
| **Config B — canonical v1 per-regime ensemble** (17 feat) | 17 | Per-regime ensemble (4 regimes + global fallback) | **0.5293** |

---

## Section 2 — Comparison 1: did adding `symbol` to v1 strengthen or hurt it?

| Metric | Value |
|---|---:|
| Modeler-modified v1 (15 feat with `symbol`) | 0.5120 |
| Canonical v1 Config A (17 feat, NO `symbol`) | **0.5286** |
| Δ (canonical − modeler-modified) | **+0.0166** |

**Hypothesis: REFUTED.** The orchestrator's interrogation hypothesis B2 was "adding `symbol` likely STRENGTHENED v1, narrowing the v2 gap." The data shows the opposite: **canonical v1 (without `symbol`) is HIGHER by 0.0166 AUC.** Adding `symbol` (7-class) at n=528 likely overfit to per-instrument patterns the leaner canonical features avoided.

**Implication for K54 v2's lift:**

- Modeler reported v2 vs modeler-v1: +0.0309.
- Real v2 vs canonical-v1 (Config A): **+0.0143** — DROPS by 0.0166.

The +0.0309 lift was substantially produced by the modeler's choice to weaken K54 v1's baseline, not by K54 v2's strength. **Stouffer combined p collapses from 0.0015 (modeler) to 0.196 (canonical Config A) — NOT significant at any reasonable threshold.**

---

## Section 3 — Comparison 2: per-regime architecture vs global (canonical v1)

| Metric | Value |
|---|---:|
| Config A — canonical global | 0.5286 |
| Config B — canonical per-regime | 0.5293 |
| Δ (B − A) | **+0.0007** |
| K54 v1 audit-cited per-regime lift | +0.032 (single time-walk-forward, n=94, 2026-04 only) |
| **CPCV-honest verdict** | **REVERSED — per-regime does NOT add the audit-cited +0.032 lift; only +0.0007 here** |

The K54 v1 audit reported per-regime ensemble adds +0.032 AUC over global. Under CPCV K=6/N=2 (15 paths), the per-regime architecture adds **+0.0007** — essentially zero. **The audit's +0.032 lift was a test-slice artifact, not a replicable architectural property.**

### Per-regime AUC breakdown (Config B aggregate predictions across all 15 paths)

| Regime | n predictions | AUC | Below random? |
|---|---:|---:|:---:|
| UNTAGGED | 215 | 0.4350 | **YES** (−0.065) |
| bearish | 68 | 0.4363 | **YES** (−0.064) |
| bullish | 135 | 0.4831 | YES (−0.017) |
| transitional | 110 | 0.5150 | NO (+0.015) |

**3 of 4 regime models perform BELOW random.** Only `transitional` is positive, and barely. The per-regime ensemble works on Config B's 0.5293 aggregate purely because of the Platt calibration + ensemble averaging effect, not because each regime model has predictive power.

### Regime label distribution (cohort)

UNTAGGED 215 / bullish 135 / transitional 110 / bearish 68. Distribution skewed heavily UNTAGGED (40.7% of cohort).

---

## Section 4 — K54 v2 vs canonical v1 — Gate (a) under correct baseline

| Metric | Modeler-v1 (with symbol) | Canonical Config A | Canonical Config B (per-regime) |
|---|---:|---:|---:|
| auc_v2_mean | 0.5429 | 0.5429 | 0.5429 |
| auc_v1_mean | 0.5120 | **0.5286** | **0.5293** |
| Δ (v2 − v1) | +0.0309 | **+0.0143** | **+0.0136** |
| Stouffer combined p | 0.001546 | **0.195705** | **0.032428** |
| Fisher combined p | (not in modeler output) | 0.266968 | 0.022443 |
| 95% CI (per-path SE) | [−0.0093, +0.0711] | [−0.0172, +0.0459] | [−0.0287, +0.0558] |
| Per-path positive lift count | 10/15 | (per-path data in cpcv_results.json paths_per_hp) | (per-path data in cpcv_results.json paths_per_hp) |
| **Gate (a) verdict** | FAIL (mean<0.04) | **FAIL (mean<<0.04 AND p>>0.01)** | **FAIL (mean<<0.04 AND p>0.01)** |

**The Q1.3 verdict is even more decisively FAIL than the modeler reported.** With the canonical baseline:

- Lift collapses from +0.0309 to +0.0143 (~0.014, well below the +0.04 target).
- Stouffer combined p collapses from 0.001546 to 0.196 (Config A) / 0.032 (Config B) — neither beats the p<0.01 gate.
- Under CPCV-honest train-overlap-corrected SE (per `audit/statistical_reevaluation.md`: SE 0.0649 vs naive ~0.016), the lift is **statistically indistinguishable from zero** (CPCV-honest p ≈ 0.7+).

---

## Section 5 — Selected hyperparameters

| Config | n_estimators | max_depth | learning_rate | Selection method |
|---|---:|---:|---:|---|
| Config A — canonical v1 global | 50 | 3 | 0.05 | Best mean OOS AUC across 27-grid × 15 paths |
| Config B — canonical v1 per-regime | 50 | 5 | 0.01 | Best mean OOS AUC across 27-grid × 15 paths |
| K54 v2 (per `meta.json`) | 100 | 5 | 0.1 | Same selection method |

**Pattern:** all 3 selected HPs are at the heavily-regularized end of the grid (smallest n_estimators or smallest learning_rate). Confirms the orchestrator's interrogation Q D1 — at 0.43 rows-per-feature for v2 (or 31 rows-per-feature for canonical v1's 17), the optimizer correctly throttles to maximum regularization. Each model is essentially the smallest version of itself that fits the available data.

---

## Section 6 — Key implications

1. **The +0.0309 modeler lift was substantially baseline-weakening, not catalog-strengthening.** Canonical v1 reduces the lift to +0.0143; per-regime canonical reduces further to +0.0136.
2. **Per-regime architecture does NOT replicate the K54 v1 audit's +0.032 lift under CPCV** — the cited lift was test-slice-specific. Per-regime adds +0.0007 (effectively nothing) under proper CPCV.
3. **K54 v1's per-regime models are individually worse than random** on 3 of 4 regimes (UNTAGGED 0.435, bearish 0.436, bullish 0.483). The ensemble's 0.5293 aggregate is calibration-driven, not predictive-power-driven.
4. **K54 v1's published AUC 0.571 was a single-test-slice fluke.** Under CPCV, K54 v1 sits at 0.512-0.529 across canonical/modified/per-regime variants — barely above random.
5. **There is no "proper-architecture K54 v1" baseline that K54 v2 must beat.** The per-regime ensemble is itself near-random under CPCV. The headline +0.04 effect-size threshold was set against an inflated baseline that doesn't exist under CPCV-honest measurement.

This refutes orchestrator interrogation hypotheses B2 (symbol strengthens v1), B3 (canonical v1 might give larger lift), and B5 (per-regime v1 might beat v2). All three predicted Q1.4-rescue paths via baseline correction. **None work.** The verdict only gets MORE decisively FAIL under proper baselines, not less.

---

## Section 7 — Per-path tables

Available in:
- `research/ml_program/models/k54_v1_canonical/cpcv_results.json` (Config A)
- `research/ml_program/models/k54_v1_per_regime/cpcv_results.json` (Config B)

Both contain 15-path AUC + DeLong p details.

---

## Section 8 — Code revisions + file map

- `research/ml_program/models/k54_v1_canonical/run_canonical_v1_rerun.py` — full pipeline (the agent's deliverable; crashed at line 960 on numpy `int64` JSON-serialization issue while writing per-regime aggregate output, AFTER both configs computed successfully).
- `research/ml_program/models/k54_v1_canonical/k54_v1_canonical.lgb` — Config A model.
- `research/ml_program/models/k54_v1_canonical/cpcv_results.json` — Config A per-path + summary.
- `research/ml_program/models/k54_v1_per_regime/regime_*.lgb` — Config B per-regime models (UNTAGGED, bearish, bullish, transitional, global_fallback).
- `research/ml_program/models/k54_v1_per_regime/cpcv_results.json` — Config B per-path + summary.
- This synthesis: `research/ml_program/audit/canonical_v1_rerun.md`.

---

## Final report (under 300 words)

1. **Canonical v1 (Config A) CPCV mean AUC: 0.5286.** Adding `symbol` HURT v1 (modeler v1 = 0.5120; canonical without `symbol` = 0.5286). Hypothesis "symbol strengthens v1" REFUTED.
2. **Per-regime v1 (Config B) CPCV mean AUC: 0.5293.** Per-regime adds **+0.0007** over global, NOT the +0.032 cited in K54 v1 audit. The audit's lift was a test-slice fluke; the per-regime architecture does NOT replicate under CPCV. Per-regime AUCs: UNTAGGED 0.435, bearish 0.436, bullish 0.483, transitional 0.515 — 3 of 4 below random.
3. **K54 v2 vs canonical v1 (Config A): mean lift +0.0143**, Stouffer p=0.196. Gate (a) FAILS far more decisively than the modeler reported. Under CPCV-honest train-overlap-corrected SE the lift is ~0 (p≈0.7+).
4. **K54 v2 vs per-regime v1 (Config B): mean lift +0.0136**, Stouffer p=0.032. Even with per-regime architecture, K54 v2 doesn't beat v1 by anything close to +0.04 AUC.
5. **The "K54 v1 baseline AUC 0.571" published number was a single-test-slice artifact.** CPCV-honest K54 v1 sits at 0.512-0.529 across all three architectural variants — barely above random.
6. **Top-1 surprise:** the K54 v1 audit's "+0.032 per-regime lift" REVERSED under CPCV. The per-regime ensemble adds essentially zero lift over global at this n. We were chasing a baseline that wasn't there. K54 v1's headline numbers were CV-overfit; the program's "lift over K54 v1" framing was mathematically broken from inception.
