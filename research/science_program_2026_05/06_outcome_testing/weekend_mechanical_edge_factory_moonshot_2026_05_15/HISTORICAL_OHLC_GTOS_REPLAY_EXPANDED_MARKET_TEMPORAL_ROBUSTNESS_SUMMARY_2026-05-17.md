# Expanded-Market Temporal Robustness

This checkpoint replays CP217 side-pair rows through full, early-half, recent-half, and recent-quarter chronological folds from the same OHLC source geometry.

## Counts

- Input performance rows: `45220`
- Input side-pair rows: `22610`
- Temporal robustness rows: `22610`
- Temporal fold rows: `90440`
- Aggregate rows: `3373`
- Issue rows: `0`
- Unique temporal profile keys replayed: `4764`

## Decisions

`{"IMPLEMENT_EXPANDED_MARKET_TEMPORAL_SIDE_FILTER": 5517, "KILL_EXPANDED_MARKET_TEMPORAL_DECAY": 667, "REDESIGN_EXPANDED_MARKET_TEMPORAL_GEOMETRY": 12143, "REDESIGN_EXPANDED_MARKET_TEMPORAL_INSTABILITY": 2306, "REDESIGN_EXPANDED_MARKET_TEMPORAL_RECENT_DECAY": 1140, "REDESIGN_EXPANDED_MARKET_TEMPORAL_UNDERPOWERED": 837}`

## Fold Decisions

`{"IMPLEMENT_EXPANDED_MARKET_TEMPORAL_FOLD_CONFIRMATION": 64740, "REDESIGN_EXPANDED_MARKET_TEMPORAL_FOLD_INSTABILITY": 23995, "REDESIGN_EXPANDED_MARKET_TEMPORAL_FOLD_UNDERPOWERED": 1705}`

## Continuation

Use temporal-stable and temporally failed rows to drive the next numeric robustness or replay-implementation plate.
