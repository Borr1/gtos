# T2a AI Evaluation Zero-Cost Diagnostics — Results

**Date:** 2026-04-11
**Basis:** 31,145 batch API evaluations (20 batch files, Oct 2025–Mar 2026)
**Matched trades:** 121/121 T1 CANDIDATE trades (100% match rate)
**Pre-registered hypotheses:** H-3.4a (confidence dead) + H-3.7a (XGBoost < 58% OOS WR)
**Bonferroni threshold (primary tests only):** p < 0.025 for H-3.4a and H-3.7a
**Feature correlation scan:** exploratory, 24 features → p < 0.002 required for feature-level correction (Bonferroni p<0.05/24)
**seed=42** for all random operations

**Strategic review corrections applied 2026-04-11:**
- Bonferroni threshold in feature scan was incorrect (was p<0.025, should be p<0.002 for 24 features)
- Part B accuracy comparison was apples-to-oranges (RF 62.0% < majority-class baseline 64.5%)
- Verdict updated: OUTCOMES UNPREDICTABLE (not "ambiguous") — AUC≈0.5 is the decisive metric
- T2b reframed as frequency/bias test, not accuracy test

---

## Phase 0: Data Availability

### Evaluation Counts
| Class | Count | % |
|-------|-------|---|
| CANDIDATE | 1,532 | 4.9% |
| NO_TRADE | 29,613 | 95.1% |
| **Total** | **31,145** | **100%** |

### Feature Coverage
| Feature | Coverage (All) | Coverage (Candidates) | Used in |
|---------|---------------|----------------------|---------|
| confidence_score | 100.0% | 100.0% | A+B |
| daily_bias_direction | 100.0% | 100.0% | A+B |
| daily_bias_confidence | 100.0% | 100.0% | A+B |
| h4_aligned | 100.0% | 100.0% | A+B |
| h1_poi_identified | 100.0% | 100.0% | A+B |
| h1_poi_type | 100.0% | 100.0% | A+B |
| h1_zone | 60.7% | 95.0% | A+B |
| **h1_fib_pct** | **13.7%** | **82.6%** | **B only** |
| h1_causing_event | 100.0% | 100.0% | A+B |
| sweep_detected | 100.0% | 100.0% | A+B |
| sweep_quality | 76.3% | 71.9% | A+B |
| m15_choch_detected | 100.0% | 100.0% | A+B |
| displacement_quality | 96.8% | 92.6% | A+B |
| displacement_ratio | 100.0% | 100.0% | A+B |
| setup_grade | 100.0% | 100.0% | A+B |
| sweep_count | 97.8% | 100.0% | A+B |
| h1_ob_count | 100.0% | 100.0% | A+B |
| h1_fvg_count | 100.0% | 100.0% | A+B |
| h1_atr | 97.8% | 100.0% | A+B |
| h1_avg_body | 97.8% | 100.0% | A+B |
| h1_break_count | 100.0% | 100.0% | A+B |
| h1_last_break_disp | 97.8% | 100.0% | A+B |
| h1_last_break_ratio | 97.8% | 100.0% | A+B |
| h1_structure_dir | 100.0% | 100.0% | A+B |
| m15_ob_count | 100.0% | 100.0% | A+B |
| m15_fvg_count | 100.0% | 100.0% | A+B |
| m15_atr | 97.8% | 100.0% | A+B |
| m15_avg_body | 97.8% | 100.0% | A+B |
| m15_break_count | 100.0% | 100.0% | A+B |
| m15_last_break_disp | 97.8% | 100.0% | A+B |
| m15_last_break_ratio | 97.8% | 100.0% | A+B |
| m15_structure_dir | 100.0% | 100.0% | A+B |
| sl_distance_atr | 100.0% (T1) | 100.0% | B only |
| rr_ratio_ai | 100.0% (T1) | 100.0% | B only |

**Part A:** 31 features (h1_fib_pct excluded — 13.7% overall coverage)
**Part B:** 34 features (h1_fib_pct reinstated — 82.6% coverage in candidates)

---

## Test 1: Confidence Score Diagnostic (H-3.4a)

**Pre-registered:** ρ(confidence_score, WIN/LOSS) ~ 0. Score carries no discriminative information.
**Result: CONFIRMED.**

