# G12 CNR Source No-Leak Duplicate Audit - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "accepted_limits": [
    "Source contracts are valid as research contracts.",
    "No-leak and boundary flags are acceptable for control-pack scope.",
    "Duplicate controls prevent row-level six from becoming six independent validation samples."
  ],
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "G12_CNR_SOURCE_NOLEAK_DUPLICATE_AUDIT",
  "blocked_94_exclusion": {
    "blocked_audit_status": "PASS_EXACT_94_BLOCKED_ROWS_EXCLUDED",
    "blocked_overlap_with_accepted": [],
    "blocked_rows": 94,
    "note": "The 94 blocked rows are verified only as excluded; no blocked-row terminal labels or performance were computed by G12.",
    "packet_hashes_from_accepted_manifest": [
      "2d82227ec0dfd01b140471932701e4885dd065fca5c618d5dc2bf0e9c9da76ab",
      "41da6796ddb651413f558333ae52db302fc76a2863f00c204bee6ef37d10a23e",
      "4e76395873c48a3b9f20114c20d0247c92ef80846b170ee9b2f2d52919fa8d04",
      "5a7146782dc6564ac7a04ba163bd3d262ab731c2e1c3b6706ea14aeed979c7bb",
      "5ee22ed74a3eb5c16b1f7857d29346b2713ddbdb8b9a61de9f57c8414889959c",
      "63d08012951489781b7f892fe2d22a968e88101ded2429354aac16e68d3d93c8"
    ],
    "packet_rows_from_blocked_set": [],
    "status": "PASS"
  },
  "blocked_limits": [
    "validation_safe remains false.",
    "No broker/account/live/hidden label source was used or needed.",
    "The 94 blocked rows remain excluded from all score/lifecycle claims."
  ],
  "blocked_packet_outcome_source_read": false,
  "boundary_flag_scan": {
    "failures": [],
    "status": "PASS"
  },
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-08",
  "decision": "ACCEPT_AS_RESEARCH_CONTROL_NOLEAK_DUPLICATE_SAMPLE_BOUNDARY",
  "duplicate_denominator_review": {
    "control_pack_sample_floor": {
      "countable_rows": 2,
      "packet_row_count": 6,
      "reason": "n=6 row-level and one duplicate group is an input packet only; validation/promotion sample floor is not met.",
      "sample_floor_for_validation_met": false,
      "unique_duplicate_groups": 1
    },
    "countable_rows": 2,
    "decision": "PASS_REPEATED_ROWS_VISIBLE_NOT_FALSE_INDEPENDENT_EVIDENCE",
    "duplicate_denominator_key_counts": {
      "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": 3,
      "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": 3
    },
    "duplicate_group_counts": {
      "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222": 6
    },
    "row_count": 6,
    "unique_duplicate_groups": 1
  },
  "generated_at_utc": "2026-05-08T06:23:47Z",
  "lifecycle_forbidden_key_scan": {
    "forbidden_lifecycle_key_hits": [],
    "status": "PASS"
  },
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_account_calls": 0,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "sample_floor_review": {
    "reason": "The lifecycle packet has six row-level rows, two countable timing-target denominator rows, and one duplicate group; this is below any validation/promotion floor.",
    "sample_floor_for_validation_met": false
  },
  "schema_version": "g12_cnr_next_model_control_audit_v1",
  "source_contract_decision": "ACCEPT_AS_RESEARCH_CONTRACTS_KEEP_VALIDATION_SAFE_FALSE",
  "source_contract_summary": {
    "allowed_parsers": [
      "pyarrow parquet reader for ts_utc/bid/ask",
      "json/jsonl source-hash parser",
      "future preregistered source-specific parser"
    ],
    "allowed_source_roots": [
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\{SYMBOL}\\YYYY-MM-DD.parquet",
      "research/science_program_2026_05/06_outcome_testing/* source-hashed JSON/JSONL artifacts",
      "future source-hashed shadow logger files explicitly registered by G12/G0"
    ],
    "forbidden_sources": [
      "broker actual-R",
      "account history",
      "live trade results",
      "live order state",
      "hidden path labels",
      "94 G12-blocked CNR061 rows as scored evidence"
    ],
    "legal_source_state": {
      "E2_E3_E4": "preregistered but current rows blocked by missing source fields",
      "T1_T2_T3": "preregistered; T3 lifecycle packet built for six no-terminal rows without R scoring"
    },
    "source_artifact_inventory_files": 309
  },
  "validation_safe": false
}
```
