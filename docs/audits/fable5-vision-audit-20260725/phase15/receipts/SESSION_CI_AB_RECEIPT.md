# Session CI — scoped A/B vs the ZERO baseline

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `d312e06e3` | `7fcb4400c` |
| captured (UTC) | 2026-07-31T10:22:21Z | 2026-07-31T11:55:32Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 12476 | 22 |
| skipped | 120 | 0 |

## Scope difference — declared, not hidden

- before: `['tests/']`
- after : `['tests/research_infra/test_ci_thirdparty_m1.py', 'tests/test_implementation_state_block_citations.py']`

**Why this is still a comparison:** Before is the committed whole-suite ZERO baseline at d312e06e3 (12,476 passed, 0 failed, 0 errors). After is the mechanically computed two-file import/citation closure for CI: tests/research_infra/test_ci_thirdparty_m1.py and tests/test_implementation_state_block_citations.py. A ZERO baseline means any bad test in that after scope is a regression. The CI test file is new and cannot exist on the before side; the one shared pre-existing test was separately exercised by mandated copy-back, never git checkout, at 9 passed -> 9 passed with 0 regressed in SESSION_CI_COPYBACK_AB_RECEIPT.md. The after capture is at 7fcb4400c with all code/tests/evidence committed; its dirty flag is only the mechanically regenerated .context/LIVE_STATE.md, not source, test, config, or receipt bytes.

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
  "commit": "7fcb4400ca9b7ebf18fb23e1979f85434b74ccf0",
  "commit_subject": "Close Session CI with verified structural stop",
  "captured_utc": "2026-07-31T11:55:32Z",
  "dirty": true,
  "totals": {
   "passed": 22
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
   "tests/research_infra/test_ci_thirdparty_m1.py",
   "tests/test_implementation_state_block_citations.py"
  ],
  "justification": "Before is the committed whole-suite ZERO baseline at d312e06e3 (12,476 passed, 0 failed, 0 errors). After is the mechanically computed two-file import/citation closure for CI: tests/research_infra/test_ci_thirdparty_m1.py and tests/test_implementation_state_block_citations.py. A ZERO baseline means any bad test in that after scope is a regression. The CI test file is new and cannot exist on the before side; the one shared pre-existing test was separately exercised by mandated copy-back, never git checkout, at 9 passed -> 9 passed with 0 regressed in SESSION_CI_COPYBACK_AB_RECEIPT.md. The after capture is at 7fcb4400c with all code/tests/evidence committed; its dirty flag is only the mechanically regenerated .context/LIVE_STATE.md, not source, test, config, or receipt bytes."
 }
}
```
