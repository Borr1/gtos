# T2a — AI Evaluation Zero-Cost Diagnostics (H-3.4a + H-3.7a)
## For: Claude Code execution agent (Sonnet, max effort)
## Date: April 11, 2026
## Written by: Strategic Research Advisor
## Basis: phase1_ai_evaluation_papers_v1.md (96 papers, 7 hypotheses)
## Data discovery verified by: T1 analysis script (121/129 trades matched)

---

## Prerequisites

Before starting, ensure the following are available:

```bash
pip install scikit-learn pandas scipy numpy
# Optional (may fail — skip if so):
pip install tabpfn
```

**Required skills/tools:** Python data analysis, JSON parsing, ML model training (scikit-learn), statistical testing. No API keys needed — this is analysis-only on existing data.

**Codebase reading required BEFORE running tests:**
1. Read `knowledge_base/index/_trade_index.json` — understand trade fields
2. Read one `*_raw_results.json` file in `knowledge_base_backtest/batch_api/` — understand AI decision JSON structure (field names, nesting)
3. Read `research/academic_pipeline/data/entry_engineering_dataset.csv` — T1 dataset, reuse the trade matching

---

## Overview

Run 2 zero-cost diagnostic tests on existing GTOS data. These require NO API calls — only analysis of batch trade evaluations that already exist on disk. Together they answer the two most important questions from the AI evaluation literature search:

1. **H-3.4a:** Does the confidence score carry ANY discriminative signal?
2. **H-3.7a:** Does a simple statistical model match the LLM's 65% WR?

**These are the existential tests.** If confidence is dead AND a free model matches the LLM, the entire $60/month AI component is overhead. If confidence is dead BUT the free model underperforms, the LLM's spatial reasoning justifies its cost. Either outcome drives immediate action.

**Bonferroni correction:** 2 primary tests → p < 0.025 significance threshold.
**Practical significance:** Effects < 2pp WR or < 0.05R are "detectable but negligible."

---

## Phase 0: Data Extraction

### CRITICAL: Data structure already discovered by T1

The T1 entry engineering analysis (April 11, 2026) already mapped the full data layout. Use these findings directly — do NOT re-discover from scratch.

**Batch API directory:** `knowledge_base_backtest/batch_api/`
Contains multiple batch runs, each with 3 key file types:
- `*_full_prompts.json` — List of dicts. Each entry has: `custom_id`, `date`, `candle_time`, `kill_zone`, `prompt.user_message` (the full MSO text sent to Claude)
- `*_raw_results.json` — Dict keyed by `{date}_{kill_zone}_{time}`. Each value has `text` containing the AI decision JSON
- `*_results.json` — Processed results

**T1 matched 121/129 trades to AI decisions.** The T1 dataset is at `research/academic_pipeline/data/entry_engineering_dataset.csv` and contains trade_id, outcome, r_multiple, mfe_r, mae_r, entry_price_ai, stop_loss, take_profit_1, sl_distance_atr, rr_ratio_ai for 121 trades with data.

### Step 0.1: Load T1 dataset as foundation

```python
import pandas as pd
t1_data = pd.read_csv('research/academic_pipeline/data/entry_engineering_dataset.csv')
# Already has: trade_id, outcome, r_multiple, sl_distance_atr, rr_ratio_ai
# These are bonus features for the baseline model (from T1 findings)
```

### Step 0.2: Extract features from AI decision JSON

For EVERY evaluation (CANDIDATE and NO_TRADE), the raw results JSON contains a structured reasoning block. Parse these fields:

**From the decision JSON (verified structure from batch data):**

