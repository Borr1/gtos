# Lane 5 K54 Architecture Triage

Date: 2026-05-03
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Question

Classify K54/K55 architecture backlog items K-5..K-15 and K-18 from existing K54 v3/v4 artifacts.

## Evidence Summary

- K54 v3 primary lift: `0.04835986000202819`; DSR-p `0.32095808514499824`; PBO `0.2`; verdict `FAIL`.
- W-unit ablation: ON AUC `0.5099822065485595` vs OFF AUC `0.5639553708274125`; v3 features over Arch A `0.003457028435499998`.
- Feature stability: `2` stable features; mean Jaccard `0.1685447455309013`; gate pass `False`.
- Conformal proxy: coverage `0.8810606060606061` vs target `0.9`; Christoffersen p `0.0015804301852155866`.
- K54 v4 verdicts: all architectures failed `True`; ship arch `None`.
- Strongest remaining K-family finding is the NAS_US30 specialist as K55-shadow discovery only: AUC `0.6014106583072101`, delta `0.10297805642633234`.

## Task Classifications

| id | status | blocker / trigger | candidate strength |
| --- | --- | --- | --- |
| K-5 | REJECTED_FAILED | Raw W-unit pooling failed on the MT5 retail/CFD substrate; literal mechanism needs LOB/TAQ-style depth and trade volume. | rejected_substrate_failed |
| K-6 | REJECTED_FAILED | Pooled K54 v3/v4 training ran and failed global decision gates; same-cohort iteration is closed. | rejected_global_k54_failed |
| K-7 | REJECTED_FAILED | K-7..K-10 additions contributed only below-noise lift in the K54 v3 ablation. | rejected_below_noise |
| K-8 | REJECTED_FAILED | K-7..K-10 additions contributed only below-noise lift in the K54 v3 ablation. | rejected_below_noise |
| K-9 | REJECTED_FAILED | K-9 was below noise in the K54 v3 global model and the global K54 family failed per-cohort floors. | rejected_below_noise |
| K-10 | REJECTED_FAILED | K-10 appeared marginally in some top-100 screens but did not produce decision-grade lift. | rejected_below_noise |
| K-11 | DONE | No backlog blocker remains for the research component; keep as methodology/tooling, not a promotion verdict. | not_strategy_comparable_tooling_done |
| K-12 | DEFERRED_WITH_TRIGGER | Meta-labeling ran, but n=528 with about 250 primary-positive rows was statistically weak and showed no measurable lift. | deferred_sample_size |
| K-13 | DONE | No backlog blocker remains for the research label component. | not_strategy_comparable_tooling_done |
| K-14 | DONE | CPCV proxy exists; true holdout remains a separate deferred validation gate, not an implementation blocker. | not_strategy_comparable_calibration_done |
| K-15 | DONE | Gate is implemented/reported; current K54 features failed stability, which is a result rather than a tooling blocker. | not_strategy_comparable_stability_gate_done |
| K-18 | REJECTED_FAILED | K54 v3 master failed DSR and stability gates; K54 v4 fallback architectures also failed. No same-cohort K54 architecture iteration remains unblocked. | NAS_US30 specialist remains a K55-shadow discovery only: AUC 0.6014106583072101 delta 0.10297805642633234 |

## Interpretation

- `K-5` and `K-6` close as failed for the current substrate/cohort: pooled W-unit normalization did not transmit the published mechanism on MT5 retail CFD data.
- `K-7` through `K-10` close as failed for the current cohort: their combined marginal lift was below noise and should not keep Lane 5 open.
- `K-11`, `K-13`, `K-14`, and `K-15` are done as research/tooling components, even where their empirical gates failed.
- `K-12` is deferred until sample size is high enough for the secondary classifier.
- `K-18` closes as failed globally. The NAS_US30 specialist remains a K55-shadow discovery path only, not a promotion verdict.

## Source Files

- `research/ml_program/audit/Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md`
- `research/ml_program/KILLED_HYPOTHESES.md`
- `research/ml_program/PRE_REGISTERED_HYPOTHESES.md`
- `research/ml_program/models/k54_v3/dsr_per_gate.json`
- `research/ml_program/models/k54_v3/diagnostic_w_unit_ablation.json`
- `research/ml_program/models/k54_v3/feature_stability.json`
- `research/ml_program/models/k54_v3/conformal_calibration.json`
- `research/ml_program/models/k54_v3/specialist_results.json`
- `research/ml_program/models/k54_v4/final_verdicts.json`
- `research/ml_program/models/k54_v4/component_ablation.json`
- `research/ml_program/models/k54_v4/feature_stability.json`

## NO_PROMOTION_VERDICT

This artifact classifies K54-family research state only. It does not validate, promote, or modify live trading behavior.
