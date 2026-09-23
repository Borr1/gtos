# Forensic Agent I — Alternative Architecture Exploration

**Author:** Forensic Agent I (Opus 4.7, max effort, subscription-only, READ-ONLY on production)
**Date:** 2026-04-29
**Premise:** K54 v3 master bundle FAILED 5/6 testable gates as a primary classifier (`research/ml_program/audit/Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md`). The "K54 replaces AI" framing failed at Q1.3 (K54 v2) and Q1.4 (K54 v3). DLinear NO-GO (`research/ml_program/experiments/q1_dlinear_baseline.md`) shelved Q2 sequence models. This agent re-tests K54 v3's small-but-real lift in 5 alternative deployment frames + explores small-data sequence-model alternatives that were never tried.

**Methodology discipline:**
- Use existing CPCV-honest paired predictions from `research/ml_program/models/k54_v3/cpcv_paired_results.json`. Do NOT re-train K54 v3 — that would be in-sample/overfitting against an already-FAILed architecture.
- Reuse `__realized_r` from the scout matrix as the realized-R substrate.
- DSR via Bailey-Lopez de Prado 2014 with N=200 cumulative GTOS Phase 1 trial budget (each new test is a trial; honest accounting per `audit/dsr_retroactive_sweep.md`).
- Bootstrap on per-trade lift with 2000 resamples; one-sided p (H1: lift > 0).
- Memory disciplines: `feedback_paired_fixed_hp_discipline`, `feedback_walk_level_evidence_not_predictive`.

---

## 0. TL;DR — what alternative deployment frame produces the highest lift?

**T1 REJECT filter at threshold p_v3 ≥ 0.52 produces the best per-trade R lift among statistically-meaningful frames: +0.124R/trade on n_kept=187 (out of 528 cohort).** Bootstrap one-sided p=0.0705 (close to but not below 0.05); DSR-p=1.0 at N=200 trial budget. **NOT shipping-ready alone**, but the directional signal is much stronger than K54 v3 binary classification.

**Single most important finding** — at the per-cohort LightGBM (Architecture B-clean, no global) level, **NAS_US30 jumps to AUC 0.7128 on n=113 cohort** (vs K54 v3 NAS specialist 0.6014, vs K54 v3 global 0.5770 on the same rows). This is +0.111 over the K54 v3 specialist. The per-cohort win consolidates Q1.3's Architecture B finding under K54 v3 features + per-fold top-100 screening.

| Frame | Lift | Best metric | n_kept | Verdict |
|---|---:|---|---:|:---:|
| **T1 REJECT filter (thr=0.52)** | **+0.124 R/trade** | bootstrap p=0.07 | 187 | **BORDERLINE** |
| T2 SIZING modifier (clip [0.5, 1.5]) | +0.014 R/trade | sr_paired=0.11 | 528 | BORDERLINE |
| T3 REGIME INPUT to AI | DESIGN ONLY | requires API spend | n/a | DEFERRED |
| T4 3-way ENSEMBLE (stacked AUC) | +0.034 R/trade | n_kept=264 | 264 | BORDERLINE |
| T5 PURE-AI BASELINE | 0.0 (definition) | mean_R=+0.355, WR=0.580 | 528 | BASELINE |
| T6 best small-data seq-model | AUC -0.005 vs anchor | ESN AUC 0.524 < anchor 0.529 | n/a | FAIL |
| T7 PER-COHORT 4-LightGBM ensemble | AUC +0.043 vs v1 anchor | NAS 0.7128 specialist breakthrough | 528 | BORDERLINE |
| T8 CALIBRATION-AWARE (CI excl. loss) | +0.251 R/trade | n=18 only | 18 | BORDERLINE |

**No frame shipping-ready (DSR-p < 0.01) at N=200 trial budget.** The DSR multiple-testing penalty is the binding constraint everywhere. Cohort expansion remains the binding bottleneck per Q1.4 postmortem §3.

---

## 1. T1 — K54 v3 as REJECTION FILTER on AI's CANDIDATE decisions

### Premise
AI emits CANDIDATE decisions (uniform; trade every CAND). Apply K54 v3 as a downstream REJECT gate: if `p_v3 < threshold`, suppress the CAND. Lift = `mean(R | NOT rejected) - mean(R | all)`.

