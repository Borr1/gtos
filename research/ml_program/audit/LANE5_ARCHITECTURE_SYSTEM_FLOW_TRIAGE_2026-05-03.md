# Lane 5 Architecture/System-Flow Triage

Date: 2026-05-03
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Question

Classify Lane 5 P-family system-flow architecture items from existing vol-conditioning and K54 evidence.

## Evidence Summary

- H-PM01 portfolio-wide vol-conditioning: delta mean R `-0.004960547358764833`, delta Sharpe `%` `-2.5761764707408985`, DSR-p `0.9999646857030353`, gate pass `False`.
- H-PM01 NAS100 subcandidate: n `252`, delta mean R `0.09066365782920549`, delta Sharpe `%` `9.65503862508914`, DSR-p `0.015223281554341606`.
- Meta-labeling head: ran in K54 v3, but remains sample-size deferred at n=528 / about 250 primary-positive rows.
- Conformal proxy: coverage `0.8810606060606061` vs target `0.9`, Christoffersen p `0.0015804301852155866`, status `DEFERRED (holdout 2026-04-29 to 2026-05-12 not yet opened); CPCV proxy reported`.
- Routing: K54 v4 gate_h pass `False`, T7-NAS routing delta `-0.0052050670338545674`, boot p `0.5874`, ship arch `None`.

## Task Classifications

| id | status | blocker / trigger | candidate strength |
| --- | --- | --- | --- |
| P-1 | DEFERRED_WITH_TRIGGER | Portfolio-wide vol-conditioning failed H-PM01; live insertion between 3A and execution would change risk/trading behavior and needs CEO approval even for shadow. | NAS100-only subcandidate delta_R 0.09066365782920549 DSR-p 0.015223281554341606; portfolio-wide failed, not promotion comparable |
| P-2 | DEFERRED_WITH_TRIGGER | Meta-labeling ran in K54 v3 but was statistically weak at the current cohort size. | deferred_sample_size |
| P-3 | DEFERRED_WITH_TRIGGER | K54 global candidates failed; conformal has only a CPCV proxy and no live/holdout system-flow candidate to calibrate. | not_strategy_comparable_calibration_deferred |
| P-5 | REJECTED_FAILED | K-5 W-unit pooling failed and K-6 pooled K54 v3/v4 training failed global gates. | rejected_inherits_k5_k6_failure |
| P-6 | DEFERRED_WITH_TRIGGER | K54 v4 T7-NAS routing add was negative and all K54 v4 architectures failed; any inference routing layer is shadow-only until a specialist survives forward evidence. | deferred_k55_shadow_specialist_only |

## Interpretation

- `P-1` is deferred, not implementation-ready: portfolio-wide Component 3C failed; only a NAS100-only shadow candidate remains and would require approval.
- `P-2` follows `K-12`: meta-labeling is sample-size deferred.
- `P-3` follows `K-14`: calibration tooling exists, but no approved live/holdout candidate is ready for a system-flow module.
- `P-5` inherits the `K-5`/`K-6` failure and is rejected for the current substrate/cohort.
- `P-6` is deferred: current routing ablation failed, and specialist routing must stay K55-shadow-only until forward evidence exists.

## Source Files

- `research/ml_program/phase_2/position_mgmt/h_pm01_vol_conditional_sizing.md`
- `research/ml_program/phase_2/position_mgmt/h_pm01_per_cohort_results.json`
- `research/ml_program/phase_2/MASTER_SYNTHESIS_PHASE_2.md`
- `research/ml_program/audit/Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md`
- `research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md`
- `research/ml_program/models/k54_v3/conformal_calibration.json`
- `research/ml_program/models/k54_v4/component_ablation.json`
- `research/ml_program/models/k54_v4/final_verdicts.json`

## NO_PROMOTION_VERDICT

This artifact classifies architecture/system-flow readiness only. It does not validate, promote, or modify live trading behavior.
