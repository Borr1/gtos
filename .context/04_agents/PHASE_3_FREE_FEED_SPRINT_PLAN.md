# Phase 3 Free-Feed Integration Sprint Plan

**Date:** 2026-04-30  
**Owner:** Main-thread engineering plan for CEO approval  
**Status:** PLAN ONLY — no production trading-logic change  
**Deliverable scope:** ingestion/cache/join architecture for free public macro, precious-metals, and options-regime feeds. This plan intentionally does **not** edit `src/components/orchestrator.py`, `prompts/`, or `config/agent_config.yaml`.

---

## Executive Summary

Phase 3 should implement the existing Agent D free-feed ticket as data infrastructure before any new ML or trading-logic work. The goal is to unblock calendar/macro/dealer-regime feature research at $0 recurring data cost while preserving the DSR discipline locked on 2026-04-29.

**Primary rule:** every source enters GTOS as a cached, versioned sidecar feed first. Production decision impact requires a later CEO-approved change, a pre-registered hypothesis, and the existing methodology gates: DSR-corrected p-value, PBO, effective_N, CPCV/path discipline, and no in-sample re-validation.

**Expected Phase 3 value:** the sprint does not by itself claim alpha. It creates the substrate for 19 Agent D substrate-immune items, especially Agent J calendar/macro candidates and NAS/US30 dealer-gamma regime features. Individual feed features are unlikely to clear the Sharpe 3.078 DSR noise ceiling at N=200 alone; the defensible claim unit is a frozen, bundled feature family tested once against canonical baselines.

---

## Pre-Flight Evidence Read

- Regenerated `.context/LIVE_STATE.md` with `python scripts/generate_live_state.py`.
- Read `.context/LIVE_STATE.md`, session 47 handoff, session 45 handoff, quick reference card, Phase 2 master synthesis, and the three required Claude memory files.
- Located existing ticket: `research/operations/free_feed_integration_sprint_2026-04-29.md`.
- Located substrate screen function: `research/ml_program/forensics/2026-04-29/agent_d_pre_dispatch_screen.py`.
- Located partial COT research scripts: `scripts/session9_task2_cot.py` and `scripts/session9_task2_cot_v2.py`.

**Existing-state conclusion:** no production-ready free-feed fetcher/cache/join layer exists. The COT scripts are historical research scripts that directly download CFTC files and yfinance gold futures data; they should be mined for field mappings only, not reused as production ingestion. The existing free-feed ticket is directionally correct but lacks source-level schemas, validation gates, and day-by-day dependencies; this document fills that gap.

---

## Non-Goals and Guardrails

- No trading-logic changes in this sprint plan.
- No prompt changes, no config changes, no orchestrator edits.
- No live order gating or sizing effect from these feeds until a later CEO approval.
- No paid data subscription commitment; account creation is limited to free API keys/accounts.
- No scraping where source terms prohibit automated extraction.
- No standalone alpha claim from any source until the frozen validation protocol clears the DSR ceiling.

---

## Target Architecture

### Sprint Output Shape

The implementation sprint should create an external-feed spine with three layers:

1. **Raw cache** — immutable source pulls under `data/external/raw/{source}/`.
2. **Normalized cache** — source-independent parquet/CSV tables under `data/external/normalized/{source}/`.
3. **Shadow join artifacts** — per-symbol, per-candle feature snapshots under `data/external/features/{symbol}/`, aligned to the M15 candle timestamp but not consumed by live trading.

### Common Fetcher Contract

Each source fetcher should expose the same conceptual contract:

```text
fetch_since(start_date, end_date) -> raw_artifact_paths
normalize(raw_artifact_paths) -> normalized_table
latest_status() -> freshness + schema + row_count + checksum
join_asof(symbol, candle_close_utc) -> feature_dict
```

### Join Policy

- **Join key:** `asof_utc <= candle_close_utc`, never forward-fill future publications.
- **Publication timestamp:** store separately from observation date for every source.
- **Timezone:** normalize all timestamps to UTC and store source-local timestamp fields when relevant.
- **Initial integration:** shadow-only artifact generation and research/K54 feature-catalog input.
- **Possible later production integration:** a CEO-approved external-context provider can join these artifacts after Component 2 MSO creation and before Component 3A prompt rendering, or post-AI as a risk/regime overlay. That is explicitly outside this task.

