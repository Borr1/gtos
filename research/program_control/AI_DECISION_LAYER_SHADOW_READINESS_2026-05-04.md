# AI Decision Layer Shadow Readiness - 2026-05-04

**Status:** `RESEARCH_ARTIFACT_DONE`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Boundary

- PrimaryAnalyzer behavior unchanged.
- Prompt behavior unchanged.
- Component 3B debate not run.

## Required Shadow Labels

- mechanical replay outcome lane
- AI candidate/reject decision
- POI quality at decision time
- FVG/OB confluence bucket
- regime
- orderflow availability flag
- pending-limit lifecycle state
- broker actual-R where available

## Trigger

Need paired forward rows with AI decision, mechanical comparator, lifecycle state, and actual/synthetic label separation.
