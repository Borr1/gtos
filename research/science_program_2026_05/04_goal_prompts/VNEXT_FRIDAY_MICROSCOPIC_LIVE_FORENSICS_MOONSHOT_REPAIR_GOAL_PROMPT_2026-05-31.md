# vNext Friday Microscopic Live Forensics And Moonshot Repair Goal Prompt

Date: 2026-05-31

Route id: `vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31`

Evidence class: `FRIDAY_LIVE_FORENSIC_REPLAY_REPAIR_AND_MOONSHOT_EXPANSION`

Objective: reconstruct the Friday live execution era at microscopic resolution, identify every live defect, anomaly, stale blocker, limitation, false refusal, bad trade mechanism, missed-opportunity mechanism, market-behavior pattern, logging gap, replay mismatch, selector mismatch, risk mismatch, execution mismatch, and context-staleness issue present in current local/MT5/read-only source evidence; then repair auditable local code, config, tests, verifiers, logging, replay builders, and current context so the vNext/moonshot system becomes more accurate, broader, more profitable, and less stale. This route produces replay, repairs, implementation, and committed current truth; it is not a wait-for-more-live-data route, not a raw-candidate-only tournament, and not a narrow quality-filter route.

## Current Contract

The current production truth is vNext/moonshot production replacement on the 24-symbol redacted_account surface. Fixed `1.5R`, J46/J49, BE-only, old 5/7-symbol fleets, old `PrimaryAnalyzer -> L2`, and old April/May context are historical or comparator-only unless current-head artifacts explicitly prove active use.

Current vNext anchors to read before using old context:

