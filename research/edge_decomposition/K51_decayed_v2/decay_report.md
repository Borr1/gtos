# K51 — Decayed-Component Identification (proper SHAP + Bonferroni)

_Generated: 2026-04-26T19:03:51.030463+00:00_

## Methodology

For each non-overlapping rolling window of **50 trades**, compute per-feature **shap_treeexplainer** importance (mean |SHAP| under the SHAP path; baseline-MSE − stratum-mean-MSE under the permutation fallback). Track per-feature trajectories across windows. A **decayed component** has its mean importance drop ≥ **40%** from H1 (first half of windows) to H2 (second half) **AND** the H1/H2 importance-delta one-sided Welch's t-test survives Bonferroni correction (family_size = 12, α = 0.050).

Data sources:
- Trade records dir: `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-ad510a06415ac802b\knowledge_base\trade_records`
- Aux index: `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-ad510a06415ac802b\knowledge_base\index\_trade_index.json`
- Symbol filter: (all)
- Method requested: `shap` → actually used: `shap_treeexplainer`
- SHAP available: `True`

Sample: **129 filled trades**, **2 windows** of 50.
H1 period: `2025-03-14` → `2025-03-14`. H2 period: `2026-01-06` → `2026-01-06`.

## Components decayed >=40% H1->H2 (mean |SHAP|, Bonferroni-corrected)

| Feature | H1 mean |SHAP| | H2 mean |SHAP| | drop % | bootstrap 95% CI (H1, H2) | bonf p | status |
| --- | --- | --- | --- | --- | --- | --- |
| _(none)_ | — | — | — | — | — | — |

## All canonical features (regardless of decay verdict)

| Feature | H1 mean |SHAP| | H2 mean |SHAP| | drop % | bootstrap 95% CI (H1, H2) | raw p | bonf p | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| daily_bias | 0.0000 | 0.0000 | +0.0% | H1 [0.0000, 0.0000] / H2 [0.0000, 0.0000] | — | — | stable |
| direction | 0.0505 | 0.0757 | -50.0% | H1 [0.0099, 0.1687] / H2 [0.0121, 0.1930] | — | — | stable |
| displacement_quality | 0.0476 | 0.0017 | +96.5% | H1 [0.0015, 0.1135] / H2 [0.0000, 0.0411] | — | — | suggestive |
| framework | 0.0018 | 0.0000 | +100.0% | H1 [0.0000, 0.0160] / H2 [0.0000, 0.0925] | — | — | suggestive |
| hold_time_candles | 0.1565 | 0.1581 | -1.0% | H1 [0.0386, 0.3558] / H2 [0.0532, 0.2533] | — | — | stable |
| kill_zone | 0.0588 | 0.0233 | +60.4% | H1 [0.0094, 0.1608] / H2 [0.0113, 0.2074] | — | — | suggestive |
| liquidity_pool_type | 0.0000 | 0.0000 | +0.0% | H1 [0.0000, 0.0000] / H2 [0.0000, 0.0000] | — | — | stable |
| mae_r | 0.5534 | 0.5790 | -4.6% | H1 [0.2724, 0.7182] / H2 [0.3051, 0.7597] | — | — | stable |
| mfe_r | 0.5065 | 0.7301 | -44.1% | H1 [0.2904, 0.9899] / H2 [0.3640, 1.0956] | — | — | stable |
| planned_rr | 0.0000 | 0.0000 | +0.0% | H1 [0.0000, 0.0000] / H2 [0.0000, 0.0000] | — | — | stable |
| setup_grade | 0.0545 | 0.1061 | -94.5% | H1 [0.0098, 0.1583] / H2 [0.0186, 0.1641] | — | — | stable |
| sweep_quality | 0.0000 | 0.0000 | +0.0% | H1 [0.0000, 0.0000] / H2 [0.0000, 0.0000] | — | — | stable |

## Newly important features (H1 mass == 0, H2 mass > 0)

| Feature | H1 mean |SHAP| | H2 mean |SHAP| | gain | bonf p | n_h1 | n_h2 |
| --- | --- | --- | --- | --- | --- | --- |
| _(none)_ | — | — | — | — | — | — |

## Stable features (or large-drop-but-not-significant)

| Feature | H1 mean |SHAP| | H2 mean |SHAP| | drop % | bonf p | n_h1 | n_h2 |
| --- | --- | --- | --- | --- | --- | --- |
| daily_bias | 0.0000 | 0.0000 | +0.0% | — | 1 | 1 |
| direction | 0.0505 | 0.0757 | -50.0% | — | 1 | 1 |
| displacement_quality | 0.0476 | 0.0017 | +96.5% | — | 1 | 1 |
| framework | 0.0018 | 0.0000 | +100.0% | — | 1 | 1 |
| hold_time_candles | 0.1565 | 0.1581 | -1.0% | — | 1 | 1 |
| kill_zone | 0.0588 | 0.0233 | +60.4% | — | 1 | 1 |
| liquidity_pool_type | 0.0000 | 0.0000 | +0.0% | — | 1 | 1 |
| mae_r | 0.5534 | 0.5790 | -4.6% | — | 1 | 1 |
| mfe_r | 0.5065 | 0.7301 | -44.1% | — | 1 | 1 |
| planned_rr | 0.0000 | 0.0000 | +0.0% | — | 1 | 1 |
| setup_grade | 0.0545 | 0.1061 | -94.5% | — | 1 | 1 |
| sweep_quality | 0.0000 | 0.0000 | +0.0% | — | 1 | 1 |

## Strategic verdict

- Most decayed (proper-method): _(none survive Bonferroni at α=0.050)_.
- Newly important (proper-method): _(none)_.

Reasoning:
- No feature dropped past the threshold AND survived Bonferroni correction. The H1/H2 split with this many windows is underpowered for a Bonferroni-corrected family-of-12 test — large raw drops can fail Bonferroni when n_h1_windows + n_h2_windows is small. The permutation-method (no Bonferroni) results in the original K51 are screening hints, not significant signals.
- Cross-reference with K50 (population-level attribution) before drawing strategic conclusions: if K50 ranks a feature low and K51 shows it decaying, the feature was never load-bearing.
- Walk-level evidence is not predictive of realized R (`feedback_walk_level_evidence_not_predictive`) — these importances are computed against realized R per filled trade.
