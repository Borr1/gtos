# Sierra Depth Event-Window Replay

Generated UTC: `2026-05-15T19:26:25Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: Sierra `.depth` event-window replay and source-gap repair only. No strategy validation, R/PnL, expectancy, live-readiness, promotion, or sprint completion.

## Counts

- `request_rows`: `10382`
- `route_c_request_rows`: `2143`
- `sierra_scid_request_rows`: `8239`
- `local_depth_request_rows`: `882`
- `missing_depth_request_rows`: `9500`
- `unique_local_depth_files`: `75`
- `feature_rows`: `882`
- `file_rows`: `75`
- `source_gap_rows`: `1106`
- `blocker_rows`: `9535`
- `bucket_rows`: `7`
- `question_rows`: `5`

## Buckets

- `DEPTH_COMMAND_PROXY_EVENT15_ASK_UPDATE_DOMINANT`: `68`
- `DEPTH_COMMAND_PROXY_EVENT15_BALANCED_OR_LOW_QUANTITY`: `623`
- `DEPTH_COMMAND_PROXY_EVENT15_BID_UPDATE_DOMINANT`: `156`
- `DEPTH_COMMAND_PROXY_NO_PRE60_OR_EVENT15_RECORDS`: `8`
- `DEPTH_COMMAND_PROXY_PRE60_ONLY_EVENT15_EMPTY`: `27`
- `LOCAL_DEPTH_AVAILABLE_COMMAND_FLOW_REPLAYED`: `882`
- `MISSING_DEPTH_FILE_SOURCE_DATE_GAP`: `9500`

## Interpretation

- The full request ledger preserves every aligned Route C and Sierra event row before local availability filtering.
- Locally available `.depth` source-date windows were replayed from audited parser records using pre-decision windows only.
- Missing `.depth` files are exact source-date gaps; no SCID/OHLC proxy was used to infer depth.
- Rows without a prior `CLEAR_BOOK` before the window are preserved but must be split before downstream feature claims.

## Next Same-Resource Work

- Join depth feature buckets back to Route C residual families and run same-source/date/time controls.
- Search exact source-date gaps across alternate local roots before declaring them forward-capture only.
- Convert clean depth descriptors into a no-promotion control packet, not a live rule.
