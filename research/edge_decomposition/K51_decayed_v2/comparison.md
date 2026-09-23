# K51 comparison — proper SHAP + Bonferroni vs original (permutation, no Bonferroni)

_Generated: 2026-04-26T19:03:51.041817+00:00_

Original trajectories: `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-ad510a06415ac802b\research\edge_decomposition\K51_decayed_original\trajectories.json`
Original method: `permutation_importance` (no Bonferroni). Proper method: `shap_treeexplainer` (Bonferroni at α=0.050, family_size=12).

## Comparison vs original K51 (permutation, no Bonferroni)

| Feature | original drop% | proper drop% | delta | bonf p | original status | proper status | status change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| daily_bias | +0.0% | +0.0% | +0.0% | — | stable | stable | — |
| direction | +97.5% | -50.0% | -147.5% | — | decayed | stable | decayed → stable |
| displacement_quality | +97.5% | +96.5% | -1.1% | — | decayed | suggestive | decayed → suggestive |
| framework | -111.9% | +100.0% | +211.9% | — | stable | suggestive | stable → suggestive |
| hold_time_candles | +7.5% | -1.0% | -8.6% | — | stable | stable | — |
| kill_zone | +65.0% | +60.4% | -4.6% | — | decayed | suggestive | decayed → suggestive |
| liquidity_pool_type | +0.0% | +0.0% | +0.0% | — | stable | stable | — |
| mae_r | -6.2% | -4.6% | +1.6% | — | stable | stable | — |
| mfe_r | -44.0% | -44.1% | -0.2% | — | stable | stable | — |
| planned_rr | +0.0% | +0.0% | +0.0% | — | stable | stable | — |
| setup_grade | -1878.4% | -94.5% | +1783.9% | — | stable | stable | — |
| sweep_quality | +0.0% | +0.0% | +0.0% | — | stable | stable | — |

## Reasoning

The proper method (SHAP / mean(|SHAP|) when available, plus a one-sided Welch's t-test on the H1/H2 importance series Bonferroni-corrected over family_size=12, α=0.050) is a stricter test than the original screening rule. With only a handful of windows per half, Bonferroni at α=0.05 is hard to satisfy; large raw drops can drop to 'suggestive' status. The comparison block makes this dynamic transparent and is the right lens for ranking K54 ML-classifier feature inclusion.
