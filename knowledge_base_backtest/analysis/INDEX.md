# Analysis Index

All analysis files with timestamps. Newest first.

| Date | File | Description | Status |
|------|------|-------------|--------|
| 2026-04-02 | phase0_corrected_0.md | **Phase 0 CORRECTED: Naive is near-zero with proper stops (p=0.264). AI precision confirmed (+100% MFE$). "Trade more" conclusion REVERSED. HOLD.** | CURRENT |
| 2026-04-02 | phase0_corrected_data_0_1959.json | Corrected naive baseline data (318 trades, 4 strategies, 5 TP levels) | CURRENT (data) |
| 2026-04-02 | phase0_baseline_diagnostic_0.md | Phase 0 original — FLAWED: broken SL methodology inflated results. See corrected version. | SUPERSEDED |
| 2026-04-02 | phase0_naive_baseline_data_0_1920.json | Original Phase 0 data — broken SL methodology | SUPERSEDED |
| 2026-04-02 | supplementary_replay_report_0.md | **Supplementary replay: 55 random dates, 4 trades (all losses), combined p=0.246 NOT significant. BE move validated. DEPLOY AS-IS MONITOR.** | CURRENT |
| 2026-04-02 | supplementary_replay_0_1643.json | 4 new trades with full r_path (candle-by-candle R) | CURRENT (data) |
| 2026-04-02 | supplementary_pa_responses_0_1643.jsonl | 287 PA responses with reasoning text for selection effect analysis | CURRENT (data) |
| 2026-04-02 | supplementary_candle_log_0_1643.json | 1,088 candle evaluations from 55 dates | CURRENT (data) |
| 2026-04-02 | deep_trade_analysis_0.md | **Deep trade analysis: exit optimization (+78% R with 2.0R TP), loser autopsy, patience effect, temporal patterns, 6 prioritized recommendations** | CURRENT |
| 2026-04-02 | deep_trade_analysis_data_0_1439.json | Per-trade R-paths, simulation results, feature vectors (data companion to deep analysis) | CURRENT (data) |
| 2026-04-02 | prelaunch_audit_0_0600.md | Pre-launch system audit: config consistency, safety checks, execution engine, preflight checklist | CURRENT |
| 2026-04-02 | tp1_fix_validation_sonnet_0_0529.md | **TP1 fix validation: 36 trades, +0.335R exp, 52.8% WR, PF 2.01 — GO** | CURRENT |
| 2026-04-02 | bugfix_validation_report_20260401_1822.md | Bug fix report: TP1 placement, outcome labeling, null params | CURRENT |
| 2026-04-02 | replay_blitz_report_0.md | Replay blitz NO-GO: 7 trades, -0.48R exp. Bugs found in TP1 placement + outcome labeling | SUPERSEDED — TP1 bug invalidates results |
| 2026-04-02 | vertical_analysis_report_0.md | Vertical analysis of system components | CURRENT |
| 2026-04-02 | displacement_investigation_0.md | Investigation of displacement quality thresholds | CURRENT |
| 2026-04-02 | feasibility_checks_report_0.md | Feasibility checks for system deployment | CURRENT |
| 2026-04-01 | vision_ab_test_report_20260401.md | Vision vs text-only A/B test results | CURRENT |
| 2026-03-31 | full_analysis_report_20260331.md | Full system analysis report | CURRENT |
| 2026-03-31 | codebase_audit_20260331.md | Codebase structure and quality audit | CURRENT |
| 2026-03-31 | session1_deep_analysis_20260331.md | Session 1 deep dive analysis | CURRENT |
| 2026-03-31 | session3_validation_report_20260331.md | Session 3 validation results | CURRENT |
| 2026-03-31 | session4_smoke_test_report_20260331.md | Session 4 smoke test | CURRENT |
| 2026-03-31 | timeout_policy_analysis_20260331.md | Analysis of session timeout policy | CURRENT |
| 2026-03-31 | tp_optimization_detailed_20260331.md | Take-profit optimization analysis | SUPERSEDED — TP1 bug found |
| 2026-03-31 | unified_trades_v2_20260331.json | 111 trades unified dataset (old system) | CURRENT (data) |
| 2026-03-31 | unified_trades_20260331.json | Original unified trades dataset | SUPERSEDED by v2 |
| 2026-03-30 | candidate_review_20260330.json | Candidate trade review data | CURRENT (data) |

## Data Files
| File | Description |
|------|-------------|
| session1_decisions_20260331.json | Session 1 decision log |
| tp_optimization_20260331.json | TP optimization raw data |

## Subdirectories
| Directory | Description |
|-----------|-------------|
| replay/ | Replay session results (replay_results.json, replay_candle_log.json) |
| sample_charts/ | Sample chart images |
