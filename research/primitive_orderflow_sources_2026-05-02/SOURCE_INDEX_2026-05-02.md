# Primitive Orderflow Source Research Source Index

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Fetch Method

All external pages in this folder were fetched with `curl.exe` and saved under:

- `research/primitive_orderflow_sources_2026-05-02/raw/`

Raw file count: `37`.

This pass intentionally targeted official exchange, venue, and vendor pages. Search-engine snippets were not used as evidence.

## Definition Used

In this pass, "primitive" means closer to the venue or exchange where the book is formed or first distributed:

- exchange-native multicast/API feeds,
- direct exchange or venue market-data products,
- venue central-limit-order-book data,
- normalized feeds sourced from exchange colocation sites,
- broker/DMA feeds only if they expose the exchange/venue book with clear provenance.

It does not mean old historical OHLC data, broad retail quote feeds, or generic platform charts.

## Fetched Sources

| Source | Local raw file | Fetch result | Evidence use |
|---|---|---:|---|
| CME market data | `raw/cme_market_data.html` | 403 body saved | Blocked; not used for facts beyond access constraint. |
| CME Datamine | `raw/cme_datamine.html` | 403 body saved | Blocked; not used for facts beyond access constraint. |
| CME EBS market data | `raw/cme_ebs_market_data.html` | 403 body saved | Blocked; not used for facts beyond access constraint. |
| CME MDP 3.0 public Confluence route | `raw/cme_mdp3_client_systems.html` | 200 | Confirms public route existed, but page shell was noisy; not used for granular claims without separate corroboration. |
| CME MDP 3.0 cmegroup.com route | `raw/cme_globex_mdp3_pdf.pdf` | 403 body saved | Blocked. |
| Databento GLBX.MDP3 docs | `raw/databento_glbx_mdp3.html` | 200 SPA shell | Used with prior saved Databento bundle/evidence and local Databento outputs. |
| Databento MBO docs | `raw/databento_mbo_schema.html` | 200 SPA shell | Used with prior saved Databento bundle/evidence and local Databento outputs. |
| Databento live docs | `raw/databento_live.html` | 200 SPA shell | Used with prior saved Databento bundle/evidence and local Databento outputs. |
| Nasdaq TotalView | `raw/nasdaq_totalview.html` | 200 redirected to Data Link shell | Limited use; validates Nasdaq data route but not detailed feature claims. |
| Nasdaq Historical ITCH | `raw/nasdaq_itch.html` | 200 redirected to Data Link shell | Limited use; validates Nasdaq data route but not detailed feature claims. |
| Nasdaq market data products | `raw/nasdaq_data_products.html` | 200 | Used for navigation/product route only. |
| Cboe U.S. equities market data | `raw/cboe_equities_market_data.html` | 200 | Used only as equity-market source context. |
| Cboe U.S. futures market data | `raw/cboe_futures_market_data.html` | 200 | Used only as non-primary futures/volatility-product context. |
| Cboe book-depth route | `raw/cboe_equities_book_depth.html` | 404 body saved | Not used for facts. |
| Cboe FX route | `raw/cboe_fx_market_data.html` | 404 body saved | Not used for facts. |
| ICE market data | `raw/ice_market_data.html` | 200 | Used only as non-primary exchange/vendor context. |
| ICE connectivity/feeds | `raw/ice_connectivity_feeds.html` | 200 | Used for broad low-latency/connectivity context. |
| Eurex market data routes | `raw/eurex_market_data.html`, `raw/eurex_eobi.html`, `raw/eurex_emdi.html` | 404 bodies saved | Not used for facts. |
| LSEG FX home | `raw/lseg_fx_home.html` | 200 | Used for LSEG FX product map only. |
| LSEG FX subroutes | `raw/lseg_fx_trading.html`, `raw/lseg_fx_market_data.html`, `raw/lseg_fxall.html`, `raw/lseg_matching.html`, `raw/lseg_fx_matching.html` | 404 bodies saved | Not used for detailed claims. |
| LMAX market data | `raw/lmax_market_data.html` | 200 | High-value source for venue-native FX CLOB Level 2/3/ITCH claims. |
| LMAX Global market data fee PDF | `raw/lmax_market_data_fees_pdf.pdf`, `raw/lmax_market_data_fees_pdf.txt` | 200 | Parsed after follow-up; used for LMAX Global fee schedule. |
| LMAX Exchange market data fee PDF | `raw/lmax_market_data_fees_user_supplied_2026-05-02.pdf`, `raw/lmax_market_data_fees_user_supplied_2026-05-02.txt` | User-supplied local PDF | Parsed after follow-up; used for LMAX Exchange fee schedule. |
| Integral market data route | `raw/integral_market_data.html` | 404 body with navigation | Not used for detailed claims. |
| Rithmic home | `raw/rithmic_home.html` | 200 | Used for DMA/low-latency/market-data positioning only. |
| dxFeed futures | `raw/dxfeed_futures.html` | 200 | Used for vendor coverage/real-time/historical route. |
| CQG market data | `raw/cqg_market_data.html` | 200 | Used for broad vendor coverage. |
| IQFeed services | `raw/iqfeed_services.html` | 200 | Used for tick/history/Level II limits. |
| Bookmap data-provider route | `raw/bookmap_data.html` | 404 body saved | Not used for facts. |

