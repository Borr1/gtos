# G11 Source Index

Date: 2026-05-06  
Lane: G11 Data Sources And Market Expansion  
Verdict: NO_PROMOTION_VERDICT

## Local Program Sources

| Source | Role | G11 use |
|---|---|---|
| `research/science_program_2026_05/05_synthesis/G0_WAVE1_RECONCILIATION_2026-05-06.md` | Current merged science-program state | Confirms G11 was not run and no source is validation-safe |
| `research/science_program_2026_05/00_control/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md` | Master registry | Confirms G0 counts and no promotion-safe inherited row |
| `research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.md` | Source registry | Confirms all wave-1 source rows remain blocked |
| `research/science_program_2026_05/00_control/SCHEMA_CONTRACTS_2026-05-06.*` | Row schemas | Used to write G11 JSON rows |
| `research/operations/LTO031_LTO032_SOURCE_CONTRACT_REGISTRY_2026-05-06.md` | Source-unblocking state | Main local source-contract evidence |
| `research/operations/LTO031_LTO032_FREE_PUBLIC_SOURCE_MANIFESTS_2026-05-06.md` | Free/public manifests | CFTC/FRED/BIS/FlashAlpha source status |
| `research/operations/LTO031_LTO032_DATABENTO_CREDIT_REPLAY_MANIFESTS_2026-05-06.md` | Databento replay plan | Blocks paid pull and fetch-ready claims |
| `research/operations/LTO031_LTO032_SIERRA_SCID_FOOTPRINT_PROFILE_PLAN_2026-05-06.md` | Sierra conversion and footprint plan | Supports bid/ask source readiness and derived-feature blockers |
| `research/operations/LTO032_OPTIONS_GAMMA_VRP_SOURCE_MANIFESTS_2026-05-06.md` | Options/gamma manifests | Blocks options/gamma validation |
| `research/operations/K55_SOURCE_BUNDLE_INTEGRATION_PLAN_2026-05-06.md` | External source integration plan | Confirms no numeric-ready K55 feature |
| `research/operations/NO_AI_SHADOW_OBSERVER_RELOAD_PROOF_SOURCE_REGISTRY_2026-05-06.md` | Observer registry | Supports observer-only expansion path |
| `research/primitive_orderflow_sources_2026-05-02/PRIMITIVE_ORDERFLOW_SOURCE_SYNTHESIS_2026-05-02.md` | Orderflow source architecture | Supports Sierra/Databento/LMAX/direct-exchange treatment |
| `research/instrument_expansion_2026-05-02/*.md` | Expansion screen, decay, microstructure | Supports coverage/transfer/friction gates |
| `research/expanded_oos_2026-05-03/*.md` | Expanded OOS source map and candidate registry | Blocks validation claims |
| `research/science_program_2026_05/01_domain_syntheses/G4_MICROSTRUCTURE_AUCTION_SYNTHESIS_2026-05-06.md` | Neighbor lane | Source-gated orderflow cross-domain hypothesis |

## Public Source Captures

All public pages were fetched into `research/science_program_2026_05/01_domain_syntheses/raw/G11_data_sources_expansion_sources_2026-05-06/`. Network access required an approval after the first sandboxed `curl` failed; no paid source was accessed.

| Source ID | URL | Cached file | Evidence notes | Validation-safe |
|---|---|---|---|---|
| G11-PUB-SIERRA-SCID | `https://www.sierrachart.com/index.php?page=doc/IntradayDataFileFormat.html` | `sierra_intraday_file_format.html` | `.scid` format and fields including `NumTrades`, `BidVolume`, `AskVolume` | false |
| G11-PUB-SIERRA-DEPTH | `https://www.sierrachart.com/index.php?page=doc/MarketDepthDataFileFormat.html` | `sierra_market_depth_file_format.html` | market-depth commands and `NumOrders`, `Price`, `Quantity` | false |
| G11-PUB-CFTC-COT | `https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm` | `cftc_cot_index.html` | COT purpose, release lag, history/API notes | false |
| G11-PUB-FRED | `https://fred.stlouisfed.org/docs/api/fred/` | `fred_api_docs.html` | vintages, release calendar, series vintage dates | false |
| G11-PUB-BIS | `https://data.bis.org/` | `bis_data_portal.html` | BIS Data Portal and embedded release calendar | false |
| G11-PUB-CBOE-DATASHOP | `https://datashop.cboe.com/` | `cboe_datashop.html` | downloadable tick/intraday/daily options/equity/ETF source exists | false |
| G11-PUB-CBOE-VIX | `https://www.cboe.com/tradable_products/vix/` | `cboe_vix_overview.html` | volatility-product context | false |
| G11-PUB-NASDAQ-CROSS | `https://www.nasdaqtrader.com/Trader.aspx?id=OpenClose` | `nasdaq_trader_open_close.html` | opening/closing cross timing and subscription-only imbalance data | false |
| G11-PUB-LBMA | `https://www.lbma.org.uk/prices-and-data/precious-metal-prices` | `lbma_precious_metal_prices.html` | benchmark pages and licensing notes | false |
| G11-PUB-DATABENTO-GLBX | `https://databento.com/docs/standards-and-conventions/datasets/GLBX.MDP3` | `databento_glbx_mdp3.html` | JS shell only in capture; weak source-existence evidence | false |
| G11-PUB-DATABENTO-MBO | `https://databento.com/docs/schemas-and-data-formats/mbo` | `databento_mbo_schema.html` | JS shell only in capture; weak source-existence evidence | false |
| G11-PUB-DATABENTO-MBP10 | `https://databento.com/docs/schemas-and-data-formats/mbp-10` | `databento_mbp10_schema.html` | JS shell only in capture; weak source-existence evidence | false |