- `.context/LIVE_STATE.md`
- `.context/00_core/current_vnext_system_map.md`
- `.context/00_core/current_repo_reading_order.md`
- `.context/00_core/quick_reference_card.md`
- `.context/00_core/goal_session_research_discipline.md`
- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/orchestrator_successor_operating_brief.md`
- `.context/00_core/orchestrator_methodology_hardening_controls.md`
- `.context/00_core/parallel_goal_merge_playbook.md`
- `research/operations/vnext_live_activation_active_repair_companion_2026_05_28/ACTIVE_REPAIR_STATE.json`
- `research/operations/vnext_live_activation_active_repair_companion_2026_05_28/LIVE_REPLAY_GATE_STACK_PARITY_SUMMARY.json`
- `research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27/VNEXT_ACTIVATION_REPAIR_STAGE06_FINAL_ROUTE_STATE_2026-05-27.json`

Current active symbols:

`AUDJPY`, `AUDUSD`, `BTCUSD`, `CHFJPY`, `ETHUSD`, `EURGBP`, `EURJPY`, `EURUSD`, `GBPJPY`, `GBPUSD`, `GER40`, `JP225`, `NAS100`, `NZDUSD`, `SPX500`, `UK100`, `UKOIL_cash`, `US30_cash`, `USDCAD`, `USDCHF`, `USDJPY`, `USOIL_cash`, `XAGUSD`, `XAUUSD`.

Primary Friday forensic scope excludes crypto from the main execution-era denominator because BTCUSD/ETHUSD had no placed trades in this live slice and use different market-hours behavior. Record a compact crypto exclusion summary; keep the route's work on the non-crypto execution-era surface.

## Authority And Boundaries

You have explicit authority for local code, config, test, replay, verifier, logging, context, route-artifact, source-join, and repair implementation work needed by this route. For defects requiring four steps, twenty steps, or a new builder/test/verifier before the correct repair is reachable, do those steps in the same run. Do not convert repairable same-evidence-class work into a "later" item.

Use local files, route artifacts, shadow logs, knowledge-base trade records, tick/M1/M15/D1-H4-H1 data, read-only MT5 account/history/spec exports from the available terminal, git history, current code, tests, and locally cached source evidence. Missing MT5 read-only evidence becomes an exact source-gap row with searched commands and substitute local evidence, not a stop. Spawn focused subagents whenever they materially advance independent context gathering, audits, source joins, code-surface inspection, and red-team checks. Reconcile their findings against disk before committing or closing.

Route execution boundary:

- Do not place, modify, close, or otherwise mutate live broker orders/positions.
- Do not restart live trading execution as part of this route.
- Production-impacting Friday discoveries become current vNext truth only through the broad selected-system replay, stress, and implementation evidence required by this prompt.

These boundaries do not limit local repair, implementation, code/config/test changes, replay, source extraction, or committed route artifacts.

## Known Starting Facts To Verify, Not Trust Blindly

The current "weekend" artifacts are not clean authority for this route. They were built with a May 28 through June 1 window and include pre-trade rows plus later spread-close/weekend noise. Rebuild the Friday microscope from raw evidence.

Known current artifact facts to verify from disk:

- Existing anatomy denominator: `604` candidate rows.
- Existing outcome counts: `397` dynamic skips, `76` Gate1 rejects, `78` Gate3 rejects, `45` prop deferrals, `8` placed.
- First placed vNext order in current anatomy: `XAUUSD` short at candle `2026-05-28T23:45:00Z`.
- Placed symbols in current anatomy: `XAUUSD=5`, `NAS100=3`.
- Non-crypto rows from first placed trade through Friday close are approximately `328` before the 21:00 UTC spread-close batch or `360` including that batch; derive the exact boundary from broker/session evidence and record the rule.
- The raw tournament `current_selected_policy_gross_r_sum=-127.60944487551178R` is raw-candidate diagnostic output, not whole vNext selected-system performance.
- The promoted full vNext selected-system replay had a much larger selected denominator and positive aggregate metrics; do not compare it directly with raw rejected live candidates.
- The current config includes `moonshot_candidate_quality_selector_apply_to_execution: true` and a Friday-derived London liquidity/displacement rule. Treat that as an active candidate mechanism requiring full selected-system reconciliation and an implement/merge/remove decision, not as settled moonshot truth.

## Mandatory Preflight

Run and read from current disk before work:

```powershell
python scripts/generate_live_state.py
git rev-parse HEAD
git status --short
git log --oneline -n 40
```

Then read:

- `.context/LIVE_STATE.md`
- `.context/00_core/current_vnext_system_map.md`
- `.context/00_core/current_repo_reading_order.md`
- `.context/00_core/quick_reference_card.md`
- latest handoff path named by `LIVE_STATE` for stale-conflict classification; current route artifacts override it
- `.context/00_core/goal_session_research_discipline.md`
- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/orchestrator_successor_operating_brief.md`
- `.context/00_core/orchestrator_methodology_hardening_controls.md`
- `.context/00_core/parallel_goal_merge_playbook.md`
- current active route state and summaries under `research/operations/vnext_live_activation_active_repair_companion_2026_05_28/`

After context compaction, resume, interruption, long wait, tool crash, uncertainty, or stale nudge, repeat the relevant preflight from disk, reread this prompt and the starter message, reread doctrine, reread the route state, then continue from the current route checkpoint. Do not reconstruct state from chat memory.

## Route Directory And Required State

Create and maintain:

`research/operations/vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31/`

Required state/control artifacts:

- `FRIDAY_MICROSCOPE_ROUTE_STATE.json`
- `FRIDAY_MICROSCOPE_CONTROL_LEDGER.jsonl`
- `FRIDAY_MICROSCOPE_CONTEXT_ANCHOR.md`
- `FRIDAY_MICROSCOPE_OUTPUT_MANIFEST.json`
- `FRIDAY_MICROSCOPE_REPAIR_LEDGER.jsonl`
- `FRIDAY_MICROSCOPE_COMPLETION_AUDIT.json`
- `FRIDAY_MICROSCOPE_FINAL_REPORT.md`