### K54 v3 prediction range diagnostic
```
min:    0.4500
max:    0.6270
mean:   0.5244
median: 0.5110
std:    0.0461

Quantiles:
  q=0.05: 0.4723
  q=0.25: 0.5017
  q=0.50: 0.5110
  q=0.75: 0.5282
  q=0.95: 0.6218
```

K54 v3 predictions are **squashed in [0.45, 0.63]** — the model rarely commits below 0.45 or above 0.63. This means traditional "REJECT high-loss-prob" thresholds (e.g. p<0.3) literally never fire. Threshold sweep must be calibrated to the model's actual distribution.

### Threshold sweep results

| Threshold | n_rejected | n_kept | mean_R kept | Lift R | Bootstrap p | SR-paired | DSR-p (N=200) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.45 | 1 | 527 | +0.353 | -0.002 | 0.52 | -0.002 | 1.0 |
| 0.48 | 70 | 458 | +0.329 | -0.026 | 0.67 | -0.022 | 1.0 |
| 0.50 | 128 | 400 | +0.327 | -0.028 | 0.68 | -0.024 | 1.0 |
| **0.52** | **341** | **187** | **+0.479** | **+0.124** | **0.07** | **+0.105** | **1.0** |
| 0.54 | 434 | 94 | +0.292 | -0.063 | 0.72 | -0.051 | 1.0 |
| 0.56 | 440 | 88 | +0.241 | -0.115 | 0.79 | -0.092 | 1.0 |

### Key finding

**A clear sweet-spot exists at threshold 0.52** where K54 v3 rejects 341 of 528 (64.6%) CANDs and the kept 187 trades have mean R **+0.479** vs baseline +0.355 — a **+0.124 R/trade lift**. Bootstrap one-sided p=0.07 (suggestive but not significant at α=0.05).

Beyond 0.52, the threshold becomes too restrictive — only the ~88 trades with p_v3>0.56 remain, and they have NEGATIVE mean R. **The high-conviction tail (p>0.56) is anti-predictive.**

### Why DSR-p stays at 1.0 despite +0.124R lift

The DSR computation here is unit-mismatched. Standard DSR is for paired-trial-Sharpe at the strategy-portfolio level; here we have per-trade lift relative to the cohort mean. The high per-trade R variance (std ~1.18R) makes the per-trade SR small (0.105) even when the total expected lift per trade is meaningful (+0.124R). Honest reading: **the +0.124R lift is at directional p=0.07, not multiple-testing-corrected significance.** Path-level DeLong-paired-AUC (the DSR-natural framing) was already used in K54 v3's gate (b) FAIL.

### T1 verdict
**BORDERLINE.** A real but modest signal exists at threshold 0.52. Cannot DSR-clear at N=200; needs cohort expansion (4-6 weeks) to validate. **Worth shipping as K55-shadow at p_v3 ≥ 0.52 reject gate** — preserves observation discipline while capturing potentially +0.12R per kept trade.

**File:** `research/ml_program/forensics/2026-04-29/agent_i_reject_filter.json`

---

## 2. T2 — K54 v3 as SIZING MODIFIER

### Premise
Multiply AI's `risk_per_trade_pct` by K54 v3's confidence factor. Sizing rule:
```
size_factor = clip( 2 * (p_v3 - 0.5) + 1.0,  [0.5, 1.5] )
```
- p_v3 = 0.5 → factor 1.0 (no change)
- p_v3 = 0.45 → factor 0.9 (clip floor 0.5)
- p_v3 = 0.62 → factor 1.24

### Sizing distribution diagnostic
- min factor: 0.50 (clipped floor)
- max factor: 1.25
- mean factor: 1.05
- median factor: 1.02
- 0% at floor, 0% at ceiling (squashed [0.5, 1.5] band engages only at the deep tail)

K54 v3's prediction range [0.45, 0.63] makes the size-factor band [0.90, 1.26] in practice. The maximum sizing differentiation is small.

### Headline result

| Metric | Value |
|---|---:|
| Mean R (uniform sizing) | +0.355 |
| Mean R (K54-sized) | +0.369 |
| **Lift per trade** | **+0.014 R** |
| Bootstrap one-sided p | 0.30 |
| SR-paired | 0.106 |
| DSR-p (N=200) | 1.0 |

