# Session HDC exit/capture falsifier A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `82c41b122` | `ffff7542c` |
| captured (UTC) | 2026-08-01T13:58:36Z | 2026-08-01T14:27:55Z |
| working tree | dirty | clean |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 526 | 562 |
| skipped | 2 | 2 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_ao_candidate_family_v3.py",
  "tests/research_infra/test_ao_p_floor_headroom.py",
  "tests/research_infra/test_candidate_family.py",
  "tests/research_infra/test_candidate_family_chain.py",
  "tests/research_infra/test_candidate_family_v2_ratchet.py",
  "tests/research_infra/test_direct_fidelity_measurement.py",
  "tests/research_infra/test_era_population.py",
  "tests/research_infra/test_exit_overlay.py",
  "tests/research_infra/test_fidelity_threshold_variant.py",
  "tests/research_infra/test_gate_partial_universe_stamp.py",
  "tests/research_infra/test_gate_wipeout_signal.py",
  "tests/research_infra/test_session_cs_breaker_folds.py",
  "tests/research_infra/test_session_fc_exit_overlay.py",
  "tests/research_infra/test_train_engine_cuts.py",
  "tests/research_infra/test_trainer_folds.py",
  "tests/research_infra/test_trainer_partitions.py",
  "tests/research_infra/test_training_lane_protocol.py",
  "tests/research_infra/test_walkforward_book_replay.py",
  "tests/research_infra/test_walkforward_family.py",
  "tests/research_infra/test_walkforward_gate.py",
  "tests/research_infra/test_walkforward_supply.py",
  "tests/research_infra/test_wf_diagnostics.py",
  "tests/test_spread_composition.py"
 ],
 "before": {
  "commit": "82c41b122364c4ef56612a5468867fe796bd6c1a",
  "commit_subject": "docs(phase20): close HC exit capture repair",
  "captured_utc": "2026-08-01T13:58:36Z",
  "dirty": true,
  "totals": {
   "passed": 526,
   "skipped": 2
  }
 },
 "after": {
  "commit": "ffff7542cd39e7f1546bc9d5cbecb580f73ecac0",
  "commit_subject": "fix(research): falsify exit capture semantics",
  "captured_utc": "2026-08-01T14:27:55Z",
  "dirty": false,
  "totals": {
   "passed": 562,
   "skipped": 2
  }
 },
 "bad_before": 0,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [],
 "regressed": [],
 "bad_before_nodeids": [],
 "bad_after_nodeids": []
}
```
