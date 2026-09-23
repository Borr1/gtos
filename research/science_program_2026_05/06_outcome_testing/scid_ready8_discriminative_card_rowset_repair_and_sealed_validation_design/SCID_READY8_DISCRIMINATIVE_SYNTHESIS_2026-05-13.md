# SCID READY8 Discriminative Card Rowset Repair And Sealed Validation Design

Date: 2026-05-13

Evidence class: `SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN_ONLY`

Promotion posture: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Decision

The READY8 redundancy failure is repaired at source-control design level. The source candidate universe remains the accepted `3,014` SCID as-of rows, but the repaired rowset no longer treats all `3,014` rows as card passes for every card. Each card now has a card-specific predicate or descriptor contrast key, with row-level `pass`, `contrast`, `non-applicable`, and `fail-closed` denominator roles.

## Card Repairs

- `ADV-001`: session/time/symbol placebo contrast.
- `ADV-003`: duplicate-key hash placebo contrast.
- `BEH-001`: session-open participant pressure versus later active-session controls.
- `HAZ-001`: waiting-time reset and dense prior-24h candidate-burst contrast.
- `HAZ-005`: predecision descriptor/clock transition contrast with missing descriptors fail-closed.
- `MAC-001`: day-of-week and month-turn calendar context.
- `MAC-004`: metals-only LBMA fix-window context; non-metals are non-applicable.
- `UNC-004`: source-confidence tier contrast from predecision descriptor completeness.

## Guardrails

No target scoring, validation, performance claim, AI/API call, paid/vendor access, broker/account/order/history/deal/position evidence, raw market blob commit, registry edit, remote push, or live trading-surface change was opened. Existing `SEALED_VALIDATION_CANDIDATE_DESIGN` labels remain source-control assignments only until a later G12/G0 target-opening gate accepts this repaired package.

## Next Gate

The next evidence-class gate is independent G12 acceptance of this repaired source-control rowset package. A future result-opening route must freeze target families/horizons, denominator rules, fail-closed behavior, duplicate/concentration gates, and no-leak/as-of proof before opening any target rows.
