# Phase 3 Next Actions And Data Audit

**Status:** research-only. No live trading logic, prompts, orchestrator, or `agent_config.yaml` changed.
**Date:** 2026-05-01

## Current Answer

This experiment moved us closer to the goal. We now have a recent live/shadow candidate-level external-feed join, a verdict-suppressed diagnostic evaluator, and live MT5 history probes that show the current redacted_account terminal can support a much larger all-candle validation substrate than the previously committed 2026-only CSVs.

It is still not enough for an alpha verdict. Actual realized-R is absent from most joined trade records, candidate coverage is only 72 recent live/shadow CANDIDATE rows in this artifact, resolved synthetic opportunity R is only 29 rows, the 2022-2026 historical candidate/opportunity population has not been generated yet, FlashAlpha/WGC have no usable candidate-level history yet, and DSR/PBO/effective_N have not been computed.

## Committed/Generated Artifacts Used

Committed:

- `scripts/analyze_external_feed_candidate_diagnostics.py`
- `scripts/inspect_mt5_history_availability.py`
- `research/phase_3_external_feed_validation/CANDIDATE_DIAGNOSTIC_2026-05-01.md`

Ignored runtime artifacts:

- `data/external/validation/calendar_macro_bundle_v1/candidate_join/phase3_candidate_calendar_macro_join_union_v2_20260501T010216Z.jsonl`
- `data/external/validation/calendar_macro_bundle_v1/candidate_join/diagnostics/phase3_candidate_calendar_macro_diagnostic_v1_20260501T011700Z.json`
- `data/mt5_research_exports/history_availability/phase3_broad_h1_d1_probe_20260501_20260501T012026Z.json`
- `data/mt5_research_exports/history_availability/phase3_m15_probe_2024_2026_v2_20260501_20260501T012150Z.json`
- `data/mt5_research_exports/history_availability/phase3_m15_probe_2023_calendar_year_v2_20260501_20260501T012150Z.json`
- `data/mt5_research_exports/history_availability/phase3_m15_probe_2022_calendar_year_v2_20260501_20260501T012150Z.json`
- `data/mt5_research_exports/history_availability/phase3_m15_probe_2021_calendar_year_v2_20260501_20260501T012140Z.json`
- `data/mt5_research_exports/history_availability/phase3_m1_current_week_v2_probe_20260501_20260501T012150Z.json`

## What The Diagnostic Extracted

The candidate diagnostic is suppressed by design:

- Verdict: `SUPPRESSED_DIAGNOSTIC_ONLY`
- Actual realized-R rows: 0
- Synthetic target rows: 29
- Required gates not computed: DSR-corrected p, PBO, effective_N
- Trial budget remains protected at bundle level, not feature level.

Useful lead signals, not alpha claims:

- Synthetic resolved candidate set: n=29, sum +9.3602R, mean +0.3228R, win rate 55.2%.
- NAS100 is the current drag: n=11, sum -8.5R, mean -0.7727R, win rate 9.1%.
- GBPUSD and GBPJPY are positive in this tiny synthetic slice, but heavily target-availability-confounded.
- `fred__VIXCLS__value` is the strongest frozen numeric screen in this small artifact: Spearman r -0.5635, high-VIX half mean R lower by -1.4554R. This is a lead for a future frozen hypothesis, not a feature claim.
- LBMA/CFTC touched only the 2 XAUUSD rows. WGC and FlashAlpha were 0 at candidate level, so they need forward accumulation or separately sourced history.

## Off-Boundary Timestamp Audit

Six CANDIDATE rows were excluded from snapshot matching because their timestamps were not on M15 boundaries: examples include `2026-04-20T00:16:10Z`, `2026-04-20T01:31:11Z`, `2026-04-30T00:25:01Z`, `2026-05-01T00:20:04Z`, and `2026-05-01T00:25:03Z`.

Evidence:

- `src/components/data_ingestion.py` stamps live `raw_data["timestamp_utc"]` with `datetime.now(timezone.utc)` instead of the latest closed candle time.
- `src/components/orchestrator.py` normally sleeps to `_next_m15_close(now)` and then processes, but if Windows wakes late or the loop resumes late, the wall-clock timestamp can be off-boundary.
- `src/components/orchestrator.py` passes `getattr(mso, "timestamp_utc", "")` into `log_candidate_features`.
- `src/components/candidate_features_logger.py` writes that timestamp as `timestamp_utc` and builds the evaluation id from it.
- `scripts/build_external_feed_candidate_dataset.py` intentionally refuses off-boundary timestamps instead of flooring them to a guessed candle.

Verdict: this is a data-quality ambiguity, not a live-trading blocker. The highest-quality fix is to add a shadow-only canonical candle-close timestamp derived from the latest closed M15 bar and log it alongside the wall-clock timestamp. That would require explicit approval to edit `src/components/orchestrator.py` and/or live ingestion plumbing.

Do not silently floor these six rows in validation. That would create hidden lookahead/label ambiguity.

## MT5 History Availability

Current connected terminal: redacted_account live account on `redacted_account-Server 2`. The probes were read-only and did not send orders.

Broad H1/D1 probe, 2019-01-01 to 2026-05-01:

- FX majors/crosses: H1/D1 available from 2019.
- XAUUSD/XAGUSD: H1/D1 available from 2019-12.
- NAS100/US30: H1/D1 available from 2022-10-20.

M15 probes:

- 2024-01-01 to 2026-05-01 works in one request for all Phase 3 symbols.
- 2023 calendar-year chunk works for all Phase 3 symbols.
- 2022 calendar-year chunk works partially:
  - XAGUSD from 2022-01-03.
  - XAUUSD from 2022-02-01.
  - GBPJPY/GBPUSD/USDJPY from 2022-04-14.
  - NAS100/US30 from 2022-10-20.
- 2021 M15 is not broadly usable from this terminal. Only XAGUSD has a small late-2021 slice; other symbols return first available bars after the requested range.

M1 probes:

- Current week M1 works for all Phase 3 symbols.
- Full 2026 M1 fails with MT5 `Invalid params`, so M1 must be requested in smaller chunks, probably weekly/monthly.

Interpretation:

- We have enough broker-native M15 data to build a much better 2022-2026 validation substrate than we had this morning.
- We do not have clean pre-2022 NAS100/US30 M15 from this terminal.
- For M1/tick-heavy validation, we should use chunked exports and/or tick daemon captures forward. A second broker/source is still valuable for robustness, especially pre-2022 indices.

## External Source Audit

Primary references checked:

- MetaTrader 5 Python `copy_rates_range` docs: bars are returned from terminal history only, UTC datetimes are required, and availability depends on chart history / Max bars in chart. https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py
- MetaTrader 5 chart docs: charts download history from the server when opened/scrolling, and displayed data is governed by terminal chart settings. https://www.metatrader5.com/en/terminal/help/charts_analysis/charts
- MetaTrader 5 platform settings: `Max. bars in chart` controls how much data is displayed/available for chart work and may require restart. https://www.metatrader5.com/en/terminal/help/startworking/settings
- Dukascopy historical data feed: official historical feed covers FX, commodities, and indices, with downloadable timeframes from tick to monthly. https://www.dukascopy.com/swiss/english/marketwatch/historical/
- Dukascopy JForex FAQ: stored base periods are ticks, 1 minute, 1 hour, and 1 day; other periods are derived; level-2 history is not saved. https://www.dukascopy.com/wiki/en/faq/JForex/feed/
- FTMO Free Trial: 14-day demo/free-trial path exists and supports MT4/MT5 plus other platforms depending region/page. https://ftmo.com/es/ftmo-free-trial/
- FTMO trading platforms: MT5 is officially supported. https://ftmo.com/en/trading-platforms/
- Cboe delayed quote pages explicitly prohibit automated extraction of delayed quote table data. https://www.cboe.com/delayed_quotes/shop/quote_table/
- Cboe historical options data page provides historical options volume / put-call ratio downloads and points paid/custom needs to DataShop. https://ww2.cboe.com/us/options/market_statistics/historical_data/