| Field | Path in JSON | Type | Available for |
|-------|-------------|------|---------------|
| decision | `.decision` | categorical | ALL |
| confidence_score | `.confidence_score` | numeric | ALL |
| confidence_computation | `.confidence_computation` | text | ALL |
| framework | `.framework` | categorical | ALL |
| daily_bias_direction | `.reasoning.daily_bias.direction` | categorical (bullish/bearish/ranging) | ALL |
| daily_bias_confidence | `.reasoning.daily_bias.confidence` | categorical (high/medium/low) | ALL |
| h4_aligned | `.reasoning.h4_alignment.aligned` | binary | ALL |
| h1_poi_identified | `.reasoning.h1_setup.poi_identified` | binary | ALL |
| h1_poi_type | `.reasoning.h1_setup.poi_type` | categorical (OB/FVG/none) | ALL |
| h1_zone | `.reasoning.h1_setup.zone` | categorical (premium/discount/eq) | ALL |
| h1_fib_pct | `.reasoning.h1_setup.fib_retracement_pct` | numeric | ALL |
| sweep_detected | `.reasoning.liquidity_sweep.detected` | binary | ALL |
| sweep_quality | `.reasoning.liquidity_sweep.sweep_quality` | categorical | ALL |
| m15_choch_detected | `.reasoning.m15_confirmation.choch_detected` | binary | ALL |
| displacement_quality | `.reasoning.m15_confirmation.displacement_quality` | categorical | ALL |
| displacement_ratio | `.reasoning.m15_confirmation.displacement_candle_body_vs_avg_ratio` | numeric | ALL |
| setup_grade | `.reasoning.setup_grade` | ordinal (A+/A/B/C) | ALL |

**From the MSO text (parse from `prompt.user_message`):**

| Field | Parse method | Type |
|-------|-------------|------|
| h1_ob_count | Count lines matching "bullish/bearish X.XXXXX-X.XXXXX" under "Unmitigated OBs" | integer |
| m15_ob_count | Same for M15 section | integer |
| h1_fvg_count | Count under "Unfilled FVGs" in H1 section | integer |
| m15_fvg_count | Same for M15 | integer |
| sweep_count | Number in "Sweeps (N)" header | integer |
| h1_atr | Parse "ATR(14): X.XXXXX" in H1 section | numeric |
| m15_atr | Same for M15 | numeric |
| h1_avg_body | Parse "Avg body: X.XXXXX" in H1 | numeric |
| m15_avg_body | Same for M15 | numeric |
| h1_structure_dir | Parse "Structure: bullish/bearish" in H1 header | categorical |
| m15_structure_dir | Same for M15 | categorical |
| h1_break_count | Count of breaks listed in H1 section | integer |
| h1_last_break_displacement | Last break's `disp=True/False` | binary |
| h1_last_break_ratio | Last break's `ratio=X.X` | numeric |
| kill_zone | From entry metadata | categorical |

**Total: ~30 extractable features per evaluation.** This is the FULL feature space the LLM sees.

### Step 0.3: Build unified datasets

**Phase 0.3a: Match evaluations to trade outcomes**

For each CANDIDATE trade in the trade index (129 trades):
1. Parse trade_id to get date, kill_zone, symbol
2. Search raw_results files for matching key pattern: `{date}_{kill_zone}_{time}`
3. T1 already matched 121/129 — reuse that mapping if the T1 script's matching logic is accessible, or re-match using the same approach

**Phase 0.3b: Extract NO_TRADE evaluations**

From the SAME raw results files, extract all evaluations where `decision == "NO_TRADE"`. These are the negative examples for Part A. There should be thousands — T1 found 1271 CANDIDATE decisions out of many more total evaluations.

Target: ALL extractable NO_TRADE evaluations (expect 5000-10000+). More negative examples = better class-imbalance handling.

**Phase 0.3c: Build DataFrames**

```python
# DataFrame 1: All evaluations with features (for Part A)
# Columns: eval_id, date, symbol, kill_zone, decision (CANDIDATE=1/NO_TRADE=0),
#           + all 30 extracted features

# DataFrame 2: CANDIDATE outcomes (for Part B + H-3.4a)  
# Columns: trade_id, date, symbol, outcome, r_multiple,
#           confidence_score, confidence_computation,
#           + all 30 extracted features
#           + sl_distance_atr, rr_ratio_ai from T1 dataset
```

### Step 0.4: Report data availability

