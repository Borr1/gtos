# Failure-set A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `f6b51dd07` | `30f031e64` |
| captured (UTC) | 2026-07-30T13:37:27Z | 2026-07-30T15:37:52Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 11688 | 11843 |
| skipped | 121 | 121 |

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
 "after": {
  "commit": "30f031e640443feefa2233ff0a5fa75813976bc2",
  "commit_subject": "De-arm source claims found structurally, not by line number \u2014 the train collision CLAUDE.md \u00a76 warns about",
  "captured_utc": "2026-07-30T15:37:52Z",
  "dirty": true,
  "totals": {
   "passed": 11843,
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