---

## 10-Engineering-Day Breakdown

One engineering day here means approximately 3-6 focused hours.

| Day | Work | Dependencies | Output |
|---:|---|---|---|
| 1 | Define common external-feed schema, directory layout, source registry, status metadata, and frozen as-of join rules | None | Design doc + schema fixtures + no-source fake feed tests |
| 2 | Build common ingestion/cache library and validation harness scaffolding | Day 1 | Fetcher base class, checksum cache, HTTP retry/backoff, freshness validator, fixture-driven tests |
| 3 | Implement FRED fetcher first because it is clean JSON, high validation value, and supplies shared macro series for other features | Days 1-2, free FRED API key | FRED raw/normalized cache + series metadata + stale-series checks |
| 4 | Implement CFTC COT fetcher using Public Reporting/Socrata endpoints with annual ZIP fallback | Days 1-2 | COT gold/silver/FX/index mappings, normalized weekly positioning table |
| 5 | Implement WGC fetcher for central-bank reserves/flows and ETF flows via free Goldhub downloads/manual-cookie-safe workflow | Days 1-2 | WGC normalized monthly/weekly gold-flow tables and source checksum registry |
| 6 | Implement LBMA fix calendar and licensed-data gate; optionally support an approved free/legal price file if CEO confirms terms | Days 1-2 | Fix-window calendar features, DST tests, legal gate for actual fix prices |
| 7 | Implement CBOE/FlashAlpha GEX proxy plus official Cboe vol-index fallback series | Days 1-2, free FlashAlpha API key | Daily SPY/QQQ/DIA GEX snapshots + VIX/VIX9D/GVZ fallback normalized table |
| 8 | Build M15 as-of join harness and generate shadow feature snapshots for historical candles | Days 3-7 | Per-symbol feature joins, no-lookahead tests, missing-data markers |
| 9 | Add source-specific tests, schema-drift fixtures, freshness dashboard, and failure-mode simulations | Days 3-8 | Unit tests, golden fixtures, status report script |
| 10 | Produce sprint handoff: source status, validation evidence, unresolved terms/account issues, and next research dispatch specs | Days 1-9 | Completion report + recommended pre-registered feature bundles |

**Critical dependency order:** schema and validation come first. Fetchers are not useful until as-of semantics, publication timestamps, and stale-data behavior are standardized.

---

## Source Plan: CFTC COT

### Source and Access

- **Primary source:** CFTC Commitments of Traders Public Reporting Environment.
- **PRE landing page:** `https://publicreporting.cftc.gov/stories/s/r4w3-av2u`
- **Disaggregated combined endpoint:** `https://publicreporting.cftc.gov/resource/kh3c-gbw2.json`
- **Disaggregated futures-only endpoint:** `https://publicreporting.cftc.gov/resource/72hh-3qpy.json`
- **Traders in Financial Futures endpoint:** `https://publicreporting.cftc.gov/resource/gpe5-46if.json`
- **Fallback annual ZIPs:** `https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm`

### Rate Limits / Quota

- CFTC FAQ indicates API use generally works without tokens if not overused.
- Underlying Socrata guidance: app tokens provide higher quotas; conservative default should be <=1 request/second and <=100 requests/day because COT is weekly.
- Fetch cadence should be weekly after Friday publication, with daily retry until the new report appears.

### Extracted Schema

| Field | Type | Unit | Notes |
|---|---|---|---|
| `source` | string | n/a | `cftc_cot` |
| `report_type` | string | n/a | `disagg_futures_only`, `disagg_combined`, `tff_futures_only` |
| `report_date` | date | date | Tuesday observation date |
| `published_at_utc` | datetime | UTC | Friday release timestamp inferred from fetch time unless source exposes exact publication |
| `market_name` | string | n/a | Source market name |
| `cftc_contract_market_code` | string | n/a | Contract identifier; e.g. gold COMEX mapping uses existing research code `088691` |
| `gtos_symbol` | string | n/a | `XAUUSD`, `XAGUSD`, `USDJPY`, `GBPJPY`, `GBPUSD`, `US30`, `NAS100` where mapping is defensible |
| `open_interest` | int | contracts | Source open interest |
| `managed_money_long` | int | contracts | Disaggregated report |
| `managed_money_short` | int | contracts | Disaggregated report |
| `managed_money_spread` | int | contracts | Disaggregated report |
| `managed_money_net` | int | contracts | long - short |
| `producer_merchant_net` | int | contracts | long - short; physical hedger proxy |
| `swap_dealer_net` | int | contracts | long - short |
| `leveraged_funds_net` | int | contracts | TFF only |
| `asset_manager_net` | int | contracts | TFF only |
| `net_position_pct_lookback` | float | percentile | Rolling percentile over 3y/5y/full history |
| `weekly_net_change` | int | contracts | Current net minus prior report |

