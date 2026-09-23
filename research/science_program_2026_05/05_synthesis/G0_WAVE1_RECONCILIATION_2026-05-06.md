# G0 Wave-1 Cross-Agent Synthesis - 2026-05-06

**Lane:** `G0`
**Status:** `G0_WAVE1_RECONCILIATION_COMPLETE_COMMITTED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Checked at UTC:** `2026-05-06T07:43:59Z`
**Main HEAD reconciled:** `08ffc24b`
**Primary reconciliation commit:** `df29b36c`

## Objective Restated

Run G0 wave-1 reconciliation for the primitive-science program: read merged G1-G6 outputs, validate mechanism/hypothesis/source/prereg/status rows, update master registries/status/synthesis, identify missing artifacts and duplicate/killed/leakage/source blockers, preserve `NO_PROMOTION_VERDICT`, and avoid all live-trading surfaces.

## Registry Outcome

| Registry | Rows | Status |
| --- | ---: | --- |
| Mechanism | 41 | `MERGED_RESEARCH_ONLY` |
| Hypothesis | 51 | `MERGED_RESEARCH_ONLY` |
| Experiment prereg | 50 | `MERGED_OUTCOMES_CLOSED` |
| Source contract | 45 | `RECONCILED_NOT_VALIDATION_SAFE` |
| Survivor backlog | 0 | `EMPTY_NO_PROMOTION` |

## Validation Findings

- Required-field checks passed for G1-G6 rows after G0 reconciliation.
- Hypothesis-to-mechanism and prereg-to-hypothesis relationships passed.
- Duplicate row-ID checks found no duplicate mechanism, hypothesis, experiment, or source IDs.
- All experiment preregs keep `outcome_review_opened=false`.
- All source contracts keep `validation_safe=false`.
- Four G6 hypothesis rows used verbose label classes; G0 normalized the master copies to schema enums and recorded each repair in the JSON audit.

## Lane Blockers

### G1

Rows: `6` mechanisms, `6` hypotheses, `6` preregs, `10` sources. Effective commit: `649ead84`.

- No outcome review was opened; all prereg rows keep outcome_review_opened=false.
- All source contracts remain validation_safe=false.
- Public references are methodology/context evidence only, not decision-time market data.
- SSRN/OUP blocked pages were cached as Cloudflare challenge HTML; no bypass or paid access was attempted.
- Neighbor G2/G9/G10 artifacts were unavailable at inspection time, so no neighbor-derived hypotheses were added.
- Master registry reconciliation remains a future G0/control-lane task.

### G2

Rows: `7` mechanisms, `7` hypotheses, `7` preregs, `6` sources. Effective commit: `fe08479f`.

- Neighbor lanes G1, G3, and G10 have no committed lane rows to merge.
- Pure volatility clustering direct OB route is killed; GARCH use is limited to lifecycle/ambiguity context.
- Broad portfolio vol-managed sizing is rejected failed; risk-policy replacements remain deferred and owner-approval blocked.
- Sticky-HDP-HMM replacement is deferred; HMM/dwell features are context-only.
- Hawkes/jump intensity is source-blocked until mature tick/depth/signed-orderflow source exists.
- Broker actual-R rows remain sparse for current lifecycle/V2b rows; no validation or promotion claim.

### G3

Rows: `7` mechanisms, `8` hypotheses, `8` preregs, `8` sources. Effective commit: `f0e0c8c9`.

- All source_contract_v2 rows remain validation_safe=false.
- External cash cap is $0 and no paid source approval exists.
- No outcome review has been opened.
- Neighbor lanes G2/G4/G6 had no committed survivor outputs beyond scaffold at this pass.
- Any future validation requires independent split, duplicate lifecycle controls, no-leak feature generation, DSR/PBO/effective-N, and source-contract tests.

### G4

Rows: `8` mechanisms, `14` hypotheses, `13` preregs, `7` sources. Effective commit: `00621862`.

- Databento live GLBX.MDP3 license remains blocked for live NAS100 collection.
- NAS100 broker actual-R and MBP10 candidate floors are not met.
- Sierra `.scid` stacked imbalance, VAH, and VAL are source-definition blocked.
- USDJPY/6J transfer remains review-open; GBPJPY direct orderflow proxy remains blocked.
- LBMA/ICE and Nasdaq auction imbalance data require licensed/source-contracted as-of feeds before use.
- No source contract is validation-safe under the current G0 source/budget ledger.

### G5

Rows: `6` mechanisms, `9` hypotheses, `9` preregs, `7` sources. Effective commit: `7dfc0c59`.

- No validation-safe Google Trends, retail-flow-share, broker sentiment, social-flow, or direct counterparty stop-placement source exists in lane.
- OANDA/IG-like broker sentiment/order-book data requires legal/API/historical-capture review before use.
- CFTC COT is weekly and delayed; it can only be context-only until release-lag and contract mapping are implemented.
- Local news calendar is operator maintained and stale-source risk blocks event-cohort validation.
- Prompt-neutral AI rerun requires paid API budget approval and must not alter the live prompt.
- G4/G6/G7 had no committed lane outputs at this pass; cross-domain rows are candidate-only dependencies.

### G6

Rows: `7` mechanisms, `7` hypotheses, `7` preregs, `7` sources. Effective commit: `9344cda5`.

- No G3/G5/G10 neighbor outputs available for cross-domain import
- Continuation/no-retrace exact decision entry price and ordered M1/tick path missing
- No unseen validation cohort for OB versus generic retrace comparator
- Source budget cap remains $0 and no paid/vendor data was used
- All findings are research-only and not promotion-safe

## Missing Artifacts And Packaging Gaps

- `G2`: No standalone 00_control goal-status JSON; status row is embedded in G2_STOCHASTIC_TAILS_SYNTHESIS_2026-05-06.json. Blocking master merge: `False`.
- `G2`: No standalone mechanism/hypothesis/prereg/source JSON files; all rows are embedded in the synthesis JSON. Blocking master merge: `False`.
- `G3`: No dedicated completion-audit artifact found; prompt done-standard evidence is in synthesis/status rows. Blocking master merge: `False`.
- `G4`: Mechanism/hypothesis/prereg/source files are bare JSON lists rather than schema wrapper objects. Blocking master merge: `False`.
- `G5`: Lane-owned status row still has commit_sha null; G0 status registry reconciles effective commit from git log. Blocking master merge: `False`.
- `G6`: No standalone 00_control goal-status JSON; status row is embedded in G6_MOMENTUM_REVERSION_ROWS_2026-05-06.json. Blocking master merge: `False`.
- `G6`: Four lane hypothesis label_class values use verbose non-enum wording; G0 master copy normalizes them and records the repair. Blocking master merge: `False`.
- `G9`: G0 controlling prompt names G9 for neighbor pass, but G9 is not part of wave 1 and has no lane outputs yet. Blocking master merge: `True`.

## Forbidden-Surface Boundary

G0 did not change live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid data, or order behavior. Final forbidden-surface diff verification is recorded in the completion audit.

## NO_PROMOTION_VERDICT

Wave-1 reconciliation creates an organized research backlog and source-blocker map. It is not a promotion, validation result, live selector, risk change, or execution change.
