# V114C Pre-Replay Brief: Risk-Expression Authority Repair

Generated: 2026-07-04T07:14:12Z

Route: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20`

## Current Run State

- No broad replay or pytest process is running.
- Latest completed replay: `BROAD_LIVE_AS_IF_REPLAY_V114B2_DISPLACEMENT_GATE_REPAIR_20260603_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`
- V114B2 status: `broad_live_as_if_replay_materialized_broker_live_closed`
- Window: 2026-06-03 only, full 24-symbol surface, repaired profile only, compact missed ledger, candidate ledger omitted, candidate index retained.
- This is a bounded repair proof slice. It does not prove full reservoir conversion and must not be compared directly to the full source-bound million-R reservoir.

## Latest Completed Numbers

V114B2:

- candidates: 6,603
- scorecard rows: 96
- order rows: 56
- order status: 28 pending accepted, 16 expired unfilled, 12 filled
- trade rows: 12
- missed opportunity rows: 6,575
- source universe rows: 123
- net R: -2.30082618
- gross R: -1.15118996
- final R: -1.15118996
- summary cash PnL: -230.28228129
- risk cash: 1,200.53417139
- risk pct sum: 1.2
- W/L/F: 3/9/0
- filled selector action distribution: 12 open-reduced-risk
- filled symbols: USOIL_cash 11, BTCUSD 1
- filled side: 12 SHORT
- filled sessions: london 8, off_configured_session 4

V114B2 was behavior-neutral versus V114B and V113C on the same 2026-06-03 slice.

## Baseline Comparison

These are hostile 5-day comparators, not same-window denominators:

- V89D `2026-05-13..2026-05-17`: 25,006 candidates, 288 scorecard rows, 243 order rows, 56 fills, 24,885 missed rows, +34.84520454 net R, +39.93441037 gross/final R, +8,178.90660707 cash.
- V90 `2026-05-13..2026-05-17`: 25,006 candidates, 288 scorecard rows, 233 order rows, 51 fills, 24,890 missed rows, +28.84201157 net R, +33.36349114 gross/final R, +6,371.80465431 cash.
- V92 `2026-05-13..2026-05-17`: 25,006 candidates, 288 scorecard rows, 239 order rows, 51 fills, 24,887 missed rows, +29.35570236 net R, +33.9321286 gross/final R, +6,228.63096022 cash.

Do not judge V114C by whether it matches those 5-day totals. Judge it by whether the B3 authority truth changed the same 2026-06-03 slice correctly.

## Dirty Code Changes In This Batch

- `config/agent_config.yaml`
- `src/components/selector_v4.py`
- `src/research/reduced_risk_action_reason_contract.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py`
- focused tests in `tests/test_selector_v4.py`, `tests/test_broad_replay_repair_config.py`, `tests/test_timewarp_scheduler_materialization.py`, `tests/test_v4_timewarp_simulated_live_research_loop.py`, and `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`

## Subagent Findings

- Parfit: incorporated for B3. Broker-net below-full-floor should not default to open-reduced; fill-floor selector softening should default false; exact-block mode diagnostic in repaired replay.
- Huygens: incorporated. Selected bridge stale fill-floor true fixed; strict full-package parity now uses signed reduce-risk authority for reduce-risk rows; scheduler/timewarp missing broker-gradient config now fails closed.
- Ampere: deferred. Fallback-time expiry clamp and lifecycle attribution are valid but are a separate lifecycle/fillability root batch unless V114C shows them as the next dominant leak.

## Root Mismatch Classes

- Source-bound -> candidate: unchanged in V114C; same-window source/candidate transfer must be measured after replay.
- Candidate -> selector: fixed. Fill-floor selector softening defaults false; broker-net-gradient open-reduced defaults false; below-full-trade broker-net EV maps to reduce-risk by default.
- Selector -> scheduler: fixed. Repaired profile and selected bridge forward the broker-gradient flag; shared reason contract no longer infers open-reduced from missing selector action.
- Scheduler -> risk: partially fixed. Strict parity uses signed reduce-risk authority for reduce-risk rows; broader signed full/reduced risk ladder remains open.
- Risk -> order/fillability: fixed for B3. Open-reduced materialization fails closed when broker-gradient/fill-floor config is absent or false.
- Lifecycle/fill/expiry: open. Prior V114B2 showed passive queue fill probability and fallback envelope distance blockers; Ampere fallback expiry clamp remains deferred.
- Exit/profit harvest: unchanged in V114C.
- Ledger/verifier: partially fixed through strict parity and focused tests; route verifier still needs to run after replay.

## Patch Classification

- Correctness repairs: selector defaults/action mapping, shared reduced-risk reason contract, base config, broad runtime, selected bridge, scheduler config status, timewarp materialization status.
- Diagnostic/ledger repairs: strict full-package parity authority split and tests.
- Performance repairs: none claimed before replay. Any R improvement must be explained as authority truth, not as proof the whole system is solved.

## Expected Measurable Effect

- Candidate -> scorecard transfer: may decrease or remain flat.
- Scorecard -> order transfer: may decrease if prior orders depended on unsigned open-reduced authority.
- Order -> fill transfer: may decrease; acceptable if removed fills lacked signed open-reduced authority.
- Missed positive R: may increase because demoted rows remain scoreable/missed.
- Missed negative R: may increase or decrease depending on which fills are demoted.
- Trade count: expected below 12 if V114B2 fills were unsigned broker-gradient/fill-floor open-reduced; unchanged if they had other signed authority.
- Net/gross/final R: may improve, worsen, or remain flat. This patch is about truth first.
- W/L/F: report after replay.
- Cost-refused/source-gap execution: must remain zero.
- Full-risk vs reduced/open-reduced distribution: open-reduced should fall unless explicit signed authority exists; reduce-risk rows must carry reduce-risk provenance.

## Replay Success Criteria

Helped:

- broker-gradient/fill-floor rows are not open-reduced unless explicitly enabled and signed;
- below-full-trade broker-net EV appears as reduce-risk or missed/proven signed authority;
- strict full-package parity excludes unsigned reduced rows;
- refused-cost/source-gap executions remain zero.

Failed:

- any filled row still enters only because `broker_net_admission_ev_below_full_trade_floor` was inferred as open-reduced without signed authority;
- selected bridge or broad repaired runtime re-enable fill-floor selector softening;
- strict parity counts reduced rows from the open-reduced authority surface.

Next deeper flaw:

- if V114C behavior is unchanged and all fills are signed correctly, the next limiting batch is lifecycle/fillability/expiry or exit geometry, not selector risk-expression truth.

## Targeted Replay

Run:

```bash
python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-06-03 \
  --end 2026-06-03 \
  --profiles repaired_package_conversion_v3 \
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V114C_RISK_EXPRESSION_AUTHORITY_REPAIR_20260603_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS \
  --chunk-size 1 \
  --omit-candidate-ledger \
  --compact-missed-ledger \
  --skip-tick-source
```

After replay, parse summary/trade/order/missed/bucket/flow artifacts and compare V114C against V114B2 same-window only.
