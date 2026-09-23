# Phase 3 Substrate Expansion And Shadow Timestamp Audit

**Date:** 2026-05-01
**Status:** research substrate expanded; shadow-only timestamp instrumentation added
**Scope:** no trade decision logic changed. The only live-path edit is additive shadow metadata for validation joins.

## What Changed

The MT5 research exporter now supports chunked `copy_rates_range` pulls via `--chunk-days`. Large M1/M5/M15 ranges can be exported in smaller windows, deduped by bar timestamp, filtered to the requested range, and audited for gaps. This directly fixes the `Invalid params` failure observed on oversized MT5 requests.

Live candidate feature logging now keeps two separate clocks:

- `timestamp_utc`: existing wall-clock evaluation timestamp.
- `candle_close_utc`: canonical latest-closed M15 candle close derived from MT5 candles.

The candidate join now prefers `candle_close_utc` when present and falls back to the historical `timestamp_utc` behavior for older rows. Trade records also receive `metadata.candle_close_utc` on future CANDIDATE records.

## Tests

Commands:

```powershell
python -m py_compile src/components/data_ingestion.py src/components/candidate_features_logger.py src/components/orchestrator.py scripts/build_external_feed_candidate_dataset.py scripts/export_mt5_research_ohlcv.py
python -m pytest tests/test_data_ingestion.py tests/test_candidate_features_logger.py tests/test_external_feeds.py -q -p no:cacheprovider --basetemp=C:\tmp\pytest_gtos_phase3_verify
```

Result: `72 passed`.

## MT5 Chunked Export

Command:

```powershell
python scripts/export_mt5_research_ohlcv.py --start 2022-01-01T00:00:00Z --end 2026-05-01T00:00:00Z --label phase3_m15_2022_2026_fn_chunked_v1 --timeframes M15 --chunk-days 90 --yes-live-readonly
```

The connected account was redacted_account live account `0` on `redacted_account-Server 2`. The command is read-only and sends no orders.

Ignored output root:

```text
data/mt5_research_exports/phase3_m15_2022_2026_fn_chunked_v1/
```

| Symbol file | MT5 symbol | Rows | First bar UTC | Last bar UTC |
|---|---|---:|---|---|
| XAGUSD | XAGUSD | 99,195 | 2022-01-03 01:00 | 2026-04-30 23:45 |
| XAUUSD | XAUUSD | 100,012 | 2022-02-01 21:30 | 2026-04-30 23:45 |
| GBPJPY | GBPJPY | 100,012 | 2022-04-14 11:15 | 2026-04-30 23:45 |
| GBPUSD | GBPUSD | 100,012 | 2022-04-14 19:00 | 2026-04-30 23:45 |
| USDJPY | USDJPY | 100,012 | 2022-04-14 19:00 | 2026-04-30 23:45 |
| NAS100 | NDX100 | 72,862 | 2022-10-20 11:00 | 2026-04-30 23:45 |
| US30_cash | US30 | 72,847 | 2022-10-20 11:00 | 2026-04-30 23:45 |

Interpretation: current redacted_account MT5 is enough for a materially stronger 2022-2026 M15 validation substrate. It still does not provide clean pre-2022 NAS100/US30 M15 history.

## Expanded Snapshot And Validation Artifacts

Commands:

```powershell
python scripts/build_external_feed_snapshots_historical.py --data-dir data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1 --start 2022-01-01T00:00:00Z --end 2026-05-01T00:00:00Z --write --label phase3_m15_2022_2026_external_v1
python scripts/build_external_feed_validation_dataset.py --data-dir data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1 --snapshot-label-contains phase3_m15_2022_2026_external_v1 --label phase3_m15_2022_2026_calendar_macro_validation_v1 --bundle-id calendar_macro_bundle_v1 --write
```

Ignored outputs:

```text
data/external/features/{SYMBOL}/phase3_m15_2022_2026_external_v1_20260501T013833Z.jsonl
data/external/validation/calendar_macro_bundle_v1/phase3_m15_2022_2026_calendar_macro_validation_v1_summary_20260501T014025Z.json
data/external/validation/calendar_macro_bundle_v1/phase3_m15_2022_2026_calendar_macro_validation_v1_{SYMBOL}_20260501T014025Z.jsonl
```

Total validation rows: **644,952**.

