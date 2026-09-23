# G8 Options, Gamma, VRP Source Index - 2026-05-06

Promotion verdict: `NO_PROMOTION_VERDICT`

This index records the raw source evidence cached for G8 before claims were written. It is not a validation-safe source registry. All sources below remain research-only until parser contracts, publication-time rules, legal/license review, and no-lookahead tests are added.

## Fetch Notes

- First direct shell fetch failed under the workspace network sandbox, then public-source fetches were rerun with approved escalation.
- No paid data was purchased.
- No Cboe delayed option-chain scraping was performed.
- Raw cache directory: `research/science_program_2026_05/01_domain_syntheses/raw/G8_options_vol_sources_2026-05-06/`

## Public Volatility Index CSVs

| Source ID | URL | Cached path | HTTP status | Rows | First date | Last date | G8 use | Validation-safe blockers |
|---|---|---|---:|---:|---|---|---|---|
| `SRC-G8-CBOE-VIX-CSV` | `https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv` | `.../cboe_vix_history.csv` | 200 | 9178 | 1990-01-02 | 2026-05-05 | VIX broad index implied-vol context | Publication timestamp, license review, parser tests, no-lookahead join |
| `SRC-G8-CBOE-VIX1D-CSV` | `https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX1D_History.csv` | `.../cboe_vix1d_history.csv` | 200 | 997 | 2022-05-13 | 2026-05-05 | 1-day equity implied-vol stress context | Same-day availability rule unknown; no source registry entry yet |
| `SRC-G8-CBOE-VIX9D-CSV` | `https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX9D_History.csv` | `.../cboe_vix9d_history.csv` | 200 | 3856 | 2011-01-04 | 2026-05-05 | 9-day implied-vol term-structure context | Same-day availability rule unknown; no source registry entry yet |
| `SRC-G8-CBOE-GVZ-CSV` | `https://cdn.cboe.com/api/global/us_indices/daily_prices/GVZ_History.csv` | `.../cboe_gvz_history.csv` | 200 | 4180 | 2009-09-18 | 2026-05-05 | Gold ETF implied-vol context for XAU/XAG hypotheses | ETF-to-CFD proxy transfer, publication timestamp, parser tests |
| `SRC-G8-CBOE-VVIX-CSV` | `https://cdn.cboe.com/api/global/us_indices/daily_prices/VVIX_History.csv` | `.../cboe_vvix_history.csv` | 200 | 5013 | 2006-03-06 | 2026-05-05 | Vol-of-vol tail context for index hypotheses | Publication timestamp, parser tests, no-lookahead join |
| `SRC-G8-CBOE-VIX3M-CSV` | `https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX3M_History.csv` | `.../cboe_vix3m_history.csv` | 200 | 4182 | 2009-09-18 | 2026-05-05 | Longer-tenor implied-vol/VRP context | Publication timestamp, parser tests, no-lookahead join |

## Cboe Methodology And Product Pages

| Source ID | URL | Cached path | HTTP status | G8 use | Validation-safe blockers |
|---|---|---|---:|---|---|
| `SRC-G8-CBOE-VIX1D-METHODOLOGY` | `https://cdn.cboe.com/api/global/us_indices/governance/Volatility_Index_Methodology_Cboe_1-Day_Volatility_Index.pdf` | `.../cboe_vix1d_methodology.pdf` | 200 | Methodology context for VIX1D construction | Methodology is not a time-series source; no decision-time availability rule |
| `SRC-G8-CBOE-SELECTED-VOL-METHODOLOGY` | `https://cdn.cboe.com/api/global/us_indices/governance/Volatility_Index_Methodology_Cboe_Selected_Volatility_Indices.pdf` | `.../cboe_selected_vol_indices_methodology.pdf` | 200 | Methodology context for GVZ/VVIX and selected volatility indices | Methodology is not a time-series source |
| `SRC-G8-CBOE-VIX-PRODUCT` | `https://www.cboe.com/tradable_products/vix/` | `.../cboe_vix_product.html` | 200 | Cboe description of VIX as SPX-option-implied expected volatility | Product page is descriptive, not a validation feed |
| `SRC-G8-CBOE-VIX-HISTORICAL-DATA-PAGE` | `https://www.cboe.com/tradable_products/vix/vix_historical_data/` | `.../cboe_vix_historical_data.html` | 200 | Discovery page for historical volatility-index CSVs | Page-level discovery only |
| `SRC-G8-CBOE-VIX-OPTIONS-SPEC` | `https://www.cboe.com/tradable_products/vix/vix_options/specifications/` | `.../cboe_vix_options_specifications.html` | 200 | VIX option product and expiration context | Product spec only; not an options-position or gamma source |
| `SRC-G8-CBOE-SPX-OPTIONS-SPEC` | `https://www.cboe.com/tradable_products/sp_500/spx_options/specifications/` | `.../cboe_spx_options_specifications.html` | 200 | SPX/SPXW option expiration-calendar context | Calendar context only; no open-interest/gamma data |
| `SRC-G8-CBOE-VIX-WHITEPAPER` | `https://www.cboe.com/micro/vix/vixwhite.pdf` | `.../cboe_vix_whitepaper.pdf` | 403/blocked placeholder | Blocked alternate VIX methodology source | Do not cite as valid PDF |

