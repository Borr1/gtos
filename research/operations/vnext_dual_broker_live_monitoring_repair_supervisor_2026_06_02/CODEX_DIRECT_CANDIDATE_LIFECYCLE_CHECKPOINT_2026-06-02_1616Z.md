# Codex Direct Candidate Lifecycle Checkpoint - 2026-06-02 16:16Z

Route: `vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02`
Evidence class: `DUAL_BROKER_VPS_LIVE_RUNTIME_DATA_BROKER_PROCESS_REPAIR_SUPERVISION`
Runtime effect boundary: read-only process, disk, MT5 account/position/order, candidate, intent, follower-state inspection. No manual broker order, position, deal, or account mutation.

## Current Runtime Shape

- `LIVE_STATE` regenerated at `2026-06-02 16:06:31 UTC`; inspected HEAD before this checkpoint was `7c76a2b58 runtime: checkpoint dual broker live status`.
- Process command-line pass found 24 redacted_account `run_agent.py` workers, 0 FTMO `run_agent.py` workers, 1 FTMO `dual_broker_execution_follower.py`, 1 trade-record projector, 24 redacted_account tick-capture workers, 1 redacted_account M1 capture worker, 1 redacted_account notification worker, and 2 MT5 terminals.
- Free physical memory at the post-compaction checkpoint was approximately 2.08 GB of 8.0 GB.
- `rg` exists at `host-local\AppData\Roaming\npm\rg.cmd`; the shim requires avoiding raw `|` regex quoting in PowerShell commands.

## Fresh Read-Only MT5 Snapshot

Fresh route-owned read-only probe: `DUAL_MT5_TERMINAL_ACCOUNT_PROBE.json`, captured `2026-06-02T16:13:23Z`.

- redacted_account account identity matched profile. Positions: 12. Orders: 0. Equity: `101421.12`. Positive configured-symbol ticks without mass select: 24/24.
- FTMO account identity matched profile. Positions: 9. Orders: 0. Equity: `98545.34`. Positive configured-symbol ticks without mass select: 19/24, absent ticks 5/24 without mass select.
- FTMO target state reconciliation after the probe: 9 persisted active trades, 9 broker positions, 0 missing state positions, 0 extra broker positions, and 0 material volume/SL mismatches.

## Latest Source Intents And Follower Outcomes

The canonical intent log has no projected intents after the ETHUSD row at `2026-06-02T15:46:19.168086+00:00`.

- US30 source record: `knowledge_base\redacted_account_live_bee34003\trade_records\US30_cash\2026-06-02_ny_1530_broadorigin_1ac119b7b5f762a511c5922d.json`.
  - redacted_account filled as a valid vNext source order. FTMO follower consumed the intent but rejected it by target risk budget: `target_account_drawdown_budget_blocked_by:internal_daily_drawdown_overlay`, available new risk about `2.37`, requested risk about `244.91`.
- ETHUSD source record: `knowledge_base\redacted_account_live_bee34003\trade_records\ETHUSD\2026-06-02_off_configured_session_1545_broadorigin_3a82cefc242aee6274c8f027.json`.
  - redacted_account filled as a valid vNext source order. FTMO follower consumed the intent but rejected it by target risk budget: `target_account_drawdown_budget_blocked_by:internal_daily_drawdown_overlay`, available new risk about `2.02`, requested risk about `122.46`.

Interpretation: current US30/ETH FTMO non-follows are not namespace loss, target-state loss, stale `max_concurrent`, symbol alias failure, or projector loss. They are target-account aggregate drawdown-budget blocks after existing FTMO open SL exposure plus buffer.

## 16:00 Candidate/Rejection Inspection

Four redacted_account trade-record JSON files appeared after the 15:57Z checkpoint, all directly inspected:

- `JP225\2026-06-02_moonshot_h15_16_1600_broadorigin_999ed9410fa1b18b07d1d86f.json`
  - Outcome: `SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC`.
  - AI decision: `CANDIDATE`, short, `origin_structural_distance_extreme`.
  - Gate3 passed, old PA and old L2 both false.
  - Dynamic policy selected: `momentum_exhaustion`; not applied.
  - Direct refusal reasons: spread-R `0.3479532163742542` exceeded max `0.2`, outside repo-configured kill zone, no verified selected-cell risk due session/hour key mismatch, and framework/scope not activated for this exact selector path.
  - No source order path reached and no canonical intent was projected.
- `NAS100\2026-06-02_ny_1600_broadorigin_a6aaaa5dbf2406a1f1b0a6ba.json`
  - Outcome: `REJECTED_GATE3_CIRCUIT_BREAKER`.
  - AI decision: `CANDIDATE`, short, `origin_structural_distance_extreme`.
  - Dynamic policy selected and applied: `momentum_exhaustion`; selected-cell risk verified at `0.25`, cell `STAGE13-FN-RISK-CELL-000428`; candidate quality allowed, spread-R `0.0748958934921341` below max `0.2`.
  - Gate3 rejected because redacted_account already had one NDX100/NAS100 live position, ticket `242629619`; current vNext contract rejects same-symbol stacking until ticket-bound multi-position lifecycle support is explicit.
  - No source order path reached and no canonical intent was projected.
