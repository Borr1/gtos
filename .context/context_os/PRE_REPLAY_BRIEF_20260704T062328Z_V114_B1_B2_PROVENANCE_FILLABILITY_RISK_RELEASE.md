# Pre-Replay Brief - V114 B1/B2 Provenance Fillability Risk Release

Generated at: 2026-07-04T06:23:28Z

Route: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20`

## Boundary

Broker/live/final remain closed. Local replay/package authority remains full for the 82-sleeve surface. This checkpoint is a targeted repair proof slice, not a full-reservoir claim and not a live-ready claim.

## Current Process State

No broad replay, pytest, py_compile, git add/diff/status/commit helper, or v4_timewarp process is running before replay. Context OS MCP helpers are background read-only services only.

## Latest Completed Run

Latest completed prefix:
`BROAD_LIVE_AS_IF_REPLAY_V113C_TRANSFER_RISK_EXPRESSION_FILLABILITY_TRACE_TIGHTENED_20260603_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`

Window: `2026-06-03`

V113C metrics:
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

Risk finalizer V113C:
- finalizer rows: 96
- reallocation candidate probes: 24
- admitted probes: 19
- quality blocked probes: 19
- policy blocked probes: 0
- selected probes: 0

## Baseline Comparison

Hostile baselines:
- V89D, 2026-05-13..17: 56 trades, +34.84520454 net R, W/L/F 41/15/0.
- V90, 2026-05-13..17: 51 trades, +28.84201157 net R, W/L/F 37/14/0.
- V92, 2026-05-13..17: 51 trades, +29.35570236 net R, W/L/F 37/14/0.

Broad comparators:
- V110B, 2026-06-01..19: 95 trades, +22.80442652 net R.
- V111, 2026-06-01..19: 45 trades, -4.19333138 net R.

Same-window V111 vs V113C on 2026-06-03:
- V111: 28 trades, -4.91291701 net R, -1.81632146 gross/final R, cash PnL -491.66938909, W/L/F 3/25/0, 58 orders, 1 expired, 22 fallback fills, 16 off-config-disabled fallback fills.
- V113C: 12 trades, -2.30082618 net R, -1.15118996 gross/final R, cash PnL -230.28228129, W/L/F 3/9/0, 56 orders, 16 expired, 6 fallback fills, 0 off-config-disabled fallback fills.
- Trade delta: 0 added, 16 removed, 12 common, removed net R -2.61209083.

Interpretation: V113C improved the one-day headline only by removing losing fills. It did not add positive transfer. This B1/B2 patch must be judged on conversion/reallocation truth, not on another suppression-only improvement.

## Same-Window Source-Bound Transfer

V113C same-window transfer:
- effective source-bound R in replay window: 40965.119787918
- diagnostic combined source-bound signal R: 1249248.03066685
- package axes: 1101
- candidate-generated axes: 856
- candidate-not-generated axes: 245
- scheduler-option-present axes: 854
- scorecard selected axes: 10
- order-present axes: 10
- trade axes: 10
- unique actual R: -3.03266791
- unique cash PnL: -303.46645429

Do not compare this one-day proof directly against the full million-R reservoir. The valid denominator is the exact 2026-06-03 source-bound window above.

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
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`
- this pre-replay brief

B0 artifacts already produced:
- `AUDIT_PROVENANCE_AND_FLAGS_V114.json`
- `BROKER_COST_REFUSAL_HISTOGRAM_V111.json`

## Subagent Findings

Newton: incorporated. V113C removed 16 losing fills vs V111 but added no transfer; all fills remained open-reduced-risk; no broad replay active.

Turing: incorporated. Package-executable, cost-passed, source-complete candidates were made runtime-ineligible by zero requested risk and stale fill-floor authority. Scheduler risk-release and unresolved-only authority patches landed.

Aquinas: incorporated as boundary. Terminal veto must clear cap-release/full-authority truth. Scheduler terminal-veto cap-release clearing landed.

Bohr: incorporated. Timewarp finalizer helper re-poisoned resolved fill-floor raw failures and soft-probed package-executable runtime-ineligible rows too broadly. Helper/finalizer patches landed.

Singer: incorporated. Focused tests added/updated for selector raw/effective semantics, unresolved-only fill-floor failures, zero-risk bounded release, route-family membership, tier context, and account gross/net identity.

## Known Mismatch Classes

Source-bound -> candidate: partially fixed. 856/1101 axes generate candidates in V113C; 245 remain non-generated and must stay in parity ledgers.

