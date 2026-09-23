# Snapshot Segment Manifest

- Route: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR`
- Evidence class: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `False`
- outcome_review_opened: `False`
- live_effect: `False`

## Summary

```json
{
  "policy": "bounded eligible segment hashes",
  "raw_snapshot_files_written": 0,
  "segment_count": 9
}
```
## Payload

```json
{
  "artifact_family": "snapshot_segment_manifest",
  "changes_live_trading_behavior": false,
  "chosen_policy": "BOUNDED_ELIGIBLE_SEGMENT",
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
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "raw_snapshot_commit_policy": "NO_RAW_SCID_OR_SEGMENT_BYTES_COMMITTED; COMMITTED HASH_MANIFEST_ONLY",
  "raw_snapshot_files_committed": 0,
  "raw_snapshot_files_written": 0,
  "route_id": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR",
  "schema_version": "fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_v1",
  "segment_count": 9,
  "segments": [
    {
      "append_safety_rule": "hash only frozen record byte range; later EOF growth is outside segment_byte_end_exclusive",
      "eligible_segment_start_utc_hard_floor": "2026-05-01T20:59:01Z",
      "immediate_rehash_matches": true,
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
      "snapshot_file_written": false,
      "snapshot_policy": "NOT_USED_BOUNDED_SEGMENT_HASH_IS_COMMITTED",
      "source": "6BM26-CME.scid",
      "source_path": "C:\\SierraChart\\Data\\6BM26-CME.scid",
      "symbol": "GBPUSD_6B"
    },
    {
      "append_safety_rule": "hash only frozen record byte range; later EOF growth is outside segment_byte_end_exclusive",
      "eligible_segment_start_utc_hard_floor": "2026-05-08T23:45:01Z",
      "immediate_rehash_matches": true,
      "segment_byte_end_exclusive": 155726296,
      "segment_byte_length": 744920,
      "segment_byte_start": 154981376,
      "segment_descriptor_sha256": "e7f997ce783fd0ea15e0d48a0fb74b756698a8ea2b4b243ea8f56d1c8f4a2783",
      "segment_first_record_utc": "2026-05-10T22:00:00Z",
      "segment_last_record_utc": "2026-05-11T10:12:19Z",
      "segment_record_count": 18623,
      "segment_record_end_index_inclusive": 3893155,
      "segment_record_start_index": 3874533,
      "segment_records_sha256": "3e755a319b4f895c27203d63fd7ddb310b81066384f93f007943bddc94ca2053",
      "snapshot_file_written": false,
      "snapshot_policy": "NOT_USED_BOUNDED_SEGMENT_HASH_IS_COMMITTED",
      "source": "6EM26-CME.scid",
      "source_path": "C:\\SierraChart\\Data\\6EM26-CME.scid",
      "symbol": "EURUSD"
    },
    {
      "append_safety_rule": "hash only frozen record byte range; later EOF growth is outside segment_byte_end_exclusive",
      "eligible_segment_start_utc_hard_floor": "2026-05-01T20:59:01Z",
      "immediate_rehash_matches": true,
      "segment_byte_end_exclusive": 119363656,
      "segment_byte_length": 16543160,
      "segment_byte_start": 102820496,
      "segment_descriptor_sha256": "cb1e18f67e507ccc4b37a362e2ac730c975c9847ef714eaf325ae95ee0b6ac09",
      "segment_first_record_utc": "2026-05-01T20:59:15Z",
      "segment_last_record_utc": "2026-05-11T10:12:12Z",
      "segment_record_count": 413579,
      "segment_record_end_index_inclusive": 2984089,
      "segment_record_start_index": 2570511,
      "segment_records_sha256": "c7bcc874ee594d78d51c1637c249372b59cf6e16194fb67fdea446a33b3832eb",
      "snapshot_file_written": false,
      "snapshot_policy": "NOT_USED_BOUNDED_SEGMENT_HASH_IS_COMMITTED",
      "source": "6JM26-CME.scid",
      "source_path": "C:\\SierraChart\\Data\\6JM26-CME.scid",
      "symbol": "USDJPY_6J"
    },
    {
      "append_safety_rule": "hash only frozen record byte range; later EOF growth is outside segment_byte_end_exclusive",
      "eligible_segment_start_utc_hard_floor": "2026-05-01T20:59:01Z",
      "immediate_rehash_matches": true,
      "segment_byte_end_exclusive": 148543656,
      "segment_byte_length": 21133840,
      "segment_byte_start": 127409816,
      "segment_descriptor_sha256": "c001576c6812abfd1cc29964cbd55129318e3a9a1cfa5217c6603e268995540d",
      "segment_first_record_utc": "2026-05-01T20:59:05Z",
      "segment_last_record_utc": "2026-05-11T10:12:11Z",
      "segment_record_count": 528346,
      "segment_record_end_index_inclusive": 3713589,
      "segment_record_start_index": 3185244,
      "segment_records_sha256": "4be989f00e606c8e7478064a3d2610c0318ab87a7791824812dea1da2181f1af",
      "snapshot_file_written": false,
      "snapshot_policy": "NOT_USED_BOUNDED_SEGMENT_HASH_IS_COMMITTED",
      "source": "GCM26-COMEX.scid",
      "source_path": "C:\\SierraChart\\Data\\GCM26-COMEX.scid",
      "symbol": "XAUUSD_GC"
    },
    {
      "append_safety_rule": "hash only frozen record byte range; later EOF growth is outside segment_byte_end_exclusive",
      "eligible_segment_start_utc_hard_floor": "2026-05-01T20:59:01Z",
      "immediate_rehash_matches": true,
      "segment_byte_end_exclusive": 436573736,
      "segment_byte_length": 64670040,
      "segment_byte_start": 371903696,
      "segment_descriptor_sha256": "9ff0a7fd2704599a18a44247fa5294b5db0659750dbf277605b11a7dd23fdc09",
      "segment_first_record_utc": "2026-05-01T20:59:06Z",
      "segment_last_record_utc": "2026-05-11T10:12:19Z",
      "segment_record_count": 1616751,
      "segment_record_end_index_inclusive": 10914341,
      "segment_record_start_index": 9297591,
      "segment_records_sha256": "fd7ea4c9eacae010887a6ea060018a7cdcabb636395537475f9daa44c332a0c0",
      "snapshot_file_written": false,
      "snapshot_policy": "NOT_USED_BOUNDED_SEGMENT_HASH_IS_COMMITTED",
      "source": "MGCM26-COMEX.scid",
      "source_path": "C:\\SierraChart\\Data\\MGCM26-COMEX.scid",
      "symbol": "XAUUSD_MGC"
    },
    {
      "append_safety_rule": "hash only frozen record byte range; later EOF growth is outside segment_byte_end_exclusive",
      "eligible_segment_start_utc_hard_floor": "2026-05-01T20:59:01Z",
      "immediate_rehash_matches": true,
      "segment_byte_end_exclusive": 238621336,
      "segment_byte_length": 26332440,
      "segment_byte_start": 212288896,
      "segment_descriptor_sha256": "fe03f46a32cb71075878c124dfd40f6725a71de93b6952b4245658ad23a88200",
      "segment_first_record_utc": "2026-05-01T20:59:01Z",
      "segment_last_record_utc": "2026-05-11T10:11:57Z",
      "segment_record_count": 658311,
      "segment_record_end_index_inclusive": 5965531,
      "segment_record_start_index": 5307221,
      "segment_records_sha256": "793eb8ee21e23dcefba7a4b2a7fce48444c10994c38afd82fbc858ae5bd67da7",
      "snapshot_file_written": false,
      "snapshot_policy": "NOT_USED_BOUNDED_SEGMENT_HASH_IS_COMMITTED",
      "source": "MYMM26-CBOT.scid",
      "source_path": "C:\\SierraChart\\Data\\MYMM26-CBOT.scid",
      "symbol": "US30_MYM"
    },
    {
      "append_safety_rule": "hash only frozen record byte range; later EOF growth is outside segment_byte_end_exclusive",
      "eligible_segment_start_utc_hard_floor": "2026-05-01T20:59:01Z",
      "immediate_rehash_matches": true,
      "segment_byte_end_exclusive": 782134776,
      "segment_byte_length": 107062200,
      "segment_byte_start": 675072576,
      "segment_descriptor_sha256": "199c2b26c5a639ffcced037026342b956cb0ce99c090471a85b12c12b7f1aa8e",
      "segment_first_record_utc": "2026-05-01T20:59:01Z",
      "segment_la
... truncated in markdown; see matching JSON artifact ...
```
