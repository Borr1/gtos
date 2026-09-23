# SCID No-API Ready-8 Rowset, Target-Horizon, And Result-Packet Materialization

Evidence class: `SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_RESULT_PACKET_MATERIALIZATION_ONLY`

Route rank: `1`

Run state: `RUN_NOW_NO_API_PACKET_MATERIALIZATION_NO_SCORING`

Objective: for the `8` preregisterable descriptor/control cards accepted by G12 and selected by G0, materialize the strongest possible no-API source-control packet: source-hashed rowsets, target-horizon contracts, duplicate-denominator manifests, partition/control manifests, baseline/control assignment manifests, and a future result-opening gate prompt if and only if the packet dependencies are frozen. Do not score outcomes in this route.

This is not a passive design memo. It is a source-control materialization lane. Use every accepted disk artifact and all source-safe historical/as-of inputs available inside this evidence class. Runtime is not a quality constraint. Do not choose compact-only, shallow, or "good enough" packets when a fuller no-leak rowset can be built.

## Mandatory Context Use

Run and read before work:

1. `python scripts/generate_live_state.py`
2. `.context/LIVE_STATE.md`
3. `.context/00_core/goal_session_research_discipline.md`
4. `.context/00_core/research_operating_doctrine.md`
5. `.context/00_core/research_current_state.md`
6. `.context/00_core/local_heavy_data_inventory.md`
7. `.context/00_core/ai_in_loop_cost_control_research_plan.md`
8. `research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_40card_prereg_replay_input_design_synthesis/`

The completion audit must explicitly state how this route applied anti-boxing, proof-or-impossibility, historical replay opportunity-cost, no-API cost control, and the builder posture from `goal_session_research_discipline.md`.

## Required Inputs

Read from disk. Do not rely on chat memory or closeout summaries.

