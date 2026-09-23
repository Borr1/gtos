# G12 NOFILL Forward Lifecycle Capture Contract Audit Goal Prompt

Date: 2026-05-09
Owner lane: G12 red-team audit
Worktree: `C:\tmp\gtos_otb\G12NOFILLFORWARD`
Branch: `g12-nofill-forward-capture-contract-audit`
Starting HEAD: `aaf2f77a docs: refresh no-fill forward usdjpy research state`

## Goal

Run a maximum-depth G12 audit of the `NOFILL_CAT_V3_FORWARD_LIFECYCLE_CAPTURE_CONTRACT` lane and decide whether the forward capture contract can be accepted as a source/control contract for future audited implementation, or whether it must be returned with exact blockers.

This is not result scoring, validation, promotion, or live implementation. The output must stay research/control only and preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

## Mandatory Preflight And Context

Before using memory or prior summaries:

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read the latest numbered handoff in `.context/02_session_handoffs/`.
4. Read `.context/00_core/quick_reference_card.md`.
5. Read `.context/00_core/research_operating_doctrine.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read `.context/00_core/goal_session_research_discipline.md`.
8. Read `.context/00_core/local_heavy_data_inventory.md`.

Do not rely on chat memory. If context compaction or uncertainty occurs, regenerate live state, reread this prompt and the lane context anchor, then continue from disk artifacts.

## Controlling Inputs

Read and cite the forward contract lane:

- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_forward_lifecycle_capture_contract/NOFILL_FORWARD_CONTEXT_ANCHOR_2026-05-09.md`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_forward_lifecycle_capture_contract/NOFILL_FORWARD_CAPTURE_CONTRACT_2026-05-09.md`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_forward_lifecycle_capture_contract/NOFILL_FORWARD_CAPTURE_CONTRACT_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_forward_lifecycle_capture_contract/NOFILL_FORWARD_SOURCE_FIELD_SCHEMA_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_forward_lifecycle_capture_contract/NOFILL_FORWARD_NO_LEAK_FIELD_POLICY_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_forward_lifecycle_capture_contract/NOFILL_FORWARD_DUPLICATE_DENOMINATOR_POLICY_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_forward_lifecycle_capture_contract/NOFILL_FORWARD_EXISTING_SOURCE_AND_CODE_AUDIT_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_forward_lifecycle_capture_contract/NOFILL_FORWARD_CAPTURE_BACKLOG_AND_IMPLEMENTATION_ROUTE_2026-05-09.json`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_forward_lifecycle_capture_contract/NOFILL_FORWARD_HOSTILE_EDGE_REVIEW_AND_SATURATION_2026-05-09.md`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_forward_lifecycle_capture_contract/NOFILL_FORWARD_COMPLETION_AUDIT_2026-05-09.md`
- the lane builder, verifier, and focused test files.

Also read the upstream chain:

- `research/science_program_2026_05/06_outcome_testing/g0_nofill_cat_v3_categorical_evidence_synthesis_control_review/`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v3_quarantined_categorical_count_packet_audit/`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_quarantined_categorical_count_packet/`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v3_result_contract_audit/`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_result_contract_update/`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_cat_v3_source_control_audit/`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_source_control_rebuild/`
- `research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_usdjpy_quote_event_sequence_source_access/`

## Hardening Standard

Operate at maximum practical reasoning depth. Take as much time and as many internal steps as needed inside hard safety boundaries.

Enforce curiosity, truthfulness, and active creativity:

- Curiosity: search for contradictions, missing fields, stale context, source routes, implementation traps, and improvement opportunities beyond the obvious files.
- Truthfulness: do not rescue, soften, or relabel weak evidence. If a contract claim fails, state exactly why and what field/source/schema/control breaks.
- Active creativity: think beyond the current GTOS edge, known strategy norms, default timeframes, and the first framing, but let source-safe data and strict controls decide.

Do not stop at shallow blocker taxonomy. Within this source/control evidence class, pursue every relevant ambiguity until it is accepted, rejected, proven impossible from approved inputs, or reduced to an exact owner/access/source/capture requirement. Split only when the next route crosses an evidence-class gate such as live implementation, result scoring, validation, promotion, registry edit, or paid/API/live trading behavior.

