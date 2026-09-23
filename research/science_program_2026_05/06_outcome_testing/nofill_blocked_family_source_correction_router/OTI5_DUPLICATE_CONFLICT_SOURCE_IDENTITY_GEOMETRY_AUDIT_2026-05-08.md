# OTI5 Duplicate Conflict Source Identity Geometry Audit

Generated: `2026-05-08T15:20:00Z`
Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

Rows audited: `42`
Duplicate groups: `3`
Verdict: `SOURCE_CORRECTABLE_CONTRACT_REVISION_PACKET_READY_NO_LABELS_ASSIGNED`

## Frozen Rules

- Canonical geometry: For each nofill_duplicate_key in this OTI5 family, sort rows by decision_asof_utc then source_row_id; select the first row as the only canonical geometry/order source for any future categorical packet. All later rows in the same key are repeated projections and must remain non-countable unless a future preregistered source contract deliberately splits the opportunity identity before any label assignment.
- Duplicate denominator: Collapse the OTI5 duplicate-conflict family by nofill_duplicate_key after canonical geometry selection. Exactly one source-corrected denominator unit may exist per key; noncanonical row projections are excluded from denominator and label assignment.

## Group Decisions

| nofill_duplicate_key | rows | canonical row | decision | signatures |
| --- | ---: | --- | --- | ---: |
| `OTI5_G6_CUSUM|OTG0-PKT-063|G6_EXHAUSTION|NAS100|2026-05-04|ny|LONG|LONG|no_entry_touch_no_r_scored` | 12 | `NOFILL-CAT-ROW-0016` | `SOURCE_CORRECTABLE_DENOMINATOR_COLLISION_WITH_REPEATED_PROJECTIONS_AND_GEOMETRY_MISMATCH` | 12 |
| `OTI5_G6_CUSUM|OTG0-PKT-063|G6_EXHAUSTION|XAGUSD|2026-05-04|london|SHORT|LONG|no_entry_touch_no_r_scored` | 14 | `NOFILL-CAT-ROW-0001` | `SOURCE_CORRECTABLE_DENOMINATOR_COLLISION_WITH_REPEATED_PROJECTIONS_AND_GEOMETRY_MISMATCH` | 14 |
| `OTI5_G6_CUSUM|OTG0-PKT-063|G6_EXHAUSTION|XAGUSD|2026-05-04|ny|SHORT|LONG|no_entry_touch_no_r_scored` | 16 | `NOFILL-CAT-ROW-0017` | `SOURCE_CORRECTABLE_DENOMINATOR_COLLISION_WITH_REPEATED_PROJECTIONS_AND_GEOMETRY_MISMATCH` | 16 |

## Boundary

No categorical lifecycle labels are assigned in this audit. The current packet remains blocked until a future source-correction/contract-revision packet consumes the frozen canonical geometry rule.
