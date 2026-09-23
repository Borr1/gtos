# Saturation Self Redteam Pass

**Generated UTC:** 2026-05-10T15:46:07+00:00
**Route:** `NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE`
**Evidence class:** `NO_API_MECHANICAL_PRE_AI_REPLAY_DISCOVERY_ONLY`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**validation_safe:** `False`
**outcome_review_opened:** `False`
**live_effect:** `False`

| artifact_family | selected_source_count | excluded_source_slice_count | opened_family_count |
| --- | --- | --- | --- |
| saturation_self_redteam_pass | 365 | 3135 | 11 |

## Anti-Boxing Checks

| axis | status | evidence |
| --- | --- | --- |
| family | PASS | core Model A families, lifecycle, KZ sweeps, liquidity, baselines, and adjacent compression family opened |
| timeframe | PASS | M1/M5/M15/H1/H4 selected where OHLC source rows exist |
| symbol | PASS | selected source ledger records all symbols available after source-hash dedupe |
| source_type | PASS | LOCAL_OHLCV_CSV and SIERRA_DERIVED_OHLCV_EXPORT opened; native depth/tick source slices terminally routed |
| large_file_hashing | PASS | selected deferred OHLC files hashed in this route |
| evidence_class | PASS | projection-only and discovery-only labels preserved; validation and result scoring closed |