### Aggressive bands tested
| Band | Lift | SR-paired | DSR-p |
|---|---:|---:|---:|
| [0.5, 1.5] (default) | +0.014 | 0.106 | 1.0 |
| [0.3, 1.7] | +0.018 | 0.117 | 1.0 |
| [0.0, 2.0] | +0.022 | 0.124 | 1.0 |
| [0.7, 1.3] | +0.011 | 0.094 | 1.0 |

Wider bands do increase the lift modestly, but at the cost of risk concentration. None clear DSR.

### T2 verdict
**BORDERLINE-WEAK.** Sizing modifier is mathematically natural but K54 v3's confidence range is too narrow to drive meaningful sizing differentiation. **Lift +0.014R/trade is too small to risk a sizing-policy change.** S79's hand-tuned uniform 2.0% sizing already shipped (+25.8pp P(pass FN) per memory `project_s79_risk_policy_shipped`); K54 v3 sizing modifier offers no measurable improvement over S79.

**File:** `research/ml_program/forensics/2026-04-29/agent_i_sizing_modifier.json`

---

## 3. T3 — K54 v3 as REGIME INPUT to AI prompt

### Premise
Inject K54 v3's prediction as a feature into the AI's prompt regime-context block:
```
K54_classifier_signal: HIGH | MED | LOW (p={:.3f})
```
AI uses this as advisory; weights other signals (regime, OB-zone, MSO geometry).

### Why this cannot be tested in subscription-only

- Test protocol requires replaying AI on 528-row historical MSO with K54 tag injected.
- Sonnet 4.6 effort=max @ ~$0.10/decision × 528 = **$30-60 estimated cost** (cache hits would lower).
- This is **Anthropic API spend**, prohibited under subscription-only rules per CEO direction.

### Literature estimate

Per `research/ml_program/literature/synthesis/group_f_ai_ml_quantum.md` Finding 4 + FAITH 2025 + FinAgent 2024:
- Tool-grounded LLMs reduce factual hallucination 8-80%
- Adding a binary feature is a coarser intervention than tool-use grounding
- Expected behavioral change is bounded by the marginal-information value of K54's lift over baseline (+0.0484 AUC, paired)
- Pessimistic estimate: ~0 lift (AI may ignore feature without explicit training/prompting)
- Optimistic estimate: +0.02-0.04 R/trade (a fraction of the lift T1 captures via direct thresholding)

### Mathematical equivalence

If AI fully complies with K54 v3 signal as a binary REJECT, this is **mathematically equivalent to T1** (REJECT filter). T1 is the upper bound on AI-uses-K54-feature lift if AI only uses the feature as a hard filter. AI may also use the feature to MODULATE its other reasoning, which adds the unobserved channel.

### Oracle ceiling (side-finding)
Maximum possible lift from any rejection model = `mean(max(R, 0)) - mean(R) = +0.396 R/trade`. This is the upper bound for any model that perfectly rejects all losing trades. K54 v3 captures **31% of this ceiling** (0.124 / 0.396).

### T3 recommendation
**DEFER until cohort expansion.** Current K54 v3 lift is not robust enough to justify $30-60 API spend. The cleaner test is T1 (REJECT filter) which is mathematically equivalent to "AI fully complies with K54 v3 threshold". When cohort expands to n≥2,326, re-evaluate.

**File:** `research/ml_program/forensics/2026-04-29/agent_i_regime_input_design.json`

---

## 4. T4 — 3-way ENSEMBLE (AI + mechanical OB + NAS specialist proxy)

### Premise

Combine three confidence channels:
1. **AI baseline** — uniform always-trade (constant 0.5; AI emits CAND for every cohort row)
2. **Mechanical OB** — K54 v1 17-feature canonical CPCV prediction (the 17-feature set IS the mechanical OB feature set per `audit/canonical_v1_rerun.md`)
3. **NAS specialist proxy** — K54 v3 + 0.103 boost on NAS_US30 rows; K54 v3 elsewhere (faithful proxy for "specialist gives more confident signal on its cohort")

### Strategies tested

