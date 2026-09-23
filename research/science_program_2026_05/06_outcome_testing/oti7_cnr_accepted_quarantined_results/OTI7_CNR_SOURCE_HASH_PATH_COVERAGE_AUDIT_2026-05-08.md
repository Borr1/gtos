# OTI7 CNR Source Hash Path Coverage Audit - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `False`  
**Outcome review opened:** `False`  
**Live effect:** `False`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "OTI7_CNR_ACCEPTED_QUARANTINED_RESULTS",
  "artifact_type": "source_hash_path_coverage_audit",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "databento_calls": 0,
  "g12_source_hash_audit_status": {
    "all_required_current_worktree_sources_present": true,
    "all_strict_hashes_match_current_worktree_sources": true,
    "quote_rows_checked": 2368,
    "strict_hash_mismatch_count": 0
  },
  "generated_at_utc": "2026-05-08T01:56:25Z",
  "listed_source_hash_mismatch_count": 0,
  "listed_source_hash_mismatches": [],
  "live_effect": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "path_expansion_policy": "Use each accepted row's listed source-hashed parquet for the executable quote, then add read-only same-symbol/date tick parquet files from approved local heavy-data roots only when packet path_end extends beyond the listed quote file date. All additional files are hashed and reported.",
  "path_missing_entries": [],
  "path_missing_entry_count": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "quote_recompute_mismatch_count": 0,
  "quote_recompute_mismatches": [],
  "result_status": "RESULT_QUARANTINED_DISCOVERY_ONLY",
  "searched_roots": {
    "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks": {
      "exists": true,
      "purpose": "absolute local heavy tick root"
    },
    "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY": {
      "exists": true,
      "purpose": "candidate local tick root for source-hashed path expansion"
    },
    "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100": {
      "exists": true,
      "purpose": "candidate local tick root for source-hashed path expansion"
    },
    "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NDX100": {
      "exists": false,
      "purpose": "candidate local tick root for source-hashed path expansion"
    },
    "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD": {
      "exists": true,
      "purpose": "candidate local tick root for source-hashed path expansion"
    },
    "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD": {
      "exists": true,
      "purpose": "candidate local tick root for source-hashed path expansion"
    },
    "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery": {
      "exists": true,
      "purpose": "OTR061 read-only XAU tick recovery source root"
    },
    "C:\\tmp\\gtos_otb\\OTI7CNRRESULT": {
      "exists": true,
      "purpose": "current worktree"
    },
    "C:\\tmp\\gtos_otb\\OTI7CNRRESULT\\research\\science_program_2026_05\\06_outcome_testing\\g12_cnr_source_field_packet_audit": {
      "exists": true,
      "purpose": "G12 CNR accepted/blocker audit artifacts"
    },
    "C:\\tmp\\gtos_otb\\OTI7CNRRESULT\\research\\science_program_2026_05\\06_outcome_testing\\oti7_cnr_accepted_quarantined_results": {
      "exists": true,
      "purpose": "OTI7 scoped output directory"
    }
  },
  "source_file_count": 16,
  "source_files": [
    {
      "actual_sha256": "4e2d512fb980b2437e56e939b28cb6dae7a9fd4cf863536cfc59a4126da77fe1",
      "exists": true,
      "expected_sha256_values": [
        "4e2d512fb980b2437e56e939b28cb6dae7a9fd4cf863536cfc59a4126da77fe1"
      ],
      "parquet_metadata": {
        "first_utc": "2026-05-04T00:00:00.127000Z",
        "last_utc": "2026-05-04T23:59:59.858000Z",
        "rows": 318567
      },
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet",
      "rows_referencing": 16,
      "size_bytes": 4856218,
      "strict_hash_match": true,
      "used_as": [
        "listed_ready_source",
        "path_expansion_source"
      ]
    },
    {
      "actual_sha256": "fa2b64a91ed38e54c7a1b57683e5a7991a86db8a9c9b37a72b312e7fc39d5c02",
      "exists": true,
      "expected_sha256_values": [],
      "parquet_metadata": {
        "first_utc": "2026-05-05T00:00:00.364000Z",
        "last_utc": "2026-05-05T23:59:59.257000Z",
        "rows": 250931
      },
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet",
      "rows_referencing": 0,
      "size_bytes": 3892480,
      "strict_hash_match": null,
      "used_as": [
        "path_expansion_source"
      ]
    },
    {
      "actual_sha256": "f94cd1ba695b36c099fe50cfb926937d0af8057a5255b73fd00587b58f75fe3e",
      "exists": true,
      "expected_sha256_values": [
        "f94cd1ba695b36c099fe50cfb926937d0af8057a5255b73fd00587b58f75fe3e"
      ],
      "parquet_metadata": {
        "first_utc": "2026-05-06T00:00:00.269000Z",
        "last_utc": "2026-05-06T23:59:59.483000Z",
        "rows": 365250
      },
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet",
      "rows_referencing": 16,
      "size_bytes": 5377035,
      "strict_hash_match": true,
      "used_as": [
        "listed_ready_source",
        "path_expansion_source"
      ]
    },
    {
      "actual_sha256": "7b2f89ecbbbc59124fc56c7b9e504d7b41e299f7bd950fc54821e8f18a7fa478",
      "exists": true,
      "expected_sha256_values": [
        "7b2f89ecbbbc59124fc56c7b9e504d7b41e299f7bd950fc54821e8f18a7fa478"
      ],
      "parquet_metadata": {
        "first_utc": "2026-05-04T00:00:00.293000Z",
        "last_utc": "2026-05-04T23:59:57.055000Z",
        "rows": 1084963
      },
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-04.parquet",
      "rows_referencing": 6,
      "size_bytes": 15119257,
      "strict_hash_match": true,
      "used_as": [
        "listed_ready_source",
        "path_expansion_source"
      ]
    },
    {
      "actual_sha256": "13357b7bc6b4d02690ab7055b611b431c6e2ce2a77c36df791f347cf7fcaed35",
      "exists": true,
      "expected_sha256_values": [],
      "parquet_metadata": {
        "first_utc": "2026-05-05T00:00:00.153000Z",
        "last_utc": "2026-05-05T23:59:59.459000Z",
        "rows": 804482
      },
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-05.parquet",
      "rows_referencing": 0,
      "size_bytes": 11479489,
      "strict_hash_match": null,
      "used_as": [
        "path_expansion_source"
      ]
    },
    {
      "actual_sha256": "fe80b36da79fe2491eb488c77d20f4e734435752715228e1199f7f76055a7868",
      "exists": true,
      "expected_sha256_values": [
        "fe80b36da79fe2491eb488c77d20f4e734435752715228e1199f7f76055a7868"
      ],
      "parquet_metadata": {
        "first_utc": "2026-05-04T00:00:00.359000Z",
        "last_utc": "2026-05-04T23:59:59.708000Z",
        "rows": 217453
      },
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-04.parquet",
      "rows_referencing": 8,
      "size_bytes": 3589112,
      "strict_hash_match": true,
      "used_as": [
        "listed_ready_source",
        "path_expansion_source"
      ]
    },
    {
      "actual_sha256": "ad451c922db79a8643e32b7b9c5f55e6d5cd417834ef0fbf5b20b5799d004237",
      "exists": true,
      "expected_sha256_values": [
        "ad451c922db79a8643e32b7b9c5f55e6d5cd417834ef0fbf5b20b5799d004237"
      ],
      "parquet_metadata": {
        "first_utc": "2026-05-05T00:00:00.107000Z",
        "last_utc": "2026-05-05T23:59:59.710000Z",
        "rows": 168865
      },
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-05.parquet",
      "rows_referencing": 24,
      "size_bytes": 2892270,
      "strict_hash_match": true,
      "used_as": [
        "listed_ready_source",
        "path_expansion_source"
      ]
    },
    {
      "actual_sha256": "c824a97a603940424ad43dc1a1263ae998053b5df262d3c3ab53dd83ccdab36e",
      "exists": true,
      "expected_sha256_values": [
        "c824a97a603940424ad43dc1a1263ae998053b5df262d3c3ab53dd83ccdab36e"
      ],
      "parquet_metadata": {
        "first_utc": "2026-05-06T00:00:00.110000Z",
        "last_utc": "2026-05-06T23:59:56.883000Z",
        "rows": 235332
      },
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-06.parquet",
      "rows_referencing": 18,
      "size_bytes": 3842206,
      "strict_hash_match": true,
      "used_as": [
        "listed_ready_source",
        "path_expansion_source"
      ]
    },
    {
      "actual_sha256": "9a361078f8448d8d69aacbf3905d38d291282ce223d269fe033b0e6eb9814a0f",
      "exists": true,
      "expected_sha256_values": [
        "9a361078f8448d8d69aacbf3905d38d291282ce223d269fe033b0e6eb9814a0f"
      ],
      "parquet_metadata": {
        "first_utc": "2026-05-05T00:00:00.063000Z",
        "last_utc": "2026-05-05T23:59:59.998000Z",
        "rows": 460423
      },
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-05.parquet",
      "rows_referencing": 8,
      "size_bytes": 6788510,
      "strict_hash_match": true,
      "used_as": [
        "listed_ready_source",
        "path_expansion_source"
      ]
    },
    {
      "actual_sha256": "fdec881196886808c90aa25d6a91d99c5f1105274ecbd435e442f63bcac59439",
      "exists": true,
      "expected_sha256_values": [],
      "parquet_metadata": {
        "first_utc": "2026-05-06T17:16:17.131000Z",
        "last_utc": "2026-05-06T23:59:59.392000Z",
        "rows": 108541
      },
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-06.parquet",
      "rows_referencing": 0,
      "size_bytes": 1883513,
      "strict_hash_match": null,
      "used_as": [
        "path_expansion_source"
      ]
    },
    {
      "actual_sha256": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff",
      "exists": true,
      "expected_sha256_values": [
        "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"
      ],
      "parquet_metadata": {
        "first_utc": "2026-05-06T07:10:01.820000Z",
        "last_utc": "2026-05-06T11:15:59.763000Z",
        "rows": 89391
      },
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet",
      "rows_referencing": 6,
      "size_bytes": 1584013,
      "strict_hash_match": true,
      "used_as": [
        "listed_ready_source",
        "path_expansion_source"
      ]
    },
    {
      "actual_sha256": "b682ba1377af7ac11721be068f91cf78e546d7f88a0865332432cffd6704bd1c",
      "exists": true,
      "expected_sha256_values": [
        "b682ba1377af7ac11721be068f91cf78e546d7f88a0865332432cffd6704bd1c"
      ],
      "parquet_metadata": null,
      "path": "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-060__G6-EXP-001-OB-VS-GENERIC-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
      "rows_referencing": 26,
      "size_bytes": 1020194,
      "strict_hash_match": true,
      "used_as": [
        "listed_ready_source"
      ]
    },
    {
      "actual_sha256": "3deee0b19325723795b0e3e6fb99a507486b291044b62820857050a105e75f1a",
      "exists": true,
      "expected_sha256_values": [
        "3deee0b19325723795b0e3e6fb99a507486b291044b62820857050a105e75f1a"
      ],
      "parquet_metadata": null,
      "path": "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-061__G6-EXP-002-CONTINUATION-NO-RETRACE__g6_local_ohlc_input_packet_2026-05-07.json",
      "rows_referencing": 8,
      "size_bytes": 338492,
      "strict_hash_match": true,
      "used_as": [
        "listed_ready_source"
      ]
    },
    {
      "actual_sha256": "fc587c1ffb8452718bc3d00fd8f80bd443b043387b862dce1679944dea3af080",
      "exists": true,
      "expected_sha256_values": [
        "fc587c1ffb8452718bc3d00fd8f80bd443b043387b862dce1679944dea3af080"
      ],
      "parquet_metadata": null,
      "path": "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-062__G6-EXP-003-OPENING-DRIVE-CONTINUATION__g6_local_ohlc_input_packet_2026-05-07.json",
      "rows_referencing": 32,
      "size_bytes": 568343,
      "strict_hash_match": true,
      "used_as": [
        "listed_ready_source"
      ]
    },
    {
      "actual_sha256": "0064500e34b9880ddd8b1db1f84035c63cdf2433e80f05c9c27e5fbc92b3e828",
      "exists": true,
      "expected_sha256_values": [
        "0064500e34b9880ddd8b1db1f84035c63cdf2433e80f05c9c27e5fbc92b3e828"
      ],
      "parquet_metadata": null,
      "path": "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-063__G6-EXP-004-EXHAUSTION-CHANGEPOINT__g6_local_ohlc_input_packet_2026-05-07.json",
      "rows_referencing": 32,
      "size_bytes": 984983,
      "strict_hash_match": true,
      "used_as": [
        "listed_ready_source"
      ]
    },
    {
      "actual_sha256": "4a2fc13bd16855cea11df01c9781bca9dc79176356cb9966b7f5d315f6904714",
      "exists": true,
      "expected_sha256_values": [
        "4a2fc13bd16855cea11df01c9781bca9dc79176356cb9966b7f5d315f6904714"
      ],
      "parquet_metadata": null,
      "path": "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-066__G6-EXP-007-GOLD-ROUND-OB-CONFLUENCE__g6_local_ohlc_input_packet_2026-05-07.json",
      "rows_referencing": 4,
      "size_bytes": 60157,
      "strict_hash_match": true,
      "used_as": [
        "listed_ready_source"
      ]
    }
  ],
  "validation_safe": false
}
```
