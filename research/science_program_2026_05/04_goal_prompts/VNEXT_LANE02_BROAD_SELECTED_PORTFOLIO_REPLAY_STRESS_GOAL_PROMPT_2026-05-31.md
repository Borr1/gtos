# Lane 02 - Broad Selected Portfolio Replay Stress Goal Prompt

You own the broad selected-denominator portfolio replay and stress lane. Generalize the fixed-Friday portfolio replay into a selected-denominator engine that evaluates quality/meta-selector candidates across the large vNext selected surface, historical splits, source/cost stress, and portfolio-exposure constraints.

## Active Context

Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`, `.context/00_core/current_vnext_system_map.md`, `.context/00_core/current_repo_reading_order.md`, `.context/00_core/quick_reference_card.md`, `.context/00_core/goal_session_research_discipline.md`, and `.context/00_core/research_operating_doctrine.md`. Read Lane01 outputs as they land on disk; before they exist, build a compatible interface and record the adapter. Do not rely on chat memory. After any context compaction, resume, interruption, long wait, tool crash, or uncertainty, regenerate `LIVE_STATE` and reread this starter, this controlling prompt, the doctrine files, lane-specific context, and latest route artifacts from disk before continuing.

## Route Directory

Write route-owned outputs under:

`research/operations/vnext_lane02_broad_selected_portfolio_replay_stress_2026_05_31/`

## Required Build

Build a portfolio replay/stress engine over selected vNext denominators, not a raw-candidate tournament. Use the `289,600` selected-row surface and current selected-trade shards/manifests needed to reconstruct as-of source-bound paths. Evaluate the Friday-quality mechanisms and broader candidates through:

- symbol, session, origin family, side, market type, date, month, regime, spread/R, source mode, and risk-cell splits;
- portfolio scheduling with worst-case open + pending + new risk in dollars and percent;
- same-symbol conflict semantics and alternative explicit multi-ticket scenarios when source-bound evidence supports them;
- partial release and residual exposure;
- transaction-cost, spread, slippage, commission, swap, stop/freeze feasibility, and missing-source stress;
- time split, leave-one-symbol-out, leave-one-session-out, recent-vs-old, and deconcentration;
- exact/proxy R, expectancy, win rate, average win/loss, drawdown, exposure, frequency, and concentration metrics.

The output must distinguish discovery from sealed or stress evidence. It must not call same-data selection validation. It must identify what survives broad stress, what was a Friday-specific artifact, the source completeness state for each material family, and the branch decision or implementation decision that follows from each result.

## Completion Standard

No arbitrary top-N, top 3/5/10, representative-only, or number-limited cutoff is allowed; ranked tables must be backed by full ledgers preserving all material rows. Full same-evidence-class pursuit is required. Literal impossibility means exactly that every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action available from the approved source class has been attempted or proven inapplicable with row-level source proof.

There is no conservative brake inside the replay/stress evidence class. Operationalize `.context/00_core/goal_session_research_discipline.md` and `.context/00_core/research_operating_doctrine.md` as active instructions, not background. Use as many highest-reasoning subagents as needed for source-shard mapping, split validation, concentration checks, and red-team leakage review.

External action boundary: live trading broker operation, paid API/vendor spending, credential changes, and hidden production-change deployment are outside the task. Reading broker/account/order/history/deal/position evidence is required for cost/risk calibration when present on disk or extractable. Prompt/config/risk/execution/safety/canary/selector surfaces must be inspected and locally tested wherever they define current replay semantics.

Finish with builder, verifier, result ledgers, stress summaries, output manifest, and completion audit.
