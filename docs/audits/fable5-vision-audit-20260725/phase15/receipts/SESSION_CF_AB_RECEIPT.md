# Session CF — scoped A/B vs the ZERO baseline

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `02edf909a` | `99670b502` |
| captured (UTC) | 2026-07-31T05:31:16Z | 2026-07-31T07:43:53Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 12403 | 3193 |
| skipped | 120 | 10 |

## Scope difference — declared, not hidden

- before: `['tests/']`
- after : `['tests/ultimate_book', 'tests/safety', 'tests/research_infra']`

**Why this is still a comparison:** Before is the committed whole-suite ZERO baseline (12,403 passed / 0 failed, commit 02edf909a). After is scoped to the blast radius of CF's changes — tests/ultimate_book tests/safety tests/research_infra, the only directories importing gtos_command_center, symbol_map, symbol_resolution_watch, book_owner or book_engine. Because the before side has ZERO failures suite-wide, any failure appearing in the after scope is a regression, so the scope difference can only make this comparison stricter, never laxer. The after capture is at CF's own commit 99670b502, with every source and test change COMMITTED; the 'dirty' flag reflects one untracked file — this receipt's own earlier draft — and no source, test or config byte.

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
  "commit": "02edf909ad108615daa84568834246d6bdc0e8d8",
  "commit_subject": "H-CB-2 run: the trusted key is measured clean at 44.3M hits; three memos are measured dirty and CD is bound to the safe set",
  "captured_utc": "2026-07-31T05:31:16Z",
  "dirty": true,
  "totals": {
   "passed": 12403,
   "skipped": 120,
   "xfailed": 32
  }
 },
 "after": {
  "commit": "99670b50278d69ab644557967d80b3d03d3fceeb",
  "commit_subject": "Session CF: the FTMO rename did not happen \u2014 the canonical/broker name-space error, refuted with the broker's own tree, and the silence it exposed is now a watchdog",
  "captured_utc": "2026-07-31T07:43:53Z",
  "dirty": true,
  "totals": {
   "passed": 3193,
   "skipped": 10,
   "xfailed": 3
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
   "tests/ultimate_book",
   "tests/safety",
   "tests/research_infra"
  ],
  "justification": "Before is the committed whole-suite ZERO baseline (12,403 passed / 0 failed, commit 02edf909a). After is scoped to the blast radius of CF's changes \u2014 tests/ultimate_book tests/safety tests/research_infra, the only directories importing gtos_command_center, symbol_map, symbol_resolution_watch, book_owner or book_engine. Because the before side has ZERO failures suite-wide, any failure appearing in the after scope is a regression, so the scope difference can only make this comparison stricter, never laxer. The after capture is at CF's own commit 99670b502, with every source and test change COMMITTED; the 'dirty' flag reflects one untracked file \u2014 this receipt's own earlier draft \u2014 and no source, test or config byte."
 }
}
```