Before running tests, report:
- Total evaluations extracted (CANDIDATE + NO_TRADE)
- Class distribution: n_CANDIDATE, n_NO_TRADE, ratio
- Feature coverage table: for each of the ~30 features, what % of evaluations have parseable data?
- Drop any feature with < 50% coverage
- Report final feature count used

**CRITICAL CHECK:** Distribution of confidence_score across ALL evaluations. Previous claim was "98% get 80." The actual data may show more variance — one verified CANDIDATE has confidence=85 with computation breakdown "Baseline 70 + strong M15 displacement (+10) + clean H1 OB retest (+5) = 85". Report the actual distribution before proceeding.

---

## Test 1: Confidence Score Diagnostic (H-3.4a)

**Hypothesis:** The current raw confidence score has Spearman ρ < 0.05 with actual trade outcomes among CANDIDATE trades.

**Pre-registered prediction:** ρ ~ 0. The confidence score carries zero discriminative information.

### Method

1. **Distribution analysis (FULL — all evaluations):**
   - Histogram of confidence_score across ALL evaluations (CANDIDATE + NO_TRADE)
   - Histogram of confidence_score among CANDIDATE trades only
   - What % of CANDIDATEs are exactly 80? What's the full range?
   - What % of NO_TRADEs have confidence=0?
   - If >90% of CANDIDATEs have the same score: variance is trivially insufficient

2. **Confidence computation analysis:**
   - Parse `confidence_computation` text to extract the breakdown formula
   - Identify what factors contribute to the confidence score (displacement, zone quality, etc.)
   - This tells us whether confidence is computed from the same features we're extracting — if so, it's redundant

3. **Spearman correlations (among 121+ matched CANDIDATE trades):**
   - ρ(confidence_score, binary_outcome) — does confidence predict WIN/LOSS?
   - ρ(confidence_score, r_multiple) — does confidence predict magnitude?
   - ρ(setup_grade_encoded, binary_outcome) — comparison signal
   - ρ(displacement_quality_encoded, binary_outcome) — comparison signal
   - ρ(displacement_ratio, binary_outcome) — the continuous version
   - ρ(h1_fib_pct, binary_outcome) — zone position
   - ρ(rr_ratio_ai, binary_outcome) — T1 bonus finding (R:R matters?)
   - ρ(sl_distance_atr, binary_outcome) — T1 bonus finding (SL width)
   - Report ALL correlations in a single ranked table

4. **Binned analysis (if confidence has variance):**
   - If confidence has ≥ 3 distinct values with n ≥ 5 each:
   - Bin by confidence level, compute WR and mean_R per bin
   - Wilson CI for WR, bootstrap CI (seed=42, n=10000) for mean_R
   - Kruskal-Wallis across bins on r_multiple

5. **Platt scaling (if ρ > 0.10):**
   - If confidence shows ANY signal (ρ > 0.10): apply Platt scaling
   - Use leave-one-out CV on 121+ trades
   - Report calibrated probabilities and ECE (Expected Calibration Error)
   - Compare calibration curve: raw confidence vs Platt-scaled vs actual frequency

### Decision gate

- **ρ < 0.05 for confidence:** Dead. No signal to calibrate.
- **ρ 0.05-0.10:** Marginal. Check if another feature (setup_grade, displacement_ratio) does better. If yes, replace confidence with that feature.
- **ρ > 0.10:** Surprising and immediately actionable. Apply Platt scaling.
- **If any OTHER feature has ρ > 0.15:** Report it as the real quality signal, regardless of confidence result.

### Output
- Full confidence distribution table (value → count) for CANDIDATEs and NO_TRADEs
- Ranked correlation table: all features × outcome, sorted by |ρ|
- Binned WR table (if variance exists)
- Platt scaling results (if applicable)
- Verdict: dead / marginal / alive / **replaced by [feature]**

---

## Test 2: XGBoost Baseline — The Existential Test (H-3.7a)

**Hypothesis:** XGBoost trained on the ~30 extractable features achieves < 58% OOS WR on WIN/LOSS prediction among CANDIDATEs, confirming the LLM's spatial reasoning adds value beyond simple feature thresholds.

