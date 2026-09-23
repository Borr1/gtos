# V120E Derived Raw-Reject Promotion Contract Pre-Replay Brief

Status: targeted proof brief. Broker/live/final remain closed. This is a correctness repair for order-executable package replay transfer.

## Latest Completed Run

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V120D_SOURCE_READINESS_TRANSFER_REPAIR_20260515_REPAIRED_ONLY_FULLGRID`
- Window: `2026-05-15..2026-05-15`
- Result: 2304 decision rows, 8174 generated/written candidates, 96 scorecards, 0 orders, 0 trades, 8174 missed rows.
- Meaning: the source-readiness repair worked; all 24 symbols were ready and candidate generation was no longer crypto-only. This smoke proves a local source-generation repair only. It does not prove full reservoir transfer.

## Baselines

- V92 same day: 84 orders, 16 fills, 7/9/0 W/L/F, `-2.23790002R` trade net-like R. Orders were all `limit_first_reduced_risk` across XAUUSD, XAGUSD, BTCUSD, USOIL_cash, UKOIL_cash, USDJPY, and GER40.
- V120D same day: 8174 candidates and 96 scorecards, but every scorecard ended `zero_trade`; top blockers were `raw_reject_order_executable_promotion_contract_missing` and `source_bound_package_replay_not_allowed`.

## Current Finding

All 16 V92 May-15 filled candidate keys still exist in V120D candidate and missed ledgers.

- 7/16 are broker-cost passed, source-complete, signed-authority valid, above the raw-reject limit-fillability floor, and blocked only by `raw_reject_order_executable_promotion_contract_missing`.
- 4/16 are low-fillability or source-bound-not-allowed and should remain non-executable unless a later policy proves a causal route.
- 3/16 remain plain selector rejects with no materialized effective risk action.
- 2/16 are already order-executable but final-blocked by downstream guards.

## Patch Batch

- Scheduler now derives `raw_selector_reject_open_reduced_order_executable_promotion_v1_derived_from_signed_source_bound_authority` when the upstream helper stamp is absent but the row independently satisfies signed predecision authority, package admission, source-bound allowance, broker-cost/package replay executable authority, and the limit-fillability floor.
- Low-fillability raw-reject promotions remain blocked and tested.
- REFUSED/source-gap rows remain non-executable.

## Expected Effects

- Candidate -> scorecard: unchanged.
- Scorecard -> order: valid signed source-bound rows should no longer be blocked only by missing helper stamp.
- Order -> fill: some valid V92-like transfers may reappear, or downstream risk/order/fill blockers should become exact.
- Missed positive/negative R: both may move because this restores opportunity instead of suppressing it.
- Trade count/R: may improve or worsen. Success is valid transfer restoration and precise blockers, not a positive-by-suppression result.
- Cost REFUSED/source-gap execution: must stay zero.

## Targeted Proof

Run `BROAD_LIVE_AS_IF_REPLAY_V120E_DERIVED_RAW_REJECT_PROMOTION_CONTRACT_20260515_REPAIRED_ONLY_FULLGRID` on `2026-05-15..2026-05-15`, repaired-only fullgrid, candidate ledger omitted unless needed.

Helped if:

- `contract_missing` is no longer the dominant blocker for signed, cost-passed, high-fillability rows;
- order/trade transfer reappears or downstream blockers become precise;
- low-fillability rows remain non-executable with named reasons;
- cost REFUSED/source-gap executed counts remain zero.

Failed if:

- zero orders remain and `contract_missing` is still the main blocker;
- rows execute without signed authority, source completeness, broker-cost pass, or fillability floor;
- trade-count improvement hides unscoreable suppression.
