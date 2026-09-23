# CNR Source Field Multitimeframe Evidence Map - 2026-05-07

Promotion verdict: `NO_PROMOTION_VERDICT`  
Validation safe: `false`  
Outcome review opened: `false`  
Live effect: `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_SOURCE_FIELD_MULTITIMEFRAME_EVIDENCE_MAP",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "evidence_status_by_timeframe": {
    "H1": "PARTIAL_OB_STRUCTURE_WHERE_PACKET_FAMILY_SUPPLIES_IT",
    "M15": "SOURCE_PACKET_FIELDS_PRESENT",
    "M1_M5_H4_D1": "SOURCE_ROOTS_SEARCHED; not used as outcome/path fields in this input builder",
    "tick_or_quote": {
      "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE": 112,
      "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED": 3720,
      "QUOTE_EXTRACTED_SOURCE_HASHED": 2368
    }
  },
  "generated_at_utc": "2026-05-07T16:38:18Z",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "timeframe_roles": {
    "D1": "context role only; no structured per-row D1 field in current input packet",
    "H1": "OB/structure bounds only when structured in input packet; otherwise blocked",
    "H4": "context role only; no structured per-row H4 field in current input packet",
    "M1": "available in approved local roots but not consumed for post-decision path or outcome scoring in this builder",
    "M15": "source packet decision close, candidate id, local OHLC/g6 feature fields where present",
    "M5": "available in approved local roots but not consumed for post-decision path or outcome scoring in this builder",
    "session": "session label from source packet",
    "tick_or_quote": "decision-time executable bid/ask/spread; extracted only from source-hashed parquet where trigger exists"
  },
  "validation_safe": false
}
```
