# Pre-Replay Brief - V204 B7 Missed Selector-Origin And Flow Diagnostic Repair

Generated UTC: 2026-07-08T22:53:56Z.

## Current Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V203_B7_SIGNED_ALIAS_AND_SELECTOR_ORIGIN_REPAIR_20260513_REPAIRED_ONLY_COMPACT_FULLGRID`
- Window/profile: `2026-05-13`, `repaired_package_conversion_v3`
- Candidates / scorecards / order rows / trades: `8864 / 96 / 24 / 14`
- W/L/F: `7/7/0`
- Net/gross/final R: `-2.94390255 / -1.88067619 / -1.88067619`
- Cash PnL: `-2136.50639331`
- Risk cash / risk pct: `6820.65726438 / 6.875`
- Expected cost R: `1.06322636`
- Broker/live/final: all false.

V203 is behavior-identical to V202 and closes the V201/V202 order-executable false-materialized class. It is a bounded one-day proof slice only, not full-reservoir transfer evidence.

## Active Process State

No broad replay, route builder, verifier, parity builder, or pytest process is running. Context OS build/pack completed before this brief. Do not start a duplicate broad run.

## Baseline Comparison

- V198 hostile fullgrid five-day: `25006 / 288 / 178 / 74`, W/L/F `43/31/0`, net/gross/final R `-3.84033809 / 1.79005938 / 1.79005938`.
- V199 targeted hostile: `14384 / 288 / 154 / 67`, W/L/F `37/30/0`, net/gross/final R `-6.48266227 / -1.51201107 / -1.51201107`.
- V201 targeted hostile: `14384 / 288 / 85 / 70`, net/gross/final R `-6.5478412 / -1.36541623 / -1.36541623`.
- V202 one-day proof: `8864 / 96 / 24 / 14`, W/L/F `7/7/0`, net/gross/final R `-2.94390255 / -1.88067619 / -1.88067619`.
- V203 one-day proof: same behavior as V202; verifier issue count reduced to two proof-surface issues.

The V204 proof must compare to V203, not to the full million-R reservoir.

## Current Dirty / Active Files

Active route-owned batch files:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_broad_replay_repair_config.py`
- `tests/test_denominator_to_deployment_verifier.py`
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260708.md`

Other dirty Context OS/science-program files exist but are not part of this replay proof batch.

## Subagent Findings Incorporated

- Faraday verifier lane: incorporated. Verifier now treats selected-cell risk aliases, not-order-executable status, and signed scale-in lifecycle authority precisely.
- Lovelace order-contract lane: incorporated. Contract-unmet marketable route rows final-block without bound order/trade ids.
- Lorentz rebuild lane: incorporated. V201/V202/V203 parity/build/verifier sequence was run from deterministic commands.
- Prior B7 risk/order/fillability lanes: incorporated as background. No REFUSED/source-gap execution is allowed.

## Mismatch Classes

- Source-bound -> candidate: not active blocker for V204; one-day candidate count is stable at `8864`.
- Candidate -> selector -> scheduler: active proof-surface leak in missed rows. Original selector action can be lost after effective risk/action materialization.
- Scheduler -> risk -> order: V203 order executable transfer is clean; preserve it.
- Order -> lifecycle -> fill -> exit: behavior should remain unchanged.
- Ledger -> verifier: active flow diagnostic missing plus missed-row selector-origin identity failure.

## Fixed / Partial / Open

- Fixed: order-executable false materialized, candidate selected-cell risk fallback, signed scale-in authority verifier precision, contract-unmet order binding.
- Partial: B1/B5 projection into missed rows; active patch adds producer/consumer coverage.
- Open: selected-prefix flow diagnostic generation.

## Highest-Leverage Same-Root Batch

`B7_missed_selector_origin_projection_and_flow_diagnostic_closure`.

This is a correctness/proof-surface repair, not a policy tune. It should not change behavior.

## Expected Measurable Effect

- Candidate -> scorecard: unchanged at approximately `8864 -> 96`.
- Scorecard -> order: unchanged at order rows `24`.
- Order -> fill: unchanged at trades `14`.
- Missed positive/negative R: unchanged except identity/provenance fields become verifier-clean.
- Trade count: unchanged at `14`.
- Net/gross/final R: unchanged at `-2.94390255 / -1.88067619 / -1.88067619`.
- W/L/F: unchanged at `7/7/0`.
- Cost-refused/source-gap execution: `0/0`.
- Risk-reduced/full-risk distribution: unchanged unless existing projection-only count becomes visible.

## Proof Criteria

Helped:

- Compile and focused tests pass.
- V204 behavior matches V203.
- `analyze_broad_live_as_if_replay_flow.py` writes selected-prefix flow diagnostics.
- Source-bound parity, denominator summary, manifest, and verifier regenerate.
- Verifier `issue_count=0`.

Failed:

- Trades or R move without a policy change.
- Missed selector-origin verifier issue remains.
- Flow diagnostic cannot be generated from V204 artifacts.

Next deeper flaw:

- If verifier is green but V204 remains negative, leave one-day proof-surface work and proceed in Fable order to B7.2/B7.3 value-transfer evidence.
