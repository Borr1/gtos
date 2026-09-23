# Failure-set A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `8db17b29c` | `6f8a2e031` |
| captured (UTC) | 2026-07-30T04:21:13Z | 2026-07-30T11:51:57Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 11454 | 11516 |
| skipped | 112 | 112 |

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
  "commit": "8db17b29ca6b6b458509ae713169698733756748",
  "commit_subject": "Wave 10: commission AN (population rule + decidability wiring) and AO (regime conditioning + power-pool)",
  "captured_utc": "2026-07-30T04:21:13Z",
  "dirty": true,
  "totals": {
   "passed": 11454,
   "skipped": 112,
   "xfailed": 32
  }
 },
 "after": {
  "commit": "6f8a2e031c6b3f40f41bdfed74c342a3d3d55205",
  "commit_subject": "AO's A/B receipt made self-contained \u2014 the guard's own remedy, applied at the train",
  "captured_utc": "2026-07-30T11:51:57Z",
  "dirty": true,
  "totals": {
   "passed": 11516,
   "skipped": 112,
   "xfailed": 32
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
