# CNR Source Field Sample Floor And Expansion Report - 2026-05-07

Promotion verdict: `NO_PROMOTION_VERDICT`  
Validation safe: `false`  
Outcome review opened: `false`  
Live effect: `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_SOURCE_FIELD_SAMPLE_FLOOR_AND_EXPANSION_REPORT",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "current_unique_primary_duplicate_groups": 74,
  "databento_calls": 0,
  "duplicate_report_ref": "research/science_program_2026_05/06_outcome_testing/cnr_source_field_packet_builder/CNR_SOURCE_FIELD_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.json",
  "expansion_status": "LOCAL_TICK_QUOTE_EXTRACTION_ATTEMPTED_FOR_ALL_SOURCE_RECORDS; remaining blockers are source-field/schema blockers, not worktree absence",
  "generated_at_utc": "2026-05-07T16:38:18Z",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "ready_unique_primary_duplicate_groups": 30,
  "sample_floor_policy": {
    "aggregate_descriptive": ">=30 unique duplicate groups",
    "single_packet": "single-row result-or-impossibility can be audited by G12/G0 only after input packet audit",
    "validation_dossier": ">=50 unique duplicate groups with DSR/PBO/effective-N computable or explicitly not_computable"
  },
  "searched_root_count": 9,
  "searched_roots": [
    {
      "denied_or_walk_errors": [],
      "exists": true,
      "result_count_returned": 120,
      "root": "C:\\Users\\MSI\\Documents\\ai-trading-agent",
      "search_status": "SEARCHED",
      "truncated": true
    },
    {
      "denied_or_walk_errors": [],
      "exists": true,
      "result_count_returned": 120,
      "root": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\research\\science_program_2026_05\\06_outcome_testing",
      "search_status": "SEARCHED",
      "truncated": true
    },
    {
      "denied_or_walk_errors": [],
      "exists": true,
      "result_count_returned": 120,
      "root": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data",
      "search_status": "SEARCHED",
      "truncated": true
    },
    {
      "denied_or_walk_errors": [],
      "exists": true,
      "result_count_returned": 62,
      "root": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks",
      "search_status": "SEARCHED",
      "truncated": false
    },
    {
      "denied_or_walk_errors": [],
      "exists": true,
      "result_count_returned": 69,
      "root": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external",
      "search_status": "SEARCHED",
      "truncated": false
    },
    {
      "denied_or_walk_errors": [],
      "exists": true,
      "result_count_returned": 6,
      "root": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs",
      "search_status": "SEARCHED",
      "truncated": false
    },
    {
      "denied_or_walk_errors": [],
      "exists": true,
      "result_count_returned": 120,
      "root": "C:\\tmp",
      "search_status": "SEARCHED",
      "truncated": true
    },
    {
      "denied_or_walk_errors": [],
      "exists": true,
      "result_count_returned": 120,
      "root": "C:\\Users\\MSI\\Documents",
      "search_status": "SEARCHED",
      "truncated": true
    },
    {
      "denied_or_walk_errors": [],
      "exists": true,
      "result_count_returned": 14,
      "root": "C:\\SierraChart\\Data",
      "search_status": "SEARCHED",
      "truncated": false
    }
  ],
  "small_n_handling": "small n blocks validation claims only; packet build/search/extraction continued across approved roots",
  "validation_safe": false
}
```
