# Session CA (wave 14, B2100-B2149) — scoped A/B vs the wave-14 base 7b5cbf8d8

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `0044c1b14` | `0044c1b14` |
| captured (UTC) | 2026-07-31T03:50:36Z | 2026-07-31T03:51:03Z |
| working tree | dirty | clean |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 269 | 279 |
| skipped | 0 | 0 |

## Scope difference — declared, not hidden

- before: `['tests/research_infra/test_ar_vol_level_tilt.py', 'tests/research_infra/test_av_timebase_per_file.py', 'tests/research_infra/test_bb_fill_truth.py', 'tests/research_infra/test_candidate_family.py', 'tests/research_infra/test_candidate_family_chain.py', 'tests/research_infra/test_regime_spine_conditions.py', 'tests/research_infra/test_vig_trial_ledger_prospective.py', 'tests/test_canary_watch.py', 'tests/test_implementation_state_block_citations.py', 'tests/test_replay_policy_generation.py', 'tests/ultimate_book/test_book_sleeve_telemetry.py', 'tests/ultimate_book/test_gtos_command_center.py']`
- after : `['tests/research_infra/test_ar_vol_level_tilt.py', 'tests/research_infra/test_av_timebase_per_file.py', 'tests/research_infra/test_bb_fill_truth.py', 'tests/research_infra/test_candidate_family.py', 'tests/research_infra/test_candidate_family_chain.py', 'tests/research_infra/test_regime_spine_conditions.py', 'tests/research_infra/test_vig_trial_ledger_prospective.py', 'tests/test_canary_watch.py', 'tests/test_implementation_state_block_citations.py', 'tests/test_replay_policy_generation.py', 'tests/ultimate_book/test_book_sleeve_telemetry.py', 'tests/ultimate_book/test_gtos_command_center.py']`

**Why this is still a comparison:** the import-closure scope reached 7 files; five more (test_gtos_command_center.py, test_canary_watch.py, test_bb_fill_truth.py, test_candidate_family.py, test_candidate_family_chain.py) read FIVE_SLEEVE_STOP_CONDITIONS_V1.json or the family declaration by PATH LITERAL through their tools rather than by import, and Session CA amended both. Added on BOTH sides.

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_ar_vol_level_tilt.py",
  "tests/research_infra/test_av_timebase_per_file.py",
  "tests/research_infra/test_bb_fill_truth.py",
  "tests/research_infra/test_candidate_family.py",
  "tests/research_infra/test_candidate_family_chain.py",
  "tests/research_infra/test_regime_spine_conditions.py",
  "tests/research_infra/test_vig_trial_ledger_prospective.py",
  "tests/test_canary_watch.py",
  "tests/test_implementation_state_block_citations.py",
  "tests/test_replay_policy_generation.py",
  "tests/ultimate_book/test_book_sleeve_telemetry.py",
  "tests/ultimate_book/test_gtos_command_center.py"
 ],
 "before": {
  "commit": "0044c1b14a87f064a3541e9958ba2bbbec6b4dae",
  "commit_subject": "Session CA: incubation dossier page, block ledger B2100-B2149, reproduction re-run",
  "captured_utc": "2026-07-31T03:50:36Z",
  "dirty": true,
  "totals": {
   "passed": 269
  }
 },
 "after": {
  "commit": "0044c1b14a87f064a3541e9958ba2bbbec6b4dae",
  "commit_subject": "Session CA: incubation dossier page, block ledger B2100-B2149, reproduction re-run",
  "captured_utc": "2026-07-31T03:51:03Z",
  "dirty": false,
  "totals": {
   "passed": 279
  }
 },
 "bad_before": 0,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [],
 "regressed": [],
 "bad_before_nodeids": [],
 "bad_after_nodeids": [],
 "scope_difference": {
  "before": [
   "tests/research_infra/test_ar_vol_level_tilt.py",
   "tests/research_infra/test_av_timebase_per_file.py",
   "tests/research_infra/test_bb_fill_truth.py",
   "tests/research_infra/test_candidate_family.py",
   "tests/research_infra/test_candidate_family_chain.py",
   "tests/research_infra/test_regime_spine_conditions.py",
   "tests/research_infra/test_vig_trial_ledger_prospective.py",
   "tests/test_canary_watch.py",
   "tests/test_implementation_state_block_citations.py",
   "tests/test_replay_policy_generation.py",
   "tests/ultimate_book/test_book_sleeve_telemetry.py",
   "tests/ultimate_book/test_gtos_command_center.py"
  ],
  "after": [
   "tests/research_infra/test_ar_vol_level_tilt.py",
   "tests/research_infra/test_av_timebase_per_file.py",
   "tests/research_infra/test_bb_fill_truth.py",
   "tests/research_infra/test_candidate_family.py",
   "tests/research_infra/test_candidate_family_chain.py",
   "tests/research_infra/test_regime_spine_conditions.py",
   "tests/research_infra/test_vig_trial_ledger_prospective.py",
   "tests/test_canary_watch.py",
   "tests/test_implementation_state_block_citations.py",
   "tests/test_replay_policy_generation.py",
   "tests/ultimate_book/test_book_sleeve_telemetry.py",
   "tests/ultimate_book/test_gtos_command_center.py"
  ],
  "justification": "the import-closure scope reached 7 files; five more (test_gtos_command_center.py, test_canary_watch.py, test_bb_fill_truth.py, test_candidate_family.py, test_candidate_family_chain.py) read FIVE_SLEEVE_STOP_CONDITIONS_V1.json or the family declaration by PATH LITERAL through their tools rather than by import, and Session CA amended both. Added on BOTH sides."
 }
}
```
