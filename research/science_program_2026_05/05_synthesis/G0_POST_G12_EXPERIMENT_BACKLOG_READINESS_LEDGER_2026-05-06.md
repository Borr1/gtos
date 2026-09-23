# G0 Post-G12 Experiment And Backlog Readiness Ledger - 2026-05-06

**Lane:** `G0`  
**Status:** `G0_POST_G12_READINESS_LEDGER_COMPLETE_RESEARCH_CONTROL_ONLY`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Ledger Rule

Readiness in this ledger means "ready for a next research-control action", not validation readiness, promotion readiness, or live readiness. No row enters the survivor backlog unless separate evidence proves it belongs there. Current survivor backlog remains `0`.

## Registry Readiness Summary

| Surface | Count | Readiness verdict |
| --- | ---: | --- |
| Master experiment preregs | `97` | Inventory only; all outcomes closed. |
| Accepted CD2 preregs | `2` | Research-control rows only. |
| Outcome-open preregs | `0` | No outcome review opened. |
| Validation-safe sources | `0` | No source cleared. |
| Survivor backlog rows | `0` | No survivor backlog. |
| CD2 blocked/status-only assignments | `6` | Explicit next-action map required. |

## Experiment Readiness

| Assignment | Experiment or artifact | Current status | Readiness class | Next research action |
| --- | --- | --- | --- | --- |
| `CD2-01` | Macro/vol source freshness proposal | `BLOCKED_SOURCE_FRESHNESS_ASOF` | `BLOCKED_SOURCE_CONTRACT_DOSSIER_REQUIRED` | Build parser/cache/hash/publication/vintage/no-lookahead tests for COT, FRED, BIS, Cboe, and VRP before any outcome review. |
| `CD2-02` | `EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001` | `SURVIVES_RESEARCH_ONLY_OUTCOME_CLOSED` | `READY_FOR_BLOCKER_CLEARING_ONLY` | Keep outcome closed while proving Cboe publication timing, lifecycle ordering, source hashes, duplicate controls, and label separation. |
| `CD2-03` | `EXP-G9-CD2-03-OFFLINE-RL-RISKBANK-001` | `SURVIVES_RESEARCH_ONLY_OUTCOME_CLOSED_WITH_LEDGER_NAMING_BLOCKER` | `READY_FOR_CONTRACT_RENAME_AND_TESTS_ONLY` | Rename risk-bank ledgers by label lane, freeze behavior policy, enforce duplicate episode IDs, cost model, same-bar handling, and G1 gates. |
| `CD2-04` | K55/orderflow provenance contract | `STATUS_ONLY_SOURCE_PROVENANCE_SURVIVES_RAW_FEATURES_BLOCKED` | `STATUS_METADATA_ONLY` | Keep K55 source-status/provenance flags as audit metadata unless as-of feature contracts and no-leak tests exist. |
| `CD2-05` | Macro/behavioral attention proposal | `BLOCKED_DUPLICATE_AND_SOURCE_PATH_CLEANUP` | `BLOCKED_CANONICAL_ROW_AND_SOURCE_CLEANUP_REQUIRED` | Produce canonical machine-readable row, local calendar path cleanup, stale-calendar cache, Fed parser, G5 source contract, and event-cluster effective-N. |
| `CD2-06` | Prefill/path capture spec | `STATUS_ONLY_CAPTURE_SPEC_SURVIVES_ANALYSIS_BLOCKED` | `CAPTURE_SPEC_READY_ANALYSIS_BLOCKED` | Add source hash/symbol, entry/SL/TP packet, ordered prefill candles or ticks, broker-native pending fields, spread/tick, trade IDs, and broker actual-R/cost floors. |
| `CD2-07` | Opportunity-cost sidecar | `BLOCKED_SIDECAR_ONLY_NOT_MASTER_REGISTERED` | `BLOCKED_MASTER_ID_AND_SOURCE_ASOF_REQUIRED` | Create canonical master hypothesis ID, prop parser completeness, risk/correlation as-of snapshots, stress source proof, and no-R/no-value label boundary. |
| `CD2-08` | Source/no-leak cleanup proposal | `ACCEPT_AS_FUTURE_CLEANUP_GUIDANCE_NO_MASTER_EDIT_NOW` | `READY_FOR_CONTROLLED_CLEANUP_PASS_ONLY` | Run a later G0/G12-controlled cleanup moving forbidden fields and placeholders without changing source or outcome flags. |

## Backlog Readiness

| Backlog bucket | Count | Status |
| --- | ---: | --- |
| Survivor backlog | `0` | Remains empty. G12 found no survivor row to add. |
| Outcome-opening backlog | `0` | No prereg can open outcomes yet. |
| Source-validation backlog | `0` | No source can be flipped validation-safe from this program. Future source-specific dossiers may be created separately. |
| Cleanup/control backlog | `8` | CD2-01 through CD2-08 all have next research-control actions, but none are promotions. |

## NO_PROMOTION_VERDICT

This readiness ledger is an action map for future research-control work only. It opens no outcomes, validates no sources, promotes no rows, and adds no survivor backlog.
