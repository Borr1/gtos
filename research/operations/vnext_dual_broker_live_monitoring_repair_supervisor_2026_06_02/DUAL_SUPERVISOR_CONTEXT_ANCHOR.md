# Dual-Broker Live Monitoring Repair Supervisor Context Anchor

Route id: `vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02`
Generated: `2026-06-02T07:11:48.997599Z`
HEAD: `fd1592516964746f7a7f19370a56776bc0a350b0`
Branch: `vps-prod-live-sync-2026-06-02`

## Active Objective

Follow the controlling prompt at
`research/science_program_2026_05/04_goal_prompts/VNEXT_DUAL_BROKER_LIVE_MONITORING_REPAIR_SUPERVISOR_GOAL_PROMPT_2026-06-02.md`.

## Durable Hardening Reminder

After any compaction, restart, interruption, or uncertainty, regenerate
`LIVE_STATE`, treat pre-restart process state as stale, inspect current
process/memory/MT5 evidence from disk, and continue repair-first from current
code and runtime artifacts. The owner explicitly wants maximum practical
reasoning and best-correct solutions inside the safety boundaries, not shallow
speed or memory-driven passivity. Memory is a checkpoint and process-footprint
control, not a reason to under-run the approved lightweight dual-broker
architecture. Keep the redacted_account full brain unrestricted, keep FTMO lightweight
unless an explicitly implemented architecture change requires more, avoid
duplicate legacy/unscoped processes, and never manually mutate broker
orders/positions/deals.

## Current Checkpoint

The first verified defect class is notification queue namespace collision risk:
the prior default queue path and worker lock could mix redacted_account and FTMO
notifications or let one account worker satisfy the other account's watchdog
liveness check.

Repair applied in this checkpoint:
- profile/env-derived queue paths in `src/utils/notification_queue.py`;
- orchestrator profile hook before lazy queue singleton creation;
- account-scoped `GTOS_NOTIFICATION_QUEUE_PATH` defaults in `start_all.bat` and `scripts/watchdog.ps1`;
- namespace-scoped worker locks `.notification_queue_worker_<namespace>.lock`;
- dead-zone audit queue/lock path parameters;
- focused tests and watchdog verifier substrings.

## Verification

- `python -m py_compile src\utils\notification_queue.py src\components\orchestrator.py src\research_infra\notification_queue_dead_zone_status.py scripts\audit_notification_queue_dead_zone.py scripts\watchdog_e2e_verify.py`
- PowerShell parser check for `scripts/watchdog.ps1`
- `python -m pytest tests/test_notification_queue.py tests/test_notifications.py tests/test_start_all_runtime_contract.py tests/test_watchdog_e2e_verify.py -q --basetemp=.pytest-tmp-dual-notification-repair -o cache_dir=.pytest-tmp-dual-notification-repair-cache`
  - Result: `107 passed, 1 skipped`

## Continuation

This is a checkpoint, not terminal completion. Remaining work includes current
MT5/process proof, scoped process reload, FTMO order-capable activation after
verification, direct candidate/lifecycle inspection, and persistent dual-broker
supervision until CEO stop or tested persistent supervisor replacement.

## Latest Repair Checkpoint

Recorded 2026-06-02 after the FTMO BTC miss investigation:
- stale FTMO `max_concurrent` trade-count authority was removed from the dual-broker follower path;
- FTMO follower now evaluates account-specific aggregate drawdown budget before copying an intent: current equity, reconstructed day-start balance at 00:00 CE(S)T, open position SL exposure, pending risk, 5% daily loss, 10% overall loss, 4% internal daily overlay, and 1% overall cushion;
- `operator_profile` and `ftmo` profiles set `max_concurrent: null`, `max_concurrent_policy: disabled_for_vnext_dual_follower_aggregate_drawdown_budget`, `prop_safe_selector_daily_reset_timezone: Europe/Prague`, and portable FTMO terminal mode;
- corrected follower was reloaded as the only FTMO execution follower with zero FTMO `run_agent.py` fleet processes and no broker order/position mutation by the repair itself.

## Latest Target-State Restore Checkpoint

Recorded 2026-06-02 after the FTMO BTC residual-volume restart defect:
- FTMO follower now persists active target `TradeState` snapshots under the
  target runtime namespace;
- startup recovery restores target state by broker ticket from the compact store
  or action-log fallback, then synchronizes broker ticket/current volume/SL/TP
  before management;
- residual volume or BE SL on a vNext runner is treated as TP1 already handled,
  preventing duplicate TP1 close attempts after restart;
- corrected follower was relaunched as the only FTMO execution follower at
  `2026-06-02T15:31:27Z`; post-relaunch action-log scan found `0` TP1
  invalid-volume rows;
- focused verification passed: `python -m py_compile scripts\dual_broker_execution_follower.py`
  and `python -m pytest tests\test_dual_broker_execution_follower.py -q`
  (`20 passed`).

## Latest Broker Cash-Risk And Reload Checkpoint

