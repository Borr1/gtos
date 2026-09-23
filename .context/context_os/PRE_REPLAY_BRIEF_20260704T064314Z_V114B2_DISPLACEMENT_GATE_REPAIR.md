# Pre-Replay Brief - V114B2 Displacement Gate Repair

Generated at: 2026-07-04T06:43:14Z

Route: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20`

## Boundary

Broker/live/final remain closed. Local replay/package authority remains full for the 82-sleeve surface. This is a one-day targeted repair proof for 2026-06-03, not a full-reservoir transfer claim.

## Current Process State

No Python broad replay, pytest, or py_compile process is active. The `pgrep` hits are Chronicle/Codex helper processes whose prompt text contains replay keywords, not live replay harnesses.

## Latest Completed Run

Latest completed prefix:

`BROAD_LIVE_AS_IF_REPLAY_V114B_FILLABILITY_REALLOCATION_TRUTH_20260603_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`

Window: `2026-06-03`

V114B metrics:

- candidate rows: 6603
- scorecard rows: 96
- order rows: 56
- trade rows: 12
- missed rows: 6575
- net R: -2.30082618
- gross/final R: -1.15118996 / -1.15118996
- cash PnL: -230.28228129
- W/L/F: 3/9/0
- expired unfilled: 16
- fallback applied: 6
- executed cost-refused/source-gap: 0/0
- risk decisions: 12 open-reduced-risk

Interpretation: V114B was behavior-identical to V113C. It proved the B1/B2 patch was not yet reaching behavior because a later scheduler displacement gate still emitted `candidate_vetoed_package_fill_floor_quality_failed`.

## Baseline Comparison

Hostile baselines:

- V89D, 2026-05-13..17: 56 trades, +34.84520454 net R, W/L/F 41/15/0.
- V90, 2026-05-13..17: 51 trades, +28.84201157 net R, W/L/F 37/14/0.
- V92, 2026-05-13..17: 51 trades, +29.35570236 net R, W/L/F 37/14/0.

Broad comparators:

- V110B, 2026-06-01..19: 95 trades, +22.80442652 net R.
- V111, 2026-06-01..19: 45 trades, -4.19333138 net R.

Same-window V111/V113C/V114B on 2026-06-03:

- V111: 28 trades, -4.91291701 net R, W/L/F 3/25/0, 58 orders, 1 expired, 22 fallback fills.
- V113C: 12 trades, -2.30082618 net R, W/L/F 3/9/0, 56 orders, 16 expired, 6 fallback fills.
- V114B: 12 trades, -2.30082618 net R, W/L/F 3/9/0, 56 orders, 16 expired, 6 fallback fills.

V113C/V114B improvement over V111 came from removing losing fills, not adding positive transfer.

## V114B Exposed Leak

Bounded candidate parse found 1217 candidate rows with `scheduler_option_status = candidate_vetoed_package_fill_floor_quality_failed`.

Sample row truth:

- broker cost: PASSED
- cost source gap: source_bound_cost_authority_present
- package new-entry authority: valid, failures empty
- replay executable candidate use allowed: true
- source-bound package candidate use allowed: true
- raw selector action: reject
- effective selector action: open-reduced-risk
- selected cell risk pct: 0
- scheduler option status: candidate_vetoed_package_fill_floor_quality_failed
- terminal veto reason: selected_cell_or_requested_risk_missing_nonpositive

Root cause: `_apply_package_soft_authority_displacement_gate` still treated any signed fill-floor invalidation as a hard veto, even after route resolution made unresolved fill-floor authority failures empty. That kept stale raw fill-floor diagnostics executable as a displacement veto.

## Current Dirty Files / Active Changes

Production code:

- `src/components/selector_v4.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`

Tests:

- `tests/test_selector_v4.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

Control/artifacts:

- `.context/context_os/ultimate_system_plan/IMPLEMENTATION_SEQUENCE_ULTIMATE_SYSTEM_FLOW_20260704.md`
- `.context/context_os/ultimate_system_plan/FABLE_ROOT_CAUSE_AUDIT_AND_IMPLEMENTATION_PLAN_20260704.md`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260704T062328Z_V114_B1_B2_PROVENANCE_FILLABILITY_RISK_RELEASE.json`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260704T064314Z_V114B2_DISPLACEMENT_GATE_REPAIR.json`
- this pre-replay brief

## Subagent Findings

Newton: incorporated. V113C/V114B removed V111 losers but added no positive transfer.

