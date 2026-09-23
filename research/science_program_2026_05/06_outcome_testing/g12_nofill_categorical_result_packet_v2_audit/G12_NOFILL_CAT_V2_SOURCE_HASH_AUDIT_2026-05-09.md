# G12 NOFILL CAT V2 Source Hash Audit

Promotion posture: `NO_PROMOTION_VERDICT`.

Status: `PASS`.
Control inputs hashed: `19`.
V2 control input rehash status: `PASS`.
Recomputed OTI3 same-tick blockers: `4`.
Recomputed OTI4 May 3 source gaps: `3`.
Recomputed original OTI2 source gap rows: `1`.

## Blocker Saturation

- OTI3 same-tick rows: one source tick at the first timestamp satisfies multiple event predicates; no intra-tick order exists in the approved source.
- OTI4 May 3 rows: local tick files exist but contain zero rows in the frozen 13:00-13:30 UTC opening range; no approved CSV/OHLC substitute is recorded.
- Original OTI2 row: M1 context is not side-aware tick proof and XAUUSD tick coverage misses the active window through cancel.
