# G12 NOFILL Forward Projection Repair Hostile Edge Review 2026-05-09

Promotion posture: `NO_PROMOTION_VERDICT`.

The hostile review tried to make the repaired projection fake, leaky, under-specified, or stale. The strongest attacks were:

- A verifier could pass without reading regenerated `.context/LIVE_STATE.md`: closed by rerunning the upstream verifier after live-state regeneration and recording parsed `ok=true`.
- A broad allowlist could hide future unsafe fields: closed for current artifacts because the exhaustive allowlist is exactly equal to the emitted projection key set (`64` fields, no extras).
- Nonaccepted rows could re-enter counts: closed by recomputing `298 = 225 + 4 + 4 + 65`, source-control/source-impossible row IDs, and zero denominator delta from `47` reject-overlap rows.
- Spread fields could be misread as slippage or execution quality: closed by fixed status fields `NOT_OPENED_FOR_SOURCE_CONTROL` / `COST_TESTING_NOT_OPENED` and source-hashed tick lineage only.
- Pending-order statuses could leak broker tickets/order state: closed by status-only redaction fields and no raw ticket/order/deal/position values emitted or hashed.
- Mutable-context or line-ending hash policy could hide a real data change: bounded to mutable context snapshots and LF-normalized text drift; strict source/parser failures are `0`.
- Prior worktrees or local-heavy roots could contradict missing-source claims: no extra needed candidate matches were found in `264` prior-worktree approved log files.

Narrow acceptance is fair if all verifier checks pass: the artifact is source/control projection evidence only, not a result, validation, promotion, or live-behavior route.
