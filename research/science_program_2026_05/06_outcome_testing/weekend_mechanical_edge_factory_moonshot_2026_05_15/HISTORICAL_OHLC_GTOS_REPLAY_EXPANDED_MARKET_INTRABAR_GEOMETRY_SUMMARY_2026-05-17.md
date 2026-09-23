# Expanded-Market Intrabar Geometry

This checkpoint replays CP216 broad-market rows with OHLC high-low target/stop path geometry, preserving ambiguous same-bar cases explicitly.

## Counts

- Input performance rows: `45220`
- Intrabar geometry rows: `45220`
- Aggregate rows: `5732`
- Source/access proof rows: `0`
- Unique intrabar profile keys replayed: `4764`

## Decisions

`{"CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_INTRABAR": 6320, "IMPLEMENT_EXPANDED_MARKET_INTRABAR_SCORER": 3552, "KILL_EXPANDED_MARKET_INTRABAR_BRANCH": 2052, "REDESIGN_EXPANDED_MARKET_INTRABAR_CONCENTRATION": 1920, "REDESIGN_EXPANDED_MARKET_INTRABAR_GEOMETRY": 31132, "REDESIGN_EXPANDED_MARKET_INTRABAR_UNDERPOWERED": 244}`

## Path Counts

`{"AMBIGUOUS_TARGET_AND_STOP_SAME_BAR": 9193728, "NEITHER_INTRABAR_TARGET_NOR_STOP_TOUCHED_CLOSE_EXIT": 19138140, "STOP_FIRST_INTRABAR_PATH": 94521915, "TARGET_FIRST_INTRABAR_PATH": 94521915}`

## Continuation

Compare intrabar geometry, side-pair, and temporal decisions into branch-local implementation-selection rows.
