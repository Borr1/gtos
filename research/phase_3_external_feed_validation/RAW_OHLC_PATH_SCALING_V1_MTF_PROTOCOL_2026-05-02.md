# Raw-OHLC Path Scaling V1 MTF Protocol

**Date:** 2026-05-02
**Spec:** `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V1_MTF_SPEC_V1.json`
**Status:** Registered research protocol
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Purpose

V1 answers one measurement question from the V0 report:

> When M15 path replay reports or hides same-bar ordering ambiguity, does M1 or M5 resolve the sequence materially differently?

V1 is not a new strategy. It is a lower-timeframe path-ordering layer for the already registered V0 variants.

## Boundary

- Research/tooling only.
- No live trading logic changes.
- No prompt edits.
- No parameter optimization.
- No paid AI/API calls.
- No reentry.
- No L2 reconstruction.
- No promotion claim.

## Inherited Inputs

V1 inherits the V0 candidate stream and exit policies:

- `BASE_RAW_FIXED_TP`
- `J46_J49_ONLY`
- `PATH_LOCK_CONSERVATIVE_V0`
- `PATH_LOCK_HALF_GAIN_V0`
- `PATH_LOCK_EARLY_BE_V0`

The setup decision still happens at the M15 candle close. M1/M5 candles are only used after that decision is locked.

## MTF Resolution Rule

For each refinable TAKE setup:

1. Build the same M15 setup row as V0.
2. Load post-decision path candles.
3. Select path timeframe by hierarchy:
   - M1 if rows exist in the post-decision path window.
   - Else M5 if rows exist in the post-decision path window.
   - Else M15 fallback.
4. Require lower-timeframe close time to be strictly greater than setup candle close.
5. Use the frozen V0 exit levels and lock ladders.
6. Convert registered M15-bar time stops into elapsed UTC time for M1/M5 rows.
7. Report unresolved same-bar ambiguity if fill and a path event still occur in the same selected row.

## Required Report Sections

The V1 full-corpus report must include:

- run scope,
- coverage diagnostics,
- V1 variant summary,
- V0 M15-only comparison,
- V0 versus V1 deltas,
- cost sensitivity,
- methodology diagnostics,
- ambiguity ledger,
- opened questions,
- next steps,
- synthesis.

## Acceptance Before V2

V2 must not start until the V1 report is reviewed for:

- remaining same-bar ambiguity,
- M1/M5/M15 coverage mix,
- outcome deltas versus V0,
- group or cohort conclusion changes,
- any clock/as-of ambiguity.

If any item blocks interpretation, V1 remains open and V2 is deferred.
