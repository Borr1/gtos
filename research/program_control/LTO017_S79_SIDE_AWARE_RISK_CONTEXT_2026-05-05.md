# LTO-017 S79 / Side-Aware Risk Context - 2026-05-05

**Schema:** `lto017_s79_side_aware_risk_context_report_v1`
**Generated:** `2026-06-01T23:36:58.695124+00:00`
**Status:** `OK_S79_SIDE_AWARE_RISK_CONTEXT_DOCUMENTED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Counts

- Rows computed: `543`
- Status rows available: `2208`
- Status rows appended this run: `543`
- Candidate context rows: `538`
- Filled context rows: `5`
- Filled account-history joined: `5`
- Actual-R claim allowed rows: `5`
- Action required: `0`

## Status Breakdown

- Status counts: `{'S79_SIDE_AWARE_CONTEXT_DOCUMENTED': 538, 'S79_SIDE_AWARE_FILLED_ACCOUNT_HISTORY_JOINED': 5}`
- Row type counts: `{'candidate_risk_context': 538, 'filled_risk_context': 5}`
- Symbol counts: `{'AUDJPY': 8, 'BTCUSD': 24, 'CHFJPY': 21, 'ETHUSD': 23, 'EURGBP': 27, 'EURJPY': 19, 'GBPJPY': 52, 'GBPUSD': 57, 'JP225': 20, 'NAS100': 77, 'NZDUSD': 3, 'UK100': 1, 'UKOIL_cash': 26, 'US30_cash': 40, 'USDCAD': 25, 'USDJPY': 4, 'USOIL_cash': 24, 'XAGUSD': 61, 'XAUUSD': 31}`
- ML label eligibility counts: `{'RISK_CONTEXT_ONLY_NO_ACCOUNT_HISTORY_LABEL': 538, 'ACCOUNT_HISTORY_LABEL_WITH_RISK_CONTEXT': 5}`
- Action-required codes: `{}`
- Documented limitations: `{}`

## Boundary

This report snapshots shipped S79/side-aware risk context. It does not change risk, position sizing, execution, prompts, or safety gates.

## ML Goal Contribution

The lane makes S79 and side-aware state available as ML risk-policy context and sample-weight metadata with explicit account-history label status.

## Safety Counters

- ai_calls: `0`
- canary_calls: `0`
- order_calls: `0`
- paid_data_calls: `0`
