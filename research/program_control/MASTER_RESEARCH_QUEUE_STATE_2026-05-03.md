# Master Research Queue State

Date: 2026-05-03
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Control Summary

- Total queue items: `192`.
- Master-backlog items: `180`.
- Generated follow-up/control items: `12`.
- Stronger-than-baseline candidates: `['P1-C-V3-FVG-ONLY-RESCUE']`.
- Promotion-allowed items: `[]`.

Status counts:

| status | count |
| --- | --- |
| ACCEPTED_CANDIDATE_DISCOVERY | 2 |
| BLOCKED_WITH_REASON | 40 |
| DEFERRED_WITH_TRIGGER | 59 |
| DONE | 60 |
| FILED_FOR_APPROVAL | 10 |
| REJECTED_FAILED | 20 |
| STRONGER_THAN_BASELINE_CANDIDATE | 1 |

Lane counts:

| lane | count |
| --- | --- |
| lane_0_control_tower | 7 |
| lane_1_methodology | 19 |
| lane_2_path_scaling | 6 |
| lane_3_execution_telemetry | 10 |
| lane_4_orderflow_proxy_sierra | 18 |
| lane_5_data_ml_quality | 48 |
| lane_6_asset_risk_edge | 53 |
| lane_7_recurring_open_questions | 31 |

## Backlog Delta Report

Artifact-backed deltas and status clarifications found while reconciling the backlog:

