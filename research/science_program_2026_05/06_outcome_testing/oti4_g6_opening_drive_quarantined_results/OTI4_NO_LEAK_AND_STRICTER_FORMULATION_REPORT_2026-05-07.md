# OTI4 G6 Opening-Drive No-Leak And Stricter Formulation Report - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `False`  
**Outcome review opened:** `False`

```json
{
  "alternative_stricter_no_leak_formulations": [
    {
      "evidence": "No forbidden result keys in packet records; raw path-label sources skipped.",
      "name": "packet_fields_only_no_raw_path_labels",
      "result": "PASS_WITH_BLOCKER"
    },
    {
      "evidence": "All opening_drive_packet.status values are SOURCE_BLOCKED_NO_RANGE_BARS_ASOF.",
      "name": "source_complete_opening_range_required",
      "result": "FAIL_COUNTABLE_ROWS_ZERO"
    },
    {
      "evidence": "All duplicate_breakout_key values end with NO_BREAKOUT_ASOF.",
      "name": "duplicate_key_must_not_encode_no_breakout",
      "result": "FAIL_COUNTABLE_ROWS_ZERO"
    }
  ],
  "artifact_family": "OTI4_G6_OPENING_DRIVE_NO_LEAK_AND_STRICTER_FORMULATION_REPORT",
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
    "path_order_label",
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
  "forbidden_record_key_hit_count": 0,
  "forbidden_record_key_hits": [],
  "hidden_path_label_search": {
    "ordered_path_source_id_present_rows": 86,
    "raw_candidate_ltf_path_order_opened": false,
    "reason": "Raw path-order logs can contain post-decision terminal labels; OTI4 requires source-complete opening-drive range fields first."
  },
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "skipped_result_or_label_sources": [
    "shadow_logs/broker_actual_r_audit.jsonl",
    "data/account_history/mt5_deals_2026-04-27_2026-05-05.jsonl",
    "shadow_logs/continuation_no_retrace_resolutions.jsonl",
    "shadow_logs/candidate_ltf_path_order.jsonl",
    "shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl",
    "knowledge_base/trade_records/",
    "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/",
    "research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/"
  ],
  "validation_safe": false
}
```
