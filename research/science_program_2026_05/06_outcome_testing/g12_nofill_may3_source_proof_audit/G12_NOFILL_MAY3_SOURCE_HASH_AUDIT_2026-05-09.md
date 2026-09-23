# G12 NOFILL May 3 Source Hash Audit - 2026-05-09

Generated: `2026-05-09T03:38:51Z`

Strict source hashes recomputed: `36`.

Overall status: `PASS`.

## Tick Recompute

```json
{
  "NAS100": {
    "columns": [
      "ts_utc",
      "ts_msc",
      "bid",
      "ask",
      "last",
      "volume",
      "flags",
      "inferred_aggressor"
    ],
    "exists": true,
    "first_five_timestamps_utc": [
      "2026-05-03T22:00:00.391000Z",
      "2026-05-03T22:00:00.472000Z",
      "2026-05-03T22:00:00.574000Z",
      "2026-05-03T22:00:00.674000Z",
      "2026-05-03T22:00:00.772000Z"
    ],
    "first_timestamp_utc": "2026-05-03T22:00:00.391000Z",
    "last_timestamp_utc": "2026-05-03T23:59:59.872000Z",
    "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-03.parquet",
    "pre_2200_utc_rows": 0,
    "rows_total": 34500,
    "sha256": "41996c1de550993f124120b821d9495c0ffde06d5c0c04b36676a2112766e208",
    "window_end_utc": "2026-05-03T13:30:00Z",
    "window_rows": 0,
    "window_start_utc": "2026-05-03T13:00:00Z"
  },
  "XAUUSD": {
    "columns": [
      "ts_utc",
      "ts_msc",
      "bid",
      "ask",
      "last",
      "volume",
      "flags",
      "inferred_aggressor"
    ],
    "exists": true,
    "first_five_timestamps_utc": [
      "2026-05-03T22:00:00.780000Z",
      "2026-05-03T22:00:00.818000Z",
      "2026-05-03T22:00:00.878000Z",
      "2026-05-03T22:00:00.879000Z",
      "2026-05-03T22:00:00.888000Z"
    ],
    "first_timestamp_utc": "2026-05-03T22:00:00.780000Z",
    "last_timestamp_utc": "2026-05-03T23:59:59.226000Z",
    "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-03.parquet",
    "pre_2200_utc_rows": 0,
    "rows_total": 38191,
    "sha256": "0911ab624dc038992e3f3ac5d7c5e70bc9bcc498cf61c1388035f795b599a6f3",
    "window_end_utc": "2026-05-03T13:30:00Z",
    "window_rows": 0,
    "window_start_utc": "2026-05-03T13:00:00Z"
  }
}
```

## Official CME Recheck Capture

- File: `research\science_program_2026_05\06_outcome_testing\g12_nofill_may3_source_proof_audit\G12_NOFILL_MAY3_OFFICIAL_CME_SOURCE_RECHECK_2026-05-09.json`
- SHA256: `d3cffd9aef2ca29791fadf3b2bad98221bb876e8f5bb4ac95774bf93dc0682e6`

## Source Hash Records

