# Pre-Replay Brief - V135 B7 Source-Bound Signed-Authority Execution-Fillability Floor Repair

Status: targeted B7 proof brief before replay. This is a bounded five-symbol, five-day local repair proof, not broad proof, full-reservoir conversion, or a live/final claim.

## Current Completed Targeted Proof

- V134 completed: `BROAD_LIVE_AS_IF_REPLAY_V134_B7_ROUTER_REFUSAL_EXECUTION_FILLABILITY_FLOOR_REPAIR_20260601_20260605_TARGETED`.
- V134 behavior: `6633` candidates, `480` scorecard rows, `17` order rows, `5` filled trades, `6625` missed rows, `62` source rows, net `-0.45200680R`, gross/final `-0.00248497R`, cash PnL `-$113.47824670`, W/L/F `3/2/0`, all fills ordered-tick and open-reduced-risk, zero executed REFUSED/source-gap/live/final rows.
- V134 failed the intended authority proof: `3a90...` and `03f5...` still filled as source-bound router-refusal rows with execution fillability `0.606185449` and `0.625165167` below the source-bound router floor.

## Root Cause Found After V134

- Producer and passive-route resolution were patched, but the core signed new-entry authority validator did not enforce router floors for `source_bound_router_refusal_open_reduced_materialized_for_replay` unless positive-router floor keys/flags were explicit in the validation trigger path.
- Replay passes a normalized `SchedulerV4Config` object, so raw config-key detection alone cannot trigger the floor block.
- Result: source-bound router-refusal rows could carry `package_new_entry_authority_valid=true` and empty authority failures using entry-quality fillability `0.95`, while execution fillability remained below floor.

## Current Patch Batch

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: `reduced_package_new_entry_authority_validation` now treats source-bound router-refusal materialization itself as a router-floor trigger, using execution/limit fillability from the payload.
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`: added `test_source_bound_router_refusal_signed_authority_requires_execution_fillability_floor` and updated source-bound router tests to expect invalid signed authority plus non-bypassable route failures.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`: derived immediate-marketability fixture now provides execution fillability when expecting signed authority to pass.
- Focused verification passed: all-touched `py_compile`; timewarp router-refusal tests `4 passed`; scheduler router/refusal/fill-floor/passive-route tests `27 passed`.

## Expected Measurable Effect

- Candidate and scorecard counts should remain near V134 (`6633` candidates, `480` scorecard rows); this is not a generator change.
- Source-bound router-refusal rows with execution fillability below the configured floor should not be signed-valid and should not become order/trade executable.
- Expected removed V134 losing fills: `3a90...` `-1.09572776R` and `03f5...` `-0.20077613R`.
- Valid explicit materialization/off-session rows should remain if they satisfy their separate authority contract: `62c...`, `e59c...`, `a143...`.
- V135 helps only if it removes the invalid source-bound fills without deleting all opportunity. If trade count collapses to zero, this is not accepted as a performance proof.

## Success / Failure Criteria

- Helped: V134 source-bound router-refusal losers move to missed/non-executable with `router_refusal_fill_probability_below_floor` and/or `source_bound_router_refusal_execution_fill_floor_non_bypassable`; explicit materialization winners remain executable.
- Failed: `3a90...` or `03f5...` still fills with `package_new_entry_authority_valid=true` despite execution fillability below floor.
- Exposed next flaw: the invalid rows are removed but positive V129/V133 transfers are also displaced by lifecycle/reallocation instead of replaced by next valid candidates.
