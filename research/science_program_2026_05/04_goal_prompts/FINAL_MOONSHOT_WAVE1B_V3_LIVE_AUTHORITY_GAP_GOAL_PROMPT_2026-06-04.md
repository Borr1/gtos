# Final Moonshot Wave 1B V3 Live Authority Gap Goal Prompt

You are running Wave 1B of the final GTOS/vNext moonshot rebuild after the redacted_account hard halt.

This route answers a controlling question: what was true live authority at halt time, what was only V3 research/default-off/provenance, where did live behavior diverge, and what production code must change so the final system is not built on false V3 assumptions.

## Full Repo-Control Rule

This session has full control over repo changes on this research laptop. Change production code, live-behavior code, config, prompt surfaces, selector/scheduler/execution logic, risk and safety gates, canary/runtime behavior, profiles, launchers, tests, verifiers, replay builders, capture contracts, route artifacts, manifests, and integration packages to build the strongest final system.

When the V3/live audit proves a runtime or code gap, implement the change. Do not park necessary code work as a ledger. The repo build surface is fully open. Any older context line that makes production-code or live-behavior-code changes sound unavailable is stale for this final moonshot route.

Outside-route owner-action surfaces are broker account/order/history/deal/position mutation, live trading broker operation, paid API/vendor spending, credential mutation/disclosure, and remote publishing. Record exact action requirements when they appear and keep building every local repo, data, parser, verifier, code, test, and integration artifact. These outside-route surfaces are not limits on production-code or live-behavior-code changes in this worktree.

Builder posture: no conservative brake. Use constructive active creativity, curiosity, and rigorous evidence labeling to build the strongest auditable artifact set the repo can support.

## Mandatory Context Use

Start from current disk state. Run:

```powershell
python scripts\generate_live_state.py
```

Then read:

- `.context/LIVE_STATE.md`
- `.context/00_core/current_repo_reading_order.md`
- `.context/00_core/current_vnext_system_map.md`
- `.context/00_core/quick_reference_card.md`
- `.context/00_core/research_current_state.md`
- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/goal_session_research_discipline.md`
- `.context/00_core/final_moonshot_post_hard_halt_research_plan.md`
- `.context/00_core/final_moonshot_goal_session_execution_architecture.md`
- `.context/00_core/final_moonshot_central_orchestrator_successor_brief.md`
- `.context/02_session_handoffs/SESSION_64_FINAL_MOONSHOT_CENTRAL_ORCHESTRATOR_SUCCESSOR_2026-06-04.md`

Treat the doctrine files as active instructions, not background. Operationalize them into route ledgers, implementation decisions, saturation, and completion audit. Do not rely on chat memory.

After context compaction, resume, interruption, uncertainty, or tool failure, regenerate `LIVE_STATE`, reread this starter, this controlling prompt, the doctrine files, current route artifacts, and continue from disk evidence.

## Owned Evidence Class

Wave 1B owns live authority evidence, default-off research evidence, production code evidence, committed package evidence, uncommitted worktree dirt, source gaps, non-generatable historical truth, and prospective capture requirements. It also owns the code/config/test/verifier implementation needed to repair V3/live authority mismatch in the repo.

Every claim must preserve evidence class: live authority, default-off research, production code, committed package, broker-real PnL/cash only when broker truth is joined, exact-R/proxy-R only when source-bound geometry is computed, replay result, simulation result, shadow result, source gap, non-generatable historical truth, or prospective capture requirement.

Result materialization is required: every component gets an implementation decision, branch decision, source-capture state, source-completeness state, and runtime disposition. Do not leave V3 packages as inert ledgers.

## Objective

Classify every material live candidate/trade/runtime decision from the hard-halt window and every V3 component as active live authority, partially active live authority, fallback live authority, hybrid live authority, provenance-only, default-off research, packet-present but not used, package-present but not wired, missing, divergent, or rejected by evidence.

Required V3 surfaces:

- Selector V3;
- Scheduler V3 and money-risk scheduling;
- Execution Policy V3;
- same-symbol lifecycle logic;
- cost/swap/slippage handling;
- exposure and correlation controls;
- halt semantics and runtime control;
- LiveDecisionPacket completeness;
- market whiteboard or state inputs;
- broker profile/spec/session authority;
- replay and capture contracts.

The output must decide what is active, what gets changed now, what gets staged, what gets rejected, and what becomes a Wave 2/3 input.

## Required Source Discovery

Use `rg` before relying on summaries. Required roots include:

- `research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03/`
- `research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/`
- `research/operations/vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02/`
- `research/operations/final_moonshot_live_failure_intelligence_2026_06_04/`
- `research/operations/final_moonshot_goal_session_execution_architecture_2026_06_04/`
- `shadow_logs/gtos_vnext_runtime_decisions.jsonl`
- `shadow_logs/gtos_vnext_replacement_monitoring.jsonl`
- `shadow_logs/pending_limit_lifecycle.jsonl`
- `pipeline_state/`
- `src/`
- `scripts/`
- `config/`
- `tests/`
- every V3 route, prompt, package, branch, commit, launcher, profile, and runtime artifact discovered by `rg`.

Inspect code before claiming behavior. Inspect commits and route artifacts before relying on stale summaries. If `LIVE_STATE` or curated context is stale, state what is stale and what disk evidence supersedes it.

## Finite Work Queue

1. Create or refresh `research/operations/final_moonshot_wave1b_v3_live_authority_gap_2026_06_04/`.
2. Create a context anchor with branch, HEAD, LIVE_STATE timestamp, mandatory reads, LFS/data status, and dirty/staged state.
3. Build searched-root, source-inventory, and component-inventory ledgers.
4. Build a code/runtime path map for selector, scheduler, execution, lifecycle, cost, exposure, halt, packet, profile, launcher, and replay surfaces.
5. Join material hard-halt runtime decisions/trades to their actual selector/scheduler/execution authority.
6. Classify each V3 component and each material live decision with the disposition taxonomy above.
7. Identify every mismatch between intended V3 design and live authority: selector authority, money-risk scheduling, packet completeness, broker-cost truth, exposure controls, halt semantics, target/stop/partial behavior, and source capture.
8. Implement production code, live-behavior code, tests, verifiers, profile changes, launcher changes, capture contracts, or prompt/config changes needed to repair the authority gap in the repo.
9. Produce implementation decisions for every material component.
10. Run validators, focused tests, and route audit.
11. Commit scoped prompt/artifact/code/test changes.

## Required Subagent Reviews

Use subagents as force multipliers with disjoint responsibilities. Preserve material intelligence in route-local `SUBAGENT_*.md` or `SUBAGENT_*.jsonl` artifacts. Required review classes:

- selector authority auditor;
- scheduler and money-risk auditor;
- execution policy and packet-completeness auditor;
- halt semantics and runtime-control auditor;
- production-code implementation/scope auditor;
- saturation and prompt-language hardening auditor.

If the runtime has no separate subagent tool, perform the same reviews serially and save the same `SUBAGENT_*` artifacts.

## Terminal Artifacts

Produce at minimum:

- `WAVE1B_CONTEXT_ANCHOR.json`
- `WAVE1B_SEARCHED_ROOT_LEDGER.jsonl`
- `WAVE1B_SOURCE_INVENTORY.jsonl`
- `WAVE1B_COMPONENT_INVENTORY.jsonl`
- `WAVE1B_CODE_RUNTIME_PATH_MAP.md`
- `LIVE_CANDIDATE_AUTHORITY_MATRIX.jsonl`
- `V3_COMPONENT_RUNTIME_DISPOSITION_LEDGER.jsonl`
- `SELECTOR_AUTHORITY_GAP_LEDGER.jsonl`
- `SCHEDULER_MONEY_RISK_GAP_LEDGER.jsonl`
- `EXECUTION_POLICY_GAP_LEDGER.jsonl`
- `LIVE_DECISION_PACKET_COMPLETENESS_LEDGER.jsonl`
- `COST_SWAP_SLIPPAGE_AUTHORITY_LEDGER.jsonl`
- `EXPOSURE_AND_CLUSTER_AUTHORITY_LEDGER.jsonl`
- `HALT_SEMANTICS_AND_RUNTIME_CONTROL_LEDGER.jsonl`
- `PRODUCTION_CODE_CHANGE_LEDGER.jsonl`
- `IMPLEMENTATION_DECISION_LEDGER.jsonl`
- `WAVE1B_AUTHORITY_GAP_SUMMARY.md`
- `WAVE1B_SATURATION_AND_SELF_RED_TEAM.md`
- `WAVE1B_VERIFICATION_RESULT.json`
- `WAVE1B_OUTPUT_MANIFEST.json`
- `WAVE1B_COMPLETION_AUDIT.md`

If an artifact name changes, record the replacement in the manifest and route-decision ledger.

## Material Coverage Rules

No arbitrary top-N, top 3/5/10, number-limited cutoff, representative-only sample, compact-only summary, or summary-only closure. Full ledger and all material rows must be preserved before rankings.

Full same-evidence-class pursuit is mandatory. Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action inside the owned evidence class has been attempted or proven inapplicable from disk evidence.

Same-evidence-class blockers are not completion. Repair before handoff. Source gaps require searched-root proof and exact prospective capture requirements.

## Verification

Run at minimum:

```powershell
python scripts\audit_goal_route_artifacts.py research\operations\final_moonshot_wave1b_v3_live_authority_gap_2026_06_04 --full-jsonl
python scripts\validate_goal_prompt_hardening.py research\science_program_2026_05\04_goal_prompts\FINAL_MOONSHOT_WAVE1B_V3_LIVE_AUTHORITY_GAP_GOAL_PROMPT_2026-06-04.md
```

Run focused `pytest` or `python -m py_compile` for every changed parser, joiner, verifier, runtime component, or production-code file. Record exact command, exit code, and material output in `WAVE1B_VERIFICATION_RESULT.json`.

## Completion Audit

Mark complete only when the completion audit proves mandatory context was read from disk, no chat memory was used as evidence, the full repo-control rule was applied, stale restrictive implementation language was not imported, every material V3 component received a runtime disposition, every material hard-halt live candidate/trade/runtime decision received an authority classification, production code/live-behavior code/parsers/tests/verifiers changed where needed, source-capture/source-completeness/branch-decision/implementation-decision fields are present, full ledgers preserve all material rows, source gaps are repaired or proven non-generatable with exact capture requirements, verifier/tests ran or exact environment friction is recorded, staged paths and LFS/storage scope were inspected, a scoped commit exists or exact uncommitted state is recorded, and next Wave 2/3 inputs are exact evidence-class labeled decisions.
