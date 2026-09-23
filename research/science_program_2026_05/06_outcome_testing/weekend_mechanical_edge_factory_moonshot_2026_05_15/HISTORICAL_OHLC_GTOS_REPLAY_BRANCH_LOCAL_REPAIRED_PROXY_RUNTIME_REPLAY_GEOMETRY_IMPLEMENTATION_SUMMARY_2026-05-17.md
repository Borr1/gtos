# Runtime Replay Geometry Implementation

Checkpoint 205 materializes deterministic geometry repair decisions into branch-local implementation candidates and self-tests.

## Counts

- Geometry implementation rows: `1057`
- Aggregate implementation rows: `70`
- Self-test rows: `1057`
- Self-test pass rows: `1057`

## Implementation Kinds

- `GEOMETRY_AVOID_COMPARATOR_KILL_IMPLEMENTATION`: `262`
- `GEOMETRY_AVOID_INTELLIGENCE_IMPLEMENTATION`: `106`
- `GEOMETRY_DEFAULT_OFF_KILL_IMPLEMENTATION`: `157`
- `GEOMETRY_SCORER_PROTOTYPE_IMPLEMENTATION`: `532`

## Next Action

Apply the branch-local implementation candidates into concrete scorer/comparator tables and source-repair tasks without adding a routing layer.
