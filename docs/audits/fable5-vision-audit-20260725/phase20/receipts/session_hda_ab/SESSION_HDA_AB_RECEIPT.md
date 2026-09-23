# Session HDA fidelity-authority falsifier A/B

**7 bad → 0 bad · 7 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `113b04891` | `4f5c5d428` |
| captured (UTC) | 2026-08-01T13:54:19Z | 2026-08-01T14:01:56Z |
| working tree | dirty | dirty |
| failed | 7 | 0 |
| errored | 0 | 0 |
| **bad** | **7** | **0** |
| passed | 216 | 227 |
| skipped | 0 | 0 |

## Fixed (7)

- `tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_fake_live_label_needs_hash_bound_recording_authority`
- `tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_independent_sources_cannot_be_two_paths_to_one_canonical_population`
- `tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_legacy_spec_cannot_emit_a_v2_authority_result`
- `tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_nonstandard_json_constants_are_not_identity_values`
- `tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_process_local_registrars_share_one_nonshadowable_namespace`
- `tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_public_authored_register_cannot_be_mutated_into_v2_authority`
- `tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_relabelled_same_lineage_needs_hash_bound_lineage_authority`

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_hda_fidelity_authority_falsifier.py",
  "tests/research_infra/test_direct_fidelity_measurement.py",
  "tests/research_infra/test_walkforward_gate.py",
  "tests/research_infra/test_candidate_family.py",
  "tests/research_infra/test_fidelity_threshold_variant.py",
  "tests/research_infra/test_walkforward_family.py",
  "tests/research_infra/test_walkforward_supply.py",
  "tests/research_infra/test_fidelity_register_matches_receipt.py"
 ],
 "before": {
  "commit": "113b04891969213614d4635c1e609629c935f67c",
  "commit_subject": "audit(phase20): close fidelity authority session",
  "captured_utc": "2026-08-01T13:54:19Z",
  "dirty": true,
  "totals": {
   "failed": 7,
   "passed": 216
  }
 },
 "after": {
  "commit": "4f5c5d4286764b622cc0f539ac40887a2bbbd8b4",
  "commit_subject": "fix(walkforward): close fidelity authority bypasses",
  "captured_utc": "2026-08-01T14:01:56Z",
  "dirty": true,
  "totals": {
   "passed": 227
  }
 },
 "bad_before": 7,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [
  "tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_fake_live_label_needs_hash_bound_recording_authority",
  "tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_independent_sources_cannot_be_two_paths_to_one_canonical_population",
  "tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_legacy_spec_cannot_emit_a_v2_authority_result",
  "tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_nonstandard_json_constants_are_not_identity_values",
  "tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_process_local_registrars_share_one_nonshadowable_namespace",
  "tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_public_authored_register_cannot_be_mutated_into_v2_authority",
  "tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_relabelled_same_lineage_needs_hash_bound_lineage_authority"
 ],
 "regressed": [],
 "bad_before_nodeids": [
  "tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_fake_live_label_needs_hash_bound_recording_authority",
  "tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_independent_sources_cannot_be_two_paths_to_one_canonical_population",
  "tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_legacy_spec_cannot_emit_a_v2_authority_result",
  "tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_nonstandard_json_constants_are_not_identity_values",
  "tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_process_local_registrars_share_one_nonshadowable_namespace",
  "tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_public_authored_register_cannot_be_mutated_into_v2_authority",
  "tests/research_infra/test_hda_fidelity_authority_falsifier.py::test_relabelled_same_lineage_needs_hash_bound_lineage_authority"
 ],
 "bad_after_nodeids": []
}
```
