# Live Shadow Follow-Up Coverage Audit - 2026-05-04

**Schema:** `live_shadow_followup_coverage_audit_v1`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Status Counts

| Status | Count |
|---|---:|
| `BLOCKED_WITH_EVIDENCE_AND_TRIGGER` | 1 |
| `CONFIG_PRESENT_WAITING_FOR_FORWARD_STRATEGY_ROWS` | 1 |
| `DOCUMENTED_SOURCE_BLOCKERS` | 2 |
| `EXPLICIT_OWNER_APPROVAL_BLOCKED` | 1 |
| `LIVE_HOOK_READY_WAITING_FOR_EXIT_TRIGGER_ROWS` | 1 |
| `LIVE_SNAPSHOT_PLUS_DISCOVERY_ONLY_BLOCKER` | 1 |
| `PARTIAL_EXIT_FLOW_PLUS_BLOCKER` | 1 |
| `PARTIAL_FORWARD_CONTEXT_PLUS_SOURCE_BLOCKERS` | 1 |
| `PRE_REGISTRATION_REQUIRED` | 1 |
| `ROWS_PRESENT` | 20 |
| `SOURCE_STATUS_BLOCKED_WITH_TRIGGER` | 1 |
| `SOURCE_STATUS_REQUIRED_WITH_FORWARD_SNAPSHOT` | 1 |
| `VERIFIER_REQUIRED_WITH_KNOWN_GAP` | 1 |
| `VERIFIER_REQUIRED_WITH_LOCAL_ROWS` | 1 |

## Coverage Matrix

