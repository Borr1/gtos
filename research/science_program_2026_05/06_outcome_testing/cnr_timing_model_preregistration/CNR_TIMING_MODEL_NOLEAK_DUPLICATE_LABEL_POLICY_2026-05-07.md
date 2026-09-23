# CNR Timing Model Noleak Duplicate Label Policy - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_TIMING_MODEL_NOLEAK_DUPLICATE_LABEL_POLICY",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-07",
  "duplicate_denominator_policy": {
    "pretouch_extension_denominator": "G6_CNR|symbol|trade_date|session|side|original_entry_price|pretouch_trigger_id",
    "primary_denominator": "G6_CNR|symbol|trade_date|session|side|original_entry_price",
    "rule": "Only one primary countable row per denominator per model family and target model. Duplicate rows can exist for context or source coverage but do not add effective N."
  },
  "generated_at_utc": "2026-05-07T11:29:43Z",
  "git_branch_at_build": "cnr-timing-model-preregistration",
  "git_head_at_build": "6aa3d07a docs: refresh research state after cnr small-n mandate",
  "label_family_policy": {
    "broker_actual_r": "forbidden in this lane and not interchangeable with synthetic path labels",
    "input_only_features_no_labels": "allowed for packet construction and preregistration",
    "lifecycle_no_fill": "context-only unless a lifecycle lane explicitly opens that label family",
    "synthetic_path_r_quarantined_discovery": "allowed only in explicitly opened quarantined result lanes, never for this preregistration lane"
  },
  "lane_id": "CNR_TIMING_MODEL_PREREGISTRATION",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "no_leak_controls": [
    "model family and target model must be selected before outcome path fields are opened",
    "target-already-passed gate must run before R scoring",
    "post-decision path can verify terminal ordering only after G12/G0 packet audit opens a result lane",
    "source hashes and parser versions must be recorded before outcome opening",
    "same-bar ambiguity must be classified or bounded rather than guessed"
  ],
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "policy_verdict": "FROZEN_NOLEAK_DUPLICATE_POLICY_READY_FOR_G12_G0_PACKET_AUDIT",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
  "validation_safe": false
}
```
