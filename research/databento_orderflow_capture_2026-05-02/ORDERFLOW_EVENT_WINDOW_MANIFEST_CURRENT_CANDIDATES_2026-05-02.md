# Orderflow Event Window Manifest

Date: 2026-05-02
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Summary

This manifest converts supported GTOS structure/candidate rows into Databento futures harvest windows. It is a data acquisition plan, not an alpha or promotion claim.

## Counts

- Rows loaded: 518
- Events selected: 58
- Merged fetch groups: 13
- Truncated event windows: 0
- Symbol counts: {'GBPUSD': 21, 'NAS100': 12, 'US30_cash': 1, 'XAGUSD': 14, 'XAUUSD': 10}
- Event class counts: {'candidate': 58}

## Fetch Groups

| Group | Symbols | Start UTC | End UTC | Events | Classes |
|---|---|---|---:|---:|---|
| ofwin_0001 | 6B.v.0 | 2026-04-17T07:00:00+00:00 | 2026-04-17T09:00:00+00:00 | 1 | [('candidate', 1)] |
| ofwin_0002 | 6B.v.0 | 2026-04-17T12:30:00+00:00 | 2026-04-17T15:15:00+00:00 | 3 | [('candidate', 3)] |
| ofwin_0003 | 6B.v.0 | 2026-04-29T07:00:00+00:00 | 2026-04-29T16:30:00+00:00 | 17 | [('candidate', 17)] |
| ofwin_0004 | GC.v.0 | 2026-04-17T12:15:00+00:00 | 2026-04-17T14:30:00+00:00 | 2 | [('candidate', 2)] |
| ofwin_0005 | GC.v.0 | 2026-05-01T07:15:00+00:00 | 2026-05-01T09:15:00+00:00 | 1 | [('candidate', 1)] |
| ofwin_0006 | GC.v.0 | 2026-05-01T13:15:00+00:00 | 2026-05-01T16:45:00+00:00 | 7 | [('candidate', 7)] |
| ofwin_0007 | NQ.v.0 | 2026-04-28T06:30:00+00:00 | 2026-04-28T10:45:00+00:00 | 8 | [('candidate', 8)] |
| ofwin_0008 | NQ.v.0 | 2026-04-28T13:45:00+00:00 | 2026-04-28T15:45:00+00:00 | 1 | [('candidate', 1)] |
| ofwin_0009 | NQ.v.0 | 2026-04-29T13:45:00+00:00 | 2026-04-29T16:00:00+00:00 | 2 | [('candidate', 2)] |
| ofwin_0010 | NQ.v.0 | 2026-05-01T07:15:00+00:00 | 2026-05-01T09:15:00+00:00 | 1 | [('candidate', 1)] |
| ofwin_0011 | SI.v.0 | 2026-05-01T07:15:00+00:00 | 2026-05-01T09:30:00+00:00 | 2 | [('candidate', 2)] |
| ofwin_0012 | SI.v.0 | 2026-05-01T12:30:00+00:00 | 2026-05-01T18:00:00+00:00 | 12 | [('candidate', 12)] |
| ofwin_0013 | YM.v.0,ES.v.0 | 2026-04-17T14:45:00+00:00 | 2026-04-17T16:45:00+00:00 | 1 | [('candidate', 1)] |

## Ambiguity Ledger

- canonical_m15_close_utc is inferred by flooring live wall-clock evaluation timestamps to the prior M15 boundary.
- The manifest only covers GTOS symbols with validated CME proxy mappings so far: XAUUSD, XAGUSD, NAS100, US30_cash/US30, and GBPUSD.
- Fetch commands use trades schema first; depth schemas require a separate cost and value gate.
- Event inclusion is limited to fields already present in candidate_features_log.jsonl.
- Rows at or after available_end_utc are excluded when an availability cap is supplied; windows crossing the cap are truncated.

## Open Questions

1. Do trades-level features around these windows separate candidates from structural no-trade context?
2. Which event classes justify mbp-1/mbp-10 depth after trades features are measured?
3. Do inferred M15 candle timestamps match future shadow-only canonical candle-close logging?

## Next Steps

1. Fetch trades schema for the merged candidate/context groups under explicit cost caps.
2. Extract CVD, delta acceleration, POC/HVN/LVN, volume imbalance, and absorption proxies per event.
3. Join features back to synthetic/actual outcomes before any strategy hypothesis is registered.