- `GBPJPY\2026-06-02_moonshot_h15_16_1600_broadorigin_9e80ab32937efa33faa7ece9.json`
  - Outcome: `SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC`.
  - AI decision: `CANDIDATE`, short, `origin_liquidity_sweep_reclaim`.
  - Gate3 passed, old PA and old L2 both false.
  - Dynamic policy selected: `partial_be_runner`; not applied.
  - Direct refusal reasons: spread-R `0.5209302325577326` exceeded max `0.2` and outside repo-configured kill zone. Selected-cell risk was verified at `0.25`, cell `STAGE13-FN-RISK-CELL-000663`.
  - No source order path reached and no canonical intent was projected.
- `GBPJPY\2026-06-02_moonshot_h15_16_1600_broadorigin_1e19890c8be671e2607eb6ad.json`
  - Outcome: `SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC`.
  - AI decision: `CANDIDATE`, short, `origin_structural_distance_extreme`.
  - Gate3 passed, old PA and old L2 both false.
  - Dynamic policy selected: `momentum_exhaustion`; not applied.
  - Direct refusal reasons: spread-R `0.5209302325577326` exceeded max `0.2` and outside repo-configured kill zone. Selected-cell risk was verified at `0.25`, cell `STAGE13-FN-RISK-CELL-000697`.
  - No source order path reached and no canonical intent was projected.

Interpretation: no active selector or candidate-flow defect is proven by these four rows. The rejected/held records are explained by configured spread, kill-zone, selected-cell, and same-symbol lifecycle gates.

## FTMO Broker-Local Management Proof

- Follower action log: `pipeline_state\operator_profile\dual_broker_execution_follower_actions.jsonl`.
- The latest post-15:57 management action is `active_trade_management`, symbol `JP225`, status `tp1_partial_vnext_partial_be_runner`, at `2026-06-02T15:57:12.305044+00:00`.
- FTMO broker position `155129522` is now `JP225.cash`, remaining volume `9.84`, entry `67169.5`, SL `67169.5`, TP `67767.3`, comment `TP1_vnext_partia`.
- Persisted target state for ticket `155129522` has initial volume `19.69`, current volume `9.84`, `tp1_hit=true`, and `sl_at_breakeven=true`.
- The event sequence contains `SL_TO_BREAKEVEN_MODIFY_SUCCESS` followed by the partial-close event. The partial-close event embeds a pre-BE `sl_at_breakeven` metadata snapshot from close-side slippage capture, while the standalone BE event, persisted target state, and broker SL are correct. This is an observability ordering quirk, not an execution defect.

## Architecture Status

Current best-fit architecture remains: one full redacted_account vNext brain plus one lightweight FTMO execution follower. The follower is not a passive notification copier; it:

- consumes canonical source intents only after redacted_account source records reach the execution/fill path;
- evaluates FTMO account-specific risk budget before entry;
- maps to FTMO broker symbols and live FTMO ticks;
- restores target `TradeState` on startup only for target symbols that have positions or pending intents;
- runs `ExecutionEngine.check_and_manage_trade({})` against FTMO-local broker state for active FTMO positions;
- persists target trade state under `pipeline_state\operator_profile\dual_broker_target_trade_state.json`.

This gives the desired memory-light shape without limiting the main redacted_account system or running a second full 24-worker FTMO selector/orchestrator fleet. A future explicit `BrokerLocalLifecycleManager` split could improve naming/observability, but current evidence does not justify widening memory footprint or restarting the full live system now.

## Verification

- `python -m py_compile research\operations\vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02\verify_dual_supervisor_checkpoint.py` passed.
- `python research\operations\vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02\verify_dual_supervisor_checkpoint.py` passed with `failure_count=0`.
- `python -m pytest tests\test_dual_broker_execution_follower.py -q --basetemp=.pytest-tmp-dual-follower-verifier -o cache_dir=.pytest-tmp-dual-follower-verifier-cache` passed: `20 passed`.
- The verifier had one stale contract marker, `market_intent_no_target_order`. The live follower and focused tests already use the stronger split contract: `market_intent_deferred_no_target_order`, `market_intent_expired_no_target_order`, and `market_intent_target_position_detected_before_retry`. The route verifier was updated to assert those current markers and their tests; no live follower behavior was changed.

## Remaining Work

- Continue live supervision for any new candidate, source fill, follower risk block, target execution, partial/BE, modify, close, or stale-state event after this checkpoint.
- If another partial/BE event occurs and audit clarity becomes material, consider a narrow telemetry-only patch to add explicit post-BE fields to the partial-close event metadata; no broker behavior repair is currently required.
- Commit and push this scoped checkpoint plus route-owned probe/ledger updates, excluding broad unrelated runtime dirt.
