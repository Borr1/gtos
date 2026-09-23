# Session BB (wave 13) — scoped A/B: the fill truth, the supply rank, and the silence check

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `562f35acb` | `a280f7f09` |
| captured (UTC) | 2026-07-30T17:06:57Z | 2026-07-30T17:14:20Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 549 | 567 |
| skipped | 1 | 1 |

## Scope difference — declared, not hidden

- before: `['tests/research_infra/test_walkforward_book_replay.py', 'tests/research_infra/test_walkforward_gate.py', 'tests/research_infra/test_walkforward_supply.py', 'tests/research_infra/test_era_population.py', 'tests/research_infra/test_candidate_family.py', 'tests/research_infra/test_candidate_family_chain.py', 'tests/research_infra/test_candidate_family_v2_ratchet.py', 'tests/research_infra/test_ao_candidate_family_v3.py', 'tests/research_infra/test_population_rule_ratified.py', 'tests/scripts', 'tests/test_armed_set_mc.py']`
- after : `['tests/research_infra/test_bb_fill_truth.py', 'tests/research_infra/test_walkforward_book_replay.py', 'tests/research_infra/test_walkforward_gate.py', 'tests/research_infra/test_walkforward_supply.py', 'tests/research_infra/test_era_population.py', 'tests/research_infra/test_candidate_family.py', 'tests/research_infra/test_candidate_family_chain.py', 'tests/research_infra/test_candidate_family_v2_ratchet.py', 'tests/research_infra/test_ao_candidate_family_v3.py', 'tests/research_infra/test_population_rule_ratified.py', 'tests/scripts', 'tests/test_armed_set_mc.py']`

**Why this is still a comparison:** The AFTER scope adds tests/research_infra/test_bb_fill_truth.py, which does not exist on the BEFORE side because this session creates it. Every other path is identical and was run on both sides. The BEFORE side was produced by COPY-BACK (BB's new files moved out of the working tree and moved back), never by git checkout, per WAVE_11_WORKING_AGREEMENT section 2. Captured at the FINISHED tree.

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_walkforward_book_replay.py",
  "tests/research_infra/test_walkforward_gate.py",
  "tests/research_infra/test_walkforward_supply.py",
  "tests/research_infra/test_era_population.py",
  "tests/research_infra/test_candidate_family.py",
  "tests/research_infra/test_candidate_family_chain.py",
  "tests/research_infra/test_candidate_family_v2_ratchet.py",
  "tests/research_infra/test_ao_candidate_family_v3.py",
  "tests/research_infra/test_population_rule_ratified.py",
  "tests/scripts",
  "tests/test_armed_set_mc.py"
 ],
 "before": {
  "commit": "562f35acb7503186507db9cd4e12dbe2d145521a",
  "commit_subject": "BB deliverable 2: the supply hunt ranked by FIRE RATE, gated at the ratified rule, priced (B1976-B1999)",
  "captured_utc": "2026-07-30T17:06:57Z",
  "dirty": true,
  "totals": {
   "passed": 549,
   "skipped": 1,
   "xfailed": 1
  }
 },
 "after": {
  "commit": "a280f7f09b73dcaeb9f273cded93d84208774dd2",
  "commit_subject": "BB: the adversarial pass (which refuted my own headline), the silence tool, the A/B and the result doc",
  "captured_utc": "2026-07-30T17:14:20Z",
  "dirty": true,
  "totals": {
   "passed": 567,
   "skipped": 1,
   "xfailed": 1
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
   "tests/research_infra/test_walkforward_book_replay.py",
   "tests/research_infra/test_walkforward_gate.py",
   "tests/research_infra/test_walkforward_supply.py",
   "tests/research_infra/test_era_population.py",
   "tests/research_infra/test_candidate_family.py",
   "tests/research_infra/test_candidate_family_chain.py",
   "tests/research_infra/test_candidate_family_v2_ratchet.py",
   "tests/research_infra/test_ao_candidate_family_v3.py",
   "tests/research_infra/test_population_rule_ratified.py",
   "tests/scripts",
   "tests/test_armed_set_mc.py"
  ],
  "after": [
   "tests/research_infra/test_bb_fill_truth.py",
   "tests/research_infra/test_walkforward_book_replay.py",
   "tests/research_infra/test_walkforward_gate.py",
   "tests/research_infra/test_walkforward_supply.py",
   "tests/research_infra/test_era_population.py",
   "tests/research_infra/test_candidate_family.py",
   "tests/research_infra/test_candidate_family_chain.py",
   "tests/research_infra/test_candidate_family_v2_ratchet.py",
   "tests/research_infra/test_ao_candidate_family_v3.py",
   "tests/research_infra/test_population_rule_ratified.py",
   "tests/scripts",
   "tests/test_armed_set_mc.py"
  ],
  "justification": "The AFTER scope adds tests/research_infra/test_bb_fill_truth.py, which does not exist on the BEFORE side because this session creates it. Every other path is identical and was run on both sides. The BEFORE side was produced by COPY-BACK (BB's new files moved out of the working tree and moved back), never by git checkout, per WAVE_11_WORKING_AGREEMENT section 2. Captured at the FINISHED tree."
 }
}
```
