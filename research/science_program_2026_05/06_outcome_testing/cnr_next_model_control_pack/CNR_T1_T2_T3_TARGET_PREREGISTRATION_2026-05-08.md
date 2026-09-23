# CNR T1 T2 T3 Target Preregistration - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_T1_T2_T3_TARGET_PREREGISTRATION",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-08",
  "families": {
    "CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE": {
      "exact_blocker": "No result lane may score T1 until fixed_r_multiple and stop source are frozen in a packet.",
      "invalid_tiny_residual_gate": "invalid stop or non-positive fixed target geometry is excluded; no OTI7/OTI8 outcome-derived threshold is introduced.",
      "pre_outcome_target_contract": "Fixed-R target prices are generated from executable quote and source-hashed stop before path opening.",
      "price_side_rule": "LONG entry quote uses ask and terminal target/stop uses bid; SHORT entry quote uses bid and terminal target/stop uses ask.",
      "sample_floor_dsr_pbo_effective_n_policy": ">=30 countable duplicate groups, effective_N>=3, DSR p<0.01, PBO<0.4 for promotion dossier only.",
      "source_asof_fields": [
        "executable_quote_price",
        "executable_quote_side",
        "quote_timestamp_utc",
        "stop_loss",
        "stop_source_hash",
        "fixed_r_multiple",
        "target_price"
      ],
      "stop_model": "frozen source stop; invalid if stop is not beyond executable quote in the risk direction."
    },
    "CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL": {
      "exact_blocker": "Current CNR rows bind original TP1 only; no source-hashed structural-level rank/source snapshot is available for CNR_T2.",
      "invalid_tiny_residual_gate": "reject target already passed or invalid stop before scoring; tiny residual bins are descriptive until separately preregistered.",
      "pre_outcome_target_contract": "Target is a structural level selected from an as-of source snapshot with hierarchy/rank policy frozen before terminal path opening.",
      "price_side_rule": "same executable/terminal quote-side rule as T1.",
      "sample_floor_dsr_pbo_effective_n_policy": ">=30 countable duplicate groups per level family plus concentration and source-family diagnostics.",
      "source_asof_fields": [
        "structural_level_id",
        "level_price",
        "level_timestamp_utc",
        "level_source_hash",
        "hierarchy_rank",
        "selection_rule_id"
      ],
      "stop_model": "source stop frozen independently from structural target source."
    },
    "CNR_T3_TERMINAL_TIMEBOX_OR_LIFECYCLE": {
      "exact_blocker": "Promotion/result scoring remains blocked; Workstream C builds only source-hashed labels for the six no-terminal rows.",
      "invalid_tiny_residual_gate": "invalid stop or missing source yields source/geometry blocker labels, not rescue scoring.",
      "pre_outcome_target_contract": "Lifecycle labels are categorical terminal/timebox states, not R results.",
      "price_side_rule": "same terminal quote-side rule as T1 for detecting target/stop event order; labels do not compute R.",
      "sample_floor_dsr_pbo_effective_n_policy": "lifecycle packet can be built at n=6, but validation/promotion remains blocked below sample floor.",
      "source_asof_fields": [
        "timebox_policy_id",
        "path_start_utc",
        "original_horizon_end_utc",
        "extended_horizon_end_utc",
        "path_source_files",
        "path_source_sha256"
      ],
      "stop_model": "source stop frozen from input row; lifecycle labels can identify target/stop/still-open/source-insufficient only."
    }
  },
  "generated_at_utc": "2026-05-08T06:01:13Z",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_account_calls": 0,
  "mt5_order_calls": 0,
  "no_outcomes_scored": true,
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "schema_version": "cnr_next_model_control_pack_v1",
  "status": "INPUT_ONLY_TARGET_FAMILIES_PREREGISTERED_NO_RESULT_SCORING",
  "validation_safe": false
}
```