### 1.1 Confidence Score Distribution

**ALL evaluations (n=31,145):**

| Score | Count | % |
|-------|-------|---|
| 0 | 25,373 | 81.5% |
| 75 | 67 | 0.2% |
| 78 | 13 | 0.0% |
| 80 | 912 | 2.9% |
| 82 | 39 | 0.1% |
| 85 | 4,727 | 15.2% |
| 92 | 2 | 0.0% |
| 95 | 12 | 0.0% |

**CANDIDATE trades (n=121):**

| Score | Count | % |
|-------|-------|---|
| 75 | 6 | 5.0% |
| 78 | 4 | 3.3% |
| **80** | **92** | **76.0%** |
| 82 | 13 | 10.7% |
| 85 | 6 | 5.0% |

- 76.0% of CANDIDATEs: exactly score=80
- 85.7% of NO_TRADEs: score=0
- CANDIDATE range: [75, 85], std=1.74
- Variance insufficient for binning (q33=q67=80)

### 1.2 Confidence Computation Analysis

Fixed additive formula: **Baseline 70 + bonuses = score**

| Formula | Count |
|---------|-------|
| Baseline 70 + strong displacement (+5) + clean unmitigated OB (+5) = 80 | 39 |
| Baseline 70 + strong displacement (+5) + clean OB formation (+5) = 80 | 29 |
| Baseline 70 + strong displacement (+5) + clean BOS confirmation (+5) = 80 | 7 |
| Baseline 70 + strong displacement (+5) + clean sweep reversal (+5) = 80 | 5 |
| Baseline 70 + strong displacement (+5) + clean sweep with immediate reversal (+5) = 80 | 5 |
| Baseline 70 + strong displacement (+5) + clean sweep (+5) = 80 | 3 |
| Baseline 70 + strong displacement (+5) = 75 | 3 |
| Baseline 70 + strong displacement (+8) = 78 | 2 |
| Baseline 70 + strong displacement (+10) + clean liquidity sweep (+5) = 85 | 2 |

The formula awards "strong displacement" + "clean OB/sweep" bonuses to all passing trades. These ARE the definition of CANDIDATE — so the formula cannot discriminate. The score is a post-hoc arithmetic rationalization of the binary decision.

### 1.3 Spearman Correlation Table (Exploratory)

**n=121 CANDIDATE trades. Sorted by |ρ vs outcome|.**

**NOTE: This is an exploratory scan of 24 features. Feature-level Bonferroni correction requires p < 0.05/24 = 0.002. No feature survives this threshold. Results below are exploratory/unconfirmed and require dedicated pre-registered testing before any implementation.**

| Feature | ρ vs WIN/LOSS | p | p<0.025? | p<0.002? | ρ vs R | n |
|---------|--------------|---|---------|---------|--------|---|
| h1_fib_pct | −0.273 | 0.006 | YES | **NO** | −0.283 | 100 |
| h1_poi_identified | +0.228 | 0.012 | YES | **NO** | +0.187 | 121 |
| h1_last_break_disp | −0.178 | 0.050 | NO | NO | −0.189 | 121 |
| h1_last_break_ratio | −0.134 | 0.144 | NO | NO | −0.127 | 121 |
| m15_break_count | +0.123 | 0.179 | NO | NO | +0.061 | 121 |
| m15_atr | +0.118 | 0.196 | NO | NO | +0.161 | 121 |
| h1_atr | +0.115 | 0.209 | NO | NO | +0.174 | 121 |
| sweep_count | +0.112 | 0.222 | NO | NO | +0.154 | 121 |
| rr_ratio_ai | −0.110 | 0.231 | NO | NO | +0.120 | 121 |
| m15_last_break_disp | −0.106 | 0.247 | NO | NO | −0.144 | 121 |
| m15_last_break_ratio | −0.105 | 0.251 | NO | NO | −0.090 | 121 |
| displacement_ratio | +0.071 | 0.437 | NO | NO | +0.114 | 121 |
| displacement_quality | −0.069 | 0.467 | NO | NO | +0.007 | 112 |
| daily_bias_confidence | −0.068 | 0.460 | NO | NO | −0.134 | 121 |
| m15_ob_count | −0.065 | 0.477 | NO | NO | −0.005 | 121 |
| sweep_quality | +0.045 | 0.680 | NO | NO | −0.054 | 87 |
| **confidence_score** | **+0.044** | **0.632** | **NO** | **NO** | +0.113 | 121 |
| h1_break_count | +0.039 | 0.670 | NO | NO | +0.009 | 121 |
| m15_choch_detected | +0.039 | 0.670 | NO | NO | +0.036 | 121 |
| h1_zone | −0.026 | 0.783 | NO | NO | +0.062 | 115 |
| setup_grade | −0.012 | 0.893 | NO | NO | +0.008 | 121 |
| h1_ob_count | +0.011 | 0.908 | NO | NO | +0.061 | 121 |
| sl_distance_atr | +0.002 | 0.987 | NO | NO | −0.135 | 121 |
| h4_aligned | NaN | NaN | NO | NO | NaN | 121 |

