# V207 B7 Default Confidence Provenance Pre-Replay Brief

Generated: 2026-07-09T01:37:52Z

## Current Completed Prefix

- Latest completed proof slice: `BROAD_LIVE_AS_IF_REPLAY_V206_B7_STOP_PRESSURE_QUALITY_REPAIR_20260513_REPAIRED_ONLY_COMPACT_FULLGRID`
- Window: 2026-05-13 only, repaired profile only, compact fullgrid
- Trades: 2
- Net/gross/final R: `+0.52110312 / +0.65111456 / +0.65111456`
- Cash PnL: `+130.31196876`
- W/L/F: `2/0/0`
- Orders: 6 summary rows, 9 order-ledger lifecycle rows
- Candidate -> scorecard/order -> fill axes: `853/1101` candidate-generated axes, 5 scorecard/order-present count, 2 filled axes
- Same-window package source-bound R: `149486.17602471`
- Full-reservoir transfer claim allowed: false

## Verifier Failure Being Repaired

Pinned V206 verifier result: `VERIFICATION_RESULT.json`, `ok=false`, issue count 4.

Resolved by code/config batch:

- `broad_quality_parity_order_trade_cost_authority_weak` was caused by hidden default-confidence provenance on order/trade rows, not missing broker-calibrated cost. Rows already carried `pretrade_cost_packet_status=PASSED`, `cost_authority=broker_calibrated_replay_cost`, and `cost_source_gap_status=source_bound_cost_authority_present`.
- The root bug was producer-side: candidate/scheduler quality surfaces could flatten `confidence=0.55` as `candidate.candidate_confidence` while nested package authority exposed `scheduler_default_missing_confidence_0_55`.
- `candidate_decision_quality_fields`, `scheduler_option_quality_backfill_fields`, the canonical quality envelope, and candidate generation whitelist now preserve `confidence_missing_degraded_default_applied` and the default-confidence provenance warning when any source map identifies scheduler-default confidence.

Still expected before verifier green:

- Route manifest/current selected broad-quality prefix must be refreshed from V204 to the new V207 artifact set after V207 flow/parity artifacts are materialized.

## Expected Replay Effect

This patch is a correctness/provenance repair. It should be behavior-neutral:

- Candidate -> scorecard transfer: unchanged.
- Scorecard -> order transfer: unchanged.
- Order -> fill transfer: unchanged.
- Trade count: expected unchanged from V206 unless deterministic ordering changes unexpectedly.
- Net/gross/final R and W/L/F: expected unchanged from V206.
- Cost-refused/source-gap execution: expected zero.
- Risk distribution: expected unchanged.
- Verifier effect: order/trade default-confidence provenance issues should go to zero on regenerated ledgers.

## Success/Failure Criteria

Helped:

- V207 rerun reproduces V206 behavior within deterministic replay tolerance.
- V207 order/trade rows carry visible degraded-default confidence flags wherever nested quality sources use `scheduler_default_missing_confidence_0_55`.
- V207 flow/parity artifacts materialize.
- Verifier no longer reports `candidate_decision_quality:default_confidence_*` for order/trade rows.

Failed:

- Replay behavior changes materially without a deterministic code-path reason.
- Default-confidence source remains hidden in regenerated order/trade rows.
- Verifier still reports the same order/trade weak authority reasons after V207 artifacts and manifest refresh.

Exposes Next Flaw:

- If V207 verifier passes provenance but remains blocked by manifest selection only, refresh route manifest through the route builder/pinned-prefix path.
- If V207 behavior is still positive only because opportunity was suppressed, broaden to the 2026-05-13..2026-05-17 hostile bucket under the same code after verifier/artifact proof is green.
