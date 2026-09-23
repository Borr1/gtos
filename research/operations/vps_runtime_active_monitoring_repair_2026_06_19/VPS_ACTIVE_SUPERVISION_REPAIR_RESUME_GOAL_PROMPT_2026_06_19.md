# VPS Active Supervision Repair Resume Goal Prompt - 2026-06-19

## Objective

Resume the interrupted VPS active supervision repair goal from current disk state. Do not restart from the older initial active-supervision prompt as if no work happened. The previous goal session already produced committed repairs, a controlled reload, fresh active-supervision artifacts, subagent ledgers, and an uncommitted post-checkpoint verifier/test hardening set. Your job is to absorb exactly what was done, finish the interrupted scoped checkpoint safely, commit/push the verified scoped artifacts, refresh context, and continue active VPS supervision from the newest broker/runtime evidence.

This is a constructive production-code/runtime supervision and repair lane with no conservative brake inside the authorized evidence class. Green status is a checkpoint, not completion. If new evidence exposes a bug, stale detail, missing join, candidate weakness, profile mismatch, chronology defect, verifier blind spot, or opportunity-capture limitation that is repairable in this lane, fix it and prove the repair.

## Current Known Disk State At Prompt Preparation

Prepared at `2026-06-19T04:57:19Z` from `C:\Users\MSI\Documents\ai-trading-agent`.

Current branch and remote:

- branch: `vps/ultimate-conditioned-expansion-minimal-2026-06-18`
- HEAD and origin at preparation: `d7536dbdf context: capture active supervision artifact checkpoint`
- latest committed active-supervision route commit captured in `.context/00_core/research_current_state.md`: `a362e71e2 vps: harden active supervision artifacts`
- `.context/00_core/research_current_state.md` is stale for any later commit you create after resuming; refresh it after the scoped checkpoint commit.

Committed work after the older `d967ba10f context: add active vps supervision goal prompt`:

- `0c4259ff4 vps: harden swap cost source guard`
  - live-facing broker-net-cost repair: required selected-cell swap-cost conversion now requires live `mt5.symbol_info` provenance for side-aware swap and `swap_mode`; profile/config fallback no longer satisfies required conversion unless an explicit override disables that requirement;
  - `src/components/permissions.py` passes read-only live symbol_info into the pretrade cost packet;
  - controlled book-worker reload proof exists at `VPS_ACTIVE_SUPERVISION_REPAIR_RELOAD_PROOF_20260619T040949Z.json`; broker mutation status was `none`, config hash was unchanged, and open broker tickets were unchanged across reload.
- `b112d22c3 context: mark swap guard checkpoint captured`
- `a362e71e2 vps: harden active supervision artifacts`
  - route JSON readers tolerate UTF-8 BOM JSON via `utf-8-sig`;
  - scheduled task `0x800710E0` is classified as `running_ignore_new_overlap_not_process_failure` when `MultipleInstances=IgnoreNew` and the supervisor heartbeat is fresh;
  - active-supervision artifacts, subagent ledger rows, and focused tests were added.
- `d7536dbdf context: capture active supervision artifact checkpoint`

Interrupted uncommitted work present at prompt preparation:

- Modified scoped route/test files:
  - `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/BOM_JSON_READER_FOCUSED_TEST_RESULT.json`
  - `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/NEXT_PROMPT.md`
  - `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/OUTPUT_MANIFEST.json`
  - `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_SUPERVISION_REPAIR_ACTION_LEDGER.jsonl`
  - `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_SUPERVISION_REPAIR_COMPLETION_OR_HANDOFF_AUDIT.json`
  - `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_SUPERVISION_REPAIR_CONTEXT_ANCHOR.md`
  - `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_SUPERVISION_REPAIR_CYCLE_LEDGER.jsonl`
  - `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_SUPERVISION_REPAIR_ISSUE_LEDGER.jsonl`
  - `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/verify_vps_runtime_active_monitoring_repair.py`
  - `tests/test_vps_active_supervision_json_readers.py`
