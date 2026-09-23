# OTI4 Opening-Drive Failure And Learning Ledger

- Generated at UTC: `2026-05-08T14:58:23Z`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- Validation safe: `false`
- Outcome review opened: `false`
- Live effect: `false`

- Records exact blockers and future contract terms without promotion claims.

```json
{
  "artifact_family": "OTI4_OPENING_DRIVE_FAILURE_AND_LEARNING_LEDGER",
  "future_contract_terms": {
    "allow_separate_future_partial_range_family_only_with_new_preregistration": true,
    "exclude_decision_before_range_close": true,
    "exclude_no_breakout_or_side_mismatch_from_opening_drive_continuation_family": true,
    "require_source_hashed_range_bars_and_breakout_scan_bars": true
  },
  "generated_at_utc": "2026-05-08T14:58:23Z",
  "lane_id": "OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION",
  "live_effect": false,
  "outcome_review_opened": false,
  "parser_version": "oti4_opening_drive_tick_mid_m1_source_contract_v1_2026_05_08",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "source_closure_learning": [
    "Tick parquet repairs the missing opening-drive range/breakout/as-of source fields for 69 of 80 no-fill blocked OTI4 rows.",
    "Eight rows are impossible under the frozen full-range contract because the decision timestamp is before the 30-minute range close.",
    "Three 2026-05-03 rows are exact local source gaps: the tick files begin at 22:00 UTC, while the frozen NY range is 13:00-13:30 UTC, and targeted local CSV/OHLC search found no approved coverage.",
    "The stale duplicate group field NO_BREAKOUT_ASOF is not source-safe after tick reconstruction; future lanes must use source_contract_key and blocker status."
  ],
  "source_contract_id": "OTI4_OPENING_DRIVE_TICK_RANGE_BREAKOUT_SOURCE_CONTRACT_V1",
  "validation_safe": false
}
```
