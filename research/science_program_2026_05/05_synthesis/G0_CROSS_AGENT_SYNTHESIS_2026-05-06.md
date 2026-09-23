# G0 CD2 Cross-Agent Synthesis - 2026-05-06

**Lane:** `G0`
**Status:** `G0_CD2_RECONCILIATION_COMPLETE_VERIFIED_PENDING_SCOPED_COMMIT`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Checked at UTC:** `2026-05-06T11:29:13Z`
**HEAD reconciled:** `4db7f47a`
**CD2 merge commit:** `0e865798`

## Objective Restated

Run G0 CD2 cross-domain reconciliation: read HEAD `4db7f47a`, merged CD2 artifacts, wave-2 reconciliation, master registries, assignment file, G12 guidance, and research current state; reconcile CD2-01 through CD2-08 without promotion; update master/status/source/synthesis artifacts; preserve source and label blockers; and prepare G12 launch instructions.

## Registry Outcome

| Registry | Rows | CD2 delta | Status |
| --- | ---: | ---: | --- |
| Mechanism | 77 | 0 | unchanged research inventory |
| Hypothesis | 96 | 0 | unchanged research inventory |
| Experiment prereg | 97 | 2 | schema-safe CD2 rows added, outcomes closed |
| Source contract | 86 | 0 | all validation_safe=false |
| Survivor backlog | 0 | 0 | empty |

## CD2 Decisions

| Assignment | Decision | G12 focus |
| --- | --- | --- |
| `CD2-01` | `BLOCKER_ONLY_PROPOSAL_UPDATES_EXISTING_ROWS` | Verify publication/as-of rules before any macro-vol outcome review. |
| `CD2-02` | `REGISTER_SCHEMA_SAFE_PREREG_RESEARCH_ONLY` | Review Cboe same-day timing, pending lifecycle ordering, and lifecycle_no_fill label separation. |
| `CD2-03` | `REGISTER_SCHEMA_SAFE_PREREG_RESEARCH_ONLY` | Adversarially test state-field leakage, risk-bank invariant, duplicate episode counting, and cost accounting. |
| `CD2-04` | `STATUS_SYNTHESIS_ONLY` | Confirm K55 receives only source-status/provenance flags, not raw orderflow/depth predictive features. |
| `CD2-05` | `BLOCKER_ONLY_MARKDOWN_PROPOSAL` | Resolve duplicate G5/G7 attention rows and calendar/Fed source freshness before a machine row exists. |
| `CD2-06` | `STATUS_SYNTHESIS_ONLY` | Verify prefill/no-fill, synthetic path-R, same-bar ambiguity, and broker actual-R lanes cannot mix. |
| `CD2-07` | `BLOCKER_ONLY_SIDECAR_PREREG` | Keep observation-only opportunity-cost context separate from risk/correlation/order behavior and R labels. |
| `CD2-08` | `BLOCKER_ONLY_G12_CLEANUP_PROPOSAL` | Resolve no_leak semantic inversion and source_ids placeholders without marking sources validation-safe. |

## Validation Findings

- Schema-safe CD2 preregs registered: `2`.
- CD2 source contracts promoted: `0`.
- Source contracts with `validation_safe=true`: `0`.
- Outcome reviews opened: `0`.
- Survivor backlog rows: `0`.
- Existing no-leak/source-reference blockers remain assigned to G12.

## Final G12 Launch

Launch G12 only as red-team review. It must start from `G0_CD2_RECONCILIATION_2026-05-06.md/json`, then inspect the master registries and each CD2 artifact. Its output should decide whether the two registered CD2 preregs stay schema-safe, whether blocked proposal rows need cleanup, and whether any source/no-leak/label text creates promotion drift. It must not modify live trading surfaces.

## NO_PROMOTION_VERDICT

CD2 reconciliation is research governance only. It is not a validation result, promotion dossier, live selector, risk change, execution change, or source approval.
