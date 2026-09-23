# Pre-Replay Brief - 2026-07-04T09:00Z - B4 Fill Realism

Scope: denominator-to-deployment ultimate-system replay repair under `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20`.

Broker/live/final remain false. Local replay/package authority remains full across the 82-sleeve surface. This is a correctness checkpoint, not a live claim.

## 1. Latest Completed Replay

Latest completed bounded proof:

`BROAD_LIVE_AS_IF_REPLAY_V116_SCORECARD_RISK_LADDER_PROOF_PROPAGATION_20260603_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK`

- window: `2026-06-03..2026-06-03`
- candidate rows: `6603`
- scorecards: `96`
- terminal orders: `56` by summary/order rollup
- filled trades: `12`
- missed rows: `6575`
- net R: `-2.30082618`
- gross/final R: `-1.15118996`
- cash PnL: `-230.28228129`
- risk cash / risk %: `1200.53417139` / `1.2`
- W/L/F: `3/9/0`
- risk decisions: `28 open-reduced-risk`, `0 full-risk fills`
- verifier: green after V116 checkpoint, broker/live/final false

This one-day smoke proves local B3/B5 truth propagation only. It does not prove total reservoir conversion.

## 2. Running Process State

No broad replay, pytest, py_compile, route verifier, or git-diff helper process is active. Context OS sidecars are the only Python processes relevant to this repo. Decision: do not start a replay before the B4 same-root patch is implemented and focused tests pass.

## 3. Baseline Comparison

| Run | Scope | Trades | Net R | Notes |
|---|---|---:|---:|---|
| V89D | 2026-05-13..17 hostile 5d | 56 | +34.84520454 | old hostile comparator |
| V90 | 2026-05-13..17 hostile 5d | 51 | +28.84201157 | old hostile comparator |
| V92 | 2026-05-13..17 hostile 5d | 51 | +29.35570236 | same-window source-bound R `218870.181480028`, 894 generated axes |
| V110B | 2026-06-01..19 broad 19d | 95 | +22.80442652 | same-window source-bound R `342126.925564897` |
| V111 | 2026-06-01..19 broad 19d | 45 | -4.19333138 | disjoint replacement regression versus V110B |
| V116 | 2026-06-03 one-day | 12 | -2.30082618 | bounded proof slice; fill realism missing |

Do not compare V116 or B4 smokes directly to the global million-R reservoir. Every transfer claim must use the exact replay-window denominator.

## 4. Dirty Files And Active Changes

The tree is dirty with prior route/code work. B4 should touch only:

- `src/research_infra/wave4r_replay_microstructure.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- focused tests under `tests/`
- this root-cause/pre-replay control surface

Do not stage unrelated historical JSONL deletions, unrelated Context OS infrastructure changes, or `.context/LIVE_STATE.md`.

## 5. Subagent Findings

- Plato: incorporated into B4. Passive limit fills still grant on first touch; same-bar ambiguity returns unresolved R; `fill_realism_class` is absent from simulator rows.
- Meitner: incorporated into B4 tests/verifier. V116 has missing fill realism on all executable trade/order/oracle rows; executable rows need fatal protection against missing/unknown, `first_touch_optimistic`, and `m15_proxy`.
- Aristotle: deferred to B2/B3 after B4. Reallocation selected remains zero and risk-reduced collapse remains real, but scheduler/risk transfer needs fill-realism fields before row-level repair can be trusted.

## 6. Known Mismatch Chain

- source-bound -> candidate: partially fixed; exact-window denominators exist.
- candidate -> selector: partially fixed; raw/effective split exists but selector calibration remains open.
- selector -> scheduler: partially fixed; B2 reallocation/fill-floor transfer remains open.
- scheduler -> risk: partially fixed; structured risk ladder exists, all current fills reduced-risk.
- risk -> order: partially fixed; REFUSED/source-gap rows remain non-executable.
- order -> lifecycle -> fill: open B4 issue; passive first-touch optimism, M15 proxy fills, missing realism classes, and same-bar ambiguity distort executable replay truth.
- fill -> exit: open; same-bar ambiguity must stop leaving executable rows without final R.
- ledger/verifier: partially fixed; V116 green but fill-realism fatal scans are missing.

## 7. Fixed, Partial, Open

Fixed:

- B1/B3/B5 provenance and scorecard risk-expression proof surfaces exist through V116.
- Broker-cost REFUSED/source-gap execution remains forbidden.
- Broker/live/final remain closed.

Partially fixed:

- Risk-expression ladder is visible but all current fills remain reduced-risk.
- Reallocation diagnostics exist but no selected reallocation is proven.
- Bounded smoke denominator reporting exists.

Open:

- Passive first-touch fills need queue realism.
- M15 proxy fills must be diagnostic/non-executable.
- Fill-realism fields must propagate to order/trade/missed and comparison outputs.
- Same-bar ambiguity must be conservative-close or non-executable with provenance.

## 8. Highest-Leverage Same-Root Batch

Patch B4 fill-simulation realism as one batch:

- add repaired-profile queue-realism config while preserving raw comparator behavior;
- classify ordered-path fills by realism class;
- demote first-touch-only and M15 proxy fills to diagnostic/missed, not executable trades;
- propagate fill-realism and queue stats through ledger fields;
- force conservative same-bar ambiguity close when no tick ordering exists;
- add focused tests and verifier hooks.

## 9. Affected Files

- `src/research_infra/wave4r_replay_microstructure.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_wave4r_replay_microstructure.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_denominator_to_deployment_verifier.py`

## 10. Patch Classification

- Queue-realism gate: correctness repair.
- M15 proxy and first-touch demotion: correctness plus diagnostic ledger repair.
- Same-bar conservative close: correctness repair.
- Fill-realism propagation and verifier scans: diagnostic/ledger repair that enforces executable truth.
- Harness config keys and comparison splits: reproducibility/measurement repair.

## 11. Expected Measurable Effect Before Replay

- candidate -> scorecard transfer: unchanged.
- scorecard -> order transfer: unchanged except added realism fields.
- order -> fill transfer: may decrease under repaired profile because optimistic fills become diagnostic/missed.
- missed positive R: may increase with explicit `first_touch_optimistic` / `m15_proxy` reasons.
- missed negative R: remains scoreable and classified.
- trade count: may decrease.
- net/gross/final R: may worsen initially; that is acceptable if it removes fill optimism.
- W/L/F: may change only through truthful fill demotion/conservative close.
- cost-refused/source-gap execution: must remain zero.
- full-risk/reduced-risk distribution: likely unchanged in B4; B2/B3 follows.

## 12. Success / Failure Criteria

Helped:

- no executable order/trade carries missing or unknown `fill_realism_class`;
- `first_touch_optimistic` and `m15_proxy` are diagnostic/missed only;
- queue-confirmed fills carry touch/penetration fields;
- same-bar ambiguity resolves as conservative close or non-executable with provenance;
- raw comparator still measures legacy optimism delta;
- broker/live/final remain false.

Failed:

- unknown fill realism remains on executable rows;
- M15 proxy or first-touch-only fills become headline package trades;
- same-bar executable rows retain `final_r=None`;
- package axes shrink instead of creating missed/diagnostic rows;
- REFUSED/source-gap rows execute.

Next deeper flaw if helped: B2/B3 scheduler reallocation, scorecard/order namespace transfer, and risk ladder finalization, using fill-realism as a causal field.
