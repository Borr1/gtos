# CNR E2 E3 E4 Timing Preregistration - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_E2_E3_E4_TIMING_PREREGISTRATION",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-08",
  "families": {
    "CNR_E2_SIGNAL_EMITTED_AT_SOURCE": {
      "allowed_source_roots_parsers": [
        "future source-hashed signal/candidate logger JSONL",
        "CNR_SOURCE_FIELD_PACKET_ROWS only if signal_emitted_utc is non-null and source-hashed"
      ],
      "duplicate_policy": "duplicate_denominator_key must include timing family; duplicate groups cannot be joined by group alone.",
      "exact_blocker": "No committed source-hashed signal emission logger exists for these rows; preregister field only.",
      "forbidden_fields": [
        "terminal_event",
        "synthetic_path_r",
        "broker_actual_r",
        "account_history",
        "live_order_state",
        "hidden_path_label"
      ],
      "legal_source_state": "BLOCKED_FOR_CURRENT_OTI8_ROWS; current CNR matrix has signal_emitted_utc null.",
      "no_lookahead_asof_rule": "signal_emitted_utc must be emitted by the source logger no later than the decision-as-of timestamp and hashed before terminal path opening.",
      "required_fields": [
        "signal_emitted_utc",
        "source_id",
        "source_hash",
        "emission_rule_id",
        "source_record_id"
      ],
      "sample_floor": ">=30 countable duplicate groups per timing-target family and effective_N>=3 before validation-style diagnostics."
    },
    "CNR_E3_DECISION_LATENCY_AWARE": {
      "allowed_source_roots_parsers": [
        "future decision-latency audit JSONL",
        "source-hashed analyzer request ledger if added as shadow-only telemetry"
      ],
      "duplicate_policy": "same candidate may produce separate E3 rows only when latency_policy_id differs and is preregistered.",
      "exact_blocker": "Current OTI8/G12 artifacts have executable quote timestamps but not request/response timestamps or timeout policy ids.",
      "forbidden_fields": [
        "terminal_event",
        "synthetic_path_r",
        "broker_actual_r",
        "account_history",
        "live_order_state",
        "hidden_path_label"
      ],
      "legal_source_state": "BLOCKED_FOR_CURRENT_OTI8_ROWS; request/response latency timestamps are not present in accepted packets.",
      "no_lookahead_asof_rule": "latency fields must be logged by the decision client before any path/result source is opened; quote lookup must be bound to the response timestamp policy.",
      "required_fields": [
        "decision_request_sent_utc",
        "decision_response_received_utc",
        "latency_ms",
        "latency_policy_id",
        "quote_lookup_policy_id",
        "timeout_behavior"
      ],
      "sample_floor": ">=30 countable duplicate groups per latency policy plus DSR/PBO/effective-N diagnostics in a separate result lane."
    },
    "CNR_E4_PRETOUCH_TRIGGER": {
      "allowed_source_roots_parsers": [
        "future pretouch shadow logger JSONL",
        "source-hashed tick/quote proximity parser with frozen trigger distance rule"
      ],
      "duplicate_policy": "pretouch_trigger_id is unique; repeated triggers for the same duplicate group are context rows unless a preregistered denominator key says otherwise.",
      "exact_blocker": "No source-hashed pretouch trigger id, trigger type, distance-to-level rule, or cancellation source is present.",
      "forbidden_fields": [
        "terminal_event",
        "synthetic_path_r",
        "broker_actual_r",
        "account_history",
        "live_order_state",
        "hidden_path_label"
      ],
      "legal_source_state": "BLOCKED_FOR_CURRENT_OTI8_ROWS; pretouch trigger source does not exist.",
      "no_lookahead_asof_rule": "trigger must be emitted before first touch of the level and before terminal path opening; cancellation must be logged from pre-touch state only.",
      "required_fields": [
        "pretouch_trigger_id",
        "pretouch_trigger_utc",
        "trigger_type",
        "distance_to_level_rule_id",
        "cancellation_rule_id",
        "source_hash"
      ],
      "sample_floor": ">=30 countable duplicate groups per trigger type; no promotion from input packet counts."
    }
  },
  "generated_at_utc": "2026-05-08T06:01:13Z",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_account_calls": 0,
  "mt5_order_calls": 0,
  "no_outcomes_scored": true,
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "schema_version": "cnr_next_model_control_pack_v1",
  "status": "INPUT_ONLY_PREREGISTERED_CURRENT_ROWS_BLOCKED_FOR_E2_E3_E4_FIELDS",
  "validation_safe": false
}
```
