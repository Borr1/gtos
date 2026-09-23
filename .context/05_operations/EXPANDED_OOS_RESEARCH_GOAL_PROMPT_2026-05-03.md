# Expanded OOS Research Goal Prompt - 2026-05-03

Status: active launch wrapper
Scope: research/tooling only
Promotion posture: `NO_PROMOTION_VERDICT`

Use this file to start the next fresh `/goal` or `codex exec` session.

The full durable prompt is:

- `research/program_control/EXPANDED_OOS_DATA_RESEARCH_PROGRAM_AND_GOAL_PROMPT_2026-05-03.md`

## Short Starter Prompt

```text
Expanded OOS/data-expansion research goal for GTOS.

You are working in C:\Users\MSI\Documents\ai-trading-agent.

Use `research/program_control/EXPANDED_OOS_DATA_RESEARCH_PROGRAM_AND_GOAL_PROMPT_2026-05-03.md` as the active goal specification.

Mandatory first actions:
1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest handoff in `.context\02_session_handoffs\`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `research/program_control/RESEARCH_NEXT_STEPS_AND_OPEN_QUESTIONS_PLAN_2026-05-03.md`.
8. Read `research/program_control/DATA_AND_APPROVAL_GATE_RECLASSIFICATION_2026-05-03.md`.
9. Read `research/program_control/EXPANDED_OOS_DATA_RESEARCH_PROGRAM_AND_GOAL_PROMPT_2026-05-03.md`.
10. Read `research/program_control/SIERRA_DOWNLOAD_STATUS_AND_GOAL_SESSION_NOTES_2026-05-03.md`.
11. Read `research/program_control/AI_AND_ORDERFLOW_EXECUTION_DISCUSSION_CONTEXT_2026-05-03.md`.

Then execute the goal from the full prompt.

Core posture:
- Aggressive research, strict promotion.
- This is a looping research goal, not a one-pass smoke test. Keep iterating across feasible dates, instruments, sources, regimes, and candidates until the P0-P8 queue is completed or each remaining branch has an exact blocker/trigger.
- Freeze candidate rules before opening expanded outcome data.
- Treat other dates, sources, futures proxies, regimes, and instruments as different evidence classes.
- Use the latest Sierra first-wave inventory: depth is now present for `NQM26-CME`, `MNQM26-CME`, `YMM26-CBOT`, `MYMM26-CBOT`, `GCM26-COMEX`, `MGCM26-COMEX`, `SIM26-COMEX`, `SILM26-COMEX`, `6JM26-CME`, `6BM26-CME`, `6EM26-CME`, `ESM26-CME`, `MESM26-CME`, `CLM26-NYMEX`, and `ZNM26-CBOT`.
- Do not fabricate or artifact numbers. Every statistic must trace to a saved artifact, command, source rows, or a clear `not_computable` reason.
- Do not call cross-instrument transfer live validation.
- Do not use Component 3B debate; it is parked due to extra AI/API cost.
- Preserve NO_PROMOTION_VERDICT unless a separate promotion dossier is explicitly requested.

Done means:
- Data-source map completed.
- Frozen candidate registry completed.
- Replay portability audited.
- Same-instrument temporal OOS, regime-transfer, source/proxy-transfer, and cross-instrument expansion work pursued across the feasible first-wave data, not just one sample.
- Failure/decay attribution completed.
- Final synthesis includes a completion ledger for every P0-P8 item and an ambiguity/blocker ledger with exact triggers.
```

## Non-Interactive Launch Form

```powershell
codex exec -C C:\Users\MSI\Documents\ai-trading-agent -s workspace-write -a on-request < .context\05_operations\EXPANDED_OOS_RESEARCH_GOAL_PROMPT_2026-05-03.md
```

Use `-a never` only if the session must run unattended and should write blocker notes instead of requesting network/data approvals.
