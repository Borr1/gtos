# G12 Live Forward Evidence Capture Hardening Audit Goal Prompt

Date: 2026-05-12
Owner lane: independent audit of main commit `3faa2b70 research: harden live forward evidence capture`
Evidence class: `G12_LIVE_FORWARD_EVIDENCE_CAPTURE_HARDENING_AUDIT_ONLY`
Target commit: `3faa2b70`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags for research artifacts: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Objective

Independently audit the main live/research hardening commit. This audit must verify that the commit improves source capture, append-only evidence selection, live monitoring integrity, missed-fill study tooling, daemon/lock robustness, and timeout-trailing anchoring without accidental unsafe trading behavior, broker-order mutation, prompt/config/risk/safety/canary/selector drift, raw sensitive data commits, or hidden validation/performance claims.

Be evidence-bound and fair. Do not manufacture blockers or vague warnings. If an issue can be resolved inside this audit lane by rereading the commit, recomputing reports, refreshing context, stabilizing verifier output, or rerunning targeted tests, do that before deciding. Block only on exact file/line/test/scoped-diff/runtime-surface/no-leak/evidence-class failures.

This is not a promotion or edge-selection audit. Do not reject or weaken the artifact because it does not prove performance, does not produce an OB-only conclusion, or opens monitoring routes beyond the current GTOS edge. Absence of validation/R/PnL/win-rate/expectancy is required in this lane, not a defect. Accept source/control hardening if the commit is scoped, tested, auditable, no-leak, and safe inside this evidence class.

New monitoring, capture, or research-control doors are acceptable when they are auditable, source/control scoped, no-leak, and routed to exact next evidence classes. Do not collapse the audit back to the existing OB edge or reject merely because a safe route is broader than current production logic.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read `git show --stat --name-only 3faa2b70` and the full diff for every source/script/test/report file changed by `3faa2b70`.

## Required Audit Checks

1. Verify the exact FVG/OB geometry capture path:
   - `src/research_infra/forward_capture.py`
   - `scripts/backfill_fvg_ob_confluence_source_geometry.py`
   - `src/research_infra/fvg_ob_confluence_audit.py`
   - maintenance/checklist wiring and tests.
2. Verify append-only evidence selection cannot allow a later source-blocked placeholder to override a recovered/source-richer row unless that is explicitly intended and tested.
3. Verify missed-fill entry-geometry study tooling is preregistered, source/read-only, no-API, no-execution, and does not claim market-entry profitability, R, PnL, win rate, expectancy, or promotion.
4. Verify daemon/runtime changes:
   - tick-capture time-based flush and broker-time query behavior,
   - lock reclaim only when argv marker mismatch is positively identified,
   - watchdog detached launch/lock-claim handling,
   - live monitor KZ grace behavior.
5. Verify orchestrator timeout-trailing anchor change is intentionally limited to late fills and does not change order entry, order placement, AI decisions, risk sizing, safety gates, or broker account/order-history reads.
6. Verify account-history reader changes deduplicate read-only exported deal files and do not commit raw account-history data.
7. Verify modified research-infra audits/tests use the shared evidence selector consistently and preserve documented no-leak/source-control boundaries.
8. Run targeted tests with a repo-local pytest base temp:
   `python -m pytest tests/test_forward_capture_shadow_loggers.py tests/test_fvg_ob_confluence_audit.py tests/test_fvg_ob_confluence_source_geometry_backfill.py tests/test_daily_monitoring_checklist.py tests/test_verify_shadow_log_integrity.py tests/test_live_shadow_gap_closure.py tests/test_decision_layer_diagnostics_join.py tests/test_exit_management_no_event_audit.py tests/test_opportunity_lifecycle_audit.py tests/test_pending_limit_lifecycle_audit.py tests/test_v2_structural_selector_readiness.py tests/test_tick_capture.py tests/test_mt5_daemon_runtime.py tests/test_orchestrator.py tests/test_missed_fill_opportunity_study.py -q -p no:cacheprovider --basetemp .pytest_tmp`
9. Verify no staged/tracked raw `shadow_logs/`, `data/account_history/`, large raw market blobs, credentials, remote pushes, validation/result scoring, or prompt/config/risk/safety/canary/selector edits were included in `3faa2b70`.
10. Ledger unrelated live/runtime dirt as unscoped. Do not let live session churn become a blocker unless it overlaps the target commit or a forbidden surface.

## Required Outputs

Create an audit route under:

`research/science_program_2026_05/06_outcome_testing/g12_live_forward_evidence_capture_hardening_audit/`

Required artifacts:

- decision ledger JSON and Markdown,
- commit diff scope audit,
- FVG/OB geometry capture audit,
- append-only evidence-selection audit,
- missed-fill study audit,
- daemon/watchdog/orchestrator safety audit,
- no-leak/raw-data/forbidden-surface audit,
- test result artifact,
- verifier script, focused tests if useful, verification result,
- completion audit,
- next repair prompt if blocked or next monitoring prompt if accepted.

## Completion Standard

Terminal decision must be exactly one of:

- `ACCEPT_AS_G12_LIVE_FORWARD_EVIDENCE_CAPTURE_HARDENING_CONTROL_EVIDENCE`
- `REPAIR_LIVE_FORWARD_EVIDENCE_CAPTURE_HARDENING_BEFORE_RELIANCE`

Commit all scoped audit artifacts. Mark complete only when the verifier/test evidence supports the terminal decision. Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` for research artifacts. Do not open validation, result scoring, strategy-edge claims, AI/API, paid/vendor access, broker account/order/history/deal/position reads, raw market/account data commits, live restart, remote push, or prompt/config/risk/safety/execution/canary/selector changes.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G12_LIVE_FORWARD_EVIDENCE_CAPTURE_HARDENING_AUDIT_GOAL_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight/context refresh first and do not rely on chat memory; independently audit main commit 3faa2b70 from disk, inspect every changed source/script/test/report file, verify FVG/OB exact geometry capture and backfill, shared append-only evidence selection, missed-fill study tooling, tick-capture/daemon/watchdog/orchestrator timeout changes, no-leak/raw-data/forbidden-surface scope, and run the targeted 287-test command with --basetemp .pytest_tmp; be evidence-bound and fair, do not invent hypothetical blockers, do not collapse to OB-only, treat auditable new doors as valid next-route evidence, repair/recompute inside this G12 lane when possible, and block only on exact file/line/test/scoped-diff/runtime-surface/evidence-class failures; preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false and open no validation/result/AI/API/paid/broker/raw-data/live-restart/prompt-config-risk-safety-execution-canary-selector surface; commit audit artifacts and mark complete only when the prompt completion standard is fully satisfied.`
