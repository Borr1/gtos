# V218 B3 Route-Resolved Full-Risk Expression Repair

Generated UTC: 2026-07-09T16:32:00Z.

## Current Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V217_B7_SIGNED_TRANSFER_SELECTED_POLICY_PRECONDITION_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`.
- Scope: bounded proof slice, `2026-05-13..2026-05-14`,
  symbols `XAUUSD, USDCAD, USDJPY`, repaired profile only.
- Behavior: candidates/scorecards/order rows/trades `1651/192/8/3`.
- W/L/F: `3/0/0`.
- Net/gross/final R: `+1.10761535 / +1.35101129 / +1.35101129`.
- Cash PnL / risk cash / risk pct sum: `+277.0648589 / 750.86709783 / 0.75`.
- Expected cost R: `0.24339594`.
- Risk decisions: all filled trades `open-reduced-risk`.
- Executed broker-cost REFUSED/source-gap rows: `0/0`.
- Fill realism: `ordered_tick_entry_touch:3`.
- Same-window source-bound R: `83516.534265543`.
- Package axes/candidate axes/scorecard-order axes/filled axes: `1101/827/2/2`.

This is a targeted repair proof slice, not total reservoir conversion proof.

## Running Replay State

No broad replay, targeted replay, route builder, verifier, pytest, or git fetch
process is running. Active Python processes are Context OS MCP stdio servers and
unrelated local services.

## Baseline Comparison

- V92 hostile 5-day comparator: 51 trades, +29.35570236R net,
  +33.93212860R gross/final, +6228.63096022 cash PnL.
- V211 hostile 5-day post-B1/B5 proof: 18 trades, -3.47466796R net,
  -1.91290882R gross/final, -868.32556257 cash PnL, all accepted orders
  reduced-risk.
- V217 targeted slice: 3 trades, +1.10761535R net, all filled trades
  reduced-risk.

The B3 repair is not expected to recover V92 by itself. It tests whether valid
signed route-resolved rows can express full risk instead of collapsing to
reduced-risk solely because the raw diagnostic fillability field is below the
default full-risk floor.

## Current Dirty Code Changes

- Added `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260710.md`.
- Patched `src/research_infra/v4_timewarp_simulated_live_research_loop.py`.
- Patched `tests/test_v4_timewarp_simulated_live_research_loop.py`.
- This brief and updated root/cursor artifacts are part of the B3 control
  surface.

Unrelated pre-existing dirty files remain outside this checkpoint and must not
be staged or reverted with B3.

## Subagent Findings Disposition

- Dalton: incorporated, cost REFUSED remains non-executable.
- Fermat: incorporated, full-risk path exists for `trade`; B3 gap is reduced
  origins blocked before full-risk promotion.
- Kant: incorporated, stop-loss outcomes remain ordered-tick selected-policy
  stops, not proven profit-harvest damage.
- Meitner: incorporated, current failure concentration is risk/order/fillability
  and stop exposure.
- Pascal: incorporated, removed winners stay visible as missed/candidate rows.
- Kuhn: incorporated through prior stop-pressure and selected-policy repairs.
- Popper/James/Hilbert/Dirac/Halley: incorporated at current evidence level;
  their main control point is to repair same-root conversion before broad replay.

## Top-To-Bottom Mismatch Classes

- source-bound -> candidate: not the immediate B3 blocker in V217; 827/1101
  package axes generated candidates in the bounded window.
- candidate -> selector: signed reduced-origin authority exists; do not promote
  unsigned or source-gap rows.
- selector -> scheduler: selected-policy precondition is verifier-clean after
  V217; preserve explicit selected-policy quality precedence.
- scheduler -> risk: active B3 mismatch. `fill_floor_route_resolved_for_full_risk`
  is recorded, but `route_resolution_full_risk_bypass_allowed` was previously
  hardcoded false, forcing signed route-resolved rows to reduced-risk.
- risk -> order: preserve broker-cost/source-gap non-executable behavior.
- order -> lifecycle -> fill: no new lifecycle patch in B3; targeted replay must
  report selected/skipped/expired/filled unchanged or exactly changed.
- fill -> exit: B3 does not tune exit policy.
- ledger: raw below-floor fillability remains visible; route-resolution bypass
  is its own field and is true only for causal accepted bypass.

## Patch Batch

Batch: `B3_ROUTE_RESOLVED_FULL_RISK_EXPRESSION_REPAIR`.

Files:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260710.md`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`
- `.context/context_os/CONTINUATION_CURSOR.json`

Patch types:

- Correctness: route-resolved fill-floor authority can satisfy the full-risk
  fillability condition only when signed, broker-cost-passed, source-complete,
  replay-executable, top-ranked/transfer-authorized, and unresolved failures are
  empty.
- Performance: valid package rows can express full risk instead of permanent
  reduced-risk.
- Diagnostic: raw fillability below floor is preserved separately from the
  route-resolution bypass.

## Focused Verification Completed

- `python3 -m py_compile src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_v4_timewarp_simulated_live_research_loop.py`: passed.
- Focused pytest cluster: `10 passed`, warning only for existing unknown
  `asyncio_mode` config.

Key focused assertions:

- Signed, cost-passed, source-complete, route-resolved, no-unresolved-failure
  rows promote to full-risk even when raw execution fill probability is below
  the default full-risk floor.
- Unresolved fill-floor failures still block full-risk and preserve
  `execution_fillability_below_full_risk_floor`.
- Rank control still blocks full-risk when original rank is not top and no
  transfer-dominance authority exists.
- Signed-authority tampering, lifecycle rejection, and stop-hazard cap behavior
  remain protective.

## Expected Measurable Effect

- candidate -> scorecard transfer: neutral for unit proof; targeted replay may
  remain unchanged.
- scorecard -> order transfer: neutral unless promoted risk changes finalizer
  headroom/reallocation.
- order -> fill transfer: neutral unless full-risk headroom changes accepted
  order set.
- missed positive/negative R: should be reported; no positive-by-suppression
  accepted.
- trade count: likely neutral for the smallest V217-like targeted replay.
- net/gross/final R: R-multiple may be neutral if trade set is unchanged.
- cash PnL/risk cash/risk pct: expected to change if V217-like filled rows
  promote from 0.25 risk to 1.0 risk.
- W/L/F: likely neutral for V217-like targeted replay.
- cost-refused/source-gap execution: must remain `0/0`.
- risk distribution: targeted proof should show at least one full-risk row if
  V217-like rows satisfy route-resolution conditions in replay ledgers.

## Targeted Replay Success / Failure Criteria

Helped:

- Full-risk vs reduced-risk distribution changes for valid signed
  route-resolved rows.
- Broker-cost REFUSED/source-gap execution remains `0/0`.
- No unsigned, unresolved-fill-floor, source-gap, cost-refused, or off-authority
  row promotes to full-risk.
- Trade count/order/fill changes are explained by risk headroom/reallocation.

Failed:

- Full-risk remains zero because another causal blocker now dominates; classify
  that blocker exactly.
- Any cost/source/unresolved/off-authority row executes or promotes.
- Positive result comes only from opportunity suppression.

Next replay should be the smallest V217-like targeted B3 proof, not a broad B7
run. Broad B7 resumes only after this B3 proof is parsed.

Broker/live/final remain closed.
