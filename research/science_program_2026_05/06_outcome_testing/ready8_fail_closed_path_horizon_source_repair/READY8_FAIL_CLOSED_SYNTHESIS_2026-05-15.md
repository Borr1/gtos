# READY8 Fail-Closed Path/Horizon Source Repair

Date: 2026-05-15

Evidence class: `READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_ONLY`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Result

- Accepted fail-closed/excluded inventory preserved: `35,811` rows (`30,560` target fail-closed plus `5,251` computable per-card fail-closed exclusions).
- Current local Sierra SCID search recovered `220` missing M15 bar windows without committing raw market blobs.
- Recovered bars make `5,320` fail-closed target rows repair-candidate computable pending G12 audit.
- `25,240` target rows remain fail-closed after the current approved local search.
- `5,251` role-excluded rows are exactly routed as denominator-policy exclusions, not path/horizon source gaps.

## Sensitivity

If G12 accepts the recovered source bars, target computable rows would move from `162,336` to `167656`, and target fail-closed rows would move from `30,560` to `25240`. This is neutral target-movement sensitivity only, not R/PnL/win-rate/expectancy, validation, promotion, or live readiness.

## Source Search

Recovered unique bars by source summary:

```json
{
  "EURUSD": {
    "needed_missing_bar_ends": 32,
    "recovered_bar_count": 32,
    "source_status": "SOURCE_FILE_SEARCHED_AND_HASHED_BY_RECOVERED_BAR_RECORDS",
    "still_missing_bar_count": 0
  },
  "GBPUSD_6B": {
    "needed_missing_bar_ends": 112,
    "recovered_bar_count": 32,
    "source_status": "SOURCE_FILE_SEARCHED_AND_HASHED_BY_RECOVERED_BAR_RECORDS",
    "still_missing_bar_count": 80
  },
  "NAS100_NQ": {
    "needed_missing_bar_ends": 112,
    "recovered_bar_count": 32,
    "source_status": "SOURCE_FILE_SEARCHED_AND_HASHED_BY_RECOVERED_BAR_RECORDS",
    "still_missing_bar_count": 80
  },
  "US30_YM": {
    "needed_missing_bar_ends": 112,
    "recovered_bar_count": 32,
    "source_status": "SOURCE_FILE_SEARCHED_AND_HASHED_BY_RECOVERED_BAR_RECORDS",
    "still_missing_bar_count": 80
  },
  "USDJPY_6J": {
    "needed_missing_bar_ends": 112,
    "recovered_bar_count": 32,
    "source_status": "SOURCE_FILE_SEARCHED_AND_HASHED_BY_RECOVERED_BAR_RECORDS",
    "still_missing_bar_count": 80
  },
  "XAGUSD_SI": {
    "needed_missing_bar_ends": 164,
    "recovered_bar_count": 28,
    "source_status": "SOURCE_FILE_SEARCHED_AND_HASHED_BY_RECOVERED_BAR_RECORDS",
    "still_missing_bar_count": 136
  },
  "XAUUSD_GC": {
    "needed_missing_bar_ends": 112,
    "recovered_bar_count": 32,
    "source_status": "SOURCE_FILE_SEARCHED_AND_HASHED_BY_RECOVERED_BAR_RECORDS",
    "still_missing_bar_count": 80
  }
}
```

Remaining unrecoverable proof rows: `536` unique bar windows. Each requires an approved source-hashed alternate archive/export or remains fail-closed; OHLC cannot be inferred from adjacent bars.

## Next Gate

`research/science_program_2026_05/04_goal_prompts/G12_READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR_AUDIT_GOAL_PROMPT_2026-05-15.md` audits this repair packet before any R7 expanded packet may consume the recovered rows.
