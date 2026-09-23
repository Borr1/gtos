# Pre-Replay Brief - 2026-07-03T20:02:00Z

Scope: V106 hostile fullgrid replay after the selector full-trade local replay authority repair and scheduler/finalizer probe audit.

Broker/live/final remain false. Local replay keeps full 82-sleeve authority.

## 1. Latest Completed Replay

Latest hostile completed replay:

`BROAD_LIVE_AS_IF_REPLAY_V105_SOURCEFIELD_M1_PROFIT_HARVEST_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`

- trades: `86`
- net/gross/final R: `+31.85943340 / +38.77147731 / +38.77147731`
- cash PnL: `+8571.89448575`
- W/L/F: `58/28/0`
- expired unfilled: `4`
- candidates/scorecards/orders/events: `25006 / 288 / 92 / 186`
- missed +R / -R: `+2040.41583953 / -7902.82906870`
- stress: `+27.55943340` at extra `0.05R`, `+23.25943340` at `0.10R`, `+14.65943340` at `0.20R`
- MC max drawdown p50/p05/worst: `-4.37212916 / -6.70167065 / -7.54607472`
- same-window axes: source-bound R `422103.4001250788`, package axes `1101`, candidate axes `894`, scorecard/order axes `51`, filled axes `50`, actual executable R `+30.55917992`

This is a five-day hostile repair proof, not a full-reservoir conversion proof.

## 2. Running Replay

No broad replay is running. The prior live-state generator finished. A two-file git diff helper stalled and was killed; use bounded source reads until post-replay verification.

## 3. Baselines

V92 hostile: `51` trades, `+29.35570236R` net, `+33.93212860R` gross/final, `+6228.63096022` cash, W/L/F `37/14/0`, expired `62`, candidate/scorecard/order/event `25006/288/119/239`, missed `+2054.54396823 / -7914.65328589R`.

V97 hostile: `47` trades, `+13.89627731R` net, `+18.23890670R` gross/final, `+4461.09800786` cash, W/L/F `23/24/0`, expired `51`, candidate/scorecard/order/event `25006/288/98/196`, missed `+2059.22271586 / -9738.85318535R`. V97 vs V92 added `19` trades for `+0.99594545R` but removed `23` trades worth `+13.53876156R`; added transfers were net positive but the swap was net worse by `-12.54281611R`.

V105 hostile vs V92: `+35` trades, `+2.50373104R` net, `+4.83934871R` gross/final, `+2343.26352553` cash, expired `-58`, added `70` trades for `+22.78464705R`, removed `35` for `+20.28091601R`; added-minus-removed `+2.50373104R`.

V105 hostile vs V97: `+39` trades, `+17.96315609R` net, `+20.53257061R` gross/final, expired `-47`, added `66` trades for `+25.95171644R`, removed `27` for `+8.60127923R`; added-minus-removed `+17.35043721R`.

## 4. Dirty Files And Active Changes

Current active code change to prove:

- `src/components/selector_v4.py`: local replay positive package router-refusal full-trade release now allowed under broker-cost-passed, non-live, non-final package authority; full-trade branch wins before open-reduced.
- `tests/test_selector_v4.py`: updated selector full-trade replay test and strengthened REFUSED-cost non-executable coverage.

Existing unrelated dirty tree includes old science JSONL deletions and Context OS infrastructure changes; do not stage those with this checkpoint.

## 5. Subagent Findings

- Kepler the 3rd: incorporated. Found selector full-trade request was hardwired false and open-reduced branch won first. Patch applied.
- Linnaeus the 3rd: incorporated. V105 exit/profit-harvest is restored and not the next mismatch patch.
- Tesla the 3rd: incorporated. Dominant remaining transfer leak is scheduler/finalizer: `candidate_generated_not_scheduler_selected` has `207` axes and `312498.8119839571` source-bound R; all V105 orders are open-reduced.
- Halley the 3rd: running read-only V105 leakage examples.
- Mencius the 3rd: running read-only scheduler/finalizer code audit.

## 6. Mismatch Map

- source-bound -> candidate: partially open, but not next patch; `894/1101` candidate axes in V105 hostile.
- candidate -> selector: patched pending replay; full-trade replay release now possible under strict local authority.
- selector -> scheduler -> risk: open major bottleneck. Probe reduction shows `91` selected probes, `4` true reallocations, `59` causal reallocation quality blocks. Top blocked candidates pass broker cost and source completeness but fail expected/probability/fill/scheduler comparison to current originals.
- risk -> order: open sizing authority bottleneck; V105 risk decisions are all `open-reduced-risk`.
- order -> lifecycle/fill: improved; expired unfilled now `4`.
- fill -> exit: not next patch; V105 profit-harvest is restored and positive.
- ledger/verifier: rerun after V106.

## 7. Fixed / Partial / Open

Fixed before V106: selector local replay full-trade authority split; REFUSED/source-gap hard blocks stay non-executable by test.

Partially fixed: scheduler/finalizer reallocation exists and selected `4` reallocations in V105, but large source-bound scheduler-not-selected parity remains.

Open: all orders are open-reduced; V106 must tell whether that was selector hardwire, downstream risk/finalizer action translation, or legitimate package authority.

## 8. Next Same-Root Batch

`v106_selector_full_trade_authority_measurement_then_scheduler_transfer_reassessment`

Run V106 hostile fullgrid with current code. Do not tune scheduler before this replay because current probe evidence does not justify opening causal quality gates.

## 9. Affected Files

- `src/components/selector_v4.py`
- `tests/test_selector_v4.py`
- replay harness/artifact builders for V106 outputs:
  `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
  and analyzer/parity/compare scripts in the same route.

## 10. Patch Classification

Selector patch: correctness repair.

No scheduler patch yet: current evidence says blocked alternatives are lower predecision quality than originals, so opening that gate would be performance tuning without proof.

## 11. Expected Measurable Effect

- candidate -> scorecard: expected unchanged at `25006 / 288`.
- scorecard -> order: should not execute refused/source-gap rows; order count may change if selector full-trade alters risk admission.
- order -> fill: should stay near V105 unless full-trade sizing changes lifecycle/risk admission.
- missed positive/negative R: report, but do not call suppression a win.
- trade count/net R/W-L-F: compare against V92/V97/V105.
- cost refused/source-gap execution: must remain `0`.
- risk distribution: success requires nonzero full-trade/local replay releases if eligible rows reach finalizer; if still all open-reduced, next root patch is downstream risk/finalizer action translation.

## 12. Proof Criteria

Helped: V106 preserves broker/live/final false, zero REFUSED/source-gap executions, and either improves net/executable transfer or explains full-trade release distribution with no headline degradation.

Failed: V106 worsens added trades or still emits all open-reduced with no full-trade release rows, proving the next leak is downstream of selector.

Exposes next flaw: full-trade rows appear but net R worsens; then patch risk sizing/full-risk authority calibration or scheduler replacement, not selector.
