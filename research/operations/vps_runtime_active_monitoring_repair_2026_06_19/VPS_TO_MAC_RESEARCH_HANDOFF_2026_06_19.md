# VPS To Mac Research Handoff - 2026-06-19

Status: current VPS runtime context packet for the active Mac research session.
Evidence class: production-runtime observation, deployment-context handoff, research-session routing.
Runtime-effect boundary: this packet changes no broker/account/order/deal/position state.

## Branch To Pull

Pull and verify:

```bash
git fetch origin
git checkout vps/ultimate-conditioned-expansion-minimal-2026-06-18
git pull --ff-only origin vps/ultimate-conditioned-expansion-minimal-2026-06-18
git rev-parse HEAD
```

Required floor: `a18730398 context: record slippage evidence repair` or any newer fast-forward on the same branch.

Latest research-relevant code/evidence commit before this handoff:

- `5f361f79b vps: merge redirected slippage evidence`
- `a18730398 context: record slippage evidence repair`

Do not rely on chat memory. Start from disk, regenerate live state, and treat older hard-halt/current-state language as historical when current VPS route evidence disagrees.

## Mandatory Context Use

Read these first after checkout:

1. `.context/LIVE_STATE.md` after running `python scripts/generate_live_state.py`
2. `.context/00_core/current_vnext_system_map.md`
3. `.context/00_core/current_repo_reading_order.md`
4. `.context/00_core/quick_reference_card.md`
5. `.context/00_core/research_current_state.md`
6. `.context/00_core/goal_session_research_discipline.md`
7. `.context/00_core/research_operating_doctrine.md`
8. `.context/00_core/orchestrator_successor_operating_brief.md`
9. `.context/00_core/orchestrator_methodology_hardening_controls.md`
10. `.context/00_core/parallel_goal_merge_playbook.md`

Then read the current VPS routes before making runtime, broker, candidate, packet, profile, cost, or rollback claims:

- `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_MONITORING_REPAIR_EVIDENCE.md`
- `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/SLIPPAGE_COST_RUNTIME_MERGE_COVERAGE.md`
- `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/BROKER_R_RUNTIME_MERGE_COVERAGE.md`
- `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/LIVE_SHADOW_FOLLOWUP_RUNTIME_MERGE_COVERAGE.md`
- `research/operations/vps_runtime_ultimate_monitoring_repair_2026_06_18/VPS_RUNTIME_ULTIMATE_MONITORING_REPAIR_EVIDENCE.md`
- `research/operations/final_moonshot_market_expansion_conditioned_policy_runtime_alias_2026_06_18/VPS_CODEX_ULTIMATE_ACTIVATION_HANDOFF.md`
- `research/operations/final_moonshot_wave_e_runtime_learning_packet_parity_2026_06_18/VPS_CODEX_RUNTIME_LEARNING_PACKET_PROMPT.md`

## Current VPS Runtime Truth

The VPS is the active runtime surface for the ultimate-book package on branch `vps/ultimate-conditioned-expansion-minimal-2026-06-18`.

Active config parity verified from config, launcher packets, and route verifiers:

- `ultimate_book_enabled=true`
- `ultimate_book_apply_to_execution=true`
- `ultimate_book_live_activation_allowed=true`
- `selector_v4_apply_to_execution=false`
- `ultimate_book_include_candidate_book=true`
- `ultimate_book_include_market_expansion_book=true`
- `ultimate_book_market_expansion_policy=positive_weighted12_after_swap`
- `ultimate_book_profile=clean3_w7_ceiling_nom2p00`
- Candidate book active with 9 current sleeves.
- Conditioned market-expansion book active with 12 current sleeves.
- Kelly-lite, conservative Kelly, running count, smooth stress derisk, A8 metals gate, W7 dropped-symbol filter, and runtime-learning packet logging are active.

Current expectation remains replay/MC package evidence, not broker-real future PnL:

- Positive12 expansion monthly: `5.09%`
- Sharpe: `0.28419`
- MC pass: `0.9999`
- Max-DD fail: `0.0001`
- Worst day: `-2.083%`
- MaxDD: `8.842614R`

## Current Broker Snapshot

Fresh read-only direct MT5 snapshot captured on the VPS at `2026-06-19T03:29:16Z`.

FTMO:

- Terminal path: `C:\MT5\FTMO\terminal64.exe`
- Account server/company: `FTMO-Server3`, `FTMO Global Markets Ltd`
- Balance `96270.01`, equity `96123.93`, floating profit `-146.08`
- `trade_allowed=true`, `trade_expert=true`
- Open positions: 2
- Pending orders: 0
- Open positions:
  - `JP225.cash` SELL ticket `159993636`, volume `2.36`, SL `72269.15`, TP `70302.64`, floating `-11.71`, comment `W7:idxrev`
  - `UK100.cash` BUY ticket `160080305`, volume `1.82`, SL `10352.66`, TP `10471.47`, floating `-128.05`, comment `W7:idxrev`

redacted_account:

- Terminal path: `C:\MT5\redacted_account\terminal64.exe`
- Account server/company: `redacted_account-Server 2`, `redacted_account Ltd`
- Balance `98651.72`, equity `98569.05`, floating profit `-82.67`
- `trade_allowed=true`, `trade_expert=true`
- Open positions: 2
- Pending orders: 0
- Open positions:
  - `UK100` BUY ticket `246763216`, volume `0.19`, SL `10357.02`, TP `10473.39`, floating `-143.46`, comment `W7:idxrev`
  - `JP225` SELL ticket `246920173`, volume `2.21`, SL `72700.0`, TP `70791.0`, floating `60.56`, comment `W7:idxrev`

Current broker-state interpretation:

- No XAU/gold position is open.
- No crypto position is open.
- Every open position has a broker SL and broker TP.
- Current active management packets show native book management with `time_stop`, final target mode, and runtime-learning joinability.
- Legacy FTMO JP225/UK100 and redacted_account UK100 records remain honestly `ticket_policy_joinable` because full original candidate/decision placement rows are not present. Do not fabricate unavailable candidate truth.
- redacted_account JP225 is `ticket_candidate_decision_policy_joinable`.

## Current Process And Packet Surface

Observed on `2026-06-19T03:28Z` through `2026-06-19T03:29Z`:

- Scheduled task `GTOS_W7_BookSupervisor`: running.
- Supervisor heartbeat PID: `1456`.
- Monitor loop PIDs: launcher `9520`, worker `2404`.
- FTMO book launcher/worker PIDs: `4744` / `6992`.
- redacted_account book launcher/worker PIDs: `848` / `5872`.
- Scheduled task `LastTaskResult=2147946720` is the known overlap/IgnoreNew signal; `NumberOfMissedRuns=0`.
- Runtime packet path: `shadow_logs/ultimate_book_runtime_learning_packets.jsonl`.
- Latest management packet rows were created at `2026-06-19T03:28:00Z` to `2026-06-19T03:28:01Z`.
- Packet rows continue to carry `broker_runtime_change_status=false`, current bridge flags, policy alias `positive_weighted12_after_swap`, profile `clean3_w7_ceiling_nom2p00`, and runtime-effect `true`.

Most recent candidate cycle behavior:

- FTMO `2026-06-19T03:00:57Z`: one `asia_pdl_fade` UK100 intent was admitted by book authority, then skipped by the cost screen: `cost_screen_spread_r:0.920>0.100 (spread 3.4500 vs asia_pdl_fade stop 3.7514)`. This is protective behavior, not a placement failure.
- redacted_account `2026-06-19T03:00:59Z`: no candidates; unavailable redacted_account instruments failed closed through `profile_missing_instrument_config`.
- Both accounts continued normal position-management packets after the candidate cycles.

## Broker Profile Parity

Direct Windows VPS probes are authoritative for deployment claims.

FTMO profile:

- Supports all `46/46` active canonical symbols.
- Known duplicate alias groups are intentional:
  - `GER40/GER40_cash -> GER40.cash`
  - `JP225/JP225_cash -> JP225.cash`
  - `NAS100/US100_cash -> US100.cash`
  - `SPX500/US500_cash -> US500.cash`

redacted_account profile:

- Active verifier reports `ok=true` with the reduced direct broker surface.
- Supported active surface: `36/46`.
- Directly unavailable active symbols:
  - `AVAUSD`
  - `CORN_c`
  - `COTTON_c`
  - `DASHUSD`
  - `XAGAUD`
  - `XAGEUR`
  - `XAUAUD`
  - `XAUEUR`
  - `XPDUSD`
  - `XTZUSD`
