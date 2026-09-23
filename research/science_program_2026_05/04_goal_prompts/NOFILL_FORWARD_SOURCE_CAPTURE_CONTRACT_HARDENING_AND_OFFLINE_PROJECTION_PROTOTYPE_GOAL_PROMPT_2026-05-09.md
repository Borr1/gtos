# NOFILL Forward Source Capture Contract Hardening And Offline Projection Prototype Goal Prompt

Date: 2026-05-09
Owner: G0/G12-controlled NOFILL forward source-capture lane
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build `NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_HARDENING_AND_OFFLINE_PROJECTION_PROTOTYPE` from the accepted G0 synthesis/control route.

The output must be a source/control-only contract and offline prototype package that can later be audited by G12 before any live logger wiring is considered. It must freeze exact forward capture fields, source-safe status vocabulary, parser/projection fixtures, redaction/no-leak controls, source/hash manifests, duplicate/denominator controls, hostile-review saturation, verifiers, focused tests, and the next G12 prompt pack.

This goal must not score outcomes, validate an edge, promote anything, edit registries, wire live loggers, change live trading behavior, call paid/API routes, or use broker/account/order/history/deal/position labels.

## Mandatory Preflight

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read latest `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `.context\00_core\goal_session_research_discipline.md`.
8. Read `.context\00_core\local_heavy_data_inventory.md`.
9. Read this prompt file again after preflight and record the exact HEAD and prompt path in the lane context anchor.

## Controlling Inputs

Primary controlling artifacts:

- `research/science_program_2026_05/06_outcome_testing/g0_nofill_forward_projection_synthesis_control_route/`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_projection_repair_reaudit/`
- `research/science_program_2026_05/06_outcome_testing/nofill_forward_source_safe_projection_builder/`
- `research/science_program_2026_05/06_outcome_testing/nofill_forward_contract_addendum_projection_plan/`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_lifecycle_capture_contract_audit/`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_source_control_rebuild/`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v3_source_control_audit/`

Also inspect neighboring NOFILL V3 count/synthesis/control artifacts if needed for denominator or label-family consistency. Examples are starting points, not boundaries.

## Research Hardening

Operate at maximum practical reasoning depth. Take as much time and as many internal steps as needed inside the hard safety boundaries.

Enforce the owner's three research virtues:

- Curiosity: search aggressively for better source-capture routes, hidden assumptions, missing source fields, and non-obvious improvement paths.
- Truthfulness: never invent, rescue, or soften evidence. If a field cannot be source-safe, state exactly why and what would be required.
- Active creativity: do not be boxed by the first field list, timeframe, instrument, worktree, data modality, or current model framing. Create useful alternative source-safe contract designs, then let no-leak/source/as-of constraints decide.

Same-evidence-class continuation is mandatory. Do not stop at blocker taxonomy if the next action is still source/control contract work, offline parser/projection work, fixture design, no-leak verification, source/hash manifesting, or duplicate/denominator control. Pursue every allowed ambiguity until it is cleared, proven impossible from approved inputs, or reduced to an exact owner/access/source/capture requirement.

Split only when crossing an evidence-class gate: G12 acceptance, result/cost scoring, validation, promotion, registry edit, live logger wiring, or live trading behavior. This goal stops before those gates.

Small `n` is not an excuse to stop. If sample-size or coverage is insufficient for a future lane, define the exact denominator, sample floor, expansion inventory, fields, parser, source path, hash policy, as-of rule, and owner/access requirement. Do not claim validation.

Negative or blocked findings are first-class evidence. For every blocked field family, explain whether the failure is source/as-of, no-leak, redaction, parser, duplicate, timestamp, cost/execution-label, worktree-data, or approval-bound.

Maintain a context anchor, active question stack, searched-root ledger, route-decision ledger, saturation/self-red-team ledger, and instruction-coverage checklist so context compaction cannot erase requirements.

## Required Work

1. Reconstruct the evidence chain from NOFILL CAT V3 source-control rebuild through G12 projection repair reaudit and G0 synthesis.
2. Freeze a forward source-capture contract with exact field names, types, required/optional/fail-closed status, as-of rule, source lineage, forbidden-field rule, and owner/G12 acceptance status.
3. Build offline parser/projection prototype artifacts only. The prototype may consume existing source/control artifacts and fixtures; it must not wire live loggers or touch live trading surfaces.
4. Create fixtures covering accepted rows, source-control rows, source-impossible rows, rejects, touch-not-observed rows, spread-present rows, redacted-ticket rows, same-tick ambiguity rows, missing/NA status rows, duplicate projections, and forbidden-field examples.
5. Freeze missing-status vocabulary so missing, not-applicable, not-observed, source-impossible, redacted, not-yet-captured, and forbidden states cannot be confused.
6. Build redaction controls for pending-order observability. No raw MT5 ticket, order id, deal id, position id, account id, account history, broker actual-R, or live result labels may be emitted or hashed.
7. Freeze source/hash manifests for every source, parser, fixture, schema, and projection artifact consumed or generated.
8. Preserve duplicate/denominator controls: `298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject`; accepted denominators remain `225` row-level, `182` `nofill_duplicate_key`, and `139` `duplicate_group_id`; reject-overlap rows have zero denominator effect.
9. Produce no-leak scans for generated contracts, fixtures, projections, and reports.
10. Produce a G12-ready next prompt pack for independent acceptance audit.
11. Write builder, verifier, and focused tests where useful. Verifiers should check committed lane scope and treat unrelated runtime dirt as informational, not as lane failure.
12. Update `.context/00_core/research_current_state.md` only if the research map changes materially; otherwise explain why it remains unchanged.

## Required Artifacts

Create a new lane under:

`research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_contract_hardening_offline_projection_prototype/`

Required outputs:

- context anchor
- evidence-chain reconciliation
- frozen source-capture contract
- source field schema JSON
- missing-status vocabulary JSON
- offline parser/projection prototype design
- fixture manifest and fixture files
- source/hash manifest
- no-leak and redaction audit
- duplicate/denominator control audit
- source/cost/execution separation ledger
- hostile-review and saturation ledger
- forbidden-route ledger
- G12 next prompt pack
- completion audit with instruction coverage
- builder script
- verifier script
- focused tests
- verification result JSON

Use versioned file names ending `2026-05-09` unless the goal runs after midnight; then use the actual run date and state it.

## Verification Requirements

At minimum:

- Parse all generated JSON/JSONL.
- Run `python -B -m py_compile` on generated Python.
- Run focused pytest with `-p no:cacheprovider` and controlled `--basetemp` under `C:\tmp`.
- Run the generated verifier.
- Recompute source/parser/fixture hashes.
- Scan generated artifacts for forbidden keys and forbidden value tokens.
- Check `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
- Check committed diff scope before commit.
- Regenerate `LIVE_STATE.md` after commits.

## Forbidden

Do not touch or modify:

- `src/` live trading behavior
- `prompts/` live trading prompts
- `config/` risk/execution/permissions/safety/selectors/canaries/order behavior
- MT5 order/account/history/deal/position routes
- credentials
- remote pushes
- paid/API/Databento calls
- master registries, unless producing proposed patch artifacts only and explicitly labeling them as proposals
- live logger wiring

Do not emit:

- R, synthetic path-R, broker actual-R, win rate, expectancy, DSR, PBO, profit factor, cost/slippage result labels, validation-safe claims, promotion claims, live-effect claims, account/order/history labels, or hidden outcome labels.

## Completion Standard

The goal is complete only when the source/control contract and offline projection prototype are built, verified, committed, and ready for a separate G12 acceptance audit, or when a completion audit proves exact impossibility from approved inputs and names the exact owner/access/source/capture requirement.

The completion audit must explicitly state whether a future live logger wiring lane is still gated. Default answer: yes, it remains gated behind G12 acceptance and separate owner approval.
