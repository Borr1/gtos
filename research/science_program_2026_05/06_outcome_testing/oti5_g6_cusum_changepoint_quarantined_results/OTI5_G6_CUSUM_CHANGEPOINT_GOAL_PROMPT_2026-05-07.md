# OTI5 G6 CUSUM/Changepoint Quarantined Result Goal Prompt

Date: 2026-05-07
Lane: OTI5 / G6 CUSUM-changepoint quarantined discovery result
Packet: OTG0-PKT-063
Experiment: G6-EXP-004-EXHAUSTION-CHANGEPOINT
Promotion posture: NO_PROMOTION_VERDICT

## Objective

Run the OTG0-PKT-063 CUSUM/changepoint quarantined result lane to proof-or-impossibility. G12 accepted only the frozen 81-row source-ready subset for a future quarantined audit. This goal must either compute the permitted quarantined discovery result from approved packet/tick inputs, or prove exactly why the result cannot be computed from current approved sources.

Do not stop at "needs G12 review"; G12 already accepted the substrate in `g12_otx_g6_post_audit`. Do not stop at a vague blocker. Pursue all approved local paths, use the local heavy-data inventory, and write machine-checkable artifacts.

## Mandatory Preflight And Context

1. Run `python scripts/generate_live_state.py` and read `.context/LIVE_STATE.md`.
2. Read the latest numbered handoff in `.context/02_session_handoffs/`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read `.context/00_core/goal_session_research_discipline.md`.
7. Read `.context/00_core/local_heavy_data_inventory.md`.
8. Record HEAD, freshness, and any stale-context repair in the completion audit.

If Git, filesystem, or data access is blocked, request access instead of silently downgrading the result.

## Controlling Inputs

Read directly:

- `research/science_program_2026_05/06_outcome_testing/g12_otx_g6_post_audit/G12_OTX_G6_POST_AUDIT_DECISION_LEDGER_2026-05-07.md/json`
- `research/science_program_2026_05/06_outcome_testing/g12_otx_g6_post_audit/G12_OTX_G6_SOURCE_HASH_TICK_COVERAGE_AUDIT_2026-05-07.md/json`
- `research/science_program_2026_05/06_outcome_testing/g12_otx_g6_post_audit/G12_OTX_G6_RESULT_ACCEPTANCE_REVIEW_2026-05-07.md/json`
- `research/science_program_2026_05/06_outcome_testing/g12_otx_g6_post_audit/G12_OTX_G6_NEXT_LANE_PROMPT_PACK_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_REBUILT_PACKET_PROPOSALS_2026-05-07.md/json`
- `research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_TICK_COVERAGE_LEDGER_2026-05-07.md/json`
- `research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/OTX_G6_SOURCE_HASH_LEDGER_2026-05-07.md/json`
- `research/science_program_2026_05/06_outcome_testing/otx_g6_tick_aware_end_to_end_resolution/build_otx_g6_tick_aware_end_to_end_resolution_2026_05_07.py`
- `research/science_program_2026_05/06_outcome_testing/g12_otx_g6_post_audit/build_g12_otx_g6_post_audit_2026_05_07.py`

Absolute data rule:

- Inspect and use the absolute main tick path when needed: `C:\Users\MSI\Documents\ai-trading-agent\data\ticks`.
- A missing file in this worktree is not proof of absence.
- Hash every external/local source file consumed.

## Frozen Subset

Only these rules are allowed:

- Packet: `OTG0-PKT-063`.
- Use only the G12 accepted source-ready subset: `81` rows.
- Exclude exactly these five rows unless G12 has a later committed audit that changes the subset:
  - `OTG0-PKT-063|NAS100_2026-05-03T16:15:00+00:00`
  - `OTG0-PKT-063|XAUUSD_2026-05-03T16:15:00+00:00`
  - `OTG0-PKT-063|XAUUSD_2026-05-03T16:30:00+00:00`
  - `OTG0-PKT-063|XAUUSD_2026-05-06T07:15:00+00:00`
  - `OTG0-PKT-063|XAUUSD_2026-05-06T08:00:00+00:00`
- Required statuses: `DECISION_QUOTE_FOUND_ASOF`, `ORDERED_TICK_PATH_AVAILABLE`, and `PREREGISTERED_TICK_CUSUM_FEATURE_READY`.
- Duplicate denominator must be frozen before scoring.
- Broker actual-R, account history, live trade results, hidden path labels, and blocked-packet outcomes remain closed.

## Work To Perform

1. Rebuild or independently verify the 81-row accepted subset from OTX/G12 artifacts.
2. Validate every source hash and feature-asof rule.
3. Verify the CUSUM/changepoint feature is decision-time only and not outcome-derived.
4. Define the duplicate denominator before scoring, then apply it consistently.
5. If a synthetic path outcome can be recomputed from approved tick/path inputs without leakage, compute the quarantined discovery metrics.
6. If the result cannot be computed, prove exactly why: missing field, missing source, parser gap, label-family conflict, duplicate ambiguity, or source/as-of failure.
7. Report DSR/PBO/effective-N as computable only if the lane actually has enough independent rows and a valid variant/train-test matrix; otherwise write exact `not_computable` reasons.
8. Write next-lane prompts only if a follow-up is justified by the result.

## Required Outputs

Write only under:

- `research/science_program_2026_05/06_outcome_testing/oti5_g6_cusum_changepoint_quarantined_results/`

Required artifacts:

- `OTI5_G6_CUSUM_METHOD_FREEZE_2026-05-07.md/json`
- `OTI5_G6_CUSUM_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.md/json`
- `OTI5_G6_CUSUM_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.md/json`
- `OTI5_G6_CUSUM_LABEL_FAMILY_NOLEAK_REPORT_2026-05-07.md/json`
- `OTI5_G6_CUSUM_RESULT_LEDGER_2026-05-07.md/json/jsonl` if scoring is possible, or `OTI5_G6_CUSUM_RESULT_IMPOSSIBILITY_LEDGER_2026-05-07.md/json` if not
- `OTI5_G6_CUSUM_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT_2026-05-07.md/json`
- `OTI5_G6_CUSUM_BLOCKER_AND_NEXT_ACTION_LEDGER_2026-05-07.md/json`
- `OTI5_G6_CUSUM_COMPLETION_AUDIT_2026-05-07.md/json`
- Builder/verifier script and focused tests.

## Verification

Before marking complete:

- JSON parse every generated JSON/JSONL artifact.
- Run `python -B -m py_compile` on generated Python.
- Run focused pytest for generated tests.
- Run relevant G12/OTX tests if they are still applicable.
- Scan outputs for `NO_PROMOTION_VERDICT`.
- Confirm no `validation_safe=true`, `outcome_review_opened=true`, or `live_effect=true`.
- Confirm no forbidden live-surface diff under `src`, `prompts`, `config`, `scripts/canary`, MT5, execution, permissions, safety gates, selectors, credentials, remote pushes, paid/API/Databento, or order behavior.
- Regenerate `.context/LIVE_STATE.md` and update `.context/00_core/research_current_state.md` if the durable research map changed.

## Forbidden

No live trading prompt/risk/execution/permission/safety/selector/MT5/canary/order behavior changes. No broker actual-R, account history, live trade results, blocked-packet outcomes, hidden path labels, paid/API/Databento calls, credentials, remote pushes, source validation flips, outcome-review flips, or promotion language.

## Stop Condition

The goal is complete only when the frozen 81-row subset has either a committed quarantined discovery result or a committed proof that the result cannot be computed from approved inputs, with exact blockers and verification passing.