| id | backlog status | queue status | artifact | note | follow-ups |
| --- | --- | --- | --- | --- | --- |
| M-5 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.md | Current empirical read keeps AFML/CPCV-honest as promotion doctrine; exact per-symbol Inoue-Kilian/Diebold resolution is data-blocked. |  |
| M-6 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.md | Romano-Wolf StepM harness exists and is smoke-tested, but the requested 47-cell empirical panel is absent. |  |
| C-9 | BLOCKED | BLOCKED_WITH_REASON | research/phase_3_external_feed_validation/LANE2_C7_C9_PATH_SCALING_TRIAGE_2026-05-03.md | Protocol/V0/V2/V2b/V3 subcomponents exist, but the exact L2 on/off and close-and-reenter comparison remains blocked rather than failed. |  |
| O-3 | BLOCKED | BLOCKED_WITH_REASON | research/operations/LANE3_EXECUTION_TELEMETRY_VERIFIERS_2026-05-03.md | Repo-side triage confirms O-3 is operator-only, not an unblocked research/coding task. |  |
| O-5 | BLOCKED | BLOCKED_WITH_REASON | research/operations/LANE3_EXECUTION_TELEMETRY_VERIFIERS_2026-05-03.md | Repo-side triage confirms O-5 is operator/admin maintenance, not an unblocked research/coding task. |  |
| E-4 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md | F11-vs-retail-flow regression is blocked until a retail-flow-share proxy exists. |  |
| A-2 | BLOCKED | BLOCKED_WITH_REASON | research/operations/LANE4_OPTIONS_GAMMA_PROXY_TRIAGE_2026-05-03.md | Lane 4 triage found VIX1D/VIX9D absent from local external-feed inventory; A-2 is data/source blocked, not executable. |  |
| A-3 | BLOCKED | BLOCKED_WITH_REASON | research/operations/LANE4_OPTIONS_GAMMA_PROXY_TRIAGE_2026-05-03.md | Lane 4 triage keeps A-3 blocked until VRP source, estimator, and publication-time convention are registered. |  |
| A-6 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | GBP specialist feature construction is source-blocked, not an ML architecture task. |  |
| U-2 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | FlashAlpha Basic proxy data exists, but gamma sign is not constructible from MT5 OHLC/tick data alone. |  |
| X-3 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Do not substitute candle direction for signed trade imbalance. |  |
| D-12 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md | Lane 5 data-source triage blocks D-12 on broker history availability; current redacted_account MT5 cannot supply full pre-2022 coverage. |  |
| D-2 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md | Lane 5 remaining data/feed triage blocks D-2 on broker tick-history retention. |  |
| D-4 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md | Lane 5 data-source triage confirms the CFTC infrastructure/gold cache exists, but the full gold+FX backlog item remains blocked. |  |
| D-5 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md | Lane 5 data-source triage confirms LBMA calendar exists, but the full LBMA+KMW FX-fix backlog item remains blocked. |  |
| D-7 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md | Lane 5 remaining data/feed triage blocks D-7 until a legal H-K-M/intermediary-capital source is registered. |  |
| D-8 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md | Lane 5 remaining data/feed triage confirms FRED is ready but BIS is absent. |  |
| D-9 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md | Lane 5 remaining data/feed triage blocks D-9 because the requested Fed research feed is not specified or cached beyond FRED. |  |
| S-1 | FILED | FILED_FOR_APPROVAL | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | K55 shadow design is filed, but not an unblocked coding task in this research loop. |  |
| D-11 | DONE | DONE | research/ml_program/audit/D11_2022_2023_BACKFILL_BIAS_CHECK_2026-05-03.md | Bias audit completed; old backfill usable with downsampling/source flags, not live-equivalent. | D11-REGENERATE-GBPJPY-US30CASH-OLD-LABELS, D11-SOURCE-PERIOD-FEATURE-FLAGS |
| D-6 | DONE | DONE | research/operations/weekend_backlog_ops_triage_2026-05-03.md | Alias boundary documented: NAS100 canonical, NDX100 redacted_account broker alias, US100.cash historical demo context. | ALIAS-HYGIENE-CENTRALIZE-EXTRACTION-MAPPING |
| O-1 | FILED | DONE | research/operations/weekend_backlog_ops_triage_2026-05-03.md | _trade_index.json staleness refreshed; implementation/verifier split into generated Lane 3 follow-up. | O1-INDEX-REBUILD-OR-STALE-VERIFIER |
| O-2 | DONE | DONE | research/operations/weekend_backlog_ops_triage_2026-05-03.md | Alias triage filed and no live-code change needed. |  |
| O-8 | FILED | DONE | research/operations/weekend_backlog_ops_triage_2026-05-03.md | Gap audit completed; lifecycle-aware completeness verifier split into generated Lane 3 follow-up. | O8-LIFECYCLE-COMPLETENESS-VERIFIER |
| U-11 | DONE | DONE | research/ml_program/audit/D11_2022_2023_BACKFILL_BIAS_CHECK_2026-05-03.md | Open research question answered by D-11 audit; follow-ups are data generation/source-flag tasks. | D11-REGENERATE-GBPJPY-US30CASH-OLD-LABELS, D11-SOURCE-PERIOD-FEATURE-FLAGS |
| M-10 | DONE | DONE | research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.md | SPA-style stationary bootstrap applied to K54 v2/v3/v4 lift series with explicit CPCV-path-dependence caveat; diagnostic only, no promotion p-values. |  |
| M-11 | DONE | DONE | research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.md | Fold-aggregated paired AUC DM-style HAC diagnostics reconstructed for K54 v2/v3 where per-row CPCV predictions exist. |  |
| M-12 | DONE | DONE | research/ml_program/audit/METHODOLOGY_INFRASTRUCTURE_GATE_2026-05-03.md | Effective-N and cumulative trial-budget helpers implemented in research_infra methodology gate. |  |
| M-13 | DONE | DONE | research/ml_program/audit/METHODOLOGY_INFRASTRUCTURE_GATE_2026-05-03.md | PBO hardened-claim gate implemented and current primary artifacts audited; promotion p-values allowed count remains zero. |  |
| M-14 | DONE | DONE | research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.md | K54 v3 conformal calibration has Christoffersen proxy coverage p=0.00158; holdout remains deferred, no validation claim. |  |
| M-15 | DONE | DONE | research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.md | Bayesian normal-normal posterior track applied to K54-class lifts under CPCV-weighted SE and skeptical prior; parallel evidence only. |  |
| M-16 | DONE | DONE | research/ml_program/audit/Q13_CPCV_BIAS_VARIANCE_BOOKKEEPING_2026-05-03.md | Q1.3 +0.030896 lift classified variance-dominated: 13.1% signal share vs 86.9% path-variance share. |  |
| M-7 | DONE | DONE | research/ml_program/audit/METHODOLOGY_INFRASTRUCTURE_GATE_2026-05-03.md | Implemented in src/research_infra/methodology_gate.py and audited across current primary methodology artifacts; historical Stouffer fields are archived and blocked from promotion use. |  |
| C-7 | DONE | DONE | research/phase_3_external_feed_validation/LANE2_C7_C9_PATH_SCALING_TRIAGE_2026-05-03.md | Path-9 was Feb-heavy and cross-cohort, not single-symbol; replication scan shows temporal fragility rather than stable all-window lift. |  |
| D-3 | DONE | DONE | research/operations/LANE4_OPTIONS_GAMMA_PROXY_TRIAGE_2026-05-03.md | FlashAlpha Basic single-expiry GEX proxy integration is complete and locally cached for QQQ/DIA/SPY/GLD/SLV; no alpha or official-CBOE validation claim. |  |
| K-14 | DONE | DONE | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | Adaptive conformal calibration CPCV proxy exists; coverage was 0.881 vs 0.900 target with Christoffersen p 0.00158. |  |
| P-3 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md | Adaptive conformal module is deferred as system-flow work even though the CPCV proxy exists. |  |
| D-1 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md | Lane 5 data-source triage defers D-1 until tick history/substrate trigger is met; tick capture/helpers are present but not volume/dollar/imbalance bar infrastructure. |  |
| D-10 | DONE | DONE | research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md | Lane 5 remaining data/feed triage closes D-10 as WGC data plumbing; local GDT/ETF imports include central-bank/other-institution rows. |  |
| K-10 | FAILED | REJECTED_FAILED | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | Above-up/below-down round-aligned feature is closed for the current K54 cohort. |  |
| K-11 | DONE | DONE | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | Per-fold top-100 screening ran in K54 v3/v4; empirical stability failed, but the component is not pending. |  |
| K-12 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | Component 3A meta-labeling head is deferred on sample size rather than unblocked. |  |
| K-13 | DONE | DONE | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | Triple-barrier labels fed the K54 v3 meta-label head; no K-13 tooling blocker remains. |  |
| K-15 | DONE | DONE | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | TreeSHAP-style stability gate is reported; current K54 features have only 2 stable features and mean Jaccard 0.169. |  |
| K-16 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | Remaining Lane 5 architecture triage defers K-16 until a larger/source-balanced cohort or shadow cohort exists. |  |
| K-17 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | Remaining Lane 5 architecture triage defers hierarchical pooling until cohort/data-quality blockers clear. |  |
| K-18 | FAILED | REJECTED_FAILED | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | K54 v3/v4 global architecture work is closed for the current cohort; top-3%/NAS_US30 findings remain shadow/discovery paths only. |  |
| K-5 | FAILED | REJECTED_FAILED | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | K54 v3 W-unit ablation shows ON AUC 0.510 vs OFF AUC 0.564; current substrate closes K-5. |  |
| K-6 | FAILED | REJECTED_FAILED | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | K54 v3 DSR-p 0.321 and K54 v4 all-architecture fail close pooled multi-instrument K54 as an unblocked lane item. |  |
| K-7 | FAILED | REJECTED_FAILED | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | Osler stop-cluster proxy was marginal/not top-50; K-7 does not remain unblocked on the current cohort. |  |
| K-8 | FAILED | REJECTED_FAILED | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | Power-law OB-age weighting is closed for the current cohort as part of the below-noise K-7..K-10 feature block. |  |
| K-9 | FAILED | REJECTED_FAILED | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | Regime/round/side interaction does not remain an unblocked architecture task on the current cohort. |  |
| P-1 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md | Component 3C portfolio-wide overlay is deferred; only a NAS100-only shadow/approval path remains. |  |
| P-10 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | Remaining Lane 5 architecture triage keeps signature/fractional/HAR-RV features as a future preregistered feature refresh, not current K54 iteration. |  |
| P-2 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md | Component 3D module inherits K-12 sample-size deferral. |  |
| P-5 | FAILED | REJECTED_FAILED | research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md | Pooled multi-instrument training pipeline is closed for the current substrate/cohort. |  |
| P-6 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md | Per-instrument-group inference routing remains deferred after K54 v4 routing ablation failed. |  |
| P-7 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | Remaining Lane 5 architecture triage defers Hawkes threshold work until data and approval triggers exist. |  |
| P-8 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | Remaining Lane 5 architecture triage defers sticky HDP-HMM until the Kirby null-test and OOS harness exist. |  |
| P-9 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | Remaining Lane 5 architecture triage defers trade-count-time triggers until D-1 substrate maturity and approval. |  |
| S-2 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | S-2 inherits P-6 routing deferral after K54 v4 routing ablation failed. |  |
| S-3 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | K55 30-day evaluation is deferred until shadow rows exist. |  |
| S-4 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | Hybrid ML+AI measurement is deferred until paired shadow data exists. |  |
| S-5 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | K55 production flip remains deferred and cannot be inferred from current discovery artifacts. |  |
| B-6 | COMPLETED | DONE | research/ml_program/audit/METHODOLOGY_INFRASTRUCTURE_GATE_2026-05-03.md | Methodology-discipline bundle closed for current/future research claims: weighted SE, effective-N/trial counter, and PBO hardened-claim gate are now in research_infra. |  |
| E-1 | FAILED | REJECTED_FAILED | research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md | Current Osler/K-7 proxy path is closed as failed; this does not disprove true counterparty stop clustering. |  |
| A-8 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md | Lane 6 triage blocks A-8 until the real-gold deflator/source and no-leak construction are registered. |  |
| C-2 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md | Disposition-effect feature work is blocked on unobserved counterparty stop-placement data. |  |
| E-2 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md | Toth-Bouchaud V-shape work is deferred until the tick/depth substrate is mature enough for the mechanism. |  |
| V-1 | DONE | DONE | research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md | Lane 6 triage closes V-1 because realized-vol-rank tooling exists in H-PM01/H-PM03/NA8; sizing integration remains deferred elsewhere. |  |
| V-2 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md | Lane 6 triage keeps VRP blocked on source/construction, consistent with A-3. |  |
| V-3 | DONE | DONE | research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md | K54 regime feature family already includes run-length, flip-window, and score-dynamics persistence features. |  |
| A-12 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | LBMA calendar readiness does not supply the KMW top-9-currency FX-fix dataset. |  |
| A-13 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | FRED cache is partial and does not complete the Brunnermeier-Nagel-Pedersen funding-liquidity feature. |  |
| A-14 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | Aquilina-style JPY carry-unwind classifier is source-blocked until BIS data is registered. |  |
| A-16 | FILED | FILED_FOR_APPROVAL | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | DCC/cDCC/Block-DECO is filed as an approval-gated risk-model replacement, not an unblocked live-code change. |  |
| A-4 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | NAS_US30 specialist retrain cannot verify the sign-flip cure from current local inputs. |  |
| A-5 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | Local FRED/DXY/VIX partial macro cache is insufficient for JPY carry factor decomposition. |  |
| A-7 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | FRED cache has yields, DXY, VIX/GVZ, and inflation proxies, but not the full dollar-specialist feature set. |  |
| B-4 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | Most constituent specialist features lack source-complete as-of data. |  |
| B-7 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | No bundle-level edge-mechanism validation can proceed from current local data. |  |
| C-3 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | knowledge_base/inverted_tp_log.jsonl has 66 rows, but current keys lack realized-R/outcome and symbol linkage. |  |
| C-8 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | K54 v3 mean Jaccard=0.1685447455309013 with 2 stable features; deployment-performance regression awaits K55 rows. |  |
| E-3 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | Do not substitute candle direction or retail tick volume for signed meta-order flow. |  |
| X-1 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Current tick cache is quote/retail-substrate limited. |  |
| X-2 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Use only after futures/venue trade-volume data exists. |  |
| A-15 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Same blocker as D-7; FRED/WGC/CFTC feeds do not supply H-K-M intermediary-capital SDF. |  |
| B-5 | FILED | FILED_FOR_APPROVAL | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Tool scaffolding exists, but live AI behavior changes need explicit CEO approval; Component 3B debate remains dormant by owner decision. |  |
| X-7 | FILED | FILED_FOR_APPROVAL | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Recovered template exists, but no prompt rebuild is an unblocked research-loop change. |  |
| L-1 | FILED | FILED_FOR_APPROVAL | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | ai_tools scaffolding and design exist, but PrimaryAnalyzer does not import ai_tools. |  |
| L-2 | FILED | FILED_FOR_APPROVAL | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Current ai_tools files include recent-outcome/session-vol registry scaffolding. |  |
| L-4 | FILED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Debate code/tests exist, but orchestrator does not import debate; keep it out of near-term approval queue. |  |
| U-1 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Current doctrine remains AFML/CPCV-honest; exact per-instrument Inoue-Kilian resolution is data-blocked. |  |
| U-12 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Erb-Harvey remains a literature lens, not a locally validated decay attribution feature. |  |
| U-6 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Same substrate blocker as X-1/X-2/X-3; do not relabel quote-tick count as trade-count time. |  |
| L-3 | FILED | FILED_FOR_APPROVAL | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | AdaptiveReview exists, but this is not a live Reflexion loop. |  |
| U-8 | BLOCKED | BLOCKED_WITH_REASON | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Lane 7 triage found no local H-K-M/intermediary-capital source. |  |
| A-1 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | FlashAlpha GEX has 15 local proxy rows; gamma sign is forward-only until the history trigger is met. |  |
| U-14 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Current monitor observes decay but does not validate McLean-Pontiff publication-decay rate on GTOS edge. |  |
| X-5 | DONE | DONE | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Rough-vol proxy H estimated on 7 symbols from local M15 data; median H=0.5050851741228051, range=[0.48422314477656087, 0.6033981383377698]. |  |
| B-2 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | H-PM01 portfolio delta mean R=-0.004960547358764833 with DSR-p=0.9999646857030353; NAS100-only remains a future shadow candidate. |  |
| B-3 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | Combined MC supports shipped full-stack risk; no replacement policy is validated. |  |
| C-5 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | Sharpe-objective training is a future K-family loss-function study, not current-cohort work. |  |
| C-6 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | Existing MC covers fixed policy overlays; continuous sizing remains future research after label-truth blockers clear. |  |
| R-1 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | Current evidence supports shipped S79/full-stack risk, not replacing it with RCK. |  |
| R-2 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | No lambda knob is approved or validated for FN constraint auto-calibration. |  |
| R-5 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | Existing S79/full-stack evidence remains the active baseline. |  |
| R-7 | FAILED | REJECTED_FAILED | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | All-7 vol-scaled sizing failed portfolio-wide in H-PM01: delta mean R=-0.004960547358764833, DSR-p=0.9999646857030353. |  |
| R-9 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | Risk-policy bundle cannot replace S79/full-stack from current evidence. |  |
| V-5 | FAILED | REJECTED_FAILED | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Barroso-Santa-Clara vol-managed backtest failed portfolio-wide: delta mean R=-0.004960547358764833, delta Sharpe=-2.5761764707408985%, DSR-p=0.9999646857030353. |  |
| V-6 | FAILED | REJECTED_FAILED | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Vol-managed sizing vs uniform 2% A/B is H-PM01 and failed portfolio-wide. |  |
| V-8 | FAILED | REJECTED_FAILED | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Moreira-Muir/Barroso broad vol-scaling fails as an all-symbol policy; NAS100-only remains shadow/deferred. |  |
| V-9 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Keep only NAS100-only shadow/approval route open from current H-PM01 evidence. |  |
| R-3 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Keep as future risk-policy replacement branch, not an unblocked live implementation. |  |
| R-4 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Do not alter live drawdown behavior from current evidence. |  |
| X-4 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Current tick cache has 30 parquet files across 7 symbols. |  |
| A-11 | DONE | DONE | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | LBMA fix-calendar feature feasibility is satisfied for metals via the normalized calendar cache. |  |
| A-9 | DONE | DONE | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | Gold COT feed feasibility is satisfied for XAUUSD via the normalized CFTC cache; no alpha validation is implied. |  |
| C-4 | DONE | DONE | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | Daniel-Moskowitz-style LONG modifier simulation is closed by H-PM03/combined MC: side_aware_everywhere H2 P(pass)=0.7806666666666666 and full P(bust HARD)=0.022. |  |
| E-5 | DONE | DONE | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | Uncorrelated-edge discovery inventory is current via NA-11 plus queue state; live candidates remain discovery/forward-shadow only. |  |
| R-6 | DONE | DONE | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | Side-aware sizing is closed by H-PM03/combined MC and existing config flip: full P(bust HARD)=0.022. |  |
| R-8 | DONE | DONE | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | Lambda-context audit is resolved at control level; any lambda-knob replacement is deferred under R-1/R-2. |  |
| V-4 | DONE | DONE | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Sigma multiplier mapping exists in H-PM01: bsc_sigma_mult = clip(median_vol / realized_vol_30d, 0.5, 2.0). |  |
| V-7 | DONE | DONE | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Daniel-Moskowitz-style LONG/side-aware sizing is closed by H-PM03/combined MC. |  |
| X-6 | DONE | DONE | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | K54 v1 0.571 was reconciled by canonical_v1_rerun/K1 follow-ups; promotion anchor is CPCV-honest 0.5286. |  |
| L-8 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | No Sonnet-class transfer test can be run before the grounding intervention exists in a shadow harness. |  |
| RR-1 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Existing local literature corpus remains usable, but RR-1 specifically asks for current last-6-month paper discovery. |  |
| RR-4 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Local killed-hypothesis and backlog artifacts are current, but new-literature refresh is not a local-evidence task. |  |
| RR-7 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | No local source can prove that no domain paper expired or was retracted. |  |
| A-10 | DONE | DONE | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | WGC data plumbing exists with latest demand rows=9475 and central-bank-like rows=162; alpha validation remains separate. |  |
| A-17 | DONE | DONE | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Copula/tail-dependence diagnostic ran on 13064 aligned M15 returns and 21 pairs; feature feasibility only. |  |
| A-18 | DONE | DONE | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | Forbes-Rigobon adjusted high-vol correlations are included in the tail-correlation diagnostic; feature feasibility only. |  |
| L-5 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Current K54 global architectures failed; L-5 is a future architecture path, not an unblocked implementation. |  |
| RR-5 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Current live prop-account scale does not trigger capacity analysis. |  |
| RR-6 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Current alpha inventory is not enough to estimate a hypothesis-portfolio correlation matrix. |  |
| U-10 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Tool scaffolding exists but PrimaryAnalyzer does not import ai_tools. |  |
| U-13 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Same practical trigger as RR-5. |  |
| U-15 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Session-45 pivot references Renaissance-style candidates, but this item is not locally closed as a deep dive. |  |
| U-16 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | No local HDP-HMM/Kirby-null harness has passed. |  |
| Z-1 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Local quantum-related research files found but no GTOS implementation path is unblocked. |  |
| Z-2 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Quantum Monte Carlo is not an unblocked GTOS trading-research task. |  |
| Z-3 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Quantum RL review is not an unblocked GTOS trading-research task. |  |
| Z-4 | DEFERRED | DEFERRED_WITH_TRIGGER | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | IBM/Goldman quantum derivatives literature follow is not an unblocked GTOS trading-research task. |  |
| RR-2 | DONE | DONE | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Current DSR/effective-N tracker snapshot has 15 DSR rows and promotion-p-value allowed count 0. |  |
| RR-3 | DONE | DONE | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Current OB continuation snapshot has latest date 2026-05-01 with 0 alarms; monthly decay report exists. |  |
| U-17 | DONE | DONE | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Path-9 is Feb-heavy and cross-cohort, not single-symbol; fold 4 turns negative after the window and cached FRED shows elevated gold volatility. |  |
| U-4 | DONE | DONE | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Per-instrument/group sweep is answered by K54 v3/v4 triage: global K54 failed; strongest remaining group is NAS_US30 specialist discovery. |  |
| U-9 | DONE | DONE | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | Live config/code scan found 0 literal lambda=2 hits; relevant risk/ratio knobs are config-driven. |  |

