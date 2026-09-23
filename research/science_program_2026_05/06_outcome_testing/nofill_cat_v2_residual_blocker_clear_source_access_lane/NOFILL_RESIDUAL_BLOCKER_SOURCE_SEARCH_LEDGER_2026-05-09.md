# NOFILL Residual Blocker Source Search Ledger

Promotion posture: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

| Root | Patterns | Files | Access |
| --- | --- | ---: | --- |
| repo-local data | data/**/*NAS100*_M*.csv, data/**/*XAUUSD*_M*.csv | 2 | SEARCHED |
| C:\Users\MSI\Documents\ai-trading-agent\data\ticks | NAS100/2026-05-03.parquet, USDJPY/2026-05-01.parquet, XAUUSD/2026-05-03.parquet, XAUUSD/2026-05-05.parquet, XAUUSD/2026-05-06.parquet | 5 | SEARCHED |
| C:\Users\MSI\Documents\ai-trading-agent\data\sierra_ohlcv_roots | **/NAS100*_M1.csv, **/XAUUSD*_M1.csv | 2 | SEARCHED |
| C:\SierraChart\Data | 6JM26-CME.scid, GCM26-COMEX.scid, MGCM26-COMEX.scid, MNQM26-CME.scid, NQM26-CME.scid, XAUUSD.scid | 6 | SEARCHED |
| C:\SierraChart\Data\MarketDepthData | *.2026-05-03.depth | 2 | SEARCHED |
| C:\tmp\gtos_otb | */OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet | 1 | SEARCHED |
| C:\Users\MSI\Documents\ai-trading-agent | XAUUSD_M1.csv | 1 | SEARCHED |
| C:\tmp\gtos_otb\NOFILLBLOCKCLEAR\research\science_program_2026_05\06_outcome_testing\oti3_usdjpy_price_only_quote_or_tick_contract | OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet | 1 | SEARCHED |
| C:\Users\MSI\Documents\ai-trading-agent\data\mt5_research_exports | USDJPY_M1.csv | 1 | SEARCHED |
| C:\tmp | OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet, OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet, XAUUSD_M1.csv / NAS100_M1.csv / USDJPY_M1.csv | 4 | SEARCHED_WITH_SOME_PERMISSION_DENIED_TEMP_PYTEST_DIRS_NOT_SOURCE_CANDIDATES |
| data/account_history and broker/order/history-like sources | account_history, order_history, broker_actual_r | 0 | INTENTIONALLY_NOT_CONSUMED_FOR_THIS_LANE |

Every consumed source file with `exists=true` is hashed in the JSON ledger and clearance packet source hash manifest.
