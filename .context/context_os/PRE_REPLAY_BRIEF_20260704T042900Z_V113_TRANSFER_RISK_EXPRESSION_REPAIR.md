# V113 Transfer/Risk-Expression Repair Pre-Replay Brief

Generated: 2026-07-04T04:29:00Z

## Current State

- No broad replay, pytest, or parity builder is running.
- A stale wide `git add` helper and stale `generate_live_state.py` worker were terminated after inspection; no index lock remained.
- Context OS catalog refreshed at 2026-07-04T04:22:16Z and a fresh task pack was read.
- Broker/live/final remain closed. Local replay/package authority remains full.

## Baselines

Hostile stress bucket, 2026-05-13..2026-05-17:
- V89D: 56 trades, +34.84520454 net R, +39.93441037 gross/final R, +8178.90660707 cash, W/L/F 41/15/0, 25006 candidates, 288 scorecard rows, 243 order rows, 59 expired.
- V90: 51 trades, +28.84201157 net R, +33.36349114 gross/final R, +6371.80465431 cash, W/L/F 37/14/0, 25006 candidates, 288 scorecard rows, 233 order rows, 59 expired.
- V92: 51 trades, +29.35570236 net R, +33.9321286 gross/final R, +6228.63096022 cash, W/L/F 37/14/0, 25006 candidates, 288 scorecard rows, 239 order rows, 62 expired.
- V97: 47 trades, +13.89627731 net R, +18.2389067 gross/final R, +4461.09800786 cash, W/L/F 23/24/0, 25006 candidates, 288 scorecard rows, 196 order rows, 51 expired.

Same-window denominator for V92: +218870.181480028 source-bound R, 1101 package axes, 894 candidate axes, 39 scorecard/order axes, 25 filled axes, +17.76833767 executable R.

Same-window denominator for V97: +222423.262022048 source-bound R, 1101 package axes, 894 candidate axes, 29 scorecard/order axes, 18 filled axes, +13.48984606 executable R. V97 added 19 trades for +0.99594545R but removed 23 trades for +13.53876156R, so the transfer swap was -12.54281611R.

Broad non-May comparator, 2026-06-01..2026-06-19:
- V110B: 95 trades, +22.80442652 net R, +28.71092008 gross/final R, +3098.56483036 cash, W/L/F 52/43/0, 75274 candidates, 1056 scorecard rows, 193 order rows, 0 expired.
- V111: 45 trades, -4.19333138 net R, +0.53053553 gross/final R, -420.03678236 cash, W/L/F 12/33/0, 75911 candidates, 1056 scorecard rows, 146 order rows, 28 expired.

Same-window denominator for V110B/V111: +342126.925564897 source-bound R, 1101 package axes, 944 candidate axes. V110B had 34 scorecard/order axes, 33 filled axes, +21.88363795 executable R. V111 had 16 scorecard/order axes, 13 filled axes, -2.06644961 executable R.

V111 versus V110B: common trade count 0, added 45 trades for -4.19333138R, removed 95 trades for +22.80442652R. This is a disjoint transfer replacement/regression, not the same trades exiting worse.

## Dirty Files And Active Changes

Tracked dirty route/code/test files include:
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- focused tests under `tests/test_broad_replay_repair_config.py`, `tests/test_denominator_to_deployment_verifier.py`, `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`, and `tests/test_v4_timewarp_simulated_live_research_loop.py`.

There are unrelated context-os and cleanup/deletion changes in the worktree; preserve them and stage only scoped route-owned files at commit time.

## Subagent Findings

- Hooke: incorporated. V111 is materialization displacement, not candidate availability.
- Schrodinger: incorporated. Raw selector action is overwritten by materialized package action; action provenance collapses into open-reduced-risk.
- Erdos: incorporated. Limit-first/fallback contract and fill-floor materialization are the order leaks; cancel-replace is not primary.
- Euclid: incorporated. Patch upstream scheduler/order transfer before exit tuning because V111 substituted off-session USOIL-heavy shorts and removed broader V110B source families.
- Herschel: incorporated for patch. Timewarp overwrites selector action/reason in open-position, trade-close, and package-authority normalizer paths.
- Kepler: incorporated for patch. Entry-quality probability and execution fillability are distinct; resolved passive-limit routes should stay eligible while unresolved fill-floor failures block executable authority.
- Sagan: incorporated for verifier patch. Off-configured guarded-market fallback applied while disabled must be verifier-fatal.
- Noether: incorporated for proof scope. Use 2026-06-03 first because V111 concentrates 58/146 order rows and 28/45 trade rows there, while session_open_range_break has 50 candidate-index rows.

