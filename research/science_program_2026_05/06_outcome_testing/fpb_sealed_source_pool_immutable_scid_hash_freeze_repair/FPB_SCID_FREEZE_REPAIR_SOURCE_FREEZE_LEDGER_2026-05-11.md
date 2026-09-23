# Source Freeze Ledger

- Route: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR`
- Evidence class: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `False`
- outcome_review_opened: `False`
- live_effect: `False`

## Summary

```json
{
  "candidate_count": 9,
  "repaired_source_count": 9,
  "source_access_blocker_count": 0,
  "terminal_repair_status": "ALL_9_SOURCES_REPAIRED"
}
```
## Payload

```json
{
  "all_9_sources_repaired": true,
  "all_9_sources_repaired_or_exact_blocked": true,
  "artifact_family": "source_freeze_ledger",
  "candidate_count": 9,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY",
  "freeze_rows": [
    {
      "chosen_repair_policy": "BOUNDED_ELIGIBLE_SEGMENT",
      "coverage_end_drift_vs_source_packet": true,
      "current_mutable_metadata": {
        "absolute_path": "C:\\SierraChart\\Data\\6BM26-CME.scid",
        "coverage_end_utc": "2026-05-11T10:12:19Z",
        "coverage_start_utc": "2025-10-29T14:16:38Z",
        "current_full_file_hash_status": "MUTABLE_REFERENCE_ONLY_NOT_ACCEPTED_SOURCE_EVIDENCE",
        "current_full_file_sha256_reference_only": "4e1886e4428d45d967e50121aa68af03f531632e6e0048edff87b9ed5cbab4ef",
        "exists": true,
        "file_name": "6BM26-CME.scid",
        "first_record_timestamp_us": 3970908998206000,
        "header_sha256": "907f092cd22a0e25ae7f88e46ca90e268506cd89733023a358ebafa75e23211d",
        "header_size": 56,
        "last_record_timestamp_us": 3987655939912000,
        "magic": "SCID",
        "parser_status": "SCID_HEADER_AND_RECORD_PARSER_OK",
        "record_count": 1539403,
        "record_size": 40,
        "remainder_bytes": 0,
        "size_bytes": 61576176,
        "utc_start_index": 0,
        "version": 1
      },
      "duplicate_source_decision_prior": "UNIQUE_NATIVE_HASH_NOT_SELECTED_AND_POST_EMBARGO_SEGMENT_EXISTS",
      "duplicate_source_decision_repaired": "UNIQUE_SEGMENT_HASH_NOT_DISCOVERY_SELECTED_AND_G12_REAUDIT_REQUIRED",
      "eligible_hard_floor_preserved": true,
      "eligible_segment_start_utc_hard_floor": "2026-05-01T20:59:01Z",
      "g12_failure_anatomy": "native Sierra SCID file is append-mutable after packet materialization, so full-file source hash/size/end coverage drifted",
      "g12_recomputed_coverage_end_utc": "2026-05-11T09:32:02Z",
      "g12_recomputed_full_file_sha256": "29923e17d0d40310ec943429864f7178b163ff3c86970524d11c344494904e2e",
      "g12_recomputed_size_bytes": 61540776,
      "no_leak_status": "SOURCE_TIME_ORDERED_NATIVE_RECORDS_NO_BROKER_ACCOUNT_ORDER_OR_RESULT_FIELDS_READ",
      "parser_asof_status": "SOURCE_LOCAL_FILE_ONLY_REQUIRES_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_BEFORE_REPLAY",
      "proxy_note": "GBP futures proxy",
      "raw_snapshot_policy": "NO_RAW_SNAPSHOT_WRITTEN_OR_COMMITTED",
      "record_count_drift_vs_source_packet": 1741,
      "refreshed_coverage_end_utc": "2026-05-11T10:12:19Z",
      "refreshed_coverage_start_utc": "2025-10-29T14:16:38Z",
      "refreshed_record_count": 1539403,
      "refreshed_size_bytes": 61576176,
      "remaining_gates_before_validation": [
        "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT",
        "separate validation-execution prompt after source-control contract acceptance"
      ],
      "repair_partition_assignment": "SEALED_HISTORICAL_SOURCE_POOL_CANDIDATE_G12_REAUDIT_REQUIRED",
      "repair_status": "REPAIRED_BOUNDED_ELIGIBLE_SEGMENT_HASH_FROZEN",
      "repaired_immutable_metadata": {
        "append_mutability_repaired_by": "hash only frozen record byte range; later EOF growth is outside segment_byte_end_exclusive",
        "eligible_segment_start_utc_hard_floor": "2026-05-01T20:59:01Z",
        "immediate_rehash_matches": true,
        "immediate_rehash_sha256": "91ae9eb8ca0493cd301ae7dd3be2c08d2f8529473ac049206187f3b805e2a263",
        "policy": "BOUNDED_ELIGIBLE_SEGMENT",
        "pre_eligible_records_excluded": 1369662,
        "records_after_segment_may_append_without_hash_effect": true,
        "segment_byte_end_exclusive": 61576176,
        "segment_byte_length": 6789640,
        "segment_byte_start": 54786536,
        "segment_descriptor_sha256": "78109494711d8ee2de98c7d0f411733c73f07af6bd2cd1a20006a3d1e26dab0a",
        "segment_first_record_utc": "2026-05-01T20:59:41Z",
        "segment_last_record_utc": "2026-05-11T10:12:19Z",
        "segment_record_count": 169741,
        "segment_record_end_index_inclusive": 1539402,
        "segment_record_start_index": 1369662,
        "segment_records_sha256": "91ae9eb8ca0493cd301ae7dd3be2c08d2f8529473ac049206187f3b805e2a263",
        "segment_status": "REPAIRED_BOUNDED_ELIGIBLE_SEGMENT_HASH_FROZEN",
        "source_file_name": "6BM26-CME.scid",
        "source_path": "C:\\SierraChart\\Data\\6BM26-CME.scid"
      },
      "segment_hash_is_discovery_selected_source_hash": false,
      "source": "6BM26-CME.scid",
      "source_family": "SIERRA_NATIVE_SCID",
      "source_full_file_hash_reference_only_not_accepted": true,
      "source_instrument": "6BM26-CME",
      "source_packet_coverage_end_utc": "2026-05-11T08:45:00Z",
      "source_packet_coverage_start_utc": "2025-10-29T14:16:38Z",
      "source_packet_eligible_segment_end_utc": "2026-05-11T08:45:00Z",
      "source_packet_full_file_sha256": "2ec058872a29a643d2e46b30c93fc11a774cbebede59f748705339aeb0494540",
      "source_packet_partition_assignment": "SEALED_HISTORICAL_SOURCE_POOL_CANDIDATE_G12_AUDIT_REQUIRED",
      "source_packet_record_count": 1537662,
      "source_packet_size_bytes": 61506536,
      "source_path": "C:\\SierraChart\\Data\\6BM26-CME.scid",
      "symbol": "GBPUSD_6B"
    },
    {
      "chosen_repair_policy": "BOUNDED_ELIGIBLE_SEGMENT",
      "coverage_end_drift_vs_source_packet": true,
      "current_mutable_metadata": {
        "absolute_path": "C:\\SierraChart\\Data\\6EM26-CME.scid",
        "coverage_end_utc": "2026-05-11T10:12:19Z",
        "coverage_start_utc": "2025-10-29T19:16:06Z",
        "current_full_file_hash_status": "MUTABLE_REFERENCE_ONLY_NOT_ACCEPTED_SOURCE_EVIDENCE",
        "current_full_file_sha256_reference_only": "a1376d5933d804f13b0922a366ead7b6160ae8e877c54e1bbbcf754a7adb95fe",
        "exists": true,
        "file_name": "6EM26-CME.scid",
        "first_record_timestamp_us": 3970926966452000,
        "header_sha256": "907f092cd22a0e25ae7f88e46ca90e268506cd89733023a358ebafa75e23211d",
        "header_size": 56,
        "last_record_timestamp_us": 3987655939911004,
        "magic": "SCID",
        "parser_status": "SCID_HEADER_AND_RECORD_PARSER_OK",
        "record_count": 3893156,
        "record_size": 40,
        "remainder_bytes": 0,
        "size_bytes": 155726296,
        "utc_start_index": 0,
        "version": 1
      },
      "duplicate_source_decision_prior": "UNIQUE_NATIVE_HASH_NOT_SELECTED_AND_POST_EMBARGO_SEGMENT_EXISTS",
      "duplicate_source_decision_repaired": "UNIQUE_SEGMENT_HASH_NOT_DISCOVERY_SELECTED_AND_G12_REAUDIT_REQUIRED",
      "eligible_hard_floor_preserved": true,
      "eligible_segment_start_utc_hard_floor": "2026-05-08T23:45:01Z",
      "g12_failure_anatomy": "native Sierra SCID file is append-mutable after packet materialization, so full-file source hash/size/end coverage drifted",
      "g12_recomputed_coverage_end_utc": "2026-05-11T09:32:23Z",
      "g12_recomputed_full_file_sha256": "ea8209c10b4983121080b07fc1d0dbdb320711a8b2983d898d6d1e39b269ab57",
      "g12_recomputed_size_bytes": 155675176,
      "no_leak_status": "SOURCE_TIME_ORDERED_NATIVE_RECORDS_NO_BROKER_ACCOUNT_ORDER_OR_RESULT_FIELDS_READ",
      "parser_asof_status": "SOURCE_LOCAL_FILE_ONLY_REQUIRES_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_BEFORE_REPLAY",
      "proxy_note": "EUR futures proxy",
      "raw_snapshot_policy": "NO_RAW_SNAPSHOT_WRITTEN_OR_COMMITTED",
      "record_count_drift_vs_source_packet": 2694,
      "refreshed_coverage_end_utc": "2026-05-11T10:12:19Z",
      "refreshed_coverage_start_utc": "2025-10-29T19:16:06Z",
      "refreshed_record_count": 3893156,
      "refreshed_size_bytes": 155726296,
      "remaining_gates_before_validation": [
        "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT",
        "separate validation-execution prompt after source-control contract acceptance"
      ],
      "repair_partition_assignment": "SEALED_HISTO
... truncated in markdown; see matching JSON artifact ...
```
