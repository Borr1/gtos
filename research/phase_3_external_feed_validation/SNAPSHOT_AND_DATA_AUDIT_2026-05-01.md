# Phase 3 Snapshot And Market-Data Audit

**Date:** 2026-05-01
**Status:** implementation + data-readiness audit
**Scope:** external-feed validation snapshots and market-data substrate. No live trading logic changed.

> Continuation note: the initial v3 five-symbol snapshot described below was
> superseded by the v5/v3 validation substrate in
> `FIRST_VALIDATION_DATASET_2026-05-01.md`. The continuation added USDJPY and
> GBPJPY, fixed deterministic LBMA next-fix timing, and generated 95,168
> no-lookahead validation rows across seven symbols.

## Executive Verdict

We have enough data to start validating `calendar_macro_bundle_v1` on the existing 2025-10 to 2026-04 M15 historical window for metals/cable/index proxies where labels already exist or can be generated.

We do **not** yet have enough data for a proper historical `nas_us30_gamma_regime_v1` verdict. FlashAlpha Basic is usable for forward shadow collection, but the current feed is point-in-time single-expiry snapshots only; it does not backfill historical GEX. Any historical GEX claim would need a separate options-history source or a paid/licensed source.

We also do **not** yet have point-in-time WGC history. The imported WGC workbooks are useful context archives, but historical rows in a current workbook are not the same as files known at each historical candle. For quality, WGC stays unavailable before import unless we obtain archived monthly/quarterly releases with publication dates.

## Snapshot Artifact Built

Generated ignored research artifacts:

```text
data/external/features/XAUUSD/phase3_m15_2025_2026_external_v3_20260501T000956Z.jsonl
data/external/features/XAGUSD/phase3_m15_2025_2026_external_v3_20260501T000956Z.jsonl
data/external/features/NAS100/phase3_m15_2025_2026_external_v3_20260501T000956Z.jsonl
data/external/features/US30_CASH/phase3_m15_2025_2026_external_v3_20260501T000956Z.jsonl
data/external/features/GBPUSD/phase3_m15_2025_2026_external_v3_20260501T000956Z.jsonl
```

Counts:

| Symbol file | Snapshots | First close UTC | Last close UTC |
|---|---:|---|---|
| XAUUSD | 13,288 | 2025-10-01 01:15 | 2026-04-25 00:00 |
| XAGUSD | 13,282 | 2025-10-01 01:15 | 2026-04-25 00:00 |
| NAS100 | 13,284 | 2025-10-01 01:15 | 2026-04-25 00:00 |
| US30_cash | 13,279 | 2025-10-01 01:15 | 2026-04-25 00:00 |
| GBPUSD | 14,013 | 2025-10-01 00:15 | 2026-04-25 00:00 |

XAUUSD availability check:

| Source family | Available candles | Notes |
|---|---:|---|
| FRED | 13,288 / 13,288 | Conservative publication model: observation date + 1 UTC day. |
| CFTC COT | 13,288 / 13,288 | Official 3:30pm ET release model; 2025 shutdown catch-up schedule encoded. |
| LBMA calendar | 13,255 / 13,288 | Deterministic fix calendar; holiday/weekend gaps remain unavailable. |
| WGC | 0 / 13,288 | Correctly unavailable before current workbook import. Needs PIT archive for historical use. |
| FlashAlpha GEX | 0 / 13,288 | Correctly unavailable before first collected snapshot. Needs forward collection or historical options source. |

## Implementation Notes

The first full build timed out because the naive join tried to project every WGC GDT category into every M15 candle. That was rejected as a quality and methodology problem, not just a performance problem.

The current generator uses a prepared source index with binary-search as-of selection. Default WGC group filters keep only pre-declared context groups:

- `gold_etf_flows_monthly_total`
- `gold_demand_trends_gold_balance_total_demand_quarterly`
- `gold_demand_trends_gold_balance_total_supply_quarterly`

The CLI supports `--group SOURCE:GROUP_VALUE` for pre-declared additions and `--all-groups` for exploratory archive work, but `--all-groups` should not be used for validation claims.

## MT5 Substrate Findings

Current MT5 connection: redacted_account live account, server `redacted_account-Server 2`.

Important symbol mapping:

| GTOS / file symbol | redacted_account symbol found |
|---|---|
| NAS100 | `NDX100` |
| US30 / US30_cash | `US30` |
| XAUUSD | `XAUUSD` |
| XAGUSD | `XAGUSD` |
| GBPJPY | `GBPJPY` |
| USDJPY | `USDJPY` |
| GBPUSD | `GBPUSD` |

Observed MT5 history depth:

| Market set | M15 availability | H1 availability | M1/M5 availability |
|---|---|---|---|
| XAUUSD/XAGUSD | M15 from 2024-01 / 2024-01 to 2026-04-30 | H1 from 2020 to 2026-04-30 | M1 ~30d; M5 ~180d |
| GBPJPY/USDJPY/GBPUSD | M15 from 2024-01 to 2026-05-01 | H1 from 2020 to 2026-05-01 | M1 ~30d; M5 ~180d |
| NDX100/US30 | Tick data works under live symbols; broad bar probe needs export alias update | needs alias update | ticks available for last 7d |

