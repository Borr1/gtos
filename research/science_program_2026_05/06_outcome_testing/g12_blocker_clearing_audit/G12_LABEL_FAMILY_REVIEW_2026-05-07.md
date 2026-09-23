# G12 Label-Family Review - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`

| Family | Label family | Status | Details |
| --- | --- | --- | --- |
| OTB1 | lifecycle_no_fill | PRIMARY_ROWS_PHYSICALLY_SEPARATED_BUT_SOURCE_HASH_BLOCKED | All OTB1 primary rows use lifecycle_no_fill and no broker/synthetic R columns, but source/hash construction still touches result-bearing audit path-label fields. |
| OTB2 | synthetic_path_r | PRIMARY_ROWS_DECLARED_SYNTHETIC_ONLY_BUT_SOURCE_ROWS_RESULT_BEARING | The synthetic label family is declared as a guard; primary records do not contain result columns, but referenced path-order source rows contain post-entry path/touch labels. |
| OTB3 | context_only_source_noleak_sidecar | ACCEPT_CONTEXT_ONLY | OTB3 proposes as-of whitelists and keeps forbidden current fields out of proposed no_leak_fields. |
