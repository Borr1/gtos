# G12 OTI Next-Lane Recommendation - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `False`
**Outcome review opened:** `False`
**Generated:** `2026-05-07T01:17:05Z`

## Recommendation

`G0_OUTCOME_SYNTHESIS_CAN_USE_OTI1_OTI2_ONLY_AS_QUARANTINED_DISCOVERY_EVIDENCE`

## Allowed Next Use

- OTI1 can support lifecycle/no-fill descriptive discovery only.
- OTI2 can support synthetic path descriptive discovery and risk-bank packet gap definition only.
- Both lanes can define sharper future frozen packet requirements.

## Do Not Do

- Do not promote either lane.
- Do not mark validation_safe=true.
- Do not set outcome_review_opened=true in master registries.
- Do not pool lifecycle_no_fill, synthetic_path_r, broker_actual_r, or live trade results.
- Do not compute promotion DSR/PBO from these quarantined artifacts.
- Do not inspect blocked-packet outcomes; answer their exact blocker questions first.

## Next Exact Questions

| Lane | Question |
| --- | --- |
| OTI1 | Before any covariate-conditioned claim, which packet-bound source/as-of proofs clear the OTI1 covariate source-complete blockers while keeping lifecycle_no_fill separate from synthetic_path_r and broker_actual_r? |
| OTI2 | Which future frozen input packet provides leg-level reentry state, risk_bank_before_action_r, risk_bank_after_action_r, realized_closed_leg_r, open_leg_stop_if_hit_r, and numeric estimated_remaining_cost_r for G10-EXP-RISKBANK-005 without broker actual-R or blocked-packet outcome pooling? |
| G0 | Will G0 synthesis keep OTI1 and OTI2 in a discovery-only section, preserve NO_PROMOTION_VERDICT, and route OTI2 leg-level risk-bank packet construction plus OTI1 covariate source/as-of proofs as separate future blocker-clearing tasks? |
