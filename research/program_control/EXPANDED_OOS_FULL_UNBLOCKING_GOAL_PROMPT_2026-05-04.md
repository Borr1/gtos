# Expanded OOS Full Unblocking Goal Prompt - 2026-05-04

Status: owner-approved full-run research direction
Scope: research/tooling only
Promotion posture: `NO_PROMOTION_VERDICT`

This prompt supersedes the launch behavior of:

- `research/program_control/EXPANDED_OOS_DATA_RESEARCH_PROGRAM_AND_GOAL_PROMPT_2026-05-03.md`
- `.context/05_operations/EXPANDED_OOS_RESEARCH_GOAL_PROMPT_2026-05-03.md`

The 2026-05-03 control pass completed source inventory, frozen registry, replay portability audit, P3/P5 status checks, and final blocker synthesis. That pass did **not** run full expanded replay across all Sierra/MT5/Databento sources. The purpose of this prompt is to continue from that state and explicitly treat missing adapters, converters, extractors, and replay glue as work to build, not as a reason to stop.

## Copy-Paste Goal Prompt

```text
Expanded OOS/data-expansion full-unblocking research goal for GTOS.

You are working in C:\Users\MSI\Documents\ai-trading-agent.

Use these as active context:
- `research/program_control/EXPANDED_OOS_DATA_RESEARCH_PROGRAM_AND_GOAL_PROMPT_2026-05-03.md`
- `research/program_control/EXPANDED_OOS_FINAL_SYNTHESIS_2026-05-03.md`
- `research/program_control/EXPANDED_OOS_REPLAY_PORTABILITY_AUDIT_2026-05-03.md`
- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/research_current_state.md`

Objective:
Go all the way from source availability to replayable expanded OOS/source-transfer/instrument-transfer evidence. Do not stop at "adapter missing", "converter missing", "tool not portable", or "needs a harness." Build the required research-only adapters, converters, extractors, tests, and replay glue needed to pursue the goal across the feasible first-wave data.

Core owner authorization:
- The owner approves research-only adapter/converter/extractor/tooling work needed to unblock the goal.
- The owner approves using local compute and long runtimes.
- The owner approves targeted Databento API calls when needed for predeclared replay/orderflow questions.
- The owner does not approve AI/API calls for Component 3B, broad AI replay, prompt experiments, or LLM-based brute force.
- No live trading logic, prompts, risk settings, execution behavior, or active safety gates may be changed.
- All outputs remain `NO_PROMOTION_VERDICT` unless a separate promotion dossier is explicitly requested later.