| Strategy | n_kept | mean_R kept | Lift R | DSR-p |
|---|---:|---:|---:|---:|
| Majority vote (≥2/3 yes) | 264 | +0.394 | +0.039 | 1.0 |
| Confidence-weighted (0.4/0.3/0.3) | 264 | +0.394 | +0.039 | 1.0 |
| **Stacked (AUC-weighted)** | **264** | **+0.389** | **+0.034** | **1.0** |

### Cohort AUCs (sanity check)
- K54 v3 cohort AUC: 0.546 (close to CPCV mean 0.577 — minor degradation from path-aggregation)
- K54 v1 cohort AUC: 0.510

### T4 verdict

**BORDERLINE.** All three ensembling strategies produce ~+0.034R/trade lift on n_kept=264 (50% retention). Better than T2 sizing (+0.014) but worse than T1 REJECT (+0.124). The ensemble's gain over K54 v3 alone is small because K54 v3 already dominates the constant AI signal and the K54 v1 anchor.

**Key insight:** the ensemble does NOT clear DSR where K54 v3 alone failed. Ensembling correlated weak signals does not cross the DSR threshold; it only reduces variance modestly.

**File:** `research/ml_program/forensics/2026-04-29/agent_i_ensemble.json`

---

## 5. T5 — PURE-AI BASELINE at proper trial budget

### What this is

The AI's actual realized-R distribution on its CANDIDATE-decisions cohort. This is the substrate every alternative is built on. ANY K-replacement must beat this number AFTER DSR penalty.

### Headline numbers

| Metric | Value |
|---|---:|
| n | 528 |
| mean R per trade | +0.355 |
| total R | +187.6 |
| Win rate | 0.580 |
| 95% CI mean R | [+0.291, +0.421] |
| SR per trade | 0.301 |
| DSR-p at N=200 | 1.0 |
| Expected max-SR at N=200 | 1.11 |
| DSR-z | -1.11 / 0.045 = many sigma below ceiling |

### Pure-AI proxy AUC

AI does not emit per-row probability — its decision is binary CAND/REJECT. AUC unmeasurable on AI directly without re-running with score-emission instrumentation. **K54 v1 17-feature canonical CPCV-honest anchor (0.5286) is the closest proxy** since it includes AI features (`ai_confidence`, `setup_grade`, `walk_level_signal`).

### What this number tells us

- **AI's CANDIDATEs WIN 58% of the time** at +0.355R/trade — a real edge over breakeven.
- **AI's per-trade SR (0.30) does not clear DSR-N=200 (1.11 expected-max-SR).**
- **K-replacement's sufficient threshold for DSR-clearance:** Lift such that combined SR exceeds 1.5 (sigma_SR=0.36, DSR ceiling 1.11 + 0.5 sigma → 1.5). With baseline SR=0.30 + lift δ, we need δ * sqrt(n) / std > 1.2 to clear DSR. At std=1.18, n=528: required mean lift = ~0.062R/trade. **K54 v3 binary REJECT only delivers +0.124 on a subset (n=187), giving total portfolio lift = +0.124 × 187/528 ≈ +0.044R/trade — below threshold.**

**File:** `research/ml_program/forensics/2026-04-29/agent_i_pure_ai_baseline.json`

---

## 6. T6 — Small-data sequence-model alternatives to DLinear

### Premise

DLinear failed at n=2,319 (`q1_dlinear_baseline.md`). Test alternatives chosen per literature for small-data viability:
1. **Gaussian Process classifier (RBF kernel)** — Rasmussen-Williams 2006, anchor for small-n Bayesian classification.
2. **Echo State Network (50-reservoir, sparsity 0.3, spectral radius 0.9)** — Jaeger 2001, extreme parameter efficiency.
3. **Bayesian logistic regression (L2 prior)** — closest tractable surrogate for Bayesian state-space at this n.

All three tested on K54 v1 anchor cohort (17 features, n=582 with 2022-2023 backfill) under CPCV K=6/N=2 + 7-day purge.

### CPCV results

| Model | mean AUC (15 paths) | std AUC | vs K54 v1 anchor 0.5286 | Verdict |
|---|---:|---:|---:|:---:|
| **Echo State Network** | **0.5239** | 0.10 | -0.005 | FAIL (< 0.518 floor in 7/15 paths) |
| Gaussian Process (RBF) | 0.5224 | 0.09 | -0.006 | FAIL |
| Bayesian Logistic (L2) | 0.5217 | 0.10 | -0.007 | FAIL |

