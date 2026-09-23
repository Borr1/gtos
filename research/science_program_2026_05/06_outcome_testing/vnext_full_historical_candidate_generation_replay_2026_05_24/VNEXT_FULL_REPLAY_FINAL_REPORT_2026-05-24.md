# vNext Full Historical Replay Final Report

Route: `vnext_full_historical_candidate_generation_replay_2026_05_24`
Status: `COMPLETE_REPLAY_OUTPUTS_VERIFIED_AND_TERMINAL_PACKAGED`

## Replay Spine

- Stage01 source universe: 903,163 M15 denominator rows across 45 source shards.
- Stage02 candidate origin: 253,234 market-bar candidates, 903,163 denominator dispositions, and 903,163 market-state packets.
- Stage03 runtime trace: 506,468 current-shadow and hypothetical-activated vNext trace rows.
- Stage04 path truth: 1,978,947 path/R rows across M15, M1, M5, tick/Sierra, missing-source, and OHLC proxy modes.
- Stage05 dominance/MIXED: 1,278,432 dominance/pollution rows and 1,018 MIXED-resolution rows.
- Stage06 terminal metrics: ablation, robustness, prop proxy metrics, behavioral forensics, and final decision map.

## Stage02 Steer

The durability/lookback/scope-control steer is recorded as applied once. Stage02 remains candidate-origin generation only; lower-timeframe/path/R and final replay coverage are measured in later stages.

## Final Decisions

- `KEEP_SHADOW`: 5443
- `KEEP_SHADOW_OR_GUARD_ONLY`: 272
- `KILL_OR_REDESIGN_BEFORE_USE`: 858
- `PROMOTE_TO_PRODUCTION_CHANGE_DOSSIER`: 982

## Boundary

This package does not change live trading behavior. Owner review or a separate production-change dossier is required before any live prompt/config/risk/execution/safety/canary/selector change.

## Verification

- Stage02 verifier: `ok`
- Stage03 verifier: `ok`
- Stage04 verifier: `ok`
- Stage05 verifier: `OK`
- Stage06 verifier: `OK`
- Independent review: `OK`
- Generic route artifact audit: expected pass after final terminal packaging.