**Pre-registered prediction:** Based on tabular data literature (Grinsztajn 2022, Hollmann 2025), XGBoost should achieve 60-65% on CANDIDATE/NO_TRADE classification. For WIN/LOSS among CANDIDATEs, the prediction is less clear — if features predict outcomes as well as the LLM, the LLM is $60/month of overhead.

### Method

**Part A: CANDIDATE vs NO_TRADE classification**

This tests: can a simple model replicate the LLM's filtering decision?

1. Dataset: ALL evaluations with extractable features + decision label (CANDIDATE=1, NO_TRADE=0)
2. Encode categoricals:
   - setup_grade: A+=4, A=3, B=2, C=1
   - displacement_quality: strong=3, moderate=2, weak=1, none=0
   - daily_bias_direction: use one-hot (bullish, bearish, ranging)
   - h1_zone: discount=1, eq=0.5, premium=0
   - kill_zone: one-hot
   - All binary features: True=1, False=0
3. Handle missing values:
   - Drop features with < 50% coverage
   - Impute remaining: mode (categorical), median (numeric)
4. Handle class imbalance (CANDIDATE rate ~10%):
   - Use `class_weight='balanced'` in all models
   - Report BOTH accuracy and F1 for the minority class (CANDIDATE)
   - Also report precision and recall separately — precision tells us "when the model says CANDIDATE, is it right?" and recall tells us "does it catch all real CANDIDATEs?"

5. **Models to run:**

   ```python
   from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
   from sklearn.linear_model import LogisticRegression
   from sklearn.model_selection import StratifiedKFold, cross_val_predict
   from sklearn.metrics import classification_report, roc_auc_score
   from sklearn.utils.class_weight import compute_sample_weight
   
   cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
   
   models = {
       'LogisticRegression': LogisticRegression(
           random_state=42, max_iter=1000, class_weight='balanced'
       ),
       'GradientBoosting': GradientBoostingClassifier(
           n_estimators=100, max_depth=3, learning_rate=0.1,
           random_state=42, subsample=0.8
       ),
       # NOTE: GradientBoostingClassifier does NOT have class_weight param.
       # Use compute_sample_weight('balanced', y_train) and pass to .fit():
       #   weights = compute_sample_weight('balanced', y_train)
       #   model.fit(X_train, y_train, sample_weight=weights)
       'RandomForest': RandomForestClassifier(
           n_estimators=200, max_depth=5, random_state=42,
           class_weight='balanced'
       ),
   }
   ```

   For each model:
   - Stratified 5-fold CV (repeated 3x with seeds 42, 43, 44 for stability estimate)
   - Report: accuracy, precision(CANDIDATE), recall(CANDIDATE), F1(CANDIDATE), AUC
   - Report feature importances (GradientBoosting and RandomForest)

6. **Random baselines:**
   - "Always NO_TRADE": accuracy = 1 - CANDIDATE_rate (expect ~89.7%)
   - "Always CANDIDATE": accuracy = CANDIDATE_rate (expect ~10.3%)
   - Any useful model must have F1(CANDIDATE) > 0 and AUC > 0.5

7. **Feature importance analysis:**
   - Rank all features by GradientBoosting importance
   - Identify top 5 features driving the CANDIDATE/NO_TRADE split
   - Compare to what the LLM claims to evaluate (reasoning text)
   - Check: are the top features "obvious" (e.g., m15_choch_detected is trivially required by the prompt rules)? If the model is just learning hard-coded prompt rules, it's not replicating reasoning — it's replicating logic.

**Part B: WIN/LOSS prediction among CANDIDATEs — THE EXISTENTIAL TEST**

This is the test that matters. Part A shows if a model can mimic the LLM's decision. Part B shows if ANYTHING predicts which CANDIDATEs win.