- Runtime behavior: unavailable symbols fail closed before order generation.
- Known duplicate alias groups are intentional:
  - `GER40/GER40_cash -> GER30`
  - `JP225/JP225_cash -> JP225`
  - `NAS100/US100_cash -> NDX100`
  - `SPX500/US500_cash -> SPX500`

Mac research should not treat FTMO and redacted_account naming as interchangeable. Any candidate, profile, or replay-to-runtime proposal must carry broker-specific canonical symbol, broker symbol, tick value/point/contract metadata, spread/cost, swap, min/max/step volume, stops/freeze level, session availability, and unsupported-symbol disposition.

## Recent Repairs The Mac Session Must Absorb

1. Runtime-learning packet parity and cost gate hardening:
   - Strict packet validation, redacted ticket hashes, packet/source hashes, join keys, and swap-aware cost-to-R conversion are active.
   - Runtime packet logging remains observational and has `broker_runtime_change_status=false`.

2. Trade-record joinability repair:
   - Placement ledger now indexes full placement rows by ticket.
   - Restart adoption and management packets normalize legacy records where source-bound.
   - Reconstructed legacy index records are kept honest as `ticket_policy_joinable`.

3. Absent trade-record active-monitoring repair:
   - Stale local XAU records were reconciled closed only after a confirmed non-empty broker-open snapshot proved absence.
   - No broker mutation was used.
   - XAU/gold is currently flat on both accounts.

4. Slippage runtime merge repair:
   - `shadow_logs/slippage.jsonl` is an LFS pointer on the VPS.
   - Live writes redirect to `shadow_logs/slippage_runtime.jsonl`.
   - Read helpers now merge pointer-path rows with runtime-redirect rows and skip non-JSON pointer headers.
   - Cost/slippage coverage now sees `slippage_rows=7`, `entry_spread_rows=7`, and `entry_slippage_rows=7`.
   - Broker-R coverage now sees `slippage_rows=7`.
   - LIVE-FOLLOW-012 now reports merged line count `7` with no error.

## Mac Research Work To Continue

Use the Mac research session for broad research and package-quality evidence that does not require direct broker mutation:

- Build sealed replay, rolling holdout, stress, concentration, and leave-one-symbol/session/regime-out evidence for the current 9-sleeve candidate book plus the 12-sleeve conditioned market-expansion book.
- Search beyond the current sleeves for measurable, auditable market-state, path, volatility, session, regime, calendar, cross-asset, cost, and execution-quality mechanisms that can improve candidate quality, rejection quality, exits, sizing, or opportunity capture.
- Build full instrument/session/regime/horizon coverage ledgers that preserve all material rows, not top-N summaries.
- Validate whether the current `positive_weighted12_after_swap` activation set remains the strongest among updated broker-cost, swap, spread, volume, and session assumptions.
- Derive candidate deltas only with source-bound fields, duplicate controls, no-leak/as-of checks, cost/slippage stress, and broker-specific profile support.
- Produce close-side scoring and lifecycle-analysis specs that the VPS can later bind to broker-real deal joins.
- Identify any replay/data gaps precisely: symbol, broker, timeframe, date window, source field, parser, hash, and whether the gap is recoverable market data or non-generatable historical runtime state.
- Preserve negative findings and inverse/avoid findings as useful system intelligence instead of deleting the underlying mechanism.
- Prepare deployment-package dossiers only when broad replay/holdout/stress and verifier evidence justify them, with packet parity requirements, promotion criteria, rollback criteria, and owner-action boundary.

Do not make broker/account/order/deal/position mutations from the Mac session. Treat the VPS as the source of current direct broker truth.

## What To Send Back To The VPS Session

Send exact file paths and commits for:

- Route completion audits, output manifests, verifier results, and focused test outputs.
- Candidate deltas with source-bound row ledgers and broker-specific symbol/profile requirements.
- Updated replay/holdout/stress/concentration results with exact denominator policy.
- Cost, spread, swap, slippage, fillability, session, and broker-profile assumptions that differ from current VPS config.
- Any proposed config or code patch with rollback, tests, and live packet parity expectations.
- Any exact missing file/source/data request, including symbol, date window, timeframe, source root, schema field, and why it materially improves the system.

Completion standard for Mac-side work: produce committed artifacts, not chat-only summaries. If a blocker appears, pursue it inside the same evidence class until cleared, proven impossible from approved sources, or reduced to an exact owner/source/access/capture requirement.
