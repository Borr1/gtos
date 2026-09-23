# G12 Survivor And Blocker Decisions - 2026-05-06

**Lane:** `G12`  
**Status:** `G12_RED_TEAM_DECISIONS_COMPLETE_RESEARCH_ONLY`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Decision Rule

`SURVIVES` in this file means a row survives G12 red-team review as a research-control artifact only. It does not mean validation-safe, promotion-safe, source-safe, outcome-opened, survivor-backlog, or live-ready.

## CD2 Decisions

| Assignment | Row or artifact | G12 decision | Required next evidence |
|---|---|---|---|
| `CD2-01` | G7 macro-vol-source freshness proposal | `BLOCKED_SOURCE_FRESHNESS_ASOF` | Source-specific parser/cache/hash/publication/vintage/no-lookahead tests for COT, FRED, BIS, Cboe, and VRP. |
| `CD2-02` | `EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001` | `SURVIVES_RESEARCH_ONLY_OUTCOME_CLOSED` | Cboe publication-as-of proof, lifecycle ordering fields, source hashes, duplicate tests, and label-separation implementation checks. |
| `CD2-03` | `EXP-G9-CD2-03-OFFLINE-RL-RISKBANK-001` | `SURVIVES_RESEARCH_ONLY_OUTCOME_CLOSED_WITH_LEDGER_NAMING_BLOCKER` | Label-lane-specific risk-bank ledger fields, behavior policy freeze, duplicate episode IDs, cost model, same-bar handling, sample floors, and G1 statistics gates. |
| `CD2-04` | G4 K55/orderflow provenance contract | `STATUS_ONLY_SOURCE_PROVENANCE_SURVIVES_RAW_FEATURES_BLOCKED` | K55 metadata-vs-feature separation, source-status as-of tests, no raw OFI/depth predictive fields, no validation-safe source flip. |
| `CD2-05` | G5/G7 macro-attention proposal | `BLOCKED_DUPLICATE_AND_SOURCE_PATH_CLEANUP` | Canonical machine-readable hypothesis/prereg, local calendar path cleanup, stale-calendar cache, Fed parser, G5 attention source contract, event-cluster effective-N. |
| `CD2-06` | G10 prefill/path capture spec and audit | `STATUS_ONLY_CAPTURE_SPEC_SURVIVES_ANALYSIS_BLOCKED` | Source hash/symbol, entry/SL/TP packet or deterministic pointer, ordered prefill candles/ticks, pending/native fields, spread/tick, trade IDs, broker actual-R/cost floors. |
| `CD2-07` | G11 opportunity-cost sidecar | `BLOCKED_SIDECAR_ONLY_NOT_MASTER_REGISTERED` | Master hypothesis ID, prop parser completeness, risk/correlation as-of snapshots, stress source as-of proof, and strict no-R/no-value label boundary. |
| `CD2-08` | G0 source/no-leak cleanup proposal | `ACCEPT_AS_FUTURE_CLEANUP_GUIDANCE_NO_MASTER_EDIT_NOW` | G0/G12-controlled schema cleanup pass that moves forbidden fields and placeholders without changing validation-safe or outcome-review flags. |

## Standing Wave-2 Decisions

| Topic | G12 decision | Exact future correction |
|---|---|---|
| G11 no-leak semantic inversion | `HARD_BLOCKER_FOR_OUTCOME_OPENING_AND_PROMOTION` | Replace forbidden outcome/future names in 8 G11 `no_leak_fields` lists with as-of feature whitelists; move forbidden names to blockers/test-method text. |
| Unregistered source placeholders | `HARD_BLOCKER_FOR_SOURCE_VALIDITY` | Move hypothesis IDs to `neighbor_lane_dependency`, future placeholders to `blocked_dependency_refs`, and `LIT-G5-*` to `evidence_refs` or `SRC-G5-ACADEMIC-LIT-001` context-only source. |
| Broker actual-R scarcity | `HARD_BLOCKER_FOR_ACTUAL_R_CLAIMS` | Keep broker actual-R separate until sufficient account-history realized rows with fill/cost linkage exist under a separate prereg. |
| Macro/vol publication leakage | `HARD_BLOCKER_FOR_SOURCE_FEATURE_USE` | Require release/as-of, cache, parser, vintage/revision, and same-day daily-row rules before joining to candidates. |
| Execution/path label separation | `HARD_BLOCKER_FOR_ANALYSIS_AND_PROMOTION` | Separate decision packets, ordered path labels, lifecycle labels, execution/friction labels, synthetic path-R, and broker actual-R. |
| Old G6 normalization residue | `SCHEMA_HYGIENE_BLOCKER_FOR_DIRECT_LANE_ROW_CONSUMPTION` | Either patch G6 lane artifacts later or require downstream consumers to use the G0 master-normalized rows plus normalization ledger. |
| Global `validation_safe=false` boundary | `PRESERVE_GLOBAL_BLOCKER` | No `validation_safe=true` change without a source-specific blocker-clearing dossier. |

## Final Decision

No CD2 row is promotable. No source is validation-safe. No outcome review is opened. No survivor backlog row exists. The only G12 survivors are the two accepted CD2 preregs as outcome-closed research-control rows plus selected status/spec/proposal artifacts as future-cleanup guidance.

## NO_PROMOTION_VERDICT

G12 makes no live trading, risk, execution, prompt, selector, safety-gate, MT5, canary, paid-data, credential, remote, order-behavior, source-validation, or promotion change.
