# OTI3 USDJPY Source Hash Noleak Audit - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

```json
{
  "artifact_family": "OTI3_USDJPY_SOURCE_HASH_NOLEAK_AUDIT",
  "flags_preserved": {
    "live_effect": false,
    "outcome_review_opened": false,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": false
  },
  "forbidden_key_hits": [],
  "forbidden_surfaces": {
    "account_history_accessed": false,
    "broker_actual_r_accessed": false,
    "live_trade_result_accessed": false,
    "mt5_account_calls": 0,
    "mt5_history_calls": 0,
    "mt5_order_calls": 0,
    "mt5_position_calls": 0,
    "order_send_calls": 0,
    "paid_api_or_databento_calls": 0
  },
  "generated_at_utc": "2026-05-08T14:57:32Z",
  "lane_id": "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT",
  "live_effect": false,
  "missing_sources": [],
  "no_leak_status": "PASS",
  "no_r_performance_scoring": true,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "repo_head": "9cad99c83bc12bf84a569ac82d579aa6ee978dc9",
  "schema_version": "oti3_usdjpy_price_only_quote_or_tick_contract_v1",
  "scope": "source_correction_or_contract_revision_only",
  "source_hash_failures": [],
  "source_hash_record_count": 15,
  "source_hash_records": [
    {
      "exists": true,
      "last_write_utc": "2026-05-08T14:33:26.308522+00:00",
      "path": "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\no_fill_lifecycle_categorical_result_packet\\NOFILL_CAT_PACKET_ROWS_2026-05-08.jsonl",
      "role": "controlling_or_upstream_input",
      "sha256": "824e984b8dcc1451671ff0d6a827cfe5dea47017971b718c3842ec370069ca6f",
      "size_bytes": 836817
    },
    {
      "exists": true,
      "last_write_utc": "2026-05-08T14:33:26.299382+00:00",
      "path": "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\no_fill_lifecycle_categorical_result_packet\\NOFILL_CAT_ELIGIBILITY_AND_BLOCKER_LEDGER_2026-05-08.json",
      "role": "controlling_or_upstream_input",
      "sha256": "d392da8f013641e0d3528396cbb4694b4fa86c029923c9d7c195794daaf877a1",
      "size_bytes": 236049
    },
    {
      "exists": true,
      "last_write_utc": "2026-05-08T14:33:26.337444+00:00",
      "path": "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\no_fill_lifecycle_closure_source_packet\\NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl",
      "role": "controlling_or_upstream_input",
      "sha256": "3a0c1e0d3eb42bbc540ba2857ee534f8e8c9d8a2b7e09c34ce954a25bdad0200",
      "size_bytes": 1072062
    },
    {
      "exists": true,
      "last_write_utc": "2026-05-08T14:33:26.389915+00:00",
      "path": "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\nofill_blocked_family_source_correction_router\\NOFILL_ROUTER_ROUTE_DECISION_LEDGER_2026-05-08.json",
      "role": "controlling_or_upstream_input",
      "sha256": "602bf97073797a3e4c82c19ac1d2880fa26fc1babae1ad81e55e3e25d7bf3f9c",
      "size_bytes": 499135
    },
    {
      "exists": true,
      "last_write_utc": "2026-05-08T14:33:26.390939+00:00",
      "path": "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\nofill_blocked_family_source_correction_router\\NOFILL_ROUTER_SOURCE_SEARCH_LEDGER_2026-05-08.json",
      "role": "controlling_or_upstream_input",
      "sha256": "5486c852baee643a9ea20ca67638e5718566fc3e5813497731938de69d1f90ce",
      "size_bytes": 152759
    },
    {
      "exists": true,
      "last_write_utc": "2026-05-08T14:33:26.384985+00:00",
      "path": "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\nofill_blocked_family_source_correction_router\\NOFILL_ROUTER_CONTEXT_ANCHOR_2026-05-08.md",
      "role": "controlling_or_upstream_input",
      "sha256": "5b4e78613a0ebe7c221bae69cbdd1d549856a0f7356e611a898d9beb5636caf9",
      "size_bytes": 2737
    },
    {
      "exists": true,
      "last_write_utc": "2026-05-08T14:33:26.393379+00:00",
      "path": "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\nofill_blocked_family_source_correction_router\\OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT_PROMPT_PACK_2026-05-08.md",
      "role": "controlling_or_upstream_input",
      "sha256": "7a336337f790a8632fa608fde518a67e0dc2e956bb34c75dd4d29dccc03b58c6",
      "size_bytes": 5139
    },
    {
      "exists": true,
      "last_write_utc": "2026-05-08T14:33:26.351252+00:00",
      "path": "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\no_fill_lifecycle_result_contract_design\\NOFILL_RESULT_CONTRACT_FROZEN_RULEBOOK_2026-05-08.json",
      "role": "controlling_or_upstream_input",
      "sha256": "80e37bd10346aeec9e858a3b73fa238c0f657b7178e466017ae11ad2ed579227",
      "size_bytes": 13581
    },
    {
      "exists": true,
      "last_write_utc": "2026-05-08T14:33:26.354765+00:00",
      "path": "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\no_fill_lifecycle_result_contract_design\\NOFILL_RESULT_CONTRACT_TOUCH_AND_PATH_PARSER_2026-05-08.json",
      "role": "controlling_or_upstream_input",
      "sha256": "e3d342f02890ad1894100f13d2f62a04d58688d9b86032ae90b8f40f3a2232cb",
      "size_bytes": 3386
    },
    {
      "exists": true,
      "expected_sha256": "9a16ad55351131b0675bbc83390059deeb3ee6b669b42f848219cee7b47b5519",
      "hash_match": true,
      "last_write_utc": "2026-05-02T07:28:22.591448+00:00",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260401_20260502_readonly\\USDJPY_M1.csv",
      "role": "price_compatible_context_only",
      "sha256": "9a16ad55351131b0675bbc83390059deeb3ee6b669b42f848219cee7b47b5519",
      "size_bytes": 1832342
    },
    {
      "exists": true,
      "expected_sha256": "ff7db8dc50f7f7083557f54fc539aff951583f35ffab9f711ecb7af85aa27622",
      "hash_match": true,
      "last_write_utc": "2026-05-08T14:57:04.341702+00:00",
      "path": "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-17.parquet",
      "role": "bid_ask_quote_tick_source",
      "sha256": "ff7db8dc50f7f7083557f54fc539aff951583f35ffab9f711ecb7af85aa27622",
      "size_bytes": 2209369
    },
    {
      "exists": true,
      "expected_sha256": "13951dcfc7a0dd14783cadd18782bb2caec1573601c6b6e49d53da8f261d2fb9",
      "hash_match": true,
      "last_write_utc": "2026-05-08T14:57:04.493546+00:00",
      "path": "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet",
      "role": "bid_ask_quote_tick_source",
      "sha256": "13951dcfc7a0dd14783cadd18782bb2caec1573601c6b6e49d53da8f261d2fb9",
      "size_bytes": 2045401
    },
    {
      "exists": true,
      "expected_sha256": "a48099563df87d2b2654ccae9c235917024dbbf32817eed5997880d15c544bce",
      "hash_match": true,
      "last_write_utc": "2026-05-01T00:00:01.123979+00:00",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-04-30.parquet",
      "role": "bid_ask_quote_tick_source",
      "sha256": "a48099563df87d2b2654ccae9c235917024dbbf32817eed5997880d15c544bce",
      "size_bytes": 3908592
    },
    {
      "exists": true,
      "expected_sha256": "7d13dd73d30a2fb5964b14e688d9aa9a4425828f6901067c1f04e36321430456",
      "hash_match": true,
      "last_write_utc": "2026-05-03T23:46:11.814101+00:00",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-01.parquet",
      "role": "bid_ask_quote_tick_source",
      "sha256": "7d13dd73d30a2fb5964b14e688d9aa9a4425828f6901067c1f04e36321430456",
      "size_bytes": 2768379
    },
    {
      "exists": true,
      "expected_sha256": null,
      "hash_match": null,
      "last_write_utc": "2026-05-08T14:33:26.736551+00:00",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\oti3_g3_geometry_quarantined_results\\OTI3_G3_GEOMETRY_RESULT_LEDGER_ROWS_2026-05-07.jsonl",
      "role": "upstream_source_artifact",
      "sha256": "a2b7c790bba3a16d6762f7be7e4a81b790b35c3bc3c91acfb9d703a186f44847",
      "size_bytes": 519340
    }
  ],
  "validation_safe": false
}
```