Candidate -> selector: fixed for B1. Selector records immutable raw selector_action/selector_reason and explicit candidate_use_allowed_now semantics.

Selector -> scheduler: fixed for B1/B2. Scheduler preserves effective selector action separately and fill-floor authority failures now mean unresolved failures only.

Scheduler -> risk: fixed for B2. Broker-cost-passed, source-complete, package-executable candidates with zero requested risk can get bounded risk when route/fill-floor authority is resolved.

Scheduler reallocation: fixed for B2. Route-resolved fill-floor invalidation no longer hard-blocks reallocation quality, and fallback tier demotion requires an eligible primary trade competitor.

Risk/order/lifecycle/fill: still open. V113C had 16 expired-unfilled orders; if B2 increases valid selections but they expire, fallback/expiry lifecycle becomes the next blocker.

Fill/exit: still open. If B2 increases fills but net R remains negative, stop/exit geometry is the next blocker.

Ledger: fixed for B1. Trade/account rows preserve gross/final R, expected cost, and net_proxy_r separately.

## Patch Batch

Highest-leverage same-root batch patched now:
- B1 provenance truth contract.
- B2 fillability/reallocation truth chain.
- B2 risk-expression transfer for package-executable zero-risk rows.

Files/components:
- selector admission record contract
- scheduler fill-floor authority, reallocation hard gate, zero-risk bounded release, terminal veto clearing, fallback priority context, session-open route family
- timewarp finalizer fill-floor authority fields, soft-probe eligibility, original comparison floor filter, account gross/net fields
- focused tests

Repair type:
- correctness: selector/scheduler/finalizer/risk authority truth
- ledger: gross-cost-net and raw/effective selector provenance
- performance: expected improved transfer only where authority is broker-cost-passed, source-complete, route-resolved, and risk-released

## Expected Measurable Effect

Before replay, expected direction:
- candidate -> scorecard transfer: should hold or improve for package-executable rows; no broad candidate narrowing.
- scorecard -> order transfer: should improve for rows formerly blocked by `selected_cell_or_requested_risk_missing_nonpositive` or stale fill-floor veto.
- order -> fill transfer: may improve, or expose expiry/fallback lifecycle as the next blocker.
- missed positive R: should fall if valid positive package rows move to order/fill; if not, missed reasons must become sharper.
- missed negative R: may also move; do not accept positive by suppressing all opportunity.
- trade count: allowed to move either direction; added/removed trades must be attributed.
- net/gross/final R: not required to improve in this truth patch, but any deterioration must expose a named deeper flaw.
- W/L/F: report separately.
- cost-refused/source-gap execution: must remain 0/0.
- risk distribution: open-reduced can remain, but bounded-release provenance must replace unexplained zero-risk collapse.

## Replay Pass / Fail Criteria

Targeted next proof: 2026-06-03 repaired profile, prefix `V114B_FILLABILITY_REALLOCATION_TRUTH_20260603` or equivalent B1/B2 same-root proof.

Helped if:
- executed REFUSED/source-gap rows remain zero;
- R accounting drift remains zero;
- `selected_cell_or_requested_risk_missing_nonpositive` drops for broker-cost-passed, source-complete, package-executable, route-resolved rows;
- `candidate_vetoed_package_fill_floor_quality_failed` only appears with non-empty unresolved failures;
- reallocation probes and selected probes improve where a top candidate was vetoed;
- added/removed trades are causally attributed with net R.

Failed if:
- improvement comes only from suppressing more trades;
- REFUSED/source-gap rows execute;
- raw fill-floor diagnostics reappear as unresolved authority after route resolution;
- open-reduced rows are still demoted when no eligible primary trade competitor exists;
- new fills are unexplained disjoint replacements.

Exposes next deeper flaw if:
- scheduler/risk transfer improves but orders expire unfilled -> lifecycle/fallback window is next.
- fills improve but R stays negative -> exit/stop geometry is next.
- transfer does not improve despite scheduler truth repairs -> candidate materialization/source-bound eligibility is next.

## Verification Before Replay

Passed:
- `python3 -m py_compile` for selector, scheduler, timewarp, B0 audit script, and focused tests.
- Focused pytest: 7 passed for selector provenance, scheduler route/fill-floor/risk/tier, timewarp account/fill-floor helper.
- Focused pytest: 1 passed for unresolved blocked package replay executable numeric reduce-risk case.

No broad replay has been started for this batch yet.
