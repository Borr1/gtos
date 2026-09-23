# Phase 3 Market-Data Expansion Audit

**Date:** 2026-05-01
**Status:** research-only; no live trading decision logic changed.

## Executive Answer

We do not have everything needed for a promotion-grade external-feed alpha verdict yet. We do have enough broker-native data to keep building high-quality validation substrates:

- M15: usable across 2022-2026 for all Phase 3 symbols, with indices starting 2022-10-20 on the connected redacted_account terminal.
- H1/D1: usable across 2022-2026 for FX/metals and from 2022-10-20 for NAS100/US30.
- M5: about 100k bars per symbol, back to late 2024.
- M1: about 100k bars per symbol, back to January 2026.
- Tick history: recent daily windows are available from MT5 at high row counts, but not yet exported through a committed backfill script.

The current hard blockers for alpha validation are not MT5 connectivity. They are candidate/outcome depth, actual realized-R coverage, forward GEX/WGC availability, and methodology gates.

## Local Extractions Completed

### M15 expanded substrate

Command:

```powershell
python scripts/export_mt5_research_ohlcv.py --start 2022-01-01T00:00:00Z --end 2026-05-01T00:00:00Z --label phase3_m15_2022_2026_fn_chunked_v1 --timeframes M15 --chunk-days 90 --yes-live-readonly
```

Validation rows generated from this substrate:

- Total rows: 644,952.
- Output root: `data/external/validation/calendar_macro_bundle_v1/phase3_m15_2022_2026_calendar_macro_validation_v1_*`.
- This is the best current all-candle external-feed substrate.

### M1/M5/H1/D1 expanded substrate

Command:

```powershell
python scripts/export_mt5_research_ohlcv.py --start 2022-01-01T00:00:00Z --end 2026-05-01T00:00:00Z --label phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1 --timeframes M1,M5,H1,D1 --chunk-days 30 --yes-live-readonly
```

Output root:

```text
data/mt5_research_exports/phase3_m1_m5_h1_d1_2022_2026_fn_chunked_v1/
```

Total rows exported:

| Timeframe | Files | Total rows |
|---|---:|---:|
| M1 | 7 | 698,224 |
| M5 | 7 | 699,635 |
| H1 | 7 | 171,309 |
| D1 | 7 | 7,421 |

Coverage summary:

| Symbol | M1 first | M5 first | H1 first | D1 first |
|---|---|---|---|---|
| XAUUSD | 2026-01-19 11:59 | 2024-11-29 06:40 | 2022-01-03 01:00 | 2022-01-03 00:00 |
| XAGUSD | 2026-01-19 11:39 | 2024-11-29 03:20 | 2022-01-03 01:00 | 2022-01-03 00:00 |
| GBPJPY | 2026-01-23 08:54 | 2024-12-26 11:25 | 2022-01-03 00:00 | 2022-01-03 00:00 |
| GBPUSD | 2026-01-23 09:15 | 2024-12-26 16:50 | 2022-01-03 00:00 | 2022-01-03 00:00 |
| USDJPY | 2026-01-23 08:58 | 2024-12-26 17:30 | 2022-01-03 00:00 | 2022-01-03 00:00 |
| NAS100 | 2026-01-20 05:27 | 2024-11-28 06:30 | 2022-10-20 11:00 | 2022-10-20 00:00 |
| US30_cash | 2026-01-20 02:01 | 2024-11-28 06:10 | 2022-10-20 11:00 | 2022-10-20 00:00 |

Interpretation: current terminal depth appears governed by MT5 history/chart retention. This is still enough for better labels and regime context, but not enough for deep 2022-2024 M1/M5 unless the terminal history limit can be increased or an alternate source provides it.

## M5 Candidate Simulation

The candidate join now supports timeframe-specific OHLCV simulation. The shared resolver previously hardcoded `{SYMBOL}_M15.csv`; the Phase 3 candidate join now preloads rows from `SYMBOL_<timeframe>.csv` and passes them to the resolver.

