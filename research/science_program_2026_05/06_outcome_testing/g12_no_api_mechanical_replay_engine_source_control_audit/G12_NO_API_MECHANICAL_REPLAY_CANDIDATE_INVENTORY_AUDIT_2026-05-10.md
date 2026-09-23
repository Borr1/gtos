# Candidate Inventory Audit

- status=PASS
- promotion_verdict=NO_PROMOTION_VERDICT
- validation_safe=false outcome_review_opened=false live_effect=false

```json
{
  "artifact_family": "candidate_inventory_audit",
  "candidate_dimension_sums": {
    "by_family": 12852758,
    "by_regime_phase": 12852758,
    "by_session_or_kill_zone": 12852758,
    "by_source_family": 12852758,
    "by_symbol": 12852758,
    "by_timeframe": 12852758
  },
  "candidate_row_count_raw_attempts": 13540033,
  "candidate_rows_suppressed_by_artifact_cap": 12732758,
  "candidate_rows_written_recomputed": 120000,
  "candidate_rows_written_reported": 120000,
  "cap_policy_preserves_full_count": true,
  "changes_live_trading_behavior": false,
  "compact_duplicate_key_duplicate_count": 0,
  "compact_family_sample_counts": {
    "adjacent_range_compression_breakout": 4984,
    "baseline_mean_reversion": 9859,
    "baseline_momentum_continuation": 17333,
    "baseline_random_session_control": 3359,
    "baseline_shifted_entry_control": 23665,
    "breaker_re_entry": 171,
    "fvg_fill": 12231,
    "liquidity_stop_run_context": 28876,
    "ob_retest": 14096,
    "opening_drive_no_fill_lifecycle": 3122,
    "session_kz_sweep": 2304
  },
  "credentials_touched": false,
  "dimension_sums_equal_unique_candidate_denominator": true,
  "duplicate_candidate_keys_reported": 687275,
  "evidence_class": "G12_SOURCE_CONTROL_AUDIT_ONLY",
  "forbidden_field_samples": [],
  "generated_at_utc": "2026-05-10T21:10:22+00:00",
  "issues": [],
  "live_effect": false,
  "missing_required_field_samples": [],
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_NO_API_MECHANICAL_REPLAY_ENGINE_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_no_api_mechanical_replay_source_control_audit_v1",
  "source_progress_final_candidate_count": 13540033,
  "source_progress_final_candidate_rows_written": 120000,
  "source_progress_rows": 365,
  "status": "PASS",
  "unique_candidate_denominator": 12852758,
  "validation_safe": false
}
```
