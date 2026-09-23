# OTI2 Risk-Bank Methodology Report - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Result status:** `RESULT_QUARANTINED_DISCOVERY_ONLY`

## Effective N And Statistics

| item | value |
| --- | --- |
| accepted unique duplicate groups | 86 |
| riskbank primary effective N | 0 |
| descriptive non-ambiguous path n | 51 |
| validation floor | 150 |
| validation floor pass | False |
| DSR | not_computable |
| PBO | not_computable |

## Risk-Bank Scoreability

Status: `not_computable`.

Missing packet fields:

- `estimated_remaining_cost_r`
- `leg_id`
- `open_leg_stop_if_hit_r`
- `realized_closed_leg_r`
- `reentry_leg`
- `reentry_state`
- `risk_bank_after_action_r`
- `risk_bank_before_action_r`
- `structural_lock_event`
- `synthetic_closed_leg_r`
- `synthetic_episode_reward_r`
- `synthetic_open_leg_stop_if_hit_r`

## Not Computable Reasons

- `dsr_not_computable_no_unseen_validation_split`
- `dsr_not_computable_effective_n_below_150_floor`
- `validation_stats_not_computable_result_quarantined_discovery_only`
- `riskbank_primary_metric_not_computable_missing_leg_level_reentry_ledger`
- `pbo_not_computable_no_strategy_variant_matrix`
- `pbo_not_computable_no_train_test_or_cpcv_blocks`
- `riskbank_primary_metric_not_computable_missing_leg_level_reentry_ledger`
