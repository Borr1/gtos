# NOFILL Router Source Search Ledger

Generated: 2026-05-08T14:13:17Z

Promotion posture: `NO_PROMOTION_VERDICT`
Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Root Searches

| root | exists | match_count | description |
| --- | --- | --- | --- |
| C:\tmp\gtos_otb\NOFILLROUTER\research\science_program_2026_05\06_outcome_testing | True | 251 | worktree outcome-testing artifacts |
| C:\Users\MSI\Documents\ai-trading-agent\data | True | 78 | absolute main data root |
| C:\Users\MSI\Documents\ai-trading-agent\data\ticks | True | 72 | absolute main tick root |
| C:\Users\MSI\Documents\ai-trading-agent\data\mt5_research_exports | True | 139 | read-only MT5 research exports |
| C:\Users\MSI\Documents\ai-trading-agent\shadow_logs | True | 3 | absolute main shadow logs |
| C:\Users\MSI\Documents\ai-trading-agent\exports | True | 90 | absolute exports root |
| C:\tmp | True | 24 | temporary worktrees and prior artifacts |
| C:\SierraChart | True | 123 | SierraChart data root |

## Family Tick Availability

{
  "OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET": {
    "missing": 0,
    "needed_symbol_dates": [
      "GBPJPY|2026-05-04",
      "GBPJPY|2026-05-06",
      "NAS100|2026-05-03",
      "NAS100|2026-05-04",
      "NAS100|2026-05-05",
      "NAS100|2026-05-06",
      "XAUUSD|2026-05-05"
    ],
    "present": 7
  },
  "OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT": {
    "missing": 0,
    "needed_symbol_dates": [
      "XAUUSD|2026-05-05"
    ],
    "present": 1
  },
  "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT": {
    "missing": 2,
    "needed_symbol_dates": [
      "USDJPY|2026-04-17",
      "USDJPY|2026-04-20",
      "USDJPY|2026-04-30",
      "USDJPY|2026-05-01"
    ],
    "present": 2
  },
  "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION": {
    "missing": 0,
    "needed_symbol_dates": [
      "GBPJPY|2026-05-04",
      "GBPJPY|2026-05-06",
      "NAS100|2026-05-03",
      "NAS100|2026-05-04",
      "NAS100|2026-05-05",
      "NAS100|2026-05-06",
      "US30_cash|2026-05-06",
      "USDJPY|2026-05-05",
      "XAGUSD|2026-05-04",
      "XAGUSD|2026-05-05",
      "XAUUSD|2026-05-03",
      "XAUUSD|2026-05-04",
      "XAUUSD|2026-05-05",
      "XAUUSD|2026-05-06"
    ],
    "present": 14
  },
  "OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT": {
    "missing": 0,
    "needed_symbol_dates": [
      "NAS100|2026-05-04",
      "XAGUSD|2026-05-04"
    ],
    "present": 2
  }
}

## Pending Intent Field Search

{
  "materialized_entry_touched_at_utc_found": false,
  "required_fields": [
    "entry_touched_at_utc",
    "filled_at_utc",
    "cancelled_at_utc",
    "expired_at_utc",
    "pending_created_at_utc",
    "pending_active_from_utc",
    "pending_active_until_utc"
  ]
}

## Conclusions

- `OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION`: Local tick source is present for all OTI4 symbol-date probes, but current accepted packet still lacks source-hashed prereg opening-drive fields.
- `OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET`: Pending lifecycle logs are present, but entry_touched_at_utc is not materialized; local ticks are present for family symbol-date probes and can be used by a future source packet if contract-safe.
- `OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT`: USDJPY M1 CSV context exists and matches expected hash; USDJPY tick parquet exists for 2026-04-30 and 2026-05-01 rows but is absent for 2026-04-17 and 2026-04-20 rows.
- `OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT`: Duplicate conflict is denominator/source-identity ambiguity, not missing tick data.
- `OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT`: The single XAUUSD row has local tick source available, but it requires a separate label family contract because entry touch moves it out of no-fill closure.