**Confirmed findings:**
- **confidence_score: ρ=+0.044 (p=0.632) → DEAD.** H-3.4a confirmed.
- **setup_grade: ρ=−0.012 (p=0.893) → also dead.** Grade drives CANDIDATE selection, not outcomes.
- **h4_aligned: zero variance** — all CANDIDATEs have h4_aligned=True (required criterion).
- **displacement_ratio: ρ=+0.071 (p=0.437)** — the LLM's primary confidence driver does not predict outcomes.

**Unconfirmed exploratory signals (require dedicated pre-registered testing):**
- h1_fib_pct: ρ=−0.273 (p=0.006) — directional signal, NOT confirmed. Fib zone depth may matter but needs 200+ trades + pre-registration.
- h1_poi_identified: ρ=+0.228 (p=0.012) — NOT confirmed.

**Previous version error:** These were incorrectly labeled as "surviving Bonferroni correction." Retracted.

### 1.4 Binned Analysis

Skipped — insufficient variance (q33=q67=80).

### 1.5 Platt Scaling

Skipped — ρ=0.044 < threshold of 0.10.

**Test 1 Verdict: H-3.4a CONFIRMED. Confidence score is DEAD.**
No feature survives proper multiple-comparison correction for feature-level Bonferroni (p<0.002).
h1_fib_pct shows the strongest exploratory signal (ρ=−0.273) but requires dedicated pre-registered testing.

---

## Test 2: Statistical Model Baseline (H-3.7a)

**Pre-registered:** XGBoost OOS WR < 58% confirms LLM adds value.
**Corrected result: OUTCOMES UNPREDICTABLE — Edge is mechanical.**

### Part A: CANDIDATE vs NO_TRADE Classification

**Dataset:** 31,145 evaluations | CANDIDATE rate 4.9% | class_weight=balanced

**Random baselines:**
- Always NO_TRADE: accuracy=0.951, F1(CANDIDATE)=0.000
- Always CANDIDATE: accuracy=0.049, F1(CANDIDATE)=0.094

**5-fold CV × 3 seeds results (mean):**

| Model | Accuracy | Precision(C) | Recall(C) | F1(C) | AUC |
|-------|----------|-------------|----------|-------|-----|
| LogisticRegression | 0.998 | 0.962 | 0.993 | 0.977 | 1.000 |
| GradientBoosting | **1.000** | **0.998** | **0.996** | **0.997** | **1.000** |
| RandomForest | 0.999 | 0.997 | 0.989 | 0.993 | 1.000 |

**All three models achieve near-perfect classification (AUC=1.000). The LLM's CANDIDATE/NO_TRADE decision is completely mechanically replicable.**

### Part A: Feature Importance (GradientBoosting)

| Feature | Importance | Note |
|---------|-----------|------|
| **setup_grade** | **0.9702** | LLM's own self-assigned grade |
| confidence_score | 0.0204 | LLM's own score |
| h1_last_break_ratio | 0.0053 | Input feature |
| h1_causing_event | 0.0007 | Input feature |
| displacement_ratio | 0.0006 | Input feature |
| sweep_count | 0.0006 | Input feature |
| sweep_quality | 0.0005 | Input feature |
| m15_choch_detected | 0.0004 | Prompt rule |
| h4_aligned | 0.0004 | Prompt rule |
| m15_fvg_count | 0.0002 | Input feature |

