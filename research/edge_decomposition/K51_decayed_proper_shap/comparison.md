# K51 comparison — proper SHAP + Bonferroni vs original (permutation, no Bonferroni)

_Generated: 2026-04-26T17:54:33.786678+00:00_

Original trajectories: `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-aeeca02fd0bd4d662\research\edge_decomposition\K51_decayed_original\trajectories.json`
Original method: `permutation_importance` (no Bonferroni). Proper method: `shap_treeexplainer` (Bonferroni at α=0.050, family_size=12).

## Comparison vs original K51 (permutation, no Bonferroni)

| Feature | original drop% | proper drop% | delta | bonf p | original status | proper status | status change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| daily_bias | +0.0% | +0.0% | +0.0% | — | stable | stable | — |
| direction | +97.5% | -28.1% | -125.6% | 1.0000 | decayed | stable | decayed → stable |
| displacement_quality | +97.5% | +41.7% | -55.8% | 1.0000 | decayed | suggestive | decayed → suggestive |
| framework | -111.9% | -254.1% | -142.2% | 1.0000 | stable | stable | — |
| hold_time_candles | +7.5% | -254.7% | -262.3% | 1.0000 | stable | stable | — |
| kill_zone | +65.0% | -19.9% | -84.9% | 1.0000 | decayed | stable | decayed → stable |
| liquidity_pool_type | +0.0% | +0.0% | +0.0% | — | stable | stable | — |
| mae_r | -6.2% | +26.3% | +32.6% | 1.0000 | stable | stable | — |
| mfe_r | -44.0% | -17.3% | +26.7% | 1.0000 | stable | stable | — |
| planned_rr | +0.0% | +0.0% | +0.0% | — | stable | stable | — |
| setup_grade | -1878.4% | +21.9% | +1900.3% | 1.0000 | stable | stable | — |
| sweep_quality | +0.0% | +0.0% | +0.0% | — | stable | stable | — |

## Reasoning

The proper method (SHAP / mean(|SHAP|) when available, plus a one-sided Welch's t-test on the H1/H2 importance series Bonferroni-corrected over family_size=12, α=0.050) is a stricter test than the original screening rule. With only a handful of windows per half, Bonferroni at α=0.05 is hard to satisfy; large raw drops can drop to 'suggestive' status. The comparison block makes this dynamic transparent and is the right lens for ranking K54 ML-classifier feature inclusion.
