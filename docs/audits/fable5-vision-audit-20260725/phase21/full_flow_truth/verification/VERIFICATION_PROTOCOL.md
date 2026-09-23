# Wave 21 verification baseline and equal-scope protocol

## Outcome

The clean commission checkout is not green in its ten-cone sparse state. The exact clean
baseline at `95719539797b22776642e9e24e2e208b0aa801c4` is **1,036 bad identities**:
11,919 passed, 936 failed, 100 collection/setup errors, 235 skipped and 30 xfailed. The
capture is complete and usable. It ran for 771.24 seconds and reached 934,477,824 bytes
maximum RSS.

An explicitly different, reviewed fixture context materialised 28 exact committed files
(10,640,199 bytes; one hydrated LFS object) without network access or sparse-rule widening.
That diagnostic found **217 bad identities**: 13,041 passed, 191 failed, 26 errors, 227
skipped and 30 xfailed. It ran for 1,079.79 seconds and reached 1,070,825,472 bytes maximum
RSS. This is not an A/B result and the 819-net-bad reduction is not a code fix. The strict
guard refuses the comparison because the sparse, LFS and fixture roots differ; it records
835 diagnostic-only removed identities and 16 diagnostic-only added identities, with no
`fixed` or `regressed` claim.

Neither run was a result-bearing strategy replay. Neither contacted a host or broker, read
token material, changed live configuration, or established activation authority.

## Machine and dependency boundary

- macOS 26.5.2, arm64, 10 logical CPUs, 16 GiB memory; 35 GiB free at closeout.
- CPython 3.14.4 at `/opt/homebrew/opt/python@3.14/bin/python3.14`; pytest 9.1.0.
- Selected imports/versions: numpy 2.4.4, pandas 3.0.2, scipy 1.17.1,
  scikit-learn 1.8.0, pyarrow 23.0.1, PyYAML 6.0.3, anyio 4.13.0 and orjson
  3.11.9. `MetaTrader5`, `pytest_asyncio` and `sentence_transformers` are absent.
  The suite emits one `asyncio_mode` unknown-option warning because `pytest_asyncio` is
  absent. Do not install or remove packages between A and B.
- Dependency fingerprint:
  `39b0ccf04a7f0bf6997c36086454591f45f37975a6f8124f41a8577169101cf7`;
  91-distribution inventory root:
  `c90e9367a58499a6736a0528b5e0a9566ed5ed0ba092a87c1fbf108ccadf8ebb`.
- Git LFS 3.7.1 is configured with smudge/process `--skip`. At the clean baseline all
  4,151 tracked LFS paths were sparse-absent. The reviewed tier hydrates exactly one local
  object and leaves 4,150 absent. A missing local object is a stop; the protocol never
  silently downloads it.
- Sparse checkout is cone mode with ten patterns: `.context`, `config`, `docs`, the three
  broker/spread truth routes, the Wave 19 broad forensic route, `scripts`, `src`, and
  `tests`. The clean root is
  `a3bee90aa2d9b95076b7d01a4819579fd1ebcaaa8f446fa499dc43965bab821a`;
  the reviewed-fixture root is
  `3a7a2a151e068236aea635ab736ff3f36f4c66f2da3822aed1e4ee2823f2917e`.

The repository helper `scripts/gtos_hydrate_test_data.py` is not used here: in this cone
worktree it passes leading-slash non-cone patterns to `git sparse-checkout add`, which Git
rejects. `wave21_verification.py hydrate-required` instead checks out only a reviewed
allowlist with `--ignore-skip-worktree-bits`, hydrates an already-local LFS object, caps the
total bytes, refuses any `REPLAY_EXTENSION` path, and does not change sparse rules.

## Exact commands

Regenerate context before each serious run:

```bash
python3 scripts/generate_live_state.py
python3 scripts/gtos_context.py build
python3 docs/audits/fable5-vision-audit-20260725/phase21/full_flow_truth/verification/wave21_verification.py context-pack \
  --task "Wave 21 full-flow truth verification baseline, equal-scope sparse-worktree A/B, integrity gates, and offline host-parity verification" \
  --include-memory -o docs/audits/fable5-vision-audit-20260725/phase21/full_flow_truth/verification/ULTIMATE_CONTEXT_PACK.md
```

Capture the monolithic suite (the output path must identify the commit and context):

```bash
/usr/bin/time -l env -u FORCE_COLOR NO_COLOR=1 PY_COLORS=0 \
  PYTHONDONTWRITEBYTECODE=1 python3 scripts/pytest_failset.py capture \
  -o <capture.json>
```

Plan or apply exact offline hydration:

```bash
python3 docs/audits/fable5-vision-audit-20260725/phase21/full_flow_truth/verification/wave21_verification.py \
  hydrate-required --max-bytes 20971520 -o <plan.json>
python3 docs/audits/fable5-vision-audit-20260725/phase21/full_flow_truth/verification/wave21_verification.py \
  hydrate-required --apply --max-bytes 20971520 -o <applied.json>
```

Capture the context beside each pytest capture, then compare only through the guard:

```bash
env -u FORCE_COLOR NO_COLOR=1 PY_COLORS=0 PYTHONDONTWRITEBYTECODE=1 \
  python3 docs/audits/fable5-vision-audit-20260725/phase21/full_flow_truth/verification/wave21_verification.py \
  inspect --base 9392e9bbddb9eddfb5dc51ef36bc2d7ff7e8f285 \
  --baseline <capture.json> --wall-seconds <seconds> --max-rss-bytes <bytes> \
  -o <inspection.json>
python3 docs/audits/fable5-vision-audit-20260725/phase21/full_flow_truth/verification/wave21_verification.py \
  ab-guard --before-capture <A.json> --after-capture <B.json> \
  --before-inspection <A-context.json> --after-inspection <B-context.json> \
  -o <ab.json>
```

