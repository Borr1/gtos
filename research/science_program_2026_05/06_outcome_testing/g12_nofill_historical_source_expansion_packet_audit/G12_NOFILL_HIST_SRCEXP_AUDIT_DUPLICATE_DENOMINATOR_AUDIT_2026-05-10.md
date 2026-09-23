# Duplicate Denominator Audit

Route: `G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_AUDIT`
Target route: `NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET`
Promotion posture: `NO_PROMOTION_VERDICT`
Safe flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Summary

```json
{
  "artifact_family": "duplicate_denominator_audit",
  "audit_passed": true,
  "changes_live_trading_behavior": false,
  "checks": {
    "all_duplicate_count_flags_true": true,
    "primary_hashes_match_packet": true,
    "primary_unique_count_is_2": true,
    "row_level_count_is_2": true,
    "secondary_hashes_match_packet": true,
    "secondary_unique_count_is_2": true
  },
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T05:28:55Z",
  "live_effect": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "primary_duplicate_denominator": {
    "all_hashes": [
      "4f84a73bdb43ab857ecfc62fce80d76d744d2acf4b26a216200681b857eb2788",
      "b4028da1e1992c3c46600fb09c00d7b00db9b275c4ce64060712092321378152"
    ],
    "field": "nofill_duplicate_key_sha256",
    "unique_count": 2
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "row_level_count": 2,
  "secondary_duplicate_denominator": {
    "all_hashes": [
      "ed49e8e25098e3f9360d9cfb72def6ec0e64d8d9a0736bfb60eb282aa652eeeb",
      "f3238269ef5157c4e92752ad7e3e49d4d7f099b36908d7e31ae8fd9cbc1bf732"
    ],
    "field": "duplicate_group_id_sha256",
    "unique_count": 2
  },
  "target_ledger_summary": {
    "primary_unique_count": 2,
    "row_level_count": 2,
    "secondary_unique_count": 2
  },
  "validation_safe": false
}
```
