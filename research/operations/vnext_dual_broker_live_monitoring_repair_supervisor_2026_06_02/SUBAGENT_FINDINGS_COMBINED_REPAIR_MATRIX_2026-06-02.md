# Combined Subagent Findings Repair Matrix - 2026-06-02

Route: `vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02`

Purpose: preserve the main-session disposition of every captured subagent finding. Priority controls execution order only; it is not a scope reduction.

## Repaired In This Tranche

| Finding Class | Root Failure | Repair | Verification |
|---|---|---|---|
| FTMO target-state `intent_id:null` and blank cash-risk provenance | Compact target-state persistence preserved trade management state but not enough source/provenance identity across restart | `scripts/dual_broker_execution_follower.py` now preserves action-log intent lineage, refreshes active target state from broker position before every persist, and upgrades weak legacy/tick provenance to broker-verified provenance when available | `tests/test_dual_broker_execution_follower.py` |
| FTMO aggregate open-risk fallback | Live target admission could price current open-position stop risk from symbol tick metadata if MT5 broker `order_calc_profit` was unavailable | Target open-position risk now requires broker `order_calc_profit`; missing/unavailable broker valuation blocks new target exposure | `tests/test_dual_broker_execution_follower.py` |
| Source/redacted_account aggregate open-risk fallback | Source prop-safe budget evidence could convert lifecycle risk percent to cash exposure when broker cash-risk valuation was missing | Source open-position stop-risk now requires broker `order_calc_profit`; prop-safe selector blocks live-applied decisions when open-position cash exposure is missing or fallback-valued | `tests/test_vnext_broader_origin_orchestrator.py`, targeted `tests/test_gtos_vnext_runtime.py -k prop_safe_selector` |
| Source intent risk-cap fallback on FTMO | Follower could use target profile risk if a copied source intent omitted the source effective risk cap | `target_risk_cap_pct()` now requires source intent risk cap and only then applies the lower target cap | `tests/test_dual_broker_execution_follower.py` |
| M1 namespace leak in no-candidate packets | Orchestrator read legacy `pipeline_state/m1_capture_state.json` even under a broker runtime namespace | No-candidate M1 source packet now reads `namespaced_file_path(..., runtime_namespace)` and only falls back to legacy when no runtime namespace exists | `tests/test_vnext_broader_origin_orchestrator.py` |
| Duplicate FTMO follower replay flag | Watchdog command could include duplicate `--replay-existing` | Primary bridge now emits one canonical live-recovery flag set | PowerShell parse check |
| Maintenance false-positive on pytest | Watchdog maintenance guard could treat pytest command lines as live dual-broker bridge/follower processes | Maintenance guard now excludes pytest command lines from live bridge detection | PowerShell parse check |
| FTMO checkpoint outcome ambiguity | Checkpoint `processed_intent_count` blended copied, blocked, skipped, failed, and detected-position outcomes | Follower now writes `intent_outcome_summary` with latest outcome/event counts by intent to startup evidence and checkpoint | `tests/test_dual_broker_execution_follower.py` |
| Market execution record identity gap | vNext market trade records could omit entry order/deal/retcode fields even though the intent bus carried them | Orchestrator market execution record writers now persist `entry_order_ticket`, `entry_deal_ticket`, `entry_deal_ticket_status`, retcode, and join keys | `tests/test_vnext_broader_origin_orchestrator.py`, `tests/test_orchestrator.py` |

## Current Code Already Clean Or Not Reproduced

| Finding | Current Evidence Disposition |
|---|---|
| BE/partial/trailing management duplicating trades after restart | Current FTMO target restore synchronizes residual volume/BE SL and treats residual runners as TP1 already handled; focused follower tests cover no duplicate TP1 close after restore. |
| Shadow R denominator near-zero from moved BE stop | Current orchestrator `_resolve_exit_sl_distance()` explicitly prefers immutable entry-risk geometry and protects against current BE stop denominators. Treat bad historical rows as stale unless reproduced by post-repair rows. |
| Selector V3 accidentally live | Current runtime still uses the vNext/moonshot path with dynamic execution policy; Selector V3 remains default-off until a production dossier supports activation. |
| Old PrimaryAnalyzer/L2 fallback in no-candidate path | Current broader-origin no-candidate tests assert old PrimaryAnalyzer/L2 are not called on consumed vNext no-candidate path. |
| BE/partial/exit management on FTMO applying as new trades | Current follower manages existing target `TradeState` by broker ticket and does not convert BE/partial modifications into new copied market entries. |

