# V232R2 Active Artifact Requirements And Storage Checkpoint

Generated UTC: 2026-07-12T01:26:18Z.

## Checkpoint State

- Active targeted prefix:
  `BROAD_LIVE_AS_IF_REPLAY_V232R2_B7_2_SIGNED_FINALIZER_CAUSAL_PARTITION_20260514_US30_REPAIRED_ONLY`.
- Route checkpoint commit: `101c6850f`.
- Route verifier: `ok=true`, `issue_count=0`.
- Integrated barrier: `1545 passed`, with one unchanged pytest configuration
  warning.
- Prompt hardening and standard route artifact audit: green.
- Broker/live/final authority: false.
- Disk before cleanup: 16 GiB free on `/System/Volumes/Data`.
- V232R2 artifact family: 25 files, 421,509,788 bytes (401.98 MiB).

## Protected Requirements

The bounded cleanup must retain:

- all tracked files;
- current code, config, tests, route builders, analyzers, and verifiers;
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`, the Fable execution
  matrix, pre-replay brief, and continuation controls;
- current `OUTPUT_MANIFEST.json`, `VERIFICATION_RESULT.json`, and route summary;
- all V232R2, V232, V231, and V230 replay, flow, parity, leakage, projection,
  and comparison artifacts;
- the V220R16 canonical terminal-identity proof family;
- V219 hostile five-day, V211 and V92 hostile comparators, and V104/V128/V150
  non-hostile comparator families;
- all version summary JSON, behavior dossiers, repair plans, and manifests;
- reconstructed denominator, Phase2 bridge, source-bound reservoir, broker-cost,
  and MT5 tick/source evidence outside superseded broad-replay raw families.

## Integrity Anchors

- `OUTPUT_MANIFEST.json`:
  `091fa8daba60f35d9b6425a0c8fe33ed4ff0aae49b2fffe13a529f81c99c101a`.
- `VERIFICATION_RESULT.json`:
  `898712935b162e4d6db8473109c789e043ca84e74f4c9ccc2088317f4889bdb1`.
- V232R2 replay summary:
  `70c15e80103ed5b1162391f7477124499e601292a03109786341dd71a9d5be5c`.
- V232R2 parity summary:
  `32a428e03df0f53e8f5b30a1cbc4ac8ca8c46c6ea7fbee80f10089a183e3e99f`.
- V232R2 flow summary:
  `16ba5991a17b6db1a52702d0ddc9f8be74f063fb538677e55623b03741f50ccf`.
- V232R2-vs-V232 behavior summary:
  `bcf3ac9e362c435fd43dbc7ebe5cebfa72883c1ce131887ff1ec727ad48401f3`.

## Bounded Cleanup Contract

The dry-run selector found 919 files totaling 347,731,126,223 logical bytes
(323.850 GiB). A file is eligible only when every condition is true:

- it is an ignored, untracked `.jsonl` file;
- it is larger than 100 MiB;
- its basename is a broad-replay, source-bound parity, or candidate-instance
  parity-projection raw ledger;
- it is not in any protected current or comparator family listed above.

No tracked file, JSON summary, manifest, code/config/test file, source evidence,
MT5 data, active proof family, or required comparator may be removed. Do not use
`git clean`. Re-run the same selector at deletion time and record actual count,
logical bytes, free-space delta, and post-cleanup anchor validation.
