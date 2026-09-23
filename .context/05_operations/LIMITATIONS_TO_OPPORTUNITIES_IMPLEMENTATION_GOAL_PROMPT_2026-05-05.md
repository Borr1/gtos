# Limitations-To-Opportunities Implementation Goal Prompt - 2026-05-05

Use this prompt for a fresh `/goal` or resumed implementation session.

## Objective

Implement the limitations-to-opportunities engineering queue from:

- `research/program_control/LIMITATIONS_TO_OPPORTUNITIES_ENGINEERING_PLAN_2026-05-05.md`

The goal is to convert every known 2026-05-04 monitoring limitation, source blocker, no-event lane, approval blocker, and hardening opportunity into correct, reliable, tested infrastructure or an explicit blocker artifact. Preserve `NO_PROMOTION_VERDICT` throughout.

This is not only a data-capture hardening goal. It is also an ML-improvement goal: every capture, join, source registry, lifecycle repair, account-history reconciliation, orderflow feature, regime/decay join, and diagnostic row should improve the future K55/ML shadow substrate when it is valid, as-of, provenance-tagged, and non-leaking. Treat "better data" and "better ML evidence" as two coupled outcomes of the same implementation program.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read `research/program_control/LIMITATIONS_TO_OPPORTUNITIES_ENGINEERING_PLAN_2026-05-05.md`.
7. Read the latest numbered handoff in `.context/02_session_handoffs/`.

## Resume Context Hygiene

- If this prompt is being read inside an already-resumed `/goal` session, continue the queue directly. Do not tell the owner to run `/goal resume`; they are already in it.
- After context compaction, treat the two anchor files in this prompt and the generated queue state as the active source of truth. Do not ask whether the TikTok/orderflow context was included; it is already incorporated below and in the engineering plan as a measurable orderflow hypothesis.
- Status updates should name the current LTO item being implemented, the verifier/test being run, or the blocker being written.

## Non-Negotiable Boundaries

- No live trading behavior changes without explicit owner approval.
- No prompt changes, risk changes, execution changes, safety-gate changes, order calls, or canary calls unless explicitly approved.
- Databento live pulls are owner-approved for `LTO-010` value-max forward confluence when routed through the registered trigger policy, cost cap, cooldown, environment/API gate, and confluence/budget ledgers. Non-collector monitoring/backfill scripts still make zero paid calls.
- Do not fabricate `SOURCE_NOT_CAPTURED` fields. Recover exact values only from point-in-time source rows/files, derive only from declared as-of market data, otherwise keep the blocker.
- Preserve append-only logs and deterministic row keys.
- Do not stage unrelated runtime dirt.

## Execution Order

1. `LTO-040` and `LTO-034`: queue integration and runbook/checklist generator.
2. `LTO-039`: verifier expansion for deeper semantic corruption checks.
3. `LTO-001` through `LTO-008`: candidate truth, path, structural, confluence, duplicate, V2b, V3, and FVG/OB core.
4. `LTO-005`, `LTO-015`, `LTO-025`, `LTO-026`: lifecycle and account-truth work.
5. `LTO-010` through `LTO-014` plus `LTO-030` through `LTO-033`: external feed, Sierra, Databento, proxy, source, and orderflow primitive work.
6. `LTO-021`, `LTO-022`, `LTO-036`, `LTO-037`, `LTO-038`: no-event proof, watchdog/notification/storage operations.
7. `LTO-016` through `LTO-020`: exit-policy, S79, regime/decay, decision diagnostics, and mechanical diagnostic joins.
8. `LTO-023`: owner-approved K55/ML target refresh plus read-only shadow inference; improve ML inputs with validated as-of features and paired labels, but keep zero decision impact.
9. `LTO-024`, `LTO-027`, `LTO-028`, `LTO-029`: approval/preregistration lanes.
10. `LTO-035`: observer hardening and expansion controls.

## Orderflow / Footprint / Volume-Profile Context

The owner added external discretionary context from a TikTok comment: traders often report that moving from pure ICT-style structure into orderflow with footprints, Sierra Chart, and volume profile can improve RR by sharpening entry timing, stop/invalidation placement, and target expansion. This context is already included in the plan. Treat it as a hypothesis and design requirement, not evidence, and continue implementation without re-asking whether it was considered.

