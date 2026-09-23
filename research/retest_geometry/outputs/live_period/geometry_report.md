# Retest Geometry Study (v2, ADR 003) — Live-Period Report

**Generated:** 2026-04-17T21:23:25.516857+00:00
**Window:** 2026-04-07 -> 2026-04-17
**Symbols:** XAUUSD, US30_cash, USDJPY, GBPJPY, GBPUSD
**Methodology:** ADR 003 live-period section.

This report emphasizes **Geometry B** (Test A calibration) because it is directly comparable to live execution semantics (1.5R target, tight SL). Geometry A numbers are included alongside for reference.

## Coverage — retests with a matching live evaluation

A retest is 'covered' if a live_evaluations JSONL row exists at the
same M15 candle bucket. Non-covered retests are expected outside kill
zones (live system isn't running) and during orchestrator downtime.

| symbol | matched | total | coverage |
|---|---|---|---|
| GBPUSD | 1 | 4 | 25.0% |
| US30_cash | 0 | 4 | 0.0% |
| USDJPY | 2 | 2 | 100.0% |
| XAUUSD | 1 | 3 | 33.3% |

## Alignment — CANDIDATEs vs mechanically-detected retests

- CANDIDATEs issued at an M15 bucket that matches a mechanical retest: **0** (Geom B) / **0** (Geom A — same by definition, geometry only affects outcome classification, not bucket join)
- CANDIDATEs issued WITHOUT a matching mechanical retest: **71**

## Mechanical outcomes (side-by-side)

Of the CANDIDATEs that matched a mechanical retest, what did our
walk-forward classification say — under each geometry?

| mechanical outcome | Geometry A | Geometry B |
|---|---|---|
| CONTINUED | 0 | 0 |
| REVERSED | 0 | 0 |
| UNRESOLVED | 0 | 0 |

## Misses — Geometry B (live-relevant)

Retests that CONTINUED per Geometry B mechanical classification but the
live system did NOT issue a CANDIDATE (either NO_TRADE or no evaluation).

**Total misses (Geom B):** 2
**Total misses (Geom A, reference):** 6

**Miss reasons — Geometry B (no_trade_reason prefix -> count):**

| reason | n |
|---|---|
| XAUUSD D1 bearish conflicts with required LONG direction; decision guidance mandates exceptional confluence to override  | 1 |
| All three C-gates pass (H1 bullish bias confirmed, M15 aligned bullish, direction LONG matches), but the sole unmitigate | 1 |

## False positives — Geometry B (live-relevant)

CANDIDATEs issued where the Geometry B mechanical classification says REVERSED.

**Total false positives (Geom B):** 0
**Total false positives (Geom A, reference):** 0

## Per-retest diagnostic rows (first 30)

| symbol | retest_ts | bos_confirm_ts | side | outcome_A | outcome_B | live decision | KZ | setup grade |
|---|---|---|---|---|---|---|---|---|
| GBPUSD | 2026-04-13T13:45:00Z | 2026-04-10T17:00:00Z | long | REVERSED | CONTINUED | NO_TRADE | ny | C |
| USDJPY | 2026-04-07T01:00:00Z | 2026-04-06T18:00:00Z | long | CONTINUED | UNRESOLVED | NO_TRADE | tokyo | C |
| USDJPY | 2026-04-17T01:00:00Z | 2026-04-16T17:00:00Z | long | CONTINUED | CONTINUED | NO_TRADE | tokyo | C |
| XAUUSD | 2026-04-09T13:45:00Z | 2026-04-08T22:00:00Z | short | REVERSED | REVERSED | NO_TRADE | ny | C |

---

Notes:
- Live-period window: 2026-04-07 onwards.
- Bucket-matching: retest_ts rounded down to M15 boundary, compared to live eval candle_time.
- A retest outside kill-zone hours has no live eval by design — those show as 'no live evaluation'.
- **Primary geometry for live-period interpretation: B.** A is reported alongside for completeness.