| Symbol | Rows | First close UTC | Last close UTC | Months | ISO weeks |
|---|---:|---|---|---:|---:|
| XAGUSD | 99,195 | 2022-01-03 01:15 | 2026-05-01 00:00 | 53 | 226 |
| XAUUSD | 100,012 | 2022-02-01 21:45 | 2026-05-01 00:00 | 52 | 222 |
| GBPJPY | 100,012 | 2022-04-14 11:30 | 2026-05-01 00:00 | 50 | 212 |
| GBPUSD | 100,012 | 2022-04-14 19:15 | 2026-05-01 00:00 | 50 | 212 |
| USDJPY | 100,012 | 2022-04-14 19:15 | 2026-05-01 00:00 | 50 | 212 |
| NAS100 | 72,862 | 2022-10-20 11:15 | 2026-05-01 00:00 | 44 | 185 |
| US30_cash | 72,847 | 2022-10-20 11:15 | 2026-05-01 00:00 | 44 | 185 |

Label coverage is complete except for the expected tail rows at each horizon: 1, 4, 12, and 96 bars.

## Source Availability

FRED macro is available for almost the full expanded substrate. LBMA calendar is available for XAUUSD/XAGUSD. CFTC is currently mapped only to XAUUSD gold COT and covers 87,929 XAUUSD rows. FlashAlpha remains forward-only. WGC appears in exactly one XAUUSD row because the imported WGC files were cached at `2026-04-30T23:49:45Z`, before the final `2026-05-01T00:00:00Z` candle close. This is point-in-time correct, not historical backfill.

## Candidate Join After Expansion

Scope note: this join is recent live/shadow candidate coverage only. It does not mean GTOS produced only 76 candidates from 2022-2026. The 2022-2026 artifact is an all-candle external-feed substrate; a separate historical candidate/opportunity generation pass is still required to create a high-N candidate-level population.

Command:

```powershell
python scripts/build_external_feed_candidate_dataset.py --validation-label-contains phase3_m15_2022_2026_calendar_macro_validation_v1 --validation-label-contains phase3_m15_candidate_gap_validation_v1 --label phase3_candidate_calendar_macro_join_2022_2026_plus_gap_v2 --simulate-opportunity --ohlcv-dir data\mt5_research_exports\phase3_m15_2022_2026_fn_chunked_v1 --ohlcv-dir data\mt5_research_exports\phase3_candidate_gap_20260501 --ohlcv-dir data\historical_2026 --write
```

Summary:

- Candidate rows read: 424
- CANDIDATE rows kept: 76
- External validation matched: 70
- Old off-boundary rows quarantined: 6
- Trade records matched: 70
- Actual realized-R rows: 2
- Synthetic opportunity R rows: 29

The new shadow `candle_close_utc` field fixes future off-boundary rows but does not rewrite old logs. The six old rows remain quarantined because assigning them to a candle now would be a guess.

The first candidate join undercounted actual outcomes because live exit records use the historical `realized_R` key while the join initially read only lowercase `realized_r`. The extractor now accepts both spellings from `decision_pipeline.outcome`, top-level record fields, `exit`, and `execution`.

## Diagnostic Verdict

Generated:

```text
research/phase_3_external_feed_validation/CANDIDATE_DIAGNOSTIC_2022_2026_PLUS_GAP_2026-05-01.md
```

Verdict remains `SUPPRESSED_DIAGNOSTIC_ONLY`:

- target rows below 30
- DSR/PBO/effective_N not computed
- bundle-level trial budget protected

Useful but non-actionable lead: `fred__VIXCLS__value` remains the strongest current diagnostic screen, with higher VIX associated with worse synthetic candidate R in this tiny sample. This is not an alpha claim.

## Remaining Data Needs

1. Actual realized-R enrichment from execution/exit records. Only 2 current joined rows carry realized-R after accepting both `realized_R` and `realized_r`; most rejected or pending-limit outcomes still need synthetic/no-entry target handling or forward accumulation.
2. Historical candidate/opportunity generation over the 2022-2026 candle substrate. The current candidate join uses only live/shadow rows from April-May 2026.
3. Forward accumulation under the new `candle_close_utc` field.
4. CFTC mappings beyond XAUUSD only where futures proxies are defensible.
5. FlashAlpha forward collection after the May 1 quota reset; historical GEX still needs a separate legal source.
6. Optional broker/source robustness check for pre-2022 NAS100/US30, because redacted_account starts indices in October 2022.
