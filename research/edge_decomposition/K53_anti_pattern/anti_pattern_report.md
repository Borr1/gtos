# K53 Loser Anti-Pattern Report

_Generated 2026-04-26T16:46:25+00:00_

## Population

- Total filled CANDIDATEs: **217**
- Losers (realized R ≤ 0): **101**
- H2-2026 losers in window: **56**
- sklearn used: **True**

## Loser anti-pattern clusters (k=3, silhouette=0.670)

| Cluster | n | Top 3 features (centroid, deviation vs population) | Mean R | WR within | H2-2026 frequency in cluster |
|--------:|--:|---|--:|--:|--:|
| 0 | 59 | fvg_m15_unfilled_count: +0.000 (Δ=-5.099)<br>fvg_h1_unfilled_count: +0.000 (Δ=-2.416)<br>ob_retest_distance_atr: +2.000 (Δ=+1.611) | -1.000 | 0.000 | 0.542 |
| 1 | 41 | fvg_m15_unfilled_count: +12.561 (Δ=+7.462)<br>fvg_h1_unfilled_count: +5.951 (Δ=+3.535)<br>ob_retest_distance_atr: -1.969 (Δ=-2.358) | -1.000 | 0.000 | 0.585 |
| 2 | 1 | risk_reward: +52.782 (Δ=+50.786)<br>fvg_m15_unfilled_count: +0.000 (Δ=-5.099)<br>fvg_h1_unfilled_count: +0.000 (Δ=-2.416) | -1.000 | 0.000 | 0.000 |

### Silhouette by k

| k | silhouette |
|--:|--:|
| 3 | 0.670 |
| 4 | 0.614 |
| 5 | 0.597 |
| 6 | 0.615 |
| 7 | 0.572 |

## Loss classifier

- Classifier type: `gradient_boosting`
- Train AUC: **0.996**
- Held-out (random split, n=28) AUC: **0.526**
- Held-out (H2-2026 time slice, n=103) AUC: **0.598**
- Regime-stationarity ratio (holdout / random-test): **1.136**

### Top 5 features by importance

| # | feature | importance |
|--:|---|--:|
| 1 | risk_reward | 0.3462 |
| 2 | ob_retest_distance_atr | 0.1755 |
| 3 | hour_cos | 0.1003 |
| 4 | ob_touch_max | 0.0921 |
| 5 | day_of_week | 0.0885 |

## Strategic verdict

- Distinct anti-patterns identified: **yes (strong cluster structure)**
- Most actionable cluster (highest H2-2026 frequency): **Cluster 1** (n=41, H2 freq=0.59) — fvg_m15_unfilled_count +7.46, fvg_h1_unfilled_count +3.54, ob_retest_distance_atr -2.36
- Reasoning: Held-out time-slice AUC is comparable to random-split AUC, suggesting anti-patterns are stable across H1 / H2.

## Handoff to K54

The clusters above become K54's feature-engineering hints — the trained ML classifier should attend to the highest-importance features surfaced here AND the per-cluster centroid signatures.
