# OTI3 USDJPY Quote Tick Contract - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

```json
{
  "allowed_labels": [
    "nofill_terminal_before_entry"
  ],
  "artifact_family": "OTI3_USDJPY_QUOTE_TICK_CONTRACT_PACKET",
  "blocked_or_separate_family_evidence": {
    "entry_touch_before_terminal": "quote/tick evidence belongs to separate fill/path contract; no no-fill lifecycle label assigned here",
    "missing_tick_source": "exact access/source request required",
    "protective_touch_before_terminal": "unsupported no-fill label family under frozen contract"
  },
  "contract_status": "ROW_LEVEL_EVIDENCE_OR_EXACT_BLOCKERS_EMITTED",
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
  "label_family_boundary": "categorical_lifecycle_only; no R/performance/broker/account/live/order labels",
  "lane_id": "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT",
  "live_effect": false,
  "no_r_performance_scoring": true,
  "outcome_review_opened": false,
  "parser_contract": {
    "long": {
      "entry_touch": "ask <= entry_price",
      "protective_touch": "bid <= protective_level_price",
      "terminal_area_touch": "bid >= terminal_area_price"
    },
    "no_event_policy": "block unless a frozen observation horizon is present in the source row",
    "parser_id": "bid_ask_side_aware_touch_times_v1",
    "same_timestamp_policy": "block as BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS",
    "short": {
      "entry_touch": "bid >= entry_price",
      "protective_touch": "ask >= protective_level_price",
      "terminal_area_touch": "ask <= terminal_area_price"
    }
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "repo_head": "9cad99c83bc12bf84a569ac82d579aa6ee978dc9",
  "row_count": 69,
  "schema_version": "oti3_usdjpy_price_only_quote_or_tick_contract_v1",
  "scope": "source_correction_or_contract_revision_only",
  "validation_safe": false
}
```
