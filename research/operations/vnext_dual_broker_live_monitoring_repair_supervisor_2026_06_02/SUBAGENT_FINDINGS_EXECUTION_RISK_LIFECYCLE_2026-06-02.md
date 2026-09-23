# Subagent Findings - Execution, Risk, Trade Lifecycle

Agent: `019e89f1-4231-7852-b303-d56e7319e58b`

Scope: execution/risk/order sizing/BE/partial/exits/lifecycle.

Status: read-only audit completed. The agent reported no broker/order/position/deal/file mutation and no generated Python audit scripts as proof.

## Clean Proofs Reported

- Live selected-cell entry sizing uses broker `order_calc_profit`, not tick-value fallback.
  - Code requires verified broker geometry for vNext selected-cell entries at `src/components/execution.py:2370`.
  - Code aborts if broker cash-risk is unavailable at `src/components/execution.py:2400`.
  - Code disables fallback when broker calc is required at `src/components/execution.py:6109`.
  - Current redacted_account BTCUSD and US30_cash source records show `broker_order_calc_profit` and `BROKER_ORDER_CALC_PROFIT_VERIFIED`.
  - Current FTMO target BTCUSD/US30_cash rows are also broker-verified.
  - Direct log search found no current selected-cell rows using `tick_value_legacy_fallback`, `contract_size_legacy_fallback`, or `intended_risk_budget_unverified`.
- Partial/BE residual handling is not duplicating live trades.
  - Code detects already-reduced broker volume before second TP1 partial at `src/components/execution.py:4893`.
  - Code appends `TP1_PARTIAL_ALREADY_REFLECTED_BY_BROKER` at `src/components/execution.py:4927`.
  - Current target USDJPY and JP225 rows show one residual restore marker, `tp1_hit: true`, `sl_at_breakeven: true`, reduced volume.
  - Current code treats already-matched no-change SLTP as benign at `src/components/execution.py:6564`.
- Failed-intent replay is bounded.
  - GER40 failed reprocess was skipped because source record was terminal/outside live recovery window at FTMO follower action row 264.
  - Similar terminal skips exist for older BTCUSD/EURJPY/USDCAD/XAGUSD/CHFJPY rows.
  - No duplicate FTMO GER40 trade was produced.

## Findings

1. Six current FTMO target active trades still lacked cash-risk provenance.
   - Evidence:
     - `pipeline_state/operator_profile/dual_broker_target_trade_state.json` updated around `2026-06-02T20:25:13Z`;
     - blank `cash_risk_amount_source/status`, `broker_lot_sizing_diagnostic: null`, and `broker_cash_risk_per_lot: 0.0` for:
       - UK100;
       - USDJPY;
       - GBPJPY;
       - USDCAD;
       - JP225;
       - ETHUSD.
   - Reported root cause:
     - restore/backfill code existed in current file after main-session patch, but the running follower had not reloaded and current persisted rows remained unbackfilled.
   - Required repair:
     - reload follower and verify startup/every persist recomputes active-position stop risk with target broker `order_calc_profit`;
     - persist source/status/diagnostic;
     - block target new-risk admission while any active target trade has unverified cash-risk provenance.

2. Current-position aggregate risk can silently fall back to tick metadata.
   - Evidence:
     - source risk accounting tries broker `order_calc_profit`, then falls back to profile tick metadata at `src/components/orchestrator.py:3929`;
     - FTMO follower has the same fallback at `scripts/dual_broker_execution_follower.py:928`;
     - follower discarded the source at `scripts/dual_broker_execution_follower.py:976`;
     - selector copies missing/fallback counts into exposure at `src/components/gtos_vnext_runtime.py:15353` but does not block on them before ALLOW/REDUCE/BLOCK.
   - Impact:
     - if broker calc fails for open GER30/GER40, JP225, UK100, US30, NAS100, oil, or other CFDs, aggregate drawdown can admit a new selected-cell order with unverified open risk.
   - Required repair:
     - live aggregate risk must require broker `order_calc_profit` for every open position;
     - include `profit_model` per position;
     - block/defer on fallback or missing valuation;
     - add forced-order-calc-failure tests for GER30/GER40 and index CFDs.

3. Source trade records keep `entry_deal_ticket: null` after broker-history reconciliation.
   - Evidence:
     - current redacted_account BTCUSD source record has `entry_deal_ticket: null`, while `shadow_logs/slippage.jsonl` row 150 captured deal `226473277`;
     - current redacted_account US30_cash source record has `entry_deal_ticket: null`, while `shadow_logs/slippage.jsonl` row 153 captured deal `226474407`.
   - Root cause:
     - `TradeState.entry_deal_ticket` is set from `result.deal` only at `src/components/execution.py:2675`;
     - broker-history deal is passed only to slippage at `src/components/execution.py:2807`.
   - Required repair:
     - backfill `entry_deal_ticket` from reconciled history into `TradeState` and trade record.

4. Active target rows lose `intent_id`.
   - Evidence:
     - all eight active target rows had `intent_id: null`, including BTCUSD and US30_cash;
     - FTMO follower action rows 265/267 had concrete intent IDs.
   - Current main-session status:
     - commit `5652c67e1` repairs active ticket-to-intent binding and action-log recovery, pending reload/verification.
   - Required repair:
     - reload follower and verify target state writes non-null intent IDs immediately after open/fill and after restart restore.

5. BE/partial/trailing shadow logs still use mutated BE stop as R denominator.
   - Evidence:
     - `shadow_logs/partial_close_shadow_log.jsonl` UKOIL rows at lines 6 and 7 show `sl_distance: 1.4210854715202004e-14`, `remaining_r: 72761281479704.0`, duplicate within one second;
     - `shadow_logs/trailing_stop_v1_shadow_log.jsonl` line 14 has the same impossible denominator.
   - Impact:
     - shadow-only, not broker-mutating, but poisons lifecycle research.
   - Required repair:
     - use immutable entry stop distance;
     - reject near-zero denominators;
     - dedupe by trade id/ticket/trigger timestamp.

6. Closed GER40/GER30 and UKOIL records are not self-sufficient.
   - Evidence:
     - redacted_account profile maps `GER40` to broker `GER30` at `config/profiles/redacted_account.yaml:454`;
     - FTMO maps `GER40.cash` at `config/profiles/operator_profile.yaml:518`;
     - GER40 source record has `cash_risk_amount` but no source/status fields and is closed;
     - UKOIL source record is closed but has blank source/status and null diagnostic.
   - Impact:
     - no current open risk remains, but durable audit/replay proof is incomplete.
   - Required repair:
     - one-time record repair ledger using broker-history evidence;
     - schema tests forbidding persisted selected-cell records without cash-risk source/status.

7. Missing-position close confirmation can stick an active trade in monitoring.
   - Evidence:
     - vNext close confirmation path returns `NO_CLOSE_DEAL_FOUND` at `src/components/execution.py:1719`.
     - Agent found no current active raw `NO_CLOSE_DEAL_FOUND` incident.
   - Required repair:
     - after bounded broker-history attempts, persist explicit unresolved-terminal state;
     - block same-symbol reopening until reconciled.
