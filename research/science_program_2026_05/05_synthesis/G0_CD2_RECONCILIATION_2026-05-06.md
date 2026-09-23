# G0 CD2 Reconciliation - 2026-05-06

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Checked at UTC:** `2026-05-06T11:29:13Z`
**HEAD reconciled:** `4db7f47a`
**CD2 merge commit:** `0e865798`

## Concrete Deliverables

- Mandatory GTOS preflight completed.
- HEAD `4db7f47a`, CD2 artifacts, wave-2 reconciliation, master registries, assignment file, G12 guidance, and research current state read.
- CD2-01 through CD2-08 artifacts reconciled.
- Master experiment preregistry updated only for schema-safe research-only rows.
- Source registry refreshed with zero source promotions.
- Status registry, synthesis, completion audit, and G12 launch instructions refreshed.
- Schema, relationship, duplicate, source, prereg, no-leak, no-promotion, and label-separation checks recorded.

## Accepted Rows

| Assignment | Experiment | Reason |
| --- | --- | --- |
| `CD2-02` | `EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001` | schema-safe, outcome closed, research-only, existing hypothesis |
| `CD2-03` | `EXP-G9-CD2-03-OFFLINE-RL-RISKBANK-001` | schema-safe, outcome closed, research-only, existing hypothesis |

## Blocked Or Status-Only Rows

| Assignment | Master action | Blocker |
| --- | --- | --- |
| `CD2-01` | `BLOCKER_ONLY_PROPOSAL_UPDATES_EXISTING_ROWS` | Markdown proposal updates existing source/no-leak/prereg fields but leaves COT/FRED/BIS/Cboe/VRP as-of blockers unresolved. |
| `CD2-04` | `STATUS_SYNTHESIS_ONLY` | Contract/join map is not a science_mechanism, hypothesis, prereg, or source_contract row; no source was validation-safe. |
| `CD2-05` | `BLOCKER_ONLY_MARKDOWN_PROPOSAL` | Canonical hypothesis/prereg are markdown proposal-only, source path mismatch and stale-calendar blockers remain, and artifact explicitly says no master edit. |
| `CD2-06` | `STATUS_SYNTHESIS_ONLY` | Spec and missing-field audit define capture requirements but create no schema row; source_hash, source_symbol, ordered prefill candles, tick summaries, and lifecycle state remain blocked. |
| `CD2-07` | `BLOCKER_ONLY_SIDECAR_PREREG` | Sidecar row uses a new hypothesis ID that is not in the master hypothesis registry; prop parser, correlation lifecycle, and stress as-of blockers remain. |
| `CD2-08` | `BLOCKER_ONLY_G12_CLEANUP_PROPOSAL` | Cleanup proposal intentionally edits no master rows; G12 must decide dependency/evidence fields and no_leak field cleanup. |

## Required Checks

- Required-field/relationship/duplicate/source/prereg hard blocker count: `0`.
- Duplicate ID issues: `0`.
- Source `validation_safe=true` rows: `0`.
- Prereg `outcome_review_opened=true` rows: `0`.
- No-leak semantic blockers retained: `8`.
- Source-reference issues retained: `18`.

## Non-Actions

- No source was marked validation-safe.
- No outcome review was opened.
- No mechanism, hypothesis, source-contract, survivor, validation, risk, prompt, execution, selector, MT5, canary, paid-data, credential, remote, or order-behavior row was promoted.

## NO_PROMOTION_VERDICT

The reconciliation is complete for G0 governance scope, but G12 remains required before any cleanup or promotion discussion.
