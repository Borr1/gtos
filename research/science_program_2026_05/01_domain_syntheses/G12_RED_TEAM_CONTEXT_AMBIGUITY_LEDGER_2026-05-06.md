# G12 Red-Team Context And Ambiguity Ledger - 2026-05-06

**Lane:** `G12`  
**Role:** methodology red team  
**Worktree:** `C:\tmp\gtosg\G12`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Initial Red-Team Mechanism Map

| Mechanism worth finding | Evidence that would distinguish it from noise | GTOS component at risk | Strongest evidence location |
|---|---|---|---|
| Source publication leakage | A source row is joined by observation date, cache date, or daily close before true publication/as-of time. | Macro/vol context, G7/G8/G11 source contracts, K55 source flags | CD2-01, G11 source rows, source-contract registry |
| No-leak semantic inversion | `no_leak_fields` lists forbidden outcome/future fields instead of allowed as-of feature fields. | Master hypothesis registry, future prereg cleanup | G11 hypothesis rows and CD2-08 |
| Label-family mixing | Lifecycle/no-fill, synthetic path-R, broker actual-R, cost/slippage, or context labels appear in one metric or denominator. | G8 CD2-02, G9 CD2-03, G10 CD2-06, G11 CD2-07 | Experiment preregistry, CD2 artifacts, G1 synthesis |
| Duplicate or child-row inflation | Attempts, legs, retries, overlapping active setups, or repeated lifecycle checks count as independent observations. | CD2-02 lifecycle, CD2-03 offline RL, CD2-05 event windows, CD2-06 path rows | Prereg duplicate policies and missing-field audit |
| Source-validity drift | Prose implies readiness while all source contracts remain `validation_safe=false`. | CD2-01, CD2-04, CD2-07, CD2-08, K55 source bundles | Source registry and G12 shortlist |
| Promotion drift | A research-only contract reads like a filter, policy, risk rule, K55 feature activation, or live execution change. | CD2 accepted preregs and blocked proposal rows | G0 reconciliation, CD2 files, forbidden-path diff |

## Artifacts Read

| Artifact | Claim or mechanism changed | Next question created | Follow-up check |
|---|---|---|---|
| `.context/LIVE_STATE.md` after regeneration | Current HEAD is `6e0d77dd`; latest handoff is session 54; this branch is `science-goals/g12-red-team`. | Is worktree boundary correct? | `git status --short --branch` showed only regenerated `.context/LIVE_STATE.md` before G12 edits. |
| `.context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md` | Research-only, no-forward-data, no-promotion discipline remains active. | Does G12 need live data? | No; all required evidence is local science-program artifacts. |
| `.context/00_core/quick_reference_card.md` | Live surfaces and emergency stops are out of scope. | Could any CD2 row imply live execution? | Review all CD2 non-authorization sections. |
| `.context/00_core/research_operating_doctrine.md` | Aggressive research is allowed, but promotion requires a separate dossier. | Can G12 clear a source to validation-safe? | No explicit blocker-clearing evidence exists. |
| `.context/00_core/research_current_state.md` | Science program is research/tooling only; G12 had not run. | Are G0 summaries stale versus HEAD? | Read HEAD and G0 CD2 reconciliation directly. |
| `.context/00_READING_ORDER.md` | Red-team work maps to Tier 4 red-team discipline and validation context. | Which neighboring lanes matter? | Read G1, G9, and G11 outputs. |
| `HEAD 6e0d77dd` | HEAD refreshes research state after path repair and touches `.context` docs only. | Did HEAD change science CD2 inputs? | CD2 artifacts are still the current local inputs. |
| `G12_G12_RED_TEAM_GOAL_PROMPT_2026-05-06.md` | Required stop outputs are seven G12-owned review/ledger/decision files. | Should G12 edit master registries? | No; propose exact future corrections only. |
| `G0_CD2_RECONCILIATION_2026-05-06.md/json` | Only two CD2 preregs accepted; six CD2 rows remain blocked/status-only; no source or outcome promoted. | Do accepted rows survive adversarial review? | Review CD2-02 and CD2-03 rows directly. |
| `G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.md/json` | G12 must retain five CD2 addenda and seven standing wave-2 topics. | Does every topic get a ledger row? | Covered across leakage, source, label, duplicate, and decisions files. |
| `SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json` | Master state records 8 no-leak semantic blockers, 18 source-reference issues, 4 G6 label normalizations, 0 survivor rows. | Are blockers hard or cleanup-only? | Hard for outcome opening/promotion; cleanup-only for schema hygiene. |
| `EXPERIMENT_PREREGISTRY_2026-05-06.json` | 97 preregs; `outcome_review_opened=true` rows = 0; both accepted CD2 rows are outcome-closed. | Do accepted rows mix labels in row text? | Label-separation review. |
| `SOURCE_CONTRACT_REGISTRY_2026-05-06.json` | 86 source contracts; `validation_safe=true` rows = 0. | Can any CD2 row rely on validation-safe data? | No; all source use remains blocked/context-only. |
| `GOAL_STATUS_REGISTRY_2026-05-06.json` | G12 status is ready for red team, not complete. | Should G12 edit the status registry? | No, this pass writes G12-owned files only. |
| `SOURCE_BUDGET_LEDGER_2026-05-06.json` | Spend allowed = false; current new external cash cap = `$0`. | Does G12 need public fetches? | No new fetch needed; all required evidence was local. |
| CD2-01 artifacts | Macro/vol source-freshness rules are explicit but unresolved. | Can proposal update master rows now? | No; needs parser/cache/as-of/legal tests first. |
| CD2-02 artifacts | Short-vol lifecycle prereg is schema-safe and label-separated, but source and lifecycle blockers remain. | Is accepted row promotion-safe? | No; survives as research-only, blocked from outcome opening. |
| CD2-03 artifacts | Offline RL reward contract blocks live behavior, duplicates, risk-bank breaches, and label mixing. | Is risk-bank label naming sufficiently strict? | Needs lane-specific R ledger names before outcome opening. |
| CD2-04 artifacts | K55/orderflow contract quarantines raw OFI/depth and allows source-status flags only. | Can all allowed flags become model features? | Some readiness/floor flags should remain audit metadata unless as-of and non-outcome. |
| CD2-05 artifacts | G5/G7 attention rows are duplicate proposals and source-calendar blocked. | Should canonical ID enter master now? | No; future machine row only after source-path and stale-calendar blockers clear. |
| CD2-06 artifacts | Prefill/path capture spec is correct, but current rows miss source hash, source symbol, ordered prefill candles/ticks, pending-native fields, and broker actual-R. | Can path labels be analyzed as outcomes? | No; capture/status only until fields exist. |
| CD2-07 artifacts | Portfolio opportunity-cost sidecar is observation-only and source-blocked; hypothesis ID is not in master. | Can it be master-registered? | No; requires canonical hypothesis and as-of prop/correlation/stress fields. |
| CD2-08 artifact | G0 proposes exact cleanup for G11 no-leak and source placeholders. | Which schema cleanup path should G12 prefer? | Use existing fields first; avoid a new optional field unless schema owner approves. |
| G1 synthesis | G1 confirms trial budget, PBO, effective-N, as-of, target-trial, and sample-floor gates. | Do CD2 rows meet promotion standards? | No; every row remains prereg/source-control only. |
| G9 synthesis, context, ambiguity, source/counter-evidence | K55/RL/tool/debate routes are shadow-only; stale K54 reuse and online RL are killed. | Can CD2-03 imply policy readiness? | No; offline-only and sample/source blocked. |
| G11 synthesis, ledgers, killed routes, completion audit | Source contracts and market expansion remain source-governed and validation-unsafe. | Does CD2-08 cleanup need validation-safe flips? | No; every referenced source stays `validation_safe=false`. |

