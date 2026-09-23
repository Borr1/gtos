# CNR Timing Target No-Leak Duplicate Sample-Floor Audit - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_TIMING_TARGET_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT",
  "blocked_94_not_scored_proof": {
    "blocked_rows": 94,
    "g12_blocked_audit_source": "research/science_program_2026_05/06_outcome_testing/g12_cnr061_sidecar_reaudit/G12_CNR061_BLOCKED_ROW_EXCLUSION_AUDIT_2026-05-08.json",
    "packet_rows_from_blocked_set": [],
    "status": "PASS_94_BLOCKED_ROWS_NOT_SCORED"
  },
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-08",
  "duplicate_policy": {
    "do_not_join_on_duplicate_group_alone": true,
    "duplicate_denominator_key_counts": {
      "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": 3,
      "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": 3
    },
    "duplicate_group_counts": {
      "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222": 6
    }
  },
  "exact_six_row_scope_check": {
    "oti8_no_terminal_sidecar_hashes": [
      "2d82227ec0dfd01b140471932701e4885dd065fca5c618d5dc2bf0e9c9da76ab",
      "41da6796ddb651413f558333ae52db302fc76a2863f00c204bee6ef37d10a23e",
      "4e76395873c48a3b9f20114c20d0247c92ef80846b170ee9b2f2d52919fa8d04",
      "5a7146782dc6564ac7a04ba163bd3d262ab731c2e1c3b6706ea14aeed979c7bb",
      "5ee22ed74a3eb5c16b1f7857d29346b2713ddbdb8b9a61de9f57c8414889959c",
      "63d08012951489781b7f892fe2d22a968e88101ded2429354aac16e68d3d93c8"
    ],
    "packet_sidecar_hashes": [
      "2d82227ec0dfd01b140471932701e4885dd065fca5c618d5dc2bf0e9c9da76ab",
      "41da6796ddb651413f558333ae52db302fc76a2863f00c204bee6ef37d10a23e",
      "4e76395873c48a3b9f20114c20d0247c92ef80846b170ee9b2f2d52919fa8d04",
      "5a7146782dc6564ac7a04ba163bd3d262ab731c2e1c3b6706ea14aeed979c7bb",
      "5ee22ed74a3eb5c16b1f7857d29346b2713ddbdb8b9a61de9f57c8414889959c",
      "63d08012951489781b7f892fe2d22a968e88101ded2429354aac16e68d3d93c8"
    ],
    "status": "PASS_EXACT_SIX"
  },
  "generated_at_utc": "2026-05-08T06:01:14Z",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_account_calls": 0,
  "mt5_order_calls": 0,
  "no_leak_scan": {
    "forbidden_packet_row_hits": [],
    "status": "PASS"
  },
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "sample_floor": {
    "countable_rows": 2,
    "packet_row_count": 6,
    "reason": "n=6 row-level and one duplicate group is an input packet only; validation/promotion sample floor is not met.",
    "sample_floor_for_validation_met": false,
    "unique_duplicate_groups": 1
  },
  "schema_version": "cnr_next_model_control_pack_v1",
  "source_contract_inventory_files": 309,
  "status": "PASS_INPUT_ONLY_NOLEAK_DUPLICATE_SAMPLE_BOUNDARY",
  "validation_safe": false
}
```