- Untracked scoped artifacts:
  - `VPS_ACTIVE_SUPERVISION_REPAIR_BROKER_SNAPSHOT_20260619T044308Z.json`
  - `VPS_ACTIVE_SUPERVISION_REPAIR_PACKET_CHRONOLOGY_AUDIT_20260619T044308Z.json`
  - `VPS_ACTIVE_SUPERVISION_REPAIR_PROFILE_DETAIL_AUDIT_20260619T044308Z.json`
  - `VPS_ACTIVE_SUPERVISION_REPAIR_LIMITATIONS_AND_OPPORTUNITIES_20260619T044308Z.md`
- The uncommitted verifier/test hardening already passed before this prompt was written:
  - `python -m py_compile research\operations\vps_runtime_active_monitoring_repair_2026_06_19\verify_vps_runtime_active_monitoring_repair.py tests\test_vps_active_supervision_json_readers.py`
  - `pytest tests\test_vps_active_supervision_json_readers.py -q`: `5 passed`
  - active monitoring route verifier: `ok=true`, `issue_count=0`
  - route artifact audit: `ok=true`, JSON parse errors `0`, JSONL parse errors `0`

Unrelated live/runtime dirt also exists and must not be staged with research/route commits unless you intentionally update it as route evidence:

- `.context/LIVE_STATE.md`
- `pipeline_state/**`
- `shadow_logs/**`
- generated verifier result files outside this route unless deliberately refreshed and scoped.

Do not reset, checkout, revert, delete, or overwrite these uncommitted changes. Inspect them, verify them, then either commit scoped route/test/context changes or record an exact reason they should remain uncommitted.

## Mandatory Preflight And Context Use

Start from disk, not chat memory. Do not rely on chat memory:

```powershell
git fetch origin
git branch --show-current
git rev-parse HEAD
git status --short
python scripts\generate_live_state.py
```

Then read these active instructions and artifacts from disk before acting:

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
- latest numbered handoff in `.context/02_session_handoffs/` as historical context only
- `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_SUPERVISION_REPAIR_GOAL_PROMPT_2026_06_19.md`
- `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_SUPERVISION_REPAIR_STARTER_2026_06_19.md`
- `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_SUPERVISION_REPAIR_CONTEXT_ANCHOR.md`
- `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_SUPERVISION_REPAIR_COMPLETION_OR_HANDOFF_AUDIT.json`
- `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/OUTPUT_MANIFEST.json`
- `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/NEXT_PROMPT.md`
- `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_SUPERVISION_REPAIR_ACTION_LEDGER.jsonl`
- `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_SUPERVISION_REPAIR_ISSUE_LEDGER.jsonl`
- `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_SUPERVISION_REPAIR_CYCLE_LEDGER.jsonl`
- `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_SUPERVISION_REPAIR_SUBAGENT_LEDGER.jsonl`
- newest `VPS_ACTIVE_SUPERVISION_REPAIR_BROKER_SNAPSHOT_*.json`
- newest `VPS_ACTIVE_SUPERVISION_REPAIR_PACKET_CHRONOLOGY_AUDIT_*.json`
- newest `VPS_ACTIVE_SUPERVISION_REPAIR_PROFILE_DETAIL_AUDIT_*.json`
- newest `VPS_ACTIVE_SUPERVISION_REPAIR_LIMITATIONS_AND_OPPORTUNITIES_*.md`
- `research/operations/final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18/VPS_CODEX_ULTIMATE_ACTIVATION_HANDOFF.md`
- `research/operations/final_moonshot_wave_e_runtime_learning_packet_parity_2026_06_18/VPS_CODEX_RUNTIME_LEARNING_PACKET_PROMPT.md`

These files are active instructions, not background. Operationalize them in the completion audit and context anchor. After any context compaction, resume, interruption, tool crash, uncertainty, or branch change, regenerate `LIVE_STATE` and reread this resume prompt, the original supervision prompt, doctrine files, and latest route artifacts from disk.

## Evidence Class And Forbidden Surfaces

This is a production-code/runtime supervision and repair evidence class with `RESULT_MATERIALIZATION_REQUIRED` posture. It may edit and verify code/config/profile/verifier/launcher/supervisor/watchdog/tests/context artifacts, prompt/config/risk/execution/safety/canary/selector diagnostics, and route evidence when the change is source-bound and improves current VPS runtime truth.

Still forbidden unless separately authorized in the active turn:

- discretionary strategic trade decisions;
- live trading or broker operation that mutates broker/account/order/history/deal/position state;
- credential mutation or disclosure;
- paid API/vendor calls;
- broad remote history rewrite;
- fabricated broker-real, candidate, placement, deal, lifecycle, exact-R, proxy-R, source-capture, or result materialization claims.

