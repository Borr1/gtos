# G9 AI, ML, RL, LLM Trading Systems Synthesis - 2026-05-06

**Lane:** `G9`  
**Role:** `science_lane`  
**Domain:** `AI, ML, RL, LLM trading systems`  
**Status:** `G9_SYNTHESIS_COMPLETE_SHADOW_ONLY`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Objective

Map K55 target/model paths, no-leak feature bundles, classical-vs-LLM comparisons, tool grounding, debate, Reflexion, and offline-RL-style policy learning into measurable shadow-only experiments.

This lane is research/control work only. It does not change live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid-data paths, or order behavior.

## Mandatory Preflight Evidence

| Requirement | Evidence |
| --- | --- |
| Run live-state generator | `python scripts/generate_live_state.py` wrote `.context/LIVE_STATE.md`. |
| Read live state | `.context/LIVE_STATE.md` read; HEAD was `42bf621c research: merge g0 wave 1 reconciliation`, and it flagged `research_current_state.md` stale versus the G0 wave-1 merge. |
| Read latest handoff | `.context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md` read. |
| Read quick reference | `.context/00_core/quick_reference_card.md` read. |
| Read doctrine | `.context/00_core/research_operating_doctrine.md` read. |
| Read research current state | `.context/00_core/research_current_state.md` read, then direct newer G0 artifacts were read because LIVE_STATE marked it stale. |
| Read reading order and relevant Tier 2-4 | `.context/00_READING_ORDER.md` read; relevant AI/ML artifacts listed below were read directly. |
| Read controlling G9 prompt | `research/science_program_2026_05/04_goal_prompts/G9_G9_AI_ML_SYSTEMS_GOAL_PROMPT_2026-05-06.md` read. |
| Read merged G0 reconciliation and registries | `G0_WAVE1_RECONCILIATION_2026-05-06.md`, `SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md`, `SOURCE_CONTRACT_REGISTRY_2026-05-06.md`, and `GOAL_STATUS_REGISTRY_2026-05-06.json` read at HEAD `42bf621c`. |

## Initial Deep-Research Map

Mechanisms worth finding before source search:

| Mechanism family | Evidence that would distinguish it from noise | GTOS component affected | Strongest evidence location |
| --- | --- | --- | --- |
| K55 label-safe target/model gating | A matching K55 artifact computes read-only predictions only when target, feature bundle, numeric weights, threshold, and no-leak keys match. | K55 ML shadow, future paired AI-vs-ML review | K55 registry, K55 tests, LTO-023 report |
| No-leak feature bundle provenance | Feature vectors include only decision-time/as-of fields, while broker/path labels stay outside features. | ML feature substrate, source contracts | K55 target feature registry, G1 validation rows |
| Classical ML vs LLM complementarity | Paired K55 and Component 3A decisions disagree in explainable cohorts, then broker actual-R or synthetic context resolves whether the disagreement is useful. | Component 3A shadow review, K55 comparison | `ml_shadow_predictions.jsonl`, decision diagnostics, account truth |
| Tool-grounded LLM numeric verification | Tool or MCP-style retrieval lowers precision/hallucination errors in MSO facts without changing decisions. | `ai_tools`, PrimaryAnalyzer shadow design | `research/tool_use_grounding/DESIGN.md`, `src/components/ai_tools/` |
| Multi-agent debate disagreement | Bull/Bear/Judge disagreement isolates false approvals or false rejections, but only after budget-capped shadow approval. | Component 3B, AI decision audit | `src/components/debate.py`, LTO-024 dossier, Domain 20 literature |
| Reflexion/verbal reinforcement | Post-trade verbal failure-mode tags create durable next-trade context or training labels without model fine-tuning. | Knowledge base, K55 labels, future prompt memory | Domain 20 Reflexion/FinCon rows, adaptive review code |
| Offline RL policy approximation | A tabular/offline RL policy over regime, side, instrument, and framework can be compared to hand policies without live exploration or risk changes. | Research-only sizing/exit evaluation, G10 future neighbor | Domain 20 RL literature, J46/J49/S79 artifacts |
| LLM self-report and alignment audit | A model may omit its own precision or policy failures under pressure; audit needs independent logs, not self-report. | AI monitoring and malformed/refusal logs | Domain 20 alignment literature, malformed/decision logs |

## Repo Cross-Check