The route state must record current stage, current HEAD, source window, freeze rule, active question stack, subagent assignments, searched roots, finished artifacts, open defects, repaired defects, tests run, current blockers, and exact next action. Update it after every material stage.

## Subagent Strategy

Use focused subagents aggressively. Do not use them for vague summaries. Assign them independent evidence surfaces so they add coverage without duplicating the main critical path. Close or reuse completed agents.

Required subagent lanes unless the main agent completes the lane directly before spawning:

- Freeze-window and source-inventory auditor.
- Trade/order/fill/broker lifecycle auditor.
- Candidate/refusal/selector/risk bridge auditor.
- Tick/M1/M15/D1-H4-H1 price-action path auditor.
- Full vNext selected-system replay auditor.
- Execution-policy and path-management auditor.
- Risk/prop/exposure/accounting auditor.
- Market coverage/starvation auditor across all non-crypto symbols.
- Code-surface stale behavior auditor.
- Context/documentation staleness auditor for files touched or relied on by this route.

Each subagent must return concrete files inspected, row counts, mismatches, defect candidates, repair candidates, and exact uncertainty. Reconcile every finding against disk. A subagent result is an input, not authority by itself.

## Stage 01 - Freeze Friday Exactly

Build a new source-bound Friday freeze, not a "weekend" derivative.

Tasks:

1. Determine the first actual placed vNext order from raw evidence: trade records, pending lifecycle, order reconciliation, broker history, and anatomy ledgers. Missing broker history requires an exact source-gap row and a local-evidence fallback, not an assumption.
2. Determine Friday end-of-trading-day for the non-crypto redacted_account/broker surface using broker/session/spread evidence. Classify the `2026-05-29T21:00:00Z` spread-close batch exactly: include as valid close-spread evidence or exclude as after-close artifact, with proof.
3. Exclude BTCUSD/ETHUSD from the primary Friday execution-era denominator. Preserve their rows in a separate appendix only.
4. Exclude all later weekend/current-day rows from the primary evidence.
5. Record code/reload/commit timeline during the freeze so every candidate is mapped to the runtime version and fixes active at that moment.

Outputs:

- `FRIDAY_FREEZE_SOURCE_WINDOW.json`
- `FRIDAY_FREEZE_EVENT_SOURCE_INVENTORY.jsonl`
- `FRIDAY_FREEZE_CODE_RELOAD_TIMELINE.jsonl`
- `FRIDAY_FREEZE_DENOMINATOR_SUMMARY.json`
- `FRIDAY_CRYPTO_EXCLUSION_SUMMARY.json`

Completion condition: every included/excluded row has an exact reason and timestamp basis.

## Stage 02 - Full Evidence Inventory

Search all relevant local evidence roots, not only the current route summaries:

- `research/operations/vnext_live_activation_active_repair_companion_2026_05_28/`
- `research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_repair_hardening_2026_05_27/`
- `research/science_program_2026_05/06_outcome_testing/vnext_moonshot_production_replacement_activation_2026_05_26/`
- `shadow_logs/`
- `pipeline_state/`
- `knowledge_base/trade_records/`
- `data/ticks/`
- `data/m1/`
- current config and profile files
- current runtime code
- current tests
- relevant git commits and diffs from the live repair sequence
- local archives if the active files point to moved data

Build a file/source inventory with row counts, timestamp coverage, schema version, hash, freshness, and whether the source is authoritative, derived, stale, cold, or contaminated for Friday.

Outputs:

- `FRIDAY_SOURCE_COVERAGE_LEDGER.jsonl`
- `FRIDAY_SOURCE_SCHEMA_LEDGER.jsonl`
- `FRIDAY_SOURCE_GAP_LEDGER.jsonl`
- `FRIDAY_SOURCE_HASH_MANIFEST.json`

Completion condition: every material source used by Friday claims is covered, hashed, and classified.

## Stage 03 - Canonical Friday Event Ledger

