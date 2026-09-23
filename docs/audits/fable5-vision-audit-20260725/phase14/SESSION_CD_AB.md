# Session CD A/B — zero to zero, 6 scoped files, +43 new tests captured apart

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `2f5cd96c9` | `2f5cd96c9` |
| captured (UTC) | 2026-07-31T10:41:05Z | 2026-07-31T10:41:12Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 107 | 110 |
| skipped | 0 | 0 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_train_engine_cuts.py",
  "tests/research_infra/test_train_engine_guard.py",
  "tests/test_implementation_state_block_citations.py",
  "tests/test_replay_acceleration_contract_split.py",
  "tests/test_replay_acceleration_real_contract.py",
  "tests/test_replay_acceleration_real_parity.py"
 ],
 "before": {
  "commit": "2f5cd96c916e0e5dc4e6c8d6aacdbd52d32de689",
  "commit_subject": "cd_ab: drop scope files absent at BASE, and say which",
  "captured_utc": "2026-07-31T10:41:05Z",
  "dirty": true,
  "totals": {
   "passed": 107
  }
 },
 "after": {
  "commit": "2f5cd96c916e0e5dc4e6c8d6aacdbd52d32de689",
  "commit_subject": "cd_ab: drop scope files absent at BASE, and say which",
  "captured_utc": "2026-07-31T10:41:12Z",
  "dirty": true,
  "totals": {
   "passed": 110
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

---

## What the two commit hashes mean, and what was captured apart

**Both captures report `2f5cd96c9` because this is a copy-back A/B**, which the
working agreement mandates: `HEAD` never moved. The BEFORE side is every changed
file restored to its state at `9a8d69abc` (16 of the 21 do not exist there at all
and were deleted for the capture); the AFTER side is `HEAD` restored and
**verified byte-for-byte against a sha256 recorded before the swap** — `cd_ab.py`
refuses to publish otherwise, and it did refuse once, on an uncommitted edit to
the result document.

**`tests/research_infra/test_train_engine_lane.py` is deliberately outside the
scope above and captured separately: 43 passed, 0 failed.** It does not exist at
BASE, and a scope entry that is absent at BASE makes pytest exit on a usage error
— so the BEFORE capture parses ZERO outcomes and an empty failure set reads
exactly like a clean one. That is Session BD's B2073 shape, and this session hit
it on the first attempt. It was visible only because `pytest_failset` marks such
a capture `usable_as_baseline=false` and refuses to diff it. `cd_ab.py` now drops
absent-at-BASE files from the shared scope and names them in the run log.

The `+3 passed` inside the scope (107 → 110) is
`test_implementation_state_block_citations.py`: the new
`test_no_wave_in_flight_is_declared_or_the_table_is_populated`, plus two
parametrised cases the wave-range retirement re-enabled.

**Wider sanity outside this receipt:** `tests/research_infra/` at HEAD is
**1,896 passed, 7 skipped, 0 failed**.
