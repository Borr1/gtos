# Raw-OHLC Architecture Ablation And Path-Scaling Protocol

**Date:** 2026-05-01
**Spec:** `research/phase_3_external_feed_validation/RAW_OHLC_ARCHITECTURE_ABLATION_SPEC_V1.json`
**Status:** Registered research protocol
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## What The User Is Asking To Test

The question is not just "does this cohort make money?" It is:

1. What happens with the raw setup stream before our architecture?
2. What does L2 verification add or remove?
3. What does J46-J49 position management add or remove?
4. What happens with both L2 and J46-J49?
5. Can a smarter path-scaling exit/reentry model outperform fixed TP or J46-J49?

The path-scaling idea is understood as a path-dependent exit overlay:

- Price reaches a predefined favorable level.
- The system locks break-even or a defined profit level.
- If price keeps running, the trade remains exposed.
- If price pulls back to a predefined reentry level, the system may enter again with explicit risk accounting.
- The goal is to convert trades that would later reverse into positive-R outcomes while still participating in large moves.

This is not a normal trailing stop. It is a state machine with lock, pullback, reentry, risk-budget, and final-exit states.

## Existing Context

J46-J49 was previously reported as:

- 0% partial close.
- TP1 at 3.0R.
- Immediate break-even move when TP1 is reached.
- Higher target around 6R.
- 12-bar time stop.
- Historical lift reported as +0.742R/trade in the Phase 1 position-management sweep.

The important mechanism read from the forensic note is that J46-J49 is already a trailing-stop-like transform: do not bank early, let price reach 3R, then protect the trade and let it try for 6R.

The user-proposed path-scaling idea is more aggressive than J46-J49 because it asks whether we can harvest repeated structured pullbacks during the same directional move.

## Correct Comparison Design

All variants must be evaluated on the same reconstructed candidate stream:

| Variant | L2 | Exit policy | Status |
|---|---|---|---|
| `BASE_RAW_FIXED_TP` | off/not reconstructed | current raw fixed TP/SL | available now |
| `L2_ONLY_FIXED_TP` | on | current raw fixed TP/SL | requires candidate L2 reconstruction |
| `J46_J49_ONLY` | off/not reconstructed | 0% partial, 3R lock, 6R target, 12 M15 bars | requires path outcome engine |
| `L2_PLUS_J46_J49` | on | J46-J49 | requires L2 plus path engine |
| `PATH_SCALE_LOCK_ONLY_V0` | off/not reconstructed | pre-registered lock ladder, no reentry | requires path level selector |
| `L2_PLUS_PATH_SCALE_LOCK_ONLY_V0` | on | lock ladder, no reentry | requires L2 plus path level selector |
| `PATH_SCALE_CLOSE_REENTER_V0` | off/not reconstructed | lock then reenter on predefined pullback | blocked until lock-only passes |
| `L2_PLUS_PATH_SCALE_CLOSE_REENTER_V0` | on | full path scaling | blocked until reentry V0 is valid |

The first engineering blocker is L2 reconstruction. A correct L2-on/off test needs the pre-L2 candidate stream and deterministic L2 verdicts. We cannot infer L2 value by looking only at rows that already survived L2, because that would hide the rejected population.

## V0 Exit Policies Frozen For First Full Run

The first executable V0 keeps L2 and reentry out of scope and compares five exit overlays on the same raw-OHLC TAKE stream:

| Variant | Final target | Time stop | Lock ladder |
|---|---:|---:|---|
| `BASE_RAW_FIXED_TP` | setup TP/RR | 96 M15 bars | none |
| `J46_J49_ONLY` | 6.0R | 12 M15 bars | 3.0R -> 0.0R |
| `PATH_LOCK_CONSERVATIVE_V0` | 6.0R | 12 M15 bars | 1.5R -> 0.0R; 2.0R -> 0.5R; 3.0R -> 1.0R |
| `PATH_LOCK_HALF_GAIN_V0` | 6.0R | 12 M15 bars | 1.5R -> 0.5R; 2.0R -> 1.0R; 3.0R -> 1.5R |
| `PATH_LOCK_EARLY_BE_V0` | 6.0R | 12 M15 bars | 1.0R -> 0.0R; 1.5R -> 0.5R; 2.0R -> 1.0R; 3.0R -> 1.5R |

