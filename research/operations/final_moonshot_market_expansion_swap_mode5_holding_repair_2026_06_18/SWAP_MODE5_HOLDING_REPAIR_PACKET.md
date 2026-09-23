# Market Expansion Swap Mode5 And Holding Repair

Decision: `MARKET_EXPANSION_SWAP_MODE5_HOLDING_PROXY_REPAIRED_DEFAULT_OFF_NOT_LIVE_AUTHORITY`

Runtime effect: `none_swap_mode5_holding_proxy_only`

## Result

- Source events preserved: `2596`.
- Computed swap proxy rows: `2596`.
- Mode-5 interest-current event rows repaired: `913`.
- Point-mode event rows recomputed with holding model: `1683`.
- Mean swap proxy R per source event: `-0.0319715806`.
- Total source-event swap proxy R: `-82.9982231247`.

This route repairs the formula/holding-time layer using official MQL5 swap
documentation, committed broker swap fields, order-calc profit conversion, and
local D1 bars. It remains a default-off source-bound proxy: exact broker swap
posting time, broker-posted swap debits/credits, explicit trading-session table,
prospective fills, and VPS packet parity are not closed here.