## Next Unblocked Ranked Items

| priority | id | lane | artifact required | tests required |
| --- | --- | --- | --- | --- |

## Blocked And Deferred Triggers

| id | status | blocked by | trigger/artifact required |
| --- | --- | --- | --- |
| M-5 | BLOCKED_WITH_REASON | Exact 7-symbol per-instrument resolution needs full 2022-2023 v2/v3 feature catalog and old mechanical labels for missing symbols; current evidence is v1-schema/effective-group only. | rerun after D11 missing labels and v2/v3 feature backfill exist |
| M-6 | BLOCKED_WITH_REASON | No observations x 47 instrument-side-regime cell performance-differential matrix was found in current artifacts. | 47-cell cell_id x observation/fold matrix with candidate and benchmark metrics |
| C-9 | BLOCKED_WITH_REASON | Full C-9 needs deterministic L2 reconstruction, resolved V2b post-cutoff OB-boundary/J46 pairs, pending lifecycle + original POI/pre-fill fields for reentry, and measured cost/slippage. | L2 reconstruction plus resolved V2b rows plus lifecycle/pre-fill join before full ablation/reentry validation |
| P1-D-V2B-ROLLING-STATUS-TOOL | BLOCKED_WITH_REASON | 0 resolved post-cutoff OB-boundary/J46 pairs; keep collection/replay running. | resolved prospective pair rows reaching registered sample floors |
| O-3 | BLOCKED_WITH_REASON | Operator must enable the Windows scheduled-task 'Wake the computer to run this task' setting and verify the next active kill-zone wake cycle. | operator confirmation plus next active KZ wake verification |
| O-5 | BLOCKED_WITH_REASON | Disk cleanup and pagefile raise require OS/admin action outside repo research tooling. | operator/admin completion plus rerun of ops checks |
| E-4 | BLOCKED_WITH_REASON | F11/OB-decay artifacts exist, but no retail-flow-share proxy, broker client-sentiment cache, Google Trends cache, or social-flow dataset is available locally. | legal retail-flow-share proxy with time coverage aligned to F11 windows |
| A-2 | BLOCKED_WITH_REASON | Local external-feed inventory has VIXCLS/GVZCLS but no VIX1D or VIX9D cache/source; the spread cannot be constructed without a confirmed legal/free source. | confirmed legal/free VIX1D and VIX9D source plus no-leak as-of fetch/cache |
| A-3 | BLOCKED_WITH_REASON | No local VRP, VIX futures, implied-variance term-structure, or registered realized-vol estimator source exists in data/external. | no-leak VRP construction spec with as-of implied-vol/variance source and realized-vol estimator |
| A-6 | BLOCKED_WITH_REASON | No local BoE policy, GBP political-risk, or registered legal proxy feed exists. | legal BoE/GBP policy-risk source contract and cache |
| U-2 | BLOCKED_WITH_REASON | MT5 alone has no option dealer gamma sign, VIX1D/VIX9D, VRP, or official GEX source. | external options/gamma source or approved proxy contract |
| X-3 | BLOCKED_WITH_REASON | Imbalance-bar E24/E26 retest needs signed trades or aggressor-side proxy; current local data is OHLCV/quote-tick only. | approved signed-trade/aggressor-side feed |
| D-12 | BLOCKED_WITH_REASON | Current MT5 history probes show no full 2021 all-symbol M15 coverage; only XAGUSD has a small late-2021 slice. | alternate broker/provider/archive for pre-2022 OHLCV coverage |
| D-2 | BLOCKED_WITH_REASON | Local MT5 tick probes and tick-capture cache do not provide pre-2024 tick history; broker retention only covers recent windows. | alternate broker/provider/archive or paid historical tick/LOB source with pre-2024 coverage |
| D-4 | BLOCKED_WITH_REASON | CFTC fetcher and XAUUSD gold cache exist, but no local FX COT contract mappings/rows are present. | official CFTC FX contract map plus fetched/cached FX COT rows with publication-time guards |
| D-5 | BLOCKED_WITH_REASON | LBMA gold/silver fix calendar exists, but no local Krohn-Mueller-Whelan FX-fix source/cache is present. | confirmed KMW FX-fix source/licensing path or registered legal FX-fix proxy |
| D-7 | BLOCKED_WITH_REASON | No local H-K-M/intermediary-capital SDF source, status file, normalized cache, or registered source spec was found. | legal H-K-M source/access path plus no-lookahead publication metadata |
| D-8 | BLOCKED_WITH_REASON | FRED macro cache exists, but no BIS source/cache/spec exists locally; full FRED/BIS item remains incomplete. | BIS macro source tables cached with publication-time metadata and joined to existing FRED cache |
| D-9 | BLOCKED_WITH_REASON | No distinct Federal Reserve research-feed source contract, parser, status file, or normalized cache exists beyond the FRED macro feed. | defined Federal Reserve research source, fields, cadence, publication-time model, and parser/cache |
| A-8 | BLOCKED_WITH_REASON | Local feeds have XAUUSD nominal bars plus FRED real-rate/inflation-expectation proxies, but no CPI/PCE deflator or pre-registered real-gold-price percentile construction. | legal CPI/PCE deflator source with publication-time metadata and registered real-gold-price percentile lookback |
| P1-F-PROXY-MAPPING-WEEKEND-FORENSICS | DEFERRED_WITH_TRIGGER | Needs approved/pre-registered USDJPY/6J price-transfer follow-up data; no broad paid pulls. | registered price-transfer follow-up before depth or alpha features |
| P-3 | DEFERRED_WITH_TRIGGER | K54 global candidates failed; conformal has only a CPCV proxy and no live/holdout system-flow candidate to calibrate. | approved K55/K54 shadow candidate plus preregistered holdout/calibration window |
| D-1 | DEFERRED_WITH_TRIGGER | Tick capture exists for 7/7 symbols, but local history is only 5 days at best and MT5 retail volume/last fields are not a real volume/dollar substrate. | >=30 trading days of all-symbol tick captures or approved paid LOB/trade feed |
| K-12 | DEFERRED_WITH_TRIGGER | Meta-labeling ran, but n=528 with about 250 primary-positive rows was statistically weak and showed no measurable lift. | n>5000 or new label-rich K55 shadow cohort |
| K-16 | DEFERRED_WITH_TRIGGER | No same-cohort K54 architecture iteration remains unblocked after K54 v3/v4 primary failure; focal loss would be another current-cohort loss-function variant. | n>=5000 regime-balanced labels or new label-rich K55 shadow cohort plus preregistered focal-loss comparison |
| K-17 | DEFERRED_WITH_TRIGGER | Pooled K54 v3/v4 training failed global gates, and data-poor instruments still need source-period flags and missing old labels resolved before new pooling claims are meaningful. | source-period flags, missing old labels resolved, and n>=5000 or source-balanced expanded cohort |
| P-1 | DEFERRED_WITH_TRIGGER | Portfolio-wide vol-conditioning failed H-PM01; live insertion between 3A and execution would change risk/trading behavior and needs CEO approval even for shadow. | CEO approval for NAS100-only shadow A/B or fresh portfolio-wide preregistration that clears gates |
| P-10 | DEFERRED_WITH_TRIGGER | Feature family has a literature prior, but same-cohort K54 feature iteration is closed after v3/v4 failure; old-label/source-period blockers still constrain new pooled training. | preregistered feature-family ablation after source flags/missing old labels are fixed and n>=5000 or new label-rich shadow cohort exists |
| P-2 | DEFERRED_WITH_TRIGGER | Meta-labeling ran in K54 v3 but was statistically weak at the current cohort size. | n>5000 or new label-rich K55 shadow cohort plus CEO approval for live system-flow wiring |
| P-6 | DEFERRED_WITH_TRIGGER | K54 v4 T7-NAS routing add was negative and all K54 v4 architectures failed; any inference routing layer is shadow-only until a specialist survives forward evidence. | K55-shadow specialist evidence clearing sample, stability, and approval gates |
| P-7 | DEFERRED_WITH_TRIGGER | Heartbeat/drawdown thresholds are safety/risk behavior, current tick history is too short for Hawkes calibration, and live threshold changes require CEO approval. | >=30 trading days all-symbol ticks or approved depth/feed data plus research-only simulation before approval path |
| P-8 | DEFERRED_WITH_TRIGGER | The literature-prior is documented, but no local HDP-HMM/Kirby-null research harness has passed; replacing the regime classifier would touch live/shadow behavior. | standalone HDP-HMM research harness with Kirby fat-tailed-mixture null-test and OOS realized-R comparison |
| P-9 | DEFERRED_WITH_TRIGGER | This depends on D-1 tick-count-time substrate maturity and would alter Component 1/tick-daemon runtime behavior; current all-symbol tick history is below the 30-day trigger. | >=30 trading days all-symbol ticks or approved feed plus research-only trade-count resampling validation |
| S-2 | DEFERRED_WITH_TRIGGER | K54 v4 T7-NAS routing add was negative and P-6 is already deferred; routing needs forward K55 specialist evidence first. | K55-shadow specialist evidence clearing sample, stability, and approval gates |
| S-3 | DEFERRED_WITH_TRIGGER | No K55 shadow logger/output exists yet; 30-day evaluation requires implementation plus enough forward shadow events. | S-1 implementation/smoke test plus >=30 days or n>=50 K55-shadow events |
| S-4 | DEFERRED_WITH_TRIGGER | No paired live AI+ML shadow dataset exists; current K54 evidence is discovery/refinement only. | paired AI decision, K55 decision, and realized-R rows from S-3 at preregistered sample floors |
| S-5 | DEFERRED_WITH_TRIGGER | Production flip requires successful S-3/S-4 shadow evaluation, promotion dossier, and explicit CEO approval; no such evidence exists. | successful K55 shadow gate, separate promotion dossier, and explicit CEO approval |
| E-2 | DEFERRED_WITH_TRIGGER | Current all-symbol MT5 tick coverage is short and quote-only; Toth-Bouchaud latent-liquidity shape needs mature tick/depth/order-flow evidence. | >=30 trading days all-symbol ticks or approved depth/order-flow feed plus preregistered V-shape estimator |
| L-4 | DEFERRED_WITH_TRIGGER | Owner decision 2026-05-03: leave Component 3B debate dormant because it is down-road work and adds extra AI/API cost. | Reopen only with explicit CEO request plus a shadow-only, budget-capped debate design |
| A-1 | DEFERRED_WITH_TRIGGER | Local FlashAlpha GEX proxy exists but only forward/current snapshots are cached; no legal historical gamma-sign series is available for NAS/US30 cross-period sign-flip validation. | >=30 trading days of FlashAlpha snapshots or legal historical CBOE/GEX data |