## Ambiguity Ledger

| Ambiguity | Pursued answer | Status | Next evidence needed |
|---|---|---|---|
| Does `validation_safe=false` mean source rows cannot be referenced at all? | Source rows may be referenced as context/control/provenance, but not validation-safe evidence or live features. | Answered. | Parser/cache/legal/no-lookahead dossier per source before any flip. |
| Are the two accepted CD2 preregs genuine survivors? | They survive only as schema-safe, outcome-closed, research-only preregs. They are not survivor-backlog or promotion survivors. | Answered. | Separate outcome-opening dossier with blocker proof. |
| Is G11 `no_leak_fields` a whitelist or blacklist? | `science_hypothesis_v1.no_leak_fields` expects allowed decision-time/as-of field names. Current G11 rows list forbidden outcome fields. | Answered: semantic inversion blocker. | Future G0/G12 cleanup edit after schema-owner decision. |
| Should CD2-08 add `forbidden_outcome_fields_for_g12_review` to schema? | Prefer no schema extension in this G12 pass; move forbidden names into `promotion_blockers`, `test_method`, or `blocked_dependency_refs` unless schema owner explicitly approves. | Answered as G12 recommendation. | Owner/G0 schema decision if a new field is desired. |
| Can CD2-04 source-readiness flags include broker-actual-R floor state? | Readiness flags can be audit metadata; per-row predictive use is unsafe unless timestamped as-of and proven not to encode post-outcome coverage. | Answered with blocker. | K55 feature-contract update separating metadata from model features. |
| Is CD2-06 decision packet clean if it contains terminal lifecycle context? | The current audit says terminal fields are present and should remain lifecycle/resolution context, not decision features. | Answered with label-separation warning. | Physical row-family separation or explicit feature blacklist before outcome opening. |
| Can CD2-07 quantify opportunity cost without R labels? | It can count transition/source-context states only. Missed R, financial value, synthetic path-R, and broker actual-R require a separate prereg. | Answered. | Canonical master hypothesis plus source-as-of parser fields. |
| Did G12 need web/public fetches? | No. Required source evidence was already cached locally and the task was a red-team review of local registries/artifacts. | Answered. | Public fetch only if a future blocker-clearing dossier needs current source terms/timestamps. |

## NO_PROMOTION_VERDICT

This ledger is G12-owned red-team context only. It opens no outcomes, marks no source validation-safe, and changes no live trading behavior.
