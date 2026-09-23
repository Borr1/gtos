# OTI2 Risk-Bank Ambiguity Resolution Ledger - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Result status:** `RESULT_QUARANTINED_DISCOVERY_ONLY`

| item | value |
| --- | --- |
| terminal order claim allowed | False |
| same-bar flagged rows | 34 |
| non-same-bar unresolved rows | 1 |
| unresolved or bounded rows | 35 |

## Same-Bar State Counts

| state | rows |
| --- | --- |
| not_flagged_or_not_applicable | 52 |
| same_m1_ambiguity_flagged | 34 |

## Policy

same-minute terminal order is not guessed; flagged rows are retained as conservative/bounded ambiguity rows and excluded from primary resolved riskbank scoring
