# vNext Production-Change Activation Dossier

Route: `vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25`
Audit created: `2026-05-25T11:10:34.353653Z`

## Runtime Behavior Changed

- Stage05 redacted_account prop-safe selector implements 5% daily floor/cushion, static 10% overall floor, GMT+3 reset, and separate internal overlay reporting.
- Stage06 LTF path/no-fill execution context adds activation-gated pending/no-fill/monitor decisions.
- Stage07 AI policy constrains AI to source-bound mechanical route validation and records no-paid-call decisions.
- Stage08 AI supervisor monitors schema/route health and can disable AI narrowing, but cannot place orders or rewrite trade parameters.

## Replay Intelligence Consumed

- Stage09 replay rows: 253,234 over 253,234 candidates.
- Replay basis: `stage03_verified_asof_runtime_trace_rehydration`.
- Markets/symbols: {"AUDJPY": 1261, "AUDUSD": 1252, "BTCUSD": 4003, "CHFJPY": 1254, "ETHUSD": 3318, "EURGBP": 1173, "EURJPY": 1230, "EURUSD": 3999, "GBPJPY": 34838, "GBPUSD": 33592, "GER40": 4667, "JP225": 2811, "NAS100": 25659, "NZDUSD": 2505, "SPX500": 2020, "UK100": 4405, "UKOIL_cash": 1142, "US30_cash": 27854, "USDCAD": 1044, "USDCHF": 1262, "USDJPY": 35716, "USOIL_cash": 1013, "XAGUSD": 27242, "XAUUSD": 29974}.
- Sessions: {"london": 58842, "ny": 56920, "off_kz": 111762, "tokyo": 25710}.
- Sides: {"LONG": 129601, "SHORT": 123633}.
- Frameworks: {"breaker_re_entry": 69502, "fvg_fill": 106679, "ob_retest": 77053}.

## Replay Impact

- Mechanical scenario selected 10 rows, performance rows 10, total R -4.999959196997, expectancy -0.4999959197, WR 0.2, PF 0.375005100375.
- Pass proxy phase1/phase2: False / False; max DD 9.907647919809%; max loss streak 4.
- Missed winners 104,440; avoided losers 135,300; risk reductions 2; deferred 16; blocked 216,161.
- Daily-loss proximity min cushion 1097.5; max-loss proximity min cushion 92.35208.
- External redacted_account-only scenario selected 10, total R -4.999959196997, risk reductions 3, deferred 6, blocked 216,171.
- AI no-paid-call simulation selected 0; AI calls required 39,323; AI calls avoided 213,911.

## Activation Status

- Broker-facing activation remains owner-gated. No live trading, broker mutation, paid API call, remote push, source deletion, or activation flip occurred.
- Current/default execution gates remain non-broker-mutating: `gtos_vnext_runtime.apply_to_execution=false`, `prop_safe_selector_apply_to_execution=false`, `ltf_path_execution_apply_to_execution=false`, `ai_policy_apply_to_ai_call=false`.
- `ai_supervisor.apply_runtime_overrides=true` is fail-safe only: it disables AI narrowing effects when health checks fail.

## Owner Review Items

- Decide whether to keep the explicit 4% GTOS internal daily overlay applying to selector budget; it is measured separately from redacted_account external 5% daily loss.
- Decide whether any demo/shadow run should activate vNext execution, prop-safe selector, LTF path execution, or AI policy gates.
- Paid AI calls remain separated from code readiness; the no-paid-call replay shows required/avoided call counts only.

## Completion Audit

- Instruction coverage ok: True.
- Remaining executable actions before owner activation: [].