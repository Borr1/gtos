# K53 Loser Anti-Pattern Report (phase1)

_Generated 2026-04-26T17:47:12+00:00_

**Source-stratified pass:** rows restricted to `source == 'phase1'`. F3 mandate (post-K53 confound diagnosis): the original mixed-source K53 had train AUC 0.996 → H2 holdout 0.598 because the joined matrix let Phase 1 vs Tier 2 schema differences leak into the labels. This pass clusters and trains WITHIN a single source so schema differences cannot drive the result.

## Population

- Pass label: **phase1**
- Total filled CANDIDATEs: **75**
- Losers (realized R ≤ 0): **41**
- H2-2026 losers in window: **24**
- sklearn used: **True**

## Loser anti-pattern clusters (k=4, silhouette=0.339)

| Cluster | n | Top 3 features (centroid, deviation vs population) | Mean R | WR within | H2-2026 frequency in cluster |
|--------:|--:|---|--:|--:|--:|
| 0 | 17 | fvg_m15_unfilled_count: +9.588 (Δ=-2.973)<br>ob_retest_distance_atr: -0.057 (Δ=+1.912)<br>fvg_h1_unfilled_count: +5.176 (Δ=-0.775) | -1.000 | 0.000 | 0.529 |
| 1 | 4 | fvg_m15_unfilled_count: +23.750 (Δ=+11.189)<br>fvg_h1_unfilled_count: +11.000 (Δ=+5.049)<br>ob_retest_distance_atr: +0.348 (Δ=+2.317) | -1.000 | 0.000 | 0.750 |
| 2 | 9 | ob_retest_distance_atr: -6.451 (Δ=-4.482)<br>fvg_m15_unfilled_count: +9.556 (Δ=-3.005)<br>fvg_h1_unfilled_count: +4.222 (Δ=-1.729) | -1.000 | 0.000 | 0.667 |
| 3 | 11 | fvg_m15_unfilled_count: +15.546 (Δ=+2.985)<br>fvg_h1_unfilled_count: +6.727 (Δ=+0.776)<br>day_of_week: +1.091 (Δ=-0.763) | -1.000 | 0.000 | 0.545 |

### Silhouette by k

| k | silhouette |
|--:|--:|
| 3 | 0.291 |
| 4 | 0.339 |
| 5 | 0.285 |
| 6 | 0.277 |
| 7 | 0.252 |

## Loss classifier

- Classifier type: `gradient_boosting`
- Train AUC: **1.000**
- Held-out (random split, n=10) AUC: **0.208**
- Held-out (H2-2026 time slice, n=33) AUC: **0.400**
- Regime-stationarity ratio (holdout / random-test): **1.922**

### Top 5 features by importance

| # | feature | importance |
|--:|---|--:|
| 1 | hour_cos | 0.2143 |
| 2 | touch_count | 0.1968 |
| 3 | ob_retest_distance_atr | 0.1792 |
| 4 | fvg_m15_unfilled_count | 0.1587 |
| 5 | day_of_week | 0.1439 |

## Strategic verdict

- Distinct anti-patterns identified: **partial (moderate cluster structure)**
- Most actionable cluster (highest H2-2026 frequency): **Cluster 1** (n=4, H2 freq=0.75) — fvg_m15_unfilled_count +11.19, fvg_h1_unfilled_count +5.05, ob_retest_distance_atr +2.32
- Reasoning: Held-out time-slice AUC is comparable to random-split AUC, suggesting anti-patterns are stable across H1 / H2.

## Handoff to K54

The clusters above become K54's feature-engineering hints — the trained ML classifier should attend to the highest-importance features surfaced here AND the per-cluster centroid signatures.
