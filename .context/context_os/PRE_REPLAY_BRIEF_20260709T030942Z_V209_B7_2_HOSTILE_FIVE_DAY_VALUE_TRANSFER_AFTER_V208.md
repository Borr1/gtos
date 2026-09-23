# Pre-Replay Brief - V209 B7.2 Hostile Five-Day Value Transfer After V208

Generated UTC: 2026-07-09T03:09:42Z.

## 1. Latest Completed Replay

Latest completed prefix:
`BROAD_LIVE_AS_IF_REPLAY_V208_B7_DEFAULT_CONFIDENCE_SCORECARD_REPAIR_20260513_REPAIRED_ONLY_COMPACT_FULLGRID`

Numbers: candidates `8864`, decisions `2304`, scorecards `96`, order-ledger rows `9`, summary order rows `6`, filled trades `2`, missed rows `8858`, bucket rows `412`, W/L/F `2/0/0`, net/gross/final R `+0.52110312/+0.65111456/+0.65111456`, cash PnL `+130.31196876`, risk cash/risk pct `500.10039132/0.5`, expected cost R `0.13001144`, executed broker-cost REFUSED/source-gap `0/0`.

Interpretation: one-day proof-surface repair only. It is not B7.2 or full-reservoir proof.

## 2. Current Process State

No broad replay, route builder, verifier, parity builder, or pytest process is running. Active Python processes are Context OS MCP stdio servers only. Start V209 only after this brief and the matrix exist.

## 3. Baselines

Hostile 2026-05-13..2026-05-17:

- V89D: `56` trades, net `+34.84520454R`, gross/final `+39.93441037R`, cash `+8178.90660707`.
- V90: `51` trades, net `+28.84201157R`, gross/final `+33.36349114R`, cash `+6371.80465431`.
- V92: `51` trades, net `+29.35570236R`, gross/final `+33.93212860R`, cash `+6228.63096022`.
- V97: `47` trades, net `+13.89627731R`, gross/final `+18.23890670R`, cash `+4461.09800786`.
- V198: `74` filled trades, net `-3.84033809R`, gross/final `+1.79005938R`, cash `-3530.29276461`.
- V205: `72` filled trades, net `-5.20239659R`, gross/final `+0.16828289R`, cash `-3907.50669036`.

Non-hostile 2026-06-01..2026-06-05 baselines for the next gate:

- V104: `46` trades, net `+14.73101491R`.
- V128: `55` trades, net `+1.12099062R`.
- V150: `3` trades, net `+0.84449709R`.

## 4. Dirty Files / Active Code Changes

Route/code files from V208 are committed at `e12cb4028`. Current relevant control-state repair changes are expected in:

- `.context/context_os/fable_ultimate_plan/FABLE_EXECUTION_MATRIX_20260709.md`
- `.context/context_os/PRE_REPLAY_BRIEF_20260709T030942Z_V209_B7_2_HOSTILE_FIVE_DAY_VALUE_TRANSFER_AFTER_V208.md`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP_20260709T030942Z_V209_B7_2_HOSTILE_FIVE_DAY_VALUE_TRANSFER_AFTER_V208.json`
- `.context/context_os/CURRENT_ROOT_CAUSE_MAP.json`
- `.context/context_os/CONTINUATION_CURSOR.json`

Existing unrelated dirt remains in Context OS code/docs, `scripts/generate_live_state.py`, `src/components/broader_origin_generators.py`, `tests/test_gtos_context_os.py`, `tests/test_mt5_research_export_symbol_defaults.py`, and old deleted science-program JSONL ledgers. Do not stage those with V209 unless separately verified.

## 5. Subagent Findings

- Dalton: incorporated; cost-refused rows are honest non-executable absent dated B6 calibration proof.
- Fermat: incorporated; full-risk sizing can be correct even when public action labels are wrong.
- Kant: incorporated; the recent stop-loss losers are honest ordered-tick selected-policy stop outcomes.
- Meitner: incorporated; V198/V205 failure is risk/order/fillability and full-tier exposure, not live/broker authority.
- Pascal: incorporated; removed V92/V97 winners are visible but mostly blocked before scorecard/order by broker-cost or scheduler/risk transfer classes.
- Kuhn: incorporated through V199/V201/V206 stop-pressure and quality-provenance repairs.

No current subagent result is pending before V209.

## 6. Known Mismatch Classes

- Source-bound -> candidate: currently full hostile candidate universe should materialize (`25006` rows in prior hostile fullgrid); no top-N narrowing allowed.
- Candidate -> selector: raw/effective selector provenance and default-confidence source must remain visible.
- Selector -> scheduler: signed authority and hazard-adjusted transfer quality must avoid stale/default provenance.
- Scheduler -> risk: full-risk requires original top rank or explicit transfer-dominates authority; stop-pressure rows cannot get full-risk via stale confidence.
- Risk -> order: broker-cost REFUSED/source-gap/unfillable/off-authority rows remain non-executable and scoreable/missed.
- Order -> lifecycle/fill: tick-hydrated path is required when available; fill-realism classes must split headline vs diagnostic/proxy.
- Fill -> exit: stop-loss bucket must be attributed; no exit tuning before transfer evidence is parsed.
- Exit -> ledger: net/gross/final/cash/risk and added/removed trade identity must be deterministic.

## 7. Fixed / Partial / Open

- Fixed: B0 baseline instrumentation; B1 provenance/default-confidence projection; B5 verifier summary-count contract; REFUSED/source-gap non-execution.
- Partial: B2/B3/B4/B6 are conditional under broader B7 because value transfer must still prove the consumers hold over five days.
- Open: B7.2 hostile five-day, B7.3 non-hostile five-day, B7.4 19-day, B7.5 extended history, and all B8 live path gates.

## 8. Highest-Leverage Same-Root Batch

Selected batch: `V209_B7_2_hostile_five_day_value_transfer_after_v208`.

This is a proof batch, not a policy patch. Current evidence does not justify another one-day local tuning patch before broader hostile proof.

## 9. Exact Files / Components Affected

- Replay: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- Flow: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/analyze_broad_live_as_if_replay_flow.py`
- Parity/leakage: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py`
- Route summary/verifier: `build_denominator_to_deployment_execution.py`, `verify_denominator_to_deployment_execution.py`
- Comparison: route comparison tools against V92/V97/V198/V205.

## 10. Patch Type

Current control edits are diagnostic/proof-surface repairs. The replay itself is behavior measurement. No production/live/broker authority changes.

## 11. Expected Measurable Effect

- Candidate -> scorecard: expected around hostile fullgrid `25006 -> 288`.
- Scorecard -> order: may improve or reduce versus V205 depending on stop-pressure/default-confidence transfer.
- Order -> fill: should preserve `0` executed REFUSED/source-gap rows.
- Missed positive/negative R: must be reported; missed-positive cannot balloon without exact reasons.
- Trades: may be lower than V205 if stop-pressure losers are honestly demoted; positive-by-suppression is rejected.
- Net/gross/final R: should improve versus V205 if V206-V208 repairs transfer; if not, the next blocker is selected by added/removed and bucket evidence.
- W/L/F: report separately.
- Full-risk/reduced-risk distribution: report PnL by tier and causes.
- Cost/source execution: must remain `0/0`.

## 12. Helped / Failed / Next Deeper Flaw

Helped: V209 artifacts exist, verifier/parity/flow are green, transfer is cleanly attributed, executed REFUSED/source-gap remain zero, and V209 improves or precisely explains the V205/V198 transfer failure without suppressing opportunity.

Failed: V209 reopens proof-surface issues, executes REFUSED/source-gap rows, narrows/caps the package without bounded-smoke labeling, removes V92/V97 winners without causal predecision blockers, or turns positive only by collapsing opportunity.

Next deeper flaw: if V209 is clean but still weak/negative, assign subagents to V209 current artifacts by lane and patch the highest same-root blocker before B7.3.

Broker/live/final remain closed.
