# Sierra Chart / Data Source Crawl Source Index

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`
Fetch method: `curl.exe` direct URL fetches, with raw responses saved locally.

## Crawl Summary

- Sierra sitemap URL supplied by owner: <https://www.sierrachart.com/Sitemap.php>
- Sierra sitemap links extracted: `316`
- Sierra raw evidence files saved: `35`
- Upstream/vendor raw evidence files saved: `12`
- Broad web search used for this source set: `no`
- `web.open` used for this source set after owner correction: `no`

## Sierra Chart Evidence

Raw files are under:

`research/sierrachart_data_source_research_2026-05-02/raw/`

Key official Sierra Chart URLs fetched:

- `sierra_sitemap.html` -> <https://www.sierrachart.com/Sitemap.php>
- `sierra_01_page_doc_Packages_php.html` -> <https://www.sierrachart.com/index.php?page=doc/Packages.php>
- `sierra_02_page_doc_FuturesData_php.html` -> <https://www.sierrachart.com/index.php?page=doc/FuturesData.php>
- `sierra_03_page_doc_DenaliExchangeDataFeed_php.html` -> <https://www.sierrachart.com/index.php?page=doc/DenaliExchangeDataFeed.php>
- `sierra_04_page_doc_DelayedExchangeDataFeed_php.html` -> <https://www.sierrachart.com/index.php?page=doc/DelayedExchangeDataFeed.php>
- `sierra_05_page_doc_SierraChartHistoricalData_php.html` -> <https://www.sierrachart.com/index.php?page=doc/SierraChartHistoricalData.php>
- `sierra_08_page_doc_MarketByOrder_php.html` -> <https://www.sierrachart.com/index.php?page=doc/MarketByOrder.php>
- `sierra_09_page_doc_MarketDepthDataFileFormat_html.html` -> <https://www.sierrachart.com/index.php?page=doc/MarketDepthDataFileFormat.html>
- `sierra_10_page_doc_c_ACSILDepthBars_php.html` -> <https://www.sierrachart.com/index.php?page=doc/c_ACSILDepthBars.php>
- `sierra_11_page_doc_DTCMessages_MarketDataMessages_php.html` -> <https://www.sierrachart.com/index.php?page=doc/DTCMessages_MarketDataMessages.php>
- `sierra_13_page_doc_DTCServer_php.html` -> <https://www.sierrachart.com/index.php?page=doc/DTCServer.php>
- `sierra_16_page_doc_TickbyTickDataConfiguration_php.html` -> <https://www.sierrachart.com/index.php?page=doc/TickbyTickDataConfiguration.php>
- `sierra_17_page_doc_IntradayDataFileFormat_html.html` -> <https://www.sierrachart.com/index.php?page=doc/IntradayDataFileFormat.html>
- `sierra_18_page_doc_ImportExport_html.html` -> <https://www.sierrachart.com/index.php?page=doc/ImportExport.html>
- `sierra_20_page_doc_NumbersBars_php.html` -> <https://www.sierrachart.com/index.php?page=doc/NumbersBars.php>
- `sierra_21_ID_375_page_doc_StudiesReference_php.html` -> <https://www.sierrachart.com/index.php?ID=375&page=doc/StudiesReference.php>
- `sierra_22_ID_141_page_doc_StudiesReference_php.html` -> <https://www.sierrachart.com/index.php?ID=141&page=doc/StudiesReference.php>
- `sierra_24_page_doc_EasySolutionToCMEFundedTradingAccountRequirement_php.html` -> <https://www.sierrachart.com/index.php?page=doc/EasySolutionToCMEFundedTradingAccountRequirement.php>
- `sierra_33_page_doc_SCRealTimeFOREX_php.html` -> <https://www.sierrachart.com/index.php?page=doc/SCRealTimeFOREX.php>

## Upstream / Vendor Evidence

Raw files are under:

`research/sierrachart_data_source_research_2026-05-02/raw/upstream/`

Fetched and usable:

- `vendor_01_databento_com_pricing.html` -> <https://databento.com/pricing>
- `databento_docs_main_bundle.js` -> <https://databento.com/docs/main.380e1401a9de70792589.bundle.js>
- `vendor_07_www_iqfeed_net_index_cfm_displayaction_data_section_services.html` -> <https://www.iqfeed.net/index.cfm?displayaction=data&section=services>
- `vendor_09_www_cqg_com_solutions_market_data.html` -> <https://www.cqg.com/solutions/market-data>

Fetched but not usable as supporting evidence:

- `cme_market_data_platform_attempt.html` -> CME returned an explicit automated-fetch block / 403. No CME facts in the synthesis rely on this blocked page.
- `vendor_08_dxfeed_com_market_data_futures.html` -> dxFeed returned an anti-bot redirect / 403 path. Not used for claims.
- `vendor_06_bookmap_com_en_data.html` -> returned 404 for the attempted URL. Not used for claims.
- `rithmic_data.html` -> returned a Rithmic 404 page for the attempted URL. Not used for claims.

## Evidence Rules Used

- If a page was blocked or returned 404, it is recorded as blocked and not used as proof.
- Sierra facts are sourced from saved official Sierra pages.
- Databento facts are sourced from its saved pricing page, saved docs bundle, and the already-validated local Databento capture work in `research/databento_orderflow_capture_2026-05-02/`.
- No live-trading recommendation is made. Everything here remains research/tooling.
