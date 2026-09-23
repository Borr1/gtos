# G0 Wave-2 Cross-Agent Synthesis - 2026-05-06

**Lane:** `G0`
**Status:** `G0_WAVE2_RECONCILIATION_COMPLETE_COMMITTED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Checked at UTC:** `2026-05-06T08:53:27Z`
**HEAD reconciled:** `7a95a293`
**Wave-2 merge commit:** `a5714d04`
**Primary reconciliation commit:** `20e84c43`

## Objective Restated

Run G0 wave-2 reconciliation for the primitive-science program: read merged G7-G11 outputs now visible at HEAD `7a95a293`, merge them with the existing G1-G6 master rows, validate mechanism/hypothesis/source/prereg/status rows, update master registries/status/synthesis, identify duplicate/source/prereg/no-leak blockers, preserve `NO_PROMOTION_VERDICT`, create cross-domain second-pass assignments, and prepare G12 red-team shortlist and prompt guidance without touching live-trading surfaces.

## Registry Outcome

| Registry | Rows | Status |
| --- | ---: | --- |
| Mechanism | 77 | `MERGED_RESEARCH_ONLY` |
| Hypothesis | 96 | `MERGED_RESEARCH_ONLY` |
| Experiment prereg | 95 | `MERGED_OUTCOMES_CLOSED` |
| Source contract | 86 | `RECONCILED_NOT_VALIDATION_SAFE` |
| Survivor backlog | 0 | `EMPTY_NO_PROMOTION` |

## Validation Findings

- Required-field checks passed for G1-G11 rows after G0 reconciliation, apart from the already-recorded G6 label-class master-copy normalizations.
- Hypothesis-to-mechanism and prereg-to-hypothesis relationships passed.
- Duplicate row-ID checks found no duplicate mechanism, hypothesis, experiment, or source IDs.
- All experiment preregs keep `outcome_review_opened=false`.
- All source contracts keep `validation_safe=false`.
- G0 recorded `8` no-leak semantic blockers, primarily G11 rows that list outcome/future field names under `no_leak_fields`.
- G0 recorded `18` source-reference placeholders or literature references that are not source_contract_v2 rows.

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

### G7

Rows: `7` mechanisms, `12` hypotheses, `12` preregs, `9` sources. Effective commit: `ef3eb3a0`.

- No G7 source contract is validation-safe.
- FRED/rates official refresh failed during this pass and no validation-ready normalized cache was visible in the working tree.
- Direct gold COT predictor route remains killed by local evidence; FX COT mapping remains blocked.
- DXY remains soft context only; no validation-safe official DXY/broad-dollar parser/cache exists.
- LBMA fix pages provide timing context only; no legal auction imbalance/order-flow source exists.
- BIS/WGC sources need exact table/series selection, release/vintage rules, parser/cache, and no-lookahead tests.
- G8 and G11 had no committed lane outputs at this HEAD, so cross-domain rows are blocked placeholders.
- No live prompts, risk, execution, permissions, selectors, MT5 behavior, canaries, or paid-data access may be changed by this lane.

### G8

Rows: `7` mechanisms, `7` hypotheses, `7` preregs, `8` sources. Effective commit: `ca037ca8`.

- Official historical aggregate GEX remains blocked by paid/license/source-contract requirements.
- FlashAlpha Basic GEX is forward-context/proxy only and not validation-safe.
- Cboe volatility-index CSVs were discovered and cached, but parser, publication timestamp, license, and no-lookahead join tests are missing.
- VRP formula is preregistered only; implied-variance source and realized-variance estimator must be frozen before any outcome review.
- OPEX calendar features already exist locally, but calendar-only pressure cannot validate gamma/pinning without point-in-time open-interest/gamma source.

### G9

Rows: `8` mechanisms, `10` hypotheses, `10` preregs, `8` sources. Effective commit: `1423a7e7`.

- K55 production model artifact is missing; inference remains disabled until a matching target/feature/no-leak artifact exists.
- Current K55 rows are synthetic_path_context_only and cannot validate promotion.
- Component 3B, tool grounding, and Reflexion are owner-parked and require explicit approval plus budget cap before AI/API calls or wiring.
- G10 neighbor lane has no committed synthesis output yet, so offline-RL sizing/exit rows are future-neighbor dependent.
- All G9 source contracts remain validation_safe=false and source/budget cap remains $0.

### G10

Rows: `7` mechanisms, `8` hypotheses, `8` preregs, `7` sources. Effective commit: `9116ceed`.

- No source contract in G10 is validation_safe=true.
- Broker actual-R evidence is too sparse for execution or exit promotion.
- Close-side slippage/cost evidence is missing in current audit coverage.
- Historical path replay lacks original POI bounds and broker lifecycle state.
- redacted_account official page cache needs a parser and complete program-rule mapping.
- G9 neighbor synthesis was absent, blocking a full AI/ML neighbor pass.
- Live trading prompt, risk, execution, permissions, safety, selector, MT5, canary, and paid-data surfaces were not touched.

### G11

Rows: `7` mechanisms, `8` hypotheses, `8` preregs, `9` sources. Effective commit: `7264cd0c`.

- All G11 source contracts are validation_safe=false
- No paid source access authorized or used
- No outcome labels opened
- G7/G8 completed lane outputs were not present at HEAD 42bf621c
- Databento public captures are JavaScript shells and cannot support schema claims
- Source-transfer, release-aware joins, and friction manifests are future experiments only

## Cross-Domain Second Pass

G0 created `8` second-pass assignments in `G0_CROSS_DOMAIN_SECOND_PASS_ASSIGNMENTS_2026-05-06.md`. They are lane-handoff prompts only, not promotions.

## G12 Red-Team Shortlist

G0 created `7` red-team topics in `G12_RED_TEAM_SHORTLIST_AND_PROMPT_GUIDANCE_2026-05-06.md`. G12 should focus on no-leak semantics, source validity, source-reference placeholders, label separation, duplicate counting, prereg closure, and promotion drift.

## Forbidden-Surface Boundary

G0 did not change live trading prompts, risk, execution, permissions, safety gates, selectors, MT5, canaries, paid data, or order behavior. Final forbidden-surface diff verification is recorded in the completion audit.

## NO_PROMOTION_VERDICT

Wave-2 reconciliation creates an organized research backlog and red-team/source-blocker map. It is not a promotion, validation result, live selector, risk change, or execution change.
