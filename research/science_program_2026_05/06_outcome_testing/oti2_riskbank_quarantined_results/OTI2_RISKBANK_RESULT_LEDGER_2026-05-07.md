# OTI2 Risk-Bank Result Ledger - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Result status:** `RESULT_QUARANTINED_DISCOVERY_ONLY`  
**Scope:** `OTG0-PKT-013` / `G10-EXP-RISKBANK-005` only

## Summary

| metric | value |
| --- | --- |
| raw rows | 86 |
| unique duplicate groups | 86 |
| risk-bank primary metric | not_computable |
| descriptive non-ambiguous n | 51 |
| descriptive non-ambiguous mean R | 0.147037 |
| conservative lower-bound n | 85 |
| conservative lower-bound mean R | -0.311778 |

## Path Labels

| label | rows |
| --- | --- |
| tp1_area_reached_without_entry_touch | 46 |
| entry_then_sl_before_tp1 | 29 |
| entry_then_tp1_before_sl | 5 |
| entry_sl_same_m1_ambiguous | 5 |
| entry_touched_unresolved | 1 |

## Cost Sensitivity

| cost R | non-amb n | non-amb mean | conservative n | conservative mean |
| --- | --- | --- | --- | --- |
| 0.0 | 51 | 0.147037 | 85 | -0.311778 |
| 0.02 | 51 | 0.145076 | 85 | -0.320954 |
| 0.05 | 51 | 0.142135 | 85 | -0.334719 |
| 0.1 | 51 | 0.137233 | 85 | -0.357660 |

## Note

The primary risk-bank reentry metric is not computable from the accepted input-only packet because leg-level reentry and risk-bank ledger fields are absent. Descriptive values are quarantined synthetic path summaries, not validation.
