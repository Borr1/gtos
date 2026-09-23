# V148 B7 Router-Refusal Self-Lock Authority Repair Pre-Replay Brief

Generated UTC: 2026-07-07T09:53:31Z

This brief is the control surface before the next replay. It follows the saved
Fable implementation sequence and keeps the current dependency at B7. No broad
replay is authorized from this brief. The next replay, if run, must be the same
bounded 2026-06-01..2026-06-05 targeted proof slice used by V147.

## 1. Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V147_B7_SOURCE_BOUND_ROUTER_REFUSAL_MATERIALIZATION_FLOOR_REPAIR_20260601_20260605_TARGETED`.
- Scope: 2026-06-01..2026-06-05, symbols `XAUUSD`, `XAGUSD`, `USDCAD`, `USDJPY`, `UKOIL_cash`, profile `repaired_package_conversion_v3`.
- Rows: candidates `6633`, scorecards `480`, order event rows `13`, simulated orders `6`, filled trades `3`, missed rows `6627`, source-universe rows `62`.
- Headline: net `+0.84449709R`, gross/final `+1.09529478R / +1.09529478R`, cash PnL `+84.46094125`, risk cash `300.06790974`, risk pct sum `0.3`, W/L/F `3/0/0`.
- Invalid execution counts: executed REFUSED cost `0`, executed source-gap `0`, unresolved-fill-floor order/trade `0/0`, live/final authority rows `0`.
- Interpretation: bounded local B7 transfer proof only. It does not prove B7.4 19-day transfer, B7.5 extended-history transfer, or B8 live readiness.

## 2. Running Process State

No broad replay, targeted replay, verifier, py_compile, or pytest process is
running. Stale desktop-app `git diff --numstat` helpers were killed when they
appeared; they are not replay evidence and should not be allowed to consume
the run lane.

## 3. Baseline Comparison

- Required historical hostile comparators from disk, not denominator-equivalent
  to this V148 targeted June 1-5 slice:
  - V89D 2026-05-13..17 fullgrid: 56 trades, `+34.84520454R` net,
    `+39.93441037R` gross/final, cash `+8178.90660707`, W/L/F `41/15/0`.
  - V90 2026-05-13..17 fullgrid: 51 trades, `+28.84201157R` net,
    `+33.36349114R` gross/final, cash `+6371.80465431`, W/L/F `37/14/0`.
  - V92 2026-05-13..17 fullgrid: 51 trades, `+29.35570236R` net,
    `+33.93212860R` gross/final, cash `+6228.63096022`, W/L/F `37/14/0`.
  - Source: `.context/context_os/PRE_REPLAY_BRIEF_20260703T0330Z.md:53-55`.
  - Use: hostile/stress reference only. Do not compare headline R directly to
    the bounded V148 June 1-5 five-symbol proof slice.
- V147 vs V146 targeted: `+1` trade, net delta `+0.29090804R`, added exactly `broadorigin_62cb335107ef114d9725321c@@2026-06-04T17:45:00+00:00`, removed none.
- V147 vs V144 targeted: same three filled trade keys and same net `+0.84449709R`, with cleaner unresolved-fill-floor/order-event surface.
- V128 full five-day B7 reference: 55 trades, `+1.12099062R`, W/L/F `38/17/0`, candidates `35191`, scorecards `480`, order rows `212`, fills `55`.
- V104 same-window comparator: 46 trades, `+14.73101491R`; V128 still had zero common V104 canonical trade keys and trailed V104 by `-13.61002429R`.

## 4. Dirty Files And Active Code Changes

Active V148B files:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260707.md`
- `.context/context_os/CONTINUATION_CURSOR.json`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260707T0953Z_V148_B7_ROUTER_REFUSAL_SELF_LOCK_AUTHORITY_REPAIR.json`
- `.context/context_os/PRE_REPLAY_BRIEF_20260707T0953Z_V148_B7_ROUTER_REFUSAL_SELF_LOCK_AUTHORITY_REPAIR.md`

Unrelated pre-existing dirty files and old deleted raw science ledgers remain
outside this checkpoint scope.

## 5. Subagent Findings Incorporated

- Kepler: incorporated. The 280 displacement-quality rows are not missing data.
  They are cost-passed/source-complete/fillable source-bound opportunities that
  self-locked through stale signed authority. The fix is not to loosen consumer
  gates; it is to rederive only exact source-bound router-refusal self-lock rows
  through signed, predecision, cost/source/fill authority.
- Archimedes: incorporated. The focused proof should cover a positive stale
  restamp/displacement path and negative cost/source/fill cases. Added scheduler
  tests for the signed self-lock path and refused-cost non-bypass.
- Curie: incorporated. The producer surface is not missing fields. The drift is
  downstream in signer/backfill/missed projection. The signer now hydrates
  source-bound aliases from packets/decision inputs, preserves an already-valid
  hash, and missed rows preserve scheduler-materialized intent while effective
  selector action remains reject for non-executable diagnostics.

## 6. Mismatch Classes

- Source-bound -> candidate: partial. Same-window V147 candidates stay visible,
  but high-R source-bound axes still leak before order.
- Candidate -> selector: partial. Source-bound router-refusal rows can still
  carry raw selector reject while materialized package action is valid for
  local replay evaluation.