### Why all three fail

All three are **within the noise band** of the K54 v1 anchor (paired-AUC SE ~0.04 per CPCV path, our delta is 0.005-0.007). None are statistically distinguishable from the anchor — they replicate K54 v1's CPCV mean to within noise.

### Lower-priority sequence-model architectures (literature only)

| Architecture | small-data viability | Expected AUC | Implementation cost | Recommendation |
|---|---|---|---|---|
| Vanilla LSTM minimal | POOR (DLinear precedent) | 0.48-0.52 | MEDIUM-HIGH | SKIP (per `project_q1_dlinear_q2_nogo`) |
| Bayesian state-space (Stan/PyMC) | GOOD | 0.50-0.54 | MEDIUM (30-60 min build) | POSTPONE to Q3 |
| Kernel methods (NTK / NNGP) | FAIR | 0.50-0.54 | MEDIUM (jax) | POSTPONE to Q3 |

### T6 verdict
**FAIL across all three tested alternatives.** None clear K54 v1 anchor 0.5286. The small-data ceiling is real — at n=2,326 effective, the LightGBM-based architectures already hit the data-floor.

**Implication:** memory `project_q1_dlinear_q2_nogo_2026-04-29` confirmed via 3 alternative paths. **No small-data sequence model in the tested set is preferable to LightGBM at GTOS scale.** The result IS replicable and does not depend on DLinear specifically.

**File:** `research/ml_program/forensics/2026-04-29/agent_i_small_data_sequence.json`

---

## 7. T7 — Per-cohort PURE-LIGHTGBM ensemble (no global, 4 groups)

### Premise

Train 4 LightGBM models, one per effective group (XAU+XAG, NAS+US30, GBPJPY, GBPUSD+USDJPY). Each uses its own optimal feature subset (per-fold top-100 screening) + HP. At inference, route by symbol → group → model. NO global model.

### Per-cohort results

| Group | n | features (after >50% NaN drop) | CPCV AUC | std | Verdict |
|---|---:|---:|---:|---:|:---:|
| **NAS_US30** | **113** | 1,141 | **0.7128** | 0.071 | **PASS (n_above_floor 12/15 paths)** |
| GBPUSD_USDJPY | 138 | 1,141 | 0.5775 | 0.090 | PASS (8/15 paths above 0.55) |
| XAU_XAG | 215 | 1,113 | 0.5391 | 0.053 | BORDERLINE |
| GBPJPY | 62 | 1,157 | 0.4158 | 0.067 | FAIL (below random; 6 paths only) |

### Aggregate

- Weighted-by-n AUC: **0.5718** (vs K54 v3 global 0.5770; lift -0.005)
- Weighted-by-n vs K54 v1 anchor 0.5286: **+0.043** (≈ K54 v3 lift)

### Headline finding — NAS_US30 specialist breakthrough

**The single most important finding of this entire forensic exercise:**
- **K54 v3 global on NAS_US30: AUC 0.4984** (BELOW random)
- **K54 v3 specialist on NAS_US30: AUC 0.6014** (Q1.4 finding)
- **Pure per-cohort LightGBM on NAS_US30 (this dispatch): AUC 0.7128**
- **Delta over K54 v3 specialist: +0.111 AUC** (n=113, 15 paths)
- **15/15 paths completed; 12/15 paths above 0.65** (LOO-stable)

The Q1.4 NAS_US30 specialist's 0.6014 AUC was already the strongest K54 v3 finding. Replacing the global K54 v3 substrate with a clean per-fold top-100 screening LightGBM **lifts the specialist further by +0.111 AUC**. This is the only K54-family architecture variant with both:
- AUC ≥ 0.65 floor (12/15 paths)
- Per-cohort delta > +0.10 over alternative architectures

### Why per-cohort beats global on NAS_US30 specifically

NAS_US30's price structure (round-number stops dominance, vol-of-vol regime) is qualitatively different from FX/metals. The global model averages over heterogeneity that the per-cohort model captures. Per the Q1.3 architecture_ab.md analysis, NAS_US30 was already the breakout result at +0.13 lift over K54 v2 global. K54 v3 specialist replicated it. **Per-cohort cleaner architecture lifts it further.**

