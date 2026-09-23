# V220R2 Authority-Integrity Targeted Proof

Generated UTC: 2026-07-10T17:21:41Z.

## Current State

- Latest completed behavioral replay remains V219 hostile five-day:
  `BROAD_LIVE_AS_IF_REPLAY_V219_B7_2_HOSTILE_5D_AFTER_B3_RISK_EXPRESSION_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`.
- V219 rows candidate/scorecard/order/trade/missed:
  `25006/288/68/23/24972`; W/L/F `14/9/0`;
  net/gross/final R `-2.82440031/-0.79141028/-0.79141028`;
  cash PnL `+204.17530212`; full/reduced-risk fills `17/6`;
  executed broker-cost REFUSED/source-gap `0/0`.
- Failed V220 is preserved as partial proof, not a completed replay:
  `1651` candidates, `192` scorecards, `0` orders, `0` trades, `1651` missed.
  Twelve risk-finalizer probes failed selected-policy expected-net calibration
  projection, and current-summary certification rejected stale/provisional
  authority surfaces. Diagnostic missed scoreable R was `-117.18932322R`.
- No replay, test, verifier, or builder is running. Context OS sidecars are idle.
- Broker/live/final remain false. Local replay/package authority remains full.

This targeted replay proves or disproves the local authority-integrity repair.
It does not prove total reservoir conversion, hostile five-day value, broad
holdout strength, final selection, or live readiness.

## Baselines

- V89D hostile five-day: 56 trades, `+34.84520454R` net.
- V90 hostile five-day: 51 trades, `+28.84201157R` net.
- V92 hostile five-day: 51 trades, `+29.35570236R` net.
- V218 same-scope two-day/three-symbol comparator: 3 trades, W/L/F `3/0/0`,
  net/gross/final `+1.10761535/+1.35101129/+1.35101129`, cash PnL
  `+989.52983936`, full/reduced-risk fills `1/2`, executed REFUSED/source-gap
  `0/0`.
- V220 failed partial is the direct structural comparator; V219 remains the
  broader behavior comparator.

## Same-Root Repair Batch

1. Candidate-instance fillability precedence now uses selector event, then the
   signed candidate-instance packet, then candidate fallback. Weak recomputation
   cannot overwrite a stronger predecision packet.
2. Router/lifecycle floor bypass is restricted to a fully proven
   close-and-reverse transition with exact identity and opposite release IDs.
   Legacy scale-in or router-refusal rows cannot bypass floors.
3. Normal runtime validation prefers scheduler-selected signed authority;
   scheduler-row finalization deliberately prefers the authority it just
   finalized. This removes stale raw-candidate and stale component precedence.
4. Provisional authority cannot reuse a different nested legacy signature. It
   is finalized from the completed scheduler row exactly once.
5. Fill-floor softening and router-refusal authority families remain separate,
   so one family cannot accidentally invoke the other's execution floors.
6. Global envelope selection honors an explicitly designated valid nested
   authority before generic flattened surfaces; unselected conflicting hashes
   remain fatal.
7. Bridge source time is explicit source/candle provenance only; decision time
   is no longer fabricated as source time.
8. Bridge hydration preserves nested predecision fillability for strict
   consumers without projecting it into unsigned flat authority aliases.

Classification: items 1-8 are correctness repairs. Items 1, 3, 5, and 6 are
also expected to restore valid candidate-to-order transfer. Verifier and ledger
assertions are diagnostic proof, not independent policy.

## Files In This Batch

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- focused scheduler, runtime, materialization, bridge, broad-config, and verifier tests

Other dirty worktree files are not part of this replay command and must not be
reverted or staged accidentally.

## Verification Before Replay

- Scheduler: `307 passed`.
- Runtime: `725 passed`.
- Scheduler materialization: `82 passed`.
- Selected-package bridge: `130 passed`.
- Route verifier tests: `158 passed`.
- Combined materialization/bridge/verifier: `370 passed`.
- All touched Python modules compile with
  `PYTHONPYCACHEPREFIX=/tmp/gtos-pyc-v220`.
- Scoped `git diff --check` passes.
- Only warning is the existing unknown pytest `asyncio_mode` option.

## Subagent Disposition

- Popper: INCORPORATED, exact member-axis identity and scheduler proof.
- Kant: INCORPORATED, strict runtime fixture and contract audit.
- Curie: INCORPORATED, diagnostic-only missing-fill scoring and hash binding.
- Euler: INCORPORATED, current-denial and selected-input precedence.
- Ohm: INCORPORATED, provisional-marker and count-only verifier failures.
- Boole: INCORPORATED, scheduler/runtime authority-family findings.
- Archimedes: INCORPORATED, bridge producer/consumer and source-time findings.
- No returned finding in this batch is waiting on an unreviewed subagent.

## Root-Cause Chain Status

- Source-bound -> candidate: exact member axes are signed; unmatched carried
  axes remain diagnostic.
- Candidate -> selector: candidate-instance packet quality/fillability now has
  canonical precedence.
- Selector -> scheduler: selected authority and finalized-row authority have
  explicit, context-dependent precedence.
- Scheduler -> risk: provisional and stale nested signatures cannot self-lock
  or invalidate the finalized row.
- Risk -> order: current denial remains fail-closed; valid selected authority
  is not displaced by unrelated flattened aliases.
- Order -> lifecycle/fill: only proven close/reverse can override lifecycle
  floors; fill evidence remains predecision and hash-bound.
- Fill -> exit: unchanged in this batch.
- Ledger/verifier: finalized rows reject provisional markers, malformed exact
  identity, and conflicting unselected current envelopes.

## Expected Measurable Effect

- Candidate -> scorecard: expected near-neutral against failed V220
  `1651 -> 192`; a large change requires exact reason attribution.
- Scorecard -> order: should recover valid signed rows from failed V220's
  `192 -> 0` collapse. REFUSED/source-gap/unfillable rows remain missed.
- Order -> fill: no fixed count is assumed; ordered tick truth remains required.
- Missed positive/negative R: must be measured separately and remain visible.
- Trades and R: compare against V218 same scope and failed V220. A positive
  result caused only by fewer opportunities is not acceptance.
- Cost REFUSED/source-gap executions: must remain `0/0`.
- Full/reduced risk: both counts and PnL must retain signed provenance.
- Current-summary schema-v2 certification must complete with zero provisional,
  exact-axis, or authority-envelope failures.

## Targeted Command

`PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py --start 2026-05-13 --end 2026-05-14 --profiles repaired_package_conversion_v3 --symbols XAUUSD USDCAD USDJPY --max-candidates-per-symbol-window 0 --output-prefix BROAD_LIVE_AS_IF_REPLAY_V220R2_AUTHORITY_INTEGRITY_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

## Acceptance

Helped if V220R2 writes a final schema-v2 summary, has zero authority/provisional/
exact-axis/cost/source execution leaks, restores valid scorecard-to-order flow,
and does not improve by deleting opportunity.

Failed if it repeats the `192 -> 0` collapse without honest non-executable
reasons, reopens a current denial, executes REFUSED/source-gap rows, or cannot
certify serialized authority.

The next deeper flaw is exposed if structural truth passes but scheduler
reallocation, expiry/fillability, stop geometry, or exit behavior dominates the
same-scope loss and missed-positive buckets.

Storage protection and the bounded cleanup decision are recorded in
`.context/context_os/V220R2_ACTIVE_ARTIFACT_REQUIREMENTS_AND_STORAGE_CHECKPOINT_20260710T172141Z.md`.
