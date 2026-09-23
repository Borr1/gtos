# Candidate Promotion Plumbing Summary

Date: 2026-06-18

Decision: `INSTALL_DEFAULT_OFF_RUNTIME_EXECUTABLE_NATIVE_EXIT_CANDIDATE_BOOK_PLUMBING`.

This route converts the candidate-book research catalog into production-owned, default-off runtime plumbing without
changing active live behavior. The active config keeps `ultimate_book_include_candidate_book: false`; the current live
book remains core-8 plus the A8 metals confluence gate.

## Runtime-Executable Now

The v2 promotion lane covers every positive-confidence candidate whose native exit is represented exactly by the
current V4 execution contract:

- fixed-target plus time-stop with broker TP;
- capless trailing-runner with no broker TP;
- targetless hold-to-close/time-stop with no broker TP.

Runtime-executable candidates:

- `vol_compression` at confidence `0.40`, fixed `3R`, D1-horizon time stop.
- `asian_fade` at confidence `0.40`, capless trailing-runner, trigger `0.5R`, gap `0.5R`, `48`-bar time stop, no broker TP.
- `ny_crypto_momentum` at confidence `0.35`, targetless no-TP time stop, `20` bars.
- `metal_session_reversion` at confidence `0.40`, capless trailing-runner, trigger `0.6R`, gap `0.5R`, `24`-bar time stop, no broker TP.
- `asia_pdl_fade` at confidence `0.25`, fixed `3R`, `32`-bar time stop.
- `orb_crypto_london` at confidence `0.35`, fixed `2R`, `80`-bar time stop.
- `liq_asia_up_low_metal` at confidence `0.25`, fixed `3R`, `16`-bar time stop.
- `kz_london_crypto_low` at confidence `0.10`, targetless no-TP time stop, `32` bars.
- `vss_fxcross_london_up_low` at confidence `0.12`, fixed `2R`, `48`-bar time stop.

These candidates now have:

- candidate generation specs in `src/components/ultimate_book/sleeves/registry.py`
- default-off admission through `include_candidate_book`
- bridge/config keys `ultimate_book_include_candidate_book` and `ultimate_book_candidate_book_profile`
- per-candidate native exit profiles in `execution_packets.py`
- targetless geometry support in `dynamic_target_stop_geometry_v4.py`
- no-broker-TP open, persist, fill, and recovery fields in `execution.py`
- focused regression tests proving default-off behavior, admission gating, broker TP/no-TP geometry, and targetless trade-state shape

## Preserved Work Items

No positive-confidence candidate remains blocked by native-exit semantics. Zero-confidence candidates remain
quarantined inventory: `vol_squeeze`, `ny_index_momentum`, and `structural_retest`.

## Next Build Lanes

- Rerun unified MC/replay on the actual core8 + A8 active profile before any candidate-book live activation.
- Prove broker-profile aliases and MT5 history availability for candidate-only symbols such as `DASHUSD`,
  `LTCUSD`, `NATGAS_cash`, `XPDUSD`, `XPTUSD`, `XRPUSD`, and `XTZUSD`, plus the reintroduced FX candidate
  symbols used by `asian_fade` and `asia_pdl_fade`.
- Seal May 2026 rolling/stress replay artifacts into tracked manifests.
- Package foundation vol/distribution/MoE as shadow-only, shrink-first intelligence before any model-driven runtime
  effect.

This route used no orderflow/depth data and made no broker, VPS, MT5 bridge, credential, or live-order mutation.