## Intentional Current Design

| Finding | Disposition |
|---|---|
| Duplicate notifications / FTMO notification namespace inactive | Intentional suppression for follower notifications remains acceptable because duplicated notifications have low operator value and can create double alerts. Execution/action logs and checkpoints remain the authority. |
| FTMO lightweight follower instead of full 24-symbol orchestrator | Current architecture preserves full redacted_account system performance and mirrors execution intent to FTMO with broker-local price/risk checks. A future architecture can add per-account management engines, but not by running a second full selector/orchestrator fleet. |
| Selector V3 source-limited package | Kept default-off. Promotion requires complete source hashes, source coverage, and production-change dossier. |

## Historical Or Comparator Evidence, Not Active Execution Authority

| Finding | Disposition |
|---|---|
| `strategy_follow_evaluations.jsonl` and `strategy_follow_candidates.jsonl` stale J46/J49/PrimaryAnalyzer labels | These are shadow/comparator artifacts referenced by observer/audit tooling, not the current vNext execution authority. They should be demoted or relabeled in a cleanup route, but they are not a live selector/execution input. |
| Pre-AI vNext trade records with false AI labels | Historical record hygiene issue. Do not rewrite active live orders; future cleanup can annotate legacy records as pre-AI/non-authoritative. |
| Closed GER40/UKOIL records not fully self-sufficient | Historical record repair/backfill item. Current live sizing and aggregate-risk paths now require broker valuation; closed-record repair should be evidence-only. |
| Legacy unnamespaced runtime artifacts | Active readers patched where a live leak was proven. Remaining stale artifacts should be archived/demoted by cleanup policy, not consumed by live runtime. |

## Remaining Architecture / Follow-Up Work

| Finding | Required Durable Path |
|---|---|
| Account-wide target risk budget including off-symbol/off-map positions/deals | Extend FTMO target budget to probe all broker positions/deals account-wide, then classify mapped, unmapped, and foreign-magic exposure with fail-closed rules. This is a larger account-risk enhancement beyond the current symbol-map loop. |
| Tick/M1 freshness watchdog treating null progress as OK | Repair watchdog/data health logic so null progress is neither OK nor infinite-failure noise; stale symbols should restart capture or mark data unavailable explicitly. |
| SPX500 transient tick-capture restart lacked failure cause | Add crash/failure-cause capture to tick-capture watchdog restart ledger. |
| Runtime JSONL chronological anomalies | Add monotonic sequence/cycle ids to active vNext writers or force consumers to sort by event timestamp plus sequence. Do not rewrite historical evidence as a substitute. |
| Safety-gate blocked rows with contradictory candidate source packet | Repair safety-gate row schema so candidate-present rows cannot carry nested `no candidate` packets. |
| Pending lifecycle diagnostics missing MT5 retcode on failed sends | Extend lifecycle failure rows to carry raw MT5 retcode/comment/error where available. |
| Active per-broker management architecture | Research/design decision: keep redacted_account as full selector brain, but consider per-account management/exits on each broker for broker-local prices and deal lifecycle. Requires explicit design because it changes live management behavior. |

## Verification Commands Run

- `python -m py_compile scripts\dual_broker_execution_follower.py src\components\orchestrator.py src\components\gtos_vnext_runtime.py`
- PowerShell parse: `[scriptblock]::Create((Get-Content scripts\watchdog.ps1 -Raw))`
- `python -m pytest tests\test_dual_broker_execution_follower.py -q`
- `python -m pytest tests\test_vnext_broader_origin_orchestrator.py -q`
- `python -m pytest tests\test_orchestrator.py -q`
- `python -m pytest tests\test_vnext_production_wiring.py tests\test_profile_overrides.py tests\test_broker_profile_namespace.py -q`
- `python -m pytest tests\test_execution.py tests\test_dual_broker_intent_bus.py tests\test_dual_broker_trade_record_projector.py -q`
- `python -m pytest tests\test_gtos_vnext_runtime.py -q -k "prop_safe_selector or runtime_decision or record_vnext_runtime_decision"`

Note: one full `tests\test_gtos_vnext_runtime.py -q` run timed out and remained alive with high memory. It was stopped; memory recovered before further work.
