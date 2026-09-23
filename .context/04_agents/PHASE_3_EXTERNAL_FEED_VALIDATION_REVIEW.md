# Phase 3 External Feed Validation Review

**Date:** 2026-05-01  
**Reviewer:** Codex GPT-5  
**Scope:** Verify whether the Phase 3 free-feed setup and the operator-provided WGC/FlashAlpha assets were fully handled, or whether gaps remained.

## Verdict

We did **not** lazily stop at the first successful import. Initial implementation had two real gaps:

1. `GDT_Tables_Q126_EN.xlsx` had only been inspected, not imported.
2. The methodology PDFs had not been read/checked against the importer assumptions.

Those are now addressed for this session's scope:

- `ETF_Flows_March_2026.xlsx` imports into normalized WGC ETF-flow rows.
- `GDT_Tables_Q126_EN.xlsx` imports into normalized WGC Gold Demand Trends rows.
- `ETF-Flows-Data-Methodology.pdf` was extracted/read and checked against the importer semantics.
- `Gold_and_major_asset_returns_methodology.pdf` was extracted/read; it describes a returns-comparison tool/methodology, not a raw data table supplied in this session, so no feed import was added for it.
- FlashAlpha Basic is confirmed usable for single-expiry GEX snapshots; full-chain GEX remains Growth-only and is intentionally not pursued right now.

No live trading logic, prompts, or `agent_config.yaml` were changed.

## Validation Commands Run

```powershell
python -m pytest tests/test_external_feeds.py -q
python scripts/fetch_external_feeds.py wgc-import --file ETF_Flows_March_2026.xlsx --dataset gold_etf_flows
python scripts/fetch_external_feeds.py wgc-import --file GDT_Tables_Q126_EN.xlsx --dataset gold_demand_trends
python scripts/fetch_external_feeds.py flashalpha-gex --proxy QQQ:NAS100 --proxy DIA:US30 --proxy SPY:US30 --proxy GLD:XAUUSD --proxy SLV:XAGUSD --expiration 2026-05-15
python scripts/build_external_feed_snapshot.py --symbol XAUUSD --candle-close 2026-04-30T22:50:00Z --source wgc --source flashalpha_gex --source fred --source cftc_cot --source lbma_calendar --write
python scripts/external_feed_status.py --json
```

Latest focused tests: `20 passed`.

## Source-by-Source Closure

| Source / file | Status | Evidence | Notes |
|---|---:|---|---|
| FRED | ✅ Working | DGS10 fetch: 21 rows, latest observation 2026-04-29 | Only DGS10 smoke-fetched so far; broader frozen macro list still needs scheduled run. |
| CFTC/Socrata | ✅ Working | COMEX gold COT fetch: 20 mapped rows, latest report date 2026-04-21 | Socrata alias env vars are supported. |
| LBMA calendar | ✅ Working | 3 generated rows for 2026-05-01 gold/silver fix calendar | Calendar-only by design; no benchmark price ingestion. |
| FlashAlpha Basic | ✅ Working with expiry | QQQ/DIA/SPY/GLD/SLV fetched for expiry 2026-05-15 | Full-chain GEX returns Growth-only 403; Basic requires `expiration=YYYY-MM-DD`. |
| `ETF_Flows_March_2026.xlsx` | ✅ Imported | 101 normalized WGC ETF rows | Snapshot contains March 2026 total ETF demand `-84.83159126` tonnes. |
| `GDT_Tables_Q126_EN.xlsx` | ✅ Imported | 9475 normalized WGC Gold Demand Trends rows | Generic annual/quarterly wide-table importer; useful as context archive, not promoted alpha. |
| `ETF-Flows-Data-Methodology.pdf` | ✅ Reviewed | Extracted with `pypdf`; fields match importer: AUM, holdings, demand, flows | Stored extracted text only under ignored `data/external/status`. |
| `Gold_and_major_asset_returns_methodology.pdf` | ✅ Reviewed / no import | Extracted with `pypdf`; describes dynamic returns methodology | No supplied raw returns workbook, so no normalized feed added. |

## Data Sanity Checks

- WGC ETF workbook sheets detected: `Disclaimer`, `Important notes & Definitions`, `Periods Legend`, `All flows by fund`, `All flows by sub-class`, `Key Tables by fund`, `Key Tables by sub-class`, `Charts Data`, `Holdings by month`, `Demand by month`, `Fund flows by month`.
- WGC ETF normalized output includes both key-table summary rows and monthly history rows.
- WGC GDT workbook sheets detected: `User guide & contents`, `Exec Summary`, `Snapshot`, `Gold Balance`, `Jewellery`, `Bar and Coin`, `Consumer per Capita`, `Gold Prices`, `India Supply`, `ETFs`.
- FlashAlpha values were cached for all intended proxies: `QQQ`, `DIA`, `SPY`, `GLD`, `SLV`.
- XAUUSD snapshot joined: WGC ETF flow, GLD GEX, FRED DGS10, CFTC COT, and LBMA availability marker.

## Known Non-Blocking Limitations

1. `external_feed_status.py` is source-level, so repeated WGC imports overwrite the `wgc` status summary. The normalized cache still preserves both `gold_etf_flows` and `gold_demand_trends`. A future status improvement should report dataset-level freshness.
2. GDT import is broad normalization, not feature selection. It archives rows; the next research step should decide which GDT categories enter the frozen macro bundle.
3. FlashAlpha Basic only gives single-expiry GEX. This is acceptable for shadow research; do not upgrade to Growth unless one month of Basic data shows useful separation.
4. The two methodology PDFs are reviewed context, not data feeds. No PDF-derived numeric rows are joined.
5. No scheduler/cron was added in this session. Fetches are manual CLI runs until the next implementation slice.

## Recommendation

This session's data-acquisition objectives are now complete enough to stop safely. The next session should be fresh and focused on:

1. Dataset-level status reporting.
2. Scheduled daily fetch wrapper for FRED/CFTC/LBMA/FlashAlpha and operator-triggered WGC imports.
3. Frozen feature-bundle definition for `calendar_macro_bundle_v1` and `nas_us30_gamma_regime_v1`.
4. Shadow-only historical snapshot generation across the evaluation window.
