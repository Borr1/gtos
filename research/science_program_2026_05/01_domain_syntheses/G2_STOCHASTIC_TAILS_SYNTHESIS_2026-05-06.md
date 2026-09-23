# G2 Stochastic Processes, Time Series, Tails Synthesis - 2026-05-06

**Lane:** `G2`  
**Role:** `science_lane`  
**Domain:** `stochastic processes, time series, tails`  
**Status:** `G2_RESEARCH_SYNTHESIS_COMPLETE_WITH_BLOCKERS`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Scope Boundary

This lane extracts primitive mechanisms from SDEs, Markov/HMM state models, GARCH/EVT, rough volatility, drawdown/tail risk, hazard models, and survival timing. It writes research rows only. It does not change live trading prompts, risk, execution, permissions, selectors, safety gates, MT5, canaries, paid data, or order behavior.

Companion machine-readable rows are in `research/science_program_2026_05/01_domain_syntheses/G2_STOCHASTIC_TAILS_SYNTHESIS_2026-05-06.json`.

## Mandatory Preflight Evidence

| Requirement | Evidence |
| --- | --- |
| Run live-state generator | `python scripts/generate_live_state.py` wrote `.context/LIVE_STATE.md` in `C:\tmp\gtosg\G2`. |
| Read live state | `.context/LIVE_STATE.md` reports generated UTC `2026-05-06 06:44:48`, branch HEAD `e55a0993`, latest handoff `.context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md`, clean tree before runtime refresh, and research context `FRESH`. |
| Read latest numbered handoff | `.context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md` read. |
| Read quick reference | `.context/00_core/quick_reference_card.md` read for kill zones, SPRT/CUSUM, drawdown, and risk boundaries. |
| Read doctrine | `.context/00_core/research_operating_doctrine.md` read; it requires aggressive research and strict promotion separation. |
| Read current state | `.context/00_core/research_current_state.md:70-78` confirms the primitive-science program is research/tooling only, uses `science_mechanism_v1`, `science_hypothesis_v1`, `experiment_prereg_v1`, `source_contract_v2`, and `goal_status_v1`, and keeps `$0` new external cash spend. |
| Read reading order and relevant Tier 2-4 artifacts | `.context/00_READING_ORDER.md`, `CLAUDE.md`, `.context/00_core/architecture.md`, `.context/00_core/master_roadmap.md`, `.context/01_knowledge_base/kb_edge_mechanisms_and_risks.md`, `.context/01_knowledge_base/kb_validation_and_monitoring_framework.md`, `.context/01_knowledge_base/kb_gold_market_deep_knowledge.md`, and `.context/03_analysis/research_execution_plan_113q.md` were inspected for G2-relevant mechanisms and stale routes. |
| Read G0 governor artifacts | `PROGRAM_GOVERNOR_2026-05-06.md`, `SCHEMA_CONTRACTS_2026-05-06.md`, `WORKTREE_MAP_2026-05-06.md`, `SOURCE_BUDGET_LEDGER_2026-05-06.md`, `G0_CROSS_AGENT_SYNTHESIS_2026-05-06.md`, `G0_COMPLETION_AUDIT_2026-05-06.md`, and `GOAL_STATUS_REGISTRY_2026-05-06.json` read. |
| Worktree boundary | Work performed in `C:\tmp\gtosg\G2` on `science-goals/g2-stochastic-tails`. Runtime `.context/LIVE_STATE.md` dirt is not staged. |

## Search Plan Before Outcome Review

Before inspecting G2-specific source hits, the useful mechanisms worth finding were:

1. Momentum persistence and decay: H1 return autocorrelation should lead OB continuation decay if GTOS is mostly exploiting pullback-in-trend persistence rather than an independent zone effect.
2. Conditional variance and vol-of-vol: GARCH-like state should explain fill ambiguity, stop distance fragility, same-bar TP/SL ambiguity, or lifecycle quality, but local evidence should decide whether it is a direct OB-continuation driver.
3. Hidden state persistence: Markov/HMM dwell time, transition hazard, and regime instability may be more useful than static regime labels.
4. Rough volatility/path roughness: roughness should identify instruments or sessions where M15 bars are too coarse and lower-TF ordering is mandatory.
5. Tail dependence and first-passage risk: lower-tail co-movement should inform portfolio research and drawdown-simulation inputs, not bypass existing risk gates.
6. Hazard/survival timing: time from candidate decision to entry touch, skipped fill, TP-area pass-through, SL touch, or unresolved path should become a preregistered lifecycle model.
7. Jump/self-exciting event arrivals: stop-cascade bursts can be modeled as jump/Hawkes events, but the source substrate must be signed trades, depth, or mature tick logs, not inferred candle direction.

