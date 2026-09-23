# Wave 20 — exact hydrated suite baseline

## Decision

**BASELINE SEALED: 12,809 passed, 2 failed, 0 errored.**

This is the official pre-integration failure set for Wave 20. It was collected at control head
`cf46792ee4823175c67eed30329cf93ba1a95a7d` with the final 388-rule sparse profile, exact committed
LFS objects and receipts, and the two required external XAUUSD H4 sources locally materialized.
No application source changed during hydration.

The two failures are understood and bounded:

1. `tests/research_infra/test_session_fg_integration.py::test_session_fg_integrated_evidence_and_default_off_boundaries`
   deterministically reproduces a stale three-path R2 drift expectation. The hydrated
   `SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl` now hashes exactly to its R2 seal, so the verifier
   correctly observes only two inherited drifts while its hard-coded expectation still names
   three.
2. `tests/test_replay_acceleration_streaming_archive.py::test_streaming_archive_seal_settles_before_publishing_segment`
   is suite-order pollution in the test harness. The test monkeypatches the shared standard-library
   `time.sleep` object and therefore records sleeps from unrelated background work. The exact node
   passes alone, and the complete 37-test module passes alone. The repair is to isolate the test's
   module-local clock; no archive behavior needs to be weakened.

Neither failure is an economic, opportunity, broker-cost, exit, capture, or live-path result.

## Exact command and environment

```text
/usr/bin/time -l env PYTHONDONTWRITEBYTECODE=1 pytest -q tests/ --junitxml=/private/tmp/wave20_control_baseline_v4.xml
```

- Python: `3.14.4`
- pytest: `9.1.0`
- tests collected: `12,974`
- result: `12,809 passed, 2 failed, 131 skipped, 32 xfailed, 72 warnings`
- pytest duration: `1,459.78 s`
- measured wall: `1,462.17 s`
- maximum resident set size: `1,175,552,000 bytes`
- sparse rules: `388`, SHA-256
  `8b19788683e6ed07682b5562260bd41478f50775ebf173e50038d8b5531f7b5b`
- excluded denominator-execution `REPLAY_EXTENSION*` materialized files: `0`
- worktree status after run: clean

The durable JUnit is
`/Users/borr/GTOSColdEvidence/wave20-preservation-20260801/wave20_control_baseline_v4.xml`,
size `1,979,133` bytes, SHA-256
`65b9cddf5483be0d1e9fb90899d765a1eb9dc1da9fcffd1b888eb92b00d9b3d7`.
The exact sparse rules are preserved beside it as `wave20_control_sparse_rules.txt` with the same
rules hash stated above.

## Hydration progression

The earlier runs are diagnostics, not comparable pre-integration baselines:

| run | passed | failed | errors | skipped | xfailed | role |
|---|---:|---:|---:|---:|---:|---|
| v2 | 12,692 | 17 | 22 | 212 | 31 | unhydrated sparse/LFS diagnostic |
| v3 | 12,785 | 9 | 0 | 148 | 32 | first exact-hydration diagnostic |
| v4 | 12,809 | 2 | 0 | 131 | 32 | official final hydrated baseline |

The v2 JUnit SHA-256 is
`b2fd688d7288d82194f61c4ab25da3f5870e64a36895f4432ae438a9e7c43482`; the v3 JUnit SHA-256 is
`f65772f7780bececc874f78c2f90adb6d7d53de255a1e7ae978ca682421ede6f`.

The final v3-to-v4 materialization added only these exact inputs:

- two Task 9 acceptance/rebind receipts;
- the Task 6 prepared-pack acceptance receipt;
- the MC firm survivor book;
- the committed LFS object for the ultimate sleeve registry ledger;
- two external XAUUSD H4 CSVs, materialized in place through iCloud.

Their paths and hashes are machine-recorded in
`phase20/receipts/WAVE20_EXACT_SUITE_BASELINE.json`. The external files were read-only test inputs;
no broker, VPS, token, live service, production config, trade, or activation surface was touched.

## Failure classification proof

The FG verifier reports `265/266` checks passing and exactly one failed check,
`safety.r2_drift_inherited_exact`. Its observed drift paths are the broker net-cost engine and
ultimate candidate sleeve registry ledger. The exact join ledger SHA-256 is
`64fd10148a1b656a31fd3687354d3e5df9cab396101ec9816b5d85d6f7a09870`, matching the R2-bound value.
The verifier expectation must therefore be corrected to the two actually drifted paths, not made
to manufacture a third drift.

For the archive test, the exact node passed in isolation and its whole module completed
`37 passed` in `2.97 s`. That module JUnit is preserved as
`wave20_streaming_archive_isolation.xml`, SHA-256
`8950650ef079cc15514143e8ee1d9954836e6bff506ea80afdfae7afdb1b1ce2`.

## Post-integration A/B contract

The post-integration suite must use the same Python/pytest environment, the preserved 388-rule
sparse profile, the same exact command and collection, and failure identities rather than pass
counts. Both baseline failures may be fixed, but no new failure ID is allowed. Any fixture change,
opportunity suppression, selection narrowing, or March/live result access invalidates the A/B.

Activation authority remains **false**.
