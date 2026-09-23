# LTO-015 Broker Actual-R Audit - 2026-05-05

**Schema:** `lto015_broker_actual_r_audit_v1`
**Generated:** `2026-05-17T13:46:25.062994+00:00`
**Status:** `OK_WITH_DOCUMENTED_ACCOUNTING_LIMITATIONS`
**Result scope:** `ACCOUNT_HISTORY_AND_LOCAL_R_MATERIALIZATION`

## Counts

- Audit rows available: `285`
- Audit rows appended this run: `1`
- Complete: `0`
- Complete with documented limitations: `279`
- Action required: `0`

## Evidence Classes

`{'ACCOUNT_HISTORY_REALIZED': 5, 'LIVE_R_ARTIFACT': 274}`

## Scopes

`{'candidate_account_truth': 274, 'filled_trade_reconciliation': 5}`

## Entry Slippage

`{'ENTRY_SLIPPAGE_ROW_BROKER_ZERO_FILL_PRICE_RECORDED_NOT_USED_AS_ACTUAL_FILL': 5, 'NOT_FILL_SCOPE': 274}`

## Truth Boundary

- Broker actual-R claim allowed rows: `5`
- Account-history-realized rows: `5`
- Live R artifact rows: `274`

## MT5 Read-Only Export

`python scripts/export_mt5_account_history_readonly.py --start YYYY-MM-DD --end YYYY-MM-DD --output data/account_history/mt5_deals_YYYY-MM-DD_YYYY-MM-DD.jsonl --execute`

## Safety Counters

- no_ai_calls: `True`
- no_canary_required: `True`
- no_execution: `True`
- paid_data_calls: `0`