Evidence that would distinguish signal from noise:

- as-of features available at or before candidate decision time;
- sample floors, duplicate-aware counts, and label separation by `broker_actual_r`, `synthetic_path_r`, `lifecycle_no_fill`, `observation_only`, and `context_only`;
- counter-evidence from killed/deferred GTOS routes;
- recent/forward rows instead of same-dataset discovery when validation is claimed;
- source contracts that keep blocked or paid sources `validation_safe=false`.

## Domain Synthesis

G2 should not add a new live filter or risk rule. Its highest-value contribution is to translate time-series state into point-in-time shadow fields and preregistered lifecycle tests.

The first synthesis result is negative but useful: pure volatility clustering as the direct explanation for OB continuation is already a killed route. `kb_edge_mechanisms_and_risks.md:85-89` records the GARCH/volatility-clustering argument and a refutation from regime tests with p-values above 0.05. The G2 move is therefore not "use high volatility to approve/reject OBs." It is to ask narrower questions: does realized volatility or vol-of-vol predict unresolved paths, same-M1 ambiguity, entry non-touch, cost dominance, or path roughness?

Momentum persistence remains live as a decay diagnostic, not as a promotion claim. `kb_edge_mechanisms_and_risks.md:117-123` warns that wrong mechanism attribution leads to wrong decay monitoring and names H1 autocorrelation as the right signal if the edge is momentum-like. `kb_validation_and_monitoring_framework.md:223` and `:324` also identify H1 autocorrelation as an early warning monitor. This becomes a G2 preregistered observation lane: test whether rolling H1 autocorrelation predicts future OB-continuation decay or candidate path quality before OB statistics degrade.

Markov/HMM state models should stay shadow-only. Current local state already joins regime and decay context into candidate and filled rows: `LTO018_REGIME_DECAY_OUTCOME_JOIN_2026-05-05.md:10-18` reports 79 computed rows and only 3 account-history actual-R claim rows; `:26` records regime mix; `:47` states the K55 contribution is as-of feature/provenance/sample-eligibility metadata. `research_current_state.md:1150` says sticky-HDP-HMM is deferred and must not replace the current regime classifier from literature prior alone. G2 should therefore preregister dwell/transition features as context or lifecycle predictors, not a regime-classifier replacement.

Rough-volatility evidence is diagnostic. Lane 6 tail triage found a rough-Hurst proxy for 7 symbols with median H `0.5050851741228051` and range `0.48422314477656087` to `0.6033981383377698` (`LANE6_TAIL_TRIAGE_2026-05-03.md:17` and `:56`). This suggests most instruments are near Brownian roughness at the tested scale, with US30/NAS100 somewhat more persistent/roughness-different. The preregistered G2 use is not directional prediction; it is to identify where M15 ordering is too coarse and lower-TF path evidence should be mandatory.

Tail dependence is already a source-aware research branch, but not a live risk change. Lane 6 tail triage reports a copula/tail-dependence diagnostic on 13,064 aligned M15 returns and 21 pairs (`LANE6_TAIL_TRIAGE_2026-05-03.md:60`) and Forbes-Rigobon adjusted high-vol correlations (`:61`). The strongest local pairs are XAUUSD-XAGUSD and US30-NAS100 in the same artifact's tail table. This should feed a context-only first-passage/drawdown simulation lane, not override the existing cross-instrument risk gate.

Broad volatility-managed sizing is killed portfolio-wide. `LANE6_TAIL_TRIAGE_2026-05-03.md:48-51` records rejected Barroso-Santa-Clara / Moreira-Muir broad vol-scaling attempts with negative portfolio delta and DSR-p near 1. EVT/CDaR and smooth drawdown control remain deferred risk-policy research: `:63-64` require preregistered simulation and owner approval and explicitly preserve current H29 drawdown behavior. G2 can specify the simulation, but not touch `config`, `src/components/drawdown_manager.py`, or risk settings.

