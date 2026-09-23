# Phase 3 First Validation Dataset

**Date:** 2026-05-01
**Status:** substrate artifact built; no alpha claim yet
**Scope:** `calendar_macro_bundle_v1`, shadow-only. No live trading logic, prompt, orchestrator, or production config change.

## What Changed

Implemented `scripts/build_external_feed_validation_dataset.py`, which turns as-of external-feed snapshots into validation rows with:

- strict future-only OHLCV labels at 1, 4, 12, and 96 M15 bars
- fold metadata: month, quarter, ISO week
- source availability counts
- source timestamp no-lookahead validation for `published_at`, `as_of`, and past-fix fields
- ignored JSONL/summary outputs under `data/external/validation/`

Also fixed a snapshot-quality gap: LBMA fix timing is deterministic and known before the event, but the prior join only exposed past fixes. Historical snapshots now expose previous-fix and next-fix timing fields while keeping price-like `fix_time_utc` fields tied to past fixes only.

## Commands Run

```powershell
python -m pytest tests/test_external_feeds.py -q -p no:cacheprovider
python scripts/build_external_feed_snapshots_historical.py --write --label phase3_m15_2025_2026_external_v5
python scripts/build_external_feed_validation_dataset.py --write --snapshot-label-contains phase3_m15_2025_2026_external_v5 --label phase3_m15_calendar_macro_validation_v3 --bundle-id calendar_macro_bundle_v1
```

Test result: `30 passed`.

## Generated Artifacts

Feature snapshots:

```text
data/external/features/GBPJPY/phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl
data/external/features/GBPUSD/phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl
data/external/features/NAS100/phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl
data/external/features/US30_CASH/phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl
data/external/features/USDJPY/phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl
data/external/features/XAGUSD/phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl
data/external/features/XAUUSD/phase3_m15_2025_2026_external_v5_20260501T004212Z.jsonl
```

Validation rows:

```text
data/external/validation/calendar_macro_bundle_v1/phase3_m15_calendar_macro_validation_v3_summary_20260501T004230Z.json
data/external/validation/calendar_macro_bundle_v1/phase3_m15_calendar_macro_validation_v3_{SYMBOL}_20260501T004230Z.jsonl
```

These files are intentionally gitignored. The committed artifact is this report plus the code/tests that regenerate them.

## Coverage

| Symbol | Rows | First close UTC | Last close UTC | Months | ISO weeks |
|---|---:|---|---|---:|---:|
| GBPJPY | 14,009 | 2025-10-01 00:15 | 2026-04-25 00:00 | 7 | 30 |
| GBPUSD | 14,013 | 2025-10-01 00:15 | 2026-04-25 00:00 | 7 | 30 |
| NAS100 | 13,284 | 2025-10-01 01:15 | 2026-04-25 00:00 | 7 | 30 |
| US30_cash | 13,279 | 2025-10-01 01:15 | 2026-04-25 00:00 | 7 | 30 |
| USDJPY | 14,013 | 2025-10-01 00:15 | 2026-04-25 00:00 | 7 | 30 |
| XAGUSD | 13,282 | 2025-10-01 01:15 | 2026-04-25 00:00 | 7 | 30 |
| XAUUSD | 13,288 | 2025-10-01 01:15 | 2026-04-25 00:00 | 7 | 30 |

Total rows: **95,168**.

Label coverage:

| Horizon | Available rows | Missing rows | Missing reason |
|---:|---:|---:|---|
| 1 bar | 95,161 | 7 | final candle per symbol has no future bar |
| 4 bars | 95,140 | 28 | tail horizon |
| 12 bars | 95,084 | 84 | tail horizon |
| 96 bars | 94,496 | 672 | tail horizon |

## Source Availability

Ready now:

- FRED macro series are available for all 95,168 rows.
- LBMA schedule features are available for all XAUUSD and XAGUSD rows after the deterministic calendar fix.
- CFTC disaggregated gold COT is available for all XAUUSD rows.

Not ready for historical promotion:

- WGC ETF/GDT fields are 0 across this historical window because current workbooks were imported after the candles. This is correct point-in-time behavior.
- FlashAlpha GEX is 0 across this historical window because Basic has no historical GEX backfill. This is correct.
- CFTC mappings are not yet available for XAGUSD, USDJPY, GBPJPY, GBPUSD, NAS100, or US30 in this validation artifact.

## No-Lookahead Notes

- External source timestamps ending in `published_at_utc`, `as_of_utc`, or past `fix_time_utc` are rejected if they are after the candle close.
- OHLCV labels use only bars strictly after the snapshot candle. Current-candle high/low cannot enter MFE/MAE-style labels.
- LBMA `next_fix_time_utc` is allowed as deterministic schedule context, not as a benchmark price or future market value.

## What This Does Not Prove

This is not a DSR/PBO alpha result. It is a high-quality validation substrate.

The registered primary target remains `candidate_realized_r`. This artifact provides forward OHLCV labels for all M15 candles, which is useful for substrate QA, calendar/regime diagnostics, and pre-model feature engineering. The next validation step must join these snapshots to the canonical GTOS candidate/opportunity population and realized candidate outcomes before making any promotion claim.

## Next Actions

1. Build the candidate/opportunity join layer: trade/candidate rows -> nearest snapshot by symbol and candle close.
2. Add CFTC contract mappings for XAGUSD and defensible FX/index futures where source mapping is clean.
3. Run the first CPCV/PBO-ready baseline-vs-external evaluation only after the candidate join is complete.
4. Keep FlashAlpha and WGC as forward/PIT-only until enough collected rows exist or archived point-in-time files are obtained.