| role | ok | path |
| --- | --- | --- |
| control_input | True | research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/NOFILL_MAY3_OPENING_RANGE_MARKET_CLOSURE_OR_SOURCE_PROOF_GOAL_PROMPT_2026-05-09.md |
| control_input | True | research/science_program_2026_05/06_outcome_testing/nofill_may3_opening_range_market_closure_or_source_proof/NOFILL_MAY3_OPENING_RANGE_STARTER_MESSAGE_2026-05-09.txt |
| control_input | False | .context/LIVE_STATE.md |
| control_input | True | .context/00_core/quick_reference_card.md |
| control_input | True | .context/00_core/research_operating_doctrine.md |
| control_input | False | .context/00_core/research_current_state.md |
| control_input | True | .context/00_core/goal_session_research_discipline.md |
| control_input | True | .context/00_core/local_heavy_data_inventory.md |
| control_input | True | .context/00_READING_ORDER.md |
| control_input | True | .context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md |
| control_input | True | research/science_program_2026_05/06_outcome_testing/nofill_cat_v2_residual_blocker_clear_source_access_lane/NOFILL_RESIDUAL_BLOCKER_ROW_DECISION_LEDGER_2026-05-09.jsonl |
| control_input | True | research/science_program_2026_05/06_outcome_testing/oti4_opening_drive_source_correction_or_contract_revision/OTI4_OPENING_DRIVE_ROW_DECISION_LEDGER_ROWS_2026-05-08.jsonl |
| control_input | True | research/science_program_2026_05/06_outcome_testing/oti4_opening_drive_source_correction_or_contract_revision/OTI4_OPENING_DRIVE_SOURCE_SEARCH_LEDGER_2026-05-08.json |
| control_input | True | research/science_program_2026_05/06_outcome_testing/oti4_opening_drive_source_correction_or_contract_revision/OTI4_OPENING_DRIVE_SOURCE_CONTRACT_PACKET_2026-05-08.json |
| official_web_tool_capture | True | C:\tmp\gtos_otb\NOFILLMAY3PROOF\research\science_program_2026_05\06_outcome_testing\nofill_may3_opening_range_market_closure_or_source_proof\raw\NOFILL_MAY3_OFFICIAL_CME_WEB_CAPTURE_2026-05-09.json |
| direct_curl_attempt_ledger | True | C:\tmp\gtos_otb\NOFILLMAY3PROOF\research\science_program_2026_05\06_outcome_testing\nofill_may3_opening_range_market_closure_or_source_proof\raw\NOFILL_MAY3_DIRECT_CME_CURL_ATTEMPTS_2026-05-09.json |
| broker_tick_parquet_NAS100 | True | C:\Users\MSI\Documents\ai-trading-agent\data\ticks\NAS100\2026-05-03.parquet |
| broker_tick_parquet_XAUUSD | True | C:\Users\MSI\Documents\ai-trading-agent\data\ticks\XAUUSD\2026-05-03.parquet |
| worktree_converted_sierra_nq_to_nas100_m1 | True | C:\tmp\gtos_otb\NOFILLMAY3PROOF\data\sierra_ohlcv_roots\sierra_nq_to_nas100_pilot_20260504\NAS100_M1.csv |
| worktree_converted_sierra_xauusd_m1 | True | C:\tmp\gtos_otb\NOFILLMAY3PROOF\data\sierra_ohlcv_roots\sierra_xauusd_scid_to_xauusd_pilot_20260504\XAUUSD_M1.csv |
| absolute_converted_sierra_nq_to_nas100_m1 | True | C:\Users\MSI\Documents\ai-trading-agent\data\sierra_ohlcv_roots\sierra_nq_to_nas100_pilot_20260504\NAS100_M1.csv |
| absolute_converted_sierra_xauusd_m1 | True | C:\Users\MSI\Documents\ai-trading-agent\data\sierra_ohlcv_roots\sierra_xauusd_scid_to_xauusd_pilot_20260504\XAUUSD_M1.csv |
| first_wave_nq_m1 | True | C:\tmp\gtos_otb\NOFILLMAY3PROOF\data\sierra_ohlcv_roots\sierra_first_wave_bounded_conversion_20260504\NAS100_NQ_M1.csv |
| first_wave_mnq_m1 | True | C:\tmp\gtos_otb\NOFILLMAY3PROOF\data\sierra_ohlcv_roots\sierra_first_wave_bounded_conversion_20260504\NAS100_MNQ_M1.csv |
| first_wave_xauusd_scid_m1 | True | C:\tmp\gtos_otb\NOFILLMAY3PROOF\data\sierra_ohlcv_roots\sierra_first_wave_bounded_conversion_20260504\XAUUSD_SCID_M1.csv |
| first_wave_gc_m1 | True | C:\tmp\gtos_otb\NOFILLMAY3PROOF\data\sierra_ohlcv_roots\sierra_first_wave_bounded_conversion_20260504\XAUUSD_GC_M1.csv |
| first_wave_mgc_m1 | True | C:\tmp\gtos_otb\NOFILLMAY3PROOF\data\sierra_ohlcv_roots\sierra_first_wave_bounded_conversion_20260504\XAUUSD_MGC_M1.csv |
| raw_sierra_nq_futures_proxy_scid | True | C:\SierraChart\Data\NQM26-CME.scid |
| raw_sierra_mnq_futures_proxy_scid | True | C:\SierraChart\Data\MNQM26-CME.scid |
| raw_sierra_xauusd_same_market_scid | True | C:\SierraChart\Data\XAUUSD.scid |
| raw_sierra_gc_futures_proxy_scid | True | C:\SierraChart\Data\GCM26-COMEX.scid |
| raw_sierra_mgc_futures_proxy_scid | True | C:\SierraChart\Data\MGCM26-COMEX.scid |
| raw_sierra_nq_depth_date_file | True | C:\SierraChart\Data\MarketDepthData\NQM26-CME.2026-05-03.depth |
| raw_sierra_mnq_depth_date_file | True | C:\SierraChart\Data\MarketDepthData\MNQM26-CME.2026-05-03.depth |
| raw_sierra_gc_depth_date_file | True | C:\SierraChart\Data\MarketDepthData\GCM26-COMEX.2026-05-03.depth |
| raw_sierra_mgc_depth_date_file | True | C:\SierraChart\Data\MarketDepthData\MGCM26-COMEX.2026-05-03.depth |

Note: recorded `resolved_path` values are authoritative for the upstream packet's source hash records. Current worktree copies of mutable context or prompt files can differ after merge/context refresh and are not source-data failures when the recorded source path still hash-matches.