Survival timing is the most immediately useful G2 primitive because GTOS now has candidate lifecycle rows. `LTO006_V2B_FORWARD_PAIR_RESOLUTION_AUDIT_2026-05-05.md` records 76 V2b pair rows, 70 synthetic path-R rows, 0 broker actual-R rows, 8 duplicate-aware countable R pairs, and explicit path outcome states. `LTO007_PREFILL_DELIVERY_PATH_AUDIT_2026-05-05.md` records 76 pre-fill rows, 12 duplicate-aware countable path rows, no-leak status, derived fill/no-fill counts, and source gaps for exact pre-fill candle sequence and tick summaries. These are exactly the objects a hazard model should ingest: time-to-entry, time-to-TP-area-without-fill, time-to-entry-then-SL, and unresolved/censored paths.

Jump/Hawkes modeling remains source-blocked. `LANE6_TAIL_TRIAGE_2026-05-03.md:65` says tick-level Hawkes fitting needs mature tick/depth/order-flow history and current tick capture is short and quote-only, with trigger `>=30` trading days all-symbol ticks or approved signed order-flow/depth feed. That blocks any self-exciting arrival model from validation. It can remain a future source contract and prereg, not a live idea.

## Mechanism Rows

All rows use `science_mechanism_v1` and carry `NO_PROMOTION_VERDICT`.

| mechanism_id | mechanism | expected GTOS signature | repo cross-check |
| --- | --- | --- | --- |
| `SCI-G2-AR-DECAY-001` | H1 autocorrelation decay / AR persistence loss | Rolling H1 return autocorrelation falls before OB-continuation or candidate path quality degrades. | Active monitoring idea in `kb_edge_mechanisms_and_risks.md:117-123`, `:146`, and `kb_validation_and_monitoring_framework.md:223`, `:324`; not a live filter. |
| `SCI-G2-GARCH-LIFECYCLE-002` | Conditional variance affects lifecycle ambiguity, not direct OB continuation | Realized-vol percentile or vol-of-vol predicts no-fill, same-M1 ambiguity, or stop-distance fragility after controlling for symbol/session/side. | Direct volatility-clustering OB explanation refuted in `kb_edge_mechanisms_and_risks.md:85-89`; session-vol/sweep status exists as monitor-only in `LTO022_SESSION_VOLATILITY_SWEEP_STATUS_2026-05-05.md`. |
| `SCI-G2-HMM-DWELL-003` | Hidden state dwell/transition hazard | Regime dwell age, transition probability, or recent state flip predicts candidate lifecycle failure or shadow-path ambiguity. | Regime-decay join is K55-ready context only (`LTO018...md:47`); sticky-HDP-HMM deferred, not replacement (`research_current_state.md:1150`). |
| `SCI-G2-ROUGH-PATH-004` | Rough/path-roughness sampling risk | Higher roughness or unstable local variation predicts lower-TF path-order necessity and same-bar ambiguity. | Rough-Hurst proxy already diagnostic only (`LANE6_TAIL_TRIAGE_2026-05-03.md:17`, `:56`). |
| `SCI-G2-EVT-TAILDEP-005` | Tail dependence / first-passage drawdown risk | Lower-tail co-movement clusters among symbols raise simultaneous adverse path probability. | Tail-correlation diagnostic done, no live risk rule (`LANE6_TAIL_TRIAGE_2026-05-03.md:60-61`); existing risk gate untouched. |
| `SCI-G2-SURVIVAL-PATH-006` | Candidate lifecycle survival and censoring | Time-to-entry, skipped fill, TP-area pass-through, entry-then-SL/TP, and unresolved paths follow measurable hazard curves. | V2b/pre-fill audits have candidate path state but broker actual-R and exact source fields remain limited (`LTO006...md`, `LTO007...md`). |
| `SCI-G2-JUMP-HAWKES-007` | Jump/self-exciting stop-cascade arrival process | Signed-trade/depth/tick bursts before or after liquidity sweeps predict cascade exhaustion or continuation timing. | Hawkes route deferred until mature tick/depth/order-flow source exists (`LANE6_TAIL_TRIAGE_2026-05-03.md:65`). |

## Hypothesis Rows

All rows use `science_hypothesis_v1`, are preregistration targets, and are not validation claims.

