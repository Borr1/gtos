# K50 — Causal Edge Attribution

- **Method**: permutation_importance  
- **Samples (filled trades)**: 215  
- **Sources**: trade_index:_trade_index.json, unified_csv:trades_unified.csv  
- **Symbol filter**: XAUUSD  
- **Input trades read**: 240 (filled = 215)


## Edge Component Ranking (mean |SHAP|)

| Feature | mean \|SHAP\| | mean SHAP | relative importance | Bayesian rank |
|---|---:|---:|---:|---:|
| framework_id | 0.1008 | +0.1008 | 75.0% | 1 |
| displacement_quality_score | 0.0220 | +0.0220 | 16.4% | 2 |
| session_id | 0.0074 | +0.0074 | 5.5% | 3 |
| hour_of_day_utc | 0.0042 | +0.0042 | 3.1% | 4 |
| ob_retest_distance_atr | 0.0000 | +0.0000 | 0.0% | 5 |
| fvg_present | 0.0000 | +0.0000 | 0.0% | 6 |
| touch_count | 0.0000 | +0.0000 | 0.0% | 7 |
| regime_tag | 0.0000 | +0.0000 | 0.0% | 8 |

## Bayesian Posterior (standardised coefficients)

| Feature | posterior mean | posterior std | raw-space coef |
|---|---:|---:|---:|
| framework_id | +0.1874 | 0.0757 | +0.6604 |
| displacement_quality_score | +0.1018 | 0.0728 | +0.2124 |
| session_id | +0.0358 | 23.8735 | +0.0715 |
| hour_of_day_utc | +0.0358 | 23.8735 | +0.0119 |
| ob_retest_distance_atr | +0.0000 | 33.7622 | +0.0000 |
| fvg_present | +0.0000 | 33.7622 | +0.0000 |
| touch_count | +0.0000 | 33.7622 | +0.0000 |
| regime_tag | +0.0000 | 33.7622 | +0.0000 |

## Strategic verdict

- **Top R contributor**: `framework_id` (75.0% of total |SHAP| mass)
- **Negative contributor**: none (all features net non-negative on average)
- **Top contributor H1**: `framework_id`
- **Top contributor H2**: `displacement_quality_score`
- **Decayed since H1**: `framework_id` (H1 rank 1 → H2 rank 4)

## Caveats

- SHAP rank vs Bayesian-magnitude rank Spearman r = `1.000` (n=8).
- Realised-R target only — no walk-level proxies (per `feedback_walk_level_evidence_not_predictive`).
- Categorical features are integer-encoded (framework_id, session_id, regime_tag); the GBM tree splits handle them natively but the Bayesian linear model treats them as ordinal — interpret Bayesian coefficients on those columns with care.
- Output feeds K54 ML classifier feature engineering. K50 does **not** propose system changes.
