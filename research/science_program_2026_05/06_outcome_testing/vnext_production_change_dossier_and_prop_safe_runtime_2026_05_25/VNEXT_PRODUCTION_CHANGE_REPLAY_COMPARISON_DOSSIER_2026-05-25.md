# Stage09 Forward-Only Replay Comparison

Route: `vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25`
Created: `2026-05-25T11:04:04.676227Z`

## Replay Universe

- Candidate rows replayed: 253,234.
- Replay comparison rows written: 253,234 across 11 shards.
- Runtime artifact rows loaded: 506,468.
- Decision inputs are as-of runtime trace fields; path/R/no-fill/outcome labels are scoring-only joins after the decision.

## New Production-Change Mechanical Metrics

- Selected: 10; skipped: 253,224; no-fill: 0.
- Total R: -4.999959196997; expectancy R: -0.4999959197; win rate: 0.2; PF: 0.375005100375.
- Pass proxy phase1/phase2: False / False.
- Max drawdown pct: 9.907647919809; max loss streak: 4.
- Missed winners: 104440; avoided losers: 135300; accepted losers: 8.
- Risk reductions: 2; deferred: 16; blocked: 216161.
- Daily cushion min: 1097.5; overall cushion min: 92.35208.

## redacted_account External-Budget-Only Scenario

- Selected: 10; performance rows: 10.
- Total R: -4.999959196997; expectancy R: -0.4999959197; pass proxy phase1/phase2: False / False.
- External-only risk reductions: 3; deferred: 6; blocked: 216171.
- External-only daily cushion min: 96.798357; overall cushion min: 194.298357.

## AI No-Paid-Call Simulation

- AI calls required: 39,323; AI calls avoided: 213,911.
- No-paid-call selected trades: 0; malformed-response paths: 0.

## Prop Budget Model

- redacted_account external daily loss is 5% of initial balance with 00:00 GMT+3 reset.
- Overall max loss floor is static at 90% of initial balance; no trailing drawdown is modeled.
- Existing `risk.max_daily_loss_pct=4.0` is treated only as a separately reported internal overlay when explicitly enabled.

## Coverage

- Symbols: {"AUDJPY": 1261, "AUDUSD": 1252, "BTCUSD": 4003, "CHFJPY": 1254, "ETHUSD": 3318, "EURGBP": 1173, "EURJPY": 1230, "EURUSD": 3999, "GBPJPY": 34838, "GBPUSD": 33592, "GER40": 4667, "JP225": 2811, "NAS100": 25659, "NZDUSD": 2505, "SPX500": 2020, "UK100": 4405, "UKOIL_cash": 1142, "US30_cash": 27854, "USDCAD": 1044, "USDCHF": 1262, "USDJPY": 35716, "USOIL_cash": 1013, "XAGUSD": 27242, "XAUUSD": 29974}.
- Sessions: {"london": 58842, "ny": 56920, "off_kz": 111762, "tokyo": 25710}.
- Sides: {"LONG": 129601, "SHORT": 123633}.
- Frameworks: {"breaker_re_entry": 69502, "fvg_fill": 106679, "ob_retest": 77053}.
- Source modes: {"bar_close_m15": 6183, "m1_path_aware": 215610, "m5_path_aware": 322, "tick_or_sierra_path_aware": 31119}.

## Boundaries

- No live trading, broker mutation, paid API/vendor call, source deletion, remote push, or activation flip was performed.