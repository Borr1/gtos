# SI Source Definition Status - 2026-05-04

**Status:** `BLOCKED_WITH_EVIDENCE_AND_TRIGGER`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Decision

`BLOCKED_SOURCE_OR_DEPTH_DEFINITION`; do not use Sierra SI depth in replay synthesis.

## Evidence

| Source | Status | Common max delta | Jaccard |
| --- | --- | --- | --- |
| SIM26-COMEX | SOURCE_OR_DEPTH_DEFINITION_BLOCKED | 25 | 0.967654986522911 |
| SILM26-COMEX | ALTERNATE_LOCAL_SOURCE_NOT_BETTER | 25 | 0.8660714285714286 |

## Unblock Trigger

Obtain explicit SI contract/book definition evidence or a Databento/Sierra same-instrument window whose common-second depth fields match registered tolerances.
