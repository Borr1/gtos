# Expanded OOS Data Research Program And Goal Prompt - 2026-05-03

Status: owner-approved research direction
Scope: research/tooling only
Promotion posture: `NO_PROMOTION_VERDICT`
Base documents:

- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/research_current_state.md`
- `research/program_control/RESEARCH_NEXT_STEPS_AND_OPEN_QUESTIONS_PLAN_2026-05-03.md`
- `research/program_control/DATA_AND_APPROVAL_GATE_RECLASSIFICATION_2026-05-03.md`
- `research/program_control/SIERRA_DOWNLOAD_STATUS_AND_GOAL_SESSION_NOTES_2026-05-03.md`
- `research/program_control/AI_AND_ORDERFLOW_EXECUTION_DISCUSSION_CONTEXT_2026-05-03.md`
- `research/sierrachart_data_source_research_2026-05-02/SIERRACHART_AND_PRIMITIVE_DATA_SOURCE_SYNTHESIS_2026-05-02.md`

## Honest Assessment

The owner's idea is directionally correct and high value.

The current studied dataset has been heavily mined. If more data is now available through MT5, Sierra Chart Package 12, Databento, and possible symbol expansion, the next strong research move is not to squeeze the old cohort harder. It is to freeze the best current candidates and test them across new dates, regimes, sources, and instruments.

The caveat is important:

- New dates on the same instrument/source can be genuine temporal OOS if those dates were not used to discover or tune the rule.
- New source data for the same market is source-transfer evidence, not perfect OOS.
- Futures proxies for MT5 CFD symbols are proxy-transfer evidence, not broker execution truth.
- New instruments are mechanism-transfer and expansion discovery, not automatic validation of the current live system.

That still makes the idea worth pursuing. It can answer questions that live-forward data would otherwise take months to answer, as long as the research keeps the labels honest.

## Core Thesis

Use expanded historical and newly available market data to test whether the strongest GTOS discoveries survive outside the original studied windows and whether they transfer across instruments, regimes, and data sources.

This program should be aggressive in data acquisition and replay, but conservative in interpretation. It should kill weak ideas quickly, identify candidates that truly generalize, and build a better expansion map for GTOS.

This is a long-running research goal, not a one-pass smoke test. The session must keep looping through dates, instruments, sources, regimes, and candidates until the stated queue is completed or a blocker is proven with file/path/error evidence. Do not stop after one symbol, one date range, one tool run, or one headline result if more registered work remains possible with local data and pure compute.

## Completion Standard

The goal is complete only when the fresh session has produced a defensible final synthesis and an explicit ledger for every major question it opened.

Acceptable terminal states:

- `ANSWERED_WITH_EVIDENCE`: result is supported by saved artifacts and reproducible commands.
- `REJECTED_WITH_EVIDENCE`: idea failed under registered tests; include why.
- `BLOCKED_WITH_REASON`: exact missing data/source/API/operator condition is documented.
- `DEFERRED_WITH_TRIGGER`: exact future trigger is documented.
- `DISCOVERY_ONLY`: outcome-informed or transfer evidence that cannot be promoted.

Unacceptable terminal states:

- vague "needs more research",
- stopping after a single instrument/date when more local data exists,
- headline results without source/evidence-class labels,
- numbers not backed by files,
- assumptions about unavailable data instead of explicit inventory checks.

The final report must not leave loose ambiguities. If something cannot be answered, it must appear in the ambiguity/blocker ledger with the precise reason, the artifact proving the blocker, and the next action that would resolve it.

## Evidence Strength Taxonomy

Every result must be classified into one of these evidence classes:

| Class | Meaning | Promotion value |
|---|---|---|
| `TRUE_TEMPORAL_OOS` | Same symbol/source, untouched date range, frozen rule before run. | Strongest historical evidence, still needs promotion dossier. |
| `SAME_MARKET_SOURCE_TRANSFER` | Same market, different broker/source/history format. | Useful robustness evidence; check timestamp, spread, and contract differences. |
| `FUTURES_PROXY_TRANSFER` | CME/COMEX/CBOT futures proxy for MT5 CFD/FX symbol. | Useful for mechanism/orderflow; not broker execution truth. |
| `CROSS_INSTRUMENT_TRANSFER` | Frozen rule tested on a new instrument. | Expansion discovery; not validation of original symbol. |
| `REGIME_TRANSFER` | Frozen rule tested on distinct volatility/trend/macro/session regimes. | Strong diagnostic; needs enough n per regime. |
| `FORWARD_SHADOW` | Data arrives after rule registration and is processed by scheduled replay/shadow. | Strong once sample floor and label truth are adequate. |
| `DISCOVERY_ONLY` | Rule, cohort, or instrument selected after seeing outcomes. | Useful for hypothesis generation only. |

Do not collapse these classes into one headline number.

## Frozen Candidate Set

The next goal should test only frozen, high-value candidates first:

1. Current live/J46-J49 baseline stack.
2. V2 OB-boundary path candidate.
3. V2 FVG path candidate.
4. V3 FVG-only rescue risk-bank candidate.
5. NAS100 depth/thinness orderflow diagnostic, where actual broker-R or clearly labeled synthetic/path labels exist.
6. Current full-stack/S79/side-aware risk baseline as a simulation comparator, not a live replacement.

Explicitly exclude near-term retesting of failed or parked routes as strategy candidates:

- Composite structural selector as a broad policy.
- K54 v3/v4 global architecture iteration on the same cohort.
- Portfolio-wide vol scaling that already failed.
- V3 OB-lock / FVG-then-OB variants that underperformed the cleaner FVG-only rescue path.
- Component 3B debate; owner parked it because of extra AI/API cost.
- Prompt cascade rebuild, Reflexion/adaptive loop, or live AI behavior changes.
- Quantum tracks or other low-priority speculative routes.

Failed routes may be used only as negative controls or sanity checks if that does not create extra tuning.

## Data Expansion Policy

Use new data in stages. Do not open everything at once.

1. Inventory data availability before outcomes:
   - symbol,
   - source,
   - date range,
   - timeframes,
   - tick/depth availability,
   - spread/contract specs,
   - session coverage,
   - missing bars/timestamp gaps,
   - source licensing/cost.
2. Freeze the candidate registry before running outcomes on a new batch.
3. Split expanded data into:
   - development diagnostics,
   - validation slice,
   - reserved holdout slice opened once.
4. Every opened batch is burned for future pure validation if it influences rules.
5. Include source-period and mechanism labels in every row:
   - `source_period`,
   - `source_system`,
   - `instrument_family`,
   - `broker_or_proxy`,
   - `mechanical_vs_live_like`,
   - `actual_vs_synthetic_label`,
   - `candidate_rule_version`.

## Preferred Data Order

1. MT5 historical OHLCV/tick inventory for current and candidate symbols.
2. Existing local historical/backfill data with explicit source flags.
3. Sierra Package 12 active-session delayed-depth capture and recent depth files.
4. Targeted Databento futures windows only after a predeclared question and cost estimate.
5. External/current webpages only through the saved-source protocol: use local cached pages first, then `curl.exe` or web-fetch/search if needed, save raw evidence and source index.

Do not run broad paid Databento pulls or expensive API experiments inside this goal unless the owner explicitly approves that spend.

Current Sierra first-wave status as of the latest local inventory:

- `GTOS_HISTORICAL_RESEARCH` / intraday `.scid`: first-wave files are mostly ready.
- Sparse `.scid` warnings: `SIM26-COMEX`, `SILM26-COMEX`, `VXMM26-CFE`.
- `GTOS_FORWARD_DEPTH_CAPTURE` / `.depth`: first-wave depth is ready for the 30-day window from about `2026-04-03` to `2026-05-03`.
- Depth present for: `NQM26-CME`, `MNQM26-CME`, `YMM26-CBOT`, `MYMM26-CBOT`, `GCM26-COMEX`, `MGCM26-COMEX`, `SIM26-COMEX`, `SILM26-COMEX`, `6JM26-CME`, `6BM26-CME`, `6EM26-CME`, `ESM26-CME`, `MESM26-CME`, `CLM26-NYMEX`, `ZNM26-CBOT`.
- The depth folder had `465` `.depth` files totaling about `59.701 GB` at the last checkpoint, with no changes over a 30-second sample.
- Use `research/program_control/SIERRA_DOWNLOAD_STATUS_AND_GOAL_SESSION_NOTES_2026-05-03.md` as the current Sierra inventory; older notes that mark `NQM26-CME`, `CLM26-NYMEX`, or `ZNM26-CBOT` as missing are stale.

## Goal Prompt

```text
Expanded OOS/data-expansion research goal for GTOS.