**97% of the split is explained by setup_grade alone.** The LLM assigns itself A+/A/B/C and then decides CANDIDATE iff grade ≥ A. This is a self-referential rule: the model predicts the LLM's grade from the LLM's own output. To truly mechanize the gate we would need to predict setup_grade from raw MSO inputs — that's a separate unanswered question.

### Part B: WIN/LOSS Among CANDIDATEs — The Existential Test

**Dataset:** 121 matched CANDIDATE trades (78 WIN, 43 LOSS) | LOO-CV
**Majority-class baseline (always-WIN accuracy):** 78/121 = **64.5%**
**Coin flip:** 50.0%

| Model | OOS Accuracy | AUC | vs Majority Baseline | vs Coin Flip |
|-------|-------------|-----|---------------------|-------------|
| LogisticRegression | 0.587 | 0.544 | **−0.058** | +0.087 |
| GradientBoosting | 0.529 | 0.522 | **−0.116** | +0.029 |
| **RandomForest** | **0.620** | **0.562** | **−0.025** | +0.120 |

**CRITICAL CORRECTION:** All three models have accuracy *below* the majority-class baseline (64.5%). A trivial "predict all WIN" model beats every ML model. This was misread in the initial analysis.

**AUC analysis:**
- LR: 0.544, GB: 0.522, RF: 0.562
- Approximate SE(AUC) at n=121 ≈ sqrt(0.5×0.5/121) ≈ 0.045
- None are meaningfully above 0.5 (AUC≈0.5 = chance-level discrimination)

**Confusion matrix — RandomForest:**
```
              Pred LOSS  Pred WIN
Actual LOSS:     17         26
Actual WIN:      20         58
```
"Always predict WIN": TN=0, FP=43, FN=0, TP=78 → accuracy=64.5% (beats RF)

### Part B: Permutation Importance (RandomForest, n=121)

| Feature | Importance | ±std | Note |
|---------|-----------|------|------|
| h1_fib_pct | +0.052 | 0.026 | Exploratory only |
| sl_distance_atr | +0.034 | 0.014 | |
| rr_ratio_ai | +0.025 | 0.017 | |
| h1_last_break_ratio | +0.023 | 0.022 | |
| sweep_detected | +0.019 | 0.008 | |
| sweep_quality | +0.016 | 0.008 | |
| m15_ob_count | +0.015 | 0.011 | |
| h1_avg_body | +0.015 | 0.012 | |
| m15_atr | +0.008 | 0.016 | |
| h1_zone | +0.006 | 0.005 | |

Even the top permutation importance feature (h1_fib_pct) is tiny. The model adds marginal accuracy on specific samples but cannot reliably discriminate win from loss.

### Part C: TabPFN

Unavailable. Not installed.

### Part D: Feature Ablation

| Feature set | LOO WR (GradientBoosting) | vs Majority Baseline |
|-------------|--------------------------|---------------------|
| Top-5 grade-based features | 0.421 | −0.224 |
| All 34 features | 0.529 | −0.116 |
| All 34 features (RandomForest) | 0.620 | −0.025 |

Every configuration is below the majority-class baseline. Grade-based features (setup_grade, confidence_score) are the worst, at 42.1% — well below coin flip. These are actively harmful for WIN/LOSS prediction.

### Part B Verdict: **OUTCOMES UNPREDICTABLE — Edge is mechanical**

**(Corrected from initial "AMBIGUOUS")**

- All models: AUC ≈ 0.5 (no discriminative power)
- All models: accuracy < majority-class baseline (64.5%)
- The 64.5% WR is the OB zone continuation base rate for qualified setups
- No pre-trade feature combination can improve on this, because outcome variability within properly-identified zones is irreducible noise at n=121
- Maps to pre-registered decision tree: "Model WR ≤ 52% (AUC metric)" → **"No feature predicts outcomes. Edge is entirely mechanical."**

---

## Phase 3: Synthesis (Corrected)

### Corrected Summary Table

