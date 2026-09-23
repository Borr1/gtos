# G0 SCID READY8 Discriminative Result-Opening Gate After G12 Audit

Date: 2026-05-13

## Evidence Class

`G0_SCID_READY8_DISCRIMINATIVE_RESULT_OPENING_GATE_AFTER_G12_AUDIT_ONLY`

This is a narrow G0 gate after independent G12 acceptance of the repaired READY8 discriminative card rowset.

It is not target-result scoring, not validation, not promotion, and not a live-trading change. It is also not another passive synthesis loop. Its job is to decide whether the accepted repaired discriminative rowset is ready to open a separate quarantined no-API target-result/materialization route, and if ready, emit that exact next prompt and starter.

The accepted repaired rowset is the object under test:

- source candidate universe: `3,014`
- READY8 cards: `8`
- repaired accounting rowset: `24,112`
- rowset SHA256: `fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3`
- G12 terminal decision: `ACCEPT_AS_G12_SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_CONTROL_EVIDENCE_ONLY`

## Mandatory Preflight And Context Use

Run and read:

1. `python scripts/generate_live_state.py`
2. `.context/LIVE_STATE.md`
3. `.context/00_core/quick_reference_card.md`
4. `.context/00_core/research_operating_doctrine.md`
5. `.context/00_core/goal_session_research_discipline.md`
6. `.context/00_core/research_current_state.md`
7. Latest session handoff in `.context/02_session_handoffs/`

Treat `goal_session_research_discipline.md` and `research_operating_doctrine.md` as active instructions, not background. Apply the anti-loop, anti-boxing, same-evidence-class continuation, completion-as-exhaustion, no arbitrary top-N, and speed-is-not-quality-limit rules to this gate.

Do not rely on chat memory or pasted closeout summaries. Read the disk artifacts.

## Inputs To Read From Disk

Read at minimum:

- `research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_card_rowset_repair_audit/`
- `research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design/`
- `research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_numerical_screen_audit/`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_numerical_screen_learning_synthesis_after_g12_audit/`
- `research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_quarantined_target_result_packet_after_g0_gate/`
- `research/science_program_2026_05/06_outcome_testing/g12_scid_noapi_ready8_quarantined_target_result_packet_audit/`

If a referenced file is missing, search the committed route manifests and `rg --files` before declaring it missing.

## Objective

Freeze the exact prerequisites for the next separate discriminative READY8 no-API target-result/materialization route.

This gate must answer:

1. Is the accepted repaired rowset ready for a separate quarantined result-packet/materialization route?
2. If yes, what exact result-packet route should run next?
3. If no, what exact same-evidence-class blocker remains, and can it be repaired in this gate before stopping?

Do not emit another generic G0 or G12 unless disk evidence proves that is the only valid route. The default expected successful output is a next prompt that materializes target/result rows over the accepted repaired discriminative rowset, while preserving the result lane as quarantined and non-promotional.

## No-Loop Blocker Pursuit Contract

This gate exists to prevent the research from looping through "found blocker -> ask for another goal -> find same blocker again". Treat blocker discovery as the start of same-G0 pursuit, not as a stop condition.

If an issue, ambiguity, stale hash, missing manifest field, denominator uncertainty, no-leak question, duplicate/concentration problem, target-family/horizon uncertainty, prompt weakness, or artifact mismatch appears, the session must immediately ask:

1. Can this be repaired, rebound, recomputed, normalized, re-read, rehashed, re-manifested, or exactly classified inside this G0 evidence class?
2. Can another accepted artifact in the listed inputs answer it from disk?
3. Can a local search over route manifests, source ledgers, prior accepted packets, current git history, or committed rowsets answer it?
4. Can the next result-packet prompt be written to handle it as a frozen prerequisite instead of deferring this gate?
5. Does resolving it truly require crossing into target-result row generation, G12 post-result audit, validation, promotion, live behavior, paid/API/vendor access, broker/account/order/deal/position evidence, raw market blob commit, registry edit, remote push, or trading-surface change?

The session may not emit a repair prompt, future-work item, or terminal blocker for any item whose answer to questions 1-4 is yes. It must pursue that item now, write the evidence, rerun the relevant verifier, and only then continue the gate.

The session may split only when question 5 is yes, or when a same-G0 pursuit is proven impossible from approved inputs. If it splits, the blocker must be exact: file/path/field/hash/rowset/status/source/access/capture requirement, every search route attempted, and why the current G0 gate cannot lawfully or technically close it.

Completion means no known useful same-G0 gate intelligence remains. "This should be done later", "needs another prompt", "not enough time", "top issues only", "likely okay", "blocked by missing data", or "G12 can check later" are not completion standards when the issue is answerable inside this gate.

## Gate Requirements

Before opening the next route, freeze all of these from disk:

- accepted G12 decision path and commit;
- accepted repaired rowset path and SHA256;
- row identity policy:
  - `candidate_input_row_id`
  - `card_id`
  - `rowset_row_id`
  - `duplicate_proxy_denominator_key`
  - `row_hash`
- per-card status policy:
  - `PASS_DESCRIPTOR_CONTRAST_ELIGIBLE`
  - `PASS_CARD_PREDICATE`
  - `ELIGIBLE_CONTRAST_CONTROL`
  - `NON_APPLICABLE_SOURCE_CONTEXT`
  - `FAIL_CLOSED_MISSING_PRIOR_CANDIDATE`
  - `FAIL_CLOSED_DESCRIPTOR_NOT_COMPUTABLE`
- denominator policy:
  - pass rows enter per-card pass denominator;
  - contrast rows are retained as within-card controls;
  - non-applicable rows remain visible but cannot enter pass denominators;
  - fail-closed rows remain visible, with exact source requirements, and cannot be silently dropped or counted as passes;
  - adversarial full-coverage descriptor-control cards must remain controls/placebos, not edge-card pass claims;
- duplicate and concentration gates using `duplicate_proxy_denominator_key`, `candidate_input_row_id`, `canonical_economic_group`, symbol/session/source-proxy groups, and `source_segment_sha256`;
- no-leak/as-of proof requirements for every source field consumed by each card predicate;
- target horizons and target families to be opened in the next result-packet route;
- handling of the previous neutral target families and horizons:
  - close-to-close and high-low excursion;
  - horizons `1/4/16/32`;
  - keep them only if disk evidence supports reusing them under the repaired rowset;
- whether additional target families/horizons are source-safe and useful inside a no-API quarantined result-packet route;
- exact G12 post-result audit requirement;
- exact rule preventing validation, performance, live-readiness, R/PnL/win-rate/expectancy, or promotion claims from the next packet alone.

## Aggressive But Clean Gate Posture

This prompt must not be conservative or boxed:

- Do not stop at "G12 accepted, now future work" if the next result-packet prompt can be emitted now.
- Do not limit the next result-packet design to a tiny obvious slice if the accepted rowset and target source artifacts support a full-population route.
- Do not collapse the question back to OB-only, current GTOS edge framing, or only the old redundant screen.
- Do not arbitrarily cap cards, statuses, blockers, target families, horizons, partitions, examples, or route questions.
- Do not invent blockers to look rigorous.
- Do not use hard boundaries as psychological brakes. Boundaries prevent contamination; inside them, pursue the strongest exact next route.

If a same-evidence-class blocker appears, pursue it inside this G0 gate until it is:

- repaired;
- proven impossible from approved inputs;
- reduced to an exact source/access/capture requirement;
- or proven to require crossing into target-result scoring, G12 result audit, validation, promotion, live behavior, broker/API/paid/raw/remote/registry territory.

## Required Outputs

Create:

`research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_discriminative_result_opening_gate_after_g12_audit/`

Emit versioned artifacts with `2026-05-13` in file names:

1. `G0_SCID_READY8_DISCRIMINATIVE_RESULT_OPENING_GATE_DECISION_LEDGER_2026-05-13.json`
   - terminal decision,
   - accepted G12 evidence binding,
   - exact route decision,
   - blocker/repair summary,
   - safe flags.

2. `G0_SCID_READY8_DISCRIMINATIVE_RESULT_OPENING_PREREQUISITE_FREEZE_LEDGER_2026-05-13.json`
   - rowset path/hash,
   - row identity,
   - card/status/role policy,
   - target family/horizon freeze,
   - no-leak/as-of prerequisites,
   - duplicate/concentration gates.

3. `G0_SCID_READY8_DISCRIMINATIVE_DENOMINATOR_GATE_LEDGER_2026-05-13.json`
   - pass/control/non-applicable/fail-closed treatment for every card and status;
   - adversarial-control treatment for `ADV-001` and `ADV-003`;
   - blocked/expansion sidecar exclusion rules.

4. `G0_SCID_READY8_DISCRIMINATIVE_NO_LEAK_AND_FORBIDDEN_SURFACE_GATE_LEDGER_2026-05-13.json`
   - forbidden field scan plan;
   - allowed source fields;
   - prohibited result/live/broker/API/paid/raw/registry/remote surfaces;
   - exact next-route boundary.

5. `G0_SCID_READY8_DISCRIMINATIVE_BLOCKER_AND_REPAIR_LEDGER_2026-05-13.json`
   - every issue found,
   - same-G0 repairs performed,
   - exact unrepaired blocker only if not same-G0-repairable.

6. `G0_SCID_READY8_DISCRIMINATIVE_ROUTE_DECISION_SYNTHESIS_2026-05-13.md`
   - concise explanation of what opens next and why.

7. Standalone builder, verifier, and focused tests.

8. If ready, emit:
   - `research/science_program_2026_05/04_goal_prompts/SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_GOAL_PROMPT_2026-05-13.md`
   - a one-line starter file under this route directory.

9. If not ready, emit an exact repair prompt instead, but only after same-G0 repair options are exhausted.

## Verification Requirements

Before marking complete:

1. Rerun the accepted G12 audit verifier from disk.
2. Parse the accepted repaired rowset manifest and recomputation ledger.
3. Confirm the next prompt, if emitted, references the accepted repaired rowset rather than the old redundant rowset.
4. Run the new G0 gate verifier.
5. Run focused pytest.
6. Syntax-check new Python files. If Windows pycache friction appears, use explicit cfile or AST/no-bytecode fallback and record it precisely.
7. Parse every emitted JSON/JSONL artifact.
8. Confirm no unrelated live/runtime/shadow dirt is staged.
9. Regenerate `.context/LIVE_STATE.md`.
10. Update `.context/00_core/research_current_state.md`.
11. Commit scoped route/prompt/context files only.

## Safe Boundaries

Preserve:

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

Do not open:

- target-result scoring inside this G0 gate;
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

The next prompt may authorize a separate quarantined no-API target-result packet if and only if this gate freezes all prerequisites and keeps that next packet non-promotional.

## Allowed Terminal Decisions

- `OPEN_DISCRIMINATIVE_READY8_QUARANTINED_TARGET_RESULT_PACKET_PROMPT`
- `OPEN_DISCRIMINATIVE_READY8_TARGET_PACKET_WITH_EXACT_NONBLOCKING_FOLLOWUPS`
- `REPAIR_BLOCKED_WITH_EXACT_G0_READY8_RESULT_OPENING_REPAIR_REQUIREMENTS`
- `CLOSE_READY8_RESULT_OPENING_AS_NOT_READY_WITH_EXACT_KILL_OR_FORWARD_CAPTURE_REQUIREMENTS`

## Completion Standard

Complete only when:

- the accepted G12 audit and repaired rowset are bound from disk;
- every prerequisite is frozen or exactly blocked;
- every issue/blocker/ambiguity found during the run has been pursued through the No-Loop Blocker Pursuit Contract;
- every same-G0 repairable issue has been repaired, reverified, and recorded;
- every unrepaired issue is proven impossible from approved inputs or crosses an explicit evidence-class/forbidden-surface boundary;
- the next route is exact and non-looping;
- verifier/focused tests pass;
- no forbidden surface is opened;
- context is updated;
- scoped commits are made.
