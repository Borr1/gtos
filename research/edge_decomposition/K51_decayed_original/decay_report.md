# K51 — Decayed-Component Identification

_Generated: 2026-04-26T17:42:35.489847+00:00_

## Methodology

For each non-overlapping rolling window of **30 trades**, compute permutation-importance per feature (stratum-mean predictor; importance = baseline MSE − stratum-mean MSE). Track per-feature trajectories across windows. A **decayed component** has its mean importance drop ≥ **40%** from the H1 baseline period (first half of windows) to the H2 current period (second half).

Data sources:
- Trade records dir: `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-aeeca02fd0bd4d662\knowledge_base\trade_records`
- Aux index: `C:\Users\MSI\Documents\ai-trading-agent\.claude\worktrees\agent-aeeca02fd0bd4d662\knowledge_base\index\_trade_index.json`
- Symbol filter: (all)

Sample: **129 filled trades**, **4 windows** of 30.
H1 period: `2025-02-19` → `2025-04-17`. H2 period: `2025-12-19` → `2026-02-03`.

## Components decayed ≥40% H1→H2 (mean importance)

| Feature | H1 mean importance | H2 mean importance | drop % | n_h1 | n_h2 |
| --- | --- | --- | --- | --- | --- |
| displacement_quality | 0.1127 | 0.0028 | +97.5% | 2 | 2 |
| direction | 0.1119 | 0.0028 | +97.5% | 2 | 2 |
| kill_zone | 0.0599 | 0.0210 | +65.0% | 2 | 2 |

## Newly important features (H1 mass == 0, H2 mass > 0)

| Feature | H1 mean importance | H2 mean importance | gain | n_h1 | n_h2 |
| --- | --- | --- | --- | --- | --- |
| _(none)_ | — | — | — | — | — |

## Stable features

| Feature | H1 mean importance | H2 mean importance | drop % | n_h1 | n_h2 |
| --- | --- | --- | --- | --- | --- |
| daily_bias | 0.0000 | 0.0000 | +0.0% | 2 | 2 |
| framework | 0.0742 | 0.1571 | -111.9% | 2 | 2 |
| hold_time_candles | 0.2561 | 0.2368 | +7.5% | 2 | 2 |
| liquidity_pool_type | 0.0000 | 0.0000 | +0.0% | 2 | 2 |
| mae_r | 0.5763 | 0.6122 | -6.2% | 2 | 2 |
| mfe_r | 0.5344 | 0.7693 | -44.0% | 2 | 2 |
| planned_rr | 0.0000 | 0.0000 | +0.0% | 2 | 2 |
| setup_grade | 0.0015 | 0.0293 | -1878.4% | 2 | 2 |
| sweep_quality | 0.0000 | 0.0000 | +0.0% | 2 | 2 |

## Strategic verdict

Most decayed: **displacement_quality** (+97.5%).
Newly important: _(none)_.
Stable: daily_bias, framework, hold_time_candles, liquidity_pool_type, mae_r, mfe_r, planned_rr, setup_grade, sweep_quality.

Reasoning:
- Features displacement_quality, direction, kill_zone carried meaningful R-variance explanation in H1 but lost it in H2. Either the AI's selection criteria along these axes have weakened (system decay) or the underlying market relationship between these features and outcome has dissolved (regime decay).
- Cross-reference with K50 (population-level attribution) before drawing strategic conclusions: if K50 ranks a feature low and K51 shows it decaying, the feature was never load-bearing.
- Walk-level evidence is not predictive of realized R (`feedback_walk_level_evidence_not_predictive`) — these importances are computed against realized R per filled trade.