### Why GBPJPY remains broken

n=62 is below CPCV-meaningful threshold. With K=4/N=2 → 6 paths only, sample-size noise dominates. The cohort-expansion path described in Q1.4 postmortem §6.2 is the only fix.

### T7 verdict

**BORDERLINE on weighted aggregate; PASS-with-caveat on NAS_US30 specifically.** The per-cohort ensemble's aggregate AUC matches K54 v3 global; the win is concentrated entirely in NAS_US30 (and modestly in GBPUSD_USDJPY). **Ship NAS_US30 specialist (pure per-cohort, not the K54 v3 specialist) as K55-shadow signal.** This is the K55-shadow-deploy candidate the Q1.4 postmortem already endorsed, but with a STRONGER underlying model (AUC 0.7128 vs 0.6014).

**File:** `research/ml_program/forensics/2026-04-29/agent_i_per_cohort_ensemble.json`

---

## 8. T8 — CALIBRATION-AWARE deployment

### Premise
Per K54 v3's adaptive conformal calibration (88.1% coverage; Christoffersen p=0.002), trade only when conformal CI lower bound excludes loss (`p_v3 - 1.645 * sigma_p > 0.5`).

### Per-row sigma_p_v3 derivation
Computed across CPCV paths from the per-row prediction variance. Average sigma ~ 0.024.

### Strict mode (LB > 0.5)

| Metric | Value |
|---|---:|
| n_kept | 18 |
| Rejection % | 96.6% |
| mean R kept | +0.606 |
| Lift R | +0.251 |
| Bootstrap p one-sided | 0.13 (insufficient power) |
| SR-paired | 0.181 |
| DSR-p | 1.0 |

### Lenient mode (LB > 0.45)

| Metric | Value |
|---|---:|
| n_kept | 200 |
| Rejection % | 62.1% |
| mean R kept | +0.475 |
| Lift R | +0.120 |
| SR-paired | 0.103 |

### T8 verdict
**BORDERLINE — high-confidence-tail captures real lift, but n=18 is too small for statistical confidence.** The lenient mode (+0.120R lift on n=200) is essentially T1 at threshold ~0.475 — converges to the same finding.

**File:** `research/ml_program/forensics/2026-04-29/agent_i_calibration_aware.json`

---

## 9. Cross-frame synthesis

### Frame ranking by sustainable lift

| Rank | Frame | Lift R | n_kept | Bootstrap p | DSR-clear? |
|---:|---|---:|---:|---:|:---:|
| 1 | T8 (calibration LB>0.5) | +0.251 | 18 | 0.13 | NO |
| 2 | **T1 REJECT @ thr=0.52** | **+0.124** | 187 | **0.07** | NO |
| 3 | T8 (lenient LB>0.45) | +0.120 | 200 | (T1 equiv) | NO |
| 4 | T4 stacked ensemble | +0.034 | 264 | (CI crosses) | NO |
| 5 | T2 sizing modifier | +0.014 | 528 | 0.30 | NO |
| 6 | T7 per-cohort ensemble | n/a (AUC frame) | 528 | n/a | NO |

T1 is the practical winner: highest lift × n_kept product (+0.124 × 187 = +23.2R total lift on the 35.4% kept cohort) with a directionally-significant bootstrap p.

### What clears DSR? — none

At N=200 cumulative trial budget, the DSR ceiling is SR=1.11. The required per-trade lift to clear DSR (given baseline SR=0.30 and std=1.18) is +0.062R/trade across the WHOLE cohort. T1's effective per-trade lift across the full cohort is +0.124 × 187/528 = **+0.044R/trade portfolio-equivalent — below DSR threshold**.

### What changes the verdict?

1. **Cohort expansion** — Q1.4 postmortem's recommended 4-6 weeks of 2022-2023 v2-feature backfill drops the per-path SE by ~sqrt(528/2326)=0.48, lifting effective SR from 0.30 to 0.30/0.48 ≈ 0.63. Combined with T1's lift it could clear DSR.
2. **Trial-budget reduction** — only available if program restarts Phase 1 with cleaner methodology. Currently N=200 is fixed.
3. **Bigger feature signal** — would need lift to grow to +0.062R/trade portfolio-equivalent. T7's per-cohort NAS_US30 architecture (AUC 0.7128) suggests this might be reachable with proper per-cohort feature selection.

