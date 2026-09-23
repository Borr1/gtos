# vNext VPS Live + Local V3/FTMO Production Integration

Own the production-code integration route that combines the VPS live production truth with the local V3/FTMO/moonshot production-ready work. This is production engineering. The output must be a coherent deployable branch, scoped route evidence, verifiers, tests, and a VPS handoff that can be pulled into the live machine.

The goal is to move the strongest current moonshot system toward live production, not to keep V3 trapped as research ledgers. The route has explicit owner authority for local production-code, runtime-code, config, profile, verifier, launcher, watchdog, supervisor, test, and deployment-handoff changes required to make the integrated system coherent and deployable. This authority covers changing live-facing code and production configuration in the integration branch when the change is required and verified.

## Mandatory Context Use

Run mandatory GTOS preflight from disk before using memory:

1. Regenerate `.context/LIVE_STATE.md`.
2. Read `AGENTS.md`.
3. Read `.context/LIVE_STATE.md`.
4. Read `.context/00_core/current_vnext_system_map.md`.
5. Read `.context/00_core/current_repo_reading_order.md`.
6. Read `.context/00_core/quick_reference_card.md`.
7. Read `.context/00_core/research_current_state.md`.
8. Read `.context/00_core/goal_session_research_discipline.md`.
9. Read `.context/00_core/research_operating_doctrine.md`.
10. Read `.context/00_core/orchestrator_methodology_hardening_controls.md`.
11. Read `.context/00_core/parallel_goal_merge_playbook.md`.
12. Read `.context/00_core/vnext_absolute_moonshot_vision_and_limitations.md`.

Treat these files as active instructions. Carry their requirements into the route context anchor, searched-root ledger, branch-decision ledger, implementation decision ledger, conflict-resolution ledger, verifier matrix, saturation pass, completion audit, and final handoff. Do not rely on chat memory. Chat memory is context only; disk evidence controls.

Apply constructive production-integration builder posture: curiosity, active creativity, and no conservative brake inside this evidence class. The route is allowed to change production code when the change is required by current disk evidence and verification.

Operationalize full same-evidence-class pursuit. Literal impossibility means exactly that every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action available inside this production-integration evidence class has been attempted or proven inapplicable.

After compaction, resume, interruption, long wait, tool failure, LFS failure, merge conflict, or uncertainty, regenerate `LIVE_STATE`, reread this prompt, reread the one-line starter, reread the doctrine files above, reread current route artifacts, and continue from the recorded route state.

## Current Branch Anchors To Verify

Inspect current disk before branching. The following are anchors to verify, not facts to trust after context compaction or later commits:

- VPS production branch: `origin/vps-prod-live-sync-2026-06-02`.
- Local production/research branch expected to contain post-V3 moonshot and FTMO work.
- VPS branch expected to contain live production sync truth, supervisor/watchdog/Stage13/canary-removal/runtime fixes, and VPS handoff/classification artifacts.

Do not assume current branch, HEAD, divergence, commit hash, live process count, broker state, route completion state, or dirty-path state from this prompt. Verify them from disk with current Git commands and route artifacts, then update the route context anchor with current hashes, branch names, divergence, and artifact paths before editing.

## Objective

Create a production integration route under:

`research/operations/vnext_vps_local_v3_ftmo_production_integration_2026_06_02/`

Create or move to a scoped integration branch, recommended name:

`vnext-prod-integration-vps-v3-ftmo-2026-06-02`

The integration branch must combine:

- VPS live production fixes and runtime truth from `origin/vps-prod-live-sync-2026-06-02`.
- Local V3/FTMO/moonshot production-ready code, config, tests, verifiers, and deployment handoff material.
- Current vNext production truth: 24-symbol vNext/moonshot replacement, selected-cell proof, account-risk exposure, ticket-bound lifecycle, broker-truth cost capture, and no old PA/L2 or stale fixed-policy authority.

The branch must exclude large research-only LFS ledgers unless the file is required for runtime, deployment reproducibility, profile verification, production verifier execution, or production handoff. Preserve local research evidence by reference, route manifest, commit hash, path pointer, or existing local route, but do not drag raw research ledgers into the production branch as a side effect.

## Required VPS Production Review

Before editing conflict files, fully inspect the VPS branch from disk. Build a VPS production change inventory that records file, commit/source, behavior changed, production reason, tests/verifiers, and integration disposition.

