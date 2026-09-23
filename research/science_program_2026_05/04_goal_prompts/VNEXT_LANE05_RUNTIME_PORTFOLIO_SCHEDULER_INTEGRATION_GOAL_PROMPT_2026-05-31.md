# Lane 05 - Runtime Portfolio Scheduler Integration Goal Prompt

You own the runtime portfolio scheduler integration lane. Convert the repaired vNext risk/exposure concept into local runtime code, config, tests, and verifier evidence so account exposure, not stale count/session caps, becomes the portfolio authority for current vNext candidates.

## Active Context

Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`, `.context/00_core/current_vnext_system_map.md`, `.context/00_core/current_repo_reading_order.md`, `.context/00_core/quick_reference_card.md`, `.context/00_core/goal_session_research_discipline.md`, and `.context/00_core/research_operating_doctrine.md`. Read Lane01 and Lane04 artifacts as they land on disk, plus `src/components/permissions.py`, orchestrator/runtime execution paths, config profiles, and live companion gate artifacts. Do not rely on chat memory. After any context compaction, resume, interruption, long wait, tool crash, or uncertainty, regenerate `LIVE_STATE` and reread this starter, this controlling prompt, the doctrine files, lane-specific context, and latest route artifacts from disk before continuing.

## Route Directory

Write route-owned outputs under:

`research/operations/vnext_lane05_runtime_portfolio_scheduler_integration_2026_05_31/`

## Required Work

Implement and test the vNext portfolio scheduler package locally. It must compute and enforce:

- current equity/balance and day-start baseline;
- realized broker PnL, open floating PnL, commission, swap, and cost buffers;
- open worst-case SL risk, pending worst-case risk, and new trade risk in dollars and percent;
- selected-cell risk and per-instrument profile risk;
- partial close risk release and residual risk;
- dynamic daily cushion based on realized/current account path;
- overall account limit and internal daily overlay;
- same-symbol conflict authority and multi-ticket extension contract points;
- exact refusal reason when a candidate fails portfolio authority.

Stale `max_concurrent`, kill-zone count, trades-today, static R, or old count/session caps cannot block a current vNext candidate when current account-exposure proof says the total worst-case risk stays inside configured limits. Keep them as evidence fields, diagnostics, or non-vNext controls when code proves the boundary.

## Completion Standard

Produce code/config/test changes, scheduler ledger, before/after gate matrix, verifier, and completion audit. Include implementation decision rows and exact/proxy R linkage from Lane01 where useful.

No arbitrary top-N, top 3/5/10, representative-only, or number-limited cutoff is allowed; preserve all material gate paths and tests. Full same-evidence-class pursuit is required. Literal impossibility means exactly that every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action available from the approved source class has been attempted or proven inapplicable with row-level source proof.

There is no conservative brake inside local runtime implementation and tests. Operationalize `.context/00_core/goal_session_research_discipline.md` and `.context/00_core/research_operating_doctrine.md` as active instructions, not background. Use as many highest-reasoning subagents as needed for permission-path tracing, account-risk math audit, and negative-test review.

External action boundary: live trading broker operation, paid API/vendor spending, credential changes, and hidden production-change deployment are outside the task. Reading broker/account/order/history/deal/position evidence is required for risk model truth. Prompt/config/risk/execution/safety/canary/selector code is this lane's work surface.
