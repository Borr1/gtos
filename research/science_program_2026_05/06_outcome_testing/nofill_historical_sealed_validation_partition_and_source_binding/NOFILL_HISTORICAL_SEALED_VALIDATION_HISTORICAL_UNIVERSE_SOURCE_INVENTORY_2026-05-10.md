# NOFILL Historical Universe Source Inventory

Route: `NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING`
Promotion posture: `NO_PROMOTION_VERDICT`

## Summary

```json
{
  "accepted_rows": 225,
  "reject_rows": 65,
  "row_count": 298,
  "source_control_rows": 4,
  "source_impossible_rows": 4,
  "summary": {
    "row_count": 298,
    "session_counts": {
      "london": 90,
      "ny": 154,
      "tokyo": 54
    },
    "side_counts": {
      "LONG": 107,
      "SHORT": 191
    },
    "source_lane_counts": {
      "OTI1_LIFECYCLE": 54,
      "OTI2_RISKBANK": 47,
      "OTI3_G3_GEOMETRY": 69,
      "OTI4_G6_OPENING_DRIVE": 80,
      "OTI5_G6_CUSUM": 48
    },
    "symbol_counts": {
      "GBPJPY": 18,
      "NAS100": 78,
      "US30_cash": 3,
      "USDJPY": 72,
      "XAGUSD": 106,
      "XAUUSD": 21
    },
    "terminal_family_counts": {
      "accepted": 225,
      "reject": 65,
      "source_control": 4,
      "source_impossible": 4
    },
    "terminal_state_counts": {
      "ACCEPTED_INPUT_ONLY_CATEGORICAL": 225,
      "REJECTED_EXCLUDED_FROM_DENOMINATOR": 65,
      "SOURCE_CONTROL_INPUT_ONLY_NO_ENTRY_THROUGH_CANCEL": 1,
      "SOURCE_CONTROL_MARKET_SESSION_EMPTY": 3,
      "SOURCE_IMPOSSIBLE_EXACT_ORDERING": 4
    },
    "used_source_dates": {
      "2026-04-17": 3,
      "2026-04-20": 4,
      "2026-04-30": 20,
      "2026-05-01": 42,
      "2026-05-03": 6,
      "2026-05-04": 129,
      "2026-05-05": 31,
      "2026-05-06": 9
    }
  },
  "unique_duplicate_groups_all_rows": 153,
  "unique_nofill_duplicate_keys_all_rows": 196
}
```
