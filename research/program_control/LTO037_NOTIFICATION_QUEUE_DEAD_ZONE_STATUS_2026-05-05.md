# LTO-037 Notification Queue Dead-Zone Status - 2026-05-05

**Schema:** `lto037_notification_queue_dead_zone_status_v1`
**Generated:** `2026-06-03T00:02:14.008539+00:00`
**Status:** `OK_NOTIFICATION_QUEUE_DEAD_ZONE_STATUS_DOCUMENTED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Status

- Notification queue status: `NOTIFICATION_QUEUE_STATUS_DOCUMENTED`
- Worker status: `RUNNING`
- Queue status: `QUEUE_EMPTY`
- Dead-zone active: `False`
- Expected worker policy: `RUNNING_REQUIRED_DURING_ACTIVE_WINDOW`
- Watchdog local time: `2026-06-03T08:02:14.000460+08:00`
- Watchdog local day: `Wednesday`
- Queue file status: `QUEUE_FILE_PRESENT`
- Lock status: `LOCK_PRESENT`
- Lock PID alive: `True`
- Action-required codes: `[]`

## Counts

- Status rows available: `31`
- Status rows appended this run: `1`
- Action required: `0`
- Pending alerts: `0`
- Queue rows: `1`
- Terminal markers: `1`

## Boundary

This row classifies notification queue worker state against the watchdog dead-zone policy only. It does not deliver alerts, approve restarts, or validate trading behavior.

## Safety Counters

- no_ai_calls: `True`
- no_canary_required: `True`
- no_execution: `True`
- paid_data_calls: `0`
