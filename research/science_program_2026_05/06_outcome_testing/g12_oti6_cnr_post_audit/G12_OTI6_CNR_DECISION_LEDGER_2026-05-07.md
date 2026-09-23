# G12 OTI6 CNR Decision Ledger - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

- Terminal decision: `ACCEPT_AS_QUARANTINED_TARGET_ALREADY_PASSED_DISCOVERY_EVIDENCE`.
- Accepted as quarantined target-already-passed discovery/impossibility evidence only.

```json
{
  "acceptance_scope": "Quarantined discovery/impossibility evidence only; not validation, not promotion, not live logic.",
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "G12_OTI6_CNR_DECISION_LEDGER",
  "audit_verdict": "PASS_ACCEPT_TARGET_ALREADY_PASSED_RESULT_AS_QUARANTINED_DISCOVERY_EVIDENCE",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-07",
  "decision_options": {
    "accepted": "ACCEPT_AS_QUARANTINED_TARGET_ALREADY_PASSED_DISCOVERY_EVIDENCE",
    "blocked": "BLOCKED_WITH_EXACT_NEXT_QUESTION",
    "rejected": "REJECT_INVALID_RESULT_IMPLEMENTATION"
  },
  "generated_at_utc": "2026-05-07T10:47:40Z",
  "git_head_at_build": "16713c77 docs: refresh research state for g12 oti6 prompt",
  "global_boundaries": {
    "live_effect": false,
    "no_live_surface_edits": true,
    "no_new_outcome_scoring": true,
    "no_paid_api_databento": true,
    "no_promotion_or_validation_meaning": true,
    "outcome_review_opened": false,
    "validation_safe": false
  },
  "key_verified_claims": [
    {
      "claim": "terminal_status",
      "expected": "RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION",
      "observed": "RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION",
      "status": "PASS"
    },
    {
      "claim": "entry_model",
      "expected": "CNR_E0_DECISION_CLOSE_MARKET",
      "observed": "CNR_E0_DECISION_CLOSE_MARKET",
      "status": "PASS"
    },
    {
      "claim": "decision_quote_timestamp_utc",
      "expected": "2026-05-06T07:14:59.889000Z",
      "observed": "2026-05-06T07:14:59.889000Z",
      "status": "PASS"
    },
    {
      "claim": "decision_bid",
      "expected": 4647.65,
      "observed": 4647.65,
      "status": "PASS"
    },
    {
      "claim": "decision_ask",
      "expected": 4648.29,
      "observed": 4648.29,
      "status": "PASS"
    },
    {
      "claim": "original_entry_price",
      "expected": 4561.52,
      "observed": 4561.52,
      "status": "PASS"
    },
    {
      "claim": "original_stop_loss",
      "expected": 4547.35,
      "observed": 4547.35,
      "status": "PASS"
    },
    {
      "claim": "original_take_profit_1",
      "expected": 4582.77,
      "observed": 4582.77,
      "status": "PASS"
    },
    {
      "claim": "base_r_price",
      "expected": 14.17,
      "observed": 14.17,
      "status": "PASS"
    },
    {
      "claim": "target_gap_price",
      "expected": 65.52,
      "observed": 65.52,
      "status": "PASS"
    },
    {
      "claim": "target_gap_r",
      "expected": 4.62385321,
      "observed": 4.62385321,
      "status": "PASS"
    },
    {
      "claim": "synthetic_path_r",
      "expected": null,
      "observed": null,
      "status": "PASS"
    },
    {
      "claim": "r_scoring_attempted",
      "expected": false,
      "observed": false,
      "status": "PASS"
    },
    {
      "claim": "r_block_reason",
      "expected": "LONG executable ask is above original TP1 before CNR_E0 can enter.",
      "observed": "LONG executable ask is above original TP1 before CNR_E0 can enter.",
      "status": "PASS"
    },
    {
      "claim": "first_ordered_path_ask",
      "expected": 4648.31,
      "observed": 4648.31,
      "status": "PASS"
    },
    {
      "claim": "first_ordered_path_bid",
      "expected": 4647.67,
      "observed": 4647.67,
      "status": "PASS"
    },
    {
      "claim": "last_ordered_path_ask",
      "expected": 4680.18,
      "observed": 4680.18,
      "status": "PASS"
    },
    {
      "claim": "last_ordered_path_bid",
      "expected": 4679.63,
      "observed": 4679.63,
      "status": "PASS"
    }
  ],
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "not_rejected_because": "Null synthetic R is the correct output for preregistered target-already-passed geometry; scoring it as a win/loss would be the implementation error.",
  "not_rejected_for": [
    "synthetic_path_r is null",
    "the result is non-promotable",
    "the recovered post-decision path continued upward"
  ],
  "objective_restated": "Run the G12 post-audit over OTI6 and decide whether the OTI6 target-already-passed terminal result is accepted, rejected, or blocked.",
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "rationale": [
    "OTI6 preserved source/hash/no-leak/duplicate/label controls and did not open forbidden live or broker-result sources.",
    "The preregistered CNR_E0 LONG market entry uses the decision ask, and that ask was already above original TP1 before CNR_E0 could enter.",
    "OTI6 correctly left synthetic_path_r null because the geometry gate failed before path scoring.",
    "The row is useful evidence that the original no-retrace continuation had already delivered before the decision-close market-entry model was eligible."
  ],
  "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
  "target_result_lane": "OTI6_OTR061_CNR_QUARANTINED_RESULT",
  "terminal_g12_decision": "ACCEPT_AS_QUARANTINED_TARGET_ALREADY_PASSED_DISCOVERY_EVIDENCE",
  "terminal_status": "RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION",
  "validation_safe": false
}
```
