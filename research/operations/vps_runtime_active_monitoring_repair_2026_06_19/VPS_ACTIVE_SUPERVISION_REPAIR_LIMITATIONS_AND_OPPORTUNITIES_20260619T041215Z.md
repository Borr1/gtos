# VPS Active Supervision Repair Limitations And Opportunities

Generated: `2026-06-19T04:12:15.417650Z`

## Current Findings

- Broker snapshot ok: `True`; positions total: `{'operator_profile': 2, 'redacted_account_live_bee34003': 2}`; orders total: `{'operator_profile': 0, 'redacted_account_live_bee34003': 0}`.
- Metals/gold positions: `0`.
- Runtime-learning packets parsed: `3292`; validation issues: `0`.
- Slippage merged stream rows: `8`.
- Slippage source files: `2`; non-JSON source lines explicitly recorded: `3`; mixed content detected: `True`.
- Profile audit ok: `True`; issues: `0`; warnings: `291`.

## Repairable Gaps Addressed In This Checkpoint

- Active route artifacts now preserve the fresh FTMO AUDUSD position and the prompt-required supervision ledger set.
- Route verification should use current merged slippage counts rather than the earlier fixed count.
- Canonical slippage LFS-pointer mixed content is now explicit artifact evidence instead of a silent reader assumption.

## Residuals

- Legacy index records without durable placement rows remain `ticket_policy_joinable`; fabricating missing candidate truth remains forbidden.
- redacted_account unsupported symbols remain fail-closed direct-broker gaps unless a separate broker-profile/source lane proves support.
- Scheduled task `LastTaskResult=0x800710E0` remains a noisy overlap signal under `IgnoreNew`; process and heartbeat state are the health authority.