Mandatory preflight:
1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest handoff in `.context\02_session_handoffs\`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `research/program_control/EXPANDED_OOS_DATA_RESEARCH_PROGRAM_AND_GOAL_PROMPT_2026-05-03.md`.
8. Read `research/program_control/EXPANDED_OOS_FINAL_SYNTHESIS_2026-05-03.md`.
9. Read `research/program_control/EXPANDED_OOS_REPLAY_PORTABILITY_AUDIT_2026-05-03.md`.
10. Read `research/program_control/EXPANDED_OOS_DATA_SOURCE_MAP_2026-05-03.md`.
11. Inspect recent commits and current git dirt before editing.

Non-negotiable interpretation:
- The 2026-05-03 P0/P1/P2 artifacts are not the goal endpoint. They are the launchpad.
- `BLOCKED_WITH_REASON` is allowed only after an unblock attempt has been made or after the blocker is genuinely external.
- Missing local code is not an external blocker. Build it.
- Missing adapter/converter/extractor is not a valid final blocker until you have attempted an MVP adapter, added tests, and documented why it cannot work.
- "This would take more time" is not a blocker. Continue or checkpoint with resumable artifacts.
- Do not ask the owner whether to build research-only infrastructure. Build it.
- Do not ask the owner whether to run targeted Databento pulls if they are required for a predeclared non-AI research question. Record the estimated/actual cost and proceed, subject to tool/sandbox approval mechanics.
- If the runtime environment still requires an escalation approval, request it immediately through the tool with a precise justification; do not stop to write a planning question.

Hard stop conditions:
Only stop before completing the full queue if one of these is true:
1. A required external service/API/network/filesystem approval is denied by the runtime.
2. A vendor/source is unavailable, illegal, expired, or unauthenticated, proven by saved command/source evidence.
3. A local file format cannot be decoded after implementing a documented MVP parser and test fixture.
4. Disk/memory/runtime limits prevent completion, and a resumable batch plan/checkpoint artifact has been written.
5. The user explicitly interrupts or changes scope.

Research-only build requirements:
Build whatever is needed under scripts/tests/research tooling to make the data replayable:
- Sierra `.scid` inventory/export/bulk conversion into GTOS-compatible OHLCV roots.
- Sierra `.depth` parser/extractor or parity extractor for the selected orderflow fields.
- Databento fetch/cache wrappers for targeted windows, with source indexes and cost logs.
- Symbol/proxy mapping tables with contract metadata.
- Replay batch registries that freeze symbol/source/date/candidate rules before outcomes.
- V2/J46/V2b/V3 replay adapters that can consume the converted roots.
- Join/label validators separating actual broker R, synthetic/path R, fill/no-fill, internal intent, and proxy labels.
- No-leak checks, row-count checks, source-quality checks, and reproducibility manifests.

Data priority:
Go broad across the feasible first-wave families. Do not ask which target to start with; start with the fastest pilot that proves the adapter path, then expand.

Required first-wave families:
- NAS100/NDX100 with NQ/MNQ
- US30/US30_cash with YM/MYM
- XAUUSD with XAUUSD.scid and GC/MGC
- XAGUSD with SI/SIL, preserving sparse `.scid` warnings
- USDJPY with 6J
- GBPUSD with 6B
- EURUSD with EURUSD/6E
- S&P with ES/MES where broker/source mapping exists
- CL as macro/liquidity proxy/control
- ZN as macro/rates proxy/control
- VIX/VXM controls where available

Execution loop:
For each source family:
1. Register the batch before outcomes: symbol, source, date range, timeframe, candidate set, evidence class, and reserved holdout.
2. Build or reuse the adapter/converter/extractor.
3. Add focused tests for the adapter and row-count/schema invariants.
4. Produce GTOS-compatible replay input or a saved reason why conversion cannot work.
5. Run deterministic replay for frozen candidates where labels are available.
6. If labels are not available, build the label join or lifecycle/proxy label audit needed; do not silently skip.
7. Classify evidence as `TRUE_TEMPORAL_OOS`, `SAME_MARKET_SOURCE_TRANSFER`, `FUTURES_PROXY_TRANSFER`, `CROSS_INSTRUMENT_TRANSFER`, `REGIME_TRANSFER`, `FORWARD_SHADOW`, or `DISCOVERY_ONLY`.
8. Report concentration, cost/slippage assumptions, no-leak status, sample floors, DSR/PBO/effective-N where computable, and `not_computable` reasons where not.
9. Continue to the next family until all feasible first-wave families have either replay results or a proven external blocker.

Candidate set:
Use the frozen registry from `research/program_control/EXPANDED_OOS_FROZEN_CANDIDATE_REGISTRY_2026-05-03.md`:
1. Current live/J46-J49 baseline stack.
2. V2 OB-boundary path candidate.
3. V2 FVG path candidate.
4. V3 FVG-only rescue risk-bank candidate.
5. NAS100 depth/thinness diagnostic where depth labels exist.
6. Current full-stack/S79/side-aware risk baseline as simulation comparator only.

Do not run:
- Component 3B debate.
- Any AI/LLM replay or prompt cascade.
- Live behavior/risk/execution changes.
- Broad unregistered Databento pulls.
- Same-slice tuning presented as OOS.

Databento policy:
- Targeted Databento calls are approved for predeclared non-AI research questions.
- Before a paid pull, write a tiny JSON/MD request artifact naming symbol, schema, date window, fields, question, and expected use.
- Fetch only the declared windows.
- Save raw/cached outputs and source index.
- Record actual or estimated cost.
- Do not use Databento data to tune and validate on the same slice.

Completion standard:
The goal is not complete until all of these exist:
1. Adapter/converter status table for every first-wave source family.
2. At least one working end-to-end converted-source replay path, unless a true external blocker prevents it.
3. Replay or label-status artifacts for every first-wave family.
4. Candidate survival table by evidence class.
5. Instrument/source expansion scorecard: promising, neutral, rejected, blocked.
6. Data-quality table: date coverage, gaps, source mismatch, sparse warnings, contract/spec issues.
7. Opened/burned/reserved slice ledger.
8. Cost ledger, including Databento costs if used.
9. Failure/decay/source-mismatch attribution.
10. Final synthesis with `NO_PROMOTION_VERDICT`.

Commit discipline:
- Commit scoped research/tooling artifacts periodically.
- Do not stage unrelated runtime dirt.
- Use commit trailer: `Co-Authored-By: Codex GPT-5 <redacted@example.com>`.
- Update `.context\00_core\research_current_state.md` after material research-state changes.

Final closeout:
1. Run focused tests for new tooling.
2. Run `python scripts\generate_live_state.py`.
3. Read `.context\LIVE_STATE.md` freshness block.
4. Summarize completed adapters, replays, tests, commits, data opened/burned/reserved, costs, blockers, and next triggers.
5. State explicitly: `NO_PROMOTION_VERDICT`.
```

## Recommended Launch Forms

Interactive, approval-capable:

```powershell
codex --enable goals -C C:\Users\MSI\Documents\ai-trading-agent -s workspace-write -a on-request
```

Then paste the goal prompt above.

Non-interactive file launch, if no interactive `/goal` UI is available:

```powershell
codex exec -C C:\Users\MSI\Documents\ai-trading-agent -s workspace-write -a on-request < research\program_control\EXPANDED_OOS_FULL_UNBLOCKING_GOAL_PROMPT_2026-05-04.md
```

Do not use `-a never` if the run needs Databento/network/filesystem escalation; the agent will be unable to receive runtime approvals and may be forced to write blocker notes.
