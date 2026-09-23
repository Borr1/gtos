# K50 — proper SHAP vs original permutation comparison

- **Original K50 method**: `permutation_importance` (no Bonferroni, no bootstrap CI). n_samples = 215.
- **Proper-SHAP K50 method**: `shap_treeexplainer` (Bonferroni α = 0.050, family_size = 8). n_samples = 215.
- **Original ranking JSON**: `research\edge_decomposition\K50_attribution\ranking.json`


## K50 — proper SHAP vs original permutation

| Feature | original mean importance% | proper SHAP mean \|SHAP\| | proper rel imp% | rank delta | bonf p | status change |
|---|---:|---:|---:|---:|---:|---|
| ob_retest_distance_atr | 0.0% | 0.0000 ([0.0000, 0.0000]) | 0.0% | -1 | — | — |
| displacement_quality_score | 16.4% | 0.1098 ([0.0371, 0.2413]) | 38.0% | -1 | 1.69e-05 | became #1 |
| fvg_present | 0.0% | 0.0000 ([0.0000, 0.0000]) | 0.0% | -1 | — | — |
| touch_count | 0.0% | 0.0000 ([0.0000, 0.0000]) | 0.0% | -1 | — | — |
| framework_id | 75.0% | 0.0972 ([0.0353, 0.2155]) | 33.6% | +1 | 0.3766 | lost #1 dominance |
| session_id | 5.5% | 0.0821 ([0.0250, 0.1879]) | 28.4% | +0 | 1.0000 | — |
| hour_of_day_utc | 3.1% | 0.0000 ([0.0000, 0.0000]) | 0.0% | +3 | — | — |
| regime_tag | 0.0% | 0.0000 ([0.0000, 0.0000]) | 0.0% | +0 | — | — |

## Comparison verdict

- Top feature under proper SHAP: **displacement_quality_score** (38.0% relative |SHAP|).
- Top feature under original permutation: **framework_id** (75.0% relative).
- Whether `framework_id` remains dominant under proper SHAP: **no**.
- Sign-flips between methods: framework_id.
- Reasoning: Under proper SHAP, `framework_id` no longer ranks #1. `displacement_quality_score` is now the dominant edge component. The original permutation-importance estimate was likely inflated by univariate-mean shifts that don't survive a tree-model's joint attribution. K50's original verdict therefore does NOT replicate under proper SHAP — analogous to F5's K51 finding where 2/3 features sign-flipped.

## Strategic implication

- For K54 feature engineering: prioritise the proper-SHAP top contributors (rank-1: `displacement_quality_score`). Treat the original K50 ranking as a screening hint, not a confirmed feature attribution.
- For Phase 2 prompt research: re-frame any prior framing that leant on `framework_id 81%` (the original 215-trade run shipped 75%). Where proper SHAP demotes or sign-flips a feature, the prompt research that followed that feature's trail should be re-evaluated.
- F16 + F5 confirm a methodology pattern: permutation importance without correction is a screening tool only. Confirmatory K-series research must use SHAP TreeExplainer plus Bonferroni and bootstrap CI before strategic conclusions are drawn.