| hypothesis_id | mechanism_id | label_class | null | alternative | sample floor |
| --- | --- | --- | --- | --- | --- |
| `H-G2-AR-DECAY-001` | `SCI-G2-AR-DECAY-001` | `observation_only` | Rolling H1 autocorrelation decile has no association with next-window OB continuation or candidate path-quality rate after symbol/session controls. | Lower autocorrelation deciles precede lower OB continuation or poorer candidate path-quality rate. | `>=12` weekly windows and `>=100` candidate/context rows, or report underpowered. |
| `H-G2-GARCH-LIFECYCLE-002` | `SCI-G2-GARCH-LIFECYCLE-002` | `lifecycle_no_fill` | Realized-vol percentile and vol-of-vol do not change no-fill, TP-area-without-fill, or same-M1 ambiguity odds after symbol/session controls. | Extreme vol or vol-of-vol increases lifecycle ambiguity and skipped-fill rates. | `>=150` lifecycle rows and `>=30` ambiguous/no-fill rows. |
| `H-G2-HMM-DWELL-003` | `SCI-G2-HMM-DWELL-003` | `context_only` | Regime dwell age, recent flip, and transition score do not stratify lifecycle quality beyond static regime label. | Recent flips or short dwell ages increase unresolved/adverse path states. | `>=150` regime-joined candidate rows and `>=4` state buckets with `>=20` rows each. |
| `H-G2-ROUGH-PATH-004` | `SCI-G2-ROUGH-PATH-004` | `observation_only` | Roughness/Hurst proxy does not predict same-bar ambiguity or need for lower-TF ordering. | Higher roughness or roughness instability identifies symbols/sessions where M15 labels are less reliable. | `>=7` symbols and `>=200` candidate-path rows with lower-TF availability flags. |
| `H-G2-EVT-TAILDEP-005` | `SCI-G2-EVT-TAILDEP-005` | `observation_only` | Lower-tail dependence proxy does not improve adverse co-movement/drawdown simulation calibration versus Pearson correlation alone. | Tail-dependence proxy improves simultaneous adverse path risk calibration for XAUUSD-XAGUSD and US30-NAS100 cohorts. | `>=250` aligned return windows per pair and `>=30` adverse-tail events per pair, or simulation-only. |
| `H-G2-SURVIVAL-PATH-006` | `SCI-G2-SURVIVAL-PATH-006` | `lifecycle_no_fill` | Candidate time-to-entry and censoring covariates do not distinguish no-fill-to-TP-area from entry-touch outcomes. | Survival model separates no-fill-through-TP, entry-then-TP1, entry-then-SL, ambiguous, and unresolved states with predecision covariates. | `>=200` candidate lifecycle rows, duplicate-aware, with exact decision time and path status. |
| `H-G2-JUMP-HAWKES-007` | `SCI-G2-JUMP-HAWKES-007` | `context_only` | Self-exciting quote/depth burst intensity has no relation to cascade continuation/exhaustion timing. | Burst intensity around liquidity sweeps predicts cascade timing only when signed trade/depth/tick substrate is mature. | Blocked until `>=30` all-symbol trading days or approved signed order-flow/depth source. |

## Experiment Prereg Specs

All preregs use `experiment_prereg_v1`, freeze before outcome review, and keep `outcome_review_opened=false`.

| experiment_id | hypothesis_id | metric | cohort | DSR/PBO/effective-N policy |
| --- | --- | --- | --- | --- |
| `EXP-G2-AR-DECAY-001` | `H-G2-AR-DECAY-001` | Spearman/partial rank association between H1 autocorrelation decile and next-window OB/candidate quality | Portfolio plus XAUUSD, XAGUSD, NAS100, US30, USDJPY, GBPJPY, GBPUSD when rows exist | No promotion p-values; DSR/PBO `not_computable` unless preregistered forward windows and fold design exist. |
| `EXP-G2-GARCH-LIFECYCLE-002` | `H-G2-GARCH-LIFECYCLE-002` | Logistic/ordinal model for no-fill, TP-area-without-fill, same-M1 ambiguity | Candidate lifecycle rows from forward shadow logs only | Discovery p-values allowed only as screen; promotion p-values forbidden until unseen sample floors and label separation pass. |
| `EXP-G2-HMM-DWELL-003` | `H-G2-HMM-DWELL-003` | Incremental lift in lifecycle stratification from dwell/transition features over static regime | Regime-decay outcome join plus candidate path rows | Effective-N by state bucket; PBO only if fold matrix has enough state-bucket diversity. |
| `EXP-G2-ROUGH-PATH-004` | `H-G2-ROUGH-PATH-004` | Same-bar ambiguity rate and lower-TF ordering availability by roughness bucket | Symbols with rough-Hurst proxy and candidate-path rows | Descriptive until lower-TF availability is complete; no validation from proxy alone. |
| `EXP-G2-EVT-TAILDEP-005` | `H-G2-EVT-TAILDEP-005` | Tail-calibrated simultaneous adverse move rate vs Pearson-only baseline | XAUUSD-XAGUSD and US30-NAS100 first, other pairs later | Simulation calibration only; no live risk change without separate owner-approved risk dossier. |
| `EXP-G2-SURVIVAL-PATH-006` | `H-G2-SURVIVAL-PATH-006` | Cause-specific hazard / survival curves for entry touch, no-fill-to-TP, entry-then-SL/TP, unresolved | Duplicate-aware candidate lifecycle rows | Censor unresolved paths; broker actual-R never mixed with synthetic path-R or lifecycle labels. |
| `EXP-G2-JUMP-HAWKES-007` | `H-G2-JUMP-HAWKES-007` | Event intensity stability and cascade-timing association | Future mature tick/depth/order-flow windows only | Blocked; no statistic until source contract and sample floor are present. |

