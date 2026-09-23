# LTO-009 Context/Control Audit - 2026-05-05

**Schema:** `lto009_context_control_audit_v1`
**Generated:** `2026-06-01T23:36:17.378526+00:00`
**Status:** `ACTION_REQUIRED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Counts

- Context rows considered: `538`
- Audit rows available: `7103`
- Audit rows appended this run: `281`
- Complete: `0`
- Complete with documented limitations: `207`
- Action required: `331`

## Control Boundary

- Control-only rows: `538`
- No-promotion rows: `538`
- Direct strategy-validation status counts: `{'NOT_DIRECT_STRATEGY_VALIDATION': 538}`
- Source evidence-class counts: `{'CONTROL_ONLY': 490, 'CROSS_INSTRUMENT_CONTEXT': 48}`

## Context Families

`{'CL:SOURCE_NOT_CAPTURED_AT_DECISION_TIME': 538, 'VIX:SOURCE_NOT_CAPTURED_AT_DECISION_TIME': 538, 'VXM:SOURCE_NOT_CAPTURED_AT_DECISION_TIME': 538, 'ZN:SOURCE_NOT_CAPTURED_AT_DECISION_TIME': 538}`

## Exploratory Outcomes

`{'PATH_NOT_JOINED': 50, 'continued_without_entry_touch_to_tp_area': 80, 'entry_touched_then_reached_tp1': 87, 'entry_touched_tp_and_sl_m15_ambiguous': 221, 'entry_touched_unresolved': 22, 'no_touch_stayed_below_entry': 1, 'went_through_entry_and_continued_to_sl': 77}`

## Limitations

- Existing CL/ZN/VIX/VXM point-in-time values are not captured in the current 2026-05-04 context rows.
- Existing rows remain usable only as control/exploratory context, not direct strategy validation.
- Legacy rows use `CROSS_INSTRUMENT_CONTEXT`; audit rows normalize them to `CONTROL_ONLY` without rewriting the source log.

## Safety Counters

- no_ai_calls: `True`
- no_canary_required: `True`
- no_execution: `True`
- paid_data_calls: `0`

## Action Required Examples

```json
[
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "GBPJPY_2026-05-31T22:30:00Z",
    "decision_time_utc": "2026-05-31T22:30:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "GBPJPY"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "JP225_2026-05-31T22:30:00Z",
    "decision_time_utc": "2026-05-31T22:30:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "JP225"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "XAUUSD_2026-05-31T22:30:00Z",
    "decision_time_utc": "2026-05-31T22:30:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "XAUUSD"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "BTCUSD_2026-05-31T23:15:00Z",
    "decision_time_utc": "2026-05-31T23:15:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "BTCUSD_2026-05-31T23:45:00Z",
    "decision_time_utc": "2026-05-31T23:45:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "ETHUSD_2026-05-31T23:45:00Z",
    "decision_time_utc": "2026-05-31T23:45:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "ETHUSD"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "EURJPY_2026-06-01T00:00:00Z",
    "decision_time_utc": "2026-06-01T00:00:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "EURJPY"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "GBPJPY_2026-06-01T00:00:00Z",
    "decision_time_utc": "2026-06-01T00:00:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "GBPJPY"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "JP225_2026-05-31T22:45:00Z",
    "decision_time_utc": "2026-05-31T22:45:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "JP225"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "JP225_2026-05-31T23:00:00Z",
    "decision_time_utc": "2026-05-31T23:00:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "JP225"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "NAS100_2026-05-31T23:15:00Z",
    "decision_time_utc": "2026-05-31T23:15:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "NAS100"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "NAS100_2026-06-01T00:00:00Z",
    "decision_time_utc": "2026-06-01T00:00:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "NAS100"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "AUDJPY_2026-06-01T00:15:00Z",
    "decision_time_utc": "2026-06-01T00:15:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "AUDJPY"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "AUDJPY_2026-06-01T00:30:00Z",
    "decision_time_utc": "2026-06-01T00:30:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "AUDJPY"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "AUDJPY_2026-06-01T01:00:00Z",
    "decision_time_utc": "2026-06-01T01:00:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "AUDJPY"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "AUDJPY_2026-06-01T01:15:00Z",
    "decision_time_utc": "2026-06-01T01:15:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "AUDJPY"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "BTCUSD_2026-06-01T01:15:00Z",
    "decision_time_utc": "2026-06-01T01:15:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "CHFJPY_2026-06-01T00:15:00Z",
    "decision_time_utc": "2026-06-01T00:15:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "CHFJPY"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "CHFJPY_2026-06-01T00:30:00Z",
    "decision_time_utc": "2026-06-01T00:30:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "CHFJPY"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "CHFJPY_2026-06-01T00:45:00Z",
    "decision_time_utc": "2026-06-01T00:45:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "CHFJPY"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "ETHUSD_2026-06-01T01:15:00Z",
    "decision_time_utc": "2026-06-01T01:15:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "ETHUSD"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "EURJPY_2026-06-01T00:15:00Z",
    "decision_time_utc": "2026-06-01T00:15:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "EURJPY"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "GBPJPY_2026-06-01T00:30:00Z",
    "decision_time_utc": "2026-06-01T00:30:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "GBPJPY"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "GBPJPY_2026-06-01T01:00:00Z",
    "decision_time_utc": "2026-06-01T01:00:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "GBPJPY"
  },
  {
    "action_required_codes": [
      "CONTEXT_ROW_PROMOTION_VERDICT_NOT_NO_PROMOTION"
    ],
    "candidate_id": "JP225_2026-06-01T00:15:00Z",
    "decision_time_utc": "2026-06-01T00:15:00Z",
    "direct_validation_problem_paths": [],
    "symbol": "JP225"
  }
]
```