Create the canonical row-level event ledger from raw evidence. It must include every candidate, skip, rejection, prop deferral, order intent, broker order, fill, no-fill, partial close, SL/TP/BE modify request, close, Telegram event, risk decision, cost record, slippage record, account state, manual intervention, and final status in the freeze window.

For every row, capture:

- symbol, broker symbol, candidate id, trade id, side
- candle time, record time, source time, broker/server time, or exact missing-source reason
- runtime commit/version
- route/session/hour bucket
- origin family and framework
- selected policy and execution policy id
- selector decision and proof id
- selected-cell risk proof and risk percent
- gate0/gate1/gate3/prop/circuit decisions
- spread, spread/R, tick snapshot, M1 snapshot, M15/MSO snapshot
- raw and repaired entry/SL/TP/dynamic target
- lot size, dollar risk, equity/balance, exposure before/after
- order result retcode/comment
- fill price/time and slippage
- modify attempts and retcodes
- broker realized profit/commission/swap
- local projected PnL/R and broker truth reconciliation
- final row disposition: correct trade, correct refusal, stale refusal, stale blocker, execution defect, logging defect, data defect, ambiguous pending exact source, manual contaminated, or non-actionable market no-trade

Outputs:

- `FRIDAY_CANONICAL_EVENT_LEDGER.jsonl`
- `FRIDAY_CANONICAL_EVENT_SUMMARY.json`
- `FRIDAY_EVENT_RECONCILIATION_VERIFIER.py`
- `FRIDAY_EVENT_RECONCILIATION_VERIFICATION.json`

Completion condition: no raw Friday event class remains unjoined without an exact reason.

## Stage 04 - Full vNext System Replay, Not Raw Candidate Tournament

Rebuild the Friday result through the real vNext system chain:

`raw live candidate -> current moonshot selector -> follow/avoid/mixed intelligence -> selected-cell risk -> broker spec/geometry -> spread/cost -> prop exposure -> execution policy -> lifecycle simulation -> broker truth where placed`

Required denominator separation:

- raw generated candidates
- candidates matching current full moonshot selected universe
- selected candidates with selected-cell risk proof
- selected candidates passing broker geometry
- selected candidates passing spread/cost
- selected candidates passing exposure/prop risk
- broker-placement-ready candidates
- actually placed orders
- broker-reconciled outcomes

Join Friday rows to:

- Stage13/full moonshot selector artifacts.
- 289,600 selected-row promotion evidence.
- final dynamic-router replay evidence.
- momentum/partial policy promotion evidence.
- current selected-cell risk ledgers.
- current broker geometry ledgers.
- all prior question/answer/follow/avoid/mixed intelligence that was consumed into the activated vNext system.

The output must show whether Friday rows were true selected vNext opportunities or raw noisy candidates. Do not treat raw rejected candidates as proof that the moonshot system failed.

Outputs:

- `FRIDAY_FULL_VNEXT_SYSTEM_REPLAY_LEDGER.jsonl`
- `FRIDAY_FULL_VNEXT_SYSTEM_REPLAY_SUMMARY.json`
- `FRIDAY_RAW_VS_SELECTED_DENOMINATOR_RECONCILIATION.json`
- `FRIDAY_SELECTED_RISK_BROKER_READY_LEDGER.jsonl`
- `verify_friday_full_vnext_system_replay.py`

Completion condition: every Friday row has a canonical denominator status and every replay metric states which denominator it belongs to.

## Stage 05 - Microscopic Price-Action Anatomy

For every primary Friday row, follow price from candidate announcement through terminal status at the closest available resolution:

- D1/H4/H1 context before candidate.
- M15 candle context and structure.
- M5/M1 lower-timeframe transition, with exact missing-source rows where absent.
- Tick bid/ask path, with exact missing-source rows where absent.
- Entry touch/no-touch timing.
- Time to MFE, MAE, 0.25R, 0.5R, 1R, partial, BE return, 1.5R, 2R, 3R, SL, time stop, and final available price.
- Duration stuck near entry.
- First adverse excursion timing.
- First favorable excursion timing.
- Reversal timing.
- Spread/R at candidate and during path.
- Same-bar/tick ordering ambiguity.
- Broker stop/freeze/stops-level feasibility for every modify policy tested.

