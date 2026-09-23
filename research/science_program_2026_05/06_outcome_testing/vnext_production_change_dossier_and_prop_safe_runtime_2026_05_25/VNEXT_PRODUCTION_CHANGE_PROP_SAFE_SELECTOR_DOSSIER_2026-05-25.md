# vNext Production Change Stage05 Prop-Safe Selector Dossier

Created: 2026-05-25T08:03:44.923530Z

## Selector Contract

- Account model: redacted_account-style 100k challenge.
- Phase targets: Phase 1 8%, Phase 2 5%.
- External daily loss: 5% of initial balance, reset at 00:00 GMT+3.
- Malaysia conversion: 00:00 GMT+3 equals 05:00 Malaysia time.
- Daily floor: day_start_equity_or_balance_baseline - initial_balance * 0.05.
- Overall floor: initial_balance * 0.90, static, no trailing drawdown modeled.
- Internal 4% overlay is reported separately and never masquerades as the external rule.
- Runtime actions are limited to ALLOW, REDUCE_RISK, DEFER_UNTIL_RESET, or BLOCK.

## Replay Prop-Risk Baseline

- Prop metric rows: 24.
- Breach rows: 24; deterministic pass rows: 0.
- Trade count range: 29952 to 210975.
- Max trades/day: 931.
- Max loss streak: 54.
- Max drawdown proxy pct: 1645.264039.
- Pass proxy range: 0.002000 to 0.328000.

## R And Expectancy

- R/expectancy source: full replay robustness prop metric chunks; these are overlapping group metrics, not a single account curve.
- Robustness rows: 6954 across 45 chunks.
- Aggregate overlapping performance rows: 36127200.
- Aggregate overlapping total R: -447630.920723.
- Weighted overlapping expectancy R: -0.012390.
- Profit factor range: 0.000000 to 19.500029.
- Robustness max drawdown R: 52319.341030.
- Robustness max loss streak: 4866.

## Missed Winners And Avoided Losers

- Source rows: 253234 across 45 chunks.
- Classification counts: {"accepted_loser": 100166, "avoided_loser": 16815, "captured_winner": 75646, "missed_winner": 13073, "no_fill_pending": 37023, "same_bar_ambiguous": 5236, "timeout_mark_to_market": 5275}.

## Selector Behavior

- Scenario rows: 14.
- Selector action counts: {"ALLOW": 5, "BLOCK": 1, "DEFER_UNTIL_RESET": 1, "REDUCE_RISK": 7}.
- Selector would-action counts: {"ALLOW": 5, "BLOCK": 1, "DEFER_UNTIL_RESET": 1, "REDUCE_RISK": 7}.
- +2% intraday profit remaining daily cushion: 7000.00.
- Reset before-row next reset UTC: 2026-05-25T21:00:00+00:00.
- Reset before-row next reset Malaysia: 2026-05-26T05:00:00+08:00.

## Daily And Max-Loss Proximity

- Daily-loss proximity is reported per row as remaining_daily_cushion and projected_daily_cushion_after_full_risk.
- Max-loss proximity is reported per row as remaining_overall_cushion and projected_overall_cushion_after_full_risk.
- Intraday profit increases the current-equity cushion; losing days reduce it.

## Coverage

- Symbols: {"AUDJPY": 24, "AUDUSD": 23, "BTCUSD": 31, "CHFJPY": 23, "ETHUSD": 31, "EURGBP": 23, "EURJPY": 23, "EURUSD": 31, "GBPJPY": 106, "GBPUSD": 111, "GER40": 31, "JP225": 31, "NAS100": 105, "NZDUSD": 31, "SPX500": 31, "UK100": 31, "UKOIL_cash": 23, "US30_cash": 113, "USDCAD": 23, "USDCHF": 23, "USDJPY": 105, "USOIL_cash": 30, "XAGUSD": 108, "XAUUSD": 107}.
- Sessions: {"london_broad": 268, "ny_broad": 275, "off_kz_broad": 282, "tokyo_broad": 249}.
- Sides: {"LONG": 494, "SHORT": 499}.
- Frameworks: {"breaker_re_entry": 352, "fvg_fill": 318, "ob_retest": 360}.
- Source modes: {"lower_timeframe_ohlc": 19806320, "m15_ohlc_path": 10129360, "missing_source": 16957120, "ohlc_only_proxy": 10129360, "runtime_reference_not_path_truth": 20258720, "sierra_m1_proxy_path": 1803400, "tick_quote_path": 73600}.

## Activation Boundary

- Current config enables selector telemetry but keeps prop_safe_selector_apply_to_execution=false.
- No live trading, broker mutation, paid API, trailing drawdown assumption, or arbitrary no-trade collapse is introduced.
- If budget remains available, the selector preserves opportunity through ALLOW or REDUCE_RISK.
