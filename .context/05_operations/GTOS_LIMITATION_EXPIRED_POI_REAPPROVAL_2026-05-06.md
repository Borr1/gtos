# GTOS Limitation - Expired POI Reapproval And Manual Execution Gap

Status: ACTIVE OPERATING LIMITATION WITH SHADOW MITIGATION
Date recorded: 2026-05-06
Incident: XAUUSD expired 2026-05-05 08:15 London SHORT limit retest during 2026-05-06 London pre-open/open
Promotion posture: NO_PROMOTION_VERDICT

## Limitation Statement

GTOS currently has no approved fast execution path for this case:

1. A prior valid production `LIMIT_PLACED` setup expires or is cancelled by the normal new-day lifecycle.
2. The original POI remains visually/structurally relevant on the chart.
3. The owner explicitly re-approves watching or taking the same setup.
4. Price later touches/rejects the old POI before the production system emits a fresh candidate.
5. A monitoring agent can see the discretionary opportunity, but the live system has no active pending intent and no fresh passed L2/Gate1 trade.

In this state, the monitoring agent must not silently narrate the move while the level is being lost. The agent must immediately make the execution boundary explicit.

## Shadow Mitigation Implemented 2026-05-06

The first engineered mitigation is now code-wired as a shadow-only lifecycle split:

- `src/components/expired_poi_watch.py` preserves eligible expired/cancelled `LIMIT_PLACED` geometry as a structural POI watch.
- `config/agent_config.yaml` has `expired_poi_watch.enabled: true`, `mode: shadow`, `max_watch_hours: 72`, `min_rearm_rr: 1.5`, `log_all_revalidations: false`, and `execution_override_enabled: false`.
- `src/components/orchestrator.py` archives watch-eligible new-day and 48h expiries before clearing executable pending intent state, then evaluates active watches during active KZ, between-KZ, after-KZ, and pre-KZ loops.
- Watch registry: `knowledge_base/meta/expired_poi_watches/expired_poi_watches_{SYMBOL}.jsonl`.
- Revalidation log: `shadow_logs/expired_poi_revalidation.jsonl`.
- Manual one-shot evaluator: `python scripts/follow_expired_poi_watches.py --symbol XAUUSD --no-write`.
- Historical seed/replay path: `python scripts/follow_expired_poi_watches.py --symbol XAUUSD --seed-record knowledge_base\trade_records\XAUUSD\2026-05-05_london_0815.json --cancel-reason new_day`.
- Tests: `tests/test_expired_poi_watch.py`.
- Terminal state hardening: commit `ccd77bff` appends `WATCH_CLOSED` rows for `INVALIDATED_BY_SL` and `EXPIRED_WATCH_MAX_AGE`; the loader uses the latest registry row per `watch_id`, so stale or duplicate create rows do not remain active after closure.

This mitigation does not place trades, rearm intents, or bypass production L2/Gate1. It only prevents GTOS from losing the old POI context after executable intent expiry and labels whether current price is far, approaching, touched with RR decay, touched with SL-distance too tight, touched with shadow-eligible geometry, invalidated by SL, or watch-expired.

Operational caveat: running orchestrator processes must be restarted before this code is loaded. XAUUSD was restarted on 2026-05-06 after the watcher and terminal-close hardening were added. Any POI that expired before this patch was loaded will not appear in the watch registry unless it is explicitly seeded/replayed from historical records with the seed command above.

## 2026-05-06 XAUUSD Outcome Update

The specific XAUUSD watch created from `lim_XAUUSD_2026-05-05_081526` is no longer active. It revalidated as `TOUCHED_SL_DISTANCE_TOO_TIGHT_NO_REARM` near the old POI, then invalidated at/through the old SL `4679.89` during the 08:00 UTC London candle. The final state is `INVALIDATED_BY_SL` with a terminal `WATCH_CLOSED` registry row. `load_active_watches("XAUUSD")` and `scripts/follow_expired_poi_watches.py --symbol XAUUSD --mode live --no-write` returned no active rows after closure. This confirmed that GTOS avoiding a late forced re-entry saved the account from the old setup's SL path.

