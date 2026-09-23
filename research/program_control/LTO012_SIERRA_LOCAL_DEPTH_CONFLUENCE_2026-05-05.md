# LTO012 Sierra Local Depth Confluence - 2026-05-05

**Status:** `OK_WITH_FILE_SIZE_GUARDED_BACKGROUND_QUEUE`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Depth feature version:** `sierra_depth_predecision_eob_top10_v2`

## Summary

Sierra live depth confluence is covered by source/status rows and an out-of-band feature lane. Large depth files are now kept in a guarded background queue instead of blocking live candidate capture.

## Counts

| Metric | Value |
| --- | --- |
| latest_candidate_rows | 538 |
| latest_source_status_rows | 404 |
| latest_feature_rows | 538 |
| missing_feature_rows | 0 |
| features_extracted | 52 |
| background_queue_candidates | 212 |
| file_size_guard_candidates | 11 |
| pending_heavy_scan_candidates | 201 |
| no_registered_proxy_candidates | 271 |
| checkpoint_candidates | 526 |
| max_depth_file_size_bytes_seen | 724675816 |

## Feature Status Counts

| Status | Count |
| --- | --- |
| FEATURES_ATTEMPTED_NO_SAMPLES | 3 |
| FEATURES_EXTRACTED | 52 |
| FEATURE_EXTRACTION_DEFERRED_FILE_SIZE_GUARD | 11 |
| FEATURE_EXTRACTION_PENDING_HEAVY_DEPTH_SCAN | 201 |
| NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL | 271 |

## Symbol Feature Status Counts

| Symbol:status | Count |
| --- | --- |
| AUDJPY:NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL | 8 |
| BTCUSD:NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL | 24 |
| CHFJPY:NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL | 21 |
| ETHUSD:NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL | 23 |
| EURGBP:NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL | 27 |
| EURJPY:NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL | 19 |
| GBPJPY:NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL | 50 |
| GBPUSD:FEATURES_EXTRACTED | 2 |
| GBPUSD:FEATURE_EXTRACTION_PENDING_HEAVY_DEPTH_SCAN | 55 |
| JP225:NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL | 20 |
| NAS100:FEATURES_ATTEMPTED_NO_SAMPLES | 1 |
| NAS100:FEATURES_EXTRACTED | 7 |
| NAS100:FEATURE_EXTRACTION_DEFERRED_FILE_SIZE_GUARD | 11 |
| NAS100:FEATURE_EXTRACTION_PENDING_HEAVY_DEPTH_SCAN | 57 |
| NZDUSD:NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL | 3 |
| UK100:NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL | 1 |
| UKOIL_cash:NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL | 26 |
| US30_cash:FEATURE_EXTRACTION_PENDING_HEAVY_DEPTH_SCAN | 40 |
| USDCAD:NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL | 25 |
| USDJPY:FEATURES_EXTRACTED | 1 |
| USDJPY:FEATURE_EXTRACTION_PENDING_HEAVY_DEPTH_SCAN | 3 |
| USOIL_cash:NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL | 24 |
| XAGUSD:FEATURES_EXTRACTED | 36 |
| XAGUSD:FEATURE_EXTRACTION_PENDING_HEAVY_DEPTH_SCAN | 24 |
| XAUUSD:FEATURES_ATTEMPTED_NO_SAMPLES | 2 |
| XAUUSD:FEATURES_EXTRACTED | 6 |
| XAUUSD:FEATURE_EXTRACTION_PENDING_HEAVY_DEPTH_SCAN | 22 |

## Background Queue Policy

| Field | Value |
| --- | --- |
| live_candidate_capture | source_path_mtime_size_first |
| feature_extraction | out_of_band_background_queue |
| throttle | supported_by_max_per_symbol_and_limit |
| checkpoint | pipeline_state\sierra_depth_enrichment_checkpoint.json |
| file_size_guard | supported_by_max_file_size_mb |
| no_leak_window | pre60_and_event15_end_at_decision_time |

## Boundary

Sierra depth rows are shadow confluence only. They are not live filters, risk modifiers, entry rules, or promotion evidence.

## Next Action

Run the guarded enrichment command during monitoring; raise --max-file-size-mb only in a dedicated backfill window when the expected runtime is acceptable.

## Non-Claims

- This audit made zero Sierra depth scans.
- This audit made zero AI, canary, MT5 order, execution, or paid data calls.
- This does not create a live filter, signal, entry rule, risk modifier, or promotion dossier.
