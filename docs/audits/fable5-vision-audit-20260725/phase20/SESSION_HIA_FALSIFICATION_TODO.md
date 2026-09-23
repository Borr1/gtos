# Session HIA falsification TODO

Starting authority: branch `phase20/repair-integration-falsifier`, commit
`7728701d7c5fcb9911d04ec536436bb2261b0250`, 388 sparse rules at SHA-256
`8b19788683e6ed07682b5562260bd41478f50775ebf173e50038d8b5531f7b5b`.

## HI claims to distrust until reproduced

- Four reviewed heads are ancestors through the four stated deliberate merge commits; no semantic
  side was dropped by the one manual conflict or three auto-merged overlaps.
- Current `gate_spec.v2` composes fidelity and capture authority, while explicit legacy v1 retains
  its published seal/result behavior and cannot acquire v2 authority.
- HDE remains the finite four-component, authority-backed minimal cost closure; HDF retains all
  terminal/collision/null/tie repairs and the identical seven-node HDC-to-current delta.
- CR, CS, FC and FD identities are exact; the FG, streaming-archive, HG namespace and LFS fixture
  repairs are behavioral rather than false-green or suppression changes.
- The changed-test union and exact full-suite receipts are failure-set correct, hash-correct and
  self-contained; HG's critical path is minimal and cannot cycle fallback work on a shared stop.

## Independent work

- [x] Rebuild ancestry, merge parents, changed paths, conflict bases and every HI output hash from
  Git/disk; validate the embedded `gtos-ab-receipt-v1` and exact JUnit node identities.
- [x] Diff each merge against both source parents, with line-by-line semantic review of
  `walkforward/spec.py`, `gate.py`, and the two overlapping test files.
- [x] Attack v2/current and explicit-v1 read/write/result paths: forged/missing seals, downgrade,
  schema mixing, provenance/lineage/path/symlink drift, nested mutability, replacement, duplicates,
  invalid dates, nonfinite/null precision and registrar/process-order isolation.
- [x] Reattack HDE component completeness/nonfinites/commission identity and downstream refusal;
  reattack HDF collision, gap, partial/ratchet, segmented-null, exact-tail and fold semantics.
- [x] Run the identical HDF adversarial source against exact HDC and current; independently verify
  CR/CS/FC/FD identities without opening new science outcomes.
- [x] Prove FG pointer/drift behavior, archive clock isolation/order behavior, HG namespace guard,
  pointer-only permissions failure and exact hydration repair.
- [x] Audit HG critical-path minimality: breaker -> P1; candidate-specific failure only -> O1 ->
  N1 -> FC2; shared stops halt; calibration only when learned outputs are consumed; no suppression.
- [x] Derive and run the control-to-reviewed changed-test union, compile changed Python, parse JSON,
  and run `git diff --check`.
- [x] Run the exact full suite alone if disk/process gates still pass. The first green run exposed
  two missing baseline node identities; after bounded test-only repair `5b2fe3020`, the required
  replacement run is the final authority.
- [x] Repair the bounded fidelity snapshot defect with the smallest coherent change and rerun its
  same-test A/B plus every affected targeted closure.
- [x] Preserve both full-suite JUnits without overwrite and emit the final HIA
  result/A-B/completion/map/register package.

HIA-V1 targeted executable evidence is recorded in
`receipts/HIA_TARGETED_VERIFICATION.json`. Its terminal verdict is
`READY_FOR_HIA_FULL_SUITE`; no full-suite or final HIA completion claim is made here.

## Final HIA-V2 closeout

Verdict: `SAFE_ONLY_WITH_HIA_COMMITS`.

- Unsafe integrated head: `7728701d7c5fcb9911d04ec536436bb2261b0250`.
- Required TOCTOU repair: `2e62847b57097c35f899334b0ac7ef0268eaa09c`.
- Targeted evidence head: `e7fe31fad93ec60a61fc66fb09a6187e93aaaaa5`.
- Required baseline-node identity repair: `5b2fe3020211eb7456dcd747de20dfcb1d85806d`.
- Final exact suite: 13,236 collected; 13,073 passed; 131 skipped; 32 xfailed; zero
  failed/errors; every baseline and HI node present; zero regressed IDs.
- Final durable JUnit SHA-256:
  `9c85cf52a663029a8ac6f21fbf9dbd3d731afd716a5ed6087485adca05b9345b`.
- Exact parent for the next offline science commission:
  `5b2fe3020211eb7456dcd747de20dfcb1d85806d`.

The result, independent machine verification, tool-emitted A/B receipt, completion receipt,
root-cause map and visible-session register are the final HIA evidence package. No science or live
authority was exercised.

## Fixed boundaries

No preregistered science, result-bearing replay, calibration, paper shadow, canary, broker/VPS/live
contact, credential/token read, runtime/config/activation change, March/live-forward outcome read,
push or merge. February remains attribution-only. `activation_authority: false`.

Fixture gate before tests: the exact join ledger is hydrated at 5,995,223 bytes / SHA-256
`64fd10148a1b656a31fd3687354d3e5df9cab396101ec9816b5d85d6f7a09870`; the committed sleeve
registry is hydrated at 205,754 bytes / SHA-256
`a5bcc0f81941a123d75f390e2cd7abca625de584033aad8e34d3e7898588b54e`. The older R2 contract still
expects `19365f603bc06eb0354406e0f584a33900c85c29493c625c09fe4fee9d2998fa` for the registry; this
known contract drift is recorded, not substituted away.
