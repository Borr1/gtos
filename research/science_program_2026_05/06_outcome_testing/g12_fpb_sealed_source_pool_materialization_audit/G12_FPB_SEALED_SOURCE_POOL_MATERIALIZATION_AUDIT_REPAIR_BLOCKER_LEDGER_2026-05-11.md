# Repair Blocker Ledger

- Route: `G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT`
- Artifact family: `repair_blocker_ledger`
- Evidence class: `G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "artifact_family": "repair_blocker_ledger",
  "audit_decision": "REPAIR_BLOCKED_SOURCE_POOL_PACKET",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY",
  "generated_at_utc": "2026-05-11T09:43:01Z",
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
  "remaining_non_repair_gates_before_validation": [
    "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT",
    "separate validation-execution prompt after source-control contract acceptance"
  ],
  "repair_blocker_count": 9,
  "repair_blockers": [
    {
      "exact_next_artifact": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR: copy or segment-freeze each accepted SCID source at an audit timestamp, hash immutable snapshot or bounded eligible segment, update coverage/end metadata, then rerun source-expansion verifier and this G12 audit",
      "failed_checks": [
        "sha256_matches_ledger",
        "size_matches_ledger",
        "coverage_end_matches_ledger",
        "record_count_matches_ledger"
      ],
      "failure_anatomy": "native Sierra SCID file is append-mutable after packet materialization, so full-file source hash/size/end coverage drifted",
      "ledger_coverage_end_utc": "2026-05-11T08:45:00Z",
      "ledger_sha256": "2ec058872a29a643d2e46b30c93fc11a774cbebede59f748705339aeb0494540",
      "ledger_size_bytes": 61506536,
      "recomputed_coverage_end_utc": "2026-05-11T09:32:02Z",
      "recomputed_sha256": "29923e17d0d40310ec943429864f7178b163ff3c86970524d11c344494904e2e",
      "recomputed_size_bytes": 61540776,
      "source": "6BM26-CME.scid",
      "symbol": "GBPUSD_6B"
    },
    {
      "exact_next_artifact": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR: copy or segment-freeze each accepted SCID source at an audit timestamp, hash immutable snapshot or bounded eligible segment, update coverage/end metadata, then rerun source-expansion verifier and this G12 audit",
      "failed_checks": [
        "sha256_matches_ledger",
        "size_matches_ledger",
        "coverage_end_matches_ledger",
        "record_count_matches_ledger"
      ],
      "failure_anatomy": "native Sierra SCID file is append-mutable after packet materialization, so full-file source hash/size/end coverage drifted",
      "ledger_coverage_end_utc": "2026-05-11T08:45:05Z",
      "ledger_sha256": "da26d04e97e857fde5bd96837c67165f22d183d7106d689343443c075279407d",
      "ledger_size_bytes": 155618536,
      "recomputed_coverage_end_utc": "2026-05-11T09:32:23Z",
      "recomputed_sha256": "ea8209c10b4983121080b07fc1d0dbdb320711a8b2983d898d6d1e39b269ab57",
      "recomputed_size_bytes": 155675176,
      "source": "6EM26-CME.scid",
      "symbol": "EURUSD"
    },
    {
      "exact_next_artifact": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR: copy or segment-freeze each accepted SCID source at an audit timestamp, hash immutable snapshot or bounded eligible segment, update coverage/end metadata, then rerun source-expansion verifier and this G12 audit",
      "failed_checks": [
        "sha256_matches_ledger",
        "size_matches_ledger",
        "coverage_end_matches_ledger",
        "record_count_matches_ledger"
      ],
      "failure_anatomy": "native Sierra SCID file is append-mutable after packet materialization, so full-file source hash/size/end coverage drifted",
      "ledger_coverage_end_utc": "2026-05-11T08:44:54Z",
      "ledger_sha256": "1e882236bb9746971af889b3a0b8b8fa157f0c3b92c35b92d3af2f6e1d0855bd",
      "ledger_size_bytes": 119304096,
      "recomputed_coverage_end_utc": "2026-05-11T09:32:00Z",
      "recomputed_sha256": "cb5aa19f74f4db3cb4d938fe59690e115d98df4b688faaff2848b132edc0c605",
      "recomputed_size_bytes": 119334496,
      "source": "6JM26-CME.scid",
      "symbol": "USDJPY_6J"
    },
    {
      "exact_next_artifact": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR: copy or segment-freeze each accepted SCID source at an audit timestamp, hash immutable snapshot or bounded eligible segment, update coverage/end metadata, then rerun source-expansion verifier and this G12 audit",
      "failed_checks": [
        "sha256_matches_ledger",
        "size_matches_ledger",
        "coverage_end_matches_ledger",
        "record_count_matches_ledger"
      ],
      "failure_anatomy": "native Sierra SCID file is append-mutable after packet materialization, so full-file source hash/size/end coverage drifted",
      "ledger_coverage_end_utc": "2026-05-11T08:45:05Z",
      "ledger_sha256": "2ff5025ed64bfb0ce514d0190bdbf6a66d3262b5a23066465b4ec2eb0418c6b8",
      "ledger_size_bytes": 148296176,
      "recomputed_coverage_end_utc": "2026-05-11T09:32:45Z",
      "recomputed_sha256": "f48257a0b1e38689b18ccecf5d83acf73a79f30dd794f4621849d7182bc2887f",
      "recomputed_size_bytes": 148421856,
      "source": "GCM26-COMEX.scid",
      "symbol": "XAUUSD_GC"
    },
    {
      "exact_next_artifact": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR: copy or segment-freeze each accepted SCID source at an audit timestamp, hash immutable snapshot or bounded eligible segment, update coverage/end metadata, then rerun source-expansion verifier and this G12 audit",
      "failed_checks": [
        "sha256_matches_ledger",
        "size_matches_ledger",
        "coverage_end_matches_ledger",
        "record_count_matches_ledger"
      ],
      "failure_anatomy": "native Sierra SCID file is append-mutable after packet materialization, so full-file source hash/size/end coverage drifted",
      "ledger_coverage_end_utc": "2026-05-11T08:45:10Z",
      "ledger_sha256": "87545458248c3739f7108df116963f631b563210e4e0bfaa52d719df118a7fb9",
      "ledger_size_bytes": 436061776,
      "recomputed_coverage_end_utc": "2026-05-11T09:32:46Z",
      "recomputed_sha256": "f789b5d969cf2c89c2fef1f2f4e3cc0babfb828d7961a14645ebc017564abb8a",
      "recomputed_size_bytes": 436326416,
      "source": "MGCM26-COMEX.scid",
      "symbol": "XAUUSD_MGC"
    },
    {
      "exact_next_artifact": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR: copy or segment-freeze each accepted SCID source at an audit timestamp, hash immutable snapshot or bounded eligible segment, update coverage/end metadata, then rerun source-expansion verifier and this G12 audit",
      "failed_checks": [
        "sha256_matches_ledger",
        "size_matches_ledger",
        "coverage_end_matches_ledger",
        "record_count_matches_ledger"
      ],
      "failure_anatomy": "native Sierra SCID file is append-mutable after packet materialization, so full-file source hash/size/end coverage drifted",
      "ledger_coverage_end_utc": "2026-05-11T08:45:05Z",
      "ledger_sha256": "5a6163f9f4af5fd8186dad70daf3a761eb1fc44c96f60d21e1c495adc71cb4a9",
      "ledger_size_bytes": 238574896,
      "recomputed_coverage_end_utc": "2026-05-11T09:32:44Z",
      "recomputed_sha256": "2d422898cbc3d065003786a3985c01b50c3a35f9d7462b8e9f8cbf4da0ab5595",
      "recomputed_size_bytes": 238597336,
      "source": "MYMM26-CBOT.scid",
      "symbol": "US30_MYM"
    },
    {
      "exact_next_artifact": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR: copy or segment-freeze each accepted SCID source at an audit timestamp, hash immutable snapshot or bounded eligible segment, update coverage/end metadata, then rerun source-expansion verifier and this G12 audit",
      "failed_checks": [
        "sha256_matches_ledger",
        "size_matches_ledger",
        "coverage_end_matches_ledger",
        "record_count_matches_ledger"
      ],
      "failure_anatomy": "native Sierra SCID file is append-mutable after packet materialization, so full-file source hash/size/end coverage drifted",
      "ledger_coverage_end_utc": "2026-05-11T08:45:16Z",
      "ledger_sha256": "360565c76068cee7b36ea3cc83c6128ab7e821b4d2d5c8951a91be2a497e1054",
      "ledger_size_bytes": 781759096,
      "recomputed_coverage_end_utc": "2026-05-11T09:32:45Z",
      "recomputed_sha256": "da854da1515b5695c5f8285593a44570254c3a8f6792825d33938343078fc2e3",
      "recomputed_size_bytes": 781933936,
      "source": "NQM26-CME.scid",
      "symbol": "NAS100_NQ"
    },
    {
      "exact_next_artifact": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR: copy or segment-freeze each accepted SCID source at an audit timestamp, hash immutable snapshot or bounded eligible segment, update coverage/end metadata, then rerun source-expansion verifier and this G12 audit",
      "failed_checks": [
        "sha256_matches_ledger",
        "size_matches_ledger",
        "coverage_end_matches_ledger",
        "record_count_matches_ledger"
      ],
      "failure_anatomy": "native Sierra SCID file is append-mutable after packet materialization, so full-file source hash/size/end coverage drifted",
      "ledger_coverage_end_utc": "2026-05-11T08:41:47Z",
      "ledger_sha256": "87bde2de570e088da9accd85a567f9384d02f04f2d7cc6cc889adf1650394e38",
      "ledger_size_bytes": 609016,
      "recomputed_coverage_end_utc": "2026-05-11T09:26:42Z",
      "recomputed_sha256": "a15bcdbf2fbd3fe82d225d5e370117384a61519f84deddb3e52d005fa627d3db",
      "recomputed_size_bytes": 609376,
      "source": "SIM26-COMEX.scid",
      "symbol": "XAGUSD_SI"
    },
    {
      "exact_next_artifact": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR: copy or segment-freeze each accepted SCID source at an audit timestamp, hash immutable snapshot or bounded eligible segment, update coverage/end metadata, then rerun source-expansion verifier and this G12 audit",
      "failed_checks": [
        "sha256_matches_ledger",
        "size_matches_ledger",
        "coverage_end_matches_ledger",
        "record_count_matches_ledger"
      ],
      "failure_anatomy": "native Sierra SCID file is append-mutable after packet materialization, so full-file source hash/size/end coverage drifted",
      "ledger_coverage_end_utc": "2026-05-11T08:45:19Z",
      "ledger_sha256": "9ef61d85eeb7bbfe65a1f74eab581d1b5f3b6e7857589882f26012ced4572bbe",
      "ledger_size_bytes": 54378736,
      "recomputed_coverage_end_utc": "2026-05-11T09:32:44Z",
      "recomputed_sha256": "057d7895356da5fd7c3f9d4ef34fc5737e478c55e5e06e075867d1d880af3929",
      "recomputed_size_bytes": 54396896,
      "source": "YMM26-CBOT.scid",
      "symbol": "US30_YM"
    }
  ],
  "repair_blockers_exact_and_actionable": true,
  "route_id": "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT",
  "schema_version": "g12_fpb_sealed_source_pool_materialization_audit_v1",
  "terminal_repair_status": "REPAIR_BLOCKED_WITH_EXACT_NEXT_ARTIFACT",
  "validation_safe": false
}
```
