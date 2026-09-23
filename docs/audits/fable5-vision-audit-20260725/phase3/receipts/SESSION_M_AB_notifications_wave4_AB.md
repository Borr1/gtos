# Session M batch 3 A/B — F30/Q7 notification suppression + wave4 skip-with-reason

**16 bad → 4 bad · 12 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `8ed443982` | `7feabae2a` |
| captured (UTC) | 2026-07-26T21:48:03Z | 2026-07-26T21:48:23Z |
| working tree | dirty | dirty |
| failed | 16 | 4 |
| errored | 0 | 0 |
| **bad** | **16** | **4** |
| passed | 202 | 202 |
| skipped | 0 | 3 |

## Fixed (12)

- `tests/test_wave4a_digital_twin_historical_microscope.py::test_wave4a_asof_event_excludes_path_and_result_labels`
- `tests/test_wave4a_digital_twin_historical_microscope.py::test_wave4a_build_and_verify_temp_route`
- `tests/test_wave4a_digital_twin_historical_microscope.py::test_wave4a_loser_mfe_coverage_preserves_source_gaps`
- `tests/test_wave4a_digital_twin_historical_microscope.py::test_wave4a_material_source_contract_preserves_all_rows`
- `tests/test_wave4b_feature_store_v2.py::test_wave4b_build_and_verify_temp_route`
- `tests/test_wave4b_feature_store_v2.py::test_wave4b_builds_one_feature_row_per_wave4a_canonical_row`
- `tests/test_wave4b_feature_store_v2.py::test_wave4b_feature_values_exclude_forbidden_label_tokens`
- `tests/test_wave4b_feature_store_v2.py::test_wave4b_probability_and_confluence_gaps_are_explicit`
- `tests/test_wave4c_label_store_v2.py::test_wave4c_builds_full_row_label_ledgers_in_temp_route`
- `tests/test_wave4c_label_store_v2.py::test_wave4c_evidence_classes_keep_cash_and_r_separate`
- `tests/test_wave4c_label_store_v2.py::test_wave4c_labels_are_banned_from_feature_store_inputs`
- `tests/test_wave4c_label_store_v2.py::test_wave4c_required_label_families_and_source_trace_are_complete`

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/test_notification_queue.py",
  "tests/test_notification_html_escape.py",
  "tests/test_api_refusal_monitor.py",
  "tests/test_no_data_alert_monitor.py",
  "tests/test_wave4a_digital_twin_historical_microscope.py",
  "tests/test_wave4b_feature_store_v2.py",
  "tests/test_wave4c_label_store_v2.py",
  "tests/safety",
  "tests/test_runtime_control_atomic_halt.py"
 ],
 "before": {
  "commit": "8ed4439824f7ccd1fd5ce249509b8a24f9ea5a9d",
  "commit_subject": "Cleanup: retire twelve merged worktrees; preserve the unique .hermes campaign evidence",
  "captured_utc": "2026-07-26T21:48:03Z",
  "dirty": true,
  "totals": {
   "failed": 16,
   "passed": 202
  }
 },
 "after": {
  "commit": "7feabae2a1a37f6585b5f0b214a9190e13e1ac8f",
  "commit_subject": "Wave 3 / Session M: Session C's four B42 defects, and the one-character claim refuted",
  "captured_utc": "2026-07-26T21:48:23Z",
  "dirty": true,
  "totals": {
   "failed": 4,
   "passed": 202,
   "skipped": 3
  }
 },
 "bad_before": 16,
 "bad_after": 4,
 "unchanged": 4,
 "fixed": [
  "tests/test_wave4a_digital_twin_historical_microscope.py::test_wave4a_asof_event_excludes_path_and_result_labels",
  "tests/test_wave4a_digital_twin_historical_microscope.py::test_wave4a_build_and_verify_temp_route",
  "tests/test_wave4a_digital_twin_historical_microscope.py::test_wave4a_loser_mfe_coverage_preserves_source_gaps",
  "tests/test_wave4a_digital_twin_historical_microscope.py::test_wave4a_material_source_contract_preserves_all_rows",
  "tests/test_wave4b_feature_store_v2.py::test_wave4b_build_and_verify_temp_route",
  "tests/test_wave4b_feature_store_v2.py::test_wave4b_builds_one_feature_row_per_wave4a_canonical_row",
  "tests/test_wave4b_feature_store_v2.py::test_wave4b_feature_values_exclude_forbidden_label_tokens",
  "tests/test_wave4b_feature_store_v2.py::test_wave4b_probability_and_confluence_gaps_are_explicit",
  "tests/test_wave4c_label_store_v2.py::test_wave4c_builds_full_row_label_ledgers_in_temp_route",
  "tests/test_wave4c_label_store_v2.py::test_wave4c_evidence_classes_keep_cash_and_r_separate",
  "tests/test_wave4c_label_store_v2.py::test_wave4c_labels_are_banned_from_feature_store_inputs",
  "tests/test_wave4c_label_store_v2.py::test_wave4c_required_label_families_and_source_trace_are_complete"
 ],
 "regressed": [],
 "bad_before_nodeids": [
  "tests/safety/test_raw_broker_script_guards.py::test_the_raw_guard_allows_a_close_without_a_token",
  "tests/safety/test_raw_broker_script_guards.py::test_the_raw_guard_refuses_a_new_entry_without_a_token",
  "tests/test_no_data_alert_monitor.py::TestKZActiveForSymbol::test_supervised_symbol_maps_cover_watchdog_fleet",
  "tests/test_no_data_alert_monitor.py::TestKZActiveForSymbol::test_us30_cash_alias_resolves",
  "tests/test_wave4a_digital_twin_historical_microscope.py::test_wave4a_asof_event_excludes_path_and_result_labels",
  "tests/test_wave4a_digital_twin_historical_microscope.py::test_wave4a_build_and_verify_temp_route",
  "tests/test_wave4a_digital_twin_historical_microscope.py::test_wave4a_loser_mfe_coverage_preserves_source_gaps",
  "tests/test_wave4a_digital_twin_historical_microscope.py::test_wave4a_material_source_contract_preserves_all_rows",
  "tests/test_wave4b_feature_store_v2.py::test_wave4b_build_and_verify_temp_route",
  "tests/test_wave4b_feature_store_v2.py::test_wave4b_builds_one_feature_row_per_wave4a_canonical_row",
  "tests/test_wave4b_feature_store_v2.py::test_wave4b_feature_values_exclude_forbidden_label_tokens",
  "tests/test_wave4b_feature_store_v2.py::test_wave4b_probability_and_confluence_gaps_are_explicit",
  "tests/test_wave4c_label_store_v2.py::test_wave4c_builds_full_row_label_ledgers_in_temp_route",
  "tests/test_wave4c_label_store_v2.py::test_wave4c_evidence_classes_keep_cash_and_r_separate",
  "tests/test_wave4c_label_store_v2.py::test_wave4c_labels_are_banned_from_feature_store_inputs",
  "tests/test_wave4c_label_store_v2.py::test_wave4c_required_label_families_and_source_trace_are_complete"
 ],
 "bad_after_nodeids": [
  "tests/safety/test_raw_broker_script_guards.py::test_the_raw_guard_allows_a_close_without_a_token",
  "tests/safety/test_raw_broker_script_guards.py::test_the_raw_guard_refuses_a_new_entry_without_a_token",
  "tests/test_no_data_alert_monitor.py::TestKZActiveForSymbol::test_supervised_symbol_maps_cover_watchdog_fleet",
  "tests/test_no_data_alert_monitor.py::TestKZActiveForSymbol::test_us30_cash_alias_resolves"
 ]
}
```