1. Dataset: 121+ matched CANDIDATE trades with features + outcome (WIN=1, LOSS=0)
2. **Add T1-derived features:** sl_distance_atr, rr_ratio_ai (from T1 dataset)
3. **WARNING:** n~121. Leave-one-out CV is mandatory.

   ```python
   from sklearn.model_selection import LeaveOneOut
   
   loo = LeaveOneOut()
   # For each model: collect OOS predictions for all 121 trades
   ```

4. Report:
   - OOS WR for each model (= accuracy on binary WIN/LOSS)
   - AUC for each model
   - Comparison to observed WR (65% is the LLM benchmark)
   - Confusion matrix for each model

5. **Permutation importance on Part B:**
   - For the best-performing model, run permutation importance
   - This tells us which features PREDICT OUTCOMES, not just which features predict the AI's decision
   - If no feature has permutation importance > 0: outcomes are unpredictable from these features (the edge is in zone detection, not in any individual feature)

**Part C: TabPFN (if installable)**

```bash
pip install tabpfn 2>/dev/null
```

If it installs: run on both Part A and Part B with same CV schemes. TabPFN's advantage is at n < 10K with no hyperparameter tuning. If it fails to install, note "TabPFN unavailable" and move on — LogisticRegression + GradientBoosting + RandomForest provide a solid baseline.

**Part D: Feature ablation study**

After Part A and B are complete:
1. Identify the top 5 features from Part A (feature importance)
2. Run Part B again using ONLY those top 5 features
3. Run Part B again using ALL ~30 features
4. Compare: does having more features help or hurt WIN/LOSS prediction?
5. If more features hurts: overfitting at n=121, confirming the curse-of-dimensionality concern from Q-1.5

### Decision gates

**For Part A (CANDIDATE/NO_TRADE):**
- F1(CANDIDATE) ≥ 0.80: The LLM's filtering is mechanically replicable. Check Part A feature importance — if top features are prompt-rule features (m15_choch, h1_poi_identified), the model is just learning the prompt's hard-coded rules, which means the LLM's contribution is executing those rules, not independent reasoning.
- F1(CANDIDATE) < 0.50: The LLM uses information not captured in these features.
- 0.50–0.80: Partial replication. Some of the LLM's filtering is feature-based, some is not.

**For Part B (WIN/LOSS) — the one that matters:**
- Model WR ≥ 62% OOS: Features predict outcomes nearly as well as the LLM. LLM is likely overhead for the tabular component. Spatial reasoning adds ≤ 3pp.
- Model WR 58-62% OOS: Ambiguous zone. The LLM may add 3-7pp through non-tabular reasoning. Extend to 200+ trades before deciding.
- Model WR < 58% OOS: Features alone don't predict outcomes. Either (a) the LLM's spatial reasoning adds genuine value, or (b) outcomes are unpredictable from any pre-trade features (the edge is purely in zone detection mechanics, not in filtering). Check: is the model WR close to random (50%) or close to the base rate (65%)? If close to 50%, features are noise. If close to base rate minus a few pp, the LLM adds a small increment.
- Model WR ≤ 52% (not significantly different from coin flip): No feature predicts outcomes. The edge is entirely mechanical (zone continuation at 70%+ minus the ~5pp dilution from wrong-direction entries). This would mean both the LLM AND the features are overhead — the system works because OB zones work, period.

### Output
- Data availability report: total evaluations, features extracted, coverage table
- Part A results table: model × {accuracy, precision, recall, F1, AUC}
- Part A feature importance ranking (top 10)
- Part A interpretation: are top features trivially prompt-rules or genuine reasoning signals?
- Part B results table: model × {OOS WR, AUC} with LOO-CV
- Part B comparison to 65% LLM benchmark and 50% coin flip
- Part B permutation importance: which features predict actual outcomes?
- Part D ablation: top-5 vs all features comparison
- TabPFN results or "unavailable" note
- **Verdict: LLM overhead / LLM justified / ambiguous / outcomes unpredictable**

---

## Phase 3: Synthesis

Write a synthesis that addresses BOTH the CEO and the execution pipeline:

1. **Confidence score verdict:** Dead / marginal / alive? If dead, what's the best alternative signal from the correlation table? Is ANY pre-trade feature predictive of outcome?