### Update Cadence

Weekly. Observation is Tuesday close; publication is Friday. The join must use publication availability, not observation date, to avoid lookahead.

### Pipeline Join

- **Initial:** shadow-only feature snapshots and K54/research catalog input.
- **Eventual candidate:** pre-AI context for gold, silver, and FX/JPY crowding regimes; also possible post-AI risk overlay if extreme positioning correlates with continuation decay.

### Validation Gate

- New report freshness: latest `report_date` should be the prior Tuesday after Friday publication; tolerate CFTC holiday delays.
- Open-interest identities must balance long and short totals within source-defined tolerances.
- Contract mapping must be pinned in a local mapping fixture and reviewed manually for each GTOS symbol.
- Normalized row count per report date must be stable; unexpected column additions/removals fail schema validation.
- Backfill must reproduce existing research-script gold COT fields for overlapping dates before the old scripts are retired as references.

### Hypothesis and DSR Rank

**Rank: 4 of 5 feeds.** COT can proxy slow crowding and hedger/speculator extremes, especially for XAUUSD/XAGUSD and JPY/GBP futures. It is structurally independent from M15 OB detection but too slow and lagged to be a standalone intraday alpha. Treat as a regime-conditioning feature inside a bundled macro/calendar hypothesis. Do not claim lift unless the bundled feature family clears Sharpe 3.078 DSR noise-floor discipline at N=200.

### Definition of Done

- Production-ready fetcher with cached raw JSON/CSV and normalized parquet/CSV.
- Contract mapping fixture with at least XAUUSD and XAGUSD confirmed; FX/index mappings either confirmed or explicitly disabled.
- Unit tests for parser, no-lookahead publication join, schema drift, missing weekly report, and holiday delay.
- Status report exposes latest report date, fetch timestamp, row count, checksum, and stale/fresh verdict.

---

## Source Plan: FRED Macro

### Source and Access

- **Docs:** `https://fred.stlouisfed.org/docs/api/fred/`
- **Series observations endpoint:** `https://api.stlouisfed.org/fred/series/observations?series_id={SERIES_ID}&api_key={FRED_API_KEY}&file_type=json`
- **Candidate series:** `DGS10`, `DGS2`, `DFII10`, `T10YIE`, `VIXCLS`, `GVZCLS`, `DTWEXBGS`, `SOFR`, `IORB`. Final series list should be frozen after an availability audit on Day 3.

### Rate Limits / Quota

- Free API key required.
- FRED v2 documentation states 2 requests/second before 429; use <=1 request/second with exponential backoff and cache daily.
- Some series have third-party copyright or discontinuation notes; fetcher must record source notes and fail closed for prohibited use.

### Extracted Schema

| Field | Type | Unit | Notes |
|---|---|---|---|
| `source` | string | n/a | `fred` |
| `series_id` | string | n/a | FRED series ID |
| `series_title` | string | n/a | From FRED metadata |
| `observation_date` | date | source date | Economic observation date |
| `published_at_utc` | datetime | UTC | Prefer FRED realtime/update metadata; otherwise fetch time with release-lag marker |
| `value` | float | series unit | `.` becomes null |
| `unit` | string | n/a | Percent, index, spread, etc. |
| `frequency` | string | n/a | Daily/weekly/monthly |
| `is_revised` | bool | n/a | If ALFRED/vintage tracking is added later |
| `z_252d` | float | z-score | Rolling daily z-score where valid |
| `delta_1d` | float | unit | Daily change |
| `delta_5d` | float | unit | Weekly change |

### Update Cadence

