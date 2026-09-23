# K50 — Causal Edge Attribution (F16: proper SHAP + Bonferroni + bootstrap CI)

- **Method requested**: `shap`  
- **Method used**: `shap_treeexplainer`  
- **SHAP available**: `True`  
- **Samples (filled trades)**: 240  
- **Sources**: trade_index:_trade_index.json, unified_csv:trades_unified.csv  
- **Symbol filter**: none (all)  
- **Input trades read**: 240 (filled = 240)  
- **Bonferroni alpha**: 0.050 | family size: 8  
- **Bootstrap resamples**: 100 | CI alpha: 0.050


## Edge Component Ranking (mean |SHAP| with bootstrap CI)

| Feature | mean \|SHAP\| | mean SHAP | relative importance | bootstrap CI | Bayesian rank |
|---|---:|---:|---:|---:|---:|
| framework_id | 0.0920 | -0.0011 | 51.2% | [0.0208, 0.2030] | 1 |
| displacement_quality_score | 0.0469 | +0.0013 | 26.1% | [0.0253, 0.2010] | 2 |
| session_id | 0.0407 | -0.0002 | 22.6% | [0.0210, 0.2008] | 4 |
| ob_retest_distance_atr | 0.0000 | +0.0000 | 0.0% | [0.0000, 0.0000] | 5 |
| fvg_present | 0.0000 | +0.0000 | 0.0% | [0.0000, 0.0000] | 6 |
| touch_count | 0.0000 | +0.0000 | 0.0% | [0.0000, 0.0000] | 7 |
| hour_of_day_utc | 0.0000 | +0.0000 | 0.0% | [0.0000, 0.0000] | 3 |
| regime_tag | 0.0000 | +0.0000 | 0.0% | [0.0000, 0.0000] | 8 |

## H1 vs H2 importance-delta test (Bonferroni-corrected)

H1 / H2 sample sizes: **120 / 120** filled trades. One-sided Welch's t-test on bootstrap distributions of mean |SHAP| (H0: H1 ≤ H2). Bonferroni family size = 8, α = 0.050. Bootstrap resamples per half: 100.

| Feature | H1 |SHAP| | H2 |SHAP| | delta | raw p | bonf p | status |
|---|---:|---:|---:|---:|---:|---|
| ob_retest_distance_atr | 0.0000 | 0.0000 | +0.0000 | — | — | stable |
| displacement_quality_score | 0.1055 | 0.1239 | -0.0184 | 0.9738 | 1.0000 | stable |
| fvg_present | 0.0000 | 0.0000 | +0.0000 | — | — | stable |
| touch_count | 0.0000 | 0.0000 | +0.0000 | — | — | stable |
| framework_id | 0.1072 | 0.1118 | -0.0046 | 0.7084 | 1.0000 | stable |
| session_id | 0.0972 | 0.1381 | -0.0408 | 1.0000 | 1.0000 | stable |
| hour_of_day_utc | 0.0000 | 0.0000 | +0.0000 | — | — | stable |
| regime_tag | 0.0000 | 0.0000 | +0.0000 | — | — | stable |


## Bayesian Posterior (standardised coefficients)

| Feature | posterior mean | posterior std | raw-space coef |
|---|---:|---:|---:|
| framework_id | +0.1783 | 0.0736 | +0.6604 |
| displacement_quality_score | +0.0373 | 0.0711 | +0.0763 |
| hour_of_day_utc | +0.0142 | 24.6154 | +0.0047 |
| session_id | +0.0142 | 24.6154 | +0.0284 |
| ob_retest_distance_atr | +0.0000 | 34.8114 | +0.0000 |
| fvg_present | +0.0000 | 34.8114 | +0.0000 |
| touch_count | +0.0000 | 34.8114 | +0.0000 |
| regime_tag | +0.0000 | 34.8114 | +0.0000 |

## Strategic verdict

- **Top R contributor (proper SHAP)**: `framework_id` (51.2% of total |SHAP| mass)
- **Top negative contributor**: `framework_id` (mean SHAP -0.0011)
- **Most decayed H1→H2**: _(none survive Bonferroni at α=0.050)_

## Caveats

- SHAP rank vs Bayesian-magnitude rank Spearman r = `0.762` (n=8).
- Realised-R target only — no walk-level proxies (per `feedback_walk_level_evidence_not_predictive`).
- Categorical features are integer-encoded (framework_id, session_id, regime_tag); the GBM tree splits handle them natively but the Bayesian linear model treats them as ordinal — interpret Bayesian coefficients on those columns with care.
- F16 update: SHAP is now the default attribution path when `shap` + a tree backend (`lightgbm` / `xgboost` / sklearn-GBM) are importable. The original K50 (commit `44d0644`) ran the permutation-importance fallback because the local environment lacked `shap` at the time. See `comparison.md` (when present) for proper-SHAP vs original-permutation deltas.
- Bonferroni correction is applied to the H1/H2 importance-delta test family across the 8 canonical features. With small-n bootstrap distributions per half, the corrected α=0.050 demands raw_p < 0.0063, which is conservative.
- Bootstrap CIs are computed by resampling filled trades with replacement and re-fitting the regressor. Per-feature mean |SHAP| percentile bounds reflect sampling variability of the importance statistic, not model misspecification.
- Output feeds K54 ML classifier feature engineering. K50 does **not** propose system changes.
