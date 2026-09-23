# Session HM P1 adapter independent falsification A/B

`execution_authority: false`

`activation_authority: false`

`result_bearing_science_executed: false`

**40 bad → 0 bad · 40 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `41534770f` | `1c81f5cd3` |
| captured (UTC) | 2026-08-01T20:36:34Z | 2026-08-01T20:36:38Z |
| working tree | dirty | clean |
| failed | 40 | 0 |
| errored | 0 | 0 |
| **bad** | **40** | **0** |
| passed | 30 | 70 |
| skipped | 0 | 0 |

## Fixed (40)

- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_cyclic_scheduler_packet_fails_closed_without_recursion_escape`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_dependency_exception_becomes_first_miss_without_denominator_loss[candidate_generation-overrides0]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_dependency_exception_becomes_first_miss_without_denominator_loss[dynamic_router-overrides1]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_dependency_exception_becomes_first_miss_without_denominator_loss[fill_or_no_fill-overrides3]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_dependency_exception_becomes_first_miss_without_denominator_loss[scheduler_capture_only-overrides2]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_generated_candidate_identity_alias_refuses_before_transform[candidate_id-another-candidate]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_generated_candidate_identity_alias_refuses_before_transform[decision_time_utc-2026-01-02T13:16:00Z]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_generated_candidate_identity_alias_refuses_before_transform[direction-SHORT]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_generated_candidate_identity_alias_refuses_before_transform[side-SHORT]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_generated_candidate_identity_alias_refuses_before_transform[symbol-EURUSD]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_hdf_exception_becomes_first_miss_without_denominator_loss`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_malformed_permission_container_fails_closed[7]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_malformed_permission_container_fails_closed[None]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_malformed_permission_container_fails_closed[True]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_malformed_permission_container_fails_closed[malformed1]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_malformed_permission_container_fails_closed[permission]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_nested_aliased_learned_probability_or_value_stops_k1[candidate-probability]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_nested_aliased_learned_probability_or_value_stops_k1[candidateProbability]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_nested_aliased_learned_probability_or_value_stops_k1[learnedValue]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_nested_aliased_learned_probability_or_value_stops_k1[modelProbability]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_nested_aliased_learned_probability_or_value_stops_k1[predicted-value]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_noncommissioned_or_non_utc_identity_refuses_before_dependency[april_2026-2026-05-01T00:00:00Z-source_decision_outside_commissioned_window]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_noncommissioned_or_non_utc_identity_refuses_before_dependency[january_2026-2026-01-02T13:15:00-source_decision_time_not_true_utc]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_noncommissioned_or_non_utc_identity_refuses_before_dependency[january_2026-2026-01-31T00:00:00Z-source_decision_outside_commissioned_window]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_noncommissioned_or_non_utc_identity_refuses_before_dependency[january_2026-not-a-time-source_decision_time_invalid]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_noncommissioned_or_non_utc_identity_refuses_before_dependency[may_2026-2026-05-31T00:00:00Z-source_decision_outside_commissioned_window]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_one_dependency_refusal_cannot_drop_or_duplicate_another_identity`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_only_literal_true_can_leave_default_off[1]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_only_literal_true_can_leave_default_off[enabled2]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_only_literal_true_can_leave_default_off[enabled3]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_only_literal_true_can_leave_default_off[true]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_order_preimage_malformed_nonfinite_negative_alias_and_geometry_refuse[<lambda>-order_preimage_geometry_invalid]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_order_preimage_malformed_nonfinite_negative_alias_and_geometry_refuse[<lambda>-order_preimage_nonpositive:entry_price]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_order_preimage_malformed_nonfinite_negative_alias_and_geometry_refuse[<lambda>-order_preimage_nonpositive:stop_loss]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_order_preimage_malformed_nonfinite_negative_alias_and_geometry_refuse[<lambda>-order_preimage_side_direction_conflict]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_path_aliased_forbidden_window_refuses_before_reader[april\\..\\live-forward\\rows.jsonl-live_forward_read_forbidden]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_path_aliased_forbidden_window_refuses_before_reader[january/%2e%2e/january/pool.jsonl-source_path_alias_forbidden]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_path_aliased_forbidden_window_refuses_before_reader[january/../march/pool.jsonl.gz-march_2026_read_forbidden]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_path_aliased_forbidden_window_refuses_before_reader[may/../february/result.json-february_window_alias_forbidden]`
- `tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_scheduler_input_mutation_is_isolated_refused_and_cannot_change_preimage`

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "--noconftest",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py"
 ],
 "before": {
  "commit": "41534770fa338f12b34d79c9625fd406219a41fe",
  "commit_subject": "phase20: add broker-inert P1 path adapter",
  "captured_utc": "2026-08-01T20:36:34Z",
  "dirty": true,
  "totals": {
   "failed": 40,
   "passed": 30
  }
 },
 "after": {
  "commit": "1c81f5cd384671a4a99ddcda49f9dfc6ef7bae51",
  "commit_subject": "phase20: harden P1 adapter under HM falsification",
  "captured_utc": "2026-08-01T20:36:38Z",
  "dirty": false,
  "totals": {
   "passed": 70
  }
 },
 "bad_before": 40,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_cyclic_scheduler_packet_fails_closed_without_recursion_escape",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_dependency_exception_becomes_first_miss_without_denominator_loss[candidate_generation-overrides0]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_dependency_exception_becomes_first_miss_without_denominator_loss[dynamic_router-overrides1]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_dependency_exception_becomes_first_miss_without_denominator_loss[fill_or_no_fill-overrides3]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_dependency_exception_becomes_first_miss_without_denominator_loss[scheduler_capture_only-overrides2]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_generated_candidate_identity_alias_refuses_before_transform[candidate_id-another-candidate]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_generated_candidate_identity_alias_refuses_before_transform[decision_time_utc-2026-01-02T13:16:00Z]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_generated_candidate_identity_alias_refuses_before_transform[direction-SHORT]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_generated_candidate_identity_alias_refuses_before_transform[side-SHORT]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_generated_candidate_identity_alias_refuses_before_transform[symbol-EURUSD]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_hdf_exception_becomes_first_miss_without_denominator_loss",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_malformed_permission_container_fails_closed[7]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_malformed_permission_container_fails_closed[None]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_malformed_permission_container_fails_closed[True]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_malformed_permission_container_fails_closed[malformed1]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_malformed_permission_container_fails_closed[permission]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_nested_aliased_learned_probability_or_value_stops_k1[candidate-probability]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_nested_aliased_learned_probability_or_value_stops_k1[candidateProbability]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_nested_aliased_learned_probability_or_value_stops_k1[learnedValue]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_nested_aliased_learned_probability_or_value_stops_k1[modelProbability]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_nested_aliased_learned_probability_or_value_stops_k1[predicted-value]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_noncommissioned_or_non_utc_identity_refuses_before_dependency[april_2026-2026-05-01T00:00:00Z-source_decision_outside_commissioned_window]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_noncommissioned_or_non_utc_identity_refuses_before_dependency[january_2026-2026-01-02T13:15:00-source_decision_time_not_true_utc]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_noncommissioned_or_non_utc_identity_refuses_before_dependency[january_2026-2026-01-31T00:00:00Z-source_decision_outside_commissioned_window]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_noncommissioned_or_non_utc_identity_refuses_before_dependency[january_2026-not-a-time-source_decision_time_invalid]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_noncommissioned_or_non_utc_identity_refuses_before_dependency[may_2026-2026-05-31T00:00:00Z-source_decision_outside_commissioned_window]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_one_dependency_refusal_cannot_drop_or_duplicate_another_identity",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_only_literal_true_can_leave_default_off[1]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_only_literal_true_can_leave_default_off[enabled2]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_only_literal_true_can_leave_default_off[enabled3]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_only_literal_true_can_leave_default_off[true]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_order_preimage_malformed_nonfinite_negative_alias_and_geometry_refuse[<lambda>-order_preimage_geometry_invalid]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_order_preimage_malformed_nonfinite_negative_alias_and_geometry_refuse[<lambda>-order_preimage_nonpositive:entry_price]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_order_preimage_malformed_nonfinite_negative_alias_and_geometry_refuse[<lambda>-order_preimage_nonpositive:stop_loss]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_order_preimage_malformed_nonfinite_negative_alias_and_geometry_refuse[<lambda>-order_preimage_side_direction_conflict]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_path_aliased_forbidden_window_refuses_before_reader[april\\\\..\\\\live-forward\\\\rows.jsonl-live_forward_read_forbidden]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_path_aliased_forbidden_window_refuses_before_reader[january/%2e%2e/january/pool.jsonl-source_path_alias_forbidden]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_path_aliased_forbidden_window_refuses_before_reader[january/../march/pool.jsonl.gz-march_2026_read_forbidden]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_path_aliased_forbidden_window_refuses_before_reader[may/../february/result.json-february_window_alias_forbidden]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_scheduler_input_mutation_is_isolated_refused_and_cannot_change_preimage"
 ],
 "regressed": [],
 "bad_before_nodeids": [
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_cyclic_scheduler_packet_fails_closed_without_recursion_escape",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_dependency_exception_becomes_first_miss_without_denominator_loss[candidate_generation-overrides0]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_dependency_exception_becomes_first_miss_without_denominator_loss[dynamic_router-overrides1]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_dependency_exception_becomes_first_miss_without_denominator_loss[fill_or_no_fill-overrides3]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_dependency_exception_becomes_first_miss_without_denominator_loss[scheduler_capture_only-overrides2]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_generated_candidate_identity_alias_refuses_before_transform[candidate_id-another-candidate]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_generated_candidate_identity_alias_refuses_before_transform[decision_time_utc-2026-01-02T13:16:00Z]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_generated_candidate_identity_alias_refuses_before_transform[direction-SHORT]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_generated_candidate_identity_alias_refuses_before_transform[side-SHORT]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_generated_candidate_identity_alias_refuses_before_transform[symbol-EURUSD]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_hdf_exception_becomes_first_miss_without_denominator_loss",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_malformed_permission_container_fails_closed[7]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_malformed_permission_container_fails_closed[None]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_malformed_permission_container_fails_closed[True]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_malformed_permission_container_fails_closed[malformed1]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_malformed_permission_container_fails_closed[permission]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_nested_aliased_learned_probability_or_value_stops_k1[candidate-probability]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_nested_aliased_learned_probability_or_value_stops_k1[candidateProbability]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_nested_aliased_learned_probability_or_value_stops_k1[learnedValue]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_nested_aliased_learned_probability_or_value_stops_k1[modelProbability]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_nested_aliased_learned_probability_or_value_stops_k1[predicted-value]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_noncommissioned_or_non_utc_identity_refuses_before_dependency[april_2026-2026-05-01T00:00:00Z-source_decision_outside_commissioned_window]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_noncommissioned_or_non_utc_identity_refuses_before_dependency[january_2026-2026-01-02T13:15:00-source_decision_time_not_true_utc]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_noncommissioned_or_non_utc_identity_refuses_before_dependency[january_2026-2026-01-31T00:00:00Z-source_decision_outside_commissioned_window]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_noncommissioned_or_non_utc_identity_refuses_before_dependency[january_2026-not-a-time-source_decision_time_invalid]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_noncommissioned_or_non_utc_identity_refuses_before_dependency[may_2026-2026-05-31T00:00:00Z-source_decision_outside_commissioned_window]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_one_dependency_refusal_cannot_drop_or_duplicate_another_identity",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_only_literal_true_can_leave_default_off[1]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_only_literal_true_can_leave_default_off[enabled2]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_only_literal_true_can_leave_default_off[enabled3]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_only_literal_true_can_leave_default_off[true]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_order_preimage_malformed_nonfinite_negative_alias_and_geometry_refuse[<lambda>-order_preimage_geometry_invalid]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_order_preimage_malformed_nonfinite_negative_alias_and_geometry_refuse[<lambda>-order_preimage_nonpositive:entry_price]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_order_preimage_malformed_nonfinite_negative_alias_and_geometry_refuse[<lambda>-order_preimage_nonpositive:stop_loss]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_order_preimage_malformed_nonfinite_negative_alias_and_geometry_refuse[<lambda>-order_preimage_side_direction_conflict]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_path_aliased_forbidden_window_refuses_before_reader[april\\\\..\\\\live-forward\\\\rows.jsonl-live_forward_read_forbidden]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_path_aliased_forbidden_window_refuses_before_reader[january/%2e%2e/january/pool.jsonl-source_path_alias_forbidden]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_path_aliased_forbidden_window_refuses_before_reader[january/../march/pool.jsonl.gz-march_2026_read_forbidden]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_path_aliased_forbidden_window_refuses_before_reader[may/../february/result.json-february_window_alias_forbidden]",
  "tests/research_infra/test_session_hm_p1_adapter_falsifier.py::test_scheduler_input_mutation_is_isolated_refused_and_cannot_change_preimage"
 ],
 "bad_after_nodeids": []
}
```
