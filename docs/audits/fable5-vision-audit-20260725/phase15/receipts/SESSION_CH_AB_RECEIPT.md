# Session CH — scoped A/B vs the 12,476-pass ZERO baseline

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `d312e06e3` | `f0418a830` |
| captured (UTC) | 2026-07-31T10:22:21Z | 2026-07-31T11:40:27Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 12476 | 226 |
| skipped | 120 | 1 |

## Scope difference — declared, not hidden

- before: `['tests/']`
- after : `['tests/research_infra/test_ao_candidate_family_v3.py', 'tests/research_infra/test_bb_fill_truth.py', 'tests/research_infra/test_candidate_family.py', 'tests/research_infra/test_candidate_family_chain.py', 'tests/research_infra/test_candidate_family_v2_ratchet.py', 'tests/research_infra/test_ch_lever_measurements.py', 'tests/research_infra/test_ch_measurement_protocol.py', 'tests/research_infra/test_training_lane_protocol.py', 'tests/research_infra/test_vig_trial_ledger_prospective.py', 'tests/test_implementation_state_block_citations.py', 'tests/ultimate_book/test_gtos_command_center.py']`

**Why this is still a comparison:** Before is the committed whole-suite ZERO baseline: 12,476 passed and 0 bad at d312e06e3. After is the tool-derived 11-file import/path closure of the exact Session CH diff from its commission commit be9b5ed4c through findings commit f0418a830: 226 passed and 0 bad. Because the before side has zero failures and zero collection errors suite-wide, any bad test in the after scope is a regression. The after dirty flag comprises the preflight-generated .context/LIVE_STATE.md plus the SCOPE/AFTER capture artifacts themselves; every Session CH source, test, ledger, result and measured receipt under comparison was committed before capture.

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/"
 ],
 "before": {
  "commit": "d312e06e3cbfbc676ea654ef2464725f0d87188d",
  "commit_subject": "Merge Session CF: there was no rename \u2014 the orchestrator's event refuted with the broker's own tree, and the real silence gets a watchdog",
  "captured_utc": "2026-07-31T10:22:21Z",
  "dirty": true,
  "totals": {
   "passed": 12476,
   "skipped": 120,
   "xfailed": 32
  }
 },
 "after": {
  "commit": "f0418a830ce964103f76e819393b0868e5934cb8",
  "commit_subject": "Session CH: deliver lever measurement findings",
  "captured_utc": "2026-07-31T11:40:27Z",
  "dirty": true,
  "totals": {
   "passed": 226,
   "skipped": 1
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
   "tests/"
  ],
  "after": [
   "tests/research_infra/test_ao_candidate_family_v3.py",
   "tests/research_infra/test_bb_fill_truth.py",
   "tests/research_infra/test_candidate_family.py",
   "tests/research_infra/test_candidate_family_chain.py",
   "tests/research_infra/test_candidate_family_v2_ratchet.py",
   "tests/research_infra/test_ch_lever_measurements.py",
   "tests/research_infra/test_ch_measurement_protocol.py",
   "tests/research_infra/test_training_lane_protocol.py",
   "tests/research_infra/test_vig_trial_ledger_prospective.py",
   "tests/test_implementation_state_block_citations.py",
   "tests/ultimate_book/test_gtos_command_center.py"
  ],
  "justification": "Before is the committed whole-suite ZERO baseline: 12,476 passed and 0 bad at d312e06e3. After is the tool-derived 11-file import/path closure of the exact Session CH diff from its commission commit be9b5ed4c through findings commit f0418a830: 226 passed and 0 bad. Because the before side has zero failures and zero collection errors suite-wide, any bad test in the after scope is a regression. The after dirty flag comprises the preflight-generated .context/LIVE_STATE.md plus the SCOPE/AFTER capture artifacts themselves; every Session CH source, test, ledger, result and measured receipt under comparison was committed before capture."
 }
}
```
