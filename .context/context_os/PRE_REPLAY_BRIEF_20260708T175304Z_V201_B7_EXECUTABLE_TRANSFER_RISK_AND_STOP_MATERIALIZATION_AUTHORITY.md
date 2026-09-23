# Pre-Replay Brief - V201 B7 Executable Transfer Risk And Stop Materialization Authority

Generated UTC: 2026-07-08T17:53:04Z.

## Control State

- Current HEAD: `579fffdf5 Project B7 tick-hydrated comparator selection proof`.
- Current process check: no `BROAD_LIVE_AS_IF_REPLAY`, broad harness, pytest, or git diff/check process is running; only idle Context OS MCP helpers and app services were visible.
- Broker/live/final boundary: `broker_mutation_enabled=false`, `live_broker_authority=false`, `final_selection_claim=false`. Local replay/package authority remains full.
- This is a targeted B7 proof slice. It does not prove total reservoir conversion and must be normalized to its 2026-05-13..2026-05-17 targeted symbol window.

## Latest Completed Replay

Latest completed behavior replay:

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V199_B7_STOP_PRESSURE_RISK_TRANSFER_SOFT_PENALTY_20260513_20260517_TARGETED`.
- Window/scope: hostile 5-day targeted symbols `XAUUSD USDJPY XAGUSD GER40 NAS100 SPX500 UK100 AUDUSD US30_cash`.
- Candidate / scorecard / order / trade rows: `14384 / 288 / 154 / 67`.
- Missed rows / bucket rows: `14300 / 262`.
- W/L/F: `37 / 30 / 0`.
- Net/gross/final R: `-6.48266227 / -1.51201107 / -1.51201107`.
- Cash PnL: `-3276.73133579`.
- Risk cash / risk pct sum: `35400.83902524 / 36.0242944`.
- Expected cost R: `4.9706512`.
- Expired unfilled: `3`.
- Executed broker-cost REFUSED/source-gap trades: `0 / 0`.

Same-symbol V198 baseline:

- Trades: `63`.
- W/L/F: `37 / 26 / 0`.
- Net/gross/final R: `-2.59265384 / 2.07430014 / 2.07430014`.
- V199 delta vs same-symbol V198: `+4` trades, net `-3.89000843R`, gross/final `-3.58631121R`.
- Common 60 unchanged trades net: `-0.61879204R`.
- Added 7 trades net: `-5.86387023R`; six added stop-loss rows net `-6.45900147R`; one US30 giveback winner `+0.59513124R`.
- Removed 3 trades net: `-1.97386180R`.

Full hostile V198 baseline:

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V198_B7_2_HOSTILE_5D_TICK_HYDRATED_CURRENT_RUNTIME_TRANSFER_POLICY_20260513_20260517_FULLGRID`.
- Candidate / scorecard / order / trade rows: `25006 / 288 / 178 / 74`.
- W/L/F: `43 / 31 / 0`.
- Net/gross/final R: `-3.84033809 / 1.79005938 / 1.79005938`.
- Same-window V92 comparison: V92 `51` trades / `+29.35570236R`; V198 delta `-33.19604045R`; added `70 / -2.92365995R`; removed `46 / +27.43898396R`.
- Same-window V97 comparison: V97 `47` trades / `+13.89627731R`; V198 delta `-17.73661540R`; added `67 / -2.40415782R`; removed `39 / +10.44440501R`.

V89D and V90 exact same-window values remain unresolved in current compact anchors. They must not be invented; use only if exact current artifacts are located before a broad comparison.

## Fable B0-B8 Matrix

| Batch | Status | Evidence | Remaining Gap / Next Step |
|---|---|---|---|
| B0 truth instrumentation | DONE | `AUDIT_PROVENANCE_AND_FLAGS_V114.json`; `BROKER_COST_REFUSAL_HISTOGRAM_V111.json`; V114 baseline briefs | Keep as baseline; no new instrumentation before current B7 proof. |
| B1 provenance truth | DONE | selector/timewarp/scheduler provenance tests and prior V114/V121 root maps; raw/effective split now propagated into risk/order/trade/missed ledgers | No current blocker; preserve raw/effective split in all new fields. |
| B2 fillability/reallocation truth | DONE | scheduler unresolved-first fill-floor fields, route-resolution reallocation tests, fallback/expiry explicit-reason repairs in prior V114/V121 series | Current B7 issues are downstream transfer quality, not raw failure poisoning. |
| B3 risk-expression ladder | DONE | signed ladder fields and full/reduced/diagnostic propagation are present; current patch adds original-rank provenance and override proof fields | Verify V201 replay reports full-risk vs reduced-risk distribution correctly. |
| B4 fill-simulation realism | DONE/CONDITIONAL | V197 tick-hydrated proof corrected skip-tick smoke; ordered-tick source-gap and guarded-M1 queue-gap missed rows were `0` in V197 XAUUSD slice | Still requires broader B7.2/B7.3 fill-realism split before live claim. |
| B5 verifier/comparison precision | DONE/CONDITIONAL | verifier has expanded blocker scans, diagnostic/non-executable materialization checks, order-executable transfer contract tests | V201 adds stop-hazard materialization verifier coverage; run focused verifier tests before replay. |
| B6 broker-cost calibration | PARTIAL | REFUSED/source-gap execution remains closed in V198/V199; Gibbs audit found V123 had 23575 candidate rows, 16069 refused, 9699 honest measured-tick matches, but also 607 source gaps, 12 mapping/stale-floor passes, 7 metadata-review samples, and cell classes `731` honest / `7` mapping-stale-floor / `53` source-gap / `4` metadata-review | Do not loosen REFUSED. Close source-gap/mapping/stale-floor cells later with dated evidence; current B7 can proceed because execution gate is safe and cost-refused rows stay missed/non-executable. |
| B7 proof ladder | PARTIAL | V197 local tick-hydrated 2-day proof green; V198 hostile fullgrid failed value transfer; V199 targeted soft penalty worsened same-symbol value transfer | Next actionable batch is V201 targeted proof for hazard-adjusted hard dominance, original-rank risk authority, and stop-hazard materialization blocker enforcement. |
| B8 live path | OPEN | No B7.1-B7.5 proof ladder completion; live/shadow/canary dossier not assembled | Remains closed until B7 gates pass. |

