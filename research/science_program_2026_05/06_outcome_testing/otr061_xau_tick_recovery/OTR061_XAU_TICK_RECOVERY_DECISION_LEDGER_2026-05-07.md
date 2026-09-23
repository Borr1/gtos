# OTR061 XAU Tick Recovery Decision Ledger

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

- This is a data-recovery/source-proof decision only.
- No outcome scoring or promotion verdict is opened.

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "OTR061_XAU_TICK_RECOVERY_DECISION_LEDGER",
  "broker_actual_r_accessed": false,
  "databento_calls": 0,
  "date_stamp": "2026-05-07",
  "experiment_id": "G6-EXP-002-CONTINUATION-NO-RETRACE",
  "forbidden_surfaces_assertion": {
    "account_history_accessed": false,
    "blocked_packet_outcomes_opened": false,
    "broker_actual_r_accessed": false,
    "live_order_state_accessed": false,
    "orders_or_positions_read": false,
    "orders_placed": false,
    "paid_api_or_databento_called": false
  },
  "generated_at_utc": "2026-05-07T09:15:22Z",
  "live_effect": false,
  "live_order_state_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "packet_proposal_emitted": true,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "recovery_decision": {
    "absolute_tick_source_status": "ZERO_OR_INSUFFICIENT_REQUIRED_WINDOW_ROWS",
    "final_blocker": null,
    "known_g12_file_rechecked": true,
    "mt5_read_only_status": "RECOVERED_ROWS_FROM_READ_ONLY_MT5",
    "next_unblocker": "External G12 re-audit of source-hashed packet proposal.",
    "sierra_futures_proxy_status": "LOCAL_PROXY_EXISTS_BUT_NOT_SAME_MARKET_XAUUSD_BROKER_QUOTE_TRUTH",
    "sierra_same_market_status": "NO_ROWS_IN_REQUIRED_WINDOW"
  },
  "repo_head": "ee34bc50c8f1326ccbf697c9bee4e96171b1e433",
  "required_window_utc": {
    "decision_asof": "2026-05-06T07:15:00+00:00",
    "end": "2026-05-06T11:15:00+00:00",
    "start": "2026-05-06T07:10:00+00:00"
  },
  "source_hash_verdict": "PASS_ALL_EXISTING_USED_SOURCES_HASHED",
  "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
  "target_symbol": "XAUUSD",
  "terminal_state": "RECOVERY_PACKET_READY_FOR_G12_REAUDIT",
  "validation_safe": false,
  "vendor_or_access_manifest_emitted": false
}
```
