# VNEXT VPS V3 Full Promotion And FTMO Setup Goal Prompt

Date: 2026-06-02
Evidence class: VPS production engineering, runtime integration, broker-profile verification, default-off package consumption, supervisor setup, rollback proof, and scoped deployment readiness.
Branch to consume on VPS: `origin/vnext-vps-ftmo-v3-clean-deploy-2026-06-02`.

## Objective

Turn the pushed clean deploy branch into a verified VPS production package that consumes the Selector V3, Scheduler V3, and Execution Policy V3 packages, wires them into the live runtime as scoped production authority with rollback proof, preserves redacted_account production continuity, and sets up FTMO as a separate broker/account namespace ready for owner-controlled activation.

This is not a report-only route and not another replay lane. Build, inspect, repair, test, verify, commit, and push the scoped VPS production package. If a defect, stale assumption, missing source, profile mismatch, namespace collision, risk mismatch, packet gap, supervisor gap, rollback gap, or runtime incompatibility appears, pursue and repair it inside this goal until it is closed, proven impossible from approved inputs, or reduced to an exact owner/account/manual-input requirement.

The clean deploy branch already carries the deploy-relevant code, profiles, verifiers, FTMO prep package, broker truth helper, and compact V3 default-off packages. Heavy moonshot research LFS ledgers are not prerequisites for this VPS production integration. If any large research file is claimed as required, prove the exact code path, field, package, or verifier that needs it and record the smallest exact transfer requirement.

This is a constructive production-engineering builder prompt with no conservative brake. Curiosity and active creativity apply to implementation quality: search all current code paths, supervisors, profiles, launchers, packet builders, verifiers, logs, and process evidence that can make the VPS package stronger, safer to operate, easier to roll back, and less stale. The task has no arbitrary top-N cutoff and no number-limited cutoff: preserve all material rows, all material defects, all material branch decisions, and all material production-change risks in the full ledger set before summarizing.

Literal impossibility means exactly this: every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action inside this VPS production-engineering evidence class has been attempted or proven unavailable from approved inputs. Full same-evidence-class pursuit is mandatory before any blocker is terminal.

## Mandatory Preflight And Re-Anchor

Start from disk, not chat memory.

1. Fetch all remotes and inspect the current VPS branch, current HEAD, and active process state.
2. Checkout or update a scoped VPS worktree/branch from `origin/vnext-vps-ftmo-v3-clean-deploy-2026-06-02`.
3. Run `python scripts/generate_live_state.py` or `py -3 scripts\generate_live_state.py`.
4. Read `.context/LIVE_STATE.md`.
5. Read `.context/00_core/current_vnext_system_map.md`.
6. Read `.context/00_core/current_repo_reading_order.md`.
7. Read `.context/00_core/quick_reference_card.md`.
8. Read `.context/00_core/goal_session_research_discipline.md`.
9. Read `.context/00_core/research_operating_doctrine.md`.
10. Read `.context/00_core/orchestrator_successor_operating_brief.md`.
11. Read `.context/00_core/orchestrator_methodology_hardening_controls.md`.
12. Read `.context/00_core/parallel_goal_merge_playbook.md`.
13. Read this controlling prompt and the one-line starter from disk after every context compaction, resume, interruption, uncertainty, command failure, merge conflict, or branch update.

Do not rely on chat memory. Treat the context files above as active instructions, not background. Operationalize them into the route objective, source inventory, work queue, instruction-coverage audit, route ledgers, verification matrix, completion audit, and closeout.

Treat `.context/00_core/research_current_state.md` as a curated snapshot only. If `LIVE_STATE` marks it stale, inspect the newer route artifacts directly.

## Required Current Evidence To Read

Read these files before changing code:

- `research/operations/vnext_vps_ftmo_v3_clean_deploy_package_2026_06_02/CLEAN_DEPLOY_HANDOFF.md`
- `research/operations/vnext_vps_ftmo_v3_clean_deploy_package_2026_06_02/CLEAN_DEPLOY_SCOPE_LEDGER.jsonl`
- `research/operations/vnext_vps_ftmo_v3_clean_deploy_package_2026_06_02/CLEAN_DEPLOY_VERIFICATION_RESULT.json`
- `research/operations/vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02/VPS_DUAL_PRODUCTION_IMPLEMENTATION_CONTRACT.md`
- `research/operations/vnext_ftmo_local_profile_and_vps_dual_prod_prep_2026_06_02/COMPLETION_AUDIT.json`
- `config/profiles/redacted_account.yaml`
- `config/profiles/operator_profile.yaml`
- `config/profiles/ftmo.yaml`
- `research/operations/vnext_absolute_moonshot_selector_v3_2026_06_01/SELECTOR_V3_DEFAULT_OFF_PACKAGE.json`
- `research/operations/vnext_absolute_moonshot_selector_v3_2026_06_01/SELECTOR_V3_RUNTIME_PACKET_SCHEMA.json`
- `research/operations/vnext_absolute_moonshot_scheduler_v3_2026_06_01/SCHEDULER_V3_DEFAULT_OFF_PACKAGE.json`
- `research/operations/vnext_absolute_moonshot_execution_policy_v3_2026_06_01/V3_DEFAULT_OFF_EXECUTION_POLICY_PACKAGE.json`
- current VPS live supervisor handoff/evidence under `research/operations/vnext_vps_live_activation_active_supervisor_2026_06_01/` when present on the VPS
- current process commands, watchdog scripts, lock files, `pipeline_state`, `shadow_logs`, `data/m1`, `data/ticks`, `knowledge_base`, and active MT5 terminal paths on the VPS

Examples are not limits. Search any additional code, config, tests, routes, logs, and artifacts required to prove the production package.

## Production Engineering Scope

Implement the full production path needed for V3 and dual broker operation:

1. **Repository and branch convergence**
   - Consume the clean deploy branch.
   - Preserve the latest VPS live fixes already pushed to the source branch.
   - Resolve conflicts by reading current runtime code and preserving the stronger current behavior.
   - Keep scoped production commits and push them to the working branch.

2. **redacted_account continuity**
   - Verify the redacted_account profile, terminal path, account identity, symbol aliases, symbol specs, account currency, account size, and runtime namespace.
   - Verify that redacted_account open positions, pending orders, locks, checkpoints, pending intents, M1/tick roots, notification queue, trade records, and broker truth logs remain namespaced and coherent.
   - Prove that the package does not downgrade current redacted_account live supervisor, watcher, M1/tick capture, malformed OHLC repair, Stage13 risk evidence, or broker-truth capture behavior.

3. **FTMO setup**
   - Verify the FTMO profile against the VPS FTMO MT5 terminal and actual logged-in account.
   - If the VPS lacks FTMO terminal/account proof, write the exact terminal/account export requirement and keep FTMO in a verified staged state.
   - Ensure FTMO uses a distinct namespace, process group, terminal path, data path, logs root, M1 root, tick root, knowledge base root, pipeline state root, broker truth log, lock pattern, checkpoint path, pending-intent path, and Telegram identity prefix.
   - Verify all 24 vNext symbols resolve through FTMO aliases and broker-native specs.
   - Preserve credentials outside git. Profile identity uses redacted values and SHA-256 account proof only.

4. **Selector V3 production wiring**
   - Load the Selector V3 package from disk with version/hash/provenance proof.
   - Replace stale hardcoded two-rule or prior-package behavior with package-driven V3 behavior where code still depends on old selectors.
   - Ensure runtime candidate packets carry Selector V3 proof, action, rule id, mechanism identity, confidence/quality evidence, source completeness, exact/proxy boundary, and refusal/action reason.
   - Verify all Selector V3 actions are handled: `trade`, `reduce_risk`, `avoid`, `capture_repair`, `no_trade_by_evidence`, and `source_required`.

5. **Scheduler V3 production wiring**
   - Load the Scheduler V3 package from disk with version/hash/provenance proof.
   - Make account-risk exposure the scheduler authority: balance/equity, day-start baseline, realized PnL, open risk, pending risk, new risk, selected-cell risk, symbol risk, portfolio buffers, daily/overall challenge limits, same-symbol conflict state, and correlated exposure.
   - Static max-trade/count caps may remain as evidence fields or emergency hard limits, not as stale primary authority over valid V3 rows.
   - Verify Scheduler V3 can reduce risk, reject correctly, admit correctly, and record exact money-risk reasoning per account namespace.

