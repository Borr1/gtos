# Sierra Depth Ladder In-Window CLEAR_BOOK Repair

Generated UTC: `2026-05-15T22:07:24Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: same-source Sierra `.depth` source-control repair only. No validation, R/PnL, expectancy, live-readiness, promotion, or completion claim.

## Counts

- `input_no_prior_clear_rows`: `393`
- `requirement_earlier_book_rows`: `393`
- `row_rows`: `393`
- `feature_rows`: `385`
- `blocker_rows`: `51`
- `file_rows`: `75`
- `rows_with_in_window_clear_before_canonical`: `385`
- `repaired_full_pre_and_event_rows`: `342`
- `repaired_event_only_rows`: `0`
- `remaining_blocker_primary_rows`: `51`
- `bucket_rows`: `60`
- `question_rows`: `7`

## Primary Repair Status

- `BLOCKED_IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY_BUT_NO_EVENT_SAMPLES`: `43`
- `BLOCKED_NO_IN_WINDOW_CLEAR_BEFORE_CANONICAL`: `8`
- `REPAIRED_IN_WINDOW_CLEAR_FULL_PRE_AND_EVENT_BOUNDARY60`: `342`

## Feature Buckets

- `IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY60_DEPTH10_BALANCED`: `324`
- `IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY60_DEPTH10_IMBALANCED`: `18`
- `IN_WINDOW_CLEAR_EXACT_EVENT_BOUNDARY60_NO_EVENT_SAMPLES`: `43`

## Interpretation Boundary

- The input denominator is every `393` no-prior-clear local Sierra depth row from the prior ladder probe.
- A row is repaired only when a real in-window `CLEAR_BOOK` occurs before the event boundary window required for exact reconstruction.
- Rows with late clears keep partial post-clear sample counts as source diagnostics only; they are not boundary60 ladder features.
- Rows with no in-window clear remain exact earlier-source-history/file-start-state requirements.
- This packet is descriptor/source-control intelligence only and does not alter live behavior.

## Next Same-Resource Work

- Join repaired in-window-clear rows into the ladder Route C denominator and mutation-design ledgers.
- Split remaining earlier-book blockers by no-clear, late-clear, no-sample, and metric-missing families.
- Continue exact missing `.depth` source-date acquisition from owned/free/current roots.
