# Wave 1A Broker/Candidate Forensic Summary

Evidence labels are preserved row-by-row in `BROKER_TRADE_CANDIDATE_FORENSIC_MATRIX.jsonl`.

## Broker-Real Seed Reconciliation

- Recent GTOS broker trades: `77`.
- Broker-real cash PnL: `$-859.69`.
- Wins/losses: `31` / `46`.
- Win rate: `0.402597`.
- Broker-real expectancy per trade: `$-11.16`.
- Stop-loss/broker-SL exits: `54` for `$-9280.84`.
- Largest winner: position `242667071` `GER30` for `$1318.24`; window without it is `$-2177.93`.

## Worst Symbol Partitions

| Symbol | Trades | Broker-real cash | Wins | Losses |
|---|---:|---:|---:|---:|
| XAUUSD | 12 | -1327.23 | 2 | 10 |
| NDX100 | 15 | -1151.56 | 3 | 12 |
| ETHUSD | 6 | -696.18 | 2 | 4 |
| GBPJPY | 2 | -543.61 | 0 | 2 |
| UKOUSD | 3 | -297.35 | 1 | 2 |
| AUDJPY | 1 | -274.05 | 0 | 1 |
| USDCAD | 3 | -191.6 | 1 | 2 |
| NZDUSD | 2 | -149.99 | 1 | 1 |

## Ledger Counts

- `COST_SWAP_SLIPPAGE_LEDGER.jsonl`: `90` rows
- `DATA_GAP_AND_SOURCE_REPAIR_LEDGER.jsonl`: `27` rows
- `ENTRY_TIMING_AND_PATH_QUALITY_LEDGER.jsonl`: `471` rows
- `FAILURE_TAXONOMY_LEDGER.jsonl`: `96` rows
- `MFE_MAE_TIME_IN_TRADE_LEDGER.jsonl`: `125` rows
- `PORTFOLIO_EXPOSURE_AND_CLUSTER_LEDGER.jsonl`: `77` rows
- `PRODUCTION_CODE_CHANGE_LEDGER.jsonl`: `7` rows
- `PROFIT_RETENTION_AND_GIVEBACK_LEDGER.jsonl`: `94` rows
- `SELECTOR_WEAKNESS_LEDGER.jsonl`: `512` rows
- `SYMBOL_SESSION_HEALTH_LEDGER.jsonl`: `18` rows

## Implementation Consequence

Wave 1A does not mutate broker/account/order/deal/position state. It does create the local builder, matrix, and verifier package required for Wave 2/V4 implementation decisions. The ledger-level implementation decisions require a cost/swap gate, non-bypassable cluster exposure governor, symbol/session recent-damage controls, and stricter broker-net selector admission.