For each row, explain what happened as a market story with measurable fields, not vague labels. Identify why it won, why it lost, why it was stuck, why it reversed, why it did not fill, why the spread rejected it, why the selector rejected it, or why evidence was missing.

Outputs:

- `FRIDAY_MICRO_PRICE_ACTION_LEDGER.jsonl`
- `FRIDAY_WINNER_ANATOMY_LEDGER.jsonl`
- `FRIDAY_LOSER_ANATOMY_LEDGER.jsonl`
- `FRIDAY_STUCK_CANDIDATE_LEDGER.jsonl`
- `FRIDAY_MFE_MAE_TIMING_LEDGER.jsonl`
- `FRIDAY_MICRO_PRICE_ACTION_SUMMARY.md`

Completion condition: every candidate has a terminal path class and every placed trade has a full lifecycle/path autopsy.

## Stage 06 - Placed Trade Autopsy And Broker Truth

Autopsy every placed order and every open/residual lifecycle from broker truth and local logs.

Required placed trade questions:

- Was the trade selected by the full vNext system or only by a stale bridge?
- Was the origin/session/symbol historically positive in the activated selected universe?
- Was entry timing accurate or late?
- Did the system enter at the intended price or at a materially worse touch/fill?
- Did the position hit partial/BE/final/SL according to broker truth?
- Did SL/TP/BE modify use the correct ticket?
- Did same-symbol conflict affect it?
- Did spread/slippage/commission/swap change the R interpretation?
- Did manual intervention affect outcome?
- Would current repaired code have managed it differently?
- Did the live result expose a code defect, logger defect, policy defect, selector defect, risk defect, market no-edge condition, or validation gap?

Outputs:

- `FRIDAY_PLACED_TRADE_AUTOPSY_LEDGER.jsonl`
- `FRIDAY_BROKER_TRUTH_RECONCILIATION_LEDGER.jsonl`
- `FRIDAY_MANUAL_INTERVENTION_LEDGER.jsonl`
- `FRIDAY_OPEN_RESIDUAL_STATUS_LEDGER.jsonl`
- `verify_friday_broker_truth_reconciliation.py`

Completion condition: all placed tickets and residuals are reconciled or have exact read-only broker-history blocker proof.

## Stage 07 - Refusal, Skip, And Starvation Forensics

Study every non-traded row, especially:

- `SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC`
- `REJECTED_GATE1_SAFETY`
- `REJECTED_GATE3_CIRCUIT_BREAKER`
- `DEFERRED_GTOS_VNEXT_PROP_RESET`
- selected-cell risk unresolved/zero
- framework not activated
- session/off-session mismatch
- source-risk mismatch
- stale raw Gate1 geometry
- stale count/session cap
- spread/cost gate
- same-symbol conflict gate
- no-candidate/silent symbols

Classify each row as:

- correct current no-trade
- stale blocker requiring repair
- bridge/proof gap requiring source repair
- market-quality filter candidate
- selected-system opportunity missed
- raw-noise candidate correctly rejected
- data/logger gap requiring prospective capture

Do not blindly convert stale blockers into trades. Do not let stale blockers hide true opportunities. Separate both row by row.

Outputs:

- `FRIDAY_REFUSAL_FORENSIC_LEDGER.jsonl`
- `FRIDAY_STALE_BLOCKER_REPAIR_LEDGER.jsonl`
- `FRIDAY_CORRECT_NO_TRADE_LEDGER.jsonl`
- `FRIDAY_MISSED_SELECTED_OPPORTUNITY_LEDGER.jsonl`
- `FRIDAY_MARKET_STARVATION_BY_SYMBOL_LEDGER.jsonl`

