# OTI4 Opening-Drive Source Search Ledger

- Generated at UTC: `2026-05-08T14:58:23Z`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- Validation safe: `false`
- Outcome review opened: `false`
- Live effect: `false`

- Records consumed files, tick roots, local CSV search, and source hash checks.

```json
{
  "artifact_family": "OTI4_OPENING_DRIVE_SOURCE_SEARCH_LEDGER",
  "generated_at_utc": "2026-05-08T14:58:23Z",
  "lane_id": "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION",
  "live_effect": false,
  "no_approved_csv_covering_empty_2026_05_03_range_windows": true,
  "outcome_review_opened": false,
  "parser_version": "oti4_opening_drive_tick_mid_m1_source_contract_v1_2026_05_08",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "searched_roots": [
    {
      "consumed_files": [
        ".context/LIVE_STATE.md",
        ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
        ".context/00_core/quick_reference_card.md",
        ".context/00_core/research_operating_doctrine.md",
        ".context/00_core/research_current_state.md",
        ".context/00_core/goal_session_research_discipline.md",
        ".context/00_core/local_heavy_data_inventory.md",
        "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION_PROMPT_PACK_2026-05-08.md",
        "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_CONTEXT_ANCHOR_2026-05-08.md",
        "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_ROUTE_DECISION_LEDGER_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_2026-05-08.json",
        "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-062__G6-EXP-003-OPENING-DRIVE-CONTINUATION__g6_local_ohlc_input_packet_2026-05-07.json",
        "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json",
        "research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_SOURCE_HASH_LEDGER_2026-05-07.json",
        "research/science_program_2026_05/06_outcome_testing/g12_otx_g6_post_audit/G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_2026-05-07.json",
        "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_categorical_result_packet/NOFILL_CAT_ELIGIBILITY_AND_BLOCKER_LEDGER_2026-05-08.json"
      ],
      "purpose": "worktree prompt/router/OTI4/OTX/G12 artifacts",
      "root": "."
    },
    {
      "missing_needed_tick_files": [],
      "needed_symbol_dates": [
        "GBPJPY|2026-05-04",
        "GBPJPY|2026-05-06",
        "NAS100|2026-05-03",
        "NAS100|2026-05-04",
        "NAS100|2026-05-05",
        "NAS100|2026-05-06",
        "US30_cash|2026-05-06",
        "USDJPY|2026-05-05",
        "XAGUSD|2026-05-04",
        "XAGUSD|2026-05-05",
        "XAUUSD|2026-05-03",
        "XAUUSD|2026-05-04",
        "XAUUSD|2026-05-05",
        "XAUUSD|2026-05-06"
      ],
      "purpose": "approved local tick parquet source for OTI4 symbol-date range and breakout proof",
      "root": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks"
    },
    {
      "candidate_file_count": 49,
      "covering_2026_05_03_1300_1630_count": 0,
      "patterns": [
        "NAS100_M1.csv",
        "NAS100_M15.csv",
        "NAS100_M5.csv",
        "XAUUSD_M1.csv",
        "XAUUSD_M15.csv",
        "XAUUSD_M5.csv"
      ],
      "records": [
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2025-12-18T10:10:00Z",
          "last_utc": "2026-04-02T23:49:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\historical\\XAUUSD_M1.csv",
          "rows": 99999,
          "size_bytes": 5645375
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2024-04-01T01:00:00Z",
          "last_utc": "2026-04-17T23:15:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\historical\\XAUUSD_M15.csv",
          "rows": 48359,
          "size_bytes": 2768718
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2024-10-29T03:20:00Z",
          "last_utc": "2026-04-02T23:45:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\historical\\XAUUSD_M5.csv",
          "rows": 99999,
          "size_bytes": 5670559
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2022-10-20T11:00:00Z",
          "last_utc": "2024-02-19T18:45:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\historical_2022_2023\\NAS100_M15.csv",
          "rows": 21695,
          "size_bytes": 1276861
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2022-01-28T11:30:00Z",
          "last_utc": "2024-02-19T21:15:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\historical_2022_2023\\XAUUSD_M15.csv",
          "rows": 48365,
          "size_bytes": 2709428
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-01-14T19:01:00Z",
          "last_utc": "2026-04-27T22:27:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\historical_2026\\NAS100_M1.csv",
          "rows": 100003,
          "size_bytes": 6096002
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2025-10-01T01:00:00Z",
          "last_utc": "2026-04-24T23:45:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\historical_2026\\NAS100_M15.csv",
          "rows": 13284,
          "size_bytes": 821838
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-01-14T06:30:00Z",
          "last_utc": "2026-04-27T22:27:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\historical_2026\\XAUUSD_M1.csv",
          "rows": 100003,
          "size_bytes": 5667600
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2025-10-01T01:00:00Z",
          "last_utc": "2026-04-24T23:45:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\historical_2026\\XAUUSD_M15.csv",
          "rows": 13288,
          "size_bytes": 764698
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-04-27T01:00:00Z",
          "last_utc": "2026-05-01T03:45:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_candidate_gap_20260501\\NAS100_M15.csv",
          "rows": 380,
          "size_bytes": 23609
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-04-27T01:00:00Z",
          "last_utc": "2026-05-01T03:45:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_candidate_gap_20260501\\XAUUSD_M15.csv",
          "rows": 380,
          "size_bytes": 22010
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2022-10-20T11:00:00Z",
          "last_utc": "2026-04-30T23:45:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_m15_2022_2026_fn_chunked_v1\\NAS100_M15.csv",
          "rows": 72862,
          "size_bytes": 4448668
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2022-02-01T21:30:00Z",
          "last_utc": "2026-04-30T23:45:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_m15_2022_2026_fn_chunked_v1\\XAUUSD_M15.csv",
          "rows": 100012,
          "size_bytes": 5728651
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-01-20T05:27:00Z",
          "last_utc": "2026-04-30T23:59:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\\NAS100_M1.csv",
          "rows": 99768,
          "size_bytes": 6080996
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2024-11-28T06:30:00Z",
          "last_utc": "2026-04-30T23:55:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\\NAS100_M5.csv",
          "rows": 99953,
          "size_bytes": 6115519
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-01-19T11:59:00Z",
          "last_utc": "2026-04-30T23:59:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\\XAUUSD_M1.csv",
          "rows": 99768,
          "size_bytes": 5653825
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2024-11-29T06:40:00Z",
          "last_utc": "2026-04-30T23:55:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1\\XAUUSD_M5.csv",
          "rows": 99953,
          "size_bytes": 5715943
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2022-10-20T11:00:00Z",
          "last_utc": "2026-04-30T23:59:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_rescue_all_m1_m5_chunk1_after_maxbars\\NAS100_M1.csv",
          "rows": 1052457,
          "size_bytes": 63104589
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2022-10-20T11:00:00Z",
          "last_utc": "2026-04-30T23:55:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_rescue_all_m1_m5_chunk1_after_maxbars\\NAS100_M5.csv",
          "rows": 212964,
          "size_bytes": 12920547
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2022-01-03T01:00:00Z",
          "last_utc": "2026-04-30T23:59:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_rescue_all_m1_m5_chunk1_after_maxbars\\XAUUSD_M1.csv",
          "rows": 1528838,
          "size_bytes": 85709688
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2022-01-03T01:00:00Z",
          "last_utc": "2026-04-30T23:55:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_rescue_all_m1_m5_chunk1_after_maxbars\\XAUUSD_M5.csv",
          "rows": 305941,
          "size_bytes": 17371690
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-01-19T12:29:00Z",
          "last_utc": "2026-04-30T23:59:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_rescue_xau_m1_m5_chunk1_20220501\\XAUUSD_M1.csv",
          "rows": 99738,
          "size_bytes": 5652126
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2024-11-29T07:10:00Z",
          "last_utc": "2026-04-30T23:55:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_rescue_xau_m1_m5_chunk1_20220501\\XAUUSD_M5.csv",
          "rows": 99947,
          "size_bytes": 5715599
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2022-01-03T01:00:00Z",
          "last_utc": "2026-04-30T23:59:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_rescue_xau_m1_m5_chunk1_after_maxbars\\XAUUSD_M1.csv",
          "rows": 1528838,
          "size_bytes": 85709688
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2022-01-03T01:00:00Z",
          "last_utc": "2026-04-30T23:55:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_rescue_xau_m1_m5_chunk1_after_maxbars\\XAUUSD_M5.csv",
          "rows": 305941,
          "size_bytes": 17371690
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-04-01T01:00:00Z",
          "last_utc": "2026-05-01T23:59:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260401_20260502_readonly\\NAS100_M1.csv",
          "rows": 31276,
          "size_bytes": 1901558
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-04-01T01:00:00Z",
          "last_utc": "2026-05-01T23:45:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260401_20260502_readonly\\NAS100_M15.csv",
          "rows": 2086,
          "size_bytes": 129295
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-04-01T01:00:00Z",
          "last_utc": "2026-05-01T23:55:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260401_20260502_readonly\\NAS100_M5.csv",
          "rows": 6256,
          "size_bytes": 384937
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-04-01T01:00:00Z",
          "last_utc": "2026-05-01T23:59:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260401_20260502_readonly\\XAUUSD_M1.csv",
          "rows": 30357,
          "size_bytes": 1719841
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-04-01T01:00:00Z",
          "last_utc": "2026-05-01T23:45:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260401_20260502_readonly\\XAUUSD_M15.csv",
          "rows": 2024,
          "size_bytes": 117057
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-04-01T01:00:00Z",
          "last_utc": "2026-05-01T23:55:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260401_20260502_readonly\\XAUUSD_M5.csv",
          "rows": 6072,
          "size_bytes": 349193
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-05-01T01:00:00Z",
          "last_utc": "2026-05-01T23:59:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260501_readonly\\NAS100_M1.csv",
          "rows": 1380,
          "size_bytes": 83999
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-05-01T01:00:00Z",
          "last_utc": "2026-05-01T23:45:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260501_readonly\\NAS100_M15.csv",
          "rows": 92,
          "size_bytes": 5738
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-05-01T01:00:00Z",
          "last_utc": "2026-05-01T23:55:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260501_readonly\\NAS100_M5.csv",
          "rows": 276,
          "size_bytes": 17022
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-05-01T01:00:00Z",
          "last_utc": "2026-05-01T23:59:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260501_readonly\\XAUUSD_M1.csv",
          "rows": 1380,
          "size_bytes": 78191
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-05-01T01:00:00Z",
          "last_utc": "2026-05-01T23:45:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260501_readonly\\XAUUSD_M15.csv",
          "rows": 92,
          "size_bytes": 5347
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-05-01T01:00:00Z",
          "last_utc": "2026-05-01T23:55:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260501_readonly\\XAUUSD_M5.csv",
          "rows": 276,
          "size_bytes": 15881
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2024-01-02T01:00:00Z",
          "last_utc": "2026-04-02T23:45:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\NAS100_M15.csv",
          "rows": 49215,
          "size_bytes": 2934918
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2024-10-24T09:20:00Z",
          "last_utc": "2026-04-03T04:45:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\NAS100_M5.csv",
          "rows": 90000,
          "size_bytes": 5301737
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2024-07-01T00:00:00Z",
          "last_utc": "2025-09-30T23:45:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\old_huggingface_backup\\XAUUSD_M15.csv",
          "rows": 22346,
          "size_bytes": 1300118
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2024-07-01T00:00:00Z",
          "last_utc": "2025-09-30T23:45:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\raw\\XAUUSD_M15.csv",
          "rows": 22346,
          "size_bytes": 1300118
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2025-10-29T22:43:00Z",
          "last_utc": "2026-05-01T20:59:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_nq_to_nas100_pilot_20260504\\NAS100_M1.csv",
          "rows": 70210,
          "size_bytes": 4779986
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2025-10-29T22:30:00Z",
          "last_utc": "2026-05-01T20:45:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_nq_to_nas100_pilot_20260504\\NAS100_M15.csv",
          "rows": 7683,
          "size_bytes": 529758
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2025-10-29T22:40:00Z",
          "last_utc": "2026-05-01T20:55:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_nq_to_nas100_pilot_20260504\\NAS100_M5.csv",
          "rows": 18877,
          "size_bytes": 1297480
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2025-10-28T14:19:00Z",
          "last_utc": "2026-05-01T20:44:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\XAUUSD_M1.csv",
          "rows": 177692,
          "size_bytes": 15540189
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2025-10-28T14:15:00Z",
          "last_utc": "2026-05-01T20:30:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\XAUUSD_M15.csv",
          "rows": 11885,
          "size_bytes": 1108234
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2025-10-28T14:15:00Z",
          "last_utc": "2026-05-01T20:40:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\sierra_ohlcv_roots\\sierra_xauusd_scid_to_xauusd_pilot_20260504\\XAUUSD_M5.csv",
          "rows": 35618,
          "size_bytes": 3255891
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-03-24T05:00:00Z",
          "last_utc": "2026-04-02T22:45:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\XAUUSD_M15.csv",
          "rows": 700,
          "size_bytes": 43229
        },
        {
          "covers_2026_05_03_1300_1630": false,
          "first_utc": "2026-04-01T20:00:00Z",
          "last_utc": "2026-04-02T22:55:00Z",
          "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\XAUUSD_M5.csv",
          "rows": 300,
          "size_bytes": 18529
        }
      ],
      "root": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data"
    },
    {
      "evidence": "research/science_program_2026_05/06_outcome_testing/nofill_blocked_family_source_correction_router/NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_2026-05-08.json",
      "oti4_router_conclusion": "Local tick source is present for all OTI4 symbol-date probes, but current accepted packet still lacks source-hashed prereg opening-drive fields.",
      "purpose": "prior router-saturated local-heavy search",
      "root": "C:\\tmp and C:\\SierraChart"
    }
  ],
  "source_contract_id": "OTI4_OPENING_DRIVE_TICK_RANGE_BREAKOUT_SOURCE_CONTRACT_V1",
  "source_hash_mismatch_count": 0,
  "source_hash_mismatches": [],
  "source_hash_records": [
    {
      "exists": true,
      "expected_sha256": "4e2d512fb980b2437e56e939b28cb6dae7a9fd4cf863536cfc59a4126da77fe1",
      "observed_sha256": "4e2d512fb980b2437e56e939b28cb6dae7a9fd4cf863536cfc59a4126da77fe1",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet",
      "role": "strict_tick_source",
      "sha256_match": true,
      "size_bytes": 4856218,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "f94cd1ba695b36c099fe50cfb926937d0af8057a5255b73fd00587b58f75fe3e",
      "observed_sha256": "f94cd1ba695b36c099fe50cfb926937d0af8057a5255b73fd00587b58f75fe3e",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet",
      "role": "strict_tick_source",
      "sha256_match": true,
      "size_bytes": 5377035,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "41996c1de550993f124120b821d9495c0ffde06d5c0c04b36676a2112766e208",
      "observed_sha256": "41996c1de550993f124120b821d9495c0ffde06d5c0c04b36676a2112766e208",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-03.parquet",
      "role": "strict_tick_source",
      "sha256_match": true,
      "size_bytes": 649819,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "7b2f89ecbbbc59124fc56c7b9e504d7b41e299f7bd950fc54821e8f18a7fa478",
      "observed_sha256": "7b2f89ecbbbc59124fc56c7b9e504d7b41e299f7bd950fc54821e8f18a7fa478",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-04.parquet",
      "role": "strict_tick_source",
      "sha256_match": true,
      "size_bytes": 15119257,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "13357b7bc6b4d02690ab7055b611b431c6e2ce2a77c36df791f347cf7fcaed35",
      "observed_sha256": "13357b7bc6b4d02690ab7055b611b431c6e2ce2a77c36df791f347cf7fcaed35",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-05.parquet",
      "role": "strict_tick_source",
      "sha256_match": true,
      "size_bytes": 11479489,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "41896f6984bcba5ef3ba5ae656303e5968c5a5ed26acda58f439aa45bee45ad4",
      "observed_sha256": "41896f6984bcba5ef3ba5ae656303e5968c5a5ed26acda58f439aa45bee45ad4",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-06.parquet",
      "role": "strict_tick_source",
      "sha256_match": true,
      "size_bytes": 15555785,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "eb90e21f12aef7564a6f2995fc8a051eb27a61057326e3c5ccf4b5c3132f69fb",
      "observed_sha256": "eb90e21f12aef7564a6f2995fc8a051eb27a61057326e3c5ccf4b5c3132f69fb",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-05-06.parquet",
      "role": "strict_tick_source",
      "sha256_match": true,
      "size_bytes": 3945958,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "7316926c90065e3f0d8c3c8b49d38544a82dd82cc0536cc35d415e93c82dad76",
      "observed_sha256": "7316926c90065e3f0d8c3c8b49d38544a82dd82cc0536cc35d415e93c82dad76",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-05.parquet",
      "role": "strict_tick_source",
      "sha256_match": true,
      "size_bytes": 1934862,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "fe80b36da79fe2491eb488c77d20f4e734435752715228e1199f7f76055a7868",
      "observed_sha256": "fe80b36da79fe2491eb488c77d20f4e734435752715228e1199f7f76055a7868",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-04.parquet",
      "role": "strict_tick_source",
      "sha256_match": true,
      "size_bytes": 3589112,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "ad451c922db79a8643e32b7b9c5f55e6d5cd417834ef0fbf5b20b5799d004237",
      "observed_sha256": "ad451c922db79a8643e32b7b9c5f55e6d5cd417834ef0fbf5b20b5799d004237",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-05.parquet",
      "role": "strict_tick_source",
      "sha256_match": true,
      "size_bytes": 2892270,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "0911ab624dc038992e3f3ac5d7c5e70bc9bcc498cf61c1388035f795b599a6f3",
      "observed_sha256": "0911ab624dc038992e3f3ac5d7c5e70bc9bcc498cf61c1388035f795b599a6f3",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-03.parquet",
      "role": "strict_tick_source",
      "sha256_match": true,
      "size_bytes": 664233,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "1186ffbcdba2bb028fd39ebada82dce9c1d342a318b9e3cc65e823b2b280f09f",
      "observed_sha256": "1186ffbcdba2bb028fd39ebada82dce9c1d342a318b9e3cc65e823b2b280f09f",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-04.parquet",
      "role": "strict_tick_source",
      "sha256_match": true,
      "size_bytes": 9679772,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "9a361078f8448d8d69aacbf3905d38d291282ce223d269fe033b0e6eb9814a0f",
      "observed_sha256": "9a361078f8448d8d69aacbf3905d38d291282ce223d269fe033b0e6eb9814a0f",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-05.parquet",
      "role": "strict_tick_source",
      "sha256_match": true,
      "size_bytes": 6788510,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "fdec881196886808c90aa25d6a91d99c5f1105274ecbd435e442f63bcac59439",
      "observed_sha256": "fdec881196886808c90aa25d6a91d99c5f1105274ecbd435e442f63bcac59439",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-06.parquet",
      "role": "strict_tick_source",
      "sha256_match": true,
      "size_bytes": 1883513,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "d8637b6e9809801cb8e28d0c2b633bfac9b22f74196d9b3c43c55856fe9ca994",
      "observed_sha256": "d8637b6e9809801cb8e28d0c2b633bfac9b22f74196d9b3c43c55856fe9ca994",
      "path": "C:\\tmp\\gtos_otb\\OTI4OPEN\\.context\\00_core\\goal_session_research_discipline.md",
      "role": "mutable_preflight_context",
      "sha256_match": true,
      "size_bytes": 11274,
      "strict_recompute_required": false
    },
    {
      "exists": true,
      "expected_sha256": "fad850db93ce63f2ccf599cb4a54047b40db852b14c9be2711a362beab0584d0",
      "observed_sha256": "fad850db93ce63f2ccf599cb4a54047b40db852b14c9be2711a362beab0584d0",
      "path": "C:\\tmp\\gtos_otb\\OTI4OPEN\\.context\\00_core\\local_heavy_data_inventory.md",
      "role": "mutable_preflight_context",
      "sha256_match": true,
      "size_bytes": 4218,
      "strict_recompute_required": false
    },
    {
      "exists": true,
      "expected_sha256": "e09d71390f6862a97fe7d40223e1acd1a7914f5350ea6f954e4a84521f6d9ffd",
      "observed_sha256": "e09d71390f6862a97fe7d40223e1acd1a7914f5350ea6f954e4a84521f6d9ffd",
      "path": "C:\\tmp\\gtos_otb\\OTI4OPEN\\.context\\00_core\\quick_reference_card.md",
      "role": "mutable_preflight_context",
      "sha256_match": true,
      "size_bytes": 11078,
      "strict_recompute_required": false
    },
    {
      "exists": true,
      "expected_sha256": "9ba0b5d4d54a027d7fd06fe2cac7b69d8c35a93cae0eac4aaf97295ef149ad3a",
      "observed_sha256": "9ba0b5d4d54a027d7fd06fe2cac7b69d8c35a93cae0eac4aaf97295ef149ad3a",
      "path": "C:\\tmp\\gtos_otb\\OTI4OPEN\\.context\\00_core\\research_current_state.md",
      "role": "mutable_preflight_context",
      "sha256_match": true,
      "size_bytes": 490101,
      "strict_recompute_required": false
    },
    {
      "exists": true,
      "expected_sha256": "27901cd44d28dc159efd487f4717f295f4089afa34bb0bba14a171dc0f769ebe",
      "observed_sha256": "27901cd44d28dc159efd487f4717f295f4089afa34bb0bba14a171dc0f769ebe",
      "path": "C:\\tmp\\gtos_otb\\OTI4OPEN\\.context\\00_core\\research_operating_doctrine.md",
      "role": "mutable_preflight_context",
      "sha256_match": true,
      "size_bytes": 11400,
      "strict_recompute_required": false
    },
    {
      "exists": true,
      "expected_sha256": "0662139cbae0ef3ee6a0282af14136b02a9e5c49d5e462b62fd16243a4645235",
      "observed_sha256": "0662139cbae0ef3ee6a0282af14136b02a9e5c49d5e462b62fd16243a4645235",
      "path": "C:\\tmp\\gtos_otb\\OTI4OPEN\\.context\\02_session_handoffs\\SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
      "role": "mutable_preflight_context",
      "sha256_match": true,
      "size_bytes": 25348,
      "strict_recompute_required": false
    },
    {
      "exists": true,
      "expected_sha256": "81eaf6cd499a190a0462e9b8e4a611c923afc50d8118c47477042bf529d463b6",
      "observed_sha256": "81eaf6cd499a190a0462e9b8e4a611c923afc50d8118c47477042bf529d463b6",
      "path": "C:\\tmp\\gtos_otb\\OTI4OPEN\\.context\\LIVE_STATE.md",
      "role": "mutable_preflight_context",
      "sha256_match": true,
      "size_bytes": 13375,
      "strict_recompute_required": false
    },
    {
      "exists": true,
      "expected_sha256": "bb0f5428ef5e9e3de376caa9ecd0544ca0d891842fa8f0dcac3f800d1deb6f2c",
      "observed_sha256": "bb0f5428ef5e9e3de376caa9ecd0544ca0d891842fa8f0dcac3f800d1deb6f2c",
      "path": "C:\\tmp\\gtos_otb\\OTI4OPEN\\research\\science_program_2026_05\\06_outcome_testing\\g12_otx_g6_post_audit\\G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_2026-05-07.json",
      "role": "strict_source_or_control_artifact",
      "sha256_match": true,
      "size_bytes": 9841,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "d392da8f013641e0d3528396cbb4694b4fa86c029923c9d7c195794daaf877a1",
      "observed_sha256": "d392da8f013641e0d3528396cbb4694b4fa86c029923c9d7c195794daaf877a1",
      "path": "C:\\tmp\\gtos_otb\\OTI4OPEN\\research\\science_program_2026_05\\06_outcome_testing\\no_fill_lifecycle_categorical_result_packet\\NOFILL_CAT_ELIGIBILITY_AND_BLOCKER_LEDGER_2026-05-08.json",
      "role": "strict_source_or_control_artifact",
      "sha256_match": true,
      "size_bytes": 236049,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "5b4e78613a0ebe7c221bae69cbdd1d549856a0f7356e611a898d9beb5636caf9",
      "observed_sha256": "5b4e78613a0ebe7c221bae69cbdd1d549856a0f7356e611a898d9beb5636caf9",
      "path": "C:\\tmp\\gtos_otb\\OTI4OPEN\\research\\science_program_2026_05\\06_outcome_testing\\nofill_blocked_family_source_correction_router\\NOFILL_ROUTER_CONTEXT_ANCHOR_2026-05-08.md",
      "role": "strict_source_or_control_artifact",
      "sha256_match": true,
      "size_bytes": 2737,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "602bf97073797a3e4c82c19ac1d2880fa26fc1babae1ad81e55e3e25d7bf3f9c",
      "observed_sha256": "602bf97073797a3e4c82c19ac1d2880fa26fc1babae1ad81e55e3e25d7bf3f9c",
      "path": "C:\\tmp\\gtos_otb\\OTI4OPEN\\research\\science_program_2026_05\\06_outcome_testing\\nofill_blocked_family_source_correction_router\\NOFILL_ROUTER_ROUTE_DECISION_LEDGER_2026-05-08.json",
      "role": "strict_source_or_control_artifact",
      "sha256_match": true,
      "size_bytes": 499135,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "5486c852baee643a9ea20ca67638e5718566fc3e5813497731938de69d1f90ce",
      "observed_sha256": "5486c852baee643a9ea20ca67638e5718566fc3e5813497731938de69d1f90ce",
      "path": "C:\\tmp\\gtos_otb\\OTI4OPEN\\research\\science_program_2026_05\\06_outcome_testing\\nofill_blocked_family_source_correction_router\\NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_2026-05-08.json",
      "role": "strict_source_or_control_artifact",
      "sha256_match": true,
      "size_bytes": 152759,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "1bffecae37d5bc42a69027bb86176c3900ee8102971bbbbf677c63d5ea48cc1b",
      "observed_sha256": "1bffecae37d5bc42a69027bb86176c3900ee8102971bbbbf677c63d5ea48cc1b",
      "path": "C:\\tmp\\gtos_otb\\OTI4OPEN\\research\\science_program_2026_05\\06_outcome_testing\\nofill_blocked_family_source_correction_router\\OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION_PROMPT_PACK_2026-05-08.md",
      "role": "strict_source_or_control_artifact",
      "sha256_match": true,
      "size_bytes": 4098,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "fc587c1ffb8452718bc3d00fd8f80bd443b043387b862dce1679944dea3af080",
      "observed_sha256": "fc587c1ffb8452718bc3d00fd8f80bd443b043387b862dce1679944dea3af080",
      "path": "C:\\tmp\\gtos_otb\\OTI4OPEN\\research\\science_program_2026_05\\06_outcome_testing\\otb2r_g6_local_ohlc_momentum_reversion_packets\\packets\\OTG0-PKT-062__G6-EXP-003-OPENING-DRIVE-CONTINUATION__g6_local_ohlc_input_packet_2026-05-07.json",
      "role": "strict_source_or_control_artifact",
      "sha256_match": true,
      "size_bytes": 568343,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "38d5ef2dd5335fa4e4268e446f2cbc5ae0c10602d937c4d6c4242f66b2b09224",
      "observed_sha256": "38d5ef2dd5335fa4e4268e446f2cbc5ae0c10602d937c4d6c4242f66b2b09224",
      "path": "C:\\tmp\\gtos_otb\\OTI4OPEN\\research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.json",
      "role": "strict_source_or_control_artifact",
      "sha256_match": true,
      "size_bytes": 1207034,
      "strict_recompute_required": true
    },
    {
      "exists": true,
      "expected_sha256": "6b501751b38edabb05bff9049d59379d213d54b40b3885d0587effa237b1ea6a",
      "observed_sha256": "6b501751b38edabb05bff9049d59379d213d54b40b3885d0587effa237b1ea6a",
      "path": "C:\\tmp\\gtos_otb\\OTI4OPEN\\research\\science_program_2026_05\\06_outcome_testing\\otx_g6_tick_aware_end_to_end_resolution\\OTX_G6_SOURCE_HASH_LEDGER_2026-05-07.json",
      "role": "strict_source_or_control_artifact",
      "sha256_match": true,
      "size_bytes": 22128,
      "strict_recompute_required": true
    }
  ],
  "validation_safe": false
}
```