| G9 route | Current GTOS state | Evidence |
| --- | --- | --- |
| K55 target and feature substrate | Active as read-only shadow rows; inference enabled rows are zero because production model artifact is missing. | `research/program_control/LTO023_K55_ML_SHADOW_2026-05-05.md:13`, `:18`, `:27-31`, `:42`; `research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.md:12`, `:16`, `:20`. |
| Stale K54 model reuse | Explicitly blocked; K54 v3/v4 cannot be silently reused for K55 inference. | `research/program_control/K55_SOURCE_BUNDLE_INTEGRATION_PLAN_2026-05-06.md:36-44`; `research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md:13-18`, `:35`, `:43`. |
| Same-cohort K54 iteration | Closed/deferred until label-rich K55 shadow cohort or much larger balanced sample exists. | `research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md:23`, `:28`, `:37-39`. |
| Tool grounding | `ai_tools` scaffolding exists, but PrimaryAnalyzer is not wired to it and current `_call_claude` makes a single SDK call without `tools=`. | `src/components/ai_tools/README.md:1`, `:7`, `:34-46`; `research/tool_use_grounding/DESIGN.md:30`, `:928`; `src/components/primary_analyzer.py:368-397`. |
| Component 3B debate | Code and config exist, but orchestration remains parked/approval-blocked and debate is not imported by orchestrator. | `src/components/debate.py:1`, `:87`; `config/agent_config.yaml:195-198`; `research/program_control/LTO024_COMPONENT3B_TOOL_GROUNDING_REFLEXION_APPROVAL_DOSSIER_2026-05-05.md:8`, `:18-19`, `:26-33`; `.context/00_core/research_current_state.md:433`, `:1271`. |
| Reflexion | Research route exists conceptually through Domain 20 and LTO-024, but no wiring or AI spend is approved. | `research/ml_program/literature/20_rl_llms_in_trading/papers.md:860-871`, `:912-923`; `research/program_control/LTO024_COMPONENT3B_TOOL_GROUNDING_REFLEXION_APPROVAL_DOSSIER_2026-05-05.md:8`, `:26-33`. |
| G0 wave-1 reconciliation | G9 was absent from wave 1 and is explicitly a blocking missing lane for the neighbor pass. | `research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md:11-18`, `:49`; `research/science_program_2026_05/05_synthesis/G0_WAVE1_RECONCILIATION_2026-05-06.md:18-30`, `:108`. |
| Source/budget safety | All wave-1 source contracts remain validation-safe false and the source budget cap remains $0. | `research/science_program_2026_05/00_control/SOURCE_CONTRACT_REGISTRY_2026-05-06.md:10`, `:23`; `research/science_program_2026_05/00_control/SOURCE_BUDGET_LEDGER_2026-05-06.md:5`, `:31-34`. |

## Domain Synthesis

G9's primitive-science answer is that GTOS should not treat "AI" as one module. It should split AI/ML/RL/LLM ideas into independent shadow mechanisms with separate evidence lanes:

1. **K55 as a label-safe classical model substrate.** The current K55 work is valuable because it forces target versioning, no-leak feature keys, stale-model rejection, and label eligibility. It is not a promoted classifier because current rows are synthetic-path-context-only and inference is disabled without a matching artifact.
2. **Classical-vs-LLM comparison as paired evidence, not a replacement fight.** The useful question is not "ML beats Claude" globally. The useful question is when K55, deterministic mechanics, and Component 3A disagree, and whether those disagreement cohorts are stable after broker actual-R, synthetic path-R, lifecycle/no-fill, duplicate, and source controls.
3. **Tool grounding as numeric-fact verification, not a live prompt change.** Local `ai_tools` and the tool-use design already target recent outcomes, session volatility, correlation exposure, and similar setup retrieval. G9 maps this into observation-only preregs until explicit approval exists for API calls and prompt/runtime wiring.
4. **Debate as disagreement instrumentation.** Component 3B can be studied as a shadow disagreement engine only after owner approval and a token budget. The current correct state is parked, not deleted and not activated.
5. **Reflexion as post-trade label generation.** Reflexion should first produce structured failure-mode tags and counterfactual notes that K55 can consume later as labels or context. It must not be injected into live prompts or decisions without a separate approval/promotion dossier.
6. **Offline RL as a policy-comparison harness.** RL is attractive for sizing and exit policy because it directly optimizes sequential reward under frictions, but GTOS's live sample is too small for online exploration. The only acceptable first experiment is offline, frozen, duplicate-aware comparison against hand policies.
7. **LLM self-audit has to be externally verified.** Finance LLM literature and GTOS hallucination history both argue that model self-report is not enough. Any LLM-generated rationale, debate verdict, or reflection needs independent source-grounding, numeric verification, and malformed/refusal monitoring.

## Killed-Route Notes