Daily for market series and most rates; monthly/irregular for macro releases. The fetcher should read series frequency from metadata and validate freshness per series, not globally.

### Pipeline Join

- **Initial:** shadow-only and K54 feature catalog.
- **Eventual candidate:** pre-AI context for macro regime: real yields, USD pressure, volatility regime, and funding-liquidity stress.
- **Possible later post-AI use:** risk/sizing overlay only after CEO approval and a separate validation ticket.

### Validation Gate

- API response status must be 200; 429 triggers retry/backoff and stale-cache fallback.
- `.` values become null and never silently zero.
- Latest observation age must be within expected series cadence plus holiday tolerance.
- Series metadata must be cached with `last_updated`, title, unit, and frequency.
- Known sanity ranges: rates and volatility indices must be finite and non-negative where economically required; dollar-index series must be positive.

### Hypothesis and DSR Rank

**Rank: 3 of 5 feeds.** FRED macro features are broad, clean, and cheap. They are likely more useful as conditioning variables than entry signals: real yields and USD strength for XAUUSD/XAGUSD, VIX/GVZ for volatility state, and funding stress for risk-off regimes. Individual series are low expected lift; bundle as one macro-regime hypothesis to preserve DSR trial budget.

### Definition of Done

- Free-key FRED fetcher supports frozen series list and incremental updates.
- Normalized daily table has metadata, observations, rolling transforms, and null handling.
- Tests cover 429 handling, missing API key, discontinued series, null value parsing, cadence-specific staleness, and no-lookahead joins.
- One command produces a source status summary without touching live trading code.

---

## Source Plan: WGC Gold Flows

### Source and Access

- **Goldhub data index:** `https://www.gold.org/goldhub/data`
- **Central bank reserves/flows:** `https://www.gold.org/goldhub/data/monthly-central-bank-statistics`
- **Gold ETF holdings and flows:** `https://www.gold.org/goldhub/data/gold-etfs-holdings-and-flows`

### Rate Limits / Quota

- No public API rate limit is published.
- Goldhub says registered users get free unlimited access to market data/tools; full dashboard/download access may require free login.
- Use one scheduled fetch/day for weekly ETF data and one scheduled fetch/month for central-bank data; store downloaded XLSX files by checksum.

### Extracted Schema

| Field | Type | Unit | Notes |
|---|---|---|---|
| `source` | string | n/a | `wgc` |
| `dataset` | string | n/a | `central_bank_reserves`, `central_bank_changes`, `gold_etf_flows` |
| `observation_date` | date | source period end | Month/week/date depending on table |
| `published_at_utc` | datetime | UTC | Fetch time unless source file exposes publication date |
| `country_or_region` | string | n/a | Country, region, or global |
| `holder_or_fund` | string | n/a | Central bank, regional ETF aggregate, or fund |
| `gold_tonnes` | float | tonnes | Holdings |
| `change_tonnes` | float | tonnes | Flow/change |
| `flow_usd_mn` | float | USD millions | ETF flow where available |
| `aum_usd_mn` | float | USD millions | ETF AUM where available |
| `source_lag_days` | int | days | Publication lag from observation date |
| `rolling_3m_tonnes` | float | tonnes | Rolling demand impulse |
| `rolling_12m_tonnes` | float | tonnes | Structural-demand state |

### Update Cadence

- Central-bank reserve changes: monthly, often two months in arrears.
- ETF holdings/flows: weekly and monthly; monthly downloadable data usually follows month-end.

### Pipeline Join

- **Initial:** shadow-only gold-flow regime context for XAUUSD/XAGUSD research.
- **Eventual candidate:** pre-AI context for structural gold demand floor, especially for LONG/SHORT asymmetry and side-aware gold sizing research.

### Validation Gate

- XLSX checksum and worksheet names must match expected patterns.
- Latest central-bank file should update within the first 10 days of the month, with explicit two-month arrears tolerance.
- ETF file should update weekly/monthly per Goldhub schedule; stale verdict should distinguish source lag from fetch failure.
- Units must be pinned: tonnes and USD, never ounces unless explicitly converted.
- Cross-table sanity: global/regional subtotals should be reconcilable within rounding tolerance when source tables provide both.

### Hypothesis and DSR Rank

