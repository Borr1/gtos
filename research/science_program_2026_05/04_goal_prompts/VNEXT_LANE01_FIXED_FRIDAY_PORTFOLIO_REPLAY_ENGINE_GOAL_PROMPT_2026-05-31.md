# Lane 01 - Fixed Friday Portfolio Replay Engine Goal Prompt

You own the reproducible fixed-Friday portfolio replay engine. Build the official artifact path that answers the hypothetical precisely: if the current repaired vNext system, current quality selector, current effective risk configuration, account-exposure scheduler, same-symbol conflict rule, selected-cell risk, and partial-BE lifecycle had existed during the clean Friday freeze, what trades would have been accepted, rejected, sized, timed, managed, and closed?

## Active Context

Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`, `.context/00_core/current_vnext_system_map.md`, `.context/00_core/current_repo_reading_order.md`, `.context/00_core/quick_reference_card.md`, `.context/00_core/goal_session_research_discipline.md`, and `.context/00_core/research_operating_doctrine.md`. Read the Friday route report and artifacts under `research/operations/vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31/`. Do not rely on chat memory. After any context compaction, resume, interruption, long wait, tool crash, or uncertainty, regenerate `LIVE_STATE` and reread this starter, this controlling prompt, the doctrine files, lane-specific context, and latest route artifacts from disk before continuing.

## Route Directory

Write route-owned outputs under:

`research/operations/vnext_lane01_fixed_friday_portfolio_replay_engine_2026_05_31/`

## Required Build

Create a builder and verifier that reconstruct the clean Friday fixed-vNext portfolio simulation from source artifacts. The builder must produce row-level ledgers and summaries for:

- input candidate universe and freeze boundaries;
- quality-selector inclusion/exclusion;
- selected-cell risk and effective per-instrument risk;
- current account/equity baseline used by the simulation;
- worst-case exposure before and after each accepted/rejected candidate;
- realized PnL, open PnL, partial release, same-symbol conflict, daily cushion, and portfolio risk state;
- accepted trade timeline with entry, partial trigger, final close or Friday close status;
- rejected trade ledger with exact rejection reason;
- final gross R, gross dollars, expectancy, win rate, max open risk, max daily exposure, and account path.

Known manual seed to reproduce or correct from disk:

- clean quality subset: `43` rows;
- accepted/rejected seed: `18` accepted and `25` rejected;
- R seed: `+13.5R`;
- gross dollar seed: about `+$17,528.76`;
- max open risk seed: about `$7,299.56`.

If recomputation differs, write the exact row-level cause. Disk evidence wins.

## Completion Standard

This lane must materialize exact-R/proxy-R and dollar rows, not a prose hypothesis. Include source completeness, branch decision, implementation decision, and result materialization status for every material row. No arbitrary top-N, top 3/5/10, representative-only, or number-limited cutoff is allowed; preserve all material rows in full ledgers.

Full same-evidence-class pursuit is required. Literal impossibility means exactly that every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action available from the approved source class has been attempted or proven inapplicable with row-level source proof.

There is no conservative brake inside this replay evidence class. Operationalize `.context/00_core/goal_session_research_discipline.md` and `.context/00_core/research_operating_doctrine.md` as active instructions, not background. Use as many highest-reasoning subagents as needed for ledger joins, risk math review, and timeline verification.

External action boundary: live trading broker operation, paid API/vendor spending, credential changes, and hidden production-change deployment are outside the task. Reading broker/account/order/history/deal/position evidence is required when it affects the Friday account baseline or cost model. Prompt/config/risk/execution/safety/canary/selector code must be inspected and locally tested whenever it defines faithful replay semantics.

Finish with a manifest, verifier result, focused tests for every implemented replay contract, and completion audit.
