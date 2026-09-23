# G1 Validation, Probability, Statistics, Causality Synthesis - 2026-05-06

**Lane:** `G1`  
**Domain:** validation, probability, statistics, causality  
**Status:** `G1_SYNTHESIS_COMPLETE_COMMITTED`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Scope

This is a primitive-science research artifact. It extracts validation/statistics/causality mechanisms and translates them into lane-owned mechanism rows, hypothesis rows, experiment preregistration rows, and source contracts. It does not open outcome slices, run live trading, call MT5, change prompts, alter risk, modify execution, touch permissions/safety gates/selectors/canaries, spend money, or make a promotion claim.

## Mandatory Preflight Evidence

| Requirement | Evidence |
| --- | --- |
| Run live-state generator | `python scripts/generate_live_state.py` in `C:\tmp\gtosg\G1` wrote `.context\LIVE_STATE.md`. |
| Read live state | `.context/LIVE_STATE.md` read after regeneration; it reported clean tree before G1 artifacts except regenerated live-state dirt. |
| Read latest handoff | `.context/LIVE_STATE.md` identified `.context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md`; read. |
| Read quick reference | `.context/00_core/quick_reference_card.md` read; it carries SPRT/power monitoring context. |
| Read doctrine | `.context/00_core/research_operating_doctrine.md` read; active posture is aggressive research, strict promotion. |
| Read research current state | `.context/00_core/research_current_state.md` read; science program is research/tooling only with `NO_PROMOTION_VERDICT`. |
| Read reading order and relevant Tier 2-4 | `.context/00_READING_ORDER.md`, `CLAUDE.md`, `.context/01_knowledge_base/kb_validation_and_monitoring_framework.md`, `.context/01_knowledge_base/kb_edge_mechanisms_and_risks.md`, `.context/03_analysis/research_execution_plan_113q.md`, and `.context/04_agents/ZETA_RED_TEAM.md` read for validation, population, and red-team constraints. |
| Read G0 governor artifacts | Program governor, schema contracts, source/budget ledger, worktree map, G0 cross-agent synthesis, completion audit, and goal-status registry read. |

## Initial Deep-Research Map

Mechanisms worth finding before source search:

| Candidate mechanism | Evidence that distinguishes it from noise | GTOS component affected | Strongest evidence location |
| --- | --- | --- | --- |
| Trial-budget deflation / DSR | Raw lift loses promotion status after cumulative trials and return-distribution adjustment. | Research claim gate, ML/path/orderflow reports | `CLAUDE.md`, `methodology_gate.py`, DSR diagnostics |
| PBO / CPCV path overfit | IS-selected variant ranks poorly OOS across combinatorial splits. | Variant selection, path-scaling, K54/K55 | `methodology_gate.py`, posthoc PBO tooling, CPCV reports |
| Effective independent N | Raw n collapses under bucket/correlation/duplicate stress. | Sample floors, concentration gates, source contracts | effective-N tooling, V2/V3 concentration reports |
| Leakage / as-of contracts | A post-decision or revised field enters feature set; fixed by as-of manifest and embargo. | Data feeds, ML feature bundles, path reconstruction | schema contracts, source contracts, no-leak source docs |
| Causal target-trial framing | Component-effect estimate only interpretable after eligibility, time-zero, assignment, confounders, and positivity are frozen. | Strategy changes, ablations, telemetry | causal source, red-team population checks, prereg rows |
| Power/sample-floor policy | Validation stays blocked until effect size, alpha/beta, label class, and duplicate-adjusted n are reached. | V2b, broker actual-R, forward lanes | quick reference, V2b rolling status, statsmodels docs |

## Source Evidence

Saved raw/source-index evidence lives under:

`research/science_program_2026_05/01_domain_syntheses/raw/G1_validation_statistics_sources_2026-05-06/`

Primary source index:

`research/science_program_2026_05/01_domain_syntheses/raw/G1_validation_statistics_sources_2026-05-06/SOURCE_INDEX_G1_VALIDATION_STATISTICS_2026-05-06.json`

Useful fetched sources:

| Source | Local evidence | G1 use |
| --- | --- | --- |
| White, Reality Check for Data Snooping | `econometric_society_white_reality_check.html:66` | Data reuse and best-model-vs-benchmark inference risk. |
| WMU ScholarWorks backtest overfitting | `wmich_pseudo_math_backtest_overfitting.html:327-328` | Configuration-search overfit and OOS degradation risk. |
| scikit-learn TimeSeriesSplit | `sklearn_timeseriessplit.html:1315-1318`, `1351-1352` | Time-order and gap/embargo source-contract mechanism. |
| PMC target trial emulation | `pmc_target_trial_emulation_causal_inference.html:1394`, `1422`, `1429-1433` | Causal identification, time-zero, no post-baseline assignment. |
| Nature Li-Ji effective tests | `nature_li_ji_effective_tests.html:779`, `889` | Effective number of correlated tests and sample design. |
| statsmodels power/confint | `statsmodels_power_proportions.html:2358-2375`, `statsmodels_proportion_confint.html:2262-2275` | Power/sample-floor and Wilson/binomial interval references. |

Blocked raw fetches were recorded, not bypassed:

- SSRN DSR page, SSRN PBO page, OUP Benjamini-Hochberg page, and SSRN Hansen SPA page returned Cloudflare challenge HTML.
- No paid access, paywall bypass, credentialed access, or source spend was attempted.

## Repo Cross-Check

| G1 idea | Current GTOS state | Evidence |
| --- | --- | --- |
| DSR/PBO/effective-N gate | Already active as research infrastructure; G1 should standardize policy, not reimplement. | `src/research_infra/methodology_gate.py:17-19`, `:178`, `:262-309`; `CLAUDE.md:210`. |
| Discovery-only Phase 3 claims | Already blocked from promotion p-values. | `research/phase_3_external_feed_validation/PHASE3_METHODOLOGY_DIAGNOSTICS_2026-05-03.md:5`; lines 9-15 and diagnostics JSON forbid promotion p-values. |
| V2b validation | Blocked by no resolved prospective pairs; sample floor not evaluable. | `RAW_OHLC_PATH_SCALING_V2B_ROLLING_STATUS_TOOL_2026-05-03.md:6`, `:35-36`, `:81`, `:108`. |
| Label separation | Science schema requires separate broker actual-R, synthetic path-R, lifecycle/no-fill, observation-only, context-only labels. | `SCHEMA_CONTRACTS_2026-05-06.md:52`, `:126-127`. |
| Source contract no-lookahead | Required by G0 and source/budget ledger; validation_safe remains false until legal/timestamp/cache/parser tests pass. | `SCHEMA_CONTRACTS_2026-05-06.md:102`, `:124`; `SOURCE_BUDGET_LEDGER_2026-05-06.md:15`, `:30`. |
| Same-dataset path/V3 claims | Useful discovery only; not validation or promotion. | `.context/00_core/research_current_state.md:429`, `:436-437`, `:764`, `:825`. |
| OB headline overclaim | OB mechanism survives separately, but relative headline failed DSR. | `CLAUDE.md:221`, `:236`. |

## Domain Synthesis

The G1 primitive mechanism is not a new trading setup. It is the machinery that decides when a setup claim is allowed to mean anything.

The current GTOS research map already contains many useful discovery routes, but the main validation failure mode is predictable: repeated searches produce an attractive row, agents quote the row as if it were validation, and later work forgets how many variants, cohorts, prompts, label classes, and datasets were touched. G1 therefore translates validation science into six reusable gates:

1. Trial-budget deflation: no raw p-value or lift stands alone after hidden trials.
2. PBO/CPCV path overfit: an in-sample winner must survive alternate path splits or be labeled diagnostic.
3. Effective-N/concentration: raw n is not evidence when the rows share the same underlying event or bucket.
4. Leakage/as-of source contract: a feature is illegal for decision-time use until its timestamp and field lineage prove availability.
5. Causal target-trial framing: a component-effect claim is causal only if eligibility, assignment, time zero, follow-up, estimand, and positivity are frozen before outcomes.
6. Power/sample-floor policy: validation remains blocked until the minimum effect can be detected in the correct label lane.

## Mechanism Rows

Full rows are in:

`research/science_program_2026_05/02_hypothesis_registry/G1_VALIDATION_STATISTICS_MECHANISMS_2026-05-06.json`

| mechanism_id | Mechanism | Existing overlap |
| --- | --- | --- |
| `SCI-G1-VAL-001` | Selection-adjusted probability / DSR | Active methodology gate, DSR diagnostics |
| `SCI-G1-VAL-002` | CPCV/PBO path overfit | `cscv_pbo`, posthoc PBO tooling |
| `SCI-G1-VAL-003` | Effective-N / concentration | effective-N scripts, V2/V3 concentration blockers |
| `SCI-G1-VAL-004` | Leakage/as-of contracts | source_contract_v2, no-lookahead source readiness |
| `SCI-G1-VAL-005` | Causal target-trial emulation | partial prereg overlap, no generic target-trial protocol yet |
| `SCI-G1-VAL-006` | Power/sample-floor/sequential policy | SPRT tables, V2b sample-floor status |