## Source Contracts And Budget Blockers

All `source_contract_v2` rows in the JSON companion keep `validation_safe=false`.

| source_id | status | allowed role | blockers |
| --- | --- | --- | --- |
| `SRC-G2-LOCAL-OHLC-RETURNS` | local existing data allowed | research/shadow feature construction | Same-dataset discovery cannot validate; stale/source-period flags required. |
| `SRC-G2-FORWARD-SHADOW-LIFECYCLE` | local shadow logs allowed | lifecycle and observation labels | Broker actual-R sparse, duplicate-aware sample floor not met, exact source fields missing for some strategies. |
| `SRC-G2-REGIME-DECAY-JOIN` | local derived context allowed | context-only/K55 substrate | Only 3 account-history actual-R claim rows in current audit; static-regime replacement forbidden. |
| `SRC-G2-SIERRA-DATABENTO-DEPTH` | existing Sierra/access and Databento credits only under cost ledger | context-only/source research | Paid/live Databento and source parity blockers remain; no broad pulls. |
| `SRC-G2-OPTIONS-GAMMA-VRP` | partial/blocked | context-only | FlashAlpha Basic is forward context only; historical GEX, VIX1D/VIX9D, and VRP construction remain blocked (`LTO032...md:14-17`). |
| `SRC-G2-TICK-DEPTH-HAWKES` | blocked/deferred | blocked until mature source | Tick/Hawkes source floor not met; signed trade/depth source needed. |

Budget remains `$0` new external cash spend. `SOURCE_BUDGET_LEDGER_2026-05-06.md` says spend allowed is false and no lane may spend cash or mark a source validation-safe without numeric cap, per-source limit, source contract, and owner approval.

## Killed Routes And Counter-Evidence

| route | disposition | evidence |
| --- | --- | --- |
| Pure volatility clustering as OB-continuation explanation | Killed for direct entry/filter use | `kb_edge_mechanisms_and_risks.md:85-89` says the regime/volatility tests returned p-values above 0.05. |
| Broad portfolio vol-managed sizing | Rejected failed | `LANE6_TAIL_TRIAGE_2026-05-03.md:48-51` records failed broad vol-managed backtests. |
| Sticky-HDP-HMM replacing current regime classifier | Deferred/blocked | `research_current_state.md:1150` says do not replace current regime classifier from literature prior alone. |
| EVT-CDaR or smooth drawdown replacing H29 | Deferred and approval-blocked | `LANE6_TAIL_TRIAGE_2026-05-03.md:63-64` requires prereg simulation and owner approval. |
| Hawkes/self-exciting event model on current quote-only tick cache | Deferred/source-blocked | `LANE6_TAIL_TRIAGE_2026-05-03.md:65` requires mature tick/depth/order-flow history. |
| V3 same-dataset replay as validation | Forbidden | `PHASE3_METHODOLOGY_DIAGNOSTICS_2026-05-03.md:19-23` forbids promotion p-values for current same-dataset discovery claims; `RAW_OHLC_PATH_SCALING_V3_FULL_EXPLORATORY_REPLAY_2026-05-03.md:64` says DSR is not computable for V3 same-dataset discovery. |
| COT as direct gold signal | Killed | `kb_gold_market_deep_knowledge.md:67-69` says COT has zero predictive value for gold and should not be implemented as filter/input/context signal. |

