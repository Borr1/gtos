# G12 G3 G6 Leakage Noleak Review 2026-05-07 - 2026-05-07

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `False`
Outcome review opened: `False`

```json
{
  "allowed_control_keys": [
    "blocked_packet_outcomes_inspected",
    "blocked_packet_outcomes_not_opened",
    "broker_actual_r_absent_from_primary_metric",
    "broker_actual_r_inspected",
    "c_gate_result",
    "label_values_absent",
    "no_outcome_columns_in_records",
    "no_result_columns_in_records",
    "outcome_review_opened",
    "outcome_scoring_run",
    "result_or_quarantine_outputs_created"
  ],
  "artifact_family": "G12_G3_G6_LEAKAGE_NOLEAK_REVIEW",
  "audit_scope": "packet records plus top-level safety flags; forbidden result/account-history/resolution sources are not opened",
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
    "realized_r",
    "resolution",
    "resolved",
    "result",
    "sl_first_touch",
    "synthetic_path",
    "terminal_order",
    "touch_sequence",
    "tp1_first_touch",
    "trade_result",
    "win_loss"
  ],
  "outcome_review_opened": false,
  "packet_rows": [
    {
      "forbidden_record_key_hit_count": 0,
      "forbidden_record_key_hits": [],
      "packet_id": "OTG0-PKT-031",
      "record_count": 95,
      "top_level_safety_flags": {
        "blocked_packet_outcomes_inspected": null,
        "broker_actual_r_inspected": null,
        "outcome_review_opened": false,
        "outcome_scoring_run": null,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "result_or_quarantine_outputs_created": null,
        "validation_safe": false
      }
    },
    {
      "forbidden_record_key_hit_count": 0,
      "forbidden_record_key_hits": [],
      "packet_id": "OTG0-PKT-032",
      "record_count": 8,
      "top_level_safety_flags": {
        "blocked_packet_outcomes_inspected": null,
        "broker_actual_r_inspected": null,
        "outcome_review_opened": false,
        "outcome_scoring_run": null,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "result_or_quarantine_outputs_created": null,
        "validation_safe": false
      }
    },
    {
      "forbidden_record_key_hit_count": 0,
      "forbidden_record_key_hits": [],
      "packet_id": "OTG0-PKT-036",
      "record_count": 96,
      "top_level_safety_flags": {
        "blocked_packet_outcomes_inspected": null,
        "broker_actual_r_inspected": null,
        "outcome_review_opened": false,
        "outcome_scoring_run": null,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "result_or_quarantine_outputs_created": null,
        "validation_safe": false
      }
    },
    {
      "forbidden_record_key_hit_count": 0,
      "forbidden_record_key_hits": [],
      "packet_id": "OTG0-PKT-060",
      "record_count": 80,
      "top_level_safety_flags": {
        "blocked_packet_outcomes_inspected": false,
        "broker_actual_r_inspected": false,
        "outcome_review_opened": false,
        "outcome_scoring_run": false,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "result_or_quarantine_outputs_created": false,
        "validation_safe": false
      }
    },
    {
      "forbidden_record_key_hit_count": 0,
      "forbidden_record_key_hits": [],
      "packet_id": "OTG0-PKT-061",
      "record_count": 51,
      "top_level_safety_flags": {
        "blocked_packet_outcomes_inspected": false,
        "broker_actual_r_inspected": false,
        "outcome_review_opened": false,
        "outcome_scoring_run": false,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "result_or_quarantine_outputs_created": false,
        "validation_safe": false
      }
    },
    {
      "forbidden_record_key_hit_count": 0,
      "forbidden_record_key_hits": [],
      "packet_id": "OTG0-PKT-062",
      "record_count": 86,
      "top_level_safety_flags": {
        "blocked_packet_outcomes_inspected": false,
        "broker_actual_r_inspected": false,
        "outcome_review_opened": false,
        "outcome_scoring_run": false,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "result_or_quarantine_outputs_created": false,
        "validation_safe": false
      }
    },
    {
      "forbidden_record_key_hit_count": 0,
      "forbidden_record_key_hits": [],
      "packet_id": "OTG0-PKT-063",
      "record_count": 86,
      "top_level_safety_flags": {
        "blocked_packet_outcomes_inspected": false,
        "broker_actual_r_inspected": false,
        "outcome_review_opened": false,
        "outcome_scoring_run": false,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "result_or_quarantine_outputs_created": false,
        "validation_safe": false
      }
    },
    {
      "forbidden_record_key_hit_count": 0,
      "forbidden_record_key_hits": [],
      "packet_id": "OTG0-PKT-066",
      "record_count": 7,
      "top_level_safety_flags": {
        "blocked_packet_outcomes_inspected": false,
        "broker_actual_r_inspected": false,
        "outcome_review_opened": false,
        "outcome_scoring_run": false,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "result_or_quarantine_outputs_created": false,
        "validation_safe": false
      }
    }
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "red_team_finding": "No forbidden record keys were found under the stricter scan if total_forbidden_record_key_hits remains zero. TP fields are allowed only as input geometry.",
  "skipped_by_policy_sources": [
    "shadow_logs/broker_actual_r_audit.jsonl",
    "data/account_history/mt5_deals_2026-04-27_2026-05-05.jsonl",
    "shadow_logs/continuation_no_retrace_resolutions.jsonl",
    "shadow_logs/m15_choch_diagnostic_audit.jsonl",
    "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/",
    "research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/",
    "research/science_program_2026_05/06_outcome_testing/outcome_review/"
  ],
  "total_forbidden_record_key_hits": 0,
  "validation_safe": false
}
```
