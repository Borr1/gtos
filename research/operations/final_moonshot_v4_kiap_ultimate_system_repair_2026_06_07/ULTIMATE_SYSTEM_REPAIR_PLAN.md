# KIAP Ultimate System Repair Plan

Route id: `final_moonshot_v4_kiap_ultimate_system_repair_2026_06_07`
Status: `IN_PROGRESS`
Parent checkpoint: `6d645a7f3 feat: complete kia parity tick-first replay repair`
Parent route: `research/operations/final_moonshot_v4_kia_parity_tick_first_runtime_repair_2026_06_07/`
Full program plan: `ULTIMATE_SYSTEM_FULL_VISION_AND_LOOP_PLAN.md`

## Purpose

Turn the completed KIAP scalable replay into the production-code repair loop. The tick/source problem is no longer the first limiter. The active limiter is system behavior: scheduler regret, weak accepted trades, risk-headroom lockout, cost flips, stale execution-policy residue, uncalibrated probability/EV/fill scoring, incomplete chronological validation machinery, and low-quality risk-budget consumption.

This route produces concrete code/config/replay changes, repair deltas, and deployment-package dossier inputs. Evidence labels stay exact and function as routing metadata for what gets built next.

The broader program is a compounding replay intelligence loop: materialize memory-bounded day/symbol/week partitions, freeze partition/embargo/touched-state ledgers, convert failure families into production-called repairs, rerun identical windows, promote only positive repair deltas across development and holdout, then expand to rolling, sealed historical, stress, and adversarial partitions.

Current methodological boundary: the `2026-04-20` through `2026-04-30` repair/holdout slice has now been used repeatedly for degradation analysis and exact symbol/session/family/side tuning. It remains useful development and failure-anatomy evidence, but it cannot be treated as fresh validation. The exact rule-list shape is diagnostic only; generalized calibrated Selector V4 admission is now the frozen production-called candidate, and the route must source-materialize broader untouched rolling/stress/sealed partitions before replay validation.

The route must not freeze a diagnostic checkpoint as the final architecture. The earlier cap-8 daily risk-order budget proved weak risk consumption; it is not the target design. The current checkpoint implements dynamic daily drawdown-budget allocation where selector, scheduler, risk authority, exit policy, and market-awareness components compete every candidate against zero-trade, expected net edge, calibrated probability, fill probability, cost, correlation, pending/open risk, consumed intraday risk spend, opportunity cost, drawdown state, and chronology-safe session reserve.

Risk authority is now a first-class repair surface. FTMO broker read/export data supplies the replay price/path evidence for this lane; risk sizing must be resolved from the explicit FTMO profile/instrument table and carried with source labels. Old KIAP global-risk numbers are valid comparators, not current FTMO-risk-parity rerun evidence.

## Current KIAP Facts

