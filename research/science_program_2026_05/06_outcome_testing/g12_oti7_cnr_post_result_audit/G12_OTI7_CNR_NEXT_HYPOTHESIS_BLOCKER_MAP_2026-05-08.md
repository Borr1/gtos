# G12 OTI7 CNR Next Hypothesis Blocker Map - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

## Creativity Boundary

Hypotheses are source-safe next routes only. They are not evidence, rescue rules, or validation claims.

## Next Routes

| status | hypothesis | required unblocker |
| --- | --- | --- |
| BLOCKED_BY_G12_EXCLUSION_CURRENT_LANE | CNR_E2/E3/E4 could matter only if source-safe timestamps are captured before outcome opening. | signal_emitted_utc or latency-window fields with source hash, plus no-lookahead tests |
| BLOCKED_BY_G12_EXCLUSION_CURRENT_LANE | A target model measured from executable entry may avoid tiny residual TP1 R. | CNR_T1/T2/T3 target contract frozen before outcomes with stop model and source-hashed level/terminal source |
| EXACT_PACKET_FIELD_BLOCKER | Continuation-no-retrace rows need geometry and horizon fields before result scoring. | OTG0-PKT-061 packet rebuild with entry_sl_tp_or_level_packet and path_start/path_end fields |
| LEARNING_FROM_NEGATIVE_RESULT | Market-entry geometry should have its own invalidity gate. | source-bound rule for stop invalid at executable quote before future CNR result audit |
| SOURCE_SAFE_PREREG_REQUIRED_NO_OUTCOME_CLAIM | Market-entry CNR needs a pre-entry residual-R eligibility gate, not a post-hoc rescue threshold. | Input-only packet field residual_target_r_from_executable_quote computed before result opening, plus preregistered sample floor and duplicate policy. |
| SOURCE_SAFE_FEATURE_PACKET_REQUIRED | The failed rows may be late-entry artifacts where original pending-entry geometry has decayed before executable market entry. | As-of quote displacement fields from original entry/stop/TP, captured in input packets before any future outcome opening. |
| BLOCKED_BY_MISSING_SOURCE_FIELD | CNR may need pretouch continuation trigger timing rather than decision-close/candidate-close timing. | CNR_E4 pretouch_trigger_id and pretouch_trigger_utc logger/parser fields, source hashed and frozen before outcomes. |
| BLOCKED_BY_TARGET_CONTRACT | A structural target or fixed-R target could be tested only if defined before outcomes. | CNR_T1/T2/T3 target contracts with stop model, target selection source, timestamp, parser version, and no-leak source hash. |
| EXACT_PACKET_FIELD_BLOCKER | OTG0-PKT-061 continuation-no-retrace cannot teach result quality until geometry exists. | Packet rebuild that materializes entry_sl_tp_or_level_packet and path_start/path_end fields for CNR rows without using result labels. |

Blocked CNR_E2/E3/E4 and CNR_T1/T2/T3 outcome families remain closed.