The reported cost sensitivities are `0.00R`, `0.02R`, `0.05R`, and `0.10R` per completed round turn. They are sensitivity cases, not measured historical costs, because the OHLC replay corpus does not contain reliable commission, spread, and slippage fields. Since V0 has no reentry, each resolved outcome is charged one completed round turn. Any future reentry lane must charge additional round turns and report incremental risk separately.

## Path-Scaling Risk Accounting

This is the part that can easily become wrong if it is not explicit.

Base R is the initial distance from entry to initial structural stop on initial position size.

For a long example:

- Initial entry = 100.
- Initial SL = 90.
- Base R price distance = 10.
- If price reaches 107 and a lock captures +0.7R, that is +7 price units on the original position size.
- If a later reentry occurs at 105 with the same SL at 90, the new risk distance is 15 price units, or 1.5 base R per same-size position.

Therefore same-lot reentry cannot be reported as if risk remained 1R. A valid path-scaling engine must either:

- resize the reentry so incremental risk is capped,
- explicitly report increased risk,
- or forbid the reentry if it breaks the risk budget.

The clean first version is lock-only. Reentry should come after the lock-only engine proves that the lock levels are not just truncating winners.

## Level Selection Rules

The main danger is post-hoc level fitting. The level selector must be frozen before final runs.

Allowed level families for future implementation:

| Family | Example | Notes |
|---|---|---|
| Fixed R anchors | 0.7R, 1.6R, 3.0R | Useful as a control, but can overfit if swept. |
| Structural liquidity | prior M15/H1 swing, session high/low, equal high/low | Closer to the user's intended market logic. |
| POI boundaries | OB boundary, breaker boundary, FVG edge/mid | Must be known as of the replay clock. |
| Volatility/displacement | ATR multiple, displacement candle extension | Good for normalizing across instruments. |
| Round-number psychology | instrument-specific tick/figure levels | Must be pre-specified by symbol. |

The first correct implementation should pick one conservative level family plus one fixed-R benchmark, not sweep a large grid.

## Metrics

The report must include:

- Mean R, median R, sum R, win rate, resolved n.
- Max drawdown in R.
- Average bars held and timeout rate.
- Stop rate, lock-trigger rate, lock-then-stop rate.
- MFE and MAE distributions.
- Missed direct 3R and 6R rates.
- Reentry fill rate for reentry variants.
- Incremental R per incremental risk.
- Spread/slippage cost sensitivity.
- DSR, PBO, effective_N.
- Target family, negative controls, and blocked dominance controls.

## Limitations And Failure Modes

The idea is promising, but these are the hard constraints:

- It can miss direct runners if the lock is too tight.
- It can inflate trade count and transaction costs.
- Reentry with the same structural SL often has a larger R distance than the original trade.
- Multiple reentries can quietly create more exposure than the prop-risk envelope allows.
- Same-bar ordering can fabricate gains unless lower-timeframe data resolves the path.
- Liquidity levels are tempting to optimize after the fact; that must be blocked.
- The outcome can look better by increasing risk unless R accounting is strict.
- L2 and exit policy interact, so they must be tested factorially on the same candidate stream.

## Engineering Plan

1. Extend the raw replay event model to emit a pre-L2 candidate stream and deterministic L2 verdicts.
2. Build a reusable path outcome engine that can replay M15 with M5/M1 refinement where available.
3. Implement `BASE_RAW_FIXED_TP`, `J46_J49_ONLY`, and `PATH_SCALE_LOCK_ONLY_V0` first.
4. Add L2 variants once the L2 reconstruction is verified.
5. Add close-and-reenter variants only after lock-only results prove the lock levels are not just truncating winners.
6. Run bounded smoke tests only for debugging.
7. Run final reports on the full available corpus.

## Synthesis

The path-scaling idea makes sense as a research hypothesis. It is trying to exploit a behavior we have already observed: many trades move favorably before failing, and J46-J49 already benefits from changing the exit distribution rather than changing the entry signal.

The highest-quality version is not "trail at 0.7R." It is a path state machine with pre-registered structural levels, strict R accounting, lower-timeframe path resolution, and control cohorts. If it works after that, it is a real position-management candidate. If it only works after level-sweeping, same-lot reentries, or selective reporting, it is not usable.
