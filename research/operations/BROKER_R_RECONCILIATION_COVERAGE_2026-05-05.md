# Broker-R Reconciliation Coverage

**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Coverage

| Metric | Count |
|---|---:|
| `trade_records_total` | 316 |
| `trade_records_with_broker_actual_r` | 3 |
| `trade_records_with_internal_execution_block` | 0 |
| `trade_records_with_synthetic_or_path_fields` | 316 |
| `pending_lifecycle_rows` | 60 |
| `pending_lifecycle_internal_filled_rows` | 0 |
| `slippage_rows` | 3 |
| `j46_shadow_rows` | 3 |
| `j46_rows_with_broker_deal_reconciled_true` | 2 |
| `mt5_deal_history_rows` | 22 |
| `mt5_close_deal_rows` | 11 |
| `mt5_agent_magic_deal_rows` | 6 |

## Join Plan

1. Join pending lifecycle to slippage by trade_id where present, then by ticket and nearest timestamp when trade_id is absent.
2. Join slippage to MT5 deal/account history by ticket and symbol; broker actual R is valid only when close/deal evidence exists.
3. Join trade_records by metadata.trade_id/candle time/symbol to lifecycle rows; do not overwrite broker_actual_r with synthetic/path R.
4. Keep LIMIT_PLACED rows without lifecycle telemetry as unrecoverable for broker actual-R unless MT5 deal history proves a fill.

## MT5 Probe

`python scripts/export_mt5_account_history_readonly.py --start 2026-04-27 --end 2026-05-05 --output data/account_history/mt5_deals_2026-04-27_2026-05-05.jsonl --execute`

## Blocker

Canonical MT5 deal-history export is present. Broker actual-R still requires per-trade joins and must not be inferred from synthetic path rows.
