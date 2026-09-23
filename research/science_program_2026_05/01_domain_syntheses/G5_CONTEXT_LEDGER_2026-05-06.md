# G5 Lane Context Ledger

Generated: 2026-05-06T07:00:00Z
Lane: G5
Promotion verdict: NO_PROMOTION_VERDICT

## Preflight Context Read

- `.context/LIVE_STATE.md`: fresh live-state file generated before the pass; G5 branch started clean except regenerated live-state runtime dirt.
- `.context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md`: historical no-forward-data handoff; no live behavior changes allowed.
- `.context/00_core/quick_reference_card.md`: GTOS operational constraints and live-safety context.
- `.context/00_core/research_operating_doctrine.md`: aggressive research, strict promotion, cached/source-indexed evidence first.
- `.context/00_core/research_current_state.md`: primitive science scaffold current; source/budget ledger `$0`; no live changes.
- `.context/00_READING_ORDER.md`: required context order followed.
- `CLAUDE.md`: live-trading restrictions and repo conduct.
- `research/science_program_2026_05/00_control/*`: G0 governor, schema contracts, source budget ledger, master registries, and status registry read.
- Tier 2-4 artifacts: architecture, edge mechanisms and risks, gold market knowledge, validation/monitoring framework, and 113-question execution plan.

## Repo Cross-Checks

### Crowding And Decay

- `.context/01_knowledge_base/edge_mechanism.md` identifies pattern crowding as a possible reversal/TP decay source, with OB continuation and average TP/SL drift as monitorable signals.
- `research/monthly_decay_monitor/DESIGN.md` defines monthly/weekly edge decay monitoring.
- `.context/03_analysis/SWOT_FINAL.md` flags edge crowding over time and OB continuation logging as decay evidence.

Status: active/shadow monitoring exists; no promotion evidence.

### Dumb Baseline And AI Increment

- `research/dumb_momentum_baseline/REPORT.md` states AI+OB may be unnecessary, the dumb-baseline shadow logger exists, FVG alone may invert continuation, and same-window samples cannot reject honest dumb-baseline rates.
- `research/program_control/AI_AND_ORDERFLOW_EXECUTION_DISCUSSION_CONTEXT_2026-05-03.md` frames the owner concern: AI may be weakest and must be measured against mechanical challengers.
- `research/program_control/AI_DECISION_LAYER_SHADOW_READINESS_2026-05-04.md` requires paired forward rows before any AI decision-layer claim.
- `research/ml_program/audit/LANE5_REMAINING_ARCH_ML_QUALITY_TRIAGE_2026-05-03.md` says no paired live AI+ML shadow is available and production requires a dossier.

Status: shadow-only; prompt-neutral tests blocked by API budget and live-prompt no-touch rule.

### Retail Flow, Stop Clusters, And Herding

- `research/ml_program/audit/LANE6_ASSET_RISK_EDGE_TRIAGE_2026-05-03.md` says production trade records are GTOS levels, not counterparty stop observations.
- The same audit marks C-2 and E-4 blocked due missing counterparty stop placements, broker client positioning, IG/OANDA sentiment, retail-flow share, Google Trends, or social-flow datasets.
- `research/program_control/DATA_AND_APPROVAL_GATE_RECLASSIFICATION_2026-05-03.md` says retail-flow/crowding and counterparty stop placement need direct or legal proxy data; futures depth is not the same object.
- `research/program_control/MASTER_RESEARCH_QUEUE_STATE_2026-05-03.json` records E-4 retail-flow/crowding blocked and K54 Osler proxy failed below-noise.

Status: blocked for validation; can only become source-contract and preregistration work.

### News And Calendar Attention

- `src/components/news_calendar.py` implements the news calendar component, returns no skip when disabled/no events, and warns on stale JSON calendar sources.
- `src/components/orchestrator.py` wires `NewsCalendar`.
- `config/agent_config.yaml` has `news_filter.enabled: true` and notes it replaces the economic calendar.
- `scripts/refresh_economic_calendar.py` detects stale calendar files and does not auto-fetch; operator update remains required.

Status: active live filter exists but untouched; research row is source freshness/cohort labeling only.

### Backlog/Research Queue

- `.context/backlog_synthesis_2026-04-18/research_wf2_open_items.md` lists Fed linguistic sentiment, Google Trends SVI, and prompt-neutral rerun as not wired or not run.
- `.context/backlog_synthesis_2026-04-18/00_MASTER_BACKLOG.md` lists AI news-scan shadow logging, Google Trends SVI, prompt-neutral rerun budget, and AI vs mechanical OB entry concerns.
- `.context/03_analysis/research_execution_plan_113q.md` includes narrative fitting, crowding measurement, herd behavior, predatory/forced flow, retail herding, crowded strategies, and disposition effect.

Status: research backlog exists; G5 converts selected items into source contracts and preregistered rows only.

## Neighbor Lane Check

- G4: branch `science-goals/g4-microstructure-auction`; untracked raw source-evidence directory exists but no committed G4 synthesis/row artifacts beyond prompts. Do not depend on uncommitted neighbor artifacts for merge.
- G6: branch `science-goals/g6-momentum-reversion`; no committed G6 row artifacts beyond prompts.
- G7: branch `science-goals/g7-macro-cross-asset`; no committed G7 row artifacts beyond prompts.

Neighbor status: cross-domain G5 rows are candidate-only and blocked until neighbor lanes publish committed outputs.

## Killed/Blocked Route Notes

- K54/Osler stop-cluster route: failed below-noise; do not reopen without direct stop-cluster/counterparty data and a preregistered cohort.
- Retail-flow share / broker sentiment / Google Trends: blocked locally; source contracts required before any validation.
- Same-dataset AI explanation: blocked; paired forward rows and label separation required.
- Calendar/source freshness: stale source can invalidate event labels; source contract required before experiment acceptance.

Promotion verdict: NO_PROMOTION_VERDICT
