# Lane 5 Remaining Architecture / ML Quality Triage

Date: 2026-05-03
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Question

Classify remaining Lane 5 K/P/S architecture and ML-quality items from existing evidence.

## Evidence Summary

- K54 v3 primary lift `0.04835986000202819` failed with DSR-p `0.32095808514499824`; K54 v4 all architectures failed `True` and ship arch `None`.
- T7/NAS routing add over master fallthrough: delta `-0.0052050670338545674`, p `0.5874`.
- NAS_US30 specialist remains discovery/shadow-only: n `113`, AUC `0.6014106583072101`, delta `0.10297805642633234`.
- Tick substrate remains short: max symbol days `5`, symbols with ticks `7`.
- Existing K55 ticket present `True`, target-upgrade-pending text `True`, shadow module exists `False`.

## Task Classifications

| id | status | blocker / trigger | candidate strength |
| --- | --- | --- | --- |
| K-16 | DEFERRED_WITH_TRIGGER | No same-cohort K54 architecture iteration remains unblocked after K54 v3/v4 primary failure; focal loss would be another current-cohort loss-function variant. Trigger: Reopen only with n>=5000 regime-balanced labels or a new label-rich K55 shadow cohort plus a preregistered focal-loss comparison. | deferred_same_cohort_k54_closed |
| K-17 | DEFERRED_WITH_TRIGGER | Pooled K54 v3/v4 training failed global gates, and data-poor instruments still need source-period flags and missing old labels resolved before new pooling claims are meaningful. Trigger: Reopen after missing old labels/source-period flags are fixed and n>=5000 or a new source-balanced cohort exists. | deferred_cohort_quality |
| P-7 | DEFERRED_WITH_TRIGGER | Heartbeat/drawdown thresholds are safety/risk behavior, current tick history is too short for Hawkes calibration, and live threshold changes require CEO approval. Trigger: Research-only simulation after >=30 trading days of all-symbol ticks or approved depth/feed data, followed by a separate approval path for any safety/risk threshold change. | not_strategy_comparable_safety_threshold_research |
| P-8 | DEFERRED_WITH_TRIGGER | The literature-prior is documented, but no local HDP-HMM/Kirby-null research harness has passed; replacing the regime classifier would touch live/shadow behavior. Trigger: Standalone research harness with fat-tailed-mixture Kirby null-test, OOS realized-R comparison, and approval before any runtime replacement. | deferred_literature_prior_no_empirical_gate |
| P-9 | DEFERRED_WITH_TRIGGER | This depends on D-1 tick-count-time substrate maturity and would alter Component 1/tick-daemon runtime behavior; current all-symbol tick history is below the 30-day trigger. Trigger: Reopen after >=30 trading days of all-symbol ticks or an approved feed, then validate as research-only resampling before any live ingestion hook. | deferred_depends_on_d1_tick_substrate |
| P-10 | DEFERRED_WITH_TRIGGER | Feature family has a literature prior, but same-cohort K54 feature iteration is closed after v3/v4 failure; old-label/source-period blockers still constrain new pooled training. Trigger: Reopen as a preregistered feature-family ablation after source flags/missing old labels are fixed and n>=5000 or a new label-rich shadow cohort exists. | deferred_literature_feature_prior_not_empirical |
| S-1 | FILED_FOR_APPROVAL | Design ticket exists, but target assumptions are stale after K54 v4 failed and implementation would touch orchestrator/config live paths. Trigger: Refresh target model to current K55-shadow evidence and obtain explicit approval before scaffold/logger/orchestrator hook implementation. | filed_design_only_no_promotion |
| S-2 | DEFERRED_WITH_TRIGGER | K54 v4 T7-NAS routing add was negative and P-6 is already deferred; routing needs forward K55 specialist evidence first. Trigger: Reopen after K55-shadow specialist evidence clears sample, stability, and approval gates. | deferred_inherits_p6_routing_failure |
| S-3 | DEFERRED_WITH_TRIGGER | No K55 shadow logger/output exists yet; 30-day evaluation requires implementation plus enough forward shadow events. Trigger: Run only after S-1 implementation/smoke test and >=30 days or n>=50 K55-shadow events. | deferred_no_shadow_rows |
| S-4 | DEFERRED_WITH_TRIGGER | No paired live AI+ML shadow dataset exists; current K54 evidence is discovery/refinement only. Trigger: Reopen after S-3 produces paired AI decision, K55 decision, and realized-R rows at preregistered sample floors. | deferred_no_paired_shadow_dataset |
| S-5 | DEFERRED_WITH_TRIGGER | Production flip requires successful S-3/S-4 shadow evaluation, promotion dossier, and explicit CEO approval; no such evidence exists. Trigger: Only after shadow correlation/lift clears the registered gate, including >=1.2x AI where applicable, with a separate promotion dossier. | deferred_requires_future_promotion_dossier |

## Interpretation

- The K/P architecture ideas remain research-useful, but none is executable as a same-cohort K54 architecture iteration now.
- `S-1` is not an unblocked coding task: a design ticket exists, but the target model needs refresh and implementation would touch live orchestrator/config paths.
- `S-2` through `S-5` depend on a working K55 shadow dataset and later promotion evidence; they are not current validation claims.

## Source Files

- `research/ml_program/MASTER_BACKLOG.md`
- `research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md`
- `research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md`
- `research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.json`
- `research/ml_program/audit/D11_2022_2023_BACKFILL_BIAS_CHECK_2026-05-03.json`
- `research/ml_program/models/k54_v3/`
- `research/ml_program/models/k54_v4/`
- `research/ml_program/literature/synthesis/group_a_foundations.md`
- `research/operations/k55_shadow_k54_v3_top3pct_integration_ticket_2026-04-29.md`
- `.context/05_operations/WEEKEND_RESEARCH_GOAL_PROMPT_2026-05-03.md`

## NO_PROMOTION_VERDICT

This artifact classifies architecture and ML-quality readiness only. It does not validate, promote, or modify live trading behavior.