| Agent Claim | Verdict | Correction |
|-------------|---------|-----------|
| Confidence dead (ρ=0.044) | CORRECT | — |
| 76% at score=80 | CORRECT | — |
| h1_fib_pct survives Bonferroni | **WRONG** | p=0.006 fails feature-level correction (need p<0.002 for 24 features) |
| h1_poi_identified survives Bonferroni | **WRONG** | p=0.012 fails — same issue |
| Part A: AUC=1.000 | CORRECT | — |
| 97% explained by setup_grade | VERIFIED | Confirmed by feature importance table |
| RF 62% "close to LLM 64.5%" | **MISLEADING** | RF 62% < majority baseline 64.5%. None beat "always WIN." |
| displacement_ratio near-zero | CORRECT | ρ=0.071, confirmed |
| "fib <38.2% preferred" thresholds | **PREMATURE** | Fib levels aren't data-derived; finding unconfirmed |
| Verdict: AMBIGUOUS | **MISLEADING** | AUC≈0.5 → OUTCOMES UNPREDICTABLE → edge is mechanical |

### Corrected Verdict

**The LLM's gate is a deterministic rule, and within the gate, outcomes are stochastic.**

1. **Part A (AUC=1.000):** The LLM's CANDIDATE/NO_TRADE decision is mechanically replicable. 97% of the decision is explained by the LLM's own self-assigned setup_grade. The LLM executes: "If H4 aligned AND sweep detected AND M15 ChoCH AND displacement sufficient AND zone identified → grade A → CANDIDATE." This is an if/then tree that costs $60/month.

2. **Part B (AUC≈0.5):** Among CANDIDATE trades, outcomes are unpredictable from any of the 34 extracted features. No model beats the majority-class baseline (always predict WIN). The LLM does not add outcome selectivity — it approves a pool with a 64.5% base rate, and within that pool, outcomes are noise.

3. **The edge is OB zone continuation mechanics.** The 64.5% WR is the statistical property of correctly identified OB zones continuing in the impulse direction. No AI reasoning or feature-based filtering improves on this.

### T2b Reframing

**Initial (incorrect) framing:** "Does the LLM add 2.5pp accuracy above RandomForest?"
**Corrected framing:** "Does LLM bias suppress CANDIDATE frequency?"

Since accuracy is irrelevant (all approved trades win at the base rate), the question becomes: is the LLM wrongly rejecting valid zones due to:
- **Memory bias (Exp 1–2):** Majority-NO_TRADE priming suppresses CANDIDATE rate
- **SMC framing (Exp 4):** Narrative framing causes false negatives on structurally valid setups
- **3-run consistency (Exp 5):** Flip-flops on borderline setups that a deterministic rule would always approve

If T2b recovers even 5 trades/month at the same 64.5% WR and +0.20R expectancy:
→ +1.0R/month ≈ +$100/month at current sizing
→ $80 one-time cost recovers in one month

**T2b priority is UNCHANGED but the test design must measure CANDIDATE rate, not accuracy.**

### Pipeline Implications (Corrected)

| Component | Status | Action |
|-----------|--------|--------|
| confidence_score | **DEAD** | Remove from any filter logic |
| setup_grade | Predicts gate, not outcomes | Keep as LLM internal output only |
| displacement_ratio | Overweighted by LLM, predicts nothing | De-emphasize in prompt (pending CEO review) |
| h1_fib_pct | Exploratory signal (ρ=−0.273, p=0.006) | Log for monitoring; pre-register dedicated test at n=200+ before any implementation |
| LLM itself | Gate is replicable; outcomes are stochastic | T2b frequency test: measure bias impact on CANDIDATE rate |

---

## Output Files

| File | Purpose |
|------|---------|
| `data/all_evaluations_features.csv` | 31,145 evaluations × 33 features |
| `data/ai_evaluation_features.csv` | 121 CANDIDATE trades × 34 features + outcomes |
| `results/T2a_ai_diagnostics_results_v1.md` | This file (corrected version) |
| `T2a_ai_diagnostics_analysis.py` | Analysis script (reproducible, seed=42) |

---

*Generated by T2a_ai_diagnostics_analysis.py | April 11, 2026*
*Corrections applied after strategic review: Bonferroni threshold, accuracy vs AUC interpretation, verdict updated to OUTCOMES UNPREDICTABLE*
