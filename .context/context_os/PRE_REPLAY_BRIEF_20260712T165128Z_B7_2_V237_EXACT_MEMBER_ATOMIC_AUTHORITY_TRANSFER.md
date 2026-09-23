# B7.2 V237 Exact-Member Atomic Authority Transfer

Generated UTC: 2026-07-12T16:51:28Z.

Status: targeted proof ready after focused code tests. This brief freezes the
current evidence and acceptance criteria; it does not claim hostile-five-day,
broad-history, final-selection, or live readiness.

## 1. Latest Completed Replay

Prefix:
`BROAD_LIVE_AS_IF_REPLAY_V236_B7_2_CAUSAL_POI_LIFECYCLE_HOSTILE_5D_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`

V236 is a recovered, fully finalized five-day replay with summary schema v2:

| Metric | V236 |
| --- | ---: |
| source / decision / candidate / scorecard rows | 276 / 11,424 / 25,006 / 288 |
| order events / logical terminal orders / fills | 4 / 2 / 2 |
| missed rows | 25,004 |
| W/L/F | 1 / 1 / 0 |
| net / gross / final R | -0.92559780 / -0.79425689 / -0.79425689 |
| cash PnL / risk cash / risk pct sum | -$92.57809253 / $200.01675249 / 0.20% |
| full-risk / reduced-risk fills | 0 / 2 |
| REFUSED-cost / source-gap executed | 0 / 0 |
| executable missed rows / R | 0 / 0.0R |
| diagnostic scoreable missed rows / R | 7,319 / -4,322.71364327R |
| stress +0.05 / +0.10 / +0.20R per trade | -1.02559780 / -1.12559780 / -1.32559780R |
| MC iterations / total net / worst drawdown | 200 / -0.92559780R / -1.09312270R |

V236 improved headline net R versus V219 mainly by executing 21 fewer trades
and paying 1.90164912R less cost. Gross R worsened by about 0.00284661R. This
is opportunity suppression, not accepted value-transfer improvement.

The recovered V236 summary does not recompute the window source-bound R
denominator. The same-window V219 parity artifact reports 1,101 package axes,
894 candidate axes, nine scorecard/order axes, eight filled axes, and
425,333.0444635402R of source-bound diagnostic denominator. That comparator is
not executable R and is not silently relabeled as a V236 denominator.

## 2. Current Process State

No replay, compile, verifier, or non-interactive test process is active. One
stale focused pytest process was found waiting in `--pdb` and terminated; it was
not executing replay work. Context OS stdio sidecars remain active.

### V237 Failed-Before-Simulation Repair

The first V237 launch failed on the first source symbol before any simulation
row was produced. `resolve_h1()` called `rows_by_day()` and received `None`.
Current diff evidence proved an accidental refactor had changed the helper's
direct `return {...}` into `event = {...}` without adding `return event`.

The shared return contract is restored. A direct unit test proves day grouping,
in-day ordering, and invalid-time exclusion; a harness-level test proves derived
H1 rows populate `rows_by_day` and `day_counts`. Compile and both tests pass.
The failed prefix remains explicitly partial and is not behavioral evidence.
The repaired successor prefix is V237R2.

## 3. Baseline Comparison

| Run | Window | Trades | W/L/F | Net R | Gross/Final R | Cash PnL |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| V89D | hostile 5d | 56 | 41/15/0 | +34.84520454 | +39.93441037 | +$8,178.90660707 |
| V90 | hostile 5d | 51 | 37/14/0 | +28.84201157 | +33.36349114 | +$6,371.80465431 |
| V92 | hostile 5d | 51 | 37/14/0 | +29.35570236 | +33.93212860 | +$6,228.63096022 |
| V219 | hostile 5d | 23 | 14/9/0 | -2.82440031 | -0.79141028 | +$204.17530212 |
| V236 | hostile 5d | 2 | 1/1/0 | -0.92559780 | -0.79425689 | -$92.57809253 |

V89D/V90/V92 are historical comparators, not permission to restore their
weaker provenance, fill optimism, or off-session authority.

## 4. Current Dirty Implementation Surface

Behavior-changing correctness repairs:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
  - transfers one atomic execution-fillability atom and the causal POI/lifecycle
    snapshot into both scheduler decision-input namespaces;
  - seeds exact-member open-reduced signing with executable aliases, normalized
    quality floors, causal fillability, and POI lifecycle authority;
  - declares signed-authority requirements before strict self-validation;
  - preserves immutable signed order permission separately from finalizer state.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
  - repairs all public final-risk aliases atomically after the stop-hazard cap.

Diagnostic/verifier correctness repairs:

- `run_broad_live_as_if_replay_harness.py`
- `verify_denominator_to_deployment_execution.py`
- `tests/test_broad_replay_repair_config.py`
- `tests/test_denominator_to_deployment_verifier.py`

Focused scheduler/runtime tests:

- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

No unrelated Context OS changes, historical deletions, or `.context/LIVE_STATE.md`
changes belong to this route checkpoint.

## 5. Reconciled Snapshot Findings

