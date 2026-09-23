# Runtime Replay Geometry Tables

Checkpoint 206 splits branch-local geometry implementation candidates into concrete scorer, avoid-intelligence, kill, and redirection task tables.

## Counts

- Scorer table rows: `532`
- Avoid-intelligence table rows: `106`
- Kill table rows: `419`
- Redirection task rows: `41`

## Continuation

Execute scorer and avoid tables against held local replay rows or emit row-level source gaps.
