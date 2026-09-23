# G12 OTI7 CNR Row Exclusion Duplicate Audit - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

## Status

`PASS`

| check | value |
| --- | --- |
| accepted rows processed | 102 |
| JSONL rows | 102 |
| blocked rows excluded | 6098 |
| accepted-blocked SHA overlap | 0 |
| accepted-blocked row-number overlap | 0 |
| countable rows | 54 |
| duplicate-context rows | 48 |
| countable unique duplicate groups | 27 |
| scored countable unique duplicate groups | 22 |

Duplicate policy: one countable row per duplicate_group_id per packet/timing_model_family/target_model_family