`ab-guard` requires both captures to say `parse_complete=true` and
`usable_as_baseline=true`. Each `inspect` call must receive its corresponding capture via
`--baseline`. The guard binds pytest argument order, selected-test materialization,
dependency, LFS, fixture and controlled-environment roots plus sparse enabled/cone state
and the exact ordered pattern list. Full tracked materialized/skipped path inventories stay
in the receipt as diagnostics; expected commit-added paths do not define context drift.
The comparison contract has a closed key set and its complete scope hash must match across
the pair. Missing selected tests, changed sparse patterns, unknown contract keys, or tampered
context hashes fail closed.
Only `NO_REGRESSION` with `same_scope=true` supports an A/B statement.

Guarded captures use a deliberately closed pytest selection grammar: pass literal repository
test paths or nodeids after `--`. Pytest option forms, `--pyargs`, configuration/root overrides,
and `@argfile` selectors are not interpreted or hash-bound by this verifier and therefore make
the inspection unavailable for A/B rather than falling back to a guessed `tests/` scope.

## Failure identity and flake policy

Failure identity is the normalized pytest node ID, not a count: Unicode NFC, forward path
separators, no leading `./`, and parameter IDs preserved. The parser strips ANSI escapes,
forces color off even when its parent exported `FORCE_COLOR`, and separately retains
collection/setup `ERROR` identities. The adversarial tests cover colored summaries,
Windows separators, non-zero returns with unparseable output, duplicate identities, and
parent color leakage.

No failure is suppressed as a flake. A suspected flake remains in the bad set until the
exact node and its containing module are rerun, with recorded attempt counts, at both A and
B under the same context hash. A final monolithic run is still required after shards to
catch suite-order effects.

## Shards and focused lanes

The deterministic four-way whole-file plan covers all 707 discovered test files with zero
overlap and zero missing files. In the reviewed fixture context collection returned 1 but
yielded 13,506 node IDs (root
`b5b85d04835e05f2511006945c8e756ceb4d4d5a39b2d2d2a88ffc19e53c0a89`).
The four estimated weights are 3,380 each. Run shards sequentially by default with
`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1`; parallel replay-like
tests would compete with active research. Budget roughly 13–20 minutes and up to 1.1 GB
RSS for a monolithic run on this machine; shard timing must be measured rather than inferred.

Focused suite ownership is encoded in the inspection receipt:

- candidate generation: candidate path, origin registry, broad-origin emission repairs;
- selector: Selector V4 and permissions;
- scheduler/risk: scheduler allocator and timewarp materialisation;
- quote/execution/lifecycle: quote side, execution, lifecycle and exit policy;
- cost truth: broker net-cost engine and costs layer;
- offline live flow: importability, account identity, book owner and armed-set source;
- W7/divergence: W7 re-cost and divergence matrix;
- verification tooling: fail-set parser and Wave 21 verifier tests.

Use the command emitted for each lane by `inspect`. Focused success does not replace the
monolithic failure-set certification.

## Integrity gates

At commission HEAD, the 5 MiB normal-Git-blob check found 303 inherited blobs totalling
5,441,979,623 bytes and **zero new blobs since the reviewed base**. The high-confidence
tracked-text secret scan found three inherited redacted test-fixture matches and **zero new
matches**; matched values are never emitted. The static AST first-party import-closure gate
resolved every named lane entrypoint, inventory root
`f7f7fcc5b3eeade6b1898e80f8bf547eb768b1b232916fa22bc9183431a012e1`.
Two identical detailed inspection passes produced deterministic hash
`a9495e00437212b0cdda62fb0f6559e9f3a2900d46d4271e11a2a62febe2f384`;
generation time is deliberately excluded.

## Offline host-parity boundary

`verify_host_parity.py` consumes only a canonical-SHA-256-bound JSON export conforming to
`HOST_OBSERVATION_SCHEMA.json`. It compares worker argument boundaries (namespace, profile,
tags, frontier exits and spread-geometry floor), runtime and token config digests, host and
preservation HEAD, launcher bytes, the local declaration, and the local launcher. It also
requires explicit observations of the host armed-set module and manifest. It has no host,
broker, network, token-read or mutation path.

A fresh matching receipt can report `CURRENT_MATCH`; a fresh mismatch reports
`CURRENT_MISMATCH`; an expired receipt always reports `STALE_NOT_CURRENT` and cannot claim
current state; malformed, overlong-validity or hash-tampered evidence is
`INVALID_RECEIPT`. The adversarial FTMO fixture proves that host `frontier=crypto` versus
local empty frontier plus absent host module/manifest is detected as a current mismatch.
That fixture is a tooling proof, not a fabricated host observation. Until an authorized
collector supplies a valid unexpired export, no current host parity is established.

## Evidence index

- `receipts/WAVE21_SPARSE_BASELINE_957195397.json`: clean minimal-cone capture.
- `receipts/WAVE21_REVIEWED_FIXTURE_BASELINE_957195397.json`: dirty verification-only,
  reviewed-fixture diagnostic capture.
- `receipts/WAVE21_MINIMAL_CONE_CONTEXT.json` and
  `receipts/WAVE21_REVIEWED_FIXTURE_CONTEXT.json`: compact fingerprints and gates.
- `receipts/WAVE21_MINIMAL_VS_REVIEWED_GUARD.json`: fail-closed incomparable result.
- `receipts/WAVE21_SHARD_PLAN.json`: deterministic file shards.
- `receipts/WAVE21_INSPECTION_DETERMINISM.json`: two-run output-hash proof.
- `receipts/WAVE21_TOOLING_TESTS.json`: focused parser/verifier result.