Practical conclusions:

- Do not scrape Cboe delayed quote tables. It is explicitly prohibited.
- Cboe historical volume/put-call files are acceptable for market-level context, but not dealer GEX.
- FlashAlpha remains the cleaner free/low-cost GEX proxy path for now, within daily quota.
- Dukascopy is the best next non-scraper candidate for independent OHLCV/tick robustness, but it is not the exact redacted_account CFD feed. Treat it as substrate robustness, not production-price truth.
- FTMO free trial is worth probing if the CEO can provide credentials, but current redacted_account already gives substantial M15/H1/D1 history.

## Ambiguities Left Open

- Actual realized-R enrichment: trade records currently do not provide enough realized-R for candidate validation. We need to enrich from live session summaries, trade index, execution/exit records, or broker history.
- Canonical candidate candle close: live shadow rows need a canonical candle-close field separate from wall-clock evaluation time. This needs explicit approval if implemented in orchestrator/live ingestion.
- FlashAlpha history: Basic single-expiry GEX is forward-looking from fetch time; we do not yet have historical GEX snapshots. Validation must start forward or use a paid/archive source later.
- WGC publication timing: imported workbooks are useful context, but candidate rows before the import/publication timestamp should not see them. This correctly produces 0 WGC availability in the current join.
- Broker substrate equivalence: redacted_account CFD candles are the production substrate. Dukascopy/FTMO/other MT5 feeds may improve robustness checks but can also introduce feed mismatch.
- Tick/M1 depth: current terminal supports current-week M1; longer M1 needs chunked probing/export and possibly MT5 chart-cache preparation.

## Next Actions

1. Export broker-native M15 in calendar-year chunks for all Phase 3 symbols:

```powershell
python scripts/export_mt5_research_ohlcv.py --start 2022-01-01 --end 2023-01-01 --timeframes M15 --label phase3_m15_2022 --yes-live-readonly
python scripts/export_mt5_research_ohlcv.py --start 2023-01-01 --end 2024-01-01 --timeframes M15 --label phase3_m15_2023 --yes-live-readonly
python scripts/export_mt5_research_ohlcv.py --start 2024-01-01 --end 2026-05-01 --timeframes M15 --label phase3_m15_2024_2026 --yes-live-readonly
```

2. Build Phase 3 snapshots/validation rows on the chunked M15 substrate and rerun the candidate join. This should materially increase candidate/opportunity coverage.

3. Add actual realized-R enrichment before any alpha verdict. Synthetic R is useful for opportunity diagnostics but not enough for promotion.

4. Keep daily external fetches running so FlashAlpha/WGC/FRED/CFTC/LBMA accumulate forward as-of history.

5. If CEO wants multi-broker robustness, set up one alternate MT5 demo/free trial with NAS100/US30/XAUUSD/GBPJPY/USDJPY and run `scripts/inspect_mt5_history_availability.py` first. No need to export until the probe proves depth.

6. If CEO approves live-ingestion observability work, add a shadow-only canonical `candle_close_utc` field to candidate/trade records. This would remove the off-boundary ambiguity without changing trading decisions.

## Bottom Line

We are closer, not further. The ingestion spine is now usable for validation, the first candidate-level diagnostic exists, and MT5 can provide a broader 2022-2026 M15 substrate if we extract in chunks. The remaining blockers are not hidden complexity; they are data-quality gates: actual realized outcomes, canonical candle timestamps, forward GEX/WGC accumulation, and enough effective independent folds for DSR/PBO.
