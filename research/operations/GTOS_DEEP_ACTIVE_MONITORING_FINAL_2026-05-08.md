# GTOS Deep Active Monitoring Final Report - 2026-05-08

Generated: 2026-05-08 17:15 UTC

Promotion posture: `NO_PROMOTION_VERDICT`

## Overall Status

- Overall readiness: `COMPLETE_WITH_DOCUMENTED_LIMITATIONS`.
- Production safety: clean. Final MT5 truth showed balance/equity `101223.36`, broker positions `0`, broker orders `0`.
- Final monitor: `_live_monitor_iter.py` iter `829`, candle `2026-05-08T17:00:00+00:00`, `crit=0`, `anom=0`, `pids=2`, `open_pos=0`.
- Trading behavior changed: none. No prompt, risk, execution, safety-gate, selector, ML, source, or order-behavior promotion.
- Files written by this monitoring closeout: AI observation ledger, NY KZ mini-synthesis, final report, completion audit.

## Production Safety

| Area | Status | Evidence |
|---|---|---|
| Broker account | `OK_FLAT` | Account `0`, balance/equity `101223.36` |
| Broker exposure | `OK_NONE` | MT5 positions `0`, orders `0`, profit `0.0`, margin `0.0` |
| Live monitor | `OK` | Final iter `829`, `crit=0`, `anom=0`, `open_pos=0` |
| Active process after close | `EXPECTED_WITH_PENDING` | `NAS100` and `US30_cash` remain for internal pending intents |
| Watchdog | `WARN_CANARY_ONLY` | owner-approved canary cache skip; other checks pass |
| Shadow integrity | `OK_WITH_DOCUMENTED_WAITING_LANES` | issues `{}`, JSONL rows `210284` |
| Live shadow data health | `OK_WITH_DOCUMENTED_LIMITATIONS` | `issue_count=0`, latest candidates `190` |
| Storage | `WARNING` | `10.47 GB` free / `4.41%`; no cleanup performed |

## Candidate And Pending Lifecycle

Two production `LIMIT_PLACED` rows remained internal only at close:

| Intent | Symbol | Side | Entry / SL / TP1 | Production Truth | Market-Path Truth |
|---|---|---|---|---|---|
| `lim_US30_cash_2026-05-08_134523` | US30_cash | LONG | `49340.72 / 49213.39 / 49531.81` | no broker order, no MT5 ticket, no position, no trigger, no order send | TP area reached without entry touch; min low `49558.05`, max high `49756.8`, latest close `49565.3` |
| `lim_NAS100_2026-05-08_154524` | NAS100 | LONG | `27300.0 / 27193.4 / 27459.9` | no broker order, no MT5 ticket, no position, no trigger, no order send | TP area reached without entry touch; min low `29062.9`, max high `29141.25`, latest close `29140.87` |

These are missed internal-limit path outcomes, not realized wins and not realized broker R. Current logic keeps internal candle-polled intents alive when TP area is reached without entry touch.

## NY Timeline

- 13:45 UTC: US30_cash produced an internal LONG limit intent. Production state was internal/no broker ticket. Market immediately stayed above entry and reached TP area without touching the entry.
- 14:00-15:30 UTC: NAS100 repeatedly produced candidate rows rejected by Gate1 safety; GBPUSD observer rows were rejected by L2. No broker exposure.
- 15:30 UTC: FX/JPY/GBPUSD KZ close reduced active orchestrator count from 7 to 4 as expected. A transient shadow integrity issue appeared in historical opportunity-lifecycle rows, traced to append-only stale latest cluster projections; wider refresh superseded them.
- 15:45 UTC: NAS100 produced a new internal LONG limit intent. First audit cycle briefly showed a missing pending lifecycle join, then the 16:00 lifecycle row caught up.
- 16:00 UTC: US30 KZ close checkpoint. Shadow integrity and data health returned to documented OK statuses. NAS100 lifecycle row confirmed no-fill/no-trigger/no-order-send.
- 16:15-16:45 UTC: no new candidates; both active intents stayed no-fill/no-trigger/no-order-send. Integrity and data health remained clean.
- 17:00 UTC: final NY closeout. Production remained broker-flat; path/lifecycle/audit chain completed cleanly.

## Source / Orderflow / ML

- Sierra Chart was running. Final checked source files for NQ/YM/GC/SI had mtimes around 17:14-17:15 UTC.
- NAS100/NQ and US30/YM are usable only as registered futures-context/proxy lanes, not direct broker CFD liquidity.
- XAGUSD/SI depth remains source-definition blocked for interpretation.
- Databento live remained disabled/no API key; paid fetch attempted `false`; paid data calls `0`.
- K55/ML, V2/V2B, J46/J49, pending-limit lifecycle, prefill, FVG/OB, and mechanical strategy rows remain observational only. No promotion verdict changed.

## Operational Warnings

- Storage: `audit_storage_retention.py --dry-run` returned `STORAGE_RETENTION_WARNING`, free `10.47 GB` / `4.41%`, `25` dry-run cleanup candidates. This needs operator attention before extended capture continues.
- Watchdog: `WARN` is limited to the owner-approved canary cache skip. Do not treat this as a canary pass or failure; it is a cost-control exception.
- Internal pending stale-opportunity policy remains unresolved: US30_cash and NAS100 keep candle-polled pending intents after TP area was reached without entry touch.

## Final Posture

The monitored NY session closed broker-flat and operationally safe. Shadow and source systems are coherent after final writer/audit/verifier sequencing. The day produced two important missed-limit intelligence cases, but no realized trade, no broker exposure, and no promotion-grade evidence.

Final verdict: `COMPLETE_WITH_DOCUMENTED_LIMITATIONS`, `NO_PROMOTION_VERDICT`.
