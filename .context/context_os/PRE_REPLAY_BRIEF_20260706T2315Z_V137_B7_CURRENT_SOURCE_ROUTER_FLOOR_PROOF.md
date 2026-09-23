# Pre-Replay Brief - V137 B7 Current-Source Router Floor Proof

Status: targeted B7 proof brief before replay. This uses the same bounded five-symbol, five-day denominator as V133-V136 and does not claim full-reservoir transfer.

## Latest Completed Targeted Proof

- V136 completed at `BROAD_LIVE_AS_IF_REPLAY_V136_B7_MATERIALIZED_ROUTER_FLOOR_CONSUMER_REPAIR_20260601_20260605_TARGETED`.
- Window/scope: `2026-06-01..2026-06-05`, active symbols `XAUUSD XAGUSD USDCAD USDJPY UKOIL_cash`, profile `repaired_package_conversion_v3`, tick source mode `resolved_when_available`.
- Behavior: `6633` candidates, `480` scorecard rows, `17` orders, `5` filled trades, `6625` missed rows, `62` source rows, net `-0.45200680R`, gross/final `-0.00248497R`, cash PnL `-$113.47824670`, W/L/F `3/2/0`.
- Authority boundary remained closed: broker mutation false, live broker authority false, final selection false.

## V136 Finding

- V136 was behavior-identical to V133-V135. The two source-bound router-refusal rows with below-floor execution fillability still filled:
  - `broadorigin_3a90b339627ebad3f67e12ed@@2026-06-02T06:15:00+00:00`: `-1.09572776R`, execution fillability `0.606185449`, materialized router fill floor `0.90`.
  - `broadorigin_03f542cd3bcc217f5007cef3@@2026-06-04T06:00:00+00:00`: `-0.20077613R`, execution fillability `0.625165167`, materialized router fill floor `0.90`.
- A direct current-source call to `reduced_package_new_entry_authority_validation` on the V136 candidate row now returns invalid with `router_refusal_fill_probability_below_floor` and `authority_hash_mismatch`.
- Interpretation: V136 artifacts do not prove the current source state. The next proof must rerun the same targeted slice with the current validator, not tune a new policy.

## Current Patch Surface

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
  - Source-bound router-refusal new-entry materialization cannot apply runtime router-floor override.
  - Router-refusal signed authority validation consumes materialized row floors before generic config defaults.
  - Source-bound router-refusal passive-limit queue routing cannot bypass unresolved execution-fillability floor failures.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
  - Source-bound router-refusal materialization carries execution-fillability aliases and keeps broker-cost refused/source-gap rows non-executable.
- Focused verification before V137:
  - all-touched `py_compile`: pass.
  - scheduler focused tests: `27 passed`.
  - timewarp router-refusal materialization tests: `4 passed`.

## Expected Effect

- Candidate and scorecard counts should remain near V136 (`6633` / `480`) unless authority invalidation removes rows earlier in the targeted chain.
- `3a90...` and `03f5...` should no longer become filled trades; they should be scoreable/missed or rejected with `router_refusal_fill_probability_below_floor`.
- `6e88...` should remain missed/non-executable with `router_refusal_fill_probability_below_floor`.
- Existing off-session/explicit winners should remain executable if their separate authority surfaces still pass.
- Expected local net if only those two losing fills are removed and no other transfer changes: approximately `+0.84449709R`, `3` trades, W/L/F `3/0/0`. This is a bounded repair expectation, not a final-system claim.

## Replay Result Interpretation

- Helped: below-floor source-bound router-refusal fills are blocked while scoreable missed accounting preserves their opportunity R and other valid transfers remain executable.
- Failed: the same rows still execute with valid authority, proving a stale flattened authority consumer downstream from validation.
- Exposed next flaw: valid winners such as `bf1a...` or `aa4b...` remain missed for lifecycle/order reasons after this authority leak is closed.