| Agent lane | Disposition | Current-code conclusion |
| --- | --- | --- |
| Averroes, summary/finalization | INCORPORATED | V236 summary recovered under narrow deterministic finalization; automatic GC stays disabled during aggregation/writes. |
| Hume, authority construction | VALID_OPEN THEN PATCHED | The exact-member signing path blocked the high-value in-session cohort through circular/missing authority construction. Current focused reproducer signs valid authority with no failures. Replay proof remains open. |
| Confucius, lifecycle | INCORPORATED / NO POLICY PATCH | The cohort is causally lifecycle-valid and rankable. Lifecycle was not the blocker and must not be loosened. |
| Descartes, reallocation/risk/fillability | VALID_OPEN THEN PATCHED | No valid finalizer replacement existed because upstream candidates were unsigned; JP225 risk aliases and US30 fillability projection were contradictory. Both producers are repaired and focused-tested. Replay proof remains open. |

All agents audited frozen commit `fcbad7065`; all were collected and closed.
Their findings were rechecked against current code before implementation.

## 6. Current Root-Cause Chain

| Stage | Status | Current truth |
| --- | --- | --- |
| source-bound -> candidate | PARTIAL | Supply is not the immediate choke: V219 generated 894/1,101 axes. Seventy-four materialization gaps remain a later B7 source batch. |
| candidate -> selector | FIXED IN CODE / UNPROVEN | Candidate quality and causal fillability now cross the selector event atomically instead of disappearing between nested and flat namespaces. |
| selector -> scheduler | FIXED IN CODE / UNPROVEN | Exact-member open-reduced authority now signs from one complete predecision atom rather than circularly requiring its own finished declaration. |
| scheduler -> risk | FIXED IN CODE / UNPROVEN | Valid signed rows can reach the finalizer; public capped-risk aliases now equal the actual approved risk. |
| risk -> order | FIXED IN CODE / UNPROVEN | Immutable signed order permission remains separate from effective finalizer permission; REFUSED/source-gap rows remain non-executable. |
| order -> lifecycle | VERIFIED FOR COHORT | The target rows were lifecycle-valid/rankable. No lifecycle relaxation is included. |
| lifecycle -> fill | OPEN FOR TARGETED PROOF | Exact 0.5508-0.7617 fillability must survive to order/fill; honest queue expiry remains allowed. |
| fill -> exit | OPEN AFTER TRANSFER | V219 harvest damaged selected-policy R. Exit repair is next only after the transfer cohort executes under current truth. |
| exit -> ledger | PARTIAL | Current-summary, flat authority namespaces, missed lifecycle attribution, and recovery contracts are repaired; post-patch route verification remains open. |

## 7. Highest-Leverage Same-Root Batch

Batch:
`B7_2_EXACT_MEMBER_ATOMIC_AUTHORITY_RISK_AND_FILLABILITY_TRANSFER`

The exact V219 comparator cohort is 18 in-session/router-authorized logical
orders across 2026-05-13..15 and five symbols: `GER40`, `JP225`, `NAS100`,
`US30_cash`, and `XAUUSD`. It contains 13 historical V219 fills and five honest
expiries; the 13 fills were 11W/2L and +3.22861062R.

The V236 candidate surface contains 19 same decision/symbol/side candidates for
those 18 contexts because one GER40 decision has two distinct causal POIs. The
scheduler must rank those two POIs rather than treating both as one order.
Separately, 16 V219 off-session logical orders produced -6.05301093R and remain
blocked absent explicit causal off-session authority.

## 8. Expected Measurable Effect

- Candidate generation: stable for the targeted window; no source rows are
  hidden or deleted.
- Candidate -> scorecard/order: the old
  `package_open_reduced_exact_member_axis_signed_authority_invalid` terminal
  reason must disappear for the covered causally valid cohort.
- Scorecard -> order: should increase from the V236 equivalent slice wherever
  scheduler ranking, risk, cost, session, and lifecycle remain valid.
- Order -> fill: exact fillability and queue realism decide fill versus expiry;
  the proof does not require all 18 orders to fill.
- Missed positive/negative R: remain visible; blocked diagnostics and honest
  expiries stay scoreable under their evidence class.
- Trade count: must increase through restored valid authority, not by weakening
  cost, source, session, lifecycle, or fill rules.
- Net/gross/final R and W/L/F: measured, not preregistered as positive. A
  negative result can still prove the truth repair and expose exit or ranking as
  the next root flaw.
- Risk: public final-risk aliases must equal actual risk; report full-risk and
  reduced-risk rows separately.
- Safety: executed REFUSED-cost and source-gap rows remain exactly zero;
  broker/live/final remain false.

## 9. Targeted Proof

Run V237R2 over 2026-05-13..15 with the five exact cohort symbols and the repaired
package profile. This is the smallest slice covering all 18 historical logical
contexts and all 19 current causal candidate instances.

Helped:

- the old signed-authority-invalid reason is zero for the covered valid cohort;
- at least one previously blocked valid candidate reaches scorecard/order;
- exact fillability and risk aliases remain atomic through trade/missed rows;
- no forbidden cost/source/off-session row executes;
- opportunity is restored rather than suppressed.

Failed:

- the same valid rows remain unsigned or disappear;
- scorecard/order/fill transfer does not move despite valid authority;
- any REFUSED/source-gap/off-session row executes;
- risk or fillability aliases conflict again;
- the result improves only by reducing trade count or hiding missed rows.

Next deeper flaw:

- if authority transfer is correct but selection is still weak, inspect exact
  scheduler ranking/reallocation on the competing POIs;
- if valid orders execute but R remains damaged, compare raw selected-policy
  exit against harvest overlay before any broad policy tuning;
- only after the targeted proof passes should the corrected path return to the
  full hostile-five-day B7.2 window.

This smoke proves or disproves the local repair; it does not prove total
reservoir conversion.