When resuming the goal, keep this hypothesis active in the external-feed/orderflow items:

- `LTO-012` / `LTO-013`: Sierra `.depth` and source/parity registry must convert local depth into usable or explicitly blocked market-awareness features.
- `LTO-030`: Sierra `.scid` / 6B / SI work should prepare footprint-style bid/ask volume, delta, and volume-profile source semantics.
- `LTO-033`: orderflow primitives should include footprint delta/absorption, stacked imbalance, profile POC/VAH/VAL/HVN/LVN context, depth thinness, liquidity pulls, and wall concentration.
- `LTO-011`: NAS100/NQ adverse-selection diagnostics should test whether orderflow helps entry timing, bad-condition vetoes, and target/RR expansion around the same GTOS structural setup.

Boundary: this does not replace GTOS OB/FVG/breaker structure and does not authorize live signal, prompt, risk, execution, or order behavior changes. Promote only after pre-registered shadow evidence is joined to broker actual-R, cost/slippage, and lifecycle truth, with separate owner approval.

## K55 / ML Improvement Context

The owner approved adding K55 target refresh and read-only ML shadow inference to the active task list on 2026-05-05. The goal is not only better capture infrastructure; it is also to improve the ML substrate by feeding it cleaner, richer, as-of features from candidate structure, strategy state, lifecycle truth, account evidence classes, regime/decay, Sierra/Databento/orderflow, volatility/session context, mechanical comparators, and diagnostics.

ML improvement is a first-class goal for this queue. For each LTO item, ask whether its output should become:

- a model feature,
- a feature freshness/provenance flag,
- a target/label quality input,
- a sample eligibility/no-leak flag,
- a paired AI-vs-ML comparison field,
- or a blocker proving why the data cannot safely feed ML yet.

Boundary: ML rows may run in parallel as shadow evidence only. They must carry model/target/feature-bundle versions, source freshness/provenance, no-leak checks, and no-action counters. They must not affect AI decisions, execution, sizing, prompts, safety gates, or order placement until a separate promotion dossier proves lift on unseen paired rows and receives owner approval.

## Per-Item Completion Standard

For each LTO item:

1. Read current code/tests/artifacts first.
2. Implement the smallest correct reusable tool, logger, schema, verifier, report, or blocker artifact.
3. Add targeted tests.
4. Backfill existing 2026-05-04 data where honest, or write exact `SOURCE_NOT_CAPTURED`, `SOURCE_BLOCKED`, `APPROVAL_BLOCKED`, or `EVENT_WAITING` rows/reports.
5. Run targeted tests plus relevant verifiers.
6. Update a versioned report and, when the research map changes materially, `.context/00_core/research_current_state.md`.
7. Commit scoped files only.

## Stop Conditions

Stop and report if an item would require:

- live trading behavior change,
- prompt/risk/execution/safety-gate change,
- canary call,
- paid live data pull outside the registered LTO-010 Databento collector policy,
- unavailable credentials,
- legal/source access that is not locally available,
- owner approval not yet granted.

When stopped on one item, write the blocker artifact and continue to the next safe item.

## Approved Source-Unblocking Extension

The original LTO implementation goal closed with `LTO-031` and `LTO-032` documented as source-blocked rather than implementation-blocked. The owner has now approved continuing from that completed state into a source-unblocking and replay program for those two lanes.

Use this extension prompt and plan as the active continuation context:

- `.context/05_operations/LTO031_LTO032_SOURCE_UNBLOCKING_GOAL_EXTENSION_2026-05-05.md`
- `research/program_control/LTO031_LTO032_SOURCE_UNBLOCKING_AND_REPLAY_PLAN_2026-05-05.md`

The intent is to use free/public sources first, use Sierra data immediately where it adds market-awareness features, and use existing Databento historical credits for cost-capped counterfactual replay windows. This extension remains `NO_PROMOTION_VERDICT` and still forbids prompt, risk, execution, safety-gate, order, or live-decision behavior changes.
