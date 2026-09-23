# V178 B7 Pre-Replay Brief - Signed Daily-Loss Quality Floor Repair

Generated UTC: 2026-07-08T09:20:04Z

## Control State

- Fable ladder status from saved matrix: B0/B1/B2/B5 DONE, B3/B4/B6 DONE_WITH_LABEL, B7 PARTIAL, B8 OPEN.
- Current actionable batch: B7 package replay conversion and scheduler/order/risk transfer.
- Broker/live/final: closed. Local replay/package authority: full.
- No broad replay/build/pytest process was active before this patch.

## Latest Completed Local Replay

Latest targeted completed prefix:
`BROAD_LIVE_AS_IF_REPLAY_V177_B7_SIGNED_DAILY_LOSS_RELEASE_ALIAS_REPAIR_20260604_20260605_XAUUSD_TARGETED`

V177 local metrics:
- candidates/scorecards/orders/trades/missed/buckets: 1130 / 184 / 9 / 4 / 1125 / 27
- net/gross/final R: 0.57154290 / 0.95526857 / 0.95526857
- W/L/F: 3 / 1 / 0
- cost-refused executed/source-gap executed: 0 / 0
- missed diagnostic positive/negative R: +61.92688265 / -184.91760067
- V176 -> V177 added trade: `broadorigin_e59c330b1467251e45c3fd09@@2026-06-04T18:15:00+00:00`, +0.38818935R.
- Remaining same-root missed winner: `broadorigin_62cb335107ef114d9725321c@@2026-06-04T17:45:00+00:00`, +0.29090804R, same-symbol daily-loss lockout.

## Baseline Comparison

- V175: 3 trades, net R +0.84449709, W/L/F 3/0/0.
- V176: 3 trades, net R +0.18335355, W/L/F 2/1/0.
- V177: 4 trades, net R +0.57154290, W/L/F 3/1/0.
- This V178 proof is still a bounded 2026-06-04..2026-06-05 XAUUSD repair slice; it does not prove full reservoir conversion.

## Dirty Files Relevant To This Batch

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`

Other dirty files/deletions exist in the worktree and are not part of this B7 patch.

## Incorporated Findings

- Franklin: 17:45/18:15 V175 winners disappeared after V176 because a newly released 14:30 loss triggered `same_symbol_daily_loss_lockout_after_closed_trade`; 17:45 score 2.618938145 is below generic release score floor 3.0, 18:15 score 5.397239885. Incorporated.
- Planck: 08:45 guarded-market fallback block is valid thesis-geometry protection, not off-config fallback drift. Incorporated as non-target.
- Bernoulli: cost-refused/source-gap rows stay non-executable; package authority and lifecycle/daily-loss rows remain B7 targets. Incorporated.

## Root Mismatch Being Patched

Stage: selector/scheduler/risk -> order transfer.

Problem:
- V177 candidate and packet sidecar prove the 17:45 row is signed, source-bound, order-executable, broker-cost PASSED, pre-finalizer selected, and has no same-symbol exposure.
- The narrow signed-executable daily-loss release still consumed the generic `package_cooldown_release` quality packet, so a signed/order-executable row with score 2.618938145 failed the generic score floor 3.0.
- Missed ledger then demoted executable aliases after rejection, which is a downstream proof-surface issue; behavior repair comes first.

Patch:
- Add `package_cooldown_release_signed_executable_authority_*` threshold config.
- Create and consume a dedicated signed-executable daily-loss quality packet.
- Keep broad daily-loss release and package-quality daily-loss release closed.
- Ledger the signed quality packet under `signed_executable_authority_quality_release`.
- Harness repaired profile defaults: score >= 2.50, expected net >= 0.70, probability >= 0.70, fill probability >= 0.80, source completeness >= 0.95.

## Focused Proof Already Run

Command:
`python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "package_cooldown_release_daily_loss_lockout_requires_explicit_flag or package_fill_floor_authority_daily_loss_release_is_narrow_replay_path or package_router_refusal_authority_daily_loss_release_is_narrow_replay_path or order_materialization_consumes_scheduler_inputs_signed_router_refusal_authority or order_materialization_preserves_router_refusal_fill_floor_false or replay_order_materialization_blocks_unresolved_fill_floor_stale_allowed" -q --tb=short`

Result: 6 passed, 575 deselected, 1 warning.

## Expected V178 Effect

- candidate -> scorecard/order transfer: one additional signed 17:45 candidate should survive the risk finalizer.
- scorecard/order -> fill transfer: expected to materialize one additional order/fill if lifecycle/order geometry remains consistent.
- missed positive R: expected to drop by about 0.29090804R.
- missed negative R: expected neutral.
- trade count: expected +1 versus V177.
- net R: expected +0.29090804R versus V177 if the exact V177 missed-opportunity replay result transfers.
- W/L/F: expected +1 winner.
- cost-refused/source-gap execution: must remain 0 / 0.
- risk distribution: new row remains reduced-risk unless existing signed risk ladder promotes it from current policy.

## Success / Failure Criteria

Success:
- V178 fills or order-materializes the 17:45 signed candidate without executing cost-refused/source-gap rows.
- Net R improves by the recovered row or the ledger explains a new, real downstream blocker.
- The signed quality packet appears in the risk/order proof surface.

Failure:
- 17:45 remains blocked by generic package-quality floor.
- Broad daily-loss release accidentally opens.
- Cost-refused/source-gap rows execute.
- Positive result comes only from suppressing other trades rather than transfer.

Next if success: parse V178 against V175/V176/V177, then move to the next B7 root batch from package-order-executable authority missing / contract-passed raw reject rows.
