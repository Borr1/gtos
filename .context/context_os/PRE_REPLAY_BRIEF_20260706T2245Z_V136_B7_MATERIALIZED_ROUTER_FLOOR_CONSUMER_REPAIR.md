# Pre-Replay Brief - V136 B7 Materialized Router-Floor Consumer Repair

Status: targeted B7 proof brief before replay. This is the same five-symbol, five-day proof slice used by V133-V135.

## Latest Evidence

- V135 completed but was behavior-identical to V134: `5` trades, `-0.45200680R`, W/L/F `3/2/0`, `6633` candidates, `480` scorecard rows, `17` orders, `6625` missed rows.
- The two invalid source-bound router-refusal fills still executed: `3a90...` `-1.09572776R` with execution fillability `0.606185449`, and `03f5...` `-0.20077613R` with execution fillability `0.625165167`.
- Drilldown showed the correct source-bound floor was present on the row as `scheduler_option_package_numeric_open_reduced_floor_fill_probability=0.90`, but `reduced_package_new_entry_authority_validation` still compared against the generic config-object default.

## Current Patch

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: router-refusal signed authority validation now consumes materialized row floors from `scheduler_option_package_numeric_open_reduced_floor_*`, `package_numeric_open_reduced_floor_*`, or `numeric_disagreement_open_reduced_floors` before generic config defaults.
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`: the source-bound router-refusal signed-authority test now uses default config plus row-level `scheduler_option_package_numeric_open_reduced_floor_*` values, matching the replay failure mode.
- Focused verification passed: all-touched `py_compile`; scheduler focused tests `27 passed`; timewarp focused tests `4 passed`.

## Expected Effect

- Candidate/scorecard counts should stay near V135.
- `3a90...` and `03f5...` should no longer execute; they should become missed/non-executable with `router_refusal_fill_probability_below_floor`.
- Existing explicit/off-session winners should remain if their separate authority chain still passes.
- If the same invalid rows still execute, the next leak is a post-validation stale flattened authority consumer, not the validator itself.
