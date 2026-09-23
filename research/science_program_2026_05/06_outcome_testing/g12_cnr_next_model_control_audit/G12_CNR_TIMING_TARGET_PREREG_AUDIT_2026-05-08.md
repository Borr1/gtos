# G12 CNR Timing Target Prereg Audit - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "G12_CNR_TIMING_TARGET_PREREG_AUDIT",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "control_pack_blockers_crosscheck": [
    {
      "blocker": "No committed source-hashed signal emission logger exists for these rows; preregister field only.",
      "family": "CNR_E2"
    },
    {
      "blocker": "Current OTI8/G12 artifacts have executable quote timestamps but not request/response timestamps or timeout policy ids.",
      "family": "CNR_E3"
    },
    {
      "blocker": "No source-hashed pretouch trigger id, trigger type, distance-to-level rule, or cancellation source is present.",
      "family": "CNR_E4"
    },
    {
      "blocker": "Current CNR rows bind original TP1 only; no source-hashed structural-level rank/source snapshot is available for CNR_T2.",
      "family": "CNR_T2"
    }
  ],
  "databento_calls": 0,
  "date_stamp": "2026-05-08",
  "decision": "ACCEPT_AS_RESEARCH_CONTROL_PREREGISTRATION_WITH_SOURCE_BLOCKERS",
  "family_audits": [
    {
      "audit_reason": "The family is frozen as a future input contract, but current OTI8 rows do not contain the source-hashed fields needed to score it.",
      "decision": "ACCEPT_AS_RESEARCH_PREREGISTRATION_BLOCK_CURRENT_ROWS",
      "exact_blocker": "No committed source-hashed signal emission logger exists for these rows; preregister field only.",
      "family_id": "CNR_E2_SIGNAL_EMITTED_AT_SOURCE",
      "family_type": "timing",
      "forbidden_fields": [
        "terminal_event",
        "synthetic_path_r",
        "broker_actual_r",
        "account_history",
        "live_order_state",
        "hidden_path_label"
      ],
      "required_fields": [
        "signal_emitted_utc",
        "source_id",
        "source_hash",
        "emission_rule_id",
        "source_record_id"
      ],
      "source_state": "BLOCKED_FOR_CURRENT_OTI8_ROWS; current CNR matrix has signal_emitted_utc null."
    },
    {
      "audit_reason": "The family is frozen as a future input contract, but current OTI8 rows do not contain the source-hashed fields needed to score it.",
      "decision": "ACCEPT_AS_RESEARCH_PREREGISTRATION_BLOCK_CURRENT_ROWS",
      "exact_blocker": "Current OTI8/G12 artifacts have executable quote timestamps but not request/response timestamps or timeout policy ids.",
      "family_id": "CNR_E3_DECISION_LATENCY_AWARE",
      "family_type": "timing",
      "forbidden_fields": [
        "terminal_event",
        "synthetic_path_r",
        "broker_actual_r",
        "account_history",
        "live_order_state",
        "hidden_path_label"
      ],
      "required_fields": [
        "decision_request_sent_utc",
        "decision_response_received_utc",
        "latency_ms",
        "latency_policy_id",
        "quote_lookup_policy_id",
        "timeout_behavior"
      ],
      "source_state": "BLOCKED_FOR_CURRENT_OTI8_ROWS; request/response latency timestamps are not present in accepted packets."
    },
    {
      "audit_reason": "The family is frozen as a future input contract, but current OTI8 rows do not contain the source-hashed fields needed to score it.",
      "decision": "ACCEPT_AS_RESEARCH_PREREGISTRATION_BLOCK_CURRENT_ROWS",
      "exact_blocker": "No source-hashed pretouch trigger id, trigger type, distance-to-level rule, or cancellation source is present.",
      "family_id": "CNR_E4_PRETOUCH_TRIGGER",
      "family_type": "timing",
      "forbidden_fields": [
        "terminal_event",
        "synthetic_path_r",
        "broker_actual_r",
        "account_history",
        "live_order_state",
        "hidden_path_label"
      ],
      "required_fields": [
        "pretouch_trigger_id",
        "pretouch_trigger_utc",
        "trigger_type",
        "distance_to_level_rule_id",
        "cancellation_rule_id",
        "source_hash"
      ],
      "source_state": "BLOCKED_FOR_CURRENT_OTI8_ROWS; pretouch trigger source does not exist."
    },
    {
      "audit_reason": "The contract avoids outcome-fit rescue thresholds, but no result lane may score T1 until fixed_r_multiple and stop source are frozen in a packet.",
      "decision": "ACCEPT_AS_RESEARCH_PREREGISTRATION_BLOCK_RESULT_SCORING_UNTIL_FIXED_R_PACKET",
      "exact_blocker": "No result lane may score T1 until fixed_r_multiple and stop source are frozen in a packet.",
      "family_id": "CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE",
      "family_type": "target",
      "price_side_rule": "LONG entry quote uses ask and terminal target/stop uses bid; SHORT entry quote uses bid and terminal target/stop uses ask.",
      "source_asof_fields": [
        "executable_quote_price",
        "executable_quote_side",
        "quote_timestamp_utc",
        "stop_loss",
        "stop_source_hash",
        "fixed_r_multiple",
        "target_price"
      ]
    },
    {
      "audit_reason": "The contract is source-safe, but current CNR rows do not have source-hashed structural-level snapshots or hierarchy/rank fields.",
      "decision": "ACCEPT_AS_RESEARCH_PREREGISTRATION_BLOCK_SOURCE_READINESS",
      "exact_blocker": "Current CNR rows bind original TP1 only; no source-hashed structural-level rank/source snapshot is available for CNR_T2.",
      "family_id": "CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL",
      "family_type": "target",
      "price_side_rule": "same executable/terminal quote-side rule as T1.",
      "source_asof_fields": [
        "structural_level_id",
        "level_price",
        "level_timestamp_utc",
        "level_source_hash",
        "hierarchy_rank",
        "selection_rule_id"
      ]
    },
    {
      "audit_reason": "T3 categorical lifecycle labels were built for the six no-terminal rows without R scoring; validation and promotion remain blocked.",
      "decision": "ACCEPT_RESEARCH_PREREGISTRATION_AND_ACCEPT_SIX_ROW_LIFECYCLE_EVIDENCE_ONLY",
      "exact_blocker": "Promotion/result scoring remains blocked; Workstream C builds only source-hashed labels for the six no-terminal rows.",
      "family_id": "CNR_T3_TERMINAL_TIMEBOX_OR_LIFECYCLE",
      "family_type": "target",
      "price_side_rule": "same terminal quote-side rule as T1 for detecting target/stop event order; labels do not compute R.",
      "source_asof_fields": [
        "timebox_policy_id",
        "path_start_utc",
        "original_horizon_end_utc",
        "extended_horizon_end_utc",
        "path_source_files",
        "path_source_sha256"
      ]
    }
  ],
  "generated_at_utc": "2026-05-08T06:23:47Z",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_account_calls": 0,
  "mt5_order_calls": 0,
  "no_outcome_opening_checks": {
    "outcome_review_opened_false": true,
    "status": "PASS",
    "targets_no_outcomes_scored": true,
    "timing_no_outcomes_scored": true
  },
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "schema_version": "g12_cnr_next_model_control_audit_v1",
  "source_contract_family_check": {
    "status": "PASS",
    "target_family_ids": [
      "CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE",
      "CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL",
      "CNR_T3_TERMINAL_TIMEBOX_OR_LIFECYCLE"
    ],
    "timing_family_ids": [
      "CNR_E2_SIGNAL_EMITTED_AT_SOURCE",
      "CNR_E3_DECISION_LATENCY_AWARE",
      "CNR_E4_PRETOUCH_TRIGGER"
    ]
  },
  "target_family_set_check": {
    "expected": [
      "CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE",
      "CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL",
      "CNR_T3_TERMINAL_TIMEBOX_OR_LIFECYCLE"
    ],
    "observed": [
      "CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE",
      "CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL",
      "CNR_T3_TERMINAL_TIMEBOX_OR_LIFECYCLE"
    ],
    "status": "PASS"
  },
  "timing_family_set_check": {
    "expected": [
      "CNR_E2_SIGNAL_EMITTED_AT_SOURCE",
      "CNR_E3_DECISION_LATENCY_AWARE",
      "CNR_E4_PRETOUCH_TRIGGER"
    ],
    "observed": [
      "CNR_E2_SIGNAL_EMITTED_AT_SOURCE",
      "CNR_E3_DECISION_LATENCY_AWARE",
      "CNR_E4_PRETOUCH_TRIGGER"
    ],
    "status": "PASS"
  },
  "validation_safe": false,
  "what_is_accepted": [
    "E2/E3/E4 are accepted as future input-only timing preregistrations.",
    "T1/T2/T3 are accepted as future input-only target/lifecycle preregistrations.",
    "T3 is additionally accepted as six-row categorical lifecycle evidence only."
  ],
  "what_is_blocked": [
    "E2/E3/E4 current-row scoring remains blocked by missing source-hashed signal, latency, and pretouch fields.",
    "T1 result scoring remains blocked until fixed_r_multiple and stop source are frozen in a source-hashed packet.",
    "T2 result scoring remains blocked until as-of structural level snapshots and selection rules exist.",
    "All validation, promotion, and live-effect interpretations remain blocked."
  ]
}
```