## Hypothesis Rows

Full rows are in:

`research/science_program_2026_05/02_hypothesis_registry/G1_VALIDATION_STATISTICS_HYPOTHESES_2026-05-06.json`

| hypothesis_id | Primary claim gate | Label class |
| --- | --- | --- |
| `SCI-G1-HYP-001` | Trial-budget DSR gate | `broker_actual_r` |
| `SCI-G1-HYP-002` | CSCV/PBO frozen-universe gate | `synthetic_path_r` |
| `SCI-G1-HYP-003` | Effective-N/concentration gate | `synthetic_path_r` |
| `SCI-G1-HYP-004` | No-leak/as-of source-contract gate | `context_only` |
| `SCI-G1-HYP-005` | Target-trial causal-estimand gate | `observation_only` |
| `SCI-G1-HYP-006` | Power/sample-floor/sequential gate | `broker_actual_r` |

## Experiment Prereg Specs

Full rows are in:

`research/science_program_2026_05/03_experiment_specs/G1_VALIDATION_STATISTICS_PREREGS_2026-05-06.json`

Every prereg row is frozen at `2026-05-06T06:50:00Z`, keeps `outcome_review_opened=false`, and carries `NO_PROMOTION_VERDICT`. These are future validation contracts, not outcome analyses.

## Source/Budget Blockers

Full source contracts are in:

`research/science_program_2026_05/00_control/G1_VALIDATION_STATISTICS_SOURCE_CONTRACTS_2026-05-06.json`

Blockers:

- Source/budget ledger cap remains `$0`; spend allowed is `False`.
- No public methodology source is marked `validation_safe`; these are context/control references, not decision-time market data.
- SSRN/OUP raw pages blocked by Cloudflare challenge are recorded as blocked; no bypass was attempted.
- Any future market source must pass `source_contract_v2` legality, publication-asof timestamp, cache, parser, and no-lookahead tests before validation use.

## Lane Context Ledger

| Artifact/source read | Claim/mechanism changed | Next question created | Next source/repo check |
| --- | --- | --- | --- |
| `.context/LIVE_STATE.md` | Worktree is G1 branch with only regenerated live-state dirt before artifacts. | Which files are safe to commit? | `git status --short` and forbidden-path diff before commit. |
| G0 program governor/schema/source ledger | G1 must emit rows, not promotion claims; all rows keep `NO_PROMOTION_VERDICT`. | Should master registries be edited? | Use lane-owned G1 files; leave G0 master registry for later reconciliation. |
| `methodology_gate.py` | DSR/PBO/effective-N infrastructure exists; G1 should formalize policy. | What missing mechanism remains? | Add causal target-trial and sample-floor policies as rows. |
| Phase 3 methodology diagnostics | Discovery-only claims must report `not_computable`, not raw promotion p-values. | How to prevent future markdown misuse? | Hypotheses require hardened methodology columns and source contracts. |
| V2b rolling status | Sample-floor state already distinguishes no resolved pairs from below floor. | How to generalize sample-floor policy? | Add G1 sample-floor/power prereg row. |
| White data-snooping source | Repeated data reuse is itself a primitive mechanism. | How does this map to GTOS variants? | Trial-budget and PBO rows. |
| WMU backtest-overfit source | Configuration count must be explicit. | What if trial count is unknown? | Block promotion p-values until declared. |
| scikit-learn TimeSeriesSplit | Time-ordered split plus gap is a practical leakage contract. | How to handle label horizon? | Purge/embargo in G1 no-leak prereg. |
| PMC causal source | Causal estimates need identification assumptions, time-zero alignment, and no post-baseline assignment. | Is GTOS causal tooling present? | No generic protocol found; add mechanism/hypothesis/prereg. |
| Nature Li-Ji source | Effective-N is a correlated-testing/sample-design mechanism. | How should it affect GTOS? | effective_N >= 3 and bucket caps as promotion prerequisites. |

## Ambiguity Ledger

