# NOFILL Router Failure And Learning Ledger

Generated: 2026-05-08T14:13:17Z

Promotion posture: `NO_PROMOTION_VERDICT`
Validation posture: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Family Lessons

| route_family | teaches | future_capture_change |
| --- | --- | --- |
| OTI4_OPENING_DRIVE_SOURCE_CORRECTION_OR_CONTRACT_REVISION | Terminal tick evidence cannot substitute for prereg opening-drive range and breakout fields. Future opening-drive packets must carry source-hashed range bars and breakout fields as first-class source contract fields. | Log range_high, range_low, breakout_close_time, breakout_side, range_start/end, parser version, source file hash, and decision-time as-of status before any categorical label lane. |
| OTI1_PENDING_INTENT_CLOSURE_SOURCE_PACKET | Pending final-state labels are insufficient without an explicit entry_touched_at_utc or side-aware quote replay proving no earlier fill touch. | Every pending-intent closure row needs entry_touched_at_utc plus fill/cancel/expiry/horizon timestamps and source hashes. |
| OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT | Price-compatible M1 context is useful source inventory, but bid/ask quote ordering remains the contract boundary for categorical lifecycle labels. | Archive USDJPY tick/quote parquet for all source rows or freeze a conservative quote contract that explicitly states what M1 can and cannot prove. |
| OTI5_DUPLICATE_CONFLICT_SOURCE_IDENTITY_GEOMETRY_AUDIT | Duplicate keys that collapse rows with conflicting geometry/order signatures cannot be rescued by earliest-row selection without denominator leakage. | Separate source identity, duplicate denominator, geometry signature, and row projection keys before any label assignment. |
| OTI2_SEPARATE_FILL_PATH_CATEGORICAL_CONTRACT | Once entry is touched, the row leaves the no-fill lifecycle family even if terminal-area timing looks favorable. | Use a separate fill/path categorical label family with tick-ordered entry, terminal, protective, and ambiguity events while keeping R/performance closed. |

## Global Lessons

- Blocked categorical rows are source-contract evidence, not negative performance evidence.
- A next lane must source-correct or contract-revise before categorical labels expand beyond the accepted 52 rows.
- No row should be relabeled just because local heavy data exists; source hashes, as-of validity, parser contracts, and label-family boundaries remain mandatory.
