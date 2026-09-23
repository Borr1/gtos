# Runtime Replay Geometry Table Execution

Checkpoint 207 executes concrete geometry scorer and avoid tables against held local replay geometry.

## Counts

- Scorer table execution rows: `532`
- Avoid table execution rows: `106`
- Aggregate table execution rows: `41`
- Source gap rows: `0`
- Joined replay geometry rows: `638`

## Continuation

Consume held-replay table execution results into branch-local scorer and avoid observations with row-level source gaps closed or preserved.