Turing: incorporated. Zero requested risk and stale fill-floor authority made package-executable rows runtime-ineligible.

Aquinas: incorporated as boundary. Terminal veto must clear cap-release/full-authority truth.

Bohr: incorporated. Timewarp finalizer helper re-poisoned resolved fill-floor raw failures and soft-probed package-executable runtime-ineligible rows too broadly.

Singer: incorporated. Focused tests are needed around raw/effective selector contract, unresolved-only fill-floor failures, zero-risk bounded release, route family membership, tier context, and account gross/net identity.

V114B2 local trace: incorporated. The remaining behavior leak is scheduler displacement gate, not candidate generation alone.

## Known Mismatch Classes

Source-bound -> candidate: partially fixed. Same-window package axes still require normalized transfer reporting; do not compare one-day smoke against the global reservoir.

Candidate -> selector: fixed for B1 truth. Raw/effective selector action is preserved.

Selector -> scheduler: partially fixed. Fill-floor authority failures are unresolved-only in the earlier authority structures, but displacement gate still consumed the signed invalidation as hard.

Scheduler -> risk: partially fixed. Bounded zero-risk release exists, but V114B showed zero release applied because displacement hard-veto ran first.

Scheduler reallocation: partially fixed. Reallocation hard gate was patched, but displacement hard gate prevented candidate rankability before reallocation could help.

Risk/order/lifecycle/fill: open. If released rows reach orders but expire, fallback/expiry lifecycle is next.

Fill/exit: open. If released rows fill and lose, stop/exit/fill-realism is next.

Ledger: improved. V114B2 adds displacement fields for route-resolved vs unresolved fill-floor quality.

## Patch Batch

Highest-leverage same-root patch now:

- distinguish raw fill-floor diagnostic failure from unresolved fill-floor authority failure in `_apply_package_soft_authority_displacement_gate`;
- allow route-resolved fill-floor-only signed invalidations to remain rankable when broker cost/source/executable authority pass;
- keep unresolved fill-floor authority failures as hard vetoes;
- export `package_displacement_fill_floor_quality_failure_route_resolved` and `package_displacement_fill_floor_quality_authority_unresolved`.

Files/components:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`

Repair type:

- correctness: displacement-gate authority truth;
- ledger: route-resolved vs unresolved displacement diagnostics;
- performance: expected increased valid transfer only where prior veto was stale.

## Verification Before Replay

Passed:

- `python3 -m py_compile` for scheduler, selector, timewarp, focused tests, and B0 audit script.
- Focused scheduler gate pytest: 15 passed.
- Focused V114 batch pytest: 9 passed.

Known warning: pytest reports unknown `asyncio_mode`; this is pre-existing config noise.

## Expected Measurable Effect

- candidate -> scorecard transfer: should hold, no narrowing.
- scorecard -> order transfer: should improve if route-resolved fill-floor rows become rankable and risk-released.
- order -> fill transfer: may improve or expose expiry/fallback lifecycle.
- missed positive R: should fall if released rows were positive executable opportunities.
- missed negative R: may also move; added fills must be attributed.
- trade count: allowed to increase; positive-by-suppression is not acceptable.
- net/gross/final R: not required to improve for this truth patch, but deterioration must expose a named deeper flaw.
- W/L/F: report separately.
- cost-refused/source-gap execution: must remain 0/0.
- risk distribution: likely still mostly reduced until B3 risk ladder; report full vs reduced separately.

## Replay Pass / Fail Criteria

Targeted proof:

`BROAD_LIVE_AS_IF_REPLAY_V114B2_DISPLACEMENT_GATE_REPAIR_20260603_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`

Helped if:

- `candidate_vetoed_package_fill_floor_quality_failed` drops for route-resolved/empty-unresolved fill-floor cases;
- released rows reach scorecard/order/fill or carry an explicit next blocker;
- executed REFUSED/source-gap remains 0/0;
- R accounting drift remains zero.

Failed if:

- fill-floor quality veto count remains unchanged for route-resolved rows;
- improvement comes only from suppressing more trades;
- REFUSED/source-gap rows execute;
- released rows disappear without explicit missed-opportunity reason.

Exposes next deeper flaw if:

- `selected_cell_or_requested_risk_missing_nonpositive` remains dominant after displacement is cleared -> B3 risk-expression ladder.
- orders increase but expire unfilled -> fallback/expiry/lifecycle.
- fills increase but R stays negative -> exit/stop/fill-realism.
