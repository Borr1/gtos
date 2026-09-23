# Runtime Replay Performance Tables

Checkpoint 203 converts executed repaired-proxy scorer/comparator specs into row-level and aggregate historical replay/simulated-R performance rows.

## Counts

- Row-level performance rows: `1057`
- Aggregate performance rows: `70`
- Rows with proxy-R: `1057`
- Rows without proxy-R: `0`
- Win/loss/flat/no-fill rows: `657` / `400` / `0` / `0`
- Target-first/stop-first/neither/ambiguous rows: `0` / `0` / `0` / `1057`

## Aggregate Decisions

- `KEEP_FOR_BRANCH_LOCAL_REPLAY_REVIEW`: `42`
- `KILL_AVOID_COMPARATOR_AGGREGATE`: `27`
- `KILL_BRANCH_LOCAL_DEFAULT_OFF_AGGREGATE`: `1`

## Geometry Boundary

Exact trade side, timestamp, entry, stop, target, and target/stop ordering are not present in the executed-spec inputs. Rows therefore use replay proxy-R from source close return over the replay denominator, with exact missing fields retained on every row. Rows lacking a usable proxy denominator are emitted with a concrete missing-field disposition.
