# G9 AI ML Systems Completion Audit - 2026-05-06

**Lane:** `G9`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Status:** `CHECKED_AND_COMMITTED_BY_GIT_HISTORY`

## Objective Restated

Run the G9 primitive-science lane in `C:\tmp\gtosg\G9`: complete mandatory preflight, read the controlling G9 prompt and merged G0 wave-1 reconciliation/registries at HEAD `42bf621c`, use deep research discipline with source, counter-evidence, and ambiguity ledgers, produce only scoped G9 research artifacts, preserve `NO_PROMOTION_VERDICT`, avoid live trading surfaces, and commit scoped G9 artifacts.

## Prompt-To-Artifact Checklist

| Requirement | Evidence |
| --- | --- |
| Mandatory preflight run/read | `G9_AI_ML_SYSTEMS_SYNTHESIS_2026-05-06.md`, Mandatory Preflight Evidence section. |
| Read G0 wave-1 reconciliation and master registries | Synthesis preflight table plus repo cross-check cites G0 reconciliation, master registry, source contract registry, source budget ledger, and goal status registry. |
| Deep research mode | Synthesis Initial Deep-Research Map and Domain Synthesis sections. |
| Lane context ledger | `G9_CONTEXT_LEDGER_2026-05-06.md`. |
| Ambiguity ledger | `G9_AMBIGUITY_LEDGER_2026-05-06.md`. |
| Source/counter-evidence ledger | `G9_SOURCE_COUNTEREVIDENCE_LEDGER_2026-05-06.md`. |
| K55 target/model path mapping | Mechanism `SCI-G9-K55-TARGET-001`, hypothesis `HYP-G9-K55-ARTIFACT-001`, prereg `EXP-G9-K55-ARTIFACT-001`. |
| No-leak feature bundle mapping | Mechanism `SCI-G9-NOLEAK-FEATURE-002`, hypotheses `HYP-G9G1-K55-NOLEAK-002` and `HYP-G9G4-K55-SOURCE-006`, preregs `EXP-G9-K55-NOLEAK-002` and `EXP-G9-K55-SOURCE-006`. |
| Classical-vs-LLM comparison mapping | Mechanism `SCI-G9-AIML-COMPLEMENT-003`, hypothesis `HYP-G9G1-COMPARE-AIML-003`, prereg `EXP-G9-AIML-COMPARATOR-003`. |
| Tool grounding mapping | Mechanism `SCI-G9-TOOL-GROUND-004`, hypotheses `HYP-G9-TOOL-NUMERIC-004` and `HYP-G9G4-TOOL-ORDERFLOW-005`, preregs `EXP-G9-TOOL-NUMERIC-004` and `EXP-G9-TOOL-ORDERFLOW-005`. |
| Debate mapping | Mechanism `SCI-G9-DEBATE-DISAGREE-005`, hypothesis `HYP-G9-DEBATE-DISAGREE-007`, prereg `EXP-G9-DEBATE-007`. |
| Reflexion mapping | Mechanism `SCI-G9-REFLEXION-LABEL-006`, hypothesis `HYP-G9-REFLEXION-LABEL-008`, prereg `EXP-G9-REFLEXION-008`. |
| RL mapping | Mechanism `SCI-G9-OFFLINE-RL-007`, hypothesis `HYP-G9-OFFLINE-RL-POLICY-009`, prereg `EXP-G9-OFFLINE-RL-009`. |
| LLM self-audit mapping | Mechanism `SCI-G9-LLM-SELFAUDIT-008`, hypothesis `HYP-G9-LLM-SELFAUDIT-010`, prereg `EXP-G9-LLM-SELFAUDIT-010`. |
| Mechanism rows | `G9_AI_ML_SYSTEMS_MECHANISMS_2026-05-06.json`, 8 rows. |
| Hypothesis rows | `G9_AI_ML_SYSTEMS_HYPOTHESES_2026-05-06.json`, 10 rows. |
| Experiment prereg specs | `G9_AI_ML_SYSTEMS_EXPERIMENT_PREREGS_2026-05-06.json`, 10 rows, all `outcome_review_opened=false`. |
| Source/budget blockers | `G9_AI_ML_SYSTEMS_SOURCE_CONTRACTS_2026-05-06.json`, 8 rows, all `validation_safe=false`; synthesis Source And Budget Blockers section. |
| Neighbor pass after first synthesis | Synthesis Neighbor-Lane Pass section reads G1, G4, and G10 and adds only G1/G4-derived rows. |
| Killed-route notes | Synthesis Killed-Route Notes section. |
| Preserve `NO_PROMOTION_VERDICT` | Every scoped G9 artifact contains `NO_PROMOTION_VERDICT`; coverage scan passed with 12 files. |
| Only scoped G9 research artifacts | G9 output paths are under `research/science_program_2026_05/`; forbidden-surface diff pending. |
| Do not touch live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid data, or order behavior | No such edits intended; final forbidden-surface diff pending. |

## Focused Checks

| Check | Result |
| --- | --- |
| G9 JSON parse | `G9 JSON parse ok`. |
| G9 required-field/schema row policy | `G9 schema/row policy checks ok`. |
| `NO_PROMOTION_VERDICT` coverage | `NO_PROMOTION_VERDICT coverage ok: 12 files`. |
| Forbidden live-surface diff | `git diff --name-only -- prompts src config scripts/canary_fixtures scripts/mt5_preflight.py scripts/canary_test.py src/components/permissions.py src/components/execution.py` returned empty output. |
| Science-goal pytest | First sandbox run failed before tests with Windows temp-dir `PermissionError`; approved rerun of `python -m pytest tests\test_science_goal_program.py -q -p no:cacheprovider --basetemp C:\tmp\pytest_g9_science_program` passed with `9 passed`. |
| Runtime dirt boundary | `git status --short` showed generated `.context/LIVE_STATE.md` dirt plus scoped untracked G9 artifacts; `.context/LIVE_STATE.md` is not part of the scoped G9 commit. |

## Blockers

- K55 inference remains disabled until a matching K55 artifact exists.
- Debate, tool grounding, and Reflexion remain approval-blocked and budget-blocked.
- G10 neighbor evidence is absent, so offline-RL execution/risk rows are future-neighbor dependent.
- Source contracts remain `validation_safe=false`; no source or result is promotion-safe.

## NO_PROMOTION_VERDICT

This audit is research-only and carries `NO_PROMOTION_VERDICT`.