6. **Execution Policy V3 production wiring**
   - Load the Execution Policy V3 package from disk with version/hash/provenance proof.
   - Route execution policy by V3 selector/scheduler context rather than relying only on old global defaults.
   - Preserve current `momentum_exhaustion` and `partial_be_runner` behavior when V3 chooses those paths, and implement the additional V3 policy-router decisions only where the package and tests prove support.
   - Enforce ticket-bound lifecycle management, partial close residual identity, SL/TP modify diagnostics, broker stop/freeze checks, retcode/request_id/retcode_external capture, and false-close prevention.

7. **Supervisor, launcher, and namespace control**
   - Update launchers/watchdogs/supervisor scripts so redacted_account and FTMO can run as separate process groups without lock, heartbeat, log, data, queue, or checkpoint collision.
   - Add or repair dry-run/mock/no-order launch checks for both namespaces.
   - Verify `run_agent.py`, M1 capture, tick capture, orchestrator, execution, MT5 interface, and supervisor receive the correct `--runtime-namespace`, broker profile, and terminal path.

8. **Data and packet capture**
   - Verify all production-required reference files exist on the VPS or are generated by the route.
   - Verify M1/tick capture roots are namespaced and producing/ready to produce data for both broker profiles.
   - Verify candidate, gate, risk, scheduler, execution, broker truth, Telegram, and lifecycle packets have no silent nulls, no generic source gaps, and exact reasons for absent fields.

9. **Rollback and deployment control**
   - Build rollback scripts/proof for namespace-specific stop/reload.
   - redacted_account rollback must not stop FTMO, and FTMO rollback must not stop redacted_account.
   - Produce an activation checklist that states exactly what is active now, what is staged, what command reloads or starts each namespace, what command stops each namespace, and which verifier must pass before each command.

## Subagent Use

Use subagents or equivalent independent audit passes aggressively when available. Split the work by evidence family so each pass has a sharp objective and no duplicate loops:

- VPS runtime/process/supervisor audit
- redacted_account profile and continuity audit
- FTMO profile/account/symbol/spec audit
- Selector V3 runtime wiring audit
- Scheduler V3 risk/exposure audit
- Execution Policy V3 lifecycle/order-management audit
- Data/packet/no-null audit
- Test/verifier/rollback audit

Merge findings through a route-local work queue and decision ledger. A shard is closed only when its source hash/state is recorded and the verifier/test/proof has passed. Reopen a shard only when source hash changed or a validator identifies a concrete gap.

## Required Route Artifacts

Create a route under:

`research/operations/vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02/`

Required outputs:

- `VPS_V3_FTMO_CONTEXT_ANCHOR.md`
- `VPS_V3_FTMO_SOURCE_INVENTORY.jsonl`
- `VPS_V3_FTMO_BRANCH_CONVERGENCE_LEDGER.jsonl`
- `VPS_V3_FTMO_PROFILE_VERIFICATION_LEDGER.jsonl`
- `VPS_V3_FTMO_V3_PACKAGE_CONSUMPTION_LEDGER.jsonl`
- `VPS_V3_FTMO_RUNTIME_WIRING_LEDGER.jsonl`
- `VPS_V3_FTMO_RISK_SCHEDULER_LEDGER.jsonl`
- `VPS_V3_FTMO_EXECUTION_POLICY_LEDGER.jsonl`
- `VPS_V3_FTMO_NAMESPACE_AND_SUPERVISOR_LEDGER.jsonl`
- `VPS_V3_FTMO_PACKET_COMPLETENESS_LEDGER.jsonl`
- `VPS_V3_FTMO_ROLLBACK_AND_ACTIVATION_PLAN.md`
- `VPS_V3_FTMO_VERIFICATION_RESULT.json`
- `VPS_V3_FTMO_COMPLETION_AUDIT.json`
- `VPS_V3_FTMO_OUTPUT_MANIFEST.json`
- a route-local verifier script
- focused tests for any changed runtime/config/verifier behavior

Add additional artifacts when needed. Every artifact must feed code/config verification, deployment readiness, rollback, or future troubleshooting. Repeated ledgers without new evidence are invalid.

