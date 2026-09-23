# GTOS KZ Mini Syntheses - 2026-05-08

Generated: 2026-05-08 17:15 UTC

Promotion posture: `NO_PROMOTION_VERDICT`

Scope note: this file covers the active monitoring window handled in this session: NY KZ and post-NY closeout. Earlier-day context was read from structured logs but was not live-monitored end to end in this turn.

## NY JPY / GBPUSD - 13:00-15:30 UTC

- Production truth: no broker orders, no broker positions, no realized account PnL.
- System behavior: GBPUSD repeatedly produced LONG `ob_retest` candidate-shaped rows but stayed `REJECTED_L2`; GBPUSD remains observer/no-execution. NAS100 also produced repeated pre-15:45 LONG `ob_retest` rows rejected by Gate1 safety. JPY symbols did not create a production exposure during the monitored NY window.
- Process behavior: at 15:30 UTC the live monitor process count dropped from 7 to 4. Process inspection confirmed the remaining orchestrators were `NAS100`, `XAUUSD`, `US30_cash`, and `XAGUSD`; the drop was consistent with FX/JPY/GBPUSD KZ close behavior.
- Source/orderflow context: GBPUSD/6B remained source-transfer/context only; Databento paid fetches were not attempted. Sierra status rows were present where applicable.
- Shadow health: after the 15:30 writer cycle, integrity temporarily reported historical opportunity-lifecycle mismatches. A wider append-only refresh superseded stale cluster projections; no production exposure was implicated.

## NY Indices / Metals - XAUUSD / XAGUSD / US30 / NAS100 - 13:00-17:00 UTC

- Production truth: final MT5 account truth showed account `0` on `redacted_account-Server 2`, balance/equity `101223.36`, broker orders `0`, broker positions `0`, profit `0.0`, margin `0.0`, `trade_allowed=true`, `trade_expert=true`.
- Final monitor truth: `_live_monitor_iter.py` iter `829`, candle `2026-05-08T17:00:00+00:00`, `crit=0`, `anom=0`, `pids=2`, `open_pos=0`.
- Process truth: after 17:00 UTC, the two remaining orchestrators were `NAS100` and `US30_cash`, matching the two still-active internal candle-polled pending intents. Other KZ orchestrators closed; all seven tick-capture daemons and monitor/queue helpers remained running.
- US30_cash production truth: `US30_cash_2026-05-08T13:45:00+00:00` / `lim_US30_cash_2026-05-08_134523` remained internal only: `broker_pending_order_created=false`, `mt5_order_ticket=null`, no broker order, no broker position, no order send, no trigger.
- US30_cash market-path truth: by the 17:00 path row, price still had not touched entry `49340.72`; min low `49558.05`, max high `49756.8`, latest close `49565.3`; TP1 area `49531.81` was reached from decision time without entry touch. Classification: `TP_AREA_REACHED_NO_FILL`, not realized R.
- NAS100 production truth: `NAS100_2026-05-08T15:45:00+00:00` / `lim_NAS100_2026-05-08_154524` remained internal only: `broker_pending_order_created=false`, `mt5_order_ticket=null`, no broker order, no broker position, no order send, no trigger.
- NAS100 market-path truth: by the 17:00 path row, price still had not touched entry `27300.0`; min low `29062.9`, max high `29141.25`, latest close `29140.87`; TP1 area `27459.9` was reached from decision time without entry touch. Classification: `TP_AREA_REACHED_NO_FILL`, not realized R.
- XAUUSD/XAGUSD production truth: no broker exposure during monitored NY closeout. Their orchestrators closed after NY; tick captures stayed fresh.
- Source/orderflow context: Sierra Chart process was running. NQ/YM/GC/SI `.depth` and `.scid` files had final checked mtimes around 17:14-17:15 UTC. NAS100/NQ and US30/YM are registered futures-context lanes; XAGUSD/SI remains source-definition blocked for interpretation. Databento live remained disabled/no API key; paid data calls stayed `0`.
- Shadow/ML context: final integrity `OK_WITH_DOCUMENTED_WAITING_LANES`, data health `OK_WITH_DOCUMENTED_LIMITATIONS`, `issue_count=0`, latest candidates `190`. K55/ML and strategy-shadow lanes remain observational only.
- Operational warning: storage is tight. `audit_storage_retention.py --dry-run` returned `STORAGE_RETENTION_WARNING`, free space `10.47 GB` / `4.41%`, with 25 dry-run cleanup candidates. No deletion was performed.

## End-Of-NY Closeout

- Final writer sequence ran after the 17:00 candle: path follow, Sierra pending-status enrichment, 59-step maintenance/audit chain, final integrity verifier, final data-health audit, MT5 account truth, process inspection, watchdog, tick-capture freshness, Sierra file freshness, and storage dry run.
- Watchdog final status: `WARN` only because the canary cache is stale under owner-approved canary skip through 2026-12-31. Other watchdog checks passed.
- Tick capture: all seven daemon heartbeats/state files were present; active NAS100/US30/XAUUSD/XAGUSD states were fresh, and closed-session symbols were still within a few minutes.
- Final posture: production safe and broker-flat; shadow/data-health clean with documented limitations; storage requires operator attention; no trading-logic, prompt, risk, execution, source, ML, or selector promotion.
