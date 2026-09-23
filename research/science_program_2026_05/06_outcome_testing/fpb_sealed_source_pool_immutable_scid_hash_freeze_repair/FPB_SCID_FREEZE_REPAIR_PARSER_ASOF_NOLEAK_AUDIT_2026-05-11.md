# Parser Asof No Leak Audit

- Route: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR`
- Evidence class: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `False`
- outcome_review_opened: `False`
- live_effect: `False`

## Summary

```json
{
  "all_hard_floors_preserved": true,
  "parser_row_count": 9
}
```
## Payload

```json
{
  "artifact_family": "parser_asof_no_leak_audit",
  "changes_live_trading_behavior": false,
  "checks": {
    "all_hard_floors_preserved": true,
    "all_parser_status_ok": true,
    "all_record_sizes_are_40": true,
    "no_broker_account_order_history_position_fields_read": true,
    "scid_to_asof_gate_explicit": true
  },
  "credentials_touched": false,
  "evidence_class": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY",
  "generated_at_utc": "2026-05-11T10:22:32Z",
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
  "parser_rows": [
    {
      "as_of_rule": "future SCID-to-asof-bar derivation must read only records with timestamp >= eligible_segment_start_utc_hard_floor and <= segment_last_record_utc from this manifest",
      "broker_account_order_history_position_fields_read": false,
      "eligible_hard_floor_preserved": true,
      "forbidden_fields_read": [],
      "header_size": 56,
      "no_leak_rule": "native SCID records contain time, OHLC, volume/num-trades/bid-volume/ask-volume fields only",
      "parser_implementation": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/build_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_2026_05_11.py",
      "parser_implementation_sha256": "dd4ff50579294b871f1611edee375822a73072f49c9ff6a885033738624de2bc",
      "parser_status": "SCID_HEADER_AND_RECORD_PARSER_OK",
      "record_size": 40,
      "remaining_gate": "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT",
      "segment_first_record_utc": "2026-05-01T20:59:41Z",
      "segment_last_record_utc": "2026-05-11T10:12:19Z",
      "source": "6BM26-CME.scid",
      "symbol": "GBPUSD_6B",
      "version": 1
    },
    {
      "as_of_rule": "future SCID-to-asof-bar derivation must read only records with timestamp >= eligible_segment_start_utc_hard_floor and <= segment_last_record_utc from this manifest",
      "broker_account_order_history_position_fields_read": false,
      "eligible_hard_floor_preserved": true,
      "forbidden_fields_read": [],
      "header_size": 56,
      "no_leak_rule": "native SCID records contain time, OHLC, volume/num-trades/bid-volume/ask-volume fields only",
      "parser_implementation": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/build_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_2026_05_11.py",
      "parser_implementation_sha256": "dd4ff50579294b871f1611edee375822a73072f49c9ff6a885033738624de2bc",
      "parser_status": "SCID_HEADER_AND_RECORD_PARSER_OK",
      "record_size": 40,
      "remaining_gate": "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT",
      "segment_first_record_utc": "2026-05-10T22:00:00Z",
      "segment_last_record_utc": "2026-05-11T10:12:19Z",
      "source": "6EM26-CME.scid",
      "symbol": "EURUSD",
      "version": 1
    },
    {
      "as_of_rule": "future SCID-to-asof-bar derivation must read only records with timestamp >= eligible_segment_start_utc_hard_floor and <= segment_last_record_utc from this manifest",
      "broker_account_order_history_position_fields_read": false,
      "eligible_hard_floor_preserved": true,
      "forbidden_fields_read": [],
      "header_size": 56,
      "no_leak_rule": "native SCID records contain time, OHLC, volume/num-trades/bid-volume/ask-volume fields only",
      "parser_implementation": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/build_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_2026_05_11.py",
      "parser_implementation_sha256": "dd4ff50579294b871f1611edee375822a73072f49c9ff6a885033738624de2bc",
      "parser_status": "SCID_HEADER_AND_RECORD_PARSER_OK",
      "record_size": 40,
      "remaining_gate": "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT",
      "segment_first_record_utc": "2026-05-01T20:59:15Z",
      "segment_last_record_utc": "2026-05-11T10:12:12Z",
      "source": "6JM26-CME.scid",
      "symbol": "USDJPY_6J",
      "version": 1
    },
    {
      "as_of_rule": "future SCID-to-asof-bar derivation must read only records with timestamp >= eligible_segment_start_utc_hard_floor and <= segment_last_record_utc from this manifest",
      "broker_account_order_history_position_fields_read": false,
      "eligible_hard_floor_preserved": true,
      "forbidden_fields_read": [],
      "header_size": 56,
      "no_leak_rule": "native SCID records contain time, OHLC, volume/num-trades/bid-volume/ask-volume fields only",
      "parser_implementation": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/build_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_2026_05_11.py",
      "parser_implementation_sha256": "dd4ff50579294b871f1611edee375822a73072f49c9ff6a885033738624de2bc",
      "parser_status": "SCID_HEADER_AND_RECORD_PARSER_OK",
      "record_size": 40,
      "remaining_gate": "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT",
      "segment_first_record_utc": "2026-05-01T20:59:05Z",
      "segment_last_record_utc": "2026-05-11T10:12:11Z",
      "source": "GCM26-COMEX.scid",
      "symbol": "XAUUSD_GC",
      "version": 1
    },
    {
      "as_of_rule": "future SCID-to-asof-bar derivation must read only records with timestamp >= eligible_segment_start_utc_hard_floor and <= segment_last_record_utc from this manifest",
      "broker_account_order_history_position_fields_read": false,
      "eligible_hard_floor_preserved": true,
      "forbidden_fields_read": [],
      "header_size": 56,
      "no_leak_rule": "native SCID records contain time, OHLC, volume/num-trades/bid-volume/ask-volume fields only",
      "parser_implementation": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/build_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_2026_05_11.py",
      "parser_implementation_sha256": "dd4ff50579294b871f1611edee375822a73072f49c9ff6a885033738624de2bc",
      "parser_status": "SCID_HEADER_AND_RECORD_PARSER_OK",
      "record_size": 40,
      "remaining_gate": "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT",
      "segment_first_record_utc": "2026-05-01T20:59:06Z",
      "segment_last_record_utc": "2026-05-11T10:12:19Z",
      "source": "MGCM26-COMEX.scid",
      "symbol": "XAUUSD_MGC",
      "version": 1
    },
    {
      "as_of_rule": "future SCID-to-asof-bar derivation must read only records with timestamp >= eligible_segment_start_utc_hard_floor and <= segment_last_record_utc from this manifest",
      "broker_account_order_history_position_fields_read": false,
      "eligible_hard_floor_preserved": true,
      "forbidden_fields_read": [],
      "header_size": 56,
      "no_leak_rule": "native SCID records contain time, OHLC, volume/num-trades/bid-volume/ask-volume fields only",
      "parser_implementation": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/build_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_2026_05_11.py",
      "parser_implementation_sha256": "dd4ff50579294b871f1611edee375822a73072f49c9ff6a885033738624de2bc",
      "parser_status": "SCID_HEADER_AND_RECORD_PARSER_OK",
      "record_size": 40,
      "remaining_gate": "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT",
      "segment_first_record_utc": "2026-05-01T20:59:01Z",
      "segment_last_record_utc": "2026-05-11T10:11:57Z",
      "source": "MYMM26-CBOT.sci
... truncated in markdown; see matching JSON artifact ...
```
