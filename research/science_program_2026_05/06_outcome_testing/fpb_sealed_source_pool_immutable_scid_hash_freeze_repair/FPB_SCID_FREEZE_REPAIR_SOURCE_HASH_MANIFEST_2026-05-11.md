# Source Hash Manifest

- Route: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR`
- Evidence class: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `False`
- outcome_review_opened: `False`
- live_effect: `False`

## Summary

```json
{
  "accepted_hashes_present": true,
  "hash_row_count": 9
}
```
## Payload

```json
{
  "accepted_hash_policy": "only segment record-byte hashes are accepted repaired source evidence",
  "all_accepted_hashes_present": true,
  "artifact_family": "source_hash_manifest",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY",
  "full_file_hash_policy": "full-file hashes are mutable reference metadata only",
  "generated_at_utc": "2026-05-11T10:22:32Z",
  "hash_rows": [
    {
      "accepted_source_evidence_hash_type": "SEGMENT_RECORD_BYTES_SHA256",
      "accepted_source_evidence_sha256": "91ae9eb8ca0493cd301ae7dd3be2c08d2f8529473ac049206187f3b805e2a263",
      "full_file_reference_is_not_validation_evidence": true,
      "g12_recomputed_full_file_sha256_stale_reference": "29923e17d0d40310ec943429864f7178b163ff3c86970524d11c344494904e2e",
      "header_sha256": "907f092cd22a0e25ae7f88e46ca90e268506cd89733023a358ebafa75e23211d",
      "mutable_full_file_hash_reference_only": "4e1886e4428d45d967e50121aa68af03f531632e6e0048edff87b9ed5cbab4ef",
      "mutable_full_file_hash_status": "MUTABLE_REFERENCE_ONLY_NOT_ACCEPTED_SOURCE_EVIDENCE",
      "parser_implementation": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/build_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_2026_05_11.py",
      "parser_implementation_sha256": "dd4ff50579294b871f1611edee375822a73072f49c9ff6a885033738624de2bc",
      "segment_descriptor_sha256": "78109494711d8ee2de98c7d0f411733c73f07af6bd2cd1a20006a3d1e26dab0a",
      "source": "6BM26-CME.scid",
      "source_packet_full_file_sha256_stale_reference": "2ec058872a29a643d2e46b30c93fc11a774cbebede59f748705339aeb0494540",
      "source_path": "C:\\SierraChart\\Data\\6BM26-CME.scid",
      "symbol": "GBPUSD_6B"
    },
    {
      "accepted_source_evidence_hash_type": "SEGMENT_RECORD_BYTES_SHA256",
      "accepted_source_evidence_sha256": "3e755a319b4f895c27203d63fd7ddb310b81066384f93f007943bddc94ca2053",
      "full_file_reference_is_not_validation_evidence": true,
      "g12_recomputed_full_file_sha256_stale_reference": "ea8209c10b4983121080b07fc1d0dbdb320711a8b2983d898d6d1e39b269ab57",
      "header_sha256": "907f092cd22a0e25ae7f88e46ca90e268506cd89733023a358ebafa75e23211d",
      "mutable_full_file_hash_reference_only": "a1376d5933d804f13b0922a366ead7b6160ae8e877c54e1bbbcf754a7adb95fe",
      "mutable_full_file_hash_status": "MUTABLE_REFERENCE_ONLY_NOT_ACCEPTED_SOURCE_EVIDENCE",
      "parser_implementation": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/build_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_2026_05_11.py",
      "parser_implementation_sha256": "dd4ff50579294b871f1611edee375822a73072f49c9ff6a885033738624de2bc",
      "segment_descriptor_sha256": "e7f997ce783fd0ea15e0d48a0fb74b756698a8ea2b4b243ea8f56d1c8f4a2783",
      "source": "6EM26-CME.scid",
      "source_packet_full_file_sha256_stale_reference": "da26d04e97e857fde5bd96837c67165f22d183d7106d689343443c075279407d",
      "source_path": "C:\\SierraChart\\Data\\6EM26-CME.scid",
      "symbol": "EURUSD"
    },
    {
      "accepted_source_evidence_hash_type": "SEGMENT_RECORD_BYTES_SHA256",
      "accepted_source_evidence_sha256": "c7bcc874ee594d78d51c1637c249372b59cf6e16194fb67fdea446a33b3832eb",
      "full_file_reference_is_not_validation_evidence": true,
      "g12_recomputed_full_file_sha256_stale_reference": "cb5aa19f74f4db3cb4d938fe59690e115d98df4b688faaff2848b132edc0c605",
      "header_sha256": "907f092cd22a0e25ae7f88e46ca90e268506cd89733023a358ebafa75e23211d",
      "mutable_full_file_hash_reference_only": "ee4cfcd578708d7af3b8329d6796494f909786ac64b6cd2d3392dc9da2744d13",
      "mutable_full_file_hash_status": "MUTABLE_REFERENCE_ONLY_NOT_ACCEPTED_SOURCE_EVIDENCE",
      "parser_implementation": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/build_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_2026_05_11.py",
      "parser_implementation_sha256": "dd4ff50579294b871f1611edee375822a73072f49c9ff6a885033738624de2bc",
      "segment_descriptor_sha256": "cb1e18f67e507ccc4b37a362e2ac730c975c9847ef714eaf325ae95ee0b6ac09",
      "source": "6JM26-CME.scid",
      "source_packet_full_file_sha256_stale_reference": "1e882236bb9746971af889b3a0b8b8fa157f0c3b92c35b92d3af2f6e1d0855bd",
      "source_path": "C:\\SierraChart\\Data\\6JM26-CME.scid",
      "symbol": "USDJPY_6J"
    },
    {
      "accepted_source_evidence_hash_type": "SEGMENT_RECORD_BYTES_SHA256",
      "accepted_source_evidence_sha256": "4be989f00e606c8e7478064a3d2610c0318ab87a7791824812dea1da2181f1af",
      "full_file_reference_is_not_validation_evidence": true,
      "g12_recomputed_full_file_sha256_stale_reference": "f48257a0b1e38689b18ccecf5d83acf73a79f30dd794f4621849d7182bc2887f",
      "header_sha256": "907f092cd22a0e25ae7f88e46ca90e268506cd89733023a358ebafa75e23211d",
      "mutable_full_file_hash_reference_only": "12807ecacdd65448d05ec44c0a0f6ded3fe56a213af51c9eef2ca9372fcee492",
      "mutable_full_file_hash_status": "MUTABLE_REFERENCE_ONLY_NOT_ACCEPTED_SOURCE_EVIDENCE",
      "parser_implementation": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/build_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_2026_05_11.py",
      "parser_implementation_sha256": "dd4ff50579294b871f1611edee375822a73072f49c9ff6a885033738624de2bc",
      "segment_descriptor_sha256": "c001576c6812abfd1cc29964cbd55129318e3a9a1cfa5217c6603e268995540d",
      "source": "GCM26-COMEX.scid",
      "source_packet_full_file_sha256_stale_reference": "2ff5025ed64bfb0ce514d0190bdbf6a66d3262b5a23066465b4ec2eb0418c6b8",
      "source_path": "C:\\SierraChart\\Data\\GCM26-COMEX.scid",
      "symbol": "XAUUSD_GC"
    },
    {
      "accepted_source_evidence_hash_type": "SEGMENT_RECORD_BYTES_SHA256",
      "accepted_source_evidence_sha256": "fd7ea4c9eacae010887a6ea060018a7cdcabb636395537475f9daa44c332a0c0",
      "full_file_reference_is_not_validation_evidence": true,
      "g12_recomputed_full_file_sha256_stale_reference": "f789b5d969cf2c89c2fef1f2f4e3cc0babfb828d7961a14645ebc017564abb8a",
      "header_sha256": "907f092cd22a0e25ae7f88e46ca90e268506cd89733023a358ebafa75e23211d",
      "mutable_full_file_hash_reference_only": "00240391a9c6c631ec2a491251adeadf124709bbef709cb6287209eaf95e896f",
      "mutable_full_file_hash_status": "MUTABLE_REFERENCE_ONLY_NOT_ACCEPTED_SOURCE_EVIDENCE",
      "parser_implementation": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/build_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_2026_05_11.py",
      "parser_implementation_sha256": "dd4ff50579294b871f1611edee375822a73072f49c9ff6a885033738624de2bc",
      "segment_descriptor_sha256": "9ff0a7fd2704599a18a44247fa5294b5db0659750dbf277605b11a7dd23fdc09",
      "source": "MGCM26-COMEX.scid",
      "source_packet_full_file_sha256_stale_reference": "87545458248c3739f7108df116963f631b563210e4e0bfaa52d719df118a7fb9",
      "source_path": "C:\\SierraChart\\Data\\MGCM26-COMEX.scid",
      "symbol": "XAUUSD_MGC"
    },
    {
      "accepted_source_evidence_hash_type": "SEGMENT_RECORD_BYTES_SHA256",
      "accepted_source_evidence_sha256": "793eb8ee21e23dcefba7a4b2a7fce48444c10994c38afd82fbc858ae5bd67da7",
      "full_file_reference_is_not_validation_evidence": true,
      "g12_recomputed_full_file_sha256_stale_reference": "2d422898cbc3d065003786a3985c01b50c3a35f9d7462b8e9f8cbf4da0ab5595",
      "header_sha256": "907f092cd22a0e25ae7f88e46ca90e268506cd89733023a358ebafa75e23211d",
      "mutable_full_file_hash_reference_only": "f16263a57c6c4891f96fc680e3ac12fc91115fb4e7f449ce0f782c597cce9252",
      "mutable_full_file_hash_status": "MUTABLE_REFERENCE_ONLY_NOT_ACCEPTED_SOURCE_EVIDENCE",
      "parser_implem
... truncated in markdown; see matching JSON artifact ...
```