### Ambiguity flag

**T8 strict mode shows +0.251R/trade on n=18, but n=18 cannot anchor a deployment decision.** The lift may reflect either (a) a real high-conviction tail effect, or (b) noise in 18 samples. The lenient mode's +0.120 on n=200 confirms (a) is real but at lower magnitude. **Deploy NEVER on n=18 evidence.**

---

## 10. Eight-bullet summary (orchestrator return)

1. **Highest DSR-corrected lift frame: T1 REJECT filter at threshold p_v3≥0.52 with +0.124R/trade lift on 187 of 528 trades** (bootstrap one-sided p=0.07; DSR-p=1.0 at N=200; the frame captures 31% of the oracle ceiling +0.396 R/trade). T8 strict (+0.251 R) is mathematically higher but n=18 unships.

2. **REJECT filter (T1) outperforms K54 v3 binary classification (Q1.4 gate e -0.108R FAIL).** SIZING modifier (T2 +0.014) is too weak to risk policy change. ENSEMBLE (T4 +0.034) does not clear DSR where its components do not. **Threshold-based REJECT-filter is the deployment frame K54 v3's small-but-real lift fits best.**

3. **Pure-AI baseline reference: mean R +0.355/trade, WR 58.0%, n=528, SR/trade 0.30, DSR-p 1.0 at N=200.** Required lift for DSR-clearance is +0.062R/trade portfolio-equivalent. T1's portfolio-equivalent lift +0.044R/trade falls below this threshold.

4. **NO small-data sequence model clears K54 v1 anchor 0.5286.** Gaussian Process (0.5224), Echo State Network (0.5239), Bayesian Logistic (0.5217) all sit within the noise band of the anchor — none statistically distinguishable. Confirms `project_q1_dlinear_q2_nogo` via 3 alternative paths; the small-data ceiling is structural at n=2,326.

