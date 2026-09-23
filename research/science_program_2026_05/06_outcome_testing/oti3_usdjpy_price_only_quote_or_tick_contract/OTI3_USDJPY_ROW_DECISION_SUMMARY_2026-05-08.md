# OTI3 USDJPY Row Decision Summary - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

```json
{
  "access_request_rows_remaining": [],
  "artifact_family": "OTI3_USDJPY_ROW_DECISION_SUMMARY",
  "blocked_exact_rows": 11,
  "categorical_label_counts": {
    "nofill_terminal_before_entry": 58
  },
  "date_counts": {
    "2026-04-17": 3,
    "2026-04-20": 4,
    "2026-04-30": 20,
    "2026-05-01": 42
  },
  "eligible_contract_evidence_rows": 58,
  "exact_blocker_counts": {
    "BLOCK_OTI3_ENTRY_TOUCH_BEFORE_TERMINAL_SEPARATE_FILL_PATH_CONTRACT_REQUIRED": 7,
    "BLOCK_RESULT_TERMINAL_ORDER_AMBIGUOUS": 4
  },
  "first_event_counts": {
    "entry_touch": 11,
    "terminal_area": 58
  },
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
  "no_r_performance_scoring": true,
  "non_claims": [
    "No R/performance, win-rate, expectancy, DSR/PBO, validation, promotion, or live-effect claim is made.",
    "Entry-first quote/tick evidence is not converted into a performance or broker-fill label."
  ],
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "repo_head": "9cad99c83bc12bf84a569ac82d579aa6ee978dc9",
  "row_count": 69,
  "schema_version": "oti3_usdjpy_price_only_quote_or_tick_contract_v1",
  "scope": "source_correction_or_contract_revision_only",
  "separate_fill_path_rows": [
    "NOFILL-CLOSE-ROW-0129",
    "NOFILL-CLOSE-ROW-0132",
    "NOFILL-CLOSE-ROW-0133",
    "NOFILL-CLOSE-ROW-0163",
    "NOFILL-CLOSE-ROW-0164",
    "NOFILL-CLOSE-ROW-0167",
    "NOFILL-CLOSE-ROW-0168"
  ],
  "validation_safe": false
}
```
