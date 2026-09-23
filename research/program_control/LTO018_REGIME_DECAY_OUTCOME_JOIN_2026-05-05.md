# LTO-018 Regime / Decay Outcome Join - 2026-05-05

**Schema:** `lto018_regime_decay_outcome_join_report_v1`
**Generated:** `2026-06-01T23:37:20.698246+00:00`
**Status:** `OK_REGIME_DECAY_OUTCOME_JOIN_DOCUMENTED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Counts

- Rows computed: `543`
- Status rows available: `7234`
- Status rows appended this run: `281`
- Candidate context rows: `538`
- Filled context rows: `5`
- Complete joined rows: `208`
- Regime joined rows: `208`
- OB-continuation joined rows: `543`
- Actual-R claim allowed rows: `5`
- Action required: `0`

## Status Breakdown

- Status counts: `{'REGIME_JOIN_MISSING_DECAY_CONTEXT_DOCUMENTED': 335, 'REGIME_DECAY_CONTEXT_JOINED': 208}`
- Row type counts: `{'candidate_regime_decay_context': 538, 'filled_regime_decay_context': 5}`
- Symbol counts: `{'AUDJPY': 8, 'BTCUSD': 24, 'CHFJPY': 21, 'ETHUSD': 23, 'EURGBP': 27, 'EURJPY': 19, 'GBPJPY': 52, 'GBPUSD': 57, 'JP225': 20, 'NAS100': 77, 'NZDUSD': 3, 'UK100': 1, 'UKOIL_cash': 26, 'US30_cash': 40, 'USDCAD': 25, 'USDJPY': 4, 'USOIL_cash': 24, 'XAGUSD': 61, 'XAUUSD': 31}`
- Regime counts: `{'REGIME_MISSING': 335, 'reversal_in_progress': 19, 'trending_bull': 39, 'chop': 100, 'unclear': 50}`
- ML label eligibility counts: `{'SYNTHETIC_PATH_LABEL_WITH_REGIME_DECAY_CONTEXT_NOT_ACCOUNT_HISTORY': 407, 'NO_ACTUAL_R_LABEL_PATH_CONTEXT_WITH_REGIME_DECAY': 81, 'FEATURE_CONTEXT_ONLY_LABEL_NOT_AVAILABLE': 50, 'ACCOUNT_HISTORY_LABEL_WITH_REGIME_DECAY_CONTEXT': 5}`
- Action-required codes: `{}`
- Documented limitations: `{'REGIME_JOIN_MISSING_WITHIN_ASOF_WINDOW': 335, 'SYMBOL_OB_CONTINUATION_SCOPE_UNAVAILABLE_PORTFOLIO_ONLY': 359}`

## Cadence Mix

- Daily regime mix: `{'2026-04-28': {'trending_bull': 1}, '2026-04-29': {'unclear': 1}, '2026-05-01': {'unclear': 1}, '2026-05-03': {'REGIME_MISSING': 2, 'chop': 1}, '2026-05-04': {'reversal_in_progress': 6, 'trending_bull': 14, 'chop': 28}, '2026-05-05': {'REGIME_MISSING': 1, 'chop': 1, 'trending_bull': 21, 'reversal_in_progress': 2}, '2026-05-06': {'reversal_in_progress': 3, 'unclear': 4, 'chop': 3}, '2026-05-07': {'chop': 35, 'unclear': 5}, '2026-05-08': {'chop': 29, 'unclear': 35}, '2026-05-10': {'unclear': 1}, '2026-05-11': {'trending_bull': 2, 'reversal_in_progress': 4, 'unclear': 2}, '2026-05-12': {'reversal_in_progress': 4, 'trending_bull': 1, 'chop': 3, 'unclear': 1}, '2026-05-14': {'REGIME_MISSING': 1}, '2026-05-31': {'REGIME_MISSING': 9}, '2026-06-01': {'REGIME_MISSING': 322}}`
- Weekly regime mix: `{'2026-W18': {'REGIME_MISSING': 2, 'chop': 1, 'trending_bull': 1, 'unclear': 2}, '2026-W19': {'reversal_in_progress': 11, 'chop': 96, 'trending_bull': 35, 'REGIME_MISSING': 1, 'unclear': 45}, '2026-W20': {'trending_bull': 3, 'reversal_in_progress': 8, 'unclear': 3, 'chop': 3, 'REGIME_MISSING': 1}, '2026-W22': {'REGIME_MISSING': 9}, '2026-W23': {'REGIME_MISSING': 322}}`

## Monthly / OB Decay Sources

- Monthly decay report: `{'status': 'MONTHLY_DECAY_REPORT_PRESENT', 'path': 'research\\monthly_decay_monitor\\2026-04_report_including_a1.md', 'mtime_utc': '2026-05-31T21:35:15.036564+00:00', 'age_days': 1.085}`
- Latest OB continuation by scope: `{'AUDJPY': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '0', 'total_count': '0', 'rate_pct': '0.0000', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '-', 'window_end_date': '-'}, 'AUDUSD': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '0', 'total_count': '0', 'rate_pct': '0.0000', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '-', 'window_end_date': '-'}, 'BTCUSD': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '0', 'total_count': '0', 'rate_pct': '0.0000', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '-', 'window_end_date': '-'}, 'CHFJPY': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '0', 'total_count': '0', 'rate_pct': '0.0000', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '-', 'window_end_date': '-'}, 'ETHUSD': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '0', 'total_count': '0', 'rate_pct': '0.0000', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '-', 'window_end_date': '-'}, 'EURGBP': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '0', 'total_count': '0', 'rate_pct': '0.0000', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '-', 'window_end_date': '-'}, 'EURJPY': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '0', 'total_count': '0', 'rate_pct': '0.0000', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '-', 'window_end_date': '-'}, 'EURUSD': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '6', 'total_count': '12', 'rate_pct': '50.0000', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '2025-02-11', 'window_end_date': '2026-03-31'}, 'GBPJPY': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '27', 'total_count': '31', 'rate_pct': '87.0968', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '2023-02-03', 'window_end_date': '2026-04-07'}, 'GBPUSD': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '11', 'total_count': '14', 'rate_pct': '78.5714', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '2025-01-13', 'window_end_date': '2026-04-13'}, 'GER40': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '0', 'total_count': '0', 'rate_pct': '0.0000', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '-', 'window_end_date': '-'}, 'JP225': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '0', 'total_count': '0', 'rate_pct': '0.0000', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '-', 'window_end_date': '-'}, 'NAS100': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '15', 'total_count': '18', 'rate_pct': '83.3333', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '2024-01-08', 'window_end_date': '2026-04-02'}, 'NZDUSD': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '1', 'total_count': '1', 'rate_pct': '100.0000', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '2025-11-25', 'window_end_date': '2025-11-25'}, 'PORTFOLIO': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '35', 'total_count': '50', 'rate_pct': '70.0000', 'alarm_fired': 'false', 'insufficient_sample': 'false', 'window_start_date': '2025-09-26', 'window_end_date': '2026-04-17'}, 'SPX500': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '0', 'total_count': '0', 'rate_pct': '0.0000', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '-', 'window_end_date': '-'}, 'UK100': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '0', 'total_count': '0', 'rate_pct': '0.0000', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '-', 'window_end_date': '-'}, 'UKOIL_cash': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '0', 'total_count': '0', 'rate_pct': '0.0000', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '-', 'window_end_date': '-'}, 'US30_cash': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '21', 'total_count': '32', 'rate_pct': '65.6250', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '2023-03-24', 'window_end_date': '2026-04-17'}, 'USDCAD': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '0', 'total_count': '0', 'rate_pct': '0.0000', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '-', 'window_end_date': '-'}, 'USDCHF': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '0', 'total_count': '0', 'rate_pct': '0.0000', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '-', 'window_end_date': '-'}, 'USDJPY': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '6', 'total_count': '9', 'rate_pct': '66.6667', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '2025-04-22', 'window_end_date': '2026-02-24'}, 'USOIL_cash': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '0', 'total_count': '0', 'rate_pct': '0.0000', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '-', 'window_end_date': '-'}, 'XAGUSD': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '26', 'total_count': '43', 'rate_pct': '60.4651', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '2024-02-29', 'window_end_date': '2026-04-02'}, 'XAUUSD': {'date_utc': '2026-06-01', 'window_size': '50', 'continuation_count': '35', 'total_count': '45', 'rate_pct': '77.7778', 'alarm_fired': 'false', 'insufficient_sample': 'true', 'window_start_date': '2024-04-02', 'window_end_date': '2026-04-17'}}`

## Boundary

This report joins regime/decay context to candidate and filled outcome rows. It is analysis/ML substrate only and does not alter prompts, safety gates, risk, execution, or orders.

## ML Goal Contribution

The lane turns regime labels, H4 regime raw features, OB-continuation decay snapshots, monthly decay report freshness, and account-history label status into K55-ready as-of feature/provenance/sample-eligibility fields.

## Safety Counters

- ai_calls: `0`
- canary_calls: `0`
- order_calls: `0`
- paid_data_calls: `0`