## Mandatory Agent Response Rule

When an expired/cancelled POI is re-approved by the owner and price is approaching the old entry, the agent must do all of the following within the next update:

- State whether there is an active production path: fresh candidate, pending intent, broker order, or open position.
- State whether the agent can execute through an approved system path right now.
- If the agent cannot execute, say plainly: `I cannot place this manually through GTOS right now; if you want the discretionary trade, you must place it manually or we need a pre-approved override tool/runbook.`
- Provide the current price, old entry, old SL, old TP, and current RR if entered now.
- If the old RR has decayed below `risk.min_rr`, say that the original trade is gone and any entry is a different trade.
- Record the event as `EXPIRED_POI_REAPPROVAL_LIMITATION` in the AI observation ledger.

Do not wait for the level to be missed before explaining the boundary.

## 2026-05-06 XAUUSD Evidence

Original setup:

- Record: `knowledge_base/trade_records/XAUUSD/2026-05-05_london_0815.json`
- Candidate: `XAUUSD_2026-05-05T08:15:00+00:00`
- Trade id: `lim_XAUUSD_2026-05-05_081526`
- Direction/framework: SHORT `ob_retest`
- Original grade: A+
- Entry: `4668.45`
- H1 bearish OB: `4668.45-4675.72`
- SL: `4679.89`
- TP1: `4651.28`
- Lifecycle: cancelled at UTC new day, `cancel_reason=new_day`, no broker order, no pending intent

Owner/operator context:

- The owner identified that price was returning to the expired entry before London.
- The owner explicitly approved executing the valid setup if confirmed.
- The monitoring agent tracked the touch and rejection but did not execute and did not force a clear manual handoff early enough.

Market path:

- 2026-05-06 06:35 UTC M5: high `4668.82`, touching old entry, close `4666.15`.
- 2026-05-06 06:55 UTC M5: high `4669.77`, close `4669.22`.
- 2026-05-06 07:00 UTC M5: high `4670.41`, then rejection.
- 2026-05-06 07:10 UTC M5: low `4658.46`, close `4658.57`.
- At 2026-05-06 07:16 UTC, current bid was about `4658.71`; entering short there against old SL/TP gave only about `0.35R`, below `risk.min_rr=1.5`.

Production truth:

- No active XAUUSD broker order.
- No active XAUUSD position.
- No persisted `knowledge_base/meta/pending_intent_XAUUSD.pkl`.
- Fresh 2026-05-06 07:15 production record existed, but it was an AI `CANDIDATE` LONG and final `REJECTED_L2`; it did not recreate the short.

## Operational Lesson

The missed event was not a broker/account outage and not a shadow-log health failure. It was an operating-design gap:

- expired but still-valid-looking POIs can produce real discretionary reactions before GTOS emits a fresh candidate;
- monitoring can see this market-path event;
- GTOS currently has no safe, pre-approved way for the AI monitor to rearm or manually execute that expired POI;
- future agents must not confuse "owner approval" with "approved execution mechanism exists."

## Required Follow-Up

Create a separate design ticket before enabling any automated or agent-assisted override. Minimum requirements:

- explicit owner command syntax for discretionary override;
- in-KZ check or explicit outside-KZ override acknowledgement;
- current RR check against `risk.min_rr`;
- current spread and SL-distance checks;
- duplicate-position/order protection;
- broker/account truth check immediately before send;
- durable audit row that labels the trade as `OPERATOR_DISCRETIONARY_OVERRIDE`, not production baseline;
- tests around expired pending intent reapproval and duplicate-order prevention.

Until that exists, the only valid response to this case is immediate explicit handoff to the owner plus monitoring, not silent narration and not late chasing.
