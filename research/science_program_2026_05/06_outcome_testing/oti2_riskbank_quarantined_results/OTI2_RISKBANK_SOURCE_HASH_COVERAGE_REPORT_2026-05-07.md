# OTI2 Risk-Bank Source Hash Coverage Report - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Result status:** `RESULT_QUARANTINED_DISCOVERY_ONLY`

| check | value |
| --- | --- |
| packet hash match | True |
| row source hash matches | 86 |
| row source hash failures | 0 |
| coverage reaches path_end | 86 |
| coverage failures | 0 |
| duplicate denominator | 86/86 |
| within-packet duplicate drift | 0 |

## Coverage Modes

| mode | rows |
| --- | --- |
| EXPLICIT_INPUT_ONLY_PATH_ORDER_ROW_COVERAGE_VALID | 86 |

## Leakage Guard

| guard | value |
| --- | --- |
| packet_broker_actual_r_absent | True |
| packet_label_family | synthetic_path_r |
| builder_result_values_inspected | False |
| builder_quarantine_outputs_created | False |
| g12_rebuild_leakage_verdict | PASS_REBUILT_NOLEAK per G12 OTB rebuild review; this result script opens path labels only after freeze |
