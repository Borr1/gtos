# OTI3 G3 Geometry Self Review - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Strongest Reason This Could Be Wrong

The strongest reason OTI3 could be wrong is that local M1 outcome labels are not part of the original G12 accepted G3 packet source_hash; they are a quarantined outcome-source join added by this result lane. That could make the descriptive R summaries a new packetization rather than a pure packet result.

## Status

MITIGATED_BUT_RECORDED_AS_RESIDUAL_G12_PACKETIZATION_QUESTION

## Mitigation Or Residual

The builder records separate M1 source hashes, refuses USDJPY proxy price-scale labels, refuses GBPJPY without local M1, excludes same-M1 terminal-order guesses, marks every primary prereg metric not_computable, and preserves validation_safe=false/outcome_review_opened=false. The residual question remains open for G12: whether future G3 validation needs a separate packet that binds post-decision M1 outcome sources before scoring.
