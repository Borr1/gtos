# Failure-set A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `6f8a2e031` | `f6b51dd07` |
| captured (UTC) | 2026-07-30T11:51:57Z | 2026-07-30T13:37:27Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 11516 | 11688 |
| skipped | 112 | 121 |

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
 "after": {
  "commit": "f6b51dd07cada007bb236c84e846f95c1b1fdcb0",
  "commit_subject": "Wave 12: commission AU (contract wiring + estate restamp B1550-B1599) and AV (the sample engine B1600-B1649)",
  "captured_utc": "2026-07-30T13:37:27Z",
  "dirty": true,
  "totals": {
   "passed": 11688,
   "skipped": 121,
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
