# Wave-16a train — full-suite A/B, four sessions, one capture

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `ce40cd566` | `6608eb969` |
| captured (UTC) | 2026-07-31T12:08:02Z | 2026-07-31T17:26:48Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 12522 | 12600 |
| skipped | 120 | 120 |

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
  "commit": "ce40cd566f80cd4c4845b8d48b3cb27cc2f14ec7",
  "commit_subject": "Merge Session CD: the regeneration lands \u2014 the repairs make the family worse, and the deficit was never the cost model",
  "captured_utc": "2026-07-31T12:08:02Z",
  "dirty": true,
  "totals": {
   "passed": 12522,
   "skipped": 120,
   "xfailed": 32
  }
 },
 "after": {
  "commit": "6608eb969297ed8cbe218662f3987344a576bc6c",
  "commit_subject": "Merge Session CI: the vp time-depth blockade is solved; the comparability gate honestly refuses",
  "captured_utc": "2026-07-31T17:26:48Z",
  "dirty": true,
  "totals": {
   "passed": 12600,
   "skipped": 120,
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

Sessions merged in this train, in order: **CG** (`18b9a7efd`, lane footprint B2400–B2449),
**CK** (`15c058a46`, mechanism autopsy B2600–B2615), **CH** (`fb374156f`, lever measurements
B2450–B2467), **CI** (`6608eb969`, third-party M1 B2500–B2549).

Integration notes of record: the `cuts.py` merge was semantic — the auto-merge DUPLICATED
`make_ledger_projection_patch`/`make_missed_pool_projection_patch` (CD's + CG's copies,
silent Python last-wins), caught by symbol-diff before commit; resolution took CG's whole
file (measured supersession: `Sequence` out of the ABC rebind on 47,444,764 wrong per-call
checks, v2 memos off as net-negative, reader-complete projections default-on), renamed the
lane test's two `_project_row` call sites to `_project_scalar_row`, and re-pinned CD's three
off-by-default policy tests to CG's contract with the protective halves kept (dirty memos
excluded, `sealed_compatible=False` on every projection). CH∩CK iteration-ledger add/add
resolved by row union (CD 14 + CK 1,903 + CH 12 = 1,929 rows). Baseline advanced to this
capture; diff with `scripts/pytest_failset.py`, never re-capture the before side.

The original train note named integration commit `dbdead310` as the before **tree**, while
the committed capture it advanced from names `ce40cd566`, the Session CD merge contained by
that tree. This self-contained form reports the capture's exact commit, as the tool does.
