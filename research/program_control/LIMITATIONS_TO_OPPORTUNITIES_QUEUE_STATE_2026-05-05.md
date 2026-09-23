# Limitations To Opportunities Queue State - 2026-05-05

**Schema:** `limitations_to_opportunities_queue_state_v1`
**Generated:** `2026-05-05T06:23:11.021682+00:00`
**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Source plan:** `research\program_control\LIMITATIONS_TO_OPPORTUNITIES_ENGINEERING_PLAN_2026-05-05.md`
**Source coverage audit:** `research\program_control\LIVE_SHADOW_FOLLOWUP_COVERAGE_AUDIT_2026-05-04.json`

## Summary

- LTO items: `40`
- LIVE-FOLLOW rows mapped: `34` / `34`
- Unmapped LIVE-FOLLOW rows: `none`
- Missing coverage IDs from plan: `none`
- Promotion-allowed items: `none`

## Status Counts

| Status | Count |
|---|---:|
| `APPROVAL_BLOCKED` | 1 |
| `DONE` | 37 |
| `SOURCE_BLOCKED` | 2 |

## Queue

| LTO | Status | Follow IDs | Coverage statuses | Blocker / note |
|---|---|---|---|---|
| `LTO-040` Research Queue / Master Backlog Integration | `DONE` | `LIVE-FOLLOW-032` | `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-034` Live Monitoring Goal / Runbook Persistence | `DONE` | `LIVE-FOLLOW-032` | `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-039` Shadow Log Integrity And Semantic Data Health | `DONE` | `LIVE-FOLLOW-001`, `LIVE-FOLLOW-003B` | `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-001` AI-Independent MSO Evaluation Anchor | `DONE` | `LIVE-FOLLOW-001` | `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-002` AI Candidate Registry And External Confluence | `DONE` | `LIVE-FOLLOW-002` | `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-003` Candidate Path Follow | `DONE` | `LIVE-FOLLOW-003` | `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-004` Opportunity Duplicate Lifecycle | `DONE` | `LIVE-FOLLOW-003B` | `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-005` Pending-Limit Lifecycle Truth | `DONE` | `LIVE-FOLLOW-004` | `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-006` V2b Forward Pair Resolution | `DONE` | `LIVE-FOLLOW-003`, `LIVE-FOLLOW-005`, `LIVE-FOLLOW-025` | `LIVE_SNAPSHOT_PLUS_DISCOVERY_ONLY_BLOCKER`, `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-007` V3 / Pre-Fill Delivery Path | `DONE` | `LIVE-FOLLOW-003`, `LIVE-FOLLOW-006` | `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-008` FVG/OB Confluence And Disagreement | `DONE` | `LIVE-FOLLOW-007` | `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-009` Context/Control Ledger For CL/ZN/VIX/VXM | `DONE` | `LIVE-FOLLOW-008` | `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-015` Broker Actual-R, Slippage, Cost, And Exit Accounting | `DONE` | `LIVE-FOLLOW-012`, `LIVE-FOLLOW-013`, `LIVE-FOLLOW-018`, `LIVE-FOLLOW-023` | `LIVE_HOOK_READY_WAITING_FOR_EXIT_TRIGGER_ROWS`, `PARTIAL_EXIT_FLOW_PLUS_BLOCKER`, `ROWS_PRESENT`, `VERIFIER_REQUIRED_WITH_LOCAL_ROWS` | artifact-backed queue/checklist control work exists |
| `LTO-025` Account/PnL Truth And Evidence-Class Separation | `DONE` | `LIVE-FOLLOW-012`, `LIVE-FOLLOW-023` | `PARTIAL_EXIT_FLOW_PLUS_BLOCKER`, `VERIFIER_REQUIRED_WITH_LOCAL_ROWS` | artifact-backed queue/checklist control work exists |
| `LTO-026` Trade Index Staleness And Lifecycle Completeness | `DONE` | `LIVE-FOLLOW-004`, `LIVE-FOLLOW-024` | `ROWS_PRESENT`, `VERIFIER_REQUIRED_WITH_KNOWN_GAP` | artifact-backed queue/checklist control work exists |
| `LTO-010` Databento Targeted Live Confluence | `DONE` | `LIVE-FOLLOW-009`, `LIVE-FOLLOW-011`, `LIVE-FOLLOW-031` | `DOCUMENTED_SOURCE_BLOCKERS`, `ROWS_PRESENT` | Owner-approved value-max trigger policy, cost cap, cooldown, env/API gate, and dry-run tooling are implemented; live Databento is no longer owner-approval-blocked but still requires enabled collector env/API key and a registered trigger. |
| `LTO-011` NAS100/NQ Orderflow Adverse-Selection Diagnostic | `DONE` | `LIVE-FOLLOW-011` | `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-012` Sierra Local Depth Confluence | `DONE` | `LIVE-FOLLOW-010` | `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-013` Sierra Source/Parity Registry | `DONE` | `LIVE-FOLLOW-002`, `LIVE-FOLLOW-010`, `LIVE-FOLLOW-028` | `ROWS_PRESENT`, `SOURCE_STATUS_BLOCKED_WITH_TRIGGER` | artifact-backed queue/checklist control work exists |
| `LTO-014` GBPJPY Sierra/Databento Proxy Gap | `DONE` | `LIVE-FOLLOW-022` | `BLOCKED_WITH_EVIDENCE_AND_TRIGGER` | artifact-backed queue/checklist control work exists |
| `LTO-030` 6B Sampling Alignment And SI Depth Definition | `DONE` | `LIVE-FOLLOW-028` | `SOURCE_STATUS_BLOCKED_WITH_TRIGGER` | artifact-backed queue/checklist control work exists |
| `LTO-031` External Feed Blockers | `SOURCE_BLOCKED` | `LIVE-FOLLOW-029` | `DOCUMENTED_SOURCE_BLOCKERS` | Named external sources require legal access path, cache schema, and publication-time/no-lookahead convention before validation. Artifacts: `research\program_control\LTO031_EXTERNAL_FEED_SOURCE_READINESS_2026-05-05.md`, `shadow_logs\lto_blocked_lane_status.jsonl`. |
| `LTO-032` Options/Gamma, VRP, FlashAlpha Basic GEX | `SOURCE_BLOCKED` | `LIVE-FOLLOW-030` | `PARTIAL_FORWARD_CONTEXT_PLUS_SOURCE_BLOCKERS` | Options/gamma/VRP/GEX work requires legal timestamped source evidence before historical or forward collection. Artifacts: `research\program_control\LTO032_OPTIONS_GAMMA_SOURCE_READINESS_2026-05-05.md`, `shadow_logs\lto_blocked_lane_status.jsonl`. |
| `LTO-033` X-1/X-2/X-3 Imbalance / Meta-Order-Flow Primitives | `DONE` | `LIVE-FOLLOW-009`, `LIVE-FOLLOW-031` | `DOCUMENTED_SOURCE_BLOCKERS`, `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-021` Exit-Management Shadows: BE, Partial Close, Time In Trade | `DONE` | `LIVE-FOLLOW-018` | `LIVE_HOOK_READY_WAITING_FOR_EXIT_TRIGGER_ROWS` | artifact-backed queue/checklist control work exists |
| `LTO-022` Session Volatility And US30 Sweep Divergence | `DONE` | `LIVE-FOLLOW-019` | `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-036` Watchdog, Canary Skip, And Restart Governance | `DONE` | - | - | artifact-backed queue/checklist control work exists |
| `LTO-037` Notification Queue Dead-Zone Policy | `DONE` | - | - | artifact-backed queue/checklist control work exists |
| `LTO-038` Storage, Retention, And Non-Overwrite | `DONE` | - | - | artifact-backed queue/checklist control work exists |
| `LTO-016` J46-J49 Exit Policy Comparator | `DONE` | `LIVE-FOLLOW-013` | `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-017` S79 / Side-Aware Compounding Context | `DONE` | `LIVE-FOLLOW-014` | `CONFIG_PRESENT_WAITING_FOR_FORWARD_STRATEGY_ROWS` | artifact-backed queue/checklist control work exists |
| `LTO-018` Regime Classifier And Monthly Decay | `DONE` | `LIVE-FOLLOW-015` | `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-019` Decision-Layer Diagnostics | `DONE` | `LIVE-FOLLOW-016` | `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-020` Mechanical Baselines, Proximity, Liquidity, Displacement, Structure Divergence | `DONE` | `LIVE-FOLLOW-017` | `ROWS_PRESENT` | artifact-backed queue/checklist control work exists |
| `LTO-023` K55 / ML Shadow | `DONE` | `LIVE-FOLLOW-020` | `ROWS_PRESENT` | Owner-approved read-only ML shadow path is implemented after target refresh/preregistration; prediction remains disabled until a matching registered model artifact exists, and no decision impact or promotion is allowed without a separate dossier. |
| `LTO-024` Component 3B / Tool Grounding / Reflexion | `APPROVAL_BLOCKED` | `LIVE-FOLLOW-021` | `EXPLICIT_OWNER_APPROVAL_BLOCKED` | Component 3B/tool-grounding/Reflexion must not wire or call AI without explicit owner approval. Artifacts: `research\program_control\LTO024_COMPONENT3B_TOOL_GROUNDING_REFLEXION_APPROVAL_DOSSIER_2026-05-05.md`, `shadow_logs\lto_blocked_lane_status.jsonl`. |
| `LTO-027` V2 Structural Oracle / As-Of Selector | `DONE` | `LIVE-FOLLOW-005`, `LIVE-FOLLOW-025` | `LIVE_SNAPSHOT_PLUS_DISCOVERY_ONLY_BLOCKER`, `ROWS_PRESENT` | Promotion-readiness audit is implemented and remains shadow-only: MT5 account history is used for filled broker outcomes where available, while unresolved shadow alternatives, exact V2 lock metadata, concentration, lifecycle, and preregistered dossier gates still block promotion. |
| `LTO-028` XAUUSD Same-Market Structural Path Extension | `DONE` | `LIVE-FOLLOW-026` | `SOURCE_STATUS_REQUIRED_WITH_FORWARD_SNAPSHOT` | XAUUSD same-market structural/path extension is preregistered as source-status only with outcomes closed at registration and live rows separated from replay evidence. |
| `LTO-029` ES/MES Strategy-Cohort Pre-Registration | `DONE` | `LIVE-FOLLOW-027` | `PRE_REGISTRATION_REQUIRED` | ES/MES strategy cohort is preregistered as context/control and future separate-cohort source status only, with source mapping, session windows, evidence classes, no-lookahead rules, and closed outcomes documented. |
| `LTO-035` No-AI MSO Shadow Observer Instruments | `DONE` | `LIVE-FOLLOW-008`, `LIVE-FOLLOW-033` | `ROWS_PRESENT` | No-AI/no-execution observer hardening is implemented with a source/proxy/evidence-class registry, stale detection, restart policy, and GER40 final-closeout evidence; it does not enable new instruments or open outcomes. |

## Guardrails

- This queue is research/tooling only.
- It does not validate, promote, or modify live trading behavior.
- Every item remains `NO_PROMOTION_VERDICT` until a separate promotion dossier exists.
- Rows marked source-, approval-, or event-blocked must not be fabricated from later data.