**Rank: 5 of 5 feeds.** WGC flows are mechanistically important for gold but slow and publication-lagged. Their plausible contribution is structural context: central-bank bid, ETF flow regime, and LONG-side asymmetry. Expect low standalone predictive power for M15 entry outcomes; use only inside a gold macro-flow bundle and never as an immediate trade trigger without later evidence.

### Definition of Done

- Download/cache path works with either free-login manual export or approved non-interactive download that respects terms.
- Parser normalizes at least central-bank changes and ETF regional flows.
- Tests cover worksheet drift, unit conversion, missing monthly file, arrears handling, and checksum-based idempotency.
- Status report states latest observation period, latest fetch, expected lag, and stale/fresh verdict.

---

## Source Plan: LBMA Daily Fixings

### Source and Access

- **LBMA precious metals prices page:** `https://www.lbma.org.uk/prices-and-data/precious-metal-prices`
- **ICE LBMA Gold Price catalog:** `https://developer.ice.com/fixed-income-data-services/catalog/lbma-gold-price`

### Rate Limits / Quota

- No free bulk API endpoint is published by LBMA/IBA.
- LBMA states that an IBA licence is required to obtain and use real-time or historical LBMA Gold/Silver Price data for pricing, valuation, transactions, and financial products.
- Therefore, the sprint should split this source into two pieces:
  1. **Free and safe:** fix-time calendar and event-window features.
  2. **Blocked pending CEO/legal decision:** actual historical AM/PM benchmark price ingestion unless an approved free/legal source is confirmed.

### Extracted Schema

For the free fix calendar:

| Field | Type | Unit | Notes |
|---|---|---|---|
| `source` | string | n/a | `lbma_calendar` |
| `metal` | string | n/a | `gold`, `silver`, optional platinum/palladium |
| `fix_name` | string | n/a | `AM`, `PM` |
| `fix_time_london` | time | Europe/London | AM 10:30 London, PM 15:00 London for gold |
| `fix_time_utc` | datetime | UTC | DST-normalized timestamp |
| `trading_date_london` | date | London date | Business day |
| `minutes_to_fix` | int | minutes | Relative to M15 candle close |
| `minutes_since_fix` | int | minutes | Relative to M15 candle close |
| `in_fix_window` | bool | n/a | Configured research window, e.g. +/-30 minutes |
| `uk_us_dst_misalignment` | bool | n/a | True in March/October transition weeks |

For actual prices, if later approved:

| Field | Type | Unit | Notes |
|---|---|---|---|
| `fix_price_usd_oz` | float | USD/troy oz | AM/PM benchmark |
| `fix_price_source` | string | n/a | Licensed source or approved free source |
| `fix_price_licence_ok` | bool | n/a | Must be true before use |

### Update Cadence

- Calendar: deterministic business-day schedule with UK DST.
- Price data, if approved: twice daily for gold and silver benchmarks.

### Pipeline Join

- **Initial:** shadow-only calendar feature for XAUUSD/XAGUSD; no benchmark-price ingestion until licensing is resolved.
- **Eventual candidate:** pre-AI context for candles near AM/PM fix windows, plus research feature for Agent J calendar candidates.

### Validation Gate

- UTC fix times must match quick-reference-card DST rules.
- DST transition weeks must have explicit tests: UK March shift, UK October shift, US/UK misalignment windows.
- Business-day/holiday gaps must be marked as no-fix rather than stale.
- If actual prices are later used, licence approval must be recorded and price rows must have positive USD/oz values, AM/PM labels, source file checksum, and publication timestamp.

### Hypothesis and DSR Rank

**Rank: 2 of 5 feeds.** LBMA fix timing is a high-prior calendar mechanism already embedded in GTOS domain knowledge and independent from OB-zone mechanics. The calendar-only version is likely more robust than scraped fix prices because the hypothesis is event timing, not benchmark-price prediction. Test as part of Agent J calendar bundle: LBMA fix, pre-FOMC drift, FX-fix W-shape, and OPEX calendar.

### Definition of Done

- Calendar generator produces AM/PM fix timestamps in UTC for the full backtest/live period.
- Tests prove correct UTC conversion across 2026 DST transitions and holiday/no-fix gaps.
- Actual price ingestion remains disabled unless CEO confirms legal source/usage.
- Feature snapshots expose fix proximity but do not affect live decisions.