Recorded 2026-06-02 after the GER30/GER40 live sizing defect:
- entry sizing for live/vNext selected-cell trades must use broker-side
  `order_calc_profit` cash-risk mechanics as authority; tick-value metadata is
  diagnostic/fallback only and cannot size live selected-cell orders;
- saved `cash_risk_amount` must represent broker-verified worst-case cash loss
  for the actual normalized/fill volume, not just the intended budget;
- stale FTMO failed-intent replay can retry recent misses inside the live
  recovery window, but it must never open a new market entry after that window;
  old closed source records are terminal audited skips, not late backfills;
- FTMO management stays target-local for existing target positions, including
  BE/partial/exit state restore, but the FTMO process footprint remains the
  lightweight follower architecture unless a researched architecture change
  replaces it;
- watchdog overlap is a live process-footprint defect: the watchdog now takes a
  namespace-scoped single-instance file lock before launching workers;
- post-reload verification at `2026-06-02T19:52Z` found 24 redacted_account workers,
  24 tick captures, one FTMO follower, one projector, two MT5 terminals, zero
  duplicate symbols, and healthy memory.

## Latest Follower State Provenance Checkpoint

Recorded 2026-06-02 after direct inspection of the live FTMO compact target
state:
- active target tickets in
  `pipeline_state/operator_profile/dual_broker_target_trade_state.json`
  could retain enough trade state for management while losing the source
  `intent_id` in the compact restart store;
- restored legacy FTMO target trades could also carry blank
  `cash_risk_amount_source` and `cash_risk_amount_status`, even when the
  current broker position/SL could prove the current worst-case risk state;
- `scripts/dual_broker_execution_follower.py` now preserves active
  ticket-to-intent lineage in memory, repairs missing compact-store intent ids
  from action-log rows on startup, and persists the repaired lineage on the
  next target-state write;
- restart restore now annotates blank cash-risk provenance explicitly from the
  current broker position/SL using `order_calc_profit` when available and
  labels tick-metadata fallback or unresolved cases without pretending legacy
  amounts are broker-verified;
- verification passed:
  `python -m pytest tests/test_dual_broker_execution_follower.py -q`
  (`30 passed`) and
  `python -m pytest tests/test_execution.py tests/test_orchestrator.py tests/test_dual_broker_intent_bus.py tests/test_dual_broker_trade_record_projector.py tests/test_profile_overrides.py tests/test_vnext_production_wiring.py -q`
  (`211 passed`).

## Latest Subagent Findings Materialization Checkpoint

Recorded 2026-06-02 after the final four read-only subagent audits returned:
- all subagent outputs are preserved as Markdown files under this route, not
  left in chat memory:
  - `SUBAGENT_FINDINGS_RUNTIME_PROCESS_DATA_FRESHNESS_2026-06-02.md`;
  - `SUBAGENT_FINDINGS_FTMO_FOLLOWER_2026-06-02.md`;
  - `SUBAGENT_FINDINGS_EXECUTION_RISK_LIFECYCLE_2026-06-02.md`;
  - `SUBAGENT_FINDINGS_CANDIDATES_SELECTORS_V3_2026-06-02.md`;
  - `SUBAGENT_FINDINGS_INDEX_2026-06-02.md`;
- the candidates/selectors/V3 agent was not shell-stuck; it was still
  broadening raw JSONL/log inspection and was explicitly interrupted with a
  finalize-now instruction so the current findings could be preserved and the
  repair queue could proceed;
- the combined repair plan must reconcile every subagent finding against raw
  disk/runtime evidence before repair or closure.

## Latest Combined Repair Matrix And Code Repair Checkpoint

Recorded 2026-06-02 after reconciling the captured subagent findings:
- combined finding-to-disposition matrix preserved at
  `SUBAGENT_FINDINGS_COMBINED_REPAIR_MATRIX_2026-06-02.md`;
- live admission risk now requires broker-side `order_calc_profit` cash-risk
  valuation for both FTMO target aggregate exposure and redacted_account source
  open-position exposure; tick metadata is not live admission authority;
- FTMO copied intents now require a source intent risk cap before target risk
  can be calculated;
- FTMO compact target-state persistence now refreshes active trades from the
  current broker position before writing and can upgrade weak legacy/tick
  provenance to broker-verified provenance;
- no-candidate M1 source packets now read the namespaced M1 capture state file;
- watchdog primary bridge no longer emits duplicate `--replay-existing`, and
  maintenance process detection excludes pytest command lines;
- follower checkpoints now include latest intent outcome classification instead
  of only blended processed counts;
- vNext market execution records now persist entry order/deal/retcode identity
  and filled-order join keys, matching the intent-bus identity surface;
- current shadow R denominator code already prefers immutable entry-risk
  geometry; reported near-zero denominator rows are treated as stale unless
  reproduced by post-repair evidence;
- one full `tests\test_gtos_vnext_runtime.py -q` run timed out and remained as
  a high-memory pytest process; PID 2720 was stopped, after which available
  memory recovered to roughly 5.4-6.4 GB.
