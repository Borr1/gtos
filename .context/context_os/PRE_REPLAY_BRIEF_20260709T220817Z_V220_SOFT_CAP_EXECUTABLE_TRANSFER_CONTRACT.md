# V220 Pre-Replay Brief - Soft-Cap Executable Transfer Contract

Generated UTC: 2026-07-09T22:08:17Z.

## Current State

- Latest completed replay: `BROAD_LIVE_AS_IF_REPLAY_V219_B7_2_HOSTILE_5D_AFTER_B3_RISK_EXPRESSION_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`.
- Scope: hostile 2026-05-13 through 2026-05-17, repaired profile, compact full grid.
- No replay, analyzer, parity builder, pytest, or route builder is active.
- A read-only git fetch helper is still being allowed to finish; the current remote ref already proves the required VPS freshness floor is an ancestor.
- Broker/live/final remain false. Local replay/package authority remains full.

V219 numbers:

- source/candidate/scorecard/order/trade/missed rows: `276 / 25006 / 288 / 68 / 23 / 24972`;
- W/L/F: `14 / 9 / 0`;
- net/gross/final R: `-2.82440031 / -0.79141028 / -0.79141028`;
- cash PnL: `+204.17530212`;
- risk cash / risk pct: `15451.27872744 / 15.25`;
- expected cost: `2.03299003R`;
- order risk actions: `trade=52`, `open-reduced-risk=16`;
- filled risk actions: `trade=17`, `open-reduced-risk=6`;
- expired unfilled: `11`;
- executed broker-cost REFUSED/source-gap: `0/0`;
- fills: `fvg_fill=23` only.

V219 parity refresh is complete: `18901` parity rows and `1101` leakage buckets. Its executable-gated same-window source-bound R is `425333.0444635402`; global diagnostic reservoir values are not this replay denominator.

## Baselines

| Run | Candidates | Scorecards | Order events | Trades | Net R | Gross/final R | Cash PnL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| V89D | 25006 | 288 | 243 | 56 | +34.84520454 | +39.93441037 | +8178.90660707 |
| V90 | 25006 | 288 | 233 | 51 | +28.84201157 | +33.36349114 | +6371.80465431 |
| V92 | 25006 | 288 | 239 | 51 | +29.35570236 | +33.93212860 | +6228.63096022 |
| V219 | 25006 | 288 | 68 | 23 | -2.82440031 | -0.79141028 | +204.17530212 |

The V92 trade set is not an executable target under current truth: only 2 of 51 V92 trade instances also fill in V219; the 49 removed V92 instances have 47 scoreable V219 counterfactuals totaling `-7.89025822R`. Current broker-cost and fill-realism gates therefore supersede blind V92 parity.

## Subagent Disposition

- Bacon: INCORPORATED. Candidate and scorecard generation match V92; the collapse is scorecard-to-order breadth. Conditional same-window transfer is required, not an origin-family allow-all.
- Dirac: INCORPORATED. Candidate quality fields exist, but selected and probe scorecard namespaces do not form one canonical consumed contract. Runtime and verifier lanes own the repair.
- Feynman: INCORPORATED. V219 has zero broker/source authority leaks. The 11 selected expiries need exact fallback terminal proof; cost-refused and broad fill-floor pools remain blocked.
- Sagan: INCORPORATED/DEFERRED BY DEPENDENCY. Profit harvest is net positive in V219 and did not cause the nine stop losses. Stop losses are an upstream admission/risk-expression issue; exit tuning is not part of this batch.
- Peirce: INCORPORATED. A green verifier can remain bound to an older replay prefix. The verifier lane is making current-prefix and parity-artifact binding fatal.
- Three current implementation workers use `gpt-5.6-sol` at `max` reasoning with disjoint runtime, parity, and verifier ownership.

## Root-Cause Chain