## Ambiguity Ledger

| ambiguity | pursued answer | status | next evidence |
| --- | --- | --- | --- |
| Is GARCH/volatility a direct OB edge driver? | Existing regime tests say no. | Answered/killed for direct filter. | Only lifecycle/ambiguity use remains open. |
| Is GTOS actually momentum with OB vocabulary? | H1 autocorrelation is the cleanest decay discriminator; generic momentum baseline still unresolved. | Sharper hypothesis. | Forward H1 autocorrelation plus candidate path quality and dumb-baseline comparison. |
| Can HMM improve regime handling? | Static replacement is deferred; dwell/transition features can be context-only. | Blocked from replacement, open as shadow feature. | Regime-joined candidate rows with dwell/transition feature snapshots. |
| Does roughness matter? | Current H proxy near 0.5 median, with instrument variation. | Diagnostic only. | Lower-TF ambiguity and path-order availability joined by symbol/session. |
| Does tail dependence require risk action? | Current evidence is feature feasibility only. | No live risk action. | Tail-calibrated simulation over DSR-surviving baselines and owner-approved risk dossier. |
| Can survival timing improve fills/paths? | Current lifecycle logs have enough shape to preregister, but broker actual-R and exact metadata are sparse. | Open preregistered shadow lane. | More forward candidate lifecycle rows, exact pre-fill sequence, and censoring policy. |
| Is Hawkes modeling ready? | No; source maturity missing. | Source-blocked. | >=30 all-symbol tick days or signed trade/depth source contract. |
| Are neighbor lanes ready for cross-domain merges? | G1/G3/G10 have no committed domain synthesis rows as of this pass. G1 has untracked raw source cache only. | No cross-domain rows added. | Re-run neighbor pass after committed G1/G3/G10 rows exist. |

## Lane Context Ledger

| artifact/source read | claim/mechanism changed | next question/source check |
| --- | --- | --- |
| `.context/LIVE_STATE.md` | Confirmed current branch, clean baseline, fresh research context, and runtime state. | Re-run before final status/audit and do not stage runtime dirt. |
| `SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md` | Reinforced no-promotion, no-forward-data, artifact-first discipline. | Keep all rows as research-only. |
| `research_operating_doctrine.md` | Set aggressive research / strict promotion boundary. | Ensure each hypothesis has blockers and no same-dataset validation. |
| `research_current_state.md:70-78` | Science program scaffold and schema rows are active; source budget is zero. | Use lane-owned schema rows, no spending. |
| `PROGRAM_GOVERNOR_2026-05-06.md` | G2 is first-wave science lane; G1/G3/G10 are neighbors. | Neighbor pass after first synthesis. |
| `SCHEMA_CONTRACTS_2026-05-06.md` | Required fields for mechanism/hypothesis/prereg/source/status rows. | Validate JSON rows with `validate_schema_row`. |
| `SOURCE_BUDGET_LEDGER_2026-05-06.md` | `$0` external spend; paid and validation-safe sources blocked. | Keep every source contract `validation_safe=false`. |
| `kb_edge_mechanisms_and_risks.md` | Killed pure volatility-clustering route; elevated H1 autocorrelation as decay discriminator. | Register AR-decay and GARCH-lifecycle separately. |
| `kb_validation_and_monitoring_framework.md` | SPRT/CUSUM and H1 autocorrelation are monitoring/early-warning tools. | Keep G2 outputs observational unless validation lane exists. |
| `research_execution_plan_113q.md` | Existing queue includes HMM/change-point, quantile SL, drawdown EVT, risk of ruin, copula tail dependence. | Translate only non-duplicative rows. |
| `LANE6_TAIL_TRIAGE_2026-05-03.md/json` | Broad vol sizing rejected; rough Hurst and tail diagnostics done; Hawkes/EVT drawdown deferred. | Register source-aware, blocked/future experiments. |
| `LTO018_REGIME_DECAY_OUTCOME_JOIN_2026-05-05.md` | Regime/decay context already exists as K55-ready as-of substrate. | Use HMM/dwell only as context features. |
| `LTO006/LTO007/LTO008` audits | Lifecycle, V2b, pre-fill, and FVG/OB exact-source gaps define survival-model inputs and blockers. | Preregister survival timing without scoring hidden fields. |
| `PHASE3_METHODOLOGY_DIAGNOSTICS_2026-05-03.md` | Same-dataset discovery claims cannot report promotion p-values. | Set DSR/PBO policies to not_computable until prereg/folds exist. |
| Neighbor worktrees G1/G3/G10 | No committed neighbor domain rows. G1 has untracked raw source cache only. | No cross-domain hypotheses merged. |

