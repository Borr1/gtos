# V121D Exact-Bound Soft-Probe Risk Transfer Pre-Replay Brief

Broker/live/final remain closed. Local replay/package authority remains full. This is a bounded one-day same-root repair proof, not a full-reservoir conversion claim.

## Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V121C_SELECTOR_SCHEDULER_RISK_TRUTH_20260515_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`
- Window: `2026-05-15..2026-05-15`
- Candidate ledger: omitted
- Scorecards / order events / unique orders / trades / missed: `96 / 26 / 13 / 4 / 8161`
- Expired unfilled: `9`
- Net R: `-3.80274600`
- Gross/final R: `-3.36900465`
- Cash PnL / risk cash / risk pct: `-947.38489674 / 995.84992526 / 1.0`
- W/L/F: `0/4/0`
- Executed REFUSED/source-gap rows: `0`

V121C improved proof visibility but did not change behavior: the same four reduced-risk losers filled and the same transfer blockers remained.

## Active Process State

No broad replay, pytest, or stale git helper is running. The killed stale `git add` left no staged files. Disk has about 12 GiB free.

## Baseline Context

Do not compare this one-day smoke directly to the global million-R reservoir. V89D/V90/V92 are hostile five-day comparators; V120F/V121C are same-day local baselines.

| Run | Window | Trades | Net R | Gross/Final R | Cash | W/L/F |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| V89D | 2026-05-13..17 | 56 | +34.84520454 | +39.93441037 | +8178.90660707 | 41/15/0 |
| V90 | 2026-05-13..17 | 51 | +28.84201157 | +33.36349114 | +6371.80465431 | 37/14/0 |
| V92 | 2026-05-13..17 | 51 | +29.35570236 | +33.93212860 | +6228.63096022 | 37/14/0 |
| V120F | 2026-05-15 | 4 | -3.80274600 | -3.36900465 | -947.38489674 | 0/4/0 |
| V121C | 2026-05-15 | 4 | -3.80274600 | -3.36900465 | -947.38489674 | 0/4/0 |

## Subagent Findings

- Jason: incorporated. Keep `6450` cost-refused rows non-executable. Target the cost-passed `835/826` fill-floor/zero-risk chain with signed bounded risk intent.
- Popper: incorporated. The exact root bug was stale `runtime_eligible=false` and zero selected/requested risk surviving into finalizer authority even after a soft probe proved executable.
- Tesla: incorporated. The next root fix should be selector/scheduler materialization before stop/exit, because the largest positive missed pool is not the four filled losers.

## Same-Root Patch

Correctness repair:

- Exact-bound soft probes now restamp `runtime_eligible=true`, clear stale vetoes, and transfer bounded `risk_per_trade_pct` into requested, scheduler-requested, approved, scheduler-approved, risk-delta, and selected-cell risk.
- The transfer is constrained by `_candidate_requested_risk_pct_with_source`: exact candidate/time identity, signed package authority, source completeness, broker-cost pass, and package replay executable authority.
- Original stale runtime/veto values are retained as `risk_finalizer_soft_probe_*_original` diagnostics.

Diagnostic repair:

- Finalizer probe rows now retain `risk_finalizer_soft_probe_bounded_risk_transfer_applied` and source.

Test proof before replay:

- `py_compile`: passed
- Focused finalizer tests: `2 passed`
- V121-adjacent timewarp slice: `68 passed`
- Scoped `git diff --check`: passed

## Expected Effect

- Candidate ledger should be present in V121D, unlike V121C.
- `scheduler_option_runtime_ineligible` and `selected_cell_or_requested_risk_missing_nonpositive` should drop or move to a downstream blocker.
- Order/trade count may increase. Headline R may improve or worsen; both are valid if the transfer is truthful.
- Positive and negative missed R should move according to exact transfer, not suppression.
- REFUSED/source-gap executions must remain zero.

## Replay Result Interpretation

Helped if exact-bound soft probes become risk-admitted/order-present and the old stale-runtime/zero-risk buckets fall without REFUSED/source-gap execution.

Failed if the same blockers remain unchanged, or if transfers occur only by bypassing cost/source/signed authority. If behavior worsens, keep the truth repair and classify the next exposed blocker: selection ranking, fillability, lifecycle, or exit.