- Route verifier: `passed`, `failure_count=0`.
- Source requirement coverage: `2746` latest selected orders, `2746` source requirements, `2746` selected tick truth rows.
- Selected truth: `2719` tick-derived rows, `27` exact zero-duration unresolved rows, `0` unlabeled M1 selected fills.
- Full development: `3884` candidates, `967` selected/oracle orders, `88` filled trades, `32` winners, `56` losses, `+1.37246892R` gross, `13.6047531R` expected cost, `-12.23228416R` net proxy, `869` risk rejected, `21.19921307%` max drawdown.
- Repair rerun: `3884` candidates, `1076` selected/oracle orders, `83` filled trades, `28` winners, `55` losses, `-0.85664356R` gross, `13.05461606R` expected cost, `-13.91125963R` net proxy, `983` risk rejected, `20.56538209%` max drawdown.
- Holdout rolling: `1817` candidates, `498` selected/oracle orders, `21` filled trades, `1` winner, `20` losses, `-14.65616667R` gross, `3.29921463R` expected cost, `-17.95538129R` net proxy, `471` risk rejected, `11.38468539%` max drawdown.
- Risk authority repair checkpoint: `ULTIMATE_RISK_AUTHORITY_PARITY_AUDIT.json` records the prior replay gap, FTMO profile-backed per-symbol risk source, direct BTCUSD/ETHUSD/NAS100/US30/AUDUSD probes, and the rerun requirement for item #8.
- Current bounded dynamic-allocator repair probe: `2026-04-21`, `963` candidates, `346` simulated orders, `1` fill, `1/0` winners/losses, `+0.52416554R` gross, `0.04787173R` expected cost, `+0.47629381R` net proxy, `0.0%` max drawdown, `339` risk rejected, `2` selected `replace_pending` options, `2` replacement cancel events.
- Post-allocator daily risk-order budget sweep: no-count and caps `8`, `10`, `12`, `14`, `16`, and `20` all tie at `+0.47629381R`; cap `6` also ties while adding count rejections. The static count cap is disabled in active config and remains only a diagnostic outer circuit breaker candidate pending broad partition additive proof.
- Broad dynamic repair rerun through bounded day/source materialization: repair window `2026-04-20` through `2026-04-24` is `+5.26787086R` net proxy with `2.0328745%` max drawdown versus parent repair `-13.91125963R` and `20.56538209%`; holdout window `2026-04-29` and `2026-04-30` is `+1.09793134R` net proxy with `1.31133241%` max drawdown versus parent holdout `-17.95538129R` and `11.38468539%`.
- Broad dynamic classification: positive same-window repair delta and failure-anatomy evidence only. The partition ledger and command-center touched boundary set `validation_claim_allowed=false` and `fresh_validation_status=invalid_after_iterative_exact_rule_tuning`.
- Generalized admission checkpoint: `ULTIMATE_GENERALIZED_CALIBRATED_ADMISSION_BOUNDARY.json` records active calibrated admission floors, exact-list diagnostic mode, and six passing mechanism probes. `ULTIMATE_UNTOUCHED_REPLAY_SOURCE_PROBE.json` records that current non-touched probe dates are source-blocked with zero included symbols.
- Verification checkpoint: syntax passed, combined focused/permissions tests `173 passed`, scheduler/timewarp tests `39 passed`, broader permissions probe `97 passed`.

## Measured Repair Priorities

1. Scheduler regret: `2315` rows, with full development missed net proxy `+1388.528463R`, repair missed net proxy `+1127.82122903R`, holdout missed net proxy `+552.55437114R`.
2. Weak accepted trades: `131` rows, total accepted loser net drag across phases about `-127.04729577R`.
3. Risk-headroom lockout: `2323` rows, repair rerun increased lockouts by `114` versus full development.
4. Partial BE runner: `1594` pre-repair rows. The current repair disables partial-BE exception families unless a later evidence-routed family wins net after cost and opportunity cost.
5. Cost flips: `9` rows; small count, but they prove cost can flip positive gross into negative net and must feed scoring.
6. Risk-profile parity: prior KIAP/timewarp replay used a global `2.0%` risk baseline plus runtime reductions. The next repair/holdout rerun must use per-symbol FTMO profile risk with `risk_config_source` provenance and scheduler window risk maps.
7. Static-cap replacement: current code now keeps the static daily order count disabled as active architecture and applies dynamic daily drawdown-budget allocation inside runtime risk authority; trade count is an optimizer output. Any future count circuit breaker must prove additive value after the allocator across broader partitions.
8. Calibration debt: probability, EV, fill probability, and cost need Brier/ECE/logloss/reliability-bin proof before they drive broader optimizer decisions.
9. Chronological validation debt: the current broad April repair/holdout rows are marked repeatedly touched and not validation; tuned development evidence must not be relabeled as sealed validation.
10. Missed-opportunity truth debt: the one-day missed ledger has `617` M1-proxy rows, all `ordered_tick_truth_satisfied=false`, `195` positive rows totaling `+249.37274161R`, `387` negative rows totaling `-384.06956815R`, and net `-134.69682654R`; the route must isolate and tick-promote positive missed families instead of expanding broad missed-trade intake.

## Execution Plan

1. Context and stale-artifact repair:
   - Refresh `.context/00_core/research_current_state.md` to current KIAP completion and this route.
   - Update `.context/00_core/vnext_absolute_moonshot_vision_and_limitations.md` from stale "after current lanes" framing to current KIAP-scalable replay execution.
   - Rewrite KIAP completion audit boundary section as an active next-builder directive.
   - Keep machine-readable evidence-class fields intact.

2. Row-level repair intelligence:
   - Build `ULTIMATE_SYSTEM_REPAIR_ANALYSIS_SUMMARY.json`.
   - Build ledgers for scheduler regret, weak accepted filters, risk lockout, partial BE cleanup, and cost flips.
   - Use only as-of decision fields for candidate rules; post-asof outcome rows are labels for measuring candidate rules.
   - Budget-consumption, opportunity-cost, calibration, missed-promotion, packet-parity, allocator, and partition/touched-state ledgers are materialized for the bounded dynamic checkpoint before promotion decisions.

