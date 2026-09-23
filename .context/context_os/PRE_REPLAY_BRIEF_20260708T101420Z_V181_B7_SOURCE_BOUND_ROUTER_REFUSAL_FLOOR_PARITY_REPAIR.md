# V181 B7 Pre-Replay Brief - Source-Bound Router-Refusal Floor Parity Repair

Generated UTC: 2026-07-08T10:14:20Z

## Control State

- Fable ladder active batch: B7 package replay conversion and scheduler/order/risk transfer.
- Broker/live/final: closed. Local replay/package authority: full.
- This is a targeted proof slice only: XAUUSD, 2026-06-04..2026-06-05, `repaired_package_conversion_v3`.
- No broad replay, focused test, or compile process is active before this run.
- Rawls subagent remains active/pending on the displacement-quality bucket. Sartre is incorporated and closed: the 219 missing-order-authority bucket stays diagnostic-only.

## Latest Completed Local Replay

V180 prefix:
`BROAD_LIVE_AS_IF_REPLAY_V180_B7_SELECTED_POLICY_STOP_HAZARD_AND_OPTION_BINDING_REPAIR_20260604_20260605_XAUUSD_TARGETED`

V180 local metrics:
- candidates/scorecards/order events/trades/missed/buckets: 1130 / 184 / 15 / 6 / 1122 / 30
- net/gross/final R: +1.43436072 / +1.98898776 / +1.98898776
- cash PnL: +788.05489059
- expected cost R: 0.55462704
- W/L/F: 5 / 1 / 0
- cost-refused/source-gap executed: 0 / 0
- missed diagnostic opportunity R: -124.13136470, positive +60.78623597, negative -184.91760067

## Incorporated Findings

- Sartre: incorporated. `package_replay_order_executable_authority_missing` is genuine diagnostic probe inventory, not an exact-option resolver gap: 219/219 candidate rows exist, 0/219 order or scorecard selected keys, 55 scoreable rows net -24.57254678R. No broad release.
- Darwin/Poincare from V180: already incorporated in exact scheduler option binding, selected-policy stop-hazard semantics, and raw-reject alias projection.
- Current disk inspection: source-bound router-refusal materialization was signed through numeric-disagreement/open-reduced floors in `_candidate_option`, while the repaired profile configures source-bound router-refusal replay materialization floors. That can demote valid source-bound router-refusal rows in displacement-quality/missed consumers.

## Patch Batch

Same-root B7 chain:
- source-bound router-refusal floor family;
- signed new-entry authority validation;
- scheduler candidate decision proof projection;
- displacement-quality safety tests.

Files:
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`

Correctness repairs:
- Source-bound router-refusal materialization now uses `scheduler_v4_best_trade_allocator_source_bound_router_refusal_replay_materialization_min_*` / positive predecision router-refusal floors instead of stale numeric-disagreement open-reduced floors.
- Validation now reads first-class `source_bound_router_refusal_materialization_floors` for source-bound router materialization, while numeric-disagreement rows still use numeric-disagreement floors.
- The source-bound router-refusal floor fields are projected into `candidate_decision_inputs` and `selector_reduce_risk_new_entry_authority`, so the fields have a producer, consumer, ledger/proof surface, and focused test.
- Fixture repairs added member-axis identity where tests claimed source-bound executable use; the source-bound admission gate remains strict.

Focused proof before replay:
- `python3 -m py_compile src/research/moonshot_scheduler_v4_best_trade_allocator.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `python3 -m py_compile src/research/moonshot_scheduler_v4_best_trade_allocator.py src/research_infra/v4_timewarp_simulated_live_research_loop.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py tests/test_v4_timewarp_simulated_live_research_loop.py research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `python3 -m pytest tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k 'source_bound_router_refusal_signing_uses_source_bound_floors_not_numeric_floors or source_bound_router_refusal_signed_authority_requires_execution_fillability_floor or source_bound_router_refusal_open_reduced_releases_zero_risk_with_authority_floors' -q --tb=short`
- `python3 -m pytest tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k 'source_bound_router_refusal or package_soft_authority_displacement_gate or soft_transfer_blocker_signed_package_candidate_stays_selectable or not_order_executable_candidate_is_not_selected' -q --tb=short`
- Result: compile passed; focused tests passed `3 passed` and expanded scheduler slice passed `28 passed`.

## Expected Measurable Effect

- Candidate -> scorecard: likely neutral on row count.
- Scorecard -> order: may increase if source-bound router-refusal rows no longer fail displacement quality from stale floor/hash mismatch.
- Order -> fill: may increase if newly admitted rows pass risk/order/lifecycle/fillability.
- Missed positive R: expected decrease in the `candidate_vetoed_package_displacement_quality_failed` bucket if the stale-floor mismatch was active.
- Missed negative R: may also decrease or increase in exposure because the bucket is mixed. Improvement is not accepted if it comes from suppressing opportunity.
- Trade count: may increase from V180's 6 trades.
- Net/gross/final R: direction unknown; a correctness repair may expose a loser.
- W/L/F: report added/removed rows by exact candidate instance.
- Cost-refused/source-gap execution: must remain 0 / 0.
- Risk distribution: any added source-bound router-refusal trade must carry signed authority and source-bound floor provenance.

## Success / Failure Criteria

Helped:
- Displacement-quality stale floor/hash mismatch shrinks, with added rows proving broker-cost passed, source-complete, member-axis bound source authority, and signed new-entry authority.
- `candidate_decision_inputs` on affected rows includes `source_bound_router_refusal_materialization_floors`.
- Cost-refused/source-gap/unresolved-fill-floor executions remain zero.

Failed:
- Displacement-quality bucket is unchanged and representative rows still fail stale numeric-disagreement floors.
- Added trades are caused by broad release of the 219 missing-authority bucket or by terminal hard-block bypass.

Exposed next blocker:
- Rows advance from displacement-quality to scheduler rank/reallocation, risk, order, lifecycle, fillability, or exit blockers. The next patch target is the largest exact downstream reason with cost/source/fillability safety preserved.

Not acceptable:
- Positive-by-suppression.
- Broad release of the mixed 219 missing-authority rows.
- Loosening broker-cost REFUSED/source-gap/unresolved-fill-floor/passive-limit-too-close terminal hard blocks.