- `KILL-G9-001`: Do not wire stale K54 v2/v3/v4 models into K55 inference. K55 requires target and feature-bundle version match plus no-leak model artifact checks.
- `KILL-G9-002`: Do not iterate same-cohort K54 architectures or loss functions as if the v3/v4 failures did not happen.
- `KILL-G9-003`: Do not change PrimaryAnalyzer prompts, runtime, or tool influence from this lane. Tool grounding is preregistered shadow/approval work only.
- `KILL-G9-004`: Do not run Component 3B debate or Reflexion API calls without explicit owner approval, model scope, and token/cost caps.
- `KILL-G9-005`: Do not call synthetic path labels validation or promotion evidence for K55, debate, Reflexion, or RL.
- `KILL-G9-006`: Do not treat public LLM/RL trading-agent papers as validation for GTOS. They provide mechanism priors and counter-evidence only.
- `KILL-G9-007`: Do not run online RL, live exploration, risk changes, sizing changes, execution changes, order changes, or safety-gate changes.
- `KILL-G9-008`: Do not add paid data, paid model evaluation, broad AI replay, or web-derived market sources unless the source/budget ledger and owner approval allow it.

## Source And Budget Blockers

- External cash cap remains `$0`; no paid source, paid model call, Databento broad pull, or subscription is authorized.
- G9 did not fetch new public web evidence because the required AI/ML/RL/LLM source context was already available in local cached literature and program-control artifacts.
- Local literature sources are mechanism/context evidence only. They are not validation-safe market sources.
- `source_contract_v2.validation_safe` remains `false` for every G9 source row.
- Any future LLM/API experiment needs a separate budget row, prompt/runtime approval, and no-action safety counters before execution.

## Neighbor-Lane Pass

After the first synthesis pass, G9 read neighboring lane outputs from G1, G4, and G10.

- G1 has committed validation/statistics rows. G9 added hypotheses requiring DSR/PBO/effective-N, no-leak feature contracts, and target-trial framing for K55, tool grounding, debate, Reflexion, and offline RL.
- G4 has committed microstructure/orderflow rows. G9 added cross-domain hypotheses for K55 source bundles and tool grounding that treat orderflow/depth as source-status and as-of features, not validation-safe live filters.
- G10 has no lane-owned synthesis output yet; only its goal prompt is present. G9 therefore added no G10-derived row as evidence, but it marked offline RL sizing/exit work as future G10-neighbor dependent.

Concrete cross-domain G9 rows created from the neighbor pass:

- `HYP-G9G1-K55-NOLEAK-002`: K55 no-leak bundle integrity inherits G1 leakage and label-separation discipline.
- `HYP-G9G1-COMPARE-AIML-003`: AI-vs-ML paired comparison inherits G1 trial-budget/effective-N discipline.
- `HYP-G9G4-TOOL-ORDERFLOW-005`: tool grounding may expose G4 orderflow/source-status facts only as shadow/context outputs.
- `HYP-G9G4-K55-SOURCE-006`: K55 can ingest G4 orderflow/source provenance flags only after source-transfer and no-leak checks.

No G10 row was added because adding cross-domain evidence without neighbor-owned output would violate source and killed-route discipline.

## Output Files

- `research/science_program_2026_05/01_domain_syntheses/G9_AI_ML_SYSTEMS_SYNTHESIS_2026-05-06.md`
- `research/science_program_2026_05/01_domain_syntheses/G9_CONTEXT_LEDGER_2026-05-06.md`
- `research/science_program_2026_05/01_domain_syntheses/G9_AMBIGUITY_LEDGER_2026-05-06.md`
- `research/science_program_2026_05/01_domain_syntheses/G9_SOURCE_COUNTEREVIDENCE_LEDGER_2026-05-06.md`
- `research/science_program_2026_05/00_control/G9_AI_ML_SYSTEMS_SOURCE_CONTRACTS_2026-05-06.json`
- `research/science_program_2026_05/00_control/G9_AI_ML_SYSTEMS_GOAL_STATUS_2026-05-06.json`
- `research/science_program_2026_05/02_hypothesis_registry/G9_AI_ML_SYSTEMS_MECHANISMS_2026-05-06.json`
- `research/science_program_2026_05/02_hypothesis_registry/G9_AI_ML_SYSTEMS_HYPOTHESES_2026-05-06.json`
- `research/science_program_2026_05/03_experiment_specs/G9_AI_ML_SYSTEMS_EXPERIMENT_PREREGS_2026-05-06.json`
- `research/science_program_2026_05/05_synthesis/G9_AI_ML_SYSTEMS_COMPLETION_AUDIT_2026-05-06.md`
- `research/science_program_2026_05/05_synthesis/G9_AI_ML_SYSTEMS_COMPLETION_AUDIT_2026-05-06.json`

## NO_PROMOTION_VERDICT

Every G9 mechanism, hypothesis, source contract, prereg, ledger, audit, and synthesis artifact carries `NO_PROMOTION_VERDICT`. This lane produced research artifacts only.
