# vNext Production Change Stage08 AI Supervisor Dossier

Created: 2026-05-25T09:31:40.603916Z

## Runtime Change

- Added `src/components/ai_supervisor.py` as a bounded schema guardian and diagnostics engine.
- The supervisor monitors AI trace hash health, malformed responses, schema/parse failures, token-cost telemetry, route drift, missing source-bound prompt fields, stale artifact loads, and abnormal candidate clusters.
- The supervisor can disable active AI-narrowing effects by forcing `pre_ai_apply_to_ai_call=false` and `ai_policy_apply_to_ai_call=false` in an effective config copy.
- It never changes trade direction, trade parameters, prop budget math, or candidate scoring.
- Formatting repair only extracts an intact JSON object and then relies on `PrimaryAnalysisOutput` schema validation.

## Evidence Consumed

- Stage08 decision-surface groups: 51.
- Stage08 decision-map rows: 149.
- Runtime surfaces: {"legacy_no_match_non_override_guard": 3, "pending_policy_nofill_limit_market_selector": 12, "pre_ai_route_selector_and_ai_narrowing": 12, "risk_adjustment_and_prop_safe_selector": 12, "route_decision_scorer_filter_router": 12}.
- Source components: {"rejected_candidate_c1_failed_value": 51}.

## Scenario Coverage

- Runtime scenario rows: 7.
- Action counts: {"DISABLE_AI_NARROWING": 4, "HEALTHY": 1, "SUPERVISOR_DISABLED": 1, "WARN": 1}.
- Severity counts: {"critical": 4, "disabled": 1, "ok": 1, "warning": 1}.
- Format repair fixtures: 3.
- Format repair parsed counts: {"False": 1, "True": 2}.

## Activation Boundary

- `ai_supervisor.apply_runtime_overrides=true` only disables AI-narrowing active effects when configured health checks fail.
- No live trading, broker mutation, paid API/vendor call, source deletion, remote push, or activation flip is performed.
