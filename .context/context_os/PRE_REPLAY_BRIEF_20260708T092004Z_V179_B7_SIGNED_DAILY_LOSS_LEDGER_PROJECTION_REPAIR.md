# V179 B7 Pre-Replay Brief - Signed Daily-Loss Ledger Projection Repair

Generated UTC: 2026-07-08T09:20:04Z

## Control State

- Fable ladder active batch: B7 package replay conversion and scheduler/order/risk transfer.
- Broker/live/final: closed. Local replay/package authority: full.
- This is not a broad replay. It reruns the same 2026-06-04..2026-06-05 XAUUSD targeted slice because V178 proved behavior but the artifact rows did not expose the full cooldown-release diagnostics.

## Latest Completed Replay

V178 prefix:
`BROAD_LIVE_AS_IF_REPLAY_V178_B7_SIGNED_DAILY_LOSS_QUALITY_FLOOR_REPAIR_20260604_20260605_XAUUSD_TARGETED`

V178 result:
- candidates/scorecards/orders/trades/missed: 1130 / 184 / 12 / 5 / 1124
- net/gross/final R: +0.86245094 / +1.32715957 / +1.32715957
- W/L/F: 4 / 1 / 0
- cost-refused/source-gap executed: 0 / 0
- added vs V177: `broadorigin_62cb335107ef114d9725321c@@2026-06-04T17:45:00+00:00`, +0.29090804R.

## Patch Since V178

- Behavior-neutral ledger repair in `risk_authority_reduction_ledger_fields`.
- Adds consumed order/trade projection for:
  - `package_cooldown_release`
  - `package_cooldown_release_applied`
  - `package_cooldown_release_reason`
  - `package_cooldown_release_original_reason`
  - `package_cooldown_release_signed_executable_authority_quality_release`
  - `package_cooldown_release_signed_executable_authority_release_eligible`
  - `package_cooldown_release_signed_executable_order_allowed`

Focused tests:
- py_compile passed.
- 6 focused B7 tests passed, 575 deselected, 1 warning.

## Expected V179 Effect

- Behavior should be neutral versus V178: same 5 trades, same net R +0.86245094, same W/L/F 4/1/0, no cost-refused/source-gap executions.
- Artifact effect: the recovered 17:45 order/trade rows should expose the signed-executable cooldown-release fields at top level.

## Success / Failure Criteria

Success:
- V179 behavior matches V178 within deterministic replay tolerance.
- The 17:45 filled trade/order rows include `package_cooldown_release_applied=true`, reason `package_signed_executable_authority_daily_loss_lockout_release_predecision_pass`, and signed-executable quality release `eligible=true`.

Failure:
- Any cost-refused/source-gap row executes.
- Trade set changes unexpectedly.
- The cooldown-release fields remain absent from filled order/trade rows.
