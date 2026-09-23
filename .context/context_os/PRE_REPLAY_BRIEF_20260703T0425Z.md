# Pre-Replay Brief - 2026-07-03T04:25Z

Scope: denominator-to-deployment ultimate-system replay repair in `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20`.

Broker/live/final remain false. Local replay/package authority remains full across the 82-sleeve surface.

## 1. Latest Completed Replay

Latest completed broad proof remains:

`BROAD_LIVE_AS_IF_REPLAY_LIFECYCLE_TRUTH_ADAPTIVE_AXIS_REPAIR_V92_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`

- candidate rows: `25,006`
- scorecards: `288`
- terminal orders: `119`
- filled trades: `51`
- missed rows: `24,887`
- net R: `+29.35570236`
- gross/final R: `+33.93212860`
- cash PnL: `+6228.63096022`
- W/L/F: `37/14/0`

Latest completed targeted smoke before the post-compaction V97 proof:

`BROAD_LIVE_AS_IF_REPLAY_PACKAGE_SCOPE_AND_EXTRA_SLOT_REPAIR_V96_20260513_REPAIRED_ONLY_COMPACT_SMOKE`

- candidate-index rows: `8,864`
- scorecards: `96`
- terminal orders: `51`
- filled trades: `15`
- missed rows: `8,813`
- net R: `+5.51066805`
- gross/final R: `+6.94074213`
- expected cost R: `1.43007408`
- cash PnL: `+2113.18149143`
- risk cash / risk %: `2719.49231429` / `2.68125`
- W/L/F: `7/8/0`
- missed scoreable R: `+605.00344588` positive, `-3660.29693267` negative, `-3055.29348679` total
- stress: extra `0.05R` cost `+4.76066805`, `0.10R` `+4.01066805`, `0.20R` `+2.51066805`
- Monte Carlo: `200` iterations, total `+5.51066805`, p50 max drawdown `-3.37319241R`, worst `-6.73103926R`
- broker/live/final: `false`

V96 behavior is materially unchanged from V95. Its value is the pre-patch truth signal: package new-entry authority scope is still fixed to `selector_reduced_risk_to_scheduler_new_position` for selected rows whose target action is `same_direction_scale_in`.

- V96 scope-target mismatch rows: scorecard `18`, order `42`, trade `4`
- dynamic-scope code/test patch after V96: package authority scope now tracks `new_position`, `same_direction_scale_in`, `replace_pending`, and `close_and_reverse`
- V97 proof target: same one-day repaired-only smoke, with scope-target mismatch counts expected to be `0`

## 2. Running Replay Or Audit

No broad replay is running. The V95 route artifact audit completed with `ok=true`, `missing_required=[]`, and `missing_warnings=[]`.

Decision: do not start a broad replay until the next same-root behavioral repair is patched and a targeted proof has a clear success/failure criterion.

## 3. Baseline Comparison

| Run | Scope | Trades | Net R | Gross/Final R | Cash PnL | W/L/F | Boundary |
|---|---|---:|---:|---:|---:|---:|---|
| V89D | 2026-05-13..17 fullgrid | 56 | +34.84520454 | +39.93441037 | +8178.90660707 | 41/15/0 | broad comparator |
| V90 | 2026-05-13..17 fullgrid | 51 | +28.84201157 | +33.36349114 | +6371.80465431 | 37/14/0 | broad comparator |
| V92 | 2026-05-13..17 fullgrid | 51 | +29.35570236 | +33.93212860 | +6228.63096022 | 37/14/0 | latest broad proof |
| V94 | 2026-05-13 one-day smoke | 16 | +6.77427007 | +8.23945742 | +2565.01995828 | 9/7/0 | pre-truth-normalization targeted proof |
| V95 | 2026-05-13 one-day smoke | 15 | +5.51066805 | +6.94074213 | +2113.18149143 | 7/8/0 | targeted truth repair proof |
| V96 | 2026-05-13 one-day smoke | 15 | +5.51066805 | +6.94074213 | +2113.18149143 | 7/8/0 | pre-dynamic-scope mismatch proof |

V95 underperforms V94 because M1 proxy profit-harvest terminal/headline/final-R authority was correctly demoted without ordered-tick truth. That is a truth correction, not opportunity suppression. V96 is equal to V95 on headline behavior and is used as the pre-dynamic-scope mismatch checkpoint.

Denominator boundary: V94/V95 and other one-day or five-day smokes are bounded repair proofs only. They must not be compared directly against the full source-bound reservoir. For each replay, use the exact selected replay-window denominator: source-bound R available inside that window, package axes available inside that window, candidate-generated axes, scorecard/order-present axes, filled-trade axes, and actual executable R. Diagnostic/global reservoir fields remain visible but are not the replay denominator. Interpretation for bounded smokes: “This smoke proves or disproves the local repair; it does not prove total reservoir conversion.”

V95/V96 exact replay-window transfer denominator:

- selected window: `2026-05-13` through `2026-05-13`
- package axes available inside replay window: `1,101`
- source-bound R available inside replay window: `56,984.445501245`
- positive source-bound package axes inside window: `22`
- candidate-generated axes: `853` (`77.475023%` of window package axes)
- scorecard/order-present axes: `13` (`1.524033%` of generated axes)
- filled-trade axes: `7` (`53.846154%` of scorecard/order axes)
- actual executable R inside replay window: `+4.144574` (`0.007273%` of window source-bound R)
- diagnostic global source-bound R shown in the artifact: `1,249,248.03066685`, explicitly not the V95 denominator

This smoke proves or disproves the local repair; it does not prove total reservoir conversion.

## 4. Dirty Files And Active Code Changes

Active checkpoint files:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_denominator_to_deployment_execution.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- focused tests under `tests/`
- V95 route summaries, flow/parity/leakage artifacts, manifest, verification result, and prompt hardening prompt
- `.context/context_os/*` active continuation files

Do not stage unrelated historical science JSONL deletions, unrelated Context OS infrastructure changes, unrelated selector/reduced-risk dirt, `.codex_run_logs/`, or `.context/LIVE_STATE.md`.

## 5. Subagent Findings

- Banach the 2nd: incorporated. The selected-package replay layer was not the authority leak; M1 proxy profit-harvest was re-promoting diagnostic replay into terminal/headline/final-R authority. V95 demotes that path without ordered-tick truth.
- Averroes the 2nd: incorporated. The stop-hazard cap mismatch was not only a compaction issue; scheduler source and projection needed consistent `risk_cap_applied=true` when status/action/cap pct prove a cap. V95 has zero capped-without-risk-cap rows.
- Aquinas the 2nd: incorporated. V94 verifier blockers were limited to selected-policy replay authority and stop-hazard candidate-index truth. V95 verifier is green with `issue_count=0`.
- Helmholtz: incorporated for truth boundary. V95 row-bound context/materialization labels are not proven PnL-moving; do not relabel context-only rows as executable candidate/window truth.
- Heisenberg: incorporated in selector. Router-refusal package repair remains reduced-risk only; full-trade release stays disabled and REFUSED broker-cost/source-gap rows remain non-executable.
- Gauss: incorporated in finalizer. Risk-admitted package reallocations were blocked after target-count fill; patched one bounded additive package transfer slot instead of dropping those rows flat.
- Franklin the 2nd: incorporated. Exact-window denominator reporting is now machine-readable in parity summaries and protected by the verifier contract; one-day/five-day smokes must not be compared to the full 1.249M source-bound reservoir.
- Sagan the 2nd: incorporated. V96 proves same-direction scale-in rows are carrying `new_position` package authority scope; dynamic package scope repair is patched and V97 will prove row parity.
- Hume the 2nd: deferred next. Passive-limit order materialization/fillability fallback envelope and lifecycle-label parity remain the next root batch if V97 is scope-clean or behavior-neutral.

## 6. Known Mismatch Classes

- source-bound -> candidate: `853/1101` axes generate broad replay candidates; `248/1101` remain non-generated or non-executable by explicit labels.
- candidate -> selector: `229` axes still land in `candidate_generated_selector_reject`; next selector repair must target package-admission sleeve overrides without opening cost-refused rows.
- selector -> scheduler: `102` axes are `candidate_generated_not_scheduler_selected`; transfer ranking/reallocation remains a behavioral leak after hard cost/package gates.
- scheduler -> risk: all `51` V95 terminal orders are `open-reduced-risk`; risk finalizer has `41` admitted reallocation probes but `0` selected reallocations.
- risk -> order: broker-cost REFUSED/source-gap rows remain non-executable; executed refused/source-gap counts are zero and must stay zero.
- order -> lifecycle/fill: `36/51` V95 terminal orders expired unfilled; `6` source axes are `order_accepted_not_filled`.
- fill -> exit: V95 has `7` target-first wins, `7` stop-first losses, and `1` M1 time-stop close; raw exit damage is now separated from unproven profit-harvest authority.
- ledger truth: selected-policy authority, stop-hazard capped truth, context envelope, source-bound parity, cost authority, lifecycle root, and adaptive-axis verifier scans are clean.

## 7. Fixed / Partial / Open

Fixed in V95:

- M1 proxy profit-harvest cannot set terminal/headline/final-R authority without ordered-tick truth.
- Stop-hazard capped rows normalize `risk_cap_applied=true`.
- V95 verifier is green: `ok=true`, `issue_count=0`, final/live false.
- Route artifact audit and prompt hardening pass.

Fixed after V95, pending targeted replay measurement:

- `src/components/selector_v4.py` disables router-refusal full-trade release and defaults positive package router-refusal to open-reduced-risk only.
- `run_selected_package_replay_bridge.py` sets the same authority split in the selected-package bridge config.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py` no longer treats generic replay permission as package authority scope; signed/source/admission lineage is required.
- The finalizer preserves original scheduler selection priority before transfer/cost tie-breaks, preventing accidental displacement by generic package flags.
- The finalizer can select one bounded risk-admitted package reallocation extra slot after target count only when source authority, selector reduced-risk origin, broker-calibrated cost, transfer score, and causal quality all pass.
- `build_source_bound_execution_parity.py` emits exact selected replay-window transfer denominator fields and the bounded-smoke interpretation.

Partially fixed:

- scheduler transfer ranking/fillability repairs exist, but V95 source-bound transfer still shows only `13` scorecard/order-present axes, `21` scorecard/order rows, and `10` axis-attributed trades.
- guarded-market fallback exists, but most V95 accepted orders still expire unfilled.
- risk finalizer evaluates reallocations but selects none in V95.

Open:

- selected-package row-bound source/lifecycle context materialization (`73` row-bound missing decision-window/candidate labels, `16` lifecycle-label context gaps);
- selector admission calibration (`229` selector rejects);
- scheduler ranking/reallocation (`102` generated-not-selected axes);
- order/fill lifecycle (`36` expired orders, `6` order-accepted-not-filled axes);
- exit/stop geometry remains a behavioral lane after transfer materialization.

## 8. Highest-Leverage Same-Root Batch To Patch Next

`selected_package_source_context_and_admission_transfer_batch`

Reason: V95 proves the truth-envelope blockers are closed. The highest next same-root issue is that executable source-bound axes do not consistently carry row-bound selected-package source/lifecycle context into selector/scheduler/risk, so valid package candidates either fail materialization, remain generic selector rejects, or never reach reallocation.

Post-V95/V96 measurement batch:

`dynamic_package_new_entry_scope_target_parity_v97_then_passive_limit_fillability_envelope`

Reason: V96 proves selected `same_direction_scale_in` rows still carry `selector_reduced_risk_to_scheduler_new_position` package authority scope. This is a package authority truth mismatch across scheduler, scorecard, order, and trade ledgers. The dynamic-scope patch should make row authority match target action without opening broker-cost/source-gap rows. If V97 is scope-clean but behavior-neutral, the next same-root batch is passive-limit/fillability pre-order envelope and lifecycle label parity, because V96 still has `36/51` terminal orders expired unfilled and `6` source axes in `order_accepted_not_filled`.

## 9. Affected Files / Components

- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `src/components/selector_v4.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- route verifier/tests for selected-package context, selector package admission, and risk finalizer reallocation provenance
- `tests/test_build_source_bound_execution_parity.py`
- `tests/test_selector_v4.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

## 10. Patch Classification

- selected-package row-bound/lifecycle context materialization: correctness repair.
- selector package-admission override for valid admission sleeves: correctness plus performance repair.
- scheduler/risk reallocation after valid package admission: performance repair under existing cost/package gates.
- ledger/verifier additions: diagnostic/ledger repair only when they enforce a real executable contract.
- package authority scope split: correctness repair.
- router-refusal reduced-risk-only authority: correctness repair with performance guardrail.
- bounded finalizer extra-slot: performance repair under existing cost/package/source gates.
- exact replay-window denominator: diagnostic/ledger repair enforcing a real measurement contract.

## 11. Expected Measurable Effect Before Replay

- candidate -> scorecard transfer: increase source-axis scorecard/order-present count above `13` axes, with row count reported separately from axes.
- scorecard -> order transfer: increase cost-passed/package-authorized order attempts without executing broker-cost REFUSED or source-gap rows.
- order -> fill transfer: reduce `36` expired-unfilled orders only when fillability/fallback contract is met.
- missed positive R: reduce materialized positive missed buckets without accepting the large negative cost-refused reservoir.
- missed negative R: keep cost-refused diagnostic negative rows non-executable.
- trade count: may increase, but positive-by-suppression is not acceptable.
- net/gross/final R: should improve or expose whether selector/scheduler admission was correctly blocking bad candidates.
- W/L/F: should not improve solely by suppressing trades.
- cost-refused/source-gap execution: must remain `0`.
- risk-reduced/full-risk distribution: should explain why all terminal orders are reduced and whether valid full-risk allocation is being blocked by finalizer budget, scheduler caps, or source/package authority.

For the immediate targeted replay, compare only against V95/V96 in the same selected window. V97 success requires scope-target mismatch counts of `0` across scorecard/order/trade rows, exact-window denominator fields present with `full_reservoir_transfer_claim_allowed=false`, and cost-refused/source-gap execution still `0`. Behavior improvement is welcome but not required for this truth repair. A behavior-neutral V97 exposes the next limiter: passive-limit/fillability pre-order envelope and lifecycle label parity.

## 12. Proof Criteria

Helped:

- focused tests for context/admission/reallocation pass;
- targeted replay shows improved candidate -> scorecard/order transfer or a lower high-value missed bucket with zero refused/source-gap execution;
- V95 verifier scans remain green;
- the result explains improvement source as conversion/admission/reallocation/fill, not simple blocking.

Failed:

- row-bound/lifecycle context gaps remain unchanged;
- selector rejects remain generic for package-admission sleeves;
- risk finalizer admitted probes still select zero reallocations with no causal reason;
- cost-refused/source-gap rows become executable;
- headline improves only through opportunity suppression.

Exposes next flaw:

- transfer improves but order expiry/fillability or exit stop geometry becomes the dominant limiter. Then run targeted order/fill or exit bucket replay before broad replay.
