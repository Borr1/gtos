# G7 Source Index

Generated: 2026-05-06T08:30:00Z
Lane: G7
Promotion verdict: NO_PROMOTION_VERDICT

Raw cache directory:

`research/science_program_2026_05/01_domain_syntheses/raw/G7_macro_cross_asset_sources_2026-05-06/`

## Public Source Cache

| Source ID | URL or source | Raw cache | Fetch status | Lane use | Validation state |
| --- | --- | --- | --- | --- | --- |
| SRC-G7-CFTC-COT-001 | `https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm` and historical compressed page | `cftc_cot_index.html`, `cftc_cot_historical.html` | HTTP 200 cached | Weekly positioning/source contract; direct gold predictor killed; FX mapping blocked | `validation_safe=false` |
| SRC-G7-BIS-STATS-001 | `https://www.bis.org/statistics/index.htm` | `bis_statistics_index.html` | HTTP 200 cached | Global liquidity, banking, FX, derivatives source discovery | `validation_safe=false` |
| SRC-G7-FED-FOMC-001 | `https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm` | `fed_fomc_calendars.html` | HTTP 200 cached | Scheduled event/attention labels | `validation_safe=false` |
| SRC-G7-FED-ECONRES-001 | `https://www.federalreserve.gov/econres.htm` | `fed_econres.html` | HTTP 200 cached | Research-feed discovery only | `validation_safe=false` |
| SRC-G7-FRED-RATES-001 | FRED pages/CSV for DFII10, DGS10, DTWEXBGS, T10YIE | No raw cache; curl reset/HTTP 000 during this pass | Fetch blocked | Rates, real-yield, and broad-dollar source candidate only | `validation_safe=false` |
| SRC-G7-LBMA-FIX-001 | `https://www.lbma.org.uk/prices-and-data/lbma-gold-price` and daily auction prices | `lbma_gold_price.html`, `lbma_daily_auction_prices.html` | HTTP 200 cached | Metals benchmark timing context | `validation_safe=false` |
| SRC-G7-WGC-GOLDHUB-001 | `https://www.gold.org/goldhub/data` | `wgc_goldhub_data.html` | HTTP 200 cached | Gold data/flow/correlation source discovery | `validation_safe=false` |
| SRC-G7-ICE-DXY-001 | ICE U.S. Dollar Index futures page | `ice_us_dollar_index_futures.html` | HTTP 200 cached | Official DXY-adjacent source candidate | `validation_safe=false` |
| SRC-G7-LOCAL-GTOS-MACRO-001 | Local GTOS docs/code/audits listed in context ledger | No raw web cache; repo-local sources | Read locally | Prior blockers, killed routes, and local source inventory | `validation_safe=false` |

## Official-Source Notes

- CFTC pages identify Commitments of Traders reports and historical compressed files. Use release timestamp, not report date, for as-of logic.
- BIS statistics page describes official/statistical data access via BIS data services, but no exact table was selected by this lane.
- Fed FOMC calendar page provides scheduled meeting/event context; it is not a surprise or sentiment source.
- LBMA pages identify LBMA Gold Price / daily auction context; timestamp labels do not equal auction imbalance.
- WGC Goldhub data page is useful for data discovery; exact series, download method, and revision rules remain unresolved.
- ICE page is official DXY-adjacent evidence; a validation-safe DXY/broad-dollar data path was not established.

## Local Source Notes

Local artifacts constrain source use:

- `kb_gold_market_deep_knowledge.md`: kills direct COT-gold predictiveness and demotes DXY to soft context.
- `LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md`: notes CFTC/LBMA feasibility and FX COT/KMW fix blockers.
- `LANE6_PRIORITY620_TRIAGE_2026-05-03.md`: notes FRED/LBMA/CFTC/WGC-style source triage and unresolved blockers.
- `LTO031_EXTERNAL_FEED_SOURCE_READINESS_2026-05-05.md`: records external feed blockers for FX mapping, BIS, Fed research, and related macro feeds.
- `src/components/external_feeds.py` and `scripts/fetch_external_feeds.py`: show external-feed plumbing exists, but this lane did not find a validation-ready normalized data cache in the working tree.
- `data/DXY_D1.csv`: visible but stale/suspicious and not accepted as validation evidence.

## Budget State

No paid source was accessed. FRED, BIS, CFTC, Fed, LBMA, WGC, and ICE review stayed within `$0` public/source-discovery constraints. Any paid source, API subscription, or broker data access remains blocked pending owner approval.

Promotion verdict: NO_PROMOTION_VERDICT
