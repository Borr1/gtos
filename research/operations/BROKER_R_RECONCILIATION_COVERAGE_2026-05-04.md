# Broker-R Reconciliation Coverage - 2026-05-04

**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Coverage

| Metric | Count |
|---|---:|
| `trade_records_total` | 268 |
| `trade_records_with_broker_actual_r` | 3 |
| `trade_records_with_internal_execution_block` | 0 |
| `trade_records_with_synthetic_or_path_fields` | 268 |
| `pending_lifecycle_rows` | 0 |
| `pending_lifecycle_internal_filled_rows` | 0 |
| `slippage_rows` | 3 |
| `j46_shadow_rows` | 3 |
| `j46_rows_with_broker_deal_reconciled_true` | 2 |

## Join Plan

1. Join pending lifecycle to slippage by trade_id where present, then by ticket and nearest timestamp when trade_id is absent.
2. Join slippage to MT5 deal/account history by ticket and symbol; broker actual R is valid only when close/deal evidence exists.
3. Join trade_records by metadata.trade_id/candle time/symbol to lifecycle rows; do not overwrite broker_actual_r with synthetic/path R.
4. Keep LIMIT_PLACED rows without lifecycle telemetry as unrecoverable for broker actual-R unless MT5 deal history proves a fill.

## MT5 Probe

`python scripts/mt5_preflight.py then export MT5 account/deal history with a read-only probe before broker-R reconciliation.`

## Blocker

No canonical MT5 deal-history export is present in this repo snapshot; broker actual-R cannot be inferred from synthetic path rows.
