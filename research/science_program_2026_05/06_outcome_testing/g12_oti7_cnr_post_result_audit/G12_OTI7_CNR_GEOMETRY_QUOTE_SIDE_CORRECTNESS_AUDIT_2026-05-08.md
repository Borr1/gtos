# G12 OTI7 CNR Geometry Quote-Side Correctness Audit - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

## Status

`PASS`

| check | value |
| --- | --- |
| scored rows | 76 |
| unscoreable rows | 26 |
| stop invalid rows | 18 |
| missing geometry rows | 8 |
| target already passed rows | 0 |
| quote timestamp mismatches | 0 |
| target-first R mean | 0.081281 |
| target-first R min | 0.054478 |
| target-first R max | 0.108085 |

LONG entries use ask and exit/terminal checks use bid. SHORT entries use bid and exit/terminal checks use ask. Geometry was checked before accepting any R value.
