# V121S Pre-Replay Brief

## Current Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V121R_STOP_HAZARD_CAP_TRANSFER_QUALITY_REPAIR_20260514_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`
- Window: `2026-05-14..2026-05-14`
- Trades: 24
- Net/gross/final R: `+0.29253564 / +2.11053495 / +2.11053495`
- Cash PnL / risk cash / risk pct: `+24.60851082 / 2406.04506533 / 2.4`
- W/L/F: `9 / 15 / 0`
- Scorecard/order/trade/missed rows: `96 / 51 / 24 / 7942`
- Interpretation: bounded hostile one-day repair proof only; not total reservoir conversion proof.

## Active Process State

No broad replay, verifier, analyzer, pytest, or Python repair process was active before this patch batch.

## Baseline Comparison

- V121R vs V121Q one-day same-window: net R delta `+2.02477337`, trade delta `0`, added trades `3` net `+2.32967074`, removed trades `3` net `+0.30489737`.
- V89D/V90/V92 remain historical full/broad comparators; do not compare this one-day smoke directly to global reservoir claims.

## Dirty Code Batch

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `src/components/broader_origin_generators.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- Focused tests under `tests/`.

## Incorporated Subagent Findings

- Goodall: stop-hazard cap escaped runtime risk. Incorporated in V121R.
- Nash: scheduler transfer ranking needed cap-aware quality. Incorporated in V121R.
- Meitner: stop-hazard cap must be verifier-fatal and full-tagged. Incorporated in V121R.
- Schrodinger: immediate-route final blockers and missed false materialization were verifier precision issues. Incorporated in V121S.
- Erdos: missed counterfactual fills were not real materialization; cross-asset stop-hazard `unit_risk_atr` missing was a producer source-field gap. Incorporated in V121S.
- James: signed-authority alias status and scorecard selected-scheduler authority projection were contract mismatches; non-executable missed reduce-risk probes should be diagnostic. Incorporated in V121S.

## Mismatch Classes Patched

- Source-bound -> candidate: cross-asset lead-lag now persists `atr14`, `lag_atr14`, and `leader_atr14` into `source_fields`.
- Candidate -> selector/scheduler: signed authority quality alias normalization now stamps `exact_materialized` when required predecision fields are complete and clean.
- Scheduler -> risk/order: scorecard verifier reads selected scheduler authority surfaces instead of requiring only top-level scorecard authority.
- Order/lifecycle/fill -> missed ledger: missed rows now keep real `fill_status=not_sent_missed_opportunity` and preserve counterfactual fills in explicit counterfactual fields.
- Verifier: immediate-market final blocks accept sourced downstream blockers; non-executable missed diagnostics no longer count as risk-bearing authority leaks.

## Patch Types

- Correctness: signed authority payload truth, missed status semantics, cross-asset ATR source projection.
- Verifier precision: scorecard selected-scheduler authority, sourced final blockers, non-executable diagnostic probes.
- Diagnostic/ledger: preserve counterfactual fill details without materialization claims.

## Expected Measurable Effect

- Candidate -> scorecard/order -> fill axes: should not be optimized by this batch; any change is a side effect of regenerated provenance.
- Missed positive/negative R: preserved, but missed counterfactual fills should not look like real materialized fills.
- Cost-refused/source-gap execution: must remain zero.
- Full-risk/reduced-risk distribution: not targeted by this batch.
- Emitted authority failures: stale V121R alias failures should clear on regenerated V121S rows unless a real unsigned row is exposed.
- Order-transfer bad counts: should remain zero.
- Stop-hazard candidate-index `unit_risk_atr` missing: stale V121R count 17 should clear or materially reduce on regenerated V121S.

## Replay Success Criteria

V121S helps if verifier scans show no regression in order-transfer truth, missed false materialization remains zero, signed-authority alias bad counts clear on regenerated rows, and cross-asset stop-hazard `unit_risk_atr` gaps clear or are reduced to exact non-reconstructable rows.

V121S fails if regenerated rows still hash signed authority with bare `materialized`, missed rows still use counterfactual fills as real fills, or cross-asset rows still omit ATR despite source generation.

If behavior R worsens, keep the truth repair and inspect the newly exposed flow bucket; do not revert a correctness repair solely for headline R.
