# Subagent Findings Index - 2026-06-02

Route: `vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02`

Purpose: preserve raw subagent findings outside chat memory before repair planning.

Current HEAD when index was started: `5652c67e1 runtime: preserve follower target trade provenance`

## Reports Captured

| Agent | Scope | File | Status |
|---|---|---|---|
| `019e89f1-3e2b-7801-8af9-5af3345ce912` | Runtime/process/data freshness | `SUBAGENT_FINDINGS_RUNTIME_PROCESS_DATA_FRESHNESS_2026-06-02.md` | captured |
| `019e89f1-43be-7440-8220-49f16a2bc98d` | FTMO follower/profile/symbol/replay/target management | `SUBAGENT_FINDINGS_FTMO_FOLLOWER_2026-06-02.md` | captured |
| `019e89f1-4231-7852-b303-d56e7319e58b` | Execution/risk/trade lifecycle | `SUBAGENT_FINDINGS_EXECUTION_RISK_LIFECYCLE_2026-06-02.md` | captured |
| `019e89f1-4076-7d72-aea5-625490eb6253` | Candidates/selectors/V3 | `SUBAGENT_FINDINGS_CANDIDATES_SELECTORS_V3_2026-06-02.md` | captured |

## Immediate Cross-Agent Defect Classes

These are not final repair-plan decisions; they are the merged defect classes already visible from returned agents.

1. FTMO target-state provenance:
   - active target rows had `intent_id: null`;
   - legacy active target rows had blank `cash_risk_amount_source/status`;
   - commit `5652c67e1` repairs intent persistence and restored cash-risk provenance, but a controlled follower reload was still pending when the hold began.
2. Live aggregate open-risk fallback:
   - source and FTMO open-position risk can fall back to tick metadata when `order_calc_profit` fails;
   - live selected-cell new-entry sizing is already broker-verified, but aggregate admission risk still needs fail-closed broker valuation.
3. Tick/M1 freshness:
   - GER40 and UK100 had null tick progress/stale M1 rows while watchdog reported OK;
   - SPX500 restarted but failure cause logging was weak.
4. M1 namespace leak:
   - orchestrator no-candidate source packets can read unnamespaced `pipeline_state/m1_capture_state.json`.
5. FTMO replay and outcome classification:
   - checkpoint `processed_intent_count` does not distinguish copied, risk-blocked, stale-skipped, source-terminal-missed, and retryable-failed outcomes.
6. Entry deal ticket self-sufficiency:
   - source trade records keep `entry_deal_ticket: null` even when slippage/broker history captured the broker entry deal.
7. Shadow R denominator corruption:
   - partial/BE/trailing shadow logs can use a near-zero mutated BE stop denominator and emit impossible R values.
8. Launcher/watchdog command construction:
   - duplicate FTMO follower `--replay-existing` flag;
   - maintenance guard false-positive on pytest process substrings;
   - old `wmic` launcher/logging remains weak.
9. Candidate and selector log truth:
   - runtime and strategy-follow logs are non-chronological without sequence ids;
   - safety-gate blocked rows contradict candidate generation status;
   - strategy-follow ledgers still expose stale J46/J49/primary-analyzer labels;
   - trade records retain false AI approval labels on pre-AI vNext records;
   - pending lifecycle rows are not self-sufficient for decision-time replay.

## Current Handling State

- Reports are evidence inputs, not final closure.
- Each finding still requires main-session reconciliation against raw disk/code/runtime evidence before repair or closure.
- All four requested subagent reports are captured on disk.