## Neighbor Pass

Neighbor lanes required by the G2 prompt: G1, G3, and G10.

| lane | actual state checked | result |
| --- | --- | --- |
| G1 | `git status --short` shows `.context/LIVE_STATE.md` runtime dirt and untracked `research/science_program_2026_05/01_domain_syntheses/raw/`; no committed G1 domain synthesis, mechanism rows, hypothesis rows, prereg rows, or goal-status row. | No cross-domain G1 rows merged. |
| G3 | `git status --short` shows `.context/LIVE_STATE.md` runtime dirt only; domain syntheses directory has only `README.md`. | No cross-domain G3 rows merged. |
| G10 | `git status --short` produced no tracked lane artifacts beyond git ignore warnings; domain syntheses directory has only `README.md`. | No cross-domain G10 rows merged. |

Cross-domain hypotheses added in this pass: `[]`.

Deferred cross-domain hypotheses:

- G2+G1: AR-decay windows need G1 methodology rows for multiple-testing/sample-floor enforcement before promotion-style statistics.
- G2+G3: roughness/path-order ambiguity should be merged with G3 geometry/signal rows after G3 produces directional-change or wavelet evidence.
- G2+G10: survival timing should be merged with G10 execution/risk rows after G10 produces pending-vs-native, slippage, or exit-risk preregs.

## Focused Checks Recorded

Completed checks after writing artifacts:

- `python -m json.tool research\science_program_2026_05\01_domain_syntheses\G2_STOCHASTIC_TAILS_SYNTHESIS_2026-05-06.json` parsed the JSON successfully.
- `validate_schema_row` over every mechanism, hypothesis, prereg, source contract, and goal-status row returned `SCHEMA_VALIDATION_OK`.
- `rg --files-without-match "NO_PROMOTION_VERDICT"` across the two G2 scoped artifacts produced no file output, so every G2 artifact carries the verdict.
- `git diff --name-only -- prompts src config scripts\canary_fixtures scripts\canary_test.py scripts\mt5_preflight.py src\components\execution.py src\components\permissions.py src\components\orchestrator.py config\agent_config.yaml` produced no output, so forbidden live trading prompt/risk/execution/permission/safety/selector/MT5/canary/order paths were not touched.
- `python -m pytest tests\test_science_goal_program.py -q -p no:cacheprovider --basetemp pytest_tmp_g2_science_program` was blocked by Windows temp-directory sandbox permissions before test results were usable.
- `python -m pytest tests\test_science_goal_program.py -q -p no:cacheprovider --basetemp C:\tmp\pytest_g2_science_program_final` passed with `9 passed` after approved escalation for the temp-directory blocker.

## Stop Outputs Coverage

| required output | artifact evidence |
| --- | --- |
| Domain synthesis | This file, `## Domain Synthesis`. |
| Lane context ledger | This file, `## Lane Context Ledger`. |
| Ambiguity ledger | This file, `## Ambiguity Ledger`. |
| Counter-evidence and decay-mode review | This file, `## Killed Routes And Counter-Evidence` plus decay discussion under domain synthesis. |
| Mechanism rows | This file and JSON companion `mechanism_rows`. |
| Hypothesis rows | This file and JSON companion `hypothesis_rows`. |
| Killed-route notes | This file, `## Killed Routes And Counter-Evidence`. |
| Experiment prereg specs | This file and JSON companion `experiment_prereg_rows`. |
| Source/budget blockers | This file and JSON companion `source_contract_rows`. |
| Neighbor-lane cross-domain hypotheses after first synthesis pass | This file, `## Neighbor Pass`; no rows merged because neighbors lack committed lane outputs. |
| `goal_status_v1` row | JSON companion `goal_status_row`, with `commit_sha=null` until the scoped commit exists. |

## NO_PROMOTION_VERDICT

Every row and report in this G2 pass remains `NO_PROMOTION_VERDICT`. The pass is primitive-science research only and cannot be used as a live trading, prompt, risk, execution, selector, safety-gate, canary, MT5, paid-data, or order-behavior change.
