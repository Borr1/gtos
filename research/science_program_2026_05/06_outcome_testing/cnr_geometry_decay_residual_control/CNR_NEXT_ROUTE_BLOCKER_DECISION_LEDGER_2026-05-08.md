# CNR Next Route Blocker Decision Ledger - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

Future CNR timing/target routes remain closed until exact source/preregistration blockers clear.

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER",
  "blocked_outcome_families_remain_closed": [
    "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK",
    "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW",
    "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER",
    "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY",
    "CNR_T2_ASOF_STRUCTURAL_LEVEL",
    "CNR_T3_TIMEBOX_TERMINAL"
  ],
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "databento_calls": 0,
  "g12_upstream_exact_requirement_counts": {
    "CNR_T1 target contract with frozen fixed-R multiple, stop model, executable entry quote, and source hash before outcome opening": 1550,
    "CNR_T2 structural target contract with as-of level id, level timestamp, parser version, selection rule, and source hash": 1550,
    "CNR_T3 terminal target contract with frozen horizon, terminal pricing source, same-bar/tick ordering policy, and source hash": 1550,
    "decision_request_sent_utc, decision_response_received_utc, latency_ms, and frozen latency policy": 1240,
    "earlier same-day tick/quote coverage for the trigger window; existing local parquet starts after the trigger or has no eligible quote at or before asof_cutoff_utc": 88,
    "input-only invalid-clearing policy for market-entry rows where the source-hashed executable quote is already past the original TP1 before any result audit": 490,
    "local read-only tick parquet or approved source-hashed quote cache for the exact broker symbol/date under approved roots": 24,
    "pre-outcome logger/parser field signal_emitted_utc joined to source_record_id": 1240,
    "pretouch_trigger_id and pretouch_trigger_utc captured as-of before any result path is opened": 1240,
    "source-bound fixed-R target model definition before outcomes": 1550,
    "source-bound structural target level selected as-of before outcomes": 1550,
    "source-bound terminal timebox policy before outcomes": 1550,
    "source-hashed decision request/response timestamps and frozen latency policy for this source_record_id": 1240,
    "source-hashed executable bid/ask/spread quote at or before the timing trigger for the packet symbol/date, with quote_timestamp_utc and source_sha256": 112,
    "source-hashed pretouch trigger id/utc captured before any outcome path review": 1240,
    "source-hashed signal_emitted_utc materialized for this source_record_id": 1240,
    "source-hashed timing trigger field materialized before outcome opening; CNR_E2 needs signal_emitted_utc, CNR_E3 needs request/response latency clock fields, and CNR_E4 needs pretouch_trigger_id/pretouch_trigger_utc": 3720
  },
  "generated_at_utc": "2026-05-08T03:35:19Z",
  "live_effect": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "next_route_decisions": [
    {
      "decision": "BLOCKED_SOURCE_FIELD_ABSENT",
      "next_unblocker": "pre-outcome signal_emitted_utc logger/parser field joined to source_record_id with source hash and no-lookahead test",
      "route": "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK"
    },
    {
      "decision": "BLOCKED_SOURCE_FIELD_ABSENT",
      "next_unblocker": "decision_request_sent_utc, decision_response_received_utc, latency_ms, latency_policy_id, and frozen quote-selection rule",
      "route": "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW"
    },
    {
      "decision": "BLOCKED_SOURCE_FIELD_ABSENT",
      "next_unblocker": "pretouch_trigger_id and pretouch_trigger_utc captured as-of before any result path is opened; cannot infer from later path",
      "route": "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER"
    },
    {
      "decision": "BLOCKED_TARGET_CONTRACT_ABSENT",
      "next_unblocker": "fixed-R multiple, stop model, executable quote binding, source hash, and sample floor frozen before outcomes",
      "route": "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY"
    },
    {
      "decision": "BLOCKED_TARGET_CONTRACT_ABSENT",
      "next_unblocker": "as-of structural level id, timestamp, parser version, selection rule, quote side, and source hash frozen before outcomes",
      "route": "CNR_T2_ASOF_STRUCTURAL_LEVEL"
    },
    {
      "decision": "BLOCKED_TARGET_CONTRACT_ABSENT",
      "next_unblocker": "terminal timebox horizon, terminal pricing source, quote side, same-bar/tick ordering policy, and source hash frozen before outcomes",
      "route": "CNR_T3_TIMEBOX_TERMINAL"
    },
    {
      "decision": "PARTIAL_SOURCE_SAFE_SIDECAR_FOUND_NOT_G12_READY",
      "next_unblocker": "unified input-only geometry+horizon sidecar packet and G12 audit before any CNR result scoring",
      "route": "OTG0-PKT-061_GEOMETRY_HORIZON_REBUILD"
    }
  ],
  "order_calls": 0,
  "otg0_pkt061_geometry_horizon_sidecar_findings": {
    "exact_next_blocker": "Build a unified input-only OTG0-PKT-061 geometry+horizon sidecar that joins source-field original geometry with source-hashed quote/path_start/path_end packets, then send that sidecar through G12 source/no-leak/duplicate audit before any result scoring.",
    "otr061_single_xau_recovery_record_count": 1,
    "otr061_single_xau_terminal_state": "RECOVERY_PACKET_READY_FOR_G12_REAUDIT",
    "otx_pkt061_proposal_rows": 51,
    "otx_pkt061_rows_with_decision_quote": 50,
    "otx_pkt061_rows_with_entry_sl_tp_or_level_packet": 0,
    "otx_pkt061_rows_with_ordered_path": 50,
    "source_field_pkt061_ready_rows": 8,
    "source_field_pkt061_rows_with_original_geometry": 8,
    "source_field_pkt061_status": "SOURCE_FIELD_GEOMETRY_EXISTS_FOR_ACCEPTED_E0_E1_T0_ROWS",
    "source_field_pkt061_unique_duplicate_groups": 2
  },
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_blocker_summary_from_source_rows": {
    "target_family_blockers": {
      "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY": {
        "ready_rows": 0,
        "row_count": 1550,
        "target_binding_status_counts": {
          "BLOCKED_TARGET_MODEL_NOT_PREBOUND_FOR_THIS_PACKET": 1550
        },
        "target_blocker_counts": {
          "requires frozen R multiple, stop model, and executable quote binding before outcome opening": 1550
        }
      },
      "CNR_T2_ASOF_STRUCTURAL_LEVEL": {
        "ready_rows": 0,
        "row_count": 1550,
        "target_binding_status_counts": {
          "BLOCKED_STRUCTURED_ASOF_LEVEL_SOURCE_NOT_BOUND": 1550
        },
        "target_blocker_counts": {
          "requires structured level id/timestamp/parser/source hash selected before outcomes": 1550
        }
      },
      "CNR_T3_TIMEBOX_TERMINAL": {
        "ready_rows": 0,
        "row_count": 1550,
        "target_binding_status_counts": {
          "BLOCKED_TERMINAL_TIMEBOX_POLICY_NOT_BOUND": 1550
        },
        "target_blocker_counts": {
          "requires terminal pricing, timebox horizon, and same-bar/tick ordering policy before outcomes": 1550
        }
      }
    },
    "timing_family_blockers": {
      "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK": {
        "non_null_signal_emitted_utc_rows": 0,
        "ready_rows": 0,
        "row_count": 1240,
        "timing_blocker_counts": {
          "source-hashed signal_emitted_utc logger field is absent from current approved packet sources": 1240
        },
        "timing_source_status_counts": {
          "BLOCKED_MISSING_SIGNAL_EMITTED_UTC": 1240
        }
      },
      "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW": {
        "non_null_signal_emitted_utc_rows": 0,
        "ready_rows": 0,
        "row_count": 1240,
        "timing_blocker_counts": {
          "decision_request_sent_utc/response_received_utc and latency policy are not bound in source packet": 1240
        },
        "timing_source_status_counts": {
          "BLOCKED_MISSING_LATENCY_CLOCK_CHAIN": 1240
        }
      },
      "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER": {
        "non_null_signal_emitted_utc_rows": 0,
        "ready_rows": 0,
        "row_count": 1240,
        "timing_blocker_counts": {
          "pretouch_trigger_id/pretouch_trigger_utc source-safe logger is absent; cannot infer from later path": 1240
        },
        "timing_source_status_counts": {
          "BLOCKED_MISSING_PRETOUCH_TRIGGER": 1240
        }
      }
    }
  },
  "validation_safe": false
}
```
