# Session HK focused metadata preflight A/B

**16 bad → 0 bad · 16 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `5b2fe3020` | `a1cf205de` |
| captured (UTC) | 2026-08-01T19:24:51Z | 2026-08-01T19:24:52Z |
| working tree | clean | clean |
| failed | 16 | 0 |
| errored | 0 | 0 |
| **bad** | **16** | **0** |
| passed | 0 | 16 |
| skipped | 0 | 0 |

## Fixed (16)

- `../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_b0_exact_published_receipts_advance_fixed_member_unchanged`
- `../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_b0_refuses_candidate_identity_change`
- `../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_b0_refuses_hdf_hash_drift_before_routing`
- `../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_b0_refuses_non_admit_hdf_even_when_bytes_are_rebound`
- `../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_b0_refuses_unreadable_exact_hdf_git_object`
- `../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_implementation_imports_are_bound_to_selected_repository`
- `../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_machine_receipts_carry_no_execution_or_activation_authority`
- `../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_accepts_only_exact_g0_hash_supersession`
- `../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_allows_february_attribution_metadata_only`
- `../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_hash_conflict_is_explicit_and_not_rejection`
- `../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_known_answer_reports_every_declared_entry_without_pool`
- `../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_missing_placeholder_names_exact_prerequisite`
- `../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_refuses_forbidden_paths_before_touch[captures/2026-02/economics.json-economics-february_economics_refused]`
- `../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_refuses_forbidden_paths_before_touch[captures/2026-03-01/outcomes.json-metadata_only-march_path_refused]`
- `../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_refuses_forbidden_paths_before_touch[captures/live_forward/outcomes.json-metadata_only-live_forward_path_refused]`
- `../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_refuses_outcome_metadata_key_requests`

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "/Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py"
 ],
 "before": {
  "commit": "5b2fe3020211eb7456dcd747de20dfcb1d85806d",
  "commit_subject": "test(phase20): retain sealed baseline node identities",
  "captured_utc": "2026-08-01T19:24:51Z",
  "dirty": false,
  "totals": {
   "failed": 16
  }
 },
 "after": {
  "commit": "a1cf205de52a7f279932e4436196a255ae5e7b9b",
  "commit_subject": "phase20: add HK metadata preflight tools",
  "captured_utc": "2026-08-01T19:24:52Z",
  "dirty": false,
  "totals": {
   "passed": 16
  }
 },
 "bad_before": 16,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_b0_exact_published_receipts_advance_fixed_member_unchanged",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_b0_refuses_candidate_identity_change",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_b0_refuses_hdf_hash_drift_before_routing",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_b0_refuses_non_admit_hdf_even_when_bytes_are_rebound",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_b0_refuses_unreadable_exact_hdf_git_object",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_implementation_imports_are_bound_to_selected_repository",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_machine_receipts_carry_no_execution_or_activation_authority",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_accepts_only_exact_g0_hash_supersession",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_allows_february_attribution_metadata_only",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_hash_conflict_is_explicit_and_not_rejection",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_known_answer_reports_every_declared_entry_without_pool",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_missing_placeholder_names_exact_prerequisite",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_refuses_forbidden_paths_before_touch[captures/2026-02/economics.json-economics-february_economics_refused]",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_refuses_forbidden_paths_before_touch[captures/2026-03-01/outcomes.json-metadata_only-march_path_refused]",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_refuses_forbidden_paths_before_touch[captures/live_forward/outcomes.json-metadata_only-live_forward_path_refused]",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_refuses_outcome_metadata_key_requests"
 ],
 "regressed": [],
 "bad_before_nodeids": [
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_b0_exact_published_receipts_advance_fixed_member_unchanged",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_b0_refuses_candidate_identity_change",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_b0_refuses_hdf_hash_drift_before_routing",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_b0_refuses_non_admit_hdf_even_when_bytes_are_rebound",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_b0_refuses_unreadable_exact_hdf_git_object",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_implementation_imports_are_bound_to_selected_repository",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_machine_receipts_carry_no_execution_or_activation_authority",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_accepts_only_exact_g0_hash_supersession",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_allows_february_attribution_metadata_only",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_hash_conflict_is_explicit_and_not_rejection",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_known_answer_reports_every_declared_entry_without_pool",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_missing_placeholder_names_exact_prerequisite",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_refuses_forbidden_paths_before_touch[captures/2026-02/economics.json-economics-february_economics_refused]",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_refuses_forbidden_paths_before_touch[captures/2026-03-01/outcomes.json-metadata_only-march_path_refused]",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_refuses_forbidden_paths_before_touch[captures/live_forward/outcomes.json-metadata_only-live_forward_path_refused]",
  "../../../../Users/borr/GTOSActive/worktrees/wave20-science-critical-path-20260802/tests/research_infra/test_session_hk_critical_path_preflight.py::test_s0_refuses_outcome_metadata_key_requests"
 ],
 "bad_after_nodeids": []
}
```
