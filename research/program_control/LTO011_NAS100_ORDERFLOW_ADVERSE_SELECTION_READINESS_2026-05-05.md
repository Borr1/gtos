# LTO011 NAS100/NQ Orderflow Adverse-Selection Readiness - 2026-05-05

**Status:** `WAITING_FOR_DATABENTO_LIVE_LICENSE`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Source signature:** `b15dd54cecfda2437e0a3463013cc1da`

## Summary

NAS100/NQ orderflow remains diagnostic-only. Cached depth/thinness is useful enough to keep collecting, but current live Databento is license-blocked and sample floors are not met.

## Registered Trigger Criteria

- Policy id: `lto010_databento_live_confluence_policy_v1`
- GTOS symbol: `NAS100`
- Databento dataset/raw symbol: `GLBX.MDP3` / `NQ.FUT`
- Eligible subjects: `['NAS100 live CANDIDATE rows', 'NAS100 REJECTED_L2 rows with structural candidate context', 'NAS100 explicit operator-declared parity/context windows']`
- Default window: `{'start': 'decision_time_utc_minus_60m', 'asof_cutoff': 'decision_time_utc', 'end': 'decision_time_utc_plus_15m_for_forensic_outcome_separation_only'}`
- Join keys: `['candidate_id', 'source_opportunity_id', 'decision_time_utc', 'asof_cutoff_utc', 'trigger_id']`

## Counts And Floors

| Metric | Current | Floor |
| --- | --- | --- |
| NAS100 broker actual-R rows | 1 | 20 |
| All-symbol broker actual-R rows | 5 | context only |
| Cached MBP10 candidate rows | 12 | 30 |
| Cached MBO candidate rows | 12 | diagnostic only |
| Live MBP10 rows | 0 | waiting |
| Declared NQ Databento requests | 5 | registered |

## Live Databento Status

- Latest confluence status: `LIVE_SESSION_FAILED_NO_LICENSE`
- Latest budget status: `LIVE_SESSION_FAILED_NO_LICENSE`
- License blocker: `True`
- Latest message: `BentoError: A live data license is required to access GLBX.MDP3.`

## Readiness Gates

| Gate | State |
| --- | --- |
| databento_live_license_available | False |
| broker_actual_r_floor_met | False |
| mbp10_candidate_floor_met | False |
| promotion_claim_allowed | False |
| adverse_selection_filter_allowed | False |

## Forward Feature Families

| Family | Priority | Fields |
| --- | --- | --- |
| depth_availability_thinness | KEEP_FORWARD_DEFAULT | event15_median_total_depth10, event15_thin_depth10_rate, event15_median_total_depth20, event15_thin_depth20_rate, pre60_median_total_depth10, pre60_median_total_depth20 |
| depth_imbalance | KEEP_AS_SECONDARY_DIAGNOSTIC | event15_median_depth10_imbalance, event15_median_depth20_imbalance |
| near_touch_pull_add_pressure | MBO_ONLY_LOW_CONFIDENCE | event15_near10_pull_pressure, event15_near10_net_liquidity, event15_near10_add_size, event15_near10_remove_size |
| wall_concentration | MONITOR_ONLY | event15_median_wall_concentration20, event15_median_max_bid_wall, event15_median_max_ask_wall |

## Boundary

No live binary orderflow filter, signal, risk modifier, or entry rule is created by this row.

## Next Action

After Databento GLBX.MDP3 live licensing is activated, run only registered NAS100/NQ candidate windows through the LTO-010 collector and keep MBO targeted to explicit unanswered queue questions.

## Non-Claims

- This audit made zero Databento calls.
- This audit made zero AI, canary, MT5 order, or execution calls.
- This does not create a live filter, signal, entry rule, risk modifier, or promotion dossier.
