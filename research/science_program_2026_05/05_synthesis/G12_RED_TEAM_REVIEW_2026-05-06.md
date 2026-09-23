# G12 Red-Team Review - 2026-05-06

**Lane:** `G12`  
**Status:** `G12_RED_TEAM_REVIEW_COMPLETE_RESEARCH_ONLY`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Objective Restated

Run the G12 methodology red-team review for the GTOS primitive-science program at HEAD `6e0d77dd`, using the controlling G12 prompt, G0 CD2 reconciliation, master registries, source/budget/status registries, all CD2-01 through CD2-08 artifacts, and neighboring G1/G9/G11 outputs. The review must cover leakage, post-hoc selection, duplicate counting, label mixing, source invalidity, stale as-of rules, `validation_safe` drift, `outcome_review` drift, and promotion drift. It must write G12-owned artifacts only and preserve `NO_PROMOTION_VERDICT`.

## Evidence Base

G12 completed the mandatory GTOS preflight:

- ran `python scripts/generate_live_state.py`;
- read `.context/LIVE_STATE.md`, latest handoff `SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md`, quick reference, research doctrine, research current state, and reading order;
- verified current branch `science-goals/g12-red-team` and HEAD `6e0d77dd`;
- read `G12_G12_RED_TEAM_GOAL_PROMPT_2026-05-06.md`;
- read `G0_CD2_RECONCILIATION_2026-05-06.md/json`;
- read `G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.md/json`;
- read `SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json`, `EXPERIMENT_PREREGISTRY_2026-05-06.json`, `SOURCE_CONTRACT_REGISTRY_2026-05-06.json`, `GOAL_STATUS_REGISTRY_2026-05-06.json`, and `SOURCE_BUDGET_LEDGER_2026-05-06.json`;
- read all CD2-01 through CD2-08 artifacts and neighboring G1/G9/G11 outputs needed for validation, ML/RL, and source-governance checks.

## Registry Facts Checked

| Check | Result |
|---|---:|
| Experiment preregs | `97` |
| Accepted CD2 preregs | `2` |
| `outcome_review_opened=true` preregs | `0` |
| Source contracts | `86` |
| `validation_safe=true` source contracts | `0` |
| Survivor backlog rows | `0` |
| No-leak semantic blockers | `8` |
| Source-reference issues | `18` |
| G6 master label-class normalizations | `4` |
| Source budget spend allowed | `false` |
| New external cash cap | `$0` |

## Executive Verdict

The two registered CD2 preregs survive red-team review only as schema-safe, outcome-closed, research-control artifacts:

- `EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001`;
- `EXP-G9-CD2-03-OFFLINE-RL-RISKBANK-001`.

They are not validation-safe, not promotion-safe, not source-safe, and not survivor-backlog rows. All six other CD2 assignments remain blocked or status-only. G12 finds no basis to change any master registry, no basis to set `validation_safe=true`, and no basis to set `outcome_review_opened=true`.

## Critical Findings

| ID | Severity | Finding | Decision |
|---|---|---|---|
| `G12-FIND-001` | High | G11 `no_leak_fields` semantic inversion remains a hard blocker: 8 G11 rows list forbidden outcome/future fields where the schema expects allowed as-of features. | Block outcome opening and promotion until cleanup. |
| `G12-FIND-002` | High | Macro/vol publication leakage remains unresolved across COT, FRED, BIS, Cboe daily vol CSVs, and VRP. Observation-date, same-day daily, or revised joins are unsafe. | CD2-01 and related rows stay source-blocked. |
| `G12-FIND-003` | High | Broker actual-R evidence remains too sparse for actual-R claims, and CD2-02/CD2-03/CD2-06 correctly keep broker actual-R out of primary metrics. | Preserve actual-R separation and sample blocker. |
| `G12-FIND-004` | High | CD2-06 path/lifecycle data is not analysis-ready: current rows miss source hashes, source symbols, ordered prefill candles/ticks, pending-native fields, and most trade IDs. | Status-only; no no-retrace/path/fill-quality validation. |
| `G12-FIND-005` | Medium | CD2-03 offline RL reward contract is well-bounded, but future risk-bank fields need label-lane-specific names to avoid mixing synthetic path-R with broker actual-R. | Accepted prereg survives with ledger-naming blocker. |
| `G12-FIND-006` | Medium | CD2-04 K55 source-status contract is narrow enough, but readiness/floor-met flags tied to actual-R or candidate counts should be audit metadata unless timestamp-safe and excluded from outcome leakage. | Status-only source provenance survives; predictive raw/source features remain blocked. |
| `G12-FIND-007` | Medium | CD2-05 correctly dedupes G5/G7 attention rows, but source path mismatch, stale calendar state, Fed parser absence, and non-validation-safe attention proxies block a master row. | Blocked proposal; future canonical row only. |
| `G12-FIND-008` | Medium | Old G6 label-class normalization residue is master-contained but still a hygiene risk if agents consume lane files directly. | Future cleanup or master-only consumption required. |
| `G12-FIND-009` | Medium | Unregistered source placeholders and literature refs remain hard source-validity blockers. | Move to dependency/evidence fields later; no source validation flip. |

