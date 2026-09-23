# Quick Reference Card

Status: post-hard-halt pointer card after Wave3 acceptance and Wave3.5 V4 activation.
Do not use old 5-symbol/7-symbol kill-zone tables, fixed `1.5R`, J46/J49, BE-only, PrimaryAnalyzer/L2 language, or pre-halt "live waiting for first proof" wording as current production truth.

## Current State

- GTOS/vNext live trading is hard-halted.
- Halt proof files: `pipeline_state/GTOS_HARD_PRODUCTION_HALT.flag`, `pipeline_state/RESEARCH_RUNTIME_HALT.flag`, `knowledge_base/meta/AUTOSTART_DISABLED.flag`.
- Previous redacted_account live surface: 24 symbols.
- Previous live policy-family surface: `momentum_exhaustion` primary with `partial_be_runner` exception selection. Treat this as failure/comparator evidence, not as a reason to preserve old behavior.
- V3 state: Selector V3, Scheduler V3, and Execution Policy V3 were package surfaces, not full live authority.
- Wave3.5 state: accepted V4 production-code components are active local repo/config authority. Read `research/operations/final_moonshot_wave3_5_v4_authority_activation_2026_06_05/` before launching Wave4 or Wave5.

## Read First

1. `.context/LIVE_STATE.md` after regeneration.
2. `.context/00_core/current_vnext_system_map.md`.
3. `.context/00_core/current_repo_reading_order.md`.
4. `.context/00_core/gtos_context_os.md` and `.context/00_core/gtos_second_brain.md`; for substantial work run `python3 scripts/gtos_context.py build` and a task-specific `python3 scripts/gtos_context.py pack --task "<active task>" --profile ultimate --include-memory`. Add `--include-second-brain` only for distilled owner-intelligence retrieval; raw inbox notes are not direct authority.
5. `.context/00_core/final_moonshot_central_orchestrator_successor_brief.md`.
6. `.context/00_core/final_moonshot_post_hard_halt_research_plan.md`.
7. `.context/00_core/final_moonshot_goal_session_execution_architecture.md`.
8. `.context/00_core/research_operating_doctrine.md`.
9. `.context/00_core/research_current_state.md`.
10. `research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03/TRADE_FAILURE_REVIEW_2026-06-03.md`.
11. `research/operations/final_moonshot_goal_session_execution_architecture_2026_06_04/SOURCE_BRANCH_DATA_AUTHORITY_LEDGER_2026-06-04.md`.
12. `.context/00_core/portable_path_authority.md` before using machine-specific paths.
13. `.context/00_core/mac_migration_package_evidence_index.md` before using, deleting, or materializing external package evidence.

## Hard-Halt Facts

- Recent redacted_account GTOS window: `77` trades, `-$859.69`, `31` wins, `46` losses.
- One GER30 winner of `+$1,318.24` masked deeper damage.
- `54` SL/broker-SL exits caused about `-$9,280.84`.
- XAUUSD, NDX100/NAS100, and ETHUSD dominated damage.
- ETHUSD exposed swap/cost tail risk.
- Emergency flattening was not atomic enough; scheduler/process shutdown and halt flags were required.

## Immediate Program

- Wave 0: source, branch, disk, LFS, data, and context authority.
- Wave 1A: hard-halt broker/candidate forensic matrix, accepted at `01783e05a`.
- Wave 1B: V3 versus live authority gap audit, accepted at `af1c94e4c`.
- Wave 1C: dual-broker failure/architecture audit, accepted at `5ce6e39df`.
- Wave 2: Final Master After Hard Halt is accepted; it produced V4 lane contracts plus Wave4/Wave5 ML/data ownership contracts.
- Wave 3: V4 selector, scheduler, execution manager, same-symbol lifecycle, cost/swap/slippage, market whiteboard, data capture, runtime control, exit/harvest, and LiveDecisionPacketV4 are accepted.
- Wave 3.5: V4 local authority activation is the current config/context bridge.
- Wave 4 accepted: Wave4A Digital Twin + Historical Microscope, Wave4B Feature Store V2, Wave4C Label Store V2, and Wave4I integration/partition handoff are accepted on local `main`.
- Wave4R next: mandatory V4-vs-V3/pre-V4 frozen replay and hard-halt live results gate. It must make frozen replay workable for current V4 as-of chronological simulation, produce actual result intelligence, and hand Wave5 dataset targets forward.
- Wave 5 follows Wave4R: Wave5A dataset/leakage guard, Wave5B baselines/calibration, Wave5C challengers/local training, and Wave5D registry/runtime packet gate.
- Final posture: build and ship the final live system package. Goal sessions have full control over repo changes; change production code and live behavior code to build it.

## Research Doctrine

- Disk evidence is authority.
- Path model: repo-relative for repo artifacts, `/Users/borr/Documents/gtos` as the Mac research workspace, explicit `vps_runtime_path` labels for VPS runtime/evidence paths, and historical Windows paths only as historical/audit evidence.
- External Mac migration packages are cold evidence at `/Users/borr/Documents/gtos/packages`; do not bulk-copy them into the repo. Materialize exact files only when a route manifest/verifier requires them.
- Preserve evidence class: broker-real PnL/cash, exact-R, proxy-R, replay, simulation, shadow, live authority, default-off research, production code, uncommitted dirt, committed package, source gap, non-generatable truth, prospective capture requirement.
- Aggressive computation, source repair, and implementation decisions remain authorized locally.
- The Mac research workspace is the orchestration/build surface. The VPS remains the production/runtime surface.
