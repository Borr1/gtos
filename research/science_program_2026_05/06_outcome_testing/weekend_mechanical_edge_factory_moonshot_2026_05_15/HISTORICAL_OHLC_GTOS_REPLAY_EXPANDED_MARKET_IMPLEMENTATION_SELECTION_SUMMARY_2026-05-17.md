# Expanded-Market Implementation Selection

This checkpoint intersects side-pair, temporal, and intrabar decisions into concrete branch-local implementation-selection rows.

## Counts

- Input side-pair rows: `22610`
- Input temporal rows: `22610`
- Input intrabar rows: `45220`
- Implementation-selection rows: `22610`
- Aggregate rows: `3210`
- Issue rows: `0`

## Decisions

`{"CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_IMPLEMENTATION_SELECTION": 1346, "IMPLEMENT_EXPANDED_MARKET_BRANCH_LOCAL_SIDE_FILTER": 1748, "KILL_EXPANDED_MARKET_IMPLEMENTATION_SELECTION": 783, "REDESIGN_EXPANDED_MARKET_IMPLEMENTATION_SELECTION": 17357, "REDESIGN_EXPANDED_MARKET_IMPLEMENTATION_SELECTION_RECENT_DECAY": 1376}`

## Continuation

Materialize implement rows into branch-local code candidates and preserve non-implement rows as row-level evidence.
