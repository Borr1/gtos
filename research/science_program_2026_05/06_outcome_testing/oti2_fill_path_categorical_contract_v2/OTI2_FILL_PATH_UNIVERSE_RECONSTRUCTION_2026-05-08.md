# OTI2 Fill/Path Universe Reconstruction

Candidate rows: `34`.
Source family counts: `{'OTI1_PENDING_INTENT': 22, 'OTI2_ORIGINAL_ROUTER': 1, 'OTI3_USDJPY': 11}`.
Label-assigned rows: `29`.
Blocked rows: `5`.

The four OTI3 same-timestamp rows are admitted to the row-decision packet but remain blocked before label because source-safe tick ordering cannot resolve a single quote row that satisfies multiple touch predicates.