Completion condition: every skipped/rejected/deferred row has a current vNext disposition and repair decision.

## Stage 08 - Execution Policy And Path-Management Research

Do not test policies only on raw candidates. Test policies on each denominator, especially selected and broker-ready denominators.

Policies to implement/simulate where source permits:

- current selected policy
- `momentum_exhaustion`
- `partial_be_runner`
- BE-after-trigger comparator
- fixed `1.5R` comparator
- strict real trailing variants with tick ordering, spread, broker stop/freeze/stops-level feasibility, modify cadence, modify retcode simulation, commission/swap/slippage accounting
- partial-then-trail variants
- time-stop variants
- hybrid policy router variants
- row-state-dependent policy selection using symbol/session/origin/failure mechanism/path state/spread cost/regime/volatility

Every policy result must specify:

- denominator
- exact/proxy evidence class
- gross R
- net/cost-adjusted R or exact missing cost-field reason
- win/loss/BE/open/no-fill counts
- expectancy
- profit factor
- drawdown/loss streak or exact missing sequence-field reason
- concentration by symbol/session/origin
- sensitivity to spread/slippage/commission
- broker feasibility
- implementation decision

A proxy-positive policy that fails a real tick/broker-feasibility simulation preserves its intelligence and kills only the unsupported claim. A policy that is strong on selected-system historical replay gets the production code/config/test change needed to use it correctly.

Outputs:

- `FRIDAY_EXECUTION_POLICY_SELECTED_DENOMINATOR_LEDGER.jsonl`
- `FRIDAY_EXECUTION_POLICY_BROKER_READY_LEDGER.jsonl`
- `FRIDAY_REAL_TRAILING_SIMULATION_LEDGER.jsonl`
- `FRIDAY_POLICY_ROUTER_REDESIGN_SUMMARY.json`
- `verify_friday_execution_policy_replay.py`

Completion condition: no policy conclusion is based only on raw candidate aggregate score.

## Stage 09 - Quality Selector And Full Moonshot Expansion

Audit the current Friday-derived quality selector. It currently points toward London liquidity sweep reclaim and London displacement continuation. Treat that as an active candidate mechanism, not as a narrow overfit ceiling.

Required work:

1. Verify whether the current quality selector was derived from contaminated "weekend" rows, pre-trade rows, close-spread rows, or non-selected raw candidates.
2. Recompute the same rule on the clean Friday freeze.
3. Recompute it on the full selected historical vNext replay.
4. Decide its correct system role from evidence:
   - removed,
   - expanded,
   - converted into a feature,
   - used as a high-confidence subset,
   - used as a negative/avoid filter,
   - merged into a broader meta-selector,
   - replaced by a stronger selector.
5. Search beyond that rule. The moonshot system includes broader origin families and prior intelligence, not one London rule.

Mechanism families to test or preserve with exact status:

- displacement continuation
- liquidity sweep reclaim
- volatility compression/expansion
- regime transition break
- session open range break
- structural distance extreme
- cross-asset lead/lag
- OB retest
- FVG fill
- breaker re-entry
- no-fill/fillability
- spread/cost/liquidity state
- M1/tick continuation confirmation
- MAE/MFE path shape
- time-in-trade hazard
- session/time-of-day effects
- same-symbol/correlation exposure
- calendar/news sensitivity
- local orderflow/depth/futures proxy source status, tests, and exact missing-source rows
- ML/meta-labeling features where audited examples exist

Outputs:

- `FRIDAY_QUALITY_SELECTOR_AUDIT_LEDGER.jsonl`
- `FRIDAY_QUALITY_SELECTOR_BROAD_REPLAY_SUMMARY.json`
- `FRIDAY_MOONSHOT_MECHANISM_EXPANSION_LEDGER.jsonl`
- `FRIDAY_META_SELECTOR_CANDIDATE_SPEC.md`