Read-only broker/account/order/history/deal/position inspection is authorized. Controlled reload/restart is authorized only when needed for a proven code/runtime repair or unhealthy process, and must include commands, PIDs, config hashes, broker read-only snapshots, packet samples, monitoring paths, and rollback proof.

## Immediate Resume Tasks

1. Classify the working tree:
   - separate scoped route/test/context changes from live telemetry dirt;
   - do not stage `.context/LIVE_STATE.md`, `pipeline_state/**`, `shadow_logs/**`, or unrelated verifier-result churn unless a route artifact explicitly needs them;
   - inspect `git diff --name-only`, `git ls-files --others --exclude-standard`, and `git diff --cached --name-only` before any commit.

2. Finish the interrupted BOM/scheduler verifier checkpoint:
   - inspect the diff in `verify_vps_runtime_active_monitoring_repair.py` and `tests/test_vps_active_supervision_json_readers.py`;
   - preserve the guard that rejects pending completion/handoff verification status and accepts only `verified_post_generation_route_verifier_and_tests_green`;
   - preserve UTF-8 BOM JSON reader tolerance and `GTOS_W7_BookSupervisor` IgnoreNew overlap classification;
   - run:

```powershell
python -m py_compile research\operations\vps_runtime_active_monitoring_repair_2026_06_19\build_vps_active_supervision_repair_artifacts.py research\operations\vps_runtime_active_monitoring_repair_2026_06_19\verify_vps_runtime_active_monitoring_repair.py tests\test_vps_active_supervision_json_readers.py
pytest tests\test_vps_active_supervision_json_readers.py -q
python research\operations\vps_runtime_active_monitoring_repair_2026_06_19\verify_vps_runtime_active_monitoring_repair.py
python scripts\audit_goal_route_artifacts.py research\operations\vps_runtime_active_monitoring_repair_2026_06_19 --full-jsonl
```

3. Commit and push the scoped interrupted checkpoint if the above is green:
   - stage only the route/test files that belong to BOM/scheduler verifier hardening and the `20260619T044308Z` active-supervision artifact refresh;
   - include this resume prompt/starter if you keep or update them;
   - exclude unrelated live telemetry;
   - commit with `Co-Authored-By: Codex GPT-5 <redacted@example.com>`;
   - push to `origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18`.

4. Refresh context after that commit:
   - run `python scripts\generate_live_state.py`;
   - update `.context/00_core/research_current_state.md` so the latest captured commit is the new scoped checkpoint commit and the active-supervision summary includes the `20260619T044308Z` checkpoint plus the verifier guard;
   - commit/push that context refresh separately if it changes.

5. Continue the rolling active supervision cycle:
   - run or update `build_vps_active_supervision_repair_artifacts.py` using a new checkpoint status such as `active_supervision_resume_after_interrupted_checkpoint`;
   - inspect current broker state directly, not from the older snapshot;
   - verify FTMO and redacted_account active positions, orders, recent deals, SL/TP, local trade-record alignment, active metals/gold state, and management state;
   - inspect runtime-learning packet tail, placement/trade-record joins, slippage merged stream, notification queues, supervisor/worker heartbeats, scheduled task state, and process tree;
   - inspect candidate/admission behavior, skip reasons, no-candidate cycles, W7/A8/candidate book/market-expansion activity, broker-profile gating, and opportunity-capture limitations.

6. Revisit the chronology details:
   - the `20260619T044308Z` packet audit reported `append_order_regression_count=12`;
   - most are classified `subsecond_cross_namespace_append_order`;
   - one line around packet line `3262` is classified `true_timestamp_order_regression_or_same_namespace_delay` with about `1.83s` delta;
   - decide whether this is benign multi-worker append timing, needs a stronger classifier, needs writer-side monotonic sequencing, or needs a route issue entry and focused test.

7. Revisit candidate/opportunity details:
   - latest packet counts at prompt preparation included `cycle_no_candidates=79`, `unit_skipped=349`, `unit_admitted=27`, `unit_placed=6`, no market-expansion placements in the inspected window, and W7-only placements;
   - inspect whether this is expected selectivity or hidden starvation caused by stale bars, broker naming, cost/spread/swap guard, A8/W7 filters, dropped-symbol logic, profile fail-closed behavior, session gating, or stale telemetry;
   - if repairable in this lane, implement and verify; if it requires research/validation/source capture, write an exact next artifact with fields and acceptance criteria.

