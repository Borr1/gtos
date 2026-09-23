# G10 Context Ledger

Generated: 2026-05-06T08:30:00Z
Lane: G10
Promotion verdict: NO_PROMOTION_VERDICT

| Context item | Repo/source evidence | G10 interpretation | Action |
|---|---|---|---|
| Internal pending intent | `src/components/execution.py:72`, `src/components/execution.py:577`, `src/components/execution.py:753`; `src/components/pending_limit_lifecycle_logger.py:18` | GTOS limit placement is an internal lifecycle state, not broker-native pending exposure. | Preregister lifecycle-no-fill experiments before any execution claim. |
| Market-order translation after trigger | `src/components/execution.py:480`, `src/components/execution.py:910` | Actual fill quality depends on tick availability, spread, slippage, retcode, and deal record after internal trigger. | Join pending lifecycle, slippage rows, and MT5 account history. |
| Slippage telemetry | `src/components/slippage_shadow_logger.py:1`, `research/operations/COST_SLIPPAGE_EXIT_ACCOUNTING_COVERAGE_2026-05-05.md` | Entry logging exists; close-side evidence is missing at current audit. | Cost/friction hypotheses remain blocked for promotion. |
| J46/J49 policy | `src/components/j46_j49_policy.py:1`, `src/components/execution.py:1306`, `src/components/execution.py:1721`, `src/components/execution.py:1759` | Exit policy is active and specific; successors must isolate BE, time stop, target, and close cost effects. | Use target-trial preregs and label separation. |
| Risk gates | `src/components/permissions.py:201`, `src/components/concurrent_tracker.py:1`, `src/components/drawdown_manager.py:1` | Daily loss, concurrency, and drawdown reduction are operational controls, not alpha evidence. | Shadow rule-distance only; no parameter changes. |
| Correlation gates | `src/components/portfolio_risk.py:1`, `src/components/cross_instrument_correlation_gate.py:1` | Portfolio exposure is group/correlation constrained and path-dependent. | Study candidate-to-position opportunity cost context only. |
| V3 path scaling | `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_FULL_EXPLORATORY_REPLAY_2026-05-03.md` | Exploratory synthetic replay is useful for mechanism discovery but not validation. | Freeze future preregs before outcome review. |
| Historical pre-fill path coverage | `research/phase_3_external_feed_validation/RAW_OHLC_PREFILL_DELIVERY_PATH_COVERAGE_2026-05-03.md` | Historical replay lacks original POI bounds and broker lifecycle state. | Require prospective lifecycle rows. |
| Broker actual-R audit | `research/program_control/LTO015_BROKER_ACTUAL_R_AUDIT_2026-05-05.md` | Only 3 rows permitted actual-R claims in that audit. | Broker-actual hypotheses need larger joined sample. |
| FTMO official rules | `raw/G10_execution_risk_sources_2026-05-06/ftmo_trading_objectives.html:2247`, `:2278`, `:2317`, `:2338` | Current official rule context was cached but is not edge validation. | Source contract validation_safe=false. |
| redacted_account daily loss article | `raw/G10_execution_risk_sources_2026-05-06/redacted_account_daily_loss_limit.html:1` | Page was cached and timestamped, but minified body parsing is incomplete. | Source contract validation_safe=false and parser blocker retained. |
| G1 neighbor | `research/science_program_2026_05/01_domain_syntheses/G1_VALIDATION_STATISTICS_SYNTHESIS_2026-05-06.md` | Execution experiments inherit leakage, DSR/PBO, and effective-N standards. | Apply to every prereg. |
| G6 neighbor | `research/science_program_2026_05/01_domain_syntheses/G6_MOMENTUM_REVERSION_DOMAIN_SYNTHESIS_2026-05-06.md` | OB/no-retrace mechanisms depend on fill path and execution friction. | Add cross-domain execution-friction hypothesis. |
| G9 neighbor | Only `G9_G9_AI_ML_SYSTEMS_GOAL_PROMPT_2026-05-06.md` exists. | G9 synthesis was not available. | Block G9-dependent rows. |

Final ledger verdict: NO_PROMOTION_VERDICT.
