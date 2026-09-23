# Wave-8 train A/B — zero to zero, +132 passing

**11,426 passed · 0 failed · 0 errored · 111 skipped · 32 xfailed** at `b48441e4c`,
against the zero baseline at `4dce24028`.

The train (AK `e2d12865b`, AH `3aecaa751`, AI `558bceeda` + integrations `fff431c6b`/`b48441e4c`)
landed **+132 net new passing tests** with zero regressions. The intermediate capture read 4 bad
and all four were the guard system doing its job across branches:

- **2 × `[XPASS(strict)]`** — Session AI's §6.3 repair fixed the two filed `test_mc_firm_rules`
  defects; the strict-xfail alarm flagged the repair (third firing since it shipped) and the
  KEEP-REAL rows are closed as `KEEP-REAL-RESOLVED`.
- **2 × lineage-register coverage** — Session AK's two new clock-owning sleeves demanded
  classification; `generation_lineage.py` now carries `structural_retest` in `DEPLOYED_HELPERS`
  (its raw-UTC `_hour` transcribed — its file EXISTS at `redacted_host`) and `session_leadlag` as the
  first `NO_DEPLOYED_LINEAGE` entry. The invariant is a two-way classification and still exact.

One cross-branch semantics decision is recorded in the AI merge commit: `spec.canonical()` treats
`"v1_multiplicative"` (not None) as the pre-field spread composition, so historical seals
reproduce from specs that behave as those runs behaved, and default (v2-behaving) specs seal
differently — a drop-when-None rule would have hashed two different-behaving specs identically.

**This after-capture is the committed baseline.** Diff with
`python3 scripts/pytest_failset.py diff baseline <after.json>`.

## Embedded captures

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/"
 ],
 "before": {
  "commit": "4dce24028fea1cc54294d57f8665babb782a673f",
  "commit_subject": "Close 8 KEEP-REAL rows the strict-xfail alarm flagged on its first firing",
  "captured_utc": "2026-07-30T01:46:15Z",
  "dirty": true,
  "totals": {
   "passed": 11294,
   "skipped": 111,
   "xfailed": 34
  }
 },
 "after": {
  "commit": "b48441e4c9af2e1e81b2071f242b94b8a9387477",
  "commit_subject": "Train integration: the lineage register learns AK's two clock sleeves, and two more filed defects close",
  "captured_utc": "2026-07-30T02:56:30Z",
  "dirty": true,
  "totals": {
   "passed": 11426,
   "skipped": 111,
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
