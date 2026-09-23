# Forward Capture And Intelligence Infrastructure Goal Prompt - 2026-05-04

Status: active launch wrapper
Scope: research/tooling plus additive fail-open shadow infrastructure
Promotion posture: `NO_PROMOTION_VERDICT`

Use this file to start the next fresh `/goal` or `codex exec` session.

The full durable prompt is:

- `research/program_control/FORWARD_CAPTURE_AND_INTELLIGENCE_INFRASTRUCTURE_GOAL_PROMPT_2026-05-04.md`

## Short Starter Prompt

```text
Forward capture and intelligence infrastructure goal for GTOS.

You are working in C:\Users\MSI\Documents\ai-trading-agent.

Use `research/program_control/FORWARD_CAPTURE_AND_INTELLIGENCE_INFRASTRUCTURE_GOAL_PROMPT_2026-05-04.md` as the active goal specification.

Mandatory first actions:
1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest handoff in `.context\02_session_handoffs\`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_OWNER_DEEP_DIVE_REPORT_2026-05-04.md`.
8. Read `research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_FINAL_SYNTHESIS_2026-05-04.md`.
9. Read `research/operations/pending_limit_lifecycle_telemetry_integration_ticket_2026-05-03.md`.
10. Read `research/program_control/AI_AND_ORDERFLOW_EXECUTION_DISCUSSION_CONTEXT_2026-05-03.md`.

Then execute the goal from the full prompt.

Core posture:
- Exhaustive infrastructure-readiness pass, not a ranked top-priority pass.
- Every action item from the deep dive should end as implemented, shadow-only active, research-artifact done, waiting for forward rows with collector active, or blocked with evidence and trigger.
- Databento API usage is allowed for targeted, declared, cost-logged forward/event-window capture.
- Sierra `.scid` and `.depth` should be used for forward/recent full-depth infrastructure where source status allows it.
- Additive fail-open shadow logging is allowed when it cannot affect live decisions and has tests.
- No live trading logic, prompt behavior, risk settings, execution decisions, safety gates, or order-placement behavior may change.
- Preserve `NO_PROMOTION_VERDICT`.

Done means:
- Master action ledger exists.
- Pending-limit lifecycle/actual broker-R/V2b/pre-fill/orderflow/confluence/cost/source/claim-ledger/monitoring items are each resolved to a concrete status.
- New collectors/loggers/tools have focused tests.
- Databento and Sierra forward-capture readiness is documented and wired where feasible.
- A monitoring-session runbook/prompt exists for checking that all forward logs and data captures are filling.
- Final synthesis states exact completed files, tests, commits, blockers, and `NO_PROMOTION_VERDICT`.
```

## Non-Interactive Launch Form

```powershell
codex exec -C C:\Users\MSI\Documents\ai-trading-agent -s workspace-write -a on-request < .context\05_operations\FORWARD_CAPTURE_AND_INTELLIGENCE_INFRASTRUCTURE_GOAL_PROMPT_2026-05-04.md
```

Use `-a on-request` if Databento/network/filesystem approvals should be available. Use `-a never` only if the session should write blocker notes instead of stopping for approvals.

