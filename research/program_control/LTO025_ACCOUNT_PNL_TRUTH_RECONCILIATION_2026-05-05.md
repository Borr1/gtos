# LTO-025 Account/PnL Truth Reconciliation - 2026-05-05

**Schema:** `lto025_account_pnl_truth_reconciliation_v1`
**Generated:** `2026-05-17T13:46:32.987415+00:00`
**Status:** `OK_WITH_DOCUMENTED_PNL_TRUTH_LIMITATIONS`
**Result scope:** `ACCOUNT_PNL_AND_MT5_DEAL_MATERIALIZATION`

## Counts

- Reconciliation rows available: `29`
- Reconciliation rows appended this run: `2`
- Complete: `13`
- Complete with documented limitations: `9`
- Action required: `0`

## Evidence Classes

- R evidence: `{'ACCOUNT_HISTORY_REALIZED_R': 4, 'LOCAL_DAILY_PNL_AGGREGATE': 1, 'LOCAL_NOTIFICATION_R_INPUT': 4, 'NONE': 13}`
- Dollar evidence: `{'ACCOUNT_HISTORY_PROFIT': 17, 'LOCAL_DAILY_PNL_AGGREGATE': 1, 'LOCAL_RISK_DOLLAR_PROJECTION': 4}`

## Truth Boundary

- Actual R claim allowed rows: `4`
- Actual dollar claim allowed rows: `17`

## Safety Counters

- no_ai_calls: `True`
- no_canary_required: `True`
- no_execution: `True`
- paid_data_calls: `0`
