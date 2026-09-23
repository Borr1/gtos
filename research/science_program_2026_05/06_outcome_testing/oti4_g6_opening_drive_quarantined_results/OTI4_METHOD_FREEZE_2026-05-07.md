# OTI4 G6 Opening-Drive Method Freeze - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `False`  
**Outcome review opened:** `False`

```json
{
  "accepted_packet_file": "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-062__G6-EXP-003-OPENING-DRIVE-CONTINUATION__g6_local_ohlc_input_packet_2026-05-07.json",
  "accepted_packet_file_sha256": "fc587c1ffb8452718bc3d00fd8f80bd443b043387b862dce1679944dea3af080",
  "accepted_packet_file_sha256_matches_g12": true,
  "allowed_experiment_id": "G6-EXP-003-OPENING-DRIVE-CONTINUATION",
  "allowed_packet_id": "OTG0-PKT-062",
  "allowed_result_family": "synthetic_path_r_only_if_opening_drive_range_breakout_is_source_complete",
  "artifact_family": "OTI4_G6_OPENING_DRIVE_METHOD_FREEZE",
  "generated_at_utc": "2026-05-07T06:22:18Z",
  "outcome_review_opened": false,
  "prereg_duplicate_policy": "One countable breakout per session/range/symbol/direction; repeated breaks diagnostic only.",
  "prereg_exclusions": [
    "Direct sweep-fade/reversal rows",
    "Rows in excluded XAU 10:30-13:00 UTC expansion cohort unless separately tagged",
    "Rows without as-of range levels",
    "News rows unless news flag is frozen before outcome"
  ],
  "prereg_metric": "Costed continuation expectancy_R by predefined session-window breakout cohort.",
  "prereg_sample_floor": null,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "result_status": "RESULT_QUARANTINED_DISCOVERY_ONLY",
  "scope": "quarantined discovery outcome audit only; no validation, promotion, live behavior, broker actual-R, blocked-packet outcome, live trade result, or raw path-label use",
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
  "strict_countable_rule": [
    "opening_drive_packet.status must be ASOF_OPENING_RANGE_BREAKOUT_READY",
    "range_high, range_low, breakout_close_time, and breakout_side must be present as-of",
    "local OHLC source must contain frozen range bars and path-window bars",
    "duplicate_breakout_key must not be NO_BREAKOUT_ASOF",
    "same-bar terminal order must remain unclaimed or be conservatively bounded"
  ],
  "validation_safe": false
}
```