3. Risk authority parity repair:
   - Resolve replay risk from `config/profiles/ftmo.yaml` by symbol/instrument alias, with explicit config source labels.
   - Preserve `risk_config_source` on candidate risk packets, order/trade/account rows, and scorecards.
   - Treat repeated `0.25%` as valid only when sourced to profile, selected-cell, prop-safe, or side-aware risk logic.
   - Keep FTMO broker read data as market/path truth and FTMO profile as this lane's replay risk authority.

4. Implemented behavior repairs:
   - Scheduler V4 dominated-pending replacement in `src/research/moonshot_scheduler_v4_best_trade_allocator.py`.
   - Replay risk authority parity and risk-order budget in `src/research_infra/v4_timewarp_simulated_live_research_loop.py`.
   - Selector V4 admission-quality guard in `src/components/selector_v4.py`.
   - Empty partial-BE exception list semantics in `src/research/moonshot_default_off_policy_router.py`.
   - Scheduler V4 source-context bridge in `src/components/permissions.py`.
   - Treat these as the pre-dynamic checkpoint repairs. The current code path adds dynamic daily drawdown-budget allocation and demotes static count tuning to diagnostic-only status.

5. Replay verification:
   - The bounded one-day probe is positive with dynamic allocation and no active static count cap, proving low-quality risk-consumption can be controlled through budget allocation rather than count-first architecture.
   - Build the chronological run matrix before broader promotion: discovery/development/repair/holdout/rolling/sealed/stress/contaminated partitions, purge/embargo rules, duplicate policy, and multiple-testing ledger.
   - The broad dynamic repair and holdout partitions are materialized and positive, but are repeatedly touched April development diagnostics, not fresh validation.
   - Generalized calibrated admission is materialized; exact block-list rules are diagnostic. Rerun broader untouched rolling/stress/sealed partitions next after bounded FTMO primary/M1 source packages are available.
   - Do not call `build_source_package(BASELINE_DAYS)` in a one-shot full tick load path.
   - Keep day/symbol partitioned materialization and source caches.

6. Dynamic capital allocator repair:
   - Compute available daily drawdown budget from FTMO reset boundary, realized drawdown, open/pending worst-case risk, cost/slippage buffer, correlation reserve, and chronology-safe opportunity reserve.
   - Score candidate risk spend by expected net R, calibrated probability, fill probability, cost, source completeness, market regime, symbol/family/session reliability, drawdown contribution, correlation, pending/open risk, and opportunity cost.
   - Allocate zero/reduced/full/proportional risk before runtime headroom is consumed. Zero-trade, reserve, reduce, replace pending, cancel pending, and trade must compete in one portfolio decision.
   - Static count is already demoted to a benchmark/outer circuit breaker candidate; broader partitions must prove additive value before it can be re-enabled.

7. Package and commit:
   - Run focused tests and route verifiers.
   - Audit stale duplicate route artifacts and scratch status.
   - Commit scoped code/context/route artifacts, excluding raw ignored MT5 exports.

## Completion Standard

This route is complete only when:

- the active context points future agents to KIAP completion plus this follow-on route;
- active human-facing route/context docs express replay-to-repair and replay-to-deployment-package posture directly;
- measured behavior repairs are implemented in production-called code/config;
- diagnostic/static checkpoint repairs are either replaced by the dynamic allocator or explicitly retained as evidence-backed outer circuit breakers;
- partition/embargo, calibration, budget-consumption, opportunity-cost, and missed-opportunity tick-promotion ledgers exist and are consumed by the repair loop;
- replay risk authority resolves from the explicit FTMO profile/instrument source and row-level source labels;
- the repair is replayed through bounded KIAP phases with before/after numbers;
- the current broad dynamic April rerun is classified as development-only after repeated tuning, and any validation/deployment-package claim is deferred until the frozen generalized calibrated mechanism is tested on broader untouched/stress/sealed evidence;
- verifier/test evidence is written to this route and current broad permission/config drift is clean;
- stale duplicate/scratch artifacts are classified or removed;
- remaining limitations are exact row/source/field/capture requirements or next executable repair items.
