# V220R3 Atomic Authority Propagation Targeted Proof

Generated UTC: 2026-07-11T02:07:26Z.

## Current Snapshot

- Base commit: `cc4bf946a` with a scoped dirty B7.2 implementation batch.
- No replay, test, verifier, builder, or subagent process is running.
- Latest completed behavioral replay remains V219 hostile five-day:
  `25006/288/68/23/24972` candidate/scorecard/order/trade/missed rows;
  W/L/F `14/9/0`; net/gross/final R
  `-2.82440031/-0.79141028/-0.79141028`; cash PnL
  `+204.17530212`; full/reduced-risk fills `17/6`; executed
  REFUSED/source-gap rows `0/0`.
- V220R2 completed the bounded campaign but is partial, not certifying:
  `1651/192/0/0/1651` candidate/scorecard/order/trade/missed rows and
  diagnostic scoreable missed R `-117.18932322R`.
- Broker/live/final remain false. Local replay/package authority remains full.

This replay is a bounded structural and local behavioral proof. It does not
prove hostile five-day value, broad holdout strength, total reservoir
conversion, final selection, or live readiness.

## Comparator Baselines

- V89D hostile five-day: 56 trades, `+34.84520454R` net.
- V90 hostile five-day: 51 trades, `+28.84201157R` net.
- V92 hostile five-day: 51 trades, `+29.35570236R` net.
- V218 same-scope two-day/three-symbol: 3 trades, W/L/F `3/0/0`,
  net/gross/final `+1.10761535/+1.35101129/+1.35101129`, cash PnL
  `+989.52983936`, full/reduced-risk fills `1/2`, executed
  REFUSED/source-gap `0/0`.
- V220 and V220R2 are failed structural partials. Neither is a completed
  behavioral comparator.

## V220R2 Root Evidence

- Eight scorecard rows had valid signed predecision authority, signed order
  authority, broker-cost pass, and derived executable package authority.
- All eight were rejected before order materialization by
  `current_signed_authority_projection_mismatch:selected_policy_expected_net_calibration_required`.
- Four of those eight also reported a stale outer
  `execution_fill_probability_source` mismatch.
- The other scorecard rows remain cost-refused, non-admission,
  member-axis-diagnostic, or otherwise non-executable and must not be opened by
  this repair.

## Same-Root Repair Batch

1. A valid selected signed package envelope is the only immutable execution
   fillability source for reduced-risk exception routes; stale outer aliases
   remain diagnostic.
2. Signed quality, cost, order, identity, member-axis, selector, lifecycle, and
   execution-fillability fields are projected atomically to finalizer option,
   decision inputs, probe, candidate, and packet consumers.
3. Canonical lifecycle action is applied before signed authority validation so
   `new_position` versus signed scale-in/replace intent cannot fail only because
   of consumer ordering.
4. Every execution-fillability tuple is bound to the same exact
   `candidate_id@@decision_time_utc` instance before aliases are exposed.
5. Ordinary package `trade` authority may still be rederived from complete
   predecision quality, atomic fillability, source-bound membership, and
   broker-calibrated cost. Its derived allow/reason/source is now projected to
   every finalizer consumer before the second canonical pass, preventing stale
   false resurrection.
6. Bridge, parity, and verifier consumers preserve exact identity, signed
   authority, and lifecycle/fillability attribution without first-valid
   cross-surface stitching.

Items 1-5 are correctness repairs and can change candidate-to-order transfer.
Item 6 is a correctness and proof-surface repair. No date/symbol/session loss
bucket, cost bypass, or trade-suppression rule was added.

## Files And Consumers

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- focused scheduler, runtime, materialization, bridge/parity, broad-config, and
  verifier tests

## Subagent Reconciliation

- Mendel: INCORPORATED. Unsigned self-authorization, cross-surface stitching,
  split fillability tuple, and verifier-contract findings reproduce as fixed.
- Herschel: INCORPORATED. Exact candidate-instance identity, collision, remint,
  and finalizer lookup findings reproduce as fixed.
- Wegener: INCORPORATED. End-to-end identity and fail-open verifier scans and
  reused-ID tests are present and green.
- Earlier Fable audit returns remain recorded in the execution matrix. No
  current return is unreviewed, no agent process is active, and no stale
  snapshot finding is being implemented by assertion alone.

## Root-Cause Chain

- Source-bound -> candidate: exact member axes authorize; carried unmatched
  axes remain diagnostic.
- Candidate -> selector: exact candidate-instance quality and fillability are
  preserved separately from model entry-quality priors.
- Selector -> scheduler: one finalized signed envelope binds quality, cost,
  fill, order, lifecycle, identity, and member axes.
- Scheduler -> risk: selected signed authority is canonical for reduced-risk
  routes; valid derived ordinary-trade authority cannot be overwritten by a
  stale decision-input false.
- Risk -> order: current denial and immutable signed order authority remain
  separate; REFUSED/source-gap rows stay non-executable.
- Order -> lifecycle/fill: lifecycle intent is canonicalized before admission;
  temporal fillability remains exact-instance and predecision.
- Fill -> exit: unchanged in this batch.
- Ledger/verifier: candidate identity, signed authority, fillability, risk, and
  lifecycle provenance remain serialized and verifier-scanned.

## Verification Barrier

- Python compile: passed for every touched production, route, and test module.
- Runtime: `743 passed`.
- Scheduler: `316 passed`.
- Scheduler materialization: `82 passed`.
- Bridge/parity: `231 passed`.
- Route verifier tests: `223 passed`.
- Scoped `git diff --check`: passed.
- Only warning is the existing unknown pytest `asyncio_mode` option.

## Expected Measurable Effect

- Candidate -> scorecard should remain near V220R2 `1651 -> 192`; a material
  change requires exact attribution.
- The eight valid signed/executable V220R2 rows must no longer fail stale
  selected-policy/fill-source projection. At least one honest downstream order
  or a new causal risk/lifecycle block is expected; `192 -> 0` with the same
  mismatch fails the repair.
- The other 184 scorecard rows must remain honestly blocked unless current code
  proves a different complete executable contract.
- Order -> fill is not precommitted; ordered-tick and lifecycle truth decide it.
- Missed positive and negative R remain separate and visible.
- REFUSED/source-gap executed rows remain `0/0`.
- Full/reduced-risk counts and PnL must retain signed risk provenance.
- A positive result created only by deleting candidates or missed rows is not
  acceptance.

## Targeted Command

`PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py --start 2026-05-13 --end 2026-05-14 --profiles repaired_package_conversion_v3 --symbols XAUUSD USDCAD USDJPY --max-candidates-per-symbol-window 0 --output-prefix BROAD_LIVE_AS_IF_REPLAY_V220R3_ATOMIC_AUTHORITY_PROPAGATION_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

## Acceptance

Helped if V220R3 writes a final schema-v2 summary, preserves all candidate and
missed-opportunity accounting, removes the eight stale projection rejections,
restores honest scorecard-to-order transfer, and has zero provisional,
identity, fillability, REFUSED-cost, or source-gap execution leaks.

Failed if the same projection mismatch recurs, derived executable authority is
again overwritten, current denial is reopened, unsigned reduced-risk authority
executes, or opportunity disappears to manufacture headline R.

If structural truth passes but orders still do not fill or trades lose, the
next blocker is selected from current order/lifecycle/fill/exit and missed-R
buckets before any hostile five-day replay.

The V220R2 storage-protection manifest remains active for V220R3 inputs,
comparators, V220R2 partial evidence, and the new successor prefix. No further
cleanup is required before this bounded replay; the next bounded storage
checkpoint is before any later broad replay.