Minimum VPS production surfaces to inspect:

- supervisor, watchdog, launcher, and heartbeat changes;
- Stage13 selected-cell risk proof and reporting repair;
- separation of configured profile risk from effective selected-cell risk;
- canary removal and any canary reference neutralization;
- live reload and process proof artifacts;
- runtime repairs in orchestrator and GTOS vNext runtime;
- execution diagnostics and lifecycle fixes;
- M1 capture and tick capture behavior;
- notification, displacement, monitoring, and supervisor surfaces;
- VPS sync handoff and dirty-path classification artifacts;
- tests and verifiers shipped by the VPS branch.

The inventory must explain what issue each VPS production change solved, why the issue happened, what code path changed, how the fix is verified, and whether the local branch contains overlapping work.

## Required Local V3/FTMO Review

Before editing conflict files, fully inspect the local production-relevant V3/FTMO work from disk. Build a local production-change inventory that records file, route/source, behavior changed, production relevance, tests/verifiers, and integration disposition.

Minimum local surfaces to inspect:

- Selector V3 default-off package and runtime wiring points;
- Scheduler V3 account-risk, portfolio scheduling, correlation, blocked-edge recovery, and default-off package;
- Execution Policy V3 package, policy registry, routing rows, split/stress evidence, and runtime requirements;
- Source Capture Repair outputs where they affect runtime packet completeness, capture contracts, or production verifier requirements;
- post-V3 Master state and launch decisions;
- FTMO profile `config/profiles/operator_profile.yaml`;
- FTMO compatibility pointer `config/profiles/ftmo.yaml`;
- redacted_account/current profile expectations;
- broker profile verifier and namespace tests;
- VPS dual-production implementation contract from the FTMO prep route;
- production code touched by V3, FTMO, Source Capture Repair, and Master refreshes.

The inventory must explain which local changes are production code, which are default-off packages, which are route evidence only, and which files must stay out of the production branch because they are large research-only artifacts.

## Subagent Work Plan

Use subagents or equivalent isolated review passes. Assign clear shards so no agent repeats the same work without new evidence.

Required roles:

- VPS production auditor: inspect `origin/vps-prod-live-sync-2026-06-02`, inventory production changes, explain issue/fix/test relationships, and identify merge-sensitive files.
- Local V3/FTMO auditor: inspect local V3/FTMO production-ready code and contracts, classify runtime versus research-only files, and identify exact files to port.
- Conflict integrator: resolve Git conflicts and semantic overlaps line by line, preserving both production truth sets.
- Verifier architect: build the verification matrix, run tests, classify failures, repair code failures, and record VPS-only verification requirements where local inputs are unavailable.
- LFS/scope auditor: prove the production branch excludes raw research LFS ledgers and includes every required deployable code/config/test/verifier/context file.

The main session owns final judgment. Subagent findings are evidence inputs, not automatic decisions.

## Integration Requirements

Build one coherent production surface. Preserve the VPS live stability fixes and add local production-ready V3/FTMO code paths.

Conflict files requiring line-level review:

- `src/components/execution.py`
- `src/components/m1_capture.py`
- `src/components/tick_capture.py`

Semantic-overlap files requiring direct review even if Git reports no conflict:

- `src/components/orchestrator.py`
- `src/components/gtos_vnext_runtime.py`
- `src/safety/heartbeat_monitor.py`
- `scripts/watchdog.ps1`
- `config/agent_config.yaml`
- `run_agent.py`
- `config/profiles/*`
- production launch scripts;
- production supervisor/verifier scripts;
- tests touching execution, M1/tick capture, broker profiles, runtime routing, Stage13 risk proof, VPS supervisor, and V3 package contracts.

Integration decisions must be explicit:

- preserve VPS behavior;
- port local behavior;
- combine both;
- default-off wiring;
- production-active wiring;
- reject stale local behavior;
- reject stale VPS behavior;
- defer only when the missing input is exact and belongs to VPS-local verification or deployment.

## V3 Activation And Runtime Posture

The integration route must move V3 toward live deployability.

If a V3 component is ready for production activation, wire it with explicit config authority, verifier coverage, runtime evidence, and rollback path.

If a V3 component needs staged activation, implement the exact default-off or staged production wiring so the VPS can run current stable production while V3 paths are available, testable, observable, and promotion-ready.

If a V3 component must remain research-only, record the exact missing production requirement and keep the runtime boundary machine-checkable.