## Subagent Findings Disposition

- Meitner: INCORPORATED. Identified risk/order/fillability weakness and full-tier negative behavior in V198; current B7 chain targets transfer/risk authority instead of cost bypass.
- Pascal: INCORPORATED. Removed V92/V97 winners mostly remain candidate-index/missed and do not reach scorecard/order; broker-cost REFUSED stays non-executable, cost-passed residuals are transfer work.
- Mencius: INCORPORATED. V199 soft-penalty markers appeared in scorecards/orders/trades/missed, but selected rows still won through raw expected-transfer dominance. V201 changes hard-dominance first key to hazard-adjusted executable-transfer selection score.
- Copernicus: INCORPORATED. Full-risk authority was using finalizer transfer rank as if it were original scheduler rank; V201 uses original scheduler rank unless explicit transfer-dominates-original authority is present.
- Gibbs: INCORPORATED. B6 corrected from DONE to PARTIAL due unresolved source-gap/mapping/stale-floor audit cells; REFUSED/source-gap execution remains closed.
- Bacon: INCORPORATED. Confirmed the V201 same-root patch and identified missing verifier coverage for stop-hazard materialization; verifier/test coverage is now included.
- Kuhn: REJECTED/STALE. Closed without a returned current finding; no disk evidence to incorporate.

## Known Mismatch Classes

- Source-bound -> candidate: B0/B1/B2 source-bound materialization repairs are not the current blocker for the V199 targeted symbol set; B6 cost source-gaps remain diagnostic/non-executable.
- Candidate -> selector: raw/effective selector split is preserved; current active concern is keeping effective materialization causal and non-diagnostic.
- Selector -> scheduler: V199 used raw expected-transfer before hazard-adjusted executable quality, allowing pressure-heavy candidates to displace safer executable transfers.
- Scheduler -> risk: finalizer-selected rank could mask original scheduler rank and promote rows to full-risk without original top-rank or explicit transfer-dominates-original proof.
- Risk -> order: broker-cost REFUSED/source-gap rows must remain non-executable but scoreable/missed.
- Order -> lifecycle/fill: suppressed stop-pressure previously stayed inert when base fragility suppressed cap/block; V201 materializes it into stop-hazard dominance when required.
- Fill -> exit: V199 added stop-heavy rows; this proof first fixes transfer/risk/stop materialization before any exit tuning.
- Ledger/verifier: risk rank provenance and stop-hazard materialization blocker class must be visible and fatal if escaped.

## V201 Patch Batch

Files/components:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: hazard-adjusted executable-transfer selection score consumed by hard-dominance selection and comparator sorting; suppressed stop-pressure soft penalty consumed in reallocation quality.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: original-rank-first full-risk authority; rank override proof fields; risk proof propagation; suppressed stop-pressure materialized into stop-hazard dominance; final blocker source stamped as `stop_hazard_materialization_authority`.
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`: stop-hazard materialization blocker allowed/required and final-blocker-class escape scan.
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`, `tests/test_v4_timewarp_simulated_live_research_loop.py`, `tests/test_denominator_to_deployment_verifier.py`: focused regressions for selection, risk rank authority, materialized stop pressure, and verifier fatal coverage.

Patch classification:

- Correctness: original scheduler rank is the default full-risk rank authority; suppressed stop pressure is no longer inert helper metadata.
- Performance: hard dominance ranks by hazard-adjusted executable-transfer selection score before raw expected-transfer.
- Diagnostic/verifier: risk rank provenance and stop-hazard materialization final-blocker proof are preserved into ledgers and fatal scans.

Expected measurable effect before replay:

- Candidate -> scorecard transfer: likely neutral.
- Scorecard -> order transfer: reallocation should avoid pressure-heavy raw-score candidates when a better hazard-adjusted executable transfer exists.
- Order -> fill transfer: may reduce or shift immediate pressure fills; should not globally suppress opportunity.
- Missed positive/negative R: pressure-heavy rejected/demoted rows should move into explicit missed/blocker buckets, not disappear.
- Trade count: may decrease or shift from V199; a collapse to near-zero is failure.
- Net/gross/final R and W/L/F: should improve vs V199 same-symbol if V199 added-loss pathway was correctly diagnosed; worsening is acceptable only if ledgers expose the next deeper flaw.
- Cost-refused/source-gap execution: must remain `0/0`.
- Risk distribution: full-risk rows must show original top-rank or explicit transfer-dominates-original override; reduced rows must carry rank/causal demotion.

Proof result interpretation:

- Helped: V201 reduces added stop-loss damage vs V199, keeps REFUSED/source-gap execution at zero, preserves missed opportunity accounting, and shows rank/stop materialization reasons on shifted rows.
- Failed: trade set remains V199-like with the same added stop-loss rows, full-risk still appears from finalizer rank without override, or stop-hazard materialization rows execute without final blocker proof.
- Exposed next flaw: V201 behaves truthfully but remains negative because another material class dominates; rank the next same-root blocker from the flow/bucket artifacts before any broad replay.