## Options/Gamma Data And Literature

| Source ID | URL | Cached path | HTTP status | G8 use | Validation-safe blockers |
|---|---|---|---:|---|---|
| `SRC-G8-FLASHALPHA-API-PAGE` | `https://www.flashalpha.ai/api` | `.../flashalpha_api.html` | 200 | Vendor description of GEX, gamma flip, call/put wall, 0DTE, Greeks, and free-tier constraints | Vendor proxy only; local Basic integration is forward-context; historical/official aggregate GEX not validated |
| `SRC-G8-BARBON-GAMMA-FRAGILITY-PAGE` | `https://sites.google.com/site/andreabarbon/gamma-fragility` | `.../barbon_gamma_fragility.html` | 200 | Academic mechanism context: dealer gamma imbalance and intraday momentum/reversal | Literature only; no GTOS decision-time source |
| `SRC-G8-BARBON-GAMMA-FRAGILITY-PDF` | `https://sites.google.com/site/andreabarbon/gamma-fragility/BarbonBuraschi_2021.pdf` | `.../barbon_buraschi_2021_gamma_fragility.pdf` | 200 | Academic mechanism context: sign of aggregate gamma and liquidity interaction | Literature only; no GTOS decision-time source |
| `SRC-G8-NBER-DEMAND-OPTION-PRICING` | `https://www.nber.org/papers/w11843` | `.../nber_demand_based_option_pricing_w11843.html` | 200 | Academic context for option demand pressure and imperfect hedging | Literature only; no direct feature source |
| `SRC-G8-FED-VRP-EXPECTED-RETURNS` | `https://www.federalreserve.gov/pubs/ifdp/2008/953/ifdp953.htm` | `.../fed_vrp_expected_stock_returns.html` | 200 | Variance risk premium construction context: implied variance minus realized variance | Quarterly equity-return context; cannot be transplanted to intraday GTOS |
| `SRC-G8-CBOE-DELAYED-QUOTES-API-PAGE` | `https://www.cboe.com/us/options/market_statistics/delayed_quotes/` | `.../cboe_delayed_quotes_api.html` | 200 | Blocked-route evidence for delayed quote/chain scraping | No scraping; no validation source without explicit legal API/source contract |
| `SRC-G8-SSRN-GAMMA-FRAGILITY` | SSRN gamma-fragility page | `.../ssrn_gamma_fragility.html` | 403 | Blocked alternate academic source | Access blocked; use author page/PDF only |
| `SRC-G8-SSRN-OPEX-CLUSTERING` | SSRN option-expiration clustering page | `.../ssrn_stock_price_clustering_expiration.html` | 403 | Blocked alternate academic source | Access blocked; no bypass |
| `SRC-G8-CBOE-EQUITY-OPTION-SPEC-ALT` | Cboe equity options spec alternate URL | `.../cboe_equity_options_spec.html` | 404 | Blocked/incorrect alternate product spec route | Not usable evidence |
| `SRC-G8-OCC-SPECS-ALT` | OCC equity options specs alternate URL | `.../occ_equity_options_specs.html` | 403 | Blocked alternate specs route | Access blocked; no bypass |

## Immediate Source Conclusion

Earlier LTO-032 blocker docs correctly blocked official historical aggregate GEX and VRP validation. They were incomplete for public Cboe volatility-index histories: G8 found and cached VIX1D/VIX9D/GVZ/VVIX/VIX/VIX3M CSVs. This does not unlock promotion. It only converts part of the VIX1D/VIX9D/GVZ/VVIX source problem from "not confirmed" to "public CSV discovered, parser/timestamp/license/no-lookahead work still required."

