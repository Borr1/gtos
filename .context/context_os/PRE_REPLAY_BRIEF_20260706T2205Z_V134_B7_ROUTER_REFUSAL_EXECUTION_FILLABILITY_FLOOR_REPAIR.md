# Pre-Replay Brief - V134 B7 Router-Refusal Execution-Fillability Floor Repair

Status: targeted B7 proof brief before replay. This is a bounded five-symbol, five-day local repair proof, not full-reservoir conversion and not a live/final claim.

## Current Completed Runs

- Latest completed broad B7 proof remains `BROAD_LIVE_AS_IF_REPLAY_V128_B7_ROUTER_REFUSAL_DERIVED_IMMEDIATE_AUTHORITY_REPAIR_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID_LAZYHASH`: 55 trades, `+1.12099062R` net, W/L/F `38/17/0`, zero executed REFUSED/source-gap/live/final rows.
- Latest targeted baseline before this patch is `BROAD_LIVE_AS_IF_REPLAY_V133_B7_ROUTER_FLOOR_OVERRIDE_CONSUMER_REPAIR_20260601_20260605_TARGETED`: 5 trades, `-0.45200680R` net, gross/final `-0.00248497R`, cash PnL `-$113.47824670`, W/L/F `3/2/0`, candidates `6633`, scorecard `480`, order rows `17`, missed rows `6625`, source rows `62`.
- Prior targeted checkpoints: V129 4 trades `+2.23793804R` all wins; V130 3 trades `-2.41628102R` all losses; V131 1 trade `+0.33108270R`; V132 5 trades `-1.79429028R`.

## Active Process State

- No broad replay, route builder, verifier, pytest, or py_compile process is running.
- V134 is intentionally replacing no active run; it is the next targeted proof after focused tests passed.

## Fable Matrix State

- B0 DONE, B1 DONE, B2 DONE, B3 DONE WITH LABEL, B4 DONE WITH LABEL, B5 DONE, B6 DONE WITH LABEL.
- B7 remains PARTIAL. B7.1/B7.2/B7.3 have proof artifacts, but same-window transfer and V104 winner recovery are not solved.
- B8 remains OPEN. Broker/live/final stay false.

## Current Patch Batch

Same-root class: source-bound router-refusal replay materialization and scheduler route resolution were using different fillability authority.

- Producer repair: `src/research_infra/v4_timewarp_simulated_live_research_loop.py` now records entry-quality fillability separately and requires execution fillability for source-bound router-refusal materialization floors.
- Consumer repair: `src/research/moonshot_scheduler_v4_best_trade_allocator.py` keeps source-bound router-refusal execution fill-floor failures non-bypassable through passive-limit route resolution.
- Focused tests passed: timewarp source-bound router-refusal materialization tests `4 passed`; scheduler router/refusal/fill-floor/passive-route tests `24 passed`; all-touched `py_compile` passed.

## Expected Measurable Effect

- Candidate -> scorecard transfer should stay near V133 (`6633 -> 480`) because this is not a generator change.
- Scorecard/order -> fill transfer should remove source-bound router-refusal rows whose execution fillability is below the configured floor.
- Expected removed V133 losing executions: `3a90...` `-1.09572776R` and `03f5...` `-0.20077613R`.
- Expected already-blocked rows: `6e88...` and `4c...` remain missed unless another valid authority path exists.
- Explicit package materialization winners `e59c...`, `a143...`, and `62c...` should remain if they satisfy their separate authority contract.
- Positive-by-suppression risk watch: if V134 improves only by deleting all fills or removing explicit package winners, the batch fails or exposes a scheduler reallocation leak.
- Cost/source-gap execution must remain zero. Broker/live/final must remain false.
- Full-risk vs reduced-risk distribution is expected to remain mostly reduced because this patch does not alter risk ladder eligibility.

## Success / Failure Criteria

- Helped: source-bound router-refusal below-execution-floor rows become missed/non-executable with explicit `fill_probability_below_floor` or `source_bound_router_refusal_execution_fill_floor_non_bypassable` reasons, while valid explicit materialization rows still execute.
- Failed: V130/V132 source-bound router-refusal losers still execute through another unproven fillability bypass.
- Exposed next flaw: all targeted winners disappear, or missed positive R rises because scheduler reallocation cannot replace blocked rows with the next valid package candidate.