| Ambiguity | Pursued answer | Status |
| --- | --- | --- |
| Should G1 populate master mechanism/hypothesis registries? | G0 synthesis says master registries are reconciled by G0 after lane evidence; G1 writes lane-owned schema-valid files. | Answered: lane files only. |
| Can public SSRN/OUP source pages be cached directly? | Direct `curl.exe` fetches were attempted with approved network access; several returned Cloudflare challenges. | Blocked but recorded; no bypass. |
| Can DSR/PBO/effective-N be reported for current G1 rows? | G1 opened no outcomes; rows are prereg/policy only. | Answered: not_computable for current lane. |
| Are neighbor-lane cross-domain hypotheses available? | G2/G9/G10 worktrees showed no lane-owned output artifacts beyond scaffold at inspection time. | Answered: none added. |
| Is causal inference already implemented generically? | Repo has prereg/no-lookahead fragments, but no generic target-trial-emulation gate for component effects. | Answered: new G1 mechanism/prereg. |

## Counter-Evidence And Decay-Mode Review

| Mechanism | Counter-evidence or misuse risk | Decay/control action |
| --- | --- | --- |
| DSR/trial budget | Over-deflation is possible if correlated tests are counted as fully independent; under-deflation is worse if hidden variants are omitted. | Record both nominal and effective trial counts; block if trial ledger is unknown. |
| PBO/CPCV | PBO is unstable with too few periods/strategies and invalid if universe is post-hoc. | Require frozen universe and period matrix; otherwise diagnostic_only. |
| Effective-N | Participation ratio can hide causal dependence if cohort labels are wrong. | Pair with duplicate policy, leave-one-bucket stress, and bucket caps. |
| Leakage/as-of | Passing a timestamp check does not prove semantic availability if source publication conventions are wrong. | Require source contract with publication timestamp and field-lineage whitelist. |
| Causal target trial | Observational data cannot guarantee exchangeability; positivity may fail in deterministic rules. | Report causal blocker instead of causal effect when assumptions fail. |
| Power/sample floor | A hard floor can be gamed by mixing label classes or duplicate rows. | Floor applies after label separation and duplicate/effective-N adjustment. |

## Killed-Route Notes

- Same-dataset discovery result labeled as validation remains killed.
- Raw p-value promotion without DSR/PBO/effective-N remains killed.
- OB relative-advantage headline remains DSR-failed; do not re-cite it as validated.
- V2b validation remains blocked until resolved post-cutoff OB-boundary/J46 pairs and sample floors exist.
- V3 same-dataset replay remains discovery-only; no promotion or validation claim.
- Any COT/direct macro feed without publication-asof source contract remains blocked as validation-safe.

## Neighbor Pass

After the first synthesis pass, G1 inspected neighboring lane worktrees `C:\tmp\gtosg\G2`, `C:\tmp\gtosg\G9`, and `C:\tmp\gtosg\G10` for G2/G9/G10 lane-owned output artifacts outside goal prompts. No committed or uncommitted neighbor output artifacts were found. G2 had only regenerated `.context/LIVE_STATE.md` dirt. Result: no neighbor-derived cross-domain hypotheses were added.

Potential future cross-domain hooks once neighbors produce evidence:

- G2 stochastic/tails: power/sample-floor policy should use tail-risk-aware effect sizes for fat-tailed R distributions.
- G9 AI/ML: no-leak feature bundle and trial-budget ledger should be mandatory for every K55/LLM classifier claim.
- G10 execution/risk: causal target-trial protocol should separate entry, exit, risk sizing, cost, and lifecycle interventions.

These are not hypothesis rows yet because neighbor evidence does not exist.

## Required Stop Outputs Map

| Required output | Artifact/evidence |
| --- | --- |
| Domain synthesis | This file. |
| Lane context ledger | This file, Lane Context Ledger section. |
| Ambiguity ledger | This file, Ambiguity Ledger section. |
| Counter-evidence and decay-mode review | This file, Counter-Evidence section. |
| Mechanism rows | `G1_VALIDATION_STATISTICS_MECHANISMS_2026-05-06.json`. |
| Hypothesis rows | `G1_VALIDATION_STATISTICS_HYPOTHESES_2026-05-06.json`. |
| Killed-route notes | This file, Killed-Route Notes section. |
| Experiment prereg specs | `G1_VALIDATION_STATISTICS_PREREGS_2026-05-06.json`. |
| Source/budget blockers | This file plus source contracts and source index. |
| Neighbor-lane cross-domain hypotheses after first pass | Neighbor pass completed; no rows added because no neighbor outputs exist. |

## NO_PROMOTION_VERDICT

Every G1 report, row, source contract, and prereg artifact carries `NO_PROMOTION_VERDICT`. This lane produces validation-control research only.