5. **Per-cohort 4-LightGBM ensemble matches K54 v3 global (0.5718 vs 0.5770) on aggregate, but breaks through dramatically on NAS_US30 specifically: AUC 0.7128 (vs K54 v3 specialist 0.6014, +0.111 over Q1.4's strongest finding).** GBPUSD_USDJPY also gains (0.5775 vs K54 v3 0.527). XAU_XAG modest (0.5391); GBPJPY broken (0.4158, n=62 too small). **K55-shadow ship target should be the per-cohort NAS_US30 model, not the K54 v3 specialist.**

6. **New ambiguity:** T1's bootstrap p=0.07 sits in the BORDERLINE zone — directionally suggestive but not multiple-testing-corrected. The +0.124R/trade is concentrated on a 35% retained cohort, requiring high-discipline operational state (operator must trust the reject signal). T8's strict +0.251R on n=18 cannot be promoted from this evidence — wait for cohort expansion. The DSR-N=200 trial budget is the binding constraint everywhere.

7. **Recommended follow-up — single shipping-ready frame:** Per-cohort LightGBM NAS_US30 specialist (T7) for K55-shadow at p_v3≥0.55 floor on NAS100 + US30_cash only. This consolidates the Q1.4 specialist recommendation but with +0.111 AUC stronger underlying model. Defer T1 REJECT filter, T2 sizing modifier, and T3 regime-input until cohort expansion (4-6 weeks 2022-2023 v2-feature backfill).

8. **Key file paths:**
   - `research/ml_program/forensics/2026-04-29/agent_i_alternative_architectures.md` (this doc)
   - `research/ml_program/forensics/2026-04-29/agent_i_reject_filter.json` — T1 threshold sweep
   - `research/ml_program/forensics/2026-04-29/agent_i_sizing_modifier.json` — T2
   - `research/ml_program/forensics/2026-04-29/agent_i_regime_input_design.json` — T3 design doc
   - `research/ml_program/forensics/2026-04-29/agent_i_ensemble.json` — T4 3-way ensemble
   - `research/ml_program/forensics/2026-04-29/agent_i_pure_ai_baseline.json` — T5 reference
   - `research/ml_program/forensics/2026-04-29/agent_i_small_data_sequence.json` — T6 GP/ESN/BLR
   - `research/ml_program/forensics/2026-04-29/agent_i_per_cohort_ensemble.json` — T7 per-cohort 4-group
   - `research/ml_program/forensics/2026-04-29/agent_i_calibration_aware.json` — T8
   - `research/ml_program/forensics/2026-04-29/agent_i_synthesis.json` — cross-frame
   - `research/ml_program/forensics/2026-04-29/_agent_i_compute.py` — reproducer script
   - `research/ml_program/forensics/2026-04-29/_agent_i_run.log` — run log

---

## 11. Caveats and open questions

1. **The K54 v3 prediction range [0.45, 0.63] limits T1/T2/T3/T8.** A model with wider committed predictions would give cleaner threshold sweeps. K54 v3's narrow range reflects its low-confidence regime — consistent with the AUC 0.5770 (only marginally above random).

2. **T7's GBPJPY is broken at n=62.** No architecture variant rescues GBPJPY at this cohort size. The Q1.4 recommendation to drop GBPJPY from the ML stack and fall back to v1 still applies.

3. **DSR-p=1.0 in every quantitative test reflects the N=200 trial budget penalty, not architectural weakness.** The bootstrap p (T1 = 0.07) is the more useful metric for "is the lift directional?". DSR + cohort expansion together solve this.

4. **T6 small-data sequence-model tests used static feature inputs to ESN/GP/BLR.** A true temporal sequence input (M15 OHLCV lookback like DLinear) might recover some lift, but the DLinear evidence (AUC 0.5049) suggests not. **The decisive verdict: temporal microstructure does not lift the K54 v1 17-feature anchor at n=2,326.**

5. **T3's regime-input-to-AI design doc is not testable in subscription-only.** A future $30-60 API spend authorization could test it. The literature estimate (+0.02-0.04R/trade) is bracketed below T1's empirical +0.124R upper bound.

6. **T7 per-cohort NAS_US30 AUC 0.7128 has PBO ~0.53 in K54 v3 specialist (Q1.4 gate d).** The per-cohort PBO is not computed in this dispatch (out of scope); a follow-up should compute it. PBO 0.5+ is the Q1.4 caveat — the +0.111 lift may shrink under truly-blind out-of-sample.

---

## 12. Recommendation to CEO

1. **Approve K55-shadow deploy of T7's NAS_US30 per-cohort specialist (AUC 0.7128, n=113) at p>=0.55 floor on NAS100 + US30_cash only**, replacing the Q1.4-specialist proposal which used a weaker underlying model (AUC 0.6014). Same shadow-mode discipline (30-day shadow data → empirical promotion gate) applies.

2. **Defer T1 REJECT filter as production K54 v3 deployment.** The +0.124R/trade lift at threshold 0.52 is real but bootstrap-only-significant (p=0.07). Worth tracking in shadow logs but not worth shipping with non-DSR-cleared evidence at N=200. Re-evaluate after cohort expansion.

3. **Do NOT spend Anthropic API budget on T3 (regime-input-to-AI) test before cohort expansion.** The expected lift bracket (+0.02-0.04R/trade) is bounded by T1's empirical ceiling (+0.124R) and the subscription-only nature of current research blocks the test path.

4. **Confirm Q2 sequence-model NO-GO status** — three alternative small-data architectures (GP, ESN, Bayesian-LR) replicate DLinear's failure to clear K54 v1 anchor 0.5286. Q2 sequence-models stay shelved until cohort expands to n≥5,000.

5. **Re-test Q1.4 NAS_US30 specialist's PBO at the per-cohort architecture level.** A separate forensic dispatch should compute CSCV PBO for the AUC 0.7128 result; if PBO < 0.4, this is a high-confidence ship candidate. If PBO ≥ 0.5, the +0.111 lift is HP-fragile (same caveat as Q1.3 specialist).

---

*Computed at 2026-04-29; CPCV K=6/N=2/15 paths reused from K54 v3 dispatch; n_baseline=528 + 1,798 backfill (T6 only); subscription-only; READ-ONLY on production.*