Completion condition: the route does not end at one positive subset; every found mechanism is either implemented, preserved with exact next proof, killed only at the current unsupported claim level, or merged into a broader selector design.

## Stage 10 - Risk, Prop, Portfolio, And Concurrency Repair

Risk governance must operate on account exposure in real money, not stale counts or generic R caps.

Audit and repair:

- open risk + pending risk + new trade risk in dollars
- risk percent from selected-cell proof
- actual SL distance and lot geometry
- contract size, tick size, tick value, lot step, min/max lot
- spread/slippage/commission/swap buffers
- current balance/equity
- day-start baseline
- realized broker PnL
- floating PnL
- external prop daily/overall limits
- internal daily overlay
- same-symbol/correlation worst-case exposure
- count caps that block valid low-risk vNext trades
- stale `max_concurrent`, KZ count, or trades-today logic

Outputs:

- `FRIDAY_ACCOUNT_EXPOSURE_RISK_LEDGER.jsonl`
- `FRIDAY_PROP_DEFERRAL_REPAIR_LEDGER.jsonl`
- `FRIDAY_CONCURRENCY_CAP_STALENESS_AUDIT.json`
- code/config/tests repairing stale risk gates where verified

Completion condition: every Friday prop/count/concurrency refusal is explained under current account-exposure logic and stale blockers are repaired.

## Stage 11 - Market Coverage And Starvation

Explain why only XAUUSD and NAS100 placed while the surface has 24 symbols.

For every primary non-crypto symbol, compute:

- raw candidates
- selected-system candidates
- selected-cell risk matches
- broker geometry pass/fail
- spread/cost pass/fail
- prop/exposure pass/fail
- execution policy selected
- broker-ready count
- placed count
- missed selected opportunity count
- correct no-trade count
- stale blocker count
- source/data/logging gaps
- best mechanism/failure mechanism

Special attention:

- symbols with candidates but no trades
- symbols with silence/no-candidate behavior
- symbols blocked by broker alias/spec/risk issues
- symbols blocked by spread close or session contract
- NZDUSD, SPX500, UK100, XAGUSD if they remain silent or underrepresented
- GER40/UKOIL/USOIL alias and risk geometry continuity

Outputs:

- `FRIDAY_MARKET_COVERAGE_FUNNEL_LEDGER.jsonl`
- `FRIDAY_MARKET_STARVATION_SUMMARY.md`
- `FRIDAY_SYMBOL_SPEC_AND_DATA_PARITY_VERIFICATION.json`

Completion condition: every non-crypto symbol has an exact reason for trade/no-trade behavior in the freeze window.

## Stage 12 - Code And Logging Repairs

Implement repairs discovered by the route. Do not stop at ledgers when code/config/test repair is available.

Likely repair surfaces include but are not limited to:

- Friday/weekend builders hardcoded to broad contaminated windows.
- Raw-candidate tournament being confused with full selected-system replay.
- Quality selector applied from a narrow contaminated slice.
- Missing full vNext replay builder.
- Missing denominator reconciliation.
- Missing broker-truth PnL fields.
- Missing or wrong selected policy propagation.
- Ticket-bound partial/BE/TP management.
- SL/TP modify diagnostics and Windows log encoding.
- Same-symbol conflict semantics.
- Account-exposure risk governor.
- Stale count/session caps.
- Spread/R calculation gaps.
- M1/tick capture and join gaps.
- Silent-symbol proof.
- Context docs that still imply old system behavior.

Every repair requires:

- code/config/artifact owner
- before/after proof
- focused test or verifier
- rerun of affected route artifact
- manifest update
- route-state update
- scoped commit

## Stage 13 - Broad Historical Recheck For Every Proposed Production Change

Friday is the microscope that produces repairs and candidate changes. Broader selected historical evidence determines the final implementation scope for production-impacting behavior.

For each proposed change:

