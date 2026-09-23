# LTO-022 Session Volatility / Sweep Status - 2026-05-05

**Schema:** `lto022_session_volatility_sweep_status_v1`
**Generated:** `2026-06-03T00:02:13.034997+00:00`
**Status:** `OK_SESSION_VOL_SWEEP_STATUS_DOCUMENTED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Target date:** `2026-06-02`

## Counts

- Status rows built: `2`
- Status rows available: `36`
- Status rows appended this run: `2`
- Event rows: `0`
- No-event rows: `5`
- Action required: `0`
- CSV no-event rows written: `{'session_volatility_log.csv': 3, 'sweep_divergence_log.csv': 2}`

## Status Breakdown

- Coverage status counts: `{'SESSION_VOL_SWEEP_COVERAGE_COMPLETE': 2}`
- Source counts: `{'session_volatility': 1, 'sweep_divergence': 1}`
- Source-file status counts: `{'SOURCE_FILE_PRESENT': 2}`
- Action-required codes: `{}`

## Source Rows

- `session_volatility` `2026-06-02`: coverage `SESSION_VOL_SWEEP_COVERAGE_COMPLETE`, events `0`, no-events `3`, latest run `2026-06-03T00:02:13.020183+00:00`
- `sweep_divergence` `2026-06-02`: coverage `SESSION_VOL_SWEEP_COVERAGE_COMPLETE`, events `0`, no-events `2`, latest run `2026-06-03T00:02:13.020183+00:00`

## Boundary

This audit proves H25/H16 monitor cadence and explicit event/no-event coverage for the configured symbol/session/date lanes. It does not validate a strategy edge or change trading decisions.

## Safety Counters

- no_ai_calls: `True`
- no_canary_required: `True`
- no_execution: `True`
- paid_data_calls: `0`
