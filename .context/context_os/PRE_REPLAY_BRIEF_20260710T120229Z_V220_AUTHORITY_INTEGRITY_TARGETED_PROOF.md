# V220 Authority-Integrity Targeted Proof

Generated UTC: 2026-07-10T12:02:29Z.

## Current State

- Latest completed replay: `BROAD_LIVE_AS_IF_REPLAY_V219_B7_2_HOSTILE_5D_AFTER_B3_RISK_EXPRESSION_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`.
- Scope: hostile five-day repaired profile, full configured symbol grid.
- Rows: source/candidate/scorecard/order/trade/missed `276/25006/288/68/23/24972`.
- W/L/F: `14/9/0`.
- Net/gross/final R: `-2.82440031/-0.79141028/-0.79141028`.
- Cash PnL/risk cash/risk percent sum: `+204.17530212/15451.27872744/15.25`.
- Filled full-risk/reduced-risk rows: `17/6`.
- Executed broker-cost REFUSED/source-gap rows: `0/0`.
- No replay, analyzer, parity builder, route builder, pytest, or verifier is running.
- Broker/live/final remain false. Local replay/package authority remains full.

## Baselines

- V89D hostile five-day: 56 trades, `+34.84520454R` net.
- V90 hostile five-day: 51 trades, `+28.84201157R` net.
- V92 hostile five-day: 51 trades, `+29.35570236R` net.
- V218 bounded two-day/three-symbol proof: 3 trades, W/L/F `3/0/0`, net/gross/final `+1.10761535/+1.35101129/+1.35101129`, cash PnL `+989.52983936`, filled full/reduced risk `1/2`, executed REFUSED/source-gap `0/0`.
- V219 is the current broad behavioral comparator; V218 is the same-scope comparator for this targeted proof.

This targeted replay proves or disproves the local authority-integrity repair. It does not prove total reservoir conversion, broad holdout success, final selection, or live readiness.

## Active Code And Test Changes

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- scheduler, runtime, verifier, parity, and bridge focused tests
- no config relaxation and no broker/live activation

Combined focused proof is green: scheduler/runtime/verifier `1123 passed`; route integration `359 passed`; all touched Python modules compile.

## Subagent Disposition

- Popper: INCORPORATED. Scheduler exact-axis identity rejects count-only membership; scheduler suite green.
- Kant: INCORPORATED. Runtime fixtures migrated to strict identity, cost, fillability, order-triplet, and lifecycle contracts; full runtime suite was reduced to two production defects before the final batch.
- Curie: INCORPORATED. Missing execution fill remains `None` in signed atoms; scoring fallback is diagnostic-only; exact member-axis IDs are hash-bound.
- Euler: INCORPORATED. Current order denials beat signed allow, complete cost/fill atoms are validated, selected scheduler inputs win, and unmatched carried axes are diagnostic-only.
- Ohm: INCORPORATED. Finalized ledgers reject provisional-marker leakage and count-only/malformed exact-axis identity.
- Boole and Archimedes: INCORPORATED. Their production findings formed this same-root batch; no finding was deferred.

## Root-Cause Chain

1. Source-bound to candidate: actual member-axis matches now materialize exact stable IDs; unmatched carried IDs cannot authorize execution.
2. Candidate to selector: selected scheduler decision inputs outrank generic/stale candidate inputs while current instance identity remains authoritative.
3. Selector to scheduler: provisional signatures are removed, final quality/cost/fill is signed once, and the final authority map wins component synchronization.
4. Scheduler to risk: missing execution fill may contribute a diagnostic scoring fallback but is not written into signed execution-fill atoms.
5. Risk to order: mutable current risk/lifecycle/fill denial remains fail-closed over a signed allow; signed denial still beats mutable allow.
6. Order to lifecycle/fill: unresolved or missing execution fill remains non-order-executable without corrupting the immutable signature.
7. Fill to exit: unchanged in this batch.
8. Ledger/verifier: provisional marker leakage and count-only finalized identity are fatal.

## Patch Classification

- Correctness: exact-axis hash binding, full atomic cost/fill binding, selected-input precedence, immutable/current order authority separation.
- Performance: valid signed rows no longer become invalid solely because scheduler scoring substituted a missing-fill sentinel.
- Diagnostic: missing-fill scoring fallback, unmatched carried axes, and current-denial-over-signed-allow are explicit fields.

## Expected Targeted Effects

- Candidate to scorecard: expected neutral versus the V218 same-scope comparator.
- Scorecard to order: valid signatures should remain valid; genuinely missing/unfillable execution paths remain blocked.
- Order to fill: no increase is assumed; fills still require ordered-tick truth.
- Missed positive/negative R: measured, not assumed.
- Trade count and net/gross/final R: measured, not assumed; no positive-by-suppression acceptance.
- Cost REFUSED/source-gap executions: must remain `0/0`.
- Full/reduced risk: must remain causally explained and preserve provenance.
- Finalized provisional-marker leaks and exact-axis identity failures: must be zero.

## Targeted Command

`PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py --start 2026-05-13 --end 2026-05-14 --profiles repaired_package_conversion_v3 --symbols XAUUSD USDCAD USDJPY --max-candidates-per-symbol-window 0 --output-prefix BROAD_LIVE_AS_IF_REPLAY_V220_AUTHORITY_INTEGRITY_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

## Acceptance

Helped if the run completes with no authority/provisional/exact-axis/cost/source leak, retains valid signed package rows, keeps missing-fill rows diagnostic/non-order-executable, and does not reduce opportunity merely to improve R.

Failed if exact-axis IDs do not materialize from actual member matches, all package signatures become invalid, any mutable denial is reopened, any REFUSED/source-gap row executes, or the run improves only by deleting existing trades.

The next deeper flaw is exposed if structural truth is green but scorecard-to-order breadth, expiry/fillability, scheduler reallocation, stop geometry, or exit behavior remains the dominant bounded-window loss or missed-opportunity bucket.
