# G0 Post-G12 Source And No-Leak Cleanup Assignments - 2026-05-06

**Lane:** `G0`  
**Status:** `G0_POST_G12_CLEANUP_ASSIGNMENTS_COMPLETE_RESEARCH_CONTROL_ONLY`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Assignment Rule

These are cleanup assignments for a future controlled pass. They do not edit master rows now, do not mark sources validation-safe, do not open outcomes, and do not create survivor backlog.

## G11 No-Leak Cleanup

| Row | Current issue | Future assignment |
| --- | --- | --- |
| `HYP-G11-PROVENANCE-GATE-001` | `no_leak_fields` lists outcome/trade-result names. | Replace with source provenance/as-of whitelist fields; move forbidden names to blockers/test-method text. |
| `HYP-G11-COVERAGE-GATE-002` | Lists actual-R, trade outcome, future return, and post-signal continuation names. | Replace with coverage-manifest/as-of fields and no outcome labels. |
| `HYP-G11-SOURCE-TRANSFER-003` | Lists actual-R, TP/SL hit, and post-entry path fields. | Replace with source-transfer alignment, missingness, lead-lag, rollover, and proxy-state fields. |
| `HYP-G11-PUBLIC-LAG-004` | Lists post-release revision, future release, and outcome fields. | Replace with release/vintage/cache/decision timestamp and stale-source fields. |
| `HYP-G11-OPTIONS-VOL-005` | Lists future vol and outcome fields. | Replace with vol source publication/cache/license/history/as-of fields. |
| `HYP-G11-OBSERVER-EXPANSION-006` | Lists actual-R, win/loss, post-signal path, and TP/SL names. | Replace with observer enabled/source freshness/friction/session eligibility fields. |
| `HYP-G11-FRICTION-GATE-007` | Lists future return, actual-R, post-entry path, and trade result. | Replace with predecision friction manifest, spread/ATR, tick value, contract spec, and version fields. |
| `HYP-G11G4-SOURCE-GATED-ORDERFLOW-008` | Lists actual-R, trade result, post path, and future orderflow. | Replace with source contract, provenance, proxy-transfer, label-separation, budget/license state, and review timestamp fields. |

## Source Reference Cleanup

| Row family | Current issue | Future assignment |
| --- | --- | --- |
| `HYP-G7-XG5-MACRO-ATTN-010` | `source_ids` contains `HYP-G5-XG7-MACRO-ATTN-009`. | Keep only concrete G7/G5 source IDs in `source_ids`; move the hypothesis ID to `neighbor_lane_dependency`. |
| `HYP-G7-XG8-VOL-MACRO-011` | `source_ids` contains `future_G8_options_vol_rows`. | Replace with concrete G8 source IDs only after source rows exist; move future placeholder to `blocked_dependency_refs`. |
| `HYP-G7-XG11-SOURCE-FRESH-012` | `source_ids` contains `future_G11_source_governance_rows`. | Replace with concrete G11 source IDs; move future placeholder to dependency/blocker field. |
| G5 mechanisms/hypotheses with `LIT-G5-*` | Literature refs are not `source_contract_v2` rows. | Move individual `LIT-G5-*` refs to `evidence_refs`; use `SRC-G5-ACADEMIC-LIT-001` only as context-only source-contract evidence if needed. |
| G6 lane artifacts | Four lane label-class values remain verbose/non-enum. | Patch lane artifacts in a future hygiene pass or require master-normalized rows for all downstream consumption. |

## Cleanup Guardrails

- Keep `validation_safe=false` for all source contracts unless a separate source-specific dossier clears the blocker.
- Keep all preregs `outcome_review_opened=false`.
- Keep survivor backlog at `0`.
- Do not add predictive raw orderflow/depth fields from CD2-04.
- Do not use source-status/floor flags as per-row predictive features unless timestamp-safe and excluded from outcome coverage leakage.
- Do not turn opportunity-cost, lifecycle, or source-status rows into R/PnL labels.

## NO_PROMOTION_VERDICT

This assignment list is cleanup guidance only. It is not a registry edit, source-validation dossier, outcome-opening request, or promotion artifact.