---

## Source Plan: CBOE GEX / Options Regime

### Source and Access

There is no confirmed official free Cboe endpoint for aggregate dealer GEX. Cboe provides official volatility-index history and paid/licensed market data; its delayed quote API page explicitly prohibits automated extraction of delayed quote tables. Therefore, the free sprint should use a GEX proxy and keep source provenance explicit.

- **GEX proxy API:** `https://lab.flashalpha.com/v1/exposure/gex/{symbol}`
- **FlashAlpha API docs:** `https://flashalpha.com/api`
- **FlashAlpha free tier:** 5 requests/day, no credit card, GEX/DEX/VEX/CHEX and levels endpoints.
- **Official Cboe volatility-index history:** `https://www.cboe.com/tradable_products/vix/vix_historical_data/`
- **Cboe delayed quote API restriction reference:** `https://www.cboe.com/delayed_quotes/api/`

### Rate Limits / Quota

- FlashAlpha free tier: 5 requests/day and delayed/freshness limits per account.
- Cboe official vol-index historical CSVs are public convenience data; use low-frequency daily fetches and respect website terms.
- Do not scrape Cboe delayed options quote tables.

### Extracted Schema

| Field | Type | Unit | Notes |
|---|---|---|---|
| `source` | string | n/a | `flashalpha_gex` or `cboe_vol_index` |
| `proxy_symbol` | string | n/a | `SPY`, `QQQ`, `DIA`; maps to US30/NAS100 through documented proxy assumptions |
| `gtos_symbol` | string | n/a | `NAS100`, `US30`, maybe portfolio-wide risk context |
| `as_of_utc` | datetime | UTC | Source snapshot timestamp |
| `underlying_price` | float | USD/index points | Source underlying |
| `net_gex` | float | USD gamma exposure | Source-defined |
| `net_gex_label` | string | n/a | `positive`, `negative`, or source equivalent |
| `gamma_flip` | float | price | Key level |
| `call_wall` | float | strike | Key level |
| `put_wall` | float | strike | Key level |
| `distance_to_gamma_flip_pct` | float | percent | Derived |
| `vix` | float | index pts | Official Cboe VIX if fetched |
| `vix9d` | float | index pts | Official Cboe VIX9D if fetched |
| `gvz` | float | index pts | Official Cboe gold-vol index if fetched |
| `vix1d_vix9d_spread` | float | index pts | Include only if VIX1D source is confirmed legal/free |

### Update Cadence

Daily snapshot for free tier. Intraday refresh is not feasible on the free quota. Paid escalation is outside this sprint and requires CEO approval.

### Pipeline Join

- **Initial:** shadow-only dealer-gamma/regime context for NAS100/US30.
- **Eventual candidate:** pre-AI context for index setups and/or post-AI risk overlay. Negative-gamma regimes may favor momentum continuation; positive-gamma regimes may favor mean reversion or reduce breakout reliability. Any effect must be validated before use.

### Validation Gate

- `as_of_utc` must be current for the latest US trading day; stale snapshots are marked unavailable.
- `underlying_price` must be within a configured tolerance of public ETF/MT5 proxy price after unit/proxy mapping.
- `net_gex_label` must match the sign of `net_gex`.
- Free-tier quota must be protected by daily cache; repeated intraday calls are a bug.
- Proxy mapping must be explicit: QQQ for NAS100, DIA/SPY for US30 depending on empirical correlation and data availability.

### Hypothesis and DSR Rank

**Rank: 1 of 5 feeds.** Options-regime data directly targets the Agent C/Group C diagnosis: NAS/US30 specialist sign-flips may reflect dealer-gamma regime changes. This has the highest source-specific prior, but the free data is a proxy with quota limits and point-in-time history limitations. The DSR-safe claim unit is a pre-registered NAS/US30 dealer-regime feature bundle, not a standalone GEX threshold found after the fact.

### Definition of Done

- Free FlashAlpha account/key documented in `.env.example` or operator instructions, not committed.
- Cached daily GEX snapshots for SPY/QQQ/DIA or confirmed supported alternatives.
- Official Cboe VIX/VIX9D/GVZ fallback fetch where terms permit.
- Tests cover quota-cache behavior, stale `as_of`, sign-label consistency, proxy mapping, and missing-source fail-open behavior.