Important scope note: this is **not** a 2022-2026 historical AI-candidate replay. The join consumes the current live/shadow candidate log, `shadow_logs/candidate_features_log.jsonl`, and joins those recent rows onto the larger external-feed snapshot substrate. At the time of this audit that live/shadow log covered 2026-04-17 to 2026-05-01, not the full 2022-2026 period.

Generated M5 artifact:

```text
data/external/validation/calendar_macro_bundle_v1/candidate_join/phase3_candidate_calendar_macro_join_2022_2026_plus_gap_m5_sim_v2_20260501T015608Z.jsonl
research/phase_3_external_feed_validation/CANDIDATE_DIAGNOSTIC_M5_SIM_2026-05-01.md
```

M5 diagnostic:

- Rows read: 76 recent live/shadow CANDIDATE rows.
- External validation matched: 70.
- Actual realized-R rows: 2.
- Synthetic R rows: 29.
- Verdict: `SUPPRESSED_DIAGNOSTIC_ONLY`.
- Main useful lead remains volatility-regime related: high VIX is associated with worse synthetic candidate R in this tiny sample. This is not an alpha claim.

## Tick Availability Probe

Read-only MT5 `copy_ticks_range` probes were run for two recent daily windows. They did not send orders.

| Window UTC | XAUUSD | XAGUSD | GBPJPY | USDJPY | GBPUSD | NAS100 | US30_cash |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-04-28 to 2026-04-29 | 717,615 | 240,028 | 266,146 | 127,622 | 171,562 | 1,103,370 | 250,027 |
| 2026-04-30 to 2026-05-01 | 690,806 | 227,561 | 430,117 | 245,746 | 267,117 | 1,278,368 | 253,364 |

Implication: tick-level backfill is available at least for recent windows. The correct next implementation is a dedicated read-only historical tick exporter that writes the same Parquet schema as `src/components/tick_capture.py`, with chunking, dedupe, and UTC timestamp validation. Do not one-off dump massive tick CSVs.

## External Source Assessment

### Current MT5 terminal

Primary source of truth for production CFD substrate. Keep it as the canonical backtest/validation price feed.

Official MT5 documentation states that `copy_rates_range` returns bars from terminal history and that available bar count is controlled by the terminal's `Max. bars in chart` setting. It also requires UTC datetime handling. Source: https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py

Official `copy_ticks_range` supports tick retrieval over a date interval with `COPY_TICKS_INFO`, `COPY_TICKS_TRADE`, or `COPY_TICKS_ALL`. Source: https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py

Action: increase MT5 history retention in the terminal if deeper M1/M5 is needed from the same broker. Then rerun the exporter.

### FTMO free trial / alternate MT5

FTMO advertises 14-day Free Trial accounts and MT5 support. Sources:

- https://ftmo.com/es/ftmo-free-trial/
- https://ftmo.com/en/trading-platforms/

Use case: broker-substrate robustness probe, especially NAS100/US30/XAUUSD/GBPJPY/USDJPY history depth. It is not guaranteed to match redacted_account candles, so treat it as robustness evidence, not production truth.

Concrete path:

```powershell
python scripts/inspect_mt5_history_availability.py --start 2020-01-01T00:00:00Z --end 2026-05-01T00:00:00Z --timeframes M1,M5,M15,H1,D1 --label ftmo_probe_2020_2026 --write-json --yes-live-readonly
```

Run this only after the terminal is logged into the alternate account.

### Dukascopy

Dukascopy provides downloadable historical data for forex, commodities, and indices across tick-to-monthly timeframes. Source: https://www.dukascopy.com/swiss/english/marketwatch/historical/

Use case: independent substrate robustness, especially for FX/metals and maybe index proxies. It is not the same CFD broker feed, so do not mix it into production-candle validation without a separate feed-mismatch study.

### OANDA REST v20

OANDA exposes candle endpoints with M1/M5/M15/H1/D and other granularities; requests have a maximum `count` of 5000 per call. Sources:

- https://developer.oanda.com/rest-live-v20/instrument-df/
- https://developer.oanda.com/rest-live-v20/instrument-ep/

