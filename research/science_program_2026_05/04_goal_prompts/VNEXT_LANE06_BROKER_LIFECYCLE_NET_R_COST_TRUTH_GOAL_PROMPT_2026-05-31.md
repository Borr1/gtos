# Lane 06 - Broker Lifecycle Net-R And Cost Truth Goal Prompt

You own broker lifecycle, net-R, cost, and Telegram truth. This lane makes placed-order accounting and lifecycle records broker-authoritative so research and runtime decisions stop mixing projected local PnL with actual deal/history evidence.

## Active Context

Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`, `.context/00_core/current_vnext_system_map.md`, `.context/00_core/current_repo_reading_order.md`, `.context/00_core/quick_reference_card.md`, `.context/00_core/goal_session_research_discipline.md`, and `.context/00_core/research_operating_doctrine.md`. Read live companion artifacts, Friday microscope artifacts, trade records, MT5 history exports/logs available locally, slippage logs, daily PnL logs, and notification logs. Do not rely on chat memory. After any context compaction, resume, interruption, long wait, tool crash, or uncertainty, regenerate `LIVE_STATE` and reread this starter, this controlling prompt, the doctrine files, lane-specific context, and latest route artifacts from disk before continuing.

## Route Directory

Write route-owned outputs under:

`research/operations/vnext_lane06_broker_lifecycle_net_r_cost_truth_2026_05_31/`

## Required Work

Build and patch broker lifecycle truth for:

- order request, fill, partial, residual, BE/TP/SL modify, close, manual intervention, commission, swap, spread, slippage, retcode, and final net-R;
- broker ticket/position identity joins across same-symbol overlap and partial close;
- Telegram notification parity with broker truth and current vNext policy labels;
- local projected R vs broker realized PnL reconciliation;
- open/residual lifecycle status and Friday close/account snapshot semantics;
- cost calibration rows consumed by downstream replay lanes.

Patch code/tests where lifecycle, ticket binding, logging, net-R, or notification truth is incomplete. Produce a broker-truth ledger for downstream lane consumption.

## Completion Standard

Produce broker lifecycle ledger, cost calibration ledger, projected-vs-broker reconciliation, notification parity verifier, tests, manifest, and completion audit. Include exact-R/net-R rows, expectancy-ready fields, source completeness, and implementation decision status.

No arbitrary top-N, top 3/5/10, representative-only, or number-limited cutoff is allowed; preserve all material broker/account/order/history/deal/position rows. Full same-evidence-class pursuit is required. Literal impossibility means exactly that every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action available from the approved source class has been attempted or proven inapplicable with row-level source proof.

There is no conservative brake inside broker-evidence parsing, source repair, and local code/test work. Operationalize `.context/00_core/goal_session_research_discipline.md` and `.context/00_core/research_operating_doctrine.md` as active instructions, not background. Use as many highest-reasoning subagents as needed for broker join review, notification audit, and same-symbol lifecycle red-team.

External action boundary: live trading broker operation, paid API/vendor spending, credential changes, and hidden production-change deployment are outside the task. Reading broker/account/order/history/deal/position evidence is the core work. Prompt/config/risk/execution/safety/canary/selector surfaces must be inspected and patched locally when they affect lifecycle truth.
