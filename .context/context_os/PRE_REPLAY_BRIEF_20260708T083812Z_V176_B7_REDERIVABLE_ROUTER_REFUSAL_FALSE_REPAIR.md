# PRE_REPLAY_BRIEF_20260708T083812Z_V176_B7_REDERIVABLE_ROUTER_REFUSAL_FALSE_REPAIR

## Current Batch

- Fable batch: B7 package replay conversion / scheduler-order-risk transfer.
- Current proof slice: XAUUSD, 2026-06-04..2026-06-05, repaired_package_conversion_v3.
- Broker/live/final authority: closed; local replay authority: full.

## Latest Completed Baseline

- V175 prefix: `BROAD_LIVE_AS_IF_REPLAY_V175_B7_COMPACT_COST_SURFACE_RISK_RELEASE_REPAIR_20260604_20260605_XAUUSD_TARGETED`.
- V175 rows: 1130 candidates, 184 scorecards, 10 orders, 3 trades, 1127 missed, 28 buckets.
- V175 behavior: net/gross/final R `0.84449709 / 1.09529478 / 1.09529478`; W/L/F `3/0/0`; risk cash `750.42443587`; risk pct sum `0.75`.
- V175 blocker: the three watched router-refusal rows still ended as `risk_rejected` with `package_replay_executable_candidate_use_not_allowed:source_bound_router_refusal_requires_signed_new_entry_authority`, despite valid signed order authority and `package_replay_order_executable_candidate_use_allowed=true`.

## Patch Under Test

- Correctness repair in `src/research_infra/v4_timewarp_simulated_live_research_loop.py`.
- `source_bound_router_refusal_requires_signed_new_entry_authority` is now classified as rederivable after signed authority is present.
- `release_rederived_package_authority_risk_reject` now tolerates a stale candidate-use false only when:
  - signed package new-entry authority is valid;
  - order executable authority is true;
  - broker-cost authority is not blocking;
  - fill-floor hard veto is not present;
  - approved risk pct is positive.
- Focused test: `test_order_materialization_consumes_scheduler_inputs_signed_router_refusal_authority` now covers the stale router-refusal false shape.

## Expected Measurable Effect

- Candidate -> scorecard: neutral.
- Scorecard -> order: neutral or +0 if rows were already order-present.
- Order -> fill: expected +3 risk-bearing orders if the stale false was the only block.
- Missed positive R: should decrease by about `1.1224184` for the 07:30 watched row; the 08:45 watched row has null opportunity; the 14:30 watched row is about `-1.10446455` and may reduce missed negative R if filled.
- Trade count: expected to rise from 3 if downstream fill/lifecycle allows.
- Net/gross/final R: unknown; this is a correctness repair, not an outcome-fit filter.
- W/L/F: should show whether released router-refusal rows are executable winners/losses.
- Cost-refused/source-gap execution: must remain 0.
- Risk-reduced/full-risk distribution: released rows should be risk-bearing at reduced risk unless a downstream causal guard blocks.

## Success / Failure Criteria

- Helped: watched rows no longer remain stale package-authority risk rejects; they become fills or move to a later explicit downstream reason.
- Failed: watched rows remain `package_replay_executable_candidate_use_not_allowed:source_bound_router_refusal_requires_signed_new_entry_authority`.
- Exposed next blocker: watched rows move to lifecycle, duplicate, fillability, expiry, same-symbol, or exit behavior with deterministic reason.
