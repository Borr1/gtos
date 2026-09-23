# GTOS Active Monitoring Checkpoint - 2026-05-08 08:12 UTC

## Scope

This checkpoint followed the active monitoring and intelligence-gathering prompt lineage, with emphasis on the stale-data incident from 2026-05-06 and the instruction to inspect more than the current candle.

- Retrospective window: `2026-05-06T17:10:00Z` through `2026-05-08T08:12:05Z`.
- Window basis: latest pre-session `shadow_logs/live_monitor.jsonl` activity was 2026-05-06 17:10 UTC; `live_monitor_alerts.jsonl` had no alerts after the 2026-05-06 stale-data episode.
- Prompt/runbook files read: `.context/05_operations/GTOS_DEEP_ACTIVE_MONITORING_GOAL_PROMPT_2026-05-05.md`, `.context/05_operations/GTOS_DEEP_ACTIVE_MONITORING_RUNBOOK_2026-05-05.md`, `.context/05_operations/GTOS_DAILY_MONITORING_CHECKLIST_2026-05-05.md`, `.context/05_operations/FORWARD_CAPTURE_MONITORING_RUNBOOK_2026-05-04.md`, `.context/05_operations/GTOS_LIMITATION_EXPIRED_POI_REAPPROVAL_2026-05-06.md`, and `research/program_control/FORWARD_CAPTURE_AND_INTELLIGENCE_INFRASTRUCTURE_GOAL_PROMPT_2026-05-04.md`.
- This is a live checkpoint while the 2026-05-08 London kill zone was still active, not a full-day closeout through NY end.

No trading logic, configuration, prompts, source code, broker orders, or positions were changed. No AI, canary, execution, or paid data calls were made by the monitoring scripts.

## Current Live Verdict

Production live safety is clean at this checkpoint.

- `scripts/_live_monitor_iter.py`: `iter=773`, `candle=2026-05-08T08:00:00+00:00`, `crit=0`, `anom=0`, `pids=7`, `open_pos=0`.
- Latest watchdog pass: 17 healthy checks, 0 restarted. All 7 orchestrator PIDs were alive.
- Tick capture progress was fresh on all 7 symbols. Oldest observed progress age was `US30_cash` at 247.8 seconds, with the watchdog still reporting OK.
- MT5 direct probe: initialized successfully on `redacted_account-Server 2`, account `0`, `trade_allowed=true`, `trade_expert=true`, balance/equity `101223.36`, positions `0`, orders `0`.
- `scripts/watchdog_e2e_verify.py --verbose`: 3 PASS, 1 WARN, 0 FAIL. The WARN was canary-cache staleness under the owner-approved canary skip/cost-control state through 2026-12-31.
- Notification queue audit: OK, worker running, queue empty.
- Storage retention dry run: OK, `44.33 GB` free, `18.66%` free, cleanup candidates listed but not removed.
- XAUUSD expired POI watch: none active from `follow_expired_poi_watches.py --symbol XAUUSD --mode live --no-write`.

## Since Last Monitoring Session

The inspected window produced candidates and shadow evidence, but no executed system trades.

| Item | Count / Status |
| --- | ---: |
| Strategy candidate records since 2026-05-06 17:10 UTC | 48 |
| Knowledge-base trade records in same window | 48 |
| Trade records with execution payload | 0 |
| Current broker positions | 0 |
| Current broker orders | 0 |

Outcome mix in the window:

| Final outcome | Count |
| --- | ---: |
| `REJECTED_GATE0_5_TRADING_ENABLED` | 21 |
| `REJECTED_L2` | 20 |
| `REJECTED_GATE1_SAFETY` | 6 |
| `LIMIT_PLACED` | 1 |

Symbol candidate mix:

| Symbol | Count |
| --- | ---: |
| GBPUSD | 32 |
| USDJPY | 2 |
| NAS100 | 5 |
| XAGUSD | 5 |
| XAUUSD | 4 |

The single `LIMIT_PLACED` event was NAS100 London 2026-05-07 07:15 UTC. It was an internal pending-limit lifecycle record, not a broker order: `broker_pending_order_created=false`, `mt5_order_ticket=null`, and later lifecycle rows remained `still_pending_no_trigger`. The direct MT5 check found no open orders.

## Market / Candidate Tape

2026-05-07:

- GBPUSD generated a large observer-only candidate stream. London candidates were blocked by `REJECTED_GATE0_5_TRADING_ENABLED`; later rows were L2-rejected, mainly `m15_choch_exists`.
- USDJPY 07:15 and 07:30 CANDIDATEs were rejected by Gate 1 because SL distance was too tight relative to ATR.
- NAS100 07:15 produced the internal `LIMIT_PLACED` record described above, but no broker order or fill.
- XAUUSD/XAGUSD later-window candidates were L2-rejected. No expired-POI execution path existed.

2026-05-08 through 08:12 UTC:

- GBPUSD 07:15, 07:30, 07:45, and 08:00 candidates were L2-rejected by `m15_choch_exists`; GBPUSD remains observer-only.
- NAS100 07:15, 07:30, 07:45, and 08:00 A+ CANDIDATE rows were rejected by Gate 1 safety on `touch_count_too_high` with touch count 2 and threshold 2. No order was sent.
- The NAS100 07:15/07:30 trade-record top-level AI `trade_parameters` differ from the M5-refined shadow values; final outcome was still Gate 1 rejection, so this is a shadow consistency/accounting issue, not execution risk.

## Shadow Intelligence State

The writer/enrichment/audit chain was refreshed in the runbook order: live monitor, candidate path follower, expired POI watcher, Sierra pending enrichment, dependent backfills, shadow integrity verifier, live data health audit, and opportunity summary.

Opportunity summary after refresh:

- Raw candidates with latest cluster: 134.
- Countable primary unique opportunities: 35.
- Duplicate active setups retained but not counted: 99.
- Promotion verdict: `NO_PROMOTION_VERDICT`.
- No AI calls, no canary required, no execution, paid data calls `0`.

Latest countable opportunity path labels:

| Path label | Count |
| --- | ---: |
| `went_through_entry_and_continued_to_sl` | 11 |
| `MISSING_PATH` | 10 |
| `continued_without_entry_touch_to_tp_area` | 9 |
| `entry_touched_tp_and_sl_m15_ambiguous` | 2 |
| `no_touch_stayed_above_entry` | 2 |
| `entry_touched_then_reached_tp1` | 1 |

Countable-only proxy R remains negative on the current shadow sample:

| Strategy / shadow lane | Proxy R | Counted rows |
| --- | ---: | ---: |
| `LIVE_AI_J46_J49_BASELINE_COMPARATOR` | -9.5 | 23 |
| `PENDING_LIMIT_LIFECYCLE` | -7.5 | 24 |
| `V2B_OB_BOUNDARY_PROSPECTIVE` | -8.5 | 20 |

This is shadow/path proxy evidence only. It is not a validated promotion or demotion claim, and the current verdict remains `NO_PROMOTION_VERDICT`.

## Integrity And Known Gaps

Operational live safety is clean, but research/monitoring data health still has action-required items.

`scripts/verify_shadow_log_integrity.py` after refresh:

- Overall: `ACTION_REQUIRED`.
- Serious issues: 91.
- Main groups: 40 `OPPORTUNITY_LIFECYCLE_AUDIT_ACTION_REQUIRED`, 40 `MISSING_REQUIRED_FIELD` on `live_candidate_opportunity_clusters.asof_latest_candle_utc`, trade-index lifecycle audit issues, stale inventory index, pending-limit lifecycle action-required/stale rows, and shadow-observer hardening/readiness rows.

`scripts/audit_live_shadow_data_health.py` after refresh:

- Overall: `ACTION_REQUIRED`.
- Issues: 130.
- Main groups: 80 `CRITICAL_FIELD_NULL`, 46 `MISSING_CANDIDATE_COVERAGE`, 4 `TRADE_RECORD_CANDIDATE_VALUE_MISMATCH`.
- The mismatch examples are NAS100 2026-05-08 candidates where top-level trade-record parameters and M5-refined shadow parameters differ; those candidates were rejected by Gate 1 and did not execute.

Source/orderflow readiness:

- Sierra pending-only enrichment wrote missing queue rows; full bounded Sierra enrichment extracted 6 feature rows with no paid calls.
- Sierra depth confluence still reports `ACTION_REQUIRED_MISSING_FEATURE_ROWS` for remaining background queue coverage.
- NAS100 orderflow adverse-selection audit remains `WAITING_FOR_DATABENTO_LIVE_LICENSE`.
- GBPJPY proxy gap remains blocked with preregistered proxy design.
- 6B/SI policy audit is OK with SI source blocker.
- Orderflow primitives are registered, with source blockers still explicit.

## Actionable Takeaways

1. No live trading intervention was required at this checkpoint: PIDs, heartbeat, tick capture, MT5 account state, broker positions/orders, and notification queue were clean.
2. The reason "no trades" remains consistent with the logs: candidates were blocked by observer-only mode, L2 `m15_choch_exists`, Gate 1 SL-tight/touch-count safety, or no-fill pending lifecycle.
3. The 2026-05-06 stale-data failure mode did not recur in this checkpoint; strategy-follow freshness, live monitor pulses, and tick-capture progress were checked in addition to process health.
4. The intelligence pipeline is collecting useful evidence but not promotion-ready. The current shadow tape is negative on proxy R and still has coverage/schema issues, so it should remain shadow-only.
5. Next engineering cleanup should target the monitoring-data action-required items: `asof_latest_candle_utc` nulls in opportunity clusters, candidate path coverage gaps, trade-index lifecycle freshness, and shadow observer hardening rows.