Use case: legal API-based FX candle robustness. Limitation: OANDA explicitly warns historical candle data can differ from the live account pricing stream by account/pricing group, so this is robustness data, not redacted_account truth. Source: https://help.oanda.com/au/en/faqs/rest-v20-api-troubleshooting-guide.htm

### Cboe

Cboe historical option volume and put/call ratio files are usable as broad options-flow context. Source: https://ww2.cboe.com/us/options/market_statistics/historical_data/

Do not scrape Cboe delayed quote tables. Cboe's delayed quote pages explicitly prohibit automated extraction. Source: https://www.cboe.com/delayed_quotes/ARE/quote_table/

Use case: market-level put/call and volume context, not dealer GEX.

### Polygon / ThetaData

Polygon options plans provide U.S. options coverage, Greeks/IV/OI at paid tiers, and varying historical depth. Source: https://polygon.io/pricing?product=options

ThetaData provides options history with 4/8/12-year depth depending tier and tick-level data from Standard upward. Source: https://www.thetadata.net/pricing

Use case: legal GEX/open-interest reconstruction if Phase 3 requires historical option-chain features. This is the clean path for historical GEX, but it is paid and must be treated as a separate source decision.

### Alpha Vantage / EODHD / TrueFX

Alpha Vantage has premium intraday endpoints with historical monthly pulls and FX intraday support. Source: https://www.alphavantage.co/documentation/

EODHD advertises broad stock, ETF, forex, options, and historical EOD coverage. Source: https://eodhd.com/

TrueFX provides indicative FX tick data. Source: https://www.truefx.com/truefx-market-data-faq/

Use case: lower-priority robustness or macro-market context. These do not directly solve production CFD candle truth for redacted_account indices/metals.

## Ambiguities And Decisions

1. **Actual realized-R is still too sparse.** The extractor now recovers 2 actual realized-R rows, but most candidate rows need forward trade completion, broker-history enrichment, or synthetic target handling. No promotion claim is possible.
2. **Historical candidate population is not generated yet.** The 2022-2026 substrate is candle-level. The 76-row candidate diagnostic is recent live/shadow coverage only. A real historical candidate/opportunity generation pass is still required before any high-N candidate-level external-feed validation.
3. **M1/M5 depth is capped at about 100k rows per symbol right now.** This is probably terminal history retention. Increasing MT5 `Max. bars in chart` and restarting/opening charts may extend this.
4. **Historical tick backfill is promising.** Recent daily tick windows are available, but we need a committed exporter before bulk tick backfill.
5. **FlashAlpha remains forward-only under the current Basic workflow.** Use the reset quota for daily snapshots; do not pretend we have historical GEX.
6. **WGC is publication-time constrained.** Current historical rows correctly do not see WGC data before import/publication timestamps.
7. **Alternate brokers improve robustness, not truth.** FTMO/OANDA/Dukascopy can reveal whether a finding survives feed variation, but production promotion must stay anchored to redacted_account candle behavior unless the trading venue changes.

## Best Next Extraction Path

1. Keep the 2022-2026 M15 substrate as the primary external-feed validation base.
2. Generate the 2022-2026 historical candidate/opportunity population. Prefer a broad deterministic opportunity pass first, then a smaller production-faithful AI replay on frozen windows if API budget allows.
3. Use M5 as the preferred synthetic opportunity resolver for 2025-2026 live candidate rows where available.
4. Add a historical tick exporter that writes `data/ticks/{SYMBOL}/{YYYY-MM-DD}.parquet` with the same schema as the live daemon, then backfill only candidate windows first.
5. Use FlashAlpha quota daily for QQQ/DIA/SPY/GLD/SLV single-expiry snapshots; this builds the `nas_us30_gamma_regime_v1` forward dataset.
6. Probe one alternate MT5 account, preferably FTMO Free Trial MT5, with `inspect_mt5_history_availability.py` before exporting anything.
7. If historical GEX becomes important enough to pay for, prefer Polygon or ThetaData APIs over scraping.

Bottom line: this experiment moved us closer. We now know the current terminal can support a much stronger M15/H1/D1 validation base, M5 can improve synthetic labels for recent candidates, tick backfill is technically feasible for recent windows, and the remaining gaps are concrete rather than vague.
