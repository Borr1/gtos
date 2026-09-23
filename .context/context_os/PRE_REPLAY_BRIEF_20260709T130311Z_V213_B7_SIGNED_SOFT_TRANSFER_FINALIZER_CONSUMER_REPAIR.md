# Pre-Replay Brief - V213 B7 Signed Soft-Transfer Finalizer Consumer Repair

Generated UTC: 2026-07-09T13:03:11Z.

## Control Surface

- Fable batch: B7 full proof ladder, transfer/composition repair after V211/V212.
- Broker/live/final boundary: broker mutation disabled, live broker authority false, final selection false.
- Replay authority: local replay/package authority full.
- Scope: targeted proof slice only, not a full reservoir transfer claim.

## Latest Completed Runs

### V211 hostile five-day baseline

Prefix:
`BROAD_LIVE_AS_IF_REPLAY_V211_B7_2_HOSTILE_5D_VALUE_TRANSFER_POST_B1_B5_PROOF_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`

- Scope: 2026-05-13..2026-05-17, 24-symbol fullgrid, repaired profile.
- Candidate/decision/scorecard/order/trade/missed rows: 25006 / 11424 / 288 / 50 / 18 / 24979.
- W/L/F: 11 / 7 / 0.
- Net/gross/final R: -3.47466796 / -1.91290882 / -1.91290882.
- Cash PnL: -868.32556257.
- Risk cash / risk pct sum / avg risk pct: 4503.6890717 / 4.5 / 0.25.
- Expected cost R: 1.56175914.
- Executed REFUSED/source-gap rows: 0 / 0.
- Dominant leak class: selected-composition transfer collapse, especially candidate-generated-not-scheduler-selected and reduce-risk-not-scheduler-selected buckets.

### V212 targeted proof failure

Prefix:
`BROAD_LIVE_AS_IF_REPLAY_V212_B7_TRANSFER_COMPOSITION_TARGETED_SOFT_TRANSFER_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

- Scope: 2026-05-13..2026-05-14, XAUUSD/USDCAD/USDJPY, repaired profile, bounded smoke.
- Candidate/decision/scorecard/order/trade/missed rows: 1651 / 4608 / 192 / 8 / 3 / 1647.
- W/L/F: 3 / 0 / 0.
- Net/gross/final R: +1.10761535 / +1.35101129 / +1.35101129.
- Cash PnL: +277.0648589.
- Risk cash / risk pct sum: 750.86709783 / 0.75.
- Expected cost R: 0.24339594.
- Executed REFUSED/source-gap rows: 0 / 0.
- Target exact transfer: 2/3 candidate, 2/3 scorecard, 2/3 missed, 0/3 order/trade.
- Failure interpretation: V212 did not prove target transfer; cost-passed/source-complete/fillable signed candidates remained final-blocked by downstream finalizer/selected-policy transfer logic.

## Current Patch Batch

Same-root repair: signed soft-transfer finalizer proof must travel from producer to all downstream consumers before another replay.

Files changed:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_denominator_to_deployment_verifier.py`
- `tests/test_broad_replay_repair_config.py`

Patch type:

- Correctness repair: signed soft-transfer finalizer proof now has producer, consumer, ledger/proof surface, verifier, and focused tests.
- Behavior repair: signed, cost-passed, source-complete, fillable soft-transfer candidates can displace stale originals without stale reallocation-score blocking.
- Diagnostic/ledger repair: scorecard, missed, compact candidate, selected-package bridge, order, trade, and broad transfer verifier surfaces preserve/prove the same signed-transfer fields.

Focused proof already run:

- `python3 -m py_compile` on timewarp, broad harness, selected-package bridge, and verifier.
- Focused pytest: 9 passed, 1 unrelated pytest config warning.

## Subagent Disposition

- Hume: incorporated. Added missing probe fields, order/trade risk-authority propagation, compact finalizer preservation, selected-package bridge compact preservation, and verifier selected-probe visibility.
- Boole: incorporated. Added central verifier reliance predicate, replay bridge scorecard/probe checks, selected order/trade checks, broad order-executable transfer checks, and focused tests.

## Expected V213 Effects

- Candidate -> scorecard transfer: unchanged except proof fields should persist.
- Scorecard -> order transfer: target signed soft-transfer rows should no longer be blocked by stale finalizer transfer/selected-policy quality proof if all causal conditions hold.
- Order -> fill transfer: must preserve broker-cost PASSED only; executed REFUSED/source-gap must remain 0/0.
- Missed positive/negative R: rows that remain missed must have exact signed-transfer proof or exact blocker reason.
- Trade count/net R: target proof may increase order/trade count if transfer repair works; positivity is not required for this smoke.
- Full/reduced risk: risk provenance must remain visible in scorecard/order/trade/missed.

## V213 Success / Failure Criteria

Run V213 only as a targeted proof slice:

`BROAD_LIVE_AS_IF_REPLAY_V213_B7_SIGNED_SOFT_TRANSFER_FINALIZER_CONSUMER_REPAIR_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

Success:

- No broker/live/final authority opens.
- No executed REFUSED/source-gap rows.
- Signed soft-transfer proof fields appear in scorecard/missed and, when selected, order/trade.
- The V212 target exact keys improve from 0/3 order/trade or expose the next blocker with exact causal reason.
- Route verifier does not flag signed soft-transfer proof leaks.

Failure:

- Signed rows still final-blocked without a concrete downstream blocker.
- Proof fields disappear from compact ledgers or selected-package bridge surfaces.
- Any signed-transfer reliance has bad boundary, outcome usage, cost-source gap, fallback cost authority, or missing order-executable/package-executable proof.
- Improvement comes only from suppressing opportunity rather than transfer/composition repair.

Broker/live/final remain closed regardless of V213 result.
