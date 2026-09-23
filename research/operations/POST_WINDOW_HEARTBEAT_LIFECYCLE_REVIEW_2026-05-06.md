# Post-Window Heartbeat Lifecycle Review - 2026-05-06

**Status:** `RESOLVED_EXPECTED_PENDING_LIMIT_SURVEILLANCE_TO_DEAD_ZONE_CLEANUP`
**Scope:** read-only operational lifecycle audit
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Live behavior impact:** none

## Objective

Answer why `XAUUSD` and `NAS100` heartbeats remained alive after the configured
May 5, 2026 NY kill-zone end at `17:00 UTC`, and classify the behavior as
expected process lifecycle or a watchdog bug.

## Evidence Read

- Kill-zone config:
  - `config/agent_config.yaml:631-635` shows `XAUUSD` NY `13:00` to `17:00`.
  - `config/agent_config.yaml:718-722` shows `NAS100` NY `13:00` to `17:00`.
- Orchestrator lifecycle:
  - `src/components/orchestrator.py:691-700` writes a per-symbol heartbeat each
    main-loop iteration.
  - `src/components/orchestrator.py:750-757` keeps the orchestrator alive after
    all KZs if `execution.pending_intent` exists, checking outside-KZ fills and
    sleeping in 60-second chunks.
  - `src/components/orchestrator.py:780-786` only exits cleanly when there is no
    active trade and no pending intent.
  - `src/components/orchestrator.py:2321-2389` defines the outside-KZ pending
    limit check path.
  - `src/components/orchestrator.py:4296-4326` deletes heartbeat files and writes
    graceful-shutdown markers only in the graceful shutdown path.
- Watchdog lifecycle:
  - `scripts/watchdog.ps1:38-39` defines the local dead zone as `01:15-07:45`
    Singapore time, equivalent to `17:15-23:45 UTC`.
  - `scripts/watchdog.ps1:525-544` runs dead-zone cleanup first unless an active
    broker position exists.
- Monitor behavior:
  - `scripts/_live_monitor_iter.py:232-264` treats heartbeat missing/stale
    differently inside versus outside KZ.
  - `scripts/_live_monitor_iter.py:384-403` counts only heartbeats fresher than
    120 seconds as alive and compares expected alive count to active KZs only.
  - `src/safety/heartbeat_monitor.py:1201-1212` logs `OUTSIDE_KZ` instead of
    flattening when no instrument KZ is active.
- Live evidence:
  - `shadow_logs/pending_limit_lifecycle.jsonl:136-141`
  - `shadow_logs/live_monitor.jsonl` monitor iterations `630-634`
  - `logs/watchdog.log:14492-14529`
  - `pipeline_state/heartbeat_XAUUSD.json`
  - `pipeline_state/heartbeat_NAS100.json`
  - `knowledge_base/meta/pending_intent_XAUUSD.pkl`
  - `knowledge_base/meta/pending_intent_NAS100.pkl`

## Findings

The configured `17:00 UTC` end is respected as the end of active KZ
classification. The apparent post-window liveness came from two still-open
internal pending limit intents:

- `XAUUSD`: `lim_XAUUSD_2026-05-05_081526`, placed at
  `2026-05-05T08:15:26.485637+00:00`, still pending at the boundary.
- `NAS100`: `lim_NAS100_2026-05-05_072816`, placed at
  `2026-05-05T07:28:16.993555+00:00`, still pending at the boundary.

At `17:00:05 UTC`, both symbols logged normal inside-KZ no-fill lifecycle rows
for the final boundary candle:

- `XAUUSD`: `shadow_logs/pending_limit_lifecycle.jsonl:136`
- `NAS100`: `shadow_logs/pending_limit_lifecycle.jsonl:138`

Immediately after that, both moved into the outside-KZ pending-limit branch:

- `XAUUSD`: `shadow_logs/pending_limit_lifecycle.jsonl:137`
- `NAS100`: `shadow_logs/pending_limit_lifecycle.jsonl:139`

At `17:15:05 UTC`, both were still pending and were checked again from
`source_branch=outside_kz_pending_check`:

- `XAUUSD`: `shadow_logs/pending_limit_lifecycle.jsonl:140`
- `NAS100`: `shadow_logs/pending_limit_lifecycle.jsonl:141`

The heartbeat files match those final checks:

```text
pipeline_state/heartbeat_XAUUSD.json -> 2026-05-05T17:15:05.153179+00:00, pid=10932
pipeline_state/heartbeat_NAS100.json -> 2026-05-05T17:15:05.196205+00:00, pid=15708
```

The watchdog then entered dead-zone cleanup at `2026-05-06 01:16:02` local
(`2026-05-05 17:16:02 UTC`) and killed exactly those two orchestrators:

- `logs/watchdog.log:14493` shows `XAUUSD` PID `10932` alive at `01:01` local.
- `logs/watchdog.log:14499` shows `NAS100` PID `15708` alive at `01:01` local.
- `logs/watchdog.log:14513-14516` shows dead-zone cleanup killing both PIDs.

Other symbols had graceful-shutdown markers because they had no pending intent
or active trade at their shutdown point. XAUUSD/NAS100 did not write those
markers because the orchestrator never entered the no-active/no-pending graceful
shutdown branch before the dead-zone cleanup.

## Classification

This is expected current process behavior, not a watchdog lifecycle bug.

The exact path is:

1. NY KZ active until `17:00 UTC`.
2. Final boundary candle processed at `17:00:05 UTC`.
3. Pending limit intents still existed.
4. Orchestrator entered `after_all_kz + pending_intent` surveillance.
5. Heartbeats remained fresh because the loop was alive by design.
6. Live monitor treated fresh outside-KZ heartbeats as non-critical.
7. Watchdog dead-zone cleanup started at `17:15 UTC` plus scheduler drift and
   killed remaining processes at `17:16:02 UTC`.

This was not timeout trailing, not a stale heartbeat file from a dead process,
and not a heartbeat-monitor flatten defect.

## Ambiguity Status

- Why did post-window heartbeats persist? `RESOLVED`.
- Was it timeout trailing? `NO`; no active broker positions were reported by
  live monitor, and the lifecycle rows show pending-limit checks.
- Was it watchdog lifecycle failure? `NO`; watchdog followed configured
  dead-zone cleanup.
- Is current pending-intent survival after the last KZ strategically desired?
  `UNRESOLVED_POLICY_DECISION`; changing that would alter trading lifecycle
  behavior and needs owner approval. Phase 1D should document pending-limit
  semantics separately before any design change is considered.

## Implementation Details

No code was changed.

No process was restarted.

No prompt, risk, execution, permissions, order-placement, or watchdog lifecycle
behavior was modified.

## Tests / Verifier Output

No tests were required because this was a read-only audit and produced no code
changes. Verification consisted of cross-checking:

- config session windows,
- orchestrator branch logic,
- live monitor classification logic,
- heartbeat files,
- pending-limit lifecycle rows,
- watchdog process lifecycle rows.

The observed rows are internally consistent.

## Remaining Blockers

- Phase 1D should clarify `LIMIT_PLACED` / pending-intent telemetry so future
  monitoring reports explicitly distinguish `INTERNAL_CANDLE_POLLED_INTENT`
  from native MT5 pending orders.
- Any proposal to cancel pending intents at NY close or dead-zone entry is a
  trading lifecycle change and remains blocked pending owner approval.

## Verdict

`NO_PROMOTION_VERDICT`

