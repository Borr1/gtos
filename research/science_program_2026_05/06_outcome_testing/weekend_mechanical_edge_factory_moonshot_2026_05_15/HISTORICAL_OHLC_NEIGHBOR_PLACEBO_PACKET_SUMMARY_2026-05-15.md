# Historical OHLC Neighbor/Placebo Control Packet

Generated UTC: `2026-05-15T15:28:24Z`

Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

Evidence class: `HISTORICAL_OHLC_NEIGHBOR_PLACEBO_CONTROL_PACKET`

Neighbor/placebo discovery control packet only. This is not sealed validation, R/PnL, expectancy, fillability, live-readiness, or a promotion verdict.

## Counts

- `input_route_queue_rows`: `477`
- `event_groups_with_rows`: `477`
- `placebo_packet_rows`: `477`
- `survivor_queue_rows`: `44`
- `symbols_loaded`: `24`

## Placebo Status

- `DESCRIPTIVE_FAILS_OR_MIXED_PLACEBO_DIRECTIONAL`: `407`
- `DESCRIPTIVE_FAILS_OR_MIXED_PLACEBO_EXCURSION`: `8`
- `DESCRIPTIVE_SURVIVES_NEIGHBOR_AND_PERMUTED_DIRECTIONAL`: `44`
- `INSUFFICIENT_PLACEBO_COVERAGE`: `18`

## Boundary

- The survivor queue is a research queue, not a trade selector.
- Same-date/session placebo controls reduce obvious timing bias but do not replace sealed validation.
- No row includes spread, fillability, slippage, commission, or lifecycle truth.