Required result-use status fields in route artifacts: `evidence_class`, `production_change_status`, `runtime_effect_boundary`, `source_capture_status`, `implementation_decision`, `branch_decision`, `exact_R_status`, `proxy_R_status`, `expectancy_status`, `broker_operation_status`, `live_trading_status`, and `remote_push_status`. Exact-R, proxy-R, and expectancy fields can be `not_applicable_to_this_production_engineering_goal` only when the artifact states why this route is code/config/profile/supervisor integration rather than replay scoring.

## Verification Matrix

Run the strongest available focused verification after implementation:

- `py_compile` for touched production code, scripts, and verifier files
- `scripts/verify_broker_profile.py` for redacted_account
- `scripts/verify_broker_profile.py` for FTMO when the FTMO terminal/account proof exists on VPS
- route-local verifier for this VPS V3/FTMO goal
- VPS supervisor verifier
- Stage13 or equivalent selected-cell/risk verifier
- focused pytest covering broker profile namespace, profile verifier, M1 capture, tick capture, orchestrator, execution, V3 selector, Scheduler V3, Execution Policy V3, broker truth cost capture, supervisor, and rollback helpers
- packet/no-null/provenance verifier for V3 runtime packets
- process/readiness check for all expected redacted_account and FTMO namespace processes after any owner-approved reload/start

If a listed verifier is not present on the branch, implement it or record the exact stronger existing verifier that covers the same production risk.

## Completion Standard

Mark this goal complete only when all are true:

1. Current VPS branch and clean deploy branch are reconciled.
2. redacted_account production continuity is verified from current VPS disk/process/profile evidence.
3. FTMO profile and namespace setup is verified or reduced to exact VPS terminal/account/export requirements.
4. Selector V3, Scheduler V3, and Execution Policy V3 are consumed from package files with version/hash/provenance proof.
5. Runtime code/config changes needed for V3 live authority are implemented, tested, and recorded.
6. Namespaces prevent redacted_account/FTMO collisions in logs, data, locks, checkpoints, pending intents, notification queues, and broker truth records.
7. Risk scheduling uses real account money-risk/exposure evidence and does not regress to stale count-cap authority.
8. Execution management remains ticket-bound and records actionable broker diagnostics.
9. Rollback and activation commands are exact and namespace-specific.
10. Required verifiers and focused tests pass, or a blocker is exact and externally owned.
11. Route artifacts, completion audit, and manifest prove closure.
12. Scoped commits are created and pushed to the working branch.
13. Closeout reports exact active/staged state for redacted_account, FTMO, Selector V3, Scheduler V3, Execution Policy V3, supervisor, rollback, tests, and remaining owner actions.

## Explicit Authority And Boundaries

CEO authorizes this goal to edit production code, production config, tests, verifiers, launchers, supervisor scripts, broker-profile files, default-off package loaders, runtime packet schemas, risk/scheduler integration, execution-policy routing, route artifacts, and context files when needed to complete the objective.

CEO authorizes scoped commits and remote pushes for this goal's branch after verification.

Broker/account mutation boundary: no order/deal/position action is part of this goal. Runtime reload/start/stop of order-capable processes is allowed only when the owner gives the explicit VPS-session command for that action or when a process-control action is required to inspect/repair a non-order-capable verifier. Read-only MT5 account/profile/symbol/spec/history inspection is part of this goal.

Credentials remain unprinted and uncommitted. Paid/vendor/API calls stay outside this goal unless the owner gives a separate explicit command.

## Saturation And Self-Red-Team

Before completion, perform a written saturation pass in the route audit:

- Which stale live assumptions from the VPS branch could override V3?
- Which local V3 package assumptions could conflict with current VPS production fixes?
- Which redacted_account paths could accidentally use FTMO data, locks, terminal path, queue, checkpoint, or profile?
- Which FTMO paths could accidentally use redacted_account data, locks, terminal path, queue, checkpoint, or profile?
- Which selector action can fall through silently?
- Which scheduler decision can lose money-risk proof or revert to count caps?
- Which execution policy can select a policy that the live order manager cannot actually manage?
- Which packet fields can become null, generic, stale, or misleading?
- Which rollback command can kill the wrong namespace?
- Which verifier could pass while the runtime would still use old behavior?
- Which heavy research file is assumed necessary, and what proof shows it is or is not required?
- Which owner/account/manual requirement remains exact and actionable?

If the saturation pass exposes a repairable same-evidence-class gap, repair it before marking complete.