## Root Mismatch Classes

- Source-bound -> candidate: not the current primary choke; candidates and generated axes remain broad.
- Candidate -> selector: partially fixed; session_open_range_break parity is restored in the broad harness, but raw selector action still needs immutable timewarp handling.
- Selector -> scheduler: open; scorecard rows stay broad while scorecard/order axes and fills collapse.
- Scheduler -> risk: open; nearly all package trades are open-reduced-risk, which affects allocation, headroom, reallocation, same-symbol lifecycle, and frequency.
- Risk -> order/fillability: open; V111 reintroduced expired limits and fallback displacement.
- Order -> lifecycle -> fill: open; off-configured fallback drift must be non-executable while configured session-open routes stay eligible.
- Fill -> exit: deferred until transfer truth is fixed; V111 losses come from a substituted set.
- Ledger/verifier: open; verifier must fatal off-configured fallback applied while disabled, and ledgers must preserve raw/effective selector and risk-expression provenance.

## Patch Batch

Files/components:
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: selector raw/effective split, trade/order provenance, signed risk-expression ladder/provenance.
- `verify_denominator_to_deployment_execution.py`: off-configured fallback-applied-while-disabled fatal.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`: raw/effective selector tests and risk-expression provenance tests.
- `tests/test_denominator_to_deployment_verifier.py`: off-configured fallback verifier test.
- `tests/test_broad_replay_repair_config.py`: session_open_range_break parity and raw/effective bridge assertions.

Patch types:
- Correctness: raw selector action/reason immutability.
- Correctness: off-configured fallback cannot execute when disabled.
- Correctness/performance: signed risk-expression ladder promotes only source-complete, cost-passed, fillable, scheduler-top-ranked package candidates; weaker rows remain reduced risk; refused/source-gap/unfillable/off-authority rows remain diagnostic/missed.
- Diagnostic: preserve risk ladder, raw/effective action, risk sizing class, risk reduction causes, and risk pct into ledgers.

## Expected Effect Before Replay

- Candidate -> scorecard transfer: should remain broad; no collapse below V111 scorecard row count.
- Scorecard -> order transfer: valid V110B-like source-family transfer should recover without off-configured fallback substitution.
- Order -> fill transfer: expired unfilled should fall versus V111 or move to explicit missed/disabled-fallback reason.
- Missed positive R: may rise if unsafe fallback is demoted, but rows must remain scoreable and visible.
- Missed negative R: refused-cost/source-gap rows remain diagnostic and non-executable.
- Trade count: the 2026-06-03 targeted proof should not collapse to zero and must explain every removed fill.
- Net/gross/final R: helped if V113 improves versus V111 on the same June 3 window without suppressing opportunity.
- W/L/F: added or retained transfers should not be dominated by fallback/off-session losers.
- Cost-refused/source-gap execution: must remain zero.
- Risk-reduced/full-risk distribution: full-risk rows should appear only for signed high-quality package candidates; reduced-risk remains for weaker or uncertain candidates.

## Proof Scope

Run focused tests first. Then run one targeted proof before broad replay:

```bash
PREFIX=BROAD_LIVE_AS_IF_REPLAY_V113_TRANSFER_RISK_EXPRESSION_REPAIR_20260603_REPAIRED_ONLY_COMPACT_FULLGRID
TAG=${PREFIX#BROAD_LIVE_AS_IF_REPLAY_}

python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-06-03 --end 2026-06-03 \
  --profiles repaired_package_conversion_v3 \
  --output-prefix "$PREFIX" \
  --chunk-size 1 \
  --omit-candidate-ledger \
  --compact-missed-ledger

python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py \
  --broad-prefix "$PREFIX" \
  --artifact-tag "$TAG"
```

Success: zero off-configured fallback applied while disabled, zero executed REFUSED/source-gap rows, raw selector action separate from effective action, session_open_range_break candidates remain visible, full-risk/reduced-risk provenance is present, and June 3 retained/added fills are net better than V111 same-window behavior.

Failure: the trade set remains disjoint/negative with V110B-like winners removed and no explicit predecision blocker, or improvement comes only from suppressing opportunity.

Next deeper flaw: if transfer truth improves but R remains weak, rank the next leak from targeted ledgers across scheduler ranking/reallocation, passive-limit fillability, same-symbol lifecycle, and stop/exit geometry.
