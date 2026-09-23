# G12 OTI7 CNR Scoring Source No-Leak Audit - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

## Status

`PASS`

| check | value |
| --- | --- |
| source files rehashed | 16 |
| source rehash missing | 0 |
| source rehash mismatches | 0 |
| quote recompute mismatches | 0 |
| G12 strict hash mismatches | 0 |
| G12 as-of issues | 0 |
| ready input forbidden-key hits | 0 |

## Label Boundary

Input rows remain `input_only_features_no_labels`; OTI7 outputs are `synthetic_path_r_quarantined_discovery_only`. Broker actual-R, account history, live trade results, hidden path labels, and blocked packet outcomes were not used.

## Scoring Boundary

This G12 audit does not rescore OTI7 rows. It audits the frozen OTI7 result ledger and recomputes source-file hashes for evidence quality.
