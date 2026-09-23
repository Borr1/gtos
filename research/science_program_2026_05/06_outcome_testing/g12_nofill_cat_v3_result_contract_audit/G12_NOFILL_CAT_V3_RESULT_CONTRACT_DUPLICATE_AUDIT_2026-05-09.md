# G12 NOFILL CAT V3 Result Contract Duplicate Audit

Promotion posture: `NO_PROMOTION_VERDICT`

Status: `PASS`
Decision: `ACCEPT_DUPLICATE_POLICY_FOR_COUNT_PACKET_WITH_REJECT_OVERLAP_GUARD`
Accepted row-level count: `225`
Accepted unique nofill_duplicate_key: `182`
Accepted unique duplicate_group_id: `139`
Accepted noncanonical projections: `43`
Accepted label conflicts: `0`
Reject key overlaps with accepted: `47`

Reject rows can share accepted duplicate keys/groups because many rejects are noncanonical projections. They remain outside every denominator and must not add to or subtract from row-level counts, duplicate-key counts, or effective-N.
