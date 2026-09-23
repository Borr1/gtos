# V235R3 Active Artifact Requirements And Storage Checkpoint

Generated UTC: 2026-07-12T11:56:15Z.

## Checkpoint State

- Active targeted prefix:
  `BROAD_LIVE_AS_IF_REPLAY_V235R3_B7_2_EARLY_TERMINAL_BLOCKER_CONTRACT_20260514_US30_REPAIRED_ONLY`.
- Route checkpoint commit: `3d6625b0eba039cf47b018bdbb361f792f1585af`.
- Route verifier: `ok=true`, `issue_count=0`.
- Integrated barrier: `2,021 passed`, with one unchanged pytest configuration
  warning.
- Prompt hardening, standard route artifact audit, compile, and whitespace
  checks: green.
- Broker/live/final authority: false.
- Disk before cleanup: 19 GiB available on `/System/Volumes/Data`.
- V235R3 artifact family: 25 files, 425,255,203 bytes (405.555 MiB).

## Protected Requirements

The bounded cleanup must retain:

- every tracked file and every current code, config, test, builder, analyzer,
  verifier, control, summary, manifest, and comparison artifact;
- the complete V235R3 replay, flow, parity, leakage, projection, source,
  candidate, decision, scorecard, order, trade, missed, and comparison family;
- the complete V219 hostile-five-day family as the exact same-window baseline
  for the next B7.2 replay;
- all version summary JSON, behavior dossiers, comparison summaries, repair
  plans, and manifests for prior V92/V104/V128/V150/V211/V220-V235 families;
- Phase2 denominator/replay bridge evidence, reconstructed-denominator evidence,
  source-bound reservoir evidence, broker-cost evidence, and MT5 tick/source
  evidence;
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`, the Fable matrix, current
  pre-replay brief, continuation controls, and this protection record.

Superseded raw replay/parity JSONL shards are not protected merely because their
compact summary remains useful. Their final summaries, comparisons, manifests,
and hashes remain on disk, and the next objective-regime proofs will run the
current code rather than reuse stale executable-policy raw rows.

## Integrity Anchors

- `OUTPUT_MANIFEST.json`:
  `56905fbf9b82993df6de793c2cf5ce79c0b35c47b3f19268049155954d1b0251`.
- `VERIFICATION_RESULT.json`:
  `115fc1130be486ac1ad657334e080c1ad71cd0851edeefac22a540b81999a8ed`.
- V235R3 replay summary:
  `2bb928ff9972a58af2ce41aacb145e3ed9d70d50744254bd7c8e9a4e8d18791f`.
- V235R3 parity summary:
  `3322f64868b2e9566fcd55e37ec69f355f87e778cfd314d2d2cca206123fef2c`.
- V235R3 flow summary:
  `6ff17a1bd574d48c54806a88a4b6ba9d3af62aacab4a673c4653f5f3c834724f`.
- V235R3-vs-V235R2 behavior summary:
  `04a2c3dcf3e69e348472c0d2ea5653a759e21cc85fc0f61882cf5c6e841dc67e`.

## Bounded Cleanup Contract

The dry-run selector found 44 files totaling 39,705,520,130 logical bytes
(36.979 GiB). A file is eligible only when every condition is true:

- it is an ignored, untracked `.jsonl` file;
- it is larger than 100 MiB;
- its basename is a broad-replay, source-bound parity, or candidate-instance
  parity-projection raw ledger;
- it is not in the V235R3 current family or V219 hostile baseline family.

No tracked file, V235R3 file, V219 file, JSON summary, manifest, code/config/test
file, source evidence, Phase2 bridge artifact, broker-cost artifact, MT5 data, or
control file may be removed. `git clean` is forbidden. Re-run the selector at
deletion time and record the actual count, logical bytes, free-space delta,
remaining eligible count, and post-cleanup anchor validation.
