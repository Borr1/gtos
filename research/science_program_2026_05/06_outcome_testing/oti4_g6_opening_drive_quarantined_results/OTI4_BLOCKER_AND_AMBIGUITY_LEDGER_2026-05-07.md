# OTI4 G6 Opening-Drive Blocker And Ambiguity Ledger - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `False`  
**Outcome review opened:** `False`

```json
{
  "artifact_family": "OTI4_G6_OPENING_DRIVE_BLOCKER_AND_AMBIGUITY_LEDGER",
  "blockers": [
    {
      "blocker_id": "OTI4-BLK-001",
      "evidence": "rows_with_range_bars=0 and rows_with_path_bars=0 across 86 records",
      "next_exact_question": "Which source-hashed local M15/M5/M1 OHLC or tick packet covers the May 3-6 2026 frozen opening ranges and path windows for OTG0-PKT-062?",
      "status": "OPEN_LOCAL_SOURCE_BLOCKER"
    },
    {
      "blocker_id": "OTI4-BLK-002",
      "evidence": "opening_drive_packet has only frozen_range_definition, ohlc_source, and status; range_high/range_low/breakout_close_time/breakout_side are absent",
      "next_exact_question": "Which packet builder supplies as-of range_high, range_low, breakout_close_time, breakout_side, spread_at_break, and killed-route exclusion fields without outcome leakage?",
      "status": "OPEN_PACKET_FIELD_BLOCKER"
    },
    {
      "blocker_id": "OTI4-BLK-003",
      "evidence": "86 raw rows collapse to 19 duplicate groups; all duplicate keys end NO_BREAKOUT_ASOF; sample floor is 200",
      "next_exact_question": "After source refresh and killed-route exclusions, does OTG0-PKT-062 reach 200 unique breakout groups under the duplicate_breakout_key policy?",
      "status": "DOCUMENTED_DENOMINATOR_BLOCKER"
    },
    {
      "blocker_id": "OTI4-BLK-004",
      "evidence": "ordered_path_source_id exists but raw path-order labels were not opened",
      "next_exact_question": "If a future lane opens path labels, can it re-derive them from approved OHLC/ticks with terminal-order uncertainty preserved instead of reading hidden path_order_label columns?",
      "status": "DOCUMENTED_NOLEAK_BLOCKER"
    },
    {
      "blocker_id": "OTI4-BLK-005",
      "evidence": "same_m1_ambiguity_flagged rows=6; terminal_order_claim_allowed=false",
      "next_exact_question": "Does a future tick-order source or predeclared conservative-bound policy resolve same-bar rows without guessing terminal event order?",
      "status": "DOCUMENTED_SAME_BAR_UNCERTAINTY"
    }
  ],
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "validation_safe": false
}
```
