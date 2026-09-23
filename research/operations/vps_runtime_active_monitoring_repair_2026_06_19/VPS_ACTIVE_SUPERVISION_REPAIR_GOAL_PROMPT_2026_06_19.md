# VPS Active Supervision Repair Goal Prompt - 2026-06-19

## Objective

Run an active VPS production-code/runtime supervision, diagnosis, repair, and strengthening goal for the current GTOS ultimate-book package. This is not a passive health check. The session must continuously inspect the live-facing system, broker profiles, runtime packets, chronological flow, candidate behavior, active-trade management, research/context freshness, and every repairable limitation that could weaken the system. When it finds a real issue, stale detail, missing join, brittle verifier, broker-profile mismatch, chronology break, candidate weakness, profile gap, stale context claim, or implementation limitation, it must fix what can be fixed inside this evidence class and prove the repair.

The goal is to make the VPS system stronger, smarter, more observable, and more internally consistent. Green status is only a checkpoint. It is not completion by itself.

This is a constructive active creativity lane with no conservative brake inside the authorized production-code/runtime evidence class. The session should be curious and aggressive about weaknesses, opportunities, stale assumptions, and non-obvious repair paths while staying honest about forbidden surfaces and evidence boundaries.

## Evidence Class

This is a production-code/runtime supervision and repair lane. It may edit and verify live-facing code, config-reading logic, profiles, verifiers, tests, launchers, supervisors, watchdogs, context artifacts, monitoring artifacts, route ledgers, and prompt/config/risk/execution/safety/canary/selector diagnostics when the change is needed to strengthen the current package and can be proven safely from current disk/runtime evidence.

Authorized in this lane:

- read-only broker/account/order/history/deal/position inspection through existing MT5/VPS tooling;
- production-code repair for runtime evidence, packet generation, profile normalization, candidate/admission plumbing, book management, logging, route verifiers, and tests;
- config/profile/verifier/launcher/supervisor/watchdog repairs when the current runtime evidence proves the need;
- controlled process reload or restart when a code/runtime repair requires it or when a live process is unhealthy, with before/after config hashes, process IDs, packet samples, monitoring paths, and rollback proof;
- scoped commits and pushes for code, tests, verifiers, prompts, context, manifests, and evidence artifacts.

Still-forbidden or separately gated surfaces:

- no discretionary strategic trade decisions;
- no manual broker operation that mutates broker/account/order/history/deal/position state unless an immediate safety invariant requires emergency protection or the owner gives a separate explicit trade-management instruction in the active turn;
- no credential mutation or disclosure;
- no paid API/vendor call unless an exact pre-call manifest and owner approval exist;
- no broad remote history rewrite;
- no fabricated live, broker-real, candidate, placement, deal, or lifecycle truth.

If broker mutation is ever unavoidable for emergency safety, record the exact reason, ticket, command, before/after broker state, packet/log evidence, and rollback or non-rollback proof. Otherwise, repair the system and its evidence without touching broker state.

## Mandatory Preflight And Context Use

Do not rely on chat memory. Current disk wins.

Start with:

```powershell
git fetch origin
git branch --show-current
git rev-parse HEAD
git status --short
python scripts\generate_live_state.py
```

Then read, from disk, before making claims:

- `.context/LIVE_STATE.md`
- `.context/00_core/current_vnext_system_map.md`
- `.context/00_core/current_repo_reading_order.md`
- `.context/00_core/quick_reference_card.md`
- `.context/00_core/research_current_state.md`
- `.context/00_core/goal_session_research_discipline.md`
- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/orchestrator_successor_operating_brief.md`
- `.context/00_core/orchestrator_methodology_hardening_controls.md`
- `.context/00_core/parallel_goal_merge_playbook.md`
- the latest numbered file in `.context/02_session_handoffs/` as historical context only
- `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_MONITORING_REPAIR_EVIDENCE.md`
- `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/OUTPUT_MANIFEST.json`
- `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/COMPLETION_AUDIT.json`
- `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/SATURATION_SELF_RED_TEAM_AUDIT.json`
- `research/operations/final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18/VPS_CODEX_ULTIMATE_ACTIVATION_HANDOFF.md`
- `research/operations/final_moonshot_wave_e_runtime_learning_packet_parity_2026_06_18/VPS_CODEX_RUNTIME_LEARNING_PACKET_PROMPT.md`

These files are active instructions, not background. Operationalize them in the work, and include instruction-coverage in the completion audit: which files were read, which doctrine requirements were applied, which were inapplicable because they crossed a forbidden surface, and what exact evidence supports that classification.

After any context compaction, resume, interruption, tool crash, uncertainty, or branch change, regenerate `LIVE_STATE`, reread this prompt, the starter, the doctrine files, and latest route artifacts from disk before continuing.

## Current Runtime Anchors To Verify, Not Assume

Verify current disk/runtime state before asserting any of these:

- branch is `vps/ultimate-conditioned-expansion-minimal-2026-06-18` or a newer fast-forward from `origin` on the same branch;
- current package has ultimate book enabled/apply/live allowed;
- `selector_v4_apply_to_execution=false`;
- candidate book and conditioned market-expansion book are enabled;
- market-expansion policy is `positive_weighted12_after_swap`;
- profile is `clean3_w7_ceiling_nom2p00`;
- Kelly-lite, conservative Kelly, running-count sizing, smooth stress derisk, A8 metals gate, W7 dropped-symbol filter, runtime-learning packets, and conditioned market expansion are active;
- FTMO and redacted_account broker profiles have the expected direct-symbol support and fail-closed unsupported handling;
- active process state, task state, heartbeats, packet tail, broker positions, pending orders, and trade records agree.

If any anchor is stale, update the route artifact and repair the code/config/context that made it stale.

## Required Active Supervision Lanes

Run these as a recurring active cycle. Do not use arbitrary top-N, top 3/5/10, representative-only, or summary-only cutoffs. Preserve all material rows in full ledgers, then rank summaries only for readability.

1. Process and scheduler health:
   - inspect Windows scheduled task state, process trees, command lines, PIDs, launcher/worker split, MT5 terminal PIDs, locks, heartbeat files, supervisor heartbeat, monitor logs, console logs, and recent error logs;
   - distinguish noisy scheduler overlap from real process failure;
   - if a process is unhealthy, repair the process, launcher, supervisor, or watchdog path and record before/after proof.

2. Active broker truth and active-trade management:
   - inspect both FTMO and redacted_account account/equity/margin state, open positions, pending orders, recent deals, comments, magic numbers, symbols, volumes, SL/TP, time-in-trade, and management eligibility through read-only MT5 paths;
   - give special attention to active metals/gold positions if any exist;
   - verify that the book manager is managing open tickets, not stale local records;
   - verify no stale local open record exists after broker closure;
   - verify every active position has the expected management state, policy joinability, time-stop/trailing/risk-state fields, and no missing SL/TP unless explicitly expected by code/config;
   - if broker truth and local state disagree, repair local evidence or management code before accepting the state.

3. Packet, log, and chronology integrity:
   - parse runtime-learning packets, placement ledgers, decision logs, lifecycle logs, slippage logs, broker-R coverage, notification queues, shadow logs, and trade-record JSONL;
   - check append order, event timestamps, broker server timestamps, decision-bar timestamps, placement timestamps, management timestamps, close timestamps, ticket hashes, candidate IDs, policy join fields, redaction, schema, and duplicate-key behavior;
   - classify sub-second cross-namespace append order separately from true chronological error;
   - repair stale paths, split LFS pointer/runtime redirect readers, missing joins, bad hashes, schema drift, and verifier blind spots.

4. Candidate and admission behavior:
   - trace candidate generation through admission, cost gate, policy weighting, symbol filtering, order routing, placement, management, and closure;
   - check candidate book, market-expansion D1 sleeve, W7 book, A8 metals gate, dropped-symbol filter, Kelly-lite sizing, stress derisk, running count, and all skip reasons;
   - identify whether no-candidate cycles are legitimate or caused by data, profile, stale bar, stale tick, selector, cost, spread, broker mapping, or chronology defects;
   - preserve full candidate/skip ledgers and repair any silent rejection or missing telemetry.

5. Broker profile and instrument parity:
   - audit every active canonical symbol against FTMO and redacted_account symbol names, tick size, point, digits, contract size, volume min/max/step, trade mode, filling mode, stops/freeze levels, spread, tick value, swap fields, margin/profit currency, session/trading constraints, and direct `symbol_info`;
   - respect different naming between FTMO and redacted_account;
   - unsupported symbols must fail closed with explicit allowed-gap evidence;
   - warnings must be classified as runtime break, review-only, or context request with exact fields.

6. Config and runtime packet parity:
   - verify all active config keys from `config/agent_config.yaml`, runtime packet content, launcher environment, and actual worker behavior;
   - compare config file hashes before and after any reload;
   - verify packet log path and reader coverage;
   - confirm rollback to `robust6_every_split_positive` and full market-expansion-off remains documented and executable.

7. Context, branch, and research parity:
   - fetch latest remote state and check whether newer fast-forward commits exist on the active VPS branch;
   - do not import unrelated branch history blindly;
   - compare route artifacts, context files, current maps, and research handoffs to current disk/runtime truth;
   - if files from another research session would directly improve the system or context, write an exact request artifact naming path, commit/hash if known, why it matters, and what verifier would consume it.

8. Weakness and opportunity hunting:
   - actively search for limitations that keep the system from being stronger: missing observability, brittle joins, under-covered tests, profile drift, stale assumptions, low opportunity capture, over-tight filters, broker-specific gaps, concentration risks, candidate starvation, execution-cost blind spots, stale ledgers, unverified rollback, missing sealed replay/forward capture link, or unhandled market condition;
   - if a limitation is repairable inside this production-code/runtime evidence class, implement the repair;
   - if it needs a research, validation, source-capture, or owner/access lane, create an exact next artifact with fields, source paths, expected row counts if knowable, and acceptance criteria.

## Subagent Use

Use all available subagent capacity when helpful. Subagents are advisory reviewers with disjoint read scopes unless the environment explicitly gives them safe write isolation. The main session owns integration, edits, verification, staging, commit, and final judgment.

Launch as many independent subagents as the system reasonably allows across these lanes:

- process/runtime health, scheduler, PIDs, heartbeats, logs, rollback;
- broker/account/position/order/deal truth and active-trade management;
- packet/log chronology, joinability, schema, redaction, duplicate keys;
- config/profile/instrument parity across FTMO and redacted_account;
- candidate/admission/sleeve/market-expansion behavior and opportunity capture;
- tests/verifiers/artifact/context freshness;
- adversarial weakness and opportunity review.

Every subagent must inspect disk/runtime evidence, not chat memory, and return exact paths, commands, timestamps, counts, and uncertainty. If subagent tooling is unavailable or paused, record that and execute the lanes serially instead.

## Repair Rules

Use full same-evidence-class pursuit. A blocker ledger is not completion when the next action is still possible here. Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action allowed by this prompt has been attempted or is proven inapplicable.

When a repair is made:

- explain the defect and why it weakens runtime truth or system strength;
- edit the smallest correct code/config/profile/verifier/test/context surface;
- add or update focused tests/verifiers;
- run the relevant py_compile, pytest, verifier, route audit, and live-read checks;
- if reload is needed, record exact commands, process IDs, config hashes, packet samples, monitoring paths, rollback proof, and post-reload broker read-only snapshot;
- update route artifacts and output manifest;
- stage only scoped files, never broad live telemetry dirt;
- commit with `Co-Authored-By: Codex GPT-5 <redacted@example.com>` and push when artifact-worthy.

If a repair cannot be done inside this lane, record exact source-capture, research, validation, broker-profile, owner/access, or deployment-package requirement. Vague blockers, lazy "future work", and passive "monitor later" are not acceptable when same-evidence-class work remains.

## Required Baseline Verification

Run the strongest relevant subset after each material repair, and run the full baseline when the change affects runtime behavior, packet schema, profile interpretation, candidate/admission routing, or active management:

```powershell
python -m py_compile src\components\ultimate_book\admission.py src\components\ultimate_book\bridge.py src\components\ultimate_book\book_owner.py src\components\ultimate_book\sleeves\candidate_registry.py src\components\ultimate_book\sleeves\market_expansion_d1.py
python scripts\audit_broker_profile_market_details.py --output-json research\operations\vps_runtime_active_monitoring_repair_2026_06_19\VPS_BROKER_PROFILE_MARKET_DETAIL_AUDIT_2026_06_19.json --output-md research\operations\vps_runtime_active_monitoring_repair_2026_06_19\VPS_BROKER_PROFILE_MARKET_DETAIL_AUDIT_2026_06_19.md
python research\operations\final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18\verify_market_expansion_conditioned_policy_runtime_alias.py
python research\operations\final_moonshot_wave_e_runtime_learning_packet_parity_2026_06_18\verify_wave_e_runtime_learning_packet_parity.py
pytest tests\test_broker_profile_market_detail_audit.py -q
pytest tests\ultimate_book\test_runtime_learning_packet.py tests\ultimate_book\test_placement_ledger.py -q
pytest tests\ultimate_book\test_book_owner.py -q
pytest tests\ultimate_book\test_market_expansion_runtime_generator.py -q
pytest $(rg --files tests\ultimate_book | rg 'market_expansion') -q
pytest tests\ultimate_book\test_candidate_promotion_plumbing.py tests\ultimate_book\test_order_route.py tests\ultimate_book\test_book_engine.py tests\ultimate_book\test_candidate_book_consistency.py tests\ultimate_book\test_active_registry_and_softband_audit.py tests\test_dynamic_target_stop_geometry_v4.py tests\test_limit_order_flow.py::test_vnext_trailing_runner_pending_fill_trails_and_final_closes_from_router tests\test_limit_order_flow.py::test_vnext_time_stop_policy_closes_at_configured_bar_count -q
python research\operations\vps_runtime_active_monitoring_repair_2026_06_19\verify_vps_runtime_active_monitoring_repair.py
python scripts\audit_goal_route_artifacts.py research\operations\vps_runtime_active_monitoring_repair_2026_06_19 --full-jsonl
```

If a command is not applicable to the actual repair, say why in the completion audit. If a command fails from environment friction rather than code failure, preserve exact output and add a smaller proof command.

## Required Artifacts

Maintain or create these route artifacts under `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/`:

- `VPS_ACTIVE_SUPERVISION_REPAIR_CONTEXT_ANCHOR.md`
- `VPS_ACTIVE_SUPERVISION_REPAIR_CYCLE_LEDGER.jsonl`
- `VPS_ACTIVE_SUPERVISION_REPAIR_ISSUE_LEDGER.jsonl`
- `VPS_ACTIVE_SUPERVISION_REPAIR_ACTION_LEDGER.jsonl`
- `VPS_ACTIVE_SUPERVISION_REPAIR_SUBAGENT_LEDGER.jsonl`
- `VPS_ACTIVE_SUPERVISION_REPAIR_BROKER_SNAPSHOT_<UTC>.json`
- `VPS_ACTIVE_SUPERVISION_REPAIR_PACKET_CHRONOLOGY_AUDIT_<UTC>.json`
- `VPS_ACTIVE_SUPERVISION_REPAIR_PROFILE_DETAIL_AUDIT_<UTC>.json`
- `VPS_ACTIVE_SUPERVISION_REPAIR_LIMITATIONS_AND_OPPORTUNITIES_<UTC>.md`
- `VPS_ACTIVE_SUPERVISION_REPAIR_COMPLETION_OR_HANDOFF_AUDIT.json`
- `OUTPUT_MANIFEST.json`
- `NEXT_PROMPT.md` or a newer starter if the session must hand off.

The artifacts must include result materialization status, source-capture state, source completeness where relevant, branch decision or implementation decision, runtime-effect boundary, forbidden surfaces, broker mutation status, active-trade status, verifier status, rollback status, and exact unresolved requirements.

## Saturation And Self-Red-Team

Before any handoff or completion checkpoint, run a written self-red-team pass:

- What exact chronology mistake would make runtime behavior look correct when it is stale?
- Which broker naming or profile field could make FTMO pass while redacted_account silently fails, or the reverse?
- Which packet field, ticket hash, candidate ID, local trade record, or placement row could cause a false join?
- Which active position could be managed under the wrong policy, wrong ticket, wrong broker, wrong symbol, wrong time-stop clock, or wrong risk state?
- Which config key could be true in YAML but false in launcher environment or worker behavior?
- Which no-candidate or skipped-unit cycles are legitimate, and which might hide a data or admission defect?
- Which legacy route/context claim is contradicted by current runtime?
- Which existing verifier would miss the issue you just inspected?
- Which limitation, if left alone, most directly reduces opportunity capture, execution quality, accuracy, or return robustness?

If any answer exposes a same-evidence-class gap, pursue and repair it before marking the checkpoint complete.

## Completion And Handoff Standard

This is a rolling supervision goal. Do not mark complete merely because all visible processes are running, packets are fresh, or the last cycle has no hard errors.

Continue active cycles until the owner stops the goal, the environment forces a handoff, or a defined checkpoint has:

- completed every required lane above at least once from current disk/runtime evidence;
- fixed every repairable same-evidence-class issue found;
- reduced remaining blockers to exact owner/access/source/capture/research/validation requirements;
- run required verifiers/focused tests or recorded exact environment friction;
- updated artifacts, manifest, context anchor, and next starter;
- committed and pushed scoped code/context/evidence changes when artifact-worthy;
- recorded rollback proof for every runtime or deployment-effect change.

If the session must stop for any reason, it must leave the next session able to continue without chat memory: write the current state, active issues, unmerged changes, commands run, verifier results, broker read-only snapshot, packet tail status, subagent findings, and exact next action.
