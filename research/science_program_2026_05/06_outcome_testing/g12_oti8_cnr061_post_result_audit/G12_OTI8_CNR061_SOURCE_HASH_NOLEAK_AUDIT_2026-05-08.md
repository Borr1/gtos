# G12 OTI8 CNR061 Source Hash Noleak Audit - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

- `hash_recompute_status`: `PASS`
- `source_policy_verdict`: `PASS_SOURCE_HASHED_AND_NO_FORBIDDEN_LABEL_LEAKAGE`

```json
{
  "accepted_sidecar_hashes": [
    "2d82227ec0dfd01b140471932701e4885dd065fca5c618d5dc2bf0e9c9da76ab",
    "41da6796ddb651413f558333ae52db302fc76a2863f00c204bee6ef37d10a23e",
    "4e76395873c48a3b9f20114c20d0247c92ef80846b170ee9b2f2d52919fa8d04",
    "5a7146782dc6564ac7a04ba163bd3d262ab731c2e1c3b6706ea14aeed979c7bb",
    "5ee22ed74a3eb5c16b1f7857d29346b2713ddbdb8b9a61de9f57c8414889959c",
    "63d08012951489781b7f892fe2d22a968e88101ded2429354aac16e68d3d93c8",
    "6b12bdca36eedc8c689617982be0f5fce05e5be3d16f84794c9ea30d87e36016",
    "95480e429f7beb460e31f4c65c0351eef65e46db4dca6557e4bb2a1f7afc998a"
  ],
  "accepted_source_hashes": [
    "340b2a33e6bb100cc893a48cbdac13c69346ec2aabe82dbf657a647453eb7202",
    "3b28e2322f1d5acdf4486212be47e4a3773d3fdcf66bfb9771ea720bedb337a2",
    "7c3093be6f686cdd2467cc6b46e5f19fc7cea7a82e71b5fdefab0d747e2bf197",
    "91668476f9891c7dcddf653c9f8790580f4c63d0a340c35a34e0bdc178b97058",
    "b0fc02e32f7aa38375194255963fc58275b09dfdaa152573e23d8388a0b5a3ac",
    "ee3cc4552784d174f54e8da4f959994b9c263dec96984ee039df218d3e0c9e88",
    "fae5fe3b8657c5adca8244a7a0abf763be6e3897e0475114a046528404b97568",
    "fdb3c2bf53decfcde7ccbfe37b0bd45514fd9de56b7e48bbc353d22f72107d7f"
  ],
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "G12_OTI8_CNR061_SOURCE_HASH_NOLEAK_AUDIT",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-08",
  "forbidden_label_and_flag_scan": {
    "forbidden_label_key_hits": [],
    "forbidden_true_flag_hits": [],
    "missing_or_wrong_promotion_verdict": [],
    "status": "PASS"
  },
  "generated_at_utc": "2026-05-08T05:43:40Z",
  "hash_recompute_status": "PASS",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_account_calls": 0,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "oti8_reported_all_required_sources_present": true,
  "oti8_reported_all_source_hash_recomputes_match": true,
  "oti8_reported_source_hash_status": "PASS",
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "prompt_named_missing_or_stale_artifacts": [
    {
      "exists": false,
      "prompt_named_path": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_ROW_MATRIX_2026-05-08.jsonl",
      "reason": "The controlling prompt's 2026-05-08 ROW_MATRIX filename is absent; the committed upstream source-field packet row file named by sidecar source_evidence is the 2026-05-07 JSONL.",
      "replacement_used": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_PACKET_ROWS_2026-05-07.jsonl"
    }
  ],
  "quote_and_ordered_path_source_hash_recompute": [
    {
      "actual_sha256": "fe80b36da79fe2491eb488c77d20f4e734435752715228e1199f7f76055a7868",
      "exists": true,
      "expected_ordered_path_sha256": "fe80b36da79fe2491eb488c77d20f4e734435752715228e1199f7f76055a7868",
      "expected_quote_sha256_values": [
        "fe80b36da79fe2491eb488c77d20f4e734435752715228e1199f7f76055a7868"
      ],
      "matches_all_declared_hashes": true,
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-04.parquet",
      "row_count_referencing_path": 2
    },
    {
      "actual_sha256": "ad451c922db79a8643e32b7b9c5f55e6d5cd417834ef0fbf5b20b5799d004237",
      "exists": true,
      "expected_ordered_path_sha256": "ad451c922db79a8643e32b7b9c5f55e6d5cd417834ef0fbf5b20b5799d004237",
      "expected_quote_sha256_values": [
        "ad451c922db79a8643e32b7b9c5f55e6d5cd417834ef0fbf5b20b5799d004237"
      ],
      "matches_all_declared_hashes": true,
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-05.parquet",
      "row_count_referencing_path": 6
    }
  ],
  "schema_version": "g12_oti8_cnr061_post_result_audit_v1",
  "sidecar_row_hash_recompute": [
    {
      "matches": true,
      "observed_sidecar_row_sha256": "95480e429f7beb460e31f4c65c0351eef65e46db4dca6557e4bb2a1f7afc998a",
      "recomputed_sidecar_row_sha256": "95480e429f7beb460e31f4c65c0351eef65e46db4dca6557e4bb2a1f7afc998a",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-04T07:15:00+00:00",
      "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
    },
    {
      "matches": true,
      "observed_sidecar_row_sha256": "6b12bdca36eedc8c689617982be0f5fce05e5be3d16f84794c9ea30d87e36016",
      "recomputed_sidecar_row_sha256": "6b12bdca36eedc8c689617982be0f5fce05e5be3d16f84794c9ea30d87e36016",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-04T07:15:00+00:00",
      "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
    },
    {
      "matches": true,
      "observed_sidecar_row_sha256": "4e76395873c48a3b9f20114c20d0247c92ef80846b170ee9b2f2d52919fa8d04",
      "recomputed_sidecar_row_sha256": "4e76395873c48a3b9f20114c20d0247c92ef80846b170ee9b2f2d52919fa8d04",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:30:00+00:00",
      "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
    },
    {
      "matches": true,
      "observed_sidecar_row_sha256": "41da6796ddb651413f558333ae52db302fc76a2863f00c204bee6ef37d10a23e",
      "recomputed_sidecar_row_sha256": "41da6796ddb651413f558333ae52db302fc76a2863f00c204bee6ef37d10a23e",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:30:00+00:00",
      "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
    },
    {
      "matches": true,
      "observed_sidecar_row_sha256": "5a7146782dc6564ac7a04ba163bd3d262ab731c2e1c3b6706ea14aeed979c7bb",
      "recomputed_sidecar_row_sha256": "5a7146782dc6564ac7a04ba163bd3d262ab731c2e1c3b6706ea14aeed979c7bb",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:45:00+00:00",
      "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
    },
    {
      "matches": true,
      "observed_sidecar_row_sha256": "2d82227ec0dfd01b140471932701e4885dd065fca5c618d5dc2bf0e9c9da76ab",
      "recomputed_sidecar_row_sha256": "2d82227ec0dfd01b140471932701e4885dd065fca5c618d5dc2bf0e9c9da76ab",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:45:00+00:00",
      "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
    },
    {
      "matches": true,
      "observed_sidecar_row_sha256": "63d08012951489781b7f892fe2d22a968e88101ded2429354aac16e68d3d93c8",
      "recomputed_sidecar_row_sha256": "63d08012951489781b7f892fe2d22a968e88101ded2429354aac16e68d3d93c8",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T17:00:00+00:00",
      "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
    },
    {
      "matches": true,
      "observed_sidecar_row_sha256": "5ee22ed74a3eb5c16b1f7857d29346b2713ddbdb8b9a61de9f57c8414889959c",
      "recomputed_sidecar_row_sha256": "5ee22ed74a3eb5c16b1f7857d29346b2713ddbdb8b9a61de9f57c8414889959c",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T17:00:00+00:00",
      "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
    }
  ],
  "source_hash_failures": [],
  "source_policy_verdict": "PASS_SOURCE_HASHED_AND_NO_FORBIDDEN_LABEL_LEAKAGE",
  "source_row_hash_recompute": [
    {
      "matches": true,
      "observed_row_sha256": "340b2a33e6bb100cc893a48cbdac13c69346ec2aabe82dbf657a647453eb7202",
      "recomputed_row_sha256": "340b2a33e6bb100cc893a48cbdac13c69346ec2aabe82dbf657a647453eb7202",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-04T07:15:00+00:00"
    },
    {
      "matches": true,
      "observed_row_sha256": "3b28e2322f1d5acdf4486212be47e4a3773d3fdcf66bfb9771ea720bedb337a2",
      "recomputed_row_sha256": "3b28e2322f1d5acdf4486212be47e4a3773d3fdcf66bfb9771ea720bedb337a2",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:30:00+00:00"
    },
    {
      "matches": true,
      "observed_row_sha256": "7c3093be6f686cdd2467cc6b46e5f19fc7cea7a82e71b5fdefab0d747e2bf197",
      "recomputed_row_sha256": "7c3093be6f686cdd2467cc6b46e5f19fc7cea7a82e71b5fdefab0d747e2bf197",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-04T07:15:00+00:00"
    },
    {
      "matches": true,
      "observed_row_sha256": "91668476f9891c7dcddf653c9f8790580f4c63d0a340c35a34e0bdc178b97058",
      "recomputed_row_sha256": "91668476f9891c7dcddf653c9f8790580f4c63d0a340c35a34e0bdc178b97058",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:45:00+00:00"
    },
    {
      "matches": true,
      "observed_row_sha256": "b0fc02e32f7aa38375194255963fc58275b09dfdaa152573e23d8388a0b5a3ac",
      "recomputed_row_sha256": "b0fc02e32f7aa38375194255963fc58275b09dfdaa152573e23d8388a0b5a3ac",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:30:00+00:00"
    },
    {
      "matches": true,
      "observed_row_sha256": "ee3cc4552784d174f54e8da4f959994b9c263dec96984ee039df218d3e0c9e88",
      "recomputed_row_sha256": "ee3cc4552784d174f54e8da4f959994b9c263dec96984ee039df218d3e0c9e88",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T17:00:00+00:00"
    },
    {
      "matches": true,
      "observed_row_sha256": "fae5fe3b8657c5adca8244a7a0abf763be6e3897e0475114a046528404b97568",
      "recomputed_row_sha256": "fae5fe3b8657c5adca8244a7a0abf763be6e3897e0475114a046528404b97568",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:45:00+00:00"
    },
    {
      "matches": true,
      "observed_row_sha256": "fdb3c2bf53decfcde7ccbfe37b0bd45514fd9de56b7e48bbc353d22f72107d7f",
      "recomputed_row_sha256": "fdb3c2bf53decfcde7ccbfe37b0bd45514fd9de56b7e48bbc353d22f72107d7f",
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T17:00:00+00:00"
    }
  ],
  "validation_safe": false
}
```