You are working in C:\Users\MSI\Documents\ai-trading-agent.

Objective:
Use newly available and expandable data sources to test whether GTOS's best current discoveries generalize outside the heavily mined original dataset. Build a strict OOS/source-transfer/instrument-transfer research program for frozen candidates only. The goal is to find which ideas survive new dates, regimes, sources, and instruments, and which fail. Every output remains research/tooling only with NO_PROMOTION_VERDICT unless a separate promotion dossier is explicitly requested.

Mandatory preflight:
1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest handoff in `.context\02_session_handoffs\`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `research\program_control\RESEARCH_NEXT_STEPS_AND_OPEN_QUESTIONS_PLAN_2026-05-03.md`.
8. Read `research\program_control\DATA_AND_APPROVAL_GATE_RECLASSIFICATION_2026-05-03.md`.
9. Read `research\program_control\EXPANDED_OOS_DATA_RESEARCH_PROGRAM_AND_GOAL_PROMPT_2026-05-03.md`.
10. Read `research\program_control\SIERRA_DOWNLOAD_STATUS_AND_GOAL_SESSION_NOTES_2026-05-03.md`.
11. Read `research\program_control\AI_AND_ORDERFLOW_EXECUTION_DISCUSSION_CONTEXT_2026-05-03.md`.
12. Inspect recent commits and current git dirt before editing anything.

Non-negotiable constraints:
- Research/tooling only.
- Preserve NO_PROMOTION_VERDICT in every report.
- Do not change live trading logic, prompts, risk settings, execution behavior, or active safety gates.
- Do not use Component 3B debate; it is owner-parked because of extra AI/API cost.
- Do not stage unrelated runtime dirt.
- Do not push to remote.
- Do not run broad paid Databento pulls. Use local/cached data first; for Databento, produce estimates and use only targeted windows after explicit approval.
- Do not use AI/API calls for broad replay brute force. Prefer deterministic/mechanical replay and local compute; use AI only where explicitly justified and budget-safe.
- Do not fabricate or "artifact" numbers. Every statistic must trace to a saved file, command, source row count, or explicit `not_computable` reason.
- Do not call cross-instrument transfer "validation" of the original instrument.
- Do not treat futures proxy outcomes as MT5 broker execution truth.
- Do not tune on a newly opened OOS slice and then call it OOS.
- Separate actual broker R, synthetic/path R, fill/no-fill, internal intent, and counterfactual path labels.
- Report trial counts, candidate counts, symbol counts, and data-source counts for every lift claim.

Core candidates to test first:
1. Current live/J46-J49 baseline stack.
2. V2 OB-boundary path candidate.
3. V2 FVG path candidate.
4. V3 FVG-only rescue risk-bank candidate.
5. NAS100 depth/thinness diagnostic where depth labels exist.
6. Current full-stack/S79/side-aware risk baseline as simulation comparator only.

Explicitly skip as strategy candidates:
- Composite broad selector.
- K54 v3/v4 same-cohort architecture iteration.
- Portfolio-wide vol scaling.
- Underperforming V3 OB-lock / FVG-then-OB variants.
- Component 3B debate.
- Prompt/cascade rebuilds.
- Reflexion/adaptive live learning.
- Quantum tracks.

Execution protocol:
For each task:
1. State the hypothesis before opening new outcome data.
2. Identify data source, date range, instrument, and evidence class.
3. Freeze candidate rule versions before running outcomes.
4. Build or reuse the smallest replay/inventory tool needed.
5. Run targeted tests for any tool changes.
6. Run the full analysis only after the frozen spec is written.
7. Report results by evidence class: TRUE_TEMPORAL_OOS, SAME_MARKET_SOURCE_TRANSFER, FUTURES_PROXY_TRANSFER, CROSS_INSTRUMENT_TRANSFER, REGIME_TRANSFER, FORWARD_SHADOW, or DISCOVERY_ONLY.
8. Include concentration, decay, source-quality, cost, no-leak, label-truth, and DSR/PBO/effective-N diagnostics where computable.
9. If a statistic is not computable, report `not_computable` with reason.
10. Add an ambiguity ledger and next triggers.
11. Commit scoped artifacts only.
12. Update `.context\00_core\research_current_state.md` after material research-state changes.

Research loop requirement:
After each run or batch, decide the next highest-value unresolved branch and continue. The loop is:

1. Inventory available data.
2. Register/freeze the next candidate/date/source/instrument batch.
3. Run replay or extraction.
4. Verify row counts, labels, joins, no-leak constraints, and evidence class.
5. Interpret results with failure/decay/source-quality attribution.
6. Write artifacts.
7. Update the queue/ambiguity ledger.
8. Continue to the next unresolved batch unless all remaining work is blocked, deferred with trigger, or rejected with evidence.

Do not end at "initial results." End only at a completed queue state with a final synthesis.

Priority task queue:

P0 - Expanded data source inventory
- Inventory MT5, Sierra, Databento, and local historical data availability.
- Include symbols, sources, date ranges, timeframes, tick/depth availability, contract specs, spreads, and costs.
- Use the latest Sierra first-wave inventory from `SIERRA_DOWNLOAD_STATUS_AND_GOAL_SESSION_NOTES_2026-05-03.md` rather than stale earlier snapshots.
- Output `research/program_control/EXPANDED_OOS_DATA_SOURCE_MAP_YYYY-MM-DD.md` and `.json`.

P1 - Frozen candidate registry
- Write a versioned registry freezing the candidate set before expanded OOS runs.
- Include exact rule names, artifacts, parameters, label requirements, excluded failed variants, and trial-count accounting.
- Output `research/program_control/EXPANDED_OOS_FROZEN_CANDIDATE_REGISTRY_YYYY-MM-DD.md` and `.json`.

P2 - Replay portability audit
- Audit whether existing V2/V2b/V3/J46 replay tools can run on arbitrary symbols/date ranges/sources.
- Add only research-tooling adapters, not live logic.
- Output a portability report and tests.

P3 - Same-instrument temporal OOS
- Run frozen candidates on untouched date blocks for current production symbols where data is available.
- Classify results as TRUE_TEMPORAL_OOS only if the date range was not used for discovery/tuning.
- Report by symbol/session/side/regime/year/quarter/source.

P4 - Regime-transfer OOS
- Use distinct volatility/trend/macro/session regimes to test whether candidates survive outside the original dominant conditions.
- Do not tune regime thresholds after outcomes.

P5 - Source-transfer and futures-proxy tests
- Use Sierra Package 12 and Databento only for focused, predeclared questions.
- Separate depth/trade/orderflow mechanisms from MT5 broker outcome truth.
- Start with NAS100/NQ because prior orderflow tooling exists.
- Also use the now-available first-wave Sierra depth subset to test whether orderflow/depth improves timing, entry quality, no-fill/abort decisions, and exit diagnostics as research-only challenger evidence. Do not treat orderflow/depth as only another yes/no signal.

P6 - Cross-instrument expansion discovery
- Screen additional tradable instruments for data quality, spread, session fit, contract specs, and replay feasibility.
- Run frozen candidates without tuning.
- Classify results as CROSS_INSTRUMENT_TRANSFER or DISCOVERY_ONLY, not live validation.
- Produce an expansion scorecard: promising, neutral, rejected, blocked.
- Do not do one instrument and stop. Cover the feasible first-wave families unless blocked: NAS100/NQ/MNQ, US30/YM/MYM, gold/GC/MGC, silver/SI/SIL, FX futures proxies `6J`, `6B`, `6E`, S&P/ES/MES, oil/CL, rates/ZN, and the available controls. If a family is excluded, document why.

P7 - Failure and decay analysis
- For every candidate that fails on expanded data, identify whether failure is due to regime, source mismatch, instrument mechanics, spread/cost, timestamp quality, label ambiguity, or actual edge decay.
- Do not immediately retune. File a new hypothesis only if mechanism evidence is clear.

P8 - Final synthesis
- Produce one final report with:
  - numbers by evidence class,
  - candidate survival table,
  - instrument expansion table,
  - data-quality table,
  - costs incurred/estimated,
  - ambiguity ledger,
  - rejected ideas,
  - next live-forward/shadow triggers,
  - promotion-readiness status.
- Preserve NO_PROMOTION_VERDICT unless separately instructed.
- Include a completion ledger mapping every P0-P8 item to `ANSWERED_WITH_EVIDENCE`, `REJECTED_WITH_EVIDENCE`, `BLOCKED_WITH_REASON`, `DEFERRED_WITH_TRIGGER`, or `DISCOVERY_ONLY`.
- Include the exact opened/burned/reserved data slices so future sessions do not reuse outcome-opened slices as pure OOS.

Final closeout:
1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md` freshness block.
3. Summarize completed tasks, commits, tests, blockers, data opened/burned, and remaining holdouts.
4. State explicitly that all outputs remain NO_PROMOTION_VERDICT.
```

## Additions To Make The Approach Stronger

1. Treat data as a scarce validation asset. Every newly opened batch should be logged as opened, used, reserved, or burned.
2. Use a champion/challenger design: frozen champions are tested first; new discoveries from expanded data become challengers and must wait for another untouched slice.
3. Keep expansion separate from validation. A rule working on a new instrument is useful, but it means "possible new instrument candidate," not "the original XAUUSD edge is confirmed."
4. Build an instrument-quality gate before replay: spread, tick value, session liquidity, contract mapping, data completeness, and kill-zone fit.
5. Prefer deterministic replay over broad AI calls. AI/API spend should not be used to brute-force new instruments.
6. Keep one reserved holdout untouched until the end of each phase.

## Bottom Line

This is the correct aggressive next research direction if executed with frozen rules and staged data opening.

It gives GTOS a way to answer "does this survive elsewhere?" faster than waiting only for live trades, while still preserving the distinction between historical OOS, source transfer, instrument transfer, and real live-forward validation.
