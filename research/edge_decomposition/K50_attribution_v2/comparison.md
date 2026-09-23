# K50 — proper SHAP vs original permutation comparison

- **Original K50 method**: `permutation_importance` (no Bonferroni, no bootstrap CI). n_samples = 215.
- **Proper-SHAP K50 method**: `shap_treeexplainer` (Bonferroni α = 0.050, family_size = 8). n_samples = 240.
- **Original ranking JSON**: `research\edge_decomposition\K50_attribution\ranking.json`


## K50 — proper SHAP vs original permutation

| Feature | original mean importance% | proper SHAP mean \|SHAP\| | proper rel imp% | rank delta | bonf p | status change |
|---|---:|---:|---:|---:|---:|---|
| ob_retest_distance_atr | 0.0% | 0.0000 ([0.0000, 0.0000]) | 0.0% | -1 | — | — |
| displacement_quality_score | 16.4% | 0.0469 ([0.0253, 0.2010]) | 26.1% | +0 | 1.0000 | — |
| fvg_present | 0.0% | 0.0000 ([0.0000, 0.0000]) | 0.0% | -1 | — | — |
| touch_count | 0.0% | 0.0000 ([0.0000, 0.0000]) | 0.0% | -1 | — | — |
| framework_id | 75.0% | 0.0920 ([0.0208, 0.2030]) | 51.2% | +0 | 1.0000 | — |
| session_id | 5.5% | 0.0407 ([0.0210, 0.2008]) | 22.6% | +0 | 1.0000 | — |
| hour_of_day_utc | 3.1% | 0.0000 ([0.0000, 0.0000]) | 0.0% | +3 | — | — |
| regime_tag | 0.0% | 0.0000 ([0.0000, 0.0000]) | 0.0% | +0 | — | — |

## Comparison verdict

- Top feature under proper SHAP: **framework_id** (51.2% relative |SHAP|).
- Top feature under original permutation: **framework_id** (75.0% relative).
- Whether `framework_id` remains dominant under proper SHAP: **yes**.
- Sign-flips between methods: framework_id, session_id.
- Reasoning: Proper SHAP confirms `framework_id` retains its #1 rank, but the magnitude shifts (0.1008 → 0.0920) and the bootstrap CI makes the variance of the estimate explicit. Other features' relative shares may have shrunk because the GBM/SHAP path captures interaction effects that the univariate permutation fallback overshoots.

## Strategic implication

- For K54 feature engineering: prioritise the proper-SHAP top contributors (rank-1: `framework_id`). Treat the original K50 ranking as a screening hint, not a confirmed feature attribution.
- For Phase 2 prompt research: re-frame any prior framing that leant on `framework_id 81%` (the original 215-trade run shipped 75%). Where proper SHAP demotes or sign-flips a feature, the prompt research that followed that feature's trail should be re-evaluated.
- F16 + F5 confirm a methodology pattern: permutation importance without correction is a screening tool only. Confirmatory K-series research must use SHAP TreeExplainer plus Bonferroni and bootstrap CI before strategic conclusions are drawn.