2. **LLM justification verdict:** Based on Part B, does the $60/month LLM add measurable value above a free statistical model?

3. **The critical distinction:** Separate two questions that are often conflated:
   - "Can a model replicate the LLM's DECISION?" (Part A — this is about whether the filtering logic can be mechanized)
   - "Can a model predict OUTCOMES?" (Part B — this is about whether any pre-trade information predicts which trades win)
   - If Part A says "yes, easily" and Part B says "no, nothing predicts outcomes": the LLM's decision process is replicable but its decisions don't add WR above the mechanical OB zone continuation rate. This means the edge is zone detection, not the filter.

4. **Implementation recommendations:**
   - If LLM is overhead: propose replacement architecture (XGBoost filter + rule-based entry)
   - If LLM adds value: propose optimization targets (which features to emphasize in prompts)
   - If outcomes are unpredictable: propose simplification (remove AI filtering, rely on mechanical OB entry rules, invest in zone detection quality instead)

5. **What this means for the remaining research pipeline:**
   - If the LLM is overhead for filtering, the T2b shadow API experiments become lower priority (optimizing a component that should be replaced)
   - If the LLM adds value, T2b becomes high priority (optimizing the decision engine)

---

## Output Files

Save results to: `research/academic_pipeline/results/T2a_ai_diagnostics_results_v1.md`
Save analysis script to: `research/academic_pipeline/T2a_ai_diagnostics_analysis.py`
Save extracted features to: `research/academic_pipeline/data/ai_evaluation_features.csv`
Save all-evaluations dataset to: `research/academic_pipeline/data/all_evaluations_features.csv`

---

## Constraints

- **Do NOT modify any files in src/ or prompts/**
- **Do NOT fabricate feature values.** If a feature can't be extracted, say so. "DATA_UNAVAILABLE" is always acceptable.
- **seed=42** for all random operations (43, 44 for repeat CV)
- **Bonferroni threshold: p < 0.025** for the 2 primary tests
- **Wilson CIs** for all proportions
- **Bootstrap CIs (seed=42, n=10000)** for means
- **Never overwrite existing files** �� use _v1 suffix
- **Leave-one-out CV** for all Part B models (n~121 is too small for holdout)
- **class_weight='balanced'** for all models in Part A (extreme class imbalance)
- **Do NOT install packages that require GPU** — use CPU-only
- If TabPFN cannot be installed: skip it. LogisticRegression + GradientBoosting + RandomForest from scikit-learn are always available and provide a sufficient baseline.
- **Report negative results clearly.** "No feature predicts trade outcomes" is the most important possible finding — it means the edge is mechanical, not predictive.

---

## Pressure Test Log

**Issues found and fixed before delivery:**
1. Original prompt assumed only 7 extractable features → Data inspection revealed 30+ features in AI reasoning JSON + MSO text. Expanded feature extraction to capture everything available.
2. Original prompt didn't reference T1 data discoveries → Now uses T1's verified data paths, match rates, and dataset as foundation.
3. Missing class imbalance handling for Part A → Added class_weight='balanced' and F1/precision/recall reporting.
4. Confidence score assumed to be 80 for all → Verified one CANDIDATE has 85 with computation breakdown. Distribution must be checked empirically.
5. No feature ablation → Added Part D to test whether more features helps or hurts at n=121.
6. Part A and Part B conflated → Clearly separated with explanation: replicating decisions ≠ predicting outcomes.
7. Missing permutation importance for Part B → Added to identify which features predict actual outcomes vs which predict AI decisions.
8. No random baseline → Added "always NO_TRADE" and "always CANDIDATE" baselines.
9. Missing interpretation framework for Part A feature importance → Added check for "trivially prompt-rule features" (e.g., m15_choch is a hard-coded requirement, not reasoning).
10. Missing link to T2b prioritization → Added synthesis point: T2a results determine whether T2b experiments are worth running.
11. Decision gate for Part B too binary → Added "outcomes unpredictable" as a fourth verdict, with interpretation (edge is mechanical, not predictive).