## Highest-Signal Evidence Captured

LMAX official page:

- Describes firm limit order liquidity and executable price data from central limit order books in `LD4`, `NY4`, `TY3`, and `SG1`.
- Lists Level 2 depth of book aggregated by price.
- Lists Level 3 disaggregated snapshots of individual entries in the order book.
- Lists ITCH as the most granular full-depth format.
- States full order book market data is available via FIX or binary ITCH.
- States the page is directed to institutional/professional clients.

LMAX Exchange fee PDF, user-supplied:

- Title: `LMAX Exchange market data`; effective date `01 JUNE 2026`; SHA256 `26D912252EF7A4FB3C1F0CB2A07477F6BD985DDAB8903C521FA0C57C409F24DD`.
- FIX connection fees: `LD4 / NY4 / TY3` cost `$500` per venue; `SG1` is free of charge.
- FX-only standard FIX fees: TOB `$1,200`, 3 levels `$2,600`, 5 levels `$6,000`, 10 levels `$13,500`, delayed trade feed `$1,500`.
- Metals-only standard FIX fees: TOB `$500`, 3 levels `$1,200`, 5 levels `$2,400`, 10 levels `$5,500`, delayed trade feed `$1,100`.
- Combined FX/metals standard FIX fees: TOB `$1,500`, 3 levels `$3,000`, 5 levels `$6,500`, 10 levels `$15,000`, delayed trade feed `$1,500`.
- Non-eligible FIX data is throttled to `10` updates/sec. Eligible trading clients can receive unthrottled FIX market data up to `1ms` updates, but the stated eligibility threshold is `$250 million` monthly traded volume per tier/per venue and `$5 billion` monthly traded volume for access to 5 and 10 levels.
- ITCH access for `LD4` costs `$80,000`, reduced to `$25,000` if total global volumes exceed `$25bn` and a minimum aggressive/passive ratio of `30%` is reached.

LMAX Global fee PDF, fetched:

- Title: `LMAX Global market data`; effective date `01 MAY 2026`; SHA256 `56C146515493FF05CF15016FBEAA1A17A4BCD2522B884103D2D8B13D4239421B`.
- Standard connection fee per venue is `$300`.
- Monthly matrix: TOB is free at 1 update/sec and `$4,000` to `$8,500` for 10 to 1,000 updates/sec; 2-5 levels cost `$2,000` to `$12,000`; 5+/10 levels cost `$3,500` to `$15,000`.
- The PDF states charges are commission deductible and that trading `>$5M` per month on any asset class waives the fee, leaving only the connection fee.

Databento official/local evidence:

- Pricing page metadata says real-time and historical APIs, sourced directly from colocation sites, with `$125` free credits.
- Prior saved docs bundle and existing GTOS Databento runs show `GLBX.MDP3`, `MBO`, and `MBP-10` are available in the practical GTOS pipeline.
- Existing GTOS artifacts already extracted trades, MBP-10, and MBO features from Databento for supported CME proxy windows.

Sierra official/local evidence:

- Prior Sierra crawl verified Denali direct exchange/full-depth claims, Package 12 MBO requirement, delayed-feed depth/MBO usefulness, `.depth` file format, and the historical-MBO limitation.

dxFeed official page:

- States real-time, delayed, historical market replay streams, and historical download for futures/futures options.
- Lists CME, CBOT, NYMEX, and COMEX futures categories.

Rithmic official page:

- Describes DMA trade-execution software with high speed, low latency, ultra-low latency, and real-time/delayed/historical market data.

CQG official page:

- Describes over `85` global market data sources, `45` tradable exchanges, and `139` broker environments.

IQFeed official page:

- States real-time true tick-by-tick data for U.S./Canadian equities.
- States Market Depth/Nasdaq Level II is available for an additional fee.
- States U.S. stock/futures/index 1-minute history back to May 2007 and U.S. futures daily history as far back as 1959.

## Blocked / Incomplete

- CME official product pages were repeatedly blocked by `403` anti-bot pages through direct `curl.exe`.
- Several LSEG subroutes and Cboe/Bookmap routes returned `404`.
- LMAX fees are now parsed, but LMAX Exchange and LMAX Global appear to be separate LMAX Group product lanes and must not be conflated.
- Direct exchange-feed pricing/contracting often requires login, sales contact, data agreements, or professional-user status; absence of public pricing is treated as an access constraint, not as evidence of affordability.
