# Sierra Depth Ladder Snapshot Probe

Generated UTC: `2026-05-15T20:29:00Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: prior-clear local Sierra `.depth` boundary-window ladder reconstruction only. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `input_local_depth_feature_rows`: `882`
- `prior_clear_input_rows`: `489`
- `no_prior_clear_blocker_rows`: `393`
- `ladder_feature_rows`: `489`
- `blocker_rows`: `419`
- `file_rows`: `58`
- `bucket_rows`: `4`
- `question_rows`: `4`

## Buckets

- `LADDER_BOUNDARY60_BLOCKED_NO_PRIOR_CLEAR_BOOK_BEFORE_WINDOW`: `393`
- `LADDER_BOUNDARY60_EVENT_DEPTH10_BALANCED`: `454`
- `LADDER_BOUNDARY60_EVENT_DEPTH10_IMBALANCED`: `9`
- `LADDER_BOUNDARY60_NO_EVENT_SAMPLES`: `52`

## Interpretation Boundary

- Prior-clear windows now have top-of-book/top-10/top-20 boundary60 snapshot descriptors from local Sierra `.depth` records.
- Full per-second median ladder reconstruction was attempted and timed out after 20 minutes; this packet is the feasible no-lookahead boundary proxy.
- No-prior-clear windows remain blockers; the packet does not infer a book from an empty state.
- The result is a descriptor/control packet only, not a validation or trading-system promotion.

## Next Same-Resource Work

- Join ladder imbalance/wall/thinness buckets back to command-flow controls and same-source neighbors.
- Treat no-prior-clear rows as exact earlier-source-history requirements.
- Stress the single-pass ladder method against a smaller independent parser fixture before broader reuse.
