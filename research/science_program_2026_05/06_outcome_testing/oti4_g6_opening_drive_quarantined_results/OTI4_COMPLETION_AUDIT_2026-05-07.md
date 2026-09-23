# OTI4 G6 Opening-Drive Completion Audit - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Result status:** `RESULT_QUARANTINED_DISCOVERY_ONLY`  
**Can mark goal complete:** `True`

## Objective Restatement

Run OTI4_G6_OPENING_DRIVE_QUARANTINED_OUTCOME_AUDIT using only G12 accepted OTG0-PKT-062, preserving quarantine/no-promotion boundaries, and either compute prereg-compatible summaries or prove exact non-computability.

## Prompt-To-Artifact Checklist

| requirement | status | evidence |
| --- | --- | --- |
| Complete GTOS preflight | PASS | generate_live_state.py and mandatory core docs were read before implementation. |
| Use only OTG0-PKT-062 accepted packet | PASS | research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/packets/OTG0-PKT-062__G6-EXP-003-OPENING-DRIVE-CONTINUATION__g6_local_ohlc_input_packet_2026-05-07.json |
| Exclude broker actual-R, blocked outcomes, live trade results, hidden path labels | PASS | Skipped sources listed; builder reads packet and OHLC coverage only. |
| Enforce duplicate denominator | PASS | raw=86 unique_duplicate_groups=19 countable=0 |
| Label-family separation | PASS | input_only_features_no_labels; future synthetic_path_r only; no label pooling. |
| Sample-floor warning | PASS | raw 86 and unique 19 below 200; countable 0. |
| DSR/PBO/effective-N or exact not_computable reasons | PASS | methodology report marks all not_computable with reasons. |
| Same-bar terminal-order uncertainty | PASS | same_bar_counts={'terminal_order_unclaimed': 80, 'same_m1_ambiguity_flagged': 6} terminal_order_claim_allowed=false |
| Search denominator inflation/stale OHLC/hidden labels/strict no-leak | PASS | duplicate, source coverage, no-leak, and adversarial reports emitted. |
| Produce result ledger or proof impossible | PASS | result ledger rows all NOT_COMPUTABLE_SOURCE_BLOCKED with exact reasons. |
| Preserve safety flags | PASS | NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false. |