## Verification Baseline After Any Material Change

Run the strongest relevant subset, and do not claim readiness from stale green results:

```powershell
python -m py_compile src\components\broker_net_cost_engine.py src\components\permissions.py src\components\ultimate_book\admission.py src\components\ultimate_book\bridge.py src\components\ultimate_book\book_owner.py src\components\ultimate_book\sleeves\candidate_registry.py src\components\ultimate_book\sleeves\market_expansion_d1.py research\operations\vps_runtime_active_monitoring_repair_2026_06_19\build_vps_active_supervision_repair_artifacts.py research\operations\vps_runtime_active_monitoring_repair_2026_06_19\verify_vps_runtime_active_monitoring_repair.py
pytest tests\test_broker_net_cost_engine.py tests\test_vps_active_supervision_json_readers.py -q
pytest tests\test_broker_profile_market_detail_audit.py -q
pytest tests\ultimate_book\test_runtime_learning_packet.py tests\ultimate_book\test_placement_ledger.py -q
pytest tests\ultimate_book\test_book_owner.py -q
pytest tests\ultimate_book\test_market_expansion_runtime_generator.py -q
pytest $(rg --files tests\ultimate_book | rg 'market_expansion') -q
python research\operations\vps_runtime_active_monitoring_repair_2026_06_19\verify_vps_runtime_active_monitoring_repair.py
python research\operations\final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18\verify_market_expansion_conditioned_policy_runtime_alias.py
python research\operations\final_moonshot_wave_e_runtime_learning_packet_parity_2026_06_18\verify_wave_e_runtime_learning_packet_parity.py
python scripts\audit_goal_route_artifacts.py research\operations\vps_runtime_active_monitoring_repair_2026_06_19 --full-jsonl
```

If a command is skipped, record why. If a command fails due to environment friction, preserve exact output and run a smaller proof command. If a command fails due to code or artifact logic, repair it before handoff.

## Subagent Use

Use available subagents as advisory, disk-inspecting lanes, not as replacements for main-session judgment. Assign disjoint reads:

- process/scheduler/supervisor/PID/heartbeat/log reviewer;
- broker/trade/position/order/deal and active-management reviewer;
- packet chronology/joinability/slippage/redaction reviewer;
- config/profile/instrument parity reviewer;
- candidate/admission/opportunity-capture reviewer;
- verifier/artifact/context freshness reviewer;
- adversarial weakness/opportunity reviewer.

Every subagent must return paths, commands, timestamps, counts, and uncertainty. Preserve their findings in `VPS_ACTIVE_SUPERVISION_REPAIR_SUBAGENT_LEDGER.jsonl` or a new route artifact. If subagents are unavailable, run the lanes serially and record that.

## Completion Or Handoff Standard

Do not mark this rolling goal complete merely because the system is green or no immediate failure appears.

A valid resume checkpoint requires:

- the interrupted scoped checkpoint either committed/pushed or exactly bounded with a reason;
- `.context/00_core/research_current_state.md` refreshed if a new research/runtime commit was created;
- latest broker snapshot, packet chronology audit, profile audit, limitations/opportunities file, context anchor, action/issue/cycle/subagent ledgers, output manifest, and completion/handoff audit updated;
- route verifier, focused tests, and route artifact audit green;
- no arbitrary top-N/top 3/5/10 truncation; full ledger rows preserved;
- result materialization/source-capture/source completeness/branch decision or implementation decision fields recorded where relevant;
- runtime-effect boundary, forbidden surfaces, broker mutation status, rollback status, and source-use state recorded;
- all same-evidence-class blockers pursued until cleared, proven impossible from approved routes, or reduced to exact owner/access/source/capture/research/validation requirements.

Use literal impossibility exactly: every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action allowed by this prompt has been attempted or proven inapplicable.

If the session must stop again, write a new exact `NEXT_PROMPT.md` and, if useful, a new resume starter with current HEAD, dirt, latest cycle ID, tests run, active trades, packet line counts, unresolved requirements, and next commands.
