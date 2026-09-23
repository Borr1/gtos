# Lane 07 - Market Coverage Source And Starvation Repair Goal Prompt

You own 24-symbol coverage, source integrity, and starvation repair. The system must explain why each symbol produced candidates, skipped, rejected, or stayed silent, using current vNext source truth instead of old-market assumptions.

## Active Context

Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`, `.context/00_core/current_vnext_system_map.md`, `.context/00_core/current_repo_reading_order.md`, `.context/00_core/quick_reference_card.md`, `.context/00_core/goal_session_research_discipline.md`, and `.context/00_core/research_operating_doctrine.md`. Read Friday microscope, live companion, tick/M1/M15 capture state, MT5 alias/spec ledgers, config profiles, and market-source activation artifacts. Do not rely on chat memory. After any context compaction, resume, interruption, long wait, tool crash, or uncertainty, regenerate `LIVE_STATE` and reread this starter, this controlling prompt, the doctrine files, lane-specific context, and latest route artifacts from disk before continuing.

## Route Directory

Write route-owned outputs under:

`research/operations/vnext_lane07_market_coverage_source_starvation_repair_2026_05_31/`

## Required Work

Build a 24-symbol source and opportunity-funnel ledger that covers:

- expected market schedule and broker availability;
- MT5 alias/spec/tick size/contract/stops/freeze/spread geometry;
- tick, M1, M15, MSO, and source joins;
- candidate generation, quality selection, risk bridge, Gate1/Gate3, portfolio scheduler, and order-readiness by symbol;
- silent/no-candidate symbols and whether they were genuinely quiet, data-starved, source-missing, risk-missing, schedule-blocked, spread-blocked, selector-blocked, or code-path missing;
- crypto vs non-crypto separation where session contracts differ;
- source-capture code/tests for fields not currently persisted.

Repair source, alias, config, logging, verifier, and packet gaps that prevent a real 24-symbol opportunity engine.

## Completion Standard

Produce 24-symbol funnel ledger, source integrity ledger, starvation decision ledger, repair ledger, tests/verifier, manifest, and completion audit. Include result materialization status, source completeness, implementation decisions, and exact/proxy R linkage whenever source evidence exists.

No arbitrary top-N, top 3/5/10, representative-only, or number-limited cutoff is allowed; preserve all symbols and material rows. Full same-evidence-class pursuit is required. Literal impossibility means exactly that every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action available from the approved source class has been attempted or proven inapplicable with row-level source proof.

There is no conservative brake inside market/source repair and local code/test work. Operationalize `.context/00_core/goal_session_research_discipline.md` and `.context/00_core/research_operating_doctrine.md` as active instructions, not background. Use as many highest-reasoning subagents as needed for market-by-market audits, alias/spec review, source path tracing, and starvation red-team.

External action boundary: live trading broker operation, paid API/vendor spending, credential changes, and hidden production-change deployment are outside the task. Reading broker/account/order/history/deal/position evidence is required when it explains coverage or execution truth. Prompt/config/risk/execution/safety/canary/selector surfaces must be inspected and locally patched when they govern coverage.