- Selector -> scheduler: patched in this batch for exact signed
  router-refusal self-lock rows. Source-bound membership is now separated from
  executable package admission; stale self-lock rows can rederive signed
  authority only when predecision/source/cost/fill conditions pass.
- Scheduler -> risk/order: still partial. This patch should remove false
  `source_bound_package_candidate_use_not_allowed` and `authority_hash_mismatch`
  vetoes for the recoverable 280-row class; it must not execute REFUSED,
  source-gap, unresolved-fill-floor, or off-authority rows.
- Order -> lifecycle/fill: unchanged by this patch. Any newly order-eligible
  rows must still pass lifecycle/fillability truth.
- Fill -> exit: unchanged by this patch.
- Ledger/verifier: patched. Missed-row non-executable diagnostics preserve raw
  materialized scheduler action/reason while effective selector/action/risk
  stay non-executable; signer alias hydration has direct tests.

## 7. Fixed / Partial / Open

- Fixed before this patch: B0, B1, B2, B5.
- Done with label before this patch: B3, B4, B6.
- Fixed in V148B focused tests: exact router-refusal signed self-lock
  rederivation and missed-row scheduler-materialization attribution.
- Partial: B7 transfer. The patch is expected to recover some of the 280
  displacement-quality rows or expose the next downstream blocker.
- Open: B7.4 19-day, B7.5 extended history, B8 live path.

## 8. Highest-Leverage Same-Root Batch

V148B B7 same-root batch:

1. Preserve source-bound package membership separately from executable package
   admission in scheduler signing inputs.
2. Permit only exact `source_bound_router_refusal_requires_signed_new_entry_authority`
   self-lock rows to rederive executable authority, and only through signed
   predecision, broker-cost-passed, source-complete, fillable package authority.
3. Hydrate source-bound aliases into the materialized scheduler signer from
   candidate packets and decision inputs.
4. Preserve already-valid package authority hashes during signer refresh.
5. Preserve scheduler-materialized intent in missed diagnostic rows while
   keeping non-executable effective selector/risk fields closed.

## 9. Affected Files And Patch Types

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: correctness and performance repair. Scheduler authority self-lock rederivation, source-bound/admission split, and terminal veto revalidation path.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: correctness and ledger repair. Signer alias hydration/hash preservation plus missed-row materialized-intent projection.
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`: verifier/focused test repair for positive self-lock restamp and negative refused-cost non-bypass.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`: verifier/focused test repair for signer hydration and non-executable missed-row action semantics.
- Matrix/root-cause/pre-replay context files: diagnostic control surface only.

## 10. Focused Proof Already Run

- `python3 -m py_compile src/research/moonshot_scheduler_v4_best_trade_allocator.py src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py tests/test_v4_timewarp_simulated_live_research_loop.py`: passed.
- `python3 -m pytest tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k "source_bound_router_refusal_self_lock or replay_materialized_open_reduced_restamps_stale_authority or source_bound_router_refusal_avoid_feature_role_is_executable_reduced_risk or source_bound_router_refusal_hard_hold_role_not_replay_executable_with_raw_flags" -q`: `7 passed, 249 deselected`.
- `python3 -m pytest tests/test_v4_timewarp_simulated_live_research_loop.py -k "missed_non_executable_authority_preserves_raw_intent or missed_non_executable_normalizer_keeps_package_authority_diagnostic or materialized_scheduler_signer_hydrates_source_bound_aliases_from_packets" -q`: `3 passed, 568 deselected`.

## 11. Expected Measurable Effect Before Replay

- Candidate -> scorecard transfer: candidate and scorecard rows should not
  collapse; expected rows remain near V147 `6633 -> 480`.
- Scorecard -> order transfer: some or all recoverable displacement-quality
  rows should lose false source-bound/hash vetoes; if not selected, they should
  expose a downstream scheduler/risk/fillability/lifecycle blocker.
- Order -> fill transfer: no REFUSED, source-gap, unresolved-fill-floor, live,
  final, or off-authority rows may execute.
- Missed positive R: should decrease only by valid conversion or become more
  accurately classified by downstream blocker reason.
- Missed negative R: must remain visible and scoreable; no positive-by-
  suppression.
- Trade count: can move either direction; any added/removed keys must be
  causal and compared to V147, V146, and V144.
- Net/gross/final R and W/L/F: can move either direction. Correctness is judged
  by removing false authority/hash vetoes without invalid execution.
- Cost-refused/source-gap execution: must remain zero.
- Risk-reduced/full-risk distribution: must remain separately reported.

## 12. Replay Success / Failure Criteria

Helped:

- The `scheduler_vetoed_candidate_package_displacement_quality` class shrinks,
  or its false source-bound/hash veto subreasons shrink materially.
- Added order/trade rows come from signed, cost-passed, source-complete,
  fillable source-bound router-refusal candidates.
- No existing valid V147 trade is removed without a causal predecision reason.
- Invalid execution counts stay zero.

Failed:

- Improvement comes only from trade collapse.
- Any REFUSED, source-gap, unresolved-fill-floor, live, final, or off-authority
  row executes.
- Candidate/scorecard rows collapse without causal blocker proof.
- The 280-row class still fails primarily on false source-bound/hash mismatch,
  meaning the patch missed a downstream consumer.
