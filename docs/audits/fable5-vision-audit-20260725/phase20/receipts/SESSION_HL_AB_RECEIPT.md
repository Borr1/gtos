# Session HL P1 adapter focused A/B

`execution_authority: false`
`activation_authority: false`
`result_bearing_science_executed: false`

**30 bad → 0 bad · 30 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `a1cf205de` | `41534770f` |
| captured (UTC) | 2026-08-01T20:01:44Z | 2026-08-01T20:00:23Z |
| working tree | dirty | clean |
| failed | 0 | 0 |
| errored | 30 | 0 |
| **bad** | **30** | **0** |
| passed | 0 | 30 |
| skipped | 0 | 0 |

## Fixed (30)

- `tests/research_infra/test_wave20_complete_path_shadow.py::test_default_off_does_not_iterate_or_call_dependencies`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_denominator_and_composite_identity_are_preserved`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_first_exact_miss_is_ledgered_once_and_later_rows_do_not_disappear`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_fixed_b0_identity_and_geometry_are_unchanged`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_forbidden_scopes_refuse_before_reader_call[february/result.json-february_2026-economic_selection-february_economics_or_selection_forbidden]`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_forbidden_scopes_refuse_before_reader_call[january/pool.jsonl.gz-january_2026-candidate_breadth-candidate_breadth_forbidden]`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_forbidden_scopes_refuse_before_reader_call[january/pool.jsonl.gz-january_2026-post_hoc_drop-post_hoc_drop_forbidden]`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_forbidden_scopes_refuse_before_reader_call[live-forward/outcome.jsonl-live_forward-metadata-live_forward_read_forbidden]`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_forbidden_scopes_refuse_before_reader_call[march/path.jsonl.gz-march_2026-metadata-march_2026_read_forbidden]`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_ftmo_is_future_economic_scope_and_redacted_account_is_mechanical_only`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_hde_complete_arithmetic_is_authoritative`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_hde_contradictory_evidence_is_refused`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_hde_incomplete_arithmetic_is_not_authoritative`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_hdf_deadline_collision_belongs_to_timebox`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_hdf_m1_collision_selects_lower_net_ordering`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_hdf_partial_uses_original_fraction_and_charges_cost_once`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_hdf_terminal_observation_closes_final_state`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_hdf_uses_first_deadline_eligible_observation`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_injected_account_authority_requires_sha256_shape`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_learned_probability_path_stops_as_k1_stale`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_learned_scheduler_path_stops_as_k1_stale`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_limit_preimage_is_an_internal_intent_not_a_broker_pending_order`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_market_order_preimage_matches_reference_fields`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_owner_risk_volume_is_never_defaulted`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_permission_invalid_numeric_fails_closed`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_permission_missing_field_fails_closed`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_runner_refuses_non_admitted_window_before_dependency_call`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_scheduler_is_capture_only_and_cannot_change_disposition`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_static_import_and_broker_write_surface_are_refused`
- `tests/research_infra/test_wave20_complete_path_shadow.py::test_zero_or_multiple_generated_candidates_fail_at_generation`

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "--noconftest",
  "tests/research_infra/test_wave20_complete_path_shadow.py"
 ],
 "before": {
  "commit": "a1cf205de52a7f279932e4436196a255ae5e7b9b",
  "commit_subject": "phase20: add HK metadata preflight tools",
  "captured_utc": "2026-08-01T20:01:44Z",
  "dirty": true,
  "totals": {
   "error": 30
  }
 },
 "after": {
  "commit": "41534770fa338f12b34d79c9625fd406219a41fe",
  "commit_subject": "phase20: add broker-inert P1 path adapter",
  "captured_utc": "2026-08-01T20:00:23Z",
  "dirty": false,
  "totals": {
   "passed": 30
  }
 },
 "bad_before": 30,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_default_off_does_not_iterate_or_call_dependencies",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_denominator_and_composite_identity_are_preserved",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_first_exact_miss_is_ledgered_once_and_later_rows_do_not_disappear",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_fixed_b0_identity_and_geometry_are_unchanged",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_forbidden_scopes_refuse_before_reader_call[february/result.json-february_2026-economic_selection-february_economics_or_selection_forbidden]",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_forbidden_scopes_refuse_before_reader_call[january/pool.jsonl.gz-january_2026-candidate_breadth-candidate_breadth_forbidden]",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_forbidden_scopes_refuse_before_reader_call[january/pool.jsonl.gz-january_2026-post_hoc_drop-post_hoc_drop_forbidden]",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_forbidden_scopes_refuse_before_reader_call[live-forward/outcome.jsonl-live_forward-metadata-live_forward_read_forbidden]",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_forbidden_scopes_refuse_before_reader_call[march/path.jsonl.gz-march_2026-metadata-march_2026_read_forbidden]",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_ftmo_is_future_economic_scope_and_redacted_account_is_mechanical_only",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_hde_complete_arithmetic_is_authoritative",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_hde_contradictory_evidence_is_refused",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_hde_incomplete_arithmetic_is_not_authoritative",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_hdf_deadline_collision_belongs_to_timebox",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_hdf_m1_collision_selects_lower_net_ordering",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_hdf_partial_uses_original_fraction_and_charges_cost_once",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_hdf_terminal_observation_closes_final_state",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_hdf_uses_first_deadline_eligible_observation",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_injected_account_authority_requires_sha256_shape",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_learned_probability_path_stops_as_k1_stale",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_learned_scheduler_path_stops_as_k1_stale",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_limit_preimage_is_an_internal_intent_not_a_broker_pending_order",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_market_order_preimage_matches_reference_fields",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_owner_risk_volume_is_never_defaulted",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_permission_invalid_numeric_fails_closed",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_permission_missing_field_fails_closed",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_runner_refuses_non_admitted_window_before_dependency_call",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_scheduler_is_capture_only_and_cannot_change_disposition",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_static_import_and_broker_write_surface_are_refused",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_zero_or_multiple_generated_candidates_fail_at_generation"
 ],
 "regressed": [],
 "bad_before_nodeids": [
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_default_off_does_not_iterate_or_call_dependencies",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_denominator_and_composite_identity_are_preserved",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_first_exact_miss_is_ledgered_once_and_later_rows_do_not_disappear",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_fixed_b0_identity_and_geometry_are_unchanged",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_forbidden_scopes_refuse_before_reader_call[february/result.json-february_2026-economic_selection-february_economics_or_selection_forbidden]",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_forbidden_scopes_refuse_before_reader_call[january/pool.jsonl.gz-january_2026-candidate_breadth-candidate_breadth_forbidden]",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_forbidden_scopes_refuse_before_reader_call[january/pool.jsonl.gz-january_2026-post_hoc_drop-post_hoc_drop_forbidden]",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_forbidden_scopes_refuse_before_reader_call[live-forward/outcome.jsonl-live_forward-metadata-live_forward_read_forbidden]",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_forbidden_scopes_refuse_before_reader_call[march/path.jsonl.gz-march_2026-metadata-march_2026_read_forbidden]",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_ftmo_is_future_economic_scope_and_redacted_account_is_mechanical_only",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_hde_complete_arithmetic_is_authoritative",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_hde_contradictory_evidence_is_refused",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_hde_incomplete_arithmetic_is_not_authoritative",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_hdf_deadline_collision_belongs_to_timebox",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_hdf_m1_collision_selects_lower_net_ordering",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_hdf_partial_uses_original_fraction_and_charges_cost_once",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_hdf_terminal_observation_closes_final_state",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_hdf_uses_first_deadline_eligible_observation",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_injected_account_authority_requires_sha256_shape",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_learned_probability_path_stops_as_k1_stale",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_learned_scheduler_path_stops_as_k1_stale",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_limit_preimage_is_an_internal_intent_not_a_broker_pending_order",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_market_order_preimage_matches_reference_fields",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_owner_risk_volume_is_never_defaulted",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_permission_invalid_numeric_fails_closed",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_permission_missing_field_fails_closed",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_runner_refuses_non_admitted_window_before_dependency_call",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_scheduler_is_capture_only_and_cannot_change_disposition",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_static_import_and_broker_write_surface_are_refused",
  "tests/research_infra/test_wave20_complete_path_shadow.py::test_zero_or_multiple_generated_candidates_fail_at_generation"
 ],
 "bad_after_nodeids": []
}
```
