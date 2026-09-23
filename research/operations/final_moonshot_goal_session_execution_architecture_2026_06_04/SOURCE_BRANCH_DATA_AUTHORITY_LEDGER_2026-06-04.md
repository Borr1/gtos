# Source Branch Data Authority Ledger - 2026-06-04

Route: `final_moonshot_goal_session_execution_architecture_2026_06_04`

## Branch Authority

- Mac integration repo: `/Users/borr/Documents/gtos/repo/ai-trading-agent`
- Mac workspace root: `/Users/borr/Documents/gtos`
- Mac package root: `/Users/borr/Documents/gtos/packages`
- Prepared Wave 1 worktree root: `/Users/borr/Documents/gtos/worktrees`
- Integration branch: `final-moonshot-context-repair-2026-06-04`
- Remote base: `origin/main` at `d02a4c5312ec00064c1a16677382a1ef31ad6bd0`
- Historical Windows research paths from earlier route artifacts are `historical_windows_research_path` only and are not active launch surfaces.

The Mac integration repo is the launch surface for central orchestration. Wave 1 goal sessions launch from the prepared Mac worktrees.

## Mandatory Preflight Result

Command run:

`python scripts\generate_live_state.py`

Result:

- `.context/LIVE_STATE.md` regenerated.
- HEAD: use `git rev-parse HEAD`; current portable authority branch is a descendant of `origin/main`.
- Research context status: `FRESH`.
- Git status has known generated `LIVE_STATE.md` dirt and LFS clean-filter noise in legacy research artifacts. Scope commits by explicit path.

## Present Required Routes

- `research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03/`
- `research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02/`
- `research/operations/vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02/`
- `research/operations/final_moonshot_live_failure_intelligence_2026_06_04/`

## Missing Context Before This Repair

The following requested paths were absent and are created by this context repair:

- `.context/00_core/final_moonshot_post_hard_halt_research_plan.md`
- `.context/00_core/final_moonshot_goal_session_execution_architecture.md`
- `.context/00_core/final_moonshot_central_orchestrator_successor_brief.md`
- `.context/02_session_handoffs/SESSION_64_FINAL_MOONSHOT_CENTRAL_ORCHESTRATOR_SUCCESSOR_2026-06-04.md`
- `research/operations/final_moonshot_goal_session_execution_architecture_2026_06_04/`

## Data Availability

- `data/m1/`: present, `126` files.
- `data/ticks/`: present, `110` files.
- Tick evidence has known corruption/quarantine findings from the dual-broker/source audit. Replay must mark corrupt intervals as source gaps.
- redacted_account trade records under `knowledge_base/redacted_account_live_bee34003/trade_records/` are LFS-tracked. The current final branch has zero missing current-branch LFS objects on the Mac integration workspace.

Sample pointer observed:

`knowledge_base/redacted_account_live_bee34003/trade_records/AUDJPY/2026-06-03_moonshot_h04_05_0500_broadorigin_ceb1655bfae2d550a6795dd0.json`

Pointer:

`oid sha256:c34fec4bfecaad2745b93a40bc0e2898c541e5a93b51ee0a26bc9ef90c9c7789`

`size 922198`

## LFS And Evidence Access

- Current final-branch missing LFS objects: `0`.
- Historical all-ref missing LFS objects: `280`; these are documented archival gaps, not current-branch launch blockers.
- `git lfs ls-files --all --long --size` is the authoritative LFS pointer inventory command.
- Checkout can report legacy files that should have been LFS pointers but are full Git content. Treat that as legacy LFS hygiene evidence and never stage those paths as part of launch-context commits.

## Authority Rules

- Broker truth JSON from the hard-halt route is authoritative for redacted_account broker-real PnL/cash.
- Local trade records, shadow logs, replay, proxy-R, and selected-cell stats are useful only with explicit evidence-class labels.
- V3 artifacts are default-off research/production-integration inputs unless a route proves specific live authority.
- FTMO evidence is dual-broker supervisor/follower evidence unless a separate FTMO broker-real extraction proves account outcomes.

## Next Launch Surface

Use the prepared Wave 1 Mac worktrees for goal sessions. Materialize only route-required evidence payloads with explicit evidence class, source path, hash, and reason. Preserve `vps_runtime_path` labels for true VPS runtime/evidence paths.
