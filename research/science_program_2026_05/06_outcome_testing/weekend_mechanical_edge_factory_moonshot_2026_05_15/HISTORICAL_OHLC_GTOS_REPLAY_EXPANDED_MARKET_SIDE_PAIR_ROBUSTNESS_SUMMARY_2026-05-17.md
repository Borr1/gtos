# Expanded-Market Side-Pair Robustness

This checkpoint converts CP216 performance rows into row-preserving LONG-versus-SHORT robustness comparisons across source path, symbol, timeframe, session, horizon, and source component.

## Counts

- Input performance rows: `45220`
- Side-pair rows: `22610`
- Issue rows: `0`
- Aggregate rows: `3302`
- Paired input performance rows: `45220`
- Unpaired input performance rows: `0`
- Source paths represented: `282`
- Symbols represented: `44`

## Decisions

`{"CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_SIDE_PAIR": 126, "IMPLEMENT_EXPANDED_MARKET_SIDE_FILTER": 7669, "REDESIGN_EXPANDED_MARKET_SIDE_PAIR_CONCENTRATION": 960, "REDESIGN_EXPANDED_MARKET_SIDE_PAIR_GEOMETRY": 13733, "REDESIGN_EXPANDED_MARKET_SIDE_PAIR_UNDERPOWERED": 122}`

## Winner Sides

`{"LONG": 18751, "SHORT": 3859}`

## Continuation

Consume these paired robustness rows into the next numeric robustness plate.
