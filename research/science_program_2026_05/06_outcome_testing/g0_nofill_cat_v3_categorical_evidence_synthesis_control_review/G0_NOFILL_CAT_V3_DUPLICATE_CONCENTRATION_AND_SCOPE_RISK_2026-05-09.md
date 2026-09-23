# G0 NOFILL CAT V3 Duplicate Concentration And Scope Risk

Promotion posture: `NO_PROMOTION_VERDICT`.

## Denominator Policy

- Row-level source inventory: `225`.
- Primary duplicate-key denominator: `182`.
- Secondary duplicate-group concentration denominator: `139`.
- Noncanonical accepted projection rows: `43`.

## Primary Dimension Counts

### symbol

| Value | Count |
|---|---:|
| `GBPJPY` | 16 |
| `NAS100` | 52 |
| `US30_cash` | 3 |
| `USDJPY` | 67 |
| `XAGUSD` | 30 |
| `XAUUSD` | 14 |

### session

| Value | Count |
|---|---:|
| `london` | 45 |
| `ny` | 90 |
| `tokyo` | 47 |

### side

| Value | Count |
|---|---:|
| `LONG` | 76 |
| `SHORT` | 106 |

### source_lane

| Value | Count |
|---|---:|
| `OTI1_LIFECYCLE` | 54 |
| `OTI2_RISKBANK` | 46 |
| `OTI3_G3_GEOMETRY` | 65 |
| `OTI4_G6_OPENING_DRIVE` | 8 |
| `OTI5_G6_CUSUM` | 9 |

## Risk Findings

- opening_drive_source_projection_ready_no_result_label is 51 rows but only 8 primary duplicate-key members, driven by 43 noncanonical accepted projections.
- nofill_terminal_before_entry dominates the primary duplicate-key view with 110 of 182 members, so it is the only broad categorical family in this frozen count-control packet.
- source_corrected_no_entry_through_pending_horizon is 32 primary duplicate-key members but only 7 duplicate-group members, so opportunity-level concentration is high.
- fill_path_entry_before_protective_level_no_terminal_observed is 22 primary duplicate-key members but only 4 duplicate-group members, also highly concentrated.
- USDJPY, XAGUSD, NAS100, NY session, SHORT side, and OTI3/OTI1/OTI4 source lanes are major scope-risk axes; none can be generalized without a separate source-safe expansion and later evidence-class gate.

## Blocking Conflict Status

- Accepted duplicate-key label conflicts: `0`.
- Accepted duplicate-key denominator conflicts: `0`.
- Accepted source-geometry conflicts: `0`.
- Accepted source-ordering blockers: `0`.
