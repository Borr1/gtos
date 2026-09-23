# NOFILL CAT V3 Duplicate Concentration Diagnostics

Promotion posture: `NO_PROMOTION_VERDICT`

Accepted row-level total: `225`
Primary duplicate-key total: `182`
Secondary duplicate-group total: `139`
Accepted noncanonical projection count: `43`

Noncanonical accepted projections remain visible as row-level source inventory, but only the lowest packet_row_id/source_inventory_id inside each nofill_duplicate_key enters the primary duplicate-collapsed denominator.

## Conflict Audit

- Label conflicts: `0`
- Source-geometry conflicts: `0`
- Source-ordering blockers: `0`
- Denominator conflicts: `0`
- Nonblocking projection-variance keys: `5`

## Effective-N / Concentration Views

- `categorical_lifecycle_label`: effective_n=`3.116727`, top=`{'label': 'nofill_terminal_before_entry', 'count': 110, 'share': 0.488889}`
- `categorical_lifecycle_label`: effective_n=`2.416752`, top=`{'label': 'nofill_terminal_before_entry', 'count': 110, 'share': 0.604396}`
- `categorical_lifecycle_label`: effective_n=`1.575552`, top=`{'label': 'nofill_terminal_before_entry', 'count': 110, 'share': 0.791367}`
- `symbol`: effective_n=`4.023285`, top=`{'label': 'USDJPY', 'count': 67, 'share': 0.297778}`
- `session`: effective_n=`2.539249`, top=`{'label': 'ny', 'count': 120, 'share': 0.533333}`
- `side`: effective_n=`1.902266`, top=`{'label': 'SHORT', 'count': 138, 'share': 0.613333}`
- `source_lane`: effective_n=`4.240305`, top=`{'label': 'OTI3_G3_GEOMETRY', 'count': 65, 'share': 0.288889}`
