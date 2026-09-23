# Wave-9 train A/B — zero to zero, +28 passing, no integration residue

**11,454 passed · 0 failed · 0 errored · 112 skipped · 32 xfailed** at `8db17b29c`,
against the wave-8 zero baseline at `b48441e4c`. NEW: 0. FIXED: 0.

The train: AL `ea6efe126` (the first sealed-α ADMIT and the population rule it exposed),
AM `93aa5532a` (the clock re-derivation and the one-hour entry lever), wave-10 commissioning
`8db17b29c`. One cross-branch resolution: both sessions added a clock-owner entry to
`generation_lineage.DEPLOYED_HELPERS` at the same anchor (AK's `structural_retest` from the
wave-8 integration, AM's `substrate`) — union, both kept, lineage suites green. The repair-queue
sidecar needed a SEMANTIC union (AL's driver re-serialised rows byte-differently while identical
as JSON): 96 base + AL 8 + AM 6 = 110, verified by canonical-JSON dedupe.

**This after-capture is the committed baseline.**

## Embedded captures

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/"
 ],
 "before": {
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
 "after": {
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
 "bad_before": 0,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [],
 "regressed": [],
 "bad_before_nodeids": [],
 "bad_after_nodeids": []
}
```
