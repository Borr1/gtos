# G12 NOFILL Remaining Decision Ledger - 2026-05-09

Generated: `2026-05-09T05:00:23Z`

Packet decision: `ACCEPT_BY_ROW_EVIDENCE_CLASS_ONLY`

Promotion posture: `NO_PROMOTION_VERDICT`; `validation_safe=false`; `outcome_review_opened=false`; `live_effect=false`.

## Row Decisions

| packet_row_id | symbol | upstream_residual_source_status | g12_terminal_decision | source_control_only | cleared_into_accepted_denominator |
| --- | --- | --- | --- | --- | --- |
| NOFILL-CAT-ROW-0241 | XAUUSD | SOURCE_CONTROL_CLEARED_INPUT_ONLY | ACCEPT_AS_SOURCE_CONTROL_INPUT_ONLY_EVIDENCE | True | False |
| NOFILL-CAT-ROW-0130 | USDJPY | SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES | ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY | True | False |
| NOFILL-CAT-ROW-0143 | USDJPY | SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES | ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY | True | False |
| NOFILL-CAT-ROW-0165 | USDJPY | SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES | ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY | True | False |
| NOFILL-CAT-ROW-0178 | USDJPY | SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES | ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY | True | False |

## Audit Question Answers

- Are exactly five target rows audited and no others?: Yes. The decision ledger contains exactly 0241, 0130, 0143, 0165, and 0178.
- Were May 3 rows kept closed?: Yes. 0049/0050/0051 remain closed context from the prior G12 May3 audit and are not row decisions here.
- Is XAUUSD 0241 acceptable as source-control input-only evidence?: Yes, narrowly. It proves no side-aware short entry touch before cancel; it does not assign a lifecycle/result/performance label.
- Are USDJPY same-tick rows source-impossible from approved routes?: Yes. Current approved quote/tick rows are MqlTick state rows with no sub-row sequence; M1 and Sierra/proxy routes cannot resolve broker-native event order.
- Is a future result/categorical rebuild allowed?: Only as a separate evidence-class gate. XAUUSD 0241 may be consumed as input-only source-control evidence; the USDJPY rows remain impossibility evidence/blockers unless a broker-native sequence source appears.
