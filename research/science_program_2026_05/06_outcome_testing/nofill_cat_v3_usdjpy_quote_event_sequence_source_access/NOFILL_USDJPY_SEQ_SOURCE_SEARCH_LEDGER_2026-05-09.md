# NOFILL USDJPY Sequence Source Search Ledger

Promotion verdict: `NO_PROMOTION_VERDICT`.

Conclusion: `NO_BROKER_NATIVE_SEQUENCE_SOURCE_FOUND`.

| Root | Status | Finding |
| --- | --- | --- |
| C:\tmp\gtos_otb\NOFILLUSDJPYSEQ | searched | Current worktree carries canonical ledgers and no local data/ticks/USDJPY target parquet. |
| C:\Users\MSI\Documents\ai-trading-agent\data\ticks\USDJPY | searched | May 1 broker quote-state parquet exists; April 20 is absent in main tick root but present in prior read-only OTI3 capture. |
| C:\tmp\gtos_otb | searched_targeted | Prior worktrees expose the same quote-state parquet/ledgers; no sequence, sub-ms, or event-id source was found. |
| C:\Users\MSI\Documents\ai-trading-agent\data\mt5_research_exports | searched | M1 context is price-compatible context only and has no bid/ask quote-event sequence fields. |
| C:\Users\MSI\Documents\ai-trading-agent\shadow_logs | searched_nonconsuming | Runtime shadow logs can identify candidate geometry but are not broker-native quote-event sequence sources; account/history/result logs were not consumed. |
| C:\Users\MSI\Documents\ai-trading-agent\exports | searched | No broker-native USDJPY quote-event sequence export found. |
| C:\SierraChart\Data | searched_proxy_only | Sierra 6J is futures proxy context, not broker-native USDJPY CFD quote sequencing. |

Negative evidence:

- The decisive broker tick files expose ts_utc, ts_msc, bid, ask, last, volume, and flags; no sequence/event ID/sub-ms field exists.
- The exact first ambiguous timestamp has one source row for each target row.
- MQL5 flags identify changed fields, not intra-row ordering among predicates evaluated on one quote-state snapshot.
- Sierra/6J and Databento 6J are proxy futures sources, not broker-native CFD quote-event ordering proof.
- No MT5 account/order/history/deal/position calls and no paid/API/Databento calls were made.
