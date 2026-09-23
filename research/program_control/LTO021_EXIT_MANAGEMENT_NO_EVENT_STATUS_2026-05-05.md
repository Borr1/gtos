# LTO-021 Exit-Management No-Event Status - 2026-05-05

**Schema:** `lto021_exit_management_no_event_status_v1`
**Generated:** `2026-06-01T23:45:30.442266+00:00`
**Status:** `OK_EXIT_MANAGEMENT_NO_EVENT_STATUS_DOCUMENTED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Counts

- Candidate rows considered: `538`
- Status rows available: `1234`
- Status rows appended this run: `21`
- No-event documented: `536`
- Event rows present: `2`
- Action required: `0`

## Status Breakdown

- Fill states: `{'NO_FILLED_TRADE': 537, 'FILLED_TRADE_OR_ACCOUNT_HISTORY_PRESENT': 1}`
- BE statuses: `{'NO_FILLED_TRADE': 537, 'NO_BE_TRIGGER_BELOW_1R_TIME_IN_TRADE': 1}`
- Partial-close statuses: `{'NO_FILLED_TRADE': 537, 'NO_PARTIAL_TRIGGER_BELOW_1R_TIME_IN_TRADE': 1}`
- Time-in-trade statuses: `{'NO_FILLED_TRADE': 536, 'EVENT_ROW_PRESENT': 2}`
- Documented no-event codes: `{'NO_BE_TRIGGER': 538, 'NO_CLOSE_EVENT': 536, 'NO_FILLED_TRADE': 537, 'NO_PARTIAL_TRIGGER': 538}`
- Actual event row totals: `{'be_shadow_log': 0, 'partial_close_shadow_log': 0, 'time_in_trade': 2}`

## Boundary

Actual BE, partial-close, and time-in-trade event rows remain in their own logs. This status lane only proves missing/empty event logs are expected no-event states.

## Safety Counters

- no_ai_calls: `True`
- no_canary_required: `True`
- no_execution: `True`
- paid_data_calls: `0`
