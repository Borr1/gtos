# G10 Execution, Entries, Exits, Risk, Portfolio Domain Synthesis

Generated: 2026-05-06T08:30:00Z
Lane: G10
Promotion verdict: NO_PROMOTION_VERDICT

## Scope

This lane converts execution and portfolio frictions into preregistered shadow research lanes. It does not recommend or change live order behavior, risk settings, safety gates, canaries, prompts, MT5 routing, or selector logic.

The controlling question is not "which execution policy should ship?" It is: which primitive execution/risk mechanisms are worth measuring with clean label separation before any future promotion discussion?

## Current GTOS Cross-Check

1. Internal pending limits are not native broker pending orders. `PendingLimitIntent` is described as an internal candle-polled intent in `src/components/execution.py:72`, and `open_trade()` sends a market `TRADE_ACTION_DEAL` request after trigger in `src/components/execution.py:480`. The lifecycle logger records explicit fields for `pending_order_mode`, `broker_pending_order_created`, `mt5_order_ticket`, and `native_pending_order_type` in `src/components/pending_limit_lifecycle_logger.py:18`.
2. Entry slippage telemetry exists but is sparse. `src/components/slippage_shadow_logger.py:1` describes observation-only slippage logging for successful market order fills; `research/operations/COST_SLIPPAGE_EXIT_ACCOUNTING_COVERAGE_2026-05-05.md` reports only 3 entry slippage rows and 0 close-side rows at that audit.
3. J46/J49 exit behavior is active and policy-specific, not a generic trailing stop. `src/components/j46_j49_policy.py:1` documents 0% partial, BE on TP1, 12 M15 bar time stop, TP1 3R, and higher target 6R. `src/components/execution.py:1306` makes TP1 BE-only under J46/J49 and `src/components/execution.py:1721` applies the 12-bar time stop.
4. Risk and portfolio gates already exist. `src/components/permissions.py:201` applies dormant-state, daily-loss, concurrent-cap, cross-instrument, connection, and spread checks. `src/components/concurrent_tracker.py:1` documents that pending limits are not counted toward filled-position concurrency. `src/components/cross_instrument_correlation_gate.py:1` documents the fleet-wide Pearson correlation gate.
5. Prop-firm constraints are live-sensitive source contracts, not validation evidence. The cached FTMO official page states the 2-step profit target, daily loss, maximum loss, and minimum trading-day rules in `raw/G10_execution_risk_sources_2026-05-06/ftmo_trading_objectives.html:2247`, `:2278`, `:2318`, and `:2338`. The cached redacted_account page has an official article timestamp `2026-04-08T03:13:46Z` in `raw/G10_execution_risk_sources_2026-05-06/redacted_account_daily_loss_limit.html:1`, but its article body is embedded in a minified Intercom payload and remains parser-blocked for validation.

## Mechanisms Worth Finding

The execution-risk lane should look for mechanisms where the current system can observe a clean signature without changing behavior:

- Internal-vs-native pending gap: a path touch can differ from an executable broker fill because the GTOS limit is candle-polled and later translated into a market order. The signature is a gap between setup/path touch, internal trigger state, tick availability, market order attempt, actual fill price, and broker deal record.
- Slippage/cost convexity: entry and close-side spread, slippage, commission, and swap can turn synthetic path-R into materially different broker actual-R. The signature is a monotone or state-conditional drag after joining entry and close deal evidence.
- Pre-fill delivery timing: the path between decision close and fill/cancel can identify no-retrace, adverse selection, or reversal-before-fill states. The signature requires exact decision timestamp, POI bounds, ordered lower-timeframe/tick path, and lifecycle state.
- J46/J49 successor exit timing: exit improvements must separate TP1/BE/time-stop/higher-target/close-cost effects instead of treating all exit changes as one policy. The signature is target-trial style arm attribution on broker-actual or rigorously separated synthetic labels.
- Risk-bank bounded re-entry: adding a re-entry can only be evaluated if worst-case aggregate realized plus open stop risk remains bounded after costs. The signature is a per-leg risk bank ledger that never crosses below -1R in the preregistered accounting.
- Prop-firm rule-distance: daily loss, max loss, minimum-day, concurrency, and correlation constraints are path-dependent. The signature is an observation-only rule-distance ledger, not a trading signal.
- Portfolio cluster exposure: filled-position caps and correlation gates can change opportunity selection. The signature is candidate-to-position transition loss or concentration under frozen group/correlation context.

## Counter-Evidence And Decay Review

- Same-dataset path scaling is discovery only. `RAW_OHLC_PATH_SCALING_V3_FULL_EXPLORATORY_REPLAY_2026-05-03.md` found large synthetic differences across variants, but explicitly marks DSR/PBO as not computable because variants were same-dataset discovery and not frozen on unseen data.
- Historical path reconstruction lacks decisive execution fields. `RAW_OHLC_PREFILL_DELIVERY_PATH_COVERAGE_2026-05-03.md` reports zero original POI bounds and zero broker lifecycle state for the historical setup rows, so it cannot prove broker-fill quality.
- Broker actual-R evidence is currently too sparse for execution-promotion claims. `LTO015_BROKER_ACTUAL_R_AUDIT_2026-05-05.md` permits actual-R claims on only 3 account-history realized rows.
- Exit event evidence is not yet present. `LTO021_EXIT_MANAGEMENT_NO_EVENT_STATUS_2026-05-05.md` documents no actual BE, partial, or time-in-trade exit events in the audited live candidate set.
- Prop-firm rules can change. Official pages were cached for source-contract context, but no source contract in this lane is validation safe.

## Killed Or Blocked Routes

- Treating `LIMIT_PLACED` as a native MT5 pending order is killed for this lane. It is an internal intent until broker-order evidence says otherwise.
- Mixing candidate/no-fill context rows with broker actual-R is killed. Label families remain separate.
- Promoting J46/J49 successors from synthetic path replay is blocked.
- Generic trailing-stop mining is blocked by the existing V3 risk-accounting note; only preregistered, bounded risk-bank or target-trial exit arms are admissible.
- Prop-firm rule pages are context contracts only. They cannot validate a trading edge.
- G9 neighbor synthesis was not committed at this pass, so no G9-derived cross-domain row was created.

## Neighbor Pass

G1 contributes the statistical gate: every execution/risk experiment must preserve as-of source capture, label separation, DSR/PBO policy, and effective-N/concentration checks. G6 contributes the market-structure side: OB continuation and no-retrace mechanisms are not actionable until fill timing and friction are measured. G9 is absent from committed lane outputs and remains a blocker.

## Output Map

- Mechanisms: `G10_MECHANISM_ROWS_2026-05-06.json`
- Hypotheses: `G10_HYPOTHESIS_ROWS_2026-05-06.json`
- Preregs: `G10_EXPERIMENT_PREREG_SPECS_2026-05-06.json`
- Source contracts: `G10_SOURCE_CONTRACT_ROWS_2026-05-06.json`
- Context and ambiguity ledgers: `G10_CONTEXT_LEDGER_2026-05-06.md`, `G10_AMBIGUITY_LEDGER_2026-05-06.md`

Final lane verdict: NO_PROMOTION_VERDICT.
