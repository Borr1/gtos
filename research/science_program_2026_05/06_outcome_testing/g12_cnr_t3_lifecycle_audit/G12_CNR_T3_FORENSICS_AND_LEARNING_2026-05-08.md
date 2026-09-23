# G12 CNR T3 Forensics And Learning - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

## decision

```json
"ACCEPT_LEARNING_AS_FAILURE_ANATOMY_ONLY"
```

## status

```json
"PASS"
```

## categorical_learning

```json
[
  "The six accepted OTI8 rows were not terminal-free forever; they became stop_after_original_horizon under the frozen extension rule.",
  "The rows all share one May 5 NY XAGUSD SHORT duplicate group, so the evidence is narrow failure anatomy, not a broad strategy result.",
  "The late-stop path suggests the original ordered horizon was too short to distinguish no-terminal from delayed adverse terminal for this group.",
  "The 298 blocked rows are learning inventory for other lifecycle contracts, not failed T3 target/stop rows."
]
```

## six_row_context

```json
{
  "original_horizon_end_utc_values": [
    "2026-05-05T20:30:00Z",
    "2026-05-05T20:30:00Z",
    "2026-05-05T20:45:00Z",
    "2026-05-05T20:45:00Z",
    "2026-05-05T21:00:00Z",
    "2026-05-05T21:00:00Z"
  ],
  "row_count": 6,
  "sides": [
    "SHORT"
  ],
  "symbols": [
    "XAGUSD"
  ],
  "terminal_event_utc_values": [
    "2026-05-05T23:22:34.677000Z",
    "2026-05-05T23:22:34.677000Z",
    "2026-05-06T00:55:10.729000Z",
    "2026-05-06T00:55:10.729000Z",
    "2026-05-05T23:22:30.264000Z",
    "2026-05-05T23:22:30.264000Z"
  ],
  "unique_duplicate_groups": [
    "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222"
  ]
}
```

## what_six_stop_after_original_horizon_labels_prove

```json
[
  "The six packet rows are exactly the accepted OTI8 CNR061 original-horizon no-terminal rows.",
  "The frozen source contract can extend those rows into categorical lifecycle labels without R scoring.",
  "Under the SHORT ask-side terminal rule, each row first hits the original stop after the original ordered horizon.",
  "The original OTI8 no-terminal state was horizon-limited for this one May 5 NY XAGUSD duplicate group."
]
```

## what_six_stop_after_original_horizon_labels_do_not_prove

```json
[
  "It does not prove R, win rate, expectancy, DSR, PBO, validation, promotion, or live edge.",
  "It does not use broker actual-R, account history, live trade results, live order state, or hidden path labels.",
  "It does not score or rescue the 94 G12-blocked CNR061 rows.",
  "It does not prove T1 fixed-R, T2 structural-level targets, or E2/E3/E4 timing telemetry.",
  "It does not justify thresholds, selectors, risk, prompt, execution, or live-gate changes."
]
```

## open_questions_reduced_to_routes

```json
[
  {
    "decision": "RUN_FIRST_AS_SOURCE_CONTRACT_ONLY",
    "hard_boundaries": [
      "Do not reuse CNR_T3_LIFECYCLE_NO_TERMINAL_EXTENSION_V1 labels.",
      "Do not compute R or score blocked rows.",
      "Do not use broker/account/live/hidden labels.",
      "Keep validation_safe=false and live_effect=false."
    ],
    "priority": 1,
    "route": "SEPARATE_NO_FILL_STILL_PENDING_LIFECYCLE_CONTRACT",
    "why": "It can use the 298 exact-blocked lifecycle-like rows without relabeling them as T3 target/stop outcomes. It should split no-fill, no-entry, still-pending, source-blocked, and terminal-order-unclaimed families under a new frozen contract."
  },
  {
    "decision": "BLOCKED_UNTIL_FIXED_R_AND_STOP_SOURCE_PACKET_FREEZE",
    "exact_next_input": "Frozen fixed-R multiple, stop-source convention, executable quote source, cost convention, and no-leak row schema.",
    "priority": 2,
    "route": "CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE_PACKET"
  },
  {
    "decision": "BLOCKED_UNTIL_ASOF_STRUCTURAL_LEVEL_SNAPSHOT_BUILDER",
    "exact_next_input": "Source-hashed structural level id, timestamp, hierarchy rank, selection rule id, and as-of snapshot hash.",
    "priority": 3,
    "route": "CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL_PACKET"
  },
  {
    "decision": "FUTURE_TELEMETRY_REQUIRED_BEFORE_RESULT_ROWS",
    "exact_next_input": "Signal emission timestamp, decision latency fields, and pretouch trigger source fields captured before outcome opening.",
    "priority": 4,
    "route": "CNR_E2_E3_E4_TELEMETRY"
  }
]
```