- `research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_40card_prereg_replay_input_design_synthesis/G0_SCID_NOAPI_PREREG_SYNTHESIS_READY_8_ROUTE_LEDGER_2026-05-12.json`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_40card_prereg_replay_input_design_synthesis/G0_SCID_NOAPI_PREREG_SYNTHESIS_ROUTE_RANKING_MATRIX_2026-05-12.json`
- `research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_40card_prereg_replay_input_design_synthesis/G0_SCID_NOAPI_PREREG_SYNTHESIS_DECISION_LEDGER_2026-05-12.json`
- `research/science_program_2026_05/06_outcome_testing/g12_scid_noapi_40card_prereg_replay_input_design_audit/G12_SCID_NOAPI_PREREG_AUDIT_DECISION_LEDGER_2026-05-12.json`
- target replay-input packet design ledger from `research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/`
- target per-card terminal status ledger from `research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/`
- target source-field mapping matrix from `research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/`
- accepted SCID as-of packet and neutral target packet artifacts needed for source/as-of/target-horizon contracts.

If an expected artifact filename differs, search the target route directory, G12 route directory, and current-state references. Missing-file wording is not enough until those roots are searched and recorded.

## Frozen Ready-8 Scope

Materialize all `8` ready cards exactly once:

- `ADV-001`: `session_only_matched_placebo`
- `ADV-003`: `duplicate_key_random_proxy_placebo`
- `BEH-001`: `session_open_constraint_family`
- `HAZ-001`: `candidate_density_waiting_time`
- `HAZ-005`: `regime_transition_hazard_clock`
- `MAC-001`: `day_of_week_month_turn_context`
- `MAC-004`: `fixing_window_context`
- `UNC-004`: `source_contract_confidence_without_scores`

Preserve these boundaries:

- accepted-card denominator remains `40`;
- ready-card denominator remains `8`;
- blocked dependency rows remain `32`, not silently mixed into ready materialization;
- quarantined expansion candidates remain outside the accepted denominator;
- this route may create expansion observations only in a separate quarantine ledger.

## Required Work

1. Recompute the ready-8 list and packet IDs from disk.
2. For each ready card, materialize all eligible source-control rows available from the accepted SCID candidate/input universe. Do not sample unless a full rowset is impossible; if impossible, write the exact proof.
3. Build row-level manifests that include candidate identity, packet ID, card ID, science domain, mechanism family, source group, symbol/session/time keys, duplicate proxy denominator key, partition assignment, baseline/control assignment, source artifact pointers, parser/as-of version, and hash fields.
4. Build target-horizon contracts without computing outcome hits or performance. A target-horizon contract may define allowed horizon windows, target/stop/hazard observation windows, source rows required for future scoring, and fail-closed missing-status vocabulary. It must not include `target_hit`, `stop_hit`, `outcome`, `R`, `PnL`, `win_rate`, `expectancy`, `performance`, or realized broker facts.
5. Build duplicate/denominator manifests before any future scoring:
   - primary candidate row denominator;
   - duplicate proxy denominator key;
   - card/packet denominator;
   - partition/control denominator;
   - exclusion and concentration diagnostics that are input-only.
6. Build partition manifests for discovery/development/sealed/stress/forward/contaminated status. If no sealed result pool can be opened yet, state the exact source-control reason and preserve the future gate.
7. Build baseline/control assignment manifests with deterministic seeds and no result lookups. Baselines must be source-control assignments only.
8. Build a future result-opening gate prompt only after packet dependencies are frozen. That future prompt must be a separate evidence class and must contain G12/G0 gates. If dependencies are not frozen, emit an exact blocker prompt instead.
9. Pursue same-evidence-class gaps. If a source field, denominator, partition, control assignment, target-horizon field, or parser/as-of binding is missing and can be derived from accepted artifacts without outcome leakage, derive it now. Do not merely classify it as future work.
10. Search relevant local accepted artifacts and source-control routes before declaring a missing dependency. Worktree absence is not data absence.
11. Preserve and route any useful new non-OB, non-current-GTOS, no-API materialization insight in a separate expansion ledger. Do not mix it into the accepted ready-8 denominator.
12. Emit a G12 audit prompt/starter for the materialized packet.

## Required Outputs

Create a route under:

`research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_rowset_target_horizon_result_packet_materialization/`

Required artifacts:

- `SCID_NOAPI_READY8_ROWSET_MANIFEST_2026-05-12.json`
- `SCID_NOAPI_READY8_ROWSET_ROWS_2026-05-12.jsonl`
- `SCID_NOAPI_READY8_TARGET_HORIZON_CONTRACT_2026-05-12.json`
- `SCID_NOAPI_READY8_DUPLICATE_DENOMINATOR_MANIFEST_2026-05-12.json`
- `SCID_NOAPI_READY8_PARTITION_CONTROL_MANIFEST_2026-05-12.json`
- `SCID_NOAPI_READY8_BASELINE_CONTROL_ASSIGNMENT_MANIFEST_2026-05-12.json`
- `SCID_NOAPI_READY8_RESULT_OPENING_GATE_DECISION_2026-05-12.json`
- `SCID_NOAPI_READY8_BLOCKER_OR_DEPENDENCY_LEDGER_2026-05-12.json`
- `SCID_NOAPI_READY8_EXPANSION_OBSERVATION_LEDGER_2026-05-12.json`
- `SCID_NOAPI_READY8_NO_LEAK_AND_FORBIDDEN_SURFACE_AUDIT_2026-05-12.json`
- `SCID_NOAPI_READY8_SOURCE_HASH_AND_ASOF_AUDIT_2026-05-12.json`
- `SCID_NOAPI_READY8_SATURATION_SELF_RED_TEAM_2026-05-12.md`
- `SCID_NOAPI_READY8_COMPLETION_AUDIT_2026-05-12.json`
- `SCID_NOAPI_READY8_VERIFICATION_RESULT_2026-05-12.json`
- builder, verifier, and focused tests.

If a JSONL row count is large, write it in chunks or stream it. Do not replace full materialization with a compact summary unless a full rowset is proven impossible.

## Forbidden Surfaces

This route must not open:

- validation execution;
- outcome/result labels;
- `target_hit`, `stop_hit`, realized outcome, R, PnL, win-rate, expectancy, performance, cost, or slippage scoring;
- promotion;
- AI/API calls;
- paid/vendor access;
- broker account/order/history/deal/position evidence;
- raw market-data blob commits;
- live restart or live behavior;
- trading/risk/safety/prompt-decision/config/execution/canary/selector changes;
- credential, registry, remote, or order-behavior changes.

## Anti-Boxing And Aggression Requirements

This route should be aggressive inside source-control materialization. It must not:

- collapse to OB-only or current GTOS logic;
- wait for live data when source-safe historical/as-of packets exist;
- stop after writing a blocker taxonomy if a source-control derivation is available;
- materialize only a small sample when all eligible rows can be materialized;
- convert the future result gate into current scoring;
- suppress useful expansion observations because they are outside the accepted ready-8 denominator.

## Verification

The verifier and focused tests must check:

- exactly `8` ready cards;
- all eight named card IDs present exactly once;
- rowset rows are source-hashed and as-of bound;
- rowset row count and exclusion counts reconcile;
- duplicate denominator manifest exists and is deterministic;
- partition/control assignment manifest exists and is deterministic;
- target-horizon contract has no result/performance fields;
- no forbidden surfaces opened;
- future result gate or exact blocker exists;
- G12 audit prompt/starter exists;
- safe flags remain closed.

## Allowed Terminal Decisions

- `MATERIALIZED_READY8_SOURCE_CONTROL_PACKET_G12_AUDIT_REQUIRED`
- `MATERIALIZED_READY8_WITH_EXACT_RESULT_GATE_BLOCKERS`
- `REPAIR_BLOCKED_READY8_MATERIALIZATION`

Do not use repair-blocked for a future scoring dependency. Use repair-blocked only for missing/invalid source-control artifacts, failed recomputation, unsafe surface opening, or broken verifier/test evidence.

## Completion Standard

Mark complete only when:

- all eight ready cards are materialized or exact row-level exclusions are proved;
- source-hashed rowset, target-horizon, denominator, partition/control, baseline/control, no-leak, source-hash/as-of, and completion artifacts exist;
- no outcome/result/performance scoring is opened;
- a saturation/self-red-team pass proves the route did not stop at compact-only output, passive waiting, OB-only framing, or vague blockers when same-evidence-class materialization remained possible;
- future result-opening gate prompt or exact blocker prompt exists;
- G12 audit prompt/starter exists;
- builder/verifier/focused tests pass;
- scoped artifacts and context refresh are committed;
- `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false` are preserved.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G0NAPI_R1_READY8_MATERIALIZE_GOAL_PROMPT_2026-05-12.md as the complete objective; run mandatory preflight/context refresh; do not rely on chat memory; stay SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_RESULT_PACKET_MATERIALIZATION_ONLY with no validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision changes; materialize all eligible source-control rows for the 8 ready cards ADV-001 ADV-003 BEH-001 HAZ-001 HAZ-005 MAC-001 MAC-004 UNC-004; build source-hashed rowsets, target-horizon contracts, duplicate-denominator manifests, partition/control manifests, baseline/control assignments, no-leak/hash/as-of audits, future result-gate or exact blocker prompt, G12 audit prompt, verifier/tests, scoped commits; treat 40 cards as floor not ceiling while preserving denominator boundaries; do not collapse to OB-only, passive waiting, compact-only summaries, or vague blockers; NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false; mark complete only when this prompt's completion standard is fully satisfied.`
