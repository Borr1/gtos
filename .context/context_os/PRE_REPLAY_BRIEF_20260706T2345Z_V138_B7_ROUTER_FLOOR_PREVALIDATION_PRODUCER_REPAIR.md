# Pre-Replay Brief - V138 B7 Router Floor Prevalidation Producer Repair

Status: targeted B7 proof brief before replay. Same bounded denominator as V133-V137: `2026-06-01..2026-06-05`, active symbols `XAUUSD XAGUSD USDCAD USDJPY UKOIL_cash`, profile `repaired_package_conversion_v3`, broker/live/final closed.

## Latest Completed Targeted Proof

- V137 completed at `BROAD_LIVE_AS_IF_REPLAY_V137_B7_CURRENT_SOURCE_ROUTER_FLOOR_PROOF_20260601_20260605_TARGETED`.
- Behavior was unchanged from V136: `6633` candidates, `480` scorecard rows, `17` orders, `5` trades, `6625` missed rows, net `-0.45200680R`, W/L/F `3/2/0`.
- The below-floor source-bound router-refusal losers still executed:
  - `3a90...` `-1.09572776R`, execution fillability `0.606185449`, materialized fill floor `0.90`.
  - `03f5...` `-0.20077613R`, execution fillability `0.625165167`, materialized fill floor `0.90`.

## Root Cause

- Direct validation on the final V137 candidate ledger row fails correctly with `router_refusal_fill_probability_below_floor`.
- The scheduler decision-time validation ran before `scheduler_option_package_numeric_open_reduced_floor_*` fields were materialized. Ledger-time rows carried the floors, but the signing input did not.
- This is a producer/consumer order mismatch, not a replay-cost or fill-simulation issue.

## Current Patch

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
  - Before `reduced_package_new_entry_authority_validation`, source-bound router-refusal new-entry candidates now stamp numeric open-reduced floors into:
    - `scheduler_option_package_numeric_open_reduced_floor_*`
    - `package_numeric_open_reduced_floor_*`
    - `numeric_disagreement_open_reduced_floors`
    - `package_new_entry_authority_numeric_disagreement_open_reduced_floors`
    - the open-reduced authority payload itself.
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
  - Focused test now asserts the stronger prevalidation contract: missing expected-R/probability/fill floors all surface under signed authority failure when the materialized source-bound router-refusal row misses them.
- Focused verification before V138:
  - scheduler `py_compile`: pass.
  - scheduler focused tests: `27 passed`.

## Expected Effect

- Candidate/scorecard counts should remain near V137 unless earlier invalidation prunes some rows.
- `3a90...` and `03f5...` should no longer fill; they should be missed or rejected with signed authority failures including `router_refusal_fill_probability_below_floor`.
- `6e88...` should remain missed for the same floor failure.
- If only those two losing trades are removed, local net should improve by `+1.29650389R` from `-0.45200680R` to about `+0.84449709R`, with `3` filled trades and W/L/F `3/0/0`.

## Result Interpretation

- Helped: invalid source-bound router-refusal floor misses stop executing while valid off-session/explicit transfers remain.
- Failed: the same rows still execute, proving a downstream stale authority consumer is bypassing `signed_package_new_entry_authority_valid`.
- Exposed next flaw: after this closes, remaining V129 winner loss is likely lifecycle/order/reallocation (`bf1a...`, `aa4b...`) rather than source-bound router-refusal floor validation.
