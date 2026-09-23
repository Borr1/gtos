# A0 identity fence (a): integration candidate vs sealed wave-20 baseline

**2 bad → 2 bad · 1 fixed · **1 REGRESSED**.

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `cf46792ee` | `82a1482de` |
| captured (UTC) | 2026-08-01T14:43:36Z | 2026-08-03T16:05:12Z |
| working tree | clean | clean |
| failed | 2 | 2 |
| errored | 0 | 0 |
| **bad** | **2** | **2** |
| passed | 12809 | 13304 |
| skipped | 131 | 131 |

## REGRESSED

- `tests/test_replay_columnar_source.py::test_verification_retains_no_rows`

## Fixed (1)

- `tests/test_replay_acceleration_streaming_archive.py::test_streaming_archive_seal_settles_before_publishing_segment`

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
  "commit": "cf46792ee4823175c67eed30329cf93ba1a95a7d",
  "commit_subject": "TRANSCRIBED from sealed WAVE20_EXACT_SUITE_BASELINE.json (12,809/2/0)",
  "captured_utc": "2026-08-01T14:43:36Z",
  "dirty": false,
  "totals": {
   "passed": 12809,
   "failed": 2,
   "skipped": 131,
   "xfailed": 32
  }
 },
 "after": {
  "commit": "82a1482de3d4210dd1dbf21bbbfddb314f8f195a",
  "commit_subject": "A0: KNOWN_GHOSTS entry for B0 \u2014 the predicted WAVE20 node-id/scanner collision, adjudicated as prescribed",
  "captured_utc": "2026-08-03T16:05:12Z",
  "dirty": false,
  "totals": {
   "failed": 2,
   "passed": 13304,
   "skipped": 131,
   "xfailed": 32
  }
 },
 "bad_before": 2,
 "bad_after": 2,
 "unchanged": 1,
 "fixed": [
  "tests/test_replay_acceleration_streaming_archive.py::test_streaming_archive_seal_settles_before_publishing_segment"
 ],
 "regressed": [
  "tests/test_replay_columnar_source.py::test_verification_retains_no_rows"
 ],
 "bad_before_nodeids": [
  "tests/research_infra/test_session_fg_integration.py::test_session_fg_integrated_evidence_and_default_off_boundaries",
  "tests/test_replay_acceleration_streaming_archive.py::test_streaming_archive_seal_settles_before_publishing_segment"
 ],
 "bad_after_nodeids": [
  "tests/research_infra/test_session_fg_integration.py::test_session_fg_integrated_evidence_and_default_off_boundaries",
  "tests/test_replay_columnar_source.py::test_verification_retains_no_rows"
 ]
}
```

## Adjudication of the one listed regression — registered load-flake, verified at this head

`tests/test_replay_columnar_source.py::test_verification_retains_no_rows` is a
`KNOWN_LOAD_FLAKES` registrant (Session Y A/B evidence: passes in isolation at both that HEAD
and base). Re-verified at THIS after-commit (`82a1482de`) immediately after the capture:
**1/1 in isolation, 29/29 whole module.** `pytest_failset.py diff` on the same two captures
partitions it as LOAD-FLAKE and prints **"No regressions."** — the diff verdict, not this
receipt's raw set arithmetic, is the fence verdict. Environment note: the capture ran solo
(no concurrent agents/arms) after disk-level environment parity with the baseline worktree was
established and verified; an earlier capture attempted under concurrent agent load produced 88
spurious bad IDs and was discarded as a measurement of the load, not of the branch — its
artifact is retained in the session scratchpad only. One mid-run tree change occurred during
the DISCARDED run only (the HIA doc-leaf cherry-pick; rg-swept: zero tests read the touched
files); the fence capture of record started at the final integration HEAD and saw no tree
change at all.
