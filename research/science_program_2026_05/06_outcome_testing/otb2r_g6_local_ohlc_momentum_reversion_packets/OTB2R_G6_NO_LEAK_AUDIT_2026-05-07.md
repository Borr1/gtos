# OTB2R G6 No-Leak Audit - 2026-05-07

Promotion posture: `NO_PROMOTION_VERDICT`

```json

{
  "allowed_control_keys": [
    "blocked_packet_outcomes_inspected",
    "broker_actual_r_inspected",
    "declared_future_label_family",
    "outcome_review_opened",
    "outcome_scoring_run",
    "promotion_verdict",
    "result_or_quarantine_outputs_created"
  ],
  "artifact_family": "OTB2R_G6_NO_LEAK_AUDIT",
  "audit_scope": "packet records only; top-level control flags are separately allowed",
  "forbidden_key_fragments": [
    "actual_r",
    "broker_actual",
    "close_fill",
    "entry_first_touch",
    "final_outcome",
    "gross_r",
    "hit_sl",
    "hit_tp",
    "mae",
    "mfe",
    "net_r",
    "outcome",
    "path_label",
    "path_outcome",
    "pnl",
    "profit",
    "realized_r",
    "result",
    "sl_first_touch",
    "synthetic_path",
    "tp1_first_touch",
    "trade_result",
    "win_loss"
  ],
  "outcome_review_opened": false,
  "packets": [
    {
      "forbidden_record_key_hit_count": 0,
      "forbidden_record_key_hits": [],
      "packet_id": "OTG0-PKT-060",
      "record_count": 80
    },
    {
      "forbidden_record_key_hit_count": 0,
      "forbidden_record_key_hits": [],
      "packet_id": "OTG0-PKT-061",
      "record_count": 51
    },
    {
      "forbidden_record_key_hit_count": 0,
      "forbidden_record_key_hits": [],
      "packet_id": "OTG0-PKT-062",
      "record_count": 86
    },
    {
      "forbidden_record_key_hit_count": 0,
      "forbidden_record_key_hits": [],
      "packet_id": "OTG0-PKT-063",
      "record_count": 86
    },
    {
      "forbidden_record_key_hit_count": 0,
      "forbidden_record_key_hits": [],
      "packet_id": "OTG0-PKT-066",
      "record_count": 7
    }
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "skipped_result_sources_by_policy": [
    "shadow_logs/continuation_no_retrace_resolutions.jsonl",
    "shadow_logs/m15_choch_diagnostic_audit.jsonl",
    "shadow_logs/broker_actual_r_audit.jsonl",
    "data/account_history/mt5_deals_2026-04-27_2026-05-05.jsonl"
  ],
  "total_forbidden_record_key_hits": 0,
  "validation_safe": false
}

```