---

## Cross-Source Risk Mitigations

| Risk | Mitigation |
|---|---|
| Rate-limit hits | Source-specific throttles, checksum cache, exponential backoff, daily/weekly schedules, and no repeated M15 live calls |
| Data-source death | Keep raw artifacts immutable; each source has fallback path or explicit degraded mode; status report marks source unavailable without blocking GTOS |
| Schema drift | Golden fixtures, required-column checks, unknown-column logging, and parser fail-fast for renamed critical fields |
| Timezone errors | Store UTC and source-local timestamps; use `Europe/London` for LBMA, CFTC report-date publication timestamps, US/Eastern only where source release time requires it |
| Holiday gaps | Encode source calendars; holiday/no-publication is not stale; unexpected gap is stale |
| Lookahead bias | Every join uses publication availability timestamp, not observation date; tests intentionally create delayed-publication rows |
| Source licensing | No automated extraction from prohibited pages; LBMA actual fix prices disabled until source/licence is approved |
| Bad values | Null markers for missing values, range checks, no silent zero fill, and provenance metadata on every derived feature |
| Overfitting | Bundle features into pre-registered hypotheses; track trial count; no per-feature p-hacking or in-sample re-validation |
| Live-trading safety | All outputs shadow-only until a separate CEO-approved production integration changes trading behavior |

---

## Done Criteria by Source

| Source | Production-Ready Fetcher | Cache | Join | Tests Required |
|---|---|---|---|---|
| CFTC COT | Incremental Socrata/ZIP fetch with pinned contract mappings | Raw JSON/ZIP + normalized weekly table | Publication-aware weekly as-of join | Parser, contract mapping, OI identity, schema drift, holiday delay, no-lookahead |
| FRED | API-key fetch for frozen series list | Raw JSON + normalized daily table with metadata | Frequency-aware as-of join | API key missing, 429 backoff, null values, stale cadence, discontinued series, no-lookahead |
| WGC | Free-download workflow respecting Goldhub terms | Raw XLSX by checksum + normalized flow tables | Monthly/weekly lag-aware join | Worksheet drift, unit checks, source lag, checksum idempotency, missing file |
| LBMA | Calendar generator; price ingestion only if licence approved | Calendar table; optional licensed price table | Fix-window proximity join | DST transitions, UK/US misalignment, holidays, disabled price gate |
| CBOE/GEX | FlashAlpha free GEX proxy + official Cboe vol-index fallback | Daily JSON/CSV snapshots | Daily options-regime as-of join | Quota cache, stale as_of, sign-label consistency, proxy mapping, missing-source fail-open |

**Global done:** one status command can show freshness, row counts, checksums, schema versions, and next expected update for all sources. A separate join validation command can generate feature snapshots for a historical candle range without modifying live trading code.

---

## Research and Promotion Gates

1. **Pre-register the feature bundle** before looking at outcomes. Recommended bundle names:
   - `calendar_macro_bundle_v1`: LBMA fix calendar + FRED real-yield/USD/vol + WGC flow + COT positioning.
   - `nas_us30_gamma_regime_v1`: FlashAlpha GEX proxy + Cboe VIX/VIX9D/GVZ + OPEX/calendar controls.
2. **Use canonical baselines** from the Phase 2 methodology gate. Do not compare against modeler-modified baselines.
3. **Report DSR-corrected p-values** against cumulative trial count N=200 and Sharpe 3.078 noise ceiling.
4. **Require PBO < 0.4 and effective_N >= 3** before promotion claims.
5. **Keep all live outputs shadow-only** until CEO approves a specific production pathway.

---

## CEO Open Questions

