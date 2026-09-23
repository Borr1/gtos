# V220R13 Signed Fillability Authority-Class Contract Proof

Generated UTC: 2026-07-11T06:13:34Z.

## Current State

- Base commit is `cc4bf946a`; no GTOS replay, builder, verifier, pytest, or
  compile process is active. The four prior subagent IDs are absent and there
  are no unreconciled returns. No new subagent wave is authorized during this
  integration checkpoint.
- V220R12 is the latest completed bounded comparator. It certified the
  no-selected scorecard ownership repair and materialized
  `29/4608/1651/192/6/3/1648` source/decision/candidate/scorecard/order-event/
  trade/missed rows, including 3 terminal orders and 3 source-safe immediate
  marketable fills.
- V220R12 behavior is trades `3`, W/L/F `2/1/0`, net/gross/final R
  `+0.18799082/+0.29037839/+0.29037839`, cash PnL `+18.79934014`, risk cash/
  risk pct `300.00298298/0.3`, cost `0.10238757R`, and full/reduced trades
  `0/3`. Guarded fallback and executed REFUSED/source-gap rows are `0`.
- V220R12 stress net R is `+0.03799082` at `+0.05R/trade`, `-0.11200918` at
  `+0.10R/trade`, and `-0.41200918` at `+0.20R/trade`. Deterministic Monte
  Carlo has 200 iterations and worst/p05/p50 maximum drawdown
  `-0.05292613R`.
- V89D/V90/V92 remain hostile-five-day context at `56/+34.84520454R`,
  `51/+28.84201157R`, and `51/+29.35570236R`; V219 remains the current
  post-B3 hostile-five-day value comparator at `23/-2.82440031R`. None is a
  direct denominator comparator for this two-day/three-symbol contract proof.

## Same-Root Contract Failure

V220R12 proved that selected orders and trades carried a valid immutable
package-new-entry signature and the correct atomic execution-fillability value,
source, timestamp, boundary, and hash. The immutable signed payload did not,
however, contain `execution_fill_probability_authority_class`. Runtime later
projected `signed_predecision_execution_fillability_authority` outside the
signed payload. Bridge, parity, and verifier consumers correctly required the
class to be immutable, so the V220R12 candidate-instance projection classified
all 1,651 candidates as `no_current_stage_authority_envelope` even though three
signed proposals executed.

This is one schema/ownership root across the whole chain, not a policy gate:

1. Scheduler payload producer now signs either the canonical execution-
   fillability class or an explicit missing-fillability class.
2. Required-payload validation binds class semantics to value presence.
3. Runtime immutable projection and alias consumers preserve the signed class
   without overwriting the current raw materialization class.
4. Selected-package bridge requires and projects the exact signed class rather
   than inventing it after signing.
5. Candidate-instance parity and route verifier require the canonical class and
   reject missing, unsafe, or mutable drift.
6. Source-window parity now uses `candidate.trading_day` before decision-time
   fallback, keeping session-boundary rows inside their declared replay day.

## Files And Classification

Correctness and executable-authority contract repairs:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py`

Diagnostic/verifier contract repairs:

- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/analyze_broad_live_as_if_replay_flow.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_timewarp_scheduler_materialization.py`
- `tests/test_broad_replay_repair_config.py`
- `tests/test_build_source_bound_execution_parity.py`
- `tests/test_denominator_to_deployment_verifier.py`

Behavior expectation: neutral. This batch changes the immutable contract and
proof consumers, not selector, scheduler ranking, risk sizing, order geometry,
fill simulation, lifecycle, or exit policy.

## Proof Before Replay

- Python compile passes for all touched production/route modules.
- The current same-snapshot scheduler/runtime/materialization/bridge/parity/
  verifier barrier passes: `1618 passed, 1 warning`.
- Focused tests cover canonical signed class production, explicit missing-class
  semantics, immutable runtime projection, bridge projection, parity rejection,
  verifier rejection, and trading-day source-window ownership.
- V220R12 full-tag parity/flow artifacts are source-scope clean: all 1,651
  candidate rows bind to the selected prefix/profile and `candidate.trading_day`;
  selected-window out-of-window count is zero.

## Expected Measurable Effect

- Candidate -> scorecard remains `1651 -> 192`; candidate-instance scorecard
  presence remains `138` under exact-instance matching.
- Scheduler-selected -> order -> fill remains `3 -> 3 -> 3`.
- Trade count, W/L/F, net/gross/final R, cash PnL, risk cash, risk percentage,
  stress, Monte Carlo, missed diagnostic R, and origin-family transfer remain
  deterministic V220R12 equivalents.
- Executed REFUSED/source-gap remains `0/0`; guarded fallback remains `0`.
- Full/reduced filled-trade distribution remains `0/3` because risk policy is
  outside this batch.
- Signed candidates/orders/trades must carry the canonical fillability class
  inside the immutable payload hash and through prefixed projection.
- Candidate-instance parity must no longer classify valid signed envelopes as
  missing solely because the authority class was absent from the payload.
- Any trade/R/fill delta is failure for this behavior-neutral batch. A correct
  behavior reproduction with a remaining envelope failure exposes the next
  exact consumer/serialization break and blocks route certification.

This smoke proves or disproves the local immutable authority contract. It does
not prove hostile-regime value, broad value, total reservoir conversion, final
selection, or live readiness.

## Command

`PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py --start 2026-05-13 --end 2026-05-14 --profiles repaired_package_conversion_v3 --symbols XAUUSD USDCAD USDJPY --max-candidates-per-symbol-window 0 --output-prefix BROAD_LIVE_AS_IF_REPLAY_V220R13_SIGNED_FILLABILITY_AUTHORITY_CLASS_CONTRACT_REPAIR_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

V220 through V220R12 and the active code/source/comparator inputs remain
protected. No deletion, move, eviction, or Git-clean is authorized during this
bounded proof. A fresh bounded storage review remains mandatory before any
later broad replay.
