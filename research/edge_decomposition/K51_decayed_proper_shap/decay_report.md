# K51 — Decayed-Component Identification (proper SHAP + Bonferroni)

_Generated: 2026-04-26T17:54:33.775863+00:00_

## Methodology

For each non-overlapping rolling window of **30 trades**, compute per-feature **shap_treeexplainer** importance (mean |SHAP| under the SHAP path; baseline-MSE − stratum-mean-MSE under the permutation fallback). Track per-feature trajectories across windows. A **decayed component** has its mean importance drop ≥ **40%** from H1 (first half of windows) to H2 (second half) **AND** the H1/H2 importance-delta one-sided Welch's t-test survives Bonferroni correction (family_size = 12, α = 0.050).

Data sources:
- Trade records dir: `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-aeeca02fd0bd4d662\knowledge_base\trade_records`
- Aux index: `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-aeeca02fd0bd4d662\knowledge_base\index\_trade_index.json`
- Symbol filter: (all)
- Method requested: `auto` → actually used: `shap_treeexplainer`
- SHAP available: `True`

Sample: **129 filled trades**, **4 windows** of 30.
H1 period: `2025-02-19` → `2025-04-17`. H2 period: `2025-12-19` → `2026-02-03`.

## Components decayed >=40% H1->H2 (mean |SHAP|, Bonferroni-corrected)

| Feature | H1 mean |SHAP| | H2 mean |SHAP| | drop % | bootstrap 95% CI (H1, H2) | bonf p | status |
| --- | --- | --- | --- | --- | --- | --- |
| _(none)_ | — | — | — | — | — | — |

## All canonical features (regardless of decay verdict)

| Feature | H1 mean |SHAP| | H2 mean |SHAP| | drop % | bootstrap 95% CI (H1, H2) | raw p | bonf p | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| daily_bias | 0.0000 | 0.0000 | +0.0% | H1 [0.0000, 0.0000] / H2 [0.0000, 0.0000] | — | — | stable |
| direction | 0.0214 | 0.0274 | -28.1% | H1 [0.0016, 0.1449] / H2 [0.0001, 0.1621] | 0.5712 | 1.0000 | stable |
| displacement_quality | 0.0263 | 0.0153 | +41.7% | H1 [0.0000, 0.1618] / H2 [0.0000, 0.0924] | 0.3227 | 1.0000 | suggestive |
| framework | 0.0048 | 0.0171 | -254.1% | H1 [0.0000, 0.0916] / H2 [0.0000, 0.1753] | 0.6997 | 1.0000 | stable |
| hold_time_candles | 0.0645 | 0.2287 | -254.7% | H1 [0.0168, 0.5238] / H2 [0.0234, 0.4988] | 0.8532 | 1.0000 | stable |
| kill_zone | 0.0660 | 0.0791 | -19.9% | H1 [0.0064, 0.2381] / H2 [0.0049, 0.2556] | 0.9717 | 1.0000 | stable |
| liquidity_pool_type | 0.0000 | 0.0000 | +0.0% | H1 [0.0000, 0.0000] / H2 [0.0000, 0.0000] | — | — | stable |
| mae_r | 0.4927 | 0.3629 | +26.3% | H1 [0.1969, 0.6526] / H2 [0.1505, 0.7043] | 0.1284 | 1.0000 | stable |
| mfe_r | 0.6160 | 0.7223 | -17.3% | H1 [0.1298, 0.9806] / H2 [0.2394, 1.0967] | 0.6056 | 1.0000 | stable |
| planned_rr | 0.0000 | 0.0000 | +0.0% | H1 [0.0000, 0.0000] / H2 [0.0000, 0.0000] | — | — | stable |
| setup_grade | 0.1268 | 0.0990 | +21.9% | H1 [0.0029, 0.3035] / H2 [0.0026, 0.3227] | 0.3373 | 1.0000 | stable |
| sweep_quality | 0.0000 | 0.0000 | +0.0% | H1 [0.0000, 0.0000] / H2 [0.0000, 0.0000] | — | — | stable |

## Newly important features (H1 mass == 0, H2 mass > 0)

| Feature | H1 mean |SHAP| | H2 mean |SHAP| | gain | bonf p | n_h1 | n_h2 |
| --- | --- | --- | --- | --- | --- | --- |
| _(none)_ | — | — | — | — | — | — |

## Stable features (or large-drop-but-not-significant)

| Feature | H1 mean |SHAP| | H2 mean |SHAP| | drop % | bonf p | n_h1 | n_h2 |
| --- | --- | --- | --- | --- | --- | --- |
| daily_bias | 0.0000 | 0.0000 | +0.0% | — | 2 | 2 |
| direction | 0.0214 | 0.0274 | -28.1% | 1.0000 | 2 | 2 |
| displacement_quality | 0.0263 | 0.0153 | +41.7% | 1.0000 | 2 | 2 |
| framework | 0.0048 | 0.0171 | -254.1% | 1.0000 | 2 | 2 |
| hold_time_candles | 0.0645 | 0.2287 | -254.7% | 1.0000 | 2 | 2 |
| kill_zone | 0.0660 | 0.0791 | -19.9% | 1.0000 | 2 | 2 |
| liquidity_pool_type | 0.0000 | 0.0000 | +0.0% | — | 2 | 2 |
| mae_r | 0.4927 | 0.3629 | +26.3% | 1.0000 | 2 | 2 |
| mfe_r | 0.6160 | 0.7223 | -17.3% | 1.0000 | 2 | 2 |
| planned_rr | 0.0000 | 0.0000 | +0.0% | — | 2 | 2 |
| setup_grade | 0.1268 | 0.0990 | +21.9% | 1.0000 | 2 | 2 |
| sweep_quality | 0.0000 | 0.0000 | +0.0% | — | 2 | 2 |

## Strategic verdict

- Most decayed (proper-method): _(none survive Bonferroni at α=0.050)_.
- Newly important (proper-method): _(none)_.

Reasoning:
- No feature dropped past the threshold AND survived Bonferroni correction. The H1/H2 split with this many windows is underpowered for a Bonferroni-corrected family-of-12 test — large raw drops can fail Bonferroni when n_h1_windows + n_h2_windows is small. The permutation-method (no Bonferroni) results in the original K51 are screening hints, not significant signals.
- Cross-reference with K50 (population-level attribution) before drawing strategic conclusions: if K50 ranks a feature low and K51 shows it decaying, the feature was never load-bearing.
- Walk-level evidence is not predictive of realized R (`feedback_walk_level_evidence_not_predictive`) — these importances are computed against realized R per filled trade.
