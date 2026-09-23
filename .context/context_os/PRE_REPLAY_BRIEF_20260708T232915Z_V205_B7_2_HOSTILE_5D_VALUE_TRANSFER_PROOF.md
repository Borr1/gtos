# Pre-Replay Brief - V205 B7.2 Hostile Five-Day Value-Transfer Proof

## Current State

- Latest committed checkpoint: `682a0e8fa Repair B7 missed selector-origin proof surface`.
- Latest completed proof-surface replay: `BROAD_LIVE_AS_IF_REPLAY_V204_B7_MISSED_SELECTOR_ORIGIN_AND_FLOW_DIAGNOSTIC_REPAIR_20260513_REPAIRED_ONLY_COMPACT_FULLGRID`.
- V204 one-day numbers: `8864` candidates, `96` scorecards, `41` order ledger rows, `14` filled trades, W/L/F `7/7/0`, net/gross/final R `-2.94390255 / -1.88067619 / -1.88067619`, cash PnL `-2136.50639331`, missed rows `8840`.
- V204 route verifier: `ok=true`, `issue_count=0`, `final_package_selected=false`, `live_trading_enabled=false`.
- Active replay process at brief creation: none observed.

## Fable Matrix Position

B0 and B1 are done after V204. B2, B3, B4, and B6 remain conditional truth surfaces to preserve. B5 is green. B7 is active. B8 is open.

The next dependency-ordered step is B7.2 hostile five-day value-transfer proof, not another one-day proof-surface patch.

## Baselines

Same hostile window where available: 2026-05-13..2026-05-17.

| Run | Scope | Trades | Net R | Gross R | Final R | Cash PnL | W/L/F | Transfer Counts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| V92 | hostile 5d fullgrid | 51 | 29.35570236 | 33.9321286 | 33.9321286 | 6228.63096022 | 37/14/0 | candidates 25006, scorecards 288, orders 239, missed 24887 |
| V97 | hostile 5d fullgrid | 47 | 13.89627731 | 18.2389067 | 18.2389067 | 4461.09800786 | 23/24/0 | candidates 25006, scorecards 288, orders 196, missed 24908 |
| V198 | hostile 5d fullgrid | 75 | -3.84033809 | 1.79005938 | 1.79005938 | -3530.29276461 | 44/31/0 | candidates 25006, scorecards 288, orders 178, missed 24908 |
| V201 | hostile 5d targeted | 70 | -6.5478412 | -1.36541623 | -1.36541623 | -2186.20676163 | 40/30/0 | candidates 14384, scorecards 288, orders 161, missed 14299 |
| V204 | one-day proof slice only | 14 | -2.94390255 | -1.88067619 | -1.88067619 | -2136.50639331 | 7/7/0 | candidates 8864, scorecards 96, orders 41, missed 8840 |

V204 must not be compared directly to the global source-bound reservoir. V205 will be normalized to the 2026-05-13..2026-05-17 replay window.

## Next Replay

Prefix: `BROAD_LIVE_AS_IF_REPLAY_V205_B7_2_HOSTILE_5D_VALUE_TRANSFER_PROOF_20260513_20260517_FULLGRID`

Command shape:

```bash
python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py \
  --start 2026-05-13 --end 2026-05-17 \
  --profiles repaired_package_conversion_v3 \
  --output-prefix BROAD_LIVE_AS_IF_REPLAY_V205_B7_2_HOSTILE_5D_VALUE_TRANSFER_PROOF_20260513_20260517_FULLGRID \
  --omit-packet-sidecar-ledger --compact-missed-ledger --gc-between-chunks
```

## Expected Effect

No new behavior patch is being introduced before this replay. The replay proves whether the committed V204 authority/truth path transfers value over the hostile five-day window.

Expected measurable effects:

- Candidate -> scorecard transfer: should remain close to the known five-day universe unless V204 authority fields intentionally exclude non-executable rows.
- Scorecard -> order transfer: must show whether V92/V97 winner paths remain absent after truth repairs.
- Order -> fill transfer: executed broker-cost REFUSED/source-gap counts must remain zero.
- Missed positive R: must identify removed winners and the exact stage reason.
- Missed negative R: must identify beneficial suppression separately from positive-by-suppression.
- Trade count: compare to V92 `51`, V97 `47`, V198 `75`, V201 `70`.
- Net/gross/final R: helpful if materially better than V198/V201 with truth preserved; failure if still negative from the same transfer leak.
- W/L/F: compare to V92 `37/14/0`, V97 `23/24/0`, V198 `44/31/0`, V201 `40/30/0`.
- Risk distribution: full-risk versus reduced-risk must be reported separately.
- Cost/source execution: cost-refused/source-gap execution must remain zero.

## Proof Rules

Helpful result: V205 improves against V198/V201 while preserving verifier truth, without simply suppressing trades.

Failed result: V205 remains materially negative or loses the V92/V97 winner set before scorecard/order under the same root leak.

Next deeper flaw: if V205 is truth-clean but value does not transfer, patch the highest same-root leak shown by added/removed trades, candidate-to-scorecard transfer, risk expression, order/fillability, lifecycle, or exit evidence before another broad replay.

Broker/live/final remain false. Local replay/package authority remains full.
