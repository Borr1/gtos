# Subagent Findings - FTMO Follower, Profile, Symbol Mapping, Replay, Target Management

Agent: `019e89f1-43be-7440-8220-49f16a2bc98d`

Scope: FTMO follower/profile/symbol mapping/replay/target management.

Status: read-only audit completed. The agent reported no broker mutation and no generated Python audit scripts as proof.

## Clean Proofs Reported

- FTMO was lightweight follower-only:
  - 24 redacted_account `run_agent.py --profile redacted_account` workers;
  - 0 FTMO `run_agent.py`;
  - 1 `dual_broker_execution_follower.py`;
  - 1 projector;
  - terminals at `C:\Program Files\MetaTrader 5\terminal64.exe` and `C:\MT5\FTMO\terminal64.exe /portable`.
- FTMO account/profile identity was clean:
  - follower action log row 258 `account_check.status=passed`;
  - company `FTMO Global Markets Ltd`;
  - server `FTMO-Server3`;
  - login hash prefix `310fcf...`;
  - terminal/data path `C:\MT5\FTMO`.
- FTMO profile had repaired no-count-cap policy:
  - `config/profiles/operator_profile.yaml:49` `max_concurrent: null`;
  - line 50 disables count caps for aggregate drawdown budget.
- Symbol mapping was clean for all 24 active symbols:
  - examples: `GER40 -> GER40.cash`, `NAS100 -> US100.cash`, `US30_cash -> US30.cash`;
  - no `skip_unmapped_symbol`, namespace-skip, unsupported-intent, pending-limit-staging, or processing-error rows in FTMO follower action log.
- Current post-repair copying worked for fresh examples:
  - canonical BTCUSD row 30 copied at action row 265 with `BROKER_ORDER_CALC_PROFIT_VERIFIED`;
  - canonical US30_cash row 31 copied at action row 267 with `BROKER_ORDER_CALC_PROFIT_VERIFIED`.

## Findings

1. FTMO had 31 canonical intents but only 21 successful target copies.
   - Latest raw state by intent:
     - 21 `market_intent_processed` with non-null result;
     - 3 `risk_guard_rejected`;
     - 6 `market_intent_reprocess_failed_retry_skipped_source_not_open`;
     - 1 `market_intent_skipped_outside_live_recovery_window`.
   - Defect:
     - checkpoint `processed_intent_count: 31` is not a success count.
   - Required repair:
     - split checkpoint/health into copied, risk-blocked, missed-terminal, stale-skipped, retryable-failed.

2. One NZDUSD copy was missed by startup replay semantics.
   - Evidence:
     - canonical row 1 projected at `2026-06-02T08:01:47Z`;
     - follower started later at action rows 1-4 with `replay_existing:false` and `offset:2034`;
     - it only handled the intent at row 241 as `market_intent_skipped_outside_live_recovery_window` at `18:30:35Z`;
     - source record later showed terminal broker close at `12:00:24Z`.
   - Root cause:
     - first live startup began from EOF instead of replaying pre-existing canonical rows.
   - Required repair:
     - first bridge start must replay existing rows or prove checkpoint lineage;
     - add startup test with one pre-existing canonical intent.

3. One stale FTMO max-concurrent rejection remains an unrecovered missed copy.
   - Evidence:
     - canonical BTCUSD row 5 rejected at action row 22, `2026-06-02T12:16:17Z`;
     - reason `target_max_concurrent_reached:2>=2`;
     - current FTMO profile lines 49-51 prove the count cap is stale;
     - current code marks `risk_guard_rejected` terminal and not reprocessable via `scripts/dual_broker_execution_follower.py:80` and `:99`.
   - Required repair:
     - durable missed-intent ledger entry;
     - regression test that future FTMO rows cannot emit `target_max_concurrent_reached`.

4. No-target-order failures are real missed copies.
   - Evidence classes:
     - BTCUSD row 6;
     - EURJPY rows 32-33/260;
     - USDCAD rows 37-38/261;
     - XAGUSD rows 42-43/262;
     - CHFJPY rows 65-123/263.
   - CHFJPY detail:
     - retried for 120 seconds;
     - expired at row 122;
     - wrote `market_intent_processed` with `result:null` at row 123.
   - Required repair:
     - log failed processed rows as explicit failure outcomes;
     - include MT5 retcode/order-send context;
     - add replay tests for no-target-order while source open versus terminal.

5. Legacy event names leak into recovery.
   - Evidence:
     - action rows 32, 37, 42 use `market_intent_no_target_order`;
     - current terminal/reprocess sets do not include that event;
     - current code knows `market_intent_expired_no_target_order` and processed-null retry logic.
   - Required repair:
     - legacy event migration/classification;
     - verifier for unknown action-log event names.

