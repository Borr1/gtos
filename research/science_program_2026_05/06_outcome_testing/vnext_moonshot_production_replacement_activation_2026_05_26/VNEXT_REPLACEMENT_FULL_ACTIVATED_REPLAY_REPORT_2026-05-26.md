# vNext Replacement Stage05 Full Activated Historical Replay

Generated: `2026-05-26T12:39:47Z`

## Coverage

- Full denominator rows: `903163`
- Full candidate rows represented: `253234`
- Dynamic policy replay rows attached: `214536`
- Activated runtime-effect rows: `15799`
- Shards: `45`

## Scenario Expectancy

- Old GTOS live-current J46/J49: `0.1802181092521316`
- Legacy fixed 1.5R comparator: `0.3765151394122705`
- Moonshot BE-after-trigger: `0.3894716001928694`
- Condition router challenger: `0.4167408770181886`
- Activated source-bound primary rows: `-0.4555420048452025`

## Boundary

Every Stage04 bar-close candidate is represented. Dynamic policy performance is attached only when the upstream ordered-OHLC policy replay row exists; missing or source-repair rows remain explicit exclusions rather than silent shrinkage.

Fixed 1.5R remains a comparator only. Old GTOS live-current J46/J49 is the rollback baseline, not the activated target.
