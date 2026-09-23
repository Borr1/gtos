# Expanded-Market Source Expansion Execution

Generated: 2026-05-18T03:20:49Z

This checkpoint consumes the CP265 source-expansion acquisition-proof rows and scores every reachable same-symbol/timeframe alternate OHLC source discovered locally. Rows without an alternate local source are preserved as row-level source-gap proof.

## Counts

- Input source-expansion proof rows: `3348`
- Discovered local OHLC CSV sources: `301`
- Source-expansion execution rows: `4194`
- Execution rows with simulated R: `4182`
- Source-gap proof rows: `792`
- Input consumption rows: `3348`
- Aggregate rows: `1128`
- Issue rows: `0`

## Decisions

`{"CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_SOURCE_EXPANSION": 48, "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_ACQUIRED_PROXY_R": 9, "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_CONCENTRATION": 3924, "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_LOCAL_SOURCE_GAP": 792, "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_REPLAY_IMPLEMENTATION": 12, "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_SIGNAL_GEOMETRY": 201}`

## Continuation

Continue to the next highest-value numeric source/replay plate after this checkpoint is committed.
