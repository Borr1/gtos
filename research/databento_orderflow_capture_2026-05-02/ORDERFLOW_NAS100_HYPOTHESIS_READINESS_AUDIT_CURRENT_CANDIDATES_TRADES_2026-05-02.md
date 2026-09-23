# NAS100 Orderflow Hypothesis Readiness Audit

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`
Registration verdict: `DO_NOT_REGISTER_REPLAY_HYPOTHESIS_YET`

## Summary

NAS100 orderflow evidence is useful for failure forensics but is not ready for a registered replay hypothesis. The bottleneck is not feature imagination; it is sparse, selected, winner-poor labels.

## Coverage

- Orderflow rows: 12
- Synthetic/path labels: 11
- Actual broker-R labels: 1
- Coverage classes: {'actual_realized_r_available': 1, 'candidate_join_missing': 1, 'no_actual_by_design_pre_execution_reject': 10}
- Final outcomes: {'LIMIT_PLACED': 1, 'REJECTED_L2': 10, 'none': 1}
- Synthetic outcomes: {'SL': 10, 'TP': 1, 'none': 1}
- Label-count source: coverage
- Synthetic winners/losers for readiness gates: 1 / 10

## Feature Counts

| Schema | feature rows | candidate rows | context rows | synthetic winners | synthetic losers |
|---|---:|---:|---:|---:|---:|
| trades | 12 | 12 | 0 | 0 | 0 |
| mbp1 | 43 | 11 | 32 | 1 | 10 |
| mbp10 | 43 | 11 | 32 | 1 | 10 |

## Key Deltas

| Schema | Feature | candidate-context | winner-loser |
|---|---|---:|---:|
| trades | event15_absorption_volume_per_tick | n/a | n/a |
| trades | event15_buy_fraction | n/a | n/a |
| trades | event15_signed_volume | n/a | n/a |
| trades | profile_nearest_lvn_distance_ticks | n/a | n/a |
| mbp1 | event15_median_book_imbalance | 0.0000 | 0.0000 |
| mbp1 | event15_median_top_liquidity | n/a | n/a |
| mbp1 | event15_thin_top_book_rate | 0.0093 | -0.0494 |
| mbp10 | event15_median_depth10_imbalance | 0.0225 | -0.0135 |
| mbp10 | event15_median_max_ask_wall | -2.0000 | 2.0000 |
| mbp10 | event15_median_max_bid_wall | -2.0000 | 2.0000 |
| mbp10 | event15_median_near_far_ratio | -0.0152 | 0.0152 |
| mbp10 | event15_median_total_depth10 | -28.0000 | 34.0000 |
| mbp10 | event15_thin_depth10_rate | -0.0053 | -0.1693 |

## Readiness Gates

- Passed: False
- Failed gates: ['actual_r_coverage_min_20', 'synthetic_winner_min_10', 'mbp10_candidate_min_30']
- Gate states: {'actual_r_coverage_min_20': False, 'synthetic_winner_min_10': False, 'synthetic_loser_min_10': True, 'mbp10_candidate_min_30': False, 'context_min_30': True}

## Candidate Hypothesis

- status: CANDIDATE_NOT_REGISTERED
- name: NAS100 thin-depth adverse-selection filter
- scope: NAS100 GTOS CANDIDATE rows only
- as_of_window: pre60 + event15 only; no post-event features
- feature_family: MBP-10 total depth and thin-depth rate, with trades-level signed-flow diagnostics as covariates
- label_policy: separate actual broker R, synthetic/path R, and fill/no-fill labels
- non_registered_reason: Current evidence is selected, sparse, and winner-poor; freezing a threshold now would be threshold mining.

## Readout

- NAS100 coverage is actual-R 1/12 and synthetic/path 11/12.
- Synthetic outcome contrast is winner n=1 and loser n=10 from coverage; the winner side is still too sparse for stable winner-minus-loser feature direction.
- MBP-10 remains the more relevant depth view than MBP-1, but current candidate sample is n=11 and context n=32.
- The strongest current MBP-10 clue is thin/depth related: candidate-context event15 total-depth delta=-28.0, winner-loser total-depth delta=34.0.
- Registration gate passed=False failed=['actual_r_coverage_min_20', 'synthetic_winner_min_10', 'mbp10_candidate_min_30']; therefore the correct action is forward data collection plus pre-registration criteria, not replay.

## Ambiguity Ledger

- Current NAS100 windows are selected from a known failure cluster, not a population-random sample.
- Actual broker-R coverage is too sparse to know whether the synthetic/path cluster translates to live P&L.
- Winner-minus-loser deltas are dominated by one synthetic winner.
- MBP-10 one-second snapshots do not prove causal queue withdrawal or order identity.
- No threshold has been frozen; any threshold chosen now would be post-hoc.

## Open Questions

1. Does thin top-10 depth persist as a NAS100 failure signature in future candidate windows?
2. Is thin depth a causal adverse-selection condition or merely a correlate of the same structural state?
3. Do actual broker fills show the same pattern once forward actual-R coverage improves?
4. Can a no-threshold or rank-only hypothesis be defined before the next replay to avoid threshold mining?
5. Does MBP-10 add enough over MBP-1 to justify targeted collection beyond forensic windows?

## Next Steps

1. Do not register or replay a NAS100 orderflow filter yet.
2. Forward-collect trades + MBP-1 for all supported NAS100 candidate windows; add MBP-10 only for pre-declared forensic buckets.
3. Before the next replay, freeze a rank-only or quantile-based criterion with explicit train/test separation.
4. Require materially larger label coverage before promotion: actual-R rows or clean synthetic labels must be separated by label type.
5. Keep MBO deferred until MBP-10 leaves an explicit queue-behavior question unanswered.
