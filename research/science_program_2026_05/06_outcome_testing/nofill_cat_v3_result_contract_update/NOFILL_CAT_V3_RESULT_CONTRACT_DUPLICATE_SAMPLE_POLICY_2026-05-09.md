# NOFILL CAT V3 Result Contract Duplicate/Sample Policy - 2026-05-09

Promotion posture: `NO_PROMOTION_VERDICT`

## Frozen Denominators

- Row-level accepted input rows: `225`.
- Primary duplicate-collapsed denominator: `182` unique `nofill_duplicate_key` values.
- Secondary concentration denominator: `139` unique `duplicate_group_id` values.
- Source inventory identities inside accepted rows: `225`.

Row-level counts are allowed only as source inventory and descriptive categorical counts. Any future interpretation must also report the collapsed `nofill_duplicate_key` denominator.

## Canonical Projection Rule

Within a `nofill_duplicate_key`, the canonical collapsed row is the lowest `packet_row_id`, then lowest `source_inventory_id`. Noncanonical accepted rows can appear in row-level lineage but cannot inflate the duplicate-collapsed denominator.

## Conflict Rule

Current accepted duplicate-key label conflicts: `0`.

If a future scorer finds conflicting categorical labels, source geometry, source ordering, or unsafe flags inside one duplicate key, it must block the whole duplicate key and route back to source-control review.

## Sample-Floor Rule

Current lane opened no result records, so no scoring sample floor applies here.

A future categorical discovery lane may report counts at any n, but must mark a family `DISCOVERY_UNDER_SAMPLE_FLOOR` until it has at least 30 unique `nofill_duplicate_key` rows and 10 unique `duplicate_group_id` rows in that family.

Validation or promotion remains closed by this contract regardless of n. A separate preregistered validation/promotion dossier is required.