## CD2 Review Table

| Assignment | G12 outcome | Rationale |
|---|---|---|
| `CD2-01` | `BLOCKED_SOURCE_FRESHNESS_ASOF` | Source freshness rules are correct, but COT/FRED/BIS/Cboe/VRP parser/cache/as-of blockers are not cleared. |
| `CD2-02` | `SURVIVES_RESEARCH_ONLY_OUTCOME_CLOSED` | Accepted prereg is lifecycle-only and label-separated; source and lifecycle blockers remain. |
| `CD2-03` | `SURVIVES_RESEARCH_ONLY_OUTCOME_CLOSED_WITH_LEDGER_NAMING_BLOCKER` | Offline RL row blocks live behavior and label mixing; future scoring needs label-specific risk-bank ledger fields. |
| `CD2-04` | `STATUS_ONLY_SOURCE_PROVENANCE_SURVIVES_RAW_FEATURES_BLOCKED` | K55 can receive source-status/provenance flags only; raw OFI/depth and validation-safe claims stay quarantined. |
| `CD2-05` | `BLOCKED_DUPLICATE_AND_SOURCE_PATH_CLEANUP` | Proposal resolves duplicates conceptually but lacks source-safe calendar/Fed/attention evidence and a machine row. |
| `CD2-06` | `STATUS_ONLY_CAPTURE_SPEC_SURVIVES_ANALYSIS_BLOCKED` | Capture spec is useful; current data lacks required fields for path/fill-quality analysis. |
| `CD2-07` | `BLOCKED_SIDECAR_ONLY_NOT_MASTER_REGISTERED` | Sidecar uses non-master hypothesis ID and source/as-of blockers remain. |
| `CD2-08` | `ACCEPT_AS_FUTURE_CLEANUP_GUIDANCE_NO_MASTER_EDIT_NOW` | Cleanup proposal is the right direction, but G12 makes no registry edit. |

## Required Output Map

| Required G12 stop output | Artifact |
|---|---|
| Red-team review | This file |
| Red-team context and ambiguity ledger | `research/science_program_2026_05/01_domain_syntheses/G12_RED_TEAM_CONTEXT_AMBIGUITY_LEDGER_2026-05-06.md` |
| Leakage ledger | `research/science_program_2026_05/05_synthesis/G12_LEAKAGE_LEDGER_2026-05-06.md` |
| Duplicate-counting review | `research/science_program_2026_05/05_synthesis/G12_DUPLICATE_COUNTING_REVIEW_2026-05-06.md` |
| Label-separation review | `research/science_program_2026_05/05_synthesis/G12_LABEL_SEPARATION_REVIEW_2026-05-06.md` |
| Source-validity review | `research/science_program_2026_05/05_synthesis/G12_SOURCE_VALIDITY_REVIEW_2026-05-06.md` |
| Survivor/blocker decisions | `research/science_program_2026_05/05_synthesis/G12_SURVIVOR_BLOCKER_DECISIONS_2026-05-06.md` and `.json` |

## Non-Actions

- No master registry was edited.
- No source was marked `validation_safe=true`.
- No outcome review was opened.
- No survivor backlog row was added.
- No live trading prompt, risk, execution, permissions, safety-gate, selector, MT5, canary, paid-data, credential, remote, or order-behavior file was touched.
- No AI, MT5, canary, paid-data, order, or remote call was made.

## NO_PROMOTION_VERDICT

G12 is complete as a methodology red-team artifact lane only. Nothing in this review authorizes promotion, validation, live behavior, source-safety, or outcome opening.