Do not let V3 collapse into summary artifacts. Selector V3, Scheduler V3, and Execution Policy V3 must have clear production-code disposition.

## FTMO And redacted_account Dual-Production Requirements

Integrate FTMO profile support beside redacted_account without breaking redacted_account.

Broker/account profile fields must remain profile-bound:

- symbol aliases;
- broker-native symbols;
- tick size;
- contract size;
- lot step/min/max;
- stop level;
- freeze level;
- spread handling;
- sessions;
- commission/swap assumptions where available;
- margin/tick value requirements;
- account stage and drawdown limits;
- risk overlays;
- profile-specific verifier expectations.

The integrated branch must support VPS deployment where redacted_account is already live and FTMO is added as a second production target. Any missing VPS-local export, account-stage confirmation, MT5 login proof, or broker-terminal requirement must be recorded as an exact deployment requirement, not a vague blocker.

## Risk, Execution, And Lifecycle Requirements

Preserve corrected production truth:

- live sizing separates configured profile risk from effective selected-cell risk;
- selected-cell proof is explicit;
- account-risk exposure governs portfolio acceptance;
- stale count caps, stale max-trades authority, and old fixed-risk labels do not govern valid vNext trades;
- old fixed `1.5R`, J46/J49, BE-only, and old PA/L2 production authority do not re-enter current vNext runtime;
- ticket-bound lifecycle management remains intact;
- partial-close residual resolution remains ticket/symbol/side/magic/volume/broker-response aware;
- broker-truth cost capture stays separate from projected/local PnL;
- false-close handling and broker close/deal reconciliation remain explicit;
- Stage13 evidence reports configured profile risk and effective selected-cell risk separately.

Any code path that violates these requirements must be repaired in the integration branch.

## LFS And Production-Branch Scope Requirements

The repo has large research LFS evidence and an LFS budget constraint. The production integration branch must be scoped.

Include:

- deployable production code;
- production config and broker profiles;
- production launch/supervisor/watchdog scripts;
- runtime packet schemas where required by production tests;
- focused tests and verifiers;
- route-local integration evidence;
- small context/handoff files required for VPS deployment;
- production profile verification artifacts.

Exclude:

- raw research-only JSONL/JSONL.GZ ledgers;
- large route outputs not required by runtime or production verifier execution;
- historical broad replay ledgers not needed by VPS deployment;
- stale archived reports;
- unrelated runtime dirt and shadow logs unless directly required by the integration route.

Record every included and excluded path family in the LFS/scope ledger. If an LFS pointer is required for production, prove why. If a research artifact is referenced but not included, record the source commit/path/manifest pointer that preserves recoverability.

No arbitrary top-N, no top 3/5/10, no representative-only cutoff, and no number-limited cutoff may replace evidence. A ranked summary is allowed only after a full ledger preserves all material rows, path families, branch decisions, source completeness decisions, and implementation decisions.

## Verification Matrix

Run focused verification that proves the merged production surface. Minimum checks:

- execution tests;
- M1 capture tests;
- tick capture tests;
- broker truth/cost capture tests;
- FTMO profile verifier;
- redacted_account/current profile verifier;
- broker profile namespace tests;
- Selector V3 package/verifier tests where production-relevant;
- Scheduler V3 package/verifier tests where production-relevant;
- Execution Policy V3 package/verifier tests where production-relevant;
- Stage13 risk proof verifier;
- VPS supervisor verifier;
- launcher/watchdog static checks or tests;
- runtime/router/orchestrator focused tests;
- prompt/config/runtime parse checks;
- route artifact JSON/JSONL parse checks for the integration route;
- `git diff --check`;
- scoped staged-path review before commit.

If a verifier fails because of code, repair the code and rerun the relevant checks. If a verifier requires VPS-only broker/terminal input, record the exact VPS-side command, file, expected proof, and deployment gate.

## Required Artifacts

Write route outputs under:

`research/operations/vnext_vps_local_v3_ftmo_production_integration_2026_06_02/`

Required artifacts:

- `INTEGRATION_CONTEXT_ANCHOR.md`
- `VPS_PRODUCTION_CHANGE_INVENTORY.jsonl`
- `LOCAL_V3_FTMO_PRODUCTION_CHANGE_INVENTORY.jsonl`
- `BRANCH_BASE_AND_DIVERGENCE_LEDGER.json`
- `CONFLICT_RESOLUTION_LEDGER.jsonl`
- `SEMANTIC_OVERLAP_REVIEW_LEDGER.jsonl`
- `RUNTIME_BEHAVIOR_MAP_AFTER_INTEGRATION.json`
- `redacted_account_FTMO_PROFILE_COMPATIBILITY_LEDGER.jsonl`
- `V3_RUNTIME_DISPOSITION_LEDGER.jsonl`
- `RISK_EXECUTION_LIFECYCLE_INVARIANT_LEDGER.jsonl`
- `LFS_AND_PRODUCTION_SCOPE_LEDGER.jsonl`
- `VERIFICATION_MATRIX.json`
- `VERIFICATION_RESULT.json`
- `VPS_DEPLOYMENT_HANDOFF.md`
- `OUTPUT_MANIFEST.json`
- `COMPLETION_AUDIT.json`

The route must include result-use status and result materialization status for every V3/FTMO production-relevant component. Where exact-R, proxy-R, or expectancy evidence is owned by the integrated component or its upstream route, record the exact source and runtime-use boundary. Where result metrics are not runtime authority, record that boundary instead of dropping the intelligence. Source-capture decisions, source completeness decisions, branch decisions, and implementation decisions must be machine-readable.

Add a route verifier and focused tests where useful. Existing verifiers may be reused, but the route must still have its own completion audit and verifier result.

## Saturation And Self-Red-Team Pass

Before completion, run a written saturation pass and pursue every same-evidence-class gap it exposes.

Answer with evidence:

- What exact VPS live issue did each VPS production change fix?
- Which VPS changes would be lost by a naive local-main merge?
- Which local V3/FTMO changes would be lost by a naive VPS-branch deployment?
- Which files contain semantic overlap without Git conflicts?
- Which V3 components are production-active, staged default-off, or research-only after integration?
- Which FTMO requirements are fully local-ready and which require VPS-local terminal/account proof?
- Which redacted_account behavior could break from FTMO profile introduction?
- Which risk labels, selected-cell fields, configured-risk fields, and effective-risk fields can be confused?
- Which execution/lifecycle paths could regress wrong-ticket management, false close, or broker-truth separation?
- Which large LFS/research artifacts are excluded and how can future agents recover them?
- Which verification failures are real defects and which are exact VPS-only requirements?
- What branch/commit is deployable to VPS, and what exact VPS commands or checks come next?

If any answer exposes a feasible code repair, config repair, verifier repair, path-scope repair, merge repair, or source classification repair, complete it before marking the route done.

## Completion Standard

Completion requires:

- integration branch created and recorded;
- VPS production changes inventoried from disk;
- local V3/FTMO production-relevant changes inventoried from disk;
- conflicts resolved with line-level evidence;
- semantic overlaps reviewed;
- V3 runtime disposition recorded;
- FTMO and redacted_account profile compatibility recorded;
- risk/execution/lifecycle invariants checked;
- production branch scope and LFS exclusions proven;
- focused verifiers/tests run and failures repaired or reduced to exact VPS-only requirements;
- output manifest written;
- completion audit written;
- scoped commit created on the integration branch;
- final response records branch name, commit hash, changed files, verification results, VPS-only checks, and next VPS deployment instruction.

No arbitrary top-N, no representative-only closure, no broad research/LFS dump, no infinite rerun loop, no chat-only result, no unreviewed conflict resolution, no unscoped staging, no hidden production activation, no stale old-system authority, no V3-as-ledger-only closure.

## Hard Boundaries

Authorized in this route:

- local production-code edits;
- runtime-code edits;
- config/profile edits;
- default-off or staged V3 wiring;
- production verifier/test edits;
- launcher/watchdog/supervisor edits;
- route artifact creation;
- scoped commits on the integration branch;
- local read-only inspection of repo, Git history, branch diffs, and route evidence.

Deployment-stage surfaces requiring separate final owner action after the branch is ready:

- live broker/order/deal/position mutation;
- MT5 account mutation;
- live runtime restart or reload on the VPS;
- credential creation, printing, mutation, or disclosure;
- paid API/vendor calls;
- remote push if not explicitly approved in the active turn;
- enabling production-active V3/FTMO behavior on the VPS without the integration route handoff and verifier evidence.

These boundaries are execution control, not research or code brakes. Inside the authorized production-code integration class, pursue every required change until the branch is coherent, verified, and ready for VPS deployment.