6. GER40 was correctly fail-closed but exposes an upstream context defect.
   - Evidence:
     - canonical row 28 rejected at action row 220 with `selected_cell_unresolved:condition_challenger_cell_join_missing_for_broader_origin_allowlist_entry`;
     - source-terminal skipped at row 264.
   - Required repair:
     - repair selected-cell/condition-challenger context emission for GER40 broader-origin rows;
     - add 24-symbol intent-context validation fixtures.

7. Two risk blocks were active and intended, not defects.
   - Evidence:
     - US30_cash row 203 and ETHUSD row 205 blocked on `target_account_drawdown_budget_blocked_by:internal_daily_drawdown_overlay`;
     - only about `$2` available against a `$244+` minimum reduced risk.
   - Handling:
     - keep as risk-policy proof, not missed-copy bugs.

8. FTMO drawdown budget is symbol-map scoped, not account-wide.
   - Evidence:
     - `_history_realized_pnl_since_reset` loops `symbol_map.values()` and calls history per symbol at `scripts/dual_broker_execution_follower.py:841`;
     - `_target_open_position_sl_risk_amount` loops mapped symbols only at `scripts/dual_broker_execution_follower.py:991`.
   - Impact:
     - manual/off-universe FTMO deals, fees, or positions can be missed.
   - Required repair:
     - query account-wide history/positions;
     - include off-map exposure;
     - fail closed on off-map missing SL.

9. Target-state store was not self-sufficient.
   - Evidence:
     - active target store mapped 8 tickets but top-level `intent_id` was null for every row, including BTCUSD ticket `155209892` and US30_cash ticket `155211378`;
     - action rows 265/267 had correct canonical IDs.
   - Current main-session status:
     - commit `5652c67e1` repairs ticket-to-intent persistence and action-log recovery, but reload/verification was pending when the user asked to hold.
   - Required repair:
     - reload follower and verify target-state intent IDs are persisted;
     - keep restart test requiring non-null intent IDs for active copied tickets.

10. Six active FTMO tickets still lacked cash-risk provenance in target state.
    - Evidence:
      - tickets `155108218`, `155108230`, `155129060`, `155129494`, `155129522`, `155207767`;
      - `broker_lot_sizing_diagnostic:null`;
      - `cash_risk_amount_status:""`;
      - newer BTCUSD/US30_cash tickets verified.
    - Current main-session status:
      - commit `5652c67e1` annotates restored blank cash-risk provenance from current broker position/SL, using `order_calc_profit` when available.
    - Required repair:
      - reload follower and verify blank statuses are replaced with explicit verified/fallback/unresolved legacy status;
      - verifier must reject empty status for active target rows.

11. FTMO notification namespace was inactive.
    - Evidence:
      - profile defines `pipeline_state/operator_profile/notification_queue.jsonl`;
      - file missing;
      - process census had `ftmo_notification_worker: 0`;
      - follower start row 258 had `notifications_enabled:false`;
      - follower suppresses notifications unless `--enable-notifications` is passed at `scripts/dual_broker_execution_follower.py:1237`.
    - Current user preference:
      - duplicate FTMO notifications are low priority because both accounts generally do same trades.
    - Required handling:
      - either explicitly document secondary suppression as intentional or start namespaced worker and enable follower notifications;
      - archive stale unscoped `pipeline_state\notification_queue.jsonl`.

12. Follower launch had duplicate replay flag.
    - Evidence:
      - live command line included `--replay-existing --replay-existing`;
      - root cause in `scripts/watchdog.ps1:724` and `scripts/watchdog.ps1:760`.
    - Required repair:
      - build replay args once;
      - test command line contains one replay flag.

13. Intent validator does not require risk fields.
    - Evidence:
      - all 31 canonical rows had `effective_risk_pct_cap` and target recompute instruction today;
      - `validate_intent` only requires source/trade fields at `src/components/dual_broker_intent_bus.py:842`;
      - `target_risk_cap_pct` can fall back to configured FTMO profile risk at `scripts/dual_broker_execution_follower.py:636`.
    - Required repair:
      - fail closed if `risk.effective_risk_pct_cap` or risk instruction is absent.

14. Execution engine remains one-active-trade-per-symbol.
    - Evidence:
      - `reconcile_on_startup` loops positions but assigns single `self.active_trade` at `src/components/execution.py:6833`.
      - Current target state had no duplicate active symbols.
    - Impact:
      - multiple FTMO same-symbol positions would drop management state for all but one.
    - Required repair:
      - ticket-keyed active trade management or explicit one-position-per-symbol enforcement.

15. Stale/noise artifacts remain.
    - Evidence:
      - `config/agent_config.yaml` still has old FTMO/XAUUSD and challenge comments at lines 47, 3214-3217, 3332, 3717;
      - old FTMO follower error log shows non-portable terminal data-path mismatch, while current follower account checks pass.
    - Required handling:
      - archive or relabel stale/noise artifacts to avoid operator confusion.
