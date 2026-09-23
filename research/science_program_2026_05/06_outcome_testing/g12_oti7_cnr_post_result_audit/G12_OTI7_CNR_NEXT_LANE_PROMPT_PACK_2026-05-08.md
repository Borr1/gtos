# G12 OTI7 CNR Next-Lane Prompt Pack - 2026-05-08

Promotion posture: `NO_PROMOTION_VERDICT`  
Validation safe: `false`  
Outcome review opened: `false`  
Live effect: `false`

These prompts are source-safe next routes only. They must not be treated as evidence that CNR works.

## Prompt 1 - Residual-R Input Packet Audit

`/goal Build an input-only CNR residual-target-R packet audit for E0/E1 rows. Freeze executable quote, original entry/SL/TP, residual_target_r_from_executable_entry, duplicate key, source hash, no-leak scan, and sample-floor blocker before any outcome opening. Do not score outcomes or open blocked CNR_T1/T2/T3 rows. Preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false.`

## Prompt 2 - CNR E4 Pretouch Trigger Source Builder

`/goal Build a source-field packet builder for CNR_E4_PRETOUCH_CONTINUATION_TRIGGER. Search current logs for pretouch_trigger_id and pretouch_trigger_utc; if absent, write exact logger/parser/source-field requirements. Do not infer pretouch triggers from later path and do not open outcomes. Preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false.`

## Prompt 3 - CNR Geometry Decay And Invalidity Gate Preregistration

`/goal Preregister market-entry geometry decay and invalidity controls for future CNR audits. Use only input fields: executable quote, original entry, original SL, original TP1, quote age, spread, side, and duplicate group. Define invalidity and residual-R bins before outcomes. Do not backfit thresholds or rescore OTI7. Preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false.`

## Prompt 4 - OTG0-PKT-061 Geometry Rebuild

`/goal Rebuild OTG0-PKT-061 CNR continuation-no-retrace input packets with source-hashed entry/stop/target or level packet and path_start/path_end fields. Produce a G12 packet audit and exact blocker ledger only. Do not score outcomes until the rebuilt packet passes source/no-leak/duplicate/geometry audit. Preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false.`
