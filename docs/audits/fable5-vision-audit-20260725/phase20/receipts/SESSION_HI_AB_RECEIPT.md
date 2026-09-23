# Session HI Wave 20 exact full-suite A/B

**2 bad → 0 bad · 2 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `cf46792ee` | `6b72de84d` |
| captured (UTC) | 2026-08-01T14:43:36Z | 2026-08-01T16:48:42Z |
| working tree | clean | clean |
| failed | 2 | 0 |
| errored | 0 | 0 |
| **bad** | **2** | **0** |
| passed | 12809 | 13065 |
| skipped | 131 | 131 |

## Fixed (2)

- `tests/research_infra/test_session_fg_integration.py::test_session_fg_integrated_evidence_and_default_off_boundaries`
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
  "commit_subject": "phase20: register visible Sol repair sessions",
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
  "commit": "6b72de84d27e10563da102237be46e5a0180c7d6",
  "commit_subject": "docs(phase20): namespace preregistration branch labels",
  "captured_utc": "2026-08-01T16:48:42Z",
  "dirty": false,
  "totals": {
   "passed": 13065,
   "skipped": 131,
   "xfailed": 32
  }
 },
 "bad_before": 2,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [
  "tests/research_infra/test_session_fg_integration.py::test_session_fg_integrated_evidence_and_default_off_boundaries",
  "tests/test_replay_acceleration_streaming_archive.py::test_streaming_archive_seal_settles_before_publishing_segment"
 ],
 "regressed": [],
 "bad_before_nodeids": [
  "tests/research_infra/test_session_fg_integration.py::test_session_fg_integrated_evidence_and_default_off_boundaries",
  "tests/test_replay_acceleration_streaming_archive.py::test_streaming_archive_seal_settles_before_publishing_segment"
 ],
 "bad_after_nodeids": []
}
```