## Full Queue Index

| priority | id | lane | status | blocked_by | artifact | candidate strength |
| --- | --- | --- | --- | --- | --- | --- |
| 5 | P0-SOURCE-MAP | lane_0_control_tower | DONE |  | research/phase_3_external_feed_validation/WEEKEND_NO_FORWARD_DATA_SOURCE_MAP_2026-05-03.md | not_applicable |
| 120 | M-5 | lane_1_methodology | BLOCKED_WITH_REASON | Exact 7-symbol per-instrument resolution needs full 2022-2023 v2/v3 feature catalog and old mechanical labels for missing symbols; current evidence is v1-schema/effective-group only. | research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.md | not_applicable |
| 120 | M-6 | lane_1_methodology | BLOCKED_WITH_REASON | No observations x 47 instrument-side-regime cell performance-differential matrix was found in current artifacts. | research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.md | not_applicable |
| 205 | P1-A-V2-CONFLUENCE-DEEPDIVE | lane_2_path_scaling | ACCEPTED_CANDIDATE_DISCOVERY | Unseen/forward confluence rows required before validation. | research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_CONFLUENCE_DEEPDIVE_2026-05-03.md | positive_same_dataset_discovery_vs_j46; FVG delta full +0.033292R, 2026 +0.365975R; OB delta full +0.024061R, 2026 +0.233839R; no promotion |
| 206 | P1-C-V3-FVG-ONLY-RESCUE | lane_2_path_scaling | STRONGER_THAN_BASELINE_CANDIDATE | Same-dataset exploratory replay only; needs V2b/forward resolved rows, lifecycle telemetry, and promotion dossier if CEO asks. | research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_FULL_EXPLORATORY_REPLAY_2026-05-03.md | V3_FVG_ONLY_RESCUE_RISK_BANK mean delta vs J46 +0.270259R on existing replay; discovery-only stronger candidate, not validation |
| 210 | C-9 | lane_2_path_scaling | BLOCKED_WITH_REASON | Full C-9 needs deterministic L2 reconstruction, resolved V2b post-cutoff OB-boundary/J46 pairs, pending lifecycle + original POI/pre-fill fields for reentry, and measured cost/slippage. | research/phase_3_external_feed_validation/LANE2_C7_C9_PATH_SCALING_TRIAGE_2026-05-03.md | partial_chain_positive_discovery_only; V3 FVG-only rescue delta +0.270259R vs J46 on same-dataset replay, no promotion |
| 210 | P1-D-V2B-ROLLING-STATUS-TOOL | lane_2_path_scaling | BLOCKED_WITH_REASON | 0 resolved post-cutoff OB-boundary/J46 pairs; keep collection/replay running. | research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2B_ROLLING_STATUS_TOOL_2026-05-03.md | blocked_no_resolved_prospective_pairs |
| 310 | L-6 | lane_3_execution_telemetry | FILED_FOR_APPROVAL |  |  | not_applicable |
| 310 | O-3 | lane_3_execution_telemetry | BLOCKED_WITH_REASON | Operator must enable the Windows scheduled-task 'Wake the computer to run this task' setting and verify the next active kill-zone wake cycle. | research/operations/LANE3_EXECUTION_TELEMETRY_VERIFIERS_2026-05-03.md | not_applicable_operator_action |
| 310 | O-5 | lane_3_execution_telemetry | BLOCKED_WITH_REASON | Disk cleanup and pagefile raise require OS/admin action outside repo research tooling. | research/operations/LANE3_EXECUTION_TELEMETRY_VERIFIERS_2026-05-03.md | not_applicable_operator_action |
| 310 | O-6 | lane_3_execution_telemetry | FILED_FOR_APPROVAL |  |  | not_applicable |
| 330 | P2-I-PENDING-LIMIT-LIFECYCLE-TELEMETRY | lane_3_execution_telemetry | FILED_FOR_APPROVAL | CEO/main-thread approval required before touching execution.py or orchestrator.py. | research/operations/pending_limit_lifecycle_telemetry_integration_ticket_2026-05-03.md | not_applicable_label_truth_tooling |
| 405 | P1-E-NAS100-CACHED-ORDERFLOW-FORENSICS | lane_4_orderflow_proxy_sierra | ACCEPTED_CANDIDATE_DISCOVERY | Actual-R coverage 1 and synthetic winner side 1; leave-one-date flips depth sign. | research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_CACHED_FEATURE_FORENSICS_2026-05-03.md | not_strategy_comparable; diagnostic depth/thinness branch only |
| 410 | E-4 | lane_4_orderflow_proxy_sierra | BLOCKED_WITH_REASON | F11/OB-decay artifacts exist, but no retail-flow-share proxy, broker client-sentiment cache, Google Trends cache, or social-flow dataset is available locally. | research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md | not_applicable_missing_retail_flow_proxy |
| 420 | A-2 | lane_4_orderflow_proxy_sierra | BLOCKED_WITH_REASON | Local external-feed inventory has VIXCLS/GVZCLS but no VIX1D or VIX9D cache/source; the spread cannot be constructed without a confirmed legal/free source. | research/operations/LANE4_OPTIONS_GAMMA_PROXY_TRIAGE_2026-05-03.md | not_applicable_feature_feasibility |
| 420 | A-3 | lane_4_orderflow_proxy_sierra | BLOCKED_WITH_REASON | No local VRP, VIX futures, implied-variance term-structure, or registered realized-vol estimator source exists in data/external. | research/operations/LANE4_OPTIONS_GAMMA_PROXY_TRIAGE_2026-05-03.md | not_applicable_feature_feasibility |
| 420 | A-6 | lane_4_orderflow_proxy_sierra | BLOCKED_WITH_REASON | No local BoE policy, GBP political-risk, or registered legal proxy feed exists. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | blocked_missing_gbp_policy_sources |
| 420 | U-2 | lane_4_orderflow_proxy_sierra | BLOCKED_WITH_REASON | MT5 alone has no option dealer gamma sign, VIX1D/VIX9D, VRP, or official GEX source. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | blocked_missing_gamma_source |
| 420 | X-3 | lane_4_orderflow_proxy_sierra | BLOCKED_WITH_REASON | Imbalance-bar E24/E26 retest needs signed trades or aggressor-side proxy; current local data is OHLCV/quote-tick only. | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | blocked_missing_imbalance_bar_substrate |
| 440 | P1-F-PROXY-MAPPING-WEEKEND-FORENSICS | lane_4_orderflow_proxy_sierra | DEFERRED_WITH_TRIGGER | Needs approved/pre-registered USDJPY/6J price-transfer follow-up data; no broad paid pulls. | research/databento_orderflow_capture_2026-05-02/ORDERFLOW_PROXY_MAPPING_WEEKEND_FORENSICS_2026-05-03.md | not_alpha_claim_proxy_transfer_only |
| 505 | D11-REGENERATE-GBPJPY-US30CASH-OLD-LABELS | lane_5_data_ml_quality | DONE |  | research/ml_program/audit/D11_MISSING_OLD_LABELS_REGENERATION_2026-05-03.md | not_applicable_data_quality |
| 510 | M-2 | lane_1_methodology | REJECTED_FAILED |  |  | not_applicable |
| 510 | M-4 | lane_1_methodology | REJECTED_FAILED |  |  | not_applicable |
| 520 | D-12 | lane_5_data_ml_quality | BLOCKED_WITH_REASON | Current MT5 history probes show no full 2021 all-symbol M15 coverage; only XAGUSD has a small late-2021 slice. | research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md | not_applicable_data_availability |
| 520 | D-2 | lane_5_data_ml_quality | BLOCKED_WITH_REASON | Local MT5 tick probes and tick-capture cache do not provide pre-2024 tick history; broker retention only covers recent windows. | research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md | not_applicable_data_availability |
| 520 | D-4 | lane_5_data_ml_quality | BLOCKED_WITH_REASON | CFTC fetcher and XAUUSD gold cache exist, but no local FX COT contract mappings/rows are present. | research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md | not_applicable_data_source |
| 520 | D-5 | lane_5_data_ml_quality | BLOCKED_WITH_REASON | LBMA gold/silver fix calendar exists, but no local Krohn-Mueller-Whelan FX-fix source/cache is present. | research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md | not_applicable_data_source |
| 520 | D-7 | lane_5_data_ml_quality | BLOCKED_WITH_REASON | No local H-K-M/intermediary-capital SDF source, status file, normalized cache, or registered source spec was found. | research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md | not_applicable_data_source |
| 520 | D-8 | lane_5_data_ml_quality | BLOCKED_WITH_REASON | FRED macro cache exists, but no BIS source/cache/spec exists locally; full FRED/BIS item remains incomplete. | research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md | not_applicable_data_source_partial_fred_ready |
| 520 | D-9 | lane_5_data_ml_quality | BLOCKED_WITH_REASON | No distinct Federal Reserve research-feed source contract, parser, status file, or normalized cache exists beyond the FRED macro feed. | research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md | not_applicable_ambiguous_source |
| 530 | S-1 | lane_5_data_ml_quality | FILED_FOR_APPROVAL | Design ticket exists, but target assumptions are stale after K54 v4 failed and implementation would touch orchestrator/config live paths. | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | filed_design_only_no_promotion |
| 600 | D-11 | lane_0_control_tower | DONE |  | research/ml_program/audit/D11_2022_2023_BACKFILL_BIAS_CHECK_2026-05-03.md | not_applicable |
| 600 | D-6 | lane_0_control_tower | DONE |  | research/operations/weekend_backlog_ops_triage_2026-05-03.md | not_applicable |
| 600 | O-1 | lane_0_control_tower | DONE |  | research/operations/weekend_backlog_ops_triage_2026-05-03.md | not_applicable |
| 600 | O-2 | lane_0_control_tower | DONE |  | research/operations/weekend_backlog_ops_triage_2026-05-03.md | not_applicable |
| 600 | O-8 | lane_0_control_tower | DONE |  | research/operations/weekend_backlog_ops_triage_2026-05-03.md | not_applicable |
| 600 | U-11 | lane_0_control_tower | DONE |  | research/ml_program/audit/D11_2022_2023_BACKFILL_BIAS_CHECK_2026-05-03.md | not_applicable |
| 600 | M-10 | lane_1_methodology | DONE |  | research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.md | not_applicable |
| 600 | M-11 | lane_1_methodology | DONE |  | research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.md | not_applicable |
| 600 | M-12 | lane_1_methodology | DONE |  | research/ml_program/audit/METHODOLOGY_INFRASTRUCTURE_GATE_2026-05-03.md | not_applicable |
| 600 | M-13 | lane_1_methodology | DONE |  | research/ml_program/audit/METHODOLOGY_INFRASTRUCTURE_GATE_2026-05-03.md | not_applicable |
| 600 | M-14 | lane_1_methodology | DONE |  | research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.md | not_applicable |
| 600 | M-15 | lane_1_methodology | DONE |  | research/ml_program/audit/LANE1_REMAINING_METHODOLOGY_TRIAGE_2026-05-03.md | not_applicable |
| 600 | M-16 | lane_1_methodology | DONE |  | research/ml_program/audit/Q13_CPCV_BIAS_VARIANCE_BOOKKEEPING_2026-05-03.md | not_applicable |
| 600 | M-7 | lane_1_methodology | DONE |  | research/ml_program/audit/METHODOLOGY_INFRASTRUCTURE_GATE_2026-05-03.md | not_applicable |
| 600 | C-7 | lane_2_path_scaling | DONE |  | research/phase_3_external_feed_validation/LANE2_C7_C9_PATH_SCALING_TRIAGE_2026-05-03.md | not_applicable_ml_diagnostic |
| 600 | D-3 | lane_4_orderflow_proxy_sierra | DONE |  | research/operations/LANE4_OPTIONS_GAMMA_PROXY_TRIAGE_2026-05-03.md | not_strategy_comparable_feed_integration_only |
| 600 | K-14 | lane_4_orderflow_proxy_sierra | DONE |  | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | not_strategy_comparable_calibration_done |
| 600 | P-3 | lane_4_orderflow_proxy_sierra | DEFERRED_WITH_TRIGGER | K54 global candidates failed; conformal has only a CPCV proxy and no live/holdout system-flow candidate to calibrate. | research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md | not_strategy_comparable_calibration_deferred |
| 600 | D-1 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER | Tick capture exists for 7/7 symbols, but local history is only 5 days at best and MT5 retail volume/last fields are not a real volume/dollar substrate. | research/ml_program/audit/LANE5_DATA_SOURCE_TRIAGE_2026-05-03.md | not_applicable_data_substrate |
| 600 | D-10 | lane_5_data_ml_quality | DONE |  | research/ml_program/audit/LANE5_REMAINING_DATA_FEED_TRIAGE_2026-05-03.md | not_strategy_comparable_feed_integration_only |
| 600 | K-10 | lane_5_data_ml_quality | REJECTED_FAILED | K-10 appeared marginally in some top-100 screens but did not produce decision-grade lift. | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | rejected_below_noise |
| 600 | K-11 | lane_5_data_ml_quality | DONE |  | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | not_strategy_comparable_tooling_done |
| 600 | K-12 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER | Meta-labeling ran, but n=528 with about 250 primary-positive rows was statistically weak and showed no measurable lift. | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | deferred_sample_size |
| 600 | K-13 | lane_5_data_ml_quality | DONE |  | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | not_strategy_comparable_tooling_done |
| 600 | K-15 | lane_5_data_ml_quality | DONE |  | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | not_strategy_comparable_stability_gate_done |
| 600 | K-16 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER | No same-cohort K54 architecture iteration remains unblocked after K54 v3/v4 primary failure; focal loss would be another current-cohort loss-function variant. | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | deferred_same_cohort_k54_closed |
| 600 | K-17 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER | Pooled K54 v3/v4 training failed global gates, and data-poor instruments still need source-period flags and missing old labels resolved before new pooling claims are meaningful. | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | deferred_cohort_quality |
| 600 | K-18 | lane_5_data_ml_quality | REJECTED_FAILED | K54 v3 master failed DSR and stability gates; K54 v4 fallback architectures also failed. No same-cohort K54 architecture iteration remains unblocked. | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | NAS_US30 specialist remains K55-shadow discovery only; not promotion comparable to J46-J49. |
| 600 | K-5 | lane_5_data_ml_quality | REJECTED_FAILED | Raw W-unit pooling failed on the MT5 retail/CFD substrate; literal mechanism needs LOB/TAQ-style depth and trade volume. | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | rejected_substrate_failed |
| 600 | K-6 | lane_5_data_ml_quality | REJECTED_FAILED | Pooled K54 v3/v4 training ran and failed global decision gates; same-cohort iteration is closed. | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | rejected_global_k54_failed |
| 600 | K-7 | lane_5_data_ml_quality | REJECTED_FAILED | K-7..K-10 additions contributed only below-noise lift in the K54 v3 ablation. | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | rejected_below_noise |
| 600 | K-8 | lane_5_data_ml_quality | REJECTED_FAILED | K-7..K-10 additions contributed only below-noise lift in the K54 v3 ablation. | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | rejected_below_noise |
| 600 | K-9 | lane_5_data_ml_quality | REJECTED_FAILED | K-9 was below noise in the K54 v3 global model and the global K54 family failed per-cohort floors. | research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md | rejected_below_noise |
| 600 | P-1 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER | Portfolio-wide vol-conditioning failed H-PM01; live insertion between 3A and execution would change risk/trading behavior and needs CEO approval even for shadow. | research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md | NAS100-only subcandidate delta_R +0.0907 DSR-p 0.0152; portfolio-wide failed, not promotion comparable. |
| 600 | P-10 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER | Feature family has a literature prior, but same-cohort K54 feature iteration is closed after v3/v4 failure; old-label/source-period blockers still constrain new pooled training. | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | deferred_literature_feature_prior_not_empirical |
| 600 | P-2 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER | Meta-labeling ran in K54 v3 but was statistically weak at the current cohort size. | research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md | deferred_sample_size |
| 600 | P-5 | lane_5_data_ml_quality | REJECTED_FAILED | K-5 W-unit pooling failed and K-6 pooled K54 v3/v4 training failed global gates. | research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md | rejected_inherits_k5_k6_failure |
| 600 | P-6 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER | K54 v4 T7-NAS routing add was negative and all K54 v4 architectures failed; any inference routing layer is shadow-only until a specialist survives forward evidence. | research/ml_program/audit/LANE5_ARCHITECTURE_SYSTEM_FLOW_TRIAGE_2026-05-03.md | deferred_k55_shadow_specialist_only |
| 600 | P-7 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER | Heartbeat/drawdown thresholds are safety/risk behavior, current tick history is too short for Hawkes calibration, and live threshold changes require CEO approval. | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | not_strategy_comparable_safety_threshold_research |
| 600 | P-8 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER | The literature-prior is documented, but no local HDP-HMM/Kirby-null research harness has passed; replacing the regime classifier would touch live/shadow behavior. | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | deferred_literature_prior_no_empirical_gate |
| 600 | P-9 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER | This depends on D-1 tick-count-time substrate maturity and would alter Component 1/tick-daemon runtime behavior; current all-symbol tick history is below the 30-day trigger. | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | deferred_depends_on_d1_tick_substrate |
| 600 | S-2 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER | K54 v4 T7-NAS routing add was negative and P-6 is already deferred; routing needs forward K55 specialist evidence first. | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | deferred_inherits_p6_routing_failure |
| 600 | S-3 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER | No K55 shadow logger/output exists yet; 30-day evaluation requires implementation plus enough forward shadow events. | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | deferred_no_shadow_rows |
| 600 | S-4 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER | No paired live AI+ML shadow dataset exists; current K54 evidence is discovery/refinement only. | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | deferred_no_paired_shadow_dataset |
| 600 | S-5 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER | Production flip requires successful S-3/S-4 shadow evaluation, promotion dossier, and explicit CEO approval; no such evidence exists. | research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md | deferred_requires_future_promotion_dossier |
| 610 | B-6 | lane_1_methodology | DONE |  | research/ml_program/audit/METHODOLOGY_INFRASTRUCTURE_GATE_2026-05-03.md | not_applicable |
| 610 | M-1 | lane_1_methodology | DONE |  |  | not_applicable |
| 610 | M-17 | lane_1_methodology | DONE |  |  | not_applicable |
| 610 | M-3 | lane_1_methodology | DONE |  |  | not_applicable |
| 610 | M-8 | lane_1_methodology | DONE |  |  | not_applicable |
| 610 | M-9 | lane_1_methodology | DONE |  |  | not_applicable |
| 610 | P2-G-PHASE3-METHODOLOGY-DIAGNOSTICS | lane_1_methodology | DONE |  | research/phase_3_external_feed_validation/PHASE3_METHODOLOGY_DIAGNOSTICS_2026-05-03.md | not_applicable_methodology_guard |
| 610 | E-1 | lane_4_orderflow_proxy_sierra | REJECTED_FAILED | The K54 v3 Osler round-level stop-cluster proxy was implemented as K-7 and contributed only below-noise lift; production trade history records proposed GTOS levels, not counterparty stop clusters. | research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md | rejected_below_noise_proxy |
| 610 | A-8 | lane_6_asset_risk_edge | BLOCKED_WITH_REASON | Local feeds have XAUUSD nominal bars plus FRED real-rate/inflation-expectation proxies, but no CPI/PCE deflator or pre-registered real-gold-price percentile construction. | research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md | not_applicable_feature_feasibility |
| 610 | C-2 | lane_6_asset_risk_edge | BLOCKED_WITH_REASON | GTOS does not observe counterparty stop placements, broker client positioning, or IG/OANDA-style client sentiment locally; production trade records contain our proposed levels only. | research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md | not_applicable_unobserved_counterparty_data |
| 610 | E-2 | lane_6_asset_risk_edge | DEFERRED_WITH_TRIGGER | Current all-symbol MT5 tick coverage is short and quote-only; Toth-Bouchaud latent-liquidity shape needs mature tick/depth/order-flow evidence. | research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md | deferred_substrate_maturity |
| 610 | V-1 | lane_6_asset_risk_edge | DONE |  | research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md | not_strategy_comparable_feature_done; portfolio-wide H-PM01 failed |
| 610 | V-2 | lane_6_asset_risk_edge | BLOCKED_WITH_REASON | No local VRP, VIX futures, implied-variance term-structure, or registered realized-vol estimator source exists; VIXCLS/GVZCLS alone do not define VRP. | research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md | not_applicable_feature_feasibility |
| 610 | V-3 | lane_6_asset_risk_edge | DONE |  | research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md | not_strategy_comparable_feature_done |
| 615 | O8-LIFECYCLE-COMPLETENESS-VERIFIER | lane_3_execution_telemetry | DONE |  | research/operations/LANE3_EXECUTION_TELEMETRY_VERIFIERS_2026-05-03.md | not_applicable_label_truth_tooling |
| 616 | O1-INDEX-REBUILD-OR-STALE-VERIFIER | lane_3_execution_telemetry | DONE |  | research/operations/LANE3_EXECUTION_TELEMETRY_VERIFIERS_2026-05-03.md | not_applicable_label_truth_tooling |
| 620 | A-12 | lane_6_asset_risk_edge | BLOCKED_WITH_REASON | No Krohn-Mueller-Whelan FX-fix source/cache exists locally; D-5 remains blocked for FX-fix scope. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | blocked_missing_fx_fix_source |
| 620 | A-13 | lane_6_asset_risk_edge | BLOCKED_WITH_REASON | VIXCLS and Treasury yields exist, but TED/funding-liquidity/intermediary-capital source contract is incomplete. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | blocked_incomplete_funding_liquidity_sources |
| 620 | A-14 | lane_6_asset_risk_edge | BLOCKED_WITH_REASON | No BIS JPY carry-unwind table/cache/source spec exists locally. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | blocked_missing_bis_jpy_source |
| 620 | A-16 | lane_6_asset_risk_edge | FILED_FOR_APPROVAL | Replacing the live cross-instrument correlation gate would alter risk behavior and needs CEO approval; research-only prototype can be scoped separately. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | not_strategy_comparable_risk_model_approval |
| 620 | A-4 | lane_6_asset_risk_edge | BLOCKED_WITH_REASON | A-1 is forward-only and A-2/A-3 are blocked; same-cohort K54/K55 retraining is closed until cohort/source-quality triggers. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | blocked_specialist_retrain_inputs_absent |
| 620 | A-5 | lane_6_asset_risk_edge | BLOCKED_WITH_REASON | No local Japan/UK rate-differential, carry-unwind, or BIS/Aquilina source is cached for JPY-pair factor decomposition. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | blocked_missing_jpy_carry_sources |
| 620 | A-7 | lane_6_asset_risk_edge | BLOCKED_WITH_REASON | FRED has partial USD macro series but no Treasury-basis/intermediary-capital source or Fed-funds feature contract is registered. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | blocked_partial_macro_cache_only |
| 620 | B-4 | lane_6_asset_risk_edge | BLOCKED_WITH_REASON | Asset-specialist bundle depends on blocked/deferred A-1/A-2/A-3/A-4/A-5/A-6/A-7/A-8; A-9/A-11 are feed-feasibility only. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | blocked_bundle_constituents_unavailable |
| 620 | B-7 | lane_6_asset_risk_edge | BLOCKED_WITH_REASON | Edge-mechanism bundle has E-1 failed, E-2 deferred, E-4 blocked, and E-3 blocked. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | blocked_bundle_constituents_unavailable |
| 620 | C-3 | lane_6_asset_risk_edge | BLOCKED_WITH_REASON | Inverted-TP log has correction records but no symbol/outcome linkage, so Walasek lambda-context dependence cannot be measured from current data. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | blocked_missing_outcome_linkage |
| 620 | C-8 | lane_6_asset_risk_edge | BLOCKED_WITH_REASON | Feature-stability artifacts exist, but there is no K54 production deployment performance series because K54 is not deployed. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | blocked_no_production_ml_performance_series |
| 620 | E-3 | lane_6_asset_risk_edge | BLOCKED_WITH_REASON | Lillo-Mike-Farmer-Sato meta-order long-memory needs signed order-flow/meta-order aggregates; local OHLCV/H1 bars and MT5 tick volume are not a parent-order flow substrate. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | blocked_missing_signed_orderflow |
| 620 | X-1 | lane_6_asset_risk_edge | BLOCKED_WITH_REASON | Volume-bar E24/E26 retest needs real trade volume or approved tick/depth feed; MT5 retail tick volume is not a volume-bar substrate. | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | blocked_missing_real_volume_bars |
| 620 | X-2 | lane_6_asset_risk_edge | BLOCKED_WITH_REASON | Dollar-bar E24/E26 retest needs price x real traded volume; current MT5 feed lacks true centralized trade volume. | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | blocked_missing_dollar_bar_substrate |
| 630 | A-15 | lane_6_asset_risk_edge | BLOCKED_WITH_REASON | No He-Kelly-Manela/intermediary-capital source, status file, normalized cache, or source spec exists locally. | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | blocked_missing_hkm_source |
| 630 | B-5 | lane_6_asset_risk_edge | FILED_FOR_APPROVAL | AI-grounding bundle depends on L-1/L-2/L-8 and would alter Component 3A behavior if wired live; L-4 debate is owner-parked for now because it adds AI/API cost. | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | filed_ai_behavior_bundle_approval |
| 630 | X-7 | lane_6_asset_risk_edge | FILED_FOR_APPROVAL | Cascade-prompt rebuild would touch prompts/trading evaluation behavior; V4/cascade remains shelved/lost and requires explicit CEO approval before rebuild. | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | filed_prompt_behavior_approval |
| 705 | P1-B-PREFILL-DELIVERY-PATH-HARNESS | lane_2_path_scaling | DONE |  | research/phase_3_external_feed_validation/RAW_OHLC_PREFILL_DELIVERY_PATH_COVERAGE_2026-05-03.md | not_applicable_tooling_only |
| 720 | L-1 | lane_7_recurring_open_questions | FILED_FOR_APPROVAL | QuantMCP-style grounding would alter Component 3A behavior if wired live; approval and shadow-only design refresh are required. | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | filed_tool_use_grounding_approval |
| 720 | L-2 | lane_7_recurring_open_questions | FILED_FOR_APPROVAL | FinAgent-style market-state tool inventory would alter Component 3A behavior if wired live; approval and shadow-only design refresh are required. | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | filed_tool_inventory_approval |
| 720 | L-4 | lane_7_recurring_open_questions | DEFERRED_WITH_TRIGGER | Owner decision 2026-05-03: leave Component 3B debate dormant because it is down-road work and adds extra AI/API cost. | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | deferred_owner_parked_extra_api_cost |
| 720 | U-1 | lane_7_recurring_open_questions | BLOCKED_WITH_REASON | Same blocker as M-5: full 2022-2023 v2/v3 feature catalog plus source-flagged supplemental old-label integration. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | blocked_same_as_m5 |
| 720 | U-12 | lane_7_recurring_open_questions | BLOCKED_WITH_REASON | Same blocker as A-8: no local CPI/PCE-deflated real-gold-price percentile construction. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | blocked_missing_real_gold_feature |
| 720 | U-6 | lane_7_recurring_open_questions | BLOCKED_WITH_REASON | Broker substrate lacks true trade count/depth; current tick files are retail quote ticks, not centralized trade prints. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | blocked_missing_trade_count_substrate |
| 730 | L-3 | lane_7_recurring_open_questions | FILED_FOR_APPROVAL | Reflexion/post-trade feedback loop would alter AI/adaptation behavior and needs CEO approval plus shadow-only design. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | filed_ai_adaptation_approval |
| 730 | U-8 | lane_7_recurring_open_questions | BLOCKED_WITH_REASON | No He-Kelly-Manela/intermediary-capital source, cache, or source contract exists locally. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | blocked_missing_hkm_source |
| 810 | L-7 | lane_3_execution_telemetry | DONE |  |  | not_applicable |
| 810 | O-7 | lane_3_execution_telemetry | DONE |  |  | not_applicable |
| 810 | C-1 | lane_4_orderflow_proxy_sierra | REJECTED_FAILED |  |  | not_applicable |
| 810 | K-4 | lane_4_orderflow_proxy_sierra | REJECTED_FAILED |  |  | not_applicable |
| 810 | P-4 | lane_4_orderflow_proxy_sierra | REJECTED_FAILED |  |  | not_applicable |
| 820 | A-1 | lane_4_orderflow_proxy_sierra | DEFERRED_WITH_TRIGGER | Local FlashAlpha GEX proxy exists but only forward/current snapshots are cached; no legal historical gamma-sign series is available for NAS/US30 cross-period sign-flip validation. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | deferred_proxy_feature_not_strategy_comparable |
| 830 | U-14 | lane_4_orderflow_proxy_sierra | DEFERRED_WITH_TRIGGER | Needs longer live history or a clean publication/crowding proxy panel; current OB-decay monitor is sample-limited. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | deferred_decay_sample_limited |
| 890 | O-4 | lane_3_execution_telemetry | DONE |  |  | not_applicable |
| 920 | X-5 | lane_4_orderflow_proxy_sierra | DONE |  | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | not_strategy_comparable_rough_vol_diagnostic |
| 920 | K-1 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER |  |  | not_applicable |
| 920 | K-2 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER |  |  | not_applicable |
| 920 | K-3 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER |  |  | not_applicable |
| 920 | Q-1 | lane_5_data_ml_quality | REJECTED_FAILED |  |  | not_applicable |
| 930 | Q-2 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER |  |  | not_applicable |
| 930 | Q-3 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER |  |  | not_applicable |
| 930 | Q-4 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER |  |  | not_applicable |
| 930 | Q-5 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER |  |  | not_applicable |
| 930 | Q-6 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER |  |  | not_applicable |
| 930 | Q-7 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER |  |  | not_applicable |
| 930 | Q-8 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER |  |  | not_applicable |
| 930 | Q-9 | lane_5_data_ml_quality | DEFERRED_WITH_TRIGGER |  |  | not_applicable |
| 1020 | B-1 | lane_6_asset_risk_edge | REJECTED_FAILED |  |  | not_applicable |
| 1020 | B-2 | lane_6_asset_risk_edge | DEFERRED_WITH_TRIGGER | Portfolio-wide vol conditioning failed; NAS100-only subcandidate needs shadow/approval trigger before Component 3C work. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | deferred_component_3c_nas100_only_shadow |
| 1020 | B-3 | lane_6_asset_risk_edge | DEFERRED_WITH_TRIGGER | Risk-policy replacement must be simulated over DSR-surviving J46-J49/S79 baselines and needs live-risk approval. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | deferred_risk_replacement_not_validated |
| 1020 | C-5 | lane_6_asset_risk_edge | DEFERRED_WITH_TRIGGER | K54/K55 same-cohort training is closed after v3/v4 failures; reopen only with n>=5000 or source-quality/cohort-expansion trigger. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | deferred_loss_function_until_new_cohort |
| 1020 | C-6 | lane_6_asset_risk_edge | DEFERRED_WITH_TRIGGER | Continuous-sized entries require actual broker-R/fill truth, lifecycle telemetry, and live-risk approval before system-flow use. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | deferred_continuous_sizing_label_truth |
| 1020 | R-1 | lane_6_asset_risk_edge | DEFERRED_WITH_TRIGGER | Risk-constrained Kelly replacement needs a preregistered simulation over DSR-surviving J46-J49/S79 baselines and CEO approval before risk behavior changes. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | deferred_risk_policy_replacement |
| 1020 | R-2 | lane_6_asset_risk_edge | DEFERRED_WITH_TRIGGER | Lambda auto-calibration depends on R-1 and owner-approved risk replacement path. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | deferred_depends_on_r1 |
| 1020 | R-5 | lane_6_asset_risk_edge | DEFERRED_WITH_TRIGGER | Per-instrument weights require the R-1 simulation path and source-flagged all-symbol cohort; do not override S79 uniform profile from current evidence. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | deferred_weight_optimization_not_validated |
| 1020 | R-7 | lane_6_asset_risk_edge | REJECTED_FAILED |  | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | rejected_portfolio_wide_vol_scaled_sizing |
| 1020 | R-9 | lane_6_asset_risk_edge | DEFERRED_WITH_TRIGGER | Bundle depends on deferred R-1/R-2/R-5 and rejected R-7; only R-6 is done. | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | deferred_bundle_constituents_not_ready |
| 1020 | V-5 | lane_6_asset_risk_edge | REJECTED_FAILED |  | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | rejected_portfolio_wide_vol_managed_backtest |
| 1020 | V-6 | lane_6_asset_risk_edge | REJECTED_FAILED |  | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | rejected_uniform_vs_vol_managed_ab |
| 1020 | V-8 | lane_6_asset_risk_edge | REJECTED_FAILED |  | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | rejected_broad_vol_scaling_policy |
| 1020 | V-9 | lane_6_asset_risk_edge | DEFERRED_WITH_TRIGGER | Component 3C bundle depends on V-2 source completion and broad V-5/V-6 success; portfolio-wide vol sizing failed and live insertion requires approval. | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | deferred_component_3c_bundle_not_validated |
| 1030 | R-3 | lane_6_asset_risk_edge | DEFERRED_WITH_TRIGGER | Strub EVT-CDaR sizing needs preregistered simulation over DSR-surviving baselines and CEO approval before risk behavior changes. | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | deferred_risk_policy_replacement |
| 1030 | R-4 | lane_6_asset_risk_edge | DEFERRED_WITH_TRIGGER | Smooth Grossman-Zhou drawdown control needs simulation and owner approval; current H29 drawdown reducer remains the live safety path. | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | deferred_drawdown_policy_replacement |
| 1030 | X-4 | lane_6_asset_risk_edge | DEFERRED_WITH_TRIGGER | Tick-level Hawkes fitting needs mature tick/depth/order-flow history; current tick capture is short and quote-only. | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | deferred_tick_substrate_maturity |
| 1110 | B-8 | lane_6_asset_risk_edge | DONE |  |  | not_applicable |
| 1120 | A-11 | lane_6_asset_risk_edge | DONE |  | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | not_strategy_comparable_calendar_feature_only |
| 1120 | A-9 | lane_6_asset_risk_edge | DONE |  | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | not_strategy_comparable_feed_feasibility_only |
| 1120 | C-4 | lane_6_asset_risk_edge | DONE |  | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | risk_modifier_live_stack_not_new_signal |
| 1120 | E-5 | lane_6_asset_risk_edge | DONE |  | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | not_single_strategy_inventory_only |
| 1120 | R-6 | lane_6_asset_risk_edge | DONE |  | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | risk_modifier_already_live_not_new_signal |
| 1120 | R-8 | lane_6_asset_risk_edge | DONE |  | research/ml_program/audit/LANE6_PRIORITY620_TRIAGE_2026-05-03.md | not_strategy_comparable_static_risk_audit |
| 1120 | V-4 | lane_6_asset_risk_edge | DONE |  | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | not_strategy_comparable_sizing_function_done |
| 1120 | V-7 | lane_6_asset_risk_edge | DONE |  | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | risk_modifier_already_live_not_new_signal |
| 1120 | X-6 | lane_6_asset_risk_edge | DONE |  | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | not_applicable_baseline_reconciliation |
| 1120 | L-8 | lane_7_recurring_open_questions | DEFERRED_WITH_TRIGGER | LLM transfer test depends on L-1/L-2 shadow grounding implementation and approval path. | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | deferred_depends_on_grounding_shadow |
| 1120 | RR-1 | lane_7_recurring_open_questions | DEFERRED_WITH_TRIGGER | Quarterly last-6-months literature refresh across 22 domains requires a dedicated current-web literature sweep and source-citation pass outside this local evidence triage. | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | deferred_dedicated_literature_refresh |
| 1120 | RR-4 | lane_7_recurring_open_questions | DEFERRED_WITH_TRIGGER | Requires the same dedicated current-web literature sweep deferred under RR-1. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | deferred_current_literature_refresh |
| 1120 | RR-7 | lane_7_recurring_open_questions | DEFERRED_WITH_TRIGGER | Requires a current-web paper status/retraction watcher with source citations. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | deferred_current_paper_status_watcher |
| 1130 | A-10 | lane_6_asset_risk_edge | DONE |  | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | not_strategy_comparable_feed_feasibility_only |
| 1130 | A-17 | lane_6_asset_risk_edge | DONE |  | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | not_strategy_comparable_tail_diagnostic |
| 1130 | A-18 | lane_6_asset_risk_edge | DONE |  | research/ml_program/audit/LANE6_TAIL_TRIAGE_2026-05-03.md | not_strategy_comparable_correlation_diagnostic |
| 1130 | L-5 | lane_7_recurring_open_questions | DEFERRED_WITH_TRIGGER | Hybrid LLM+ML architecture depends on a surviving K55/K54 shadow candidate and approval for system-flow changes. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | deferred_architecture_path_no_surviving_candidate |
| 1130 | RR-5 | lane_7_recurring_open_questions | DEFERRED_WITH_TRIGGER | Capacity-decay band re-evaluation needs actual AUM/capacity growth or venue-volume participation data. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | deferred_capacity_trigger_absent |
| 1130 | RR-6 | lane_7_recurring_open_questions | DEFERRED_WITH_TRIGGER | Needs separately logged live edge return streams before an edge-correlation/diversification metric is meaningful. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | deferred_missing_edge_return_streams |
| 1130 | U-10 | lane_7_recurring_open_questions | DEFERRED_WITH_TRIGGER | Depends on L-1/L-2 tool-use grounding shadow implementation and approval path. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | deferred_depends_on_grounding_shadow |
| 1130 | U-13 | lane_7_recurring_open_questions | DEFERRED_WITH_TRIGGER | Needs AUM/capacity trigger plus venue-volume or slippage/capacity data by instrument. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | deferred_capacity_trigger_absent |
| 1130 | U-15 | lane_7_recurring_open_questions | DEFERRED_WITH_TRIGGER | Requires dedicated literature/book synthesis and translation into substrate-immune candidate specs. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | deferred_dedicated_literature_synthesis |
| 1130 | U-16 | lane_7_recurring_open_questions | DEFERRED_WITH_TRIGGER | Depends on P-8: standalone sticky-HDP-HMM plus Kirby fat-tailed-mixture null-test harness. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | deferred_depends_on_p8_harness |
| 1140 | Z-1 | lane_7_recurring_open_questions | DEFERRED_WITH_TRIGGER | No current GTOS classical-pipeline blocker requires quantum finance work; revisit only on explicit CEO request or after classical methods saturate. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | deferred_low_priority_quantum_track |
| 1140 | Z-2 | lane_7_recurring_open_questions | DEFERRED_WITH_TRIGGER | No current GTOS derivatives-evaluation bottleneck or quantum runtime path exists. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | deferred_low_priority_quantum_track |
| 1140 | Z-3 | lane_7_recurring_open_questions | DEFERRED_WITH_TRIGGER | No current GTOS RL/quantum runtime path exists, and live-learning changes would require separate approval. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | deferred_low_priority_quantum_track |
| 1140 | Z-4 | lane_7_recurring_open_questions | DEFERRED_WITH_TRIGGER | No current GTOS classical-pipeline blocker requires quantum finance work; revisit only on explicit CEO request or after classical methods saturate. | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | deferred_low_priority_quantum_track |
| 1220 | RR-2 | lane_7_recurring_open_questions | DONE |  | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | not_applicable_methodology_tracker |
| 1220 | RR-3 | lane_7_recurring_open_questions | DONE |  | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | not_applicable_decay_monitor_snapshot |
| 1220 | U-17 | lane_7_recurring_open_questions | DONE |  | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | not_applicable_path_diagnostic |
| 1220 | U-3 | lane_7_recurring_open_questions | DONE |  |  | not_applicable |
| 1220 | U-4 | lane_7_recurring_open_questions | DONE |  | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | NAS_US30 specialist discovery only; global K54 failed |
| 1220 | U-5 | lane_7_recurring_open_questions | DONE |  |  | not_applicable |
| 1220 | U-7 | lane_7_recurring_open_questions | DONE |  |  | not_applicable |
| 1220 | U-9 | lane_7_recurring_open_questions | DONE |  | research/ml_program/audit/LANE7_RECURRING_OPEN_QUESTIONS_TRIAGE_2026-05-03.md | not_strategy_comparable_control_scan |

## NO_PROMOTION_VERDICT

This queue state is a control artifact. It does not validate, promote, or modify any live trading behavior.
