# G12 OTI7 CNR Post-Result Decision Ledger - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

## Decision

`ACCEPT_AS_QUARANTINED_NEGATIVE_DISCOVERY_EVIDENCE`

## Reasons

- 102 accepted rows exactly match G12 ready shortlist
- 6098 blocked rows have zero row-sha and row-number overlap with OTI7 result rows
- source hashes, quote recomputation, no-leak flags, duplicate policy, and geometry/quote-side controls pass
- negative result remains quarantined discovery evidence with no promotion or live effect

## Boundary

Negative R, small effective-N, and noncomputable DSR/PBO are not rejection reasons by themselves. They are barriers to validation and promotion. This audit accepts OTI7 only as quarantined negative discovery evidence.