Small-N is not an excuse. If a contract or backlog claim cites small samples or incomplete capture, define the exact expansion/capture path and fields rather than stopping.

Apply hostile review from the trading-system memo: ask what part of the evidence is real versus noise, what destroys the edge, whether costs/execution/regime/source timing are measurable, and whether the proposed capture contract can support later survival-adjusted expectancy testing without leakage.

## Audit Requirements

1. Reconstruct the full V3 NOFILL evidence chain and the frozen equation:
   - `298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject`
   - denominators: `225` row-level accepted, `182` `nofill_duplicate_key`, `139` `duplicate_group_id`
   - `47` reject-overlap rows neutralized by accepted-first filtering.
2. Independently audit the forward capture schema:
   - field count and family count;
   - source/as-of timestamp fields;
   - no-leak exclusions;
   - cost/spread/slippage/execution-observability fields where source-safe;
   - duplicate/denominator controls;
   - source provenance, hashes, parser/version fields, and capture latency fields;
   - fields needed to prevent repeated no-fill, opening-drive, fill/path, and same-tick blocker patterns.
3. Audit existing code/source coverage:
   - `src/research_infra/forward_capture.py`
   - current shadow logs and source logs named by the lane;
   - source-safe projection risks where raw logs contain account/order/result-shaped fields.
4. Search local heavy-data and committed artifacts for any missed capture/source fields that would make the contract stronger. Worktree absence is not data absence.
5. Produce an adversarial finding set:
   - accepted contract claims;
   - rejected or weakened claims;
   - exact missing fields;
   - exact implementation blockers;
   - source/no-leak hazards;
   - duplicate/denominator hazards;
   - where the future implementation must not cross into result scoring or live behavior.
6. Decide one terminal G12 verdict:
   - `ACCEPT_AS_SOURCE_CONTROL_CONTRACT_FOR_FUTURE_AUDITED_IMPLEMENTATION`
   - `ACCEPT_WITH_EXACT_CONTRACT_BLOCKERS`
   - `RETURN_TO_G0_OR_FORWARD_LANE_WITH_EXACT_FIXES`
   - `REJECT_INVALID_CONTRACT`

## Required Outputs

Create a new folder:

`research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_lifecycle_capture_contract_audit/`

Produce at minimum:

- `G12_NOFILL_FORWARD_DECISION_LEDGER_2026-05-09.md`
- `G12_NOFILL_FORWARD_SCHEMA_AUDIT_2026-05-09.json`
- `G12_NOFILL_FORWARD_NO_LEAK_SOURCE_AUDIT_2026-05-09.json`
- `G12_NOFILL_FORWARD_DUPLICATE_DENOMINATOR_AUDIT_2026-05-09.json`
- `G12_NOFILL_FORWARD_BACKLOG_AND_IMPLEMENTATION_AUDIT_2026-05-09.md`
- `G12_NOFILL_FORWARD_HOSTILE_EDGE_REVIEW_2026-05-09.md`
- `G12_NOFILL_FORWARD_NEXT_PROMPT_PACK_2026-05-09.md`
- `G12_NOFILL_FORWARD_COMPLETION_AUDIT_2026-05-09.md`
- builder/verifier/focused pytest files if useful for reproducibility.

Update `.context/00_core/research_current_state.md` after the audit commit.

## Verification Required

Before marking complete:

- JSON parse all generated JSON.
- Run `python -m py_compile` on generated Python.
- Run focused pytest for the audit.
- Recompute source/hash/no-leak/duplicate checks that the audit claims.
- Confirm no `validation_safe=true`, no `outcome_review_opened=true`, no `live_effect=true`.
- Confirm every generated artifact carries or preserves `NO_PROMOTION_VERDICT`.
- Check committed diff scope, not unrelated dirty live-monitoring files.
- Confirm no changes under live trading prompts, `src` trading logic, config/risk/execution/permissions/safety/selectors, MT5 order/account/history behavior, canaries, credentials, remote pushes, paid/API/Databento calls, registry promotion, or order behavior.
- Regenerate `LIVE_STATE.md` at closeout and ensure research context is fresh or update `.context/00_core/research_current_state.md`.

Commit scoped artifacts with a clear research commit and a docs/context refresh commit. Do not push remote.
