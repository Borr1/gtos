# G9 Ambiguity Ledger - 2026-05-06

**Lane:** `G9`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Ambiguities Pursued

| Ambiguity | Pursued answer | Status | Next evidence needed |
| --- | --- | --- | --- |
| Is K55 approval-blocked or already shadow-running? | LTO-023 shows K55 feature bundle rows exist and action-required is zero, but prediction-computed and inference-enabled rows are zero because the model artifact is missing. | Answered: K55 feature substrate is shadow-ready; inference is disabled. | Matching K55 JSON model artifact plus target/feature/no-leak checks. |
| Can G9 reuse K54 v3/v4 models to satisfy model-path mapping? | K55 registry and source-bundle plan reject stale K54 direct reuse; K54 v3/v4 failed current gates. | Answered: no stale K54 reuse. | New K55-compatible artifact only. |
| Is PrimaryAnalyzer already using `ai_tools`? | `ai_tools` README and actual `_call_claude` show scaffolding exists but no live `tools=` wiring. | Answered: not active. | Owner-approved shadow tool-call design and code path, outside this lane. |
| Can G9 run Component 3B debate or Reflexion now? | LTO-024 says Component 3B, tool grounding, and Reflexion remain parked and need owner budget/scope. | Answered: no API calls or wiring. | Explicit owner approval, budget cap, symbols, model, duration, stop conditions. |
| Does local literature validate debate/tool/Reflexion as GTOS improvements? | Domain 20 supports mechanism priors, but papers are not GTOS validation and often have short-horizon/cost/sample caveats. | Answered: context evidence only. | GTOS paired shadow rows with label separation and G1 methodology gates. |
| Can classical ML vs LLM be judged with current labels? | Current K55 rows are synthetic-path-context-only; broker actual-R is sparse. | Answered: comparison can be preregistered, not concluded. | Paired AI decision, K55 prediction, lifecycle, and broker actual-R sample floors. |
| Can offline RL be useful without live exploration? | Literature supports offline RL/direct reward optimization, but GTOS sample size and risk behavior boundaries block live policy changes. | Answered: offline/prereg only. | G10 neighbor evidence, frozen reward/duplicate policy, broker/path label separation. |
| Should G9 add G10 neighbor-derived rows? | G10 has only its goal prompt and no lane-owned outputs. | Answered: no G10 evidence rows yet. | Rerun neighbor pass after G10 synthesis commits. |

## Blocked Items

| Blocked item | Blocker | Owner question, if any |
| --- | --- | --- |
| Tool-grounding shadow API run | Requires AI/API calls, prompt/runtime wiring, and budget cap. | Should the owner reopen tool grounding with a scoped, no-action, budget-capped shadow design? |
| Component 3B debate shadow run | Owner parked due extra AI/API cost; LTO-024 requires DELETE/WIRE/LEAVE decision and budget/duration. | Should Component 3B remain parked, be deleted, or be reopened as budget-capped shadow only? |
| Reflexion post-trade generation | Would call an LLM and could alter future prompt/memory behavior if injected. | Should Reflexion start as offline label-generation from historical records only, or stay parked with Component 3B? |
| K55 inference artifact | Missing production K55 artifact; stale K54 direct reuse forbidden. | Should a separate K55 artifact-build goal be launched once label floors/source balance triggers are met? |
| Offline RL sizing/exit comparison | Needs G10 execution/risk lane, frozen rewards, and no live risk changes. | No owner question now; wait for G10 lane and label/sample triggers. |

## Sharper Hypotheses Produced

- K55 first value is not a live classifier; it is a no-leak paired disagreement ledger between deterministic structure, Component 3A, and a registered classical model.
- Tool grounding should be measured first as a numeric precision/hallucination audit, not as a trade-outcome uplift test.
- Debate should be measured first as disagreement and false-approval/false-rejection instrumentation, not as a production judge.
- Reflexion should first produce structured failure-mode labels for K55 and postmortem search, not next-trade memory injection.
- Offline RL should first compare to existing hand policies under frozen cost/risk accounting, not search for a live risk policy.

## NO_PROMOTION_VERDICT

This ambiguity ledger is research-only and carries `NO_PROMOTION_VERDICT`.
