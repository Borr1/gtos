# V220R14 Canonical Source-Status Signature Convergence Proof

Generated UTC: 2026-07-11T06:36:06Z.

## Current State

- Base commit remains `cc4bf946a`; no GTOS replay, builder, verifier, pytest,
  compile, or subagent process is active. No subagent return is unreconciled.
- V220R13 is the latest completed bounded replay. It exactly reproduced V220R12:
  `29/4608/1651/192/6/3/1648` source/decision/candidate/scorecard/order-event/
  trade/missed rows; W/L/F `2/1/0`; net/gross/final R
  `+0.18799082/+0.29037839/+0.29037839`; cash PnL `+18.79934014`; risk
  cash/risk pct `300.00298298/0.3`; cost `0.10238757R`; full/reduced trades
  `0/3`; guarded fallback and executed REFUSED/source-gap `0/0`.
- V220R13 stress and Monte Carlo also exactly reproduce V220R12: stress net R
  `+0.03799082/-0.11200918/-0.41200918` at `+0.05/+0.10/+0.20R` per trade;
  200-iteration worst/p05/p50 maximum drawdown `-0.05292613R`.
- V220R13 full-tag parity is source-scope clean for all 1,651 rows and proves
  the signed fillability-class atom reached all 12 signed candidates, all 6
  order events, and all 3 trades.
- The same parity pass found 3 valid executed envelopes, 9
  `cross_stage_authority_envelope_mismatch` rows, and 1,639 unsigned/non-entry
  rows. V220R13 is therefore completed behavior evidence but a failed/partial
  immutable-envelope certification checkpoint.
- V89D/V90/V92 and V219 remain hostile-five-day context, not direct
  denominators for this two-day contract proof.

## Same-Root Failure And Repair

Each of the nine mismatches carried two valid signatures for the same exact
candidate instance. The only payload difference was
`source_completeness_status`: the candidate/scheduler/finalizer envelope signed
`complete`, while a later candidate-owned missed surface signed
`source_completeness_present`. Runtime validation already treats those statuses
as execution-equivalent, but the scheduler payload builder hashed the raw alias.

The repair canonicalizes execution-equivalent complete-source aliases to
`complete` before constructing or comparing the immutable payload. Missing,
degraded, and incomplete statuses remain distinct. The fix belongs at the
signing boundary; parity is not weakened and continues to reject genuinely
different payloads.

Files changed in this sub-batch:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`

Classification: immutable identity/provenance correctness; behavior-neutral.
It changes no selector, scheduler ranking, risk, cost, order, lifecycle, fill,
or exit policy.

## Proof Before Replay

- Python compile passes for all active production/route modules.
- Direct regression proves `complete` and `source_completeness_present` produce
  the same canonical payload and hash while `incomplete` stays hash-distinct.
- The current same-snapshot scheduler/runtime/materialization/bridge/parity/
  verifier barrier passes: `1619 passed, 1 warning`.
- V220R13 flow, parity, leakage, stress, and Monte Carlo artifacts are complete
  and bind all 1,651 candidates to the selected profile/window.

## Expected Measurable Effect

- Candidate -> scorecard remains `1651 -> 192`; exact-instance scorecard
  presence remains `138`.
- Scheduler-selected -> terminal order -> fill remains `3 -> 3 -> 3`.
- Trades, W/L/F, net/gross/final R, cash PnL, risk, cost, stress, Monte Carlo,
  and missed diagnostic R remain exact V220R13 equivalents.
- Signed candidate payloads retain the canonical execution-fillability class.
- `package_authority_valid=True` becomes `12` candidate instances: 3 executed
  and 9 honestly blocked/missed. `cross_stage_authority_envelope_mismatch`
  becomes zero.
- Current order-executable permission remains true only for the 3 executed
  instances; the 9 blocked signatures remain scoreable/missed and cannot gain
  executable authority from immutable proposal validity.
- Executed REFUSED/source-gap and guarded fallback remain `0/0` and `0`.
- Full/reduced filled-trade distribution remains `0/3`.
- Any behavior delta, blocked-candidate execution, nonzero cross-stage conflict,
  or source-scope failure is a failed proof and must be diagnosed before route
  certification.

This smoke proves or disproves local signature convergence. It does not prove
hostile-regime value, broad value, total reservoir conversion, final selection,
or live readiness.

## Command

`PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py --start 2026-05-13 --end 2026-05-14 --profiles repaired_package_conversion_v3 --symbols XAUUSD USDCAD USDJPY --max-candidates-per-symbol-window 0 --output-prefix BROAD_LIVE_AS_IF_REPLAY_V220R14_CANONICAL_SOURCE_STATUS_SIGNATURE_CONVERGENCE_REPAIR_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

V220 through V220R13 and active code/source/comparator inputs remain protected.
No deletion, move, eviction, or Git-clean is authorized during this bounded
proof. A fresh bounded storage review remains mandatory before any later broad
replay.
