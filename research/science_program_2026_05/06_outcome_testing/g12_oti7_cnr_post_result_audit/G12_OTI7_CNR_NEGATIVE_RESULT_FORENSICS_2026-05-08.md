# G12 OTI7 CNR Negative Result Forensics - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

## Headline

CNR E0/E1 market-entry with original TP1 is accepted as a clean quarantined negative discovery result, not rescued or promoted.

## Symbol Anatomy

| symbol | rows | scored | status counts | mean R scored |
| --- | --- | --- | --- | --- |
| GBPJPY | 32 | 32 | {'SCORED_STOP_FIRST': 32} | -1.0 |
| NAS100 | 6 | 6 | {'SCORED_STOP_FIRST': 6} | -1.0 |
| XAGUSD | 50 | 24 | {'SCORED_STOP_FIRST': 18, 'SCORED_TARGET_FIRST': 6, 'UNSCOREABLE_MISSING_SOURCE_GEOMETRY': 8, 'UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY': 18} | -0.73638 |
| XAUUSD | 14 | 14 | {'SCORED_STOP_FIRST': 8, 'SCORED_TARGET_FIRST': 6} | -0.525106 |

## Failure Lessons

### The accepted CNR E0/E1 plus original TP1 package failed negatively.

Evidence: `{"all_scored_mean_r": -0.829271, "countable_scored_mean_r": -0.755473, "scored_rows": 76, "stop_first": 64, "target_first": 12}`

Interpretation: The negative result is not a target-already-passed artifact in accepted rows; most eligible market-entry paths hit the original stop first.
### Target-first rows were too small to offset one-R stop losses.

Evidence: `{"target_first_r_max": 0.108085, "target_first_r_mean": 0.081281, "target_first_r_min": 0.054478, "target_first_rows": 12}`

Interpretation: Original TP1 was often close to the executable market-entry quote. A win was only a small residual target, while a loss remained -1R from the market quote to original stop.
### E0 and E1 are identical in this packet set.

Evidence: `"Both timing families have 51 rows, identical status counts, and identical mean R because the accepted packet rows share the same executable quote timestamp."`

Interpretation: This is a packet-field limitation, not proof that decision-close and candidate-close timing are equivalent.
### Invalid stop geometry is itself failure evidence.

Evidence: `{"invalid_stop_by_symbol_session_packet": {"XAGUSD|london|OTG0-PKT-060": 6, "XAGUSD|london|OTG0-PKT-062": 6, "XAGUSD|london|OTG0-PKT-063": 6}, "invalid_stop_rows": 18}`

Interpretation: The source-safe market quote could already be beyond the original stop for short XAGUSD rows, so original pending-entry geometry is not transferable to late market-entry execution.
### Missing geometry is confined and actionable.

Evidence: `{"missing_geometry_by_symbol_session_packet": {"XAGUSD|london|OTG0-PKT-061": 2, "XAGUSD|ny|OTG0-PKT-061": 6}, "missing_geometry_rows": 8}`

Interpretation: OTG0-PKT-061 cannot be scored until entry/stop/target and path horizon fields are rebuilt source-safely.