| ID | Research item | Coverage status | Row sources | Required next state |
|---|---|---|---|---|
| LIVE-FOLLOW-001 | AI-independent mechanical/MSO evaluation anchor | `ROWS_PRESENT` | `shadow_logs/strategy_follow_evaluations.jsonl` (675 rows) | row per MSO/live evaluation after orchestrator reload |
| LIVE-FOLLOW-002 | AI CANDIDATE terminal strategy registry and external confluence | `ROWS_PRESENT` | `shadow_logs/strategy_follow_candidates.jsonl` (76 rows) | row per AI CANDIDATE terminal path |
| LIVE-FOLLOW-003 | Candidate path follow: close/touch/fill/pass-through/continue/return | `ROWS_PRESENT` | `shadow_logs/candidate_path_follow.jsonl` (1537 rows) | append path state for every strategy_follow_candidates row |
| LIVE-FOLLOW-003B | Opportunity-level duplicate protection for consecutive same setup detections | `ROWS_PRESENT` | `shadow_logs/live_candidate_opportunity_clusters.jsonl` (1768 rows) | raw rows preserved; count COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY only for trade-opportunity comparisons |
| LIVE-FOLLOW-004 | Pending-limit lifecycle truth | `ROWS_PRESENT` | `shadow_logs/pending_limit_lifecycle.jsonl` (144 rows) | state coverage across pending/fill/cancel/expiry events |
| LIVE-FOLLOW-005 | V2b OB-boundary/J46/fixed-R/FVG forward pairs | `ROWS_PRESENT` | `shadow_logs/v2b_forward_pairs.jsonl` (76 rows) | resolved post-cutoff pairs plus broker/synthetic lane separation |
| LIVE-FOLLOW-006 | V3/pre-fill delivery path and reversal-leg taxonomy | `ROWS_PRESENT` | `shadow_logs/prefill_delivery_path.jsonl` (76 rows) | arm/fill/cancel and path-order fields before V3 scoring |
| LIVE-FOLLOW-007 | FVG/OB confluence and disagreement ledger | `ROWS_PRESENT` | `shadow_logs/fvg_ob_confluence.jsonl` (76 rows) | forward-only confluence rows with no post-outcome leakage |
| LIVE-FOLLOW-008 | CL/ZN/VIX/VXM context/control ledger | `ROWS_PRESENT` | `shadow_logs/context_control_ledger.jsonl` (76 rows)<br>`shadow_logs/shadow_observer_hardening_status.jsonl` (38 rows) | context/control rows only; never direct strategy validation |
| LIVE-FOLLOW-009 | Databento targeted live confluence/orderflow | `ROWS_PRESENT` | `shadow_logs/databento_live_confluence.jsonl` (3 rows) | run only on registered strategy/orderflow triggers, not every candle |
| LIVE-FOLLOW-010 | Sierra local depth confluence | `ROWS_PRESENT` | `shadow_logs/strategy_follow_candidates.jsonl` (76 rows)<br>`shadow_logs/candidate_path_follow.jsonl` (1537 rows) | delayed/local Sierra snapshots attached where proxy mapping exists |
| LIVE-FOLLOW-011 | NAS100/NQ orderflow adverse-selection diagnostic | `ROWS_PRESENT` | `shadow_logs/databento_live_confluence.jsonl` (3 rows)<br>`shadow_logs/strategy_follow_candidates.jsonl` (76 rows) | track broker_actual_r>=20 and MBP10 candidate rows>=30 |
| LIVE-FOLLOW-012 | Broker actual-R, slippage, cost, and exit accounting | `PARTIAL_EXIT_FLOW_PLUS_BLOCKER` | `shadow_logs/slippage.jsonl` (3 rows)<br>`shadow_logs/j46_j49_shadow_outcomes.jsonl` (3 rows)<br>`shadow_logs/time_in_trade.jsonl` (0 rows) | canonical MT5 deal-history export for full broker actual-R joins |
| LIVE-FOLLOW-013 | J46-J49 exit policy comparator | `ROWS_PRESENT` | `shadow_logs/j46_j49_shadow_outcomes.jsonl` (3 rows) | accumulate fill rows; compare actual vs old-policy hypothetical |
| LIVE-FOLLOW-014 | S79/side-aware compounding context | `CONFIG_PRESENT_WAITING_FOR_FORWARD_STRATEGY_ROWS` | `shadow_logs/strategy_follow_candidates.jsonl` (76 rows)<br>`shadow_logs/daily_pnl_history.jsonl` (2 rows)<br>`pipeline_state/side_aware_sprt_state.json` (12 rows) | candidate/fill rows preserve S79/side-aware context without changing risk |
| LIVE-FOLLOW-015 | Regime classifier and monthly decay/OB continuation | `ROWS_PRESENT` | `shadow_logs/regime_classifications.jsonl` (1058 rows)<br>`shadow_logs/ob_continuation_daily.csv` (61 rows) | >=14d regime shadow plus realized-outcome comparison; monthly decay report cadence |
| LIVE-FOLLOW-016 | Decision-layer diagnostics: candidate features, D1 lag, direction, SL/touch gates | `ROWS_PRESENT` | `shadow_logs/candidate_features_log.jsonl` (743 rows)<br>`shadow_logs/d1_bias_lag.jsonl` (448 rows)<br>`shadow_logs/direction_emission_xau_audit.jsonl` (189 rows)<br>`shadow_logs/sl_beyond_ob_decisions.jsonl` (162 rows)<br>`shadow_logs/touch_count_gate_decisions.jsonl` (44 rows) | continue freshness checks and per-candidate joins |
| LIVE-FOLLOW-017 | Mechanical/dumb baseline, proximity, liquidity, displacement, structure divergence | `ROWS_PRESENT` | `shadow_logs/dumb_baseline_hypotheticals.jsonl` (15 rows)<br>`shadow_logs/proximity_shadow_log.jsonl` (255 rows)<br>`shadow_logs/liquidity_distance_log.jsonl` (34 rows)<br>`shadow_logs/displacement_events.jsonl` (98 rows)<br>`shadow_logs/structure_detector_divergences.jsonl` (1009 rows) | keep per-candle freshness and join to candidate/fill outcomes |
| LIVE-FOLLOW-018 | Exit-management shadows: BE, partial close Variant C, time in trade | `LIVE_HOOK_READY_WAITING_FOR_EXIT_TRIGGER_ROWS` | `shadow_logs/be_shadow_log.jsonl` (0 rows)<br>`shadow_logs/partial_close_shadow_log.jsonl` (0 rows)<br>`shadow_logs/time_in_trade.jsonl` (0 rows) | rows appear only when fills reach trigger/close states |
| LIVE-FOLLOW-019 | Session volatility and US30 sweep divergence | `ROWS_PRESENT` | `shadow_logs/session_volatility_log.csv` (10 rows)<br>`shadow_logs/sweep_divergence_log.csv` (7 rows) | verify watchdog cadence or run manually if stale |
| LIVE-FOLLOW-020 | K55 shadow / ML specialist paired AI+ML labels | `ROWS_PRESENT` | `shadow_logs/ml_shadow_predictions.jsonl` (989 rows) | collect paired AI/K55 feature rows; train or register a matching model artifact only after enough clean labels exist |
| LIVE-FOLLOW-021 | Component 3B debate / AI tool grounding / Reflexion behavior changes | `EXPLICIT_OWNER_APPROVAL_BLOCKED` | n/a | do not run or spend API unless owner reopens explicitly |
| LIVE-FOLLOW-022 | GBPJPY Sierra/orderflow proxy gap | `BLOCKED_WITH_EVIDENCE_AND_TRIGGER` | n/a | separate 6B/6J cross proxy design before using Sierra/Databento confluence |
| LIVE-FOLLOW-023 | Account/PnL truth and R-vs-dollar evidence separation | `VERIFIER_REQUIRED_WITH_LOCAL_ROWS` | `shadow_logs/daily_pnl.json` (20 rows)<br>`shadow_logs/daily_pnl_history.jsonl` (2 rows)<br>`shadow_logs/equity_read_anomalies.jsonl` (18 rows) | build/read read-only MT5 account-history reconciliation: ACCOUNT_HISTORY_REALIZED vs LIVE_R_ARTIFACT vs RESEARCH_MEASURED |
| LIVE-FOLLOW-024 | O1 trade-index staleness and O8 lifecycle completeness verifiers | `VERIFIER_REQUIRED_WITH_KNOWN_GAP` | `knowledge_base/trade_records/_trade_index.json` (0 rows)<br>`shadow_logs/pending_limit_lifecycle.jsonl` (144 rows) | rebuild/migrate stale trade index and verify each LIMIT_PLACED has execution or pending_lifecycle state |
| LIVE-FOLLOW-025 | V2 structural oracle/as-of selector remains shadow/discovery only | `LIVE_SNAPSHOT_PLUS_DISCOVERY_ONLY_BLOCKER` | `shadow_logs/strategy_follow_evaluations.jsonl` (675 rows)<br>`shadow_logs/v2b_forward_pairs.jsonl` (76 rows) | do not wire a structural selector until resolved unseen V2b rows, lifecycle, cost, and preregistered gates exist |
| LIVE-FOLLOW-026 | XAUUSD same-market structural path extension and frozen-slice guard | `SOURCE_STATUS_REQUIRED_WITH_FORWARD_SNAPSHOT` | `shadow_logs/strategy_follow_evaluations.jsonl` (675 rows)<br>`shadow_logs/strategy_follow_candidates.jsonl` (76 rows)<br>`shadow_logs/xauusd_same_market_extension_status.jsonl` (36 rows) | register same-market source-transfer slice before opening outcomes; keep live rows separate from replay evidence |
| LIVE-FOLLOW-027 | ES/MES strategy-cohort pre-registration | `PRE_REGISTRATION_REQUIRED` | `shadow_logs/es_mes_preregistration_status.jsonl` (2 rows) | keep outcomes closed until a separate event-id/source-hash/scoring dossier is frozen |
| LIVE-FOLLOW-028 | 6B sampling alignment and SI source/depth-definition blockers | `SOURCE_STATUS_BLOCKED_WITH_TRIGGER` | `shadow_logs/strategy_follow_candidates.jsonl` (76 rows)<br>`shadow_logs/candidate_path_follow.jsonl` (1537 rows) | use common-second policy for 6B and keep SI blocked until source/depth definition resolves |
| LIVE-FOLLOW-029 | External feed blockers: pre-2024 tick, pre-2022 OHLCV, FX COT, KMW fix, H-K-M, BIS, Fed research feed | `DOCUMENTED_SOURCE_BLOCKERS` | n/a | reopen only after source/access path, cache schema, publication-time/no-lookahead convention, and budget approval exist |
| LIVE-FOLLOW-030 | Options/gamma and volatility-risk-premium blockers plus FlashAlpha Basic GEX forward context | `PARTIAL_FORWARD_CONTEXT_PLUS_SOURCE_BLOCKERS` | n/a | accumulate legal forward rows or register legal historical GEX/VRP/VIX1D/VIX9D sources before validation |
| LIVE-FOLLOW-031 | X-1/X-2/X-3 imbalance/meta-order-flow primitives | `DOCUMENTED_SOURCE_BLOCKERS` | `shadow_logs/databento_live_confluence.jsonl` (3 rows)<br>`shadow_logs/strategy_follow_candidates.jsonl` (76 rows) | define primitive-specific extractor, label plan, cost cap, and candidate trigger before broader collection |
| LIVE-FOLLOW-032 | Live monitoring goal/runbook persistence for all shadow rows | `ROWS_PRESENT` | `.context/05_operations/FORWARD_CAPTURE_MONITORING_RUNBOOK_2026-05-04.md` (121 rows)<br>`scripts/_live_monitor_iter.py` (451 rows) | after orchestrator restart, monitor row freshness and path outcomes during each active session |
| LIVE-FOLLOW-033 | Separate no-AI MSO shadow observer for tested non-orchestrator instruments | `ROWS_PRESENT` | `shadow_logs/shadow_observer_status.jsonl` (1003 rows)<br>`shadow_logs/strategy_follow_evaluations.jsonl` (675 rows)<br>`shadow_logs/shadow_observer_hardening_status.jsonl` (38 rows) | run active EURUSD/GER40/UK100 MSO-only observers; keep ES/MES prereg-blocked and CL/ZN/VIX control-only; audit stale detection and final closeout |

## Hard Boundaries

- This audit does not promote any strategy, risk setting, prompt, or execution behavior.
- Databento Live is event-triggered and explicitly enabled only; no blind every-candle subscription is allowed.
- Sierra depth is local/delayed confluence and is embedded only where a registered proxy mapping exists.
- GBPJPY has no registered direct Sierra/Databento proxy in this audit; strategy rows must show that blocker instead of guessing.
- K55/ML shadow target refresh and read-only feature/status rows are implemented; prediction remains disabled until a matching registered model artifact exists. Component 3B/debate/tool-grounding remains approval-blocked.
