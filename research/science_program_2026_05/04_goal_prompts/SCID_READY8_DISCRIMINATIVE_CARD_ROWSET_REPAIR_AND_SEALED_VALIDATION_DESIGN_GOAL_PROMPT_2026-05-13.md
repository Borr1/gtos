# SCID READY8 Discriminative Card Rowset Repair And Sealed Validation Design

Date: 2026-05-13

## Evidence Class

`SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN_ONLY`

This is a source-control repair/design route. It is not result scoring, not validation, not promotion, and not a live-trading change. The accepted READY8 numerical screen proved that the current target packet repeats the same `3,014` source candidates under all `8` READY8 cards, producing `24,112` card/candidate rows and `192,896` target rows across horizons `1/4/16/32` and two neutral target families. Your job is to repair/design the next card-discriminative rowset and the sealed-validation prerequisites so a future card-level comparison can become meaningful.

Do not treat "cards are redundant" as a dead end. Treat it as the exact design failure to repair.

## Mandatory Preflight And Context Use

Run and read:

1. `python scripts/generate_live_state.py`
2. `.context/LIVE_STATE.md`
3. `.context/00_core/quick_reference_card.md`
4. `.context/00_core/research_operating_doctrine.md`
5. `.context/00_core/research_current_state.md`
6. `.context/00_core/goal_session_research_discipline.md`
7. Latest session handoff in `.context/02_session_handoffs/`

Then read from disk, not chat memory:

- `research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_numerical_screen_learning_synthesis_after_g12_audit/`
- `research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_numerical_screen_audit/`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_ready8_target_result_synthesis_and_quarantined_numerical_screen/`
- `research/science_program_2026_05/06_outcome_testing/g12_scid_noapi_ready8_quarantined_target_result_packet_audit/`
- `research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_quarantined_target_result_packet_after_g0_gate/`
- the upstream source-control/card-definition artifacts referenced by those ledgers and manifests.

Apply builder posture from `goal_session_research_discipline.md`: aggressive, constructive, source-safe repair/design. Search broadly for card-specific predicates, descriptor contrasts, source fields, and denominator rules. Do not self-censor because G12 will audit later. Do not collapse to OB-only framing; READY8 includes adversarial, behavioral, hazard, macro/session, uncertainty, and source-confidence/card families.

## Objective

Build the strongest auditable source-control repair/design package possible for discriminative READY8 card rowsets.

At minimum, produce:

1. A per-card source-field map for all `8` cards (`ADV-001`, `ADV-003`, `BEH-001`, `HAZ-001`, `HAZ-005`, `MAC-001`, `MAC-004`, `UNC-004`).
2. For each card, an explicit candidate predicate or descriptor-contrast design. A card is not discriminative if it merely repeats all `3,014` source candidates.
3. A candidate/card denominator policy that separates:
   - source candidate universe;
   - per-card eligible/pass rows;
   - per-card fail-closed rows;
   - non-applicable rows;
   - cross-card overlaps;
   - duplicate proxy denominator keys;
   - blocked/expansion sidecars.
4. A fail-closed policy preserving horizon/path/source missingness without inference or silent exclusion.
5. Duplicate and concentration controls using `duplicate_proxy_denominator_key`, candidate IDs, symbol/session/source-proxy groups, canonical economic groups, and source segment hashes.
6. A sealed/stress partition design that names discovery, development, sealed historical validation, stress/robustness, forward shadow, and contaminated partitions. Existing READY8 partition labels are source-control assignments only until this design is frozen and audited.
7. Target-opening prerequisites for any future no-API result packet: accepted repaired rowset, frozen horizons, frozen target families, frozen denominator rules, no-leak/as-of proof, fail-closed policy, duplicate/concentration gates, and independent G12 acceptance.
8. A saturation/self-red-team pass that asks what would make the repaired rowset non-discriminative again and repairs any same-evidence-class weakness found.

If source fields exist, materialize a draft repaired source-control rowset/design packet with row-level statuses and hashes. If a field is missing, do not write vague "needs data"; write the exact missing field/source/logger/parser/schema/access requirement and whether it is recoverable historical market data or non-generatable historical source-state truth.

## Required Outputs

Create a route directory:

`research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design/`

Emit machine-readable ledgers, not chat-only conclusions:

- decision ledger;
- source-field map ledger;
- card-predicate and descriptor-contrast ledger;
- denominator and duplicate policy ledger;
- fail-closed policy ledger;
- sealed/stress partition design ledger;
- target-opening prerequisite ledger;
- blocker/source-repair ledger;
- saturation/self-red-team ledger;
- completion audit;
- concise `.md` synthesis;
- builder/verifier/focused tests, or an explicit checklist only if a script is genuinely unnecessary and the audit proves why.

Do not rank or emit only a top-N slice of cards, fields, blockers, or questions. Preserve all discovered items in ledgers, then summarize separately if useful.

## Safe Boundaries

Preserve:

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

Do not open:

- target-result scoring;
- validation or promotion;
- strategy-edge, R, PnL, win-rate, expectancy, performance, or live-readiness claims;
- live trading behavior;
- AI/API calls;
- paid/vendor access;
- broker account/order/history/deal/position evidence;
- raw market blob commits;
- prompt/config/risk/safety/execution/canary/selector changes;
- registry edits;
- remote pushes.

## Completion Standard

Complete only when:

- all `8` READY8 cards have source-field maps and predicate/descriptor-contrast designs;
- every same-evidence-class blocker is repaired, proven impossible from approved inputs, or reduced to an exact source/access/capture requirement;
- denominator, fail-closed, duplicate/concentration, partition, and target-opening policies are explicit and verifier-covered;
- the route does not merely defer to "future work" where same-evidence-class repair/design was possible;
- emitted artifacts preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`;
- verifier/focused tests pass;
- `.context/00_core/research_current_state.md` and `.context/LIVE_STATE.md` are refreshed as required;
- scoped files are committed with `Co-Authored-By: Codex GPT-5 <redacted@example.com>`.
