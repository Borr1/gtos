# K53 Loser Anti-Pattern Report (tier2)

_Generated 2026-04-26T17:47:29+00:00_

**Source-stratified pass:** rows restricted to `source == 'tier2'`. F3 mandate (post-K53 confound diagnosis): the original mixed-source K53 had train AUC 0.996 → H2 holdout 0.598 because the joined matrix let Phase 1 vs Tier 2 schema differences leak into the labels. This pass clusters and trains WITHIN a single source so schema differences cannot drive the result.

## Population

- Pass label: **tier2**
- Total filled CANDIDATEs: **142**
- Losers (realized R ≤ 0): **60**
- H2-2026 losers in window: **32**
- sklearn used: **True**

## Loser anti-pattern clusters (k=6, silhouette=0.433)

| Cluster | n | Top 3 features (centroid, deviation vs population) | Mean R | WR within | H2-2026 frequency in cluster |
|--------:|--:|---|--:|--:|--:|
| 0 | 9 | day_of_week: +3.444 (Δ=+1.394)<br>risk_reward: +1.503 (Δ=-0.832)<br>hour_sin: -0.416 (Δ=-0.650) | -1.000 | 0.000 | 0.667 |
| 1 | 1 | risk_reward: +52.782 (Δ=+50.447)<br>day_of_week: +4.000 (Δ=+1.950)<br>touch_count: +2.000 (Δ=+0.767) | -1.000 | 0.000 | 0.000 |
| 2 | 21 | risk_reward: +1.478 (Δ=-0.857)<br>day_of_week: +2.762 (Δ=+0.712)<br>hour_sin: +0.802 (Δ=+0.568) | -1.000 | 0.000 | 0.619 |
| 3 | 8 | day_of_week: +0.625 (Δ=-1.425)<br>risk_reward: +1.407 (Δ=-0.928)<br>hour_sin: -0.539 (Δ=-0.774) | -1.000 | 0.000 | 0.375 |
| 4 | 9 | risk_reward: +1.500 (Δ=-0.835)<br>hour_sin: -0.494 (Δ=-0.729)<br>session_london: +0.000 (Δ=-0.567) | -1.000 | 0.000 | 0.556 |
| 5 | 12 | day_of_week: +0.583 (Δ=-1.467)<br>risk_reward: +1.500 (Δ=-0.835)<br>hour_sin: +0.729 (Δ=+0.495) | -1.000 | 0.000 | 0.417 |

### Silhouette by k

| k | silhouette |
|--:|--:|
| 3 | 0.322 |
| 4 | 0.399 |
| 5 | 0.413 |
| 6 | 0.433 |
| 7 | 0.387 |

## Loss classifier

- Classifier type: `gradient_boosting`
- Train AUC: **1.000**
- Held-out (random split, n=18) AUC: **0.679**
- Held-out (H2-2026 time slice, n=70) AUC: **0.511**
- Regime-stationarity ratio (holdout / random-test): **0.753**

### Top 5 features by importance

| # | feature | importance |
|--:|---|--:|
| 1 | risk_reward | 0.4469 |
| 2 | hour_sin | 0.1946 |
| 3 | hour_cos | 0.1319 |
| 4 | day_of_week | 0.1244 |
| 5 | touch_count | 0.0590 |

## Strategic verdict

- Distinct anti-patterns identified: **partial (moderate cluster structure)**
- Most actionable cluster (highest H2-2026 frequency): **Cluster 0** (n=9, H2 freq=0.67) — day_of_week +1.39, risk_reward -0.83, hour_sin -0.65
- Reasoning: The held-out time-slice AUC dropped substantially below the random-split AUC — this is the SYSTEM_DECAY signature: anti-patterns from H1 do not generalize to H2.

## Handoff to K54

The clusters above become K54's feature-engineering hints — the trained ML classifier should attend to the highest-importance features surfaced here AND the per-cluster centroid signatures.
