# Science Program Master Registry - 2026-05-06

**Status:** `G0_POST_G12_CLOSEOUT_HEAD_64135c3a`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Checked at UTC:** `2026-05-06T12:08:31Z`
**HEAD read:** `64135c3a`
**HEAD reconciled for CD2:** `4db7f47a`
**CD2 merge commit:** `0e865798`
**Wave-2 reconciliation commit:** `20e84c43`

## G0 Registry State

- Mechanisms: `77`
- Hypotheses: `96`
- Experiment preregs: `97`
- Source contracts: `86`
- CD2 preregs registered research-only: `2`
- Survivor backlog rows: `0`

G0 reconciled CD2-01 through CD2-08 artifacts at HEAD `4db7f47a`. Only two CD2 experiment prereg rows were schema-safe and explicitly research-only, so they were added to the experiment preregistry with outcomes closed. No mechanism, hypothesis, source-contract, survivor, validation, prompt, risk, execution, selector, MT5, canary, paid-data, or order-behavior row was promoted.

## CD2 Assignment Outcomes

| Assignment | Lane | Master action | Reason |
| --- | --- | --- | --- |
| `CD2-01` | `G7` | `BLOCKER_ONLY_PROPOSAL_UPDATES_EXISTING_ROWS` | Markdown proposal updates existing source/no-leak/prereg fields but leaves COT/FRED/BIS/Cboe/VRP as-of blockers unresolved. |
| `CD2-02` | `G8` | `REGISTER_SCHEMA_SAFE_PREREG_RESEARCH_ONLY` | Machine-readable experiment_prereg_v1 row is outcome-closed, label-separated, source-blocked, and references an existing hypothesis. |
| `CD2-03` | `G9` | `REGISTER_SCHEMA_SAFE_PREREG_RESEARCH_ONLY` | Proposed prereg has all experiment_prereg_v1 fields, keeps outcomes closed, references an existing hypothesis, and is explicitly offline-only. |
| `CD2-04` | `G4` | `STATUS_SYNTHESIS_ONLY` | Contract/join map is not a science_mechanism, hypothesis, prereg, or source_contract row; no source was validation-safe. |
| `CD2-05` | `G5` | `BLOCKER_ONLY_MARKDOWN_PROPOSAL` | Canonical hypothesis/prereg are markdown proposal-only, source path mismatch and stale-calendar blockers remain, and artifact explicitly says no master edit. |
| `CD2-06` | `G10` | `STATUS_SYNTHESIS_ONLY` | Spec and missing-field audit define capture requirements but create no schema row; source_hash, source_symbol, ordered prefill candles, tick summaries, and lifecycle state remain blocked. |
| `CD2-07` | `G11` | `BLOCKER_ONLY_SIDECAR_PREREG` | Sidecar row uses a new hypothesis ID that is not in the master hypothesis registry; prop parser, correlation lifecycle, and stress as-of blockers remain. |
| `CD2-08` | `G0` | `BLOCKER_ONLY_G12_CLEANUP_PROPOSAL` | Cleanup proposal intentionally edits no master rows; G12 must decide dependency/evidence fields and no_leak field cleanup. |

## Registered CD2 Preregs

| Experiment | Hypothesis | Source artifact |
| --- | --- | --- |
| `EXP-G8-CD2-02-SHORTVOL-LIFECYCLE-001` | `HYP-G8-VIX1D9D-STRESS-002` | `C:/tmp/gtosg/G0/research/science_program_2026_05/03_experiment_specs/G8_CD2_02_SHORT_VOL_EXECUTION_LIFECYCLE_PREREG_2026-05-06.json` |
| `EXP-G9-CD2-03-OFFLINE-RL-RISKBANK-001` | `HYP-G9-OFFLINE-RL-POLICY-009` | `C:/tmp/gtosg/G0/research/science_program_2026_05/05_synthesis/G9_CD2_03_RED_TEAM_PREREG_PROPOSAL_2026-05-06.json` |

## Check Results

- Required-field hard issues: `0` hard blockers in accepted/master rows.
- Duplicate mechanism/hypothesis/prereg/source IDs: `0`.
- Source contracts with `validation_safe=true`: `0`.
- Experiment preregs with `outcome_review_opened=true`: `0`.
- No-leak semantic blockers retained for G12: `8`.
- Source-reference placeholders/literature references retained for G12: `18`.

## Survivor Backlog

No survivor hypotheses exist. CD2 improved research-control contracts only.

## Post-G12 Closeout

G12 red-team review is reconciled by `G0_POST_G12_CLOSEOUT_SYNTHESIS_2026-05-06.md/json`. The final program state remains unchanged in row counts: `77` mechanisms, `96` hypotheses, `97` experiment preregs, `86` source contracts, and `0` survivor-backlog rows. G12 accepted only the two CD2 preregs as outcome-closed research-control rows and cleared no source, opened no outcome review, and added no survivor backlog row. All standing wave-2/CD2 blockers remain enforced.

## NO_PROMOTION_VERDICT

This master registry remains research/control inventory only. It does not change live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid data, credentials, remote pushes, or order behavior.