Tick probe, last 7 days:

| Symbol | 7d ticks |
|---|---:|
| XAUUSD | 3,429,331 |
| XAGUSD | 1,191,658 |
| GBPJPY | 1,446,687 |
| USDJPY | 734,348 |
| GBPUSD | 921,866 |
| NDX100 | 5,164,082 |
| US30 | 1,185,483 |

Conclusion: current MT5 is good enough for fresh tick/microstructure capture and 2024+ M15 expansion on FX/metals. It is not enough by itself for pre-2024 M15/M5/tick substrate robustness across GBPJPY/US30/NAS100.

## External Source Readiness

| Source | Current status | Validation use now |
|---|---|---|
| FRED | Ready for historical snapshots after publication model fix | Yes, macro/calendar bundle |
| CFTC COT | Ready for XAUUSD gold COT; publication model includes 2025 catch-up | Yes for XAUUSD/XAGUSD gold context; more contract mappings needed for FX/index use |
| LBMA calendar | Ready after historical calendar backfill | Yes |
| WGC | Imported, but not PIT historical | Forward/current context only until archived files are collected |
| FlashAlpha | Refreshed 2026-05-01 for QQQ/DIA/SPY/GLD/SLV May expiry | Forward shadow only; no historical verdict yet |

FlashAlpha latest refresh:

| Proxy | GTOS target | Expiry | Net GEX |
|---|---|---|---:|
| QQQ | NAS100 | 2026-05-15 | +581,518,250 |
| DIA | US30 | 2026-05-15 | -83,326,613 |
| SPY | US30 | 2026-05-15 | -77,913,435 |
| GLD | XAUUSD | 2026-05-15 | +15,132,405 |
| SLV | XAGUSD | 2026-05-15 | +31,358,202 |

## Do We Need More Data?

Yes, but not for everything.

We have enough to proceed with:

- `calendar_macro_bundle_v1` first-pass validation over the 2025-10 to 2026-04 M15 window.
- Forward collection of FlashAlpha GEX and WGC context from 2026-05-01 onward.
- Fresh MT5 tick and M1/M5 extraction for the recent 30-180 day window.

We need more data for:

- Historical GEX/options-regime validation before 2026-05-01.
- Point-in-time WGC history.
- Pre-2024 M15/M5 robustness for GBPJPY, US30, NAS100, and XAUUSD if the goal is substrate-robust external-feed validation rather than only current-regime validation.
- Broker-normalized index histories, because redacted_account live symbols are `NDX100` and `US30` while older files use `NAS100` and `US30_cash`.

## Recommended Next Extraction Path

1. Update/export a redacted_account alias-aware OHLCV extractor for `NDX100` -> `NAS100` and `US30` -> `US30`, without overwriting existing historical CSVs.
2. Export current broker M15/H1/H4/D1 from 2024-01-01 to now for XAUUSD, XAGUSD, GBPJPY, USDJPY, GBPUSD, NDX100, and US30 into a versioned substrate folder.
3. Export M1 for the last 30 days and M5 for the last 180 days for the same symbols.
4. Export tick data in daily chunks for the last 7-30 days where MT5 permits it, especially NDX100/US30/XAUUSD.
5. For pre-2024 M15/M5 robustness, test no-cost alternate MT5 demo brokers with the same history-depth probe before committing to any broker-specific substrate.
6. For FX/metals tick backfill, evaluate Dukascopy/JForex or a stable Dukascopy downloader because Dukascopy exposes historical tick retrieval by time interval.
7. For historical options/GEX, do not scrape. Use FlashAlpha forward collection now; separately investigate licensed/paid historical options data or public Cboe volume/put-call data as a weaker proxy.

## Source Notes

- MQL5 Python `copy_rates_range` supports bar retrieval by symbol, timeframe, and date range: https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py
- MQL5 Python `copy_ticks_range` supports tick retrieval by symbol/date range and tick flags: https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py
- MetaTrader chart history depends on local/server history and the terminal `Max. bars on chart` setting: https://www.metatrader5.com/en/terminal/help/charts_analysis/charts
- CFTC states COT reports are usually released Friday at 3:30pm Eastern and reflect the previous Tuesday; holiday delays exist: https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm
- CFTC published a 2025 shutdown catch-up schedule with revised publication dates: https://www.cftc.gov/PressRoom/PressReleases/9138-25
- FRED observations use real-time periods; defaults describe what is known today, while historical availability needs explicit modeling/vintages: https://fred.stlouisfed.org/docs/api/fred/realtime_period.html
- Dukascopy JForex supports historical tick retrieval by time interval: https://www.dukascopy.com/wiki/en/development/strategy-api/historical-data/history-ticks/
- Cboe public historical data is mainly volume/put-call style data; custom options/VIX datasets point to Cboe DataShop: https://ww2.cboe.com/us/options/market_statistics/historical_data/
