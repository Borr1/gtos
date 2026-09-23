# GTOS Deep Active Monitoring Final Report - 2026-05-05

Generated: 2026-05-05 17:12 UTC

Verdict: `NO_PROMOTION_VERDICT`

## Executive Status

- Overall status: `NO_ACTION_REQUIRED_FOR_TRADING_LOGIC`.
- Production safety: clean. Broker positions `0`, broker orders `0`, account balance/equity `101223.36`, profit `0.0`.
- Final monitor state: `_live_monitor_iter.py` iter `634` returned `crit=0`, `anom=0`, `pids=2`, `open_pos=0`.
- Final data state: integrity `OK_WITH_DOCUMENTED_WAITING_LANES`; semantic health `OK_WITH_DOCUMENTED_LIMITATIONS`, `issue_count=0`.
- Trading behavior changed: none.

## Safety And Operations

| Area | Status | Evidence |
|---|---|---|
| MT5/broker truth | `OK_FLAT` | Balance/equity `101223.36`; positions/orders `0/0` |
| Execution | `NO_BROKER_EXECUTION` | All NY candidates rejected before order placement |
| Watchdog/monitor | `OK_WITH_NOTE` | No criticals; one 16:00 boundary anomaly cleared immediately |
| Tick capture | `OK_WITH_SIDE_PROBE_LIMITATION` | Production tick states stayed fresh; direct NAS100/US30 side probe failed |
| Sierra/Databento | `SOURCE_STATUS_ONLY` | Sierra files present; SI interpretation blocked; Databento paid calls `0` |
| Storage/audits | `OK` | Final append-only audits and verifiers clean |

## Candidate Lifecycle

| Scope | Count | Notes |
|---|---:|---|
| Latest raw candidates | `76` | `strategy_follow_candidates.jsonl` |
| NY new candidates | `10` | All XAGUSD short `ob_retest` |
| NY broker executions | `0` | No order/position created |
| Final opportunity counts | `12 / 63 / 1` | Countable / duplicate-active / same-symbol-overlap |

NY candidate pattern:
- 14:15, 14:30, 14:45, 15:15, 15:30, 15:45, 16:15 used/repeated older XAGUSD bearish OB `75.789-75.471`.
- 16:30, 16:45, 17:00 used newer XAGUSD bearish OB `73.971-73.222`.
- All were `REJECTED_L2`, primarily blocked by `m15_choch_exists`.

## Pending Limits

| Candidate | Symbol | Direction | Entry / SL / TP1 | Final monitored state |
|---|---|---|---|---|
| `NAS100_2026-05-05T07:15:00+00:00` | NAS100 | LONG | `27646.2 / 27598.4 / 27717.8` | Internal no-fill/still-pending; no broker order/position |
| `XAUUSD_2026-05-05T08:15:00+00:00` | XAUUSD | SHORT | `4668.45 / 4679.89 / 4651.28` | Internal no-fill/still-pending; no broker order/position |

## Market Tape Timeline

- London: XAUUSD rebounded from the 4539 area into the 4560s; XAGUSD recovered into the 73.7s; GBPUSD moved but stayed prescreen-blocked.
- NY open to 15:30: XAGUSD repeatedly emitted short OB candidates and L2 rejected all for missing M15 structure confirmation. FX window closed flat.
- 15:30 to 16:00: XAUUSD/XAGUSD sold off; US30 closed flat at 16:00.
- 16:00 to 17:00: XAGUSD shifted to a newer H1 bearish OB, but L2 still blocked entries. Metals/NAS closeout remained broker-flat.

## Incidents And False Positives

- 14:15 transient heartbeat jitter on US30/XAGUSD cleared on immediate recheck.
- 16:00 closeout boundary anomaly cleared on immediate recheck.
- Persistent direct side-probe failure for NAS100/US30_cash did not affect production tick-capture, candidate logging, or broker truth.
- Post-window XAUUSD/NAS100 heartbeats persisted at 17:05 after configured end `17:00`; no exposure, no anomaly, but worth operator/watchdog review.

## Open Blockers

- `SOURCE_DEPTH_DEFINITION_BLOCKED_SI`: XAGUSD Sierra SI depth cannot be interpreted as Databento-equivalent orderflow.
- V2/V3/K55 lanes are shadow-only; required promotion-grade lock/reentry/FVG metadata is not available.
- Direct read-only side probe for NAS100/US30_cash still fails with `Terminal: Call failed`.

## Hypotheses For Later Validation

- XAGUSD can repeatedly identify bearish H1 OB context during a real selloff, but current L2 M15 structure confirmation prevented all entries.
- The newer XAGUSD OB `73.971-73.222` may be a distinct late-NY short opportunity class, but current evidence is only source-status/forward-shadow and rejected by L2.
- Post-window lingering XAUUSD/NAS100 heartbeats may be scheduler/watchdog behavior rather than trading exposure; verify process lifecycle separately.

Final posture: `NO_PROMOTION_VERDICT`
