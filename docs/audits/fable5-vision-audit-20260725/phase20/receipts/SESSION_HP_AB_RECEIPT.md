# Session HP Canonical P1 Source-Control A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

## Authority and measurement boundary

- `execution_authority: false`
- `activation_authority: false`
- `result_bearing_science_executed: false`
- `broker_orders: 0`
- `result_use_status: SOURCE_CONTROL_ONLY_NO_OUTCOME_READ`
- `exact_r: NOT_READ_SOURCE_CONTROL_ONLY`
- `proxy_r: NOT_READ_SOURCE_CONTROL_ONLY`
- `expectancy: NOT_READ_SOURCE_CONTROL_ONLY`
- `measurement_scope: COMMON_PARENT_SOURCE_TEST_SURFACE`
- `added_packet_m1_cases: 59`
- `added_packet_m1_capture_sha256: 460d56bdb5d149264bc3c6b1745ed062e089cc3c0ec500b26d0f7987d4d0ae84`

The parent does not contain the two newly added packet/M1 test files, so the self-contained A/B
compares the exact test paths present on both sides. The 59 added packet/M1 cases are captured
separately and passed; they were not forced into an unusable parent baseline.

| | before | after |
|---|---|---|
| commit | `f59fbb829` | `9059cfa06` |
| captured (UTC) | 2026-08-02T02:27:31Z | 2026-08-02T02:27:31Z |
| working tree | clean | clean |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 45 | 52 |
| skipped | 0 | 0 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "--disable-warnings",
  "-p",
  "no:cacheprovider",
  "tests/research_infra/test_p1_upstream_reconstruction.py",
  "tests/research_infra/test_wave20_complete_path_shadow.py"
 ],
 "before": {
  "commit": "f59fbb829a5561b7e7b78bed324d67a8c01d6e74",
  "commit_subject": "phase20: reconstruct P1 upstream source packet",
  "captured_utc": "2026-08-02T02:27:31Z",
  "dirty": false,
  "totals": {
   "passed": 45
  }
 },
 "after": {
  "commit": "9059cfa0659f710dc56ba779181770468d5450f1",
  "commit_subject": "fix(phase20): accept hash-proven sparse M1 bars",
  "captured_utc": "2026-08-02T02:27:31Z",
  "dirty": false,
  "totals": {
   "passed": 52
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