1. Source-bound to candidate: operational; `894/1101` package axes generate candidates in current parity.
2. Candidate to selector: quality values are present, but generic reason families still mix exact source, authority, and lifecycle failures.
3. Selector to scheduler: scorecard construction remains broad, but executable contract failures leave 228/288 windows with no hard-clean executable comparator.
4. Scheduler to risk: 14 signed, cost/source-clean, order-executable candidates have no raw hard failures, yet `predecision_stop_hazard_guard_capped` subtracts an absolute `1.25` from a risk-scaled transfer score. The resulting negative soft score is appended to `hard_gate_failures` as `reallocation_quality_score_below_floor`.
5. Risk to order: the finalizer then treats that soft risk cap as an executable-quality rejection. This is a units/semantics mismatch, not an honest hard gate.
6. Order to lifecycle/fill: 11 selected passive orders expire; fallback terminal eligibility/counterfactual truth is incomplete.
7. Fill to exit: profit harvest is positive overall; selected-policy stop losses remain a later upstream risk/geometry batch.
8. Ledger/verifier: V219 parity exists, but current root/cursor and verifier prefix binding are stale at V218.

Exact V219 soft-cap leak:

- selected-policy executable-quality failures: `25` rows, 17 scoreable, `+5.37675553R`;
- soft stop-cap/no-raw-hard-failure subset: `14` rows, 11 scoreable, W/L `10/1`, `+5.37737681R`;
- remaining low execution-fill/distance subset: `11` rows, 6 scoreable, net `-0.00062128R`; it stays blocked;
- the 14-row subset is already runtime eligible, order-executable, broker-cost passed, source complete, and signed. Risk remains capped/reduced.

## V220 Same-Root Batch

Batch: `B7_2_SOFT_CAP_EXECUTABLE_TRANSFER_CONTRACT`.

Files/components:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`;
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`;
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py` and focused tests through the runtime worker;
- parity/analyzer and verifier files through disjoint workers;
- repaired-profile scheduler config only where the repaired contract has a real consumer.

Patch classifications:

- Correctness: split raw hard-gate failures from soft risk-cap demotion; a capped risk score cannot become a hard non-executable label by units accident.
- Performance: allow hard-clean, signed, capped candidates to remain in finalizer reallocation while preserving reduced risk and lower rank.
- Diagnostic: canonical candidate-instance quality, terminal fallback proof, exact blocker taxonomy, V219/V220 current-prefix enforcement.

Expected effects before replay:

- candidate to scorecard: unchanged `25006 -> 288`;
- scorecard to order: may increase only for the 14 hard-clean soft-capped candidates that survive same-window/headroom/lifecycle ranking;
- order to fill: no assumed increase; selected passive orders still must satisfy ordered-tick truth;
- missed positive R: should fall if hard-clean capped candidates transfer;
- missed negative R: may also fall by the one known losing row; no outcome field enters policy;
- trade count: must not fall by suppression;
- net/gross/final R and W/L/F: measured, not assumed;
- cost REFUSED/source-gap executions: must remain `0/0`;
- risk distribution: recovered rows remain reduced/capped, never promoted to full risk solely by this repair.

Help criteria:

- focused tests prove soft-capped/no-raw-hard-failure candidates remain eligible while hard cost/source/fill/lifecycle failures and genuinely negative non-cap candidates remain ineligible;
- targeted projection or replay transfers at least one previously hard-misclassified row without suppressing existing opportunities;
- canonical selected/probe quality has one exact candidate-instance source;
- expired selected orders expose fallback eligibility, blocker, and counterfactual presence;
- verifier is bound to the current prefix and required parity artifacts.

Failure or next-flaw criteria:

- no candidate reaches order because a later lifecycle/headroom/finalizer gate still treats the soft cap as hard;
- recovered rows remain net negative under a non-hostile objective regime;
- any REFUSED/source-gap/unresolved hard-fill row executes;
- behavior improves only by deleting existing trades;
- after the soft-cap repair, stop-loss pressure or terminal expiry becomes the dominant remaining causal bucket.

This is a focused B7.2 contract repair. It is not total-reservoir conversion proof, final selection, or live readiness.
