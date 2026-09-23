# OTI3 G3 Geometry Method Freeze - 2026-05-07

**Lane:** `OTI3_G3_GEOMETRY_QUARANTINED_OUTCOME_AUDIT`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Result status:** `RESULT_QUARANTINED_DISCOVERY_ONLY`  
**Validation safe:** `false`  
**Outcome review opened:** `false`

## Scope

Only the G12-accepted G3 geometry packets may enter this lane:

| Packet | Experiment | Allowed use |
| --- | --- | --- |
| `OTG0-PKT-031` | `EXP-G3-DC-OVERSHOOT-002` | Quarantined duplicate-aware overshoot/path-label discovery summaries or exact not-computable proof |
| `OTG0-PKT-032` | `EXP-G3-DC-SWING-001` | Quarantined duplicate-aware DC event-rate/path-label discovery summaries or exact not-computable proof |
| `OTG0-PKT-036` | `EXP-G3-TDA-007` | Quarantined duplicate-aware TDA/path-label discovery summaries or exact not-computable proof |

All non-G3 accepted packets, blocked packet outputs, broker actual-R rows, lifecycle/no-fill rows, live trade results, and prior result folders are excluded.

## Frozen Method

- Verify each accepted packet file hash against the G12 accepted shortlist before reading rows.
- Recompute row `source_hash` from `source_hash_payload`.
- Use unique `duplicate_group_id` inside each packet and unique `parent_duplicate_group_id` for cross-packet setup reuse warnings.
- Preserve label-family separation: `synthetic_path_r` only, with broker actual-R absent.
- Path labels may be opened only as quarantined labels, never as decision-time features.
- Same-bar terminal order must not be guessed. Same-bar flagged rows are excluded from resolved summaries and recorded in the ambiguity ledger.
- Report DSR, PBO, effective-N, and raw-p status, or exact `not_computable` reasons.

## Result Boundary

Any computed values are discovery-only, not validation. The lane may describe feature/path-label associations when the label source can be local-source-hash bound to the accepted packet rows. If not, the packet receives an exact impossibility proof instead of an invented result.
