# OTI7 CNR No-Leak Label Family Audit - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `False`  
**Outcome review opened:** `False`  
**Live effect:** `False`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "OTI7_CNR_ACCEPTED_QUARANTINED_RESULTS",
  "artifact_type": "noleak_label_family_audit",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "broker_actual_r_inspected": false,
  "databento_calls": 0,
  "forbidden_input_key_fragment_hit_count": 0,
  "forbidden_input_key_fragment_hits": [],
  "forbidden_sources_skipped": [
    "shadow_logs/broker_actual_r_audit.jsonl",
    "data/account_history/",
    "knowledge_base/trade_records/",
    "shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl",
    "shadow_logs/candidate_ltf_path_order.jsonl hidden terminal labels",
    "shadow_logs/continuation_no_retrace_resolutions.jsonl",
    "blocked rows from G12_CNR_EXACT_BLOCKER_LEDGER_2026-05-08.json"
  ],
  "generated_at_utc": "2026-05-08T01:56:25Z",
  "hidden_path_labels_read": false,
  "input_label_family": "input_only_features_no_labels",
  "label_boundary_note": "Result rows are synthetic tick-path quarantine outputs created in this lane. They are not broker actual-R, account history, live trade results, or validation labels.",
  "live_effect": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "ordered_tick_quotes_used_instead_of_hidden_path_labels": true,
  "outcome_review_opened": false,
  "output_label_family": "synthetic_path_r_quarantined_discovery_only",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "raw_candidate_ltf_path_order_opened": false,
  "result_status": "RESULT_QUARANTINED_DISCOVERY_ONLY",
  "validation_safe": false
}
```
