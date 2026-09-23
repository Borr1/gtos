# OTB1R Schema And No-Leak Validation Report - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Primary Row Validation

| Packet | Experiment | Decision | Rows | Issues |
| --- | --- | --- | --- | --- |
| OTG0-PKT-011 | G10-EXP-PREFILL-003 | REBUILT_INPUT_ONLY_READY_FOR_G12_REAUDIT | 8 | 0 |
| OTG0-PKT-016 | EXP-G11-FRICTION-GATE-007 | REBUILT_INPUT_ONLY_READY_FOR_G12_REAUDIT | 8 | 0 |
| OTG0-PKT-017 | EXP-G11-OBSERVER-EXPANSION-006 | BLOCKED_WITH_NEXT_EXACT_QUESTION | 0 | 0 |
| OTG0-PKT-025 | EXP-G2-GARCH-LIFECYCLE-002 | REBUILT_INPUT_ONLY_READY_FOR_G12_REAUDIT | 8 | 0 |
| OTG0-PKT-029 | EXP-G2-SURVIVAL-PATH-006 | REBUILT_INPUT_ONLY_READY_FOR_G12_REAUDIT | 8 | 0 |
| OTG0-PKT-045 | EXP-G4-XAUUSD-FOOTPRINT-ABSORB-003 | REBUILT_INPUT_ONLY_READY_FOR_G12_REAUDIT | 2 | 0 |
| OTG0-PKT-055 | EXP-G5-NEWS-005 | REBUILT_INPUT_ONLY_READY_FOR_G12_REAUDIT | 8 | 0 |
| OTG0-PKT-059 | EXP-G5-XG7-MACRO-ATTN-009 | REBUILT_INPUT_ONLY_READY_FOR_G12_REAUDIT | 8 | 0 |
| OTG0-PKT-071 | EXP-G7-FOMC-ATTN-003 | REBUILT_INPUT_ONLY_READY_FOR_G12_REAUDIT | 8 | 0 |
| OTG0-PKT-079 | EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001 | REBUILT_INPUT_ONLY_READY_FOR_G12_REAUDIT | 4 | 0 |

## Source Projection Validation

- Source projection rows: `8`
- Projection issues: `0`
- `path_label` excluded count: `8`
- Source hashes are recomputed from sanitized projected source rows only.
- Excluded source key values are not stored in projection audit rows; only key names and counts are reported.

## Forbidden Primary Fields

`actual_r`, `broker_actual_r`, `future_return`, `outcome_r`, `post_entry_path`, `synthetic_path_r`, `trade_result`, `win_loss`
