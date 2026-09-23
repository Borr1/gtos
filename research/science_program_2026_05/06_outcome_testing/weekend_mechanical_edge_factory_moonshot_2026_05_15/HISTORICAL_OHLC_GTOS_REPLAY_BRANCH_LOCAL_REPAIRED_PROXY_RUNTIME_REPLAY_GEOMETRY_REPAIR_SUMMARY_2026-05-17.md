# Runtime Replay Geometry Repair

Checkpoint 204 streams reachable source CSVs to derive proxy entry, target, stop, and path-order repair rows for every Checkpoint 203 performance row.

## Counts

- Geometry repair rows: `1057`
- Aggregate geometry rows: `70`
- Source path scan rows: `7`
- Deterministic geometry-R rows: `1057`
- Ambiguous rows: `0`
- No-fill rows: `0`
- Target-first / stop-first / neither: `794` / `263` / `0`

## Aggregate Decisions

- `KILL_AVOID_COMPARATOR_FROM_GEOMETRY`: `17`
- `KILL_DEFAULT_OFF_FROM_GEOMETRY`: `12`
- `REDESIGN_AVOID_COMPARATOR_FROM_GEOMETRY`: `10`
- `REDESIGN_DEFAULT_OFF_FROM_GEOMETRY`: `31`

## Repair Boundary

Rows use source-file first open as proxy entry and one-denominator proxy target/stop levels. Same-bar target/stop hits remain explicit intrabar-order repair tasks with source path, hash, key, and missing field retained.
