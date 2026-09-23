# VPS Active Supervision Repair Limitations And Opportunities

Generated: `2026-06-19T08:00:15.654081Z`

## Current Findings

- Broker snapshot ok: `True`; positions total: `{'operator_profile': 2, 'redacted_account_live_bee34003': 1}`; orders total: `{'operator_profile': 0, 'redacted_account_live_bee34003': 0}`.
- Metals/gold positions: `0`.
- Runtime-learning packets parsed: `4150`; validation issues: `0`.
- Slippage merged stream rows: `13`.
- Slippage source files: `2`; non-JSON source lines explicitly recorded: `3`; mixed content detected: `True`.
- Profile audit ok: `True`; issues: `0`; warnings: `291`.

## Repairable Gaps Addressed In This Checkpoint

- Active route artifacts now preserve the current read-only broker/packet/profile state and the prompt-required supervision ledger set.
- Route verification should use current merged slippage counts rather than the earlier fixed count.
- Canonical slippage LFS-pointer mixed content is now explicit artifact evidence instead of a silent reader assumption.
- Supervisor heartbeat JSON with a UTF-8 BOM is parsed as valid JSON instead of being recorded as a decode error.
- `GTOS_W7_BookSupervisor` task result `0x800710E0` is classified as `running_ignore_new_overlap_not_process_failure` when `MultipleInstances=IgnoreNew` and the supervisor heartbeat is fresh.
- Broker recent-deal queries use broker-server offset-aware MT5 history windows and preserve UTC-normalized deal timestamps.
- Cross-namespace packet append inversions are classified separately from same-namespace timestamp regressions.

## Residuals

- Legacy index records without durable placement rows remain `ticket_policy_joinable`; fabricating missing candidate truth remains forbidden.
- redacted_account unsupported symbols remain fail-closed direct-broker gaps unless a separate broker-profile/source lane proves support.
- Scheduled task overlap remains intentionally non-fatal; process and heartbeat state are the health authority.
