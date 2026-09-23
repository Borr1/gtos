# G12 No-Fill Duplicate Sample-Floor Audit - 2026-05-08

Status: `PASS`
Decision: `ACCEPT_DUPLICATE_CONTROLS_FOR_INPUT_ONLY_SCOPE`
Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

- Packet rows: `298`
- Unique source inventory ids: `298`
- Unique no-fill duplicate keys: `196`
- Repeated no-fill duplicate keys: `12`
- Max no-fill duplicate key repeat: `16`
- Sample floor status: `FALSE_INPUT_ONLY_CONTROL_PACKET_NOT_VALIDATION`

Rows are mixed input-control lifecycle/source-block families with repeated opportunity groups; this blocks validation/promotion but preserves source-control usefulness.