- identify the affected denominator and source artifacts;
- run or build the broad selected-system replay needed to test it;
- include cost/spread/slippage stress;
- include leave-symbol, leave-session, origin-family, and time-split checks where source coverage supports them;
- check concentration;
- verify no stale raw-candidate rows leak into selected denominators;
- implement only the portion supported by evidence;
- preserve weaker mechanisms as active feature candidates, redesign inputs, inverse filters, or exact source-capture tasks rather than deleting them.

Outputs:

- `FRIDAY_TO_BROAD_REPLAY_CHANGE_DOSSIER.jsonl`
- `FRIDAY_PRODUCTION_CHANGE_EVIDENCE_MATRIX.json`
- `FRIDAY_IMPLEMENT_KILL_REDESIGN_DECISION_LEDGER.jsonl`

Completion condition: every code/config behavior change from this route is tied to source evidence beyond one noisy Friday slice, or explicitly labeled as logging/replay/forensic infrastructure rather than trading decision logic.

## Stage 14 - Research Current-State Repair

Update current context that future agents will read:

- `.context/00_core/research_current_state.md` if stale.
- Relevant current-truth docs touched by this route.
- Route final report.
- Manifests and reading pointers.

Do not rewrite old cold history for style. Repair current reading-path files and route outputs that affect later research, implementation, or agent understanding.

Outputs:

- current-state update if needed
- `FRIDAY_CONTEXT_STALENESS_REPAIR_LEDGER.jsonl`

Completion condition: later agents read the current route without confusing raw-candidate Friday diagnostics with full vNext selected performance.

## Anti-Loop And Completion Controls

No infinite ledger production. A ledger exists to feed a decision, repair, verifier, test, or final route state. Every rerun must state the changed input, expected new evidence, and verdict. Re-running unchanged checks for comfort is not progress.

No early completion. The route is not complete because:

- one subset is positive;
- one verifier is green;
- one policy looks bad on raw candidates;
- no-trade baseline wins a contaminated denominator;
- a builder writes a summary;
- subagents return no blockers;
- the Friday raw candidate surface is noisy.

Completion requires:

- clean Friday freeze from first placed trade through proven Friday close;
- primary non-crypto denominator and compact crypto exclusion summary;
- canonical event ledger;
- full vNext selected-system replay;
- raw-vs-selected denominator reconciliation;
- microscopic price-action anatomy for every primary row;
- placed-trade broker truth autopsy;
- refusal/stale-blocker disposition for every skipped/rejected/deferred row;
- market coverage/starvation explanation for every non-crypto symbol;
- execution-policy analysis on selected/broker-ready denominators;
- quality-selector audit against broad historical selected evidence;
- account-exposure risk/concurrency repair;
- same-symbol lifecycle decision/repair;
- broker-cost/accounting repair;
- code/logging/context repairs for every verified defect inside this evidence class;
- focused tests/verifiers passing;
- output manifest current;
- route state current;
- scoped commits;
- final report with exact remaining blockers only where source/broker/platform evidence cannot be obtained or a hard boundary is reached.

## Final Report Required Structure

The final report must include:

- exact freeze window and row counts;
- raw, selected, risk-proof, broker-ready, placed, and broker-reconciled denominators;
- what really happened Friday;
- why only XAUUSD/NAS100 placed;
- what stale blockers were found and repaired;
- what refusals were correct;
- which live defects were real code/config/logging defects;
- every placed trade autopsy;
- every major losing mechanism;
- every major winning mechanism;
- every market/starvation explanation;
- full-system replay metrics, not raw-candidate-only metrics;
- execution-policy conclusions by denominator;
- quality-selector decision;
- risk/exposure/concurrency decision;
- code/config/test/context changes made;
- what remains unsolved and exact source required;
- next moonshot research directions produced by this microscope.

Mark the goal complete only after the completion standard is satisfied with committed route artifacts and scoped code/config/test/context repairs.