1. **FRED account/key:** should GTOS create a dedicated FRED API key for this repo, or use an operator-managed key outside repo?
2. **Goldhub account:** approve creation of a free World Gold Council Goldhub account for downloadable central-bank and ETF flow data?
3. **LBMA licensing:** do we want actual AM/PM benchmark price ingestion, or only calendar/fix-window features until an IBA/LBMA licence position is clear?
4. **FlashAlpha account:** approve a free FlashAlpha key for 5 GEX requests/day, accepting that this is a proxy and not official Cboe GEX?
5. **Proxy symbols:** for NAS100/US30, should the first pass use QQQ/DIA, QQQ/SPY, or wait for a source that supports index symbols directly?
6. **Production path after shadow:** if a bundle validates, should first production use be pre-AI context, post-AI risk overlay, or K54-only shadow scoring?
7. **Trial-budget allocation:** should the two bundles above each consume one registered trial, or should all five feeds be frozen into one larger Phase 3 macro/calendar trial?

---

## Cost Estimate

| Cost Type | Estimate |
|---|---:|
| Engineering time | 10 eng days = ~30-60 focused hours |
| Paid data accounts | $0 required |
| Free accounts/API keys | FRED, WGC Goldhub, FlashAlpha |
| Ongoing scheduled fetch maintenance | ~1-2 hours/month after stabilization |
| Ongoing source-drift maintenance | ~0.5 day/quarter, higher if WGC/LBMA download formats change |
| Storage | Negligible; expected raw/normalized artifacts are MB-scale to low GB-scale |
| Paid escalation triggers | Only if CBOE/GEX proxy proves valuable or LBMA benchmark prices require licence; separate CEO approval required |

---

## Recommended Immediate Next Step

Approve Day 1-2 only as a schema + cache + validation-harness implementation slice. That keeps the sprint safe: no source credentials needed, no live trading behavior affected, and it forces the no-lookahead/publication-timestamp discipline before any data-specific work begins.

---

## CEO Decision Update — 2026-05-01

The CEO approved proceeding with the recommended implementation path and approved creation of all free accounts/API keys needed for the sprint. Implementation policy is now:

- **Credential storage:** use environment variables loaded from the local operator environment or `.env`; do not hard-code API keys into source files.
- **Approved free accounts/API keys:** FRED, World Gold Council Goldhub, FlashAlpha, and optional Socrata app token.
- **First implementation slice:** schema, cache spine, validation harness, source parsers, read-only status CLI, and tests.
- **First data-source order:** FRED + CFTC first, then WGC + LBMA calendar, then FlashAlpha/Cboe proxy.
- **LBMA actual prices:** remain disabled until IBA/LBMA licensing/use rights are explicit; calendar/fix-window features proceed.
- **CBOE/GEX:** FlashAlpha is accepted for shadow proxy research; not production-authoritative until validated.
- **Promotion path:** external feeds remain shadow/K54-feature-catalog only until a later CEO-approved production integration.
- **Trial budget:** freeze two research bundles rather than five separate source trials: `calendar_macro_bundle_v1` and `nas_us30_gamma_regime_v1`.
- **Broker substrate audit:** approved as a later no-cost investigation across FTMO demo/free MT5 brokers to test history depth, `last`/volume, BookEvents/L2, and spread quality.

---

## Source Reference Links

- CFTC COT PRE and API: `https://www.cftc.gov/MarketReports/CommitmentsofTraders/ExplanatoryNotes/index.htm`
- CFTC Disaggregated Combined Socrata view: `https://publicreporting.cftc.gov/w/kh3c-gbw2/default`
- Socrata app-token/rate guidance: `https://dev.socrata.com/docs/app-tokens.html`
- FRED API docs: `https://fred.stlouisfed.org/docs/api/fred/`
- FRED API errors/rate-limit docs: `https://fred.stlouisfed.org/docs/api/fred/v2/errors.html`
- WGC Goldhub data index: `https://www.gold.org/goldhub/data`
- WGC central-bank gold reserves: `https://www.gold.org/goldhub/data/monthly-central-bank-statistics`
- WGC gold ETF flows: `https://www.gold.org/goldhub/data/gold-etfs-holdings-and-flows`
- LBMA precious-metal prices: `https://www.lbma.org.uk/prices-and-data/precious-metal-prices`
- ICE LBMA Gold Price catalog: `https://developer.ice.com/fixed-income-data-services/catalog/lbma-gold-price`
- Cboe VIX and volatility-index history: `https://www.cboe.com/tradable_products/vix/vix_historical_data/`
- Cboe delayed quote API restriction: `https://www.cboe.com/delayed_quotes/api/`
- FlashAlpha GEX API: `https://flashalpha.com/api`
